# Complete System Architecture Integration
**Risk Manager V34 - Full System Map**

**Date**: 2025-10-30
**Purpose**: Map the ENTIRE system architecture and show how ALL components interact
**Scope**: Configs, Rules, State Management, Timers, Lockouts, Enforcement, SDK

---

## 🎯 Executive Summary

This document maps the COMPLETE Risk Manager V34 architecture, showing how:
1. **Configuration** drives behavior
2. **13 Rules** coordinate with each other
3. **State Management** (P&L, Lockouts, Timers) persists data
4. **Enforcement** executes actions via SDK
5. **Composite Enforcement** ties it all together

**Key Insight**: The system is NOT a collection of independent rules - it's a coordinated enforcement pipeline where rules share state, respect lockouts, coordinate timers, and enforce actions through a unified SDK layer.

---

## 📐 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CONFIGURATION LAYER                              │
│  risk_config.yaml + timers_config.yaml + accounts.yaml                   │
│  ↓ Defines: Rules, Limits, Schedules, Timers, Lockout Conditions        │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INITIALIZATION LAYER                                │
│  manager.py: Wires everything together                                   │
│  ├─ Creates shared state managers (DB, P&L, Lockouts, Timers)           │
│  ├─ Initializes 13 rules with appropriate dependencies                   │
│  ├─ Connects SDK (TradingSuite, real-time feeds)                         │
│  └─ Starts event loop                                                    │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         RUNTIME LAYER                                    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  STATE MANAGEMENT (Shared across all rules)                        │ │
│  │  ├─ Database (SQLite persistence)                                  │ │
│  │  ├─ PnLTracker (Realized P&L, daily resets)                        │ │
│  │  ├─ LockoutManager (Hard lockouts + cooldowns)                     │ │
│  │  └─ TimerManager (Countdown timers, scheduled tasks)               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                             │                                             │
│                             ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  EVENT ROUTER (engine.py)                                          │ │
│  │  ├─ Receives events from SDK (orders, positions, quotes)           │ │
│  │  ├─ Routes to relevant rules based on event type                   │ │
│  │  ├─ Coordinates rule evaluation (sequential, by priority)          │ │
│  │  └─ Collects violations                                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                             │                                             │
│                             ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  RULE EVALUATION (13 Rules)                                        │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │  CATEGORY 1: Trade-by-Trade (6 rules)                        │ │ │
│  │  │  Action: Close position | Lockout: NONE | Retry: IMMEDIATE   │ │ │
│  │  ├──────────────────────────────────────────────────────────────┤ │ │
│  │  │  - max_contracts                   (RULE-001)                 │ │ │
│  │  │  - max_contracts_per_instrument     (RULE-002)                 │ │ │
│  │  │  - daily_unrealized_loss           (RULE-004) ⭐ COMPOSITE    │ │ │
│  │  │  - max_unrealized_profit           (RULE-005)                 │ │ │
│  │  │  - no_stop_loss_grace              (RULE-008)                 │ │ │
│  │  │  - symbol_blocks                   (RULE-011)                 │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │  CATEGORY 2: Timer/Cooldown (2 rules)                        │ │ │
│  │  │  Action: Flatten all | Lockout: TEMPORARY | Auto-unlock      │ │ │
│  │  ├──────────────────────────────────────────────────────────────┤ │ │
│  │  │  - trade_frequency_limit           (RULE-006) → TimerManager │ │ │
│  │  │  - cooldown_after_loss             (RULE-007) → TimerManager │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │  CATEGORY 3: Hard Lockout (4 rules)                          │ │ │
│  │  │  Action: Flatten all | Lockout: HARD | Until condition met   │ │ │
│  │  ├──────────────────────────────────────────────────────────────┤ │ │
│  │  │  - daily_realized_loss             (RULE-003) → LockoutMgr   │ │ │
│  │  │  - daily_realized_profit           (RULE-013) → LockoutMgr   │ │ │
│  │  │  - session_block_outside           (RULE-009) → TimerManager │ │ │
│  │  │  - auth_loss_guard                 (RULE-010) → LockoutMgr   │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │  CATEGORY 4: Automation (1 rule)                             │ │ │
│  │  │  Action: Modify orders | Lockout: NONE                       │ │ │
│  │  ├──────────────────────────────────────────────────────────────┤ │ │
│  │  │  - trade_management                (RULE-012)                 │ │ │
│  │  │    (Auto breakeven + trailing stop)                          │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  │                                                                     │ │
│  │  Each rule can:                                                    │ │
│  │  ✅ Access shared state (P&L, Lockouts, Timers)                   │ │
│  │  ✅ Check other rules' limits (composite enforcement)             │ │
│  │  ✅ Return violation with enforcement action                      │ │
│  │  ✅ Set lockouts / start timers                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                             │                                             │
│                             ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  ENFORCEMENT EXECUTOR (enforcement.py)                             │ │
│  │  ├─ Receives violations from rules                                 │ │
│  │  ├─ Checks lockout state BEFORE executing                          │ │
│  │  ├─ Executes actions via SDK:                                      │ │
│  │  │  • close_position                                               │ │
│  │  │  • close_all_positions (flatten)                                │ │
│  │  │  • cancel_order                                                 │ │
│  │  │  • modify_order                                                 │ │
│  │  ├─ Sets lockouts/timers AFTER successful enforcement              │ │
│  │  └─ Logs enforcement with full context                             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                             │                                             │
│                             ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  SDK LAYER (trading_integration.py + suite_manager.py)             │ │
│  │  ├─ TradingSuite (per instrument)                                  │ │
│  │  ├─ PositionManager.close_position()                               │ │
│  │  ├─ OrderManager.cancel_order()                                    │ │
│  │  └─ Real-time feeds (orders, positions, quotes)                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Component Deep Dive

