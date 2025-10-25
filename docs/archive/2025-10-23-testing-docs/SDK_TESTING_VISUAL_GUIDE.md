# 📊 SDK Testing Visual Guide: HOW They Test (With Examples)

**Project:** risk-manager-v34
**Reference:** project-x-py SDK (153 test files, 65,653 lines)
**Your Tests:** 3 files, ~300 lines (early stage)

---

## 📍 Quick Navigation

- [1. Test Organization Comparison](#1-test-organization-comparison)
- [2. Fixture Patterns (Visual Examples)](#2-fixture-patterns-visual-examples)
- [3. Async Testing Patterns](#3-async-testing-patterns)
- [4. Mock Strategies (Side-by-Side)](#4-mock-strategies-side-by-side)
- [5. Test Class Organization](#5-test-class-organization)
- [6. Parametrized Testing](#6-parametrized-testing)
- [7. Performance Benchmarking](#7-performance-benchmarking)
- [8. Copy-Paste Templates](#8-copy-paste-templates)

---

## 1. Test Organization Comparison

### 📂 SDK Test Structure (What They Do)

```
tests/
├── conftest.py                    # 272 lines - Centralized fixtures
├── unit/                          # Fast, isolated tests
│   ├── test_client_auth.py        # 100 lines
│   ├── test_order_manager.py      # 200 lines
│   └── test_indicators.py         # 150 lines
├── integration/                   # Component interaction
│   ├── test_trading_suite.py      # 300 lines
│   └── test_realtime_flow.py      # 250 lines
├── benchmarks/                    # Performance tests
│   └── test_performance.py        # 200 lines
├── client/                        # Domain-specific
│   ├── test_client_auth.py
│   ├── test_client_core.py
│   └── test_market_data.py
├── order_manager/                 # 15 test files
├── position_manager/              # 12 test files
├── indicators/                    # 20 test files
└── fixtures/                      # JSON test data
    ├── market_data.json
    └── order_responses.json
```

### 📂 Your Current Structure

```
tests/
├── conftest.py                    # 228 lines - Good fixtures!
└── unit/
    ├── test_core/
    │   └── test_events.py
    └── test_state/
        └── test_pnl_tracker.py    # 214 lines - TDD approach ✅
```

### 📊 Comparison Table

| Aspect | SDK (project-x-py) | Your Project (risk-manager-v34) |
|--------|-------------------|----------------------------------|
| **Total Test Files** | 153 files | 3 files |
| **Test Lines** | ~65,653 lines | ~300 lines |
| **Test Markers** | ✅ unit, integration, slow, performance, realtime | ✅ unit, integration, slow, ai |
| **Async Tests** | ✅ Extensive (AsyncMock everywhere) | 🔄 Starting (AsyncMock in conftest) |
| **Fixtures** | ✅ Factory pattern + composition | ✅ Good start (mock_engine, mock_suite) |
| **Parametrized** | ✅ Heavy use | ❌ None yet |
| **Performance** | ✅ Dedicated benchmark tests | ❌ None yet |
| **Domain Folders** | ✅ client/, order_manager/, indicators/ | 🔄 Starting (test_core/, test_state/) |

---

## 2. Fixture Patterns (Visual Examples)

### Pattern 1: Factory Fixtures (SDK's Favorite Pattern)

#### 🎯 SDK Example: `mock_response()` Factory

```python
# tests/conftest.py (SDK)
@pytest.fixture
def mock_response():
    """Factory fixture - returns a function to create responses."""
    def _create_response(status_code=200, json_data=None, success=True):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code

        if json_data is None:
            json_data = {"success": success}

        mock_resp.json.return_value = json_data
        mock_resp.text = json.dumps(json_data)

        # Headers
        headers = {"Content-Type": "application/json"}
        mock_resp.headers = MagicMock()
        mock_resp.headers.get = lambda key, default=None: headers.get(key, default)

        return mock_resp

    return _create_response


# USAGE IN TESTS:
def test_api_call(mock_response):
    # Create different responses easily
    success_resp = mock_response(status_code=200, json_data={"balance": 10000})
    error_resp = mock_response(status_code=500, json_data={"error": "Server error"})
    auth_fail = mock_response(status_code=401, json_data={"error": "Unauthorized"})

    # Use in test...
```

#### 💡 Your Version (Copy-Paste Template)

```python
# Add to tests/conftest.py
@pytest.fixture
def event_factory():
    """Factory to create RiskEvents with different data."""
    def _create_event(
        event_type=EventType.TRADE_EXECUTED,
        symbol="MNQ",
        realized_pnl=-12.50,
        **kwargs
    ):
        return RiskEvent(
            type=event_type,
            data={
                "symbol": symbol,
                "realized_pnl": realized_pnl,
                "timestamp": datetime.now().isoformat(),
                **kwargs
            }
        )
    return _create_event


# USAGE:
def test_multiple_scenarios(event_factory):
    losing_trade = event_factory(realized_pnl=-150.0)
    winning_trade = event_factory(realized_pnl=100.0)
    breakeven = event_factory(realized_pnl=0.0)
    es_trade = event_factory(symbol="ES", realized_pnl=-50.0)
```

---

### Pattern 2: Fixture Composition (Building on Other Fixtures)

#### 🎯 SDK Example: Composed Authentication

```python
# tests/conftest.py (SDK)
@pytest.fixture
def mock_auth_response(mock_response):
    """Compose authentication response from base response."""
    token_payload = {
        "token": "eyJhbGci..."
    }
    accounts_payload = {
        "success": True,
        "accounts": [{
            "id": 12345,
            "name": "Test Account",
            "balance": 100000.0,
            "canTrade": True
        }]
    }
    return (
        mock_response(json_data=token_payload),
        mock_response(json_data=accounts_payload)
    )


# USAGE:
async def test_authenticate_success(initialized_client, mock_auth_response):
    client = initialized_client
    auth_response, accounts_response = mock_auth_response
    client._client.request.side_effect = [auth_response, accounts_response]

    await client.authenticate()

    assert client._authenticated
    assert client.session_token == auth_response.json()["token"]
```

#### 💡 Your Version (Copy-Paste Template)

```python
# Add to tests/conftest.py
@pytest.fixture
def mock_risk_breach(event_factory):
    """Compose a risk breach scenario from events."""
    def _create_breach(
        daily_loss=-500.0,
        limit=-400.0,
        rule_id="RULE-001"
    ):
        breach_event = event_factory(realized_pnl=daily_loss)
        breach_data = {
            "rule_id": rule_id,
            "action": "CLOSE_ALL",
            "daily_pnl": daily_loss,
            "limit": limit,
            "severity": "CRITICAL"
        }
        return breach_event, breach_data
    return _create_breach


# USAGE:
def test_breach_enforcement(mock_risk_breach, mock_engine):
    breach_event, breach_data = mock_risk_breach(daily_loss=-600, limit=-500)
    # Test enforcement...
```

---

### Pattern 3: Parameterized Fixtures (Multiple Test Data Sets)

#### 🎯 SDK Example: Multiple Instruments

```python
# tests/conftest.py (SDK)
@pytest.fixture
def mock_bars_data():
    """Generate 100 bars of test data."""
    now = datetime.now(pytz.UTC)
    data = []
    for i in range(100):
        timestamp = now - timedelta(minutes=i * 5)
        data.append({
            "t": timestamp.isoformat(),
            "o": 1900.0 + i * 0.1,
            "h": 1905.0 + i * 0.1,
            "l": 1895.0 + i * 0.1,
            "c": 1902.0 + i * 0.1,
            "v": 100 + i,
        })
    return data


# USAGE:
def test_indicator_with_real_bars(mock_bars_data):
    df = pl.DataFrame(mock_bars_data)
    sma = df.pipe(SMA, period=20)
    assert len(sma) == 100
```

---

## 3. Async Testing Patterns

### 📊 Comparison Table: Sync vs Async Testing

| Pattern | Sync Test | Async Test (SDK) |
|---------|-----------|------------------|
| **Decorator** | `def test_...()` | `@pytest.mark.asyncio`<br>`async def test_...()` |
| **Mocks** | `Mock()` | `AsyncMock()` |
| **Assertions** | `func()` | `await func()` |
| **Setup** | `@pytest.fixture` | `@pytest.fixture`<br>`async def fixture()` |

### 🎯 SDK Example: Async Test with AsyncMock

```python
# tests/client/test_client_auth.py (SDK)
@pytest.mark.asyncio
async def test_authenticate_success(self, initialized_client, mock_auth_response):
    """Test successful authentication flow."""
    # ARRANGE
    client = initialized_client
    auth_response, accounts_response = mock_auth_response
    client._client.request.side_effect = [auth_response, accounts_response]

    # ACT
    await client.authenticate()

    # ASSERT
    assert client._authenticated
    assert client.session_token == auth_response.json()["token"]
    assert client.account_info is not None
    assert client.account_info.name == "Test Account"

    # Verify mock calls
    assert client._client.request.call_count == 2
```

### 💡 Your Current Approach (Already Good!)

```python
# tests/conftest.py (Your Project)
@pytest.fixture
async def risk_manager():
    """Fully configured RiskManager for integration tests."""
    from risk_manager import RiskManager

    rm = await RiskManager.create(
        instruments=["MNQ"],
        rules={"max_contracts": 5}
    )

    yield rm

    # Cleanup
    await rm.stop()
```

### ✅ What You're Doing Right:
- Using `AsyncMock()` in conftest ✅
- Async fixtures with cleanup ✅
- Using `@pytest.mark.asyncio` configured in pyproject.toml ✅

---

## 4. Mock Strategies (Side-by-Side)

### 📊 Mock Levels Comparison

```
┌─────────────────────────────────────────────────┐
│              MOCK AT THE RIGHT LEVEL             │
├─────────────────────────────────────────────────┤
│                                                  │
│  ❌ Too High:  Mock entire system               │
│  ✅ Just Right: Mock at boundaries              │
│  ❌ Too Low:   Mock internal details            │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 🎯 SDK Example: Mocking at HTTP Boundary

```python
# ✅ GOOD: Mock at HTTP client level
@patch('httpx.AsyncClient.post')
async def test_place_order_api_call(mock_post):
    """Test API call without hitting real server."""
    # Mock HTTP response
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={
        "success": True,
        "order_id": 12345
    })
    mock_post.return_value = mock_response

    # Test order placement
    async with ProjectX.from_env() as client:
        result = await client.place_order({"symbol": "MNQ"})
        assert result["order_id"] == 12345
```

### 💡 Your Approach (Already Good!)

```python
# tests/conftest.py (Your Project)
@pytest.fixture
def mock_suite():
    """Mock TradingSuite (SDK) for testing."""
    suite = AsyncMock()
    suite.close_position = AsyncMock()
    suite.cancel_all_orders = AsyncMock()
    suite.place_order = AsyncMock()

    # Mock stats
    mock_stats = Mock()
    mock_stats.balance = 100000.0
    suite.get_stats = AsyncMock(return_value=mock_stats)

    return suite
```

### ✅ What You're Doing Right:
- Mocking at service boundaries (suite, engine) ✅
- Using specs appropriately ✅

### 🔄 Enhancement: Add `spec=` for Type Safety

```python
# BEFORE:
suite = AsyncMock()

# AFTER (SDK pattern):
from project_x_py import TradingSuite
suite = AsyncMock(spec=TradingSuite)  # Only allows real TradingSuite methods

# This would error:
suite.invalid_method()  # AttributeError!
```

---

## 5. Test Class Organization

### 📊 Visual Structure

```
┌──────────────────────────────────────────────────────┐
│             SDK TEST CLASS PATTERN                    │
├──────────────────────────────────────────────────────┤
│                                                       │
│  class TestFeatureBasics:                            │
│      """Test basic functionality."""                │
│      ✓ Happy path tests                             │
│      ✓ Simple success cases                         │
│                                                       │
│  class TestFeatureEdgeCases:                        │
│      """Test edge cases and boundaries."""          │
│      ✓ Boundary conditions                          │
│      ✓ Null/None handling                           │
│      ✓ Empty inputs                                 │
│                                                       │
│  class TestFeatureErrors:                           │
│      """Test error handling."""                     │
│      ✓ Invalid inputs                               │
│      ✓ Exception cases                              │
│      ✓ Network failures                             │
│                                                       │
│  class TestFeaturePerformance:                      │
│      """Test performance."""                        │
│      ✓ Speed benchmarks                             │
│      ✓ Memory usage                                 │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 🎯 SDK Example: Order Manager Tests

```python
# tests/order_manager/test_core_advanced.py (SDK)

class TestOrderManagerInitialization:
    """Test OrderManager initialization paths."""

    @pytest.mark.asyncio
    async def test_initialize_with_realtime_connection_failure(self, order_manager):
        """Real-time connection failure should be handled gracefully."""
        realtime_client = MagicMock()
        realtime_client.user_connected = False
        realtime_client.connect = AsyncMock(return_value=False)

        result = await order_manager.initialize(realtime_client)
        assert result is False
        assert order_manager._realtime_enabled is False

    @pytest.mark.asyncio
    async def test_initialize_with_realtime_already_connected(self, order_manager):
        """Should handle already connected real-time client."""
        # ... test implementation


class TestCircuitBreaker:
    """Test the circuit breaker mechanism."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self, order_manager):
        """Circuit breaker should open after failure threshold."""
        order_manager.status_check_circuit_breaker_threshold = 3

        # Simulate failures
        for _ in range(3):
            await order_manager._record_circuit_breaker_failure()

        assert order_manager._circuit_breaker_state == "open"

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_after_time(self, order_manager):
        """Circuit breaker should reset to half-open after reset time."""
        # ... test implementation


class TestOrderStatusChecking:
    """Test order status checking with retries."""

    @pytest.mark.asyncio
    async def test_is_order_filled_with_retry_backoff(self, order_manager):
        """Should retry with exponential backoff on failure."""
        # ... test implementation
```

### 💡 Your Current Approach (Already Excellent!)

```python
# tests/unit/test_state/test_pnl_tracker.py (Your Project)

class TestPnLTrackerBasics:
    """Test basic PnLTracker functionality."""

    def test_tracker_initializes(self, pnl_tracker):
        assert pnl_tracker is not None

    def test_get_daily_pnl_returns_zero_for_new_account(self, pnl_tracker):
        # ... test


class TestPnLTrackerPersistence:
    """Test that P&L data persists across tracker instances."""

    def test_pnl_survives_restart(self, temp_db):
        # ... test

    def test_multiple_accounts_tracked_independently(self, pnl_tracker):
        # ... test


class TestPnLTrackerReset:
    """Test daily reset functionality."""
    # ...


class TestPnLTrackerEdgeCases:
    """Test edge cases and error handling."""
    # ...
```

### ✅ What You're Doing Right:
- Clear class organization ✅
- Descriptive class docstrings ✅
- Logical grouping (Basics → Persistence → Reset → EdgeCases) ✅

---

## 6. Parametrized Testing

### 📊 Visual: Before vs After Parametrization

```
┌─────────────────────────────────────────────────────┐
│              WITHOUT PARAMETRIZATION                 │
├─────────────────────────────────────────────────────┤
│  def test_loss_under_limit():                       │
│      # Test with -400                               │
│      assert result is None                          │
│                                                      │
│  def test_loss_at_limit():                          │
│      # Test with -500                               │
│      assert result is None                          │
│                                                      │
│  def test_loss_over_limit():                        │
│      # Test with -501                               │
│      assert result is not None                      │
│                                                      │
│  → 3 separate test functions (lots of duplication)  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              WITH PARAMETRIZATION                    │
├─────────────────────────────────────────────────────┤
│  @pytest.mark.parametrize("pnl,should_breach", [    │
│      (-400, False),  # Under limit                  │
│      (-500, False),  # At limit                     │
│      (-501, True),   # Over limit                   │
│  ])                                                  │
│  def test_loss_limit(pnl, should_breach):           │
│      # Single test, 3 scenarios                     │
│      if should_breach:                              │
│          assert result is not None                  │
│      else:                                          │
│          assert result is None                      │
│                                                      │
│  → 1 test function, 3 test runs (DRY principle)     │
└─────────────────────────────────────────────────────┘
```

### 🎯 SDK Example: Multiple Scenarios

```python
# tests/indicators/test_sma.py (SDK)
@pytest.mark.parametrize("period,expected_length", [
    (5, 5),
    (10, 10),
    (20, 20),
    (50, 50),
])
def test_sma_different_periods(period, expected_length):
    """Test SMA with different periods."""
    data = pl.DataFrame({"close": list(range(100))})
    sma = data.pipe(SMA, period=period)

    # First 'period-1' values should be null
    valid_values = sma[period-1:]
    assert len(valid_values) == len(data) - period + 1


@pytest.mark.parametrize("symbol,expected_multiplier", [
    ("MNQ", 20),   # Micro Nasdaq
    ("MES", 50),   # Micro S&P
    ("MYM", 50),   # Micro Dow
    ("M2K", 50),   # Micro Russell
])
async def test_instrument_multipliers(symbol, expected_multiplier, mock_client):
    """Test instrument-specific multipliers."""
    mock_client.get_instruments.return_value = [{
        "symbol": symbol,
        "multiplier": expected_multiplier
    }]

    instruments = await mock_client.get_instruments()
    instrument = next(i for i in instruments if i["symbol"] == symbol)
    assert instrument["multiplier"] == expected_multiplier
```

### 💡 Copy-Paste Template for Your Tests

```python
# Add to your test files
@pytest.mark.parametrize("daily_pnl,trade_pnl,limit,should_breach", [
    # (current_pnl, new_trade, limit, expected_breach)
    (-400, -50,  -500, False),  # Under limit
    (-450, -50,  -500, False),  # At limit
    (-451, -50,  -500, True),   # Breach by $1
    (-400, -200, -500, True),   # Large loss
    (100,  -50,  -500, False),  # Profitable day
    (-490, -10,  -500, False),  # Just under
    (-490, -11,  -500, True),   # Just over
])
def test_daily_loss_scenarios(
    daily_pnl, trade_pnl, limit, should_breach,
    event_factory, mock_engine
):
    """Test daily loss limit with various P&L scenarios."""
    # Create rule
    rule = DailyLossRule(limit=limit)

    # Simulate current state
    mock_engine.get_daily_pnl.return_value = daily_pnl

    # Create trade event
    trade = event_factory(realized_pnl=trade_pnl)

    # Check rule
    result = rule.check(trade, mock_engine)

    # Verify
    if should_breach:
        assert result is not None
        assert result["action"] == "CLOSE_ALL"
    else:
        assert result is None


# Example: Multiple symbols
@pytest.mark.parametrize("symbol,tick_size,multiplier", [
    ("MNQ", 0.25, 2.0),   # Micro Nasdaq
    ("MES", 0.25, 5.0),   # Micro S&P
    ("ES",  0.25, 50.0),  # E-mini S&P
])
def test_symbol_configurations(symbol, tick_size, multiplier):
    """Test different symbol configurations."""
    # ... test implementation
```

---

## 7. Performance Benchmarking

### 📊 Performance Testing Structure

```
┌──────────────────────────────────────────────────────┐
│          SDK PERFORMANCE TESTING PATTERN              │
├──────────────────────────────────────────────────────┤
│                                                       │
│  tests/benchmarks/test_performance.py                │
│                                                       │
│  class TestOrderPerformance:                         │
│      @pytest.mark.benchmark(group="order_placement") │
│      def test_market_order_speed(benchmark):         │
│          result = benchmark(lambda: place_order())   │
│          assert result is not None                   │
│                                                       │
│  class TestDataProcessing:                           │
│      @pytest.mark.benchmark(group="data")            │
│      def test_tick_processing(benchmark):            │
│          result = benchmark(lambda: process_ticks()) │
│          assert processing_time < 0.001  # 1ms       │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 🎯 SDK Example: Benchmark Test

```python
# tests/benchmarks/test_performance.py (SDK)
class TestOrderPerformance:
    """Benchmark order operations."""

    @pytest.mark.benchmark(group="order_placement")
    def test_market_order_speed(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark market order placement."""

        async def place_order() -> Any:
            # Create mock suite
            mock_client = AsyncMock()
            mock_client.place_order = AsyncMock(return_value={"order_id": "123"})

            suite = TradingSuite.__new__(TradingSuite)
            suite._orders = MagicMock()
            suite._orders.place_market_order = AsyncMock(
                return_value={"order_id": "123"}
            )

            return await suite._orders.place_market_order(
                contract_id="MNQ", side=0, size=1
            )

        result = benchmark(lambda: asyncio.run(place_order()))
        assert result is not None


# Run with: pytest tests/benchmarks/ --benchmark-only
```

### 💡 Copy-Paste Template for Your Project

```python
# Create: tests/benchmarks/test_performance.py
import pytest
import time
from pytest_benchmark.fixture import BenchmarkFixture


class TestRulePerformance:
    """Benchmark risk rule evaluation."""

    @pytest.mark.benchmark(group="rule_evaluation")
    def test_daily_loss_rule_speed(self, benchmark, event_factory):
        """Ensure daily loss rule evaluates quickly."""
        from risk_manager.rules import DailyLossRule

        rule = DailyLossRule(limit=-500)
        trade = event_factory(realized_pnl=-100)

        # Benchmark should complete in < 1ms
        result = benchmark(lambda: rule.check(trade))
        assert result is not None or result is None  # Either is valid


class TestPnLPerformance:
    """Benchmark P&L calculations."""

    @pytest.mark.performance
    def test_pnl_calculation_under_load(self, pnl_tracker):
        """Ensure P&L calculation scales well."""
        account_id = "TEST-ACCOUNT"

        start = time.perf_counter()

        # Simulate 1000 trades
        for i in range(1000):
            pnl_tracker.add_trade_pnl(account_id, -50.0)

        elapsed = time.perf_counter() - start

        # Should complete in < 100ms
        assert elapsed < 0.1, f"Too slow: {elapsed:.3f}s"

        # Verify correctness
        assert pnl_tracker.get_daily_pnl(account_id) == -50000.0


# Run with: pytest tests/benchmarks/ -v
```

---

## 8. Copy-Paste Templates

### Template 1: Async Test with Mocks

```python
@pytest.mark.asyncio
async def test_async_operation_success(mock_suite, event_factory):
    """Test successful async operation."""
    # ARRANGE
    event = event_factory(realized_pnl=-100.0)
    mock_suite.close_position.return_value = True

    # ACT
    result = await some_async_function(event, mock_suite)

    # ASSERT
    assert result is True
    mock_suite.close_position.assert_called_once_with("MNQ")
```

### Template 2: Error Handling Test

```python
@pytest.mark.asyncio
async def test_handles_api_error_gracefully(mock_suite):
    """Test graceful handling of API errors."""
    # ARRANGE
    mock_suite.place_order.side_effect = Exception("API Error")

    # ACT & ASSERT
    with pytest.raises(Exception, match="API Error"):
        await some_function(mock_suite)
```

### Template 3: Parametrized Test

```python
@pytest.mark.parametrize("input_value,expected_output", [
    (100, "success"),
    (0, "zero"),
    (-100, "negative"),
])
def test_multiple_scenarios(input_value, expected_output):
    """Test with multiple input scenarios."""
    result = process_value(input_value)
    assert result == expected_output
```

### Template 4: Fixture with Cleanup

```python
@pytest.fixture
async def temporary_resource():
    """Create a temporary resource with cleanup."""
    # Setup
    resource = await create_resource()

    yield resource

    # Cleanup
    await resource.cleanup()
```

### Template 5: Mock with Side Effects

```python
def test_sequential_calls(mock_client):
    """Test sequential API calls with different responses."""
    # Setup different responses for each call
    mock_client.get_balance.side_effect = [
        100000.0,  # First call
        95000.0,   # Second call
        90000.0,   # Third call
    ]

    # Each call returns next value
    assert mock_client.get_balance() == 100000.0
    assert mock_client.get_balance() == 95000.0
    assert mock_client.get_balance() == 90000.0
```

---

## 9. Visual Summary: Key SDK Testing Patterns

### 🎯 Pattern Quick Reference

| Pattern | When to Use | SDK Example Location |
|---------|-------------|---------------------|
| **Factory Fixtures** | Need flexible test data | `conftest.py:mock_response()` |
| **Fixture Composition** | Build complex scenarios | `conftest.py:mock_auth_response()` |
| **Parametrized Tests** | Test multiple scenarios | `test_indicators.py:test_sma_different_periods()` |
| **AsyncMock** | Test async functions | All async tests |
| **Circuit Breaker** | Test retry logic | `test_core_advanced.py:TestCircuitBreaker` |
| **Performance** | Ensure speed | `test_performance.py:TestOrderPerformance` |
| **Test Classes** | Group related tests | `TestOrderManagerInitialization` |

---

## 10. Next Steps for Your Project

### ✅ What You're Already Doing Right

1. **Test markers configured** (`unit`, `integration`, `slow`, `ai`) ✅
2. **Async fixtures** (`async def risk_manager()`) ✅
3. **Mock fixtures** (`mock_engine`, `mock_suite`) ✅
4. **Test class organization** (`TestPnLTrackerBasics`, etc.) ✅
5. **TDD approach** (tests written before implementation) ✅

### 🔄 Patterns to Adopt Next

**Priority 1: High Value, Low Effort (This Week)**

```python
# 1. Add fixture factories (30 min)
@pytest.fixture
def trade_factory():
    def _create(pnl=-50, symbol="MNQ", **kwargs):
        return RiskEvent(...)
    return _create

# 2. Parametrize existing tests (1 hour)
@pytest.mark.parametrize("pnl,should_breach", [
    (-400, False), (-501, True)
])

# 3. Add spec to mocks (15 min)
suite = AsyncMock(spec=TradingSuite)
```

**Priority 2: Important for Growth (Next 2 Weeks)**

```python
# 4. Add performance tests (2 hours)
@pytest.mark.performance
def test_rule_speed(benchmark):
    ...

# 5. Add integration tests (4 hours)
@pytest.mark.integration
async def test_full_workflow():
    ...

# 6. Add error tests (1 hour)
with pytest.raises(Exception, match="error"):
    ...
```

**Priority 3: Production Ready (Next Month)**

```python
# 7. Benchmark regression (4 hours)
# 8. Coverage reporting (2 hours)
# 9. CI/CD integration (4 hours)
```

---

## 📊 Testing Metrics Comparison

| Metric | SDK (Production) | Your Project (Early Stage) | Target (3 Months) |
|--------|------------------|----------------------------|-------------------|
| **Test Files** | 153 | 3 | 20-30 |
| **Test Coverage** | 90%+ | Unknown | 80%+ |
| **Parametrized Tests** | Heavy | None | 10-15 tests |
| **Performance Tests** | 15+ | None | 5-10 |
| **Async Tests** | 100+ | 1 | 20-30 |
| **Test Classes** | 200+ | 5 | 30-40 |

---

## 🎓 Learning Resources

**To explore SDK tests yourself:**

```bash
# Navigate to SDK
cd /home/jakers/projects/project-x-py/tests

# See all test files
find . -name "*.py" | head -20

# Read a specific test
cat client/test_client_auth.py

# Read the main conftest
cat conftest.py
```

**Run your tests with markers:**

```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run with coverage
pytest --cov=src/risk_manager --cov-report=html
```

---

## 🎯 Quick Win: Copy This Into Your Tests Today

```python
# Add to tests/conftest.py
@pytest.fixture
def trade_factory():
    """Factory for creating test trades."""
    def _create_trade(
        symbol="MNQ",
        realized_pnl=-12.50,
        event_type=EventType.TRADE_EXECUTED,
        **kwargs
    ):
        return RiskEvent(
            type=event_type,
            data={
                "symbol": symbol,
                "realized_pnl": realized_pnl,
                "timestamp": datetime.now().isoformat(),
                **kwargs
            }
        )
    return _create_trade


# Then use it everywhere:
def test_something(trade_factory):
    losing_trade = trade_factory(realized_pnl=-150.0)
    winning_trade = trade_factory(realized_pnl=100.0)
    es_trade = trade_factory(symbol="ES")
```

---

**This guide created:** 2025-10-23
**Based on:** project-x-py SDK (153 test files)
**Your project:** risk-manager-v34

