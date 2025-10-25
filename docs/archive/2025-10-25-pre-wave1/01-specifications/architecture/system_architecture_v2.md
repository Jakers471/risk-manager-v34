---
doc_id: ARCH-V2
version: 2.0
last_updated: 2025-01-17
dependencies: [ARCH-V1, MOD-001, MOD-002, MOD-003, MOD-004]
---

# Risk Manager - System Architecture (v2)

**Status:** Current system architecture - see CURRENT_VERSION.md for version info.

---

## 📁 Complete Directory Structure

```
risk-manager/
├── src/
│   ├── core/                              # Core daemon logic
│   │   ├── __init__.py
│   │   ├── daemon.py                      # Main service entry (~100 lines)
│   │   ├── risk_engine.py                 # Rule orchestrator (~150 lines)
│   │   ├── rule_loader.py                 # Loads rules from config (~80 lines)
│   │   └── event_router.py                # Routes events to rules (~100 lines)
│   │
│   ├── api/                               # TopstepX API integration
│   │   ├── __init__.py
│   │   ├── auth.py                        # JWT authentication (~80 lines)
│   │   ├── rest_client.py                 # REST API wrapper (~120 lines)
│   │   ├── signalr_listener.py            # WebSocket event listener (~150 lines)
│   │   └── connection_manager.py          # Connection health, reconnect (~100 lines)
│   │
│   ├── enforcement/                       # 🔧 Enforcement module (MOD-001)
│   │   ├── __init__.py
│   │   ├── actions.py                     # Close, cancel, reduce actions (~120 lines)
│   │   └── enforcement_engine.py          # Orchestrates enforcement (~80 lines)
│   │
│   ├── rules/                             # Risk rules (each rule = 1 file)
│   │   ├── __init__.py
│   │   ├── base_rule.py                   # Base class for all rules (~80 lines)
│   │   │
│   │   ├── max_contracts.py               # RULE-001 (~90 lines)
│   │   ├── max_contracts_per_instrument.py# RULE-002 (~100 lines)
│   │   ├── daily_realized_loss.py         # RULE-003 (~120 lines)
│   │   ├── daily_unrealized_loss.py       # RULE-004 (~130 lines)
│   │   ├── max_unrealized_profit.py       # RULE-005 (~120 lines)
│   │   ├── trade_frequency_limit.py       # RULE-006 (~150 lines)
│   │   ├── cooldown_after_loss.py         # RULE-007 (~130 lines)
│   │   ├── no_stop_loss_grace.py          # RULE-008 (~110 lines)
│   │   ├── session_block_outside.py       # RULE-009 (~140 lines)
│   │   ├── auth_loss_guard.py             # RULE-010 (~80 lines)
│   │   ├── symbol_blocks.py               # RULE-011 (~90 lines)
│   │   └── trade_management.py            # RULE-012 (~150 lines)
│   │
│   ├── state/                             # State management & persistence
│   │   ├── __init__.py
│   │   ├── state_manager.py               # In-memory state tracking (~150 lines)
│   │   ├── persistence.py                 # SQLite save/load (~120 lines)
│   │   ├── lockout_manager.py             # 🔧 MOD-002 - Lockout logic (~150 lines)
│   │   ├── timer_manager.py               # 🔧 MOD-003 - Timer logic (~120 lines)
│   │   ├── reset_scheduler.py             # 🔧 MOD-004 - Daily reset (~100 lines)
│   │   └── pnl_tracker.py                 # P&L calculations (~130 lines)
│   │
│   ├── cli/                               # Command-line interfaces
│   │   ├── __init__.py
│   │   ├── main.py                        # CLI entry point & routing (~80 lines)
│   │   │
│   │   ├── admin/                         # Admin CLI (password-protected)
│   │   │   ├── __init__.py
│   │   │   ├── admin_main.py              # Admin menu (~100 lines)
│   │   │   ├── auth.py                    # Password verification (~60 lines)
│   │   │   ├── configure_rules.py         # Rule configuration wizard (~150 lines)
│   │   │   ├── manage_accounts.py         # Account/API key setup (~120 lines)
│   │   │   └── service_control.py         # Start/stop daemon (~80 lines)
│   │   │
│   │   └── trader/                        # Trader CLI (view-only)
│   │       ├── __init__.py
│   │       ├── trader_main.py             # Trader menu (~80 lines)
│   │       ├── status_screen.py           # Main status display (~120 lines)
│   │       ├── lockout_display.py         # Lockout timer UI (~100 lines)
│   │       ├── logs_viewer.py             # Enforcement log viewer (~100 lines)
│   │       ├── clock_tracker.py           # Clock in/out tracking (~70 lines)
│   │       └── formatting.py              # Colors, tables, UI helpers (~80 lines)
│   │
│   ├── config/                            # Configuration management
│   │   ├── __init__.py
│   │   ├── loader.py                      # Load/validate YAML (~100 lines)
│   │   ├── validator.py                   # Config validation (~90 lines)
│   │   └── defaults.py                    # Default config templates (~60 lines)
│   │
│   ├── utils/                             # Shared utilities
│   │   ├── __init__.py
│   │   ├── logging.py                     # Logging setup (~80 lines)
│   │   ├── datetime_helpers.py            # Time/date utils (~70 lines)
│   │   ├── holidays.py                    # Holiday calendar (~60 lines)
│   │   └── validation.py                  # Input validation (~50 lines)
│   │
│   └── service/                           # Windows Service wrapper
│       ├── __init__.py
│       ├── windows_service.py             # Windows Service integration (~120 lines)
│       ├── installer.py                   # Service install/uninstall (~100 lines)
│       └── watchdog.py                    # Auto-restart on crash (~80 lines)
│
├── config/                                # Configuration files
│   ├── accounts.yaml                      # TopstepX auth & monitored account
│   ├── risk_config.yaml                   # Risk rule settings
│   ├── holidays.yaml                      # Trading holidays calendar
│   ├── admin_password.hash                # Hashed admin password
│   └── config.example.yaml                # Example config (for docs)
│
├── data/                                  # Runtime data (gitignored)
│   ├── state.db                           # SQLite database (state persistence)
│   └── backups/                           # State backups (auto-rotation)
│
├── logs/                                  # Log files (gitignored)
│   ├── daemon.log                         # Main daemon log
│   ├── enforcement.log                    # Rule enforcement actions
│   ├── api.log                            # TopstepX API interactions
│   └── error.log                          # Errors only
│
├── tests/                                 # Tests (pytest)
│   ├── __init__.py
│   ├── conftest.py                        # Pytest fixtures
│   │
│   ├── unit/                              # Unit tests
│   │   ├── test_rules/                    # Test each rule independently
│   │   │   ├── test_max_contracts.py
│   │   │   ├── test_daily_realized_loss.py
│   │   │   └── (one test file per rule)
│   │   ├── test_enforcement_actions.py
│   │   ├── test_lockout_manager.py
│   │   ├── test_timer_manager.py
│   │   ├── test_state_manager.py
│   │   └── test_pnl_tracker.py
│   │
│   └── integration/                       # Integration tests
│       ├── test_full_workflow.py          # End-to-end scenarios
│       ├── test_api_integration.py        # TopstepX API mocking
│       └── test_persistence.py            # State save/load
│
├── docs/                                  # Documentation (YOU ARE HERE)
│   ├── ARCHITECTURE_INDEX.md              # Master doc index
│   ├── architecture/                      # Architecture docs
│   ├── rules/                             # Rule specifications
│   ├── modules/                           # Module specifications
│   └── summary/                           # Overview docs
│
├── scripts/                               # Utility scripts
│   ├── install_service.py                 # Install Windows Service
│   ├── uninstall_service.py               # Remove service
│   └── dev_run.py                         # Run daemon in dev mode (no service)
│
├── .gitignore                             # Git ignore (config, data, logs)
├── .env.example                           # Environment variables example
├── pyproject.toml                         # Python dependencies & config
├── pytest.ini                             # Pytest configuration
├── README.md                              # Project overview
└── requirements.txt                       # Python dependencies (pip)
```

