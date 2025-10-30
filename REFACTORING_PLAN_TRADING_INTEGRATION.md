# Trading Integration Refactoring Plan

**Goal**: Break `src/risk_manager/integrations/trading.py` (2,169 lines) into 6 focused modules while maintaining 100% functional equivalence.

**Critical Constraint**: `run_dev.py` must work EXACTLY the same before and after.

---

## 📋 Current State

**File**: `src/risk_manager/integrations/trading.py`
- **Size**: 2,169 lines
- **Class**: `TradingIntegration` (single monolithic class)
- **Entry Point**: `run_dev.py` → imports `TradingIntegration`

**What It Does**:
1. Stop loss/take profit caching
2. SDK lifecycle (connect/disconnect)
3. Event routing (14 SDK events → RiskEvent)
4. P&L calculation (realized + unrealized)
5. Semantic analysis (order intent detection)
6. Deduplication (3x event suppression)
7. Order polling (background task)
8. Market data handling (quotes, prices)

---

## 🎯 Target State

**New Directory Structure**:
```
src/risk_manager/integrations/
├── trading.py                      # 300 lines - Facade (public API)
├── sdk/                            # New subdirectory
│   ├── __init__.py
│   ├── connection_manager.py      # 200 lines - Lifecycle
│   ├── event_router.py            # 500 lines - Event handlers
│   ├── protective_orders.py       # 400 lines - Stop/TP cache
│   ├── market_data.py             # 300 lines - Quotes, polling
│   ├── order_polling.py           # 200 lines - Background polling
│   └── pnl_tracker.py             # 300 lines - Position tracking
└── ...existing files...
```

**Key Design Decision: Facade Pattern**

