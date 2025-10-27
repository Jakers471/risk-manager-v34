# Schema-to-SDK Field Mapping

**Version**: 1.0
**Last Updated**: 2025-10-27
**Status**: Reference Guide
**Purpose**: Complete mapping between SDK raw fields and canonical Risk Manager schemas

---

## Document Purpose

This document provides the **exact field-by-field mapping** from SDK raw event data to our canonical event schemas. Use this as a reference when:
- Implementing event bridge handlers
- Writing tests with mock SDK data
- Debugging field name mismatches
- Validating event data

**Source of Truth**:
- SDK Raw Data: TopstepX SignalR events (camelCase)
- Canonical Schemas: `event-data-schemas.md` (snake_case)

---

## Quick Reference Table

| Risk Manager Field | SDK Field | Type | Notes |
|-------------------|-----------|------|-------|
| **Position Events** |
| `contract_id` | `contractId` | str | Direct mapping |
| `symbol` | Extract from `contractId` | str | Parse from contract ID |
| `account_id` | `accountId` | int | CRITICAL - always include |
| `size` | `size` | int | Signed: positive=long, negative=short |
| `average_price` | `averagePrice` | float | NOT `entry_price` or `avgPrice` |
| `unrealized_pnl` | `unrealizedPnl` | float | camelCase from SDK |
| `realized_pnl` | `realizedPnl` | float | camelCase from SDK |
| **Order Events** |
| `order_id` | `id` | int | Order ID |
| `side` | `side` | int | 1=BUY, 2=SELL |
| `quantity` | `size` | int | SDK uses `size`, we use `quantity` for orders |
| `order_type` | `type` | int | 1=MARKET, 2=LIMIT, 3=STOP |
| `status` | `status` | int | 1=PENDING, 2=FILLED, 3=CANCELLED, etc. |
| `limit_price` | `limitPrice` | float\|None | Limit order price |
| `stop_price` | `stopPrice` | float\|None | **CRITICAL** - stop order trigger price |
| `filled_quantity` | `filledQuantity` | int | Contracts filled |
| `filled_price` | `filledPrice` | float | Actual execution price |
| **Trade Events** |
| `trade_id` | `id` | int | Trade ID |
| `size` | `quantity` | int | SDK uses `quantity`, we use `size` for trades |
| `price` | `price` | float | Execution price |
| `realized_pnl` | `profitAndLoss` | float\|None | **CRITICAL** - None for opening trades |
| **Quote Events** |
| `last_price` | `last` | float | **CRITICAL** - current market price |
| `bid` | `bid` | float | Best bid |
| `ask` | `ask` | float | Best ask |
| `bid_size` | `bidSize` | int | Contracts at bid |
| `ask_size` | `askSize` | int | Contracts at ask |
| **Account Events** |
| `balance` | `balance` | float | Account balance |
| `can_trade` | `canTrade` | bool | **CRITICAL** - trading authorization |
| `equity` | `equity` | float | Account equity |
| `margin_used` | `marginUsed` | float | Used margin |
| `margin_available` | `marginAvailable` | float | Available margin |

---

## Position Events

### POSITION_OPENED / POSITION_UPDATED

**SDK Raw Data** (SignalR):
```json
{
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "size": 2,
    "averagePrice": 25947.0,
    "unrealizedPnl": 0.0,
    "realizedPnl": 0.0,
    "type": 1
}
```

**Risk Manager Canonical Schema**:
```python
{
    "contract_id": "CON.F.US.MNQ.Z25",      # contractId
    "symbol": "MNQ",                         # Extract from contractId
    "account_id": 123456,                    # accountId
    "size": 2,                               # size (unchanged)
    "average_price": 25947.0,                # averagePrice (NOT avgPrice!)
    "unrealized_pnl": 0.0,                   # unrealizedPnl
    "realized_pnl": 0.0,                     # realizedPnl
    "timestamp": datetime.utcnow(),          # Generated (not from SDK)
    "raw_data": { ... }                      # Store original SDK data
}
```

