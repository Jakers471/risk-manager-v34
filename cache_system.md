# Stop Loss Cache System - Architecture Decision

**Date**: 2025-10-29
**Status**: Analysis Complete - Implementation Pending
**Decision**: Use SDK as Source of Truth (Option A)

---

## 🎯 Problem Statement

We need to track active stop loss orders for open positions to enable risk management features like:
- Validating that positions have stop losses
- Calculating worst-case loss scenarios
- Enforcing minimum stop loss distance requirements
- Displaying position protection in dashboards

### The Challenge: Position Scaling

When traders scale into positions (e.g., buy 2 contracts, then buy 2 more), multiple questions arise:

**Scenario:**
```
t=0: Buy 2 MNQ @ $26250 (stop @ $26240)
     → Position: 2 contracts

t=1: Buy 2 MORE MNQ @ $26260 (stop @ $26250)
     → Position: 4 contracts @ avg $26255
```

**Questions:**
1. Which stop loss applies? First? Second? Both?
2. Is there ONE stop @ $26240 for all 4 contracts?
3. Or TWO stops: @ $26240 for 2, @ $26250 for 2?
4. What if you close 2 contracts - which stop gets cancelled?
5. What if broker modifies/moves a stop?

This is **position aggregation complexity** - not a trivial caching problem.

---

## 🔍 What the SDK Provides

**Project-X-Py SDK Handles:**
- ✅ Position tracking (size, avg price, unrealized P&L)
- ✅ Order management (working orders, filled orders)
- ✅ Event streaming (ORDER_PLACED, ORDER_FILLED, POSITION_UPDATED)
- ✅ Position lifecycle (opened, updated, closed)
- ✅ Order state management (working, filled, cancelled, modified)

**SDK Does NOT Provide:**
- ❌ "Which stop belongs to which entry?"
- ❌ "Which stop covers which portion of position?"
- ❌ Automatic stop loss aggregation/scaling logic
- ❌ Position entry tracking (original entries vs scale-ins)

**Why?** Different traders use different strategies:
- **Strategy A**: One stop for entire position (aggregate)
- **Strategy B**: Multiple stops for different entries (scaling)
- **Strategy C**: Trailing stop that moves (dynamic)
- **Strategy D**: Mental stop (no actual order)

The SDK can't assume which strategy you use - that's application-level business logic.

---

## 🛠️ Architecture Options

### Option A: Query SDK Directly ⭐ **RECOMMENDED**

**Approach**: Don't cache - query SDK when needed.

```python
def get_stop_loss_for_position(contract_id):
    # Ask SDK for all working orders
    working_orders = suite.order_manager.get_working_orders()

    # Filter for stop orders on this contract
    stop_orders = [
        order for order in working_orders
        if order.contractId == contract_id and order.type in [3, 4, 5]  # Stop types
    ]

    return stop_orders  # Could be 0, 1, or multiple stops
```

**Pros:**
- ✅ SDK is always source of truth (no cache drift)
- ✅ SDK handles position scaling automatically
- ✅ SDK handles order modifications, cancellations
- ✅ Simple - no state management needed
- ✅ Works with polling (5-second refresh captures new stops)
- ✅ Handles broker-initiated changes (stop moved by platform)

**Cons:**
- ❌ Requires SDK access (but we already have it)
- ❌ Slightly slower (API call ~1-5ms vs dict lookup ~0.001ms)
- ❌ Need to query each time (but negligible for risk management)

**Performance:**
- Querying SDK: ~1-5ms (in-memory data structures)
- Dict lookup: ~0.001ms
- **Difference: Irrelevant for risk management** (not HFT)

**When to use:** Default choice for most use cases.

---

### Option B: Cache Per-Contract, Last-Stop-Wins (Current Implementation)

**Approach**: One stop loss per contract_id in cache.

```python
_active_stop_losses = {
    "CON.F.US.MNQ.Z25": {"stop_price": 26240, "quantity": 4, "order_id": 123},
}
```

**Pros:**
- ✅ Simple
- ✅ Fast (dict lookup)
- ✅ Works if trader uses "one stop per position" strategy

**Cons:**
- ❌ Doesn't handle multiple stops per position
- ❌ Last stop placed overwrites previous ones
- ❌ No way to track "2 @ 26240, 2 @ 26250"
- ❌ Cache can drift (if stop modified outside our tracking)
- ❌ Breaks with position scaling

