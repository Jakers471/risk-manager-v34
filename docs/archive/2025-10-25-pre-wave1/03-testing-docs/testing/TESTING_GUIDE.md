# Testing Guide - Simple Risk Manager

**THE authoritative testing reference for this project.**

---

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest -m slow              # Slow tests only
```

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures & configuration
├── fixtures/                # Test data
│   ├── accounts.py
│   ├── orders.py
│   ├── positions.py
│   └── trades.py
├── unit/                    # Fast, isolated tests
│   ├── rules/
│   └── test_*.py
└── integration/             # Component interaction tests
    └── test_*.py
```

## TDD Workflow (Test-Driven Development)

**ALWAYS write tests BEFORE implementation:**

### Red-Green-Refactor Cycle

1. **RED**: Write failing test
   ```python
   def test_daily_loss_limit():
       """Test that rule triggers at loss limit"""
       rule = DailyRealizedLossRule(limit=-500)
       result = rule.check(trade_with_loss(-500))
       assert result is not None  # ❌ FAILS - not implemented yet
   ```

2. **GREEN**: Write minimal code to pass
   ```python
   class DailyRealizedLossRule:
       def check(self, trade):
           if trade.pnl <= self.limit:
               return RuleBreach(...)
   ```

3. **REFACTOR**: Improve code quality
   - Extract methods
   - Remove duplication
   - Optimize performance
   - Tests still pass ✅

## Writing Tests

### ⚠️ BEFORE Writing Tests - Check API Contracts!

**CRITICAL**: Always verify actual API signatures to prevent test/code mismatches!

**Common Test Mistakes**:
- ❌ Using `RiskEvent(type=...)` → ✅ Use `RiskEvent(event_type=...)`
- ❌ Assuming `EventType.TRADE_EXECUTED` exists → ✅ Check `events.py` first!
- ❌ Using `PnLTracker(account_id=...)` → ✅ Use `PnLTracker(db=...)`
- ❌ Forgetting `await` on async methods → ✅ Make test `async` and use `await`

**See**: `SDK_API_REFERENCE.md` (root directory) for all actual API contracts

### AAA Pattern (Arrange-Act-Assert)

```python
def test_position_update():
    # ARRANGE - Set up test data
    position = Position(symbol="MNQ", size=1, price=15000)
    trade = Trade(symbol="MNQ", pnl=-50)

    # ACT - Execute the behavior
    result = position.update(trade)

    # ASSERT - Verify outcomes
    assert result.pnl == -50
    assert result.size == 0
```

### Given-When-Then Pattern (BDD Style)

Use for business logic and rules:

```python
def test_daily_loss_breach():
    """
    GIVEN: Daily loss limit of -$500
    WHEN: Trade pushes total loss to -$501
    THEN: Rule triggers breach and locks out account
    """
    # Given
    rule = DailyRealizedLossRule(limit=-500)
    pnl_tracker.daily_loss = -400

    # When
    result = rule.check(trade_with_loss(-101))

    # Then
    assert result.action == "LOCKOUT"
    assert result.severity == "CRITICAL"
```

## Test Markers

Categorize tests for selective execution:

```python
@pytest.mark.unit        # Fast unit test
@pytest.mark.integration # Integration test
@pytest.mark.slow        # Takes >1 second
@pytest.mark.requires_api  # Needs TopstepX API
@pytest.mark.requires_db   # Needs database

# Run specific categories
pytest -m unit           # Only unit tests
pytest -m "not slow"     # Skip slow tests
pytest -m "unit and not slow"  # Fast unit tests
```

## Fixtures

### Using Existing Fixtures

```python
def test_with_fixtures(single_mnq_long_position, filled_buy_order):
    """Use pre-built test data"""
    position = single_mnq_long_position  # From fixtures/positions.py
    order = filled_buy_order              # From fixtures/orders.py
    # Test logic here
```

### Creating Factory Fixtures

```python
@pytest.fixture
def position_factory():
    """Factory to create positions with different parameters"""
    def _create(symbol="MNQ", size=1, price=15000.0):
        return {
            "contract_id": f"CON.F.US.{symbol}.U25",
            "size": size,
            "average_price": price
        }
    return _create

# Usage
def test_multiple_positions(position_factory):
    mnq_pos = position_factory(symbol="MNQ", size=2)
    mes_pos = position_factory(symbol="MES", size=5)
```

## Mocking

### Mock at Service Boundaries

```python
from unittest.mock import Mock

@pytest.fixture
def mock_pnl_tracker():
    """Mock P&L tracking service"""
    tracker = Mock(spec=PnLTracker)  # spec= prevents typos
    tracker.get_daily_pnl.return_value = -400
    return tracker

def test_with_mock(mock_pnl_tracker):
    rule = DailyLossRule(pnl_tracker=mock_pnl_tracker)
    # Mock is injected, real PnLTracker not needed
```

### Verify Mock Interactions

```python
def test_pnl_tracker_called():
    mock_tracker = Mock()
    rule = DailyLossRule(pnl_tracker=mock_tracker)

    rule.check(trade)

    # Verify mock was called correctly
    mock_tracker.add_trade.assert_called_once_with(trade)
```

