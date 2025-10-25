# Testing Integration Foundation

**Complete testing workflow integrated with implementation**

**Authority**: THE testing integration guide
**Last Updated**: 2025-10-25
**Status**: Foundation Document

---

## Purpose

This document shows how testing integrates with every aspect of the development workflow:
- TDD (Test-Driven Development)
- Implementation (IMPLEMENTATION_ROADMAP.md)
- Runtime validation (RUNTIME_VALIDATION_INTEGRATION.md)
- Progress tracking
- Quality assurance

**Key Principle**: Tests are not optional. They are the foundation of every feature.

---

## The Testing Ecosystem

### Components Overview

```
┌─────────────────────────────────────────────────────┐
│                TESTING ECOSYSTEM                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. TDD Workflow       Write tests FIRST            │
│  2. Test Runner        Interactive menu             │
│  3. Test Reports       Auto-save results            │
│  4. Runtime Validation Smoke tests                  │
│  5. Coverage           Track completeness           │
│  6. Progress Tracking  Update roadmap               │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Component Details

**1. TDD Workflow**
- Location: Core development practice
- Purpose: Write tests before implementation
- Pattern: RED → GREEN → REFACTOR → SMOKE
- Enforced: Every feature, no exceptions

**2. Test Runner**
- Location: `/mnt/c/Users/jakers/Desktop/risk-manager-v34/run_tests.py`
- Purpose: Interactive menu for running tests
- Outputs: Auto-saves to `test_reports/latest.txt`
- Integration: Used at every step

**3. Test Reports**
- Location: `/mnt/c/Users/jakers/Desktop/risk-manager-v34/test_reports/`
- Purpose: Persistent test results
- Format: Pytest output with tracebacks
- Usage: Agents read `latest.txt` for results

**4. Runtime Validation**
- Location: `/mnt/c/Users/jakers/Desktop/risk-manager-v34/src/runtime/`
- Purpose: Prove system is alive
- Key Test: Smoke test (8s boot validation)
- Exit Codes: 0=pass, 1=exception, 2=stalled

**5. Coverage**
- Tool: pytest-cov
- Target: 90%+ for core modules
- Current: 18% (from PROJECT_STATUS.md)
- Tracking: Per-module in IMPLEMENTATION_ROADMAP.md

**6. Progress Tracking**
- Location: `docs/foundation/IMPLEMENTATION_ROADMAP.md`
- Updates: After each feature completes
- Format: `[x]` when all tests pass + smoke passes

---

## Complete Implementation Workflow

### The Full Cycle

```
┌──────────────────────────────────────────────────────┐
│  STEP 1: Pick Feature from Roadmap                   │
│  └─ Read IMPLEMENTATION_ROADMAP.md                   │
│  └─ Find [ ] task                                    │
│  └─ Note feature requirements                        │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│  STEP 2: Write Tests FIRST (TDD - RED)               │
│  └─ Create tests/unit/test_[module]/test_[feat].py  │
│  └─ Write test cases (AAA pattern)                   │
│  └─ Run: python run_tests.py → [2] Unit             │
│  └─ Check: test_reports/latest.txt (should fail)    │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│  STEP 3: Implement Feature (GREEN)                   │
│  └─ Implement: src/[module]/[feature].py            │
│  └─ Run: python run_tests.py → [2] Unit             │
│  └─ Check: test_reports/latest.txt (should pass)    │
│  └─ Refactor if needed                               │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│  STEP 4: Integration Tests (if SDK/DB involved)      │
│  └─ Create tests/integration/test_[feature].py      │
│  └─ Run: python run_tests.py → [3] Integration      │
│  └─ Check: test_reports/latest.txt                  │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│  STEP 5: Smoke Test (MANDATORY)                      │
│  └─ Run: python run_tests.py → [s] Smoke            │
│  └─ Wait: 8 seconds                                  │
│  └─ Check: Exit code (0=pass, 1/2=fail)             │
│  └─ If fail: See RUNTIME_VALIDATION_INTEGRATION.md  │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│  STEP 6: Update Progress                             │
│  └─ Update IMPLEMENTATION_ROADMAP.md → [x]          │
│  └─ Git commit: "Implemented [feature]"             │
│  └─ Update coverage % if significant                 │
└──────────────────────────────────────────────────────┘
```

---

## Detailed Step-by-Step Guide

### Step 1: Pick Feature from Roadmap

**File**: `docs/foundation/IMPLEMENTATION_ROADMAP.md`

**What to do**:
1. Find next uncompleted task `[ ]`
2. Read feature requirements
3. Check dependencies (must complete in order)
4. Note acceptance criteria

**Example**:
```markdown
### RULE-003: Daily Realized Loss Limit
- [ ] Unit tests (15 tests)
- [ ] Integration tests (3 tests)
- [ ] Smoke test passes
- [ ] Coverage: 90%+
```

**Before starting**: Verify all dependencies are complete

---

### Step 2: Write Tests FIRST (TDD - RED Phase)

**Principle**: Test-Driven Development is mandatory

#### Create Test File

**Location**: `tests/unit/test_rules/test_daily_realized_loss.py`

**Template**:
```python
import pytest
from datetime import date
from risk_manager.rules.daily_realized_loss import DailyRealizedLoss
from risk_manager.core.events import RiskEvent, EventType

