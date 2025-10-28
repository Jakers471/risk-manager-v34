# Code Changes - Priority Summary

**Generated**: 2025-10-27
**Purpose**: Quick reference for what to fix FIRST
**Full Details**: See `CODE_CHANGES_CHECKLIST.md`

---

## TL;DR - Fix These 5 Things First

### 1. Add `realized_pnl` to TRADE_EXECUTED Events
**File**: `src/risk_manager/sdk/event_bridge.py` line 328
**Why**: RULE-003 (Daily Loss Limit) completely broken without this
**Fix**:
```python
"realized_pnl": trade_data.get("profitAndLoss"),  # ADD THIS LINE
```

---

### 2. Add `account_id` to ALL Events
**Files**: `src/risk_manager/sdk/event_bridge.py` lines 193, 209, 277, 328
**Why**: Multi-account support completely broken
**Fix**: Add to every event:
```python
"account_id": data.get("accountId"),  # ADD THIS LINE
```

---

### 3. Add ORDER_PLACED Fields (order_type, stop_price)
**File**: `src/risk_manager/sdk/event_bridge.py` line 267-280
**Why**: RULE-008 (Stop-Loss Check) completely broken without this
**Fix**:
```python
"order_type": order_data.get("type"),      # 1=Market, 2=Limit, 3=Stop
"stop_price": order_data.get("stopPrice"), # Critical for stop-loss detection
```

---

### 4. Emit POSITION_OPENED Events
**File**: `src/risk_manager/sdk/event_bridge.py` line 178-199
**Why**: RULE-008 needs this to start grace period timer
**Fix**: Track previous position sizes, emit POSITION_OPENED when size changes from 0 → non-zero

---

### 5. Add QUOTE_UPDATE Events
**File**: `src/risk_manager/sdk/event_bridge.py` (new handler)
**Why**: RULE-004/005 (Unrealized P&L) completely blocked without this
**Fix**: Implement `_on_quote_update` handler and subscribe to "quote_update" callback

---

## The Big Picture

**What's Wrong**:
1. EventBridge is missing **12 critical fields** across all event types
2. Rules are subscribing to **wrong events** (RULE-003 uses PNL_UPDATED instead of TRADE_EXECUTED)
3. RULE-008 specification is **fundamentally broken** (wrong event logic)
4. QUOTE_UPDATE events **never fire** (not implemented)
5. POSITION_OPENED events **never fire** (only emits POSITION_UPDATED)

**What Happens if We Don't Fix**:
- ❌ RULE-003 (Daily Loss): Can't track realized P&L → Won't work at all
- ❌ RULE-004/005 (Unrealized P&L): No quote updates → Won't work at all
- ❌ RULE-008 (Stop-Loss Check): No order type detection → Won't work at all
- ❌ Multi-account: Events have no account_id → Data mixing, crashes
- ❌ Tests: Fixtures have wrong fields → Everything fails

---

## Critical Fixes by File

### `src/risk_manager/sdk/event_bridge.py` (12 changes)
**Priority**: CRITICAL
**Impact**: Blocks 3 rules + multi-account support

**Missing Fields**:
- `realized_pnl` in TRADE_EXECUTED (line 328)
- `account_id` in ALL events (lines 193, 209, 277, 328)
- `order_type`, `stop_price` in ORDER_PLACED (line 277)
- `contract_id` in ORDER events (line 277)

**Missing Event Types**:
- POSITION_OPENED never emitted (need state tracking)
- QUOTE_UPDATE not implemented (need new handler)

**Wrong Data Types**:
- Timestamps are strings, should be datetime objects (lines 193, 209, 277, 328)

---

### `src/risk_manager/core/events.py` (3 changes)
**Priority**: CRITICAL
**Impact**: Blocks RULE-004/005

