# Data Schema Quick Reference

**Quick lookup for field names, types, and enum values**
**Last Updated:** 2025-10-27

---

## Field Name Quick Reference

### Position Fields

| Use This ✅ | NOT These ❌ | Type | Source |
|------------|-------------|------|--------|
| `average_price` | ~~entry_price~~, ~~avgPrice~~ | `float` | SignalR: `averagePrice` |
| `size` | ~~quantity~~, ~~contracts~~ | `int` (signed) | Positive=long, negative=short |
| `unrealized_pnl` | ~~unrealizedPnl~~, ~~pnl~~ | `float` | SignalR: `unrealizedPnl` |
| `realized_pnl` | ~~realizedPnl~~, ~~pnl~~ | `float` | SignalR: `realizedPnl` |
| `contract_id` | ~~position_id~~ | `str` | SignalR: `contractId` |

**Position Side:** DO NOT use separate `side` or `type` field. Use signed `size` instead.

---

### Trade Fields

| Use This ✅ | NOT These ❌ | Type | Source |
|------------|-------------|------|--------|
| `realized_pnl` | ~~profitAndLoss~~, ~~profit_and_loss~~, ~~pnl~~ | `float \| None` | SignalR: `profitAndLoss` |
| `size` | ~~quantity~~ | `int` | SignalR: `quantity` |
| `side` | N/A | `int` | 0=Buy, 1=Sell |
| `trade_id` | N/A | `int` | SignalR: `id` |

---

### Order Fields

| Use This ✅ | NOT These ❌ | Type | Source |
|------------|-------------|------|--------|
| `quantity` | ~~size~~, ~~contracts~~ | `int` | SignalR: `quantity` |
| `side` | N/A | `int` | 0=Buy, 1=Sell |
| `order_type` | N/A | `int` | 1=Limit, 2=Market, 4=Stop |
| `status` | N/A | `int` | 1=Pending, 2=Filled, 3=Cancelled |
| `order_id` | N/A | `int` | SignalR: `id` |

---

### Quote Fields

| Use This ✅ | NOT These ❌ | Type | Source |
|------------|-------------|------|--------|
| `last_price` | ~~price~~ | `float` | SignalR: `lastPrice` |
| `bid` | ~~best_bid~~ | `float` | SignalR: `bestBid` |
| `ask` | ~~best_ask~~ | `float` | SignalR: `bestAsk` |
| `mid_price` | N/A | `float` | Calculated: (bid + ask) / 2 |
| `spread` | N/A | `float` | Calculated: ask - bid |

---

### Common Fields

| Use This ✅ | NOT These ❌ | Type | Notes |
|------------|-------------|------|-------|
| `account_id` | N/A | `int` | REQUIRED in all events |
| `symbol` | N/A | `str` | REQUIRED in all events |
| `timestamp` | N/A | `datetime` | datetime object, NOT string |

---

## Enum Quick Reference

### OrderSide

```python
class OrderSide(IntEnum):
    BUY = 0
    SELL = 1
```

**Usage:** Orders and trades use this. Positions use signed `size` instead.

---

### OrderType

```python
class OrderType(IntEnum):
    LIMIT = 1
    MARKET = 2
    STOP = 4
    STOP_LIMIT = 8  # If supported
```

---

### OrderStatus

```python
class OrderStatus(IntEnum):
    PENDING = 1
    FILLED = 2
    CANCELLED = 3
    REJECTED = 4
    PENDING_TRIGGER = 6
```

**SignalR String Mapping:**
```python
STATUS_MAP = {
    "Working": OrderStatus.PENDING,
    "Accepted": OrderStatus.PENDING,
    "Pending": OrderStatus.PENDING,
    "Filled": OrderStatus.FILLED,
    "Cancelled": OrderStatus.CANCELLED,
    "Rejected": OrderStatus.REJECTED,
}
```

---

## SignalR to Python Mapping