## Parametrized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("limit,pnl,should_breach", [
    (-500, -400, False),  # Under limit
    (-500, -500, False),  # At limit
    (-500, -501, True),   # Breach by $1
    (-500, -1000, True),  # Large breach
])
def test_daily_loss_scenarios(limit, pnl, should_breach):
    rule = DailyLossRule(limit=limit)
    mock_tracker.daily_pnl = pnl

    result = rule.check(trade)

    if should_breach:
        assert result is not None
    else:
        assert result is None
```

## Coverage Requirements

**Minimum:** 90% overall coverage
**Critical paths:** 95%+ coverage
**New features:** 100% coverage

### Check Coverage

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows

# Find uncovered code
pytest --cov=src --cov-report=term-missing
```

### Coverage by File

```
src/core/pnl_tracker.py     95%  ← Good
src/rules/daily_loss.py     88%  ← Needs more tests
src/api/client.py           45%  ← Critical gap!
```

## Edge Cases & Error Testing

### Test Boundaries

```python
def test_exactly_at_limit():
    """Edge case: exactly at limit (not over)"""
    rule = DailyLossRule(limit=-500)
    result = rule.check(trade_with_loss(-500))
    assert result is None  # Not a breach

def test_one_dollar_over():
    """Edge case: $1 over limit"""
    result = rule.check(trade_with_loss(-501))
    assert result is not None  # IS a breach
```

### Test Error Handling

```python
def test_invalid_config_raises_error():
    """Validate configuration errors are caught"""
    with pytest.raises(ValueError, match="limit must be negative"):
        DailyLossRule(limit=500)  # Positive limit is invalid

def test_missing_required_field():
    """Handle missing data gracefully"""
    trade = {}  # No accountId
    result = rule.check(trade)
    assert result is None  # Or raise specific error
```

### Test None/Null Cases

```python
def test_ignores_none_pnl():
    """Half-turn trades have no P&L"""
    trade = {"profitAndLoss": None}
    result = rule.check(trade)
    assert result is None  # Ignored, not error
```

## Performance Testing

Add benchmarks for critical paths:

```python
@pytest.mark.performance
def test_pnl_calculation_speed():
    """Ensure P&L calculation is fast"""
    import time

    pnl_tracker = PnLTracker()
    start = time.perf_counter()

    # Simulate 1000 trades
    for i in range(1000):
        pnl_tracker.add_trade(account_id=123, pnl=-50)

    elapsed = time.perf_counter() - start
    assert elapsed < 0.1, f"Too slow: {elapsed:.3f}s"
```

## Integration Testing

### Test Component Interactions

```python
@pytest.mark.integration
def test_rule_enforcement_flow():
    """Test complete flow: rule → action → lockout"""
    # Use REAL components (not mocks)
    pnl_tracker = PnLTracker()
    actions = EnforcementActions()
    lockout = LockoutManager()

    rule = DailyLossRule(
        limit=-500,
        pnl_tracker=pnl_tracker,
        actions=actions,
        lockout=lockout
    )

    # Simulate losing trades
    for _ in range(10):
        rule.check(trade_with_loss(-60))

    # Verify full enforcement
    assert lockout.is_locked_out(account_id=123)
    assert actions.positions_closed(account_id=123)
```

## Test Reports

All test results auto-saved to `/test-results/`:

### Coverage Reports
- **HTML:** `test-results/coverage/html/index.html`
- **JSON:** `test-results/coverage/coverage.json`
- **XML:** `test-results/coverage/coverage.xml`

### Test Results
- **HTML:** `test-results/reports/report.html`
- **JUnit XML:** `test-results/reports/junit.xml`

### View Results Dashboard

```bash
# All metrics in one view
./view_test_results.sh

# Or specific sections
python scripts/test-management/view_results.py coverage
python scripts/test-management/view_results.py tests
```

## Common Patterns

### Test Rule Behavior

```python
def test_rule_triggers_correctly():
    # Setup
    config = {'enabled': True, 'limit': -500}
    rule = DailyLossRule(config, mock_tracker, mock_actions)

    # Trigger condition
    mock_tracker.daily_pnl.return_value = -600

    # Execute
    result = rule.check(trade)

    # Verify
    assert result is not None
    assert result['severity'] == 'CRITICAL'
    mock_actions.lockout_account.assert_called_once()
```

### Test Time-Based Rules

```python
from datetime import datetime, time

def test_outside_trading_hours():
    rule = TradingHoursRule(
        start_time=time(8, 30),
        end_time=time(15, 0)
    )

    # Before hours
    trade_at_8am = create_trade(timestamp="08:00:00")
    assert rule.check(trade_at_8am) is not None

    # During hours
    trade_at_10am = create_trade(timestamp="10:00:00")
    assert rule.check(trade_at_10am) is None

    # After hours
    trade_at_5pm = create_trade(timestamp="17:00:00")
    assert rule.check(trade_at_5pm) is not None
```

## Best Practices