### 1. Configuration Layer

**Files**:
- `config/risk_config.yaml` - Rule configurations
- `config/timers_config.yaml` - Timer/schedule configurations
- `config/accounts.yaml` - Account mappings

**Responsibilities**:
- ✅ Enable/disable rules
- ✅ Set limits and thresholds
- ✅ Define schedules and reset times
- ✅ Configure enforcement actions
- ✅ Enable composite enforcement flags

**Example Configuration** (Composite Enforcement):
```yaml
rules:
  # Hard lockout rule
  daily_realized_loss:
    enabled: true
    limit: -900.0
    reset_time: "17:00"
    timezone: "America/Chicago"

  # Trade-by-trade rule WITH composite enforcement
  daily_unrealized_loss:
    enabled: true
    limit: -200.0
    composite_enforcement:
      enabled: true                           # ⭐ Enable composite
      respect_realized_limit: true            # Adjust based on realized P&L
      realized_rule_ref: "daily_realized_loss"  # Which rule to coordinate with
```

---

### 2. State Management Layer

**Components**:

#### 2A: Database (`state/database.py`)
- **Purpose**: SQLite persistence for crash recovery
- **Tables**:
  - `pnl_tracker` - Daily realized P&L
  - `lockouts` - Hard lockouts and cooldowns
  - `rule_violations` - Violation history
- **Features**:
  - Atomic transactions
  - Connection pooling
  - Auto-migration

#### 2B: PnLTracker (`state/pnl_tracker.py`)
- **Purpose**: Track realized P&L (closed trades only)
- **Key Methods**:
  ```python
  add_trade_pnl(account_id: str, pnl: float) -> float
  get_daily_pnl(account_id: str) -> float
  reset_daily_pnl(account_id: str) -> None
  ```
- **Features**:
  - Daily resets at configured time
  - Database persistence
  - Account-wide aggregation
- **Used By**:
  - RULE-003 (daily_realized_loss) ✅
  - RULE-013 (daily_realized_profit) ✅
  - RULE-004 (daily_unrealized_loss) ⭐ NEW for composite enforcement

#### 2C: LockoutManager (`state/lockout_manager.py`)
- **Purpose**: Manage trading lockouts (hard + cooldowns)
- **Lockout Types**:
  1. **Hard Lockout**: Until specific time (e.g., until 5 PM)
  2. **Cooldown**: Duration-based (e.g., 30 minutes)
- **Key Methods**:
  ```python
  set_lockout(account_id, reason, until: datetime) -> None
  set_cooldown(account_id, reason, duration_seconds: int) -> None
  is_locked_out(account_id) -> bool
  get_lockout_info(account_id) -> dict
  clear_lockout(account_id) -> None
  ```
- **Features**:
  - Background task for auto-expiry
  - Database persistence
  - Integration with TimerManager
- **Used By**:
  - RULE-003 (daily_realized_loss) → Hard lockout until reset time
  - RULE-013 (daily_realized_profit) → Hard lockout until reset time
  - RULE-010 (auth_loss_guard) → Hard lockout until API restored
  - RULE-006 (trade_frequency) → Cooldown lockouts
  - RULE-007 (cooldown_after_loss) → Cooldown lockouts

#### 2D: TimerManager (`state/timer_manager.py`)
- **Purpose**: Manage countdown timers with callbacks
- **Key Methods**:
  ```python
  start_timer(name: str, duration: int, callback: Callable) -> None
  get_remaining_time(name: str) -> int
  cancel_timer(name: str) -> None
  ```
- **Features**:
  - In-memory (no persistence)
  - Background task checks every 1 second
  - Automatic callback execution
  - Async/sync callback support
- **Used By**:
  - RULE-006 (trade_frequency) → Cooldown timers
  - RULE-007 (cooldown_after_loss) → Cooldown timers
  - RULE-009 (session_block_outside) → Session checks
  - LockoutManager → Auto-expiry callbacks

---

### 3. Rule Evaluation Layer

**The 13 Rules** (Categorized by Enforcement Type):

#### Category 1: Trade-by-Trade (6 rules)
**Characteristic**: Close only that position, NO lockout, immediate retry allowed

