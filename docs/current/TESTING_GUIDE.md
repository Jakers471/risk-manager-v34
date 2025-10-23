# Testing Guide - TDD Approach

**Test-Driven Development**: Write tests first, then implement

---

## 🎯 Testing Philosophy

### Red-Green-Refactor

```
1. 🔴 RED:    Write a failing test
2. 🟢 GREEN:  Write minimal code to make it pass
3. 🔵 REFACTOR: Clean up the code
4. Repeat
```

### Why TDD?

- ✅ **Design First**: Tests force you to think about API design
- ✅ **Confidence**: Know it works before shipping
- ✅ **Regression Prevention**: Tests catch breaks
- ✅ **Documentation**: Tests show how code should be used
- ✅ **Refactor Safely**: Change code without fear

---

## 📁 Test Structure

```
tests/
├── conftest.py                 # Pytest configuration & fixtures
├── __init__.py
│
├── unit/                       # Fast, isolated tests
│   ├── __init__.py
│   │
│   ├── test_core/              # Core components
│   │   ├── test_manager.py
│   │   ├── test_engine.py
│   │   ├── test_events.py
│   │   └── test_config.py
│   │
│   ├── test_rules/             # Each risk rule
│   │   ├── test_max_position.py
│   │   ├── test_daily_loss.py
│   │   ├── test_trade_frequency.py
│   │   └── ...
│   │
│   ├── test_sdk/               # SDK wrapper
│   │   ├── test_suite_manager.py
│   │   ├── test_event_bridge.py
│   │   └── test_enforcement.py
│   │
│   └── test_state/             # State management
│       ├── test_lockout_manager.py
│       ├── test_pnl_tracker.py
│       └── test_persistence.py
│
├── integration/                # Slow, full-stack tests
│   ├── __init__.py
│   ├── test_end_to_end.py      # Complete workflows
│   ├── test_sdk_live.py        # Real SDK connection
│   └── test_persistence.py     # Database integration
│
└── fixtures/                   # Shared test data
    ├── __init__.py
    ├── sample_events.py        # Sample event data
    ├── sample_positions.py     # Sample positions
    └── sample_config.yaml      # Test configuration
```

---

## 🏃 Running Tests

### All Tests
```bash
uv run pytest
```

### With Coverage
```bash
uv run pytest --cov=risk_manager --cov-report=html
# Opens htmlcov/index.html
```

### Specific Test File
```bash
uv run pytest tests/unit/test_rules/test_daily_loss.py
```

### Specific Test
```bash
uv run pytest tests/unit/test_rules/test_daily_loss.py::test_daily_loss_enforcement
```

### Only Unit Tests
```bash
uv run pytest tests/unit/
```

### Only Integration Tests (slower)
```bash
uv run pytest tests/integration/ -v
```

### Watch Mode (re-run on changes)
```bash
uv run pytest-watch
```

---

## 📝 Writing Tests

### Example: TDD Workflow for New Rule

#### Step 1: Write Failing Test (RED 🔴)

```python
# tests/unit/test_rules/test_trade_frequency.py
import pytest
from datetime import datetime
from risk_manager.rules import TradeFrequencyRule
from risk_manager.core.events import RiskEvent, EventType

@pytest.mark.asyncio
async def test_blocks_when_frequency_exceeded():
    """Test that rule blocks trading when frequency limit exceeded."""
    # Arrange
    rule = TradeFrequencyRule(
        max_per_minute=3,
        max_per_hour=10,
    )

    # Simulate 3 trades in one minute
    trades = [
        create_trade_event(datetime.now()),
        create_trade_event(datetime.now()),
        create_trade_event(datetime.now()),
    ]

    # Act
    for trade in trades:
        await rule.evaluate(trade, mock_engine)

    # Try 4th trade (should be blocked)
    result = await rule.evaluate(create_trade_event(datetime.now()), mock_engine)

    # Assert
    assert result.blocked is True
    assert "frequency limit" in result.reason.lower()
    assert result.cooldown_seconds > 0
```

