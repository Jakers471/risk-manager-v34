"""
Test state persistence across database restarts.

Validates cooldowns, lockouts, and P&L survive DB connection close/reopen.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone
from risk_manager.state.database import Database
from risk_manager.state.lockout_manager import LockoutManager
from risk_manager.state.timer_manager import TimerManager
from risk_manager.state.pnl_tracker import PnLTracker


@pytest.mark.integration
class TestStatePersistence:
    """Test state persistence across restarts."""

    @pytest.mark.asyncio
    async def test_cooldown_persists_across_restart(self, tmp_path):
        """Cooldown survives DB close/reopen."""
        db_path = tmp_path / "test_state.db"
        account_id = 123

        # Phase 1: Set cooldown
        db1 = Database(db_path=str(db_path))
        timer_mgr1 = TimerManager()
        await timer_mgr1.start()

        lockout_mgr1 = LockoutManager(database=db1, timer_manager=timer_mgr1)

        # Set 300s cooldown
        await lockout_mgr1.set_cooldown(
            account_id=account_id,
            duration_seconds=300,
            reason="Test cooldown persistence"
        )

        # Verify active
        is_locked_1 = lockout_mgr1.is_locked_out(account_id)
        assert is_locked_1 is True, "Cooldown should be active in phase 1"

        # Get details
        details_1 = lockout_mgr1.get_lockout_info(account_id)
        assert details_1 is not None
        assert details_1["remaining_seconds"] > 0

        print(f"Phase 1: Cooldown set, {details_1['remaining_seconds']}s remaining")

        # Close connections
        await timer_mgr1.stop()
        db1.close()

        # Phase 2: Restart and verify
        db2 = Database(db_path=str(db_path))
        timer_mgr2 = TimerManager()
        await timer_mgr2.start()

        # LockoutManager should auto-load from DB
        lockout_mgr2 = LockoutManager(database=db2, timer_manager=timer_mgr2)

        # Verify cooldown still active
        is_locked_2 = lockout_mgr2.is_locked_out(account_id)
        assert is_locked_2 is True, "Cooldown should persist after restart"

        # Get details
        details_2 = lockout_mgr2.get_lockout_info(account_id)
        assert details_2 is not None
        assert details_2["remaining_seconds"] > 0, "Duration should still be positive"

        print(f"Phase 2: Cooldown restored, {details_2['remaining_seconds']}s remaining")

        # Cleanup
        await timer_mgr2.stop()
        db2.close()

    @pytest.mark.asyncio
    async def test_hard_lockout_persists_with_until_time(self, tmp_path):
        """Hard lockout with until datetime survives restart."""
        db_path = tmp_path / "test_lockout.db"
        account_id = 456

        # Phase 1: Set hard lockout
        db1 = Database(db_path=str(db_path))
        timer_mgr1 = TimerManager()
        await timer_mgr1.start()

        lockout_mgr1 = LockoutManager(database=db1, timer_manager=timer_mgr1)

        # Set lockout until 2 hours from now
        until_time = datetime.now(timezone.utc) + timedelta(hours=2)
        lockout_mgr1.set_lockout(
            account_id=account_id,
            reason="Daily loss limit exceeded",
            until=until_time
        )

        # Verify active
        is_locked_1 = lockout_mgr1.is_locked_out(account_id)
        assert is_locked_1 is True

        # Close
        await timer_mgr1.stop()
        db1.close()

        # Phase 2: Restart
        db2 = Database(db_path=str(db_path))
        timer_mgr2 = TimerManager()
        await timer_mgr2.start()

        lockout_mgr2 = LockoutManager(database=db2, timer_manager=timer_mgr2)

        # Verify lockout persists
        is_locked_2 = lockout_mgr2.is_locked_out(account_id)
        assert is_locked_2 is True, "Hard lockout should persist"

        # Verify details match
        details = lockout_mgr2.get_lockout_info(account_id)
        assert details is not None
        assert details["reason"] == "Daily loss limit exceeded"
        # Should still have ~2 hours remaining (with some tolerance)
        assert details["remaining_seconds"] > 7000, "Should have ~2 hours remaining"

        # Cleanup
        await timer_mgr2.stop()
        db2.close()

    @pytest.mark.asyncio
    async def test_pnl_persists_across_restart(self, tmp_path):
        """Daily P&L survives restart."""
        db_path = tmp_path / "test_pnl.db"
        account_id = "TEST-003"

        # Phase 1: Add P&L
        db1 = Database(db_path=str(db_path))
        pnl_tracker1 = PnLTracker(db=db1)

        # Add trades
        pnl_tracker1.add_trade_pnl(account_id, -200.00)
        pnl_tracker1.add_trade_pnl(account_id, -150.00)

        # Verify total
        daily_pnl_1 = pnl_tracker1.get_daily_pnl(account_id)
        assert daily_pnl_1 == -350.00, f"Expected -$350, got ${daily_pnl_1}"

        # Close
        db1.close()

        # Phase 2: Restart
        db2 = Database(db_path=str(db_path))
        pnl_tracker2 = PnLTracker(db=db2)

        # Verify P&L persists
        daily_pnl_2 = pnl_tracker2.get_daily_pnl(account_id)
        assert daily_pnl_2 == -350.00, f"P&L should persist, expected -$350, got ${daily_pnl_2}"

        # Cleanup
        db2.close()

    @pytest.mark.asyncio
    async def test_expired_lockout_not_restored(self, tmp_path):
        """Lockouts expired before restart are not restored."""
        db_path = tmp_path / "test_expired.db"
        account_id = 789

        # Phase 1: Set short cooldown (1 second)
        db1 = Database(db_path=str(db_path))
        timer_mgr1 = TimerManager()
        await timer_mgr1.start()

        lockout_mgr1 = LockoutManager(database=db1, timer_manager=timer_mgr1)

        await lockout_mgr1.set_cooldown(
            account_id=account_id,
            duration_seconds=1,  # 1 second
            reason="Short cooldown"
        )

        # Wait for expiry
        await asyncio.sleep(2)

        # Verify expired
        is_locked_1 = lockout_mgr1.is_locked_out(account_id)
        assert is_locked_1 is False, "Cooldown should have expired"

        # Close
        await timer_mgr1.stop()
        db1.close()

        # Phase 2: Restart
        db2 = Database(db_path=str(db_path))
        timer_mgr2 = TimerManager()
        await timer_mgr2.start()

        lockout_mgr2 = LockoutManager(database=db2, timer_manager=timer_mgr2)

        # Verify NOT restored (because it expired)
        is_locked_2 = lockout_mgr2.is_locked_out(account_id)
        assert is_locked_2 is False, "Expired lockout should NOT be restored"

        # Cleanup
        await timer_mgr2.stop()
        db2.close()

    @pytest.mark.asyncio
    async def test_multiple_accounts_persist_independently(self, tmp_path):
        """Multiple accounts with different states persist correctly."""
        db_path = tmp_path / "test_multi.db"

        # Phase 1: Setup multiple accounts
        db1 = Database(db_path=str(db_path))
        timer_mgr1 = TimerManager()
        await timer_mgr1.start()

        lockout_mgr1 = LockoutManager(database=db1, timer_manager=timer_mgr1)
        pnl_tracker1 = PnLTracker(db=db1)

        # Account 1: Cooldown
        await lockout_mgr1.set_cooldown(101, duration_seconds=300, reason="Reason 1")

        # Account 2: Hard lockout
        until_time = datetime.now(timezone.utc) + timedelta(hours=1)
        lockout_mgr1.set_lockout(102, "Reason 2", until_time)

        # Account 3: P&L only (no lockout)
        pnl_tracker1.add_trade_pnl("ACC-103", -100.00)

        # Close
        await timer_mgr1.stop()
        db1.close()

        # Phase 2: Restart and verify
        db2 = Database(db_path=str(db_path))
        timer_mgr2 = TimerManager()
        await timer_mgr2.start()

        lockout_mgr2 = LockoutManager(database=db2, timer_manager=timer_mgr2)
        pnl_tracker2 = PnLTracker(db=db2)

        # Verify each account
        assert lockout_mgr2.is_locked_out(101) is True, "Account 1 should be locked"
        assert lockout_mgr2.is_locked_out(102) is True, "Account 2 should be locked"
        assert lockout_mgr2.is_locked_out(103) is False, "Account 3 should NOT be locked"

        assert pnl_tracker2.get_daily_pnl("ACC-103") == -100.00, "Account 3 P&L should persist"

        # Cleanup
        await timer_mgr2.stop()
        db2.close()

    @pytest.mark.asyncio
    async def test_pnl_with_trade_count_persists(self, tmp_path):
        """P&L and trade count both persist correctly."""
        db_path = tmp_path / "test_pnl_count.db"
        account_id = "TEST-006"

        # Phase 1: Add multiple trades
        db1 = Database(db_path=str(db_path))
        pnl_tracker1 = PnLTracker(db=db1)

        # Add 5 trades
        pnl_tracker1.add_trade_pnl(account_id, -50.00)  # Trade 1
        pnl_tracker1.add_trade_pnl(account_id, -75.00)  # Trade 2
        pnl_tracker1.add_trade_pnl(account_id, 100.00)  # Trade 3
        pnl_tracker1.add_trade_pnl(account_id, -25.00)  # Trade 4
        pnl_tracker1.add_trade_pnl(account_id, -50.00)  # Trade 5

        # Verify totals
        stats1 = pnl_tracker1.get_stats(account_id)
        assert stats1["realized_pnl"] == -100.00, "Expected -$100 total P&L"
        assert stats1["trade_count"] == 5, "Expected 5 trades"

        # Close
        db1.close()

        # Phase 2: Restart
        db2 = Database(db_path=str(db_path))
        pnl_tracker2 = PnLTracker(db=db2)

        # Verify both persist
        stats2 = pnl_tracker2.get_stats(account_id)
        assert stats2["realized_pnl"] == -100.00, "P&L should persist"
        assert stats2["trade_count"] == 5, "Trade count should persist"

        # Cleanup
        db2.close()

    @pytest.mark.asyncio
    async def test_lockout_details_persist_accurately(self, tmp_path):
        """Lockout reason and type persist correctly."""
        db_path = tmp_path / "test_details.db"
        account_id = 999

        # Phase 1: Create lockout with specific details
        db1 = Database(db_path=str(db_path))
        timer_mgr1 = TimerManager()
        await timer_mgr1.start()

        lockout_mgr1 = LockoutManager(database=db1, timer_manager=timer_mgr1)

        reason = "Test: Trade frequency limit exceeded"
        await lockout_mgr1.set_cooldown(
            account_id=account_id,
            duration_seconds=600,
            reason=reason
        )

        # Get details
        details1 = lockout_mgr1.get_lockout_info(account_id)
        assert details1 is not None
        assert details1["reason"] == reason

        # Close
        await timer_mgr1.stop()
        db1.close()

        # Phase 2: Restart and verify details match
        db2 = Database(db_path=str(db_path))
        timer_mgr2 = TimerManager()
        await timer_mgr2.start()

        lockout_mgr2 = LockoutManager(database=db2, timer_manager=timer_mgr2)

        details2 = lockout_mgr2.get_lockout_info(account_id)
        assert details2 is not None
        assert details2["reason"] == reason, "Reason should persist exactly"
        # Should still be a hard_lockout type (cooldowns become hard lockouts after restart)
        assert details2["type"] == "hard_lockout", "Type should be restored"

        # Cleanup
        await timer_mgr2.stop()
        db2.close()

    @pytest.mark.asyncio
    async def test_simultaneous_multiple_db_connections(self, tmp_path):
        """Multiple DB connections can read/write simultaneously."""
        db_path = tmp_path / "test_concurrent.db"

        # Create two independent database connections
        db1 = Database(db_path=str(db_path))
        db2 = Database(db_path=str(db_path))

        # Write from db1
        pnl_tracker1 = PnLTracker(db=db1)
        pnl_tracker1.add_trade_pnl("ACC-001", -50.00)

        # Read from db2 (should see the change)
        pnl_tracker2 = PnLTracker(db=db2)
        pnl = pnl_tracker2.get_daily_pnl("ACC-001")
        assert pnl == -50.00, "Changes should be visible across connections"

        # Write from db2
        pnl_tracker2.add_trade_pnl("ACC-001", -25.00)

        # Read from db1 (should see the update)
        pnl = pnl_tracker1.get_daily_pnl("ACC-001")
        assert pnl == -75.00, "Updates should be visible across connections"

        # Cleanup
        db1.close()
        db2.close()
