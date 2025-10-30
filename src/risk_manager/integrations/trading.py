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
from risk_manager.integrations.adapters import adapter
from risk_manager.errors import MappingError, UnitsError
from risk_manager.integrations.tick_economics import (
    get_tick_economics_safe,
    get_tick_economics_and_values,
    normalize_symbol,
    UnitsError,
    MappingError,
    TICK_VALUES,
    ALIASES,
)
from risk_manager.integrations.unrealized_pnl import UnrealizedPnLCalculator
from risk_manager.integrations.sdk.protective_orders import ProtectiveOrderCache
from risk_manager.integrations.sdk.market_data import MarketDataHandler
from risk_manager.integrations.sdk.order_polling import OrderPollingService


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

        # Order polling service (to detect protective stops that don't emit events)
        # NEW: Delegated to OrderPollingService module
        self._order_polling = OrderPollingService()

        # Recent order fills tracking (for correlating position updates with stop losses)
        # Format: {contract_id: {"type": "stop_loss"|"take_profit"|"manual", "timestamp": float, "side": str, "order_id": int, "fill_price": float}}
        self._recent_fills: dict[str, dict[str, Any]] = {}
        self._recent_fills_ttl = 2.0  # seconds - window to correlate fills with position updates

        # Protective order cache (stop loss and take profit)
        # NEW: Delegated to ProtectiveOrderCache module
        self._protective_cache = ProtectiveOrderCache()

        # Unrealized P&L calculator (for both floating and realized P&L)
        # MUST be created BEFORE MarketDataHandler (which depends on it)
        self.pnl_calculator = UnrealizedPnLCalculator()

        # Market data handler (quote updates, price polling, status bar)
        # NEW: Delegated to MarketDataHandler module
        self._market_data = MarketDataHandler(
            pnl_calculator=self.pnl_calculator,
            event_bus=event_bus,
            instruments=instruments
        )

        # Status bar update task is now managed by MarketDataHandler

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
        # Delegate to protective order cache
        return await self._protective_cache.get_stop_loss(
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
        # Delegate to protective order cache
        return await self._protective_cache.get_take_profit(
            contract_id, position_entry_price, position_type
        )

    def get_all_active_stop_losses(self) -> dict[str, dict[str, Any]]:
        """
        Get all active stop loss orders across all positions.

        Returns:
            Dict mapping contract_id to stop loss data
        """
        # Delegate to protective order cache
        return self._protective_cache.get_all_stop_losses()

    def get_all_active_take_profits(self) -> dict[str, dict[str, Any]]:
        """
        Get all active take profit orders across all positions.

        Returns:
            Dict mapping contract_id to take profit data
        """
        # Delegate to protective order cache
        return self._protective_cache.get_all_take_profits()

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

            # Wire up protective order cache with SDK access
            self._protective_cache.set_suite(self.suite)
            self._protective_cache.set_helpers(
                self._extract_symbol_from_contract,
                self._get_side_name
            )
            logger.debug("Wired ProtectiveOrderCache to SDK suite")

            # Wire up market data handler with SDK access
            self._market_data.set_client(self.client)
            self._market_data.set_suite(self.suite)
            logger.debug("Wired MarketDataHandler to SDK client and suite")

            # Wire up order polling service with SDK access
            self._order_polling.set_suite(self.suite)
            self._order_polling.set_protective_cache(self._protective_cache)
            self._order_polling.set_helpers(
                self._extract_symbol_from_contract,
                self._get_side_name
            )
            logger.debug("Wired OrderPollingService to SDK suite and protective cache")

        except Exception as e:
            logger.error(f"Failed to connect to trading platform: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from trading platform."""
        logger.info("Disconnecting from trading platform...")

        # Stop background tasks
        self.running = False

        # Stop order polling (delegated to OrderPollingService)
        await self._order_polling.stop_polling()
        logger.debug("Order polling task stopped (OrderPollingService)")

        # Stop status bar (delegated to MarketDataHandler)
        await self._market_data.stop_status_bar()
        logger.debug("Status bar task stopped (MarketDataHandler)")

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

            # Subscribe to market data events for unrealized P&L tracking
            # Try multiple event types since realtime_data manager doesn't exist
            logger.info("📊 Registering market data event handlers...")

            # QUOTE_UPDATE (primary) - Delegated to MarketDataHandler
            await self.suite.on(SDKEventType.QUOTE_UPDATE, self._market_data.handle_quote_update)
            logger.info("✅ Registered: QUOTE_UPDATE (MarketDataHandler)")

            # DATA_UPDATE (alternative - might contain price data) - Delegated to MarketDataHandler
            await self.suite.on(SDKEventType.DATA_UPDATE, self._market_data.handle_data_update)
            logger.info("✅ Registered: DATA_UPDATE (MarketDataHandler)")

            # TRADE_TICK (alternative - trade executions with prices) - Delegated to MarketDataHandler
            await self.suite.on(SDKEventType.TRADE_TICK, self._market_data.handle_trade_tick)
            logger.info("✅ Registered: TRADE_TICK (MarketDataHandler)")

            # NEW_BAR (from timeframes - contains OHLC data including close price) - Delegated to MarketDataHandler
            await self.suite.on(SDKEventType.NEW_BAR, self._market_data.handle_new_bar)
            logger.info("✅ Registered: NEW_BAR (1min, 5min timeframes - MarketDataHandler)")

            # Check instrument structure and initial prices
            logger.info("Checking instruments for price data...")
            for symbol in self.instruments:
                try:
                    instrument = self.suite[symbol]
                    attrs = [attr for attr in dir(instrument) if not attr.startswith('_')]
                    logger.debug(f"{symbol} attributes: {attrs[:20]}")
                    logger.debug(f"{symbol} type: {type(instrument)}")

                    # SDK v3.5.9 doesn't have last_price on instruments
                    # Prices come via QUOTE_UPDATE events instead
                    logger.info(f"  ℹ️  {symbol} - prices will come from QUOTE_UPDATE events")

                    if hasattr(instrument, 'data'):
                        logger.debug(f"  {symbol} has data attribute: {type(instrument.data)}")
                        # Try to access data
                        try:
                            if instrument.data and hasattr(instrument.data, '1min'):
                                bars_1min = instrument.data['1min']
                                if bars_1min and len(bars_1min) > 0:
                                    latest_bar = bars_1min[-1]
                                    logger.info(f"  📊 {symbol} has 1min bar data, latest close: ${latest_bar.get('close', 'N/A')}")
                        except Exception as e:
                            logger.debug(f"  Error accessing {symbol} bar data: {e}")

                    if hasattr(instrument, 'current_price'):
                        logger.debug(f"  {symbol} has current_price: ${instrument.current_price}")

                except Exception as e:
                    logger.debug(f"Error inspecting {symbol}: {e}")

            # Catch-all disabled - too noisy with market data events
            # If you need to debug new events, uncomment this block:
            # for event_type in SDKEventType:
            #     if event_type.name not in [...known events...]:
            #         await self.suite.on(event_type, self._on_unknown_event)

            logger.success("✅ Trading monitoring started (14 event handlers registered)")
            logger.info("📡 Listening for events: ORDER (8 types), POSITION (3 types), MARKET DATA (4 types)")

            # Start order polling task (to catch protective stops that don't emit events) - Delegated to OrderPollingService
            await self._order_polling.start_polling()
            logger.info("🔄 Started order polling task (5s interval - OrderPollingService)")

            # Start status bar update task (for real-time P&L display) - Delegated to MarketDataHandler
            await self._market_data.start_status_bar()
            logger.info("📊 Started unrealized P&L status bar (0.5s refresh - MarketDataHandler)")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Failed to register realtime callbacks: {e}")
            raise

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

            # Cache active protective orders (delegated to cache module)
            self._protective_cache.update_from_order_placed(order)

            # Mark order as seen by polling service (prevents duplicate logging)
            self._order_polling.mark_order_seen(order.id)

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

            # Remove from known orders (it's filled now) - Delegated to OrderPollingService
            self._order_polling.mark_order_unseen(order.id)

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
            if is_sl:
                self._protective_cache.remove_stop_loss(order.contractId)

            if is_tp:
                self._protective_cache.remove_take_profit(order.contractId)

            # Bridge to risk event bus
            risk_event = RiskEvent(
                event_type=EventType.ORDER_FILLED,
                data={
                    "account_id": order.accountId,  # ← CRITICAL: Rules need account_id
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

            # Remove from known orders (it's cancelled now) - Delegated to OrderPollingService
            self._order_polling.mark_order_unseen(order.id)

            # Remove from active caches (order is now cancelled)
            # Note: Cache removal is idempotent (safe to call even if not in cache)
            self._protective_cache.remove_stop_loss(order.contractId)
            self._protective_cache.remove_take_profit(order.contractId)

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
            self._protective_cache.invalidate(contract_id)
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
                self._protective_cache.invalidate(contract_id)

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
                logger.debug("Invalidating protective order cache")
                self._protective_cache.invalidate(contract_id)

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

            # Calculate realized P&L for CLOSED positions (delegated to UnrealizedPnLCalculator)
            # SDK doesn't provide profitAndLoss, so we calculate it ourselves!
            realized_pnl = None
            if action_name == "CLOSED":
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

                # Calculate realized P&L using consolidated calculator
                realized_pnl_decimal = self.pnl_calculator.calculate_realized_pnl(contract_id, exit_price)

                if realized_pnl_decimal is not None:
                    realized_pnl = float(realized_pnl_decimal)

                    # Log P&L details
                    logger.info(f"💰 Realized P&L: ${realized_pnl:+,.2f}")
                    logger.debug(f"   Exit price: ${exit_price:,.2f}")

                    # Remove from unrealized P&L calculator
                    self.pnl_calculator.remove_position(contract_id)
                else:
                    logger.warning(f"⚠️  Position closed but not tracked! Can't calculate P&L for {contract_id}")

            # Track OPENED positions for P&L calculation (consolidated in UnrealizedPnLCalculator)
            elif action_name == "OPENED":
                side = 'long' if size > 0 else 'short'

                # Track position in consolidated calculator (handles both unrealized and realized P&L)
                self.pnl_calculator.update_position(contract_id, {
                    'price': avg_price,
                    'size': size,
                    'side': side,
                    'symbol': symbol,
                })
                logger.debug(f"📝 Position tracked in calculator: {contract_id} @ ${avg_price:,.2f} x {size} ({side})")

                # IMMEDIATE: Try to get current price and seed the calculator
                # This gives us an initial P&L even if polling hasn't started yet
                try:
                    instrument = self.suite.get(symbol)
                    if instrument and hasattr(instrument, 'last_price') and instrument.last_price:
                        current_price = instrument.last_price
                        if current_price > 0:
                            self.pnl_calculator.update_quote(symbol, current_price)
                            logger.info(f"  💹 Initial price loaded: {symbol} @ ${current_price:.2f}")
                except Exception as e:
                    logger.debug(f"Could not get initial price for {symbol}: {e}")

            risk_event = RiskEvent(
                event_type=event_type_map.get(action_name, EventType.POSITION_UPDATED),
                data={
                    "account_id": self.client.account_info.id if self.client else None,  # ← CRITICAL: Rules need account_id
                    "symbol": symbol,
                    "contractId": contract_id,  # ← CRITICAL: Rules need contractId (for enforcement)
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

            # ============================================================================
            # SHADOW MODE: Canonical Domain Model (No Behavior Change)
            # ============================================================================
            # Convert SDK position to canonical Position type
            # This runs in parallel with existing dict-based event.data
            # Rules can gradually migrate from event.data to event.position
            try:
                # Skip adapter for FLAT/CLOSED positions (type=0)
                # Adapter only handles LONG (1) and SHORT (2)
                if action_name == "CLOSED" or pos_type == 0 or size == 0:
                    logger.debug(f"  ⚠️  Skipping adapter for FLAT position (shadow mode)")
                    risk_event.position = None
                else:
                    # Get current market price for P&L calculation
                    current_price = None
                    if self.suite and hasattr(self.suite, 'get'):
                        try:
                            instrument = self.suite.get(symbol)
                            if instrument and hasattr(instrument, 'last_price'):
                                current_price = instrument.last_price
                        except (KeyError, AttributeError):
                            pass  # No market price available yet

                    # Convert to canonical Position
                    canonical_position = adapter.normalize_position_from_dict(
                        position_data={
                            "contractId": contract_id,
                            "avgPrice": avg_price,
                            "size": size,
                            "type": pos_type,
                        },
                        current_price=current_price,
                        account_id=None,  # Will be added when we have account context
                    )

                    # Attach canonical position to event (shadow mode - doesn't break existing code)
                    risk_event.position = canonical_position

                    # Log the normalization for visibility
                    logger.info(
                        f"  🔄 CANONICAL: {symbol} → {canonical_position.symbol_root} | "
                        f"Side: {canonical_position.side.value.upper()} | "
                        f"Qty: {canonical_position.quantity} | "
                        f"P&L: {canonical_position.unrealized_pnl}"
                    )

            except (MappingError, UnitsError) as e:
                # Log adapter errors but don't crash - shadow mode is best-effort
                logger.warning(f"  ⚠️  Adapter error (shadow mode): {e}")
                risk_event.position = None

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

    def get_total_unrealized_pnl(self) -> float:
        """
        Get total unrealized P&L across all open positions.

        Used by RULE-004 (Daily Unrealized Loss).

        Returns:
            Total unrealized P&L in USD
        """
        total = self.pnl_calculator.calculate_total_unrealized_pnl()
        return float(total)

    def get_position_unrealized_pnl(self, contract_id: str) -> float | None:
        """
        Get unrealized P&L for a specific position.

        Used by RULE-005 (Max Unrealized Profit).

        Args:
            contract_id: Position identifier

        Returns:
            Unrealized P&L in USD, or None if position not found
        """
        pnl = self.pnl_calculator.calculate_unrealized_pnl(contract_id)
        return float(pnl) if pnl is not None else None

    def get_open_positions(self) -> dict[str, dict[str, Any]]:
        """
        Get all currently open positions.

        Returns:
            Dictionary of {contract_id: position_data}
        """
        return self.pnl_calculator.get_open_positions()

    def get_stats(self) -> dict[str, Any]:
        """Get trading integration statistics."""
        return {
            "connected": self.suite is not None,
            "running": self.running,
            "instruments": self.instruments,
        }
