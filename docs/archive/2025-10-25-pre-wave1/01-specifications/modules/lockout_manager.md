---
doc_id: MOD-002
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-003]
---

# MOD-002: Lockout Manager

**Purpose:** Centralized lockout state management - all lockout rules call these functions.

**File:** `src/state/lockout_manager.py`

---

## 🎯 Core Principle

**All lockout states managed in one place. Rules set lockouts, event_router checks lockouts.**

Handles:
- **Hard lockouts** (until specific time: daily reset, session start)
- **Cooldown timers** (duration-based: trade frequency, cooldown after loss)
- **Auto-expiry** (background task clears expired lockouts)
- **Persistence** (saves to SQLite for crash recovery)

---

## 🔧 Public API

### **1. set_lockout(account_id, reason, until)**
**Purpose:** Set hard lockout until specific datetime.

**Implementation:**
```python
def set_lockout(account_id: int, reason: str, until: datetime) -> None:
    """
    Set hard lockout until specific time.

    Args:
        account_id: TopstepX account ID
        reason: Human-readable lockout reason
        until: Datetime when lockout expires

    Example:
        set_lockout(123, "Daily loss limit hit", datetime(2025, 1, 17, 17, 0))
    """
    lockout_state[account_id] = {
        "reason": reason,
        "until": until,
        "type": "hard_lockout",
        "created_at": datetime.now()
    }

    # Persist to SQLite
    db.execute(
        "INSERT OR REPLACE INTO lockouts (account_id, reason, expires_at, created_at) VALUES (?, ?, ?, ?)",
        (account_id, reason, until, datetime.now())
    )

    logger.info(f"Lockout set for account {account_id}: {reason} until {until}")

    # Notify Trader CLI
    cli.update_lockout_display(account_id, reason, until)
```

**Used By:** RULE-003 (DailyRealizedLoss), RULE-009 (SessionBlockOutside), RULE-011 (SymbolBlocks)

---

### **2. set_cooldown(account_id, reason, duration_seconds)**
**Purpose:** Set lockout for specific duration.

**Implementation:**
```python
def set_cooldown(account_id: int, reason: str, duration_seconds: int) -> None:
    """
    Set lockout for specific duration.

    Args:
        account_id: TopstepX account ID
        reason: Human-readable lockout reason
        duration_seconds: Lockout duration in seconds

    Example:
        set_cooldown(123, "Trade frequency limit", 1800)  # 30 minutes
    """
    until = datetime.now() + timedelta(seconds=duration_seconds)

    lockout_state[account_id] = {
        "reason": reason,
        "until": until,
        "type": "cooldown",
        "duration": duration_seconds,
        "created_at": datetime.now()
    }

    # Persist to SQLite
    db.execute(
        "INSERT OR REPLACE INTO lockouts (account_id, reason, expires_at, created_at) VALUES (?, ?, ?, ?)",
        (account_id, reason, until, datetime.now())
    )

    # Start countdown timer (via MOD-003)
    timer_manager.start_timer(
        name=f"lockout_{account_id}",
        duration=duration_seconds,
        callback=lambda: clear_lockout(account_id)
    )

    logger.info(f"Cooldown set for account {account_id}: {reason} for {duration_seconds}s")

    # Notify Trader CLI
    cli.update_lockout_display(account_id, reason, until)
```

**Used By:** RULE-006 (TradeFrequencyLimit), RULE-007 (CooldownAfterLoss)

---

### **3. is_locked_out(account_id)**
**Purpose:** Check if account is currently locked out.

**Implementation:**
```python
def is_locked_out(account_id: int) -> bool:
    """
    Check if account is currently locked out.

    Args:
        account_id: TopstepX account ID

    Returns:
        True if locked out, False otherwise
    """
    if account_id not in lockout_state:
        return False

    lockout = lockout_state[account_id]

    # Check if lockout expired
    if datetime.now() >= lockout['until']:
        clear_lockout(account_id)
        return False

    return True
```

**Called By:** `event_router.py` (before processing every event)

**Event Router Logic:**
```python
def route_event(event_type, event_data):
    account_id = event_data['accountId']

    # CHECK LOCKOUT FIRST
    if lockout_manager.is_locked_out(account_id):
        # If locked and new position detected, close immediately
        if event_type == "GatewayUserPosition" and event_data['size'] > 0:
            actions.close_position(account_id, event_data['contractId'])
            logger.warning(f"Closed position while locked out: {event_data['contractId']}")
        return  # Don't process event further

    # Not locked out, route to rules
    # ...
```

---

### **4. get_lockout_info(account_id)**
**Purpose:** Get lockout details for CLI display.

**Implementation:**
```python
def get_lockout_info(account_id: int) -> dict | None:
    """
    Get lockout information for display.

    Args:
        account_id: TopstepX account ID

    Returns:
        Dict with lockout details, or None if not locked out

    Example Return:
        {
            "reason": "Daily loss limit hit",
            "until": datetime(2025, 1, 17, 17, 0),
            "remaining_seconds": 9845,
            "type": "hard_lockout"
        }
    """
    if not is_locked_out(account_id):
        return None

    lockout = lockout_state[account_id]
    remaining = (lockout['until'] - datetime.now()).total_seconds()

    return {
        "reason": lockout['reason'],
        "until": lockout['until'],
        "remaining_seconds": int(remaining),
        "type": lockout['type']
    }
```

