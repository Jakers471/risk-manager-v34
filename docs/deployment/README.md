# Windows Service Deployment

**Risk Manager V34 - Production Deployment Documentation**

---

## Overview

This directory contains complete documentation for deploying Risk Manager V34 as a Windows Service with LocalSystem privileges.

The Windows Service implementation provides:
- ✅ 24/7 background operation
- ✅ Auto-start on system boot
- ✅ Automatic crash recovery
- ✅ LocalSystem privileges (unkillable by trader)
- ✅ Protected configuration files
- ✅ Enterprise-grade security

---

## Documentation Index

### Quick Start
📘 **[QUICKSTART.md](./QUICKSTART.md)** - 5-minute installation guide
- Prerequisites
- Step-by-step installation
- Basic configuration
- First-time setup
- Common commands

**Start here** if you want to get running quickly!

### Complete Guide
📗 **[WINDOWS_SERVICE.md](./WINDOWS_SERVICE.md)** - Comprehensive deployment guide
- Detailed installation instructions
- Complete configuration reference
- Service management (start/stop/restart)
- Troubleshooting procedures
- Security model explanation
- Monitoring and maintenance
- Backup and recovery
- Best practices

**Read this** for production deployments and advanced configuration.

---

## Installation Files

Located in project root:

### Installation Script
**`install_service.py`** - Automated installation
- Creates directories
- Copies configuration templates
- Installs Windows Service
- Configures crash recovery
- Validates installation

**Usage**: Right-click terminal → "Run as Administrator" → `python install_service.py`

### Uninstallation Script
**`uninstall_service.py`** - Service removal
- Stops service
- Uninstalls Windows Service
- Optionally removes data
- Clean uninstallation

**Usage**: Right-click terminal → "Run as Administrator" → `python uninstall_service.py`

---

## Service Implementation

Located in: `src/risk_manager/daemon/`

### Service Components

#### `service.py` - Windows Service Wrapper
- Windows Service class using pywin32
- Service lifecycle management (start/stop/restart)
- Windows Event Log integration
- Crash recovery handling
- LocalSystem privilege execution

#### `runner.py` - Service Controller
- Risk Manager lifecycle management
- Configuration loading
- SDK connection handling
- Async event loop management
- Graceful shutdown
- Health monitoring

#### `__init__.py` - Package Exports
- Public API for service components

---

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Service Manager                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Controls
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              RiskManagerService (LocalSystem)                │
│  • Windows Service wrapper                                   │
│  • Event log integration                                     │
│  • Crash recovery                                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Manages
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      ServiceRunner                           │
│  • Config loading                                            │
│  • Event loop management                                     │
│  • Graceful shutdown                                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Runs
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      RiskManager                             │
│  • Core risk management logic                                │
│  • SDK integration                                           │
│  • Rule enforcement                                          │
│  • Event processing                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## File Locations

### Production Deployment

**All data stored in**: `C:\ProgramData\RiskManagerV34\`

```
C:\ProgramData\RiskManagerV34\
├── config\
│   ├── risk_config.yaml       # Risk rules configuration
│   └── accounts.yaml          # TopstepX credentials
├── data\
│   ├── logs\
│   │   └── risk_manager.log   # Application logs
│   └── database\
│       └── state.db           # SQLite database
```

### Permissions

- **config\**: LocalSystem + Administrators (read/write)
- **data\**: LocalSystem (read/write), Administrators (read)
- **Trader**: No access to any files

---

## Security Model

### LocalSystem Privileges

The service runs as **LocalSystem** - the highest privilege level in Windows:

✅ **Protection**:
- Trader CANNOT stop service without Windows admin password
- Trader CANNOT edit configuration files
- Trader CANNOT kill service via Task Manager
- Trader CANNOT access data files

✅ **Only Windows Administrator can**:
- Stop the service
- Modify configuration
- View/edit data files
- Manage service settings

### Access Control

**Two Modes**:

1. **Admin Mode** (requires Windows admin password):
   - Full control
   - Can stop service
   - Can modify config
   - Can manage lockouts

2. **Trader Mode** (no admin required):
   - View-only access
   - See status and P&L
   - Cannot modify anything
   - Cannot stop service

**Implementation**: Windows UAC (User Account Control) - NO custom passwords!

---

## Service Management

### Common Operations

#### Start Service
```bash
net start RiskManagerV34
```

#### Stop Service (requires admin)
```bash
net stop RiskManagerV34
```

#### Restart Service (requires admin)
```bash
net stop RiskManagerV34 && net start RiskManagerV34
```

#### Check Status
```bash
sc query RiskManagerV34
```

#### View Logs
```bash
type "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log"
```

### Windows Services Console

1. Press `Win+R`
2. Type `services.msc`
3. Press Enter
4. Find "Risk Manager V34 - Trading Protection"

---

## Configuration

### Main Configuration

**File**: `C:\ProgramData\RiskManagerV34\config\risk_config.yaml`

**Example**:
```yaml
instruments:
  - MNQ
  - ES