**Mapping Code**:
```python
def map_position_event(position_data: dict) -> dict:
    """Map SDK position data to canonical schema."""
    contract_id = position_data.get("contractId")
    symbol = extract_symbol(contract_id)  # e.g., "CON.F.US.MNQ.Z25" → "MNQ"

    return {
        "contract_id": contract_id,
        "symbol": symbol,
        "account_id": position_data.get("accountId"),  # CRITICAL
        "size": position_data.get("size"),
        "average_price": position_data.get("averagePrice"),  # Note camelCase
        "unrealized_pnl": position_data.get("unrealizedPnl", 0.0),
        "realized_pnl": position_data.get("realizedPnl", 0.0),
        "timestamp": datetime.utcnow(),
        "raw_data": position_data
    }
```

**Critical Notes**:
- ⚠️ SDK uses `averagePrice` (camelCase), NOT `entry_price` or `avgPrice`
- ⚠️ `account_id` is CRITICAL - must be extracted from SDK
- ⚠️ `size` is already signed (positive=long, negative=short)
- ⚠️ SDK field `type` (1=long, 2=short) is REDUNDANT - ignore it, use signed `size`

---

### POSITION_CLOSED

**SDK Raw Data** (SignalR):
```json
{
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "realizedPnl": -40.0,
    "size": 0
}
```

**Risk Manager Canonical Schema**:
```python
{
    "contract_id": "CON.F.US.MNQ.Z25",
    "symbol": "MNQ",
    "account_id": 123456,
    "realized_pnl": -40.0,                   # Total P&L from position
    "timestamp": datetime.utcnow(),
    "raw_data": { ... }
}
```

**Mapping Code**:
```python
def map_position_closed_event(position_data: dict) -> dict:
    """Map SDK position closed data to canonical schema."""
    contract_id = position_data.get("contractId")
    symbol = extract_symbol(contract_id)

    return {
        "contract_id": contract_id,
        "symbol": symbol,
        "account_id": position_data.get("accountId"),
        "realized_pnl": position_data.get("realizedPnl", 0.0),
        "timestamp": datetime.utcnow(),
        "raw_data": position_data
    }
```

---

## Order Events

### ORDER_PLACED

**SDK Raw Data** (SignalR):
```json
{
    "id": 78910,
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "side": 2,
    "size": 1,
    "type": 3,
    "status": 6,
    "limitPrice": null,
    "stopPrice": 25940.0
}
```

**Risk Manager Canonical Schema**:
```python
{
    "order_id": 78910,                       # id
    "symbol": "MNQ",                         # Extract from contractId
    "account_id": 123456,                    # accountId
    "contract_id": "CON.F.US.MNQ.Z25",      # contractId
    "side": 2,                               # side (2=SELL)
    "quantity": 1,                           # size → quantity (for orders)
    "order_type": 3,                         # type (3=STOP)
    "status": 6,                             # status (6=PENDING_TRIGGER)
    "limit_price": None,                     # limitPrice
    "stop_price": 25940.0,                   # stopPrice (CRITICAL!)
    "timestamp": datetime.utcnow(),
    "raw_data": { ... }
}
```

**Mapping Code**:
```python
def map_order_placed_event(order_data: dict) -> dict:
    """Map SDK order placed data to canonical schema."""
    contract_id = order_data.get("contractId")
    symbol = extract_symbol(contract_id)

    return {
        "order_id": order_data.get("id"),
        "symbol": symbol,
        "account_id": order_data.get("accountId"),
        "contract_id": contract_id,
        "side": order_data.get("side"),  # 1=BUY, 2=SELL
        "quantity": order_data.get("size"),  # SDK uses 'size'
        "order_type": order_data.get("type"),  # 1=MARKET, 2=LIMIT, 3=STOP
        "status": order_data.get("status"),
        "limit_price": order_data.get("limitPrice"),
        "stop_price": order_data.get("stopPrice"),  # CRITICAL for RULE-008
        "timestamp": datetime.utcnow(),
        "raw_data": order_data
    }
```

**Critical Notes**:
- ⚠️ `stop_price` (SDK: `stopPrice`) is CRITICAL for RULE-008
- ⚠️ SDK uses `size`, we use `quantity` for orders
- ⚠️ `order.side`: 1=BUY, 2=SELL (NOT 0-indexed)
- ⚠️ `order.type`: 3=STOP means stop-loss or stop-entry order
- ⚠️ `order.status`: 6=PENDING_TRIGGER means stop order waiting for trigger

