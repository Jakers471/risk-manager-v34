"""Trading integration using Project-X-Py SDK."""

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

        except Exception as e:
            logger.error(f"Failed to connect to trading platform: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from trading platform."""
        logger.info("Disconnecting from trading platform...")

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

            # Subscribe to POSITION events via suite EventBus (using SDK EventType)
            await self.suite.on(SDKEventType.POSITION_OPENED, self._on_position_opened)
            logger.info("✅ Registered: POSITION_OPENED")

            await self.suite.on(SDKEventType.POSITION_CLOSED, self._on_position_closed)
            logger.info("✅ Registered: POSITION_CLOSED")

            await self.suite.on(SDKEventType.POSITION_UPDATED, self._on_position_updated)
            logger.info("✅ Registered: POSITION_UPDATED")

            logger.success("✅ Trading monitoring started (8 event handlers registered)")
            logger.info("📡 Listening for events: ORDER, POSITION")
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

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_placed", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)

            logger.info("=" * 80)
            logger.info(f"📋 ORDER PLACED - {symbol}")
            logger.info(f"   ID: {order.id} | Side: {self._get_side_name(order.side)} | Qty: {order.size}")
            logger.info("=" * 80)

            # Bridge to risk event bus
            risk_event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={
                    "symbol": symbol,
                    "order_id": order.id,
                    "side": self._get_side_name(order.side),
                    "quantity": order.size,
                    "price": getattr(order, 'limitPrice', None),
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

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_filled", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)

            logger.info("=" * 80)
            logger.info(f"💰 ORDER FILLED - {symbol}")
            logger.info(
                f"   ID: {order.id} | Side: {self._get_side_name(order.side)} | "
                f"Qty: {order.fillVolume} @ ${order.filledPrice:.2f}"
            )
            logger.info("=" * 80)

            # Bridge to risk event bus
            risk_event = RiskEvent(
                event_type=EventType.ORDER_FILLED,
                data={
                    "symbol": symbol,
                    "order_id": order.id,
                    "side": self._get_side_name(order.side),
                    "quantity": order.fillVolume,
                    "price": order.filledPrice,
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
            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_partial_fill", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)

            logger.info("=" * 80)
            logger.info(f"📊 ORDER PARTIALLY FILLED - {symbol}")
            logger.info(
                f"   ID: {order.id} | Filled: {order.fillVolume}/{order.size} @ ${order.filledPrice:.2f}"
            )
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Error handling ORDER_PARTIAL_FILL: {e}")

    async def _on_order_cancelled(self, event) -> None:
        """Handle ORDER_CANCELLED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_CANCELLED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}
            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_cancelled", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)

            logger.info("=" * 80)
            logger.info(f"❌ ORDER CANCELLED - {symbol}")
            logger.info(f"   ID: {order.id}")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Error handling ORDER_CANCELLED: {e}")

    async def _on_order_rejected(self, event) -> None:
        """Handle ORDER_REJECTED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_REJECTED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}
            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_rejected", str(order.id)):
                return

            symbol = self._extract_symbol_from_contract(order.contractId)

            logger.warning("=" * 80)
            logger.warning(f"⛔ ORDER REJECTED - {symbol}")
            logger.warning(f"   ID: {order.id}")
            logger.warning("=" * 80)

        except Exception as e:
            logger.error(f"Error handling ORDER_REJECTED: {e}")

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

            # Check for duplicate (prevents 3x events from 3 instruments)
            # Use contract_id + action for deduplication key
            dedup_key = f"{contract_id}_{action_name}"
            if self._is_duplicate_event(f"position_{action_name.lower()}", dedup_key):
                return

            symbol = self._extract_symbol_from_contract(contract_id)

            logger.info("=" * 80)
            logger.info(f"📊 POSITION {action_name} - {symbol}")
            logger.info(
                f"   Type: {self._get_position_type_name(pos_type)} | Size: {size} | "
                f"Price: ${avg_price:.2f} | Unrealized P&L: ${unrealized_pnl:.2f}"
            )
            logger.info("=" * 80)

            # Bridge to risk event bus
            event_type_map = {
                "OPENED": EventType.POSITION_UPDATED,
                "CLOSED": EventType.POSITION_UPDATED,
                "UPDATED": EventType.POSITION_UPDATED,
            }

            risk_event = RiskEvent(
                event_type=event_type_map.get(action_name, EventType.POSITION_UPDATED),
                data={
                    "symbol": symbol,
                    "contract_id": contract_id,
                    "size": size,
                    "side": "long" if size > 0 else "short" if size < 0 else "flat",
                    "average_price": avg_price,
                    "unrealized_pnl": unrealized_pnl,
                    "action": action_name.lower(),
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
