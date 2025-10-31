# ALL Rules Respect Timers/Schedules

**CRITICAL DISTINCTION**:
- Some rules **CREATE** timers/schedules
- **ALL rules RESPECT** timers/schedules

---

## 🎯 The Truth: Every Rule Respects Every Timer

### Rules That CREATE Timers/Schedules (7 rules)
```
RULE-003: Creates hard lockout until 17:00 CT
RULE-006: Creates cooldown timer (60s-60min)
RULE-007: Creates cooldown timer (30min-60min)
RULE-008: Creates grace period timer (60s + 300s)
RULE-009: Creates session lockout (08:30-15:00 CT)
RULE-010: Creates API polling timer (every 30s)
RULE-013: Creates hard lockout until 17:00 CT
```

### Rules That DON'T Create Timers (6 rules)
```
RULE-001: max_contracts
RULE-002: max_contracts_per_instrument
RULE-004: daily_unrealized_loss
RULE-005: max_unrealized_profit
RULE-011: symbol_blocks
RULE-012: trade_management
```

### But HERE'S THE KEY: ALL 13 Rules Check Timer State!

---

## 🔒 The Enforcement Pre-Check Layer

**BEFORE any rule evaluates, the engine checks:**

```python
# src/risk_manager/core/engine.py

async def handle_event(self, event: RiskEvent):
    """
    Route event to rules with PRE-CHECK LAYER.

    CRITICAL: Check lockout/timer state BEFORE rule evaluation!
    """

    # ═══════════════════════════════════════════════════════════
    # PRE-CHECK 1: Is account locked out?
    # ═══════════════════════════════════════════════════════════

    if self.lockout_manager.is_locked_out(event.account_id):
        lockout_info = self.lockout_manager.get_lockout_info(event.account_id)

        logger.warning(
            f"⚠️ Account locked out - skipping rule evaluation\n"
            f"   Reason: {lockout_info['reason']}\n"
            f"   Until: {lockout_info['until']}\n"
            f"   Remaining: {lockout_info['remaining_time']}"
        )

        # ❌ DON'T EVALUATE ANY RULES - Account is locked!
        return

    # ═══════════════════════════════════════════════════════════
    # PRE-CHECK 2: Is it within trading session?
    # ═══════════════════════════════════════════════════════════

    if self.session_manager.is_outside_session():
        logger.warning(
            f"⚠️ Outside trading session - skipping rule evaluation\n"
            f"   Current: {datetime.now()}\n"
            f"   Session: 08:30 - 15:00 CT"
        )

        # ❌ DON'T EVALUATE ANY RULES - Outside session!
        return

    # ═══════════════════════════════════════════════════════════
    # PRE-CHECK 3: Is there an active cooldown?
    # ═══════════════════════════════════════════════════════════

    if self.lockout_manager.has_cooldown(event.account_id):
        cooldown_info = self.lockout_manager.get_cooldown_info(event.account_id)

        logger.warning(
            f"⚠️ Cooldown active - skipping rule evaluation\n"
            f"   Remaining: {cooldown_info['remaining_seconds']}s"
        )

        # ❌ DON'T EVALUATE ANY RULES - Cooldown active!
        return

    # ═══════════════════════════════════════════════════════════
    # ✅ ALL PRE-CHECKS PASSED - Evaluate rules normally
    # ═══════════════════════════════════════════════════════════

    for rule in self.rules:
        violation = await rule.evaluate(event, self)
        if violation:
            await self.enforce(violation)
```

**This means**:
- ✅ RULE-001 won't evaluate if RULE-003 locked out the account
- ✅ RULE-002 won't evaluate if RULE-009 says we're outside session
- ✅ RULE-004 won't evaluate if RULE-006 set a cooldown
- ✅ RULE-005 won't evaluate if RULE-007 triggered a cooldown
- ✅ **EVERY RULE** respects lockouts/timers from **EVERY OTHER RULE**!

---

## 🎬 What You See in run_dev.py

### Scenario: RULE-006 Creates Cooldown, ALL Other Rules Respect It

