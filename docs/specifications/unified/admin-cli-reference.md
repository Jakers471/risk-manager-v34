# Admin CLI Reference

**Wave 3 Unified Specification**
**Date:** 2025-10-25
**Authority:** User-provided requirements (CONFLICTS-FOR-USER-REVIEW.md)
**Purpose:** Complete Admin CLI command reference with UAC security

---

## Overview

The Admin CLI provides privileged access to configure risk settings, monitor the daemon, and control the system. All admin commands require Windows UAC elevation (admin password).

**Key Principles:**
- ✅ Admin configures API credentials
- ✅ Admin configures account IDs to monitor
- ✅ Admin configures risk rules (enable/disable, set limits)
- ✅ Admin configures timers/schedules (reset times, lockout durations)
- ✅ Admin starts/stops/restarts daemon
- ✅ Admin checks daemon status
- ❌ Admin does NOT manually unlock trading lockouts (timer-based only)
- ❌ Admin does NOT need emergency stop (stopping daemon IS the stop)
- ❌ Admin does NOT need ticket system

---

## Security Model

### UAC Elevation Required

**All admin commands require Windows admin privileges:**

```bash
# Windows: Right-click PowerShell → "Run as Administrator" → Enter admin password
# Linux/Mac: Run with sudo
risk-manager admin <command>
```

**If not elevated:**
```
❌ Error: Admin CLI requires administrator privileges

🔐 This protects you from making changes while locked out.

To access Admin CLI:
  1. Right-click PowerShell or Terminal
  2. Select 'Run as Administrator'
  3. Windows will prompt for admin password
  4. Enter your Windows admin password
  5. Run 'risk-manager admin' again
```

**Implementation:**
- Windows: `ctypes.windll.shell32.IsUserAnAdmin()`
- Linux/Mac: Check `os.geteuid() == 0`

---

## Command Reference

### 1. API Credentials

Configure TopstepX API connection.

#### `risk-manager admin api set-credentials`

Set API key and secret for TopstepX SDK connection.

**Usage:**
```bash
risk-manager admin api set-credentials --key <API_KEY> --secret <API_SECRET>
```

**Options:**
- `--key`: TopstepX API key (required)
- `--secret`: TopstepX API secret (required)
- `--validate`: Test connection before saving (optional)

**Example:**
```bash
risk-manager admin api set-credentials \
  --key "your-api-key" \
  --secret "your-api-secret" \
  --validate
```

**Output:**
```
✅ API credentials saved to config/api_credentials.yaml
✅ Connection test successful
🔄 Restart daemon to apply changes: risk-manager admin daemon restart
```

**File Modified:** `config/api_credentials.yaml`

**Security:**
- Credentials stored encrypted
- File protected by Windows ACL (admin-only read/write)
- Trader cannot view credentials

---

#### `risk-manager admin api set-account`

Add account ID to monitor.

**Usage:**
```bash
risk-manager admin api set-account <ACCOUNT_ID>
```

**Arguments:**
- `ACCOUNT_ID`: TopstepX account ID to monitor

**Options:**
- `--description`: Human-readable description (optional)
- `--validate`: Verify account exists via API (optional)

**Example:**
```bash
risk-manager admin api set-account DEMO-12345 \
  --description "Trader account" \
  --validate
```

**Output:**
```
✅ Account DEMO-12345 added to monitoring
✅ Account validation successful
🔄 Restart daemon to apply changes
```

**File Modified:** `config/accounts.yaml`

---

### 2. Risk Rule Configuration

Configure risk rules (limits, thresholds, enable/disable).

#### `risk-manager admin config view`

Display current risk configuration.

**Usage:**
```bash
risk-manager admin config view
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  Risk Configuration                                        ║
╚════════════════════════════════════════════════════════════╝

Rule                           Status      Limit        Type
─────────────────────────────────────────────────────────────
Max Contracts                  ✅ Enabled   5            Trade-by-Trade
Daily Realized Loss            ✅ Enabled   -$1000       Hard Lockout
Daily Realized Profit          ✅ Enabled   +$1000       Hard Lockout
Daily Unrealized Loss          ✅ Enabled   -$500        Trade-by-Trade
Max Unrealized Profit          ✅ Enabled   +$500        Trade-by-Trade
Trade Frequency (hour)         ✅ Enabled   10 trades    Hard Lockout
Trade Frequency (day)          ❌ Disabled  20 trades    Hard Lockout
Max Loss Per Trade             ✅ Enabled   -$200        Trade-by-Trade
Session Block (Outside)        ✅ Enabled   8:30-15:00   Hard Lockout
Auth Loss Guard                ✅ Enabled   API-based    Hard Lockout
Position Monitor (Stale)       ✅ Enabled   30s timeout  Trade-by-Trade
Symbol Blocks                  ❌ Disabled  []           Trade-by-Trade

Timers & Schedules:
  Daily Reset: 5:00 PM CT (Chicago)
  Lockout Duration: Until reset
```

---

#### `risk-manager admin config set`

Set a specific rule parameter.

