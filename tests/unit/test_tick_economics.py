"""
Test tick economics utilities - fail-fast behavior for unknown symbols.

Tests the safe utility functions that replace silent .get() fallbacks.
"""

import pytest
from risk_manager.integrations.tick_economics import (
    normalize_symbol,
    get_tick_economics_safe,
    get_tick_value_safe,
    get_tick_size_safe,
    get_tick_economics_and_values,
    validate_symbol_known,
    UnitsError,
    MappingError,
    TICK_VALUES,
    ALIASES,
)


class TestNormalizeSymbol:
    """Test symbol normalization via aliases."""

    def test_normalize_known_alias(self):
        """Test normalizing a known alias."""
        assert normalize_symbol("ENQ") == "NQ"

    def test_normalize_unknown_symbol_passthrough(self):
        """Test normalizing an unknown symbol (returns as-is)."""
        assert normalize_symbol("NQ") == "NQ"
        assert normalize_symbol("ES") == "ES"
        assert normalize_symbol("MNQ") == "MNQ"

    def test_normalize_empty_symbol_raises(self):
        """Test normalizing empty symbol raises MappingError."""
        with pytest.raises(MappingError, match="Symbol cannot be empty"):
            normalize_symbol("")


class TestGetTickEconomicsSafe:
    """Test get_tick_economics_safe - FAIL FAST on unknown symbols."""

    def test_get_known_symbol(self):
        """Test getting tick economics for known symbol."""
        tick_info = get_tick_economics_safe("NQ")
        assert tick_info == {"size": 0.25, "tick_value": 5.00}

    def test_get_known_symbol_via_alias(self):
        """Test getting tick economics via alias."""
        tick_info = get_tick_economics_safe("ENQ")
        assert tick_info == {"size": 0.25, "tick_value": 5.00}

    def test_get_all_known_symbols(self):
        """Test all symbols in TICK_VALUES are retrievable."""
        for symbol in TICK_VALUES.keys():
            tick_info = get_tick_economics_safe(symbol)
            assert "size" in tick_info
            assert "tick_value" in tick_info
            assert tick_info["size"] > 0
            assert tick_info["tick_value"] > 0

    def test_unknown_symbol_raises_units_error(self):
        """Test unknown symbol raises UnitsError with helpful message."""
        with pytest.raises(UnitsError) as exc_info:
            get_tick_economics_safe("UNKNOWN")

        error_msg = str(exc_info.value)
        assert "Unknown symbol: UNKNOWN" in error_msg
        assert "normalized: UNKNOWN" in error_msg
        assert "Known symbols:" in error_msg
        assert "NQ" in error_msg
        assert "ES" in error_msg

    def test_empty_symbol_raises_mapping_error(self):
        """Test empty symbol raises MappingError."""
        with pytest.raises(MappingError, match="Symbol cannot be empty"):
            get_tick_economics_safe("")


class TestGetTickValueSafe:
    """Test get_tick_value_safe - convenience function."""

    def test_get_tick_value_nq(self):
        """Test getting tick value for NQ."""
        assert get_tick_value_safe("NQ") == 5.00

    def test_get_tick_value_mnq(self):
        """Test getting tick value for MNQ."""
        assert get_tick_value_safe("MNQ") == 0.50

    def test_get_tick_value_es(self):
        """Test getting tick value for ES."""
        assert get_tick_value_safe("ES") == 12.50

    def test_unknown_symbol_raises(self):
        """Test unknown symbol raises UnitsError."""
        with pytest.raises(UnitsError):
            get_tick_value_safe("UNKNOWN")


class TestGetTickSizeSafe:
    """Test get_tick_size_safe - convenience function."""

    def test_get_tick_size_nq(self):
        """Test getting tick size for NQ."""
        assert get_tick_size_safe("NQ") == 0.25

    def test_get_tick_size_mnq(self):
        """Test getting tick size for MNQ."""
        assert get_tick_size_safe("MNQ") == 0.25

    def test_get_tick_size_ym(self):
        """Test getting tick size for YM."""
        assert get_tick_size_safe("YM") == 1.00

    def test_unknown_symbol_raises(self):
        """Test unknown symbol raises UnitsError."""
        with pytest.raises(UnitsError):
            get_tick_size_safe("UNKNOWN")


