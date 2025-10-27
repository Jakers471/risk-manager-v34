# Risk Manager V34 - Complete Project Structure

**Target**: Full implementation based on specification documents
**Status**: Foundation complete, CLI & Service layers needed

---

## 📁 Complete Directory Tree

```
risk-manager-v34/
│
├── 📄 README.md                           ✅ Project overview
├── 📄 STATUS.md                           ✅ Current status & setup guide
├── 📄 CURRENT_STATE.md                    ✅ Detailed progress tracking
├── 📄 PROJECT_STRUCTURE.md                ✅ This file
├── 📄 ROADMAP.md                          ✅ Implementation roadmap
├── 📄 SESSION_RESUME.md                   ✅ Quick resume guide for Claude
│
├── 📄 .env                                ✅ Environment variables (gitignored)
├── 📄 .env.example                        ✅ Example environment file
├── 📄 .gitignore                          ✅ Git ignore rules
├── 📄 pyproject.toml                      ✅ Python dependencies & config
├── 📄 uv.lock                             ✅ UV lock file
│
├── 📂 src/risk_manager/                   # Main source code
│   │
│   ├── 📄 __init__.py                     ✅ Package initialization
│   ├── 📄 __main__.py                     ❌ Entry point for CLI commands
│   │
│   ├── 📂 core/                           # Core daemon logic ✅
│   │   ├── 📄 __init__.py                 ✅ Core module exports
│   │   ├── 📄 manager.py                  ✅ RiskManager main class (~200 lines)
│   │   ├── 📄 engine.py                   ✅ Rule evaluation engine (~150 lines)
│   │   ├── 📄 events.py                   ✅ Event system (EventBus) (~100 lines)
│   │   ├── 📄 config.py                   ⚠️  Basic Pydantic config (~80 lines)
│   │   ├── 📄 daemon.py                   ❌ Main service loop (~150 lines)
│   │   ├── 📄 rule_loader.py              ❌ Dynamic rule loading (~80 lines)
│   │   └── 📄 event_router.py             ❌ Route events to rules (~100 lines)
│   │
│   ├── 📂 api/                            # TopstepX API integration ❌
│   │   ├── 📄 __init__.py                 ❌ API module exports
│   │   ├── 📄 auth.py                     ❌ JWT authentication (~80 lines)
│   │   ├── 📄 rest_client.py              ❌ REST API wrapper (~120 lines)
│   │   ├── 📄 signalr_listener.py         ❌ WebSocket event listener (~150 lines)
│   │   └── 📄 connection_manager.py       ❌ Connection health, reconnect (~100 lines)
│   │
│   ├── 📂 sdk/                            # Project-X-Py SDK wrapper ✅
│   │   ├── 📄 __init__.py                 ✅ SDK module exports
│   │   ├── 📄 suite_manager.py            ✅ TradingSuite lifecycle (~220 lines)
│   │   ├── 📄 event_bridge.py             ✅ SDK → RiskManager events (~150 lines)
│   │   └── 📄 enforcement.py              ⚠️  Basic enforcement (~100 lines)
│   │
│   ├── 📂 enforcement/                    # Enforcement actions (MOD-001) ❌
│   │   ├── 📄 __init__.py                 ❌ Enforcement module exports
│   │   ├── 📄 actions.py                  ❌ Close, cancel, reduce (~120 lines)
│   │   └── 📄 enforcement_engine.py       ❌ Orchestrate enforcement (~80 lines)
│   │
│   ├── 📂 rules/                          # Risk rules (12 total)
│   │   ├── 📄 __init__.py                 ✅ Rule exports
│   │   ├── 📄 base.py                     ✅ Abstract RiskRule class (~80 lines)
│   │   │
│   │   ├── 📄 max_position.py             ✅ RULE-001: Max contracts (~90 lines)
│   │   ├── 📄 max_contracts_per_instrument.py ✅ RULE-002: Per-instrument (~100 lines)
│   │   ├── 📄 daily_loss.py               ⚠️  RULE-003: Daily realized loss (~70 lines, incomplete)
│   │   ├── 📄 daily_unrealized_loss.py    ❌ RULE-004: Daily unrealized loss (~130 lines)
│   │   ├── 📄 max_unrealized_profit.py    ❌ RULE-005: Profit target (~120 lines)
│   │   ├── 📄 trade_frequency_limit.py    ❌ RULE-006: Trade frequency (~150 lines)
│   │   ├── 📄 cooldown_after_loss.py      ❌ RULE-007: Cooldown timer (~130 lines)
│   │   ├── 📄 no_stop_loss_grace.py       ❌ RULE-008: Stop-loss enforcement (~110 lines)
│   │   ├── 📄 session_block_outside.py    ❌ RULE-009: Session restrictions (~140 lines)
│   │   ├── 📄 auth_loss_guard.py          ❌ RULE-010: canTrade monitor (~80 lines)
│   │   ├── 📄 symbol_blocks.py            ❌ RULE-011: Symbol blacklist (~90 lines)
│   │   └── 📄 trade_management.py         ❌ RULE-012: Auto stops/breakeven (~150 lines)
│   │
│   ├── 📂 state/                          # State management & persistence ❌
│   │   ├── 📄 __init__.py                 ❌ State module exports
│   │   ├── 📄 state_manager.py            ❌ In-memory state (~150 lines)
│   │   ├── 📄 persistence.py              ❌ SQLite save/load (~120 lines)
│   │   ├── 📄 lockout_manager.py          ❌ MOD-002: Lockout logic (~150 lines)
│   │   ├── 📄 timer_manager.py            ❌ MOD-003: Timer logic (~120 lines)
│   │   ├── 📄 reset_scheduler.py          ❌ MOD-004: Daily reset (~100 lines)
│   │   └── 📄 pnl_tracker.py              ❌ P&L calculations (~130 lines)
│   │
│   ├── 📂 cli/                            # Command-line interfaces ❌
│   │   ├── 📄 __init__.py                 ❌ CLI module exports
│   │   ├── 📄 main.py                     ❌ CLI entry & routing (~80 lines)
│   │   │
│   │   ├── 📂 admin/                      # Admin CLI (password-protected) ❌
│   │   │   ├── 📄 __init__.py             ❌ Admin module exports
│   │   │   ├── 📄 admin_main.py           ❌ Admin menu (~100 lines)
│   │   │   ├── 📄 auth.py                 ❌ Password verification (~60 lines)
│   │   │   ├── 📄 configure_rules.py      ❌ Rule config wizard (~150 lines)
│   │   │   ├── 📄 manage_accounts.py      ❌ Account/API setup (~120 lines)
│   │   │   └── 📄 service_control.py      ❌ Start/stop daemon (~80 lines)
│   │   │
│   │   └── 📂 trader/                     # Trader CLI (view-only) ❌
│   │       ├── 📄 __init__.py             ❌ Trader module exports
│   │       ├── 📄 trader_main.py          ❌ Trader menu (~80 lines)
│   │       ├── 📄 status_screen.py        ❌ Main status display (~120 lines)
│   │       ├── 📄 lockout_display.py      ❌ Lockout timer UI (~100 lines)
│   │       ├── 📄 logs_viewer.py          ❌ Enforcement log viewer (~100 lines)
│   │       ├── 📄 clock_tracker.py        ❌ Clock in/out tracking (~70 lines)
│   │       └── 📄 formatting.py           ❌ Colors, tables, helpers (~80 lines)
│   │
│   ├── 📂 config/                         # Configuration management ❌
│   │   ├── 📄 __init__.py                 ❌ Config module exports
│   │   ├── 📄 loader.py                   ❌ Load/validate YAML (~100 lines)
│   │   ├── 📄 validator.py                ❌ Config validation (~90 lines)
│   │   └── 📄 defaults.py                 ❌ Default templates (~60 lines)
│   │
│   ├── 📂 utils/                          # Shared utilities ⚠️
│   │   ├── 📄 __init__.py                 ❌ Utils module exports
│   │   ├── 📄 logging.py                  ⚠️  Basic logging setup (~80 lines)
│   │   ├── 📄 datetime_helpers.py         ❌ Time/date utils (~70 lines)
│   │   ├── 📄 holidays.py                 ❌ Holiday calendar (~60 lines)
│   │   └── 📄 validation.py               ❌ Input validation (~50 lines)
│   │
│   ├── 📂 service/                        # Windows Service wrapper ❌
│   │   ├── 📄 __init__.py                 ❌ Service module exports
│   │   ├── 📄 windows_service.py          ❌ Windows Service (~120 lines)
│   │   ├── 📄 installer.py                ❌ Install/uninstall (~100 lines)
│   │   └── 📄 watchdog.py                 ❌ Auto-restart (~80 lines)
│   │
│   ├── 📂 integrations/                   # External integrations ⚠️
│   │   ├── 📄 __init__.py                 ✅ Integrations exports
│   │   └── 📄 trading.py                  ⚠️  Basic placeholder (~80 lines)
│   │
│   ├── 📂 ai/                             # AI integration (optional) ⚠️
│   │   ├── 📄 __init__.py                 ✅ AI module exports
│   │   └── 📄 integration.py              ⚠️  Claude-Flow placeholder (~50 lines)
│   │
│   └── 📂 monitoring/                     # Monitoring & metrics ❌
│       ├── 📄 __init__.py                 ❌ Monitoring exports
│       ├── 📄 metrics.py                  ❌ Performance metrics (~100 lines)
│       ├── 📄 health.py                   ❌ Health checks (~80 lines)
│       └── 📄 dashboard.py                ❌ Real-time dashboard (~150 lines)
│
├── 📂 config/                             # Configuration files ❌
│   ├── 📄 accounts.yaml                   ❌ TopstepX auth & account
│   ├── 📄 risk_config.yaml                ❌ Risk rule settings
│   ├── 📄 holidays.yaml                   ❌ Trading holidays
│   ├── 📄 admin_password.hash             ❌ Hashed admin password
│   └── 📄 config.example.yaml             ❌ Example config
│
├── 📂 data/                               # Runtime data (gitignored) ❌
│   ├── 📄 state.db                        ❌ SQLite database
│   └── 📂 backups/                        ❌ State backups
│
├── 📂 logs/                               # Log files (gitignored) ⚠️
│   ├── 📄 daemon.log                      ⚠️  Main daemon log
│   ├── 📄 enforcement.log                 ❌ Enforcement actions
│   ├── 📄 api.log                         ❌ API interactions
│   └── 📄 error.log                       ❌ Errors only
│
├── 📂 tests/                              # Test suite ❌
│   ├── 📄 __init__.py                     ❌ Test package
│   ├── 📄 conftest.py                     ❌ Pytest fixtures
│   │
│   ├── 📂 unit/                           # Unit tests ❌
│   │   ├── 📂 test_rules/                 # Test each rule
│   │   │   ├── 📄 test_max_contracts.py   ❌
│   │   │   ├── 📄 test_daily_loss.py      ❌
│   │   │   └── 📄 ... (one per rule)      ❌
│   │   ├── 📄 test_enforcement.py         ❌
│   │   ├── 📄 test_lockout_manager.py     ❌
│   │   ├── 📄 test_timer_manager.py       ❌
│   │   ├── 📄 test_state_manager.py       ❌
│   │   └── 📄 test_pnl_tracker.py         ❌
│   │
│   └── 📂 integration/                    # Integration tests ❌
│       ├── 📄 test_full_workflow.py       ❌ End-to-end scenarios
│       ├── 📄 test_api_integration.py     ❌ TopstepX API mocking
│       └── 📄 test_persistence.py         ❌ State save/load
│
├── 📂 docs/                               # Documentation ✅
│   ├── 📄 INDEX.md                        ✅ Documentation index
│   ├── 📄 quickstart.md                   ✅ Quick start guide
│   ├── 📄 summary_2025-10-23.md           ✅ Project summary
│   │
│   ├── 📂 implementation/                 # Implementation guides ⚠️
│   │   └── 📄 plan_2025-10-23.md          ✅ Implementation plan
│   │
│   ├── 📂 progress/                       # Progress tracking ⚠️
│   │   └── 📄 phase_2-1_complete_2025-10-23.md ✅
│   │
│   └── 📂 PROJECT_DOCS/                   # Specification docs ✅
│       ├── 📄 README.md                   ✅ Docs overview
│       ├── 📄 INTEGRATION_NOTE.md         ✅ How to use these docs
│       ├── 📄 ARCHITECTURE_INDEX.md       ✅ Architecture index
│       ├── 📄 REFERENCE_GUIDE.md          ✅ Quick reference
│       ├── 📄 CURRENT_VERSION.md          ✅ Version info
│       │
│       ├── 📂 summary/                    ✅ High-level overviews
│       │   └── 📄 project_overview.md     ✅ Vision & goals
│       │
│       ├── 📂 architecture/               ✅ System architecture
│       │   ├── 📄 system_architecture_v1.md ✅
│       │   └── 📄 system_architecture_v2.md ✅
│       │
│       ├── 📂 modules/                    ✅ Module specifications
│       │   ├── 📄 enforcement_actions.md  ✅ MOD-001 spec
│       │   ├── 📄 lockout_manager.md      ✅ MOD-002 spec
│       │   ├── 📄 timer_manager.md        ✅ MOD-003 spec
│       │   └── 📄 reset_scheduler.md      ✅ MOD-004 spec
│       │
│       ├── 📂 rules/                      ✅ Rule specifications
│       │   ├── 📄 01_max_contracts.md     ✅ RULE-001 spec
│       │   ├── 📄 02_max_contracts_per_instrument.md ✅
│       │   ├── 📄 03_daily_realized_loss.md ✅
│       │   ├── 📄 04_daily_unrealized_loss.md ✅
│       │   ├── 📄 05_max_unrealized_profit.md ✅
│       │   ├── 📄 06_trade_frequency_limit.md ✅
│       │   ├── 📄 07_cooldown_after_loss.md ✅
│       │   ├── 📄 08_no_stop_loss_grace.md ✅
│       │   ├── 📄 09_session_block_outside.md ✅
│       │   ├── 📄 10_auth_loss_guard.md   ✅
│       │   ├── 📄 11_symbol_blocks.md     ✅
│       │   └── 📄 12_trade_management.md  ✅
│       │
│       ├── 📂 api/                        ✅ API integration
│       │   └── 📄 topstepx_integration.md ✅
│       │
│       ├── 📂 projectx_gateway_api/       ✅ API documentation
│       │   ├── 📂 getting_started/        ✅
│       │   ├── 📂 account/                ✅
│       │   ├── 📂 orders/                 ✅
│       │   ├── 📂 positions/              ✅
│       │   ├── 📂 trades/                 ✅
│       │   ├── 📂 market_data/            ✅
│       │   └── 📂 realtime_updates/       ✅
│       │
│       └── 📂 sessions/                   ✅ Session notes
│           └── 📄 2025-10-19.md           ✅
│
├── 📂 examples/                           # Code examples ✅
│   ├── 📄 README.md                       ✅ Examples guide
│   ├── 📄 01_basic_usage.py               ✅ Simple protection
│   ├── 📄 02_advanced_rules.py            ✅ Custom rules
│   ├── 📄 03_multi_instrument.py          ✅ Multi-instrument
│   └── 📄 04_sdk_integration.py           ✅ Direct SDK usage
│
├── 📂 scripts/                            # Utility scripts ❌
│   ├── 📄 install_service.py              ❌ Install Windows Service
│   ├── 📄 uninstall_service.py            ❌ Remove service
│   └── 📄 dev_run.py                      ❌ Run in dev mode
│
└── 📄 test_connection.py                  ✅ API connection test
```

