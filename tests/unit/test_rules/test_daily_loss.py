"""
Unit Tests for DailyLossRule

Tests the daily loss limit rule which enforces maximum daily loss limits.

Rule: DailyLossRule
- Enforce maximum daily loss limit
- Default action: "flatten"
- Triggers on: PNL_UPDATED, POSITION_CLOSED events
- Limit must be negative (e.g., -1000.0)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from risk_manager.rules.daily_loss import DailyLossRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine


class TestDailyLossRuleUnit:
    """Unit tests for DailyLossRule."""

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization_default_action(self):
        """Test rule initializes with default flatten action."""
        rule = DailyLossRule(limit=-1000.0)
        assert rule.limit == -1000.0
        assert rule.action == "flatten"
        assert rule.enabled is True

    def test_rule_initialization_custom_action(self):
        """Test rule initializes with custom action."""
        rule = DailyLossRule(limit=-500.0, action="alert")
        assert rule.limit == -500.0
        assert rule.action == "alert"

    def test_rule_initialization_pause_action(self):
        """Test rule initializes with pause action."""
        rule = DailyLossRule(limit=-2000.0, action="pause")
        assert rule.limit == -2000.0
        assert rule.action == "pause"

    # ========================================================================
    # Test 2: Validation - Limit Must Be Negative
    # ========================================================================

    def test_positive_limit_raises_error(self):
        """Test that positive limit raises ValueError."""
        with pytest.raises(ValueError, match="must be negative"):
            DailyLossRule(limit=1000.0)

    def test_zero_limit_raises_error(self):
        """Test that zero limit raises ValueError."""
        with pytest.raises(ValueError, match="must be negative"):
            DailyLossRule(limit=0.0)

    def test_small_positive_limit_raises_error(self):
        """Test that even small positive limit raises ValueError."""
        with pytest.raises(ValueError, match="must be negative"):
            DailyLossRule(limit=0.01)

    # ========================================================================
    # Test 3: Event Type Filtering
    # ========================================================================

    @pytest.mark.asyncio
    async def test_ignores_non_pnl_events(self):
        """Test rule ignores events that are not P&L related."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -500.0

        # Test ORDER_PLACED event
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "MNQ"}
        )
        result = await rule.evaluate(event, engine)
        assert result is None

        # Test ORDER_FILLED event
        event = RiskEvent(
            event_type=EventType.ORDER_FILLED,
            data={"symbol": "MNQ"}
        )
        result = await rule.evaluate(event, engine)
        assert result is None

        # Test POSITION_OPENED event
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ"}
        )
        result = await rule.evaluate(event, engine)
        assert result is None

    @pytest.mark.asyncio
    async def test_evaluates_pnl_updated_event(self):
        """Test rule evaluates PNL_UPDATED events."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0  # Breach

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None  # Should trigger violation

    @pytest.mark.asyncio
    async def test_evaluates_position_closed_event(self):
        """Test rule evaluates POSITION_CLOSED events."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1200.0  # Breach

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={"symbol": "MNQ", "pnl": -1200.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None  # Should trigger violation

    # ========================================================================
    # Test 4: Rule Enabled/Disabled State
    # ========================================================================

    @pytest.mark.asyncio
    async def test_disabled_rule_returns_none(self):
        """Test disabled rule always returns None."""
        rule = DailyLossRule(limit=-1000.0)
        rule.enabled = False
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -5000.0  # Way over limit

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -5000.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is None  # Should ignore violation when disabled

    @pytest.mark.asyncio
    async def test_enabled_rule_evaluates_normally(self):
        """Test enabled rule evaluates violations."""
        rule = DailyLossRule(limit=-1000.0)
        rule.enabled = True  # Explicitly enabled
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None

    # ========================================================================
    # Test 5: P&L Below Limit (No Violation)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_pnl_within_limit_no_violation(self):
        """Test P&L within limit does not trigger violation."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -500.0  # Within limit

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is None

    @pytest.mark.asyncio
    async def test_zero_pnl_no_violation(self):
        """Test zero P&L does not trigger violation."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = 0.0  # Breakeven

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": 0.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is None

    @pytest.mark.asyncio
    async def test_positive_pnl_no_violation(self):
        """Test positive P&L (profit) does not trigger violation."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = 500.0  # Profit

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": 500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is None

    @pytest.mark.asyncio
    async def test_small_loss_no_violation(self):
        """Test small loss within limit does not trigger violation."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -10.0  # Small loss

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -10.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is None

    # ========================================================================
    # Test 6: P&L At Limit Boundary (Edge Case)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_pnl_exactly_at_limit_triggers_violation(self):
        """Test P&L exactly at limit triggers violation (boundary inclusive)."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1000.0  # Exactly at limit

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1000.0}
        )

        result = await rule.evaluate(event, engine)
        # At limit triggers violation (uses <= comparison)
        assert result is not None
        assert result["current_loss"] == -1000.0
        assert result["limit"] == -1000.0

    @pytest.mark.asyncio
    async def test_pnl_one_cent_below_limit_no_violation(self):
        """Test P&L one cent below limit does not trigger violation."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -999.99  # Just below limit

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -999.99}
        )

        result = await rule.evaluate(event, engine)
        assert result is None

    # ========================================================================
    # Test 7: P&L Exceeds Limit (Violation)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_pnl_exceeds_limit_triggers_violation(self):
        """Test P&L exceeding limit triggers violation."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0  # Exceeds limit

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None

    @pytest.mark.asyncio
    async def test_pnl_one_cent_over_limit_triggers_violation(self):
        """Test P&L one cent over limit triggers violation."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1000.01  # Just over limit

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1000.01}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None

    @pytest.mark.asyncio
    async def test_large_loss_triggers_violation(self):
        """Test large loss far exceeding limit triggers violation."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -5000.0  # Way over limit

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -5000.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None

    # ========================================================================
    # Test 8: Violation Structure and Content
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_contains_rule_name(self):
        """Test violation includes rule name."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert "rule" in result
        assert result["rule"] == "DailyLossRule"

    @pytest.mark.asyncio
    async def test_violation_contains_message(self):
        """Test violation includes descriptive message."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 10
        assert "loss limit exceeded" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_violation_contains_current_loss(self):
        """Test violation includes current loss value."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert "current_loss" in result
        assert result["current_loss"] == -1500.0

    @pytest.mark.asyncio
    async def test_violation_contains_limit(self):
        """Test violation includes limit value."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert "limit" in result
        assert result["limit"] == -1000.0

    @pytest.mark.asyncio
    async def test_violation_contains_action(self):
        """Test violation includes enforcement action."""
        rule = DailyLossRule(limit=-1000.0, action="flatten")
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert "action" in result
        assert result["action"] == "flatten"

    # ========================================================================
    # Test 9: Different Actions
    # ========================================================================

    @pytest.mark.asyncio
    async def test_alert_action_in_violation(self):
        """Test violation with alert action."""
        rule = DailyLossRule(limit=-1000.0, action="alert")
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert result["action"] == "alert"

    @pytest.mark.asyncio
    async def test_pause_action_in_violation(self):
        """Test violation with pause action."""
        rule = DailyLossRule(limit=-1000.0, action="pause")
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert result["action"] == "pause"

    # ========================================================================
    # Test 10: Different Limit Values
    # ========================================================================

    @pytest.mark.asyncio
    async def test_small_limit_value(self):
        """Test rule with small loss limit."""
        rule = DailyLossRule(limit=-50.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -100.0  # Exceeds

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -100.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert result["limit"] == -50.0

    @pytest.mark.asyncio
    async def test_large_limit_value(self):
        """Test rule with large loss limit."""
        rule = DailyLossRule(limit=-10000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -5000.0  # Within limit

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -5000.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is None

    @pytest.mark.asyncio
    async def test_fractional_limit_value(self):
        """Test rule with fractional loss limit."""
        rule = DailyLossRule(limit=-123.45)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -150.00  # Exceeds

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -150.00}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert result["limit"] == -123.45

    # ========================================================================
    # Test 11: Message Formatting Quality
    # ========================================================================

    @pytest.mark.asyncio
    async def test_message_shows_formatted_values(self):
        """Test violation message shows properly formatted dollar values."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1234.56

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1234.56}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        message = result["message"]
        # Should contain formatted values with $ and 2 decimal places
        assert "$" in message
        assert "1234.56" in message or "1,234.56" in message
        assert "1000.00" in message or "1,000.00" in message

    @pytest.mark.asyncio
    async def test_message_clarity(self):
        """Test violation message is clear and actionable."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1500.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        message = result["message"].lower()
        # Message should explain what happened
        assert "loss" in message or "pnl" in message
        assert "limit" in message
        assert "exceeded" in message

    # ========================================================================
    # Test 12: Multiple Violations in Sequence
    # ========================================================================

    @pytest.mark.asyncio
    async def test_consecutive_violations(self):
        """Test rule triggers on consecutive violations."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)

        # First violation
        engine.daily_pnl = -1500.0
        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )
        result1 = await rule.evaluate(event, engine)
        assert result1 is not None

        # Second violation (worse)
        engine.daily_pnl = -2000.0
        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -2000.0}
        )
        result2 = await rule.evaluate(event, engine)
        assert result2 is not None

    @pytest.mark.asyncio
    async def test_violation_then_recovery(self):
        """Test violation followed by recovery within limit."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)

        # First violation
        engine.daily_pnl = -1500.0
        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1500.0}
        )
        result1 = await rule.evaluate(event, engine)
        assert result1 is not None

        # Recovery (back within limit)
        engine.daily_pnl = -800.0
        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -800.0}
        )
        result2 = await rule.evaluate(event, engine)
        assert result2 is None

    # ========================================================================
    # Test 13: Edge Cases
    # ========================================================================

    @pytest.mark.asyncio
    async def test_very_small_breach(self):
        """Test rule detects even very small breaches."""
        rule = DailyLossRule(limit=-1000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -1000.001  # Tiny breach

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -1000.001}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None

    @pytest.mark.asyncio
    async def test_negative_limit_with_large_negative_pnl(self):
        """Test large negative P&L against negative limit."""
        rule = DailyLossRule(limit=-5000.0)
        engine = Mock(spec=RiskEngine)
        engine.daily_pnl = -10000.0  # Exceeds

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={"daily_pnl": -10000.0}
        )

        result = await rule.evaluate(event, engine)
        assert result is not None
        assert result["current_loss"] == -10000.0
        assert result["limit"] == -5000.0
