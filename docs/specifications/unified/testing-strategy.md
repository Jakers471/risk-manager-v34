# Unified Testing Strategy

**Version**: 1.0
**Date**: 2025-10-25
**Status**: Authoritative Specification
**Purpose**: Complete testing approach for Risk Manager V34

---

## Executive Summary

This document consolidates all testing strategies, methodologies, and best practices for the Risk Manager V34 project. It defines a comprehensive 4-tier testing pyramid with runtime validation, establishing the authoritative approach for all testing activities.

**Key Statistics**:
- **Current Tests**: 93 total (23 unit + 70 runtime)
- **Passing Rate**: 94.6% (88 passing, 5 failing)
- **Coverage**: 18.27% overall (target: 90%+)
- **Testing Infrastructure**: Excellent (interactive runner, auto-reports, 8-checkpoint logging)

**Critical Gap**: Need integration and E2E tests for production deployment.

---

## 1. Testing Pyramid Architecture

### 1.1 Four-Tier Testing Model

The Risk Manager V34 uses a 4-tier testing pyramid with runtime validation:

```
               /\
              /E2E\                10% - Full workflows (5-10 tests)
             /------\
            /  Integ \             30% - Component interaction (20-30 tests)
           /----------\
          / Unit Tests \           60% - Fast, isolated logic (60+ tests)
         /--------------\
        /  Runtime Pack  \         Cross-cutting - Deployment validation
       /------------------\
```

### 1.2 Test Type Definitions

#### Unit Tests (60% of test suite)
**Purpose**: Validate individual function/class logic in isolation

**Characteristics**:
- **Speed**: <1 second per test
- **Isolation**: Heavy mocking of dependencies
- **Scope**: Single function or class
- **Location**: `tests/unit/`
- **Markers**: `@pytest.mark.unit`

**What to test**:
- Rule evaluation logic
- State calculations (P&L, position tracking)
- Configuration parsing
- Event transformations
- Data validation

**Example**:
```python
def test_daily_loss_rule_triggers_at_limit():
    """Test rule triggers when daily loss exceeds limit."""
    # ARRANGE
    rule = DailyLossRule(limit=-500)
    mock_tracker = Mock(spec=PnLTracker)
    mock_tracker.get_daily_pnl.return_value = -501

    # ACT
    result = rule.evaluate(mock_tracker)

    # ASSERT
    assert result.violated is True
    assert result.severity == "CRITICAL"
```

#### Integration Tests (30% of test suite)
**Purpose**: Validate component interactions with real dependencies

**Characteristics**:
- **Speed**: 0.5-2 seconds per test
- **Isolation**: Real components, mock only external APIs
- **Scope**: Multiple components interacting
- **Location**: `tests/integration/`
- **Markers**: `@pytest.mark.integration`

**What to test**:
- SDK connection lifecycle
- Event pipeline (SDK → EventBridge → EventBus → Rules → Enforcement)
- Multi-rule interactions
- State persistence across operations
- Error recovery and retry logic
- Configuration hot-reload

**Example**:
```python
@pytest.mark.integration
async def test_event_pipeline_end_to_end():
    """Test complete event flow through system."""
    # ARRANGE - Use REAL components
    event_bus = EventBus()
    engine = RiskEngine(event_bus, config)
    mock_suite = Mock(spec=TradingSuite)  # Mock only external SDK

    # ACT
    event = RiskEvent(event_type=EventType.POSITION_UPDATED, data={...})
    await event_bus.publish(event)
    await asyncio.sleep(0.1)  # Allow processing

    # ASSERT
    assert engine.rules_evaluated == ["DailyLossRule", "MaxPositionRule"]
    assert mock_suite.close_position.called
```

#### E2E Tests (10% of test suite)
**Purpose**: Validate complete user workflows end-to-end

**Characteristics**:
- **Speed**: 5-30 seconds per test
- **Isolation**: Full system, mock only broker API
- **Scope**: Complete workflows
- **Location**: `tests/e2e/`
- **Markers**: `@pytest.mark.e2e`, `@pytest.mark.slow`

