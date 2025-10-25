# Wave 2 Gap Analysis: State Management Implementation

**Document ID:** 02-STATE-MANAGEMENT-GAPS
**Created:** 2025-10-25
**Researcher:** RESEARCHER 2: State Management Gap Analyst
**Status:** Complete

---

## Executive Summary

### Implementation Status
- **Total State Managers:** 5 (Database, PnL Tracker, Lockout Manager, Timer Manager, Reset Manager)
- **Implemented:** 2 (40%) - Database, PnL Tracker
- **Missing:** 3 (60%) - Lockout Manager, Timer Manager, Reset Manager
- **Rules Blocked:** 9 of 13 rules (69%)
- **Estimated Total Effort:** 3-4 weeks

### Critical Finding
**Three missing state managers are blocking 69% of all risk rules**, creating a significant bottleneck for project completion. These managers form the foundation for lockout enforcement, cooldown timers, and daily resets.

### Priority Impact
- **Lockout Manager (MOD-002):** Blocks 7 rules - CRITICAL
- **Timer Manager (MOD-003):** Blocks 4 rules - HIGH
- **Reset Manager (MOD-004):** Blocks 5 rules - HIGH

---

## Implementation Status Matrix

| Module | Name | Status | Priority | Effort | Rules Blocked | Lines |
|--------|------|--------|----------|--------|---------------|-------|
| MOD-001 | Database | ✅ Implemented | Critical | Done | None | ~150 |
| **N/A** | **PnL Tracker** | ✅ Implemented | Critical | Done | None | ~180 |
| **MOD-002** | **Lockout Manager** | ❌ Missing | **CRITICAL** | **1.5 weeks** | **RULE-003, 006, 007, 009, 010, 011, 013** | **~250** |
| **MOD-003** | **Timer Manager** | ❌ Missing | **HIGH** | **1 week** | **RULE-006, 007, 008, 009** | **~150** |
| **MOD-004** | **Reset Manager** | ❌ Missing | **HIGH** | **1 week** | **RULE-003, 004, 005, 009, 013** | **~180** |

**Note:** PnL Tracker was not listed in original MOD specs but exists as a critical state component.

---

## Detailed Gap Analysis

### ✅ Implemented Managers

#### MOD-001: Database (database.py)
**Status:** ✅ Fully Implemented
**Location:** `/src/risk_manager/state/database.py`
**Lines:** ~150 lines

**Purpose:** SQLite database abstraction layer for state persistence

**Features Implemented:**
- ✅ Database connection management
- ✅ Schema initialization
- ✅ Query execution wrapper
- ✅ Transaction support
- ✅ Connection pooling

**Database Schema (from implementation):**
```sql
CREATE TABLE IF NOT EXISTS daily_pnl (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    date TEXT NOT NULL,
    realized_pnl REAL DEFAULT 0.0,
    unrealized_pnl REAL DEFAULT 0.0,
    timestamp TEXT NOT NULL,
    UNIQUE(account_id, date)
);
```

**What It Provides:**
- Foundation for all state persistence
- Used by PnL Tracker currently
- Ready for Lockout Manager, Timer Manager, Reset Manager

**Rules Enabled:**
- None directly (provides infrastructure for other managers)

---

#### PnL Tracker (pnl_tracker.py)
**Status:** ✅ Fully Implemented
**Location:** `/src/risk_manager/state/pnl_tracker.py`
**Lines:** ~180 lines

**Purpose:** Track daily realized and unrealized P&L

**Features Implemented:**
- ✅ Daily realized P&L tracking
- ✅ Daily unrealized P&L tracking
- ✅ SQLite persistence via Database module
- ✅ Per-account tracking
- ✅ Date-based P&L queries

**Public API:**
```python
class PnLTracker:
    async def add_trade_pnl(account_id: str, pnl: float) -> float
    async def update_unrealized_pnl(account_id: str, pnl: float) -> float
    async def get_daily_pnl(account_id: str) -> dict
    async def get_realized_pnl(account_id: str) -> float
    async def get_unrealized_pnl(account_id: str) -> float
    async def reset_daily_pnl(account_id: str) -> None
```

