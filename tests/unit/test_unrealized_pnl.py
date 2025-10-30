"""
Unit tests for UnrealizedPnLCalculator module.

Tests position tracking and P&L calculations (both unrealized and realized).
"""

import pytest
from decimal import Decimal
from risk_manager.integrations.unrealized_pnl import UnrealizedPnLCalculator


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def calculator():
    """Create UnrealizedPnLCalculator instance."""
    return UnrealizedPnLCalculator()


@pytest.fixture
def mnq_long_position():
    """Sample MNQ long position data."""
    return {
        'price': 21500.00,
        'size': 2,
        'side': 'long',
        'symbol': 'MNQ',
    }


@pytest.fixture
def mnq_short_position():
    """Sample MNQ short position data."""
    return {
        'price': 21500.00,
        'size': -2,  # Negative for short
        'side': 'short',
        'symbol': 'MNQ',
    }


@pytest.fixture
def es_long_position():
    """Sample ES long position data."""
    return {
        'price': 5200.00,
        'size': 1,
        'side': 'long',
        'symbol': 'ES',
    }


# ============================================================================
# Test: Initialization
# ============================================================================

def test_initialization(calculator):
    """Test that calculator initializes with empty state."""
    assert calculator.get_position_count() == 0
    assert calculator.get_open_positions() == {}
    assert calculator.calculate_total_unrealized_pnl() == Decimal('0')


# ============================================================================
# Test: Position Tracking
# ============================================================================

def test_update_position_adds_new_position(calculator, mnq_long_position):
    """Test that update_position tracks a new position."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)

    assert calculator.get_position_count() == 1
    positions = calculator.get_open_positions()
    assert 'CON.F.US.MNQ.Z25' in positions

    position = positions['CON.F.US.MNQ.Z25']
    assert position['entry_price'] == Decimal('21500.00')
    assert position['size'] == 2
    assert position['side'] == 'long'
    assert position['symbol'] == 'MNQ'


def test_update_position_stores_symbol(calculator):
    """Test that symbol is stored correctly."""
    position_data = {
        'price': 21500.00,
        'size': 1,
        'side': 'long',
        'symbol': 'MNQ',
    }
    calculator.update_position('CON.F.US.MNQ.Z25', position_data)

    positions = calculator.get_open_positions()
    position = positions['CON.F.US.MNQ.Z25']
    assert position['symbol'] == 'MNQ'
    assert position['original_symbol'] == 'MNQ'


def test_remove_position_deletes_position(calculator, mnq_long_position):
    """Test that remove_position deletes tracked position."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)
    assert calculator.get_position_count() == 1

    calculator.remove_position('CON.F.US.MNQ.Z25')
    assert calculator.get_position_count() == 0


def test_remove_position_idempotent(calculator):
    """Test that removing non-existent position doesn't error."""
    calculator.remove_position('NON_EXISTENT')  # Should not raise


def test_multiple_positions_tracked(calculator, mnq_long_position, es_long_position):
    """Test tracking multiple positions simultaneously."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)
    calculator.update_position('CON.F.US.ES.H25', es_long_position)

    assert calculator.get_position_count() == 2


# ============================================================================
# Test: Quote Updates
# ============================================================================

def test_update_quote_stores_price(calculator):
    """Test that update_quote stores market price."""
    calculator.update_quote('MNQ', 21550.00)

    # Quote storage is internal, verify via unrealized P&L calculation
    # (we'll test this more thoroughly in P&L tests)


def test_update_quote_normalizes_symbol(calculator):
    """Test that quote symbol normalization works."""
    calculator.update_quote('F.US.MNQ', 21550.00)  # SDK format
    # Should normalize to 'MNQ' internally


# ============================================================================
# Test: Unrealized P&L Calculation
# ============================================================================

def test_calculate_unrealized_pnl_long_profit(calculator, mnq_long_position):
    """Test unrealized P&L calculation for long position in profit."""
    # Track position
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)

    # Update market price (price went up = profit for long)
    calculator.update_quote('MNQ', 21550.00)

    # Calculate unrealized P&L
    pnl = calculator.calculate_unrealized_pnl('CON.F.US.MNQ.Z25')

    # MNQ: tick_size=0.25, tick_value=$0.50
    # Price diff: 21550 - 21500 = 50 points = 200 ticks
    # P&L: 200 ticks × $0.50 × 2 contracts = $200
    assert pnl == Decimal('200.00')


def test_calculate_unrealized_pnl_long_loss(calculator, mnq_long_position):
    """Test unrealized P&L calculation for long position in loss."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)

    # Price went down = loss for long
    calculator.update_quote('MNQ', 21450.00)

    pnl = calculator.calculate_unrealized_pnl('CON.F.US.MNQ.Z25')

    # Price diff: 21450 - 21500 = -50 points = -200 ticks
    # P&L: -200 ticks × $0.50 × 2 contracts = -$200
    assert pnl == Decimal('-200.00')


