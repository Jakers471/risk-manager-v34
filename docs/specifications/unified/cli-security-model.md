# CLI Security Model

**Wave 3 Unified Specification**
**Date:** 2025-10-25
**Authority:** User-provided requirements (CONFLICTS-FOR-USER-REVIEW.md)
**Purpose:** Complete security model for Admin vs Trader CLI separation

---

## Executive Summary

The Risk Manager uses Windows UAC (User Account Control) to enforce strict separation between Admin configuration and Trader view-only access. This prevents traders from modifying risk settings, killing the daemon, or bypassing enforcement.

**Key Security Principles:**

1. **Admin CLI = UAC Elevation Required**
   - Right-click terminal → "Run as Administrator"
   - Windows prompts for admin password
   - Only admin can configure settings or control daemon

2. **Trader CLI = Normal User (No Elevation)**
   - Runs as regular user
   - View-only access to status, P&L, logs
   - Cannot modify anything

3. **Daemon = Unkillable by Trader**
   - Runs as Windows Service (LocalSystem privilege)
   - Auto-starts on boot
   - Cannot be stopped without admin password

4. **Config Files = ACL Protected**
   - Admin: Read/Write
   - Trader: Read-only (or no access for credentials)
   - Prevents file tampering

**User Guidance (CONFLICT-008A):** "THE TRADER SHOULD NEVER BE ABLE TO SHUT DOWN THE CLI VIA ANYTHING. CANNOT KILL INSIDE TASK MANAGER WITHOUT UAC PRIVILEGE, ADMIN PASSWORD."

---

## Table of Contents

