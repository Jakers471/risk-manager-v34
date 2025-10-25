# Security Model - Windows UAC Protection

**Date**: 2025-10-23
**Status**: ✅ Core Design Principle
**Critical**: This is how we make the system "virtually unkillable"

---

## 🎯 Core Security Principle

**The Risk Manager uses Windows operating system security (UAC) to protect traders from themselves.**

**NO custom passwords. NO stored credentials. Just Windows admin rights.**

---

## 🔐 How It Works

### Two Access Levels

```
┌─────────────────────────────────────────────────────────────┐
│                    WINDOWS ADMIN PASSWORD                    │
│                     (UAC Protection)                         │
│              Controls EVERYTHING administrative              │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────┐                  ┌──────────────────┐
│   ADMIN CLI      │                  │   TRADER CLI     │
│   (Elevated)     │                  │   (Normal User)  │
│                  │                  │                  │
│ - Configure      │                  │ - View status    │
│ - Unlock         │                  │ - View logs      │
│ - Stop service   │                  │ - Monitor P&L    │
│ - Edit rules     │                  │ - See lockouts   │
└──────────────────┘                  └──────────────────┘
       ▲                                       ▲
       │                                       │
   REQUIRES UAC                            NO UAC NEEDED
   Admin password                          Anyone can use
```

---

## 🛡️ Why This is "Virtually Unkillable"

### What Trader CANNOT Do (Without Admin Password)

#### 1. Kill the Service Process

```powershell
# Trader attempts in Task Manager
Task Manager → Find "Risk Manager V34" → End Task

# Windows Response
❌ Access Denied
   Administrator privileges required to stop protected services
```

#### 2. Stop the Windows Service

```powershell
# Trader attempts via Services
Services → Risk Manager V34 → Stop

# Windows Response
┌─────────────────────────────────────────────┐
│  User Account Control                       │
│                                             │
│  Do you want to allow this app to make     │
│  changes to your device?                   │
│                                             │
│  Services - Stop Service                    │
│                                             │
│  Enter administrator password: _______      │
│                                             │
│         [ Yes ]        [ No ]               │
└─────────────────────────────────────────────┘

# Trader doesn't have password → BLOCKED ✅
```

#### 3. Kill via Command Line

```powershell
# Trader attempts
PS> taskkill /F /IM risk-manager.exe

# Windows Response
ERROR: Access Denied. Administrator privileges required.

# Trader attempts elevated command
PS> Stop-Service RiskManagerV34

# Windows Response
UAC Prompt appears → Trader doesn't have password → BLOCKED ✅
```

#### 4. Edit Configuration Files

```
Trader navigates to: C:\ProgramData\RiskManager\config\
Trader opens: risk_config.yaml
Trader changes: daily_loss: -10000 (from -500)
Trader tries to save...

# Windows Response
┌─────────────────────────────────────────────┐
│  Access Denied                              │
│                                             │
│  You need administrator permission to save  │
│  changes to this file.                      │
│                                             │
│         [ Cancel ]     [ Retry as Admin ]   │
└─────────────────────────────────────────────┘

# Trader clicks "Retry as Admin" → UAC prompt → No password → BLOCKED ✅
```

#### 5. Delete State Database

```
Trader navigates to: C:\ProgramData\RiskManager\data\
Trader tries to delete: state.db (contains P&L, lockouts)

# Windows Response
❌ Access Denied
   You need administrator permission to delete this file
```

#### 6. Run Admin CLI

```powershell
# Trader attempts
PS> risk-manager admin

# Our Code Response
❌ Error: Admin CLI requires administrator privileges

Please run this command in an elevated terminal:
  1. Right-click PowerShell/Terminal
  2. Select 'Run as Administrator'
  3. Enter Windows admin password when prompted
  4. Run 'risk-manager admin' again

# Script exits before showing admin menu
```

**Result: Trader is completely blocked from administrative actions. ✅**

---

## ✅ What Trader CAN Do

### Trader CLI (View-Only Access)

