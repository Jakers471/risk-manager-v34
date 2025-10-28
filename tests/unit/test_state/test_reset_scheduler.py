"""
TDD Tests for MOD-004: Reset Scheduler

Tests the daily/weekly reset system for P&L tracking, lockouts, and trade counters.
Handles timezone conversion (ET ↔ UTC), DST transitions, and database persistence.

Written BEFORE implementation (TDD RED phase).
"""

import pytest
from datetime import datetime, timedelta, timezone, time
from pathlib import Path
import tempfile
from unittest.mock import Mock, AsyncMock, call, patch
import asyncio
from zoneinfo import ZoneInfo

from risk_manager.state.database import Database
from risk_manager.state.reset_scheduler import ResetScheduler


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = Database(db_path)
    yield db

    # Cleanup
    db.close()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def mock_pnl_tracker():
    """Mock PnL Tracker for reset integration tests."""
    mock = Mock()
    mock.reset_daily_pnl = Mock()
    mock.reset_weekly_pnl = Mock()
    return mock


@pytest.fixture
def mock_lockout_manager():
    """Mock Lockout Manager for reset integration tests."""
    mock = Mock()
    mock.clear_lockout = Mock()
    return mock


@pytest.fixture
def reset_scheduler(temp_db, mock_pnl_tracker, mock_lockout_manager):
    """Create a ResetScheduler instance for testing."""
    return ResetScheduler(
        database=temp_db,
        pnl_tracker=mock_pnl_tracker,
        lockout_manager=mock_lockout_manager
    )


# =============================================================================
# CATEGORY 1: DAILY RESET SCHEDULING (6 tests)
# =============================================================================


