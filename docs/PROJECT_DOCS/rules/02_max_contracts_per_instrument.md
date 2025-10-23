---
doc_id: RULE-002
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001]
enforcement_type: Trade-by-Trade (No Lockout)
---

# RULE-002: MaxContractsPerInstrument

**Purpose:** Enforce per-symbol contract limits to prevent concentration risk.

---

## ⚙️ Configuration

```yaml
max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 2      # Max 2 contracts in MNQ
    ES: 1       # Max 1 contract in ES
    NQ: 1       # Max 1 contract in NQ
  enforcement: "reduce_to_limit"  # "close_all" or "reduce_to_limit"
  unknown_symbol_action: "block"  # "block", "allow_with_limit:N", "allow_unlimited"
  lockout_on_breach: false
```

---

## 🎯 Trigger Condition

**Event Type:** `GatewayUserPosition`

**Logic:**
```python
def check(position_event):
    contract_id = position_event['contractId']
    symbol = extract_symbol(contract_id)  # "CON.F.US.MNQ.U25" → "MNQ"

    current_size = abs(position_event['size'])

    # Check if symbol has configured limit
    if symbol in config['limits']:
        limit = config['limits'][symbol]
        if current_size > limit:
            return BREACH
    else:
        # Unknown symbol handling
        if config['unknown_symbol_action'] == "block":
            if current_size > 0:
                return BREACH  # Close any position in unlisted symbol
```

**Symbol Extraction:**
```python
def extract_symbol(contract_id):
    # "CON.F.US.MNQ.U25" → "MNQ"
    # "CON.F.US.ES.U25" → "ES"
    parts = contract_id.split('.')
    return parts[3] if len(parts) >= 4 else contract_id
```

---

## 🚨 Enforcement Action

**Action Sequence:**
1. ✅ **Enforce limit** (via MOD-001)
   - If `enforcement: "reduce_to_limit"` → Close excess contracts only
   - If `enforcement: "close_all"` → Close entire position in that symbol
2. ✅ **Log enforcement**
3. ✅ **Update Trader CLI**
4. ❌ **NO lockout**

**Enforcement Code:**
```python
def enforce(account_id, contract_id, current_size, limit):
    if config['enforcement'] == "reduce_to_limit":
        excess = current_size - limit
        actions.reduce_position(account_id, contract_id, reduce_by=excess)
        logger.log_enforcement(f"MaxContractsPerInstrument - {symbol}: Reduced from {current_size} to {limit}")

    elif config['enforcement'] == "close_all":
        actions.close_position(account_id, contract_id)
        logger.log_enforcement(f"MaxContractsPerInstrument - {symbol}: Closed entire position (size={current_size}, limit={limit})")

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
  "type": 1,
  "size": 3      // Breach if limit=2
}
```

### **REST API Calls (Enforcement):**

**Reduce to Limit:**
```http
POST /api/Position/partialCloseContract
{
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "size": 1      // Close 1 contract (3 - 2 = 1 excess)
}
```

**Close All:**
```http
POST /api/Position/closeContract
{
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25"
}
```

---

## 🗄️ State Tracking

**Track per-symbol positions:**
```python
positions_by_symbol = {
    "MNQ": {"contract_id": "CON.F.US.MNQ.U25", "size": 2},
    "ES": {"contract_id": "CON.F.US.ES.U25", "size": 1}
}
```

---

## 🧪 Test Scenarios

### **Test 1: Normal Enforcement**
- Config: `MNQ: 2`, `enforcement: "reduce_to_limit"`
- Open Long MNQ 3
- **Expected:** Reduce from 3 to 2 (close 1 contract)

### **Test 2: Unknown Symbol - Block**
- Config: `unknown_symbol_action: "block"`
- Open Long RTY 1 (RTY not in limits)
- **Expected:** Close entire RTY position

### **Test 3: Unknown Symbol - Allow**
- Config: `unknown_symbol_action: "allow_unlimited"`
- Open Long RTY 5
- **Expected:** No enforcement

### **Test 4: Multiple Instruments**
- Limits: `MNQ: 2`, `ES: 1`
- Open MNQ 2, ES 1
- **Expected:** Both OK
- Open ES 2
- **Expected:** ES reduced to 1

---

## 📋 CLI Display

```
Per-Instrument Limits:
  MNQ: 2/2 ⚠️ (at limit)
  ES: 1/1 ⚠️ (at limit)
  NQ: 0/1 🟢

Recent Enforcement:
  [14:23:15] MaxContractsPerInstrument - MNQ: Reduced from 3 to 2
```

---

## 🔗 Dependencies

- **MOD-001** (actions.py) - close_position(), reduce_position()
- **state_manager.py** - get_position_by_symbol()

---

**This rule prevents concentration in single instruments.**
