# E2E Tests: Monitoring & Lockout Rules

**Created**: 2025-10-28
**Status**: ✅ Complete
**File**: `tests/e2e/test_monitoring_lockout_e2e.py`
**Test Count**: 8 tests (8 collected by pytest)

---

## Overview

Comprehensive end-to-end tests for RULE-010 (Auth Loss Guard) and RULE-013 (Daily Realized Profit Target), covering the complete flow from SDK events through rule evaluation and enforcement.

---

## Test Coverage

### RULE-010: Auth Loss Guard (Connection Monitoring)

**Rule Type**: Alert Only (No Enforcement)
**Purpose**: Monitor SDK connection health and generate alerts

#### Test 1: `test_auth_loss_guard_disconnect_alert`
- **Scenario**: SDK connection lost (network failure)
- **Flow**:
  1. System connected normally
  2. SDK disconnects (simulate network loss)
  3. `SDK_DISCONNECTED` event fired
  4. RULE-010 detects disconnect
  5. Alert generated with WARNING severity
  6. Connection state tracked as disconnected
- **Assertions**:
  - ✅ Alert generated with correct severity and type
  - ✅ Alert action is "alert_only" (no enforcement)
  - ✅ Connection state tracked correctly
  - ✅ Last alert time recorded

#### Test 2: `test_auth_loss_guard_auth_failure_alert`
- **Scenario**: Authentication fails with invalid credentials
- **Flow**:
  1. System attempts to connect
  2. Authentication fails
  3. `AUTH_FAILED` event fired
  4. RULE-010 detects auth failure
  5. Alert generated with ERROR severity
  6. No enforcement actions taken
- **Assertions**:
  - ✅ Alert generated with ERROR severity
  - ✅ Alert contains reason and recommendation
  - ✅ Connection fails gracefully
  - ✅ No enforcement actions (alert only)

#### Test 3: `test_auth_loss_guard_reconnect_clears_alert`
- **Scenario**: Connection lost then restored
- **Flow**:
  1. System connected
  2. SDK disconnects → Alert triggered
  3. SDK reconnects → Alert cleared
  4. Connection status updated to connected
- **Assertions**:
  - ✅ Disconnect generates alert
  - ✅ Reconnect clears alert state
  - ✅ Connection state updated correctly
  - ✅ No false alerts after reconnection

---

### RULE-013: Daily Realized Profit Target

**Rule Type**: Hard Lockout (Category 3)
**Purpose**: Prevent giving back profits after hitting daily target

#### Test 4: `test_daily_profit_target_lockout`
- **Scenario**: Account reaches daily profit target
- **Flow**:
  1. Account realizes $1100 profit (target: $1000)
  2. `POSITION_CLOSED` event with profit
  3. RULE-013 evaluates P&L
  4. Violation detected (P&L >= target)
  5. Hard lockout set until reset time
  6. Account locked from trading
- **Assertions**:
  - ✅ Violation detected when P&L >= target
  - ✅ Positive reinforcement message ("Good job!")
  - ✅ Lockout set with expiry time
  - ✅ Account is locked out
  - ✅ Lockout persists until reset

#### Test 5: `test_daily_profit_prevents_new_trades`
- **Scenario**: Locked account attempts to trade
- **Flow**:
  1. Account locked due to profit target
  2. Attempt to open new position
  3. Rule skips evaluation (account locked)
  4. No additional violations generated
  5. Lockout remains in effect
- **Assertions**:
  - ✅ Locked account skips rule evaluation
  - ✅ No redundant violations generated
  - ✅ Lockout remains in effect
  - ✅ Trading blocked until reset

#### Test 6: `test_daily_profit_reset_clears_lockout`
- **Scenario**: Daily reset clears profit lockout
- **Flow**:
  1. Account locked due to profit target
  2. Reset time arrives
  3. Lockout cleared (expired)
  4. P&L reset to $0
  5. Account can trade again
- **Assertions**:
  - ✅ Expired lockouts cleared automatically
  - ✅ P&L reset to zero
  - ✅ New trades allowed after reset
  - ✅ New P&L tracked correctly

#### Test 7: `test_multiple_accounts_independent_lockouts`
- **Scenario**: Multiple accounts with independent lockouts
- **Flow**:
  1. Account A reaches profit target → Locked
  2. Account B still under target → Not locked
  3. Account A cannot trade
  4. Account B can trade normally
- **Assertions**:
  - ✅ Account A locked correctly
  - ✅ Account B remains unlocked
  - ✅ P&L tracked independently
  - ✅ Lockouts isolated per account

