# Architecture & Modules Feature Inventory

**Document ID:** 03-ARCHITECTURE-INVENTORY
**Created:** 2025-10-25
**Researcher:** RESEARCHER 3: Architecture Specialist
**Status:** Complete

---

## Executive Summary

This document analyzes the system architecture evolution from v1 to v2, detailing core modules, component relationships, and key design decisions for the Risk Manager V34 project.

### Key Findings

1. **Architecture evolved from v1 (initial planning) to v2 (refined modular design)**
2. **Four core reusable modules (MOD-001 to MOD-004) form the foundation**
3. **Event-driven architecture using TopstepX SignalR WebSocket**
4. **200-line file limit strictly enforced for modularity**
5. **SDK-first approach was NOT available at spec time** (critical context)

---

## System Architecture Evolution

### Version 1 (Initial Planning - ARCH-V1)

**Date:** 2025-01-17
**Status:** Historical Reference
**Context:** Original planning session notes

#### Core Concepts (v1)

**Technology Stack:**
- **Language:** Python (beginner-friendly, great for daemons)
- **API Integration:** SignalR via `signalrcore` library
- **Why Python:** Clarity and simplicity over efficiency

**Windows Service Approach:**
- Daemon runs as Windows Service (true protection)
- Auto-starts on computer boot
- Admin password required to stop/reconfigure
- Professional/hedge fund grade security

