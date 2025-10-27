# Master Integration Roadmap
## Risk Manager V34 - Complete Implementation Plan

**Generated**: 2025-10-27
**Synthesized From**: 7-Agent Swarm Analysis
**Project Status**: 30% Complete → Path to 100%

---

## 🎯 Executive Summary

This roadmap synthesizes findings from comprehensive analysis of:
- ✅ Source code (22 files, 2,789 lines)
- ✅ Test suite (136 tests, 88 passing)
- ✅ Working proof-of-concept (`test_max_contracts_exact.py`)
- ✅ 13 risk rule specifications
- ✅ Architecture & SDK integration documentation
- ✅ Foundation & testing documentation
- ✅ Cross-referenced gap analysis (54 distinct gaps)

**Key Discovery**: You have a **working event-driven architecture** proven by your test. The path forward is **modularization + expansion**, NOT rebuilding from scratch.

**Timeline to Production**: 12-14 weeks parallelized (26 weeks sequential)

---

## 📊 Current State Assessment

### What's Working ✅

**1. Core Architecture (75% Complete)**
- Event-driven flow: SDK → EventBridge → RiskEngine → Rules → Enforcement
- 8-checkpoint logging system (100% implemented, 100% documented)
- Async/await architecture throughout
- Database persistence layer (SQLite)
- Two complete rules (RULE-001, RULE-002) with 31 comprehensive tests

**2. Working Proof-of-Concept**
- `test_max_contracts_exact.py` (347 lines) proves entire concept works
- Real-time WebSocket events (<100ms latency)
- Position tracking and auto-flattening
- Guard pattern prevents feedback loops
- Correct SDK integration (camelCase fields, realtime callbacks)

**3. SDK Integration**
- EventBridge uses CORRECT pattern (`suite.realtime.add_callback()`)
- TradingIntegration properly wired to SDK
- Enforcement layer complete with Checkpoint 8 logging

**4. Testing Infrastructure**
- Interactive test runner with 20+ menu options
- Auto-save reports to `test_reports/latest.txt`
- Runtime reliability pack (smoke, soak, trace)
- TDD workflow established

### What's Broken ❌