---

### ORDER_FILLED

**SDK Raw Data** (SignalR):
```json
{
    "id": 78910,
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "filledQuantity": 1,
    "filledPrice": 25940.0,
    "side": 2,
    "type": 1,
    "status": 2
}
```

**Risk Manager Canonical Schema**:
```python
{
    "order_id": 78910,
    "symbol": "MNQ",
    "account_id": 123456,
    "contract_id": "CON.F.US.MNQ.Z25",
    "filled_quantity": 1,                    # filledQuantity
    "filled_price": 25940.0,                 # filledPrice
    "side": 2,                               # side
    "order_type": 1,                         # type (1=MARKET - stop converted)
    "old_status": 6,                         # From state tracking
    "new_status": 2,                         # status (2=FILLED)
    "timestamp": datetime.utcnow(),
    "raw_data": { ... }
}
```

**Mapping Code**:
```python
def map_order_filled_event(order_data: dict, old_status: int) -> dict:
    """Map SDK order filled data to canonical schema."""
    contract_id = order_data.get("contractId")
    symbol = extract_symbol(contract_id)

    return {
        "order_id": order_data.get("id"),
        "symbol": symbol,
        "account_id": order_data.get("accountId"),
        "contract_id": contract_id,
        "filled_quantity": order_data.get("filledQuantity"),
        "filled_price": order_data.get("filledPrice"),
        "side": order_data.get("side"),
        "order_type": order_data.get("type"),
        "old_status": old_status,  # From state
        "new_status": order_data.get("status"),
        "timestamp": datetime.utcnow(),
        "raw_data": order_data
    }
```

**Critical Notes**:
- ⚠️ `old_status` = 6 indicates stop order was triggered
- ⚠️ `order_type` changes from 3 (STOP) → 1 (MARKET) after trigger

---

## Trade Events

### TRADE_EXECUTED

**SDK Raw Data** (SignalR):
```json
{
    "id": 101112,
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "side": 2,
    "quantity": 2,
    "price": 25927.0,
    "profitAndLoss": -40.0
}
```

**Risk Manager Canonical Schema**:
```python
{
    "trade_id": 101112,                      # id
    "symbol": "MNQ",                         # Extract from contractId
    "account_id": 123456,                    # accountId (CRITICAL!)
    "side": 2,                               # side (2=SELL)
    "size": 2,                               # quantity → size (for trades)
    "price": 25927.0,                        # price
    "realized_pnl": -40.0,                   # profitAndLoss (CRITICAL!)
    "timestamp": datetime.utcnow(),
    "raw_data": { ... }
}
```

**Mapping Code**:
```python
def map_trade_executed_event(trade_data: dict) -> dict:
    """Map SDK trade executed data to canonical schema."""
    contract_id = trade_data.get("contractId")
    symbol = extract_symbol(contract_id)

    return {
        "trade_id": trade_data.get("id"),
        "symbol": symbol,
        "account_id": trade_data.get("accountId"),  # CRITICAL
        "side": trade_data.get("side"),  # 1=BUY, 2=SELL
        "size": trade_data.get("quantity"),  # SDK uses 'quantity'
        "price": trade_data.get("price"),
        "realized_pnl": trade_data.get("profitAndLoss"),  # CRITICAL - can be None!
        "timestamp": datetime.utcnow(),
        "raw_data": trade_data
    }
```

**Critical Notes**:
- ⚠️ `realized_pnl` (SDK: `profitAndLoss`) is **CRITICAL** for RULE-003 and RULE-013
- ⚠️ `realized_pnl` is **None for opening trades** (half-turn) - ALWAYS check!
- ⚠️ `realized_pnl` is **float for closing trades** (full round-turn)
- ⚠️ `account_id` is **CRITICAL** for multi-account support
- ⚠️ SDK uses `quantity`, we use `size` for trades

**Example - Opening Trade**:
```python
{
    "trade_id": 101112,
    "realized_pnl": None  # ← None means opening trade (skip P&L tracking)
}
```

