# Event Handling Specification

**Document ID:** UNIFIED-SDK-002
**Created:** 2025-10-25
**Status:** Complete - Event-Driven Architecture
**Dependencies:** SDK Integration (UNIFIED-SDK-001)

---

## Executive Summary

Risk Manager V34 uses **event-driven architecture** where all risk rule evaluations are triggered by real-time events from the SDK. Events flow from TopstepX platform → SDK → Event Bridge → Risk Engine → Risk Rules.

### Event Flow Overview

```
┌──────────────────────────────────────────────────────────────┐
│  TopstepX Platform                                          │
│  - Trader executes order                                    │
│  - Position opened/closed                                   │
│  - Market data updates                                      │
└────────────────────────┬─────────────────────────────────────┘
                         │ SignalR WebSocket
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  Project-X-Py SDK                                           │
│  - RealtimeDataManager receives SignalR events              │
│  - Publishes to SDK EventBus                                │
└────────────────────────┬─────────────────────────────────────┘
                         │ SDK Event (e.g., ORDER_FILLED)
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  EventBridge (src/risk_manager/sdk/event_bridge.py)        │
│  - Subscribes to SDK events                                 │
│  - Converts SDK events → RiskEvents                         │
└────────────────────────┬─────────────────────────────────────┘
                         │ RiskEvent
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  Risk EventBus (src/risk_manager/core/events.py)           │
│  - Pub/sub system for risk events                          │
└────────────────────────┬─────────────────────────────────────┘
                         │ RiskEvent published
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  RiskEngine (src/risk_manager/core/engine.py)              │
│  - Receives event                                           │
│  - Routes to all registered rules                           │
│  - Checkpoint 6: "Event received"                          │
└────────────────────────┬─────────────────────────────────────┘
                         │ For each rule
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  Risk Rules (src/risk_manager/rules/*.py)                  │
│  - Evaluate event against rule conditions                   │
│  - Return violation if limit exceeded                       │
│  - Checkpoint 7: "Rule evaluated"                          │
└────────────────────────┬─────────────────────────────────────┘
                         │ Violation detected
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  RiskEngine._handle_violation()                            │
│  - Execute enforcement action                               │
│  - Checkpoint 8: "Enforcement triggered"                   │
└────────────────────────┬─────────────────────────────────────┘
                         │ Flatten command
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  TradingIntegration (src/risk_manager/integrations)        │
│  - Call SDK to close positions                              │
│  - Platform executes orders                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 1. Event Types

### 1.1 SDK Event Types

**From Project-X-Py SDK:**

```python
from project_x_py import EventType as SDKEventType

# Connection Events
EventType.CONNECTED                # Connected to platform
EventType.DISCONNECTED             # Disconnected from platform
EventType.AUTHENTICATED            # Successfully authenticated
EventType.RECONNECTING             # Attempting reconnect

# Order Events
EventType.ORDER_PLACED             # Order submitted to platform
EventType.ORDER_FILLED             # Order completely filled
EventType.ORDER_PARTIAL_FILL       # Order partially filled
EventType.ORDER_CANCELLED          # Order cancelled
EventType.ORDER_MODIFIED           # Order modified
EventType.ORDER_REJECTED           # Order rejected by platform
EventType.ORDER_EXPIRED            # Order expired

# Position Events
EventType.POSITION_OPENED          # New position opened
EventType.POSITION_CLOSED          # Position closed
EventType.POSITION_UPDATED         # Position size/price changed
EventType.POSITION_PNL_UPDATE      # P&L updated

# Market Data Events
EventType.NEW_BAR                  # New OHLCV bar
EventType.QUOTE_UPDATE             # Bid/Ask update ⭐ NEW
EventType.TRADE_TICK               # Market trade
EventType.ORDERBOOK_UPDATE         # Level 2 depth update

# System Events
EventType.ERROR                    # Error occurred
EventType.WARNING                  # Warning condition
EventType.LATENCY_WARNING          # High latency detected
```

---

### 1.2 Risk Event Types

**Defined in Risk Manager:**

```python
from risk_manager.core.events import EventType