**What It Provides:**
- Real-time P&L tracking
- Daily P&L state persistence
- Ready for RULE-003, 004, 005, 013 to consume

**Rules Enabled:**
- ✅ RULE-003: DailyRealizedLoss (partially - needs Lockout Manager + Reset Manager)
- ✅ RULE-004: DailyUnrealizedLoss (partially - needs Reset Manager)
- ✅ RULE-005: MaxUnrealizedProfit (partially - needs Reset Manager)
- ✅ RULE-013: DailyRealizedProfit (partially - needs Lockout Manager + Reset Manager)

**Note:** These rules can detect breaches but cannot enforce lockouts or daily resets without missing managers.

---

### ❌ Missing Managers

---

#### MOD-002: Lockout Manager
**Status:** ❌ MISSING - CRITICAL BLOCKER
**Planned Location:** `/src/risk_manager/state/lockout_manager.py`
**Estimated Lines:** ~250 lines
**Estimated Effort:** 1.5 weeks (6-8 developer days)

**Purpose:** Centralized lockout state management - all lockout rules call these functions

**Features Required:**

1. **Hard Lockouts (until specific time)**
   - Lock account until daily reset (5:00 PM)
   - Lock account until session start
   - Lock account until admin unlock
   - Persist lockout across restarts

2. **Cooldown Timers (duration-based)**
   - Lock account for N seconds
   - Auto-unlock when timer expires
   - Countdown display for Trader CLI
   - Integration with Timer Manager (MOD-003)

3. **Auto-Expiry**
   - Background task checks expired lockouts
   - Auto-clear when time reached
   - Notify Trader CLI

4. **Persistence**
   - SQLite storage for crash recovery
   - Load lockouts on startup
   - Survive service restarts

**Public API Required:**
```python
# Hard lockouts
def set_lockout(account_id: int, reason: str, until: datetime) -> None
def set_cooldown(account_id: int, reason: str, duration_seconds: int) -> None

# Lockout checks
def is_locked_out(account_id: int) -> bool
def get_lockout_info(account_id: int) -> dict | None

# Lockout management
def clear_lockout(account_id: int) -> None
def check_expired_lockouts() -> None

# Startup/persistence
def load_lockouts_from_db() -> None
```

**Database Schema Required:**
```sql
CREATE TABLE lockouts (
    account_id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lockouts_expires ON lockouts(expires_at);
```

**In-Memory State:**
```python
lockout_state = {
    123: {
        "reason": "Daily loss limit hit",
        "until": datetime(2025, 1, 17, 17, 0),
        "type": "hard_lockout",  # or "cooldown"
        "created_at": datetime(2025, 1, 17, 14, 23)
    }
}
```

**Rules Blocked (7 rules - 54% of all rules):**

| Rule | Name | Category | Lockout Type | Impact |
|------|------|----------|--------------|--------|
| RULE-003 | DailyRealizedLoss | Hard Lockout | Until reset (5 PM) | Cannot enforce daily loss limit |
| RULE-006 | TradeFrequencyLimit | Timer/Cooldown | Duration-based | Cannot enforce trade limits |
| RULE-007 | CooldownAfterLoss | Timer/Cooldown | Duration-based | Cannot enforce cooldown |
| RULE-009 | SessionBlockOutside | Hard Lockout | Until session start | Cannot block outside hours |
| RULE-010 | AuthLossGuard | Hard Lockout | Manual unlock | Cannot lock on API restriction |
| RULE-011 | SymbolBlocks | Hard Lockout | Permanent (per-symbol) | Cannot blacklist symbols |
| RULE-013 | DailyRealizedProfit | Hard Lockout | Until reset (5 PM) | Cannot enforce profit target |

**SDK Integration Needs:**
- Event router must check lockout before processing events
- If locked out + new position detected → close immediately
- Integration point: `event_router.py` (not yet implemented)

**Persistence Requirements:**
- Load lockouts on service startup (survive crashes)
- Persist lockout changes to SQLite immediately
- Delete expired lockouts from database

**Windows Service Integration:**
- Background task runs every second (`check_expired_lockouts()`)
- Called by main daemon loop
- Must be async/await compatible