---

## 📊 File Status Legend

- ✅ **Complete** - Fully implemented and tested
- ⚠️  **Partial** - Basic implementation, needs enhancement
- ❌ **Missing** - Not yet implemented

---

## 📈 Progress by Directory

| Directory | Total Files | Complete | Partial | Missing | Progress |
|-----------|-------------|----------|---------|---------|----------|
| `src/core/` | 7 | 5 | 1 | 1 | 71% |
| `src/sdk/` | 4 | 3 | 1 | 0 | 75% |
| `src/rules/` | 13 | 3 | 1 | 9 | 23% |
| `src/enforcement/` | 3 | 0 | 0 | 3 | 0% |
| `src/state/` | 7 | 0 | 0 | 7 | 0% |
| `src/cli/` | 14 | 0 | 0 | 14 | 0% |
| `src/config/` | 4 | 0 | 0 | 4 | 0% |
| `src/service/` | 4 | 0 | 0 | 4 | 0% |
| `src/api/` | 5 | 0 | 0 | 5 | 0% |
| `src/utils/` | 5 | 0 | 1 | 4 | 10% |
| `tests/` | 15+ | 0 | 0 | 15+ | 0% |
| `config/` | 5 | 0 | 0 | 5 | 0% |
| `examples/` | 5 | 5 | 0 | 0 | 100% |
| `docs/` | 50+ | 48 | 2 | 0 | 96% |

