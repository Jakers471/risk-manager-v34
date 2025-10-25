# Testing Infrastructure Feature Inventory

**Researcher**: RESEARCHER 4 - Testing Specialist
**Date**: 2025-10-25
**Purpose**: Comprehensive analysis of all testing infrastructure and methodology

---

## Executive Summary

The Risk Manager V34 project has evolved a sophisticated multi-layered testing system with comprehensive runtime validation capabilities. The testing infrastructure includes:

- **Interactive test runner** with 20+ menu options
- **Automated test reporting** with AI integration
- **4-tier testing pyramid** (unit, integration, e2e, runtime)
- **Runtime Reliability Pack** with 8 checkpoint validation
- **TDD workflow** with fixture factories and parametrization
- **AI-assisted testing** workflows with 11 documented patterns

**Key Stats**:
- 3 unit test files currently implemented
- 70 runtime validation tests
- 6 runtime reliability capabilities
- Auto-save test reports for AI review
- Exit codes 0/1/2 for smoke test states

---

## Testing System Overview

### Interactive Test Runner

**File**: `/run_tests.py` (200+ lines)

#### Core Features

1. **Test Selection Menu** (20+ options):
   ```
   Test Types:
   [1] All tests
   [2] Unit tests (tests/unit/)
   [3] Integration tests (tests/integration/)
   [4] E2E tests
   [5] Slow tests only

   Coverage:
   [6] Coverage report (terminal)
   [7] Coverage + HTML report

   Targeting:
   [8] Specific test file
   [9] Keyword matching
   [0] Last failed only

   Runtime Validation:
   [s] Smoke test (8s timeout, exit codes 0/1/2)
   [r] Soak test (30-60s stability)
   [t] Trace mode (ASYNC_DEBUG=1)
   [l] View/tail logs
   [e] Environment snapshot
   [g] GATE (tests + smoke combo)

   Utilities:
   [v] Verbose mode
   [c] Coverage status
   [p] View latest report
   [h] AI workflow help
   [q] Quit
   ```

2. **Auto-Save Test Reports**:
   - `test_reports/latest.txt` - Always overwritten with most recent run
   - `test_reports/YYYY-MM-DD_HH-MM-SS_passed.txt` - Timestamped passes
   - `test_reports/YYYY-MM-DD_HH-MM-SS_failed.txt` - Timestamped failures

   **Format**:
   ```
   ============================================================
   Risk Manager V34 - Test Report
   ============================================================
   Test Run: Unit tests only
   Timestamp: 2025-10-24 18:13:37
   Status: PASSED
   Exit Code: 0
   ============================================================

   [Full pytest output with colors preserved]

   ============================================================
   End of Report
   ============================================================
   ```

3. **Performance Optimizations**:
   - Uses venv python directly (not `uv run`) for 5-10s faster startup
   - Real-time output streaming (no buffering)
   - Directory-based test selection (not markers) for reliability
   - WSL2-aware (~10s startup overhead documented)

4. **AI Integration**:
   - Quick commands printed after each run
   - Reports formatted for AI consumption
   - Exit codes clearly communicated
   - Troubleshooting guidance included

### Test Reporting System

**Directory**: `/test_reports/`
**Documentation**: `/test_reports/README.md`

#### Report Types

1. **Standard Test Reports**:
   - Full pytest output preserved
   - ANSI colors maintained
   - Pass/fail status
   - Exit codes
   - Timestamps

2. **Runtime Debug Reports**:
   - 8-checkpoint validation results
   - Exit code meanings (0=success, 1=exception, 2=stalled)
   - Troubleshooting flowcharts
   - Log file locations

#### AI Integration Patterns

```python
# AI reads latest results
Read test_reports/latest.txt

# User says "fix test errors"
# AI gets full pytest output with tracebacks

# AI implements fixes
Edit src/risk_manager/...

# User reruns via menu
python run_tests.py → [2]

# Cycle repeats until green
```

---

## Test Types

### Unit Tests

**Location**: `/tests/unit/`
**Current Files**: 3
**Test Count**: 23 tests across 3 files

#### Structure