**Dependencies:**
- **Requires:** MOD-003 (Timer Manager) for cooldown timers
- **Requires:** Database module (already implemented)
- **Used By:** 7 rules, Event Router, Trader CLI

**Implementation Notes:**
1. **Symbol-specific lockouts needed for RULE-011**
   - Current design assumes account-wide lockouts
   - Need to support `(account_id, symbol)` tuple keys
   - Example: `lockout_state[("123", "RTY")] = {...}`

2. **Lockout priority handling**
   - If multiple rules trigger lockouts, which wins?
   - Longest duration? Most restrictive?
   - Need policy decision

3. **Event Router integration**
   - Must be implemented before lockout enforcement works
   - Event router checks `is_locked_out()` before routing events

**Test Scenarios:**
- Hard lockout until specific time
- Cooldown timer auto-clears
- Persistence across daemon restart
- Symbol-specific lockout (RULE-011)
- Multiple simultaneous lockouts

**Estimated Effort Breakdown:**
- Core implementation: 3 days
- SQLite persistence: 1 day
- Symbol-specific lockout support: 1 day
- Event router integration: 1 day
- Testing: 2 days
- **Total: 8 days (~1.5 weeks)**

---

#### MOD-003: Timer Manager
**Status:** ❌ MISSING - HIGH PRIORITY
**Planned Location:** `/src/risk_manager/state/timer_manager.py`
**Estimated Lines:** ~150 lines
**Estimated Effort:** 1 week (5 developer days)

**Purpose:** Countdown timers for cooldowns, session checks, and scheduled tasks

**Features Required:**

1. **Countdown Timers**
   - Start timer with duration + callback
   - Execute callback when timer expires
   - Track multiple timers simultaneously
   - Get remaining time for CLI display

2. **Background Task**
   - Check timers every second
   - Fire callbacks for expired timers
   - Clean up expired timers

3. **Timer Cancellation**
   - Cancel timer before expiry
   - Remove from tracking

**Public API Required:**
```python
def start_timer(name: str, duration: int, callback: callable) -> None
def get_remaining_time(name: str) -> int
def cancel_timer(name: str) -> None
def check_timers() -> None  # Background task
```

**In-Memory State:**
```python
timers = {
    "lockout_123": {
        "expires_at": datetime(2025, 1, 17, 14, 53),
        "callback": lambda: clear_lockout(123),
        "duration": 1800  # 30 minutes
    },
    "grace_period_789": {
        "expires_at": datetime(2025, 1, 17, 14, 25),
        "callback": lambda: check_stop_loss(789),
        "duration": 10  # 10 seconds
    }
}
```

**Rules Blocked (4 rules):**

| Rule | Name | Category | Timer Usage | Impact |
|------|------|----------|-------------|--------|
| RULE-006 | TradeFrequencyLimit | Timer/Cooldown | Cooldown duration | Cannot enforce cooldown |
| RULE-007 | CooldownAfterLoss | Timer/Cooldown | Loss-based cooldown | Cannot enforce cooldown |
| RULE-008 | NoStopLossGrace | Trade-by-Trade | Grace period (10s) | Cannot enforce SL requirement |
| RULE-009 | SessionBlockOutside | Hard Lockout | Session end timer | Cannot auto-close at session end |

**SDK Integration Needs:**
- No direct SDK integration
- Pure in-memory timer tracking
- Callbacks invoke SDK actions (via MOD-001)

**Persistence Requirements:**
- **NOT persisted to SQLite** (timers recreated on restart)
- Lockout Manager persists cooldowns, Timer Manager just tracks countdown
- On restart: Lockout Manager reloads lockouts → recalculates remaining time

**Windows Service Integration:**
- Background task runs every second (`check_timers()`)
- Called by main daemon loop
- Must be async/await compatible

**Dependencies:**
- **None** (no external dependencies)
- **Used By:** MOD-002 (Lockout Manager), RULE-008, RULE-009

**Implementation Notes:**
1. **Simple in-memory dictionary**
   - No database needed
   - Fast lookups
   - Timers recreated from lockout state on restart

2. **Callback execution**
   - Callbacks must be async-safe
   - Handle callback exceptions gracefully
   - Log callback execution

3. **Timer precision**
   - Background task runs every 1 second
   - Timers may fire up to 1 second late (acceptable)

