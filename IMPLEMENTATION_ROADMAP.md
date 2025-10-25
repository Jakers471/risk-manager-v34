# Risk Manager V34 - Implementation Roadmap

**🎯 CENTRAL PROGRESS TRACKER - UPDATE THIS AS YOU BUILD**

**Last Updated**: 2025-10-25
**Overall Progress**: 30% (26 of 88 features)
**Next Priority**: Phase 1 - State Managers

---

## ⚠️ HOW TO USE THIS DOCUMENT

**For AI Agents**:
1. Read `AGENT_GUIDELINES.md` first
2. Check "Next Priority" phase below
3. Pick unchecked [ ] item to work on
4. Read referenced specs (paths provided)
5. Build the feature
6. Update checkbox to [x] when complete
7. Update "Last Updated" timestamp above
8. Commit with message: "Implemented [feature-name]"

**For Developers**:
- This is your single source of truth for what needs building
- All details are in `docs/specifications/unified/` - this just tracks progress
- Update checkboxes as you complete work

**For Test Integration**:
- Run tests: `python run_tests.py`
- Results auto-save to: `test_reports/latest.txt`
- Agents can read test results from that file

---

## 📊 Progress Summary

| Phase | Status | Items | Complete | Progress |
|-------|--------|-------|----------|----------|
| **Phase 1: State Managers** | 🔴 Blocked | 3 | 0/3 | 0% |
| **Phase 2: Risk Rules** | 🔴 Blocked | 13 | 3/13 | 23% |
| **Phase 3: SDK Integration** | 🟡 Partial | 4 | 2/4 | 50% |
| **Phase 4: CLI System** | 🔴 Not Started | 13 | 0/13 | 0% |
| **Phase 5: Configuration** | 🟡 Partial | 4 | 1/4 | 25% |
| **Phase 6: Windows Service** | 🔴 Not Started | 5 | 0/5 | 0% |
| **Phase 7: Infrastructure** | 🟡 Partial | 6 | 2/6 | 33% |
| **Phase 8: Testing** | 🟡 Partial | 4 | 1/4 | 25% |

---

## 🚀 PHASE 1: State Managers (CRITICAL - BLOCKS 8 RULES)

**Status**: 🔴 Not Started
**Blockers**: None - can start immediately
**Estimated Effort**: 3.5 weeks

### MOD-003: Timer Manager (1 week)
**Priority**: CRITICAL (blocks MOD-002 and 4 rules)

- [ ] **Create `src/risk_manager/state/timer_manager.py`**
  - Spec: `docs/specifications/unified/architecture/MODULES_SUMMARY.md` (MOD-003)
  - Contract: `CONTRACTS_REFERENCE.md` (TimerManager API)
  - Implements: Session timers, countdown timers, schedule checking
  - Tests: 20 unit tests, 5 integration tests

- [ ] **Implement database schema for timers**
  - Schema: `docs/specifications/unified/architecture/MODULES_SUMMARY.md` (MOD-003 Database Schema)
  - Tables: `timers`, `timer_events`

- [ ] **Add timer configuration support**
  - Config: `docs/specifications/unified/configuration/timers-config-schema.md`
  - Load from `config/timers.yaml`

- [ ] **Write unit tests for TimerManager**
  - Test guide: `docs/specifications/unified/testing-strategy.md`
  - Target: 20 tests, 90%+ coverage
  - Run: `python run_tests.py` → [2] Unit tests

---

### MOD-002: Lockout Manager (1.5 weeks)
**Priority**: CRITICAL (blocks 7 rules - 54% of all rules)
**Dependencies**: MOD-003 (Timer Manager)

- [ ] **Create `src/risk_manager/state/lockout_manager.py`**
  - Spec: `docs/specifications/unified/architecture/MODULES_SUMMARY.md` (MOD-002)
  - Contract: `CONTRACTS_REFERENCE.md` (LockoutManager API)
  - Implements: Account locking, countdown timers, violation tracking
  - Tests: 25 unit tests, 8 integration tests

- [ ] **Implement database schema for lockouts**
  - Schema: `docs/specifications/unified/architecture/MODULES_SUMMARY.md` (MOD-002 Database Schema)
  - Tables: `lockouts`, `violation_history`

- [ ] **Integrate with TimerManager**
  - Timer integration: `docs/specifications/unified/architecture/MODULES_SUMMARY.md` (MOD-002 Dependencies)
  - Lockout countdown timers

- [ ] **Implement lockout enforcement logic**
  - On new trade event → check if locked → close immediately
  - Spec: `docs/specifications/unified/rules/RULE-003-daily-realized-loss.md` (Enforcement Action)