### camelCase → snake_case

| SignalR (camelCase) | Python (snake_case) | Type |
|---------------------|---------------------|------|
| `profitAndLoss` | `realized_pnl` | `float \| None` |
| `unrealizedPnl` | `unrealized_pnl` | `float` |
| `realizedPnl` | `realized_pnl` | `float` |
| `averagePrice` | `average_price` | `float` |
| `contractId` | `contract_id` | `str` |
| `accountId` | `account_id` | `int` |
| `orderId` | `order_id` | `int` |
| `tradeId` | `trade_id` | `int` |
| `lastPrice` | `last_price` | `float` |
| `bestBid` | `bid` | `float` |
| `bestAsk` | `ask` | `float` |

---

## Event Schema Templates

### TRADE_EXECUTED

```python
{
    # Identifiers (REQUIRED)
    "trade_id": int,
    "symbol": str,
    "account_id": int,

    # Trade details
    "side": int,  # 0=Buy, 1=Sell
    "size": int,
    "price": float,

    # P&L (CRITICAL)
    "realized_pnl": float | None,  # None for half-turn trades

    # Metadata
    "timestamp": datetime,
    "raw_data": dict,
}
```

---

### POSITION_UPDATED

```python
{
    # Identifiers (REQUIRED)
    "contract_id": str,
    "symbol": str,
    "account_id": int,

    # Position details
    "size": int,  # Signed: positive=long, negative=short
    "average_price": float,

    # P&L
    "unrealized_pnl": float,
    "realized_pnl": float,

    # Metadata
    "timestamp": datetime,
    "raw_data": dict,
}
```

---

### ORDER Event (PLACED/FILLED/CANCELLED/REJECTED)

```python
{
    # Identifiers (REQUIRED)
    "order_id": int,
    "symbol": str,
    "account_id": int,

    # Order details
    "side": int,  # 0=Buy, 1=Sell
    "quantity": int,
    "order_type": int,  # 1=Limit, 2=Market, 4=Stop
    "status": int,  # 1=Pending, 2=Filled, 3=Cancelled

    # Prices
    "price": float | None,  # Limit price
    "stop_price": float | None,  # Stop price

    # Fill info
    "filled_quantity": int,

    # Metadata
    "timestamp": datetime,
    "raw_data": dict,
}
```

---

### QUOTE_UPDATED

```python
{
    # Identifier (REQUIRED)
    "symbol": str,

    # Quote data
    "last_price": float,
    "bid": float,
    "ask": float,
    "bid_size": int,
    "ask_size": int,

    # Calculated fields
    "mid_price": float,  # (bid + ask) / 2
    "spread": float,  # ask - bid

    # Metadata
    "timestamp": datetime,
    "age_ms": int,  # Quote age in milliseconds
}
```

---

## Common Mistakes to Avoid

### ❌ DON'T Use These

```python
# WRONG: Using camelCase in Python code
event.data["profitAndLoss"]  # ❌
event.data["unrealizedPnl"]  # ❌
event.data["averagePrice"]   # ❌

# WRONG: Using old field names
event.data["pnl"]            # ❌ Ambiguous (realized or unrealized?)
event.data["entry_price"]    # ❌ Use average_price
event.data["avgPrice"]       # ❌ Typo/old name

# WRONG: Timestamp as string
"timestamp": datetime.now().isoformat()  # ❌ Use datetime object

# WRONG: Position side enum
position["type"] == 1  # ❌ Use signed size instead

# WRONG: Missing account_id
{
    "symbol": "MNQ",
    # ❌ Missing account_id!
}
```

---

### ✅ DO Use These

