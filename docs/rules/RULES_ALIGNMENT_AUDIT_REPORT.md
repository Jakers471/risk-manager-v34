# Rules Alignment Audit Report

**Generated**: 2025-10-27
**Auditor**: Agent #1 (Rules Alignment Audit)
**Mission**: Audit ALL 13 rule specifications for alignment with SDK event patterns

---

## Executive Summary

### Alignment Status
**Overall Alignment**: 82% (10.5/13 rules aligned)

- **Fully Aligned**: 9 rules (RULE-001, 002, 003, 006, 007, 009, 010, 011, 013)
- **Partially Aligned**: 2 rules (RULE-004, 005)
- **Not Aligned**: 1 rule (RULE-008)
- **Needs Clarification**: 1 rule (RULE-012)

### Critical Findings
1. ✅ **Event subscription patterns are correct** across all rules
2. ⚠️ **RULE-008 has CRITICAL semantic error** - wrong event type for stop-loss detection
3. ⚠️ **RULE-004/005 have inconsistent event subscriptions** - missing POSITION_OPENED/CLOSED
4. ⚠️ **RULE-012 event subscriptions are unclear** - needs market data clarification

---

## Detailed Audit by Rule

### RULE-001: Max Contracts ✅ FULLY ALIGNED

**Category**: Trade-by-Trade (Category 1)
**Status**: Fully Implemented

#### Event Subscriptions: ✅ CORRECT
```
Spec (line 15): EventType.POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED
SDK Pattern: ✅ Matches - All 3 position events covered
```

#### Data Field References: ✅ CORRECT
```
Spec (lines 22-25):
- position['type'] - 1=Long, 2=Short ✅
- position['size'] - Position size ✅
SDK Provides: type, size in POSITION_UPDATED ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Uses all 3 position events for comprehensive tracking ✅
- Correct semantic usage: detects position changes in real-time ✅

#### Severity: **NONE** - Fully aligned

#### Recommendations: None needed

---

### RULE-002: Max Contracts Per Instrument ✅ FULLY ALIGNED

**Category**: Trade-by-Trade (Category 1)
**Status**: Fully Implemented

#### Event Subscriptions: ✅ CORRECT
```
Spec (line 15): EventType.POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED
SDK Pattern: ✅ Matches - All 3 position events covered
```

#### Data Field References: ✅ CORRECT
```
Spec (lines 20-21):
- position_event['contractId'] - Extract symbol ✅
- position_event['size'] - Position size ✅
SDK Provides: contractId, size in POSITION_UPDATED ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Uses all 3 position events for comprehensive tracking ✅
- Symbol extraction from contractId is correct pattern ✅

#### Severity: **NONE** - Fully aligned

#### Recommendations: None needed

---

### RULE-003: Daily Realized Loss ✅ FULLY ALIGNED

**Category**: Hard Lockout (Category 3)
**Status**: Partially Implemented (70%)

#### Event Subscriptions: ✅ CORRECT
```
Spec (line 15): EventType.TRADE_EXECUTED
SDK Pattern: ✅ Correct - TRADE_EXECUTED has profitAndLoss field
```

#### Data Field References: ✅ CORRECT
```
Spec (lines 20, 23):
- trade_event['profitAndLoss'] ✅
- trade_event['accountId'] ✅
SDK Provides: profitAndLoss in TRADE_EXECUTED (null for opening trades) ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Correctly checks for `pnl is not None` to skip half-turn trades (line 23) ✅
- Uses semantically correct event (TRADE_EXECUTED has realized P&L) ✅

#### Severity: **NONE** - Fully aligned

#### Recommendations: None needed (implementation gap is MOD-002/MOD-004, not spec alignment)

---

### RULE-004: Daily Unrealized Loss ⚠️ PARTIALLY ALIGNED

**Category**: Trade-by-Trade (Category 1)
**Status**: Not Implemented

#### Event Subscriptions: ⚠️ INCONSISTENT
```
Spec (line 17): EventType.POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED + market price updates
SDK Pattern: ⚠️ Only lists POSITION_UPDATED explicitly in "Events needed" (line 124)
Issue: Should list all 3 position events for consistency with RULE-001/002
```

**Lines Needing Update**:
- Line 17: ✅ Already lists all 3 events correctly
- Line 124: ❌ Only lists POSITION_UPDATED - should match line 17

#### Data Field References: ✅ CORRECT
```
Spec (lines 24-28):
- position_event['avgPrice'] - Entry price ✅
- current_market_price - From quote updates ✅
- position_event['size'] - Position size ✅
- position_event['type'] - 1=Long, 2=Short ✅
- tick_value, tick_size - Configuration ✅