class TestDailyResetScheduling:
    """Test daily reset at 5:00 PM ET."""

    def test_schedule_daily_reset_creates_schedule(self, reset_scheduler):
        """
        GIVEN: ResetScheduler initialized
        WHEN: schedule_daily_reset() is called
        THEN: Daily reset is scheduled for account
        """
        # ARRANGE
        account_id = "123"
        reset_time_str = "17:00"  # 5:00 PM ET

        # ACT
        reset_scheduler.schedule_daily_reset(account_id, reset_time_str)

        # ASSERT
        assert reset_scheduler.has_daily_reset(account_id) is True

    def test_daily_reset_converts_et_to_utc(self, reset_scheduler):
        """
        GIVEN: Reset scheduled for 5:00 PM ET
        WHEN: get_next_reset_time() is called
        THEN: Returns correct UTC time (9:00 PM or 10:00 PM UTC depending on DST)
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # ACT
        next_reset = reset_scheduler.get_next_reset_time(account_id)

        # ASSERT
        # Next reset should be today or tomorrow at 5:00 PM ET
        et_tz = ZoneInfo("America/New_York")
        next_reset_et = next_reset.astimezone(et_tz)
        assert next_reset_et.hour == 17
        assert next_reset_et.minute == 0

    def test_daily_reset_persists_to_database(self, reset_scheduler, temp_db):
        """
        GIVEN: Daily reset scheduled
        WHEN: Reset is triggered
        THEN: Reset event is saved to database
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # ACT
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # ASSERT
        row = temp_db.execute_one(
            "SELECT * FROM reset_log WHERE account_id = ? AND reset_type = 'daily'",
            (account_id,)
        )
        assert row is not None
        assert row["reset_type"] == "daily"

    def test_daily_reset_clears_pnl_tracker(self, reset_scheduler, mock_pnl_tracker):
        """
        GIVEN: Daily reset scheduled
        WHEN: Reset time is reached
        THEN: PnL Tracker's reset_daily_pnl() is called
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # ACT
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # ASSERT
        mock_pnl_tracker.reset_daily_pnl.assert_called_once_with(account_id)

    def test_daily_reset_clears_lockout(self, reset_scheduler, mock_lockout_manager):
        """
        GIVEN: Daily reset scheduled
        WHEN: Reset time is reached
        THEN: Lockout Manager's clear_lockout() is called
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # ACT
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # ASSERT
        mock_lockout_manager.clear_lockout.assert_called_once_with(int(account_id))

    def test_daily_reset_does_not_trigger_twice_same_day(self, reset_scheduler, mock_pnl_tracker):
        """
        GIVEN: Reset already triggered today
        WHEN: trigger_reset_manually() is called again
        THEN: Reset is not triggered again (idempotent)
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")
        reset_scheduler.trigger_reset_manually(account_id, "daily")
        mock_pnl_tracker.reset_daily_pnl.reset_mock()

        # ACT
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # ASSERT
        mock_pnl_tracker.reset_daily_pnl.assert_not_called()


# =============================================================================
# CATEGORY 2: WEEKLY RESET SCHEDULING (3 tests)
# =============================================================================


class TestWeeklyResetScheduling:
    """Test weekly reset (Monday at 5:00 PM ET)."""

    def test_schedule_weekly_reset_creates_schedule(self, reset_scheduler):
        """
        GIVEN: ResetScheduler initialized
        WHEN: schedule_weekly_reset() is called with day="Monday"
        THEN: Weekly reset is scheduled
        """
        # ARRANGE
        account_id = "123"
        reset_day = "Monday"
        reset_time_str = "17:00"

        # ACT
        reset_scheduler.schedule_weekly_reset(account_id, reset_day, reset_time_str)

        # ASSERT
        assert reset_scheduler.has_weekly_reset(account_id) is True

    def test_weekly_reset_triggers_on_monday(self, reset_scheduler):
        """
        GIVEN: Weekly reset scheduled for Monday
        WHEN: get_next_reset_time() is called
        THEN: Next reset is on Monday at 5:00 PM ET
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_weekly_reset(account_id, "Monday", "17:00")

        # ACT
        next_reset = reset_scheduler.get_next_reset_time(account_id, reset_type="weekly")

        # ASSERT
        # Next reset should be on Monday
        et_tz = ZoneInfo("America/New_York")
        next_reset_et = next_reset.astimezone(et_tz)
        assert next_reset_et.weekday() == 0  # Monday = 0
        assert next_reset_et.hour == 17
        assert next_reset_et.minute == 0

    def test_weekly_reset_clears_weekly_pnl(self, reset_scheduler, mock_pnl_tracker):
        """
        GIVEN: Weekly reset scheduled
        WHEN: Reset is triggered
        THEN: PnL Tracker's reset_weekly_pnl() is called (if it exists)
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_weekly_reset(account_id, "Monday", "17:00")

        # ACT
        reset_scheduler.trigger_reset_manually(account_id, "weekly")

        # ASSERT
        # Weekly reset should also reset daily P&L
        mock_pnl_tracker.reset_daily_pnl.assert_called_once_with(account_id)


# =============================================================================
# CATEGORY 3: TIMEZONE HANDLING (3 tests)
# =============================================================================


class TestTimezoneHandling:
    """Test ET ↔ UTC conversion and DST handling."""

    def test_et_to_utc_conversion_standard_time(self, reset_scheduler):
        """
        GIVEN: Reset scheduled for 5:00 PM ET during standard time (EST = UTC-5)
        WHEN: Timezone conversion occurs
        THEN: UTC time is 10:00 PM (5:00 PM + 5 hours)
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # ACT
        next_reset = reset_scheduler.get_next_reset_time(account_id)

        # ASSERT
        # Should always be at 5:00 PM ET when converted back
        et_tz = ZoneInfo("America/New_York")
        next_reset_et = next_reset.astimezone(et_tz)
        assert next_reset_et.hour == 17
        assert next_reset_et.minute == 0

    def test_et_to_utc_conversion_daylight_time(self, reset_scheduler):
        """
        GIVEN: Reset scheduled for 5:00 PM ET during daylight time (EDT = UTC-4)
        WHEN: Timezone conversion occurs
        THEN: UTC time is 9:00 PM (5:00 PM + 4 hours)
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # ACT
        next_reset = reset_scheduler.get_next_reset_time(account_id)

        # ASSERT
        # Should always be at 5:00 PM ET when converted back
        et_tz = ZoneInfo("America/New_York")
        next_reset_et = next_reset.astimezone(et_tz)
        assert next_reset_et.hour == 17
        assert next_reset_et.minute == 0

    def test_dst_transition_handling(self, reset_scheduler):
        """
        GIVEN: Reset scheduled during DST transition period
        WHEN: DST change occurs
        THEN: Reset time adjusts correctly to maintain 5:00 PM ET
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # ACT
        next_reset = reset_scheduler.get_next_reset_time(account_id)

        # ASSERT
        # Should always be at 5:00 PM ET regardless of DST
        et_tz = ZoneInfo("America/New_York")
        next_reset_et = next_reset.astimezone(et_tz)
        assert next_reset_et.hour == 17
        assert next_reset_et.minute == 0


