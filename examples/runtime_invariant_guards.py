"""Example: Using Runtime Invariant Guards to Catch Mapping Bugs Early.

This example demonstrates how to integrate runtime invariant guards into
the risk management system to validate data at ingestion points.

Guards fail fast with clear error messages when data is inconsistent,
helping debug SDK mapping issues before they reach rule evaluation.

Example Scenarios:
  1. Unknown symbol (contract ID → symbol mapping bug)
  2. Price not aligned to tick (exchange feed corruption or order submission bug)
  3. P&L sign mismatch (side reversal or exit price source bug)
  4. Missing event fields (incomplete data from exchange)
"""

from decimal import Decimal
from loguru import logger

from risk_manager.domain import (
    Money,
    Position,
    Side,
    UnitsError,
    SignConventionError,
    PriceError,
    ValidationError,
    validate_position,
    validate_pnl_sign,
    validate_order_price_alignment,
    validate_event_data_consistency,
)
from risk_manager.integrations.trading import TICK_VALUES


def example_1_unknown_symbol_caught():
    """Example 1: Catch unknown symbol (mapping bug)."""
    logger.info("=" * 80)
    logger.info("Example 1: Unknown Symbol Detection")
    logger.info("=" * 80)

    # Scenario: Contract ID mapping failed, symbol became "UNKNOWN"
    position = Position(
        symbol_root="UNKNOWN",  # BUG: Should be MNQ, NQ, ES, etc.
        contract_id="CON.F.US.UNKNOWN.Z25",
        side=Side.LONG,
        quantity=1,
        entry_price=Decimal("26385.50"),
        unrealized_pnl=Money(amount=Decimal("0.00")),
    )

    try:
        validate_position(position, TICK_VALUES)
    except UnitsError as e:
        logger.error(f"CAUGHT: {e}")
        logger.info(f"Action: Check contract ID mapping in SDK integration")
        logger.info(f"Details: {e}")
        return True

    return False


def example_2_price_misalignment_caught():
    """Example 2: Catch price not aligned to tick size."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("Example 2: Price Tick Misalignment Detection")
    logger.info("=" * 80)

    # Scenario: Order filled at price that doesn't match tick size
    # MNQ tick size is 0.25, so valid prices end in .00, .25, .50, .75
    position = Position(
        symbol_root="MNQ",
        contract_id="CON.F.US.MNQ.Z25",
        side=Side.LONG,
        quantity=1,
        entry_price=Decimal("26385.33"),  # BUG: 0.33 is not aligned to 0.25
        unrealized_pnl=Money(amount=Decimal("0.00")),
    )

    try:
        validate_position(position, TICK_VALUES)
    except UnitsError as e:
        logger.error(f"CAUGHT: {e}")
        logger.info(f"Action: Check exchange feed or order submission")
        logger.info(f"This usually indicates corrupted market data or SDK bug")
        return True

    return False


def example_3_pnl_sign_mismatch_caught():
    """Example 3: Catch P&L sign mismatch (side reversal bug)."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("Example 3: P&L Sign Mismatch Detection")
    logger.info("=" * 80)

    # Scenario: LONG position, price went up, but P&L is negative (sign bug)
    entry_price = 26300.00
    exit_price = 26350.00  # Price went UP $50
    pnl = Money(amount=Decimal("-50.00"))  # BUG: P&L is negative (should be positive)

    logger.info(f"Entry: ${entry_price:,.2f}")
    logger.info(f"Exit: ${exit_price:,.2f}")
    logger.info(f"Price movement: UP ${exit_price - entry_price:,.2f}")
    logger.info(f"P&L reported: {pnl} (negative)")

    try:
        validate_pnl_sign(
            side=Side.LONG,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl=pnl,
            tick_size=0.25,
        )
    except SignConventionError as e:
        logger.error(f"CAUGHT: {e}")
        logger.info(f"Action: Check P&L calculation code")
        logger.info(
            f"Possible causes:"
        )
        logger.info(f"  1. Side was reversed (LONG reported as SHORT)")
        logger.info(f"  2. Exit price from wrong order")
        logger.info(f"  3. Entry price calculated from close instead of fill")
        return True

    return False


def example_4_incomplete_event_caught():
    """Example 4: Catch incomplete event data."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("Example 4: Incomplete Event Detection")
    logger.info("=" * 80)

    # Scenario: Event missing required fields
    incomplete_event = {
        "contractId": "CON.F.US.MNQ.Z25",
        "size": 1,
        # BUG: Missing 'averagePrice' field
    }

    required_fields = ["contractId", "size", "averagePrice"]

    try:
        validate_event_data_consistency(
            event_type="position_opened",
            event_data=incomplete_event,
            required_fields=required_fields,
        )
    except ValidationError as e:
        logger.error(f"CAUGHT: {e}")
        logger.info(f"Action: Check SDK event structure")
        logger.info(f"Possible causes:")
        logger.info(f"  1. SDK version mismatch")
        logger.info(f"  2. Event subscription filtering wrong fields")
        logger.info(f"  3. Exchange doesn't provide this field for this event")
        return True

    return False


def example_5_order_price_validation():
    """Example 5: Validate order prices at submission."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("Example 5: Order Price Validation")
    logger.info("=" * 80)

    # Scenario: Stop loss order with misaligned price
    symbol = "ES"
    price = 5850.33  # ES tick size is 0.25, so this is invalid

    logger.info(f"Symbol: {symbol}")
    logger.info(f"Price: ${price}")
    logger.info(f"Tick size: {TICK_VALUES[symbol]['size']}")

    try:
        validate_order_price_alignment(
            symbol_root=symbol,
            price=price,
            tick_table=TICK_VALUES,
            order_type="stop",
        )
    except UnitsError as e:
        logger.error(f"CAUGHT: {e}")
        logger.info(f"Action: Round order price to valid tick multiple")
        logger.info(f"Suggested price: 5850.25 or 5850.50")
        return True

    return False


