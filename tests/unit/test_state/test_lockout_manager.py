"""
TDD Tests for MOD-002: Lockout Manager

Tests the centralized lockout state management system.
Handles hard lockouts (until specific time), cooldown timers (duration-based),
auto-expiry, and persistence.

Written BEFORE implementation (TDD RED phase).
"""

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
from unittest.mock import Mock, AsyncMock, call
import asyncio

from risk_manager.state.database import Database
from risk_manager.state.lockout_manager import LockoutManager


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
def mock_timer_manager():
    """Mock Timer Manager (MOD-003) for cooldown timer tests."""
    mock = Mock()
    mock.start_timer = AsyncMock()
    mock.cancel_timer = Mock()  # Synchronous method
    mock.get_remaining_time = Mock(return_value=1800)
    mock.is_active = Mock(return_value=True)
    return mock


@pytest.fixture
def lockout_manager(temp_db, mock_timer_manager):
    """Create a LockoutManager instance for testing."""
    return LockoutManager(temp_db, mock_timer_manager)


# =============================================================================
# CATEGORY 1: HARD LOCKOUT OPERATIONS (6 tests)
# =============================================================================


class TestHardLockoutOperations:
    """Test hard lockout operations (locked until specific time)."""

    def test_set_lockout_locks_account(self, lockout_manager):
        """
        GIVEN: LockoutManager initialized
        WHEN: set_lockout() is called with account_id, reason, and until time
        THEN: Account is locked until specified time
        """
        # ARRANGE
        account_id = 123
        reason = "Daily loss limit exceeded"
        until = datetime.now(timezone.utc) + timedelta(hours=2)

        # ACT
        lockout_manager.set_lockout(account_id, reason, until)

        # ASSERT
        assert lockout_manager.is_locked_out(account_id) is True

    def test_is_locked_out_returns_true_when_locked(self, lockout_manager):
        """
        GIVEN: Account is locked
        WHEN: is_locked_out() is called
        THEN: Returns True
        """
        # ARRANGE
        account_id = 123
        until = datetime.now(timezone.utc) + timedelta(hours=2)
        lockout_manager.set_lockout(account_id, "Test reason", until)

        # ACT
        result = lockout_manager.is_locked_out(account_id)

        # ASSERT
        assert result is True

    def test_is_locked_out_returns_false_when_not_locked(self, lockout_manager):
        """
        GIVEN: Account is not locked
        WHEN: is_locked_out() is called
        THEN: Returns False
        """
        # ARRANGE
        account_id = 123

        # ACT
        result = lockout_manager.is_locked_out(account_id)

        # ASSERT
        assert result is False

    def test_get_lockout_info_returns_details(self, lockout_manager):
        """
        GIVEN: Account is locked
        WHEN: get_lockout_info() is called
        THEN: Returns dict with reason, until, type, created_at
        """
        # ARRANGE
        account_id = 123
        reason = "Daily loss limit exceeded"
        until = datetime.now(timezone.utc) + timedelta(hours=2)
        lockout_manager.set_lockout(account_id, reason, until)

        # ACT
        info = lockout_manager.get_lockout_info(account_id)

        # ASSERT
        assert info is not None
        assert info["reason"] == reason
        assert info["until"] == until
        assert info["type"] == "hard_lockout"
        assert "created_at" in info

    def test_get_lockout_info_returns_none_when_not_locked(self, lockout_manager):
        """
        GIVEN: Account is not locked
        WHEN: get_lockout_info() is called
        THEN: Returns None
        """
        # ARRANGE
        account_id = 123

        # ACT
        info = lockout_manager.get_lockout_info(account_id)

        # ASSERT
        assert info is None

    def test_clear_lockout_removes_lockout(self, lockout_manager):
        """
        GIVEN: Account is locked
        WHEN: clear_lockout() is called
        THEN: Account is no longer locked
        """
        # ARRANGE
        account_id = 123
        until = datetime.now(timezone.utc) + timedelta(hours=2)
        lockout_manager.set_lockout(account_id, "Test reason", until)
        assert lockout_manager.is_locked_out(account_id) is True

        # ACT
        lockout_manager.clear_lockout(account_id)

        # ASSERT
        assert lockout_manager.is_locked_out(account_id) is False


# =============================================================================
# CATEGORY 2: COOLDOWN TIMERS (5 tests)
# =============================================================================


