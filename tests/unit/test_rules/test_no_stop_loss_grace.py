"""
RULE-008: No Stop-Loss Grace - Unit Tests

Tests for the no stop-loss grace period enforcement rule.
This rule starts a grace period when a position opens and closes
the position if no stop-loss order is placed within the grace period.

Reference: docs/specifications/unified/rules/RULE-008-no-stop-loss-grace.md
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.no_stop_loss_grace import NoStopLossGraceRule
from risk_manager.state.timer_manager import TimerManager


@pytest.fixture
def timer_manager():
    """Create timer manager for tests."""
    manager = TimerManager()
    return manager


@pytest.fixture
async def started_timer_manager(timer_manager):
    """Create and start timer manager."""
    await timer_manager.start()
    yield timer_manager
    await timer_manager.stop()


@pytest.fixture
def mock_engine():
    """Create mock risk engine with enforcement executor."""
    engine = MagicMock()
    engine.enforcement_executor = MagicMock()
    engine.enforcement_executor.close_position = AsyncMock(return_value={"success": True})
    return engine


@pytest.fixture
def rule(started_timer_manager):
    """Create NoStopLossGraceRule with default config."""
    return NoStopLossGraceRule(
        grace_period_seconds=10,
        enforcement="close_position",
        timer_manager=started_timer_manager,
    )


# ============================================================================
# Configuration Tests
# ============================================================================


def test_rule_initialization(started_timer_manager):
    """Test rule initializes with correct configuration."""
    rule = NoStopLossGraceRule(
        grace_period_seconds=15,
        enforcement="close_position",
        timer_manager=started_timer_manager,
    )

    assert rule.grace_period_seconds == 15
    assert rule.enforcement == "close_position"
    assert rule.timer_manager == started_timer_manager
    assert rule.enabled is True


def test_rule_can_be_disabled(started_timer_manager):
    """Test rule can be disabled."""
    rule = NoStopLossGraceRule(
        grace_period_seconds=10,
        enforcement="close_position",
        timer_manager=started_timer_manager,
        enabled=False,
    )

    assert rule.enabled is False


# ============================================================================
# Position Opened Event Tests
# ============================================================================


@pytest.mark.asyncio
async def test_position_opened_starts_grace_period_timer(rule, mock_engine):
    """Test that POSITION_OPENED event starts a grace period timer."""
    # Create position opened event
    event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
            "average_price": 18500.0,
        },
    )

    # Evaluate the rule
    violation = await rule.evaluate(event, mock_engine)

    # No immediate violation - grace period starts
    assert violation is None

    # Check that timer was started
    timer_name = "no_stop_loss_grace_CON.F.US.MNQ.Z25"
    assert rule.timer_manager.has_timer(timer_name)

    # Check timer duration is correct
    remaining = rule.timer_manager.get_remaining_time(timer_name)
    assert 9 <= remaining <= 10  # Allow 1 second variance


@pytest.mark.asyncio
async def test_position_opened_with_zero_size_ignored(rule, mock_engine):
    """Test that position opened with size 0 is ignored."""
    event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 0,
        },
    )

    violation = await rule.evaluate(event, mock_engine)

    assert violation is None
    assert not rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")


@pytest.mark.asyncio
async def test_position_opened_missing_contract_id_ignored(rule, mock_engine):
    """Test that position event without contract_id is ignored."""
    event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "size": 2,
        },
    )

    violation = await rule.evaluate(event, mock_engine)

    assert violation is None


# ============================================================================
# Stop-Loss Order Placed Tests
# ============================================================================


@pytest.mark.asyncio
async def test_stop_order_placed_cancels_grace_period(rule, mock_engine):
    """Test that placing a stop-loss order cancels the grace period timer."""
    # Step 1: Open position (start grace period)
    position_event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
        },
    )

    await rule.evaluate(position_event, mock_engine)
    timer_name = "no_stop_loss_grace_CON.F.US.MNQ.Z25"
    assert rule.timer_manager.has_timer(timer_name)

    # Step 2: Place stop-loss order (type=3, stopPrice present)
    stop_order_event = RiskEvent(
        event_type=EventType.ORDER_PLACED,
        data={
            "contract_id": "CON.F.US.MNQ.Z25",
            "symbol": "MNQ",
            "type": 3,  # STOP order
            "stopPrice": 18450.0,
            "size": 2,
        },
    )

    violation = await rule.evaluate(stop_order_event, mock_engine)

    # No violation - stop-loss placed correctly
    assert violation is None

    # Grace period timer should be cancelled
    assert not rule.timer_manager.has_timer(timer_name)


@pytest.mark.asyncio
async def test_stop_order_without_stop_price_ignored(rule, mock_engine):
    """Test that order with type=3 but no stopPrice is ignored."""
    # Open position first
    position_event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
        },
    )
    await rule.evaluate(position_event, mock_engine)

    # Place "stop" order without stopPrice (should be ignored)
    order_event = RiskEvent(
        event_type=EventType.ORDER_PLACED,
        data={
            "contract_id": "CON.F.US.MNQ.Z25",
            "symbol": "MNQ",
            "type": 3,
            # No stopPrice!
            "size": 2,
        },
    )

    await rule.evaluate(order_event, mock_engine)

    # Timer should still exist (stop-loss not properly placed)
    assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")


@pytest.mark.asyncio
async def test_non_stop_order_ignored(rule, mock_engine):
    """Test that non-stop orders (market, limit) don't cancel grace period."""
    # Open position
    position_event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
        },
    )
    await rule.evaluate(position_event, mock_engine)

    # Place limit order (type=1)
    limit_order_event = RiskEvent(
        event_type=EventType.ORDER_PLACED,
        data={
            "contract_id": "CON.F.US.MNQ.Z25",
            "symbol": "MNQ",
            "type": 1,  # LIMIT order
            "limitPrice": 18600.0,
            "size": 2,
        },
    )

    await rule.evaluate(limit_order_event, mock_engine)

    # Timer should still exist
    assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")


