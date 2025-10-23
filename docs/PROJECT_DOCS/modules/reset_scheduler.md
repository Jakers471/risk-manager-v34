---
doc_id: MOD-004
version: 2.0
last_updated: 2025-01-17
dependencies: []
---

# MOD-004: Reset Scheduler

**Purpose:** Daily reset logic for P&L counters and holiday calendar integration.

**File:** `src/state/reset_scheduler.py`

---

## 🔧 Public API

### **1. schedule_daily_reset(reset_time, timezone)**
```python
def schedule_daily_reset(reset_time: str = "17:00", timezone: str = "America/New_York") -> None:
    """
    Schedule daily reset at specific time.

    Args:
        reset_time: Time in "HH:MM" format (24-hour)
        timezone: IANA timezone string

    Example:
        schedule_daily_reset("17:00", "America/New_York")  # 5:00 PM ET
    """
    reset_config['time'] = reset_time
    reset_config['timezone'] = timezone
    logger.info(f"Daily reset scheduled for {reset_time} {timezone}")
```

### **2. reset_daily_counters(account_id)**
```python
def reset_daily_counters(account_id: int) -> None:
    """
    Reset all daily counters (P&L, trade counts).

    Args:
        account_id: TopstepX account ID
    """
    # Reset P&L
    db.execute("UPDATE daily_pnl SET realized_pnl=0, unrealized_pnl=0 WHERE account_id=?", (account_id,))

    # Clear daily lockouts
    lockout_manager.clear_lockout(account_id)

    logger.info(f"Daily counters reset for account {account_id}")
```

### **3. check_reset_time()**
```python
def check_reset_time() -> None:
    """Background task: check if reset time reached. Called every minute."""
    tz = timezone(reset_config['timezone'])
    now = datetime.now(tz)
    reset_time = time.fromisoformat(reset_config['time'])

    if now.time() >= reset_time and not reset_triggered_today:
        reset_daily_counters(account_id)
        reset_triggered_today = True
```

### **4. is_holiday(date)**
```python
def is_holiday(date: datetime) -> bool:
    """Check if date is a trading holiday."""
    return date.strftime("%Y-%m-%d") in holiday_calendar
```

**Holiday Calendar (`config/holidays.yaml`):**
```yaml
holidays:
  - "2025-01-01"  # New Year's Day
  - "2025-07-04"  # Independence Day
  - "2025-12-25"  # Christmas
```

---

**Used By:** RULE-003, 004, 005 (daily P&L rules), RULE-009 (session/holiday checks)
