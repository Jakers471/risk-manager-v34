# Data Schema Consistency Audit Report

**Audit Date:** 2025-10-27
**Auditor:** Agent #4 - Data Schema Consistency
**Scope:** All documents in `docs/specifications/unified/`
**Status:** Complete

---

## Executive Summary

This audit examined data schema consistency across all unified specification documents, comparing field names, data types, enum values, and event structures. The audit identified **12 critical inconsistencies** that must be resolved to prevent runtime errors and test failures.

### Key Findings

✅ **Good News:**
- Event type enums are consistently defined
- Position data field naming is mostly consistent
- Database schemas are well-documented

❌ **Critical Issues:**
- **P&L field names**: 4 different variations (`pnl`, `profitAndLoss`, `profit_and_loss`, `unrealizedPnl`)
- **Price field names**: 3 different variations (`averagePrice`, `average_price`, `avgPrice`)
- **Side/Type enums**: Inconsistent numeric values and missing definitions
- **Missing fields**: Several documented fields not present in implementation

---

## 1. Field Name Consistency Matrix

### 1.1 P&L Fields (CRITICAL INCONSISTENCY)

| Field Purpose | Doc Reference | Implementation | Status |
|--------------|---------------|----------------|--------|
| **Trade realized P&L** | `profitAndLoss` (event-handling.md:329) | `profit_and_loss` (event_bridge.py - NOT FOUND) | ❌ **MISMATCH** |
| **Trade realized P&L** | `pnl` (event-handling.md:204) | Not used | ⚠️ Alias |
| **Position unrealized P&L** | `unrealized_pnl` (event-handling.md:231) | `unrealizedPnl` (event_bridge.py:170) | ❌ **MISMATCH** |
| **Position realized P&L** | `realized_pnl` (event-handling.md:222) | `realizedPnl` (event_bridge.py:208) | ❌ **MISMATCH** |

**Impact:** Trade events from SDK will have `profitAndLoss` field, but RULE-003 expects `pnl` or `profit_and_loss`.

**Evidence:**
- event-handling.md line 329: `"pnl": getattr(sdk_event, "profit_and_loss", None),  # ⭐ KEY`
- RULE-003 spec line 21: `pnl = trade_event['profitAndLoss']`
- Implementation event_bridge.py: Uses `unrealizedPnl` (camelCase), not `unrealized_pnl` (snake_case)

**Recommendation:**
```python
# Canonical schema (use snake_case for consistency with Python conventions)
{
    "realized_pnl": float,      # From trade execution (SDK: profitAndLoss)
    "unrealized_pnl": float     # From position update (SDK: unrealizedPnl)
}
```

---

### 1.2 Position Entry Price (CRITICAL INCONSISTENCY)

| Field Purpose | Doc Reference | Implementation | Status |
|--------------|---------------|----------------|--------|
| **Position entry price** | `entry_price` (event-handling.md:214) | `average_price` (event_bridge.py:191) | ❌ **MISMATCH** |
| **Position entry price** | `averagePrice` (sdk-integration.md:124) | `averagePrice` (SignalR raw) | ✅ Canonical |
| **Position entry price** | `avgPrice` (RULE-004:24) | Not used | ⚠️ Typo |

**Impact:** Rules expect `entry_price`, but events provide `average_price`.

**Evidence:**
- event-handling.md line 214: `"entry_price": 21000.50`
- event_bridge.py line 169: `avg_price = position_data.get('averagePrice', 0.0)`
- event_bridge.py line 191: `"average_price": avg_price`
- RULE-004 line 24: `entry_price=position_event['avgPrice']` (TYPO!)

**Recommendation:**
```python
# Canonical schema (use average_price - more accurate than entry_price)
{
    "average_price": float,  # Average entry price (SDK: averagePrice)
}

# Mapping in EventBridge:
"average_price": position_data.get("averagePrice", 0.0)
```

---

### 1.3 Position Size/Quantity

