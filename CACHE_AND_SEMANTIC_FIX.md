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

## 🐛 Problem #3: Second Protective Order Not Detected Until Moved

### Symptom
```
Sequence:
1. Entry fills → Detected immediately ✅
2. Place first order (stop OR take profit) → Detected immediately ✅
3. Place second order (whichever isn't placed yet) → NOT detected ❌
4. Move second order in broker UI → Suddenly detected ✅
```

**User Description**: "IF I GET FILLED ON AN ENTRY, EVENT RECEIVED RIGHT AWAY. IF I THEN PLACE STOP/TAKE PROFIT, THAT GETS RECEIVED RIGHT AWAY. THEN IF I GO TO PLACE THE TAKE PROFIT OR STOP, WHICHEVER WASN'T ALREADY CREATED, IT DOESN'T GET THE EVENT UNTIL I MOVE IT!"

### Root Cause: Event Deduplication Blocking Queries

**Discovery**: The broker SDK fires 3x identical POSITION_UPDATED events (one per instrument subscription). We use deduplication to prevent processing the same event 3 times.

**The Problem**:
1. First protective order placement → Position changes (now has protection) → POSITION_UPDATED event fires → Query runs → Order detected ✅
2. Second protective order placement → Position data DOESN'T change (still size=1, entry=$26178.75, P&L same) → Event IS fired but data is identical → Deduplication check blocks query from running ❌
3. Moving the order → ORDER_MODIFIED event → Cache invalidated → Next POSITION_UPDATED → Query runs with empty cache → Order detected ✅

**Code Location**: Lines 1154-1158 (OLD VERSION):
```python
# Check for duplicate (prevents 3x events from 3 instruments)
dedup_key = f"{contract_id}_{action_name}"
if self._is_duplicate_event(f"position_{action_name.lower()}", dedup_key):
    return  # ❌ EXIT HERE - no query ran!
```

**Why It Happened**: Protective order queries ran AFTER the deduplication check. If the event was marked as duplicate, the method returned early, and queries never executed.

### Fix: Query BEFORE Deduplication

**Solution**: Move protective order checking to run BEFORE the deduplication check, so queries execute on EVERY POSITION_UPDATED event (even duplicates).

**New Code** (Lines 1125-1158):
```python
# CRITICAL: Check protective orders BEFORE dedup
# Second order placements don't trigger unique events!
# Must query on EVERY event to catch them
if action_name in ["OPENED", "UPDATED"]:
    logger.debug(f"🔍 Checking protective orders on {contract_id} (BEFORE dedup)...")

    # Always invalidate cache and query fresh
    if contract_id in self._active_stop_losses:
        del self._active_stop_losses[contract_id]
    if contract_id in self._active_take_profits:
        del self._active_take_profits[contract_id]

    # Query with position data from event
    stop_loss_early = await self.get_stop_loss_for_position(
        contract_id, avg_price, pos_type
    )
    take_profit_early = await self.get_take_profit_for_position(
        contract_id, avg_price, pos_type
    )

    # Log findings
    if stop_loss_early:
        logger.info(f"  🛡️  Stop Loss: ${stop_loss_early['stop_price']:.2f} (ID: {stop_loss_early['order_id']})")
    else:
        logger.warning(f"  ⚠️  NO STOP LOSS")

    if take_profit_early:
        logger.info(f"  🎯 Take Profit: ${take_profit_early['take_profit_price']:.2f} (ID: {take_profit_early['order_id']})")

# Check for duplicate (prevents 3x events from 3 instruments)
# Use contract_id + action for deduplication key
dedup_key = f"{contract_id}_{action_name}"
if self._is_duplicate_event(f"position_{action_name.lower()}", dedup_key):
    return  # Exit after protective order check
```

**Key Changes**:
1. ✅ Queries run FIRST (lines 1128-1153)
2. ✅ Deduplication check runs SECOND (lines 1154-1158)
3. ✅ Cache always invalidated before queries
4. ✅ Even duplicate events trigger queries

**File**: `src/risk_manager/integrations/trading.py` lines 1125-1158

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

