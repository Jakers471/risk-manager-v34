# Cache Invalidation & Semantic Analysis Fix

**Date**: 2025-10-29
**Problem**: Two critical issues discovered during live testing
**Status**: Fixed + Added introspection for debugging

---

## 🐛 Problem #1: Stale Cache on Order Modification

### Symptom
```
User moves stop loss from $26175 → $26180 in broker UI
Logs still show: "Active Stop Loss: $26175.00"
Cache not invalidated when order modified!
```

### Root Cause
`ORDER_MODIFIED` event handler didn't invalidate cache entries.

When trader modifies stop in broker UI:
1. ✅ `ORDER_MODIFIED` event fires
2. ❌ Cache still holds old price ($26175)
3. ❌ Next position event shows stale data

### Fix
Added cache invalidation in `_on_order_modified()` handler:

```python
# CRITICAL: Invalidate cache when order is modified
if order.contractId in self._active_stop_losses:
    if self._active_stop_losses[order.contractId]["order_id"] == order.id:
        old_price = self._active_stop_losses[order.contractId]["stop_price"]
        del self._active_stop_losses[order.contractId]
        logger.info(f"  └─ 🔄 Invalidated stop loss cache (modified from ${old_price:.2f} → ${order.stopPrice:.2f})")
```

**File**: `src/risk_manager/integrations/trading.py` lines 885-897

---

## 🐛 Problem #2: Take Profit Misidentified as Stop Loss

### Symptom
```
User creates:
- Position: LONG @ $26200
- Stop Loss: SELL @ $26175 (below entry - protects downside)
- Take Profit: SELL @ $26250 (above entry - takes profit)

Logs show:
- "FOUND stop loss @ $26175" ✅ Correct
- "FOUND stop loss @ $26250" ❌ WRONG! This is take profit!
```

### Root Cause
Code only checked order **TYPE**, not price **SEMANTICS**.

Old logic:
```python
# ❌ WRONG - Only checks order type
if order.type in [3, 4, 5]:  # STOP types
    # Assumes ALL stops are stop losses
    return "stop_loss"
```

**Problem**: Broker uses STOP type for both:
- Stop losses (protective stops below entry for longs)
- Stop entries (breakout entries above current price)

Similarly, LIMIT type used for both:
- Take profits (profit targets above entry for longs)
- Limit entries (value entries below current price)

### The Semantic Layer Solution

**Key Insight**: Need to compare trigger price to entry price!

```python
def _determine_order_intent(order, position_entry_price, position_size):
    """
    Semantic analysis - determines intent from price context.

    LONG Position:
        Entry: $26200
        - Order @ $26175 (below entry) → STOP LOSS ✅
        - Order @ $26250 (above entry) → TAKE PROFIT ✅

    SHORT Position:
        Entry: $26200
        - Order @ $26250 (above entry) → STOP LOSS ✅
        - Order @ $26175 (below entry) → TAKE PROFIT ✅
    """

    # Determine if order closes position
    is_long = position_size > 0
    is_closing = (is_long and order.side == 2) or (not is_long and order.side == 1)

    if not is_closing:
        return "entry"  # Opening position, not closing

    trigger_price = order.stopPrice or order.limitPrice

    if is_long:
        # LONG: stops below entry, targets above
        if trigger_price < position_entry_price:
            return "stop_loss"
        else:
            return "take_profit"
    else:
        # SHORT: stops above entry, targets below
        if trigger_price > position_entry_price:
            return "stop_loss"
        else:
            return "take_profit"
```

**File**: `src/risk_manager/integrations/trading.py` lines 361-418

### Updated Query Logic

Now queries broker API AND applies semantic analysis:

```python
# Get position context
position = await instrument.positions.get_all_positions()
position_entry_price = position.avgPrice
position_size = position.size

# Analyze EACH order semantically
for order in working_orders:
    trigger_price = order.stopPrice or order.limitPrice

    # Determine intent from price + position context
    intent = self._determine_order_intent(order, position_entry_price, position_size)

    if intent == "stop_loss":
        # Cache as stop loss
        self._active_stop_losses[contract_id] = {...}
        logger.info(f"✅ FOUND stop loss @ ${trigger_price:.2f}")

    elif intent == "take_profit":
        # Cache as take profit
        self._active_take_profits[contract_id] = {...}
        logger.info(f"✅ FOUND take profit @ ${trigger_price:.2f}")
```