**Configuration Security:**
- **Development:** Config files in regular user folder
- **Production:** Config moved to `C:\ProgramData\RiskManager\`
- Windows ACL permissions (only Admin + SYSTEM can access)
- Trader cannot view or edit config files

**Architecture Philosophy:**
- **Modular from Day 1**
- **One rule = one file**
- **No file over 200 lines** (hard limit)
- **Clear interfaces between modules**
- **Adding features = adding files** (no refactoring existing code)

**Phase-Based Implementation:**
- **Phase 1:** Solid base + 2-3 simple rules
  - Complete architecture (daemon, API, state, CLI)
  - MaxContracts, MaxContractsPerInstrument, SessionBlockOutside
  - Testing infrastructure
  - Windows Service setup
- **Phase 2+:** Add rules one by one
  - Each new rule = new file in `rules/`
  - No major refactoring needed

**Data Persistence:**
- SQLite database for state persistence
- Survives computer crashes/reboots
- Stores: P&L, trade counts, cooldown timers, lockout states

#### Directory Structure (v1)

```
risk-manager/
├── src/
│   ├── core/                    # Core daemon logic
│   │   ├── daemon.py            (~100 lines)
│   │   ├── risk_engine.py       (~150 lines)
│   │   ├── rule_loader.py       (~80 lines)
│   │   ├── enforcement.py       (~100 lines)
│   │   └── priority_handler.py  (~70 lines)
│   │
│   ├── api/                     # TopstepX API integration
│   │   ├── client.py            (~120 lines)
│   │   ├── signalr_listener.py  (~150 lines)
│   │   ├── auth.py              (~60 lines)
│   │   └── position_manager.py  (~80 lines)
│   │
│   ├── rules/                   # Risk rules (each = 1 file)
│   │   ├── base_rule.py         (~60 lines)
│   │   ├── max_contracts.py     (~90 lines)
│   │   ├── max_contracts_per_instrument.py (~90 lines)
│   │   └── [10 more rules...]
│   │
│   ├── state/                   # State management
│   │   ├── state_manager.py     (~150 lines)
│   │   ├── persistence.py       (~120 lines)
│   │   ├── timer_manager.py     (~100 lines)
│   │   └── pnl_tracker.py       (~110 lines)
│   │
│   ├── cli/                     # Command-line interfaces
│   │   ├── admin/               # Password-protected
│   │   └── trader/              # View-only
│   │
│   ├── config/                  # Configuration management
│   ├── utils/                   # Shared utilities
│   └── service/                 # Windows Service wrapper
```

**Key v1 Characteristics:**
- Direct TopstepX API integration (no SDK mentioned)
- Manual WebSocket handling via `signalrcore`
- Manual position/order management
- All 12 rules planned upfront

---

### Version 2 (Refined Architecture - ARCH-V2)

**Date:** 2025-01-17
**Status:** Current system architecture
**Dependencies:** ARCH-V1, MOD-001, MOD-002, MOD-003, MOD-004

#### Evolution from v1 to v2

**Major Changes:**

1. **Introduced Reusable Modules:**
   - **MOD-001:** Enforcement Actions (centralized enforcement)
   - **MOD-002:** Lockout Manager (centralized lockout state)
   - **MOD-003:** Timer Manager (countdown timers)
   - **MOD-004:** Reset Scheduler (daily resets)

2. **Refined Core Structure:**
   - `priority_handler.py` → Removed (simplified)
   - `event_router.py` → Added (routes events to rules)
   - `enforcement.py` → Moved to `enforcement/` module
   - Added `connection_manager.py` for WebSocket health

3. **Enhanced State Management:**
   - Added `lockout_manager.py` (MOD-002)
   - Added `reset_scheduler.py` (MOD-004)
   - Timer management formalized (MOD-003)

4. **Clearer Separation of Concerns:**
   - Enforcement logic centralized in MOD-001
   - Lockout logic centralized in MOD-002
   - All rules now call modules (no direct API calls)

#### Directory Structure (v2)

```
risk-manager/
├── src/
│   ├── core/                    # Core daemon logic
│   │   ├── daemon.py            (~100 lines)
│   │   ├── risk_engine.py       (~150 lines)
│   │   ├── rule_loader.py       (~80 lines)
│   │   └── event_router.py      (~100 lines) [NEW]
│   │
│   ├── api/                     # TopstepX API integration
│   │   ├── auth.py              (~80 lines)
│   │   ├── rest_client.py       (~120 lines)
│   │   ├── signalr_listener.py  (~150 lines)
│   │   └── connection_manager.py (~100 lines) [NEW]
│   │
│   ├── enforcement/             # MOD-001 [NEW MODULE]
│   │   ├── actions.py           (~120 lines)
│   │   └── enforcement_engine.py (~80 lines)
│   │
│   ├── rules/                   # Risk rules (12 rules)
│   │   ├── base_rule.py         (~80 lines)
│   │   └── [12 individual rule files]
│   │
│   ├── state/                   # State management
│   │   ├── state_manager.py     (~150 lines)
│   │   ├── persistence.py       (~120 lines)
│   │   ├── lockout_manager.py   (~150 lines) [MOD-002]
│   │   ├── timer_manager.py     (~120 lines) [MOD-003]
│   │   ├── reset_scheduler.py   (~100 lines) [MOD-004]
│   │   └── pnl_tracker.py       (~130 lines)
│   │
│   ├── cli/                     # CLIs
│   │   ├── admin/               # Password-protected
│   │   │   ├── admin_main.py    (~100 lines)
│   │   │   ├── auth.py          (~60 lines)
│   │   │   ├── configure_rules.py (~150 lines)
│   │   │   ├── manage_accounts.py (~120 lines)
│   │   │   └── service_control.py (~80 lines)
│   │   │
│   │   └── trader/              # View-only
│   │       ├── trader_main.py   (~80 lines)
│   │       ├── status_screen.py (~120 lines)
│   │       ├── lockout_display.py (~100 lines) [NEW]
│   │       ├── logs_viewer.py   (~100 lines)
│   │       ├── clock_tracker.py (~70 lines)
│   │       └── formatting.py    (~80 lines)
│   │
│   ├── config/                  # Configuration
│   ├── utils/                   # Utilities
│   └── service/                 # Windows Service
```

---

### Evolution Analysis

#### What Changed and Why

| Aspect | v1 | v2 | Reason for Change |
|--------|----|----|-------------------|
| **Enforcement** | Scattered in rules | Centralized in MOD-001 | Eliminate duplication, ensure consistency |
| **Lockout State** | In state_manager | Dedicated MOD-002 | Complex enough to warrant own module |
| **Timers** | Basic timer_manager | Formalized MOD-003 | Better integration with lockouts |
| **Event Routing** | In risk_engine | Dedicated event_router | Clear separation of concerns |
| **Connection Health** | In signalr_listener | Dedicated connection_manager | Handle reconnection logic separately |
| **CLI Lockout Display** | In status_screen | Dedicated lockout_display.py | Lockouts important enough for own screen |

#### Design Improvements in v2

1. **Reusable Modules:** Four core modules (MOD-001 to MOD-004) that all rules call
2. **Single Responsibility:** Each module has one clear purpose
3. **Testability:** Mock modules instead of API for rule testing
4. **Consistency:** All rules enforce/lockout the same way
5. **Documentation:** Each module has detailed spec document

---

## Core Modules

### MOD-001: Enforcement Actions

**File:** `src/enforcement/actions.py`
**Purpose:** Centralized enforcement logic - all rules call these functions

#### Key Principle

**All risk rules call MOD-001 to enforce actions. NO rule directly calls the API.**

**Benefits:**
- No duplication (enforcement logic written once)
- Consistency (all rules enforce the same way)
- Testability (mock MOD-001 for rule testing)
- Logging (all enforcement logged in one place)

#### Public API

##### 1. close_all_positions(account_id)
**Purpose:** Close all open positions for an account

**Implementation:**
```python
def close_all_positions(account_id: int) -> bool:
    # Step 1: Get all open positions
    response = rest_client.post(
        "/api/Position/searchOpen",
        json={"accountId": account_id}
    )

    # Step 2: Close each position
    for position in positions:
        rest_client.post(
            "/api/Position/closeContract",
            json={"accountId": account_id, "contractId": position["contractId"]}
        )

    logger.info(f"Closed {len(positions)} positions for account {account_id}")
    log_enforcement(f"CLOSE_ALL_POSITIONS: account={account_id}, count={len(positions)}")
    return True