def example_6_integration_in_event_pipeline():
    """Example 6: Integrate guards into event processing pipeline."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("Example 6: Integration in Event Pipeline")
    logger.info("=" * 80)

    # This is how guards would be integrated in core/engine.py

    # Simulated event from SDK
    sdk_event = {
        "contractId": "CON.F.US.MNQ.Z25",
        "size": 1,
        "averagePrice": 26385.50,
        "type": 1,  # 1 = LONG
        "unrealizedPnl": 100.00,
    }

    logger.info(f"Received event from SDK: position_opened")
    logger.info(f"Event data: {sdk_event}")

    # Step 1: Validate event has required fields
    logger.info("\nStep 1: Validate event completeness...")
    try:
        validate_event_data_consistency(
            event_type="position_opened",
            event_data=sdk_event,
            required_fields=["contractId", "size", "averagePrice", "type"],
        )
        logger.info("  ✓ Event has all required fields")
    except ValidationError as e:
        logger.error(f"  ✗ Event incomplete: {e}")
        return False

    # Step 2: Create Position object from event
    logger.info("Step 2: Create Position from event...")
    try:
        position = Position(
            symbol_root="MNQ",  # Would be extracted from contractId
            contract_id=sdk_event["contractId"],
            side=Side.LONG if sdk_event["type"] == 1 else Side.SHORT,
            quantity=sdk_event["size"],
            entry_price=Decimal(str(sdk_event["averagePrice"])),
            unrealized_pnl=Money(amount=Decimal(str(sdk_event["unrealizedPnl"]))),
        )
        logger.info("  ✓ Position object created")
    except Exception as e:
        logger.error(f"  ✗ Position creation failed: {e}")
        return False

    # Step 3: Validate position invariants
    logger.info("Step 3: Validate position invariants...")
    try:
        validate_position(position, TICK_VALUES)
        logger.info("  ✓ Position invariants valid")
    except (UnitsError, PriceError) as e:
        logger.error(f"  ✗ Position invariant violation: {e}")
        return False

    # Step 4: Safe to proceed with rule evaluation
    logger.info("\nStep 4: Proceed with rule evaluation")
    logger.info("  All invariants validated, data is safe for processing")
    return True


def example_7_showing_error_details():
    """Example 7: How error messages help debugging."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("Example 7: Error Message Detail for Debugging")
    logger.info("=" * 80)

    # Show what developers see when debugging
    logger.info("When a bug occurs, the error message tells you exactly what's wrong:")
    logger.info("")

    position = Position(
        symbol_root="BADTICKER",
        contract_id="CON.F.US.BADTICKER.Z25",
        side=Side.LONG,
        quantity=1,
        entry_price=Decimal("1000.00"),
        unrealized_pnl=Money(amount=Decimal("0.00")),
    )

    try:
        validate_position(position, TICK_VALUES)
    except UnitsError as error:
        logger.info(f"Error message:\n{str(error)}\n")
        logger.info("This tells you:")
        logger.info("  1. What failed: Unknown symbol BADTICKER")
        logger.info("  2. What's valid: Known symbols are [MNQ, ES, NQ, YM, ...]")
        logger.info("  3. Why it happened: Likely mapping bug in contract → symbol conversion")
        logger.info("  4. Where to look: SDK integration's symbol extraction code")


def main():
    """Run all examples."""
    logger.info("\n\n")
    logger.info(
        "Runtime Invariant Guards: Catching Mapping Bugs Early"
    )
    logger.info(
        "=" * 80
    )
    logger.info("")

    examples = [
        example_1_unknown_symbol_caught,
        example_2_price_misalignment_caught,
        example_3_pnl_sign_mismatch_caught,
        example_4_incomplete_event_caught,
        example_5_order_price_validation,
        example_6_integration_in_event_pipeline,
        example_7_showing_error_details,
    ]

    results = []
    for example in examples:
        try:
            result = example()
            results.append((example.__name__, result))
        except Exception as e:
            logger.error(f"Example {example.__name__} failed: {e}")
            results.append((example.__name__, False))

    # Summary
    logger.info("")
    logger.info("")
    logger.info("=" * 80)
    logger.info("Summary")
    logger.info("=" * 80)
    for name, result in results:
        status = "✓ CAUGHT" if result else "✗ MISSED"
        logger.info(f"{status}: {name}")

    logger.info("")
    logger.info("Key Takeaways:")
    logger.info("  1. Invariant guards validate data at ingestion points")
    logger.info("  2. They catch mapping bugs before rule evaluation")
    logger.info("  3. Clear error messages make debugging faster")
    logger.info("  4. Integration is simple: just call validator before processing")


if __name__ == "__main__":
    main()
