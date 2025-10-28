"""
Integration Tests for RULE-007: Cooldown After Loss

Tests the complete integration of CooldownAfterLossRule with:
- Real TimerManager (countdown timers)
- Real LockoutManager (temporary lockouts)
- Real Database (SQLite persistence)
- Real P&L tracking (from trade events)
- Real event sequence

This validates that the rule works end-to-end with real components,
not mocked dependencies.

Flow: Trade Event → Rule Evaluates → Timer Starts → Lockout Set → Timer Expires → Auto Unlock
"""

import asyncio
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from risk_manager.rules.cooldown_after_loss import CooldownAfterLossRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.state.timer_manager import TimerManager
from risk_manager.state.lockout_manager import LockoutManager
from risk_manager.state.database import Database
from risk_manager.state.pnl_tracker import PnLTracker


class TestCooldownAfterLossIntegration:
    """Integration tests for RULE-007 with real components."""

    @pytest.fixture
    async def db(self, tmp_path):
        """Create real test database."""
        db_path = tmp_path / "test_cooldown_integration.db"
        database = Database(db_path)
        yield database
        database.close()

    @pytest.fixture
    async def timer_manager(self):
        """Create real timer manager."""
        manager = TimerManager()
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.fixture
    async def lockout_manager(self, db, timer_manager):
        """Create real lockout manager."""
        manager = LockoutManager(db, timer_manager)
        await manager.start()
        yield manager
        await manager.shutdown()

    @pytest.fixture
    async def pnl_tracker(self, db):
        """Create real P&L tracker."""
        return PnLTracker(db)

    @pytest.fixture
    async def simple_rule(self, timer_manager, pnl_tracker, lockout_manager):
        """Create rule with single threshold for testing."""
        return CooldownAfterLossRule(
            loss_thresholds=[
                {"loss_amount": -100.0, "cooldown_duration": 2}  # 2s for fast testing
            ],
            timer_manager=timer_manager,
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_manager,
            action="flatten"
        )

    @pytest.fixture
    async def tiered_rule(self, timer_manager, pnl_tracker, lockout_manager):
        """Create rule with tiered thresholds."""
        return CooldownAfterLossRule(
            loss_thresholds=[
                {"loss_amount": -100.0, "cooldown_duration": 2},   # Tier 1: 2s
                {"loss_amount": -200.0, "cooldown_duration": 4},   # Tier 2: 4s
                {"loss_amount": -300.0, "cooldown_duration": 6}    # Tier 3: 6s
            ],
            timer_manager=timer_manager,
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_manager,
            action="flatten"
        )

    @pytest.fixture
    def mock_engine(self):
        """Create mock risk engine."""
        return Mock()

    # ========================================================================
    # Test 1: Full Cooldown After Loss Flow
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_cooldown_flow_with_timer_expiry(
        self, simple_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test complete flow: Loss → Violation → Timer → Lockout → Auto-unlock.

        Flow:
        1. Trade executed: -$150 loss (>= -$100 threshold)
        2. Verify violation triggered
        3. Verify 2-second cooldown timer started
        4. Verify lockout set
        5. Wait 2+ seconds (real timer)
        6. Verify lockout cleared automatically
        7. Verify account can trade again
        """
        account_id = 123

        # Given: Losing trade event
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": account_id,
                "symbol": "MNQ",
                "profitAndLoss": -150.0
            }
        )

        # When: Rule evaluates event
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["loss_amount"] == -150.0
        assert violation["cooldown_duration"] == 2
        assert violation["account_id"] == account_id

        # When: Enforcement triggered
        await simple_rule.enforce(account_id, violation, mock_engine)

        # Then: Lockout is active
        assert lockout_manager.is_locked_out(account_id)

        # And: Timer is running (LockoutManager uses "lockout_" prefix)
        assert timer_manager.has_timer(f"lockout_{account_id}")

        # And: Remaining time is approximately 2 seconds
        remaining = timer_manager.get_remaining_time(f"lockout_{account_id}")
        assert 1 <= remaining <= 2

        # When: Wait for timer to expire (2.5s to be safe)
        await asyncio.sleep(2.5)

        # Then: Lockout is automatically cleared
        assert not lockout_manager.is_locked_out(account_id)

        # And: Timer is removed
        assert not timer_manager.has_timer(f"lockout_{account_id}")

    # ========================================================================
    # Test 2: Tiered Cooldown System
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tiered_cooldown_selects_correct_duration(
        self, tiered_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test tiered cooldown system selects correct duration.

        Config: -$100 → 2s, -$200 → 4s, -$300 → 6s
        Loss: -$250 → Should trigger -$200 tier (4s)
        """
        account_id = 456

        # Given: Loss of -$250 (triggers tier 2)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": account_id,
                "profitAndLoss": -250.0
            }
        )

        # When: Rule evaluates
        violation = await tiered_rule.evaluate(event, mock_engine)

        # Then: Tier 2 selected (4s cooldown)
        assert violation is not None
        assert violation["cooldown_duration"] == 4

        # When: Enforcement triggered
        await tiered_rule.enforce(account_id, violation, mock_engine)

        # Then: Timer duration is 4 seconds
        remaining = timer_manager.get_remaining_time(f"lockout_{account_id}")
        assert 3 <= remaining <= 4

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tiered_cooldown_tier1(
        self, tiered_rule, lockout_manager, timer_manager, mock_engine
    ):
        """Test tier 1 cooldown: -$100 loss → 2s cooldown."""
        account_id = 101

        # Given: Loss exactly at tier 1 threshold
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -100.0}
        )

        # When: Evaluate and enforce
        violation = await tiered_rule.evaluate(event, mock_engine)
        assert violation["cooldown_duration"] == 2

        await tiered_rule.enforce(account_id, violation, mock_engine)

        # Then: Timer is 2 seconds
        remaining = timer_manager.get_remaining_time(f"lockout_{account_id}")
        assert 1 <= remaining <= 2

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tiered_cooldown_tier3(
        self, tiered_rule, lockout_manager, timer_manager, mock_engine
    ):
        """Test tier 3 cooldown: -$350 loss → 6s cooldown."""
        account_id = 103

        # Given: Loss exceeding tier 3 threshold
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -350.0}
        )

        # When: Evaluate and enforce
        violation = await tiered_rule.evaluate(event, mock_engine)
        assert violation["cooldown_duration"] == 6

        await tiered_rule.enforce(account_id, violation, mock_engine)

        # Then: Timer is 6 seconds
        remaining = timer_manager.get_remaining_time(f"lockout_{account_id}")
        assert 5 <= remaining <= 6

    # ========================================================================
    # Test 3: Timer + Lockout Integration
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_timer_callback_clears_lockout(
        self, simple_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test that timer expiry callback clears lockout.

        Verifies:
        1. Lockout set when cooldown triggers
        2. Timer callback registered
        3. Timer expires and calls callback
        4. Callback clears lockout
        """
        account_id = 789

        # Given: Losing trade
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -150.0}
        )

        # When: Violation and enforcement
        violation = await simple_rule.evaluate(event, mock_engine)
        await simple_rule.enforce(account_id, violation, mock_engine)

        # Then: Lockout is active
        assert lockout_manager.is_locked_out(account_id)

        # Get lockout info
        info = lockout_manager.get_lockout_info(account_id)
        assert info is not None
        assert "Cooldown" in info["reason"] or "loss" in info["reason"].lower()

        # When: Timer expires
        await asyncio.sleep(2.5)

        # Then: Lockout cleared by timer callback
        assert not lockout_manager.is_locked_out(account_id)

        # And: Lockout info is None
        info = lockout_manager.get_lockout_info(account_id)
        assert info is None

    # ========================================================================
    # Test 4: Winning Trade → No Cooldown
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_winning_trade_no_cooldown_no_timer(
        self, simple_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test that winning trade does not trigger cooldown or timer.

        Verifies:
        1. No violation
        2. No timer started
        3. No lockout set
        """
        account_id = 999

        # Given: Winning trade
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": 200.0}
        )

        # When: Rule evaluates
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

        # And: No timer started
        assert not timer_manager.has_timer(f"lockout_{account_id}")

        # And: No lockout
        assert not lockout_manager.is_locked_out(account_id)

    # ========================================================================
    # Test 5: Multi-Account Independence
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_account_independent_cooldowns(
        self, simple_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test that multiple accounts have independent cooldown timers.

        Accounts:
        - Account A: -$150 loss → cooldown
        - Account B: -$50 loss → no cooldown
        - Account C: +$100 profit → no cooldown
        """
        account_a = 111
        account_b = 222
        account_c = 333

        # Account A: Losing trade (triggers cooldown)
        event_a = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_a, "profitAndLoss": -150.0}
        )
        violation_a = await simple_rule.evaluate(event_a, mock_engine)
        assert violation_a is not None
        await simple_rule.enforce(account_a, violation_a, mock_engine)

        # Account B: Small loss (below threshold)
        event_b = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_b, "profitAndLoss": -50.0}
        )
        violation_b = await simple_rule.evaluate(event_b, mock_engine)
        assert violation_b is None

        # Account C: Winning trade
        event_c = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_c, "profitAndLoss": 100.0}
        )
        violation_c = await simple_rule.evaluate(event_c, mock_engine)
        assert violation_c is None

        # Verify independent states
        assert lockout_manager.is_locked_out(account_a)  # Locked
        assert not lockout_manager.is_locked_out(account_b)  # Not locked
        assert not lockout_manager.is_locked_out(account_c)  # Not locked

        assert timer_manager.has_timer(f"lockout_{account_a}")  # Timer running
        assert not timer_manager.has_timer(f"lockout_{account_b}")  # No timer
        assert not timer_manager.has_timer(f"lockout_{account_c}")  # No timer

        # Wait for account A timer to expire
        await asyncio.sleep(2.5)

        # Account A now unlocked
        assert not lockout_manager.is_locked_out(account_a)

        # Other accounts remain unchanged
        assert not lockout_manager.is_locked_out(account_b)
        assert not lockout_manager.is_locked_out(account_c)

    # ========================================================================
    # Test 6: Lockout Persistence
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_lockout_persists_to_database(
        self, simple_rule, lockout_manager, db, mock_engine
    ):
        """
        Test that lockout is persisted to database.

        Verifies:
        1. Lockout written to DB
        2. Lockout survives manager restart
        3. Lockout can be retrieved from DB
        """
        account_id = 555

        # Given: Cooldown triggered
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -150.0}
        )
        violation = await simple_rule.evaluate(event, mock_engine)
        await simple_rule.enforce(account_id, violation, mock_engine)

        # Then: Lockout in database
        rows = db.execute(
            "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
            (str(account_id),)
        )
        assert len(rows) == 1
        assert rows[0]["account_id"] == str(account_id)
        assert rows[0]["active"] == 1

        # Verify lockout details
        lockout_row = rows[0]
        assert "Cooldown" in lockout_row["reason"] or "loss" in lockout_row["reason"].lower()
        assert lockout_row["expires_at"] is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_lockout_loaded_from_database_on_restart(
        self, timer_manager, pnl_tracker, db, tmp_path, mock_engine
    ):
        """
        Test that lockouts are restored from database on restart.

        Flow:
        1. Trigger cooldown → lockout persisted
        2. Create new lockout manager (simulates restart)
        3. Verify lockout loaded from DB
        4. Verify lockout is still active
        """
        account_id = 666

        # Step 1: Create initial manager and trigger cooldown
        lockout_mgr_1 = LockoutManager(db, timer_manager)
        await lockout_mgr_1.start()

        rule_1 = CooldownAfterLossRule(
            loss_thresholds=[{"loss_amount": -100.0, "cooldown_duration": 10}],
            timer_manager=timer_manager,
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_mgr_1,
            action="flatten"
        )

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -150.0}
        )
        violation = await rule_1.evaluate(event, mock_engine)
        await rule_1.enforce(account_id, violation, mock_engine)

        # Verify lockout active
        assert lockout_mgr_1.is_locked_out(account_id)

        # Shutdown first manager
        await lockout_mgr_1.shutdown()

        # Step 2: Create new manager (simulates restart)
        lockout_mgr_2 = LockoutManager(db, timer_manager)
        # This should load lockouts from DB
        lockout_mgr_2.load_lockouts_from_db()

        # Step 3: Verify lockout loaded
        assert lockout_mgr_2.is_locked_out(account_id)

        # Verify lockout info
        info = lockout_mgr_2.get_lockout_info(account_id)
        assert info is not None
        assert info["type"] == "hard_lockout"  # Restored as hard lockout

        # Cleanup
        await lockout_mgr_2.shutdown()

    # ========================================================================
    # Test 7: Rapid Loss Sequence
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rapid_loss_sequence_only_first_triggers_timer(
        self, simple_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test rapid loss sequence only triggers one timer.

        Sequence:
        1. Trade 1: -$80 (below threshold) → no cooldown
        2. Trade 2: -$120 → cooldown triggered
        3. Already in cooldown, Trade 3: -$200 → ignored
        4. Verify only one timer running
        """
        account_id = 777

        # Trade 1: Small loss (below threshold)
        event1 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -80.0}
        )
        violation1 = await simple_rule.evaluate(event1, mock_engine)
        assert violation1 is None  # No violation

        # Trade 2: Loss triggers cooldown
        event2 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -120.0}
        )
        violation2 = await simple_rule.evaluate(event2, mock_engine)
        assert violation2 is not None
        await simple_rule.enforce(account_id, violation2, mock_engine)

        # Verify lockout and timer
        assert lockout_manager.is_locked_out(account_id)
        assert timer_manager.has_timer(f"lockout_{account_id}")
        initial_timer_count = timer_manager.get_timer_count()

        # Trade 3: Another loss while in cooldown
        event3 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -200.0}
        )
        violation3 = await simple_rule.evaluate(event3, mock_engine)

        # Should be ignored (already in cooldown)
        assert violation3 is None

        # Verify timer count unchanged
        assert timer_manager.get_timer_count() == initial_timer_count

        # Verify still only one timer for this account
        assert timer_manager.has_timer(f"lockout_{account_id}")

    # ========================================================================
    # Test 8: Event Bus Integration
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_event_flow_from_trade_to_lockout(
        self, simple_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test complete event flow from trade event to lockout.

        Flow:
        1. Publish TRADE_EXECUTED event with profitAndLoss=-150
        2. Rule evaluates event
        3. Violation detected
        4. Enforcement triggered
        5. Lockout set
        6. Timer started
        """
        account_id = 888

        # Given: Trade event
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": account_id,
                "symbol": "ES",
                "profitAndLoss": -150.0,
                "quantity": 1,
                "side": "SELL"
            }
        )

        # When: Rule evaluates
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: Violation detected with correct metadata
        assert violation is not None
        assert violation["rule"] == "CooldownAfterLossRule"
        assert violation["account_id"] == account_id
        assert violation["loss_amount"] == -150.0
        assert violation["cooldown_duration"] == 2
        assert violation["action"] == "flatten"

        # When: Enforcement executed
        await simple_rule.enforce(account_id, violation, mock_engine)

        # Then: Complete flow executed
        # 1. Lockout is active
        assert lockout_manager.is_locked_out(account_id)

        # 2. Timer is running
        assert timer_manager.has_timer(f"lockout_{account_id}")

        # 3. Lockout info is correct
        info = lockout_manager.get_lockout_info(account_id)
        assert info is not None
        assert info["remaining_seconds"] > 0

        # 4. Timer auto-unlocks after duration
        await asyncio.sleep(2.5)
        assert not lockout_manager.is_locked_out(account_id)

    # ========================================================================
    # Test 9: Timer Precision
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_timer_precision_within_tolerance(
        self, simple_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test that timer expiry is within acceptable tolerance.

        Expected duration: 2 seconds
        Tolerance: ±0.5 seconds
        """
        account_id = 999

        # Given: Cooldown triggered
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -150.0}
        )
        violation = await simple_rule.evaluate(event, mock_engine)
        await simple_rule.enforce(account_id, violation, mock_engine)

        # Record start time
        import time
        start_time = time.time()

        # Wait for lockout to clear
        while lockout_manager.is_locked_out(account_id):
            await asyncio.sleep(0.1)

        # Record end time
        end_time = time.time()
        actual_duration = end_time - start_time

        # Verify duration within tolerance
        expected_duration = 2.0
        tolerance = 0.5
        assert expected_duration - tolerance <= actual_duration <= expected_duration + tolerance

    # ========================================================================
    # Test 10: Database Cleanup on Lockout Clear
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_database_cleanup_on_lockout_clear(
        self, simple_rule, lockout_manager, db, mock_engine
    ):
        """
        Test that database is updated when lockout clears.

        Verifies:
        1. Lockout active in DB
        2. After expiry, lockout inactive in DB
        """
        account_id = 1010

        # Given: Cooldown triggered
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -150.0}
        )
        violation = await simple_rule.evaluate(event, mock_engine)
        await simple_rule.enforce(account_id, violation, mock_engine)

        # Then: Lockout active in database
        rows = db.execute(
            "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
            (str(account_id),)
        )
        assert len(rows) == 1

        # When: Timer expires
        await asyncio.sleep(2.5)

        # Then: Lockout inactive in database
        rows_active = db.execute(
            "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
            (str(account_id),)
        )
        assert len(rows_active) == 0

        # And: Lockout exists but is inactive
        rows_all = db.execute(
            "SELECT * FROM lockouts WHERE account_id = ?",
            (str(account_id),)
        )
        assert len(rows_all) == 1
        assert rows_all[0]["active"] == 0

    # ========================================================================
    # Test 11: Position Closed Events
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_position_closed_event_triggers_cooldown(
        self, simple_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test that POSITION_CLOSED events also trigger cooldown.

        Rule should respond to both TRADE_EXECUTED and POSITION_CLOSED.
        """
        account_id = 1111

        # Given: Position closed with loss
        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": account_id,
                "symbol": "NQ",
                "profitAndLoss": -175.0
            }
        )

        # When: Rule evaluates
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["loss_amount"] == -175.0

        # When: Enforcement triggered
        await simple_rule.enforce(account_id, violation, mock_engine)

        # Then: Lockout and timer active
        assert lockout_manager.is_locked_out(account_id)
        assert timer_manager.has_timer(f"lockout_{account_id}")

    # ========================================================================
    # Test 12: Half-Turn Trades Ignored
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_half_turn_trades_no_cooldown_no_timer(
        self, simple_rule, lockout_manager, timer_manager, mock_engine
    ):
        """
        Test that half-turn trades (profitAndLoss=None) are ignored.

        Opening positions have no realized P&L yet.
        """
        account_id = 1212

        # Given: Half-turn trade (opening position)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": account_id,
                "symbol": "MNQ",
                "profitAndLoss": None  # No realized P&L yet
            }
        )

        # When: Rule evaluates
        violation = await simple_rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

        # And: No timer or lockout
        assert not timer_manager.has_timer(f"cooldown_{account_id}")
        assert not lockout_manager.is_locked_out(account_id)
