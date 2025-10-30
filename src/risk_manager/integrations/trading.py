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
from risk_manager.integrations.sdk.order_correlator import OrderCorrelator
from risk_manager.integrations.sdk.event_router import EventRouter


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

        # Order correlator (correlates fills with position closes for exit type detection)
        # NEW: Delegated to OrderCorrelator module
        self._order_correlator = OrderCorrelator(ttl=2.0)

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

        # Event router (handles ALL SDK event callbacks)
        # NEW: Routes events to specialized processors and publishes to risk event bus
        self._event_router = EventRouter(
            protective_cache=self._protective_cache,
            order_correlator=self._order_correlator,
            pnl_calculator=self.pnl_calculator,
            order_polling=self._order_polling,
            event_bus=event_bus,
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

            # Wire up event router with SDK access and helper functions
            self._event_router.set_client(self.client)
            self._event_router.set_suite(self.suite)
            self._event_router.set_helper_functions(
                extract_symbol_fn=self._extract_symbol_from_contract,
                get_stop_loss_fn=self.get_stop_loss_for_position,
                get_take_profit_fn=self.get_take_profit_for_position,
            )
            logger.debug("Wired EventRouter to SDK client, suite, and helper functions")

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
            logger.info("Registering event callbacks via suite.on() → EventRouter...")

            # Subscribe to ORDER events via suite EventBus (delegated to EventRouter)
            await self.suite.on(SDKEventType.ORDER_PLACED, self._event_router._on_order_placed)
            logger.info("✅ Registered: ORDER_PLACED → EventRouter")

            await self.suite.on(SDKEventType.ORDER_FILLED, self._event_router._on_order_filled)
            logger.info("✅ Registered: ORDER_FILLED → EventRouter")

            await self.suite.on(SDKEventType.ORDER_PARTIAL_FILL, self._event_router._on_order_partial_fill)
            logger.info("✅ Registered: ORDER_PARTIAL_FILL → EventRouter")

            await self.suite.on(SDKEventType.ORDER_CANCELLED, self._event_router._on_order_cancelled)
            logger.info("✅ Registered: ORDER_CANCELLED → EventRouter")

            await self.suite.on(SDKEventType.ORDER_REJECTED, self._event_router._on_order_rejected)
            logger.info("✅ Registered: ORDER_REJECTED → EventRouter")

            await self.suite.on(SDKEventType.ORDER_MODIFIED, self._event_router._on_order_modified)
            logger.info("✅ Registered: ORDER_MODIFIED → EventRouter")

            await self.suite.on(SDKEventType.ORDER_EXPIRED, self._event_router._on_order_expired)
            logger.info("✅ Registered: ORDER_EXPIRED → EventRouter")

            # Subscribe to POSITION events via suite EventBus (delegated to EventRouter)
            await self.suite.on(SDKEventType.POSITION_OPENED, self._event_router._on_position_opened)
            logger.info("✅ Registered: POSITION_OPENED → EventRouter")

            await self.suite.on(SDKEventType.POSITION_CLOSED, self._event_router._on_position_closed)
            logger.info("✅ Registered: POSITION_CLOSED → EventRouter")

            await self.suite.on(SDKEventType.POSITION_UPDATED, self._event_router._on_position_updated)
            logger.info("✅ Registered: POSITION_UPDATED → EventRouter")

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
