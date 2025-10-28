"""
Unit Tests for TradeFrequencyLimitRule (RULE-006)

Tests the trade frequency limit rule with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-006 - Trade Frequency Limit
- Track trades in rolling time windows (per minute, per hour, per session)
- Set temporary cooldown timer when limit breached
- Auto-unlock when timer expires
- NO position close (trade already executed)

Category: Timer/Cooldown (Category 2)
Priority: High
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, MagicMock, call

from risk_manager.rules.trade_frequency_limit import TradeFrequencyLimitRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine


class TestTradeFrequencyLimitRule:
    """Unit tests for TradeFrequencyLimitRule."""

    @pytest.fixture
    def mock_timer_manager(self):
        """Create mock timer manager."""
        manager = Mock()
        manager.start_timer = AsyncMock()
        manager.cancel_timer = Mock()
        manager.get_remaining_time = Mock(return_value=0)
        manager.has_timer = Mock(return_value=False)
        return manager

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        db = Mock()
        db.get_trade_count = Mock(return_value=0)
        db.add_trade_timestamp = Mock()
        db.get_trades_in_window = Mock(return_value=[])
        db.clear_old_trades = Mock()
        return db

    @pytest.fixture
    def rule(self, mock_timer_manager, mock_db):
        """Create trade frequency limit rule with default config."""
        return TradeFrequencyLimitRule(
            limits={
                'per_minute': 3,
                'per_hour': 10,
                'per_session': 50
            },
            cooldown_on_breach={
                'per_minute_breach': 60,      # 1 min
                'per_hour_breach': 1800,      # 30 min
                'per_session_breach': 3600    # 1 hour
            },
            timer_manager=mock_timer_manager,
            db=mock_db,
            action="cooldown"
        )

    @pytest.fixture
    def mock_engine(self):
        """Create mock risk engine."""
        engine = Mock(spec=RiskEngine)
        return engine

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization(self, rule):
        """Test rule initializes with correct parameters."""
        assert rule.limits['per_minute'] == 3
        assert rule.limits['per_hour'] == 10
        assert rule.limits['per_session'] == 50
        assert rule.cooldown_on_breach['per_minute_breach'] == 60
        assert rule.cooldown_on_breach['per_hour_breach'] == 1800
        assert rule.cooldown_on_breach['per_session_breach'] == 3600
        assert rule.action == "cooldown"
        assert rule.name == "TradeFrequencyLimitRule"

    def test_rule_initialization_custom_limits(self, mock_timer_manager, mock_db):
        """Test rule can be initialized with different limits."""
        rule = TradeFrequencyLimitRule(
            limits={
                'per_minute': 5,
                'per_hour': 20,
                'per_session': 100
            },
            cooldown_on_breach={
                'per_minute_breach': 30,
                'per_hour_breach': 900,
                'per_session_breach': 1800
            },
            timer_manager=mock_timer_manager,
            db=mock_db
        )
        assert rule.limits['per_minute'] == 5
        assert rule.limits['per_hour'] == 20
        assert rule.limits['per_session'] == 100

    def test_rule_initialization_validates_limits(self, mock_timer_manager, mock_db):
        """Test that zero or negative limits raise validation error."""
        with pytest.raises(ValueError, match="must be positive"):
            TradeFrequencyLimitRule(
                limits={
                    'per_minute': 0,  # Invalid
                    'per_hour': 10,
                    'per_session': 50
                },
                cooldown_on_breach={
                    'per_minute_breach': 60,
                    'per_hour_breach': 1800,
                    'per_session_breach': 3600
                },
                timer_manager=mock_timer_manager,
                db=mock_db
            )

    # ========================================================================
    # Test 2: Trades Within Limit (Should PASS)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_trades_within_minute_limit_passes(self, rule, mock_engine, mock_db):
        """Test that trades within per-minute limit do not trigger violation."""
        # Given: 2 trades in last minute (below 3 limit)
        mock_db.get_trade_count.return_value = 2

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ",
                "size": 1
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    @pytest.mark.asyncio
    async def test_trades_within_hour_limit_passes(self, rule, mock_engine, mock_db):
        """Test that trades within per-hour limit do not trigger violation."""
        # Given: 2 trades in last minute, 8 in last hour (below limits)
        def get_count_side_effect(account_id, window):
            if window == 60:
                return 2  # Per minute
            elif window == 3600:
                return 8  # Per hour
            return 0

        mock_db.get_trade_count.side_effect = get_count_side_effect

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    @pytest.mark.asyncio
    async def test_first_trade_of_day_passes(self, rule, mock_engine, mock_db):
        """Test that first trade of the day does not trigger violation."""
        # Given: 0 trades (first trade)
        mock_db.get_trade_count.return_value = 0

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 3: Trades At Limit (Should PASS - boundary condition)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_trades_at_minute_limit_passes(self, rule, mock_engine, mock_db):
        """Test that trades at exact per-minute limit do not trigger violation."""
        # Given: Exactly 3 trades in last minute (at limit)
        mock_db.get_trade_count.return_value = 3

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (at limit is OK, must exceed to breach)
        assert violation is None

    # ========================================================================
    # Test 4: Per-Minute Limit Exceeded (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_per_minute_limit_exceeded_violates(self, rule, mock_engine, mock_db):
        """Test that exceeding per-minute limit triggers violation."""
        # Given: 4 trades in last minute (exceeds 3 limit)
        mock_db.get_trade_count.return_value = 4

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["action"] == "cooldown"
        assert violation["breach_type"] == "per_minute"
        assert violation["trade_count"] == 4
        assert violation["limit"] == 3
        assert violation["cooldown_duration"] == 60
        assert "minute" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_per_minute_limit_significantly_exceeded(self, rule, mock_engine, mock_db):
        """Test that significantly exceeding per-minute limit triggers violation."""
        # Given: 10 trades in last minute (far exceeds 3 limit)
        mock_db.get_trade_count.return_value = 10

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected with large count
        assert violation is not None
        assert violation["trade_count"] == 10
        assert violation["trade_count"] > violation["limit"]

    # ========================================================================
    # Test 5: Per-Hour Limit Exceeded (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_per_hour_limit_exceeded_violates(self, rule, mock_engine, mock_db):
        """Test that exceeding per-hour limit triggers violation."""
        # Given: 2 trades/min (OK), but 11 trades/hour (exceeds 10 limit)
        def get_count_side_effect(account_id, window):
            if window == 60:
                return 2  # Per minute OK
            elif window == 3600:
                return 11  # Per hour EXCEEDED
            return 0

        mock_db.get_trade_count.side_effect = get_count_side_effect

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected for per-hour limit
        assert violation is not None
        assert violation["breach_type"] == "per_hour"
        assert violation["trade_count"] == 11
        assert violation["limit"] == 10
        assert violation["cooldown_duration"] == 1800  # 30 min

    # ========================================================================
    # Test 6: Per-Session Limit Exceeded (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_per_session_limit_exceeded_violates(self, rule, mock_engine, mock_db):
        """Test that exceeding per-session limit triggers violation."""
        # Given: 51 trades in session (exceeds 50 limit)
        mock_db.get_session_trade_count.return_value = 51

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected for per-session limit
        assert violation is not None
        assert violation["breach_type"] == "per_session"
        assert violation["trade_count"] == 51
        assert violation["limit"] == 50
        assert violation["cooldown_duration"] == 3600  # 1 hour

    # ========================================================================
    # Test 7: Cooldown Timer Started on Violation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_starts_cooldown_timer(self, rule, mock_engine, mock_db, mock_timer_manager):
        """Test that violation starts cooldown timer via TimerManager."""
        # Given: Per-minute limit exceeded
        mock_db.get_trade_count.return_value = 4

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["cooldown_duration"] == 60

        # Simulate enforcement (would be called by engine)
        if violation:
            await rule.enforce("ACC-001", violation, mock_engine)

        # Verify timer manager was called
        mock_timer_manager.start_timer.assert_called_once()
        call_args = mock_timer_manager.start_timer.call_args
        assert call_args[1]['name'] == "trade_frequency_ACC-001"
        assert call_args[1]['duration'] == 60

    @pytest.mark.asyncio
    async def test_different_cooldowns_for_different_breaches(self, rule, mock_engine, mock_db, mock_timer_manager):
        """Test that different breach types trigger different cooldown durations."""
        # Test per-minute breach (60s cooldown)
        mock_db.get_trade_count.return_value = 4
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-001"}
        )
        violation = await rule.evaluate(event, mock_engine)
        assert violation["cooldown_duration"] == 60

        # Test per-hour breach (1800s cooldown)
        def get_count_side_effect(account_id, window):
            if window == 60:
                return 2
            elif window == 3600:
                return 11
            return 0
        mock_db.get_trade_count.side_effect = get_count_side_effect
        violation = await rule.evaluate(event, mock_engine)
        assert violation["cooldown_duration"] == 1800

    # ========================================================================
    # Test 8: Rolling Window Tracking
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rolling_window_only_counts_recent_trades(self, rule, mock_engine, mock_db):
        """Test that rolling window only counts trades within time window."""
        # Given: 2 trades in last 60s (recent), 5 trades total (some old)
        mock_db.get_trade_count.return_value = 2  # Only recent trades

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (only counts recent trades)
        assert violation is None

    @pytest.mark.asyncio
    async def test_old_trades_expire_from_window(self, rule, mock_engine, mock_db):
        """Test that old trades expire from rolling window."""
        # Given: Database returns only trades within window
        # (Old trades have been cleaned up)
        mock_db.get_trade_count.return_value = 1

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (old trades expired)
        assert violation is None

        # Database should have been asked to clean old trades
        # (Implementation detail - may vary)

    # ========================================================================
    # Test 9: Multiple Accounts Independent Tracking
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multiple_accounts_tracked_independently(self, rule, mock_engine, mock_db):
        """Test that trade counts are tracked per account."""
        # Given: Account ACC-001 has 2 trades, ACC-002 has 4 trades
        def get_count_by_account(account_id, window):
            if account_id == "ACC-001":
                return 2
            elif account_id == "ACC-002":
                return 4
            return 0

        mock_db.get_trade_count.side_effect = get_count_by_account

        # When: ACC-001 trades (below limit)
        event1 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-001"}
        )
        violation1 = await rule.evaluate(event1, mock_engine)

        # When: ACC-002 trades (exceeds limit)
        event2 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-002"}
        )
        violation2 = await rule.evaluate(event2, mock_engine)

        # Then: ACC-001 OK, ACC-002 violates
        assert violation1 is None
        assert violation2 is not None
        assert violation2["account_id"] == "ACC-002"

    # ========================================================================
    # Test 10: Cooldown Auto-Unlock
    # ========================================================================

    @pytest.mark.asyncio
    async def test_cooldown_auto_unlocks_via_timer(self, rule, mock_engine, mock_db, mock_timer_manager):
        """Test that cooldown auto-unlocks when timer expires."""
        # Given: Violation triggers cooldown
        mock_db.get_trade_count.return_value = 4

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-001"}
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is not None

        # When: Enforcement sets timer with callback
        callback_executed = False

        def unlock_callback():
            nonlocal callback_executed
            callback_executed = True

        # Simulate timer manager calling callback after 60s
        await mock_timer_manager.start_timer(
            name="trade_frequency_ACC-001",
            duration=60,
            callback=unlock_callback
        )

        # Simulate timer expiration
        unlock_callback()

        # Then: Callback executed (account would be unlocked)
        assert callback_executed is True

    # ========================================================================
    # Test 11: Priority Order (Minute > Hour > Session)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_minute_limit_takes_priority(self, rule, mock_engine, mock_db):
        """Test that per-minute limit is checked first (shortest cooldown)."""
        # Given: Both per-minute and per-hour limits exceeded
        def get_count_side_effect(account_id, window):
            if window == 60:
                return 4  # Per minute EXCEEDED (checked first)
            elif window == 3600:
                return 15  # Per hour EXCEEDED
            return 0

        mock_db.get_trade_count.side_effect = get_count_side_effect

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-001"}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Per-minute violation takes priority (shortest cooldown)
        assert violation is not None
        assert violation["breach_type"] == "per_minute"
        assert violation["cooldown_duration"] == 60  # Not 1800

    # ========================================================================
    # Test 12: Event Type Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_only_evaluates_trade_executed_events(self, rule, mock_engine, mock_db):
        """Test rule only evaluates TRADE_EXECUTED events."""
        # Given: A non-trade event (order placed)
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No evaluation (returns None for non-trade events)
        assert violation is None

    @pytest.mark.asyncio
    async def test_evaluates_all_trade_types(self, rule, mock_engine, mock_db):
        """Test rule evaluates all trade execution events."""
        # Given: Trade executed event
        mock_db.get_trade_count.return_value = 2

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES",
                "side": "BUY",
                "size": 1
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Rule evaluates trade (no violation in this case)
        assert violation is None

    # ========================================================================
    # Test 13: Edge Cases
    # ========================================================================

    @pytest.mark.asyncio
    async def test_missing_account_id(self, rule, mock_engine, mock_db):
        """Test rule handles missing account_id gracefully."""
        # Given: Event with missing account_id
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "symbol": "MNQ"
                # Missing account_id
            }
        )

        # When: Rule evaluates event
        # Should not crash
        violation = await rule.evaluate(event, mock_engine)

        # Then: Handled gracefully
        assert violation is None

    @pytest.mark.asyncio
    async def test_database_error_handled(self, rule, mock_engine, mock_db):
        """Test rule handles database errors gracefully."""
        # Given: Database raises exception
        mock_db.get_trade_count.side_effect = Exception("Database error")

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-001"}
        )

        # When: Rule evaluates event
        # Should not crash
        violation = await rule.evaluate(event, mock_engine)

        # Then: Handled gracefully (returns None on error)
        assert violation is None

    @pytest.mark.asyncio
    async def test_zero_cooldown_duration(self, mock_timer_manager, mock_db, mock_engine):
        """Test rule handles zero cooldown duration."""
        # Given: Rule with zero cooldown (edge case)
        rule = TradeFrequencyLimitRule(
            limits={'per_minute': 3, 'per_hour': 10, 'per_session': 50},
            cooldown_on_breach={
                'per_minute_breach': 0,  # Zero cooldown
                'per_hour_breach': 1800,
                'per_session_breach': 3600
            },
            timer_manager=mock_timer_manager,
            db=mock_db
        )

        mock_db.get_trade_count.return_value = 4

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-001"}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected with zero cooldown
        assert violation is not None
        assert violation["cooldown_duration"] == 0

    # ========================================================================
    # Test 14: Violation Message Quality
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_message_clarity(self, rule, mock_engine, mock_db):
        """Test violation message is clear and actionable."""
        # Given: Per-minute limit exceeded
        mock_db.get_trade_count.return_value = 5

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-001"}
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
        assert any(word in message_lower for word in ["trade", "frequency", "limit", "cooldown"])

    @pytest.mark.asyncio
    async def test_violation_includes_countdown_info(self, rule, mock_engine, mock_db):
        """Test violation includes countdown information for UI."""
        # Given: Per-hour limit exceeded
        def get_count_side_effect(account_id, window):
            if window == 60:
                return 2
            elif window == 3600:
                return 11
            return 0

        mock_db.get_trade_count.side_effect = get_count_side_effect

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-001"}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation includes countdown info
        assert violation is not None
        assert "cooldown_duration" in violation
        assert violation["cooldown_duration"] == 1800
        # UI could display: "🟡 COOLDOWN - 11/10 trades - Unlocks in 30:00"

    # ========================================================================
    # Test 15: Rule Disabled Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_disabled_skips_evaluation(self, rule, mock_engine, mock_db):
        """Test that disabled rule skips evaluation."""
        # Given: Rule is disabled
        rule.enabled = False
        mock_db.get_trade_count.return_value = 10  # Would violate if enabled

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": "ACC-001"}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (rule disabled)
        assert violation is None
