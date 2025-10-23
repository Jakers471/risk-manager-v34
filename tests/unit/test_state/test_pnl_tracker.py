"""
TDD Tests for PnLTracker

Tests the daily P&L tracking with SQLite persistence.
Written BEFORE implementation (TDD approach).
"""

import pytest
from datetime import date, datetime
from pathlib import Path
import tempfile

from risk_manager.state.database import Database
from risk_manager.state.pnl_tracker import PnLTracker


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
def pnl_tracker(temp_db):
    """Create a PnLTracker instance for testing."""
    return PnLTracker(temp_db)


class TestPnLTrackerBasics:
    """Test basic PnLTracker functionality."""

    def test_tracker_initializes(self, pnl_tracker):
        """Test that tracker initializes successfully."""
        assert pnl_tracker is not None
        assert pnl_tracker.db is not None

    def test_get_daily_pnl_returns_zero_for_new_account(self, pnl_tracker):
        """Test that new accounts start with zero P&L."""
        account_id = "TEST-ACCOUNT-001"
        today = date.today()

        pnl = pnl_tracker.get_daily_pnl(account_id, today)

        assert pnl == 0.0

    def test_add_trade_pnl_updates_daily_total(self, pnl_tracker):
        """Test that adding trade P&L updates daily total."""
        account_id = "TEST-ACCOUNT-001"
        today = date.today()

        # Add first trade
        pnl_tracker.add_trade_pnl(account_id, -100.0, today)
        assert pnl_tracker.get_daily_pnl(account_id, today) == -100.0

        # Add second trade
        pnl_tracker.add_trade_pnl(account_id, -150.0, today)
        assert pnl_tracker.get_daily_pnl(account_id, today) == -250.0

        # Add positive trade
        pnl_tracker.add_trade_pnl(account_id, 80.0, today)
        assert pnl_tracker.get_daily_pnl(account_id, today) == -170.0


class TestPnLTrackerPersistence:
    """Test that P&L data persists across tracker instances."""

    def test_pnl_survives_restart(self, temp_db):
        """Test that P&L data survives tracker restart."""
        account_id = "TEST-ACCOUNT-001"
        today = date.today()

        # First tracker instance
        tracker1 = PnLTracker(temp_db)
        tracker1.add_trade_pnl(account_id, -200.0, today)
        tracker1.add_trade_pnl(account_id, -150.0, today)
        assert tracker1.get_daily_pnl(account_id, today) == -350.0

        # Create new tracker instance (simulates restart)
        tracker2 = PnLTracker(temp_db)

        # Data should persist
        assert tracker2.get_daily_pnl(account_id, today) == -350.0

    def test_multiple_accounts_tracked_independently(self, pnl_tracker):
        """Test that multiple accounts are tracked independently."""
        account1 = "ACCOUNT-001"
        account2 = "ACCOUNT-002"
        today = date.today()

        pnl_tracker.add_trade_pnl(account1, -200.0, today)
        pnl_tracker.add_trade_pnl(account2, -300.0, today)

        assert pnl_tracker.get_daily_pnl(account1, today) == -200.0
        assert pnl_tracker.get_daily_pnl(account2, today) == -300.0


class TestPnLTrackerReset:
    """Test daily reset functionality."""

    def test_reset_clears_daily_pnl(self, pnl_tracker):
        """Test that reset clears daily P&L."""
        account_id = "TEST-ACCOUNT-001"
        today = date.today()

        # Add some trades
        pnl_tracker.add_trade_pnl(account_id, -200.0, today)
        pnl_tracker.add_trade_pnl(account_id, -150.0, today)
        assert pnl_tracker.get_daily_pnl(account_id, today) == -350.0

        # Reset
        pnl_tracker.reset_daily_pnl(account_id, today)

        # Should be zero after reset
        assert pnl_tracker.get_daily_pnl(account_id, today) == 0.0

    def test_different_dates_tracked_separately(self, pnl_tracker):
        """Test that different dates are tracked separately."""
        account_id = "TEST-ACCOUNT-001"

        from datetime import timedelta
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Add trades on different days
        pnl_tracker.add_trade_pnl(account_id, -200.0, yesterday)
        pnl_tracker.add_trade_pnl(account_id, -150.0, today)

        # Check both days
        assert pnl_tracker.get_daily_pnl(account_id, yesterday) == -200.0
        assert pnl_tracker.get_daily_pnl(account_id, today) == -150.0


class TestPnLTrackerTradeCount:
    """Test trade count tracking."""

    def test_trade_count_increments(self, pnl_tracker):
        """Test that trade count increments correctly."""
        account_id = "TEST-ACCOUNT-001"
        today = date.today()

        # Add trades
        pnl_tracker.add_trade_pnl(account_id, -100.0, today)
        pnl_tracker.add_trade_pnl(account_id, -150.0, today)
        pnl_tracker.add_trade_pnl(account_id, 80.0, today)

        # Check trade count
        count = pnl_tracker.get_trade_count(account_id, today)
        assert count == 3

    def test_trade_count_resets_with_pnl(self, pnl_tracker):
        """Test that trade count resets with P&L."""
        account_id = "TEST-ACCOUNT-001"
        today = date.today()

        # Add trades
        pnl_tracker.add_trade_pnl(account_id, -100.0, today)
        pnl_tracker.add_trade_pnl(account_id, -150.0, today)
        assert pnl_tracker.get_trade_count(account_id, today) == 2

        # Reset
        pnl_tracker.reset_daily_pnl(account_id, today)

        # Count should be zero
        assert pnl_tracker.get_trade_count(account_id, today) == 0


class TestPnLTrackerEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_zero_pnl_trades(self, pnl_tracker):
        """Test that zero P&L trades are handled correctly."""
        account_id = "TEST-ACCOUNT-001"
        today = date.today()

        pnl_tracker.add_trade_pnl(account_id, 0.0, today)
        pnl_tracker.add_trade_pnl(account_id, -100.0, today)

        assert pnl_tracker.get_daily_pnl(account_id, today) == -100.0
        assert pnl_tracker.get_trade_count(account_id, today) == 2

    def test_handles_large_pnl_values(self, pnl_tracker):
        """Test that large P&L values are handled correctly."""
        account_id = "TEST-ACCOUNT-001"
        today = date.today()

        pnl_tracker.add_trade_pnl(account_id, -10000.50, today)
        pnl_tracker.add_trade_pnl(account_id, 5000.25, today)

        assert pnl_tracker.get_daily_pnl(account_id, today) == -5000.25

    def test_get_all_account_pnls(self, pnl_tracker):
        """Test getting P&L for all accounts on a given date."""
        today = date.today()

        pnl_tracker.add_trade_pnl("ACCOUNT-001", -200.0, today)
        pnl_tracker.add_trade_pnl("ACCOUNT-002", -300.0, today)
        pnl_tracker.add_trade_pnl("ACCOUNT-003", 100.0, today)

        all_pnls = pnl_tracker.get_all_daily_pnls(today)

        assert len(all_pnls) == 3
        assert all_pnls["ACCOUNT-001"] == -200.0
        assert all_pnls["ACCOUNT-002"] == -300.0
        assert all_pnls["ACCOUNT-003"] == 100.0
