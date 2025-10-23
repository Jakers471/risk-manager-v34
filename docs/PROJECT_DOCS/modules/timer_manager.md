---
doc_id: MOD-003
version: 2.0
last_updated: 2025-01-17
dependencies: []
---

# MOD-003: Timer Manager

**Purpose:** Countdown timers for cooldowns, session checks, and scheduled tasks.

**File:** `src/state/timer_manager.py`

---

## 🔧 Public API

### **1. start_timer(name, duration, callback)**
```python
def start_timer(name: str, duration: int, callback: callable) -> None:
    """
    Start countdown timer with callback.

    Args:
        name: Unique timer identifier
        duration: Duration in seconds
        callback: Function to call when timer expires

    Example:
        start_timer("lockout_123", 1800, lambda: clear_lockout(123))
    """
    timers[name] = {
        "expires_at": datetime.now() + timedelta(seconds=duration),
        "callback": callback,
        "duration": duration
    }
```

### **2. get_remaining_time(name)**
```python
def get_remaining_time(name: str) -> int:
    """Get seconds remaining on timer."""
    if name not in timers:
        return 0
    remaining = (timers[name]['expires_at'] - datetime.now()).total_seconds()
    return max(0, int(remaining))
```

### **3. check_timers()**
```python
def check_timers() -> None:
    """Background task: check timers and fire callbacks. Called every second."""
    now = datetime.now()
    expired = []

    for name, timer in timers.items():
        if now >= timer['expires_at']:
            timer['callback']()  # Execute callback
            expired.append(name)

    for name in expired:
        del timers[name]
```

---

**Used By:** MOD-002 (lockout cooldowns), RULE-009 (session timers)
