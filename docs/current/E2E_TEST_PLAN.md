# End-to-End Test Plan - Risk Manager V34

**Created**: 2025-10-27
**Status**: Planning Phase
**Goal**: Test complete pipeline with LIVE TopstepX SDK integration

---

## 🎯 Executive Summary

**Current State**: All unit tests passing (475), integration tests using mocked components
**Target State**: E2E tests using LIVE TopstepX SDK (`project-x-py`) for full pipeline validation
**Priority**: CRITICAL - Must validate before deployment

---

## 📋 Test Coverage Analysis

### ✅ What's Already Tested (Unit + Integration)

| Component | Unit Tests | Integration Tests | E2E Tests | Status |
|-----------|------------|-------------------|-----------|--------|
| Event Bus | ✅ 7 tests | ✅ Included | ⏸️ 1 test | Good |
| Risk Engine | ✅ Included | ✅ 14 tests | ⏸️ 1 test | Good |
| Risk Rules (All 13) | ✅ 380 tests | ✅ 93 tests | ⏸️ 1 test | Good |
| State Management | ✅ 88 tests | ✅ Integrated | ❌ None | **MISSING** |
| SDK Integration | ❌ Mocked | ❌ Mocked | ❌ Mocked | **MISSING** |
| Authentication | ❌ Mocked | ❌ Mocked | ❌ None | **MISSING** |
| Order Execution | ❌ Mocked | ❌ Mocked | ❌ None | **MISSING** |
| Position Management | ❌ Mocked | ❌ Mocked | ❌ None | **MISSING** |
| Timers + Resets | ✅ 22 tests | ✅ Integrated | ❌ None | **MISSING** |

### ❌ What's NOT Tested (Critical Gaps)

1. **LIVE SDK Connection** - No tests with real TopstepX API
2. **Real Authentication Flow** - No tests of actual login/token management
3. **Real Order Execution** - No tests of SDK order placement/cancellation
4. **Real Position Updates** - No tests with live WebSocket position events
5. **Complete Pipeline** - No tests of auth → events → rules → enforcement → timers
6. **Crash Recovery** - No tests of system restart with persisted state
7. **Multi-Symbol Real Trading** - No tests with live multi-symbol positions

---

## 🔍 Test Strategy: Swap Mocks for Live SDK

### Current Architecture (Mocked)

```
┌─────────────────┐
│  Mock SDK       │ ← AsyncMock, fake data
├─────────────────┤
│  EventBridge    │
├─────────────────┤
│  RiskEngine     │
├─────────────────┤
│  Rules          │
├─────────────────┤
│  Enforcement    │ ← AsyncMock.flatten_all()
└─────────────────┘
```

### Target Architecture (Live SDK)

```
┌─────────────────┐
│  TopstepX SDK   │ ← project-x-py (LIVE)
│  (TradingSuite) │
├─────────────────┤
│  EventBridge    │ ← Listen to REAL SDK events
├─────────────────┤
│  RiskEngine     │ ← Evaluate REAL positions
├─────────────────┤
│  Rules          │ ← Check REAL P&L, positions
├─────────────────┤
│  Enforcement    │ ← Call REAL SDK methods
│   suite["MNQ"]  │    (close_all_positions, etc.)
│   .positions    │
│   .close_all()  │
└─────────────────┘
```

### Implementation Steps

1. **Create SDK Test Fixture** (`tests/fixtures/live_sdk.py`)
   - Authenticate with TopstepX practice account
   - Return real `TradingSuite` instance
   - Handle connection lifecycle (connect/disconnect)
   - Use environment variables for credentials

2. **Create E2E Test Base Class** (`tests/e2e/base.py`)
   - Inherit from this for all E2E tests
   - Provides live SDK fixture
   - Provides state cleanup between tests
   - Provides position verification helpers

3. **Swap Mocks in Existing Tests** (Gradual Migration)
   - Start with `test_max_contracts_e2e.py` (already exists)
   - Replace `MockTradingSuite` with real SDK
   - Replace `AsyncMock()` enforcement with real methods
   - Verify tests still pass with live SDK

---

## 📦 E2E Test Suites

### Suite 1: Authentication & Connection (NEW)

