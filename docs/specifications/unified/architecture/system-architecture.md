# System Architecture - Unified Specification

**Document ID:** ARCH-UNIFIED-001
**Version:** 2.0 (Authoritative)
**Created:** 2025-10-25
**Based On:** system_architecture_v2.md (2025-01-17)
**Status:** Production Specification

---

## Executive Summary

Risk Manager V34 is a **professional-grade risk management daemon** that protects trading accounts by enforcing configurable risk rules. The system uses a **daemon-based architecture** running as a Windows Service, with SDK-first integration to Project-X-Py for trading operations.

### Key Characteristics
- **Daemon Architecture:** Runs continuously as background service
- **SDK-First:** Uses Project-X-Py SDK (v3.5.9) for all trading operations
- **Event-Driven:** Real-time event processing (no polling)
- **State Persistence:** SQLite database for crash recovery
- **Dual CLI:** Admin (full control) and Trader (view-only)
- **UAC Protected:** Trader cannot stop daemon without admin password

---

## Architecture Evolution

### Version 1 (Historical Reference)
**Date:** 2025-01-17 (initial planning)
**Context:** Designed before Project-X-Py SDK existed

**Approach:**
- Direct TopstepX Gateway API integration
- Manual SignalR WebSocket handling via `signalrcore` library
- Custom position/order management
- Manual state tracking

**Status:** Archived for historical context

### Version 2 (Current - AUTHORITATIVE)
**Date:** 2025-01-17 (refined architecture)
**Context:** Uses Project-X-Py SDK as foundation

**Approach:**
- **SDK Handles:** WebSocket, auth, events, orders, positions, reconnection
- **Risk Manager Adds:** Risk rules, enforcement, lockouts, state management, CLIs
- **Result:** Cleaner, more maintainable, production-ready