| Rule | File | Triggers On | Action | Lockout |
|------|------|-------------|--------|---------|
| RULE-001 | max_contracts.py | Position opened | Close position | None |
| RULE-002 | max_contracts_per_instrument.py | Position opened | Close position | None |
| **RULE-004** | **daily_unrealized_loss.py** | Unrealized P&L update | Close position | None |
| RULE-005 | max_unrealized_profit.py | Unrealized P&L update | Close position (profit target) | None |
| RULE-008 | no_stop_loss_grace.py | Order placed without stop | Close position after grace | None |
| RULE-011 | symbol_blocks.py | Blocked symbol traded | Close position | None |

**RULE-004 Special Note (Composite Enforcement)**:
```python
class DailyUnrealizedLossRule(RiskRule):
    def __init__(
        self,
        loss_limit: float,
        pnl_tracker: PnLTracker,              # ⭐ NEW: Access to realized P&L
        realized_loss_limit: float,           # ⭐ NEW: Realized limit to respect
        # ...
    ):
        self.loss_limit = loss_limit
        self.pnl_tracker = pnl_tracker
        self.realized_loss_limit = realized_loss_limit

    async def evaluate(self, event, engine):
        # Get unrealized P&L
        unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

        # ⭐ COMPOSITE ENFORCEMENT LOGIC ⭐
        if self.pnl_tracker and self.realized_loss_limit:
            # Get current realized P&L
            realized_pnl = self.pnl_tracker.get_daily_pnl(account_id)

            # Calculate remaining budget
            remaining_budget = self.realized_loss_limit - realized_pnl

            # Adjust effective limit (more conservative wins)
            effective_limit = max(self.loss_limit, remaining_budget)

            # Log adjustment
            if effective_limit != self.loss_limit:
                logger.warning(
                    f"⚙️ COMPOSITE: Limit adjusted {self.loss_limit} → {effective_limit}"
                )

        # Check against effective limit
        if unrealized_pnl <= effective_limit:
            return violation
```

**Why This Matters**:
- Without composite enforcement: Unrealized losses can breach realized limit when closed
- With composite enforcement: Unrealized rule dynamically tightens to protect realized limit
- Result: Trader CANNOT inadvertently breach realized limit through unrealized losses!

---

#### Category 2: Timer/Cooldown (2 rules)
**Characteristic**: Close all positions, temporary lockout, auto-unlock

| Rule | File | Triggers On | Action | Lockout | Timer |
|------|------|-------------|--------|---------|-------|
| RULE-006 | trade_frequency_limit.py | Trade frequency exceeded | Flatten all | Cooldown (30-60 min) | TimerManager |
| RULE-007 | cooldown_after_loss.py | Large single-trade loss | Flatten all | Cooldown (configurable tiers) | TimerManager |

**Integration with TimerManager**:
```python
class TradeFrequencyLimitRule(RiskRule):
    async def evaluate(self, event, engine):
        if trades_per_minute > limit:
            # Trigger violation
            violation = {
                "action": "flatten_all",
                "lockout_type": "cooldown",
                "lockout_duration": 1800,  # 30 minutes
            }
            return violation

# Enforcement executor handles lockout:
async def enforce(self, violation, engine):
    # 1. Close all positions
    await self.enforcement_executor.close_all_positions()

    # 2. Set cooldown via LockoutManager
    await engine.lockout_manager.set_cooldown(
        account_id,
        reason=violation["message"],
        duration_seconds=violation["lockout_duration"]
    )

    # LockoutManager internally uses TimerManager:
    await engine.timer_manager.start_timer(
        name=f"cooldown_{account_id}",
        duration=duration_seconds,
        callback=lambda: engine.lockout_manager.clear_lockout(account_id)
    )
    # After 30 minutes, timer fires callback, lockout auto-clears!
```

**Key Insight**: Cooldown rules DON'T directly use TimerManager - they return a lockout_duration, and the LockoutManager coordinates with TimerManager for auto-expiry!

---

#### Category 3: Hard Lockout (4 rules)
**Characteristic**: Close all positions, hard lockout until condition met

| Rule | File | Triggers On | Action | Lockout | Unlock Condition |
|------|------|-------------|--------|---------|------------------|
| RULE-003 | daily_realized_loss.py | Realized P&L ≤ limit | Flatten all | Hard (until reset time) | Daily reset (17:00 CT) |
| RULE-013 | daily_realized_profit.py | Realized P&L ≥ target | Flatten all | Hard (until reset time) | Daily reset (17:00 CT) |
| RULE-009 | session_block_outside.py | Trade outside hours | Flatten all | Hard (until session start) | Session start time |
| RULE-010 | auth_loss_guard.py | API canTrade = false | Flatten all | Hard (until API restored) | API canTrade = true |

