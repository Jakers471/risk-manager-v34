# Bug Fix Validation - 2025-10-30

## Status: ⚠️ NEEDS TESTING

The 3 critical bugs were fixed, BUT two rules were simultaneously rewritten with architectural changes that need validation.

---

## ✅ What Was Fixed (The 3 Critical Bugs)

### Bug #1: Event Type Mismatch ✅ FIXED
**Files**: `src/risk_manager/rules/daily_realized_loss.py`, `daily_realized_profit.py`

**Fix**: Added `EventType.ORDER_FILLED` to trigger lists

```python
# BEFORE
if event.event_type not in [
    EventType.POSITION_CLOSED,
    EventType.PNL_UPDATED,
    EventType.TRADE_EXECUTED,
]:

# AFTER
if event.event_type not in [
    EventType.ORDER_FILLED,      # ← ADDED
    EventType.POSITION_CLOSED,
    EventType.PNL_UPDATED,
    EventType.TRADE_EXECUTED,
]:
```

**Validation**: ✅ Correct

---

### Bug #2: Missing Event Subscription ✅ FIXED
**File**: `src/risk_manager/core/manager.py`

**Fix**: Added subscription and handler for UNREALIZED_PNL_UPDATE events

```python
# Line 541 - Added subscription
self.event_bus.subscribe(EventType.UNREALIZED_PNL_UPDATE, self._handle_unrealized_pnl)

# Lines 581-583 - Added handler
async def _handle_unrealized_pnl(self, event: RiskEvent) -> None:
    """Handle unrealized P&L update event."""
    await self.engine.evaluate_rules(event)
```

**Validation**: ✅ Correct

---

### Bug #3: Missing account_id ✅ FIXED
**File**: `src/risk_manager/integrations/trading.py`

**Fix**: Added `account_id` and `contractId` to all event data

**Line 986** (ORDER_FILLED events):
```python
"account_id": order.accountId,  # ← ADDED
```

**Line 1409** (POSITION events):
```python
"account_id": self.client.account_info.id if self.client else None,  # ← ADDED
"contractId": contract_id,  # ← ADDED
```

**Line 1917** (UNREALIZED_PNL_UPDATE events):
```python
'account_id': self.client.account_info.id if self.client else None,  # ← ADDED
'contractId': contract_id,  # ← ADDED
```

**Validation**: ✅ Correct

---

## ⚠️ What Changed (Architecture Rewrites)

### Change #1: DailyUnrealizedLossRule - SEMANTIC CHANGE! ⚠️

**File**: `src/risk_manager/rules/daily_unrealized_loss.py`

**CRITICAL**: The rule's PURPOSE changed from "per-position stop loss" to "account-wide total loss limit"!

#### OLD Behavior (Per-Position Stop Loss):
```python
"""
Purpose: Close losing positions when unrealized loss hits limit
Category: Trade-by-Trade (Category 1)
Enforcement: Close ONLY that losing position (no lockout)

This rule implements stop-loss behavior - when a position's unrealized
loss reaches the limit, close that position to prevent further losses.
"""

# Evaluated on POSITION_UPDATED events
# Calculated P&L for SINGLE position
# Closed ONLY the losing position

Example:
- Limit: -$300 per position
- Position 1: MNQ Long, -$400 unrealized → Close MNQ position only
- Position 2: ES Short, -$200 unrealized → No action (under limit)
```

#### NEW Behavior (Account-Wide Total Loss):
```python
"""
Purpose: Monitor total unrealized loss across ALL open positions
Category: Trade-by-Trade (Category 1)
Enforcement: Flatten all positions when total unrealized loss exceeds limit (no lockout)

This rule monitors the combined floating loss across all open positions
and triggers when the total unrealized loss hits the limit.
"""

# Evaluates on UNREALIZED_PNL_UPDATE events
# Gets TOTAL P&L across ALL positions via get_total_unrealized_pnl()
# Flattens ALL positions when limit breached

Example:
- Limit: -$750 total account
- Position 1: MNQ Long, unrealized P&L: -$400
- Position 2: ES Long, unrealized P&L: -$350
- Total unrealized P&L: -$750 → TRIGGER (flatten ALL positions)
```

**This is a FUNDAMENTAL BEHAVIOR CHANGE!**

