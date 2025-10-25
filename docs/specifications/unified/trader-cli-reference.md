# Trader CLI Reference

**Wave 3 Unified Specification**
**Date:** 2025-10-25
**Authority:** User-provided requirements (CONFLICTS-FOR-USER-REVIEW.md)
**Purpose:** Complete Trader CLI command reference (read-only, no UAC required)

---

## Overview

The Trader CLI provides view-only access to monitor risk status, P&L, enforcement logs, and lockout information. Trader CLI runs as normal user (no admin privileges required).

**Key Principles:**
- ✅ Trader views configured settings (read-only)
- ✅ Trader views live unrealized P&L (floating) + realized P&L
- ✅ Trader views enforcement logs (WHY position was closed, which rule breached)
- ✅ Trader can clock in/out
- ✅ Trader views holidays, current time, market hours
- ✅ Trader views lockout status and reason
- ✅ Trader views if account is being monitored (daemon running?)
- ❌ Trader CANNOT pause/stop daemon
- ❌ Trader CANNOT modify any settings
- ❌ Trader CANNOT request admin unlock (no ticket system)
- ❌ Trader CANNOT view verbose logs (just breach reasons)

---

## Security Model

### No Elevation Required

**Trader CLI runs as normal user:**

```bash
# Normal PowerShell or Terminal (no admin rights needed)
risk-manager trader <command>
```

**File Permissions:**
- **Config files:** Read-only (cannot modify)
- **Database:** Read-only queries (cannot write)
- **Logs:** Read-only (filtered, no DEBUG level)
- **Daemon control:** None (cannot start/stop)

**Protection:**
- Windows ACL prevents file modification
- Daemon runs as Windows Service (trader cannot kill)
- Config changes require admin password (UAC)

---

## Command Reference

### 1. Status - Live Snapshot

View current account status, P&L, positions, and risk utilization.

#### `risk-manager trader status`

Display live snapshot of account status.

**Usage:**
```bash
risk-manager trader status
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  Account Status                                            ║
╚════════════════════════════════════════════════════════════╝

Account:     DEMO-12345
Status:      ✅ ACTIVE (monitoring enabled)
Daemon:      ✅ RUNNING (PID: 12345)

╔════════════════════════════════════════════════════════════╗
║  P&L Summary                                               ║
╚════════════════════════════════════════════════════════════╝

Realized P&L (Today):    +$450.00
Unrealized P&L (Live):   -$125.50
Total P&L (Today):       +$324.50

Daily Limit:             -$1000.00
Current Utilization:     32% ████░░░░░░░░░░░░░░

╔════════════════════════════════════════════════════════════╗
║  Current Positions                                         ║
╚════════════════════════════════════════════════════════════╝

Symbol  Side   Qty  Entry Price   Current Price   Unrealized P&L
MNQ     LONG   2    14250.00      14225.00        -$125.50
ES      -      -    -             -               -

╔════════════════════════════════════════════════════════════╗
║  Risk Rules                                                ║
╚════════════════════════════════════════════════════════════╝

Rule                       Limit        Current      Status
Max Contracts              5            2            ████░░ 40%
Daily Realized Loss        -$1000       -$450        ████░░ 45%
Daily Unrealized Loss      -$500        -$125.50     ██░░░░ 25%
Trade Frequency (hour)     10 trades    3 trades     ███░░░ 30%

╔════════════════════════════════════════════════════════════╗
║  Lockouts                                                  ║
╚════════════════════════════════════════════════════════════╝

Status: ✅ No active lockouts

╔════════════════════════════════════════════════════════════╗
║  Market Info                                               ║
╚════════════════════════════════════════════════════════════╝

Current Time:    2:15 PM CT (Chicago)
Market Status:   ✅ OPEN
Session Window:  8:30 AM - 3:00 PM CT
Next Reset:      5:00 PM CT (in 2 hours 45 minutes)
```

**User Guidance:** "they can see a live snapshot of their floating unrealised pnl and realised pnl. they can see logs for WHY A POSITION WAS ENFORCED, SHOWING WHAT RISK RULE WAS BREACHED!"

---

#### `risk-manager trader status --live`

Live updating status (refreshes every 5 seconds).

**Usage:**
```bash
risk-manager trader status --live
```

**Behavior:**
- Auto-refresh every 5 seconds
- Press Ctrl+C to exit
- Shows real-time P&L changes
- Updates position prices

---

### 2. P&L - Realized and Unrealized

View detailed P&L breakdown.

#### `risk-manager trader pnl`

