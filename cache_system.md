# Risk Manager Data Model & Filtering Strategy

**Date**: 2025-10-29
**Status**: Discovery Phase - Understanding Broker Data Model
**Goal**: Map broker payloads → Design risk manager data model → Implement filtering/caching

---

## 🎯 The Real Problem

**We jumped to implementation before understanding the data model.**

We need to:
1. **Map what we receive** - Document all broker payloads (orders, positions, trades)
2. **Understand the dimensions** - Order types, position states, contract details, protective orders
3. **Design a data model** - How should risk rules access this data?
4. **Choose filtering strategy** - Cache? Query SDK? Hybrid?
5. **Handle complexity** - Position scaling, multiple stops, modifications

### The Challenge: Multiple Data Dimensions

There are several overlapping dimensions of data:

**Dimension 1: Order Types** (type field)
```
0 = MARKET
1 = LIMIT
2 = ??? (unknown)
3 = STOP_LIMIT
4 = STOP
5 = TRAILING_STOP
... others?
```

**Dimension 2: Position Lifecycle** (event types)
```
POSITION_OPENED   - New position created
POSITION_UPDATED  - Size/price changed
POSITION_CLOSED   - Position flattened
```

**Dimension 3: Order Lifecycle** (event types)
```
ORDER_PLACED      - Order submitted (status = working?)
ORDER_FILLED      - Order executed (status = 2)
ORDER_PARTIAL_FILL - Partially filled
ORDER_CANCELLED   - Order cancelled
ORDER_MODIFIED    - Order changed (price, qty, etc.)
ORDER_REJECTED    - Order rejected by broker
ORDER_EXPIRED     - Order expired
```

**Dimension 4: Contract Details** (position/order data)
```
contractId: "CON.F.US.MNQ.Z25" → Symbol: MNQ
size: Number of contracts
averagePrice: Entry price (for positions)
side: 0=BUY, 1=SELL
```

**Dimension 5: Protective Orders**
```
Stop Loss: type=3,4,5 (STOP types)
Take Profit: type=1? (LIMIT to close at profit)
Bracket Orders: Entry + Stop + Target together
```

### The Relationships We Need to Understand

```
Position (id=123, symbol=MNQ, size=4, entry=$26250)
  │
  ├─ Entry Orders (how did we get here?)
  │   ├─ Order A: +2 @ $26245 (filled)
  │   └─ Order B: +2 @ $26255 (filled)
  │
  ├─ Protective Orders (how are we protected?)
  │   ├─ Stop Loss A: -2 @ $26240 (working, for Order A?)
  │   ├─ Stop Loss B: -2 @ $26250 (working, for Order B?)
  │   └─ Take Profit: -4 @ $26280 (working, for entire position?)
  │
  └─ Exit Orders (how did we exit? - if closed)
      └─ Order C: -4 @ $26260 (filled, manual close?)
```

**Questions We Can't Answer Yet:**
1. Do stop losses link to specific entry orders?
2. Is there ONE stop for entire position or MULTIPLE stops for each scale-in?
3. How does broker handle stop loss when you scale in?
4. What fields connect orders to positions? (position_id? contract_id only?)
5. Can we have partial stops (stop for 2 out of 4 contracts)?

This is **data model complexity** - we need to understand the broker's model before designing ours.

---

## 📋 Phase 1: Document Broker Payloads

**Goal**: Capture every payload we receive and understand the data model.

### Order Event Payloads

#### ORDER_PLACED
```python
# From logs: 📦 ORDER_PLACED Payload: {...}
{
    'order': Order(
        id=1815779004,
        contractId='CON.F.US.MNQ.Z25',
        type=4,              # STOP
        type_str='STOP',
        side=1,              # SELL
        size=1,
        stopPrice=26242.25,
        limitPrice=None,
        status=0,            # Working? Pending?
        fillVolume=0,
        filledPrice=0.0
    )
}
```

**Questions:**
- What is `status=0`? (Working/Pending/Accepted?)
- Are there other fields we're not seeing? (parent_order_id? position_id? bracket_id?)
- What's the full Order object schema?

#### ORDER_FILLED
```python
# From logs: 🛑 ORDER FILLED - Stop Loss
{
    'order': Order(
        id=1815779004,
        contractId='CON.F.US.MNQ.Z25',
        type=4,              # STOP
        side=1,              # SELL
        size=1,
        stopPrice=26242.25,
        fillVolume=1,
        filledPrice=26242.25,
        status=2             # Filled
    )
}
```