class TestDailyRealizedLossEvaluation:
    """Test evaluation logic"""

    @pytest.mark.asyncio
    async def test_not_violated_no_trades(self, rule_003, mock_pnl_tracker):
        """No trades today = not violated"""
        # Arrange
        mock_pnl_tracker.get_daily_pnl.return_value = 0.0
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATE,
            account_id="ACC123",
            instrument="ES",
            timestamp=datetime.now()
        )

        # Act
        result = await rule_003.evaluate(event)

        # Assert
        assert result is False
        mock_pnl_tracker.get_daily_pnl.assert_called_once()

    @pytest.mark.asyncio
    async def test_violated_exceeds_limit(self, rule_003, mock_pnl_tracker):
        """Loss > $100 = violated"""
        # Arrange
        mock_pnl_tracker.get_daily_pnl.return_value = -150.0
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATE,
            account_id="ACC123",
            instrument="ES",
            timestamp=datetime.now()
        )

        # Act
        result = await rule_003.evaluate(event)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_not_violated_at_exactly_limit(self, rule_003, mock_pnl_tracker):
        """Loss = $100 exactly = not violated"""
        # Arrange
        mock_pnl_tracker.get_daily_pnl.return_value = -100.0
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATE,
            account_id="ACC123",
            instrument="ES",
            timestamp=datetime.now()
        )

        # Act
        result = await rule_003.evaluate(event)

        # Assert
        assert result is False  # At limit, not over

class TestDailyRealizedLossEnforcement:
    """Test enforcement actions"""

    @pytest.mark.asyncio
    async def test_enforce_closes_all_positions(self, rule_003, mock_suite):
        """Enforcement must close all positions"""
        # Arrange
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATE,
            account_id="ACC123",
            instrument="ES",
            timestamp=datetime.now()
        )

        # Act
        await rule_003.enforce(event)

        # Assert
        mock_suite.close_all_positions.assert_called_once()

    @pytest.mark.asyncio
    async def test_enforce_triggers_lockout(self, rule_003, mock_lockout_manager):
        """Enforcement must trigger lockout"""
        # Arrange
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATE,
            account_id="ACC123",
            instrument="ES",
            timestamp=datetime.now()
        )

        # Act
        await rule_003.enforce(event)

        # Assert
        mock_lockout_manager.lock_account.assert_called_once_with("ACC123")

# 15 total tests for RULE-003
```

#### Run Tests (Expect Failures)

**Command**:
```bash
python run_tests.py
# Select: [2] Unit tests
```

**Expected Result**: Tests FAIL (RED phase)

**Check Results**:
```bash
cat test_reports/latest.txt
```

**Should see**:
```
FAILED tests/unit/test_rules/test_daily_realized_loss.py::test_not_violated_no_trades
ModuleNotFoundError: No module named 'risk_manager.rules.daily_realized_loss'
```

**This is CORRECT** - Tests written before implementation

---

### Step 3: Implement Feature (GREEN Phase)

**Create Implementation**

**File**: `src/risk_manager/rules/daily_realized_loss.py`

**Template**:
```python
from typing import Optional
from datetime import date
from risk_manager.rules.base import BaseRule
from risk_manager.core.events import RiskEvent
from risk_manager.state.pnl_tracker import PnLTracker
from risk_manager.sdk.suite_manager import SuiteManager

