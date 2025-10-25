# Wave 2 Gap Analysis: CLI System Implementation

**Researcher:** Researcher 3 - CLI System Gap Analyst
**Date:** 2025-10-25
**Project:** Risk Manager V34
**Mission:** Analyze missing CLI system and create implementation roadmap

---

## Executive Summary

The CLI system (both Admin and Trader interfaces) is **100% missing** from the codebase. The `src/risk_manager/cli/` directory does not exist, and `pyproject.toml` declares an entry point that has no implementation.

**Key Findings:**
- **Total CLI Commands**: 13 (6 admin + 7 trader)
- **Implemented**: 0 (0%)
- **Missing**: 13 (100%)
- **CLI Framework**: Typer (already in dependencies)
- **Estimated Total Effort**: 2-3 weeks
- **Critical Blocker**: CLI depends on state managers (lockout, timer, reset) which are also missing

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Implementation Status](#2-implementation-status)
3. [Detailed Gap Analysis](#3-detailed-gap-analysis)
4. [Critical Dependencies](#4-critical-dependencies)
5. [Windows UAC Integration](#5-windows-uac-integration)
6. [Recommended Implementation Order](#6-recommended-implementation-order)
7. [Integration Requirements](#7-integration-requirements)
8. [CLI Framework Choice](#8-cli-framework-choice)
9. [Effort Estimates](#9-effort-estimates)

---

## 1. Current State Analysis

### 1.1 Directory Structure Check

**Expected:**
```
src/risk_manager/
├── cli/
│   ├── __init__.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── auth.py          # Windows UAC elevation check
│   │   ├── config.py        # Configure rules
│   │   ├── unlock.py        # Unlock accounts
│   │   ├── service.py       # Start/stop service
│   │   ├── logs.py          # View logs
│   │   ├── status.py        # Detailed status
│   │   └── emergency.py     # Emergency stop
│   └── trader/
│       ├── __init__.py
│       ├── status.py        # View risk status
│       ├── pnl.py           # View P&L
│       ├── rules.py         # View rules
│       ├── lockouts.py      # View lockouts
│       ├── history.py       # View violations
│       ├── limits.py        # View limits
│       └── logs.py          # View logs (read-only)
```

**Actual:**
```bash
$ ls -la src/risk_manager/cli/
ls: cannot access 'src/risk_manager/cli/': No such file or directory
```

**Status:** ❌ **Directory does not exist**

---

### 1.2 Entry Point Configuration

**pyproject.toml declares:**
```toml
[project.scripts]
risk-manager = "risk_manager.cli:app"
```

**Problem:** The module `risk_manager.cli` does not exist, so this entry point will fail at runtime.

**Status:** ❌ **Entry point broken**

---

### 1.3 CLI Framework

**pyproject.toml dependencies:**
```toml
dependencies = [
    "typer>=0.9.0",          # CLI framework ✅ Already declared
    "rich>=13.7.0",          # Beautiful console output ✅ Already declared
]
```

**Good News:** Framework choice already made (Typer + Rich for beautiful output)

**Status:** ✅ **Framework declared, needs implementation**

---

## 2. Implementation Status

### 2.1 Admin CLI Commands (6)

| Command | Purpose | Status | Implementation File | Effort |
|---------|---------|--------|---------------------|--------|
| **config** | Configure risk rules, update YAML | ❌ Missing | `cli/admin/config.py` | 3 days |
| **unlock** | Unlock locked accounts (emergency override) | ❌ Missing | `cli/admin/unlock.py` | 2 days |
| **service** | Start/stop/restart Windows Service | ❌ Missing | `cli/admin/service.py` | 2 days |
| **logs** | View logs, set log levels | ❌ Missing | `cli/admin/logs.py` | 1 day |
| **status** | View detailed system status | ❌ Missing | `cli/admin/status.py` | 2 days |
| **emergency** | Emergency stop, force close all positions | ❌ Missing | `cli/admin/emergency.py` | 2 days |

**Total Admin CLI:** 0/6 (0%)

---

### 2.2 Trader CLI Commands (7)

| Command | Purpose | Status | Implementation File | Effort |
|---------|---------|--------|---------------------|--------|
| **status** | View current risk status | ❌ Missing | `cli/trader/status.py` | 2 days |
| **pnl** | View P&L breakdown | ❌ Missing | `cli/trader/pnl.py` | 2 days |
| **rules** | View active rules (not edit) | ❌ Missing | `cli/trader/rules.py` | 1 day |
| **lockouts** | View if account locked and why | ❌ Missing | `cli/trader/lockouts.py` | 1 day |
| **history** | View violation history | ❌ Missing | `cli/trader/history.py` | 1 day |
| **limits** | View current limits and utilization | ❌ Missing | `cli/trader/limits.py` | 1 day |
| **logs** | View logs (read-only) | ❌ Missing | `cli/trader/logs.py` | 1 day |

**Total Trader CLI:** 0/7 (0%)

---

### 2.3 Overall Status

```
┌─────────────────────────────────────────────────────────┐
│ CLI SYSTEM IMPLEMENTATION STATUS                         │
├─────────────────────────────────────────────────────────┤
│ Admin CLI:     0/6  (0%)   ██░░░░░░░░░░░░░░░░░░░░      │
│ Trader CLI:    0/7  (0%)   ██░░░░░░░░░░░░░░░░░░░░      │
│ Framework:     1/1  (100%) ████████████████████████     │
│ Auth System:   0/1  (0%)   ██░░░░░░░░░░░░░░░░░░░░      │
├─────────────────────────────────────────────────────────┤
│ TOTAL:         1/15 (7%)   ███░░░░░░░░░░░░░░░░░░░      │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Gap Analysis

### 3.1 Admin CLI Commands

#### 3.1.1 Command: config

**Purpose:** Configure risk rules, update `risk_config.yaml` interactively

**Status:** ❌ Missing

**What it should do:**
- List current rules and their enabled/disabled status
- Enable/disable rules interactively
- Update rule parameters (limits, thresholds, timeouts)
- Validate YAML syntax before saving
- Reload Risk Manager without full restart
- Show preview of changes before applying
- Rollback capability if changes break system

**Dependencies:**
- **Config loader** (❌ missing - `src/risk_manager/core/config.py` exists but basic)
- **YAML validation** (❌ missing - Pydantic models incomplete)
- **Service communication** (❌ missing - how CLI talks to running service)
- **Hot reload mechanism** (❌ missing - update config without restart)

**Windows UAC:** ✅ Requires elevation (file write permissions)

**Estimated Effort:** 3 days

**Implementation Notes:**
```python
# cli/admin/config.py

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, IntPrompt

app = typer.Typer()
console = Console()

@app.command()
def list():
    """List all risk rules and their configuration."""
    # Load config/risk_config.yaml
    # Display as table with Rich
    pass

@app.command()
def set(rule: str, parameter: str, value: str):
    """Set a rule parameter."""
    # Load YAML
    # Validate new value
    # Update YAML
    # Reload service
    pass

@app.command()
def enable(rule: str):
    """Enable a risk rule."""
    pass

@app.command()
def disable(rule: str):
    """Disable a risk rule."""
    pass

@app.command()
def edit():
    """Interactive rule editor (TUI)."""
    # Launch full-screen editor
    pass
```

**Key Challenges:**
1. How does CLI communicate with running Risk Manager service?
   - Option A: Shared SQLite database (state updates)
   - Option B: IPC (named pipes, sockets)
   - Option C: Config file + service watches for changes
2. How to trigger config reload in service?
3. How to validate config without breaking running system?

---

#### 3.1.2 Command: unlock

**Purpose:** Manually unlock locked accounts (emergency override)

**Status:** ❌ Missing

**What it should do:**
- Display current lockouts (reason, expires_at)
- Show countdown timers
- Allow admin to remove specific lockout or all lockouts
- Log unlock event (audit trail)
- Confirm unlock action (requires explicit "yes")
- Immediately notify trader CLI of unlock

**Dependencies:**
- **Lockout Manager** (❌ missing - `src/risk_manager/state/lockout_manager.py` doesn't exist)
- **Database access** (✅ exists - `src/risk_manager/state/database.py`)
- **Service communication** (❌ missing - notify service of unlock)

**Windows UAC:** ✅ Requires elevation

**Estimated Effort:** 2 days

**Implementation Notes:**
```python
# cli/admin/unlock.py

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

app = typer.Typer()
console = Console()

@app.command()
def list():
    """List all active lockouts."""
    # Query lockouts table from SQLite
    # Display as table
    pass

@app.command()
def remove(account_id: str, rule_id: str = None):
    """Remove lockout for account (specific rule or all)."""
    # Confirm action
    if not Confirm.ask("Are you sure you want to unlock this account?"):
        return

    # Remove from lockouts table
    # Log event
    # Notify service
    pass

@app.command()
def remove_all():
    """Remove all lockouts (DANGEROUS)."""
    if not Confirm.ask("Remove ALL lockouts? This is dangerous!"):
        return

    # Clear lockouts table
    # Log event
    # Notify service
    pass
```

**Key Challenges:**
1. Lockout Manager doesn't exist yet (Wave 2 critical dependency)
2. How to notify running service of unlock?
3. Race condition: What if rule re-locks immediately after unlock?

---

#### 3.1.3 Command: service

**Purpose:** Start/stop/restart Windows Service

**Status:** ❌ Missing

**What it should do:**
- Start Risk Manager Windows Service
- Stop service gracefully
- Restart service
- View service status (running/stopped)
- View service logs (last N lines)
- Set service startup type (automatic/manual)

**Dependencies:**
- **Windows Service wrapper** (❌ missing - `src/service/windows_service.py` doesn't exist)
- **`pywin32` library** (❌ not in dependencies)
- **Service installer** (❌ missing - `scripts/install_service.py` doesn't exist)

**Windows UAC:** ✅ Requires elevation (service control requires admin)

**Estimated Effort:** 2 days

**Implementation Notes:**
```python
# cli/admin/service.py

import typer
import win32serviceutil
import win32service
from rich.console import Console

app = typer.Typer()
console = Console()

SERVICE_NAME = "RiskManagerV34"

@app.command()
def start():
    """Start the Risk Manager service."""
    try:
        win32serviceutil.StartService(SERVICE_NAME)
        console.print("✅ Service started", style="green")
    except Exception as e:
        console.print(f"❌ Failed to start service: {e}", style="red")

@app.command()
def stop():
    """Stop the Risk Manager service."""
    try:
        win32serviceutil.StopService(SERVICE_NAME)
        console.print("✅ Service stopped", style="green")
    except Exception as e:
        console.print(f"❌ Failed to stop service: {e}", style="red")

@app.command()
def restart():
    """Restart the Risk Manager service."""
    stop()
    start()

@app.command()
def status():
    """View service status."""
    status = win32serviceutil.QueryServiceStatus(SERVICE_NAME)
    # Parse status code and display
    pass
```

**Key Challenges:**
1. Windows Service doesn't exist yet (Wave 2 component)
2. Need to add `pywin32` to dependencies
3. Linux/Mac compatibility? (Service concept is Windows-specific)

---

#### 3.1.4 Command: logs

**Purpose:** View logs, set log levels

**Status:** ❌ Missing

**What it should do:**
- View last N lines of log file
- Stream logs in real-time (tail -f behavior)
- Filter logs by level (DEBUG, INFO, WARNING, ERROR)
- Filter logs by module
- Search logs by keyword
- Set log level (requires service reload)

**Dependencies:**
- **Log file location** (✅ defined - `data/logs/risk_manager.log`)
- **Logging system** (✅ exists - using loguru)

**Windows UAC:** ✅ Requires elevation (log file is in protected directory)

**Estimated Effort:** 1 day

**Implementation Notes:**
```python
# cli/admin/logs.py

import typer
from rich.console import Console
from pathlib import Path

app = typer.Typer()
console = Console()

LOG_FILE = Path("data/logs/risk_manager.log")

@app.command()
def tail(lines: int = 50):
    """View last N lines of log file."""
    if not LOG_FILE.exists():
        console.print("❌ Log file not found", style="red")
        return

    with open(LOG_FILE) as f:
        all_lines = f.readlines()
        for line in all_lines[-lines:]:
            console.print(line.strip())

@app.command()
def stream():
    """Stream logs in real-time (tail -f)."""
    # Implement tail -f behavior
    pass

@app.command()
def filter(level: str = None, module: str = None):
    """Filter logs by level or module."""
    pass

@app.command()
def search(keyword: str):
    """Search logs by keyword."""
    pass
```

**Key Challenges:**
1. Real-time streaming (tail -f) requires file watching
2. Large log files (>100MB) need efficient reading
3. JSON log format parsing (production mode)

---

#### 3.1.5 Command: status

**Purpose:** View detailed system status

**Status:** ❌ Missing

**What it should do:**
- Display service status (running/stopped)
- Show connected accounts
- Show active rules (enabled/disabled)
- Show current positions (all instruments)
- Show daily P&L (realized, unrealized)
- Show active lockouts and timers
- Show system health (SDK connected, database accessible)
- Show recent violations (last 10)

**Dependencies:**
- **Service communication** (❌ missing - query running service)
- **Database access** (✅ exists)
- **State managers** (❌ missing - PnLTracker, LockoutManager, TimerManager)

**Windows UAC:** ✅ Requires elevation

**Estimated Effort:** 2 days

**Implementation Notes:**
```python
# cli/admin/status.py

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer()
console = Console()

@app.command()
def show():
    """Display comprehensive system status."""

    # 1. Service Status
    console.print(Panel("🚀 Service Status: RUNNING", style="green"))

    # 2. Account Status
    # Query from database/service

    # 3. Active Rules
    table = Table(title="Active Rules")
    table.add_column("Rule")
    table.add_column("Status")
    table.add_column("Threshold")
    # ... populate from config

    # 4. Current Positions
    # Query from SDK via service

    # 5. Daily P&L
    # Query from PnLTracker

    # 6. Active Lockouts
    # Query from LockoutManager

    # 7. Recent Violations
    # Query from database

    console.print(table)

@app.command()
def health():
    """Check system health (SDK connected, DB accessible)."""
    pass
```

**Key Challenges:**
1. Requires access to running service (IPC)
2. Requires multiple state managers (not implemented)
3. Performance (querying many sources)

---

#### 3.1.6 Command: emergency

**Purpose:** Emergency stop, force close all positions

**Status:** ❌ Missing

**What it should do:**
- Force close ALL positions across ALL accounts
- Cancel ALL pending orders
- Set hard lockout (cannot trade until admin unlocks)
- Log emergency stop event (who, when, why)
- Confirm action (requires typing "EMERGENCY STOP" to confirm)
- Send notifications (Discord, Telegram if configured)

**Dependencies:**
- **SDK integration** (✅ exists - `suite.close_position()`, `suite.cancel_all_orders()`)
- **Enforcement executor** (✅ exists - `src/risk_manager/sdk/enforcement.py`)
- **Lockout manager** (❌ missing)

**Windows UAC:** ✅ Requires elevation

**Estimated Effort:** 2 days

**Implementation Notes:**
```python
# cli/admin/emergency.py

import typer
from rich.console import Console
from rich.prompt import Prompt

app = typer.Typer()
console = Console()

@app.command()
def stop():
    """
    EMERGENCY STOP: Force close all positions and lock trading.

    ⚠️  WARNING: This will immediately:
    - Close ALL open positions
    - Cancel ALL pending orders
    - Lock trading until manual unlock
    """
    console.print("⚠️  EMERGENCY STOP", style="bold red")
    console.print("This will close ALL positions and lock trading!")

    confirmation = Prompt.ask("Type 'EMERGENCY STOP' to confirm")
    if confirmation != "EMERGENCY STOP":
        console.print("❌ Cancelled", style="yellow")
        return

    # 1. Close all positions
    # await suite.close_position()  # All instruments

    # 2. Cancel all orders
    # await suite.cancel_all_orders()

    # 3. Set hard lockout
    # lockout_manager.set_lockout(reason="EMERGENCY STOP", permanent=True)

    # 4. Log event
    # logger.critical(f"EMERGENCY STOP by {admin_user}")

    # 5. Send notifications
    # notify_discord/telegram

    console.print("✅ Emergency stop completed", style="green")
```

**Key Challenges:**
1. Direct SDK access from CLI (not via service)
2. Authentication needed (API key from config)
3. Risk of partial execution (position closes but order cancel fails)
4. Notification system not implemented

---

### 3.2 Trader CLI Commands

#### 3.2.1 Command: status

**Purpose:** View current risk status (view-only)

**Status:** ❌ Missing

**What it should do:**
- Display account status (ACTIVE, LOCKED, WARNING)
- Show daily P&L (realized, unrealized, total)
- Show current positions (all instruments)
- Show rule status (which rules are near limits)
- Show active lockouts (if any)
- Show countdown timers (until reset, until unlock)
- Auto-refresh every 5 seconds (live TUI)

**Dependencies:**
- **Database access** (✅ exists - read-only)
- **PnL Tracker** (❌ missing)
- **Lockout Manager** (❌ missing)
- **Service communication** (❌ missing - for live positions)

**Windows UAC:** ❌ **No elevation needed** (read-only)

**Estimated Effort:** 2 days

**Implementation Notes:**
```python
# cli/trader/status.py

import typer
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout

app = typer.Typer()
console = Console()

@app.command()
def show(live: bool = False):
    """Display current risk status."""

    if not live:
        # One-time display
        display_status()
    else:
        # Live updating display (every 5s)
        with Live(auto_refresh=False) as live_display:
            while True:
                live_display.update(display_status())
                time.sleep(5)

def display_status():
    """Generate status display."""
    layout = Layout()

    # Account status banner
    # Daily P&L section
    # Current positions section
    # Rule status section
    # Lockouts/timers section

    return layout
```

**Key Challenges:**
1. Live TUI requires Rich Live display
2. Performance (refresh every 5s)
3. Data access (DB + running service)

---

#### 3.2.2 Command: pnl

**Purpose:** View P&L breakdown

**Status:** ❌ Missing

**What it should do:**
- Show daily P&L (realized, unrealized, total)
- Show P&L by instrument (MNQ, ES, GC)
- Show P&L history (last 7 days, last 30 days)
- Show trade count (today, this week, this month)
- Show win rate (winning trades / total trades)
- Show largest win/loss
- Export to CSV

**Dependencies:**
- **PnL Tracker** (❌ missing)
- **Database access** (✅ exists - trades table)

**Windows UAC:** ❌ No elevation needed

**Estimated Effort:** 2 days

**Implementation Notes:**
```python
# cli/trader/pnl.py

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def today():
    """Show today's P&L."""
    pass

@app.command()
def history(days: int = 7):
    """Show P&L history for last N days."""
    pass

@app.command()
def by_instrument():
    """Show P&L breakdown by instrument."""
    pass

@app.command()
def stats():
    """Show P&L statistics (win rate, largest win/loss)."""
    pass
```

**Key Challenges:**
1. PnL Tracker doesn't exist (Wave 2 dependency)
2. Historical data might not be stored (only daily_pnl, not per-trade)
3. Win rate calculation requires trade history

---

#### 3.2.3 Command: rules

**Purpose:** View active rules (not edit)

**Status:** ❌ Missing

**What it should do:**
- List all rules (enabled/disabled)
- Show rule thresholds (limits, timeouts)
- Show current utilization (e.g., "2/5 contracts", "90% of daily loss")
- Color-code by risk level (green, yellow, red)
- No ability to edit (view-only)

**Dependencies:**
- **Config loader** (❌ incomplete)
- **State access** (for current utilization)

**Windows UAC:** ❌ No elevation needed

**Estimated Effort:** 1 day

**Implementation Notes:**
```python
# cli/trader/rules.py

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def list():
    """List all risk rules and their status."""

    table = Table(title="Risk Rules")
    table.add_column("Rule")
    table.add_column("Status")
    table.add_column("Limit")
    table.add_column("Current")
    table.add_column("Utilization")

    # Load from risk_config.yaml
    # Query current values from database/service

    # Example rows:
    # | Max Contracts           | ✅ Enabled | 5       | 2       | ████░░ 40%  |
    # | Daily Realized Loss     | ✅ Enabled | -$500   | -$450   | █████░ 90%  |
    # | Trade Frequency (hour)  | ✅ Enabled | 10      | 7       | ███░░░ 70%  |

    console.print(table)
```

**Key Challenges:**
1. Current utilization requires live data (service communication)
2. Per-rule state queries (different for each rule type)

---

#### 3.2.4 Command: lockouts

**Purpose:** View if account locked and why

**Status:** ❌ Missing

**What it should do:**
- Show if account is currently locked
- Show lockout reason (which rule violated)
- Show lockout expiration (countdown timer)
- Show lockout type (hard lockout vs cooldown timer)
- Show unlock condition (time, manual, reset)
- Show history of recent lockouts

**Dependencies:**
- **Lockout Manager** (❌ missing)
- **Database access** (✅ exists - lockouts table)

**Windows UAC:** ❌ No elevation needed

**Estimated Effort:** 1 day

**Implementation Notes:**
```python
# cli/trader/lockouts.py

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer()
console = Console()

@app.command()
def show():
    """Show current lockout status."""

    # Query lockouts table
    lockouts = db.get_active_lockouts(account_id)

    if not lockouts:
        console.print("✅ No active lockouts", style="green")
        return

    for lockout in lockouts:
        panel = Panel(
            f"Reason: {lockout['reason']}\n"
            f"Since: {lockout['locked_at']}\n"
            f"Until: {lockout['expires_at']}\n"
            f"Remaining: {calculate_remaining_time(lockout['expires_at'])}",
            title="🔒 LOCKOUT ACTIVE",
            style="red"
        )
        console.print(panel)

@app.command()
def history(days: int = 7):
    """Show lockout history for last N days."""
    pass
```

**Key Challenges:**
1. Lockout Manager doesn't exist (Wave 2 dependency)
2. Countdown timer requires continuous refresh

---

#### 3.2.5 Command: history

**Purpose:** View violation history

**Status:** ❌ Missing

**What it should do:**
- Show recent rule violations (last 10, last 50, all)
- Show violation details (rule, timestamp, reason, enforcement action)
- Filter by rule
- Filter by date range
- Show enforcement actions taken (close position, cancel orders, lockout)

**Dependencies:**
- **Database access** (✅ exists - need violations table)
- **Violations table** (❌ doesn't exist - need to create)

**Windows UAC:** ❌ No elevation needed

**Estimated Effort:** 1 day

**Implementation Notes:**
```python
# cli/trader/history.py

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def show(limit: int = 10):
    """Show recent rule violations."""

    table = Table(title=f"Recent Violations (last {limit})")
    table.add_column("Timestamp")
    table.add_column("Rule")
    table.add_column("Reason")
    table.add_column("Action")

    # Query violations table
    # violations = db.get_violations(account_id, limit)

    console.print(table)

@app.command()
def filter(rule: str = None, start_date: str = None, end_date: str = None):
    """Filter violations by rule and/or date range."""
    pass
```

**Key Challenges:**
1. Violations table doesn't exist (need to create)
2. Enforcement logging needs to write to violations table
3. Large violation history (pagination needed)

---

#### 3.2.6 Command: limits

**Purpose:** View current limits and utilization

**Status:** ❌ Missing

**What it should do:**
- Show all rule limits (thresholds)
- Show current values
- Show utilization percentage
- Color-code by risk level (green <50%, yellow 50-80%, red >80%)
- Show visual progress bars

**Dependencies:**
- **Config loader** (❌ incomplete)
- **State access** (for current values)

**Windows UAC:** ❌ No elevation needed

**Estimated Effort:** 1 day

**Implementation Notes:**
```python
# cli/trader/limits.py

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

app = typer.Typer()
console = Console()

@app.command()
def show():
    """Show current limits and utilization."""

    table = Table(title="Risk Limits")
    table.add_column("Rule")
    table.add_column("Limit")
    table.add_column("Current")
    table.add_column("Utilization")

    # Load limits from config
    # Query current values from database/service

    # Add rows with color-coding
    # Green: <50%, Yellow: 50-80%, Red: >80%

    console.print(table)
```

**Key Challenges:**
1. Current values require live data (service communication)
2. Different rules have different data sources (positions, P&L, trade counts)

---

#### 3.2.7 Command: logs

**Purpose:** View logs (read-only)

**Status:** ❌ Missing

**What it should do:**
- View last N lines of log file
- Filter by log level (INFO, WARNING, ERROR only - no DEBUG)
- Search logs by keyword
- **Cannot** change log level (admin-only)
- **Cannot** clear logs (admin-only)

**Dependencies:**
- **Log file access** (✅ read permission granted by ACL)

**Windows UAC:** ❌ No elevation needed (read-only)

**Estimated Effort:** 1 day

**Implementation Notes:**
```python
# cli/trader/logs.py

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def tail(lines: int = 50):
    """View last N lines of log file."""
    # Same as admin/logs.py but read-only
    pass

@app.command()
def filter(level: str = None):
    """Filter logs by level (INFO, WARNING, ERROR only)."""
    # No DEBUG access for trader
    pass

@app.command()
def search(keyword: str):
    """Search logs by keyword."""
    pass
```

**Key Challenges:**
1. Same as admin logs command but restricted (no DEBUG, no clear)
2. Code duplication (should share logic with admin logs)

---

## 4. Critical Dependencies

### 4.1 Blocker: State Managers

**All CLI commands depend on state managers that don't exist:**

```
CLI Commands → State Managers (MISSING) → Database
```

**Missing State Managers:**

1. **PnLTracker** (`src/risk_manager/state/pnl_tracker.py`)
   - Status: ✅ **EXISTS** (8KB, 200 lines)
   - Used by: `admin/status`, `trader/status`, `trader/pnl`

2. **LockoutManager** (`src/risk_manager/state/lockout_manager.py`)
   - Status: ❌ **MISSING**
   - Used by: `admin/unlock`, `admin/status`, `trader/status`, `trader/lockouts`

3. **TimerManager** (`src/risk_manager/state/timer_manager.py`)
   - Status: ❌ **MISSING**
   - Used by: `admin/status`, `trader/status`, `trader/lockouts`

4. **ResetScheduler** (`src/risk_manager/state/reset_scheduler.py`)
   - Status: ❌ **MISSING**
   - Used by: Daily P&L reset, lockout expiration

5. **ViolationLogger** (new requirement)
   - Status: ❌ **MISSING**
   - Used by: `trader/history`

**Dependency Chain:**
```
Phase 1: Build State Managers
  └─ LockoutManager    (2 days)
  └─ TimerManager      (2 days)
  └─ ResetScheduler    (1 day)
  └─ ViolationLogger   (1 day)

Phase 2: Build CLI Commands (depends on Phase 1)
  └─ Admin CLI         (12 days)
  └─ Trader CLI        (9 days)
```

**Recommendation:** **State managers MUST be built first in Wave 2**

---

### 4.2 Blocker: Service Communication

**Problem:** CLI needs to communicate with running Risk Manager service

**Current Options:**

**Option A: Shared Database (RECOMMENDED)**
```
CLI → SQLite Database ← Risk Manager Service
```
- Pros: Simple, no IPC needed, works cross-platform
- Cons: Limited (can't trigger actions in real-time)
- Use for: Status queries, P&L, lockouts, logs

**Option B: Named Pipes (Windows)**
```
CLI → Named Pipe → Risk Manager Service
```
- Pros: Real-time, bi-directional
- Cons: Windows-only, complex
- Use for: Service control (start/stop), config reload

**Option C: HTTP API (Future)**
```
CLI → HTTP API → Risk Manager Service
```
- Pros: Standard, cross-platform, scalable
- Cons: More complex, requires web server
- Use for: Production deployments

**Recommendation:**
- **Phase 1 (MVP):** Shared database only (Option A)
- **Phase 2 (Production):** Add named pipes for Windows (Option B)
- **Phase 3 (Future):** Add HTTP API (Option C)

---

### 4.3 Blocker: Windows Service

**Problem:** Admin CLI commands (start/stop service) require Windows Service wrapper

**Current Status:**
- `src/service/windows_service.py` ❌ **MISSING**
- `scripts/install_service.py` ❌ **MISSING**
- `pywin32` dependency ❌ **NOT DECLARED**

**What's Needed:**
1. Windows Service wrapper class
2. Service installer script
3. Service uninstaller script
4. Add `pywin32>=306` to dependencies
5. Windows-specific installation docs

**Estimated Effort:** 3 days

**Can defer?** ✅ **YES** - CLI can work without service control commands initially

---

### 4.4 Blocker: Config Loader

**Problem:** CLI commands need to load/validate/update YAML configs

**Current Status:**
- `src/risk_manager/core/config.py` ✅ EXISTS (2.5KB)
- But: Missing validation, missing hot reload, missing YAML update utilities

**What's Needed:**
1. **Config Validator** - Validate YAML before saving
2. **Config Updater** - Update specific fields in YAML
3. **Hot Reload** - Notify service of config changes
4. **Config Templates** - Generate example configs

**Estimated Effort:** 2 days

**Can defer?** ❌ **NO** - Admin `config` command won't work without this

---

## 5. Windows UAC Integration

### 5.1 Elevation Detection

**Implementation:** `src/cli/admin/auth.py`

**Status:** ❌ Missing

**Code:**
```python
# src/cli/admin/auth.py

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

**Usage:**
```python
# cli/admin/admin_main.py

from .auth import require_admin

def main():
    """Admin CLI entry point."""

    # FIRST THING: Check elevation
    require_admin()  # Exits immediately if not elevated

    # Only reaches here if user has admin rights
    display_admin_menu()
```

**Cross-Platform:**
- Windows: Check `IsUserAnAdmin()`
- Linux/Mac: Check if `os.geteuid() == 0` (root)

**Estimated Effort:** 1 day

---

### 5.2 Access Control Summary

| CLI Type | UAC Required? | File Permissions | Service Access |
|----------|---------------|------------------|----------------|
| Admin CLI | ✅ YES (Run as Administrator) | Read/Write all files | Full control |
| Trader CLI | ❌ NO (Normal user) | Read-only (ACL protected) | Read-only queries |

---

## 6. Recommended Implementation Order

### Phase 1: Foundation (1 week)

**Goal:** Basic CLI structure + Trader CLI status (no admin features)

```
Day 1-2: CLI Framework Setup
  ├─ Create src/risk_manager/cli/ directory
  ├─ Implement cli/__init__.py (main entry point)
  ├─ Set up Typer app structure
  ├─ Implement auth.py (UAC detection)
  └─ Update pyproject.toml entry point

Day 3-4: Trader Status Command (MVP)
  ├─ Implement cli/trader/status.py
  ├─ Query database directly (PnL, lockouts)
  ├─ Display basic status (no live updates)
  └─ Test on Windows

Day 5: Trader Logs Command
  ├─ Implement cli/trader/logs.py
  ├─ Read log file (read-only)
  └─ Filter by level
```

**Deliverable:** `risk-manager status` works (view-only)

---

### Phase 2: Core Admin CLI (1 week)

**Goal:** Admin CLI with config, unlock, logs

**Prerequisites:** State managers (LockoutManager, TimerManager) must be built first

```
Day 1-2: Admin Config Command
  ├─ Implement cli/admin/config.py
  ├─ Load risk_config.yaml
  ├─ Display current rules
  ├─ Enable/disable rules
  └─ Update rule parameters

Day 3-4: Admin Unlock Command
  ├─ Implement cli/admin/unlock.py
  ├─ Query lockouts table
  ├─ Remove lockouts
  ├─ Log unlock events
  └─ Test emergency unlock scenario

Day 5: Admin Logs & Status
  ├─ Implement cli/admin/logs.py
  ├─ Implement cli/admin/status.py
  └─ Test admin workflows
```

**Deliverable:** Admin can configure rules and unlock accounts

---

### Phase 3: Advanced Trader CLI (3-4 days)

**Goal:** Complete trader CLI (P&L, rules, lockouts, history, limits)

```
Day 1: P&L & Rules
  ├─ Implement cli/trader/pnl.py
  ├─ Implement cli/trader/rules.py
  └─ Query database for historical data

Day 2: Lockouts & History
  ├─ Implement cli/trader/lockouts.py
  ├─ Implement cli/trader/history.py
  └─ Display violations

Day 3: Limits & Live Updates
  ├─ Implement cli/trader/limits.py
  ├─ Add live TUI updates (Rich Live)
  └─ Test refresh loops
```

**Deliverable:** Trader CLI fully functional

---

### Phase 4: Service Control (3-4 days)

**Goal:** Admin can start/stop Windows Service

**Prerequisites:** Windows Service wrapper must be built first

```
Day 1-2: Windows Service Wrapper
  ├─ Implement src/service/windows_service.py
  ├─ Add pywin32 to dependencies
  └─ Test service start/stop

Day 3: Service Control Commands
  ├─ Implement cli/admin/service.py
  ├─ start, stop, restart, status
  └─ Test on Windows

Day 4: Emergency Command
  ├─ Implement cli/admin/emergency.py
  ├─ Force close all positions
  └─ Set permanent lockout
```

**Deliverable:** Full admin control over service

---

## 7. Integration Requirements

### 7.1 SDK Integration

**CLI needs SDK access for:**
- Emergency stop (close all positions)
- Real-time position queries (trader status)
- Current P&L (if not using database)

**Problem:** CLI is separate process from Risk Manager service

**Solution Options:**

**Option A: CLI connects to SDK directly**
```python
# cli/admin/emergency.py

from risk_manager.sdk import TradingSuite

async def emergency_stop():
    # CLI creates its own SDK connection
    suite = await TradingSuite.create(instruments=["MNQ", "ES"])
    await suite.close_position()
```
- Pros: Direct control, no service needed
- Cons: Requires API credentials in CLI, duplicate connections

**Option B: CLI sends command to service**
```python
# cli/admin/emergency.py

async def emergency_stop():
    # CLI tells service to execute emergency stop
    service_client.send_command("emergency_stop")
```
- Pros: Single SDK connection, secure
- Cons: Requires IPC, service must implement command handler

**Recommendation:** Option A for MVP (simpler), Option B for production

---

### 7.2 State Management Integration

**CLI accesses state via:**

```
CLI → Database (Direct) ← Risk Manager Service

OR

CLI → Service API → State Managers → Database
```

**Recommendation:** Direct database access for read-only queries, service API for mutations

---

### 7.3 Configuration Management

**Config update flow:**

```
1. Admin edits config via CLI
2. CLI validates YAML
3. CLI saves to config/risk_config.yaml
4. CLI notifies service (file watch or IPC)
5. Service reloads config
6. Service applies new rules
```

**File Watch Implementation:**
```python
# src/risk_manager/core/manager.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("risk_config.yaml"):
            logger.info("Config file changed, reloading...")
            self.reload_config()

# Start watching
observer = Observer()
observer.schedule(ConfigWatcher(), path="config/", recursive=False)
observer.start()
```

**Estimated Effort:** 1 day

---

## 8. CLI Framework Choice

### 8.1 Framework Decision

**Typer** ✅ (already in dependencies)

**Why Typer?**
- Modern Python CLI framework (by creator of FastAPI)
- Type hints for auto-completion and validation
- Beautiful help messages (auto-generated)
- Integrates with Rich for beautiful output
- Supports sub-commands (admin/trader separation)

**Example:**
```python
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def status():
    """View current risk status."""
    console.print("Status: ACTIVE", style="green")

if __name__ == "__main__":
    app()
```

---

### 8.2 CLI Structure

```python
# cli/__init__.py

import typer
from .admin import admin_app
from .trader import trader_app

app = typer.Typer()

app.add_typer(admin_app.app, name="admin", help="Admin commands (requires elevation)")
app.add_typer(trader_app.app, name="trader", help="Trader commands (view-only)")

# Usage:
# risk-manager admin status
# risk-manager trader status
```

---

### 8.3 Output Formatting

**Rich** ✅ (already in dependencies)

**Features:**
- Tables
- Panels
- Progress bars
- Live updating displays
- Syntax highlighting
- Colors and styles

**Example:**
```python
from rich.table import Table
from rich.console import Console

console = Console()

table = Table(title="Risk Rules")
table.add_column("Rule", style="cyan")
table.add_column("Status", style="green")
table.add_row("Max Contracts", "✅ Enabled")
table.add_row("Daily Loss", "⚠️  90% utilized")

console.print(table)
```

---

## 9. Effort Estimates

### 9.1 Detailed Breakdown

| Component | Effort | Prerequisites |
|-----------|--------|---------------|
| **Foundation** |  |  |
| CLI framework setup | 2 days | None |
| Windows UAC auth module | 1 day | None |
| **Admin CLI** |  |  |
| config command | 3 days | Config loader complete |
| unlock command | 2 days | LockoutManager exists |
| service command | 2 days | Windows Service exists |
| logs command | 1 day | None |
| status command | 2 days | All state managers exist |
| emergency command | 2 days | SDK integration |
| **Trader CLI** |  |  |
| status command | 2 days | PnLTracker, LockoutManager |
| pnl command | 2 days | PnLTracker |
| rules command | 1 day | Config loader |
| lockouts command | 1 day | LockoutManager |
| history command | 1 day | ViolationLogger |
| limits command | 1 day | All state managers |
| logs command | 1 day | None |
| **Integration** |  |  |
| Service communication | 2 days | Windows Service |
| Config hot reload | 1 day | File watching |
| Live TUI updates | 2 days | Rich Live |

**Total:** 30 days (6 weeks) for one developer

**With Prerequisites Built First:** Add 6 days (LockoutManager, TimerManager, ViolationLogger)

**Grand Total:** 36 days (~7 weeks)

---

### 9.2 Critical Path

```
Week 1: State Managers (Wave 2 prerequisite)
  ├─ LockoutManager (2 days)
  ├─ TimerManager (2 days)
  └─ ViolationLogger (1 day)

Week 2: CLI Foundation + Trader Status
  ├─ CLI framework (2 days)
  ├─ UAC auth (1 day)
  ├─ Trader status (2 days)
  └─ Trader logs (1 day)

Week 3: Admin Core
  ├─ Config command (3 days)
  ├─ Unlock command (2 days)
  └─ Admin logs (1 day)

Week 4: Admin Service Control
  ├─ Windows Service wrapper (2 days)
  ├─ Service command (2 days)
  └─ Emergency command (2 days)

Week 5: Trader CLI Complete
  ├─ P&L command (2 days)
  ├─ Rules command (1 day)
  ├─ Lockouts command (1 day)
  └─ History command (1 day)

Week 6: Polish & Integration
  ├─ Limits command (1 day)
  ├─ Live TUI (2 days)
  ├─ Config hot reload (1 day)
  └─ Testing & bug fixes (2 days)
```

---

### 9.3 MVP Timeline (Minimum Viable Product)

**Goal:** Basic trader status + admin unlock (no service control)

```
Week 1: Foundation + Trader Status
  └─ CLI framework, UAC, trader status, trader logs

Week 2: Admin Unlock + Config
  └─ Admin config, admin unlock, admin logs

Total: 2 weeks (10 days)
```

**MVP Deliverable:** Trader can view status, admin can unlock accounts and edit configs

---

## 10. Risks & Challenges

### 10.1 Technical Risks

1. **Windows Service Communication** (HIGH)
   - No IPC implemented yet
   - Multiple options (pipes, sockets, HTTP)
   - Risk: Complex, easy to get wrong

2. **State Manager Dependencies** (CRITICAL)
   - CLI can't work without LockoutManager, TimerManager
   - Risk: Blocked until Wave 2 state managers complete

3. **Live TUI Performance** (MEDIUM)
   - Refresh every 5 seconds requires efficient queries
   - Risk: Slow database queries → laggy UI

4. **Config Hot Reload** (MEDIUM)
   - File watching + service notification
   - Risk: Race conditions, partial updates

5. **Cross-Platform Compatibility** (LOW)
   - Windows Service commands won't work on Linux/Mac
   - Risk: Need conditional logic

---

### 10.2 User Experience Risks

1. **Trader Confusion** (MEDIUM)
   - Two CLIs (admin vs trader) might confuse users
   - Risk: Trader tries admin commands, gets access denied

2. **Admin Complexity** (MEDIUM)
   - Many commands, many options
   - Risk: Steep learning curve

3. **Error Messages** (LOW)
   - Need clear, actionable error messages
   - Risk: User doesn't understand what went wrong

---

### 10.3 Security Risks

1. **Insufficient UAC Check** (HIGH)
   - If `require_admin()` is bypassed somehow
   - Risk: Trader gains admin access
   - Mitigation: File ACL permissions (defense in depth)

2. **Database Corruption** (MEDIUM)
   - CLI writing to database while service reads
   - Risk: Race conditions, data loss
   - Mitigation: Use WAL mode, transactions

3. **Config Injection** (LOW)
   - Malicious YAML in config files
   - Risk: Code execution via YAML deserialization
   - Mitigation: Use `yaml.safe_load()`, validate all inputs

---

## 11. Summary & Recommendations

### 11.1 Current Status

**CLI System: 0% Complete**
- Directory doesn't exist
- Entry point declared but broken
- Framework chosen (Typer + Rich)
- Dependencies declared

---

### 11.2 Critical Path

```
1. Build State Managers FIRST (Wave 2 priority)
   └─ LockoutManager, TimerManager, ViolationLogger

2. Build CLI Foundation
   └─ Directory structure, auth, entry point

3. Build MVP CLI
   └─ Trader status, admin unlock

4. Build Full CLI
   └─ All 13 commands

5. Add Service Control
   └─ Windows Service integration
```

---

### 11.3 Recommendations

**Priority 1: State Managers (CRITICAL)**
- CLI is blocked until LockoutManager and TimerManager exist
- Estimated: 6 days
- **Do this first in Wave 2**

**Priority 2: CLI Foundation (HIGH)**
- Basic structure, UAC, entry point
- Estimated: 3 days
- **Do this second**

**Priority 3: MVP CLI (HIGH)**
- Trader status + admin unlock
- Estimated: 7 days
- **Do this third - delivers value quickly**

**Priority 4: Full CLI (MEDIUM)**
- All 13 commands
- Estimated: 20 days
- **Do this over multiple sprints**

**Priority 5: Service Control (LOW)**
- Windows Service integration
- Estimated: 3 days
- **Can defer until production deployment**

---

### 11.4 Minimum Viable CLI

**MVP Definition:**
- ✅ Trader can view status (P&L, positions, lockouts)
- ✅ Trader can view logs
- ✅ Admin can unlock accounts (emergency override)
- ✅ Admin can view/edit config
- ✅ Admin can view logs
- ❌ No service control (manual start/stop)
- ❌ No advanced features (live TUI, history, stats)

**MVP Effort:** 2 weeks (10 days)

**MVP Deliverable:** Functional CLI for basic operations

---

## 12. Next Steps

1. **Complete Wave 2 state managers** (LockoutManager, TimerManager)
2. **Create CLI directory structure**
3. **Implement authentication module** (Windows UAC)
4. **Build MVP CLI** (trader status + admin unlock)
5. **Test on Windows** (UAC, file permissions, service)
6. **Iterate based on user feedback**
7. **Add remaining commands incrementally**

---

**Analysis Complete**
**Date:** 2025-10-25
**Total Features Documented:** 13 CLI commands
**Implementation Status:** 0% (100% gap)
**Recommended Timeline:** 6-7 weeks for full implementation
**Recommended MVP:** 2 weeks for basic functionality

---

## Appendix A: Command Reference

### Admin CLI Commands

```bash
# Configuration
risk-manager admin config list
risk-manager admin config set daily_realized_loss limit -600
risk-manager admin config enable max_contracts
risk-manager admin config disable symbol_blocks

# Unlock
risk-manager admin unlock list
risk-manager admin unlock remove ACCOUNT-001
risk-manager admin unlock remove-all

# Service Control
risk-manager admin service start
risk-manager admin service stop
risk-manager admin service restart
risk-manager admin service status

# Logs
risk-manager admin logs tail 100
risk-manager admin logs stream
risk-manager admin logs filter --level ERROR

# Status
risk-manager admin status
risk-manager admin status health

# Emergency
risk-manager admin emergency stop
```

### Trader CLI Commands

```bash
# Status
risk-manager trader status
risk-manager trader status --live  # Live updating

# P&L
risk-manager trader pnl today
risk-manager trader pnl history --days 7
risk-manager trader pnl by-instrument
risk-manager trader pnl stats

# Rules
risk-manager trader rules list

# Lockouts
risk-manager trader lockouts show
risk-manager trader lockouts history --days 7

# History
risk-manager trader history show --limit 10
risk-manager trader history filter --rule daily_realized_loss

# Limits
risk-manager trader limits show

# Logs
risk-manager trader logs tail 50
risk-manager trader logs filter --level WARNING
```

---

**End of Report**
