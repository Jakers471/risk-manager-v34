# IMPLEMENTATION MASTER PLAN
**Version**: 1.0
**Date**: 2025-10-27
**Agent**: Implementation Plan Agent (#7)
**Status**: Complete - Ready for Execution

---

## Executive Summary

This document provides a comprehensive, phased implementation plan to wire all 13 risk rules into the event-driven, SDK-first architecture. The plan is based on:

- ✅ **13 unified rule specifications** (conflict-free, user guidance applied)
- ✅ **SDK event mapping** (which events trigger which rules)
- ✅ **Enforcement architecture** (SDK enforcement flow documented)
- ✅ **Current implementation status** (2 rules complete, 11 missing)
- ✅ **Architectural patterns** (EventBus, EventBridge, RiskEngine validated)

### Current State
- **Implemented**: 2/13 rules (15%) - RULE-001, RULE-002
- **Partial**: 1/13 rules (8%) - RULE-003 (70% done, needs MOD-002/MOD-004)
- **Missing**: 10/13 rules (77%)
- **Critical Blockers**: 3 state managers (MOD-002, MOD-003, MOD-004), Market Data Feed, Event Router

### Target State
- **100% rule implementation** across all 4 categories
- **Complete state management** infrastructure
- **Market data integration** for unrealized P&L rules
- **Full enforcement wiring** with SDK actions
- **Production-ready testing** (unit, integration, E2E, runtime)

### Total Effort Estimate
- **Phase 1** (Infrastructure): 5-7 days
- **Phase 2** (High-Priority Rules): 6-8 days
- **Phase 3** (Medium-Priority Rules): 4-5 days
- **Phase 4** (Market Data + Rules): 5-7 days
- **Phase 5** (Production Polish): 3-4 days

**Total**: 23-31 days (4.5-6 weeks)

---

## Table of Contents

1. [Phase 1: Core Event Infrastructure](#phase-1-core-event-infrastructure) (5-7 days)
2. [Phase 2: State Management Modules](#phase-2-state-management-modules) (4-6 days)
3. [Phase 3: High-Priority Rules](#phase-3-high-priority-rules) (6-8 days)
4. [Phase 4: Medium-Priority Rules](#phase-4-medium-priority-rules) (4-5 days)
5. [Phase 5: Market Data + Unrealized PnL](#phase-5-market-data-unrealized-pnl) (5-7 days)
6. [Phase 6: Production Polish](#phase-6-production-polish) (3-4 days)
7. [Dependency Graph](#dependency-graph)
8. [Testing Strategy](#testing-strategy)
9. [Risk Mitigation](#risk-mitigation)

---

## Phase 1: Core Event Infrastructure
**Duration**: 5-7 days
**Goal**: Establish robust event routing and SDK integration foundation

### 1.1 Event Router Implementation (2 days)

**Why First?**
- Event Router is documented but not implemented (critical blocker)
- Lockout enforcement requires pre-rule event routing
- All rules depend on proper event routing

**Files to Create**:
```
src/risk_manager/core/event_router.py (150 lines)
tests/unit/test_event_router.py (200 lines)
tests/integration/test_event_router_lockout.py (150 lines)
```

**Key Classes/Functions**:
```python
class EventRouter:
    """Routes events from SDK to appropriate rules, enforces lockouts."""

    def __init__(self, lockout_manager: LockoutManager):
        self.lockout_manager = lockout_manager
        self.rules: List[RiskRule] = []

    async def route_event(self, event: RiskEvent) -> None:
        """
        Route event through system:
        1. Check if account is locked out
        2. If locked and new position opens → close immediately
        3. If not locked → route to all subscribed rules
        """
        account_id = event.data.get('accountId')

        # CHECK LOCKOUT FIRST (critical for RULE-003, RULE-009, RULE-013)
        if self.lockout_manager.is_locked_out(account_id):
            if event.event_type == EventType.POSITION_OPENED:
                # Close immediately (lockout enforcement)
                await self.enforcement.close_position(
                    account_id,
                    event.data.get('contractId')
                )
            return  # Don't process event further

        # Not locked out, route to all rules
        for rule in self.rules:
            if rule.subscribes_to(event.event_type):
                await rule.evaluate(event, self.engine)

    def register_rule(self, rule: RiskRule) -> None:
        """Register rule for event routing."""
        self.rules.append(rule)
```

**Integration Points**:
- **Wired into**: `RiskEngine.evaluate_rules()` - Replace direct rule iteration with `EventRouter.route_event()`
- **Depends on**: `LockoutManager` (implement in Phase 2)
- **Used by**: All 13 rules

**Success Criteria**:
- ✅ Events routed to correct rules based on subscriptions
- ✅ Lockout check prevents rule evaluation when account locked
- ✅ Locked accounts: new positions closed immediately
- ✅ Unit tests: 95%+ coverage
- ✅ Integration tests: lockout enforcement validated

**Effort**: 2 days (1 day implementation, 1 day testing)

---

### 1.2 Event Subscription Registry (1 day)

**Why?**
- Rules need to declare which events they care about
- EventRouter needs efficient lookup of event → rules mapping
- Prevents unnecessary rule evaluations

**Files to Modify**:
```
src/risk_manager/rules/base.py (add subscription methods)
src/risk_manager/core/engine.py (build subscription registry)
tests/unit/test_base_rule.py (test subscriptions)
```

**Key Additions to BaseRule**:
```python
class RiskRule(ABC):
    """Base class for all risk rules."""

    @classmethod
    @abstractmethod
    def subscribed_events(cls) -> List[EventType]:
        """
        Declare which event types this rule cares about.

        Example:
            RULE-001: [POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED]
            RULE-003: [TRADE_EXECUTED]
            RULE-009: [POSITION_OPENED] + timer events
        """
        pass

    def subscribes_to(self, event_type: EventType) -> bool:
        """Check if rule subscribes to this event type."""
        return event_type in self.subscribed_events()
```

**Event Subscription Table** (from SDK_EVENTS_QUICK_REFERENCE.txt):

| Rule ID | Event Types | Frequency |
|---------|-------------|-----------|
| RULE-001 | POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED | High |
| RULE-002 | POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED | High |
| RULE-003 | TRADE_EXECUTED | Medium |
| RULE-004 | POSITION_UPDATED + QUOTE_UPDATE | Very High |
| RULE-005 | POSITION_UPDATED + QUOTE_UPDATE | Very High |
| RULE-006 | TRADE_EXECUTED | Medium |
| RULE-007 | TRADE_EXECUTED (when pnl < 0) | Low |
| RULE-008 | ORDER_PLACED, POSITION_OPENED | Medium |
| RULE-009 | POSITION_OPENED + Timer | Low |
| RULE-010 | ACCOUNT_UPDATED | Low |
| RULE-011 | POSITION_OPENED, POSITION_UPDATED | Medium |
| RULE-012 | POSITION_UPDATED + QUOTE_UPDATE | Very High |
| RULE-013 | TRADE_EXECUTED | Medium |

**Success Criteria**:
- ✅ All rules declare subscribed events
- ✅ EventRouter only calls rules subscribed to event type
- ✅ Performance: O(1) event-to-rules lookup
- ✅ Tests validate subscription filtering

**Effort**: 1 day

---

### 1.3 Enhanced Event Validation (1 day)

**Why?**
- SDK events need validation before rule processing
- Prevent null/malformed data from breaking rules
- Add defensive logging for debugging

**Files to Modify**:
```
src/risk_manager/sdk/event_bridge.py (add validation)
src/risk_manager/core/events.py (add validators)
tests/unit/test_event_validation.py (new)
```

**Key Validations**:
```python
class EventValidator:
    """Validate SDK events before processing."""

    @staticmethod
    def validate_position_event(data: dict) -> bool:
        """Validate POSITION_OPENED/UPDATED/CLOSED events."""
        required = ['accountId', 'contractId', 'size', 'type', 'avgPrice']
        if not all(k in data for k in required):
            logger.error(f"Invalid position event: {data}")
            return False

        # Type validation
        if data['type'] not in [1, 2]:  # 1=Long, 2=Short
            logger.error(f"Invalid position type: {data['type']}")
            return False

        return True

    @staticmethod
    def validate_trade_event(data: dict) -> bool:
        """Validate TRADE_EXECUTED events."""
        required = ['accountId', 'contractId', 'quantity', 'price']
        if not all(k in data for k in required):
            logger.error(f"Invalid trade event: {data}")
            return False

        # NOTE: profitAndLoss can be null for opening trades (half-turn)
        # Don't validate as required

        return True
```

**Integration Points**:
- **Called from**: `EventBridge._on_position_update()`, `_on_trade_update()`
- **Logs to**: `data/logs/risk_manager.log` (checkpoint 6 context)

**Success Criteria**:
- ✅ Invalid events logged and dropped (not passed to rules)
- ✅ All event types validated
- ✅ Graceful handling of null/missing fields
- ✅ Unit tests: edge cases covered

**Effort**: 1 day

---

### 1.4 Enforcement Action Queue (1-2 days)

**Why?**
- Multiple rules may trigger simultaneously (e.g., RULE-001 + RULE-003)
- Prevent race conditions when closing positions
- Ensure atomicity of enforcement actions

**Files to Create**:
```
src/risk_manager/core/action_queue.py (200 lines)
tests/unit/test_action_queue.py (150 lines)
```

**Key Classes**:
```python
class EnforcementAction(Enum):
    """All possible enforcement actions."""
    CLOSE_POSITION = "close_position"
    CLOSE_ALL_POSITIONS = "close_all_positions"
    CANCEL_ALL_ORDERS = "cancel_all_orders"
    SET_LOCKOUT = "set_lockout"
    START_TIMER = "start_timer"
    MODIFY_STOP_LOSS = "modify_stop_loss"


class ActionQueue:
    """
    Queue enforcement actions to prevent race conditions.

    Example:
        RULE-001 fires: "Close 1 MNQ contract (reduce to limit)"
        RULE-003 fires: "Close all positions (daily loss limit)"

        Without queue: Both try to close positions simultaneously → race condition
        With queue: RULE-003 runs first (higher priority), RULE-001 becomes no-op
    """

    def __init__(self):
        self.queue: asyncio.Queue[EnforcementAction] = asyncio.Queue()
        self.processing = False

    async def enqueue(self, action: EnforcementAction, priority: int = 5) -> None:
        """
        Add action to queue with priority.

        Priority levels:
        - 1: CRITICAL (RULE-003, RULE-009 hard lockouts)
        - 3: HIGH (RULE-006 cooldowns)
        - 5: MEDIUM (RULE-001, RULE-002 position limits)
        - 7: LOW (RULE-012 automation)
        """
        await self.queue.put((priority, action))

    async def process(self) -> None:
        """Process actions sequentially (prevent race conditions)."""
        while not self.queue.empty():
            priority, action = await self.queue.get()

            try:
                await self._execute_action(action)
            except Exception as e:
                logger.error(f"Action failed: {action}, error: {e}")
            finally:
                self.queue.task_done()

    async def _execute_action(self, action: EnforcementAction) -> None:
        """Execute single enforcement action."""
        # Checkpoint 8 logging
        sdk_logger.warning(f"⚠️ Enforcement triggered: {action.action_type}")

        if action.action_type == EnforcementAction.CLOSE_ALL_POSITIONS:
            await self.trading_integration.flatten_all()
        elif action.action_type == EnforcementAction.CLOSE_POSITION:
            await self.trading_integration.close_position(
                action.account_id,
                action.contract_id
            )
        # ... etc
```

**Integration Points**:
- **Wired into**: `RiskEngine._handle_violation()` - Replace direct enforcement with queue
- **Used by**: All rules that trigger enforcement

**Success Criteria**:
- ✅ Actions processed sequentially (no race conditions)
- ✅ Priority-based execution (hard lockouts before position limits)
- ✅ Idempotency (duplicate actions handled gracefully)
- ✅ Error handling (one action failure doesn't crash queue)
- ✅ Integration tests: simultaneous rule violations handled correctly

**Effort**: 1-2 days

---

### 1.5 Phase 1 Testing & Integration (1 day)

**Goal**: Validate Phase 1 components work together

**Test Scenarios**:
1. **Event Flow Test**:
   - SDK event → EventBridge → EventRouter → Rule → ActionQueue → Enforcement
   - Validate all checkpoints log correctly

2. **Lockout Enforcement Test**:
   - Set lockout (simulate RULE-003 breach)
   - New position opens → EventRouter closes it immediately
   - Event not passed to rules

3. **Action Queue Race Condition Test**:
   - Trigger RULE-001 and RULE-003 simultaneously
   - Validate RULE-003 (higher priority) runs first
   - Validate RULE-001 becomes no-op (positions already closed)

4. **Performance Test**:
   - 100 events/second through EventRouter
   - Validate subscription filtering works (O(1) lookup)
   - No memory leaks

**Files to Create**:
```
tests/integration/test_phase1_integration.py (300 lines)
tests/performance/test_event_throughput.py (150 lines)
```

**Success Criteria**:
- ✅ All Phase 1 components integrated
- ✅ Event flow validated end-to-end
- ✅ Lockout enforcement working
- ✅ Action queue preventing race conditions
- ✅ Performance targets met (100 events/sec)

**Effort**: 1 day

---

## Phase 2: State Management Modules
**Duration**: 4-6 days
**Goal**: Implement 3 missing state managers (MOD-002, MOD-003, MOD-004)

### 2.1 MOD-002: Lockout Manager (2 days)

**Why Critical?**
- Blocks 5 rules (38%): RULE-003, RULE-009, RULE-010, RULE-011, RULE-013
- Required for Event Router (Phase 1)
- Core enforcement mechanism for hard lockouts

**Files to Create**:
```
src/risk_manager/state/lockout_manager.py (250 lines)
tests/unit/test_lockout_manager.py (200 lines)
tests/integration/test_lockout_persistence.py (150 lines)
```

**Key Classes**:
```python
class LockoutType(Enum):
    """Types of lockouts."""
    HARD = "hard"           # Close all + lockout (RULE-003, RULE-009, RULE-013)
    SYMBOL = "symbol"       # Lock specific symbol only (RULE-011)
    TIMER = "timer"         # Temporary cooldown (RULE-006, RULE-007)


class Lockout:
    """Represents a single lockout."""
    account_id: str
    rule_id: str
    lockout_type: LockoutType
    reason: str
    locked_at: datetime
    expires_at: Optional[datetime]  # None = permanent until API unlock
    symbol: Optional[str]  # For symbol-specific lockouts


class LockoutManager:
    """
    Manages trading lockouts across all rules.

    Lockout Types:
    - HARD: Account-wide, timer-based unlock (RULE-003, RULE-009, RULE-013)
    - SYMBOL: Symbol-specific, permanent (RULE-011)
    - TIMER: Account-wide, timer-based unlock (RULE-006, RULE-007)
    """

    def __init__(self, db: Database):
        self.db = db
        self._init_table()

    def _init_table(self) -> None:
        """Create lockouts table if not exists."""
        self.db.execute_write('''
            CREATE TABLE IF NOT EXISTS lockouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                lockout_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                locked_at DATETIME NOT NULL,
                expires_at DATETIME,
                symbol TEXT,
                UNIQUE(account_id, rule_id, symbol)
            )
        ''')

    def is_locked_out(self, account_id: str, symbol: Optional[str] = None) -> bool:
        """
        Check if account (or symbol) is locked out.

        Logic:
        1. Check account-wide lockouts (HARD or TIMER)
        2. If symbol provided, check symbol-specific lockouts
        3. Auto-clear expired lockouts
        """
        # Check account-wide lockouts
        row = self.db.execute_one('''
            SELECT * FROM lockouts
            WHERE account_id = ? AND symbol IS NULL
            ORDER BY locked_at DESC LIMIT 1
        ''', (account_id,))

        if row:
            # Check if expired
            if row['expires_at']:
                expires = datetime.fromisoformat(row['expires_at'])
                if datetime.now() >= expires:
                    self.clear_lockout(account_id, row['rule_id'])
                else:
                    return True  # Still locked
            else:
                return True  # Permanent lockout (until API unlock)

        # Check symbol-specific lockout
        if symbol:
            row = self.db.execute_one('''
                SELECT * FROM lockouts
                WHERE account_id = ? AND symbol = ?
            ''', (account_id, symbol))

            if row:
                return True

        return False

    def set_lockout(
        self,
        account_id: str,
        rule_id: str,
        lockout_type: LockoutType,
        reason: str,
        expires_at: Optional[datetime] = None,
        symbol: Optional[str] = None
    ) -> None:
        """
        Set lockout for account or symbol.

        Examples:
            # RULE-003 (Daily Realized Loss)
            set_lockout(
                account_id="123",
                rule_id="RULE-003",
                lockout_type=LockoutType.HARD,
                reason="Daily loss limit: -$550 / -$500",
                expires_at=datetime(2025, 10, 28, 17, 0)  # 5 PM tomorrow
            )

            # RULE-011 (Symbol Blocks)
            set_lockout(
                account_id="123",
                rule_id="RULE-011",
                lockout_type=LockoutType.SYMBOL,
                reason="RTY blocked by admin",
                symbol="RTY"
            )
        """
        self.db.execute_write('''
            INSERT OR REPLACE INTO lockouts
            (account_id, rule_id, lockout_type, reason, locked_at, expires_at, symbol)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            account_id,
            rule_id,
            lockout_type.value,
            reason,
            datetime.now().isoformat(),
            expires_at.isoformat() if expires_at else None,
            symbol
        ))

        logger.critical(
            f"LOCKOUT SET: Account {account_id}, Rule {rule_id}, "
            f"Type: {lockout_type.value}, Expires: {expires_at}"
        )

    def clear_lockout(self, account_id: str, rule_id: str, symbol: Optional[str] = None) -> None:
        """Clear lockout for account/rule/symbol."""
        if symbol:
            self.db.execute_write('''
                DELETE FROM lockouts
                WHERE account_id = ? AND rule_id = ? AND symbol = ?
            ''', (account_id, rule_id, symbol))
        else:
            self.db.execute_write('''
                DELETE FROM lockouts
                WHERE account_id = ? AND rule_id = ? AND symbol IS NULL
            ''', (account_id, rule_id))

        logger.info(f"LOCKOUT CLEARED: Account {account_id}, Rule {rule_id}")

    def get_lockout_status(self, account_id: str) -> Dict[str, Any]:
        """Get current lockout status for account (for CLI display)."""
        rows = self.db.execute('''
            SELECT * FROM lockouts
            WHERE account_id = ?
            ORDER BY locked_at DESC
        ''', (account_id,))

        return {
            'locked': len(rows) > 0,
            'lockouts': [dict(r) for r in rows]
        }
```

**Integration Points**:
- **Used by**: EventRouter (lockout check), RULE-003/009/010/011/013 (set lockout)
- **Depends on**: Database (already exists)

**Success Criteria**:
- ✅ Account-wide lockouts work (HARD, TIMER types)
- ✅ Symbol-specific lockouts work (SYMBOL type)
- ✅ Expired lockouts auto-cleared
- ✅ Persistence: lockouts survive service restart
- ✅ Unit tests: 95%+ coverage
- ✅ Integration tests: lockout enforcement validated

**Effort**: 2 days (1 day implementation, 1 day testing)

---

### 2.2 MOD-003: Timer Manager (1-2 days)

**Why Critical?**
- Blocks 4 rules (31%): RULE-006, RULE-007, RULE-008
- Required for cooldown enforcement
- Handles countdown timers and auto-unlock

**Files to Create**:
```
src/risk_manager/state/timer_manager.py (200 lines)
tests/unit/test_timer_manager.py (150 lines)
tests/integration/test_timer_expiry.py (100 lines)
```

**Key Classes**:
```python
class Timer:
    """Represents a single countdown timer."""
    account_id: str
    rule_id: str
    reason: str
    started_at: datetime
    duration_seconds: int
    expires_at: datetime
    callback: Optional[Callable]  # Called when timer expires


class TimerManager:
    """
    Manages countdown timers for cooldown rules.

    Used by:
    - RULE-006: Trade frequency cooldown (1 min to 1 hour)
    - RULE-007: Cooldown after loss (5 min to 30 min)
    - RULE-008: Stop-loss grace period (10 seconds)
    """

    def __init__(self, db: Database, lockout_manager: LockoutManager):
        self.db = db
        self.lockout_manager = lockout_manager
        self.active_timers: Dict[str, Timer] = {}
        self._init_table()

    def _init_table(self) -> None:
        """Create timers table if not exists."""
        self.db.execute_write('''
            CREATE TABLE IF NOT EXISTS timers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                started_at DATETIME NOT NULL,
                duration_seconds INTEGER NOT NULL,
                expires_at DATETIME NOT NULL,
                UNIQUE(account_id, rule_id)
            )
        ''')

    async def start_timer(
        self,
        account_id: str,
        rule_id: str,
        duration_seconds: int,
        reason: str,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Start countdown timer.

        Examples:
            # RULE-006: Trade frequency limit (1 min cooldown)
            await timer_manager.start_timer(
                account_id="123",
                rule_id="RULE-006",
                duration_seconds=60,
                reason="Trade frequency: 3/3 trades in 1 min"
            )

            # RULE-007: Cooldown after -$200 loss (15 min)
            await timer_manager.start_timer(
                account_id="123",
                rule_id="RULE-007",
                duration_seconds=900,
                reason="Loss cooldown: -$200"
            )
        """
        started_at = datetime.now()
        expires_at = started_at + timedelta(seconds=duration_seconds)

        # Persist to database
        self.db.execute_write('''
            INSERT OR REPLACE INTO timers
            (account_id, rule_id, reason, started_at, duration_seconds, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            account_id,
            rule_id,
            reason,
            started_at.isoformat(),
            duration_seconds,
            expires_at.isoformat()
        ))

        # Create in-memory timer
        timer = Timer(
            account_id=account_id,
            rule_id=rule_id,
            reason=reason,
            started_at=started_at,
            duration_seconds=duration_seconds,
            expires_at=expires_at,
            callback=callback
        )

        self.active_timers[f"{account_id}:{rule_id}"] = timer

        # Set lockout during timer
        self.lockout_manager.set_lockout(
            account_id=account_id,
            rule_id=rule_id,
            lockout_type=LockoutType.TIMER,
            reason=reason,
            expires_at=expires_at
        )

        # Schedule auto-unlock
        asyncio.create_task(self._wait_for_expiry(timer))

        logger.info(
            f"TIMER STARTED: Account {account_id}, Rule {rule_id}, "
            f"Duration: {duration_seconds}s, Expires: {expires_at}"
        )

    async def _wait_for_expiry(self, timer: Timer) -> None:
        """Wait for timer to expire, then unlock."""
        remaining = (timer.expires_at - datetime.now()).total_seconds()
        if remaining > 0:
            await asyncio.sleep(remaining)

        # Timer expired
        await self._handle_expiry(timer)

    async def _handle_expiry(self, timer: Timer) -> None:
        """Handle timer expiry."""
        # Clear lockout
        self.lockout_manager.clear_lockout(timer.account_id, timer.rule_id)

        # Remove from active timers
        key = f"{timer.account_id}:{timer.rule_id}"
        if key in self.active_timers:
            del self.active_timers[key]

        # Remove from database
        self.db.execute_write('''
            DELETE FROM timers
            WHERE account_id = ? AND rule_id = ?
        ''', (timer.account_id, timer.rule_id))

        # Call callback if provided
        if timer.callback:
            await timer.callback(timer)

        logger.info(
            f"TIMER EXPIRED: Account {timer.account_id}, Rule {timer.rule_id}, "
            f"Auto-unlocked"
        )

    def get_remaining_time(self, account_id: str, rule_id: str) -> Optional[int]:
        """Get remaining seconds on timer (for CLI display)."""
        key = f"{account_id}:{rule_id}"
        if key in self.active_timers:
            timer = self.active_timers[key]
            remaining = (timer.expires_at - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return None

    async def load_timers_from_db(self) -> None:
        """Load active timers from database (crash recovery)."""
        rows = self.db.execute('SELECT * FROM timers')

        for row in rows:
            expires_at = datetime.fromisoformat(row['expires_at'])

            # Skip expired timers
            if datetime.now() >= expires_at:
                self.db.execute_write('''
                    DELETE FROM timers WHERE id = ?
                ''', (row['id'],))
                continue

            # Recreate timer
            timer = Timer(
                account_id=row['account_id'],
                rule_id=row['rule_id'],
                reason=row['reason'],
                started_at=datetime.fromisoformat(row['started_at']),
                duration_seconds=row['duration_seconds'],
                expires_at=expires_at,
                callback=None  # No callback on recovery
            )

            self.active_timers[f"{timer.account_id}:{timer.rule_id}"] = timer

            # Schedule auto-unlock
            asyncio.create_task(self._wait_for_expiry(timer))

        logger.info(f"Loaded {len(self.active_timers)} active timers from database")
```

**Integration Points**:
- **Used by**: RULE-006, RULE-007, RULE-008
- **Depends on**: Database, LockoutManager

**Success Criteria**:
- ✅ Timers start correctly
- ✅ Auto-unlock on expiry
- ✅ Persistence: timers survive service restart
- ✅ Multiple timers per account supported
- ✅ Unit tests: 95%+ coverage
- ✅ Integration tests: timer expiry validated

**Effort**: 1-2 days

---

### 2.3 MOD-004: Reset Scheduler (1-2 days)

**Why Critical?**
- Blocks 3 rules (23%): RULE-003, RULE-009, RULE-013
- Required for daily P&L reset
- Handles timezone-aware scheduled resets

**Files to Create**:
```
src/risk_manager/state/reset_scheduler.py (250 lines)
tests/unit/test_reset_scheduler.py (150 lines)
tests/integration/test_daily_reset.py (100 lines)
```

**Key Classes**:
```python
class ResetSchedule:
    """Represents a scheduled reset."""
    rule_id: str
    reset_time: time  # e.g., 17:00:00
    timezone: str  # e.g., "America/New_York"
    callback: Callable  # Called at reset time


class ResetScheduler:
    """
    Manages scheduled resets for daily/session-based rules.

    Used by:
    - RULE-003: Daily realized loss (reset at 5 PM)
    - RULE-013: Daily realized profit (reset at 5 PM)
    - RULE-009: Session block (reset at session start)
    """

    def __init__(
        self,
        pnl_tracker: PnLTracker,
        lockout_manager: LockoutManager
    ):
        self.pnl_tracker = pnl_tracker
        self.lockout_manager = lockout_manager
        self.schedules: List[ResetSchedule] = []
        self.running = False

    def register_schedule(
        self,
        rule_id: str,
        reset_time: str,  # "HH:MM" format
        timezone: str,
        callback: Callable
    ) -> None:
        """
        Register scheduled reset.

        Examples:
            # RULE-003: Daily loss reset at 5 PM ET
            reset_scheduler.register_schedule(
                rule_id="RULE-003",
                reset_time="17:00",
                timezone="America/New_York",
                callback=self._reset_daily_pnl
            )

            # RULE-009: Session start at 9:30 AM ET
            reset_scheduler.register_schedule(
                rule_id="RULE-009",
                reset_time="09:30",
                timezone="America/New_York",
                callback=self._unlock_for_session
            )
        """
        hour, minute = map(int, reset_time.split(':'))
        schedule = ResetSchedule(
            rule_id=rule_id,
            reset_time=time(hour, minute),
            timezone=timezone,
            callback=callback
        )
        self.schedules.append(schedule)

        logger.info(
            f"SCHEDULE REGISTERED: Rule {rule_id}, "
            f"Reset at {reset_time} {timezone}"
        )

    async def start(self) -> None:
        """Start scheduler background task."""
        self.running = True
        asyncio.create_task(self._scheduler_loop())
        logger.info("Reset scheduler started")

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop (checks every minute)."""
        while self.running:
            await asyncio.sleep(60)  # Check every minute

            now = datetime.now()

            for schedule in self.schedules:
                # Convert to schedule timezone
                tz = pytz.timezone(schedule.timezone)
                local_now = now.astimezone(tz)

                # Check if reset time reached
                if (local_now.hour == schedule.reset_time.hour and
                    local_now.minute == schedule.reset_time.minute):

                    logger.info(
                        f"RESET TIME REACHED: Rule {schedule.rule_id} "
                        f"at {schedule.reset_time} {schedule.timezone}"
                    )

                    # Execute callback
                    try:
                        await schedule.callback(schedule)
                    except Exception as e:
                        logger.error(
                            f"Reset callback failed: {schedule.rule_id}, "
                            f"error: {e}"
                        )

    async def _reset_daily_pnl(self, schedule: ResetSchedule) -> None:
        """
        Reset daily P&L for all accounts (RULE-003, RULE-013).

        Called at reset_time (e.g., 5 PM ET).
        """
        # Reset P&L for all accounts
        all_pnls = self.pnl_tracker.get_all_daily_pnls(date.today())

        for account_id in all_pnls.keys():
            # Reset P&L to $0
            self.pnl_tracker.reset_daily_pnl(account_id, date.today())

            # Clear lockouts for daily P&L rules
            self.lockout_manager.clear_lockout(account_id, "RULE-003")
            self.lockout_manager.clear_lockout(account_id, "RULE-013")

        logger.info(
            f"Daily P&L reset complete: {len(all_pnls)} accounts reset"
        )

    async def _unlock_for_session(self, schedule: ResetSchedule) -> None:
        """
        Unlock accounts for session start (RULE-009).

        Called at session_start (e.g., 9:30 AM ET).
        """
        # Get all accounts locked by RULE-009
        # Clear lockouts to allow trading
        # (Implementation depends on how we track locked accounts)

        logger.info("Session start: RULE-009 lockouts cleared")

    def calculate_next_reset_time(
        self,
        reset_time: str,
        timezone: str
    ) -> datetime:
        """
        Calculate next occurrence of reset time.

        Examples:
            # Current time: 2 PM ET
            # Reset time: 5 PM ET
            # Returns: Today 5 PM ET

            # Current time: 6 PM ET
            # Reset time: 5 PM ET
            # Returns: Tomorrow 5 PM ET
        """
        hour, minute = map(int, reset_time.split(':'))
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        # Try today first
        reset_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if now >= reset_today:
            # Already passed today, use tomorrow
            return reset_today + timedelta(days=1)
        else:
            return reset_today
```

**Integration Points**:
- **Used by**: RULE-003, RULE-009, RULE-013
- **Depends on**: PnLTracker, LockoutManager

**Success Criteria**:
- ✅ Daily resets execute at configured time
- ✅ Timezone-aware scheduling
- ✅ Multiple schedules supported
- ✅ Callbacks executed correctly
- ✅ Service restart: schedules restored
- ✅ Unit tests: 95%+ coverage
- ✅ Integration tests: reset execution validated

**Effort**: 1-2 days

---

### 2.4 Phase 2 Testing & Integration (1 day)

**Goal**: Validate all 3 state managers work together

**Test Scenarios**:
1. **Lockout → Timer → Reset Flow**:
   - RULE-003 breach → Set lockout (LockoutManager)
   - Lockout expires at reset_time (ResetScheduler)
   - P&L reset to $0, lockout cleared

2. **Multiple Timers Test**:
   - RULE-006 and RULE-007 both set timers
   - Validate both count down independently
   - Both auto-unlock at correct times

3. **Crash Recovery Test**:
   - Start service, set lockout + timer
   - Stop service (simulate crash)
   - Restart service
   - Validate lockouts and timers restored from database

4. **Timezone Test**:
   - Configure reset_time in different timezones
   - Validate correct reset time in each zone

**Files to Create**:
```
tests/integration/test_state_managers_integration.py (400 lines)
tests/integration/test_crash_recovery.py (200 lines)
```

**Success Criteria**:
- ✅ All 3 state managers integrated
- ✅ Lockout → Timer → Reset flow working
- ✅ Crash recovery validated
- ✅ Timezone handling correct

**Effort**: 1 day

---

## Phase 3: High-Priority Rules
**Duration**: 6-8 days
**Goal**: Implement critical account protection rules

### 3.1 Complete RULE-003 (1 day)

**Current Status**: 70% complete - needs MOD-002/MOD-004 integration

**Files to Modify**:
```
src/risk_manager/rules/daily_loss.py (add lockout integration)
tests/unit/test_daily_loss.py (expand tests)
tests/integration/test_rule003_lockout.py (new - E2E test)
```

**What's Missing**:
```python
# ADD to daily_loss.py:

async def _enforce_lockout(self, account_id: str, daily_pnl: float) -> None:
    """Enforce hard lockout on daily loss limit breach."""

    # 1. Close all positions
    await self.engine.enforcement.close_all_positions(account_id)

    # 2. Cancel all orders
    await self.engine.enforcement.cancel_all_orders(account_id)

    # 3. Calculate next reset time
    reset_time = self.engine.reset_scheduler.calculate_next_reset_time(
        reset_time=self.config['reset_time'],
        timezone=self.config['timezone']
    )

    # 4. Set timer-based lockout
    await self.engine.lockout_manager.set_lockout(
        account_id=account_id,
        rule_id="RULE-003",
        lockout_type=LockoutType.HARD,
        reason=f"Daily realized loss limit: ${daily_pnl:.2f} / ${self.config['limit']:.2f}",
        expires_at=reset_time
    )

    # 5. Log enforcement (Checkpoint 8)
    sdk_logger.critical(
        f"⚠️ RULE-003 BREACH: Account {account_id} locked until {reset_time}. "
        f"Daily P&L: ${daily_pnl:.2f}, Limit: ${self.config['limit']:.2f}"
    )
```

**Testing**:
- Unit tests: lockout integration
- Integration tests: full enforcement flow
- E2E test: trade execution → P&L update → lockout → reset → unlock

**Success Criteria**:
- ✅ RULE-003 100% complete
- ✅ Lockout enforcement working
- ✅ Daily reset working
- ✅ Timer-based unlock working
- ✅ Tests: 95%+ coverage

**Effort**: 1 day

---

### 3.2 RULE-009: Session Block Outside (3 days)

**Why High Priority?**
- Prevents trading outside session hours (account violation)
- Most complex rule (multiple session types, holidays, timezones)

**Files to Create**:
```
src/risk_manager/rules/session_block.py (400 lines)
config/holidays.yaml (50 lines)
tests/unit/test_session_block.py (300 lines)
tests/integration/test_rule009_session.py (200 lines)
```

**Key Implementation**:
```python
class SessionBlockOutside(RiskRule):
    """
    RULE-009: Block trading outside configured session hours and on holidays.

    Enforcement: HARD LOCKOUT (timer-based unlock at session start)
    """

    @classmethod
    def subscribed_events(cls) -> List[EventType]:
        """Subscribe to position opens (real-time) + timer events."""
        return [EventType.POSITION_OPENED]

    def __init__(self, config: Dict[str, Any], engine: RiskEngine):
        super().__init__(action="close_all_and_lockout")
        self.config = config
        self.engine = engine
        self.holiday_calendar = self._load_holidays()

        # Register session start schedule
        if config.get('global_session', {}).get('enabled'):
            engine.reset_scheduler.register_schedule(
                rule_id="RULE-009",
                reset_time=config['global_session']['start'],
                timezone=config['global_session']['timezone'],
                callback=self._unlock_for_session_start
            )

    def _load_holidays(self) -> List[date]:
        """Load holiday calendar from config/holidays.yaml."""
        with open(self.config['holiday_calendar']) as f:
            data = yaml.safe_load(f)
            return [date.fromisoformat(d) for d in data['holidays']]

    async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> Optional[Dict]:
        """
        Check if position opened outside session hours.

        Logic:
        1. Check if today is holiday → BREACH
        2. Check global session hours → BREACH if outside
        3. Check per-instrument session (if configured)
        """
        account_id = event.data.get('accountId')
        contract_id = event.data.get('contractId')
        symbol = self._extract_symbol(contract_id)

        # 1. Holiday check
        if date.today() in self.holiday_calendar:
            return {
                'rule': 'RULE-009',
                'severity': 'critical',
                'message': f'Trading on holiday: {date.today()}',
                'action': 'close_all_and_lockout',
                'account_id': account_id
            }

        # 2. Global session check
        if self.config.get('global_session', {}).get('enabled'):
            if not self._in_session(self.config['global_session']):
                return {
                    'rule': 'RULE-009',
                    'severity': 'critical',
                    'message': 'Trading outside global session',
                    'action': 'close_all_and_lockout',
                    'account_id': account_id
                }

        # 3. Per-instrument session check
        if self.config.get('per_instrument_sessions', {}).get('enabled'):
            instrument_sessions = self.config['per_instrument_sessions']['sessions']

            if symbol in instrument_sessions:
                if not self._in_session(instrument_sessions[symbol]):
                    return {
                        'rule': 'RULE-009',
                        'severity': 'critical',
                        'message': f'Trading {symbol} outside session',
                        'action': 'close_all_and_lockout',
                        'account_id': account_id
                    }

        return None  # Within session

    def _in_session(self, session: Dict[str, str]) -> bool:
        """Check if current time is within session."""
        tz = pytz.timezone(session['timezone'])
        now = datetime.now(tz)

        start = datetime.strptime(session['start'], '%H:%M').time()
        end = datetime.strptime(session['end'], '%H:%M').time()

        # Handle overnight sessions (e.g., 18:00 → 17:00 next day)
        if start > end:
            return now.time() >= start or now.time() <= end
        else:
            return start <= now.time() <= end

    async def _unlock_for_session_start(self, schedule: ResetSchedule) -> None:
        """Called by ResetScheduler at session start time."""
        # Clear all RULE-009 lockouts
        # (Implementation depends on tracking locked accounts)
        logger.info("Session start: Unlocking all RULE-009 lockouts")
```

**Configuration**:
```yaml
session_block_outside:
  enabled: true

  # Global session (all instruments)
  global_session:
    enabled: true
    start: "09:30"
    end: "16:00"
    timezone: "America/New_York"

  # Per-instrument sessions (override global)
  per_instrument_sessions:
    enabled: true
    sessions:
      ES:
        start: "18:00"  # Sunday 6pm
        end: "17:00"    # Friday 5pm
        timezone: "America/Chicago"
      MNQ:
        start: "18:00"
        end: "17:00"
        timezone: "America/Chicago"

  # Enforcement
  close_positions_at_session_end: true
  lockout_outside_session: true

  # Holidays
  respect_holidays: true
  holiday_calendar: "config/holidays.yaml"
```

**Testing**:
- Unit tests: session detection, holiday check, timezone handling
- Integration tests: session start → unlock, session end → lockout
- E2E test: full day cycle (session start → trading → session end → lockout → next day unlock)

**Success Criteria**:
- ✅ Global session hours enforced
- ✅ Per-instrument sessions enforced
- ✅ Holiday trading blocked
- ✅ Timezone handling correct
- ✅ Session start auto-unlock working
- ✅ Tests: 95%+ coverage

**Effort**: 3 days (most complex rule)

---

### 3.3 RULE-006: Trade Frequency Limit (2 days)

**Why High Priority?**
- Prevents overtrading (common account violation)
- Requires rolling window counting

**Files to Create**:
```
src/risk_manager/rules/trade_frequency.py (300 lines)
tests/unit/test_trade_frequency.py (200 lines)
tests/integration/test_rule006_cooldown.py (150 lines)
```

**Key Implementation**:
```python
class TradeFrequencyLimit(RiskRule):
    """
    RULE-006: Limit trades per time window (minute/hour/session).

    Enforcement: TIMER/COOLDOWN (temporary lockout with countdown)
    """

    @classmethod
    def subscribed_events(cls) -> List[EventType]:
        """Subscribe to trade executions."""
        return [EventType.TRADE_EXECUTED]

    def __init__(self, config: Dict[str, Any], engine: RiskEngine):
        super().__init__(action="start_timer")
        self.config = config
        self.engine = engine
        self.db = engine.db
        self._init_table()

    def _init_table(self) -> None:
        """Create trade_counts table for rolling window."""
        self.db.execute_write('''
            CREATE TABLE IF NOT EXISTS trade_counts (
                account_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                PRIMARY KEY (account_id, timestamp)
            )
        ''')

    async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> Optional[Dict]:
        """
        Count trades in rolling windows (1 min, 1 hour, session).

        Breach levels:
        - per_minute: 60s cooldown
        - per_hour: 1800s cooldown (30 min)
        - per_session: 3600s cooldown (1 hour)
        """
        account_id = event.data.get('accountId')

        # Record this trade
        self._record_trade(account_id)

        # Count trades in windows
        minute_count = self._count_trades_in_window(account_id, 60)
        hour_count = self._count_trades_in_window(account_id, 3600)
        session_count = self._count_trades_since_session_start(account_id)

        # Check limits (highest severity first)
        if session_count >= self.config['limits']['per_session']:
            return {
                'rule': 'RULE-006',
                'severity': 'high',
                'message': f'Session limit: {session_count}/{self.config["limits"]["per_session"]} trades',
                'action': 'start_timer',
                'account_id': account_id,
                'cooldown_seconds': self.config['cooldown_on_breach']['per_session_breach']
            }
        elif hour_count >= self.config['limits']['per_hour']:
            return {
                'rule': 'RULE-006',
                'severity': 'high',
                'message': f'Hourly limit: {hour_count}/{self.config["limits"]["per_hour"]} trades',
                'action': 'start_timer',
                'account_id': account_id,
                'cooldown_seconds': self.config['cooldown_on_breach']['per_hour_breach']
            }
        elif minute_count >= self.config['limits']['per_minute']:
            return {
                'rule': 'RULE-006',
                'severity': 'medium',
                'message': f'Per-minute limit: {minute_count}/{self.config["limits"]["per_minute"]} trades',
                'action': 'start_timer',
                'account_id': account_id,
                'cooldown_seconds': self.config['cooldown_on_breach']['per_minute_breach']
            }

        return None  # Within limits

    def _record_trade(self, account_id: str) -> None:
        """Record trade timestamp."""
        self.db.execute_write('''
            INSERT INTO trade_counts (account_id, timestamp)
            VALUES (?, ?)
        ''', (account_id, datetime.now().isoformat()))

    def _count_trades_in_window(self, account_id: str, window_seconds: int) -> int:
        """Count trades in rolling window."""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)

        rows = self.db.execute('''
            SELECT COUNT(*) as count FROM trade_counts
            WHERE account_id = ? AND timestamp >= ?
        ''', (account_id, cutoff.isoformat()))

        return rows[0]['count'] if rows else 0

    def _count_trades_since_session_start(self, account_id: str) -> int:
        """Count trades since session start (e.g., 9:30 AM today)."""
        # Simplified: count trades today
        # TODO: Integrate with RULE-009 session times

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        rows = self.db.execute('''
            SELECT COUNT(*) as count FROM trade_counts
            WHERE account_id = ? AND timestamp >= ?
        ''', (account_id, today_start.isoformat()))

        return rows[0]['count'] if rows else 0
```

**Integration with TimerManager**:
```python
# In RiskEngine._handle_violation():

if violation['action'] == 'start_timer':
    await self.timer_manager.start_timer(
        account_id=violation['account_id'],
        rule_id=violation['rule'],
        duration_seconds=violation['cooldown_seconds'],
        reason=violation['message']
    )
```

**Testing**:
- Unit tests: trade counting, window calculations
- Integration tests: cooldown timer, auto-unlock
- E2E test: hit limit → cooldown → wait → unlock → trade again

**Success Criteria**:
- ✅ Rolling window counting accurate
- ✅ All 3 window types working (minute, hour, session)
- ✅ Cooldown timers working
- ✅ Auto-unlock after cooldown
- ✅ Tests: 95%+ coverage

**Effort**: 2 days

---

## Phase 4: Medium-Priority Rules
**Duration**: 4-5 days
**Goal**: Complete timer/cooldown and symbol-based rules

### 4.1 RULE-007: Cooldown After Loss (1 day)

**Files to Create**:
```
src/risk_manager/rules/cooldown_after_loss.py (200 lines)
tests/unit/test_cooldown_after_loss.py (150 lines)
```

**Key Implementation**:
```python
class CooldownAfterLoss(RiskRule):
    """
    RULE-007: Force break after losing trades to prevent revenge trading.

    Enforcement: TIMER/COOLDOWN (tiered cooldown based on loss amount)
    """

    @classmethod
    def subscribed_events(cls) -> List[EventType]:
        return [EventType.TRADE_EXECUTED]

    async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> Optional[Dict]:
        """Trigger tiered cooldown based on loss amount."""
        pnl = event.data.get('profitAndLoss')

        # Only trigger on losing trades
        if pnl is None or pnl >= 0:
            return None

        # Find matching threshold (highest first)
        for threshold in sorted(
            self.config['loss_thresholds'],
            key=lambda t: t['loss_amount']
        ):
            if pnl <= threshold['loss_amount']:
                return {
                    'rule': 'RULE-007',
                    'severity': 'medium',
                    'message': f'Loss cooldown: ${pnl:.2f} loss',
                    'action': 'start_timer',
                    'account_id': event.data.get('accountId'),
                    'cooldown_seconds': threshold['cooldown_duration']
                }

        return None
```

**Success Criteria**: ✅ Tiered cooldowns, ✅ Timer integration, ✅ Tests 95%+

**Effort**: 1 day

---

### 4.2 RULE-008: No Stop-Loss Grace (2 days)

**Files to Create**:
```
src/risk_manager/rules/no_stop_loss_grace.py (250 lines)
tests/unit/test_no_stop_loss_grace.py (200 lines)
```

**Key Implementation**:
```python
class NoStopLossGrace(RiskRule):
    """
    RULE-008: Enforce stop-loss placement within grace period.

    Enforcement: TRADE-BY-TRADE (close that position if no SL found)
    """

    @classmethod
    def subscribed_events(cls) -> List[EventType]:
        return [EventType.POSITION_OPENED, EventType.ORDER_PLACED]

    def __init__(self, config: Dict[str, Any], engine: RiskEngine):
        super().__init__(action="close_position")
        self.config = config
        self.grace_timers: Dict[str, asyncio.Task] = {}  # position → timer task

    async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> Optional[Dict]:
        """
        Logic:
        1. POSITION_OPENED → Start grace period timer
        2. ORDER_PLACED (type=STOP) → Cancel timer (SL placed)
        3. Timer expires → Check for stop loss, close if missing
        """
        if event.event_type == EventType.POSITION_OPENED:
            return await self._handle_position_opened(event, engine)
        elif event.event_type == EventType.ORDER_PLACED:
            return await self._handle_order_placed(event, engine)

        return None

    async def _handle_position_opened(self, event: RiskEvent, engine: RiskEngine) -> None:
        """Start grace period timer for new position."""
        account_id = event.data.get('accountId')
        contract_id = event.data.get('contractId')
        position_key = f"{account_id}:{contract_id}"

        # Start grace period timer
        timer_task = asyncio.create_task(
            self._grace_period_timer(account_id, contract_id, engine)
        )

        self.grace_timers[position_key] = timer_task

        logger.info(
            f"RULE-008: Grace period started for {contract_id} "
            f"({self.config['grace_period_seconds']}s)"
        )

    async def _grace_period_timer(
        self,
        account_id: str,
        contract_id: str,
        engine: RiskEngine
    ) -> None:
        """Wait for grace period, then check for stop loss."""
        await asyncio.sleep(self.config['grace_period_seconds'])

        # Check if stop loss exists
        has_stop_loss = await self._check_for_stop_loss(account_id, contract_id, engine)

        if not has_stop_loss:
            # No stop loss found - close position
            logger.warning(
                f"RULE-008 BREACH: No stop loss placed within grace period. "
                f"Closing {contract_id}"
            )

            await engine.enforcement.close_position(account_id, contract_id)

    async def _handle_order_placed(self, event: RiskEvent, engine: RiskEngine) -> None:
        """Check if stop-loss order placed - cancel timer if so."""
        order_type = event.data.get('order', {}).get('type')

        if order_type == 3:  # STOP order
            account_id = event.data.get('accountId')
            contract_id = event.data.get('order', {}).get('contractId')
            position_key = f"{account_id}:{contract_id}"

            # Cancel grace period timer (SL placed in time)
            if position_key in self.grace_timers:
                self.grace_timers[position_key].cancel()
                del self.grace_timers[position_key]

                logger.info(
                    f"RULE-008: Stop loss placed for {contract_id} "
                    f"(grace period satisfied)"
                )

    async def _check_for_stop_loss(
        self,
        account_id: str,
        contract_id: str,
        engine: RiskEngine
    ) -> bool:
        """Check if stop-loss order exists for position."""
        # Query SDK for orders
        orders = await engine.trading_integration.get_orders(contract_id)

        for order in orders:
            if order.get('type') == 3:  # STOP order
                return True

        return False
```

**Success Criteria**: ✅ Grace period timer, ✅ SL detection, ✅ Tests 95%+

**Effort**: 2 days

---

### 4.3 RULE-010: Auth Loss Guard (1 day)

**Files to Create**:
```
src/risk_manager/rules/auth_loss_guard.py (150 lines)
tests/unit/test_auth_loss_guard.py (100 lines)
```

**Key Implementation**:
```python
class AuthLossGuard(RiskRule):
    """
    RULE-010: Monitor TopstepX canTrade status.

    Enforcement: HARD LOCKOUT (until API sends canTrade: true)
    """

    @classmethod
    def subscribed_events(cls) -> List[EventType]:
        return [EventType.ACCOUNT_UPDATED]

    async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> Optional[Dict]:
        """Check canTrade field in account updates."""
        can_trade = event.data.get('canTrade')
        account_id = event.data.get('accountId')

        if can_trade is False:
            return {
                'rule': 'RULE-010',
                'severity': 'critical',
                'message': 'TopstepX API: canTrade = false',
                'action': 'close_all_and_lockout',
                'account_id': account_id,
                'lockout_until': None  # Permanent until API unlock
            }
        elif can_trade is True:
            # Clear lockout if previously set
            engine.lockout_manager.clear_lockout(account_id, "RULE-010")
            logger.info(f"RULE-010: canTrade restored for account {account_id}")

        return None
```

**Success Criteria**: ✅ canTrade monitoring, ✅ Auto-lock/unlock, ✅ Tests 95%+

**Effort**: 1 day

---

### 4.4 RULE-011: Symbol Blocks (1 day) & RULE-013: Daily Realized Profit (1 day)

**Quick implementations** (straightforward, similar to existing rules)

**Total Effort Phase 4**: 4-5 days

---

## Phase 5: Market Data + Unrealized PnL
**Duration**: 5-7 days
**Goal**: Enable unrealized P&L rules (RULE-004, RULE-005, RULE-012)

### 5.1 Market Data Feed Integration (3 days)

**Why Last?**
- Blocks 3 rules (23%): RULE-004, RULE-005, RULE-012
- Most complex: requires high-frequency quote processing

**Files to Create**:
```
src/risk_manager/sdk/market_data_feed.py (400 lines)
src/risk_manager/state/unrealized_calculator.py (250 lines)
tests/unit/test_market_data_feed.py (200 lines)
tests/integration/test_market_data_integration.py (150 lines)
```

**Key Implementation**:
```python
class MarketDataFeed:
    """
    Subscribe to real-time market data (quote updates) for unrealized P&L calculation.

    Used by: RULE-004, RULE-005, RULE-012
    """

    def __init__(self, trading_integration: TradingIntegration, event_bus: EventBus):
        self.trading_integration = trading_integration
        self.event_bus = event_bus
        self.subscribed_symbols: Set[str] = set()
        self.current_prices: Dict[str, float] = {}  # symbol → last price

    async def subscribe(self, symbol: str) -> None:
        """Subscribe to market data for symbol."""
        if symbol in self.subscribed_symbols:
            return

        # Subscribe to SDK quote updates
        await self.trading_integration.suite.subscribe_market_data(symbol)

        # Register callback for quote updates
        await self.trading_integration.suite.realtime.add_callback(
            "quote_update",
            lambda data: self._on_quote_update(symbol, data)
        )

        self.subscribed_symbols.add(symbol)
        logger.info(f"Subscribed to market data: {symbol}")

    async def _on_quote_update(self, symbol: str, data: Any) -> None:
        """
        Handle quote update from SDK.

        Data format:
        {
            'last': 25935.75,
            'bid': 25935.50,
            'ask': 25936.00,
            'volume': 12345
        }
        """
        last_price = data.get('last')

        if last_price:
            self.current_prices[symbol] = last_price

            # Publish QUOTE_UPDATE event to rules
            await self.event_bus.publish(RiskEvent(
                event_type=EventType.QUOTE_UPDATE,
                timestamp=datetime.now(),
                data={
                    'symbol': symbol,
                    'last': last_price,
                    'bid': data.get('bid'),
                    'ask': data.get('ask')
                }
            ))

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get most recent price for symbol."""
        return self.current_prices.get(symbol)


class UnrealizedPnLCalculator:
    """Calculate unrealized P&L for positions."""

    def __init__(self, tick_values: Dict[str, float], tick_sizes: Dict[str, float]):
        self.tick_values = tick_values
        self.tick_sizes = tick_sizes

    def calculate(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        position_size: int,
        position_type: int  # 1=Long, 2=Short
    ) -> float:
        """
        Calculate unrealized P&L.

        Formula:
        - Long: (current_price - entry_price) / tick_size * position_size * tick_value
        - Short: (entry_price - current_price) / tick_size * position_size * tick_value
        """
        tick_value = self.tick_values.get(symbol, 1.0)
        tick_size = self.tick_sizes.get(symbol, 0.01)

        if position_type == 1:  # Long
            price_diff = current_price - entry_price
        elif position_type == 2:  # Short
            price_diff = entry_price - current_price
        else:
            raise ValueError(f"Invalid position type: {position_type}")

        ticks = price_diff / tick_size
        unrealized_pnl = ticks * position_size * tick_value

        return unrealized_pnl
```

**Success Criteria**:
- ✅ Real-time quote subscriptions working
- ✅ QUOTE_UPDATE events published
- ✅ Unrealized P&L calculations accurate
- ✅ High-frequency handling (100+ quotes/sec)
- ✅ Tests: 95%+ coverage

**Effort**: 3 days

---

### 5.2 RULE-004 & RULE-005 (2-3 days)

**Implementation**:
```python
class DailyUnrealizedLoss(RiskRule):
    """
    RULE-004: Enforce unrealized loss limit on individual positions.

    Enforcement: TRADE-BY-TRADE (close that position only)
    """

    @classmethod
    def subscribed_events(cls) -> List[EventType]:
        return [EventType.POSITION_UPDATED, EventType.QUOTE_UPDATE]

    async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> Optional[Dict]:
        """Calculate unrealized P&L on quote updates."""
        if event.event_type == EventType.QUOTE_UPDATE:
            return await self._check_all_positions(event, engine)

        return None

    async def _check_all_positions(self, event: RiskEvent, engine: RiskEngine) -> Optional[Dict]:
        """Check unrealized P&L for all positions in this symbol."""
        symbol = event.data.get('symbol')
        current_price = event.data.get('last')

        # Get all positions in this symbol
        positions = engine.get_positions_by_symbol(symbol)

        for position in positions:
            unrealized_pnl = engine.unrealized_calculator.calculate(
                symbol=symbol,
                entry_price=position['avgPrice'],
                current_price=current_price,
                position_size=position['size'],
                position_type=position['type']
            )

            # Check if breach
            if unrealized_pnl <= self.config['limit']:
                return {
                    'rule': 'RULE-004',
                    'severity': 'high',
                    'message': f'Unrealized loss limit: ${unrealized_pnl:.2f} / ${self.config["limit"]:.2f}',
                    'action': 'close_position',
                    'account_id': position['accountId'],
                    'contract_id': position['contractId']
                }

        return None
```

**Success Criteria**:
- ✅ Real-time unrealized P&L tracking
- ✅ Trade-by-trade enforcement (close that position only)
- ✅ Accurate calculations
- ✅ Tests: 95%+ coverage

**Effort**: 2-3 days (2 rules, shared infrastructure)

---

### 5.3 RULE-012: Trade Management (1-2 days)

**Simple implementation** (automation, not enforcement)

**Effort**: 1-2 days

---

## Phase 6: Production Polish
**Duration**: 3-4 days
**Goal**: Production readiness

### 6.1 Comprehensive Testing (2 days)

**Test Suites**:
1. **Unit Tests**: All 13 rules + all modules
2. **Integration Tests**: Event flow, SDK integration, state persistence
3. **E2E Tests**: Full scenarios (day cycle, lockout → reset, etc.)
4. **Runtime Tests**: Smoke, soak, trace (from Runtime Reliability Pack)
5. **Performance Tests**: 100 events/sec, memory leaks, latency

**Target Coverage**: 95%+

**Effort**: 2 days

---

### 6.2 Documentation & Deployment (1 day)

**Deliverables**:
- Update `docs/current/PROJECT_STATUS.md` (100% complete)
- Create `docs/OPERATOR_RUNBOOK.md` (troubleshooting guide)
- Update `README.md` with new rule status
- Create deployment checklist

**Effort**: 1 day

---

### 6.3 Production Monitoring (1 day)

**Add**:
- Prometheus metrics for each rule
- Grafana dashboards
- Alerting rules

**Effort**: 1 day

---

## Dependency Graph

```
LEGEND:
  [X] = Implemented
  [ ] = Not Implemented
  → = Depends on

PHASE 1: Core Event Infrastructure (5-7 days)
  [ ] Event Router → [X] EventBus
  [ ] Event Subscriptions → [X] BaseRule
  [ ] Event Validation → [X] EventBridge
  [ ] Action Queue → [X] RiskEngine

PHASE 2: State Management (4-6 days)
  [ ] MOD-002 (LockoutManager) → [X] Database
  [ ] MOD-003 (TimerManager) → [X] Database, [ ] MOD-002
  [ ] MOD-004 (ResetScheduler) → [X] PnLTracker, [ ] MOD-002

PHASE 3: High-Priority Rules (6-8 days)
  [ ] RULE-003 (complete) → [X] PnLTracker, [ ] MOD-002, [ ] MOD-004
  [ ] RULE-009 → [ ] MOD-002, [ ] MOD-004
  [ ] RULE-006 → [ ] MOD-003

PHASE 4: Medium-Priority Rules (4-5 days)
  [ ] RULE-007 → [ ] MOD-003
  [ ] RULE-008 → [ ] MOD-003
  [ ] RULE-010 → [ ] MOD-002
  [ ] RULE-011 → [ ] MOD-002
  [ ] RULE-013 → [X] PnLTracker, [ ] MOD-002, [ ] MOD-004

PHASE 5: Market Data + Unrealized PnL (5-7 days)
  [ ] Market Data Feed → [X] TradingIntegration
  [ ] Unrealized Calculator → [ ] Market Data Feed
  [ ] RULE-004 → [ ] Unrealized Calculator
  [ ] RULE-005 → [ ] Unrealized Calculator
  [ ] RULE-012 → [ ] Unrealized Calculator

PHASE 6: Production Polish (3-4 days)
  [ ] Comprehensive Testing → All phases
  [ ] Documentation → All phases
  [ ] Monitoring → All phases

CRITICAL PATH (longest):
  Phase 1 → Phase 2 → Phase 3 (RULE-009) → Phase 5 (Market Data) → Phase 6
  Total: 5 + 4 + 3 + 5 + 3 = 20 days minimum
```

---

## Testing Strategy

### Unit Tests (Per Rule/Module)
- **Coverage Target**: 95%+
- **Focus**: Business logic, edge cases, validation
- **Mock**: SDK, Database, external dependencies
- **Run Time**: <1s per test

### Integration Tests (Per Rule/Module)
- **Coverage Target**: 80%+
- **Focus**: Component integration, SDK interaction, state persistence
- **Real**: Database, EventBus, SDK (test mode)
- **Run Time**: 1-5s per test

### E2E Tests (Per Scenario)
- **Coverage Target**: Critical paths
- **Focus**: Full system, realistic scenarios, enforcement flows
- **Real**: Everything (except live trading)
- **Run Time**: 10-60s per test

### Runtime Tests (Runtime Reliability Pack)
- **Smoke Test**: Boot + first event within 8s (exit code 0/1/2)
- **Soak Test**: 30-60s stability, memory leaks, deadlocks
- **Trace Mode**: Async task dump for debugging

### Performance Tests
- **Throughput**: 100 events/sec sustained
- **Latency**: <10ms event → rule evaluation
- **Memory**: <100MB RSS for 1000 events
- **No Leaks**: Stable memory over 1 hour

---

## Risk Mitigation

### Risk 1: SDK API Changes
**Mitigation**:
- Pin SDK version: `project-x-py==3.5.9`
- Monitor SDK releases for breaking changes
- Comprehensive integration tests catch API breakage

### Risk 2: Market Data Feed Overload
**Mitigation**:
- Throttle quote updates (max 10/sec per symbol)
- Debounce unrealized P&L calculations (100ms)
- Circuit breaker if quote lag >1s

### Risk 3: Database Performance
**Mitigation**:
- SQLite adequate for single-account use
- Add indexes on hot queries
- Consider PostgreSQL for multi-account

### Risk 4: Rule Conflicts
**Mitigation**:
- Action Queue prevents race conditions
- Priority-based execution (hard lockouts first)
- Comprehensive E2E tests validate conflict resolution

### Risk 5: Phase Dependencies
**Mitigation**:
- Each phase has clear success criteria
- Integration tests validate phase boundaries
- Can parallelize some work (e.g., RULE-011 + RULE-013)

---

## Success Metrics

### Phase Completion Criteria
- ✅ All files created/modified as planned
- ✅ Unit tests: 95%+ coverage
- ✅ Integration tests: 80%+ coverage
- ✅ E2E tests: Critical paths covered
- ✅ Runtime smoke test: Exit code 0
- ✅ Code review passed
- ✅ Documentation updated

### Overall Project Success
- ✅ 13/13 rules implemented (100%)
- ✅ All 3 state managers working (MOD-002, MOD-003, MOD-004)
- ✅ Event Router implemented
- ✅ Market Data Feed integrated
- ✅ Action Queue preventing race conditions
- ✅ Test coverage: 95%+ unit, 80%+ integration
- ✅ Runtime validation: All 8 checkpoints logging correctly
- ✅ Performance: 100 events/sec sustained
- ✅ Production deployment: Successful live trading test

---

## Next Steps

### Immediate (Start Phase 1)
1. Create `src/risk_manager/core/event_router.py`
2. Add event subscription methods to `BaseRule`
3. Wire `EventRouter` into `RiskEngine`
4. Write tests for `EventRouter`

### Week 1 Goals
- ✅ Phase 1 complete (Event Infrastructure)
- ✅ Phase 2 started (MOD-002 LockoutManager)

### Week 2 Goals
- ✅ Phase 2 complete (All state managers)
- ✅ Phase 3 started (High-priority rules)

### Week 3 Goals
- ✅ Phase 3 complete (RULE-003, RULE-006, RULE-009)
- ✅ Phase 4 started (Medium-priority rules)

### Week 4 Goals
- ✅ Phase 4 complete (RULE-007, RULE-008, RULE-010, RULE-011, RULE-013)
- ✅ Phase 5 started (Market Data Feed)

### Week 5 Goals
- ✅ Phase 5 complete (RULE-004, RULE-005, RULE-012)
- ✅ Phase 6 started (Testing & Polish)

### Week 6 Goals
- ✅ Phase 6 complete (Production ready)
- ✅ Deployment to production

---

## Appendix A: File Inventory

### New Files to Create (Phase 1-6)
```
src/risk_manager/core/event_router.py (150 lines)
src/risk_manager/core/action_queue.py (200 lines)
src/risk_manager/state/lockout_manager.py (250 lines)
src/risk_manager/state/timer_manager.py (200 lines)
src/risk_manager/state/reset_scheduler.py (250 lines)
src/risk_manager/state/unrealized_calculator.py (250 lines)
src/risk_manager/sdk/market_data_feed.py (400 lines)
src/risk_manager/rules/session_block.py (400 lines)
src/risk_manager/rules/trade_frequency.py (300 lines)
src/risk_manager/rules/cooldown_after_loss.py (200 lines)
src/risk_manager/rules/no_stop_loss_grace.py (250 lines)
src/risk_manager/rules/auth_loss_guard.py (150 lines)
src/risk_manager/rules/symbol_blocks.py (150 lines)
src/risk_manager/rules/daily_profit.py (200 lines)
src/risk_manager/rules/daily_unrealized_loss.py (300 lines)
src/risk_manager/rules/max_unrealized_profit.py (300 lines)
src/risk_manager/rules/trade_management.py (250 lines)
config/holidays.yaml (50 lines)

tests/unit/test_event_router.py (200 lines)
tests/unit/test_action_queue.py (150 lines)
tests/unit/test_lockout_manager.py (200 lines)
tests/unit/test_timer_manager.py (150 lines)
tests/unit/test_reset_scheduler.py (150 lines)
tests/unit/test_market_data_feed.py (200 lines)
tests/unit/test_unrealized_calculator.py (150 lines)
tests/unit/test_session_block.py (300 lines)
tests/unit/test_trade_frequency.py (200 lines)
tests/unit/test_cooldown_after_loss.py (150 lines)
tests/unit/test_no_stop_loss_grace.py (200 lines)
tests/unit/test_auth_loss_guard.py (100 lines)
tests/unit/test_symbol_blocks.py (100 lines)
tests/unit/test_daily_profit.py (150 lines)
tests/unit/test_daily_unrealized_loss.py (200 lines)
tests/unit/test_max_unrealized_profit.py (200 lines)
tests/unit/test_trade_management.py (150 lines)

tests/integration/test_event_router_lockout.py (150 lines)
tests/integration/test_phase1_integration.py (300 lines)
tests/integration/test_lockout_persistence.py (150 lines)
tests/integration/test_timer_expiry.py (100 lines)
tests/integration/test_daily_reset.py (100 lines)
tests/integration/test_state_managers_integration.py (400 lines)
tests/integration/test_crash_recovery.py (200 lines)
tests/integration/test_rule003_lockout.py (150 lines)
tests/integration/test_rule006_cooldown.py (150 lines)
tests/integration/test_rule009_session.py (200 lines)
tests/integration/test_market_data_integration.py (150 lines)

tests/performance/test_event_throughput.py (150 lines)

docs/OPERATOR_RUNBOOK.md (new)
```

**Total New Code**: ~8,300 lines (implementation + tests)

---

## Appendix B: Configuration Templates

### Complete Risk Config (After All Rules Implemented)
```yaml
# risk_config.yaml (all 13 rules configured)

risk_rules:
  # RULE-001: Max Contracts (Trade-by-Trade)
  max_contracts:
    enabled: true
    limit: 5
    count_type: "net"
    reduce_to_limit: true

  # RULE-002: Max Contracts Per Instrument (Trade-by-Trade)
  max_contracts_per_instrument:
    enabled: true
    limits:
      MNQ: 2
      ES: 1
      NQ: 3
    enforcement: "reduce_to_limit"

  # RULE-003: Daily Realized Loss (Hard Lockout)
  daily_realized_loss:
    enabled: true
    limit: -500.0
    reset_time: "17:00"
    timezone: "America/New_York"
    enforcement: "close_all_and_lockout"

  # RULE-004: Daily Unrealized Loss (Trade-by-Trade)
  daily_unrealized_loss:
    enabled: true
    limit: -300.0
    enforcement: "close_position"
    tick_values:
      MNQ: 5.0
      ES: 50.0
      NQ: 20.0
    tick_sizes:
      MNQ: 0.25
      ES: 0.25
      NQ: 0.25

  # RULE-005: Max Unrealized Profit (Trade-by-Trade)
  max_unrealized_profit:
    enabled: true
    target: 1000.0
    enforcement: "close_position"
    tick_values:
      MNQ: 5.0
      ES: 50.0
      NQ: 20.0
    tick_sizes:
      MNQ: 0.25
      ES: 0.25
      NQ: 0.25

  # RULE-006: Trade Frequency Limit (Timer/Cooldown)
  trade_frequency_limit:
    enabled: true
    limits:
      per_minute: 3
      per_hour: 10
      per_session: 50
    cooldown_on_breach:
      per_minute_breach: 60
      per_hour_breach: 1800
      per_session_breach: 3600

  # RULE-007: Cooldown After Loss (Timer/Cooldown)
  cooldown_after_loss:
    enabled: true
    loss_thresholds:
      - loss_amount: -100.0
        cooldown_duration: 300
      - loss_amount: -200.0
        cooldown_duration: 900
      - loss_amount: -300.0
        cooldown_duration: 1800

  # RULE-008: No Stop-Loss Grace (Trade-by-Trade)
  no_stop_loss_grace:
    enabled: true
    grace_period_seconds: 10
    enforcement: "close_position"

  # RULE-009: Session Block Outside (Hard Lockout)
  session_block_outside:
    enabled: true
    global_session:
      enabled: true
      start: "09:30"
      end: "16:00"
      timezone: "America/New_York"
    per_instrument_sessions:
      enabled: true
      sessions:
        ES:
          start: "18:00"
          end: "17:00"
          timezone: "America/Chicago"
    close_positions_at_session_end: true
    lockout_outside_session: true
    respect_holidays: true
    holiday_calendar: "config/holidays.yaml"

  # RULE-010: Auth Loss Guard (Hard Lockout)
  auth_loss_guard:
    enabled: true
    enforcement: "close_all_and_lockout"

  # RULE-011: Symbol Blocks (Trade-by-Trade + Symbol Lockout)
  symbol_blocks:
    enabled: true
    blocked_symbols:
      - "RTY"
      - "BTC"
    enforcement: "close_and_lockout_symbol"

  # RULE-012: Trade Management (Automation)
  trade_management:
    enabled: true
    auto_breakeven:
      enabled: true
      profit_trigger_ticks: 10
    trailing_stop:
      enabled: true
      activation_ticks: 20
      trail_distance_ticks: 10
    tick_sizes:
      MNQ: 0.25
      ES: 0.25
      NQ: 0.25

  # RULE-013: Daily Realized Profit (Hard Lockout)
  daily_realized_profit:
    enabled: true
    target: 1000.0
    reset_time: "17:00"
    timezone: "America/New_York"
    enforcement: "close_all_and_lockout"
    success_message: "Daily profit target reached! Good job! See you tomorrow."
```

---

## Appendix C: Operator Checklist

### Pre-Deployment Checklist
- [ ] All 13 rules configured in `risk_config.yaml`
- [ ] Database schema created (`data/risk_manager.db`)
- [ ] Holiday calendar populated (`config/holidays.yaml`)
- [ ] Unit tests passing (95%+ coverage)
- [ ] Integration tests passing (80%+ coverage)
- [ ] Runtime smoke test passing (exit code 0)
- [ ] Performance tests passing (100 events/sec)
- [ ] 8-checkpoint logging validated (all emojis present)
- [ ] Event Router wired into RiskEngine
- [ ] Action Queue preventing race conditions
- [ ] All 3 state managers working (MOD-002, MOD-003, MOD-004)
- [ ] Market Data Feed subscriptions active
- [ ] TradingIntegration connected to SDK
- [ ] Lockout enforcement validated
- [ ] Timer-based unlocks validated
- [ ] Daily resets validated

### Post-Deployment Monitoring
- [ ] Monitor logs for 8 checkpoints (🚀 ✅ ✅ ✅ ✅ 📨 🔍 ⚠️)
- [ ] Check `test_reports/latest.txt` for test results
- [ ] Monitor action queue length (should be 0 most of the time)
- [ ] Monitor lockout table (should be empty when no violations)
- [ ] Monitor timer table (should have entries during cooldowns)
- [ ] Monitor daily_pnl table (should reset at configured time)
- [ ] Watch for enforcement actions (Checkpoint 8 logs)
- [ ] Validate unrealized P&L calculations (compare with broker)
- [ ] Check market data lag (should be <1s)

---

**END OF MASTER IMPLEMENTATION PLAN**

**Status**: Ready for Phase 1 execution

**Questions?** Refer to:
- `docs/specifications/unified/rules/` (rule specs)
- `SDK_EVENTS_QUICK_REFERENCE.txt` (event mapping)
- `docs/analysis/wave3-audits/06-architecture-consistency-audit.md` (architecture validation)
- `CLAUDE.md` (project entry point)

**Let's build! 🛡️**
