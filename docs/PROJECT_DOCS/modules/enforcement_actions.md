---
doc_id: MOD-001
version: 2.0
last_updated: 2025-01-17
dependencies: []
---

# MOD-001: Enforcement Actions

**Purpose:** Centralized enforcement logic - all rules call these functions to execute actions.

**File:** `src/enforcement/actions.py`

---

## 🎯 Core Principle

**All risk rules call MOD-001 to enforce actions. NO rule directly calls the API.**

This ensures:
- **No duplication:** Enforcement logic written once
- **Consistency:** All rules enforce the same way
- **Testability:** Mock MOD-001 for rule testing
- **Logging:** All enforcement logged in one place

---

## 🔧 Public API

### **1. close_all_positions(account_id)**
**Purpose:** Close all open positions for an account.

**Implementation:**
```python
def close_all_positions(account_id: int) -> bool:
    """
    Close all open positions via TopstepX API.

    Args:
        account_id: TopstepX account ID

    Returns:
        True if successful, False otherwise
    """
    try:
        # Step 1: Get all open positions
        response = rest_client.post(
            "/api/Position/searchOpen",
            json={"accountId": account_id}
        )

        positions = response.json()["positions"]

        if not positions:
            logger.info(f"No positions to close for account {account_id}")
            return True

        # Step 2: Close each position
        for position in positions:
            rest_client.post(
                "/api/Position/closeContract",
                json={
                    "accountId": account_id,
                    "contractId": position["contractId"]
                }
            )

        logger.info(f"Closed {len(positions)} positions for account {account_id}")
        log_enforcement(f"CLOSE_ALL_POSITIONS: account={account_id}, count={len(positions)}")
        return True

    except Exception as e:
        logger.error(f"Error closing positions: {e}")
        return False
```

**REST API Calls:**
```http
POST /api/Position/searchOpen
{
  "accountId": 123
}

Response:
{
  "positions": [
    {"contractId": "CON.F.US.MNQ.U25", ...},
    {"contractId": "CON.F.US.ES.U25", ...}
  ]
}

For each position:
  POST /api/Position/closeContract
  {
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25"
  }
```

**Used By:** RULE-001, 003, 009 (all "close all" rules)

---

### **2. close_position(account_id, contract_id)**
**Purpose:** Close a specific position.

**Implementation:**
```python
def close_position(account_id: int, contract_id: str) -> bool:
    """
    Close specific position via TopstepX API.

    Args:
        account_id: TopstepX account ID
        contract_id: Contract ID (e.g., "CON.F.US.MNQ.U25")

    Returns:
        True if successful, False otherwise
    """
    try:
        rest_client.post(
            "/api/Position/closeContract",
            json={
                "accountId": account_id,
                "contractId": contract_id
            }
        )

        logger.info(f"Closed position {contract_id} for account {account_id}")
        log_enforcement(f"CLOSE_POSITION: account={account_id}, contract={contract_id}")
        return True

    except Exception as e:
        logger.error(f"Error closing position {contract_id}: {e}")
        return False
```

**REST API Call:**
```http
POST /api/Position/closeContract
{
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25"
}
```

**Used By:** RULE-002, 009, 011 (symbol-specific rules)

---

### **3. reduce_position_to_limit(account_id, contract_id, target_size)**
**Purpose:** Partially close position to reach target size.

**Implementation:**
```python
def reduce_position_to_limit(account_id: int, contract_id: str, target_size: int) -> bool:
    """
    Reduce position to target size via TopstepX API.

    Args:
        account_id: TopstepX account ID
        contract_id: Contract ID
        target_size: Desired position size

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current position size
        response = rest_client.post(
            "/api/Position/searchOpen",
            json={"accountId": account_id}
        )

        positions = response.json()["positions"]
        current_position = next((p for p in positions if p["contractId"] == contract_id), None)

        if not current_position:
            logger.warning(f"Position {contract_id} not found")
            return False

        current_size = current_position["size"]

        if current_size <= target_size:
            logger.info(f"Position {contract_id} already at or below target ({current_size} <= {target_size})")
            return True

        # Calculate how many contracts to close
        contracts_to_close = current_size - target_size

        # Partially close position
        rest_client.post(
            "/api/Position/partialCloseContract",
            json={
                "accountId": account_id,
                "contractId": contract_id,
                "size": contracts_to_close
            }
        )

        logger.info(f"Reduced {contract_id} from {current_size} to {target_size}")
        log_enforcement(f"REDUCE_POSITION: account={account_id}, contract={contract_id}, from={current_size}, to={target_size}")
        return True

    except Exception as e:
        logger.error(f"Error reducing position {contract_id}: {e}")
        return False
```

**REST API Calls:**
```http
POST /api/Position/searchOpen
{
  "accountId": 123
}

POST /api/Position/partialCloseContract
{
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "size": 1    // Number of contracts to close
}
```

**Used By:** RULE-001 (with reduce_to_limit option), RULE-002

---

### **4. cancel_all_orders(account_id)**
**Purpose:** Cancel all pending orders.

