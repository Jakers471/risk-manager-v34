# Risk Rule Categories & Enforcement Types

**Date**: 2025-10-23
**Critical**: Understanding enforcement types for correct implementation

---

## 🎯 Three Rule Categories

**Risk rules fall into 3 categories based on enforcement behavior:**

```
┌────────────────────────────────────────────────────────────────┐
│  CATEGORY 1: TRADE-BY-TRADE                                    │
│  - Close ONLY that specific position                           │
│  - Do NOT close other positions                                │
│  - Do NOT create lockout                                       │
│  - Trader can immediately trade again                          │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  CATEGORY 2: TIMER/COOLDOWN                                    │
│  - Close all positions                                         │
│  - Create TEMPORARY lockout with countdown                     │
│  - Auto-unlock when timer expires                              │
│  - Duration: 60s, 30min, 1hr, etc.                            │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  CATEGORY 3: HARD LOCKOUT                                      │
│  - Close all positions                                         │
│  - Create PERMANENT lockout until condition met                │
│  - Unlock at: Reset time (5 PM), admin override, or condition  │
│  - Cannot trade until unlocked                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 📋 Complete Rule List (13 Rules)

### Category 1: Trade-by-Trade (6 Rules)

**Enforcement**: Close ONLY that position, no lockout

| Rule | Name | Trigger | Action |
|------|------|---------|--------|
| **RULE-001** | Max Contracts | Position update | Close position that caused breach |
| **RULE-002** | Max Contracts Per Instrument | Position update | Close position in that instrument |
| **RULE-004** | Daily Unrealized Loss | Position P&L check | Close that losing position only |
| **RULE-005** | Max Unrealized Profit | Position P&L check | Close that winning position only (take profit) |
| **RULE-008** | Stop-Loss Enforcement | Order/Position check | Close position if no stop placed |
| **RULE-011** | Symbol Blocks | Any event | Close position in blocked symbol |

**Example (RULE-004)**:
```
Trader has:
- MNQ: 2 contracts, P&L: -$150  ← Trigger: Unrealized loss too high
- ES: 1 contract, P&L: +$50

Action: Close MNQ position ONLY
Result:
- MNQ: 0 contracts (closed) ✅
- ES: 1 contract (still open) ✅
- No lockout, can trade immediately
```

---

### Category 2: Timer/Cooldown (2 Rules)

**Enforcement**: Close all + Temporary lockout with countdown

| Rule | Name | Trigger | Cooldown Duration |
|------|------|---------|-------------------|
| **RULE-006** | Trade Frequency Limit | Trade count | 60s / 30min / 1hr (configurable) |
| **RULE-007** | Cooldown After Loss | Loss threshold | Configurable (e.g., 15 minutes) |

**Example (RULE-007)**:
```
Trader loses $150 in one trade (threshold: $100)

Action:
1. Close all positions
2. Cancel all orders
3. Start 15-minute timer

Trader CLI shows:
┌──────────────────────────────────────────┐
│ ⏱️  COOLDOWN ACTIVE                       │
│ Reason: Loss exceeded $100               │
│ Time Remaining: 14:23                    │
│ Auto-unlocks at: 2:47 PM                 │
└──────────────────────────────────────────┘

After 15 minutes: Auto-unlock ✅
```

---

### Category 3: Hard Lockout (5 Rules)

**Enforcement**: Close all + Lockout until reset/condition

| Rule | Name | Trigger | Unlock Condition |
|------|------|---------|------------------|
| **RULE-003** | Daily Realized Loss | Daily P&L | Reset time (5 PM) or admin override |
| **RULE-013** | Daily Realized Profit | Daily P&L | Reset time (5 PM) or admin override |
| **RULE-009** | Session Block Outside | Time check | Session start time (9:30 AM) |
| **RULE-010** | Auth Loss Guard | canTrade status | Admin override only |
| **RULE-012** | Trade Management (optional) | Automation | N/A (automation, not enforcement) |

**Example (RULE-003)**:
```
Trader hits -$500 daily loss (limit: -$500)

Action:
1. Close all positions
2. Cancel all orders
3. Lock account until 5:00 PM

Trader CLI shows:
┌──────────────────────────────────────────┐
│ 🔴 HARD LOCKOUT                          │
│ Reason: Daily loss limit exceeded        │
│ Current: -$520 / Limit: -$500           │
│ Unlocks at: 5:00 PM (4h 32m)            │
│                                          │
│ Cannot trade until unlock.               │
└──────────────────────────────────────────┘

Cannot trade until 5 PM or admin unlocks ❌
```

---

### Category 4: Automation (1 Rule)

**Not enforcement - just automation**

| Rule | Name | Description |
|------|------|-------------|
| **RULE-012** | Trade Management | Auto breakeven stops, trailing stops |

---

## 🔧 Implementation Differences

### Trade-by-Trade Implementation

```python
# RULE-004: Daily Unrealized Loss (Trade-by-Trade)

