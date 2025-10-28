# Rules Alignment Audit - Quick Summary

**Generated**: 2025-10-27
**Full Report**: `RULES_ALIGNMENT_AUDIT_REPORT.md`

---

## Overall Status: 82% Aligned (10.5/13 rules)

### ✅ Fully Aligned (9 rules)
- RULE-001: Max Contracts
- RULE-002: Max Contracts Per Instrument
- RULE-003: Daily Realized Loss
- RULE-006: Trade Frequency Limit
- RULE-007: Cooldown After Loss
- RULE-009: Session Block Outside
- RULE-010: Auth Loss Guard
- RULE-011: Symbol Blocks
- RULE-013: Daily Realized Profit

### ⚠️ Partially Aligned (2 rules)
- **RULE-004**: Daily Unrealized Loss (inconsistent event documentation + field naming)
- **RULE-005**: Max Unrealized Profit (inconsistent event documentation + field naming)

### 🔴 Not Aligned (1 rule)
- **RULE-008**: No Stop-Loss Grace (CRITICAL - wrong event type)

### ⚠️ Needs Clarification (1 rule)
- **RULE-012**: Trade Management (missing explicit QUOTE_UPDATE reference)

---

## Critical Issues Requiring Immediate Action

### 🔴 RULE-008: CRITICAL Semantic Error
**Issue**: Spec says "when position opens" but subscribes to ORDER_PLACED
- **Problem**: ORDER_PLACED fires for ALL orders (entry, stop, limit), not just position opens
- **Missing**: Should use POSITION_OPENED to detect position opens
- **Missing**: Should check `ORDER_PLACED.order.type == 3` to identify stop-loss orders
- **Impact**: Will cause false triggers on every order
- **Fix Required**: Complete rewrite of trigger condition logic
- **File**: `RULE-008-no-stop-loss-grace.md` lines 14-17, 35

---

## Medium Priority Issues

### ⚠️ RULE-004 & RULE-005: Documentation Inconsistency
**Issue**: "Trigger Condition" lists 3 position events, but "SDK Integration" only lists POSITION_UPDATED

**RULE-004 (`RULE-004-daily-unrealized-loss.md`)**:
- Line 17: ✅ Correctly lists POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED
- Line 124: ❌ Only lists POSITION_UPDATED
- Line 24: ❌ Uses `avgPrice` (should be `averagePrice` to match SDK)

**RULE-005 (`RULE-005-max-unrealized-profit.md`)**:
- Line 17: ✅ Correctly lists POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED
- Line 125: ❌ Only lists POSITION_UPDATED
- Line 24: ❌ Uses `avgPrice` (should be `averagePrice` to match SDK)

**Fix Required**: Update SDK Integration sections to match Trigger Condition sections

---

## Low Priority Issues

### ⚠️ RULE-012: Missing Event Clarity
**Issue**: Mentions "market price updates" but doesn't explicitly list QUOTE_UPDATE event
- **File**: `RULE-012-trade-management.md` lines 17, 44-45
- **Fix Required**: Add explicit QUOTE_UPDATE event reference and data fields

---

## Quick Fix Guide

### Fix RULE-008 (CRITICAL)
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

### Fix RULE-004/005 (MEDIUM)
```markdown
# In SDK Integration section (line 124/125):
**Events needed**:
- `EventType.POSITION_OPENED` - New positions
- `EventType.POSITION_UPDATED` - Position changes
- `EventType.POSITION_CLOSED` - Position closes
- `EventType.QUOTE_UPDATE` - Real-time price updates

# In Trigger Logic (line 24):
# Change:
entry_price=position_event['avgPrice']
# To:
entry_price=position_event['averagePrice']
```

### Fix RULE-012 (LOW)
```markdown
# In Trigger Condition (line 17):
**Events**:
- `EventType.POSITION_OPENED` - New positions
- `EventType.POSITION_UPDATED` - Position changes
- `EventType.POSITION_CLOSED` - Position closes
- `EventType.QUOTE_UPDATE` - Real-time price updates

# In SDK Integration (lines 44-45):
**Events needed**:
- POSITION_UPDATED, QUOTE_UPDATE, ORDER_PLACED
**Quote data**: Yes - QUOTE_UPDATE.last for current price
```

---

## Pattern Verification Checklist

When reviewing any rule spec, verify:
- [ ] Event types match SDK exactly (see `SDK_EVENTS_QUICK_REFERENCE.txt`)
- [ ] Field names match SDK (`averagePrice`, not `avgPrice`)
- [ ] Event semantics are correct (ORDER_PLACED ≠ position opens)
- [ ] Position-tracking rules use all 3 events (OPENED, UPDATED, CLOSED)
- [ ] Null checks for `profitAndLoss` field present
- [ ] Event subscriptions consistent across all sections

---

## Reference Documents
- **SDK Event Patterns**: `SDK_EVENTS_QUICK_REFERENCE.txt`
- **Full Audit Report**: `RULES_ALIGNMENT_AUDIT_REPORT.md`
- **Rule Specifications**: `docs/specifications/unified/rules/RULE-*.md`

---

**Next Steps**:
1. Fix RULE-008 (CRITICAL) immediately
2. Fix RULE-004/005 (MEDIUM) for consistency
3. Clarify RULE-012 (LOW) when implementing market data feed