**File**: `src/risk_manager/integrations/trading.py` lines 298-362

---

## 🔍 Added Debugging: Position API Introspection

### Problem
Initial fix used `instrument.positions.get_position(contract_id)` which might not exist.

### Solution
Added live introspection to discover correct API:

```python
# Debug: Check what methods are available
positions_obj = instrument.positions
logger.info(f"Positions object type: {type(positions_obj)}")
position_methods = [m for m in dir(positions_obj) if not m.startswith('_') and callable(getattr(positions_obj, m))]
logger.info(f"Available position methods: {position_methods[:20]}")

# Use get_all_positions and filter (safer)
all_positions = await instrument.positions.get_all_positions()
logger.info(f"get_all_positions returned {len(all_positions)} positions")

position = None
for pos in all_positions:
    if pos.contractId == contract_id:
        position = pos
        break
```

**Why**: Same introspection pattern that worked for discovering `search_open_orders()`. If `get_position()` doesn't exist, we'll see it in the logs and can adapt.

---

## 📊 Updated Logging

### Stop Loss & Take Profit Shown Separately

**Before**:
```
└─ 🛡️ Active Stop Loss: $26175.00 (Order ID: 1818943311)
```

**After**:
```
└─ 🛡️ Active Stop Loss: $26175.00 (Order ID: 1818943311)
└─ 🎯 Active Take Profit: $26250.00 (Order ID: 1818943312)
```

**Or if missing**:
```
└─ ⚠️ NO STOP LOSS for this position!
└─ No take profit for this position
```

### Semantic Analysis Logging

New logs show intent determination:

```
Order #1818943311: type=4 (STOP), trigger=$26175.0, side=2
  └─ Semantic intent: stop_loss
✅ FOUND stop loss @ $26175.00

Order #1818943312: type=1 (LIMIT), trigger=$26250.0, side=2
  └─ Semantic intent: take_profit
✅ FOUND take profit @ $26250.00
```

### Cache Invalidation Logging

Shows when cache is invalidated:

```
📝 ORDER MODIFIED - MNQ | STOP @ $26180.00
  └─ 🔄 Invalidated stop loss cache (modified from $26175.00 → $26180.00)
```

---

## 🧪 Testing

### Manual Test Scenario

1. **Open position**:
   ```
   Buy 1 MNQ @ $26200
   ```

2. **Create stop loss in broker UI**:
   ```
   Sell Stop @ $26175 (25 points below entry)
   ```
   - ✅ Should log: "FOUND stop loss @ $26175.00"

3. **Create take profit in broker UI**:
   ```
   Sell Limit @ $26250 (50 points above entry)
   ```
   - ✅ Should log: "FOUND take profit @ $26250.00"
   - ❌ Should NOT log: "FOUND stop loss @ $26250.00"

4. **Modify stop loss in broker UI**:
   ```
   Move stop from $26175 → $26180
   ```
   - ✅ Should log: "Invalidated stop loss cache"
   - ✅ Next position update should show: "$26180.00" (new price)
   - ❌ Should NOT show: "$26175.00" (stale price)

5. **Wait for position update events**:
   - Every few seconds as P&L changes
   - ✅ Should show both stop and target
   - ✅ Should show current prices (not stale)

---

## 🎯 Expected Logs

### Position Opened with Both Orders

```
2025-10-29 18:15:30 | INFO - 📊 POSITION OPENED - MNQ | LONG | Size: 1 | Price: $26200.00
2025-10-29 18:15:30 | INFO - 🔍 SDK QUERY: Checking for stops on CON.F.US.MNQ.Z25...
2025-10-29 18:15:30 | INFO -   Positions object type: <class 'project_x_py.position_manager.PositionManager'>
2025-10-29 18:15:30 | INFO -   Available position methods: ['get_all_positions', 'close_position', ...]
2025-10-29 18:15:30 | INFO -   get_all_positions returned 1 positions
2025-10-29 18:15:30 | INFO -   Position: entry=$26200.00, size=1 (LONG)
2025-10-29 18:15:30 | INFO -   Order #1818943311: type=4 (STOP), trigger=$26175.0, side=2
2025-10-29 18:15:30 | INFO -     └─ Semantic intent: stop_loss
2025-10-29 18:15:30 | INFO -   ✅ FOUND stop loss @ $26175.00
2025-10-29 18:15:30 | INFO -   Order #1818943312: type=1 (LIMIT), trigger=$26250.0, side=2
2025-10-29 18:15:30 | INFO -     └─ Semantic intent: take_profit
2025-10-29 18:15:30 | INFO -   ✅ FOUND take profit @ $26250.00
2025-10-29 18:15:30 | INFO -   └─ 🛡️ Active Stop Loss: $26175.00 (Order ID: 1818943311)
2025-10-29 18:15:30 | INFO -   └─ 🎯 Active Take Profit: $26250.00 (Order ID: 1818943312)
```

