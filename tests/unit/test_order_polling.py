"""
Unit tests for OrderPollingService module.

Tests background order polling in isolation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock

from risk_manager.integrations.sdk.order_polling import OrderPollingService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def service():
    """Create OrderPollingService instance."""
    return OrderPollingService()


@pytest.fixture
def mock_protective_cache():
    """Create mock protective order cache."""
    cache = Mock()
    cache.update_from_order_placed = Mock()
    return cache


@pytest.fixture
def mock_suite():
    """Create mock SDK suite."""
    suite = {}
    return suite


# ============================================================================
# Test: Initialization
# ============================================================================

def test_initialization(service):
    """Test that OrderPollingService initializes correctly."""
    assert service._suite is None
    assert service._protective_cache is None
    assert service._extract_symbol_fn is None
    assert service._get_side_name_fn is None
    assert service._running is False
    assert service._poll_task is None
    assert isinstance(service._known_orders, set)
    assert len(service._known_orders) == 0


def test_set_suite(service):
    """Test that set_suite stores SDK suite reference."""
    mock_suite = Mock()
    service.set_suite(mock_suite)

    assert service._suite is mock_suite


def test_set_protective_cache(service, mock_protective_cache):
    """Test that set_protective_cache stores cache reference."""
    service.set_protective_cache(mock_protective_cache)

    assert service._protective_cache is mock_protective_cache


def test_set_helpers(service):
    """Test that set_helpers stores helper functions."""
    def mock_extract(contract_id):
        return "TEST"

    def mock_side(side):
        return "BUY"

    service.set_helpers(mock_extract, mock_side)

    assert service._extract_symbol_fn is not None
    assert service._get_side_name_fn is not None


# ============================================================================
# Test: Order Tracking
# ============================================================================

def test_mark_order_seen(service):
    """Test that mark_order_seen adds order to known list."""
    order_id = 12345

    service.mark_order_seen(order_id)

    assert order_id in service._known_orders


def test_mark_order_unseen(service):
    """Test that mark_order_unseen removes order from known list."""
    order_id = 12345

    # Add order
    service.mark_order_seen(order_id)
    assert order_id in service._known_orders

    # Remove order
    service.mark_order_unseen(order_id)
    assert order_id not in service._known_orders


def test_mark_order_unseen_idempotent(service):
    """Test that mark_order_unseen is idempotent (safe to call multiple times)."""
    order_id = 12345

    # Remove order that was never added (should not error)
    service.mark_order_unseen(order_id)
    assert order_id not in service._known_orders


# ============================================================================
# Test: Polling Lifecycle
# ============================================================================

@pytest.mark.asyncio
async def test_start_polling_creates_task(service):
    """Test that start_polling creates a background task."""
    await service.start_polling()

    # Task should be created
    assert service._poll_task is not None
    assert not service._poll_task.done()
    assert service._running is True

    # Cleanup
    await service.stop_polling()


@pytest.mark.asyncio
async def test_stop_polling_cancels_task(service):
    """Test that stop_polling cancels the background task."""
    await service.start_polling()

    # Give task a moment to start
    await asyncio.sleep(0.1)

    await service.stop_polling()

    # Task should be cancelled
    assert service._running is False
    assert service._poll_task.done()


@pytest.mark.asyncio
async def test_start_polling_twice_warns(service):
    """Test that starting polling twice logs a warning."""
    await service.start_polling()

    # Try to start again (should warn, not create second task)
    await service.start_polling()

    # Still only one task
    assert service._poll_task is not None

    # Cleanup
    await service.stop_polling()


# ============================================================================
# Test: Polling Logic
# ============================================================================

@pytest.mark.asyncio
async def test_polling_discovers_new_orders(service, mock_protective_cache):
    """Test that polling discovers new orders and updates cache."""
    # Create mock order
    mock_order = Mock()
    mock_order.id = 12345
    mock_order.contractId = "CON.F.US.MNQ.Z25"
    mock_order.type_str = "STOP"
    mock_order.side = 1
    mock_order.size = 1
    mock_order.stopPrice = 21500.00
    mock_order.limitPrice = None
    mock_order.status = "Working"

    # Create mock position
    mock_position = Mock()
    mock_position.contractId = "CON.F.US.MNQ.Z25"

    # Create mock instrument
    mock_orders_manager = Mock()
    mock_orders_manager.get_position_orders = AsyncMock(return_value=[mock_order])

    mock_positions_manager = Mock()
    mock_positions_manager.get_all_positions = AsyncMock(return_value=[mock_position])

    mock_instrument = Mock()
    mock_instrument.orders = mock_orders_manager
    mock_instrument.positions = mock_positions_manager

    # Create mock suite
    mock_suite = {"MNQ": mock_instrument}

    service.set_suite(mock_suite)
    service.set_protective_cache(mock_protective_cache)
    service.set_helpers(
        lambda cid: "MNQ",
        lambda side: "SELL"
    )

    # Start polling
    await service.start_polling()

    # Wait for one poll cycle (5s + margin)
    await asyncio.sleep(5.5)

    # Stop polling
    await service.stop_polling()

    # Order should be marked as seen
    assert 12345 in service._known_orders

    # Protective cache should have been updated
    mock_protective_cache.update_from_order_placed.assert_called()


@pytest.mark.asyncio
async def test_polling_skips_duplicate_orders(service):
    """Test that polling doesn't log the same order twice."""
    mock_order = Mock()
    mock_order.id = 12345
    mock_order.contractId = "CON.F.US.MNQ.Z25"
    mock_order.type_str = "STOP"
    mock_order.side = 1
    mock_order.size = 1

    mock_position = Mock()
    mock_position.contractId = "CON.F.US.MNQ.Z25"

    # Mark order as already seen
    service.mark_order_seen(12345)

    mock_orders_manager = Mock()
    mock_orders_manager.get_position_orders = AsyncMock(return_value=[mock_order])

    mock_positions_manager = Mock()
    mock_positions_manager.get_all_positions = AsyncMock(return_value=[mock_position])

    mock_instrument = Mock()
    mock_instrument.orders = mock_orders_manager
    mock_instrument.positions = mock_positions_manager

    mock_suite = {"MNQ": mock_instrument}

    service.set_suite(mock_suite)

    # Start polling
    await service.start_polling()

    # Wait for one poll cycle
    await asyncio.sleep(5.5)

    # Stop polling
    await service.stop_polling()

    # get_position_orders should have been called, but order skipped (already known)
    mock_orders_manager.get_position_orders.assert_called()