**File**: `tests/e2e/test_authentication_e2e.py`
**Duration**: ~30 seconds per test
**SDK Mode**: LIVE (Practice Account)

#### Tests:
1. **test_authentication_success**
   - Given: Valid credentials in .env
   - When: RiskManager starts
   - Then: SDK authenticates successfully
   - Then: SDK_CONNECTED event fired
   - Then: Account info retrieved

2. **test_authentication_failure**
   - Given: Invalid credentials
   - When: RiskManager starts
   - Then: AUTH_FAILED event fired
   - Then: RULE-010 alert triggered
   - Then: System handles gracefully

3. **test_connection_loss_recovery**
   - Given: System connected
   - When: Force disconnect SDK
   - Then: SDK_DISCONNECTED event fired
   - Then: RULE-010 alert triggered
   - When: SDK reconnects
   - Then: SDK_CONNECTED event fired
   - Then: System resumes operation

4. **test_multi_account_authentication**
   - Given: Multiple account credentials
   - When: System starts
   - Then: All accounts authenticate
   - Then: Each account tracked independently

**Expected Runtime**: ~2 minutes total

---

### Suite 2: Event Pipeline (LIVE SDK Events) (NEW)

**File**: `tests/e2e/test_event_pipeline_live_e2e.py`
**Duration**: ~60 seconds per test
**SDK Mode**: LIVE (Practice Account, Real Positions)

#### Tests:
1. **test_position_opened_event_flow**
   - Given: System monitoring live account
   - When: Open position via SDK (1 MNQ contract)
   - Then: SDK fires POSITION_OPENED event
   - Then: EventBridge converts to RiskEvent
   - Then: RiskEngine receives event
   - Then: All rules evaluate
   - Then: No violations (within limits)
   - Cleanup: Close position

2. **test_position_updated_event_flow**
   - Given: Existing position (1 MNQ)
   - When: Add 1 more contract via SDK
   - Then: SDK fires POSITION_UPDATED event
   - Then: RiskEngine updates position tracking
   - Then: Rules evaluate updated position
   - Cleanup: Close all positions

3. **test_order_filled_event_flow**
   - Given: System monitoring
   - When: Place limit order via SDK
   - Then: SDK fires ORDER_PLACED event
   - When: Order fills
   - Then: SDK fires ORDER_FILLED event
   - Then: Position tracking updates
   - Cleanup: Close position

4. **test_pnl_update_event_flow**
   - Given: Open position (1 MNQ long)
   - When: Market price changes (wait 5 seconds)
   - Then: SDK fires PNL_UPDATED events
   - Then: PnL Tracker updates unrealized P&L
   - Then: RULE-004 (Daily Unrealized Loss) evaluates
   - Cleanup: Close position

5. **test_multi_symbol_event_flow**
   - Given: System monitoring
   - When: Open positions in MNQ + ES simultaneously
   - Then: SDK fires events for both symbols
   - Then: RiskEngine tracks both independently
   - Then: RULE-001 (Max Contracts) sums across symbols
   - Cleanup: Close all positions

**Expected Runtime**: ~5 minutes total

---

### Suite 3: Risk Rule Enforcement (LIVE SDK Actions) (NEW)

**File**: `tests/e2e/test_enforcement_live_e2e.py`
**Duration**: ~60 seconds per test
**SDK Mode**: LIVE (Practice Account, Real Orders/Positions)

#### Tests:
1. **test_max_contracts_flatten_enforcement**
   - Given: Max contracts = 2
   - When: Open 3 MNQ contracts via SDK
   - Then: RULE-001 violation detected
   - Then: Enforcement calls `suite["MNQ"].positions.close_all_positions()`
   - Then: SDK actually closes positions
   - Then: Verify positions closed via SDK query
   - Then: ENFORCEMENT_ACTION event published

2. **test_daily_loss_lockout_enforcement**
   - Given: Daily loss limit = $50
   - When: Realize loss of $60 via closed trade
   - Then: RULE-003 violation detected
   - Then: Lockout Manager creates hard lockout
   - Then: Database persists lockout
   - When: Attempt to place order
   - Then: Order rejected before reaching SDK
   - Cleanup: Manual lockout removal

