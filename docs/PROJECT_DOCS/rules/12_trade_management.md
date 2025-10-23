---
doc_id: RULE-012
version: 2.0
last_updated: 2025-01-17
dependencies: []
enforcement_type: Trade-by-Trade (Automation)
---

# RULE-012: TradeManagement

**Purpose:** Automated trade management - auto breakeven stop, trailing stops.

## Config
```yaml
trade_management:
  enabled: true
  auto_breakeven:
    enabled: true
    profit_trigger_ticks: 10  # Move SL to breakeven after +10 ticks profit
  trailing_stop:
    enabled: true
    activation_ticks: 20      # Start trailing after +20 ticks profit
    trail_distance_ticks: 10  # Trail 10 ticks behind high
```

## Trigger
**Event:** `GatewayUserPosition` + market price updates

**Logic:**
```python
def check(position_event, current_price):
    unrealized_profit_ticks = calculate_ticks(position_event, current_price)

    # Auto Breakeven
    if config['auto_breakeven']['enabled']:
        if unrealized_profit_ticks >= config['auto_breakeven']['profit_trigger_ticks']:
            return ACTION_MOVE_SL_TO_BREAKEVEN

    # Trailing Stop
    if config['trailing_stop']['enabled']:
        if unrealized_profit_ticks >= config['trailing_stop']['activation_ticks']:
            return ACTION_UPDATE_TRAILING_STOP
```

## Enforcement
1. **Modify stop-loss order** via API:
   ```http
   POST /api/Order/modify
   {
     "accountId": 123,
     "orderId": 789,
     "stopPrice": 21005.0  // New stop price (breakeven or trailing)
   }
   ```
2. **NO position close** (just modify SL)
3. **NO lockout**

**Use Case:** Automated risk management - protect profits without manual intervention.