**Integration with LockoutManager**:
```python
class DailyRealizedLossRule(RiskRule):
    async def evaluate(self, event, engine):
        daily_pnl = self.pnl_tracker.add_trade_pnl(account_id, pnl)

        if daily_pnl <= self.limit:
            # Calculate reset time (17:00 CT today or tomorrow)
            reset_time = self._calculate_next_reset_time()

            violation = {
                "action": "flatten_all_and_lockout",
                "lockout_type": "hard",
                "lockout_until": reset_time,  # datetime
            }
            return violation

# Enforcement executor handles hard lockout:
async def enforce(self, violation, engine):
    # 1. Close all positions
    await self.enforcement_executor.close_all_positions()

    # 2. Set hard lockout
    await engine.lockout_manager.set_lockout(
        account_id,
        reason=violation["message"],
        until=violation["lockout_until"]  # datetime (e.g., 17:00 CT today)
    )
    # Lockout persists in database, survives crashes!
```

**Daily Reset Integration** (`timers_config.yaml`):
```yaml
timers:
  daily_reset:
    enabled: true
    time: "17:00"
    timezone: "America/Chicago"
    actions:
      - reset_pnl_tracker          # Clear realized P&L
      - clear_expired_lockouts     # Remove lockouts past their "until" time
```

**Key Insight**: Hard lockouts are NOT managed by TimerManager - they're database-persisted and cleared by:
1. Daily reset task (scheduled via TimerManager)
2. Manual admin unlock
3. Condition met (e.g., API restored for auth_loss_guard)

---

#### Category 4: Automation (1 rule)
**Characteristic**: Modify orders, no lockout

| Rule | File | Triggers On | Action | Lockout |
|------|------|-------------|--------|---------|
| RULE-012 | trade_management.py | Position P&L milestones | Modify stop-loss order | None |

**Features**:
- Auto-breakeven: Move stop to entry price after X ticks profit
- Trailing stop: Adjust stop as price moves favorably

**Not part of composite enforcement** - Operates independently to protect profits.

---

### 4. Enforcement Executor Layer

**File**: `src/risk_manager/sdk/enforcement.py`

**Responsibilities**:
1. ✅ Receive violations from rules
2. ✅ Check lockout state BEFORE executing actions
3. ✅ Execute actions via SDK
4. ✅ Set lockouts/timers AFTER successful enforcement
5. ✅ Log enforcement with full context

**Enforcement Actions**:
```python
class EnforcementExecutor:
    async def close_all_positions(self, symbol: str | None = None) -> dict:
        """Flatten all positions (symbol-specific or all instruments)"""

    async def close_position(self, symbol: str, contract_id: str) -> dict:
        """Close specific position"""

    async def cancel_order(self, symbol: str, order_id: str) -> dict:
        """Cancel specific order"""

    async def modify_order(self, symbol: str, order_id: str, updates: dict) -> dict:
        """Modify order (for RULE-012 trade management)"""
```

**Enforcement Flow**:
```python
async def enforce(self, violation: dict, engine: "RiskEngine"):
    """
    Execute enforcement action with lockout coordination.

    Steps:
    1. Check if account is locked out (skip enforcement if locked)
    2. Log violation details
    3. Execute action via SDK
    4. Set lockout/timer if specified in violation
    5. Log enforcement result
    """

    account_id = violation["account_id"]

    # 1. Check lockout state
    if engine.lockout_manager.is_locked_out(account_id):
        logger.warning(f"Account {account_id} already locked out - skipping enforcement")
        return

    # 2. Log violation
    logger.critical(f"⚠️ VIOLATION: {violation['rule']} - {violation['message']}")

    # 3. Execute action
    action = violation["action"]
    if action == "close_position":
        result = await self.executor.close_position(
            violation["symbol"],
            violation["contract_id"]
        )
    elif action == "flatten_all":
        result = await self.executor.close_all_positions()
    # ... other actions ...

    # 4. Set lockout/timer if specified
    if violation.get("lockout_type") == "hard":
        await engine.lockout_manager.set_lockout(
            account_id,
            reason=violation["message"],
            until=violation["lockout_until"]
        )
    elif violation.get("lockout_type") == "cooldown":
        await engine.lockout_manager.set_cooldown(
            account_id,
            reason=violation["message"],
            duration_seconds=violation["lockout_duration"]
        )

    # 5. Log result with composite enforcement context (if applicable)
    if violation.get("composite_enforcement"):
        logger.warning(
            f"🎯 COMPOSITE ENFORCEMENT:\n"
            f"   Unrealized P&L: ${violation['current_unrealized_pnl']:.2f}\n"
            f"   Effective limit: ${violation['effective_limit']:.2f}\n"
            f"   Realized P&L: ${violation['current_realized_pnl']:.2f}\n"
            f"   Remaining budget: ${violation['remaining_budget']:.2f}"
        )
```

---

### 5. SDK Layer

**Files**:
- `src/risk_manager/integrations/trading.py` - TradingIntegration wrapper
- `src/risk_manager/sdk/suite_manager.py` - Manages TradingSuite instances

