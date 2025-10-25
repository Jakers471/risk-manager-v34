# Technical Reference Feature Inventory

**Researcher**: #8 - Technical Reference Specialist
**Generated**: 2025-10-25
**Sources**: SDK_API_REFERENCE.md, SDK_ENFORCEMENT_FLOW.md, examples/, actual implementation

---

## Executive Summary

This inventory documents the **actual API contracts** used in Risk Manager V34, preventing test/code mismatches. It maps SDK capabilities, our custom implementations, enforcement flows, and usage patterns from working examples.

**Key Finding**: The Project-X-Py SDK provides infrastructure (WebSocket, order/position management), but we define our own event types and risk logic on top.

---

## 1. API Contracts - Core Events

### 1.1 RiskEvent Class (OUR CUSTOM CLASS)

**Location**: `src/risk_manager/core/events.py`

**Actual Constructor Signature**:
```python
@dataclass
class RiskEvent:
    event_type: EventType  # ← CRITICAL: "event_type", NOT "type"!
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)
    source: str = "risk_manager"
    severity: str = "info"  # info, warning, error, critical
```

**Common Mistake**:
```python
# ❌ WRONG (tests do this)
event = RiskEvent(type=EventType.POSITION_UPDATED, data={})

# ✅ CORRECT
event = RiskEvent(event_type=EventType.POSITION_UPDATED, data={})
```

**Methods**:
- `to_dict() -> dict[str, Any]` - Serialize to dictionary
- `from_dict(data: dict) -> RiskEvent` - Deserialize from dictionary

---

### 1.2 EventType Enum (OUR CUSTOM ENUM)

**Location**: `src/risk_manager/core/events.py`

**All Available Values**:
```python
class EventType(str, Enum):
    # Position events (SDK-compatible)
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"

    # Order events (SDK-compatible)
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    ORDER_UPDATED = "order_updated"  # Added for test compatibility

    # Risk events (CUSTOM)
    RULE_VIOLATED = "rule_violated"
    RULE_WARNING = "rule_warning"
    ENFORCEMENT_ACTION = "enforcement_action"

    # P&L events (CUSTOM)
    PNL_UPDATED = "pnl_updated"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    DRAWDOWN_ALERT = "drawdown_alert"

    # Trade events (CUSTOM)
    TRADE_EXECUTED = "trade_executed"  # Added for test compatibility

    # System events (CUSTOM)
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"

    # AI events (CUSTOM)
    PATTERN_DETECTED = "pattern_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    AI_ALERT = "ai_alert"
```

**Note**: We define our own EventType enum that includes both SDK-compatible events and custom risk events.

---

### 1.3 EventBus Class (OUR CUSTOM CLASS)

**Location**: `src/risk_manager/core/events.py`

**Constructor Signature**:
```python
class EventBus:
    def __init__(self):
        self._handlers: dict[EventType, list] = {}
```

**API Methods**:
```python
def subscribe(self, event_type: EventType, handler) -> None
def unsubscribe(self, event_type: EventType, handler) -> None
async def publish(self, event: RiskEvent) -> None
```

**Usage Pattern**:
```python
# Create event bus
bus = EventBus()

# Subscribe to events
async def on_violation(event: RiskEvent):
    print(f"Violation: {event.data['message']}")

bus.subscribe(EventType.RULE_VIOLATED, on_violation)

# Publish events
event = RiskEvent(
    event_type=EventType.RULE_VIOLATED,
    data={"message": "Daily loss limit exceeded", "action": "flatten"}
)
await bus.publish(event)
```

---

## 2. API Contracts - State Management

### 2.1 PnLTracker Class

**Location**: `src/risk_manager/state/pnl_tracker.py`

**Constructor Signature**:
```python
class PnLTracker:
    def __init__(self, db: Database):
        """
        Args:
            db: Database instance for persistence
        """
```

**IMPORTANT**: Constructor takes `db: Database`, NOT `account_id: str`!

