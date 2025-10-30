"""Runtime invariant guards for risk management.

This module provides runtime validation to catch mapping bugs early by validating
invariants at data ingestion points. Guards fail fast with clear error messages.

Design:
  1. Position Invariants - Validate symbol, quantity, price alignment
  2. P&L Sign Invariants - Validate profit/loss direction matches trade direction
  3. Order Invariants - Validate order prices and quantities
  4. Event Invariants - Validate event data consistency

Usage:
  Guards are integrated into the event pipeline in core/engine.py and
  integrations/trading.py to validate data BEFORE rule evaluation.

Example:
  from risk_manager.domain.validators import validate_position
  from risk_manager.domain.types import Position, Side, Money
  from risk_manager.integrations.trading import TICK_VALUES

  try:
      validate_position(position, TICK_VALUES)
  except UnitsError as e:
      logger.error(f"Position invariant violated: {e}")
      # Emit alert, skip rule evaluation
"""

from decimal import Decimal
from typing import Any

from risk_manager.domain.types import Money, Position, Side


class ValidationError(Exception):
    """Base exception for invariant violations."""

    pass


class UnitsError(ValidationError):
    """Error for unit/tick alignment violations."""

    pass


class SignConventionError(ValidationError):
    """Error for sign/direction convention violations."""

    pass


class QuantityError(ValidationError):
    """Error for quantity invariants."""

    pass


class PriceError(ValidationError):
    """Error for price invariants."""

    pass


class EventInvariantsError(ValidationError):
    """Error for event invariant violations."""

    pass


def validate_position(position: Position, tick_table: dict[str, dict]) -> None:
    """Validate position invariants.

    Checks:
      1. Symbol exists in tick table
      2. Quantity is positive integer
      3. Entry price aligns to tick size
      4. Price is positive

    Args:
        position: Position to validate
        tick_table: Dictionary mapping symbols to {"size": tick_size, "tick_value": value}

    Raises:
        UnitsError: If symbol unknown or price not aligned to tick
        QuantityError: If quantity invalid
        PriceError: If price invalid
    """
    # 1. Symbol must exist in tick table
    if position.symbol_root not in tick_table:
        available = list(tick_table.keys())
        raise UnitsError(
            f"Unknown symbol: {position.symbol_root}. "
            f"Known symbols: {available}. "
            f"This likely means a mapping bug (contract ID → symbol conversion failed)."
        )

    # 2. Quantity must be positive integer
    if not isinstance(position.quantity, int) or position.quantity <= 0:
        raise QuantityError(
            f"Invalid quantity for {position.symbol_root}: {position.quantity}. "
            f"Quantity must be positive integer (got {type(position.quantity).__name__})."
        )

    # 3. Entry price must be positive
    entry_price_decimal = Decimal(str(position.entry_price))
    if entry_price_decimal <= 0:
        raise PriceError(
            f"Invalid entry price for {position.symbol_root}: ${entry_price_decimal}. "
            f"Price must be positive."
        )

    # 4. Entry price must align to tick size
    tick_size = tick_table[position.symbol_root]["size"]
    tick_decimal = Decimal(str(tick_size))

    remainder = entry_price_decimal % tick_decimal
    if remainder != 0:
        raise UnitsError(
            f"Price not aligned to tick for {position.symbol_root}: "
            f"${entry_price_decimal} is not a multiple of tick size {tick_size}. "
            f"(remainder: {remainder}). "
            f"This likely means an exchange mapping bug or feed corruption."
        )