**When to use:** Only if you're 100% certain there's one stop per position.

---

### Option C: Cache Multiple Stops Per Contract (Complex)

**Approach**: Track array of stops per contract.

```python
_active_stop_losses = {
    "CON.F.US.MNQ.Z25": [
        {"order_id": 123, "stop_price": 26240, "quantity": 2, "timestamp": ...},
        {"order_id": 456, "stop_price": 26250, "quantity": 2, "timestamp": ...},
    ]
}
```

**Pros:**
- ✅ Handles position scaling
- ✅ Tracks multiple entry points
- ✅ Can calculate worst-case scenario (all stops hit)
- ✅ Preserves stop loss history

**Cons:**
- ❌ Complex - need to match quantities
- ❌ What if total stop qty ≠ position size?
- ❌ Need to handle stop modifications, partial fills
- ❌ Cache can still drift
- ❌ Still doesn't know "which stop for which entry"
- ❌ Need to handle order modifications (stop price changed)
- ❌ Need to handle partial cancellations

**Implementation complexity:**
- Order placed → Add to array
- Order filled → Remove from array
- Order cancelled → Remove from array
- Order modified → Update in array (find by order_id)
- Position closed → Clear array for that contract
- Position scaled → Multiple stops in array

**When to use:** If you need detailed stop loss tracking and accept the complexity.

---

### Option D: Hybrid - Cache SDK Snapshot (Polling)

**Approach**: Periodically fetch working orders from SDK and cache.

```python
# Every 5 seconds (in polling task):
async def _refresh_stop_loss_cache(self):
    working_orders = self.suite.order_manager.get_working_orders()

    # Clear and rebuild cache
    self._stop_loss_cache.clear()

    for order in working_orders:
        if self._is_stop_loss(order):
            contract_id = order.contractId
            if contract_id not in self._stop_loss_cache:
                self._stop_loss_cache[contract_id] = []
            self._stop_loss_cache[contract_id].append({
                "order_id": order.id,
                "stop_price": order.stopPrice,
                "quantity": order.size,
                "timestamp": time.time(),
            })
```

**Pros:**
- ✅ SDK is source of truth
- ✅ Fast lookups between refreshes
- ✅ Handles scaling/modifications/cancellations automatically
- ✅ Simpler than event-driven caching
- ✅ Automatically syncs with broker state

**Cons:**
- ❌ Data can be up to 5 seconds stale
- ❌ Extra complexity (polling + caching)
- ❌ Need to handle cache expiration

**When to use:** If you need fast lookups but still want SDK as source of truth.

---

## 📊 Decision Matrix

| Feature | Option A (Query SDK) | Option B (Simple Cache) | Option C (Complex Cache) | Option D (Hybrid) |
|---------|---------------------|------------------------|-------------------------|-------------------|
| **Accuracy** | ✅ Always correct | ❌ Can drift | ❌ Can drift | ✅ Mostly correct |
| **Handles Scaling** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| **Complexity** | 🟢 Low | 🟢 Low | 🔴 High | 🟡 Medium |
| **Performance** | 🟡 1-5ms | 🟢 0.001ms | 🟢 0.001ms | 🟢 0.001ms |
| **Cache Drift** | ✅ None | ❌ Possible | ❌ Possible | 🟡 Up to 5s |
| **Broker Changes** | ✅ Handles | ❌ Misses | ❌ Misses | ✅ Syncs |
| **Code Maintenance** | 🟢 Simple | 🟢 Simple | 🔴 Complex | 🟡 Medium |

**Legend:**
- 🟢 Low/Good
- 🟡 Medium/Acceptable
- 🔴 High/Poor

---

## 💡 Recommendation: Option A (Query SDK Directly)

**Why?**

1. **SDK is already tracking everything** - position size, working orders, order lifecycle
2. **No cache drift** - always accurate, always in sync with broker
3. **Handles scaling automatically** - SDK knows position is 4 contracts and which stops are active
4. **Less code to maintain** - remove caching logic, just query
5. **Already have access** - `self.suite.order_manager` exists
6. **Performance is not a concern** - risk management doesn't need microsecond response times