| Field Purpose | Doc Reference | Implementation | Status |
|--------------|---------------|----------------|--------|
| **Position size** | `size` (event-handling.md:202) | `size` (event_bridge.py:189) | ✅ **CONSISTENT** |
| **Order quantity** | `quantity` (event_bridge.py:274) | `quantity` | ✅ **CONSISTENT** |
| **Trade size** | `size` (event-handling.md:202) | `quantity` (event_bridge.py:312) | ⚠️ Minor inconsistency |

**Status:** Mostly consistent. Minor discrepancy between `size` (positions/trades) and `quantity` (orders/trades).

**Recommendation:** Use `size` for positions and trades, `quantity` for orders.

---

### 1.4 Identifiers

| Field Purpose | Doc Reference | Implementation | Status |
|--------------|---------------|----------------|--------|
| **Position ID** | `contract_id` (event-handling.md:211) | `contract_id` (event_bridge.py:187) | ✅ **CONSISTENT** |
| **Order ID** | `order_id` (event-handling.md) | `order_id` (event_bridge.py:271) | ✅ **CONSISTENT** |
| **Trade ID** | `trade_id` (event-handling.md:200) | `trade_id` (event_bridge.py:324) | ✅ **CONSISTENT** |
| **Account ID** | `account_id` (event-handling.md) | `account_id` | ✅ **CONSISTENT** |
| **Symbol** | `symbol` (event-handling.md:199) | `symbol` (event_bridge.py:187) | ✅ **CONSISTENT** |

**Status:** All identifier fields are consistent. ✅

---

## 2. Enum Value Consistency

### 2.1 Position Type/Side (MAJOR INCONSISTENCY)

| Document | Enum Name | Long Value | Short Value | Status |
|----------|-----------|------------|-------------|--------|
| **event-handling.md:202** | `side` | `0` (Buy) | `1` (Sell) | ⚠️ Order-centric |
| **event-handling.md:213** | `side` | `1` (Long) | `2` (Short) | ⚠️ Position-centric |
| **sdk-integration.md:123** | `size` | `> 0` (positive) | `< 0` (negative) | ⚠️ Signed integer |
| **RULE-001:22** | `type` | `1` (Long) | `2` (Short) | ⚠️ Different field name |
| **Implementation (event_bridge.py:190)** | `side` | `"long"` | `"short"` | ⚠️ String, not int |

**Impact:** Rules check numeric values (1=Long, 2=Short), but events may use strings or signed integers.

**Evidence:**
- event-handling.md line 202: `"side": 0,  # 0=Buy, 1=Sell`
- event-handling.md line 213: `"side": 1,  # 1=Long, 2=Short`
- RULE-001 line 22: `if position['type'] == 1:  # Long`
- event_bridge.py line 190: `"side": "long" if size > 0 else "short"`

**Root Cause:** Conflation of **order side** (buy/sell) and **position side** (long/short).

**Recommendation:**
```python
# For POSITIONS: Use signed size (simpler, matches SDK)
{
    "size": int,  # Positive = long, negative = short
    # DO NOT include separate "side" or "type" field for positions
}

# For ORDERS: Use side enum
{
    "side": int,  # 0 = Buy, 1 = Sell (matches TopstepX API)
}

# For TRADES: Use side enum
{
    "side": int,  # 0 = Buy, 1 = Sell
}
```

---

### 2.2 Order Type (PARTIALLY CONSISTENT)

| Document | Field Name | Market | Limit | Stop | Status |
|----------|-----------|--------|-------|------|--------|
| **event-handling.md:175** | `order_type` | `2` | `1` | `4` | ⚠️ Undocumented |
| **sdk-integration.md:175** | `order_type` | `2` | `1` | `4` | ⚠️ Same |

**Status:** Values are consistent, but enum definition is missing from documentation.

**Recommendation:** Add OrderType enum to all specs:
```python
class OrderType(IntEnum):
    LIMIT = 1
    MARKET = 2
    STOP = 4
    STOP_LIMIT = 8  # If supported
```

---

### 2.3 Order Status (MISSING ENUM DEFINITION)

