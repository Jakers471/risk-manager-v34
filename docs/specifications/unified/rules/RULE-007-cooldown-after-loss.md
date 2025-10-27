# RULE-007: Cooldown After Loss

**Category**: Timer/Cooldown (Category 2)
**Priority**: Medium
**Status**: Not Implemented

---

## Unified Specification (v3.0)

### Purpose
Force break after losing trades to prevent revenge trading.

### Trigger Condition
**Event**: `EventType.TRADE_EXECUTED` (when `profitAndLoss < 0`)

### Enforcement Action
**Type**: TIMER/COOLDOWN

1. Close all positions
2. Start tiered cooldown based on loss amount
3. Auto-unlock when timer expires

### Configuration
```yaml
cooldown_after_loss:
  enabled: true
  loss_thresholds:
    - loss_amount: -100.0
      cooldown_duration: 300   # 5 min
    - loss_amount: -200.0
      cooldown_duration: 900   # 15 min
    - loss_amount: -300.0
      cooldown_duration: 1800  # 30 min
```

### Dependencies
- MOD-003 (TimerManager): ❌ Missing
- PnLTracker: ✅ Exists

---

## Conflict Resolutions
**No conflicts found.**

---

## Version History
- v3.0 (2025-10-25): Unified specification (Wave 3)

---

## Implementation Status
- **Status**: Not Started
- **Blockers**: MOD-003
- **Effort**: 1-2 days
