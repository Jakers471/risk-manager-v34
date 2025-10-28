"""
Base Class for End-to-End Tests

Provides common functionality for E2E tests that use live SDK integration.

All E2E test classes should inherit from BaseE2ETest to get:
- Live SDK fixture
- RiskManager with live SDK integration
- Event waiting helpers
- Position/order verification helpers
- State cleanup between tests
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Any, Callable
from pathlib import Path

from project_x_py import TradingSuite
from loguru import logger

from risk_manager.core.manager import RiskManager
from risk_manager.core.config import RiskConfig
from risk_manager.core.events import EventType, RiskEvent


class BaseE2ETest:
    """
    Base class for all E2E tests.

    Provides:
    - Live SDK integration
    - RiskManager with live SDK
    - Event waiting utilities
    - Position/order verification
    - State cleanup

    Usage:
        @pytest.mark.e2e
        class TestMyE2EScenario(BaseE2ETest):
            async def test_something(self, risk_manager):
                # Test with live SDK and RiskManager
                event = await self.wait_for_event(EventType.POSITION_UPDATED)
                assert event is not None
    """

    # ========================================================================
    # Fixtures
    # ========================================================================

    @pytest.fixture
    async def risk_manager(
        self,
        live_sdk: TradingSuite,
        tmp_path: Path
    ) -> RiskManager:
        """
        Create RiskManager with live SDK integration.

        Args:
            live_sdk: Live SDK fixture from live_sdk.py
            tmp_path: Temporary directory for database

        Yields:
            RiskManager: Configured and started RiskManager

        Example:
            async def test_position_limit(self, risk_manager):
                # risk_manager is already started with live SDK
                await risk_manager.trading_integration.suite["MNQ"].orders.place_market_order(
                    side="buy",
                    quantity=3
                )
        """
        logger.info("🚀 Creating RiskManager for E2E test...")

        # Create config with default settings
        # Tests can override these settings
        config = RiskConfig(
            max_contracts=2,  # Intentionally low for testing violations
            max_daily_loss=-50.0,  # $50 loss limit
            enable_all_rules=True,
            log_level="DEBUG",
            log_file=str(tmp_path / "risk_manager.log"),
            database_url=f"sqlite:///{tmp_path / 'test_db.sqlite'}"
        )

        # Create RiskManager
        rm = await RiskManager.create(
            config=config,
            instruments=["MNQ", "ES", "NQ"]
        )

        # Replace mock SDK with live SDK (THIS IS THE KEY!)
        # This is where we swap mocks for real SDK integration
        if hasattr(rm, 'trading_integration') and rm.trading_integration:
            rm.trading_integration.suite = live_sdk
            logger.info("✅ Injected live SDK into RiskManager")
        else:
            logger.warning("⚠️  No trading_integration found, may need to set up SDK integration")

        # Start RiskManager
        await rm.start()
        logger.info("✅ RiskManager started with live SDK")

        # Store reference for helper methods
        self._risk_manager = rm
        self._events_received = []

        # Subscribe to all events for testing
        self._subscribe_to_all_events(rm)

        # Yield to test
        try:
            yield rm
        finally:
            # Cleanup
            logger.info("🛑 Stopping RiskManager...")
            await rm.stop()
            self._risk_manager = None
            self._events_received = []

    def _subscribe_to_all_events(self, rm: RiskManager) -> None:
        """Subscribe to all events for tracking."""

        async def event_tracker(event: RiskEvent):
            """Track all events for wait_for_event()."""
            self._events_received.append(event)
            logger.debug(f"📨 Event tracked: {event.event_type}")

        # Subscribe to all event types
        for event_type in EventType:
            rm.event_bus.subscribe(event_type, event_tracker)

    # ========================================================================
    # Event Waiting Helpers
    # ========================================================================

    async def wait_for_event(
        self,
        event_type: EventType,
        timeout: float = 5.0,
        predicate: Callable[[RiskEvent], bool] | None = None
    ) -> RiskEvent:
        """
        Wait for a specific event to be published.

        Args:
            event_type: Type of event to wait for
            timeout: Maximum time to wait in seconds
            predicate: Optional filter function for event data

        Returns:
            RiskEvent: The event that was received

        Raises:
            TimeoutError: If event not received within timeout

        Example:
            # Wait for any position update
            event = await self.wait_for_event(EventType.POSITION_UPDATED)

            # Wait for specific position update (MNQ)
            event = await self.wait_for_event(
                EventType.POSITION_UPDATED,
                predicate=lambda e: e.data.get("symbol") == "MNQ"
            )
        """
        start_time = asyncio.get_event_loop().time()
        check_interval = 0.05  # Check every 50ms

        while True:
            # Check received events
            for event in self._events_received:
                if event.event_type == event_type:
                    # Check predicate if provided
                    if predicate is None or predicate(event):
                        logger.info(f"✅ Event received: {event_type}")
                        return event

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Event {event_type} not received within {timeout}s. "
                    f"Received {len(self._events_received)} other events."
                )

            # Wait before next check
            await asyncio.sleep(check_interval)

    async def wait_for_events(
        self,
        event_type: EventType,
        count: int,
        timeout: float = 10.0
    ) -> list[RiskEvent]:
        """
        Wait for multiple events of the same type.

        Args:
            event_type: Type of events to wait for
            count: Number of events to wait for
            timeout: Maximum time to wait

        Returns:
            List of events received

        Raises:
            TimeoutError: If all events not received within timeout

        Example:
            # Wait for 3 position updates
            events = await self.wait_for_events(
                EventType.POSITION_UPDATED,
                count=3,
                timeout=10.0
            )
        """
        events = []
        start_time = asyncio.get_event_loop().time()

        while len(events) < count:
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining_timeout = timeout - elapsed

            if remaining_timeout <= 0:
                raise TimeoutError(
                    f"Only received {len(events)}/{count} events "
                    f"of type {event_type} within {timeout}s"
                )

            try:
                event = await self.wait_for_event(
                    event_type,
                    timeout=remaining_timeout
                )
                events.append(event)
            except TimeoutError:
                raise TimeoutError(
                    f"Received {len(events)}/{count} events before timeout"
                )

        return events

    async def wait_for_any_event(
        self,
        event_types: list[EventType],
        timeout: float = 5.0
    ) -> tuple[EventType, RiskEvent]:
        """
        Wait for any of the specified event types.

        Args:
            event_types: List of event types to wait for
            timeout: Maximum time to wait

        Returns:
            Tuple of (event_type, event)

        Raises:
            TimeoutError: If no matching event received

        Example:
            # Wait for either violation or enforcement
            event_type, event = await self.wait_for_any_event([
                EventType.RULE_VIOLATED,
                EventType.ENFORCEMENT_ACTION
            ])
        """
        start_time = asyncio.get_event_loop().time()
        check_interval = 0.05

        while True:
            for event in self._events_received:
                if event.event_type in event_types:
                    logger.info(f"✅ Event received: {event.event_type}")
                    return (event.event_type, event)

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"None of {event_types} received within {timeout}s"
                )

            await asyncio.sleep(check_interval)

    def clear_received_events(self) -> None:
        """
        Clear the list of received events.

        Useful between test phases to isolate event tracking.

        Example:
            # Phase 1
            await self.open_position()
            event1 = await self.wait_for_event(EventType.POSITION_OPENED)

            # Clear for phase 2
            self.clear_received_events()

            # Phase 2
            await self.close_position()
            event2 = await self.wait_for_event(EventType.POSITION_CLOSED)
        """
        self._events_received = []
        logger.debug("🧹 Cleared received events")

    # ========================================================================
    # Position Verification Helpers
    # ========================================================================

    async def get_current_positions(
        self,
        suite: TradingSuite,
        symbol: str
    ) -> list[Any]:
        """
        Get current positions for a symbol.

        Args:
            suite: TradingSuite instance
            symbol: Symbol to check (e.g., "MNQ")

        Returns:
            List of current positions

        Example:
            positions = await self.get_current_positions(live_sdk, "MNQ")
            assert len(positions) == 1
        """
        try:
            positions = await suite[symbol].positions.get_all_positions()
            logger.debug(f"📊 Current {symbol} positions: {len(positions)}")
            return positions
        except Exception as e:
            logger.error(f"❌ Failed to get positions for {symbol}: {e}")
            return []

    async def verify_position_count(
        self,
        suite: TradingSuite,
        symbol: str,
        expected_count: int,
        timeout: float = 3.0
    ) -> bool:
        """
        Verify position count for a symbol (with retry).

        Positions may take a moment to update after orders fill.

        Args:
            suite: TradingSuite instance
            symbol: Symbol to check
            expected_count: Expected number of positions
            timeout: How long to retry

        Returns:
            True if count matches, False otherwise

        Example:
            # Verify position closed
            success = await self.verify_position_count(live_sdk, "MNQ", 0)
            assert success
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            positions = await self.get_current_positions(suite, symbol)

            if len(positions) == expected_count:
                logger.info(f"✅ Position count verified: {len(positions)} = {expected_count}")
                return True

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.error(
                    f"❌ Position count mismatch: {len(positions)} != {expected_count} "
                    f"after {timeout}s"
                )
                return False

            # Wait before retry
            await asyncio.sleep(0.2)

    async def verify_no_positions(
        self,
        suite: TradingSuite,
        symbols: list[str] | None = None,
        timeout: float = 3.0
    ) -> bool:
        """
        Verify no open positions across symbols.

        Args:
            suite: TradingSuite instance
            symbols: Symbols to check (default: ["MNQ", "ES", "NQ"])
            timeout: How long to wait for positions to clear

        Returns:
            True if no positions, False otherwise

        Example:
            success = await self.verify_no_positions(live_sdk)
            assert success
        """
        if symbols is None:
            symbols = ["MNQ", "ES", "NQ"]

        for symbol in symbols:
            if not await self.verify_position_count(suite, symbol, 0, timeout):
                return False

        logger.info(f"✅ Verified no positions across {symbols}")
        return True

    # ========================================================================
    # Order Verification Helpers
    # ========================================================================

    async def get_open_orders(self, suite: TradingSuite) -> list[Any]:
        """
        Get all open orders.

        Args:
            suite: TradingSuite instance

        Returns:
            List of open orders

        Example:
            orders = await self.get_open_orders(live_sdk)
            assert len(orders) == 0
        """
        try:
            orders = await suite.orders.get_all_open_orders()
            logger.debug(f"📊 Open orders: {len(orders)}")
            return orders
        except Exception as e:
            logger.error(f"❌ Failed to get orders: {e}")
            return []

    async def verify_no_open_orders(
        self,
        suite: TradingSuite,
        timeout: float = 3.0
    ) -> bool:
        """
        Verify no open orders (with retry).

        Args:
            suite: TradingSuite instance
            timeout: How long to wait

        Returns:
            True if no orders, False otherwise

        Example:
            success = await self.verify_no_open_orders(live_sdk)
            assert success
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            orders = await self.get_open_orders(suite)

            if len(orders) == 0:
                logger.info("✅ Verified no open orders")
                return True

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.error(f"❌ Still have {len(orders)} open orders after {timeout}s")
                return False

            await asyncio.sleep(0.2)

    # ========================================================================
    # State Verification Helpers
    # ========================================================================

    def is_account_locked(self, rm: RiskManager, account_id: int) -> bool:
        """
        Check if account is locked out.

        Args:
            rm: RiskManager instance
            account_id: Account ID to check

        Returns:
            True if locked, False otherwise

        Example:
            locked = self.is_account_locked(risk_manager, 12345)
            assert locked
        """
        if hasattr(rm, 'lockout_manager'):
            return rm.lockout_manager.is_locked(account_id)
        return False

    async def get_daily_pnl(
        self,
        rm: RiskManager,
        account_id: int
    ) -> float:
        """
        Get current daily P&L for account.

        Args:
            rm: RiskManager instance
            account_id: Account ID to check

        Returns:
            Current daily P&L

        Example:
            pnl = await self.get_daily_pnl(risk_manager, 12345)
            assert pnl < 0  # Loss
        """
        if hasattr(rm, 'pnl_tracker'):
            pnl_data = await rm.pnl_tracker.get_daily_pnl(account_id)
            return pnl_data.get('realized_pnl', 0.0)
        return 0.0

    # ========================================================================
    # Assertion Helpers
    # ========================================================================

    def assert_event_data_contains(
        self,
        event: RiskEvent,
        **expected_fields
    ) -> None:
        """
        Assert event data contains expected fields with values.

        Args:
            event: Event to check
            **expected_fields: Expected field=value pairs

        Raises:
            AssertionError: If any field missing or doesn't match

        Example:
            event = await self.wait_for_event(EventType.POSITION_UPDATED)
            self.assert_event_data_contains(
                event,
                symbol="MNQ",
                size=2
            )
        """
        for field, expected_value in expected_fields.items():
            if field not in event.data:
                raise AssertionError(
                    f"Event data missing field '{field}'. "
                    f"Available fields: {list(event.data.keys())}"
                )

            actual_value = event.data[field]
            if actual_value != expected_value:
                raise AssertionError(
                    f"Event data field '{field}' mismatch: "
                    f"{actual_value} != {expected_value}"
                )

        logger.info(f"✅ Event data contains expected fields: {expected_fields}")
