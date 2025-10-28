# Windows Service Deployment Guide

**Risk Manager V34 - Windows Service Installation**

This guide covers installation, configuration, and management of the Risk Manager as a Windows Service with LocalSystem privileges.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Service Management](#service-management)
6. [Troubleshooting](#troubleshooting)
7. [Security Model](#security-model)
8. [Uninstallation](#uninstallation)

---

## Overview

The Risk Manager Windows Service provides:

- **24/7 Operation**: Runs continuously in background
- **Auto-Start**: Starts automatically on system boot
- **Crash Recovery**: Automatically restarts on failure
- **LocalSystem Privilege**: Highest security level
- **Unkillable by Trader**: Requires Windows admin password to stop
- **Protected Configuration**: Files protected by Windows ACL

### Service Details

- **Name**: `RiskManagerV34`
- **Display Name**: `Risk Manager V34 - Trading Protection`
- **Description**: Automated risk management for TopstepX trading accounts
- **Start Type**: Automatic
- **Account**: LocalSystem
- **Recovery**: Restart on failure (3 attempts, 1 min delay)

---

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11 or Windows Server 2016+
- **Python**: 3.12 or higher
- **Privileges**: Administrator access required for installation
- **Disk Space**: 500 MB minimum
- **Network**: Internet connection for TopstepX API

### Python Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `pywin32` - Windows Service support
- `project-x-py` - TopstepX SDK
- `loguru` - Logging
- `pydantic` - Configuration validation
- `sqlalchemy` - Database

---

## Installation

### Step 1: Download and Extract

1. Download Risk Manager V34 package
2. Extract to preferred location (e.g., `C:\RiskManager`)
3. Open terminal in extracted directory

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or using uv (recommended)
uv pip install -r requirements.txt
```

### Step 3: Run Installation Script

**IMPORTANT**: Must run with Administrator privileges

#### Option A: Right-click Terminal

1. Right-click on Command Prompt or PowerShell
2. Select "Run as Administrator"
3. Navigate to project directory
4. Run installation script:

```bash
python install_service.py
```

#### Option B: UAC Prompt

1. Run installation script normally:
   ```bash
   python install_service.py
   ```
2. Accept UAC prompt when requested

### Step 4: Installation Process

The installer will:

1. ✅ Verify Administrator privileges
2. ✅ Create directories in `C:\ProgramData\RiskManagerV34\`
3. ✅ Copy configuration templates
4. ✅ Install Windows Service
5. ✅ Configure crash recovery
6. ✅ Validate installation

### Step 5: Verify Installation

Check service installation:

```bash
# Check service status
sc query RiskManagerV34

# Or use services.msc
services.msc
```

Look for "Risk Manager V34 - Trading Protection" in services list.

---

## Configuration

### Configuration Files

Located in: `C:\ProgramData\RiskManagerV34\config\`

#### 1. risk_config.yaml

Main configuration file for risk rules and limits.

**Example**:

```yaml
# Risk Manager Configuration

# Instruments to monitor
instruments:
  - MNQ
  - ES
  - NQ

# Risk limits
max_daily_loss: -500.0        # Maximum daily loss ($500)
max_contracts: 2               # Maximum contracts per position
max_daily_trades: 10          # Maximum trades per day

# Logging
log_level: INFO
log_file: C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log

# TopstepX SDK settings
sdk:
  base_url: https://gateway.topstepx.com
  reconnect_attempts: 5
  reconnect_delay: 5

# Database
database:
  path: C:\ProgramData\RiskManagerV34\data\database\state.db
```

#### 2. accounts.yaml

TopstepX account credentials and mappings.

**Example**:

```yaml
# TopstepX Account Configuration

accounts:
  - account_id: "ACC123456"
    username: "trader@example.com"
    password: "your_password"  # IMPORTANT: Secure this file!
    enabled: true

  - account_id: "ACC789012"
    username: "trader2@example.com"
    password: "your_password2"
    enabled: false  # Disabled account
```

**⚠️ SECURITY WARNING**:
- Passwords stored in plain text
- Protect this file with Windows ACL
- Only LocalSystem and Administrators can access
- Never commit to version control

### Editing Configuration

**Option A: Notepad (as Administrator)**

1. Right-click Notepad → "Run as Administrator"
2. Open configuration file
3. Make changes and save

**Option B: Command Line**

```bash
# Edit risk config
notepad C:\ProgramData\RiskManagerV34\config\risk_config.yaml

# Edit accounts
notepad C:\ProgramData\RiskManagerV34\config\accounts.yaml
```

**⚠️ IMPORTANT**: Restart service after configuration changes!

---

## Service Management

### Starting the Service

#### Option A: Services Console

1. Press `Win+R` → Type `services.msc` → Enter
2. Find "Risk Manager V34 - Trading Protection"
3. Right-click → Start

#### Option B: Command Line

```bash
# Start service
net start RiskManagerV34

# Or using sc
sc start RiskManagerV34
```

#### Option C: PowerShell

```powershell
Start-Service -Name "RiskManagerV34"
```

### Stopping the Service

**⚠️ REQUIRES ADMINISTRATOR PRIVILEGES**

#### Option A: Services Console

1. Right-click terminal → "Run as Administrator"
2. Press `Win+R` → Type `services.msc` → Enter
3. Find "Risk Manager V34"
4. Right-click → Stop

#### Option B: Command Line (as Admin)

```bash
# Stop service
net stop RiskManagerV34

# Or using sc
sc stop RiskManagerV34
```

### Restarting the Service

**After configuration changes:**

```bash
# Restart service
net stop RiskManagerV34 && net start RiskManagerV34

# Or using PowerShell
Restart-Service -Name "RiskManagerV34"
```

### Checking Service Status

```bash
# Query service status
sc query RiskManagerV34

# Or using PowerShell
Get-Service -Name "RiskManagerV34"
```

**Status Codes**:
- `STOPPED` (1) - Service not running
- `START_PENDING` (2) - Service starting
- `STOP_PENDING` (3) - Service stopping
- `RUNNING` (4) - Service running normally

### Viewing Logs

#### File Logs

**Location**: `C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log`

```bash
# View last 50 lines
Get-Content "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log" -Tail 50

# Watch live
Get-Content "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log" -Wait
```

#### Windows Event Logs

1. Press `Win+R` → Type `eventvwr` → Enter
2. Navigate to: Windows Logs → Application
3. Filter by source: "RiskManagerV34"

**Event Types**:
- **Information**: Service start/stop, normal operations
- **Warning**: Non-critical issues, reconnections
- **Error**: Critical failures, crashes

---

## Troubleshooting

### Service Won't Start

**Symptom**: Service fails to start or starts then stops

**Possible Causes**:

1. **Missing Configuration**
   ```bash
   # Check if config exists
   dir "C:\ProgramData\RiskManagerV34\config\risk_config.yaml"
   ```

   **Solution**: Run `install_service.py` again

2. **Invalid Configuration**
   - Check logs for validation errors
   - Verify YAML syntax
   - Ensure all required fields present

3. **Missing Dependencies**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

4. **Permission Issues**
   - Ensure service running as LocalSystem
   - Check file permissions on config directory

### Service Crashes Repeatedly

**Symptom**: Service starts but crashes within seconds/minutes

**Steps**:

1. **Check Windows Event Log**
   - Look for error messages
   - Note exception details

2. **Check File Logs**
   ```bash
   type "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log"
   ```

3. **Run in Debug Mode** (temporary)
   ```bash
   # Stop service
   net stop RiskManagerV34

   # Run in console for debugging
   python -m risk_manager.daemon.runner "C:\ProgramData\RiskManagerV34\config\risk_config.yaml"
   ```

4. **Check SDK Connection**
   - Verify internet connection
   - Check TopstepX credentials
   - Ensure API accessible

### Configuration Not Applied

**Symptom**: Changes to config not reflected in service behavior

**Solution**: Restart service after config changes

```bash
net stop RiskManagerV34
net start RiskManagerV34
```

### Cannot Stop Service

**Symptom**: Service refuses to stop or requires admin password

**This is intentional security behavior!**

**Solution**:
1. Right-click terminal → "Run as Administrator"
2. Run stop command with admin privileges
3. Enter Windows admin password when prompted

### High CPU/Memory Usage

**Normal Behavior**:
- CPU: 1-5% during active trading
- Memory: 50-100 MB

**Excessive Usage**:
1. Check number of instruments being monitored
2. Review log verbosity settings
3. Check for SDK connection issues
4. Restart service if memory leak suspected

---

## Security Model

### LocalSystem Privileges

The service runs as **LocalSystem** account:

- ✅ Highest privilege level
- ✅ Cannot be killed by trader without admin password
- ✅ Protected from tampering
- ✅ Full access to system resources

### File Permissions

**Configuration Files** (`C:\ProgramData\RiskManagerV34\config\`):
- **Read/Write**: LocalSystem, Administrators
- **No Access**: Standard users (trader)

**Data Files** (`C:\ProgramData\RiskManagerV34\data\`):
- **Read/Write**: LocalSystem
- **Read Only**: Administrators
- **No Access**: Standard users

### Password Security

**⚠️ CRITICAL**: Account passwords stored in plain text

**Protection Measures**:
1. File permissions restrict access to LocalSystem/Administrators
2. Encrypt disk if possible (BitLocker)
3. Never commit accounts.yaml to version control
4. Rotate passwords regularly
5. Use strong, unique passwords

**Future Enhancement**: Encrypted credential storage planned

### Access Control

**Two Access Levels**:

1. **Admin Mode** (requires Windows admin password)
   - Start/stop service
   - Modify configuration
   - View all logs
   - Manage lockouts

2. **Trader Mode** (no admin required)
   - View status (read-only)
   - View current P&L
   - View lockouts
   - Cannot modify anything

---

## Uninstallation

### Complete Removal

**Removes service AND all data:**

```bash
# Run as Administrator
python uninstall_service.py
```

**This will remove**:
- Windows Service
- All configuration files
- All log files
- All database files
- Complete trading history

### Keep Data

**Removes service but keeps data:**

```bash
# Run as Administrator
python uninstall_service.py --keep-data
```

**This will**:
- ✅ Remove Windows Service
- ✅ Keep configuration files
- ✅ Keep log files
- ✅ Keep database files

**Data location**: `C:\ProgramData\RiskManagerV34\`

### Manual Cleanup

If automatic uninstall fails:

```bash
# 1. Stop service
net stop RiskManagerV34

# 2. Delete service
sc delete RiskManagerV34

# 3. Manually delete data (optional)
rmdir /S "C:\ProgramData\RiskManagerV34"
```

---

## Advanced Configuration

### Auto-Start on Boot

**Already configured by default!**

To disable auto-start:

```bash
# Set to manual start
sc config RiskManagerV34 start= demand

# To re-enable auto-start
sc config RiskManagerV34 start= auto
```

### Service Recovery Options

**Already configured by default:**
- First failure: Restart after 1 minute
- Second failure: Restart after 1 minute
- Subsequent failures: Restart after 1 minute
- Reset failure count: After 24 hours

**To customize**:

```bash
# Example: restart after 30 seconds
sc failure RiskManagerV34 reset= 86400 actions= restart/30000/restart/30000/restart/30000
```

### Multiple Service Instances

To run multiple independent instances:

1. Modify service name in `service.py`
2. Change config paths
3. Install with different service name
4. Each instance needs separate config

---

## Monitoring and Maintenance

### Health Checks

**Daily**:
- Check service status: `sc query RiskManagerV34`
- Review logs for errors
- Verify trading activity

**Weekly**:
- Check disk space
- Review log file size
- Verify backup of database

**Monthly**:
- Rotate log files if needed
- Update credentials if required
- Review and update risk rules

### Log Rotation

Logs rotate automatically:
- **Rotation**: Daily at midnight
- **Retention**: 30 days
- **Location**: `C:\ProgramData\RiskManagerV34\data\logs\`

### Backup and Recovery

**Configuration Backup**:

```bash
# Backup config directory
robocopy "C:\ProgramData\RiskManagerV34\config" "D:\Backups\RiskManager\config" /E

# Restore config
robocopy "D:\Backups\RiskManager\config" "C:\ProgramData\RiskManagerV34\config" /E
```

**Database Backup**:

```bash
# Stop service first
net stop RiskManagerV34

# Backup database
copy "C:\ProgramData\RiskManagerV34\data\database\state.db" "D:\Backups\RiskManager\state.db"

# Start service
net start RiskManagerV34
```

---

## Best Practices

### Security
- ✅ Use strong passwords for TopstepX accounts
- ✅ Rotate credentials every 90 days
- ✅ Enable BitLocker disk encryption
- ✅ Regular backups of configuration
- ✅ Monitor Windows Event Log daily
- ✅ Keep Windows updated with latest security patches

### Configuration
- ✅ Start with conservative risk limits
- ✅ Test configuration changes thoroughly
- ✅ Document all changes
- ✅ Keep backup of working configuration
- ✅ Review rules weekly

### Operations
- ✅ Monitor service status daily
- ✅ Check logs for warnings/errors
- ✅ Verify trading activity aligns with rules
- ✅ Review enforcement actions
- ✅ Test disaster recovery procedures

---

## Support and Documentation

### Additional Resources

- **Configuration Guide**: `docs/current/CONFIG_FORMATS.md`
- **Security Model**: `docs/current/SECURITY_MODEL.md`
- **SDK Integration**: `docs/current/SDK_INTEGRATION_GUIDE.md`
- **Testing Guide**: `docs/testing/TESTING_GUIDE.md`

### Getting Help

1. Check this documentation
2. Review logs for error messages
3. Check Windows Event Log
4. Review test reports
5. Consult project documentation

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0
**Maintainer**: Risk Manager V34 Team