**Responsibilities**:
1. ✅ WebSocket connections (SignalR)
2. ✅ Real-time event streaming (orders, positions, quotes)
3. ✅ Position management (open, close, modify)
4. ✅ Order management (place, cancel, modify)
5. ✅ Market data (quotes, bars, trade ticks)

**Integration Points**:
- **Events IN**: SDK events → EventRouter → Rules
- **Actions OUT**: Rules → Enforcement → SDK actions

**Example**:
```python
# SDK Event → Rule
suite.on("position_opened", lambda event: engine.handle_event(
    RiskEvent(event_type=EventType.POSITION_OPENED, data=event)
))

# Rule → SDK Action
suite.positions.close_position(contract_id, reason="Risk rule enforcement")
```

---

## 🔄 Complete Enforcement Pipeline

### End-to-End Flow (Composite Enforcement Example)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SCENARIO: Trader takes 5 losing trades, composite enforcement prevents  │
│           breach of realized loss limit                                  │
└─────────────────────────────────────────────────────────────────────────┘

Configuration:
  - RULE-003 (daily_realized_loss): limit = -$900
  - RULE-004 (daily_unrealized_loss): limit = -$200, composite_enforcement = enabled

Timeline:

┌───────────────────────────────────────────────────────────────────────┐
│ 1. SYSTEM STARTUP                                                     │
├───────────────────────────────────────────────────────────────────────┤
│ manager.py:                                                           │
│   ├─ Create Database                                                  │
│   ├─ Create PnLTracker (db)                                           │
│   ├─ Create LockoutManager (db)                                       │
│   ├─ Create TimerManager                                              │
│   ├─ Initialize RULE-003 (daily_realized_loss):                       │
│   │    DailyRealizedLossRule(limit=-900, pnl_tracker=pnl_tracker)     │
│   ├─ Initialize RULE-004 (daily_unrealized_loss):                     │
│   │    DailyUnrealizedLossRule(                                       │
│   │        loss_limit=-200,                                           │
│   │        pnl_tracker=pnl_tracker,          ← ⭐ COMPOSITE WIRING    │
│   │        realized_loss_limit=-900          ← ⭐ COMPOSITE WIRING    │
│   │    )                                                              │
│   └─ Start event loop                                                 │
│                                                                        │
│ Logs:                                                                 │
│   ✅ Loaded: DailyRealizedLossRule (limit=$-900.0)                    │
│   ✅ Loaded: DailyUnrealizedLossRule                                  │
│      (limit=$-200.0, composite=ENABLED with realized limit $-900.0)   │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ 2. TRADE 1 CLOSES (Loss: -$200)                                       │
├───────────────────────────────────────────────────────────────────────┤
│ SDK Event:                                                            │
│   position_closed → POSITION_CLOSED event                             │
│                                                                        │
│ EventRouter:                                                          │
│   ├─ Routes to RULE-003 (daily_realized_loss)                         │
│   └─ RULE-003.evaluate():                                             │
│        daily_pnl = pnl_tracker.add_trade_pnl(account_id, -200)        │
│        # daily_pnl = -200                                             │
│        # Check: -200 <= -900? NO                                      │
│        return None (no violation)                                     │
│                                                                        │
│ State:                                                                │
│   PnLTracker: daily_pnl = -$200                                       │
│   Remaining budget: -$900 - (-$200) = -$700                           │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ 3. TRADE 2 CLOSES (Loss: -$200)                                       │
├───────────────────────────────────────────────────────────────────────┤
│ RULE-003.evaluate():                                                  │
│   daily_pnl = pnl_tracker.add_trade_pnl(account_id, -200)             │
│   # daily_pnl = -400                                                  │
│   # Check: -400 <= -900? NO                                           │
│   return None                                                         │
│                                                                        │
│ State:                                                                │
│   PnLTracker: daily_pnl = -$400                                       │
│   Remaining budget: -$900 - (-$400) = -$500                           │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ 4. TRADE 3 CLOSES (Loss: -$200)                                       │
├───────────────────────────────────────────────────────────────────────┤
│ State:                                                                │
│   PnLTracker: daily_pnl = -$600                                       │
│   Remaining budget: -$900 - (-$600) = -$300                           │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ 5. TRADE 4 CLOSES (Loss: -$200)                                       │
├───────────────────────────────────────────────────────────────────────┤
│ State:                                                                │
│   PnLTracker: daily_pnl = -$800                                       │
│   Remaining budget: -$900 - (-$800) = -$100 ⚠️ TIGHT BUDGET!         │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ 6. TRADE 5 OPENS (MNQ Long @ 21000)                                   │
├───────────────────────────────────────────────────────────────────────┤
│ SDK Event:                                                            │
│   position_opened → POSITION_OPENED event                             │
│                                                                        │
│ EventRouter:                                                          │
│   ├─ Routes to RULE-004 (daily_unrealized_loss)                       │
│   └─ RULE-004.evaluate():                                             │
│        unrealized_pnl = 0 (position just opened)                      │
│        # No violation yet                                             │
│        return None                                                    │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ 7. PRICE MOVES DOWN (Quote: 20990)                                    │
├───────────────────────────────────────────────────────────────────────┤
│ SDK Event:                                                            │
│   quote_update → UNREALIZED_PNL_UPDATE event                          │
│                                                                        │
│ EventRouter:                                                          │
│   └─ Routes to RULE-004 (daily_unrealized_loss)                       │
│                                                                        │
│ RULE-004.evaluate():                                                  │
│   unrealized_pnl = -$50 (MNQ down 10 ticks * $5/tick)                │
│                                                                        │
│   # ⭐ COMPOSITE ENFORCEMENT LOGIC ⭐                                 │
│   realized_pnl = pnl_tracker.get_daily_pnl(account_id)  # -$800       │
│   remaining_budget = -$900 - (-$800) = -$100                          │
│   effective_limit = max(-$200, -$100) = -$100  ← ADJUSTED!            │
│                                                                        │
│   # Check: -$50 <= -$100? NO                                          │
│   return None                                                         │
│                                                                        │
│ Logs:                                                                 │
│   ⚙️ COMPOSITE ENFORCEMENT: Unrealized limit adjusted                 │
│      $-200.00 → $-100.00                                              │
│      (realized P&L: $-800.00, remaining budget: $-100.00)             │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ 8. PRICE MOVES DOWN MORE (Quote: 20980)                               │
├───────────────────────────────────────────────────────────────────────┤
│ RULE-004.evaluate():                                                  │
│   unrealized_pnl = -$100 (MNQ down 20 ticks * $5/tick)               │
│   effective_limit = -$100 (already adjusted)                          │
│                                                                        │
│   # Check: -$100 <= -$100? YES! ⚠️ TRIGGER!                          │
│                                                                        │
│   return {                                                            │
│       "rule": "DailyUnrealizedLossRule",                              │
│       "message": "Daily unrealized loss limit exceeded: -$100 ≤ -$100"│
│       "action": "close_position",                                     │
│       "current_unrealized_pnl": -100.0,                               │
│       "configured_limit": -200.0,          ← Original limit           │
│       "effective_limit": -100.0,           ← Adjusted limit!          │
│       "composite_enforcement": True,        ← Flag                    │
│       "current_realized_pnl": -800.0,                                 │
│       "remaining_budget": -100.0,                                     │
│       "limit_adjusted": True,               ← Indicates composite     │
│   }                                                                   │
│                                                                        │
│ Enforcement:                                                          │
│   ├─ Check lockout: Not locked out ✅                                 │
│   ├─ Execute: close_position(MNQ, contract_id)                        │
│   └─ No lockout set (trade-by-trade rule)                             │
│                                                                        │
│ SDK:                                                                  │
│   ├─ suite.positions.close_position(contract_id)                      │
│   └─ Position closed at -$100 loss                                    │
│                                                                        │
│ Logs:                                                                 │
│   ⚠️ VIOLATION: DailyUnrealizedLossRule - Daily unrealized loss       │
│      limit exceeded: -$100.00 ≤ -$100.00                              │
│   🎯 COMPOSITE ENFORCEMENT TRIGGERED:                                 │
│      Unrealized P&L: $-100.00                                         │
│      Configured limit: $-200.00                                       │
│      Effective limit: $-100.00     ← Saved us from breach!            │
│      Realized P&L: $-800.00                                           │
│      Remaining budget: $-100.00                                       │
│   ✅ Closed position MNQ/CON.F.US.MNQ.Z25                             │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ 9. POSITION CLOSES                                                    │
├───────────────────────────────────────────────────────────────────────┤
│ SDK Event:                                                            │
│   position_closed → POSITION_CLOSED event                             │
│                                                                        │
│ EventRouter:                                                          │
│   └─ Routes to RULE-003 (daily_realized_loss)                         │
│                                                                        │
│ RULE-003.evaluate():                                                  │
│   daily_pnl = pnl_tracker.add_trade_pnl(account_id, -100)             │
│   # daily_pnl = -$900 (exactly at limit!)                             │
│                                                                        │
│   # Check: -$900 <= -$900? YES! ⚠️ AT LIMIT!                         │
│                                                                        │
│   return {                                                            │
│       "rule": "DailyRealizedLossRule",                                │
│       "message": "Daily realized loss limit reached: -$900 ≤ -$900"   │
│       "action": "flatten_all_and_lockout",                            │
│       "lockout_type": "hard",                                         │
│       "lockout_until": datetime(2025, 10, 30, 17, 0, 0),  # 5 PM CT   │
│   }                                                                   │
│                                                                        │
│ Enforcement:                                                          │
│   ├─ Execute: close_all_positions() (no positions left)               │
│   ├─ Set hard lockout until 17:00 CT                                  │
│   └─ lockout_manager.set_lockout(account_id, until=17:00 CT)          │
│                                                                        │
│ Logs:                                                                 │
│   ⚠️ VIOLATION: DailyRealizedLossRule - Daily realized loss limit     │
│      reached: -$900.00 ≤ -$900.00                                     │
│   🔒 HARD LOCKOUT SET until 2025-10-30 17:00:00 CT                    │
│   ✅ No positions to close (already flat)                             │
│                                                                        │
│ State:                                                                │
│   PnLTracker: daily_pnl = -$900 (exactly at limit!)                   │
│   LockoutManager: Locked out until 17:00 CT                           │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ RESULT                                                                │
├───────────────────────────────────────────────────────────────────────┤
│ ✅ WITHOUT composite enforcement:                                     │
│    - Trade 5 would have closed at -$200 (configured limit)            │
│    - Total realized P&L: -$800 + (-$200) = -$1000                     │
│    - BREACH! Exceeded -$900 limit by -$100!                           │
│                                                                        │
│ ✅ WITH composite enforcement:                                        │
│    - Trade 5 closed at -$100 (adjusted limit)                         │
│    - Total realized P&L: -$800 + (-$100) = -$900                      │
│    - PROTECTED! Exactly at limit, no breach!                          │
│                                                                        │
│ Composite enforcement prevented -$100 overage! 🎯                     │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 🎓 How ALL Systems Coordinate

