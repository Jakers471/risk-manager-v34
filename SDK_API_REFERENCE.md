# Project-X-Py SDK - API Reference for Risk Manager

**Purpose**: This document maps the actual SDK APIs to prevent test/code mismatches

**SDK Version**: 3.5.8
**Documentation**: https://texascoding.github.io/project-x-py/
**Repository**: https://github.com/TexasCoding/project-x-py

---

## 🔑 Key Finding: We Define Our Own Events!

**IMPORTANT**: The Project-X-Py SDK does NOT have a `RiskEvent` class - we define our own!

```python
# SDK provides:
from project_x_py import EventType  # ← SDK's event types

# WE define:
from risk_manager.core.events import RiskEvent  # ← Our custom event class
from risk_manager.core.events import EventType  # ← Our risk-specific event types
```

---

## 📊 SDK EventType Enum (What the SDK Provides)

**Location**: `project_x_py.EventType`

**All Available Values**:

```python
from project_x_py import EventType

# Connection Events
EventType.CONNECTED
EventType.DISCONNECTED
EventType.AUTHENTICATED
EventType.RECONNECTING

# Order Events
EventType.ORDER_PLACED
EventType.ORDER_FILLED
EventType.ORDER_PARTIAL_FILL
EventType.ORDER_CANCELLED
EventType.ORDER_MODIFIED
EventType.ORDER_REJECTED
EventType.ORDER_EXPIRED

# Position Events
EventType.POSITION_OPENED
EventType.POSITION_CLOSED
EventType.POSITION_UPDATED
EventType.POSITION_PNL_UPDATE

# Market Data Events
EventType.NEW_BAR
EventType.QUOTE_UPDATE
EventType.TRADE_TICK
EventType.ORDERBOOK_UPDATE
EventType.MARKET_DEPTH_UPDATE
EventType.DATA_UPDATE

# Risk Events (SDK's Built-in)
EventType.RISK_LIMIT_EXCEEDED
EventType.RISK_LIMIT_WARNING
EventType.STOP_LOSS_TRIGGERED
EventType.TAKE_PROFIT_TRIGGERED

# System Events
EventType.ERROR
EventType.WARNING
EventType.LATENCY_WARNING
EventType.MEMORY_WARNING
EventType.RATE_LIMIT_WARNING
```

**What's MISSING from SDK** (we add these):
- ❌ `TRADE_EXECUTED` (not in SDK!)
- ❌ `ORDER_UPDATED` (SDK has `ORDER_MODIFIED`)

---

## 🎯 Our RiskEvent Class (What We Define)

**Location**: `src/risk_manager/core/events.py`

**Actual Constructor Signature**:

```python
@dataclass
class RiskEvent:
    event_type: EventType  # ← NOTE: "event_type", NOT "type"!
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)
    source: str = "risk_manager"
    severity: str = "info"  # info, warning, error, critical
```

**Correct Usage**:

```python
# ✅ CORRECT
event = RiskEvent(
    event_type=EventType.POSITION_UPDATED,  # ← "event_type"
    data={"symbol": "MNQ", "size": 2}
)

# ❌ WRONG (test code does this!)
event = RiskEvent(
    type=EventType.POSITION_UPDATED,  # ← "type" is WRONG!
    data={}
)
```

---

## 🎯 Our EventType Enum (What We Define)

**Location**: `src/risk_manager/core/events.py`

**Our Risk-Specific Event Types**:

```python
from risk_manager.core.events import EventType

# Position Events
EventType.POSITION_OPENED      # ✅ Matches SDK
EventType.POSITION_CLOSED      # ✅ Matches SDK
EventType.POSITION_UPDATED     # ✅ Matches SDK

# Order Events
EventType.ORDER_PLACED         # ✅ Matches SDK
EventType.ORDER_FILLED         # ✅ Matches SDK
EventType.ORDER_CANCELLED      # ✅ Matches SDK
EventType.ORDER_REJECTED       # ✅ Matches SDK

# Risk Events (Our Custom)
EventType.RULE_VIOLATED        # ⭐ Custom
EventType.RULE_WARNING         # ⭐ Custom
EventType.ENFORCEMENT_ACTION   # ⭐ Custom

# P&L Events (Our Custom)
EventType.PNL_UPDATED          # ⭐ Custom
EventType.DAILY_LOSS_LIMIT     # ⭐ Custom
EventType.DRAWDOWN_ALERT       # ⭐ Custom

# System Events (Our Custom)
EventType.SYSTEM_STARTED       # ⭐ Custom
EventType.SYSTEM_STOPPED       # ⭐ Custom
EventType.CONNECTION_LOST      # ⭐ Custom
EventType.CONNECTION_RESTORED  # ⭐ Custom

# AI Events (Our Custom)
EventType.PATTERN_DETECTED     # ⭐ Custom
EventType.ANOMALY_DETECTED     # ⭐ Custom
EventType.AI_ALERT             # ⭐ Custom
```