---

## 🏗️ Architecture Layers

### **Layer 1: Windows Service (Entry Point)**
```
src/service/windows_service.py
    ↓
src/core/daemon.py (main event loop)
    ↓
src/core/risk_engine.py (orchestrator)
```

### **Layer 2: API Integration**
```
src/api/signalr_listener.py
    ↓ (receives events)
src/core/event_router.py
    ↓ (routes to rules)
src/rules/*.py (each rule processes)
```

### **Layer 3: Enforcement & State**
```
src/rules/*.py (detects breach)
    ↓
src/enforcement/actions.py (executes)
    ↓
src/state/lockout_manager.py (manages lockouts)
    ↓
src/state/persistence.py (saves to SQLite)
```

### **Layer 4: CLI Interfaces**
```
src/cli/admin/admin_main.py (admin interface)
src/cli/trader/trader_main.py (trader interface)
    ↓ (both read from)
src/state/state_manager.py (current state)
```

---

## 🔧 Reusable Modules (Core Innovation)

### **MOD-001: Enforcement Actions** (`src/enforcement/actions.py`)
**Purpose:** Centralized enforcement logic - all rules call this.

**Key Functions:**
```python
def close_all_positions(account_id: int) -> bool:
    """Close all open positions via REST API."""
    # POST /api/Position/searchOpen -> get all positions
    # For each position: POST /api/Position/closeContract

def close_position(account_id: int, contract_id: str) -> bool:
    """Close specific position."""
    # POST /api/Position/closeContract

def reduce_position_to_limit(account_id: int, contract_id: str, target_size: int) -> bool:
    """Partially close position to reach target size."""
    # POST /api/Position/partialCloseContract

def cancel_all_orders(account_id: int) -> bool:
    """Cancel all pending orders."""
    # POST /api/Order/searchOpen -> get all orders
    # For each order: POST /api/Order/cancel
```