class TestGetTickEconomicsAndValues:
    """Test get_tick_economics_and_values - convenience function."""

    def test_get_all_values_nq(self):
        """Test getting all values for NQ in one call."""
        tick_info, tick_value, tick_size = get_tick_economics_and_values("NQ")

        assert tick_info == {"size": 0.25, "tick_value": 5.00}
        assert tick_value == 5.00
        assert tick_size == 0.25

    def test_get_all_values_es(self):
        """Test getting all values for ES in one call."""
        tick_info, tick_value, tick_size = get_tick_economics_and_values("ES")

        assert tick_info == {"size": 0.25, "tick_value": 12.50}
        assert tick_value == 12.50
        assert tick_size == 0.25

    def test_unknown_symbol_raises(self):
        """Test unknown symbol raises UnitsError."""
        with pytest.raises(UnitsError):
            get_tick_economics_and_values("UNKNOWN")


class TestValidateSymbolKnown:
    """Test validate_symbol_known - validation at boundaries."""

    def test_validate_known_symbol(self):
        """Test validating known symbol (no exception)."""
        validate_symbol_known("NQ")
        validate_symbol_known("ES")
        validate_symbol_known("MNQ")
        # If we get here, validation passed

    def test_validate_unknown_symbol_raises(self):
        """Test validating unknown symbol raises UnitsError."""
        with pytest.raises(UnitsError):
            validate_symbol_known("UNKNOWN")

    def test_validate_empty_symbol_raises(self):
        """Test validating empty symbol raises MappingError."""
        with pytest.raises(MappingError):
            validate_symbol_known("")


class TestErrorMessages:
    """Test error messages are clear and actionable."""

    def test_units_error_lists_known_symbols(self):
        """Test UnitsError includes list of known symbols."""
        with pytest.raises(UnitsError) as exc_info:
            get_tick_economics_safe("FOO")

        error_msg = str(exc_info.value)
        # Should list ALL known symbols
        for symbol in TICK_VALUES.keys():
            assert symbol in error_msg

    def test_units_error_shows_normalization(self):
        """Test UnitsError shows normalized symbol."""
        with pytest.raises(UnitsError) as exc_info:
            get_tick_economics_safe("ENQ123")

        error_msg = str(exc_info.value)
        assert "Unknown symbol: ENQ123" in error_msg
        # ENQ normalizes to NQ, but ENQ123 doesn't match any alias
        assert "normalized: ENQ123" in error_msg


class TestNoSilentFallbacks:
    """Test that there are NO silent fallbacks (defense test)."""

    def test_no_default_fallback_in_get_tick_economics_safe(self):
        """
        Test that get_tick_economics_safe raises on unknown symbol
        rather than returning a default value.
        """
        # This is a defense test - ensure we NEVER add silent fallbacks
        with pytest.raises(UnitsError):
            get_tick_economics_safe("DEFINITELY_UNKNOWN_SYMBOL")

    def test_no_zero_fallback_in_get_tick_value_safe(self):
        """
        Test that get_tick_value_safe raises on unknown symbol
        rather than returning 0.0.
        """
        with pytest.raises(UnitsError):
            get_tick_value_safe("UNKNOWN")

    def test_no_default_tick_size_fallback(self):
        """
        Test that get_tick_size_safe raises on unknown symbol
        rather than returning 0.25.
        """
        with pytest.raises(UnitsError):
            get_tick_size_safe("UNKNOWN")


class TestKnownSymbols:
    """Test that all expected symbols are in TICK_VALUES."""

    def test_all_common_futures_present(self):
        """Test all common futures are in TICK_VALUES."""
        expected_symbols = ["NQ", "MNQ", "ES", "MES", "YM", "MYM", "RTY", "M2K"]

        for symbol in expected_symbols:
            assert symbol in TICK_VALUES, f"Missing expected symbol: {symbol}"

    def test_tick_values_structure(self):
        """Test all TICK_VALUES entries have required structure."""
        for symbol, tick_info in TICK_VALUES.items():
            assert "size" in tick_info, f"{symbol} missing 'size'"
            assert "tick_value" in tick_info, f"{symbol} missing 'tick_value'"
            assert tick_info["size"] > 0, f"{symbol} size must be > 0"
            assert tick_info["tick_value"] > 0, f"{symbol} tick_value must be > 0"

    def test_aliases_point_to_known_symbols(self):
        """Test all aliases resolve to symbols in TICK_VALUES."""
        for alias, target in ALIASES.items():
            assert target in TICK_VALUES, f"Alias {alias} -> {target} but {target} not in TICK_VALUES"