@pytest.mark.asyncio
async def test_stop_order_for_different_position_ignored(rule, mock_engine):
    """Test that stop order for different contract doesn't cancel grace period."""
    # Open position for MNQ
    position_event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
        },
    )
    await rule.evaluate(position_event, mock_engine)

    # Place stop order for ES (different contract)
    stop_order_event = RiskEvent(
        event_type=EventType.ORDER_PLACED,
        data={
            "contract_id": "CON.F.US.ES.H25",  # Different contract!
            "symbol": "ES",
            "type": 3,
            "stopPrice": 5180.0,
            "size": 1,
        },
    )

    await rule.evaluate(stop_order_event, mock_engine)

    # Timer for MNQ should still exist
    assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")


# ============================================================================
# Grace Period Expiry Tests
# ============================================================================


@pytest.mark.asyncio
async def test_grace_period_expiry_closes_position(rule, mock_engine):
    """Test that grace period expiry triggers position close enforcement."""
    # Open position
    position_event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
            "average_price": 18500.0,
        },
    )

    await rule.evaluate(position_event, mock_engine)

    # Wait for grace period to expire (use very short duration for testing)
    # We'll manually trigger the timer check for faster testing
    await asyncio.sleep(0.1)  # Small delay to ensure timer is set

    # Manually trigger timer expiry callback
    timer_name = "no_stop_loss_grace_CON.F.US.MNQ.Z25"
    timer = rule.timer_manager.timers.get(timer_name)
    assert timer is not None

    # Execute the callback manually
    callback = timer["callback"]
    await callback()

    # Verify enforcement was triggered
    mock_engine.enforcement_executor.close_position.assert_called_once_with(
        "MNQ", "CON.F.US.MNQ.Z25"
    )


@pytest.mark.asyncio
async def test_grace_period_expiry_with_actual_timer(started_timer_manager, mock_engine):
    """Test grace period expiry with actual timer countdown."""
    # Create rule with very short grace period for testing
    rule = NoStopLossGraceRule(
        grace_period_seconds=1,  # 1 second for fast test
        enforcement="close_position",
        timer_manager=started_timer_manager,
    )

    # Track if callback was executed
    callback_executed = False
    original_close = mock_engine.enforcement_executor.close_position

    async def tracked_close(*args, **kwargs):
        nonlocal callback_executed
        callback_executed = True
        return await original_close(*args, **kwargs)

    mock_engine.enforcement_executor.close_position = tracked_close

    # Open position
    position_event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
        },
    )

    await rule.evaluate(position_event, mock_engine)

    # Wait for timer to expire (1 second + buffer for background task)
    await asyncio.sleep(2.5)

    # Callback should have been executed
    assert callback_executed


# ============================================================================
# Position Closed Event Tests
# ============================================================================


@pytest.mark.asyncio
async def test_position_closed_cancels_grace_period(rule, mock_engine):
    """Test that closing a position cancels the grace period timer."""
    # Open position
    position_event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
        },
    )
    await rule.evaluate(position_event, mock_engine)

    timer_name = "no_stop_loss_grace_CON.F.US.MNQ.Z25"
    assert rule.timer_manager.has_timer(timer_name)

    # Close position
    close_event = RiskEvent(
        event_type=EventType.POSITION_CLOSED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 0,
        },
    )

    violation = await rule.evaluate(close_event, mock_engine)

    # No violation
    assert violation is None

    # Timer should be cancelled
    assert not rule.timer_manager.has_timer(timer_name)