class DailyRealizedLoss(BaseRule):
    """RULE-003: Daily Realized Loss Limit"""

    def __init__(
        self,
        config: dict,
        pnl_tracker: PnLTracker,
        lockout_manager,
        suite: SuiteManager
    ):
        super().__init__(config)
        self.pnl_tracker = pnl_tracker
        self.lockout_manager = lockout_manager
        self.suite = suite
        self.limit = config.get("limit", 100.0)

    async def evaluate(self, event: RiskEvent) -> bool:
        """Check if daily realized loss exceeds limit"""
        daily_pnl = self.pnl_tracker.get_daily_pnl(
            account_id=event.account_id,
            date=date.today()
        )

        # Violated if loss > limit (negative PnL)
        return daily_pnl < -self.limit

    async def enforce(self, event: RiskEvent) -> None:
        """Close all positions and lock account"""
        # Close all positions via SDK
        await self.suite.close_all_positions()

        # Trigger lockout
        self.lockout_manager.lock_account(event.account_id)
```

#### Run Tests (Expect Success)

**Command**:
```bash
python run_tests.py
# Select: [2] Unit tests
```

**Expected Result**: Tests PASS (GREEN phase)

**Check Results**:
```bash
cat test_reports/latest.txt
```

**Should see**:
```
tests/unit/test_rules/test_daily_realized_loss.py ............... PASSED

======================== 15 passed in 2.34s ========================
```

#### Refactor (If Needed)

- Improve code quality
- Add comments/docstrings
- Extract common logic
- Re-run tests after each refactor

**Tests must stay GREEN during refactoring**

---

### Step 4: Integration Tests (If SDK/DB Involved)

**When to write integration tests**:
- Feature uses SDK (TradingSuite)
- Feature uses database (SQLite)
- Feature integrates multiple components
- Feature has complex async behavior

**Example**: RULE-003 enforcement with real SDK

**File**: `tests/integration/test_rule_003_enforcement.py`

**Template**:
```python
import pytest
from risk_manager.rules.daily_realized_loss import DailyRealizedLoss
from risk_manager.core.events import RiskEvent, EventType
from datetime import datetime

@pytest.mark.integration
@pytest.mark.asyncio
async def test_rule_003_full_enforcement_flow(
    real_suite,
    real_pnl_tracker,
    real_lockout_manager
):
    """Test complete enforcement flow with real SDK"""

    # Arrange
    config = {"limit": 100.0}
    rule = DailyRealizedLoss(
        config=config,
        pnl_tracker=real_pnl_tracker,
        lockout_manager=real_lockout_manager,
        suite=real_suite
    )

    # Simulate daily loss of $150
    real_pnl_tracker.record_trade(
        account_id="ACC123",
        instrument="ES",
        pnl=-150.0,
        timestamp=datetime.now()
    )

    event = RiskEvent(
        event_type=EventType.POSITION_UPDATE,
        account_id="ACC123",
        instrument="ES",
        timestamp=datetime.now()
    )

    # Act - Evaluate
    violated = await rule.evaluate(event)

    # Assert - Should be violated
    assert violated is True

    # Act - Enforce
    await rule.enforce(event)

    # Assert - Positions closed
    positions = await real_suite.get_positions()
    assert len(positions) == 0

    # Assert - Account locked
    assert real_lockout_manager.is_locked("ACC123") is True
```

#### Run Integration Tests

**Command**:
```bash
python run_tests.py
# Select: [3] Integration tests
```

**Check Results**:
```bash
cat test_reports/latest.txt
```

**Note**: Integration tests may fail if SDK connection unavailable. That's OK during development.

---

### Step 5: Smoke Test (MANDATORY)

**Purpose**: Prove the system boots and is alive

**What smoke test validates**:
1. Service starts without crashing
2. Config loads
3. SDK connects
4. Rules initialize
5. Event loop runs
6. **First event fires within 8 seconds** ← Key validation

**Run Smoke Test**:
```bash
python run_tests.py
# Select: [s] Runtime SMOKE
```

**Wait**: 8 seconds

**Check Exit Code**:
- **0** = Success (system is alive)
- **1** = Exception (check logs)
- **2** = Boot stalled (no events)

#### If Smoke Test Fails

**See**: `docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md`

**Quick troubleshooting**:

**Exit Code 1 (Exception)**:
```bash
# View logs
python run_tests.py → [l]