**API Methods**:
```python
# Add trade P&L
def add_trade_pnl(
    self,
    account_id: str,
    pnl: float,
    trade_date: date | None = None
) -> float

# Get daily P&L
def get_daily_pnl(
    self,
    account_id: str,
    trade_date: date | None = None
) -> float

# Get trade count
def get_trade_count(
    self,
    account_id: str,
    trade_date: date | None = None
) -> int

# Reset daily P&L (5 PM reset)
def reset_daily_pnl(
    self,
    account_id: str,
    trade_date: date | None = None
) -> None

# Get all accounts' daily P&L
def get_all_daily_pnls(
    self,
    trade_date: date | None = None
) -> Dict[str, float]

# Get complete stats
def get_stats(
    self,
    account_id: str,
    trade_date: date | None = None
) -> Dict[str, float | int]
```

**Usage Pattern**:
```python
from risk_manager.state.database import Database
from risk_manager.state.pnl_tracker import PnLTracker

# Create tracker
db = Database("data/risk_manager.db")
tracker = PnLTracker(db)

# Track trade P&L
new_total = tracker.add_trade_pnl("ACCOUNT-001", -150.0)

# Check if limit hit
daily_pnl = tracker.get_daily_pnl("ACCOUNT-001")
if daily_pnl <= -500.0:
    # Enforce daily loss limit
    pass
```

---

### 2.2 Database Class

**Location**: `src/risk_manager/state/database.py`

**Constructor Signature**:
```python
class Database:
    def __init__(self, db_path: str = "data/risk_manager.db"):
        """
        Args:
            db_path: Path to SQLite database file
        """
```

**API Methods**:
```python
def execute(self, query: str, params: tuple = ()) -> list[dict]
def execute_one(self, query: str, params: tuple = ()) -> dict | None
def execute_write(self, query: str, params: tuple = ()) -> int
def close(self) -> None
```

**Tables**:
- `daily_pnl` - Daily P&L tracking per account

---

## 3. API Contracts - Rules

### 3.1 RiskRule Base Class

**Location**: `src/risk_manager/rules/base.py`

**Constructor Signature**:
```python
class RiskRule(ABC):
    def __init__(self, action: str = "alert"):
        """
        Args:
            action: Action to take on violation ("alert", "pause", "flatten")
        """
        self.action = action
        self.enabled = True
```

**Abstract Methods**:
```python
@abstractmethod
async def evaluate(
    self,
    event: RiskEvent,
    engine: "RiskEngine"
) -> dict[str, Any] | None:
    """
    Returns:
        Dictionary with violation details if violated, None otherwise
    """
```

**Provided Methods**:
```python
def enable(self) -> None
def disable(self) -> None
```

**Usage Pattern**:
```python
from risk_manager.rules.base import RiskRule
from risk_manager.core.events import RiskEvent

class CustomRule(RiskRule):
    def __init__(self, limit: float, action: str = "alert"):
        super().__init__(action)
        self.limit = limit

    async def evaluate(self, event: RiskEvent, engine) -> dict | None:
        # Implement rule logic
        if condition_violated:
            return {
                "rule": "CustomRule",
                "message": "Limit exceeded",
                "action": self.action,
                "details": {...}
            }
        return None
```

---

## 4. API Contracts - SDK Integration

### 4.1 SuiteManager Class

**Location**: `src/risk_manager/sdk/suite_manager.py`

**Constructor Signature**:
```python
class SuiteManager:
    def __init__(self, event_bus: EventBus):
        """
        Args:
            event_bus: Event bus for publishing SDK events
        """
```

**API Methods**:
```python
# Add instrument and create TradingSuite
async def add_instrument(
    self,
    symbol: str,
    timeframes: list[str] | None = None,
    enable_orderbook: bool = False,
    enable_statistics: bool = True,
) -> TradingSuite

# Remove instrument
async def remove_instrument(self, symbol: str) -> None

# Get specific suite
def get_suite(self, symbol: str) -> TradingSuite | None

# Get all suites
def get_all_suites(self) -> dict[str, TradingSuite]

# Start/stop manager
async def start(self) -> None
async def stop(self) -> None

# Health monitoring
async def get_health_status(self) -> dict[str, Any]
```