```
tests/unit/
├── test_core/
│   ├── test_events.py (event system tests)
│   └── test_enforcement_wiring.py (enforcement integration)
├── test_state/
│   ├── __init__.py
│   └── test_pnl_tracker.py (214 lines, 5 test classes)
└── test_rules/ (planned, not yet created)
```

#### Characteristics

- **Speed**: <1s per test
- **Isolation**: Heavy mocking (mock_engine, mock_suite fixtures)
- **Scope**: Single function/class testing
- **Purpose**: Logic validation

#### Example: PnL Tracker Tests

**File**: `tests/unit/test_state/test_pnl_tracker.py`

```python
class TestPnLTrackerBasics:
    """Test basic PnLTracker functionality."""
    # Simple foundational tests

class TestPnLTrackerPersistence:
    """Test that P&L data persists across tracker instances."""
    # Database persistence with temp_db fixture

class TestPnLTrackerReset:
    """Test daily reset functionality."""
    # Reset and cleanup logic

class TestPnLTrackerTradeCount:
    """Test trade count tracking."""
    # Counter validation

class TestPnLTrackerEdgeCases:
    """Test edge cases and error handling."""
    # Boundary conditions
```

**Key Patterns**:
- AAA pattern (Arrange-Act-Assert)
- Given-When-Then for business logic
- Real database (temp_db fixture) for persistence tests
- Edge case coverage (nulls, boundaries, errors)

### Integration Tests

**Location**: `/tests/integration/` (planned)
**Status**: NOT YET IMPLEMENTED
**Target**: 10-20 tests covering component interactions

#### Planned Tests

1. **SDK Integration** (`test_sdk_integration.py`):
   - Real TradingSuite initialization
   - Real event flow to SDK
   - Real enforcement actions calling SDK
   - Real SDK response handling

2. **Event Pipeline** (`test_event_pipeline.py`):
   - Event published → EventBus → Rule evaluates → Action enforced
   - Multiple rules processing same event
   - Event priority handling
   - Event error propagation

3. **Enforcement Flow** (`test_enforcement_flow.py`):
   - Rule violation → EnforcementExecutor → SDK action
   - Enforcement logging
   - Enforcement error handling
   - Enforcement retry logic

4. **Configuration** (`test_configuration.py`):
   - YAML config loads correctly
   - Environment variable overrides
   - Invalid config rejection
   - Default value application

5. **Lifecycle** (`test_lifecycle.py`):
   - System startup
   - Component initialization
   - Graceful shutdown
   - Resource cleanup

#### Characteristics

- **Speed**: 0.5-2s per test
- **Isolation**: Real components, mock only external APIs
- **Scope**: Multiple components interacting
- **Purpose**: Interface validation

### E2E Tests

**Location**: `/tests/e2e/` (planned)
**Status**: NOT YET IMPLEMENTED
**Target**: 1-2 comprehensive workflow tests

#### Planned Scenarios

1. **Complete Trading Flow**:
   - System starts
   - Config loads
   - SDK connects
   - Trade event received
   - Rule evaluates
   - Violation detected
   - Position closed
   - Logged and persisted

2. **Multi-Rule Interaction**:
   - Multiple rules active
   - Single event triggers multiple evaluations
   - Enforcement priority handling
   - Conflict resolution

#### Characteristics

- **Speed**: >5s per test
- **Isolation**: Full system, mock only broker API
- **Scope**: Complete workflows
- **Purpose**: System validation

### Runtime Tests

**Location**: `/tests/runtime/`
**Files**: 5 files
**Test Count**: 70 tests
**Source Code**: `/src/runtime/` (1,316 lines across 6 files)

#### Runtime Reliability Pack

**NEW** system for preventing "tests green but runtime broken" syndrome.

**Files**:
```
src/runtime/
├── smoke_test.py       # Boot validation (exit codes 0/1/2)
├── heartbeat.py        # Liveness monitoring (1s intervals)
├── async_debug.py      # Task dump for deadlock detection
├── post_conditions.py  # System wiring validation
└── dry_run.py          # Deterministic mock event generator

tests/runtime/
├── test_smoke.py       # 13 smoke test scenarios
├── test_heartbeat.py
├── test_async_debug.py
├── test_post_conditions.py
└── test_dry_run.py
```

#### 8-Checkpoint Validation System

**Integrated into**: `src/risk_manager/core/`, `src/risk_manager/sdk/`

