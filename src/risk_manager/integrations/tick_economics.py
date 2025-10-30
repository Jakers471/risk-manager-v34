"""
Tick Economics Utilities

Provides safe, fail-fast utilities for working with tick values, tick sizes,
and symbol normalization. All critical lookups raise exceptions on missing data
rather than silently falling back to defaults.

This prevents silent calculation errors in P&L and risk management.
"""

from typing import Dict, Tuple


class UnitsError(Exception):
    """Raised when tick economics are unknown for a symbol."""
    pass


class MappingError(Exception):
    """Raised when symbol or contract mapping fails."""
    pass


# Tick economics for common futures instruments
# Format: {symbol: {"size": tick_size, "tick_value": tick_value_in_dollars}}
TICK_VALUES = {
    "NQ":  {"size": 0.25, "tick_value": 5.00},    # NASDAQ-100 E-mini
    "MNQ": {"size": 0.25, "tick_value": 0.50},    # Micro NASDAQ-100 E-mini
    "ES":  {"size": 0.25, "tick_value": 12.50},   # S&P 500 E-mini
    "MES": {"size": 0.25, "tick_value": 1.25},    # Micro S&P 500 E-mini
    "YM":  {"size": 1.00, "tick_value": 5.00},    # Dow E-mini
    "MYM": {"size": 1.00, "tick_value": 0.50},    # Micro Dow E-mini
    "RTY": {"size": 0.10, "tick_value": 5.00},    # Russell 2000 E-mini
    "M2K": {"size": 0.10, "tick_value": 0.50},    # Micro Russell 2000 E-mini
}

# Symbol aliases (some brokers use different names)
ALIASES = {"ENQ": "NQ"}


def normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol using alias table.

    Args:
        symbol: Raw symbol (e.g., "ENQ", "NQ", "MNQ")

    Returns:
        Normalized symbol (e.g., "ENQ" -> "NQ")
    """
    if not symbol:
        raise MappingError("Symbol cannot be empty")

    return ALIASES.get(symbol, symbol)


def get_tick_economics_safe(symbol: str) -> Dict[str, float]:
    """
    Get tick economics with validation (FAIL FAST).

    Args:
        symbol: Symbol identifier (will be normalized via ALIASES)

    Returns:
        Dictionary with "size" and "tick_value" keys

    Raises:
        UnitsError: If symbol is unknown after normalization
        MappingError: If symbol is empty/invalid
    """
    if not symbol:
        raise MappingError("Symbol cannot be empty")

    # Normalize via aliases
    normalized = normalize_symbol(symbol)

    # Check if we have tick economics
    if normalized not in TICK_VALUES:
        raise UnitsError(
            f"Unknown symbol: {symbol} (normalized: {normalized}). "
            f"Known symbols: {list(TICK_VALUES.keys())}"
        )

    return TICK_VALUES[normalized]


def get_tick_value_safe(symbol: str) -> float:
    """
    Get tick value for symbol (FAIL FAST).

    Args:
        symbol: Symbol identifier

    Returns:
        Tick value in dollars per tick

    Raises:
        UnitsError: If symbol is unknown
    """
    tick_info = get_tick_economics_safe(symbol)
    return tick_info["tick_value"]


def get_tick_size_safe(symbol: str) -> float:
    """
    Get tick size for symbol (FAIL FAST).

    Args:
        symbol: Symbol identifier

    Returns:
        Minimum price increment (tick size)

    Raises:
        UnitsError: If symbol is unknown
    """
    tick_info = get_tick_economics_safe(symbol)
    return tick_info["size"]


def get_tick_economics_and_values(symbol: str) -> Tuple[Dict[str, float], float, float]:
    """
    Get all tick economics in one call (FAIL FAST).

    Convenience function for getting tick info, tick value, and tick size together.

    Args:
        symbol: Symbol identifier

    Returns:
        Tuple of (tick_info_dict, tick_value, tick_size)

    Raises:
        UnitsError: If symbol is unknown
    """
    tick_info = get_tick_economics_safe(symbol)
    return tick_info, tick_info["tick_value"], tick_info["size"]


def validate_symbol_known(symbol: str) -> None:
    """
    Validate that symbol is known (FAIL FAST).

    Useful for validation at boundaries before computation.

    Args:
        symbol: Symbol identifier

    Raises:
        UnitsError: If symbol is unknown
        MappingError: If symbol is empty/invalid
    """
    get_tick_economics_safe(symbol)  # Will raise if unknown