**Usage Pattern**:
```python
from risk_manager.sdk.suite_manager import SuiteManager
from risk_manager.core.events import EventBus

# Create suite manager
event_bus = EventBus()
suite_manager = SuiteManager(event_bus)

# Add instruments
mnq_suite = await suite_manager.add_instrument(
    "MNQ",
    timeframes=["1min", "5min"],
    enable_statistics=True
)

# Start monitoring
await suite_manager.start()

# Get suite for operations
suite = suite_manager.get_suite("MNQ")
```

---

### 4.2 EnforcementExecutor Class

**Location**: `src/risk_manager/sdk/enforcement.py`

**Constructor Signature**:
```python
class EnforcementExecutor:
    def __init__(self, suite_manager: SuiteManager):
        """
        Args:
            suite_manager: SuiteManager for accessing TradingSuites
        """
```

**API Methods**:
```python
# Close all positions
async def close_all_positions(
    self,
    symbol: str | None = None
) -> dict[str, Any]
# Returns: {"success": bool, "closed": int, "errors": list}

# Close specific position
async def close_position(
    self,
    symbol: str,
    contract_id: str
) -> dict[str, Any]
# Returns: {"success": bool, "error": str | None}

# Reduce position to limit
async def reduce_position_to_limit(
    self,
    symbol: str,
    contract_id: str,
    target_size: int
) -> dict[str, Any]
# Returns: {"success": bool, "error": str | None}

# Cancel all orders
async def cancel_all_orders(
    self,
    symbol: str | None = None
) -> dict[str, Any]
# Returns: {"success": bool, "cancelled": int, "errors": list}

# Cancel specific order
async def cancel_order(
    self,
    symbol: str,
    order_id: str
) -> dict[str, Any]
# Returns: {"success": bool, "error": str | None}

# Full flatten (positions + orders)
async def flatten_and_cancel(
    self,
    symbol: str | None = None
) -> dict[str, Any]
# Returns: {"success": bool, "closed": int, "cancelled": int, "errors": list}
```

**Usage Pattern**:
```python
from risk_manager.sdk.enforcement import EnforcementExecutor

# Create executor
enforcement = EnforcementExecutor(suite_manager)

# Enforce daily loss limit - close all positions
result = await enforcement.close_all_positions()
if result["success"]:
    print(f"Closed {result['closed']} positions")

# Enforce max contracts - reduce to limit
result = await enforcement.reduce_position_to_limit(
    "MNQ",
    contract_id="123",
    target_size=2
)
```

**Logging**: All enforcement actions log via SDK logger with checkpoint markers:
```python
sdk_logger.warning(f"⚠️ Enforcement triggered: CLOSE ALL POSITIONS - Symbol: {symbol}")
```

---

### 4.3 EventBridge Class

**Location**: `src/risk_manager/sdk/event_bridge.py`

**Constructor Signature**:
```python
class EventBridge:
    def __init__(
        self,
        suite_manager: SuiteManager,
        risk_event_bus: EventBus
    ):
        """
        Args:
            suite_manager: SuiteManager for accessing TradingSuites
            risk_event_bus: Risk engine's EventBus for publishing events
        """
```

**API Methods**:
```python
async def start(self) -> None
async def stop(self) -> None
async def add_instrument(self, symbol: str, suite: TradingSuite) -> None
```

**Event Mapping** (SDK → Risk Manager):
```python
# SDK Event Type → Risk Event Type
SDKEventType.TRADE_EXECUTED → EventType.TRADE_EXECUTED
SDKEventType.POSITION_OPENED → EventType.POSITION_OPENED
SDKEventType.POSITION_CLOSED → EventType.POSITION_CLOSED
SDKEventType.POSITION_UPDATED → EventType.POSITION_UPDATED
SDKEventType.ORDER_PLACED → EventType.ORDER_PLACED
SDKEventType.ORDER_FILLED → EventType.ORDER_FILLED
SDKEventType.ORDER_CANCELLED → EventType.ORDER_CANCELLED
SDKEventType.ORDER_REJECTED → EventType.ORDER_REJECTED
```

