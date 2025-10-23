# Rules to SDK Mapping - What We Build vs What SDK Provides

**Date**: 2025-10-23
**Purpose**: Clear breakdown of detailed rule specs, SDK capabilities, and what we need to build

---

## 🎯 The Big Picture

Your rule specs describe **12 detailed risk rules** with:
- Trigger conditions (what events to watch)
- Enforcement actions (close positions, lockouts, etc.)
- State tracking (P&L, trade counts, timers)
- CLI displays (status screens, countdowns)

**The Project-X SDK provides**:
- ✅ Real-time events (positions, trades, orders)
- ✅ Enforcement actions (close positions, cancel orders)
- ✅ Current state queries (positions, P&L, account status)
- ✅ WebSocket connection management

**What we build**:
- 🔧 Rule logic (when to trigger each rule)
- 🔧 Lockout management (timers, cooldowns, daily resets)
- 🔧 State persistence (daily P&L tracking, trade counts)
- 🔧 CLI interfaces (Trader & Admin)
- 🔧 Configuration system (YAML rule configs)

---

## 📊 Rule-by-Rule Breakdown

### RULE-001: MaxContracts

**Spec Says** (`docs/PROJECT_DOCS/rules/01_max_contracts.md`):
```yaml
Purpose: Cap net contract exposure across all instruments
Trigger: GatewayUserPosition event
Action: Close all positions (or reduce to limit)
State: Track current positions across instruments
```

#### What SDK Provides ✅

```python
# 1. TRIGGER: Position update events
suite['MNQ'].on_position_update(callback)
# SDK sends event every time position changes

# 2. GET CURRENT POSITIONS
positions = await suite.get_positions()
# Returns: [{"symbol": "MNQ", "quantity": 3, "side": "Long"}, ...]

# 3. ENFORCEMENT: Close positions
await suite['MNQ'].close_position()  # Close entire position
await suite['MNQ'].close_position(quantity=2)  # Partial close
```

#### What We Build 🔧

```python
# 1. RULE LOGIC (src/risk_manager/rules/max_contracts.py)
class MaxContractsRule(RiskRule):
    async def evaluate(self, event: RiskEvent, engine):
        # Calculate total net contracts
        total_net = 0
        for symbol, suite in engine.suite_manager.get_all_suites().items():
            positions = await suite.get_positions()  # SDK call
            for pos in positions:
                total_net += pos.quantity if pos.side == "Long" else -pos.quantity

        # Check breach
        if abs(total_net) > self.config['limit']:
            # Enforce!
            await self._enforce(engine)

    async def _enforce(self, engine):
        # Close all positions using SDK
        for symbol, suite in engine.suite_manager.get_all_suites().items():
            await suite.close_position()  # SDK handles API call

        # Log enforcement (we build this)
        self.logger.log_enforcement("MaxContracts breach")
```

**Summary**:
- SDK: Gives us events + close methods ✅
- We: Write logic to calculate net, detect breach, execute enforcement 🔧

---

### RULE-003: DailyRealizedLoss

**Spec Says** (`docs/PROJECT_DOCS/rules/03_daily_realized_loss.md`):
```yaml
Purpose: Hard daily loss limit with lockout
Trigger: GatewayUserTrade event (profitAndLoss field)
Action: Close all + cancel all + lockout until 5 PM
State: Track daily realized P&L (survives restart)
```

#### What SDK Provides ✅

```python
# 1. TRIGGER: Trade events with P&L
suite['MNQ'].on_trade(callback)
# Event includes: profitAndLoss, symbol, size, price, etc.

# 2. GET CURRENT P&L (if needed)
stats = await suite.get_stats()
# Returns: realized_pl, unrealized_pl, balance, etc.

# 3. ENFORCEMENT: Close + Cancel
await suite['MNQ'].close_position()      # Close positions
await suite.cancel_all_orders()          # Cancel all pending
```

#### What We Build 🔧

