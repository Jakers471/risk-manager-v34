# Admin CLI Service Commands - Quick Reference

## Overview

The Admin CLI now has enhanced visual output for all service control commands using Rich library panels and colors.

## Commands

### `admin_cli service status`

**Purpose**: View current service status with real-time metrics

**Output Sections**:
- Service State (Running/Stopped)
- Process Info (PID, uptime, CPU, memory)
- Connection Status (API, SDK, Database)
- Monitoring Info (Account, Rules, Lockouts)

**Usage**:
```bash
admin_cli service status
```

**Requires Admin**: No (read-only)

---

### `admin_cli service start`

**Purpose**: Start the Risk Manager Windows Service

**Features**:
- Checks if service is already running
- Waits up to 30 seconds for service to start
- Shows PID, monitored account, active rules
- Displays SDK connection status

**Usage**:
```bash
admin_cli service start
```

**Requires Admin**: Yes (UAC elevation required)

**Exit Codes**:
- `0` = Success or already running
- `1` = Error (service not installed, failed to start)

---

### `admin_cli service stop`

**Purpose**: Stop the Risk Manager Windows Service

**Features**:
- Shows WARNING confirmation before stopping
- Requires explicit user confirmation (`y/N`)
- Displays risk enforcement disabled warning
- Waits up to 30 seconds for graceful shutdown

**Usage**:
```bash
admin_cli service stop
```

**Requires Admin**: Yes (UAC elevation required)

**Warning**: Stopping the service disables ALL risk protection!

**Exit Codes**:
- `0` = Success or already stopped or cancelled by user
- `1` = Error (service not installed, failed to stop)

---

### `admin_cli service restart`

**Purpose**: Restart the service (stop + start)

**Features**:
- Shows progress for both stop and start phases
- Displays old and new PID
- Confirms configuration reload
- Useful after config changes

**Usage**:
```bash
admin_cli service restart
```

**Requires Admin**: Yes (UAC elevation required)

**Exit Codes**:
- `0` = Success
- `1` = Error (service not installed, failed to restart)

---

## Visual Elements

### Box Styles
- **Double-line borders** (`╔═══╗`) for main panels
- **Single-line dividers** (`------`) for section headers
- **Color-coded borders**:
  - Cyan = Normal/In Progress
  - Green = Success
  - Yellow = Warning
  - Red = Error

### Status Indicators
- `[*]` Service running
- `[ ]` Service stopped
- `>` Operation in progress
- `[OK]` Success indicator
- `[!]` Warning/Error indicator

### Color Meanings
- **Green text**: Success, running state, connected
- **Yellow text**: Warnings, pending actions
- **Red text**: Errors, disabled state, critical warnings
- **Cyan text**: Account IDs, command names, highlights
- **Dim text**: Secondary info (PIDs, latencies, timestamps)

---

## Common Scenarios

### Check if service is running
```bash
admin_cli service status
```
Look for `State: [*] RUNNING` in output.

### Start service after system boot
```bash
# Right-click PowerShell → Run as Administrator
admin_cli service start
```

### Stop service for maintenance
```bash
# Right-click PowerShell → Run as Administrator
admin_cli service stop
# Confirm with 'y' when prompted
```

### Reload configuration changes
```bash
# After editing config/risk_config.yaml
admin_cli service restart
```

### Troubleshoot service not starting
```bash
# Check status
admin_cli service status

# Check Windows Event Log for errors
# Event Viewer → Windows Logs → Application
# Look for RiskManagerV34 events
```

---

## Error Messages

### "Service not installed!"
**Cause**: Windows Service not installed on system

**Solution**: Run service installation:
```bash
admin_cli service install
```

### "Administrator Privileges Required"
**Cause**: Not running as administrator

**Solution**:
1. Right-click PowerShell or Command Prompt
2. Select "Run as Administrator"
3. Enter Windows admin password when prompted
4. Run command again

### "Service already running"
**Cause**: Attempting to start service that's already running

**Solution**: No action needed. Use `service status` to view details or `service restart` to restart.

### "Service already stopped"
**Cause**: Attempting to stop service that's not running

**Solution**: No action needed. Use `service start` to start the service.

---

## Performance Notes

- Status checks are fast (<100ms)
- Start/stop operations wait up to 30 seconds
- CPU measurement uses 0.1s sampling interval
- All commands complete in <1 second (except waiting for state change)

---

## Dependencies

All required packages are already installed:
- `rich` - Visual output
- `typer` - CLI framework
- `pywin32` - Windows Service API
- `psutil` - Process monitoring
- `pyyaml` - Config loading

---

## See Also

- **Full Implementation**: `SERVICE_PANEL_IMPLEMENTATION_SUMMARY.md`
- **Visual Demo**: Run `python demo_service_panel.py`
- **Admin CLI Spec**: `docs/specifications/unified/admin-cli-reference.md`
- **Windows Service**: `src/risk_manager/daemon/service.py`
- **Helper Functions**: `src/risk_manager/cli/service_helpers.py`

---

**Last Updated**: 2025-10-28
**Version**: Risk Manager V34