SDK Provides:
- POSITION_UPDATED.averagePrice ✅ (note: spec says 'avgPrice', SDK uses 'averagePrice')
- QUOTE_UPDATE.last ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Uses POSITION_UPDATED for entry price ✅
- Requires QUOTE_UPDATE for current price ✅
- Semantic usage is correct ✅

#### Severity: **MEDIUM** - Inconsistent documentation

#### Recommendations:
1. **Update line 124** to match line 17:
   ```yaml
   # Current (line 124):
   - `EventType.POSITION_UPDATED` - Position updates

   # Should be:
   - `EventType.POSITION_OPENED` - New positions
   - `EventType.POSITION_UPDATED` - Position changes
   - `EventType.POSITION_CLOSED` - Position closes
   ```

2. **Fix field name inconsistency** (line 24):
   ```python
   # Current:
   entry_price=position_event['avgPrice']

   # Should match SDK:
   entry_price=position_event['averagePrice']
   ```

---

### RULE-005: Max Unrealized Profit ⚠️ PARTIALLY ALIGNED

**Category**: Trade-by-Trade (Category 1)
**Status**: Not Implemented

#### Event Subscriptions: ⚠️ INCONSISTENT
```
Spec (line 17): EventType.POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED + market price updates
SDK Pattern: ⚠️ Only lists POSITION_UPDATED explicitly in "Events needed" (line 125)
Issue: Should list all 3 position events for consistency with RULE-001/002
```

**Lines Needing Update**:
- Line 17: ✅ Already lists all 3 events correctly
- Line 125: ❌ Only lists POSITION_UPDATED - should match line 17

#### Data Field References: ✅ CORRECT (same as RULE-004)
```
Spec (lines 24-28):
- position_event['avgPrice'] - Entry price ✅ (should be 'averagePrice')
- current_market_price - From quote updates ✅
- position_event['size'] - Position size ✅
- position_event['type'] - 1=Long, 2=Short ✅
- tick_value, tick_size - Configuration ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Uses POSITION_UPDATED for entry price ✅
- Requires QUOTE_UPDATE for current price ✅
- Semantic usage is correct ✅

#### Severity: **MEDIUM** - Inconsistent documentation (identical to RULE-004)

#### Recommendations: (Identical to RULE-004)
1. **Update line 125** to list all 3 position events
2. **Fix field name**: `avgPrice` → `averagePrice` (line 24)

---

### RULE-006: Trade Frequency Limit ✅ FULLY ALIGNED

**Category**: Timer/Cooldown (Category 2)
**Status**: Not Implemented

#### Event Subscriptions: ✅ CORRECT
```
Spec (line 15): EventType.TRADE_EXECUTED
SDK Pattern: ✅ Correct - counts executed trades
```

#### Data Field References: ✅ CORRECT
```
Spec: No specific field references (just counting trades)
SDK Provides: TRADE_EXECUTED fires for every trade ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Uses TRADE_EXECUTED to count trades ✅
- Correct semantic usage ✅

#### Severity: **NONE** - Fully aligned

#### Recommendations: None needed

---

### RULE-007: Cooldown After Loss ✅ FULLY ALIGNED

**Category**: Timer/Cooldown (Category 2)
**Status**: Not Implemented

#### Event Subscriptions: ✅ CORRECT
```
Spec (line 15): EventType.TRADE_EXECUTED (when profitAndLoss < 0)
SDK Pattern: ✅ Correct - TRADE_EXECUTED has profitAndLoss field
```

