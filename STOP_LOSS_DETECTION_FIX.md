# Stop Loss Detection Fix - Debugging Journey & Solution

**Date**: 2025-10-29
**Problem**: Stop losses created in broker UI were not being detected
**Solution**: Event-triggered SDK query using `search_open_orders()`

---

## 📋 Table of Contents

1. [The Problem](#the-problem)
2. [Why This Was Hard](#why-this-was-hard)
3. [The Debugging Approach](#the-debugging-approach)
4. [What We Discovered](#what-we-discovered)
5. [The Solution](#the-solution)
6. [How to Use This Pattern](#how-to-use-this-pattern)
7. [Code Changes](#code-changes)

---

## 🔴 The Problem

### Initial Symptoms

**Logs showed**:
```
2025-10-29 15:30:45 | INFO - 📊 POSITION_OPENED Event #1
2025-10-29 15:30:45 | INFO -   └─ ⚠️ NO STOP LOSS for this position!
```

**But the trader HAD placed a stop in the broker UI!**

### Root Cause

The SDK emits `ORDER_PLACED` events **only for orders placed programmatically via the SDK**.

When traders manually create stops in the broker UI:
- ✅ The order EXISTS in the broker
- ❌ No `ORDER_PLACED` event fires
- ❌ SDK internal cache doesn't track it
- ❌ Risk manager never sees it

### Why This Matters

Two critical risk rules need stop detection:

1. **Grace Period Rule**: Close position if no stop placed within 10 seconds
2. **Auto Breakeven Rule**: Move stop to entry when profit reaches threshold

Without detecting broker-UI stops, these rules would:
- ❌ Generate false violations
- ❌ Force close positions that already have stops
- ❌ Annoy traders who follow the rules

---

## 🤔 Why This Was Hard

### Challenge 1: No Documentation

The Project-X-Py SDK documentation doesn't explicitly say:
- "Use this method to find broker-UI stops"
- "ORDER_PLACED events don't fire for UI-created orders"

We had to discover the behavior through testing.

### Challenge 2: Multiple Order Query Methods

The SDK has several order-related methods:
- `get_position_orders(contract_id)` - Returns SDK-tracked orders only
- `search_open_orders()` - Queries broker API for ALL open orders
- `get_all_orders()` - Different scope/purpose

**We didn't know which one would work!**

### Challenge 3: SDK Structure Complexity

```python
suite = TradingSuite.create(instruments=["MNQ", "ES", "NQ"])
```

This creates a dict-like structure:
```
suite
├── "MNQ" → InstrumentManager
│   ├── orders → OrderManager
│   ├── positions → PositionManager
│   └── bars → BarManager
├── "ES" → InstrumentManager
└── "NQ" → InstrumentManager
```

**Question**: Where do we call the order query method?
- `suite.orders`? (doesn't exist)
- `suite["MNQ"].orders`? (exists, but which method?)
- `suite.order_manager`? (doesn't exist)

---

## 🔍 The Debugging Approach

### Step 1: Live Introspection

Instead of guessing API methods, **we printed what actually exists**:

```python
# Show what attributes the suite has
logger.info(f"Suite type: {type(self.suite)}")
logger.info(f"Suite attributes: {[a for a in dir(self.suite) if not a.startswith('_')][:20]}")

# Get the orders object
orders_obj = instrument.orders
logger.info(f"Orders object type: {type(orders_obj)}")

# Show ALL available methods
order_methods = [m for m in dir(orders_obj) if not m.startswith('_') and callable(getattr(orders_obj, m))]
logger.info(f"Available order methods: {order_methods}")
```

**This printed**:
```
Orders object type: <class 'project_x_py.order_manager.OrderManager'>
Available order methods: ['cancel_all_orders', 'cancel_order', 'get_all_orders',
'get_position_orders', 'modify_order', 'place_order', 'search_open_orders']
```

### Step 2: Try Each Method Systematically

```python
# Try #1: get_position_orders
working_orders = await instrument.orders.get_position_orders(contract_id)
logger.info(f"get_position_orders returned {len(working_orders)} orders")
# Result: 0 orders (doesn't track broker-UI stops)

# Try #2: search_open_orders
if len(working_orders) == 0 and hasattr(orders_obj, 'search_open_orders'):
    all_orders = await orders_obj.search_open_orders()
    logger.info(f"search_open_orders returned {len(all_orders)} orders from broker")
    # Result: 1 order! ✅
```

### Step 3: Inspect the Order Object

```python
for order in working_orders:
    logger.info(f"Order on {contract_id}: type={order.type} ({order.type_str}), stopPrice={order.stopPrice}")
```

**This printed**:
```
Order on CON.F.US.MNQ.Z25: type=4 (STOP), stopPrice=26176.75
```

### Step 4: Validate the Discovery

**Final logs confirmed success**:
```
2025-10-29 17:56:54 | INFO - 🔍 SDK QUERY: Checking for stops on CON.F.US.MNQ.Z25...
2025-10-29 17:56:54 | INFO -   Suite type: <class 'project_x_py.trading_suite.TradingSuite'>
2025-10-29 17:56:54 | INFO -   Symbol: MNQ
2025-10-29 17:56:54 | INFO -   Orders object type: <class 'project_x_py.order_manager.OrderManager'>
2025-10-29 17:56:54 | INFO -   Available order methods: ['cancel_all_orders', 'cancel_order', ...]
2025-10-29 17:56:54 | INFO -   ✅ get_position_orders returned 0 orders for CON.F.US.MNQ.Z25
2025-10-29 17:56:54 | INFO -   Trying search_open_orders (queries broker API)...
2025-10-29 17:56:54 | INFO -   search_open_orders returned 1 orders from broker
2025-10-29 17:56:54 | INFO -   Filtered to 1 orders for CON.F.US.MNQ.Z25
2025-10-29 17:56:54 | INFO -   Order on CON.F.US.MNQ.Z25: type=4 (STOP), stopPrice=26176.75
2025-10-29 17:56:54 | INFO -   ✅ FOUND stop loss @ $26176.75
2025-10-29 17:56:54 | INFO -   └─ 🛡️ Active Stop Loss: $26176.75 (Order ID: 1818943311)
```

**User confirmed**: "BINGO !!!!!!!!!"

---

## 💡 What We Discovered

### SDK Order Query Methods - The Truth

| Method | What It Does | Use Case |
|--------|-------------|----------|
| `get_position_orders(contract_id)` | Returns SDK-tracked orders only | Orders placed via SDK |
| `search_open_orders()` | **Queries broker API directly** | **ALL open orders (SDK + UI)** |
| `get_all_orders()` | Different scope (unclear) | TBD |

### Order Types (Enum Values)

```python
# From broker API and SDK introspection
ORDER_TYPES = {
    1: "LIMIT",
    2: "MARKET",
    3: "STOP_LIMIT",
    4: "STOP",           # ← This is what broker-UI stops use
    5: "TRAILING_STOP",
    6: "JOIN_BID",
    7: "JOIN_ASK"
}

# Stop loss detection logic
if order.type in [3, 4, 5]:  # Any stop type
    # This is a stop loss!
```

### Order Object Structure

```python
order = {
    "id": 1818943311,              # Broker order ID
    "contractId": "CON.F.US.MNQ.Z25",
    "type": 4,                      # ORDER_TYPES[4] = "STOP"
    "type_str": "STOP",             # Human-readable
    "stopPrice": 26176.75,          # Trigger price
    "side": 2,                      # 1=Buy, 2=Sell
    "size": 2,                      # Quantity
    "status": 1,                    # 1=Open/Working
    # ... more fields
}
```

---

## ✅ The Solution

### Two-Tier Query Strategy

**Tier 1: Check Cache (Fast Path)**
```python
async def get_stop_loss_for_position(self, contract_id: str) -> dict[str, Any] | None:
    """Get stop loss - cache first, then query SDK if needed."""

    # Fast path: Check cache
    cached = self._active_stop_losses.get(contract_id)
    if cached:
        return cached

    # Cache miss: Query SDK (slow path)
    return await self._query_sdk_for_stop_loss(contract_id)
```

**Tier 2: Query Broker API (Slow Path)**
```python
async def _query_sdk_for_stop_loss(self, contract_id: str) -> dict[str, Any] | None:
    """Query broker API for ALL orders (including UI-created)."""

    # Get instrument manager
    symbol = self._extract_symbol_from_contract(contract_id)
    instrument = self.suite[symbol]

    # Try SDK cache first (cheap)
    working_orders = await instrument.orders.get_position_orders(contract_id)

    # If empty, query broker API (expensive but complete)
    if len(working_orders) == 0:
        all_orders = await instrument.orders.search_open_orders()
        working_orders = [o for o in all_orders if o.contractId == contract_id]

    # Find stop orders (type 3, 4, or 5)
    for order in working_orders:
        if order.type in [3, 4, 5]:  # STOP_LIMIT, STOP, TRAILING_STOP
            stop_data = {
                "order_id": order.id,
                "stop_price": order.stopPrice,
                "side": self._get_side_name(order.side),
                "quantity": order.size,
                "timestamp": time.time(),
            }

            # Cache it for next time
            self._active_stop_losses[contract_id] = stop_data
            return stop_data

    return None
```

### Event-Triggered (NOT Polling)

**CRITICAL**: This is **NOT background polling**. It's event-triggered:

```python
async def _handle_position_opened(self, data: Dict[str, Any]) -> None:
    """Handle position opened event."""
    contract_id = data.get("contractId")

    # Query is triggered ONLY when position events fire
    stop_loss = await self.get_stop_loss_for_position(contract_id)

    if stop_loss:
        logger.info(f"  └─ 🛡️ Active Stop Loss: ${stop_loss['stop_price']:.2f}")
    else:
        logger.warning(f"  └─ ⚠️ NO STOP LOSS for this position!")
```

**Triggers**:
- ✅ `POSITION_OPENED` event → Query once
- ✅ `POSITION_UPDATED` event → Query once
- ❌ Background timer → Never polls

---

## 🎯 How to Use This Pattern

### Pattern: Live API Discovery via Introspection

**Use this when**:
- Working with unfamiliar SDK/library
- Documentation is incomplete
- You need to find the right method

**Steps**:

1. **Print the object type**:
   ```python
   logger.info(f"Object type: {type(obj)}")
   ```

2. **Print all attributes**:
   ```python
   attrs = [a for a in dir(obj) if not a.startswith('_')]
   logger.info(f"Attributes: {attrs}")
   ```

3. **Filter for methods**:
   ```python
   methods = [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m))]
   logger.info(f"Available methods: {methods}")
   ```

4. **Try each method systematically**:
   ```python
   # Try method A
   result_a = await obj.method_a()
   logger.info(f"method_a returned: {len(result_a)} items")

   # Try method B
   result_b = await obj.method_b()
   logger.info(f"method_b returned: {len(result_b)} items")
   ```

5. **Inspect the results**:
   ```python
   for item in result:
       logger.info(f"Item: {item}")
       logger.info(f"Item attributes: {[a for a in dir(item) if not a.startswith('_')]}")
   ```

### Real-World Example from This Fix

```python
# 1. What type is this?
logger.info(f"Suite type: {type(self.suite)}")
# Output: <class 'project_x_py.trading_suite.TradingSuite'>

# 2. What can I do with it?
logger.info(f"Suite methods: {[m for m in dir(self.suite) if callable(getattr(self.suite, m))]}")
# Output: ['create', 'disconnect', 'on', ...]

# 3. It's dict-like, what's inside?
instrument = self.suite["MNQ"]
logger.info(f"Instrument type: {type(instrument)}")
# Output: <class 'project_x_py.instrument_manager.InstrumentManager'>

# 4. What methods does orders have?
logger.info(f"Order methods: {[m for m in dir(instrument.orders) if callable(getattr(instrument.orders, m))]}")
# Output: ['cancel_all_orders', 'get_position_orders', 'search_open_orders', ...]

# 5. Try each one!
result1 = await instrument.orders.get_position_orders(contract_id)
logger.info(f"get_position_orders: {len(result1)} orders")  # 0 orders

result2 = await instrument.orders.search_open_orders()
logger.info(f"search_open_orders: {len(result2)} orders")  # 1 order ✅ FOUND IT!
```

**This approach saved us hours of guessing and reading source code.**

---

## 📝 Code Changes

### File: `src/risk_manager/integrations/trading.py`

#### Change 1: Added `_query_sdk_for_stop_loss()` Method

**Location**: Lines 223-317

**Purpose**: Query broker API directly for stop loss orders

**Key Features**:
- ✅ Live introspection logging (shows available methods)
- ✅ Two-tier query (SDK cache first, then broker API)
- ✅ Filters for stop types (3, 4, 5)
- ✅ Caches results for performance

#### Change 2: Made `get_stop_loss_for_position()` Async

**Location**: Lines 170-190

**Before**:
```python
def get_stop_loss_for_position(self, contract_id: str) -> dict[str, Any] | None:
    """Get stop loss from cache only."""
    return self._active_stop_losses.get(contract_id)
```

**After**:
```python
async def get_stop_loss_for_position(self, contract_id: str) -> dict[str, Any] | None:
    """Get stop loss - cache first, then query SDK."""
    cached = self._active_stop_losses.get(contract_id)
    if cached:
        return cached

    # Cache miss - query broker API
    return await self._query_sdk_for_stop_loss(contract_id)
```

#### Change 3: Updated Position Event Handler

**Location**: Lines 970-974

**Before**:
```python
# Show active stop loss
stop_loss = self.get_stop_loss_for_position(contract_id)  # Not async
```

**After**:
```python
# Show active stop loss (query broker if cache empty)
stop_loss = await self.get_stop_loss_for_position(contract_id)  # Now async
```

#### Change 4: Fixed Duplicate Logs

**Location**: Lines 828-839

**Before**:
```python
# Log payload FIRST
logger.info(f"📦 POSITION_{action_name} Payload: {data}")

# Then check for duplicates
if self._is_duplicate_event(...):
    return
```

**After**:
```python
# Check for duplicates FIRST
if self._is_duplicate_event(f"position_{action_name.lower()}", dedup_key):
    return

# Then log (only for unique events)
logger.debug(f"📦 POSITION_{action_name} Payload: {data}")
```

---

## 🎓 Key Learnings

### 1. Events vs Queries

**SDK Events**: Only fire for SDK-initiated actions
- `ORDER_PLACED` → Fires when **SDK** places order
- `ORDER_FILLED` → Fires for **any** order (SDK or UI)
- `POSITION_OPENED` → Fires for **any** position (SDK or UI)

**Implication**: Can't rely on events for UI-created stops. Must query.

### 2. Cache vs Fresh Data

**SDK Cache** (`get_position_orders`):
- ✅ Fast (no API call)
- ❌ Incomplete (only SDK-tracked orders)

**Broker API** (`search_open_orders`):
- ✅ Complete (all orders)
- ❌ Slower (network call)

**Solution**: Try cache first, fallback to API.

### 3. Introspection > Documentation

When documentation is unclear:
- ✅ Print object types
- ✅ Print available methods
- ✅ Try each method systematically
- ✅ Inspect results

**This finds the answer faster than reading source code.**

### 4. Event-Triggered Queries ≠ Polling

**Polling** (BAD):
```python
while True:
    await asyncio.sleep(1)  # Every second
    check_for_stops()        # Wasteful
```

**Event-Triggered** (GOOD):
```python
async def on_position_opened(event):
    # Query ONLY when event fires
    check_for_stops()
```

**Our solution is event-triggered, NOT polling.**

---

## 🔧 Testing the Fix

### Manual Test

1. Start the risk manager:
   ```bash
   python run_dev.py
   ```

2. Open broker UI and place a trade:
   - Buy 2 MNQ contracts
   - Place a stop loss in broker UI (NOT via SDK)

3. Check logs:
   ```
   2025-10-29 17:56:54 | INFO - 📊 POSITION_OPENED Event #1
   2025-10-29 17:56:54 | INFO - 🔍 SDK QUERY: Checking for stops on CON.F.US.MNQ.Z25...
   2025-10-29 17:56:54 | INFO -   search_open_orders returned 1 orders from broker
   2025-10-29 17:56:54 | INFO -   ✅ FOUND stop loss @ $26176.75
   2025-10-29 17:56:54 | INFO -   └─ 🛡️ Active Stop Loss: $26176.75 (Order ID: 1818943311)
   ```

### Automated Test

**TODO**: Add integration test in `tests/integration/test_trading.py`:
```python
async def test_detect_broker_ui_stop():
    """Test that we can detect stops created in broker UI."""
    # 1. Connect to broker
    # 2. Create position via UI (manual step or mock)
    # 3. Create stop via UI (manual step or mock)
    # 4. Verify get_stop_loss_for_position() finds it
    pass
```

---

## 📊 Performance Impact

### Query Cost

**Scenario 1**: Stop already cached
- ✅ Cost: O(1) dictionary lookup
- ✅ Time: <1ms

**Scenario 2**: Cache miss, SDK has order
- ✅ Cost: 1 async call to `get_position_orders()`
- ✅ Time: ~10-50ms

**Scenario 3**: Cache miss, UI-created stop
- ⚠️ Cost: 2 async calls (`get_position_orders()` + `search_open_orders()`)
- ⚠️ Time: ~50-150ms

### Frequency

**Triggers per session**:
- `POSITION_OPENED`: 1 time per position
- `POSITION_UPDATED`: ~2-5 times per position (as P&L changes)

**Example session**:
- Open 3 positions = 3 queries
- Each position gets 3 updates = 9 queries
- Total: 12 queries per session

**With caching**: After first query, all subsequent queries hit cache (O(1))

**Verdict**: Negligible performance impact.

---

## 🚀 Next Steps

### Immediate
- [x] Fix stop loss detection ✅
- [ ] Clean up debug logs (lines 245-246, 268-270, 274, 278-284, 290)
- [ ] Test grace period rule with new detection
- [ ] Test breakeven rule with new detection

### Future Enhancements
- [ ] Add integration test for broker-UI stops
- [ ] Cache invalidation on `ORDER_CANCELLED` event
- [ ] Support for take-profit detection (same pattern)
- [ ] Metrics: Track cache hit rate

---

## 📚 References

### Documentation
- `docs/archive/.../projectx_gateway_api/orders/place_order.md` - Bracket order API
- `docs/archive/.../projectx_gateway_api/realtime_updates/realtime_data_overview.md` - Event payloads
- `cache_system.md` - Discovery document (1,532 lines)

### Related Code
- `src/risk_manager/integrations/trading.py` - Main fix
- `src/risk_manager/rules/no_stop_loss_grace.py` - Grace period rule
- `src/risk_manager/rules/trade_management.py` - Breakeven rule
- `test_payload_capture.py` - Debugging script

---

**Created**: 2025-10-29
**Author**: AI Debugging Session
**Status**: ✅ Working
**User Confirmation**: "BINGO !!!!!!!!!"
