# Risk Manager V34 - Implementation Roadmap

**Goal**: Complete production-ready risk management system
**Approach**: Incremental implementation with working features at each phase

---

## 🎯 Implementation Phases

### ✅ Phase 0: Foundation (COMPLETE)
**Status**: Done
**Duration**: Completed 2025-10-23

- [x] Project structure created
- [x] Core modules (manager, engine, events, config)
- [x] SDK integration (suite_manager, event_bridge, enforcement)
- [x] 2 basic rules (max_position, max_contracts_per_instrument)
- [x] Example code (4 examples)
- [x] Documentation (46 spec docs)
- [x] API connection verified
- [x] WSL environment setup

**Deliverables**:
- Working async architecture
- Project-X-Py SDK integrated
- Basic risk enforcement
- Comprehensive specifications

---

### 🔄 Phase 1: Configuration & CLI (IN PROGRESS)
**Priority**: CRITICAL
**Duration**: 1-2 weeks
**Dependencies**: None

#### 1.1 YAML Configuration System
**Files to Create**:
- `src/config/loader.py` - Load/validate YAML configs
- `src/config/validator.py` - Validate config structure
- `src/config/defaults.py` - Default config templates
- `config/accounts.yaml` - TopstepX auth config
- `config/risk_config.yaml` - Risk rules config
- `config/holidays.yaml` - Trading holidays

**Features**:
- ✅ Load YAML files
- ✅ Validate structure (Pydantic schemas)
- ✅ Provide defaults
- ✅ Environment variable override
- ✅ Config migration (version updates)

**Acceptance Criteria**:
- [ ] Can load all configs from YAML
- [ ] Invalid config shows helpful errors
- [ ] Example configs provided
- [ ] Tests for config validation

**Estimated Time**: 2-3 days

---

#### 1.2 Trader CLI (View-Only Status)
**Files to Create**:
- `src/cli/trader/__init__.py`
- `src/cli/trader/trader_main.py` - Main trader menu
- `src/cli/trader/status_screen.py` - Real-time status
- `src/cli/trader/lockout_display.py` - Lockout timers
- `src/cli/trader/logs_viewer.py` - Enforcement logs
- `src/cli/trader/formatting.py` - UI helpers

**Features**:
- ✅ Real-time status display
- ✅ Current positions & P&L
- ✅ Active rules display
- ✅ Lockout timers (if locked)
- ✅ Enforcement action log
- ✅ Color-coded alerts (green/yellow/red)
- ✅ Auto-refresh every second

**UI Mockup**:
```
┌────────────────────────────────────────────────────────────┐
│ Risk Manager V34 - Trader Status                          │
├────────────────────────────────────────────────────────────┤
│ Account: PRAC-V2-126244-84184528                          │
│ Status: ✅ ACTIVE  │  Lockout: ❌ None                    │
│ Daily P&L: +$245.00 │ Unrealized: +$50.00                │
├────────────────────────────────────────────────────────────┤
│ Active Positions:                                          │
│   MNQ: +2 contracts @ 20,125.00 (+$50.00)                 │
│                                                             │
│ Active Rules:                                              │
│   ✅ Max Contracts: 2/5                                    │
│   ✅ Daily Loss Limit: +$245 / -$500                      │
│   ⚠️  Trade Frequency: 8/10 (per hour)                    │
│                                                             │
│ Recent Enforcement:                                        │
│   [14:23:15] No action needed                             │
│                                                             │
│ Press 'r' to refresh | 'q' to quit                        │
└────────────────────────────────────────────────────────────┘
```

**Acceptance Criteria**:
- [ ] Shows real-time account status
- [ ] Updates every second
- [ ] Displays all active rules
- [ ] Shows lockout if active
- [ ] Color-coded (green=good, red=violation)
- [ ] Runs without admin password

**Estimated Time**: 3-4 days

---

#### 1.3 Admin CLI (Password-Protected Config)
**Files to Create**:
- `src/cli/admin/__init__.py`
- `src/cli/admin/admin_main.py` - Admin menu
- `src/cli/admin/auth.py` - Password verification
- `src/cli/admin/configure_rules.py` - Rule config wizard
- `src/cli/admin/manage_accounts.py` - Account setup
- `src/cli/admin/service_control.py` - Start/stop daemon

