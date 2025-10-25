# Daemon Lifecycle Specification

**Document ID:** DAEMON-LIFECYCLE-001
**Version:** 1.0
**Created:** 2025-10-25
**Status:** Production Specification

---

## Overview

Risk Manager V34 operates as a **background daemon** running as a Windows Service. This document specifies how the daemon works, including startup, operation, shutdown, and admin/trader separation.

---

## Daemon Architecture

### Core Concept

```
Admin configures → Daemon runs continuously → Trader trades normally
                    ↓
              Cannot be stopped by trader (UAC protected)
```

**Key Characteristics:**
- Runs as Windows Service (LocalSystem account)
- Auto-starts on computer boot/login
- Admin-only control (UAC elevation required)
- Trader has view-only access via Trader CLI
- Configuration protected by Windows ACL

---

## Lifecycle Stages

### Stage 1: Initial Setup (Admin - One Time)

**Who:** Administrator (has Windows admin password)

**Steps:**
1. Install Windows Service
   ```powershell
   # Run as Administrator
   python scripts/install_service.py
   ```

2. Configure API Credentials
   ```yaml
   # C:/ProgramData/RiskManager/config/accounts.yaml
   topstepx:
     username: "trader_username"
     api_key: "your_api_key_here"

   monitored_account:
     account_id: 123
     account_name: "Main Trading Account"
   ```

3. Configure Risk Rules
   ```yaml
   # C:/ProgramData/RiskManager/config/risk_config.yaml
   daily_realized_loss:
     enabled: true
     limit: -500
     reset_time: "17:00"
     timezone: "America/New_York"

   max_contracts:
     enabled: true
     limit: 5
   ```

4. Start Daemon
   ```powershell
   # Admin CLI or command line
   sc start RiskManagerV34
   ```

**Result:** Daemon running, ready to protect account

---

### Stage 2: Daily Operation (Trader - Normal Use)

**Who:** Trader (no admin privileges needed)

**Flow:**
```
Computer Boots
    ↓
Windows Service Auto-Starts
    ↓
Daemon Connects to SDK
    ↓
Trader Logs In
    ↓
Opens Trader CLI (view-only)
    ↓
Trades Normally
```

**Trader Experience:**
1. **Turn on computer**
   - Windows starts
   - Risk Manager service auto-starts (background)
   - Trader doesn't see anything yet

2. **Log in to trading platform**
   - Trader logs in to broker (TopstepX)
   - Daemon already monitoring via SDK

3. **Open Trader CLI (optional)**
   ```bash
   risk-manager trader
   ```
   - View account status
   - See lockout timers
   - Check P&L
   - View enforcement log
   - **Cannot modify anything**

4. **Trade throughout day**
   - Daemon monitors every event
   - Enforces rules automatically
   - CLI updates in real-time

**Trader CANNOT:**
- Stop the daemon (requires admin password)
- Edit configuration files (Windows ACL blocks access)
- Run Admin CLI (UAC check fails)
- Bypass risk rules
- Unlock account (admin-only operation)

**Trader CAN:**
- View account status
- See why positions were closed
- Check lockout timers
- View enforcement history
- Clock in/out (consistency tracking)

---

### Stage 3: Reconfiguration (Admin - As Needed)

**Who:** Administrator (to change settings)

**When:**
- Modify risk rule limits
- Update API credentials
- Change reset times
- Add/remove rules
- Emergency unlock

**Steps:**
1. **Stop Daemon**
   ```powershell
   # Admin CLI or PowerShell
   sc stop RiskManagerV34
   ```

2. **Edit Configuration**
   ```powershell
   # Edit risk rules
   notepad C:\ProgramData\RiskManager\config\risk_config.yaml

   # Or use Admin CLI wizard
   risk-manager admin
   ```

3. **Restart Daemon**
   ```powershell
   # Reload new configuration
   sc start RiskManagerV34
   ```

4. **Verify Changes**
   ```powershell
   # Check service status
   sc query RiskManagerV34

   # View logs
   cat C:\ProgramData\RiskManager\logs\daemon.log
   ```

**Result:** New configuration loaded, daemon protecting with updated rules

**Note:** Admin can reconfigure anytime - not a "one-time setup" system

---

### Stage 4: Crash Recovery (Automatic)

