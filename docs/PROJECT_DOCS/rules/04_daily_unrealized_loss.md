---
doc_id: RULE-004
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001, MOD-002, MOD-004]
enforcement_type: Hard Lockout (Until Reset)
---

# RULE-004: DailyUnrealizedLoss

**Purpose:** Enforce hard daily floating loss limit.

## Config
```yaml
daily_unrealized_loss:
  enabled: true
  limit: -300
  reset_time: "17:00"
  enforcement: "close_all_and_lockout"
```

## Trigger
**Event:** `GatewayUserPosition` + market price updates

**Logic:** Calculate unrealized P&L for all open positions:
```python
unrealized_pnl = sum((current_price - avg_price) * size * tick_value for all positions)
if unrealized_pnl <= config['limit']:
    return BREACH
```

## Enforcement
1. Close all positions (MOD-001)
2. Set lockout until reset_time (MOD-002)
3. Auto-unlock at 5:00 PM daily (MOD-004)

**API:** Same as RULE-003 (close positions, set lockout)

**Used By:** Traders who want to limit floating drawdown, not just realized losses.