**The "performance cost" is negligible:**
- Risk rules evaluate on events (not 1000s of times per second)
- Position updates happen every few seconds at most
- 1-5ms query time is completely acceptable for risk management

**When to cache:** Only if you're doing high-frequency queries (1000s per second). You're not.

### The Caching Trade-off

> **Cache = Fast but can be wrong** (stale data)
> **Query = Slightly slower but always right** (source of truth)

For risk management, **always right > fast**. Cache only when necessary.

---

## 🧪 Testing Strategy

Before implementing, we need to answer:

### Questions to Test:

1. **How does the broker handle position scaling?**
   - One position with avg price? (Most futures brokers)
   - Multiple positions? (Some stock brokers)

2. **How do stops work with scaling?**
   - Does broker place ONE stop for total position?
   - Or MULTIPLE stops for each entry?
   - Can you have partial stops (stop for 2 out of 4 contracts)?

3. **What does the SDK return?**
   - Query SDK and log: `suite.order_manager.get_working_orders()`
   - Scale into position and query again
   - See the actual data structure

4. **What does risk management need?**
   - Just need to know "position has stop" (yes/no)?
   - Need exact stop price?
   - Need to validate stop distance?
   - Need to track multiple stops?

### Test Script

Create `test_stop_loss_query.py`:

```python
"""
Test script to explore SDK stop loss tracking.

Run this while manually trading to see what the SDK returns.
"""
import asyncio
from project_x_py import TradingSuite

async def test_stop_loss_tracking():
    # Connect to SDK
    suite = await TradingSuite.create(
        instruments=["MNQ"],
        timeframes=["1min"],
    )

    print("Connected. Now manually:")
    print("1. Open a position (buy 2 MNQ)")
    print("2. Place a stop loss")
    print("3. Press Enter to see working orders")
    input()

    # Get working orders
    orders = suite.order_manager.get_working_orders()
    print(f"\nFound {len(orders)} working orders:")

    for order in orders:
        print(f"  Order {order.id}:")
        print(f"    Contract: {order.contractId}")
        print(f"    Type: {order.type} ({order.type_str})")
        print(f"    Side: {order.side}")
        print(f"    Size: {order.size}")
        print(f"    Stop: {order.stopPrice}")
        print(f"    Limit: {order.limitPrice}")
        print(f"    Status: {order.status}")
        print()

    print("Now:")
    print("4. Scale into position (buy 2 MORE MNQ)")
    print("5. Place another stop loss")
    print("6. Press Enter to see working orders again")
    input()

    # Get working orders again
    orders = suite.order_manager.get_working_orders()
    print(f"\nFound {len(orders)} working orders:")

    for order in orders:
        print(f"  Order {order.id}:")
        print(f"    Contract: {order.contractId}")
        print(f"    Type: {order.type} ({order.type_str})")
        print(f"    Size: {order.size}")
        print(f"    Stop: {order.stopPrice}")
        print()

    # Check position
    positions = await suite[0].positions.get_all_positions()
    print(f"\nPositions:")
    for pos in positions:
        print(f"  {pos.contractId}: {pos.size} @ {pos.averagePrice}")

    await suite.disconnect()

if __name__ == "__main__":
    asyncio.run(test_stop_loss_tracking())
```

**Run this test to see:**
- How SDK tracks stops
- What data structure is returned
- How scaling affects working orders
- Whether broker uses one stop or multiple

---

## 🎯 Implementation Plan

### Phase 1: Test & Validate (Current)
- [ ] Run test script to explore SDK behavior
- [ ] Document actual SDK responses
- [ ] Confirm broker behavior with scaling
- [ ] Define business requirements

### Phase 2: Implement Query-Based Approach (Recommended)
- [ ] Remove event-driven caching from `trading.py`
- [ ] Add `get_stop_losses_for_position()` method that queries SDK
- [ ] Update position event handler to query and display stops
- [ ] Add stop loss data to risk events (queried on-demand)
- [ ] Update logging to show all active stops

### Phase 3: Integration
- [ ] Update risk rules to query stop losses
- [ ] Add validation: "position must have stop loss"
- [ ] Add validation: "stop must be X points away"
- [ ] Add dashboard display of active stops

### Phase 4: Optimization (If Needed)
- [ ] Profile performance
- [ ] If query time is a concern (unlikely), consider Option D (hybrid caching)
- [ ] Otherwise, keep it simple with direct queries