```
Checkpoint 1: 🚀 Service Start
  └─ manager.py:start()
  └─ Log: "Risk Manager starting..."

Checkpoint 2: ✅ Config Loaded
  └─ manager.py:_load_config()
  └─ Log: "Config loaded: X rules"

Checkpoint 3: ✅ SDK Connected
  └─ manager.py:_connect_sdk()
  └─ Log: "SDK connected: account_id"

Checkpoint 4: ✅ Rules Initialized
  └─ manager.py:_initialize_rules()
  └─ Log: "Rules initialized: X rules"

Checkpoint 5: ✅ Event Loop Running
  └─ engine.py:start()
  └─ Log: "Event loop running"

Checkpoint 6: 📨 Event Received
  └─ engine.py:handle_event()
  └─ Log: "Event received: {event}"

Checkpoint 7: 🔍 Rule Evaluated
  └─ engine.py:handle_event()
  └─ Log: "Rule evaluated: {rule} {result}"

Checkpoint 8: ⚠️ Enforcement Triggered
  └─ enforcement.py:enforce()
  └─ Log: "Enforcement triggered: {action}"
```

**Debugging Workflow**:
```bash
# Run smoke test
python run_tests.py → [s]

# Check exit code
# 0 = Success (first event observed within 8s)
# 1 = Exception (check logs for stack trace)
# 2 = Boot stalled (check event subscriptions)

# View logs
python run_tests.py → [l]

# Find where it stopped
# Look for last emoji checkpoint: 🚀 ✅ ✅ ✅ ✅ 📨 🔍 ⚠️
```

#### Runtime Capabilities

1. **Smoke Test** (`[s]` menu option):
   - **What**: Boots system, validates first event fires within 8s
   - **Exit Codes**: 0=success, 1=exception, 2=stalled
   - **When**: After test suite passes, before deployment
   - **Implementation**: `src/runtime/smoke_test.py`

2. **Soak Test** (`[r]` menu option):
   - **What**: Extended 30-60s runtime validation
   - **Why**: Catches memory leaks, deadlocks, resource exhaustion
   - **When**: Before major deployments
   - **Implementation**: `src/runtime/soak_test.py`

3. **Trace Mode** (`[t]` menu option):
   - **What**: Deep async task debugging (ASYNC_DEBUG=1)
   - **Output**: `runtime_trace.log` with all pending tasks
   - **When**: Service starts but hangs/stalls
   - **Implementation**: `src/runtime/async_debug.py`

4. **Log Viewer** (`[l]` menu option):
   - **What**: Stream logs in real-time or view last 100 lines
   - **Location**: `data/logs/risk_manager.log`
   - **When**: Debugging runtime issues

5. **Env Snapshot** (`[e]` menu option):
   - **What**: Shows configuration, env vars, Python version
   - **When**: Configuration troubleshooting

6. **Gate Test** (`[g]` menu option):
   - **What**: Unit + Integration + Smoke combo
   - **When**: Pre-deployment validation
   - **Exit Code**: Must be 0 for deployment

---

## TDD Workflow

### Red-Green-Refactor Cycle

**Source**: Archived docs show evolution from pre-SDK approach

```
Step 1: RED
  └─ Write test (it fails - no code yet)
  └─ Example: test_daily_loss_limit()
  └─ Run: pytest tests/unit/test_rules/test_daily_loss.py
  └─ Result: ❌ FAILED - no module

Step 2: GREEN
  └─ Write minimal code to pass test
  └─ Example: DailyLossRule class with evaluate() method
  └─ Run: pytest tests/unit/test_rules/test_daily_loss.py
  └─ Result: ✅ PASSED

Step 3: REFACTOR
  └─ Clean up code
  └─ Extract methods
  └─ Remove duplication
  └─ Run: pytest (all tests still pass)

Step 4: REPEAT
  └─ Next feature/edge case
```

### Test Organization Patterns

#### Class-Based Grouping

```python
class TestPnLTrackerBasics:
    """Test basic functionality."""
    # Foundational tests

class TestPnLTrackerPersistence:
    """Test database persistence."""
    # Persistence-specific tests

class TestPnLTrackerEdgeCases:
    """Test edge cases."""
    # Boundary conditions
```

