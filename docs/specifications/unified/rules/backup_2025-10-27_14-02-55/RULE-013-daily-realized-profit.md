# RULE-013: Daily Realized Profit

**Category**: Hard Lockout (Category 3)
**Priority**: Medium
**Status**: Not Implemented (No dedicated spec file existed before v3.0)

---

## Unified Specification (v3.0)

### Purpose
Enforce daily realized profit target to prevent giving back profits through overtrading. This rule tracks cumulative realized profits and losses from closed trades throughout the trading day and locks the account when the profit target is hit, forcing the trader to "take the win and walk away."

**Philosophy**: Profit protection + discipline - prevents psychological overtrading after hitting daily goal.

### Trigger Condition
**Event Type**: `GatewayUserTrade` (every trade execution)

**Trigger Logic**:
```python
def check(trade_event):
    pnl = trade_event['profitAndLoss']

    # Only count full-turn trades (profitAndLoss is null for opening trades)
    if pnl is not None:
        daily_realized_pnl = pnl_tracker.add_trade_pnl(
            account_id=trade_event['accountId'],
            pnl=pnl
        )

        if daily_realized_pnl >= config['target']:
            return BREACH  # Hit profit target!
```

**Key Points**:
- Only tracks **realized** P&L (closed trades)
- Ignores half-turn trades (`profitAndLoss: null`)
- Cumulative total for the trading day
- Resets daily at configured reset time
- **Opposite of RULE-003** (profit target instead of loss limit)

### Enforcement Action

