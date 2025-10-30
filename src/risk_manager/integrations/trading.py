"""
Trading integration using Project-X-Py SDK.

Stop Loss Cache System
======================

This module caches active stop loss and take profit orders to enable querying them
BEFORE they execute. This is critical for risk management.

Example Usage:
    # Get stop loss for a specific position
    stop_loss = trading_integration.get_stop_loss_for_position("CON.F.US.MNQ.Z25")
    if stop_loss:
        print(f"Stop @ ${stop_loss['stop_price']}")  # e.g., "Stop @ $26242.25"
        print(f"Order ID: {stop_loss['order_id']}")
        print(f"Side: {stop_loss['side']}")  # e.g., "SELL"
        print(f"Qty: {stop_loss['quantity']}")

    # Get all active stop losses across all positions
    all_stops = trading_integration.get_all_active_stop_losses()
    for contract_id, stop_data in all_stops.items():
        print(f"{contract_id} has stop @ ${stop_data['stop_price']}")

    # Check in risk rules
    # Example: Validate stop loss meets minimum distance requirement
    stop = trading_integration.get_stop_loss_for_position(contract_id)
    if not stop:
        return RuleEvaluation(
            passed=False,
            message="Position has no stop loss!",
            severity="CRITICAL"
        )

    if abs(position_price - stop['stop_price']) < minimum_distance:
        return RuleEvaluation(
            passed=False,
            message=f"Stop loss too close: {abs(position_price - stop['stop_price'])} < {minimum_distance}",
            severity="CRITICAL"
        )

Workflow:
    1. Stop loss order placed → Cached in `_active_stop_losses`
    2. Position opened/updated → Query cache to show active stops
    3. Stop loss fills → Removed from cache
    4. Stop loss cancelled → Removed from cache
"""

import asyncio
import os
import time
from collections import defaultdict
from typing import Any

from loguru import logger
from project_x_py import ProjectX, TradingSuite, EventType as SDKEventType
from project_x_py.realtime import ProjectXRealtimeClient

from risk_manager.config.models import RiskConfig
from risk_manager.core.events import EventBus, EventType, RiskEvent


