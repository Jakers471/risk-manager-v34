# RULE-003: Daily Realized Loss

**Category**: Hard Lockout (Category 3)
**Priority**: Critical
**Status**: Partially Implemented (70% complete - needs MOD-002 and MOD-004 integration)

---

## Unified Specification (v3.0)

### Purpose
Enforce hard daily realized P&L limit to prevent catastrophic daily losses and account termination. This rule tracks cumulative realized profits and losses from closed trades throughout the trading day.

### Trigger Condition
**Event Type**: `EventType.TRADE_EXECUTED` (every trade execution)

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

        if daily_realized_pnl <= config['limit']:
            return BREACH
```

**Key Points**:
- Only tracks **realized** P&L (closed trades)
- Ignores half-turn trades (`profitAndLoss: null`)
- Cumulative total for the trading day
- Resets daily at configured reset time

### Enforcement Action

**Type**: HARD LOCKOUT (User Guidance Applied)

**Action Sequence** (per user guidance - Resolution Rule #1):
1. **Close ALL positions account-wide immediately** (via SDK enforcement)
2. **Cancel ALL open orders** (via SDK enforcement)
3. **Enter lockout mode** (via LockoutManager)
4. **Set timer-based unlock** (configurable reset_time, e.g., 5:00 PM → 5:00 PM next day)
5. **If trader attempts new trade while locked → close immediately** (event router enforcement)
6. **NO admin manual unlock** - lockout ends ONLY via timer

**Implementation Code**:
```python
async def enforce(self, account_id, daily_pnl, engine):
    # 1. Close all positions
    await engine.enforcement.close_all_positions(account_id)

    # 2. Cancel all orders
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
        reason=f"Daily realized loss limit: ${daily_pnl:.2f} / ${self.config['limit']:.2f}",
        until=reset_time,  # Timer-based unlock
        admin_override=False  # Per user guidance
    )

    # 5. Log enforcement
    self.logger.critical(
        f"RULE-003 BREACH: Account {account_id} locked until {reset_time}. "
        f"Daily P&L: ${daily_pnl:.2f}, Limit: ${self.config['limit']:.2f}"
    )
```

### Configuration Parameters
```yaml
daily_realized_loss:
  enabled: true
  limit: -500.0  # Max daily loss (negative value, e.g., -$500)

  # Timer-based unlock configuration (MUST BE CONFIGURABLE per user guidance)
  reset_time: "17:00"  # Reset time in HH:MM format (e.g., 5:00 PM)
  timezone: "America/New_York"  # Timezone for reset time

  # Enforcement settings
  enforcement: "close_all_and_lockout"
  lockout_until_reset: true
  admin_manual_unlock: false  # Per user guidance - timer only
```

### State Requirements
- **PnL Tracker**: Yes (track daily realized P&L)
- **Lockout Manager**: Yes (MOD-002 - set/clear lockouts)
- **Timer Manager**: No (lockout expiry handled by LockoutManager)
- **Reset Scheduler**: Yes (MOD-004 - daily reset at configured time)

### SDK Integration
**Events needed**:
- `EventType.TRADE_EXECUTED` - Trigger when trades execute

**Methods needed**:
- `close_all_positions(account_id)` - Close all positions
- `cancel_all_orders(account_id)` - Cancel all open orders

**Quote data needed**: No (realized P&L provided by SDK in trade events)

### Database Schema
```sql
-- Daily P&L tracking (shared with RULE-013)
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

### Examples

**Scenario 1: Normal Trading Day**
- Account state: Daily P&L = $0
- Trade 1: +$100 → Daily P&L = $100
- Trade 2: +$50 → Daily P&L = $150
- Trade 3: -$200 → Daily P&L = -$50
- **Trigger**: No breach (within -$500 limit)
- **Enforcement**: None
- **Result**: Continue trading normally

**Scenario 2: Loss Limit Breach**
- Account state: Daily P&L = -$450
- Trade executes: -$100
- New daily P&L: -$550
- **Trigger**: Breach detected (-$550 <= -$500)
- **Enforcement**:
  1. Close all positions immediately
  2. Cancel all orders
  3. Set lockout until 5:00 PM (next day if after 5 PM today)
- **Result**: Account locked, countdown timer shows "Unlocks in 22h 15m"

