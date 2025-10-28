# Windows Service Quick Reference

**Risk Manager V34 - Command Quick Reference**

---

## Installation

```bash
# Install service (requires admin)
python install_service.py

# Uninstall service (requires admin)
python uninstall_service.py

# Uninstall but keep data (requires admin)
python uninstall_service.py --keep-data
```

---

## Service Control

### Start/Stop/Restart

```bash
# Start service
net start RiskManagerV34

# Stop service (requires admin)
net stop RiskManagerV34

# Restart service (requires admin)
net stop RiskManagerV34 && net start RiskManagerV34
```

### Status Check

```bash
# Query service status
sc query RiskManagerV34

# PowerShell alternative
Get-Service -Name "RiskManagerV34"
```

**Status Codes**:
- `1 STOPPED` - Service not running
- `2 START_PENDING` - Service starting
- `3 STOP_PENDING` - Service stopping
- `4 RUNNING` - Service running normally ✅

---

## Configuration

### File Locations

```
Config:    C:\ProgramData\RiskManagerV34\config\risk_config.yaml
Accounts:  C:\ProgramData\RiskManagerV34\config\accounts.yaml
Logs:      C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log
Database:  C:\ProgramData\RiskManagerV34\data\database\state.db
```

### Edit Configuration

```bash
# Edit risk config (as admin)
notepad C:\ProgramData\RiskManagerV34\config\risk_config.yaml

# Edit accounts (as admin)
notepad C:\ProgramData\RiskManagerV34\config\accounts.yaml

# IMPORTANT: Restart service after changes!
net stop RiskManagerV34 && net start RiskManagerV34
```

---

## Logging

### View Logs

```bash
# View last 50 lines
Get-Content "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log" -Tail 50

# Watch live (follow mode)
Get-Content "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log" -Wait

# Search logs for errors
Select-String "ERROR" "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log"
```

### Check Windows Event Log

```bash
# Open Event Viewer
eventvwr

# Navigate to: Windows Logs → Application
# Filter by source: "RiskManagerV34"
```

---

## Troubleshooting

### Service Won't Start

```bash
# 1. Check config exists
dir "C:\ProgramData\RiskManagerV34\config\risk_config.yaml"

# 2. Check Windows Event Log
eventvwr

# 3. Run in debug mode
python -m risk_manager.daemon.runner "C:\ProgramData\RiskManagerV34\config\risk_config.yaml"
```

### Configuration Not Applied

```bash
# Restart service
net stop RiskManagerV34
net start RiskManagerV34
```

### High CPU/Memory

```bash
# Check service status
sc query RiskManagerV34

# Restart service
net stop RiskManagerV34
net start RiskManagerV34
```

---

## Health Check Checkpoints

Look for these in logs:

```
🚀 Service Start
✅ Config Loaded
✅ SDK Connected
✅ Rules Initialized
✅ Event Loop Running
📨 Event Received
🔍 Rule Evaluated
⚠️ Enforcement Triggered
```

**All 8 checkpoints = Healthy service ✅**

---

## Backup and Recovery

### Backup Configuration

```bash
# Backup config
robocopy "C:\ProgramData\RiskManagerV34\config" "D:\Backups\config" /E

# Restore config
robocopy "D:\Backups\config" "C:\ProgramData\RiskManagerV34\config" /E
```

### Backup Database

```bash
# Stop service
net stop RiskManagerV34

# Backup database
copy "C:\ProgramData\RiskManagerV34\data\database\state.db" "D:\Backups\state.db"

# Start service
net start RiskManagerV34
```

---

## Service Properties

```
Name:         RiskManagerV34
Display Name: Risk Manager V34 - Trading Protection
Start Type:   Automatic
Account:      LocalSystem
Recovery:     Restart on failure (1 min delay)
```

---

## Security Notes

- ✅ **Service runs as LocalSystem** (highest privilege)
- ✅ **Requires Windows admin password to stop**
- ✅ **Trader CANNOT kill service or edit config**
- ✅ **Uses Windows UAC** (no custom passwords)

---

## Common Workflows

### Daily Check

```bash
# 1. Check service status
sc query RiskManagerV34

# 2. View recent logs
Get-Content "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log" -Tail 50

# 3. Check for errors
Select-String "ERROR" "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log" -Tail 20
```

### After Config Change

```bash
# 1. Edit config
notepad C:\ProgramData\RiskManagerV34\config\risk_config.yaml

# 2. Restart service (as admin)
net stop RiskManagerV34
net start RiskManagerV34

# 3. Verify restart
sc query RiskManagerV34

# 4. Check logs
Get-Content "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log" -Tail 20
```

### Monthly Maintenance

```bash
# 1. Check disk space
Get-PSDrive C

# 2. Review log size
Get-ChildItem "C:\ProgramData\RiskManagerV34\data\logs\" -Recurse | Measure-Object -Property Length -Sum

# 3. Backup config
robocopy "C:\ProgramData\RiskManagerV34\config" "D:\Backups\config_$(Get-Date -Format 'yyyy-MM-dd')" /E

# 4. Backup database
net stop RiskManagerV34
copy "C:\ProgramData\RiskManagerV34\data\database\state.db" "D:\Backups\state_$(Get-Date -Format 'yyyy-MM-dd').db"
net start RiskManagerV34
```

---

## Help and Documentation

### Quick Start
- 5-minute guide: `docs/deployment/QUICKSTART.md`

### Complete Guide
- Full documentation: `docs/deployment/WINDOWS_SERVICE.md`

### Configuration
- Config reference: `docs/current/CONFIG_FORMATS.md`

### Security
- Security model: `docs/current/SECURITY_MODEL.md`

### Testing
- Testing guide: `docs/testing/TESTING_GUIDE.md`

---

**Keep this reference handy for quick service management!**