**Overall**: ~25% complete (~20 of ~80 core files)

---

## 🎯 Critical Missing Components

### Priority 1: User Interface (0% complete)
```
src/cli/
├── admin/           # Admin CLI - 0/6 files
│   └── (all files missing)
└── trader/          # Trader CLI - 0/7 files
    └── (all files missing)
```
**Impact**: Cannot configure or monitor system without code editing

---

### Priority 2: Configuration System (0% complete)
```
src/config/          # Config management - 0/4 files
config/              # Config files - 0/5 files
```
**Impact**: All config is hardcoded in `.env`, no YAML support

---

### Priority 3: State Persistence (0% complete)
```
src/state/           # State management - 0/7 files
data/                # SQLite database - not created
```
**Impact**: State lost on restart, no crash recovery

---

### Priority 4: Enforcement System (Basic only)
```
src/enforcement/     # Enforcement - 0/3 files
src/sdk/enforcement.py  # Basic only
```
**Impact**: Limited enforcement actions, no coordination

---

### Priority 5: Windows Service (0% complete)
```
src/service/         # Service wrapper - 0/4 files
scripts/             # Install scripts - 0/3 files
```
**Impact**: Cannot run as Windows Service, no auto-start

---

### Priority 6: Testing Infrastructure (0% complete)
```
tests/               # Test suite - 0/15+ files
```
**Impact**: No automated testing, manual verification only