```python
# 1. P&L TRACKER (src/risk_manager/state/pnl_tracker.py)
class PnLTracker:
    """Track daily realized P&L with SQLite persistence."""

    def add_trade_pnl(self, account_id: str, pnl: float) -> float:
        """Add trade P&L to daily total, persist to database."""
        today = datetime.now().date()

        # Load from SQLite
        daily_pnl = self.db.get_daily_pnl(account_id, today)

        # Add new P&L
        new_total = daily_pnl + pnl

        # Save to SQLite (survives restart!)
        self.db.save_daily_pnl(account_id, today, new_total)

        return new_total


# 2. LOCKOUT MANAGER (src/risk_manager/state/lockout_manager.py)
class LockoutManager:
    """Manage lockout states (daily reset, cooldowns)."""

    def set_lockout(self, account_id: str, reason: str, until: datetime):
        """Set lockout until specific time (e.g., 5 PM)."""
        self.lockouts[account_id] = {
            'reason': reason,
            'until': until,
            'locked_at': datetime.now()
        }

        # Persist to SQLite
        self.db.save_lockout(account_id, reason, until)

    def is_locked_out(self, account_id: str) -> bool:
        """Check if account is currently locked."""
        if account_id in self.lockouts:
            if datetime.now() < self.lockouts[account_id]['until']:
                return True  # Still locked
            else:
                self.clear_lockout(account_id)  # Expired
        return False


# 3. RESET SCHEDULER (src/risk_manager/state/reset_scheduler.py)
class ResetScheduler:
    """Schedule daily resets (5 PM every day)."""

    def schedule_daily_reset(self, account_id: str, reset_time: str):
        """Schedule reset at specific time (e.g., "17:00")."""
        # Uses APScheduler or similar
        schedule.every().day.at(reset_time).do(
            lambda: self.reset_daily_counters(account_id)
        )

    def reset_daily_counters(self, account_id: str):
        """Reset P&L, clear lockouts at 5 PM."""
        self.pnl_tracker.reset_daily_pnl(account_id)
        self.lockout_manager.clear_lockout(account_id)


# 4. RULE LOGIC (src/risk_manager/rules/daily_realized_loss.py)
class DailyRealizedLossRule(RiskRule):
    async def evaluate(self, event: RiskEvent, engine):
        # Get P&L from trade event (SDK provides this)
        pnl = event.data.get('profitAndLoss')
        if pnl is None:
            return  # Half-turn trade, no P&L yet

        # Update daily total (we track this)
        daily_pnl = engine.pnl_tracker.add_trade_pnl(
            event.account_id,
            pnl
        )

        # Check breach
        if daily_pnl <= self.config['limit']:  # e.g., -500
            await self._enforce(engine, event.account_id, daily_pnl)

    async def _enforce(self, engine, account_id, daily_pnl):
        # 1. Close all positions (SDK)
        for suite in engine.suite_manager.get_all_suites().values():
            await suite.close_position()

        # 2. Cancel all orders (SDK)
        await suite.cancel_all_orders()

        # 3. Set lockout until 5 PM (we manage this)
        reset_time = self._calculate_next_reset_time()
        engine.lockout_manager.set_lockout(
            account_id,
            reason=f"Daily loss limit: ${daily_pnl:.2f} / ${self.config['limit']:.2f}",
            until=reset_time
        )

        # 4. Log (we do this)
        self.logger.log_enforcement(f"LOCKOUT: Daily loss ${daily_pnl:.2f}")
```

**Summary**:
- SDK: Gives us trade events with P&L + close/cancel methods ✅
- We: Track daily P&L in SQLite, manage lockouts, schedule resets 🔧

---

### RULE-006: TradeFrequencyLimit

**Spec Says** (`docs/PROJECT_DOCS/rules/06_trade_frequency_limit.md`):
```yaml
Purpose: Prevent overtrading (3/min, 10/hour, 50/session)
Trigger: GatewayUserTrade event
Action: Set cooldown timer (60s, 30min, 1hr)
State: Track trade counts in time windows
```

#### What SDK Provides ✅

