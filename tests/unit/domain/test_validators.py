"""Unit tests for runtime invariant validators.

Tests validate that:
1. Position invariants catch unknown symbols
2. P&L sign invariants catch direction mismatches
3. Order price invariants catch tick misalignment
4. Event invariants catch incomplete data
"""

import pytest
from decimal import Decimal

from risk_manager.domain import (
    Money,
    Position,
    Side,
    UnitsError,
    SignConventionError,
    QuantityError,
    PriceError,
    ValidationError,
    validate_position,
    validate_pnl_sign,
    validate_order_price_alignment,
    validate_quantity_sign,
    validate_event_data_consistency,
    validate_position_consistency,
)


# Test data
TICK_TABLE = {
    "MNQ": {"size": 0.25, "tick_value": 0.50},
    "ES": {"size": 0.25, "tick_value": 12.50},
    "NQ": {"size": 0.25, "tick_value": 5.00},
    "YM": {"size": 1.00, "tick_value": 5.00},
}


class TestPositionInvariants:
    """Test position invariant validation."""

    def test_valid_long_position(self):
        """Valid LONG position should pass."""
        position = Position(
            symbol_root="MNQ",
            contract_id="CON.F.US.MNQ.Z25",
            side=Side.LONG,
            quantity=2,
            entry_price=Decimal("26385.50"),
            unrealized_pnl=Money(amount=Decimal("100.00")),
        )
        # Should not raise
        validate_position(position, TICK_TABLE)

    def test_valid_short_position(self):
        """Valid SHORT position should pass."""
        position = Position(
            symbol_root="ES",
            contract_id="CON.F.US.ES.Z25",
            side=Side.SHORT,
            quantity=1,
            entry_price=Decimal("5850.25"),
            unrealized_pnl=Money(amount=Decimal("-50.00")),
        )
        # Should not raise
        validate_position(position, TICK_TABLE)

    def test_unknown_symbol_raises_units_error(self):
        """Unknown symbol should raise UnitsError."""
        position = Position(
            symbol_root="UNKNOWN",
            contract_id="CON.F.US.UNKNOWN.Z25",
            side=Side.LONG,
            quantity=1,
            entry_price=Decimal("1000.00"),
            unrealized_pnl=Money(amount=Decimal("0.00")),
        )
        with pytest.raises(UnitsError, match="Unknown symbol"):
            validate_position(position, TICK_TABLE)

    def test_zero_quantity_caught_by_position_class(self):
        """Zero quantity is caught by Position.__post_init__ before validator."""
        # The Position class itself validates quantity > 0
        with pytest.raises(ValueError, match="positive"):
            position = Position(
                symbol_root="MNQ",
                contract_id="CON.F.US.MNQ.Z25",
                side=Side.LONG,
                quantity=0,
                entry_price=Decimal("26385.50"),
                unrealized_pnl=Money(amount=Decimal("0.00")),
            )

    def test_negative_price_raises_price_error(self):
        """Negative price should raise PriceError."""
        position = Position(
            symbol_root="MNQ",
            contract_id="CON.F.US.MNQ.Z25",
            side=Side.LONG,
            quantity=1,
            entry_price=Decimal("-100.00"),
            unrealized_pnl=Money(amount=Decimal("0.00")),
        )
        with pytest.raises(PriceError, match="positive"):
            validate_position(position, TICK_TABLE)

    def test_price_not_aligned_to_tick_raises_units_error(self):
        """Price not aligned to tick size should raise UnitsError."""
        # MNQ tick size is 0.25, so price must be X.00, X.25, X.50, X.75
        position = Position(
            symbol_root="MNQ",
            contract_id="CON.F.US.MNQ.Z25",
            side=Side.LONG,
            quantity=1,
            entry_price=Decimal("26385.33"),  # Not aligned to 0.25
            unrealized_pnl=Money(amount=Decimal("0.00")),
        )
        with pytest.raises(UnitsError, match="not aligned to tick"):
            validate_position(position, TICK_TABLE)

    def test_price_aligned_to_tick_passes(self):
        """Price correctly aligned to tick should pass."""
        # Test all valid alignments for 0.25 tick
        for price_str in ["26385.00", "26385.25", "26385.50", "26385.75"]:
            position = Position(
                symbol_root="MNQ",
                contract_id="CON.F.US.MNQ.Z25",
                side=Side.LONG,
                quantity=1,
                entry_price=Decimal(price_str),
                unrealized_pnl=Money(amount=Decimal("0.00")),
            )
            # Should not raise
            validate_position(position, TICK_TABLE)

    def test_ym_with_1_dollar_tick(self):
        """YM uses $1.00 tick size, validate correctly."""
        position = Position(
            symbol_root="YM",
            contract_id="CON.F.US.YM.Z25",
            side=Side.LONG,
            quantity=1,
            entry_price=Decimal("40000.00"),
            unrealized_pnl=Money(amount=Decimal("0.00")),
        )
        # Should not raise
        validate_position(position, TICK_TABLE)

    def test_ym_with_non_1_dollar_price_fails(self):
        """YM with non-integer price should fail."""
        position = Position(
            symbol_root="YM",
            contract_id="CON.F.US.YM.Z25",
            side=Side.LONG,
            quantity=1,
            entry_price=Decimal("40000.50"),  # Not aligned to $1
            unrealized_pnl=Money(amount=Decimal("0.00")),
        )
        with pytest.raises(UnitsError, match="not aligned"):
            validate_position(position, TICK_TABLE)