---

## 🔧 Component Dependencies

### Dependency Graph
```
Windows Service
    ↓ requires
Core Daemon
    ↓ requires
State Persistence + Enforcement
    ↓ requires
Rules + SDK Integration
    ↓ requires
Config System
    ↓ requires
CLI (for setup)
```

### Build Order Recommendation
1. **Config System** → Enable YAML configuration
2. **CLI (Trader)** → View-only status interface
3. **CLI (Admin)** → Configuration interface
4. **State Persistence** → SQLite storage
5. **Enforcement System** → Complete MOD-001
6. **Remaining Rules** → RULE-003 through RULE-012
7. **Windows Service** → Service wrapper
8. **Testing** → Comprehensive test suite

---

## 📋 Estimated Implementation

### Line Count Estimates (from spec)
```
Core modules:          ~1,200 lines (✅ 560 complete)
SDK integration:       ~450 lines (✅ 470 complete)
Rules (12 total):      ~1,400 lines (⚠️ 260 complete)
Enforcement:           ~200 lines (⚠️ 100 complete)
State management:      ~770 lines (❌ 0 complete)
CLI (admin + trader):  ~1,030 lines (❌ 0 complete)
Config system:         ~250 lines (⚠️ 80 complete)
Service wrapper:       ~300 lines (❌ 0 complete)
Utilities:             ~260 lines (❌ 0 complete)
API layer:             ~450 lines (❌ 0 complete)
Tests:                 ~2,000 lines (❌ 0 complete)

Total estimated:       ~8,310 lines
Current progress:      ~1,470 lines (~18%)
```

