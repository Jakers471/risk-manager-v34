"""
Event Bridge - SDK to Risk Engine

Bridges events from the Project-X SDK EventBus to the Risk Engine EventBus.
Maps SDK event types to RiskEvent types for rule processing.
"""

import asyncio
from typing import Any

from loguru import logger
from project_x_py import EventType as SDKEventType
from project_x_py import TradingSuite

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.sdk.suite_manager import SuiteManager


class EventBridge:
    """
    Bridges events between SDK and Risk Engine.

    Maps SDK events to RiskEvents:
    - SDK Trade events → TRADE_EXECUTED, ORDER_FILLED
    - SDK Position events → POSITION_OPENED, POSITION_CLOSED, POSITION_UPDATED
    - SDK Order events → ORDER_PLACED, ORDER_CANCELLED, ORDER_REJECTED
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

        logger.info("EventBridge initialized")

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

        Args:
            symbol: Instrument symbol
            suite: TradingSuite instance
        """
        logger.info(f"Subscribing to events for {symbol}")

        # Get SDK's EventBus
        if not hasattr(suite, "event_bus"):
            logger.warning(f"Suite for {symbol} has no event_bus")
            return

        sdk_event_bus = suite.event_bus

        # Subscribe to trade events
        sdk_event_bus.subscribe(
            SDKEventType.TRADE_EXECUTED,
            lambda event: self._on_trade_executed(symbol, event)
        )

        # Subscribe to position events
        sdk_event_bus.subscribe(
            SDKEventType.POSITION_OPENED,
            lambda event: self._on_position_opened(symbol, event)
        )
        sdk_event_bus.subscribe(
            SDKEventType.POSITION_CLOSED,
            lambda event: self._on_position_closed(symbol, event)
        )
        sdk_event_bus.subscribe(
            SDKEventType.POSITION_UPDATED,
            lambda event: self._on_position_updated(symbol, event)
        )

        # Subscribe to order events
        sdk_event_bus.subscribe(
            SDKEventType.ORDER_PLACED,
            lambda event: self._on_order_placed(symbol, event)
        )
        sdk_event_bus.subscribe(
            SDKEventType.ORDER_FILLED,
            lambda event: self._on_order_filled(symbol, event)
        )
        sdk_event_bus.subscribe(
            SDKEventType.ORDER_CANCELLED,
            lambda event: self._on_order_cancelled(symbol, event)
        )
        sdk_event_bus.subscribe(
            SDKEventType.ORDER_REJECTED,
            lambda event: self._on_order_rejected(symbol, event)
        )

        logger.success(f"Subscribed to events for {symbol}")

    # Trade event handlers

    async def _on_trade_executed(self, symbol: str, sdk_event: Any) -> None:
        """Handle trade executed event from SDK."""
        try:
            risk_event = RiskEvent(
                type=EventType.TRADE_EXECUTED,
                data={
                    "symbol": symbol,
                    "trade_id": getattr(sdk_event, "trade_id", None),
                    "side": getattr(sdk_event, "side", None),
                    "size": getattr(sdk_event, "size", None),
                    "price": getattr(sdk_event, "price", None),
                    "timestamp": getattr(sdk_event, "timestamp", None),
                    "sdk_event": sdk_event,
                }
            )

            await self.risk_event_bus.publish(risk_event)
            logger.debug(f"Bridged TRADE_EXECUTED event for {symbol}")

        except Exception as e:
            logger.error(f"Error bridging trade executed event: {e}")

    # Position event handlers

    async def _on_position_opened(self, symbol: str, sdk_event: Any) -> None:
        """Handle position opened event from SDK."""
        try:
            risk_event = RiskEvent(
                type=EventType.POSITION_OPENED,
                data={
                    "symbol": symbol,
                    "contract_id": getattr(sdk_event, "contract_id", None),
                    "side": getattr(sdk_event, "side", None),
                    "size": getattr(sdk_event, "size", None),
                    "entry_price": getattr(sdk_event, "entry_price", None),
                    "sdk_event": sdk_event,
                }
            )

            await self.risk_event_bus.publish(risk_event)
            logger.debug(f"Bridged POSITION_OPENED event for {symbol}")

        except Exception as e:
            logger.error(f"Error bridging position opened event: {e}")

    async def _on_position_closed(self, symbol: str, sdk_event: Any) -> None:
        """Handle position closed event from SDK."""
        try:
            risk_event = RiskEvent(
                type=EventType.POSITION_CLOSED,
                data={
                    "symbol": symbol,
                    "contract_id": getattr(sdk_event, "contract_id", None),
                    "realized_pnl": getattr(sdk_event, "realized_pnl", None),
                    "sdk_event": sdk_event,
                }
            )

            await self.risk_event_bus.publish(risk_event)
            logger.debug(f"Bridged POSITION_CLOSED event for {symbol}")

        except Exception as e:
            logger.error(f"Error bridging position closed event: {e}")

    async def _on_position_updated(self, symbol: str, sdk_event: Any) -> None:
        """Handle position updated event from SDK."""
        try:
            risk_event = RiskEvent(
                type=EventType.POSITION_UPDATED,
                data={
                    "symbol": symbol,
                    "contract_id": getattr(sdk_event, "contract_id", None),
                    "size": getattr(sdk_event, "size", None),
                    "unrealized_pnl": getattr(sdk_event, "unrealized_pnl", None),
                    "sdk_event": sdk_event,
                }
            )

            await self.risk_event_bus.publish(risk_event)
            logger.debug(f"Bridged POSITION_UPDATED event for {symbol}")

        except Exception as e:
            logger.error(f"Error bridging position updated event: {e}")

    # Order event handlers

    async def _on_order_placed(self, symbol: str, sdk_event: Any) -> None:
        """Handle order placed event from SDK."""
        try:
            risk_event = RiskEvent(
                type=EventType.ORDER_PLACED,
                data={
                    "symbol": symbol,
                    "order_id": getattr(sdk_event, "order_id", None),
                    "side": getattr(sdk_event, "side", None),
                    "size": getattr(sdk_event, "size", None),
                    "order_type": getattr(sdk_event, "order_type", None),
                    "sdk_event": sdk_event,
                }
            )

            await self.risk_event_bus.publish(risk_event)
            logger.debug(f"Bridged ORDER_PLACED event for {symbol}")

        except Exception as e:
            logger.error(f"Error bridging order placed event: {e}")

    async def _on_order_filled(self, symbol: str, sdk_event: Any) -> None:
        """Handle order filled event from SDK."""
        try:
            risk_event = RiskEvent(
                type=EventType.ORDER_FILLED,
                data={
                    "symbol": symbol,
                    "order_id": getattr(sdk_event, "order_id", None),
                    "fill_price": getattr(sdk_event, "fill_price", None),
                    "fill_size": getattr(sdk_event, "fill_size", None),
                    "sdk_event": sdk_event,
                }
            )

            await self.risk_event_bus.publish(risk_event)
            logger.debug(f"Bridged ORDER_FILLED event for {symbol}")

        except Exception as e:
            logger.error(f"Error bridging order filled event: {e}")

    async def _on_order_cancelled(self, symbol: str, sdk_event: Any) -> None:
        """Handle order cancelled event from SDK."""
        try:
            risk_event = RiskEvent(
                type=EventType.ORDER_CANCELLED,
                data={
                    "symbol": symbol,
                    "order_id": getattr(sdk_event, "order_id", None),
                    "reason": getattr(sdk_event, "reason", None),
                    "sdk_event": sdk_event,
                }
            )

            await self.risk_event_bus.publish(risk_event)
            logger.debug(f"Bridged ORDER_CANCELLED event for {symbol}")

        except Exception as e:
            logger.error(f"Error bridging order cancelled event: {e}")

    async def _on_order_rejected(self, symbol: str, sdk_event: Any) -> None:
        """Handle order rejected event from SDK."""
        try:
            risk_event = RiskEvent(
                type=EventType.ORDER_REJECTED,
                data={
                    "symbol": symbol,
                    "order_id": getattr(sdk_event, "order_id", None),
                    "reason": getattr(sdk_event, "reason", None),
                    "sdk_event": sdk_event,
                }
            )

            await self.risk_event_bus.publish(risk_event)
            logger.debug(f"Bridged ORDER_REJECTED event for {symbol}")

        except Exception as e:
            logger.error(f"Error bridging order rejected event: {e}")

    async def add_instrument(self, symbol: str, suite: TradingSuite) -> None:
        """
        Start bridging events for a newly added instrument.

        Args:
            symbol: Instrument symbol
            suite: TradingSuite instance
        """
        if self.running:
            await self._subscribe_to_suite(symbol, suite)