```python
# 1. TRIGGER: Trade events
suite['MNQ'].on_trade(callback)
# SDK sends event every time trade executes

# 2. ENFORCEMENT: Close + Cancel (if needed)
await suite.close_position()
await suite.cancel_all_orders()
```

#### What We Build 🔧

```python
# 1. TRADE COUNTER (src/risk_manager/state/trade_counter.py)
class TradeCounter:
    """Track trades in rolling time windows."""

    def add_trade(self, account_id: str, trade_id: str):
        """Record new trade with timestamp."""
        now = datetime.now()

        # Store in SQLite with timestamp
        self.db.insert_trade(account_id, trade_id, now)

    def count_in_window(self, account_id: str, seconds: int) -> int:
        """Count trades in last N seconds."""
        cutoff = datetime.now() - timedelta(seconds=seconds)

        # Query SQLite
        return self.db.count_trades_since(account_id, cutoff)

    def count_in_session(self, account_id: str) -> int:
        """Count trades since session start (based on reset time)."""
        session_start = self._get_session_start_time()
        return self.db.count_trades_since(account_id, session_start)


# 2. TIMER MANAGER (src/risk_manager/state/timer_manager.py)
class TimerManager:
    """Manage cooldown timers."""

    def start_timer(self, account_id: str, duration_seconds: int, reason: str):
        """Start countdown timer."""
        expires_at = datetime.now() + timedelta(seconds=duration_seconds)

        self.timers[account_id] = {
            'expires_at': expires_at,
            'duration': duration_seconds,
            'reason': reason
        }

        # Persist to SQLite
        self.db.save_timer(account_id, expires_at, reason)

    def get_remaining_time(self, account_id: str) -> Optional[int]:
        """Get remaining seconds on timer."""
        if account_id in self.timers:
            remaining = (self.timers[account_id]['expires_at'] - datetime.now()).seconds
            if remaining > 0:
                return remaining
            else:
                self.clear_timer(account_id)  # Expired
        return None


# 3. RULE LOGIC (src/risk_manager/rules/trade_frequency_limit.py)
class TradeFrequencyRule(RiskRule):
    async def evaluate(self, event: RiskEvent, engine):
        account_id = event.account_id
        trade_id = event.data['id']

        # Record this trade (we track this)
        engine.trade_counter.add_trade(account_id, trade_id)

        # Count trades in windows (we calculate this)
        minute_count = engine.trade_counter.count_in_window(account_id, 60)
        hour_count = engine.trade_counter.count_in_window(account_id, 3600)
        session_count = engine.trade_counter.count_in_session(account_id)

        # Check breach
        if minute_count >= self.config['limits']['per_minute']:
            await self._enforce_cooldown(engine, account_id, "per_minute", 60)
        elif hour_count >= self.config['limits']['per_hour']:
            await self._enforce_cooldown(engine, account_id, "per_hour", 1800)
        elif session_count >= self.config['limits']['per_session']:
            await self._enforce_cooldown(engine, account_id, "per_session", 3600)

    async def _enforce_cooldown(self, engine, account_id, breach_type, duration):
        # Trade already happened, can't prevent it
        # Set cooldown timer to prevent NEXT trade

        reason = f"Trade frequency limit: {breach_type}"
        engine.timer_manager.start_timer(account_id, duration, reason)

        # Log
        self.logger.log_enforcement(f"COOLDOWN: {duration}s - {reason}")
```

**Summary**:
- SDK: Gives us trade events ✅
- We: Count trades in time windows, manage cooldown timers 🔧

---

## 🏗️ What We Build (Core Components)

### 1. Rule Engine (`src/risk_manager/core/engine.py`)

**Purpose**: Orchestrate rules, receive events, check for breaches

