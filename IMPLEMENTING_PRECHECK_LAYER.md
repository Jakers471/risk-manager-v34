# Implementing the PRE-CHECK Layer

**Date**: 2025-10-30
**Purpose**: Add timer/schedule respect to ALL rules via PRE-CHECK layer

---

## 🎯 What's Missing

**Current State** (`engine.py` lines 82-106):
```python
for rule in self.rules:
    try:
        violation = await rule.evaluate(event, self)  # ← NO PRE-CHECK!
        # ... handle violation
```

**Problem**: Rules evaluate EVERY TIME, even when account is locked out!

**Solution**: Add PRE-CHECK layer that blocks rule evaluation when:
- Account is locked out (from ANY rule)
- Outside trading session (RULE-009)
- Cooldown active (RULE-006/007)
- API disabled (RULE-010)

---

## 🔧 Implementation Steps

### Step 1: Wire LockoutManager to Engine

**File**: `src/risk_manager/core/manager.py`

**Current** (lines ~200-250):
```python
# Create shared state managers
pnl_tracker = PnLTracker(db=db)
lockout_manager = LockoutManager(database=db, timer_manager=timer_manager)

# Create engine (WITHOUT lockout_manager!)
engine = RiskEngine(
    config=self.config,
    event_bus=event_bus,
    trading_integration=trading_integration,
)
```

**Change To**:
```python
# Create shared state managers
pnl_tracker = PnLTracker(db=db)
lockout_manager = LockoutManager(database=db, timer_manager=timer_manager)

# Create engine WITH lockout_manager
engine = RiskEngine(
    config=self.config,
    event_bus=event_bus,
    trading_integration=trading_integration,
    lockout_manager=lockout_manager,  # ← ADD THIS
    timer_manager=timer_manager,       # ← ADD THIS
)
```

---

### Step 2: Update Engine Constructor

**File**: `src/risk_manager/core/engine.py`

**Current** (lines 20-33):
```python
def __init__(self, config: RiskConfig, event_bus: EventBus, trading_integration: Any | None = None):
    self.config = config
    self.event_bus = event_bus
    self.trading_integration = trading_integration
    self.rules: list[Any] = []
    self.running = False
```

**Change To**:
```python
def __init__(
    self,
    config: RiskConfig,
    event_bus: EventBus,
    trading_integration: Any | None = None,
    lockout_manager: Any | None = None,  # ← ADD THIS
    timer_manager: Any | None = None,     # ← ADD THIS
):
    self.config = config
    self.event_bus = event_bus
    self.trading_integration = trading_integration
    self.lockout_manager = lockout_manager  # ← ADD THIS
    self.timer_manager = timer_manager       # ← ADD THIS
    self.rules: list[Any] = []
    self.running = False
```

---

### Step 3: Add PRE-CHECK Layer to evaluate_rules()

**File**: `src/risk_manager/core/engine.py`

**Current** (lines 67-111):
```python
async def evaluate_rules(self, event: RiskEvent) -> list[dict[str, Any]]:
    """Evaluate all rules against an event."""

    # Checkpoint 6: Event received
    if len(self.rules) > 0:
        logger.info(f"📨 Event: {event.event_type.value} → evaluating {len(self.rules)} rules")

    violations = []
    rule_results = []

    # ❌ NO PRE-CHECK - Goes straight to rule evaluation!
    for rule in self.rules:
        try:
            violation = await rule.evaluate(event, self)
            # ... handle violation
```

**Change To**:
```python
async def evaluate_rules(self, event: RiskEvent) -> list[dict[str, Any]]:
    """Evaluate all rules against an event."""

    # Checkpoint 6: Event received
    if len(self.rules) > 0:
        logger.info(f"📨 Event: {event.event_type.value} → evaluating {len(self.rules)} rules")

    # ═══════════════════════════════════════════════════════════════
    # ⭐ PRE-CHECK LAYER: Check lockout/timer state before evaluation
    # ═══════════════════════════════════════════════════════════════

    if self.lockout_manager:
        # Get account_id from event
        account_id = event.data.get("account_id")

        if account_id:
            # PRE-CHECK 1: Is account locked out?
            if self.lockout_manager.is_locked_out(account_id):
                lockout_info = self.lockout_manager.get_lockout_info(account_id)

                logger.opt(colors=True).warning(
                    f"<yellow>⚠️  PRE-CHECK FAILED: Account locked out</yellow>\n"
                    f"   Reason: {lockout_info.get('reason', 'Unknown')}\n"
                    f"   Until: {lockout_info.get('until', 'Unknown')}\n"
                    f"   ❌ Skipping rule evaluation for ALL {len(self.rules)} rules"
                )

                # Log each rule being skipped
                for rule in self.rules:
                    rule_name = rule.__class__.__name__.replace('Rule', '')
                    logger.debug(f"   ❌ {rule_name} - NOT EVALUATED (account locked)")

                # Return empty violations list - don't evaluate any rules!
                return []

    # ✅ PRE-CHECK PASSED - Continue with normal rule evaluation
    logger.opt(colors=True).debug(f"<green>✅ PRE-CHECK PASSED: No lockout, evaluating rules</green>")

    violations = []
    rule_results = []

    for rule in self.rules:
        try:
            violation = await rule.evaluate(event, self)
            # ... rest of evaluation logic (unchanged)
```