def test_calculate_unrealized_pnl_short_profit(calculator, mnq_short_position):
    """Test unrealized P&L calculation for short position in profit."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_short_position)

    # Price went down = profit for short
    calculator.update_quote('MNQ', 21450.00)

    pnl = calculator.calculate_unrealized_pnl('CON.F.US.MNQ.Z25')

    # Price diff for short: 21500 - 21450 = 50 points = 200 ticks
    # P&L: 200 ticks × $0.50 × 2 contracts = $200
    assert pnl == Decimal('200.00')


def test_calculate_unrealized_pnl_short_loss(calculator, mnq_short_position):
    """Test unrealized P&L calculation for short position in loss."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_short_position)

    # Price went up = loss for short
    calculator.update_quote('MNQ', 21550.00)

    pnl = calculator.calculate_unrealized_pnl('CON.F.US.MNQ.Z25')

    # Price diff for short: 21500 - 21550 = -50 points = -200 ticks
    # P&L: -200 ticks × $0.50 × 2 contracts = -$200
    assert pnl == Decimal('-200.00')


def test_calculate_unrealized_pnl_returns_none_for_unknown_position(calculator):
    """Test that unrealized P&L returns None for unknown position."""
    pnl = calculator.calculate_unrealized_pnl('UNKNOWN')
    assert pnl is None


def test_calculate_unrealized_pnl_returns_none_without_quote(calculator, mnq_long_position):
    """Test that unrealized P&L returns None if no quote available."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)
    # No quote update

    pnl = calculator.calculate_unrealized_pnl('CON.F.US.MNQ.Z25')
    assert pnl is None


def test_calculate_total_unrealized_pnl_multiple_positions(
    calculator, mnq_long_position, es_long_position
):
    """Test total unrealized P&L across multiple positions."""
    # Track two positions
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)
    calculator.update_position('CON.F.US.ES.H25', es_long_position)

    # Update quotes
    calculator.update_quote('MNQ', 21550.00)  # +$200 (50 points = 200 ticks × $0.50 × 2)
    calculator.update_quote('ES', 5210.00)    # +$500 (10 points = 40 ticks × $12.50 × 1)

    total_pnl = calculator.calculate_total_unrealized_pnl()

    # Total: $200 + $500 = $700
    assert total_pnl == Decimal('700.00')


# ============================================================================
# Test: Realized P&L Calculation (NEW)
# ============================================================================

def test_calculate_realized_pnl_long_profit(calculator, mnq_long_position):
    """Test realized P&L calculation for long position closed at profit."""
    # Track position
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)

    # Close at higher price (profit for long)
    exit_price = 21550.00
    realized_pnl = calculator.calculate_realized_pnl('CON.F.US.MNQ.Z25', exit_price)

    # MNQ: tick_size=0.25, tick_value=$0.50
    # Price diff: 21550 - 21500 = 50 points = 200 ticks
    # P&L: 200 ticks × $0.50 × 2 contracts = $200
    assert realized_pnl == Decimal('200.00')


def test_calculate_realized_pnl_long_loss(calculator, mnq_long_position):
    """Test realized P&L calculation for long position closed at loss."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)

    # Close at lower price (loss for long)
    exit_price = 21450.00
    realized_pnl = calculator.calculate_realized_pnl('CON.F.US.MNQ.Z25', exit_price)

    # Price diff: 21450 - 21500 = -50 points = -200 ticks
    # P&L: -200 ticks × $0.50 × 2 contracts = -$200
    assert realized_pnl == Decimal('-200.00')


def test_calculate_realized_pnl_short_profit(calculator, mnq_short_position):
    """Test realized P&L calculation for short position closed at profit."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_short_position)

    # Close at lower price (profit for short)
    exit_price = 21450.00
    realized_pnl = calculator.calculate_realized_pnl('CON.F.US.MNQ.Z25', exit_price)

    # Price diff for short: 21500 - 21450 = 50 points = 200 ticks
    # P&L: 200 ticks × $0.50 × 2 contracts = $200
    assert realized_pnl == Decimal('200.00')


def test_calculate_realized_pnl_short_loss(calculator, mnq_short_position):
    """Test realized P&L calculation for short position closed at loss."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_short_position)

    # Close at higher price (loss for short)
    exit_price = 21550.00
    realized_pnl = calculator.calculate_realized_pnl('CON.F.US.MNQ.Z25', exit_price)

    # Price diff for short: 21500 - 21550 = -50 points = -200 ticks
    # P&L: -200 ticks × $0.50 × 2 contracts = -$200
    assert realized_pnl == Decimal('-200.00')