**Usage:**
```bash
risk-manager admin config set <RULE> <PARAMETER> <VALUE>
```

**Arguments:**
- `RULE`: Rule identifier (e.g., `daily_realized_loss`, `max_contracts`)
- `PARAMETER`: Parameter to change (e.g., `limit`, `enabled`)
- `VALUE`: New value

**Examples:**

**Change limit:**
```bash
risk-manager admin config set daily_realized_loss limit -1500
```

**Enable/disable rule:**
```bash
risk-manager admin config enable max_contracts
risk-manager admin config disable trade_frequency_hour
```

**Set reset time:**
```bash
risk-manager admin config set timers daily_reset "17:00 America/Chicago"
```

**Output:**
```
✅ Configuration updated
🔄 Changes take effect on: [IMMEDIATE / DAEMON_RESTART]
```

**File Modified:** `config/risk_config.yaml`

---

#### `risk-manager admin config reload`

Reload configuration (live reload or restart).

**Usage:**
```bash
risk-manager admin config reload
```

**Behavior:**
- **Option 1 (Live Reload):** Daemon watches config file, reloads automatically
- **Option 2 (Manual Restart):** Admin must restart daemon for changes to apply

**User Decision (CONFLICT-007):** "IT SHOULD BE A LIVE RELOAD OR A RESTART, DOESNT MATTER BUT MAKE SURE ITS CLEAR."

**Implementation Decision:** Use live reload with file watcher (safer, no interruption).

**Output:**
```
✅ Configuration reloaded
✅ All rules updated
✅ Daemon running with new settings
```

---

### 3. Daemon Control

Start, stop, restart the Risk Manager daemon process.

#### `risk-manager admin daemon start`

Start the Risk Manager daemon (background monitoring process).

**Usage:**
```bash
risk-manager admin daemon start
```

**Output:**
```
🚀 Starting Risk Manager daemon...
✅ Daemon started successfully (PID: 12345)
✅ Monitoring account: DEMO-12345
✅ Active rules: 10/12 enabled
✅ SDK connected to TopstepX
```

**Behavior:**
- Daemon auto-starts on system boot
- Runs as Windows Service (LocalSystem privilege)
- Cannot be killed by trader (UAC protected)

---

#### `risk-manager admin daemon stop`

Stop the Risk Manager daemon.

**Usage:**
```bash
risk-manager admin daemon stop
```

**Output:**
```
⏸️  Stopping Risk Manager daemon...
✅ Daemon stopped (PID: 12345)
⚠️  Account monitoring PAUSED
⚠️  Risk enforcement DISABLED until restart
```

**Warning:** Stopping daemon disables all risk enforcement!

**User Guidance (CONFLICT-006B):** "PART OF WHAT THE ADMIN CLI DOES IS START/STOP DAEMON PROCESS... STOPPING DAEMON = EMERGENCY STOP"

---

#### `risk-manager admin daemon restart`

Restart the daemon (apply config changes).

**Usage:**
```bash
risk-manager admin daemon restart
```

**Output:**
```
🔄 Restarting Risk Manager daemon...
⏸️  Daemon stopped (PID: 12345)
🚀 Daemon started (PID: 67890)
✅ Configuration reloaded
✅ Monitoring resumed
```

---

#### `risk-manager admin daemon status`

Check daemon status.

**Usage:**
```bash
risk-manager admin daemon status
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  Daemon Status                                             ║
╚════════════════════════════════════════════════════════════╝

Status:      ✅ RUNNING (PID: 12345)
Uptime:      2 days, 5 hours, 32 minutes
Auto-start:  ✅ Enabled (starts on boot)

Accounts:
  DEMO-12345   ✅ Monitoring (connected)

Rules:
  Enabled:     10/12 rules
  Active:      2 rules near limit
  Triggered:   5 violations today

SDK:
  Connection:  ✅ Connected to TopstepX
  WebSocket:   ✅ Active (SignalR)
  Last Event:  2 seconds ago

Database:
  Status:      ✅ Accessible
  Size:        2.3 MB
  Location:    data/risk_manager.db
```

---

### 4. Timers & Schedules

Configure reset times, lockout durations, session windows.

#### `risk-manager admin timers view`

Display current timer configuration.

**Usage:**
```bash
risk-manager admin timers view
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  Timers & Schedules                                        ║
╚════════════════════════════════════════════════════════════╝

Daily Reset:
  Time:        5:00 PM
  Timezone:    America/Chicago
  Next Reset:  2025-10-25 17:00:00 CT (in 3 hours)

Lockout Durations:
  Hard Lockout:   Until daily reset
  Trade-by-Trade: Immediate (no lockout)

Session Windows:
  Allowed Trading:  8:30 AM - 3:00 PM CT
  Block Outside:    ✅ Enabled
```

---

#### `risk-manager admin timers set-reset-time`

Set daily reset time and timezone.

**Usage:**
```bash
risk-manager admin timers set-reset-time <TIME> <TIMEZONE>
```