**Benefits**:
- Logical grouping
- Clear test intent
- Easy navigation
- Fixture reuse within class

#### File Naming Convention

```
src/{module}/{file}.py  →  tests/unit/test_{module}/test_{file}.py

Examples:
src/risk_manager/state/pnl_tracker.py
  → tests/unit/test_state/test_pnl_tracker.py

src/risk_manager/rules/daily_loss.py
  → tests/unit/test_rules/test_daily_loss.py
```

### Fixture Patterns

**File**: `tests/conftest.py` (228 lines)

#### Current Fixtures

1. **Mock Engine**:
   ```python
   @pytest.fixture
   def mock_engine():
       """Mock RiskEngine for unit tests."""
       engine = AsyncMock()
       engine.account_id = "TEST-ACCOUNT-123"
       engine.suite_manager = AsyncMock()
       engine.lockout_manager = AsyncMock()
       engine.event_bus = AsyncMock()
       return engine
   ```

2. **Mock Suite** (SDK):
   ```python
   @pytest.fixture
   def mock_suite():
       """Mock TradingSuite (SDK) for testing."""
       suite = AsyncMock()
       suite.close_position = AsyncMock()
       suite.cancel_all_orders = AsyncMock()
       suite.place_order = AsyncMock()

       # Mock stats
       mock_stats = Mock()
       mock_stats.account_id = "TEST-ACCOUNT-123"
       mock_stats.balance = 100000.0
       suite.get_stats = AsyncMock(return_value=mock_stats)

       return suite
   ```

3. **Temporary Database**:
   ```python
   @pytest.fixture
   def temp_db():
       """Create temporary database for testing."""
       # Creates isolated SQLite DB
       # Auto-cleanup after test
   ```

4. **PnL Tracker** (Real):
   ```python
   @pytest.fixture
   def pnl_tracker(temp_db):
       """Create real PnLTracker with temp database."""
       return PnLTracker(temp_db)
   ```

#### Recommended Factory Fixtures

**From archived methodology analysis**:

```python
@pytest.fixture
def event_factory():
    """Factory for creating test events with custom data."""
    def _create_event(type=EventType.TRADE_EXECUTED, **data):
        default_data = {"symbol": "MNQ", "timestamp": now()}
        default_data.update(data)
        return RiskEvent(type=type, data=default_data)
    return _create_event

# Usage:
def test_rule(event_factory):
    event = event_factory(realized_pnl=-100.0)  # Clean!
```

### Parametrized Tests

**From methodology analysis**:

```python
@pytest.mark.parametrize("limit,pnl,should_breach", [
    (-500, -400, False),  # Under limit
    (-500, -500, False),  # At limit
    (-500, -501, True),   # Breach by $1
    (-500, -1000, True),  # Large breach
])
def test_daily_loss_scenarios(limit, pnl, should_breach):
    """Test multiple scenarios in one test."""
    rule = DailyLossRule(limit=limit)
    # ... test logic
```

**Benefits**:
- 4 scenarios tested with 1 test function
- Clear data-driven testing
- Easy to add new cases
- Reduced code duplication

---

## AI-Assisted Testing Workflow

**Documentation**: `docs/testing/WORKING_WITH_AI.md` (610 lines)

### 11 Documented Workflows

#### Workflow 1: Starting Fresh - Run Unit Tests
```bash
python run_tests.py → [2]
# GREEN → Move to integration
# RED → Go to Workflow 2
```

#### Workflow 2: Fix Failed Tests
```bash
cat test_reports/latest.txt  # AI reads this
# User: "Fix test errors"
# AI analyzes, suggests fixes
# User reruns: python run_tests.py → [9]
# Repeat until GREEN
```

#### Workflow 3: Integration Tests
```bash
python run_tests.py → [3]
# Requires: SDK installed, .env credentials, API access
```

#### Workflow 4: E2E Tests
```bash
python run_tests.py → [4]
# Tests complete user workflows
```

#### Workflow 5: Adding New Features (TDD)
```python
# Step 1: Write test FIRST (RED)
def test_new_feature():
    result = new_feature()
    assert result == expected

# Step 2: Run test (expect RED)
python run_tests.py → [7] → tests/unit/test_new_feature.py

# Step 3: AI implements minimal code (GREEN)
# Step 4: Rerun test → [9]
# Step 5: Refactor
```

