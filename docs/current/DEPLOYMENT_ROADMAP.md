# Risk Manager V34 - Deployment Roadmap
**Status**: Phase 1 Complete (MOD-002, MOD-003) - 95/95 Tests Passing ✅
**Goal**: 100% Production-Ready Trading Risk Management System
**Current Progress**: ~25% Complete

---

## 📊 Quick Status

| Component | Status | Tests | Priority |
|-----------|--------|-------|----------|
| **Phase 0**: Foundation | ✅ Complete | 42 tests | Foundation |
| **Phase 1**: State Management | ✅ Complete | 95 tests | CRITICAL |
| **Phase 2**: Reset & Rules | 🔄 Next | 0 tests | CRITICAL |
| **Phase 3**: Integration Tests | ❌ Pending | 0 tests | HIGH |
| **Phase 4**: CLIs | ❌ Pending | 0 tests | HIGH |
| **Phase 5**: Deployment | ❌ Pending | 0 tests | MEDIUM |

---

## ✅ Phase 1 Complete: State Management Foundation

**Duration**: 2 hours
**Test Results**: 95/95 passing (100%)
**Report**: `docs/current/PHASE1_COMPLETION_REPORT.md`

### What Was Built:

#### MOD-003: Timer Manager (276 lines, 22 tests)
**File**: `src/risk_manager/state/timer_manager.py`
**Purpose**: Countdown timers with callback execution

**Features**:
- ✅ Multiple concurrent timers
- ✅ Background task (1-second intervals)
- ✅ Async/sync callbacks
- ✅ Auto-cleanup
- ✅ Zero-duration support

#### MOD-002: Lockout Manager (497 lines, 31 tests)
**File**: `src/risk_manager/state/lockout_manager.py`
**Purpose**: Centralized account lockout management

**Features**:
- ✅ Hard lockouts (until specific datetime)
- ✅ Cooldown timers (duration-based)
- ✅ SQLite persistence (crash recovery)
- ✅ Background auto-expiry
- ✅ Timer Manager integration
- ✅ Multi-account support
- ✅ Timezone-aware datetime handling

### Bugs Fixed:
1. ✅ Timer Manager async/sync mismatch (3 tests)
2. ✅ Lockout Manager timezone handling (16 tests)
3. ✅ Test mocking parameter mismatches (3 tests)

---

## 🔄 Phase 2: Reset Scheduler & Risk Rules Implementation

**Priority**: CRITICAL
**Estimated Duration**: 3-5 hours
**Dependencies**: Phase 1 (✅ Complete)

### 2.1: MOD-004 Reset Scheduler

**File to Create**: `src/risk_manager/state/reset_scheduler.py`
**Lines**: ~200-300
**Tests to Write**: ~15-20 tests
**Priority**: CRITICAL (blocks 5 rules)

#### Purpose:
Automated daily/weekly reset system for P&L tracking, trade counters, and loss limits.

#### Public API:
```python
class ResetScheduler:
    async def start() -> None
    async def stop() -> None
    def schedule_daily_reset(account_id: int, reset_time: str) -> None  # "17:00 ET"
    def schedule_weekly_reset(account_id: int, day: str, reset_time: str) -> None
    def get_next_reset_time(account_id: int) -> datetime
    def trigger_reset_manually(account_id: int) -> None
```

#### Features Needed:
- ✅ Daily reset at 5:00 PM ET
- ✅ Weekly reset (configurable day)
- ✅ Timezone handling (ET ↔ UTC)
- ✅ Database persistence (reset_log table)
- ✅ Integration with PnL Tracker
- ✅ Integration with Trade Counter
- ✅ Background task (check every minute)

#### Test Categories:
1. Basic scheduling (daily, weekly)
2. Timezone conversion (ET ↔ UTC)
3. PnL reset integration
4. Trade counter reset
5. Database persistence
6. Edge cases (DST transitions, midnight)

#### Blocks These Rules:
- RULE-004: Daily Loss Limit
- RULE-005: Daily Profit Target
- RULE-007: Weekly Loss Limit
- RULE-009: Max Trades Per Day
- RULE-010: Trade Frequency Limit

---

### 2.2: Implement Missing Risk Rules

**Total Rules**: 13 total, 3 implemented, **10 remaining**

#### Priority 1: Account-Level Enforcement (CRITICAL)
These rules enforce TopstepX account violations and trigger lockouts.

##### RULE-004: Daily Loss Limit ⭐ CRITICAL
**File**: `src/risk_manager/rules/daily_loss_limit.py`
**Tests**: ~12 tests
**Blocks**: Account violations
**Priority**: HIGHEST