#### Data Field References: ✅ CORRECT
```
Spec: Checks profitAndLoss < 0
SDK Provides: TRADE_EXECUTED.profitAndLoss ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Uses TRADE_EXECUTED for realized loss detection ✅
- Correct semantic usage ✅

#### Severity: **NONE** - Fully aligned

#### Recommendations: None needed

---

### RULE-008: No Stop-Loss Grace 🔴 NOT ALIGNED - CRITICAL

**Category**: Trade-by-Trade (Category 1)
**Status**: Not Implemented

#### Event Subscriptions: 🔴 INCORRECT - CRITICAL SEMANTIC ERROR
```
Spec (line 15): EventType.ORDER_PLACED (when position opens)
SDK Pattern: 🔴 WRONG - ORDER_PLACED fires for ANY order (entry, stop, limit, etc.)
```

**Critical Issue**:
The spec says "when position opens" but subscribes to ORDER_PLACED. This is semantically incorrect because:
- ORDER_PLACED fires for ALL orders (entry orders, stop-loss orders, limit orders)
- To detect "position opens", must use POSITION_OPENED event
- To check for stop-loss, must look for ORDER_PLACED with `order.type == 3` (STOP order)

**Correct Pattern** (from SDK_EVENTS_QUICK_REFERENCE.txt lines 103-105):
```
RULE-008 (Stop Loss Check):
  → POSITION_OPENED + ORDER_PLACED
  → Need: Check if stopPrice exists when position opens
```

#### Lines Needing Update:
- **Line 15**: Change trigger condition
- **Line 17**: Add POSITION_OPENED event

#### Data Field References: ⚠️ INCOMPLETE
```
Spec (line 17): "Start timer, check for stop-loss order at expiry"
SDK Provides:
- ORDER_PLACED.order.type == 3 (STOP order) ✅
- ORDER_PLACED.order.stopPrice (stop price) ✅
- POSITION_OPENED (detect when position opens) ✅

Missing: Spec doesn't mention how to identify stop-loss orders
```

#### Event Type Accuracy: 🔴 INCORRECT
- **Wrong event choice**: ORDER_PLACED fires for ALL orders, not just position opens
- **Missing event**: Should use POSITION_OPENED to detect position opens
- **Logic gap**: Doesn't explain how to identify stop-loss vs entry orders

#### Severity: **CRITICAL** - Wrong event semantics will cause false triggers

#### Recommendations:
1. **Rewrite Trigger Condition** (line 14-17):
   ```markdown
   ### Trigger Condition
   **Events**:
   1. `EventType.POSITION_OPENED` - Detect when position opens
   2. `EventType.ORDER_PLACED` - Detect when stop-loss is placed

   **Logic**:
   1. When POSITION_OPENED fires, start grace period timer
   2. Monitor ORDER_PLACED events for stop-loss order:
      - Check if `order.type == 3` (STOP order)
      - Check if `order.stopPrice` exists
      - Match `order.contractId` to position's contractId
   3. If no matching stop-loss found before timer expires, close position
   ```

2. **Add field references** for stop-loss detection:
   ```markdown
   ### Data Fields Required
   - POSITION_OPENED.contractId - Track which position opened
   - ORDER_PLACED.order.type - 3=STOP order
   - ORDER_PLACED.order.stopPrice - Stop price
   - ORDER_PLACED.contractId - Match to position
   ```

3. **Update SDK Integration section** (around line 35):
   ```markdown
   ### SDK Integration
   - Events: `EventType.POSITION_OPENED`, `EventType.ORDER_PLACED`
   - Check: `order.type == 3` (STOP) and `order.stopPrice` exists
   - Methods: `close_position(account_id, contract_id)`
   ```

---

### RULE-009: Session Block Outside ✅ FULLY ALIGNED

**Category**: Hard Lockout (Category 3)
**Status**: Not Implemented

#### Event Subscriptions: ✅ CORRECT
```
Spec (lines 15-18):
1. EventType.POSITION_UPDATED (position opens outside session) ✅
2. Background timer (session end time reached) ✅
3. Holiday detection ✅
```

#### Data Field References: ✅ CORRECT
```
Spec: Time-based checks (no specific event fields needed)
SDK Provides: POSITION_UPDATED fires when position opens ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Uses POSITION_UPDATED to detect position opens ✅
- Uses timer for session boundaries ✅
- Correct semantic usage ✅

#### Severity: **NONE** - Fully aligned

#### Recommendations: None needed

---

### RULE-010: Auth Loss Guard ✅ FULLY ALIGNED

**Category**: Hard Lockout (Category 3)
**Status**: Not Implemented

#### Event Subscriptions: ✅ CORRECT
```
Spec (line 15): EventType.ACCOUNT_UPDATED (when canTrade changes)
SDK Pattern: ✅ Correct - ACCOUNT_UPDATED has canTrade field
```