class TestCooldownTimers:
    """Test cooldown timer operations (duration-based lockouts)."""

    @pytest.mark.asyncio
    async def test_set_cooldown_creates_timer(self, lockout_manager, mock_timer_manager):
        """
        GIVEN: LockoutManager initialized with timer manager
        WHEN: set_cooldown() is called with duration
        THEN: Timer is started via MOD-003 Timer Manager
        """
        # ARRANGE
        account_id = 123
        reason = "Post-loss cooldown"
        duration = 1800  # 30 minutes

        # ACT
        await lockout_manager.set_cooldown(account_id, reason, duration)

        # ASSERT
        mock_timer_manager.start_timer.assert_called_once()
        assert lockout_manager.is_locked_out(account_id) is True

    @pytest.mark.asyncio
    async def test_cooldown_auto_expires_after_duration(self, lockout_manager, mock_timer_manager):
        """
        GIVEN: Cooldown timer set
        WHEN: Timer duration expires
        THEN: Lockout is automatically cleared
        """
        # ARRANGE
        account_id = 123
        duration = 1800

        # Setup mock to execute callback immediately
        async def mock_start_timer(name, duration, callback):
            await callback()

        mock_timer_manager.start_timer = mock_start_timer

        # ACT
        await lockout_manager.set_cooldown(account_id, "Test", duration)

        # Wait for async callback
        await asyncio.sleep(0.1)

        # ASSERT
        assert lockout_manager.is_locked_out(account_id) is False

    @pytest.mark.asyncio
    async def test_cooldown_remaining_time_decreases(self, lockout_manager, mock_timer_manager):
        """
        GIVEN: Cooldown timer active
        WHEN: Time passes
        THEN: Remaining time decreases
        """
        # ARRANGE
        account_id = 123
        duration = 1800

        # Mock remaining time to simulate countdown
        mock_timer_manager.get_remaining_time.side_effect = [1800, 1500, 1200]

        # ACT
        await lockout_manager.set_cooldown(account_id, "Test", duration)

        # ASSERT
        assert lockout_manager.get_remaining_time(account_id) == 1800
        assert lockout_manager.get_remaining_time(account_id) == 1500
        assert lockout_manager.get_remaining_time(account_id) == 1200

    @pytest.mark.asyncio
    async def test_cooldown_cleared_cancels_timer(self, lockout_manager, mock_timer_manager):
        """
        GIVEN: Cooldown timer active
        WHEN: clear_lockout() is called
        THEN: Timer is cancelled via MOD-003
        """
        # ARRANGE
        account_id = 123
        duration = 1800
        await lockout_manager.set_cooldown(account_id, "Test", duration)

        # ACT
        lockout_manager.clear_lockout(account_id)

        # ASSERT
        mock_timer_manager.cancel_timer.assert_called_once()
        assert lockout_manager.is_locked_out(account_id) is False

    @pytest.mark.asyncio
    async def test_cooldown_integrates_with_timer_manager(self, lockout_manager, mock_timer_manager):
        """
        GIVEN: LockoutManager with timer manager
        WHEN: set_cooldown() is called
        THEN: Timer manager receives correct parameters
        """
        # ARRANGE
        account_id = 123
        reason = "Post-loss cooldown"
        duration = 1800

        # ACT
        await lockout_manager.set_cooldown(account_id, reason, duration)

        # ASSERT
        call_args = mock_timer_manager.start_timer.call_args
        assert call_args is not None
        assert call_args.kwargs["duration"] == duration
        assert "callback" in call_args.kwargs


# =============================================================================
# CATEGORY 3: BACKGROUND TASK (3 tests)
# =============================================================================


class TestBackgroundTask:
    """Test background task for checking expired lockouts."""

    @pytest.mark.asyncio
    async def test_check_expired_lockouts_runs_every_second(self, lockout_manager):
        """
        GIVEN: Background task started
        WHEN: Multiple seconds pass
        THEN: check_expired_lockouts() is called repeatedly
        """
        # ARRANGE
        check_count = 0

        # Mock the check method
        original_check = lockout_manager.check_expired_lockouts

        def mock_check():
            nonlocal check_count
            check_count += 1
            original_check()

        lockout_manager.check_expired_lockouts = mock_check

        # ACT
        task = asyncio.create_task(lockout_manager.start_background_task())
        await asyncio.sleep(2.5)  # Run for 2.5 seconds
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # ASSERT
        assert check_count >= 2  # Should run at least 2 times in 2.5 seconds

    @pytest.mark.asyncio
    async def test_expired_lockout_auto_cleared(self, lockout_manager):
        """
        GIVEN: Lockout with past expiry time
        WHEN: check_expired_lockouts() runs
        THEN: Lockout is automatically cleared
        """
        # ARRANGE
        account_id = 123
        until = datetime.now(timezone.utc) - timedelta(seconds=10)  # Expired 10 seconds ago
        lockout_manager.set_lockout(account_id, "Test", until)
        # Verify lockout is in state (don't use is_locked_out() which auto-clears)
        assert account_id in lockout_manager.lockout_state

        # ACT
        lockout_manager.check_expired_lockouts()

        # ASSERT
        assert account_id not in lockout_manager.lockout_state

    @pytest.mark.asyncio
    async def test_background_task_stops_on_shutdown(self, lockout_manager):
        """
        GIVEN: Background task running
        WHEN: Shutdown is requested
        THEN: Background task stops gracefully
        """
        # ARRANGE
        task = asyncio.create_task(lockout_manager.start_background_task())
        await asyncio.sleep(0.5)

        # ACT
        task.cancel()

        # ASSERT
        try:
            await task
            assert False, "Task should have been cancelled"
        except asyncio.CancelledError:
            pass  # Expected


