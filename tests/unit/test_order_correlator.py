"""
Unit tests for OrderCorrelator module.

Tests fill recording, correlation, and TTL-based cleanup.
"""

import pytest
import time
from risk_manager.integrations.sdk.order_correlator import OrderCorrelator


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def correlator():
    """Create OrderCorrelator instance."""
    return OrderCorrelator(ttl=2.0)


@pytest.fixture
def short_ttl_correlator():
    """Create OrderCorrelator with short TTL for testing expiration."""
    return OrderCorrelator(ttl=0.1)  # 100ms TTL


# ============================================================================
# Test: Initialization
# ============================================================================

def test_initialization(correlator):
    """Test that OrderCorrelator initializes correctly."""
    assert correlator.get_active_fills_count() == 0
    assert correlator.get_active_contracts() == []


def test_initialization_with_custom_ttl():
    """Test initialization with custom TTL."""
    correlator = OrderCorrelator(ttl=5.0)
    assert correlator._ttl == 5.0


# ============================================================================
# Test: Recording Fills
# ============================================================================

def test_record_fill_stop_loss(correlator):
    """Test recording a stop loss fill."""
    correlator.record_fill(
        contract_id="CON.F.US.MNQ.Z25",
        fill_type="stop_loss",
        fill_price=21500.00,
        side="SELL",
        order_id=12345
    )

    assert correlator.get_active_fills_count() == 1
    assert "CON.F.US.MNQ.Z25" in correlator.get_active_contracts()


def test_record_fill_take_profit(correlator):
    """Test recording a take profit fill."""
    correlator.record_fill(
        contract_id="CON.F.US.ES.H25",
        fill_type="take_profit",
        fill_price=5200.00,
        side="BUY",
        order_id=67890
    )

    assert correlator.get_active_fills_count() == 1
    fill_type = correlator.get_fill_type("CON.F.US.ES.H25")
    assert fill_type == "take_profit"


def test_record_fill_manual(correlator):
    """Test recording a manual exit fill."""
    correlator.record_fill(
        contract_id="CON.F.US.MNQ.Z25",
        fill_type="manual",
        fill_price=21550.00,
        side="SELL",
        order_id=11111
    )

    fill_type = correlator.get_fill_type("CON.F.US.MNQ.Z25")
    assert fill_type == "manual"


def test_record_multiple_fills(correlator):
    """Test recording multiple fills for different contracts."""
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 1
    )
    correlator.record_fill(
        "CON.F.US.ES.H25", "take_profit", 5200.00, "BUY", 2
    )

    assert correlator.get_active_fills_count() == 2


def test_record_fill_overwrites_previous(correlator):
    """Test that recording a new fill for same contract overwrites previous."""
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 1
    )
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "manual", 21550.00, "SELL", 2
    )

    # Should only have 1 fill (second overwrites first)
    assert correlator.get_active_fills_count() == 1
    assert correlator.get_fill_type("CON.F.US.MNQ.Z25") == "manual"
    assert correlator.get_fill_price("CON.F.US.MNQ.Z25") == 21550.00


# ============================================================================
# Test: Retrieving Fill Data
# ============================================================================

def test_get_fill_type_returns_correct_type(correlator):
    """Test getting fill type for recorded fill."""
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 12345
    )

    fill_type = correlator.get_fill_type("CON.F.US.MNQ.Z25")
    assert fill_type == "stop_loss"


def test_get_fill_type_returns_none_for_unknown_contract(correlator):
    """Test that unknown contract returns None."""
    fill_type = correlator.get_fill_type("UNKNOWN")
    assert fill_type is None


def test_get_fill_price_returns_correct_price(correlator):
    """Test getting fill price for recorded fill."""
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 12345
    )

    fill_price = correlator.get_fill_price("CON.F.US.MNQ.Z25")
    assert fill_price == 21500.00


def test_get_fill_price_returns_none_for_unknown_contract(correlator):
    """Test that unknown contract returns None."""
    fill_price = correlator.get_fill_price("UNKNOWN")
    assert fill_price is None


def test_get_fill_data_returns_complete_dict(correlator):
    """Test getting complete fill data."""
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 12345
    )

    fill_data = correlator.get_fill_data("CON.F.US.MNQ.Z25")
    assert fill_data is not None
    assert fill_data["type"] == "stop_loss"
    assert fill_data["fill_price"] == 21500.00
    assert fill_data["side"] == "SELL"
    assert fill_data["order_id"] == 12345
    assert "timestamp" in fill_data


def test_get_fill_data_returns_none_for_unknown_contract(correlator):
    """Test that unknown contract returns None."""
    fill_data = correlator.get_fill_data("UNKNOWN")
    assert fill_data is None


# ============================================================================
# Test: Clearing Fills
# ============================================================================

def test_clear_fill_removes_fill(correlator):
    """Test that clear_fill removes fill from tracking."""
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 12345
    )
    assert correlator.get_active_fills_count() == 1

    correlator.clear_fill("CON.F.US.MNQ.Z25")
    assert correlator.get_active_fills_count() == 0
    assert correlator.get_fill_type("CON.F.US.MNQ.Z25") is None


def test_clear_fill_idempotent(correlator):
    """Test that clearing non-existent fill doesn't error."""
    correlator.clear_fill("UNKNOWN")  # Should not raise
    assert correlator.get_active_fills_count() == 0