`TradingIntegration` stays as the **public API** (so `run_dev.py` doesn't change!), but internally delegates to specialized modules:

```python
# trading.py (NEW - 300 lines)
class TradingIntegration:
    """
    Public API for trading integration.

    Delegates to specialized modules internally.
    """

    def __init__(self, instruments, config, event_bus):
        # Create internal modules
        self._connection = SDKConnectionManager(instruments, config)
        self._protective_orders = ProtectiveOrderCache()
        self._market_data = MarketDataHandler()
        self._order_polling = OrderPollingService()
        self._pnl_tracker = PnLTracker()
        self._event_router = EventRouter(event_bus, self._protective_orders, self._pnl_tracker)

    async def connect(self):
        """Public API - unchanged signature"""
        await self._connection.connect()

    async def get_stop_loss_for_position(self, contract_id, ...):
        """Public API - unchanged signature"""
        return await self._protective_orders.get_stop_loss(contract_id, ...)

    # ... all other public methods delegate to internal modules
```

**Why This Works**:
- ✅ `run_dev.py` doesn't need ANY changes
- ✅ All existing code using `TradingIntegration` continues to work
- ✅ We can refactor incrementally without breaking anything
- ✅ Public API stays stable, internal implementation changes

---

## 📦 New Module Breakdown

### 1. `sdk/connection_manager.py` (~200 lines)

**Responsibility**: SDK lifecycle management

**Extracted Code**:
- `connect()` (lines 537-592)
- `disconnect()` (lines 593-629)
- HTTP API auth
- SignalR WebSocket setup
- TradingSuite creation

**Public API**:
```python
class SDKConnectionManager:
    async def connect(self) -> tuple[ProjectX, ProjectXRealtimeClient, TradingSuite]
    async def disconnect(self)
    @property
    def is_connected(self) -> bool
    @property
    def suite(self) -> TradingSuite
    @property
    def client(self) -> ProjectX
    @property
    def realtime(self) -> ProjectXRealtimeClient
```

---

### 2. `sdk/protective_orders.py` (~400 lines)

**Responsibility**: Stop loss and take profit detection/caching

**Extracted Code**:
- `get_stop_loss_for_position()` (lines 192-222)
- `get_take_profit_for_position()` (lines 223-256)
- `get_all_active_stop_losses()` (lines 257-264)
- `get_all_active_take_profits()` (lines 266-273)
- `_query_sdk_for_stop_loss()` (lines 275-429)
- `_determine_order_intent()` (lines 473-536)
- `_is_stop_loss()` (lines 1569-1580)
- `_is_take_profit()` (lines 1582-1600)
- `_active_stop_losses` cache logic
- `_active_take_profits` cache logic

**Public API**:
```python
class ProtectiveOrderCache:
    async def get_stop_loss(self, contract_id: str, ...) -> dict | None
    async def get_take_profit(self, contract_id: str, ...) -> dict | None
    def get_all_stop_losses(self) -> dict
    def get_all_take_profits(self) -> dict
    def invalidate_cache(self, contract_id: str)
    def update_from_event(self, order: OrderData)  # Called on ORDER_PLACED
```

---

### 3. `sdk/market_data.py` (~300 lines)

**Responsibility**: Market data handling and price polling

**Extracted Code**:
- `_on_quote_update()` (lines 1841-1945)
- `_on_data_update()` (lines 1947-1963)
- `_on_trade_tick()` (lines 1965-1987)
- `_on_new_bar()` (lines 1989-2026)
- `_update_pnl_status_bar()` (lines 2066-2126)
- Price polling logic (inside status bar task)

**Public API**:
```python
class MarketDataHandler:
    async def handle_quote_update(self, event: Any)
    async def handle_data_update(self, event: Any)
    async def handle_trade_tick(self, event: Any)
    async def handle_new_bar(self, event: Any)
    async def start_status_bar(self)
    async def stop_status_bar(self)
    def get_latest_price(self, symbol: str) -> float | None
```

---

### 4. `sdk/order_polling.py` (~200 lines)

**Responsibility**: Background order polling (catches protective stops that don't emit events)

**Extracted Code**:
- `_poll_orders()` (lines 760-842)
- `_known_orders` tracking
- Order discovery logic

**Public API**:
```python
class OrderPollingService:
    async def start_polling(self)
    async def stop_polling(self)
    def mark_order_seen(self, order_id: int)
```

---

### 5. `sdk/pnl_tracker.py` (~300 lines)

**Responsibility**: Position tracking and P&L calculation

**Extracted Code**:
- `_open_positions` tracking (lines 1376-1405)
- Realized P&L calculation (lines 1314-1374)
- `get_total_unrealized_pnl()` (lines 2127-2137)
- `get_position_unrealized_pnl()` (lines 2139-2152)
- `get_open_positions()` (lines 2154-2161)
- UnrealizedPnLCalculator integration

**Public API**:
```python
class PnLTracker:
    def track_position_opened(self, contract_id: str, price: float, size: int, symbol: str)
    def track_position_closed(self, contract_id: str, exit_price: float) -> float | None
    def get_unrealized_pnl(self, contract_id: str) -> float | None
    def get_total_unrealized_pnl(self) -> float
    def get_open_positions(self) -> dict
```

---

### 6. `sdk/event_router.py` (~500 lines)

**Responsibility**: Route SDK events to risk system

**Extracted Code**:
- `start()` - event handler registration (lines 631-758)
- `_on_order_placed()` (lines 848-921)
- `_on_order_filled()` (lines 923-1006)
- `_on_order_partial_fill()` (lines 1008-1033)
- `_on_order_cancelled()` (lines 1035-1072)
- `_on_order_rejected()` (lines 1074-1097)
- `_on_order_modified()` (lines 1099-1145)
- `_on_order_expired()` (lines 1147-1170)
- `_on_position_opened/closed/updated()` (lines 1178-1191)
- `_handle_position_event()` (lines 1193-1484)
- Deduplication logic (lines 131-163)
- Recent fills tracking (lines 165-190)

**Public API**:
```python
class EventRouter:
    def __init__(self, event_bus: EventBus, protective_cache: ProtectiveOrderCache, pnl_tracker: PnLTracker)
    async def register_handlers(self, suite: TradingSuite)
    async def handle_order_placed(self, event)
    async def handle_order_filled(self, event)
    # ... all event handlers
```

---

### 7. `trading.py` (NEW - ~300 lines)

**Responsibility**: Facade / Public API

**Contains**:
- Public methods that delegate to internal modules
- Initialization that wires modules together
- Helper methods used by multiple modules:
  - `_extract_symbol_from_contract()` (lines 431-471)
  - `_get_side_name()` (lines 1486-1488)
  - `_get_position_type_name()` (lines 1490-1497)
  - `_get_order_placement_display()` (lines 1499-1527)
  - `_get_order_type_display()` (lines 1529-1558)
  - `_get_order_emoji()` (lines 1560-1567)
  - `flatten_position()` (lines 2028-2057)
  - `flatten_all()` (lines 2059-2064)
  - `get_stats()` (lines 2163-2169)

**Structure**:
```python
class TradingIntegration:
    """
    Public API for trading integration.

    This is a facade that delegates to specialized modules.
    Maintains backward compatibility with existing code.
    """

    def __init__(self, instruments, config, event_bus):
        # Initialize internal modules
        self._connection_manager = SDKConnectionManager(...)
        self._protective_orders = ProtectiveOrderCache(...)
        self._market_data = MarketDataHandler(...)
        self._order_polling = OrderPollingService(...)
        self._pnl_tracker = PnLTracker(...)
        self._event_router = EventRouter(...)

        # Expose suite/client for backward compatibility
        self.suite = None
        self.client = None
        self.realtime = None

    # Public API methods (unchanged signatures)
    async def connect(self): ...
    async def disconnect(self): ...
    async def start(self): ...
    async def get_stop_loss_for_position(...): ...
    async def get_take_profit_for_position(...): ...
    # ... etc
```

---

## 🧪 Testing Strategy (CRITICAL!)

### Phase 1: Capture Current Behavior

**BEFORE any refactoring**, write comprehensive integration tests:

```python
# tests/integration/test_trading_integration_behavior.py

class TestTradingIntegrationBehavior:
    """
    Capture current behavior BEFORE refactoring.

    These tests validate that refactoring doesn't change functionality.
    """

    async def test_stop_loss_caching_workflow(self):
        """Test complete stop loss detection workflow"""
        # 1. Position opens
        # 2. Stop loss order placed
        # 3. get_stop_loss_for_position() returns cached data
        # 4. Order fills
        # 5. Cache cleared
        pass

    async def test_event_routing_preserves_data(self):
        """Test that SDK events → RiskEvents with correct data"""
        # Mock SDK events, verify RiskEvent data matches
        pass

    async def test_pnl_calculation_accuracy(self):
        """Test realized and unrealized P&L calculations"""
        # Open position, track entry
        # Update quotes
        # Close position
        # Verify P&L matches expected
        pass

    async def test_deduplication_prevents_3x_events(self):
        """Test that 3 identical events → 1 RiskEvent"""
        pass

    async def test_order_polling_discovers_orders(self):
        """Test background polling finds orders"""
        pass

    async def test_semantic_analysis_detects_intent(self):
        """Test order intent detection (stop loss vs take profit)"""
        pass

    async def test_public_api_signatures(self):
        """Test all public methods exist with correct signatures"""
        # This ensures facade maintains compatibility
        integration = TradingIntegration(...)
        assert hasattr(integration, 'connect')
        assert hasattr(integration, 'get_stop_loss_for_position')
        # ... etc
        pass
```

**Validation Script**:
```python
# tests/validate_refactoring.py

"""
Run this script BEFORE and AFTER refactoring.
Output must be IDENTICAL.
"""

async def main():
    # Create TradingIntegration
    # Run through typical workflow
    # Print deterministic output (event sequence, P&L values, etc.)
    # Compare output before/after refactoring
    pass
```

---

### Phase 2: Incremental Refactoring with Tests

**After each module extraction**:

1. Run unit tests: `pytest tests/unit/test_trading_integration*.py`
2. Run integration tests: `pytest tests/integration/test_trading_integration*.py`
3. Run validation script: `python tests/validate_refactoring.py`
4. Run `run_dev.py` manually and verify behavior
5. **Only proceed if all pass!**

---

## 🔄 Refactoring Workflow

### Option 1: Single Agent (Recommended ✅)

**Pros**:
- Maintains context across entire refactor
- Understands dependencies between modules
- Can backtrack if something breaks
- Coherent design decisions

**Cons**:
- Takes longer (sequential)
- More tokens used in single session

**Process**:
1. Agent writes behavior tests FIRST
2. Agent extracts modules ONE AT A TIME
3. Agent validates after EACH module
4. Agent maintains facade pattern throughout

**Estimated Time**: 4-6 hours of agent work

---

### Option 2: Multiple Agents (Parallel)

**Pros**:
- Faster (parallel work)
- Each agent specialized on one module

**Cons**:
- ⚠️ **High risk of integration issues**
- Agents may make incompatible design decisions
- Need careful coordination
- More human oversight required

**Process** (if you choose this):
1. **Agent 0** (Coordinator): Writes behavior tests, creates module structure
2. **Agent 1**: Extracts `ProtectiveOrderCache`
3. **Agent 2**: Extracts `MarketDataHandler`
4. **Agent 3**: Extracts `EventRouter`
5. **Agent 4**: Extracts `PnLTracker`
6. **Agent 5**: Extracts `SDKConnectionManager`
7. **Agent 0** (Coordinator): Wires everything together in facade, validates

**Estimated Time**: 2-3 hours of wall time, but higher failure risk

---

## 📝 Refactoring Steps (Single Agent Recommended)

### Step 1: Write Behavior Tests (1 hour)

**Goal**: Capture current behavior in tests

**Tasks**:
- Create `tests/integration/test_trading_integration_behavior.py`
- Write 10-15 comprehensive integration tests
- Write `tests/validate_refactoring.py` script
- Run tests to establish baseline (all should pass)
- Save test output as "golden snapshot"

**Success Criteria**:
- ✅ All behavior tests pass
- ✅ Validation script produces deterministic output
- ✅ `run_dev.py` works normally

---

### Step 2: Create Module Structure (30 min)

**Goal**: Create new files with placeholder classes

**Tasks**:
- Create `src/risk_manager/integrations/sdk/` directory
- Create `__init__.py`
- Create 6 module files with empty classes
- Import new modules in `trading.py` (but don't use yet)
- Run tests (should still pass - nothing changed yet)

**Success Criteria**:
- ✅ New files exist
- ✅ Imports work (no import errors)
- ✅ All existing tests still pass

---

### Step 3: Extract ProtectiveOrderCache (1 hour)

**Goal**: Move stop loss/take profit logic to new module

**Tasks**:
- Implement `ProtectiveOrderCache` class in `sdk/protective_orders.py`
- Copy all stop loss/take profit methods
- Write unit tests for `ProtectiveOrderCache`
- Update `TradingIntegration` to use `ProtectiveOrderCache`
- Run all tests

**Success Criteria**:
- ✅ Unit tests pass for `ProtectiveOrderCache`
- ✅ Integration tests still pass
- ✅ `run_dev.py` works identically
- ✅ Validation script output matches baseline

---

### Step 4: Extract MarketDataHandler (45 min)

**Goal**: Move quote/market data handling

**Tasks**:
- Implement `MarketDataHandler` in `sdk/market_data.py`
- Copy quote update handlers, status bar task
- Write unit tests
- Update `TradingIntegration` to delegate
- Run all tests

**Success Criteria**: (same as Step 3)

---

### Step 5: Extract EventRouter (1.5 hours)

**Goal**: Move SDK event handlers (largest module!)

**Tasks**:
- Implement `EventRouter` in `sdk/event_router.py`
- Copy all 14 event handlers
- Copy deduplication logic
- Write unit tests (mock SDK events)
- Update `TradingIntegration` to delegate
- Run all tests

**Success Criteria**: (same as Step 3)

---

### Step 6: Extract OrderPollingService (30 min)

**Goal**: Move background order polling

**Tasks**:
- Implement `OrderPollingService` in `sdk/order_polling.py`
- Copy polling task
- Write unit tests
- Update `TradingIntegration` to delegate
- Run all tests

**Success Criteria**: (same as Step 3)

---

### Step 7: Extract SDKConnectionManager (45 min)

**Goal**: Move lifecycle management

**Tasks**:
- Implement `SDKConnectionManager` in `sdk/connection_manager.py`
- Copy connect/disconnect logic
- Write unit tests
- Update `TradingIntegration` to delegate
- Run all tests

**Success Criteria**: (same as Step 3)

---

### Step 8: Extract PnLTracker (45 min)

**Goal**: Move P&L calculation logic

**Tasks**:
- Implement `PnLTracker` in `sdk/pnl_tracker.py`
- Copy position tracking, P&L calculation
- Write unit tests
- Update `TradingIntegration` to delegate
- Run all tests

**Success Criteria**: (same as Step 3)

---

### Step 9: Finalize Facade (1 hour)

**Goal**: Clean up `TradingIntegration` to be pure facade

**Tasks**:
- Remove all extracted code from `trading.py`
- Keep only public API methods (delegation)
- Keep helper methods (shared utilities)
- Add comprehensive docstring explaining facade pattern
- Run all tests

**Success Criteria**:
- ✅ `trading.py` is ~300 lines (down from 2,169)
- ✅ All tests pass
- ✅ `run_dev.py` works identically
- ✅ Validation script output matches baseline EXACTLY

---

### Step 10: Final Validation (30 min)

**Goal**: Prove refactoring success

**Tasks**:
- Run full test suite: `pytest`
- Run validation script: `python tests/validate_refactoring.py`
- Run `run_dev.py` and manually verify behavior
- Compare logs/output with pre-refactor baseline
- Run smoke test: `python run_tests.py` → `[s]`

**Success Criteria**:
- ✅ All tests pass (same count as before)
- ✅ Validation output IDENTICAL to baseline
- ✅ `run_dev.py` behavior unchanged
- ✅ No new warnings/errors in logs
- ✅ Smoke test passes

---

## 🎯 Success Metrics

**Before Refactoring**:
- `trading.py`: 2,169 lines
- Tests passing: X tests
- `run_dev.py` behavior: [baseline recording]

**After Refactoring**:
- `trading.py`: ~300 lines (facade)
- `sdk/*.py`: 6 modules, ~1,900 lines total
- Tests passing: X tests (same count!)
- `run_dev.py` behavior: IDENTICAL to baseline

**Key Metric**: Zero functional changes, 100% behavior preservation.

---

## 🚨 Risk Mitigation

### What Could Go Wrong?

1. **Shared State Issues**
   - **Risk**: Modules need shared state (suite, event_bus, etc.)
   - **Mitigation**: Pass dependencies explicitly, use dependency injection

2. **Circular Dependencies**
   - **Risk**: EventRouter needs ProtectiveOrderCache, which needs EventRouter
   - **Mitigation**: Use interfaces/protocols, inject dependencies via constructor

3. **Event Ordering Changes**
   - **Risk**: Refactoring changes event processing order
   - **Mitigation**: Behavior tests catch this, validation script detects differences

4. **Performance Regression**
   - **Risk**: Extra delegation layers slow things down
   - **Mitigation**: Profile before/after, extra function calls negligible vs I/O

5. **Import Errors**
   - **Risk**: Circular imports break at runtime
   - **Mitigation**: Test imports in isolation, use TYPE_CHECKING for type hints

### Safety Nets

✅ **Comprehensive behavior tests** - Catch functional changes
✅ **Validation script** - Deterministic output comparison
✅ **Manual verification** - Run `run_dev.py` after each step
✅ **Git commits** - Commit after each successful module extraction
✅ **Rollback plan** - Can revert to any commit if something breaks

---

## 🛠️ Tools and Commands

### Run Tests After Each Step
```bash
# Unit tests (fast)
pytest tests/unit/test_trading_integration*.py -v

# Integration tests (slower, requires SDK)
pytest tests/integration/test_trading_integration*.py -v

# All tests
pytest -v

# Validation script
python tests/validate_refactoring.py
```

### Manual Verification
```bash
# Run dev environment (most important test!)
python run_dev.py

# Check for import errors
python -c "from risk_manager.integrations.trading import TradingIntegration; print('OK')"
```

### Code Quality
```bash
# Check line counts
find src/risk_manager/integrations/sdk -name "*.py" -exec wc -l {} +

# Check for TODOs or broken code
grep -r "TODO\|FIXME\|XXX" src/risk_manager/integrations/sdk/
```

---

## 📚 Documentation Updates

After refactoring, update:

1. **Module docstrings** - Explain new structure
2. **CLAUDE.md** - Update architecture section
3. **SDK_INTEGRATION_GUIDE.md** - Document new modules
4. **This file** - Mark as "COMPLETED" and archive

---

## 🎬 Ready to Start?

**Recommended Approach**: **Single Agent** with incremental validation

**Estimated Duration**: 4-6 hours of agent work

**Safety Level**: ⭐⭐⭐⭐⭐ (Very safe with testing strategy)

**Next Step**: Start with Step 1 (Write Behavior Tests)

---

**Questions Before We Begin?**

1. Do you want to proceed with **single agent** (safer) or **multiple agents** (faster but riskier)?
2. Should we start with behavior tests, or do you want to review the module design first?
3. Any specific concerns about backward compatibility?

Let me know and we'll begin! 🚀