**Questions:**
- Does `status=2` always mean filled?
- Is there a timestamp?
- Is there an execution_id or trade_id?

#### ORDER_MODIFIED
```python
# Need to capture this payload
# What happens when stop loss is moved?
{
    'order': Order(
        id=???,
        # ... what changes? old_stopPrice? new_stopPrice?
    )
}
```

**Questions:**
- What fields show the change? (old_price vs new_price?)
- Does modification create a new order_id or update existing?

### Position Event Payloads

#### POSITION_OPENED
```python
# Need to capture this payload
{
    'id': ???,
    'accountId': ???,
    'contractId': 'CON.F.US.MNQ.Z25',
    'type': 1,           # LONG
    'size': 1,
    'averagePrice': 26246.0,
    'creationTimestamp': '...',
    'unrealizedPnl': 0.0
}
```

**Questions:**
- Is there a position_id field?
- Does it link to entry order_id?
- Does it include protective orders (stopLoss/takeProfit fields)?

#### POSITION_UPDATED
```python
# From logs:
{
    'id': 418808227,
    'accountId': 13298777,
    'contractId': 'CON.F.US.MNQ.Z25',
    'creationTimestamp': '2025-10-29T15:50:13.776995+00:00',
    'type': 1,           # LONG
    'size': 1,           # Current size
    'averagePrice': 26246.0
}
```

**Questions:**
- When does UPDATED fire? (scale-in? stop loss added? price change?)
- Does it show position history? (original size vs current size?)
- Are protective orders included in this payload?

#### POSITION_CLOSED
```python
# From logs:
{
    'id': 418782239,
    'accountId': 13298777,
    'contractId': 'CON.F.US.MNQ.Z25',
    'creationTimestamp': '2025-10-29T15:40:39.689152+00:00',
    'type': 0,           # FLAT?
    'size': 0,
    'averagePrice': 26244.25
}
```

**Questions:**
- Is there a realized_pnl field?
- How do we know WHY it closed? (stop loss? manual? take profit?)
- Is there a closing_order_id field?

### Trade Event Payloads

```python
# We're not currently capturing TRADE events separately
# Do we need them? Or are ORDER_FILLED events sufficient?
```

**Questions:**
- Is there a TRADE_EXECUTED event separate from ORDER_FILLED?
- What's the difference?
- Do we need both?

---

## 📊 Phase 2: Map Data Relationships

### What We Know (From Logs)

**Order → Position Correlation:**
```
10:40:39 | POSITION_OPENED - MNQ | size=1 | entry=$26244.25
         | (No order_id reference?)

10:40:46 | ORDER_FILLED - Stop Loss | order_id=1815779004
10:40:46 | POSITION_CLOSED - MNQ | size=0
         | (How do we know these are related? Contract ID only?)
```

**Current Linking Strategy:**
- Orders and positions linked by `contractId` only
- No explicit `position_id` ↔ `order_id` relationship
- Use timing window (2-second correlation) to link fills with closures

**What We Need to Map:**

1. **Order → Position** (Entry)
   - When ORDER_FILLED (entry order) → POSITION_OPENED/UPDATED
   - How to link: contract_id + timestamp? Or is there a position_id field?

2. **Position → Order** (Protection)
   - When POSITION_OPENED → Stop loss ORDER_PLACED
   - How to link: Which stop belongs to which position?

3. **Order → Position** (Exit)
   - When ORDER_FILLED (stop/exit) → POSITION_CLOSED
   - How to link: Was it a stop loss, take profit, or manual close?

4. **Position Scaling**
   - When POSITION_UPDATED (size increased) → Which orders added to position?
   - Do we get multiple POSITION_OPENED or one POSITION_UPDATED?

---

## 🔬 Phase 3: Discovery Test Plan

### Test Script 1: Capture All Payloads

