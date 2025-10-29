# RULE-006: Trade Frequency Limit

**Category**: Timer/Cooldown (Category 2)
**Priority**: High
**Status**: Not Implemented

---

## Unified Specification (v3.0)

### Purpose
Prevent overtrading by limiting trades per time window (minute/hour/session).

### Trigger Condition
**Event Type**: `EventType.TRADE_EXECUTED` (every trade execution)

**Trigger Logic**:
```python
minute_count = count_trades_in_window(account_id, window=60)  # Last 60s
hour_count = count_trades_in_window(account_id, window=3600)  # Last 1 hour
session_count = count_trades_since_session_start(account_id)

if minute_count >= config['limits']['per_minute']:
    return BREACH, "per_minute", 60  # 1 min cooldown
elif hour_count >= config['limits']['per_hour']:
    return BREACH, "per_hour", 1800  # 30 min cooldown
elif session_count >= config['limits']['per_session']:
    return BREACH, "per_session", 3600  # 1 hour cooldown
```

### Enforcement Action

**Type**: TIMER/COOLDOWN

**Action Sequence**:
1. **NO position close** (trade already executed, can't prevent it)
2. **Set cooldown timer** based on which limit breached
3. **Auto-unlock** when timer expires

**Implementation**:
```python
async def enforce(self, account_id, breach_type, engine):
    # NO close positions (trade already happened)

    # Set cooldown timer
    duration = self.config['cooldown_on_breach'][f'{breach_type}_breach']
    await engine.timer_manager.start_timer(
        account_id=account_id,
        duration_seconds=duration,
        reason=f"Trade frequency limit: {breach_type}"
    )

    # Trader sees countdown: "🟡 COOLDOWN - 3/3 trades - Unlocks in 47s"
```

### Configuration Parameters
```yaml
trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3
    per_hour: 10
    per_session: 50
  cooldown_on_breach:
    per_minute_breach: 60      # 1 min
    per_hour_breach: 1800      # 30 min
    per_session_breach: 3600   # 1 hour
```

### State Requirements
- PnL Tracker: No
- Lockout Manager: No
- Timer Manager: Yes (MOD-003 - countdown timers)
- Reset Scheduler: No
- Trade Counter: Yes (SQLite - track trades in rolling windows)

### SDK Integration
- Events: `EventType.TRADE_EXECUTED`
- Methods: None (no enforcement action, just set timer)
- Quote data: No

### Database Schema
```sql
CREATE TABLE trade_counts (
    account_id INTEGER,
    timestamp DATETIME,
    count INTEGER,
    PRIMARY KEY (account_id, timestamp)
);
```

### Examples

**Scenario**: Hit Per-Minute Limit
- Limit: 3 trades/min
- Trader executes 4th trade within 60s
- **Trigger**: Breach (per_minute)
- **Enforcement**: 60-second cooldown
- **Result**: Cannot trade for 60 seconds, then auto-unlock

---

## Conflict Resolutions
**No conflicts found.** All sources aligned.

---

## Version History
- v3.0 (2025-10-25): Unified specification (Wave 3)

---

## Implementation Status
- **Status**: Not Started
- **Blockers**: MOD-003 (TimerManager) missing
- **Estimated Effort**: 2-3 days

---

## Related Rules
- **RULE-007** (CooldownAfterLoss): Also uses timer/cooldown mechanism