**What to test**:
- Full violation flow (trade → rule breach → enforcement → lockout)
- Daily reset flow
- Account lockout/unlock flow
- Multi-symbol trading (account-wide limits)
- Service restart and recovery

**Example**:
```python
@pytest.mark.e2e
@pytest.mark.slow
async def test_full_violation_flow():
    """Test complete violation workflow from trade to enforcement."""
    # ARRANGE - Start full system
    manager = RiskManager(config_path="config/test_risk_config.yaml")
    await manager.start()

    # ACT - Simulate violation
    mock_position_event = create_position_update(symbol="MNQ", quantity=6)
    await manager._suite.fire_position_update(mock_position_event)
    await asyncio.sleep(1)

    # ASSERT
    violations = await db.query("SELECT * FROM violations WHERE symbol='MNQ'")
    assert len(violations) == 1
    assert manager._sdk.close_position.called
```

#### Runtime Validation Pack (Cross-cutting)
**Purpose**: Validate system liveness and deployment readiness

**Characteristics**:
- **Speed**: 8-60 seconds
- **Isolation**: Real environment
- **Scope**: Boot validation, liveness monitoring
- **Location**: `tests/runtime/` and `src/runtime/`
- **Markers**: `@pytest.mark.runtime`

**What to test**:
- Smoke tests (8s boot validation)
- Heartbeat monitoring (liveness)
- Async debugging (deadlock detection)
- Post-conditions (wiring validation)
- Dry-run mode (deterministic testing)

**Example**:
```python
@pytest.mark.runtime
async def test_smoke_boot_and_first_event():
    """Smoke test: Boot system and validate first event within 8s."""
    # ARRANGE
    manager = RiskManager(config)

    # ACT
    start_time = time.time()
    await manager.start()

    # Wait for first event (max 8s)
    for _ in range(80):  # 8s timeout
        if manager._events_processed > 0:
            break
        await asyncio.sleep(0.1)

    elapsed = time.time() - start_time

    # ASSERT
    assert manager._events_processed > 0, "No events processed"
    assert elapsed < 8.0, f"Boot took too long: {elapsed}s"
```

---

## 2. Test-Driven Development (TDD)

### 2.1 Red-Green-Refactor Cycle

**ALWAYS write tests BEFORE implementation.**

#### Step 1: RED - Write Failing Test
```python
def test_daily_loss_limit():
    """Test that rule triggers at loss limit."""
    rule = DailyRealizedLossRule(limit=-500)
    result = rule.check(trade_with_loss(-500))
    assert result is not None  # ❌ FAILS - not implemented yet
```

#### Step 2: GREEN - Minimal Implementation
```python
class DailyRealizedLossRule:
    def check(self, trade):
        if trade.pnl <= self.limit:
            return RuleBreach(...)
        return None
```

#### Step 3: REFACTOR - Improve Quality
- Extract methods
- Remove duplication
- Optimize performance
- Tests still pass ✅

#### Step 4: REPEAT
Move to next feature or edge case.

### 2.2 TDD Benefits

✅ **Design**: Tests force good API design
✅ **Documentation**: Tests document expected behavior
✅ **Confidence**: Know when feature is complete
✅ **Regression**: Catch breaking changes immediately
✅ **Coverage**: 100% coverage by design

---

## 3. Test Organization

### 3.1 Directory Structure