class TestPnLSignInvariants:
    """Test P&L sign validation."""

    def test_long_profitable_trade_passes(self):
        """LONG position with exit > entry and positive P&L should pass."""
        validate_pnl_sign(
            side=Side.LONG,
            entry_price=26300.00,
            exit_price=26350.00,
            pnl=Money(amount=Decimal("50.00")),
            tick_size=0.25,
        )
        # Should not raise

    def test_long_loss_trade_passes(self):
        """LONG position with exit < entry and negative P&L should pass."""
        validate_pnl_sign(
            side=Side.LONG,
            entry_price=26350.00,
            exit_price=26300.00,
            pnl=Money(amount=Decimal("-50.00")),
            tick_size=0.25,
        )
        # Should not raise

    def test_short_profitable_trade_passes(self):
        """SHORT position with entry > exit and positive P&L should pass."""
        validate_pnl_sign(
            side=Side.SHORT,
            entry_price=26350.00,
            exit_price=26300.00,
            pnl=Money(amount=Decimal("50.00")),
            tick_size=0.25,
        )
        # Should not raise

    def test_short_loss_trade_passes(self):
        """SHORT position with entry < exit and negative P&L should pass."""
        validate_pnl_sign(
            side=Side.SHORT,
            entry_price=26300.00,
            exit_price=26350.00,
            pnl=Money(amount=Decimal("-50.00")),
            tick_size=0.25,
        )
        # Should not raise

    def test_long_sign_mismatch_raises_error(self):
        """LONG position with wrong P&L sign should raise SignConventionError."""
        # Price went up (should be profit) but P&L is negative (loss)
        with pytest.raises(SignConventionError, match="LONG"):
            validate_pnl_sign(
                side=Side.LONG,
                entry_price=26300.00,
                exit_price=26350.00,
                pnl=Money(amount=Decimal("-50.00")),  # Wrong sign!
                tick_size=0.25,
            )

    def test_short_sign_mismatch_raises_error(self):
        """SHORT position with wrong P&L sign should raise SignConventionError."""
        # Sold high, bought low (should be profit) but P&L is negative (loss)
        with pytest.raises(SignConventionError, match="SHORT"):
            validate_pnl_sign(
                side=Side.SHORT,
                entry_price=26350.00,
                exit_price=26300.00,
                pnl=Money(amount=Decimal("-50.00")),  # Wrong sign!
                tick_size=0.25,
            )

    def test_zero_pnl_passes_with_no_price_movement(self):
        """Entry == exit with zero P&L should pass."""
        validate_pnl_sign(
            side=Side.LONG,
            entry_price=26300.00,
            exit_price=26300.00,
            pnl=Money(amount=Decimal("0.00")),
            tick_size=0.25,
        )
        # Should not raise