**Usage Pattern**:
```python
from risk_manager.sdk.event_bridge import EventBridge

# Create event bridge
event_bridge = EventBridge(suite_manager, risk_event_bus)

# Add instrument to bridge
await event_bridge.add_instrument("MNQ", mnq_suite)

# Start bridging (SDK events → Risk events)
await event_bridge.start()

# Now SDK events automatically flow to risk engine
```

---

## 5. Enforcement Flow

### 5.1 Complete Enforcement Chain

**Step-by-Step Flow** (Violation → SDK Action):

```
1. TRADE EXECUTES
   ├─ TopstepX Platform
   └─ WebSocket event sent

2. SDK RECEIVES EVENT
   ├─ Project-X-Py TradingSuite
   └─ Fires SDK event

3. EVENT BRIDGE CONVERTS
   ├─ EventBridge._on_position_updated()
   ├─ SDK event → RiskEvent
   └─ Publishes to risk EventBus

4. RISK MANAGER RECEIVES
   ├─ RiskManager._handle_position_update()
   └─ Calls engine.evaluate_rules(event)

5. ENGINE EVALUATES RULES
   ├─ RiskEngine.evaluate_rules()
   ├─ For each rule: rule.evaluate(event, engine)
   └─ DailyLossRule checks: daily_pnl <= -500?

6. RULE VIOLATION DETECTED
   ├─ Rule returns: {"action": "flatten", "reason": "..."}
   └─ Engine calls: _handle_violation()

7. ENFORCEMENT TRIGGERED
   ├─ RiskEngine._handle_violation()
   ├─ Logs: "⚠️ Enforcement triggered"
   └─ Calls: flatten_all_positions()

8. ENGINE → TRADING INTEGRATION
   ├─ RiskEngine.flatten_all_positions()
   ├─ Publishes ENFORCEMENT_ACTION event
   └─ Calls: self.trading_integration.flatten_all()

9. TRADING INTEGRATION → SDK
   ├─ TradingIntegration.flatten_all()
   └─ For each instrument: flatten_position(symbol)

10. SDK CALL EXECUTES
    ├─ suite[symbol].positions.close_all_positions()
    └─ SDK's PositionManager.close_all_positions()

11. REST API CALLED
    ├─ POST /api/Position/closeAllPositions
    └─ TopstepX Platform

12. POSITIONS CLOSED
    └─ ✅ Trader is now flat
```

---

### 5.2 Critical Wiring Points

**Wiring #1**: RiskEngine ← TradingIntegration

**File**: `src/risk_manager/core/manager.py:140`
```python
async def _init_trading_integration(self, instruments: list[str]) -> None:
    # Create and connect TradingIntegration
    self.trading_integration = TradingIntegration(instruments, self.event_bus)
    await self.trading_integration.connect()

    # 🔗 THE CRITICAL WIRING
    self.engine.trading_integration = self.trading_integration
    logger.info("✅ TradingIntegration wired to RiskEngine")
```

**Wiring #2**: TradingIntegration ← SDK TradingSuite

**File**: `src/risk_manager/integrations/trading.py:36`
```python
async def connect(self) -> None:
    # 🔗 REAL SDK CONNECTION
    self.suite = await TradingSuite.create(
        instruments=self.instruments,
        timeframes=["1min", "5min"],
        enable_orderbook=True,
        enable_risk_management=True,
    )
```

---

### 5.3 SDK Methods Used for Enforcement

**PositionManager** (via `suite.positions`):
```python
# Close all positions for instrument
await suite.positions.close_all_positions()

# Close specific position
await suite.positions.close_position_by_contract(contract_id)

# Partially close position
await suite.positions.partially_close_position(contract_id, size)

# Get all positions
positions = await suite.positions.get_all_positions()

# Get portfolio P&L
pnl = await suite.positions.calculate_portfolio_pnl()
```

**OrderManager** (via `suite.orders`):
```python
# Cancel all orders
await suite.orders.cancel_all_orders()

# Cancel specific order
await suite.orders.cancel_order(order_id)

# Cancel all orders for position
await suite.orders.cancel_position_orders(contract_id)
```

---

## 6. Usage Patterns from Examples

