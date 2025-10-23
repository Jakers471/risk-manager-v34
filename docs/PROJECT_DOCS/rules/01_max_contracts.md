---
doc_id: RULE-001
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001]
enforcement_type: Trade-by-Trade (No Lockout)
---

# RULE-001: MaxContracts

**Purpose:** Cap net contract exposure across all instruments to prevent over-leveraging.

---

## ⚙️ Configuration

```yaml
max_contracts:
  enabled: true
  limit: 5                  # Max net contracts across all instruments
  count_type: "net"         # "net" or "gross"
  close_all: true           # Close all positions on breach
  reduce_to_limit: false    # Alternative: reduce to limit instead
  lockout_on_breach: false  # No lockout for this rule
```

---

## 🎯 Trigger Condition

**Event Type:** `GatewayUserPosition`

**Logic:**
```python
def check(position_event):
    # Calculate total net position across all instruments
    all_positions = state_manager.get_all_positions(account_id)

    total_net = 0
    for pos in all_positions:
        if pos['type'] == 1:  # Long
            total_net += pos['size']
        elif pos['type'] == 2:  # Short
            total_net -= pos['size']

    # Convert to absolute value for net count
    total_net = abs(total_net)

    if total_net > config['limit']:
        return BREACH
```

**Example Scenarios:**

| Position | Type | Size | Net Total | Breach (limit=5)? |
|----------|------|------|-----------|-------------------|
| MNQ | Long | 3 | 3 | ❌ No |
| ES | Long | 2 | 5 | ❌ No |
| MNQ | Long | 3 | 3 | ❌ No |
| ES | Long | 3 | 6 | ✅ **YES** |
| MNQ | Long | 5, Short | 3 | 2 | ❌ No |
| ES | Long | 5, Short | 1 | 4 | 6 | ✅ **YES** |

---

## 🚨 Enforcement Action

**Type:** Trade-by-Trade (NO lockout, trader can trade again immediately)

**Action Sequence:**
1. ✅ **Close positions** (via MOD-001)
   - If `close_all: true` → `actions.close_all_positions(account_id)`
   - If `reduce_to_limit: true` → Calculate excess and close positions to reach limit
2. ✅ **Log enforcement** → `logs/enforcement.log`
3. ✅ **Update Trader CLI** → Show warning: `"⚠️ MaxContracts breach - All positions closed"`
4. ❌ **NO lockout** → Trader can place next trade immediately

**Enforcement Code:**
```python
def enforce(account_id):
    if config['close_all']:
        actions.close_all_positions(account_id)
        logger.log_enforcement(f"MaxContracts breach - Closed all positions (net={total_net}, limit={config['limit']})")

    elif config['reduce_to_limit']:
        # Close positions until net <= limit
        actions.reduce_positions_to_limit(account_id, target_net=config['limit'])
        logger.log_enforcement(f"MaxContracts breach - Reduced to limit (from {total_net} to {config['limit']})")

    # NO lockout
```

---

## 📡 API Requirements

### **SignalR Event (Trigger):**
```json
{
  "id": 456,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 1,              // 1=Long, 2=Short
  "size": 3,
  "averagePrice": 21000.5
}
```

### **REST API Calls (Enforcement):**

**If `close_all: true`:**
```http
POST /api/Position/searchOpen
{
  "accountId": 123
}

Response: {"positions": [...]}

For each position:
  POST /api/Position/closeContract
  {
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25"
  }
```

**If `reduce_to_limit: true`:**
```http
POST /api/Position/searchOpen
{
  "accountId": 123
}

Calculate which positions to close:
  - Sort by size (largest first)
  - Close positions until net <= limit

POST /api/Position/closeContract (for selected positions)
```

---

## 🗄️ State Tracking

**State Manager:**
```python
# Track all current positions
positions = {
    "CON.F.US.MNQ.U25": {"type": 1, "size": 3},
    "CON.F.US.ES.U25": {"type": 1, "size": 2}
}

# Update on every GatewayUserPosition event
def update_position(event):
    contract_id = event['contractId']
    if event['size'] == 0:
        del positions[contract_id]  # Position closed
    else:
        positions[contract_id] = {
            "type": event['type'],
            "size": event['size']
        }
```

**No SQLite persistence needed** (positions rebuild from API on daemon restart)

---

## 🧪 Test Scenarios

### **Test 1: Net Calculation**
- Open Long MNQ 3
- Open Long ES 2
- **Expected:** Total net = 5, no breach (limit=5)

### **Test 2: Breach Detection**
- Open Long MNQ 3
- Open Long ES 3
- **Expected:** Total net = 6, **BREACH** → close all positions

### **Test 3: Net vs Gross**
- Open Long MNQ 5
- Open Short MNQ 3
- **Net:** abs(5 - 3) = 2, no breach
- **Gross:** 5 + 3 = 8, breach if limit=5

### **Test 4: Reduce to Limit**
- Config: `reduce_to_limit: true`, `limit: 3`
- Open Long MNQ 2, Long ES 3 (net=5, breach)
- **Expected:** Close ES position (reduces net to 2, within limit)

---

## ⚡ Performance

- **Event frequency:** Every position update (high frequency)
- **Calculation cost:** O(n) where n = number of open positions (typically < 10)
- **API calls on breach:** 1 search + n closes (where n = number of positions)

---

## 📋 CLI Display

**Trader CLI shows:**
```
Max Contracts: 5/5 ⚠️  (at limit)

Recent Enforcement:
  [14:23:15] MaxContracts breach - Closed all positions (net=6, limit=5)
```

**No lockout timer** (can trade again immediately)

---

## 🔗 Dependencies

- **MOD-001** (enforcement/actions.py) - close_all_positions(), close_position()
- **state_manager.py** - get_all_positions()

---

**This rule enforces on a trade-by-trade basis with no lockout period.**