**Run test**: `pytest tests/unit/test_rules/test_trade_frequency.py`

**Result**: ❌ FAILS (TradeFrequencyRule doesn't exist yet)

---

#### Step 2: Write Minimal Code (GREEN 🟢)

```python
# src/risk_manager/rules/trade_frequency.py
from datetime import datetime, timedelta
from risk_manager.rules import RiskRule
from risk_manager.core.events import RiskEvent

class TradeFrequencyRule(RiskRule):
    """RULE-006: Trade Frequency Limit"""

    def __init__(self, max_per_minute: int, max_per_hour: int):
        super().__init__(action="pause")
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.trade_history: list[datetime] = []

    async def evaluate(self, event: RiskEvent, engine):
        if event.type != EventType.TRADE_EXECUTED:
            return None

        now = datetime.now()
        self.trade_history.append(now)

        # Check last minute
        one_minute_ago = now - timedelta(minutes=1)
        recent_trades = [t for t in self.trade_history if t > one_minute_ago]

        if len(recent_trades) > self.max_per_minute:
            return RuleResult(
                blocked=True,
                reason=f"Trade frequency limit: {len(recent_trades)}/{self.max_per_minute} per minute",
                cooldown_seconds=60
            )

        return None
```

**Run test**: `pytest tests/unit/test_rules/test_trade_frequency.py`

**Result**: ✅ PASSES

---

#### Step 3: Refactor (REFACTOR 🔵)

```python
# Refactor: Extract method, add hour check
class TradeFrequencyRule(RiskRule):
    # ... (same as above)

    async def evaluate(self, event: RiskEvent, engine):
        if event.type != EventType.TRADE_EXECUTED:
            return None

        now = datetime.now()
        self.trade_history.append(now)

        # Clean old trades (memory management)
        self._clean_old_trades(now)

        # Check both minute and hour limits
        minute_check = self._check_minute_limit(now)
        if minute_check:
            return minute_check

        hour_check = self._check_hour_limit(now)
        if hour_check:
            return hour_check

        return None

    def _check_minute_limit(self, now: datetime) -> RuleResult | None:
        one_minute_ago = now - timedelta(minutes=1)
        recent = [t for t in self.trade_history if t > one_minute_ago]

        if len(recent) > self.max_per_minute:
            return RuleResult(
                blocked=True,
                reason=f"Exceeded {self.max_per_minute} trades/minute",
                cooldown_seconds=60
            )
        return None

    def _check_hour_limit(self, now: datetime) -> RuleResult | None:
        # Similar logic
        pass

    def _clean_old_trades(self, now: datetime):
        # Remove trades older than 1 hour (keep memory low)
        cutoff = now - timedelta(hours=1)
        self.trade_history = [t for t in self.trade_history if t > cutoff]
```

**Run test**: `pytest tests/unit/test_rules/test_trade_frequency.py`

**Result**: ✅ STILL PASSES (refactor didn't break anything)

---

#### Step 4: Add More Tests

```python
# tests/unit/test_rules/test_trade_frequency.py

@pytest.mark.asyncio
async def test_allows_within_limit():
    """Test that trading is allowed when within limits."""
    rule = TradeFrequencyRule(max_per_minute=5, max_per_hour=20)

    # 2 trades (under limit)
    for _ in range(2):
        result = await rule.evaluate(create_trade_event(), mock_engine)
        assert result is None  # No block


@pytest.mark.asyncio
async def test_cooldown_expires():
    """Test that cooldown expires after time passes."""
    # TODO: Implement
    pass


@pytest.mark.asyncio
async def test_tracks_per_instrument():
    """Test that limits can be per-instrument."""
    # TODO: Implement
    pass
```

---

## 🧩 Test Fixtures

### conftest.py

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, Mock
from risk_manager.core.engine import RiskEngine
from risk_manager.core.events import RiskEvent, EventType

@pytest.fixture
def mock_engine():
    """Mock RiskEngine for unit tests."""
    engine = AsyncMock(spec=RiskEngine)
    engine.account_id = "TEST-ACCOUNT-123"
    engine.suite_manager = AsyncMock()
    return engine


@pytest.fixture
def sample_trade_event():
    """Sample trade event for testing."""
    return RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={
            "symbol": "MNQ",
            "side": "Buy",
            "quantity": 1,
            "price": 20125.0,
            "realized_pnl": -12.50,
            "timestamp": "2025-10-23T14:30:00Z"
        }
    )


@pytest.fixture
def sample_position():
    """Sample position for testing."""
    return {
        "symbol": "MNQ",
        "quantity": 2,
        "average_price": 20100.0,
        "current_price": 20125.0,
        "unrealized_pnl": 50.0
    }


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

---

## 🎨 Testing Patterns

### Pattern 1: Arrange-Act-Assert (AAA)

```python
async def test_daily_loss_enforcement():
    # Arrange: Set up test data
    rule = DailyLossRule(limit=-500)
    trade = create_losing_trade(amount=-600)  # Over limit

    # Act: Execute the code under test
    result = await rule.evaluate(trade, mock_engine)

    # Assert: Verify the outcome
    assert result.action == "flatten"
    assert result.lockout_until is not None
```

---

### Pattern 2: Mocking SDK

```python
from unittest.mock import AsyncMock

async def test_enforcement_closes_position():
    # Mock SDK
    mock_suite = AsyncMock()
    mock_suite.close_position = AsyncMock()

    # Test enforcement
    enforcement = EnforcementActions(mock_suite)
    await enforcement.flatten("MNQ")

    # Verify SDK was called
    mock_suite.close_position.assert_called_once()
```

---

### Pattern 3: Parametrize for Multiple Cases

```python
@pytest.mark.parametrize("pnl,should_trigger", [
    (-400, False),  # Under limit
    (-500, True),   # At limit
    (-600, True),   # Over limit
    (100, False),   # Positive (profit)
])
async def test_daily_loss_various_amounts(pnl, should_trigger):
    rule = DailyLossRule(limit=-500)
    trade = create_trade(realized_pnl=pnl)

    result = await rule.evaluate(trade, mock_engine)

    if should_trigger:
        assert result.action == "flatten"
    else:
        assert result is None
```

---

### Pattern 4: Testing Async Code

```python
@pytest.mark.asyncio  # Required for async tests
async def test_async_enforcement():
    enforcement = EnforcementActions(suite_manager)

    # Test async method
    result = await enforcement.flatten_all("account-123")

    assert result.success is True
```

---

## 📊 Coverage Goals

### Target Coverage
- **Overall**: >80%
- **Critical Paths** (risk rules, enforcement): >95%
- **SDK Wrapper**: >90%
- **CLI**: >70%

### Generate Coverage Report
```bash
uv run pytest --cov=risk_manager --cov-report=html
open htmlcov/index.html  # Opens in browser
```

### Coverage in CI/CD
```bash
# Fail if coverage below 80%
uv run pytest --cov=risk_manager --cov-fail-under=80
```

---

## 🔍 Integration Testing

### Testing with Real SDK

```python
# tests/integration/test_sdk_live.py
import pytest

@pytest.mark.integration  # Mark as integration test
@pytest.mark.asyncio
async def test_connect_to_live_account():
    """Integration test: Connect to real TopstepX account."""
    from project_x_py import TradingSuite

    # Real connection (requires credentials in .env)
    suite = await TradingSuite.create(instruments=["MNQ"])

    # Verify connection
    assert suite is not None

    # Get real stats
    stats = await suite.get_stats()
    assert stats.account_id == "PRAC-V2-126244-84184528"

    # Cleanup
    await suite.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_enforcement():
    """Integration test: Full enforcement workflow."""
    from risk_manager import RiskManager

    # Create real risk manager
    rm = await RiskManager.create(
        instruments=["MNQ"],
        rules={"daily_loss_limit": -10}  # Low limit for testing
    )

    # Start monitoring
    await rm.start()

    # Simulate breach (in test environment)
    # ... trigger enforcement ...

    # Verify enforcement happened
    # ...

    # Cleanup
    await rm.stop()
```

### Run Integration Tests Separately
```bash
# Unit tests (fast)
pytest tests/unit/  # Run frequently

# Integration tests (slow, requires connection)
pytest tests/integration/ -v  # Run before commits
```

---

## 🧪 Test Data & Fixtures

### Sample Events
```python
# tests/fixtures/sample_events.py

def create_trade_event(symbol="MNQ", pnl=-12.50):
    return RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={
            "symbol": symbol,
            "realized_pnl": pnl,
            "timestamp": datetime.now().isoformat()
        }
    )

def create_position_event(symbol="MNQ", quantity=2):
    return RiskEvent(
        type=EventType.POSITION_UPDATED,
        data={
            "symbol": symbol,
            "quantity": quantity,
            "unrealized_pnl": 50.0
        }
    )
```

---

## 📋 Test Checklist (Before Commit)

### Before Every Commit
- [ ] All tests pass (`pytest`)
- [ ] Coverage >80% (`pytest --cov`)
- [ ] No warnings in test output
- [ ] New code has tests
- [ ] Tests are fast (<5 seconds for unit tests)

### Before Merge to Main
- [ ] Integration tests pass
- [ ] All rules tested
- [ ] Edge cases covered
- [ ] Error handling tested
- [ ] Documentation updated

---

## 🎓 TDD Example: Complete Workflow

### Scenario: Implement RULE-003 (Daily Realized Loss)

#### 1. Write Test First
```python
# tests/unit/test_rules/test_daily_realized_loss.py

@pytest.mark.asyncio
async def test_enforces_daily_loss_limit():
    # ARRANGE
    rule = DailyRealizedLossRule(limit=-500, reset_time="17:00")
    mock_stats = Mock(realized_pl=-600)  # Over limit
    mock_suite = AsyncMock()
    mock_suite.get_stats.return_value = mock_stats

    # ACT
    trade_event = create_trade_event(realized_pnl=-600)
    result = await rule.evaluate(trade_event, mock_engine)

    # ASSERT
    assert result.action == "flatten"
    assert result.lockout_until.hour == 17  # Reset at 5 PM
```

#### 2. Run Test (Fails)
```bash
$ pytest tests/unit/test_rules/test_daily_realized_loss.py
# ❌ FAILED: DailyRealizedLossRule not found
```

#### 3. Implement Minimal Code
```python
# src/rules/daily_realized_loss.py
class DailyRealizedLossRule(RiskRule):
    async def evaluate(self, event, engine):
        stats = await engine.suite.get_stats()
        if stats.realized_pl <= self.limit:
            return RuleResult(
                action="flatten",
                lockout_until=self.get_reset_time()
            )
```

#### 4. Run Test (Passes)
```bash
$ pytest tests/unit/test_rules/test_daily_realized_loss.py
# ✅ PASSED
```

#### 5. Add More Tests
```python
async def test_allows_within_limit():
    # Test trading allowed when under limit
    pass

async def test_resets_at_5pm():
    # Test lockout clears at reset time
    pass
```

#### 6. Refactor & Clean
```python
# Extract methods, improve readability, add type hints
```

---

## 🚀 Quick Reference

### Common Test Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific file
pytest tests/unit/test_rules/test_daily_loss.py

# Run in watch mode
pytest-watch

# Run only fast tests
pytest -m "not integration"

# Show print statements
pytest -s

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run last failed
pytest --lf
```

---

## 📖 Further Reading

- **pytest docs**: https://docs.pytest.org/
- **TDD Guide**: Kent Beck - "Test-Driven Development by Example"
- **Our fixtures**: `tests/conftest.py`
- **Integration tests**: `tests/integration/`

---

**Last Updated**: 2025-10-23
**See Also**:
- `CLAUDE.md` - Main entry point
- `docs/current/PROJECT_STATUS.md` - Current implementation
