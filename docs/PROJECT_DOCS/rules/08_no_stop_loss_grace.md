---
doc_id: RULE-008
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001]
enforcement_type: Trade-by-Trade (No Lockout)
---

# RULE-008: NoStopLossGrace

**Purpose:** Enforce stop-loss placement - close position if no SL placed within grace period.

## Config
```yaml
no_stop_loss_grace:
  enabled: true
  grace_period_seconds: 10  # Must place SL within 10 seconds of opening position
  enforcement: "close_position"
```

## Trigger
**Event:** `GatewayUserOrder` (when position opens)

**Logic:**
```python
def on_position_open(position_event):
    # Start timer
    timer_manager.start_timer(
        name=f"sl_grace_{position_event['id']}",
        duration=config['grace_period_seconds'],
        callback=lambda: check_stop_loss(position_event)
    )

def check_stop_loss(position_event):
    # Check if SL order exists for this position
    orders = get_open_orders(account_id)
    has_stop_loss = any(o['type'] == 4 and o['contractId'] == position_event['contractId'] for o in orders)

    if not has_stop_loss:
        return BREACH  # No SL placed
```

## Enforcement
1. Close position (MOD-001)
2. **NO lockout** (can trade again)
3. Log: `"No stop-loss placed within 10s - position closed"`

**Use Case:** Force traders to always use stop-losses.