class TestOrderPriceAlignment:
    """Test order price alignment validation."""

    def test_limit_order_with_valid_price_passes(self):
        """Limit order with tick-aligned price should pass."""
        validate_order_price_alignment(
            symbol_root="MNQ",
            price=26385.50,
            tick_table=TICK_TABLE,
            order_type="limit",
        )
        # Should not raise

    def test_stop_order_with_valid_price_passes(self):
        """Stop order with tick-aligned price should pass."""
        validate_order_price_alignment(
            symbol_root="ES",
            price=5850.25,
            tick_table=TICK_TABLE,
            order_type="stop",
        )
        # Should not raise

    def test_market_order_skips_tick_validation(self):
        """Market order skips tick alignment check."""
        # Market orders don't have limit/stop prices, so any price is OK
        validate_order_price_alignment(
            symbol_root="MNQ",
            price=99999.99,  # Invalid for limit, but OK for market
            tick_table=TICK_TABLE,
            order_type="market",
        )
        # Should not raise

    def test_limit_order_with_misaligned_price_raises_error(self):
        """Limit order with non-aligned price should raise UnitsError."""
        with pytest.raises(UnitsError, match="not aligned"):
            validate_order_price_alignment(
                symbol_root="MNQ",
                price=26385.33,  # Not a multiple of 0.25
                tick_table=TICK_TABLE,
                order_type="limit",
            )

    def test_unknown_symbol_raises_error(self):
        """Unknown symbol should raise UnitsError."""
        with pytest.raises(UnitsError, match="Unknown symbol"):
            validate_order_price_alignment(
                symbol_root="UNKNOWN",
                price=1000.00,
                tick_table=TICK_TABLE,
                order_type="limit",
            )

    def test_negative_price_raises_error(self):
        """Negative price should raise PriceError."""
        with pytest.raises(PriceError, match="positive"):
            validate_order_price_alignment(
                symbol_root="MNQ",
                price=-100.00,
                tick_table=TICK_TABLE,
                order_type="limit",
            )


class TestQuantitySign:
    """Test quantity sign validation."""

    def test_long_position_positive_quantity_passes(self):
        """LONG with positive quantity should pass."""
        validate_quantity_sign(quantity=5, side=Side.LONG)
        # Should not raise

    def test_short_position_negative_quantity_passes(self):
        """SHORT with negative quantity should pass."""
        validate_quantity_sign(quantity=-5, side=Side.SHORT)
        # Should not raise

    def test_long_position_negative_quantity_raises_error(self):
        """LONG with negative quantity should raise SignConventionError."""
        with pytest.raises(SignConventionError, match="sign mismatch"):
            validate_quantity_sign(quantity=-5, side=Side.LONG)

    def test_short_position_positive_quantity_raises_error(self):
        """SHORT with positive quantity should raise SignConventionError."""
        with pytest.raises(SignConventionError, match="sign mismatch"):
            validate_quantity_sign(quantity=5, side=Side.SHORT)

    def test_zero_quantity_raises_error(self):
        """Zero quantity should raise QuantityError."""
        with pytest.raises(QuantityError, match="cannot be zero"):
            validate_quantity_sign(quantity=0, side=Side.LONG)


class TestEventDataConsistency:
    """Test event data validation."""

    def test_event_with_all_required_fields_passes(self):
        """Event with all required fields should pass."""
        validate_event_data_consistency(
            event_type="position_opened",
            event_data={
                "contractId": "CON.F.US.MNQ.Z25",
                "size": 1,
                "averagePrice": 26385.50,
                "type": 1,
            },
            required_fields=["contractId", "size", "averagePrice", "type"],
        )
        # Should not raise

    def test_event_missing_required_field_raises_error(self):
        """Event missing required field should raise ValidationError."""
        with pytest.raises(ValidationError, match="Missing required field"):
            validate_event_data_consistency(
                event_type="position_opened",
                event_data={
                    "contractId": "CON.F.US.MNQ.Z25",
                    "size": 1,
                    # Missing 'averagePrice'
                },
                required_fields=["contractId", "size", "averagePrice"],
            )

    def test_event_with_none_required_field_raises_error(self):
        """Event with None value for required field should raise ValidationError."""
        with pytest.raises(ValidationError, match="is None"):
            validate_event_data_consistency(
                event_type="position_opened",
                event_data={
                    "contractId": "CON.F.US.MNQ.Z25",
                    "size": None,  # None value
                    "averagePrice": 26385.50,
                },
                required_fields=["contractId", "size", "averagePrice"],
            )


