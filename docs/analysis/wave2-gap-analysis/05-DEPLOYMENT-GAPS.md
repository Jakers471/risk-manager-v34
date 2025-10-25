# Wave 2 Gap Analysis: Windows Service & Deployment

**Researcher:** RESEARCHER 5 - Windows Service & Deployment Gap Analyst
**Date:** 2025-10-25
**Project:** Risk Manager V34
**Focus:** Windows Service wrapper, deployment system, and scheduled tasks

---

## Executive Summary

Risk Manager V34 currently **lacks the entire Windows Service deployment layer**, despite having comprehensive security specifications. The system cannot run as a production Windows Service, cannot auto-start on boot, and has no deployment infrastructure.

**Critical Finding:** 0% implemented - no Windows Service code exists in codebase

**Key Insights:**
- Complete specifications exist in archived docs (security model, MOD-004 reset scheduler)
- `pyproject.toml` missing `pywin32` dependency (critical blocker)
- No `src/risk_manager/service/` directory exists
- No installation/deployment scripts exist
- Current system can only run as standalone Python process
- Cannot survive reboot, cannot be "unkillable" as designed

**Total Components:** 5 (Wrapper, Installer, Control, Scheduled Tasks, Protection)
- **Implemented:** 0 (0%)
- **Missing:** 5 (100%)
- **Estimated Total Effort:** 2-3 weeks

---

## Table of Contents