max_daily_loss: -500.0
max_contracts: 2
max_daily_trades: 10

log_level: INFO
log_file: C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log
```

### Account Configuration

**File**: `C:\ProgramData\RiskManagerV34\config\accounts.yaml`

**Example**:
```yaml
accounts:
  - account_id: "ACC123456"
    username: "trader@example.com"
    password: "your_password"
    enabled: true
```

**⚠️ IMPORTANT**: Restart service after configuration changes!

---

## Logging and Monitoring

### Log Files

**Application Log**: `C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log`

Features:
- Daily rotation
- 30-day retention
- Detailed error messages
- 8 strategic checkpoints

**Checkpoints**:
1. 🚀 Service Start
2. ✅ Config Loaded
3. ✅ SDK Connected
4. ✅ Rules Initialized
5. ✅ Event Loop Running
6. 📨 Event Received
7. 🔍 Rule Evaluated
8. ⚠️ Enforcement Triggered

### Windows Event Log

**Location**: Windows Event Viewer → Application → Source: "RiskManagerV34"

**Event Types**:
- Information: Service start/stop
- Warning: Reconnections, non-critical issues
- Error: Crashes, critical failures

---

## Troubleshooting

### Service Won't Start

1. Check configuration file exists
2. Verify YAML syntax
3. Check Windows Event Log
4. Review application logs
5. Verify dependencies installed

### Service Crashes

1. Check Windows Event Log for exception
2. Review application logs
3. Run in debug mode (console)
4. Verify SDK connection
5. Check credentials

### Configuration Not Applied

**Solution**: Restart service after changes
```bash
net stop RiskManagerV34
net start RiskManagerV34
```

### Cannot Stop Service

**This is intentional!**

The service requires Windows admin password to stop - this is the security model working correctly.

**Solution**: Right-click terminal → "Run as Administrator" → Run stop command

---

## Backup and Recovery

### Configuration Backup

```bash
# Backup
robocopy "C:\ProgramData\RiskManagerV34\config" "D:\Backups\config" /E

# Restore
robocopy "D:\Backups\config" "C:\ProgramData\RiskManagerV34\config" /E
```

### Database Backup

```bash
# Stop service first
net stop RiskManagerV34

# Backup database
copy "C:\ProgramData\RiskManagerV34\data\database\state.db" "D:\Backups\state.db"

# Restart service
net start RiskManagerV34
```

---

## Best Practices

### Security
- ✅ Use strong passwords
- ✅ Enable BitLocker disk encryption
- ✅ Rotate credentials every 90 days
- ✅ Regular configuration backups
- ✅ Monitor Windows Event Log daily

### Operations
- ✅ Monitor service status daily
- ✅ Review logs for warnings/errors
- ✅ Test disaster recovery monthly
- ✅ Keep Windows updated
- ✅ Document configuration changes

### Configuration
- ✅ Start with conservative limits
- ✅ Test changes thoroughly
- ✅ Keep backup of working config
- ✅ Document all rule changes
- ✅ Review and adjust weekly

---

## Additional Resources

### Documentation
- **Configuration Guide**: `docs/current/CONFIG_FORMATS.md`
- **Security Model**: `docs/current/SECURITY_MODEL.md`
- **SDK Integration**: `docs/current/SDK_INTEGRATION_GUIDE.md`
- **Testing Guide**: `docs/testing/TESTING_GUIDE.md`

### Support
- Check this documentation first
- Review logs for error messages
- Check Windows Event Log
- Consult project documentation

---

## Version Information

- **Version**: 1.0.0
- **Last Updated**: 2025-10-28
- **Python**: 3.12+
- **Windows**: 10/11, Server 2016+
- **Dependencies**: See `requirements.txt`

---

**Ready to deploy! 🚀**

For quick setup, start with [QUICKSTART.md](./QUICKSTART.md)

For complete guide, read [WINDOWS_SERVICE.md](./WINDOWS_SERVICE.md)
