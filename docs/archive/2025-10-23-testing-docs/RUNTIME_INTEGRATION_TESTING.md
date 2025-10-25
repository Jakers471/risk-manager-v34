# Runtime Integration Testing Guide

**Preventing "Green Tests But Broken Runtime" Syndrome**

This guide solves the most frustrating problem in testing: **tests pass but nothing works in production**. Based on analyzing why your previous risk manager failed at runtime despite passing tests, and how the SDK prevents this.

---

## Table of Contents

1. [The Problem: Green Tests, Broken Runtime](#the-problem-green-tests-broken-runtime)
2. [Root Cause Analysis](#root-cause-analysis)
3. [SDK's Solution: The Testing Pyramid](#sdks-solution-the-testing-pyramid)
4. [Your Current Testing Gaps](#your-current-testing-gaps)
5. [Integration Testing Strategy](#integration-testing-strategy)
6. [Testing Critical Paths](#testing-critical-paths)
7. [Mock/Real Boundaries](#mockreal-boundaries)
8. [Smoke Tests for Runtime Validation](#smoke-tests-for-runtime-validation)
9. [Logging & Observability Tests](#logging--observability-tests)
10. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)

---

## The Problem: Green Tests, Broken Runtime

### Your Previous Experience:

```python
# Terminal 1: Running tests
$ pytest tests/
================================ test session starts ================================
collected 47 items

tests/unit/test_rules/test_daily_loss.py ✅ PASSED
tests/unit/test_rules/test_max_contracts.py ✅ PASSED
tests/unit/test_enforcement.py ✅ PASSED
tests/unit/test_logging.py ✅ PASSED
tests/unit/test_events.py ✅ PASSED

================================ 47 passed in 2.35s =================================
😊 "All tests pass! This is ready!"
```

```python
# Terminal 2: Running actual risk manager
$ python -m risk_manager start

✅ Risk Manager starting...
✅ Loading configuration...
✅ Initializing components...
✅ Ready.

# Trading happens...
❌ Rules NOT enforcing (positions allowed beyond limits)
❌ Logs NOT appearing (no output files created)
❌ Events NOT detected (API responses ignored)
❌ SDK NOT communicating (positions not closing)

😰 "But all the tests passed!!!"
```

### Why This Happens:

**Tests validated mocks, not reality:**

```python
# Your test (from conftest.py lines 32-54)
@pytest.fixture
def mock_suite():
    """Mock TradingSuite (SDK) for testing."""
    suite = AsyncMock()
    suite.close_position = AsyncMock()  # ← Mocked!
    # ...

def test_enforcement():
    """Test enforcement closes positions."""
    # ARRANGE
    rule = DailyLossRule(max_loss=-1000.0)
    event = RiskEvent(realized_pnl=-1500.0)

    # ACT
    await rule.enforce(mock_suite)  # ← Using mock!

    # ASSERT
    mock_suite.close_position.assert_called_once()  # ← ✅ PASSES
    # But says NOTHING about whether REAL SDK would work!
```

**At runtime:**
```python
# Real SDK has different signature:
real_suite.close_position(symbol="MNQ")  # ← Requires symbol!
# Your code:
real_suite.close_position()  # ← Missing parameter!
# Error: TypeError: close_position() missing 1 required positional argument: 'symbol'

# But test passed because mock accepts any call!
```

---

## Root Cause Analysis

### What Went Wrong in Previous Risk Manager

#### Problem 1: Over-Mocking

**Your conftest.py (lines 21-62):**

```python
@pytest.fixture
def mock_engine():
    """Mock RiskEngine for unit tests."""
    engine = AsyncMock()  # ← Everything is AsyncMock!
    engine.account_id = "TEST-ACCOUNT-123"
    engine.suite_manager = AsyncMock()  # ← This too!
    engine.lockout_manager = AsyncMock()  # ← And this!
    engine.event_bus = AsyncMock()  # ← Everything!
    return engine

@pytest.fixture
def mock_suite():
    """Mock TradingSuite (SDK) for testing."""
    suite = AsyncMock()  # ← SDK completely mocked
    suite.close_position = AsyncMock()
    suite.cancel_all_orders = AsyncMock()
    suite.place_order = AsyncMock()
    # ... ALL SDK methods mocked
```

**Result:**
- ✅ Tests pass (mocks always succeed)
- ❌ Runtime fails (real SDK has different behavior)

**Why mocks lie:**

```python
# Mock accepts ANY call
mock_suite.close_position()  # ✅ Works
mock_suite.close_position("MNQ")  # ✅ Works
mock_suite.close_position(1, 2, 3, foo="bar")  # ✅ Still works!
mock_suite.nonexistent_method()  # ✅ Even this works!

# Real SDK is strict
real_suite.close_position()  # ❌ TypeError: missing required argument
real_suite.close_position("MNQ")  # ✅ Correct
real_suite.nonexistent_method()  # ❌ AttributeError
```

#### Problem 2: No Integration Layer Tests

**Your current test structure:**

```
tests/
├── unit/                    # ← All tests are here
│   ├── test_core/
│   ├── test_rules/
│   └── test_state/
│
└── integration/             # ← MISSING!
```

**What's missing:**
```python
# No tests for:
✗ Real event flow (event → rule → enforcement → SDK)
✗ Real SDK integration (actual API calls)
✗ Real logging (files actually created)
✗ Real database persistence (SQLite operations)
✗ Real configuration loading (YAML parsing)
```

#### Problem 3: Testing Signatures, Not Behavior

```python
# What you tested (signature)
mock_suite.close_position.assert_called_once()  # ✅ Method was called

# What you didn't test (behavior)
# - Was the RIGHT method called?
# - With the RIGHT parameters?
# - Did it actually CLOSE the position?
# - Did the SDK respond correctly?
# - Did logging record it?
# - Did database update?
```

#### Problem 4: No Runtime Smoke Tests

```python
# No tests for actual startup:
✗ Does config load from YAML?
✗ Does database initialize?
✗ Do loguru handlers attach?
✗ Does SDK connect?
✗ Do event listeners register?
✗ Does the system actually START?
```

---

## SDK's Solution: The Testing Pyramid

### From SDK's `testing.md`:

```
             ┌────────────────┐
             │   E2E Tests    │  ← Few (slow, comprehensive)
             │  (1-2 tests)   │
             ├────────────────┤
             │  Integration   │  ← Some (medium speed)
             │   (10-20 tests)│
             ├────────────────┤
             │  Unit Tests    │  ← Many (fast, isolated)
             │  (100+ tests)  │
             └────────────────┘
```

**SDK's testing.md breakdown:**

1. **Unit Tests (70% of tests)**
   - Fast (< 0.1s each)
   - Isolated (mock external deps)
   - Test single functions/methods
   - **Example:** `test_calculate_position_size()`

2. **Integration Tests (25% of tests)**
   - Medium speed (< 2s each)
   - Real components interacting
   - Mock only external APIs
   - **Example:** `test_order_manager_with_client()`

3. **End-to-End Tests (5% of tests)**
   - Slow (> 5s each)
   - Full system flow
   - Real SDK, real data structures
   - **Example:** `test_full_trading_workflow()`

### Your Current Reality:

```
             ┌────────────────┐
             │   E2E Tests    │
             │  (0 tests!)    │  ← ❌ MISSING!
             ├────────────────┤
             │  Integration   │
             │  (0 tests!)    │  ← ❌ MISSING!
             ├────────────────┤
             │  Unit Tests    │
             │  (3 files)     │  ← ✅ Only this exists
             └────────────────┘
```

**This is why runtime fails!** You only tested the bottom layer.

---

## Your Current Testing Gaps

### Analysis of Existing Tests

#### ✅ What You Have:

**1. `tests/conftest.py` (228 lines)**
```python
# Good fixtures:
✅ mock_engine - Basic engine mock
✅ mock_suite - SDK mock for unit tests
✅ sample_trade_event - Event fixtures
✅ temp_db - Temporary database fixture
✅ pnl_tracker - Real PnLTracker instance
```

**2. `tests/unit/test_state/test_pnl_tracker.py` (214 lines)**
```python
# Excellent TDD example:
✅ TestPnLTrackerBasics - Unit tests
✅ TestPnLTrackerPersistence - Database tests
✅ TestPnLTrackerReset - Reset logic tests
✅ TestPnLTrackerTradeCount - Counter tests
✅ TestPnLTrackerEdgeCases - Edge cases

# Uses REAL database (temp_db fixture)
# This is GOOD - tests actual persistence!
```

#### ❌ What You're Missing:

**1. SDK Integration Tests**
```python
# tests/integration/test_sdk_integration.py - DOESN'T EXIST
# Should test:
❌ Real TradingSuite initialization
❌ Real event flow to SDK
❌ Real enforcement actions calling SDK
❌ Real SDK responses handling
```

**2. Event Flow Integration**
```python
# tests/integration/test_event_pipeline.py - DOESN'T EXIST
# Should test:
❌ Event published → EventBus receives → Rule evaluates → Action enforced
❌ Multiple rules processing same event
❌ Event priority handling
❌ Event error propagation
```

**3. Enforcement Flow Tests**
```python
# tests/integration/test_enforcement_flow.py - DOESN'T EXIST
# Should test:
❌ Rule violation → EnforcementExecutor called → SDK action taken
❌ Enforcement logging
❌ Enforcement error handling
❌ Enforcement retry logic
```

**4. Logging Tests**
```python
# tests/integration/test_logging.py - DOESN'T EXIST
# Should test:
❌ Log files actually created
❌ Log rotation works
❌ Log levels filter correctly
❌ Structured logging format correct
```

**5. Configuration Tests**
```python
# tests/integration/test_configuration.py - DOESN'T EXIST
# Should test:
❌ YAML config loads correctly
❌ Environment variables override
❌ Invalid config rejected
❌ Default values applied
```

**6. Startup/Shutdown Tests**
```python
# tests/integration/test_lifecycle.py - DOESN'T EXIST
# Should test:
❌ System starts successfully
❌ All components initialize
❌ Shutdown is graceful
❌ Resources cleaned up
```

---

## Integration Testing Strategy

### Create Integration Test Directory

```bash
# Create structure
mkdir -p tests/integration
touch tests/integration/__init__.py
touch tests/integration/test_sdk_integration.py
touch tests/integration/test_enforcement_flow.py
touch tests/integration/test_event_pipeline.py
touch tests/integration/test_logging.py
touch tests/integration/test_configuration.py
touch tests/integration/test_lifecycle.py
```

### Integration Test Template

```python
# tests/integration/test_sdk_integration.py

"""
Integration tests for SDK integration.

These tests use REAL components with minimal mocking.
They test that our code actually works with the real SDK.
"""

import pytest
from unittest.mock import AsyncMock, patch
from project_x_py import TradingSuite  # Real SDK!

from risk_manager.sdk.suite_manager import SuiteManager
from risk_manager.sdk.enforcement import EnforcementExecutor
from risk_manager.core.events import RiskEvent, EventType


@pytest.mark.integration
class TestSDKIntegrationBasics:
    """Test basic SDK integration works."""

    @pytest.mark.asyncio
    async def test_suite_manager_creates_real_suite(self):
        """
        Test that SuiteManager can create a real TradingSuite instance.

        This tests:
        - SuiteManager.add_suite() works
        - TradingSuite can be instantiated
        - Suite is stored correctly
        """
        # ARRANGE
        manager = SuiteManager()

        # ACT - Create REAL suite (but don't connect to API)
        with patch('project_x_py.TradingSuite.create') as mock_create:
            # Mock ONLY the API connection, not the SDK itself
            mock_suite = AsyncMock(spec=TradingSuite)
            mock_suite.symbol = "MNQ"
            mock_create.return_value = mock_suite

            suite = await TradingSuite.create("MNQ")
            manager.add_suite("MNQ", suite)

        # ASSERT
        retrieved_suite = manager.get_suite("MNQ")
        assert retrieved_suite is not None
        assert retrieved_suite.symbol == "MNQ"

    @pytest.mark.asyncio
    async def test_enforcement_executor_uses_real_sdk_interface(self):
        """
        Test that EnforcementExecutor calls real SDK methods correctly.

        This tests:
        - Correct method signatures
        - Correct parameter passing
        - Correct return value handling
        """
        # ARRANGE
        manager = SuiteManager()

        # Use REAL TradingSuite interface (but mock the API)
        mock_suite = AsyncMock(spec=TradingSuite)  # spec= ensures real interface
        mock_suite.positions.get_all_positions = AsyncMock(return_value=[
            {"symbol": "MNQ", "quantity": 2}
        ])
        mock_suite.positions.close_position = AsyncMock(return_value=True)

        manager.add_suite("MNQ", mock_suite)
        executor = EnforcementExecutor(manager)

        # ACT
        result = await executor.close_all_positions("MNQ")

        # ASSERT - Verify REAL SDK method was called correctly
        assert result["success"] is True
        mock_suite.positions.close_position.assert_called_once_with("MNQ")
        # ↑ If signature is wrong, this will fail!


@pytest.mark.integration
class TestEventFlowIntegration:
    """Test complete event flow through the system."""

    @pytest.mark.asyncio
    async def test_trade_event_triggers_rule_enforcement(self):
        """
        Test full flow: Event → Rule → Enforcement → SDK

        This is a CRITICAL integration test that catches runtime issues.
        """
        # ARRANGE - Use REAL components
        from risk_manager.core.engine import RiskEngine
        from risk_manager.core.events import EventBus
        from risk_manager.core.config import RiskConfig
        from risk_manager.rules.daily_loss import DailyLossRule

        # Real event bus
        event_bus = EventBus()

        # Real config
        config = RiskConfig(
            rules={"daily_loss": {"max_loss": -1000.0}}
        )

        # Real engine
        engine = RiskEngine(config, event_bus)

        # Real rule
        rule = DailyLossRule(max_loss=-1000.0)
        engine.add_rule(rule)

        # Mock ONLY the final SDK call
        mock_suite = AsyncMock(spec=TradingSuite)
        mock_suite.positions.close_all_positions = AsyncMock()

        # Setup enforcement executor with mock suite
        manager = SuiteManager()
        manager.add_suite("MNQ", mock_suite)
        engine.enforcement_executor = EnforcementExecutor(manager)

        # ACT - Trigger real event flow
        event = RiskEvent(
            type=EventType.TRADE_EXECUTED,
            data={"symbol": "MNQ", "realized_pnl": -1500.0}  # Exceeds limit
        )

        await engine.evaluate_rules(event)

        # ASSERT - Verify SDK was called (real enforcement happened)
        mock_suite.positions.close_all_positions.assert_called()
        # If ANY part of the chain is broken, this fails!
```

### Key Differences from Unit Tests

| Aspect | Unit Test | Integration Test |
|--------|-----------|------------------|
| **Speed** | < 0.1s | 0.5-2s |
| **Scope** | Single function | Multiple components |
| **Mocking** | Mock everything external | Mock only APIs |
| **Purpose** | Test logic | Test integration |
| **Failure** | Logic bug | Interface mismatch |
| **Example** | `test_calculate_pnl()` | `test_event_flow_end_to_end()` |

---

## Testing Critical Paths

### Identify Critical Runtime Paths

**Critical Path 1: Rule Enforcement**

```
┌──────────────────────────────────────────────────────────────┐
│ Critical Path: Rule Violation → Position Closed             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Trade executed (API event)                              │
│     ↓                                                        │
│  2. EventBridge receives event                              │
│     ↓                                                        │
│  3. RiskEvent created                                       │
│     ↓                                                        │
│  4. EventBus publishes event                                │
│     ↓                                                        │
│  5. RiskEngine.evaluate_rules(event)                        │
│     ↓                                                        │
│  6. DailyLossRule.evaluate() detects violation              │
│     ↓                                                        │
│  7. RiskEngine._handle_violation() called                   │
│     ↓                                                        │
│  8. EnforcementExecutor.close_all_positions()               │
│     ↓                                                        │
│  9. SuiteManager.get_suite("MNQ")                           │
│     ↓                                                        │
│ 10. TradingSuite.positions.close_position("MNQ")            │
│     ↓                                                        │
│ 11. SDK sends API request to close position                 │
│     ↓                                                        │
│ 12. Position actually closes in broker account              │
│                                                              │
└──────────────────────────────────────────────────────────────┘

❌ Your unit tests covered steps 6-7 only
✅ Integration test must cover steps 1-11
```

**Test this path:**

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_critical_path_rule_enforcement_end_to_end():
    """
    Test the COMPLETE enforcement path.

    This test catches integration issues that unit tests miss.
    """
    # ARRANGE - Build real pipeline
    from risk_manager.core.engine import RiskEngine
    from risk_manager.core.events import EventBus
    from risk_manager.sdk.event_bridge import EventBridge
    from risk_manager.sdk.suite_manager import SuiteManager
    from risk_manager.sdk.enforcement import EnforcementExecutor
    from risk_manager.rules.daily_loss import DailyLossRule

    # 1. Real event bus
    event_bus = EventBus()

    # 2. Real risk engine
    config = RiskConfig(rules={"daily_loss": {"max_loss": -1000.0}})
    engine = RiskEngine(config, event_bus)

    # 3. Real rule
    rule = DailyLossRule(max_loss=-1000.0)
    engine.add_rule(rule)

    # 4. Real suite manager (mock only the SDK API)
    suite_manager = SuiteManager()
    mock_suite = AsyncMock(spec=TradingSuite)
    mock_suite.positions.close_all_positions = AsyncMock(return_value=True)
    suite_manager.add_suite("MNQ", mock_suite)

    # 5. Real enforcement executor
    executor = EnforcementExecutor(suite_manager)
    engine.enforcement_executor = executor

    # 6. Real event bridge
    bridge = EventBridge(event_bus)

    # ACT - Simulate real trade event from SDK
    sdk_trade_event = {
        "symbol": "MNQ",
        "realized_pnl": -1500.0,  # Exceeds -1000 limit
        "timestamp": "2025-10-23T12:00:00Z"
    }

    # Bridge converts SDK event → RiskEvent
    await bridge.handle_trade_event(sdk_trade_event)

    # Give event time to propagate through system
    await asyncio.sleep(0.1)

    # ASSERT - Verify entire chain worked
    mock_suite.positions.close_all_positions.assert_called_once()

    # If ANY step failed, this assertion fails!
    # - Event bridge didn't convert event? Fail
    # - Event bus didn't publish? Fail
    # - Engine didn't evaluate? Fail
    # - Rule didn't detect violation? Fail
    # - Enforcement didn't execute? Fail
    # - SDK wasn't called? Fail
```

**Critical Path 2: Logging**

```python
@pytest.mark.integration
def test_critical_path_logging_actually_works(tmp_path):
    """
    Test that logging actually creates log files.

    This catches configuration issues that unit tests miss.
    """
    from risk_manager.core.engine import RiskEngine
    from loguru import logger

    # ARRANGE - Configure real logging to temp directory
    log_file = tmp_path / "risk_manager.log"

    # Configure loguru to write to test file
    logger.add(log_file, format="{time} {level} {message}")

    # ACT - Generate real log messages
    engine = RiskEngine(config, event_bus)
    await engine.start()

    # Trigger actions that should log
    await engine.evaluate_rules(event)

    # Wait for log flush
    import time
    time.sleep(0.1)

    # ASSERT - Verify log file exists and has content
    assert log_file.exists(), "Log file was not created!"

    log_content = log_file.read_text()
    assert "Risk Engine started" in log_content
    assert "evaluating rule" in log_content.lower()

    # If logging isn't configured right, this fails!
```

**Critical Path 3: Database Persistence**

```python
@pytest.mark.integration
def test_critical_path_pnl_persists_across_restarts(tmp_path):
    """
    Test that P&L actually persists when system restarts.

    This catches database issues that unit tests miss.
    """
    from risk_manager.state.database import Database
    from risk_manager.state.pnl_tracker import PnLTracker

    # ARRANGE
    db_path = tmp_path / "test_risk.db"
    account_id = "TEST-ACCOUNT"

    # ACT - First session: Add P&L
    db1 = Database(db_path)
    tracker1 = PnLTracker(db1)
    tracker1.add_trade_pnl(account_id, -500.0)

    # Simulate system shutdown
    db1.close()
    del tracker1
    del db1

    # ACT - Second session: Restart system
    db2 = Database(db_path)  # Reopen same database
    tracker2 = PnLTracker(db2)

    # ASSERT - Data should still be there
    pnl = tracker2.get_daily_pnl(account_id)
    assert pnl == -500.0, "P&L did not persist across restart!"

    db2.close()
```

---

## Mock/Real Boundaries

### The Golden Rule: Mock at System Boundaries

```
┌───────────────────────────────────────────────────────────┐
│                    Your System                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ✅ Use REAL components                             │   │
│  │                                                     │   │
│  │  RiskEngine → Rules → EventBus → Enforcement       │   │
│  │                                                     │   │
│  └────────────────────────────────┬───────────────────┘   │
│                                   │                       │
│                                   ↓                       │
│  ┌────────────────────────────────┴───────────────────┐   │
│  │ ⚠️ Mock ONLY at the boundary                       │   │
│  │                                                     │   │
│  │  Mock TradingSuite API calls                       │   │
│  │  (because you can't call real broker in tests)     │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
                                   │
                                   ↓
                          ┌────────────────┐
                          │  Real Broker   │
                          │  (Production)  │
                          └────────────────┘
```

### Good Mock Boundaries

```python
# ✅ GOOD - Mock only the SDK API layer
from project_x_py import TradingSuite

mock_suite = AsyncMock(spec=TradingSuite)  # spec= ensures real interface!
mock_suite.positions.close_position = AsyncMock()

# Use REAL components for everything else
real_engine = RiskEngine(config, event_bus)
real_rule = DailyLossRule(max_loss=-1000.0)
real_enforcer = EnforcementExecutor(suite_manager)

# Test real flow, mock only SDK
await real_engine.evaluate_rules(event)
mock_suite.positions.close_position.assert_called()  # ✅ Verifies integration
```

```python
# ❌ BAD - Mocking internal components
mock_engine = AsyncMock()  # ❌ Don't mock your own code!
mock_rule = AsyncMock()    # ❌ This defeats the purpose!

await mock_engine.evaluate_rules(event)
# ❌ This tests nothing - just that mocks can call mocks
```

### Spec-Based Mocking

**Always use `spec=` to ensure real interface:**

```python
# ✅ GOOD - spec= enforces real interface
from project_x_py import TradingSuite

mock_suite = AsyncMock(spec=TradingSuite)

# This will FAIL if signature is wrong
mock_suite.positions.close_position("MNQ")  # ✅ Correct
mock_suite.positions.close_position()       # ❌ Fails - missing symbol!

# ✅ Catches integration bugs in tests!
```

```python
# ❌ BAD - No spec, accepts anything
mock_suite = AsyncMock()  # No spec!

# These all "work" even if wrong
mock_suite.positions.close_position()            # "Works"
mock_suite.nonexistent_method()                  # "Works"
mock_suite.close_position(wrong_params=True)     # "Works"

# ❌ Doesn't catch integration bugs!
```

---

## Smoke Tests for Runtime Validation

### What Are Smoke Tests?

**Smoke tests** are minimal tests that verify the system can actually start and perform basic operations. Think of them as "does the engine turn on?"

### Create Smoke Test Suite

```python
# tests/integration/test_smoke.py

"""
Smoke tests for runtime validation.

These tests verify the system can actually start and run.
Run these BEFORE deploying to catch basic integration issues.
"""

import pytest
from pathlib import Path


@pytest.mark.integration
class TestSmokeBasics:
    """Basic smoke tests - system can start."""

    def test_imports_work(self):
        """Test that all main modules can be imported."""
        # If imports fail, system won't start
        from risk_manager import RiskManager
        from risk_manager.core import RiskEngine, EventBus
        from risk_manager.rules import DailyLossRule
        from risk_manager.sdk import SuiteManager, EnforcementExecutor

        # Just importing is enough - if broken, this fails

    @pytest.mark.asyncio
    async def test_risk_manager_can_start(self):
        """Test that RiskManager can actually start."""
        from risk_manager import RiskManager

        # ACT - Try to start the system
        rm = await RiskManager.create(
            instruments=["MNQ"],
            config_path=None  # Use defaults
        )

        # ASSERT - System started without errors
        assert rm is not None
        assert rm.running is True

        # Cleanup
        await rm.stop()

    @pytest.mark.asyncio
    async def test_configuration_loads(self, tmp_path):
        """Test that YAML configuration actually loads."""
        from risk_manager.core.config import RiskConfig

        # Create test config file
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
rules:
  daily_loss:
    enabled: true
    max_loss: -1000.0
  max_contracts:
    enabled: true
    max_contracts: 5
        """)

        # ACT - Load config
        config = RiskConfig.from_yaml(config_file)

        # ASSERT - Config loaded correctly
        assert config.rules["daily_loss"]["max_loss"] == -1000.0
        assert config.rules["max_contracts"]["max_contracts"] == 5

    @pytest.mark.asyncio
    async def test_database_initializes(self, tmp_path):
        """Test that database actually initializes."""
        from risk_manager.state.database import Database

        # ACT - Create database
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        # ASSERT - Database file created
        assert db_path.exists()

        # ASSERT - Can write and read
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        db.execute("INSERT INTO test (value) VALUES (?)", ("test_data",))
        result = db.execute("SELECT value FROM test WHERE id = 1").fetchone()

        assert result[0] == "test_data"

        db.close()

    @pytest.mark.asyncio
    async def test_logging_creates_files(self, tmp_path):
        """Test that logging actually creates log files."""
        from loguru import logger

        # Configure logging to temp directory
        log_file = tmp_path / "test.log"
        logger.add(log_file, format="{message}")

        # Write log message
        logger.info("Test message")

        # Give logger time to flush
        import time
        time.sleep(0.1)

        # ASSERT - Log file exists and has content
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content


@pytest.mark.integration
class TestSmokeEventFlow:
    """Smoke tests for event flow."""

    @pytest.mark.asyncio
    async def test_events_actually_publish_and_receive(self):
        """Test that EventBus actually works."""
        from risk_manager.core.events import EventBus, EventType, RiskEvent

        # ARRANGE
        event_bus = EventBus()
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Subscribe handler
        await event_bus.subscribe(EventType.TRADE_EXECUTED, handler)

        # ACT - Publish event
        event = RiskEvent(
            type=EventType.TRADE_EXECUTED,
            data={"test": "data"}
        )
        await event_bus.publish(event)

        # Give event time to propagate
        await asyncio.sleep(0.1)

        # ASSERT - Event was received
        assert len(received_events) == 1
        assert received_events[0].data["test"] == "data"


@pytest.mark.integration
class TestSmokeSDKIntegration:
    """Smoke tests for SDK integration."""

    @pytest.mark.asyncio
    async def test_can_create_suite_manager(self):
        """Test that SuiteManager can be created."""
        from risk_manager.sdk.suite_manager import SuiteManager

        manager = SuiteManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_can_create_enforcement_executor(self):
        """Test that EnforcementExecutor can be created."""
        from risk_manager.sdk.suite_manager import SuiteManager
        from risk_manager.sdk.enforcement import EnforcementExecutor

        manager = SuiteManager()
        executor = EnforcementExecutor(manager)

        assert executor is not None
        assert executor.suite_manager is manager
```

### Run Smoke Tests Before Every Deployment

```bash
# Quick smoke test
pytest tests/integration/test_smoke.py -v

# If smoke tests fail, DO NOT deploy!
# Fix integration issues first.
```

---

## Logging & Observability Tests

### Test Logging Actually Works

```python
# tests/integration/test_logging.py

"""
Integration tests for logging system.

These verify that logging actually works at runtime.
"""

import pytest
from pathlib import Path
from loguru import logger


@pytest.mark.integration
class TestLoggingIntegration:
    """Test logging creates actual log files with correct content."""

    def test_log_file_created(self, tmp_path):
        """Test that log files are actually created."""
        log_file = tmp_path / "risk_manager.log"

        # Configure logger
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO"
        )

        # Write logs
        logger.info("Risk Manager started")
        logger.warning("Test warning")

        # Flush
        import time
        time.sleep(0.1)

        # ASSERT - File exists
        assert log_file.exists(), "Log file not created!"

        # ASSERT - Content is correct
        content = log_file.read_text()
        assert "Risk Manager started" in content
        assert "Test warning" in content
        assert "INFO" in content
        assert "WARNING" in content

    def test_log_rotation_works(self, tmp_path):
        """Test that log rotation actually creates new files."""
        log_file = tmp_path / "risk_manager.log"

        # Configure with rotation
        logger.add(
            log_file,
            rotation="100 bytes",  # Rotate after 100 bytes
            format="{message}"
        )

        # Write enough to trigger rotation
        for i in range(20):
            logger.info(f"Message {i}" * 10)  # Long messages

        import time
        time.sleep(0.2)

        # ASSERT - Multiple log files created
        log_files = list(tmp_path.glob("risk_manager.log*"))
        assert len(log_files) > 1, "Log rotation didn't create new files!"

    def test_structured_logging_format(self, tmp_path):
        """Test that structured logging works correctly."""
        log_file = tmp_path / "structured.log"

        # Configure structured logging (JSON)
        logger.add(
            log_file,
            format="{message}",
            serialize=True  # JSON output
        )

        # Write structured log
        logger.bind(
            rule="DailyLossRule",
            violation="max_loss_exceeded",
            pnl=-1500.0
        ).warning("Rule violation detected")

        import time
        time.sleep(0.1)

        # ASSERT - JSON format
        content = log_file.read_text()
        import json
        log_entry = json.loads(content.strip())

        assert log_entry["record"]["extra"]["rule"] == "DailyLossRule"
        assert log_entry["record"]["extra"]["violation"] == "max_loss_exceeded"
        assert log_entry["record"]["extra"]["pnl"] == -1500.0

    @pytest.mark.asyncio
    async def test_logging_in_real_event_flow(self, tmp_path):
        """Test that logging works in actual event processing."""
        log_file = tmp_path / "event_flow.log"

        logger.add(log_file, format="{message}")

        # Use real components
        from risk_manager.core.engine import RiskEngine
        from risk_manager.core.events import EventBus, RiskEvent, EventType
        from risk_manager.rules.daily_loss import DailyLossRule

        event_bus = EventBus()
        engine = RiskEngine(config, event_bus)
        rule = DailyLossRule(max_loss=-1000.0)
        engine.add_rule(rule)

        # Trigger event that should log
        event = RiskEvent(
            type=EventType.TRADE_EXECUTED,
            data={"realized_pnl": -1500.0}
        )

        await engine.evaluate_rules(event)

        import time
        time.sleep(0.1)

        # ASSERT - Logs contain expected messages
        content = log_file.read_text()
        assert "evaluating rule" in content.lower() or "rule violation" in content.lower()
```

---

## Quick Diagnostic Checklist

### When Runtime Fails But Tests Pass

**Run through this checklist:**

#### 1. Are you testing the right layer?

```bash
# Check your test files
find tests/ -name "test_*.py" -type f

# You should have:
✅ tests/unit/          # Fast isolated tests
✅ tests/integration/   # Real component interaction tests
❌ Missing integration/ ? That's your problem!
```

#### 2. Are you mocking too much?

```python
# Check your conftest.py
grep -n "AsyncMock\|Mock" tests/conftest.py

# Count mocks:
# - 1-3 fixtures: ✅ OK
# - 5+ fixtures all AsyncMock: ❌ Too much mocking!
```

#### 3. Do you have spec-based mocks?

```bash
# Check if mocks use spec=
grep -n "AsyncMock()" tests/  # ❌ No spec
grep -n "AsyncMock(spec=" tests/  # ✅ Has spec

# If no spec= found, add it!
```

#### 4. Do integration tests exist?

```bash
# Check for integration tests
pytest tests/ --collect-only | grep integration

# Should see:
# tests/integration/test_sdk_integration.py
# tests/integration/test_enforcement_flow.py
# etc.

# If none found, CREATE THEM!
```

#### 5. Can the system actually start?

```bash
# Try starting the system
python -m risk_manager start

# Should NOT see:
# ❌ ImportError
# ❌ ConfigurationError
# ❌ DatabaseError
# ❌ Silent failure (nothing happens)
```

#### 6. Does logging work?

```bash
# Check if log files are created
ls -la logs/ data/ *.log 2>/dev/null

# If no logs found:
# ❌ Logging not configured
# ❌ Log directory doesn't exist
# ❌ Permissions issue
```

#### 7. Does configuration load?

```bash
# Check config loading
python -c "
from risk_manager.core.config import RiskConfig
config = RiskConfig.from_yaml('config/risk_config.yaml')
print(config)
"

# Should print config
# If error: ❌ Config loading broken
```

---

## Summary: Preventing "Green Tests But Broken Runtime"

### The Core Problem

```
Tests validate mocks, not reality
├── Unit tests: Mock everything → Tests pass
├── No integration tests → Gaps not caught
└── Runtime: Real SDK has different behavior → Everything fails
```

### The Solution

```
1. Test Pyramid
   ├── 70% Unit Tests (mock external deps)
   ├── 25% Integration Tests (real components)
   └── 5% E2E Tests (full system)

2. Mock at Boundaries
   ├── Mock: External APIs, broker connections
   └── Real: Your code, event flow, rules, enforcement

3. Spec-Based Mocks
   └── Always use spec= to enforce real interfaces

4. Critical Path Tests
   ├── Test: Event → Rule → Enforcement → SDK
   ├── Test: Logging actually creates files
   └── Test: Database actually persists

5. Smoke Tests
   ├── System can start
   ├── Config loads
   ├── Database initializes
   └── Logging works
```

### Action Items

#### Immediate (Do This Now):

1. **Create integration test directory:**
   ```bash
   mkdir -p tests/integration
   cp docs/examples/test_sdk_integration.py tests/integration/
   ```

2. **Add spec= to all mocks:**
   ```python
   # Edit tests/conftest.py
   # Change: mock_suite = AsyncMock()
   # To: mock_suite = AsyncMock(spec=TradingSuite)
   ```

3. **Write first integration test:**
   ```bash
   # Create tests/integration/test_smoke.py
   # Copy smoke test examples from this guide
   ```

4. **Run integration tests:**
   ```bash
   pytest tests/integration/ -v
   # Fix any failures before continuing!
   ```

#### Short Term (This Week):

5. **Test critical paths:**
   - [ ] Event flow end-to-end
   - [ ] Rule enforcement with SDK
   - [ ] Logging creates files
   - [ ] Database persists data

6. **Add smoke tests:**
   - [ ] System starts
   - [ ] Config loads
   - [ ] All imports work

7. **Test markers:**
   ```bash
   pytest -m unit       # Fast tests
   pytest -m integration  # Real component tests
   pytest -m "not slow"  # Skip slow tests
   ```

#### Long Term (Next Sprint):

8. **Increase integration coverage:**
   - Target: 50+ integration tests
   - Cover all critical paths
   - Test all SDK interactions

9. **Add E2E tests:**
   - Full trading workflow
   - Complete lifecycle test
   - Multi-rule interaction tests

10. **CI/CD integration:**
    ```yaml
    # Add to .github/workflows/test.yml
    - name: Integration Tests
      run: pytest tests/integration/ -v
    ```

---

## Final Checklist: Is Your Runtime Actually Tested?

**Before deploying, ensure:**

- [ ] Integration tests exist (`tests/integration/` directory)
- [ ] Critical paths tested (event → rule → enforcement → SDK)
- [ ] Smoke tests pass (system starts, config loads, logs work)
- [ ] Mocks use `spec=` (enforce real interfaces)
- [ ] SDK integration tested with real TradingSuite interface
- [ ] Logging creates actual files (tested)
- [ ] Database persists across restarts (tested)
- [ ] Configuration loads from YAML (tested)
- [ ] Can start system without errors: `python -m risk_manager start`
- [ ] Log files appear when system runs
- [ ] Can see actual enforcement in logs
- [ ] SDK methods called correctly (verified in integration tests)

**If any checkbox is unchecked, you're at risk of "green tests but broken runtime"!**

---

*This guide analyzes the gap between unit tests and runtime behavior, providing actionable strategies to ensure your tests actually validate that the system works in production.*