async def enforce(self, position, engine):
    """Close ONLY this position, not others."""

    # Close only this specific position
    await engine.enforcement.close_position(
        account_id=position.account_id,
        symbol=position.symbol  # ← ONLY this symbol
    )

    # NO lockout
    # NO cancel other orders
    # Trader can immediately place next trade

    self.logger.info(
        f"Closed {position.symbol} position "
        f"(unrealized loss: ${position.unrealized_pnl})"
    )
```

### Timer/Cooldown Implementation

```python
# RULE-007: Cooldown After Loss (Timer)

async def enforce(self, trade, engine):
    """Close all + temporary lockout."""

    # 1. Close all positions
    await engine.enforcement.flatten_all(account_id)

    # 2. Start countdown timer
    duration = self.config['cooldown_minutes'] * 60  # 15 min = 900s
    await engine.timer_manager.start_timer(
        account_id=account_id,
        duration_seconds=duration,
        reason=f"Cooldown after ${trade.pnl} loss"
    )

    # Timer auto-expires and unlocks
```

### Hard Lockout Implementation

```python
# RULE-003: Daily Realized Loss (Hard Lockout)

async def enforce(self, trade, engine):
    """Close all + hard lockout until reset."""

    # 1. Close all positions
    await engine.enforcement.flatten_all(account_id)

    # 2. Set lockout until 5 PM
    reset_time = self._calculate_reset_time()  # 5:00 PM
    await engine.lockout_manager.set_lockout(
        account_id=account_id,
        reason=f"Daily loss: ${daily_pnl} / ${self.limit}",
        until=reset_time  # ← DOES NOT AUTO-EXPIRE
    )

    # Requires reset time or admin override to unlock
```

---

## 📊 Enforcement Matrix

| Rule | Close Position | Close All | Cancel Orders | Lockout Type | Can Trade Again |
|------|----------------|-----------|---------------|--------------|-----------------|
| **001** | That position | No | No | None | Immediately |
| **002** | That symbol | No | No | None | Immediately |
| **003** | All | Yes | Yes | Hard (5 PM) | At reset/admin |
| **004** | That position | No | No | None | Immediately |
| **005** | That position | No | No | None | Immediately |
| **006** | All | Yes | Yes | Timer (60s-1hr) | When timer expires |
| **007** | All | Yes | Yes | Timer (15min) | When timer expires |
| **008** | That position | No | No | None | Immediately |
| **009** | All | Yes | Yes | Hard (session) | At session start |
| **010** | All | Yes | Yes | Hard (permanent) | Admin only |
| **011** | That symbol | No | No | None | Immediately |
| **012** | N/A | N/A | N/A | N/A | N/A (automation) |
| **013** | All | Yes | Yes | Hard (5 PM) | At reset/admin |

---

## 🆕 RULE-013: Daily Realized Profit (NEW)

**Category**: Hard Lockout
**Purpose**: Take profit and stop trading once daily target hit

```yaml
# RULE-013: Daily Realized Profit
daily_realized_profit:
  enabled: true
  target: 1000.0              # Take profit at $1000/day
  reset_time: "17:00"         # Reset at 5 PM

  enforcement:
    close_all: true           # Close all positions (take profit)
    cancel_orders: true       # Stop further trading
    lockout_until_reset: true # Lock until 5 PM
```

**Logic**:
```
Trader reaches +$1000 daily realized profit

Action:
1. Close all positions (lock in profit!)
2. Cancel all orders
3. Lock account until 5:00 PM

Message: "Daily profit target reached! Good job! See you tomorrow."
```

**Why Hard Lockout?**
Prevents giving back profits through overtrading. Forces trader to stop on a winning day.

---

## 🎯 Summary

### When to Close ONLY That Position (Trade-by-Trade)
```
✅ RULE-001: Over contract limit
✅ RULE-002: Over per-instrument limit
✅ RULE-004: That position has too much unrealized loss
✅ RULE-005: That position has hit profit target
✅ RULE-008: That position has no stop-loss
✅ RULE-011: That symbol is blacklisted
```

### When to Close ALL + Timer
```
✅ RULE-006: Too many trades (cooldown 60s-1hr)
✅ RULE-007: Big loss in one trade (cooldown 15min)
```

### When to Close ALL + Hard Lockout
```
✅ RULE-003: Daily realized loss limit hit (until 5 PM)
✅ RULE-013: Daily realized profit target hit (until 5 PM)
✅ RULE-009: Trading outside session hours (until session start)
✅ RULE-010: canTrade = false (until admin unlocks)
```

---

## 🔄 State Management Requirements

### Trade-by-Trade Rules
**Need**:
- Position tracking (SDK provides)
- NO lockout storage
- NO timer storage

### Timer/Cooldown Rules
**Need**:
- Timer storage (SQLite)
- Expiration tracking
- Auto-unlock logic

### Hard Lockout Rules
**Need**:
- Lockout storage (SQLite)
- Daily P&L tracking (SQLite)
- Reset scheduler
- Admin override capability

---

**Created**: 2025-10-23
**Critical Changes**:
- RULE-004, 005, 008 are trade-by-trade (NOT close all)
- Added RULE-013: Daily Realized Profit
- Corrected enforcement categories

**Next**: Update config formats and implementation guides
