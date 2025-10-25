# Module Specifications Summary

**Document ID:** MODULES-SUMMARY-001
**Version:** 1.0
**Created:** 2025-10-25
**Status:** Unified Specification

---

## Overview

This document summarizes the four core reusable modules (MOD-001 through MOD-004) that form the foundation of Risk Manager V34's architecture. These modules provide centralized functionality that all risk rules depend on.

---

## Module Inventory

| Module | Name | File | Status | Priority | Blocks |
|--------|------|------|--------|----------|--------|
| **MOD-001** | Database Manager | `src/risk_manager/state/database.py` | ✅ Implemented | Foundation | None |
| **MOD-002** | Lockout Manager | `src/risk_manager/state/lockout_manager.py` | ❌ Missing | **CRITICAL** | 7 rules (54%) |
| **MOD-003** | Timer Manager | `src/risk_manager/state/timer_manager.py` | ❌ Missing | **HIGH** | 4 rules |
| **MOD-004** | Reset Scheduler | `src/risk_manager/state/reset_scheduler.py` | ❌ Missing | **HIGH** | 5 rules |

**Additional Component:**
- **Enforcement Actions** (originally MOD-001 in v2 specs, now separate) - `src/enforcement/actions.py` - NOT IMPLEMENTED

---

## MOD-001: Database Manager

### Purpose
SQLite database abstraction layer for state persistence. Foundation for all state management.

### Public API
```python
class Database:
    def __init__(self, db_path: str)
    async def execute(self, query: str, params: tuple = ()) -> list
    async def execute_many(self, query: str, params: list) -> None
    async def commit(self) -> None
    async def rollback(self) -> None
    async def close(self) -> None
```

### Database Schema
```sql
-- Daily P&L tracking
CREATE TABLE daily_pnl (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    date TEXT NOT NULL,
    realized_pnl REAL DEFAULT 0.0,
    unrealized_pnl REAL DEFAULT 0.0,
    timestamp TEXT NOT NULL,
    UNIQUE(account_id, date)
);

-- Lockout state (MOD-002)
CREATE TABLE lockouts (
    account_id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lockouts_expires ON lockouts(expires_at);

-- Reset history (MOD-004)
CREATE TABLE reset_log (
    account_id INTEGER,
    reset_date DATE,
    reset_time DATETIME,
    PRIMARY KEY (account_id, reset_date)
);
```

### Implementation Status
- ✅ **Implemented:** `src/risk_manager/state/database.py` (~150 lines)
- ✅ Basic schema created (daily_pnl table)
- ⚠️ Missing: lockouts table, reset_log table (needed by MOD-002, MOD-004)

### Dependencies
- None (foundation module)

### Used By
- PnL Tracker (current)
- Lockout Manager (future - MOD-002)
- Reset Scheduler (future - MOD-004)
- All rules indirectly

---

## MOD-002: Lockout Manager

### Purpose
Centralized lockout state management. Handles hard lockouts (until specific time), cooldown timers (duration-based), auto-expiry, and persistence.

### Public API
```python
# Hard lockouts
def set_lockout(account_id: int, reason: str, until: datetime) -> None
def set_cooldown(account_id: int, reason: str, duration_seconds: int) -> None

# Lockout checks
def is_locked_out(account_id: int) -> bool
def get_lockout_info(account_id: int) -> dict | None

# Lockout management
def clear_lockout(account_id: int) -> None
def check_expired_lockouts() -> None  # Background task

# Startup/persistence
def load_lockouts_from_db() -> None
```

### State Management
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

**Persistence:** Saves to `lockouts` table (MOD-001) after every state change

### Background Tasks
- **check_expired_lockouts()** - Runs every 1 second in daemon main loop
- Auto-clears lockouts when `until` time reached
- Notifies Trader CLI of status changes

### Integration Points

**Event Router:**
```python
def route_event(event_type, event_data):
    account_id = event_data['accountId']

    # CHECK LOCKOUT FIRST
    if lockout_manager.is_locked_out(account_id):
        # If locked and new position detected, close immediately
        if event_type == "GatewayUserPosition" and event_data['size'] > 0:
            actions.close_position(account_id, event_data['contractId'])
        return  # Don't process event further

    # Not locked out, route to rules
```