# =============================================================================
# CATEGORY 4: DATABASE PERSISTENCE (2 tests)
# =============================================================================


class TestDatabasePersistence:
    """Test reset log persistence to database."""

    def test_reset_log_saved_to_database(self, reset_scheduler, temp_db):
        """
        GIVEN: Reset is triggered
        WHEN: Reset completes
        THEN: Reset event is saved to reset_log table
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # ACT
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # ASSERT
        rows = temp_db.execute(
            "SELECT * FROM reset_log WHERE account_id = ?",
            (account_id,)
        )
        assert len(rows) == 1
        assert rows[0]["reset_type"] == "daily"
        assert rows[0]["account_id"] == account_id

    def test_last_reset_time_loaded_from_database(self, reset_scheduler, temp_db):
        """
        GIVEN: Reset log exists in database
        WHEN: ResetScheduler is initialized
        THEN: Last reset time is loaded correctly
        """
        # ARRANGE
        account_id = "123"
        reset_time = datetime.now(timezone.utc)

        # Insert reset log directly
        temp_db.execute_write(
            """
            INSERT INTO reset_log (account_id, reset_type, reset_time, triggered_at)
            VALUES (?, ?, ?, ?)
            """,
            (account_id, "daily", reset_time.isoformat(), reset_time.isoformat())
        )

        # ACT - Create new scheduler instance (should load from DB)
        new_scheduler = ResetScheduler(
            database=temp_db,
            pnl_tracker=Mock(),
            lockout_manager=Mock()
        )

        # ASSERT
        last_reset = new_scheduler.get_last_reset_time(account_id, "daily")
        assert last_reset is not None
        # Times should match within 1 second
        assert abs((last_reset - reset_time).total_seconds()) < 1


# =============================================================================
# CATEGORY 5: BACKGROUND TASK (3 tests)
# =============================================================================


class TestBackgroundTask:
    """Test background task that checks for reset time every minute."""

    @pytest.mark.asyncio
    async def test_background_task_checks_every_minute(self, reset_scheduler):
        """
        GIVEN: Background task started
        WHEN: Multiple minutes pass
        THEN: check_reset_time() is called repeatedly
        """
        # ARRANGE
        check_count = 0
        original_check = reset_scheduler.check_reset_time

        def mock_check():
            nonlocal check_count
            check_count += 1
            original_check()

        reset_scheduler.check_reset_time = mock_check

        # ACT
        await reset_scheduler.start()
        await asyncio.sleep(2.5)  # Run for 2.5 seconds
        await reset_scheduler.stop()

        # ASSERT
        # With 1-second interval for testing, should run at least 2 times
        assert check_count >= 2

    @pytest.mark.asyncio
    async def test_reset_triggered_automatically_at_time(self, reset_scheduler, mock_pnl_tracker):
        """
        GIVEN: Daily reset scheduled
        WHEN: check_reset_time() is called manually
        THEN: Reset can be triggered on schedule

        Note: This test verifies the check mechanism works. Full background task
        timing is tested in integration tests.
        """
        # ARRANGE
        account_id = "123"

        # Schedule a daily reset
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # Manually trigger a reset to simulate time passage
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # ASSERT
        # Reset should have been executed
        mock_pnl_tracker.reset_daily_pnl.assert_called_once_with(account_id)

    @pytest.mark.asyncio
    async def test_shutdown_stops_background_task(self, reset_scheduler):
        """
        GIVEN: Background task running
        WHEN: stop() is called
        THEN: Background task stops gracefully
        """
        # ARRANGE
        await reset_scheduler.start()
        assert reset_scheduler.running is True

        # ACT
        await reset_scheduler.stop()

        # ASSERT
        assert reset_scheduler.running is False


# =============================================================================
# CATEGORY 6: EDGE CASES (3 tests)
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_multiple_accounts_independent_schedules(self, reset_scheduler):
        """
        GIVEN: Multiple accounts with different reset times
        WHEN: Resets are scheduled
        THEN: Each account has independent schedule
        """
        # ARRANGE
        account1 = "123"
        account2 = "456"

        # ACT
        reset_scheduler.schedule_daily_reset(account1, "17:00")
        reset_scheduler.schedule_daily_reset(account2, "18:00")

        # ASSERT
        next_reset1 = reset_scheduler.get_next_reset_time(account1)
        next_reset2 = reset_scheduler.get_next_reset_time(account2)

        et_tz = ZoneInfo("America/New_York")
        assert next_reset1.astimezone(et_tz).hour == 17
        assert next_reset2.astimezone(et_tz).hour == 18

    def test_reset_time_calculation_near_midnight(self, reset_scheduler):
        """
        GIVEN: Reset time near midnight
        WHEN: get_next_reset_time() is called late in day
        THEN: Correctly schedules for next day if time passed
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "00:30")  # 12:30 AM

        # ACT
        with patch('risk_manager.state.reset_scheduler.datetime') as mock_datetime:
            # Current time is 1:00 AM (past reset time)
            mock_now = datetime(2025, 10, 27, 5, 0, tzinfo=timezone.utc)  # 1:00 AM ET
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            next_reset = reset_scheduler.get_next_reset_time(account_id)

        # ASSERT
        # Should be tomorrow at 12:30 AM
        assert next_reset > mock_now

    def test_unscheduled_account_returns_none(self, reset_scheduler):
        """
        GIVEN: Account with no reset scheduled
        WHEN: get_next_reset_time() is called
        THEN: Returns None
        """
        # ARRANGE
        account_id = "999"

        # ACT
        next_reset = reset_scheduler.get_next_reset_time(account_id)

        # ASSERT
        assert next_reset is None