```

**REST API Calls:**
- `POST /api/Position/searchOpen` - Get all positions
- `POST /api/Position/closeContract` - Close each position

**Used By:** RULE-001, 003, 009 (all "close all" rules)

##### 2. close_position(account_id, contract_id)
**Purpose:** Close a specific position

**REST API Call:**
- `POST /api/Position/closeContract`

**Used By:** RULE-002, 009, 011 (symbol-specific rules)

##### 3. reduce_position_to_limit(account_id, contract_id, target_size)
**Purpose:** Partially close position to reach target size

**Logic:**
1. Get current position size
2. Calculate contracts to close (current - target)
3. Partially close position

**REST API Calls:**
- `POST /api/Position/searchOpen` - Get current size
- `POST /api/Position/partialCloseContract` - Reduce position

**Used By:** RULE-001 (with reduce_to_limit option), RULE-002

##### 4. cancel_all_orders(account_id)
**Purpose:** Cancel all pending orders

**REST API Calls:**
- `POST /api/Order/searchOpen` - Get all orders
- `POST /api/Order/cancel` - Cancel each order

**Used By:** RULE-003, 009 (lockout rules)

##### 5. cancel_order(account_id, order_id)
**Purpose:** Cancel a specific order

**REST API Call:**
- `POST /api/Order/cancel`

#### Enforcement Logging

**Log Format:**
```
[2025-01-17 14:23:15] CLOSE_ALL_POSITIONS: account=123, count=3
[2025-01-17 14:23:15] CANCEL_ALL_ORDERS: account=123, count=2
[2025-01-17 14:23:16] CLOSE_POSITION: account=123, contract=CON.F.US.MNQ.U25
[2025-01-17 14:23:17] REDUCE_POSITION: account=123, contract=CON.F.US.ES.U25, from=3, to=2
```

**Log File:** `logs/enforcement.log`

#### Error Handling

**Rate Limiting:**
- Handle 429 Too Many Requests
- Back off 30 seconds

**Authentication Errors:**
- Handle 401 Unauthorized
- Refresh token and retry

**Retry Logic:**
- Max 3 retries
- Exponential backoff (2^attempt seconds)

#### Performance

| Function | API Calls | Typical Latency |
|----------|-----------|-----------------|
| `close_all_positions` | 1 search + n closes | 100-500ms (n=1-5) |
| `close_position` | 1 close | 50-100ms |
| `cancel_all_orders` | 1 search + n cancels | 100-500ms (n=1-10) |
| `reduce_position_to_limit` | 1 search + 1 partial | 100-200ms |

**Enforcement Speed:** Typically < 500ms from breach detection to API call completion

---

### MOD-002: Lockout Manager

**File:** `src/state/lockout_manager.py`
**Purpose:** Centralized lockout state management - all lockout rules call these functions

**Dependencies:** MOD-003 (Timer Manager)

#### Core Principle

**All lockout states managed in one place. Rules set lockouts, event_router checks lockouts.**

#### Handles

1. **Hard lockouts** - Until specific time (daily reset, session start)
2. **Cooldown timers** - Duration-based (trade frequency, cooldown after loss)
3. **Auto-expiry** - Background task clears expired lockouts
4. **Persistence** - Saves to SQLite for crash recovery

#### Public API

##### 1. set_lockout(account_id, reason, until)
**Purpose:** Set hard lockout until specific datetime

**Implementation:**
```python
def set_lockout(account_id: int, reason: str, until: datetime) -> None:
    lockout_state[account_id] = {
        "reason": reason,
        "until": until,
        "type": "hard_lockout",
        "created_at": datetime.now()
    }

    # Persist to SQLite
    db.execute(
        "INSERT OR REPLACE INTO lockouts (account_id, reason, expires_at, created_at) VALUES (?, ?, ?, ?)",
        (account_id, reason, until, datetime.now())
    )

    # Notify Trader CLI
    cli.update_lockout_display(account_id, reason, until)