**Missing Event Types**:
- QUOTE_UPDATE (doesn't exist in enum)
- NEW_BAR (optional)
- DATA_UPDATE (optional)

---

### `src/risk_manager/rules/daily_loss.py` (3 changes)
**Priority**: HIGH
**Impact**: RULE-003 won't work

**Wrong Event Subscription**:
- Currently: Subscribes to PNL_UPDATED, POSITION_CLOSED
- Should: Subscribe to TRADE_EXECUTED
- Needs: Extract `realized_pnl` from event.data
- Needs: Check for `None` (skip half-turn trades)

---

### `src/risk_manager/rules/stop_loss_check.py` (NEW FILE)
**Priority**: HIGH
**Impact**: RULE-008 won't work

**Spec is Wrong**:
- Current spec: Subscribe to ORDER_PLACED "when position opens"
- Correct logic: Subscribe to POSITION_OPENED + ORDER_PLACED
- Must check: `order_type == 3` (STOP order)
- Must check: `stop_price` exists

---

### `src/risk_manager/rules/daily_unrealized_loss.py` (NEW FILE)
**Priority**: HIGH
**Impact**: RULE-004 won't work

**Not Implemented**:
- Subscribe to: POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED, QUOTE_UPDATE
- Calculate: Unrealized P&L using current price vs entry price
- Requires: Quote cache in RiskEngine

---

## What to Fix in What Order

### Hour 1-2: EventBridge Fields
1. Add `realized_pnl` to TRADE_EXECUTED
2. Add `account_id` to ALL events
3. Fix timestamps (datetime objects)
4. Add `order_type`, `stop_price` to ORDER events

**Test**: Smoke test should show events with correct fields

---

### Hour 3-4: Event Types
1. Add QUOTE_UPDATE to EventType enum
2. Implement POSITION_OPENED detection (state tracking)
3. Implement QUOTE_UPDATE handler

**Test**: Should see POSITION_OPENED and QUOTE_UPDATE in logs

---

### Hour 5-6: Fix RULE-003
1. Change to TRADE_EXECUTED event
2. Extract `realized_pnl` from event.data
3. Add null check for half-turns

**Test**: RULE-003 should track daily loss correctly

---

### Hour 7-8: Implement RULE-004/005
1. Add quote_cache to RiskEngine
2. Create daily_unrealized_loss.py
3. Create max_unrealized_profit.py

**Test**: RULE-004/005 should calculate unrealized P&L

---

### Hour 9-10: Implement RULE-008
1. Create stop_loss_check.py
2. Implement grace period timer
3. Implement stop-loss detection (order_type == 3)

**Test**: RULE-008 should detect stop-loss orders

---

### Hour 11-12: Fix Tests & Docs
1. Update test fixtures
2. Fix documentation specs
3. Run full test suite

**Test**: All tests should pass

---

## Verification Checklist

After fixing, verify:

**Events**:
- [ ] TRADE_EXECUTED has `realized_pnl` field
- [ ] All events have `account_id` field
- [ ] ORDER_PLACED has `order_type` and `stop_price`
- [ ] POSITION_OPENED fires when position opens
- [ ] QUOTE_UPDATE fires on price changes
- [ ] All timestamps are datetime objects (not strings)

**Rules**:
- [ ] RULE-003 subscribes to TRADE_EXECUTED
- [ ] RULE-003 checks for `realized_pnl is None`
- [ ] RULE-004/005 subscribe to QUOTE_UPDATE
- [ ] RULE-008 subscribes to POSITION_OPENED + ORDER_PLACED
- [ ] RULE-008 checks `order_type == 3` for stop orders

**Tests**:
- [ ] Smoke test passes (events flow through)
- [ ] Unit tests pass (rule logic works)
- [ ] Integration tests pass (SDK integration works)
- [ ] Gate test passes (full suite + smoke)

---

## Quick Command Reference

```bash
# After each fix, run smoke test
python run_tests.py
# Select [s] for smoke test

# After rules fixed, run gate test
python run_tests.py
# Select [g] for gate test (unit + integration + smoke)

# After everything, run full suite
python run_tests.py
# Select [1] for all tests
```

---

## Expected Timeline

**Day 1** (6-8 hours):
- Fix EventBridge (12 changes)
- Add event types (3 changes)
- Smoke test passes

**Day 2** (6-8 hours):
- Fix RULE-003 (3 changes)
- Implement RULE-004/005 (2 new files)
- Implement RULE-008 (1 new file)
- Integration tests pass

**Day 3** (4-6 hours):
- Update test fixtures
- Fix documentation
- Full test suite passes

**Total**: 2-3 days (16-22 hours)

---

## Gotchas to Watch For

1. **Timestamp serialization**: Don't convert to string in EventBridge, only in `RiskEvent.to_dict()`
2. **Half-turn trades**: `realized_pnl` is `None` for opening trades, must check!
3. **QUOTE_UPDATE flood**: Quote events fire on every tick (high frequency), consider throttling
4. **POSITION_OPENED detection**: Need to track previous size to detect 0 → non-zero transitions
5. **Stop order detection**: Must check `order_type == 3`, not just `stop_price` exists

---

## Most Common Mistakes to Avoid

❌ **Don't**: Convert timestamps to strings in EventBridge
✅ **Do**: Keep as datetime objects, convert in to_dict()

❌ **Don't**: Forget to check `realized_pnl is None`
✅ **Do**: Skip half-turn trades in RULE-003

❌ **Don't**: Subscribe RULE-008 to ORDER_PLACED only
✅ **Do**: Subscribe to POSITION_OPENED + ORDER_PLACED

❌ **Don't**: Assume all position events are POSITION_UPDATED
✅ **Do**: Detect POSITION_OPENED when size changes from 0

❌ **Don't**: Emit every QUOTE_UPDATE event
✅ **Do**: Add throttling (max once per 100ms)

---

## Success Criteria

**After all fixes**:
1. ✅ All 48 checkboxes in CODE_CHANGES_CHECKLIST.md marked done
2. ✅ Smoke test passes (exit code 0)
3. ✅ Gate test passes (unit + integration + smoke)
4. ✅ Full test suite passes
5. ✅ All 8 checkpoints log correctly in smoke test
6. ✅ RULE-003, RULE-004, RULE-005, RULE-008 all work correctly

---

**Next Step**: Start with Hour 1-2 (EventBridge fields)

See `CODE_CHANGES_CHECKLIST.md` for complete details and code examples.

---

**End of Priority Summary**
