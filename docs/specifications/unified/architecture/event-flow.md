# Event Flow Architecture

**Document ID:** ARCH-UNIFIED-002
**Version:** 1.0
**Created:** 2025-10-27
**Status:** Production Specification

---

## Executive Summary

This document provides detailed event flow diagrams and sequence flows for the Risk Manager V34 architecture. It clarifies how events flow from the TopstepX platform through the SDK to risk rules and enforcement actions.

**Key Architectural Patterns:**
1. **SignalR Direct Callbacks**: Subscribe to `realtime.add_callback()` NOT `suite.on()`
2. **Event-Driven**: All rule evaluations triggered by real-time events
3. **Async Throughout**: Full async/await pattern from SDK to enforcement
4. **8-Checkpoint Logging**: Strategic log points for runtime debugging

---

## 1. Complete Event Flow (High-Level)

```
┌───────────────────────────────────────────────────────────────┐
│                    TOPSTEPX PLATFORM                          │
│  Trader executes order → Position opened → Trade executed     │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ SignalR WebSocket (Gateway Hub)
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│              PROJECT-X-PY SDK (TradingSuite)                  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ProjectXRealtimeClient (SignalR Hub Proxy)              │ │
│  │  - Connected to User Hub                                │ │
│  │  - Connected to Market Hub                              │ │
│  │  - Receives: position_update, order_update, trade_update│ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ realtime.add_callback()
                         │ (CRITICAL: Must use direct callbacks!)
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│           TRADINGINTEGRATION (SDK Wrapper)                    │
│            src/risk_manager/integrations/trading.py           │
│                                                               │
│  async def _on_position_update(data):                         │
│      # Parse SignalR data format                             │
│      risk_event = RiskEvent(                                 │
│          event_type=EventType.POSITION_UPDATED,              │
│          data={"symbol": "MNQ", "size": 2, ...}              │
│      )                                                        │
│      await event_bus.publish(risk_event)                     │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ RiskEvent published
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                   RISK EVENTBUS                               │
│                  src/core/events.py                           │
│                                                               │
│  Simple pub/sub system                                       │
│  - Subscribers: RiskEngine, Monitoring, PnL Tracker          │
│  - Async event distribution                                  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ Event distributed to subscribers
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                    RISK ENGINE                                │
│                 src/core/engine.py                            │
│                                                               │
│  async def evaluate_rules(event):                            │
│      # 📨 Checkpoint 6: Event received                       │
│      logger.info("📨 Event received: POSITION_UPDATED")      │
│                                                               │
│      for rule in self.rules:                                 │
│          violation = await rule.evaluate(event, self)        │
│          # 🔍 Checkpoint 7: Rule evaluated                   │
│          if violation:                                       │
│              await self._handle_violation(rule, violation)   │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ Rule.evaluate() called
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                    RISK RULES                                 │
│                 src/rules/*.py                                │
│                                                               │
│  Example: DailyRealizedLossRule                              │
│                                                               │
│  async def evaluate(event, engine):                          │
│      if event.event_type != EventType.TRADE_EXECUTED:        │
│          return None  # Ignore                               │
│                                                               │
│      pnl = event.data.get("pnl")                             │
│      daily_pnl = await self.pnl_tracker.add_trade_pnl(pnl)  │
│                                                               │
│      if daily_pnl <= self.config.daily_loss_limit:           │
│          return {                                            │
│              "action": "flatten",                            │
│              "reason": f"Daily loss: ${daily_pnl:.2f}"       │
│          }                                                   │
│                                                               │
│      return None  # No violation                             │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ Violation detected
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│            RISKENGINE._handle_violation()                     │
│                                                               │
│  # ⚠️ Checkpoint 8: Enforcement triggered                    │
│  logger.warning("⚠️ Enforcement: FLATTEN ALL")               │
│                                                               │
│  if action == "flatten":                                     │
│      await self.flatten_all_positions()                      │
│                                                               │
│  # Publish enforcement event                                 │
│  await event_bus.publish(ENFORCEMENT_ACTION)                 │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ Execute enforcement
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│         RISKENGINE.flatten_all_positions()                    │
│                                                               │
│  if self.trading_integration:                                │
│      await self.trading_integration.flatten_all()            │
│  else:                                                        │
│      logger.warning("TradingIntegration not connected")      │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ Call TradingIntegration
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│         TRADINGINTEGRATION.flatten_all()                      │
│                                                               │
│  for symbol in self.instruments:                             │
│      await self.flatten_position(symbol)                     │
│                                                               │
│  async def flatten_position(symbol):                         │
│      context = self.suite[symbol]                            │
│      await context.positions.close_all_positions()           │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ SDK API call
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│              PROJECT-X-PY SDK                                 │
│        PositionManager.close_all_positions()                  │
│                                                               │
│  Makes REST API call:                                        │
│  POST /api/Position/closeAllPositions                        │
│  Authorization: Bearer <JWT>                                 │
│  Body: {"accountId": 123}                                    │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ REST API call
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│              TOPSTEPX PLATFORM REST API                       │
│                                                               │
│  Receives close_all_positions request                        │
│  - Validates account ID                                      │
│  - Closes all open positions                                 │
│  - Sends position_update via SignalR                         │
│                                                               │
│  ✅ Positions actually closed!                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. Two Event Subscription Patterns

### Pattern A: Direct Realtime Callbacks (WORKING)

**Used by:** TradingIntegration

```python
# src/risk_manager/integrations/trading.py