#### Test 8: `test_profit_rule_ignores_half_turn_trades`
- **Scenario**: Opening positions (half-turn trades) ignored
- **Flow**:
  1. Account opens position (profitAndLoss=None)
  2. `POSITION_OPENED` event fired
  3. Rule evaluates but ignores (no realized P&L)
  4. No violation generated
  5. Lockout NOT triggered
- **Assertions**:
  - ✅ Half-turn trades ignored
  - ✅ No false positives on position opens
  - ✅ P&L unchanged
  - ✅ Account not locked

---

## Test Architecture

### Mock Components

#### `MockAccount`
- Simulates SDK account object
- Properties: `id`, `name`, `balance`, `equity`
- Used by `MockTradingSuite`

#### `MockTradingSuite`
- Simulates TopstepX SDK with connection capability
- Features:
  - Connection/disconnection simulation
  - Authentication failure simulation
  - Event bus integration
  - Instrument context mocking
- Modes:
  - Normal connection
  - Auth failure mode (`should_fail_auth=True`)
  - Disconnect mode (`should_disconnect=True`)

### Real Components Used

#### `AuthLossGuardRule`
- Real implementation from `src/risk_manager/rules/auth_loss_guard.py`
- Tests alert generation without mocks

#### `DailyRealizedProfitRule`
- Real implementation from `src/risk_manager/rules/daily_realized_profit.py`
- Tests lockout enforcement with real components

#### `LockoutManager`
- Real implementation with SQLite database
- Tests persistence and expiry

#### `PnLTracker`
- Real implementation with SQLite database
- Tests P&L tracking and reset

#### `Database`
- Real SQLite database (temporary for tests)
- Tests crash recovery capability

---

## Test Patterns

### Follows E2E Best Practices

1. **Complete Flow Testing**
   - Tests full pipeline from event → evaluation → enforcement
   - Uses real components where possible
   - Mocks only SDK (external dependency)

2. **Event-Driven Architecture**
   - Uses `EventBus` for event publishing
   - Tests subscribe/publish mechanism
   - Verifies event data completeness

3. **Async Testing**
   - All tests use `@pytest.mark.asyncio`
   - Proper async/await usage
   - Realistic async delays for event processing

4. **Isolation & Cleanup**
   - Each test uses fresh fixtures
   - Temporary database per test class
   - No state leakage between tests

5. **Clear Documentation**
   - Detailed docstrings with flow diagrams
   - Step-by-step assertions
   - Business logic explained

---

## Running the Tests

### Collect Tests
```bash
pytest tests/e2e/test_monitoring_lockout_e2e.py --collect-only
```

**Output**: 8 tests collected

### Run All Tests
```bash
pytest tests/e2e/test_monitoring_lockout_e2e.py -v
```

### Run RULE-010 Tests Only
```bash
pytest tests/e2e/test_monitoring_lockout_e2e.py::TestAuthLossGuardE2E -v
```

### Run RULE-013 Tests Only
```bash
pytest tests/e2e/test_monitoring_lockout_e2e.py::TestDailyRealizedProfitE2E -v
```

### Run Specific Test
```bash
pytest tests/e2e/test_monitoring_lockout_e2e.py::TestAuthLossGuardE2E::test_auth_loss_guard_disconnect_alert -v
```

### Run with Coverage
```bash
pytest tests/e2e/test_monitoring_lockout_e2e.py --cov=risk_manager.rules --cov-report=html
```

---

## Test Markers

All tests are marked with `@pytest.mark.e2e`:

```bash
# Run all E2E tests
pytest -m e2e

# Run E2E tests excluding monitoring/lockout
pytest -m e2e --ignore=tests/e2e/test_monitoring_lockout_e2e.py
```

---

## Integration with Test Runner

The tests integrate with the interactive test runner (`run_tests.py`):

```bash
python run_tests.py
# Select [4] Run E2E tests only
# → Includes these 8 tests
```

---

## Dependencies

### Required Packages
- `pytest>=8.0.0`
- `pytest-asyncio>=0.21.0`
- `pytest-mock>=3.11.1`
- `loguru>=0.7.0`

### Required Modules
- `risk_manager.core.manager`
- `risk_manager.core.events`
- `risk_manager.core.config`
- `risk_manager.rules.auth_loss_guard`
- `risk_manager.rules.daily_realized_profit`
- `risk_manager.state.lockout_manager`
- `risk_manager.state.pnl_tracker`
- `risk_manager.state.database`

---

## Key Testing Insights

### RULE-010 (Auth Loss Guard)

