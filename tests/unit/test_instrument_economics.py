"""
Test instrument economics: tick sizes, point values, and P&L calculations.

Ensures financial arithmetic is correct for ES/NQ/MNQ/MES contracts.
"""

import pytest


@pytest.mark.unit
class TestInstrumentEconomics:
    """Validate financial arithmetic for CME futures."""

    def test_tick_sizes_all_025(self, contract_es, contract_nq, contract_mnq, contract_mes):
        """All four contracts use 0.25 tick size."""
        assert contract_es["tick_size"] == 0.25
        assert contract_nq["tick_size"] == 0.25
        assert contract_mnq["tick_size"] == 0.25
        assert contract_mes["tick_size"] == 0.25

    def test_point_values_correct(self, contract_es, contract_nq, contract_mnq, contract_mes):
        """Verify point values: ES=$50, NQ=$20, MNQ=$2, MES=$5."""
        assert contract_es["point_value"] == 50.00
        assert contract_nq["point_value"] == 20.00
        assert contract_mnq["point_value"] == 2.00
        assert contract_mes["point_value"] == 5.00

    def test_tick_value_consistency(self, contract_es, contract_nq, contract_mnq, contract_mes):
        """tick_value = tick_size * point_value for all contracts."""
        for contract in [contract_es, contract_nq, contract_mnq, contract_mes]:
            expected = contract["tick_size"] * contract["point_value"]
            assert contract["tick_value"] == expected, \
                f"{contract['symbol_id']}: expected {expected}, got {contract['tick_value']}"

    @pytest.mark.parametrize("price,expected", [
        (5000.00, 5000.00),  # Already valid
        (5000.12, 5000.00),  # Round down
        (5000.25, 5000.25),  # Valid tick
        (5000.37, 5000.25),  # Round down to nearest 0.25
        (5000.50, 5000.50),  # Valid tick
        (5000.62, 5000.50),  # Round down
        (5000.75, 5000.75),  # Valid tick
        (5000.87, 5000.75),  # Round down to nearest 0.25
        (5000.88, 5001.00),  # Round up to nearest 0.25
    ])
    def test_price_rounding_to_valid_ticks(self, price, expected):
        """Prices must round to valid 0.25 increments."""
        tick_size = 0.25
        rounded = round(price / tick_size) * tick_size
        assert abs(rounded - expected) < 0.01, \
            f"Price {price} should round to {expected}, got {rounded}"

    def test_pnl_es_long_profit(self, contract_es):
        """ES Long: 1 contract @ 5000, exit 5010 = +$500."""
        entry = 5000.00
        exit = 5010.00
        size = 1
        point_value = contract_es["point_value"]

        pnl = (exit - entry) * point_value * size
        assert pnl == 500.00

    def test_pnl_es_long_loss(self, contract_es):
        """ES Long: 2 contracts @ 5000, exit 4990 = -$1000."""
        entry = 5000.00
        exit = 4990.00
        size = 2
        point_value = contract_es["point_value"]

        pnl = (exit - entry) * point_value * size
        assert pnl == -1000.00

    def test_pnl_mnq_long_loss(self, contract_mnq):
        """MNQ Long: 5 contracts @ 21500, exit 21400 = -$1000."""
        entry = 21500.00
        exit = 21400.00
        size = 5
        point_value = contract_mnq["point_value"]

        pnl = (exit - entry) * point_value * size
        assert pnl == -1000.00

    def test_pnl_nq_short_profit(self, contract_nq):
        """NQ Short: 2 contracts @ 18000, exit 17900 = +$4000."""
        entry = 18000.00
        exit = 17900.00
        size = 2
        point_value = contract_nq["point_value"]

        # Short: profit when price goes down
        pnl = (entry - exit) * point_value * size
        assert pnl == 4000.00

    def test_pnl_mes_short_loss(self, contract_mes):
        """MES Short: 10 contracts @ 5000, exit 5002 = -$100."""
        entry = 5000.00
        exit = 5002.00
        size = 10
        point_value = contract_mes["point_value"]

        # Short: loss when price goes up
        pnl = (entry - exit) * point_value * size
        assert pnl == -100.00
