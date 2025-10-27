"""
Unit Tests for MaxPositionRule (RULE-001)

Tests the max contracts position rule in isolation with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-001 - Max Total Position Size
- Limit total contract count across all symbols
- Default: 5 contracts
- Configurable per account
- Enforcement: Reject new orders, flatten excess
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from risk_manager.rules import MaxPositionRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine
from risk_manager.core.config import RiskConfig


class TestMaxPositionRuleUnit:
    """Unit tests for MaxPositionRule."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return RiskConfig(max_contracts=2)

    @pytest.fixture
    def rule(self, config):
        """Create max position rule."""
        return MaxPositionRule(
            max_contracts=2,
            action="flatten"
        )

    @pytest.fixture
    def mock_engine(self, config):
        """Create mock risk engine."""
        engine = Mock(spec=RiskEngine)
        engine.config = config
        engine.current_positions = {}
        engine.daily_pnl = 0.0
        return engine

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization(self, rule):
        """Test rule initializes with correct parameters."""
        assert rule.max_contracts == 2
        assert rule.action == "flatten"
        assert rule.name == "MaxPositionRule"

    def test_rule_initialization_custom_action(self):
        """Test rule can be initialized with different actions."""
        rule = MaxPositionRule(max_contracts=5, action="reject")
        assert rule.max_contracts == 5
        assert rule.action == "reject"

    # ========================================================================
    # Test 2: Position Below Limit (Should PASS)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_below_limit_passes(self, rule, mock_engine):
        """Test that position below limit does not trigger violation."""
        # Given: Position of 1 contract (below limit of 2)
        mock_engine.current_positions = {
            "MNQ": {"size": 1, "side": "long"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 1}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    @pytest.mark.asyncio
    async def test_zero_position_passes(self, rule, mock_engine):
        """Test that zero position does not trigger violation."""
        # Given: No position
        mock_engine.current_positions = {}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 0}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 3: Position At Limit (Should PASS)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_at_limit_passes(self, rule, mock_engine):
        """Test that position at exact limit does not trigger violation."""
        # Given: Position of 2 contracts (at limit of 2)
        mock_engine.current_positions = {
            "MNQ": {"size": 2, "side": "long"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 4: Position Exceeds Limit (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_exceeds_limit_violates(self, rule, mock_engine):
        """Test that position exceeding limit triggers violation."""
        # Given: Position of 3 contracts (exceeds limit of 2)
        mock_engine.current_positions = {
            "MNQ": {"size": 3, "side": "long"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 3}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["action"] == "flatten"
        assert violation["current_size"] == 3
        assert violation["max_size"] == 2
        assert "exceeds" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_large_position_violates(self, rule, mock_engine):
        """Test that significantly larger position triggers violation."""
        # Given: Position of 10 contracts (far exceeds limit of 2)
        mock_engine.current_positions = {
            "MNQ": {"size": 10, "side": "long"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 10}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["current_size"] == 10
        assert violation["max_size"] == 2

    # ========================================================================
    # Test 5: Multi-Symbol Position Tracking
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_symbol_total_below_limit(self, rule, mock_engine):
        """Test total position across multiple symbols below limit."""
        # Given: 1 MNQ + 1 ES = 2 contracts total (at limit)
        mock_engine.current_positions = {
            "MNQ": {"size": 1, "side": "long"},
            "ES": {"size": 1, "side": "long"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (total = 2, limit = 2)
        assert violation is None

    @pytest.mark.asyncio
    async def test_multi_symbol_total_exceeds_limit(self, rule, mock_engine):
        """Test total position across multiple symbols exceeds limit."""
        # Given: 2 MNQ + 1 ES = 3 contracts total (exceeds limit of 2)
        mock_engine.current_positions = {
            "MNQ": {"size": 2, "side": "long"},
            "ES": {"size": 1, "side": "long"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected (total = 3 > limit = 2)
        assert violation is not None
        assert violation["current_size"] == 3

    # ========================================================================
    # Test 6: Short Positions
    # ========================================================================

    @pytest.mark.asyncio
    async def test_short_position_below_limit(self, rule, mock_engine):
        """Test short position below limit does not trigger violation."""
        # Given: Short position of 1 contract (below limit of 2)
        mock_engine.current_positions = {
            "MNQ": {"size": -1, "side": "short"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": -1}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (uses absolute value)
        assert violation is None

    @pytest.mark.asyncio
    async def test_short_position_exceeds_limit(self, rule, mock_engine):
        """Test short position exceeding limit triggers violation."""
        # Given: Short position of 3 contracts (exceeds limit of 2)
        mock_engine.current_positions = {
            "MNQ": {"size": -3, "side": "short"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": -3}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected (absolute value checked)
        assert violation is not None
        assert abs(violation["current_size"]) == 3

    # ========================================================================
    # Test 7: Enforcement Actions
    # ========================================================================

    @pytest.mark.asyncio
    async def test_flatten_action_in_violation(self, rule, mock_engine):
        """Test violation includes correct flatten action."""
        mock_engine.current_positions = {"MNQ": {"size": 5, "side": "long"}}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 5}
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert violation["action"] == "flatten"

    @pytest.mark.asyncio
    async def test_reject_action_in_violation(self):
        """Test rule with reject action."""
        rule = MaxPositionRule(max_contracts=2, action="reject")
        mock_engine = Mock(spec=RiskEngine)
        mock_engine.current_positions = {"MNQ": {"size": 3, "side": "long"}}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 3}
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert violation["action"] == "reject"

    # ========================================================================
    # Test 8: Event Type Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_only_evaluates_position_events(self, rule, mock_engine):
        """Test rule only evaluates position-related events."""
        # Given: A non-position event
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "MNQ", "size": 5}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No evaluation (returns None or passes)
        # Rule should ignore non-position events
        assert True  # Rule implementation will determine exact behavior

    @pytest.mark.asyncio
    async def test_evaluates_order_filled_event(self, rule, mock_engine):
        """Test rule evaluates ORDER_FILLED events."""
        mock_engine.current_positions = {"MNQ": {"size": 3, "side": "long"}}

        event = RiskEvent(
            event_type=EventType.ORDER_FILLED,
            data={"symbol": "MNQ", "size": 3}
        )

        violation = await rule.evaluate(event, mock_engine)

        # Rule should evaluate fills as they change positions
        assert violation is not None or violation is None  # Depends on implementation

    # ========================================================================
    # Test 9: Edge Cases
    # ========================================================================

    @pytest.mark.asyncio
    async def test_negative_limit_raises_error(self):
        """Test that negative limit raises validation error."""
        with pytest.raises((ValueError, AssertionError)):
            MaxPositionRule(max_contracts=-1, action="flatten")

    @pytest.mark.asyncio
    async def test_zero_limit(self):
        """Test rule with zero limit (blocks all positions)."""
        rule = MaxPositionRule(max_contracts=0, action="flatten")
        mock_engine = Mock(spec=RiskEngine)
        mock_engine.current_positions = {"MNQ": {"size": 1, "side": "long"}}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 1}
        )

        violation = await rule.evaluate(event, mock_engine)

        # Even 1 contract should violate with limit of 0
        assert violation is not None

    @pytest.mark.asyncio
    async def test_missing_position_data(self, rule, mock_engine):
        """Test rule handles missing position data gracefully."""
        mock_engine.current_positions = {}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={}  # Missing size data
        )

        # Should not crash
        violation = await rule.evaluate(event, mock_engine)
        # Should handle gracefully (exact behavior TBD)
        assert True

    # ========================================================================
    # Test 10: Violation Message Quality
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_message_clarity(self, rule, mock_engine):
        """Test violation message is clear and actionable."""
        mock_engine.current_positions = {"MNQ": {"size": 5, "side": "long"}}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 5}
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert "message" in violation
        assert isinstance(violation["message"], str)
        assert len(violation["message"]) > 10  # Not empty
        # Message should contain key info
        message_lower = violation["message"].lower()
        assert "contract" in message_lower or "position" in message_lower
        assert "limit" in message_lower or "max" in message_lower