**1. Documentation Errors (CRITICAL)**
- ❌ Docs claim `suite.event_bus.subscribe()` works (IT DOESN'T)
- ❌ Docs use snake_case fields (SDK uses camelCase)
- ❌ `TradingSuite.create()` signature incomplete
- ❌ 14+ references to non-existent `PROJECT_STATUS.md`

**2. State Management Gap (HIGH PRIORITY)**
- Events arrive but don't update `engine.current_positions`
- P&L tracker not wired to position events
- State managers missing (MOD-002, MOD-003, MOD-004)

**3. Test Coverage (BLOCKER)**
- Overall: 18.27% (target: 90%)
- Rules: 0% coverage (except RULE-001/002)
- SDK integration: 0% coverage
- 5 failing tests out of 136

**4. Missing Components**
- 11 of 13 risk rules not implemented
- Quote event integration unvalidated
- Multi-symbol support untested
- Windows Service deployment layer missing

---

## 🚨 Phase 0: Critical Documentation Fixes (Week 1)

**Duration**: 3-5 days
**Priority**: BLOCKING - Must fix before building
**Effort**: Low (documentation only)

### Fix 1: SDK Event Subscription Pattern

**Files to Update**:
- `docs/specifications/unified/sdk-integration.md`
- `docs/specifications/unified/event-handling.md`
- `CLAUDE.md` (if contains examples)

**Wrong**:
```python
# ❌ THIS DOESN'T WORK
suite.event_bus.subscribe(SDKEventType.POSITION_UPDATED, handler)
```

**Correct**:
```python
# ✅ THIS IS THE CORRECT PATTERN
realtime_client = suite.realtime
realtime_client.add_callback("position_update", handler)
realtime_client.add_callback("order_update", handler)
realtime_client.add_callback("trade_update", handler)
```

**Proof**: `src/risk_manager/sdk/event_bridge.py` lines 7-10 explicitly states EventBus doesn't emit position/order/trade events.

### Fix 2: Field Naming Convention

**Files to Update**: All documentation with SDK examples

**Wrong**:
```python
# ❌ SDK doesn't have snake_case fields
position.contract_id
position.average_price
position.unrealized_pnl
order.filled_quantity
```

**Correct**:
```python
# ✅ SDK uses camelCase
position.contractId
position.averagePrice
position.unrealizedPnl
order.fillVolume
```

**Proof**: `test_max_contracts_exact.py` lines 108-124 shows correct camelCase usage.

### Fix 3: TradingSuite.create() Signature

**File**: `docs/specifications/unified/sdk-integration.md`

**Wrong**:
```python
suite = await TradingSuite.create(instruments=["MNQ"])
```

**Correct**:
```python
suite = await TradingSuite.create(
    http_client=px_http,
    realtime_client=px_realtime,
    instruments=["MNQ"]
)
```

**Proof**: `src/risk_manager/integrations/trading.py` lines 38-42

### Fix 4: PROJECT_STATUS.md References

**File**: `CLAUDE.md` (14+ references)

**Options**:
1. Create `docs/current/PROJECT_STATUS.md` with live status tracking
2. OR: Replace all references with `IMPLEMENTATION_ROADMAP.md`

**Recommendation**: Create `PROJECT_STATUS.md` - useful for AI session resumption.

### Validation Checklist

- [ ] Search all docs for `event_bus.subscribe` → Replace with `realtime.add_callback`
- [ ] Search all docs for snake_case SDK fields → Replace with camelCase
- [ ] Update TradingSuite.create() signature with all required parameters
- [ ] Create PROJECT_STATUS.md OR update all references
- [ ] Run grep to verify no incorrect patterns remain

---

## 🧩 The Working Pattern (From test_max_contracts_exact.py)

**Agent 3 dissected your working test and identified these reusable patterns:**

### Pattern 1: Event Handler with Type Checking

**Test (lines 135-158)**:
```python
async def on_position_event(event):
    data = event.data if hasattr(event, 'data') else {}
    if not isinstance(data, dict):
        return

    contract = get_contract_name(data.get('contractId', ''))
    pos_type = data.get('type', 0)  # 1=LONG, 2=SHORT
    size = data.get('size', 0)
    avg_price = data.get('averagePrice', 0)
```

**Maps To**: `src/risk_manager/sdk/event_bridge.py` → `_on_position_updated()`

**Modularization**:
- ✅ Already extracted in EventBridge
- ⚠️ MISSING: State update to `engine.current_positions`

### Pattern 2: Rule Evaluation Logic

**Test (lines 160-162)**:
```python
MAX_CONTRACTS = 2
if abs(size) > MAX_CONTRACTS and size != 0:
    # Violation detected
```

**Maps To**: `src/risk_manager/rules/max_position.py` → `evaluate()`

**Modularization**:
- ✅ Already extracted as MaxPositionRule
- ✅ 31 tests passing
- ✅ Parameterized (max_contracts configurable)

### Pattern 3: Enforcement Guard (Anti-Feedback Loop)

**Test (lines 163-171)**:
```python
global currently_flattening

if currently_flattening:
    print("⏸️ Already flattening - ignoring")
    return

currently_flattening = True  # SET IMMEDIATELY
```

**Maps To**: Either:
1. `src/risk_manager/state/lockout_manager.py` (MOD-002 - not implemented)
2. OR: New `EnforcementGuard` class

**Modularization**:
- ❌ NOT extracted yet
- ⚠️ CRITICAL: Without this, feedback loops will occur
- 📝 Recommendation: Implement as `EnforcementGuard` in enforcement.py

### Pattern 4: Opposite Side Calculation

**Test (lines 192-200)**:
```python
if pos_type == 1:  # LONG position
    side = 1  # SELL to close
    side_name = "SELL"
elif pos_type == 2:  # SHORT position
    side = 0  # BUY to close
    side_name = "BUY"
```

**Maps To**: `src/risk_manager/sdk/enforcement.py` → `_close_position()`

**Modularization**:
- ✅ Already extracted in enforcement.py lines 120-127
- ✅ Correct logic implemented

### Pattern 5: Flatten Execution

**Test (lines 207-211)**:
```python
mnq = suite["MNQ"]
result = await mnq.orders.place_market_order(
    contract_id=contract_id,
    side=side,
    size=abs(size)
)
```

**Maps To**: `src/risk_manager/sdk/enforcement.py` → `_close_position()`

**Modularization**:
- ✅ Already extracted
- ✅ Uses correct SDK API
- ✅ Checkpoint 8 logging included

### Pattern 6: Guard Release with Delay

**Test (lines 222-226)**:
```python
finally:
    await asyncio.sleep(2)  # Wait for position to close
    currently_flattening = False
    print("🔓 Flatten guard released")
```

**Modularization**:
- ❌ NOT extracted
- ⚠️ Need to determine correct delay (2s? event-driven? configurable?)
- 📝 Recommendation: Make configurable in EnforcementGuard

### Summary: What to Extract

| Pattern | Status | Next Action |
|---------|--------|-------------|
| Event Handler | ✅ Extracted | Wire state updates |
| Rule Evaluation | ✅ Extracted | Expand to 11 more rules |
| Enforcement Guard | ❌ Missing | Implement EnforcementGuard |
| Side Calculation | ✅ Extracted | None needed |
| Flatten Execution | ✅ Extracted | None needed |
| Guard Release | ❌ Missing | Add to EnforcementGuard |

---

## 🏗️ Phase 1: Foundation Fixes (Weeks 2-3)

**Duration**: 2 weeks
**Priority**: HIGH - Unblocks all rules
**Dependencies**: Phase 0 complete

### Task 1.1: Fix State Update Gap

**Problem**: Events arrive but `engine.current_positions` not updated (Agent 1 finding)

**Files to Modify**:
- `src/risk_manager/sdk/event_bridge.py` (add state update calls)
- `src/risk_manager/core/engine.py` (ensure state methods exist)

**Implementation**:
```python
# In event_bridge.py → _on_position_updated()
async def _on_position_updated(self, position_data: dict[str, Any]) -> None:
    # Convert to RiskEvent (already done)
    risk_event = RiskEvent(...)

    # NEW: Update engine state
    await self.engine.update_position_state(position_data)

    # Emit event
    await self.engine.handle_event(risk_event)
```

**Tests Needed**:
- `tests/unit/test_event_bridge.py` → Verify state update called
- `tests/integration/test_engine_state.py` → End-to-end state tracking

**Success Criteria**:
- `engine.current_positions` reflects live SDK positions
- `engine.get_total_position()` returns correct values
- Rules can access current state

### Task 1.2: Implement EnforcementGuard

**Purpose**: Prevent feedback loops during enforcement (Pattern 3 + 6 from test)

**New File**: `src/risk_manager/sdk/enforcement_guard.py`

**API Design**:
```python
class EnforcementGuard:
    """Prevents concurrent enforcement feedback loops."""

    def __init__(self, cooldown_seconds: float = 2.0):
        self._active_enforcements: set[str] = set()
        self._cooldown = cooldown_seconds

    async def __aenter__(self, key: str):
        if key in self._active_enforcements:
            raise EnforcementInProgress(f"Already enforcing: {key}")
        self._active_enforcements.add(key)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.sleep(self._cooldown)
        self._active_enforcements.discard(key)
```

**Usage in enforcement.py**:
```python
async def _close_position(self, contract_id: str, ...):
    guard_key = f"close_position:{contract_id}"

    try:
        async with self.enforcement_guard(guard_key):
            # Place market order
            result = await self._place_market_order(...)
    except EnforcementInProgress:
        logger.info(f"⏸️ Already closing {contract_id}, skipping")
        return
```

**Tests Needed**:
- `tests/unit/test_enforcement_guard.py` (15 tests)
  - Test concurrent calls blocked
  - Test cooldown timing
  - Test exception handling
  - Test multiple keys tracked independently

**Success Criteria**:
- No duplicate enforcement actions
- Configurable cooldown period
- Clear logging when enforcement skipped

### Task 1.3: Wire P&L Tracker to Events

**Problem**: PnLTracker exists but not updated from position events (Agent 1 finding)

**Files to Modify**:
- `src/risk_manager/sdk/event_bridge.py` (add P&L tracking)
- `src/risk_manager/core/engine.py` (wire to PnLTracker)

**Implementation**:
```python
# In event_bridge.py → _on_trade_executed()
async def _on_trade_executed(self, trade_data: dict[str, Any]) -> None:
    # Convert to RiskEvent (already done)
    risk_event = RiskEvent(...)

    # NEW: Update P&L tracker
    await self.engine.pnl_tracker.record_trade(
        symbol=trade_data.get('contractId'),
        side=trade_data.get('side'),
        quantity=trade_data.get('size'),
        price=trade_data.get('price'),
        timestamp=datetime.now()
    )

    # Emit event
    await self.engine.handle_event(risk_event)
```

**Tests Needed**:
- `tests/integration/test_pnl_tracking.py` (10 tests)
  - Verify trades update P&L
  - Verify daily P&L calculated correctly
  - Verify P&L persists to database

**Success Criteria**:
- Real-time P&L tracking from SDK events
- Rules can query current P&L
- P&L survives service restart

### Phase 1 Acceptance Criteria

- [ ] `engine.current_positions` updates in real-time
- [ ] `EnforcementGuard` prevents concurrent enforcement
- [ ] P&L tracker receives trade events
- [ ] All 5 failing tests fixed
- [ ] Test coverage: 40%+ (from 18.27%)
- [ ] Smoke test passes (exit code 0)

---

## 🔧 Phase 2: State Manager Infrastructure (Weeks 4-6)

**Duration**: 3 weeks
**Priority**: HIGH - Unblocks 8 rules (62%)
**Dependencies**: Phase 1 complete

### Critical Path Discovery (Agent 4)

**8 of 13 rules blocked by 3 missing state managers:**

```
MOD-003 (TimerManager)
  └─ Blocks: RULE-006, 007, 008, 009, 010, 011, 012, 013

MOD-002 (LockoutManager)
  └─ Blocks: RULE-006, 007, 008, 009, 010, 011, 012

MOD-004 (ResetScheduler)
  └─ Blocks: RULE-003, 004, 005, 013
```

**Implementation Order**: MOD-003 → MOD-002 → MOD-004 (reverse dependency chain)

### Task 2.1: Implement MOD-003 (TimerManager)

**Duration**: 1 week
**Effort**: Medium
**Blocks**: 8 rules

**Specification**: `docs/specifications/unified/architecture/state-management.md`

**API Design**:
```python
class TimerManager:
    """Manages time-based cooldowns and rate limits."""

    async def start_cooldown(self, key: str, duration_seconds: int) -> None:
        """Start a cooldown timer."""

    async def is_in_cooldown(self, key: str) -> bool:
        """Check if cooldown is active."""

    async def get_remaining_time(self, key: str) -> float | None:
        """Get seconds remaining in cooldown."""

    async def cancel_cooldown(self, key: str) -> None:
        """Cancel a cooldown early."""
```

**Storage**: SQLite table
```sql
CREATE TABLE cooldowns (
    key TEXT PRIMARY KEY,
    started_at REAL NOT NULL,
    duration_seconds INTEGER NOT NULL,
    expires_at REAL NOT NULL
);
CREATE INDEX idx_cooldowns_expires ON cooldowns(expires_at);
```

**Tests Needed** (25 tests):
- Unit tests (20): Timer start/check/cancel/expiry
- Integration tests (5): Database persistence, concurrent access

**Success Criteria**:
- Timers persist across service restart
- Expired timers auto-cleaned
- Sub-second precision
- Query performance <1ms

### Task 2.2: Implement MOD-002 (LockoutManager)

**Duration**: 1 week
**Effort**: Medium
**Blocks**: 7 rules

**API Design**:
```python
class LockoutManager:
    """Manages hard lockouts (trading disabled)."""

    async def lock_trading(self, reason: str, until: datetime | None = None) -> None:
        """Lock trading with optional expiry."""

    async def unlock_trading(self, admin_override: bool = False) -> None:
        """Unlock trading (requires admin or auto-expiry)."""

    async def is_locked(self) -> bool:
        """Check if trading is locked."""

    async def get_lockout_info(self) -> dict[str, Any] | None:
        """Get lockout details."""
```

**Storage**: SQLite table + in-memory cache
```sql
CREATE TABLE lockouts (
    id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    locked_at REAL NOT NULL,
    unlocked_at REAL,
    expires_at REAL,
    admin_override BOOLEAN DEFAULT 0
);
```

**Tests Needed** (20 tests):
- Unit tests (15): Lock/unlock/check/expiry
- Integration tests (5): Admin override, persistence

**Success Criteria**:
- Lockouts survive restart
- Admin override logged
- Expiry auto-unlocks
- Check latency <1ms (cached)

### Task 2.3: Implement MOD-004 (ResetScheduler)

**Duration**: 1 week
**Effort**: Medium-High (timezone complexity)
**Blocks**: 4 rules

**API Design**:
```python
class ResetScheduler:
    """Manages daily/weekly P&L resets."""

    async def schedule_daily_reset(self, time_utc: str) -> None:
        """Schedule daily reset (e.g., '00:00:00')."""

    async def schedule_weekly_reset(self, day: int, time_utc: str) -> None:
        """Schedule weekly reset (0=Monday, 6=Sunday)."""

    async def get_next_reset(self) -> datetime:
        """Get next scheduled reset time."""

    async def trigger_reset_now(self, admin_override: bool = False) -> None:
        """Immediate reset (testing/admin)."""
```

**Implementation Notes**:
- Use UTC internally, convert for display
- APScheduler for reliable scheduling
- Idempotent resets (safe to call multiple times)

**Tests Needed** (30 tests):
- Unit tests (20): Schedule parsing, next reset calculation
- Integration tests (10): Reset triggers, timezone handling

**Success Criteria**:
- Resets occur within 1 second of scheduled time
- Timezone conversions correct
- Missed resets caught on restart
- Admin manual reset logged

### Phase 2 Acceptance Criteria

- [ ] MOD-003 (TimerManager) implemented with 25 passing tests
- [ ] MOD-002 (LockoutManager) implemented with 20 passing tests
- [ ] MOD-004 (ResetScheduler) implemented with 30 passing tests
- [ ] All state managers persist to database
- [ ] Test coverage: 55%+ (from 40%)
- [ ] Smoke test passes with all managers initialized
- [ ] 8-checkpoint system shows all managers loaded

---

## 📏 Phase 3: Implement Remaining Rules (Weeks 7-11)

**Duration**: 5 weeks
**Priority**: HIGH - Core product features
**Dependencies**: Phase 2 complete

### Rule Implementation Order (Agent 4 Analysis)

**Week 7: P&L Rules (MOD-004 unblocked)**
- RULE-003: Daily Loss Limit (3 days, 15 tests)
- RULE-004: Trailing Drawdown (3 days, 20 tests)
- RULE-005: Daily Profit Target (2 days, 10 tests)

**Week 8-9: Time-Based Rules (MOD-003 unblocked)**
- RULE-006: Trading Hours (2 days, 15 tests)
- RULE-007: Max Trades Per Day (2 days, 12 tests)
- RULE-008: Trade Cooldown (2 days, 10 tests)
- RULE-009: Position Hold Time (3 days, 15 tests)

**Week 10-11: Behavior Rules (MOD-002 + MOD-003 unblocked)**
- RULE-010: Rapid Fire Detection (3 days, 15 tests)
- RULE-011: Max Consecutive Losses (2 days, 12 tests)
- RULE-012: Revenge Trading Detection (4 days, 20 tests)
- RULE-013: Weekly Loss Limit (2 days, 12 tests)

### Rule Implementation Template

**For Each Rule**:

1. **Read Specification** (`docs/specifications/unified/rules/RULE-XXX.md`)
2. **Write Tests First** (TDD):
   ```bash
   # Create test file
   tests/unit/test_rules/test_<rule_name>.py

   # Write 10-20 tests covering:
   # - Happy path (rule passes)
   # - Violation scenarios
   # - Edge cases
   # - State persistence
   # - Configuration variations
   ```

3. **Implement Rule** (`src/risk_manager/rules/<rule_name>.py`):
   ```python
   from risk_manager.rules.base import RiskRule
   from risk_manager.core.events import RiskEvent, EventType

   class RuleName(RiskRule):
       async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict | None:
           # 1. Check if event type relevant
           # 2. Query required state (positions, P&L, timers, lockouts)
           # 3. Apply rule logic
           # 4. Return violation dict or None
   ```

4. **Wire to Engine** (`config/risk_config.yaml`):
   ```yaml
   rules:
     - name: RuleName
       enabled: true
       parameters:
         param1: value1
   ```

5. **Integration Test**:
   ```bash
   # Verify rule loads from config
   # Verify rule evaluates on correct events
   # Verify enforcement triggered
   ```

6. **Update Checkpoint Logs**:
   ```python
   sdk_logger.info(f"✅ Rule initialized: {rule.__class__.__name__}")
   ```

### Rule-Specific Notes

**RULE-003, 004, 005, 013 (P&L Rules)**:
- Depend on PnLTracker (Phase 1.3)
- Depend on ResetScheduler (Phase 2.3)
- Need accurate trade-by-trade P&L
- Must handle unrealized P&L for open positions

**RULE-006, 007, 008, 009 (Time Rules)**:
- Depend on TimerManager (Phase 2.1)
- Need accurate timezone handling
- RULE-006 needs market hours calendar (futures markets)

**RULE-010, 011, 012 (Behavior Rules)**:
- Depend on TimerManager (Phase 2.1) for detection windows
- Depend on LockoutManager (Phase 2.2) for enforcement
- RULE-012 (Revenge Trading) is most complex:
  - Requires loss detection + rapid trade detection
  - Subjective threshold tuning
  - Recommend conservative defaults

### Phase 3 Acceptance Criteria

- [ ] All 11 remaining rules implemented
- [ ] 156+ new tests (avg 14 per rule)
- [ ] Each rule has integration test
- [ ] All rules load from config
- [ ] Test coverage: 80%+ (from 55%)
- [ ] Smoke test validates all 13 rules initialize
- [ ] All rules documented in config/risk_config.yaml

---

## 🧪 Phase 4: Testing & Quality (Weeks 12-13)

**Duration**: 2 weeks
**Priority**: HIGH - Production readiness
**Dependencies**: Phase 3 complete

### Task 4.1: Integration Test Suite

**Goal**: Test component interactions, not just units

**Create**:
- `tests/integration/test_event_to_enforcement_flow.py` (30 tests)
  - End-to-end: SDK event → Rule violation → Enforcement action
  - Test all 13 rules in realistic scenarios
  - Verify state managers interact correctly

- `tests/integration/test_multi_symbol_support.py` (15 tests)
  - Multiple instruments (MNQ, MES, MCL)
  - Account-wide position limits
  - Symbol-specific rules

- `tests/integration/test_concurrent_events.py` (20 tests)
  - Rapid event streams
  - Race condition detection
  - EnforcementGuard validation

**Total**: 65 integration tests

### Task 4.2: E2E Test Suite

**Goal**: Validate complete workflows from trader perspective

**Create**:
- `tests/e2e/test_realistic_trading_day.py` (8 tests)
  - Scenario: Open position → Hit profit target → Rule locks trading
  - Scenario: Exceed position limit → Auto-flatten → Cooldown
  - Scenario: Daily loss limit → Hard lockout → Admin unlock

- `tests/e2e/test_service_lifecycle.py` (5 tests)
  - Start service → Place trades → Restart → Verify state persists

**Total**: 13 E2E tests

### Task 4.3: Quote Event Integration

**CRITICAL**: Agent 5 flagged this as "completely unvalidated"

**Investigation Tasks**:
1. Verify if quote events use EventBus or realtime callbacks
2. Test QuoteManager with real SDK connection
3. Validate field names (likely camelCase like positions)

**Create**:
- `tests/integration/test_quote_manager.py` (15 tests)
  - Quote event subscription
  - Bid/ask spread tracking
  - Integration with market-data dependent rules

**Estimated Effort**: 3 days

### Task 4.4: Fix All Failing Tests

**Current**: 5 failing tests (Agent 2 finding)

**Process**:
1. Run `python run_tests.py → [0]` (last failed)
2. Read `test_reports/latest.txt`
3. Fix failures one by one
4. Verify no regressions

**Success Criteria**: 0 failing tests

### Task 4.5: Coverage Push to 90%

**Current**: 18.27% → **Target**: 90%+

**Focus Areas** (Agent 2 gap analysis):
- Rules: 0% → 95% (critical path)
- SDK integration: 0% → 85%
- Core engine: 54% → 90%
- Core manager: 22% → 90%

**Strategy**:
```bash
# Generate coverage report with missing lines
python run_tests.py → [7]  # Coverage + HTML

# Open htmlcov/index.html
# Click red lines to see what's untested
# Write tests for missing coverage
```

### Phase 4 Acceptance Criteria

- [ ] 65 integration tests passing
- [ ] 13 E2E tests passing
- [ ] Quote events validated and documented
- [ ] 0 failing tests
- [ ] Overall coverage ≥ 90%
- [ ] Critical path coverage ≥ 95%
- [ ] Smoke test passes in <8s
- [ ] Soak test passes (30-60s runtime)

---

## 🚀 Phase 5: Production Readiness (Week 14+)

**Duration**: 2-4 weeks
**Priority**: MEDIUM - Deployment infrastructure
**Dependencies**: Phase 4 complete

### Task 5.1: Windows Service Layer

**Current**: Service deployment not implemented

**Create**:
- `src/risk_manager/service/windows_service.py`
- Service installer script
- UAC permission handling
- Service lifecycle management

**Reference**: `docs/current/SECURITY_MODEL.md`

**Tests Needed** (15 tests):
- Service install/uninstall
- Start/stop/restart
- Crash recovery
- Permission validation

**Estimated Effort**: 1 week

### Task 5.2: CLI Enhancements

**Current**: Basic CLI exists but incomplete

**Enhancements**:
- Admin CLI (requires elevation)
- Trader CLI (view-only)
- Rich formatting (colors, tables)
- Interactive menu system

**Reference**: Original specs in `docs/PROJECT_DOCS/`

**Tests Needed** (20 tests)

**Estimated Effort**: 1 week

### Task 5.3: Multi-Symbol Support

**Current**: Architecture supports it, but untested

**Validation Tasks**:
1. Test with MNQ + MES simultaneously
2. Verify account-wide position limits
3. Test symbol-specific rules
4. Validate cross-symbol P&L tracking

**Reference**: `docs/current/MULTI_SYMBOL_SUPPORT.md`

**Tests Needed** (15 integration tests)

**Estimated Effort**: 4 days

### Task 5.4: Monitoring & Alerting

**Optional but Recommended**:
- `src/risk_manager/monitoring/metrics.py` (Prometheus exports)
- `src/risk_manager/monitoring/alerts.py` (Email/SMS on lockouts)
- Dashboard for real-time status

**Tests Needed** (10 tests)

**Estimated Effort**: 1 week

### Task 5.5: Documentation Refresh

**After all implementation complete**:

1. Update `IMPLEMENTATION_ROADMAP.md` (mark completed)
2. Create `PROJECT_STATUS.md` with final stats
3. Update `CLAUDE.md` with production info
4. Write deployment guide
5. Write operator manual

**Estimated Effort**: 3 days

### Phase 5 Acceptance Criteria

- [ ] Windows Service installer works
- [ ] Service survives crashes/reboots
- [ ] Admin/Trader CLI both functional
- [ ] Multi-symbol support validated
- [ ] Monitoring dashboards live
- [ ] Documentation complete and accurate
- [ ] Deployment guide tested on clean Windows machine

---

## 📊 Success Metrics

### Code Metrics

| Metric | Current | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Target |
|--------|---------|---------|---------|---------|---------|--------|
| **Source LOC** | 2,789 | 3,200 | 4,500 | 7,000 | 7,200 | 7,500 |
| **Test LOC** | ~2,500 | 3,500 | 5,000 | 7,500 | 9,000 | 9,000 |
| **Test Count** | 136 | 170 | 245 | 400+ | 480+ | 500+ |
| **Test Pass %** | 94.6% | 100% | 100% | 100% | 100% | 100% |
| **Coverage** | 18.27% | 40% | 55% | 80% | 90%+ | 90%+ |

### Feature Completeness

| Component | Current | Phase 1 | Phase 2 | Phase 3 | Phase 5 | Target |
|-----------|---------|---------|---------|---------|---------|--------|
| **Core Architecture** | 75% | 90% | 95% | 95% | 100% | 100% |
| **Risk Rules** | 15% | 15% | 15% | 100% | 100% | 100% |
| **State Managers** | 0% | 33% | 100% | 100% | 100% | 100% |
| **SDK Integration** | 80% | 95% | 95% | 95% | 100% | 100% |
| **Testing Infra** | 90% | 95% | 95% | 100% | 100% | 100% |
| **Documentation** | 70% | 95% | 95% | 95% | 100% | 100% |
| **Deployment** | 0% | 0% | 0% | 0% | 100% | 100% |

### Runtime Validation

**8-Checkpoint System** (must all pass):

```
🚀 Checkpoint 1: Service Start
   Status: ✅ Working

✅ Checkpoint 2: Config Loaded (13 rules)
   Status: ⚠️ Phase 3 - will show all 13 rules

✅ Checkpoint 3: SDK Connected
   Status: ✅ Working

✅ Checkpoint 4: Rules Initialized
   Status: ⚠️ Phase 3 - will show 13 rules

✅ Checkpoint 5: Event Loop Running
   Status: ✅ Working

📨 Checkpoint 6: Event Received (<8s)
   Status: ✅ Working (proven by test)

🔍 Checkpoint 7: Rule Evaluated
   Status: ✅ Working (2 rules tested)

⚠️ Checkpoint 8: Enforcement Triggered
   Status: ✅ Working (flatten tested)
```

**Smoke Test Exit Codes**:
- Phase 1+: Exit code 0 (first event within 8s)
- Phase 2+: All state managers initialized
- Phase 3+: All 13 rules evaluated
- Phase 4+: 90%+ coverage

---

## ⚠️ Risk Mitigation

### Risk 1: Quote Events Don't Work Like Position Events

**Likelihood**: High (Agent 5 warning)
**Impact**: High (blocks 3 rules)

**Mitigation**:
- Investigate in Phase 4.3 (before implementing dependent rules)
- Create spike/prototype for quote subscription
- Document actual pattern in sdk-integration.md

**Contingency**: If quotes unworkable, mark RULE-006/010/012 as "Phase 6"

### Risk 2: State Manager Performance Issues

**Likelihood**: Medium
**Impact**: Medium (latency)

**Mitigation**:
- Load test TimerManager with 1000+ active timers
- Benchmark LockoutManager cache hit rate
- Profile database query performance

**Contingency**: Add Redis cache layer if SQLite too slow

### Risk 3: Feedback Loops Despite EnforcementGuard

**Likelihood**: Low (proven pattern from test)
**Impact**: Critical (infinite order placement)

**Mitigation**:
- Comprehensive testing in Phase 4.1 (concurrent events)
- Add max enforcement counter per minute
- Emergency kill switch in config

**Contingency**: Add rate limiter to TradingIntegration

### Risk 4: Windows Service Deployment Issues

**Likelihood**: Medium (complex UAC/permissions)
**Impact**: High (can't deploy)

**Mitigation**:
- Test on clean Windows VM early (Phase 5.1)
- Document exact installation steps
- Create automated installer

**Contingency**: Deploy as background process if service fails

### Risk 5: Documentation Still Has Errors After Phase 0

**Likelihood**: Medium
**Impact**: Medium (confusion)

**Mitigation**:
- Thorough grep for all incorrect patterns
- Have second person review after Phase 0
- Run example code snippets from docs

**Contingency**: Create "Doc Errata" page until full refresh

---

## 🎯 Recommended Next Steps

**For User (Jake)**:

### This Week (Week 1):
1. **Read this roadmap completely** (30 min)
2. **Review Phase 0 documentation fixes** (1 hour)
3. **Decide**: Fix docs yourself OR deploy doc-fixer agent
4. **Priority decision**: Start Phase 1 immediately OR finish docs first?

### Week 2-3 (Phase 1):
1. **Task 1.1**: Fix state update gap in event_bridge.py
2. **Task 1.2**: Implement EnforcementGuard (extract from test)
3. **Task 1.3**: Wire P&L tracker to events
4. **Goal**: All 5 failing tests fixed, smoke test passes

### Week 4-6 (Phase 2):
1. **Task 2.1**: Implement MOD-003 (TimerManager)
2. **Task 2.2**: Implement MOD-002 (LockoutManager)
3. **Task 2.3**: Implement MOD-004 (ResetScheduler)
4. **Goal**: 8 rules unblocked, 75 new tests passing

### Months 2-3 (Phase 3-4):
1. **Phase 3**: Implement all 11 remaining rules
2. **Phase 4**: Integration/E2E testing, coverage push to 90%

### Month 4 (Phase 5):
1. **Phase 5**: Windows Service, CLI polish, monitoring
2. **Go Live**: Deploy to production

---

## 🛠️ Development Workflow

**Daily Workflow**:

```bash
# Morning: Check status
python run_tests.py → [s]  # Smoke test
python run_tests.py → [2]  # Unit tests

# During development (TDD):
# 1. Write test FIRST
# 2. Run: python run_tests.py → [9]  # Last failed
# 3. Implement feature
# 4. Repeat until green

# Before commit:
python run_tests.py → [1]  # All tests
python run_tests.py → [6]  # Coverage
python run_tests.py → [s]  # Smoke test

# Check results:
cat test_reports/latest.txt
```

**Agent Collaboration**:

When deploying agents for implementation:
1. Agent reads THIS roadmap
2. Agent reads phase-specific tasks
3. Agent reads relevant docs (now corrected)
4. Agent implements TDD (test first)
5. Agent verifies smoke test passes
6. Agent updates PROJECT_STATUS.md

---

## 📁 Key Files Reference

**Roadmap & Planning**:
- ✅ `MASTER_INTEGRATION_ROADMAP.md` (this file)
- ⚠️ `docs/current/PROJECT_STATUS.md` (CREATE THIS - track progress)
- ✅ `IMPLEMENTATION_ROADMAP.md` (original, now supplemented)
- ✅ `CLAUDE.md` (AI entry point - update after Phase 0)

**Foundation Docs** (corrected in Phase 0):
- ✅ `docs/foundation/IMPLEMENTATION_FOUNDATION.md`
- ✅ `docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md`
- ✅ `docs/foundation/TESTING_INTEGRATION.md`

**Specifications** (fix in Phase 0):
- ⚠️ `docs/specifications/unified/sdk-integration.md` (4 critical errors)
- ⚠️ `docs/specifications/unified/event-handling.md` (field names)
- ✅ `docs/specifications/unified/rules/` (13 files - accurate)

**Working Pattern**:
- ✅ `test_max_contracts_exact.py` (THE PROOF - keep as reference)

**Test Reports**:
- ✅ `test_reports/latest.txt` (check after every run)

---

## 🎓 Insights from Analysis

**★ Insight ─────────────────────────────────────**

**Key Discovery #1: Your Test IS the Blueprint**

Your 347-line test (`test_max_contracts_exact.py`) isn't just a proof-of-concept—it's the correct implementation compressed into a single file. The "modularization" task isn't about redesigning the architecture, it's about **extracting patterns** that already work and **expanding** them to handle 11 more rules.

**Key Discovery #2: Documentation vs Reality Gap**

Agent 5 found a critical discrepancy: your documentation describes an SDK EventBus pattern that **doesn't actually work** for position/order/trade events. Your source code uses the **correct** pattern (`suite.realtime.add_callback()`), but the docs would lead someone astray. This is why Phase 0 (doc fixes) is BLOCKING.

**Key Discovery #3: The 3 Missing Pieces**

62% of your rules (8 of 13) are blocked by just 3 state managers. Implementing MOD-003, MOD-002, and MOD-004 is the **highest leverage** work you can do—each one unlocks multiple rules simultaneously.

**Key Discovery #4: 8-Checkpoint System is Gold**

Your runtime validation system with 8 strategic checkpoints is **production-grade** and solves the "tests pass but nothing happens" problem that plagues event-driven systems. This should be the model for other projects.

**Key Discovery #5: You're 30% Done, Not 5%**

The working test + core architecture + 2 complete rules + testing infrastructure represents **substantial** progress. You're not starting from scratch—you're scaling what works.

─────────────────────────────────────────────────

---

## ✅ Phase Completion Checklist

### Phase 0: Documentation Fixes ☐
- [ ] Fix SDK event subscription pattern in all docs
- [ ] Fix field naming (snake_case → camelCase) in all docs
- [ ] Fix TradingSuite.create() signature
- [ ] Create PROJECT_STATUS.md OR fix references
- [ ] Grep verification: no incorrect patterns remain

### Phase 1: Foundation Fixes ☐
- [ ] State updates wired to engine.current_positions
- [ ] EnforcementGuard implemented with tests
- [ ] P&L tracker receives trade events
- [ ] All 5 failing tests fixed
- [ ] Test coverage ≥ 40%
- [ ] Smoke test passes (exit code 0)

### Phase 2: State Managers ☐
- [ ] MOD-003 (TimerManager) implemented with 25 tests
- [ ] MOD-002 (LockoutManager) implemented with 20 tests
- [ ] MOD-004 (ResetScheduler) implemented with 30 tests
- [ ] All state managers persist to database
- [ ] Test coverage ≥ 55%
- [ ] All managers log initialization (Checkpoint 4)

### Phase 3: All Rules Implemented ☐
- [ ] RULE-003, 004, 005, 013 (P&L rules) complete
- [ ] RULE-006, 007, 008, 009 (time rules) complete
- [ ] RULE-010, 011, 012 (behavior rules) complete
- [ ] 156+ new tests passing
- [ ] All rules load from config
- [ ] Test coverage ≥ 80%

### Phase 4: Testing & Quality ☐
- [ ] 65 integration tests passing
- [ ] 13 E2E tests passing
- [ ] Quote events validated
- [ ] 0 failing tests
- [ ] Coverage ≥ 90% (critical paths ≥ 95%)
- [ ] Smoke test <8s, soak test passes

### Phase 5: Production Ready ☐
- [ ] Windows Service installer works
- [ ] Admin/Trader CLI functional
- [ ] Multi-symbol support validated
- [ ] Monitoring dashboards live
- [ ] Documentation complete
- [ ] Deployment guide tested

---

## 📞 Support & Questions

**If Stuck on Phase 0**:
- Grep all docs: `grep -r "event_bus.subscribe" docs/`
- Grep for snake_case SDK fields: `grep -r "contract_id" docs/specifications/`

**If Stuck on Phase 1**:
- Review `test_max_contracts_exact.py` lines 135-226 (working patterns)
- Check `src/risk_manager/sdk/event_bridge.py` (current implementation)

**If Stuck on Phase 2**:
- Read `docs/specifications/unified/architecture/state-management.md`
- Check SQLite schema in `src/risk_manager/state/database.py`

**If Stuck on Phase 3**:
- Read rule spec: `docs/specifications/unified/rules/RULE-XXX.md`
- Reference RULE-001/002 as working examples

**If Stuck on Testing**:
- Read `docs/testing/TESTING_GUIDE.md`
- Check `test_reports/latest.txt` for failure details
- Run smoke test: `python run_tests.py → [s]`

---

## 🏁 Final Notes

**This roadmap synthesizes findings from**:
- Agent 1: Source Code Deep Dive (22 files, 2,789 LOC analyzed)
- Agent 2: Test Suite Analysis (136 tests, coverage gaps)
- Agent 3: Working Test Dissection (6 reusable patterns extracted)
- Agent 4: 13 Rules Validation (dependency analysis, effort estimates)
- Agent 5: SDK Documentation Audit (55/100 accuracy, 4 critical errors)
- Agent 6: Foundation Validation (8-checkpoint system verified)
- Agent 7: Comprehensive Gap Analysis (54 gaps, critical path identified)

**Timeline Summary**:
- **Phase 0**: 1 week (documentation fixes)
- **Phase 1**: 2 weeks (foundation fixes)
- **Phase 2**: 3 weeks (state managers)
- **Phase 3**: 5 weeks (11 rules)
- **Phase 4**: 2 weeks (testing/quality)
- **Phase 5**: 2-4 weeks (production readiness)
- **Total**: 15-17 weeks (parallelizable to 12-14 weeks)

**Current Status**: 30% complete
**Next Milestone**: 50% (end of Phase 2)
**Production Ready**: 100% (end of Phase 5)

**The path is clear. The architecture works. Time to build.** 🚀

---

**Last Updated**: 2025-10-27
**Maintained By**: Master Integration Swarm
**Next Review**: After Phase 0 completion