**Arguments:**
- `TIME`: Reset time in HH:MM format (24-hour)
- `TIMEZONE`: IANA timezone (e.g., `America/Chicago`, `America/New_York`)

**Example:**
```bash
risk-manager admin timers set-reset-time "17:00" "America/Chicago"
```

**Output:**
```
✅ Daily reset time updated
   Time: 5:00 PM
   Timezone: America/Chicago (Central Time)
   Next Reset: 2025-10-25 17:00:00 CT (in 3 hours)
🔄 Restart daemon to apply changes
```

**User Guidance (CONFLICT-010):** "I SHOULD BE ABLE TO CONFIGURE THIS INSIDE CONFIGS!!!!!!!!!!!"

---

### 5. View Daemon Logs (Optional)

**User Guidance (CONFLICT-006A):** "ADMIN DOES NOT NEED TO SEE LOGS."

**Decision:** Omit `admin logs` command. Admin can view logs via trader CLI if needed.

---

## Configuration Files

### Files Modified by Admin CLI

| File | Purpose | Protection |
|------|---------|-----------|
| `config/api_credentials.yaml` | TopstepX API key/secret | ACL: Admin R/W, Trader None |
| `config/accounts.yaml` | Account IDs to monitor | ACL: Admin R/W, Trader R |
| `config/risk_config.yaml` | Risk rule settings | ACL: Admin R/W, Trader R |
| `config/timers.yaml` | Reset times, schedules | ACL: Admin R/W, Trader R |

---

## Workflow Examples

### Setup New Account

```bash
# 1. Configure API credentials
risk-manager admin api set-credentials \
  --key "your-key" \
  --secret "your-secret"

# 2. Add account to monitor
risk-manager admin api set-account DEMO-12345

# 3. Configure risk limits
risk-manager admin config set daily_realized_loss limit -1000
risk-manager admin config set max_contracts limit 5

# 4. Set reset time
risk-manager admin timers set-reset-time "17:00" "America/Chicago"

# 5. Start daemon
risk-manager admin daemon start

# Done! Trader can now trade with risk protection.
```

---

### Update Risk Limits

```bash
# 1. View current settings
risk-manager admin config view

# 2. Update limits (trader has grown account, allow more risk)
risk-manager admin config set daily_realized_loss limit -2000
risk-manager admin config set max_contracts limit 10

# 3. Reload configuration (live reload)
risk-manager admin config reload

# OR restart daemon (if using manual restart approach)
risk-manager admin daemon restart

# Done! New limits active.
```

---

### Check Daemon Health

```bash
# View daemon status
risk-manager admin daemon status

# Output shows:
# - Is daemon running?
# - How long has it been running?
# - Are accounts being monitored?
# - Any recent violations?
# - SDK connection healthy?
```

---

## Implementation Notes

### UAC Detection

**File:** `src/risk_manager/cli/admin/auth.py`

```python
import ctypes
import sys
import platform

def is_admin() -> bool:
    """Check if running with admin privileges."""
    if platform.system() != 'Windows':
        import os
        return os.geteuid() == 0

    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def require_admin():
    """Exit if not running as admin."""
    if not is_admin():
        print("❌ Error: Admin CLI requires administrator privileges")
        # [show help message]
        sys.exit(1)
```

### Entry Point

**File:** `src/risk_manager/cli/admin/__init__.py`

```python
import typer
from .auth import require_admin

app = typer.Typer()

@app.callback()
def main():
    """Admin CLI - Requires UAC elevation."""
    require_admin()  # Exit if not admin

# Add subcommands
from . import api, config, daemon, timers
app.add_typer(api.app, name="api")
app.add_typer(config.app, name="config")
app.add_typer(daemon.app, name="daemon")
app.add_typer(timers.app, name="timers")
```

### Config File Watcher (Live Reload)

**File:** `src/risk_manager/core/manager.py`

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("risk_config.yaml"):
            logger.info("Config file changed, reloading...")
            self.reload_config()

# Start watching
observer = Observer()
observer.schedule(ConfigWatcher(), path="config/", recursive=False)
observer.start()
```

---

## Summary

**Admin CLI provides:**
1. ✅ API credential configuration
2. ✅ Account management (add accounts to monitor)
3. ✅ Risk rule configuration (limits, enable/disable)
4. ✅ Timer/schedule configuration (reset times, session windows)
5. ✅ Daemon control (start/stop/restart/status)
6. ❌ NO manual trading lockout unlock (auto-timer only)
7. ❌ NO emergency stop command (stopping daemon = emergency stop)
8. ❌ NO log viewing (trader CLI has logs)

**Security:**
- All commands require UAC elevation
- Config files protected by Windows ACL
- Daemon cannot be killed by trader
- Credentials stored encrypted

**Next Steps:**
- Implement admin commands in `src/risk_manager/cli/admin/`
- Add config file validation (YAML syntax, value ranges)
- Add daemon health checks
- Test on Windows with UAC

---

**Document Version:** 1.0
**Last Updated:** 2025-10-25
**Status:** Unified specification (ready for implementation)