**Timer Manager (MOD-003):**
```python
def set_cooldown(account_id, reason, duration_seconds):
    # Set lockout state
    lockout_state[account_id] = { ... }

    # Start timer (MOD-003)
    timer_manager.start_timer(
        name=f"lockout_{account_id}",
        duration=duration_seconds,
        callback=lambda: clear_lockout(account_id)  # Auto-clear on expiry
    )
```

### Implementation Status
- ❌ **NOT IMPLEMENTED** (0% complete)
- **Estimated Effort:** 1.5 weeks (6-8 developer days)
- **Blocks:** 7 rules (RULE-003, 006, 007, 009, 010, 011, 013) = 54% of all rules

### Dependencies
- **Requires:** MOD-003 (Timer Manager) for cooldown timers
- **Requires:** MOD-001 (Database) for persistence
- **Used By:** 7 rules, Event Router, Trader CLI

### Critical Path
**Must implement after MOD-003** (depends on timer manager for cooldowns)

**See:** Original spec at `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/lockout_manager.md`

**See:** Gap analysis at `/docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md` (lines 129-263)

---

## MOD-003: Timer Manager

### Purpose
Countdown timers for cooldowns, session checks, and scheduled tasks. Provides timer infrastructure with callbacks.

### Public API
```python
def start_timer(name: str, duration: int, callback: callable) -> None
def get_remaining_time(name: str) -> int
def cancel_timer(name: str) -> None
def check_timers() -> None  # Background task
```

### State Management
**In-Memory State (No Database Persistence):**
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

**Note:** Timers are NOT persisted to database. On daemon restart, timers are recreated from lockout expiry times (for lockouts) or discarded (for grace periods).

### Background Tasks
- **check_timers()** - Runs every 1 second in daemon main loop
- Checks if any timer expired
- Executes callback for expired timers
- Removes expired timer from tracking

### Timer Precision
- Background task runs every 1 second
- Timers may fire up to 1 second late (acceptable)
- For more precise timing, reduce check interval (not currently needed)

### Example Usage

**Lockout Cooldown:**
```python
# MOD-002 calls this when setting cooldown
timer_manager.start_timer(
    name="lockout_123",
    duration=1800,  # 30 minutes
    callback=lambda: lockout_manager.clear_lockout(123)
)

# 30 minutes later, timer fires
# → callback executes → lockout cleared automatically
```

**Trader CLI Display:**
```python
# Get remaining time for countdown display
remaining = timer_manager.get_remaining_time("lockout_123")
minutes = remaining // 60
seconds = remaining % 60
print(f"Cooldown: {minutes}m {seconds}s remaining")
```

### Implementation Status
- ❌ **NOT IMPLEMENTED** (0% complete)
- **Estimated Effort:** 1 week (5 developer days)
- **Blocks:** 4 rules (RULE-006, 007, 008, 009)
- **Blocks:** MOD-002 (Lockout Manager depends on this)

### Dependencies
- **None** (no external dependencies)
- **Used By:** MOD-002 (cooldowns), RULE-008 (grace period), RULE-009 (session timers)

### Critical Path
**Must implement first** (MOD-002 depends on this for cooldowns)

**See:** Original spec at `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/timer_manager.md`

**See:** Gap analysis at `/docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md` (lines 266-370)

---

## MOD-004: Reset Scheduler

### Purpose
Daily reset logic for P&L counters and holiday calendar integration. Automates daily reset at midnight ET.

### Public API
```python
def schedule_daily_reset(reset_time: str = "17:00", timezone: str = "America/New_York") -> None
def reset_daily_counters(account_id: int) -> None
def check_reset_time() -> None  # Background task
def is_holiday(date: datetime) -> bool
```

### Reset Sequence
```python
def reset_daily_counters(account_id: int) -> None:
    """Reset all daily counters at midnight ET."""

    # 1. Reset P&L (via PnL Tracker)
    pnl_tracker.reset_daily_pnl(account_id)

    # 2. Clear daily lockouts (via Lockout Manager)
    lockout_manager.clear_lockout(account_id)

    # 3. Reset trade frequency counts (future)
    # trade_counter.reset_counts(account_id)

    # 4. Log reset event
    db.execute(
        "INSERT INTO reset_log (account_id, reset_date, reset_time) VALUES (?, ?, ?)",
        (account_id, date.today(), datetime.now())
    )

    logger.info(f"Daily counters reset for account {account_id}")
```