**Test Scenarios:**
- Start timer, callback fires after duration
- Get remaining time decreases over time
- Cancel timer before expiry
- Multiple timers running simultaneously

**Estimated Effort Breakdown:**
- Core implementation: 2 days
- Background task integration: 1 day
- Testing: 1 day
- Integration with Lockout Manager: 1 day
- **Total: 5 days (~1 week)**

---

#### MOD-004: Reset Manager
**Status:** ❌ MISSING - HIGH PRIORITY
**Planned Location:** `/src/risk_manager/state/reset_scheduler.py`
**Estimated Lines:** ~180 lines
**Estimated Effort:** 1 week (5 developer days)

**Purpose:** Daily reset logic for P&L counters and holiday calendar integration

**Features Required:**

1. **Daily Reset Scheduling**
   - Schedule reset at specific time (e.g., 5:00 PM ET)
   - Timezone-aware (America/New_York, America/Chicago)
   - Trigger reset at configured time
   - Prevent duplicate resets on same day

2. **Daily Counter Resets**
   - Reset daily realized P&L to 0
   - Reset daily unrealized P&L to 0
   - Clear daily lockouts (via Lockout Manager)
   - Reset trade counts (if implemented)

3. **Holiday Calendar**
   - Load holidays from `config/holidays.yaml`
   - Check if date is trading holiday
   - Skip resets on holidays (configurable)

4. **Background Scheduler**
   - Check reset time every minute
   - Trigger reset when time reached
   - Handle timezone conversions

**Public API Required:**
```python
def schedule_daily_reset(reset_time: str = "17:00", timezone: str = "America/New_York") -> None
def reset_daily_counters(account_id: int) -> None
def check_reset_time() -> None  # Background task
def is_holiday(date: datetime) -> bool
```

**Holiday Calendar (`config/holidays.yaml`):**
```yaml
holidays:
  - "2025-01-01"  # New Year's Day
  - "2025-07-04"  # Independence Day
  - "2025-12-25"  # Christmas
  # CME futures holidays...
```

**Rules Blocked (5 rules):**

| Rule | Name | Category | Reset Requirement | Impact |
|------|------|----------|-------------------|--------|
| RULE-003 | DailyRealizedLoss | Hard Lockout | Reset P&L + clear lockout | Cannot unlock at 5 PM |
| RULE-004 | DailyUnrealizedLoss | Trade-by-Trade | Reset unrealized P&L | Cannot reset daily tracking |
| RULE-005 | MaxUnrealizedProfit | Trade-by-Trade | Reset unrealized P&L | Cannot reset daily target |
| RULE-009 | SessionBlockOutside | Hard Lockout | Holiday calendar | Cannot respect holidays |
| RULE-013 | DailyRealizedProfit | Hard Lockout | Reset P&L + clear lockout | Cannot unlock at 5 PM |

**SDK Integration Needs:**
- No direct SDK integration
- Calls PnL Tracker to reset P&L
- Calls Lockout Manager to clear lockouts

**Persistence Requirements:**
- Track last reset timestamp in SQLite
- Prevent duplicate resets
- Survive service restart (know if reset already happened today)

**Database Schema Required:**
```sql
CREATE TABLE reset_log (
    account_id INTEGER,
    reset_date DATE,
    reset_time DATETIME,
    PRIMARY KEY (account_id, reset_date)
);
```

**Windows Service Integration:**
- Background task runs every 60 seconds (`check_reset_time()`)
- Called by main daemon loop
- Must be async/await compatible
- Handle system clock changes (DST transitions)

**Dependencies:**
- **Requires:** PnL Tracker (to reset P&L)
- **Requires:** Lockout Manager (to clear lockouts)
- **Requires:** Database module (to track resets)
- **Requires:** `pytz` or `zoneinfo` for timezone handling
- **Used By:** RULE-003, 004, 005, 009, 013

**Implementation Notes:**
1. **Timezone handling**
   - Use `pytz` or Python 3.9+ `zoneinfo`
   - Handle DST transitions correctly
   - Support multiple timezones (ES uses Chicago, most use New York)