**What Happens:**
```
Daemon Crashes (exception, power loss, etc.)
    ↓
Windows Service Manager Detects Failure
    ↓
Wait 1 Minute (Recovery Policy)
    ↓
Auto-Restart Service
    ↓
Load State from SQLite
    ↓
Resume Monitoring
```

**State Recovery:**
1. **Load Lockouts from Database**
   ```sql
   SELECT account_id, reason, expires_at
   FROM lockouts
   WHERE expires_at > NOW()
   ```

2. **Load Daily P&L**
   ```sql
   SELECT account_id, realized_pnl, unrealized_pnl
   FROM daily_pnl
   WHERE date = TODAY()
   ```

3. **Reconnect to SDK**
   - Authenticate with API key
   - Subscribe to account events
   - Resume event processing

4. **Restore Timers**
   - Recalculate remaining time on lockouts
   - Restart countdown timers
   - Resume background tasks

**Result:** Seamless recovery - no loss of protection

**Critical:** Daily lockouts persist across crashes (can't escape by rebooting)

---

## Admin vs Trader Separation

### Access Control

| Operation | Admin | Trader |
|-----------|-------|--------|
| **Start/Stop Service** | ✅ Yes | ❌ No (requires admin password) |
| **Edit Configurations** | ✅ Yes | ❌ No (Windows ACL blocks) |
| **View Status** | ✅ Yes | ✅ Yes |
| **Emergency Unlock** | ✅ Yes | ❌ No |
| **View Logs** | ✅ Yes | ✅ Yes (read-only) |
| **Modify Risk Rules** | ✅ Yes | ❌ No |

### Windows UAC Integration

**Admin CLI Elevation:**
```python
# src/cli/admin/auth.py

import ctypes

def require_admin():
    """Exit if not running elevated."""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("❌ Error: Admin CLI requires administrator privileges")
        print("")
        print("To access Admin CLI:")
        print("  1. Right-click PowerShell or Terminal")
        print("  2. Select 'Run as Administrator'")
        print("  3. Windows will prompt for admin password")
        print("  4. Run 'risk-manager admin' again")
        sys.exit(1)
```

**Trader CLI (No Elevation):**
```python
# src/cli/trader/trader_main.py

def main():
    """Trader CLI - no elevation required."""
    # No admin check - anyone can view status
    display_status_screen()
```

**File Permissions (Windows ACL):**
```
C:/ProgramData/RiskManager/config/
  ├─ SYSTEM: Full Control
  ├─ Administrators: Full Control
  └─ Users: Read Only (trader can see files but cannot modify)

C:/ProgramData/RiskManager/data/
  ├─ SYSTEM: Full Control
  ├─ Administrators: Full Control
  └─ Users: No Access (trader cannot access database)

C:/ProgramData/RiskManager/logs/
  ├─ SYSTEM: Full Control
  ├─ Administrators: Full Control
  └─ Users: Read Only (trader can view logs)
```

**Result:** "Virtually Unkillable" Protection
- Trader cannot stop service
- Trader cannot edit configs
- Trader cannot access database
- Trader cannot bypass rules

---

## Startup Sequence Detail

### 1. Service Start (0-1 seconds)
```
Windows Service Manager
    ↓
Starts RiskManagerV34 service
    ↓
Calls SvcDoRun() in windows_service.py
    ↓
Launches async main loop
```

**Logging:**
```
[2025-10-25 08:00:00] Service starting...
```

### 2. Configuration Loading (1-2 seconds)
```
Load risk_config.yaml
    ↓
Load accounts.yaml
    ↓
Validate configurations
    ↓
Load holiday calendar
```

**Logging:**
```
[2025-10-25 08:00:01] Loading configuration...
[2025-10-25 08:00:01] Config loaded: 8 rules enabled
```

### 3. Database Initialization (2-3 seconds)
```
Open SQLite connection
    ↓
Create tables (if not exist)
    ↓
Load state from database
    ↓
Restore lockouts
    ↓
Load daily P&L
```

**Logging:**
```
[2025-10-25 08:00:02] Database initialized: C:/ProgramData/RiskManager/data/risk_state.db
[2025-10-25 08:00:02] Loaded 1 active lockout from database
```

### 4. SDK Connection (3-4 seconds)
```
Authenticate with API key
    ↓
Connect to WebSocket (SignalR)
    ↓
Subscribe to account events
    ↓
Wait for connection confirmation
```

**Logging:**
```
[2025-10-25 08:00:03] Connecting to Project-X SDK...
[2025-10-25 08:00:04] SDK connected: account_id=123
```

### 5. Rule Initialization (4-5 seconds)
```
Read enabled rules from config
    ↓
Instantiate rule objects
    ↓
Initialize modules (MOD-001, 002, 003, 004)
    ↓
Verify rule configurations
```

**Logging:**
```
[2025-10-25 08:00:04] Loading risk rules...
[2025-10-25 08:00:04] Rules loaded: MaxContracts, DailyRealizedLoss, TradeFrequencyLimit, ...
[2025-10-25 08:00:05] Modules initialized: MOD-001, MOD-002, MOD-003, MOD-004
```

### 6. Event Loop Start (5+ seconds)
```
Start background tasks
    ↓
Begin listening for SDK events
    ↓
System ready
```

**Logging:**
```
[2025-10-25 08:00:05] Event loop started
[2025-10-25 08:00:05] Risk Manager ready - monitoring account 123
```

**Total Startup Time:** 5 seconds (typical)

---

## Shutdown Sequence Detail

### Graceful Shutdown (Admin Initiated)
```
Admin: sc stop RiskManagerV34
    ↓
Windows calls SvcStop()
    ↓
Set stop event signal
    ↓
Async main loop detects signal
    ↓
Begin graceful shutdown
```

**Steps:**
1. **Stop Accepting Events**
   ```python
   await sdk.unsubscribe_from_events()
   ```

2. **Flush Database Writes**
   ```python
   await db.flush_all()
   await db.close()
   ```

3. **Save Current State**
   ```python
   await persistence.save_lockout_state()
   await persistence.save_pnl_state()
   ```

4. **Close SDK Connection**
   ```python
   await sdk.disconnect()
   ```

5. **Stop Background Tasks**
   ```python
   await scheduler.stop()
   await timer_manager.stop_all()
   ```

6. **Report Service Stopped**
   ```python
   servicemanager.LogMsg("Service stopped successfully")
   ```

**Logging:**
```
[2025-10-25 17:00:00] Stop signal received
[2025-10-25 17:00:00] Flushing database writes...
[2025-10-25 17:00:00] Closing SDK connection...
[2025-10-25 17:00:01] Risk Manager stopped
```

**Shutdown Time:** < 2 seconds (typical)

---

## Background Tasks

### Task 1: Check Expired Lockouts (Every 1 Second)
```python
async def background_task_lockouts():
    """Check and clear expired lockouts every second."""
    while daemon_running:
        lockout_manager.check_expired_lockouts()
        await asyncio.sleep(1)
```

**Purpose:** Auto-clear lockouts when time expires

### Task 2: Check Reset Time (Every 1 Minute)
```python
async def background_task_reset():
    """Check if daily reset time reached every minute."""
    while daemon_running:
        reset_scheduler.check_reset_time()
        await asyncio.sleep(60)
```

**Purpose:** Trigger daily reset at midnight ET

### Task 3: Check Timers (Every 1 Second)
```python
async def background_task_timers():
    """Check countdown timers and fire callbacks."""
    while daemon_running:
        timer_manager.check_timers()
        await asyncio.sleep(1)
```

**Purpose:** Execute timer callbacks (cooldown expiry, etc.)

---

## State Persistence

### What Persists (Survives Crashes)
- ✅ Active lockouts (hard lockouts and cooldowns)
- ✅ Daily P&L (realized and unrealized)
- ✅ Trade frequency counts
- ✅ Last reset timestamp
- ✅ Enforcement history (last 1000 actions)

### What Doesn't Persist (Recreated on Startup)
- ❌ WebSocket connection (reconnects)
- ❌ SDK session (re-authenticates)
- ❌ In-memory timers (recalculated from lockout expiry)
- ❌ Event queue (fresh start)

### Persistence Timing
- **On State Change:** Immediate write to SQLite
- **On Shutdown:** Flush all pending writes
- **On Crash:** Last committed state recovered

---

## Error Handling

### Service Crash (Unexpected)
```
Exception occurs in daemon
    ↓
Service exits with non-zero code
    ↓
Windows Service Manager detects failure
    ↓
Wait 1 minute (recovery policy)
    ↓
Auto-restart service
    ↓
Load state from SQLite
    ↓
Resume monitoring
```

**Logging:**
```
[2025-10-25 14:30:15] FATAL ERROR: Unhandled exception
[2025-10-25 14:30:15] Exception: ConnectionError: SDK connection lost
[2025-10-25 14:31:15] Service restarting (recovery policy)
[2025-10-25 14:31:20] Service started successfully
```

### SDK Connection Loss
```
WebSocket disconnects
    ↓
SDK auto-reconnection (handled by SDK)
    ↓
Daemon waits for reconnection
    ↓
Resume event processing
```

**Logging:**
```
[2025-10-25 14:45:00] WARNING: SDK connection lost
[2025-10-25 14:45:01] SDK reconnecting...
[2025-10-25 14:45:05] SDK reconnected successfully
```

### Database Corruption
```
SQLite error on write
    ↓
Attempt recovery from backup
    ↓
If recovery fails, start fresh
    ↓
Log error to Windows Event Log
```

**Logging:**
```
[2025-10-25 15:00:00] ERROR: Database write failed
[2025-10-25 15:00:01] Attempting recovery from backup...
[2025-10-25 15:00:02] Recovery successful - state restored
```

---

## Logging Strategy

### Log Locations

**1. Daemon Log** (Main operational log)
- **File:** `C:/ProgramData/RiskManager/logs/daemon.log`
- **Content:** Startup, shutdown, state changes, background tasks
- **Rotation:** Daily, keep 30 days
- **Access:** Admin (read/write), Trader (read-only)

**2. Enforcement Log** (Rule enforcement actions)
- **File:** `C:/ProgramData/RiskManager/logs/enforcement.log`
- **Content:** Position closes, lockouts, rule violations
- **Rotation:** Daily, keep 90 days
- **Access:** Admin (read/write), Trader (read-only)

**3. API Log** (SDK interactions)
- **File:** `C:/ProgramData/RiskManager/logs/api.log`
- **Content:** SDK calls, WebSocket events, authentication
- **Rotation:** Daily, keep 7 days
- **Access:** Admin only

**4. Error Log** (Errors only)
- **File:** `C:/ProgramData/RiskManager/logs/error.log`
- **Content:** Exceptions, failures, warnings
- **Rotation:** Daily, keep 90 days
- **Access:** Admin only

**5. Windows Event Log**
- **Source:** Risk Manager V34
- **Content:** Service start/stop, critical errors
- **Access:** Admin via Event Viewer (`eventvwr.msc`)

### Log Levels
- **DEBUG:** Development only (verbose)
- **INFO:** Normal operations (startup, shutdown, state changes)
- **WARNING:** Unexpected but recoverable (connection loss, retry)
- **ERROR:** Errors requiring attention (config errors, API failures)
- **CRITICAL:** Fatal errors causing service failure

---

## Production Deployment Checklist

### Pre-Deployment
- [ ] Windows Service wrapper implemented
- [ ] Service installer tested
- [ ] Service recovery policy configured
- [ ] Windows ACL permissions set correctly
- [ ] Admin CLI elevation check working
- [ ] Crash recovery tested
- [ ] State persistence tested

### Installation
- [ ] Install service as administrator
- [ ] Configure API credentials
- [ ] Configure risk rules
- [ ] Set file ACL permissions
- [ ] Start service
- [ ] Verify service running
- [ ] Test Trader CLI (view-only)

### Post-Deployment Validation
- [ ] Service auto-starts on reboot
- [ ] Trader cannot stop service
- [ ] Trader cannot edit configs
- [ ] Admin can stop/start service
- [ ] Admin can modify configs
- [ ] Crash recovery works (test by killing process)
- [ ] Daily reset triggers at midnight
- [ ] Lockouts persist across restarts

---

## Related Documentation

- `system-architecture.md` - Complete system architecture
- `MOD-002-lockout-manager.md` - Lockout system details
- `/docs/analysis/wave2-gap-analysis/05-DEPLOYMENT-GAPS.md` - Windows Service implementation gaps
- `/docs/current/SECURITY_MODEL.md` - Windows UAC security details

---

**This specification defines how the Risk Manager daemon operates in production.**