### Background Tasks
- **check_reset_time()** - Runs every 60 seconds in daemon main loop
- Checks if current time >= configured reset time
- Triggers reset if time reached and not already reset today
- Prevents duplicate resets on same day

### Timezone Handling
```python
import pytz

# Configure reset for midnight ET
et_tz = pytz.timezone('America/New_York')
reset_time = time(0, 0)  # Midnight

# Check if reset time reached (DST-aware)
now = datetime.now(et_tz)
if now.time() >= reset_time and not reset_triggered_today:
    reset_daily_counters(account_id)
    reset_triggered_today = True
```

**Daylight Saving Time:**
- Uses `pytz` for DST-aware timezone handling
- ET = UTC-5 (Standard Time, winter)
- EDT = UTC-4 (Daylight Time, summer)
- `pytz` handles transitions automatically

### Holiday Calendar
**File:** `config/holidays.yaml`
```yaml
holidays:
  - "2025-01-01"  # New Year's Day
  - "2025-07-04"  # Independence Day
  - "2025-12-25"  # Christmas
  # CME futures holidays...
```

**Usage:**
```python
def is_holiday(date: datetime) -> bool:
    """Check if date is a trading holiday."""
    return date.strftime("%Y-%m-%d") in holiday_calendar
```

**Used By:** RULE-009 (SessionBlockOutside) to respect holidays

### Implementation Status
- ❌ **NOT IMPLEMENTED** (0% complete)
- **Estimated Effort:** 1 week (5 developer days)
- **Blocks:** 5 rules (RULE-003, 004, 005, 009, 013)

### Dependencies
- **Requires:** PnL Tracker (to reset P&L)
- **Requires:** Lockout Manager (to clear lockouts)
- **Requires:** Database (to track resets)
- **Requires:** `pytz` library (timezone handling)
- **Used By:** 5 daily P&L rules

### Critical Path
**Can be implemented in parallel with MOD-002/MOD-003** (relatively independent)

**See:** Original spec at `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/reset_scheduler.md`

**See:** Gap analysis at `/docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md` (lines 373-506)

---

## Enforcement Actions Module

**Note:** This was originally called MOD-001 in v2 architecture specs, but Database Manager is now MOD-001 in implementation. Enforcement Actions is a separate critical module.

### Purpose
Centralized enforcement logic - all rules call these functions to execute actions (close positions, cancel orders, etc.).

### Public API
```python
# Position management
def close_all_positions(account_id: int) -> bool
def close_position(account_id: int, contract_id: str) -> bool
def reduce_position_to_limit(account_id: int, contract_id: str, target_size: int) -> bool

# Order management
def cancel_all_orders(account_id: int) -> bool
def cancel_order(account_id: int, order_id: int) -> bool

# Logging
def log_enforcement(message: str) -> None
```

### SDK Integration
**All enforcement functions use Project-X SDK** (not direct API calls):

```python
def close_all_positions(account_id: int) -> bool:
    """Close all open positions via SDK."""

    # Get all positions via SDK
    positions = await sdk.get_open_positions(account_id)

    # Close each position via SDK
    for position in positions:
        await sdk.close_position(
            account_id=account_id,
            contract_id=position.contract_id
        )

    logger.info(f"Closed {len(positions)} positions for account {account_id}")
    log_enforcement(f"CLOSE_ALL_POSITIONS: account={account_id}, count={len(positions)}")
    return True
```

**Key Change from Original Specs:**
- Original specs (v1) described direct TopstepX Gateway API calls
- **Current approach (v2):** Use Project-X-Py SDK for all operations
- SDK provides cleaner, more reliable interface

### Implementation Status
- ⚠️ **PARTIALLY EXISTS** (framework in place, needs SDK integration)
- **Location:** `src/risk_manager/sdk/enforcement.py` (current placeholder)
- **Should Be:** `src/enforcement/actions.py` (per v2 architecture)
- **Estimated Effort:** 1 week (after SDK integration complete)