class TradingIntegration:
    """
    Integration with Project-X-Py trading SDK.

    Bridges between the trading platform and risk management system.

    Uses two-step connection:
    1. HTTP API authentication (get JWT token)
    2. SignalR WebSocket connection (real-time events)
    """

    def __init__(self, instruments: list[str], config: RiskConfig, event_bus: EventBus):
        self.instruments = instruments
        self.config = config
        self.event_bus = event_bus
        self.suite: TradingSuite | None = None
        self.client: ProjectX | None = None
        self.realtime: ProjectXRealtimeClient | None = None
        self.running = False

        # Contract ID → Symbol mapping (populated as events arrive)
        self.contract_to_symbol: dict[str, str] = {}

        # Event deduplication cache: {(event_type, entity_id): timestamp}
        # Prevents duplicate events from multiple instrument managers
        self._event_cache: dict[tuple[str, str], float] = {}
        self._event_cache_ttl = 5.0  # seconds

        # Order polling task (to detect protective stops that don't emit events)
        self._order_poll_task = None
        self._known_orders: set[int] = set()  # Track order IDs we've already logged

        # Recent order fills tracking (for correlating position updates with stop losses)
        # Format: {contract_id: {"type": "stop_loss"|"take_profit"|"manual", "timestamp": float, "side": str, "order_id": int, "fill_price": float}}
        self._recent_fills: dict[str, dict[str, Any]] = {}
        self._recent_fills_ttl = 2.0  # seconds - window to correlate fills with position updates

        # Active stop loss cache (tracks WORKING stop orders before they fill)
        # Format: {contract_id: {"order_id": int, "stop_price": float, "side": str, "quantity": int, "timestamp": float}}
        # This allows us to query "What's the stop loss for this position?" BEFORE it gets hit
        self._active_stop_losses: dict[str, dict[str, Any]] = {}

        # Active take profit cache (tracks WORKING limit orders before they fill)
        self._active_take_profits: dict[str, dict[str, Any]] = {}

        # Open positions tracking for P&L calculation
        # Format: {contract_id: {"entry_price": float, "size": int, "side": "long"|"short"}}
        self._open_positions: dict[str, dict[str, Any]] = {}

        logger.info(f"Trading integration initialized for: {instruments}")

    def _is_duplicate_event(self, event_type: str, entity_id: str) -> bool:
        """
        Check if this event is a duplicate.

        The SDK EventBus emits events from each instrument manager separately,
        so a single order can trigger 3 identical events (one per instrument).

        Args:
            event_type: Type of event (e.g., "order_filled", "position_opened")
            entity_id: Unique identifier (order_id or position_id)

        Returns:
            True if this is a duplicate event (recently seen)
        """
        current_time = time.time()
        cache_key = (event_type, entity_id)

        # Clean old entries from cache
        expired_keys = [
            key for key, timestamp in self._event_cache.items()
            if current_time - timestamp > self._event_cache_ttl
        ]
        for key in expired_keys:
            del self._event_cache[key]

        # Check if we've seen this event recently
        if cache_key in self._event_cache:
            logger.debug(f"🔄 Duplicate {event_type} event for {entity_id} - skipping")
            return True

        # Mark event as seen
        self._event_cache[cache_key] = current_time
        return False

    def _check_recent_fill_type(self, contract_id: str) -> str | None:
        """
        Check if there was a recent order fill for this contract.

        Args:
            contract_id: Contract ID to check

        Returns:
            "stop_loss", "take_profit", "manual", or None if no recent fill
        """
        current_time = time.time()

        # Clean old entries
        expired_contracts = [
            cid for cid, fill_data in self._recent_fills.items()
            if current_time - fill_data["timestamp"] > self._recent_fills_ttl
        ]
        for cid in expired_contracts:
            del self._recent_fills[cid]

        # Check if we have a recent fill for this contract
        fill_data = self._recent_fills.get(contract_id)
        if fill_data:
            return fill_data["type"]

        return None

    async def get_stop_loss_for_position(
        self,
        contract_id: str,
        position_entry_price: float = None,
        position_type: int = None,
    ) -> dict[str, Any] | None:
        """
        Get the active stop loss order for a position.

        First checks cache, then queries SDK if cache is empty.
        This handles cases where ORDER_PLACED doesn't fire for broker-UI stops.

        Args:
            contract_id: Contract ID of the position
            position_entry_price: Optional entry price (from event data, avoids query)
            position_type: Optional position type (1=LONG, 2=SHORT from event data)

        Returns:
            Stop loss data dict or None if no active stop loss
            Dict format: {"order_id": int, "stop_price": float, "side": str, "quantity": int, "timestamp": float}
        """
        # Check cache first (fast path)
        cached = self._active_stop_losses.get(contract_id)
        if cached:
            return cached

        # Cache miss - query SDK (handles broker-UI stops that don't emit ORDER_PLACED)
        return await self._query_sdk_for_stop_loss(
            contract_id, position_entry_price, position_type
        )

    async def get_take_profit_for_position(
        self,
        contract_id: str,
        position_entry_price: float = None,
        position_type: int = None,
    ) -> dict[str, Any] | None:
        """
        Get the active take profit order for a position.

        First checks cache, then queries SDK if cache is empty.
        This handles cases where take profits are created in broker UI.

        Args:
            contract_id: Contract ID of the position
            position_entry_price: Optional entry price (from event data, avoids query)
            position_type: Optional position type (1=LONG, 2=SHORT from event data)

        Returns:
            Take profit data dict or None if no active take profit
            Dict format: {"order_id": int, "take_profit_price": float, "side": str, "quantity": int, "timestamp": float}
        """
        # Check cache first (fast path)
        cached = self._active_take_profits.get(contract_id)
        if cached:
            return cached

        # Cache miss - query SDK (semantic analysis will populate take profit cache too)
        await self._query_sdk_for_stop_loss(
            contract_id, position_entry_price, position_type
        )

        # Return take profit from cache (populated by query if found)
        return self._active_take_profits.get(contract_id)

    def get_all_active_stop_losses(self) -> dict[str, dict[str, Any]]:
        """
        Get all active stop loss orders across all positions.

        Returns:
            Dict mapping contract_id to stop loss data
        """
        return self._active_stop_losses.copy()

    def get_all_active_take_profits(self) -> dict[str, dict[str, Any]]:
        """
        Get all active take profit orders across all positions.

        Returns:
            Dict mapping contract_id to take profit data
        """
        return self._active_take_profits.copy()

    async def _query_sdk_for_stop_loss(
        self,
        contract_id: str,
        position_entry_price: float = None,
        position_type: int = None,
    ) -> dict[str, Any] | None:
        """
        Query SDK directly for stop loss orders (bypasses cache).

        This is called when cache is empty. Handles broker-UI stops that
        don't emit ORDER_PLACED events.

        This is NOT polling - only called on-demand when position events fire.

        Args:
            contract_id: Contract ID to query
            position_entry_price: Optional position entry price (avoids querying)
            position_type: Optional position type (1=LONG, 2=SHORT, avoids querying)

        Returns:
            Stop loss data dict or None if no stop found
        """
        symbol = self._extract_symbol_from_contract(contract_id)
        logger.debug(f"Checking for stop loss on {symbol}")

        if not self.suite:
            logger.warning("No suite available for stop loss query")
            return None

        # SDK introspection (DEBUG level only)
        logger.debug(f"Suite type: {type(self.suite)}")
        logger.debug(f"Suite attributes: {[a for a in dir(self.suite) if not a.startswith('_')][:20]}")

        try:
            # Get the instrument manager for this symbol
            if symbol not in self.suite:
                logger.debug(f"Symbol {symbol} not in suite")
                return None

            instrument = self.suite[symbol]
            if not hasattr(instrument, 'orders'):
                logger.error(f"Instrument has no orders attribute")
                return None

            # SDK method introspection (DEBUG level only)
            orders_obj = instrument.orders
            logger.debug(f"Orders object type: {type(orders_obj)}")
            order_methods = [m for m in dir(orders_obj) if not m.startswith('_') and callable(getattr(orders_obj, m))]
            logger.debug(f"Available order methods: {order_methods}")

            # Query orders
            working_orders = await instrument.orders.get_position_orders(contract_id)
            logger.debug(f"get_position_orders returned {len(working_orders)} orders")

            # If empty, try search_open_orders - queries broker API for ALL orders
            if len(working_orders) == 0 and hasattr(orders_obj, 'search_open_orders'):
                logger.debug("Trying search_open_orders (broker API query)...")
                all_orders = await orders_obj.search_open_orders()
                logger.debug(f"search_open_orders returned {len(all_orders)} orders")

                # Filter for this contract
                working_orders = [o for o in all_orders if o.contractId == contract_id]
                logger.debug(f"Filtered to {len(working_orders)} orders for {contract_id}")

            # Get position data for semantic analysis
            if position_entry_price is None or position_type is None:
                logger.debug("Position data not provided, fetching from SDK...")

                try:
                    all_positions = await instrument.positions.get_all_positions()
                    logger.debug(f"get_all_positions returned {len(all_positions)} positions")

                    position = None
                    for pos in all_positions:
                        logger.debug(f"Checking position: {pos.contractId}")
                        if pos.contractId == contract_id:
                            position = pos
                            logger.debug("Found matching position")
                            break

                    if not position:
                        logger.warning(f"No position found for {contract_id}")
                        logger.debug(f"Available positions: {[p.contractId for p in all_positions]}")
                        return None

                    position_entry_price = position.avgPrice
                    position_type = position.type  # 1=LONG, 2=SHORT

                except Exception as pos_error:
                    logger.error(f"Error fetching position: {pos_error}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    return None
            else:
                logger.debug("Using provided position data (avoids hanging get_all_positions)")

            # Log position details
            pos_direction = "LONG" if position_type == 1 else "SHORT" if position_type == 2 else "UNKNOWN"
            logger.debug(f"Position: {pos_direction} @ ${position_entry_price:.2f}")

            # Analyze orders using semantic layer
            stop_loss_data = None
            take_profit_data = None

            for order in working_orders:
                if order.contractId == contract_id:
                    # Determine trigger price
                    trigger_price = order.stopPrice if order.stopPrice else order.limitPrice

                    logger.debug(f"Order #{order.id}: type={order.type_str}, trigger=${trigger_price}")

                    # Use semantic analysis to determine intent
                    intent = self._determine_order_intent(order, position_entry_price, position_type)
                    logger.debug(f"Semantic intent: {intent}")

                    if intent == "stop_loss":
                        # Found stop loss!
                        stop_loss_data = {
                            "order_id": order.id,
                            "stop_price": trigger_price,
                            "side": self._get_side_name(order.side),
                            "quantity": order.size,
                            "timestamp": time.time(),
                        }
                        # Cache it
                        self._active_stop_losses[contract_id] = stop_loss_data
                        logger.debug(f"Found stop loss: ${trigger_price:,.2f}")

                    elif intent == "take_profit":
                        # Found take profit!
                        take_profit_data = {
                            "order_id": order.id,
                            "take_profit_price": trigger_price,
                            "side": self._get_side_name(order.side),
                            "quantity": order.size,
                            "timestamp": time.time(),
                        }
                        # Cache it
                        self._active_take_profits[contract_id] = take_profit_data
                        logger.debug(f"Found take profit: ${trigger_price:,.2f}")

            # Return stop loss (if found)
            if stop_loss_data:
                logger.debug(f"Query result: Found stop loss @ ${stop_loss_data['stop_price']:,.2f}")
                return stop_loss_data

            # No stop found
            logger.debug("Query result: No stop loss found")
            return None

        except Exception as e:
            logger.error(f"Error querying SDK for stops: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    def _extract_symbol_from_contract(self, contract_id: str) -> str:
        """
        Extract symbol from contract ID.

        Contract ID format: CON.F.US.{SYMBOL}.{EXPIRY}
        Examples:
        - CON.F.US.MNQ.U25 → MNQ
        - CON.F.US.ES.H25 → ES
        - CON.F.US.NQ.Z25 → NQ

        Args:
            contract_id: Full contract ID from SDK

        Returns:
            Symbol (e.g., "MNQ", "ES", "NQ")
        """
        if not contract_id:
            return self.instruments[0] if self.instruments else "UNKNOWN"

        # Check cache first
        if contract_id in self.contract_to_symbol:
            return self.contract_to_symbol[contract_id]

        # Parse contract ID
        try:
            parts = contract_id.split('.')
            if len(parts) >= 4:
                symbol = parts[3]  # CON.F.US.{SYMBOL}.{EXPIRY}

                # Cache for future lookups
                self.contract_to_symbol[contract_id] = symbol
                logger.debug(f"Mapped contract {contract_id} → {symbol}")

                return symbol
        except Exception as e:
            logger.warning(f"Could not parse contract ID '{contract_id}': {e}")

        # Fallback: use first instrument
        fallback = self.instruments[0] if self.instruments else "UNKNOWN"
        logger.warning(f"Using fallback symbol '{fallback}' for contract {contract_id}")
        return fallback

    def _determine_order_intent(
        self, order, position_entry_price: float, position_type: int
    ) -> str:
        """
        Determine order intent using simplified logic.

        For positions that exist, STOP orders are protective (stop loss),
        LIMIT orders are profit targets (take profit).

        Args:
            order: Order object from SDK
            position_entry_price: Position's average entry price
            position_type: Position type (1=LONG, 2=SHORT)

        Returns:
            "stop_loss" | "take_profit" | "entry" | "unknown"
        """
        if not order or position_entry_price is None:
            return "unknown"

        # SIMPLIFIED RULE: For existing positions:
        # - STOP orders (type 3, 4, 5) = Stop Loss (protective)
        # - LIMIT orders (type 1) = Take Profit (target)
        # - MARKET orders (type 2) = Manual exit/entry

        if order.type in [3, 4, 5]:  # STOP_LIMIT, STOP, TRAILING_STOP
            # STOP orders on existing positions are stop losses
            return "stop_loss"

        elif order.type == 1:  # LIMIT
            # LIMIT orders on existing positions are take profits
            # (assuming they're closing orders, not entries)
            trigger_price = order.limitPrice

            if trigger_price is None:
                return "unknown"

            # Use position TYPE (1=LONG, 2=SHORT), not size sign
            is_long_position = (position_type == 1)
            is_short_position = (position_type == 2)

            # Verify this is actually a profit target
            if is_long_position:
                # LONG: Take profit ABOVE entry, entry BELOW
                if trigger_price > position_entry_price:
                    return "take_profit"
                else:
                    return "entry"  # Limit buy below entry = entry order
            elif is_short_position:
                # SHORT: Take profit BELOW entry, entry ABOVE
                if trigger_price < position_entry_price:
                    return "take_profit"
                else:
                    return "entry"  # Limit sell above entry = entry order
            else:
                return "unknown"

        elif order.type == 2:  # MARKET
            # Market orders could be manual exit or entry
            return "unknown"

        else:
            return "unknown"

    async def connect(self) -> None:
        """
        Connect to trading platform using two-step process.

        Step 1: HTTP API authentication
        Step 2: SignalR WebSocket connection
        """
        logger.info("Connecting to ProjectX trading platform...")

        try:
            # STEP 1: HTTP API Authentication
            logger.info("Step 1: Authenticating via HTTP API...")
            self.client = await ProjectX.from_env().__aenter__()
            await self.client.authenticate()

            account = self.client.account_info
            logger.info(f"✅ Authenticated: {account.name} (ID: {account.id})")
            logger.info(f"   Balance: ${account.balance:,.2f}, Trading: {account.canTrade}")

            # STEP 2: SignalR WebSocket Connection
            logger.info("Step 2: Establishing SignalR WebSocket connection...")
            self.realtime = ProjectXRealtimeClient(
                jwt_token=self.client.session_token,
                account_id=str(self.client.account_info.id),
                config=self.client.config
            )

            await self.realtime.connect()

            if self.realtime.is_connected:
                logger.success("✅ SignalR WebSocket connected (User Hub + Market Hub)")
            else:
                raise ConnectionError("SignalR connection failed")

            # STEP 3: Create TradingSuite with established connections
            logger.info("Step 3: Initializing TradingSuite...")
            self.suite = await TradingSuite.create(
                instruments=self.instruments,
                timeframes=["1min", "5min"],
                features=["performance_analytics", "auto_reconnect"],  # Removed orderbook (causes depth entry errors)
            )

            # Wire the realtime client to the suite
            if hasattr(self.suite, 'realtime'):
                self.suite.realtime = self.realtime
                logger.debug("Wired realtime client to TradingSuite")
            else:
                logger.warning("Suite doesn't have realtime attribute, adding it manually")
                self.suite.realtime = self.realtime

            logger.success("✅ Connected to ProjectX (HTTP + WebSocket + TradingSuite)")

        except Exception as e:
            logger.error(f"Failed to connect to trading platform: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from trading platform."""
        logger.info("Disconnecting from trading platform...")

        # Stop polling task
        self.running = False
        if self._order_poll_task:
            self._order_poll_task.cancel()
            try:
                await self._order_poll_task
            except asyncio.CancelledError:
                pass
            logger.debug("Order polling task stopped")

        # Disconnect in reverse order
        if self.suite:
            await self.suite.disconnect()
            logger.debug("TradingSuite disconnected")

        if self.realtime:
            await self.realtime.disconnect()
            logger.debug("SignalR WebSocket disconnected")

        if self.client:
            await self.client.__aexit__(None, None, None)
            logger.debug("HTTP client closed")

        logger.success("✅ Disconnected from trading platform")

    async def start(self) -> None:
        """
        Start monitoring trading events via realtime callbacks.

        NOTE: We subscribe to realtime.add_callback() NOT suite.on()
        The SDK EventBus doesn't emit position/order/trade events from SignalR.
        """
        if not self.suite or not self.realtime:
            raise RuntimeError("Not connected - call connect() first")

        if not self.realtime.is_connected:
            raise RuntimeError("SignalR not connected")

        # Prevent duplicate callback registration
        if self.running:
            logger.warning("⚠️ Trading monitoring already started - skipping duplicate registration")
            return

        self.running = True
        logger.info("Starting trading event monitoring...")

        try:
            logger.info("Registering event callbacks via suite.on()...")

            # Subscribe to ORDER events via suite EventBus (using SDK EventType)
            await self.suite.on(SDKEventType.ORDER_PLACED, self._on_order_placed)
            logger.info("✅ Registered: ORDER_PLACED")

            await self.suite.on(SDKEventType.ORDER_FILLED, self._on_order_filled)
            logger.info("✅ Registered: ORDER_FILLED")

            await self.suite.on(SDKEventType.ORDER_PARTIAL_FILL, self._on_order_partial_fill)
            logger.info("✅ Registered: ORDER_PARTIAL_FILL")

            await self.suite.on(SDKEventType.ORDER_CANCELLED, self._on_order_cancelled)
            logger.info("✅ Registered: ORDER_CANCELLED")

            await self.suite.on(SDKEventType.ORDER_REJECTED, self._on_order_rejected)
            logger.info("✅ Registered: ORDER_REJECTED")

            await self.suite.on(SDKEventType.ORDER_MODIFIED, self._on_order_modified)
            logger.info("✅ Registered: ORDER_MODIFIED")

            await self.suite.on(SDKEventType.ORDER_EXPIRED, self._on_order_expired)
            logger.info("✅ Registered: ORDER_EXPIRED")

            # Subscribe to POSITION events via suite EventBus (using SDK EventType)
            await self.suite.on(SDKEventType.POSITION_OPENED, self._on_position_opened)
            logger.info("✅ Registered: POSITION_OPENED")

            await self.suite.on(SDKEventType.POSITION_CLOSED, self._on_position_closed)
            logger.info("✅ Registered: POSITION_CLOSED")

            await self.suite.on(SDKEventType.POSITION_UPDATED, self._on_position_updated)
            logger.info("✅ Registered: POSITION_UPDATED")

            # Catch-all disabled - too noisy with market data events
            # If you need to debug new events, uncomment this block:
            # for event_type in SDKEventType:
            #     if event_type.name not in [...known events...]:
            #         await self.suite.on(event_type, self._on_unknown_event)

            logger.success("✅ Trading monitoring started (10 event handlers registered)")
            logger.info("📡 Listening for events: ORDER (8 types), POSITION (3 types), + catch-all")

            # Start order polling task (to catch protective stops that don't emit events)
            self._order_poll_task = asyncio.create_task(self._poll_orders())
            logger.info("🔄 Started order polling task (5s interval)")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Failed to register realtime callbacks: {e}")
            raise

    async def _poll_orders(self):
        """
        Poll for active orders periodically.

        Some platforms don't emit events when protective stops are placed,
        so we need to poll the order list to detect them.
        """
        logger.debug("Order polling task started")

        while self.running:
            try:
                await asyncio.sleep(5)  # Poll every 5 seconds

                if not self.suite:
                    logger.debug("Suite not available yet")
                    continue

                # Get all working orders from all instruments
                # Note: get_position_orders() requires contract_id, so we need to get positions first
                orders = []
                for symbol, instrument in self.suite.items():
                    if not hasattr(instrument, 'positions') or not hasattr(instrument, 'orders'):
                        continue

                    # Get all positions for this instrument
                    try:
                        positions = await instrument.positions.get_all_positions()
                        for position in positions:
                            # Get orders for this position's contract (needs await)
                            position_orders = await instrument.orders.get_position_orders(position.contractId)
                            orders.extend(position_orders)
                    except Exception as e:
                        logger.debug(f"Error getting orders for {symbol}: {e}")
                        continue

                logger.debug(f"Polling found {len(orders)} working orders")

                for order in orders:
                    order_id = order.id

                    # Skip if we've already seen this order
                    if order_id in self._known_orders:
                        continue

                    # Mark as seen
                    self._known_orders.add(order_id)

                    # Log new orders at INFO level (concise)
                    symbol = self._extract_symbol_from_contract(order.contractId)
                    logger.info(f"🔍 NEW ORDER (polling): {symbol} {order.type_str} {self._get_side_name(order.side)} {order.size}")
                    logger.debug(f"Stop: {order.stopPrice}, Limit: {order.limitPrice}, Status: {order.status}")

                    # Check if it's a protective stop and cache it
                    if self._is_stop_loss(order):
                        # Cache it (if not already cached)
                        if order.contractId not in self._active_stop_losses:
                            self._active_stop_losses[order.contractId] = {
                                "order_id": order.id,
                                "stop_price": order.stopPrice,
                                "side": self._get_side_name(order.side),
                                "quantity": order.size,
                                "timestamp": time.time(),
                            }
                            logger.info(f"  🛡️  Stop Loss cached: ${order.stopPrice:,.2f}")

                    # Check if it's a take profit and cache it
                    if self._is_take_profit(order):
                        if order.contractId not in self._active_take_profits:
                            self._active_take_profits[order.contractId] = {
                                "order_id": order.id,
                                "limit_price": order.limitPrice,
                                "side": self._get_side_name(order.side),
                                "quantity": order.size,
                                "timestamp": time.time(),
                            }
                            logger.info(f"  🎯 Take Profit cached: ${order.limitPrice:,.2f}")

            except Exception as e:
                logger.warning(f"Error polling orders: {e}")
                import traceback
                logger.debug(traceback.format_exc())

        logger.debug("Order polling task stopped")

    # ============================================================================
    # SDK EventBus Callbacks (suite.on)
    # ============================================================================

    async def _on_order_placed(self, event) -> None:
        """Handle ORDER_PLACED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_PLACED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate FIRST (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_placed", str(order.id)):
                return

            # Debug: Show payload AFTER dedup (only for unique events)
            logger.debug(f"📦 ORDER_PLACED Payload: order_id={order.id}, type={order.type}, stopPrice={order.stopPrice}")

            symbol = self._extract_symbol_from_contract(order.contractId)
            order_type_str = order.type_str

            # Build descriptive order placement message
            order_desc = self._get_order_placement_display(order)

            logger.info(f"📋 ORDER PLACED - {symbol} | {order_desc}")

            # Order details at DEBUG level only
            logger.debug(f"Order ID: {order.id}, Type: {order.type} ({order.type_str}), Stop: {order.stopPrice}, Limit: {order.limitPrice}, Status: {order.status}")

            # Cache active stop losses (so we can query them before they fill)
            if self._is_stop_loss(order):
                self._active_stop_losses[order.contractId] = {
                    "order_id": order.id,
                    "stop_price": order.stopPrice,
                    "side": self._get_side_name(order.side),
                    "quantity": order.size,
                    "timestamp": time.time(),
                }
                logger.debug(f"Cached stop loss: {order.contractId} → SL @ ${order.stopPrice:,.2f}")

            # Cache active take profits
            if self._is_take_profit(order):
                self._active_take_profits[order.contractId] = {
                    "order_id": order.id,
                    "limit_price": order.limitPrice,
                    "side": self._get_side_name(order.side),
                    "quantity": order.size,
                    "timestamp": time.time(),
                }
                logger.debug(f"Cached take profit: {order.contractId} → TP @ ${order.limitPrice:,.2f}")

            # Bridge to risk event bus
            risk_event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={
                    "symbol": symbol,
                    "order_id": order.id,
                    "side": self._get_side_name(order.side),
                    "quantity": order.size,
                    "price": getattr(order, 'limitPrice', None),
                    "order_type": order.type,
                    "order_type_str": order_type_str,
                    "stop_price": order.stopPrice,
                    "limit_price": order.limitPrice,
                    "is_stop_loss": self._is_stop_loss(order),
                    "raw_data": data,
                },
                source="trading_sdk",
            )
            await self.event_bus.publish(risk_event)

        except Exception as e:
            logger.error(f"Error handling ORDER_PLACED: {e}")
            logger.exception(e)

    async def _on_order_filled(self, event) -> None:
        """Handle ORDER_FILLED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_FILLED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate FIRST (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_filled", str(order.id)):
                return

            # Debug: Show payload AFTER dedup (only for unique events)
            logger.debug(f"📦 ORDER_FILLED Payload: order_id={order.id}, type={order.type}, stopPrice={order.stopPrice}")

            symbol = self._extract_symbol_from_contract(order.contractId)
            order_type = self._get_order_type_display(order)

            # Use different emoji for stop loss vs take profit vs manual
            emoji = self._get_order_emoji(order)

            # Concise fill message with formatted price
            logger.info(
                f"{emoji} ORDER FILLED - {symbol} {self._get_side_name(order.side)} "
                f"{order.fillVolume} @ ${order.filledPrice:,.2f}"
            )

            # Order details at DEBUG level only
            logger.debug(f"Order ID: {order.id}, Type: {order.type} ({order.type_str}), Stop: {order.stopPrice}, Limit: {order.limitPrice}, Status: {order.status}")

            # Remove from known orders (it's filled now)
            self._known_orders.discard(order.id)

            # Track this fill for correlation with position updates
            is_sl = self._is_stop_loss(order)
            is_tp = self._is_take_profit(order)
            fill_type = "stop_loss" if is_sl else "take_profit" if is_tp else "manual"

            self._recent_fills[order.contractId] = {
                "type": fill_type,
                "timestamp": time.time(),
                "side": self._get_side_name(order.side),
                "order_id": order.id,
                "fill_price": order.filledPrice,  # Store exit price for P&L calculation
            }
            logger.debug(f"Recorded {fill_type} fill | _is_stop_loss={is_sl}, _is_take_profit={is_tp}")

            # Remove from active caches (order is now filled)
            if is_sl and order.contractId in self._active_stop_losses:
                del self._active_stop_losses[order.contractId]
                logger.debug("Removed stop loss from cache (filled)")

            if is_tp and order.contractId in self._active_take_profits:
                del self._active_take_profits[order.contractId]
                logger.debug("Removed take profit from cache (filled)")

            # Bridge to risk event bus
            risk_event = RiskEvent(
                event_type=EventType.ORDER_FILLED,
                data={
                    "symbol": symbol,
                    "order_id": order.id,
                    "side": self._get_side_name(order.side),
                    "quantity": order.fillVolume,
                    "price": order.filledPrice,
                    "order_type": order.type,
                    "order_type_str": order.type_str,
                    "is_stop_loss": self._is_stop_loss(order),
                    "is_take_profit": self._is_take_profit(order),
                    "stop_price": order.stopPrice,
                    "limit_price": order.limitPrice,
                    "raw_data": data,
                },
                source="trading_sdk",
            )
            await self.event_bus.publish(risk_event)

        except Exception as e:
            logger.error(f"Error handling ORDER_FILLED: {e}")
            logger.exception(e)

    async def _on_order_partial_fill(self, event) -> None:
        """Handle ORDER_PARTIAL_FILL event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_PARTIAL_FILL event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload
            logger.debug(f"📦 ORDER_PARTIAL_FILL Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_partial_fill", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)

            logger.info(
                f"📊 ORDER PARTIALLY FILLED - {symbol} | ID: {order.id} | Filled: {order.fillVolume}/{order.size} @ ${order.filledPrice:.2f}"
            )

        except Exception as e:
            logger.error(f"Error handling ORDER_PARTIAL_FILL: {e}")

    async def _on_order_cancelled(self, event) -> None:
        """Handle ORDER_CANCELLED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_CANCELLED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload
            logger.debug(f"📦 ORDER_CANCELLED Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_cancelled", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)

            logger.info(f"❌ ORDER CANCELLED - {symbol} | ID: {order.id}")

            # Remove from known orders (it's cancelled now)
            self._known_orders.discard(order.id)

            # Remove from active caches (order is now cancelled)
            if order.contractId in self._active_stop_losses:
                if self._active_stop_losses[order.contractId]["order_id"] == order.id:
                    del self._active_stop_losses[order.contractId]
                    logger.info(f"  └─ 🛡️ Removed stop loss from cache (cancelled)")

            if order.contractId in self._active_take_profits:
                if self._active_take_profits[order.contractId]["order_id"] == order.id:
                    del self._active_take_profits[order.contractId]
                    logger.info(f"  └─ 🎯 Removed take profit from cache (cancelled)")

        except Exception as e:
            logger.error(f"Error handling ORDER_CANCELLED: {e}")

    async def _on_order_rejected(self, event) -> None:
        """Handle ORDER_REJECTED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_REJECTED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload
            logger.debug(f"📦 ORDER_REJECTED Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_rejected", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)

            logger.warning(f"⛔ ORDER REJECTED - {symbol} | ID: {order.id}")

        except Exception as e:
            logger.error(f"Error handling ORDER_REJECTED: {e}")

    async def _on_order_modified(self, event) -> None:
        """Handle ORDER_MODIFIED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_MODIFIED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload at DEBUG level
            logger.debug(f"📦 ORDER_MODIFIED Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_modified", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)
            order_type_str = order.type_str

            # Build descriptive order modification message
            order_desc = self._get_order_placement_display(order)

            logger.info(f"📝 ORDER MODIFIED - {symbol} | {order_desc}")

            # Order details at DEBUG level only
            logger.debug(f"Order ID: {order.id}, Type: {order.type} ({order.type_str}), Stop: {order.stopPrice}, Limit: {order.limitPrice}, Status: {order.status}")

            # CRITICAL: Invalidate ALL cache for this position when ANY order is modified
            # This catches new orders that were placed but not detected yet!
            # Also detects price changes from broker-UI modifications
            contract_id = order.contractId

            logger.debug(f"Invalidating protective order cache for {contract_id}")

            if contract_id in self._active_stop_losses:
                del self._active_stop_losses[contract_id]

            if contract_id in self._active_take_profits:
                del self._active_take_profits[contract_id]

            logger.debug("Cache cleared - next POSITION_UPDATED will query fresh data")

        except Exception as e:
            logger.error(f"Error handling ORDER_MODIFIED: {e}")
            logger.exception(e)

    async def _on_order_expired(self, event) -> None:
        """Handle ORDER_EXPIRED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_EXPIRED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload at DEBUG level
            logger.debug(f"📦 ORDER_EXPIRED Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_expired", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)

            logger.warning(f"⏰ ORDER EXPIRED - {symbol} | ID: {order.id}")

        except Exception as e:
            logger.error(f"Error handling ORDER_EXPIRED: {e}")

    async def _on_unknown_event(self, event) -> None:
        """Catch-all handler for events we haven't explicitly subscribed to."""
        event_type = event.type if hasattr(event, 'type') else "UNKNOWN"
        logger.warning(f"🔍 UNHANDLED EVENT: {event_type}")
        logger.warning(f"   Event data: {event.data if hasattr(event, 'data') else event}")

    async def _on_position_opened(self, event) -> None:
        """Handle POSITION_OPENED event from SDK EventBus."""
        logger.debug(f"🔔 POSITION_OPENED event received")
        await self._handle_position_event(event, "OPENED")

    async def _on_position_closed(self, event) -> None:
        """Handle POSITION_CLOSED event from SDK EventBus."""
        logger.debug(f"🔔 POSITION_CLOSED event received")
        await self._handle_position_event(event, "CLOSED")

    async def _on_position_updated(self, event) -> None:
        """Handle POSITION_UPDATED event from SDK EventBus."""
        logger.debug(f"🔔 POSITION_UPDATED event received")
        await self._handle_position_event(event, "UPDATED")

    async def _handle_position_event(self, event, action_name: str) -> None:
        """Common handler for all position events."""
        try:
            data = event.data if hasattr(event, 'data') else {}

            if not isinstance(data, dict):
                return

            contract_id = data.get('contractId')
            size = data.get('size', 0)
            avg_price = data.get('averagePrice', 0.0)
            unrealized_pnl = data.get('unrealizedPnl', 0.0)
            pos_type = data.get('type', 0)

            # CRITICAL: Check protective orders BEFORE dedup
            # Second order placements don't trigger unique events!
            # Must query on EVERY event to catch them
            if action_name in ["OPENED", "UPDATED"]:
                logger.debug(f"Checking protective orders (pre-dedup)")

                # Always invalidate cache and query fresh
                if contract_id in self._active_stop_losses:
                    del self._active_stop_losses[contract_id]
                if contract_id in self._active_take_profits:
                    del self._active_take_profits[contract_id]

                # Query with position data from event
                stop_loss_early = await self.get_stop_loss_for_position(
                    contract_id, avg_price, pos_type
                )
                take_profit_early = await self.get_take_profit_for_position(
                    contract_id, avg_price, pos_type
                )

                # Log findings (DEBUG level for early check)
                logger.debug(f"Pre-dedup query: SL={bool(stop_loss_early)}, TP={bool(take_profit_early)}")

            # Check for duplicate (prevents 3x events from 3 instruments)
            # Use contract_id + action for deduplication key
            dedup_key = f"{contract_id}_{action_name}"
            if self._is_duplicate_event(f"position_{action_name.lower()}", dedup_key):
                return  # Exit after protective order check

            # Debug: Show payload AFTER dedup (only for unique events)
            logger.debug(f"📦 POSITION_{action_name} Payload keys: {list(data.keys())}")

            # Check if position data includes protective stops (some platforms embed them)
            if 'stopLoss' in data or 'takeProfit' in data or 'protectiveOrders' in data:
                logger.info(f"🛡️  Position has protective orders: SL={data.get('stopLoss')}, TP={data.get('takeProfit')}")

            symbol = self._extract_symbol_from_contract(contract_id)

            # Check if this position update correlates with a recent order fill
            fill_type = self._check_recent_fill_type(contract_id)
            logger.debug(f"🔍 Checking recent fills for {contract_id}: fill_type={fill_type}")
            logger.debug(f"   Recent fills cache: {list(self._recent_fills.keys())}")

            # Build position update label with fill context
            position_label = f"📊 POSITION {action_name}"
            if fill_type == "stop_loss":
                position_label = f"🛑 POSITION {action_name} (STOP LOSS)"
            elif fill_type == "take_profit":
                position_label = f"🎯 POSITION {action_name} (TAKE PROFIT)"

            # Concise position message with formatted numbers
            logger.info(
                f"{position_label} - {symbol} {self._get_position_type_name(pos_type)} "
                f"{size} @ ${avg_price:,.2f} | P&L: ${unrealized_pnl:,.2f}"
            )

            # Show active stop loss/take profit for this position (if any)
            # CRITICAL: Always check on EVERY event, even if deduped for logging
            # This ensures we catch new orders that don't trigger unique events
            if action_name in ["OPENED", "UPDATED"]:
                logger.debug("Checking protective orders (post-dedup)")

                # ALWAYS invalidate cache on position updates
                # This forces a fresh query EVERY time, catching new orders
                if contract_id in self._active_stop_losses:
                    logger.debug("Invalidating stop loss cache")
                    del self._active_stop_losses[contract_id]

                if contract_id in self._active_take_profits:
                    logger.debug("Invalidating take profit cache")
                    del self._active_take_profits[contract_id]

                # Pass position data from event to avoid hanging get_all_positions() call
                # pos_type: 1=LONG, 2=SHORT
                stop_loss = await self.get_stop_loss_for_position(
                    contract_id, avg_price, pos_type
                )
                take_profit = await self.get_take_profit_for_position(
                    contract_id, avg_price, pos_type
                )

                if stop_loss:
                    logger.info(f"  🛡️  Stop Loss: ${stop_loss['stop_price']:,.2f}")
                else:
                    logger.warning(f"  ⚠️  NO STOP LOSS")

                if take_profit:
                    logger.info(f"  🎯 Take Profit: ${take_profit['take_profit_price']:,.2f}")
                else:
                    logger.info("  ℹ️  No take profit order")

            # Bridge to risk event bus
            event_type_map = {
                "OPENED": EventType.POSITION_OPENED,
                "CLOSED": EventType.POSITION_CLOSED,  # Fixed: was POSITION_UPDATED
                "UPDATED": EventType.POSITION_UPDATED,
            }

            # Get active stop loss/take profit data for this position
            # Note: We already queried this above for logging, cache will make this instant
            stop_loss_for_event = await self.get_stop_loss_for_position(
                contract_id, avg_price, pos_type
            )
            take_profit_for_event = await self.get_take_profit_for_position(
                contract_id, avg_price, pos_type
            )

            # Calculate realized P&L for CLOSED positions
            # SDK doesn't provide profitAndLoss, so we calculate it ourselves!
            realized_pnl = None
            if action_name == "CLOSED":
                # Check if we tracked this position when it opened
                if contract_id in self._open_positions:
                    tracked = self._open_positions[contract_id]
                    entry_price = tracked['entry_price']
                    entry_size = tracked['size']
                    side = tracked['side']  # 'long' or 'short'

                    # Get exit price from recent fill, not from position event!
                    # POSITION_CLOSED gives us avg_price (entry), not exit price
                    # The actual exit price comes from the ORDER_FILLED event
                    exit_price = avg_price  # Fallback
                    if contract_id in self._recent_fills:
                        fill_data = self._recent_fills[contract_id]
                        if fill_data.get('fill_price'):
                            exit_price = fill_data['fill_price']
                            logger.debug(f"Using exit price from recent fill: ${exit_price:,.2f}")
                        else:
                            logger.warning(f"Recent fill found but no fill_price! Using position avg_price: ${avg_price:,.2f}")
                    else:
                        logger.warning(f"No recent fill found for {contract_id}, using position avg_price: ${avg_price:,.2f}")

                    # Calculate P&L: (exit - entry) * size * tick_value
                    # MNQ tick value: $5 per contract per tick (0.25 points)
                    tick_value = 5.0  # TODO: Make this configurable per symbol
                    tick_size = 0.25

                    if side == 'long':
                        # Long: profit when price goes up
                        price_diff = exit_price - entry_price
                    else:
                        # Short: profit when price goes down
                        price_diff = entry_price - exit_price

                    # Convert price difference to ticks
                    ticks = price_diff / tick_size
                    realized_pnl = ticks * tick_value * abs(entry_size)

                    logger.info(f"💰 Calculated P&L:")
                    logger.info(f"   Entry: ${entry_price:,.2f} @ {entry_size} ({side})")
                    logger.info(f"   Exit: ${exit_price:,.2f}")
                    logger.info(f"   Price diff: {price_diff:+.2f} = {ticks:+.1f} ticks")
                    logger.info(f"   Realized P&L: ${realized_pnl:+,.2f}")

                    # Remove from tracking
                    del self._open_positions[contract_id]
                else:
                    logger.warning(f"⚠️  Position closed but not in tracking! Can't calculate P&L for {contract_id}")

            # Track OPENED positions for P&L calculation
            elif action_name == "OPENED":
                side = 'long' if size > 0 else 'short'
                self._open_positions[contract_id] = {
                    'entry_price': avg_price,
                    'size': size,
                    'side': side,
                }
                logger.debug(f"📝 Tracking position: {contract_id} @ ${avg_price:,.2f} x {size} ({side})")

            risk_event = RiskEvent(
                event_type=event_type_map.get(action_name, EventType.POSITION_UPDATED),
                data={
                    "symbol": symbol,
                    "contract_id": contract_id,
                    "size": size,
                    "side": "long" if size > 0 else "short" if size < 0 else "flat",
                    "average_price": avg_price,
                    "unrealized_pnl": unrealized_pnl,
                    "profitAndLoss": realized_pnl,  # Add realized P&L for closed positions
                    "action": action_name.lower(),
                    "fill_type": fill_type,  # "stop_loss", "take_profit", "manual", or None
                    "is_stop_loss": fill_type == "stop_loss",
                    "is_take_profit": fill_type == "take_profit",
                    "stop_loss": stop_loss_for_event,  # Active stop loss order data (or None)
                    "take_profit": take_profit_for_event,  # Active take profit order data (or None)
                    "raw_data": data,
                },
                source="trading_sdk",
            )

            await self.event_bus.publish(risk_event)

        except Exception as e:
            logger.error(f"Error handling POSITION_{action_name}: {e}")
            logger.exception(e)

    def _get_side_name(self, side: int) -> str:
        """Convert side int to name (0=BUY, 1=SELL)."""
        return "BUY" if side == 0 else "SELL"

    def _get_position_type_name(self, pos_type: int) -> str:
        """Convert position type to name (1=LONG, 2=SHORT)."""
        if pos_type == 1:
            return "LONG"
        elif pos_type == 2:
            return "SHORT"
        else:
            return "FLAT"

    def _get_order_placement_display(self, order) -> str:
        """
        Get human-readable order placement display.

        Returns formatted string like:
        - "🛡️ STOP LOSS @ $3975.50 | SELL | Qty: 1" (stop loss protection placed)
        - "🎯 TAKE PROFIT @ $3980.00 | SELL | Qty: 1" (take profit placed)
        - "MARKET | BUY | Qty: 1" (manual market order)
        - "LIMIT @ $3978.00 | BUY | Qty: 1" (manual limit order)
        """
        order_type = order.type_str
        side = self._get_side_name(order.side)
        qty = order.size

        if self._is_stop_loss(order):
            price = order.stopPrice
            return f"🛡️ STOP LOSS @ ${price:.2f} | {side} | Qty: {qty}"
        elif order_type == "LIMIT":
            price = order.limitPrice
            return f"LIMIT @ ${price:.2f} | {side} | Qty: {qty}"
        elif order_type == "MARKET":
            return f"MARKET | {side} | Qty: {qty}"
        elif order_type == "STOP_LIMIT":
            price = order.stopPrice
            return f"STOP_LIMIT @ ${price:.2f} | {side} | Qty: {qty}"
        elif order_type == "TRAILING_STOP":
            return f"TRAILING_STOP | {side} | Qty: {qty}"
        else:
            return f"{order_type} | {side} | Qty: {qty}"

    def _get_order_type_display(self, order) -> str:
        """
        Get human-readable order type display (for fills).

        Returns formatted string like:
        - "STOP LOSS @ $3975.50" (stop order closing a position)
        - "TAKE PROFIT @ $3980.00" (limit order closing at profit)
        - "MARKET" (manual market order)
        - "LIMIT @ $3978.00" (manual limit order)
        """
        order_type = order.type_str

        if self._is_stop_loss(order):
            price = order.stopPrice or order.filledPrice
            return f"🛑 STOP LOSS @ ${price:.2f}"
        elif self._is_take_profit(order):
            price = order.limitPrice or order.filledPrice
            return f"🎯 TAKE PROFIT @ ${price:.2f}"
        elif order_type == "MARKET":
            return "MARKET"
        elif order_type == "LIMIT":
            return f"LIMIT @ ${order.limitPrice:.2f}" if order.limitPrice else "LIMIT"
        elif order_type == "STOP":
            return f"STOP @ ${order.stopPrice:.2f}" if order.stopPrice else "STOP"
        elif order_type == "STOP_LIMIT":
            return f"STOP_LIMIT @ ${order.stopPrice:.2f}" if order.stopPrice else "STOP_LIMIT"
        elif order_type == "TRAILING_STOP":
            return "TRAILING_STOP"
        else:
            return order_type

    def _get_order_emoji(self, order) -> str:
        """Get emoji based on order type/intent."""
        if self._is_stop_loss(order):
            return "🛑"  # Stop sign for stop loss
        elif self._is_take_profit(order):
            return "🎯"  # Target for take profit
        else:
            return "💰"  # Money bag for regular fills

    def _is_stop_loss(self, order) -> bool:
        """
        Detect if order is a stop loss.

        A stop loss is:
        - Type STOP (4) or STOP_LIMIT (3)
        - AND closing a position (SELL when we were long, BUY when we were short)
        """
        # Stop orders (types 3, 4, 5)
        if order.type in [3, 4, 5]:  # STOP_LIMIT, STOP, TRAILING_STOP
            return True
        return False

    def _is_take_profit(self, order) -> bool:
        """
        Detect if order is a take profit.

        A take profit is typically:
        - Type LIMIT (1)
        - AND closing a position at a profit target
        - AND has a limit price above entry (for longs) or below (for shorts)

        Note: Without position context, we use heuristics:
        - LIMIT orders that close positions are likely take profits
        - This is not 100% accurate but good enough for logging
        """
        # For now, we'll mark LIMIT orders that close positions as potential TPs
        # This is a heuristic since we don't have full position context here
        if order.type == 1:  # LIMIT
            # Could be enhanced with position tracking to confirm
            return False  # Conservative: don't assume unless we're certain
        return False

    # ============================================================================
    # OLD SignalR Callbacks (deprecated - keeping for reference)
    # ============================================================================

    async def _on_position_update_old(self, data: Any) -> None:
        """
        Handle position update from SignalR.

        SignalR sends data in format:
        [{'action': 1, 'data': {'contractId': 123, 'size': 2, ...}}]

        Actions:
        - 1 = Add/Update
        - 2 = Remove/Close
        """
        logger.debug(f"🔔 _on_position_update callback invoked (received {len(data) if isinstance(data, list) else 1} update(s))")
        try:
            if not isinstance(data, list):
                logger.warning(f"Position update not a list: {type(data)}")
                return

            for update in data:
                action = update.get('action', 0)
                position_data = update.get('data', {})

                # Extract position details
                contract_id = position_data.get('contractId')
                size = position_data.get('size', 0)
                avg_price = position_data.get('averagePrice', 0.0)
                unrealized_pnl = position_data.get('unrealizedPnl', 0.0)

                # Determine symbol from contract ID
                symbol = self._extract_symbol_from_contract(contract_id)

                logger.info("=" * 80)
                logger.info(f"📊 POSITION UPDATE - {symbol}")
                logger.info(
                    f"   Action: {action} | Size: {size} | Price: ${avg_price:.2f} | "
                    f"Unrealized P&L: ${unrealized_pnl:.2f}"
                )
                logger.info("=" * 80)

                # Determine event type based on action and size
                if action == 1 and size != 0:
                    # Position opened or updated
                    event_type = EventType.POSITION_UPDATED

                    risk_event = RiskEvent(
                        event_type=event_type,
                        data={
                            "symbol": symbol,
                            "contract_id": contract_id,
                            "size": size,
                            "side": "long" if size > 0 else "short",
                            "average_price": avg_price,
                            "unrealized_pnl": unrealized_pnl,
                            "raw_data": position_data,
                        },
                        source="trading_sdk",
                    )

                    await self.event_bus.publish(risk_event)
                    logger.debug(f"Bridged {event_type} event for {symbol}")

                elif action == 2 or (action == 1 and size == 0):
                    # Position closed
                    risk_event = RiskEvent(
                        event_type=EventType.POSITION_CLOSED,
                        data={
                            "symbol": symbol,
                            "contract_id": contract_id,
                            "realized_pnl": position_data.get('realizedPnl', 0.0),
                            "raw_data": position_data,
                        },
                        source="trading_sdk",
                    )

                    await self.event_bus.publish(risk_event)
                    logger.debug(f"Bridged POSITION_CLOSED event for {symbol}")

        except Exception as e:
            logger.error(f"Error handling position update: {e}")
            logger.exception(e)

    async def _on_order_update(self, data: Any) -> None:
        """
        Handle order update from SignalR.

        SignalR sends data in format:
        [{'action': 1, 'data': {'id': 123, 'status': 'Filled', ...}}]
        """
        logger.debug(f"🔔 _on_order_update callback invoked (received {len(data) if isinstance(data, list) else 1} update(s))")
        try:
            if not isinstance(data, list):
                logger.warning(f"Order update not a list: {type(data)}")
                return

            for update in data:
                action = update.get('action', 0)
                order_data = update.get('data', {})

                # Extract order details
                order_id = order_data.get('id')
                status = order_data.get('status', 'Unknown')
                side = order_data.get('side', 'Unknown')
                quantity = order_data.get('quantity', 0)
                price = order_data.get('price', 0.0)
                filled_quantity = order_data.get('filledQuantity', 0)
                contract_id = order_data.get('contractId')

                symbol = self._extract_symbol_from_contract(contract_id)

                logger.info("=" * 80)
                logger.info(f"📋 ORDER UPDATE - {symbol}")
                logger.info(
                    f"   ID: {order_id} | Status: {status} | Side: {side} | "
                    f"Qty: {quantity} | Filled: {filled_quantity}"
                )
                logger.info("=" * 80)

                # Map status to event type
                event_type = None
                if status in ['Working', 'Accepted', 'Pending']:
                    event_type = EventType.ORDER_PLACED
                elif status == 'Filled':
                    event_type = EventType.ORDER_FILLED
                elif status == 'Cancelled':
                    event_type = EventType.ORDER_CANCELLED
                elif status == 'Rejected':
                    event_type = EventType.ORDER_REJECTED

                if event_type:
                    risk_event = RiskEvent(
                        event_type=event_type,
                        data={
                            "symbol": symbol,
                            "order_id": order_id,
                            "status": status,
                            "side": side,
                            "quantity": quantity,
                            "price": price,
                            "filled_quantity": filled_quantity,
                            "raw_data": order_data,
                        },
                        source="trading_sdk",
                    )

                    await self.event_bus.publish(risk_event)
                    logger.debug(f"Bridged {event_type} event for {symbol}")

        except Exception as e:
            logger.error(f"Error handling order update: {e}")
            logger.exception(e)

    async def _on_trade_update(self, data: Any) -> None:
        """
        Handle trade update from SignalR.

        SignalR sends data in format:
        [{'action': 1, 'data': {'id': 123, 'price': 21500.0, ...}}]
        """
        logger.debug(f"🔔 _on_trade_update callback invoked (received {len(data) if isinstance(data, list) else 1} update(s))")
        try:
            if not isinstance(data, list):
                logger.warning(f"Trade update not a list: {type(data)}")
                return

            for update in data:
                action = update.get('action', 0)
                trade_data = update.get('data', {})

                # Extract trade details
                trade_id = trade_data.get('id')
                price = trade_data.get('price', 0.0)
                quantity = trade_data.get('quantity', 0)
                side = trade_data.get('side', 'Unknown')
                contract_id = trade_data.get('contractId')

                symbol = self._extract_symbol_from_contract(contract_id)

                logger.info("=" * 80)
                logger.info(f"💰 TRADE EXECUTED - {symbol}")
                logger.info(
                    f"   ID: {trade_id} | Side: {side} | Qty: {quantity} | "
                    f"Price: ${price:.2f}"
                )
                logger.info("=" * 80)

                risk_event = RiskEvent(
                    event_type=EventType.TRADE_EXECUTED,
                    data={
                        "symbol": symbol,
                        "trade_id": trade_id,
                        "side": side,
                        "quantity": quantity,
                        "price": price,
                        "raw_data": trade_data,
                    },
                    source="trading_sdk",
                )

                await self.event_bus.publish(risk_event)
                logger.debug(f"Bridged TRADE_EXECUTED event for {symbol}")

        except Exception as e:
            logger.error(f"Error handling trade update: {e}")
            logger.exception(e)

    async def _on_account_update(self, data: Any) -> None:
        """
        Handle account update from SignalR.

        Account updates are frequent (every few seconds) and mostly contain
        balance changes. We log them but don't forward to risk engine.
        """
        logger.debug(f"🔔 _on_account_update callback invoked (received {len(data) if isinstance(data, list) else 1} update(s))")
        try:
            if not isinstance(data, list):
                return

            for update in data:
                account_data = update.get('data', {})
                balance = account_data.get('balance', 0.0)
                realized_pnl = account_data.get('realizedPnl', 0.0)
                unrealized_pnl = account_data.get('unrealizedPnl', 0.0)

                # Log account updates with P&L info
                logger.info("=" * 80)
                logger.info(f"💼 ACCOUNT UPDATE")
                logger.info(
                    f"   Balance: ${balance:,.2f} | "
                    f"Realized P&L: ${realized_pnl:.2f} | "
                    f"Unrealized P&L: ${unrealized_pnl:.2f}"
                )
                logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Error handling account update: {e}")

    async def _on_quote_update(self, data: Any) -> None:
        """
        Handle market quote update from SignalR.

        Quote updates provide real-time bid/ask prices needed for:
        - Unrealized PnL calculations
        - RULE-004 (Daily Unrealized Loss)
        - RULE-005 (Max Unrealized Profit)
        - Position monitoring
        """
        try:
            if not isinstance(data, list):
                return

            for update in data:
                quote_data = update.get('data', {})

                # Extract quote details
                symbol = quote_data.get('symbol', 'UNKNOWN')
                bid = quote_data.get('bid', 0.0)
                ask = quote_data.get('ask', 0.0)
                last = quote_data.get('last', 0.0)

                # Use last price or midpoint for PnL calculations
                market_price = last if last > 0 else (bid + ask) / 2

                if market_price > 0:
                    logger.trace(f"Quote update: {symbol} @ {market_price:.2f} (bid: {bid:.2f}, ask: {ask:.2f})")

                    # Publish market price event for rules that need it
                    risk_event = RiskEvent(
                        event_type=EventType.MARKET_DATA_UPDATED,
                        data={
                            "symbol": symbol,
                            "price": market_price,
                            "bid": bid,
                            "ask": ask,
                            "last": last,
                            "timestamp": quote_data.get('timestamp'),
                        },
                        source="trading_sdk",
                    )

                    await self.event_bus.publish(risk_event)

        except Exception as e:
            logger.error(f"Error handling quote update: {e}")

    async def flatten_position(self, symbol: str) -> None:
        """Flatten a specific position."""
        if not self.suite:
            raise RuntimeError("Not connected")

        logger.warning(f"Flattening position for {symbol}")

        context = self.suite[symbol]

        # Use SDK's built-in close_all_positions() method
        # This is cleaner than manually placing opposite orders
        try:
            await context.positions.close_all_positions()
            logger.info(f"✅ Closed all positions for {symbol} via SDK")
        except Exception as e:
            logger.error(f"❌ Failed to close positions for {symbol}: {e}")
            # Fallback: manual approach if SDK method fails
            logger.warning(f"Attempting manual position closing for {symbol}")
            positions = await context.positions.get_all_positions()

            for position in positions:
                if position.size != 0:
                    # Close position by trading opposite side
                    side = 1 if position.size > 0 else 0  # 0=buy, 1=sell
                    await context.orders.place_market_order(
                        contract_id=position.contractId,
                        side=side,
                        size=abs(position.size),
                    )
                    logger.info(f"Closed {symbol} position: {position.size} contracts (manual)")

    async def flatten_all(self) -> None:
        """Flatten all positions across all instruments."""
        logger.warning("FLATTENING ALL POSITIONS")

        for symbol in self.instruments:
            await self.flatten_position(symbol)

    def get_stats(self) -> dict[str, Any]:
        """Get trading integration statistics."""
        return {
            "connected": self.suite is not None,
            "running": self.running,
            "instruments": self.instruments,
        }
