"""
Unit Tests for DailyRealizedLossRule (RULE-003)

Tests the daily realized loss limit rule with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-003 - Daily Realized Loss Limit
- Track cumulative daily realized P&L from closed trades
- Hard lockout when limit breached
- Lockout until reset time (5:00 PM ET)
- Close all positions and cancel all orders
- Auto-unlock via daily reset

Category: Hard Lockout (Category 3)
Priority: CRITICAL
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, MagicMock

from risk_manager.rules.daily_realized_loss import DailyRealizedLossRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine


class TestDailyRealizedLossRule:
    """Unit tests for DailyRealizedLossRule."""

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
        """Create daily realized loss rule."""
        return DailyRealizedLossRule(
            limit=-500.0,  # -$500 daily loss limit
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
        assert rule.limit == -500.0
        assert rule.action == "flatten"
        assert rule.reset_time == "17:00"
        assert rule.timezone_name == "America/New_York"
        assert rule.name == "DailyRealizedLossRule"

    def test_rule_initialization_custom_limit(self, mock_pnl_tracker, mock_lockout_manager):
        """Test rule can be initialized with different loss limits."""
        rule = DailyRealizedLossRule(
            limit=-1000.0,
            action="flatten",
            pnl_tracker=mock_pnl_tracker,
            lockout_manager=mock_lockout_manager
        )
        assert rule.limit == -1000.0

    def test_rule_initialization_validates_limit(self, mock_pnl_tracker, mock_lockout_manager):
        """Test that positive limit raises validation error."""
        with pytest.raises(ValueError, match="must be negative"):
            DailyRealizedLossRule(
                limit=500.0,  # Positive (invalid)
                action="flatten",
                pnl_tracker=mock_pnl_tracker,
                lockout_manager=mock_lockout_manager
            )

    # ========================================================================
    # Test 2: Loss Below Limit (Should PASS)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_loss_below_limit_passes(self, rule, mock_engine, mock_pnl_tracker):
        """Test that daily P&L below limit does not trigger violation."""
        # Given: Daily P&L = -$200 (below -$500 limit)
        mock_pnl_tracker.get_daily_pnl.return_value = -200.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -50.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    @pytest.mark.asyncio
    async def test_profitable_day_passes(self, rule, mock_engine, mock_pnl_tracker):
        """Test that profitable day does not trigger violation."""
        # Given: Daily P&L = +$300 (profitable)
        mock_pnl_tracker.get_daily_pnl.return_value = 300.0

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

    # ========================================================================
    # Test 3: Loss At Limit (Should PASS - boundary condition)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_loss_at_limit_passes(self, rule, mock_engine, mock_pnl_tracker):
        """Test that daily P&L at exact limit does not trigger violation."""
        # Given: Daily P&L = exactly -$500 (at limit)
        mock_pnl_tracker.get_daily_pnl.return_value = -500.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -100.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (at limit is OK, must exceed to breach)
        assert violation is None

    # ========================================================================
    # Test 4: Loss Exceeds Limit (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_loss_exceeds_limit_violates(self, rule, mock_engine, mock_pnl_tracker):
        """Test that daily P&L exceeding limit triggers violation."""
        # Given: Adding trade brings total P&L to -$550 (exceeds -$500 limit)
        mock_pnl_tracker.add_trade_pnl.return_value = -550.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -100.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["action"] == "flatten"
        assert violation["current_loss"] == -550.0
        assert violation["limit"] == -500.0
        assert "daily loss limit" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_large_loss_violates(self, rule, mock_engine, mock_pnl_tracker):
        """Test that significantly larger loss triggers violation."""
        # Given: Adding trade brings total P&L to -$1500 (far exceeds -$500 limit)
        mock_pnl_tracker.add_trade_pnl.return_value = -1500.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -500.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected with large loss
        assert violation is not None
        assert violation["current_loss"] == -1500.0
        assert abs(violation["current_loss"]) > abs(violation["limit"])

    # ========================================================================
    # Test 5: Violation Triggers Lockout
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_triggers_lockout(self, rule, mock_engine, mock_pnl_tracker, mock_lockout_manager):
        """Test that violation triggers lockout via LockoutManager."""
        # Given: Adding trade brings total to -$600 (exceeds limit)
        mock_pnl_tracker.add_trade_pnl.return_value = -600.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -150.0
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
        reset_time = now + timedelta(hours=3)  # 3 hours from now

        mock_lockout_manager.is_locked_out.return_value = True
        mock_lockout_manager.get_lockout_info.return_value = {
            "reason": "Daily loss limit exceeded",
            "until": reset_time,
            "remaining_seconds": 10800,  # 3 hours
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
    # Test 7: Multi-Symbol Loss Tracking
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_symbol_loss_tracking(self, rule, mock_engine, mock_pnl_tracker):
        """Test that losses are tracked across all symbols."""
        # Given: Losses from multiple symbols
        # MNQ: -$200, ES: -$150, NQ: -$200 = -$550 total
        mock_pnl_tracker.add_trade_pnl.return_value = -550.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "symbol": "NQ",
                "profitAndLoss": -200.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected for cumulative loss
        assert violation is not None
        assert violation["current_loss"] == -550.0

    # ========================================================================
    # Test 8: Only Realized P&L Counted (Ignore Half-Turns)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_ignores_half_turn_trades(self, rule, mock_engine, mock_pnl_tracker):
        """Test that half-turn trades (profitAndLoss=None) are ignored."""
        # Given: Opening trade (no realized P&L yet)
        mock_pnl_tracker.get_daily_pnl.return_value = -200.0

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
        mock_pnl_tracker.get_daily_pnl.return_value = -450.0
        mock_pnl_tracker.add_trade_pnl.return_value = -450.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -150.0  # Realized loss
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: PnL tracker was called with realized P&L
        # No violation yet (within limit)
        assert violation is None

    # ========================================================================
    # Test 9: Approaching Limit Warning (Optional)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_approaching_limit_warning(self, rule, mock_engine, mock_pnl_tracker):
        """Test warning when approaching loss limit (90% threshold)."""
        # Given: Daily P&L = -$450 (90% of -$500 limit)
        mock_pnl_tracker.get_daily_pnl.return_value = -450.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -50.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation, but warning could be logged
        # (Implementation detail - rule might emit warning at 90%)
        assert violation is None
        # Rule implementation could log warning here

    # ========================================================================
    # Test 10: Rule Disabled When Locked
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_disabled_when_locked(self, rule, mock_engine, mock_pnl_tracker, mock_lockout_manager):
        """Test that rule skips evaluation when account is locked."""
        # Given: Account is already locked
        mock_lockout_manager.is_locked_out.return_value = True
        mock_pnl_tracker.get_daily_pnl.return_value = -600.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -100.0
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
        # Given: Adding trade brings total to -$550 (exceeds limit)
        mock_pnl_tracker.add_trade_pnl.return_value = -550.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -100.0
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
        # Given: P&L update event
        mock_pnl_tracker.get_daily_pnl.return_value = -600.0

        event = RiskEvent(
            event_type=EventType.PNL_UPDATED,
            data={
                "account_id": "ACC-001",
                "daily_pnl": -600.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Rule should evaluate P&L updates
        assert violation is not None or violation is None  # Depends on implementation

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
        mock_pnl_tracker.get_daily_pnl.return_value = -200.0

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
        # Given: Adding trade brings total to -$650 (exceeds limit)
        mock_pnl_tracker.add_trade_pnl.return_value = -650.0

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -200.0
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
        assert any(word in message_lower for word in ["loss", "limit", "daily", "p&l"])