### Time Estimates
```
Config System:        1-2 days
Trader CLI:           2-3 days
Admin CLI:            3-4 days
State Persistence:    3-4 days
Enforcement System:   2-3 days
Rules (10 remaining): 5-7 days
Windows Service:      2-3 days
Testing Suite:        5-7 days
Documentation:        2-3 days

Total: 25-36 days (solo developer)
```

---

## 🗂️ File Size Targets (from spec)

**Architecture Constraint**: No file over 200 lines

### Current Compliance
- ✅ `suite_manager.py`: 220 lines (over limit)
- ✅ `manager.py`: 200 lines (at limit)
- ✅ All other files: Under 200 lines

### Action Items
- Consider splitting `suite_manager.py` into:
  - `suite_manager.py` (core logic)
  - `suite_health.py` (health monitoring)

---

## 💡 Key Architectural Notes

### Hybrid Architecture Decision
**Spec** (PROJECT_DOCS):
- Windows Service daemon
- Synchronous Python
- Direct TopstepX API
- Config-driven rules

**V34** (Current):
- Async Python daemon
- Project-X-Py SDK abstraction
- Programmatic rules
- Event-driven

**Solution**:
- Keep async core (better performance)
- Add Windows Service wrapper (production deployment)
- Support both programmatic + config-driven rules
- Use SDK but allow direct API access if needed