---

### Step 4: Add Enhanced Logging

**File**: `src/risk_manager/core/engine.py`

**Add this helper method** (after line 213):
```python
def _log_precheck_status(self, event: RiskEvent) -> bool:
    """
    Log PRE-CHECK status and return whether to proceed with rule evaluation.

    Returns:
        True if rules should be evaluated, False if blocked
    """
    if not self.lockout_manager:
        return True  # No lockout manager, allow evaluation

    account_id = event.data.get("account_id")
    if not account_id:
        return True  # No account ID in event, allow evaluation

    # Check lockout state
    if self.lockout_manager.is_locked_out(account_id):
        lockout_info = self.lockout_manager.get_lockout_info(account_id)

        # Determine lockout type for better messaging
        lockout_type = lockout_info.get('type', 'unknown')
        reason = lockout_info.get('reason', 'Unknown reason')

        if lockout_type == 'hard':
            until = lockout_info.get('until', 'Unknown')
            logger.opt(colors=True).warning(
                f"<yellow>🔒 HARD LOCKOUT ACTIVE</yellow>\n"
                f"   Reason: {reason}\n"
                f"   Until: {until}\n"
                f"   ❌ ALL {len(self.rules)} rules BLOCKED"
            )
        elif lockout_type == 'cooldown':
            remaining = lockout_info.get('remaining_seconds', 0)
            logger.opt(colors=True).warning(
                f"<yellow>⏱️  COOLDOWN ACTIVE</yellow>\n"
                f"   Reason: {reason}\n"
                f"   Remaining: {remaining}s\n"
                f"   ❌ ALL {len(self.rules)} rules BLOCKED"
            )
        else:
            logger.opt(colors=True).warning(
                f"<yellow>⚠️  LOCKOUT ACTIVE ({lockout_type})</yellow>\n"
                f"   Reason: {reason}\n"
                f"   ❌ ALL {len(self.rules)} rules BLOCKED"
            )

        return False  # Block rule evaluation

    # No lockout - allow evaluation
    logger.opt(colors=True).debug(
        f"<green>✅ PRE-CHECK PASSED: No lockout active</green>"
    )
    return True
```

---

## 🧪 How to Test It

### Test 1: Trigger RULE-006 Cooldown, Watch ALL Rules Blocked

**Steps**:
1. Start `run_dev.py`
2. Place 4 trades rapidly (exceeds per_minute limit of 3)
3. Watch RULE-006 trigger cooldown
4. Try to trade again
5. **Expected**: ALL rules blocked, order canceled

**Logs You Should See**:
```bash
# RULE-006 triggers
⚠️ VIOLATION: TradeFrequencyLimit
🔒 COOLDOWN LOCKOUT: 60 seconds
⏱️  Timer started: cooldown_PRAC-V2-126244 (60s)

# New event arrives (position opened)
📨 Event: POSITION_OPENED → evaluating 9 rules

# ⭐ PRE-CHECK BLOCKS ALL RULES
⏱️  COOLDOWN ACTIVE
   Reason: Trade frequency exceeded
   Remaining: 55s
   ❌ ALL 9 rules BLOCKED

# Individual rules skipped
   ❌ MaxContracts - NOT EVALUATED (cooldown active)
   ❌ MaxContractsPerInstrument - NOT EVALUATED (cooldown active)
   ❌ DailyUnrealizedLoss - NOT EVALUATED (cooldown active)
   ❌ ALL RULES - NOT EVALUATED
```

---

### Test 2: Trigger RULE-003 Hard Lockout, Watch ALL Rules Blocked

**Steps**:
1. Edit config: `daily_realized_loss.limit: -5.0` (small limit)
2. Start `run_dev.py`
3. Close 3 trades at -$2 each (total: -$6, exceeds -$5 limit)
4. Watch RULE-003 trigger hard lockout
5. Try to trade again
6. **Expected**: ALL rules blocked until 17:00 CT