### Dependencies
- **Requires:** Project-X-Py SDK (TradingSuite)
- **Used By:** All 12 risk rules

### Critical Path
**Can be implemented in parallel** with state managers, but rules cannot fully work without it.

**See:** Original spec at `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/enforcement_actions.md`

---

## Implementation Priority

### Phase 1: Foundation (Week 1)
**Status:** ✅ COMPLETE
- MOD-001 (Database Manager) - Implemented

### Phase 2: Timer Foundation (Week 2)
**Priority:** CRITICAL (blocks MOD-002)
- MOD-003 (Timer Manager) - NOT IMPLEMENTED
- **Why First:** No dependencies, needed by MOD-002

### Phase 3: Lockout System (Week 3-4)
**Priority:** CRITICAL (blocks 54% of rules)
- MOD-002 (Lockout Manager) - NOT IMPLEMENTED
- **Why Second:** Depends on MOD-003, blocks most rules

### Phase 4: Daily Reset (Week 4-5)
**Priority:** HIGH (blocks 5 rules)
- MOD-004 (Reset Scheduler) - NOT IMPLEMENTED
- **Why Third:** Relatively independent, can parallel with MOD-002

### Phase 5: Enforcement Integration (Week 5-6)
**Priority:** HIGH (all rules need this)
- Enforcement Actions - SDK integration
- **Why Last:** Rules can detect breaches, just can't enforce yet

---

## Module Dependencies Graph

```
MOD-001 (Database)
    ↓
    ├─ PnL Tracker (uses DB) ✅ Implemented
    ├─ MOD-002 (Lockout Manager - uses DB) ❌ Missing
    │      ↑
    │      └─ Requires: MOD-003 (Timer Manager)
    │
    └─ MOD-004 (Reset Scheduler - uses DB) ❌ Missing
           ↑
           └─ Requires: PnL Tracker, MOD-002

MOD-003 (Timer Manager) ❌ Missing
    ↓
    └─ Used by: MOD-002 (cooldowns), RULE-008, RULE-009

Enforcement Actions ⚠️ Partial
    ↓
    └─ Used by: All 12 rules
```

**Critical Path:**
1. Implement MOD-003 first (no dependencies)
2. Then implement MOD-002 (depends on MOD-003)
3. Then implement MOD-004 (depends on MOD-002)
4. Then complete Enforcement Actions (SDK integration)

---

## Testing Strategy

### MOD-001 (Database Manager)
- ✅ Unit tests exist: `tests/unit/test_state/test_database.py`
- ✅ Schema creation tests
- ✅ Query execution tests
- ✅ Transaction tests

### MOD-002 (Lockout Manager)
**Needed Tests:**
- Hard lockout (set, check, auto-clear)
- Cooldown timer (set, check, auto-clear via callback)
- Persistence (save to DB, load from DB after restart)
- Symbol-specific lockout (RULE-011 requirement)
- Multiple simultaneous lockouts

### MOD-003 (Timer Manager)
**Needed Tests:**
- Start timer, callback fires after duration
- Get remaining time decreases over time
- Cancel timer before expiry
- Multiple timers running simultaneously
- Timer precision (acceptable 1-second variance)

### MOD-004 (Reset Scheduler)
**Needed Tests:**
- Daily reset triggers at configured time
- Timezone conversion works correctly (ET/EDT)
- Holiday detection prevents trading
- Reset doesn't trigger twice on same day
- Reset survives service restart

---

## Related Documentation

### Original Module Specifications
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/enforcement_actions.md`
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/lockout_manager.md`
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/timer_manager.md`
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/reset_scheduler.md`

### Wave Analysis
- `/docs/analysis/wave1-feature-inventory/03-ARCHITECTURE-INVENTORY.md` (Module descriptions)
- `/docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md` (Detailed gap analysis)

### Current Implementation
- `src/risk_manager/state/database.py` - MOD-001 (Implemented)
- `src/risk_manager/state/pnl_tracker.py` - PnL Tracker (Implemented)

---

**This summary provides a complete overview of all core modules needed for Risk Manager V34.**