# Look for stack trace
# Fix the exception
# Re-run smoke test
```

**Exit Code 2 (Stalled)**:
```bash
# Check which checkpoint failed
cat data/logs/risk_manager.log | tail -20

# Look for last emoji:
# 🚀 ✅ ✅ ✅ ✅ 📨 🔍 ⚠️
#         ^^^ Stopped here

# If stopped at Checkpoint 6 (📨 Event Received):
# → Event subscriptions not working
# → Check SDK event handlers
```

**Complete protocol**: See RUNTIME_VALIDATION_INTEGRATION.md Section 4

---

### Step 6: Update Progress

**After all tests pass + smoke test passes**:

#### Update Roadmap

**File**: `docs/foundation/IMPLEMENTATION_ROADMAP.md`

**Change**:
```markdown
### RULE-003: Daily Realized Loss Limit
- [ ] Unit tests (15 tests)
- [ ] Integration tests (3 tests)
- [ ] Smoke test passes
- [ ] Coverage: 90%+
```

**To**:
```markdown
### RULE-003: Daily Realized Loss Limit
- [x] Unit tests (15 tests) ✅
- [x] Integration tests (3 tests) ✅
- [x] Smoke test passes ✅
- [x] Coverage: 92% ✅
```

#### Git Commit

```bash
git add .
git commit -m "$(cat <<'EOF'
Implement RULE-003: Daily Realized Loss Limit

- Add DailyRealizedLoss rule class
- Add 15 unit tests (all passing)
- Add 3 integration tests (all passing)
- Smoke test: Exit code 0
- Coverage: 92%

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Test Types & Requirements

### Testing Pyramid

```
        /\
       /E2E\        10% - Full workflows
      /------\      Target: 15 tests
     /  Integ \     30% - SDK + DB integration
    /----------\    Target: 45 tests
   / Unit Tests \   60% - Fast, isolated
  /--------------\  Target: 90 tests

  Total: 150 tests (from PROJECT_STATUS.md)
```

### Unit Tests (60% - 90 tests)

**Purpose**: Test individual functions/methods in isolation

**Characteristics**:
- Fast (<1s total)
- No external dependencies (mocked)
- No SDK, no database, no network
- Test business logic only

**Coverage Target**: 90%+ for all core modules

**When to write**:
- EVERY function/method
- EVERY class
- EVERY rule
- EVERY manager
- EVERY state handler

**Example modules needing unit tests**:
```
src/risk_manager/rules/
  ├── daily_realized_loss.py         → 15 tests
  ├── max_position.py                → 12 tests
  ├── max_contracts_per_instrument.py → 10 tests
  └── ... (9 more rules)             → ~120 tests total

src/risk_manager/state/
  ├── pnl_tracker.py                 → 20 tests
  ├── database.py                    → 15 tests
  └── lockout_manager.py             → 10 tests

src/risk_manager/core/
  ├── manager.py                     → 25 tests
  ├── engine.py                      → 20 tests
  ├── events.py                      → 10 tests
  └── config.py                      → 12 tests
```

**Test structure** (AAA pattern):
```python
def test_function_name_scenario():
    """Clear description of what's being tested"""
    # Arrange - Setup test data
    # Act - Execute the function
    # Assert - Verify the result
```

**Fixtures** (reusable test setup):
```python
# tests/conftest.py

@pytest.fixture
def rule_003(mock_pnl_tracker, mock_lockout_manager, mock_suite):
    """Fixture for RULE-003 with mocked dependencies"""
    config = {"limit": 100.0}
    return DailyRealizedLoss(
        config=config,
        pnl_tracker=mock_pnl_tracker,
        lockout_manager=mock_lockout_manager,
        suite=mock_suite
    )

@pytest.fixture
def mock_pnl_tracker():
    """Mock PnLTracker"""
    return Mock(spec=PnLTracker)
```

---

### Integration Tests (30% - 45 tests)

**Purpose**: Test component interaction with real dependencies

**Characteristics**:
- Slower (5-10s total)
- Real SDK connection
- Real database (SQLite in test mode)
- Test integration, not just logic

**Coverage Target**: All major flows with external systems

