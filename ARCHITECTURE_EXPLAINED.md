# Risk Manager Architecture - What You Already Have

**TL;DR**: You already built the system! It's just not fully wired yet. Let me show you what exists and the small gaps.

---

## 🎯 The Big Picture (How It Works)

```
┌─────────────────────────────────────────────────────────────┐
│                      BROKER (Project-X)                      │
│  (Orders, Positions, Trades, P&L, Market Data)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Events via SignalR/WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  TradingIntegration (src/integrations/trading.py)           │
│  - Receives broker events (callbacks)                        │
│  - Transforms to RiskEvent objects                           │
│  - Publishes to EventBus                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ RiskEvent objects
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  EventBus (src/core/events.py)                               │
│  - Simple pub/sub message bus                                │
│  - Routes events to subscribers                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Subscribers get events
                     ├──────────────┬──────────────┐
                     ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ RiskManager  │ │ AI Module    │ │ Monitoring   │
│ (Manager.py) │ │ (optional)   │ │ (optional)   │
└──────┬───────┘ └──────────────┘ └──────────────┘
       │
       │ Calls evaluate_rules()
       ▼
┌─────────────────────────────────────────────────────────────┐
│  RiskEngine (src/core/engine.py)                             │
│  - Has list of Rule objects                                  │
│  - For each event: calls rule.evaluate()                     │
│  - Collects violations                                       │
│  - Triggers enforcement actions                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ If violation: Take action
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Enforcement (via TradingIntegration)                        │
│  - Flatten positions                                         │
│  - Close positions                                           │
│  - Pause trading                                            │
│  - Send alerts                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ What You Already Have (The Good News!)

### 1. **EventBus** ✅
**Location**: `src/risk_manager/core/events.py`

**What it does**: Simple pub/sub message bus

```python
# Anyone can publish
event_bus.publish(RiskEvent(...))

# Anyone can subscribe
event_bus.subscribe(EventType.POSITION_UPDATED, handler_function)
```

**Status**: ✅ Implemented and working

---

### 2. **TradingIntegration** ✅
**Location**: `src/risk_manager/integrations/trading.py`

**What it does**:
- Connects to Project-X SDK
- Receives broker events (ORDER_PLACED, ORDER_FILLED, POSITION_UPDATED, etc.)
- Transforms to RiskEvent objects
- **Publishes to EventBus** ✅

**Key code** (already in trading.py):
```python
# Line 416: Publishes events to EventBus
risk_event = RiskEvent(
    event_type=EventType.ORDER_PLACED,
    data={...},
    source="trading_sdk",
)
await self.event_bus.publish(risk_event)
```

**Status**: ✅ Fully implemented - already publishing events!

---

### 3. **RiskEngine** ✅
**Location**: `src/risk_manager/core/engine.py`

**What it does**:
- Holds list of Rule objects
- `evaluate_rules(event)` - calls each rule
- `_handle_violation()` - triggers enforcement
- `flatten_all_positions()` - enforcement actions

**Key code**:
```python
# Line 67-96: Rule evaluation loop
async def evaluate_rules(self, event: RiskEvent):
    violations = []
    for rule in self.rules:
        violation = await rule.evaluate(event, self)  # Pass engine as context
        if violation:
            await self._handle_violation(rule, violation)
            violations.append(violation)
    return violations
```

**Status**: ✅ Implemented and ready to use

---

### 4. **RiskManager** (Coordinator) ✅
**Location**: `src/risk_manager/core/manager.py`

**What it does**:
- Creates EventBus
- Creates RiskEngine
- Creates TradingIntegration
- **Subscribes to events** ✅
- Routes events to RiskEngine

**Key code** (already in manager.py):
```python
# Line 250-251: Event subscription
self.event_bus.subscribe(EventType.ORDER_FILLED, self._handle_fill)
self.event_bus.subscribe(EventType.POSITION_UPDATED, self._handle_position_update)

# Line 283-289: Event handlers
async def _handle_fill(self, event: RiskEvent):
    await self.engine.evaluate_rules(event)  # ← Passes to engine!

async def _handle_position_update(self, event: RiskEvent):
    await self.engine.evaluate_rules(event)
```

**Status**: ✅ Already wired! Events flow to engine!

---

### 5. **State Management** ✅
**Location**: `src/risk_manager/state/`

**Files**:
- `database.py` - SQLite storage
- `pnl_tracker.py` - Tracks daily P&L
- `lockout_manager.py` - Manages account locks
- `timer_manager.py` - Tracks cooldowns
- `reset_scheduler.py` - Daily resets

**What it does**:
- Accumulates data across events (daily P&L, trade count)
- Persists state to SQLite
- Provides query interface for rules

**Status**: ✅ Implemented

---

### 6. **Risk Rules** ✅
**Location**: `src/risk_manager/rules/`

**Examples**:
- `daily_realized_loss.py` - Daily loss limit
- `max_contracts_per_instrument.py` - Position size limit
- `no_stop_loss_grace.py` - Stop loss required
- `trade_frequency_limit.py` - Max trades per day
- Many more...

**Interface** (all rules have this):
```python
class SomeRule:
    async def evaluate(self, event: RiskEvent, context: RiskEngine):
        # Check if rule is violated
        if violation_detected:
            return {
                "passed": False,
                "message": "Daily loss limit exceeded",
                "action": "flatten"  # or "close_position", "alert"
            }
        return None  # No violation
