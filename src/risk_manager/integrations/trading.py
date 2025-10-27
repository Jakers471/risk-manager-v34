"""Trading integration using Project-X-Py SDK."""

import asyncio
import os
from typing import Any

from loguru import logger
from project_x_py import ProjectX, TradingSuite, EventType as SDKEventType
from project_x_py.realtime import ProjectXRealtimeClient

from risk_manager.core.config import RiskConfig
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

        logger.info(f"Trading integration initialized for: {instruments}")

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
                features=["orderbook", "statistics"],  # Enable orderbook and statistics
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

        self.running = True
        logger.info("Starting trading event monitoring...")

        try:
            # Subscribe to position updates via DIRECT realtime callback
            await self.realtime.add_callback(
                "position_update",
                lambda data: asyncio.create_task(self._on_position_update(data))
            )
            logger.debug("✅ Registered callback: position_update")

            # Subscribe to order updates via DIRECT realtime callback
            await self.realtime.add_callback(
                "order_update",
                lambda data: asyncio.create_task(self._on_order_update(data))
            )
            logger.debug("✅ Registered callback: order_update")

            # Subscribe to trade updates via DIRECT realtime callback
            await self.realtime.add_callback(
                "trade_update",
                lambda data: asyncio.create_task(self._on_trade_update(data))
            )
            logger.debug("✅ Registered callback: trade_update")

            # Subscribe to account updates for logging
            await self.realtime.add_callback(
                "account_update",
                lambda data: asyncio.create_task(self._on_account_update(data))
            )
            logger.debug("✅ Registered callback: account_update")

            logger.success("✅ Trading monitoring started (4 realtime callbacks registered)")

        except Exception as e:
            logger.error(f"Failed to register realtime callbacks: {e}")
            raise

    async def _on_position_update(self, data: Any) -> None:
        """
        Handle position update from SignalR.

        SignalR sends data in format:
        [{'action': 1, 'data': {'contractId': 123, 'size': 2, ...}}]

        Actions:
        - 1 = Add/Update
        - 2 = Remove/Close
        """
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

                # Determine symbol from contract (you may need to map this)
                symbol = self.instruments[0] if self.instruments else "UNKNOWN"

                logger.info(
                    f"📨 Position update for {symbol}: "
                    f"action={action}, size={size}, price={avg_price:.2f}, "
                    f"pnl={unrealized_pnl:.2f}"
                )

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

                symbol = self.instruments[0] if self.instruments else "UNKNOWN"

                logger.info(
                    f"📨 Order update for {symbol}: "
                    f"id={order_id}, status={status}, side={side}, "
                    f"qty={quantity}, filled={filled_quantity}"
                )

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

                symbol = self.instruments[0] if self.instruments else "UNKNOWN"

                logger.info(
                    f"📨 Trade update for {symbol}: "
                    f"id={trade_id}, side={side}, qty={quantity}, price={price:.2f}"
                )

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
        try:
            if not isinstance(data, list):
                return

            for update in data:
                account_data = update.get('data', {})
                balance = account_data.get('balance', 0.0)

                # Only log significant updates
                logger.trace(f"Account update: balance=${balance:,.2f}")

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

    def get_stats(self) -> dict[str, Any]:
        """Get trading integration statistics."""
        return {
            "connected": self.suite is not None,
            "running": self.running,
            "instruments": self.instruments,
        }