**When to write**:
- Feature uses SDK (TradingSuite)
- Feature uses database
- Feature integrates multiple components
- Feature has async event handling

**Example scenarios**:
```python
# tests/integration/test_rule_enforcement.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_rule_003_closes_positions_via_sdk():
    """RULE-003 enforcement closes positions via real SDK"""
    # Real SDK connection
    # Real database
    # Trigger violation
    # Verify SDK called close_all_positions()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pnl_tracker_persists_to_database():
    """PnLTracker writes to real database"""
    # Real database connection
    # Record trades
    # Query database directly
    # Verify data persisted

@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_engine_processes_sdk_events():
    """Event engine receives and processes real SDK events"""
    # Real SDK connection
    # Subscribe to events
    # Trigger SDK event
    # Verify engine received and processed
```

**Markers**:
```python
@pytest.mark.integration  # Mark as integration test
@pytest.mark.asyncio      # Required for async tests
@pytest.mark.slow         # Mark if test takes >5s
```

**Run integration tests**:
```bash
python run_tests.py → [3] Integration tests
```

---

### E2E Tests (10% - 15 tests)

**Purpose**: Test complete user workflows end-to-end

**Characteristics**:
- Slowest (30s+ total)
- Full system running
- Real SDK, real database
- Simulate complete scenarios

**Coverage Target**: All critical user journeys

**When to write**:
- Complete violation workflow (trade → violation → enforcement → lockout)
- Complete startup workflow (boot → config → SDK → events)
- Complete recovery workflow (lockout → admin reset → trading resumes)

**Example scenarios**:
```python
# tests/e2e/test_violation_flow.py

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_daily_loss_violation_full_flow():
    """Complete flow from trading to lockout"""

    # Step 1: Start system
    manager = RiskManager(config_path="config/test_config.yaml")
    await manager.start()

    # Step 2: Simulate trades that trigger RULE-003
    # (Use SDK to place trades, SDK fires events)
    await suite.place_order(...)  # Trade 1: -$60
    await suite.place_order(...)  # Trade 2: -$50
    # Total: -$110 (violates $100 limit)

    # Step 3: Wait for event processing
    await asyncio.sleep(2)

    # Step 4: Verify enforcement actions
    # All positions closed via SDK
    positions = await suite.get_positions()
    assert len(positions) == 0

    # Account locked
    assert lockout_manager.is_locked("ACC123")

    # Step 5: Verify lockout persists
    # Try to place order (should be rejected)
    result = await suite.place_order(...)
    assert result.status == "REJECTED"

    # Step 6: Verify trader CLI shows lockout
    cli_output = trader_cli.get_status()
    assert "LOCKED" in cli_output

    # Cleanup
    await manager.stop()
```

**Run E2E tests**:
```bash
python run_tests.py → [4] E2E tests
```

---

### Runtime Validation Tests (Smoke/Soak/Trace)

**See**: `docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md`

**Purpose**: Prove system is ALIVE (not just logically correct)

**Types**:

**Smoke Test** (8s):
- Boots system
- Validates first event fires
- Exit codes: 0=pass, 1=exception, 2=stalled
- Run: `python run_tests.py → [s]`

**Soak Test** (30-60s):
- Extended runtime
- Catches memory leaks, deadlocks
- Run: `python run_tests.py → [r]`

**Trace Test** (with ASYNC_DEBUG=1):
- Deep async debugging
- Shows all pending tasks
- Run: `python run_tests.py → [t]`

**When to run**:
- After every feature implementation (smoke)
- Before deployment (smoke + soak)
- When runtime hangs (trace)

---

## Test Runner Integration

### Interactive Menu

**Command**: `python run_tests.py`

**Menu Structure**:
```
Test Selection:
  [1] Run ALL tests
  [2] Run UNIT tests only          ← Use this most
  [3] Run INTEGRATION tests only
  [4] Run E2E tests only
  [5] Run SLOW tests only
  [6] Run with COVERAGE report
  [7] Run with COVERAGE + HTML
  [8] Run specific test file
  [9] Run tests matching keyword
  [0] Run last failed tests only

Runtime Checks:
  [s] Runtime SMOKE                 ← MANDATORY before marking complete
  [r] Runtime SOAK
  [t] Runtime TRACE
  [l] View/Tail LOGS
  [e] Env/Config SNAPSHOT
  [g] GATE: Tests + Smoke combo     ← Ultimate validation

Utilities:
  [v] Run in VERBOSE mode
  [c] Check COVERAGE status
  [p] View last test REPORT
  [h] Help
  [q] Quit
```

