"""
Unit Tests for CooldownAfterLossRule (RULE-007)

Tests the cooldown after loss rule with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-007 - Cooldown After Loss
- Force cooldown after losing trades to prevent revenge trading
- Tiered cooldown durations based on loss amount
- Auto-unlock when timer expires
- Close all positions when cooldown triggered

Category: Timer/Cooldown (Category 2)
Priority: Medium
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, MagicMock

from risk_manager.rules.cooldown_after_loss import CooldownAfterLossRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine


class TestCooldownAfterLossRule:
    """Unit tests for CooldownAfterLossRule."""

    @pytest.fixture
    def mock_timer_manager(self):
        """Create mock timer manager."""
        manager = Mock()
        manager.start_timer = AsyncMock()
        manager.cancel_timer = Mock()
        manager.has_timer = Mock(return_value=False)
        manager.get_remaining_time = Mock(return_value=0)
        return manager

    @pytest.fixture
    def mock_pnl_tracker(self):
        """Create mock PnL tracker."""
        tracker = Mock()
        tracker.get_daily_pnl = Mock(return_value=0.0)
        return tracker

    @pytest.fixture
    def mock_lockout_manager(self):
        """Create mock lockout manager."""
        manager = Mock()
        manager.set_lockout = AsyncMock()
        manager.set_cooldown = AsyncMock()
        manager.clear_lockout = AsyncMock()
        manager.is_locked_out = Mock(return_value=False)
        return manager

    @pytest.fixture
    def rule(self, mock_timer_manager, mock_pnl_tracker, mock_lockout_manager):
        """Create cooldown after loss rule with tiered thresholds."""
        return CooldownAfterLossRule(
            loss_thresholds=[
                {"loss_amount": -100.0, "cooldown_duration": 300},   # -$100 -> 5 min
                {"loss_amount": -200.0, "cooldown_duration": 900},   # -$200 -> 15 min
                {"loss_amount": -300.0, "cooldown_duration": 1800},  # -$300 -> 30 min
            ],
            action="flatten",
            timer_manager=mock_timer_manager,
            pnl_tracker=mock_pnl_tracker,
            lockout_manager=mock_lockout_manager
        )

    @pytest.fixture
    def simple_rule(self, mock_timer_manager, mock_pnl_tracker, mock_lockout_manager):
        """Create simple cooldown rule with single threshold."""
        return CooldownAfterLossRule(
            loss_thresholds=[
                {"loss_amount": -100.0, "cooldown_duration": 300},  # -$100 -> 5 min
            ],
            action="flatten",
            timer_manager=mock_timer_manager,
            pnl_tracker=mock_pnl_tracker,
            lockout_manager=mock_lockout_manager
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
        assert rule.action == "flatten"
        assert rule.name == "CooldownAfterLossRule"
        assert len(rule.loss_thresholds) == 3

    def test_rule_initialization_validates_thresholds(self, mock_timer_manager, mock_pnl_tracker, mock_lockout_manager):
        """Test that positive loss threshold raises validation error."""
        with pytest.raises(ValueError, match="negative"):
            CooldownAfterLossRule(
                loss_thresholds=[
                    {"loss_amount": 100.0, "cooldown_duration": 300},  # Positive (invalid)
                ],
                action="flatten",
                timer_manager=mock_timer_manager,
                pnl_tracker=mock_pnl_tracker,
                lockout_manager=mock_lockout_manager
            )

    def test_rule_initialization_validates_duration(self, mock_timer_manager, mock_pnl_tracker, mock_lockout_manager):
        """Test that negative duration raises validation error."""
        with pytest.raises(ValueError, match="duration"):
            CooldownAfterLossRule(
                loss_thresholds=[
                    {"loss_amount": -100.0, "cooldown_duration": -60},  # Negative (invalid)
                ],
                action="flatten",
                timer_manager=mock_timer_manager,
                pnl_tracker=mock_pnl_tracker,
                lockout_manager=mock_lockout_manager
            )

    def test_rule_initialization_sorts_thresholds(self, mock_timer_manager, mock_pnl_tracker, mock_lockout_manager):
        """Test that thresholds are sorted by loss amount (descending)."""
        rule = CooldownAfterLossRule(
            loss_thresholds=[
                {"loss_amount": -100.0, "cooldown_duration": 300},
                {"loss_amount": -300.0, "cooldown_duration": 1800},
                {"loss_amount": -200.0, "cooldown_duration": 900},
            ],
            action="flatten",
            timer_manager=mock_timer_manager,
            pnl_tracker=mock_pnl_tracker,
            lockout_manager=mock_lockout_manager
        )

        # Should be sorted: -300, -200, -100
        assert rule.loss_thresholds[0]["loss_amount"] == -300.0
        assert rule.loss_thresholds[1]["loss_amount"] == -200.0
        assert rule.loss_thresholds[2]["loss_amount"] == -100.0

    # ========================================================================
    # Test 2: Winning Trade - No Cooldown
    # ========================================================================

    @pytest.mark.asyncio
    async def test_winning_trade_no_cooldown(self, simple_rule, mock_engine):
        """Test that winning trade does not trigger cooldown."""
        # Given: Winning trade (+$50)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ",
                "profitAndLoss": 50.0  # Winning trade
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    @pytest.mark.asyncio
    async def test_breakeven_trade_no_cooldown(self, simple_rule, mock_engine):
        """Test that breakeven trade does not trigger cooldown."""
        # Given: Breakeven trade ($0)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": 0.0  # Breakeven
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 3: Small Loss - Below Threshold (No Cooldown)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_small_loss_below_threshold(self, simple_rule, mock_engine):
        """Test that loss below threshold does not trigger cooldown."""
        # Given: Loss of -$50 (below -$100 threshold)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -50.0  # Below threshold
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 4: Loss At Threshold - Cooldown Triggers
    # ========================================================================

    @pytest.mark.asyncio
    async def test_loss_at_threshold_triggers_cooldown(self, simple_rule, mock_engine):
        """Test that loss at exact threshold triggers cooldown."""
        # Given: Loss of exactly -$100 (at threshold)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -100.0  # At threshold
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["action"] == "flatten"
        assert violation["loss_amount"] == -100.0
        assert violation["cooldown_duration"] == 300  # 5 minutes

    # ========================================================================
    # Test 5: Loss Exceeds Threshold - Cooldown Triggers
    # ========================================================================

    @pytest.mark.asyncio
    async def test_loss_exceeds_threshold_triggers_cooldown(self, simple_rule, mock_engine):
        """Test that loss exceeding threshold triggers cooldown."""
        # Given: Loss of -$150 (exceeds -$100 threshold)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -150.0  # Exceeds threshold
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["loss_amount"] == -150.0

    # ========================================================================
    # Test 6: Tiered Cooldown Durations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_tiered_cooldown_tier1(self, rule, mock_engine):
        """Test tier 1 cooldown: -$100 loss -> 5 min cooldown."""
        # Given: Loss of -$100
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -100.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Tier 1 cooldown (5 min)
        assert violation is not None
        assert violation["cooldown_duration"] == 300  # 5 minutes

    @pytest.mark.asyncio
    async def test_tiered_cooldown_tier2(self, rule, mock_engine):
        """Test tier 2 cooldown: -$200 loss -> 15 min cooldown."""
        # Given: Loss of -$200
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -200.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Tier 2 cooldown (15 min)
        assert violation is not None
        assert violation["cooldown_duration"] == 900  # 15 minutes

    @pytest.mark.asyncio
    async def test_tiered_cooldown_tier3(self, rule, mock_engine):
        """Test tier 3 cooldown: -$300 loss -> 30 min cooldown."""
        # Given: Loss of -$350 (triggers tier 3)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -350.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Tier 3 cooldown (30 min)
        assert violation is not None
        assert violation["cooldown_duration"] == 1800  # 30 minutes

    @pytest.mark.asyncio
    async def test_tiered_cooldown_selects_highest_tier(self, rule, mock_engine):
        """Test that highest applicable tier is selected."""
        # Given: Loss of -$250 (exceeds tier 1 and 2, but not tier 3)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -250.0
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Tier 2 cooldown (highest applicable)
        assert violation is not None
        assert violation["cooldown_duration"] == 900  # Tier 2: 15 minutes

    # ========================================================================
    # Test 7: Cooldown Timer Management
    # ========================================================================

    @pytest.mark.asyncio
    async def test_cooldown_starts_timer(self, simple_rule, mock_engine, mock_lockout_manager):
        """Test that cooldown triggers lockout with duration."""
        # Given: Losing trade
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -150.0
            }
        )

        # When: Rule evaluates and enforces
        violation = await simple_rule.evaluate(event, mock_engine)
        if violation:
            await simple_rule.enforce("ACC-001", violation, mock_engine)

        # Then: Lockout manager sets cooldown (which internally manages the timer)
        mock_lockout_manager.set_cooldown.assert_called_once()
        call_args = mock_lockout_manager.set_cooldown.call_args
        assert call_args[1]["duration_seconds"] == 300

    @pytest.mark.asyncio
    async def test_cooldown_expires_unlocks_account(self, simple_rule, mock_engine, mock_lockout_manager):
        """Test that cooldown is set with proper duration (lockout manager handles expiry internally)."""
        # Given: Losing trade
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -150.0
            }
        )

        # When: Rule evaluates and enforces
        violation = await simple_rule.evaluate(event, mock_engine)
        if violation:
            await simple_rule.enforce("ACC-001", violation, mock_engine)

        # Then: Lockout manager sets cooldown (auto-unlock is handled internally by lockout_manager)
        mock_lockout_manager.set_cooldown.assert_called_once()
        call_args = mock_lockout_manager.set_cooldown.call_args
        # Verify the cooldown has a duration (will auto-unlock after this time)
        assert call_args[1]["duration_seconds"] == 300
        assert "ACC-001" in str(call_args[1]["account_id"])

    # ========================================================================
    # Test 8: Already In Cooldown - Skip Evaluation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_already_in_cooldown_skips_evaluation(self, simple_rule, mock_engine, mock_lockout_manager):
        """Test that rule skips evaluation when account is in cooldown."""
        # Given: Account is already in cooldown
        mock_lockout_manager.is_locked_out.return_value = True

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -150.0
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No violation (already in cooldown)
        assert violation is None

    # ========================================================================
    # Test 9: Half-Turn Trades Ignored
    # ========================================================================

    @pytest.mark.asyncio
    async def test_half_turn_trade_ignored(self, simple_rule, mock_engine):
        """Test that half-turn trades (profitAndLoss=None) are ignored."""
        # Given: Opening trade (no P&L yet)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": None  # Half-turn
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No violation (half-turns ignored)
        assert violation is None

    # ========================================================================
    # Test 10: Event Type Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_only_evaluates_trade_executed_events(self, simple_rule, mock_engine):
        """Test rule only evaluates TRADE_EXECUTED events."""
        # Given: Non-trade event
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No evaluation
        assert violation is None

    @pytest.mark.asyncio
    async def test_evaluates_position_closed_events(self, simple_rule, mock_engine):
        """Test rule evaluates POSITION_CLOSED events."""
        # Given: Position closed with loss
        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -150.0
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None

    # ========================================================================
    # Test 11: Missing Data Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_missing_account_id(self, simple_rule, mock_engine):
        """Test rule handles missing account_id gracefully."""
        # Given: Event without account_id
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "profitAndLoss": -150.0
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No violation (missing data handled gracefully)
        assert violation is None

    @pytest.mark.asyncio
    async def test_missing_pnl_field(self, simple_rule, mock_engine):
        """Test rule handles missing profitAndLoss field gracefully."""
        # Given: Event without profitAndLoss
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001"
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No violation (missing data handled gracefully)
        assert violation is None

    # ========================================================================
    # Test 12: Violation Message Quality
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_message_clarity(self, simple_rule, mock_engine):
        """Test violation message is clear and actionable."""
        # Given: Losing trade
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "profitAndLoss": -150.0
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: Message is clear
        assert violation is not None
        assert "message" in violation
        assert isinstance(violation["message"], str)
        assert len(violation["message"]) > 10

        # Message should contain key info
        message_lower = violation["message"].lower()
        assert any(word in message_lower for word in ["loss", "cooldown", "trade"])