### State Sharing Matrix

| Component | Reads From | Writes To | Coordinates With |
|-----------|------------|-----------|------------------|
| **PnLTracker** | Database | Database | RULE-003, RULE-013, RULE-004 (composite) |
| **LockoutManager** | Database, TimerManager | Database | RULE-003, RULE-006, RULE-007, RULE-009, RULE-010, RULE-013 |
| **TimerManager** | In-memory | In-memory | LockoutManager, RULE-006, RULE-007, RULE-009 |
| **RULE-003** | PnLTracker | LockoutManager | RULE-004 (provides limit for composite) |
| **RULE-004** | PnLTracker (NEW), TradingIntegration | - | RULE-003 (reads limit for composite) |
| **RULE-006** | TradingIntegration | LockoutManager | TimerManager (via LockoutManager) |
| **RULE-007** | PnLTracker | LockoutManager | TimerManager (via LockoutManager) |
| **RULE-009** | Clock/Schedule | LockoutManager | TimerManager (session checks) |
| **RULE-010** | SDK API (canTrade) | LockoutManager | SDK (polls canTrade status) |
| **RULE-013** | PnLTracker | LockoutManager | - |

### Rule Coordination Patterns

#### 1. **Composite Enforcement** (RULE-004 ↔ RULE-003)
```
RULE-004 (Unrealized) asks RULE-003 (Realized):
  "What's your limit?" → -$900
  "What's current realized P&L?" → -$800 (via PnLTracker)
  "Remaining budget?" → -$100

RULE-004 adjusts its threshold:
  effective_limit = max(-$200, -$100) = -$100
```