def validate_pnl_sign(
    side: Side,
    entry_price: float,
    exit_price: float,
    pnl: Money,
    tick_size: float,
    tolerance: float = 0.01,
) -> None:
    """Validate P&L sign matches trade direction.

    Checks that realized P&L direction (profit/loss) matches trade direction:
      - LONG: exit > entry → profit (positive P&L)
      - LONG: exit < entry → loss (negative P&L)
      - SHORT: entry > exit → profit (positive P&L)
      - SHORT: entry < exit → loss (negative P&L)

    Args:
        side: Trade direction (LONG or SHORT)
        entry_price: Entry price in dollars
        exit_price: Exit price in dollars
        pnl: Realized P&L in Money object
        tick_size: Tick size for this symbol (to calculate expected direction)
        tolerance: Tolerance for sign check (default 0.01 to handle rounding)

    Raises:
        SignConventionError: If P&L sign doesn't match direction

    Example:
        # LONG position: paid $26,300, sold at $26,350 → profit
        validate_pnl_sign(
            side=Side.LONG,
            entry_price=26300.00,
            exit_price=26350.00,
            pnl=Money(amount=Decimal("50.00")),
            tick_size=0.25
        )
        # ✅ Passes: LONG + exit > entry + positive P&L = consistent

        # SHORT position: shorted at $26,350, covered at $26,300 → profit
        validate_pnl_sign(
            side=Side.SHORT,
            entry_price=26350.00,
            exit_price=26300.00,
            pnl=Money(amount=Decimal("50.00")),
            tick_size=0.25
        )
        # ✅ Passes: SHORT + entry > exit + positive P&L = consistent
    """
    price_diff = exit_price - entry_price
    is_profitable = price_diff > 0

    # Convert Money amount to Decimal for comparison
    pnl_amount = Decimal(str(pnl.amount))
    tolerance_decimal = Decimal(str(tolerance))

    if side == Side.LONG:
        expected_profitable = is_profitable
        if expected_profitable != (pnl_amount > tolerance_decimal):
            raise SignConventionError(
                f"LONG position P&L sign mismatch: "
                f"Entry ${entry_price:,.2f} → Exit ${exit_price:,.2f} "
                f"(diff: ${price_diff:,.2f}, should be {'profitable' if is_profitable else 'loss'}) "
                f"but P&L shows {pnl} "
                f"(sign: {'positive' if pnl_amount > tolerance_decimal else 'negative/zero'}). "
                f"This likely indicates: exit price source bug, side reversal, "
                f"or entry price from wrong order."
            )

    elif side == Side.SHORT:
        expected_profitable = entry_price > exit_price
        if expected_profitable != (pnl_amount > tolerance_decimal):
            raise SignConventionError(
                f"SHORT position P&L sign mismatch: "
                f"Entry ${entry_price:,.2f} → Exit ${exit_price:,.2f} "
                f"(entry > exit: {entry_price > exit_price}, should be {'profitable' if expected_profitable else 'loss'}) "
                f"but P&L shows {pnl} "
                f"(sign: {'positive' if pnl_amount > tolerance_decimal else 'negative/zero'}). "
                f"This likely indicates: side reversal, exit price from wrong order, "
                f"or entry price corruption."
            )


def validate_order_price_alignment(
    symbol_root: str,
    price: float,
    tick_table: dict[str, dict],
    order_type: str = "limit",
) -> None:
    """Validate order price aligns to tick size.

    Args:
        symbol_root: Symbol name (e.g., "MNQ", "ES")
        price: Order price in dollars
        tick_table: Dictionary mapping symbols to {"size": tick_size, ...}
        order_type: Type of order ("limit", "stop", "market")

    Raises:
        UnitsError: If price not aligned to tick size
        PriceError: If price invalid for order type
    """
    if symbol_root not in tick_table:
        available = list(tick_table.keys())
        raise UnitsError(
            f"Unknown symbol in order price validation: {symbol_root}. "
            f"Known symbols: {available}."
        )

    if price <= 0:
        raise PriceError(f"Invalid order price: ${price} (must be positive).")

    if order_type in ("limit", "stop"):
        tick_size = tick_table[symbol_root]["size"]
        price_decimal = Decimal(str(price))
        tick_decimal = Decimal(str(tick_size))

        remainder = price_decimal % tick_decimal
        if remainder != 0:
            raise UnitsError(
                f"Order price not aligned to tick: ${price} "
                f"(symbol: {symbol_root}, tick: {tick_size}). "
                f"Remainder: {remainder}. "
                f"This indicates exchange feed corruption or order submission bug."
            )