**Questions**:
1. ❓ Was this intentional or accidental?
2. ❓ Does the configuration limit (-$20.00) match the new behavior?
3. ❓ Should there be BOTH a per-position stop AND an account-wide limit?

**Current Config**:
```yaml
daily_unrealized_loss:
  enabled: true
  limit: -20.0  # ← This is now TOTAL account loss, not per-position!
```

**Impact**:
- With limit at -$20, ONE position losing $20 will flatten ALL positions
- This is VERY aggressive for a "stop loss" rule
- Might need separate rules: `StopLossPerPosition` vs `TotalUnrealizedLossLimit`

---

### Change #2: MaxUnrealizedProfitRule - Implementation Change (Same Behavior) ✅

**File**: `src/risk_manager/rules/max_unrealized_profit.py`

**GOOD NEWS**: The BEHAVIOR stayed the same, just implementation changed!

#### OLD Implementation:
```python
# Manual P&L calculation
unrealized_pnl = self._calculate_unrealized_pnl(
    symbol=symbol,
    position=position,
    current_price=current_price,
)

if unrealized_pnl >= self.target:
    return violation  # Close this position
```

#### NEW Implementation:
```python
# Use infrastructure
open_positions = engine.trading_integration.get_open_positions()
for contract_id, position_data in open_positions.items():
    unrealized_pnl = engine.trading_integration.get_position_unrealized_pnl(contract_id)

    if unrealized_pnl >= self.target:
        positions_at_target.append(...)  # Close winning positions
```

**Validation**: ✅ Correct - Still per-position profit target, just cleaner implementation

---

## 🧪 Testing Required

### Test #1: Realized Loss Rule (Bug #1 Fix)
```bash
python run_dev.py

# Take losing trade > $5
# Expected: Rule violation, trading paused, account locked
```

**Look for**:
```
❌ Rule: DailyRealizedLoss → FAIL
🚨 VIOLATION: DailyRealizedLoss
🛑 ENFORCING: Pausing trading
```