#### 2. **Lockout Coordination** (All Hard Lockout Rules → LockoutManager)
```
RULE-003, RULE-013, RULE-010:
  1. Trigger violation
  2. Return lockout_type="hard" + lockout_until=datetime
  3. Enforcement sets lockout via LockoutManager
  4. Lockout persists in database
  5. Daily reset clears expired lockouts
```

#### 3. **Cooldown Coordination** (RULE-006, RULE-007 → LockoutManager → TimerManager)
```
RULE-006 (Trade Frequency):
  1. Trigger violation
  2. Return lockout_type="cooldown" + lockout_duration=1800
  3. Enforcement calls: lockout_manager.set_cooldown(account_id, 1800)
  4. LockoutManager calls: timer_manager.start_timer(name, 1800, callback)
  5. After 1800 seconds, timer fires callback
  6. Callback clears lockout
```

#### 4. **Daily Reset Coordination** (TimerManager → PnLTracker + LockoutManager)
```
timers_config.yaml:
  daily_reset:
    time: "17:00"
    timezone: "America/Chicago"
    actions:
      - reset_pnl_tracker
      - clear_expired_lockouts

At 17:00 CT daily:
  1. TimerManager triggers daily_reset timer
  2. Callback executes:
     - pnl_tracker.reset_daily_pnl(all accounts)
     - lockout_manager.clear_expired_lockouts()
  3. Hard lockouts from RULE-003/RULE-013 are cleared
  4. Trading can resume
```

---

## 📝 Configuration Integration

### Complete Configuration Example