### 6.1 Basic Usage Pattern (Example 01)

**File**: `examples/01_basic_usage.py`

```python
import asyncio
from risk_manager import RiskManager

async def main():
    # Create with simple rules (dict config)
    rm = await RiskManager.create(
        instruments=["MNQ"],
        rules={
            "max_daily_loss": -500.0,
            "max_contracts": 2,
        }
    )

    # Subscribe to events
    @rm.on("rule_violated")
    async def handle_violation(event):
        print(f"ALERT: {event.data['message']}")

    # Start monitoring
    await rm.start()

    # Run until interrupted
    try:
        await rm.wait_until_stopped()
    except KeyboardInterrupt:
        await rm.stop()

asyncio.run(main())
```

**Key Patterns**:
- Use `RiskManager.create()` classmethod (async)
- Pass rules as dict for simple config
- Subscribe to events with `@rm.on("event_type")`
- Start/stop lifecycle management

---

### 6.2 Advanced Rules Pattern (Example 02)

**File**: `examples/02_advanced_rules.py`

```python
from risk_manager import RiskManager
from risk_manager.rules import DailyLossRule, MaxPositionRule

async def main():
    # Create risk manager
    rm = await RiskManager.create(instruments=["MNQ", "ES"])

    # Add custom rules with specific actions
    daily_loss = DailyLossRule(
        limit=-1000.0,
        action="flatten"  # Automatically close positions
    )
    rm.add_rule(daily_loss)

    max_position = MaxPositionRule(
        max_contracts=5,
        per_instrument=True,
        action="reject"  # Reject orders that exceed
    )
    rm.add_rule(max_position)

    # Subscribe to multiple event types
    @rm.on("rule_violated")
    async def on_violation(event):
        print(f"VIOLATION: {event.data['rule']}")

    @rm.on("enforcement_action")
    async def on_enforcement(event):
        print(f"ENFORCEMENT: {event.data['action']}")

    @rm.on("position_updated")
    async def on_position_update(event):
        print(f"Position: {event.data['symbol']} - {event.data['size']}")

    await rm.start()
```

**Key Patterns**:
- Import specific rule classes
- Create rule instances with custom parameters
- Add rules via `rm.add_rule(rule)`
- Subscribe to multiple event types
- Use different enforcement actions per rule

---

### 6.3 Multi-Instrument Pattern (Example 03)

**File**: `examples/03_multi_instrument.py`

```python
from risk_manager import RiskManager

async def main():
    # Monitor multiple instruments
    instruments = ["MNQ", "ES", "MGC"]

    rm = await RiskManager.create(
        instruments=instruments,
        rules={
            "max_daily_loss": -2000.0,  # Portfolio-wide
            "max_contracts": 10,  # Total across all
        }
    )

    # Track per-instrument stats
    instrument_stats = {inst: {"fills": 0, "pnl": 0.0} for inst in instruments}

    @rm.on("order_filled")
    async def track_fills(event):
        symbol = event.data.get("symbol")
        instrument_stats[symbol]["fills"] += 1

    @rm.on("position_updated")
    async def track_pnl(event):
        symbol = event.data["symbol"]
        pnl = event.data.get("unrealized_pnl", 0) + event.data.get("realized_pnl", 0)
        instrument_stats[symbol]["pnl"] = pnl

        # Calculate portfolio total
        total_pnl = sum(s["pnl"] for s in instrument_stats.values())
        print(f"Portfolio P&L: ${total_pnl:.2f}")
```

**Key Patterns**:
- Pass list of instruments to `create()`
- Rules apply portfolio-wide by default
- Track per-instrument stats in event handlers
- Aggregate across instruments for portfolio view

---

### 6.4 SDK Integration Pattern (Example 04)

**File**: `examples/04_sdk_integration.py`