#### Workflow 6: Coverage Analysis
```bash
python run_tests.py → [5]
# Look for <90% coverage
# Tell AI: "Need tests for: src/core/pnl_tracker.py"
```

#### Workflow 7: HTML Coverage Reports
```bash
python run_tests.py → [6]
# Opens htmlcov/index.html
# Red = uncovered, Green = covered
```

#### Workflow 8: Debugging Test Failures
```bash
pytest tests/unit/test_file.py -v -s
# Add debug: print(f"DEBUG: {variable}")
```

#### Workflow 9: Pattern-Based Testing
```bash
python run_tests.py → [8]
# Enter pattern: "test_daily"
# Runs all daily loss tests
```

#### Workflow 10: Continuous Testing
```bash
# Before commit:
python run_tests.py → [1]  # All tests
python run_tests.py → [5]  # Coverage
# Share results with AI
```

#### Workflow 11: Runtime Debugging with AI ⭐ NEW
```bash
# Step 1: Run smoke test
python run_tests.py → [s]

# Step 2: Check exit code
# 0 = Success → Deploy
# 1 = Exception → Step 3
# 2 = Stalled → Step 4

# Step 3: Config debugging
AI: "Read test_reports/latest.txt and identify config errors"

# Step 4: Runtime error debugging
AI: "Failed checkpoint: X, explain and fix"

# Step 5: Generate debug report
python run_tests.py → [g]
AI: "Read debug report and provide comprehensive analysis"
```

### AI Integration Patterns

**Pattern 1: Environment Issues**
```
User: "Runtime tests failing with exit code 5"
AI: Read test_reports/latest.txt
AI: Checkpoint 1 failed - missing topstepx_sdk
AI: Fix: pip install topstepx-sdk==1.2.3
```

**Pattern 2: Configuration Errors**
```
User: "Config validation failing"
AI: Read test_reports/latest.txt + config/risk_config.yaml
AI: Invalid value at line 12: limit = 500 (should be -500)
AI: Edit config/risk_config.yaml
```

**Pattern 3: API Connectivity**
```
User: "Checkpoint 4 failing"
AI: Read test_reports/latest.txt + .env
AI: 401 Unauthorized - missing TOPSTEPX_API_KEY
AI: Create .env file with credentials
```

---

## Coverage Requirements

### Targets

- **Minimum Overall**: 90%
- **Critical Paths**: 95%+
- **New Features**: 100%

### Current Coverage

**From test runs**:
```
tests/unit/test_state/test_pnl_tracker.py - Comprehensive coverage
tests/unit/test_core/test_events.py - Event system coverage
tests/unit/test_core/test_enforcement_wiring.py - Integration coverage
```

### Coverage Commands

```bash
# Terminal report
python run_tests.py → [6]

# HTML report
python run_tests.py → [7]
# Opens htmlcov/index.html

# With missing lines
pytest --cov=src --cov-report=term-missing
```

### Coverage Reports Location

- HTML: `htmlcov/index.html`
- Terminal: stdout from pytest
- XML: For CI/CD integration

---

## Evolution of Testing Approach

### Archived Docs vs Current

**Archived** (2025-10-23):
- 5 files (175KB)
- 75% redundancy
- Scattered information
- Pre-consolidation

**Current**:
- 3 files (22KB)
- 0% redundancy
- Single source of truth
- Post-consolidation

### Consolidation Summary

**Before**:
```
docs/
├── AI_ASSISTED_TESTING_WORKFLOW.md (41KB)
├── RUNTIME_INTEGRATION_TESTING.md (42KB)
├── SDK_TESTING_VISUAL_GUIDE.md (33KB)
├── TDD_WORKFLOW_GUIDE.md (30KB)
└── TESTING_METHODOLOGY_ANALYSIS.md (29KB)
Total: 175KB, 5 files
```

**After**:
```
docs/testing/
├── README.md (800B)
├── TESTING_GUIDE.md (12KB) ⭐ Authoritative
├── RUNTIME_DEBUGGING.md (36KB) ⭐ Runtime validation
└── WORKING_WITH_AI.md (9.3KB) ⭐ AI workflows
Total: 58KB, 4 files (including archived)
```

