---
doc_id: RULE-009
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001, MOD-002, MOD-004]
enforcement_type: Hard Lockout (Session-Based)
---

# RULE-009: SessionBlockOutside

**Purpose:** Block trading outside configured session hours and on holidays.

---

## ⚙️ Configuration

```yaml
session_block_outside:
  enabled: true

  # Global session (applies to all unless overridden)
  global_session:
    enabled: true
    start: "09:30"
    end: "16:00"
    timezone: "America/New_York"

  # Per-instrument overrides
  per_instrument_sessions:
    enabled: true
    sessions:
      ES:
        start: "18:00"        # Sunday 6pm
        end: "17:00"          # Friday 5pm
        timezone: "America/Chicago"
      NQ:
        start: "09:30"
        end: "16:00"
        timezone: "America/New_York"

  close_positions_at_session_end: true  # Auto-close positions at end of session
  lockout_outside_session: true         # Hard lockout when outside hours
  respect_holidays: true                # Use holiday calendar
  enforcement: "close_immediately"      # Close any fills outside session
```

**Holiday Calendar (`config/holidays.yaml`):**
```yaml
holidays:
  - "2025-01-01"  # New Year's Day
  - "2025-07-04"  # Independence Day
  - "2025-12-25"  # Christmas
```

---

## 🎯 Trigger Conditions

### **Trigger 1: Position Opens Outside Session**
**Event Type:** `GatewayUserPosition` (when size > 0)

```python
def check_position_event(position_event):
    contract_id = position_event['contractId']
    symbol = extract_symbol(contract_id)

    if not is_within_session(symbol, datetime.now()):
        return BREACH  # Position opened outside session
```

### **Trigger 2: Session End Time Reached**
**Background Task:** Timer check every minute

```python
def check_session_end():
    current_time = datetime.now()

    for symbol, session in sessions.items():
        if current_time >= session['end_time']:
            if config['close_positions_at_session_end']:
                return BREACH  # Close all positions in this symbol
```

### **Trigger 3: Holiday Detected**
```python
def is_holiday(date):
    return date.strftime("%Y-%m-%d") in holiday_calendar
```

---

## 🚨 Enforcement Action

**Action Sequence:**

**If position opens outside session:**
1. ✅ **Close position immediately** (via MOD-001)
2. ✅ **Set lockout** (via MOD-002) → Until session starts
3. ✅ **Cancel all orders**
4. ✅ **Log enforcement**

**At session end (if `close_positions_at_session_end: true`):**
1. ✅ **Close all positions** (via MOD-001)
2. ✅ **Cancel all orders**
3. ✅ **Set lockout** → Until next session start

**Enforcement Code:**
```python
def enforce_outside_session(account_id, contract_id):
    # Close the position that filled outside session
    actions.close_position(account_id, contract_id)
    actions.cancel_all_orders(account_id)

    # Calculate when session starts again
    next_session_start = calculate_next_session_start()

    # Set lockout
    lockout_manager.set_lockout(
        account_id,
        reason=f"Trading outside session hours",
        until=next_session_start
    )

def enforce_session_end(account_id):
    # Close all positions at end of session
    actions.close_all_positions(account_id)
    actions.cancel_all_orders(account_id)

    # Set lockout until next session
    next_session_start = calculate_next_session_start()
    lockout_manager.set_lockout(
        account_id,
        reason="Session ended - auto-closed all positions",
        until=next_session_start
    )
```

---

## 📡 API Requirements

### **SignalR Event (Trigger):**
```json
{
  "id": 456,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "creationTimestamp": "2025-01-17T20:00:00Z",  // 8:00 PM (outside 9:30-16:00)
  "type": 1,
  "size": 2
}
```

### **REST API Calls (Enforcement):**
```http
POST /api/Position/closeContract
{
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25"
}

POST /api/Order/cancel (for all orders)
```

---

## ⏰ Session Time Logic

