---
doc_id: RULE-006
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001, MOD-002, MOD-003]
enforcement_type: Configurable Timer Lockout
---

# RULE-006: TradeFrequencyLimit

**Purpose:** Prevent overtrading by limiting trades per time window.

## Config
```yaml
trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3
    per_hour: 10
    per_session: 50
  cooldown_on_breach:
    enabled: true
    per_minute_breach: 60      # 1 min cooldown
    per_hour_breach: 1800      # 30 min cooldown
    per_session_breach: 3600   # 1 hour cooldown
```

## Trigger
**Event:** `GatewayUserTrade`

**Logic:**
```python
minute_count = count_trades_in_window(account_id, window=60)  # Last 60 seconds
hour_count = count_trades_in_window(account_id, window=3600)
session_count = count_trades_since_session_start(account_id)

if minute_count >= config['limits']['per_minute']:
    return BREACH, "per_minute"
elif hour_count >= config['limits']['per_hour']:
    return BREACH, "per_hour"
elif session_count >= config['limits']['per_session']:
    return BREACH, "per_session"
```

## Enforcement
1. **NO position close** (trade already happened)
2. Set cooldown (MOD-002, MOD-003):
   - `set_cooldown(account_id, "3/3 trades this minute", duration=60)`
3. CLI shows countdown: `"🟡 COOLDOWN - 3/3 trades - Unlocks in 47s"`
4. Auto-unlock when timer expires

**State Tracking:**
```sql
CREATE TABLE trade_counts (
    account_id INTEGER,
    window_start DATETIME,
    count INTEGER,
    PRIMARY KEY (account_id, window_start)
);
```