```python
class RiskEngine:
    """Core orchestrator - receives events, runs all enabled rules."""

    def __init__(self, suite_manager, rules_config):
        self.suite_manager = suite_manager  # SDK wrapper
        self.event_bus = EventBus()

        # State managers (we build these)
        self.pnl_tracker = PnLTracker()
        self.lockout_manager = LockoutManager()
        self.timer_manager = TimerManager()
        self.trade_counter = TradeCounter()
        self.reset_scheduler = ResetScheduler()

        # Load rules (we build these)
        self.rules = self._load_rules(rules_config)

    async def process_event(self, event: RiskEvent):
        """Process incoming event through all rules."""

        # Check if account is locked out
        if self.lockout_manager.is_locked_out(event.account_id):
            # Account is locked! If there's a position, close it
            await self._enforce_lockout(event.account_id)
            return

        # Run event through all enabled rules
        for rule in self.rules:
            if rule.enabled:
                await rule.evaluate(event, self)
```

**What SDK provides**: Nothing - this is pure risk logic ❌
**What we build**: Everything 🔧

---

### 2. SDK Event Bridge (`src/risk_manager/sdk/event_bridge.py`)

**Purpose**: Convert SDK events → Risk events

```python
class EventBridge:
    """Bridge SDK events to Risk Engine."""

    def setup_callbacks(self, suite_manager, event_bus):
        """Set up SDK callbacks."""

        for symbol, suite in suite_manager.get_all_suites().items():
            # SDK provides callbacks ✅
            suite.on_position_update(
                lambda pos: self._on_position(pos, event_bus)
            )
            suite.on_trade(
                lambda trade: self._on_trade(trade, event_bus)
            )
            suite.on_order_update(
                lambda order: self._on_order(order, event_bus)
            )

    def _on_position(self, position, event_bus):
        """Convert SDK position event → RiskEvent."""
        risk_event = RiskEvent(
            type=EventType.POSITION_UPDATED,
            account_id=position.account_id,
            data={
                'symbol': position.symbol,
                'quantity': position.quantity,
                'side': position.side,
                'avg_price': position.average_price
            }
        )
        event_bus.publish(risk_event)  # Send to risk engine

    def _on_trade(self, trade, event_bus):
        """Convert SDK trade event → RiskEvent."""
        risk_event = RiskEvent(
            type=EventType.TRADE_EXECUTED,
            account_id=trade.account_id,
            data={
                'id': trade.id,
                'symbol': trade.symbol,
                'pnl': trade.profit_and_loss,  # SDK provides this!
                'price': trade.price,
                'quantity': trade.quantity
            }
        )
        event_bus.publish(risk_event)
```

**What SDK provides**: Raw events with data ✅
**What we build**: Event conversion layer 🔧

---

### 3. Suite Manager (`src/risk_manager/sdk/suite_manager.py`)

**Purpose**: Manage TradingSuite instances (SDK wrapper)

```python
class SuiteManager:
    """Manage SDK TradingSuite instances for each instrument."""

    def __init__(self, api_key, username, instruments):
        self.suites = {}

        # Create TradingSuite for each instrument
        for symbol in instruments:
            suite = TradingSuite(
                api_key=api_key,
                username=username,
                instrument=symbol
            )
            self.suites[symbol] = suite

    async def connect_all(self):
        """Connect all suites to SDK."""
        for suite in self.suites.values():
            await suite.start()  # SDK handles WebSocket connection

    def get_suite(self, symbol: str) -> TradingSuite:
        """Get SDK suite for symbol."""
        return self.suites[symbol]

    def get_all_suites(self) -> dict:
        """Get all SDK suites."""
        return self.suites
```

**What SDK provides**: TradingSuite class ✅
**What we build**: Multi-instrument lifecycle management 🔧

---

### 4. State Persistence (`src/risk_manager/state/`)

**Components**:
- `pnl_tracker.py` - Daily P&L tracking (SQLite)
- `lockout_manager.py` - Lockout states (SQLite)
- `timer_manager.py` - Cooldown timers (SQLite)
- `trade_counter.py` - Trade counts in windows (SQLite)
- `reset_scheduler.py` - Daily resets (APScheduler)

**What SDK provides**: Nothing - state is our responsibility ❌
**What we build**: Everything 🔧

