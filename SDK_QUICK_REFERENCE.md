# Project-X-Py SDK - Quick Reference Guide

**Last Updated**: 2025-10-29
**SDK Version**: 3.5.9
**Based On**: Live introspection and testing

This guide documents the **actual working API** discovered through introspection.

---

## 📋 Table of Contents

1. [SDK Structure](#sdk-structure)
2. [Order Management](#order-management)
3. [Position Management](#position-management)
4. [Order Types & Status](#order-types--status)
5. [Common Patterns](#common-patterns)
6. [Gotchas & Pitfalls](#gotchas--pitfalls)

---

## 🏗️ SDK Structure

### TradingSuite Initialization

```python
from project_x_py import TradingSuite

# Create suite with multiple instruments
suite = await TradingSuite.create(
    instruments=["MNQ", "ES", "NQ"],           # Symbols to trade
    timeframes=["1min", "5min"],               # Bar data timeframes
    features=["performance_analytics", "auto_reconnect"],
)
```

### Suite Structure (Dict-Like)

```python
# TradingSuite is dict-like with instrument managers
type(suite)  # <class 'project_x_py.trading_suite.TradingSuite'>

# Access instruments by symbol
mnq = suite["MNQ"]  # <class 'project_x_py.instrument_manager.InstrumentManager'>
es = suite["ES"]
nq = suite["NQ"]

# Each instrument has managers
mnq.orders      # OrderManager
mnq.positions   # PositionManager
mnq.bars        # BarManager
mnq.indicators  # IndicatorManager
```

### ❌ Common Mistakes

```python
# ❌ WRONG - No global order manager
suite.orders  # AttributeError

# ❌ WRONG - Not a list
suite[0]  # KeyError

# ✅ CORRECT - Access by symbol
suite["MNQ"].orders
```

---

## 📦 Order Management

### OrderManager Methods

**Location**: `suite[symbol].orders`

```python
# Get the order manager
orders = suite["MNQ"].orders

# Available methods (discovered via introspection)
[
    'cancel_all_orders',
    'cancel_order',
    'get_all_orders',
    'get_position_orders',      # ← SDK-tracked orders only
    'modify_order',
    'place_order',
    'search_open_orders',       # ← ALL orders (SDK + UI) ✅
]
```

### Query Methods Comparison

| Method | Scope | Use Case | Performance |
|--------|-------|----------|-------------|
| `get_position_orders(contract_id)` | SDK-tracked orders only | Orders placed via SDK | Fast (cache) |
| `search_open_orders()` | **ALL open orders** | **UI + SDK orders** ✅ | Slower (API call) |
| `get_all_orders()` | TBD (unclear scope) | TBD | Unknown |

### search_open_orders() - The Key Method

**Use this to find broker-UI created orders!**

```python
# Get ALL open orders from broker (not just SDK-tracked)
instrument = suite["MNQ"]
all_orders = await instrument.orders.search_open_orders()

# Returns list of Order objects
for order in all_orders:
    print(f"Order: {order.id}, Type: {order.type}, Price: {order.stopPrice}")
```

**Example Output**:
```python
[
    Order(
        id=1818943311,
        contractId="CON.F.US.MNQ.Z25",
        type=4,                  # STOP
        type_str="STOP",
        stopPrice=26176.75,
        side=2,                  # Sell
        size=2,
        status=1,                # Open/Working
        ...
    )
]
```

### get_position_orders() - SDK Orders Only

**Use this for orders placed by your code.**

```python
# Get SDK-tracked orders for a specific position
instrument = suite["MNQ"]
contract_id = "CON.F.US.MNQ.Z25"

orders = await instrument.orders.get_position_orders(contract_id)
# Returns: List of Order objects (only SDK-created)
```

**⚠️ Limitation**: Does NOT return broker-UI created orders!

### Place Order

```python
# Place a market order
await suite["MNQ"].orders.place_order(
    contract_id="CON.F.US.MNQ.Z25",
    side=1,              # 1=Buy, 2=Sell
    size=2,              # Quantity
    order_type=2,        # 2=MARKET
)

# Place a stop order
await suite["MNQ"].orders.place_order(
    contract_id="CON.F.US.MNQ.Z25",
    side=2,              # Sell (to close long)
    size=2,
    order_type=4,        # 4=STOP
    stop_price=26176.75,
)

# Place bracket order (entry + stop + target)
await suite["MNQ"].orders.place_order(
    contract_id="CON.F.US.MNQ.Z25",
    side=1,
    size=2,
    order_type=2,        # MARKET entry
    stop_loss_bracket={
        "ticks": 10,
        "type": 4        # STOP
    },
    take_profit_bracket={
        "ticks": 20,
        "type": 1        # LIMIT
    }
)
```

### Cancel Order

```python
# Cancel specific order
await suite["MNQ"].orders.cancel_order(order_id=1818943311)

# Cancel all orders for instrument
await suite["MNQ"].orders.cancel_all_orders()
```

### Modify Order

```python
# Modify order price
await suite["MNQ"].orders.modify_order(
    order_id=1818943311,
    stop_price=26180.00,  # New stop price
)
```

---

## 📊 Position Management

### PositionManager Methods

**Location**: `suite[symbol].positions`

```python
positions = suite["MNQ"].positions

# Available methods
[
    'close_position',
    'get_all_positions',
    'get_position',
    'partial_close',
]
```

### Get All Positions

```python
# Get all positions for this instrument
positions = await suite["MNQ"].positions.get_all_positions()

for position in positions:
    print(f"Position: {position.contractId}, Size: {position.size}, P&L: {position.unrealizedPnL}")
```

**Position Object Structure**:
```python
Position(
    contractId="CON.F.US.MNQ.Z25",
    size=2,                    # Positive=Long, Negative=Short
    avgPrice=26170.00,         # Average entry price
    unrealizedPnL=47.50,       # Current P&L
    realizedPnL=0.00,
    ...
)
```

### Get Specific Position

```python
# Get position by contract ID
position = await suite["MNQ"].positions.get_position(contract_id="CON.F.US.MNQ.Z25")
```

### Close Position

```python
# Close entire position
await suite["MNQ"].positions.close_position(contract_id="CON.F.US.MNQ.Z25")

# Partial close
await suite["MNQ"].positions.partial_close(
    contract_id="CON.F.US.MNQ.Z25",
    size=1  # Close 1 contract, keep 1 open
)
```

---

## 🔢 Order Types & Status

### Order Types (Enum)

```python
ORDER_TYPES = {
    1: "LIMIT",
    2: "MARKET",
    3: "STOP_LIMIT",
    4: "STOP",           # ← Broker-UI stops typically use this
    5: "TRAILING_STOP",
    6: "JOIN_BID",
    7: "JOIN_ASK"
}
```

**Stop Loss Detection**:
```python
# Check if order is a stop type
if order.type in [3, 4, 5]:  # STOP_LIMIT, STOP, TRAILING_STOP
    print(f"Found stop @ ${order.stopPrice}")
```

### Order Status (Enum)

```python
ORDER_STATUS = {
    0: "None",
    1: "Open",           # ← Working orders
    2: "Filled",
    3: "Cancelled",
    4: "Expired",
    5: "Rejected",
    6: "Pending"
}
```

**Filter for working orders**:
```python
working_orders = [o for o in all_orders if o.status == 1]
```

### Order Side (Enum)

```python
ORDER_SIDE = {
    1: "Buy",
    2: "Sell"
}
```

---

## 🎯 Common Patterns

### Pattern 1: Detect Broker-UI Stop Loss

**Problem**: Need to find stops created in broker UI (no ORDER_PLACED event)

**Solution**: Query broker API with `search_open_orders()`

```python
async def find_stop_for_position(suite, symbol: str, contract_id: str):
    """Find stop loss for a position (works for UI-created stops)."""

    # Query ALL open orders from broker
    all_orders = await suite[symbol].orders.search_open_orders()

    # Filter for this position's stops
    for order in all_orders:
        if order.contractId == contract_id and order.type in [3, 4, 5]:
            return {
                "order_id": order.id,
                "stop_price": order.stopPrice,
                "quantity": order.size,
            }

    return None
```

### Pattern 2: Two-Tier Query (Cache + API)

**Problem**: Want fast cache but need fallback to broker API

**Solution**: Try SDK cache first, then broker API

```python
async def get_orders_with_fallback(suite, symbol: str, contract_id: str):
    """Get orders - try cache first, then query broker."""

    instrument = suite[symbol]

    # Try 1: SDK cache (fast but incomplete)
    orders = await instrument.orders.get_position_orders(contract_id)

    # Try 2: Broker API (slower but complete)
    if len(orders) == 0:
        all_orders = await instrument.orders.search_open_orders()
        orders = [o for o in all_orders if o.contractId == contract_id]

    return orders
```

### Pattern 3: Live API Discovery

**Problem**: Don't know what methods are available

**Solution**: Use introspection

```python
# Step 1: What type is this?
print(f"Type: {type(suite)}")
# Output: <class 'project_x_py.trading_suite.TradingSuite'>

# Step 2: What attributes does it have?
attrs = [a for a in dir(suite) if not a.startswith('_')]
print(f"Attributes: {attrs[:20]}")

# Step 3: Get the orders object
instrument = suite["MNQ"]
orders = instrument.orders
print(f"Orders type: {type(orders)}")

# Step 4: What methods are available?
methods = [m for m in dir(orders) if not m.startswith('_') and callable(getattr(orders, m))]
print(f"Methods: {methods}")
# Output: ['cancel_order', 'get_position_orders', 'search_open_orders', ...]

# Step 5: Try each method!
result1 = await orders.get_position_orders(contract_id)
print(f"get_position_orders: {len(result1)}")

result2 = await orders.search_open_orders()
print(f"search_open_orders: {len(result2)}")  # ← This one works!
```

### Pattern 4: Event-Triggered Query (NOT Polling)

**Problem**: Need fresh data without polling

**Solution**: Query when events fire

```python
# ❌ WRONG - Polling (inefficient)
async def poll_for_stops():
    while True:
        await asyncio.sleep(1)  # Every second
        await check_for_stops()  # Wasteful!

# ✅ CORRECT - Event-triggered
async def on_position_opened(event):
    """Query ONLY when position event fires."""
    contract_id = event.data["contractId"]

    # Query broker (triggered by event, not timer)
    stop = await find_stop_for_position(suite, "MNQ", contract_id)

    if stop:
        print(f"Stop @ ${stop['stop_price']}")
    else:
        print("NO STOP - Violation!")
```

---

## ⚠️ Gotchas & Pitfalls

### 1. Events Don't Fire for UI Actions

**Problem**:
```python
# You register for ORDER_PLACED events
await suite.on(EventType.ORDER_PLACED, on_order_placed)

# Trader creates stop in broker UI
# → ❌ Event DOES NOT fire!
```

**Solution**: Query broker API with `search_open_orders()`

### 2. Suite is Dict-Like, Not Object

**Problem**:
```python
# ❌ WRONG - No global order manager
suite.orders.cancel_all_orders()  # AttributeError

# ❌ WRONG - Not a list
suite[0]  # KeyError
```

**Solution**:
```python
# ✅ CORRECT - Access by symbol
suite["MNQ"].orders.cancel_all_orders()
```

### 3. All SDK Methods are Async

**Problem**:
```python
# ❌ WRONG - Forgot await
orders = suite["MNQ"].orders.get_position_orders(contract_id)
# TypeError: object of type 'coroutine' has no len()
```

**Solution**:
```python
# ✅ CORRECT - Always await
orders = await suite["MNQ"].orders.get_position_orders(contract_id)
```

### 4. Order Type is Integer, Not String

**Problem**:
```python
# ❌ WRONG - Comparing to string
if order.type == "STOP":  # Never matches
```

**Solution**:
```python
# ✅ CORRECT - Compare to integer
if order.type == 4:  # STOP
    # Or check multiple types
    if order.type in [3, 4, 5]:  # Any stop type
```

### 5. Contract ID vs Symbol

**Problem**:
```python
# Contract ID: "CON.F.US.MNQ.Z25"  (specific contract)
# Symbol: "MNQ"                     (instrument)

# ❌ WRONG - Using contract_id for suite access
suite[contract_id].orders  # KeyError
```

**Solution**:
```python
# ✅ CORRECT - Extract symbol from contract
def extract_symbol(contract_id: str) -> str:
    # "CON.F.US.MNQ.Z25" → "MNQ"
    parts = contract_id.split(".")
    return parts[3] if len(parts) > 3 else contract_id

symbol = extract_symbol("CON.F.US.MNQ.Z25")  # "MNQ"
suite[symbol].orders  # ✅ Works
```

### 6. No Parent Order Linking

**Problem**: Bracket orders don't expose parent/child relationships

```python
# You place bracket order
await suite["MNQ"].orders.place_order(
    side=1, size=2, order_type=2,
    stop_loss_bracket={"ticks": 10, "type": 4},
    take_profit_bracket={"ticks": 20, "type": 1}
)

# Later query orders
all_orders = await suite["MNQ"].orders.search_open_orders()

# ❌ Orders DON'T have parentOrderId or relationship fields
# You can't tell which stop belongs to which entry!
```

**Solution**: Track relationships yourself

```python
# When you place order, store the relationship
order_id = await place_order(...)
self._bracket_relationships[order_id] = {
    "entry_id": order_id,
    "stop_id": None,     # Fill when stop order fires
    "target_id": None,   # Fill when target order fires
}
```

---

## 📚 Method Signatures Reference

### Orders

```python
# search_open_orders (no parameters)
await suite[symbol].orders.search_open_orders()
# Returns: List[Order]

# get_position_orders (requires contract_id)
await suite[symbol].orders.get_position_orders(contract_id: str)
# Returns: List[Order]

# place_order
await suite[symbol].orders.place_order(
    contract_id: str,
    side: int,                    # 1=Buy, 2=Sell
    size: int,
    order_type: int,              # 1-7 (see ORDER_TYPES)
    limit_price: float = None,    # For LIMIT orders
    stop_price: float = None,     # For STOP orders
    stop_loss_bracket: dict = None,
    take_profit_bracket: dict = None,
)
# Returns: Order ID (int)

# cancel_order
await suite[symbol].orders.cancel_order(order_id: int)
# Returns: None

# modify_order
await suite[symbol].orders.modify_order(
    order_id: int,
    stop_price: float = None,
    limit_price: float = None,
)
# Returns: None
```

### Positions

```python
# get_all_positions (no parameters)
await suite[symbol].positions.get_all_positions()
# Returns: List[Position]

# get_position (requires contract_id)
await suite[symbol].positions.get_position(contract_id: str)
# Returns: Position | None

# close_position
await suite[symbol].positions.close_position(contract_id: str)
# Returns: None

# partial_close
await suite[symbol].positions.partial_close(contract_id: str, size: int)
# Returns: None
```

---

## 🎓 Key Takeaways

1. **TradingSuite is dict-like**: Access instruments via `suite[symbol]`, not `suite.orders`

2. **search_open_orders() is the key**: Use this to find broker-UI created orders

3. **All methods are async**: Always `await` SDK calls

4. **Events don't fire for UI actions**: Query broker API when needed

5. **Order type is integer**: `order.type == 4` not `order.type == "STOP"`

6. **Contract ID ≠ Symbol**: Extract symbol from contract ID for suite access

7. **Use introspection for discovery**: Print types, attributes, methods when stuck

8. **Event-triggered queries ≠ Polling**: Query when events fire, not on timers

---

## 🔗 Related Documentation

- `STOP_LOSS_DETECTION_FIX.md` - How we discovered these methods
- `docs/current/SDK_INTEGRATION_GUIDE.md` - High-level SDK integration
- `cache_system.md` - Discovery document (1,532 lines of exploration)
- `docs/archive/.../projectx_gateway_api/` - Raw API documentation

---

**Last Updated**: 2025-10-29
**Status**: ✅ Verified via live testing
**Source**: Introspection + experimentation