class TestPositionConsistency:
    """Test position P&L consistency validation."""

    def test_long_position_profitable_pnl_consistent(self):
        """LONG position with rising price and positive P&L should pass."""
        validate_position_consistency(
            position_id="MNQ:1",
            size=1,
            entry_price=26300.00,
            current_price=26350.00,
            unrealized_pnl=50.00,
            side=Side.LONG,
        )
        # Should not raise

    def test_long_position_loss_pnl_consistent(self):
        """LONG position with falling price and negative P&L should pass."""
        validate_position_consistency(
            position_id="MNQ:1",
            size=1,
            entry_price=26350.00,
            current_price=26300.00,
            unrealized_pnl=-50.00,
            side=Side.LONG,
        )
        # Should not raise

    def test_short_position_profitable_pnl_consistent(self):
        """SHORT position with falling price and positive P&L should pass."""
        validate_position_consistency(
            position_id="ES:1",
            size=1,
            entry_price=5900.00,
            current_price=5850.00,
            unrealized_pnl=50.00,
            side=Side.SHORT,
        )
        # Should not raise

    def test_short_position_loss_pnl_consistent(self):
        """SHORT position with rising price and negative P&L should pass."""
        validate_position_consistency(
            position_id="ES:1",
            size=1,
            entry_price=5850.00,
            current_price=5900.00,
            unrealized_pnl=-50.00,
            side=Side.SHORT,
        )
        # Should not raise

    def test_long_position_pnl_sign_mismatch_raises_error(self):
        """LONG position with price up but negative P&L should raise error."""
        with pytest.raises(SignConventionError, match="sign inconsistent"):
            validate_position_consistency(
                position_id="MNQ:1",
                size=1,
                entry_price=26300.00,
                current_price=26350.00,
                unrealized_pnl=-50.00,  # Wrong sign!
                side=Side.LONG,
            )

    def test_short_position_pnl_sign_mismatch_raises_error(self):
        """SHORT position with price down but negative P&L should raise error."""
        with pytest.raises(SignConventionError, match="sign inconsistent"):
            validate_position_consistency(
                position_id="ES:1",
                size=1,
                entry_price=5900.00,
                current_price=5850.00,
                unrealized_pnl=-50.00,  # Wrong sign!
                side=Side.SHORT,
            )

    def test_small_pnl_differences_within_tolerance(self):
        """Small P&L rounding differences within tolerance should pass."""
        # Price moved 1 cent but P&L is 0 (within 1.00 tolerance)
        validate_position_consistency(
            position_id="MNQ:1",
            size=1,
            entry_price=26300.00,
            current_price=26300.01,
            unrealized_pnl=0.00,
            side=Side.LONG,
            tolerance=1.00,
        )
        # Should not raise


class TestIntegrationWithDomain:
    """Integration tests using Position and Money classes."""

    def test_position_from_event_data(self):
        """Create Position from event data and validate."""
        position = Position(
            symbol_root="MNQ",
            contract_id="CON.F.US.MNQ.Z25",
            side=Side.LONG,
            quantity=1,
            entry_price=Decimal("26385.50"),
            unrealized_pnl=Money(amount=Decimal("100.00")),
        )

        # Should validate successfully
        validate_position(position, TICK_TABLE)

    def test_invalid_symbol_caught_by_validator(self):
        """Invalid symbol in Position should be caught by validator."""
        position = Position(
            symbol_root="BADTICKER",
            contract_id="CON.F.US.BADTICKER.Z25",
            side=Side.LONG,
            quantity=1,
            entry_price=Decimal("1000.00"),
            unrealized_pnl=Money(amount=Decimal("0.00")),
        )

        with pytest.raises(UnitsError):
            validate_position(position, TICK_TABLE)

    def test_pnl_calculation_consistency(self):
        """Validate P&L calculation against position."""
        entry = Decimal("26300.00")
        exit = Decimal("26350.00")
        tick_size = Decimal("0.25")
        tick_value = Decimal("0.50")

        # Calculate realized P&L
        price_diff = exit - entry
        ticks = price_diff / tick_size
        realized_pnl = ticks * tick_value

        # Create Money object
        pnl = Money(amount=realized_pnl)

        # Validate sign
        validate_pnl_sign(
            side=Side.LONG,
            entry_price=float(entry),
            exit_price=float(exit),
            pnl=pnl,
            tick_size=0.25,
        )
        # Should not raise

        assert pnl.is_profit
        assert pnl.amount == Decimal("100.00")
