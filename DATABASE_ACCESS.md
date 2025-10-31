# Database Access Guide

**Location**: `C:\Users\jakers\Desktop\risk-manager-v34\data\risk_state.db`

---

## 🔧 Quick Access Tool

Use the **`view_database.py`** script to view lockouts, timers, P&L, and trades:

### View Everything
```bash
python view_database.py
```

### View Specific Data
```bash
python view_database.py lockouts    # Show active + historical lockouts
python view_database.py pnl         # Show P&L tracking
python view_database.py trades      # Show recent trades
python view_database.py timers      # Show active timers
```

---

## 📊 Database Tables

### 1. **lockouts** - Account Lockout State

**Columns**:
- `id` - Primary key
- `account_id` - Trading account ID
- `rule_id` - Rule that created lockout (e.g., "MANUAL", "RULE-003")
- `reason` - Why the lockout was created
- `locked_at` - When lockout was created (UTC timestamp)
- `expires_at` - When lockout expires (UTC timestamp)
- `unlock_condition` - Condition for unlock (optional)
- `active` - 1 = active, 0 = expired
- `created_at` - Record creation timestamp

**Purpose**:
- Stores hard lockouts (daily realized loss, profit targets)
- Persists across crashes/restarts
- PRE-CHECK layer reads from this table

**Example**:
```
Lockout ID: 1
  Account:    13298777
  Rule:       MANUAL
  Reason:     Daily loss limit exceeded: $-170.50 (limit: $-5.00)
  Locked at:  2025-10-31T17:21:19+00:00
  Expires at: 2025-10-31T21:00:00+00:00
  Remaining:  12361s (3h 26m)
  Active:     YES
```

---

### 2. **timers** - Duration-Based Timers

**Columns**:
- `id` - Primary key
- `account_id` - Trading account ID
- `rule_id` - Rule that created timer
- `reason` - Timer purpose
- `started_at` - When timer started (UTC)
- `expires_at` - When timer expires (UTC)
- `duration_seconds` - Original duration in seconds
- `active` - 1 = active, 0 = expired
- `created_at` - Record creation timestamp

**Purpose**:
- Stores cooldown timers (trade frequency, cooldown after loss)
- Auto-expires after duration
- Background task checks for expiry

**Example**:
```
Timer ID: 5
  Account:   13298777
  Rule:      RULE-006
  Reason:    Trade frequency limit exceeded (4 trades in 60s)
  Duration:  60s
  Started:   2025-10-31T17:15:00+00:00
  Expires:   2025-10-31T17:16:00+00:00
  Remaining: 30s
  Active:    YES
```

---

### 3. **daily_pnl** - Daily P&L Tracking

**Columns**:
- `id` - Primary key
- `account_id` - Trading account ID
- `date` - Trading date (YYYY-MM-DD)
- `realized_pnl` - Total realized P&L for the day
- `trade_count` - Number of trades
- `created_at` - Record creation timestamp
- `updated_at` - Last update timestamp

**Purpose**:
- Tracks daily realized P&L (from closed trades)
- Used by RULE-003 (daily realized loss) and RULE-013 (daily realized profit)
- Resets daily at configured reset time

**Example**:
```
Account: 13298777 | Date: 2025-10-31
  Realized P&L: $-170.50
  Trade Count:  19
  Last Update:  2025-10-31T17:21:19+00:00
```

---

### 4. **trades** - Trade History

**Columns**:
- `id` - Primary key
- `account_id` - Trading account ID
- `trade_id` - Broker's trade ID
- `symbol` - Instrument symbol (e.g., MNQ, ES)
- `side` - BUY or SELL
- `quantity` - Number of contracts
- `price` - Execution price
- `realized_pnl` - Realized P&L from this trade
- `timestamp` - Trade execution time (UTC)
- `created_at` - Record creation timestamp

**Purpose**:
- Historical trade record
- Used for analysis and audit
- NOT directly used by risk rules (rules use daily_pnl)

---

### 5. **reset_log** - Daily Reset History

**Columns**:
- `id` - Primary key
- `account_id` - Trading account ID
- `reset_type` - Type of reset (e.g., "daily_pnl", "daily_lockout")
- `reset_time` - Configured reset time
- `triggered_at` - When reset was triggered (UTC)
- `created_at` - Record creation timestamp

**Purpose**:
- Log of daily reset events
- Audit trail for P&L resets
- Debugging reset behavior

---

## 🛠️ Advanced Access (SQL)

### Using SQLite Command Line

```bash
# Open database
sqlite3 data/risk_state.db

# Show tables
.tables

# Show schema
.schema lockouts

# Query active lockouts
SELECT * FROM lockouts WHERE active = 1;

# Query today's P&L
SELECT * FROM daily_pnl WHERE date = '2025-10-31';

# Exit
.quit
```

---

### Using Python

```python
import sqlite3

# Connect to database
conn = sqlite3.connect('data/risk_state.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Query active lockouts
cursor.execute('SELECT * FROM lockouts WHERE active = 1')
lockouts = cursor.fetchall()

for lockout in lockouts:
    print(f"Account {lockout['account_id']} locked until {lockout['expires_at']}")

conn.close()
```

---

### Using DB Browser for SQLite (GUI)