**Features**:
- ✅ Password authentication (bcrypt hash)
- ✅ Interactive rule configuration
- ✅ Account/API key management
- ✅ Daemon start/stop/restart
- ✅ View raw configs
- ✅ Config validation before save

**UI Flow**:
```
$ risk-admin

Password: ********

┌────────────────────────────────────┐
│ Risk Manager - Admin Panel         │
├────────────────────────────────────┤
│ 1. Configure Risk Rules            │
│ 2. Manage Accounts                 │
│ 3. Service Control                 │
│ 4. View Logs                       │
│ 5. Exit                            │
└────────────────────────────────────┘

Select option: 1

┌────────────────────────────────────┐
│ Configure Risk Rules                │
├────────────────────────────────────┤
│ 1. Max Contracts                   │
│ 2. Daily Loss Limit                │
│ 3. Trade Frequency                 │
│ ...                                │
└────────────────────────────────────┘
```

**Acceptance Criteria**:
- [ ] Password required to access
- [ ] Can configure all rules via wizard
- [ ] Can add/edit TopstepX credentials
- [ ] Can start/stop daemon
- [ ] Changes saved to YAML files
- [ ] Config validated before save

**Estimated Time**: 4-5 days

---

#### 1.4 CLI Entry Points
**Files to Create**:
- `src/risk_manager/__main__.py` - Package entry point
- `src/cli/main.py` - CLI router

**Commands**:
```bash
# Trader CLI (no password)
risk-status

# Admin CLI (password required)
risk-admin

# Or via python module
python -m risk_manager status
python -m risk_manager admin
```

**Acceptance Criteria**:
- [ ] Both CLIs accessible via commands
- [ ] Help text available (`--help`)
- [ ] Version info (`--version`)

**Estimated Time**: 1 day

---

**Phase 1 Total**: ~10-13 days

---

### 🔄 Phase 2: State Persistence (NEXT)
**Priority**: HIGH
**Duration**: 1 week
**Dependencies**: Phase 1 (config system)

#### 2.1 SQLite Database Schema
**Files to Create**:
- `src/state/persistence.py` - Database interface
- `src/state/schema.sql` - Database schema
- `data/state.db` - SQLite database (created at runtime)

**Schema**:
```sql
-- Lockout states
CREATE TABLE lockouts (
    account_id TEXT PRIMARY KEY,
    reason TEXT NOT NULL,
    locked_until DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Daily P&L tracking
CREATE TABLE daily_pnl (
    account_id TEXT,
    date DATE,
    realized_pnl REAL,
    unrealized_pnl REAL,
    trade_count INTEGER,
    PRIMARY KEY (account_id, date)
);

-- Trade history (for frequency limits)
CREATE TABLE trade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT,
    symbol TEXT,
    timestamp DATETIME,
    side TEXT,
    quantity INTEGER,
    price REAL
);

-- Enforcement log
CREATE TABLE enforcement_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT,
    rule_name TEXT,
    action TEXT,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Timer states (cooldowns)
CREATE TABLE timers (
    name TEXT PRIMARY KEY,
    expires_at DATETIME,
    callback_data TEXT
);
```

**Features**:
- ✅ Auto-create DB on first run
- ✅ Schema migrations (version upgrades)
- ✅ Async database operations (aiosqlite)
- ✅ Automatic backups
- ✅ Crash recovery

**Acceptance Criteria**:
- [ ] Database created automatically
- [ ] All tables created
- [ ] Data persists across restarts
- [ ] Backups created daily

**Estimated Time**: 2-3 days

---

#### 2.2 State Manager
**Files to Create**:
- `src/state/state_manager.py` - In-memory state tracking
- `src/state/pnl_tracker.py` - P&L calculations

**Features**:
- ✅ Track positions in memory
- ✅ Calculate realized/unrealized P&L
- ✅ Track trade counts
- ✅ Sync to database periodically
- ✅ Restore from database on startup