async def start(self):
    """Start monitoring trading events via realtime callbacks."""

    # ✅ CORRECT: Subscribe to realtime callbacks
    await self.realtime.add_callback(
        "position_update",
        lambda data: asyncio.create_task(self._on_position_update(data))
    )

    await self.realtime.add_callback(
        "order_update",
        lambda data: asyncio.create_task(self._on_order_update(data))
    )

    await self.realtime.add_callback(
        "trade_update",
        lambda data: asyncio.create_task(self._on_trade_update(data))
    )

async def _on_position_update(self, data: Any) -> None:
    """Handle position update from SignalR."""
    # Parse SignalR data format: [{'action': 1, 'data': {...}}]
    for update in data:
        action = update.get('action', 0)
        position_data = update.get('data', {})

        # Convert to RiskEvent
        risk_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": symbol,
                "contract_id": position_data.get('contractId'),
                "size": position_data.get('size', 0),
                "unrealized_pnl": position_data.get('unrealizedPnl', 0.0),
            }
        )

        # Publish to Risk EventBus
        await self.event_bus.publish(risk_event)
```

**Why this works:**
- SignalR sends position/order/trade events to `realtime_client` callbacks
- These callbacks are the ONLY way to receive these events
- SDK EventBus does NOT emit these events (by design)

---

### Pattern B: SDK EventBus (DOESN'T WORK for position/order/trade)

```python
# ❌ INCORRECT: SDK EventBus doesn't emit position/order/trade events

async def start(self):
    """This won't work for SignalR events!"""

    # These events NEVER fire for position updates from SignalR
    await suite.on(
        EventType.POSITION_UPDATED,
        lambda event: self._on_position_update(event)
    )

    # Why? The SDK only emits these for:
    # - Internal state changes
    # - Manual position modifications
    # - NOT for SignalR WebSocket events!
```

**Why this doesn't work:**
- SDK EventBus is for SDK-generated events (strategy signals, internal state)
- SignalR events bypass the SDK EventBus entirely
- Must use `realtime.add_callback()` for real-time trading events

---

## 3. Async Pattern Throughout

### Asyncio Event Loop Coordination

```
┌────────────────────────────────────────────────────────────┐
│  Main Event Loop (asyncio.run())                           │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  RiskManager.start()                                 │ │
│  │    - Starts TradingIntegration                       │ │
│  │    - Starts RiskEngine                               │ │
│  │    - Starts background tasks                         │ │
│  │    - Keeps running until stop signal                 │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  SignalR Event Loop (inside SDK)                     │ │
│  │    - Receives WebSocket messages                     │ │
│  │    - Fires callbacks asynchronously                  │ │
│  │    - Callbacks create tasks: asyncio.create_task()   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Event Processing Tasks (concurrent)                 │ │
│  │    - Each callback spawns async task                 │ │
│  │    - Multiple events processed concurrently          │ │
│  │    - Tasks coordinate via EventBus                   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Background Tasks                                    │ │
│  │    - Position polling (every 5 seconds)              │ │
│  │    - Lockout expiry check (every 1 second)           │ │
│  │    - Daily reset check (every 1 minute)              │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Key Pattern:**
```python
# Callback must spawn async task (can't block SignalR loop)
await self.realtime.add_callback(
    "position_update",
    lambda data: asyncio.create_task(self._on_position_update(data))
    #             ^^^^^^^^^^^^^^^^^^^^ CRITICAL: Create task, don't await!
)

async def _on_position_update(self, data):
    # This runs concurrently with other events
    # Can safely await without blocking SignalR
    await self.event_bus.publish(risk_event)
```

---

## 4. Rule Category Event Flows

### Category 1: Trade-by-Trade Rules (Immediate Enforcement)