# =============================================================================
# CATEGORY 4: MULTIPLE ACCOUNTS (3 tests)
# =============================================================================


class TestMultipleAccounts:
    """Test lockout manager with multiple accounts."""

    def test_multiple_accounts_locked_independently(self, lockout_manager):
        """
        GIVEN: Multiple accounts
        WHEN: Each account is locked separately
        THEN: Each account's lockout is independent
        """
        # ARRANGE
        account1 = 123
        account2 = 456
        account3 = 789
        until1 = datetime.now(timezone.utc) + timedelta(hours=1)
        until2 = datetime.now(timezone.utc) + timedelta(hours=2)
        until3 = datetime.now(timezone.utc) + timedelta(hours=3)

        # ACT
        lockout_manager.set_lockout(account1, "Reason 1", until1)
        lockout_manager.set_lockout(account2, "Reason 2", until2)
        lockout_manager.set_lockout(account3, "Reason 3", until3)

        # ASSERT
        assert lockout_manager.is_locked_out(account1) is True
        assert lockout_manager.is_locked_out(account2) is True
        assert lockout_manager.is_locked_out(account3) is True

        info1 = lockout_manager.get_lockout_info(account1)
        info2 = lockout_manager.get_lockout_info(account2)
        info3 = lockout_manager.get_lockout_info(account3)

        assert info1["reason"] == "Reason 1"
        assert info2["reason"] == "Reason 2"
        assert info3["reason"] == "Reason 3"

    def test_lockout_affects_only_target_account(self, lockout_manager):
        """
        GIVEN: Multiple accounts, one locked
        WHEN: Lockout is set on one account
        THEN: Other accounts are not affected
        """
        # ARRANGE
        locked_account = 123
        unlocked_account1 = 456
        unlocked_account2 = 789
        until = datetime.now(timezone.utc) + timedelta(hours=2)

        # ACT
        lockout_manager.set_lockout(locked_account, "Test reason", until)

        # ASSERT
        assert lockout_manager.is_locked_out(locked_account) is True
        assert lockout_manager.is_locked_out(unlocked_account1) is False
        assert lockout_manager.is_locked_out(unlocked_account2) is False

    def test_clear_lockout_affects_only_target_account(self, lockout_manager):
        """
        GIVEN: Multiple accounts locked
        WHEN: clear_lockout() is called on one account
        THEN: Only that account is unlocked
        """
        # ARRANGE
        account1 = 123
        account2 = 456
        account3 = 789
        until = datetime.now(timezone.utc) + timedelta(hours=2)
        lockout_manager.set_lockout(account1, "Reason 1", until)
        lockout_manager.set_lockout(account2, "Reason 2", until)
        lockout_manager.set_lockout(account3, "Reason 3", until)

        # ACT
        lockout_manager.clear_lockout(account2)

        # ASSERT
        assert lockout_manager.is_locked_out(account1) is True
        assert lockout_manager.is_locked_out(account2) is False
        assert lockout_manager.is_locked_out(account3) is True


# =============================================================================
# CATEGORY 5: DATABASE PERSISTENCE (5 tests)
# =============================================================================