# Position Events (mapped from SDK)
EventType.POSITION_OPENED             # New position opened
EventType.POSITION_CLOSED             # Position closed
EventType.POSITION_UPDATED            # Position changed

# Order Events (mapped from SDK)
EventType.ORDER_PLACED                # Order submitted
EventType.ORDER_FILLED                # Order filled
EventType.ORDER_CANCELLED             # Order cancelled
EventType.ORDER_REJECTED              # Order rejected
EventType.ORDER_UPDATED               # Order modified

# Trade Events (mapped from SDK)
EventType.TRADE_EXECUTED              # Trade executed

# Risk Events (generated by Risk Manager)
EventType.RULE_VIOLATED               # Risk rule violated
EventType.RULE_WARNING                # Risk rule warning
EventType.ENFORCEMENT_ACTION          # Enforcement action taken

# P&L Events (generated by Risk Manager)
EventType.PNL_UPDATED                 # P&L updated
EventType.DAILY_LOSS_LIMIT            # Daily loss limit hit
EventType.DRAWDOWN_ALERT              # Drawdown alert
EventType.QUOTE_UPDATED ⭐ NEW        # Quote updated (for unrealized P&L)

# System Events
EventType.SYSTEM_STARTED              # System started
EventType.SYSTEM_STOPPED              # System stopped
EventType.CONNECTION_LOST             # Connection lost
EventType.CONNECTION_RESTORED         # Connection restored

# AI Events
EventType.PATTERN_DETECTED            # Pattern detected
EventType.ANOMALY_DETECTED            # Anomaly detected
EventType.AI_ALERT                    # AI alert
```

---

### 1.3 Event Data Structures

**RiskEvent Class:**

```python
@dataclass
class RiskEvent:
    """Risk management event."""

    event_type: EventType               # Type of event
    timestamp: datetime                 # When event occurred
    data: dict[str, Any]                # Event payload
    source: str = "risk_manager"        # Event source
    severity: str = "info"              # info, warning, error, critical

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "source": self.source,
            "severity": self.severity,
        }
```

**Event Data Schemas:**

```python
# TRADE_EXECUTED event data
{
    "symbol": "MNQ",
    "trade_id": 101112,
    "side": 0,  # 0=Buy, 1=Sell
    "size": 2,
    "price": 21000.75,
    "pnl": -50.25,  # Realized P&L (null for half-turns)
    "timestamp": datetime(...)
}

# POSITION_OPENED event data
{
    "symbol": "MNQ",
    "contract_id": "CON.F.US.MNQ.U25",
    "side": 1,  # 1=Long, 2=Short
    "size": 2,
    "entry_price": 21000.50,
    "account_id": 123
}

# POSITION_CLOSED event data
{
    "symbol": "MNQ",
    "contract_id": "CON.F.US.MNQ.U25",
    "realized_pnl": 100.50,
    "account_id": 123
}

# POSITION_UPDATED event data
{
    "symbol": "MNQ",
    "contract_id": "CON.F.US.MNQ.U25",
    "size": 2,
    "unrealized_pnl": 75.00,  # Current unrealized P&L
    "account_id": 123
}

# QUOTE_UPDATED event data ⭐ NEW
{
    "symbol": "MNQ",
    "last_price": 21050.25,
    "bid": 21050.00,
    "ask": 21050.50,
    "bid_size": 10,
    "ask_size": 15,
    "timestamp": datetime(...)
}

# RULE_VIOLATED event data
{
    "rule_name": "DailyRealizedLoss",
    "rule_id": "RULE-003",
    "reason": "Daily loss limit exceeded: -$520 (limit: -$500)",
    "action": "flatten",  # or "cancel", "lockout"
    "account_id": 123,
    "symbol": "MNQ"  # Optional: symbol-specific
}