**Acceptance Criteria**:
- [ ] Accurate P&L tracking
- [ ] State synced every 10 seconds
- [ ] Restores state on restart
- [ ] Memory efficient

**Estimated Time**: 2 days

---

#### 2.3 Lockout Manager (MOD-002)
**Files to Create**:
- `src/state/lockout_manager.py` - Lockout logic

**Features**:
- ✅ `set_lockout(account_id, reason, until)` - Set hard lockout
- ✅ `set_cooldown(account_id, reason, duration)` - Set timer lockout
- ✅ `is_locked_out(account_id)` - Check lockout status
- ✅ `get_lockout_info(account_id)` - Get reason & expiry
- ✅ `clear_lockout(account_id)` - Manual unlock
- ✅ `check_expired_lockouts()` - Auto-clear expired
- ✅ Persist lockouts to database

**Acceptance Criteria**:
- [ ] Lockouts persist across restarts
- [ ] Auto-expire at correct time
- [ ] Trader CLI shows lockout timers
- [ ] Admin can manually unlock

**Estimated Time**: 2 days

---

#### 2.4 Timer Manager (MOD-003)
**Files to Create**:
- `src/state/timer_manager.py` - Countdown timers

**Features**:
- ✅ `start_timer(name, duration, callback)` - Start timer
- ✅ `get_remaining_time(name)` - Time remaining
- ✅ `cancel_timer(name)` - Stop timer
- ✅ `check_timers()` - Fire callbacks
- ✅ Persist timers to database

**Acceptance Criteria**:
- [ ] Timers survive restarts
- [ ] Callbacks fire at correct time
- [ ] Trader CLI shows countdowns

**Estimated Time**: 1-2 days

---

#### 2.5 Reset Scheduler (MOD-004)
**Files to Create**:
- `src/state/reset_scheduler.py` - Daily resets

**Features**:
- ✅ Schedule daily reset (default 17:00 ET)
- ✅ Reset P&L counters
- ✅ Clear daily lockouts
- ✅ Respect trading holidays
- ✅ Manual reset trigger (admin)

**Acceptance Criteria**:
- [ ] Auto-reset at 5:00 PM ET
- [ ] Clears daily P&L
- [ ] Logs reset action
- [ ] Admin can trigger manually

**Estimated Time**: 1-2 days

---

**Phase 2 Total**: ~8-11 days

---

### 🔄 Phase 3: Complete Enforcement System
**Priority**: HIGH
**Duration**: 1 week
**Dependencies**: Phase 2 (state persistence)

#### 3.1 Enforcement Engine (MOD-001)
**Files to Create**:
- `src/enforcement/actions.py` - Enforcement actions
- `src/enforcement/enforcement_engine.py` - Orchestration

**Features**:
- ✅ `close_all_positions(account_id)` - Flatten account
- ✅ `close_position(account_id, contract_id)` - Close specific
- ✅ `reduce_position_to_limit(account_id, contract_id, limit)` - Partial close
- ✅ `cancel_all_orders(account_id)` - Cancel pending
- ✅ Simultaneous actions (close + cancel + lockout)
- ✅ Millisecond latency enforcement
- ✅ Error handling & retries
- ✅ Enforcement logging

**Acceptance Criteria**:
- [ ] Actions execute within 500ms
- [ ] Retries on failure (up to 3x)
- [ ] Logs all enforcement actions
- [ ] Coordinates with lockout manager

**Estimated Time**: 3-4 days

---

**Phase 3 Total**: ~3-4 days

---

### 🔄 Phase 4: Complete All 12 Risk Rules
**Priority**: MEDIUM
**Duration**: 1-2 weeks
**Dependencies**: Phase 3 (enforcement system)

#### Remaining 10 Rules to Implement

