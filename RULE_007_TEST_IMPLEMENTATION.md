# RULE-007 Test Implementation Summary

## Task Completion

**Status**: ✅ **COMPLETE** - Test implementation ready for integration

**File Created**: `C:\Users\jakers\Desktop\risk-manager-v34\test_rule_007_snippet.py`

---

## What Was Done

### 1. Analyzed RULE-007 Implementation
- **File**: `src/risk_manager/rules/cooldown_after_loss.py`
- **Key Features**:
  - Tiered cooldown thresholds based on loss amount
  - Uses `profitAndLoss` field (camelCase) from TRADE_EXECUTED events
  - Integrates with `TimerManager` for countdown functionality
  - Sets lockout via `LockoutManager.set_cooldown()`
  - Action: "flatten" (close all positions)

### 2. Followed Existing Test Pattern
- **Reference Tests**: RULE-001, RULE-003, RULE-009
- **Pattern Observed**:
  - Create rule with test configuration
  - Mock engine with minimal required attributes
  - Generate events with proper data structure
  - Evaluate rule with each event
  - Track violations
  - Execute enforcement for breach events
  - Verify arithmetic and enforcement actions

### 3. Created Comprehensive Test

**Test Method**: `test_rule_007_cooldown_after_loss()`

**Test Scenario**:
```
Threshold: -$100 loss → 5-minute cooldown (300 seconds)

Trade 1: -$50 loss
  ├─ Expectation: NO VIOLATION
  ├─ Reason: Below -$100 threshold
  └─ Lockout: None

Trade 2: -$150 loss
  ├─ Expectation: VIOLATION!
  ├─ Reason: Exceeds -$100 threshold
  ├─ Action: flatten
  ├─ Cooldown: 300 seconds
  └─ Lockout: Set by enforce()
```

**Validation Checks**:
1. ✅ Only 1 violation (trade 2)
2. ✅ Arithmetic correct (cooldown_duration == 300, loss_amount == -150.0)
3. ✅ Enforcement action == "flatten"
4. ✅ Lockout verified after enforcement
5. ✅ Timer manager cleanup

---

## Key Implementation Details

### API Compliance

**Event Structure** (matches actual SDK):
```python
event = RiskEvent(
    event_type=EventType.TRADE_EXECUTED,
    data={
        "account_id": test_account,
        "profitAndLoss": -150.0,  # ⚠️ camelCase (SDK format)
        "symbol": "ES"
    }
)
```

**Rule Initialization** (matches rule __init__):
```python
rule = CooldownAfterLossRule(
    loss_thresholds=[
        {"loss_amount": -100.0, "cooldown_duration": 300}
    ],
    timer_manager=timer_manager,        # Required
    pnl_tracker=self.pnl_tracker,       # Required
    lockout_manager=self.lockout_manager, # Required
    action="flatten"                     # Default action
)
```

**Timer Manager Lifecycle**:
```python
# Start before rule creation
timer_manager = TimerManager()
await timer_manager.start()

# ... use rule ...

# Cleanup after test
await timer_manager.stop()
```

### ASCII Output (No Emojis)
```
[OK] - Success indicator
[X]  - Failure indicator
```

---

## Integration Instructions

### Step 1: Add Test Method

Add the contents of `test_rule_007_snippet.py` to `test_rule_validation.py`:

**Location**: After `test_rule_005_max_unrealized_profit()` and before `run_all_tests()`

```python
# In test_rule_validation.py

class RuleTester:
    # ... existing test methods ...

    async def test_rule_005_max_unrealized_profit(self) -> dict[str, Any]:
        # ... existing code ...
        return result

    # ⬇️ INSERT RULE-007 TEST HERE ⬇️
    async def test_rule_007_cooldown_after_loss(self) -> dict[str, Any]:
        # ... code from test_rule_007_snippet.py ...
        return result

    async def run_all_tests(self) -> dict[str, dict[str, Any]]:
        # ... existing code ...
```

### Step 2: Register in run_all_tests()

Add this line to the `run_all_tests()` method:

**Location**: After `results["RULE-006"]` line