# ENFORCEMENT_ACTION event data
{
    "action": "flatten_all",
    "reason": "Daily loss limit exceeded",
    "account_id": 123,
    "timestamp": datetime(...)
}
```

---

## 2. Event Bridge

### 2.1 Purpose

Convert SDK events to Risk events with appropriate data extraction and transformation.

**File:** `src/risk_manager/sdk/event_bridge.py`

### 2.2 Event Mappings

| SDK Event | Risk Event | Handler Method | Data Extracted |
|-----------|------------|----------------|----------------|
| `TRADE_EXECUTED` | `TRADE_EXECUTED` | `_on_trade_executed` | trade_id, price, size, pnl |
| `POSITION_OPENED` | `POSITION_OPENED` | `_on_position_opened` | contract_id, side, size, entry_price |
| `POSITION_CLOSED` | `POSITION_CLOSED` | `_on_position_closed` | contract_id, realized_pnl |
| `POSITION_UPDATED` | `POSITION_UPDATED` | `_on_position_updated` | contract_id, size, unrealized_pnl |
| `ORDER_PLACED` | `ORDER_PLACED` | `_on_order_placed` | order_id, side, size, type |
| `ORDER_FILLED` | `ORDER_FILLED` | `_on_order_filled` | order_id, fill_price, fill_size |
| `ORDER_CANCELLED` | `ORDER_CANCELLED` | `_on_order_cancelled` | order_id, reason |
| `ORDER_REJECTED` | `ORDER_REJECTED` | `_on_order_rejected` | order_id, reason |
| `QUOTE_UPDATE` ⭐ | `QUOTE_UPDATED` ⭐ | `_on_quote_update` ⭐ | symbol, last_price, bid, ask |

### 2.3 Implementation Pattern

**Subscription:**
```python
async def _subscribe_to_suite(self, symbol: str, suite: TradingSuite) -> None:
    """Subscribe to events from a specific TradingSuite."""    # Subscribe to trade events
    await suite.on(
        EventType.TRADE_EXECUTED,
        lambda event: self._on_trade_executed(symbol, event)
    )

    # Subscribe to position events
    await suite.on(
        EventType.POSITION_OPENED,
        lambda event: self._on_position_opened(symbol, event)
    )

    # Subscribe to quote events ⭐ NEW
    await suite.on(
        EventType.QUOTE_UPDATE,
        lambda event: self._on_quote_update(symbol, event)
    )

    # ... other subscriptions
```

**Handler Pattern:**
```python
async def _on_trade_executed(self, symbol: str, sdk_event: Any) -> None:
    """Handle trade executed event from SDK."""
    try:
        # Extract data from SDK event
        risk_event = RiskEvent(
            type=EventType.TRADE_EXECUTED,
            data={
                "symbol": symbol,
                "trade_id": getattr(sdk_event, "trade_id", None),
                "side": getattr(sdk_event, "side", None),
                "size": getattr(sdk_event, "size", None),
                "price": getattr(sdk_event, "price", None),
                "pnl": getattr(sdk_event, "profit_and_loss", None),  # ⭐ KEY
                "timestamp": getattr(sdk_event, "timestamp", None),
                "sdk_event": sdk_event,  # Keep reference for debugging
            }
        )

        # Publish to Risk EventBus
        await self.risk_event_bus.publish(risk_event)
        logger.debug(f"Bridged TRADE_EXECUTED event for {symbol}")

    except Exception as e:
        logger.error(f"Error bridging trade executed event: {e}")
```

**Quote Update Handler ⭐ NEW:**
```python
async def _on_quote_update(self, symbol: str, sdk_event: Any) -> None:
    """Handle quote update event from SDK."""
    try:
        risk_event = RiskEvent(
            type=EventType.QUOTE_UPDATED,
            data={
                "symbol": symbol,
                "last_price": getattr(sdk_event, "last_price", None),
                "bid": getattr(sdk_event, "best_bid", None),
                "ask": getattr(sdk_event, "best_ask", None),
                "bid_size": getattr(sdk_event, "bid_size", None),
                "ask_size": getattr(sdk_event, "ask_size", None),
                "timestamp": getattr(sdk_event, "timestamp", None),
            }
        )

        await self.risk_event_bus.publish(risk_event)
        logger.debug(f"Bridged QUOTE_UPDATED event for {symbol}")

    except Exception as e:
        logger.error(f"Error bridging quote update event: {e}")