**Download**: https://sqlitebrowser.org/

1. Open `DB Browser for SQLite`
2. File → Open Database
3. Navigate to: `C:\Users\jakers\Desktop\risk-manager-v34\data\risk_state.db`
4. Browse tables, execute SQL queries, export data

---

## 🔍 Common Queries

### Check if Account is Locked Out
```sql
SELECT
    account_id,
    reason,
    expires_at,
    (julianday(expires_at) - julianday('now')) * 86400 as remaining_seconds
FROM lockouts
WHERE account_id = '13298777'
  AND active = 1
  AND expires_at > datetime('now');
```

### View Today's P&L
```sql
SELECT account_id, realized_pnl, trade_count
FROM daily_pnl
WHERE date = date('now');
```

### View All Active Timers
```sql
SELECT
    account_id,
    rule_id,
    reason,
    (julianday(expires_at) - julianday('now')) * 86400 as remaining_seconds
FROM timers
WHERE active = 1
  AND expires_at > datetime('now');
```

### View Recent Trade History
```sql
SELECT
    timestamp,
    symbol,
    side,
    quantity,
    price,
    realized_pnl
FROM trades
ORDER BY timestamp DESC
LIMIT 20;
```

---

## 🚨 Important Notes

### Read-Only Access
- **Always use read-only access** when querying the database while the system is running
- Modifying data while the system is running can cause corruption or crashes

### Backup Before Modifying
```bash
# Create backup
cp data/risk_state.db data/risk_state.db.backup

# Restore from backup
cp data/risk_state.db.backup data/risk_state.db
```

### Timestamps
- All timestamps are stored in **UTC** (ISO 8601 format)
- Convert to local time zone when displaying to users

---

## 📈 Monitoring Lockout State

### Watch for Active Lockouts (Real-time)
```bash
# Run in loop to monitor
while true; do
    clear
    python view_database.py lockouts
    sleep 5
done
```

### Check Expiry Status
```bash
# Show lockouts that will expire in next hour
python -c "
import sqlite3
from datetime import datetime, timedelta, timezone

conn = sqlite3.connect('data/risk_state.db')
cursor = conn.cursor()

now = datetime.now(timezone.utc)
one_hour = now + timedelta(hours=1)

cursor.execute('''
    SELECT account_id, reason, expires_at
    FROM lockouts
    WHERE active = 1
      AND expires_at > ?
      AND expires_at < ?
''', (now.isoformat(), one_hour.isoformat()))

for row in cursor.fetchall():
    print(f'Account {row[0]} lockout expires at {row[2]}')

conn.close()
"
```

---

## 🔐 Manual Lockout Management

### Manually Lock Account (Emergency)
```python
import sqlite3
from datetime import datetime, timezone, timedelta

conn = sqlite3.connect('data/risk_state.db')
cursor = conn.cursor()

# Lock account for 1 hour
account_id = '13298777'
reason = 'Manual emergency lockout'
expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

cursor.execute('''
    INSERT INTO lockouts (account_id, rule_id, reason, locked_at, expires_at, active, created_at)
    VALUES (?, ?, ?, ?, ?, 1, ?)
''', (account_id, 'MANUAL', reason, datetime.now(timezone.utc).isoformat(), expires_at, datetime.now(timezone.utc).isoformat()))

conn.commit()
conn.close()

print(f'Account {account_id} locked until {expires_at}')
```

### Manually Unlock Account (Emergency)
```python
import sqlite3

conn = sqlite3.connect('data/risk_state.db')
cursor = conn.cursor()

# Unlock account
account_id = '13298777'

cursor.execute('''
    UPDATE lockouts
    SET active = 0
    WHERE account_id = ? AND active = 1
''', (account_id,))

conn.commit()
conn.close()

print(f'Account {account_id} unlocked')
```

**⚠️ WARNING**: Only use manual unlock in emergencies! System will restore lockout on restart if triggered condition still exists.

---

## 📊 Database Size & Maintenance

### Check Database Size
```bash
ls -lh data/risk_state.db
```

### Vacuum Database (Optimize)
```bash
sqlite3 data/risk_state.db "VACUUM;"
```

### Archive Old Data
```bash
# Archive trades older than 30 days
python -c "
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/risk_state.db')
cursor = conn.cursor()

thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()

cursor.execute('DELETE FROM trades WHERE timestamp < ?', (thirty_days_ago,))
cursor.execute('DELETE FROM reset_log WHERE triggered_at < ?', (thirty_days_ago,))

conn.commit()
print(f'Deleted {cursor.rowcount} old records')
conn.close()
"
```

---

## ✅ Quick Reference

| Task | Command |
|------|---------|
| View all data | `python view_database.py` |
| View lockouts only | `python view_database.py lockouts` |
| View P&L only | `python view_database.py pnl` |
| View trades only | `python view_database.py trades` |
| View timers only | `python view_database.py timers` |
| Open in SQL | `sqlite3 data/risk_state.db` |
| Backup database | `cp data/risk_state.db data/risk_state.db.backup` |
| Check size | `ls -lh data/risk_state.db` |

---

**Last Updated**: 2025-10-31
**Database Version**: 1.0
**Location**: `data/risk_state.db`
