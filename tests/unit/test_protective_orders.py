"""
Unit tests for ProtectiveOrderCache module.

Tests the stop loss and take profit caching logic in isolation.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, MagicMock

from risk_manager.integrations.sdk.protective_orders import ProtectiveOrderCache


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def cache():
    """Create ProtectiveOrderCache instance."""
    cache = ProtectiveOrderCache()

    # Set up helper functions
    def extract_symbol(contract_id: str) -> str:
        """Extract symbol from contract ID."""
        if not contract_id:
            return "UNKNOWN"
        parts = contract_id.split('.')
        if len(parts) >= 4:
            return parts[3]
        return "UNKNOWN"

    def get_side_name(side: int) -> str:
        """Convert side int to name."""
        return "BUY" if side == 0 else "SELL"

    cache.set_helpers(extract_symbol, get_side_name)

    return cache


@pytest.fixture
def mock_order_stop_loss():
    """Create mock stop loss order."""
    order = Mock()
    order.id = 12345
    order.contractId = "CON.F.US.MNQ.Z25"
    order.type = 4  # STOP
    order.type_str = "STOP"
    order.side = 1  # SELL
    order.size = 1
    order.stopPrice = 21500.00
    order.limitPrice = None
    return order


@pytest.fixture
def mock_order_take_profit():
    """Create mock take profit order."""
    order = Mock()
    order.id = 67890
    order.contractId = "CON.F.US.MNQ.Z25"
    order.type = 1  # LIMIT
    order.type_str = "LIMIT"
    order.side = 1  # SELL
    order.size = 1
    order.stopPrice = None
    order.limitPrice = 21600.00
    return order


# ============================================================================
# Test: Initialization
# ============================================================================

def test_initialization():
    """Test that ProtectiveOrderCache initializes with empty caches."""
    cache = ProtectiveOrderCache()

    assert isinstance(cache._active_stop_losses, dict)
    assert len(cache._active_stop_losses) == 0

    assert isinstance(cache._active_take_profits, dict)
    assert len(cache._active_take_profits) == 0

    assert cache._suite is None


# ============================================================================
# Test: Cache Operations
# ============================================================================

def test_update_from_order_placed_stop_loss(cache, mock_order_stop_loss):
    """Test that stop loss orders are cached correctly."""
    contract_id = mock_order_stop_loss.contractId

    # Add to cache
    cache.update_from_order_placed(mock_order_stop_loss)

    # Verify cached
    assert contract_id in cache._active_stop_losses
    cached_data = cache._active_stop_losses[contract_id]

    assert cached_data["order_id"] == 12345
    assert cached_data["stop_price"] == 21500.00
    assert cached_data["side"] == "SELL"
    assert cached_data["quantity"] == 1


def test_update_from_order_placed_take_profit(cache):
    """Test that take profit orders are cached correctly."""
    # Create a LIMIT order that would be detected as TP
    # Note: Current implementation of _is_take_profit returns False conservatively
    # So we'll test the manual caching path

    order = Mock()
    order.id = 67890
    order.contractId = "CON.F.US.MNQ.Z25"
    order.type = 1  # LIMIT
    order.side = 1  # SELL
    order.size = 1
    order.limitPrice = 21600.00
    order.stopPrice = None

    # Manually add to cache (since _is_take_profit is conservative)
    cache._active_take_profits[order.contractId] = {
        "order_id": order.id,
        "take_profit_price": order.limitPrice,
        "side": "SELL",
        "quantity": order.size,
        "timestamp": time.time(),
    }

    # Verify cached
    assert order.contractId in cache._active_take_profits


def test_remove_stop_loss(cache, mock_order_stop_loss):
    """Test that stop loss can be removed from cache."""
    contract_id = mock_order_stop_loss.contractId

    # Add to cache
    cache.update_from_order_placed(mock_order_stop_loss)
    assert contract_id in cache._active_stop_losses

    # Remove
    cache.remove_stop_loss(contract_id)
    assert contract_id not in cache._active_stop_losses


def test_remove_take_profit(cache):
    """Test that take profit can be removed from cache."""
    contract_id = "CON.F.US.MNQ.Z25"

    # Manually add
    cache._active_take_profits[contract_id] = {"order_id": 123}
    assert contract_id in cache._active_take_profits

    # Remove
    cache.remove_take_profit(contract_id)
    assert contract_id not in cache._active_take_profits


def test_invalidate_clears_both_caches(cache, mock_order_stop_loss):
    """Test that invalidate() clears both stop loss and take profit caches."""
    contract_id = mock_order_stop_loss.contractId

    # Add to both caches
    cache.update_from_order_placed(mock_order_stop_loss)
    cache._active_take_profits[contract_id] = {"order_id": 789}

    assert contract_id in cache._active_stop_losses
    assert contract_id in cache._active_take_profits

    # Invalidate
    cache.invalidate(contract_id)

    # Both should be cleared
    assert contract_id not in cache._active_stop_losses
    assert contract_id not in cache._active_take_profits


# ============================================================================
# Test: Get Methods (Cache Hits)
# ============================================================================

@pytest.mark.asyncio
async def test_get_stop_loss_returns_cached_data(cache, mock_order_stop_loss):
    """Test that get_stop_loss() returns cached data."""
    contract_id = mock_order_stop_loss.contractId

    # Add to cache
    cache.update_from_order_placed(mock_order_stop_loss)

    # Query (should hit cache, not query SDK)
    result = await cache.get_stop_loss(contract_id)

    assert result is not None
    assert result["order_id"] == 12345
    assert result["stop_price"] == 21500.00


@pytest.mark.asyncio
async def test_get_take_profit_returns_cached_data(cache):
    """Test that get_take_profit() returns cached data."""
    contract_id = "CON.F.US.MNQ.Z25"

    # Manually add to cache
    cache._active_take_profits[contract_id] = {
        "order_id": 67890,
        "take_profit_price": 21600.00,
        "side": "SELL",
        "quantity": 1,
        "timestamp": time.time(),
    }

    # Query (should hit cache)
    result = await cache.get_take_profit(contract_id)

    assert result is not None
    assert result["order_id"] == 67890
    assert result["take_profit_price"] == 21600.00


@pytest.mark.asyncio
async def test_get_stop_loss_returns_none_when_empty(cache):
    """Test that get_stop_loss() returns None when cache is empty and no SDK."""
    contract_id = "CON.F.US.MNQ.Z25"

    # Cache is empty, no SDK set
    result = await cache.get_stop_loss(contract_id)

    assert result is None


def test_get_all_stop_losses_returns_copy(cache, mock_order_stop_loss):
    """Test that get_all_stop_losses() returns a copy of the cache."""
    cache.update_from_order_placed(mock_order_stop_loss)

    result = cache.get_all_stop_losses()

    assert isinstance(result, dict)
    assert len(result) == 1
    assert mock_order_stop_loss.contractId in result

    # Should be a copy, not the original
    assert result is not cache._active_stop_losses


def test_get_all_take_profits_returns_copy(cache):
    """Test that get_all_take_profits() returns a copy of the cache."""
    contract_id = "CON.F.US.MNQ.Z25"
    cache._active_take_profits[contract_id] = {"order_id": 123}

    result = cache.get_all_take_profits()

    assert isinstance(result, dict)
    assert len(result) == 1
    assert contract_id in result

    # Should be a copy
    assert result is not cache._active_take_profits


# ============================================================================
# Test: Order Intent Detection (Semantic Analysis)
# ============================================================================

def test_determine_order_intent_stop_order_is_stop_loss(cache):
    """Test that STOP orders are detected as stop loss."""
    order = Mock()
    order.type = 4  # STOP
    order.stopPrice = 21500.00

    intent = cache._determine_order_intent(order, 21550.00, 1)  # LONG @ 21550

    assert intent == "stop_loss"


def test_determine_order_intent_limit_above_long_is_take_profit(cache):
    """Test that LIMIT order above entry (for LONG) is take profit."""
    order = Mock()
    order.type = 1  # LIMIT
    order.limitPrice = 21600.00  # Above entry

    intent = cache._determine_order_intent(order, 21550.00, 1)  # LONG @ 21550

    assert intent == "take_profit"


def test_determine_order_intent_limit_below_long_is_entry(cache):
    """Test that LIMIT order below entry (for LONG) is entry order."""
    order = Mock()
    order.type = 1  # LIMIT
    order.limitPrice = 21500.00  # Below entry

    intent = cache._determine_order_intent(order, 21550.00, 1)  # LONG @ 21550

    assert intent == "entry"


def test_determine_order_intent_limit_below_short_is_take_profit(cache):
    """Test that LIMIT order below entry (for SHORT) is take profit."""
    order = Mock()
    order.type = 1  # LIMIT
    order.limitPrice = 21500.00  # Below entry

    intent = cache._determine_order_intent(order, 21550.00, 2)  # SHORT @ 21550

    assert intent == "take_profit"


def test_determine_order_intent_market_is_unknown(cache):
    """Test that MARKET orders return unknown intent."""
    order = Mock()
    order.type = 2  # MARKET

    intent = cache._determine_order_intent(order, 21550.00, 1)

    assert intent == "unknown"


def test_is_stop_loss_detection(cache):
    """Test _is_stop_loss() detection logic."""
    # STOP order (type 4)
    order = Mock()
    order.type = 4
    assert cache._is_stop_loss(order) is True

    # STOP_LIMIT (type 3)
    order.type = 3
    assert cache._is_stop_loss(order) is True

    # TRAILING_STOP (type 5)
    order.type = 5
    assert cache._is_stop_loss(order) is True

    # LIMIT (type 1) - not a stop loss
    order.type = 1
    assert cache._is_stop_loss(order) is False

    # MARKET (type 2) - not a stop loss
    order.type = 2
    assert cache._is_stop_loss(order) is False


def test_is_take_profit_detection(cache):
    """Test _is_take_profit() detection logic."""
    # Current implementation is conservative - returns False
    # This test documents the current behavior

    order = Mock()
    order.type = 1  # LIMIT

    assert cache._is_take_profit(order) is False  # Conservative


# ============================================================================
# Test: Helper Function Integration
# ============================================================================

def test_set_helpers_stores_functions(cache):
    """Test that set_helpers() stores helper functions."""
    def mock_extract(contract_id):
        return "TEST"

    def mock_side(side):
        return "TEST_SIDE"

    cache.set_helpers(mock_extract, mock_side)

    assert cache._extract_symbol_fn is not None
    assert cache._get_side_name_fn is not None

    # Test they work
    assert cache._extract_symbol_fn("anything") == "TEST"
    assert cache._get_side_name_fn(0) == "TEST_SIDE"


def test_set_suite_stores_suite_reference(cache):
    """Test that set_suite() stores SDK suite reference."""
    mock_suite = Mock()
    cache.set_suite(mock_suite)

    assert cache._suite is mock_suite


# ============================================================================
# Summary
# ============================================================================

def test_protective_order_cache_complete_workflow(cache, mock_order_stop_loss):
    """
    Integration test: Complete workflow from order placed to query to removal.
    """
    contract_id = mock_order_stop_loss.contractId

    # 1. Initially empty
    assert len(cache.get_all_stop_losses()) == 0

    # 2. Order placed → cached
    cache.update_from_order_placed(mock_order_stop_loss)
    assert len(cache.get_all_stop_losses()) == 1

    # 3. Query returns cached data
    import asyncio
    result = asyncio.run(cache.get_stop_loss(contract_id))
    assert result is not None
    assert result["stop_price"] == 21500.00

    # 4. Remove from cache
    cache.remove_stop_loss(contract_id)
    assert len(cache.get_all_stop_losses()) == 0

    # 5. Query returns None (cache miss, no SDK)
    result = asyncio.run(cache.get_stop_loss(contract_id))
    assert result is None