- [ ] **Write unit tests for LockoutManager**
  - Test guide: `docs/specifications/unified/testing-strategy.md`
  - Target: 25 tests, 90%+ coverage

---

### MOD-004: Reset Scheduler (1 week)
**Priority**: HIGH (blocks 5 rules)
**Dependencies**: MOD-003 (Timer Manager)

- [ ] **Create `src/risk_manager/state/reset_scheduler.py`**
  - Spec: `docs/specifications/unified/architecture/MODULES_SUMMARY.md` (MOD-004)
  - Contract: `CONTRACTS_REFERENCE.md` (ResetScheduler API)
  - Implements: Daily reset at configured time, timezone handling
  - Tests: 15 unit tests, 6 integration tests

- [ ] **Implement daily reset job**
  - Scheduler: APScheduler or Windows Task Scheduler
  - Config: `docs/specifications/unified/configuration/timers-config-schema.md` (daily_reset)
  - Reset: PnL, trade counts, violation counters

- [ ] **Integrate with PnL Tracker**
  - Reset realized/unrealized PnL at configured time
  - Clear daily metrics from database

- [ ] **Write unit tests for ResetScheduler**
  - Test guide: `docs/specifications/unified/testing-strategy.md`
  - Target: 15 tests, 90%+ coverage

---

## 🎯 PHASE 2: Risk Rules (CORE FUNCTIONALITY)

**Status**: 🟡 Partial (3 of 13 implemented)
**Blockers**: Phase 1 (state managers)
**Estimated Effort**: 4-5 weeks

### ✅ Completed Rules (DO NOT MODIFY)

- [x] **RULE-001: Max Contracts** (Implemented)
  - File: `src/risk_manager/rules/max_contracts.py`
  - Tests: Passing

- [x] **RULE-002: Max Contracts Per Instrument** (Implemented)
  - File: `src/risk_manager/rules/max_contracts_per_instrument.py`
  - Tests: Passing

- [x] **RULE-012: Trade Management** (Implemented)
  - File: `src/risk_manager/rules/` (check which file)
  - Tests: Passing

---

### RULE-003: Daily Realized Loss (HARD LOCKOUT)
**Priority**: CRITICAL
**Dependencies**: MOD-002 (Lockout), MOD-003 (Timer), MOD-004 (Reset)

- [ ] **Create `src/risk_manager/rules/daily_realized_loss.py`**
  - Spec: `docs/specifications/unified/rules/RULE-003-daily-realized-loss.md`
  - Contract: `CONTRACTS_REFERENCE.md` (RiskRule base class)
  - Enforcement: **HARD LOCKOUT** - Close ALL positions, timer-based unlock
  - Config: `docs/specifications/unified/configuration/risk-config-schema.md` (daily_realized_loss)

- [ ] **Implement trigger logic**
  - Formula: `realized_pnl + unrealized_pnl <= -limit`
  - Event: Subscribe to `TRADE_EXECUTED`, `POSITION_UPDATED`
  - Check on every trade execution

- [ ] **Implement enforcement action**
  - Close ALL positions account-wide (call SDK TradingIntegration)
  - Trigger lockout via LockoutManager
  - Lockout until timer (configured reset time)

- [ ] **Write unit tests**
  - Test guide: `docs/specifications/unified/rules/RULE-003-daily-realized-loss.md` (Test Coverage)
  - Target: 15 tests
  - Scenarios: Trigger, enforcement, timer unlock, edge cases

- [ ] **Write integration tests**
  - Real SDK connection
  - Verify positions close
  - Verify lockout activates

---

### RULE-004: Daily Unrealized Loss (TRADE-BY-TRADE)
**Priority**: HIGH
**Dependencies**: Quote data integration (SDK QuoteManager)

- [ ] **Create `src/risk_manager/rules/daily_unrealized_loss.py`**
  - Spec: `docs/specifications/unified/rules/RULE-004-daily-unrealized-loss.md`
  - Contract: `CONTRACTS_REFERENCE.md` (RiskRule base class)
  - Enforcement: **TRADE-BY-TRADE** - Close ONLY that position
  - Config: `docs/specifications/unified/configuration/risk-config-schema.md` (daily_unrealized_loss)

- [ ] **Implement quote data integration**
  - Spec: `docs/specifications/unified/quote-data-integration.md`
  - Subscribe to `QUOTE_UPDATED` events
  - Calculate unrealized PnL: `(current_price - entry_price) * contracts * multiplier`

- [ ] **Implement trigger logic**
  - Formula: `unrealized_pnl <= -limit` for that specific position
  - Event: Subscribe to `QUOTE_UPDATED`
  - Check on every quote update (throttled)

