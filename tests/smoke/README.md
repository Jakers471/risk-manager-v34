# Smoke Tests

**Purpose**: Validate runtime wiring for risk rules

## What Are Smoke Tests?

Smoke tests are NOT about testing logic correctness (unit tests do that). They prove that:

1. ✅ **Events reach the rule** - The event pipeline works
2. ✅ **Manager calls the rule** - Integration is wired correctly
3. ✅ **Violation triggers enforcement** - Actions execute
4. ✅ **All within acceptable time** - Performance requirement met (<10s)

## Why Smoke Tests?

**Problem**: Tests can pass but runtime can be broken
- Unit tests: Test logic in isolation (mocked dependencies)
- Integration tests: Test components together (but not complete flow)
- Smoke tests: Test the ACTUAL runtime wiring

**Example**:
```python
# Unit test passes ✅
def test_rule_logic():
    rule = MaxPositionRule(max_contracts=2)
    violation = rule.evaluate(...)
    assert violation is not None  # Logic works!

# But runtime fails ❌
# - Event never reaches rule
# - Engine doesn't call rule.evaluate()
# - Enforcement never triggers
# - Tests green, system broken!

# Smoke test catches this ✅
async def test_rule_fires_in_runtime():
    # Setup complete system
    engine = RiskEngine(...)
    engine.add_rule(rule)

    # Inject event
    await engine.evaluate_rules(event)

    # Prove it fired
    assert violation_occurred  # Runtime works!
```

## Current Tests

### Position-Based Rules (4 tests)

File: `test_position_rules_smoke.py`

1. **RULE-001**: Max Contracts (account-wide)
2. **RULE-002**: Max Contracts Per Instrument
3. **RULE-004**: Daily Unrealized Loss (stop loss)
4. **RULE-005**: Max Unrealized Profit (take profit)
5. **BONUS**: Multi-rule test (all 4 together)

**Status**: ✅ All passing
**Performance**: All <1s (requirement: <10s)

## Running Smoke Tests

### Run All Smoke Tests
```bash
pytest tests/smoke/ -v
```

### Run Specific Test File
```bash
pytest tests/smoke/test_position_rules_smoke.py -v
```

### Run With Timing
```bash
pytest tests/smoke/ -v --durations=0
```

### Run Only Smoke Tests (marker)
```bash
pytest -m smoke -v
```

## Test Structure

Each smoke test follows this pattern:

```python
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_rule_XXX_fires():
    """
    Smoke test: Rule fires in runtime.

    PROVES:
    - Event reaches rule
    - Rule evaluates
    - Violation detected
    - Enforcement triggered
    - Complete flow <10s
    """
    # 1. Setup engine with rule
    engine = RiskEngine(...)
    rule = RuleClass(...)
    engine.add_rule(rule)

    # 2. Track events
    violations = []
    enforcements = []

    event_bus.subscribe(EventType.RULE_VIOLATED, track_violation)
    event_bus.subscribe(EventType.ENFORCEMENT_ACTION, track_enforcement)

    # 3. Start engine
    await engine.start()

    # 4. Simulate state (positions, prices)
    engine.current_positions = {...}
    engine.market_prices = {...}

    # 5. Inject trigger event
    event = RiskEvent(...)
    await engine.evaluate_rules(event)

    # 6. Wait for violation
    while len(violations) == 0:
        if timeout:
            pytest.fail("TIMEOUT: Rule didn't fire")
        await asyncio.sleep(0.1)

    # 7. Wait for enforcement
    while len(enforcements) == 0:
        if timeout:
            pytest.fail("TIMEOUT: Enforcement didn't trigger")
        await asyncio.sleep(0.1)

    # 8. Verify violation
    assert violation.event_type == EventType.RULE_VIOLATED
    assert "RuleName" in violation.data["rule"]

    # 9. Verify enforcement
    assert enforcement.data["action"] == "expected_action"

    # 10. Check timing
    total_time = time.time() - start_time
    assert total_time < 10.0

    # 11. Cleanup
    await engine.stop()

    # SUCCESS!
    print(f"[OK] RULE-XXX fired in {total_time:.2f}s")
```

## Exit Codes

Smoke tests use exit codes to indicate status:

- **0** = Success (rule fired correctly)
- **1** = Exception/error occurred
- **2** = Timeout (rule didn't fire within time limit)

## Performance Requirements

All smoke tests must complete within **10 seconds**.

Current performance:
- RULE-001: 0.00s ✅ (instant)
- RULE-002: 0.20s ✅
- RULE-004: 0.00s ✅ (instant)
- RULE-005: 0.01s ✅
- Multi-rule: 0.22s ✅

**Average**: 0.09s per test (90% faster than requirement!)

## What Smoke Tests DON'T Test

- ❌ Rule logic correctness (unit tests do this)
- ❌ Edge cases (unit tests do this)
- ❌ Error handling (integration tests do this)
- ❌ Real SDK integration (E2E tests do this)

## What Smoke Tests DO Test

- ✅ Event flow (engine → rule)
- ✅ Rule evaluation (rule.evaluate called)
- ✅ Violation detection (rule returns violation)
- ✅ Event publishing (RULE_VIOLATED, ENFORCEMENT_ACTION)
- ✅ Enforcement triggering (action executed)
- ✅ Performance (timing <10s)

## Adding New Smoke Tests

### For New Rules

1. Create test method in appropriate file
2. Follow the standard pattern (see above)
3. Use `@pytest.mark.smoke` decorator
4. Test ONE complete flow (happy path)
5. Measure timing
6. Verify all 3 events:
   - Input event (POSITION_UPDATED, ORDER_FILLED, etc.)
   - RULE_VIOLATED event
   - ENFORCEMENT_ACTION event

### Example Template

```python
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_rule_XXX_fires(self, event_bus, mock_trading_integration):
    """Smoke test: Rule XXX fires in runtime."""
    # 1. Setup
    config = RiskConfig(...)
    engine = RiskEngine(config, event_bus, mock_trading_integration)
    rule = RuleClass(...)
    engine.add_rule(rule)

    # 2. Track events
    violations = []
    enforcements = []

    async def track_violation(event):
        violations.append(event)

    async def track_enforcement(event):
        enforcements.append(event)

    event_bus.subscribe(EventType.RULE_VIOLATED, track_violation)
    event_bus.subscribe(EventType.ENFORCEMENT_ACTION, track_enforcement)

    # 3. Start & trigger
    await engine.start()

    # Setup violating state
    engine.current_positions = {...}

    # Inject event
    start_time = time.time()
    event = RiskEvent(...)
    await engine.evaluate_rules(event)

    # 4. Wait & verify
    timeout = 10.0
    while len(violations) == 0:
        if time.time() - start_time > timeout:
            pytest.fail("TIMEOUT: Rule didn't fire")
        await asyncio.sleep(0.1)

    while len(enforcements) == 0:
        if time.time() - start_time > timeout:
            pytest.fail("TIMEOUT: Enforcement didn't trigger")
        await asyncio.sleep(0.1)

    # 5. Assert
    assert len(violations) >= 1
    assert len(enforcements) >= 1
    total_time = time.time() - start_time
    assert total_time < 10.0

    # 6. Cleanup
    await engine.stop()

    print(f"[OK] RULE-XXX fired in {total_time:.2f}s")
```

## Smoke Test Categories

### Category 1: Position-Based Rules ✅ DONE
- RULE-001: Max Contracts
- RULE-002: Max Contracts Per Instrument
- RULE-004: Daily Unrealized Loss
- RULE-005: Max Unrealized Profit

### Category 2: P&L-Based Rules (TODO)
- RULE-003: Daily Realized Loss
- RULE-007: Cooldown After Loss

### Category 3: Trade-Based Rules (TODO)
- RULE-006: Trade Frequency Limit
- RULE-008: No Stop-Loss Grace
- RULE-012: Trade Management

### Category 4: Restriction Rules (TODO)
- RULE-009: Session Block Outside Hours
- RULE-010: Auth Loss Guard
- RULE-011: Symbol Blocks

## Integration with CI/CD

Smoke tests should run:
1. After unit tests pass
2. Before integration tests
3. Before deployment
4. As part of "gate" test suite

```bash
# Gate test: Unit + Smoke + Integration
pytest tests/unit/ tests/smoke/ tests/integration/ -v
```

## Best Practices

1. **Keep it simple** - One happy path per rule
2. **Measure timing** - Always track and assert <10s
3. **Mock SDK** - Use AsyncMock for trading_integration
4. **Real components** - Use real EventBus, RiskEngine
5. **Clear assertions** - Verify exact event types and data
6. **Print success** - Show timing on success
7. **Fail fast** - Use timeout to detect broken wiring

## Troubleshooting

### Test Times Out
- Check if event reaches engine (add logging)
- Check if rule.evaluate() is called (add logging)
- Check if violation is returned (print result)
- Check if event bus publishes (add subscriber)

### Test Fails Immediately
- Check rule configuration (correct limits?)
- Check event data (correct format?)
- Check engine state (positions, prices set?)

### Test Passes But Too Slow
- Check async waits (too long?)
- Check timeout value (too generous?)
- Optimize event processing

## Results

See `SMOKE_TEST_RESULTS.md` for detailed results from latest run.

---

**Last Updated**: 2025-10-28
**Coverage**: 4/12 rules (33%)
**Status**: All passing ✅