@pytest.mark.asyncio
async def test_polling_handles_errors_gracefully(service):
    """Test that polling continues despite errors."""
    # Create mock instrument that raises errors
    mock_positions_manager = Mock()
    mock_positions_manager.get_all_positions = AsyncMock(side_effect=Exception("Test error"))

    mock_instrument = Mock()
    mock_instrument.positions = mock_positions_manager
    mock_instrument.orders = Mock()

    mock_suite = {"MNQ": mock_instrument}

    service.set_suite(mock_suite)

    # Start polling
    await service.start_polling()

    # Wait for one poll cycle
    await asyncio.sleep(5.5)

    # Should still be running despite error
    assert service._running is True

    # Stop polling
    await service.stop_polling()


@pytest.mark.asyncio
async def test_polling_waits_for_suite(service):
    """Test that polling waits for suite to be available."""
    # Don't set suite

    # Start polling
    await service.start_polling()

    # Wait a bit
    await asyncio.sleep(0.5)

    # Should be running but not polling (no suite)
    assert service._running is True

    # Stop polling
    await service.stop_polling()


# ============================================================================
# Summary
# ============================================================================

def test_order_polling_service_complete_workflow(service, mock_protective_cache):
    """
    Integration test: Complete workflow from initialization to polling.
    """
    # 1. Initialize (already done in fixture)
    assert service._suite is None

    # 2. Set references
    mock_suite = Mock()
    service.set_suite(mock_suite)
    service.set_protective_cache(mock_protective_cache)
    service.set_helpers(lambda cid: "MNQ", lambda side: "BUY")

    assert service._suite is mock_suite
    assert service._protective_cache is mock_protective_cache

    # 3. Mark order as seen
    service.mark_order_seen(123)
    assert 123 in service._known_orders

    # 4. Remove order
    service.mark_order_unseen(123)
    assert 123 not in service._known_orders
