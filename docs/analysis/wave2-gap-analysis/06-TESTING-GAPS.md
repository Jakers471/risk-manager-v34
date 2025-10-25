# Wave 2 Gap Analysis: Testing Infrastructure

**Researcher**: RESEARCHER 6 - Testing Infrastructure Gap Analyst
**Date**: 2025-10-25
**Purpose**: Comprehensive analysis of testing gaps, failing tests, and testing roadmap

---

## Executive Summary

The Risk Manager V34 project has a sophisticated testing infrastructure with **93 total tests**, but significant gaps remain that block production deployment. The system shows **94.6% passing rate** (88 passing, 5 failing), but lacks critical integration and E2E test coverage.

### Critical Findings

- ✅ **Passing**: 88 tests (94.6%)
- ❌ **Failing**: 5 tests (5.4%)
- ❌ **Integration tests**: 0 (directory doesn't exist)
- ❌ **E2E tests**: 0 (directory doesn't exist)
- ✅ **Runtime validation**: Complete (70 tests)
- ⚠️ **Code coverage**: 18.27% overall (only state & events well-covered)
- ✅ **Test infrastructure**: Excellent (interactive runner, auto-reports, 8-checkpoint logging)

### Key Blocker

**Cannot deploy to production** with:
1. 5 failing tests (Database initialization issues + EventBus async misuse)
2. No integration tests (can't validate SDK integration)
3. No E2E tests (can't validate full workflows)
4. 18% code coverage (rules & enforcement untested)

---

## Test Suite Breakdown

### Current Test Status (93 Tests Total)

| Type | Directory | Count | Passing | Failing | Coverage | Status |
|------|-----------|-------|---------|---------|----------|--------|
| **Unit Tests** | `tests/unit/` | 23 | 23 | 0 | Good | ✅ 100% passing |
| **Runtime Tests** | `tests/runtime/` | 70 | 65 | 5 | Complete | ⚠️ 92.9% passing |
| **Integration Tests** | `tests/integration/` | 0 | 0 | 0 | None | ❌ Missing |
| **E2E Tests** | `tests/e2e/` | 0 | 0 | 0 | None | ❌ Missing |
| **TOTAL** | | **93** | **88** | **5** | **Partial** | ⚠️ **94.6% passing** |

### Test Distribution

```
Unit Tests (23 tests) - 24.7% of total
├── test_core/
│   ├── test_events.py (7 tests) ✅ All passing
│   └── test_enforcement_wiring.py (4 tests) ✅ All passing
└── test_state/
    └── test_pnl_tracker.py (12 tests) ✅ All passing

Runtime Tests (70 tests) - 75.3% of total
├── test_async_debug.py (14 tests) ✅ All passing
├── test_dry_run.py (14 tests) ⚠️ 2 failing
├── test_heartbeat.py (15 tests) ✅ All passing
├── test_post_conditions.py (14 tests) ⚠️ 1 failing
└── test_smoke.py (13 tests) ⚠️ 2 failing

Integration Tests (0 tests) - 0%
└── (directory doesn't exist)

E2E Tests (0 tests) - 0%
└── (directory doesn't exist)
```

---

## Failing Tests Analysis

### Test 1: `test_dry_run_pnl_calculation`

**Location**: `tests/runtime/test_dry_run.py::test_dry_run_pnl_calculation`

**What it tests**: P&L calculation in dry-run mode using real PnLTracker

**Failure**:
```python
TypeError: Database.__init__() missing 1 required positional argument: 'db_path'
```

**Root cause**: Test creates `Database()` without required `db_path` parameter

**Code**:
```python
# Line 175 in test_dry_run.py
db = Database()  # ❌ Missing db_path argument
tracker = PnLTracker(db=db)
```

**Fix**: Use temp_db fixture from conftest.py
```python
async def test_dry_run_pnl_calculation(dry_run_env, temp_db):
    """Test P&L calculation in dry-run mode."""
    tracker = PnLTracker(db=temp_db)
    # Rest of test...
```

**Estimated fix time**: 10 minutes
**Priority**: Medium (runtime test, not blocking core functionality)
**Blocks**: Dry-run mode validation

---

### Test 2: `test_dry_run_vs_real_comparison`

**Location**: `tests/runtime/test_dry_run.py::test_dry_run_vs_real_comparison`

**What it tests**: Comparison between dry-run and real execution paths

**Failure**:
```python
assert result['passed'] is True
AssertionError: assert False is True
```

**Root cause**: Test expects `real_path_taken != dry_run_path_taken` to be True, but both paths are the same

**Code (line 237)**:
```python
result = {
    'exit_code': 0,
    'passed': real_path_taken != dry_run_path_taken,  # ❌ Both are False
    'modes_different': True
}
```

**Analysis**: The test's logic is incomplete - it sets both `real_path_taken` and `dry_run_path_taken` to False, then expects them to be different. The test needs actual implementation to differentiate paths.

**Fix**: Implement actual dry-run vs real mode detection logic
```python
# Need to implement mode detection
if DRY_RUN_MODE:
    dry_run_path_taken = True
else:
    real_path_taken = True
```

**Estimated fix time**: 2 hours (needs dry-run mode implementation)
**Priority**: Low (nice-to-have feature for debugging)
**Blocks**: Dry-run mode validation

---

### Test 3: `test_post_condition_event_bus_operational`

**Location**: `tests/runtime/test_post_conditions.py::test_post_condition_event_bus_operational`

**What it tests**: Event bus remains operational after processing multiple events

**Failure**:
```python
assert result['passed'] is True
AssertionError: assert False is True
```

**Root cause**: `EventBus.publish()` is async but being called synchronously (line 117)

**Code**:
```python
# Line 117 - Calling async method without await
bus.publish(RiskEvent(event_type=EventType.TRADE_EXECUTED, data={}))
# ❌ Should be: await bus.publish(...)
```

**Warning from pytest**:
```
RuntimeWarning: coroutine 'EventBus.publish' was never awaited
```

**Fix**: Add await to async call
```python
async def test_post_condition_event_bus_operational():
    """Test that event bus remains operational after events."""
    bus = EventBus()
    events_processed = 0

    def callback(event):
        nonlocal events_processed
        events_processed += 1

    bus.subscribe(EventType.TRADE_EXECUTED, callback)

    # Process multiple events
    for i in range(5):
        await bus.publish(RiskEvent(event_type=EventType.TRADE_EXECUTED, data={}))

    # Give callbacks time to execute
    await asyncio.sleep(0.1)

    # Post-conditions
    all_events_processed = events_processed == 5
    # ... rest of test
```

**Estimated fix time**: 15 minutes
**Priority**: High (tests critical event bus functionality)
**Blocks**: Event bus validation

---

### Test 4: `test_smoke_event_bus_success`

**Location**: `tests/runtime/test_smoke.py::test_smoke_event_bus_success`

**What it tests**: Event bus initializes and processes events in smoke test

**Failure**:
```python
assert result['passed'] is True
AssertionError: assert False is True
```

**Root cause**: Same as Test 3 - `EventBus.publish()` called without await (line 85)

**Code**:
```python
# Line 85
bus.publish(RiskEvent(event_type=EventType.POSITION_UPDATED, data={}))
# ❌ Should be: await bus.publish(...)
```

**Warning from pytest**:
```
RuntimeWarning: coroutine 'EventBus.publish' was never awaited
```

**Fix**: Add await and delay
```python
async def test_smoke_event_bus_success():
    """Test that event bus initializes and processes events."""
    bus = EventBus()
    event_received = False

    def callback(event):
        nonlocal event_received
        event_received = True

    bus.subscribe(EventType.POSITION_UPDATED, callback)
    await bus.publish(RiskEvent(event_type=EventType.POSITION_UPDATED, data={}))

    # Give callback time to execute
    await asyncio.sleep(0.1)

    result = {
        'exit_code': 0,
        'passed': event_received,
        'output': 'Event bus working'
    }
    # ... rest of test
```

**Estimated fix time**: 15 minutes
**Priority**: Critical (blocks smoke test validation)
**Blocks**: Smoke test suite, pre-deployment validation

---

### Test 5: `test_smoke_state_tracking_success`

**Location**: `tests/runtime/test_smoke.py::test_smoke_state_tracking_success`

**What it tests**: State tracking components (PnLTracker) initialize correctly

**Failure**:
```python
TypeError: Database.__init__() missing 1 required positional argument: 'db_path'
```

**Root cause**: Same as Test 1 - Database created without db_path (line 127)

**Code**:
```python
# Line 127
db = Database()  # ❌ Missing db_path
tracker = PnLTracker(db=db)
```

**Fix**: Use temp_db fixture
```python
async def test_smoke_state_tracking_success(temp_db):
    """Test that state tracking components initialize."""
    tracker = PnLTracker(db=temp_db)

    # Track a simple transaction
    tracker.record_realized_pnl(100.0, "MNQ")
    total = tracker.get_total_realized_pnl()

    result = {
        'exit_code': 0,
        'passed': total == 100.0,
        'output': f'P&L tracking working: {total}'
    }
    # ... rest of test
```

**Estimated fix time**: 10 minutes
**Priority**: Critical (blocks smoke test validation)
**Blocks**: State tracking validation, pre-deployment checks

---

## Summary of Failing Tests

| Test | Issue | Fix Time | Priority | Fix Complexity |
|------|-------|----------|----------|----------------|
| test_dry_run_pnl_calculation | Missing db_path | 10 min | Medium | Trivial |
| test_dry_run_vs_real_comparison | Logic incomplete | 2 hours | Low | Moderate |
| test_post_condition_event_bus_operational | Missing await | 15 min | High | Trivial |
| test_smoke_event_bus_success | Missing await | 15 min | Critical | Trivial |
| test_smoke_state_tracking_success | Missing db_path | 10 min | Critical | Trivial |

**Total fix time for critical issues**: 50 minutes (Tests 3, 4, 5)
**Total fix time for all issues**: 3 hours

**Pattern identified**: All failures are test infrastructure issues, not implementation bugs!

---

## Coverage Gap Analysis

### Code Coverage Report (from pytest --cov)

**Overall Coverage**: 18.27% (1,505 statements, 1,230 missed)

#### Well-Covered Modules (>70%)

| Module | Statements | Coverage | Status |
|--------|------------|----------|--------|
| `core/events.py` | 56 | 94.64% | ✅ Excellent |
| `state/database.py` | 72 | 95.83% | ✅ Excellent |
| `state/pnl_tracker.py` | 56 | 78.57% | ✅ Good |
| `core/config.py` | 39 | 76.92% | ✅ Good |

#### Poorly-Covered Modules (<50%)

| Module | Statements | Coverage | Status |
|--------|------------|----------|--------|
| `ai/integration.py` | 48 | 0.00% | ❌ Untested |
| `integrations/trading.py` | 80 | 0.00% | ❌ Untested |
| `rules/base.py` | 14 | 0.00% | ❌ Untested |
| `rules/daily_loss.py` | 17 | 0.00% | ❌ Untested |
| `rules/max_contracts_per_instrument.py` | 81 | 0.00% | ❌ Untested |
| `rules/max_position.py` | 24 | 0.00% | ❌ Untested |
| `sdk/enforcement.py` | 153 | 0.00% | ❌ Untested |
| `sdk/event_bridge.py` | 104 | 0.00% | ❌ Untested |
| `sdk/suite_manager.py` | 89 | 0.00% | ❌ Untested |
| `core/manager.py` | 113 | 22.12% | ❌ Poor |
| `core/engine.py` | 77 | 54.55% | ⚠️ Moderate |

### Critical Untested Areas

#### 1. Risk Rules (0% coverage)
**Impact**: Cannot validate rule logic, violations may not trigger

**Missing tests**:
- `test_rules/test_daily_loss.py` - Daily loss limit enforcement
- `test_rules/test_max_position.py` - Position size limits
- `test_rules/test_max_contracts_per_instrument.py` - Per-instrument limits
- `test_rules/test_base.py` - Base rule functionality

**Estimated effort**: 3 days (4 rule files × 5-10 tests each)

#### 2. SDK Integration (0% coverage)
**Impact**: Cannot validate SDK calls work, enforcement may fail silently

**Missing tests**:
- `test_sdk/test_enforcement.py` - Enforcement actions (close, flatten, cancel)
- `test_sdk/test_event_bridge.py` - Event mapping SDK → Risk events
- `test_sdk/test_suite_manager.py` - SDK lifecycle (connect, disconnect, reconnect)

**Estimated effort**: 4 days (3 SDK files × 8-12 tests each)

#### 3. Trading Integration (0% coverage)
**Impact**: Cannot validate TradingIntegration wrapper works

**Missing tests**:
- `test_integrations/test_trading.py` - Wrapper around SDK

**Estimated effort**: 2 days

#### 4. AI Integration (0% coverage)
**Impact**: AI features untested

**Missing tests**:
- `test_ai/test_integration.py` - AI pattern detection

**Estimated effort**: 2 days

#### 5. Core Manager (22% coverage)
**Impact**: System lifecycle poorly tested

**Missing tests**:
- Startup sequence
- Shutdown sequence
- Config reload
- Error recovery

**Estimated effort**: 3 days

---

## Integration Test Coverage Gaps

**Current Status**: `tests/integration/` directory **does not exist**

### Missing Integration Test Scenarios

#### Scenario 1: SDK Connection Lifecycle
**Test**: `tests/integration/test_sdk_connection.py`

**What to test**:
- Connect to SDK successfully
- Disconnect gracefully
- Reconnect after connection loss
- Handle authentication errors
- Handle network timeouts

**Why critical**: SDK may disconnect in production, system must handle it

**Components tested**: SuiteManager, EventBridge, TradingIntegration

**Estimated effort**: 2 days
**Priority**: Critical

---

#### Scenario 2: Real Event Handling Flow
**Test**: `tests/integration/test_event_pipeline.py`

**What to test**:
- SDK fires PositionUpdate → EventBridge maps → RiskEvent created → EventBus publishes → Rule evaluates → Enforcement triggered → SDK action executed
- Multiple rules processing same event
- Event priority handling
- Event error propagation

**Why critical**: This is the core system flow - if this doesn't work, nothing works

**Components tested**: EventBridge, EventBus, RiskEngine, Rules, EnforcementExecutor, TradingIntegration

**Estimated effort**: 3 days
**Priority**: Critical

---

#### Scenario 3: Multi-Rule Interaction
**Test**: `tests/integration/test_multi_rule.py`

**What to test**:
- Multiple rules active simultaneously
- Single event triggers multiple rule evaluations
- Rule evaluation order
- Enforcement priority (which action takes precedence)
- Conflict resolution (rule A says flatten, rule B says cancel orders)

**Why critical**: Rules may conflict or race in production

**Components tested**: RiskEngine, all rule implementations, EnforcementExecutor

**Estimated effort**: 2 days
**Priority**: High

---

#### Scenario 4: State Persistence & Recovery
**Test**: `tests/integration/test_state_persistence.py`

**What to test**:
- P&L persists across system restart
- Rule state persists across restart
- Lockout state persists across restart
- Database migrations work
- Corrupted database recovery

**Why critical**: System must survive restarts without losing state

**Components tested**: Database, PnLTracker, LockoutManager, RiskEngine

**Estimated effort**: 2 days
**Priority**: High

---

#### Scenario 5: Error Recovery & Retry Logic
**Test**: `tests/integration/test_error_recovery.py`

**What to test**:
- SDK call fails → Retry logic kicks in → Eventually succeeds
- SDK call fails permanently → Error logged → System continues
- Network timeout → Reconnection → Resume operations
- Invalid event from SDK → Logged & skipped → System continues

**Why critical**: Production will have errors - system must be resilient

**Components tested**: EnforcementExecutor, EventBridge, SuiteManager

**Estimated effort**: 3 days
**Priority**: High

---

#### Scenario 6: Configuration Hot-Reload
**Test**: `tests/integration/test_config_reload.py`

**What to test**:
- Config file changes → System reloads → Rules updated → No restart needed
- Invalid config → Reload rejected → Previous config remains
- Partial config update → Only changed rules reload

**Why critical**: Must update rules without downtime

**Components tested**: ConfigLoader, RiskManager, RiskEngine

**Estimated effort**: 2 days
**Priority**: Medium

---

### Integration Test Summary

| Scenario | Priority | Effort | Components | Blocks |
|----------|----------|--------|------------|--------|
| SDK Connection Lifecycle | Critical | 2 days | SDK layer | Production reliability |
| Real Event Handling Flow | Critical | 3 days | Full pipeline | Core functionality |
| Multi-Rule Interaction | High | 2 days | Rules + Engine | Multi-rule accounts |
| State Persistence | High | 2 days | State layer | Restart recovery |
| Error Recovery | High | 3 days | SDK + Enforcement | Production resilience |
| Config Hot-Reload | Medium | 2 days | Config + Manager | Admin operations |

**Total integration test effort**: 14 days (~3 weeks)

---

## E2E Test Coverage Gaps

**Current Status**: `tests/e2e/` directory **does not exist**

### Missing E2E Test Scenarios

#### E2E Scenario 1: Full Violation Flow
**Test**: `tests/e2e/test_full_violation_flow.py`

**User Story**: As a trader, when I exceed max position size, the system immediately closes my position

**Test Flow**:
1. System starts (RiskManager.start())
2. Config loads (with RULE-002: max_position = 5 contracts)
3. SDK connects (mocked TradingSuite)
4. Trade event: Trader opens 6 contracts MNQ
5. SDK fires PositionUpdate event
6. EventBridge maps to RiskEvent
7. EventBus publishes POSITION_UPDATED
8. RULE-002 (MaxPosition) evaluates → VIOLATION
9. EnforcementExecutor triggers FLATTEN_ALL
10. TradingIntegration.flatten_all() called
11. SDK executes close position
12. Logged to database
13. Event published: ENFORCEMENT_ACTION

**Components tested**: ALL (end-to-end)

**Assertions**:
- Position closed within 5 seconds
- Violation logged to database
- Enforcement action logged
- SDK close_position() called exactly once

**Estimated effort**: 4 days
**Priority**: Critical
**Blocks**: Production deployment confidence

---

#### E2E Scenario 2: Daily Reset Flow
**Test**: `tests/e2e/test_daily_reset.py`

**User Story**: As an account manager, at midnight ET, daily P&L resets to zero automatically

**Test Flow**:
1. System running with accumulated P&L (-$300)
2. TimerManager fires DAILY_RESET event at midnight
3. ResetManager receives event
4. Database daily_pnl table cleared
5. PnLTracker.reset() called
6. All rules receive DAILY_RESET event
7. Rules reset internal state
8. Event published: SYSTEM_RESET_COMPLETE

**Components tested**: TimerManager, ResetManager, PnLTracker, RiskEngine, Rules

**Assertions**:
- P&L = $0 after reset
- Trade count = 0 after reset
- Rules reload correctly
- Reset logged to audit trail

**Estimated effort**: 3 days
**Priority**: High
**Blocks**: Daily compliance requirement

---

#### E2E Scenario 3: Account Lockout Flow
**Test**: `tests/e2e/test_account_lockout.py`

**User Story**: As risk manager, when critical violation occurs, account locks and only admin can unlock

**Test Flow**:
1. Critical violation triggered (e.g., daily loss > $1000)
2. LockoutManager.lock_account() called
3. Database lockout_state table updated
4. All pending orders cancelled
5. All positions flattened
6. EventBus publishes ACCOUNT_LOCKED
7. Trader CLI shows "Account Locked - Contact Admin"
8. New trades rejected automatically
9. Admin runs `admin_cli.py unlock --account-id=X`
10. Windows UAC prompt (requires admin password)
11. Admin enters password
12. LockoutManager.unlock_account() called
13. Account resumes normal operation

**Components tested**: LockoutManager, EnforcementExecutor, CLI system, Windows UAC integration

**Dependencies**:
- LockoutManager (missing - MOD-002)
- Admin CLI (missing)
- Windows Service (missing)

**Assertions**:
- Account locked within 5s of violation
- All positions closed
- New trades rejected
- Unlock requires admin rights
- Unlock logged to audit trail

**Estimated effort**: 3 days (after dependencies implemented)
**Priority**: High
**Blocks**: Security model validation

---

#### E2E Scenario 4: Multi-Symbol Trading Flow
**Test**: `tests/e2e/test_multi_symbol.py`

**User Story**: As a trader, I trade multiple instruments simultaneously, and account-wide limits apply

**Test Flow**:
1. Trader has positions: +3 MNQ, +2 NQ, -1 ES
2. Daily loss limit: -$500 across all symbols
3. Trade 1: MNQ loses -$200 → P&L = -$200 ✅ OK
4. Trade 2: NQ loses -$250 → P&L = -$450 ✅ OK
5. Trade 3: ES loses -$100 → P&L = -$550 ❌ VIOLATION
6. RULE-001 (DailyLoss) triggers
7. EnforcementExecutor flattens ALL positions (MNQ, NQ, ES)
8. Account locked for rest of day

**Components tested**: Multi-symbol P&L tracking, Account-wide rules, Cross-instrument enforcement

**Assertions**:
- P&L tracked across all symbols
- Violation triggers on account total, not per-symbol
- All instruments flattened on violation
- Account-wide lockout applied

**Estimated effort**: 3 days
**Priority**: High
**Blocks**: Multi-symbol account support

---

#### E2E Scenario 5: Service Restart & Recovery
**Test**: `tests/e2e/test_service_restart.py`

**User Story**: As system admin, when Windows Service restarts, state recovers automatically

**Test Flow**:
1. System running with state:
   - P&L = -$300
   - Trade count = 12
   - Open positions: +2 MNQ
   - Active rules: 3
2. Windows Service stopped (graceful shutdown)
3. State persisted to database
4. Windows Service restarted
5. RiskManager.start() called
6. Config reloaded
7. Database state loaded
8. SDK reconnected
9. Positions re-synced from SDK
10. Event loop resumed

**Components tested**: RiskManager lifecycle, Database persistence, SDK reconnection, State recovery

**Dependencies**:
- Windows Service implementation (missing)

**Assertions**:
- P&L restored exactly
- Trade count restored
- Positions match reality
- Rules active again
- SDK reconnected
- No events lost

**Estimated effort**: 3 days (after Windows Service implemented)
**Priority**: Medium
**Blocks**: Windows Service deployment

---

### E2E Test Summary

| Scenario | Priority | Effort | Dependencies | Blocks |
|----------|----------|--------|--------------|--------|
| Full Violation Flow | Critical | 4 days | None | Production deployment |
| Daily Reset Flow | High | 3 days | TimerManager, ResetManager | Daily compliance |
| Account Lockout Flow | High | 3 days | LockoutManager, CLI | Security model |
| Multi-Symbol Trading | High | 3 days | None | Multi-instrument support |
| Service Restart | Medium | 3 days | Windows Service | Service deployment |

**Total E2E test effort**: 16 days (~3 weeks)

**Note**: Scenarios 3 & 5 blocked by missing components (LockoutManager, CLI, Windows Service)

---

## Test Infrastructure Gaps

### Current Strengths

✅ **Interactive Test Runner** (`run_tests.py`)
- 20+ menu options
- Auto-save reports to `test_reports/latest.txt`
- Real-time output streaming
- Runtime validation (smoke, soak, trace)
- AI-friendly output

✅ **8-Checkpoint Logging System**
- Strategic logging points in core flow
- Exit codes 0/1/2 for smoke test
- Emoji-based checkpoint identification
- Troubleshooting flowcharts

✅ **Runtime Reliability Pack**
- 70 runtime tests
- Smoke test (8s validation)
- Heartbeat monitoring
- Async debugging
- Post-condition validation
- Dry-run mode

### Missing Infrastructure

#### 1. CI/CD Integration

**Current**: Manual test runs via menu
**Needed**: Automated testing on every git push

**Recommended**: GitHub Actions workflow

**Example workflow**:
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run unit tests
        run: |
          .venv/bin/python -m pytest tests/unit/ --cov
      - name: Run integration tests
        run: |
          .venv/bin/python -m pytest tests/integration/ --cov
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

**Estimated effort**: 2 days
**Priority**: High
**Blocks**: Continuous integration

---

#### 2. Performance & Load Testing

**Current**: No performance tests
**Needed**: Test system under load (1000+ events/sec)

**Recommended**: pytest-benchmark or locust

**Example test**:
```python
# tests/performance/test_event_throughput.py
def test_event_processing_throughput(benchmark):
    """Test that system can process 1000 events/sec."""
    engine = RiskEngine()
    events = [create_test_event() for _ in range(1000)]

    result = benchmark(process_events, engine, events)

    assert result.duration < 1.0  # Process 1000 events in <1s
```

**Test scenarios**:
- Event throughput (events/sec)
- Rule evaluation latency (ms)
- SDK call latency (ms)
- Memory usage under load
- CPU usage under load

**Estimated effort**: 3 days
**Priority**: Medium
**Blocks**: Performance SLA validation

---

#### 3. Regression Testing

**Current**: No automated regression suite
**Needed**: Run all tests on every PR

**Recommended**: GitHub Actions + test reports

**Benefits**:
- Catch regressions before merge
- Enforce test coverage minimums
- Block PR if tests fail
- Auto-comment test results on PR

**Example check**:
```yaml
# .github/workflows/pr-check.yml
name: PR Checks

on: pull_request

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run full test suite
        run: .venv/bin/python run_tests.py --ci-mode
      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80
      - name: Comment results on PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              body: `Test Results: ${testResults}`
            })
```

**Estimated effort**: 1 day
**Priority**: High
**Blocks**: Quality gates on PRs

---

#### 4. Mutation Testing

**Current**: No mutation testing
**Needed**: Validate tests actually catch bugs

**Recommended**: mutmut

**What it does**: Changes code (introduces bugs) and checks if tests catch them

**Example**:
```bash
# Install
pip install mutmut

# Run
mutmut run --paths-to-mutate=src/

# Report shows:
# - Killed mutants (tests caught the bug) ✅
# - Survived mutants (tests missed the bug) ❌
```

**Estimated effort**: 2 days setup + ongoing monitoring
**Priority**: Low
**Blocks**: Test quality validation

---

### Test Infrastructure Summary

| Infrastructure | Current | Needed | Effort | Priority |
|----------------|---------|--------|--------|----------|
| Interactive Runner | ✅ Excellent | ✅ Complete | 0 | - |
| Runtime Validation | ✅ Excellent | ✅ Complete | 0 | - |
| CI/CD Integration | ❌ Missing | GitHub Actions | 2 days | High |
| Performance Testing | ❌ Missing | pytest-benchmark | 3 days | Medium |
| Regression Suite | ❌ Missing | GitHub Actions | 1 day | High |
| Mutation Testing | ❌ Missing | mutmut | 2 days | Low |

**Total infrastructure effort**: 8 days

---

## Critical Path to 100% Passing Tests

### Phase 1: Fix Failing Tests (1 day)

**Goal**: Get to 100% passing (93/93)

#### Day 1 Morning: Critical Smoke Test Fixes
1. ✅ Fix `test_smoke_event_bus_success` (15 min)
   - Add `await` to `bus.publish()` call
   - Add `await asyncio.sleep(0.1)` for callback execution
2. ✅ Fix `test_smoke_state_tracking_success` (10 min)
   - Use `temp_db` fixture instead of `Database()`

**Result**: Smoke tests 100% passing → Can deploy to staging

#### Day 1 Afternoon: Event Bus & Dry-Run Fixes
3. ✅ Fix `test_post_condition_event_bus_operational` (15 min)
   - Add `await` to `bus.publish()` call
   - Add delay for async execution
4. ✅ Fix `test_dry_run_pnl_calculation` (10 min)
   - Use `temp_db` fixture
5. ⚠️ Skip `test_dry_run_vs_real_comparison` (defer to Phase 3)
   - Needs actual dry-run mode implementation
   - Mark as `@pytest.mark.skip` for now

**Result**: 92/93 tests passing (98.9%) → Good enough for continued development

---

### Phase 2: Integration Tests (2 weeks)

**Goal**: Add critical integration test coverage

#### Week 1: Core Integration Tests

**Day 1-2: SDK Connection Lifecycle**
```python
# tests/integration/test_sdk_connection.py
@pytest.mark.integration
async def test_sdk_connect_disconnect():
    """Test SDK connection lifecycle."""
    manager = SuiteManager(config)

    # Connect
    suite = await manager.connect()
    assert suite.is_connected()

    # Disconnect
    await manager.disconnect()
    assert not suite.is_connected()

@pytest.mark.integration
async def test_sdk_reconnect_after_disconnect():
    """Test SDK reconnection after disconnect."""
    manager = SuiteManager(config)

    # Connect
    suite1 = await manager.connect()

    # Simulate disconnect
    await suite1._conn.close()

    # Reconnect
    suite2 = await manager.reconnect()
    assert suite2.is_connected()
```

**Day 3-5: Real Event Handling Flow**
```python
# tests/integration/test_event_pipeline.py
@pytest.mark.integration
async def test_position_update_to_rule_evaluation():
    """Test full event pipeline: SDK → EventBridge → EventBus → Rule → Enforcement."""
    # Setup
    engine = RiskEngine(suite, config)
    await engine.start()

    # Mock SDK event
    sdk_position = create_test_position(symbol="MNQ", quantity=6)

    # Trigger event flow
    await engine._on_position_update(sdk_position)

    # Assertions
    assert len(engine.events_processed) == 1
    assert engine.rules_evaluated["MaxPosition"] == True
    assert engine.violations_detected == 1
    assert engine.enforcement_actions == ["flatten_all"]
```

#### Week 2: State & Multi-Rule Tests

**Day 1-2: State Persistence**
```python
# tests/integration/test_state_persistence.py
@pytest.mark.integration
def test_pnl_persists_across_restart():
    """Test P&L survives system restart."""
    # First run
    db1 = Database("test.db")
    tracker1 = PnLTracker(db1)
    tracker1.record_realized_pnl(-300.0, "MNQ")
    del tracker1
    del db1

    # Second run (restart)
    db2 = Database("test.db")
    tracker2 = PnLTracker(db2)
    assert tracker2.get_total_realized_pnl() == -300.0
```

**Day 3-4: Multi-Rule Interaction**
```python
# tests/integration/test_multi_rule.py
@pytest.mark.integration
async def test_multiple_rules_process_same_event():
    """Test multiple rules evaluate same event."""
    engine = RiskEngine(suite, config)
    engine.add_rule(DailyLossRule(-500))
    engine.add_rule(MaxPositionRule(5))

    event = create_test_event(
        symbol="MNQ",
        quantity=6,  # Violates MaxPosition
        realized_pnl=-600  # Violates DailyLoss
    )

    violations = await engine.evaluate_event(event)

    assert len(violations) == 2
    assert "DailyLossRule" in violations
    assert "MaxPositionRule" in violations
```

**Day 5: Error Recovery**
```python
# tests/integration/test_error_recovery.py
@pytest.mark.integration
async def test_sdk_call_retry_on_failure():
    """Test enforcement retries on SDK failure."""
    suite = MagicMock()
    suite.close_position.side_effect = [
        ConnectionError("Network error"),
        ConnectionError("Network error"),
        None  # Success on 3rd try
    ]

    executor = EnforcementExecutor(suite)
    await executor.flatten_all("MNQ")

    assert suite.close_position.call_count == 3
```

**Integration Test Deliverables**:
- 20-30 integration tests
- SDK connection validated
- Event pipeline validated
- Multi-rule interaction validated
- State persistence validated
- Error recovery validated

---

### Phase 3: E2E Tests (2 weeks)

**Goal**: Add critical E2E test scenarios

#### Week 1: Core E2E Flows

**Day 1-2: Full Violation Flow**
```python
# tests/e2e/test_full_violation_flow.py
@pytest.mark.e2e
@pytest.mark.slow
async def test_full_violation_flow():
    """Test complete flow from violation to enforcement."""
    # Start system
    manager = RiskManager(config_path="config/test_risk_config.yaml")
    await manager.start()

    # Wait for system ready
    await asyncio.sleep(2)

    # Simulate trader opens large position
    mock_sdk_event = create_position_update(symbol="MNQ", quantity=6)
    await manager._suite.fire_position_update(mock_sdk_event)

    # Wait for processing
    await asyncio.sleep(1)

    # Verify enforcement
    assert manager._enforcement_executed == ["flatten_all"]
    assert manager._sdk.close_position.called

    # Verify logging
    violations = db.query("SELECT * FROM violations WHERE symbol='MNQ'")
    assert len(violations) == 1
```

**Day 3-5: Multi-Symbol Trading**
```python
# tests/e2e/test_multi_symbol.py
@pytest.mark.e2e
async def test_multi_symbol_account_wide_limit():
    """Test account-wide limits across multiple symbols."""
    manager = RiskManager(config_path="config/test_risk_config.yaml")
    await manager.start()

    # Trade 1: MNQ loses -$200
    await simulate_trade("MNQ", realized_pnl=-200)
    assert manager.get_daily_pnl() == -200

    # Trade 2: NQ loses -$250
    await simulate_trade("NQ", realized_pnl=-250)
    assert manager.get_daily_pnl() == -450

    # Trade 3: ES loses -$100 → VIOLATION (-$550 total)
    await simulate_trade("ES", realized_pnl=-100)

    # Verify account-wide enforcement
    assert manager.account_locked == True
    assert manager._sdk.close_all_positions.called
```

#### Week 2: Complex E2E Scenarios

**Day 1-2: Daily Reset**
```python
# tests/e2e/test_daily_reset.py
@pytest.mark.e2e
async def test_midnight_reset():
    """Test daily P&L resets at midnight ET."""
    # Setup with P&L
    manager = RiskManager(config)
    await manager.start()
    await simulate_trade("MNQ", realized_pnl=-300)

    # Simulate midnight
    await manager._timer_manager.fire_midnight_reset()

    # Verify reset
    assert manager.get_daily_pnl() == 0
    assert manager.get_daily_trade_count() == 0
```

**Day 3-5: Service Restart (requires Windows Service)**
```python
# tests/e2e/test_service_restart.py
@pytest.mark.e2e
@pytest.mark.requires_service
async def test_service_restart_recovery():
    """Test state recovery after service restart."""
    # First run
    manager1 = RiskManager(config)
    await manager1.start()
    await simulate_trade("MNQ", realized_pnl=-300)
    await manager1.stop()

    # Simulate restart
    manager2 = RiskManager(config)
    await manager2.start()

    # Verify state restored
    assert manager2.get_daily_pnl() == -300
    assert manager2._rules_loaded == 3
```

**E2E Test Deliverables**:
- 5-10 E2E tests
- Full violation flow validated
- Multi-symbol trading validated
- Daily reset flow validated
- Service restart validated (after Windows Service implemented)

---

### Phase 4: Infrastructure & Coverage (1 week)

**Goal**: Add CI/CD and improve coverage to 80%+

#### Day 1-2: CI/CD Setup
1. Create `.github/workflows/test.yml`
2. Configure pytest-cov thresholds
3. Add PR comment bot for test results
4. Test workflow on sample PR

#### Day 3-4: Add Missing Unit Tests
**Priority modules to test**:
1. `src/risk_manager/rules/base.py` (14 statements)
2. `src/risk_manager/rules/daily_loss.py` (17 statements)
3. `src/risk_manager/rules/max_position.py` (24 statements)
4. `src/risk_manager/rules/max_contracts_per_instrument.py` (81 statements)

**Estimated new tests**: 30-40 unit tests for rules

#### Day 5: Coverage Validation
1. Run full test suite with coverage
2. Generate HTML coverage report
3. Identify remaining gaps
4. Document coverage strategy

**Target**: 80% overall coverage, 95% for critical paths

---

## Testing Roadmap Summary

### Week 1: Foundation (1 week)
- ✅ Fix 5 failing tests (1 day)
- ✅ Create integration test structure (1 day)
- ✅ Add SDK connection tests (2 days)
- ✅ Add event pipeline tests (2 days)

### Week 2-3: Integration Coverage (2 weeks)
- ✅ State persistence tests (2 days)
- ✅ Multi-rule interaction tests (2 days)
- ✅ Error recovery tests (2 days)
- ✅ Config hot-reload tests (2 days)
- ✅ Additional integration scenarios (2 days)

### Week 4-5: E2E Coverage (2 weeks)
- ✅ Full violation flow (2 days)
- ✅ Multi-symbol trading (2 days)
- ✅ Daily reset flow (2 days)
- ✅ Account lockout flow (2 days - after LockoutManager)
- ✅ Service restart flow (2 days - after Windows Service)

### Week 6: Infrastructure & Polish (1 week)
- ✅ CI/CD setup (2 days)
- ✅ Add missing unit tests (2 days)
- ✅ Coverage validation (1 day)

**Total Timeline**: 6 weeks to comprehensive test coverage

---

## Recommended Testing Order

### Immediate Actions (This Week)

**Priority 1: Fix Failing Tests** (1 day)
1. Fix smoke test event bus failures (30 min)
2. Fix smoke test state tracking failure (10 min)
3. Fix post-condition event bus failure (15 min)
4. Fix dry-run PnL calculation failure (10 min)
5. Skip dry-run comparison test (5 min)

**Milestone**: 92/93 tests passing (98.9%)

---

**Priority 2: Create Integration Test Structure** (1 day)
1. Create `tests/integration/` directory
2. Add `conftest.py` with real SDK fixtures
3. Document integration test patterns
4. Add first integration test (SDK connection)

**Milestone**: Integration test framework ready

---

### Short-Term (Next 2 Weeks)

**Priority 3: Core Integration Tests** (2 weeks)
1. SDK connection lifecycle (2 days)
2. Real event handling flow (3 days)
3. State persistence (2 days)
4. Multi-rule interaction (2 days)
5. Error recovery (3 days)

**Milestone**: 20-30 integration tests, critical paths validated

---

### Medium-Term (Weeks 3-5)

**Priority 4: E2E Tests** (2 weeks)
1. Full violation flow (2 days)
2. Multi-symbol trading (2 days)
3. Daily reset flow (2 days)
4. Remaining E2E scenarios (4 days)

**Milestone**: 5-10 E2E tests, full workflows validated

---

**Priority 5: Infrastructure** (1 week)
1. CI/CD setup (2 days)
2. Coverage improvement (2 days)
3. Performance testing (1 day)

**Milestone**: Automated testing pipeline, 80%+ coverage

---

### Long-Term (After Week 6)

**Priority 6: Advanced Testing** (ongoing)
1. Mutation testing
2. Load testing
3. Stress testing
4. Security testing

**Milestone**: Production-grade test suite

---

## Blockers Analysis

### What's Blocked by Testing Gaps

❌ **Production Deployment**
- 5 failing tests (smoke tests critical)
- No integration tests (can't validate SDK integration)
- No E2E tests (can't validate full workflows)
- 18% code coverage (rules & enforcement untested)

❌ **Multi-Symbol Features**
- No integration tests for multi-symbol P&L tracking
- No E2E tests for account-wide limits

❌ **Account Lockout Features**
- No E2E tests for lockout flow
- Blocked by missing LockoutManager (MOD-002)

❌ **Service Deployment**
- No E2E tests for service restart
- Blocked by missing Windows Service implementation

❌ **CI/CD Pipeline**
- No automated regression testing
- No PR quality gates

---

### What Can Be Implemented Now

✅ **Fix Failing Tests** (no blockers)
- All failures are test infrastructure issues
- Fixes are trivial (15-30 min each)

✅ **Add Integration Tests** (no blockers)
- Can mock SDK where needed
- Can test real components (EventBus, Rules, State)

✅ **Add Basic E2E Tests** (no blockers)
- Can test full violation flow
- Can test multi-symbol trading
- Can test daily reset (after TimerManager implemented)

✅ **CI/CD Setup** (no blockers)
- GitHub Actions ready to use
- pytest-cov already installed

---

## Dependencies on Other Work

### Integration Tests Depend On

✅ **SDK integration** (exists)
- SuiteManager implemented
- EventBridge implemented
- TradingIntegration implemented

✅ **Risk rules** (partial)
- 3 of 13 rules implemented
- Can test existing rules
- Add tests as new rules implemented

⚠️ **State managers** (partial)
- Database implemented
- PnLTracker implemented
- LockoutManager missing (MOD-002)

---

### E2E Tests Depend On

✅ **Full violation flow** (can implement now)
- All components exist
- Can use mocked SDK

⚠️ **Daily reset flow** (needs TimerManager)
- TimerManager missing (MOD-003)
- ResetManager missing (MOD-004)
- Can mock for now, real implementation later

❌ **Account lockout flow** (blocked)
- LockoutManager missing (MOD-002)
- Admin CLI missing
- Windows Service missing
- Can implement after these components

❌ **Service restart flow** (blocked)
- Windows Service missing
- Can implement after service deployment

---

## Test Quality Best Practices

### DO

✅ **Write tests BEFORE implementation** (TDD)
- Red → Green → Refactor
- Tests document expected behavior
- Prevents over-engineering

✅ **Use `spec=` on all mocks**
```python
# Good
mock_suite = Mock(spec=TradingSuite)
mock_suite.close_position = AsyncMock()

# Bad
mock_suite = Mock()
mock_suite.close_position = AsyncMock()
```

✅ **Test edge cases and errors**
```python
@pytest.mark.parametrize("input,expected,raises", [
    (5, True, None),           # Normal case
    (0, False, ValueError),    # Edge: zero
    (-1, False, ValueError),   # Edge: negative
    (None, False, TypeError),  # Edge: None
    (1000000, False, ValueError),  # Edge: too large
])
def test_validate_quantity(input, expected, raises):
    if raises:
        with pytest.raises(raises):
            validate_quantity(input)
    else:
        assert validate_quantity(input) == expected
```

✅ **Keep tests fast**
- Unit tests: <1s each
- Integration tests: <5s each
- E2E tests: <30s each
- Use timeouts to enforce

✅ **Use parametrize for multiple scenarios**
```python
@pytest.mark.parametrize("limit,pnl,should_breach", [
    (-500, -400, False),  # Under limit
    (-500, -500, False),  # At limit
    (-500, -501, True),   # Breach by $1
    (-500, -1000, True),  # Large breach
])
def test_daily_loss_scenarios(limit, pnl, should_breach):
    rule = DailyLossRule(limit=limit)
    result = rule.evaluate(create_event(realized_pnl=pnl))
    assert result.violated == should_breach
```

✅ **Mock at service boundaries only**
```python
# Good: Mock external SDK
mock_suite = Mock(spec=TradingSuite)
engine = RiskEngine(mock_suite)

# Bad: Mock internal components
mock_event_bus = Mock()  # EventBus is internal, don't mock!
```

✅ **Aim for 90%+ coverage**
- Critical paths: 95%+
- New features: 100%
- Exclude only unreachable code

✅ **Run smoke test before deployment**
```bash
python run_tests.py → [s]
# Exit code MUST be 0
```

✅ **Check all 8 checkpoints**
```bash
python run_tests.py → [l]
# Look for: 🚀 ✅ ✅ ✅ ✅ 📨 🔍 ⚠️
```

---

### DON'T

❌ **Write code before tests**
- Leads to untestable code
- Misses edge cases
- No documentation of expected behavior

❌ **Use mocks without `spec=`**
- Typos pass silently
- API changes not caught
- False confidence

❌ **Only test happy paths**
```python
# Bad: Only test success
def test_place_order():
    order = place_order("MNQ", 1)
    assert order.status == "filled"

# Good: Test errors too
@pytest.mark.parametrize("symbol,quantity,raises", [
    ("MNQ", 1, None),           # Success
    ("", 1, ValueError),        # Invalid symbol
    ("MNQ", 0, ValueError),     # Invalid quantity
    ("MNQ", -1, ValueError),    # Negative quantity
    (None, 1, TypeError),       # None symbol
])
def test_place_order(symbol, quantity, raises):
    if raises:
        with pytest.raises(raises):
            place_order(symbol, quantity)
    else:
        order = place_order(symbol, quantity)
        assert order.status == "filled"
```

❌ **Over-mock (mock internal components)**
```python
# Bad: Mocking EventBus (internal component)
mock_event_bus = Mock()
engine = RiskEngine(suite, mock_event_bus)

# Good: Use real EventBus, mock external SDK
real_event_bus = EventBus()
mock_suite = Mock(spec=TradingSuite)
engine = RiskEngine(mock_suite, real_event_bus)
```

❌ **Skip integration tests**
- Unit tests pass but runtime fails
- Component interfaces mismatch
- SDK integration broken

❌ **Ignore failing tests**
- "It's just a flaky test"
- Mask real issues
- Erode test suite confidence

❌ **Deploy without smoke test passing**
```bash
python run_tests.py → [s]
# Exit code 2 = Boot stalled
# Exit code 1 = Exception
# NEVER deploy with exit code != 0
```

❌ **Ignore runtime validation**
- Tests validate logic
- Runtime validates liveness
- Need both!

---

## Quick Reference

### Test Commands

```bash
# Interactive menu (recommended)
python run_tests.py

# Unit tests
python run_tests.py → [2]

# Integration tests (when implemented)
python run_tests.py → [3]

# E2E tests (when implemented)
python run_tests.py → [4]

# Smoke test (runtime validation)
python run_tests.py → [s]
# Must return exit code 0

# Gate test (full suite + smoke)
python run_tests.py → [g]

# View latest results
cat test_reports/latest.txt

# Coverage report
python run_tests.py → [6]

# HTML coverage report
python run_tests.py → [7]
# Opens htmlcov/index.html
```

---

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | SUCCESS | Deploy ready ✅ |
| 1 | EXCEPTION | Check logs, fix error 🔴 |
| 2 | STALLED | Check event subscriptions 🟡 |

---

### 8 Checkpoints

```
🚀 Service Start          (manager.py)
✅ Config Loaded          (manager.py)
✅ SDK Connected          (manager.py)
✅ Rules Initialized      (manager.py)
✅ Event Loop Running     (engine.py)
📨 Event Received         (engine.py)
🔍 Rule Evaluated         (engine.py)
⚠️ Enforcement Triggered  (enforcement.py)
```

**Find where it stopped**:
```bash
python run_tests.py → [l]
# Look for last checkpoint logged
```

---

### Daily Workflow

**Morning start**:
```bash
python run_tests.py → [s]  # Smoke test
python run_tests.py → [2]  # Unit tests
```

**During development** (TDD):
```bash
# 1. Write test first (it fails - RED)
# 2. Implement feature
# 3. Run tests
python run_tests.py → [9]  # Last failed
# 4. Repeat until GREEN
```

**Before commit**:
```bash
python run_tests.py → [1]  # All tests
python run_tests.py → [6]  # Coverage
python run_tests.py → [s]  # Smoke test
```

**Before deployment**:
```bash
python run_tests.py → [g]  # Gate test
# Exit code MUST be 0
```

---

## Conclusion

### Summary Statistics

- **Total Tests**: 93 (23 unit + 70 runtime)
- **Passing Rate**: 94.6% (88/93)
- **Coverage**: 18.27% overall (needs 80%+)
- **Integration Tests**: 0 (need 20-30)
- **E2E Tests**: 0 (need 5-10)
- **CI/CD**: Not implemented

### Critical Gaps

1. **5 failing tests** - Can fix in 1 day
2. **0 integration tests** - Need 2 weeks to add
3. **0 E2E tests** - Need 2 weeks to add
4. **82% code not covered** - Need unit tests for rules & enforcement
5. **No CI/CD** - Need GitHub Actions setup

### Timeline to Production-Ready Testing

- **Week 1**: Fix failing tests + integration test structure
- **Week 2-3**: Add integration test coverage
- **Week 4-5**: Add E2E test coverage
- **Week 6**: CI/CD + coverage improvement

**Total**: 6 weeks to comprehensive test suite

### Immediate Actions

**Today**:
1. Fix 5 failing tests (1 day)
2. Create integration test structure (1 day)

**This Week**:
3. Add SDK connection tests (2 days)
4. Add event pipeline tests (2 days)

**This Month**:
5. Complete integration test coverage (2 weeks)
6. Start E2E test coverage (1 week)

### Can We Deploy Now?

❌ **No** - Blockers:
1. 5 failing tests (including critical smoke tests)
2. No integration tests (can't validate SDK integration)
3. No E2E tests (can't validate full workflows)
4. 18% code coverage (rules & enforcement untested)

### When Can We Deploy?

✅ **After Week 1**: Fix failing tests
- Smoke tests pass → Can deploy to staging
- Still no integration/E2E tests → Risky

✅ **After Week 3**: Add integration tests
- SDK integration validated → More confident
- Still no E2E tests → No workflow validation

✅ **After Week 5**: Add E2E tests
- Full workflows validated → Production ready ✅
- With monitoring and error alerting

---

**Last Updated**: 2025-10-25
**Status**: Comprehensive testing gap analysis complete
**Next Steps**: Fix failing tests, create integration test structure
**Owner**: Development team
**Timeline**: 6 weeks to production-ready test suite