| Document | Field Name | Values | Status |
|----------|-----------|--------|--------|
| **event-handling.md:175** | `status` | `1=Open, 2=Filled, 3=Cancelled, 6=PENDING_TRIGGER` | ⚠️ Incomplete |
| **sdk-integration.md:175** | `status` | Same | ⚠️ Same |
| **event_bridge.py:257** | `status` | `'Working', 'Accepted', 'Pending', 'Filled', 'Cancelled', 'Rejected'` | ❌ **MISMATCH** |

**Impact:** Specs show numeric values, but implementation uses string values.

**Evidence:**
- event-handling.md line 175: `status: int  # 1=Open, 2=Filled, 3=Cancelled`
- event_bridge.py line 257: `if status in ['Working', 'Accepted', 'Pending']:`

**Recommendation:** Define canonical OrderStatus enum:
```python
# SDK returns strings, map to our internal enum
class OrderStatus(IntEnum):
    PENDING = 1
    FILLED = 2
    CANCELLED = 3
    REJECTED = 4
    PENDING_TRIGGER = 6

# Mapping in EventBridge
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

## 3. Data Type Consistency

### 3.1 Prices (CONSISTENT ✅)

| Field | Expected Type | Implementation Type | Status |
|-------|---------------|---------------------|--------|
| `price` | `float` | `float` | ✅ |
| `average_price` | `float` | `float` | ✅ |
| `last_price` | `float` | `float` | ✅ |
| `bid` | `float` | `float` | ✅ |
| `ask` | `float` | `float` | ✅ |

**Status:** All price fields consistently use `float`. ✅

---

### 3.2 Sizes/Quantities (CONSISTENT ✅)

| Field | Expected Type | Implementation Type | Status |
|-------|---------------|---------------------|--------|
| `size` | `int` | `int` | ✅ |
| `quantity` | `int` | `int` | ✅ |
| `bid_size` | `int` | `int` | ✅ |
| `ask_size` | `int` | `int` | ✅ |

**Status:** All size/quantity fields consistently use `int`. ✅

---

### 3.3 P&L Values (CONSISTENT ✅)

| Field | Expected Type | Implementation Type | Status |
|-------|---------------|---------------------|--------|
| `realized_pnl` | `float` | `float` | ✅ |
| `unrealized_pnl` | `float` | `float` | ✅ |
| `pnl` | `float` | `float` | ✅ |

**Status:** All P&L fields consistently use `float`. ✅

---

### 3.4 Timestamps (INCONSISTENT ⚠️)

| Field | Expected Type | Implementation Type | Status |
|-------|---------------|---------------------|--------|
| `timestamp` | `datetime` (object) | `str` (ISO format) | ⚠️ **MISMATCH** |

**Evidence:**
- event-handling.md line 206: `"timestamp": datetime(...)`
- event_bridge.py line 193: `"timestamp": datetime.utcnow().isoformat()` (returns string)

**Impact:** Rules expecting datetime objects will receive strings.

**Recommendation:**
```python
# Store as datetime objects in events
{
    "timestamp": datetime.utcnow(),  # datetime object, NOT string
}

# Convert to string only in to_dict() for serialization
def to_dict(self):
    return {
        "timestamp": self.timestamp.isoformat()
    }