3. **test_cooldown_timer_enforcement**
   - Given: 3 trades in 5 minutes triggers cooldown
   - When: Execute 3 trades rapidly
   - Then: RULE-007 violation detected
   - Then: Timer Manager starts cooldown timer
   - Then: Database persists cooldown
   - When: Attempt to place order during cooldown
   - Then: Order rejected
   - When: Wait for timer to expire
   - Then: Order allowed again

4. **test_stop_loss_auto_placement**
   - Given: RULE-012 (Trade Management) enabled
   - When: Open position without stop-loss
   - Then: RULE-012 auto-places stop-loss order via SDK
   - Then: Verify stop-loss order exists in SDK
   - Then: Verify stop-loss at correct price
   - Cleanup: Cancel stop-loss, close position

5. **test_unrealized_loss_auto_close**
   - Given: RULE-004 unrealized loss limit = $30
   - When: Open position that goes underwater > $30
   - Then: RULE-004 violation detected
   - Then: Enforcement closes position via SDK
   - Then: Verify position closed
   - Then: Loss is now realized
   - Then: PnL Tracker updated

**Expected Runtime**: ~5 minutes total

---

### Suite 4: State Persistence & Crash Recovery (NEW)

**File**: `tests/e2e/test_persistence_e2e.py`
**Duration**: ~45 seconds per test
**SDK Mode**: LIVE (Practice Account)

#### Tests:
1. **test_lockout_persists_across_restart**
   - Given: System running with lockout active
   - When: Trigger hard lockout (daily loss)
   - Then: Lockout stored in database
   - When: Stop RiskManager (simulate crash)
   - When: Restart RiskManager
   - Then: Lockout reloaded from database
   - Then: Account still locked
   - Cleanup: Remove lockout

2. **test_cooldown_timer_persists_across_restart**
   - Given: Active cooldown timer (2 minutes remaining)
   - When: Timer stored in database
   - When: Stop RiskManager
   - When: Restart RiskManager
   - Then: Timer reloaded from database
   - Then: Timer continues countdown
   - Then: Timer expires at correct time

3. **test_pnl_tracking_persists_across_restart**
   - Given: Day with $25 realized P&L
   - When: PnL stored in database
   - When: Stop RiskManager
   - When: Restart RiskManager
   - Then: PnL reloaded from database
   - Then: Daily P&L shows $25
   - Cleanup: Reset P&L

4. **test_daily_reset_clears_persisted_state**
   - Given: Active lockouts, P&L, timers
   - When: Trigger daily reset (5:00 PM ET)
   - Then: Database cleared (except permanent lockouts)
   - Then: PnL reset to $0
   - Then: Cooldowns cleared
   - Then: Reset logged in database

**Expected Runtime**: ~3 minutes total

---

### Suite 5: Multi-Rule Interactions (NEW)

**File**: `tests/e2e/test_multi_rule_interactions_e2e.py`
**Duration**: ~90 seconds per test
**SDK Mode**: LIVE (Practice Account)

#### Tests:
1. **test_position_limit_plus_loss_limit**
   - Given: Max contracts = 2, Daily loss = $50
   - When: Open 2 contracts (at position limit)
   - When: Realize $40 loss (close to loss limit)
   - Then: Both rules tracking independently
   - When: Add 1 more contract (violates RULE-001)
   - Then: Position flattened
   - When: Realized loss now $55 (violates RULE-003)
   - Then: Hard lockout triggered
   - Cleanup: Remove lockout

2. **test_cooldown_plus_session_hours**
   - Given: Session hours 9:30 AM - 4:00 PM ET
   - Given: Cooldown after 3 trades in 5 minutes
   - When: Execute 3 trades rapidly (inside hours)
   - Then: Cooldown triggered (RULE-007)
   - When: Cooldown expires at 4:05 PM (outside hours)
   - Then: RULE-009 (Session Block) prevents trading
   - When: 9:30 AM next day
   - Then: Trading allowed again

3. **test_unrealized_loss_triggers_realized_loss_lockout**
   - Given: Unrealized loss limit = $30
   - Given: Daily realized loss limit = $50
   - When: Open position with $35 unrealized loss
   - Then: RULE-004 closes position (to prevent further loss)
   - Then: Loss becomes realized ($35)
   - Then: Still under daily limit ($50)
   - When: Open another position, lose $20
   - Then: Total realized = $55 (violates RULE-003)
   - Then: Hard lockout triggered