```python
"""
test_payload_capture.py

Logs EVERYTHING we receive from the broker.
Run this while manually trading to capture all payload structures.
"""
import asyncio
from project_x_py import TradingSuite, EventType as SDKEventType
from loguru import logger
import json

async def capture_all_events():
    suite = await TradingSuite.create(
        instruments=["MNQ"],
        timeframes=["1min"],
    )

    # Capture ALL events with full payloads
    async def log_event(event, event_name):
        payload = event.data if hasattr(event, 'data') else {}
        logger.info(f"\n{'='*80}")
        logger.info(f"EVENT: {event_name}")
        logger.info(f"Payload Type: {type(payload)}")

        if isinstance(payload, dict):
            logger.info(f"Keys: {list(payload.keys())}")
            logger.info(f"Full Payload:\n{json.dumps(payload, indent=2, default=str)}")
        else:
            logger.info(f"Payload: {payload}")

        # If there's an 'order' object, introspect it
        if isinstance(payload, dict) and 'order' in payload:
            order = payload['order']
            logger.info(f"\nOrder Object Attributes:")
            logger.info(f"  All attributes: {dir(order)}")
            for attr in dir(order):
                if not attr.startswith('_'):
                    try:
                        val = getattr(order, attr)
                        if not callable(val):
                            logger.info(f"    {attr}: {val}")
                    except:
                        pass

        logger.info(f"{'='*80}\n")

    # Register for ALL order events
    await suite.on(SDKEventType.ORDER_PLACED, lambda e: log_event(e, "ORDER_PLACED"))
    await suite.on(SDKEventType.ORDER_FILLED, lambda e: log_event(e, "ORDER_FILLED"))
    await suite.on(SDKEventType.ORDER_PARTIAL_FILL, lambda e: log_event(e, "ORDER_PARTIAL_FILL"))
    await suite.on(SDKEventType.ORDER_CANCELLED, lambda e: log_event(e, "ORDER_CANCELLED"))
    await suite.on(SDKEventType.ORDER_MODIFIED, lambda e: log_event(e, "ORDER_MODIFIED"))
    await suite.on(SDKEventType.ORDER_REJECTED, lambda e: log_event(e, "ORDER_REJECTED"))
    await suite.on(SDKEventType.ORDER_EXPIRED, lambda e: log_event(e, "ORDER_EXPIRED"))

    # Register for ALL position events
    await suite.on(SDKEventType.POSITION_OPENED, lambda e: log_event(e, "POSITION_OPENED"))
    await suite.on(SDKEventType.POSITION_CLOSED, lambda e: log_event(e, "POSITION_CLOSED"))
    await suite.on(SDKEventType.POSITION_UPDATED, lambda e: log_event(e, "POSITION_UPDATED"))

    logger.info("Event capture started. Perform manual trades now...")
    logger.info("Press Ctrl+C when done")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Capture stopped")

    await suite.disconnect()

if __name__ == "__main__":
    asyncio.run(capture_all_events())
```

**Run this and:**
1. Open a position (buy 2 contracts)
2. Place a stop loss
3. Scale in (buy 2 more contracts)
4. Place another stop loss
5. Modify one stop loss (move it)
6. Cancel one stop loss
7. Let one stop loss hit
8. Manually close remaining position

**Capture:**
- Full payload structure for each event
- All fields in Order objects
- All fields in Position data
- Timestamps
- IDs (order_id, position_id, account_id, etc.)

### Test Script 2: Query SDK State

```python
"""
test_sdk_queries.py

Query SDK directly to see what it returns.
"""
import asyncio
from project_x_py import TradingSuite

async def query_sdk_state():
    suite = await TradingSuite.create(
        instruments=["MNQ"],
        timeframes=["1min"],
    )

    print("=" * 80)
    print("WORKING ORDERS")
    print("=" * 80)
    orders = suite.order_manager.get_working_orders()
    print(f"Found {len(orders)} working orders\n")

    for order in orders:
        print(f"Order ID: {order.id}")
        print(f"  Contract: {order.contractId}")
        print(f"  Type: {order.type} ({order.type_str})")
        print(f"  Side: {order.side}")
        print(f"  Size: {order.size}")
        print(f"  Stop: {order.stopPrice}")
        print(f"  Limit: {order.limitPrice}")
        print(f"  Status: {order.status}")
        print(f"  All attributes: {[a for a in dir(order) if not a.startswith('_')]}")
        print()

    print("=" * 80)
    print("POSITIONS")
    print("=" * 80)
    positions = await suite[0].positions.get_all_positions()
    print(f"Found {len(positions)} positions\n")

    for pos in positions:
        print(f"Position ID: {pos.id}")
        print(f"  Contract: {pos.contractId}")
        print(f"  Size: {pos.size}")
        print(f"  Type: {pos.type}")
        print(f"  Entry: {pos.averagePrice}")
        print(f"  Unrealized P&L: {pos.unrealizedPnl}")
        print(f"  All attributes: {[a for a in dir(pos) if not a.startswith('_')]}")
        print()

    await suite.disconnect()

if __name__ == "__main__":
    asyncio.run(query_sdk_state())
```