**SQLite Schema**:
```sql
-- Daily P&L tracking
CREATE TABLE daily_pnl (
    account_id TEXT,
    date DATE,
    realized_pnl REAL,
    PRIMARY KEY (account_id, date)
);

-- Lockout states
CREATE TABLE lockouts (
    account_id TEXT PRIMARY KEY,
    reason TEXT,
    locked_at DATETIME,
    expires_at DATETIME
);

-- Cooldown timers
CREATE TABLE timers (
    account_id TEXT PRIMARY KEY,
    reason TEXT,
    expires_at DATETIME
);

-- Trade counts
CREATE TABLE trades (
    account_id TEXT,
    trade_id TEXT,
    timestamp DATETIME,
    PRIMARY KEY (account_id, trade_id)
);
```

---

### 5. CLI Interfaces (`src/cli/`)

**Trader CLI** (`src/cli/trader/`)
- `status_screen.py` - Real-time status display
- `lockout_display.py` - Countdown timers
- `logs_viewer.py` - Enforcement log viewer

**Admin CLI** (`src/cli/admin/`)
- `configure_rules.py` - Interactive rule configuration
- `manage_accounts.py` - API key setup
- `service_control.py` - Start/stop service
- `auth.py` - Windows UAC elevation check

**What SDK provides**: Nothing - UI is our responsibility ❌
**What we build**: Everything 🔧

---

## 📊 Complete Data Flow

### Example: Daily Loss Limit Hit

```
1. Trader executes trade in broker
   ↓
2. TopstepX Gateway receives trade
   ↓
3. SDK WebSocket receives "GatewayUserTrade" event
   SDK Event Data: {profitAndLoss: -150, symbol: "MNQ", ...}
   ↓
4. EventBridge converts to RiskEvent
   (We built this) ✅
   ↓
5. RiskEngine.process_event(event)
   (We built this) ✅
   ↓
6. DailyRealizedLossRule.evaluate(event)
   (We built this) ✅
   - Calls: pnl_tracker.add_trade_pnl(-150) → Returns -520 total
   - Checks: -520 <= -500? YES, BREACH!
   ↓
7. Rule enforcement:
   a. Close all positions
      → suite['MNQ'].close_position() (SDK provides) ✅
      → suite['ES'].close_position() (SDK provides) ✅

   b. Cancel all orders
      → suite.cancel_all_orders() (SDK provides) ✅

   c. Set lockout
      → lockout_manager.set_lockout(until=5PM) (We built) ✅
      → Saves to SQLite (We built) ✅

   d. Log enforcement
      → logger.log("LOCKOUT: -$520 / -$500") (We built) ✅
   ↓
8. Trader CLI updates
   (We built this) ✅
   Display: "🔴 LOCKED OUT - Reset at 5:00 PM (3h 42m)"
```

---

## 🎯 Summary: SDK vs Our Code

### What SDK Provides ✅

```python
# Events
suite.on_position_update(callback)
suite.on_trade(callback)
suite.on_order_update(callback)
suite.on_account_update(callback)

# Actions
await suite.close_position()
await suite.close_position(quantity=2)
await suite.cancel_all_orders()
await suite.place_order(...)

# Queries
positions = await suite.get_positions()
orders = await suite.get_orders()
stats = await suite.get_stats()  # includes P&L, balance

# Connection
await suite.start()  # Connect WebSocket
await suite.stop()   # Disconnect
```

### What We Build 🔧

```python
# Rule Logic (12 rules)
class DailyRealizedLossRule(RiskRule):
    async def evaluate(event, engine):
        # Calculate breach, enforce, log

# State Management
pnl_tracker.add_trade_pnl(account_id, pnl)
lockout_manager.set_lockout(account_id, until)
timer_manager.start_timer(account_id, duration)
trade_counter.count_in_window(account_id, 60)

# Persistence (SQLite)
db.save_daily_pnl(account_id, date, pnl)
db.save_lockout(account_id, expires_at)
db.save_timer(account_id, expires_at)

# Orchestration
engine.process_event(risk_event)
engine.check_all_rules()

# CLI
trader_cli.display_status()
admin_cli.configure_rules()

# Configuration
config_loader.load_yaml("risk_config.yaml")

# Service
windows_service.install()
windows_service.start()
```

---