```powershell
# No elevation needed - runs as normal user
PS> risk-manager trader

# Opens immediately
╔══════════════════════════════════════════════════════════════╗
║         RISK MANAGER V34 - TRADER STATUS                     ║
╚══════════════════════════════════════════════════════════════╝

# Trader can:
✅ View current P&L
✅ View positions
✅ View rule status
✅ View lockout timers
✅ View enforcement logs (read-only)
✅ Monitor system status

# Trader cannot:
❌ Change any settings
❌ Unlock account
❌ Stop service
❌ Edit rules
❌ Delete logs
```

---

## 🔧 Technical Implementation

### 1. Admin Elevation Check

**File**: `src/cli/admin/auth.py`

```python
"""
Windows UAC Admin Check

NO custom passwords stored.
NO authentication database.
Just check Windows elevation status.
"""

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

    This forces the user to:
    1. Right-click terminal
    2. Select "Run as Administrator"
    3. Enter Windows admin password (UAC prompt)

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

**Usage in Admin CLI**:

```python
# src/cli/admin/admin_main.py

def main():
    """Admin CLI entry point."""

    # FIRST THING: Check elevation
    require_admin()  # Exits immediately if not elevated

    # Only reaches here if user has admin rights
    display_admin_menu()
```

### 2. File Permissions (Windows ACL)

**File**: `scripts/install_service.py`

```python
"""
Set Windows ACL Permissions

Protects config and data directories so traders cannot edit them.
"""

import win32security
import ntsecuritycon as con

def set_secure_permissions(directory_path: str):
    """
    Set Windows Access Control List (ACL) permissions.

    Permissions:
    - SYSTEM account: Full Control
    - Administrators group: Full Control
    - Users group: Read Only (can view, cannot edit)

    This ensures traders can view configs but cannot modify them.
    """

    # Get current security descriptor
    sd = win32security.GetFileSecurity(
        directory_path,
        win32security.DACL_SECURITY_INFORMATION
    )

    # Create new Discretionary Access Control List
    dacl = win32security.ACL()

    # SYSTEM account - Full Control
    system_sid = win32security.ConvertStringSidToSid("S-1-5-18")
    dacl.AddAccessAllowedAce(
        win32security.ACL_REVISION,
        con.FILE_ALL_ACCESS,
        system_sid
    )

    # Administrators group - Full Control
    admin_sid = win32security.ConvertStringSidToSid("S-1-5-32-544")
    dacl.AddAccessAllowedAce(
        win32security.ACL_REVISION,
        con.FILE_ALL_ACCESS,
        admin_sid
    )

    # Users group - Read Only
    users_sid = win32security.ConvertStringSidToSid("S-1-5-32-545")
    dacl.AddAccessAllowedAce(
        win32security.ACL_REVISION,
        con.FILE_GENERIC_READ,  # Read only!
        users_sid
    )

    # Apply DACL to directory
    sd.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(
        directory_path,
        win32security.DACL_SECURITY_INFORMATION,
        sd
    )

    print(f"✅ Secured: {directory_path}")
    print(f"   - Admins: Full Control")
    print(f"   - Users: Read Only")


def install_service():
    """Install Risk Manager as Windows Service with secure permissions."""

    config_dir = r"C:\ProgramData\RiskManager\config"
    data_dir = r"C:\ProgramData\RiskManager\data"

    # Create directories
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # Set secure permissions
    set_secure_permissions(config_dir)
    set_secure_permissions(data_dir)

    # Register Windows Service
    # ... (service registration code)
```

### 3. Windows Service Configuration

**File**: `src/service/windows_service.py`

```python
"""
Windows Service Implementation

Runs as LocalSystem (highest privilege).
Cannot be stopped by normal users.
"""

import win32serviceutil
import win32service
import win32event

class RiskManagerService(win32serviceutil.ServiceFramework):
    """Risk Manager Windows Service."""

    _svc_name_ = "RiskManagerV34"
    _svc_display_name_ = "Risk Manager V34"
    _svc_description_ = "Trading risk management protection service"

    # Service account: LocalSystem (highest privilege)
    # Normal users cannot stop this service
    _svc_account_ = None  # None = LocalSystem

    # Startup: Automatic (starts on boot)
    _svc_start_type_ = win32service.SERVICE_AUTO_START

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        """
        Called when service stop is requested.

        This can ONLY be called if:
        - User has administrator rights
        - User passed UAC prompt
        - Service Control Manager authorized the stop

        Normal users cannot reach this code path.
        """
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        """Main service loop - runs continuously."""
        # Start risk manager
        # ... (main daemon logic)