### DO
- ✅ Write tests BEFORE implementation (TDD)
- ✅ Use `spec=` on all mocks
- ✅ Test edge cases and errors
- ✅ Keep tests fast (unit tests <1s)
- ✅ Use parametrize for multiple scenarios
- ✅ Mock at service boundaries only
- ✅ Aim for 90%+ coverage

### DON'T
- ❌ Write code before tests
- ❌ Use mocks without `spec=`
- ❌ Only test happy paths
- ❌ Over-mock (mock too much)
- ❌ Skip integration tests
- ❌ Ignore failing tests
- ❌ Mock internal components

## Troubleshooting

### Tests Pass But Code Fails at Runtime

**Problem:** "Green tests" but broken in production

**Causes:**
1. Over-mocking (mocks don't match reality)
2. Missing integration tests
3. Mocks without `spec=`
4. Not testing error cases

**Solution:**
```python
# Add integration tests with REAL components
@pytest.mark.integration
def test_real_flow():
    # Use actual PnLTracker, not Mock
    pnl_tracker = PnLTracker()
    # Test real interactions
```

### Low Coverage

**Problem:** Coverage below 90%

**Find gaps:**
```bash
pytest --cov=src --cov-report=term-missing
# Shows which lines aren't covered
```

**Fix:**
```python
# Add tests for uncovered branches
def test_uncovered_error_path():
    with pytest.raises(ValueError):
        rule.validate(invalid_config)
```

### Slow Tests

**Problem:** Tests take too long

**Solutions:**
1. Use markers to skip slow tests in development
   ```bash
   pytest -m "not slow"
   ```

2. Mock expensive operations
   ```python
   @pytest.fixture
   def mock_api_client():
       return Mock(spec=APIClient)
   ```

3. Use smaller test data sets

## CI/CD Integration

Tests run automatically on every commit/PR:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Runtime Testing

### Why Runtime Testing Matters

Unit tests and integration tests verify code correctness, but **runtime tests** validate deployment readiness:

- Environment configuration
- Dependency availability
- API connectivity
- State persistence
- Resource cleanup

### Runtime Test Suite

The project includes a comprehensive Runtime Reliability Pack with 8 checkpoints:

```bash
python run_tests.py
# Select: [S] System Health Check
```

**Checkpoints:**
1. Environment Validation (Python, packages, directories)
2. Configuration Loading (YAML syntax, values)
3. Component Initialization (PnLTracker, StateManager, etc.)
4. API Connectivity (Authentication, test calls)
5. State Management (Update, persist, recover)
6. Rule Evaluation (Load, evaluate, trigger)
7. Event Handling (Publish, subscribe, dispatch)
8. Resource Cleanup (Close, save, release)

### When to Run Runtime Tests

**Development:**
- After environment setup
- Before committing changes
- After refactoring core components

**Deployment:**
- Pre-deployment validation (required)
- Post-deployment smoke test
- Environment-specific verification

**Troubleshooting:**
- "Works on my machine" issues
- Deployment failures
- Configuration problems
- API connectivity issues

### Runtime Test Menu

```bash
python run_tests.py
```

Available runtime checks:
- **[S]** System Health Check - Full validation
- **[R]** Runtime Diagnostics - Component initialization
- **[T]** Test API Connection - TopstepX connectivity
- **[L]** Load Configurations - YAML validation
- **[E]** End-to-End Flow - Complete workflow
- **[G]** Generate Debug Report - Comprehensive diagnostic

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | SUCCESS | System ready |
| 1 | CONFIG_ERROR | Fix YAML files |
| 2 | RUNTIME_ERROR | Fix code/environment |
| 3 | API_ERROR | Check credentials |
| 4 | STATE_ERROR | Check data directory |

### Quick Fixes

**Missing Dependencies:**
```bash
pip install -r requirements.txt
python tests/runtime/test_checkpoint_01_environment.py
```

**Configuration Errors:**
```bash
# Validate config
python tests/runtime/test_checkpoint_02_config.py

# Fix highlighted issues in config/*.yaml
```

**API Issues:**
```bash
# Check credentials
cat .env | grep TOPSTEPX_API_KEY

# Test connection
python tests/runtime/test_checkpoint_04_api.py
```

**See full guide:** `/docs/testing/RUNTIME_DEBUGGING.md`

## Related Documentation

### Core Testing Docs
- **Runtime Debugging:** `/docs/testing/RUNTIME_DEBUGGING.md` ⭐ Runtime validation
- **Fixtures:** `/tests/fixtures_reference.md`
- **Test Configuration:** `/tests/conftest.py`
- **AI Workflow:** `/docs/testing/WORKING_WITH_AI.md`
- **Project Specs:** `/project-specs/SPECS/`

### API Contracts & Troubleshooting ⭐ NEW
- **SDK_API_REFERENCE.md** - Actual API signatures (prevents test/code mismatches)
- **SDK_ENFORCEMENT_FLOW.md** - Complete enforcement wiring (helps understand integration)
- **TEST_RUNNER_FINAL_FIXES.md** - Test runner behavior & performance tips

---

**Last Updated:** 2025-10-23
**Coverage Goal:** ≥90%
**Test Count:** Growing with each feature
**Runtime Validation:** 8 checkpoints
