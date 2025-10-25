# Security & Configuration Feature Inventory

**Analysis Date**: 2025-10-25
**Researcher**: RESEARCHER 5 - Security & Configuration Specialist
**Project**: Risk Manager V34
**Working Directory**: /mnt/c/Users/jakers/Desktop/risk-manager-v34

---

## Executive Summary

Risk Manager V34 implements a **Windows UAC-based security model** (no custom passwords) with comprehensive configuration management supporting 13 risk rules across multiple trading instruments. The system features account-wide risk tracking, 8-checkpoint SDK logging, and multi-layer OS-level protection.

**Key Architecture**:
- Windows UAC for admin protection (zero custom credentials)
- YAML-based configuration with Pydantic validation
- SQLite persistence for multi-account P&L tracking
- Account-wide risk aggregation across all instruments
- JSON-structured SDK logging with 8 strategic checkpoints

---

## Table of Contents

1. [Security Model](#1-security-model)
2. [Configuration System](#2-configuration-system)
3. [Multi-Symbol/Account-Wide Support](#3-multi-symbolaccount-wide-support)
4. [Logging Infrastructure](#4-logging-infrastructure)
5. [State Persistence](#5-state-persistence)
6. [Security Requirements & Best Practices](#6-security-requirements--best-practices)
7. [Implementation Checklist](#7-implementation-checklist)

---

## 1. Security Model

### 1.1 Core Principle

**Windows UAC-Based Protection - NO Custom Passwords**

The system uses Windows operating system security (User Account Control) to protect traders from bypassing risk rules. There are **NO custom passwords**, **NO stored credentials**, and **NO authentication database**. Only Windows admin rights control access.

**Design Goal**: Make the system "virtually unkillable" by the trader without Windows admin password.

---

### 1.2 Two Access Levels

#### Admin CLI (Elevated Terminal)

**Access Method**:
1. Right-click PowerShell/Terminal → "Run as Administrator"
2. Windows UAC prompt appears
3. Enter Windows admin password
4. Terminal opens with elevated rights
5. Run `risk-manager admin`

**Capabilities**:
- ✅ Configure risk rules
- ✅ Manual unlock (emergency override)
- ✅ Start/stop service
- ✅ Edit configuration files
- ✅ Backup/restore state database
- ✅ View all logs
- ✅ Modify Windows Service settings

**Implementation Location**: `src/cli/admin/`

---

#### Trader CLI (Normal Terminal)

**Access Method**:
1. Open normal PowerShell/Terminal (no elevation)
2. Run `risk-manager trader`

**Capabilities (View-Only)**:
- ✅ View current P&L (daily realized, daily unrealized)
- ✅ View positions (all instruments)
- ✅ View rule status (enabled/disabled, thresholds)
- ✅ View lockout timers (countdown to reset)
- ✅ Monitor enforcement logs (read-only)
- ✅ View system status (service running, SDK connected)

**Restrictions**:
- ❌ Cannot change any settings
- ❌ Cannot unlock account
- ❌ Cannot stop service
- ❌ Cannot edit rules
- ❌ Cannot delete logs or state database

**Implementation Location**: `src/cli/trader/`

---

### 1.3 Protection Layers

#### Layer 1: Windows Service Protection

**Configuration**:
```python
# src/service/windows_service.py

class RiskManagerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "RiskManagerV34"
    _svc_display_name_ = "Risk Manager V34"
    _svc_description_ = "Trading risk management protection service"

    # Service account: LocalSystem (highest privilege)
    _svc_account_ = None  # None = LocalSystem

    # Startup: Automatic (starts on boot)
    _svc_start_type_ = win32service.SERVICE_AUTO_START
```

**Protection**:
- Runs as LocalSystem (highest Windows privilege)
- Cannot be stopped by normal users
- Auto-starts on boot
- Protected by Windows Service Control Manager
- Task Manager blocks termination attempts

**Trader Cannot**:
- Kill service via Task Manager → "Access Denied"
- Stop via command line → "Administrator privileges required"
- Stop via Services GUI → UAC prompt appears

---

#### Layer 2: File System ACL (Access Control Lists)

**Directories Protected**:
```
C:\ProgramData\RiskManager\
├── config\          # Configuration files (YAML)
├── data\            # State database (SQLite)
└── logs\            # Log files
```

**Permissions**:
- **SYSTEM account**: Full Control
- **Administrators group**: Full Control
- **Users group**: Read Only

**Implementation**:
```python
# scripts/install_service.py

def set_secure_permissions(directory_path: str):
    """Set Windows ACL permissions."""

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
```

**Trader Cannot**:
- Edit `risk_config.yaml` → "Access Denied" when saving
- Delete `state.db` → "Administrator permission required"
- Modify log files → Read-only access

---

#### Layer 3: UAC Elevation Requirement

**Admin CLI Enforcement**:
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

**Usage**:
```python
# src/cli/admin/admin_main.py

def main():
    """Admin CLI entry point."""

    # FIRST THING: Check elevation
    require_admin()  # Exits immediately if not elevated

    # Only reaches here if user has admin rights
    display_admin_menu()
```

**Trader Cannot**:
- Run `risk-manager admin` → Script exits with error message
- Bypass check → Embedded in code, cannot be circumvented

---

#### Layer 4: Process Protection

**Windows Process Controls**:
- Service process runs under SYSTEM account
- Normal users cannot terminate SYSTEM processes
- Task Manager blocks "End Task" for protected services
- Command-line kill commands (`taskkill`, `Stop-Process`) blocked by Windows

**Example Attempts**:
```powershell
# Trader attempts via Task Manager
Task Manager → Find "Risk Manager V34" → End Task
# Result: ❌ Access Denied - Administrator privileges required

# Trader attempts via PowerShell
PS> taskkill /F /IM risk-manager.exe
# Result: ERROR: Access Denied. Administrator privileges required.

# Trader attempts via PowerShell (elevated command)
PS> Stop-Service RiskManagerV34
# Result: UAC Prompt appears → No password → BLOCKED
```

---

### 1.4 Security Workflow Examples

#### Scenario 1: Trader Hits Daily Loss Limit

```
Trader loses $500 → Daily loss limit hit → Account locked

Trader Attempts to Bypass:
├─ Attempt 1: Task Manager → "End Task"
│  └─ Result: ❌ "Access Denied - Administrator privileges required"
│
├─ Attempt 2: PowerShell → taskkill /F /IM risk-manager.exe
│  └─ Result: ❌ "Access Denied. You do not have permission."
│
├─ Attempt 3: Services → Stop "Risk Manager V34"
│  └─ Result: 🔒 UAC Prompt appears → No password → Cannot proceed
│
├─ Attempt 4: Edit config → Change limit to -10000
│  └─ Result: ❌ "Access Denied. You need administrator permission."
│
└─ Attempt 5: Delete state.db (contains lockout info)
   └─ Result: ❌ "Access Denied. Administrator permission required."

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

---

#### Scenario 2: Admin Overrides Lockout

```
Admin Process:

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

### 1.5 Why Windows UAC is Superior

| Custom Password System | Windows UAC |
|------------------------|-------------|
| ❌ Password stored in code/file | ✅ No password storage needed |
| ❌ Can be forgotten | ✅ Just Windows admin password |
| ❌ Can be extracted from binary | ✅ OS-level security |
| ❌ Need reset mechanism | ✅ Windows handles password resets |
| ❌ Custom authentication code | ✅ OS handles authentication |
| ❌ Vulnerable to bypass | ✅ Cannot bypass Windows kernel |
| ❌ Not industry standard | ✅ How all Windows services work |

**Benefits**:
1. **No Password Management**: No custom password to store, hash, or forget
2. **OS-Level Security**: Protected by Windows kernel, not application code
3. **Industry Standard**: How all professional Windows services work
4. **User Familiarity**: Users understand "Run as Administrator"
5. **Impossible to Bypass**: Would require compromising Windows itself
6. **Centralized Control**: Windows admin controls everything
7. **Audit Trail**: Windows logs all UAC prompts and admin actions

---

## 2. Configuration System

### 2.1 Configuration Architecture

**File Locations**:
```
config/
├── accounts.yaml           # API credentials (TopstepX)
├── risk_config.yaml        # Risk rule settings (13 rules)
└── holidays.yaml           # Market holidays (for session blocks)
```

**Configuration Loading**:
```python
# src/risk_manager/core/config.py

from pydantic import Field
from pydantic_settings import BaseSettings

class RiskConfig(BaseSettings):
    """Risk Manager configuration with Pydantic validation."""

    # ProjectX API
    project_x_api_key: str = Field(..., validation_alias="PROJECT_X_API_KEY")
    project_x_username: str = Field(..., validation_alias="PROJECT_X_USERNAME")
    project_x_api_url: str = Field(
        default="https://api.topstepx.com/api",
        validation_alias="PROJECT_X_API_URL"
    )
    project_x_websocket_url: str = Field(
        default="wss://api.topstepx.com",
        validation_alias="PROJECT_X_WEBSOCKET_URL"
    )

    # Risk Settings
    max_daily_loss: float = -1000.0
    max_contracts: int = 5
    require_stop_loss: bool = True
    stop_loss_grace_seconds: int = 60

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None

    # Performance
    enforcement_latency_target_ms: int = 500
    max_events_per_second: int = 1000

    # AI Features (optional)
    anthropic_api_key: str | None = Field(default=None)
    enable_ai: bool = False
    enable_pattern_recognition: bool = False
    enable_anomaly_detection: bool = False

    # Notifications (optional)
    discord_webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    @classmethod
    def from_file(cls, config_file: str | Path) -> "RiskConfig":
        """Load configuration from YAML file."""
        import yaml

        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)
```

---

### 2.2 YAML Configuration Formats

#### 2.2.1 Complete Risk Config (risk_config.yaml)

**Structure**:
```yaml
# ==============================================================================
# RISK MANAGER V34 - CONFIGURATION
# ==============================================================================

# ==============================================================================
# GENERAL SETTINGS
# ==============================================================================
general:
  # Instruments to monitor
  instruments:
    - MNQ
    - ES
    - GC
    - NQ

  # Timezone
  timezone: "America/New_York"

  # Logging
  logging:
    level: "INFO"             # DEBUG, INFO, WARNING, ERROR
    log_to_file: true
    log_directory: "logs/"

  # Database
  database:
    path: "data/risk_state.db"
    backup_enabled: true
    backup_interval_hours: 24

# ==============================================================================
# CATEGORY 1: TRADE-BY-TRADE RULES
# (Close only that position, no lockout)
# ==============================================================================

# RULE-001: MAX CONTRACTS
max_contracts:
  enabled: true
  limit: 5                    # Max net contracts (all instruments combined)
  count_type: "net"           # "net" or "gross"
  close_all: false            # Trade-by-trade
  close_position: true

# RULE-002: MAX CONTRACTS PER INSTRUMENT
max_contracts_per_instrument:
  enabled: true
  default_limit: 3
  instrument_limits:
    MNQ: 2
    ES: 1
  close_all: false
  close_position: true

# RULE-004: DAILY UNREALIZED LOSS
daily_unrealized_loss:
  enabled: true
  limit: -200.0               # Max floating loss per position ($)
  check_interval_seconds: 10
  close_all: false
  close_position: true

# RULE-005: MAX UNREALIZED PROFIT (Profit Target)
max_unrealized_profit:
  enabled: true
  target: 500.0               # Take profit at $500 per position
  check_interval_seconds: 5
  close_all: false
  close_position: true

# RULE-008: STOP-LOSS ENFORCEMENT
no_stop_loss_grace:
  enabled: true
  require_within_seconds: 60
  grace_period_seconds: 300
  close_all: false
  close_position: true

# RULE-011: SYMBOL BLOCKS (Blacklist)
symbol_blocks:
  enabled: false
  blocked_symbols:
    # - ES
    # - NQ
  close_all: false
  close_position: true
  close_immediately: true

# ==============================================================================
# CATEGORY 2: TIMER/COOLDOWN RULES
# (Close all + temporary lockout with countdown)
# ==============================================================================

# RULE-006: TRADE FREQUENCY LIMIT
trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3
    per_hour: 10
    per_session: 50
  cooldowns:
    per_minute_breach: 60       # 1 minute
    per_hour_breach: 1800       # 30 minutes
    per_session_breach: 3600    # 1 hour
  close_all: true
  cancel_orders: true
  lockout_type: "timer"

# RULE-007: COOLDOWN AFTER LOSS
cooldown_after_loss:
  enabled: true
  loss_threshold: -100.0
  cooldown_minutes: 15
  close_all: true
  cancel_orders: true
  lockout_type: "timer"

# ==============================================================================
# CATEGORY 3: HARD LOCKOUT RULES
# (Close all + lockout until reset/condition)
# ==============================================================================

# RULE-003: DAILY REALIZED LOSS
daily_realized_loss:
  enabled: true
  limit: -500.0
  reset_time: "17:00"         # 5:00 PM EST
  timezone: "America/New_York"
  close_all: true
  cancel_orders: true
  lockout_type: "hard"
  lockout_until_reset: true

# RULE-013: DAILY REALIZED PROFIT
daily_realized_profit:
  enabled: true
  target: 1000.0
  reset_time: "17:00"
  timezone: "America/New_York"
  close_all: true
  cancel_orders: true
  lockout_type: "hard"
  lockout_until_reset: true
  message: "Daily profit target reached! Good job! See you tomorrow."

# RULE-009: SESSION BLOCK OUTSIDE
session_block_outside:
  enabled: true
  session_hours:
    start: "09:30"
    end: "16:00"
  allowed_days: [0, 1, 2, 3, 4]  # Monday-Friday
  respect_holidays: true
  close_all: true
  cancel_orders: true
  lockout_type: "hard"
  lockout_until_session_start: true

# RULE-010: AUTH LOSS GUARD
auth_loss_guard:
  enabled: true
  check_interval_seconds: 30
  close_all: true
  cancel_orders: true
  lockout_type: "hard"
  lockout_permanently: true
  reason: "API canTrade status is false - account disabled"

# ==============================================================================
# CATEGORY 4: AUTOMATION (Optional)
# ==============================================================================

# RULE-012: TRADE MANAGEMENT
trade_management:
  enabled: false              # Advanced feature
  auto_breakeven:
    enabled: true
    profit_threshold_ticks: 4
    offset_ticks: 1
  trailing_stop:
    enabled: true
    trail_ticks: 4
    activation_profit_ticks: 8
```

---

#### 2.2.2 Account Configuration (accounts.yaml)

```yaml
# ==============================================================================
# ACCOUNT CONFIGURATION
# ==============================================================================
# ⚠️  KEEP THIS FILE SECURE - Contains API credentials
# ==============================================================================

# TopstepX API Credentials
topstepx:
  username: "jakertrader"
  api_key: "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
  api_url: "https://api.topstepx.com/api"
  websocket_url: "wss://api.topstepx.com"

# Account to Monitor
monitored_account:
  account_id: "PRAC-V2-126244-84184528"
  account_type: "practice"    # "practice" or "live"
  description: "Jake's Practice Account"
```

---

#### 2.2.3 Holidays Configuration (holidays.yaml)

```yaml
# ==============================================================================
# MARKET HOLIDAYS
# ==============================================================================
# Used by RULE-009: Session Block Outside
# ==============================================================================

holidays:
  2025:
    - "2025-01-01"  # New Year's Day
    - "2025-01-20"  # Martin Luther King Jr. Day
    - "2025-02-17"  # Presidents' Day
    - "2025-04-18"  # Good Friday
    - "2025-05-26"  # Memorial Day
    - "2025-07-04"  # Independence Day
    - "2025-09-01"  # Labor Day
    - "2025-11-27"  # Thanksgiving
    - "2025-12-25"  # Christmas
```

---

### 2.3 Configuration Profiles by Scenario

#### Conservative Trader (Strict Limits)

```yaml
max_contracts:
  enabled: true
  limit: 2                    # Very conservative

daily_realized_loss:
  enabled: true
  limit: -200.0               # Small loss limit

daily_realized_profit:
  enabled: true
  target: 400.0               # Take smaller profits

trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 2
    per_hour: 5
    per_session: 20
```

---

#### Aggressive Trader (Loose Limits)

```yaml
max_contracts:
  enabled: true
  limit: 10

daily_realized_loss:
  enabled: true
  limit: -1000.0

daily_realized_profit:
  enabled: true
  target: 2000.0

trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 5
    per_hour: 20
    per_session: 100
```

---

#### Evaluation Account (TopstepX Rules)

```yaml
max_contracts:
  enabled: true
  limit: 5

daily_realized_loss:
  enabled: true
  limit: -500.0

daily_unrealized_loss:
  enabled: true
  limit: -150.0

max_contracts_per_instrument:
  enabled: true
  instrument_limits:
    MNQ: 2
    ES: 1

session_block_outside:
  enabled: true
  session_hours:
    start: "09:30"
    end: "16:00"
```

---

### 2.4 Configuration Validation

**Required Fields by Rule Category**:

**Trade-by-Trade**:
```yaml
rule_name:
  enabled: true/false
  limit: <number>             # Threshold value
  close_position: true        # Must be true
  close_all: false            # Must be false
```

**Timer/Cooldown**:
```yaml
rule_name:
  enabled: true/false
  threshold: <number>
  cooldown_seconds: <number>
  close_all: true             # Must be true
  lockout_type: "timer"
```

**Hard Lockout**:
```yaml
rule_name:
  enabled: true/false
  limit: <number>
  reset_time: "HH:MM"
  close_all: true             # Must be true
  lockout_type: "hard"
```

---

## 3. Multi-Symbol/Account-Wide Support

### 3.1 Architecture Overview

**YES - Risk Manager V34 supports ANY symbol/contract type (MNQ, ES, GC, NQ, MGC, etc.)**

**Risk rules apply to your ENTIRE ACCOUNT, not per-symbol.**

---

### 3.2 SDK Integration Approach

**Recommended: Single TradingSuite with Multiple Instruments**

```python
# Create ONE TradingSuite with multiple instruments
suite = await TradingSuite.create(
    instruments=["MNQ", "ES", "GC", "NQ"]  # All instruments you trade
)

# Access individual instrument data
mnq = suite['MNQ']
es = suite['ES']
gc = suite['GC']

# Events from ALL instruments come through suite.event_bus
suite.event_bus.subscribe(EventType.POSITION_UPDATED, callback)
# ↑ Receives position updates for MNQ, ES, GC, NQ, etc.
```

**Key Point**: You get **account-wide events** regardless of which symbol you're trading. The SDK's SignalR connection receives ALL position/trade/order updates for your account.

---

### 3.3 Risk Rules Scope

#### Account-Wide Rules (Aggregate ALL Symbols)

**RULE-001: Max Contracts (Account Total)**
```yaml
max_contracts:
  enabled: true
  limit: 5  # Max 5 contracts across ALL instruments combined
  count_type: "net"  # Net position (long - short)
```

**Example**:
```
Trader has:
- MNQ: 2 long
- ES: 2 long
- GC: 1 long
Total: 5 contracts ✅ At limit

Trader places order for 1 more ES → BLOCKED (would exceed 5)
```

**Implementation**:
```python
def calculate_total_contracts(self):
    total = 0
    for symbol, suite in self.suites.items():
        positions = suite.get_positions()
        total += abs(positions.net_quantity)  # Sum all symbols
    return total
```

---

**RULE-003: Daily Realized Loss (Account Total)**
```yaml
daily_realized_loss:
  enabled: true
  limit: -500.0  # Max $500 loss per day across ALL instruments
```

**Example**:
```
Today's trades:
- MNQ: -$200 realized
- ES: -$150 realized
- GC: -$180 realized
Total: -$530 → BREACH! Lock account until 5 PM
```

**Implementation**:
```python
async def track_trade(self, trade_event):
    # Trade could be from ANY symbol
    pnl = trade_event.data['realized_pnl']

    # Add to daily total (account-wide)
    self.daily_realized_pnl += pnl

    # Check against account limit
    if self.daily_realized_pnl <= -500.0:
        await self.flatten_all_instruments()  # Close ALL positions
        self.lockout_manager.set_lockout()     # Lock entire account
```

---

**RULE-006: Trade Frequency (Account Total)**
```yaml
trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3  # Max 3 trades per minute across ALL symbols
```

**Example**:
```
Within 1 minute:
- MNQ: 1 trade
- ES: 1 trade
- GC: 1 trade
Total: 3 trades → At limit

4th trade (any symbol) → BLOCKED
```

---

#### Per-Instrument Rules (Symbol-Specific)

**RULE-002: Max Contracts Per Instrument**
```yaml
max_contracts_per_instrument:
  enabled: true
  instrument_limits:
    MNQ: 2  # Max 2 MNQ contracts
    ES: 1   # Max 1 ES contract
    GC: 3   # Max 3 GC contracts
```

**Example**:
```
Trader has:
- MNQ: 2 long ✅ (at limit for MNQ)
- ES: 1 long ✅ (at limit for ES)
- GC: 0 ✅ (can trade up to 3)

Trader places order for 1 more MNQ → BLOCKED (MNQ limit)
Trader places order for 1 GC → ALLOWED (under GC limit)
```

---

**RULE-004: Daily Unrealized Loss (Per Position)**
```yaml
daily_unrealized_loss:
  enabled: true
  limit: -200.0  # Max floating loss per position
```

**Example**:
```
Trader has:
- MNQ: 2 contracts, P&L: -$150 ✅
- ES: 1 contract, P&L: -$220 ❌ (exceeds -$200)
- GC: 1 contract, P&L: +$50 ✅

Action: Close ES position ONLY (not MNQ or GC)
```

---

### 3.4 Event Flow Across Symbols

```
TopstepX API (SignalR)
     │
     ├─ Position Update: MNQ (2 long @ 20,125)
     ├─ Trade Executed: ES (1 short @ 5,950, P&L: -$50)
     ├─ Position Update: GC (1 long @ 2,030)
     ├─ Order Placed: NQ (2 long limit @ 21,000)
     │
     ▼
TradingSuite.event_bus
     │
     ▼
EventBridge (Our Code)
     │
     ├─ Convert to RiskEvent (with symbol)
     ├─ Add to Risk EventBus
     │
     ▼
RiskEngine
     │
     ├─ Evaluate all 13 rules
     ├─ Aggregate account-wide metrics
     ├─ Check per-symbol limits
     │
     ▼
Enforcement Actions (if breach)
```

**Key Insight**: The SDK receives **ALL account activity** via SignalR, regardless of which instruments you specified. The `instruments` parameter tells the SDK which instruments to track market data for, but you get account-wide position/trade/order events automatically.

---

### 3.5 Configuration: Adding New Symbols

**Method 1: Static Configuration (risk_config.yaml)**

```yaml
general:
  instruments:
    - MNQ   # E-mini NASDAQ
    - ES    # E-mini S&P 500
    - GC    # Gold futures
    - NQ    # NASDAQ-100
    - MGC   # Micro Gold
    # Add any symbol you trade
```

**On startup**:
```python
# Load config
config = yaml.safe_load(open('config/risk_config.yaml'))
instruments = config['general']['instruments']

# Create TradingSuite with all instruments
suite = await TradingSuite.create(instruments=instruments)
```

---

**Method 2: Dynamic Addition (While Running)**

**Admin CLI**:
```bash
$ risk-manager-admin

> add-instrument NQ
✅ Added NQ to monitored instruments
✅ Risk rules now apply to NQ
```

**Code**:
```python
# Add instrument dynamically
await suite_manager.add_instrument('NQ')

# Start bridging events
await event_bridge.add_instrument('NQ', suite['NQ'])
```

---

### 3.6 Summary: Multi-Symbol Support

**Supported Instruments**: MNQ, ES, GC, NQ, MGC, RTY, CL, etc. (ANY symbol)

**Account-Wide Rules** (aggregate all symbols):
- RULE-001: Max Contracts
- RULE-003: Daily Realized Loss
- RULE-006: Trade Frequency
- RULE-007: Cooldown After Loss
- RULE-009: Session Restrictions
- RULE-010: Auth Loss Guard
- RULE-013: Daily Realized Profit

**Per-Instrument Rules** (symbol-specific):
- RULE-002: Max Contracts Per Instrument
- RULE-004: Daily Unrealized Loss (per position)
- RULE-005: Max Unrealized Profit (per position)
- RULE-008: Stop-Loss Enforcement (per position)
- RULE-011: Symbol Blocks (blacklist)

**Result**: Risk Manager protects your ENTIRE ACCOUNT regardless of which symbol you trade.

---

## 4. Logging Infrastructure

### 4.1 8-Checkpoint Logging System

**Strategic Checkpoints for Runtime Debugging**:

```
Checkpoint 1: 🚀 Service Start
  └─ Log: "Risk Manager starting..."
  └─ Where: manager.py:44

Checkpoint 2: ✅ Config Loaded
  └─ Log: "Config loaded: X custom rules, monitoring Y instruments"
  └─ Where: manager.py:109

Checkpoint 3: ✅ SDK Connected
  └─ Log: "SDK connected: X instrument(s) - [MNQ, ES, ...]"
  └─ Where: manager.py:138

Checkpoint 4: ✅ Rules Initialized
  └─ Log: "Rules initialized: X rules - [DailyLossRule($-500), ...]"
  └─ Where: manager.py:184

Checkpoint 5: ✅ Event Loop Running
  └─ Log: "Event loop running: X active rules monitoring events"
  └─ Where: engine.py:38

Checkpoint 6: 📨 Event Received
  └─ Log: "Event received: EVENT_TYPE - evaluating X rules"
  └─ Where: engine.py:68

Checkpoint 7: 🔍 Rule Evaluated
  └─ Log: "Rule evaluated: RuleName - [VIOLATED|PASSED]"
  └─ Where: engine.py:75

Checkpoint 8: ⚠️ Enforcement Triggered
  └─ Log: "Enforcement triggered: ACTION - Rule: XYZ"
  └─ Where: enforcement.py:56/132/220/325
```

---

### 4.2 Application Startup Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Risk Manager V34 Startup                      │
└─────────────────────────────────────────────────────────────────┘

1. RiskManager.__init__()
   │
   ├─→ 🚀 Risk Manager starting...
   │   └─→ [manager.py:44] sdk_logger.info()

2. RiskManager.create()
   │
   ├─→ ✅ Config loaded: X custom rules, monitoring Y instruments
   │   └─→ [manager.py:109] sdk_logger.info()

3. _init_trading_integration()
   │
   ├─→ ✅ SDK connected: X instrument(s) - [MNQ, ES, ...]
   │   └─→ [manager.py:138] sdk_logger.info()

4. _add_default_rules()
   │
   ├─→ ✅ Rules initialized: X rules - [DailyLossRule($-500), ...]
   │   └─→ [manager.py:184] sdk_logger.info()

5. RiskEngine.start()
   │
   └─→ ✅ Event loop running: X active rules monitoring events
       └─→ [engine.py:38] sdk_logger.info()
```

---

### 4.3 Runtime Event Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Event Processing Cycle                         │
└─────────────────────────────────────────────────────────────────┘

Event Occurs (Order Fill, Position Update, etc.)
   │
   ├─→ 📨 Event received: EVENT_TYPE - evaluating X rules
   │   └─→ [engine.py:68] sdk_logger.info()
   │
   ├─→ For each rule:
   │   │
   │   ├─→ 🔍 Rule evaluated: RuleName - [VIOLATED|PASSED]
   │   │   └─→ [engine.py:75] sdk_logger.info()
   │   │
   │   └─→ If VIOLATED:
   │       │
   │       └─→ _handle_violation()
   │           │
   │           ├─→ action == "flatten"
   │           │   └─→ ⚠️ Enforcement triggered: FLATTEN ALL - Rule: XYZ
   │           │       └─→ [engine.py:101] sdk_logger.warning()
   │           │
   │           ├─→ action == "pause"
   │           │   └─→ ⚠️ Enforcement triggered: PAUSE TRADING - Rule: XYZ
   │           │       └─→ [engine.py:105] sdk_logger.warning()
   │           │
   │           └─→ action == "alert"
   │               └─→ ⚠️ Enforcement triggered: ALERT - Rule: XYZ
   │                   └─→ [engine.py:109] sdk_logger.info()
```

---

### 4.4 Enforcement Actions Flow

```
┌─────────────────────────────────────────────────────────────────┐
│               EnforcementExecutor Actions                        │
└─────────────────────────────────────────────────────────────────┘

1. close_all_positions(symbol)
   │
   └─→ ⚠️ Enforcement triggered: CLOSE ALL POSITIONS - Symbol: [symbol|ALL]
       └─→ [enforcement.py:56] sdk_logger.warning()

2. close_position(symbol, contract_id)
   │
   └─→ ⚠️ Enforcement triggered: CLOSE POSITION - symbol/contract_id
       └─→ [enforcement.py:132] sdk_logger.warning()

3. cancel_all_orders(symbol)
   │
   └─→ ⚠️ Enforcement triggered: CANCEL ALL ORDERS - Symbol: [symbol|ALL]
       └─→ [enforcement.py:220] sdk_logger.warning()

4. flatten_and_cancel(symbol)
   │
   └─→ ⚠️ Enforcement triggered: FLATTEN AND CANCEL - Symbol: [symbol|ALL] - CRITICAL
       └─→ [enforcement.py:325] sdk_logger.warning()
```

---

### 4.5 Log Levels by Checkpoint

| Checkpoint | Log Level | Emoji | Purpose |
|------------|-----------|-------|---------|
| Service start | INFO | 🚀 | Application initialization |
| Config loaded | INFO | ✅ | Configuration validation |
| SDK connected | INFO | ✅ | Trading SDK connection |
| Rules initialized | INFO | ✅ | Risk rules setup |
| Event loop running | INFO | ✅ | Event monitoring active |
| Event received | INFO | 📨 | Event processing start |
| Rule evaluated | INFO | 🔍 | Rule evaluation result |
| Enforcement (alert) | INFO | ⚠️ | Low-severity action |
| Enforcement (pause/flatten) | WARNING | ⚠️ | High-severity action |
| Enforcement actions | WARNING | ⚠️ | Position/order modifications |

---

### 4.6 Example Log Output

**Production Mode (JSON Format)**:
```json
{"timestamp":"2025-10-24T03:00:00.000Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"__init__","line":44,"message":"🚀 Risk Manager starting..."}

{"timestamp":"2025-10-24T03:00:00.100Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"create","line":109,"message":"✅ Config loaded: 2 custom rules, monitoring 1 instruments"}

{"timestamp":"2025-10-24T03:00:00.200Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"_init_trading_integration","line":138,"message":"✅ SDK connected: 1 instrument(s) - MNQ"}

{"timestamp":"2025-10-24T03:00:00.300Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"_add_default_rules","line":184,"message":"✅ Rules initialized: 2 rules - DailyLossRule($-500.0), MaxPositionRule(2 contracts)"}

{"timestamp":"2025-10-24T03:00:00.400Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"start","line":38,"message":"✅ Event loop running: 2 active rules monitoring events"}

{"timestamp":"2025-10-24T03:00:01.000Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"evaluate_rules","line":68,"message":"📨 Event received: order_filled - evaluating 2 rules"}

{"timestamp":"2025-10-24T03:00:01.010Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"evaluate_rules","line":75,"message":"🔍 Rule evaluated: DailyLossRule - VIOLATED"}

{"timestamp":"2025-10-24T03:00:01.020Z","level":"WARNING","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":101,"message":"⚠️ Enforcement triggered: FLATTEN ALL - Rule: DailyLossRule"}

{"timestamp":"2025-10-24T03:00:01.030Z","level":"WARNING","logger":"risk_manager.sdk.enforcement","module":"enforcement","function":"close_all_positions","line":56,"message":"⚠️ Enforcement triggered: CLOSE ALL POSITIONS - Symbol: ALL"}
```

---

### 4.7 Integration with Monitoring Tools

The SDK logging can be integrated with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Datadog**
- **CloudWatch**
- **Grafana Loki**

All logs are JSON-formatted in production mode for easy parsing and querying.

---

## 5. State Persistence

### 5.1 Database Architecture

**File**: `src/risk_manager/state/database.py`

**SQLite Database Schema**:

```
data/risk_state.db
├── schema_version        # Schema versioning
├── daily_pnl             # Daily P&L tracking per account
├── lockouts              # Hard lockout states
├── timers                # Cooldown timers
└── trades                # Trade history for frequency tracking
```

---

### 5.2 Database Tables

#### 5.2.1 daily_pnl Table

**Purpose**: Track daily realized P&L per account

**Schema**:
```sql
CREATE TABLE daily_pnl (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    date TEXT NOT NULL,
    realized_pnl REAL NOT NULL DEFAULT 0.0,
    trade_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(account_id, date)
);

CREATE INDEX idx_daily_pnl_account_date ON daily_pnl(account_id, date);
```

**Usage**:
- Track daily realized P&L across ALL instruments
- Enforce RULE-003 (Daily Realized Loss)
- Enforce RULE-013 (Daily Realized Profit)
- Track trade count for RULE-006 (Trade Frequency)

---

#### 5.2.2 lockouts Table

**Purpose**: Track hard lockout states (until condition met)

**Schema**:
```sql
CREATE TABLE lockouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    locked_at TEXT NOT NULL,
    expires_at TEXT,
    unlock_condition TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(account_id, rule_id) ON CONFLICT REPLACE
);

CREATE INDEX idx_lockouts_account_active ON lockouts(account_id, active);
```

**Usage**:
- Store hard lockouts (RULE-003, RULE-009, RULE-010, RULE-013)
- Track expiration time (e.g., "5:00 PM" for daily reset)
- Admin can query and override lockouts

---

#### 5.2.3 timers Table

**Purpose**: Track cooldown timers (temporary lockouts with countdown)

**Schema**:
```sql
CREATE TABLE timers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    started_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(account_id, rule_id) ON CONFLICT REPLACE
);

CREATE INDEX idx_timers_account_active ON timers(account_id, active);
```

**Usage**:
- Store cooldown timers (RULE-006, RULE-007)
- Auto-unlock when timer expires
- Trader CLI shows countdown

---

#### 5.2.4 trades Table

**Purpose**: Trade history for frequency tracking

**Schema**:
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    trade_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    realized_pnl REAL,
    timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(account_id, trade_id)
);

CREATE INDEX idx_trades_account_timestamp ON trades(account_id, timestamp);
```

**Usage**:
- Track trade history across ALL symbols
- Enforce RULE-006 (Trade Frequency Limit)
- Query trades per minute/hour/session

---

### 5.3 PnL Tracker Implementation

**File**: `src/risk_manager/state/pnl_tracker.py`

**Features**:
- Daily P&L aggregation per account
- Trade count tracking
- Crash recovery (persists to SQLite)
- Multi-account support
- Daily reset capability

**Example Usage**:
```python
from risk_manager.state.database import Database
from risk_manager.state.pnl_tracker import PnLTracker

# Initialize
db = Database("data/risk_state.db")
tracker = PnLTracker(db)

# Add trade P&L
tracker.add_trade_pnl("ACCOUNT-001", -150.0)  # $150 loss
tracker.add_trade_pnl("ACCOUNT-001", 80.0)    # $80 profit

# Get daily P&L
pnl = tracker.get_daily_pnl("ACCOUNT-001")
# Returns: -70.0

# Check daily loss limit
if pnl <= -500.0:
    # Daily loss limit hit! Lock account
    await lockout_manager.set_lockout()

# Get trade count
count = tracker.get_trade_count("ACCOUNT-001")
# Returns: 2

# Daily reset (5:00 PM)
tracker.reset_daily_pnl("ACCOUNT-001")
```

---

### 5.4 Multi-Account Support

**PnLTracker Tracks Multiple Accounts**:
```python
# Track P&L for multiple accounts
tracker.add_trade_pnl("ACCOUNT-001", -100.0)
tracker.add_trade_pnl("ACCOUNT-002", 50.0)
tracker.add_trade_pnl("ACCOUNT-001", -200.0)

# Get all accounts' P&L
all_pnls = tracker.get_all_daily_pnls()
# Returns: {"ACCOUNT-001": -300.0, "ACCOUNT-002": 50.0}

# Get stats for specific account
stats = tracker.get_stats("ACCOUNT-001")
# Returns: {"realized_pnl": -300.0, "trade_count": 2}
```

---

### 5.5 Thread-Safe Database Operations

**Connection Management**:
```python
# Thread-safe context manager
with db.connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_pnl")
    results = cursor.fetchall()
```

**Query Helpers**:
```python
# Execute and return results
rows = db.execute("SELECT * FROM daily_pnl WHERE account_id = ?", ("ACCOUNT-001",))

# Execute and return first result
row = db.execute_one("SELECT realized_pnl FROM daily_pnl WHERE account_id = ?", ("ACCOUNT-001",))

# Execute write query (INSERT, UPDATE, DELETE)
db.execute_write("UPDATE daily_pnl SET realized_pnl = ? WHERE id = ?", (100.0, 1))
```

---

## 6. Security Requirements & Best Practices

### 6.1 Installation Security Checklist

**Step 1: Run Install Script as Admin**
```powershell
# Right-click PowerShell → "Run as Administrator"
PS> python scripts/install_service.py

# UAC prompt appears → Enter Windows admin password
# Script creates directories and sets ACL permissions
```

**Step 2: Verify File Permissions**
```powershell
# Check permissions on config directory
PS> icacls C:\ProgramData\RiskManager\config

# Expected output:
# BUILTIN\Administrators:(OI)(CI)(F)
# NT AUTHORITY\SYSTEM:(OI)(CI)(F)
# BUILTIN\Users:(OI)(CI)(R)
```

**Step 3: Verify Service Installed**
```powershell
# Check service status
PS> Get-Service RiskManagerV34

# Expected output:
# Status: Running
# StartType: Automatic
```

---

### 6.2 Security Testing Checklist

**Test 1: Trader Cannot Access Admin CLI**
```powershell
PS> risk-manager admin
# Expected: Error message + exits
```

**Test 2: Trader Cannot Kill Service**
```powershell
PS> taskkill /F /IM risk-manager.exe
# Expected: Access Denied
```

**Test 3: Trader Cannot Edit Config**
```
Action: Try to save changes to risk_config.yaml
Expected: Windows "Access Denied" dialog
```

**Test 4: Admin CAN Access Admin CLI**
```powershell
PS> # Right-click → Run as Administrator
PS> risk-manager admin
# Expected: Admin menu appears
```

**Test 5: Service Survives Reboot**
```
Action: Reboot computer
Expected: Service auto-starts
```

---

### 6.3 Configuration Security Best Practices

**1. Protect API Credentials**
```yaml
# accounts.yaml - Keep this file secure!
topstepx:
  api_key: "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="

# Permissions: Administrators RW, Users R
# Location: C:\ProgramData\RiskManager\config\accounts.yaml
```

**2. Validate Configuration on Load**
```python
# Use Pydantic for validation
config = RiskConfig.from_file("config/risk_config.yaml")
# Raises ValidationError if invalid
```

**3. Backup State Database Regularly**
```yaml
# risk_config.yaml
general:
  database:
    backup_enabled: true
    backup_interval_hours: 24
```

**4. Restrict Access to Logs**
```
C:\ProgramData\RiskManager\logs\
└── Permissions: Admins RW, Users R
```

---

### 6.4 Audit & Compliance Features

**Windows Event Logging**:
- All UAC prompts logged to Windows Security Event Log
- Service start/stop events logged
- Admin access attempts logged

**Application Logging**:
- All enforcement actions logged with timestamps
- Manual unlocks logged (admin username + timestamp)
- Configuration changes logged

**Database Audit Trail**:
```sql
-- All tables include created_at and updated_at timestamps
SELECT * FROM lockouts WHERE account_id = 'ACCOUNT-001'
ORDER BY created_at DESC;

-- Query who unlocked account
SELECT * FROM lockouts WHERE reason LIKE '%manual unlock%';
```

---

## 7. Implementation Checklist

### 7.1 Security Implementation

- [ ] **Windows Service**
  - [ ] Install service with LocalSystem account
  - [ ] Set startup type to Automatic
  - [ ] Verify service cannot be stopped by normal users

- [ ] **File Permissions**
  - [ ] Set ACL on config directory (Admin RW, Users R)
  - [ ] Set ACL on data directory (Admin RW, Users R)
  - [ ] Set ACL on logs directory (Admin RW, Users R)

- [ ] **Admin CLI**
  - [ ] Implement `is_admin()` elevation check
  - [ ] Implement `require_admin()` guard
  - [ ] Add to admin CLI entry point

- [ ] **Trader CLI**
  - [ ] Implement view-only menu
  - [ ] Disable all write operations
  - [ ] Test cannot access admin functions

- [ ] **Testing**
  - [ ] Test trader cannot kill service
  - [ ] Test trader cannot edit config
  - [ ] Test trader cannot access admin CLI
  - [ ] Test admin CAN access admin CLI
  - [ ] Test service survives reboot

---

### 7.2 Configuration Implementation

- [ ] **YAML Configuration**
  - [ ] Create `config/risk_config.yaml` template
  - [ ] Create `config/accounts.yaml` template
  - [ ] Create `config/holidays.yaml` template

- [ ] **Pydantic Models**
  - [ ] Implement `RiskConfig` class
  - [ ] Add validation rules
  - [ ] Add `from_file()` loader

- [ ] **Configuration Loading**
  - [ ] Load config on startup
  - [ ] Validate all required fields
  - [ ] Handle missing/invalid config gracefully

- [ ] **Configuration Reloading**
  - [ ] Implement admin CLI config editor
  - [ ] Reload config without service restart
  - [ ] Validate before applying changes

---

### 7.3 Multi-Symbol Implementation

- [ ] **SDK Integration**
  - [ ] Initialize `TradingSuite` with multiple instruments
  - [ ] Subscribe to account-wide events
  - [ ] Bridge events to Risk EventBus

- [ ] **Account-Wide Aggregation**
  - [ ] Implement total contracts calculation
  - [ ] Implement daily P&L aggregation
  - [ ] Implement trade frequency tracking

- [ ] **Per-Instrument Rules**
  - [ ] Implement per-instrument contract limits
  - [ ] Implement per-position P&L tracking
  - [ ] Implement symbol blacklist

---

### 7.4 Logging Implementation

- [ ] **8 Checkpoint Logging**
  - [ ] Checkpoint 1: Service start (manager.py)
  - [ ] Checkpoint 2: Config loaded (manager.py)
  - [ ] Checkpoint 3: SDK connected (manager.py)
  - [ ] Checkpoint 4: Rules initialized (manager.py)
  - [ ] Checkpoint 5: Event loop running (engine.py)
  - [ ] Checkpoint 6: Event received (engine.py)
  - [ ] Checkpoint 7: Rule evaluated (engine.py)
  - [ ] Checkpoint 8: Enforcement triggered (enforcement.py)

- [ ] **Log Formatting**
  - [ ] JSON format for production
  - [ ] Human-readable format for development
  - [ ] Include timestamps, log levels, emojis

- [ ] **Log Management**
  - [ ] Rotate logs daily
  - [ ] Compress old logs
  - [ ] Delete logs older than 30 days

---

### 7.5 State Persistence Implementation

- [ ] **Database Schema**
  - [ ] Create `daily_pnl` table
  - [ ] Create `lockouts` table
  - [ ] Create `timers` table
  - [ ] Create `trades` table
  - [ ] Add schema versioning

- [ ] **PnL Tracker**
  - [ ] Implement `add_trade_pnl()`
  - [ ] Implement `get_daily_pnl()`
  - [ ] Implement `get_trade_count()`
  - [ ] Implement `reset_daily_pnl()`

- [ ] **Lockout Manager**
  - [ ] Implement `set_lockout()`
  - [ ] Implement `clear_lockout()`
  - [ ] Implement `get_active_lockouts()`
  - [ ] Implement auto-unlock on timer expiration

- [ ] **Database Backups**
  - [ ] Implement daily backup
  - [ ] Compress backups
  - [ ] Restore from backup (admin CLI)

---

## Summary

### Security Architecture
- **Windows UAC-based**: No custom passwords, OS-level protection
- **4 Protection Layers**: Service, ACL, UAC, Process
- **2 Access Levels**: Admin (elevated) vs Trader (view-only)
- **Multi-Account**: Supports multiple trading accounts
- **Audit Trail**: Full logging of all security events

### Configuration System
- **YAML-based**: Human-readable, easy to edit
- **Pydantic validation**: Type-safe, validated on load
- **13 Risk Rules**: 3 categories (trade-by-trade, timer, hard lockout)
- **Multi-Symbol**: Account-wide + per-instrument rules
- **Hot Reload**: Update config without service restart

### Logging & Monitoring
- **8 Strategic Checkpoints**: Track system lifecycle
- **JSON Format**: Production-ready for log aggregation
- **Emoji Markers**: Easy visual scanning
- **Integration Ready**: ELK, Splunk, Datadog compatible

### State Persistence
- **SQLite Database**: Crash-resistant, thread-safe
- **4 Tables**: P&L, lockouts, timers, trades
- **Multi-Account**: Track unlimited accounts
- **Auto-Backup**: Daily backups with compression

---

**Analysis Complete**: 2025-10-25
**Researcher**: RESEARCHER 5 - Security & Configuration Specialist
**Total Features Documented**: 50+ security/config features
**Implementation Status**: Architecture designed, core implementation in progress

---

## Key Files Reference

**Security**:
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/SECURITY_MODEL.md` (22KB)
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/dev-guides/SECURITY_QUICK_REF.md` (5KB)
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/src/service/windows_service.py` (planned)
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/src/cli/admin/auth.py` (planned)

**Configuration**:
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/CONFIG_FORMATS.md` (19KB)
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/src/risk_manager/core/config.py` (2.5KB)
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/tests/fixtures/configs.py` (9KB)

**Multi-Symbol Support**:
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/MULTI_SYMBOL_SUPPORT.md` (19KB)

**Logging**:
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/LOGGING_FLOW.md` (5KB)

**State Persistence**:
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/src/risk_manager/state/database.py` (7.5KB)
- `/mnt/c/Users/jakers/Desktop/risk-manager-v34/src/risk_manager/state/pnl_tracker.py` (8KB)