```

**Status**: ✅ Many rules implemented

---

## 🔴 What's Missing (The Small Gaps)

### Gap 1: Rules Aren't Added to Engine

**Problem**: Rules exist but aren't loaded

**Location**: `manager.py` line 221
```python
logger.warning("⚠️ Rule loading from config is not yet fully implemented")
```

**What's needed**: Add rules to engine in `_add_default_rules()`

**The fix**:
```python
# Add each rule
daily_loss_rule = DailyRealizedLossRule(config=self.config, pnl_tracker=pnl_tracker)
self.engine.add_rule(daily_loss_rule)

max_position_rule = MaxContractsPerInstrumentRule(config=self.config)
self.engine.add_rule(max_position_rule)

# etc...
```

**Why it's not done**: Rules need different parameters (some need tick data, some need state managers)

---

### Gap 2: Only 2 Event Types Subscribed

**Current** (`manager.py` line 250-251):
```python
self.event_bus.subscribe(EventType.ORDER_FILLED, self._handle_fill)
self.event_bus.subscribe(EventType.POSITION_UPDATED, self._handle_position_update)
```

**Missing**:
- ORDER_PLACED
- ORDER_CANCELLED
- POSITION_OPENED
- POSITION_CLOSED
- MARKET_DATA_UPDATED
- etc...

**Why**: Started with minimum, need to add more

**The fix**: Add more subscriptions (simple, just more lines)

---

### Gap 3: Context Building Isn't Formalized

**Current**: Rules get `engine` as context
```python
violation = await rule.evaluate(event, self)  # self = RiskEngine
```

**Problem**: Rules query what they need directly from engine:
```python
# Inside rule:
current_pnl = context.daily_pnl  # Access engine state
positions = context.current_positions  # Access engine tracking
```

**Not a gap, just informal**: Rules have access to everything via engine

**Could formalize with RuleContext class** (optional):
```python
class RuleContext:
    def __init__(self, event, engine, state, trading_integration):
        self.event = event
        self.engine = engine
        self.state = state
        self.trading = trading_integration

# Then:
context = RuleContext(event, self, pnl_tracker, trading_integration)
violation = await rule.evaluate(context)
```

**Status**: Not needed yet, works as-is

---

## 🎯 How Data Flows (Complete Picture)

### Example: Position Opened with Stop Loss

```
Step 1: Broker
  └─ You buy 2 MNQ @ $26250
  └─ Broker places stop @ $26240

Step 2: TradingIntegration receives events
  ├─ ORDER_PLACED event (entry order)
  │   └─ Publishes RiskEvent to EventBus ✅
  │
  ├─ ORDER_FILLED event (entry filled)
  │   └─ Publishes RiskEvent to EventBus ✅
  │
  ├─ POSITION_OPENED event
  │   └─ Publishes RiskEvent to EventBus ✅
  │
  └─ ORDER_PLACED event (stop loss order)
      └─ Publishes RiskEvent to EventBus ✅

Step 3: EventBus routes events
  └─ RiskManager subscribed to POSITION_UPDATED ✅
      └─ Calls engine.evaluate_rules(event) ✅

Step 4: RiskEngine evaluates rules
  ├─ For each rule in self.rules:
  │   ├─ MaxPositionSizeRule.evaluate(event, engine)
  │   │   └─ Checks: position size > max?
  │   │   └─ Returns: None (no violation)
  │   │
  │   ├─ NoStopLossRule.evaluate(event, engine)
  │   │   └─ Checks: does position have stop?
  │   │   └─ Queries: trading_integration.get_stop_loss_for_position()
  │   │   └─ Returns: None (stop exists)
  │   │
  │   └─ DailyLossLimitRule.evaluate(event, engine)
  │       └─ Checks: daily_pnl < limit?
  │       └─ Queries: pnl_tracker.get_daily_pnl()
  │       └─ Returns: None (within limit)
  │
  └─ No violations → No action taken

Step 5: If violation detected
  └─ engine._handle_violation(rule, violation)
      ├─ Logs the violation
      ├─ Publishes RULE_VIOLATED event
      └─ Executes action:
          ├─ "flatten" → trading_integration.flatten_all()
          ├─ "close_position" → trading_integration.flatten_position(symbol)
          └─ "alert" → Send notification
