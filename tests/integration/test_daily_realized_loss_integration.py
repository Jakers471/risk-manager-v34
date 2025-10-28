"""
Integration Tests for RULE-003: Daily Realized Loss

Tests the Daily Realized Loss rule with REAL components:
- Real Database (SQLite)
- Real PnLTracker
- Real LockoutManager
- Real ResetScheduler
- Real async event flow

Rule: RULE-003 - Daily Realized Loss Limit
Category: Hard Lockout (Category 3)
Priority: Critical

Integration Test Scope:
- Test full system integration with actual database persistence
- Test timer callbacks and async operations
- Test reset scheduler integration
- Test multi-account independence
- Test crash recovery (restart system, verify lockouts persist)
- Test concurrent access patterns
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.engine import RiskEngine
from risk_manager.rules.daily_realized_loss import DailyRealizedLossRule
from risk_manager.state.database import Database
from risk_manager.state.pnl_tracker import PnLTracker
from risk_manager.state.lockout_manager import LockoutManager
from risk_manager.state.reset_scheduler import ResetScheduler
from unittest.mock import Mock, AsyncMock


class TestDailyRealizedLossIntegration:
    """Integration tests for DailyRealizedLossRule (RULE-003)."""

    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Create temporary database path."""
        return tmp_path / "test_daily_loss_integration.db"

    @pytest.fixture
    async def database(self, temp_db_path):
        """Create real database instance."""
        db = Database(temp_db_path)
        yield db
        # Cleanup
        db.close()
        if temp_db_path.exists():
            temp_db_path.unlink()

    @pytest.fixture
    async def pnl_tracker(self, database):
        """Create real P&L tracker."""
        return PnLTracker(db=database)

    @pytest.fixture
    async def lockout_manager(self, database):
        """Create real lockout manager."""
        manager = LockoutManager(database=database)
        await manager.start()
        yield manager
        await manager.shutdown()

    @pytest.fixture
    async def reset_scheduler(self, database, pnl_tracker, lockout_manager):
        """Create real reset scheduler."""
        scheduler = ResetScheduler(
            database=database,
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_manager
        )
        await scheduler.start()
        yield scheduler
        await scheduler.stop()

    @pytest.fixture
    def event_bus(self):
        """Create event bus."""
        return EventBus()

    @pytest.fixture
    def mock_engine(self):
        """Create mock engine for rule evaluation."""
        engine = Mock()
        engine.current_positions = {}
        return engine

    @pytest.fixture
    async def rule(self, pnl_tracker, lockout_manager, reset_scheduler):
        """Create rule with real components."""
        return DailyRealizedLossRule(
            limit=-1000.0,  # Maximum daily loss limit
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_manager
        )

    # ========================================================================
    # Test 1: Full Loss Limit Flow with Database
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_loss_limit_flow_with_database(
        self, rule, pnl_tracker, lockout_manager, database, mock_engine
    ):
        """
        GIVEN: Real database and components
        WHEN: Multiple trades reach loss limit
        THEN: Lockout set, P&L persisted, can be retrieved

        Scenario:
        - Trade 1: -$300 → no violation
        - Trade 2: -$400 → no violation
        - Trade 3: -$400 → violation (total -$1100 <= -$1000)
        """
        account_id = 123

        # Trade 1: -$300
        event1 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -300.0}
        )
        violation1 = await rule.evaluate(event1, mock_engine)
        assert violation1 is None

        # Verify P&L tracked
        pnl = pnl_tracker.get_daily_pnl(account_id)
        assert pnl == -300.0

        # Trade 2: -$400
        event2 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -400.0}
        )
        violation2 = await rule.evaluate(event2, mock_engine)
        assert violation2 is None

        # Verify cumulative P&L
        pnl = pnl_tracker.get_daily_pnl(account_id)
        assert pnl == -700.0

        # Trade 3: -$400 → Triggers violation
        event3 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -400.0}
        )
        violation3 = await rule.evaluate(event3, mock_engine)
        assert violation3 is not None
        assert violation3["daily_loss"] == -1100.0
        assert violation3["limit"] == -1000.0

        # When: Enforcement executes
        await rule.enforce(account_id, violation3, mock_engine)

        # Then: Lockout is set
        assert lockout_manager.is_locked_out(account_id)

        # And: Lockout persisted in database
        rows = database.execute(
            "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
            (str(account_id),)
        )
        assert len(rows) == 1

    # ========================================================================
    # Test 2: Multi-Account Independence
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_account_independence(
        self, rule, pnl_tracker, lockout_manager, mock_engine
    ):
        """
        GIVEN: Two accounts trading
        WHEN: Account A hits loss limit
        THEN: Account B continues trading independently
        """
        account_a = 111
        account_b = 222

        # Account A: Hit loss limit
        event_a = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_a, "profitAndLoss": -1200.0}
        )
        violation_a = await rule.evaluate(event_a, mock_engine)
        assert violation_a is not None
        await rule.enforce(account_a, violation_a, mock_engine)

        # Account B: Small loss
        event_b = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_b, "profitAndLoss": -200.0}
        )
        violation_b = await rule.evaluate(event_b, mock_engine)
        assert violation_b is None

        # Verify independence
        assert lockout_manager.is_locked_out(account_a)
        assert not lockout_manager.is_locked_out(account_b)

        # Verify separate P&L tracking
        assert pnl_tracker.get_daily_pnl(account_a) == -1200.0
        assert pnl_tracker.get_daily_pnl(account_b) == -200.0

    # ========================================================================
    # Test 3: Lockout Persistence - Crash Recovery
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_lockout_persistence_crash_recovery(
        self, temp_db_path, pnl_tracker, mock_engine
    ):
        """
        GIVEN: Rule hits loss limit and sets lockout
        WHEN: System restarts (create new instances)
        THEN: Lockout persists and is loaded from database
        """
        account_id = 333

        # Phase 1: Initial system
        db1 = Database(temp_db_path)
        tracker1 = PnLTracker(db=db1)
        lockout1 = LockoutManager(database=db1)
        await lockout1.start()

        reset1 = ResetScheduler(
            database=db1,
            pnl_tracker=tracker1,
            lockout_manager=lockout1
        )
        await reset1.start()

        rule1 = DailyRealizedLossRule(
            limit=-1000.0,
            pnl_tracker=tracker1,
            lockout_manager=lockout1
        )

        # Trigger lockout
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -1200.0}
        )
        violation = await rule1.evaluate(event, mock_engine)
        await rule1.enforce(account_id, violation, mock_engine)

        # Verify lockout
        assert lockout1.is_locked_out(account_id)

        # Shutdown
        await reset1.stop()
        await lockout1.shutdown()
        db1.close()

        # Phase 2: Restart (new instances)
        db2 = Database(temp_db_path)
        tracker2 = PnLTracker(db=db2)
        lockout2 = LockoutManager(database=db2)
        await lockout2.start()

        # Verify lockout loaded from database
        assert lockout2.is_locked_out(account_id)

        # Verify P&L persisted
        assert tracker2.get_daily_pnl(account_id) == -1200.0

        # Cleanup
        await lockout2.shutdown()
        db2.close()

    # ========================================================================
    # Test 4: Reset Scheduler Integration
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_reset_scheduler_integration(
        self, rule, pnl_tracker, lockout_manager, reset_scheduler, mock_engine
    ):
        """
        GIVEN: Loss limit hit with lockout
        WHEN: Reset scheduler triggers daily reset
        THEN: Lockout cleared, P&L reset to $0

        Note: We manually trigger reset (not waiting for actual time)
        """
        account_id = 444

        # Hit loss limit
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -1200.0}
        )
        violation = await rule.evaluate(event, mock_engine)
        await rule.enforce(account_id, violation, mock_engine)

        # Verify locked
        assert lockout_manager.is_locked_out(account_id)
        assert pnl_tracker.get_daily_pnl(account_id) == -1200.0

        # Manually trigger reset
        reset_scheduler.trigger_reset_manually(str(account_id), reset_type="daily")

        # Verify reset
        assert not lockout_manager.is_locked_out(account_id)
        assert pnl_tracker.get_daily_pnl(account_id) == 0.0

    # ========================================================================
    # Test 5: Half-Turn Trades Ignored
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_half_turn_trades_ignored(self, rule, pnl_tracker, mock_engine):
        """
        GIVEN: Opening position (half-turn with pnl=None)
        WHEN: Event processed
        THEN: P&L unchanged, no violation
        """
        account_id = 555

        # Half-turn trade (opening position)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": account_id,
                "profitAndLoss": None  # No realized P&L yet
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        # Then: Ignored
        assert violation is None
        assert pnl_tracker.get_daily_pnl(account_id) == 0.0

    # ========================================================================
    # Test 6: Mixed Profit/Loss Day
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mixed_profit_loss_day(self, rule, pnl_tracker, mock_engine):
        """
        GIVEN: Trading day with mixed wins/losses
        WHEN: Net loss reaches limit
        THEN: Violation triggered on cumulative loss

        Scenario: -$600, +$200, -$800 = -$1200 net
        """
        account_id = 666

        # Trade 1: Loss
        event1 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -600.0}
        )
        await rule.evaluate(event1, mock_engine)

        # Trade 2: Win
        event2 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": 200.0}
        )
        await rule.evaluate(event2, mock_engine)

        # Verify net so far
        assert pnl_tracker.get_daily_pnl(account_id) == -400.0

        # Trade 3: Loss triggers violation
        event3 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -800.0}
        )
        violation = await rule.evaluate(event3, mock_engine)

        # Verify violation
        assert violation is not None
        assert violation["daily_loss"] == -1200.0

    # ========================================================================
    # Test 7: Concurrent Access Thread Safety
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_access_thread_safety(
        self, rule, pnl_tracker, mock_engine
    ):
        """
        GIVEN: Multiple events processed concurrently
        WHEN: Events arrive simultaneously
        THEN: No race conditions, P&L calculated correctly
        """
        account_id = 777

        # Process multiple trades concurrently
        events = [
            RiskEvent(
                event_type=EventType.TRADE_EXECUTED,
                data={"account_id": account_id, "profitAndLoss": -100.0}
            )
            for _ in range(10)
        ]

        # Evaluate concurrently
        results = await asyncio.gather(*[
            rule.evaluate(event, mock_engine) for event in events
        ])

        # Verify P&L is correct (no race conditions)
        assert pnl_tracker.get_daily_pnl(account_id) == -1000.0

        # Verify exactly at limit triggers violation (using <= comparison)
        violations = [r for r in results if r is not None]
        assert len(violations) == 1  # Exactly at limit triggers violation

    # ========================================================================
    # Test 8: Database Schema Validation
    # ========================================================================

    @pytest.mark.integration
    def test_database_schema_validation(self, database):
        """
        GIVEN: Database initialized
        WHEN: Schema checked
        THEN: All required tables exist with correct columns
        """
        # Verify daily_pnl table
        schema = database.execute("PRAGMA table_info(daily_pnl)")
        columns = [col["name"] for col in schema]
        assert "account_id" in columns
        assert "date" in columns
        assert "realized_pnl" in columns  # Actual column name
        assert "trade_count" in columns

        # Verify lockouts table
        schema = database.execute("PRAGMA table_info(lockouts)")
        columns = [col["name"] for col in schema]
        assert "account_id" in columns
        assert "rule_id" in columns
        assert "reason" in columns
        assert "expires_at" in columns
        assert "active" in columns

    # ========================================================================
    # Test 9: Boundary - Exactly at Limit
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_boundary_exactly_at_limit(self, rule, mock_engine):
        """
        GIVEN: Loss exactly at limit (-$1000.00)
        WHEN: Rule evaluates
        THEN: Violation triggered (<= comparison)
        """
        account_id = 888

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -1000.0}
        )

        violation = await rule.evaluate(event, mock_engine)

        # Violation at exact limit (<= used)
        assert violation is not None
        assert violation["daily_loss"] == -1000.0

    # ========================================================================
    # Test 10: Timer Auto-Unlock
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_timer_auto_unlock(
        self, rule, lockout_manager, mock_engine
    ):
        """
        GIVEN: Lockout set with expiry time
        WHEN: Time expires (simulated)
        THEN: Lockout auto-cleared
        """
        account_id = 999

        # Trigger lockout
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "profitAndLoss": -1200.0}
        )
        violation = await rule.evaluate(event, mock_engine)
        await rule.enforce(account_id, violation, mock_engine)

        # Verify locked
        assert lockout_manager.is_locked_out(account_id)

        # Set short expiry (2 seconds)
        lockout_manager.set_lockout(
            account_id=account_id,
            reason="Test auto-unlock",
            until=datetime.now(timezone.utc) + timedelta(seconds=2)
        )

        # Wait for expiry
        await asyncio.sleep(3)

        # Verify auto-unlocked
        assert not lockout_manager.is_locked_out(account_id)