**Example - Closing Trade**:
```python
{
    "trade_id": 101113,
    "realized_pnl": -40.0  # ← Has value, update cumulative P&L
}
```

---

## Quote Events

### QUOTE_UPDATE

**SDK Raw Data** (SignalR):
```json
{
    "contractId": "CON.F.US.MNQ.Z25",
    "last": 25935.75,
    "bid": 25935.50,
    "ask": 25936.00,
    "bidSize": 10,
    "askSize": 15,
    "timestamp": "2025-10-27T12:34:56.789Z"
}
```

**Risk Manager Canonical Schema**:
```python
{
    "symbol": "MNQ",                         # Extract from contractId
    "last_price": 25935.75,                  # last (CRITICAL!)
    "bid": 25935.50,                         # bid
    "ask": 25936.00,                         # ask
    "bid_size": 10,                          # bidSize
    "ask_size": 15,                          # askSize
    "mid_price": 25935.75,                   # Calculated: (bid + ask) / 2
    "spread": 0.50,                          # Calculated: ask - bid
    "timestamp": datetime.utcnow(),          # Current time
    "age_ms": 50,                            # Calculated from SDK timestamp
    "raw_data": { ... }
}
```

**Mapping Code**:
```python
def map_quote_update_event(quote_data: dict) -> dict:
    """Map SDK quote update data to canonical schema."""
    contract_id = quote_data.get("contractId")
    symbol = extract_symbol(contract_id)

    bid = quote_data.get("bid")
    ask = quote_data.get("ask")
    mid_price = (bid + ask) / 2 if bid and ask else None
    spread = ask - bid if bid and ask else None

    sdk_timestamp = quote_data.get("timestamp")
    age_ms = calculate_age_ms(sdk_timestamp) if sdk_timestamp else 0

    return {
        "symbol": symbol,
        "last_price": quote_data.get("last"),  # CRITICAL for unrealized P&L
        "bid": bid,
        "ask": ask,
        "bid_size": quote_data.get("bidSize"),
        "ask_size": quote_data.get("askSize"),
        "mid_price": mid_price,
        "spread": spread,
        "timestamp": datetime.utcnow(),
        "age_ms": age_ms,
        "raw_data": quote_data
    }
```

**Critical Notes**:
- ⚠️ `last_price` (SDK: `last`) is **CRITICAL** for calculating unrealized P&L
- ⚠️ High frequency: 10-100 updates per second per symbol
- ⚠️ **Throttling recommended**: Process max 1 per second for risk rules
- ⚠️ `mid_price` and `spread` are **calculated fields** (not from SDK)
- ⚠️ `age_ms` should be calculated from SDK timestamp

---

## Account Events

### ACCOUNT_UPDATED

**SDK Raw Data** (SignalR):
```json
{
    "id": 123456,
    "balance": 148458.28,
    "canTrade": true,
    "equity": 148500.00,
    "marginUsed": 2000.00,
    "marginAvailable": 146500.00
}
```

**Risk Manager Canonical Schema**:
```python
{
    "account_id": 123456,                    # id
    "balance": 148458.28,                    # balance
    "can_trade": True,                       # canTrade (CRITICAL!)
    "equity": 148500.00,                     # equity (optional)
    "margin_used": 2000.00,                  # marginUsed (optional)
    "margin_available": 146500.00,           # marginAvailable (optional)
    "timestamp": datetime.utcnow(),
    "raw_data": { ... }
}
```

**Mapping Code**:
```python
def map_account_updated_event(account_data: dict) -> dict:
    """Map SDK account updated data to canonical schema."""
    return {
        "account_id": account_data.get("id"),
        "balance": account_data.get("balance"),
        "can_trade": account_data.get("canTrade"),  # CRITICAL for RULE-010
        "equity": account_data.get("equity"),
        "margin_used": account_data.get("marginUsed"),
        "margin_available": account_data.get("marginAvailable"),
        "timestamp": datetime.utcnow(),
        "raw_data": account_data
    }
```

**Critical Notes**:
- ⚠️ `can_trade` (SDK: `canTrade`) is **CRITICAL** for RULE-010
- ⚠️ When `can_trade` becomes False, immediate lockout required
- ⚠️ Optional fields (equity, margin) may be None

