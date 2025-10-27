# RULE-008: No Stop-Loss Grace

**Category**: Trade-by-Trade (Category 1)
**Priority**: Medium
**Status**: Not Implemented

---

## Unified Specification (v3.0)

### Purpose
Enforce stop-loss placement - close position if no SL placed within grace period.

### Trigger Condition
**Events**:
- `EventType.POSITION_OPENED` - Start grace period timer when position opens
- `EventType.ORDER_PLACED` - Detect stop loss order placement (type=3, stopPrice present)

**Logic**:
1. On `POSITION_OPENED`: Start grace period timer for that position
2. On `ORDER_PLACED` with `order.type=3` (STOP): Record stop loss, cancel timer
3. On timer expiry: Check if stop loss exists, close position if missing

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

### Implementation Notes

**Critical: Stop Order Lifecycle**
1. **Stop price is visible in ORDER_PLACED, NOT ORDER_FILLED**
   - When stop order is placed: `ORDER_PLACED` event has `order.type=3`, `order.stopPrice=<value>`
   - When stop order triggers: `ORDER_FILLED` event has `order.type=1` (becomes MARKET), `order.stopPrice=null`
   - Must capture stopPrice from ORDER_PLACED event!

2. **Event Subscription Logic**:
   - `POSITION_OPENED`: Fires when new position created (0 → 1+ contracts)
   - `ORDER_PLACED`: Fires when ANY order placed (market, limit, stop)
   - Must filter ORDER_PLACED for `order.type=3` to detect stop orders

3. **Grace Period State Machine**:
   ```
   POSITION_OPENED → Start Timer (grace period)
        ↓
   ORDER_PLACED (type=3, stopPrice present) → Cancel Timer, Record Stop Loss
        ↓
   Timer Expires → Check if stop recorded → Close position if missing
   ```

4. **Position Tracking**:
   - Track by `contractId` (e.g., CON.F.US.MNQ.Z25)
   - Multiple positions on same symbol = separate timers
   - Position closed before timer expires = cancel timer

---

## Conflict Resolutions
**No conflicts found.**

---

## Version History
- v3.1 (2025-10-27): **CRITICAL FIX** - Event subscription logic corrected
  - Changed from ORDER_PLACED only → POSITION_OPENED + ORDER_PLACED
  - Added implementation notes explaining stop order lifecycle
  - Clarified that stopPrice visible in ORDER_PLACED, not ORDER_FILLED
- v3.0 (2025-10-25): Unified specification (Wave 3)

---

## Implementation Status
- **Status**: Not Started
- **Blockers**: MOD-003
- **Effort**: 2 days