### Auto-Save Reports

**Every test run automatically saves to**:

**Primary**:
- `test_reports/latest.txt` - Always most recent (overwritten)

**Archives**:
- `test_reports/2025-10-25_14-30-45_passed.txt` - Timestamped successes
- `test_reports/2025-10-25_14-32-18_failed.txt` - Timestamped failures

**Usage**:
```bash
# User runs tests
python run_tests.py → [2]

# Report auto-saves to test_reports/latest.txt

# Agent reads results
cat test_reports/latest.txt

# Contains:
# - Full pytest output (with colors)
# - Pass/fail status
# - Exit code
# - Complete tracebacks for failures
# - Warnings
# - Summary statistics
```

### Reading Test Results

**File**: `test_reports/latest.txt`

**Format**:
```
======================== test session starts ========================
platform linux -- Python 3.12.0, pytest-8.3.4
rootdir: /mnt/c/Users/jakers/Desktop/risk-manager-v34
plugins: asyncio-0.24.0, cov-6.0.0
collected 45 items

tests/unit/test_rules/test_daily_realized_loss.py ............... PASSED
tests/unit/test_state/test_pnl_tracker.py ...................... PASSED

======================== 45 passed in 2.34s =========================

Exit Code: 0
Timestamp: 2025-10-25 14:30:45
```

**If failures**:
```
FAILED tests/unit/test_rules/test_daily_realized_loss.py::test_violated

================================ FAILURES ================================
______________ test_violated ______________

    def test_violated():
>       assert daily_pnl < -limit
E       AssertionError: assert -90.0 < -100.0
E        +  where -90.0 = get_daily_pnl()

tests/unit/test_rules/test_daily_realized_loss.py:45: AssertionError
======================== 1 failed, 44 passed in 2.56s =================

Exit Code: 1
Timestamp: 2025-10-25 14:32:18
```

**Agents can read this file directly**:
```bash
cat test_reports/latest.txt
```

---

## Coverage Integration

### Current Status

**Overall**: 18% (from PROJECT_STATUS.md)
**Target**: 90%+ for core modules
**Tracking**: Per-module in IMPLEMENTATION_ROADMAP.md

### Per-Module Targets

**From PROJECT_STATUS.md**:
```
Risk Rules:         90%+ (currently ~30%)
State Managers:     90%+ (currently ~20%)
SDK Integration:    80%+ (currently ~15%)
Event System:       90%+ (currently ~25%)
CLI:                70%+ (currently ~10%)
```

### Check Coverage

**Command**:
```bash
python run_tests.py
# Select: [6] Coverage report
# Or: [7] Coverage + HTML
```

**Output**:
```
Name                                      Stmts   Miss  Cover
-------------------------------------------------------------
src/risk_manager/__init__.py                 10      2    80%
src/risk_manager/core/manager.py            150     45    70%
src/risk_manager/core/engine.py             120     30    75%
src/risk_manager/rules/daily_realized_loss.py 50     5    90%
src/risk_manager/state/pnl_tracker.py        80     60    25%
-------------------------------------------------------------
TOTAL                                      1200    850    29%
```

**HTML Report**:
```bash
# After running [7]
# Open: htmlcov/index.html
```

### Update Roadmap with Coverage

**When to update**:
- After implementing each major feature
- After writing significant tests
- Before marking feature complete

**Example**:
```markdown
### RULE-003: Daily Realized Loss Limit
- [x] Unit tests (15 tests) ✅
- [x] Integration tests (3 tests) ✅
- [x] Coverage: 92% ✅  ← Update this
```

---

## Test Failure Debugging

### Unit Test Failures

**Workflow**:

**1. Read Test Report**:
```bash
cat test_reports/latest.txt
```

**2. Identify Failure**:
```
FAILED tests/unit/test_rules/test_daily_realized_loss.py::test_violated

    def test_violated():
>       result = await rule.evaluate(event)
E       TypeError: evaluate() missing 1 required positional argument: 'event'
```