```bash
============================================================
                  LIVE EVENT FEED
============================================================

# ─────────────────────────────────────────────────────────
# RULE-006 Triggers (Trade frequency exceeded)
# ─────────────────────────────────────────────────────────

2025-10-30 15:30:00 | CRITICAL | ⚠️ VIOLATION: TradeFrequencyLimitRule
                                   Trades per minute (4) exceeds limit (3)

2025-10-30 15:30:00 | WARNING | ⚠️ Enforcement: FLATTEN ALL + COOLDOWN (60s)
2025-10-30 15:30:01 | SUCCESS | ✅ Closed all positions
2025-10-30 15:30:01 | WARNING | 🔒 COOLDOWN LOCKOUT: 60 seconds

2025-10-30 15:30:01 | INFO  | ⏱️  Timer started: cooldown_PRAC-V2-126244 (60s)

📊 Lockout Status: ❌ LOCKED (Cooldown: 60s)

# ─────────────────────────────────────────────────────────
# ALL RULES NOW RESPECT THIS COOLDOWN!
# ─────────────────────────────────────────────────────────

# Trader tries to open position (would trigger RULE-001 max contracts)
2025-10-30 15:30:15 | INFO  | 📨 Event: POSITION_OPENED (MNQ)

# ⭐ PRE-CHECK LAYER BLOCKS RULE EVALUATION
2025-10-30 15:30:15 | WARNING | ⚠️ PRE-CHECK FAILED: Account locked out (cooldown)
                                 Remaining: 45 seconds
                                 Skipping rule evaluation for ALL rules!

2025-10-30 15:30:15 | INFO  | ❌ RULE-001 (max_contracts) - NOT EVALUATED (locked)
2025-10-30 15:30:15 | INFO  | ❌ RULE-002 (max_contracts_per_instrument) - NOT EVALUATED (locked)
2025-10-30 15:30:15 | INFO  | ❌ RULE-004 (daily_unrealized_loss) - NOT EVALUATED (locked)
2025-10-30 15:30:15 | INFO  | ❌ ALL RULES SKIPPED (account locked)

2025-10-30 15:30:15 | WARNING | ⚠️ Enforcement: CANCEL ORDER (lockout active)
2025-10-30 15:30:15 | SUCCESS | ✅ Canceled order MNQ/ORD-12345

# ─────────────────────────────────────────────────────────
# Quote update arrives (would trigger RULE-004 unrealized loss)
# ─────────────────────────────────────────────────────────

2025-10-30 15:30:30 | INFO  | 📨 Event: QUOTE_UPDATE (MNQ: 20990)

# ⭐ PRE-CHECK LAYER BLOCKS AGAIN
2025-10-30 15:30:30 | WARNING | ⚠️ PRE-CHECK FAILED: Account locked out (cooldown)
                                 Remaining: 30 seconds
                                 Skipping rule evaluation for ALL rules!

2025-10-30 15:30:30 | INFO  | ❌ RULE-004 (unrealized loss) - NOT EVALUATED (locked)
2025-10-30 15:30:30 | INFO  | ❌ ALL OTHER RULES - NOT EVALUATED (locked)

# ─────────────────────────────────────────────────────────
# Cooldown expires
# ─────────────────────────────────────────────────────────

2025-10-30 15:31:01 | INFO  | ⏱️  Timer expired: cooldown_PRAC-V2-126244
2025-10-30 15:31:01 | INFO  | 🔓 COOLDOWN EXPIRED - Trading unlocked
2025-10-30 15:31:01 | SUCCESS | ✅ Lockout cleared

📊 Lockout Status: ✅ UNLOCKED

# ─────────────────────────────────────────────────────────
# Now ALL rules evaluate normally again
# ─────────────────────────────────────────────────────────

2025-10-30 15:31:15 | INFO  | 📨 Event: POSITION_OPENED (MNQ)

# ⭐ PRE-CHECK PASSES
2025-10-30 15:31:15 | INFO  | ✅ PRE-CHECK PASSED: No lockout, evaluating rules...

2025-10-30 15:31:15 | INFO  | ✅ RULE-001 (max_contracts) - EVALUATED (OK)
2025-10-30 15:31:15 | INFO  | ✅ RULE-002 (max_contracts_per_instrument) - EVALUATED (OK)
2025-10-30 15:31:15 | INFO  | ✅ RULE-004 (daily_unrealized_loss) - EVALUATED (OK)
2025-10-30 15:31:15 | INFO  | ✅ ALL RULES EVALUATED NORMALLY

2025-10-30 15:31:15 | SUCCESS | ✅ Position opened successfully
```

**Key Point**: ONE rule (RULE-006) created a cooldown, and **ALL 13 RULES** respected it!

---

## 📊 Complete Respect Matrix

### Which Timers/Schedules Do Rules Respect?