```python
# CORRECT: Using snake_case in Python code
event.data["realized_pnl"]   # ✅
event.data["unrealized_pnl"] # ✅
event.data["average_price"]  # ✅

# CORRECT: Specific P&L field names
event.data["realized_pnl"]   # ✅ From closed trades
event.data["unrealized_pnl"] # ✅ From open positions

# CORRECT: Timestamp as datetime object
"timestamp": datetime.now()  # ✅

# CORRECT: Position side from signed size
if position["size"] > 0:     # ✅ Long position
elif position["size"] < 0:   # ✅ Short position

# CORRECT: Always include account_id
{
    "symbol": "MNQ",
    "account_id": 123,  # ✅ Required!
}
```

---

## Rule-Specific Field Usage

### RULE-003 (DailyRealizedLoss)

```python
# Listen for: TRADE_EXECUTED events
# Critical field: realized_pnl

async def evaluate(self, event: RiskEvent, engine: RiskEngine):
    if event.event_type != EventType.TRADE_EXECUTED:
        return None

    # ✅ CORRECT
    pnl = event.data.get("realized_pnl")

    # ❌ WRONG
    # pnl = event.data.get("profitAndLoss")
    # pnl = event.data.get("pnl")

    if pnl is None:
        return None  # Half-turn trade

    # Update daily P&L
    account_id = event.data.get("account_id")  # ✅ Required
    daily_pnl = await self.pnl_tracker.add_trade_pnl(account_id, pnl)
```

---

### RULE-004 (DailyUnrealizedLoss)

```python
# Listen for: POSITION_UPDATED, QUOTE_UPDATED events
# Critical fields: average_price, size, last_price (from quote)

async def evaluate(self, event: RiskEvent, engine: RiskEngine):
    if event.event_type not in [EventType.POSITION_UPDATED, EventType.QUOTE_UPDATED]:
        return None

    # ✅ CORRECT
    current_price = event.data.get("last_price")  # From quote
    entry_price = event.data.get("average_price")  # From position
    size = event.data.get("size")  # Signed integer

    # ❌ WRONG
    # entry_price = event.data.get("entry_price")
    # entry_price = event.data.get("avgPrice")

    # Calculate unrealized P&L
    if size > 0:  # Long
        unrealized = (current_price - entry_price) * size * multiplier
    else:  # Short
        unrealized = (entry_price - current_price) * abs(size) * multiplier
```

---

## Type Annotations

```python
from typing import TypedDict
from datetime import datetime

class TradeExecutedData(TypedDict):
    """Type hints for TRADE_EXECUTED event data."""
    trade_id: int
    symbol: str
    account_id: int
    side: int
    size: int
    price: float
    realized_pnl: float | None
    timestamp: datetime
    raw_data: dict

class PositionUpdatedData(TypedDict):
    """Type hints for POSITION_UPDATED event data."""
    contract_id: str
    symbol: str
    account_id: int
    size: int
    average_price: float
    unrealized_pnl: float
    realized_pnl: float
    timestamp: datetime
    raw_data: dict

class QuoteUpdatedData(TypedDict):
    """Type hints for QUOTE_UPDATED event data."""
    symbol: str
    last_price: float
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    mid_price: float
    spread: float
    timestamp: datetime
    age_ms: int
```

---

## Migration Checklist

When updating code to use canonical schemas:

- [ ] Replace `profitAndLoss` → `realized_pnl`
- [ ] Replace `unrealizedPnl` → `unrealized_pnl`
- [ ] Replace `averagePrice` → `average_price`
- [ ] Replace `entry_price` → `average_price`
- [ ] Replace `avgPrice` → `average_price`
- [ ] Remove redundant `side` field from positions (use signed `size`)
- [ ] Add `account_id` to all events
- [ ] Change timestamp from string → datetime object
- [ ] Use `size` for trades, `quantity` for orders
- [ ] Map OrderStatus strings to enums
- [ ] Use OrderSide enum (0=Buy, 1=Sell)

---

## Questions?

**See full audit:** `DATA_SCHEMA_CONSISTENCY_AUDIT.md`

**Event handling spec:** `event-handling.md`

**SDK integration spec:** `sdk-integration.md`