```python
from risk_manager.core.config import RiskConfig
from risk_manager.core.engine import RiskEngine
from risk_manager.core.events import EventBus
from risk_manager.rules import MaxContractsPerInstrumentRule
from risk_manager.sdk import SuiteManager, EventBridge, EnforcementExecutor

async def main():
    # 1. Create event bus
    event_bus = EventBus()

    # 2. Create SDK components
    suite_manager = SuiteManager(event_bus)
    enforcement_executor = EnforcementExecutor(suite_manager)
    event_bridge = EventBridge(suite_manager, event_bus)

    # 3. Create risk engine
    config = RiskConfig()
    risk_engine = RiskEngine(config, event_bus)
    risk_engine.enforcement_executor = enforcement_executor

    # 4. Add rules
    max_contracts_rule = MaxContractsPerInstrumentRule(
        limits={"MNQ": 2, "ES": 1},
        enforcement="reduce_to_limit",
        unknown_symbol_action="block",
    )
    risk_engine.add_rule(max_contracts_rule)

    # 5. Add instruments
    mnq_suite = await suite_manager.add_instrument(
        "MNQ",
        timeframes=["1min", "5min"],
        enable_statistics=True
    )
    await event_bridge.add_instrument("MNQ", mnq_suite)

    # 6. Start all components
    await suite_manager.start()
    await event_bridge.start()
    await risk_engine.start()

    # 7. Monitor
    health = await suite_manager.get_health_status()
    print(f"Total Suites: {health['total_suites']}")
```

**Key Patterns**:
- Manual component assembly for fine-grained control
- SuiteManager → TradingSuite instances
- EventBridge → SDK events to risk events
- EnforcementExecutor → Risk engine enforcement
- Health monitoring via `get_health_status()`

---

## 7. Integration Patterns

### 7.1 Component Relationships

```
┌─────────────────┐
│  RiskManager    │ ← High-level API (examples 01-03)
└────────┬────────┘
         │
         ├─ RiskEngine ─────┐
         │                  │
         ├─ EventBus        │
         │                  │
         └─ TradingIntegration ──┐
                            │    │
┌───────────────────────────┘    │
│                                │
│  SDK Integration Layer         │
│  (Example 04 shows manual)     │
│                                │
├─ SuiteManager ────────┬────────┘
│                       │
├─ EventBridge          │
│                       │
└─ EnforcementExecutor  │
                        │
┌───────────────────────┘
│
│  Project-X-Py SDK
│
├─ TradingSuite
│  ├─ PositionManager
│  ├─ OrderManager
│  └─ EventBus (SDK's)
│
└─ WebSocket (SignalR) → TopstepX Platform
```

---

### 7.2 Event Flow Pattern

```
TopstepX Platform
    ↓ WebSocket
SDK TradingSuite
    ↓ SDK EventBus
EventBridge
    ↓ Converts: SDK Event → RiskEvent
Risk EventBus
    ↓ Distributes
RiskEngine + Rules
    ↓ Evaluates
Violation Detected
    ↓ Enforcement
EnforcementExecutor
    ↓ SDK Calls
PositionManager / OrderManager
    ↓ REST API
TopstepX Platform
```

---

### 7.3 Initialization Pattern

```python
# Pattern 1: High-level (recommended for most users)
rm = await RiskManager.create(instruments=["MNQ"], rules={...})
await rm.start()

# Pattern 2: Manual (for advanced control)
event_bus = EventBus()
suite_manager = SuiteManager(event_bus)
event_bridge = EventBridge(suite_manager, event_bus)
enforcement = EnforcementExecutor(suite_manager)
engine = RiskEngine(config, event_bus)
engine.enforcement_executor = enforcement

await suite_manager.add_instrument("MNQ")
await event_bridge.start()
await engine.start()
```

---

## 8. Best Practices

### 8.1 From Examples

1. **Use High-Level API for Simplicity**
   - `RiskManager.create()` handles all wiring
   - Dict-based rules for quick setup
   - Event decorators for clean handlers

2. **Use Manual Assembly for Control**
   - Direct component access
   - Custom initialization order
   - Fine-grained configuration

3. **Subscribe to Multiple Events**
   - `rule_violated` - Know when rules break
   - `enforcement_action` - Know when enforcement happens
   - `position_updated` - Track real-time positions
   - `order_filled` - Track trade execution