**Purpose**: Prevent daily loss exceeding TopstepX limit (e.g., -$500)
**Enforcement**: Flatten all positions + lockout until 5:00 PM ET reset
**Dependencies**: MOD-002 (Lockout), MOD-004 (Reset), PnL Tracker

**Test Scenarios**:
1. Loss approaching limit (warning)
2. Loss exceeds limit (flatten + lockout)
3. Lockout persists until reset
4. Multi-symbol tracking
5. Unrealized + realized P&L combined
6. Reset clears lockout at 5:00 PM ET

##### RULE-005: Daily Profit Target
**File**: `src/risk_manager/rules/daily_profit_target.py`
**Tests**: ~10 tests
**Priority**: HIGH

**Purpose**: Flatten at profit target (e.g., +$500) to preserve gains
**Enforcement**: Flatten all + lockout until reset
**Dependencies**: MOD-002, MOD-004, PnL Tracker

##### RULE-007: Weekly Loss Limit
**File**: `src/risk_manager/rules/weekly_loss_limit.py`
**Tests**: ~12 tests
**Priority**: HIGH

**Purpose**: Track cumulative weekly loss (e.g., -$1000)
**Enforcement**: Flatten all + lockout until Monday reset
**Dependencies**: MOD-002, MOD-004, PnL Tracker, Week tracking

##### RULE-009: Max Trades Per Day
**File**: `src/risk_manager/rules/max_trades_per_day.py`
**Tests**: ~10 tests
**Priority**: MEDIUM

**Purpose**: Limit trades per day (e.g., 10 trades)
**Enforcement**: Reject new orders + lockout until reset
**Dependencies**: MOD-002, MOD-004, Trade Counter

##### RULE-010: Trade Frequency Limit
**File**: `src/risk_manager/rules/trade_frequency_limit.py`
**Tests**: ~12 tests
**Priority**: MEDIUM

**Purpose**: Cooldown between trades (e.g., 30 minutes)
**Enforcement**: Reject orders + cooldown timer
**Dependencies**: MOD-002 (Cooldown), MOD-003 (Timer)

---

#### Priority 2: Market Hours & Sessions

##### RULE-006: Trading Hours
**File**: `src/risk_manager/rules/trading_hours.py`
**Tests**: ~10 tests
**Priority**: HIGH

**Purpose**: Enforce allowed trading hours (e.g., 9:30 AM - 4:00 PM ET)
**Enforcement**: Reject orders + flatten at session end
**Dependencies**: Timezone handling, Session scheduler

##### RULE-011: Session Block
**File**: `src/risk_manager/rules/session_block.py`
**Tests**: ~8 tests
**Priority**: MEDIUM

**Purpose**: Block trading during specific sessions (e.g., overnight)
**Enforcement**: Reject all orders + lockout during session
**Dependencies**: MOD-002 (Lockout), Session tracking

---

#### Priority 3: Advanced Constraints

##### RULE-008: Max Drawdown
**File**: `src/risk_manager/rules/max_drawdown.py`
**Tests**: ~12 tests
**Priority**: MEDIUM

**Purpose**: Track drawdown from daily high water mark
**Enforcement**: Flatten all + lockout if drawdown > threshold
**Dependencies**: PnL Tracker (high water mark tracking), MOD-002

##### RULE-012: Trailing Stop
**File**: `src/risk_manager/rules/trailing_stop.py`
**Tests**: ~10 tests
**Priority**: LOW

**Purpose**: Auto-flatten when profit retraces from peak
**Enforcement**: Flatten all when retrace exceeds threshold
**Dependencies**: PnL Tracker (peak tracking)

##### RULE-013: Max Exposure
**File**: `src/risk_manager/rules/max_exposure.py`
**Tests**: ~10 tests
**Priority**: LOW

**Purpose**: Limit total dollar exposure across all positions
**Enforcement**: Reject orders exceeding exposure limit
**Dependencies**: Position tracking, Contract value calculation

---

### Phase 2 Summary

**Deliverables**:
- ✅ 1 Module: MOD-004 Reset Scheduler (~250 lines, 18 tests)
- ✅ 10 Risk Rules (~2000 lines, ~106 tests)
- ✅ Database migrations (reset_log table, trade_counter table)

**Total Work**:
- Implementation: ~2,250 lines
- Tests: ~124 tests
- Estimated Time: 12-15 hours (can parallelize with agents)

**Test Target**: 95 → 219 tests passing

---

## 🧪 Phase 3: Integration Testing

**Priority**: HIGH
**Estimated Duration**: 2-3 hours
**Dependencies**: Phase 2 complete

### Integration Test Suites:

#### 3.1: State Module Integration (HIGH)
**File**: `tests/integration/test_state_integration.py`
**Tests**: ~15 tests