**Rules:** RULE-001 (MaxContracts), RULE-002 (MaxContractsPerInstrument)

```
Event: POSITION_UPDATED
│
├─> Rule: MaxContracts
│   ├─ Count net contracts across all positions
│   ├─ Check: total_contracts > limit?
│   └─ If YES: return {"action": "flatten", "reason": "Max contracts exceeded"}
│
└─> Enforcement: Immediate
    ├─ Flatten all positions (or reduce to limit)
    └─ No lockout (trader can re-enter immediately)
```

**Sequence Diagram:**
```
TopstepX    SDK Realtime    TradingInteg    EventBus    RiskEngine    MaxContractsRule    TradingInteg    TopstepX
    │            │               │             │            │                │                 │            │
    │─position───>│               │             │            │                │                 │            │
    │  update    │               │             │            │                │                 │            │
    │            │─callback────> │             │            │                │                 │            │
    │            │               │─RiskEvent──>│            │                │                 │            │
    │            │               │             │─publish───>│                │                 │            │
    │            │               │             │            │─evaluate──────>│                 │            │
    │            │               │             │            │                │─count contracts │            │
    │            │               │             │            │                │─check limit     │            │
    │            │               │             │            │<─violation─────│                 │            │
    │            │               │             │            │─flatten_all───────────────────> │            │
    │            │               │             │            │                │                 │─close API─>│
    │            │               │             │            │                │                 │            │─✅
    │<───────────position_update (size=0)───────────────────────────────────────────────────────────────────│
```

---

### Category 2: Hard Lockout Rules (Lock Until Reset)

**Rules:** RULE-003 (DailyRealizedLoss), RULE-004 (DailyUnrealizedLoss), RULE-013 (DailyRealizedProfit)

```
Event: TRADE_EXECUTED (realized P&L)
│
├─> Rule: DailyRealizedLoss
│   ├─ Extract realized_pnl from event
│   ├─ Update daily P&L tracker: daily_pnl += realized_pnl
│   ├─ Check: daily_pnl <= limit?
│   └─ If YES: return {
│       "action": "flatten",
│       "lockout": "until_reset",
│       "reset_time": "17:00 ET",
│       "reason": "Daily loss limit hit"
│   }
│
└─> Enforcement: Flatten + Hard Lockout
    ├─ Flatten all positions immediately
    ├─ Set lockout state until 17:00 ET
    ├─ Event Router blocks all new position events
    └─ Trader CLI displays lockout countdown
```

**Sequence Diagram:**
```
TopstepX    SDK Realtime    TradingInteg    EventBus    RiskEngine    DailyLossRule    LockoutMgr    EventRouter
    │            │               │             │            │                │             │              │
    │─trade_exec─>│               │             │            │                │             │              │
    │            │─callback────> │             │            │                │             │              │
    │            │               │─RiskEvent──>│            │                │             │              │
    │            │               │             │─publish───>│                │             │              │
    │            │               │             │            │─evaluate──────>│             │              │
    │            │               │             │            │                │─update_pnl  │              │
    │            │               │             │            │                │─check limit │              │
    │            │               │             │            │<─violation─────│             │              │
    │            │               │             │            │─flatten_all──> │             │              │
    │            │               │             │            │─set_lockout────────────────> │              │
    │            │               │             │            │                │             │─persist_db   │
    │            │               │             │            │                │             │              │
    │─position──>│               │             │            │                │             │              │
    │  update    │─callback────> │             │            │                │             │              │
    │            │               │─RiskEvent──>│            │                │             │              │
    │            │               │             │─check_lockout──────────────────────────────────────────> │
    │            │               │             │            │                │             │<─is_locked───│
    │            │               │             │            │<─BLOCKED───────────────────────────────────  │
    │            │               │             │            │─close_position──────────────────────────────>│
    │            │               │             │            │                │             │              │
```

---

### Category 3: Configurable Timer Lockout (Cooldown Period)

**Rules:** RULE-006 (TradeFrequencyLimit), RULE-007 (CooldownAfterLoss)

```
Event: TRADE_EXECUTED
│
├─> Rule: TradeFrequencyLimit
│   ├─ Count trades in last N minutes
│   ├─ Check: trade_count > per_minute_limit?
│   └─ If YES: return {
│       "action": "alert",
│       "lockout": "cooldown",
│       "duration_seconds": 60,
│       "reason": "Trade frequency exceeded"
│   }
│
└─> Enforcement: Cooldown Timer
    ├─ No position flattening (warning only)
    ├─ Set cooldown timer (60 seconds)
    ├─ Event Router blocks new position events during cooldown
    ├─ Timer auto-expires after duration
    └─ Trading resumes automatically
```

