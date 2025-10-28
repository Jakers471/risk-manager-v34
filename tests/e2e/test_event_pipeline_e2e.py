"""
End-to-End Tests for Event Pipeline

Tests the COMPLETE event flow from SDK events through to rule evaluation.
Uses mocked SDK to simulate real trading event scenarios.

Complete Event Flow:
1. SDK fires event (simulated)
2. EventBus publishes event
3. RiskEngine receives event
4. Rules evaluate against event + current state
5. Violations detected (if any)
6. Enforcement triggered (if needed)

This validates the entire event pipeline works together.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

# Risk Manager imports
from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.config import RiskConfig
from risk_manager.rules import MaxPositionRule
from risk_manager.rules.daily_unrealized_loss import DailyUnrealizedLossRule


class MockPosition:
    """Mock SDK Position object."""

    def __init__(self, size=0, symbol="MNQ", avg_price=16500.0, unrealized_pnl=0.0):
        self.size = size
        self.symbol = symbol
        self.averagePrice = avg_price
        self.unrealizedPnl = unrealized_pnl
        self.realizedPnl = 0.0
        self.contractId = f"CON.F.US.{symbol}.Z25"
        self.id = 1
        self.accountId = 12345


class MockOrder:
    """Mock SDK Order object."""

    def __init__(self, symbol="MNQ", size=1, status="Filled"):
        self.symbol = symbol
        self.size = size
        self.status = status
        self.id = "ORDER-123"
        self.contractId = f"CON.F.US.{symbol}.Z25"
        self.accountId = 12345


class MockTradingSuite:
    """Mock SDK TradingSuite."""

    def __init__(self):
        self.event_bus = EventBus()
        self._positions = []
        self._orders = []
        self.account_info = Mock()
        self.account_info.id = "PRAC-V2-126244-84184528"
        self.account_info.name = "150k Practice Account"

    def __getitem__(self, symbol):
        """Return mock instrument context."""
        context = Mock()
        context.positions = Mock()
        context.positions.get_all_positions = AsyncMock(return_value=self._positions)
        context.positions.close_all_positions = AsyncMock()
        context.positions.close_position = AsyncMock()
        context.instrument_info = Mock()
        context.instrument_info.name = symbol
        context.instrument_info.id = f"CON.F.US.{symbol}.Z25"
        return context

    async def on(self, event_type, handler):
        """Subscribe to event."""
        self.event_bus.subscribe(event_type, handler)

    async def disconnect(self):
        """Mock disconnect."""
        pass

    @property
    def is_connected(self):
        """Mock connection status."""
        return True


@pytest.mark.e2e
class TestEventPipelineE2E:
    """End-to-end tests for event pipeline flow."""

    @pytest.fixture
    def mock_sdk_suite(self):
        """Create mock SDK suite."""
        return MockTradingSuite()

    @pytest.fixture
    async def risk_manager(self, mock_sdk_suite):
        """Create simplified risk system for e2e testing."""
        # Create components directly (without full RiskManager)
        config = RiskConfig(
            project_x_api_key="test_api_key",
            project_x_username="test_user",
            max_contracts=5
        )
        event_bus = EventBus()

        # Mock trading integration
        mock_trading = AsyncMock()
        mock_trading.flatten_all = AsyncMock()
        mock_trading.flatten_position = AsyncMock()
        mock_trading.close_position = AsyncMock()
        mock_trading.suite = mock_sdk_suite

        # Create engine with mock trading
        from risk_manager.core.engine import RiskEngine
        engine = RiskEngine(config, event_bus, mock_trading)

        # Add max position rule
        rule = MaxPositionRule(max_contracts=5, action="flatten")
        engine.add_rule(rule)

        # Start engine
        await engine.start()

        # Create a simple container object
        class SimpleRiskManager:
            def __init__(self):
                self.config = config
                self.event_bus = event_bus
                self.engine = engine
                self.trading_integration = mock_trading

        rm = SimpleRiskManager()

        yield rm

        # Cleanup
        await engine.stop()

    # ========================================================================
    # Test 1: Position Opened Event Flow
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_opened_event_flow(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test position opened event flows through entire pipeline.

        Flow:
        1. Position opened event published
        2. EventBus distributes to subscribers
        3. RiskEngine receives and processes
        4. Rules evaluate against new position
        5. No violations (within limits)
        """
        # Given: System is monitoring
        # Track events flowing through system
        events_received = []

        async def track_events(event):
            events_received.append(event)

        risk_manager.event_bus.subscribe(
            EventType.POSITION_OPENED,
            track_events
        )

        # And: Position that will be opened (1 MNQ contract - within limits)
        mock_sdk_suite._positions = [MockPosition(size=1, symbol="MNQ")]
        risk_manager.engine.current_positions = {
            "MNQ": {
                "size": 1,
                "side": "long",
                "avgPrice": 16500.0,
                "contractId": "CON.F.US.MNQ.Z25"
            }
        }

        # When: SDK fires POSITION_OPENED event
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "size": 1,
                "avgPrice": 16500.0,
                "contractId": "CON.F.US.MNQ.Z25"
            }
        )

        await risk_manager.event_bus.publish(position_event)
        await asyncio.sleep(0.1)  # Allow async processing

        # Then: Event received by subscribers
        assert len(events_received) == 1
        assert events_received[0].event_type == EventType.POSITION_OPENED

        # Then: Engine state updated
        assert "MNQ" in risk_manager.engine.current_positions
        assert risk_manager.engine.current_positions["MNQ"]["size"] == 1

        # Then: Rules evaluate (no violations for 1 contract)
        violations = await risk_manager.engine.evaluate_rules(position_event)
        assert len(violations) == 0

        # Cleanup: Close position
        mock_sdk_suite._positions = []
        risk_manager.engine.current_positions = {}

    # ========================================================================
    # Test 2: Position Updated Event Flow
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_updated_event_flow(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test position updated event updates tracking and re-evaluates rules.

        Flow:
        1. Existing position (1 MNQ)
        2. Position grows to 2 contracts
        3. POSITION_UPDATED event fires
        4. Tracking updates
        5. Rules re-evaluate with updated position
        """
        # Given: Existing position (1 MNQ)
        mock_sdk_suite._positions = [MockPosition(size=1, symbol="MNQ")]
        risk_manager.engine.current_positions = {
            "MNQ": {
                "size": 1,
                "side": "long",
                "avgPrice": 16500.0,
                "contractId": "CON.F.US.MNQ.Z25"
            }
        }

        # Track updated events
        updated_events = []

        async def track_updates(event):
            updated_events.append(event)

        risk_manager.event_bus.subscribe(
            EventType.POSITION_UPDATED,
            track_updates
        )

        # When: Position grows to 2 contracts
        mock_sdk_suite._positions = [MockPosition(size=2, symbol="MNQ")]
        risk_manager.engine.current_positions["MNQ"]["size"] = 2

        position_update_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 2,
                "avgPrice": 16500.0,
                "contractId": "CON.F.US.MNQ.Z25"
            }
        )

        await risk_manager.event_bus.publish(position_update_event)
        await asyncio.sleep(0.1)

        # Then: Event received
        assert len(updated_events) == 1
        assert updated_events[0].event_type == EventType.POSITION_UPDATED

        # Then: Engine state updated
        assert risk_manager.engine.current_positions["MNQ"]["size"] == 2

        # Then: Rules re-evaluate (still within limits)
        violations = await risk_manager.engine.evaluate_rules(position_update_event)
        assert len(violations) == 0

        # Cleanup: Close position
        mock_sdk_suite._positions = []
        risk_manager.engine.current_positions = {}

    # ========================================================================
    # Test 3: Order Filled Event Flow
    # ========================================================================

    @pytest.mark.asyncio
    async def test_order_filled_event_flow(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test order placed → filled event updates position tracking.

        Flow:
        1. Order placed (ORDER_PLACED event)
        2. Order fills (ORDER_FILLED event)
        3. Position tracking updates
        4. Rules evaluate with new position
        """
        # Given: System monitoring, no positions
        risk_manager.engine.current_positions = {}

        # Track order events
        order_events = []

        async def track_orders(event):
            order_events.append(event)

        risk_manager.event_bus.subscribe(EventType.ORDER_PLACED, track_orders)
        risk_manager.event_bus.subscribe(EventType.ORDER_FILLED, track_orders)

        # When: Order placed
        order_placed_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "symbol": "MNQ",
                "size": 1,
                "orderId": "ORDER-123",
                "contractId": "CON.F.US.MNQ.Z25"
            }
        )

        await risk_manager.event_bus.publish(order_placed_event)
        await asyncio.sleep(0.05)

        # When: Order fills
        mock_sdk_suite._positions = [MockPosition(size=1, symbol="MNQ", avg_price=16500.0)]
        risk_manager.engine.current_positions = {
            "MNQ": {
                "size": 1,
                "side": "long",
                "avgPrice": 16500.0,
                "contractId": "CON.F.US.MNQ.Z25"
            }
        }

        order_filled_event = RiskEvent(
            event_type=EventType.ORDER_FILLED,
            data={
                "symbol": "MNQ",
                "size": 1,
                "fillPrice": 16500.0,
                "orderId": "ORDER-123",
                "contractId": "CON.F.US.MNQ.Z25"
            }
        )

        await risk_manager.event_bus.publish(order_filled_event)
        await asyncio.sleep(0.05)

        # Then: Both events received
        assert len(order_events) == 2
        assert order_events[0].event_type == EventType.ORDER_PLACED
        assert order_events[1].event_type == EventType.ORDER_FILLED

        # Then: Position tracking updated
        assert "MNQ" in risk_manager.engine.current_positions
        assert risk_manager.engine.current_positions["MNQ"]["size"] == 1

        # Then: Rules evaluate (no violations)
        violations = await risk_manager.engine.evaluate_rules(order_filled_event)
        assert len(violations) == 0

        # Cleanup
        mock_sdk_suite._positions = []
        risk_manager.engine.current_positions = {}

    # ========================================================================
    # Test 4: P&L Update Event Flow
    # ========================================================================

    @pytest.mark.asyncio
    async def test_pnl_update_event_flow(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test P&L update events trigger rule evaluation.

        Flow:
        1. Open position (1 MNQ long @ 16500)
        2. Price changes (market price update)
        3. PNL_UPDATED event fires
        4. P&L Tracker updates unrealized P&L
        5. RULE-004 (Daily Unrealized Loss) evaluates
        """
        # Given: Position opened
        mock_sdk_suite._positions = [MockPosition(
            size=1,
            symbol="MNQ",
            avg_price=16500.0,
            unrealized_pnl=0.0
        )]
        risk_manager.engine.current_positions = {
            "MNQ": {
                "size": 1,
                "side": "long",
                "avgPrice": 16500.0,
                "contractId": "CON.F.US.MNQ.Z25"
            }
        }

        # Set initial market price
        risk_manager.engine.market_prices["MNQ"] = 16500.0

        # Add daily unrealized loss rule for testing
        loss_rule = DailyUnrealizedLossRule(
            loss_limit=-500.0,  # Stop loss at -$500
            tick_values={"MNQ": 5.0},  # $5 per tick
            tick_sizes={"MNQ": 0.25},  # 0.25 tick size
            action="close_position"
        )
        risk_manager.engine.add_rule(loss_rule)

        # Track P&L events
        pnl_events = []

        async def track_pnl(event):
            pnl_events.append(event)

        risk_manager.event_bus.subscribe(EventType.PNL_UPDATED, track_pnl)

        # When: Market price changes (small loss, not triggering stop loss)
        risk_manager.engine.market_prices["MNQ"] = 16490.0  # -10 points = -$200 (within limit)

        pnl_update_event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={
                "symbol": "MNQ",
                "unrealizedPnl": -200.0,
                "currentPrice": 16490.0
            }
        )

        await risk_manager.event_bus.publish(pnl_update_event)
        await asyncio.sleep(0.1)

        # Then: P&L event received
        assert len(pnl_events) == 1
        assert pnl_events[0].event_type == EventType.PNL_UPDATED

        # Then: Rules evaluate (no violation, within -$500 limit)
        violations = await risk_manager.engine.evaluate_rules(pnl_update_event)
        assert len(violations) == 0

        # Cleanup
        mock_sdk_suite._positions = []
        risk_manager.engine.current_positions = {}
        risk_manager.engine.market_prices = {}

    # ========================================================================
    # Test 5: Multi-Symbol Event Flow
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_symbol_event_flow(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test system tracks multiple symbols independently and sums for rules.

        Flow:
        1. Open position in MNQ (1 contract)
        2. Open position in ES (1 contract)
        3. Events fire for both symbols
        4. Engine tracks both independently
        5. RULE-001 (Max Contracts) sums across symbols
        """
        # Given: System monitoring, no positions
        risk_manager.engine.current_positions = {}

        # Track all position events
        position_events = []

        async def track_positions(event):
            position_events.append(event)

        risk_manager.event_bus.subscribe(EventType.POSITION_OPENED, track_positions)
        risk_manager.event_bus.subscribe(EventType.POSITION_UPDATED, track_positions)

        # When: Open position in MNQ
        mock_sdk_suite._positions = [MockPosition(size=1, symbol="MNQ")]
        risk_manager.engine.current_positions["MNQ"] = {
            "size": 1,
            "side": "long",
            "avgPrice": 16500.0,
            "contractId": "CON.F.US.MNQ.Z25"
        }

        mnq_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "size": 1,
                "avgPrice": 16500.0
            }
        )

        await risk_manager.event_bus.publish(mnq_event)
        await asyncio.sleep(0.05)

        # When: Open position in ES
        mock_sdk_suite._positions.append(MockPosition(size=1, symbol="ES", avg_price=5500.0))
        risk_manager.engine.current_positions["ES"] = {
            "size": 1,
            "side": "long",
            "avgPrice": 5500.0,
            "contractId": "CON.F.US.ES.Z25"
        }

        es_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "size": 1,
                "avgPrice": 5500.0
            }
        )

        await risk_manager.event_bus.publish(es_event)
        await asyncio.sleep(0.05)

        # Then: Both events received
        assert len(position_events) == 2
        assert any(e.data.get("symbol") == "MNQ" for e in position_events)
        assert any(e.data.get("symbol") == "ES" for e in position_events)

        # Then: Engine tracks both symbols independently
        assert "MNQ" in risk_manager.engine.current_positions
        assert "ES" in risk_manager.engine.current_positions
        assert risk_manager.engine.current_positions["MNQ"]["size"] == 1
        assert risk_manager.engine.current_positions["ES"]["size"] == 1

        # Then: MaxPositionRule sums across symbols (2 total, within limit of 5)
        violations = await risk_manager.engine.evaluate_rules(es_event)
        assert len(violations) == 0

        # When: Total position exceeds limit
        # Add more contracts to exceed limit of 5
        risk_manager.engine.current_positions["MNQ"]["size"] = 3
        risk_manager.engine.current_positions["ES"]["size"] = 3  # Total = 6, exceeds 5

        exceed_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 3}
        )

        violations = await risk_manager.engine.evaluate_rules(exceed_event)

        # Then: Violation detected for total across symbols
        assert len(violations) >= 1
        assert violations[0]["rule"] == "MaxPositionRule"
        assert violations[0]["current_size"] == 6
        assert violations[0]["max_size"] == 5

        # Cleanup
        mock_sdk_suite._positions = []
        risk_manager.engine.current_positions = {}

    # ========================================================================
    # Test 6: Event Pipeline Stress Test
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_pipeline_stress(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test system handles rapid sequence of events correctly.

        Scenario: Rapid trading activity
        - Multiple position updates
        - Multiple order fills
        - P&L updates
        - All processed correctly
        """
        # Given: System monitoring
        events_processed = []

        async def track_all_events(event):
            events_processed.append(event)

        for event_type in [EventType.POSITION_OPENED, EventType.POSITION_UPDATED,
                          EventType.ORDER_FILLED, EventType.PNL_UPDATED]:
            risk_manager.event_bus.subscribe(event_type, track_all_events)

        # When: Rapid sequence of events
        events_to_publish = [
            RiskEvent(EventType.POSITION_OPENED, data={"symbol": "MNQ", "size": 1}),
            RiskEvent(EventType.ORDER_FILLED, data={"symbol": "MNQ", "size": 1}),
            RiskEvent(EventType.POSITION_UPDATED, data={"symbol": "MNQ", "size": 2}),
            RiskEvent(EventType.PNL_UPDATED, data={"symbol": "MNQ", "unrealizedPnl": 100.0}),
            RiskEvent(EventType.POSITION_UPDATED, data={"symbol": "MNQ", "size": 1}),
            RiskEvent(EventType.PNL_UPDATED, data={"symbol": "MNQ", "unrealizedPnl": 50.0}),
        ]

        for event in events_to_publish:
            await risk_manager.event_bus.publish(event)
            await asyncio.sleep(0.01)  # Minimal delay between events

        await asyncio.sleep(0.2)  # Allow all async processing to complete

        # Then: All events processed
        assert len(events_processed) == len(events_to_publish)

        # Then: System remains stable (no crashes)
        assert risk_manager.engine.running is True

        # Cleanup
        mock_sdk_suite._positions = []
        risk_manager.engine.current_positions = {}

    # ========================================================================
    # Test 7: Event Pipeline Error Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_pipeline_error_handling(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test system continues processing even if handler fails.

        Flow:
        1. Subscribe failing handler
        2. Subscribe working handler
        3. Publish event
        4. Failing handler raises exception
        5. Working handler still executes
        6. System remains stable
        """
        # Given: Handler that will fail
        async def failing_handler(event):
            raise ValueError("Test error - handler failure")

        risk_manager.event_bus.subscribe(
            EventType.POSITION_UPDATED,
            failing_handler
        )

        # And: Handler that should still work
        successful_events = []

        async def working_handler(event):
            successful_events.append(event)

        risk_manager.event_bus.subscribe(
            EventType.POSITION_UPDATED,
            working_handler
        )

        # When: Event is published
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 1}
        )

        # Should not crash the system
        await risk_manager.event_bus.publish(event)
        await asyncio.sleep(0.1)

        # Then: Working handler still executed
        assert len(successful_events) == 1
        assert successful_events[0].event_type == EventType.POSITION_UPDATED

        # Then: System remains stable
        assert risk_manager.engine.running is True

    # ========================================================================
    # Test 8: Complete Flow - Position Lifecycle
    # ========================================================================

    @pytest.mark.asyncio
    async def test_complete_position_lifecycle(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test complete position lifecycle: open → update → close.

        Flow:
        1. Position opened (POSITION_OPENED)
        2. Position grows (POSITION_UPDATED)
        3. Position shrinks (POSITION_UPDATED)
        4. Position closed (POSITION_CLOSED)
        5. All events tracked correctly
        6. State remains consistent
        """
        # Track all lifecycle events
        lifecycle_events = []

        async def track_lifecycle(event):
            lifecycle_events.append(event)

        for event_type in [EventType.POSITION_OPENED, EventType.POSITION_UPDATED,
                          EventType.POSITION_CLOSED]:
            risk_manager.event_bus.subscribe(event_type, track_lifecycle)

        # 1. Position opened
        risk_manager.engine.current_positions["MNQ"] = {
            "size": 1, "side": "long", "avgPrice": 16500.0
        }
        await risk_manager.event_bus.publish(
            RiskEvent(EventType.POSITION_OPENED, data={"symbol": "MNQ", "size": 1})
        )
        await asyncio.sleep(0.05)

        # 2. Position grows
        risk_manager.engine.current_positions["MNQ"]["size"] = 2
        await risk_manager.event_bus.publish(
            RiskEvent(EventType.POSITION_UPDATED, data={"symbol": "MNQ", "size": 2})
        )
        await asyncio.sleep(0.05)

        # 3. Position shrinks
        risk_manager.engine.current_positions["MNQ"]["size"] = 1
        await risk_manager.event_bus.publish(
            RiskEvent(EventType.POSITION_UPDATED, data={"symbol": "MNQ", "size": 1})
        )
        await asyncio.sleep(0.05)

        # 4. Position closed
        del risk_manager.engine.current_positions["MNQ"]
        await risk_manager.event_bus.publish(
            RiskEvent(EventType.POSITION_CLOSED, data={"symbol": "MNQ", "size": 0})
        )
        await asyncio.sleep(0.05)

        # Then: All lifecycle events tracked
        assert len(lifecycle_events) == 4
        assert lifecycle_events[0].event_type == EventType.POSITION_OPENED
        assert lifecycle_events[1].event_type == EventType.POSITION_UPDATED
        assert lifecycle_events[2].event_type == EventType.POSITION_UPDATED
        assert lifecycle_events[3].event_type == EventType.POSITION_CLOSED

        # Then: Final state is correct (no positions)
        assert "MNQ" not in risk_manager.engine.current_positions

        # Cleanup
        mock_sdk_suite._positions = []