def test_calculate_realized_pnl_returns_none_for_unknown_position(calculator):
    """Test that realized P&L returns None for unknown position."""
    realized_pnl = calculator.calculate_realized_pnl('UNKNOWN', 21500.00)
    assert realized_pnl is None


def test_calculate_realized_pnl_breakeven(calculator, mnq_long_position):
    """Test realized P&L calculation for breakeven trade."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)

    # Close at same price (breakeven)
    exit_price = 21500.00
    realized_pnl = calculator.calculate_realized_pnl('CON.F.US.MNQ.Z25', exit_price)

    # No price difference = $0 P&L
    assert realized_pnl == Decimal('0.00')


def test_calculate_realized_pnl_es_contract(calculator, es_long_position):
    """Test realized P&L calculation for ES contract (different tick economics)."""
    calculator.update_position('CON.F.US.ES.H25', es_long_position)

    # Close at profit
    exit_price = 5210.00
    realized_pnl = calculator.calculate_realized_pnl('CON.F.US.ES.H25', exit_price)

    # ES: tick_size=0.25, tick_value=$12.50
    # Price diff: 5210 - 5200 = 10 points = 40 ticks
    # P&L: 40 ticks × $12.50 × 1 contract = $500
    assert realized_pnl == Decimal('500.00')


# ============================================================================
# Test: Significant P&L Change Detection
# ============================================================================

def test_has_significant_pnl_change_true(calculator, mnq_long_position):
    """Test that significant P&L change is detected."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)
    calculator.update_quote('MNQ', 21550.00)  # +$200

    # First check should be True (change from $0 to $200 > $10 threshold)
    assert calculator.has_significant_pnl_change('CON.F.US.MNQ.Z25', threshold=10.0)


def test_has_significant_pnl_change_false(calculator, mnq_long_position):
    """Test that insignificant P&L change is not detected."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)
    calculator.update_quote('MNQ', 21550.00)  # +$200

    # First check (logs $200)
    calculator.has_significant_pnl_change('CON.F.US.MNQ.Z25', threshold=10.0)

    # Update quote slightly
    calculator.update_quote('MNQ', 21551.00)  # Now +$204 (only $4 change)

    # Second check should be False (change < $10 threshold)
    assert not calculator.has_significant_pnl_change('CON.F.US.MNQ.Z25', threshold=10.0)


# ============================================================================
# Test: Get Positions by Symbol
# ============================================================================

def test_get_positions_by_symbol(calculator, mnq_long_position, es_long_position):
    """Test filtering positions by symbol."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)
    calculator.update_position('CON.F.US.ES.H25', es_long_position)

    mnq_positions = calculator.get_positions_by_symbol('MNQ')
    assert len(mnq_positions) == 1
    assert 'CON.F.US.MNQ.Z25' in mnq_positions


def test_get_positions_by_symbol_empty(calculator):
    """Test get_positions_by_symbol returns empty dict for unknown symbol."""
    positions = calculator.get_positions_by_symbol('UNKNOWN')
    assert positions == {}


# ============================================================================
# Test: Clear All
# ============================================================================

def test_clear_all(calculator, mnq_long_position):
    """Test that clear_all resets calculator state."""
    calculator.update_position('CON.F.US.MNQ.Z25', mnq_long_position)
    calculator.update_quote('MNQ', 21550.00)

    assert calculator.get_position_count() > 0

    calculator.clear_all()

    assert calculator.get_position_count() == 0
    assert calculator.get_open_positions() == {}
    assert calculator.calculate_total_unrealized_pnl() == Decimal('0')


# ============================================================================
# Summary
# ============================================================================

def test_unrealized_pnl_calculator_complete_workflow(calculator):
    """
    Integration test: Complete workflow from position open to close.
    """
    # 1. Open position
    position_data = {
        'price': 21500.00,
        'size': 2,
        'side': 'long',
        'symbol': 'MNQ',
    }
    calculator.update_position('CON.F.US.MNQ.Z25', position_data)
    assert calculator.get_position_count() == 1

    # 2. Update market price
    calculator.update_quote('MNQ', 21550.00)

    # 3. Calculate unrealized P&L (while position open)
    unrealized = calculator.calculate_unrealized_pnl('CON.F.US.MNQ.Z25')
    assert unrealized == Decimal('200.00')

    # 4. Position closes - calculate realized P&L
    realized = calculator.calculate_realized_pnl('CON.F.US.MNQ.Z25', 21550.00)
    assert realized == Decimal('200.00')

    # 5. Remove position
    calculator.remove_position('CON.F.US.MNQ.Z25')
    assert calculator.get_position_count() == 0