---

## 📝 Current Implementation Status

**What's Built:**
- ✅ Event-driven caching (ORDER_PLACED → cache)
- ✅ Cache cleanup (ORDER_FILLED, ORDER_CANCELLED → remove)
- ✅ Polling-based detection (5-second refresh)
- ✅ Query methods (`get_stop_loss_for_position()`)

**Known Issues:**
- ❌ Doesn't handle position scaling (last stop overwrites previous)
- ❌ Cache can drift (broker modifications not tracked)
- ❌ Timing issue (stop placed after position opened)
- ❌ No validation of stop qty vs position size

**Recommendation:**
Replace event-driven caching with SDK queries (Option A).

---

## 🔄 Migration Path

**From Current (Event-Driven Cache) → To Recommended (SDK Query)**

### Step 1: Keep Current Cache as Fallback
```python
def get_stop_loss_for_position(self, contract_id: str) -> list[dict]:
    """Query SDK for active stop losses (primary method)."""
    if not self.suite or not hasattr(self.suite, 'order_manager'):
        # Fallback to cache if SDK not available
        cached = self._active_stop_losses.get(contract_id)
        return [cached] if cached else []

    # Primary: Query SDK
    working_orders = self.suite.order_manager.get_working_orders()

    stops = [
        {
            "order_id": order.id,
            "stop_price": order.stopPrice,
            "side": self._get_side_name(order.side),
            "quantity": order.size,
            "timestamp": time.time(),
        }
        for order in working_orders
        if order.contractId == contract_id and self._is_stop_loss(order)
    ]

    return stops
```

### Step 2: Update Position Event Handler
```python
async def _handle_position_event(self, event, action_name: str):
    # ... existing code ...

    # Query SDK for active stops (not cache)
    stops = self.get_stop_loss_for_position(contract_id)

    if action_name in ["OPENED", "UPDATED"]:
        if not stops:
            logger.warning(f"  └─ ⚠️ NO STOP LOSS for this position!")
        elif len(stops) == 1:
            logger.info(f"  └─ 🛡️ Stop Loss: ${stops[0]['stop_price']:.2f} (Qty: {stops[0]['quantity']})")
        else:
            logger.info(f"  └─ 🛡️ {len(stops)} Stop Losses:")
            for stop in stops:
                logger.info(f"       - ${stop['stop_price']:.2f} (Qty: {stop['quantity']})")
```

### Step 3: Remove Event-Driven Caching (Optional)
Once confident in SDK queries, remove:
- `_active_stop_losses` cache
- Caching logic in `_on_order_placed()`
- Cleanup logic in `_on_order_filled()` and `_on_order_cancelled()`

Or keep as fallback for offline testing.

---

## 🎓 Key Learnings

### Why This Is Hard

1. **Position scaling is complex** - not just "one position = one stop"
2. **Broker behavior varies** - different platforms handle stops differently
3. **State management is hard** - caching requires handling all edge cases
4. **SDK is your friend** - it already solved these problems

### The Right Approach

1. **Start simple** - query SDK directly
2. **Measure before optimizing** - don't cache unless proven necessary
3. **SDK as source of truth** - don't reinvent what it provides
4. **Test with real trading** - edge cases only appear in production

### When to Cache

Cache when:
- ✅ You're doing high-frequency queries (1000s/second)
- ✅ Source of truth is expensive to query (API rate limits)
- ✅ Data doesn't change frequently (static reference data)

Don't cache when:
- ❌ Source of truth is fast to query (in-memory SDK)
- ❌ Data changes frequently (orders, positions)
- ❌ Accuracy is critical (risk management)

---

## 📚 References

- **Project-X-Py SDK**: Order Manager API
- **Risk Management Best Practices**: Always use source of truth for position data
- **Software Architecture**: Prefer simplicity over premature optimization

---

## ✅ Action Items

- [ ] Run `test_stop_loss_query.py` to explore SDK behavior
- [ ] Document findings in this file
- [ ] Decide on final implementation approach
- [ ] Update `trading.py` with recommended approach
- [ ] Update risk rules to use new query method
- [ ] Add tests for position scaling scenarios
- [ ] Update documentation

---

**Last Updated**: 2025-10-29
**Next Review**: After testing SDK behavior with position scaling
