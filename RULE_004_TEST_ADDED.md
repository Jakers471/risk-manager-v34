# RULE-004 Test Added to test_rule_validation.py

## Summary

Successfully added test for RULE-004 (Daily Unrealized Loss) to the rule validation script.

## Changes Made

### 1. Test Method Added

**Location**: `test_rule_validation.py`, line 395

**Method**: `async def test_rule_004_daily_unrealized_loss(self)`

**Test Scenario**:
- Loss limit: -$750 unrealized loss per position
- Opens position: 5 MNQ long @ $21,500
- MNQ tick value: $5 per point
- MNQ tick size: 0.25 points

**Test Events**:
1. **Position opened** at $21,500 → No violation (P&L = $0)
2. **Market price drops to $21,400** → VIOLATION!
   - Price diff: -$100
   - Ticks: -400 ticks
   - P&L: -$10,000 (far below -$750 limit)
3. **Market price drops to $21,300** → Additional violation
   - P&L: -$20,000

**Expected Results**:
- [OK] At least 1 violation detected
- [OK] Arithmetic correct (unrealized P&L < -$750)
- [OK] Enforcement action: `close_position`
- [OK] Symbol to close: MNQ
- [OK] NO lockout (trade-by-trade rule)

### 2. Test Registration

**Location**: `test_rule_validation.py`, line 1238

**Added**:
```python
results["RULE-004"] = await self.test_rule_004_daily_unrealized_loss()
```

**Test Execution Order**:
1. RULE-001: Max Contracts
2. RULE-002: Max Contracts Per Instrument
3. RULE-003: Daily Realized Loss
4. **RULE-004: Daily Unrealized Loss** ← NEW
5. RULE-006: Trade Frequency Limit
6. RULE-009: Session Block Outside Hours
7. RULE-012: Trade Management
8. RULE-013: Daily Realized Profit Target

## Test Pattern Followed

The test follows the established pattern from other rule tests:

```python
async def test_rule_XXX_name(self) -> dict[str, Any]:
    """Docstring with arithmetic test details"""
    
    # 1. Create rule instance with test configuration
    # 2. Create mock engine with positions/prices
    # 3. Inject events and evaluate rule
    # 4. Validate violations and enforcement actions
    # 5. Return test result dict
```

## Files Modified

- **test_rule_validation.py**
  - Added `test_rule_004_daily_unrealized_loss()` method (145 lines)
  - Registered test in `run_all_tests()` method
  - Fixed indentation issue on line 1238

## Verification

```bash
# Syntax check passed
python -m py_compile test_rule_validation.py
# ✓ Success

# Test method exists
grep -n "async def test_rule_004" test_rule_validation.py
# 395:    async def test_rule_004_daily_unrealized_loss(self) -> dict[str, Any]:

# Test registered
grep "RULE-004" test_rule_validation.py
# 1238:        results["RULE-004"] = await self.test_rule_004_daily_unrealized_loss()
```

## Running the Test

```bash
# Run specific test
python test_rule_validation.py --rule RULE-004

# Run all tests
python test_rule_validation.py
```

## Key Implementation Details

### P&L Calculation

The test validates the unrealized P&L calculation formula:

```python
# For long position:
price_diff = current_price - entry_price
ticks = price_diff / tick_size
unrealized_pnl = ticks * size * tick_value

# Example (from test):
price_diff = 21400.0 - 21500.0 = -100.0
ticks = -100.0 / 0.25 = -400 ticks
unrealized_pnl = -400 * 5 * 5.0 = -$10,000
```

### Event Types

The rule responds to:
- `EventType.POSITION_OPENED`
- `EventType.POSITION_UPDATED`

### Enforcement

When violation occurs:
- Action: `close_position`
- Target: Only the losing position (MNQ in this case)
- Lockout: NO (trade-by-trade rule, trader can continue)

## ASCII Output Format

The test uses ASCII `[OK]`/`[X]` markers (no emojis) for clear terminal output:

```
Testing RULE-004: Daily Unrealized Loss

Position opened: 5 MNQ long @ $21,500
  [OK] No violation (P&L = $0.00)

Market price update: $21,400
  Expected P&L: $-10000.00
  [X] VIOLATION: Unrealized P&L $-10000.00 <= $-750.00
  Enforcement action: close_position
  Symbol to close: MNQ

[OK] RULE-004 PASSED
```

## Next Steps

The test is ready to run. To execute:

1. Ensure the rule implementation exists at:
   `C:\Users\jakers\Desktop\risk-manager-v34\src\risk_manager\rules\daily_unrealized_loss.py`

2. Run the test:
   ```bash
   python test_rule_validation.py --rule RULE-004
   ```

3. Expected output: `[OK] RULE-004 PASSED`

---

**Completed**: 2025-10-28
**Test Lines**: 395-539 (145 lines)
**Status**: ✓ Ready to test