### Content Migration

1. **Agent descriptions** → `.claude/agents/` (5 custom agents)
2. **AI workflow** → `docs/testing/WORKING_WITH_AI.md`
3. **Test reporting** → `docs/testing/TESTING_GUIDE.md`
4. **Mock boundaries** → `docs/testing/TESTING_GUIDE.md`
5. **Integration patterns** → `docs/testing/TESTING_GUIDE.md`
6. **Runtime validation** → `docs/testing/RUNTIME_DEBUGGING.md` (NEW)

### Key Learnings from Evolution

1. **Over-mocking problem identified**:
   - Tests passed but runtime failed
   - Solution: Integration tests + spec-based mocks

2. **Runtime validation gap**:
   - Tests validated logic, not liveness
   - Solution: 8-checkpoint system + smoke tests

3. **AI workflow optimization**:
   - Auto-save reports
   - Clear exit codes
   - Troubleshooting flowcharts

4. **Performance optimization**:
   - WSL2 overhead documented
   - venv direct usage (not `uv run`)
   - Directory-based selection

---

## Test Runner Fixes

### Final Fixes (2025-10-24)

**File**: `TEST_RUNNER_FINAL_FIXES.md`

#### Issue #1: Tests Deselected

**Problem**: `-m unit` and `-m integration` deselected all tests (no decorators)

**Fix**: Use directory paths instead
```python
# OLD: args = ["-m", "unit", "tests/"]
# NEW: args = ["tests/unit/"]
```

**Result**: 23 tests collected (not deselected)

#### Issue #2: Slow Startup

**Problem**: 15-20s startup time

**Root Causes**:
1. `uv run pytest` re-resolves dependencies (~5-10s)
2. WSL2 filesystem overhead (~8-10s unavoidable)

**Fix**: Use venv python directly
```python
venv_python = Path(__file__).parent / ".venv" / "bin" / "python"
if venv_python.exists():
    cmd = [str(venv_python), "-m", "pytest"] + args
```

**Result**: 10-12s startup (40% faster)

#### Performance Comparison

| Action | Before | After | Improvement |
|--------|--------|-------|-------------|
| Menu startup | 15-20s | 10-12s | 40% faster |
| Test collection | Deselected | Collected | ✅ Working |
| Real-time output | Buffered | Streaming | ✅ Fixed |

### Earlier Fixes (2025-10-24)

**File**: `TEST_RUNNER_FIXES.md`

#### Problem 1: Strict Markers

**Fix**: Removed `--strict-markers` from `pyproject.toml`
- Before: Tests without markers deselected
- After: Tests run by default, markers optional

#### Problem 2: Buffered Output

**Fix**: Changed from `subprocess.run()` to `subprocess.Popen()`
```python
# Before: capture_output=True (buffers everything)
# After: Line-by-line streaming with print()
```

---

## Best Practices

### DO

- ✅ Write tests BEFORE implementation (TDD)
- ✅ Use `spec=` on all mocks (catch typos)
- ✅ Test edge cases and errors
- ✅ Keep tests fast (unit <1s)
- ✅ Use parametrize for multiple scenarios
- ✅ Mock at service boundaries only
- ✅ Aim for 90%+ coverage
- ✅ Run smoke test before deployment
- ✅ Check all 8 checkpoints

### DON'T

- ❌ Write code before tests
- ❌ Use mocks without `spec=`
- ❌ Only test happy paths
- ❌ Over-mock (mock internal components)
- ❌ Skip integration tests
- ❌ Ignore failing tests
- ❌ Deploy without smoke test passing
- ❌ Ignore runtime validation

---

## Troubleshooting

### Tests Pass But Runtime Fails

**Symptom**: ✅ Tests green, ❌ Runtime broken

**Diagnosis**:
```bash
# 1. Run smoke test
python run_tests.py → [s]

# 2. Check exit code
# 0 = Working
# 1 = Exception (check logs)
# 2 = Stalled (check subscriptions)

# 3. View logs
python run_tests.py → [l]

# 4. Find stopped checkpoint
# Look for: 🚀 ✅ ✅ ⚠️ ← Stopped at checkpoint 4
```