### Manual Test Scenario (CRITICAL: Tests All 3 Fixes)

**Test 1: Entry + First Protective Order**
1. **Open position**:
   ```
   Buy 1 MNQ @ $26200
   ```
   - ✅ Should log: "POSITION OPENED"

2. **Create stop loss in broker UI** (first protective order):
   ```
   Sell Stop @ $26175 (25 points below entry)
   ```
   - ✅ Should log: "🛡️ Stop Loss: $26175.00" within 6-10 seconds
   - Tests: Problem #1 (cache) and Problem #2 (semantic analysis)

**Test 2: Second Protective Order** (CRITICAL - Tests Problem #3)
3. **Create take profit in broker UI** (second protective order):
   ```
   Sell Limit @ $26250 (50 points above entry)
   ```
   - ✅ Should log: "🎯 Take Profit: $26250.00" within 6-10 seconds
   - ❌ Should NOT require moving the order first! (Problem #3 fix)
   - ✅ Should correctly identify as "take_profit" not "entry" (Problem #2 fix)

**Test 3: SHORT Position Semantic Analysis** (Tests Problem #2)
4. **Open SHORT position**:
   ```
   Sell Short 1 MNQ @ $26178
   ```

5. **Create stop loss ABOVE entry**:
   ```
   Buy Stop @ $26194 (16 points above entry)
   ```
   - ✅ Should log: "🛡️ Stop Loss: $26194.00"

6. **Create take profit BELOW entry**:
   ```
   Buy Limit @ $26149 (29 points below entry)
   ```
   - ✅ Should log: "🎯 Take Profit: $26149.00"
   - ❌ Should NOT log as "entry" (Problem #2 fix validated)

**Test 4: Cache Invalidation** (Tests Problem #1)
7. **Modify stop loss in broker UI**:
   ```
   Move stop from $26175 → $26180
   ```
   - ✅ Should log: "🔄 Invalidated stop loss cache" (if ORDER_MODIFIED fires)
   - ✅ Next position update should show: "$26180.00" (new price)
   - ❌ Should NOT show: "$26175.00" (stale price)

8. **Wait for natural position update events**:
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

**Problem #1 Fixes (Cache Staleness)**:
1. **Lines 1046-1059**: Cache invalidation in `_on_order_modified()`
   - Invalidates BOTH stop loss AND take profit cache
   - Logs when cache is cleared
   - Next query will fetch fresh data

2. **Lines 1131-1135**: Cache invalidation on EVERY position update
   - Forces fresh queries even without ORDER_MODIFIED events
   - Ensures UI modifications are eventually detected

**Problem #2 Fixes (Semantic Misidentification)**:
3. **Lines 458-520**: Rewritten `_determine_order_intent()` method
   - NOW uses `position_type` (1=LONG, 2=SHORT) instead of `position_size` sign
   - Correctly identifies SHORT position take profits below entry
   - STOP orders (3, 4, 5) → Always "stop_loss" for existing positions
   - LIMIT orders (1) → Analyzed semantically based on price + position type

4. **Lines 170-199**: Updated method signatures for `position_type`
   - `get_stop_loss_for_position()` now accepts `position_type: int`
   - `get_take_profit_for_position()` now accepts `position_type: int`
   - All query methods pass `position_type` to semantic analysis

5. **Lines 253-362**: Updated `_query_sdk_for_stop_loss()`
   - Accepts `position_type` parameter
   - Gets `position.type` from broker (1=LONG, 2=SHORT)
   - Passes correct type to `_determine_order_intent()`
   - Logs position direction for debugging

**Problem #3 Fixes (Second Order Detection)**:
6. **Lines 1125-1158**: CRITICAL - Moved queries BEFORE deduplication
   - Protective order checking now runs FIRST
   - Cache invalidation before queries
   - Queries execute on EVERY event (even duplicates)
   - Deduplication check runs AFTER queries
   - Solves "second order not detected until moved" issue

7. **Lines 1177-1182**: Updated position event handler calls
   - Passes `pos_type` instead of `pos_size` to query methods
   - Shows both stop loss AND take profit separately
   - All async calls properly awaited

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
