# Runtime Validation Integration

**MANDATORY runtime validation for every feature**

**Last Updated**: 2025-10-25
**Authority**: THE runtime validation integration guide
**Status**: Active - Required for all development

---

## Table of Contents

1. [The 33-Project Problem](#the-33-project-problem)
2. [Integration with Workflow](#integration-with-workflow)
3. [The 8-Checkpoint System](#the-8-checkpoint-system-core-features)
4. [Feature-Specific Logging](#feature-specific-logging-every-feature-type)
5. [Smoke Test Requirements](#smoke-test-requirements-mandatory)
6. [Debugging Protocol](#debugging-protocol-when-smoke-fails)
7. [Definition of Done v2.0](#definition-of-done-v20-updated)
8. [Making Features Observable](#making-features-observable)
9. [Success Checklist](#success-checklist)

---

## The 33-Project Problem

**Tests pass, runtime broken** killed projects #1-33.

**Root Cause**: No proof system is alive after tests pass.

**Symptoms**:
- All pytest tests pass ✅
- Coverage reports look good ✅
- Static analysis clean ✅
- Code review approved ✅
- **System starts but nothing happens** ❌
- **No events fire** ❌
- **No proof of life** ❌

**Solution**: Make runtime validation MANDATORY.

**What Changed in V34**:
- Added Runtime Reliability Pack (smoke, soak, trace, logs, env)
- Added 8-checkpoint logging system
- Made smoke tests MANDATORY before marking complete
- Made features OBSERVABLE through logging
- Exit codes enforce liveness proof

---

## Integration with Workflow

### OLD Workflow (Projects #1-33)

```
Write code → Tests pass ✅ → Mark complete → Deploy
                                                ↓
                                    Runtime broken ❌
                                    No one notices until production
```

**Problem**: No runtime validation gate

### NEW Workflow (Project #34)

```
Write code → Tests pass ✅ → Smoke test → Exit code 0 ✅ → Mark complete → Deploy
                                  ↓ Exit 1 or 2
                                  Debug → Fix → Repeat
```

**Can't skip smoke test.**

### Why This Works

**Before**: Trust tests alone (insufficient)
**After**: Tests + runtime proof (sufficient)

**Tests prove**: Logic is correct
**Smoke test proves**: System is alive

**Together**: Feature works in reality, not just in tests

---

## The 8-Checkpoint System (Core Features)

### When to Use

If your feature touches ANY of these files:
- `src/risk_manager/core/manager.py`
- `src/risk_manager/core/engine.py`
- `src/risk_manager/sdk/enforcement.py`

Then you MUST add checkpoint logging.

### Why 8 Checkpoints?

**Strategic placement** covers the entire lifecycle:
1. Service starts
2. Config loads
3. SDK connects
4. Rules initialize
5. Event loop starts
6. **Events fire** ← PROOF OF LIFE (most common failure)
7. Rules evaluate
8. Enforcement executes

**When smoke test fails**: Logs show EXACTLY which checkpoint failed

### The 8 Checkpoints

#### Checkpoint 1: 🚀 Service Start

**File**: `src/risk_manager/core/manager.py`
**Function**: `start()`
**Location**: Beginning of function

**Log**:
```python
logger.info("🚀 Checkpoint 1: Service Start - Risk Manager starting...")
```

**Proves**: Service can start without exceptions

**Common Failures**:
- Import errors
- Missing dependencies
- Configuration file not found

---

#### Checkpoint 2: ✅ Config Loaded

**File**: `src/risk_manager/core/manager.py`
**Function**: `_load_config()`
**Location**: After successful config load

**Log**:
```python
logger.info(f"✅ Checkpoint 2: Config Loaded - {len(rules)} rules enabled")
```

**Proves**: Configuration loads and parses correctly

**Common Failures**:
- Invalid YAML syntax
- Missing required fields
- Type validation errors

---

#### Checkpoint 3: ✅ SDK Connected

**File**: `src/risk_manager/core/manager.py`
**Function**: `_connect_sdk()`
**Location**: After successful SDK connection

**Log**:
```python
logger.info(f"✅ Checkpoint 3: SDK Connected - account {account_id}")
```

**Proves**: SDK authentication and connection works

**Common Failures**:
- Invalid API credentials
- Network connectivity issues
- SDK version incompatibility

---

#### Checkpoint 4: ✅ Rules Initialized

**File**: `src/risk_manager/core/manager.py`
**Function**: `_initialize_rules()`
**Location**: After all rules instantiated

**Log**:
```python
logger.info(f"✅ Checkpoint 4: Rules Initialized - {len(self.rules)} rules ready")
```

**Proves**: All risk rules load correctly

**Common Failures**:
- Missing rule dependencies
- Invalid rule configuration
- Rule instantiation errors

---

#### Checkpoint 5: ✅ Event Loop Running

**File**: `src/risk_manager/core/engine.py`
**Function**: `start()`
**Location**: After event loop starts

**Log**:
```python
logger.info("✅ Checkpoint 5: Event Loop Running - awaiting events...")
```

**Proves**: Async event loop is running

**Common Failures**:
- Event loop configuration errors
- Async runtime issues

---

#### Checkpoint 6: 📨 Event Received

**File**: `src/risk_manager/core/engine.py`
**Function**: `handle_event()`
**Location**: Start of function

**Log**:
```python
logger.info(f"📨 Checkpoint 6: Event Received - {event.event_type} for {event.symbol}")
```

**Proves**: **SYSTEM IS ALIVE** - Events are flowing

**Common Failures** (MOST COMMON):
- Event subscriptions not wired
- EventBridge not forwarding events
- SDK not emitting events
- Wrong event handlers registered

**This is the #1 failure point** - System boots but nothing happens

---

#### Checkpoint 7: 🔍 Rule Evaluated

**File**: `src/risk_manager/core/engine.py`
**Function**: `handle_event()` (after rule evaluation)
**Location**: After calling rule.evaluate()

**Log**:
```python
logger.info(f"🔍 Checkpoint 7: Rule {rule_id} evaluated - result={violated}")
```

**Proves**: Rules are evaluating against events

**Common Failures**:
- Rule evaluation exceptions
- Missing state data
- Calculation errors

---

#### Checkpoint 8: ⚠️ Enforcement Triggered

**File**: `src/risk_manager/sdk/enforcement.py`
**Function**: `enforce()`
**Location**: When enforcement action executes

**Log**:
```python
logger.warning(f"⚠️ Checkpoint 8: Enforcement triggered - {action} for {rule_id}")
```

**Proves**: Enforcement actions execute

**Common Failures**:
- SDK enforcement methods not wired
- Permission errors
- Network errors during enforcement

---

### Checkpoint Usage Example

**Complete flow in logs**:
```
2025-10-25 10:00:00 INFO 🚀 Checkpoint 1: Service Start - Risk Manager starting...
2025-10-25 10:00:01 INFO ✅ Checkpoint 2: Config Loaded - 13 rules enabled
2025-10-25 10:00:02 INFO ✅ Checkpoint 3: SDK Connected - account ACC123
2025-10-25 10:00:03 INFO ✅ Checkpoint 4: Rules Initialized - 13 rules ready
2025-10-25 10:00:03 INFO ✅ Checkpoint 5: Event Loop Running - awaiting events...
2025-10-25 10:00:05 INFO 📨 Checkpoint 6: Event Received - POSITION_OPENED for ES
2025-10-25 10:00:05 INFO 🔍 Checkpoint 7: Rule RULE-001 evaluated - result=False
2025-10-25 10:00:05 INFO 🔍 Checkpoint 7: Rule RULE-002 evaluated - result=False
2025-10-25 10:00:10 INFO 📨 Checkpoint 6: Event Received - TRADE_UPDATE for ES
2025-10-25 10:00:10 INFO 🔍 Checkpoint 7: Rule RULE-003 evaluated - result=True
2025-10-25 10:00:10 WARNING ⚠️ Checkpoint 8: Enforcement triggered - CLOSE_ALL for RULE-003
```

**If logs stop at Checkpoint 5**: No events firing (most common failure)

---

## Feature-Specific Logging (Every Feature Type)

### Phase 1: State Managers

#### MOD-003: TimerManager

**File**: `src/risk_manager/state/timer_manager.py`

**When creating timer**:
```python
def create_timer(self, duration: int, callback: Callable, timer_id: str = None) -> str:
    """Create a new timer"""
    timer_id = timer_id or self._generate_id()
    fire_time = datetime.now() + timedelta(seconds=duration)

    # LOG: Timer creation
    logger.info(f"Timer created: id={timer_id}, duration={duration}s, fires_at={fire_time.isoformat()}")

    self._timers[timer_id] = {
        'fire_time': fire_time,
        'callback': callback
    }
    return timer_id
```

**When timer fires**:
```python
async def _timer_fired(self, timer_id: str):
    """Handle timer firing"""
    timer = self._timers.get(timer_id)
    if not timer:
        return

    callback_name = timer['callback'].__name__

    # LOG: Timer fired
    logger.info(f"Timer fired: id={timer_id}, callback={callback_name}")

    await timer['callback']()
    del self._timers[timer_id]
```

**When canceling timer**:
```python
def cancel_timer(self, timer_id: str) -> bool:
    """Cancel a timer"""
    if timer_id in self._timers:
        # LOG: Timer canceled
        logger.info(f"Timer canceled: id={timer_id}")
        del self._timers[timer_id]
        return True
    return False
```

**Observable**: Can see timers created, fired, and canceled

---

#### MOD-002: LockoutManager

**File**: `src/risk_manager/state/lockout_manager.py`

**When locking account**:
```python
async def lock_account(
    self,
    account_id: str,
    reason: str,
    unlock_time: datetime,
    rule_id: str
) -> None:
    """Lock an account"""
    # LOG: Account locked (use warning level - critical action)
    logger.warning(
        f"🔒 Account locked: {account_id}, reason={reason}, "
        f"unlock_at={unlock_time.isoformat()}, rule={rule_id}"
    )

    await self.db.store_lockout(account_id, reason, unlock_time, rule_id)
```

**When checking lockout**:
```python
async def is_locked(self, account_id: str) -> bool:
    """Check if account is locked"""
    lockout = await self.db.get_active_lockout(account_id)
    is_locked = lockout is not None

    # LOG: Lockout check (debug level - frequent operation)
    logger.debug(f"Lockout check: {account_id}, locked={is_locked}")

    return is_locked
```

**When unlocking account**:
```python
async def unlock_account(self, account_id: str) -> None:
    """Unlock an account (admin override or scheduled)"""
    lockout = await self.db.get_active_lockout(account_id)
    if lockout:
        duration = datetime.now() - lockout['locked_at']

        # LOG: Account unlocked
        logger.info(
            f"🔓 Account unlocked: {account_id}, "
            f"was_locked_for={duration.total_seconds()}s"
        )

        await self.db.clear_lockout(account_id)
```

**Observable**: Can see accounts locked, checked, and unlocked

---

#### MOD-004: ResetScheduler

**File**: `src/risk_manager/state/reset_scheduler.py`

**When starting scheduler**:
```python
async def start(self):
    """Start the daily reset scheduler"""
    reset_time = self.config.get('reset_time', '00:00')
    timezone = self.config.get('timezone', 'America/Chicago')

    # LOG: Reset scheduled
    logger.info(f"📅 Reset scheduled: daily at {reset_time} {timezone}")

    self._schedule_next_reset()
```

**When reset triggers**:
```python
async def reset(self):
    """Execute daily reset"""
    current_time = datetime.now(tz=self.timezone)

    # LOG: Reset triggered
    logger.info(f"📅 Daily reset triggered at {current_time.isoformat()}")

    # Reset P&L tracker
    await self.pnl_tracker.reset_daily()

    # Clear lockouts
    await self.lockout_manager.clear_daily_lockouts()

    # LOG: Reset complete
    logger.info("📅 Daily reset complete: P&L reset, lockouts cleared")
```

**Observable**: Can see reset schedule and execution

---

### Phase 2: Risk Rules

#### RULE-003: DailyRealizedLoss (HARD LOCKOUT)

**File**: `src/risk_manager/rules/daily_loss.py`

**In evaluate()**:
```python
async def evaluate(self, event: RiskEvent) -> bool:
    """Check if daily realized loss limit exceeded"""
    account_id = event.account_id

    # Get combined P&L (realized + unrealized)
    combined_pnl = await self.pnl_tracker.get_combined_pnl(account_id)

    # Check against limit
    violated = combined_pnl <= self.limit

    # LOG: Rule evaluation (Checkpoint 7)
    logger.info(
        f"🔍 Checkpoint 7: RULE-003 evaluated - "
        f"account={account_id}, combined_pnl=${combined_pnl:.2f}, "
        f"limit=${self.limit:.2f}, violated={violated}"
    )

    return violated
```

**In enforce()**:
```python
async def enforce(self, event: RiskEvent) -> None:
    """Close all positions and lock account"""
    account_id = event.account_id

    # LOG: Enforcement - closing positions (Checkpoint 8)
    logger.warning(
        f"⚠️ Checkpoint 8: RULE-003 enforcement - "
        f"closing all positions for {account_id}"
    )

    # Close all positions
    await self.trading_integration.close_all_positions(account_id)

    # Calculate unlock time (next trading day at midnight CT)
    unlock_time = self._next_trading_day_midnight()

    # LOG: Enforcement - lockout (Checkpoint 8 continued)
    logger.warning(
        f"⚠️ Checkpoint 8: RULE-003 lockout - "
        f"{account_id} locked until {unlock_time.isoformat()}"
    )

    # Lock account
    reason = f"Daily loss limit exceeded: ${combined_pnl:.2f}"
    await self.lockout_manager.lock_account(account_id, reason, unlock_time, "RULE-003")
```

**Observable**: Can see rule evaluation and enforcement actions

---

#### RULE-004: DailyUnrealizedLoss (TRADE-BY-TRADE)

**File**: `src/risk_manager/rules/daily_unrealized_loss.py`

**In evaluate()**:
```python
async def evaluate(self, event: RiskEvent) -> bool:
    """Check if daily unrealized loss limit exceeded"""
    account_id = event.account_id
    position_id = event.position_id

    # Get unrealized P&L for specific position
    unrealized = await self.pnl_tracker.get_unrealized_pnl(account_id, position_id)

    # Check against limit
    violated = unrealized <= self.limit

    # LOG: Rule evaluation (Checkpoint 7)
    logger.info(
        f"🔍 Checkpoint 7: RULE-004 evaluated - "
        f"position={position_id}, unrealized_pnl=${unrealized:.2f}, "
        f"limit=${self.limit:.2f}, violated={violated}"
    )

    return violated
```

**In enforce()**:
```python
async def enforce(self, event: RiskEvent) -> None:
    """Close only the violating position (trade-by-trade)"""
    position_id = event.position_id

    # LOG: Enforcement - closing single position (Checkpoint 8)
    logger.warning(
        f"⚠️ Checkpoint 8: RULE-004 enforcement - "
        f"closing position {position_id} only (trade-by-trade enforcement)"
    )

    # Close only this position
    await self.trading_integration.close_position(position_id)
```

**Observable**: Can see which positions trigger rule and get closed

---

#### RULE-001: MaxPositionSize

**File**: `src/risk_manager/rules/max_position.py`

**In evaluate()**:
```python
async def evaluate(self, event: RiskEvent) -> bool:
    """Check if position size exceeds maximum"""
    symbol = event.symbol
    quantity = event.quantity
    max_allowed = self.limits.get(symbol, self.default_limit)

    violated = abs(quantity) > max_allowed

    # LOG: Rule evaluation
    logger.info(
        f"🔍 Checkpoint 7: RULE-001 evaluated - "
        f"symbol={symbol}, quantity={quantity}, "
        f"max_allowed={max_allowed}, violated={violated}"
    )

    return violated
```

**In enforce()**:
```python
async def enforce(self, event: RiskEvent) -> None:
    """Reduce position to maximum allowed size"""
    symbol = event.symbol
    current_qty = event.quantity
    max_allowed = self.limits.get(symbol, self.default_limit)

    excess = abs(current_qty) - max_allowed

    # LOG: Enforcement
    logger.warning(
        f"⚠️ Checkpoint 8: RULE-001 enforcement - "
        f"reducing {symbol} position by {excess} contracts "
        f"(from {current_qty} to {max_allowed})"
    )

    await self.trading_integration.reduce_position(symbol, excess)
```

**Observable**: Can see oversized positions detected and reduced

---

#### RULE-002: MaxContractsPerInstrument

**File**: `src/risk_manager/rules/max_contracts_per_instrument.py`

**In evaluate()**:
```python
async def evaluate(self, event: RiskEvent) -> bool:
    """Check if total contracts for instrument exceed maximum"""
    instrument = event.instrument
    account_id = event.account_id

    # Get total contracts across all symbols for this instrument
    total_contracts = await self.position_tracker.get_total_contracts(
        account_id,
        instrument
    )

    max_allowed = self.limits.get(instrument, self.default_limit)
    violated = total_contracts > max_allowed

    # LOG: Rule evaluation
    logger.info(
        f"🔍 Checkpoint 7: RULE-002 evaluated - "
        f"instrument={instrument}, total_contracts={total_contracts}, "
        f"max_allowed={max_allowed}, violated={violated}"
    )

    return violated
```

**Observable**: Can see instrument-level contract tracking

---

#### RULE-005: DailyPositionTurnover

**File**: `src/risk_manager/rules/daily_turnover.py`

**In evaluate()**:
```python
async def evaluate(self, event: RiskEvent) -> bool:
    """Check if daily turnover exceeds maximum"""
    account_id = event.account_id

    # Get today's turnover
    turnover = await self.turnover_tracker.get_daily_turnover(account_id)

    violated = turnover > self.max_turnover

    # LOG: Rule evaluation
    logger.info(
        f"🔍 Checkpoint 7: RULE-005 evaluated - "
        f"account={account_id}, turnover={turnover}, "
        f"max_turnover={self.max_turnover}, violated={violated}"
    )

    return violated
```

**In enforce()**:
```python
async def enforce(self, event: RiskEvent) -> None:
    """Lock account for excessive turnover"""
    account_id = event.account_id
    turnover = await self.turnover_tracker.get_daily_turnover(account_id)

    # LOG: Enforcement
    logger.warning(
        f"⚠️ Checkpoint 8: RULE-005 enforcement - "
        f"locking account {account_id} for excessive turnover "
        f"({turnover} contracts, max {self.max_turnover})"
    )

    unlock_time = self._next_trading_day_midnight()
    reason = f"Excessive daily turnover: {turnover} contracts"
    await self.lockout_manager.lock_account(account_id, reason, unlock_time, "RULE-005")
```

**Observable**: Can see turnover tracking and enforcement

---

#### RULE-006: MaxDrawdownPercentage

**File**: `src/risk_manager/rules/max_drawdown.py`

**In evaluate()**:
```python
async def evaluate(self, event: RiskEvent) -> bool:
    """Check if drawdown percentage exceeds maximum"""
    account_id = event.account_id

    # Get peak equity and current equity
    peak_equity = await self.equity_tracker.get_peak_equity(account_id)
    current_equity = await self.equity_tracker.get_current_equity(account_id)

    # Calculate drawdown percentage
    drawdown_pct = ((peak_equity - current_equity) / peak_equity) * 100

    violated = drawdown_pct > self.max_drawdown_pct

    # LOG: Rule evaluation
    logger.info(
        f"🔍 Checkpoint 7: RULE-006 evaluated - "
        f"account={account_id}, peak=${peak_equity:.2f}, "
        f"current=${current_equity:.2f}, drawdown={drawdown_pct:.2f}%, "
        f"max={self.max_drawdown_pct}%, violated={violated}"
    )

    return violated
```

**Observable**: Can see drawdown calculations and thresholds

---

#### Remaining Rules (RULE-007 through RULE-013)

**Same pattern for all rules**:

1. **In evaluate()**: Log rule ID, inputs, calculation, result
2. **In enforce()**: Log enforcement action details
3. **Use appropriate log level**:
   - `logger.info()` for evaluations (Checkpoint 7)
   - `logger.warning()` for enforcement (Checkpoint 8)
   - `logger.error()` for exceptions

**Template**:
```python
# Evaluation
logger.info(
    f"🔍 Checkpoint 7: {RULE_ID} evaluated - "
    f"{key_metrics}, violated={violated}"
)

# Enforcement
logger.warning(
    f"⚠️ Checkpoint 8: {RULE_ID} enforcement - "
    f"{action_description}"
)
```

---

### Phase 3: SDK Integration

#### Quote Data Integration

**File**: `src/risk_manager/integrations/market_data.py`

**When receiving quote updates**:
```python
async def _on_quote_update(self, symbol: str, quote: dict):
    """Handle real-time quote update"""
    price = quote.get('last_price')
    was_throttled = self._should_throttle(symbol)

    # LOG: Quote received (use debug - high frequency)
    logger.debug(
        f"Quote: {symbol} @ ${price:.2f}, "
        f"bid=${quote.get('bid'):.2f}, ask=${quote.get('ask'):.2f}, "
        f"throttled={was_throttled}"
    )

    if not was_throttled:
        await self._update_unrealized_pnl(symbol, price)
```

**When calculating unrealized P&L**:
```python
async def calculate_unrealized_pnl(self, position_id: str) -> float:
    """Calculate unrealized P&L for position"""
    position = await self.get_position(position_id)
    current_price = await self.get_current_price(position.symbol)

    # Calculate P&L
    entry_price = position.average_price
    quantity = position.quantity
    unrealized_pnl = (current_price - entry_price) * quantity * position.multiplier

    # LOG: Unrealized P&L calculation
    logger.debug(
        f"Unrealized P&L: {position.symbol} position={position_id}, "
        f"entry=${entry_price:.2f}, current=${current_price:.2f}, "
        f"qty={quantity}, pnl=${unrealized_pnl:.2f}"
    )

    return unrealized_pnl
```

**Observable**: Can see quote flow and P&L calculations

---

#### EventBridge Integration

**File**: `src/risk_manager/sdk/event_bridge.py`

**When subscribing to SDK events**:
```python
async def subscribe(self, event_types: List[str]):
    """Subscribe to SDK events"""
    # LOG: Subscriptions
    logger.info(
        f"EventBridge: Subscribing to {len(event_types)} event types: "
        f"{', '.join(event_types)}"
    )

    for event_type in event_types:
        handler = self._get_handler(event_type)
        self.sdk.on(event_type, handler)
```

**When forwarding events to engine**:
```python
async def _forward_to_engine(self, sdk_event: dict):
    """Convert SDK event to RiskEvent and forward"""
    risk_event = self._convert_event(sdk_event)

    # LOG: Event forwarding (debug - high frequency)
    logger.debug(
        f"EventBridge: Forwarding {sdk_event['type']} → "
        f"{risk_event.event_type} for {risk_event.symbol}"
    )

    await self.engine.handle_event(risk_event)
```

**Observable**: Can see event subscriptions and forwarding

---

### Phase 4: CLI

#### Admin CLI

**File**: `src/risk_manager/cli/admin.py`

**When changing configuration**:
```python
def config_set(self, rule_id: str, param: str, value: str):
    """Set configuration parameter (admin only)"""
    user = os.getenv('USER', 'unknown')

    # LOG: Admin configuration change
    logger.info(
        f"Admin: Config changed - {rule_id}.{param}={value}, "
        f"user={user}, timestamp={datetime.now().isoformat()}"
    )

    self.config_manager.set(rule_id, param, value)
    self.config_manager.save()
```

**When restarting daemon**:
```python
def daemon_restart(self):
    """Restart the risk manager service"""
    user = os.getenv('USER', 'unknown')

    # LOG: Admin restart
    logger.warning(
        f"Admin: Daemon restart requested, "
        f"user={user}, timestamp={datetime.now().isoformat()}"
    )

    self.service_manager.restart()
```

**When unlocking account**:
```python
async def unlock_account(self, account_id: str):
    """Manually unlock account (admin override)"""
    user = os.getenv('USER', 'unknown')

    # LOG: Admin unlock
    logger.warning(
        f"Admin: Manual unlock - account={account_id}, "
        f"user={user}, timestamp={datetime.now().isoformat()}"
    )

    await self.lockout_manager.unlock_account(account_id)
```

**Observable**: Can see all admin actions with user attribution

---

#### Trader CLI

**File**: `src/risk_manager/cli/trader.py`

**When viewing status**:
```python
def status(self, account_id: str):
    """View account status (read-only)"""
    # LOG: Trader status query
    logger.info(f"Trader: Status viewed - account={account_id}")

    status = self.manager.get_status(account_id)
    self._print_status(status)
```

**When viewing P&L**:
```python
async def pnl(self, account_id: str):
    """View P&L summary (read-only)"""
    # LOG: Trader P&L query
    logger.info(f"Trader: P&L queried - account={account_id}")

    pnl_data = await self.pnl_tracker.get_summary(account_id)
    self._print_pnl(pnl_data)
```

**When viewing lockout status**:
```python
async def lockout_status(self, account_id: str):
    """View lockout status (read-only)"""
    # LOG: Trader lockout query
    logger.info(f"Trader: Lockout status queried - account={account_id}")

    lockout = await self.lockout_manager.get_active_lockout(account_id)
    self._print_lockout(lockout)
```

**Observable**: Can see trader queries (audit trail)

---

## Smoke Test Requirements (MANDATORY)

### When to Run Smoke Tests

**MANDATORY after**:
- Implementing ANY feature
- Changing ANY core file (manager.py, engine.py, enforcement.py)
- Adding ANY new rule
- Modifying SDK integration
- Changing event subscriptions
- Updating configuration loading

**Before marking feature complete**: Smoke test MUST pass

### Command

```bash
python run_tests.py
# Select: [s] Runtime SMOKE
# Wait up to 8 seconds
```

### What Smoke Test Does

1. Boots system in DRY-RUN mode
2. Waits up to 8 seconds for first event
3. Returns exit code based on result

**DRY-RUN mode**: Mock data, no real trading, deterministic

### Exit Codes

#### Exit Code 0: SUCCESS ✅

**Meaning**: System is ALIVE
- System boots without exceptions
- SDK connects (or mocked connection succeeds)
- Event loop starts
- **First event fires within 8 seconds**
- Event is processed successfully

**What this proves**:
- All imports work
- Configuration loads
- SDK integration works
- Event subscriptions are wired correctly
- Event handling works
- **Feature is observable in runtime**

**Example output**:
```
🚀 Starting smoke test (8s timeout)...
✅ Checkpoint 1: Service Start
✅ Checkpoint 2: Config Loaded
✅ Checkpoint 3: SDK Connected
✅ Checkpoint 4: Rules Initialized
✅ Checkpoint 5: Event Loop Running
📨 Checkpoint 6: Event Received (at 2.3s)
✅ SMOKE TEST PASSED
Exit code: 0
```

---

#### Exit Code 1: EXCEPTION ❌

**Meaning**: Python exception occurred during boot or processing

**Common causes**:
- Import error (missing dependency)
- Syntax error
- Type error
- SDK authentication failure
- Configuration file missing/invalid
- Database connection failure

**What to do**:
1. Read logs: `cat data/logs/risk_manager.log | tail -50`
2. Look for stack trace
3. Fix the exception
4. Run smoke test again

**Example output**:
```
🚀 Starting smoke test (8s timeout)...
✅ Checkpoint 1: Service Start
✅ Checkpoint 2: Config Loaded
❌ EXCEPTION: ModuleNotFoundError: No module named 'some_dependency'
Exit code: 1
```

**Example log**:
```
2025-10-25 10:00:00 ERROR Exception in smoke test:
Traceback (most recent call last):
  File "src/risk_manager/core/manager.py", line 45, in start
    from some_dependency import something
ModuleNotFoundError: No module named 'some_dependency'
```

---

#### Exit Code 2: STALLED ❌

**Meaning**: System boots but NO events fire within 8 seconds

**This is the MOST COMMON failure mode** - "tests green but runtime broken"

**Common causes**:
- Event subscriptions not wired
- EventBridge not forwarding events
- SDK not emitting events (in DRY-RUN mode)
- Wrong event handlers registered
- Event queue blocked/deadlocked

**What to do**:
1. Check last checkpoint: `grep "Checkpoint" data/logs/risk_manager.log | tail -1`
2. If last checkpoint is 5 (Event Loop Running) → No events firing
3. Run trace mode: `python run_tests.py → [t]`
4. Check event subscriptions in code
5. Verify EventBridge wiring

**Example output**:
```
🚀 Starting smoke test (8s timeout)...
✅ Checkpoint 1: Service Start
✅ Checkpoint 2: Config Loaded
✅ Checkpoint 3: SDK Connected
✅ Checkpoint 4: Rules Initialized
✅ Checkpoint 5: Event Loop Running
⏱️ Waiting for first event...
⏱️ Timeout: No events received in 8 seconds
❌ SMOKE TEST FAILED: STALLED
Exit code: 2
```

**Example log**:
```
2025-10-25 10:00:00 INFO 🚀 Checkpoint 1: Service Start
2025-10-25 10:00:01 INFO ✅ Checkpoint 2: Config Loaded
2025-10-25 10:00:02 INFO ✅ Checkpoint 3: SDK Connected
2025-10-25 10:00:03 INFO ✅ Checkpoint 4: Rules Initialized
2025-10-25 10:00:03 INFO ✅ Checkpoint 5: Event Loop Running
[8 seconds pass - no Checkpoint 6]
2025-10-25 10:00:11 ERROR Smoke test timeout: No events received
```

---

### Integration with Roadmap

**Every feature in roadmap MUST include smoke test**:

```markdown
### Phase 1: State Management

- [ ] MOD-003: TimerManager
  - [ ] Implement TimerManager class
  - [ ] Add logging (create, fire, cancel)
  - [ ] Unit tests passing
  - [ ] **Smoke test passing (exit code 0)** ← MANDATORY
  - [ ] Update roadmap [x]

- [ ] MOD-002: LockoutManager
  - [ ] Implement LockoutManager class
  - [ ] Add logging (lock, unlock, check)
  - [ ] Unit tests passing
  - [ ] **Smoke test passing (exit code 0)** ← MANDATORY
  - [ ] Update roadmap [x]
```

**Can't mark complete without smoke test passing**

---

### Smoke Test vs Unit Tests

**Unit tests prove**: Logic is correct
**Smoke test proves**: System is alive

**Both required**:
- Unit tests: Fast, isolated, mocked
- Smoke test: Real boot, real wiring, proof of life

**Example scenario**:
```
✅ Unit tests: TimerManager.create_timer() works
✅ Unit tests: TimerManager._timer_fired() works
❌ Smoke test: Timers never fire in runtime

Root cause: Timer event loop not started in manager.start()
Solution: Add await timer_manager.start() to manager.start()
Re-run smoke test → ✅ Exit code 0
```

**Unit tests can't catch this** - it's a wiring issue, not logic issue

---

## Debugging Protocol (When Smoke Fails)

### Step-by-Step Protocol

#### Step 1: Run Smoke Test

```bash
python run_tests.py
# Select: [s] Runtime SMOKE
# Observe output and exit code
```

#### Step 2: Check Exit Code

**Exit code determines debugging path**:
- 0 → ✅ Success! You're done!
- 1 → Go to Step 3 (Exception Debugging)
- 2 → Go to Step 4 (Stalled Debugging)

---

### Step 3: Exception Debugging (Exit Code 1)

**Symptom**: Python exception during boot or processing

#### 3.1: Read Logs

```bash
# View last 50 lines (usually shows stack trace)
cat data/logs/risk_manager.log | tail -50

# Or use log viewer
python run_tests.py → [l]
```

#### 3.2: Identify Exception Type

**Look for**:
- `ModuleNotFoundError` → Missing dependency
- `ImportError` → Wrong import path
- `FileNotFoundError` → Missing config file
- `TypeError` → Wrong type passed to function
- `AttributeError` → Accessing non-existent attribute
- `KeyError` → Missing dict key
- `ValidationError` → Pydantic validation failed

#### 3.3: Common Fixes

**Missing dependency**:
```bash
# Error: ModuleNotFoundError: No module named 'pydantic'
# Fix:
pip install pydantic
# Or:
uv add pydantic
```

**Wrong API key**:
```bash
# Error: SDK authentication failed
# Fix:
# Edit config/api_config.yaml
# Add valid credentials
```

**Import typo**:
```python
# Error: ImportError: cannot import name 'RiskEvent' from 'risk_manager.core.events'
# Fix:
# Check actual class name in events.py
# Correct import statement
```

**Configuration error**:
```bash
# Error: ValidationError: field 'limit' required
# Fix:
# Check config/risk_config.yaml
# Add missing required fields
```

#### 3.4: Re-run After Fix

```bash
# Fix the issue
# Run smoke test again
python run_tests.py → [s]
# Check exit code
```

---

### Step 4: Stalled Debugging (Exit Code 2)

**Symptom**: System boots but no events fire within 8 seconds

**This is the #1 failure mode for "tests pass but runtime broken"**

#### 4.1: Find Last Checkpoint

```bash
# Find last checkpoint reached
grep "Checkpoint" data/logs/risk_manager.log | tail -1
```

**Interpret result**:
```
Last checkpoint: 1 → Crashed during config load
Last checkpoint: 2 → Crashed during SDK connection
Last checkpoint: 3 → Crashed during rule initialization
Last checkpoint: 4 → Crashed during event loop start
Last checkpoint: 5 → Event loop running, but NO EVENTS FIRING ← MOST COMMON
```

#### 4.2: If Stuck at Checkpoint 5 (Most Common)

**Meaning**: Event loop is running, but no events are being received

**Common causes**:
1. Event subscriptions not wired
2. EventBridge not forwarding events
3. SDK not emitting events in DRY-RUN mode
4. Wrong event handlers registered

**Debug steps**:

##### Check Event Subscriptions

```python
# In src/risk_manager/sdk/event_bridge.py
async def subscribe(self):
    """Check what events we're subscribing to"""
    # Should see this in logs:
    logger.info(f"EventBridge: Subscribing to {event_types}")

    # Common issue: Not subscribing to enough events
    # Should subscribe to:
    # - position_opened
    # - position_closed
    # - trade_executed
    # - order_filled
    # etc.
```

##### Check Event Forwarding

```python
# In src/risk_manager/sdk/event_bridge.py
async def _forward_to_engine(self, sdk_event):
    """Check if forwarding is wired"""
    # Should see this in logs:
    logger.debug(f"EventBridge: Forwarding {sdk_event['type']}")

    # Common issue: Handler registered but not calling forward
```

##### Check DRY-RUN Event Generation

```python
# In src/runtime/dry_run.py
async def generate_events(self):
    """Check if DRY-RUN mode generates events"""
    # Should emit events immediately after start
    # Common issue: DRY-RUN mode not enabled or not generating events
```

#### 4.3: Run Trace Mode

```bash
# Deep async debugging
python run_tests.py → [t] Runtime TRACE

# This enables ASYNC_DEBUG=1
# Dumps all pending async tasks every second
# Shows exactly what's running and what's blocked
```

**Read trace output**:
```bash
cat runtime_trace.log

# Look for:
# - Tasks that never complete
# - Deadlocked tasks
# - Blocked coroutines
```

#### 4.4: Check Event Loop

```python
# In src/risk_manager/core/engine.py
async def start(self):
    """Check event loop is properly started"""
    logger.info("✅ Checkpoint 5: Event Loop Running")

    # Should enter event loop
    while self.running:
        event = await self.event_queue.get()  # Blocks here waiting
        await self.handle_event(event)

    # Common issue: Event queue never receives events
    # Check: Is EventBridge putting events into the queue?
```

#### 4.5: Verify EventBridge Wiring

```python
# In src/risk_manager/core/manager.py
async def start(self):
    # ...
    # After initializing rules

    # MUST wire EventBridge to Engine
    self.event_bridge = EventBridge(self.sdk, self.engine)
    await self.event_bridge.subscribe()  # ← Critical!

    # Common issue: EventBridge created but not subscribed
    # Common issue: EventBridge not given engine reference
```

#### 4.6: Common Fixes

**Issue**: EventBridge not subscribed
```python
# In manager.py start()
# Add:
await self.event_bridge.subscribe([
    'position_opened',
    'position_closed',
    'trade_executed'
])
```

**Issue**: Events not forwarded to engine
```python
# In event_bridge.py
async def _on_sdk_event(self, sdk_event):
    risk_event = self._convert_event(sdk_event)
    # MUST call:
    await self.engine.handle_event(risk_event)  # ← Critical!
```

**Issue**: DRY-RUN not generating events
```python
# In manager.py start()
# Add for DRY-RUN mode:
if self.config.dry_run:
    self.dry_run = DryRunEventGenerator(self.event_bridge)
    await self.dry_run.start()  # ← Critical!
```

#### 4.7: Re-run After Fix

```bash
# Fix the wiring issue
# Run smoke test again
python run_tests.py → [s]
# Should now see Checkpoint 6 within 8 seconds
# Exit code should be 0
```

---

### Step 5: Soak Test (After Smoke Passes)

**After smoke test passes**, run extended validation:

```bash
python run_tests.py → [r] Runtime SOAK

# Runs for 30-60 seconds
# Checks for:
# - Memory leaks
# - Deadlocks
# - Resource exhaustion
# - Slow degradation
```

**When to use**:
- Before major deployments
- After performance-sensitive changes
- After async code changes

---

## Definition of Done v2.0 (UPDATED)

### Old Definition of Done (Projects #1-33)

```
✅ Unit tests written and passing
✅ Integration tests passing (if applicable)
✅ Roadmap updated ([x])
✅ Git committed and pushed
```

**Problem**: Feature can be "done" but broken in runtime

---

### New Definition of Done (Project #34)

```
✅ Unit tests written and passing
✅ Integration tests passing (if applicable)
✅ **Smoke test passing (exit code 0)** ← NEW & MANDATORY
✅ **Logging added (feature observable)** ← NEW & MANDATORY
✅ **Runtime trace clean (no deadlocks)** ← NEW & MANDATORY
✅ Roadmap updated ([x])
✅ Git committed and pushed
```

**Can't skip steps 3-5**

---

### Detailed Checklist

#### 1. Unit Tests Written and Passing

```bash
# Write tests first (TDD)
# Tests cover:
# - Happy path
# - Edge cases
# - Error conditions
# - Boundary values

# Run tests
python run_tests.py → [2] Unit tests

# Check results
cat test_reports/latest.txt

# Must see:
# ===== X passed in Y.YYs =====
# Exit code: 0
```

---

#### 2. Integration Tests Passing (If Applicable)

```bash
# Integration tests for:
# - SDK integration
# - Database operations
# - Multi-component interactions

# Run tests
python run_tests.py → [3] Integration tests

# Check results
cat test_reports/latest.txt

# Must see:
# ===== X passed in Y.YYs =====
# Exit code: 0
```

---

#### 3. Smoke Test Passing (EXIT CODE 0) - MANDATORY

```bash
# Run smoke test
python run_tests.py → [s] Runtime SMOKE

# MUST see:
# ✅ SMOKE TEST PASSED
# Exit code: 0

# If exit code 1 or 2:
# → NOT DONE
# → Debug using protocol above
# → Fix issue
# → Re-run smoke test
# → Repeat until exit code 0
```

**This proves**:
- Feature works in runtime, not just in tests
- System is alive and processing events
- Wiring is correct

**Can't mark complete without this**

---

#### 4. Logging Added (Feature Observable) - MANDATORY

```bash
# Run system
python run_tests.py → [s]

# Check logs
cat data/logs/risk_manager.log

# Should see your feature:
# - Initialization logs
# - Activity logs
# - Decision logs
# - Result logs

# Test: Can you answer these questions from logs?
# 1. Did the feature initialize correctly?
# 2. Is the feature processing events?
# 3. What decisions is the feature making?
# 4. What results is the feature producing?

# If can't answer → NOT observable → NOT done
```

**Test observability**:
```bash
# For TimerManager:
grep "Timer" data/logs/risk_manager.log
# Should see: Timer created, Timer fired, Timer canceled

# For LockoutManager:
grep "locked\|unlocked" data/logs/risk_manager.log
# Should see: Account locked, Account unlocked

# For RULE-003:
grep "RULE-003" data/logs/risk_manager.log
# Should see: Checkpoint 7 evaluated, Checkpoint 8 enforcement
```

---

#### 5. Runtime Trace Clean (No Deadlocks) - MANDATORY

```bash
# Run trace mode
python run_tests.py → [t] Runtime TRACE

# Wait 10-15 seconds
# Check trace log
cat runtime_trace.log

# Look for:
# - Tasks that never complete
# - Growing number of pending tasks
# - Blocked coroutines
# - Deadlocked operations

# Should see:
# - Consistent number of tasks (not growing)
# - Tasks complete regularly
# - No long-running blocked operations
```

**What clean trace looks like**:
```
=== Async Task Dump (1s) ===
Pending tasks: 5
- EventLoop.run_forever()
- Engine.handle_event() [running]
- PnLTracker.update() [waiting on DB]
- HeartbeatMonitor.beat() [sleeping]
- TimerManager._check_timers() [sleeping]

=== Async Task Dump (2s) ===
Pending tasks: 5
- EventLoop.run_forever()
- Engine.handle_event() [running]
- PnLTracker.update() [completed] ← Good!
- HeartbeatMonitor.beat() [sleeping]
- TimerManager._check_timers() [sleeping]
```

**What bad trace looks like**:
```
=== Async Task Dump (1s) ===
Pending tasks: 10

=== Async Task Dump (2s) ===
Pending tasks: 20

=== Async Task Dump (3s) ===
Pending tasks: 30

← Growing! Memory leak or deadlock!
```

**If trace is not clean**:
- → NOT DONE
- → Fix async issue
- → Re-run trace
- → Repeat until clean

---

#### 6. Roadmap Updated

```bash
# Edit docs/implementation/plan_2025-10-23.md
# Change:
# - [ ] Feature X
# To:
# - [x] Feature X ✅ COMPLETE (Smoke: 0, Tests: X passed)
```

---

#### 7. Git Committed and Pushed

```bash
git add .
git commit -m "Implement Feature X

- Unit tests: X passed
- Integration tests: X passed
- Smoke test: Exit code 0
- Logging: Observable
- Runtime trace: Clean

Closes #123"

git push origin main
```

---

### Enforcement Mechanism

**Pull Request Template**:
```markdown
## Pre-merge Checklist

- [ ] Unit tests passing
- [ ] Integration tests passing (if applicable)
- [ ] **Smoke test passing (exit code 0)**
- [ ] **Logging added (feature observable)**
- [ ] **Runtime trace clean**
- [ ] Roadmap updated
- [ ] Git committed

**Smoke Test Evidence**:
```
✅ SMOKE TEST PASSED
Exit code: 0
```

**Can't merge without smoke test passing**
```

---

## Making Features Observable

### The Observability Principle

**Every feature must answer**: "Can I see it working in logs?"

**If you can't see it, you can't debug it**

---

### Observability Test

**After implementing feature**:

#### 1. Run System

```bash
python run_tests.py → [s]
```

#### 2. Search Logs for Feature

```bash
grep "[FEATURE-NAME]" data/logs/risk_manager.log
```

#### 3. Answer These Questions

**Question 1**: Did the feature initialize correctly?
```bash
# Should see initialization log
# Example:
# 2025-10-25 10:00:00 INFO TimerManager initialized - max_timers=100
```

**Question 2**: Is the feature processing events/data?
```bash
# Should see activity logs
# Example:
# 2025-10-25 10:00:05 INFO Timer created: id=timer_001, duration=60s
# 2025-10-25 10:01:05 INFO Timer fired: id=timer_001, callback=reset_daily
```

**Question 3**: What decisions is the feature making?
```bash
# Should see decision logs
# Example:
# 2025-10-25 10:00:10 INFO 🔍 Checkpoint 7: RULE-003 evaluated - violated=True
```

**Question 4**: What results is the feature producing?
```bash
# Should see result logs
# Example:
# 2025-10-25 10:00:11 WARNING ⚠️ Checkpoint 8: RULE-003 enforcement - closing all positions
```

**If you can't answer these questions from logs**:
- → Feature is NOT observable
- → Feature is NOT done
- → Add more logging
- → Re-run observability test
- → Repeat until observable

---

### What to Log (Guidelines)

#### Initialization

**ALWAYS log**:
- Feature name
- Configuration parameters
- Resource allocation
- Dependencies loaded

**Example**:
```python
logger.info(
    f"TimerManager initialized - "
    f"max_timers={self.max_timers}, "
    f"resolution={self.resolution}s"
)
```

---

#### Activity

**ALWAYS log**:
- When feature does something
- What triggered the action
- Key parameters/inputs

**Example**:
```python
logger.info(
    f"Timer created: id={timer_id}, "
    f"duration={duration}s, "
    f"fires_at={fire_time.isoformat()}"
)
```

---

#### Decisions

**ALWAYS log**:
- What was evaluated
- What was the result
- Why this decision was made

**Example**:
```python
logger.info(
    f"🔍 Checkpoint 7: RULE-003 evaluated - "
    f"combined_pnl=${combined_pnl:.2f}, "
    f"limit=${self.limit:.2f}, "
    f"violated={violated}"
)
```

---

#### Results/Actions

**ALWAYS log**:
- What action is being taken
- What entity it affects
- Expected outcome

**Example**:
```python
logger.warning(
    f"⚠️ Checkpoint 8: RULE-003 enforcement - "
    f"closing all positions for {account_id}"
)
```

---

#### Errors

**ALWAYS log**:
- What operation failed
- What was the error
- What context (inputs, state)

**Example**:
```python
logger.error(
    f"Timer fire failed: id={timer_id}, "
    f"error={str(e)}, "
    f"callback={callback_name}"
)
```

---

### Log Levels

**DEBUG**: High-frequency operations (quotes, heartbeats)
```python
logger.debug(f"Quote: {symbol} @ ${price:.2f}")
```

**INFO**: Normal operations (events, evaluations, actions)
```python
logger.info(f"📨 Checkpoint 6: Event Received - {event.event_type}")
```

**WARNING**: Important actions (enforcement, lockouts, admin changes)
```python
logger.warning(f"⚠️ Checkpoint 8: Enforcement triggered")
```

**ERROR**: Failures (exceptions, failed operations)
```python
logger.error(f"Rule evaluation failed: {str(e)}")
```

---

### Anti-Patterns (DON'T DO THIS)

#### Don't Log Without Context

**BAD**:
```python
logger.info("Timer created")
```

**GOOD**:
```python
logger.info(f"Timer created: id={timer_id}, duration={duration}s")
```

---

#### Don't Log Without Values

**BAD**:
```python
logger.info("Rule evaluated")
```

**GOOD**:
```python
logger.info(
    f"🔍 Checkpoint 7: RULE-003 evaluated - "
    f"combined_pnl=${combined_pnl:.2f}, violated={violated}"
)
```

---

#### Don't Log Generic Messages

**BAD**:
```python
logger.info("Processing event")
```

**GOOD**:
```python
logger.info(f"📨 Checkpoint 6: Event Received - {event.event_type} for {event.symbol}")
```

---

#### Don't Skip Logging for "Simple" Features

**Even simple features need logging**:

```python
# Simple feature: Account is locked?
async def is_locked(self, account_id: str) -> bool:
    lockout = await self.db.get_active_lockout(account_id)
    is_locked = lockout is not None

    # Still log it! (debug level for frequency)
    logger.debug(f"Lockout check: {account_id}, locked={is_locked}")

    return is_locked
```

**Why**: Even simple operations need to be observable for debugging

---

## Success Checklist

### For Agents

**Before starting feature**:
- [ ] Read this document
- [ ] Understand 8-checkpoint system
- [ ] Know when to add checkpoints (core features)
- [ ] Know how to add feature-specific logging

**During feature implementation**:
- [ ] Write tests first (TDD)
- [ ] Add logging at strategic points
- [ ] Use appropriate log levels
- [ ] Include relevant context in logs

**After feature implementation**:
- [ ] Unit tests passing
- [ ] Integration tests passing (if applicable)
- [ ] **Run smoke test**
- [ ] **Check exit code 0**
- [ ] **Verify feature observable in logs**
- [ ] **Run trace mode (check clean)**
- [ ] Update roadmap
- [ ] Git commit

**Can't mark complete without**:
- [ ] Smoke test exit code 0
- [ ] Feature observable in logs
- [ ] Runtime trace clean

---

### For Reviewers

**When reviewing PR**:
- [ ] Unit tests present and passing
- [ ] Integration tests present (if needed)
- [ ] **Smoke test evidence included (exit code 0)**
- [ ] **Logging added (grep shows activity)**
- [ ] **Runtime trace clean (no deadlocks)**
- [ ] Roadmap updated
- [ ] Git commit message clear

**Can't approve without**:
- [ ] Smoke test exit code 0
- [ ] Feature observable
- [ ] Trace clean

---

### For Project Managers

**Feature status**:
- **In Progress**: Code written, tests written
- **Testing**: Tests passing, smoke test running
- **Review**: Smoke passed (exit 0), observable, trace clean
- **Complete**: Merged, deployed, monitored

**Can't move to Complete without**:
- [ ] Smoke test exit code 0
- [ ] Observable in production logs
- [ ] No runtime issues reported

---

## Summary

### The Core Problem

**Projects #1-33 failed** because:
- Tests passed ✅
- Runtime broken ❌
- No proof of liveness

### The Solution

**Project #34 succeeds** because:
- Tests pass ✅
- **Smoke test passes ✅** ← Proves liveness
- **Features observable ✅** ← Can debug
- **Runtime trace clean ✅** ← No deadlocks

### The Requirements

**Every feature MUST**:
1. Have tests that pass
2. **Have smoke test that passes (exit code 0)**
3. **Be observable in logs**
4. **Have clean runtime trace**

**Can't skip 2-4**

### The Workflow

```
Write code → Tests pass → Smoke test → Exit code 0 → Mark complete
                              ↓ Exit 1 or 2
                              Debug → Fix → Repeat
```

### The Checkpoints

**8 strategic checkpoints** cover entire lifecycle:
1. Service Start
2. Config Loaded
3. SDK Connected
4. Rules Initialized
5. Event Loop Running
6. **Event Received** ← Proof of life
7. Rule Evaluated
8. Enforcement Triggered

**Use for core features**, add feature-specific logging for everything else

### The Definition of Done

**Feature is NOT complete until**:
1. Unit tests passing
2. Integration tests passing
3. **Smoke test passing (exit code 0)**
4. **Logging added (observable)**
5. **Runtime trace clean**
6. Roadmap updated
7. Git committed

**Enforcement**: Can't merge without smoke test passing

---

**Last Updated**: 2025-10-25
**Authority**: THE runtime validation integration guide
**Status**: Active - Required for all development
**Next Review**: When runtime validation system changes

---

## Appendix: Quick Reference

### Commands

```bash
# Run smoke test (MANDATORY before marking complete)
python run_tests.py → [s]

# Run trace mode (check for deadlocks)
python run_tests.py → [t]

# View logs
python run_tests.py → [l]

# Run gate test (tests + smoke combo)
python run_tests.py → [g]
```

### Exit Codes

- **0** = Success (system alive)
- **1** = Exception (read logs)
- **2** = Stalled (check subscriptions)

### Debugging Path

```
Exit 1 → Read logs → Fix exception → Re-run
Exit 2 → Check checkpoints → Find where stalled → Fix wiring → Re-run
```

### Observability Test

```bash
# 1. Run system
python run_tests.py → [s]

# 2. Search logs
grep "[FEATURE]" data/logs/risk_manager.log

# 3. Can you answer:
# - Did it initialize?
# - Is it processing?
# - What decisions is it making?
# - What results is it producing?

# If NO → Add logging → Re-run
```

### Definition of Done Checklist

```
✅ Unit tests passing
✅ Integration tests passing (if applicable)
✅ Smoke test passing (exit code 0) ← MANDATORY
✅ Logging added (observable) ← MANDATORY
✅ Runtime trace clean ← MANDATORY
✅ Roadmap updated
✅ Git committed
```

**Can't skip smoke test, logging, or trace**

---

**End of Document**
