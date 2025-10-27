"""
Event Bridge - SDK to Risk Engine

Bridges events from the Project-X SDK REALTIME CLIENT to the Risk Engine EventBus.
Maps SignalR callback events to RiskEvent types for rule processing.

IMPORTANT: This uses DIRECT realtime callbacks, NOT the SDK EventBus.
The SDK's EventBus does not emit position/order/trade events, so we
subscribe directly to the realtime_client callbacks where those events
actually arrive from SignalR.
"""

import asyncio
from datetime import datetime
from typing import Any

from loguru import logger
from project_x_py import TradingSuite

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.sdk.suite_manager import SuiteManager


class EventBridge:
    """
    Bridges events between SDK Realtime Client and Risk Engine.

    ARCHITECTURE CHANGE:
    - OLD: Subscribe to suite.event_bus (broken - position events never emitted)
    - NEW: Subscribe directly to suite.realtime.add_callback() (working!)

    Maps SignalR callbacks to RiskEvents:
    - "position_update" → POSITION_OPENED, POSITION_CLOSED, POSITION_UPDATED
    - "order_update" → ORDER_PLACED, ORDER_FILLED, ORDER_CANCELLED, ORDER_REJECTED
    - "trade_update" → TRADE_EXECUTED
    - "account_update" → (logged but not forwarded)
    """

    def __init__(self, suite_manager: SuiteManager, risk_event_bus: EventBus):
        """
        Initialize the event bridge.

        Args:
            suite_manager: SuiteManager for accessing TradingSuites
            risk_event_bus: Risk engine's EventBus for publishing events
        """
        self.suite_manager = suite_manager
        self.risk_event_bus = risk_event_bus
        self.running = False
        self._subscription_tasks: list[asyncio.Task[Any]] = []

        logger.info("EventBridge initialized (using direct realtime callbacks)")

    async def start(self) -> None:
        """Start bridging events from all active suites."""
        self.running = True
        logger.info("EventBridge started")

        # Subscribe to events from all existing suites
        for symbol, suite in self.suite_manager.get_all_suites().items():
            await self._subscribe_to_suite(symbol, suite)

    async def stop(self) -> None:
        """Stop bridging events."""
        self.running = False
        logger.info("Stopping EventBridge...")

        # Cancel all subscription tasks
        for task in self._subscription_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._subscription_tasks.clear()
        logger.success("EventBridge stopped")

    async def _subscribe_to_suite(self, symbol: str, suite: TradingSuite) -> None:
        """
        Subscribe to events from a specific TradingSuite.

        Uses DIRECT realtime callbacks, bypassing the SDK EventBus.

        Args:
            symbol: Instrument symbol
            suite: TradingSuite instance
        """
        logger.info(f"Subscribing to realtime events for {symbol}")

        # Get the realtime client (where events actually arrive!)
        if not hasattr(suite, "realtime") or not suite.realtime:
            logger.warning(f"Suite for {symbol} has no realtime client")
            return

        realtime_client = suite.realtime

        try:
            # Subscribe to position updates via DIRECT callback
            # This is where TopstepX SignalR sends position data
            await realtime_client.add_callback(
                "position_update",
                lambda data: asyncio.create_task(
                    self._on_position_update(symbol, data)
                )
            )
            logger.debug(f"✅ Registered callback: position_update for {symbol}")

            # Subscribe to order updates via DIRECT callback
            await realtime_client.add_callback(
                "order_update",
                lambda data: asyncio.create_task(
                    self._on_order_update(symbol, data)
                )
            )
            logger.debug(f"✅ Registered callback: order_update for {symbol}")

            # Subscribe to trade updates via DIRECT callback
            await realtime_client.add_callback(
                "trade_update",
                lambda data: asyncio.create_task(
                    self._on_trade_update(symbol, data)
                )
            )
            logger.debug(f"✅ Registered callback: trade_update for {symbol}")

            # Subscribe to account updates for logging (optional)
            await realtime_client.add_callback(
                "account_update",
                lambda data: asyncio.create_task(
                    self._on_account_update(symbol, data)
                )
            )
            logger.debug(f"✅ Registered callback: account_update for {symbol}")

            logger.success(f"Subscribed to 4 realtime callbacks for {symbol}")

        except Exception as e:
            logger.error(f"Failed to subscribe to realtime events for {symbol}: {e}")
            raise

    # ============================================================================
    # POSITION EVENT HANDLERS - Parse SignalR data format
    # ============================================================================

    async def _on_position_update(self, symbol: str, data: Any) -> None:
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
                logger.warning(f"Position update for {symbol} not a list: {type(data)}")
                return

            for update in data:
                action = update.get('action', 0)
                position_data = update.get('data', {})

                # Extract position details
                contract_id = position_data.get('contractId')
                size = position_data.get('size', 0)
                avg_price = position_data.get('averagePrice', 0.0)
                unrealized_pnl = position_data.get('unrealizedPnl', 0.0)

                logger.info(
                    f"📨 Position update for {symbol}: "
                    f"action={action}, size={size}, price={avg_price:.2f}, "
                    f"pnl={unrealized_pnl:.2f}"
                )

                # Determine event type based on action and size
                if action == 1 and size != 0:
                    # Position opened or updated
                    # Check if this is a new position (could track previous state)
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
                            "timestamp": datetime.utcnow().isoformat(),
                            "raw_data": position_data,
                        }
                    )

                    await self.risk_event_bus.publish(risk_event)
                    logger.debug(f"Bridged {event_type} event for {symbol}")

                elif action == 2 or (action == 1 and size == 0):
                    # Position closed
                    risk_event = RiskEvent(
                        event_type=EventType.POSITION_CLOSED,
                        data={
                            "symbol": symbol,
                            "contract_id": contract_id,
                            "realized_pnl": position_data.get('realizedPnl', 0.0),
                            "timestamp": datetime.utcnow().isoformat(),
                            "raw_data": position_data,
                        }
                    )

                    await self.risk_event_bus.publish(risk_event)
                    logger.debug(f"Bridged POSITION_CLOSED event for {symbol}")

        except Exception as e:
            logger.error(f"Error handling position update for {symbol}: {e}")
            logger.exception(e)

    # ============================================================================
    # ORDER EVENT HANDLERS - Parse SignalR data format
    # ============================================================================

    async def _on_order_update(self, symbol: str, data: Any) -> None:
        """
        Handle order update from SignalR.

        SignalR sends data in format:
        [{'action': 1, 'data': {'id': 123, 'status': 'Filled', ...}}]
        """
        try:
            if not isinstance(data, list):
                logger.warning(f"Order update for {symbol} not a list: {type(data)}")
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
                            "timestamp": datetime.utcnow().isoformat(),
                            "raw_data": order_data,
                        }
                    )

                    await self.risk_event_bus.publish(risk_event)
                    logger.debug(f"Bridged {event_type} event for {symbol}")

        except Exception as e:
            logger.error(f"Error handling order update for {symbol}: {e}")
            logger.exception(e)

    # ============================================================================
    # TRADE EVENT HANDLERS - Parse SignalR data format
    # ============================================================================

    async def _on_trade_update(self, symbol: str, data: Any) -> None:
        """
        Handle trade update from SignalR.

        SignalR sends data in format:
        [{'action': 1, 'data': {'id': 123, 'price': 21500.0, ...}}]
        """
        try:
            if not isinstance(data, list):
                logger.warning(f"Trade update for {symbol} not a list: {type(data)}")
                return

            for update in data:
                action = update.get('action', 0)
                trade_data = update.get('data', {})

                # Extract trade details
                trade_id = trade_data.get('id')
                price = trade_data.get('price', 0.0)
                quantity = trade_data.get('quantity', 0)
                side = trade_data.get('side', 'Unknown')

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
                        "timestamp": datetime.utcnow().isoformat(),
                        "raw_data": trade_data,
                    }
                )

                await self.risk_event_bus.publish(risk_event)
                logger.debug(f"Bridged TRADE_EXECUTED event for {symbol}")

        except Exception as e:
            logger.error(f"Error handling trade update for {symbol}: {e}")
            logger.exception(e)

    # ============================================================================
    # ACCOUNT EVENT HANDLERS - For logging only
    # ============================================================================

    async def _on_account_update(self, symbol: str, data: Any) -> None:
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

                # Only log significant balance changes
                logger.trace(f"Account update for {symbol}: balance=${balance:,.2f}")

        except Exception as e:
            logger.error(f"Error handling account update for {symbol}: {e}")

    # ============================================================================
    # INSTRUMENT MANAGEMENT
    # ============================================================================

    async def add_instrument(self, symbol: str, suite: TradingSuite) -> None:
        """
        Start bridging events for a newly added instrument.

        Args:
            symbol: Instrument symbol
            suite: TradingSuite instance
        """
        if self.running:
            await self._subscribe_to_suite(symbol, suite)
            logger.info(f"EventBridge now monitoring {symbol}")
