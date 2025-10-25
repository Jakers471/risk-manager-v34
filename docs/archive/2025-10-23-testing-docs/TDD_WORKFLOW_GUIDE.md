# TDD Workflow Guide for Risk Manager

**Based on project-x-py SDK Testing Methodology**

This guide shows you exactly how to implement Test-Driven Development (TDD) for the risk manager, following the proven patterns from the project-x-py SDK that powers this system.

---

## Table of Contents

1. [Critical Understanding: Why TDD Matters](#critical-understanding-why-tdd-matters)
2. [The SDK's Workflow (What We're Copying)](#the-sdks-workflow-what-were-copying)
3. [Your Risk Manager Workflow](#your-risk-manager-workflow)
4. [Step-by-Step TDD Process](#step-by-step-tdd-process)
5. [Test Organization](#test-organization)
6. [Fixture Patterns](#fixture-patterns)
7. [When to Write What](#when-to-write-what)
8. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
9. [Quick Reference](#quick-reference)

---

## Critical Understanding: Why TDD Matters

### ❌ What You Did Before (Build-Then-Test):
```python
# 1. Built 10 risk rules
src/risk_manager/rules/
    daily_loss.py
    max_contracts.py
    max_position.py
    ... 7 more rules

# 2. Then tried to test all 10
tests/... (tests written after)

# 3. Result: Tests pass but runtime fails
✅ pytest: All tests pass
❌ Runtime: Rules don't enforce, logs don't work, API doesn't respond
```

### ✅ What SDK Does (Test-Then-Build):
```python
# 1. Write ONE test for ONE feature
tests/test_order_manager.py:
    def test_place_market_order_success(): ...

# 2. Run test (it fails - no code yet)
❌ FAILED - OrderManager has no attribute 'place_market_order'

# 3. Write MINIMAL code to make test pass
src/order_manager.py:
    async def place_market_order(self, ...): ...

# 4. Run test again
✅ PASSED

# 5. Repeat for next feature
```

**Key Difference:** SDK writes tests WHILE coding, not AFTER. Each feature is tested IMMEDIATELY.

---

## The SDK's Workflow (What We're Copying)

### From `project-x-py/docs/development/contributing.md`:

```bash
# 1. Create Feature Branch
git checkout -b feature/your-feature

# 2. Make Changes (THIS IS WHERE TDD HAPPENS)
   - Write code following standards
   - Add/update tests for your changes  ← TESTS DURING CODING
   - Update documentation if needed
   - Ensure all existing tests pass      ← TESTS RUN CONTINUOUSLY

# 3. Test Locally (BEFORE COMMITTING)
uv run pytest                    # Run all tests
uv run ruff check .              # Check code quality
uv run mypy src/                 # Type checking
./test.sh examples/script.py     # Test real usage

# 4. Commit Changes (ONLY IF TESTS PASS)
git add .
git commit -m "feat: add feature"

# 5. Push and Create PR
```

### Critical Pattern from SDK:
```python
# SDK's contributing.md lines 80-98 shows:

# Step 2 is NOT:
# - Write all code first
# - Then write tests later

# Step 2 IS:
# - Write test for Feature A
# - Implement Feature A
# - Test passes ✅
# - Write test for Feature B
# - Implement Feature B
# - Test passes ✅
# - Repeat...
```

---

## Your Risk Manager Workflow

### Current Project Structure:
```
risk-manager-v34/
├── src/risk_manager/
│   ├── core/
│   │   ├── engine.py          # Risk engine (22 source files total)
│   │   ├── events.py          # Event system
│   │   └── manager.py         # Main manager
│   ├── rules/
│   │   ├── daily_loss.py      # Risk rules
│   │   ├── max_contracts_per_instrument.py
│   │   └── max_position.py
│   ├── sdk/
│   │   ├── enforcement.py     # SDK integration
│   │   ├── event_bridge.py    # Event bridging
│   │   └── suite_manager.py   # Suite management
│   └── state/
│       ├── database.py        # SQLite persistence
│       └── pnl_tracker.py     # P&L tracking
│
└── tests/
    ├── conftest.py            # Shared fixtures (228 lines)
    ├── unit/
    │   ├── test_core/
    │   │   └── test_events.py
    │   └── test_state/
    │       └── test_pnl_tracker.py  # Example TDD test (214 lines)
    └── integration/           # ⚠️ MISSING - Add this!
```

### Apply SDK Workflow to Risk Manager:

```bash
# Example: Adding a new "Max Drawdown" rule

# 1. Create feature branch
git checkout -b feature/max-drawdown-rule

# 2. TDD Cycle (THIS IS THE CRITICAL PART)

# 2a. Write test FIRST
cat > tests/unit/test_rules/test_max_drawdown.py << 'EOF'
import pytest
from risk_manager.rules.max_drawdown import MaxDrawdownRule
from risk_manager.core.events import RiskEvent, EventType

class TestMaxDrawdownBasics:
    """Test basic max drawdown rule functionality."""

    @pytest.mark.asyncio
    async def test_triggers_when_drawdown_exceeds_limit(self):
        """Test rule triggers when drawdown exceeds configured limit."""
        # ARRANGE
        rule = MaxDrawdownRule(max_drawdown_pct=0.10)  # 10% max
        event = RiskEvent(
            type=EventType.TRADE_EXECUTED,
            data={"realized_pnl": -5000.0}  # Large loss
        )
        mock_engine = Mock()
        mock_engine.peak_balance = 50000.0  # Peak was $50k
        mock_engine.daily_pnl = -5000.0     # Down to $45k = 10% drawdown

        # ACT
        violation = await rule.evaluate(event, mock_engine)

        # ASSERT
        assert violation is not None
        assert violation["action"] == "flatten"
        assert "10.0%" in violation["message"]
EOF

# 2b. Run test (should FAIL - code doesn't exist yet)
pytest tests/unit/test_rules/test_max_drawdown.py -v
# ❌ FAILED - ModuleNotFoundError: No module named 'risk_manager.rules.max_drawdown'

# 2c. Write MINIMAL code to make test pass
cat > src/risk_manager/rules/max_drawdown.py << 'EOF'
"""Max drawdown risk rule."""
from risk_manager.rules.base import RiskRule
from risk_manager.core.events import RiskEvent

class MaxDrawdownRule(RiskRule):
    """Enforce maximum drawdown limit."""

    def __init__(self, max_drawdown_pct: float):
        self.max_drawdown_pct = max_drawdown_pct

    async def evaluate(self, event: RiskEvent, engine) -> dict | None:
        """Check if drawdown exceeds limit."""
        if engine.peak_balance == 0:
            return None

        current_balance = engine.peak_balance + engine.daily_pnl
        drawdown_pct = (engine.peak_balance - current_balance) / engine.peak_balance

        if drawdown_pct >= self.max_drawdown_pct:
            return {
                "action": "flatten",
                "message": f"Drawdown {drawdown_pct*100:.1f}% exceeds limit {self.max_drawdown_pct*100:.1f}%"
            }
        return None
EOF

# 2d. Run test again (should PASS now)
pytest tests/unit/test_rules/test_max_drawdown.py -v
# ✅ PASSED

# 2e. Add MORE tests for edge cases (STILL BEFORE MOVING ON)
# Add to test_max_drawdown.py:
    @pytest.mark.asyncio
    async def test_does_not_trigger_below_limit(self):
        """Test rule does not trigger when drawdown is acceptable."""
        # ... test implementation

    @pytest.mark.asyncio
    async def test_handles_zero_peak_balance(self):
        """Test rule handles zero peak balance edge case."""
        # ... test implementation

# 2f. Run ALL tests (ensure nothing broke)
pytest tests/ -v
# ✅ All tests pass

# 3. Test Locally BEFORE COMMITTING
pytest tests/                    # All tests
python -m pytest --cov           # Coverage check
python -m ruff check .           # Linting
python -m mypy src/              # Type checking

# 4. Commit (ONLY IF ALL TESTS PASS)
git add .
git commit -m "feat: add max drawdown rule with comprehensive tests"

# 5. Push
git push origin feature/max-drawdown-rule
```

---

## Step-by-Step TDD Process

### The Red-Green-Refactor Cycle

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD CYCLE                                │
│                                                             │
│  1. RED    → Write test → Test FAILS (no code yet)        │
│              ├─ Think: What should this feature do?        │
│              └─ Write: Test describing the behavior        │
│                                                             │
│  2. GREEN  → Write code → Test PASSES (minimal impl)       │
│              ├─ Write: Simplest code to make test pass     │
│              └─ Verify: Test now passes                    │
│                                                             │
│  3. REFACTOR → Improve code → Tests STILL PASS             │
│                ├─ Clean up: Remove duplication             │
│                ├─ Optimize: Better performance             │
│                └─ Verify: All tests still pass             │
│                                                             │
│  4. REPEAT  → Next feature → Back to step 1                │
└─────────────────────────────────────────────────────────────┘
```

### Concrete Example: Adding Position Limit Rule

#### Step 1: RED (Write Test First)

```python
# tests/unit/test_rules/test_position_limit.py

import pytest
from unittest.mock import AsyncMock
from risk_manager.rules.position_limit import PositionLimitRule
from risk_manager.core.events import RiskEvent, EventType

class TestPositionLimitBasics:
    """Test basic position limit functionality."""

    @pytest.mark.asyncio
    async def test_blocks_order_exceeding_limit(self):
        """
        GIVEN a position limit rule configured for 5 contracts
        WHEN an order would bring total position to 6 contracts
        THEN the rule should trigger a violation
        """
        # ARRANGE
        rule = PositionLimitRule(max_contracts=5)

        # Mock engine with current position of 4 contracts
        mock_engine = AsyncMock()
        mock_engine.current_positions = {
            "MNQ": {"quantity": 4}  # Already have 4
        }

        # Event: Trying to buy 2 more (would be 6 total)
        event = RiskEvent(
            type=EventType.ORDER_SUBMITTED,
            data={
                "symbol": "MNQ",
                "side": "Buy",
                "quantity": 2  # 4 + 2 = 6 (exceeds 5)
            }
        )

        # ACT
        violation = await rule.evaluate(event, mock_engine)

        # ASSERT
        assert violation is not None, "Should have triggered violation"
        assert violation["action"] == "reject_order"
        assert "6 contracts" in violation["message"]
        assert "exceeds limit of 5" in violation["message"]
```

**Run test:**
```bash
pytest tests/unit/test_rules/test_position_limit.py -v
```

**Expected output:**
```
❌ FAILED - ModuleNotFoundError: No module named 'risk_manager.rules.position_limit'
```

**Perfect!** Test fails because code doesn't exist yet. This is RED phase.

#### Step 2: GREEN (Write Minimal Code)

```python
# src/risk_manager/rules/position_limit.py

"""Position limit rule to prevent over-leveraging."""

from risk_manager.rules.base import RiskRule
from risk_manager.core.events import RiskEvent, EventType

class PositionLimitRule(RiskRule):
    """Enforce maximum position size per instrument."""

    def __init__(self, max_contracts: int):
        """
        Initialize position limit rule.

        Args:
            max_contracts: Maximum allowed contracts per instrument
        """
        self.max_contracts = max_contracts

    async def evaluate(self, event: RiskEvent, engine) -> dict | None:
        """
        Evaluate if position would exceed limit.

        Returns:
            Violation dict if limit exceeded, None otherwise
        """
        # Only check order events
        if event.type != EventType.ORDER_SUBMITTED:
            return None

        symbol = event.data.get("symbol")
        new_quantity = event.data.get("quantity", 0)

        # Get current position
        current_position = engine.current_positions.get(symbol, {})
        current_quantity = current_position.get("quantity", 0)

        # Calculate total if this order fills
        total_quantity = current_quantity + new_quantity

        # Check limit
        if total_quantity > self.max_contracts:
            return {
                "action": "reject_order",
                "message": (
                    f"Order would bring position to {total_quantity} contracts, "
                    f"exceeds limit of {self.max_contracts}"
                ),
                "severity": "high"
            }

        return None
```

**Run test again:**
```bash
pytest tests/unit/test_rules/test_position_limit.py -v
```

**Expected output:**
```
✅ PASSED - test_blocks_order_exceeding_limit
```

**Perfect!** Test passes. This is GREEN phase.

#### Step 3: REFACTOR (Add More Tests)

Before moving to next feature, add edge case tests:

```python
# Add to tests/unit/test_rules/test_position_limit.py

class TestPositionLimitEdgeCases:
    """Test edge cases for position limit."""

    @pytest.mark.asyncio
    async def test_allows_order_within_limit(self):
        """Should allow orders that stay within limit."""
        rule = PositionLimitRule(max_contracts=5)

        mock_engine = AsyncMock()
        mock_engine.current_positions = {"MNQ": {"quantity": 3}}

        event = RiskEvent(
            type=EventType.ORDER_SUBMITTED,
            data={"symbol": "MNQ", "quantity": 1}  # 3 + 1 = 4 (OK)
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is None, "Should not trigger for valid order"

    @pytest.mark.asyncio
    async def test_handles_no_existing_position(self):
        """Should handle case where no position exists yet."""
        rule = PositionLimitRule(max_contracts=5)

        mock_engine = AsyncMock()
        mock_engine.current_positions = {}  # No position

        event = RiskEvent(
            type=EventType.ORDER_SUBMITTED,
            data={"symbol": "MNQ", "quantity": 3}  # First order
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is None, "Should allow first position"

    @pytest.mark.asyncio
    async def test_ignores_non_order_events(self):
        """Should ignore events that aren't orders."""
        rule = PositionLimitRule(max_contracts=5)

        mock_engine = AsyncMock()

        event = RiskEvent(
            type=EventType.TRADE_EXECUTED,  # Not an order
            data={"symbol": "MNQ", "quantity": 100}
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is None, "Should ignore non-order events"
```

**Run all tests:**
```bash
pytest tests/unit/test_rules/ -v
```

**Expected:**
```
✅ test_blocks_order_exceeding_limit PASSED
✅ test_allows_order_within_limit PASSED
✅ test_handles_no_existing_position PASSED
✅ test_ignores_non_order_events PASSED
```

#### Step 4: REPEAT (Next Feature)

Now move to next feature (e.g., "Sell orders reduce position"):

```python
# Add to test file
class TestPositionLimitSellOrders:
    """Test position limit with sell orders."""

    @pytest.mark.asyncio
    async def test_sell_orders_reduce_position(self):
        """Sell orders should reduce position, not increase it."""
        # ... write test first
        # ... implement feature
        # ... verify test passes
```

---

## Test Organization

### Current Structure:
```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_core/
│   │   └── test_events.py
│   ├── test_rules/          # ← Add your rule tests here
│   │   ├── test_daily_loss.py
│   │   ├── test_max_contracts.py
│   │   └── test_position_limit.py
│   └── test_state/
│       └── test_pnl_tracker.py
│
└── integration/             # ⚠️ CREATE THIS
    ├── test_sdk_integration.py
    ├── test_enforcement_flow.py
    └── test_event_pipeline.py
```

### Test File Naming (From SDK):
```python
# src/risk_manager/rules/daily_loss.py
# tests/unit/test_rules/test_daily_loss.py
#       ^^^^         ^^^^^
#       |            └─ test_ prefix
#       └─ mirrors source structure

# Pattern:
# src/{module}/{file}.py  →  tests/unit/test_{module}/test_{file}.py
```

### Test Class Organization (From SDK and Your pnl_tracker.py):

```python
# tests/unit/test_state/test_pnl_tracker.py (lines 38-214)
# Shows excellent TDD organization:

class TestPnLTrackerBasics:
    """Test basic PnLTracker functionality."""
    # Simple, foundational tests

class TestPnLTrackerPersistence:
    """Test that P&L data persists across tracker instances."""
    # Database persistence tests

class TestPnLTrackerReset:
    """Test daily reset functionality."""
    # Reset and cleanup tests

class TestPnLTrackerTradeCount:
    """Test trade count tracking."""
    # Counter tests

class TestPnLTrackerEdgeCases:
    """Test edge cases and error handling."""
    # Edge cases and error handling

# Pattern: Group related tests into classes
# Each class focuses on ONE aspect
```

---

## Fixture Patterns

### Your Current Fixtures (conftest.py lines 20-62):

```python
# tests/conftest.py

@pytest.fixture
def mock_engine():
    """Mock RiskEngine for unit tests."""
    engine = AsyncMock()
    engine.account_id = "TEST-ACCOUNT-123"
    engine.suite_manager = AsyncMock()
    engine.lockout_manager = AsyncMock()
    engine.event_bus = AsyncMock()
    return engine

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

### Add SDK-Style Fixture Factories:

```python
# Add to tests/conftest.py

# ============================================================================
# Fixture Factories (SDK Pattern)
# ============================================================================

@pytest.fixture
def event_factory():
    """
    Factory fixture for creating test events.

    Usage:
        def test_something(event_factory):
            trade_event = event_factory(realized_pnl=-100.0)
            order_event = event_factory(type=EventType.ORDER_SUBMITTED)
    """
    def _create_event(
        type: EventType = EventType.TRADE_EXECUTED,
        **data
    ) -> RiskEvent:
        """Create a test event with custom data."""
        default_data = {
            "symbol": "MNQ",
            "timestamp": datetime.now().isoformat()
        }
        default_data.update(data)

        return RiskEvent(type=type, data=default_data)

    return _create_event


@pytest.fixture
def engine_factory():
    """
    Factory fixture for creating test engines with custom state.

    Usage:
        def test_something(engine_factory):
            engine = engine_factory(daily_pnl=-500.0, peak_balance=10000.0)
    """
    def _create_engine(
        daily_pnl: float = 0.0,
        peak_balance: float = 100000.0,
        current_positions: dict = None
    ):
        """Create a mock engine with custom state."""
        engine = AsyncMock()
        engine.account_id = "TEST-ACCOUNT-123"
        engine.daily_pnl = daily_pnl
        engine.peak_balance = peak_balance
        engine.current_positions = current_positions or {}
        engine.suite_manager = AsyncMock()
        engine.event_bus = AsyncMock()
        return engine

    return _create_engine
```

**Using Factories in Tests:**

```python
# Before (hardcoded)
def test_rule(self):
    event = RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={"symbol": "MNQ", "realized_pnl": -100.0, "timestamp": "2025-10-23"}
    )

# After (factory)
def test_rule(self, event_factory):
    event = event_factory(realized_pnl=-100.0)  # Much cleaner!
```

---

## When to Write What

### Unit Tests (Write for EVERY feature)

**When:** Testing single components in isolation
**Where:** `tests/unit/test_{module}/`
**Mock Level:** High (mock all external dependencies)

```python
# Unit test example (from your pnl_tracker.py)
@pytest.mark.unit
def test_add_trade_pnl_updates_daily_total(self, pnl_tracker):
    """Test that adding trade P&L updates daily total."""
    account_id = "TEST-ACCOUNT-001"
    today = date.today()

    # Add first trade
    pnl_tracker.add_trade_pnl(account_id, -100.0, today)
    assert pnl_tracker.get_daily_pnl(account_id, today) == -100.0
```

**Write unit test when:**
- ✅ Adding new rule class
- ✅ Adding new method to existing class
- ✅ Changing logic in existing method
- ✅ Adding edge case handling

### Integration Tests (Write for CRITICAL paths)

**When:** Testing components working together
**Where:** `tests/integration/`
**Mock Level:** Low (use real components where possible)

```python
# Integration test example (YOU NEED TO ADD THESE)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rule_enforcement_end_to_end():
    """
    Test complete enforcement flow:
    1. Event triggered
    2. Rule evaluates
    3. Violation detected
    4. Enforcement action executed
    5. SDK called correctly
    """
    # ARRANGE - Use REAL components
    engine = RiskEngine(config, event_bus)
    rule = DailyLossRule(max_loss=-1000.0)
    engine.add_rule(rule)

    # Use REAL suite manager (but mock SDK underneath)
    suite_manager = SuiteManager()
    mock_suite = AsyncMock()  # Only mock the SDK
    suite_manager.add_suite("MNQ", mock_suite)

    enforcer = EnforcementExecutor(suite_manager)

    # ACT - Trigger real event flow
    event = RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={"realized_pnl": -1500.0}  # Exceeds limit
    )

    await engine.evaluate_rules(event)

    # ASSERT - Verify REAL enforcement happened
    mock_suite.close_position.assert_called_once()
```

**Write integration test when:**
- ✅ Adding new component that interacts with others
- ✅ Changing event flow
- ✅ Adding new enforcement action
- ✅ SDK integration changes

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Writing All Code First

```python
# WRONG - Writing features without tests
# src/risk_manager/rules/
    daily_loss.py        # ← Built
    max_contracts.py     # ← Built
    max_position.py      # ← Built
    max_drawdown.py      # ← Built
    trailing_stop.py     # ← Built

# tests/... (empty)      # ← No tests yet!

# Result: Builds up technical debt
```

```python
# RIGHT - Test-then-build for EACH feature
# Feature 1:
tests/test_daily_loss.py   # ← Write test
src/rules/daily_loss.py    # ← Build to pass test

# Feature 2:
tests/test_max_contracts.py  # ← Write test
src/rules/max_contracts.py   # ← Build to pass test

# Result: Always tested, always working
```

### ❌ Mistake 2: Only Unit Tests (Your Previous Problem)

```python
# WRONG - Only mocked unit tests
✅ Unit tests all pass (everything mocked)
❌ Runtime fails (real SDK doesn't work)

# You had this issue:
# - Tests showed "close_position called"
# - But runtime: positions weren't actually closing
# - Because: SDK integration was mocked away
```

```python
# RIGHT - Mix of unit AND integration tests

# Unit tests (fast, isolated)
@pytest.mark.unit
def test_rule_logic():
    # Test JUST the rule logic
    # Mock everything external

# Integration tests (slower, real)
@pytest.mark.integration
async def test_rule_with_sdk():
    # Test rule + SDK working together
    # Only mock the actual trading API
```

### ❌ Mistake 3: Testing Implementation, Not Behavior

```python
# WRONG - Testing how it works internally
def test_rule_calls_specific_method(self):
    """Test that rule calls _calculate_pnl method."""
    rule = DailyLossRule(max_loss=-1000.0)

    # Checking internal implementation detail
    assert hasattr(rule, '_calculate_pnl')
    # This breaks if you refactor!
```

```python
# RIGHT - Testing what it does (behavior)
def test_rule_triggers_at_loss_limit(self):
    """Test that rule triggers when loss limit reached."""
    rule = DailyLossRule(max_loss=-1000.0)

    # Test the BEHAVIOR, not implementation
    event = event_factory(realized_pnl=-1000.0)
    violation = await rule.evaluate(event, engine)

    assert violation is not None  # This is what matters!
    assert violation["action"] == "flatten"
```

### ❌ Mistake 4: Not Running Tests During Development

```python
# WRONG - Writing code for hours, then testing
# 10:00 AM - Start coding
# 11:00 AM - Still coding
# 12:00 PM - Still coding
# 1:00 PM  - Finally run tests
# ❌ 47 test failures
# 😰 "Which change broke it?!"
```

```python
# RIGHT - Testing every 10-15 minutes
# 10:00 AM - Write test + code for Feature A
# 10:15 AM - pytest → ✅ PASS
# 10:30 AM - Write test + code for Feature B
# 10:45 AM - pytest → ✅ PASS
# 11:00 AM - Write test + code for Feature C
# 11:15 AM - pytest → ❌ FAIL (know exactly what broke!)
```

---

## Quick Reference

### TDD Command Sequence (Copy-Paste This)

```bash
# 1. Write test for new feature
vim tests/unit/test_rules/test_new_feature.py

# 2. Run test (should fail)
pytest tests/unit/test_rules/test_new_feature.py -v
# ❌ FAILED (expected - no code yet)

# 3. Write minimal code
vim src/risk_manager/rules/new_feature.py

# 4. Run test again (should pass)
pytest tests/unit/test_rules/test_new_feature.py -v
# ✅ PASSED

# 5. Add more tests for edge cases
vim tests/unit/test_rules/test_new_feature.py

# 6. Run all tests
pytest tests/ -v
# ✅ All pass

# 7. Check coverage
pytest --cov=risk_manager --cov-report=term-missing
# Aim for >80% coverage

# 8. Commit (only if tests pass)
git add .
git commit -m "feat: add new feature with tests"
```

### Test Markers (Add to your pyproject.toml)

```toml
# Already in your pyproject.toml (lines 96-101)
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",           # Fast, isolated
    "integration: Integration tests",  # Slower, real components
    "slow: Slow tests",           # Very slow
    "ai: AI feature tests",       # AI-specific
]
```

**Usage in tests:**

```python
@pytest.mark.unit
def test_fast_unit():
    """Fast unit test."""

@pytest.mark.integration
async def test_with_sdk():
    """Integration test with SDK."""

@pytest.mark.slow
async def test_full_system():
    """Full system integration test."""
```

**Run specific markers:**

```bash
# Only fast unit tests (for rapid development)
pytest -m unit

# Skip slow tests (for quick validation)
pytest -m "not slow"

# Only integration tests (before deployment)
pytest -m integration
```

### File Organization Checklist

- [ ] `tests/unit/test_rules/` - Rule tests (one file per rule)
- [ ] `tests/unit/test_core/` - Core component tests
- [ ] `tests/unit/test_state/` - State management tests
- [ ] `tests/unit/test_sdk/` - SDK wrapper tests
- [ ] `tests/integration/` - Integration tests (CREATE THIS!)
- [ ] `tests/conftest.py` - Shared fixtures

### Coverage Target

```bash
# Check coverage
pytest --cov=risk_manager --cov-report=html

# Open report
open htmlcov/index.html

# Target: 80%+ coverage for critical paths
# - Core rules: 90%+
# - Event system: 85%+
# - State management: 90%+
# - SDK integration: 70%+ (harder to test)
```

---

## Summary: The Golden Rules

1. **Write Test First** - Before any code, write a failing test
2. **Make It Pass** - Write minimal code to make test pass
3. **Refactor** - Clean up code while keeping tests passing
4. **Repeat** - Do this for EVERY feature

5. **Test During Development** - Run tests every 10-15 minutes
6. **Mix Test Types** - Unit tests for logic, integration for flow
7. **Test Behavior** - Not implementation details
8. **Never Commit Broken Tests** - All tests must pass before commit

---

**Remember:** The SDK achieved 84.8% SWE-Bench solve rate through disciplined TDD. Follow their workflow and you'll achieve the same quality in your risk manager.

**Next Steps:**
1. Read `RUNTIME_INTEGRATION_TESTING.md` to learn how to prevent "green tests but broken runtime"
2. Start your next feature with TDD
3. Write tests BEFORE code
4. Run tests frequently
5. Commit only when tests pass

---

*This guide is based on analyzing project-x-py SDK's actual development workflow from `contributing.md`, `testing.md`, and test file patterns. Apply these patterns to build a production-ready risk manager.*