2. **Reset time calculation**
   - If breach occurs before reset time → unlock at reset time same day
   - If breach occurs after reset time → unlock at reset time next day
   - Handle edge case: breach at exactly reset time

3. **Holiday calendar integration**
   - RULE-009 respects holidays (no trading on holidays)
   - Other rules may or may not respect holidays (configurable?)

4. **Reset sequence**
   ```python
   def reset_daily_counters(account_id):
       # 1. Reset P&L
       pnl_tracker.reset_daily_pnl(account_id)

       # 2. Clear daily lockouts
       lockout_manager.clear_lockout(account_id)

       # 3. Log reset
       log_reset(account_id)
   ```

**Test Scenarios:**
- Daily reset triggers at configured time
- Timezone conversion works correctly
- Holiday detection prevents trading
- Reset doesn't trigger twice on same day
- Reset survives service restart

**Estimated Effort Breakdown:**
- Core implementation: 2 days
- Timezone handling: 1 day
- Holiday calendar: 1 day
- Testing: 1 day
- **Total: 5 days (~1 week)**

---

## Critical Blocking Analysis

### Rules Blocked by Missing Managers

| Rule | Name | Category | Blocked By | Can Detect Breach? | Can Enforce? |
|------|------|----------|------------|-------------------|--------------|
| RULE-001 | MaxContracts | Trade-by-Trade | None | ✅ Yes | ✅ Yes |
| RULE-002 | MaxContractsPerInstrument | Trade-by-Trade | None | ✅ Yes | ✅ Yes |
| **RULE-003** | **DailyRealizedLoss** | **Hard Lockout** | **MOD-002, MOD-004** | ✅ Yes | ❌ No (can close, no lockout/reset) |
| **RULE-004** | **DailyUnrealizedLoss** | **Trade-by-Trade** | **MOD-004** | ✅ Yes | ⚠️ Partial (can close, no reset) |
| **RULE-005** | **MaxUnrealizedProfit** | **Trade-by-Trade** | **MOD-004** | ✅ Yes | ⚠️ Partial (can close, no reset) |
| **RULE-006** | **TradeFrequencyLimit** | **Timer/Cooldown** | **MOD-002, MOD-003** | ✅ Yes | ❌ No (no cooldown) |
| **RULE-007** | **CooldownAfterLoss** | **Timer/Cooldown** | **MOD-002, MOD-003** | ✅ Yes | ❌ No (no cooldown) |
| **RULE-008** | **NoStopLossGrace** | **Trade-by-Trade** | **MOD-003** | ⚠️ Partial | ❌ No (no timer) |
| **RULE-009** | **SessionBlockOutside** | **Hard Lockout** | **MOD-002, MOD-003, MOD-004** | ✅ Yes | ❌ No (no lockout/holiday) |
| **RULE-010** | **AuthLossGuard** | **Hard Lockout** | **MOD-002** | ✅ Yes | ❌ No (can close, no lockout) |
| **RULE-011** | **SymbolBlocks** | **Trade-by-Trade** | **MOD-002** | ✅ Yes | ❌ No (can close, no lockout) |
| RULE-012 | TradeManagement | Automation | None | ✅ Yes | ✅ Yes |
| **RULE-013** | **DailyRealizedProfit** | **Hard Lockout** | **MOD-002, MOD-004** | ✅ Yes | ❌ No (can close, no lockout/reset) |

**Summary:**
- **Fully Functional:** 3 rules (RULE-001, 002, 012) = 23%
- **Partially Functional:** 2 rules (RULE-004, 005) = 15%
- **Blocked:** 8 rules (RULE-003, 006, 007, 008, 009, 010, 011, 013) = 62%

### Dependency Graph