**Sequence Diagram:**
```
TopstepX    SDK Realtime    TradingInteg    EventBus    RiskEngine    FreqLimitRule    LockoutMgr    TimerMgr
    │            │               │             │            │                │             │            │
    │─trade_exec─>│               │             │            │                │             │            │
    │            │─callback────> │             │            │                │             │            │
    │            │               │─RiskEvent──>│            │                │             │            │
    │            │               │             │─publish───>│                │             │            │
    │            │               │             │            │─evaluate──────>│             │            │
    │            │               │             │            │                │─count trades│            │
    │            │               │             │            │                │─check limit │            │
    │            │               │             │            │<─violation─────│             │            │
    │            │               │             │            │─set_cooldown───────────────> │            │
    │            │               │             │            │                │             │─start_timer────>│
    │            │               │             │            │                │             │            │─schedule(60s)
    │            │               │             │            │                │             │            │
    │─(60 seconds pass)─────────────────────────────────────────────────────────────────────────────────│
    │            │               │             │            │                │             │<─expired────│
    │            │               │             │            │                │             │─clear_lockout│
    │            │               │             │            │                │             │              │
```

---

## 5. Error Handling Flows

### Scenario 1: SignalR Disconnect

```
TopstepX    SDK Realtime    TradingInteg    RiskEngine
    │            │               │             │
    │─x─x─x─x─x─>│               │             │  (connection lost)
    │            │─disconnect──> │             │
    │            │  event        │─log error   │
    │            │               │             │
    │            │<─reconnect────│             │  (auto-reconnect)
    │            │  attempt      │             │
    │<───────────│               │             │
    │─connected──>│               │             │  (connection restored)
    │            │─reconnected─> │             │
    │            │  event        │─log success │
    │            │               │             │
    │            │─resubscribe───>│            │  (re-register callbacks)
    │            │  callbacks    │             │
```

**Handling:**
```python
async def connect(self):
    """Connect with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await self.realtime.connect()
            logger.success("✅ Connected to SignalR")
            return
        except Exception as e:
            logger.error(f"Connection attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
            else:
                raise
```

---

### Scenario 2: Rule Evaluation Exception

```
EventBus    RiskEngine    MaxContractsRule
    │            │                │
    │─event─────>│                │
    │            │─evaluate──────>│
    │            │                │─❌ exception (e.g., KeyError)
    │            │<─exception─────│
    │            │─log error      │
    │            │─continue       │  (don't fail entire evaluation)
    │            │  with other    │
    │            │  rules         │
```

**Handling:**
```python
async def evaluate_rules(self, event: RiskEvent) -> None:
    """Evaluate all rules against an event."""
    for rule in self.rules:
        try:
            violation = await rule.evaluate(event, self)
            if violation:
                await self._handle_violation(rule, violation)
        except Exception as e:
            # Log error but continue with other rules
            logger.error(f"Error evaluating rule {rule.__class__.__name__}: {e}")
            # Don't propagate - continue with remaining rules
```

---

### Scenario 3: Enforcement Failure

```
RiskEngine    TradingInteg    SDK PositionMgr    TopstepX
    │              │                 │               │
    │─flatten_all─>│                 │               │
    │              │─close_all───────>│               │
    │              │                 │─API call─────>│
    │              │                 │               │─❌ rejected
    │              │                 │<──error───────│
    │              │<─exception──────│               │
    │<─failed──────│                 │               │
    │─log critical │                 │               │
    │─retry once   │                 │               │
    │─flatten_all─>│                 │               │
    │              │─close_all───────>│               │
    │              │                 │─API call─────>│
    │              │                 │               │─✅ success
```

**Handling:**
```python
async def flatten_all_positions(self) -> None:
    """Flatten all open positions with retry."""
    if self.trading_integration:
        try:
            await self.trading_integration.flatten_all()
            logger.success("✅ All positions flattened")
        except Exception as e:
            logger.error(f"❌ Failed to flatten positions: {e}")
            # Retry once
            logger.warning("Retrying enforcement...")
            try:
                await asyncio.sleep(2)
                await self.trading_integration.flatten_all()
                logger.success("✅ Retry succeeded")
            except Exception as e2:
                logger.critical(f"❌ Retry failed: {e2}")
                # Publish critical alert
                await self.event_bus.publish(RiskEvent(
                    event_type=EventType.ENFORCEMENT_FAILED,
                    data={"error": str(e2)},
                    severity="critical"
                ))
```