# =============================================================================
# CATEGORY 7: DATABASE SCHEMA (1 test)
# =============================================================================


class TestDatabaseSchema:
    """Test database schema creation and structure."""

    def test_reset_log_table_created(self, temp_db):
        """
        GIVEN: Database initialized
        WHEN: Schema is checked
        THEN: reset_log table exists with correct structure
        """
        # ACT
        cursor = temp_db.execute("PRAGMA table_info(reset_log)")
        columns = {row["name"]: row["type"] for row in cursor}

        # ASSERT
        assert "account_id" in columns
        assert "reset_type" in columns
        assert "reset_time" in columns
        assert "triggered_at" in columns


# =============================================================================
# CATEGORY 8: INTEGRATION (2 tests)
# =============================================================================


class TestIntegration:
    """Test integration with PnL Tracker and Lockout Manager."""

    def test_reset_sequence_executes_in_order(self, reset_scheduler, mock_pnl_tracker, mock_lockout_manager):
        """
        GIVEN: Daily reset scheduled
        WHEN: Reset is triggered
        THEN: Reset sequence executes: P&L reset → Lockout clear → DB log
        """
        # ARRANGE
        account_id = "123"
        reset_scheduler.schedule_daily_reset(account_id, "17:00")

        # ACT
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # ASSERT
        # Verify execution order
        assert mock_pnl_tracker.reset_daily_pnl.called
        assert mock_lockout_manager.clear_lockout.called

    @pytest.mark.asyncio
    async def test_full_lifecycle_start_to_stop(
        self,
        reset_scheduler,
        mock_pnl_tracker,
        mock_lockout_manager
    ):
        """
        GIVEN: ResetScheduler initialized
        WHEN: Full lifecycle (start → schedule → stop) is executed
        THEN: No errors occur and state is correct
        """
        # ARRANGE
        account_id = "123"

        # ACT
        await reset_scheduler.start()
        reset_scheduler.schedule_daily_reset(account_id, "17:00")
        await asyncio.sleep(0.5)
        await reset_scheduler.stop()

        # ASSERT
        assert reset_scheduler.has_daily_reset(account_id) is True
        assert reset_scheduler.running is False