```yaml
# ═══════════════════════════════════════════════════════════════════════
# risk_config.yaml - Complete system configuration
# ═══════════════════════════════════════════════════════════════════════

general:
  instruments: [MNQ, ENQ, ES]
  timezone: "America/Chicago"

rules:
  # ─────────────────────────────────────────────────────────────────────
  # TRADE-BY-TRADE RULES
  # ─────────────────────────────────────────────────────────────────────
  max_contracts:
    enabled: true
    limit: 5
    # No lockout, no composite enforcement needed

  max_contracts_per_instrument:
    enabled: true
    instrument_limits:
      MNQ: 2
      ES: 1
    # No lockout, no composite enforcement needed

  daily_unrealized_loss:
    enabled: true
    limit: -200.0
    # ⭐ COMPOSITE ENFORCEMENT WITH RULE-003
    composite_enforcement:
      enabled: true
      respect_realized_limit: true
      realized_rule_ref: "daily_realized_loss"
    # Coordinates with: PnLTracker (via RULE-003)

  max_unrealized_profit:
    enabled: true
    target: 500.0
    # No lockout, no composite enforcement needed

  # ─────────────────────────────────────────────────────────────────────
  # TIMER/COOLDOWN RULES
  # ─────────────────────────────────────────────────────────────────────
  trade_frequency_limit:
    enabled: true
    limits:
      per_minute: 3
      per_hour: 10
      per_session: 50
    cooldowns:
      per_minute_breach: 60        # 1 minute cooldown
      per_hour_breach: 1800        # 30 minute cooldown
      per_session_breach: 3600     # 1 hour cooldown
    # Coordinates with: LockoutManager, TimerManager

  cooldown_after_loss:
    enabled: true
    loss_threshold: -100.0
    cooldown_tiers:
      - loss_threshold: -100.0
        cooldown_seconds: 1800     # 30 min cooldown
      - loss_threshold: -200.0
        cooldown_seconds: 3600     # 1 hour cooldown
    # Coordinates with: PnLTracker, LockoutManager, TimerManager

  # ─────────────────────────────────────────────────────────────────────
  # HARD LOCKOUT RULES
  # ─────────────────────────────────────────────────────────────────────
  daily_realized_loss:
    enabled: true
    limit: -900.0
    reset_time: "17:00"
    timezone: "America/Chicago"
    # Coordinates with: PnLTracker, LockoutManager
    # Provides limit to: RULE-004 (composite enforcement)

  daily_realized_profit:
    enabled: true
    target: 1000.0
    reset_time: "17:00"
    timezone: "America/Chicago"
    # Coordinates with: PnLTracker, LockoutManager

  session_block_outside:
    enabled: true
    start_time: "08:30"
    end_time: "15:00"
    timezone: "America/Chicago"
    # Coordinates with: LockoutManager, TimerManager (session checks)

  auth_loss_guard:
    enabled: true
    check_interval_seconds: 30
    # Coordinates with: SDK (canTrade polling), LockoutManager

# ═══════════════════════════════════════════════════════════════════════
# timers_config.yaml - Scheduled tasks configuration
# ═══════════════════════════════════════════════════════════════════════

timers:
  daily_reset:
    enabled: true
    time: "17:00"
    timezone: "America/Chicago"
    actions:
      - reset_pnl_tracker          # Clear realized P&L (enables RULE-003/013)
      - clear_expired_lockouts     # Remove hard lockouts from RULE-003/009/010/013
    # Coordinates with: PnLTracker, LockoutManager

  session_check:
    enabled: true
    interval_seconds: 60
    actions:
      - check_session_hours        # For RULE-009 enforcement
    # Coordinates with: RULE-009 (session_block_outside)
```

---

## ✅ Integration Checklist

### For Adding New Rules

When adding a new rule, consider:

- [ ] **State Management**: Does it need PnLTracker? LockoutManager? TimerManager?
- [ ] **Composite Enforcement**: Does it need to coordinate with other rules?
- [ ] **Lockout Type**: Trade-by-trade (none), cooldown (temporary), or hard (until condition)?
- [ ] **Configuration**: Add to risk_config.yaml with appropriate integration flags
- [ ] **Testing**: Test standalone AND integrated behavior
- [ ] **Documentation**: Update this architecture doc!

### For Modifying Existing Rules

When modifying a rule, verify:

- [ ] **Shared State Impact**: Does change affect PnLTracker, LockoutManager, or TimerManager?
- [ ] **Rule Coordination**: Does change break composite enforcement or lockout coordination?
- [ ] **Backward Compatibility**: Will old configs still work?
- [ ] **Testing**: Test integrated scenarios, not just unit tests!
- [ ] **Documentation**: Update architecture doc if integration changes!

---

## 🎯 Summary

**The Risk Manager V34 is NOT 13 independent rules - it's an integrated enforcement ecosystem!**

**Key Integration Points**:
1. ✅ **Configuration** defines behavior and enables coordination
2. ✅ **State Management** (P&L, Lockouts, Timers) is shared across rules
3. ✅ **Composite Enforcement** allows rules to coordinate (RULE-004 ↔ RULE-003)
4. ✅ **Lockout Coordination** prevents trading during violations
5. ✅ **Timer Coordination** enables auto-expiry of cooldowns
6. ✅ **Daily Reset** clears state at configured time
7. ✅ **Enforcement Pipeline** executes actions via unified SDK layer

**Composite Enforcement is Just ONE Example** of how rules coordinate - the entire system is designed for rule interdependence!

---

**Last Updated**: 2025-10-30
**Author**: Risk Manager V34 Team
**Status**: Complete System Architecture Documentation