1. **Alert-Only Rule**
   - No enforcement actions
   - Generates alerts for visibility
   - Tracks connection state per account

2. **Connection State Tracking**
   - Maintains in-memory connection state
   - Records last alert time
   - Clears state on reconnection

3. **Severity Levels**
   - WARNING: Connection lost
   - ERROR: Authentication failed

### RULE-013 (Daily Realized Profit)

1. **Hard Lockout Mechanism**
   - Closes all positions (lock in profits)
   - Cancels all orders
   - Locks account until reset time
   - Prevents all trading activity

2. **P&L Tracking**
   - Only tracks realized P&L (closed trades)
   - Ignores half-turn trades (opening positions)
   - Multi-account support
   - SQLite persistence for crash recovery

3. **Reset Behavior**
   - Lockouts auto-expire at reset time
   - P&L reset to $0
   - Fresh start next trading day

4. **Positive Reinforcement**
   - "Good job!" messaging
   - Celebrates hitting profit targets
   - Encourages disciplined trading

---

## Test Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 8 |
| RULE-010 Tests | 3 |
| RULE-013 Tests | 5 |
| Mock Components | 2 (MockAccount, MockTradingSuite) |
| Real Components | 5 (Rules, LockoutManager, PnLTracker, Database, EventBus) |
| Event Types Tested | 5 (SDK_CONNECTED, SDK_DISCONNECTED, AUTH_FAILED, POSITION_CLOSED, POSITION_OPENED) |
| Lines of Code | ~650 |
| Average Test Length | ~80 lines |

---

## Comparison to Reference Pattern

### Follows `test_authentication_e2e.py` Patterns:

✅ **Mock SDK Structure**
- Similar `MockAccount` and `MockTradingSuite` classes
- Event bus integration
- Connection simulation

✅ **Test Organization**
- Separate test classes per rule
- Numbered test names with descriptive suffixes
- Clear docstrings with flow diagrams

✅ **Event Testing**
- Event tracking with async handlers
- `await asyncio.sleep()` for event processing
- Event data validation

✅ **Assertions**
- Multiple assertions per test
- Clear assertion messages
- Business logic validation

### Enhancements Over Reference:

🚀 **Real Component Integration**
- Uses real `LockoutManager` and `PnLTracker`
- Tests actual database persistence
- Validates crash recovery

🚀 **Advanced Scenarios**
- Multi-account testing
- Lockout expiry testing
- Reset behavior testing

🚀 **Comprehensive Coverage**
- Alert-only rules (RULE-010)
- Hard lockout rules (RULE-013)
- Both monitoring and enforcement

---

## Next Steps

### Immediate
- ✅ Tests created and syntax validated
- ✅ 8 tests collected by pytest
- ⏳ Run tests to verify all pass
- ⏳ Add to CI/CD pipeline

### Future Enhancements
1. **Live SDK Integration**
   - Replace `MockTradingSuite` with real SDK
   - Test against practice account
   - Validate real connection loss scenarios

2. **Performance Testing**
   - Measure alert latency
   - Measure lockout enforcement time
   - Test under load (100+ events/sec)

3. **Additional Scenarios**
   - Multiple rapid disconnects
   - Auth failure recovery
   - Profit target edge cases (exactly at target)

4. **Integration with Other Rules**
   - RULE-010 + RULE-003 (loss limit)
   - RULE-013 + RULE-012 (trade management)
   - Multi-rule violation scenarios

---

## Success Criteria

### All Tests Must:
- ✅ Collect without errors
- ⏳ Run without failures
- ⏳ Complete within 5 seconds each
- ⏳ Leave no database artifacts
- ⏳ Provide clear failure messages

### Coverage Goals:
- ⏳ 100% of RULE-010 code paths
- ⏳ 100% of RULE-013 code paths
- ⏳ All alert generation scenarios
- ⏳ All lockout scenarios

---

## Documentation References

- **E2E Test Plan**: `docs/current/E2E_TEST_PLAN.md`
- **Auth Loss Guard Spec**: `src/risk_manager/rules/auth_loss_guard.py`
- **Daily Profit Spec**: `src/risk_manager/rules/daily_realized_profit.py`
- **Lockout Manager**: `src/risk_manager/state/lockout_manager.py`
- **PnL Tracker**: `src/risk_manager/state/pnl_tracker.py`
- **Reference Pattern**: `tests/e2e/test_authentication_e2e.py`

---

**Last Updated**: 2025-10-28
**Next Review**: After test execution
**Status**: ✅ Ready for Testing