| Rule | File | Complexity | Est. Time | Dependencies |
|------|------|------------|-----------|--------------|
| RULE-003 | `daily_realized_loss.py` | Medium | 1 day | State, Lockout |
| RULE-004 | `daily_unrealized_loss.py` | Medium | 1 day | State, Lockout |
| RULE-005 | `max_unrealized_profit.py` | Medium | 1 day | State, Lockout |
| RULE-006 | `trade_frequency_limit.py` | High | 2 days | State, Timer, Lockout |
| RULE-007 | `cooldown_after_loss.py` | High | 2 days | State, Timer, Lockout |
| RULE-008 | `no_stop_loss_grace.py` | Medium | 1 day | SDK Events |
| RULE-009 | `session_block_outside.py` | High | 2 days | State, Holidays, Lockout |
| RULE-010 | `auth_loss_guard.py` | Low | 1 day | SDK Events |
| RULE-011 | `symbol_blocks.py` | Low | 1 day | Config |
| RULE-012 | `trade_management.py` | High | 2-3 days | SDK, Enforcement |

**Total**: 14-16 days (can parallelize some)

**Approach**: Implement 1-2 rules per day, following specs in `docs/PROJECT_DOCS/rules/`

---

**Phase 4 Total**: ~14-16 days

---

### 🔄 Phase 5: Windows Service Integration
**Priority**: MEDIUM
**Duration**: 3-5 days
**Dependencies**: Phase 4 (all rules working)

#### 5.1 Windows Service Wrapper
**Files to Create**:
- `src/service/windows_service.py` - Service integration
- `src/service/installer.py` - Install/uninstall
- `src/service/watchdog.py` - Auto-restart

**Features**:
- ✅ Run as Windows Service
- ✅ Auto-start on boot
- ✅ Cannot be killed without admin password
- ✅ Auto-restart on crash
- ✅ Service control via Admin CLI

**Acceptance Criteria**:
- [ ] Installs as Windows Service
- [ ] Starts automatically on boot
- [ ] Admin password required to stop
- [ ] Restarts on crash within 10 seconds

**Estimated Time**: 3-5 days

---

**Phase 5 Total**: ~3-5 days

---

### 🔄 Phase 6: Testing & Hardening
**Priority**: HIGH
**Duration**: 1-2 weeks
**Dependencies**: Phase 5 (service working)

#### 6.1 Unit Tests
**Files to Create**:
- `tests/conftest.py` - Pytest fixtures
- `tests/unit/test_rules/*.py` - Test each rule
- `tests/unit/test_enforcement.py`
- `tests/unit/test_lockout_manager.py`
- `tests/unit/test_timer_manager.py`
- `tests/unit/test_state_manager.py`

**Coverage Goal**: >80%

**Estimated Time**: 5-7 days

---

#### 6.2 Integration Tests
**Files to Create**:
- `tests/integration/test_full_workflow.py` - End-to-end
- `tests/integration/test_api_integration.py` - API mocking
- `tests/integration/test_persistence.py` - State save/load

**Estimated Time**: 3-4 days

---

#### 6.3 Production Hardening
**Features**:
- ✅ Comprehensive error handling
- ✅ Structured logging (separate log files)
- ✅ Performance monitoring
- ✅ Memory leak testing
- ✅ Stress testing (high-frequency trading)

**Estimated Time**: 2-3 days

---

**Phase 6 Total**: ~10-14 days

---

### 🔄 Phase 7: Documentation & Deployment
**Priority**: LOW
**Duration**: 3-5 days
**Dependencies**: Phase 6 (testing complete)

**Tasks**:
- [ ] Complete API documentation
- [ ] User guide (admin + trader)
- [ ] Installation guide
- [ ] Troubleshooting guide
- [ ] Video walkthrough
- [ ] Deployment scripts
- [ ] Production config examples

**Estimated Time**: 3-5 days

---

**Phase 7 Total**: ~3-5 days

---

## 📅 Timeline Summary

| Phase | Duration | Dependencies | Start After |
|-------|----------|--------------|-------------|
| ✅ Phase 0: Foundation | Complete | None | - |
| 🔄 Phase 1: Config & CLI | 10-13 days | None | Now |
| Phase 2: Persistence | 8-11 days | Phase 1 | Week 2 |
| Phase 3: Enforcement | 3-4 days | Phase 2 | Week 3 |
| Phase 4: All Rules | 14-16 days | Phase 3 | Week 4 |
| Phase 5: Windows Service | 3-5 days | Phase 4 | Week 6 |
| Phase 6: Testing | 10-14 days | Phase 5 | Week 7 |
| Phase 7: Documentation | 3-5 days | Phase 6 | Week 9 |