4. **Handle Graceful Shutdown**
   ```python
   try:
       await rm.wait_until_stopped()
   except KeyboardInterrupt:
       await rm.stop()
   ```

5. **Track Per-Instrument Stats**
   - Maintain local state in event handlers
   - Aggregate for portfolio view
   - Use for custom logic/alerts

---

### 8.2 From API Documentation

1. **Always Use Correct Parameter Names**
   ```python
   # ✅ CORRECT
   RiskEvent(event_type=EventType.POSITION_UPDATED)
   PnLTracker(db=database_instance)
   RiskRule(action="flatten")

   # ❌ WRONG
   RiskEvent(type=EventType.POSITION_UPDATED)
   PnLTracker(account_id="ACCT-001")
   RiskRule(name="MyRule", engine=engine)
   ```

2. **Check Actual Implementation Before Writing Tests**
   ```python
   import inspect
   from risk_manager.core.events import RiskEvent

   # See actual signature
   print(inspect.signature(RiskEvent.__init__))
   ```

3. **Use SDK Methods, Don't Reinvent**
   - SDK handles WebSocket, reconnection, auth
   - We add risk logic on top
   - Don't duplicate SDK functionality

4. **Log at Strategic Checkpoints**
   ```python
   # In enforcement
   sdk_logger.warning("⚠️ Enforcement triggered: ACTION - Details")

   # In rules
   logger.info("🔍 Rule evaluated: RULE_NAME - Result")
   ```

5. **Return Structured Results**
   ```python
   # Enforcement methods return consistent format
   {"success": bool, "closed": int, "errors": list}
   {"success": bool, "error": str | None}
   ```

---

## 9. API Consistency Analysis

### 9.1 Known Mismatches (Fixed)

| Test Expectation | Actual Implementation | Status |
|------------------|----------------------|--------|
| `RiskEvent(type=...)` | `RiskEvent(event_type=...)` | ✅ Fixed - Added `ORDER_UPDATED` and `TRADE_EXECUTED` to enum |
| `EventType.TRADE_EXECUTED` | Not originally defined | ✅ Fixed - Added to EventType enum |
| `EventType.ORDER_UPDATED` | Not originally defined | ✅ Fixed - Added to EventType enum |
| `PnLTracker(account_id=...)` | `PnLTracker(db=...)` | ⚠️ Tests must use correct signature |

---

### 9.2 SDK vs Our Implementation

