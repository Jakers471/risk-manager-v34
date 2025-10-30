"""
Contract tests for SDK adapter.

These tests verify that:
1. SDK position events → canonical Position (correct fields/types)
2. Symbol normalization works (ENQ → NQ)
3. Tick economics lookups succeed for known symbols
4. Missing SDK fields raise MappingError (fail loud)
5. Unknown symbols raise UnitsError (no silent fallback to 0.0)
"""

from decimal import Decimal

import pytest

from risk_manager.domain.types import Money, Position, Side
from risk_manager.errors import MappingError, UnitsError
from risk_manager.integrations.adapters import adapter, SDKAdapter


class TestSymbolNormalization:
    """Test symbol normalization (aliases)."""

    def test_enq_normalizes_to_nq(self):
        """ENQ → NQ (alias mapping)."""
        result = adapter.normalize_symbol("ENQ")
        assert result == "NQ"

    def test_mnq_stays_mnq(self):
        """MNQ → MNQ (no alias)."""
        result = adapter.normalize_symbol("MNQ")
        assert result == "MNQ"

    def test_contract_id_extracts_symbol(self):
        """CON.F.US.MNQ.Z25 → MNQ."""
        result = adapter.normalize_symbol("CON.F.US.MNQ.Z25")
        assert result == "MNQ"

    def test_contract_id_with_alias(self):
        """CON.F.US.ENQ.Z25 → NQ (extract + alias)."""
        result = adapter.normalize_symbol("CON.F.US.ENQ.Z25")
        assert result == "NQ"

    def test_empty_symbol_raises_mapping_error(self):
        """Empty symbol → MappingError."""
        with pytest.raises(MappingError, match="Symbol or contract ID is empty"):
            adapter.normalize_symbol("")

    def test_normalize_symbol_uppercases(self):
        """Lowercase symbols are uppercased."""
        result = adapter.normalize_symbol("nq")
        assert result == "NQ"


class TestTickEconomics:
    """Test tick size/value lookups."""

    def test_es_tick_economics(self):
        """ES tick size = 0.25, tick value = $12.50."""
        result = adapter.get_tick_economics("ES")
        assert result == {"size": 0.25, "tick_value": 12.50}

    def test_mnq_tick_economics(self):
        """MNQ tick size = 0.25, tick value = $0.50."""
        result = adapter.get_tick_economics("MNQ")
        assert result == {"size": 0.25, "tick_value": 0.50}

    def test_nq_tick_economics(self):
        """NQ tick size = 0.25, tick value = $5.00."""
        result = adapter.get_tick_economics("NQ")
        assert result == {"size": 0.25, "tick_value": 5.00}

    def test_unknown_symbol_raises_units_error(self):
        """Unknown symbol → UnitsError (no silent fallback)."""
        with pytest.raises(UnitsError, match="Unknown symbol 'ZZZ'"):
            adapter.get_tick_economics("ZZZ")

    def test_units_error_lists_known_symbols(self):
        """UnitsError message includes known symbols."""
        with pytest.raises(UnitsError, match="Known symbols:"):
            adapter.get_tick_economics("UNKNOWN")