**Expected Runtime**: ~4.5 minutes total

---

### Suite 6: Performance & Latency (NEW)

**File**: `tests/e2e/test_performance_e2e.py`
**Duration**: ~120 seconds per test
**SDK Mode**: LIVE (Practice Account)

#### Tests:
1. **test_event_processing_latency**
   - Given: System monitoring
   - When: SDK fires position update event
   - Measure: Time from event to rule evaluation complete
   - Then: Latency < 50ms (p50)
   - Then: Latency < 100ms (p99)

2. **test_enforcement_execution_latency**
   - Given: Position exceeds limit
   - When: Violation detected
   - Measure: Time from violation to SDK call complete
   - Then: Latency < 200ms (p50)
   - Then: Latency < 500ms (p99)

3. **test_high_frequency_event_handling**
   - Given: System monitoring
   - When: Simulate 100 position updates in 10 seconds
   - Then: All events processed
   - Then: No events dropped
   - Then: System remains responsive

4. **test_concurrent_rule_evaluation**
   - Given: All 13 rules active
   - When: Single position event
   - Then: All rules evaluate concurrently
   - Then: Total evaluation time < 100ms

**Expected Runtime**: ~2 minutes total

---

## 🛠️ Implementation Guide

### Step 1: Create Live SDK Fixture

**File**: `tests/fixtures/live_sdk.py`

```python
"""Live TopstepX SDK fixture for E2E testing."""

import os
import pytest
from project_x_py import TradingSuite
from project_x_py.authentication import ClientCredentials

@pytest.fixture(scope="session")
async def live_sdk_credentials():
    """Load credentials from environment."""
    return {
        "client_id": os.getenv("TOPSTEPX_CLIENT_ID"),
        "client_secret": os.getenv("TOPSTEPX_CLIENT_SECRET"),
        "account_id": os.getenv("TOPSTEPX_ACCOUNT_ID")
    }

@pytest.fixture
async def live_sdk(live_sdk_credentials):
    """Create live SDK connection for testing."""
    creds = ClientCredentials(
        client_id=live_sdk_credentials["client_id"],
        client_secret=live_sdk_credentials["client_secret"]
    )

    suite = TradingSuite(
        credentials=creds,
        account_id=live_sdk_credentials["account_id"],
        environment="practice"  # ⚠️ ALWAYS use practice for testing!
    )

    await suite.connect()

    yield suite

    # Cleanup: Close all positions, cancel all orders
    await cleanup_account(suite)
    await suite.disconnect()

async def cleanup_account(suite):
    """Clean up all positions and orders."""
    # Close all open positions
    for symbol in ["MNQ", "ES", "NQ", "YM"]:
        try:
            positions = await suite[symbol].positions.get_all_positions()
            if positions:
                await suite[symbol].positions.close_all_positions()
        except:
            pass

    # Cancel all open orders
    try:
        orders = await suite.orders.get_all_open_orders()
        for order in orders:
            await suite.orders.cancel_order(order.id)
    except:
        pass
```

### Step 2: Create E2E Test Base Class

**File**: `tests/e2e/base.py`

```python
"""Base class for E2E tests."""

import pytest
from risk_manager.core.manager import RiskManager
from risk_manager.core.config import RiskConfig

class BaseE2ETest:
    """Base class for all E2E tests."""

    @pytest.fixture
    async def risk_manager(self, live_sdk):
        """Create RiskManager with live SDK."""
        config = RiskConfig(
            max_contracts=2,
            max_daily_loss=-50.0,
            enable_all_rules=True
        )

        rm = await RiskManager.create(
            config=config,
            instruments=["MNQ", "ES"]
        )

        # Inject live SDK (replace mock)
        rm.trading_integration.suite = live_sdk

        await rm.start()

        yield rm

        await rm.stop()

    async def wait_for_event(self, event_type, timeout=5.0):
        """Wait for specific event to be published."""
        import asyncio
        event_received = asyncio.Event()
        received_event = None

        async def handler(event):
            nonlocal received_event
            received_event = event
            event_received.set()

        self.risk_manager.event_bus.subscribe(event_type, handler)

        try:
            await asyncio.wait_for(event_received.wait(), timeout=timeout)
            return received_event
        except asyncio.TimeoutError:
            raise TimeoutError(f"Event {event_type} not received within {timeout}s")
```

