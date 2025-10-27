# Event Data Schemas

**Version**: 1.0
**Last Updated**: 2025-10-27
**Status**: Canonical Reference
**Purpose**: Defines the exact data schemas for all SDK events used by the Risk Manager

---

## Document Purpose

This document serves as the **single source of truth** for event data schemas. All rule specifications, implementation code, and tests MUST reference these canonical schemas.

**Key Principles**:
- ✅ Field names match SDK exactly (from `SDK_EVENTS_QUICK_REFERENCE.txt`)
- ✅ All enum values documented with numeric mappings
- ✅ All nullable fields explicitly marked
- ✅ Includes both SDK raw fields and calculated fields

---

## Table of Contents

1. [Position Events](#position-events)
   - [POSITION_OPENED](#position_opened)
   - [POSITION_UPDATED](#position_updated)
   - [POSITION_CLOSED](#position_closed)
2. [Order Events](#order-events)
   - [ORDER_PLACED](#order_placed)
   - [ORDER_FILLED](#order_filled)
   - [ORDER_PARTIAL_FILL](#order_partial_fill)
   - [ORDER_CANCELLED](#order_cancelled)
   - [ORDER_MODIFIED](#order_modified)
   - [ORDER_REJECTED](#order_rejected)
3. [Trade Events](#trade-events)
   - [TRADE_EXECUTED](#trade_executed)
4. [Quote Events](#quote-events)
   - [QUOTE_UPDATE](#quote_update)
   - [NEW_BAR](#new_bar)
5. [Account Events](#account-events)
   - [ACCOUNT_UPDATED](#account_updated)
6. [Enum Reference Tables](#enum-reference-tables)

---

## Position Events

### POSITION_OPENED

**When**: Fires when a new position is established (size goes from 0 → non-zero)

**Schema**:
```python
{
    # Identifiers
    "contract_id": str,        # e.g., "CON.F.US.MNQ.Z25"
    "symbol": str,             # e.g., "MNQ" (extracted from contract_id)
    "account_id": int,         # Account ID (CRITICAL - required for multi-account)

    # Position Details
    "size": int,               # Signed integer: positive=long, negative=short
    "average_price": float,    # Average entry price (SDK: averagePrice)

    # P&L
    "unrealized_pnl": float,   # Unrealized P&L at position open (usually 0.0)
    "realized_pnl": float,     # Cumulative realized P&L (SDK: realizedPnl)

    # Metadata
    "timestamp": datetime,     # datetime object (NOT string)
    "raw_data": dict          # Original SignalR data for debugging
}
```

**SDK Mapping**:
```python
{
    "contract_id": position_data.get("contractId"),
    "symbol": extract_symbol(position_data.get("contractId")),
    "account_id": position_data.get("accountId"),  # CRITICAL FIELD
    "size": position_data.get("size"),  # Signed integer
    "average_price": position_data.get("averagePrice"),  # Note: camelCase from SDK
    "unrealized_pnl": position_data.get("unrealizedPnl", 0.0),
    "realized_pnl": position_data.get("realizedPnl", 0.0),
    "timestamp": datetime.utcnow(),
    "raw_data": position_data
}
```

**Field Notes**:
- `size`: Positive = long position, Negative = short position
- `average_price`: Average entry price (NOT `entry_price` or `avgPrice`)
- `account_id`: CRITICAL for multi-account support
- `timestamp`: datetime object, convert to string only for JSON serialization

**Used By**: RULE-001, RULE-002, RULE-004, RULE-005, RULE-008, RULE-009, RULE-011, RULE-012

---

### POSITION_UPDATED

**When**: Fires when an existing position changes size (scaling in/out)

**Schema**: Identical to POSITION_OPENED

```python
{
    # Identifiers
    "contract_id": str,
    "symbol": str,
    "account_id": int,  # CRITICAL

    # Position Details
    "size": int,               # Updated size (signed)
    "average_price": float,    # Updated average price

    # P&L
    "unrealized_pnl": float,   # Current unrealized P&L
    "realized_pnl": float,     # Cumulative realized P&L

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**Difference from POSITION_OPENED**: Size changes from non-zero → different non-zero value

**Used By**: RULE-001, RULE-002, RULE-004, RULE-005, RULE-009, RULE-011, RULE-012

---

### POSITION_CLOSED

**When**: Fires when a position is completely flattened (size goes to 0)

**Schema**:
```python
{
    # Identifiers
    "contract_id": str,
    "symbol": str,
    "account_id": int,  # CRITICAL

    # Final P&L
    "realized_pnl": float,     # Total realized P&L from this position

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**Field Notes**:
- `size` not included (always 0)
- `realized_pnl`: Total P&L realized when position closed
- Final event in position lifecycle

**Used By**: RULE-001, RULE-002, RULE-004, RULE-005, RULE-011, RULE-012

---

## Order Events

### ORDER_PLACED

**When**: Fires when a new order is submitted to the exchange

**Schema**:
```python
{
    # Identifiers
    "order_id": int,           # Unique order ID
    "symbol": str,
    "account_id": int,
    "contract_id": str,

    # Order Details
    "side": int,               # 1=BUY, 2=SELL (see enum table)
    "quantity": int,           # Number of contracts
    "order_type": int,         # 1=MARKET, 2=LIMIT, 3=STOP (see enum table)
    "status": int,             # 6=PENDING_TRIGGER for stop orders

    # Prices (CRITICAL - includes stopPrice)
    "limit_price": float | None,  # Limit price (null for market/stop orders)
    "stop_price": float | None,   # Stop price (CRITICAL for RULE-008)

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**SDK Mapping**:
```python
{
    "order_id": order_data.get("id"),
    "symbol": extract_symbol(order_data.get("contractId")),
    "account_id": order_data.get("accountId"),
    "contract_id": order_data.get("contractId"),
    "side": order_data.get("side"),  # 1=BUY, 2=SELL
    "quantity": order_data.get("size"),  # Note: SDK uses 'size'
    "order_type": order_data.get("type"),  # 1=MARKET, 2=LIMIT, 3=STOP
    "status": order_data.get("status"),
    "limit_price": order_data.get("limitPrice"),
    "stop_price": order_data.get("stopPrice"),  # CRITICAL FIELD
    "timestamp": datetime.utcnow(),
    "raw_data": order_data
}
```

**Field Notes**:
- `stop_price`: CRITICAL for RULE-008 (stop-loss validation)
- `order_type`: 3=STOP means this is a stop-loss or stop-entry order
- `side`: 1=BUY, 2=SELL (not 0=BUY, 1=SELL)
- `quantity`: Use `quantity` for orders (not `size`)

**Used By**: RULE-008, RULE-012

**Example - Stop Loss Order**:
```python
{
    "order_id": 12345,
    "symbol": "MNQ",
    "side": 2,  # SELL (closing long position)
    "order_type": 3,  # STOP
    "stop_price": 25940.0,  # Stop triggered at this price
    "limit_price": None
}
```

---

### ORDER_FILLED

**When**: Fires when an order is completely filled

**Schema**:
```python
{
    # Identifiers
    "order_id": int,
    "symbol": str,
    "account_id": int,
    "contract_id": str,

    # Fill Details
    "filled_quantity": int,    # Number of contracts filled
    "filled_price": float,     # Actual execution price
    "side": int,               # 1=BUY, 2=SELL
    "order_type": int,         # 1=MARKET, 2=LIMIT, 3=STOP

    # Status Change
    "old_status": int,         # Previous status (e.g., 6=PENDING_TRIGGER)
    "new_status": int,         # New status (2=FILLED)

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**SDK Mapping**:
```python
{
    "order_id": order_data.get("id"),
    "symbol": extract_symbol(order_data.get("contractId")),
    "account_id": order_data.get("accountId"),
    "contract_id": order_data.get("contractId"),
    "filled_quantity": order_data.get("filledQuantity"),
    "filled_price": order_data.get("filledPrice"),
    "side": order_data.get("side"),
    "order_type": order_data.get("type"),
    "old_status": old_status,  # From state tracking
    "new_status": order_data.get("status"),  # 2=FILLED
    "timestamp": datetime.utcnow(),
    "raw_data": order_data
}
```

**Field Notes**:
- `old_status`: 6=PENDING_TRIGGER indicates stop order was triggered
- `filled_price`: Actual execution price (may differ from limit/stop price)

**Used By**: Internal state tracking

---

### ORDER_PARTIAL_FILL

**When**: Fires when an order is partially filled

**Schema**: Similar to ORDER_FILLED, but `filled_quantity` < `quantity`

```python
{
    # Identifiers
    "order_id": int,
    "symbol": str,
    "account_id": int,

    # Partial Fill Details
    "filled_quantity": int,    # Contracts filled so far
    "remaining_quantity": int, # Contracts still pending
    "filled_price": float,     # Price of this partial fill

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**Used By**: Internal state tracking

---

### ORDER_CANCELLED

**When**: Fires when an order is cancelled

**Schema**:
```python
{
    # Identifiers
    "order_id": int,
    "symbol": str,
    "account_id": int,

    # Cancellation Details
    "reason": str | None,      # Cancellation reason (if provided)

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**Used By**: Internal state tracking

---

### ORDER_MODIFIED

**When**: Fires when an order is modified (price/quantity change)

**Schema**:
```python
{
    # Identifiers
    "order_id": int,
    "symbol": str,
    "account_id": int,

    # Modified Fields
    "new_limit_price": float | None,
    "new_stop_price": float | None,
    "new_quantity": int | None,

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**Used By**: RULE-012 (trailing stop modifications)

---

### ORDER_REJECTED

**When**: Fires when an order is rejected by the exchange

**Schema**:
```python
{
    # Identifiers
    "order_id": int,
    "symbol": str,
    "account_id": int,

    # Rejection Details
    "reason": str,             # Rejection reason
    "error_code": str | None,  # Error code (if provided)

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**Used By**: Error handling, monitoring

---

## Trade Events

### TRADE_EXECUTED

**When**: Fires when a trade executes (buy or sell)

**Schema**:
```python
{
    # Identifiers
    "trade_id": int,           # Unique trade ID
    "symbol": str,
    "account_id": int,         # CRITICAL - required for multi-account

    # Trade Details
    "side": int,               # 1=BUY, 2=SELL
    "size": int,               # Number of contracts (use 'size' for trades)
    "price": float,            # Execution price

    # P&L (CRITICAL)
    "realized_pnl": float | None,  # Realized P&L (None for opening trades)

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**SDK Mapping**:
```python
{
    "trade_id": trade_data.get("id"),
    "symbol": extract_symbol(trade_data.get("contractId")),
    "account_id": trade_data.get("accountId"),  # CRITICAL FIELD
    "side": trade_data.get("side"),  # 1=BUY, 2=SELL
    "size": trade_data.get("quantity"),  # Note: SDK uses 'quantity'
    "price": trade_data.get("price"),
    "realized_pnl": trade_data.get("profitAndLoss"),  # CRITICAL - null for half-turns
    "timestamp": datetime.utcnow(),
    "raw_data": trade_data
}
```

**Field Notes**:
- `realized_pnl`: **CRITICAL** field for RULE-003 and RULE-013
  - `None` for opening trades (half-turn)
  - `float` for closing trades (full round-turn)
  - **ALWAYS check for None before using**
- `account_id`: **CRITICAL** for multi-account support
- `size`: Use `size` for trades (not `quantity`)

**Used By**: RULE-003, RULE-006, RULE-007, RULE-013

**Example - Opening Trade (Half-Turn)**:
```python
{
    "trade_id": 101112,
    "symbol": "MNQ",
    "side": 1,  # BUY
    "size": 2,
    "price": 25947.0,
    "realized_pnl": None  # ← None for opening trades
}
```

**Example - Closing Trade (Full Round-Turn)**:
```python
{
    "trade_id": 101113,
    "symbol": "MNQ",
    "side": 2,  # SELL
    "size": 2,
    "price": 25927.0,
    "realized_pnl": -40.0  # ← Actual P&L for closing trades
}
```

---

## Quote Events

### QUOTE_UPDATE

**When**: Fires on every market data update (high frequency - typically 10-100 times per second)

**Schema**:
```python
{
    # Identifiers
    "symbol": str,             # e.g., "MNQ"

    # Quote Data
    "last_price": float,       # Last traded price (CRITICAL for unrealized P&L)
    "bid": float,              # Best bid price
    "ask": float,              # Best ask price
    "bid_size": int,           # Contracts at bid
    "ask_size": int,           # Contracts at ask

    # Calculated Fields
    "mid_price": float,        # (bid + ask) / 2
    "spread": float,           # ask - bid

    # Metadata
    "timestamp": datetime,     # Quote timestamp
    "age_ms": int,             # Quote age in milliseconds
    "raw_data": dict
}
```

**SDK Mapping**:
```python
{
    "symbol": extract_symbol(quote_data.get("contractId")),
    "last_price": quote_data.get("last"),  # CRITICAL FIELD
    "bid": quote_data.get("bid"),
    "ask": quote_data.get("ask"),
    "bid_size": quote_data.get("bidSize"),
    "ask_size": quote_data.get("askSize"),
    "mid_price": (quote_data.get("bid") + quote_data.get("ask")) / 2,
    "spread": quote_data.get("ask") - quote_data.get("bid"),
    "timestamp": datetime.utcnow(),
    "age_ms": calculate_age(quote_data.get("timestamp")),
    "raw_data": quote_data
}
```

**Field Notes**:
- `last_price`: **CRITICAL** for calculating unrealized P&L (RULE-004, RULE-005)
- High frequency: Consider throttling (e.g., 1 update per second)
- `mid_price` and `spread`: Calculated fields
- `age_ms`: For detecting stale quotes

**Used By**: RULE-004, RULE-005, RULE-012

**Performance Considerations**:
- Fire rate: 10-100 times per second per symbol
- Throttling recommended: Process max 1 per second for risk rules
- Stale detection: Discard quotes older than 5 seconds

---

### NEW_BAR

**When**: Fires when a new candlestick bar completes

**Schema**:
```python
{
    # Identifiers
    "symbol": str,
    "timeframe": str,          # e.g., "1m", "5m", "1h"

    # OHLCV Data
    "open": float,
    "high": float,
    "low": float,
    "close": float,
    "volume": int,

    # Metadata
    "bar_start": datetime,     # Bar start time
    "bar_end": datetime,       # Bar end time
    "timestamp": datetime,     # Event timestamp
    "raw_data": dict
}
```

**Used By**: Future technical analysis features

---

## Account Events

### ACCOUNT_UPDATED

**When**: Fires when account state changes (balance, authorization, etc.)

**Schema**:
```python
{
    # Identifiers
    "account_id": int,

    # Account State
    "balance": float,          # Current account balance
    "can_trade": bool,         # CRITICAL for RULE-010

    # Statistics (optional)
    "equity": float | None,
    "margin_used": float | None,
    "margin_available": float | None,

    # Metadata
    "timestamp": datetime,
    "raw_data": dict
}
```

**SDK Mapping**:
```python
{
    "account_id": account_data.get("id"),
    "balance": account_data.get("balance"),
    "can_trade": account_data.get("canTrade"),  # CRITICAL FIELD
    "equity": account_data.get("equity"),
    "margin_used": account_data.get("marginUsed"),
    "margin_available": account_data.get("marginAvailable"),
    "timestamp": datetime.utcnow(),
    "raw_data": account_data
}
```

**Field Notes**:
- `can_trade`: **CRITICAL** for RULE-010 (authorization loss detection)
- Fires when trader loses permission to trade
- Immediate action required if `can_trade` becomes False

**Used By**: RULE-010

---

## Enum Reference Tables

### Order Side (order.side)

| Value | Name | Description |
|-------|------|-------------|
| `1` | BUY | Buy order (long entry or short exit) |
| `2` | SELL | Sell order (short entry or long exit) |

**Usage**:
```python
if order_event["side"] == 1:
    # BUY order
elif order_event["side"] == 2:
    # SELL order
```

**Note**: NOT 0-indexed (0=BUY is INCORRECT)

---

### Order Type (order.type)

| Value | Name | Description |
|-------|------|-------------|
| `1` | MARKET | Market order (immediate execution at current price) |
| `2` | LIMIT | Limit order (execute at specified price or better) |
| `3` | STOP | Stop order (becomes market order when stop price hit) |

**Usage**:
```python
if order_event["order_type"] == 3:
    # This is a stop order - check for stop_price
    stop_price = order_event["stop_price"]
```

**CRITICAL for RULE-008**: Stop-loss orders have `order_type == 3` and `stop_price != None`

---

### Order Status (order.status)

| Value | Name | Description |
|-------|------|-------------|
| `1` | PENDING | Order submitted but not yet filled |
| `2` | FILLED | Order completely filled |
| `3` | CANCELLED | Order cancelled |
| `4` | REJECTED | Order rejected by exchange |
| `6` | PENDING_TRIGGER | Stop order waiting for trigger price |

**Usage**:
```python
# Detect when stop order triggers
if old_status == 6 and new_status == 2:
    # Stop order was triggered and filled
```

**Note**: Status 6 (PENDING_TRIGGER) is specific to stop orders

---

### Position Type (position.size sign)

Positions use **signed integers** for size (NOT a separate enum):

| Size | Type | Description |
|------|------|-------------|
| `> 0` | LONG | Long position (positive size) |
| `< 0` | SHORT | Short position (negative size) |
| `0` | FLAT | No position |

**Usage**:
```python
size = position_event["size"]
if size > 0:
    # Long position
    contracts = size
elif size < 0:
    # Short position
    contracts = abs(size)
else:
    # Flat (no position)
```

**IMPORTANT**: Do NOT add a separate `side` or `type` field for positions. Use the sign of `size`.

---

## Schema Validation Checklist

Use this checklist when implementing or testing event handling:

### Event Completeness
- [ ] All required fields present
- [ ] All nullable fields explicitly marked
- [ ] `account_id` included in all account-specific events
- [ ] `timestamp` is datetime object (not string)

### Field Names
- [ ] Position price uses `average_price` (not `entry_price` or `avgPrice`)
- [ ] Trade P&L uses `realized_pnl` (not `pnl` or `profitAndLoss`)
- [ ] Position P&L uses `unrealized_pnl` and `realized_pnl`
- [ ] Orders use `quantity`, trades/positions use `size`

### Enum Values
- [ ] Order side uses 1=BUY, 2=SELL (not 0=BUY, 1=SELL)
- [ ] Order type uses 1=MARKET, 2=LIMIT, 3=STOP
- [ ] Order status includes 6=PENDING_TRIGGER for stop orders
- [ ] Position type uses signed `size` (not separate enum)

### Critical Fields
- [ ] `TRADE_EXECUTED.realized_pnl` present (can be None)
- [ ] `ORDER_PLACED.stop_price` present for stop orders
- [ ] `ACCOUNT_UPDATED.can_trade` present
- [ ] `QUOTE_UPDATE.last_price` present

### Data Types
- [ ] All prices are `float`
- [ ] All sizes/quantities are `int`
- [ ] All P&L values are `float | None`
- [ ] All timestamps are `datetime` objects

---

## Schema Evolution Log

### Version 1.0 (2025-10-27)
- Initial canonical schema definitions
- Fixed 12 critical inconsistencies from audit:
  1. Added `realized_pnl` to TRADE_EXECUTED
  2. Added `account_id` to all events
  3. Added `stop_price` to ORDER_PLACED
  4. Fixed position field names (use `average_price`, not `entry_price`)
  5. Fixed P&L field names (use `realized_pnl`, not `pnl`)
  6. Documented enum values (OrderSide, OrderType, OrderStatus)
  7. Removed redundant `side` field from positions (use signed `size`)
  8. Fixed timestamp type (datetime object, not string)
  9. Standardized `size` vs `quantity` usage
  10. Added calculated fields to QUOTE_UPDATE
  11. Fixed ORDER_PLACED schema with stop_price
  12. Documented position size as signed integer

---

## References

- **SDK Events Source**: `SDK_EVENTS_QUICK_REFERENCE.txt`
- **Audit Report**: `docs/specifications/unified/DATA_SCHEMA_CONSISTENCY_AUDIT.md`
- **Implementation**: `src/risk_manager/sdk/event_bridge.py`
- **State Tracking**: `docs/specifications/unified/data-schemas/state-tracking-schemas.md`

---

**Document Status**: Canonical ✅
**Last Reviewed**: 2025-10-27
**Next Review**: After any SDK version upgrade