```
tests/
├── conftest.py              # Shared fixtures & pytest config
├── fixtures/                # Test data factories
│   ├── __init__.py
│   ├── accounts.py          # Account test data
│   ├── positions.py         # Position test data
│   ├── orders.py            # Order test data
│   └── trades.py            # Trade test data
├── unit/                    # Unit tests (60% of suite)
│   ├── test_core/
│   │   ├── test_events.py
│   │   ├── test_engine.py
│   │   └── test_manager.py
│   ├── test_rules/
│   │   ├── test_base.py
│   │   ├── test_daily_loss.py
│   │   ├── test_max_position.py
│   │   └── test_max_contracts.py
│   ├── test_state/
│   │   ├── test_database.py
│   │   └── test_pnl_tracker.py
│   ├── test_sdk/
│   │   ├── test_enforcement.py
│   │   ├── test_event_bridge.py
│   │   └── test_suite_manager.py
│   └── test_integrations/
│       └── test_trading.py
├── integration/             # Integration tests (30% of suite)
│   ├── test_sdk_connection.py
│   ├── test_event_pipeline.py
│   ├── test_multi_rule.py
│   ├── test_state_persistence.py
│   ├── test_error_recovery.py
│   └── test_config_reload.py
├── e2e/                     # End-to-end tests (10% of suite)
│   ├── test_full_violation_flow.py
│   ├── test_daily_reset.py
│   ├── test_account_lockout.py
│   ├── test_multi_symbol.py
│   └── test_service_restart.py
└── runtime/                 # Runtime validation tests
    ├── test_smoke.py
    ├── test_heartbeat.py
    ├── test_async_debug.py
    ├── test_post_conditions.py
    └── test_dry_run.py
```

### 3.2 File Naming Convention

**Pattern**: Source file path maps directly to test file path

```
Source:  src/risk_manager/{module}/{file}.py
Test:    tests/unit/test_{module}/test_{file}.py

Examples:
src/risk_manager/state/pnl_tracker.py
  → tests/unit/test_state/test_pnl_tracker.py

src/risk_manager/rules/daily_loss.py
  → tests/unit/test_rules/test_daily_loss.py
```

### 3.3 Test Class Organization

**Group related tests into classes by concern**:

```python
class TestPnLTrackerBasics:
    """Test basic PnLTracker functionality."""
    def test_initialization(self):
        ...
    def test_add_trade(self):
        ...

class TestPnLTrackerPersistence:
    """Test database persistence."""
    def test_persists_across_restart(self):
        ...
    def test_recovery_after_crash(self):
        ...

class TestPnLTrackerEdgeCases:
    """Test edge cases and error handling."""
    def test_handles_none_pnl(self):
        ...
    def test_rejects_invalid_input(self):
        ...
```

**Benefits**:
- Logical grouping
- Clear intent
- Easy navigation
- Fixture reuse within class

---

## 4. Writing Effective Tests

### 4.1 AAA Pattern (Arrange-Act-Assert)

**The standard pattern for unit tests**:

```python
def test_position_update():
    # ARRANGE - Set up test data and dependencies
    position = Position(symbol="MNQ", size=1, price=15000)
    trade = Trade(symbol="MNQ", pnl=-50)

    # ACT - Execute the behavior being tested
    result = position.update(trade)

    # ASSERT - Verify expected outcomes
    assert result.pnl == -50
    assert result.size == 0
```

### 4.2 Given-When-Then Pattern (BDD Style)

**Use for business logic and rules**:

```python
def test_daily_loss_breach():
    """
    GIVEN: Daily loss limit of -$500, current loss of -$400
    WHEN: Trade pushes total loss to -$501
    THEN: Rule triggers breach and locks account
    """
    # GIVEN
    rule = DailyRealizedLossRule(limit=-500)
    pnl_tracker.daily_loss = -400

    # WHEN
    result = rule.check(trade_with_loss(-101))

    # THEN
    assert result.action == "LOCKOUT"
    assert result.severity == "CRITICAL"
```

### 4.3 Parametrized Tests

**Test multiple scenarios efficiently**:

```python
@pytest.mark.parametrize("limit,pnl,should_breach", [
    (-500, -400, False),  # Under limit
    (-500, -500, False),  # At limit (edge case)
    (-500, -501, True),   # Breach by $1
    (-500, -1000, True),  # Large breach
])
def test_daily_loss_scenarios(limit, pnl, should_breach):
    """Test daily loss rule with various scenarios."""
    rule = DailyLossRule(limit=limit)
    mock_tracker.get_daily_pnl.return_value = pnl

    result = rule.evaluate(mock_tracker)

    if should_breach:
        assert result.violated is True
    else:
        assert result.violated is False
```