### Step 3: Update Existing E2E Test

**File**: `tests/e2e/test_max_contracts_e2e.py` (Modify existing)

```python
# Change from:
class TestMaxContractsE2E:
    @pytest.fixture
    def mock_sdk_suite(self):
        return MockTradingSuite()  # ❌ MOCK

# Change to:
from tests.e2e.base import BaseE2ETest

class TestMaxContractsE2E(BaseE2ETest):
    # No mock_sdk_suite fixture needed
    # live_sdk fixture from BaseE2ETest is used automatically
    pass
```

---

## 📊 Test Execution Plan

### Phase 1: Setup (30 minutes)
1. Create `tests/fixtures/live_sdk.py`
2. Create `tests/e2e/base.py`
3. Setup `.env` with practice account credentials
4. Verify SDK connection works

### Phase 2: Authentication Suite (1 hour)
1. Implement `test_authentication_e2e.py` (4 tests)
2. Run tests, verify all pass
3. Fix any SDK integration issues

### Phase 3: Event Pipeline Suite (2 hours)
1. Implement `test_event_pipeline_live_e2e.py` (5 tests)
2. Swap mocks in existing integration tests
3. Verify live SDK events flow correctly

### Phase 4: Enforcement Suite (2 hours)
1. Implement `test_enforcement_live_e2e.py` (5 tests)
2. Verify SDK enforcement actions work
3. Test position closing, order rejection, etc.

### Phase 5: Persistence Suite (1.5 hours)
1. Implement `test_persistence_e2e.py` (4 tests)
2. Test crash recovery scenarios
3. Verify database state persistence

### Phase 6: Multi-Rule Suite (1.5 hours)
1. Implement `test_multi_rule_interactions_e2e.py` (3 tests)
2. Test complex rule interactions
3. Verify correct priority and sequencing

### Phase 7: Performance Suite (1 hour)
1. Implement `test_performance_e2e.py` (4 tests)
2. Measure latencies
3. Document performance characteristics

**Total Estimated Time**: 9-10 hours

---

## ✅ Success Criteria

### Must Pass Before Deployment:

1. **All E2E Tests Passing** (25 tests total)
   - Authentication: 4/4 ✅
   - Event Pipeline: 5/5 ✅
   - Enforcement: 5/5 ✅
   - Persistence: 4/4 ✅
   - Multi-Rule: 3/3 ✅
   - Performance: 4/4 ✅

2. **Performance Metrics Met**
   - Event processing: < 50ms (p50)
   - Enforcement execution: < 200ms (p50)
   - No dropped events under load

3. **Crash Recovery Validated**
   - Lockouts persist across restart
   - Timers resume correctly
   - P&L tracking maintained

4. **Live SDK Integration Verified**
   - Real authentication works
   - Real position updates received
   - Real enforcement actions execute
   - Real order placement/cancellation works

---

## 🚨 Risk Mitigation

### Practice Account Only
- ⚠️ **NEVER run E2E tests against live production accounts**
- ✅ Always use `environment="practice"` in SDK connection
- ✅ Verify account is practice before each test run
- ✅ Add safety checks in fixtures

### Position Cleanup
- ✅ Always close all positions after each test
- ✅ Cancel all open orders
- ✅ Use fixture teardown for cleanup
- ✅ Manual verification after test suite

### Rate Limiting
- ⚠️ TopstepX API has rate limits
- ✅ Add delays between tests if needed
- ✅ Use `pytest-xdist` for parallel execution (carefully)
- ✅ Monitor for 429 errors

### Test Data Isolation
- ✅ Use unique test identifiers
- ✅ Don't interfere with other test runs
- ✅ Clean database between test suites

---

## 📝 Next Steps

1. **Create live SDK fixture** (`tests/fixtures/live_sdk.py`)
2. **Create E2E base class** (`tests/e2e/base.py`)
3. **Implement Authentication Suite** (4 tests) ← START HERE
4. **Verify one test passes end-to-end**
5. **Continue with remaining suites**
6. **Update PROJECT_STATUS.md with E2E progress**

---

**Last Updated**: 2025-10-27
**Next Update**: After Authentication Suite complete
