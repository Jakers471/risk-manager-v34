"""
Risk Manager exception hierarchy.

These exceptions are designed to fail loud and prevent silent errors
from propagating through the system.
"""


class RiskManagerError(Exception):
    """Base exception for all risk manager errors."""

    pass


class MappingError(RiskManagerError):
    """
    Raised when SDK data cannot be mapped to canonical types.

    Examples:
        - Required field missing from SDK event
        - Field has unexpected type or format
        - Cannot parse contract ID or symbol
    """

    pass


class UnitsError(RiskManagerError):
    """
    Raised when tick economics (size/value) are unknown for a symbol.

    This prevents silent fallback to 0.0 which would make P&L
    calculations invisibly wrong.
    """

    pass


class SignConventionError(RiskManagerError):
    """
    Raised when P&L sign doesn't match position side.

    Examples:
        - Long position with positive unrealized P&L but price went down
        - Short position with negative unrealized P&L but price went up

    This catches data integrity issues early.
    """

    pass


class ConfigError(RiskManagerError):
    """
    Raised when configuration is invalid or incomplete.

    Examples:
        - Missing required config field
        - Invalid value type or range
        - Conflicting configuration
    """

    pass


class EnforcementError(RiskManagerError):
    """
    Raised when enforcement action cannot be executed.

    Examples:
        - Cannot close position (SDK error)
        - Cannot place protective order
        - SDK connection lost during enforcement
    """

    pass