**Scenario 3: Timer-Based Auto-Unlock**
- Account state: Locked at 2:00 PM (P&L = -$550)
- Time advances to 5:00 PM (reset_time)
- **Trigger**: Reset scheduler executes daily reset
- **Enforcement**:
  1. Reset daily P&L to $0
  2. Clear lockout (timer expired)
- **Result**: Account unlocked, can trade again with fresh daily P&L counter

**Scenario 4: Attempt to Trade While Locked**
- Account state: Locked (P&L = -$550)
- Trader somehow places order (e.g., via another client)
- Order fills
- **Trigger**: Event router detects locked account
- **Enforcement**: Close position immediately
- **Result**: Position closed, lockout remains until timer expires

---

## Conflict Resolutions

### Conflict 1: Admin Manual Unlock
- **Source A** (Original spec, lines 194-196): "Admin override" mentioned for unlock
- **Source B** (User Guidance - Resolution Rule #1): "NO admin manual unlock - timer only"
- **Resolution**: Use User Guidance (Resolution Rule #1 - HIGHEST AUTHORITY)
- **Rationale**: Applied user's authoritative architectural guidance. All lockouts are timer/schedule-based (automatic). Admin configures rules and timers but does NOT manually unlock trading lockouts.

### Conflict 2: Reset Time Configuration
- **Source A** (Original spec, line 22): Hardcoded "17:00" example
- **Source B** (User Guidance): "MUST be configurable" - not hardcoded
- **Resolution**: Use configurable reset_time parameter
- **Rationale**: Per user guidance, reset schedule must be configurable in config files (not hardcoded). Example: Reset time could be 5PM ET, midnight ET, 6PM CT, etc.

---

## Version History
- v1.0 (2025-01-17): Original specification
- v2.0 (2025-01-17): Revised with MOD dependencies
- v3.0 (2025-10-25): Unified specification (Wave 3) - applied user guidance on timer-based unlocks and configurable reset times

---

## Original Sources
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/rules/03_daily_realized_loss.md` (lines 1-228)
- `/docs/archive/2025-10-25-pre-wave1/02-status-tracking/current/RULE_CATEGORIES.md` (lines 101-133, 219-236)
- `/docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` (lines 286-468)
- `/docs/analysis/wave2-gap-analysis/01-RISK-RULES-GAPS.md` (lines 140-190)
- User Guidance (Resolution Rule #1): Realized vs Unrealized PnL Enforcement

---

## Implementation Status (from Wave 2)
- **Status**: Partially Implemented (70% complete)
- **What's Done**:
  - ✅ Basic rule structure and class
  - ✅ Event subscription logic (PNL_UPDATED, POSITION_CLOSED)
  - ✅ Breach detection logic (daily_pnl <= limit)
  - ✅ Configuration validation
  - ✅ PnLTracker exists and works
- **What's Missing**:
  - ❌ Integration with LockoutManager (MOD-002 doesn't exist)
  - ❌ Integration with ResetScheduler (MOD-004 doesn't exist)
  - ❌ Timer-based unlock implementation
  - ❌ Comprehensive tests
- **Dependencies**:
  - PnLTracker ✅ (exists)
  - MOD-002 (LockoutManager) ❌ (must implement first)
  - MOD-004 (ResetScheduler) ❌ (must implement first)
- **Estimated Effort**: 1 day (after MOD-002 and MOD-004 exist)
- **Priority**: Critical (account violation prevention)
- **Blockers**: MOD-002 and MOD-004 missing

---

## Test Coverage (from Wave 2)
- Unit tests: Partial (basic logic only)
- Integration tests: Missing (needs MOD-002/MOD-004)
- E2E tests: Missing

**Required Test Scenarios**:
1. Normal day (no breach)
2. Hit limit exactly
3. Exceed limit
4. Timer-based unlock at reset time
5. Attempt to trade while locked
6. Service restart during lockout (persistence)
7. Timezone handling (reset time in different timezones)
8. Ignore half-turn trades (`profitAndLoss: null`)

---

## Related Rules
- **RULE-013** (DailyRealizedProfit): Same infrastructure (PnLTracker, MOD-002, MOD-004), opposite direction
- **RULE-004** (DailyUnrealizedLoss): Different trigger (unrealized vs realized), different enforcement (trade-by-trade vs hard lockout)
- **RULE-009** (SessionBlockOutside): Similar lockout mechanism, different trigger (time-based vs P&L-based)