**Type**: HARD LOCKOUT (User Guidance Applied - Resolution Rule #1)

**Action Sequence** (per user guidance):
1. **Close ALL positions account-wide immediately** (lock in all profits)
2. **Cancel ALL open orders** (prevent further trading)
3. **Enter lockout mode** (via LockoutManager)
4. **Set timer-based unlock** (configurable reset_time, e.g., 5:00 PM → 5:00 PM next day)
5. **If trader attempts new trade while locked → close immediately** (event router enforcement)
6. **NO admin manual unlock** - lockout ends ONLY via timer

**Implementation Code**:
```python
async def enforce(self, account_id, daily_pnl, engine):
    # 1. Close all positions (take all profits!)
    await engine.enforcement.close_all_positions(account_id)

    # 2. Cancel all orders (stop further trading)
    await engine.enforcement.cancel_all_orders(account_id)

    # 3. Calculate next reset time (timer-based, configurable)
    reset_time = self._calculate_next_reset_time(
        current_time=datetime.now(),
        reset_hour=self.config['reset_time'],  # e.g., "17:00"
        timezone=self.config['timezone']       # e.g., "America/New_York"
    )

    # 4. Set timer-based lockout (NO admin manual unlock)
    await engine.lockout_manager.set_lockout(
        account_id=account_id,
        reason=f"Daily profit target reached: ${daily_pnl:.2f} / ${self.config['target']:.2f} - Good job!",
        until=reset_time,  # Timer-based unlock
        admin_override=False  # Per user guidance
    )

    # 5. Log enforcement
    self.logger.info(
        f"RULE-013 PROFIT TARGET: Account {account_id} locked until {reset_time}. "
        f"Daily P&L: ${daily_pnl:.2f}, Target: ${self.config['target']:.2f}. "
        f"Great trading day!"
    )
```

**Why Hard Lockout?** (per user guidance):
- Prevents giving back profits through overtrading
- Forces trader to stop on a winning day
- Psychological discipline: "Take the win and walk away"
- Opposite philosophy from RULE-005 (trade-by-trade profit taking)

### Configuration Parameters
```yaml
daily_realized_profit:
  enabled: true
  target: 1000.0  # Daily profit target (positive value, e.g., +$1000)

  # Timer-based unlock configuration (MUST BE CONFIGURABLE per user guidance)
  reset_time: "17:00"  # Reset time in HH:MM format (e.g., 5:00 PM)
  timezone: "America/New_York"  # Timezone for reset time

  # Enforcement settings
  enforcement: "close_all_and_lockout"
  lockout_until_reset: true
  admin_manual_unlock: false  # Per user guidance - timer only

  # Optional: Custom message for trader CLI
  success_message: "Daily profit target reached! Good job! See you tomorrow."
```

### State Requirements
- **PnL Tracker**: Yes (track daily realized P&L - **SHARED WITH RULE-003**)
- **Lockout Manager**: Yes (MOD-002 - set/clear lockouts)
- **Timer Manager**: No (lockout expiry handled by LockoutManager)
- **Reset Scheduler**: Yes (MOD-004 - daily reset at configured time)

### SDK Integration
**Events needed**:
- `GatewayUserTrade` - Trigger when trades execute

**Methods needed**:
- `close_all_positions(account_id)` - Close all positions
- `cancel_all_orders(account_id)` - Cancel all open orders

**Quote data needed**: No (realized P&L provided by SDK in trade events)

### Database Schema
```sql
-- Daily P&L tracking (SHARED WITH RULE-003)
CREATE TABLE daily_pnl (
    account_id INTEGER PRIMARY KEY,
    realized_pnl REAL DEFAULT 0,
    date DATE DEFAULT CURRENT_DATE,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Lockout tracking (managed by MOD-002)
CREATE TABLE lockouts (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    rule_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    locked_at DATETIME NOT NULL,
    expires_at DATETIME,  -- Timer-based unlock time
    UNIQUE(account_id, rule_id)
);
```

**Implementation Note**: RULE-003 and RULE-013 **share the same `daily_pnl` table**. Both track the same daily realized P&L value, just trigger on opposite conditions (loss vs profit).

### Examples

**Scenario 1: Normal Trading Day**
- Account state: Daily P&L = $0
- Trade 1: +$300 → Daily P&L = $300
- Trade 2: +$400 → Daily P&L = $700
- Trade 3: -$100 → Daily P&L = $600
- **Trigger**: No breach (below $1000 target)
- **Enforcement**: None
- **Result**: Continue trading normally

**Scenario 2: Profit Target Reached**
- Account state: Daily P&L = +$900
- Trade executes: +$200
- New daily P&L: +$1100
- **Trigger**: Breach detected ($1100 >= $1000)
- **Enforcement**:
  1. Close all positions immediately (lock in profits)
  2. Cancel all orders
  3. Set lockout until 5:00 PM (next day if after 5 PM today)
- **Result**: Account locked, countdown timer shows "Unlocks in 20h 45m"
- **Message**: "Daily profit target reached! Good job! See you tomorrow."

**Scenario 3: Timer-Based Auto-Unlock**
- Account state: Locked at 1:30 PM (P&L = +$1100)
- Time advances to 5:00 PM (reset_time)
- **Trigger**: Reset scheduler executes daily reset
- **Enforcement**:
  1. Reset daily P&L to $0
  2. Clear lockout (timer expired)
- **Result**: Account unlocked, can trade again with fresh daily P&L counter

**Scenario 4: Interaction with RULE-003**
- Account state: Daily P&L = +$950
- Trade executes: +$100
- New daily P&L: +$1050
- **Trigger**: RULE-013 breach (hit profit target)
- **Enforcement**: Lockout until 5:00 PM
- **Note**: Cannot also trigger RULE-003 (both track same P&L, but opposite directions). A trader cannot simultaneously hit both profit target and loss limit.

**Scenario 5: Attempt to Trade While Locked**
- Account state: Locked (P&L = +$1100)
- Trader somehow places order (e.g., via another client)
- Order fills
- **Trigger**: Event router detects locked account
- **Enforcement**: Close position immediately
- **Result**: Position closed, lockout remains until timer expires

---

## Conflict Resolutions

### Conflict 1: Admin Manual Unlock
- **Source A** (RULE_CATEGORIES.md, line 108): "Reset time (5 PM) or admin override"
- **Source B** (User Guidance - Resolution Rule #1): "NO admin manual unlock - timer only"
- **Resolution**: Use User Guidance (Resolution Rule #1 - HIGHEST AUTHORITY)
- **Rationale**: Applied user's authoritative architectural guidance. All lockouts are timer/schedule-based (automatic). Admin configures rules and timers but does NOT manually unlock trading lockouts.

### Conflict 2: Reset Time Configuration
- **Source A** (RULE_CATEGORIES.md, line 250): Hardcoded "17:00" example
- **Source B** (User Guidance): "MUST be configurable" - not hardcoded
- **Resolution**: Use configurable reset_time parameter
- **Rationale**: Per user guidance, reset schedule must be configurable in config files (not hardcoded). Example: Reset time could be 5PM ET, midnight ET, 6PM CT, etc.

### Conflict 3: Missing Dedicated Spec File
- **Source A** (RULE_CATEGORIES.md, lines 239-271): Summary specification exists
- **Source B** (Wave 1 Analysis, lines 1598-1731): Noted missing dedicated spec file
- **Resolution**: Created v3.0 unified spec using RULE-003 as template
- **Rationale**: RULE-013 mentioned in categories doc but lacked dedicated specification file. Created comprehensive spec matching detail level of RULE-003, as they share identical infrastructure (PnLTracker, MOD-002, MOD-004).

---

## Version History
- v1.0 (N/A): No original specification file existed
- v2.0 (N/A): No original specification file existed
- v3.0 (2025-10-25): **NEW** - Unified specification created (Wave 3) - applied user guidance on timer-based unlocks and configurable reset times

---

## Original Sources
- `/docs/archive/2025-10-25-pre-wave1/02-status-tracking/current/RULE_CATEGORIES.md` (lines 239-271, 108, 219-236)
- `/docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` (lines 1598-1731)
- `/docs/analysis/wave2-gap-analysis/01-RISK-RULES-GAPS.md` (lines 841-901)
- User Guidance (Resolution Rule #1): Realized vs Unrealized PnL Enforcement
- **Template**: RULE-003 (DailyRealizedLoss) - same infrastructure, opposite direction

---

## Implementation Status (from Wave 2)
- **Status**: Not Started (no code exists)
- **What's Missing**:
  - ❌ Rule implementation (can reuse RULE-003 structure)
  - ❌ Integration with LockoutManager (MOD-002 doesn't exist)
  - ❌ Integration with ResetScheduler (MOD-004 doesn't exist)
  - ❌ Timer-based unlock implementation
  - ❌ Tests
- **Dependencies**:
  - PnLTracker ✅ (exists - shared with RULE-003)
  - MOD-002 (LockoutManager) ❌ (must implement first)
  - MOD-004 (ResetScheduler) ❌ (must implement first)
- **Estimated Effort**: 1 day (after MOD-002 and MOD-004 exist, can copy RULE-003 structure)
- **Priority**: Medium (profit protection, not account violation)
- **Blockers**: MOD-002 and MOD-004 missing

---

## Test Coverage (from Wave 2)
- Unit tests: Not started
- Integration tests: Not started
- E2E tests: Not started

**Required Test Scenarios**:
1. Normal day (no breach)
2. Hit target exactly
3. Exceed target
4. Timer-based unlock at reset time
5. Attempt to trade while locked
6. Service restart during lockout (persistence)
7. Timezone handling (reset time in different timezones)
8. Ignore half-turn trades (`profitAndLoss: null`)
9. Multiple trades accumulating to target
10. Cannot simultaneously trigger RULE-003 and RULE-013

---

## Related Rules
- **RULE-003** (DailyRealizedLoss): **IDENTICAL INFRASTRUCTURE** (PnLTracker, MOD-002, MOD-004), opposite direction (loss vs profit)
- **RULE-005** (MaxUnrealizedProfit): Different trigger (unrealized vs realized), different enforcement (trade-by-trade vs hard lockout)
- **RULE-009** (SessionBlockOutside): Similar lockout mechanism, different trigger (time-based vs P&L-based)

---

## Implementation Notes

### Code Reuse from RULE-003
Since RULE-013 has identical infrastructure to RULE-003, implementation can largely copy RULE-003 with these changes:

```python
# RULE-003 (DailyRealizedLoss)
if daily_realized_pnl <= config['limit']:  # Loss limit
    return BREACH

# RULE-013 (DailyRealizedProfit)
if daily_realized_pnl >= config['target']:  # Profit target
    return BREACH
```

**Shared Components**:
- Same SQLite table (`daily_pnl`)
- Same PnLTracker methods
- Same LockoutManager integration
- Same ResetScheduler integration
- Same daily reset logic

**Different Components**:
- Trigger condition (>= vs <=)
- Configuration parameter name (`target` vs `limit`)
- Log messages ("profit target" vs "loss limit")
- CLI messages ("Good job!" vs "Loss limit hit")