**Total Estimated Time**: 51-68 days (solo developer, ~10-14 weeks)

**With Parallel Work**: 40-50 days (~8-10 weeks)

---

## 🎯 Minimum Viable Product (MVP)

**Goal**: Working system with core protection

### MVP Scope (4 weeks)
- [x] Phase 0: Foundation ✅
- [ ] Phase 1: Config & CLI
- [ ] Phase 2: Persistence
- [ ] Phase 3: Enforcement
- [ ] 3-5 Core Rules:
  - [ ] RULE-001: Max Contracts
  - [ ] RULE-002: Max Contracts Per Instrument
  - [ ] RULE-003: Daily Realized Loss
  - [ ] RULE-009: Session Block Outside
  - [ ] RULE-010: Auth Loss Guard

**MVP Timeline**: ~4 weeks
**MVP Features**:
- ✅ Basic risk protection
- ✅ CLI interfaces
- ✅ State persistence
- ⚠️  Limited rules (5 of 12)
- ⚠️  No Windows Service (run manually)

---

## 🚀 Quick Start for Next Session

### Immediate Next Steps (Pick One):

#### Option A: Build Trader CLI
**Why**: Immediate visibility into system
**Complexity**: Medium
**Time**: 3-4 days
**Files**: `src/cli/trader/*.py`

#### Option B: Build YAML Config System
**Why**: Enables rule configuration
**Complexity**: Low-Medium
**Time**: 2-3 days
**Files**: `src/config/*.py`, `config/*.yaml`

#### Option C: Implement RULE-003 (Daily Loss)
**Why**: Most critical risk protection
**Complexity**: Medium
**Time**: 1-2 days
**Files**: `src/rules/daily_realized_loss.py`
**Dependencies**: Need state persistence first

---

## 📊 Priority Matrix

| Task | Impact | Effort | Priority | Do When |
|------|--------|--------|----------|---------|
| Trader CLI | High | Medium | 🔴 P0 | Now |
| YAML Config | High | Low | 🔴 P0 | Now |
| Admin CLI | High | High | 🟡 P1 | After config |
| State Persistence | Critical | Medium | 🔴 P0 | Week 2 |
| RULE-003 (Daily Loss) | Critical | Low | 🔴 P0 | After persistence |
| Lockout Manager | Critical | Medium | 🔴 P0 | Week 2 |
| Remaining Rules | High | High | 🟡 P1 | Week 3-4 |
| Windows Service | Medium | Medium | 🟢 P2 | Week 6 |
| Tests | High | High | 🟡 P1 | Week 7 |

---

## 🏆 Success Criteria

### Phase Completion Checklist

**Phase 1 Complete When**:
- [ ] Can configure rules via Admin CLI
- [ ] Can view status via Trader CLI
- [ ] All configs loaded from YAML files
- [ ] Password protection working

**Phase 2 Complete When**:
- [ ] State persists to SQLite
- [ ] Survives daemon restart
- [ ] Lockouts work correctly
- [ ] Daily reset at 5 PM ET

**Phase 3 Complete When**:
- [ ] Enforcement < 500ms latency
- [ ] Simultaneous actions work
- [ ] Error handling robust
- [ ] All actions logged

**Phase 4 Complete When**:
- [ ] All 12 rules implemented
- [ ] Each rule tested
- [ ] Config examples for each rule
- [ ] Documentation updated

**Production Ready When**:
- [ ] All phases complete
- [ ] >80% test coverage
- [ ] Windows Service installed
- [ ] Running on live account (paper trading)
- [ ] Monitoring in place
- [ ] Documentation complete

---

**Last Updated**: 2025-10-23
**Next Review**: After Phase 1 completion
**See Also**: `CURRENT_STATE.md`, `PROJECT_STRUCTURE.md`
