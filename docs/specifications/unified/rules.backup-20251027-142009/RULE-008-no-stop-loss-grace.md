# RULE-008: No Stop-Loss Grace

**Category**: Trade-by-Trade (Category 1)
**Priority**: Medium
**Status**: Not Implemented

---

## Unified Specification (v3.0)

### Purpose
Enforce stop-loss placement - close position if no SL placed within grace period.

### Trigger Condition
**Event**: `EventType.ORDER_PLACED` (when position opens)

**Logic**: Start timer, check for stop-loss order at expiry

### Enforcement Action
**Type**: TRADE-BY-TRADE

1. Close that position if no stop-loss found
2. NO lockout
3. Can trade immediately

### Configuration
```yaml
no_stop_loss_grace:
  enabled: true
  grace_period_seconds: 10  # 10 seconds to place SL
  enforcement: "close_position"
```

### Dependencies
- MOD-003 (TimerManager): ❌ Missing

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
- **Effort**: 2 days