Display P&L summary.

**Usage:**
```bash
risk-manager trader pnl
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  P&L Breakdown                                             ║
╚════════════════════════════════════════════════════════════╝

Today (2025-10-25):
  Realized P&L:     +$450.00  (from 5 closed trades)
  Unrealized P&L:   -$125.50  (from 1 open position)
  Total P&L:        +$324.50

Limits:
  Realized Loss:    -$1000.00  (45% utilized)
  Unrealized Loss:  -$500.00   (25% utilized)

╔════════════════════════════════════════════════════════════╗
║  Realized P&L by Instrument                                ║
╚════════════════════════════════════════════════════════════╝

Symbol    Trades    Realized P&L
MNQ       3         +$300.00
ES        2         +$150.00
Total     5         +$450.00

╔════════════════════════════════════════════════════════════╗
║  Unrealized P&L (Open Positions)                           ║
╚════════════════════════════════════════════════════════════╝

Symbol  Side   Entry       Current     Unrealized P&L
MNQ     LONG   14250.00    14225.00    -$125.50
```

**User Guidance (CONFLICT-001):**
- "unrelaised loss/profit are trade by trade"
- "realised profit/loss for daily IS on a lockout"
- "when the total REALISED + UNREALISED COME TOGETHER TO HIT MY REALISED, IT CLOSES ALL POSITIONS ACCOUNT WIDE"

---

### 3. Enforcement Logs

View enforcement actions (WHY positions were closed).

#### `risk-manager trader logs`

Display enforcement logs (breach reasons).

**Usage:**
```bash
risk-manager trader logs
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  Enforcement Logs (Last 10 Events)                         ║
╚════════════════════════════════════════════════════════════╝

Timestamp           Rule                        Action                Reason
─────────────────────────────────────────────────────────────────────────────
2025-10-25 14:15    Daily Unrealized Loss       CLOSE_POSITION MNQ    Unrealized loss -$505 exceeded limit -$500
2025-10-25 13:45    Max Contracts               DENY_TRADE            Contract limit 5 reached
2025-10-25 12:30    Trade Frequency (hour)      HARD_LOCKOUT          10 trades in 1 hour (limit: 10)
2025-10-25 11:00    Daily Realized Loss         CLOSE_ALL + LOCKOUT   Realized+Unrealized = -$1005 (limit: -$1000)
2025-10-25 10:15    Session Block (Outside)     DENY_TRADE            Trading outside session window (8:30-15:00)

Legend:
  CLOSE_POSITION    = Closed specific position (trade-by-trade)
  CLOSE_ALL         = Closed all positions account-wide (hard lockout)
  LOCKOUT           = Account locked until reset
  DENY_TRADE        = Trade blocked (no enforcement needed)
```

**Options:**
```bash
# Filter by level
risk-manager trader logs --level WARNING
risk-manager trader logs --level ERROR

# Tail last N lines
risk-manager trader logs --tail 50

# Search by keyword
risk-manager trader logs --search "Daily Realized Loss"
```

**User Guidance:** "they can see logs for WHY A POSITION WAS ENFORCED, SHOWING WHAT RISK RULE WAS BREACHED! no verbose."

**Note:** Trader does NOT see DEBUG level logs (admin-only).

---

### 4. Lockouts - Current Status

View current lockout status and countdown.

#### `risk-manager trader lockouts`

Display active lockouts.

**Usage:**
```bash
risk-manager trader lockouts
```

**Output (No Lockouts):**
```
╔════════════════════════════════════════════════════════════╗
║  Lockout Status                                            ║
╚════════════════════════════════════════════════════════════╝

Status: ✅ No active lockouts
You are free to trade.
```

**Output (Active Lockout):**
```
╔════════════════════════════════════════════════════════════╗
║  Lockout Status                                            ║
╚════════════════════════════════════════════════════════════╝

⚠️  ACCOUNT LOCKED

Rule:             Daily Realized Loss
Reason:           Realized+Unrealized = -$1005 (limit: -$1000)
Locked Since:     2025-10-25 11:00:00 CT
Expires At:       2025-10-25 17:00:00 CT (daily reset)
Time Remaining:   6 hours 0 minutes

Type:             Hard Lockout
Behavior:         All positions closed, new trades blocked until reset

Unlock Mechanism: Automatic at daily reset (5:00 PM CT)
```

**User Guidance (CONFLICT-005):** "ADMIN DOESNT UNLOCK RISK SETTING LOCKOUTS, THEY ARE ON A TIMER/SCHEDULE, AUTO CONTROLLED EVERYDAY."