**3. Common Issues**:

**Wrong Parameter Names**:
```python
# Wrong (from old specs)
RiskEvent(type=EventType.TRADE_EXECUTED)

# Correct (actual API)
RiskEvent(event_type=EventType.TRADE_EXECUTED)
```

**Solution**: Check `SDK_API_REFERENCE.md` for actual signatures

**Missing Mocks**:
```python
# Wrong - using real object
def test_something():
    tracker = PnLTracker(db=real_db)  # Fails - no real DB

# Correct - using mock
def test_something(mock_pnl_tracker):
    tracker = mock_pnl_tracker  # Works - mocked
```

**Async/Await Issues**:
```python
# Wrong - missing await
def test_something():
    result = rule.evaluate(event)  # Returns coroutine, not result

# Correct
async def test_something():
    result = await rule.evaluate(event)  # Awaits coroutine
```

**4. Fix and Re-run**:
```bash
# Fix the code
# Re-run tests
python run_tests.py → [2]

# Check results
cat test_reports/latest.txt
```

---

### Integration Test Failures

**Common issues**:

**SDK Connection Failed**:
```
FAILED tests/integration/test_rule_enforcement.py::test_rule_003
E   ConnectionError: Cannot connect to SDK
```

**Solution**:
- Check `test_connection.py` works
- Verify SDK credentials
- Check network connection

**Database Issues**:
```
FAILED tests/integration/test_pnl_tracker.py::test_persist
E   sqlite3.OperationalError: database is locked
```

**Solution**:
- Use test database (not production)
- Close connections properly
- Use fixtures for DB setup/teardown

**Async Timing Issues**:
```
FAILED tests/integration/test_events.py::test_event_received
E   AssertionError: Event not received
```

**Solution**:
```python
# Add appropriate wait
await asyncio.sleep(2)  # Allow time for event processing
```

---

### Smoke Test Failures

**See**: `docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md` Section 4

**Quick reference**:

**Exit Code 1 (Exception)**:
```bash
# View logs
python run_tests.py → [l]

# Find exception
# Fix it
# Re-run smoke
```

**Exit Code 2 (Stalled)**:
```bash
# Check which checkpoint failed
cat data/logs/risk_manager.log | grep "🚀\|✅\|📨"

# Troubleshoot based on last checkpoint
```

**Complete protocol**: See RUNTIME_VALIDATION_INTEGRATION.md

---

## Integration with Roadmap

### Feature Completion Checklist

**Every feature in IMPLEMENTATION_ROADMAP.md must have**:

```markdown
### [Feature Name]
- [ ] Unit tests written and passing
- [ ] Integration tests (if SDK/DB involved)
- [ ] E2E tests (if complete workflow)
- [ ] Smoke test passing (exit code 0) ← MANDATORY
- [ ] Coverage meets target (90%+)
- [ ] Mark complete [x]
```

**Cannot mark feature complete unless ALL boxes checked**

### Example: RULE-003 Complete

**Before**:
```markdown
### RULE-003: Daily Realized Loss Limit
- [ ] Unit tests (15 tests)
- [ ] Integration tests (3 tests)
- [ ] Smoke test passes
- [ ] Coverage: 90%+
```

**After**:
```markdown
### RULE-003: Daily Realized Loss Limit
- [x] Unit tests (15 tests) ✅
- [x] Integration tests (3 tests) ✅
- [x] Smoke test passes ✅
- [x] Coverage: 92% ✅
```

**Git commit**:
```bash
git commit -m "Complete RULE-003: Daily Realized Loss Limit"
```

---

## CI/CD Integration (Future)

### Planned GitHub Actions

**Status**: Not implemented yet
**Priority**: Medium (after core features complete)

**Workflow** (planned):
```yaml
# .github/workflows/test.yml

name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run unit tests
        run: pytest -m unit

      - name: Run integration tests
        run: pytest -m integration

      - name: Run smoke test
        run: python src/runtime/smoke_test.py

      - name: Check coverage
        run: pytest --cov --cov-fail-under=80

      - name: Block merge if any fail
        if: failure()
        run: exit 1
```

**Benefits**:
- Automated testing on every push
- Block merge if tests fail
- Block merge if coverage < 80%
- Block merge if smoke test fails

**Implementation**: After Phase 1 complete (12 rules working)