**Implementation:**
```python
def cancel_all_orders(account_id: int) -> bool:
    """
    Cancel all open orders via TopstepX API.

    Args:
        account_id: TopstepX account ID

    Returns:
        True if successful, False otherwise
    """
    try:
        # Step 1: Get all open orders
        response = rest_client.post(
            "/api/Order/searchOpen",
            json={"accountId": account_id}
        )

        orders = response.json()["orders"]

        if not orders:
            logger.info(f"No orders to cancel for account {account_id}")
            return True

        # Step 2: Cancel each order
        for order in orders:
            rest_client.post(
                "/api/Order/cancel",
                json={
                    "accountId": account_id,
                    "orderId": order["id"]
                }
            )

        logger.info(f"Cancelled {len(orders)} orders for account {account_id}")
        log_enforcement(f"CANCEL_ALL_ORDERS: account={account_id}, count={len(orders)}")
        return True

    except Exception as e:
        logger.error(f"Error cancelling orders: {e}")
        return False
```

**REST API Calls:**
```http
POST /api/Order/searchOpen
{
  "accountId": 123
}

For each order:
  POST /api/Order/cancel
  {
    "accountId": 123,
    "orderId": 789
  }
```

**Used By:** RULE-003, 009 (lockout rules)

---

### **5. cancel_order(account_id, order_id)**
**Purpose:** Cancel a specific order.

**Implementation:**
```python
def cancel_order(account_id: int, order_id: int) -> bool:
    """
    Cancel specific order via TopstepX API.

    Args:
        account_id: TopstepX account ID
        order_id: Order ID

    Returns:
        True if successful, False otherwise
    """
    try:
        rest_client.post(
            "/api/Order/cancel",
            json={
                "accountId": account_id,
                "orderId": order_id
            }
        )

        logger.info(f"Cancelled order {order_id} for account {account_id}")
        log_enforcement(f"CANCEL_ORDER: account={account_id}, order={order_id}")
        return True

    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        return False
```

**Used By:** Individual rules that need to cancel specific orders

---

## 📝 Enforcement Logging

### **Log Format:**
```
[2025-01-17 14:23:15] CLOSE_ALL_POSITIONS: account=123, count=3
[2025-01-17 14:23:15] CANCEL_ALL_ORDERS: account=123, count=2
[2025-01-17 14:23:16] CLOSE_POSITION: account=123, contract=CON.F.US.MNQ.U25
[2025-01-17 14:23:17] REDUCE_POSITION: account=123, contract=CON.F.US.ES.U25, from=3, to=2
```

**Log File:** `logs/enforcement.log`

**Function:**
```python
def log_enforcement(message: str):
    """Log enforcement action to enforcement.log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/enforcement.log", "a") as f:
        f.write(f"[{timestamp}] {message}\n")
```

---

## 🚨 Error Handling

### **Rate Limiting:**
```python
def handle_rate_limit(response):
    """Handle 429 Too Many Requests."""
    if response.status_code == 429:
        logger.warning("Rate limit hit - backing off 30 seconds")
        time.sleep(30)
        return True  # Retry
    return False
```

### **Authentication Errors:**
```python
def handle_auth_error(response):
    """Handle 401 Unauthorized."""
    if response.status_code == 401:
        logger.warning("Auth error - refreshing token")
        rest_client.refresh_token()
        return True  # Retry
    return False
```

### **Retry Logic:**
```python
def execute_with_retry(api_call, max_retries=3):
    """Execute API call with retry logic."""
    for attempt in range(max_retries):
        try:
            response = api_call()
            if response.json()["success"]:
                return True

            if handle_rate_limit(response):
                continue
            if handle_auth_error(response):
                continue

            return False

        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

    return False
```

---

## 🧪 Testing

### **Unit Tests:**
```python
# tests/unit/test_enforcement_actions.py

def test_close_all_positions(mock_rest_client):
    mock_rest_client.post.return_value = {
        "positions": [
            {"contractId": "CON.F.US.MNQ.U25"},
            {"contractId": "CON.F.US.ES.U25"}
        ]
    }

    result = actions.close_all_positions(123)
    assert result == True
    assert mock_rest_client.post.call_count == 3  # 1 search + 2 closes
```

---

## 📊 Performance

| Function | API Calls | Typical Latency |
|----------|-----------|-----------------|
| `close_all_positions` | 1 search + n closes | 100-500ms (n=1-5) |
| `close_position` | 1 close | 50-100ms |
| `cancel_all_orders` | 1 search + n cancels | 100-500ms (n=1-10) |
| `reduce_position_to_limit` | 1 search + 1 partial | 100-200ms |

**Enforcement Speed:** Typically < 500ms from breach detection to API call completion.

---

## 🔗 Dependencies

- **src/api/rest_client.py** - REST API wrapper
- **src/utils/logging.py** - Logging utilities
- **logs/enforcement.log** - Enforcement log file

---

**This module is the foundation of all enforcement - every rule depends on it.**
