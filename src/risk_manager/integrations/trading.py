"""Trading integration using Project-X-Py SDK."""

import asyncio
from typing import Any

from loguru import logger
from project_x_py import TradingSuite
from project_x_py.realtime_data_manager.types import EventType as SDKEventType

from risk_manager.core.config import RiskConfig
from risk_manager.core.events import EventBus, EventType, RiskEvent


class TradingIntegration:
    """
    Integration with Project-X-Py trading SDK.

    Bridges between the trading platform and risk management system.
    """

    def __init__(self, instruments: list[str], config: RiskConfig, event_bus: EventBus):
        self.instruments = instruments
        self.config = config
        self.event_bus = event_bus
        self.suite: TradingSuite | None = None
        self.running = False

        logger.info(f"Trading integration initialized for: {instruments}")

    async def connect(self) -> None:
        """Connect to trading platform."""
        logger.info("Connecting to ProjectX trading platform...")

        try:
            # Initialize TradingSuite with Project-X-Py SDK
            self.suite = await TradingSuite.create(
                instruments=self.instruments,
                timeframes=["1min", "5min"],
                enable_orderbook=True,
                enable_risk_management=True,
            )

            logger.success("✅ Connected to ProjectX")

        except Exception as e:
            logger.error(f"Failed to connect to trading platform: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from trading platform."""
        if self.suite:
            await self.suite.disconnect()
            logger.info("Disconnected from trading platform")

    async def start(self) -> None:
        """Start monitoring trading events."""
        if not self.suite:
            raise RuntimeError("Not connected - call connect() first")

        self.running = True
        logger.info("Starting trading event monitoring...")

        # Register callbacks for trading events
        await self.suite.on(SDKEventType.FILL, self._on_fill)
        await self.suite.on(SDKEventType.ORDER_UPDATE, self._on_order_update)

        # Start monitoring task
        asyncio.create_task(self._monitor_positions())

        logger.success("Trading monitoring started")

    async def _on_fill(self, event: Any) -> None:
        """Handle order fill event from SDK."""
        logger.info(f"Order filled: {event.data}")

        # Convert SDK event to risk event
        risk_event = RiskEvent(
            event_type=EventType.ORDER_FILLED,
            data={
                "symbol": event.data.get("symbol"),
                "side": event.data.get("side"),
                "size": event.data.get("size"),
                "price": event.data.get("price"),
                "timestamp": event.data.get("timestamp"),
            },
            source="trading_sdk",
        )

        await self.event_bus.publish(risk_event)

    async def _on_order_update(self, event: Any) -> None:
        """Handle order update event from SDK."""
        logger.debug(f"Order update: {event.data}")

        risk_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data=event.data,
            source="trading_sdk",
        )

        await self.event_bus.publish(risk_event)

    async def _monitor_positions(self) -> None:
        """Monitor positions and P&L."""
        while self.running:
            try:
                # Get current positions for each instrument
                for symbol in self.instruments:
                    context = self.suite[symbol]
                    positions = await context.positions.get_all_positions()

                    for position in positions:
                        # Publish position update event
                        risk_event = RiskEvent(
                            event_type=EventType.POSITION_UPDATED,
                            data={
                                "symbol": symbol,
                                "size": position.size,
                                "average_price": position.averagePrice,
                                "unrealized_pnl": position.unrealizedPnl,
                                "realized_pnl": position.realizedPnl,
                            },
                            source="trading_sdk",
                        )

                        await self.event_bus.publish(risk_event)

                # Update every 5 seconds
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error monitoring positions: {e}")
                await asyncio.sleep(10)  # Wait longer on error

    async def flatten_position(self, symbol: str) -> None:
        """Flatten a specific position."""
        if not self.suite:
            raise RuntimeError("Not connected")

        logger.warning(f"Flattening position for {symbol}")

        context = self.suite[symbol]
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

                logger.info(f"Closed {symbol} position: {position.size} contracts")

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