```

---

## 📋 Installation Process

### Initial Setup (Requires Admin)

```powershell
# Step 1: Run install script (requires elevation)
PS> python scripts/install_service.py

# Windows UAC Prompt appears:
┌─────────────────────────────────────────────┐
│  User Account Control                       │
│                                             │
│  Do you want to allow this app to make     │
│  changes to your device?                   │
│                                             │
│  install_service.py                         │
│                                             │
│  Enter administrator password: _______      │
└─────────────────────────────────────────────┘

# After entering admin password:
✅ Creating service directories...
✅ Secured: C:\ProgramData\RiskManager\config (Admins: RW, Users: R)
✅ Secured: C:\ProgramData\RiskManager\data (Admins: RW, Users: R)
✅ Registered Windows Service: RiskManagerV34
✅ Set startup type: Automatic
✅ Starting service...
✅ Risk Manager V34 service running!

# Service is now protected by Windows
```

---

## 🎬 Real-World Scenarios

### Scenario 1: Trader Hit Daily Loss Limit

```
Trader: Lost $500 (hit limit) → Account locked

Trader (frustrated): "I'll just stop the service!"

Attempt 1: Task Manager
  Action: Right-click "Risk Manager V34" → End Task
  Result: ❌ "Access Denied - Administrator privileges required"

Attempt 2: Kill via PowerShell
  Action: taskkill /F /IM risk-manager.exe
  Result: ❌ "Access Denied. You do not have permission."

Attempt 3: Stop Service
  Action: Services → Stop "Risk Manager V34"
  Result: 🔒 UAC Prompt appears → No password → Cannot proceed

Attempt 4: Edit Config
  Action: Edit risk_config.yaml → Change limit to -10000
  Result: ❌ "Access Denied. You need administrator permission."

Attempt 5: Delete State DB
  Action: Delete state.db (contains lockout info)
  Result: ❌ "Access Denied. Administrator permission required."

ALL ATTEMPTS FAIL ✅

Trader CLI shows:
┌──────────────────────────────────────────────────────────────┐
│ 🔒 LOCKOUT ACTIVE - Daily Loss Limit Exceeded               │
│                                                              │
│ Time Until Reset: 4h 32m                                     │
│                                                              │
│ ⚠️  You cannot trade until reset time or admin unlocks      │
│                                                              │
│ The service is protected by Windows.                         │
│ Only an administrator can unlock your account.               │
└──────────────────────────────────────────────────────────────┘

Trader: Forced to wait (system working as designed) ✅
```

### Scenario 2: Admin Overrides Lockout

```
Admin: "Let me help unlock this..."

Step 1: Open elevated terminal
  Action: Right-click PowerShell → "Run as Administrator"
  Result: UAC Prompt → Admin enters Windows password ✅

Step 2: Open Admin CLI
  Action: risk-manager admin
  Result: CLI opens (already elevated, no additional check needed)

Step 3: Manual unlock
╔══════════════════════════════════════════════════════════════╗
║              RISK MANAGER V34 - ADMIN CONSOLE                ║
╚══════════════════════════════════════════════════════════════╝

[1] View Status
[2] Configure Rules
[3] Manage Account
[4] Manual Unlock (Emergency Override)
[5] View All Logs
[6] Start/Stop Service
[7] Backup/Restore State
[Q] Quit

Select: 4

⚠️  Manual Unlock - Emergency Override

Current Lockouts:
  - Daily Realized Loss: Active until 17:00 EST (4h 28m)

Are you sure you want to remove all lockouts? [y/n]: y

✅ All lockouts removed
✅ Account unlocked
📝 Logged: "Manual unlock by administrator at 12:32 PM"

Trader can now trade again.
```

---

## 🔐 Security Layers Summary

```
Layer 1: Windows Service Protection
  - Runs as LocalSystem (highest privilege)
  - Cannot be stopped without admin rights
  - Auto-starts on boot
  - Protected by Windows Service Control Manager

Layer 2: File System ACL
  - Config files: Admins RW, Users R
  - State database: Admins RW, Users R
  - Logs: Admins RW, Users R
  - Enforced by Windows file system

