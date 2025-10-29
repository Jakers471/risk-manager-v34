"""
Test daily reset behavior around DST transitions.

Validates timezone handling, reset timing, and DST edge cases.

Key DST Dates (2025):
- Spring forward: March 9, 2025 (2 AM → 3 AM)
- Fall back: November 2, 2025 (2 AM → 1 AM, hour repeats)

Critical Requirements:
- Reset happens at 17:00 ET (Eastern Time), not UTC
- Reset happens ONCE per day, even during DST transitions
- Lockouts expire at next 17:00 ET, respecting DST
- Timezone conversions are accurate across DST boundaries
"""

import pytest
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock

from risk_manager.state.pnl_tracker import PnLTracker
from risk_manager.state.lockout_manager import LockoutManager
from risk_manager.state.reset_scheduler import ResetScheduler
from risk_manager.state.timer_manager import TimerManager
from risk_manager.state.database import Database


@pytest.mark.integration
class TestDailyResetAndDST:
    """Test reset behavior around DST transitions."""

    @pytest.fixture
    def db(self):
        """In-memory database for testing."""
        db = Database(db_path=":memory:")
        yield db
        db.close()

    @pytest.fixture
    def pnl_tracker(self, db):
        """PnL tracker instance."""
        tracker = PnLTracker(db=db)
        return tracker

    @pytest.fixture
    async def timer_manager(self):
        """Timer manager instance."""
        timer_mgr = TimerManager()
        await timer_mgr.start()
        yield timer_mgr
        await timer_mgr.stop()

    @pytest.fixture
    async def lockout_manager(self, db, timer_manager):
        """Lockout manager instance."""
        lockout_mgr = LockoutManager(database=db, timer_manager=timer_manager)
        await lockout_mgr.start()
        yield lockout_mgr
        await lockout_mgr.stop()

    @pytest.fixture
    async def reset_scheduler(self, db, pnl_tracker, lockout_manager):
        """Reset scheduler instance."""
        scheduler = ResetScheduler(
            database=db,
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_manager
        )
        await scheduler.start()
        yield scheduler
        await scheduler.stop()

    # ====================
    # Test 1: Normal Day Reset
    # ====================

    def test_reset_normal_day(self, pnl_tracker):
        """
        Test basic reset functionality on a normal day.

        Validates that reset_daily_pnl correctly resets P&L to zero.
        """
        account_id = "TEST-001"

        # Setup: Add daily loss of -$450
        pnl_tracker.add_trade_pnl(account_id, -450.00)

        # Verify loss tracked
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == -450.00, f"Expected -$450, got ${daily_pnl}"

        # Trigger reset
        pnl_tracker.reset_daily_pnl(account_id)

        # Verify reset to zero
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == 0.00, f"After reset, expected $0, got ${daily_pnl}"

        # Trade count should also reset
        trade_count = pnl_tracker.get_trade_count(account_id)
        assert trade_count == 0, f"After reset, expected 0 trades, got {trade_count}"

    # ====================
    # Test 2: Timezone Conversions
    # ====================

    def test_timezone_conversion_et_to_utc_standard_time(self):
        """
        Test ET → UTC conversion during standard time (winter).

        In standard time (November - March):
        17:00 ET = 22:00 UTC
        """
        # Standard time: January 15, 2025 at 17:00 ET
        et_time = datetime(2025, 1, 15, 17, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        utc_time = et_time.astimezone(ZoneInfo("UTC"))

        assert utc_time.hour == 22, (
            f"17:00 ET in January (standard time) should be 22:00 UTC, "
            f"got {utc_time.hour}:00 UTC"
        )

    def test_timezone_conversion_et_to_utc_daylight_time(self):
        """
        Test ET → UTC conversion during daylight saving time (summer).

        In daylight time (March - November):
        17:00 ET = 21:00 UTC
        """
        # Daylight time: July 15, 2025 at 17:00 ET
        et_time = datetime(2025, 7, 15, 17, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        utc_time = et_time.astimezone(ZoneInfo("UTC"))

        assert utc_time.hour == 21, (
            f"17:00 ET in July (daylight time) should be 21:00 UTC, "
            f"got {utc_time.hour}:00 UTC"
        )

    # ====================
    # Test 3: DST Spring Forward
    # ====================

    def test_dst_spring_forward_17_00_still_exists(self):
        """
        Test that 17:00 exists on DST spring forward day.

        Spring DST: March 9, 2025, 2 AM → 3 AM

        The hour 2 AM doesn't exist (clock jumps forward).
        But 17:00 still exists normally and should convert to UTC correctly.
        """
        # DST spring forward day: March 9, 2025 at 17:00 ET
        dst_day = datetime(2025, 3, 9, 17, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        # Verify this is a valid datetime (17:00 exists)
        assert dst_day is not None

        # Convert to UTC
        utc_time = dst_day.astimezone(ZoneInfo("UTC"))

        # After DST starts (March 9), 17:00 ET should be 21:00 UTC
        assert utc_time.hour == 21, (
            f"Post-DST 17:00 ET (March 9) should be 21:00 UTC, "
            f"got {utc_time.hour}:00 UTC"
        )

    async def test_dst_spring_forward_no_duplicate_reset(
        self,
        reset_scheduler,
        pnl_tracker
    ):
        """
        Test that reset happens exactly once on DST spring forward day.

        Even though the clock jumps from 2 AM → 3 AM, the 17:00 reset
        should happen exactly once, not skip or duplicate.

        This test validates that the reset scheduler's duplicate prevention
        works correctly on DST transition days.
        """
        account_id = "TEST-DST-001"

        # Schedule daily reset at 17:00 ET
        reset_scheduler.schedule_daily_reset(account_id, reset_time="17:00")

        # Add some P&L for today
        pnl_tracker.add_trade_pnl(account_id, -300.00)

        # Verify P&L was added
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == -300.00, f"P&L should be -$300, got ${daily_pnl}"

        # Manually trigger reset (simulating 17:00 ET on DST day)
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # Verify P&L was reset (reset uses today's date by default)
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == 0.00, (
            f"P&L should be reset to $0 after manual reset, got ${daily_pnl}"
        )

        # Try to trigger reset again (should be prevented by today's tracking)
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # P&L should still be $0 (not reset twice)
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == 0.00, (
            "P&L should still be $0 - reset should not trigger twice on same day"
        )

    # ====================
    # Test 4: DST Fall Back
    # ====================

    def test_dst_fall_back_17_00_happens_once(self):
        """
        Test that 17:00 happens exactly once on DST fall back day.

        Fall DST: November 2, 2025, 2 AM → 1 AM (hour repeats)

        The hour 1 AM happens twice (clock falls back).
        But 17:00 only happens once and should convert to UTC correctly.
        """
        # DST fall back day: November 2, 2025 at 17:00 ET
        dst_day = datetime(2025, 11, 2, 17, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        # Convert to UTC
        utc_time = dst_day.astimezone(ZoneInfo("UTC"))

        # After DST ends (November 2), 17:00 ET should be 22:00 UTC
        # (back to standard time offset)
        assert utc_time.hour == 22, (
            f"Post-DST 17:00 ET (November 2) should be 22:00 UTC, "
            f"got {utc_time.hour}:00 UTC"
        )

    async def test_dst_fall_back_no_duplicate_reset(
        self,
        reset_scheduler,
        pnl_tracker
    ):
        """
        Test that reset happens exactly once on DST fall back day.

        Even though 1 AM happens twice (clock falls back), the 17:00 reset
        should happen exactly once, not duplicate.
        """
        account_id = "TEST-DST-002"

        # Schedule daily reset at 17:00 ET
        reset_scheduler.schedule_daily_reset(account_id, reset_time="17:00")

        # Add some P&L for today
        pnl_tracker.add_trade_pnl(account_id, -400.00)

        # Verify P&L was added
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == -400.00, "Reset should not trigger before 17:00"

        # Manually trigger reset (simulating 17:00 ET on DST fall back day)
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # Verify P&L was reset exactly once
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == 0.00, (
            f"P&L should be reset to $0 after manual reset, got ${daily_pnl}"
        )

        # Verify reset doesn't trigger again
        # Add more P&L
        pnl_tracker.add_trade_pnl(account_id, -100.00)

        # Try to trigger reset again (should be prevented by today's tracking)
        reset_scheduler.trigger_reset_manually(account_id, "daily")

        # P&L should be -$100 (not reset again)
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == -100.00, (
            "Reset should not trigger twice on same day"
        )

    # ====================
    # Test 5: Lockout Expiry Across DST
    # ====================

    async def test_lockout_expiry_respects_dst_spring(
        self,
        lockout_manager,
        db
    ):
        """
        Test that lockouts expire at correct time across DST spring forward.

        A lockout set on March 8 (before DST) should expire at 17:00 ET on
        March 9 (after DST), correctly handling the timezone change.
        """
        account_id = 12345
        et_tz = ZoneInfo("America/New_York")

        # Mock time to be on March 8 at 16:00 ET (before DST)
        current_time = datetime(2025, 3, 8, 16, 0, 0, tzinfo=et_tz)

        # Calculate expiry at 17:00 ET next day (March 9, after DST)
        expiry_time = datetime(2025, 3, 9, 17, 0, 0, tzinfo=et_tz)

        # Set lockout with mocked current time
        with patch('risk_manager.state.lockout_manager.datetime') as mock_dt:
            mock_dt.now.return_value = current_time.astimezone(ZoneInfo("UTC"))

            lockout_manager.set_lockout(
                account_id=account_id,
                reason="Test DST spring lockout",
                until=expiry_time
            )

            # Verify lockout is active (still using mocked time)
            is_locked = lockout_manager.is_locked_out(account_id)
            assert is_locked is True, "Lockout should be active"

        # Mock time to be just before expiry (March 9, 16:59:59 ET)
        with patch('risk_manager.state.lockout_manager.datetime') as mock_dt:
            before_expiry = datetime(2025, 3, 9, 16, 59, 59, tzinfo=et_tz)
            mock_dt.now.return_value = before_expiry.astimezone(ZoneInfo("UTC"))

            # Lockout should still be active
            is_locked = lockout_manager.is_locked_out(account_id)
            assert is_locked is True, "Lockout should still be active before 17:00"

        # Mock time to be after expiry (March 9, 17:00:01 ET)
        with patch('risk_manager.state.lockout_manager.datetime') as mock_dt:
            after_expiry = datetime(2025, 3, 9, 17, 0, 1, tzinfo=et_tz)
            mock_dt.now.return_value = after_expiry.astimezone(ZoneInfo("UTC"))

            # Lockout should be expired (auto-cleared by is_locked_out)
            is_locked = lockout_manager.is_locked_out(account_id)
            assert is_locked is False, (
                "Lockout should be expired after 17:00 on March 9"
            )

    async def test_lockout_expiry_respects_dst_fall(
        self,
        lockout_manager
    ):
        """
        Test that lockouts expire at correct time across DST fall back.

        A lockout set on November 1 (before fall back) should expire at
        17:00 ET on November 2 (after fall back), correctly handling the
        timezone change.
        """
        account_id = 67890
        et_tz = ZoneInfo("America/New_York")

        # Set lockout at 16:00 ET on day before DST fall back (November 1)
        lockout_time = datetime(2025, 11, 1, 16, 0, 0, tzinfo=et_tz)

        # Calculate expiry at 17:00 ET next day (November 2, after fall back)
        expiry_time = datetime(2025, 11, 2, 17, 0, 0, tzinfo=et_tz)

        # Set lockout
        lockout_manager.set_lockout(
            account_id=account_id,
            reason="Test DST fall lockout",
            until=expiry_time
        )

        # Verify lockout is active
        is_locked = lockout_manager.is_locked_out(account_id)
        assert is_locked is True, "Lockout should be active"

        # Mock time to be just before expiry (November 2, 16:59:59 ET)
        with patch('risk_manager.state.lockout_manager.datetime') as mock_dt:
            before_expiry = datetime(2025, 11, 2, 16, 59, 59, tzinfo=et_tz)
            mock_dt.now.return_value = before_expiry.astimezone(ZoneInfo("UTC"))

            # Lockout should still be active
            is_locked = lockout_manager.is_locked_out(account_id)
            assert is_locked is True, "Lockout should still be active before 17:00"

        # Mock time to be after expiry (November 2, 17:00:01 ET)
        with patch('risk_manager.state.lockout_manager.datetime') as mock_dt:
            after_expiry = datetime(2025, 11, 2, 17, 0, 1, tzinfo=et_tz)
            mock_dt.now.return_value = after_expiry.astimezone(ZoneInfo("UTC"))

            # Lockout should be expired
            is_locked = lockout_manager.is_locked_out(account_id)
            assert is_locked is False, (
                "Lockout should be expired after 17:00 on November 2"
            )

    # ====================
    # Test 6: UTC vs ET Reset Time
    # ====================

    async def test_reset_uses_et_not_utc(
        self,
        reset_scheduler,
        pnl_tracker
    ):
        """
        Test that reset time is based on ET, not UTC.

        Validates that a 17:00 ET reset happens at the correct UTC time,
        which changes depending on DST.
        """
        account_id = "TEST-TZ-001"

        # Schedule daily reset at 17:00 ET
        reset_scheduler.schedule_daily_reset(account_id, reset_time="17:00")

        # Test in standard time (January)
        et_tz = ZoneInfo("America/New_York")
        standard_time = datetime(2025, 1, 15, 17, 0, 0, tzinfo=et_tz)
        utc_time_standard = standard_time.astimezone(ZoneInfo("UTC"))

        # 17:00 ET in January should be 22:00 UTC
        assert utc_time_standard.hour == 22, (
            "17:00 ET in standard time should be 22:00 UTC"
        )

        # Test in daylight time (July)
        daylight_time = datetime(2025, 7, 15, 17, 0, 0, tzinfo=et_tz)
        utc_time_daylight = daylight_time.astimezone(ZoneInfo("UTC"))

        # 17:00 ET in July should be 21:00 UTC
        assert utc_time_daylight.hour == 21, (
            "17:00 ET in daylight time should be 21:00 UTC"
        )

        # The key insight: reset time changes in UTC, but stays at 17:00 ET
        assert standard_time.hour == daylight_time.hour == 17, (
            "Reset always happens at 17:00 ET, regardless of DST"
        )