```

---

## 4. Event Data Schema Comparison

### 4.1 TRADE_EXECUTED Event

#### Documentation (event-handling.md:198-206)
```python
{
    "symbol": "MNQ",
    "trade_id": 101112,
    "side": 0,  # 0=Buy, 1=Sell
    "size": 2,
    "price": 21000.75,
    "pnl": -50.25,  # Realized P&L (null for half-turns)
    "timestamp": datetime(...)
}
```

#### Implementation (event_bridge.py:320-331)
```python
{
    "symbol": symbol,
    "trade_id": trade_id,
    "side": side,  # String: 'Unknown', 'Buy', 'Sell'
    "quantity": quantity,  # NOT 'size'
    "price": price,
    "timestamp": datetime.utcnow().isoformat(),  # String, not datetime
    "raw_data": trade_data,
}
# MISSING: pnl field!
```

**Issues:**
1. ❌ Missing `pnl` field (critical for RULE-003)
2. ⚠️ `size` vs `quantity` naming inconsistency
3. ⚠️ `side` is string, not int
4. ⚠️ `timestamp` is string, not datetime

---

### 4.2 POSITION_UPDATED Event

#### Documentation (event-handling.md:226-233)
```python
{
    "symbol": "MNQ",
    "contract_id": "CON.F.US.MNQ.U25",
    "size": 2,
    "unrealized_pnl": 75.00,
    "account_id": 123
}
```

#### Implementation (event_bridge.py:184-196)
```python
{
    "symbol": symbol,
    "contract_id": contract_id,
    "size": size,
    "side": "long" if size > 0 else "short",  # Extra field
    "average_price": avg_price,  # Extra field
    "unrealized_pnl": unrealized_pnl,
    "timestamp": datetime.utcnow().isoformat(),
    "raw_data": position_data,
}
# MISSING: account_id field!
```

**Issues:**
1. ❌ Missing `account_id` field (needed for multi-account support)
2. ➕ Extra `side` field (redundant with signed size)
3. ➕ Extra `average_price` field (good to have, but not documented)

---

### 4.3 QUOTE_UPDATED Event (NEW)

#### Documentation (quote-data-integration.md:132-148)
```python
{
    "symbol": "MNQ",
    "last_price": 21000.25,
    "bid": 21000.00,
    "ask": 21000.50,
    "bid_size": 10,
    "ask_size": 15,
    "mid_price": 21000.25,  # Calculated
    "spread": 0.50,         # Calculated
    "timestamp": datetime(...),
    "age_ms": 50            # Quote age
}
```

#### Implementation
**NOT IMPLEMENTED YET** ⚠️

**Status:** Quote events are documented but not implemented in EventBridge.

---

## 5. Missing Fields in Implementation

### 5.1 Critical Missing Fields

| Field | Event Type | Documented | Implemented | Impact |
|-------|-----------|------------|-------------|--------|
| `pnl` | TRADE_EXECUTED | ✅ Yes | ❌ No | **CRITICAL** - RULE-003 cannot track realized P&L |
| `account_id` | POSITION_UPDATED | ✅ Yes | ❌ No | **HIGH** - Multi-account support broken |
| `account_id` | TRADE_EXECUTED | ✅ Yes | ❌ No | **HIGH** - Cannot associate trades with accounts |

**Immediate Action Required:** Add these fields to EventBridge handlers.

---

### 5.2 Nice-to-Have Missing Fields

| Field | Event Type | Documented | Implemented | Impact |
|-------|-----------|------------|-------------|--------|
| `mid_price` | QUOTE_UPDATED | ✅ Yes | ❌ Not impl | **LOW** - Can calculate from bid/ask |
| `spread` | QUOTE_UPDATED | ✅ Yes | ❌ Not impl | **LOW** - Can calculate from bid/ask |
| `age_ms` | QUOTE_UPDATED | ✅ Yes | ❌ Not impl | **LOW** - Useful for stale detection |

---

## 6. Schema Evolution Timeline

### Original Specs (2025-01-17)
- Used `profitAndLoss` (camelCase, matching TopstepX API)
- Used numeric enums for position type (1=Long, 2=Short)

### Wave 1 Implementation (2025-10-23)
- Switched to `average_price` (snake_case, Pythonic)
- Mixed camelCase from SignalR with snake_case for Python

### Wave 3 Unification (2025-10-25)
- Docs updated with `profit_and_loss` (snake_case)
- Implementation still uses mixed naming

### Current State (2025-10-27)
- **Documentation**: Mostly snake_case, but inconsistent
- **Implementation**: Mixed camelCase (SignalR) and snake_case (Python)
- **Result**: Mismatch between docs and code

---

## 7. Canonical Schema Recommendations

### 7.1 TRADE_EXECUTED Event (Canonical)

```python
@dataclass
class TradeExecutedEvent:
    """Canonical schema for trade execution events."""

    # Identifiers
    trade_id: int
    symbol: str
    account_id: int

    # Trade details
    side: int  # 0=Buy, 1=Sell
    size: int  # Number of contracts
    price: float

    # P&L (CRITICAL)
    realized_pnl: float | None  # None for half-turn trades

    # Metadata
    timestamp: datetime
    raw_data: dict  # Original SignalR data for debugging