```

---

## 📊 Data Organization Answer

> "Do we need a module to organize the data for the rules?"

**Answer: You already have it!**

### 1. **For Accumulated Data** (daily totals, trade counts)
→ **StateManager** (`src/state/`)
   - `PnLTracker` - tracks daily P&L
   - `LockoutManager` - tracks locks
   - `TimerManager` - tracks cooldowns
   - Persists to SQLite

### 2. **For Current Data** (positions, orders)
→ **TradingIntegration** methods
   - `get_stop_loss_for_position(contract_id)`
   - Query SDK: `suite.order_manager.get_working_orders()`
   - Query SDK: `suite.positions.get_all_positions()`

### 3. **For Config Data** (limits, thresholds)
→ **RiskConfig** object
   - Loaded from YAML
   - Passed to rules on creation

### 4. **Context Assembly**
→ **RiskEngine** itself acts as context
   - Rules get: `rule.evaluate(event, engine)`
   - Engine has: `engine.daily_pnl`, `engine.trading_integration`, `engine.config`
   - Rules query what they need

---

## 🔗 How Rules Get What They Need

### Example Rule: Daily Loss Limit

```python
class DailyLossLimitRule:
    def __init__(self, config: RiskConfig, pnl_tracker: PnLTracker):
        self.limit = config.rules.daily_realized_loss.limit
        self.pnl_tracker = pnl_tracker

    async def evaluate(self, event: RiskEvent, context: RiskEngine):
        # Event: POSITION_CLOSED with realized_pnl
        if event.event_type != EventType.POSITION_CLOSED:
            return None  # Don't care about other events

        # Get today's accumulated P&L from state tracker
        daily_pnl = self.pnl_tracker.get_daily_pnl()

        # Get this trade's P&L from event
        trade_pnl = event.data.get("realized_pnl", 0)

        # Calculate new total
        new_total = daily_pnl + trade_pnl

        # Check violation
        if new_total < self.limit:
            return {
                "passed": False,
                "message": f"Daily loss ${new_total} exceeds limit ${self.limit}",
                "action": "flatten",  # Close all positions
                "severity": "critical"
            }

        return None  # No violation
```

**Where data comes from:**
- `self.limit` - From config (passed at construction)
- `daily_pnl` - From PnLTracker (accumulated state)
- `trade_pnl` - From event data (current trade)
- `context` - RiskEngine (for enforcement)

---

## 🎓 The Answer to Your Questions

### Q: "Do we need a module to filter/organize this data?"

**A**: You already have multiple:
- **TradingIntegration** - filters broker events → RiskEvents
- **StateManager** - organizes accumulated data
- **RiskEngine** - routes events to relevant rules

### Q: "How do rules figure out what events they get?"

**A**: They don't subscribe directly. Flow is:
1. **All events** go to EventBus
2. **RiskManager** subscribes to events it cares about
3. **RiskManager** passes events to **RiskEngine**
4. **RiskEngine** calls **all rules** for each event
5. **Rules** check event type and decide if they care:
   ```python
   if event.event_type != EventType.POSITION_CLOSED:
       return None  # I don't care about this event
   ```

### Q: "What do rules check, and how do they get connected?"

**A**:
- **Rules check**: Event data + accumulated state + current positions
- **They get connected**: Via `engine.add_rule(rule)` in `manager._add_default_rules()`
- **They access data**: Via parameters passed at construction + event data + context (engine)

---

## 🎯 What's Actually Missing (Summary)

### Missing Piece #1: Load Rules
**File**: `manager.py` line 177-227
**What**: Uncomment/complete the rule loading code
**Status**: Partially done, needs completion

### Missing Piece #2: Subscribe to More Events
**File**: `manager.py` line 250-251
**What**: Add more event type subscriptions
**Current**: Only ORDER_FILLED and POSITION_UPDATED
**Need**: ORDER_PLACED, POSITION_OPENED, POSITION_CLOSED, etc.

### Missing Piece #3: Stop Loss Query
**File**: `trading.py`
**What**: Already implemented! (you just added it)
**Status**: ✅ `get_stop_loss_for_position()` exists

---

## 💡 The Insight

**You already built 95% of the system!**

What you're missing:
- ✅ EventBus → ✅ Built
- ✅ TradingIntegration → ✅ Publishing events
- ✅ RiskEngine → ✅ Evaluating rules
- ✅ RiskManager → ✅ Wiring it together
- ✅ StateManager → ✅ Tracking data
- ✅ Rules → ✅ Many implemented
- ❌ Loading rules → Need to uncomment/complete
- ❌ More event subscriptions → Need to add

**The gap you're sensing is real, but tiny.**

You need to:
1. Finish `_add_default_rules()` to load rules
2. Add more event subscriptions in `start()`
3. Test it

That's it. The architecture is sound and mostly complete!

---

## 🚀 Next Steps

1. **Read this document** to understand what you have
2. **Check** `manager.py` line 177-227 (rule loading)
3. **Check** `manager.py` line 250-251 (event subscriptions)
4. **Decide**: Which rules to enable first?
5. **Test**: Run `run_dev.py` and watch rules evaluate

The foundation is solid. You're closer than you think! 🎯