```python
async def run_all_tests(self) -> dict[str, dict[str, Any]]:
    """Run all rule tests."""
    # ... setup code ...

    results = {}

    results["RULE-001"] = await self.test_rule_001_max_contracts()
    results["RULE-002"] = await self.test_rule_002_max_contracts_per_instrument()
    results["RULE-003"] = await self.test_rule_003_daily_realized_loss()
    results["RULE-004"] = await self.test_rule_004_daily_unrealized_loss()
    results["RULE-005"] = await self.test_rule_005_max_unrealized_profit()
    results["RULE-006"] = await self.test_rule_006_trade_frequency_limit()
    results["RULE-007"] = await self.test_rule_007_cooldown_after_loss()  # ⬅️ ADD THIS
    results["RULE-009"] = await self.test_rule_009_session_block_outside()
    results["RULE-012"] = await self.test_rule_012_trade_management()
    results["RULE-013"] = await self.test_rule_013_daily_realized_profit()

    # ... rest of method ...
```

---

## Testing the Test

### Run Specific Rule Test
```bash
python test_rule_validation.py --rule RULE-007
```

**Expected Output**:
```
Testing RULE-007: Cooldown After Loss
Trade 1: -$50 loss
  [OK] No violation (loss below threshold)
  Account locked: False
Trade 2: -$150 loss
  [X] VIOLATION: Cooldown triggered after $-150.0 loss (300s cooldown)
  [red]Enforcement action: flatten[/red]
  [red]Cooldown duration: 300s[/red]
  Account locked after enforcement: True

[OK] RULE-007 PASSED
```

### Run All Tests
```bash
python test_rule_validation.py
```

**Expected Result**:
- RULE-007 should appear in the summary table
- Status: [OK] PASS
- Arithmetic: [OK]
- Enforcement: flatten

---

## Files Modified/Created

### Created
1. **`test_rule_007_snippet.py`**
   - Complete test method ready for copy/paste
   - Registration instructions included

2. **`RULE_007_TEST_IMPLEMENTATION.md`** (this file)
   - Complete implementation summary
   - Integration instructions
   - Testing guide

### To Be Modified
1. **`test_rule_validation.py`**
   - Add `test_rule_007_cooldown_after_loss()` method
   - Register in `run_all_tests()`

---

## Validation Checklist

Before committing, verify:

- [ ] Test method added to `RuleTester` class
- [ ] Test registered in `run_all_tests()`
- [ ] Test runs successfully: `python test_rule_validation.py --rule RULE-007`
- [ ] Test passes (arithmetic, violations, lockout verification)
- [ ] No emoji characters (uses [OK]/[X] instead)
- [ ] Timer manager properly cleaned up
- [ ] Mock engine has required attributes
- [ ] Event uses camelCase `profitAndLoss` field

---

## Implementation Notes

### Why This Test Design?

1. **Tiered Threshold Testing**: Tests the core feature of RULE-007 (tiered cooldowns)
2. **Below/Above Threshold**: Validates threshold logic works correctly
3. **Enforcement Verification**: Confirms lockout_manager is actually called
4. **Timer Integration**: Tests integration with TimerManager
5. **Cleanup**: Ensures no resource leaks (timer manager stopped)

### Key Differences from Other Tests

1. **Requires TimerManager**: Unlike RULE-001/003, RULE-007 needs timer infrastructure
2. **Lockout Verification**: Explicitly checks lockout state after enforcement
3. **Loss-Based**: Triggers on negative P&L (not position size or time)

### Edge Cases NOT Tested (Future Work)

- [ ] Multiple tiered thresholds (-100, -200, -300)
- [ ] Half-turn trades (profitAndLoss=None)
- [ ] Winning trades (profitAndLoss > 0)
- [ ] Already locked out account
- [ ] Timer expiry and auto-unlock

---

## Next Steps

1. **Integrate the test** into `test_rule_validation.py`
2. **Run the test suite** to verify it passes
3. **Review output** to ensure all checkpoints pass
4. **Consider edge cases** if time permits

---

## Questions/Issues?

If the test fails, check:

1. ✅ TimerManager is started before rule creation
2. ✅ Event uses `profitAndLoss` (camelCase, not snake_case)
3. ✅ Loss amounts are negative (-$100, not $100)
4. ✅ Cooldown duration is in seconds (300 = 5 minutes)
5. ✅ Lockout manager properly initialized in RuleTester
6. ✅ Mock engine has required attributes (current_positions, market_prices)

---

**Implementation Status**: ✅ READY FOR INTEGRATION

**Test File**: `C:\Users\jakers\Desktop\risk-manager-v34\test_rule_007_snippet.py`

**Next Action**: Copy contents to `test_rule_validation.py` and register in `run_all_tests()`