```

---

## 3. Event Bus (Risk Manager)

### 3.1 Purpose

Pub/sub system for distributing risk events to subscribers (RiskEngine, rules, monitoring).

**File:** `src/risk_manager/core/events.py`

### 3.2 API

```python
class EventBus:
    """Simple event bus for distributing events."""

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Subscribe to event type.

        Args:
            event_type: Type of event to listen for
            handler: Async or sync callback function
        """

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """Unsubscribe from event type."""

    async def publish(self, event: RiskEvent) -> None:
        """
        Publish event to all subscribers.

        Args:
            event: RiskEvent to publish
        """
```

### 3.3 Usage Pattern

**Subscribe to Events:**
```python
event_bus = EventBus()

# Subscribe to trade events
async def on_trade(event: RiskEvent):
    logger.info(f"Trade executed: {event.data}")

await suite.on(EventType.TRADE_EXECUTED, on_trade)

# Subscribe to position events
await suite.on(EventType.POSITION_OPENED, on_position_opened)
await suite.on(EventType.POSITION_CLOSED, on_position_closed)

# Subscribe to quote events ⭐
await suite.on(EventType.QUOTE_UPDATED, on_quote_update)
```

**Publish Events:**
```python
# Publish event
event = RiskEvent(
    event_type=EventType.TRADE_EXECUTED,
    data={"symbol": "MNQ", "size": 2},
    source="trading_sdk"
)

await event_bus.publish(event)
# → All subscribers to TRADE_EXECUTED receive event
```

---

## 4. RiskEngine Event Processing

### 4.1 Purpose

Central event processor that routes events to all registered risk rules.

**File:** `src/risk_manager/core/engine.py`

### 4.2 Event Flow

```
RiskEngine.evaluate_rules(event)
├─ 📨 Checkpoint 6: "Event received: {event}"
│
├─ For each registered rule:
│  └─ result = rule.evaluate(event, engine)
│      ├─ Rule checks conditions
│      ├─ 🔍 Checkpoint 7: "Rule evaluated: {rule} {result}"
│      └─ Returns violation dict or None
│
├─ If violation:
│  └─ _handle_violation(violation, event)
│      ├─ ⚠️ Checkpoint 8: "Enforcement triggered: {action}"
│      ├─ Execute action (flatten, cancel, lockout)
│      └─ Publish ENFORCEMENT_ACTION event
│
└─ Return summary
```

### 4.3 Implementation

**Event Evaluation:**
```python
async def evaluate_rules(self, event: RiskEvent) -> dict[str, Any]:
    """
    Evaluate event against all registered rules.

    Args:
        event: RiskEvent to evaluate

    Returns:
        Dictionary with evaluation results
    """
    # Checkpoint 6: Event received
    logger.info(f"📨 Event received: {event.event_type.value}")

    violations = []

    # Evaluate each rule
    for rule in self.rules:
        try:
            result = await rule.evaluate(event, self)

            # Checkpoint 7: Rule evaluated
            status = "VIOLATED" if result else "OK"
            logger.info(f"🔍 Rule evaluated: {rule.name} → {status}")

            if result:
                violations.append({
                    "rule": rule.name,
                    "violation": result,
                    "event": event
                })

        except Exception as e:
            logger.error(f"Rule evaluation error: {rule.name}: {e}")

    # Handle violations
    for violation_data in violations:
        await self._handle_violation(
            violation_data["violation"],
            violation_data["event"]
        )

    return {
        "total_rules": len(self.rules),
        "violations": len(violations),
        "details": violations
    }
```

**Violation Handling:**
```python
async def _handle_violation(self, violation: dict, event: RiskEvent) -> None:
    """
    Handle rule violation by executing enforcement action.

    Args:
        violation: Violation details from rule
        event: Original event that triggered violation
    """
    action = violation.get("action")
    reason = violation.get("reason", "Rule violated")

    # Checkpoint 8: Enforcement triggered
    logger.warning(f"⚠️ Enforcement triggered: {action} - {reason}")

    # Execute enforcement action
    if action == "flatten":
        await self.flatten_all_positions()
    elif action == "flatten_symbol":
        symbol = event.data.get("symbol")
        await self.flatten_symbol_positions(symbol)
    elif action == "cancel_orders":
        await self.cancel_all_orders()
    elif action == "lockout":
        await self.set_lockout(violation)

    # Publish enforcement event
    enforcement_event = RiskEvent(
        event_type=EventType.ENFORCEMENT_ACTION,
        data={
            "action": action,
            "reason": reason,
            "violation": violation,
            "original_event": event.to_dict()
        },
        severity="critical"
    )

    await self.event_bus.publish(enforcement_event)
```

---

## 5. Event Routing to Rules

### 5.1 Rule Evaluation Pattern

**Each rule implements:**
```python
class BaseRule:
    async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> dict | None:
        """
        Evaluate event against rule conditions.

        Args:
            event: RiskEvent to evaluate
            engine: RiskEngine (for state access)

        Returns:
            Violation dict if violated, None if OK
        """
```

### 5.2 Event Type Filtering

**Rules only respond to relevant event types:**

```python
# Example: DailyRealizedLossRule
async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> dict | None:
    # Only respond to trade events
    if event.event_type != EventType.TRADE_EXECUTED:
        return None  # Ignore other events

    # Extract P&L from event
    pnl = event.data.get("pnl")
    if pnl is None:
        return None  # Half-turn trade (no realized P&L)

    # Update daily P&L tracker
    account_id = event.data.get("account_id")
    daily_pnl = await self.pnl_tracker.add_trade_pnl(account_id, pnl)

    # Check limit
    if daily_pnl <= self.config.daily_loss_limit:
        return {
            "action": "flatten",
            "reason": f"Daily loss limit hit: ${daily_pnl:.2f}"
        }

    return None  # OK
```

### 5.3 Event Types by Rule

| Rule | Event Types Used | Purpose |
|------|------------------|---------|
| RULE-001: MaxContracts | POSITION_OPENED, POSITION_UPDATED | Count total contracts |
| RULE-002: MaxContractsPerInstrument | POSITION_OPENED, POSITION_UPDATED | Count per-symbol contracts |
| RULE-003: DailyRealizedLoss | TRADE_EXECUTED | Track realized P&L |
| RULE-004: DailyUnrealizedLoss | POSITION_UPDATED, QUOTE_UPDATED ⭐ | Track unrealized drawdown |
| RULE-005: MaxUnrealizedProfit | POSITION_UPDATED, QUOTE_UPDATED ⭐ | Track unrealized profit |
| RULE-006: TradeFrequencyLimit | TRADE_EXECUTED | Count trades in time window |
| RULE-007: CooldownAfterLoss | TRADE_EXECUTED | Detect losing trades |
| RULE-008: NoStopLossGrace | ORDER_PLACED | Check for stop-loss orders |
| RULE-009: SessionBlockOutside | POSITION_OPENED | Check session times |
| RULE-010: AuthLossGuard | SYSTEM_EVENT (canTrade=false) | Check API auth status |
| RULE-011: SymbolBlocks | POSITION_OPENED | Check symbol whitelist |
| RULE-012: TradeManagement | ORDER_PLACED | Manage bracket orders |
| RULE-013: DailyRealizedProfit | TRADE_EXECUTED | Track profit target |

---

## 6. Quote Event Handling ⭐ NEW

### 6.1 Purpose

Real-time quote updates enable accurate unrealized P&L tracking for RULE-004 and RULE-005.

### 6.2 Quote Event Flow

```
TopstepX Platform
│ Market price changes
▼
SignalR: GatewayQuote event
│
▼
SDK: QUOTE_UPDATE event
│
▼
EventBridge._on_quote_update()
│ Converts to QUOTE_UPDATED RiskEvent
▼
Risk EventBus
│
├─> RULE-004: DailyUnrealizedLoss
│   └─ Recalculate unrealized P&L
│   └─ Check if drawdown exceeds limit
│
├─> RULE-005: MaxUnrealizedProfit
│   └─ Recalculate unrealized P&L
│   └─ Check if profit target hit
│
└─> PnL Tracker
    └─ Update unrealized P&L state
```

### 6.3 Implementation

**EventBridge Subscription:**
```python
# Subscribe to quote updates
await suite.on(
    EventType.QUOTE_UPDATE,
    lambda event: self._on_quote_update(symbol, event)
)
```

**Handler:**
```python
async def _on_quote_update(self, symbol: str, sdk_event: Any) -> None:
    """Handle quote update from SDK."""
    risk_event = RiskEvent(
        type=EventType.QUOTE_UPDATED,
        data={
            "symbol": symbol,
            "last_price": sdk_event.last_price,
            "bid": sdk_event.best_bid,
            "ask": sdk_event.best_ask,
            "timestamp": sdk_event.timestamp,
        }
    )

    await self.risk_event_bus.publish(risk_event)
```

**Rule Processing (RULE-004):**
```python
async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> dict | None:
    # Listen for quote updates
    if event.event_type != EventType.QUOTE_UPDATED:
        return None

    symbol = event.data.get("symbol")
    current_price = event.data.get("last_price")

    # Get open positions for this symbol
    positions = await engine.trading_integration.suite[symbol].positions.get_all_positions()

    total_unrealized = 0.0
    for pos in positions:
        # Calculate unrealized P&L
        if pos.size > 0:  # Long
            unrealized = (current_price - pos.average_price) * pos.size * multiplier
        else:  # Short
            unrealized = (pos.average_price - current_price) * abs(pos.size) * multiplier

        total_unrealized += unrealized

    # Check limit
    if total_unrealized <= self.config.daily_unrealized_loss_limit:
        return {
            "action": "close_positions",
            "reason": f"Unrealized drawdown limit: ${total_unrealized:.2f}"
        }

    return None
```

### 6.4 Quote Event Throttling

**Problem:** Quote events fire on every price tick (high frequency)

**Solution:** Throttle or debounce quote events

```python
# Option 1: Throttle (process at most every N seconds)
from asyncio import Lock

class QuoteThrottle:
    def __init__(self, interval_seconds: float = 1.0):
        self.interval = interval_seconds
        self.last_processed = {}
        self.lock = Lock()

    async def should_process(self, symbol: str) -> bool:
        async with self.lock:
            now = time.time()
            last = self.last_processed.get(symbol, 0)

            if now - last >= self.interval:
                self.last_processed[symbol] = now
                return True

            return False

# Usage in EventBridge
throttle = QuoteThrottle(interval_seconds=1.0)

async def _on_quote_update(self, symbol: str, sdk_event: Any) -> None:
    if not await throttle.should_process(symbol):
        return  # Skip this update

    # Process quote
    risk_event = RiskEvent(...)
    await self.risk_event_bus.publish(risk_event)

# Option 2: Debounce (wait for quiet period)
# Only process if no updates for N milliseconds
```

---

## 7. Position Polling Events

### 7.1 Purpose

In addition to real-time events, poll positions every N seconds to ensure no missed updates.

**File:** `src/risk_manager/integrations/trading.py`

### 7.2 Implementation

```python
async def _monitor_positions(self) -> None:
    """Monitor positions and P&L via polling."""
    while self.running:
        try:
            # Get positions for each instrument
            for symbol in self.instruments:
                context = self.suite[symbol]
                positions = await context.positions.get_all_positions()

                for position in positions:
                    # Publish position update event
                    risk_event = RiskEvent(
                        event_type=EventType.POSITION_UPDATED,
                        data={
                            "symbol": symbol,
                            "size": position.size,
                            "average_price": position.average_price,
                            "unrealized_pnl": position.unrealized_pnl,
                            "realized_pnl": position.realized_pnl,
                        },
                        source="trading_sdk_poll"
                    )

                    await self.event_bus.publish(risk_event)

            # Update every 5 seconds
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
            await asyncio.sleep(10)  # Wait longer on error
```

### 7.3 Why Both Events + Polling?

**Real-time Events (SignalR):**
- ✅ Immediate (millisecond latency)
- ✅ Triggered by platform changes
- ❌ May miss updates if reconnecting
- ❌ May have gaps during high volume

**Polling:**
- ✅ Guaranteed to catch current state
- ✅ Simple to implement
- ❌ Higher latency (5s intervals)
- ❌ More API calls

**Best Practice:** Use both
- Real-time events for immediate enforcement
- Polling as safety net to catch missed updates

---

## 8. Event Logging

### 8.1 8-Checkpoint Logging System

**Checkpoints for event flow:**

```
Checkpoint 1: 🚀 Service Start
Checkpoint 2: ✅ Config Loaded
Checkpoint 3: ✅ SDK Connected
Checkpoint 4: ✅ Rules Initialized
Checkpoint 5: ✅ Event Loop Running

Checkpoint 6: 📨 Event Received
  └─ Log: "📨 Event received: TRADE_EXECUTED {data}"
  └─ Where: engine.py:evaluate_rules()

Checkpoint 7: 🔍 Rule Evaluated
  └─ Log: "🔍 Rule evaluated: DailyRealizedLoss → VIOLATED"
  └─ Where: engine.py:evaluate_rules() (per rule)

Checkpoint 8: ⚠️ Enforcement Triggered
  └─ Log: "⚠️ Enforcement triggered: FLATTEN ALL - Daily loss limit"
  └─ Where: engine.py:_handle_violation()
```

### 8.2 Event Log Format

```python
# Event received
logger.info(f"📨 Event received: {event.event_type.value}")
logger.debug(f"Event data: {event.data}")

# Rule evaluated
status = "VIOLATED" if result else "OK"
logger.info(f"🔍 Rule {rule.name} evaluated: {status}")
if result:
    logger.warning(f"Violation: {result}")

# Enforcement triggered
logger.warning(f"⚠️ Enforcement: {action} - {reason}")
```

---

## 9. Error Handling

### 9.1 Event Bridge Errors

**SDK Event Processing Failures:**
```python
async def _on_trade_executed(self, symbol: str, sdk_event: Any) -> None:
    try:
        # Extract data
        risk_event = RiskEvent(...)
        await self.risk_event_bus.publish(risk_event)

    except Exception as e:
        logger.error(f"Error bridging trade event: {e}")
        # Don't propagate - continue processing other events
```

### 9.2 Rule Evaluation Errors

**Rule Exceptions:**
```python
for rule in self.rules:
    try:
        result = await rule.evaluate(event, self)
        # Process result

    except Exception as e:
        logger.error(f"Rule evaluation error: {rule.name}: {e}")
        # Continue with other rules - don't fail entire evaluation
```

### 9.3 Event Bus Errors

**Subscriber Exceptions:**
```python
async def publish(self, event: RiskEvent) -> None:
    """Publish event to all subscribers."""
    if event.event_type in self._handlers:
        for handler in self._handlers[event.event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)

            except Exception as e:
                logger.error(f"Event handler error: {e}")
                # Continue with other handlers
```

---

## 10. Testing Strategy

### 10.1 Event Bridge Tests

**Test SDK → Risk event conversion:**
```python
async def test_trade_event_bridging():
    # Mock SDK event
    sdk_event = Mock()
    sdk_event.trade_id = 123
    sdk_event.price = 21000.50
    sdk_event.size = 2
    sdk_event.profit_and_loss = -50.0

    # Mock risk event bus
    risk_event_bus = AsyncMock()

    # Create bridge
    bridge = EventBridge(suite_manager, risk_event_bus)

    # Handle SDK event
    await bridge._on_trade_executed("MNQ", sdk_event)

    # Verify risk event published
    risk_event_bus.publish.assert_called_once()
    call_args = risk_event_bus.publish.call_args[0][0]
    assert call_args.event_type == EventType.TRADE_EXECUTED
    assert call_args.data["pnl"] == -50.0
```

### 10.2 Event Bus Tests

**Test pub/sub:**
```python
async def test_event_bus_pubsub():
    event_bus = EventBus()
    received_events = []

    # Subscribe
    async def handler(event: RiskEvent):
        received_events.append(event)

    await suite.on(EventType.TRADE_EXECUTED, handler)

    # Publish
    event = RiskEvent(
        event_type=EventType.TRADE_EXECUTED,
        data={"symbol": "MNQ"}
    )

    await event_bus.publish(event)

    # Verify
    assert len(received_events) == 1
    assert received_events[0].event_type == EventType.TRADE_EXECUTED
```

### 10.3 Rule Evaluation Tests

**Test event routing:**
```python
async def test_rule_evaluation_on_event():
    # Mock rule
    rule = AsyncMock()
    rule.name = "TestRule"
    rule.evaluate.return_value = None  # No violation

    # Create engine
    engine = RiskEngine(config, event_bus)
    engine.add_rule(rule)

    # Publish event
    event = RiskEvent(
        event_type=EventType.TRADE_EXECUTED,
        data={"symbol": "MNQ"}
    )

    await engine.evaluate_rules(event)

    # Verify rule was called
    rule.evaluate.assert_called_once_with(event, engine)
```

---

## 11. Performance Considerations

### 11.1 Event Frequency

**High-frequency events:**
- QUOTE_UPDATE: Every price tick (10-100+ per second)
- TRADE_TICK: Every market trade (high volume)
- ORDERBOOK_UPDATE: Every DOM change

**Medium-frequency events:**
- POSITION_UPDATED: Every position change
- ORDER_FILLED: Every order execution

**Low-frequency events:**
- POSITION_OPENED/CLOSED: New positions
- ORDER_PLACED/CANCELLED: Order management

### 11.2 Optimization Strategies

**1. Event Throttling:**
```python
# Process at most 1 quote per second per symbol
throttle = QuoteThrottle(interval_seconds=1.0)
```

**2. Event Filtering:**
```python
# Only process events for monitored instruments
if event.data.get("symbol") not in self.monitored_symbols:
    return  # Ignore
```

**3. Async Processing:**
```python
# Don't block on rule evaluation
asyncio.create_task(rule.evaluate(event, engine))
```

**4. Event Batching:**
```python
# Batch multiple quote updates
quote_buffer = []

async def process_quote_batch():
    while True:
        await asyncio.sleep(1.0)
        if quote_buffer:
            # Process all quotes at once
            await process_quotes(quote_buffer)
            quote_buffer.clear()
```

---

## 12. Implementation Checklist

### Core Event Flow
- [x] EventBus implementation
- [x] RiskEvent dataclass
- [x] EventBridge SDK subscription
- [x] EventBridge event conversion
- [x] RiskEngine event routing
- [x] Rule evaluation pattern

### Event Types
- [x] Trade events
- [x] Position events
- [x] Order events
- [ ] Quote events ⭐ NEW
- [x] System events
- [x] Risk events

### Event Logging
- [x] Checkpoint 6: Event received
- [x] Checkpoint 7: Rule evaluated
- [x] Checkpoint 8: Enforcement triggered
- [x] Debug logging

### Optimization
- [ ] Quote event throttling ⭐
- [ ] Event filtering
- [ ] Async rule processing
- [ ] Performance monitoring

---

## 13. References

**Implementation Files:**
- `src/risk_manager/core/events.py` - EventBus, RiskEvent
- `src/risk_manager/sdk/event_bridge.py` - SDK → Risk conversion
- `src/risk_manager/core/engine.py` - Event routing to rules
- `src/risk_manager/integrations/trading.py` - Position polling

**Related Specs:**
- SDK Integration (UNIFIED-SDK-001)
- Quote Data Integration (UNIFIED-SDK-003) ⭐

**Wave 1 Analysis:**
- `docs/analysis/wave1-feature-inventory/02-SDK-INTEGRATION-INVENTORY.md`

---

**Document Status:** Complete
**Last Updated:** 2025-10-25
**Next Review:** When adding new event types or optimizing performance
