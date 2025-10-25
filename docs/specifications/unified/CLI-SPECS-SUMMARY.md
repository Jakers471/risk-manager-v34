# CLI System Unified Specifications - Summary

**Wave 3 Research - Researcher 4 Deliverable**
**Date:** 2025-10-25
**Status:** Complete - Ready for Implementation

---

## Mission Complete

Created unified CLI specifications with clear Admin vs Trader separation based on user guidance from CONFLICTS-FOR-USER-REVIEW.md.

---

## Deliverables

### 1. Admin CLI Reference
**File:** `admin-cli-reference.md` (16 KB)

**Complete command reference for admin operations:**

**Commands Implemented:**
- ✅ `risk-manager admin api set-credentials` - Configure TopstepX API
- ✅ `risk-manager admin api set-account` - Add account to monitor
- ✅ `risk-manager admin config view` - Display current configuration
- ✅ `risk-manager admin config set` - Set rule parameters
- ✅ `risk-manager admin config reload` - Reload configuration (live reload)
- ✅ `risk-manager admin daemon start` - Start daemon
- ✅ `risk-manager admin daemon stop` - Stop daemon
- ✅ `risk-manager admin daemon restart` - Restart daemon
- ✅ `risk-manager admin daemon status` - Check daemon status
- ✅ `risk-manager admin timers view` - Display timer configuration
- ✅ `risk-manager admin timers set-reset-time` - Set daily reset time

**Key Features:**
- UAC elevation required (Windows admin password)
- Config file modifications with live reload
- Daemon process control (start/stop/restart)
- Timer and schedule configuration
- NO manual unlock (auto-timer only)
- NO emergency stop command (stopping daemon = emergency stop)
- NO log viewing (trader CLI handles logs)

---

### 2. Trader CLI Reference
**File:** `trader-cli-reference.md` (23 KB)

**Complete command reference for trader operations:**

**Commands Implemented:**
- ✅ `risk-manager trader status` - Live snapshot (P&L, positions, rules)
- ✅ `risk-manager trader status --live` - Auto-refreshing status
- ✅ `risk-manager trader pnl` - P&L breakdown (realized, unrealized)
- ✅ `risk-manager trader logs` - Enforcement logs (WHY position closed)
- ✅ `risk-manager trader lockouts` - Current lockout status
- ✅ `risk-manager trader rules` - View configured limits
- ✅ `risk-manager trader market-hours` - Market status, session windows
- ✅ `risk-manager trader clock-in` - Start session tracking
- ✅ `risk-manager trader clock-out` - End session tracking
- ✅ `risk-manager trader daemon-status` - Check if daemon running

**Key Features:**
- No UAC required (normal user)
- View-only access (read-only database)
- Live P&L tracking (realized + unrealized)
- Enforcement log viewing (breach reasons, no verbose DEBUG)
- Lockout status with countdown timers
- Market hours and session windows
- Clock in/out time tracking
- Daemon health check (is account monitored?)
- NO daemon control (cannot start/stop)
- NO config modification (cannot change limits)
- NO manual unlock requests (no ticket system)

---

### 3. CLI Security Model
**File:** `cli-security-model.md` (22 KB)

**Complete security specification:**

**Security Layers:**
1. **UAC Elevation** - Admin CLI requires Windows admin password
2. **Windows Service Protection** - Daemon runs as LocalSystem (unkillable by trader)
3. **File ACL Protection** - Config files require admin to modify
4. **Database Protection** - Trader CLI uses read-only mode
5. **Process Isolation** - Admin/trader command separation

**Attack Scenarios Covered:**
- ✅ Trader tries to kill daemon (BLOCKED by UAC)
- ✅ Trader tries to edit config files (BLOCKED by ACL)
- ✅ Trader tries to delete config files (BLOCKED by ACL)
- ✅ Trader copies and swaps config files (BLOCKED by ACL)
- ✅ Trader forces system reboot (daemon auto-restarts)
- ✅ Trader tries to uninstall service (BLOCKED by UAC)
- ✅ Trader tries to modify database (BLOCKED by read-only mode)