| Rule | Respects Lockouts | Respects Session | Respects Cooldown | Respects Daily Reset |
|------|-------------------|------------------|-------------------|----------------------|
| RULE-001 | ✅ | ✅ | ✅ | ✅ |
| RULE-002 | ✅ | ✅ | ✅ | ✅ |
| RULE-003 | ✅ | ✅ | ✅ | ✅ Creates reset |
| RULE-004 | ✅ | ✅ | ✅ | ✅ |
| RULE-005 | ✅ | ✅ | ✅ | ✅ |
| RULE-006 | ✅ | ✅ | ✅ Creates cooldown | ✅ |
| RULE-007 | ✅ | ✅ | ✅ Creates cooldown | ✅ |
| RULE-008 | ✅ | ✅ | ✅ | ✅ |
| RULE-009 | ✅ Creates session | ✅ Creates session | ✅ | ✅ |
| RULE-010 | ✅ Creates lockout | ✅ | ✅ | ✅ |
| RULE-011 | ✅ | ✅ | ✅ | ✅ |
| RULE-012 | ✅ | ✅ | ✅ | ✅ |
| RULE-013 | ✅ | ✅ | ✅ | ✅ Creates reset |

**Bottom Line**: **ALL 13 RULES** check **ALL timer/schedule state** before evaluating!

---

## 🔧 How It Works: The Check Hierarchy

```
Event Arrives (e.g., POSITION_OPENED)
         │
         ▼
┌─────────────────────────────────────────┐
│ PRE-CHECK LAYER (engine.py)             │
│                                          │
│ 1. Is account locked out?               │
│    └─ Check LockoutManager               │
│       ├─ Hard lockout? (RULE-003/009/010/013) │
│       └─ Cooldown? (RULE-006/007)        │
│                                          │
│ 2. Is within trading session?           │
│    └─ Check SessionManager (RULE-009)    │
│                                          │
│ 3. Has daily reset occurred?            │
│    └─ Check PnLTracker reset flag        │
└─────────────────────────────────────────┘
         │
         ├─ ❌ PRE-CHECK FAILED
         │    └─> Skip ALL rule evaluation
         │        Log: "Account locked, skipping rules"
         │        Action: Cancel order / reject action
         │
         ├─ ✅ PRE-CHECK PASSED
         │    └─> Evaluate rules normally
         ▼
┌─────────────────────────────────────────┐
│ RULE EVALUATION (All 13 rules)          │
│                                          │
│ for each rule:                           │
│   └─ rule.evaluate(event, engine)       │
│      └─ Returns violation or None       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ ENFORCEMENT (enforcement.py)             │
│                                          │
│ if violation:                            │
│   ├─ Execute action (close, flatten)    │
│   └─ Set lockout/timer if needed        │
└─────────────────────────────────────────┘
```

---

## 🎓 Real-World Examples

### Example 1: Daily Reset Affects ALL Rules

```bash
# Before 17:00 CT - RULE-003 has locked account
2025-10-30 16:59:00 | INFO  | 📊 Daily P&L: -$5.00 / -$5.00 (locked)
2025-10-30 16:59:00 | WARNING | 🔒 Account locked until 17:00 CT

# ALL RULES respect this lockout
2025-10-30 16:59:15 | INFO  | 📨 Event: QUOTE_UPDATE
2025-10-30 16:59:15 | WARNING | ⚠️ PRE-CHECK: Locked out, skipping rules
2025-10-30 16:59:15 | INFO  | ❌ RULE-001 - NOT EVALUATED
2025-10-30 16:59:15 | INFO  | ❌ RULE-004 - NOT EVALUATED
2025-10-30 16:59:15 | INFO  | ❌ RULE-005 - NOT EVALUATED
2025-10-30 16:59:15 | INFO  | ❌ ALL RULES - NOT EVALUATED

# Daily reset at 17:00 CT
2025-10-30 17:00:00 | INFO  | ⏰ DAILY RESET TRIGGERED
2025-10-30 17:00:00 | SUCCESS | ✅ P&L reset: -$5.00 → $0.00
2025-10-30 17:00:00 | SUCCESS | 🔓 Lockout cleared

# ALL RULES can now evaluate again
2025-10-30 17:00:15 | INFO  | 📨 Event: POSITION_OPENED
2025-10-30 17:00:15 | INFO  | ✅ PRE-CHECK: No lockout, evaluating rules
2025-10-30 17:00:15 | INFO  | ✅ RULE-001 - EVALUATED
2025-10-30 17:00:15 | INFO  | ✅ RULE-002 - EVALUATED
2025-10-30 17:00:15 | INFO  | ✅ RULE-004 - EVALUATED
2025-10-30 17:00:15 | INFO  | ✅ ALL RULES - EVALUATED
```