def validate_quantity_sign(quantity: int, side: Side) -> None:
    """Validate quantity sign matches side.

    Some systems expect:
      - LONG: positive quantity
      - SHORT: negative quantity

    This validator ensures consistency if side is embedded in quantity sign.

    Args:
        quantity: Quantity (may be signed)
        side: Expected trade direction

    Raises:
        SignConventionError: If quantity sign doesn't match side
    """
    if quantity == 0:
        raise QuantityError("Quantity cannot be zero.")

    quantity_is_long = quantity > 0
    side_is_long = side == Side.LONG

    if quantity_is_long != side_is_long:
        raise SignConventionError(
            f"Quantity sign mismatch: quantity={quantity} "
            f"(side: {'long' if quantity_is_long else 'short'}) "
            f"but side={side}. "
            f"This indicates a sign convention bug in order/position mapping."
        )


def validate_event_data_consistency(
    event_type: str,
    event_data: dict[str, Any],
    required_fields: list[str],
) -> None:
    """Validate event has required fields and types.

    Args:
        event_type: Type of event (e.g., "position_opened", "order_filled")
        event_data: Event data dictionary
        required_fields: List of required field names

    Raises:
        ValidationError: If required fields missing or None
    """
    for field in required_fields:
        if field not in event_data:
            raise ValidationError(
                f"Missing required field '{field}' in {event_type} event. "
                f"Available fields: {list(event_data.keys())}. "
                f"This indicates incomplete event mapping from exchange API."
            )

        if event_data[field] is None:
            raise ValidationError(
                f"Required field '{field}' is None in {event_type} event. "
                f"This indicates incomplete data in exchange response."
            )


def validate_position_consistency(
    position_id: str,
    size: int,
    entry_price: float,
    current_price: float,
    unrealized_pnl: float,
    side: Side,
    tolerance: float = 1.0,
) -> None:
    """Validate position P&L is consistent with prices.

    For positions not yet closed, unrealized P&L should be roughly:
      LONG: (current - entry) * size * tick_value
      SHORT: (entry - current) * size * tick_value

    This catches cases where unrealized P&L is from a different position
    or exchange data is corrupted.

    Args:
        position_id: Position identifier for error messages
        size: Position size
        entry_price: Entry price
        current_price: Current market price
        unrealized_pnl: Reported unrealized P&L
        side: Trade direction
        tolerance: Tolerance in dollars for rounding differences

    Raises:
        SignConventionError: If P&L sign is wrong for direction
    """
    price_diff = current_price - entry_price

    if side == Side.LONG:
        should_be_profit = price_diff > 0
    else:  # SHORT
        should_be_profit = price_diff < 0

    actually_profit = unrealized_pnl > 0

    if should_be_profit != actually_profit and abs(unrealized_pnl) > tolerance:
        raise SignConventionError(
            f"Unrealized P&L sign inconsistent for position {position_id}: "
            f"{side.value.upper()} position with "
            f"entry ${entry_price:,.2f} and current ${current_price:,.2f} "
            f"should be {'profitable' if should_be_profit else 'loss'} "
            f"but unrealized P&L shows ${unrealized_pnl:,.2f}. "
            f"This indicates: side reversal, prices from different sources, "
            f"or exchange data corruption."
        )


# Registry of common invariant checks
POSITION_INVARIANTS = [
    "symbol_exists",
    "quantity_positive",
    "price_positive",
    "price_tick_aligned",
]

PNL_INVARIANTS = [
    "sign_matches_direction",
    "magnitude_reasonable",
]

ORDER_INVARIANTS = [
    "price_tick_aligned",
    "quantity_positive",
    "price_positive",
]

EVENT_INVARIANTS = [
    "required_fields_present",
    "data_types_correct",
]