**Root Causes**:
1. Over-mocking (mocks don't match reality)
2. No integration tests
3. Mocks without `spec=`
4. Not testing error cases
5. Config not loading
6. Logging not working
7. SDK integration mismatch

**Solution**: Read `docs/testing/RUNTIME_DEBUGGING.md`

### Low Coverage

```bash
# Find gaps
pytest --cov=src --cov-report=term-missing

# Add tests for uncovered branches
def test_uncovered_error_path():
    with pytest.raises(ValueError):
        rule.validate(invalid_config)
```

### Slow Tests

```bash
# Skip slow tests in development
pytest -m "not slow"

# Mock expensive operations
@pytest.fixture
def mock_api_client():
    return Mock(spec=APIClient)
```

---

## Quick Reference

### Daily Workflow

**Morning start**:
```bash
python run_tests.py → [s]  # Smoke test
python run_tests.py → [2]  # Unit tests
```

**During development**:
```bash
# Write test first (TDD)
# Implement feature
python run_tests.py → [9]  # Last failed
# Repeat until GREEN
```

**Before commit**:
```bash
python run_tests.py → [s]  # Smoke test
python run_tests.py → [1]  # All tests
python run_tests.py → [5]  # Coverage
```

**Before deployment**:
```bash
python run_tests.py → [e]  # E2E flow
python run_tests.py → [g]  # Gate test
# Must get exit code 0
```

### Test Commands

```bash
# Interactive menu
python run_tests.py

# Direct pytest
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest -m unit
pytest -m "not slow"

# With coverage
pytest --cov=src --cov-report=html

# Specific file
pytest tests/unit/test_state/test_pnl_tracker.py -v

# Pattern match
pytest -k "test_daily"

# Last failed
pytest --lf
```

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | SUCCESS | Deploy ready |
| 1 | EXCEPTION | Check logs |
| 2 | STALLED | Check subscriptions |

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

---

## API Contracts & Integration

### Essential References

**Before writing tests**:
1. `/SDK_API_REFERENCE.md` - Actual API signatures
2. `/SDK_ENFORCEMENT_FLOW.md` - Complete enforcement wiring
3. `/TEST_RUNNER_FINAL_FIXES.md` - Runner behavior

**Common Mistakes Prevented**:
- ❌ `RiskEvent(type=...)` → ✅ `RiskEvent(event_type=...)`
- ❌ `EventType.TRADE_EXECUTED` (doesn't exist) → ✅ Check events.py
- ❌ `PnLTracker(account_id=...)` → ✅ `PnLTracker(db=...)`

---

## Statistics

### Current Implementation

- **Test Files**: 3 unit + 5 runtime = 8 total
- **Test Count**: 23 unit + 70 runtime = 93 total
- **Documentation**: 4 testing guides (58KB total)
- **Archived Docs**: 5 files (175KB) consolidated to 3 (22KB)
- **Source Code**: 1,316 lines runtime + test infrastructure
- **Menu Options**: 20+ test runner commands
- **Coverage Target**: 90% overall, 95% critical paths

### Missing Components

- ❌ Integration tests (planned, not implemented)
- ❌ E2E tests (planned, not implemented)
- ❌ Rule-specific unit tests (only PnLTracker done)

### Strengths

- ✅ Comprehensive runtime validation (8 checkpoints)
- ✅ Interactive test runner with AI integration
- ✅ Auto-save reporting system
- ✅ TDD workflow documented and used
- ✅ Real database testing (temp_db fixture)
- ✅ Clear troubleshooting guides
- ✅ Performance optimizations documented

---

## Next Steps

### Immediate

1. Create `/tests/integration/` directory
2. Add `spec=` to all mocks in conftest.py
3. Write first smoke test
4. Document integration test patterns

### Short Term

5. Test critical paths (event flow end-to-end)
6. Add logging validation tests
7. Test database persistence
8. Add factory fixtures

### Long Term

9. Increase integration coverage (50+ tests)
10. Add E2E tests (full workflows)
11. CI/CD integration
12. Performance regression testing

---

**Last Updated**: 2025-10-25
**Status**: Comprehensive inventory complete
**Coverage**: All testing infrastructure documented
**Evolution**: Consolidation from 5 files to 3 documented