---

## 6. Component Responsibility Matrix

| Component | Initiates | Responds To | Publishes | Calls |
|-----------|-----------|-------------|-----------|-------|
| **TopstepX Platform** | Trading events | REST API calls | SignalR events | N/A |
| **SDK RealtimeClient** | Reconnect attempts | SignalR messages | Callbacks | N/A |
| **TradingIntegration** | None | Realtime callbacks | RiskEvents | SDK methods |
| **EventBus** | None | publish() calls | Events to subscribers | Subscriber callbacks |
| **RiskEngine** | Rule evaluation | RiskEvents | Enforcement events | Rule.evaluate(), TradingIntegration |
| **Risk Rules** | None | evaluate() calls | None (returns violations) | State trackers (PnL, frequency) |
| **LockoutManager** | Lockout expiry check | set_lockout() calls | Lockout events | Database |
| **EventRouter** | None | All events | Filtered events | LockoutManager.is_locked_out() |
| **TimerManager** | Timer expiry check | start_timer() calls | Timer events | Callback functions |

---

## 7. 8-Checkpoint Logging in Event Flow

```
Checkpoint 1: 🚀 Service Start
  └─ File: manager.py:start()
  └─ Before: any connections

Checkpoint 2: ✅ Config Loaded
  └─ File: manager.py:_load_config()
  └─ Before: SDK connection

Checkpoint 3: ✅ SDK Connected
  └─ File: trading.py:connect()
  └─ After: SignalR connected + TradingSuite created

Checkpoint 4: ✅ Rules Initialized
  └─ File: manager.py:_add_default_rules()
  └─ After: All rules registered

Checkpoint 5: ✅ Event Loop Running
  └─ File: engine.py:start()
  └─ Before: first event processed

Checkpoint 6: 📨 Event Received
  └─ File: engine.py:evaluate_rules()
  └─ For each event: log event type

Checkpoint 7: 🔍 Rule Evaluated
  └─ File: engine.py:evaluate_rules()
  └─ For each rule: log PASSED or VIOLATED

Checkpoint 8: ⚠️ Enforcement Triggered
  └─ File: engine.py:_handle_violation()
  └─ For each enforcement: log action taken
```

**Example log sequence:**
```
2025-10-27 14:30:00 | INFO  | 🚀 Service Start: Risk Manager initializing
2025-10-27 14:30:01 | INFO  | ✅ Config Loaded: 12 rules configured
2025-10-27 14:30:03 | INFO  | ✅ SDK Connected: account_id=123, balance=$50,000
2025-10-27 14:30:03 | INFO  | ✅ Rules Initialized: 2 rules active
2025-10-27 14:30:04 | INFO  | ✅ Event Loop Running: 2 active rules monitoring events
2025-10-27 14:35:12 | INFO  | 📨 Event received: TRADE_EXECUTED - evaluating 2 rules
2025-10-27 14:35:12 | INFO  | 🔍 Rule evaluated: MaxContracts → PASSED
2025-10-27 14:35:12 | INFO  | 🔍 Rule evaluated: DailyRealizedLossRule → VIOLATED
2025-10-27 14:35:12 | WARN  | ⚠️ Enforcement triggered: FLATTEN ALL - Rule: DailyRealizedLossRule
2025-10-27 14:35:13 | INFO  | ✅ All positions flattened via SDK
```

---

## 8. Reference Implementation Files

| Component | File | Lines | Key Methods |
|-----------|------|-------|-------------|
| **TradingIntegration** | `src/risk_manager/integrations/trading.py` | 421 | `connect()`, `start()`, `_on_position_update()`, `flatten_all()` |
| **EventBus** | `src/risk_manager/core/events.py` | ~150 | `publish()`, `subscribe()`, `unsubscribe()` |
| **RiskEngine** | `src/risk_manager/core/engine.py` | 183 | `evaluate_rules()`, `_handle_violation()`, `flatten_all_positions()` |
| **EventBridge** | `src/risk_manager/sdk/event_bridge.py` | 380 | `_subscribe_to_suite()`, `_on_position_update()` |

---

## 9. Related Documentation

- **System Architecture**: `system-architecture.md` - High-level architecture
- **SDK Integration**: `../integration/event-handling.md` - SDK event patterns
- **Enforcement Flow**: `SDK_ENFORCEMENT_FLOW.md` (root) - Complete enforcement chain
- **Daemon Lifecycle**: `daemon-lifecycle.md` - Service startup/shutdown

---

**Document Status:** Complete
**Last Updated:** 2025-10-27
**Next Review:** When adding new event types or changing event patterns