**Scenarios**:
1. Lockout Manager + Timer Manager (cooldowns auto-clear)
2. Lockout Manager + Database (crash recovery)
3. Reset Scheduler + PnL Tracker (daily reset)
4. Reset Scheduler + Lockout Manager (reset clears lockout)
5. All state modules together (full lifecycle)

#### 3.2: Rule Enforcement Integration (CRITICAL)
**File**: `tests/integration/test_rule_enforcement.py`
**Tests**: ~20 tests

**Scenarios**:
1. Daily loss limit → Flatten all → Lockout
2. Max contracts → Reject order
3. Cooldown timer → Reject order during cooldown
4. Multiple rules triggered simultaneously
5. Reset clears lockouts and counters

#### 3.3: SDK Integration (CRITICAL)
**File**: `tests/integration/test_sdk_live.py`
**Tests**: ~10 tests

**Scenarios**:
1. Connect to TopstepX SDK
2. Subscribe to position events
3. Receive real-time quotes
4. Place test order (if allowed)
5. Flatten position via SDK
6. Disconnect gracefully

**Note**: These tests run against TopstepX Paper Trading API

#### 3.4: Multi-Account Integration
**File**: `tests/integration/test_multi_account.py`
**Tests**: ~8 tests

**Scenarios**:
1. Two accounts with different lockouts
2. One account locked, other active
3. Reset affects only target account
4. Database persists all accounts

---

### Phase 3 Summary

**Deliverables**:
- ✅ 4 Integration test suites (~53 tests)
- ✅ SDK connection validation
- ✅ Multi-account validation
- ✅ Full system integration validation

**Total Work**:
- Tests: ~53 integration tests
- Estimated Time: 8-10 hours

**Test Target**: 219 → 272 tests passing

---

## 🖥️ Phase 4: CLI Systems

**Priority**: HIGH
**Estimated Duration**: 4-6 hours
**Dependencies**: Phase 3 complete

### 4.1: Trader CLI (View-Only)

**File**: `src/cli/trader_cli.py`
**Lines**: ~400 lines
**Tests**: ~10 tests
**Priority**: HIGH

#### Features:
- ✅ Real-time status display (updates every 1s)
- ✅ Current positions & P&L
- ✅ Active rules display (green/yellow/red status)
- ✅ Lockout timers (countdown if locked)
- ✅ Recent enforcement log (last 10 actions)
- ✅ Color-coded alerts
- ✅ No password required (read-only)

#### UI Mockup:
```
┌──────────────────────────────────────────────────────────┐
│ Risk Manager V34 - Trader Status                        │
├──────────────────────────────────────────────────────────┤
│ Account: PRAC-V2-126244                                 │
│ Status: ✅ ACTIVE  │  Lockout: ❌ None                  │
│ Daily P&L: +$245.00 │ Unrealized: +$50.00              │
├──────────────────────────────────────────────────────────┤
│ Active Positions:                                        │
│   MNQ: +2 @ 20,125.00 (+$50.00)                        │
│                                                          │
│ Active Rules:                                            │
│   ✅ Max Contracts: 2/5                                  │
│   ✅ Daily Loss: +$245 / -$500                          │
│   ⚠️  Trade Frequency: 8/10 per hour                    │
│                                                          │
│ Recent Enforcement:                                      │
│   [14:23:15] No action needed                           │
│                                                          │
│ Press 'r' refresh | 'q' quit                            │
└──────────────────────────────────────────────────────────┘
```

---

### 4.2: Admin CLI (Password-Protected)

**File**: `src/cli/admin_cli.py`
**Lines**: ~600 lines
**Tests**: ~12 tests
**Priority**: HIGH

#### Features:
- ✅ Windows UAC authentication (admin rights required)
- ✅ Interactive rule configuration wizard
- ✅ Account/API key management
- ✅ Service start/stop/restart
- ✅ View/edit YAML configs
- ✅ Config validation before save
- ✅ Manual lockout clear
- ✅ Manual reset trigger

#### Commands:
```bash
# Requires Windows admin elevation
risk-admin

Commands:
1. Configure Risk Rules
2. Manage Accounts
3. Service Control (start/stop/restart)
4. Clear Lockout (emergency)
5. Trigger Reset (manual)
6. View Logs
7. Exit
```

---

### Phase 4 Summary

**Deliverables**:
- ✅ Trader CLI (~400 lines, 10 tests)
- ✅ Admin CLI (~600 lines, 12 tests)
- ✅ CLI entry points
- ✅ Windows UAC integration

**Total Work**:
- Implementation: ~1,000 lines
- Tests: ~22 tests
- Estimated Time: 12-16 hours

**Test Target**: 272 → 294 tests passing

---

## 🚀 Phase 5: Windows Service Deployment

**Priority**: MEDIUM
**Estimated Duration**: 2-3 hours
**Dependencies**: Phase 4 complete