---

## Symbol Extraction Utility

**Contract ID Format**: `CON.F.US.{SYMBOL}.{EXPIRY}`

**Examples**:
- `CON.F.US.MNQ.Z25` → `MNQ`
- `CON.F.US.ES.Z25` → `ES`
- `CON.F.US.NQ.Z25` → `NQ`

**Extraction Function**:
```python
def extract_symbol(contract_id: str) -> str:
    """
    Extract symbol from TopstepX contract ID.

    Examples:
        CON.F.US.MNQ.Z25 → MNQ
        CON.F.US.ES.Z25 → ES

    Args:
        contract_id: TopstepX contract ID

    Returns:
        Symbol (e.g., "MNQ", "ES")

    Raises:
        ValueError: If contract_id format is invalid
    """
    if not contract_id:
        raise ValueError("contract_id is None or empty")

    parts = contract_id.split(".")
    if len(parts) < 4:
        raise ValueError(f"Invalid contract_id format: {contract_id}")

    # Format: CON.F.US.{SYMBOL}.{EXPIRY}
    symbol = parts[3]
    return symbol
```

---

## Data Type Conversions

### Python Types

| Field Type | Python Type | Notes |
|-----------|-------------|-------|
| Prices | `float` | All prices are float |
| Sizes/Quantities | `int` | Signed for positions, unsigned for orders |
| P&L | `float \| None` | None for opening trades |
| Timestamps | `datetime` | datetime object, NOT string |
| Booleans | `bool` | `can_trade` field |
| IDs | `int` | order_id, trade_id, account_id |
| Strings | `str` | contract_id, symbol |

### Timestamp Handling

**SDK Provides**: ISO 8601 string
**We Store**: `datetime` object
**We Serialize**: ISO 8601 string (only for JSON)

```python
# When receiving from SDK
sdk_timestamp_str = "2025-10-27T12:34:56.789Z"
timestamp = datetime.fromisoformat(sdk_timestamp_str.replace('Z', '+00:00'))

# When storing in event
event["timestamp"] = datetime.utcnow()  # datetime object, NOT string

# When serializing to JSON
def to_json(event):
    return {
        **event,
        "timestamp": event["timestamp"].isoformat()  # Convert to string here
    }
```

### None Handling

**Fields that can be None**:
- `realized_pnl` - None for opening trades
- `limit_price` - None for market/stop orders
- `stop_price` - None for market/limit orders
- Optional account fields (equity, margin)

**Always check before using**:
```python
# CORRECT
if trade_event["realized_pnl"] is not None:
    cumulative_pnl += trade_event["realized_pnl"]

# INCORRECT - will crash on None
cumulative_pnl += trade_event["realized_pnl"]  # ❌ TypeError if None
```

---

## Common Mapping Errors

### Error #1: Wrong Field Name
```python
# ❌ INCORRECT
entry_price = position_data.get("entry_price")  # Does not exist!
entry_price = position_data.get("avgPrice")     # Typo!

# ✅ CORRECT
average_price = position_data.get("averagePrice")  # SDK uses camelCase
```

### Error #2: Missing realized_pnl Check
```python
# ❌ INCORRECT - will crash on opening trades
cumulative_pnl += trade_data.get("profitAndLoss")  # None + float = TypeError

# ✅ CORRECT
pnl = trade_data.get("profitAndLoss")
if pnl is not None:
    cumulative_pnl += pnl
```

### Error #3: Missing account_id
```python
# ❌ INCORRECT - breaks multi-account support
return {
    "symbol": symbol,
    "size": size,
    # Missing account_id!
}

# ✅ CORRECT
return {
    "symbol": symbol,
    "account_id": position_data.get("accountId"),  # CRITICAL
    "size": size,
}
```

### Error #4: Wrong Enum Values
```python
# ❌ INCORRECT - order.side is 1-indexed
if order_data.get("side") == 0:  # Wrong! 0 is not BUY
    # ...

# ✅ CORRECT
if order_data.get("side") == 1:  # 1 = BUY
    # ...
elif order_data.get("side") == 2:  # 2 = SELL
    # ...
```