```
RULE-003: DailyRealizedLoss
    └─ Needs: MOD-002 (Lockout Manager) ← CRITICAL BLOCKER
        └─ Depends on: MOD-003 (Timer Manager)
    └─ Needs: MOD-004 (Reset Manager)

RULE-006: TradeFrequencyLimit
    └─ Needs: MOD-002 (Lockout Manager)
        └─ Depends on: MOD-003 (Timer Manager)

RULE-007: CooldownAfterLoss
    └─ Needs: MOD-002 (Lockout Manager)
        └─ Depends on: MOD-003 (Timer Manager)

RULE-008: NoStopLossGrace
    └─ Needs: MOD-003 (Timer Manager)

RULE-009: SessionBlockOutside
    └─ Needs: MOD-002 (Lockout Manager)
        └─ Depends on: MOD-003 (Timer Manager)
    └─ Needs: MOD-004 (Reset Manager) - for holidays

RULE-010: AuthLossGuard
    └─ Needs: MOD-002 (Lockout Manager)
        └─ Depends on: MOD-003 (Timer Manager)

RULE-011: SymbolBlocks
    └─ Needs: MOD-002 (Lockout Manager)
        └─ Depends on: MOD-003 (Timer Manager)

RULE-013: DailyRealizedProfit
    └─ Needs: MOD-002 (Lockout Manager)
        └─ Depends on: MOD-003 (Timer Manager)
    └─ Needs: MOD-004 (Reset Manager)
```

### Critical Path Analysis

**Option 1: Sequential Implementation (Safest)**
```
Week 1: MOD-003 (Timer Manager)
    └─ Enables: RULE-008 (1 rule = 8%)

Week 2-3: MOD-002 (Lockout Manager)
    └─ Depends on: MOD-003
    └─ Enables: RULE-006, 007, 010, 011 (4 rules = 31%)

Week 3-4: MOD-004 (Reset Manager)
    └─ Enables: RULE-003, 004, 005, 009, 013 (5 rules = 38%)

Total: 3-4 weeks to enable ALL blocked rules
```

**Option 2: Parallel Implementation (Faster but risky)**
```
Week 1-2:
    - Team A: MOD-003 (Timer Manager) - 1 week
    - Team B: MOD-004 (Reset Manager) - 1 week
    └─ Enables: RULE-004, 005, 008, 009 (partial) = 31%

Week 2-3:
    - Team A+B: MOD-002 (Lockout Manager) - 1.5 weeks
    └─ Depends on: MOD-003 (ready)
    └─ Enables: ALL remaining rules

Total: 2-3 weeks if parallel, but requires 2 developers
```

**Recommendation:** Sequential implementation (Option 1) is safer due to dependency chain.

---

## Integration Requirements

### SDK Integration Needs

**No direct SDK integration needed** for state managers. State managers provide infrastructure that rules and enforcement modules use.

**Indirect SDK Integration:**
- **MOD-002 (Lockout Manager):** Rules detect breaches via SDK events, then call lockout manager
- **MOD-003 (Timer Manager):** Callbacks invoke enforcement actions (which use SDK)
- **MOD-004 (Reset Manager):** Calls PnL Tracker to reset state

**Event Flow:**
```
SDK Event → Rule Detects Breach → Lockout Manager Sets Lockout → SDK Enforcement (close positions)
```

### Windows Service Integration

**All three missing managers require Windows Service integration:**

1. **Background Tasks** (called by daemon main loop)
   ```python
   async def daemon_main_loop():
       while True:
           # Check lockouts (MOD-002)
           lockout_manager.check_expired_lockouts()  # Every 1s

           # Check timers (MOD-003)
           timer_manager.check_timers()  # Every 1s

           # Check reset time (MOD-004)
           reset_scheduler.check_reset_time()  # Every 60s

           await asyncio.sleep(1)
   ```

2. **Service Lifecycle**
   - **Startup:** Load lockouts from database (`load_lockouts_from_db()`)
   - **Shutdown:** Persist state gracefully
   - **Crash Recovery:** Load state from SQLite on restart

3. **Async/Await Compatibility**
   - All managers must be async-compatible
   - Callbacks must be async-safe
   - No blocking operations

### Persistence Requirements

**SQLite Tables Required:**

```sql
-- MOD-002: Lockout Manager
CREATE TABLE lockouts (
    account_id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lockouts_expires ON lockouts(expires_at);

-- MOD-004: Reset Manager
CREATE TABLE reset_log (
    account_id INTEGER,
    reset_date DATE,
    reset_time DATETIME,
    PRIMARY KEY (account_id, reset_date)
);

-- MOD-003: Timer Manager (NO TABLE - in-memory only)
```

**Schema Initialization:**
- Database module already exists and can handle schema creation
- Add table definitions to `database.py` initialization

