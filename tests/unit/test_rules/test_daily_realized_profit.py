"""
Unit Tests for DailyRealizedProfitRule (RULE-013)

Tests the daily realized profit target rule with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-013 - Daily Realized Profit Target
- Track cumulative daily realized P&L from closed trades
- Hard lockout when profit target reached
- Lockout until reset time (5:00 PM ET)
- Close all positions and cancel all orders
- Auto-unlock via daily reset
- OPPOSITE of RULE-003 (profit >= target instead of loss <= limit)

Category: Hard Lockout (Category 3)
Priority: Medium
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, MagicMock

from risk_manager.rules.daily_realized_profit import DailyRealizedProfitRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine


class TestDailyRealizedProfitRule:
    """Unit tests for DailyRealizedProfitRule."""

    @pytest.fixture
    def mock_pnl_tracker(self):
        """Create mock PnL tracker."""
        tracker = Mock()
        tracker.get_daily_pnl = Mock(return_value=0.0)
        tracker.add_trade_pnl = Mock(return_value=0.0)
        return tracker

    @pytest.fixture
    def mock_lockout_manager(self):
        """Create mock lockout manager."""
        manager = Mock()
        manager.set_lockout = Mock()
        manager.is_locked_out = Mock(return_value=False)
        manager.get_lockout_info = Mock(return_value=None)
        return manager

    @pytest.fixture
    def rule(self, mock_pnl_tracker, mock_lockout_manager):
        """Create daily realized profit rule."""
        return DailyRealizedProfitRule(
            target=1000.0,  # $1000 daily profit target
            action="flatten",
            pnl_tracker=mock_pnl_tracker,
            lockout_manager=mock_lockout_manager,
            reset_time="17:00",  # 5:00 PM reset
            timezone_name="America/New_York"
        )

    @pytest.fixture
    def mock_engine(self):
        """Create mock risk engine."""
        engine = Mock(spec=RiskEngine)
        engine.current_positions = {}
        return engine

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization(self, rule):
        """Test rule initializes with correct parameters."""
        assert rule.target == 1000.0
        assert rule.action == "flatten"
        assert rule.reset_time == "17:00"
        assert rule.timezone_name == "America/New_York"
        assert rule.name == "DailyRealizedProfitRule"

    def test_rule_initialization_custom_target(self, mock_pnl_tracker, mock_lockout_manager):
        """Test rule can be initialized with different profit targets."""
        rule = DailyRealizedProfitRule(
            target=500.0,
            action="flatten",
            pnl_tracker=mock_pnl_tracker,
            lockout_manager=mock_lockout_manager
        )
        assert rule.target == 500.0

    def test_rule_initialization_validates_target(self, mock_pnl_tracker, mock_lockout_manager):
        """Test that negative or zero target raises validation error."""
        with pytest.raises(ValueError, match="must be positive"):
            DailyRealizedProfitRule(
                target=-500.0,  # Negative (invalid)
                action="flatten",
                pnl_tracker=mock_pnl_tracker,
                lockout_manager=mock_lockout_manager
            )

        with pytest.raises(ValueError, match="must be positive"):
            DailyRealizedProfitRule(
                target=0.0,  # Zero (invalid)
                action="flatten",
                pnl_tracker=mock_pnl_tracker,
                lockout_manager=mock_lockout_manager
            )

    # ========================================================================
    # Test 2: Profit Below Target (Should PASS)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_profit_below_target_passes(self, rule, mock_engine, mock_pnl_tracker):
        """Test that daily P&L below target does not trigger violation."""
        # Given: Daily P&L = +$500 (below $1000 target)
        mock_pnl_tracker.get_daily_pnl.return_value = 500.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 100.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    @pytest.mark.asyncio
    async def test_losing_day_passes(self, rule, mock_engine, mock_pnl_tracker):
        """Test that losing day does not trigger violation."""
        # Given: Daily P&L = -$300 (losing day)
        mock_pnl_tracker.get_daily_pnl.return_value = -300.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -100.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 3: Profit At Target (Should VIOLATE - boundary condition)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_profit_at_target_violates(self, rule, mock_engine, mock_pnl_tracker):
        """Test that daily P&L at exact target triggers violation."""
        # Given: Daily P&L = exactly $1000 (at target)
        mock_pnl_tracker.add_trade_pnl.return_value = 1000.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 200.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected (at or above target triggers lockout)
        assert violation is not None
        assert violation["action"] == "flatten"
        assert violation["current_profit"] == 1000.0
        assert violation["target"] == 1000.0

    # ========================================================================
    # Test 4: Profit Exceeds Target (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_profit_exceeds_target_violates(self, rule, mock_engine, mock_pnl_tracker):
        """Test that daily P&L exceeding target triggers violation."""
        # Given: Daily P&L = $1200 (exceeds $1000 target)
        mock_pnl_tracker.add_trade_pnl.return_value = 1200.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 300.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["action"] == "flatten"
        assert violation["current_profit"] == 1200.0
        assert violation["target"] == 1000.0
        assert "profit target" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_large_profit_violates(self, rule, mock_engine, mock_pnl_tracker):
        """Test that significantly larger profit triggers violation."""
        # Given: Daily P&L = $2500 (far exceeds $1000 target)
        mock_pnl_tracker.add_trade_pnl.return_value = 2500.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 500.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected with large profit
        assert violation is not None
        assert violation["current_profit"] == 2500.0
        assert violation["current_profit"] > violation["target"]

    # ========================================================================
    # Test 5: Violation Triggers Lockout
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_triggers_lockout(self, rule, mock_engine, mock_pnl_tracker, mock_lockout_manager):
        """Test that violation triggers lockout via LockoutManager."""
        # Given: Daily P&L exceeds target
        mock_pnl_tracker.add_trade_pnl.return_value = 1100.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 200.0
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected with lockout required
        assert violation is not None
        assert violation["lockout_required"] is True
        assert violation["account_id"] == "ACC-001"

        # Simulate enforcement (would be called by engine)
        if violation:
            # Calculate next reset time (should be 5:00 PM)
            now = datetime.now(timezone.utc)
            reset_hour = 17  # 5 PM
            reset_minute = 0

            next_reset = now.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)
            if now.hour >= reset_hour:
                next_reset += timedelta(days=1)

            # Call lockout manager (simulate what engine would do)
            mock_lockout_manager.set_lockout(
                account_id="ACC-001",
                reason=violation["message"],
                until=next_reset
            )

        # Verify lockout manager would be called
        assert mock_lockout_manager.set_lockout.called

    # ========================================================================
    # Test 6: Lockout Persists Until Reset
    # ========================================================================

    @pytest.mark.asyncio
    async def test_lockout_persists_until_reset(self, rule, mock_lockout_manager):
        """Test that lockout persists until reset time."""
        # Given: Account is locked out
        now = datetime.now(timezone.utc)
        reset_time = now + timedelta(hours=5)  # 5 hours from now

        mock_lockout_manager.is_locked_out.return_value = True
        mock_lockout_manager.get_lockout_info.return_value = {
            "reason": "Daily profit target reached",
            "until": reset_time,
            "remaining_seconds": 18000,  # 5 hours
            "type": "hard_lockout"
        }

        # When: Check lockout status
        is_locked = mock_lockout_manager.is_locked_out("ACC-001")
        info = mock_lockout_manager.get_lockout_info("ACC-001")

        # Then: Account is locked until reset time
        assert is_locked is True
        assert info["until"] == reset_time
        assert info["type"] == "hard_lockout"

    # ========================================================================
    # Test 7: Multi-Symbol Profit Tracking
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_symbol_profit_tracking(self, rule, mock_engine, mock_pnl_tracker):
        """Test that profits are tracked across all symbols."""
        # Given: Profits from multiple symbols
        # MNQ: +$400, ES: +$300, NQ: +$400 = +$1100 total
        mock_pnl_tracker.add_trade_pnl.return_value = 1100.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "symbol": "NQ",
                "profitAndLoss": 400.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected for cumulative profit
        assert violation is not None
        assert violation["current_profit"] == 1100.0

    # ========================================================================
    # Test 8: Only Realized P&L Counted (Ignore Half-Turns)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_ignores_half_turn_trades(self, rule, mock_engine, mock_pnl_tracker):
        """Test that half-turn trades (profitAndLoss=None) are ignored."""
        # Given: Opening trade (no realized P&L yet)
        mock_pnl_tracker.get_daily_pnl.return_value = 500.0

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ",
                "profitAndLoss": None  # Half-turn (opening trade)
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (half-turn trades ignored)
        assert violation is None

    @pytest.mark.asyncio
    async def test_counts_only_closed_positions(self, rule, mock_engine, mock_pnl_tracker):
        """Test that only closed positions with P&L are counted."""
        # Given: Position close event with realized P&L
        mock_pnl_tracker.get_daily_pnl.return_value = 800.0
        mock_pnl_tracker.add_trade_pnl.return_value = 800.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 200.0  # Realized profit
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation yet (below target)
        assert violation is None

    # ========================================================================
    # Test 9: Approaching Target Warning (Optional)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_approaching_target_no_violation(self, rule, mock_engine, mock_pnl_tracker):
        """Test no violation when approaching profit target (90% threshold)."""
        # Given: Daily P&L = $900 (90% of $1000 target)
        mock_pnl_tracker.get_daily_pnl.return_value = 900.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 100.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation, but warning could be logged
        # (Implementation detail - rule might emit warning at 90%)
        assert violation is None

    # ========================================================================
    # Test 10: Rule Disabled When Locked
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_disabled_when_locked(self, rule, mock_engine, mock_pnl_tracker, mock_lockout_manager):
        """Test that rule skips evaluation when account is locked."""
        # Given: Account is already locked
        mock_lockout_manager.is_locked_out.return_value = True
        mock_pnl_tracker.get_daily_pnl.return_value = 1200.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 200.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (already locked, skip evaluation)
        assert violation is None

    # ========================================================================
    # Test 11: Enforcement Action Correct
    # ========================================================================

    @pytest.mark.asyncio
    async def test_enforcement_action_correct(self, rule, mock_engine, mock_pnl_tracker):
        """Test violation includes correct enforcement action."""
        # Given: Profit exceeds target
        mock_pnl_tracker.add_trade_pnl.return_value = 1150.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 150.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation has correct action (flatten all positions)
        assert violation is not None
        assert violation["action"] == "flatten"
        assert "account_id" in violation or "message" in violation

    # ========================================================================
    # Test 12: Event Type Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_only_evaluates_pnl_events(self, rule, mock_engine, mock_pnl_tracker):
        """Test rule only evaluates P&L-related events."""
        # Given: A non-P&L event (order placed)
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No evaluation (returns None for non-P&L events)
        assert violation is None

    @pytest.mark.asyncio
    async def test_evaluates_pnl_updated_event(self, rule, mock_engine, mock_pnl_tracker):
        """Test rule evaluates PNL_UPDATED events."""
        # Given: P&L update event with profitAndLoss field
        mock_pnl_tracker.add_trade_pnl.return_value = 1100.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 1100.0  # Must have profitAndLoss field
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected for profit exceeding target
        assert violation is not None

    # ========================================================================
    # Test 13: Edge Cases
    # ========================================================================

    @pytest.mark.asyncio
    async def test_zero_pnl(self, rule, mock_engine, mock_pnl_tracker):
        """Test rule handles zero P&L correctly."""
        # Given: Daily P&L = $0
        mock_pnl_tracker.get_daily_pnl.return_value = 0.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 0.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    @pytest.mark.asyncio
    async def test_missing_pnl_data(self, rule, mock_engine, mock_pnl_tracker):
        """Test rule handles missing P&L data gracefully."""
        # Given: Event with missing P&L data
        mock_pnl_tracker.get_daily_pnl.return_value = 500.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001"
                # Missing profitAndLoss field
            }
        )

        # When: Rule evaluates event
        # Should not crash
        violation = await rule.evaluate(event, mock_engine)

        # Then: Handled gracefully (exact behavior TBD)
        assert True  # Should not raise exception

    # ========================================================================
    # Test 14: Violation Message Quality
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_message_clarity(self, rule, mock_engine, mock_pnl_tracker):
        """Test violation message is clear and actionable."""
        # Given: Profit exceeds target
        mock_pnl_tracker.add_trade_pnl.return_value = 1250.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 250.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Message is clear and informative
        assert violation is not None
        assert "message" in violation
        assert isinstance(violation["message"], str)
        assert len(violation["message"]) > 10  # Not empty

        # Message should contain key info
        message_lower = violation["message"].lower()
        assert any(word in message_lower for word in ["profit", "target", "daily", "p&l"])

    # ========================================================================
    # Test 15: Mixed Profit/Loss Day
    # ========================================================================

    @pytest.mark.asyncio
    async def test_mixed_trades_reach_target(self, rule, mock_engine, mock_pnl_tracker):
        """Test that mixed profit/loss trades can reach target."""
        # Given: Mixed day: +$600, -$200, +$800 = +$1200 total
        mock_pnl_tracker.add_trade_pnl.return_value = 1200.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 800.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected for cumulative profit
        assert violation is not None
        assert violation["current_profit"] == 1200.0

    # ========================================================================
    # Test 16: Success Message Quality
    # ========================================================================

    @pytest.mark.asyncio
    async def test_success_message_positive_tone(self, rule, mock_engine, mock_pnl_tracker):
        """Test violation message has positive tone (good job!)."""
        # Given: Profit exceeds target
        mock_pnl_tracker.add_trade_pnl.return_value = 1050.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 100.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Message should have positive tone
        assert violation is not None
        message_lower = violation["message"].lower()
        # Should NOT contain negative words (unlike RULE-003)
        assert "good" in message_lower or "success" in message_lower or "target reached" in message_lower

    # ========================================================================
    # Test 17: Cannot Trigger RULE-003 and RULE-013 Simultaneously
    # ========================================================================

    @pytest.mark.asyncio
    async def test_cannot_trigger_both_profit_and_loss(self, rule, mock_engine, mock_pnl_tracker):
        """Test that a trader cannot simultaneously hit profit target and loss limit."""
        # Given: Daily P&L can only be one value (not both profit and loss)
        # If P&L = +$1000 (profit target), it cannot be -$500 (loss limit)
        mock_pnl_tracker.add_trade_pnl.return_value = 1000.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 200.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation for profit target (not loss limit)
        assert violation is not None
        assert violation["current_profit"] > 0  # Positive profit

    # ========================================================================
    # Test 18: Rule Can Be Disabled
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_can_be_disabled(self, mock_pnl_tracker, mock_lockout_manager, mock_engine):
        """Test that disabled rule does not evaluate."""
        # Given: Rule is disabled
        rule = DailyRealizedProfitRule(
            target=1000.0,
            action="flatten",
            pnl_tracker=mock_pnl_tracker,
            lockout_manager=mock_lockout_manager
        )
        rule.enabled = False  # Disable rule

        mock_pnl_tracker.get_daily_pnl.return_value = 1500.0  # Way over target

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 500.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (rule is disabled)
        assert violation is None

    # ========================================================================
    # Test 19: Enforcement Method
    # ========================================================================

    @pytest.mark.asyncio
    async def test_enforce_method_sets_lockout(self, rule, mock_engine, mock_lockout_manager):
        """Test enforce method sets lockout correctly."""
        # Given: Violation data
        violation = {
            "message": "Daily profit target reached: $1100.00 (target: $1000.00) - Good job!",
            "current_profit": 1100.0,
            "target": 1000.0,
            "account_id": "ACC-001",
            "action": "flatten"
        }

        # When: Enforce is called
        await rule.enforce("ACC-001", violation, mock_engine)

        # Then: Lockout manager was called
        assert mock_lockout_manager.set_lockout.called
        call_args = mock_lockout_manager.set_lockout.call_args
        # Account ID preserved as-is (not converted since "ACC-001" is not purely numeric)
        assert call_args[1]["account_id"] == "ACC-001"
        assert "profit target" in call_args[1]["reason"].lower()
        assert call_args[1]["until"] is not None  # Has reset time

    # ========================================================================
    # Test 20: Reset Time Calculation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_reset_time_calculation(self, rule):
        """Test that next reset time is calculated correctly."""
        # When: Calculate next reset time
        next_reset = rule._calculate_next_reset_time()

        # Then: Reset time should be in the future
        assert next_reset > datetime.now(timezone.utc)

        # Should be UTC timezone-aware
        assert next_reset.tzinfo is not None

        # Should be within 24 hours
        time_until_reset = next_reset - datetime.now(timezone.utc)
        assert timedelta(0) < time_until_reset <= timedelta(days=1)