**Logs You Should See**:
```bash
# RULE-003 triggers
⚠️ VIOLATION: DailyRealizedLoss
💰 Daily P&L: -$6.00 / -$5.00 limit
🔒 HARD LOCKOUT until 17:00 CT

# New event arrives (quote update)
📨 Event: QUOTE_UPDATE → evaluating 9 rules

# ⭐ PRE-CHECK BLOCKS ALL RULES
🔒 HARD LOCKOUT ACTIVE
   Reason: Daily loss limit exceeded
   Until: 2025-10-30 17:00:00 CT
   ❌ ALL 9 rules BLOCKED

# Even profit targets can't execute!
📊 Unrealized P&L: $+500.00  ← Would trigger RULE-005, but blocked!
   ❌ MaxUnrealizedProfit - NOT EVALUATED (hard lockout active)
```

---

### Test 3: Multiple Rules Create Lockouts, First One Blocks Rest

**Steps**:
1. Start `run_dev.py`
2. Trigger RULE-007 (close trade with -$150 loss)
3. This creates 30-minute cooldown
4. While in cooldown, try to exceed RULE-001 (max contracts)
5. **Expected**: RULE-001 never evaluates because RULE-007's cooldown blocks it!

**Logs You Should See**:
```bash
# RULE-007 triggers
⚠️ VIOLATION: CooldownAfterLoss
   Loss: -$150.00 exceeds threshold (-$100.00)
🔒 COOLDOWN LOCKOUT: 30 minutes (1800s)
⏱️  Timer started: cooldown_loss_PRAC-V2-126244 (1800s)

# Trader tries to open 6th contract (exceeds RULE-001 limit of 5)
📨 Event: POSITION_OPENED → evaluating 9 rules

# ⭐ PRE-CHECK BLOCKS ALL RULES (including RULE-001!)
⏱️  COOLDOWN ACTIVE
   Reason: Large single-trade loss (-$150)
   Remaining: 1795s (29 min 55s)
   ❌ ALL 9 rules BLOCKED

   ❌ MaxContracts - NOT EVALUATED (cooldown active)
      ↑ Would have triggered violation, but never got to evaluate!
```

---

## 📊 Complete Implementation Code

### File 1: `src/risk_manager/core/manager.py` (MODIFIED)

**Find** (around line 245):
```python
engine = RiskEngine(
    config=self.config,
    event_bus=event_bus,
    trading_integration=trading_integration,
)
```

**Replace With**:
```python
engine = RiskEngine(
    config=self.config,
    event_bus=event_bus,
    trading_integration=trading_integration,
    lockout_manager=lockout_manager,  # ← ADD
    timer_manager=timer_manager,       # ← ADD
)
```

---

### File 2: `src/risk_manager/core/engine.py` (MODIFIED)

**Add to imports** (top of file):
```python
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from risk_manager.state.lockout_manager import LockoutManager
    from risk_manager.state.timer_manager import TimerManager
```

**Update constructor** (lines 20-33):
```python
def __init__(
    self,
    config: RiskConfig,
    event_bus: EventBus,
    trading_integration: Any | None = None,
    lockout_manager: "LockoutManager | None" = None,  # ← ADD
    timer_manager: "TimerManager | None" = None,      # ← ADD
):
    self.config = config
    self.event_bus = event_bus
    self.trading_integration = trading_integration
    self.lockout_manager = lockout_manager  # ← ADD
    self.timer_manager = timer_manager       # ← ADD
    self.rules: list[Any] = []
    self.running = False

    # State tracking
    self.daily_pnl = 0.0
    self.peak_balance = 0.0
    self.current_positions: dict[str, Any] = {}
    self.market_prices: dict[str, float] = {}

    logger.info("Risk Engine initialized")
```