**Benefits**:
- Test 4 scenarios with 1 function
- Easy to add new cases
- Clear data-driven testing
- Reduced duplication

### 4.4 Edge Cases and Error Testing

**Always test boundaries and errors**:

```python
def test_exactly_at_limit():
    """Edge case: exactly at limit (not over)."""
    rule = DailyLossRule(limit=-500)
    result = rule.check(trade_with_loss(-500))
    assert result is None  # Not a breach

def test_one_dollar_over():
    """Edge case: $1 over limit."""
    result = rule.check(trade_with_loss(-501))
    assert result is not None  # IS a breach

def test_invalid_config_raises_error():
    """Validate configuration errors are caught."""
    with pytest.raises(ValueError, match="limit must be negative"):
        DailyLossRule(limit=500)  # Positive limit is invalid

def test_handles_none_pnl():
    """Half-turn trades have no P&L."""
    trade = {"profitAndLoss": None}
    result = rule.check(trade)
    assert result is None  # Ignored, not error
```

---

## 5. Fixtures and Mocking

### 5.1 Fixture Patterns

#### Factory Fixtures
**Create test data with custom parameters**:

```python
@pytest.fixture
def event_factory():
    """Factory for creating test events."""
    def _create_event(event_type=EventType.TRADE_EXECUTED, **data):
        default_data = {"symbol": "MNQ", "timestamp": datetime.now()}
        default_data.update(data)
        return RiskEvent(event_type=event_type, data=default_data)
    return _create_event

# Usage:
def test_rule(event_factory):
    event = event_factory(realized_pnl=-100.0)  # Clean!
```

#### Database Fixtures
**Provide isolated test databases**:

```python
@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    db_path = Path(f"test_{uuid.uuid4()}.db")
    db = Database(db_path)
    yield db
    db.close()
    db_path.unlink()  # Cleanup

@pytest.fixture
def pnl_tracker(temp_db):
    """Create PnLTracker with temp database."""
    return PnLTracker(db=temp_db)
```

### 5.2 Mocking Strategy

#### Mock at Service Boundaries Only

**DO**: Mock external dependencies (SDK, APIs)
```python
@pytest.fixture
def mock_suite():
    """Mock TradingSuite (external SDK)."""
    suite = Mock(spec=TradingSuite)
    suite.close_position = AsyncMock()
    suite.cancel_all_orders = AsyncMock()
    return suite
```

**DON'T**: Mock internal components (EventBus, Rules)
```python
# ❌ BAD - Mocking internal EventBus
mock_event_bus = Mock()
engine = RiskEngine(mock_event_bus)

# ✅ GOOD - Use real EventBus, mock external SDK
real_event_bus = EventBus()
mock_suite = Mock(spec=TradingSuite)
engine = RiskEngine(real_event_bus, mock_suite)
```

#### Always Use spec=

**Prevents typos and API mismatches**:

```python
# ❌ BAD - No spec, typos pass silently
mock_tracker = Mock()
mock_tracker.get_daily_pnl.return_value = -400

# ✅ GOOD - spec catches typos
mock_tracker = Mock(spec=PnLTracker)
mock_tracker.get_daily_pnl.return_value = -400  # Verified method exists
```

#### Verify Mock Interactions

```python
def test_pnl_tracker_called_correctly():
    """Verify rule calls PnL tracker with correct args."""
    mock_tracker = Mock(spec=PnLTracker)
    rule = DailyLossRule(pnl_tracker=mock_tracker)

    rule.evaluate(event)

    # Verify mock interactions
    mock_tracker.get_daily_pnl.assert_called_once()
    mock_tracker.add_trade.assert_called_with(
        symbol="MNQ",
        pnl=-100.0
    )
```

