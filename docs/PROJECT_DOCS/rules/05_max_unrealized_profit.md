---
doc_id: RULE-005
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001, MOD-002, MOD-004]
enforcement_type: Hard Lockout (Until Reset)
---

# RULE-005: MaxUnrealizedProfit

**Purpose:** Enforce profit target - close positions when daily profit limit is hit.

## Config
```yaml
max_unrealized_profit:
  enabled: true
  limit: 1000        # Close positions at +$1000 profit
  reset_time: "17:00"
  enforcement: "close_all_and_lockout"
```

## Trigger
**Event:** `GatewayUserPosition` + market price updates

**Logic:**
```python
unrealized_pnl = sum((current_price - avg_price) * size * tick_value for all positions)
if unrealized_pnl >= config['limit']:
    return BREACH  # Hit profit target
```

## Enforcement
1. Close all positions (lock in profits) (MOD-001)
2. Set lockout until reset_time (MOD-002) - prevents re-entry
3. Auto-unlock at 5:00 PM (MOD-004)

**Use Case:** "Take profit and stop for the day" rule.