class TestDatabasePersistence:
    """Test lockout state persistence to SQLite database."""

    def test_lockout_saved_to_database(self, temp_db, mock_timer_manager):
        """
        GIVEN: LockoutManager with database
        WHEN: set_lockout() is called
        THEN: Lockout is saved to database (INSERT)
        """
        # ARRANGE
        manager = LockoutManager(temp_db, mock_timer_manager)
        account_id = 123
        reason = "Daily loss limit"
        until = datetime.now(timezone.utc) + timedelta(hours=2)

        # ACT
        manager.set_lockout(account_id, reason, until)

        # ASSERT
        row = temp_db.execute_one(
            "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
            (str(account_id),)
        )
        assert row is not None
        assert row["reason"] == reason

    def test_lockout_deleted_from_database_on_clear(self, temp_db, mock_timer_manager):
        """
        GIVEN: Lockout exists in database
        WHEN: clear_lockout() is called
        THEN: Lockout is marked inactive (DELETE/UPDATE)
        """
        # ARRANGE
        manager = LockoutManager(temp_db, mock_timer_manager)
        account_id = 123
        until = datetime.now(timezone.utc) + timedelta(hours=2)
        manager.set_lockout(account_id, "Test", until)

        # Verify it exists
        row = temp_db.execute_one(
            "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
            (str(account_id),)
        )
        assert row is not None

        # ACT
        manager.clear_lockout(account_id)

        # ASSERT
        row = temp_db.execute_one(
            "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
            (str(account_id),)
        )
        assert row is None

    def test_load_lockouts_populates_memory_state(self, temp_db, mock_timer_manager):
        """
        GIVEN: Lockouts exist in database
        WHEN: load_lockouts_from_db() is called
        THEN: Lockouts are loaded into memory state
        """
        # ARRANGE
        account_id = 123
        reason = "Test lockout"
        until = datetime.now(timezone.utc) + timedelta(hours=2)

        # Insert directly into database
        temp_db.execute_write(
            """
            INSERT INTO lockouts (account_id, rule_id, reason, locked_at, expires_at, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (str(account_id), "RULE-003", reason, datetime.now(timezone.utc).isoformat(),
             until.isoformat(), 1, datetime.now(timezone.utc).isoformat())
        )

        # ACT
        manager = LockoutManager(temp_db, mock_timer_manager)
        manager.load_lockouts_from_db()

        # ASSERT
        assert manager.is_locked_out(account_id) is True
        info = manager.get_lockout_info(account_id)
        assert info["reason"] == reason

    def test_expired_lockout_removed_from_database(self, temp_db, mock_timer_manager):
        """
        GIVEN: Expired lockout in database
        WHEN: check_expired_lockouts() runs
        THEN: Lockout is removed from database
        """
        # ARRANGE
        manager = LockoutManager(temp_db, mock_timer_manager)
        account_id = 123
        until = datetime.now(timezone.utc) - timedelta(seconds=10)  # Expired
        manager.set_lockout(account_id, "Test", until)

        # ACT
        manager.check_expired_lockouts()

        # ASSERT
        row = temp_db.execute_one(
            "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
            (str(account_id),)
        )
        assert row is None

    def test_database_schema_correct(self, temp_db):
        """
        GIVEN: Database initialized
        WHEN: Schema is checked
        THEN: lockouts table has correct structure
        """
        # ACT
        cursor = temp_db.execute("PRAGMA table_info(lockouts)")
        columns = {row["name"]: row["type"] for row in cursor}

        # ASSERT
        assert "id" in columns
        assert "account_id" in columns
        assert "rule_id" in columns
        assert "reason" in columns
        assert "locked_at" in columns
        assert "expires_at" in columns
        assert "unlock_condition" in columns
        assert "active" in columns
        assert "created_at" in columns


# =============================================================================
# CATEGORY 6: EDGE CASES (3 tests)
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_lockout_until_past_time_immediately_expired(self, lockout_manager):
        """
        GIVEN: Lockout with past expiry time
        WHEN: set_lockout() is called
        THEN: Lockout is immediately expired (edge case)
        """
        # ARRANGE
        account_id = 123
        until = datetime.now(timezone.utc) - timedelta(hours=1)  # Already expired

        # ACT
        lockout_manager.set_lockout(account_id, "Test", until)
        lockout_manager.check_expired_lockouts()

        # ASSERT
        assert lockout_manager.is_locked_out(account_id) is False

    def test_lockout_reason_persisted_correctly(self, lockout_manager):
        """
        GIVEN: Lockout with multi-line reason text
        WHEN: Lockout is set and retrieved
        THEN: Reason text is preserved correctly
        """
        # ARRANGE
        account_id = 123
        reason = "Daily loss limit exceeded\nMax loss: $500\nCurrent loss: $550"
        until = datetime.now(timezone.utc) + timedelta(hours=2)

        # ACT
        lockout_manager.set_lockout(account_id, reason, until)
        info = lockout_manager.get_lockout_info(account_id)

        # ASSERT
        assert info["reason"] == reason

    def test_double_lockout_overwrites_previous(self, lockout_manager):
        """
        GIVEN: Account already locked
        WHEN: set_lockout() is called again
        THEN: Previous lockout is overwritten (idempotent)
        """
        # ARRANGE
        account_id = 123
        until1 = datetime.now(timezone.utc) + timedelta(hours=1)
        until2 = datetime.now(timezone.utc) + timedelta(hours=3)

        # ACT
        lockout_manager.set_lockout(account_id, "Reason 1", until1)
        lockout_manager.set_lockout(account_id, "Reason 2", until2)

        # ASSERT
        info = lockout_manager.get_lockout_info(account_id)
        assert info["reason"] == "Reason 2"
        assert info["until"] == until2


# =============================================================================
# CATEGORY 7: INTEGRATION WITH EVENT ROUTER (2 tests)
# =============================================================================


class TestEventRouterIntegration:
    """Test integration with Event Router (MOD-006)."""

    def test_locked_account_blocks_rule_processing(self, lockout_manager):
        """
        GIVEN: Account is locked
        WHEN: Event router checks lockout status
        THEN: Event processing is blocked
        """
        # ARRANGE
        account_id = 123
        until = datetime.now(timezone.utc) + timedelta(hours=2)
        lockout_manager.set_lockout(account_id, "Test", until)

        # ACT - Simulate event router check
        should_process_rules = not lockout_manager.is_locked_out(account_id)

        # ASSERT
        assert should_process_rules is False

    def test_unlocked_account_allows_rule_processing(self, lockout_manager):
        """
        GIVEN: Account is not locked
        WHEN: Event router checks lockout status
        THEN: Event processing is allowed
        """
        # ARRANGE
        account_id = 123

        # ACT - Simulate event router check
        should_process_rules = not lockout_manager.is_locked_out(account_id)

        # ASSERT
        assert should_process_rules is True


# =============================================================================
# CATEGORY 8: LOCKOUT TYPES (2 tests)
# =============================================================================


class TestLockoutTypes:
    """Test different lockout types (hard lockout vs cooldown)."""

    def test_hard_lockout_type_stored_correctly(self, lockout_manager):
        """
        GIVEN: Hard lockout set
        WHEN: Lockout info retrieved
        THEN: Type is 'hard_lockout'
        """
        # ARRANGE
        account_id = 123
        until = datetime.now(timezone.utc) + timedelta(hours=2)

        # ACT
        lockout_manager.set_lockout(account_id, "Test", until)
        info = lockout_manager.get_lockout_info(account_id)

        # ASSERT
        assert info["type"] == "hard_lockout"

    @pytest.mark.asyncio
    async def test_cooldown_type_stored_correctly(self, lockout_manager):
        """
        GIVEN: Cooldown timer set
        WHEN: Lockout info retrieved
        THEN: Type is 'cooldown'
        """
        # ARRANGE
        account_id = 123
        duration = 1800

        # ACT
        await lockout_manager.set_cooldown(account_id, "Test", duration)
        info = lockout_manager.get_lockout_info(account_id)

        # ASSERT
        assert info["type"] == "cooldown"


# =============================================================================
# CATEGORY 9: STARTUP AND SHUTDOWN (2 tests)
# =============================================================================


class TestStartupShutdown:
    """Test startup and shutdown procedures."""

    def test_lockouts_restored_on_startup(self, temp_db, mock_timer_manager):
        """
        GIVEN: Active lockouts in database
        WHEN: LockoutManager is initialized
        THEN: Lockouts are restored to memory
        """
        # ARRANGE - Create lockout in database
        account_id = 123
        reason = "Restored lockout"
        until = datetime.now(timezone.utc) + timedelta(hours=2)

        temp_db.execute_write(
            """
            INSERT INTO lockouts (account_id, rule_id, reason, locked_at, expires_at, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (str(account_id), "RULE-003", reason, datetime.now(timezone.utc).isoformat(),
             until.isoformat(), 1, datetime.now(timezone.utc).isoformat())
        )

        # ACT - Initialize manager (should load lockouts)
        manager = LockoutManager(temp_db, mock_timer_manager)

        # ASSERT
        assert manager.is_locked_out(account_id) is True

    @pytest.mark.asyncio
    async def test_shutdown_cancels_all_timers(self, lockout_manager, mock_timer_manager):
        """
        GIVEN: Multiple cooldown timers active
        WHEN: Shutdown is called
        THEN: All timers are cancelled
        """
        # ARRANGE
        account1 = 123
        account2 = 456
        await lockout_manager.set_cooldown(account1, "Test 1", 1800)
        await lockout_manager.set_cooldown(account2, "Test 2", 1800)

        # ACT
        await lockout_manager.shutdown()

        # ASSERT
        assert mock_timer_manager.cancel_timer.call_count >= 2