---

### 5. Rules - View Configured Limits

View risk rules and current utilization.

#### `risk-manager trader rules`

Display all risk rules and their status.

**Usage:**
```bash
risk-manager trader rules
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  Risk Rules Configuration                                  ║
╚════════════════════════════════════════════════════════════╝

Rule                       Status      Limit        Current      Utilization
────────────────────────────────────────────────────────────────────────────
Max Contracts              ✅ Enabled   5            2            ████░░ 40%
Daily Realized Loss        ✅ Enabled   -$1000       -$450        ████░░ 45%
Daily Realized Profit      ✅ Enabled   +$1000       +$0          ░░░░░░ 0%
Daily Unrealized Loss      ✅ Enabled   -$500        -$125.50     ██░░░░ 25%
Max Unrealized Profit      ✅ Enabled   +$500        +$0          ░░░░░░ 0%
Trade Frequency (hour)     ✅ Enabled   10 trades    3 trades     ███░░░ 30%
Trade Frequency (day)      ❌ Disabled  20 trades    -            -
Max Loss Per Trade         ✅ Enabled   -$200        -$125.50     ████░░ 63%
Session Block (Outside)    ✅ Enabled   8:30-15:00   INSIDE       ✅ OK
Auth Loss Guard            ✅ Enabled   API-based    -            ✅ OK
Position Monitor (Stale)   ✅ Enabled   30s timeout  -            ✅ OK
Symbol Blocks              ❌ Disabled  []           -            -

Color Legend:
  GREEN  (<50%):  ████░░░░░░  Safe
  YELLOW (50-80%): ██████░░░░  Warning
  RED    (>80%):   ████████░░  Near Limit
```

**User Guidance:** "they can see whats settings are configured"

**Note:** Trader can view but NOT edit. To change limits, admin must use `risk-manager admin config set`.

---

### 6. Market Hours & Time

View current time, market status, session windows.

#### `risk-manager trader market-hours`

Display market hours and session windows.

**Usage:**
```bash
risk-manager trader market-hours
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  Market Hours                                              ║
╚════════════════════════════════════════════════════════════╝

Current Time:     2:15 PM CT (Chicago)
Timezone:         America/Chicago (Central Time)

Market Status:    ✅ OPEN

Session Window:
  Start:          8:30 AM CT
  End:            3:00 PM CT
  Status:         ✅ INSIDE (trading allowed)
  Remaining:      45 minutes until session close

Daily Reset:
  Time:           5:00 PM CT
  Next Reset:     2025-10-25 17:00:00 CT (in 2 hours 45 minutes)

Holidays (Next 7 Days):
  No holidays
```

**User Guidance:** "they can see holidays, current time, when market opens or closes or is active"

---

### 7. Clock In/Out

Track trading session time (optional time tracking).

#### `risk-manager trader clock-in`

Clock in to start tracking session time.

**Usage:**
```bash
risk-manager trader clock-in
```

**Output:**
```
✅ Clocked in at 8:30 AM CT
📊 Session tracking started
```

---

#### `risk-manager trader clock-out`

Clock out to end session tracking.

**Usage:**
```bash
risk-manager trader clock-out
```

**Output:**
```
✅ Clocked out at 2:45 PM CT

Session Summary:
  Clock In:       8:30 AM CT
  Clock Out:      2:45 PM CT
  Duration:       6 hours 15 minutes
  Trades:         5
  Realized P&L:   +$450.00
```

**User Guidance:** "they can clock in and out"

---

### 8. Daemon Status

Check if daemon is running (account being monitored?).

#### `risk-manager trader daemon-status`

Check if Risk Manager daemon is active.

**Usage:**
```bash
risk-manager trader daemon-status
```

**Output (Running):**
```
╔════════════════════════════════════════════════════════════╗
║  Daemon Status                                             ║
╚════════════════════════════════════════════════════════════╝

Status:           ✅ RUNNING
Monitoring:       ✅ ACTIVE
Your Account:     DEMO-12345
Last Check:       2 seconds ago
SDK Connection:   ✅ Connected

🛡️  Your account is being protected by risk management.
```

**Output (Not Running):**
```
╔════════════════════════════════════════════════════════════╗
║  Daemon Status                                             ║
╚════════════════════════════════════════════════════════════╝

Status:           ❌ NOT RUNNING
Monitoring:       ❌ INACTIVE

⚠️  WARNING: Your account is NOT being monitored!
⚠️  Risk enforcement is DISABLED.

Contact admin to start the Risk Manager daemon.
```

