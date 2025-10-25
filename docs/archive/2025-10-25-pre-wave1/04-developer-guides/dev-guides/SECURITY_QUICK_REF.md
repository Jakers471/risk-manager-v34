# Security Quick Reference

**For complete details**: See [docs/current/SECURITY_MODEL.md](../current/SECURITY_MODEL.md)

---

## 🔐 Core Concept

**Windows UAC-based security. NO custom passwords.**

---

## Two Access Levels

### Admin CLI (Elevated)
```powershell
# Right-click terminal → "Run as Administrator"
# Windows UAC prompt → Enter Windows admin password
risk-manager admin

# Can:
✅ Configure rules
✅ Unlock accounts
✅ Stop service
✅ Edit settings
```

### Trader CLI (Normal)
```powershell
# Normal terminal (no elevation)
risk-manager trader

# Can:
✅ View status
✅ View P&L
✅ View lockouts
✅ View logs

# Cannot:
❌ Edit anything
❌ Unlock
❌ Stop service
```

---

## What Trader Cannot Do

❌ Kill service in Task Manager (Access Denied)
❌ Stop service via command line (Requires admin)
❌ Edit config files (Windows ACL: Read Only)
❌ Delete state database (Protected directory)
❌ Run Admin CLI (Elevation check exits immediately)

**All blocked by Windows OS - not application code.**

---

## Implementation Checklist

### Admin CLI Entry Point
```python
# src/cli/admin/admin_main.py

from .auth import require_admin

def main():
    require_admin()  # Exits if not elevated
    display_admin_menu()
```

### Check Elevation
```python
# src/cli/admin/auth.py

import ctypes

def is_admin() -> bool:
    """Check Windows elevation."""
    return ctypes.windll.shell32.IsUserAnAdmin()

def require_admin():
    """Exit if not elevated."""
    if not is_admin():
        print("❌ Admin privileges required")
        print("Right-click terminal → Run as Administrator")
        sys.exit(1)
```

### File Permissions
```python
# scripts/install_service.py

def set_secure_permissions(dir_path):
    """Set ACL: Admin RW, Users R."""
    # SYSTEM: Full Control
    # Administrators: Full Control
    # Users: Read Only
    # (See SECURITY_MODEL.md for full code)
```

### Windows Service
```python
# src/service/windows_service.py

class RiskManagerService(ServiceFramework):
    _svc_account_ = None  # LocalSystem
    _svc_start_type_ = SERVICE_AUTO_START
    # Protected by Windows Service Control Manager
```

---

## Testing

### Verify Trader Cannot Access Admin
```powershell
PS> risk-manager admin
# Expected: Error + exit
```

### Verify Admin Can Access
```powershell
PS> # Right-click → Run as Administrator
PS> risk-manager admin
# Expected: Admin menu appears
```

### Verify File Protection
```
Try to edit: C:\ProgramData\RiskManager\config\risk_config.yaml
Expected: Windows "Access Denied" when saving
```

### Verify Service Protection
```powershell
PS> taskkill /F /IM risk-manager.exe
# Expected: Access Denied
```

---

## Key Files

- **Security Model**: `docs/current/SECURITY_MODEL.md` (22KB complete guide)
- **Auth Check**: `src/cli/admin/auth.py` (elevation check)
- **Install Script**: `scripts/install_service.py` (ACL setup)
- **Service**: `src/service/windows_service.py` (Windows Service)

---

## Summary

**Protection Layers**:
1. Windows Service (LocalSystem account)
2. File ACL (Admin RW, Users R)
3. UAC elevation requirement (Admin CLI)
4. Process protection (cannot kill)

**Result**: Trader cannot bypass risk protection without Windows admin password.

**Industry standard approach - no custom passwords to manage.**

---

**Created**: 2025-10-23
**See**: [SECURITY_MODEL.md](../current/SECURITY_MODEL.md) for complete details