**What SDK Provides** (don't reimplement):
- WebSocket connection (SignalR)
- Authentication
- Order management
- Position management
- Market data
- Auto-reconnection
- Event system (SDK's EventBus)

**What We Add** (risk layer):
- Custom EventType enum (risk events)
- RiskEvent class (our event wrapper)
- RiskRule system (evaluation logic)
- P&L tracking (state persistence)
- Enforcement execution (using SDK methods)
- EventBridge (SDK events → risk events)
- Risk-specific logging checkpoints

---

### 9.3 Naming Conventions

**EventType Values**:
- Past tense for completed actions: `POSITION_OPENED`, `ORDER_FILLED`, `TRADE_EXECUTED`
- Present participle for ongoing: `POSITION_UPDATED`
- Descriptive for alerts: `RULE_VIOLATED`, `ENFORCEMENT_ACTION`

**Method Names**:
- Async methods: `async def method_name()`
- Get methods: `get_*()` or `get_*_status()`
- Action methods: `close_*()`, `cancel_*()`, `flatten_*()`
- Event handlers: `_on_*()` (private)

**Return Types**:
- Enforcement results: `dict[str, Any]` with `success`, `errors`, counts
- Queries: Specific types (`float`, `int`, `dict`, `list`)
- Events: `RiskEvent` instances

---

## 10. Common Patterns Summary

### 10.1 Creating Risk Manager

```python
# Simple
rm = await RiskManager.create(
    instruments=["MNQ"],
    rules={"max_daily_loss": -500.0}
)

# Advanced
rm = await RiskManager.create(instruments=["MNQ"])
rm.add_rule(DailyLossRule(limit=-500.0, action="flatten"))
```

### 10.2 Subscribing to Events

```python
@rm.on("rule_violated")
async def handler(event: RiskEvent):
    print(event.data["message"])
```

### 10.3 Enforcement Execution

```python
# Via EnforcementExecutor
result = await enforcement.close_all_positions("MNQ")

# Via RiskEngine (wired to TradingIntegration)
await engine.flatten_all_positions()
```

### 10.4 State Tracking

```python
# P&L tracking
tracker = PnLTracker(db)
tracker.add_trade_pnl("ACCT-001", -150.0)
daily_pnl = tracker.get_daily_pnl("ACCT-001")
```

### 10.5 SDK Suite Management

```python
# Add instrument
suite = await suite_manager.add_instrument("MNQ")

# Get suite
suite = suite_manager.get_suite("MNQ")

# Use SDK methods
await suite.positions.close_all_positions()
```

---

## 11. Reference Quick Links

**API Signatures**:
- `RiskEvent(event_type, timestamp?, data?, source?, severity?)`
- `PnLTracker(db)`
- `RiskRule(action="alert")`
- `SuiteManager(event_bus)`
- `EnforcementExecutor(suite_manager)`
- `EventBridge(suite_manager, risk_event_bus)`

**Event Types** (24 total):
- Position: `POSITION_OPENED`, `POSITION_CLOSED`, `POSITION_UPDATED`
- Order: `ORDER_PLACED`, `ORDER_FILLED`, `ORDER_CANCELLED`, `ORDER_REJECTED`, `ORDER_UPDATED`
- Risk: `RULE_VIOLATED`, `RULE_WARNING`, `ENFORCEMENT_ACTION`
- P&L: `PNL_UPDATED`, `DAILY_LOSS_LIMIT`, `DRAWDOWN_ALERT`
- Trade: `TRADE_EXECUTED`
- System: `SYSTEM_STARTED`, `SYSTEM_STOPPED`, `CONNECTION_LOST`, `CONNECTION_RESTORED`
- AI: `PATTERN_DETECTED`, `ANOMALY_DETECTED`, `AI_ALERT`

**Enforcement Actions**:
- `close_all_positions(symbol?)` → `{"success", "closed", "errors"}`
- `close_position(symbol, contract_id)` → `{"success", "error"}`
- `reduce_position_to_limit(symbol, contract_id, target_size)` → `{"success", "error"}`
- `cancel_all_orders(symbol?)` → `{"success", "cancelled", "errors"}`
- `cancel_order(symbol, order_id)` → `{"success", "error"}`
- `flatten_and_cancel(symbol?)` → `{"success", "closed", "cancelled", "errors"}`

---

## 12. Conclusion

This technical reference inventory documents the **actual APIs** as implemented, preventing test/code mismatches. Key takeaways:

1. **We define our own event system** (RiskEvent, EventType, EventBus) on top of SDK
2. **Parameter names matter** (`event_type` not `type`, `db` not `account_id`)
3. **Enforcement flows through 3 layers** (Engine → TradingIntegration → SDK)
4. **Examples show 4 usage patterns** (basic, advanced, multi-instrument, manual SDK)
5. **SDK handles infrastructure**, we add risk logic on top
6. **All enforcement returns structured results** for consistent error handling

**Always verify API contracts before writing tests!**

---

**Files Referenced**:
- `SDK_API_REFERENCE.md` - API contract documentation
- `SDK_ENFORCEMENT_FLOW.md` - Enforcement wiring explanation
- `examples/01_basic_usage.py` - Simple usage pattern
- `examples/02_advanced_rules.py` - Custom rules pattern
- `examples/03_multi_instrument.py` - Portfolio pattern
- `examples/04_sdk_integration.py` - Manual SDK assembly pattern
- `src/risk_manager/core/events.py` - Event system implementation
- `src/risk_manager/state/pnl_tracker.py` - P&L tracking implementation
- `src/risk_manager/rules/base.py` - Rule base class
- `src/risk_manager/sdk/suite_manager.py` - SDK suite management
- `src/risk_manager/sdk/enforcement.py` - Enforcement execution
- `src/risk_manager/sdk/event_bridge.py` - Event bridging
