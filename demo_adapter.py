"""
Demonstration of SDK Adapter in Shadow Mode.

This script shows how the adapter converts SDK position events
to canonical domain types without breaking existing code.
"""

from risk_manager.integrations.adapters import adapter
from risk_manager.errors import MappingError, UnitsError

print("=" * 70)
print("SDK ADAPTER DEMONSTRATION - SHADOW MODE")
print("=" * 70)
print()

# Example 1: Symbol Normalization
print("1. SYMBOL NORMALIZATION")
print("-" * 70)
print("  ENQ -> NQ (alias)")
result = adapter.normalize_symbol("ENQ")
print(f"  Result: {result}")
print()

print("  CON.F.US.MNQ.Z25 -> MNQ (contract extraction)")
result = adapter.normalize_symbol("CON.F.US.MNQ.Z25")
print(f"  Result: {result}")
print()

# Example 2: Tick Economics
print("2. TICK ECONOMICS (Fail Loud - No Silent Fallback)")
print("-" * 70)
print("  ES tick economics:")
result = adapter.get_tick_economics("ES")
print(f"  Result: {result}")
print()

print("  Unknown symbol (raises UnitsError):")
try:
    adapter.get_tick_economics("UNKNOWN")
except UnitsError as e:
    print(f"  * Error raised: {e}")
print()

# Example 3: Position Normalization
print("3. POSITION NORMALIZATION (SDK → Canonical)")
print("-" * 70)

# Simulate SDK position event
sdk_position = {
    "contractId": "CON.F.US.MNQ.Z25",
    "avgPrice": 21000.00,
    "size": 2,
    "type": 1,  # 1 = LONG
}

print("  SDK Position (raw):")
print(f"    contractId: {sdk_position['contractId']}")
print(f"    avgPrice: {sdk_position['avgPrice']}")
print(f"    size: {sdk_position['size']}")
print(f"    type: {sdk_position['type']} (1=LONG, 2=SHORT)")
print()

# Convert to canonical Position
canonical_position = adapter.normalize_position_from_dict(
    sdk_position,
    current_price=21010.00,  # +$10 profit
)

print("  Canonical Position (normalized):")
print(f"    symbol_root: {canonical_position.symbol_root}")
print(f"    contract_id: {canonical_position.contract_id}")
print(f"    side: {canonical_position.side.value.upper()}")
print(f"    quantity: {canonical_position.quantity}")
print(f"    entry_price: ${canonical_position.entry_price}")
print(f"    unrealized_pnl: {canonical_position.unrealized_pnl}")
print()

# Example 4: P&L Calculation
print("4. P&L CALCULATION (Automatic)")
print("-" * 70)
print("  MNQ Long 2 @ 21000.00")
print("  Current price: 21010.00 (+10 points)")
print("  Calculation:")
print("    - 10 points / 0.25 tick size = 40 ticks")
print("    - 40 ticks × 2 contracts × $0.50 tick value = $40 profit")
print(f"  Result: {canonical_position.unrealized_pnl}")
print()

# Example 5: Short Position
print("5. SHORT POSITION (Inverted P&L)")
print("-" * 70)

short_position = {
    "contractId": "CON.F.US.MNQ.Z25",
    "avgPrice": 21000.00,
    "size": -2,
    "type": 2,  # 2 = SHORT
}

canonical_short = adapter.normalize_position_from_dict(
    short_position,
    current_price=20990.00,  # Price down = profit for short
)

print("  SDK Position:")
print(f"    size: {short_position['size']} (negative = short)")
print(f"    type: {short_position['type']} (2=SHORT)")
print()

print("  Canonical Position:")
print(f"    side: {canonical_short.side.value.upper()}")
print(f"    quantity: {canonical_short.quantity} (always positive)")
print(f"    unrealized_pnl: {canonical_short.unrealized_pnl}")
print()

# Example 6: Fail Loud - Missing Fields
print("6. FAIL LOUD - Missing Required Fields")
print("-" * 70)

bad_position = {
    "avgPrice": 21000.00,
    "size": 2,
    # Missing contractId!
}

print("  SDK Position (missing contractId):")
try:
    adapter.normalize_position_from_dict(bad_position)
except MappingError as e:
    print(f"  * Error raised: {e}")
print()

# Example 7: Symbol Alias (ENQ → NQ)
print("7. SYMBOL ALIAS HANDLING")
print("-" * 70)

enq_position = {
    "contractId": "CON.F.US.ENQ.Z25",
    "avgPrice": 20000.00,
    "size": 1,
    "type": 1,
}

canonical_enq = adapter.normalize_position_from_dict(
    enq_position,
    current_price=20005.00,
)

print("  SDK Position:")
print(f"    contractId: {enq_position['contractId']} (ENQ)")
print()

print("  Canonical Position:")
print(f"    symbol_root: {canonical_enq.symbol_root} (normalized to NQ)")
print(f"    contract_id: {canonical_enq.contract_id} (preserves original)")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("* Symbol normalization: ENQ -> NQ")
print("* Tick economics: Lookup succeeds, unknown symbols raise UnitsError")
print("* Position normalization: SDK fields → canonical types")
print("* P&L calculation: Automatic based on tick economics")
print("* Fail loud: Missing fields raise MappingError")
print("* Shadow mode: Existing event.data still works!")
print()
print("Next step: Rules can access event.position for type safety")
print("=" * 70)