**Run this with an open position and stops active.**
**Look for:**
- Does Position object have `stopLoss` or `protectiveOrders` fields?
- Does Order object have `position_id` or `parent_order_id` fields?
- Can we link orders to positions directly?

---

## 📐 Phase 4: Design Data Model

**After we understand the payloads, design the internal model for risk rules.**

### Option 1: Rich Position Object

```python
class RiskPosition:
    """
    Aggregate view of a position with all related orders.
    """
    id: str
    contract_id: str
    symbol: str
    size: int
    side: str  # "long" | "short" | "flat"
    entry_price: float
    unrealized_pnl: float

    # Linked orders
    entry_orders: list[Order]      # Orders that created this position
    stop_losses: list[Order]       # Active stop loss orders
    take_profits: list[Order]      # Active take profit orders
    exit_orders: list[Order]       # Orders that closed this position (if closed)

    # Metadata
    created_at: datetime
    closed_at: datetime | None
    close_reason: str | None  # "stop_loss" | "take_profit" | "manual"
```

**Pros:**
- Risk rules get everything in one object
- Clear relationships between position and orders
- Easy to query "does this position have a stop?"

**Cons:**
- Need to maintain these relationships ourselves
- SDK doesn't provide this structure
- Complexity in keeping it synced

### Option 2: Query-Based Access

```python
class RiskDataAccess:
    """
    Query interface for risk rules.
    """
    def get_position(self, contract_id: str) -> Position | None:
        """Get current position from SDK."""
        pass

    def get_stop_losses_for_position(self, contract_id: str) -> list[Order]:
        """Get all working stop loss orders for a contract."""
        pass

    def get_take_profits_for_position(self, contract_id: str) -> list[Order]:
        """Get all working take profit orders for a contract."""
        pass

    def get_position_protection_status(self, contract_id: str) -> dict:
        """Get summary: has_stop, has_tp, stop_distance, etc."""
        pass
```

**Pros:**
- Simple - just queries SDK
- No state management
- Always accurate

**Cons:**
- Risk rules need to make multiple queries
- Less convenient API

### Option 3: Event-Enriched Model

```python
# When we receive POSITION_UPDATED event:
# 1. Query SDK for working orders
# 2. Enrich position data with stops/TPs
# 3. Pass enriched data to risk rules

enriched_position = {
    "symbol": "MNQ",
    "size": 4,
    "entry": 26250,
    "unrealized_pnl": 50.0,

    # Added by us:
    "active_stops": [
        {"order_id": 123, "price": 26240, "quantity": 2},
        {"order_id": 456, "price": 26250, "quantity": 2}
    ],
    "active_tps": [
        {"order_id": 789, "price": 26280, "quantity": 4}
    ],
    "protection_status": {
        "has_stop": True,
        "num_stops": 2,
        "tightest_stop": 26250,
        "total_stop_coverage": 4
    }
}
```

**Pros:**
- Risk rules get everything they need in event
- No additional queries needed
- Convenience + accuracy

**Cons:**
- Need to query SDK on every position event
- Slight overhead (1-5ms per event)

---

## ⚠️ Phase 5: Edge Cases to Test

**These scenarios will reveal how the broker/SDK handles complexity.**

### Edge Case 1: Position Scaling (Adding to Position)

**Scenario:**
```
1. Buy 2 MNQ @ $26250 (stop @ $26240)
   → Position: 2 contracts, avg $26250
   → 1 stop order working

2. Buy 2 MORE MNQ @ $26260 (stop @ $26250)
   → Position: 4 contracts, avg $26255
   → ??? stops working
```

**Questions to Answer:**
- Do we get POSITION_UPDATED or new POSITION_OPENED?
- Does first stop loss get cancelled automatically?
- Do we now have 2 stop orders working?
- Does broker aggregate to 1 stop @ $26250 for all 4 contracts?
- What happens if we manually close 2 contracts - which stop remains?

**Test:**
1. Open position with stop
2. Scale in with another stop
3. Query SDK: `get_working_orders()` - how many stops?
4. Check position: size, avg price
5. Partially close: close 2 contracts
6. Query SDK again: which stops remain?

### Edge Case 2: Stop Loss Modification (Moving Stop)