class TestPositionNormalization:
    """Test SDK position → canonical Position conversion."""

    def test_long_position_from_dict(self):
        """SDK position dict → canonical Position (long)."""
        sdk_position = {
            "contractId": "CON.F.US.MNQ.Z25",
            "avgPrice": 21000.00,
            "size": 2,
            "type": 1,  # 1 = LONG
        }

        result = adapter.normalize_position_from_dict(
            sdk_position, current_price=21010.00  # +$10 profit
        )

        assert isinstance(result, Position)
        assert result.symbol_root == "MNQ"
        assert result.contract_id == "CON.F.US.MNQ.Z25"
        assert result.side == Side.LONG
        assert result.quantity == 2
        assert result.entry_price == Decimal("21000.00")

        # Check P&L calculation
        # 10 points = 40 ticks (10 / 0.25)
        # 40 ticks * 2 contracts * $0.50 = $40 profit
        assert result.unrealized_pnl.amount == Decimal("40.0")
        assert result.unrealized_pnl.is_profit

    def test_short_position_from_dict(self):
        """SDK position dict → canonical Position (short)."""
        sdk_position = {
            "contractId": "CON.F.US.MNQ.Z25",
            "avgPrice": 21000.00,
            "size": -2,
            "type": 2,  # 2 = SHORT
        }

        result = adapter.normalize_position_from_dict(
            sdk_position, current_price=20990.00  # -$10 = profit for short
        )

        assert result.side == Side.SHORT
        assert result.quantity == 2  # Quantity is always positive

        # Check P&L calculation
        # Short: profit when price goes down
        # 10 points down = 40 ticks * 2 contracts * $0.50 = $40 profit
        assert result.unrealized_pnl.amount == Decimal("40.0")
        assert result.unrealized_pnl.is_profit

    def test_losing_long_position(self):
        """Long position with loss (negative P&L)."""
        sdk_position = {
            "contractId": "CON.F.US.NQ.Z25",
            "avgPrice": 20000.00,
            "size": 1,
            "type": 1,
        }

        result = adapter.normalize_position_from_dict(
            sdk_position, current_price=19990.00  # -$10 loss
        )

        # 10 points down = 40 ticks * 1 contract * $5.00 = -$200 loss
        assert result.unrealized_pnl.amount == Decimal("-200.0")
        assert result.unrealized_pnl.is_loss

    def test_position_with_alias_symbol(self):
        """SDK position with ENQ → normalizes to NQ."""
        sdk_position = {
            "contractId": "CON.F.US.ENQ.Z25",
            "avgPrice": 20000.00,
            "size": 1,
            "type": 1,
        }

        result = adapter.normalize_position_from_dict(sdk_position)

        # ENQ should be normalized to NQ
        assert result.symbol_root == "NQ"
        assert result.contract_id == "CON.F.US.ENQ.Z25"

    def test_position_without_current_price(self):
        """Position without current price → P&L = $0."""
        sdk_position = {
            "contractId": "CON.F.US.MNQ.Z25",
            "avgPrice": 21000.00,
            "size": 2,
            "type": 1,
        }

        result = adapter.normalize_position_from_dict(sdk_position, current_price=None)

        # No current price → unrealized P&L = 0
        assert result.unrealized_pnl.amount == Decimal("0.0")

    def test_missing_contract_id_raises_mapping_error(self):
        """Position missing contractId → MappingError."""
        sdk_position = {
            "avgPrice": 21000.00,
            "size": 2,
            "type": 1,
        }

        with pytest.raises(MappingError, match="missing contractId"):
            adapter.normalize_position_from_dict(sdk_position)

    def test_missing_avg_price_raises_mapping_error(self):
        """Position missing avgPrice → MappingError."""
        sdk_position = {
            "contractId": "CON.F.US.MNQ.Z25",
            "size": 2,
            "type": 1,
        }

        with pytest.raises(MappingError, match="missing avgPrice"):
            adapter.normalize_position_from_dict(sdk_position)

    def test_missing_size_raises_mapping_error(self):
        """Position missing size → MappingError."""
        sdk_position = {
            "contractId": "CON.F.US.MNQ.Z25",
            "avgPrice": 21000.00,
            "type": 1,
        }

        with pytest.raises(MappingError, match="missing size"):
            adapter.normalize_position_from_dict(sdk_position)

    def test_missing_type_raises_mapping_error(self):
        """Position missing type → MappingError."""
        sdk_position = {
            "contractId": "CON.F.US.MNQ.Z25",
            "avgPrice": 21000.00,
            "size": 2,
        }

        with pytest.raises(MappingError, match="missing type"):
            adapter.normalize_position_from_dict(sdk_position)

    def test_invalid_type_raises_value_error(self):
        """Position with invalid type (not 1 or 2) → ValueError."""
        sdk_position = {
            "contractId": "CON.F.US.MNQ.Z25",
            "avgPrice": 21000.00,
            "size": 2,
            "type": 999,  # Invalid
        }

        with pytest.raises(ValueError, match="Invalid SDK type: 999"):
            adapter.normalize_position_from_dict(sdk_position)

    def test_position_from_object_with_attributes(self):
        """SDK position as object (not dict) → canonical Position."""

        class MockPosition:
            contractId = "CON.F.US.MNQ.Z25"
            avgPrice = 21000.00
            size = 2
            type = 1

        result = adapter.normalize_position(MockPosition(), current_price=21010.00)

        assert result.symbol_root == "MNQ"
        assert result.quantity == 2
        assert result.side == Side.LONG


class TestPnLCalculation:
    """Test P&L calculation logic."""

    def test_es_long_10_ticks_profit(self):
        """ES long position, 10 ticks profit = $125."""
        sdk_position = {
            "contractId": "CON.F.US.ES.Z25",
            "avgPrice": 5000.00,
            "size": 1,
            "type": 1,
        }

        # ES tick = 0.25, so 10 ticks = 2.5 points
        result = adapter.normalize_position_from_dict(sdk_position, current_price=5002.50)

        # 10 ticks * 1 contract * $12.50 = $125
        assert result.unrealized_pnl.amount == Decimal("125.0")

    def test_es_short_10_ticks_profit(self):
        """ES short position, 10 ticks profit = $125."""
        sdk_position = {
            "contractId": "CON.F.US.ES.Z25",
            "avgPrice": 5000.00,
            "size": -1,
            "type": 2,
        }

        # Price goes down 2.5 points (10 ticks) → profit for short
        result = adapter.normalize_position_from_dict(sdk_position, current_price=4997.50)

        # 10 ticks * 1 contract * $12.50 = $125
        assert result.unrealized_pnl.amount == Decimal("125.0")

    def test_mnq_multiple_contracts(self):
        """MNQ with 5 contracts, 20 ticks loss."""
        sdk_position = {
            "contractId": "CON.F.US.MNQ.Z25",
            "avgPrice": 21000.00,
            "size": 5,
            "type": 1,
        }

        # 5 points down = 20 ticks (5 / 0.25)
        # 20 ticks * 5 contracts * $0.50 = $50 loss
        result = adapter.normalize_position_from_dict(sdk_position, current_price=20995.00)

        assert result.unrealized_pnl.amount == Decimal("-50.0")
        assert result.unrealized_pnl.is_loss