---

### Example 2: Session Block Affects ALL Rules

```bash
# Session closes at 15:00 CT (RULE-009)
2025-10-30 15:00:00 | INFO  | ⏰ Session check: Outside hours
2025-10-30 15:00:00 | WARNING | 🔒 SESSION CLOSED - Lockout until 08:30 CT tomorrow

# Quote update after hours
2025-10-30 15:05:00 | INFO  | 📨 Event: QUOTE_UPDATE (ES: 5990)

# PRE-CHECK blocks ALL rules (even RULE-005 profit target!)
2025-10-30 15:05:00 | WARNING | ⚠️ PRE-CHECK: Outside session, skipping rules
2025-10-30 15:05:00 | INFO  | ❌ RULE-004 (unrealized loss) - NOT EVALUATED
2025-10-30 15:05:00 | INFO  | ❌ RULE-005 (profit target) - NOT EVALUATED
2025-10-30 15:05:00 | INFO  | ❌ ALL RULES - NOT EVALUATED (outside session)

# Even if trade is hugely profitable, can't take profit outside session!
📊 Unrealized P&L: $+500.00 (RULE-005 would trigger, but blocked!)
```

---

### Example 3: Cooldown from RULE-007 Blocks RULE-001

```bash
# RULE-007 triggers (large loss on single trade)
2025-10-30 14:30:00 | CRITICAL | ⚠️ VIOLATION: CooldownAfterLossRule
                                   Loss (-$150) exceeds threshold (-$100)

2025-10-30 14:30:00 | WARNING | 🔒 COOLDOWN: 30 minutes
2025-10-30 14:30:00 | INFO  | ⏱️  Timer started: cooldown_loss (1800s)

# Trader tries to open 6th contract (would exceed RULE-001 limit of 5)
2025-10-30 14:30:30 | INFO  | 📨 Event: POSITION_OPENED (ES)

# PRE-CHECK blocks RULE-001 evaluation
2025-10-30 14:30:30 | WARNING | ⚠️ PRE-CHECK: Cooldown active, skipping rules
2025-10-30 14:30:30 | INFO  | ❌ RULE-001 (max contracts) - NOT EVALUATED
2025-10-30 14:30:30 | INFO  | ❌ Order canceled (cooldown active)

# RULE-001 never gets to evaluate - cooldown blocks it!
```

---

## 📋 Summary: The Two-Layer System

### Layer 1: PRE-CHECK (Respects ALL Timers/Schedules)
**Location**: `engine.py` - Before rule evaluation

**Checks**:
1. ✅ Lockout state (from ANY rule)
2. ✅ Session hours (from RULE-009)
3. ✅ Cooldown state (from RULE-006/007)
4. ✅ Daily reset state (from RULE-003/013)

**Applies To**: **ALL 13 RULES** without exception!

---

### Layer 2: RULE EVALUATION (Creates Timers/Schedules)
**Location**: Individual rule files

**Some rules create**:
- Hard lockouts (RULE-003, 010, 013)
- Session lockouts (RULE-009)
- Cooldown timers (RULE-006, 007)
- Grace period timers (RULE-008)
- Polling timers (RULE-010)
- Daily reset schedules (RULE-003, 013)

**But ALL rules**:
- Are blocked by lockouts
- Are blocked outside session
- Are blocked during cooldowns
- Reset state on daily reset

---

## ✅ Key Takeaways

1. **7 rules CREATE timers/schedules**
2. **ALL 13 rules RESPECT timers/schedules**
3. **PRE-CHECK layer enforces universal respect**
4. **Even rules that don't create timers are affected by them**

**Example**:
- RULE-001 (max contracts) never creates a timer
- BUT RULE-001 is blocked by:
  - RULE-003 hard lockout ✅
  - RULE-006 cooldown ✅
  - RULE-007 cooldown ✅
  - RULE-009 session block ✅
  - RULE-010 API lockout ✅
  - RULE-013 profit lockout ✅

**This is the coordination layer that makes the system work as ONE unified enforcement pipeline!**

---

**Last Updated**: 2025-10-30
**Status**: Complete timer/schedule respect map for ALL 13 rules