1. [Implementation Status Matrix](#implementation-status-matrix)
2. [Current State](#current-state)
3. [Detailed Gap Analysis](#detailed-gap-analysis)
4. [Critical Path Analysis](#critical-path-analysis)
5. [Recommended Implementation Order](#recommended-implementation-order)
6. [Technical Challenges](#technical-challenges)
7. [Deployment Checklist](#deployment-checklist)
8. [Blockers Analysis](#blockers-analysis)
9. [Testing Strategy](#testing-strategy)

---

## Implementation Status Matrix

| Component | Status | Priority | Effort | Blocks | Dependencies |
|-----------|--------|----------|--------|--------|--------------|
| **Service Wrapper** | ❌ Missing | Critical | 1 week | Everything | pywin32, RiskManager core |
| **Service Installer** | ❌ Missing | Critical | 3 days | Deployment | Service Wrapper |
| **Service Control** | ❌ Missing | High | 2 days | Admin CLI | Service Wrapper, Admin CLI |
| **Scheduled Tasks** | ❌ Missing | High | 4 days | MOD-004 reset | Service Wrapper, Reset Manager |
| **Process Protection** | ❌ Missing | Medium | 3 days | Security | Service Wrapper, ACL setup |

**Critical Blocker:** Service Wrapper must be implemented first - all other components depend on it

---

## Current State

### What Exists

**Specifications (Complete):**
- ✅ `/docs/analysis/wave1-feature-inventory/05-SECURITY-CONFIG-INVENTORY.md` (1,853 lines)
  - Windows UAC security model
  - Service protection layers
  - Admin CLI elevation checks
  - File ACL permissions
- ✅ `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/reset_scheduler.md` (MOD-004)
  - Daily reset at midnight ET
  - Holiday calendar integration
  - Scheduled task requirements

**Core Infrastructure (Exists):**
- ✅ `src/risk_manager/core/manager.py` - Risk Manager main class (async)
- ✅ `src/risk_manager/core/engine.py` - Event processing loop
- ✅ `src/risk_manager/state/database.py` - SQLite persistence
- ✅ `src/risk_manager/state/pnl_tracker.py` - P&L tracking
- ✅ Admin CLI elevation check logic (documented, not implemented)

### What's Missing (100%)

**Implementation (None Exists):**
- ❌ No `src/risk_manager/service/` directory
- ❌ No Windows Service wrapper code
- ❌ No `pywin32` dependency in `pyproject.toml`
- ❌ No installation scripts (`scripts/install_service.py`)
- ❌ No service control CLI (`src/cli/admin/service.py`)
- ❌ No scheduled task integration
- ❌ No Windows ACL setup script
- ❌ No service recovery configuration

**Dependencies (Missing):**
```toml
# NOT in pyproject.toml:
pywin32 = ">=306"        # Windows service framework
pythoncom = ">=306"      # COM initialization
pywin32-ctypes = ">=0.2" # Windows API access
APScheduler = ">=3.10"   # Async job scheduling (for scheduled tasks)
```

**Result:** Cannot deploy as Windows Service - only runs as standalone Python script with no persistence across reboots.

---

## Detailed Gap Analysis

### Component 1: Windows Service Wrapper

**Current Status:** ❌ Missing (0% implemented)

**What it should do:**
- Wrap Risk Manager as Windows Service using `win32serviceutil`
- Handle service lifecycle (start, stop, pause, resume)
- Run as LocalSystem account (highest Windows privilege)
- Report service status to Windows Service Control Manager
- Handle graceful shutdown (close SDK connections, flush database)
- Integrate async event loop with synchronous Windows Service API

**Current Implementation:** None - directory doesn't exist

**Missing Files:**
```
src/risk_manager/service/
├── __init__.py
├── windows_service.py       # Main service class
├── service_manager.py       # Lifecycle management
└── async_integration.py     # Async/sync bridge
```

**Required Implementation:**

**`src/risk_manager/service/windows_service.py`:**
```python
"""
Windows Service Wrapper for Risk Manager V34

Wraps the async Risk Manager in a Windows Service context.
Handles synchronous Windows Service API → async Risk Manager bridge.
"""

import asyncio
import sys
import win32serviceutil
import win32service
import win32event
import servicemanager
import logging

from risk_manager.core.manager import RiskManager
from risk_manager.core.config import RiskConfig


class RiskManagerService(win32serviceutil.ServiceFramework):
    """
    Windows Service wrapper for Risk Manager V34.

    Service Properties:
    - Name: RiskManagerV34
    - Display Name: Risk Manager V34
    - Description: Trading risk management protection service
    - Account: LocalSystem (highest privilege)
    - Startup: Automatic (starts on boot)
    """

    _svc_name_ = "RiskManagerV34"
    _svc_display_name_ = "Risk Manager V34"
    _svc_description_ = "Trading risk management protection service for TopstepX accounts"

    def __init__(self, args):
        """Initialize service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """Setup logging to Windows Event Log."""
        logger = logging.getLogger('RiskManagerService')
        logger.setLevel(logging.INFO)
        # Log to Windows Event Log
        handler = logging.handlers.NTEventLogHandler('Risk Manager V34')
        logger.addHandler(handler)
        return logger

    def SvcStop(self):
        """Stop service - called by Windows."""
        self.logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        """
        Service main entry point - called by Windows on service start.

        This method bridges the synchronous Windows Service API
        to our async Risk Manager.
        """
        self.logger.info("Service starting...")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )

        try:
            # Run async main in service context
            asyncio.run(self.async_main())
        except Exception as e:
            self.logger.error(f"Service error: {e}", exc_info=True)
            servicemanager.LogErrorMsg(f"Service failed: {e}")

    async def async_main(self):
        """
        Async main loop for Risk Manager.

        Handles:
        - Loading configuration
        - Initializing Risk Manager
        - Running event loop
        - Graceful shutdown on stop signal
        """
        try:
            # Load configuration
            config = RiskConfig.from_file("C:/ProgramData/RiskManager/config/risk_config.yaml")

            # Create Risk Manager
            manager = await RiskManager.create(config)

            # Start Risk Manager (non-blocking)
            await manager.start()

            # Wait for stop signal
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
            )

            # Graceful shutdown
            self.logger.info("Shutting down Risk Manager...")
            await manager.stop()

        except Exception as e:
            self.logger.error(f"Async main error: {e}", exc_info=True)
            raise


if __name__ == '__main__':
    """
    Command-line interface for service control.

    Usage:
        python windows_service.py install    # Install service
        python windows_service.py start      # Start service
        python windows_service.py stop       # Stop service
        python windows_service.py remove     # Uninstall service
    """
    if len(sys.argv) == 1:
        # No arguments - try to start service (called by Windows)
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RiskManagerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Command-line arguments - install/remove/etc.
        win32serviceutil.HandleCommandLine(RiskManagerService)
```

**Dependencies:**
- `pywin32` (Windows service API)
- `RiskManager` core (must be async-compatible)
- Configuration system (must load from fixed path)

**Estimated Effort:** 1 week
- Day 1-2: Basic service wrapper skeleton
- Day 3-4: Async/sync bridge integration
- Day 5: Graceful shutdown handling
- Day 6-7: Testing and debugging

**Key Challenges:**
1. **Async/Sync Bridge:** Windows Service API is synchronous, Risk Manager is async
   - Solution: Use `asyncio.run()` in `SvcDoRun()`
   - Challenge: Handling stop signal from Windows → async shutdown
2. **Service Context:** Service runs as LocalSystem, different environment
   - Solution: Use absolute paths (`C:/ProgramData/RiskManager/`)
   - Challenge: Debugging without console access
3. **Error Reporting:** No console output in service context
   - Solution: Windows Event Log integration
   - Challenge: Setting up proper logging handlers

---

### Component 2: Service Installer

**Current Status:** ❌ Missing (0% implemented)

**What it should do:**
- Install Windows Service (requires admin)
- Configure service properties (auto-start, recovery, description)
- Set service account to LocalSystem
- Create required directories with correct ACL permissions
- Uninstall service (requires admin)
- Handle installation errors gracefully

**Current Implementation:** None

**Missing Files:**
```
scripts/
├── install_service.py       # Installation script
├── uninstall_service.py     # Uninstallation script
└── setup_permissions.py     # ACL configuration
```

**Required Implementation:**

**`scripts/install_service.py`:**
```python
"""
Windows Service Installation Script

MUST be run as Administrator (elevated PowerShell).
Sets up:
- Windows Service registration
- Directory structure with ACL permissions
- Service recovery policy
"""

import sys
import os
import win32security
import ntsecuritycon as con
import win32serviceutil
from pathlib import Path


def check_admin():
    """Verify running as administrator."""
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("❌ ERROR: This script must be run as Administrator")
        print("")
        print("Please:")
        print("  1. Right-click PowerShell")
        print("  2. Select 'Run as Administrator'")
        print("  3. Run this script again")
        sys.exit(1)


def create_directories():
    """Create required directory structure."""
    base_dir = Path("C:/ProgramData/RiskManager")

    directories = [
        base_dir / "config",
        base_dir / "data",
        base_dir / "logs",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")


def set_acl_permissions(directory_path: str):
    """
    Set Windows ACL permissions.

    Permissions:
    - SYSTEM account: Full Control
    - Administrators group: Full Control
    - Users group: Read Only
    """
    # Get security descriptor
    sd = win32security.GetFileSecurity(
        directory_path,
        win32security.DACL_SECURITY_INFORMATION
    )

    # Create new DACL
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

    # Apply DACL
    sd.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(
        directory_path,
        win32security.DACL_SECURITY_INFORMATION,
        sd
    )

    print(f"✅ Set ACL permissions: {directory_path}")


def install_service():
    """Install Windows Service."""
    # Import service class
    from risk_manager.service.windows_service import RiskManagerService

    # Install service
    win32serviceutil.InstallService(
        pythonClassString=RiskManagerService.__module__ + '.' + RiskManagerService.__name__,
        serviceName=RiskManagerService._svc_name_,
        displayName=RiskManagerService._svc_display_name_,
        description=RiskManagerService._svc_description_,
        startType=win32service.SERVICE_AUTO_START,  # Auto-start on boot
    )

    print(f"✅ Installed service: {RiskManagerService._svc_display_name_}")


def configure_recovery():
    """Configure service recovery policy (auto-restart on crash)."""
    # TODO: Set service recovery options
    # - Restart on failure (1st, 2nd, subsequent)
    # - Reset failure count after 1 day
    # - Run recovery action after 1 minute
    print("✅ Configured service recovery policy")


def main():
    """Main installation workflow."""
    print("=" * 60)
    print("Risk Manager V34 - Service Installation")
    print("=" * 60)
    print("")

    # Step 1: Check admin
    check_admin()

    # Step 2: Create directories
    print("Creating directories...")
    create_directories()
    print("")

    # Step 3: Set ACL permissions
    print("Setting ACL permissions...")
    for directory in ["config", "data", "logs"]:
        set_acl_permissions(f"C:/ProgramData/RiskManager/{directory}")
    print("")

    # Step 4: Install service
    print("Installing Windows Service...")
    install_service()
    print("")

    # Step 5: Configure recovery
    print("Configuring recovery policy...")
    configure_recovery()
    print("")

    print("=" * 60)
    print("✅ Installation Complete!")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("  1. Configure risk rules: C:/ProgramData/RiskManager/config/risk_config.yaml")
    print("  2. Start service: sc start RiskManagerV34")
    print("  3. Check status: sc query RiskManagerV34")
    print("")


if __name__ == "__main__":
    main()
```

**Dependencies:**
- Service Wrapper (must exist first)
- `pywin32` (Windows API)
- Admin privileges (UAC check)

**Estimated Effort:** 3 days
- Day 1: Directory creation + ACL permissions
- Day 2: Service registration + configuration
- Day 3: Recovery policy + error handling

**Key Challenges:**
1. **ACL Complexity:** Windows ACL API is complex
   - Solution: Use well-known SIDs for SYSTEM/Admins/Users
   - Challenge: Testing permissions correctly
2. **Service Registration:** Multiple service properties to configure
   - Solution: Use `win32serviceutil` helper functions
   - Challenge: Ensuring service starts correctly on first boot
3. **Error Handling:** Installation can fail in many ways
   - Solution: Comprehensive try/except with clear error messages
   - Challenge: Rolling back partial installations

---

### Component 3: Service Control (CLI Integration)

**Current Status:** ❌ Missing (0% implemented)

**What it should do:**
- Admin CLI `service` command to control Windows Service
- Start/stop/restart service via CLI
- Query service status (running/stopped/error)
- View service logs from CLI
- Graceful shutdown handling

**Current Implementation:** None

**Missing Files:**
```
src/cli/admin/
├── service.py               # Service control commands
└── auth.py                  # Admin elevation check (documented, not implemented)
```

**Required Implementation:**

**`src/cli/admin/service.py`:**
```python
"""
Admin CLI - Service Control

Requires Windows administrator privileges (UAC elevation).
"""

import win32service
import win32serviceutil
from rich.console import Console
from rich.table import Table


console = Console()


def get_service_status():
    """Get current service status."""
    try:
        status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
        state = status[1]

        state_map = {
            win32service.SERVICE_STOPPED: ("Stopped", "red"),
            win32service.SERVICE_START_PENDING: ("Starting...", "yellow"),
            win32service.SERVICE_STOP_PENDING: ("Stopping...", "yellow"),
            win32service.SERVICE_RUNNING: ("Running", "green"),
            win32service.SERVICE_CONTINUE_PENDING: ("Resuming...", "yellow"),
            win32service.SERVICE_PAUSE_PENDING: ("Pausing...", "yellow"),
            win32service.SERVICE_PAUSED: ("Paused", "yellow"),
        }

        return state_map.get(state, ("Unknown", "red"))

    except Exception as e:
        return (f"Error: {e}", "red")


def service_start():
    """Start Windows Service."""
    console.print("[yellow]Starting Risk Manager service...[/yellow]")

    try:
        win32serviceutil.StartService("RiskManagerV34")
        console.print("✅ [green]Service started successfully[/green]")
    except Exception as e:
        console.print(f"❌ [red]Failed to start service: {e}[/red]")


def service_stop():
    """Stop Windows Service."""
    console.print("[yellow]Stopping Risk Manager service...[/yellow]")

    try:
        win32serviceutil.StopService("RiskManagerV34")
        console.print("✅ [green]Service stopped successfully[/green]")
    except Exception as e:
        console.print(f"❌ [red]Failed to stop service: {e}[/red]")


def service_restart():
    """Restart Windows Service."""
    console.print("[yellow]Restarting Risk Manager service...[/yellow]")

    try:
        win32serviceutil.RestartService("RiskManagerV34")
        console.print("✅ [green]Service restarted successfully[/green]")
    except Exception as e:
        console.print(f"❌ [red]Failed to restart service: {e}[/red]")


def service_status():
    """Display service status."""
    status, color = get_service_status()

    table = Table(title="Risk Manager Service Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style=color)

    table.add_row("Service Name", "RiskManagerV34")
    table.add_row("Display Name", "Risk Manager V34")
    table.add_row("Status", status)

    console.print(table)
```

**Admin CLI Integration:**
```python
# src/cli/admin/admin_main.py

from cli.admin.auth import require_admin
from cli.admin.service import (
    service_start, service_stop, service_restart, service_status
)

def display_admin_menu():
    """Admin CLI main menu."""

    # Check elevation FIRST
    require_admin()

    while True:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║         RISK MANAGER V34 - ADMIN CONSOLE                     ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print("\nService Control:")
        print("  [1] Start Service")
        print("  [2] Stop Service")
        print("  [3] Restart Service")
        print("  [4] Service Status")
        print("\nConfiguration:")
        print("  [5] Edit Risk Rules")
        print("  [6] View Configuration")
        print("\nAccount Management:")
        print("  [7] Manual Unlock (Emergency Override)")
        print("  [8] View Lockout Status")
        print("\n  [Q] Quit")
        print("")

        choice = input("Select: ").strip()

        if choice == "1":
            service_start()
        elif choice == "2":
            service_stop()
        elif choice == "3":
            service_restart()
        elif choice == "4":
            service_status()
        # ... other menu options
        elif choice.upper() == "Q":
            break
```

**Dependencies:**
- Service Wrapper (must be installed)
- Admin CLI framework (needs implementation)
- `pywin32` (service control API)

**Estimated Effort:** 2 days
- Day 1: Service control commands
- Day 2: Admin CLI integration

**Key Challenges:**
1. **Service State Management:** Service can be in multiple states
   - Solution: Use `win32service` state constants
   - Challenge: Handling state transitions gracefully
2. **Error Messages:** Clear errors when service control fails
   - Solution: Catch specific exceptions, provide helpful messages
   - Challenge: Distinguishing permission errors from other failures

---

### Component 4: Scheduled Tasks Integration

**Current Status:** ❌ Missing (0% implemented)

**What it should do:**
- Daily reset at midnight ET (MOD-004 requirement)
- Periodic health checks (every 5 minutes)
- Log rotation (daily)
- Database cleanup (weekly)
- Holiday calendar integration

**Current Implementation:** None

**Missing Files:**
```
src/risk_manager/tasks/
├── __init__.py
├── scheduler.py             # Main scheduler
├── daily_reset.py           # Daily P&L reset (MOD-004)
├── health_checks.py         # Periodic health monitoring
└── maintenance.py           # Log rotation, cleanup
```

**Required Implementation:**

**`src/risk_manager/tasks/scheduler.py`:**
```python
"""
Scheduled Tasks for Risk Manager

Runs within Windows Service context.
Uses APScheduler for async task scheduling.
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import time
import pytz

from risk_manager.tasks.daily_reset import reset_daily_counters
from risk_manager.tasks.health_checks import run_health_check
from risk_manager.tasks.maintenance import rotate_logs, cleanup_database


class TaskScheduler:
    """
    Manages scheduled tasks for Risk Manager.

    Tasks:
    - Daily reset at midnight ET (MOD-004)
    - Health checks every 5 minutes
    - Log rotation daily at 2 AM
    - Database cleanup weekly on Sunday at 3 AM
    """

    def __init__(self, account_id: str):
        self.account_id = account_id
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('America/New_York'))

    def schedule_all_tasks(self):
        """Schedule all recurring tasks."""

        # Task 1: Daily Reset at Midnight ET (MOD-004)
        self.scheduler.add_job(
            func=reset_daily_counters,
            args=[self.account_id],
            trigger=CronTrigger(hour=0, minute=0, timezone='America/New_York'),
            id='daily_reset',
            name='Daily P&L Reset',
            replace_existing=True
        )

        # Task 2: Health Check every 5 minutes
        self.scheduler.add_job(
            func=run_health_check,
            args=[self.account_id],
            trigger='interval',
            minutes=5,
            id='health_check',
            name='System Health Check'
        )

        # Task 3: Log Rotation daily at 2 AM
        self.scheduler.add_job(
            func=rotate_logs,
            trigger=CronTrigger(hour=2, minute=0, timezone='America/New_York'),
            id='log_rotation',
            name='Log Rotation'
        )

        # Task 4: Database Cleanup weekly on Sunday at 3 AM
        self.scheduler.add_job(
            func=cleanup_database,
            trigger=CronTrigger(day_of_week='sun', hour=3, minute=0, timezone='America/New_York'),
            id='db_cleanup',
            name='Database Cleanup'
        )

    def start(self):
        """Start scheduler (non-blocking)."""
        self.scheduler.start()

    def stop(self):
        """Stop scheduler gracefully."""
        self.scheduler.shutdown(wait=True)
```

**`src/risk_manager/tasks/daily_reset.py`:**
```python
"""
Daily Reset Task (MOD-004 Implementation)

Resets daily P&L counters at midnight ET.
"""

import asyncio
from datetime import datetime
from loguru import logger
from risk_manager.state.pnl_tracker import PnLTracker
from risk_manager.state.database import Database


async def reset_daily_counters(account_id: str):
    """
    Reset daily P&L counters (MOD-004).

    Actions:
    - Reset daily realized P&L to 0
    - Clear daily lockouts (hard lockouts remain)
    - Reset trade frequency counters
    - Log reset event
    """
    try:
        logger.info(f"🔄 Daily reset starting for account {account_id}")

        # Reset P&L
        db = Database("C:/ProgramData/RiskManager/data/risk_state.db")
        tracker = PnLTracker(db)
        tracker.reset_daily_pnl(account_id)

        # Clear daily lockouts (preserve permanent lockouts)
        # TODO: Integrate with LockoutManager

        logger.info(f"✅ Daily reset complete for account {account_id} at {datetime.now()}")

    except Exception as e:
        logger.error(f"❌ Daily reset failed: {e}", exc_info=True)
```

**Integration with Windows Service:**
```python
# src/risk_manager/service/windows_service.py

from risk_manager.tasks.scheduler import TaskScheduler

async def async_main(self):
    """Async main loop with scheduled tasks."""
    try:
        # Load configuration
        config = RiskConfig.from_file("C:/ProgramData/RiskManager/config/risk_config.yaml")

        # Create Risk Manager
        manager = await RiskManager.create(config)

        # Start Risk Manager
        await manager.start()

        # Start Task Scheduler ⭐ NEW
        scheduler = TaskScheduler(config.account_id)
        scheduler.schedule_all_tasks()
        scheduler.start()

        # Wait for stop signal
        # ...

        # Graceful shutdown
        scheduler.stop()  # Stop scheduler
        await manager.stop()

    except Exception as e:
        logger.error(f"Async main error: {e}", exc_info=True)
        raise
```

**Dependencies:**
- Service Wrapper (runs in service context)
- MOD-004 Reset Manager (reset logic)
- PnLTracker (state management)
- `APScheduler` (job scheduling library)

**Estimated Effort:** 4 days
- Day 1: Scheduler integration with async
- Day 2: Daily reset implementation (MOD-004)
- Day 3: Health checks + maintenance tasks
- Day 4: Holiday calendar integration + testing

**Key Challenges:**
1. **Timezone Handling:** Midnight ET != midnight server time
   - Solution: Use `pytz.timezone('America/New_York')`
   - Challenge: Daylight Saving Time transitions
2. **Task Reliability:** Tasks must run even if service restarts
   - Solution: Persistent task scheduling (check last run time on startup)
   - Challenge: Avoiding duplicate resets
3. **Async Integration:** APScheduler async mode with Risk Manager
   - Solution: Use `AsyncIOScheduler`
   - Challenge: Coordinating async tasks with service lifecycle

---

### Component 5: Process Protection

**Current Status:** ❌ Missing (0% implemented)

**What it should do:**
- Prevent trader from killing service process
- Protect config files with Windows ACL
- Auto-restart service on crash
- Admin-only service control
- Audit trail of all admin actions

**Current Implementation:** None (specifications exist)

**Missing Features:**
- Windows ACL on config/data/logs directories
- Service recovery policy (auto-restart)
- UAC integration for Admin CLI
- Process protection verification

**Required Implementation:**

**Windows ACL Protection (Implemented in Installer):**
```python
# scripts/install_service.py (already shown in Component 2)

def set_acl_permissions(directory_path: str):
    """
    Set Windows ACL:
    - SYSTEM: Full Control
    - Administrators: Full Control
    - Users: Read Only
    """
    # See Component 2 for full implementation
```

**Service Recovery Policy:**
```python
# scripts/install_service.py

def configure_recovery():
    """
    Configure service recovery policy.

    Recovery Actions:
    - First failure: Restart service after 1 minute
    - Second failure: Restart service after 1 minute
    - Subsequent failures: Restart service after 1 minute
    - Reset failure count after: 1 day
    """
    import win32service
    import win32con

    # Open service
    hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
    hs = win32service.OpenService(hscm, "RiskManagerV34", win32service.SERVICE_ALL_ACCESS)

    # Configure recovery actions
    service_failure_actions = {
        'ResetPeriod': 86400,  # 1 day in seconds
        'RebootMsg': None,
        'Command': None,
        'Actions': [
            (win32service.SC_ACTION_RESTART, 60000),  # Restart after 1 minute
            (win32service.SC_ACTION_RESTART, 60000),
            (win32service.SC_ACTION_RESTART, 60000),
        ]
    }

    win32service.ChangeServiceConfig2(
        hs,
        win32service.SERVICE_CONFIG_FAILURE_ACTIONS,
        service_failure_actions
    )

    win32service.CloseServiceHandle(hs)
    win32service.CloseServiceHandle(hscm)
```

**Admin CLI Elevation Check:**
```python
# src/cli/admin/auth.py (from specifications)

import ctypes
import sys

def is_admin() -> bool:
    """Check if running with Windows administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def require_admin():
    """Exit if not running elevated."""
    if not is_admin():
        print("❌ Error: Admin CLI requires administrator privileges")
        print("")
        print("To access Admin CLI:")
        print("  1. Right-click PowerShell or Terminal")
        print("  2. Select 'Run as Administrator'")
        print("  3. Windows will prompt for admin password")
        print("  4. Run 'risk-manager admin' again")
        sys.exit(1)
```

**Process Protection Verification:**
```python
# src/cli/admin/verify_protection.py

def verify_protection():
    """
    Verify all protection layers are active.

    Checks:
    1. Service running as LocalSystem
    2. Config files have correct ACL
    3. Service recovery policy configured
    4. Service cannot be stopped by normal user
    """
    import win32security
    import win32service

    checks = []

    # Check 1: Service account
    # TODO: Query service account (should be LocalSystem)

    # Check 2: File permissions
    # TODO: Read ACL on C:/ProgramData/RiskManager/config

    # Check 3: Recovery policy
    # TODO: Query service recovery settings

    # Display results
    for check in checks:
        print(f"{'✅' if check['pass'] else '❌'} {check['name']}")
```

**Dependencies:**
- Service Wrapper (must be installed)
- Service Installer (sets ACL permissions)
- `pywin32` (Windows API)

**Estimated Effort:** 3 days
- Day 1: ACL permissions setup (in installer)
- Day 2: Service recovery policy configuration
- Day 3: Protection verification + testing

**Key Challenges:**
1. **ACL Verification:** Checking if permissions are correct
   - Solution: Read DACL and compare to expected SIDs
   - Challenge: Handling inherited permissions
2. **Service Recovery:** Ensuring service actually restarts
   - Solution: Test by killing service process
   - Challenge: Testing without disrupting development
3. **UAC Testing:** Testing elevation checks
   - Solution: Run tests as both admin and normal user
   - Challenge: Automating UAC tests

---

## Critical Path Analysis

### Dependencies Graph

```
📦 pywin32 Dependency (0.5 days) ← CRITICAL BLOCKER
      ↓
🔧 Service Wrapper (1 week) ← CRITICAL BLOCKER
      ↓
      ├─→ 📥 Service Installer (3 days)
      │         ↓
      │         └─→ 🛡️ Process Protection (3 days)
      │
      ├─→ 🎛️ Service Control CLI (2 days)
      │         ↓
      │         └─→ (Requires Admin CLI framework - separate component)
      │
      └─→ ⏰ Scheduled Tasks (4 days)
                ↓
                └─→ (Requires MOD-004 Reset Manager - separate component)
```

### Total Time Estimates

**Sequential (All Done in Order):**
- Week 1: pywin32 + Service Wrapper
- Week 2: Service Installer + Protection
- Week 3: Service Control + Scheduled Tasks
**Total: 3 weeks**

**Parallel (After Service Wrapper Complete):**
- Week 1: pywin32 + Service Wrapper (blocker)
- Week 2: Installer + Control + Tasks + Protection (parallel)
**Total: 2 weeks**

### Critical Blockers

**1. pywin32 Dependency (0.5 days) - HIGHEST PRIORITY**
- Add to `pyproject.toml`
- Install in development environment
- Verify import works
- **Blocks:** Everything else

**2. Service Wrapper (1 week) - CRITICAL**
- Required for all other components
- **Blocks:** Installer, Control, Tasks, Protection

**3. MOD-004 Reset Manager (External Dependency)**
- Scheduled Tasks component needs this
- Must be implemented separately
- **Status:** Not analyzed yet (separate component)

---

## Recommended Implementation Order

### Phase 1: Core Service (Week 1)

**Goal:** Get basic Windows Service running

**Tasks:**
1. **Add pywin32 to dependencies** (0.5 days)
   ```bash
   # pyproject.toml
   dependencies = [
       # ... existing
       "pywin32>=306",
       "pythoncom>=306",
       "APScheduler>=3.10.0",
   ]

   # Install
   uv add pywin32 pythoncom APScheduler
   ```

2. **Create Service Wrapper Skeleton** (3 days)
   - Create `src/risk_manager/service/` directory
   - Implement `windows_service.py` with basic `ServiceFramework`
   - Implement `SvcDoRun()` with async/sync bridge
   - Test service installs and starts
   - **Milestone:** Service can be installed and started

3. **Integrate with Risk Manager** (3 days)
   - Load configuration from fixed path
   - Initialize `RiskManager` in service context
   - Handle graceful shutdown
   - Log to Windows Event Log
   - **Milestone:** Service runs Risk Manager successfully

4. **Testing** (1 day)
   - Install service in test environment
   - Start/stop service
   - Verify logs in Event Viewer
   - Test crash recovery
   - **Milestone:** Service stable and restartable

### Phase 2: Deployment Infrastructure (Week 2)

**Goal:** Enable installation and protection

**Tasks:**
1. **Service Installer** (3 days)
   - Create `scripts/install_service.py`
   - Directory creation
   - ACL permissions setup
   - Service registration
   - **Milestone:** One-click installation

2. **Process Protection** (3 days)
   - Service recovery policy
   - ACL verification
   - Admin CLI elevation check
   - Protection testing
   - **Milestone:** Service "unkillable" by trader

3. **Service Control CLI** (2 days)
   - Create `src/cli/admin/service.py`
   - Start/stop/restart commands
   - Status display
   - Integration with Admin CLI
   - **Milestone:** Admin can control service from CLI

### Phase 3: Scheduled Tasks (Week 3)

**Goal:** Enable daily reset and maintenance

**Tasks:**
1. **Task Scheduler Framework** (2 days)
   - Create `src/risk_manager/tasks/` directory
   - Implement `scheduler.py` with APScheduler
   - Integration with service lifecycle
   - **Milestone:** Scheduler runs in service

2. **Daily Reset (MOD-004)** (2 days)
   - Implement `daily_reset.py`
   - P&L reset logic
   - Lockout clearing
   - Holiday calendar integration
   - **Milestone:** Daily reset at midnight ET works

3. **Maintenance Tasks** (2 days)
   - Health checks every 5 minutes
   - Log rotation daily
   - Database cleanup weekly
   - **Milestone:** All scheduled tasks working

4. **End-to-End Testing** (1 day)
   - Install → Start → Stop → Uninstall
   - Auto-start on boot
   - Crash recovery
   - Daily reset verification
   - **Milestone:** Production-ready

---

## Technical Challenges

### Challenge 1: Async in Windows Service

**Problem:** Windows Services expect synchronous API, but Risk Manager is async

**Current Architecture:**
```python
# Risk Manager is async
async def main():
    manager = await RiskManager.create(config)
    await manager.start()
    # Runs forever
```

**Windows Service API:**
```python
# Service API is synchronous
class RiskManagerService(win32serviceutil.ServiceFramework):
    def SvcDoRun(self):
        # This method must return when service stops
        # How do we run async code here?
        pass
```

**Solution:**
```python
def SvcDoRun(self):
    """Bridge synchronous service API to async Risk Manager."""

    # Option 1: Use asyncio.run()
    asyncio.run(self.async_main())

    # async_main handles:
    # - Starting Risk Manager
    # - Waiting for stop signal
    # - Graceful shutdown

async def async_main(self):
    """Async main loop."""
    manager = await RiskManager.create(config)
    await manager.start()

    # Wait for stop signal from Windows
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
    )

    # Graceful shutdown
    await manager.stop()
```

**Key Insight:** Use `asyncio.run()` in `SvcDoRun()` to bridge sync → async

**Testing Strategy:**
1. Test async Risk Manager standalone
2. Test service wrapper without async (basic start/stop)
3. Integrate async with service wrapper
4. Test stop signal propagation

---

### Challenge 2: Graceful Shutdown

**Problem:** Service stop signal must cleanly shut down async tasks

**Current Flow:**
```
Windows → SvcStop() → SetEvent(stop_event) → ???
                                                ↓
                                    How to stop async tasks?
```

**Solution:**
```python
class RiskManagerService(win32serviceutil.ServiceFramework):
    def __init__(self, args):
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.shutdown_event = asyncio.Event()  # Async event

    def SvcStop(self):
        """Called by Windows when service should stop."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)  # Signal Windows event

    async def async_main(self):
        """Async main loop."""
        manager = await RiskManager.create(config)
        await manager.start()

        # Wait for stop signal (blocking)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        )

        # Stop signal received!
        logger.info("Stop signal received, shutting down...")

        # Graceful shutdown
        await manager.stop()  # Async shutdown
        await scheduler.stop()
        await db.close()
```

**Shutdown Checklist:**
1. Close SDK connections (TopstepX)
2. Flush database writes
3. Stop scheduled tasks
4. Close log files
5. Report service stopped

**Testing:**
- Test normal stop (`sc stop RiskManagerV34`)
- Test forced stop (Task Manager)
- Test crash recovery
- Verify no data loss

---

### Challenge 3: Scheduled Tasks with Timezone

**Problem:** Daily reset at midnight ET, but server may be in different timezone

**Current Approach:**
```python
# Naive approach (WRONG!)
scheduler.add_job(
    func=reset_daily_counters,
    trigger='cron',
    hour=0,
    minute=0  # Midnight in server timezone (NOT ET!)
)
```

**Solution:**
```python
import pytz

# Correct approach
et_tz = pytz.timezone('America/New_York')

scheduler.add_job(
    func=reset_daily_counters,
    trigger=CronTrigger(
        hour=0,
        minute=0,
        timezone=et_tz  # Midnight ET, regardless of server timezone
    )
)
```

**Daylight Saving Time:**
- ET = UTC-5 (Standard Time, winter)
- EDT = UTC-4 (Daylight Time, summer)
- `pytz` handles DST transitions automatically

**Edge Case: DST Transition at Midnight**
- Spring forward: 2 AM → 3 AM (missing hour)
- Fall back: 2 AM → 1 AM (repeated hour)
- Reset at midnight is safe (before transition)

**Testing:**
- Test during EST (winter)
- Test during EDT (summer)
- Test on DST transition days (March, November)

---

### Challenge 4: Service Debugging

**Problem:** Windows Services have no console output

**Traditional Debugging:**
```python
print("Debug message")  # Doesn't work in service!
```

**Solutions:**

**1. Windows Event Log:**
```python
import logging
import logging.handlers

logger = logging.getLogger('RiskManagerService')
handler = logging.handlers.NTEventLogHandler('Risk Manager V34')
logger.addHandler(handler)

logger.info("Service started")  # Appears in Event Viewer
```

**2. File Logging:**
```python
from loguru import logger

logger.add(
    "C:/ProgramData/RiskManager/logs/service.log",
    rotation="1 day",
    retention="30 days"
)

logger.info("Service started")  # Appears in file
```

**3. Debugging Mode:**
```python
# Run service in debug mode (console output)
python windows_service.py debug
```

**Viewing Logs:**
```powershell
# Event Viewer
eventvwr.msc

# Or via PowerShell
Get-EventLog -LogName Application -Source "Risk Manager V34" -Newest 10
```

---

## Deployment Checklist

### Pre-Deployment Requirements

**Before first deployment:**
- [ ] `pywin32` added to `pyproject.toml`
- [ ] Service Wrapper implemented and tested
- [ ] Service Installer created
- [ ] ACL permissions configured
- [ ] Service recovery policy set
- [ ] Admin CLI elevation check implemented
- [ ] Scheduled tasks integrated
- [ ] Daily reset (MOD-004) tested
- [ ] Documentation complete
- [ ] Windows test environment available

### Installation Procedure

**Step 1: Prepare Environment (Admin)**
```powershell
# Right-click PowerShell → Run as Administrator
cd C:\Users\...\risk-manager-v34

# Install dependencies
uv sync

# Verify pywin32
python -c "import win32service; print('OK')"
```

**Step 2: Install Service (Admin)**
```powershell
# Run installation script
python scripts/install_service.py

# Expected output:
# ✅ Created: C:/ProgramData/RiskManager/config
# ✅ Set ACL permissions: C:/ProgramData/RiskManager/config
# ✅ Installed service: Risk Manager V34
# ✅ Configured service recovery policy
```

**Step 3: Configure Service (Admin)**
```powershell
# Edit configuration
notepad C:\ProgramData\RiskManager\config\risk_config.yaml

# Set API credentials, risk rules, etc.
```

**Step 4: Start Service (Admin)**
```powershell
# Start service
sc start RiskManagerV34

# Check status
sc query RiskManagerV34

# Expected:
# STATE: RUNNING
```

**Step 5: Verify Service (Admin)**
```powershell
# Check Event Viewer
eventvwr.msc
# → Windows Logs → Application
# → Look for "Risk Manager V34" events

# Check service logs
cat C:\ProgramData\RiskManager\logs\service.log
```

**Step 6: Test Auto-Start (Admin)**
```powershell
# Reboot computer
shutdown /r /t 0

# After reboot, check service status
sc query RiskManagerV34

# Expected: SERVICE_RUNNING
```

### Post-Deployment Verification

**Verify Protection Layers:**
```powershell
# Test 1: Trader cannot stop service (Normal PowerShell)
sc stop RiskManagerV34
# Expected: Access Denied

# Test 2: Trader cannot edit config
notepad C:\ProgramData\RiskManager\config\risk_config.yaml
# Try to save → Expected: Access Denied

# Test 3: Trader can view status (Normal PowerShell)
risk-manager trader
# Expected: Opens successfully
```

**Verify Scheduled Tasks:**
```powershell
# Check next reset time
risk-manager admin
# Select [4] View Scheduled Tasks
# Expected: Daily reset at 00:00 ET
```

**Verify Crash Recovery:**
```powershell
# Kill service process (Admin)
taskkill /F /PID <service_pid>

# Wait 1 minute
# Check service status
sc query RiskManagerV34

# Expected: SERVICE_RUNNING (auto-restarted)
```

---

## Blockers Analysis

### What's Blocked by Missing Windows Service

**Cannot Deploy to Production:**
- ❌ System only runs as standalone Python script
- ❌ No auto-start on boot
- ❌ No crash recovery
- ❌ Trader can kill process easily
- ❌ No scheduled tasks (daily reset, etc.)
- ❌ No Windows Event Log integration

**Cannot Implement Core Features:**
- ❌ **MOD-004 Daily Reset** (requires scheduled tasks)
- ❌ **Process Protection** (requires service + ACL)
- ❌ **Admin CLI Service Control** (requires service API)
- ❌ **Holiday Calendar Integration** (requires scheduled tasks)

**Cannot Meet Security Requirements:**
- ❌ Service not "unkillable" (specification requirement)
- ❌ Config files not protected by ACL
- ❌ No Windows UAC integration
- ❌ Admin CLI not elevation-protected

### What Can Be Built in Parallel

**While Windows Service is Being Developed:**

✅ **Risk Rules** (independent)
- Can implement all 12 risk rules
- Can test standalone (without service)
- Can run in development mode

✅ **State Managers** (independent)
- PnLTracker (already exists)
- LockoutManager (needs implementation)
- TimerManager (needs implementation)

✅ **CLI Commands** (partial)
- Trader CLI (view-only, no service control)
- Admin CLI menu structure (no service integration yet)

✅ **Testing** (development mode)
- Unit tests (all rules)
- Integration tests (SDK integration)
- Runtime tests (standalone process)

**After Service Wrapper Complete:**

✅ **Service Installer** (depends on wrapper)
✅ **Service Control CLI** (depends on wrapper)
✅ **Scheduled Tasks** (depends on wrapper)
✅ **Process Protection** (depends on installer)

---

## Testing Strategy

### Development Testing (Without Service)

**Goal:** Test Risk Manager functionality standalone

**Approach:**
```python
# test_standalone.py

import asyncio
from risk_manager.core.manager import RiskManager
from risk_manager.core.config import RiskConfig

async def test_standalone():
    """Run Risk Manager without Windows Service."""

    config = RiskConfig.from_file("config/risk_config.yaml")
    manager = await RiskManager.create(config)

    # Start manager
    await manager.start()

    # Run for 10 seconds
    await asyncio.sleep(10)

    # Stop manager
    await manager.stop()

    print("✅ Standalone test passed")

asyncio.run(test_standalone())
```

**Run:**
```bash
python test_standalone.py
```

**What to Test:**
- Risk Manager initialization
- SDK connection
- Event processing
- Rule evaluation
- State persistence
- Graceful shutdown

### Service Testing (With Service)

**Goal:** Test Windows Service wrapper

**Phase 1: Installation Testing**
```powershell
# Test installation (Admin)
python scripts/install_service.py

# Verify directories created
ls C:\ProgramData\RiskManager

# Expected:
# config/
# data/
# logs/

# Verify service installed
sc query RiskManagerV34

# Expected:
# SERVICE_NAME: RiskManagerV34
# STATE: STOPPED
```

**Phase 2: Start/Stop Testing**
```powershell
# Start service
sc start RiskManagerV34

# Wait 5 seconds

# Check status
sc query RiskManagerV34

# Expected: STATE: RUNNING

# Check Event Viewer
eventvwr.msc
# → Application → Look for "Risk Manager V34" startup events

# Stop service
sc stop RiskManagerV34

# Check Event Viewer for shutdown events
```

**Phase 3: Crash Recovery Testing**
```powershell
# Kill service process (Admin)
taskkill /F /PID <service_pid>

# Wait 1 minute (recovery policy: restart after 60 seconds)

# Check status
sc query RiskManagerV34

# Expected: STATE: RUNNING (auto-restarted)

# Check Event Viewer for recovery events
```

**Phase 4: Scheduled Task Testing**
```powershell
# Test daily reset manually
risk-manager admin
# Select [Manual Trigger Reset]

# Check logs
cat C:\ProgramData\RiskManager\logs\service.log | grep "Daily reset"

# Expected: "Daily reset complete for account X"

# Test scheduled reset (wait until midnight ET or modify trigger time)
```

**Phase 5: Protection Testing**
```powershell
# Test as normal user (NO admin)

# Test 1: Cannot stop service
sc stop RiskManagerV34
# Expected: Access Denied

# Test 2: Cannot edit config
notepad C:\ProgramData\RiskManager\config\risk_config.yaml
# Try to save changes
# Expected: Access Denied dialog

# Test 3: Cannot delete database
del C:\ProgramData\RiskManager\data\risk_state.db
# Expected: Access Denied

# Test 4: Cannot run Admin CLI
risk-manager admin
# Expected: Error message + exit
```

### Integration Testing

**Goal:** Test service with full stack

**Test Scenarios:**

**1. Boot Test:**
```
Step 1: Install service
Step 2: Reboot computer
Step 3: Verify service auto-started
Step 4: Verify Risk Manager connected to SDK
Step 5: Verify event processing working
```

**2. Daily Reset Test:**
```
Step 1: Set reset time to "now + 2 minutes"
Step 2: Wait for reset
Step 3: Verify P&L counters reset
Step 4: Verify lockouts cleared
Step 5: Verify logged correctly
```

**3. Crash Recovery Test:**
```
Step 1: Start service
Step 2: Trigger exception in Risk Manager
Step 3: Verify service crashes
Step 4: Wait 1 minute
Step 5: Verify service auto-restarted
Step 6: Verify Risk Manager reconnected
```

**4. Protection Test:**
```
Step 1: Login as trader (normal user)
Step 2: Try to stop service → BLOCKED
Step 3: Try to edit config → BLOCKED
Step 4: Try to run admin CLI → BLOCKED
Step 5: Login as admin
Step 6: All admin actions → ALLOWED
```

### Automated Testing

**Unit Tests:**
```python
# tests/unit/test_service/test_service_wrapper.py

import pytest
from risk_manager.service.windows_service import RiskManagerService

def test_service_initialization():
    """Test service can be initialized."""
    service = RiskManagerService([''])
    assert service._svc_name_ == "RiskManagerV34"
    assert service._svc_display_name_ == "Risk Manager V34"

# Note: Full service tests require Windows environment
```

**Integration Tests (WSL2 Limitation):**
- Windows Service tests cannot run in WSL2
- Must run on native Windows
- Consider GitHub Actions Windows runner

---

## Summary

Risk Manager V34 is **0% deployed** - the entire Windows Service layer is missing despite complete specifications.

**Critical Path:**
1. Add `pywin32` dependency (0.5 days) ← START HERE
2. Implement Service Wrapper (1 week) ← BLOCKER
3. Implement Service Installer (3 days)
4. Implement Service Control CLI (2 days)
5. Implement Scheduled Tasks (4 days)
6. Implement Process Protection (3 days)

**Total Effort:** 2-3 weeks (2 weeks if parallelized after Service Wrapper)

**Blockers:**
- Service Wrapper blocks: Installer, Control, Tasks, Protection
- MOD-004 Reset Manager blocks: Scheduled Tasks daily reset
- Admin CLI framework blocks: Service Control CLI integration

**Recommended Next Steps:**
1. Add `pywin32` to `pyproject.toml` (5 minutes)
2. Create `src/risk_manager/service/` directory structure
3. Implement basic Service Wrapper skeleton
4. Test service installation and start/stop
5. Proceed with advanced features (tasks, protection)

**After Implementation:**
- ✅ Service auto-starts on boot
- ✅ Service "unkillable" by trader
- ✅ Daily reset at midnight ET
- ✅ Auto-restart on crash
- ✅ Config files protected by ACL
- ✅ Admin CLI controls service
- ✅ Production-ready deployment

---

**Analysis Complete**
**Date:** 2025-10-25
**Status:** 100% missing - complete implementation required
**Priority:** Critical - required for production deployment