- [ ] **Implement enforcement action**
  - Close ONLY the losing position (specific symbol/contract)
  - NO lockout, NO timer
  - Trader can continue trading

- [ ] **Write unit tests**
  - Test guide: `docs/specifications/unified/rules/RULE-004-daily-unrealized-loss.md` (Test Coverage)
  - Target: 12 tests
  - Scenarios: Trigger, enforcement, quote throttling, edge cases

---

### RULE-005: Max Unrealized Profit (TRADE-BY-TRADE)
**Priority**: MEDIUM
**Dependencies**: Quote data integration (SDK QuoteManager)

- [ ] **Create `src/risk_manager/rules/max_unrealized_profit.py`**
  - Spec: `docs/specifications/unified/rules/RULE-005-max-unrealized-profit.md`
  - Contract: `CONTRACTS_REFERENCE.md` (RiskRule base class)
  - Enforcement: **TRADE-BY-TRADE** - Close ONLY that position
  - Config: `docs/specifications/unified/configuration/risk-config-schema.md` (max_unrealized_profit)

- [ ] **Implement trigger logic**
  - Formula: `unrealized_pnl >= +limit` for that specific position
  - Event: Subscribe to `QUOTE_UPDATED`
  - Check on every quote update (throttled)

- [ ] **Implement enforcement action**
  - Close ONLY the winning position (take profit)
  - NO lockout, NO timer
  - Trader can continue trading

- [ ] **Write unit tests**
  - Test guide: `docs/specifications/unified/rules/RULE-005-max-unrealized-profit.md` (Test Coverage)
  - Target: 12 tests

---

### RULE-006 through RULE-013
**See Wave 2 Gap Analysis for complete breakdown:**
- `docs/analysis/wave2-gap-analysis/01-RISK-RULES-GAPS.md`

**Unified Specs:**
- `docs/specifications/unified/rules/RULE-006-trade-frequency-limit.md`
- `docs/specifications/unified/rules/RULE-007-cooldown-after-loss.md`
- `docs/specifications/unified/rules/RULE-008-no-stop-loss-grace.md`
- `docs/specifications/unified/rules/RULE-009-session-block-outside.md`
- `docs/specifications/unified/rules/RULE-010-auth-loss-guard.md`
- `docs/specifications/unified/rules/RULE-011-symbol-blocks.md`
- `docs/specifications/unified/rules/RULE-013-daily-realized-profit.md`

**Checkboxes** (add as you implement):
- [ ] RULE-006
- [ ] RULE-007
- [ ] RULE-008
- [ ] RULE-009
- [ ] RULE-010
- [ ] RULE-011
- [ ] RULE-013

---

## 🔌 PHASE 3: SDK Integration

**Status**: 🟡 Partial (2 of 4)
**Estimated Effort**: 2 weeks

### ✅ Completed

- [x] **SuiteManager** (Implemented)
  - File: `src/risk_manager/sdk/suite_manager.py`

- [x] **EventBridge** (Implemented)
  - File: `src/risk_manager/sdk/event_bridge.py`

---

### Quote Data Integration (NEW - BLOCKS RULE-004, RULE-005)
**Priority**: HIGH

- [ ] **Implement quote subscription in EventBridge**
  - Spec: `docs/specifications/unified/quote-data-integration.md`
  - Subscribe to SDK QuoteManager events
  - Emit `QUOTE_UPDATED` risk events

- [ ] **Implement quote throttling**
  - Spec: `docs/specifications/unified/quote-data-integration.md` (Quote Event Throttling)
  - Throttle to 1 update/second per symbol
  - 99% load reduction

- [ ] **Implement UnrealizedPnLCalculator**
  - Spec: `docs/specifications/unified/quote-data-integration.md` (Unrealized P&L Calculation)
  - Calculate: `(current_price - entry_price) * contracts * multiplier`
  - Contract multipliers: MNQ=$2, ES=$50, etc.

- [ ] **Integrate with PnLTracker**
  - Add `update_unrealized_pnl()` method
  - Add `get_unrealized_pnl()` method
  - Persist to database

---

### Enforcement Integration
**Priority**: MEDIUM

- [ ] **Complete enforcement.py**
  - Spec: `docs/specifications/unified/architecture/MODULES_SUMMARY.md` (Enforcement Actions)
  - Current: 70% complete
  - Missing: Lockout enforcement, timer-based unlock

---

## 🖥️ PHASE 4: CLI System

**Status**: 🔴 Not Started (0%)
**Blockers**: State managers (for admin to view/edit)
**Estimated Effort**: 5 weeks