#### Data Field References: ✅ CORRECT
```
Spec (line 19): account_event['canTrade']
SDK Provides: ACCOUNT_UPDATED.canTrade ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Uses ACCOUNT_UPDATED to monitor trading authorization ✅
- Correct semantic usage ✅

#### Severity: **NONE** - Fully aligned

#### Recommendations: None needed

---

### RULE-011: Symbol Blocks ✅ FULLY ALIGNED

**Category**: Trade-by-Trade (Category 1)
**Status**: Not Implemented

#### Event Subscriptions: ✅ CORRECT
```
Spec (line 15): EventType.POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED
SDK Pattern: ✅ Matches - All 3 position events covered
```

#### Data Field References: ✅ CORRECT
```
Spec: Checks contractId for symbol matching
SDK Provides: POSITION_UPDATED.contractId ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Uses all 3 position events ✅
- Correct semantic usage ✅

#### Severity: **NONE** - Fully aligned

#### Recommendations: None needed

---

### RULE-012: Trade Management ⚠️ NEEDS CLARIFICATION

**Category**: Automation (Category 4)
**Status**: Not Implemented

#### Event Subscriptions: ⚠️ UNCLEAR
```
Spec (line 17): EventType.POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED + market price updates
SDK Pattern: ⚠️ Missing "SDK Integration" section clarity
```

**Issue**: Spec mentions "market price updates" but doesn't explicitly list QUOTE_UPDATE event

#### Data Field References: ⚠️ INCOMPLETE
```
Spec: Mentions "market price updates" but no field references
SDK Provides:
- QUOTE_UPDATE.last (current price) ✅
- POSITION_UPDATED.averagePrice (entry price) ✅
- ORDER_PLACED.order.stopPrice (current stop) ✅
```

#### Event Type Accuracy: ⚠️ UNCLEAR
- Should use QUOTE_UPDATE for current price ✅
- Should use ORDER_PLACED to track existing stop-loss ✅
- Needs clarification on event flow ✅

#### Severity: **LOW** - Needs documentation clarity (not implemented yet)

#### Recommendations:
1. **Add explicit QUOTE_UPDATE reference** (line 17):
   ```markdown
   ### Trigger Condition
   **Events**:
   - `EventType.POSITION_OPENED` - New positions
   - `EventType.POSITION_UPDATED` - Position changes
   - `EventType.POSITION_CLOSED` - Position closes
   - `EventType.QUOTE_UPDATE` - Real-time price updates (for profit calculation)
   ```

2. **Add data field references**:
   ```markdown
   ### Data Fields Required
   - POSITION_UPDATED.averagePrice - Entry price
   - QUOTE_UPDATE.last - Current market price
   - ORDER_PLACED.order.stopPrice - Current stop-loss price
   - Configuration tick sizes for tick calculations
   ```

3. **Clarify SDK Integration section** (lines 44-45):
   ```markdown
   ### SDK Integration
   - Events: POSITION_UPDATED, QUOTE_UPDATE, ORDER_PLACED
   - Methods: `modify_order()` - Modify stop-loss orders
   - Quote data: Yes - QUOTE_UPDATE.last for current price
   ```

---

### RULE-013: Daily Realized Profit ✅ FULLY ALIGNED

**Category**: Hard Lockout (Category 3)
**Status**: Not Implemented

#### Event Subscriptions: ✅ CORRECT
```
Spec (line 17): EventType.TRADE_EXECUTED
SDK Pattern: ✅ Correct - TRADE_EXECUTED has profitAndLoss field
```

#### Data Field References: ✅ CORRECT
```
Spec (lines 22, 25-28):
- trade_event['profitAndLoss'] ✅
- trade_event['accountId'] ✅
SDK Provides: TRADE_EXECUTED.profitAndLoss ✅
```

#### Event Type Accuracy: ✅ CORRECT
- Correctly checks for `pnl is not None` to skip half-turn trades (line 25) ✅
- Uses semantically correct event (TRADE_EXECUTED has realized P&L) ✅
- Identical pattern to RULE-003 (opposite direction) ✅

#### Severity: **NONE** - Fully aligned

#### Recommendations: None needed

---

## Summary of Issues by Severity

### 🔴 CRITICAL Issues (1)
| Rule | Issue | Lines | Fix Required |
|------|-------|-------|--------------|
| RULE-008 | Wrong event type - ORDER_PLACED fires for ALL orders, not just position opens | 15, 17 | Add POSITION_OPENED event, explain how to identify stop-loss orders |