**Add PRE-CHECK layer** (insert at line 79, BEFORE rule loop):
```python
async def evaluate_rules(self, event: RiskEvent) -> list[dict[str, Any]]:
    """Evaluate all rules against an event."""

    # Checkpoint 6: Event received
    if len(self.rules) > 0:
        logger.info(f"📨 Event: {event.event_type.value} → evaluating {len(self.rules)} rules")
    else:
        logger.debug(f"📨 Event received: {event.event_type.value} - no rules configured")

    # ═══════════════════════════════════════════════════════════════
    # ⭐ PRE-CHECK LAYER: Respect timers/schedules from ALL rules
    # ═══════════════════════════════════════════════════════════════

    if self.lockout_manager:
        account_id = event.data.get("account_id")

        if account_id and self.lockout_manager.is_locked_out(account_id):
            lockout_info = self.lockout_manager.get_lockout_info(account_id)
            lockout_type = lockout_info.get('type', 'unknown')
            reason = lockout_info.get('reason', 'Unknown')

            # Enhanced logging based on lockout type
            if lockout_type == 'hard':
                until = lockout_info.get('until', 'Unknown')
                logger.opt(colors=True).warning(
                    f"<yellow>🔒 HARD LOCKOUT ACTIVE</yellow>\n"
                    f"   Reason: {reason}\n"
                    f"   Until: {until}\n"
                    f"   ❌ Skipping ALL {len(self.rules)} rules"
                )
            elif lockout_type == 'cooldown':
                remaining = lockout_info.get('remaining_seconds', 0)
                logger.opt(colors=True).warning(
                    f"<yellow>⏱️  COOLDOWN ACTIVE</yellow>\n"
                    f"   Reason: {reason}\n"
                    f"   Remaining: {remaining}s\n"
                    f"   ❌ Skipping ALL {len(self.rules)} rules"
                )
            else:
                logger.opt(colors=True).warning(
                    f"<yellow>⚠️  LOCKOUT ACTIVE ({lockout_type})</yellow>\n"
                    f"   Reason: {reason}\n"
                    f"   ❌ Skipping ALL {len(self.rules)} rules"
                )

            # Log each rule being skipped (debug level)
            for rule in self.rules:
                rule_name = rule.__class__.__name__.replace('Rule', '')
                logger.debug(f"   ❌ {rule_name} - NOT EVALUATED (lockout active)")

            # Return empty violations - don't evaluate ANY rules!
            return []

    # ✅ PRE-CHECK PASSED - Evaluate rules normally
    logger.opt(colors=True).debug(f"<green>✅ PRE-CHECK PASSED: No lockout, evaluating rules</green>")

    violations = []
    rule_results = []

    # Rest of method unchanged...
    for rule in self.rules:
        try:
            violation = await rule.evaluate(event, self)
            # ... existing rule evaluation logic
```

---

## 📋 Testing Checklist

### Before Testing
- [ ] Code changes applied to `manager.py`
- [ ] Code changes applied to `engine.py`
- [ ] Config has small limits for easy triggering:
  - `daily_realized_loss.limit: -5.0`
  - `trade_frequency_limit.per_minute: 3`
  - `cooldown_after_loss.loss_threshold: -100.0`

### Test Scenarios
- [ ] **Test 1**: Trigger RULE-006 cooldown, verify all rules blocked
- [ ] **Test 2**: Trigger RULE-003 hard lockout, verify all rules blocked
- [ ] **Test 3**: Trigger RULE-007 cooldown, verify RULE-001 can't evaluate
- [ ] **Test 4**: Wait for cooldown expiry, verify rules resume evaluation
- [ ] **Test 5**: Wait for daily reset (17:00 CT), verify hard lockout clears

### Expected Logs
- [ ] `⏱️ COOLDOWN ACTIVE` when cooldown triggers
- [ ] `🔒 HARD LOCKOUT ACTIVE` when hard lockout triggers
- [ ] `❌ Skipping ALL X rules` when lockout blocks evaluation
- [ ] `✅ PRE-CHECK PASSED` when no lockout active
- [ ] Individual rule skip logs in debug mode

---

## 🎯 What Changes in run_dev.py

**BEFORE** (Current Behavior):
```bash
📨 Event: POSITION_OPENED → evaluating 9 rules
✅ Rule: MaxContracts → PASS
✅ Rule: MaxContractsPerInstrument → PASS
✅ Rule: DailyUnrealizedLoss → PASS
```

**AFTER** (With PRE-CHECK):
```bash
# When lockout active:
📨 Event: POSITION_OPENED → evaluating 9 rules
⏱️  COOLDOWN ACTIVE
   Reason: Trade frequency exceeded
   Remaining: 55s
   ❌ Skipping ALL 9 rules

# When no lockout:
📨 Event: POSITION_OPENED → evaluating 9 rules
✅ PRE-CHECK PASSED: No lockout, evaluating rules
✅ Rule: MaxContracts → PASS
✅ Rule: MaxContractsPerInstrument → PASS
✅ Rule: DailyUnrealizedLoss → PASS
```

---

## ✅ Summary

**What's Missing**: PRE-CHECK layer in `engine.py` that checks lockout state before rule evaluation

**What to Add**:
1. Wire `lockout_manager` + `timer_manager` to `RiskEngine`
2. Add PRE-CHECK logic at start of `evaluate_rules()`
3. Enhanced logging to show when rules are blocked

**Result**: **ALL 13 rules** will respect **ALL timers/schedules** from **ALL other rules**!

**Testing**: Use `run_dev.py` with small limits to easily trigger lockouts and see PRE-CHECK in action

---

**Ready to implement?** This is about ~50 lines of code changes across 2 files!