**State Survival Requirements:**
- **Lockouts:** Must survive service restart (load from SQLite)
- **Timers:** Recreated from lockouts on restart (no persistence needed)
- **Resets:** Track last reset date to prevent duplicates

---

## Recommended Implementation Order

### Phase 1: Foundation (Complete)
- ✅ Database module
- ✅ PnL Tracker

### Phase 2: Timer Manager (Week 1)
**Why First:**
- No external dependencies
- Simple implementation
- Enables RULE-008 immediately
- Required by Lockout Manager (critical path)

**Implementation Steps:**
1. Create `timer_manager.py` with public API
2. Implement in-memory timer tracking
3. Add background task (`check_timers()`)
4. Write unit tests
5. Integrate with daemon main loop

**Deliverables:**
- ✅ MOD-003: Timer Manager
- ✅ RULE-008: NoStopLossGrace (enabled)

---

### Phase 3: Lockout Manager (Week 2-3)
**Why Second:**
- Depends on Timer Manager (built in Phase 2)
- Blocks most rules (7 rules = 54%)
- Most complex state manager
- Critical for enforcement

**Implementation Steps:**
1. Create `lockout_manager.py` with public API
2. Implement hard lockout logic
3. Implement cooldown logic (integrates Timer Manager)
4. Add SQLite persistence
5. Add symbol-specific lockout support (RULE-011)
6. Write unit tests
7. Integrate with daemon main loop

**Deliverables:**
- ✅ MOD-002: Lockout Manager
- ✅ RULE-006: TradeFrequencyLimit (enabled)
- ✅ RULE-007: CooldownAfterLoss (enabled)
- ✅ RULE-010: AuthLossGuard (enabled)
- ✅ RULE-011: SymbolBlocks (enabled)

---

### Phase 4: Reset Manager (Week 3-4)
**Why Third:**
- Relatively independent (can be parallel with Lockout Manager Phase 3 work)
- Blocks 5 rules
- Requires timezone handling (adds complexity)
- Holiday calendar integration

**Implementation Steps:**
1. Create `reset_scheduler.py` with public API
2. Implement daily reset scheduling
3. Add timezone handling (`pytz` or `zoneinfo`)
4. Load holiday calendar from YAML
5. Add background task (`check_reset_time()`)
6. Add SQLite reset tracking
7. Write unit tests
8. Integrate with daemon main loop

**Deliverables:**
- ✅ MOD-004: Reset Manager
- ✅ RULE-003: DailyRealizedLoss (fully enabled)
- ✅ RULE-004: DailyUnrealizedLoss (fully enabled)
- ✅ RULE-005: MaxUnrealizedProfit (fully enabled)
- ✅ RULE-009: SessionBlockOutside (fully enabled)
- ✅ RULE-013: DailyRealizedProfit (fully enabled)

---

### Phase 5: Event Router (Week 4)
**Why Last:**
- Depends on Lockout Manager
- Integrates all state managers
- Routes events to rules
- Checks lockouts before processing

**Implementation Steps:**
1. Create `event_router.py`
2. Implement lockout check before routing
3. Route events to appropriate rules
4. Handle locked-out account enforcement (close positions)
5. Write integration tests

**Deliverables:**
- ✅ Event Router
- ✅ Full enforcement flow working
- ✅ All 13 rules fully functional

---

## Risk Assessment

### High Risk
1. **Lockout Manager complexity** (symbol-specific lockouts, cooldowns, persistence)
   - Mitigation: Break into phases (hard lockouts first, then cooldowns)

2. **Timezone handling in Reset Manager** (DST transitions, multiple timezones)
   - Mitigation: Use battle-tested library (`pytz`), extensive testing

3. **Background task integration** (daemon main loop must call all managers)
   - Mitigation: Design clear interface, document integration points

### Medium Risk
1. **Lockout state race conditions** (multiple rules setting lockouts simultaneously)
   - Mitigation: Use async locks, clear precedence rules

2. **Timer precision** (1-second granularity may be too coarse for some rules)
   - Mitigation: Acceptable for current rules, can optimize later if needed

### Low Risk
1. **Database schema changes** (adding new tables)
   - Mitigation: Database module already handles migrations