**Cross-Platform:**
- Windows: Full implementation (UAC, Windows Service, ACL)
- Linux: Equivalent implementation (sudo, systemd, chmod)
- macOS: Equivalent implementation (sudo, launchd, chmod)

---

## User Guidance Implemented

### Admin CLI Capabilities (CONFLICT-006)

**What Admin CAN do:**
- ✅ Configure API credentials
- ✅ Configure account IDs to monitor
- ✅ Configure risk rules (enable/disable, set limits)
- ✅ Configure timers/schedules (reset times, lockout durations)
- ✅ Start/stop/restart daemon
- ✅ Check daemon status

**What Admin CANNOT/DOESN'T do:**
- ❌ Manually unlock trading lockouts (timer-based only)
- ❌ No emergency stop (stopping daemon IS the stop)
- ❌ No ticket system
- ❌ No log viewing (trader CLI has logs)

**Config Changes:**
- Live reload OR restart daemon (live reload implemented with file watcher)

---

### Trader CLI Capabilities (CONFLICT-007)

**What Trader CAN do:**
- ✅ View configured settings (read-only)
- ✅ View live unrealized P&L (floating) + realized P&L
- ✅ View enforcement logs (WHY position was closed, which rule breached)
- ✅ Clock in/out
- ✅ View holidays, current time, market hours
- ✅ View lockout status and reason
- ✅ View if account is being monitored (daemon running?)

**What Trader CANNOT do:**
- ❌ Pause/stop daemon
- ❌ Modify any settings
- ❌ Request admin unlock (no ticket system)
- ❌ View verbose logs (just breach reasons)

---

### Security Model (CONFLICT-008, CONFLICT-009)

**Daemon Protection:**
- ✅ Trader cannot kill daemon (UAC protected)
- ✅ Daemon auto-starts on boot (even after forced shutdown)
- ✅ Runs as Windows Service (LocalSystem privilege)

**Config File Protection:**
- ✅ Admin: Read/Write
- ✅ Trader: Read-only (or no access for credentials)
- ✅ Windows ACL prevents tampering

**Forced Restart:**
- ✅ Daemon auto-starts on boot (protection resumes immediately)

---

## Technical Implementation

### Admin CLI Structure

```
src/risk_manager/cli/admin/
├── __init__.py          # Entry point with UAC check
├── auth.py              # UAC elevation detection
├── api.py               # API credential commands
├── config.py            # Configuration commands
├── daemon.py            # Daemon control commands
└── timers.py            # Timer/schedule commands
```

### Trader CLI Structure

```
src/risk_manager/cli/trader/
├── __init__.py          # Entry point (no UAC check)
├── status.py            # Status snapshot commands
├── pnl.py               # P&L breakdown commands
├── logs.py              # Enforcement log viewing
├── lockouts.py          # Lockout status commands
├── rules.py             # Rules viewing commands
├── market_hours.py      # Market info commands
├── clock.py             # Clock in/out commands
└── daemon_status.py     # Daemon health check
```

### Security Implementation

**UAC Detection:**
```python
# src/risk_manager/cli/admin/auth.py
import ctypes

def is_admin() -> bool:
    return ctypes.windll.shell32.IsUserAnAdmin()

def require_admin():
    if not is_admin():
        print("❌ Error: Admin CLI requires administrator privileges")
        sys.exit(1)
```

**Config File Watcher (Live Reload):**
```python
# src/risk_manager/core/manager.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("risk_config.yaml"):
            logger.info("Config file changed, reloading...")
            self.reload_config()
```

**Windows Service:**
```python
# src/service/windows_service.py
import win32serviceutil
import win32service

class RiskManagerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "RiskManagerV34"
    _svc_display_name_ = "Risk Manager V34 - Trading Protection"

    def SvcDoRun(self):
        # Start daemon
        pass
```