def test_clear_all_removes_all_fills(correlator):
    """Test that clear_all removes all fills."""
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 1
    )
    correlator.record_fill(
        "CON.F.US.ES.H25", "take_profit", 5200.00, "BUY", 2
    )
    assert correlator.get_active_fills_count() == 2

    correlator.clear_all()
    assert correlator.get_active_fills_count() == 0


# ============================================================================
# Test: TTL-Based Expiration
# ============================================================================

def test_fill_expires_after_ttl(short_ttl_correlator):
    """Test that fills expire after TTL."""
    correlator = short_ttl_correlator

    # Record fill
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 12345
    )
    assert correlator.get_active_fills_count() == 1

    # Wait for TTL to expire
    time.sleep(0.15)  # 150ms > 100ms TTL

    # Query should trigger cleanup and return None
    fill_type = correlator.get_fill_type("CON.F.US.MNQ.Z25")
    assert fill_type is None
    assert correlator.get_active_fills_count() == 0


def test_fill_does_not_expire_before_ttl(correlator):
    """Test that fills don't expire before TTL."""
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 12345
    )

    # Query immediately (well before 2s TTL)
    fill_type = correlator.get_fill_type("CON.F.US.MNQ.Z25")
    assert fill_type == "stop_loss"
    assert correlator.get_active_fills_count() == 1


def test_cleanup_removes_only_expired_fills(short_ttl_correlator):
    """Test that cleanup only removes expired fills, not fresh ones."""
    correlator = short_ttl_correlator

    # Record first fill
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 1
    )

    # Wait for it to expire
    time.sleep(0.15)

    # Record second fill (fresh)
    correlator.record_fill(
        "CON.F.US.ES.H25", "take_profit", 5200.00, "BUY", 2
    )

    # Query should cleanup expired fill but keep fresh one
    fill_type = correlator.get_fill_type("CON.F.US.ES.H25")
    assert fill_type == "take_profit"
    assert correlator.get_active_fills_count() == 1
    assert "CON.F.US.ES.H25" in correlator.get_active_contracts()
    assert "CON.F.US.MNQ.Z25" not in correlator.get_active_contracts()


# ============================================================================
# Test: Monitoring Methods
# ============================================================================

def test_get_active_fills_count(correlator):
    """Test getting active fills count."""
    assert correlator.get_active_fills_count() == 0

    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 1
    )
    assert correlator.get_active_fills_count() == 1

    correlator.record_fill(
        "CON.F.US.ES.H25", "take_profit", 5200.00, "BUY", 2
    )
    assert correlator.get_active_fills_count() == 2


def test_get_active_contracts(correlator):
    """Test getting list of active contracts."""
    assert correlator.get_active_contracts() == []

    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 1
    )
    correlator.record_fill(
        "CON.F.US.ES.H25", "take_profit", 5200.00, "BUY", 2
    )

    contracts = correlator.get_active_contracts()
    assert len(contracts) == 2
    assert "CON.F.US.MNQ.Z25" in contracts
    assert "CON.F.US.ES.H25" in contracts


# ============================================================================
# Test: Complete Workflow
# ============================================================================

def test_complete_correlation_workflow(correlator):
    """
    Integration test: Complete workflow from fill to correlation to cleanup.
    """
    contract_id = "CON.F.US.MNQ.Z25"

    # 1. Order fills (ORDER_FILLED event)
    correlator.record_fill(
        contract_id=contract_id,
        fill_type="stop_loss",
        fill_price=21500.00,
        side="SELL",
        order_id=12345
    )
    assert correlator.get_active_fills_count() == 1

    # 2. Position closes (POSITION_CLOSED event - shortly after)
    fill_type = correlator.get_fill_type(contract_id)
    assert fill_type == "stop_loss"

    fill_price = correlator.get_fill_price(contract_id)
    assert fill_price == 21500.00

    # 3. After processing position close, clear the fill
    correlator.clear_fill(contract_id)
    assert correlator.get_active_fills_count() == 0

    # 4. Subsequent queries return None
    assert correlator.get_fill_type(contract_id) is None
    assert correlator.get_fill_price(contract_id) is None


def test_multiple_contracts_correlation(correlator):
    """Test correlating fills for multiple contracts simultaneously."""
    # Record fills for 3 different contracts
    correlator.record_fill(
        "CON.F.US.MNQ.Z25", "stop_loss", 21500.00, "SELL", 1
    )
    correlator.record_fill(
        "CON.F.US.ES.H25", "take_profit", 5200.00, "BUY", 2
    )
    correlator.record_fill(
        "CON.F.US.YM.M25", "manual", 42000.00, "SELL", 3
    )

    # Verify all 3 can be queried independently
    assert correlator.get_fill_type("CON.F.US.MNQ.Z25") == "stop_loss"
    assert correlator.get_fill_type("CON.F.US.ES.H25") == "take_profit"
    assert correlator.get_fill_type("CON.F.US.YM.M25") == "manual"

    # Clear one doesn't affect others
    correlator.clear_fill("CON.F.US.MNQ.Z25")
    assert correlator.get_fill_type("CON.F.US.MNQ.Z25") is None
    assert correlator.get_fill_type("CON.F.US.ES.H25") == "take_profit"
    assert correlator.get_fill_type("CON.F.US.YM.M25") == "manual"