**Status**: ⏳ Not tested yet (user didn't test after fixes)

---

### Test #2: Unrealized Loss Rule (NEW BEHAVIOR)
```bash
python run_dev.py

# Open position, let it go negative by $20+
# Expected: ALL positions flattened (not just the losing one!)
```

**Look for**:
```
💹 Unrealized P&L update: MNQ $-22.00
📨 Event: unrealized_pnl_update → evaluating 6 rules
❌ Rule: DailyUnrealizedLoss → FAIL (Total P&L: -$22.00 / -$20.00 limit)
🛑 ENFORCING: Closing all positions (DailyUnrealizedLoss)
Flattening all positions...
```

**Status**: ⏳ Not tested yet

**CRITICAL**: Verify this is the desired behavior! Current limit (-$20) is VERY low for total account loss.

---

### Test #3: Unrealized Profit Rule (Bug #2 + Change #2)
```bash
python run_dev.py

# Open position, let it go positive by $20+
# Expected: Winning position closed (same as before)
```

**Look for**:
```
💹 Unrealized P&L update: MNQ $+22.00
📨 Event: unrealized_pnl_update → evaluating 6 rules
❌ Rule: MaxUnrealizedProfit → FAIL
🛑 ENFORCING: Closing position MNQ
```

**Status**: ⏳ Not tested yet

---

## ⚠️ Configuration Concerns

### Current Configuration:
```yaml
# config/risk_config.yaml

daily_realized_loss:
  enabled: true
  limit: -5.0  # Per-trade realized loss ✅ Makes sense

daily_unrealized_loss:
  enabled: true
  limit: -20.0  # ⚠️ NOW TOTAL ACCOUNT LOSS (was per-position)
  action: "close_position"  # ⚠️ Misleading - actually flattens ALL

max_unrealized_profit:
  enabled: true
  target: 20.0  # Per-position profit target ✅ Correct
  action: "close_position"  # ✅ Correct - closes winning positions
```

### Recommendations:

1. **Clarify DailyUnrealizedLoss Purpose**:
   ```yaml
   # Option A: Keep as total account loss limit
   daily_unrealized_loss:
     enabled: true
     limit: -750.0  # ← Increase to realistic total account limit
     action: "flatten"  # ← Change action name to clarify

   # Option B: Revert to per-position stop loss
   stop_loss_per_position:  # ← Rename rule
     enabled: true
     limit: -300.0  # ← Per-position stop loss
     action: "close_position"  # ← Close ONLY losing position

   # Option C: Have BOTH rules
   stop_loss_per_position:
     limit: -300.0  # Close individual losers
   total_unrealized_loss_limit:
     limit: -750.0  # Flatten account if total loss exceeds
   ```

2. **Test With Realistic Values**:
   - Current -$20 total account limit is TOO LOW
   - One 2-tick MNQ loss would flatten everything!
   - Suggest: -$750 to -$1000 for real protection

3. **Update Documentation**:
   - Rule docstrings need to match actual behavior
   - Config comments should clarify "total" vs "per-position"

---

## 🔧 Validation Checklist

- [ ] Test Bug #1 Fix: ORDER_FILLED events trigger realized P&L rules
- [ ] Test Bug #2 Fix: UNREALIZED_PNL_UPDATE events trigger unrealized rules
- [ ] Test Bug #3 Fix: account_id present in all events
- [ ] Verify DailyUnrealizedLoss semantic change is intentional
- [ ] Verify DailyUnrealizedLoss limit (-$20) is appropriate for TOTAL account loss
- [ ] Test MaxUnrealizedProfit still closes individual winners correctly
- [ ] Update config comments to clarify "total" vs "per-position"
- [ ] Update rule docstrings to match actual behavior
- [ ] Consider splitting into separate rules (stop loss vs total loss)

---

## 🎯 Next Steps

### Immediate (Before Deployment):
1. Run `python run_dev.py` with small test trades
2. Verify all 3 bug fixes work as expected
3. Verify unrealized P&L rules trigger on UNREALIZED_PNL_UPDATE events
4. Check that DailyUnrealizedLoss behavior is what you want

### Short-Term (Configuration):
1. Decide if DailyUnrealizedLoss should be:
   - Per-position stop loss (revert changes)
   - Total account loss (increase limit to -$750+)
   - Split into two separate rules (recommended!)
2. Update config with appropriate limits
3. Update docstrings and comments

### Long-Term (Architecture):
1. Consider rule naming: "DailyUnrealizedLoss" sounds like per-day accounting
2. Better names: "StopLossPerPosition", "TotalAccountLossLimit"
3. Document rule categories clearly in PROJECT_STATUS.md

---

## 📊 Files Modified Summary

### Bug Fixes (3 files, ~20 lines):
1. ✅ `src/risk_manager/rules/daily_realized_loss.py` - Added ORDER_FILLED trigger
2. ✅ `src/risk_manager/rules/daily_realized_profit.py` - Added ORDER_FILLED trigger
3. ✅ `src/risk_manager/core/manager.py` - Added UNREALIZED_PNL_UPDATE subscription + handler
4. ✅ `src/risk_manager/integrations/trading.py` - Added account_id & contractId to events

### Rule Rewrites (2 files, ~200 lines changed):
5. ⚠️ `src/risk_manager/rules/daily_unrealized_loss.py` - Complete rewrite (BEHAVIOR CHANGED!)
6. ✅ `src/risk_manager/rules/max_unrealized_profit.py` - Implementation cleanup (behavior same)

---

## 💡 Recommendations

### Critical:
1. **TEST BEFORE DEPLOYING** - The semantic change in DailyUnrealizedLoss is significant
2. **Increase -$20 limit** - Way too low for total account loss
3. **Clarify intent** - Is this stop loss or total loss limit?

### Nice to Have:
1. **Split rules** - Have both per-position stop AND total account limit
2. **Rename rules** - Use clear names that match behavior
3. **Add tests** - Write tests that validate the new behaviors
4. **Update docs** - Sync docstrings with actual implementation

---

## ✅ Conclusion

**Bug Fixes**: ✅ All 3 fixes are technically correct and should work

**Architecture Changes**: ⚠️ Need validation and possibly configuration adjustments

**Next Action**: Run `python run_dev.py` and test all 6 rules with small trades

---

**Last Updated**: 2025-10-30 (by AI Agent)
**Status**: Ready for testing
**Priority**: HIGH - Semantic change in DailyUnrealizedLoss needs clarification