## 📋 Implementation Checklist

### Phase 1: SDK Integration (✅ Done ~100%)
- [x] Suite Manager (wraps TradingSuite)
- [x] Event Bridge (SDK events → Risk events)
- [x] Basic enforcement (close/cancel via SDK)

### Phase 2: Core State Management (⏳ ~30%)
- [x] Basic state tracking (in-memory)
- [ ] SQLite persistence schema
- [ ] PnLTracker with database
- [ ] LockoutManager with database
- [ ] TimerManager with database
- [ ] TradeCounter with database
- [ ] ResetScheduler (daily resets)

### Phase 3: Rules Implementation (⏳ ~17% - 2/12)
- [x] RULE-001: MaxContracts
- [x] RULE-002: MaxContractsPerInstrument
- [ ] RULE-003: DailyRealizedLoss
- [ ] RULE-004: DailyUnrealizedLoss
- [ ] RULE-005: MaxUnrealizedProfit
- [ ] RULE-006: TradeFrequencyLimit
- [ ] RULE-007: CooldownAfterLoss
- [ ] RULE-008: NoStopLossGrace
- [ ] RULE-009: SessionBlockOutside
- [ ] RULE-010: AuthLossGuard
- [ ] RULE-011: SymbolBlocks
- [ ] RULE-012: TradeManagement

### Phase 4: CLI System (⏳ ~0%)
- [ ] Trader CLI - Status Screen
- [ ] Trader CLI - Lockout Display
- [ ] Trader CLI - Logs Viewer
- [ ] Admin CLI - Configure Rules
- [ ] Admin CLI - Manage Account
- [ ] Admin CLI - Service Control

### Phase 5: Windows Service (⏳ ~0%)
- [ ] Service wrapper (pywin32)
- [ ] Install/uninstall scripts
- [ ] Auto-start configuration
- [ ] File ACL permissions

---

## 💡 Key Insights

### 1. **SDK = Data Provider & Action Executor**
The SDK gives us:
- Real-time events (positions, trades, orders)
- Enforcement methods (close, cancel)
- Current state queries (positions, P&L)

**We don't reimplement this. We use it.**

### 2. **We = Risk Logic & State Management**
We build:
- Rule logic (when to enforce)
- State tracking (daily P&L, trade counts)
- Persistence (SQLite for crash recovery)
- Lockout/timer management
- CLI interfaces
- Configuration system

### 3. **Clean Separation**
```
┌──────────────────────────────────────┐
│         Our Risk Manager             │
│                                      │
│  ┌────────────────────────────────┐ │
│  │   Rule Logic (12 rules)        │ │
│  │   State Management (SQLite)    │ │
│  │   Lockout/Timer Management     │ │
│  │   CLI Interfaces               │ │
│  └────────────┬───────────────────┘ │
│               │                      │
│               ▼                      │
│  ┌────────────────────────────────┐ │
│  │   SDK Integration Layer        │ │
│  │   - Event Bridge               │ │
│  │   - Suite Manager              │ │
│  │   - Enforcement Wrapper        │ │
│  └────────────┬───────────────────┘ │
└───────────────┼──────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│       Project-X-Py SDK               │
│  - WebSocket Connection              │
│  - Event System                      │
│  - close_position(), cancel_orders() │
│  - get_positions(), get_stats()      │
└──────────────────────────────────────┘
```

---

## 📖 For Implementation

**When implementing a new rule, ask**:

1. **What event triggers this rule?**
   → SDK provides via callbacks ✅

2. **What data do I need to check?**
   → SDK gives current state (positions, P&L) ✅
   → We track historical state (daily totals, counts) 🔧

3. **What action do I take on breach?**
   → SDK provides close/cancel methods ✅
   → We add lockout/timer logic 🔧

4. **What state needs to persist?**
   → We store in SQLite 🔧

5. **What does CLI show?**
   → We build display logic 🔧

---

**This mapping makes it clear: SDK handles trading, we handle risk protection.** 🛡️

**Created**: 2025-10-23
**Purpose**: Bridge specs to implementation reality