---

## Configuration Files

### Files Modified by Admin CLI

| File | Purpose | Protection |
|------|---------|-----------|
| `config/api_credentials.yaml` | TopstepX API key/secret | ACL: Admin R/W, Trader None |
| `config/accounts.yaml` | Account IDs to monitor | ACL: Admin R/W, Trader R |
| `config/risk_config.yaml` | Risk rule settings | ACL: Admin R/W, Trader R |
| `config/timers.yaml` | Reset times, schedules | ACL: Admin R/W, Trader R |

### Files Read by Trader CLI

| File | Purpose | Access |
|------|---------|--------|
| `config/accounts.yaml` | Account IDs | Read-only |
| `config/risk_config.yaml` | Risk rules | Read-only |
| `config/timers.yaml` | Reset times | Read-only |
| `data/risk_manager.db` | State database | Read-only |
| `data/logs/risk_manager.log` | Enforcement logs | Read-only (filtered) |

---

## Command Examples

### Admin Workflow

```bash
# Setup new account
risk-manager admin api set-credentials --key "KEY" --secret "SECRET"
risk-manager admin api set-account DEMO-12345
risk-manager admin config set daily_realized_loss limit -1000
risk-manager admin timers set-reset-time "17:00" "America/Chicago"
risk-manager admin daemon start

# Update risk limits later
risk-manager admin config set daily_realized_loss limit -2000
risk-manager admin config reload  # Live reload

# Check daemon health
risk-manager admin daemon status
```

### Trader Workflow

```bash
# Morning routine
risk-manager trader daemon-status
risk-manager trader status
risk-manager trader clock-in

# During trading
risk-manager trader status --live  # Auto-refresh every 5s
risk-manager trader pnl

# After breach
risk-manager trader lockouts
risk-manager trader logs  # See WHY position was closed

# End of day
risk-manager trader clock-out
risk-manager trader pnl
```

---

## Implementation Effort

### Admin CLI (12 commands)
- API commands: 2 days
- Config commands: 3 days
- Daemon commands: 2 days
- Timer commands: 2 days
- **Total:** 9 days

### Trader CLI (10 commands)
- Status commands: 3 days
- P&L commands: 2 days
- Logs commands: 1 day
- Lockouts commands: 1 day
- Rules commands: 1 day
- Market hours: 1 day
- Clock in/out: 1 day
- **Total:** 10 days

### Security Implementation
- UAC detection: 1 day
- Windows Service: 3 days
- File ACL setup: 1 day
- Config watcher: 1 day
- **Total:** 6 days

### Grand Total: 25 days (5 weeks)

---

## Next Steps

1. **Implement Admin CLI** (`src/risk_manager/cli/admin/`)
2. **Implement Trader CLI** (`src/risk_manager/cli/trader/`)
3. **Implement Windows Service** (`src/service/windows_service.py`)
4. **Implement UAC Detection** (`src/risk_manager/cli/admin/auth.py`)
5. **Setup File ACL** (`scripts/setup_permissions.ps1`)
6. **Test on Windows** (UAC, service, file permissions)
7. **Create installation script** (service install, ACL setup)

---

## Files Created

| File | Size | Purpose |
|------|------|---------|
| `admin-cli-reference.md` | 16 KB | Admin command reference |
| `trader-cli-reference.md` | 23 KB | Trader command reference |
| `cli-security-model.md` | 22 KB | Security implementation spec |
| **Total** | **61 KB** | **Complete CLI specification** |

---

## Status

✅ **All 3 unified CLI specifications created**
✅ **User guidance from CONFLICTS-FOR-USER-REVIEW.md implemented**
✅ **Command reference tables complete**
✅ **Security model documented**
✅ **Ready for implementation**

---

**Wave 3 Research Complete**
**Researcher 4: CLI System Specification Unification**
**Date:** 2025-10-25