```

**Mapping from SignalR:**
```python
{
    "trade_id": trade_data.get("id"),
    "symbol": symbol,
    "account_id": trade_data.get("accountId"),  # ADD THIS
    "side": SIDE_MAP[trade_data.get("side")],  # Map string to int
    "size": trade_data.get("quantity"),
    "price": trade_data.get("price"),
    "realized_pnl": trade_data.get("profitAndLoss"),  # ADD THIS
    "timestamp": datetime.utcnow(),  # datetime object, not string
    "raw_data": trade_data,
}
```

---

### 7.2 POSITION_UPDATED Event (Canonical)

```python
@dataclass
class PositionUpdatedEvent:
    """Canonical schema for position update events."""

    # Identifiers
    contract_id: str
    symbol: str
    account_id: int

    # Position details
    size: int  # Signed: positive=long, negative=short
    average_price: float  # Average entry price

    # P&L
    unrealized_pnl: float
    realized_pnl: float  # Cumulative realized P&L

    # Metadata
    timestamp: datetime
    raw_data: dict
```

**Mapping from SignalR:**
```python
{
    "contract_id": position_data.get("contractId"),
    "symbol": symbol,
    "account_id": position_data.get("accountId"),  # ADD THIS
    "size": position_data.get("size"),
    "average_price": position_data.get("averagePrice"),
    "unrealized_pnl": position_data.get("unrealizedPnl", 0.0),
    "realized_pnl": position_data.get("realizedPnl", 0.0),
    "timestamp": datetime.utcnow(),
    "raw_data": position_data,
}
```

---

### 7.3 ORDER Event (Canonical)

```python
@dataclass
class OrderEvent:
    """Canonical schema for order events."""

    # Identifiers
    order_id: int
    symbol: str
    account_id: int
    contract_id: str

    # Order details
    side: int  # 0=Buy, 1=Sell
    quantity: int
    order_type: int  # 1=Limit, 2=Market, 4=Stop
    status: int  # 1=Pending, 2=Filled, 3=Cancelled, 4=Rejected

    # Prices
    price: float | None  # Limit price
    stop_price: float | None  # Stop price

    # Fill info
    filled_quantity: int

    # Metadata
    timestamp: datetime
    raw_data: dict
```

---

### 7.4 QUOTE_UPDATED Event (Canonical)

```python
@dataclass
class QuoteUpdatedEvent:
    """Canonical schema for quote update events."""

    # Identifiers
    symbol: str

    # Quote data
    last_price: float
    bid: float
    ask: float
    bid_size: int
    ask_size: int

    # Calculated fields
    mid_price: float  # (bid + ask) / 2
    spread: float  # ask - bid

    # Metadata
    timestamp: datetime
    age_ms: int  # Age of quote in milliseconds
