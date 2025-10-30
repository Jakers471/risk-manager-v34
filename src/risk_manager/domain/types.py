"""
Canonical domain types for risk management.

These types define the "single source of truth" for how the risk manager
views the trading world. All SDK-specific types should be converted to these
canonical forms at the integration boundary.

This prevents SDK field names and conventions from leaking into rules,
making the system more maintainable and testable.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional


class Side(Enum):
    """Position/order side (normalized)."""

    LONG = "long"
    SHORT = "short"

    @classmethod
    def from_sdk_type(cls, sdk_type: int) -> "Side":
        """
        Convert SDK position type to Side enum.

        Args:
            sdk_type: SDK type value (1=LONG, 2=SHORT)

        Returns:
            Side enum value

        Raises:
            ValueError: If sdk_type is not 1 or 2
        """
        if sdk_type == 1:
            return cls.LONG
        elif sdk_type == 2:
            return cls.SHORT
        else:
            raise ValueError(f"Invalid SDK type: {sdk_type}, expected 1 (LONG) or 2 (SHORT)")


class OrderType(Enum):
    """Order type (normalized)."""

    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status (normalized)."""

    PENDING = "pending"
    WORKING = "working"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Money:
    """
    Monetary amount with explicit currency.

    Convention:
        - Positive = profit/credit
        - Negative = loss/debit
    """

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self):
        """Ensure amount is a Decimal."""
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))

    @property
    def is_loss(self) -> bool:
        """Check if this is a loss (negative amount)."""
        return self.amount < 0

    @property
    def is_profit(self) -> bool:
        """Check if this is a profit (positive amount)."""
        return self.amount > 0

    def __str__(self) -> str:
        """Format as currency string."""
        return f"${self.amount:,.2f}"


@dataclass
class Position:
    """
    Canonical position representation.

    Fields are normalized from SDK-specific names to our domain language.
    """

    # Identity
    symbol_root: str  # Normalized symbol (ENQ → NQ)
    contract_id: str  # Full contract identifier (CON.F.US.MNQ.Z25)

    # Position details
    side: Side  # LONG or SHORT (normalized from SDK type)
    quantity: int  # Number of contracts (always positive)
    entry_price: Decimal  # Average entry price

    # P&L
    unrealized_pnl: Money  # Current unrealized P&L

    # Metadata (optional)
    account_id: Optional[str] = None
    timestamp: Optional[float] = None

    def __post_init__(self):
        """Validate position invariants."""
        if self.quantity <= 0:
            raise ValueError(f"Position quantity must be positive, got {self.quantity}")

        if not isinstance(self.entry_price, Decimal):
            self.entry_price = Decimal(str(self.entry_price))

    @property
    def is_long(self) -> bool:
        """Check if this is a long position."""
        return self.side == Side.LONG

    @property
    def is_short(self) -> bool:
        """Check if this is a short position."""
        return self.side == Side.SHORT


@dataclass
class Order:
    """
    Canonical order representation.

    Fields are normalized from SDK-specific names to our domain language.
    """

    # Identity
    order_id: str
    contract_id: str
    symbol_root: str  # Normalized symbol

    # Order details
    side: Side  # LONG or SHORT
    order_type: OrderType
    quantity: int
    status: OrderStatus

    # Prices (optional, depends on order type)
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None

    # Metadata
    timestamp: Optional[float] = None

    def __post_init__(self):
        """Convert prices to Decimal."""
        if self.limit_price is not None and not isinstance(self.limit_price, Decimal):
            self.limit_price = Decimal(str(self.limit_price))

        if self.stop_price is not None and not isinstance(self.stop_price, Decimal):
            self.stop_price = Decimal(str(self.stop_price))

    @property
    def is_stop_loss(self) -> bool:
        """Check if this is a stop loss order."""
        return self.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

    @property
    def is_take_profit(self) -> bool:
        """Check if this is a take profit order (limit order)."""
        return self.order_type == OrderType.LIMIT