### **Global Session Example:**
```python
# Config: 09:30 - 16:00 America/New_York
def is_within_session(symbol, current_time):
    if not config['global_session']['enabled']:
        return True

    tz = timezone(config['global_session']['timezone'])
    local_time = current_time.astimezone(tz)

    session_start = time(9, 30)
    session_end = time(16, 0)

    # Check if within session
    if session_start <= local_time.time() <= session_end:
        # Also check holidays
        if config['respect_holidays'] and is_holiday(local_time.date()):
            return False  # Market closed (holiday)
        return True  # Within session
    else:
        return False  # Outside session
```

### **Per-Instrument Override Example:**
```python
# ES: Sunday 18:00 - Friday 17:00 (nearly 24/5)
def is_within_session_es(current_time):
    # ES trades Sunday 6pm - Friday 5pm
    tz = timezone("America/Chicago")
    local_time = current_time.astimezone(tz)

    day_of_week = local_time.weekday()  # 0=Monday, 6=Sunday
    hour = local_time.hour

    # Sunday 18:00 onwards
    if day_of_week == 6 and hour >= 18:
        return True

    # Monday-Thursday (all day)
    if 0 <= day_of_week <= 3:
        return True

    # Friday until 17:00
    if day_of_week == 4 and hour < 17:
        return True

    return False  # Outside session
```

---

## 🗄️ State Tracking

**Track session status:**
```python
session_state = {
    "current_session": "open",  # "open", "closed", "holiday"
    "next_session_start": datetime(2025, 1, 18, 9, 30),
    "next_session_end": datetime(2025, 1, 18, 16, 0)
}
```

**Background Timer:**
```python
# Check every minute
def check_session_status():
    if is_session_end_reached():
        if config['close_positions_at_session_end']:
            enforce_session_end(account_id)
```

---

## 🧪 Test Scenarios

### **Test 1: Trade During Session**
- Time: 10:00 AM (within 9:30-16:00)
- Open Long MNQ 1
- **Expected:** No enforcement

### **Test 2: Trade Outside Session**
- Time: 8:00 PM (outside 9:30-16:00)
- Open Long MNQ 1
- **Expected:** Position closed immediately, LOCKOUT until 9:30 AM

### **Test 3: Session End Auto-Close**
- Time: 3:59 PM (position open)
- Clock hits 4:00 PM
- **Expected:** All positions closed, LOCKOUT until 9:30 AM next day

### **Test 4: Holiday**
- Date: 2025-12-25 (Christmas)
- Time: 10:00 AM
- Attempt to trade
- **Expected:** Close immediately, LOCKOUT (market closed)

### **Test 5: Per-Instrument Override**
- Symbol: ES (session: 18:00 Sun - 17:00 Fri)
- Time: Monday 10:00 AM
- **Expected:** OK to trade (ES has extended hours)

---

## 📋 CLI Display

**During Session:**
```
Session Status: 🟢 OPEN
Current Session: 9:30 AM - 4:00 PM ET
Session Ends In: 3h 27m
```

**Outside Session:**
```
🔴 LOCKED OUT
Reason: Trading outside session hours
Next Session: Tomorrow 9:30 AM ET (14h 27m)
```

**On Holiday:**
```
🔴 LOCKED OUT
Reason: Market closed (Holiday: Christmas)
Next Session: Monday 9:30 AM ET
```

---

## 🔗 Dependencies

- **MOD-001** (actions.py) - close_all_positions(), close_position(), cancel_all_orders()
- **MOD-002** (lockout_manager.py) - set_lockout()
- **MOD-003** (timer_manager.py) - Session end timer
- **MOD-004** (reset_scheduler.py) - Holiday calendar integration
- **utils/datetime_helpers.py** - Timezone conversion
- **utils/holidays.py** - Holiday calendar

---

**This rule ensures compliance with trading hours and prevents after-hours violations.**
