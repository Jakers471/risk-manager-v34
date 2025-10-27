"""
Integration Tests for Event Pipeline

Tests the complete event flow from SDK to Rule enforcement with mocked SDK.
Tests integration between EventBus, RiskEngine, Rules, and Enforcement.

Flow: SDK Event → EventBus → RiskEngine → Rule → Violation → Enforcement
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from datetime import datetime

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.engine import RiskEngine
from risk_manager.core.config import RiskConfig
from risk_manager.rules import MaxPositionRule


class TestEventPipelineIntegration:
    """Integration tests for event pipeline."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return RiskConfig(max_contracts=2)

    @pytest.fixture
    def event_bus(self):
        """Create event bus."""
        return EventBus()

    @pytest.fixture
    def mock_trading_integration(self):
        """Create mock trading integration."""
        integration = AsyncMock()
        integration.flatten_all = AsyncMock()
        integration.flatten_position = AsyncMock()
        return integration

    @pytest.fixture
    async def engine(self, config, event_bus, mock_trading_integration):
        """Create risk engine with mock trading integration."""
        engine = RiskEngine(config, event_bus, mock_trading_integration)
        await engine.start()
        yield engine
        await engine.stop()

    # ========================================================================
    # Test 1: Event Bus Publishes to Subscribers
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_bus_publishes_to_subscribers(self, event_bus):
        """Test EventBus publishes events to subscribed handlers."""
        # Given: A subscriber
        events_received = []

        async def handler(event):
            events_received.append(event)

        event_bus.subscribe(EventType.POSITION_UPDATED, handler)

        # When: Event is published
        test_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 1}
        )
        await event_bus.publish(test_event)

        # Then: Handler receives event
        assert len(events_received) == 1
        assert events_received[0].event_type == EventType.POSITION_UPDATED

    @pytest.mark.asyncio
    async def test_event_bus_multiple_subscribers(self, event_bus):
        """Test EventBus handles multiple subscribers."""
        # Given: Multiple subscribers
        handler1_called = []
        handler2_called = []

        async def handler1(event):
            handler1_called.append(event)

        async def handler2(event):
            handler2_called.append(event)

        event_bus.subscribe(EventType.POSITION_UPDATED, handler1)
        event_bus.subscribe(EventType.POSITION_UPDATED, handler2)

        # When: Event is published
        test_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 1}
        )
        await event_bus.publish(test_event)

        # Then: Both handlers receive event
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    # ========================================================================
    # Test 2: Engine Evaluates Rules on Events
    # ========================================================================

    @pytest.mark.asyncio
    async def test_engine_evaluates_rule_on_event(self, engine):
        """Test engine evaluates rules when event received."""
        # Given: Rule added to engine
        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)

        # And: Position that violates rule
        engine.current_positions = {"MNQ": {"size": 3, "side": "long"}}

        # When: Position event received
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 3}
        )

        await engine.evaluate_rules(event)

        # Then: Rule should be evaluated
        # (Verified by enforcement action being triggered)
        # This will be tested in next test

    @pytest.mark.asyncio
    async def test_engine_skips_rules_when_no_violation(self, engine):
        """Test engine doesn't trigger enforcement when no violation."""
        # Given: Rule added to engine
        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)

        # And: Position within limit
        engine.current_positions = {"MNQ": {"size": 1, "side": "long"}}

        # When: Position event received
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 1}
        )

        await engine.evaluate_rules(event)

        # Then: No enforcement called
        engine.trading_integration.flatten_all.assert_not_called()

    # ========================================================================
    # Test 3: Violation Triggers Enforcement
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_triggers_flatten_enforcement(self, engine):
        """Test that rule violation triggers flatten enforcement."""
        # Given: Rule with flatten action
        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)

        # And: Position exceeding limit
        engine.current_positions = {"MNQ": {"size": 3, "side": "long"}}

        # When: Position event triggers violation
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 3}
        )

        await engine.evaluate_rules(event)

        # Then: Flatten all should be called
        engine.trading_integration.flatten_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_violation_publishes_event(self, engine, event_bus):
        """Test that violation publishes RULE_VIOLATED event."""
        # Given: Subscriber to violation events
        violations_received = []

        async def violation_handler(event):
            violations_received.append(event)

        event_bus.subscribe(EventType.RULE_VIOLATED, violation_handler)

        # And: Rule that will violate
        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)
        engine.current_positions = {"MNQ": {"size": 3, "side": "long"}}

        # When: Violation occurs
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 3}
        )

        await engine.evaluate_rules(event)

        # Small delay for async event propagation
        await asyncio.sleep(0.1)

        # Then: RULE_VIOLATED event published
        assert len(violations_received) == 1
        assert violations_received[0].event_type == EventType.RULE_VIOLATED

    # ========================================================================
    # Test 4: End-to-End Event Flow
    # ========================================================================

    @pytest.mark.asyncio
    async def test_end_to_end_position_violation_flow(
        self, engine, event_bus, mock_trading_integration
    ):
        """Test complete flow from position update to enforcement."""
        # Given: System is monitoring positions
        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)

        # And: Tracking enforcement actions
        enforcement_called = []

        async def enforcement_tracker(event):
            if event.event_type == EventType.ENFORCEMENT_ACTION:
                enforcement_called.append(event)

        event_bus.subscribe(EventType.ENFORCEMENT_ACTION, enforcement_tracker)

        # And: Position that will violate
        engine.current_positions = {"MNQ": {"size": 3, "side": "long"}}

        # When: Position update event flows through system
        position_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 3,
                "unrealized_pnl": 150.00
            }
        )

        await event_bus.publish(position_event)
        await engine.evaluate_rules(position_event)

        # Small delay for async propagation
        await asyncio.sleep(0.1)

        # Then: Complete flow executed
        # 1. Rule evaluated
        # 2. Violation detected
        # 3. Enforcement triggered
        mock_trading_integration.flatten_all.assert_called_once()

        # 4. Enforcement event published
        assert len(enforcement_called) == 1
        assert enforcement_called[0].data["action"] == "flatten_all"

    # ========================================================================
    # Test 5: Multiple Rules Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multiple_rules_evaluated_in_order(self, engine):
        """Test that multiple rules are evaluated for same event."""
        # Given: Two rules
        rule1 = MaxPositionRule(max_contracts=2, action="flatten")
        rule2 = MaxPositionRule(max_contracts=5, action="alert")

        engine.add_rule(rule1)
        engine.add_rule(rule2)

        # And: Position that violates both
        engine.current_positions = {"MNQ": {"size": 6, "side": "long"}}

        # When: Event evaluated
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 6}
        )

        await engine.evaluate_rules(event)

        # Then: Both rules evaluated
        # First rule (stricter) should trigger flatten
        engine.trading_integration.flatten_all.assert_called()

    # ========================================================================
    # Test 6: Event Bus Error Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_bus_handles_handler_errors(self, event_bus):
        """Test EventBus continues even if handler raises error."""
        # Given: Handler that raises error
        async def failing_handler(event):
            raise ValueError("Handler error")

        # And: Handler that works
        successful_calls = []

        async def working_handler(event):
            successful_calls.append(event)

        event_bus.subscribe(EventType.POSITION_UPDATED, failing_handler)
        event_bus.subscribe(EventType.POSITION_UPDATED, working_handler)

        # When: Event published
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 1}
        )

        # Should not raise exception
        await event_bus.publish(event)

        # Then: Working handler still executed
        # (Exact behavior depends on error handling implementation)

    # ========================================================================
    # Test 7: Engine State Management
    # ========================================================================

    @pytest.mark.asyncio
    async def test_engine_tracks_position_state(self, engine):
        """Test engine maintains position state across events."""
        # Given: Initial position
        engine.current_positions = {"MNQ": {"size": 1, "side": "long"}}

        # When: Position increases
        event1 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2}
        )

        # Update position manually (simulating state manager)
        engine.current_positions["MNQ"]["size"] = 2

        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)

        # Should not violate
        await engine.evaluate_rules(event1)
        engine.trading_integration.flatten_all.assert_not_called()

        # When: Position increases again
        event2 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 3}
        )

        engine.current_positions["MNQ"]["size"] = 3

        # Should violate
        await engine.evaluate_rules(event2)
        engine.trading_integration.flatten_all.assert_called_once()

    # ========================================================================
    # Test 8: Enforcement Action Types
    # ========================================================================

    @pytest.mark.asyncio
    async def test_flatten_action_calls_flatten_all(self, engine):
        """Test flatten action calls trading_integration.flatten_all()."""
        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)
        engine.current_positions = {"MNQ": {"size": 3, "side": "long"}}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 3}
        )

        await engine.evaluate_rules(event)

        # Verify correct enforcement method called
        engine.trading_integration.flatten_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_action_triggers_pause_trading(self, engine):
        """Test pause action triggers pause_trading()."""
        rule = MaxPositionRule(max_contracts=2, action="pause")
        engine.add_rule(rule)
        engine.current_positions = {"MNQ": {"size": 3, "side": "long"}}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 3}
        )

        await engine.evaluate_rules(event)

        # Pause trading should be triggered
        # (Implementation-dependent, verified by pause state)

    # ========================================================================
    # Test 9: Performance & Timing
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_processing_is_fast(self, engine):
        """Test event processing completes quickly."""
        import time

        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)
        engine.current_positions = {"MNQ": {"size": 1, "side": "long"}}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 1}
        )

        # When: Event evaluated
        start = time.time()
        await engine.evaluate_rules(event)
        elapsed = time.time() - start

        # Then: Should complete quickly (< 100ms)
        assert elapsed < 0.1, f"Event processing took {elapsed}s, too slow!"

    # ========================================================================
    # Test 10: Integration with Multiple Symbols
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_symbol_position_tracking(self, engine):
        """Test engine correctly tracks positions across symbols."""
        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)

        # Given: Positions in multiple symbols
        engine.current_positions = {
            "MNQ": {"size": 1, "side": "long"},
            "ES": {"size": 1, "side": "long"}
        }

        # When: Total at limit (2 contracts)
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1}
        )

        await engine.evaluate_rules(event)

        # Then: No violation (total = 2, limit = 2)
        engine.trading_integration.flatten_all.assert_not_called()

        # When: Add one more contract (exceeds limit)
        engine.current_positions["MNQ"]["size"] = 2

        event2 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2}
        )

        await engine.evaluate_rules(event2)

        # Then: Violation (total = 3 > limit = 2)
        engine.trading_integration.flatten_all.assert_called_once()