```

**Example:**
```python
set_lockout(123, "Daily loss limit hit", datetime(2025, 1, 17, 17, 0))
```

**Used By:** RULE-003 (DailyRealizedLoss), RULE-009 (SessionBlockOutside), RULE-011 (SymbolBlocks)

##### 2. set_cooldown(account_id, reason, duration_seconds)
**Purpose:** Set lockout for specific duration

**Implementation:**
```python
def set_cooldown(account_id: int, reason: str, duration_seconds: int) -> None:
    until = datetime.now() + timedelta(seconds=duration_seconds)

    lockout_state[account_id] = {
        "reason": reason,
        "until": until,
        "type": "cooldown",
        "duration": duration_seconds,
        "created_at": datetime.now()
    }

    # Start countdown timer (via MOD-003)
    timer_manager.start_timer(
        name=f"lockout_{account_id}",
        duration=duration_seconds,
        callback=lambda: clear_lockout(account_id)
    )
```

**Example:**
```python
set_cooldown(123, "Trade frequency limit", 1800)  # 30 minutes
```

**Used By:** RULE-006 (TradeFrequencyLimit), RULE-007 (CooldownAfterLoss)

##### 3. is_locked_out(account_id)
**Purpose:** Check if account is currently locked out

**Called By:** `event_router.py` before processing every event

**Event Router Integration:**
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

##### 4. get_lockout_info(account_id)
**Purpose:** Get lockout details for CLI display

**Returns:**
```python
{
    "reason": "Daily loss limit hit",
    "until": datetime(2025, 1, 17, 17, 0),
    "remaining_seconds": 9845,
    "type": "hard_lockout"
}
```

**Used By:** Trader CLI for displaying lockout timers

##### 5. clear_lockout(account_id)
**Purpose:** Remove lockout (manual or auto-expiry)

**Called By:**
- Background task (auto-expiry)
- Timer callback (cooldown expiry)
- Admin CLI (manual unlock)

##### 6. check_expired_lockouts()
**Purpose:** Background task to auto-clear expired lockouts

**Called By:** `src/core/daemon.py` main loop (every second)

#### State Persistence (SQLite)

**Database Schema:**
```sql
CREATE TABLE lockouts (
    account_id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lockouts_expires ON lockouts(expires_at);
```

**Load State on Startup:**
```python
def load_lockouts_from_db() -> None:
    rows = db.execute(
        "SELECT account_id, reason, expires_at FROM lockouts WHERE expires_at > ?",
        (datetime.now(),)
    )

    for row in rows:
        account_id, reason, until = row
        lockout_state[account_id] = {
            "reason": reason,
            "until": until,
            "type": "hard_lockout",
            "created_at": datetime.now()
        }
```

#### Lockout State (In-Memory)

```python
lockout_state = {
    123: {
        "reason": "Daily loss limit hit",
        "until": datetime(2025, 1, 17, 17, 0),
        "type": "hard_lockout",
        "created_at": datetime(2025, 1, 17, 14, 23)
    },
    456: {
        "reason": "Trade frequency limit (3/3 trades)",
        "until": datetime(2025, 1, 17, 14, 53),
        "type": "cooldown",
        "duration": 1800,
        "created_at": datetime(2025, 1, 17, 14, 23)
    }
}
```

#### Integration with Timer Manager (MOD-003)

**For cooldowns:**
```python
def set_cooldown(account_id, reason, duration_seconds):
    # Set lockout state
    lockout_state[account_id] = { ... }

    # Start timer (MOD-003)
    timer_manager.start_timer(
        name=f"lockout_{account_id}",
        duration=duration_seconds,
        callback=lambda: clear_lockout(account_id)  # Auto-clear when timer expires
    )
```

#### CLI Integration

**Trader CLI Display:**
```python
def display_lockout_status(account_id):
    lockout_info = lockout_manager.get_lockout_info(account_id)

    if lockout_info:
        remaining = lockout_info['remaining_seconds']
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60

        print(f"🔴 LOCKED OUT")
        print(f"Reason: {lockout_info['reason']}")
        print(f"Unlocks in: {hours}h {minutes}m {seconds}s")
    else:
        print(f"🟢 OK TO TRADE")
```

---

### MOD-003: Timer Manager

**File:** `src/state/timer_manager.py`
**Purpose:** Countdown timers for cooldowns, session checks, and scheduled tasks

**Dependencies:** None

#### Public API

##### 1. start_timer(name, duration, callback)
**Purpose:** Start countdown timer with callback

**Implementation:**
```python
def start_timer(name: str, duration: int, callback: callable) -> None:
    timers[name] = {
        "expires_at": datetime.now() + timedelta(seconds=duration),
        "callback": callback,
        "duration": duration
    }
```

**Example:**
```python
start_timer("lockout_123", 1800, lambda: clear_lockout(123))
```

##### 2. get_remaining_time(name)
**Purpose:** Get seconds remaining on timer

**Returns:** Integer (seconds), 0 if timer doesn't exist

**Used By:** Trader CLI for countdown display

##### 3. check_timers()
**Purpose:** Background task - check timers and fire callbacks

**Implementation:**
```python
def check_timers() -> None:
    now = datetime.now()
    expired = []

    for name, timer in timers.items():
        if now >= timer['expires_at']:
            timer['callback']()  # Execute callback
            expired.append(name)

    for name in expired:
        del timers[name]
```

**Called By:** `src/core/daemon.py` main loop (every second)

##### 4. cancel_timer(name)
**Purpose:** Stop timer before it expires

**Used By:** MOD-002 (lockout cooldowns), RULE-009 (session timers)

---

### MOD-004: Reset Scheduler

**File:** `src/state/reset_scheduler.py`
**Purpose:** Daily reset logic for P&L counters and holiday calendar integration

**Dependencies:** None

#### Public API

##### 1. schedule_daily_reset(reset_time, timezone)
**Purpose:** Schedule daily reset at specific time

**Implementation:**
```python
def schedule_daily_reset(reset_time: str = "17:00", timezone: str = "America/New_York") -> None:
    reset_config['time'] = reset_time
    reset_config['timezone'] = timezone
    logger.info(f"Daily reset scheduled for {reset_time} {timezone}")
```

**Example:**
```python
schedule_daily_reset("17:00", "America/New_York")  # 5:00 PM ET
```

##### 2. reset_daily_counters(account_id)
**Purpose:** Reset all daily counters (P&L, trade counts)

**Implementation:**
```python
def reset_daily_counters(account_id: int) -> None:
    # Reset P&L
    db.execute(
        "UPDATE daily_pnl SET realized_pnl=0, unrealized_pnl=0 WHERE account_id=?",
        (account_id,)
    )

    # Clear daily lockouts
    lockout_manager.clear_lockout(account_id)

    logger.info(f"Daily counters reset for account {account_id}")
```

##### 3. check_reset_time()
**Purpose:** Background task - check if reset time reached

**Called By:** `src/core/daemon.py` main loop (every minute)

**Implementation:**
```python
def check_reset_time() -> None:
    tz = timezone(reset_config['timezone'])
    now = datetime.now(tz)
    reset_time = time.fromisoformat(reset_config['time'])

    if now.time() >= reset_time and not reset_triggered_today:
        reset_daily_counters(account_id)
        reset_triggered_today = True
```

##### 4. is_holiday(date)
**Purpose:** Check if date is a trading holiday

**Implementation:**
```python
def is_holiday(date: datetime) -> bool:
    return date.strftime("%Y-%m-%d") in holiday_calendar
```

**Holiday Calendar (`config/holidays.yaml`):**
```yaml
holidays:
  - "2025-01-01"  # New Year's Day
  - "2025-07-04"  # Independence Day
  - "2025-12-25"  # Christmas
```

**Used By:** RULE-003, 004, 005 (daily P&L rules), RULE-009 (session/holiday checks)

---

## Component Relationships

### Architecture Layers

#### Layer 1: Windows Service (Entry Point)
```
src/service/windows_service.py
    ↓
src/core/daemon.py (main event loop)
    ↓
src/core/risk_engine.py (orchestrator)
```

#### Layer 2: API Integration
```
src/api/signalr_listener.py
    ↓ (receives events)
src/core/event_router.py
    ↓ (routes to rules)
src/rules/*.py (each rule processes)
```

#### Layer 3: Enforcement & State
```
src/rules/*.py (detects breach)
    ↓
src/enforcement/actions.py (executes) [MOD-001]
    ↓
src/state/lockout_manager.py (manages lockouts) [MOD-002]
    ↓
src/state/persistence.py (saves to SQLite)
```

#### Layer 4: CLI Interfaces
```
src/cli/admin/admin_main.py (admin interface)
src/cli/trader/trader_main.py (trader interface)
    ↓ (both read from)
src/state/state_manager.py (current state)
```

---

## Data Flow: Real-Time Event Processing

### Complete Event Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. Trader places order on broker                                       │
└────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. TopstepX Gateway sends event via SignalR WebSocket                  │
│    - GatewayUserTrade (for P&L tracking)                               │
│    - GatewayUserPosition (for position updates)                        │
│    - GatewayUserOrder (for order status)                               │
└────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. signalr_listener.py receives event                                  │
│    - Validates event structure                                         │
│    - Logs event to api.log                                             │
└────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. event_router.py routes to relevant rules                            │
│    - GatewayUserTrade → DailyLoss, TradeFreq, CooldownAfterLoss        │
│    - GatewayUserPosition → MaxContracts, MaxContractsPerInstrument     │
│    - GatewayUserOrder → NoStopLossGrace                                │
└────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. Each rule checks breach condition                                   │
│    Example: daily_realized_loss.py                                     │
│    - current_pnl = pnl_tracker.get_daily_realized_pnl()                │
│    - if current_pnl <= -limit: BREACH DETECTED                         │
└────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. Enforcement actions execute (MOD-001)                               │
│    - actions.close_all_positions(account_id)                           │
│    - actions.cancel_all_orders(account_id)                             │
│    (REST API calls happen here)                                        │
└────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 7. Lockout manager sets lockout (MOD-002)                              │
│    - lockout.set_lockout(account_id, "Daily loss limit", until=17:00) │
│    - Lockout state saved to SQLite                                     │
└────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 8. Trader CLI updates in real-time                                     │
│    - Displays: "🔴 LOCKED OUT - Daily loss limit - Reset at 5:00 PM"  │
│    - Shows countdown timer: "3h 27m remaining"                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module Responsibilities

### Core Modules

| Module | File | Responsibility | Used By |
|--------|------|----------------|---------|
| **MOD-001** | `src/enforcement/actions.py` | Execute enforcement actions (close, cancel) | All 12 rules |
| **MOD-002** | `src/state/lockout_manager.py` | Manage lockout states and timers | RULE-003, 004, 005, 006, 007, 009, 010, 011 |
| **MOD-003** | `src/state/timer_manager.py` | Countdown timers with callbacks | MOD-002, RULE-009 |
| **MOD-004** | `src/state/reset_scheduler.py` | Daily reset + holiday calendar | RULE-003, 004, 005, 009 |

### Rule Categories by Module Usage

**Enforcement Only (MOD-001):**
- RULE-001: MaxContracts
- RULE-002: MaxContractsPerInstrument

**Enforcement + Lockout (MOD-001 + MOD-002):**
- RULE-003: DailyRealizedLoss
- RULE-004: DailyUnrealizedLoss
- RULE-005: MaxUnrealizedProfit
- RULE-009: SessionBlockOutside
- RULE-010: AuthLossGuard
- RULE-011: SymbolBlocks

**Enforcement + Lockout + Timers (MOD-001 + MOD-002 + MOD-003):**
- RULE-006: TradeFrequencyLimit
- RULE-007: CooldownAfterLoss

**Complex Rules:**
- RULE-008: NoStopLossGrace (uses MOD-003 for grace period timer)
- RULE-012: TradeManagement (uses MOD-003 for breakeven/trail logic)

---

## Enforcement Action Types and Workflows

### Action Types

1. **CLOSE_ALL_POSITIONS**
   - Close all open positions immediately
   - Used when: Account-wide breach (daily loss, max contracts)
   - Typical latency: 100-500ms

2. **CLOSE_POSITION**
   - Close specific position by contract_id
   - Used when: Symbol-specific breach (symbol blocks, per-instrument limits)
   - Typical latency: 50-100ms

3. **REDUCE_POSITION**
   - Partially close to reach target size
   - Used when: Gradual enforcement (max_contracts with reduce_to_limit)
   - Typical latency: 100-200ms

4. **CANCEL_ALL_ORDERS**
   - Cancel all pending orders
   - Used when: Lockout triggered (prevent new entries)
   - Typical latency: 100-500ms

5. **CANCEL_ORDER**
   - Cancel specific order by order_id
   - Used when: Individual order violates rule
   - Typical latency: 50-100ms

### Workflow Patterns

#### Pattern 1: Immediate Close + No Lockout
```python
# Example: MaxContracts breach
actions.close_all_positions(account_id)
# No lockout - trader can continue trading if breach clears
```

**Used By:** RULE-001, RULE-002

#### Pattern 2: Immediate Close + Hard Lockout
```python
# Example: Daily loss limit breach
actions.close_all_positions(account_id)
actions.cancel_all_orders(account_id)
lockout_manager.set_lockout(account_id, "Daily loss limit", until=17:00)
```

**Used By:** RULE-003, RULE-004, RULE-005, RULE-009, RULE-011

#### Pattern 3: No Close + Cooldown Lockout
```python
# Example: Trade frequency limit breach
lockout_manager.set_cooldown(account_id, "Trade frequency", duration=1800)
# No close - just prevent new trades for 30 minutes
```

**Used By:** RULE-006

#### Pattern 4: Close + Cooldown Lockout
```python
# Example: Cooldown after loss
actions.close_all_positions(account_id)
lockout_manager.set_cooldown(account_id, "Cooldown after loss", duration=3600)
```

**Used By:** RULE-007

---

## Key Design Decisions

### 1. Modular Enforcement (MOD-001)

**Decision:** All rules call centralized enforcement module

**Rationale:**
- Eliminate code duplication
- Ensure consistency across all rules
- Centralized logging and error handling
- Easy to mock for testing

**Impact:**
- Rules are < 100 lines (focus on logic, not API calls)
- Enforcement behavior is consistent
- Changes to API only need updates in one place

### 2. Centralized Lockout (MOD-002)

**Decision:** Single module manages all lockout states

**Rationale:**
- Multiple rules need lockout capability
- Lockout state is complex (hard lockout vs cooldown, persistence, auto-expiry)
- Event router needs to check lockout before processing events

**Impact:**
- Rules just call `set_lockout()` or `set_cooldown()`
- Event router has single point to check: `is_locked_out()`
- Crash recovery through SQLite persistence
- Trader CLI gets consistent lockout display

### 3. Event-Driven Architecture

**Decision:** SignalR WebSocket events trigger rule checks (no polling)

**Rationale:**
- TopstepX provides real-time events
- Instant notification when trader's order fills
- No need to poll for position/order changes
- Efficient and low-latency

**Impact:**
- Rules react within milliseconds of events
- No API rate limit issues from polling
- Clean event → rule → enforcement flow

### 4. State Persistence (SQLite)

**Decision:** All critical state saved to SQLite database

**Rationale:**
- Computer can crash or restart anytime
- P&L, lockouts, timers must survive restarts
- Need historical data for debugging

**Impact:**
- Daemon can crash and resume exactly where it left off
- Daily lockouts persist across restarts
- Cooldown timers restored on startup

### 5. File Size Limit (200 lines)

**Decision:** Strict 200-line maximum per file

**Rationale:**
- Beginner-friendly (small files easy to understand)
- Forces modular design
- Each file has single, clear purpose
- Easy to navigate codebase

**Impact:**
- Highly modular architecture
- Clear separation of concerns
- Easy to add new rules without touching existing code

### 6. One Rule = One File

**Decision:** Each risk rule is its own file

**Rationale:**
- Rules are independent of each other
- Adding new rule = adding new file (no refactoring)
- Easy to enable/disable rules
- Clear which rules are implemented

**Impact:**
- `rules/` directory grows from 3 to 12 files (Phase 1 → Full)
- No merge conflicts when adding rules
- Easy to test rules in isolation

### 7. Windows Service (Production Mode)

**Decision:** Run as Windows Service with admin protection

**Rationale:**
- Trader cannot kill the daemon (requires admin password)
- Auto-starts on boot
- Professional/hedge fund grade security
- Config files protected by Windows ACL

**Impact:**
- "Virtually unkillable" by trader
- Production-grade reliability
- Clear admin vs trader separation

### 8. No Order Interception

**Decision:** Can't intercept orders before they reach broker

**Rationale:**
- TopstepX API doesn't support pre-order validation
- Orders fill first, then events sent
- Close positions within milliseconds after fill

**Impact:**
- Reactive enforcement (not preventive)
- Emphasis on speed (< 500ms enforcement)
- Rules need to handle "already filled" scenarios

### 9. SDK-First (NOT AVAILABLE AT SPEC TIME)

**CRITICAL CONTEXT:**
These specs (v1 and v2) were written **BEFORE** the Project-X SDK existed.

**At Spec Time:**
- Direct TopstepX Gateway API integration required
- Manual SignalR WebSocket handling (`signalrcore` library)
- Manual position/order management
- Manual state tracking

**Current Implementation (V34):**
- **Project-X-Py SDK available** (v3.5.9)
- SDK handles WebSocket, auth, positions, orders
- Risk Manager uses SDK as foundation
- Add risk logic on top of SDK

**See:** `docs/current/SDK_INTEGRATION_GUIDE.md` for SDK mapping

---

## Conflicts Between v1 and v2

### Resolved Differences

1. **enforcement.py location:**
   - v1: `src/core/enforcement.py`
   - v2: `src/enforcement/actions.py` (dedicated module)
   - **Resolution:** v2 approach is better (module deserves own directory)

2. **priority_handler.py:**
   - v1: Included `src/core/priority_handler.py`
   - v2: Removed (not mentioned)
   - **Resolution:** Simplified - rules don't need explicit priority handler

3. **event_router.py:**
   - v1: Not mentioned
   - v2: Added `src/core/event_router.py`
   - **Resolution:** Needed for clean event routing + lockout checks

4. **connection_manager.py:**
   - v1: Not mentioned
   - v2: Added `src/api/connection_manager.py`
   - **Resolution:** Needed for WebSocket reconnection logic

5. **lockout_display.py:**
   - v1: Lockout display in `timer_display.py`
   - v2: Dedicated `lockout_display.py`
   - **Resolution:** Lockouts important enough for own CLI screen

### No Conflicts Remaining

All v1 → v2 changes are **refinements** and **improvements**, not contradictions. v2 is the evolved, production-ready architecture.

---

## Configuration Management

### accounts.yaml (TopstepX Auth)

```yaml
topstepx:
  username: "your_username"
  api_key: "your_api_key_here"

monitored_account:
  account_id: 123
  account_name: "Main Trading Account"
```

### risk_config.yaml (Rule Settings)

#### Trade-by-Trade Rules (No Lockout)

```yaml
max_contracts:
  enabled: true
  limit: 5
  count_type: "net"
  close_all: true
  reduce_to_limit: false

max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 2
    ES: 1
    NQ: 1
  enforcement: "reduce_to_limit"
  unknown_symbol_action: "block"
```

#### Hard Lockout Rules

```yaml
daily_realized_loss:
  enabled: true
  limit: -500
  reset_time: "17:00"
  timezone: "America/New_York"
  enforcement: "close_all_and_lockout"
```

#### Session Rules

```yaml
session_block_outside:
  enabled: true
  global_session:
    enabled: true
    start: "09:30"
    end: "16:00"
    timezone: "America/New_York"
  per_instrument_sessions:
    enabled: true
    sessions:
      ES:
        start: "18:00"
        end: "17:00"
        timezone: "America/Chicago"
  close_positions_at_session_end: true
  lockout_outside_session: true
  respect_holidays: true
```

#### Configurable Timer Lockout Rules

```yaml
trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3
    per_hour: 10
    per_session: 50
  cooldown_on_breach:
    enabled: true
    per_minute_breach: 60
    per_hour_breach: 1800
    per_session_breach: 3600
```

---

## Startup Sequence

1. **Windows Service starts** (`windows_service.py`)
2. **Daemon initializes** (`daemon.py`)
   - Load config files (`config/loader.py`)
   - Initialize SQLite database (`state/persistence.py`)
   - Authenticate with TopstepX API (`api/auth.py`)
   - Connect to SignalR WebSocket (`api/signalr_listener.py`)
3. **Risk Engine loads rules** (`core/rule_loader.py`)
   - Read `risk_config.yaml`
   - Instantiate enabled rules
4. **Event loop starts** (`core/daemon.py`)
   - Listen for SignalR events
   - Check timers/lockouts every second
   - Process events through rules

---

## Summary

### Architecture Maturity

**v1 → v2 Evolution:** From initial planning to production-ready design

**Key Improvements:**
1. Four reusable modules (MOD-001 to MOD-004)
2. Clear separation of concerns
3. Event-driven architecture
4. Crash recovery through SQLite
5. 200-line file limit enforced

### Production Readiness

**v2 Architecture is:**
- Modular (easy to extend)
- Testable (mock modules, not API)
- Beginner-friendly (small files, clear purpose)
- Professional-grade (Windows Service, admin protection)
- Crash-resilient (SQLite persistence)

### Implementation Path

**Phase 1:** Build solid base + 3 rules
- MaxContracts (RULE-001)
- MaxContractsPerInstrument (RULE-002)
- SessionBlockOutside (RULE-009)

**Phase 2+:** Add remaining 9 rules incrementally
- Each rule = new file in `rules/`
- No refactoring needed (architecture complete)

### Critical Context for AI Agents

**IMPORTANT:** Specs written BEFORE Project-X SDK existed

**When implementing:**
1. Use Project-X-Py SDK (don't reinvent WebSocket handling)
2. SDK handles: auth, events, positions, orders
3. Risk Manager adds: rule logic, enforcement, lockout
4. See `docs/current/SDK_INTEGRATION_GUIDE.md` for mapping

---

**Document Complete - Ready for Coordinator Review**