**User Guidance:** "or if its not locked out. if accounts arent being monitored, then we need to fix the code."

---

## Restrictions

### What Trader CANNOT Do

**Daemon Control:**
- ❌ Cannot start/stop/restart daemon
- ❌ Cannot pause monitoring
- ❌ Cannot kill daemon process (UAC protected)

**Configuration:**
- ❌ Cannot modify risk limits
- ❌ Cannot enable/disable rules
- ❌ Cannot change reset times
- ❌ Cannot edit config files (ACL protected)

**Lockouts:**
- ❌ Cannot manually unlock account
- ❌ Cannot request admin unlock (no ticket system)
- ❌ Cannot bypass lockouts

**Logs:**
- ❌ Cannot view DEBUG level logs
- ❌ Cannot clear logs
- ❌ Cannot modify logs

**User Guidance (CONFLICT-007):** "TRADER cannot pause the daemon or risk manager, its always active only the admin can start/stop it. no tickets for requesting."

---

## Workflow Examples

### Morning Routine

```bash
# 1. Check daemon is running
risk-manager trader daemon-status

# 2. View current status
risk-manager trader status

# 3. Check rules and limits
risk-manager trader rules

# 4. Clock in
risk-manager trader clock-in

# 5. Start trading (via TopstepX platform)
```

---

### During Trading

```bash
# Live status (auto-refresh every 5s)
risk-manager trader status --live

# Check P&L
risk-manager trader pnl

# Check if near any limits
risk-manager trader rules
```

---

### After Breach

```bash
# 1. Check lockout status
risk-manager trader lockouts

# 2. View enforcement logs (WHY was I locked out?)
risk-manager trader logs

# 3. View when lockout expires
risk-manager trader lockouts

# 4. Wait for automatic unlock (no manual unlock available)
```

---

### End of Day

```bash
# 1. Clock out
risk-manager trader clock-out

# 2. View final P&L
risk-manager trader pnl

# 3. View enforcement history
risk-manager trader logs

# 4. Wait for daily reset (5:00 PM CT)
```

---

## Implementation Notes

### No UAC Required

**File:** `src/risk_manager/cli/trader/__init__.py`

```python
import typer

app = typer.Typer()

@app.callback()
def main():
    """Trader CLI - View-only, no admin rights required."""
    # No UAC check needed
    pass

# Add subcommands
from . import status, pnl, logs, lockouts, rules, market_hours, clock
app.add_typer(status.app, name="status")
app.add_typer(pnl.app, name="pnl")
app.add_typer(logs.app, name="logs")
app.add_typer(lockouts.app, name="lockouts")
app.add_typer(rules.app, name="rules")
app.add_typer(market_hours.app, name="market-hours")
app.add_typer(clock.app, name="clock-in")
app.add_typer(clock.app, name="clock-out")
```

### Database Access (Read-Only)

**File:** `src/risk_manager/cli/trader/status.py`

```python
from risk_manager.state.database import Database

db = Database(db_path="data/risk_manager.db")

# Read-only queries
realized_pnl = db.get_daily_realized_pnl(account_id)
unrealized_pnl = db.get_unrealized_pnl(account_id)
lockouts = db.get_active_lockouts(account_id)
violations = db.get_violations(account_id, limit=10)
```

**No write operations allowed from trader CLI.**

---

## Summary

**Trader CLI provides:**
1. ✅ Live status snapshot (P&L, positions, rules)
2. ✅ Detailed P&L breakdown (realized, unrealized, by instrument)
3. ✅ Enforcement logs (WHY position closed, which rule breached)
4. ✅ Lockout status (reason, expires at, countdown)
5. ✅ Rules view (configured limits, current utilization)
6. ✅ Market hours (session windows, current time, holidays)
7. ✅ Clock in/out (session time tracking)
8. ✅ Daemon status (is account being monitored?)
9. ❌ NO daemon control (cannot start/stop)
10. ❌ NO config modification (cannot change limits)
11. ❌ NO manual unlock (automatic timers only)

**Security:**
- No UAC required (runs as normal user)
- Read-only database access
- Config files readable but not writable
- Cannot kill daemon (UAC protected)
- Logs filtered (no DEBUG level)

**Next Steps:**
- Implement trader commands in `src/risk_manager/cli/trader/`
- Add read-only database queries
- Add live TUI with Rich Live display
- Test file permissions (ACL protection)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-25
**Status:** Unified specification (ready for implementation)