2. **Testing async code** (background tasks, timers)
   - Mitigation: Use `pytest-asyncio`, time mocking utilities

---

## Testing Strategy

### Unit Tests
**Each manager needs:**
- Public API function tests
- Edge case tests
- Persistence tests (load/save)
- Error handling tests

**Example for Lockout Manager:**
```python
async def test_hard_lockout():
    set_lockout(123, "Daily loss", datetime.now() + timedelta(hours=1))
    assert is_locked_out(123) == True

async def test_cooldown():
    set_cooldown(123, "Trade frequency", 60)
    assert is_locked_out(123) == True
    await asyncio.sleep(61)
    check_expired_lockouts()
    assert is_locked_out(123) == False

async def test_persistence():
    set_lockout(123, "Daily loss", datetime.now() + timedelta(hours=1))
    # Simulate restart
    lockout_state.clear()
    load_lockouts_from_db()
    assert is_locked_out(123) == True
```

### Integration Tests
**Test managers working together:**
- Lockout Manager + Timer Manager (cooldowns)
- Reset Manager + PnL Tracker (daily reset)
- Lockout Manager + Event Router (lockout enforcement)

### E2E Tests
**Test full enforcement flow:**
- Rule detects breach → Sets lockout → Event router blocks events → Auto-unlock at expiry

---

## Success Criteria

### MOD-003: Timer Manager
- [ ] All public API functions implemented
- [ ] Background task checks timers every second
- [ ] Callbacks execute when timers expire
- [ ] Multiple timers can run simultaneously
- [ ] Unit tests pass (95% coverage)
- [ ] Integrates with daemon main loop
- [ ] RULE-008 fully functional

### MOD-002: Lockout Manager
- [ ] All public API functions implemented
- [ ] Hard lockouts work (until specific time)
- [ ] Cooldowns work (duration-based with Timer Manager)
- [ ] SQLite persistence works
- [ ] Symbol-specific lockouts work (RULE-011)
- [ ] Background task clears expired lockouts
- [ ] Unit tests pass (95% coverage)
- [ ] Integration tests with Timer Manager pass
- [ ] RULE-006, 007, 010, 011 fully functional

### MOD-004: Reset Manager
- [ ] All public API functions implemented
- [ ] Daily reset triggers at configured time
- [ ] Timezone handling works correctly
- [ ] Holiday calendar integration works
- [ ] SQLite reset tracking works
- [ ] Background task checks reset time every minute
- [ ] Unit tests pass (95% coverage)
- [ ] Integration tests with PnL Tracker + Lockout Manager pass
- [ ] RULE-003, 004, 005, 009, 013 fully functional

---

## Conclusion

**The three missing state managers (MOD-002, MOD-003, MOD-004) are the critical bottleneck preventing 69% of risk rules from functioning.**

**Priority Order:**
1. **MOD-003 (Timer Manager)** - 1 week - Foundation for lockouts
2. **MOD-002 (Lockout Manager)** - 1.5 weeks - Enables most rules
3. **MOD-004 (Reset Manager)** - 1 week - Completes daily P&L rules

**Total Effort:** 3.5 weeks (17-20 developer days)

**After completion:**
- ✅ All 13 risk rules fully functional
- ✅ Complete enforcement system
- ✅ Daily resets working
- ✅ Lockout system working
- ✅ Production-ready state management

**Next Steps:**
1. Review this gap analysis with coordinator
2. Assign implementation priorities
3. Begin Phase 2: Timer Manager implementation
4. Proceed sequentially through Phase 3 (Lockout) and Phase 4 (Reset)

---

**Analysis Complete**

**Researcher:** RESEARCHER 2 - State Management Gap Analyst
**Date:** 2025-10-25
**Files Analyzed:**
- Architecture inventory (MOD specs)
- Risk rules inventory (13 rules)
- Current implementation (`src/risk_manager/state/`)
- Original module specifications

**Findings:**
- 2 of 5 managers implemented (40%)
- 3 managers missing (60%)
- 9 of 13 rules blocked (69%)
- Clear critical path identified
- 3.5 weeks estimated to completion

**Ready for Wave 2 Coordinator synthesis.**