---

## Definition of Done (Testing Perspective)

### Feature is Complete When

**1. Unit Tests**:
- ✅ Written FIRST (TDD)
- ✅ All passing
- ✅ Coverage: 90%+ for core modules
- ✅ Saved in test_reports/latest.txt

**2. Integration Tests** (if SDK/DB involved):
- ✅ Written and passing
- ✅ Real SDK connection tested
- ✅ Real database tested

**3. E2E Tests** (if complete workflow):
- ✅ Written and passing
- ✅ Complete user journey validated

**4. Smoke Test** (MANDATORY):
- ✅ Exit code 0 (system alive)
- ✅ First event fires within 8s
- ✅ All 8 checkpoints log correctly

**5. Coverage**:
- ✅ Meets per-module target
- ✅ Updated in IMPLEMENTATION_ROADMAP.md

**6. Documentation**:
- ✅ Roadmap updated with [x]
- ✅ Git commit with clear message

**Cannot skip ANY step**

---

## Success Metrics

### Agent Behavior Goals

**TDD Enforcement**:
- ✅ Agents write tests FIRST (RED phase)
- ✅ Agents implement code SECOND (GREEN phase)
- ✅ Agents refactor while keeping tests green
- ✅ Agents run smoke test BEFORE marking complete

**Test Runner Usage**:
- ✅ Agents use interactive menu correctly
- ✅ Agents read test_reports/latest.txt for results
- ✅ Agents understand exit codes (0/1/2)
- ✅ Agents can debug failures from reports

**Coverage Tracking**:
- ✅ Agents check coverage before marking complete
- ✅ Agents update IMPLEMENTATION_ROADMAP.md with %
- ✅ Agents don't deploy with <80% coverage

**Runtime Validation**:
- ✅ Agents run smoke test after implementation
- ✅ Agents troubleshoot using 8-checkpoint logs
- ✅ Agents use RUNTIME_VALIDATION_INTEGRATION.md protocol

### Quality Metrics

**From PROJECT_STATUS.md**:

**Current**:
- Tests: 70 (50 runtime + 15 unit + 5 integration)
- Coverage: 18%
- Smoke test: Exit code 0

**Target**:
- Tests: 150 (90 unit + 45 integration + 15 E2E)
- Coverage: 90%+
- Smoke test: Always exit code 0

**Progress tracked in**: IMPLEMENTATION_ROADMAP.md

---

## Quick Reference

### Essential Commands

```bash
# Run tests (most common)
python run_tests.py → [2] Unit tests

# Check results
cat test_reports/latest.txt

# Run smoke test (mandatory)
python run_tests.py → [s] Smoke test

# View logs (if failures)
python run_tests.py → [l] Logs

# Check coverage
python run_tests.py → [6] Coverage

# Ultimate validation
python run_tests.py → [g] Gate test
```

### Essential Files

```
CLAUDE.md                           - Start here
docs/foundation/IMPLEMENTATION_ROADMAP.md  - What to build
docs/foundation/TESTING_INTEGRATION.md     - How to test (this file)
docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md  - How to validate runtime
test_reports/latest.txt             - Latest test results
SDK_API_REFERENCE.md                - Actual API contracts
```

### Test Workflow Summary

```
1. Pick task from IMPLEMENTATION_ROADMAP.md
2. Write tests FIRST (RED)
3. Implement code (GREEN)
4. Refactor (stay GREEN)
5. Run smoke test (exit code 0)
6. Update IMPLEMENTATION_ROADMAP.md [x]
7. Git commit
```

### Exit Codes

```
0 = Success (all good)
1 = Exception (check logs)
2 = Stalled (check checkpoints)
```

---

## Document Status

**Created**: 2025-10-25
**Last Updated**: 2025-10-25
**Status**: Foundation Document
**Authority**: THE testing integration guide

**Dependencies**:
- `docs/foundation/IMPLEMENTATION_ROADMAP.md` - What to build
- `docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md` - Runtime protocol
- `docs/foundation/CONTRACTS_REFERENCE.md` - API contracts
- `SDK_API_REFERENCE.md` - SDK contracts

**Next Updates**:
- When CI/CD implemented
- When coverage reaches 50%
- When test count reaches 150

---

**This is the complete testing integration guide. All testing workflows reference this document.**
