# Testing Methodology Analysis: SDK vs. Simple Risk Manager

**Date:** 2025-10-23
**Source:** project-x-py SDK testing practices
**Purpose:** Adopt proven testing patterns for risk manager development

---

## Executive Summary

The **project-x-py SDK** has **153 test files** with **~65,653 lines** of comprehensive test code covering async trading operations, real-time data, and complex financial calculations. Their testing methodology emphasizes:

1. **Async-first testing** with pytest-asyncio
2. **Comprehensive mocking** to isolate components
3. **Test categorization** with markers for different test types
4. **Performance benchmarking** integrated into test suite
5. **Fixture-heavy approach** for reusable test data
6. **AAA pattern** (Arrange-Act-Assert) consistently applied

Your **simple-risk-manager** currently uses a simpler approach but can benefit from several SDK patterns.

---

## 1. Test Organization & Structure

### SDK Approach

```
tests/
├── conftest.py                  # Shared fixtures (272 lines)
├── unit/                        # Fast, isolated tests
│   ├── test_client_auth.py
│   ├── test_order_manager.py
│   └── test_indicators.py
├── integration/                 # Component interaction tests
│   ├── test_trading_suite.py
│   └── test_realtime_flow.py
├── benchmarks/                  # Performance tests
│   └── test_performance.py
├── client/                      # Domain-specific tests
├── order_manager/
├── position_manager/
└── fixtures/                    # Test data (JSON files)
    ├── market_data.json
    └── order_responses.json
```

**Why this works:**
- Clear separation between unit, integration, and performance tests
- Domain-specific test folders mirror source code structure
- Centralized fixtures reduce duplication
- Performance tests isolated so they can be skipped in CI

### Your Current Approach

```
tests/
├── conftest.py                  # 99 lines
├── fixtures/                    # Separate fixture files
│   ├── positions.py
│   ├── orders.py
│   ├── trades.py
│   └── accounts.py
├── unit/
│   ├── rules/                   # Rule tests
│   └── test_enforcement_actions.py
└── integration/                 # Integration tests
```

**What's working:**
- ✅ Good separation of unit vs integration
- ✅ Fixture files per domain (positions, orders, trades)
- ✅ Clear test organization by feature (rules)

**Opportunities:**
- 🔄 Add performance/benchmark tests for P&L calculations
- 🔄 Consider adding markers for slow tests
- 🔄 Create domain-specific test folders (e.g., `tests/api/`, `tests/core/`)

---

## 2. Testing Philosophy & Patterns

### SDK Testing Philosophy

From their docs:

> **Comprehensive testing strategy:**
> - Unit Tests: Fast, isolated tests for individual components
> - Integration Tests: Test component interactions
> - End-to-End Tests: Full workflow testing
> - Performance Tests: Ensure scalability and performance
> - Real-time Tests: Validate real-time data handling (market hours only)

**Test Markers Used:**
```python
@pytest.mark.unit           # Fast unit tests
@pytest.mark.integration    # Component interaction tests
@pytest.mark.slow           # Tests taking >5 seconds
@pytest.mark.realtime       # Requires live market connection
@pytest.mark.performance    # Benchmarking tests
@pytest.mark.asyncio        # Async test execution
```

**Running tests selectively:**
```bash
# Unit tests only (fast feedback)
pytest -m unit

# Skip slow tests in development
pytest -m "not slow"

# Skip real-time tests (require market hours)
pytest -m "not realtime"

# Integration tests only
pytest -m integration
```

### Your Current Approach

**No markers currently used** - all tests run together.

**Recommendation:** Adopt test markers:

```python
# In conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests (>1 second)")
    config.addinivalue_line("markers", "requires_db: Requires database")
    config.addinivalue_line("markers", "requires_api: Requires TopstepX API")

# In tests
@pytest.mark.unit
@pytest.mark.fast
def test_daily_loss_calculation():
    # Fast unit test
    pass

@pytest.mark.integration
@pytest.mark.requires_api
async def test_live_api_connection():
    # Integration test requiring API
    pass
```

---

## 3. AAA Pattern (Arrange-Act-Assert)

### SDK Implementation

Every test follows strict AAA:

```python
@pytest.mark.asyncio
async def test_authenticate_success(self, initialized_client, mock_auth_response):
    """Test successful authentication flow."""
    # ARRANGE - Set up test data and mocks
    client = initialized_client
    auth_response, accounts_response = mock_auth_response
    client._client.request.side_effect = [auth_response, accounts_response]

    # ACT - Execute the behavior being tested
    await client.authenticate()

    # ASSERT - Verify expected outcomes
    assert client._authenticated
    assert client.session_token == auth_response.json()["token"]
    assert client.account_info is not None
    assert client.account_info.name == "Test Account"

    # Assert on mock interactions
    assert client._client.request.call_count == 2
```

**Key principles:**
1. Clear comments separating each phase
2. One logical action per test (single `Act` section)
3. Multiple assertions allowed if testing same behavior
4. Mock verification in Assert phase

### Your Current Approach

You use **Given-When-Then** (BDD style):

```python
def test_check_under_limit(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
    """
    GIVEN: Limit=-500, daily P&L=-400
    WHEN: Trade is checked
    THEN: No breach, P&L tracker updated, no enforcement
    """
    # Given
    config = {'enabled': True, 'limit': -500, ...}
    mock_pnl_tracker.get_daily_realized_pnl.return_value = -400

    # When
    rule = DailyRealizedLossRule(config, ...)
    result = rule.check(trade_event)

    # Then
    assert result is None
    mock_pnl_tracker.add_trade_pnl.assert_called_once_with(123, -50)
```

**What's working:**
- ✅ Clear three-phase structure
- ✅ Descriptive docstrings explaining test scenario
- ✅ Good use of mocks