---

## 6. Test Markers

**Categorize tests for selective execution**:

```python
@pytest.mark.unit          # Fast unit test
@pytest.mark.integration   # Integration test
@pytest.mark.e2e           # End-to-end test
@pytest.mark.slow          # Takes >5 seconds
@pytest.mark.runtime       # Runtime validation test
@pytest.mark.requires_api  # Needs TopstepX API
@pytest.mark.requires_db   # Needs database

# Run specific categories
pytest -m unit                      # Only unit tests
pytest -m "not slow"                # Skip slow tests
pytest -m "integration and not slow"  # Fast integration tests
```

---

## 7. Interactive Test Runner

### 7.1 Test Runner Menu

**Command**: `python run_tests.py`

```
╔════════════════════════════════════════════════════════════╗
║  Risk Manager V34 - Test Runner                           ║
╚════════════════════════════════════════════════════════════╝

Test Selection:
  [1] Run ALL tests
  [2] Run UNIT tests only
  [3] Run INTEGRATION tests only
  [4] Run E2E tests only
  [5] Run SLOW tests only
  [6] Run tests with COVERAGE report
  [7] Run tests with COVERAGE + HTML report
  [8] Run specific test file
  [9] Run tests matching keyword
  [0] Run last failed tests only

Runtime Checks:
  [s] Runtime SMOKE (DRY-RUN, fail-fast, 8s timeout)
  [r] Runtime SOAK (30-60s DRY-RUN)
  [t] Runtime TRACE (ASYNC_DEBUG=1, deep debug)
  [l] View/Tail LOGS
  [e] Env/Config SNAPSHOT
  [g] GATE: Tests + Smoke combo

Utilities:
  [v] Run in VERBOSE mode (shows each test)
  [c] Check COVERAGE status
  [p] View last test REPORT
  [h] Help - Testing with AI
  [q] Quit
```

### 7.2 Auto-Save Test Reports

**Every test run automatically saves to**:
- `test_reports/latest.txt` - Most recent run (overwritten)
- `test_reports/YYYY-MM-DD_HH-MM-SS_passed.txt` - Timestamped pass
- `test_reports/YYYY-MM-DD_HH-MM-SS_failed.txt` - Timestamped fail

**Usage**:
```bash
# Run tests
python run_tests.py → [2]

# AI reads results
cat test_reports/latest.txt
```

---

## 8. Runtime Validation

### 8.1 The Problem: Tests Pass, Runtime Fails

**Symptom**: ✅ Tests green, ❌ Runtime broken