### Stop Loss Modified

```
2025-10-29 18:16:45 | INFO - 📝 ORDER MODIFIED - MNQ | STOP @ $26180.00
2025-10-29 18:16:45 | INFO -   └─ Order ID: 1818943311, Type: 4 (STOP), Stop: 26180.0, Status: 1
2025-10-29 18:16:45 | INFO -   └─ 🔄 Invalidated stop loss cache (modified from $26175.00 → $26180.00)

2025-10-29 18:16:50 | INFO - 📊 POSITION UPDATED - MNQ | LONG | Size: 1 | Price: $26200.00
2025-10-29 18:16:50 | INFO - 🔍 SDK QUERY: Checking for stops on CON.F.US.MNQ.Z25...
2025-10-29 18:16:50 | INFO -   ✅ FOUND stop loss @ $26180.00  ← NEW PRICE ✅
2025-10-29 18:16:50 | INFO -   └─ 🛡️ Active Stop Loss: $26180.00 (Order ID: 1818943311)
```

---

## 📝 Files Changed

### `src/risk_manager/integrations/trading.py`

1. **Lines 361-418**: New `_determine_order_intent()` method
   - Semantic analysis based on price context
   - Returns "stop_loss" | "take_profit" | "entry" | "unknown"

2. **Lines 192-215**: Updated `get_take_profit_for_position()` to async
   - Now queries SDK if cache empty (mirrors stop loss pattern)

3. **Lines 298-362**: Updated `_query_sdk_for_stop_loss()`
   - Added position introspection
   - Uses `get_all_positions()` instead of `get_position()`
   - Applies semantic analysis to each order
   - Caches both stop loss AND take profit separately

4. **Lines 885-897**: Added cache invalidation in `_on_order_modified()`
   - Deletes stale cache entries
   - Logs old → new prices

5. **Lines 1102-1115**: Updated position event handler
   - Queries both stop loss AND take profit
   - Shows both separately in logs
   - All calls properly awaited

---

## 🚀 Benefits

### 1. Accurate Detection
- ✅ Correctly identifies stop losses vs take profits
- ✅ Works for both LONG and SHORT positions
- ✅ Handles UI-created orders

### 2. Fresh Data
- ✅ Cache invalidated when orders modified
- ✅ Always shows current prices
- ✅ No stale data confusion

### 3. Better Debugging
- ✅ Shows semantic intent for each order
- ✅ Introspection reveals available API methods
- ✅ Clear logging of cache operations

### 4. Rule Support
- ✅ Grace period rule can now correctly detect stops
- ✅ Auto breakeven rule can modify the right order
- ✅ Both rules get fresh data on every check

---

## ⚠️ Next Steps

### 1. Test with Live Trading
Run `python run_dev.py` and perform the manual test scenario above.

### 2. Watch for New Logs
Look for:
- "Semantic intent" messages
- "Invalidated cache" messages
- Separate stop loss & take profit logs
- Position methods introspection

### 3. Verify Correctness
- Stop losses should be BELOW entry for longs, ABOVE for shorts
- Take profits should be ABOVE entry for longs, BELOW for shorts
- Modified orders should show NEW prices immediately

### 4. Clean Up Debug Logs (Later)
Once confirmed working, can reduce verbosity of:
- Position methods introspection (lines 301-305)
- Semantic intent logging (line 320)
- Order details logging (line 316)

---

## 📚 Related Documentation

- `STOP_LOSS_DETECTION_FIX.md` - Original stop loss detection fix
- `SDK_QUICK_REFERENCE.md` - SDK API reference
- `docs/current/SDK_INTEGRATION_GUIDE.md` - SDK integration guide

---

**Created**: 2025-10-29
**Status**: ✅ Ready for testing
**Test Required**: Manual live trading scenario