### Error #5: Timestamp as String
```python
# ❌ INCORRECT - stores string
return {
    "timestamp": datetime.utcnow().isoformat()  # String!
}

# ✅ CORRECT - stores datetime object
return {
    "timestamp": datetime.utcnow()  # datetime object
}
```

---

## Testing with Mock SDK Data

### Mock SDK Position Data
```python
mock_position_data = {
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "size": 2,
    "averagePrice": 25947.0,
    "unrealizedPnl": 0.0,
    "realizedPnl": 0.0,
    "type": 1
}

# Map to canonical schema
canonical_event = map_position_event(mock_position_data)

# Verify fields
assert canonical_event["contract_id"] == "CON.F.US.MNQ.Z25"
assert canonical_event["symbol"] == "MNQ"
assert canonical_event["account_id"] == 123456
assert canonical_event["size"] == 2
assert canonical_event["average_price"] == 25947.0
```

### Mock SDK Trade Data (Opening Trade)
```python
mock_opening_trade = {
    "id": 101112,
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "side": 1,
    "quantity": 2,
    "price": 25947.0,
    "profitAndLoss": None  # ← Opening trade
}

canonical_event = map_trade_executed_event(mock_opening_trade)

assert canonical_event["realized_pnl"] is None  # ← Must be None
assert canonical_event["size"] == 2
```

### Mock SDK Trade Data (Closing Trade)
```python
mock_closing_trade = {
    "id": 101113,
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "side": 2,
    "quantity": 2,
    "price": 25927.0,
    "profitAndLoss": -40.0  # ← Closing trade with P&L
}

canonical_event = map_trade_executed_event(mock_closing_trade)

assert canonical_event["realized_pnl"] == -40.0  # ← Has value
```

### Mock SDK Order Data (Stop Loss)
```python
mock_stop_order = {
    "id": 78910,
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "side": 2,
    "size": 1,
    "type": 3,  # ← STOP order
    "status": 6,  # ← PENDING_TRIGGER
    "limitPrice": None,
    "stopPrice": 25940.0  # ← CRITICAL field
}

canonical_event = map_order_placed_event(mock_stop_order)

assert canonical_event["order_type"] == 3  # STOP
assert canonical_event["stop_price"] == 25940.0  # ← Must exist
```

---

## Validation Checklist

Use this checklist when implementing event mapping:

### Field Names
- [ ] Position price uses `averagePrice` from SDK
- [ ] Trade P&L uses `profitAndLoss` from SDK
- [ ] Symbol extracted from `contractId`
- [ ] Account ID extracted from `accountId`
- [ ] Order prices use `limitPrice` and `stopPrice`

### Data Types
- [ ] Timestamps are `datetime` objects (not strings)
- [ ] P&L fields can be None (check before using)
- [ ] Sizes are `int` (signed for positions)
- [ ] Prices are `float`

### Critical Fields
- [ ] `account_id` included in all events
- [ ] `realized_pnl` mapped from `profitAndLoss`
- [ ] `stop_price` mapped from `stopPrice`
- [ ] `can_trade` mapped from `canTrade`
- [ ] `last_price` mapped from `last`

### Enum Values
- [ ] Order side: 1=BUY, 2=SELL (not 0-indexed)
- [ ] Order type: 3=STOP
- [ ] Order status: 6=PENDING_TRIGGER
- [ ] Position size: signed integer (not separate enum)

### Error Handling
- [ ] Handle None values for optional fields
- [ ] Handle missing fields gracefully
- [ ] Log warnings for unexpected data
- [ ] Store raw_data for debugging

---

## References

- **Canonical Schemas**: `docs/specifications/unified/data-schemas/event-data-schemas.md`
- **SDK Reference**: `SDK_EVENTS_QUICK_REFERENCE.txt`
- **Audit Report**: `docs/specifications/unified/DATA_SCHEMA_CONSISTENCY_AUDIT.md`
- **Implementation**: `src/risk_manager/sdk/event_bridge.py`

---

**Document Status**: Reference Guide ✅
**Last Reviewed**: 2025-10-27
**Next Review**: After any SDK version upgrade
