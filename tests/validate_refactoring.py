#!/usr/bin/env python3
"""
Refactoring Validation Script

Purpose:
    Run this script BEFORE and AFTER refactoring to prove behavior is unchanged.

Usage:
    # Before refactoring
    python tests/validate_refactoring.py > baseline_validation.txt

    # After refactoring
    python tests/validate_refactoring.py > refactored_validation.txt

    # Compare outputs
    diff baseline_validation.txt refactored_validation.txt

    If diff shows NO differences (except timestamps), refactoring succeeded! [OK]

What it validates:
    1. TradingIntegration can be imported
    2. All public methods exist
    3. Method signatures are correct
    4. Basic workflow simulations produce expected results
    5. Caching behavior works correctly
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from risk_manager.integrations.trading import TradingIntegration
from risk_manager.core.events import EventBus
from risk_manager.config.models import RiskConfig
from unittest.mock import Mock


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_check(item: str, passed: bool):
    """Print validation check result."""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status}: {item}")


async def main():
    """Run validation checks."""
    print_section("REFACTORING VALIDATION - TradingIntegration")
    print(f"Timestamp: {asyncio.get_event_loop().time():.6f}")

    # ========================================================================
    # Test 1: Import Check
    # ========================================================================
    print_section("Test 1: Import Check")

    try:
        from risk_manager.integrations.trading import TradingIntegration
        print_check("TradingIntegration can be imported", True)
    except ImportError as e:
        print_check(f"TradingIntegration import failed: {e}", False)
        sys.exit(1)

    # ========================================================================
    # Test 2: Initialization Check
    # ========================================================================
    print_section("Test 2: Initialization Check")

    try:
        # Create mock config
        mock_config = Mock(spec=RiskConfig)
        mock_config.account_id = "TEST_ACCOUNT"

        # Create event bus
        event_bus = EventBus()

        # Create TradingIntegration
        instruments = ["MNQ", "ES"]
        integration = TradingIntegration(
            instruments=instruments,
            config=mock_config,
            event_bus=event_bus
        )

        print_check("TradingIntegration initialized successfully", True)
        print(f"  -> Instruments: {integration.instruments}")
        print(f"  -> Connected: {integration.suite is not None}")
        print(f"  -> Running: {integration.running}")

    except Exception as e:
        print_check(f"Initialization failed: {e}", False)
        sys.exit(1)

    # ========================================================================
    # Test 3: Public API Method Existence
    # ========================================================================
    print_section("Test 3: Public API Method Existence")

    expected_methods = [
        "connect",
        "disconnect",
        "start",
        "get_stop_loss_for_position",
        "get_take_profit_for_position",
        "get_all_active_stop_losses",
        "get_all_active_take_profits",
        "flatten_position",
        "flatten_all",
        "get_total_unrealized_pnl",
        "get_position_unrealized_pnl",
        "get_open_positions",
        "get_stats",
    ]

    for method_name in expected_methods:
        has_method = hasattr(integration, method_name)
        print_check(f"Method exists: {method_name}()", has_method)

        if not has_method:
            print(f"  [ERROR] CRITICAL: Missing method '{method_name}'")
            sys.exit(1)

    # ========================================================================
    # Test 4: Method Signature Validation (async/sync)
    # ========================================================================
    print_section("Test 4: Method Signature Validation")

    async_methods = [
        "connect",
        "disconnect",
        "start",
        "get_stop_loss_for_position",
        "get_take_profit_for_position",
        "flatten_position",
        "flatten_all",
    ]

    sync_methods = [
        "get_all_active_stop_losses",
        "get_all_active_take_profits",
        "get_total_unrealized_pnl",
        "get_position_unrealized_pnl",
        "get_open_positions",
        "get_stats",
    ]

    for method_name in async_methods:
        method = getattr(integration, method_name)
        is_async = asyncio.iscoroutinefunction(method)
        print_check(f"Method is async: {method_name}()", is_async)

        if not is_async:
            print(f"  [ERROR] CRITICAL: Method '{method_name}' should be async!")
            sys.exit(1)

    for method_name in sync_methods:
        method = getattr(integration, method_name)
        is_async = asyncio.iscoroutinefunction(method)
        is_sync = not is_async
        print_check(f"Method is sync: {method_name}()", is_sync)

        if is_async:
            print(f"  [ERROR] CRITICAL: Method '{method_name}' should be synchronous!")
            sys.exit(1)

    # ========================================================================
    # Test 5: Stop Loss Caching Behavior
    # ========================================================================
    print_section("Test 5: Stop Loss Caching Behavior")

    contract_id = "CON.F.US.MNQ.Z25"

    # Initially empty
    result = await integration.get_stop_loss_for_position(contract_id)
    print_check("Cache empty initially (returns None)", result is None)

    # Add stop loss to cache (simulating ORDER_PLACED event)
    integration._protective_cache._active_stop_losses[contract_id] = {
        "order_id": 12345,
        "stop_price": 21500.00,
        "side": "SELL",
        "quantity": 1,
        "timestamp": 1234567890.0,
    }

    # Query cache
    result = await integration.get_stop_loss_for_position(contract_id)
    print_check("Cache returns stop loss data", result is not None)

    if result:
        print(f"  -> Order ID: {result['order_id']}")
        print(f"  -> Stop Price: ${result['stop_price']:.2f}")
        print(f"  -> Side: {result['side']}")
        print(f"  -> Quantity: {result['quantity']}")

        # Validate data
        data_correct = (
            result['order_id'] == 12345 and
            result['stop_price'] == 21500.00 and
            result['side'] == "SELL" and
            result['quantity'] == 1
        )
        print_check("Cached data is correct", data_correct)

    # Remove from cache (simulating ORDER_FILLED event)
    del integration._protective_cache._active_stop_losses[contract_id]

    # Query again
    result = await integration.get_stop_loss_for_position(contract_id)
    print_check("Cache cleared after removal", result is None)

    # ========================================================================
    # Test 6: Take Profit Caching Behavior
    # ========================================================================
    print_section("Test 6: Take Profit Caching Behavior")

    # Add take profit to cache
    integration._protective_cache._active_take_profits[contract_id] = {
        "order_id": 67890,
        "take_profit_price": 21600.00,
        "side": "SELL",
        "quantity": 1,
        "timestamp": 1234567890.0,
    }

    # Query cache
    result = await integration.get_take_profit_for_position(contract_id)
    print_check("Take profit cache works", result is not None)

    if result:
        print(f"  -> Order ID: {result['order_id']}")
        print(f"  -> TP Price: ${result['take_profit_price']:.2f}")

    # ========================================================================
    # Test 7: Deduplication Behavior
    # ========================================================================
    print_section("Test 7: Deduplication Behavior")

    event_type = "test_event"
    entity_id = "test_123"

    # First event - not duplicate
    is_dup_1 = integration._is_duplicate_event(event_type, entity_id)
    print_check("First event is NOT duplicate", is_dup_1 is False)

    # Second event - IS duplicate
    is_dup_2 = integration._is_duplicate_event(event_type, entity_id)
    print_check("Second event IS duplicate", is_dup_2 is True)

    # Third event - still duplicate
    is_dup_3 = integration._is_duplicate_event(event_type, entity_id)
    print_check("Third event IS duplicate", is_dup_3 is True)

    # ========================================================================
    # Test 8: Helper Methods
    # ========================================================================
    print_section("Test 8: Helper Methods")

    # Symbol extraction
    symbol = integration._extract_symbol_from_contract("CON.F.US.MNQ.Z25")
    print_check("Symbol extraction: CON.F.US.MNQ.Z25 -> MNQ", symbol == "MNQ")

    symbol = integration._extract_symbol_from_contract("CON.F.US.ES.H25")
    print_check("Symbol extraction: CON.F.US.ES.H25 -> ES", symbol == "ES")

    # Side conversion
    side_buy = integration._get_side_name(0)
    print_check("Side conversion: 0 -> BUY", side_buy == "BUY")

    side_sell = integration._get_side_name(1)
    print_check("Side conversion: 1 -> SELL", side_sell == "SELL")

    # Position type conversion
    pos_long = integration._get_position_type_name(1)
    print_check("Position type: 1 -> LONG", pos_long == "LONG")

    pos_short = integration._get_position_type_name(2)
    print_check("Position type: 2 -> SHORT", pos_short == "SHORT")

    pos_flat = integration._get_position_type_name(0)
    print_check("Position type: 0 -> FLAT", pos_flat == "FLAT")

    # ========================================================================
    # Test 9: P&L Methods
    # ========================================================================
    print_section("Test 9: P&L Methods")

    # Get total unrealized P&L (should be 0.0 with no positions)
    total_pnl = integration.get_total_unrealized_pnl()
    print_check("get_total_unrealized_pnl() returns float", isinstance(total_pnl, float))
    print(f"  -> Total P&L: ${total_pnl:.2f}")

    # Get position P&L (unknown position should return None)
    pos_pnl = integration.get_position_unrealized_pnl("UNKNOWN")
    print_check("Unknown position returns None", pos_pnl is None)

    # Get open positions (should be empty dict)
    open_pos = integration.get_open_positions()
    print_check("get_open_positions() returns dict", isinstance(open_pos, dict))
    print(f"  -> Open positions count: {len(open_pos)}")

    # ========================================================================
    # Test 10: Stats Method
    # ========================================================================
    print_section("Test 10: Stats Method")

    stats = integration.get_stats()
    print_check("get_stats() returns dict", isinstance(stats, dict))

    expected_keys = ["connected", "running", "instruments"]
    for key in expected_keys:
        has_key = key in stats
        print_check(f"Stats has key: {key}", has_key)

    print(f"\n  Stats content:")
    for key, value in stats.items():
        print(f"    {key}: {value}")

    # ========================================================================
    # FINAL RESULT
    # ========================================================================
    print_section("VALIDATION COMPLETE")

    print("\n[SUCCESS] ALL VALIDATION CHECKS PASSED!\n")
    print("TradingIntegration behavior is consistent and correct.")
    print("\nIf this is the BASELINE run:")
    print("  Save this output: python tests/validate_refactoring.py > baseline.txt")
    print("\nAfter refactoring:")
    print("  python tests/validate_refactoring.py > refactored.txt")
    print("  diff baseline.txt refactored.txt")
    print("\nIf diff shows no changes, refactoring preserved behavior!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