---

### CLI Design Considerations

**Two Separate Interfaces**:
1. **Admin CLI** (`risk-admin`)
   - Password protected
   - Full configuration access
   - Service control
   - Rule management

2. **Trader CLI** (`risk-status`)
   - No password
   - View-only
   - Real-time status
   - Lockout timers

**Implementation Approach**:
- Use `rich` for terminal UI (tables, colors)
- Use `typer` for CLI framework
- Real-time updates via daemon API
- Store admin password hash in `config/admin_password.hash`

---

### State Persistence Strategy

**SQLite Schema** (to be implemented):
```sql
-- Lockout states
CREATE TABLE lockouts (
    account_id TEXT PRIMARY KEY,
    reason TEXT NOT NULL,
    locked_until DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- P&L tracking
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
```

---

## 🚀 Next Implementation Session

### Quick Start Checklist
1. ✅ Understand current state (`CURRENT_STATE.md`)
2. ✅ Review project structure (this file)
3. ⏳ Read roadmap (`ROADMAP.md`)
4. ⏳ Pick next task
5. ⏳ Implement
6. ⏳ Test
7. ⏳ Update docs

### Suggested First Task
**Build Trader CLI - Status Viewer**
- File: `src/cli/trader/status_screen.py`
- Complexity: Medium
- Dependencies: None (reads from RiskManager)
- Impact: High (immediate visibility)
- Time: 2-3 hours

---

## 📖 Reference Documents

- **Vision**: `docs/PROJECT_DOCS/summary/project_overview.md`
- **Architecture**: `docs/PROJECT_DOCS/architecture/system_architecture_v2.md`
- **Rules**: `docs/PROJECT_DOCS/rules/*.md`
- **Modules**: `docs/PROJECT_DOCS/modules/*.md`
- **Current State**: `CURRENT_STATE.md`
- **Roadmap**: `ROADMAP.md`

---

**Last Updated**: 2025-10-23
**Next Update**: After CLI implementation
**Maintainer**: Update this file when adding new modules/files