**Used By:** Trader CLI for displaying lockout timers

---

### **5. clear_lockout(account_id)**
**Purpose:** Remove lockout (manual or auto-expiry).

**Implementation:**
```python
def clear_lockout(account_id: int) -> None:
    """
    Clear lockout for account.

    Args:
        account_id: TopstepX account ID
    """
    if account_id in lockout_state:
        reason = lockout_state[account_id]['reason']
        del lockout_state[account_id]

        # Remove from SQLite
        db.execute("DELETE FROM lockouts WHERE account_id=?", (account_id,))

        logger.info(f"Lockout cleared for account {account_id}: {reason}")

        # Notify Trader CLI
        cli.clear_lockout_display(account_id)
```

**Called By:**
- Background task (auto-expiry)
- Timer callback (cooldown expiry)
- Admin CLI (manual unlock)

---

### **6. check_expired_lockouts()**
**Purpose:** Background task to auto-clear expired lockouts.

**Implementation:**
```python
def check_expired_lockouts() -> None:
    """
    Check all lockouts and clear expired ones.
    Called every second by daemon main loop.
    """
    now = datetime.now()
    expired_accounts = []

    for account_id, lockout in lockout_state.items():
        if now >= lockout['until']:
            expired_accounts.append(account_id)

    for account_id in expired_accounts:
        clear_lockout(account_id)
        logger.info(f"Auto-cleared expired lockout for account {account_id}")
```

**Called By:** `src/core/daemon.py` main loop (every second)

---

## 🗄️ State Persistence (SQLite)

### **Database Schema:**
```sql
CREATE TABLE lockouts (
    account_id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lockouts_expires ON lockouts(expires_at);
```

### **Load State on Startup:**
```python
def load_lockouts_from_db() -> None:
    """Load lockouts from SQLite on daemon startup."""
    rows = db.execute("SELECT account_id, reason, expires_at FROM lockouts WHERE expires_at > ?", (datetime.now(),))

    for row in rows:
        account_id, reason, until = row
        lockout_state[account_id] = {
            "reason": reason,
            "until": until,
            "type": "hard_lockout",  # Assume hard lockout after restart
            "created_at": datetime.now()
        }

    logger.info(f"Loaded {len(lockout_state)} lockouts from database")
```

---

## 📊 Lockout State (In-Memory)

```python
# Global state (in-memory)
lockout_state = {
    123: {
        "reason": "Daily loss limit hit",
        "until": datetime(2025, 1, 17, 17, 0),
        "type": "hard_lockout",
        "created_at": datetime(2025, 1, 17, 14, 23)
    },
    456: {
        "reason": "Trade frequency limit (3/3 trades)",
        "until": datetime(2025, 1, 17, 14, 53),
        "type": "cooldown",
        "duration": 1800,
        "created_at": datetime(2025, 1, 17, 14, 23)
    }
}
```

---

## ⏱️ Integration with Timer Manager (MOD-003)

**For cooldowns, lockout_manager uses timer_manager:**

```python
# When setting cooldown
def set_cooldown(account_id, reason, duration_seconds):
    until = datetime.now() + timedelta(seconds=duration_seconds)

    # Set lockout state
    lockout_state[account_id] = { ... }

    # Start timer (MOD-003)
    timer_manager.start_timer(
        name=f"lockout_{account_id}",
        duration=duration_seconds,
        callback=lambda: clear_lockout(account_id)  # Auto-clear when timer expires
    )
```

**When timer expires:**
```python
# MOD-003 calls callback
clear_lockout(account_id)  # Lockout automatically removed
```

---

## 🧪 Test Scenarios

### **Test 1: Hard Lockout**
```python
set_lockout(123, "Daily loss limit", datetime(2025, 1, 17, 17, 0))
assert is_locked_out(123) == True

# Fast-forward time to 5:01 PM
assert is_locked_out(123) == False  # Auto-cleared
```

### **Test 2: Cooldown Timer**
```python
set_cooldown(123, "Trade frequency", 60)  # 60 seconds
assert is_locked_out(123) == True

# Wait 61 seconds
time.sleep(61)
check_expired_lockouts()  # Or timer callback fires
assert is_locked_out(123) == False
```

### **Test 3: Persistence (Crash Recovery)**
```python
set_lockout(123, "Daily loss", datetime(2025, 1, 17, 17, 0))

# Simulate daemon crash
lockout_state.clear()

# Restart daemon
load_lockouts_from_db()

assert is_locked_out(123) == True  # Lockout restored
```

---

## 📋 CLI Integration

**Trader CLI Display:**
```python
# src/cli/trader/lockout_display.py

def display_lockout_status(account_id):
    lockout_info = lockout_manager.get_lockout_info(account_id)

    if lockout_info:
        remaining = lockout_info['remaining_seconds']
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60

        print(f"🔴 LOCKED OUT")
        print(f"Reason: {lockout_info['reason']}")
        print(f"Unlocks in: {hours}h {minutes}m {seconds}s")
    else:
        print(f"🟢 OK TO TRADE")
```

---

## 🔗 Dependencies

- **MOD-003** (timer_manager.py) - For cooldown timers
- **src/state/persistence.py** - SQLite database
- **src/cli/trader/lockout_display.py** - CLI updates

---

**This module ensures consistent lockout behavior across all rules.**