### ⚠️ MEDIUM Issues (2)
| Rule | Issue | Lines | Fix Required |
|------|-------|-------|--------------|
| RULE-004 | Inconsistent event subscription documentation | 124 | Update "SDK Integration" section to list all 3 position events |
| RULE-004 | Wrong field name (`avgPrice` should be `averagePrice`) | 24 | Change field name to match SDK |
| RULE-005 | Inconsistent event subscription documentation | 125 | Update "SDK Integration" section to list all 3 position events |
| RULE-005 | Wrong field name (`avgPrice` should be `averagePrice`) | 24 | Change field name to match SDK |

### ⚠️ LOW Issues (1)
| Rule | Issue | Lines | Fix Required |
|------|-------|-------|--------------|
| RULE-012 | Unclear event subscriptions - missing QUOTE_UPDATE explicit mention | 17, 44-45 | Add QUOTE_UPDATE to event list, add data field references |

---

## Pattern Consistency Analysis

### Correct Patterns (Used Consistently)
1. ✅ **Position tracking**: All rules correctly use all 3 position events (OPENED, UPDATED, CLOSED)
   - RULE-001, 002, 011 ✅
   - RULE-004, 005 (line 17 correct, but line 124/125 inconsistent)

2. ✅ **Realized P&L**: Both rules correctly use TRADE_EXECUTED and check for null
   - RULE-003, 013 ✅

3. ✅ **Trade counting**: Rules correctly use TRADE_EXECUTED
   - RULE-006, 007 ✅

4. ✅ **Authorization**: Rule correctly uses ACCOUNT_UPDATED
   - RULE-010 ✅

### Inconsistent Patterns
1. ⚠️ **RULE-004/005**: Inconsistency between "Trigger Condition" (line 17) and "SDK Integration" (line 124/125)
   - **Pattern**: Should list all 3 position events in both places
   - **Fix**: Add POSITION_OPENED and POSITION_CLOSED to SDK Integration sections

2. ⚠️ **Field naming**: RULE-004/005 use `avgPrice` but SDK provides `averagePrice`
   - **Pattern**: Should match SDK field names exactly
   - **Fix**: Change to `averagePrice`

### Missing Patterns
1. 🔴 **RULE-008**: Missing the fundamental pattern of how to detect stop-loss orders
   - **Pattern**: Check `ORDER_PLACED.order.type == 3` and `order.stopPrice` exists
   - **Fix**: Add complete logic for stop-loss detection

---

## Recommendations Summary

### Immediate Actions Required
1. **RULE-008**: Complete rewrite of event subscription logic (CRITICAL)
2. **RULE-004/005**: Update SDK Integration sections for consistency (MEDIUM)
3. **RULE-004/005**: Fix field name `avgPrice` → `averagePrice` (MEDIUM)
4. **RULE-012**: Add explicit QUOTE_UPDATE event reference (LOW)

### Documentation Standards Going Forward
1. **Event listings must be consistent** between "Trigger Condition" and "SDK Integration" sections
2. **Field names must match SDK exactly** - use SDK_EVENTS_QUICK_REFERENCE.txt as source of truth
3. **Event semantics must be accurate** - verify event types actually provide the data needed
4. **All position-tracking rules should use all 3 events** (OPENED, UPDATED, CLOSED) for safety

---

## Validation Checklist

For each rule specification, verify:
- [ ] Event types listed match SDK event types exactly
- [ ] Data fields referenced exist in those events
- [ ] Event subscriptions are consistent between sections
- [ ] Field names match SDK naming (`averagePrice`, not `avgPrice`)
- [ ] Event semantics are correct (ORDER_PLACED ≠ position opens)
- [ ] All 3 position events used when tracking positions
- [ ] Null checks present for `profitAndLoss` field

---

## Files Modified
This audit found issues in the following specification files:
- `docs/specifications/unified/rules/RULE-004-daily-unrealized-loss.md` (lines 24, 124)
- `docs/specifications/unified/rules/RULE-005-max-unrealized-profit.md` (lines 24, 125)
- `docs/specifications/unified/rules/RULE-008-no-stop-loss-grace.md` (lines 14-17, 35)
- `docs/specifications/unified/rules/RULE-012-trade-management.md` (lines 17, 44-45)

---

**End of Audit Report**