1. [Windows UAC Elevation](#1-windows-uac-elevation)
2. [Daemon Protection](#2-daemon-protection)
3. [File Permissions (ACL)](#3-file-permissions-acl)
4. [Admin CLI Security](#4-admin-cli-security)
5. [Trader CLI Security](#5-trader-cli-security)
6. [Attack Scenarios & Mitigations](#6-attack-scenarios--mitigations)
7. [Cross-Platform Considerations](#7-cross-platform-considerations)

---

## 1. Windows UAC Elevation

### 1.1 What is UAC?

**User Account Control (UAC)** is Windows' security feature that prompts for admin password before allowing privileged operations.

**How it works:**
1. User runs command requiring admin rights
2. Windows detects privilege requirement
3. Windows shows UAC prompt: "Do you want to allow this app to make changes?"
4. User enters admin password
5. Command runs with elevated privileges

**We use UAC for:**
- Admin CLI access (configure risk settings)
- Daemon control (start/stop service)
- Config file modification (protected by ACL)

---

### 1.2 Admin CLI Elevation Check

**Every admin command checks elevation first:**

**File:** `src/risk_manager/cli/admin/auth.py`

```python
import ctypes
import sys
import platform

def is_admin() -> bool:
    """
    Check if running with Windows administrator privileges.

    Returns:
        True if running elevated (has admin rights)
        False if running as normal user
    """
    if platform.system() != 'Windows':
        # On Linux/Mac, check if running as root
        import os
        return os.geteuid() == 0

    try:
        # Windows: Check if process has admin token
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def require_admin():
    """
    Ensure admin CLI is running with elevation.
    Exit immediately if not elevated.

    NO custom password needed - Windows handles authentication.
    """
    if not is_admin():
        print("❌ Error: Admin CLI requires administrator privileges")
        print("")
        print("🔐 This protects you from making changes while locked out.")
        print("")
        print("To access Admin CLI:")
        print("  1. Right-click PowerShell or Terminal")
        print("  2. Select 'Run as Administrator'")
        print("  3. Windows will prompt for admin password")
        print("  4. Enter your Windows admin password")
        print("  5. Run 'risk-manager admin' again")
        print("")
        sys.exit(1)
```

**Usage in every admin command:**

```python
# cli/admin/__init__.py

from .auth import require_admin

@app.callback()
def main():
    """Admin CLI entry point."""
    # FIRST THING: Check elevation
    require_admin()  # Exits immediately if not elevated

    # Only reaches here if user has admin rights
    display_admin_menu()
```

---

### 1.3 No Custom Password System

**CRITICAL:** We do NOT implement custom passwords.

**User Guidance (CLAUDE.md):**
> "NO custom passwords stored. NO authentication database. Just Windows admin rights."

**Why?**
- Windows UAC already provides authentication
- No need to duplicate password storage
- More secure (leverages OS-level security)
- Simpler implementation

**What this means:**
- ❌ NO `password.txt` file
- ❌ NO password database
- ❌ NO password hashing
- ✅ YES Windows admin password (set by IT/user)

---

## 2. Daemon Protection

### 2.1 Windows Service Architecture

The Risk Manager runs as a **Windows Service** with LocalSystem privilege.

**Why Windows Service?**
- Runs in background (no terminal needed)
- Auto-starts on boot
- Cannot be killed by normal users
- Protected by Windows UAC

**Service Configuration:**
```
Service Name:      RiskManagerV34
Display Name:      Risk Manager V34 - Trading Protection
Start Type:        Automatic (starts on boot)
Run As:            LocalSystem (highest privilege)
Recovery:          Restart on failure
```

---

### 2.2 Trader Cannot Kill Daemon

**Protection mechanisms:**

**1. Task Manager Protection**
```
Trader attempts to kill service via Task Manager:
  → Windows prompts for UAC (admin password)
  → Trader does not have admin password
  → Operation denied
  → Service continues running
```

**2. Command Line Protection**
```bash
# Trader tries:
taskkill /F /IM risk_manager.exe

# Windows responds:
ERROR: Access is denied.
```

**3. Process Protection**
- Service runs under `NT AUTHORITY\SYSTEM`
- Trader runs under `DOMAIN\TraderUsername`
- Windows prevents cross-user process termination

**User Guidance (CONFLICT-008A):** "THE TRADER SHOULD NEVER BE ABLE TO SHUT DOWN THE CLI VIA ANYTHING. CANNOT KILL INSIDE TASK MANAGER WITHOUT UAC PRIVILEGE, ADMIN PASSWORD."

---

### 2.3 Auto-Start on Boot

**Behavior:**
1. Computer boots
2. Windows starts services (before user login)
3. Risk Manager service starts automatically
4. Trader logs in → daemon already running
5. Trader starts trading → protected from first trade

**Configuration:**
```python
# scripts/install_service.py

import win32serviceutil
import win32service

def install_service():
    """Install Risk Manager as Windows Service."""
    win32serviceutil.InstallService(
        pythonClassString="risk_manager.service.RiskManagerService",
        serviceName="RiskManagerV34",
        displayName="Risk Manager V34 - Trading Protection",
        startType=win32service.SERVICE_AUTO_START,  # Auto-start on boot
        description="Monitors TopstepX accounts and enforces risk rules"
    )
```

---

### 2.4 Forced Restart Protection

**User Guidance (CONFLICT-008B):**
> "If trader shuts down their computer, risk manager/daemon restarts and continues monitoring account."

**Scenario: Trader forces reboot**
```
Trader action:
  - Presses power button (hard shutdown)
  - Runs shutdown -r -f -t 0 (forced restart)
  - Unplugs power cord

Result:
  1. Computer reboots
  2. Windows starts services (auto-start)
  3. Risk Manager daemon starts
  4. Monitoring resumes IMMEDIATELY
  5. Trader cannot bypass protection
```

**Recovery options (CONFLICT-008B):**
- **Option A:** Service auto-starts on boot (CHOSEN)
- ~~Option B: Service auto-starts + logs "forced reboot detected"~~
- ~~Option C: Service auto-starts + locks account temporarily~~
- ~~Option D: Service requires admin to manually restart~~

**Decision:** Option A (simplest, most reliable)

---

## 3. File Permissions (ACL)

### 3.1 Windows Access Control Lists (ACL)

**ACL = Windows file permission system**

**We protect files using ACL:**
- Config files (risk settings, API credentials)
- Database file (state, lockouts, P&L)
- Log files (enforcement history)

**Permission levels:**
- **Admin:** Read + Write + Execute
- **Trader:** Read-only (or No Access for credentials)

---

### 3.2 Protected Files

| File | Admin | Trader | Purpose |
|------|-------|--------|---------|
| `config/api_credentials.yaml` | R/W | **None** | TopstepX API key/secret (SENSITIVE) |
| `config/accounts.yaml` | R/W | R | Account IDs to monitor |
| `config/risk_config.yaml` | R/W | R | Risk rule settings |
| `config/timers.yaml` | R/W | R | Reset times, schedules |
| `data/risk_manager.db` | R/W | R | State database (P&L, lockouts) |
| `data/logs/risk_manager.log` | R/W | R | Enforcement logs |

**Legend:**
- **R/W** = Read and Write
- **R** = Read-only
- **None** = No access (file hidden)

---

### 3.3 Setting ACL Permissions

**Windows PowerShell (run as admin):**

```powershell
# Protect API credentials (admin-only, trader has NO access)
$acl = Get-Acl "config/api_credentials.yaml"
$acl.SetAccessRuleProtection($true, $false)  # Remove inheritance
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    "BUILTIN\Administrators", "FullControl", "Allow"
)))
Set-Acl "config/api_credentials.yaml" $acl

# Protect risk config (admin R/W, trader read-only)
$acl = Get-Acl "config/risk_config.yaml"
$acl.SetAccessRuleProtection($true, $false)
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    "BUILTIN\Administrators", "FullControl", "Allow"
)))
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    "BUILTIN\Users", "Read", "Allow"
)))
Set-Acl "config/risk_config.yaml" $acl
```

**Installation script handles this automatically.**

---

### 3.4 Config Tampering Protection

**User Guidance (CONFLICT-009):**
> "IF WINDOWS UAC DENIES IT THEN OKAY, MAKE SURE THE TRADER CANNOT EDIT ANYTHING WITHOUT UAC."

**Scenario: Trader tries to edit config**
```bash
# Trader runs:
notepad config/risk_config.yaml

# Trader edits file, changes limit from -$1000 to -$10000
# Trader tries to save

# Windows responds:
"Access Denied. You do not have permission to save to this location."

# Result:
- File unchanged
- Protection remains
- Trader frustrated but cannot bypass
```

**Decision (CONFLICT-009):**
- **Option A (CHOSEN):** Silent fail (Windows denies, system continues)
- **Option D (CHOSEN):** Just ignore (ACL prevents it)
- ~~Option B: Log the attempt~~
- ~~Option C: Lock account + alert admin~~

**Rationale:** Windows ACL is sufficient protection. No need for additional logging or alerts.

---

## 4. Admin CLI Security

### 4.1 Entry Point Protection

**File:** `src/risk_manager/cli/admin/__init__.py`

```python
import typer
from .auth import require_admin

app = typer.Typer()

@app.callback()
def main():
    """Admin CLI - Requires UAC elevation."""
    # Exit immediately if not running as admin
    require_admin()

# Only reaches here if user has admin rights
```

**Every admin subcommand inherits this check.**

---

### 4.2 Admin Capabilities

**What admin CAN do:**
- ✅ Configure API credentials
- ✅ Configure account IDs to monitor
- ✅ Configure risk rules (enable/disable, set limits)
- ✅ Configure timers/schedules (reset times, lockout durations)
- ✅ Start/stop/restart daemon
- ✅ Check daemon status
- ❌ **NO** manual unlock of trading lockouts (auto-timer only)
- ❌ **NO** emergency stop (stopping daemon = emergency stop)
- ❌ **NO** log viewing (trader CLI has logs)

**User Guidance (CONFLICT-006):**
- "admin does not need to see logs"
- "admin should never need to unlock the accounts for trading"
- "LOCKOUTS ARE ON AN AUTO SCHEDULE"

---

### 4.3 Config Changes - Live Reload

**User Guidance (CONFLICT-006C):**
> "IT SHOULD BE A LIVE RELOAD OR A RESTART, DOESNT MATTER BUT MAKE SURE ITS CLEAR."

**Implementation: Live Reload (file watcher)**

```python
# src/risk_manager/core/manager.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("risk_config.yaml"):
            logger.info("Config file changed, reloading...")
            self.reload_config()

# Start watching config directory
observer = Observer()
observer.schedule(ConfigWatcher(), path="config/", recursive=False)
observer.start()
```

**Behavior:**
1. Admin edits `config/risk_config.yaml` via CLI
2. File watcher detects change
3. Daemon reloads config automatically (within 1 second)
4. New limits take effect immediately
5. No daemon restart needed

**Alternative: Manual Restart**
- If live reload is unreliable, admin can use `risk-manager admin daemon restart`

---

## 5. Trader CLI Security

### 5.1 No Elevation Required

**Trader CLI runs as normal user:**

```python
# src/risk_manager/cli/trader/__init__.py

import typer

app = typer.Typer()

@app.callback()
def main():
    """Trader CLI - View-only, no admin rights required."""
    # NO UAC check
    # Runs as normal user
    pass
```

---

### 5.2 Trader Capabilities

**What trader CAN do:**
- ✅ View configured settings (read-only)
- ✅ View live unrealized P&L (floating) + realized P&L
- ✅ View enforcement logs (WHY position closed, which rule breached)
- ✅ Clock in/out (time tracking)
- ✅ View holidays, current time, market hours
- ✅ View lockout status and reason
- ✅ View if account is being monitored (daemon running?)

**What trader CANNOT do:**
- ❌ Pause/stop daemon
- ❌ Modify any settings
- ❌ Request admin unlock (no ticket system)
- ❌ View verbose logs (just breach reasons, no DEBUG)

**User Guidance (CONFLICT-007):**
> "TRADER cannot pause the daemon or risk manager, its always active only the admin can start/stop it. no tickets for requesting."

---

### 5.3 Read-Only Database Access

**Trader CLI queries database in read-only mode:**

```python
# src/risk_manager/cli/trader/status.py

from risk_manager.state.database import Database

# Open database read-only
db = Database(db_path="data/risk_manager.db", read_only=True)

# Read operations only
realized_pnl = db.get_daily_realized_pnl(account_id)
unrealized_pnl = db.get_unrealized_pnl(account_id)
lockouts = db.get_active_lockouts(account_id)

# NO write operations allowed
# db.set_lockout()  ← Would fail (read-only mode)
```

**SQLite read-only mode:**
```python
import sqlite3

conn = sqlite3.connect(
    "file:data/risk_manager.db?mode=ro",  # Read-only mode
    uri=True
)
```

---

### 5.4 Log Filtering

**Trader sees filtered logs (no DEBUG level):**

```python
# src/risk_manager/cli/trader/logs.py

def get_logs(level_filter: str = "INFO"):
    """Get logs filtered by level (no DEBUG for traders)."""

    allowed_levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]

    if level_filter not in allowed_levels:
        # Trader tried to access DEBUG logs
        print("❌ DEBUG logs are admin-only")
        return []

    # Read log file, filter by level
    with open("data/logs/risk_manager.log") as f:
        lines = f.readlines()
        filtered = [l for l in lines if level_filter in l]
        return filtered
```

**User Guidance:** "they can see logs for WHY A POSITION WAS ENFORCED, SHOWING WHAT RISK RULE WAS BREACHED! no verbose."

---

## 6. Attack Scenarios & Mitigations

### 6.1 Scenario: Trader Tries to Kill Daemon

**Attack:**
```
Trader opens Task Manager
→ Finds "RiskManagerV34" service
→ Right-clicks → "End Task"
```

**Mitigation:**
```
Windows prompts for UAC (admin password)
→ Trader does not have admin password
→ Operation denied
→ Service continues running
```

**Result:** ✅ Attack failed

---

### 6.2 Scenario: Trader Edits Config Files

**Attack:**
```
Trader navigates to config/risk_config.yaml
→ Opens in notepad
→ Changes daily_realized_loss limit from -$1000 to -$10000
→ Tries to save
```

**Mitigation:**
```
Windows ACL denies write access
→ "Access Denied" error
→ File unchanged
```

**Result:** ✅ Attack failed

---

### 6.3 Scenario: Trader Deletes Config Files

**Attack:**
```
Trader runs:
del config\risk_config.yaml
```

**Mitigation:**
```
Windows ACL denies delete permission
→ "Access Denied" error
→ File not deleted
```

**Result:** ✅ Attack failed

---

### 6.4 Scenario: Trader Copies Config and Swaps

**Attack:**
```
Trader copies config\risk_config.yaml to Desktop
→ Edits Desktop copy (changes limits)
→ Tries to copy back to config\ (overwrite)
```

**Mitigation:**
```
Windows ACL denies write access to config\ directory
→ "Access Denied" error
→ Original file unchanged
```

**Result:** ✅ Attack failed

---

### 6.5 Scenario: Trader Forces System Reboot

**Attack:**
```
Trader runs:
shutdown -r -f -t 0
(Forced restart, bypassing all processes)
```

**Mitigation:**
```
Computer reboots
→ Windows starts services (auto-start enabled)
→ RiskManagerV34 service starts BEFORE user login
→ Trader logs in → daemon already running
→ Protection active from first trade
```

**Result:** ✅ Attack failed (protection resumes)

**User Guidance (CONFLICT-008B):** "If trader shuts down their computer, risk manager/daemon restarts and continues monitoring account."

---

### 6.6 Scenario: Trader Uninstalls Service

**Attack:**
```
Trader runs:
sc delete RiskManagerV34
```

**Mitigation:**
```
Windows prompts for UAC (admin password)
→ Trader does not have admin password
→ Operation denied
→ Service not deleted
```

**Result:** ✅ Attack failed

---

### 6.7 Scenario: Trader Modifies Database

**Attack:**
```
Trader opens data\risk_manager.db in SQLite browser
→ Tries to delete lockouts table
→ Tries to change realized_pnl to $0
```

**Mitigation:**
```
Windows ACL allows read-only access
→ SQLite opens in read-only mode
→ Modifications not saved
→ Database unchanged
```

**Result:** ✅ Attack failed

---

## 7. Cross-Platform Considerations

### 7.1 Windows (Primary Target)

**Security Features:**
- ✅ UAC elevation (admin password)
- ✅ Windows Service (LocalSystem)
- ✅ ACL file permissions
- ✅ Task Manager protection
- ✅ Auto-start on boot

**Implementation:** Full security model as described above.

---

### 7.2 Linux

**Security Features:**
- ✅ sudo elevation (root password)
- ✅ systemd service (root user)
- ✅ File permissions (chmod, chown)
- ✅ Process protection (requires root to kill)
- ✅ Auto-start via systemd

**Differences:**
- Use `os.geteuid() == 0` instead of `IsUserAnAdmin()`
- Use `systemd` instead of Windows Service
- Use `chmod 600` (file permissions) instead of ACL

**Example:**
```bash
# Linux equivalent of ACL protection
sudo chown root:root config/api_credentials.yaml
sudo chmod 600 config/api_credentials.yaml  # Only root can read/write

sudo chown root:root config/risk_config.yaml
sudo chmod 644 config/risk_config.yaml  # Root R/W, others read-only
```

---

### 7.3 macOS

**Security Features:**
- ✅ sudo elevation (admin password)
- ✅ launchd service (root user)
- ✅ File permissions (chmod, chown)
- ✅ Process protection (requires sudo to kill)
- ✅ Auto-start via launchd

**Similar to Linux but uses `launchd` instead of `systemd`.**

---

## 8. Summary

### 8.1 Security Layers

The Risk Manager uses **defense in depth** (multiple security layers):

```
Layer 1: UAC Elevation
  → Admin CLI requires Windows admin password
  → Trader CLI runs as normal user

Layer 2: Windows Service Protection
  → Daemon runs as LocalSystem (highest privilege)
  → Cannot be killed without admin password
  → Auto-starts on boot

Layer 3: File ACL Protection
  → Config files require admin to modify
  → Trader has read-only (or no access)

Layer 4: Database Protection
  → Trader CLI uses read-only mode
  → No write operations from trader

Layer 5: Process Isolation
  → Admin commands check elevation first
  → Trader commands cannot call admin functions
```

**Result:** Trader CANNOT bypass risk enforcement, even with physical access to machine.

---

### 8.2 User Requirements Met

**User Guidance Compliance:**

| Requirement | Implementation |
|-------------|----------------|
| "THE TRADER SHOULD NEVER BE ABLE TO SHUT DOWN THE CLI" | ✅ Windows Service + UAC protection |
| "CANNOT KILL INSIDE TASK MANAGER WITHOUT UAC PRIVILEGE" | ✅ LocalSystem service |
| "ONLY THE ADMIN CAN STOP IT WITH ADMIN PASSWORD" | ✅ UAC elevation required |
| "ADMIN DOESNT UNLOCK RISK SETTING LOCKOUTS" | ✅ Auto-timer based unlock |
| "TRADER CANNOT EDIT ANYTHING WITHOUT UAC" | ✅ ACL file protection |
| "DAEMON RESTARTS ON COMPUTER SHUTDOWN" | ✅ Auto-start on boot |

**All requirements satisfied.**

---

### 8.3 Implementation Checklist

**Windows Service:**
- [ ] Implement `src/service/windows_service.py`
- [ ] Install as LocalSystem service
- [ ] Configure auto-start on boot
- [ ] Test: Can trader kill service? (should fail)

**UAC Elevation:**
- [ ] Implement `src/cli/admin/auth.py`
- [ ] Add `require_admin()` to all admin commands
- [ ] Test: Admin CLI without elevation (should exit)
- [ ] Test: Admin CLI with elevation (should work)

**File ACL:**
- [ ] Create `scripts/setup_permissions.ps1`
- [ ] Set ACL on config files (admin R/W, trader R or none)
- [ ] Set ACL on database (admin R/W, trader R)
- [ ] Test: Trader tries to edit config (should fail)

**Read-Only Database:**
- [ ] Add read-only mode to `Database` class
- [ ] Use read-only mode in trader CLI
- [ ] Test: Trader CLI cannot write to database

**Auto-Start:**
- [ ] Configure service auto-start
- [ ] Test: Reboot computer → service starts before login
- [ ] Test: Trader logs in → daemon already running

---

**Document Version:** 1.0
**Last Updated:** 2025-10-25
**Status:** Unified specification (ready for implementation)