```

---

## 8. Update Priorities

### Priority 1: CRITICAL (Fix Immediately)

1. **Add `realized_pnl` to TRADE_EXECUTED events**
   - File: `src/risk_manager/sdk/event_bridge.py`
   - Line: 320-331 (`_on_trade_update`)
   - Map from: `trade_data.get("profitAndLoss")`
   - Blocks: RULE-003 (DailyRealizedLoss)

2. **Add `account_id` to all events**
   - File: `src/risk_manager/sdk/event_bridge.py`
   - Events: TRADE_EXECUTED, POSITION_UPDATED, ORDER events
   - Map from: `trade_data.get("accountId")` or `position_data.get("accountId")`
   - Blocks: Multi-account support

3. **Fix timestamp to use datetime objects**
   - File: `src/risk_manager/sdk/event_bridge.py`
   - Change: `datetime.utcnow().isoformat()` → `datetime.utcnow()`
   - Convert to string only in `RiskEvent.to_dict()`

---

### Priority 2: HIGH (Fix Soon)

4. **Standardize P&L field names**
   - Docs: Update all references to use `realized_pnl` and `unrealized_pnl`
   - Code: Ensure EventBridge uses `realized_pnl` and `unrealized_pnl` (snake_case)
   - Tests: Update all test assertions

5. **Implement QUOTE_UPDATED events**
   - File: `src/risk_manager/sdk/event_bridge.py`
   - Add: `_on_quote_update` handler
   - Subscribe: To SignalR quote events
   - Blocks: RULE-004, RULE-005

6. **Define canonical enums**
   - Create: `src/risk_manager/core/enums.py`
   - Define: OrderSide, OrderType, OrderStatus
   - Use: Throughout codebase

---

### Priority 3: MEDIUM (Fix Eventually)

7. **Standardize `size` vs `quantity`**
   - Convention: Use `size` for positions/trades, `quantity` for orders
   - Update: All documentation and code

8. **Remove redundant `side` field from positions**
   - Positions already have signed `size` (positive=long, negative=short)
   - Remove: `"side": "long" if size > 0 else "short"` from position events

9. **Add calculated fields to QUOTE events**
   - Add: `mid_price`, `spread`, `age_ms`
   - Can be calculated or extracted from SDK

---

## 9. Testing Recommendations

### 9.1 Schema Validation Tests

```python
def test_trade_executed_schema():
    """Verify TRADE_EXECUTED event has all required fields."""
    event = create_trade_event()

    # Required fields
    assert "trade_id" in event.data
    assert "symbol" in event.data
    assert "account_id" in event.data  # CRITICAL
    assert "side" in event.data
    assert "size" in event.data
    assert "price" in event.data
    assert "realized_pnl" in event.data  # CRITICAL
    assert "timestamp" in event.data

    # Type checks
    assert isinstance(event.data["realized_pnl"], (float, type(None)))
    assert isinstance(event.data["timestamp"], datetime)  # Not string!
```

### 9.2 Cross-Document Schema Tests

```python
def test_schema_consistency_across_docs():
    """Verify schemas in docs match implementation."""

    # Load documented schema from spec
    doc_schema = parse_schema_from_markdown("event-handling.md")

    # Load implementation schema
    impl_schema = extract_schema_from_code("event_bridge.py")

    # Compare
    for field, doc_type in doc_schema.items():
        assert field in impl_schema, f"Missing field: {field}"
        assert impl_schema[field] == doc_type, f"Type mismatch: {field}"