**Causes**:
- Over-mocking (mocks don't match reality)
- No integration tests
- Environment issues
- Configuration errors
- SDK integration mismatch

**Solution**: Runtime Reliability Pack

### 8.2 8-Checkpoint Validation System

**Strategic logging points track system boot and operation**:

```
Checkpoint 1: 🚀 Service Start
  └─ Log: "Risk Manager starting..."
  └─ Location: manager.py:start()

Checkpoint 2: ✅ Config Loaded
  └─ Log: "Config loaded: X rules"
  └─ Location: manager.py:_load_config()

Checkpoint 3: ✅ SDK Connected
  └─ Log: "SDK connected: account_id"
  └─ Location: manager.py:_connect_sdk()

Checkpoint 4: ✅ Rules Initialized
  └─ Log: "Rules initialized: X rules"
  └─ Location: manager.py:_initialize_rules()

Checkpoint 5: ✅ Event Loop Running
  └─ Log: "Event loop running"
  └─ Location: engine.py:start()

Checkpoint 6: 📨 Event Received
  └─ Log: "Event received: {event}"
  └─ Location: engine.py:handle_event()

Checkpoint 7: 🔍 Rule Evaluated
  └─ Log: "Rule evaluated: {rule} {result}"
  └─ Location: engine.py:handle_event()

Checkpoint 8: ⚠️ Enforcement Triggered
  └─ Log: "Enforcement triggered: {action}"
  └─ Location: enforcement.py:enforce()
```

**Usage**:
```bash
# Run smoke test
python run_tests.py → [s]

# Check exit code
# 0 = Success (first event observed)
# 1 = Exception (check logs)
# 2 = Boot stalled (check subscriptions)

# View logs
python run_tests.py → [l]

# Find where it stopped
# Look for last checkpoint: 🚀 ✅ ✅ ⚠️ ← Stopped at checkpoint 4
```

### 8.3 Runtime Test Capabilities

#### Smoke Test (8s validation)
**What**: Boot system and validate first event fires within 8 seconds
**When**: After tests pass, before deployment
**Exit Codes**: 0=success, 1=exception, 2=stalled

#### Soak Test (30-60s stability)
**What**: Extended runtime validation
**Why**: Catches memory leaks, deadlocks, resource exhaustion
**When**: Before major deployments

#### Trace Mode (deep async debug)
**What**: Deep async task debugging (ASYNC_DEBUG=1)
**Output**: `runtime_trace.log` with all pending tasks
**When**: Service starts but hangs/stalls

#### Log Viewer
**What**: Stream logs in real-time or view last 100 lines
**Location**: `data/logs/risk_manager.log`
**When**: Debugging runtime issues

#### Env Snapshot
**What**: Shows configuration, env vars, Python version
**When**: Configuration troubleshooting

#### Gate Test
**What**: Unit + Integration + Smoke combo
**When**: Pre-deployment validation
**Exit Code**: Must be 0 for deployment

---

## 9. Best Practices

### 9.1 DO

✅ **Write tests BEFORE implementation** (TDD)
✅ **Use `spec=` on all mocks** (catch typos)
✅ **Test edge cases and errors** (boundaries, nulls, invalid input)
✅ **Keep tests fast** (unit <1s, integration <5s)
✅ **Use parametrize** (multiple scenarios efficiently)
✅ **Mock at service boundaries only** (external APIs, not internal components)
✅ **Aim for 90%+ coverage** (95%+ for critical paths)
✅ **Run smoke test before deployment** (validate liveness)
✅ **Check all 8 checkpoints** (find exactly where runtime fails)

### 9.2 DON'T

❌ **Write code before tests** (leads to untestable code)
❌ **Use mocks without `spec=`** (typos pass silently)
❌ **Only test happy paths** (errors happen in production)
❌ **Over-mock** (mock internal components)
❌ **Skip integration tests** (unit tests pass, runtime fails)
❌ **Ignore failing tests** ("just a flaky test")
❌ **Deploy without smoke test passing** (exit code must be 0)
❌ **Ignore runtime validation** (tests validate logic, runtime validates liveness)

---

## 10. Workflow Integration

### 10.1 Daily Development Workflow

**Morning start**:
```bash
python run_tests.py → [s]  # Smoke test
python run_tests.py → [2]  # Unit tests
```

**During development (TDD)**:
```bash
# 1. Write test first (RED)
# 2. Implement feature
# 3. Run tests
python run_tests.py → [9]  # Last failed
# 4. Repeat until GREEN
```

**Before commit**:
```bash
python run_tests.py → [s]  # Smoke test
python run_tests.py → [1]  # All tests
python run_tests.py → [6]  # Coverage
```

**Before deployment**:
```bash
python run_tests.py → [g]  # Gate test
# Exit code MUST be 0
```

### 10.2 AI-Assisted Testing Workflow

**When user says "fix test errors"**:

1. User runs tests via menu → Auto-saves to `test_reports/latest.txt`
2. User says "fix test errors"
3. AI reads `test_reports/latest.txt`
4. AI identifies failures and fixes them
5. Repeat until all tests pass

**When runtime fails**:

1. Run smoke test: `python run_tests.py → [s]`
2. Check exit code:
   - 0 = Success → Deploy
   - 1 = Exception → Check logs
   - 2 = Stalled → Check event subscriptions
3. View logs: `python run_tests.py → [l]`
4. Find stopped checkpoint: Look for last emoji
5. Fix issue based on checkpoint

---

## 11. Coverage Requirements

### 11.1 Targets

| Component | Minimum Coverage | Target Coverage |
|-----------|-----------------|-----------------|
| **Overall** | 80% | 90% |
| **Risk Rules** | 90% | 95% |
| **State Managers** | 85% | 95% |
| **SDK Integration** | 70% | 80% |
| **Core Engine** | 85% | 95% |
| **Event System** | 90% | 95% |
| **CLI** | 60% | 70% |

### 11.2 Coverage Commands

```bash
# Terminal report
python run_tests.py → [6]

# HTML report (opens in browser)
python run_tests.py → [7]

# With missing lines
pytest --cov=src --cov-report=term-missing

# Check coverage threshold
pytest --cov=src --cov-report=term --cov-fail-under=90
```

### 11.3 Coverage Analysis

**Well-covered modules (>70%)**:
- `core/events.py` - 94.64%
- `state/database.py` - 95.83%
- `state/pnl_tracker.py` - 78.57%
- `core/config.py` - 76.92%

**Poorly-covered modules (<50%)** - Need immediate attention:
- `rules/` - 0% (no unit tests for rules!)
- `sdk/` - 0% (SDK integration untested!)
- `integrations/trading.py` - 0%
- `ai/integration.py` - 0%

---

## 12. Test Infrastructure

### 12.1 Current Strengths

✅ **Interactive Test Runner** - 20+ menu options, AI-friendly
✅ **Auto-Save Reports** - `test_reports/latest.txt` for AI review
✅ **Real-time Output** - No buffering, immediate feedback
✅ **8-Checkpoint Logging** - Strategic logging for runtime debugging
✅ **Runtime Reliability Pack** - 70 runtime tests, smoke/soak/trace
✅ **Performance Optimized** - Direct venv usage (not `uv run`)

### 12.2 Missing Infrastructure

❌ **CI/CD Integration** - No GitHub Actions
❌ **Performance Testing** - No load/benchmark tests
❌ **Regression Suite** - No automated PR checks
❌ **Mutation Testing** - No test quality validation

---

## 13. Troubleshooting

### 13.1 Tests Pass But Runtime Fails

**Problem**: ✅ Tests green, ❌ Runtime broken

**Diagnosis**:
```bash
python run_tests.py → [s]  # Run smoke test
```

**Exit Codes**:
- `0` = Working
- `1` = Exception (check logs)
- `2` = Stalled (check subscriptions)

**Root Causes**:
1. Over-mocking (mocks don't match reality)
2. No integration tests
3. Mocks without `spec=`
4. Not testing error cases

**Solution**: Add integration tests with REAL components

### 13.2 Low Coverage

**Problem**: Coverage below 90%

**Find gaps**:
```bash
pytest --cov=src --cov-report=term-missing
```

**Fix**: Add tests for uncovered branches

### 13.3 Slow Tests

**Problem**: Tests take too long

**Solutions**:
1. Skip slow tests in development: `pytest -m "not slow"`
2. Mock expensive operations
3. Use smaller test data sets

---

## 14. Related Documentation

**Core Testing Docs**:
- `test-coverage-requirements.md` - Coverage targets per module
- `runtime-validation-strategy.md` - 8-checkpoint system details
- `docs/testing/WORKING_WITH_AI.md` - AI workflow patterns

**API Contracts & Troubleshooting**:
- `SDK_API_REFERENCE.md` - Actual API signatures
- `SDK_ENFORCEMENT_FLOW.md` - Complete enforcement wiring
- `TEST_RUNNER_FINAL_FIXES.md` - Runner behavior & tips

---

**Last Updated**: 2025-10-25
**Version**: 1.0
**Status**: Authoritative Specification
**Maintainer**: Development Team