**What's MISSING** (tests expect but we don't have):
- ❌ `TRADE_EXECUTED` (tests expect this!)
- ❌ `ORDER_UPDATED` (tests expect this, we have `ORDER_FILLED`)

---

## 🔧 SDK PositionManager API

**Access**: `suite.positions` or `suite['SYMBOL'].positions`

```python
# Get all positions
positions = await suite.positions.get_all_positions()

# Close all positions
await suite.positions.close_all_positions()

# Close specific position
await suite.positions.close_position_by_contract(contract_id)

# Partially close
await suite.positions.partially_close_position(contract_id, size)

# Get P&L
pnl = await suite.positions.calculate_portfolio_pnl()
position_pnl = await suite.positions.calculate_position_pnl(contract_id)

# Get stats
stats = await suite.positions.get_position_stats()
```

---

## 🔧 SDK OrderManager API

**Access**: `suite.orders` or `suite['SYMBOL'].orders`

```python
# Cancel all orders
await suite.orders.cancel_all_orders()

# Cancel specific order
await suite.orders.cancel_order(order_id)

# Cancel orders for position
await suite.orders.cancel_position_orders(contract_id)

# Place market order
await suite.orders.place_market_order(contract_id, side, size)

# Place limit order
await suite.orders.place_limit_order(contract_id, side, size, price)
```

---

## 📦 Our PnLTracker API (What We Implemented)

**Location**: `src/risk_manager/state/pnl_tracker.py`

Let me check the actual signature:

```python
# Need to verify actual constructor - tests expect:
PnLTracker(account_id="TEST-001")

# But implementation might be:
PnLTracker()  # No parameters

# Or:
PnLTracker(db_path="...")
```

**ACTION NEEDED**: Check actual PnLTracker implementation to document correct API.

---

## 🎯 Test Fixes Required

### Fix #1: RiskEvent Parameter Name

**Find and replace in ALL test files**:

```python
# OLD (WRONG)
RiskEvent(type=EventType.POSITION_UPDATED, data={})

# NEW (CORRECT)
RiskEvent(event_type=EventType.POSITION_UPDATED, data={})
#         ^^^^^^^^^^
```

**Files to fix**:
- `tests/unit/test_core/test_events.py` (6 occurrences)
- `tests/runtime/test_smoke.py` (1 occurrence)

---

### Fix #2: Add Missing EventType Values

**Option A**: Add to our EventType enum

```python
# In src/risk_manager/core/events.py
class EventType(str, Enum):
    # ... existing ...

    # Add these for test compatibility:
    TRADE_EXECUTED = "trade_executed"  # ← ADD
    ORDER_UPDATED = "order_updated"    # ← ADD (or use ORDER_FILLED)
```

**Option B**: Change tests to use existing values

```python
# In tests, change:
EventType.TRADE_EXECUTED
# To:
EventType.ORDER_FILLED  # Or POSITION_UPDATED depending on context

# Change:
EventType.ORDER_UPDATED
# To:
EventType.ORDER_FILLED  # Existing value
```

---

### Fix #3: PnLTracker Constructor

**Check actual implementation**:

```bash
grep -A 5 "class PnLTracker" src/risk_manager/state/pnl_tracker.py
grep -A 10 "def __init__" src/risk_manager/state/pnl_tracker.py
```

**Then update tests** to match actual signature.

---

## 📚 SDK Documentation Links

**Official Docs**: https://texascoding.github.io/project-x-py/
**GitHub**: https://github.com/TexasCoding/project-x-py
**Issues**: https://github.com/TexasCoding/project-x-py/issues

**Quick Reference**:
- EventType: Check SDK source for all values
- TradingSuite: Main entry point (`await TradingSuite.create()`)
- PositionManager: `suite.positions.*`
- OrderManager: `suite.orders.*`

---

## 🎯 Summary: Test vs Code Mismatches

| Test Expects | Actual Code | Fix Required |
|--------------|-------------|--------------|
| `RiskEvent(type=...)` | `RiskEvent(event_type=...)` | Rename parameter in tests |
| `EventType.TRADE_EXECUTED` | Not defined | Add to enum or use `ORDER_FILLED` |
| `EventType.ORDER_UPDATED` | Not defined | Add to enum or use `ORDER_FILLED` |
| `PnLTracker(account_id=...)` | `PnLTracker()` (?) | Check actual signature |
| `RiskRule(name=..., engine=...)` | `RiskRule()` (?) | Check actual signature |

---

## ✅ Recommended Workflow

**Before writing tests**:

1. Check actual implementation:
   ```python
   from risk_manager.core.events import RiskEvent, EventType
   import inspect

   # See actual signature
   print(inspect.signature(RiskEvent.__init__))

   # See actual enum values
   print([e.name for e in EventType])
   ```

2. Use the actual API in tests (not assumed API)

3. Run tests frequently to catch mismatches early

---

**Last Updated**: 2025-10-24
**SDK Version**: 3.5.8
**Status**: Reference document for preventing test/code mismatches
