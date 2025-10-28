# Code Changes Checklist

**Generated**: 2025-10-27
**Purpose**: Actionable checklist of ALL code changes needed to align implementation with SDK patterns
**Status**: Ready for implementation

---

## Table of Contents

1. [CRITICAL Priority Changes](#critical-priority-changes)
2. [HIGH Priority Changes](#high-priority-changes)
3. [MEDIUM Priority Changes](#medium-priority-changes)
4. [Change Details by File](#change-details-by-file)
5. [Verification Tests](#verification-tests)

---

## Executive Summary

**Total Changes Required**: 48 checkboxes across 15 files
- **CRITICAL**: 12 changes (blocks core functionality)
- **HIGH**: 18 changes (needed for all rules to work)
- **MEDIUM**: 18 changes (correctness and consistency)

**Estimated Effort**: 2-3 days
- Day 1: CRITICAL changes (EventBridge + core events)
- Day 2: HIGH changes (Rules + State)
- Day 3: MEDIUM changes (Tests + Documentation)

---

## CRITICAL Priority Changes

### Section 1: EventBridge Missing Fields (BLOCKS RULE-003, Multi-Account)

**File**: `src/risk_manager/sdk/event_bridge.py`

#### Change 1.1: Add `realized_pnl` to TRADE_EXECUTED Events
**Priority**: CRITICAL (Blocks RULE-003)
**Lines**: 320-331 (`_on_trade_update`)

**Current Code**:
```python
risk_event = RiskEvent(
    event_type=EventType.TRADE_EXECUTED,
    data={
        "symbol": symbol,
        "trade_id": trade_id,
        "side": side,
        "quantity": quantity,
        "price": price,
        "timestamp": datetime.utcnow().isoformat(),
        "raw_data": trade_data,
    }
)
```

**Required Change**:
```python
risk_event = RiskEvent(
    event_type=EventType.TRADE_EXECUTED,
    data={
        "symbol": symbol,
        "trade_id": trade_id,
        "side": side,
        "quantity": quantity,
        "price": price,
        "realized_pnl": trade_data.get("profitAndLoss"),  # ⭐ ADD THIS
        "timestamp": datetime.utcnow(),  # ⭐ datetime object, not string
        "raw_data": trade_data,
    }
)
```

**Why**:
- RULE-003 needs `realized_pnl` to track daily loss
- SDK provides this as `profitAndLoss` (camelCase)
- Will be `None` for half-turn trades (opening positions)

**Test Verification**:
```python
def test_trade_event_has_realized_pnl():
    event = create_trade_executed_event()
    assert "realized_pnl" in event.data
    assert isinstance(event.data["realized_pnl"], (float, type(None)))
```

- [ ] **1.1**: Add `realized_pnl` field to TRADE_EXECUTED events

---

#### Change 1.2: Add `account_id` to TRADE_EXECUTED Events
**Priority**: CRITICAL (Blocks multi-account support)
**Lines**: 320-331 (`_on_trade_update`)

**Required Change**:
```python
"account_id": trade_data.get("accountId"),  # ⭐ ADD THIS
```

**Why**: Multi-account support requires tracking which account each trade belongs to

**Test Verification**:
```python
def test_trade_event_has_account_id():
    event = create_trade_executed_event()
    assert "account_id" in event.data
```

- [ ] **1.2**: Add `account_id` field to TRADE_EXECUTED events

---

#### Change 1.3: Add `account_id` to POSITION Events
**Priority**: CRITICAL (Blocks multi-account support)
**Lines**: 184-196 (`_on_position_update` - POSITION_UPDATED)
**Lines**: 203-212 (`_on_position_update` - POSITION_CLOSED)

**Required Change**:
```python
# In POSITION_UPDATED event (line 184-196)
risk_event = RiskEvent(
    event_type=event_type,
    data={
        "symbol": symbol,
        "contract_id": contract_id,
        "account_id": position_data.get("accountId"),  # ⭐ ADD THIS
        "size": size,
        "side": "long" if size > 0 else "short",
        "average_price": avg_price,
        "unrealized_pnl": unrealized_pnl,
        "timestamp": datetime.utcnow(),  # ⭐ datetime object, not string
        "raw_data": position_data,
    }
)

# In POSITION_CLOSED event (line 203-212)
risk_event = RiskEvent(
    event_type=EventType.POSITION_CLOSED,
    data={
        "symbol": symbol,
        "contract_id": contract_id,
        "account_id": position_data.get("accountId"),  # ⭐ ADD THIS
        "realized_pnl": position_data.get('realizedPnl', 0.0),
        "timestamp": datetime.utcnow(),  # ⭐ datetime object, not string
        "raw_data": position_data,
    }
)
```

- [ ] **1.3**: Add `account_id` to POSITION_UPDATED events
- [ ] **1.4**: Add `account_id` to POSITION_CLOSED events

---

#### Change 1.4: Fix Timestamp Type (datetime, not string)
**Priority**: CRITICAL (Rules expect datetime objects)
**Lines**: 193, 209, 277, 328 (all event handlers)

**Current**:
```python
"timestamp": datetime.utcnow().isoformat()  # Returns string
```

**Required**:
```python
"timestamp": datetime.utcnow()  # Returns datetime object
```

**Why**:
- Documentation specifies datetime objects
- Rules may do datetime arithmetic
- Conversion to string should only happen in `RiskEvent.to_dict()`

**Impact**: All event timestamps

- [ ] **1.5**: Fix POSITION_UPDATED timestamp (line 193)
- [ ] **1.6**: Fix POSITION_CLOSED timestamp (line 209)
- [ ] **1.7**: Fix ORDER event timestamp (line 277)
- [ ] **1.8**: Fix TRADE_EXECUTED timestamp (line 328)

---

#### Change 1.5: Add Missing ORDER_PLACED Fields
**Priority**: CRITICAL (Blocks RULE-008 - Stop Loss Check)
**Lines**: 267-280 (`_on_order_update`)

**Current Code**:
```python
risk_event = RiskEvent(
    event_type=event_type,
    data={
        "symbol": symbol,
        "order_id": order_id,
        "status": status,
        "side": side,
        "quantity": quantity,
        "price": price,
        "filled_quantity": filled_quantity,
        "timestamp": datetime.utcnow().isoformat(),
        "raw_data": order_data,
    }
)
```

**Required Change**:
```python
risk_event = RiskEvent(
    event_type=event_type,
    data={
        "symbol": symbol,
        "order_id": order_id,
        "account_id": order_data.get("accountId"),  # ⭐ ADD THIS
        "contract_id": order_data.get("contractId"),  # ⭐ ADD THIS
        "status": status,
        "side": side,
        "quantity": quantity,
        "order_type": order_data.get("type"),  # ⭐ ADD THIS (1=Market, 2=Limit, 3=Stop)
        "price": price,
        "stop_price": order_data.get("stopPrice"),  # ⭐ ADD THIS (Critical for RULE-008)
        "limit_price": order_data.get("limitPrice"),  # ⭐ ADD THIS
        "filled_quantity": filled_quantity,
        "timestamp": datetime.utcnow(),  # ⭐ datetime object
        "raw_data": order_data,
    }
)
```

**Why**:
- RULE-008 needs `stop_price` to verify stop-loss orders
- RULE-008 needs `order_type` to identify stop orders (type == 3)
- Multi-account needs `account_id`
- Position matching needs `contract_id`

- [ ] **1.9**: Add `account_id` to ORDER events
- [ ] **1.10**: Add `contract_id` to ORDER events
- [ ] **1.11**: Add `order_type` to ORDER events (CRITICAL for RULE-008)
- [ ] **1.12**: Add `stop_price` to ORDER events (CRITICAL for RULE-008)
- [ ] **1.13**: Add `limit_price` to ORDER events

---

### Section 2: EventBridge Missing Event Types

**File**: `src/risk_manager/sdk/event_bridge.py`

#### Change 2.1: Emit POSITION_OPENED Events
**Priority**: CRITICAL (Blocks RULE-008)
**Lines**: 178-199 (`_on_position_update`)

**Current Issue**: Only emits `POSITION_UPDATED`, never `POSITION_OPENED`

**Required Logic**:
```python
# Track previous position sizes to detect opens
self._previous_positions: dict[str, int] = {}  # Add to __init__

async def _on_position_update(self, symbol: str, data: Any) -> None:
    # ... existing code ...

    # Determine event type based on previous state
    position_key = f"{symbol}:{contract_id}"
    previous_size = self._previous_positions.get(position_key, 0)

    if action == 1 and size != 0:
        # Determine if this is OPENED or UPDATED
        if previous_size == 0 and size != 0:
            event_type = EventType.POSITION_OPENED  # ⭐ NEW POSITION
        else:
            event_type = EventType.POSITION_UPDATED  # ⭐ EXISTING POSITION

        # Update tracking
        self._previous_positions[position_key] = size

        # ... emit event ...

    elif action == 2 or (action == 1 and size == 0):
        event_type = EventType.POSITION_CLOSED
        # Clear tracking
        self._previous_positions.pop(position_key, None)
```

**Why**: RULE-008 needs `POSITION_OPENED` to start the stop-loss grace period timer

- [ ] **2.1**: Add position tracking dictionary to `__init__`
- [ ] **2.2**: Implement POSITION_OPENED detection logic
- [ ] **2.3**: Update tracking on POSITION_CLOSED

---

### Section 3: Core Events - Add QUOTE_UPDATE Event Type

**File**: `src/risk_manager/core/events.py`

#### Change 3.1: Add QUOTE_UPDATE Event Type
**Priority**: CRITICAL (Blocks RULE-004, RULE-005, RULE-012)
**Lines**: 9-46 (`EventType` enum)

**Required Change**:
```python
class EventType(str, Enum):
    """Types of risk events."""

    # Position events
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"

    # Order events
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    ORDER_UPDATED = "order_updated"

    # Quote events ⭐ ADD THIS SECTION
    QUOTE_UPDATE = "quote_update"
    NEW_BAR = "new_bar"
    DATA_UPDATE = "data_update"

    # Trade events
    TRADE_EXECUTED = "trade_executed"

    # ... rest of events ...
```

**Why**: RULE-004/005 need real-time price updates to calculate unrealized P&L

- [ ] **3.1**: Add `QUOTE_UPDATE` event type
- [ ] **3.2**: Add `NEW_BAR` event type (optional, for future use)
- [ ] **3.3**: Add `DATA_UPDATE` event type (optional, for future use)

---

### Section 4: EventBridge - Implement QUOTE_UPDATE Handler

**File**: `src/risk_manager/sdk/event_bridge.py`

#### Change 4.1: Add Quote Update Handler
**Priority**: CRITICAL (Blocks RULE-004, RULE-005)
**Lines**: After line 363 (new method)

**Required Code**:
```python
async def _on_quote_update(self, symbol: str, data: Any) -> None:
    """
    Handle quote update from SignalR.

    High-frequency event (every tick). Consider throttling.

    SignalR sends data in format:
    [{'action': 1, 'data': {'last': 21500.0, 'bid': 21499.5, ...}}]
    """
    try:
        if not isinstance(data, list):
            return

        for update in data:
            quote_data = update.get('data', {})

            # Extract quote details
            last_price = quote_data.get('last')
            bid = quote_data.get('bid')
            ask = quote_data.get('ask')

            if last_price is None:
                continue  # Skip invalid quotes

            logger.trace(
                f"📊 Quote update for {symbol}: "
                f"last={last_price:.2f}, bid={bid:.2f}, ask={ask:.2f}"
            )

            risk_event = RiskEvent(
                event_type=EventType.QUOTE_UPDATE,
                data={
                    "symbol": symbol,
                    "last_price": last_price,
                    "bid": bid,
                    "ask": ask,
                    "bid_size": quote_data.get('bidSize', 0),
                    "ask_size": quote_data.get('askSize', 0),
                    "mid_price": (bid + ask) / 2 if bid and ask else None,
                    "spread": ask - bid if bid and ask else None,
                    "timestamp": datetime.utcnow(),
                    "raw_data": quote_data,
                }
            )

            await self.risk_event_bus.publish(risk_event)

    except Exception as e:
        logger.error(f"Error handling quote update for {symbol}: {e}")
```

**Required Subscription** (add to `_subscribe_to_suite`):
```python
# Add after line 134 in _subscribe_to_suite
await realtime_client.add_callback(
    "quote_update",
    lambda data: asyncio.create_task(
        self._on_quote_update(symbol, data)
    )
)
logger.debug(f"✅ Registered callback: quote_update for {symbol}")
```

**Optional: Add Throttling**:
```python
# In __init__, add throttling state
self._last_quote_time: dict[str, datetime] = {}
self._quote_throttle_ms = 100  # Emit max once per 100ms

# In _on_quote_update, add throttle check
now = datetime.utcnow()
last_time = self._last_quote_time.get(symbol)
if last_time and (now - last_time).total_seconds() * 1000 < self._quote_throttle_ms:
    return  # Skip this quote (too soon)
self._last_quote_time[symbol] = now
```

- [ ] **4.1**: Implement `_on_quote_update` handler
- [ ] **4.2**: Subscribe to "quote_update" callback in `_subscribe_to_suite`
- [ ] **4.3**: (Optional) Add quote throttling to prevent event flood

---

## HIGH Priority Changes

### Section 5: Rule Implementations - Fix Event Subscriptions

**Files**: `src/risk_manager/rules/*.py`

#### Change 5.1: RULE-001 - Max Contracts
**File**: `src/risk_manager/rules/max_position.py`
**Priority**: HIGH
**Lines**: 37-42

**Current**:
```python
if event.event_type not in [
    EventType.POSITION_OPENED,
    EventType.POSITION_UPDATED,
    EventType.ORDER_FILLED,
]:
    return None
```

**Required**:
```python
if event.event_type not in [
    EventType.POSITION_OPENED,    # ⭐ Detect new positions
    EventType.POSITION_UPDATED,   # ⭐ Detect size changes
    EventType.POSITION_CLOSED,    # ⭐ Detect position closes
]:
    return None
```

**Why**:
- Should use all 3 position events
- Remove `ORDER_FILLED` (not a position event)
- Aligns with SDK_EVENTS_QUICK_REFERENCE.txt lines 91-93

- [ ] **5.1**: Fix RULE-001 event subscriptions

---

#### Change 5.2: RULE-002 - Max Contracts Per Instrument
**File**: `src/risk_manager/rules/max_contracts_per_instrument.py`
**Priority**: HIGH
**Lines**: Check event subscription (similar to RULE-001)

**Required**: Same pattern as RULE-001 (all 3 position events)

- [ ] **5.2**: Fix RULE-002 event subscriptions

---

#### Change 5.3: RULE-003 - Daily Realized Loss
**File**: `src/risk_manager/rules/daily_loss.py`
**Priority**: HIGH
**Lines**: 29-36

**Current**:
```python
async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict[str, Any] | None:
    if not self.enabled:
        return None

    # Only evaluate on P&L update events
    if event.event_type not in [EventType.PNL_UPDATED, EventType.POSITION_CLOSED]:
        return None

    # Check if daily P&L exceeds limit
    if engine.daily_pnl <= self.limit:
        return {
            "rule": "DailyLossRule",
            "message": f"Daily loss limit exceeded: ${engine.daily_pnl:.2f} (limit: ${self.limit:.2f})",
            "current_loss": engine.daily_pnl,
            "limit": self.limit,
            "action": self.action,
        }

    return None
```

**Required**:
```python
async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict[str, Any] | None:
    if not self.enabled:
        return None

    # Only evaluate on TRADE_EXECUTED events ⭐ CHANGE THIS
    if event.event_type != EventType.TRADE_EXECUTED:
        return None

    # Extract realized P&L from trade event ⭐ ADD THIS
    realized_pnl = event.data.get("realized_pnl")

    # Skip half-turn trades (opening positions) ⭐ ADD THIS
    if realized_pnl is None:
        return None

    # Update daily P&L tracker ⭐ ADD THIS
    # (Note: This should be handled by PnLTracker in state management)
    # For now, get from engine.daily_pnl

    # Check if daily P&L exceeds limit
    if engine.daily_pnl <= self.limit:
        return {
            "rule": "DailyRealizedLossRule",  # ⭐ Rename for clarity
            "message": f"Daily realized loss limit exceeded: ${engine.daily_pnl:.2f} (limit: ${self.limit:.2f})",
            "current_loss": engine.daily_pnl,
            "limit": self.limit,
            "realized_pnl": realized_pnl,  # ⭐ Add context
            "action": self.action,
        }

    return None
```

**Why**:
- Must use `TRADE_EXECUTED` event (has `realized_pnl`)
- Must check for `None` to skip half-turn trades
- Aligns with SDK_EVENTS_QUICK_REFERENCE.txt lines 95-97

- [ ] **5.3**: Change RULE-003 to subscribe to TRADE_EXECUTED
- [ ] **5.4**: Add realized_pnl extraction from event
- [ ] **5.5**: Add null check for half-turn trades

---

#### Change 5.4: RULE-004/005 - Unrealized P&L (NEW IMPLEMENTATION NEEDED)
**Files**: Create `src/risk_manager/rules/daily_unrealized_loss.py` and `max_unrealized_profit.py`
**Priority**: HIGH
**Lines**: N/A (new files)

**Required Implementation** (RULE-004 example):
```python
"""Daily unrealized loss limit rule."""

from typing import TYPE_CHECKING, Any

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine


class DailyUnrealizedLossRule(RiskRule):
    """Enforce maximum daily unrealized loss limit."""

    def __init__(self, limit: float, action: str = "alert"):
        super().__init__(action=action)
        self.limit = limit
        if limit >= 0:
            raise ValueError("Daily unrealized loss limit must be negative")

    async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict[str, Any] | None:
        if not self.enabled:
            return None

        # Subscribe to POSITION events and QUOTE_UPDATE ⭐
        if event.event_type not in [
            EventType.POSITION_OPENED,
            EventType.POSITION_UPDATED,
            EventType.POSITION_CLOSED,
            EventType.QUOTE_UPDATE,
        ]:
            return None

        # Calculate current unrealized P&L across all positions
        # This requires:
        # 1. Position entry price (from POSITION_UPDATED.average_price)
        # 2. Current market price (from QUOTE_UPDATE.last_price)
        # 3. Position size and direction

        total_unrealized_pnl = 0.0

        for symbol, position in engine.current_positions.items():
            # Get position details
            size = position.get("size", 0)
            if size == 0:
                continue  # Skip closed positions

            entry_price = position.get("average_price")

            # Get current market price from quote cache
            current_price = engine.quote_cache.get(symbol, {}).get("last_price")

            if not entry_price or not current_price:
                continue  # Skip if missing data

            # Calculate unrealized P&L
            # (This needs tick_size and tick_value from config)
            # For now, simplified calculation:
            tick_value = 5.0  # TODO: Get from config
            ticks = (current_price - entry_price) * (1 if size > 0 else -1)
            position_pnl = ticks * abs(size) * tick_value

            total_unrealized_pnl += position_pnl

        # Check if unrealized loss exceeds limit
        if total_unrealized_pnl <= self.limit:
            return {
                "rule": "DailyUnrealizedLossRule",
                "message": f"Unrealized loss limit exceeded: ${total_unrealized_pnl:.2f} (limit: ${self.limit:.2f})",
                "current_unrealized_pnl": total_unrealized_pnl,
                "limit": self.limit,
                "action": self.action,
            }

        return None
```

**Why**:
- RULE-004/005 not implemented yet
- Requires QUOTE_UPDATE events
- Requires position tracking + current prices
- Aligns with SDK_EVENTS_QUICK_REFERENCE.txt lines 99-101

- [ ] **5.6**: Create RULE-004 implementation (daily_unrealized_loss.py)
- [ ] **5.7**: Create RULE-005 implementation (max_unrealized_profit.py)
- [ ] **5.8**: Add quote_cache to RiskEngine for current prices

---

#### Change 5.5: RULE-008 - Stop Loss Check (CRITICAL LOGIC FIX)
**File**: Create `src/risk_manager/rules/stop_loss_check.py`
**Priority**: HIGH (Not implemented yet, and spec is WRONG)
**Lines**: N/A (new file)

**Required Implementation**:
```python
"""Stop-loss grace period enforcement rule."""

import asyncio
from typing import TYPE_CHECKING, Any
from datetime import datetime, timedelta

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine


class StopLossCheckRule(RiskRule):
    """
    Enforce stop-loss placement within grace period.

    CORRECT LOGIC:
    1. When POSITION_OPENED fires, start grace period timer
    2. Monitor ORDER_PLACED events for stop-loss orders:
       - Check if order.type == 3 (STOP order)
       - Check if order.stopPrice exists
       - Match order.contractId to position.contractId
    3. If no matching stop-loss found before timer expires, close position
    """

    def __init__(self, grace_period_seconds: int = 30, action: str = "flatten"):
        super().__init__(action=action)
        self.grace_period_seconds = grace_period_seconds
        self._pending_checks: dict[str, asyncio.Task] = {}  # Track active timers

    async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict[str, Any] | None:
        if not self.enabled:
            return None

        # Subscribe to POSITION_OPENED and ORDER_PLACED ⭐
        if event.event_type == EventType.POSITION_OPENED:
            await self._handle_position_opened(event, engine)
        elif event.event_type == EventType.ORDER_PLACED:
            await self._handle_order_placed(event, engine)

        return None

    async def _handle_position_opened(self, event: RiskEvent, engine: "RiskEngine") -> None:
        """Start grace period timer when position opens."""
        contract_id = event.data.get("contract_id")
        symbol = event.data.get("symbol")

        if not contract_id:
            return

        # Start grace period timer
        task = asyncio.create_task(
            self._grace_period_timer(contract_id, symbol, engine)
        )
        self._pending_checks[contract_id] = task

    async def _handle_order_placed(self, event: RiskEvent, engine: "RiskEngine") -> None:
        """Check if this is a stop-loss order for a pending position."""
        order_type = event.data.get("order_type")
        stop_price = event.data.get("stop_price")
        contract_id = event.data.get("contract_id")

        # Check if this is a STOP order (type == 3) ⭐
        if order_type == 3 and stop_price is not None:
            # Valid stop-loss order placed!
            # Cancel the grace period timer for this position
            if contract_id in self._pending_checks:
                self._pending_checks[contract_id].cancel()
                del self._pending_checks[contract_id]

    async def _grace_period_timer(self, contract_id: str, symbol: str, engine: "RiskEngine") -> None:
        """Wait for grace period, then enforce if no stop-loss found."""
        try:
            await asyncio.sleep(self.grace_period_seconds)

            # Timer expired - no stop-loss was placed!
            # Emit violation event to trigger enforcement
            violation_event = RiskEvent(
                event_type=EventType.RULE_VIOLATED,
                data={
                    "rule": "StopLossCheckRule",
                    "message": f"No stop-loss placed within {self.grace_period_seconds}s for {symbol}",
                    "contract_id": contract_id,
                    "symbol": symbol,
                    "action": self.action,
                }
            )

            await engine.event_bus.publish(violation_event)

        except asyncio.CancelledError:
            # Timer was cancelled (stop-loss was placed in time)
            pass
        finally:
            # Clean up
            self._pending_checks.pop(contract_id, None)
```

**Why**:
- RULE-008 spec is WRONG (uses ORDER_PLACED, but needs POSITION_OPENED + ORDER_PLACED)
- Must check `order_type == 3` to identify stop orders
- Must check `stop_price` exists
- Aligns with SDK_EVENTS_QUICK_REFERENCE.txt lines 103-105

- [ ] **5.9**: Create RULE-008 implementation (stop_loss_check.py)
- [ ] **5.10**: Implement timer-based grace period logic
- [ ] **5.11**: Add stop-loss detection (order_type == 3)

---

### Section 6: State Management - Update Trackers

**Files**: `src/risk_manager/state/*.py`

#### Change 6.1: PnLTracker - Add Realized P&L Tracking
**File**: `src/risk_manager/state/pnl_tracker.py`
**Priority**: HIGH
**Lines**: Need to see current implementation

**Required**:
- Subscribe to TRADE_EXECUTED events
- Extract `realized_pnl` from event.data
- Skip if `realized_pnl is None` (half-turn trades)
- Accumulate daily realized P&L
- Reset at day boundary

- [ ] **6.1**: Update PnLTracker to use TRADE_EXECUTED events
- [ ] **6.2**: Add realized_pnl extraction
- [ ] **6.3**: Add null check for half-turn trades

---

#### Change 6.2: PositionTracker - Handle All 3 Position Events
**File**: `src/risk_manager/state/position_tracker.py`
**Priority**: HIGH

**Required**:
- Handle POSITION_OPENED (add new position)
- Handle POSITION_UPDATED (update existing position)
- Handle POSITION_CLOSED (remove position)

- [ ] **6.4**: Add POSITION_OPENED handler
- [ ] **6.5**: Add POSITION_CLOSED handler
- [ ] **6.6**: Update POSITION_UPDATED handler

---

#### Change 6.3: OrderTracker - Add Stop Price Tracking
**File**: `src/risk_manager/state/order_tracker.py`
**Priority**: HIGH

**Required**:
- Track `stop_price` from ORDER_PLACED events
- Track `order_type` to identify stop orders
- Store stop-loss orders separately for RULE-008 lookup

- [ ] **6.7**: Add stop_price field to order tracking
- [ ] **6.8**: Add order_type field to order tracking
- [ ] **6.9**: Create stop_loss_orders lookup dict

---

### Section 7: RiskEngine - Add Quote Cache

**File**: `src/risk_manager/core/engine.py`
**Priority**: HIGH

#### Change 7.1: Add Quote Cache for Current Prices
**Lines**: Check __init__ and event handlers

**Required**:
```python
# In __init__
self.quote_cache: dict[str, dict] = {}  # symbol -> latest quote

# Add handler for QUOTE_UPDATE events
async def _handle_quote_update(self, event: RiskEvent) -> None:
    """Update quote cache with latest prices."""
    symbol = event.data.get("symbol")
    if symbol:
        self.quote_cache[symbol] = event.data
```

**Subscribe to QUOTE_UPDATE**:
```python
# In start() or _setup_event_handlers()
self.event_bus.subscribe(EventType.QUOTE_UPDATE, self._handle_quote_update)
```

**Why**: RULE-004/005 need current market prices to calculate unrealized P&L

- [ ] **7.1**: Add quote_cache to RiskEngine
- [ ] **7.2**: Subscribe to QUOTE_UPDATE events
- [ ] **7.3**: Implement quote cache update handler

---

## MEDIUM Priority Changes

### Section 8: Field Name Standardization

**Files**: Multiple

#### Change 8.1: Standardize P&L Field Names
**Priority**: MEDIUM
**Impact**: Consistency across codebase

**Pattern**:
- `realized_pnl` (not `pnl`, `profitAndLoss`, `profit_and_loss`)
- `unrealized_pnl` (not `unrealizedPnl`)

**Files to Update**:
- All event handlers (event_bridge.py)
- All rule implementations
- All state trackers
- All test fixtures

- [ ] **8.1**: Audit all uses of P&L fields
- [ ] **8.2**: Replace with canonical names

---

#### Change 8.2: Standardize Price Field Names
**Priority**: MEDIUM

**Pattern**:
- `average_price` (not `entry_price`, `avgPrice`, `averagePrice`)

**Files to Update**:
- event_bridge.py (already correct)
- Rule specs documentation (RULE-004/005)

- [ ] **8.3**: Audit all uses of price fields
- [ ] **8.4**: Replace with canonical names

---

#### Change 8.3: Remove Redundant "side" Field from Positions
**Priority**: MEDIUM
**File**: `src/risk_manager/sdk/event_bridge.py`
**Lines**: 190

**Current**:
```python
"side": "long" if size > 0 else "short",  # Redundant!
```

**Why Remove**:
- Position `size` is already signed (positive = long, negative = short)
- Redundant data increases confusion
- SDK uses signed integers, we should too

**Impact**: Low (no rules currently use "side" field)

- [ ] **8.5**: Remove "side" field from POSITION_UPDATED events
- [ ] **8.6**: Update any rules that check position["side"] to use size > 0

---

### Section 9: Test Fixture Updates

**Files**: `tests/fixtures/*.py`

#### Change 9.1: Update Test Fixtures with Correct Field Names
**Priority**: MEDIUM
**Impact**: Tests will fail until fixtures match implementation

**Required Updates**:
- Add `realized_pnl` to TRADE_EXECUTED fixtures
- Add `account_id` to all event fixtures
- Fix timestamp to use datetime objects (not strings)
- Add `stop_price`, `order_type` to ORDER_PLACED fixtures
- Add `average_price` (not `avgPrice`) to POSITION fixtures

- [ ] **9.1**: Update TRADE_EXECUTED fixtures
- [ ] **9.2**: Update POSITION fixtures
- [ ] **9.3**: Update ORDER fixtures
- [ ] **9.4**: Update all timestamp fixtures

---

### Section 10: Integration Test Updates

**Files**: `tests/integration/*.py`

#### Change 10.1: Fix Event Subscription Patterns in Tests
**Priority**: MEDIUM

**Current Issue**: Tests may use old patterns (suite.on)

**Required Pattern**:
```python
# CORRECT: Direct realtime callback
await suite.realtime.add_callback("position_update", handler)

# WRONG: SDK EventBus (doesn't work for position events)
suite.on("position_update", handler)
```

- [ ] **10.1**: Audit all integration tests for event subscription
- [ ] **10.2**: Replace suite.on with realtime.add_callback

---

### Section 11: Configuration Updates

**Files**: `config/*.yaml`

#### Change 11.1: Add Tick Size/Value Configuration
**Priority**: MEDIUM
**File**: Create `config/instruments.yaml`

**Required**:
```yaml
# Instrument-specific configuration
instruments:
  MNQ:
    tick_size: 0.25
    tick_value: 0.50
    symbol: "MNQ"
    description: "Micro E-Mini NASDAQ-100"

  MES:
    tick_size: 0.25
    tick_value: 1.25
    symbol: "MES"
    description: "Micro E-Mini S&P 500"
```

**Why**: RULE-004/005 need tick values to calculate P&L correctly

- [ ] **11.1**: Create instruments.yaml configuration
- [ ] **11.2**: Add loader in config module
- [ ] **11.3**: Integrate with RULE-004/005

---

#### Change 11.2: Add Event Configuration
**Priority**: MEDIUM
**File**: Create `config/events_config.yaml`

**Required**:
```yaml
# Event handling configuration
events:
  quote_throttle_ms: 100  # Emit max once per 100ms

  subscriptions:
    position_events:
      - POSITION_OPENED
      - POSITION_UPDATED
      - POSITION_CLOSED

    order_events:
      - ORDER_PLACED
      - ORDER_FILLED
      - ORDER_CANCELLED
      - ORDER_REJECTED

    trade_events:
      - TRADE_EXECUTED

    quote_events:
      - QUOTE_UPDATE
```

- [ ] **11.4**: Create events_config.yaml
- [ ] **11.5**: Integrate with EventBridge

---

### Section 12: Documentation Updates

**Files**: `docs/specifications/unified/rules/*.md`

#### Change 12.1: Fix RULE-008 Specification
**Priority**: MEDIUM (but CRITICAL fix to spec itself)
**File**: `docs/specifications/unified/rules/RULE-008-no-stop-loss-grace.md`
**Lines**: 14-17, 35

**Current (WRONG)**:
```markdown
### Trigger Condition
**Events**: `EventType.ORDER_PLACED` (when position opens)
```

**Required (CORRECT)**:
```markdown
### Trigger Condition
**Events**:
1. `EventType.POSITION_OPENED` - Detect when position opens
2. `EventType.ORDER_PLACED` - Detect when stop-loss is placed

**Logic**:
1. When POSITION_OPENED fires, start grace period timer
2. Monitor ORDER_PLACED events for stop-loss order:
   - Check if `order.type == 3` (STOP order)
   - Check if `order.stopPrice` exists
   - Match `order.contractId` to position's contractId
3. If no matching stop-loss found before timer expires, close position
```

- [ ] **12.1**: Rewrite RULE-008 trigger condition
- [ ] **12.2**: Add stop-loss detection logic details
- [ ] **12.3**: Add data field requirements

---

#### Change 12.2: Fix RULE-004/005 Field Names
**Priority**: MEDIUM
**Files**:
- `docs/specifications/unified/rules/RULE-004-daily-unrealized-loss.md`
- `docs/specifications/unified/rules/RULE-005-max-unrealized-profit.md`
**Lines**: 24, 124-125

**Current**: `avgPrice` (line 24)
**Required**: `average_price`

**Current**: Only lists POSITION_UPDATED (line 124/125)
**Required**: List all 3 position events + QUOTE_UPDATE

- [ ] **12.4**: Fix RULE-004 field names
- [ ] **12.5**: Fix RULE-004 event subscriptions
- [ ] **12.6**: Fix RULE-005 field names
- [ ] **12.7**: Fix RULE-005 event subscriptions

---

#### Change 12.3: Add QUOTE_UPDATE to RULE-012
**Priority**: MEDIUM
**File**: `docs/specifications/unified/rules/RULE-012-trade-management.md`
**Lines**: 17, 44-45

**Required**: Add explicit QUOTE_UPDATE event reference

- [ ] **12.8**: Add QUOTE_UPDATE to RULE-012 events

---

## Change Details by File

### File: `src/risk_manager/sdk/event_bridge.py`

**Total Changes**: 18
- Lines 100-134: Add QUOTE_UPDATE subscription
- Lines 167-220: Add POSITION_OPENED detection
- Lines 184-196: Add account_id, fix timestamp (POSITION_UPDATED)
- Lines 203-212: Add account_id, fix timestamp (POSITION_CLOSED)
- Lines 267-280: Add order_type, stop_price, account_id, contract_id, fix timestamp
- Lines 320-331: Add realized_pnl, account_id, fix timestamp
- After line 363: Add _on_quote_update handler

**Priority**: CRITICAL (12 changes) + HIGH (6 changes)

---

### File: `src/risk_manager/core/events.py`

**Total Changes**: 3
- Lines 9-46: Add QUOTE_UPDATE, NEW_BAR, DATA_UPDATE event types

**Priority**: CRITICAL

---

### File: `src/risk_manager/rules/max_position.py`

**Total Changes**: 1
- Lines 37-42: Fix event subscriptions (remove ORDER_FILLED, add POSITION_CLOSED)

**Priority**: HIGH

---

### File: `src/risk_manager/rules/daily_loss.py`

**Total Changes**: 3
- Lines 29-36: Change to TRADE_EXECUTED event
- Add realized_pnl extraction
- Add null check for half-turn trades

**Priority**: HIGH

---

### File: `src/risk_manager/rules/daily_unrealized_loss.py` (NEW)

**Total Changes**: 1 (new file)
- Implement RULE-004 with QUOTE_UPDATE support

**Priority**: HIGH

---

### File: `src/risk_manager/rules/stop_loss_check.py` (NEW)

**Total Changes**: 1 (new file)
- Implement RULE-008 with correct logic (POSITION_OPENED + ORDER_PLACED)

**Priority**: HIGH

---

### File: `src/risk_manager/core/engine.py`

**Total Changes**: 3
- Add quote_cache dictionary
- Subscribe to QUOTE_UPDATE events
- Implement quote cache update handler

**Priority**: HIGH

---

### File: `src/risk_manager/state/pnl_tracker.py`

**Total Changes**: 3
- Subscribe to TRADE_EXECUTED
- Extract realized_pnl
- Add null check

**Priority**: HIGH

---

### File: `src/risk_manager/state/position_tracker.py`

**Total Changes**: 3
- Add POSITION_OPENED handler
- Add POSITION_CLOSED handler
- Update POSITION_UPDATED handler

**Priority**: HIGH

---

### File: `src/risk_manager/state/order_tracker.py`

**Total Changes**: 3
- Add stop_price tracking
- Add order_type tracking
- Create stop_loss_orders lookup

**Priority**: HIGH

---

### Files: `tests/fixtures/*.py`

**Total Changes**: 4
- Update TRADE_EXECUTED fixtures
- Update POSITION fixtures
- Update ORDER fixtures
- Fix all timestamps

**Priority**: MEDIUM

---

### Files: `docs/specifications/unified/rules/RULE-*.md`

**Total Changes**: 6
- Fix RULE-008 (complete rewrite)
- Fix RULE-004 field names + events
- Fix RULE-005 field names + events

**Priority**: MEDIUM

---

## Verification Tests

### Test 1: EventBridge Field Presence
```python
def test_trade_event_has_all_fields():
    """Verify TRADE_EXECUTED has all required fields."""
    event = create_trade_executed_event()

    required_fields = [
        "trade_id", "symbol", "account_id", "side",
        "quantity", "price", "realized_pnl", "timestamp"
    ]

    for field in required_fields:
        assert field in event.data, f"Missing field: {field}"

    # Type checks
    assert isinstance(event.data["realized_pnl"], (float, type(None)))
    assert isinstance(event.data["timestamp"], datetime)
```

### Test 2: POSITION_OPENED Detection
```python
async def test_position_opened_event_emitted():
    """Verify POSITION_OPENED fires on new positions."""
    bridge = EventBridge(suite_manager, event_bus)

    # Simulate position opening
    await bridge._on_position_update("MNQ", [
        {"action": 1, "data": {"contractId": "123", "size": 1, "averagePrice": 21000.0}}
    ])

    # Should emit POSITION_OPENED (not POSITION_UPDATED)
    events = await event_bus.get_events()
    assert len(events) == 1
    assert events[0].event_type == EventType.POSITION_OPENED
```

### Test 3: Stop-Loss Detection
```python
async def test_stop_loss_detected():
    """Verify RULE-008 detects stop-loss orders."""
    rule = StopLossCheckRule(grace_period_seconds=2)

    # Position opens
    position_event = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        data={"contract_id": "123", "symbol": "MNQ"}
    )
    await rule.evaluate(position_event, engine)

    # Stop-loss placed (order_type == 3)
    order_event = RiskEvent(
        event_type=EventType.ORDER_PLACED,
        data={
            "contract_id": "123",
            "order_type": 3,  # STOP order
            "stop_price": 20990.0
        }
    )
    await rule.evaluate(order_event, engine)

    # Wait past grace period
    await asyncio.sleep(3)

    # No violation should be emitted (stop-loss was placed in time)
    violations = await engine.event_bus.get_events_of_type(EventType.RULE_VIOLATED)
    assert len(violations) == 0
```

### Test 4: Realized P&L Null Check
```python
def test_realized_pnl_null_for_half_turns():
    """Verify half-turn trades have null realized_pnl."""
    # Opening trade (half-turn)
    event = create_trade_executed_event(
        trade_data={"profitAndLoss": None}  # SDK returns null for opening trades
    )

    assert event.data["realized_pnl"] is None

    # RULE-003 should skip this trade
    rule = DailyRealizedLossRule(limit=-1000.0)
    result = await rule.evaluate(event, engine)
    assert result is None  # Should not evaluate
```

### Test 5: Quote Cache Updates
```python
async def test_quote_cache_updates():
    """Verify quote cache updates on QUOTE_UPDATE events."""
    engine = RiskEngine()

    quote_event = RiskEvent(
        event_type=EventType.QUOTE_UPDATE,
        data={"symbol": "MNQ", "last_price": 21500.0}
    )

    await engine._handle_quote_update(quote_event)

    assert "MNQ" in engine.quote_cache
    assert engine.quote_cache["MNQ"]["last_price"] == 21500.0
```

---

## Implementation Order

### Phase 1: CRITICAL Changes (Day 1)
1. ✅ Add missing event fields (EventBridge)
   - realized_pnl, account_id, timestamps
2. ✅ Add QUOTE_UPDATE event type
3. ✅ Implement POSITION_OPENED detection
4. ✅ Add QUOTE_UPDATE handler
5. ✅ Run smoke test to verify events flow

### Phase 2: HIGH Changes (Day 2)
1. ✅ Fix RULE-001/002 event subscriptions
2. ✅ Fix RULE-003 to use TRADE_EXECUTED
3. ✅ Implement RULE-004/005 (unrealized P&L)
4. ✅ Implement RULE-008 (stop-loss check)
5. ✅ Update state trackers
6. ✅ Add quote cache to engine
7. ✅ Run integration tests

### Phase 3: MEDIUM Changes (Day 3)
1. ✅ Update test fixtures
2. ✅ Fix documentation specs
3. ✅ Add instrument configuration
4. ✅ Standardize field names
5. ✅ Final smoke test + full test suite

---

## Progress Tracking

See `IMPLEMENTATION_PROGRESS_TRACKER.md` for detailed progress tracking.

**Total Checkboxes**: 48
**Completed**: 0
**In Progress**: 0
**Blocked**: 0

---

## Summary

This checklist provides **actionable, line-by-line changes** to align the codebase with SDK event patterns.

**Key Takeaways**:
1. **EventBridge is missing critical fields** (realized_pnl, account_id)
2. **Rules are subscribing to wrong events** (RULE-003 uses PNL_UPDATED instead of TRADE_EXECUTED)
3. **RULE-008 spec is fundamentally wrong** (needs complete rewrite)
4. **QUOTE_UPDATE events are missing** (blocks RULE-004/005)
5. **POSITION_OPENED events never fire** (EventBridge only emits POSITION_UPDATED)

**Fix these 48 items, and the system will be fully aligned with SDK patterns.**

---

**End of Checklist**