**Used By:** ALL 12 rules

---

### **MOD-002: Lockout Manager** (`src/state/lockout_manager.py`)
**Purpose:** Manages all lockout states, timers, and expiry.

**Key Functions:**
```python
def set_lockout(account_id: int, reason: str, until: datetime) -> None:
    """Set hard lockout until specific time."""
    # Used by: DailyLoss, SessionBlock, SymbolBlocks

def set_cooldown(account_id: int, reason: str, duration_seconds: int) -> None:
    """Set lockout for specific duration."""
    # Used by: TradeFrequencyLimit, CooldownAfterLoss

def is_locked_out(account_id: int) -> bool:
    """Check if account is currently locked."""
    # Called by: event_router.py before processing events

def get_lockout_info(account_id: int) -> dict:
    """Get lockout reason and expiry time."""
    # Used by: Trader CLI to display timers

def clear_lockout(account_id: int) -> None:
    """Remove lockout (manual or auto-expiry)."""

def check_expired_lockouts() -> None:
    """Background task: auto-clear expired lockouts."""
    # Runs every second in daemon loop
```

**Used By:** RULE-003, 004, 005, 006, 007, 009, 010, 011

---

### **MOD-003: Timer Manager** (`src/state/timer_manager.py`)
**Purpose:** Countdown timers for cooldowns and resets.

**Key Functions:**
```python
def start_timer(name: str, duration: int, callback: callable) -> None:
    """Start countdown timer with callback."""
    # Used by: TradeFrequencyLimit cooldowns

def get_remaining_time(name: str) -> int:
    """Get seconds remaining on timer."""
    # Used by: Trader CLI for countdown display

def cancel_timer(name: str) -> None:
    """Stop timer before it expires."""

def check_timers() -> None:
    """Background task: check timers and fire callbacks."""
    # Runs every second in daemon loop
```

**Used By:** RULE-006, 007, 009, MOD-002

---

### **MOD-004: Reset Scheduler** (`src/state/reset_scheduler.py`)
**Purpose:** Daily reset logic for P&L and counters.

**Key Functions:**
```python
def schedule_daily_reset(reset_time: str = "17:00", timezone: str = "America/New_York") -> None:
    """Schedule daily reset at specific time."""
    # Used by: DailyLoss, DailyUnrealizedLoss, MaxUnrealizedProfit

def reset_daily_counters(account_id: int) -> None:
    """Reset all daily counters (P&L, trade counts)."""
    # Called at reset_time

def is_holiday(date: datetime) -> bool:
    """Check if date is a trading holiday."""
    # Used by: SessionBlockOutside
```

**Used By:** RULE-003, 004, 005

---

## 📊 Data Flow: Real-Time Event Processing

### **Event Flow Diagram:**
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

## 🔐 Configuration Management

### **accounts.yaml** (TopstepX Auth)
```yaml
topstepx:
  username: "your_username"
  api_key: "your_api_key_here"

monitored_account:
  account_id: 123
  account_name: "Main Trading Account"
```

### **risk_config.yaml** (Rule Settings)
```yaml
# Trade-by-Trade Rules (No Lockout)
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

# Hard Lockout Rules
daily_realized_loss:
  enabled: true
  limit: -500
  reset_time: "17:00"
  timezone: "America/New_York"
  enforcement: "close_all_and_lockout"

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

# Configurable Timer Lockout Rules
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

## 🚀 Startup Sequence

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

## 🎯 Key Architectural Decisions

1. **Modular Enforcement:** All rules call MOD-001 (no duplication)
2. **Centralized Lockout:** MOD-002 manages all lockout states
3. **Event-Driven:** SignalR events trigger rule checks (no polling)
4. **State Persistence:** SQLite ensures crash recovery
5. **File Size Limit:** No file over 200 lines (enforced via code reviews)
6. **One Rule = One File:** Easy to add/remove rules
7. **No Blocking:** Can't intercept orders, but close within milliseconds

---

## 📌 Next Steps for Implementation

1. Read **ARCH-PIPE-001** for integration pipeline details
2. Read **MOD-001, MOD-002, MOD-003, MOD-004** for module specs
3. Read individual rule files (RULE-001 to RULE-012) for implementations
4. Start Phase 1 with 3 rules: MaxContracts, MaxContractsPerInstrument, SessionBlockOutside

---

**This architecture is production-ready, beginner-friendly, and designed to grow.**
