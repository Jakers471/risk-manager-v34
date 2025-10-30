# Account ID Lookup - Why We Can't Show Current P&L in Rule Context

## 🎯 The Goal (What We Wanted)

Show current P&L vs limits in rule evaluation logs:

```
✅ Rule: DailyRealizedLoss → PASS (P&L: +$125.00 / -$500.00 limit)
✅ Rule: DailyRealizedProfit → PASS (P&L: +$125.00 / +$1,000.00 target)
```

Instead of just:
```
✅ Rule: DailyRealizedLoss → PASS
✅ Rule: DailyRealizedProfit → PASS
```

---

## ❌ The Problem: Events Don't Have Account ID

### **SDK Events Don't Include `account_id`**

When the SDK sends us events (ORDER_FILLED, POSITION_UPDATED, etc.), they contain:

```python
# ORDER_FILLED event data
{
    "symbol": "MNQ",
    "order_id": 12345,
    "side": "BUY",
    "quantity": 1,
    "price": 26360.00,
    "order_type": 2,
    # ... other order fields
}
```

**Notice: NO `account_id` field!** ❌

### **Why This Matters**

The `PnLTracker` needs an `account_id` to look up P&L:

```python
# This is what we need to call:
daily_pnl = rule.pnl_tracker.get_daily_pnl(account_id)

# But we don't have account_id in the event!
account_id = event.data.get("account_id")  # Returns None ❌
```

---

## 🔧 Why Don't We Just Add It?

### **Option 1: Store account_id in RiskEngine** ✅ (Best Solution)

**Current Architecture:**
```
RiskManager (has account_id from config)
  └─ RiskEngine (doesn't store account_id)
      └─ Rules (need account_id to query P&L)
```

**What We Could Do:**
```python
class RiskEngine:
    def __init__(self, config, event_bus, trading_integration, account_id):
        self.account_id = account_id  # ← Add this!
```

Then in `_get_rule_pass_context()`:
```python
# DailyRealizedLoss - show current P&L vs limit
if "DailyRealizedLoss" in rule_name:
    if hasattr(rule, "pnl_tracker") and hasattr(rule, "limit"):
        daily_pnl = rule.pnl_tracker.get_daily_pnl(engine.account_id)  # ← Use engine's account_id
        return f" (P&L: ${daily_pnl:+,.2f} / ${rule.limit:,.2f} limit)"
```

**Why We Didn't Do This Yet:**
- Need to thread `account_id` through manager → engine
- Need to update `_get_rule_pass_context()` to accept `engine` parameter
- Not critical for functionality (just nice-to-have for logging)

---

### **Option 2: Add account_id to Every Event** ❌ (Not Recommended)

**What We Could Do:**
```python
# In trading integration, modify every event:
risk_event = RiskEvent(
    event_type=EventType.ORDER_FILLED,
    data={
        "account_id": self.account_id,  # ← Add this to every event
        "symbol": symbol,
        "order_id": order.id,
        # ... rest of data
    }
)
```

**Why We Shouldn't:**
- Requires modifying 10+ event handlers
- Duplicates data (account_id same for all events)
- Still need to get account_id from somewhere (back to Option 1)

---

### **Option 3: Current Workaround** ✅ (What We're Doing Now)

**Show limits/targets without current P&L:**

```
✅ Rule: DailyRealizedLoss → PASS (limit: $-500.00)
✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
```

**Pros:**
- Works immediately ✅
- No architecture changes needed ✅
- Still informative (shows what limits are configured) ✅

**Cons:**
- Doesn't show current P&L ❌
- Can't see "how close are we to the limit?" ❌

---

## 📊 Where DOES P&L Get Tracked?

P&L tracking happens in **two places**:

### **1. PnLTracker (Database-Backed)**

```python
# PnLTracker stores P&L by account_id
pnl_tracker.add_trade_pnl(account_id="ACC123", pnl=-125.00)
pnl_tracker.get_daily_pnl(account_id="ACC123")  # Returns -125.00
```

**Location:** `src/risk_manager/state/pnl_tracker.py`
**Storage:** SQLite database (`data/risk_manager.db`)
**Used By:** DailyRealizedLoss, DailyRealizedProfit rules

### **2. RiskEngine State (In-Memory)**

```python
# RiskEngine tracks state for current session
self.daily_pnl = 0.0
self.current_positions = {}
```

**Location:** `src/risk_manager/core/engine.py`
**Storage:** In-memory (lost on restart)
**Used By:** Rule evaluation, P&L summary logging

---

## 💡 The Solution: Pass Engine to Helper

**Current Code:**
```python
def _get_rule_pass_context(self, rule: Any, event: RiskEvent) -> str:
    # Only has access to: rule, event
    # No access to: engine.account_id, engine.daily_pnl
```

**Better Code:**
```python
def _get_rule_pass_context(self, rule: Any, event: RiskEvent, engine: RiskEngine) -> str:
    # Now has access to: engine.account_id, engine.daily_pnl

    if "DailyRealizedLoss" in rule_name:
        if hasattr(rule, "pnl_tracker"):
            daily_pnl = engine.daily_pnl  # ← Use engine's cached value!
            return f" (P&L: ${daily_pnl:+,.2f} / ${rule.limit:,.2f} limit)"
```

**Even Better:**
```python
# In RiskEngine.evaluate_rules():
context = self._get_rule_pass_context(rule, event, self)
#                                                    ^^^^ Pass 'self' (engine)
```

---

## 🎯 Recommendation

**For now:** Keep current workaround (show limits only)
**Future enhancement:** Pass engine to helper, show current P&L

**Priority:** Low (logging cosmetic, not functional)

**Benefit:** Nice-to-have for monitoring, but rules work fine without it

---

## 📝 Summary

**Q:** Why can't we show current P&L in rule logs?
**A:** Events don't have `account_id`, and helper doesn't have access to engine state.

**Q:** Can we fix it?
**A:** Yes! Pass `engine` (which is `self`) to the helper function.

**Q:** Should we fix it now?
**A:** Not critical. Current logs show limits, which is good enough for now.

**Current Output:**
```
✅ Rule: DailyRealizedLoss → PASS (limit: $-500.00)
✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
✅ Rule: MaxContractsPerInstrument → PASS (MNQ: 1/3 max)
```

**Future Enhanced Output:**
```
✅ Rule: DailyRealizedLoss → PASS (P&L: +$125.00 / -$500.00 limit)
✅ Rule: DailyRealizedProfit → PASS (P&L: +$125.00 / +$1,000.00 target)
✅ Rule: MaxContractsPerInstrument → PASS (MNQ: 1/3 max)
```

---

**Want me to implement the enhancement now?** It's a quick 5-minute change!
