"""Canonical domain model for risk management."""

from risk_manager.domain.types import (
    Money,
    Position,
    Side,
    Order,
    OrderType,
    OrderStatus,
)
from risk_manager.domain.validators import (
    ValidationError,
    UnitsError,
    SignConventionError,
    QuantityError,
    PriceError,
    EventInvariantsError,
    validate_position,
    validate_pnl_sign,
    validate_order_price_alignment,
    validate_quantity_sign,
    validate_event_data_consistency,
    validate_position_consistency,
)

__all__ = [
    # Types
    "Money",
    "Position",
    "Side",
    "Order",
    "OrderType",
    "OrderStatus",
    # Validators (exceptions)
    "ValidationError",
    "UnitsError",
    "SignConventionError",
    "QuantityError",
    "PriceError",
    "EventInvariantsError",
    # Validators (functions)
    "validate_position",
    "validate_pnl_sign",
    "validate_order_price_alignment",
    "validate_quantity_sign",
    "validate_event_data_consistency",
    "validate_position_consistency",
]