**Key Improvements from v1:**
1. Introduced 4 reusable modules (MOD-001 to MOD-004)
2. SDK-first approach (don't reinvent wheel)
3. Dedicated event router (clean event flow)
4. Lockout manager module (centralized lockout state)
5. Clearer separation of concerns
6. Better testability (mock modules, not API)

---

## System Overview

### What It Does
1. **Monitors** trading account via Project-X SDK real-time events
2. **Evaluates** each event against configured risk rules
3. **Enforces** violations (close positions, cancel orders, lock out trader)
4. **Persists** state to SQLite (P&L, lockouts, timers)
5. **Displays** status to trader via view-only CLI

### What It Prevents
- Account rule violations (e.g., max daily loss)
- Excessive position sizes
- Trading outside allowed sessions
- Over-trading (frequency limits)
- Unauthorized symbol trading
- Profit/loss limit breaches

---

## Daemon Architecture

### Deployment Model

```
┌─────────────────────────────────────────────────────────────┐
│ Windows Service (Auto-starts on boot)                       │
│   └─ Risk Manager Daemon                                    │
│       ├─ Project-X SDK Connection                           │
│       ├─ Event Processing Loop                              │
│       ├─ Rule Evaluation                                    │
│       ├─ Lockout Management                                 │
│       └─ State Persistence (SQLite)                         │
└─────────────────────────────────────────────────────────────┘
```

### Lifecycle Stages

#### 1. Initial Setup (Admin)
```
Admin → Install Service → Configure Rules → Configure API → Start Daemon
```

**Actions:**
- Install Windows Service (one-time)
- Configure API credentials (`config/accounts.yaml`)
- Configure risk rules (`config/risk_config.yaml`)
- Set reset timers, session windows, limits
- Start daemon

**Result:** Daemon running, ready to protect account

#### 2. Daily Operation (Trader)
```
Computer Boots → Service Auto-Starts → Trader Logs In → Opens Trader CLI
```

**Actions:**
- Computer starts up
- Windows Service auto-starts daemon
- Daemon connects to Project-X SDK
- Trader logs in (daemon already running)
- Trader opens Trader CLI (view-only)
- Trades normally throughout day

**Result:** Continuous protection without trader intervention

#### 3. Reconfiguration (Admin)
```
Admin → Stop Daemon → Edit Configs → Restart Daemon
```

**Actions:**
- Admin elevates with UAC
- Stops daemon via Admin CLI
- Modifies configurations
- Restarts daemon
- New settings take effect

**Result:** Configurations updated without reinstalling

#### 4. State Recovery (After Crash)
```
Daemon Crashes → Windows Restarts Service → Load State from SQLite → Resume
```

**Actions:**
- Windows Service recovery policy triggers (1 minute delay)
- Daemon restarts automatically
- Loads state from SQLite (lockouts, P&L, timers)
- Reconnects to Project-X SDK
- Resumes monitoring

**Result:** Seamless recovery without losing protection

---

## Technology Stack

### Core Platform
- **Language:** Python 3.12+ (async/await throughout)
- **Runtime:** Windows Service (LocalSystem account)
- **Database:** SQLite (state persistence)
- **SDK:** Project-X-Py v3.5.9 (trading operations)

### Key Libraries
- **pywin32:** Windows Service integration
- **signalrcore:** (Handled by SDK - not used directly)
- **Pydantic:** Configuration validation
- **loguru:** Logging
- **pytest:** Testing
- **APScheduler:** Scheduled tasks (daily reset)

### API Integration
- **Project-X SDK:** All trading operations
- **TopstepX Gateway API:** (Accessed via SDK)
- **WebSocket:** Real-time events (managed by SDK)
- **REST:** Position/order management (via SDK)

---

## Component Architecture

### Layer 1: Windows Service (Entry Point)

```python
# src/service/windows_service.py (~120 lines)

class RiskManagerService(win32serviceutil.ServiceFramework):
    """
    Windows Service wrapper for Risk Manager.
    Handles service lifecycle and async/sync bridge.
    """

    def SvcDoRun(self):
        """Service main entry (called by Windows)"""
        asyncio.run(self.async_main())

    async def async_main(self):
        """Async main loop"""
        # Load configuration
        config = RiskConfig.from_file("C:/ProgramData/RiskManager/config/risk_config.yaml")

        # Create Risk Manager
        manager = await RiskManager.create(config)

        # Start Risk Manager (non-blocking)
        await manager.start()

        # Wait for stop signal
        await self.wait_for_stop_signal()

        # Graceful shutdown
        await manager.stop()
```

**Responsibilities:**
- Windows Service integration
- Async/sync bridge (Windows API is synchronous, Risk Manager is async)
- Graceful shutdown handling
- Error reporting to Windows Event Log
- Service status reporting

**Status:** NOT IMPLEMENTED (0% - critical blocker)

**See:** `/docs/analysis/wave2-gap-analysis/05-DEPLOYMENT-GAPS.md`

---

### Layer 2: Core Daemon Logic

```python
# src/core/daemon.py (~100 lines)

class RiskManager:
    """
    Main Risk Manager daemon.
    Orchestrates all components.
    """

    async def start(self):
        """Start daemon"""
        # 1. Initialize database
        self.db = Database("C:/ProgramData/RiskManager/data/risk_state.db")

        # 2. Load state from database
        await self.load_state()

        # 3. Connect to Project-X SDK via TradingIntegration
        await self.trading_integration.connect()

        # 4. Load risk rules
        self.rules = self.load_rules()

        # 5. Start event loop
        await self.event_loop()
```

**Responsibilities:**
- Component initialization
- State loading/restoration
- SDK connection management (via TradingIntegration)
- Rule orchestration
- Event loop coordination
- Background tasks (lockout expiry, daily reset)

**Status:** PARTIALLY IMPLEMENTED (core structure exists, needs Windows Service integration)

---

### Layer 3: TradingIntegration (SDK Wrapper)

```python
# src/risk_manager/integrations/trading.py (~421 lines)

class TradingIntegration:
    """
    Integration with Project-X-Py trading SDK.

    Bridges between the trading platform and risk management system.

    Uses two-step connection:
    1. HTTP API authentication (get JWT token)
    2. SignalR WebSocket connection (real-time events)
    """

    async def connect(self):
        """Connect to trading platform using two-step process."""
        # STEP 1: HTTP API Authentication
        self.client = await ProjectX.from_env().__aenter__()
        await self.client.authenticate()

        # STEP 2: SignalR WebSocket Connection
        self.realtime = ProjectXRealtimeClient(
            jwt_token=self.client.session_token,
            account_id=str(self.client.account_info.id),
            config=self.client.config
        )
        await self.realtime.connect()

        # STEP 3: Create TradingSuite
        self.suite = await TradingSuite.create(
            instruments=self.instruments,
            timeframes=["1min", "5min"],
            features=["orderbook", "statistics"]
        )

    async def start(self):
        """Start monitoring trading events via realtime callbacks."""
        # Subscribe to realtime callbacks (NOT suite.on)
        await self.realtime.add_callback("position_update", self._on_position_update)
        await self.realtime.add_callback("order_update", self._on_order_update)
        await self.realtime.add_callback("trade_update", self._on_trade_update)
        await self.realtime.add_callback("account_update", self._on_account_update)

    async def flatten_all(self):
        """Flatten all positions across all instruments."""
        for symbol in self.instruments:
            await self.flatten_position(symbol)

    async def flatten_position(self, symbol: str):
        """Flatten a specific position."""
        context = self.suite[symbol]
        await context.positions.close_all_positions()
```

**Responsibilities:**
- SDK connection lifecycle (HTTP + WebSocket + TradingSuite)
- Subscribe to SignalR real-time events via direct callbacks
- Convert SignalR data to RiskEvents
- Publish events to Risk EventBus
- Execute enforcement actions via SDK (flatten, cancel orders)

**Key Implementation Detail:**
- Uses `realtime.add_callback()` NOT `suite.on()`
- SDK EventBus doesn't emit position/order/trade events from SignalR
- Must subscribe directly to realtime client callbacks

**Status:** ✅ IMPLEMENTED (working connection + event bridging)

**File:** `src/risk_manager/integrations/trading.py`

---

### Layer 4: Event Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ TopstepX Platform (SignalR WebSocket)                      │
│   ├─ position_update events                                │
│   ├─ order_update events                                   │
│   ├─ trade_update events                                   │
│   └─ account_update events                                 │
└──────────────────┬──────────────────────────────────────────┘
                   │ SignalR messages
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ TradingIntegration (src/integrations/trading.py)           │
│   ├─ Realtime callbacks parse SignalR data                 │
│   ├─ Convert to RiskEvent objects                          │
│   └─ Publish to Risk EventBus                              │
└──────────────────┬──────────────────────────────────────────┘
                   │ RiskEvent published
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Risk EventBus (src/core/events.py)                         │
│   └─ Pub/sub system for risk events                        │
└──────────────────┬──────────────────────────────────────────┘
                   │ Event distributed
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ RiskEngine (src/core/engine.py)                            │
│   ├─ Checkpoint 6: "📨 Event received"                     │
│   ├─ Route to all registered rules                         │
│   └─ For each rule: rule.evaluate(event, engine)           │
└──────────────────┬──────────────────────────────────────────┘
                   │ For each rule
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Risk Rules (src/rules/*.py)                                │
│   ├─ MaxContracts (RULE-001)                               │
│   ├─ DailyRealizedLoss (RULE-003)                          │
│   ├─ TradeFrequencyLimit (RULE-006)                        │
│   └─ ... (12 rules total)                                  │
│                                                              │
│ Each rule:                                                  │
│   ├─ Checkpoint 7: "🔍 Rule evaluated"                     │
│   ├─ Checks breach condition                               │
│   └─ If breach → returns violation dict                    │
└──────────────────┬──────────────────────────────────────────┘
                   │ Violation detected
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ RiskEngine._handle_violation()                             │
│   ├─ Checkpoint 8: "⚠️ Enforcement triggered"              │
│   ├─ Publish ENFORCEMENT_ACTION event                      │
│   └─ Execute action (flatten/pause/alert)                  │
└──────────────────┬──────────────────────────────────────────┘
                   │ Execute enforcement
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ TradingIntegration.flatten_all()                           │
│   ├─ For each instrument: flatten_position(symbol)         │
│   └─ Call SDK: suite[symbol].positions.close_all_positions()│
└──────────────────┬──────────────────────────────────────────┘
                   │ SDK API call
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ TopstepX Platform REST API                                 │
│   └─ POST /api/Position/closeAllPositions                  │
│   └─ ✅ Positions actually closed!                         │
└─────────────────────────────────────────────────────────────┘
```

**Component Interaction Table:**

| Component | Responsibilities | Dependencies | Status |
|-----------|-----------------|--------------|---------|
| **TradingIntegration** | SDK connection, SignalR events, enforcement execution | ProjectX SDK, EventBus | ✅ Implemented |
| **EventBus** | Pub/sub event distribution | None | ✅ Implemented |
| **RiskEngine** | Event routing, rule coordination, violation handling | EventBus, TradingIntegration | ✅ Implemented |
| **Risk Rules** | Rule logic, violation detection | RiskEngine state | ✅ Partially (2/12 rules) |
| **Lockout Manager** | Lockout state, cooldowns, auto-expiry | Database | ❌ Not implemented |
| **Event Router** | Lockout check, event filtering | Lockout Manager | ❌ Not implemented |

**See:** `docs/specifications/unified/architecture/event-flow.md` for detailed event flow diagrams

---

## Reusable Modules (Core Innovation)

### MOD-001: Enforcement Actions
**File:** `src/enforcement/actions.py`
**Purpose:** Centralized enforcement logic - all rules call these functions

**Why Centralized:**
- No code duplication (12 rules share same enforcement logic)
- Consistency (all rules enforce the same way)
- Testability (mock MOD-001 to test rules)
- Logging (all enforcement logged in one place)

**Public API:**
```python
def close_all_positions(account_id: int) -> bool
def close_position(account_id: int, contract_id: str) -> bool
def reduce_position_to_limit(account_id: int, contract_id: str, target_size: int) -> bool
def cancel_all_orders(account_id: int) -> bool
def cancel_order(account_id: int, order_id: int) -> bool
```

**Used By:** All 12 risk rules

**Status:** NOT IMPLEMENTED (framework exists, needs SDK integration)

**See:** `MOD-001-database-manager.md` (will be `MOD-001-enforcement-actions.md`)

---

### MOD-002: Lockout Manager
**File:** `src/state/lockout_manager.py`
**Purpose:** Manages all lockout states (hard lockouts, cooldowns, auto-expiry)

**Handles:**
- **Hard Lockouts:** Until specific time (e.g., daily reset at 5 PM)
- **Cooldown Timers:** Duration-based (e.g., 30-minute trade frequency cooldown)
- **Auto-Expiry:** Background task clears expired lockouts
- **Persistence:** Saves to SQLite for crash recovery

**Public API:**
```python
def set_lockout(account_id: int, reason: str, until: datetime) -> None
def set_cooldown(account_id: int, reason: str, duration_seconds: int) -> None
def is_locked_out(account_id: int) -> bool
def get_lockout_info(account_id: int) -> dict | None
def clear_lockout(account_id: int) -> None
def check_expired_lockouts() -> None  # Background task
```

**Used By:** 7 rules (RULE-003, 006, 007, 009, 010, 011, 013)

**Status:** NOT IMPLEMENTED (critical blocker - blocks 54% of rules)

**See:** `MOD-002-lockout-manager.md`

---

### MOD-003: Timer Manager
**File:** `src/state/timer_manager.py`
**Purpose:** Countdown timers for cooldowns and scheduled checks

**Handles:**
- Countdown timers with callbacks
- Background task checks timers every second
- Callback execution when timers expire
- Trader CLI countdown display

**Public API:**
```python
def start_timer(name: str, duration: int, callback: callable) -> None
def get_remaining_time(name: str) -> int
def cancel_timer(name: str) -> None
def check_timers() -> None  # Background task
```

**Used By:** MOD-002 (cooldowns), RULE-008, RULE-009

**Status:** NOT IMPLEMENTED (needed by MOD-002)

**See:** `MOD-003-timer-manager.md`

---

### MOD-004: Reset Scheduler
**File:** `src/state/reset_scheduler.py`
**Purpose:** Daily reset at midnight ET, holiday calendar integration

**Handles:**
- Daily reset at configured time (e.g., midnight ET)
- Timezone-aware (DST handling)
- Holiday calendar integration
- P&L counter resets
- Lockout clearing

**Public API:**
```python
def schedule_daily_reset(reset_time: str = "17:00", timezone: str = "America/New_York") -> None
def reset_daily_counters(account_id: int) -> None
def check_reset_time() -> None  # Background task
def is_holiday(date: datetime) -> bool
```

**Used By:** RULE-003, 004, 005 (daily P&L rules), RULE-009 (session rules)

**Status:** NOT IMPLEMENTED (needed for daily P&L rules)

**See:** `MOD-004-reset-scheduler.md`

---

## Directory Structure

```
risk-manager/
├── src/
│   ├── core/                           # Core daemon logic
│   │   ├── daemon.py                   # Main service entry (~100 lines)
│   │   ├── risk_engine.py              # Rule orchestrator (~150 lines)
│   │   ├── rule_loader.py              # Loads rules from config (~80 lines)
│   │   └── event_router.py             # Routes events to rules (~100 lines) [NEW in v2]
│   │
│   ├── api/                            # TopstepX API integration (via SDK)
│   │   ├── auth.py                     # JWT authentication (~80 lines)
│   │   ├── rest_client.py              # REST API wrapper (~120 lines)
│   │   ├── signalr_listener.py         # WebSocket event listener (~150 lines)
│   │   └── connection_manager.py       # Connection health, reconnect (~100 lines) [NEW in v2]
│   │
│   ├── enforcement/                    # MOD-001 - Enforcement module [NEW in v2]
│   │   ├── actions.py                  # Close, cancel, reduce actions (~120 lines)
│   │   └── enforcement_engine.py       # Orchestrates enforcement (~80 lines)
│   │
│   ├── rules/                          # Risk rules (12 rules, each = 1 file)
│   │   ├── base_rule.py                # Base class for all rules (~80 lines)
│   │   ├── max_contracts.py            # RULE-001 (~90 lines)
│   │   ├── max_contracts_per_instrument.py # RULE-002 (~100 lines)
│   │   ├── daily_realized_loss.py      # RULE-003 (~120 lines)
│   │   └── ... (12 rules total)
│   │
│   ├── state/                          # State management & persistence
│   │   ├── state_manager.py            # In-memory state tracking (~150 lines)
│   │   ├── persistence.py              # SQLite save/load (~120 lines)
│   │   ├── lockout_manager.py          # MOD-002 - Lockout logic (~150 lines)
│   │   ├── timer_manager.py            # MOD-003 - Timer logic (~120 lines)
│   │   ├── reset_scheduler.py          # MOD-004 - Daily reset (~100 lines)
│   │   └── pnl_tracker.py              # P&L calculations (~130 lines)
│   │
│   ├── cli/                            # Command-line interfaces
│   │   ├── admin/                      # Admin CLI (password-protected)
│   │   │   ├── admin_main.py           # Admin menu (~100 lines)
│   │   │   ├── auth.py                 # Password/UAC verification (~60 lines)
│   │   │   ├── configure_rules.py      # Rule configuration wizard (~150 lines)
│   │   │   ├── manage_accounts.py      # Account/API key setup (~120 lines)
│   │   │   └── service_control.py      # Start/stop daemon (~80 lines)
│   │   │
│   │   └── trader/                     # Trader CLI (view-only)
│   │       ├── trader_main.py          # Trader menu (~80 lines)
│   │       ├── status_screen.py        # Main status display (~120 lines)
│   │       ├── lockout_display.py      # Lockout timer UI (~100 lines) [NEW in v2]
│   │       ├── logs_viewer.py          # Enforcement log viewer (~100 lines)
│   │       ├── clock_tracker.py        # Clock in/out tracking (~70 lines)
│   │       └── formatting.py           # Colors, tables, UI helpers (~80 lines)
│   │
│   ├── config/                         # Configuration management
│   │   ├── loader.py                   # Load/validate YAML (~100 lines)
│   │   ├── validator.py                # Config validation (~90 lines)
│   │   └── defaults.py                 # Default config templates (~60 lines)
│   │
│   ├── utils/                          # Shared utilities
│   │   ├── logging.py                  # Logging setup (~80 lines)
│   │   ├── datetime_helpers.py         # Time/date utils (~70 lines)
│   │   ├── holidays.py                 # Holiday calendar (~60 lines)
│   │   └── validation.py               # Input validation (~50 lines)
│   │
│   └── service/                        # Windows Service wrapper
│       ├── windows_service.py          # Windows Service integration (~120 lines)
│       ├── installer.py                # Service install/uninstall (~100 lines)
│       └── watchdog.py                 # Auto-restart on crash (~80 lines)
│
├── config/                             # Configuration files
│   ├── accounts.yaml                   # TopstepX auth & monitored account
│   ├── risk_config.yaml                # Risk rule settings
│   ├── holidays.yaml                   # Trading holidays calendar
│   └── admin_password.hash             # Hashed admin password
│
├── data/                               # Runtime data (gitignored)
│   ├── state.db                        # SQLite database (state persistence)
│   └── backups/                        # State backups (auto-rotation)
│
└── logs/                               # Log files (gitignored)
    ├── daemon.log                      # Main daemon log
    ├── enforcement.log                 # Rule enforcement actions
    ├── api.log                         # TopstepX API interactions
    └── error.log                       # Errors only
```

---

## Key Design Decisions

### 1. SDK-First Approach (v2 vs v1)
**Decision:** Use Project-X-Py SDK for all trading operations

**v1 Approach (Rejected):**
- Manual SignalR WebSocket handling
- Direct TopstepX Gateway API calls
- Custom position/order management

**v2 Approach (Adopted):**
- SDK handles WebSocket, auth, events, orders, positions
- Risk Manager adds risk logic on top
- Cleaner, more maintainable code

**Rationale:**
- Don't reinvent wheel (SDK already exists)
- Reduced complexity (no manual WebSocket handling)
- Better reliability (SDK handles reconnection)
- Easier testing (mock SDK interfaces)

---

### 2. Modular Enforcement (MOD-001)
**Decision:** All rules call centralized enforcement module

**Rationale:**
- Eliminate code duplication (12 rules share logic)
- Ensure consistency (all rules enforce the same way)
- Centralized logging (all enforcement logged in one place)
- Easy to mock for testing

**Impact:**
- Rules are < 100 lines (focus on logic, not API calls)
- Enforcement behavior is consistent
- Changes to API only need updates in one place

---

### 3. Centralized Lockout (MOD-002)
**Decision:** Single module manages all lockout states

**Rationale:**
- Multiple rules need lockout capability (7 rules)
- Lockout state is complex (hard lockout vs cooldown, persistence, auto-expiry)
- Event router needs to check lockout before processing events

**Impact:**
- Rules just call `set_lockout()` or `set_cooldown()`
- Event router has single point to check: `is_locked_out()`
- Crash recovery through SQLite persistence
- Trader CLI gets consistent lockout display

---

### 4. Event-Driven Architecture
**Decision:** SDK events trigger rule checks (no polling)

**Rationale:**
- TopstepX provides real-time events via SDK
- Instant notification when trader's order fills
- No need to poll for position/order changes
- Efficient and low-latency

**Impact:**
- Rules react within milliseconds of events
- No API rate limit issues from polling
- Clean event → rule → enforcement flow

---

### 5. State Persistence (SQLite)
**Decision:** All critical state saved to SQLite database

**Rationale:**
- Computer can crash or restart anytime
- P&L, lockouts, timers must survive restarts
- Need historical data for debugging

**Impact:**
- Daemon can crash and resume exactly where it left off
- Daily lockouts persist across restarts
- Cooldown timers restored on startup

---

### 6. File Size Limit (200 lines)
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

---

### 7. One Rule = One File
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

---

### 8. Daemon-Based Deployment
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

---

## Startup Sequence

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Windows Service Starts (windows_service.py)             │
│    └─ Service starts on boot or admin command              │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Daemon Initializes (daemon.py)                          │
│    ├─ Load config files (risk_config.yaml, accounts.yaml) │
│    ├─ Initialize SQLite database                           │
│    ├─ Load state from database (lockouts, P&L)            │
│    └─ Setup logging                                        │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. SDK Connection (Project-X SDK)                          │
│    ├─ Authenticate with API key                            │
│    ├─ Connect to WebSocket (SignalR)                       │
│    ├─ Subscribe to account events                          │
│    └─ Wait for connection confirmation                     │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Risk Engine Loads Rules (rule_loader.py)                │
│    ├─ Read risk_config.yaml                                │
│    ├─ Instantiate enabled rules                            │
│    ├─ Initialize modules (MOD-001, 002, 003, 004)          │
│    └─ Verify rule configurations                           │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Event Loop Starts (daemon.py)                           │
│    ├─ Listen for SDK events (async)                        │
│    ├─ Check timers/lockouts every second (background)      │
│    ├─ Check reset time every minute (background)           │
│    └─ Process events through event router                  │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. System Ready                                             │
│    └─ Daemon monitoring account, enforcing rules           │
└─────────────────────────────────────────────────────────────┘
```

**Typical Startup Time:** 2-5 seconds

---

## Configuration Management

### accounts.yaml (TopstepX Authentication)
```yaml
topstepx:
  username: "your_username"
  api_key: "your_api_key_here"

monitored_account:
  account_id: 123
  account_name: "Main Trading Account"
```

**Location:** `C:/ProgramData/RiskManager/config/accounts.yaml` (production)

**Permissions:** Admin + SYSTEM (read/write), Trader (no access)

---

### risk_config.yaml (Risk Rule Settings)

#### Trade-by-Trade Rules (No Lockout)
```yaml
max_contracts:
  enabled: true
  limit: 5
  count_type: "net"  # net, long, short, gross
  close_all: true
  reduce_to_limit: false

max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 2
    ES: 1
    NQ: 1
  enforcement: "reduce_to_limit"  # or "close_all"
  unknown_symbol_action: "block"  # block, allow, close
```

#### Hard Lockout Rules
```yaml
daily_realized_loss:
  enabled: true
  limit: -500  # Negative value (loss)
  reset_time: "17:00"  # 5:00 PM
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
        end: "17:00"  # Overnight session
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
    per_minute_breach: 60      # 60-second cooldown
    per_hour_breach: 1800      # 30-minute cooldown
    per_session_breach: 3600   # 1-hour cooldown
```

**Location:** `C:/ProgramData/RiskManager/config/risk_config.yaml` (production)

**Permissions:** Admin + SYSTEM (read/write), Trader (no access)

---

## Windows Service Details

### Service Properties
- **Name:** `RiskManagerV34`
- **Display Name:** `Risk Manager V34`
- **Description:** `Trading risk management protection service for TopstepX accounts`
- **Account:** `LocalSystem` (highest privilege)
- **Startup Type:** `Automatic` (starts on boot)
- **Recovery Policy:** Auto-restart after 1 minute on failure

### Installation
```powershell
# Run as Administrator
python scripts/install_service.py

# Service installed and started
sc query RiskManagerV34
```

### Control
```powershell
# Start service (Admin)
sc start RiskManagerV34

# Stop service (Admin)
sc stop RiskManagerV34

# Restart service (Admin)
sc stop RiskManagerV34 && sc start RiskManagerV34

# Query status (Anyone)
sc query RiskManagerV34
```

**Status:** Service wrapper NOT IMPLEMENTED (critical deployment blocker)

**See:** `daemon-lifecycle.md` for complete lifecycle details

---

## Critical Implementation Gaps

### Blocking Implementation (0% Complete)
1. **Windows Service Wrapper** (Blocks deployment)
   - Location: `src/service/windows_service.py`
   - Effort: 1 week
   - Priority: CRITICAL

2. **Lockout Manager (MOD-002)** (Blocks 54% of rules)
   - Location: `src/state/lockout_manager.py`
   - Effort: 1.5 weeks
   - Priority: CRITICAL

3. **Timer Manager (MOD-003)** (Blocks 4 rules)
   - Location: `src/state/timer_manager.py`
   - Effort: 1 week
   - Priority: HIGH

4. **Reset Scheduler (MOD-004)** (Blocks 5 rules)
   - Location: `src/state/reset_scheduler.py`
   - Effort: 1 week
   - Priority: HIGH

5. **Event Router** (Integration point)
   - Location: `src/core/event_router.py`
   - Effort: 1 week
   - Priority: HIGH

**Total Estimated Effort:** 5.5 weeks

**See:** `/docs/analysis/wave2-gap-analysis/` for detailed gap analysis

---

## SDK Integration Notes

**CRITICAL:** The original specifications (v1) were written **BEFORE** Project-X-Py SDK existed.

### What SDK Provides (Don't Reinvent)
- WebSocket connections (SignalR)
- Real-time events (positions, orders, trades)
- Order management (place, cancel, modify)
- Position management (close, partially close)
- Account data & statistics
- Market data & indicators
- Auto-reconnection & error handling

### What Risk Manager Adds (Our Responsibility)
- Risk rule logic (12 rules)
- Enforcement actions (MOD-001)
- Lockout management (MOD-002)
- State persistence (SQLite)
- Admin/Trader CLIs
- Windows Service deployment
- Daily reset automation

**See:** `/docs/current/SDK_INTEGRATION_GUIDE.md` for complete SDK mapping

---

## Related Documentation

### Architecture Specifications (This Directory)
- `MOD-001-database-manager.md` - State persistence
- `MOD-002-lockout-manager.md` - Lockout system
- `MOD-003-timer-manager.md` - Timer management
- `MOD-004-reset-scheduler.md` - Daily reset
- `daemon-lifecycle.md` - Daemon operation

### Wave Analysis
- `/docs/analysis/wave1-feature-inventory/03-ARCHITECTURE-INVENTORY.md`
- `/docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md`
- `/docs/analysis/wave2-gap-analysis/05-DEPLOYMENT-GAPS.md`

### Original Specs (Archived)
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/architecture/system_architecture_v1.md`
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/architecture/system_architecture_v2.md`

---

**This is the authoritative system architecture for Risk Manager V34.**
