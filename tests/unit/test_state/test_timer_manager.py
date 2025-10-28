"""
Unit Tests for MOD-003: Timer Manager

Tests the Timer Manager which provides countdown timers for cooldowns,
session checks, and scheduled tasks.

RED PHASE (TDD): All tests expected to FAIL initially.
Implementation comes AFTER these tests are written.

Specification: docs/specifications/unified/architecture/MODULES_SUMMARY.md (lines 186-270)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, call
from typing import Dict, Any


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def timer_manager():
    """
    Create a TimerManager instance for testing.

    Starts the manager and ensures cleanup after test.
    """
    from risk_manager.state.timer_manager import TimerManager

    manager = TimerManager()
    await manager.start()

    yield manager

    # Cleanup
    await manager.stop()


@pytest.fixture
def mock_callback():
    """Mock callback function for timer expiry."""
    return Mock()


@pytest.fixture
def async_mock_callback():
    """Mock async callback function for timer expiry."""
    return AsyncMock()


# ============================================================================
# Category 1: Basic Timer Operations (5 tests)
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_start_timer_creates_timer(timer_manager, mock_callback):
    """
    GIVEN: TimerManager is running
    WHEN: start_timer is called with valid parameters
    THEN: Timer is created and tracked
    """
    # ACT
    await timer_manager.start_timer(
        name="test_timer",
        duration=5,
        callback=mock_callback
    )

    # ASSERT
    assert timer_manager.has_timer("test_timer")
    remaining = timer_manager.get_remaining_time("test_timer")
    assert remaining > 0
    assert remaining <= 5


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_remaining_time_decreases(timer_manager, mock_callback):
    """
    GIVEN: Timer started with 5-second duration
    WHEN: Time passes
    THEN: Remaining time decreases
    """
    # ARRANGE
    await timer_manager.start_timer(
        name="countdown_timer",
        duration=5,
        callback=mock_callback
    )

    # ACT
    initial_remaining = timer_manager.get_remaining_time("countdown_timer")
    await asyncio.sleep(2)
    later_remaining = timer_manager.get_remaining_time("countdown_timer")

    # ASSERT
    assert initial_remaining > later_remaining
    assert later_remaining >= 1  # At least 1 second left
    assert later_remaining <= 3  # At most 3 seconds left


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_timer_removes_timer(timer_manager, mock_callback):
    """
    GIVEN: Active timer exists
    WHEN: cancel_timer is called
    THEN: Timer is removed and callback does NOT execute
    """
    # ARRANGE
    await timer_manager.start_timer(
        name="cancelable_timer",
        duration=10,
        callback=mock_callback
    )
    assert timer_manager.has_timer("cancelable_timer")

    # ACT
    timer_manager.cancel_timer("cancelable_timer")

    # ASSERT
    assert not timer_manager.has_timer("cancelable_timer")

    # Wait long enough for timer to have expired
    await asyncio.sleep(11)

    # Callback should NOT have been called
    mock_callback.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_expired_timer_executes_callback(timer_manager, mock_callback):
    """
    GIVEN: Timer with 2-second duration
    WHEN: Timer expires
    THEN: Callback is executed exactly once
    """
    # ARRANGE
    await timer_manager.start_timer(
        name="expiring_timer",
        duration=2,
        callback=mock_callback
    )

    # ACT - Wait for timer to expire (with tolerance)
    await asyncio.sleep(3.5)  # 2s duration + 1s check interval + 0.5s buffer

    # ASSERT
    mock_callback.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_expired_timer_auto_removed(timer_manager, mock_callback):
    """
    GIVEN: Timer that has expired and executed callback
    WHEN: Checking timer status after expiry
    THEN: Timer is no longer tracked
    """
    # ARRANGE
    await timer_manager.start_timer(
        name="auto_cleanup_timer",
        duration=2,
        callback=mock_callback
    )

    # ACT - Wait for expiry
    await asyncio.sleep(3.5)

    # ASSERT
    assert not timer_manager.has_timer("auto_cleanup_timer")
    assert timer_manager.get_remaining_time("auto_cleanup_timer") == 0


# ============================================================================
# Category 2: Multiple Timers (3 tests)
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_multiple_timers_run_simultaneously(timer_manager):
    """
    GIVEN: TimerManager is running
    WHEN: Multiple timers are started
    THEN: All timers run independently and simultaneously
    """
    # ARRANGE
    callback_a = Mock()
    callback_b = Mock()
    callback_c = Mock()

    # ACT
    await timer_manager.start_timer("timer_a", duration=3, callback=callback_a)
    await timer_manager.start_timer("timer_b", duration=5, callback=callback_b)
    await timer_manager.start_timer("timer_c", duration=7, callback=callback_c)

    # ASSERT - All timers exist
    assert timer_manager.has_timer("timer_a")
    assert timer_manager.has_timer("timer_b")
    assert timer_manager.has_timer("timer_c")

    # ASSERT - All have remaining time
    assert timer_manager.get_remaining_time("timer_a") > 0
    assert timer_manager.get_remaining_time("timer_b") > 0
    assert timer_manager.get_remaining_time("timer_c") > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_timers_expire_independently(timer_manager):
    """
    GIVEN: Multiple timers with different durations
    WHEN: Timers expire at different times
    THEN: Each callback executes at correct time
    """
    # ARRANGE
    callback_short = Mock()
    callback_medium = Mock()
    callback_long = Mock()

    await timer_manager.start_timer("short", duration=2, callback=callback_short)
    await timer_manager.start_timer("medium", duration=4, callback=callback_medium)
    await timer_manager.start_timer("long", duration=6, callback=callback_long)

    # ACT & ASSERT - After 3 seconds
    await asyncio.sleep(3.5)
    callback_short.assert_called_once()
    callback_medium.assert_not_called()
    callback_long.assert_not_called()

    # ACT & ASSERT - After 5 seconds total
    await asyncio.sleep(2)
    callback_short.assert_called_once()  # Still only once
    callback_medium.assert_called_once()
    callback_long.assert_not_called()

    # ACT & ASSERT - After 7 seconds total
    await asyncio.sleep(2)
    callback_short.assert_called_once()
    callback_medium.assert_called_once()
    callback_long.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_specific_timer_preserves_others(timer_manager):
    """
    GIVEN: Three active timers
    WHEN: One timer is cancelled
    THEN: Only that timer is removed, others continue
    """
    # ARRANGE
    callback_a = Mock()
    callback_b = Mock()
    callback_c = Mock()

    await timer_manager.start_timer("keep_a", duration=5, callback=callback_a)
    await timer_manager.start_timer("cancel_b", duration=5, callback=callback_b)
    await timer_manager.start_timer("keep_c", duration=5, callback=callback_c)

    # ACT
    timer_manager.cancel_timer("cancel_b")

    # ASSERT
    assert timer_manager.has_timer("keep_a")
    assert not timer_manager.has_timer("cancel_b")
    assert timer_manager.has_timer("keep_c")

    # Wait for expiry
    await asyncio.sleep(6.5)

    # Only non-cancelled timers should fire
    callback_a.assert_called_once()
    callback_b.assert_not_called()
    callback_c.assert_called_once()


# ============================================================================
# Category 3: Callback Execution (4 tests)
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_callback_receives_correct_context(timer_manager):
    """
    GIVEN: Timer with callback that accepts context
    WHEN: Timer expires
    THEN: Callback receives timer name and metadata

    Note: This tests callbacks that accept arguments vs no-arg callbacks.
    """
    # ARRANGE
    callback_data = {}

    def callback_with_context(timer_name: str):
        callback_data["timer_name"] = timer_name
        callback_data["executed"] = True

    # ACT
    await timer_manager.start_timer(
        name="context_timer",
        duration=2,
        callback=lambda: callback_with_context("context_timer")
    )

    await asyncio.sleep(3.5)

    # ASSERT
    assert callback_data.get("executed") is True
    assert callback_data.get("timer_name") == "context_timer"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_callback_exception_doesnt_crash_manager(timer_manager, caplog):
    """
    GIVEN: Timer with callback that raises exception
    WHEN: Timer expires and callback executes
    THEN: Exception is logged but TimerManager continues running
    """
    # ARRANGE
    def failing_callback():
        raise ValueError("Intentional test exception")

    good_callback = Mock()

    await timer_manager.start_timer(
        name="failing_timer",
        duration=2,
        callback=failing_callback
    )

    await timer_manager.start_timer(
        name="good_timer",
        duration=3,
        callback=good_callback
    )

    # ACT
    await asyncio.sleep(4.5)

    # ASSERT - Good callback still executed despite failing callback
    good_callback.assert_called_once()

    # ASSERT - Exception was logged
    assert "Intentional test exception" in caplog.text or "Timer callback error" in caplog.text


@pytest.mark.asyncio
@pytest.mark.unit
async def test_callback_executes_exactly_once(timer_manager):
    """
    GIVEN: Timer with 2-second duration
    WHEN: Timer expires
    THEN: Callback executes exactly once (no duplicates)
    """
    # ARRANGE
    execution_count = {"count": 0}

    def counting_callback():
        execution_count["count"] += 1

    await timer_manager.start_timer(
        name="once_timer",
        duration=2,
        callback=counting_callback
    )

    # ACT - Wait well beyond expiry
    await asyncio.sleep(5)

    # ASSERT
    assert execution_count["count"] == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_callback_supported(timer_manager):
    """
    GIVEN: Timer with async callback function
    WHEN: Timer expires
    THEN: Async callback executes successfully
    """
    # ARRANGE
    async_executed = {"value": False}

    async def async_callback():
        await asyncio.sleep(0.1)  # Simulate async work
        async_executed["value"] = True

    # ACT
    await timer_manager.start_timer(
        name="async_timer",
        duration=2,
        callback=async_callback
    )

    await asyncio.sleep(3.5)

    # ASSERT
    assert async_executed["value"] is True


# ============================================================================
# Category 4: Edge Cases (3 tests)
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_zero_duration_timer_executes_immediately(timer_manager, mock_callback):
    """
    GIVEN: Timer with duration=0
    WHEN: Timer is started
    THEN: Callback executes immediately on next check cycle
    """
    # ACT
    await timer_manager.start_timer(
        name="immediate_timer",
        duration=0,
        callback=mock_callback
    )

    # Wait one check cycle (1-second intervals)
    await asyncio.sleep(1.5)

    # ASSERT
    mock_callback.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_negative_duration_raises_error(timer_manager, mock_callback):
    """
    GIVEN: Timer with negative duration
    WHEN: start_timer is called
    THEN: ValueError is raised
    """
    # ACT & ASSERT
    with pytest.raises(ValueError, match="duration must be non-negative|duration cannot be negative"):
        await timer_manager.start_timer(
            name="invalid_timer",
            duration=-5,
            callback=mock_callback
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_timer_precision_within_tolerance(timer_manager, mock_callback):
    """
    GIVEN: Timer with 3-second duration
    WHEN: Timer expires
    THEN: Callback fires within 1-second tolerance (3-4 seconds)

    Per spec: Background task runs every 1 second, so timers may fire up to 1 second late.
    """
    # ARRANGE
    start_time = datetime.now()
    execution_time = {"timestamp": None}

    def time_tracking_callback():
        execution_time["timestamp"] = datetime.now()
        mock_callback()

    # ACT
    await timer_manager.start_timer(
        name="precision_timer",
        duration=3,
        callback=time_tracking_callback
    )

    await asyncio.sleep(5)  # Wait long enough

    # ASSERT
    mock_callback.assert_called_once()

    elapsed = (execution_time["timestamp"] - start_time).total_seconds()

    # Should fire between 3 and 4 seconds (1-second tolerance)
    assert 3.0 <= elapsed <= 4.5, f"Timer fired at {elapsed}s, expected 3-4s"


# ============================================================================
# Category 5: Background Task (2 tests)
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_check_timers_runs_every_second(timer_manager):
    """
    GIVEN: TimerManager is started
    WHEN: Background task is running
    THEN: check_timers() executes approximately every 1 second

    Note: Tests internal behavior by observing side effects (timer countdown).
    """
    # ARRANGE
    callback = Mock()

    await timer_manager.start_timer(
        name="background_test",
        duration=3,
        callback=callback
    )

    # ACT - Observe countdown over time
    t0_remaining = timer_manager.get_remaining_time("background_test")
    await asyncio.sleep(1.5)
    t1_remaining = timer_manager.get_remaining_time("background_test")
    await asyncio.sleep(1.5)
    t2_remaining = timer_manager.get_remaining_time("background_test")

    # ASSERT - Remaining time decreases roughly by 1-2 seconds per check
    assert t0_remaining > t1_remaining > t2_remaining

    # After 3 seconds, timer should have expired
    await asyncio.sleep(1.5)
    callback.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_check_timers_stops_on_shutdown(timer_manager, mock_callback):
    """
    GIVEN: TimerManager with active timers
    WHEN: stop() is called
    THEN: Background task stops and timers no longer execute
    """
    # ARRANGE
    await timer_manager.start_timer(
        name="shutdown_test",
        duration=3,
        callback=mock_callback
    )

    # ACT - Stop manager before timer expires
    await asyncio.sleep(1)
    await timer_manager.stop()

    # Wait beyond original expiry time
    await asyncio.sleep(3)

    # ASSERT - Callback should NOT fire after shutdown
    mock_callback.assert_not_called()


# ============================================================================
# Additional Edge Cases & Error Handling
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_remaining_time_nonexistent_timer_returns_zero(timer_manager):
    """
    GIVEN: Timer that does not exist
    WHEN: get_remaining_time is called
    THEN: Returns 0 (not an error)
    """
    # ACT
    remaining = timer_manager.get_remaining_time("nonexistent_timer")

    # ASSERT
    assert remaining == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_nonexistent_timer_no_error(timer_manager):
    """
    GIVEN: Timer that does not exist
    WHEN: cancel_timer is called
    THEN: No error raised (idempotent operation)
    """
    # ACT & ASSERT - Should not raise
    timer_manager.cancel_timer("nonexistent_timer")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_duplicate_timer_name_overwrites_previous(timer_manager):
    """
    GIVEN: Timer with name 'duplicate' exists
    WHEN: New timer with same name is started
    THEN: Previous timer is replaced, first callback never fires
    """
    # ARRANGE
    first_callback = Mock()
    second_callback = Mock()

    await timer_manager.start_timer(
        name="duplicate",
        duration=5,
        callback=first_callback
    )

    await asyncio.sleep(1)

    # ACT - Start new timer with same name
    await timer_manager.start_timer(
        name="duplicate",
        duration=3,
        callback=second_callback
    )

    # Wait for second timer to expire
    await asyncio.sleep(4.5)

    # ASSERT
    first_callback.assert_not_called()  # Overwritten, never fired
    second_callback.assert_called_once()  # Only the new one fired


@pytest.mark.asyncio
@pytest.mark.unit
async def test_has_timer_returns_false_for_nonexistent(timer_manager):
    """
    GIVEN: Timer that does not exist
    WHEN: has_timer is called
    THEN: Returns False
    """
    # ACT
    exists = timer_manager.has_timer("nonexistent")

    # ASSERT
    assert exists is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_start_timer_without_callback_raises_error(timer_manager):
    """
    GIVEN: start_timer called without callback parameter
    WHEN: Timer is started
    THEN: TypeError or ValueError is raised
    """
    # ACT & ASSERT
    with pytest.raises((TypeError, ValueError)):
        await timer_manager.start_timer(
            name="no_callback_timer",
            duration=5,
            callback=None
        )