**Scenario:**
```
1. Position: 4 MNQ @ $26250 (stop @ $26240)
2. Manually move stop to $26245
   → Does ORDER_MODIFIED fire?
   → Same order_id or new order?
```

**Questions to Answer:**
- Does modification keep same order_id?
- Do we get ORDER_CANCELLED + ORDER_PLACED or just ORDER_MODIFIED?
- What fields change in the payload?
- Does position event fire when stop is moved?

**Test:**
1. Open position with stop
2. Modify stop price via broker UI
3. Capture events: look for ORDER_MODIFIED
4. Check: order_id same or different?

### Edge Case 3: Bracket Orders (OCO - One Cancels Other)

**Scenario:**
```
Entry: Buy 2 MNQ @ $26250
Stop:  Sell 2 MNQ @ $26240 (if price drops)
Target: Sell 2 MNQ @ $26280 (if price rises)

→ When target fills, does stop auto-cancel?
→ When stop fills, does target auto-cancel?
```

**Questions to Answer:**
- Does broker support bracket orders natively?
- Do we see OCO relationship in order fields?
- Are they linked via `parent_order_id` or `bracket_id`?
- When one fills, do we get ORDER_CANCELLED for the other?

**Test:**
1. Place bracket order (if supported)
2. Let one side fill
3. Check if other side cancels automatically
4. Look for linking fields in payloads

### Edge Case 4: Partial Fills

**Scenario:**
```
Order: Buy 4 MNQ @ market
Fill:  +2 filled immediately
Fill:  +2 filled 5 seconds later

→ Do we get 2 ORDER_PARTIAL_FILL events + 1 ORDER_FILLED?
→ Or 1 ORDER_FILLED with final quantity?
```

**Questions to Answer:**
- How are partial fills reported?
- Do we get POSITION_OPENED for first fill?
- Do we get POSITION_UPDATED for second fill?
- How does position avg price update?

**Test:**
1. Place limit order unlikely to fill immediately
2. Let it fill partially over time
3. Capture all events
4. Map order fills to position updates

### Edge Case 5: Stop Loss Hit vs Manual Close

**Scenario A: Stop Loss Hit**
```
Position: Long 2 MNQ @ $26250 (stop @ $26240)
Market drops to $26240
→ ORDER_FILLED (stop loss)
→ POSITION_CLOSED
```

**Scenario B: Manual Close**
```
Position: Long 2 MNQ @ $26250 (stop @ $26240)
Trader clicks "close position"
→ ORDER_FILLED (market order)
→ POSITION_CLOSED
→ What happens to the stop loss order?
```

**Questions to Answer:**
- Can we distinguish stop hit from manual close?
- Does manual close auto-cancel the stop loss?
- Do we get ORDER_CANCELLED event for the stop?
- How do we know WHY position closed?

**Test:**
1. Open position with stop
2. Manually close position
3. Check if stop gets cancelled
4. Compare event sequence to stop loss hit

### Edge Case 6: Multiple Positions Same Symbol

**Scenario:**
```
Position A: Long 2 MNQ @ $26250 (stop @ $26240)
Position B: Long 2 MNQ @ $26260 (stop @ $26250)

→ Does broker show 2 separate positions?
→ Or 1 aggregated position (4 contracts @ avg $26255)?
```

**Questions to Answer:**
- Does broker allow multiple positions per symbol?
- Or does it aggregate to single position?
- If aggregated, how do we track entry points?
- How do we know which stop belongs to which entry?

**Test:**
1. Open position
2. Close position fully
3. Open new position same symbol
4. Check position_id: same or different?

### Edge Case 7: Stop Loss Below/Above Current Price

**Scenario:**
```
Long 2 MNQ @ $26250
Market currently at $26240 (below entry)

Try to place stop @ $26245 (above current price)
→ Does broker reject it?
→ Does it accept and immediately fill?
→ Does it place as "stop market" or convert to "market"?
```

**Questions to Answer:**
- Can you place stop above market (for long)?
- What happens if you try?
- Does SDK prevent it or does broker reject it?

**Test:**
1. Open long position
2. Try placing stop above current market
3. See if rejected or how it behaves

### Edge Case 8: Position Flat But Stop Still Working

**Scenario:**
```
1. Long 2 MNQ (stop @ $26240)
2. Manually close position (sell 2 MNQ)
3. Position now flat

→ Is stop loss auto-cancelled?
→ Or does it remain working (dangerous!)?
```