**Opportunities:**
- Both AAA and Given-When-Then are valid - keep your current approach (it's excellent for business logic)
- Consider AAA for technical tests, Given-When-Then for rule/business logic tests

---

## 4. Fixture Strategy

### SDK Fixture Architecture

**Centralized conftest.py with factory patterns:**

```python
@pytest.fixture
def mock_response():
    """Factory fixture - returns a function to create responses."""
    def _create_response(status_code=200, json_data=None, success=True):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data or {"success": success}
        return mock_resp
    return _create_response

# Usage in tests:
def test_api_call(mock_response):
    success_resp = mock_response(status_code=200, json_data={"balance": 10000})
    error_resp = mock_response(status_code=500)
```

**Fixture composition:**

```python
@pytest.fixture
def mock_auth_response(mock_response):
    """Compose multiple mock responses."""
    token_payload = {"token": "eyJ..."}
    accounts_payload = {"accounts": [...]}
    return (
        mock_response(json_data=token_payload),
        mock_response(json_data=accounts_payload)
    )
```

**Parameterized fixtures:**

```python
@pytest.fixture
def mock_bars_data():
    """Generate 100 bars of test data."""
    now = datetime.now(pytz.UTC)
    return [
        {
            "t": (now - timedelta(minutes=i * 5)).isoformat(),
            "o": 1900.0 + i * 0.1,
            "h": 1905.0 + i * 0.1,
            "l": 1895.0 + i * 0.1,
            "c": 1902.0 + i * 0.1,
            "v": 100 + i,
        }
        for i in range(100)
    ]
```

### Your Current Approach

**Separate fixture files per domain:**

```python
# fixtures/positions.py
@pytest.fixture
def single_es_long_position_api():
    """Single ES long position - API response format."""
    return {
        "id": 12345,
        "accountId": 123,
        "contractId": "CON.F.US.ES.H25",
        "type": 1,  # LONG
        "size": 1,
        "averagePrice": 4500.00,
    }
```

**What's working:**
- ✅ Excellent domain separation (positions, orders, trades, accounts)
- ✅ Clear fixture naming
- ✅ Dual fixtures (API format vs internal format)

**Opportunities:**
- ✅ **Keep your current approach** - it's cleaner for your use case
- 🔄 Consider adding factory fixtures for generating multiple scenarios:

```python
@pytest.fixture
def position_factory():
    """Factory to create positions with different parameters."""
    def _create_position(contract_id="CON.F.US.MNQ.U25", size=1, price=15000.0, position_type=1):
        return {
            "id": 12345,
            "account_id": 123,
            "contract_id": contract_id,
            "type": position_type,
            "size": size,
            "average_price": price,
        }
    return _create_position

# Usage:
def test_multiple_positions(position_factory):
    mnq_long = position_factory(contract_id="MNQ", size=2)
    mes_short = position_factory(contract_id="MES", size=1, position_type=2)
```

---

## 5. Async Testing Patterns

### SDK's Async Testing

**Every async function tested with `@pytest.mark.asyncio`:**

```python
@pytest.mark.asyncio
async def test_authenticate_success(self, mock_client):
    """Test successful authentication."""
    mock_client.authenticate.return_value = True

    result = await mock_client.authenticate()

    assert result is True
    mock_client.authenticate.assert_called_once()

@pytest.mark.asyncio
async def test_connection_establishment(self):
    """Test WebSocket connection."""
    mock_connection = AsyncMock()
    mock_connection.start = AsyncMock()

    client = ProjectXRealtimeClient("token", "url")
    await client.connect()

    assert client.is_connected
    mock_connection.start.assert_called_once()
```

**Async context managers:**

```python
@pytest.mark.asyncio
async def test_client_lifecycle():
    """Test async context manager usage."""
    async with ProjectX.from_env() as client:
        result = await client.authenticate()
        assert result is True
    # Client automatically closed
```

**Mocking async functions:**

```python
from unittest.mock import AsyncMock

mock_client = AsyncMock()
mock_client.get_bars.return_value = pl.DataFrame({"close": [1, 2, 3]})

# In test:
bars = await mock_client.get_bars("MNQ")
```

### Your Current Approach

**Mostly synchronous** - your risk manager doesn't heavily use async yet.

**When you add async features (daemon, API client):**

```python
# You'll need to add:
@pytest.mark.asyncio
async def test_signalr_event_handling():
    """Test real-time event processing."""
    mock_signalr = AsyncMock()

    daemon = Daemon(config, signalr_client=mock_signalr)
    await daemon.start()

    # Simulate event
    event = {"type": "position_update", "data": {...}}
    await daemon.handle_event(event)

    # Verify rule was triggered
    assert daemon.rules_triggered == 1
```

---

## 6. Mock Strategy

### SDK Mocking Patterns

**Mock at the right level:**

```python
# ✅ GOOD: Mock HTTP client (external boundary)
@patch('httpx.AsyncClient.post')
async def test_api_call(mock_post):
    mock_post.return_value.json = AsyncMock(return_value={"success": True})
    # Test API client behavior

# ✅ GOOD: Mock at component boundary
async def test_order_manager(mock_client):
    mock_client.place_order = AsyncMock(return_value={"orderId": 123})
    # Test order manager logic

# ❌ BAD: Over-mocking (mocks too much)
@patch('project_x_py.client.ProjectX')  # Entire class
async def test_over_mocked(mock_client):
    # Test becomes meaningless
```

**Specific mock specs to prevent typos:**

```python
mock_client = AsyncMock(spec=ProjectX)  # Only allows ProjectX methods
mock_client.invalid_method()  # Would raise AttributeError
```

**Side effects for sequences:**

```python
mock_pnl_tracker.add_trade_pnl.side_effect = [100, 50, -150, -600]

# Each call returns next value in sequence
```

### Your Current Approach

**Simple Mock objects:**

```python
@pytest.fixture
def mock_pnl_tracker():
    """Mock P&L tracker."""
    return Mock()

# In test:
mock_pnl_tracker.get_daily_realized_pnl.return_value = -400
```

**What's working:**
- ✅ Mocking at service boundaries (pnl_tracker, actions, lockout_manager)
- ✅ Clear mock fixtures

**Opportunities:**
- 🔄 Add `spec=` to mocks to catch typos:

```python
from src.core.pnl_tracker import PnLTracker

@pytest.fixture
def mock_pnl_tracker():
    return Mock(spec=PnLTracker)  # Only allows real PnLTracker methods
```

- 🔄 Use `side_effect` for sequences (you already do this - good!)

---

## 7. Test Data Management

### SDK Approach

**JSON fixtures for complex data:**

```python
# tests/fixtures/market_data.json
{
  "bars_1min": [
    {
      "timestamp": "2024-01-01T10:00:00Z",
      "open": 15000.0,
      "high": 15010.0,
      "low": 14990.0,
      "close": 15005.0,
      "volume": 1000
    }
  ]
}

# Loading in tests:
@pytest.fixture
def sample_market_data():
    fixtures_path = Path(__file__).parent / "fixtures"
    with open(fixtures_path / "market_data.json") as f:
        return json.load(f)
```

**Parametrized test data:**

```python
@pytest.mark.parametrize("period,expected_length", [
    (5, 5),
    (10, 10),
    (20, 20),
])
def test_sma_different_periods(period, expected_length):
    """Test SMA with different periods."""
    data = pl.DataFrame({"close": list(range(100))})
    sma = data.pipe(SMA, period=period)

    valid_values = sma[period-1:]
    assert len(valid_values) == len(data) - period + 1
```

### Your Current Approach

**Python fixtures (not JSON):**

```python
@pytest.fixture
def single_es_long_position():
    """Single ES long position."""
    return {
        "id": 12345,
        "account_id": 123,
        "contract_id": "CON.F.US.ES.H25",
        "type": 1,
        "size": 1,
        "average_price": 4500.00,
    }
```

**What's working:**
- ✅ Simple, readable, type-safe
- ✅ No external file dependencies
- ✅ Easy to modify in IDE

**Opportunities:**
- ✅ **Keep Python fixtures** - they're better for your use case
- 🔄 Add parameterized tests for multiple scenarios:

```python
@pytest.mark.parametrize("limit,pnl,should_breach", [
    (-500, -400, False),  # Under limit
    (-500, -500, False),  # At limit
    (-500, -501, True),   # Breach by $1
    (-500, -1000, True),  # Large breach
])
def test_daily_loss_limit(limit, pnl, should_breach, mock_pnl_tracker):
    config = {'limit': limit}
    mock_pnl_tracker.add_trade_pnl.return_value = pnl

    rule = DailyRealizedLossRule(config, mock_pnl_tracker, ...)
    result = rule.check(trade_event)

    if should_breach:
        assert result is not None
    else:
        assert result is None
```

---

## 8. Performance Testing

### SDK Performance Tests

**Built-in benchmarking:**

```python
@pytest.mark.performance
def test_indicator_calculation_performance(benchmark):
    """Benchmark indicator calculation."""
    large_dataset = pl.DataFrame({"close": list(range(10000))})

    result = benchmark(large_dataset.pipe, SMA, period=20)
    assert len(result) == 10000

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_api_calls_performance():
    """Test concurrent API calls."""
    symbols = ["MNQ", "MES", "MYM", "M2K"]

    start_time = time.perf_counter()
    tasks = [mock_get_bars(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks)
    end_time = time.perf_counter()

    assert len(results) == len(symbols)
    assert end_time - start_time < 1.0  # Must complete <1s
```

**Memory profiling:**

```python
@pytest.mark.performance
def test_memory_usage_realtime_data():
    """Test memory usage patterns."""
    import psutil, os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Simulate heavy processing
    for i in range(5000):
        tick = {"price": 15000.0 + i * 0.25, "volume": 10}
        data_manager.process_tick(tick)

    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / 1024 / 1024

    assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"
```

### Your Current Approach

**No performance tests currently.**

**Recommendation:**

Add performance tests for critical paths:

```python
@pytest.mark.performance
def test_pnl_calculation_performance():
    """Ensure P&L calculation completes quickly."""
    pnl_tracker = PnLTracker()

    start = time.perf_counter()

    # Simulate 1000 trades
    for i in range(1000):
        pnl_tracker.add_trade_pnl(account_id=123, pnl=-50.0)

    end = time.perf_counter()

    assert end - start < 0.1, "P&L calculation too slow"

@pytest.mark.performance
def test_rule_evaluation_performance():
    """All 12 rules should evaluate <10ms."""
    # Test rule performance under load
    pass
```

---

## 9. Error & Edge Case Testing

### SDK Error Testing

**Comprehensive error scenarios:**

```python
@pytest.mark.asyncio
async def test_authenticate_failure(self, initialized_client, mock_response):
    """Test authentication failure handling."""
    client = initialized_client
    failed_response = mock_response(
        status_code=401,
        json_data={"success": False, "message": "Invalid credentials"}
    )
    client._client.request.return_value = failed_response

    with pytest.raises(ProjectXAuthenticationError, match="Authentication failed"):
        await client.authenticate()

    assert not client._authenticated
    assert not client.session_token

@pytest.mark.asyncio
async def test_error_handling(self):
    """Test proper error handling and propagation."""
    with patch('project_x_py.client.ProjectX.place_order') as mock_place:
        mock_place.side_effect = OrderRejectedError("Insufficient funds")

        with pytest.raises(OrderRejectedError) as exc_info:
            async with ProjectX.from_env() as client:
                await client.place_order({"symbol": "MNQ"})

        assert "Insufficient funds" in str(exc_info.value)
```

### Your Current Approach

**Good edge case coverage:**

```python
def test_check_breach_by_one_dollar(...):
    """Test breach detection at limit + $1."""
    mock_pnl_tracker.add_trade_pnl.return_value = -501  # Breach!
    # ...

def test_check_ignores_half_turn_trades(...):
    """Test trades with profitAndLoss=None are ignored."""
    trade_event = {'profitAndLoss': None}
    # ...
```

**What's working:**
- ✅ Testing exact boundary conditions (-501 vs -500)
- ✅ Testing null/None cases
- ✅ Testing time edge cases (after 5pm)

**Opportunities:**
- 🔄 Add explicit error testing:

```python
def test_invalid_config_raises_error():
    """Test invalid configuration is caught."""
    config = {'limit': 500}  # Positive limit (invalid)

    with pytest.raises(ValueError, match="limit must be negative"):
        rule = DailyRealizedLossRule(config, ...)

def test_missing_required_field():
    """Test missing trade fields handled gracefully."""
    trade = {}  # No accountId

    result = rule.check(trade)
    assert result is None  # Or raise specific error
```

---

## 10. CI/CD Integration

### SDK CI Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
    - uses: actions/checkout@v4
    - name: Install dependencies
      run: uv sync --dev
    - name: Run tests
      run: |
        uv run pytest --cov=project_x_py --cov-report=xml -m "not realtime"
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

**Key features:**
- Multiple Python versions tested
- Skip real-time tests in CI (`-m "not realtime"`)
- Coverage reporting
- Fail fast on test failures

### Recommendation for Your Project

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest  # Windows Service target

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-test.txt

    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=src --cov-report=xml

    - name: Run integration tests (skip API tests)
      run: pytest tests/integration/ -v -m "not requires_api"

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 11. Key Takeaways & Recommendations

### What SDK Does Exceptionally Well

1. **Test categorization** with markers - allows selective test runs
2. **Comprehensive async testing** - critical for real-time systems
3. **Performance benchmarking** - ensures scalability
4. **Fixture factories** - flexible test data generation
5. **Clear test organization** - unit/integration/benchmarks separation
6. **Mock at boundaries** - isolates components properly
7. **Error scenario coverage** - tests failures thoroughly

### What You're Already Doing Well

1. ✅ **Clear Given-When-Then structure** - excellent for business logic
2. ✅ **Domain-specific fixtures** - positions, orders, trades separated
3. ✅ **Edge case testing** - boundary conditions well covered
4. ✅ **Mock isolation** - dependencies properly mocked
5. ✅ **Descriptive test names** - clear intent

### Recommended Adoptions

#### Priority 1: High Value, Low Effort

1. **Add test markers** (30 minutes):
   ```python
   # pytest.ini
   markers =
       unit: Unit tests
       integration: Integration tests
       slow: Slow tests (>1 second)
       requires_db: Requires database
       requires_api: Requires TopstepX API
   ```

2. **Add fixture factories** (1 hour):
   ```python
   @pytest.fixture
   def trade_factory():
       def _create_trade(pnl=-50, account_id=123, **kwargs):
           return {"accountId": account_id, "profitAndLoss": pnl, **kwargs}
       return _create_trade
   ```

3. **Parametrize existing tests** (2 hours):
   ```python
   @pytest.mark.parametrize("pnl,should_breach", [(-400, False), (-501, True)])
   def test_daily_loss(pnl, should_breach, ...):
       # Single test covers multiple scenarios
   ```

#### Priority 2: Important for Production

4. **Add performance tests** (4 hours):
   - P&L calculation benchmarks
   - Rule evaluation speed tests
   - Memory usage validation

5. **Add async testing infrastructure** (when building daemon) (4 hours):
   - Install pytest-asyncio
   - Add async test fixtures
   - Test SignalR event handling

6. **Enhance error testing** (2 hours):
   - Test invalid configurations
   - Test missing required fields
   - Test exception propagation

#### Priority 3: Long-term Quality

7. **Mock specs for type safety** (2 hours):
   ```python
   mock_pnl = Mock(spec=PnLTracker)  # Catches typos
   ```

8. **Integration with CI/CD** (4 hours):
   - GitHub Actions workflow
   - Coverage reporting
   - Automated test runs on PR

9. **Benchmark regression testing** (4 hours):
   - Track performance over time
   - Alert on slowdowns

---

## 12. Sample Implementation: Adopting SDK Patterns

### Before (Current Style)

```python
def test_check_under_limit(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
    """
    GIVEN: Limit=-500, daily P&L=-400
    WHEN: Trade is checked
    THEN: No breach
    """
    config = {'enabled': True, 'limit': -500}
    mock_pnl_tracker.get_daily_realized_pnl.return_value = -400

    trade_event = {'accountId': 123, 'profitAndLoss': -50}

    rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
    result = rule.check(trade_event)

    assert result is None
```

### After (With SDK Patterns)

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def trade_factory():
    """Factory for creating test trades."""
    def _create_trade(pnl=-50, account_id=123, contract_id="CON.F.US.MNQ.U25", **kwargs):
        return {
            "accountId": account_id,
            "profitAndLoss": pnl,
            "contractId": contract_id,
            **kwargs
        }
    return _create_trade

@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.parametrize("daily_pnl,trade_pnl,limit,should_breach", [
    (-400, -50, -500, False),  # Under limit
    (-450, -50, -500, False),  # At limit
    (-451, -50, -500, True),   # Breach by $1
    (-400, -200, -500, True),  # Large loss breach
    (100, -50, -500, False),   # Profitable day
])
def test_daily_loss_limit_scenarios(
    daily_pnl, trade_pnl, limit, should_breach,
    trade_factory, mock_pnl_tracker, mock_actions, mock_lockout_manager
):
    """Test daily loss limit with various P&L scenarios."""
    # ARRANGE
    config = {'enabled': True, 'limit': limit}
    mock_pnl_tracker.add_trade_pnl.return_value = daily_pnl + trade_pnl
    trade = trade_factory(pnl=trade_pnl)

    # ACT
    rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
    result = rule.check(trade)

    # ASSERT
    if should_breach:
        assert result is not None
        assert result['action'] == 'CLOSE_ALL_AND_LOCKOUT'
    else:
        assert result is None
        mock_actions.close_all_positions.assert_not_called()

@pytest.mark.performance
def test_daily_loss_calculation_performance(mock_pnl_tracker, trade_factory):
    """Ensure loss calculation completes quickly under load."""
    import time

    config = {'enabled': True, 'limit': -1000}
    rule = DailyRealizedLossRule(config, mock_pnl_tracker, Mock(), Mock())

    start = time.perf_counter()

    # Simulate 1000 trades
    for i in range(1000):
        mock_pnl_tracker.add_trade_pnl.return_value = -50 * i
        trade = trade_factory(pnl=-50)
        rule.check(trade)

    elapsed = time.perf_counter() - start

    assert elapsed < 0.1, f"Processing 1000 trades took {elapsed:.3f}s (limit: 0.1s)"
```

**Benefits:**
- ✅ 5 scenarios tested in one function (was 5 separate tests)
- ✅ Performance test added
- ✅ Test markers allow selective execution
- ✅ Factory makes creating trades easier
- ✅ Still readable and maintainable

---

## 13. Testing Checklist (Adapted from SDK)

Before submitting code:

- [ ] All new code has corresponding tests
- [ ] Tests cover both success and error cases
- [ ] Edge cases tested (boundaries, nulls, empty values)
- [ ] Mocks are used appropriately (not over-mocked)
- [ ] Test markers applied correctly (`@pytest.mark.unit`, etc.)
- [ ] Performance-critical code has benchmark tests
- [ ] Integration tests verify component interactions
- [ ] Tests are properly categorized with markers
- [ ] Test coverage maintained/improved
- [ ] Tests pass locally: `pytest tests/unit/`
- [ ] Slow tests can be skipped: `pytest -m "not slow"`

---

## 14. Conclusion

The **project-x-py SDK testing methodology** is battle-tested on a production async trading system with **153 test files** and comprehensive coverage. Their patterns are directly applicable to your risk manager:

**Adopt immediately:**
- Test markers for categorization
- Parametrized tests for multiple scenarios
- Fixture factories for flexible test data

**Adopt when building daemon:**
- Async testing patterns
- Mock AsyncMock for SignalR
- Integration tests for event pipeline

**Adopt for production readiness:**
- Performance benchmarking
- CI/CD integration
- Coverage reporting

Your current testing approach is solid - this analysis provides patterns to **scale it up** as your project grows toward production deployment.

---

**Next Steps:**

1. ✅ Add test markers to `pytest.ini` (today)
2. ✅ Create `trade_factory`, `position_factory` fixtures (this week)
3. ✅ Parametrize your most complex tests (this week)
4. 🔄 Add performance tests for P&L calculations (before Phase 1 complete)
5. 🔄 Setup GitHub Actions CI (before Phase 2)