class TestAdapterSingleton:
    """Test adapter singleton instance."""

    def test_adapter_is_sdk_adapter_instance(self):
        """Adapter is an instance of SDKAdapter."""
        assert isinstance(adapter, SDKAdapter)

    def test_adapter_is_reusable(self):
        """Adapter can be called multiple times."""
        # Call 1
        result1 = adapter.normalize_symbol("MNQ")
        assert result1 == "MNQ"

        # Call 2 (should work identically)
        result2 = adapter.normalize_symbol("MNQ")
        assert result2 == "MNQ"


class TestSideConversion:
    """Test Side enum conversion."""

    def test_sdk_type_1_is_long(self):
        """SDK type 1 → Side.LONG."""
        result = Side.from_sdk_type(1)
        assert result == Side.LONG
        assert result.value == "long"

    def test_sdk_type_2_is_short(self):
        """SDK type 2 → Side.SHORT."""
        result = Side.from_sdk_type(2)
        assert result == Side.SHORT
        assert result.value == "short"

    def test_invalid_sdk_type_raises_value_error(self):
        """Invalid SDK type → ValueError."""
        with pytest.raises(ValueError, match="Invalid SDK type: 99"):
            Side.from_sdk_type(99)


class TestMoneyType:
    """Test Money type behavior."""

    def test_money_is_loss(self):
        """Negative amount is a loss."""
        money = Money(amount=Decimal("-100.0"))
        assert money.is_loss
        assert not money.is_profit

    def test_money_is_profit(self):
        """Positive amount is a profit."""
        money = Money(amount=Decimal("100.0"))
        assert money.is_profit
        assert not money.is_loss

    def test_money_zero_is_neither(self):
        """Zero is neither profit nor loss."""
        money = Money(amount=Decimal("0.0"))
        assert not money.is_profit
        assert not money.is_loss

    def test_money_formats_as_currency(self):
        """Money formats with $ and commas."""
        money = Money(amount=Decimal("1234.56"))
        assert str(money) == "$1,234.56"

    def test_money_auto_converts_to_decimal(self):
        """Money auto-converts float to Decimal."""
        money = Money(amount=100.50)
        assert isinstance(money.amount, Decimal)
        assert money.amount == Decimal("100.50")


class TestPositionInvariants:
    """Test Position invariants."""

    def test_position_is_long(self):
        """Position.is_long property."""
        position = Position(
            symbol_root="MNQ",
            contract_id="CON.F.US.MNQ.Z25",
            side=Side.LONG,
            quantity=1,
            entry_price=Decimal("21000.00"),
            unrealized_pnl=Money(amount=Decimal("0.0")),
        )
        assert position.is_long
        assert not position.is_short

    def test_position_is_short(self):
        """Position.is_short property."""
        position = Position(
            symbol_root="MNQ",
            contract_id="CON.F.US.MNQ.Z25",
            side=Side.SHORT,
            quantity=1,
            entry_price=Decimal("21000.00"),
            unrealized_pnl=Money(amount=Decimal("0.0")),
        )
        assert position.is_short
        assert not position.is_long

    def test_position_quantity_must_be_positive(self):
        """Position quantity must be > 0."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            Position(
                symbol_root="MNQ",
                contract_id="CON.F.US.MNQ.Z25",
                side=Side.LONG,
                quantity=0,  # Invalid!
                entry_price=Decimal("21000.00"),
                unrealized_pnl=Money(amount=Decimal("0.0")),
            )

    def test_position_auto_converts_entry_price_to_decimal(self):
        """Position auto-converts entry_price to Decimal."""
        position = Position(
            symbol_root="MNQ",
            contract_id="CON.F.US.MNQ.Z25",
            side=Side.LONG,
            quantity=1,
            entry_price=21000.00,  # Float
            unrealized_pnl=Money(amount=Decimal("0.0")),
        )
        assert isinstance(position.entry_price, Decimal)