**Questions to Answer:**
- Does closing position auto-cancel protective orders?
- Can you have working stop with no position?
- Could stop accidentally trigger on reverse position?

**Test:**
1. Open position with stop
2. Close position
3. Query SDK: is stop still working?
4. If yes, this is a risk (need to cancel manually)

### Edge Case 9: Connection Loss During Trade

**Scenario:**
```
1. Position opened
2. Internet disconnects
3. Stop loss hits while offline
4. Reconnect

→ Do we get missed events?
→ Does SDK replay history?
→ How do we know what happened?
```

**Questions to Answer:**
- Does SDK buffer missed events?
- Do we get position snapshot on reconnect?
- How to handle state sync after disconnect?

**Test:**
1. Open position
2. Disconnect (kill WiFi)
3. Let stop hit (verify via broker web UI)
4. Reconnect
5. Check what events we receive

### Edge Case 10: Rapid Scaling (Multiple Entries Fast)

**Scenario:**
```
t=0:  Buy 1 MNQ (stop @ $26240)
t=1s: Buy 1 MNQ (stop @ $26245)
t=2s: Buy 1 MNQ (stop @ $26250)
t=3s: Buy 1 MNQ (stop @ $26255)

→ 4 entries in 3 seconds
→ How many position events?
→ How many stop orders working?
→ Do events arrive in order?
```

**Questions to Answer:**
- Can events arrive out of order?
- Do we miss events if too fast?
- How does position avg price update?
- Which stop orders are working?

**Test:**
1. Write script to place orders rapidly
2. Capture all events with timestamps
3. Check if any missed
4. Verify order of events

---

## 📝 Phase 6: Document Findings

**After running all tests, fill in this section:**

### Order Type Mappings
```
type=0: MARKET (confirmed)
type=1: LIMIT (confirmed)
type=2: ??? (test to find out)
type=3: STOP_LIMIT (confirmed)
type=4: STOP (confirmed)
type=5: TRAILING_STOP (confirmed)
type=6: ???
```

### Order Status Mappings
```
status=0: ??? (Working? Pending? Placed?)
status=1: ???
status=2: FILLED (confirmed)
status=3: ???
status=4: CANCELLED?
```

### Position Type Mappings
```
type=0: FLAT (confirmed)
type=1: LONG (confirmed)
type=2: SHORT (assumed, needs confirmation)
```

### Event Correlation Rules
```
Entry Order → Position:
  - [Document how they link]

Position → Stop Loss:
  - [Document how they link]

Stop Fill → Position Close:
  - [Document correlation logic]
```

### Broker Behavior
```
Position Scaling:
  - [Does broker aggregate or create multiple positions?]
  - [How are stop losses handled?]

Bracket Orders:
  - [Are they supported?]
  - [How are they linked?]

Protective Order Auto-Cancel:
  - [Does closing position cancel stops?]
  - [Test result: YES/NO]
```

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

## 🎯 Current Status & Next Steps

**Where We Are:**
- ✅ Identified the problem (need stop loss tracking)
- ✅ Recognized complexity (position scaling, edge cases)
- ✅ Documented multiple architecture options
- ❌ **Haven't tested broker behavior yet** ← YOU ARE HERE
- ❌ Haven't designed data model yet
- ❌ Haven't chosen implementation strategy yet

**What We Need To Do (In Order):**

### Step 1: Run Discovery Tests ⭐ DO THIS FIRST

1. **Run `test_payload_capture.py`** (Phase 3)
   - Capture ALL event payloads
   - Document complete Order and Position object schemas
   - See ALL available fields

2. **Run `test_sdk_queries.py`** (Phase 3)
   - Query SDK state directly
   - See what `get_working_orders()` returns
   - Check for linking fields (position_id, parent_order_id, etc.)

3. **Test Edge Cases** (Phase 5)
   - Position scaling (the big one!)
   - Stop loss modification
   - Bracket orders
   - Manual close vs stop hit
   - All 10 edge cases listed above

4. **Document Findings** (Phase 6)
   - Fill in type/status mappings
   - Document correlation logic
   - Understand broker behavior

### Step 2: Design Data Model (After Testing)

Based on test results, choose ONE of these approaches:

**Option A: Query SDK (if broker provides clean linking)**
- Use this if: Position objects have stopLoss/takeProfit fields
- Or if: Order objects have position_id fields
- Or if: SDK provides easy "get stops for position" API