### Admin CLI (6 commands)
**Spec**: `docs/specifications/unified/admin-cli-reference.md`

- [ ] **Create CLI framework** (`src/risk_manager/cli/`)
  - Typer + Rich (already in dependencies)
  - UAC elevation check

- [ ] **Implement: `risk-manager admin config view`**
- [ ] **Implement: `risk-manager admin config set`**
- [ ] **Implement: `risk-manager admin daemon start`**
- [ ] **Implement: `risk-manager admin daemon stop`**
- [ ] **Implement: `risk-manager admin daemon restart`**
- [ ] **Implement: `risk-manager admin daemon status`**

---

### Trader CLI (7 commands)
**Spec**: `docs/specifications/unified/trader-cli-reference.md`

- [ ] **Implement: `risk-manager trader status`**
  - Show: Live P&L, positions, lockout status
  - Contract: `CONTRACTS_REFERENCE.md` (Trader CLI Data)

- [ ] **Implement: `risk-manager trader pnl`**
  - Show: Realized + Unrealized breakdown

- [ ] **Implement: `risk-manager trader logs`**
  - Show: Enforcement logs (which rule breached, why)

- [ ] **Implement: `risk-manager trader lockouts`**
  - Show: Lockout status, countdown timer

- [ ] **Implement: `risk-manager trader clock-in`**
- [ ] **Implement: `risk-manager trader clock-out`**
- [ ] **Implement: `risk-manager trader market-hours`**

---

### CLI Security
**Spec**: `docs/specifications/unified/cli-security-model.md`

- [ ] **Implement UAC elevation check**
  - Admin CLI requires elevation
  - Trader CLI runs as normal user

- [ ] **Implement Windows ACL protection**
  - Config files admin-only write
  - Trader CLI read-only database access

---

## ⚙️ PHASE 5: Configuration System

**Status**: 🟡 Partial (1 of 4)
**Estimated Effort**: 2 weeks

### ✅ Completed

- [x] **Basic Pydantic models** (Implemented)
  - File: `src/risk_manager/core/config.py`

---

### YAML Loader
**Priority**: HIGH

- [ ] **Implement nested Pydantic models for 13 rules**
  - Spec: `docs/specifications/unified/configuration/risk-config-schema.md`
  - Load from `config/risk_config.yaml`

- [ ] **Implement multi-file loading**
  - Load: risk_config.yaml, accounts.yaml, timers.yaml, api_config.yaml
  - Spec: `docs/specifications/unified/configuration/README.md`

---

### Configuration Validator
**Priority**: HIGH

- [ ] **Add Pydantic validators**
  - Spec: `docs/specifications/unified/configuration/config-validation.md`
  - Validate: ranges, formats, cross-rule conflicts

---

### Hot-Reload System
**Priority**: MEDIUM

- [ ] **Implement file watcher**
  - Spec: `docs/specifications/unified/configuration/README.md` (Hot-Reload)
  - Watch config files for changes
  - Reload daemon on change

---

## 🪟 PHASE 6: Windows Service

**Status**: 🔴 Not Started (0%)
**Blockers**: None (can start in parallel)
**Estimated Effort**: 2-3 weeks

**Spec**: `docs/specifications/unified/architecture/daemon-lifecycle.md`

- [ ] **Add pywin32 dependency**
  - Add to `pyproject.toml`

- [ ] **Create Windows Service wrapper**
  - File: `src/risk_manager/service/windows_service.py`
  - Spec: `docs/analysis/wave2-gap-analysis/05-DEPLOYMENT-GAPS.md` (Service Wrapper)

- [ ] **Implement service installer**
  - Install as LocalSystem
  - Auto-start on boot

- [ ] **Implement graceful shutdown**
  - Clean async event loop shutdown
  - Persist state before exit

- [ ] **Test auto-restart on reboot**
  - Verify daemon resumes monitoring

---

## 🛠️ PHASE 7: Infrastructure

**Status**: 🟡 Partial (2 of 6)
**Estimated Effort**: 3 weeks

### ✅ Completed

- [x] **8-Checkpoint Logging** (Implemented)
  - Files: `manager.py`, `engine.py`, `enforcement.py`
  - All 8 checkpoints present

- [x] **Basic Error Handling** (Implemented)
  - Try/except in place

---

### Date/Time Utilities (CRITICAL - BLOCKS DAILY RESET)
**Priority**: CRITICAL

- [ ] **Create `src/risk_manager/utils/datetime_utils.py`**
  - Spec: `docs/analysis/wave2-gap-analysis/07-INFRASTRUCTURE-GAPS.md` (Date/Time Utilities)
  - Functions: `get_midnight_et()`, `convert_to_et()`, `is_trading_hours()`

