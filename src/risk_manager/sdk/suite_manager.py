"""
TradingSuite Lifecycle Manager

Manages the Project-X SDK TradingSuite instances for multiple instruments.
Handles initialization, reconnection, and cleanup.
"""

import asyncio
from typing import Any

from loguru import logger
from project_x_py import TradingSuite

from risk_manager.core.events import EventBus


class SuiteManager:
    """
    Manages TradingSuite instances for multiple instruments.

    This class provides:
    - Multi-instrument TradingSuite management
    - Automatic reconnection on failure
    - Health monitoring
    - Graceful shutdown
    """

    def __init__(self, event_bus: EventBus):
        """
        Initialize the suite manager.

        Args:
            event_bus: Event bus for publishing SDK events
        """
        self.event_bus = event_bus
        self.suites: dict[str, TradingSuite] = {}
        self.running = False
        self._health_check_task: asyncio.Task[Any] | None = None

        logger.info("SuiteManager initialized")

    async def add_instrument(
        self,
        symbol: str,
        timeframes: list[str] | None = None,
        enable_orderbook: bool = False,
        enable_statistics: bool = True,
    ) -> TradingSuite:
        """
        Add an instrument and create a TradingSuite for it.

        Args:
            symbol: Instrument symbol (e.g., "MNQ", "ES")
            timeframes: Timeframes to track (e.g., ["1min", "5min"])
            enable_orderbook: Enable Level 2 orderbook
            enable_statistics: Enable statistics tracking

        Returns:
            The created TradingSuite instance

        Raises:
            Exception: If suite creation fails
        """
        if symbol in self.suites:
            logger.warning(f"Instrument {symbol} already exists, returning existing suite")
            return self.suites[symbol]

        logger.info(f"Creating TradingSuite for {symbol}...")

        try:
            # Create TradingSuite using SDK
            suite = await TradingSuite.create(
                symbol,
                timeframes=timeframes or ["1min", "5min"],
                enable_orderbook=enable_orderbook,
                enable_statistics=enable_statistics,
            )

            self.suites[symbol] = suite
            logger.success(f"TradingSuite created for {symbol}")

            return suite

        except Exception as e:
            logger.error(f"Failed to create TradingSuite for {symbol}: {e}")
            raise

    async def remove_instrument(self, symbol: str) -> None:
        """
        Remove an instrument and disconnect its TradingSuite.

        Args:
            symbol: Instrument symbol to remove
        """
        if symbol not in self.suites:
            logger.warning(f"Instrument {symbol} not found")
            return

        logger.info(f"Removing TradingSuite for {symbol}...")

        try:
            suite = self.suites[symbol]
            await suite.disconnect()
            del self.suites[symbol]
            logger.success(f"TradingSuite removed for {symbol}")

        except Exception as e:
            logger.error(f"Failed to remove TradingSuite for {symbol}: {e}")

    def get_suite(self, symbol: str) -> TradingSuite | None:
        """
        Get the TradingSuite for a specific instrument.

        Args:
            symbol: Instrument symbol

        Returns:
            TradingSuite instance or None if not found
        """
        return self.suites.get(symbol)

    def get_all_suites(self) -> dict[str, TradingSuite]:
        """
        Get all active TradingSuite instances.

        Returns:
            Dictionary mapping symbols to TradingSuite instances
        """
        return self.suites.copy()

    async def start(self) -> None:
        """Start the suite manager and health monitoring."""
        self.running = True
        logger.info("SuiteManager started")

        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def stop(self) -> None:
        """Stop the suite manager and disconnect all suites."""
        self.running = False
        logger.info("Stopping SuiteManager...")

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Disconnect all suites
        for symbol in list(self.suites.keys()):
            await self.remove_instrument(symbol)

        logger.success("SuiteManager stopped")

    async def _health_check_loop(self) -> None:
        """Background task to monitor suite health."""
        while self.running:
            try:
                # Check each suite's health
                for symbol, suite in self.suites.items():
                    try:
                        # Check if realtime connection is active
                        if hasattr(suite, "realtime") and suite.realtime:
                            if not suite.realtime.is_connected:
                                logger.warning(
                                    f"TradingSuite for {symbol} disconnected, attempting reconnect..."
                                )
                                # SDK handles auto-reconnection
                                # We just log for visibility

                    except Exception as e:
                        logger.error(f"Health check failed for {symbol}: {e}")

                # Check every 30 seconds
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)

    async def get_health_status(self) -> dict[str, Any]:
        """
        Get health status of all suites.

        Returns:
            Dictionary with health information
        """
        status = {
            "total_suites": len(self.suites),
            "suites": {},
        }

        for symbol, suite in self.suites.items():
            suite_status = {
                "connected": False,
                "instrument_id": None,
            }

            try:
                # Check connection status
                if hasattr(suite, "realtime") and suite.realtime:
                    suite_status["connected"] = suite.realtime.is_connected

                # Get instrument info
                if hasattr(suite, "instrument_info"):
                    suite_status["instrument_id"] = suite.instrument_info.id

                # Get statistics if available
                if hasattr(suite, "get_stats"):
                    stats = await suite.get_stats()
                    suite_status["stats"] = stats

            except Exception as e:
                suite_status["error"] = str(e)

            status["suites"][symbol] = suite_status

        return status