# ============================================================================
# Multiple Positions Tests
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_positions_tracked_separately(rule, mock_engine):
    """Test that multiple positions have separate grace period timers."""
    # Open position 1 - MNQ
    event1 = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
        },
    )
    await rule.evaluate(event1, mock_engine)

    # Open position 2 - ES
    event2 = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "ES",
            "contract_id": "CON.F.US.ES.H25",
            "size": 1,
        },
    )
    await rule.evaluate(event2, mock_engine)

    # Both timers should exist
    assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")
    assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.ES.H25")

    # Place stop for MNQ only
    stop_event = RiskEvent(
        event_type=EventType.ORDER_PLACED,
        data={
            "contract_id": "CON.F.US.MNQ.Z25",
            "symbol": "MNQ",
            "type": 3,
            "stopPrice": 18450.0,
            "size": 2,
        },
    )
    await rule.evaluate(stop_event, mock_engine)

    # MNQ timer cancelled, ES timer still active
    assert not rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")
    assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.ES.H25")


# ============================================================================
# Rule Disabled Tests
# ============================================================================


@pytest.mark.asyncio
async def test_rule_disabled_no_timers_started(started_timer_manager, mock_engine):
    """Test that disabled rule doesn't start timers."""
    rule = NoStopLossGraceRule(
        grace_period_seconds=10,
        enforcement="close_position",
        timer_manager=started_timer_manager,
        enabled=False,
    )

    event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
        },
    )

    violation = await rule.evaluate(event, mock_engine)

    assert violation is None
    assert not started_timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")


# ============================================================================
# Status Tests
# ============================================================================


def test_get_status(rule):
    """Test get_status returns correct rule information."""
    status = rule.get_status()

    assert status["rule"] == "NoStopLossGrace"
    assert status["enabled"] is True
    assert status["grace_period_seconds"] == 10
    assert status["enforcement"] == "close_position"
    assert "active_timers" in status


# ============================================================================
# Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_position_reopened_restarts_timer(rule, mock_engine):
    """Test that reopening a position restarts the grace period timer."""
    contract_id = "CON.F.US.MNQ.Z25"
    timer_name = f"no_stop_loss_grace_{contract_id}"

    # Open position
    event1 = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={"symbol": "MNQ", "contract_id": contract_id, "size": 2},
    )
    await rule.evaluate(event1, mock_engine)
    assert rule.timer_manager.has_timer(timer_name)

    # Close position
    event2 = RiskEvent(
        event_type=EventType.POSITION_CLOSED,
        data={"symbol": "MNQ", "contract_id": contract_id, "size": 0},
    )
    await rule.evaluate(event2, mock_engine)
    assert not rule.timer_manager.has_timer(timer_name)

    # Reopen position (should restart timer)
    event3 = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={"symbol": "MNQ", "contract_id": contract_id, "size": 1},
    )
    await rule.evaluate(event3, mock_engine)
    assert rule.timer_manager.has_timer(timer_name)


@pytest.mark.asyncio
async def test_enforcement_failure_logged(rule, mock_engine):
    """Test that enforcement failures are handled gracefully."""
    # Make close_position fail
    mock_engine.enforcement_executor.close_position = AsyncMock(
        return_value={"success": False, "error": "Test failure"}
    )

    # Open position
    position_event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={
            "symbol": "MNQ",
            "contract_id": "CON.F.US.MNQ.Z25",
            "size": 2,
        },
    )
    await rule.evaluate(position_event, mock_engine)

    # Trigger callback manually
    timer_name = "no_stop_loss_grace_CON.F.US.MNQ.Z25"
    timer = rule.timer_manager.timers.get(timer_name)
    callback = timer["callback"]
    await callback()

    # Should attempt enforcement despite failure
    mock_engine.enforcement_executor.close_position.assert_called_once()


@pytest.mark.asyncio
async def test_ignore_non_position_and_order_events(rule, mock_engine):
    """Test that rule ignores irrelevant event types."""
    # Test with PNL_UPDATED event
    event = RiskEvent(
        event_type=EventType.PNL_UPDATED,
        data={"pnl": 100.0},
    )

    violation = await rule.evaluate(event, mock_engine)
    assert violation is None

    # Test with SYSTEM_STARTED event
    event = RiskEvent(
        event_type=EventType.SYSTEM_STARTED,
        data={},
    )

    violation = await rule.evaluate(event, mock_engine)
    assert violation is None