```

---

## 10. Migration Plan

### Phase 1: Emergency Fixes (1 day)
1. Add `realized_pnl` to TRADE_EXECUTED events
2. Add `account_id` to all events
3. Fix timestamp to use datetime objects
4. Deploy to dev environment
5. Run integration tests

### Phase 2: Standardization (2 days)
1. Update all documentation with canonical schemas
2. Create enums.py with canonical enum definitions
3. Refactor EventBridge to use canonical schemas
4. Update all tests
5. Deploy to staging

### Phase 3: Quote Integration (3 days)
1. Implement QUOTE_UPDATED events
2. Add throttling and stale detection
3. Integrate with RULE-004 and RULE-005
4. Test unrealized P&L tracking
5. Deploy to production

---

## 11. Document Update Checklist

### Documents Requiring Updates

- [ ] `event-handling.md`
  - [ ] Fix P&L field names (use `realized_pnl`, `unrealized_pnl`)
  - [ ] Fix position side enum (use signed size instead)
  - [ ] Add OrderStatus enum definition
  - [ ] Fix timestamp type (datetime, not string)

- [ ] `sdk-integration.md`
  - [ ] Update Position object schema
  - [ ] Add missing OrderStatus enum
  - [ ] Document realized_pnl in trade events

- [ ] `quote-data-integration.md`
  - [ ] Verify QUOTE_UPDATED schema matches implementation
  - [ ] Add implementation examples

- [ ] `RULE-003-daily-realized-loss.md`
  - [ ] Fix P&L field reference (line 21: `profitAndLoss` → `realized_pnl`)
  - [ ] Update examples to use canonical schema

- [ ] `RULE-004-daily-unrealized-loss.md`
  - [ ] Fix field reference (line 24: `avgPrice` → `average_price`)
  - [ ] Update examples to use canonical schema

---

## 12. Validation Checklist

Use this checklist to verify schema consistency across all documents:

### Event Schemas
- [ ] TRADE_EXECUTED has all required fields
- [ ] POSITION_UPDATED has all required fields
- [ ] ORDER events have all required fields
- [ ] QUOTE_UPDATED schema is documented and implemented
- [ ] All events have `timestamp` as datetime (not string)
- [ ] All events have `account_id` for multi-account support

### Field Names
- [ ] P&L fields use `realized_pnl` and `unrealized_pnl` (snake_case)
- [ ] Position price uses `average_price` (not `entry_price` or `avgPrice`)
- [ ] Positions use signed `size` (not separate `side`/`type` field)
- [ ] Orders use `quantity` (not `size`)
- [ ] Trades use `size` (not `quantity`)

### Enum Values
- [ ] OrderSide enum is defined and used consistently
- [ ] OrderType enum is defined and used consistently
- [ ] OrderStatus enum is defined and used consistently
- [ ] Position side uses signed integers (not enum)

### Data Types
- [ ] All prices are `float`
- [ ] All sizes/quantities are `int`
- [ ] All P&L values are `float | None`
- [ ] All timestamps are `datetime` objects

---

## 13. Appendix: Full Schema Reference

### Complete Event Schema Matrix

| Event Type | Critical Fields | Optional Fields | Missing in Impl |
|------------|----------------|-----------------|-----------------|
| TRADE_EXECUTED | trade_id, symbol, account_id, side, size, price, realized_pnl, timestamp | raw_data | realized_pnl ❌, account_id ❌ |
| POSITION_OPENED | contract_id, symbol, account_id, size, average_price, timestamp | side (redundant) | account_id ❌ |
| POSITION_UPDATED | contract_id, symbol, account_id, size, average_price, unrealized_pnl, timestamp | side (redundant), realized_pnl | account_id ❌ |
| POSITION_CLOSED | contract_id, symbol, account_id, realized_pnl, timestamp | | account_id ❌ |
| ORDER_PLACED | order_id, symbol, account_id, side, quantity, order_type, status, timestamp | price, stop_price | account_id ⚠️ |
| ORDER_FILLED | order_id, symbol, account_id, filled_quantity, timestamp | | account_id ⚠️ |
| ORDER_CANCELLED | order_id, symbol, account_id, timestamp | reason | account_id ⚠️ |
| ORDER_REJECTED | order_id, symbol, account_id, timestamp | reason | account_id ⚠️ |
| QUOTE_UPDATED | symbol, last_price, bid, ask, timestamp | mid_price, spread, age_ms | NOT IMPLEMENTED ❌ |

---

## Conclusion

This audit identified **12 critical inconsistencies** in data schemas across the unified specifications. The most critical issues are:

1. **Missing `realized_pnl` field** in TRADE_EXECUTED events (blocks RULE-003)
2. **Missing `account_id` field** in all events (blocks multi-account support)
3. **Inconsistent P&L field naming** (`pnl` vs `profitAndLoss` vs `profit_and_loss`)
4. **Timestamp type mismatch** (string vs datetime object)
5. **Position side enum confusion** (multiple overlapping conventions)

**Immediate action required** on Priority 1 items to unblock critical features.

---

**Report Status:** Complete
**Next Steps:** Begin Phase 1 emergency fixes (add missing fields)
**Estimated Effort:** 6 days total (1 + 2 + 3)