**Option B: Event-Enriched (if we need to augment events)**
- Use this if: Broker doesn't link orders to positions
- Query SDK on each position event to enrich data
- Pass enriched data to risk rules

**Option C: Rich Cache (if SDK queries are too slow/complex)**
- Only use if: Option A/B don't work
- Or if: We need historical tracking SDK doesn't provide
- Requires maintaining complex state

### Step 3: Implement (After Design Decided)

Don't write ANY more code until we've completed Steps 1 and 2.

**Why?**
- We're guessing at solutions without understanding the problem
- Edge cases will reveal the right architecture
- Testing will show what the broker actually does
- SDK might already provide what we need (or might not)

---

## 🚫 What NOT To Do

**Don't:**
- ❌ Write more caching code yet
- ❌ Assume how position scaling works
- ❌ Assume how stops link to positions
- ❌ Build complex state management without testing first
- ❌ Commit to an architecture before understanding the data

**Do:**
- ✅ Run the test scripts
- ✅ Capture real broker behavior
- ✅ Document actual payloads
- ✅ Test all edge cases
- ✅ THEN design the system

---

## 📋 Immediate Action Plan

**Today:**
1. Create `test_payload_capture.py` (copy from Phase 3)
2. Run it while manually trading
3. Save all output to `broker_payloads.log`
4. Review captured data

**Tomorrow:**
1. Create `test_sdk_queries.py` (copy from Phase 3)
2. Run with open positions
3. Document what SDK returns
4. Look for linking fields

**This Week:**
1. Test all 10 edge cases
2. Document findings in Phase 6 section
3. Update this document with actual behavior
4. Design data model based on reality

**Next Week:**
1. Choose architecture (A, B, or C)
2. Implement chosen approach
3. Write tests for implementation
4. Deploy and monitor

---

## 🧪 Before Implementing, Answer These:

**Critical Questions:**
1. Does broker aggregate positions or keep them separate?
2. Do stop losses link to positions explicitly (position_id)?
3. When you scale in, how many stop orders are working?
4. Does manual close auto-cancel protective orders?
5. Can you have multiple stops for one position?
6. What fields exist in Order objects that we're not seeing?
7. What fields exist in Position objects beyond what we've logged?

**Don't guess. Test and document.**

---

## 📚 What This Document Should Become

**After testing, this document should have:**
- ✅ Complete payload schemas (Phase 1)
- ✅ Documented relationships (Phase 2)
- ✅ Edge case test results (Phase 5)
- ✅ Filled-in findings section (Phase 6)
- ✅ Chosen architecture with rationale
- ✅ Implementation plan based on reality

**Right now it's:**
- ❌ Speculation about architectures
- ❌ Guessing about broker behavior
- ❌ Solutions looking for problems

**Make it:**
- ✅ Documentation of actual broker behavior
- ✅ Tested understanding of data model
- ✅ Informed architecture decision

---

## 🎓 Key Lesson

**We jumped to implementation before understanding the problem.**

This is common in software development. The fix is:
1. Stop coding
2. Start testing
3. Document reality
4. Design based on facts
5. THEN implement

**"Weeks of coding can save hours of planning."** - Anonymous

Don't be that developer. Do the discovery work first.

---

## ✅ Success Criteria

**You'll know discovery is complete when you can answer:**

1. "Show me the exact payload for POSITION_OPENED" → ✅ Can provide it
2. "How many stops are working after scaling in?" → ✅ Know the answer
3. "What happens to stops when position closes?" → ✅ Tested it
4. "Can we have partial stop coverage?" → ✅ Tested it
5. "How do we know WHY a position closed?" → ✅ Know the pattern
6. "What fields link orders to positions?" → ✅ Documented them
7. "Does broker support bracket orders?" → ✅ Tested it
8. "What's the Order object schema?" → ✅ Have complete list
9. "What's the Position object schema?" → ✅ Have complete list
10. "Which architecture should we use?" → ✅ Can justify the choice

**When you can answer all 10, you're ready to implement.**

---

## 📝 Document Maintenance

**Update this document after each discovery phase:**
- After payload capture → Fill in Phase 1
- After SDK queries → Fill in Phase 2
- After edge case testing → Fill in Phase 5
- After documenting findings → Fill in Phase 6
- After choosing architecture → Add "Decision" section
- After implementing → Add "Implementation" section

**This is a living document. Keep it current.**

---

## 🧪 Testing Strategy (From Original)

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
