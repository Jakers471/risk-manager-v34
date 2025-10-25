---
doc_id: RULE-003
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001, MOD-002, MOD-004]
enforcement_type: Hard Lockout (Until Reset)
---

# RULE-003: DailyRealizedLoss

**Purpose:** Enforce hard daily realized P&L limit - stops trading when daily loss threshold is hit.

---

## ⚙️ Configuration

```yaml
daily_realized_loss:
  enabled: true
  limit: -500              # Max daily loss (negative value)
  reset_time: "17:00"      # Daily reset time (5:00 PM)
  timezone: "America/New_York"
  enforcement: "close_all_and_lockout"
  lockout_until_reset: true
```

---

## 🎯 Trigger Condition

**Event Type:** `GatewayUserTrade`

**Logic:**
```python
def check(trade_event):
    # Add this trade's P&L to daily total
    pnl = trade_event['profitAndLoss']
    if pnl is not None:  # Only count full-turn trades
        daily_realized_pnl = pnl_tracker.add_trade_pnl(trade_event['accountId'], pnl)

        if daily_realized_pnl <= config['limit']:
            return BREACH
```

**Example:**
- Trade 1: P&L = +100
- Trade 2: P&L = -200
- Trade 3: P&L = -450
- **Daily Total: -550**
- **Limit: -500**
- **BREACH!**

---

## 🚨 Enforcement Action

**Type:** Hard Lockout (trader CANNOT trade until reset time)

**Action Sequence:**
1. ✅ **Close all positions** (via MOD-001)
2. ✅ **Cancel all orders** (via MOD-001)
3. ✅ **Set lockout** (via MOD-002) → Until `reset_time`
4. ✅ **Log enforcement**
5. ✅ **Update Trader CLI** → Show countdown timer

**Enforcement Code:**
```python
def enforce(account_id, daily_pnl):
    # Close everything
    actions.close_all_positions(account_id)
    actions.cancel_all_orders(account_id)

    # Calculate next reset time
    reset_time = datetime.combine(
        datetime.now().date(),
        time(17, 0)  # 5:00 PM
    )
    if datetime.now() > reset_time:
        reset_time += timedelta(days=1)  # Next day if past 5pm

    # Set lockout until reset
    lockout_manager.set_lockout(
        account_id,
        reason=f"Daily loss limit hit (${daily_pnl:.2f} / ${config['limit']:.2f})",
        until=reset_time
    )

    logger.log_enforcement(f"DailyRealizedLoss LOCKOUT - P&L: ${daily_pnl:.2f}, Limit: ${config['limit']:.2f}")
```

---

## 📡 API Requirements

### **SignalR Event (Trigger):**
```json
{
  "id": 101112,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "price": 21000.75,
  "profitAndLoss": -50.25,    // ← This is what we track
  "fees": 2.50,
  "side": 1,
  "size": 1,
  "orderId": 789
}
```

**Important:** `profitAndLoss` is `null` for half-turn trades (opening position). Only full-turn trades (closing position) have P&L.

### **REST API Calls (Enforcement):**
```http
POST /api/Position/closeContract (for all positions)
POST /api/Order/cancel (for all orders)
```

---

## 🗄️ State Tracking

**SQLite Schema:**
```sql
CREATE TABLE daily_pnl (
    account_id INTEGER PRIMARY KEY,
    realized_pnl REAL DEFAULT 0,
    date DATE DEFAULT CURRENT_DATE
);
```

**State Update:**
```python
def add_trade_pnl(account_id, pnl):
    today = datetime.now().date()

    # Get current daily P&L
    row = db.execute("SELECT realized_pnl FROM daily_pnl WHERE account_id=? AND date=?", (account_id, today))
    current_pnl = row[0] if row else 0

    # Add new trade P&L
    new_pnl = current_pnl + pnl

    # Update database
    db.execute("INSERT OR REPLACE INTO daily_pnl (account_id, realized_pnl, date) VALUES (?, ?, ?)", (account_id, new_pnl, today))

    return new_pnl
```

**Daily Reset (via MOD-004):**
```python
def reset_daily_counters(account_id):
    today = datetime.now().date()
    db.execute("DELETE FROM daily_pnl WHERE account_id=? AND date < ?", (account_id, today))
    db.execute("INSERT INTO daily_pnl (account_id, realized_pnl, date) VALUES (?, 0, ?)", (account_id, today))
```

---

## 🧪 Test Scenarios

### **Test 1: Normal Day**
- Trade 1: +100
- Trade 2: +50
- Trade 3: -200
- **Daily P&L: -50** (within limit of -500)
- **Expected:** No enforcement

### **Test 2: Hit Limit**
- Trade 1: -300
- Trade 2: -250
- **Daily P&L: -550** (exceeds -500)
- **Expected:** LOCKOUT until 5:00 PM

### **Test 3: Reset After Lockout**
- Locked out at 2:00 PM (daily P&L = -550)
- Clock hits 5:00 PM → **Auto-unlock**
- **Expected:** Daily P&L resets to 0, can trade again

### **Test 4: Ignore Half-Turn Trades**
- Open Long MNQ 1 → `profitAndLoss: null`
- **Expected:** No P&L update, no breach check

---

## ⏱️ Lockout Behavior

**While Locked Out:**
- Trader CLI shows: `"🔴 LOCKED OUT - Daily loss limit hit - Reset at 5:00 PM (2h 47m)"`
- If trader somehow places order and it fills → **Close immediately** (event_router catches this)
- All open orders cancelled
- Countdown timer updates every second

**Auto-Unlock:**
- At 5:00 PM (reset_time) → `reset_scheduler.py` calls `reset_daily_counters()`
- `lockout_manager.check_expired_lockouts()` clears lockout
- Trader CLI updates: `"🟢 OK TO TRADE - Daily P&L reset"`

---

## 📋 CLI Display

**Before Breach:**
```
Daily Realized P&L: -$450.00 / -$500.00 ⚠️ (90% of limit)
```

**After Breach (Locked Out):**
```
🔴 LOCKED OUT
Reason: Daily loss limit hit (-$550.00 / -$500.00)
Unlocks at: 5:00 PM (2h 47m remaining)

All positions closed, all orders cancelled.
```

---

## 🔗 Dependencies

- **MOD-001** (actions.py) - close_all_positions(), cancel_all_orders()
- **MOD-002** (lockout_manager.py) - set_lockout(), get_lockout_info()
- **MOD-004** (reset_scheduler.py) - schedule_daily_reset(), reset_daily_counters()
- **pnl_tracker.py** - add_trade_pnl(), get_daily_realized_pnl()

---

**This is a critical safety rule - prevents catastrophic daily losses.**