### 5.1: Windows Service Wrapper

**File**: `src/service/windows_service.py`
**Lines**: ~300 lines
**Priority**: HIGH

#### Features:
- ✅ Auto-start with Windows
- ✅ Run as LocalSystem (highest privilege)
- ✅ Crash recovery (auto-restart)
- ✅ Service logging
- ✅ Graceful shutdown
- ✅ Status reporting

#### Installation:
```bash
# Requires admin elevation
python -m risk_manager install-service
sc start RiskManagerV34
```

---

### 5.2: UAC/ACL Security

**File**: `src/service/security.py`
**Lines**: ~200 lines
**Priority**: HIGH

#### Features:
- ✅ Trader CANNOT kill service (no admin rights)
- ✅ Config files protected (ACL permissions)
- ✅ Database protected (read-only for trader)
- ✅ Logs protected (trader can view, not delete)
- ✅ Admin CLI requires elevation
- ✅ Service control requires elevation

#### Protection Mechanisms:
1. Service runs as LocalSystem (unkillable by trader)
2. Config files: Admin read/write, Trader read-only
3. Database: Admin read/write, Trader no access
4. Logs: Admin read/write, Trader read-only

---

### 5.3: Installation Scripts

**Files**:
- `scripts/install_windows.ps1` (PowerShell installer)
- `scripts/uninstall_windows.ps1` (Uninstaller)
- `scripts/check_installation.ps1` (Validation)

#### Features:
- ✅ One-click installation
- ✅ Dependency check (Python 3.12+)
- ✅ Virtual environment setup
- ✅ Service registration
- ✅ ACL configuration
- ✅ Initial config generation
- ✅ Test connection to TopstepX

---

### Phase 5 Summary

**Deliverables**:
- ✅ Windows Service wrapper (~300 lines)
- ✅ UAC/ACL security (~200 lines)
- ✅ Installation scripts (3 PowerShell scripts)
- ✅ Deployment documentation

**Total Work**:
- Implementation: ~500 lines
- Scripts: ~400 lines PowerShell
- Estimated Time: 8-10 hours

---

## 📊 Final Metrics

### Code Metrics:
| Component | Lines | Tests | Status |
|-----------|-------|-------|--------|
| Phase 0: Foundation | ~2,000 | 42 | ✅ Complete |
| Phase 1: State Mgmt | ~773 | 53 | ✅ Complete |
| Phase 2: Rules | ~2,250 | 124 | ❌ Pending |
| Phase 3: Integration | ~0 | 53 | ❌ Pending |
| Phase 4: CLIs | ~1,000 | 22 | ❌ Pending |
| Phase 5: Deployment | ~900 | 0 | ❌ Pending |
| **TOTAL** | **~6,923** | **294** | **25% Done** |

### Time Estimates:
| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1 | 2 hours | ✅ Complete |
| Phase 2 | 12-15 hours | 🔄 Next |
| Phase 3 | 8-10 hours | ❌ Pending |
| Phase 4 | 12-16 hours | ❌ Pending |
| Phase 5 | 8-10 hours | ❌ Pending |
| **TOTAL** | **42-53 hours** | **5% Done** |

---

## 🎯 Deployment Checklist

### ✅ Phase 1 Complete:
- [x] 95/95 tests passing
- [x] MOD-002 Lockout Manager implemented
- [x] MOD-003 Timer Manager implemented
- [x] Database persistence working
- [x] Timezone handling correct
- [x] Background tasks working

### 🔄 Phase 2 Next:
- [ ] MOD-004 Reset Scheduler implemented
- [ ] 10 risk rules implemented
- [ ] 124 new tests passing
- [ ] Database migrations complete
- [ ] Integration with existing modules verified

### ❌ Remaining:
- [ ] 53 integration tests passing
- [ ] SDK live connection validated
- [ ] Trader CLI functional
- [ ] Admin CLI functional
- [ ] Windows Service deployed
- [ ] UAC/ACL security enforced
- [ ] Installation scripts tested

---

## 🚦 Next Steps for Agents

**See**: `docs/current/NEXT_STEPS.md` for detailed agent instructions

**Phase 2 Agent Swarm**:
1. **Agent 1**: Implement MOD-004 Reset Scheduler
2. **Agent 2-5**: Implement Priority 1 rules (RULE-004, 005, 007, 009)
3. **Agent 6**: Quality Enforcer (review all implementations)
4. **Agent 7**: Integration Validator (test MOD-004 + rules)

**Estimated Completion**: 12-15 hours with 4-5 parallel agents

---

**Last Updated**: 2025-10-27
**Next Review**: After Phase 2 completion
**Status**: ✅ Phase 1 Complete, 🔄 Phase 2 Ready to Start
