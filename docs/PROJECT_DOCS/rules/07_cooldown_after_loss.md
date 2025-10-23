---
doc_id: RULE-007
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001, MOD-002, MOD-003]
enforcement_type: Configurable Timer Lockout
---

# RULE-007: CooldownAfterLoss

**Purpose:** Force break after losing trades to prevent revenge trading.

## Config
```yaml
cooldown_after_loss:
  enabled: true
  loss_thresholds:
    - loss_amount: -100
      cooldown_duration: 300    # 5 min cooldown after -$100 loss
    - loss_amount: -200
      cooldown_duration: 900    # 15 min cooldown after -$200 loss
    - loss_amount: -300
      cooldown_duration: 1800   # 30 min cooldown after -$300 loss
```

## Trigger
**Event:** `GatewayUserTrade`

**Logic:**
```python
trade_pnl = trade_event['profitAndLoss']
if trade_pnl < 0:  # Losing trade
    for threshold in config['loss_thresholds']:
        if trade_pnl <= threshold['loss_amount']:
            return BREACH, threshold['cooldown_duration']
```

## Enforcement
1. **NO position close** (trade already done)
2. Set cooldown (MOD-002, MOD-003):
   - `set_cooldown(account_id, "Cooldown after -$150 loss", duration=300)`
3. CLI shows countdown
4. Auto-unlock when timer expires

**Use Case:** "Take a break after big loss" - prevents emotional trading.