---

### Monitoring & Metrics
**Priority**: MEDIUM

- [ ] **Implement system health monitoring**
  - Spec: `docs/analysis/wave2-gap-analysis/07-INFRASTRUCTURE-GAPS.md` (Monitoring)
  - Track: uptime, event throughput, rule latency

- [ ] **Implement business metrics**
  - Track: violations/day, enforcements, P&L

---

### Error Recovery
**Priority**: MEDIUM

- [ ] **Implement retry decorator**
  - Exponential backoff for SDK calls

- [ ] **Implement circuit breaker**
  - Stop retrying after N failures

---

## 🧪 PHASE 8: Testing

**Status**: 🟡 Partial (1 of 4)
**Current**: 93 tests, 88 passing (94.6%), 18% coverage
**Target**: 90%+ coverage, all passing
**Estimated Effort**: 6 weeks

### ✅ Completed

- [x] **Interactive test runner** (Implemented)
  - File: `run_tests.py`
  - Menu: 20+ options

---

### Fix Failing Tests (IMMEDIATE)
**Priority**: CRITICAL

- [ ] **Fix 5 failing runtime tests**
  - Spec: `docs/analysis/wave2-gap-analysis/06-TESTING-GAPS.md` (Failing Tests)
  - Effort: 1 day
  - Tests: Missing `await`, missing `db_path` args

---

### Unit Tests (Need 97 more)
**Priority**: HIGH

- [ ] **Add unit tests for risk rules**
  - Target: 35 tests
  - Coverage: RULE-003, RULE-004, RULE-005, etc.

- [ ] **Add unit tests for state managers**
  - Target: 45 tests
  - Coverage: LockoutManager, TimerManager, ResetScheduler

- [ ] **Add unit tests for SDK integration**
  - Target: 17 tests
  - Coverage: EventBridge, quote integration

---

### Integration Tests (Need 29-38)
**Priority**: HIGH

- [ ] **Create integration test structure**
  - Directory: `tests/integration/`
  - Fixtures: Real SDK connection

- [ ] **Add SDK integration tests**
  - Test: Event subscription, quote data, enforcement

- [ ] **Add state persistence tests**
  - Test: Database CRUD, lockout persistence

---

### E2E Tests (Need 8-13)
**Priority**: MEDIUM

- [ ] **Create E2E test structure**
  - Directory: `tests/e2e/`

- [ ] **Add full violation flow test**
  - Test: Trade → Breach → Enforcement → SDK close

- [ ] **Add daily reset flow test**
  - Test: Midnight → Reset → P&L cleared

---

## 📋 Deployment Readiness Checklist

**Target**: Production-ready system

### Security ☐ Not Ready
- [ ] Windows Service running as LocalSystem
- [ ] UAC protection verified (trader can't kill daemon)
- [ ] Config files protected by ACL
- [ ] Admin CLI requires elevation
- [ ] Trader CLI read-only

### Testing ☐ Not Ready (18% coverage)
- [ ] All unit tests passing (need 97 more)
- [ ] All integration tests passing (need 29-38)
- [ ] All E2E tests passing (need 8-13)
- [ ] 90%+ code coverage (currently 18%)
- [ ] Smoke test passing (exit code 0)

### Features ☐ 30% Complete
- [ ] All 13 rules implemented (currently 3/13)
- [ ] All 4 state managers implemented (currently 2/4)
- [ ] CLI system functional (currently 0%)
- [ ] Windows Service deployed (currently 0%)
- [ ] Quote data integration (currently 0%)

### Performance ☐ Not Tested
- [ ] Handle 1000+ events/sec
- [ ] Quote throttling effective
- [ ] Rule evaluation <10ms
- [ ] Database queries <5ms

---

## 📖 Key References

**For Agents**:
- `AGENT_GUIDELINES.md` - How to use this roadmap
- `CONTRACTS_REFERENCE.md` - All API contracts and interfaces

**Specifications**:
- `docs/specifications/unified/` - All detailed specs (AUTHORITATIVE)

**Analysis**:
- `docs/analysis/wave2-gap-analysis/` - Gap analysis (what's missing)
- `docs/analysis/wave3-spec-consolidation/` - Conflict resolutions

**Testing**:
- `test_reports/latest.txt` - Most recent test results
- `python run_tests.py` - Interactive test menu

---

**🎯 NEXT ACTION**: Implement MOD-003 (Timer Manager) - No blockers, can start now!

---

**Last Updated**: 2025-10-25
**Update Frequency**: After every feature completion
**Maintained By**: AI agents + developers