Layer 3: UAC Elevation Requirement
  - Admin CLI checks elevation on startup
  - Exits immediately if not elevated
  - No custom password to bypass
  - Windows handles authentication

Layer 4: Process Protection
  - Service process cannot be killed by normal users
  - Task Manager blocks termination
  - Command-line kill commands blocked
  - Only elevated users can terminate

Result: Multi-layered Windows OS-level protection
```

---

## 💡 Why This Approach is Superior

### vs Custom Password System

| Custom Password | Windows UAC |
|-----------------|-------------|
| ❌ Password stored in code/file | ✅ No password storage needed |
| ❌ Can be forgotten | ✅ Just Windows admin password |
| ❌ Can be extracted from binary | ✅ OS-level security |
| ❌ Need reset mechanism | ✅ Windows handles password resets |
| ❌ Custom authentication code | ✅ OS handles authentication |
| ❌ Vulnerable to bypass | ✅ Cannot bypass Windows kernel |
| ❌ Not industry standard | ✅ How all Windows services work |

### Benefits

1. **No Password Management**: No custom password to store, hash, or forget
2. **OS-Level Security**: Protected by Windows kernel, not application code
3. **Industry Standard**: How all professional Windows services work
4. **User Familiarity**: Users understand "Run as Administrator"
5. **Impossible to Bypass**: Would require compromising Windows itself
6. **Centralized Control**: Windows admin controls everything
7. **Audit Trail**: Windows logs all UAC prompts and admin actions

---

## 📖 User Documentation

### For Traders

**Q: How do I check my status?**
```powershell
# Open Trader CLI (no admin needed)
PS> risk-manager trader
```

**Q: Why can't I unlock my account?**

A: The system is protecting you from emotional trading. Only an administrator (or daily reset) can unlock. This is by design.

**Q: Can I stop the service?**

A: No. You need administrator rights (Windows admin password). This prevents you from bypassing risk protection.

**Q: Can I edit the config to increase my limits?**

A: No. Config files are protected by Windows ACL. Only administrators can modify risk rules.

---

### For Administrators

**Q: How do I access Admin CLI?**

```powershell
# Step 1: Open elevated terminal
Right-click PowerShell → "Run as Administrator"

# Step 2: Windows UAC prompt appears
Enter your Windows admin password

# Step 3: Run admin CLI
PS> risk-manager admin
```

**Q: How do I unlock a trader's account?**

See "Scenario 2" above for complete walkthrough.

**Q: How do I modify risk rules?**

```powershell
# In Admin CLI (elevated terminal required)
PS> risk-manager admin

Select: [2] Configure Rules
→ Interactive wizard to modify all 12 rules
```

**Q: How do I stop the service temporarily?**

```powershell
# Option 1: Via Admin CLI
PS> risk-manager admin
Select: [6] Start/Stop Service → Stop

# Option 2: Via Windows Services
Services → Risk Manager V34 → Stop
(UAC prompt required)

# Option 3: Via PowerShell
PS> Stop-Service RiskManagerV34
(Must be running elevated)
```

---

## ✅ Testing the Security

### Verify Protection Works

```powershell
# Test 1: Trader cannot access Admin CLI
PS> risk-manager admin
# Expected: Error message + exits

# Test 2: Trader cannot kill service
PS> taskkill /F /IM risk-manager.exe
# Expected: Access Denied

# Test 3: Trader cannot edit config
# Action: Try to save changes to risk_config.yaml
# Expected: Windows "Access Denied" dialog

# Test 4: Admin CAN access Admin CLI
PS> # Right-click → Run as Administrator
PS> risk-manager admin
# Expected: Admin menu appears

# Test 5: Service survives reboot
# Action: Reboot computer
# Expected: Service auto-starts
```

---

## 🎯 Summary

**The Risk Manager security model**:
- Uses Windows UAC for admin protection (NO custom passwords)
- Trader is completely locked out of administrative functions
- Only Windows admin password can override protection
- Multi-layered OS-level security (service, ACL, UAC, process)
- Industry standard approach (how all Windows services work)
- Virtually unkillable without Windows admin rights

**This makes the system trustworthy - traders cannot bypass their own risk rules.**

---

**Created**: 2025-10-23
**Status**: ✅ Core Design Document
**Importance**: CRITICAL - This is what makes the system work
