# Timers Configuration Schema (CRITICAL)

**Document Type**: Unified Configuration Specification
**Created**: 2025-10-25
**Researcher**: Wave 3 Researcher 5 - Configuration System Specification Unification
**Status**: PRODUCTION READY

---

## Executive Summary

This document defines the **timers configuration schema** for Risk Manager V34. Timers control when risk limits reset, how long lockouts last, and when trading sessions are allowed.

**CRITICAL PRINCIPLE**: **ALL timers, reset times, and schedules MUST be configurable**. Nothing is hardcoded. Admin controls all timing via `config/timers_config.yaml`.

---

## Table of Contents

1. [Configuration Principles](#1-configuration-principles)
2. [Complete YAML Schema](#2-complete-yaml-schema)
3. [Daily Reset Configuration](#3-daily-reset-configuration)
4. [Lockout Duration Configuration](#4-lockout-duration-configuration)
5. [Session Hours Configuration](#5-session-hours-configuration)
6. [Holiday Configuration](#6-holiday-configuration)
7. [Validation Rules](#7-validation-rules)
8. [Implementation Examples](#8-implementation-examples)

---

## 1. Configuration Principles

### 1.1 Core Principle

**Configurability is Key**: Every timer, reset time, and schedule MUST be configurable via YAML.

**NO hardcoding**:
- ❌ Reset time is NOT hardcoded to 5 PM
- ❌ Lockout duration is NOT hardcoded to 24 hours
- ❌ Session hours are NOT hardcoded to 9:30 AM - 4 PM
- ❌ Timezone is NOT hardcoded to America/New_York

**Admin decides**:
- ✅ Reset could be 5 PM ET, midnight CT, 6 PM ET, etc. (user's choice)
- ✅ Lockout could be until reset, 1 hour, 24 hours, etc. (user's choice)
- ✅ Sessions could be any hours (8:30-3:00, 9:00-5:00, etc.)
- ✅ Timezone could be any IANA timezone

### 1.2 Design Goals

1. **Flexibility**: Support any trading schedule, any timezone, any reset time
2. **Clarity**: Clear, self-documenting YAML structure
3. **Validation**: Catch invalid configurations before deployment
4. **Defaults**: Sensible defaults that work out-of-the-box

---

## 2. Complete YAML Schema

**File**: `config/timers_config.yaml`

```yaml
# ==============================================================================
# TIMERS CONFIGURATION
# ==============================================================================
# Purpose: Control when risk limits reset, lockout durations, and trading hours
# ==============================================================================

# ==============================================================================
# DAILY RESET CONFIGURATION
# ==============================================================================
# Controls when daily P&L limits reset (RULE-003, RULE-013)
# ==============================================================================
daily_reset:
  # Reset time (24-hour format HH:MM)
  time: "17:00"                    # 5:00 PM

  # Timezone (IANA timezone string)
  # Examples: America/New_York, America/Chicago, Europe/London
  timezone: "America/Chicago"      # Central Time

  # Enable/disable daily reset
  enabled: true

  # What happens at reset time
  reset_actions:
    clear_daily_pnl: true          # Reset daily P&L to $0.00
    unlock_daily_loss: true        # Unlock RULE-003 (Daily Realized Loss)
    unlock_daily_profit: true      # Unlock RULE-013 (Daily Realized Profit)
    clear_trade_count: true        # Reset trade frequency counters

# ==============================================================================
# LOCKOUT DURATION CONFIGURATION
# ==============================================================================
# Controls how long lockouts last for each rule category
# ==============================================================================
lockout_durations:
  # Hard Lockout Rules (RULE-003, RULE-013, RULE-009, RULE-010)
  hard_lockout:
    # Daily Realized Loss (RULE-003)
    daily_realized_loss: "until_reset"  # Options: "until_reset", "permanent", "<duration>"

    # Daily Realized Profit (RULE-013)
    daily_realized_profit: "until_reset"

    # Session Block Outside (RULE-009)
    session_block_outside: "until_session_start"  # Until next session starts

    # Auth Loss Guard (RULE-010)
    auth_loss_guard: "permanent"  # Requires admin unlock

  # Timer/Cooldown Rules (RULE-006, RULE-007)
  timer_cooldown:
    # Trade Frequency Limit (RULE-006)
    trade_frequency:
      per_minute_breach: "60s"     # 1 minute cooldown
      per_hour_breach: "30m"       # 30 minute cooldown
      per_session_breach: "1h"     # 1 hour cooldown

    # Cooldown After Loss (RULE-007)
    cooldown_after_loss: "15m"     # 15 minute cooldown

# Duration format examples:
# - "60s" = 60 seconds
# - "15m" = 15 minutes
# - "1h" = 1 hour
# - "24h" = 24 hours
# - "until_reset" = Until daily_reset time
# - "until_session_start" = Until next session_hours.start
# - "permanent" = Requires admin unlock

# ==============================================================================
# SESSION HOURS CONFIGURATION
# ==============================================================================
# Controls when trading is allowed (RULE-009: Session Block Outside)
# ==============================================================================
session_hours:
  # Trading hours (24-hour format HH:MM)
  start: "08:30"                   # 8:30 AM
  end: "15:00"                     # 3:00 PM

  # Timezone (IANA timezone string)
  timezone: "America/Chicago"      # Central Time

  # Enable/disable session restrictions
  enabled: true

  # Allowed trading days (0=Monday, 6=Sunday)
  allowed_days:
    - 0  # Monday
    - 1  # Tuesday
    - 2  # Wednesday
    - 3  # Thursday
    - 4  # Friday
  # Exclude weekends: [0, 1, 2, 3, 4]
  # Include weekends: [0, 1, 2, 3, 4, 5, 6]

  # Pre-market / After-hours settings
  pre_market:
    enabled: false                 # Allow pre-market trading?
    start: "07:00"                 # Pre-market start (if enabled)

  after_hours:
    enabled: false                 # Allow after-hours trading?
    end: "20:00"                   # After-hours end (if enabled)

# ==============================================================================
# HOLIDAY CONFIGURATION
# ==============================================================================
# Market holidays when trading is blocked (RULE-009: respect_holidays: true)
# ==============================================================================
holidays:
  # Enable/disable holiday checks
  enabled: true

  # Holiday dates (YYYY-MM-DD format)
  dates:
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

    2026:
      - "2026-01-01"  # New Year's Day
      - "2026-01-19"  # Martin Luther King Jr. Day
      - "2026-02-16"  # Presidents' Day
      - "2026-04-03"  # Good Friday
      - "2026-05-25"  # Memorial Day
      - "2026-07-03"  # Independence Day (observed)
      - "2026-09-07"  # Labor Day
      - "2026-11-26"  # Thanksgiving
      - "2026-12-25"  # Christmas

  # Early close days (e.g., day before Thanksgiving)
  early_close:
    - date: "2025-11-26"           # Day before Thanksgiving
      close_time: "13:00"          # 1:00 PM close

    - date: "2025-12-24"           # Christmas Eve
      close_time: "13:00"          # 1:00 PM close

# ==============================================================================
# ADVANCED TIMER SETTINGS
# ==============================================================================
advanced:
  # How often to check time-based conditions (seconds)
  check_interval: 10               # Check every 10 seconds

  # Grace period before session close enforcement (seconds)
  session_close_grace: 60          # 1 minute grace before hard close

  # Auto-unlock behavior
  auto_unlock:
    enabled: true                  # Automatically unlock at reset time
    notify_on_unlock: true         # Send notification when unlocked

  # Daylight Saving Time (DST) handling
  dst:
    auto_adjust: true              # Automatically adjust for DST
    notify_on_change: true         # Notify when DST changes occur
```

---

## 3. Daily Reset Configuration

### 3.1 Purpose

Controls when daily P&L limits reset (affects RULE-003 and RULE-013).

### 3.2 Configuration Options

```yaml
daily_reset:
  time: "17:00"                    # REQUIRED: Reset time (HH:MM)
  timezone: "America/Chicago"      # REQUIRED: IANA timezone
  enabled: true                    # REQUIRED: Enable/disable

  reset_actions:
    clear_daily_pnl: true          # Reset daily P&L counters
    unlock_daily_loss: true        # Unlock RULE-003
    unlock_daily_profit: true      # Unlock RULE-013
    clear_trade_count: true        # Reset RULE-006 counters
```

### 3.3 Examples

**Conservative Trader (Early Reset)**:
```yaml
daily_reset:
  time: "15:00"                    # 3:00 PM (market close)
  timezone: "America/Chicago"
  enabled: true
```

**Aggressive Trader (Late Reset)**:
```yaml
daily_reset:
  time: "23:59"                    # Midnight
  timezone: "America/Chicago"
  enabled: true
```

**European Trader**:
```yaml
daily_reset:
  time: "17:00"                    # 5:00 PM London time
  timezone: "Europe/London"
  enabled: true
```

### 3.4 Validation Rules

1. **time**:
   - MUST match format `HH:MM` (24-hour)
   - Hour: 00-23
   - Minute: 00-59
   - Example: `"17:00"` (valid), `"5pm"` (invalid)

2. **timezone**:
   - MUST be valid IANA timezone string
   - Examples: `America/New_York`, `America/Chicago`, `Europe/London`
   - Invalid: `EST`, `CST`, `PST` (use IANA names)

3. **enabled**:
   - MUST be boolean (true/false)
   - If false, daily limits never reset (must unlock manually)

---

## 4. Lockout Duration Configuration

### 4.1 Purpose

Controls how long lockouts last for each rule.

### 4.2 Duration Format

**Format**: `"<number><unit>"`

**Units**:
- `s` = seconds
- `m` = minutes
- `h` = hours

**Special Values**:
- `"until_reset"` = Until daily_reset time
- `"until_session_start"` = Until next session_hours.start
- `"permanent"` = Requires admin unlock

**Examples**:
- `"60s"` = 60 seconds (1 minute)
- `"15m"` = 15 minutes
- `"1h"` = 1 hour
- `"24h"` = 24 hours
- `"until_reset"` = Until daily_reset.time
- `"permanent"` = Admin-only unlock

### 4.3 Hard Lockout Rules

```yaml
lockout_durations:
  hard_lockout:
    # RULE-003: Daily Realized Loss
    daily_realized_loss: "until_reset"
    # Options: "until_reset", "24h", "permanent"

    # RULE-013: Daily Realized Profit
    daily_realized_profit: "until_reset"
    # Options: "until_reset", "24h", "permanent"

    # RULE-009: Session Block Outside
    session_block_outside: "until_session_start"
    # Options: "until_session_start", "1h", "permanent"

    # RULE-010: Auth Loss Guard
    auth_loss_guard: "permanent"
    # Options: "permanent" (cannot be time-based)
```

### 4.4 Timer/Cooldown Rules

```yaml
lockout_durations:
  timer_cooldown:
    # RULE-006: Trade Frequency Limit
    trade_frequency:
      per_minute_breach: "60s"     # 1 minute
      per_hour_breach: "30m"       # 30 minutes
      per_session_breach: "1h"     # 1 hour

    # RULE-007: Cooldown After Loss
    cooldown_after_loss: "15m"     # 15 minutes
```

### 4.5 Examples

**Strict Configuration (Long Cooldowns)**:
```yaml
lockout_durations:
  timer_cooldown:
    trade_frequency:
      per_minute_breach: "5m"      # 5 minutes (strict)
      per_hour_breach: "1h"        # 1 hour (strict)
      per_session_breach: "until_reset"  # Rest of day (strict)

    cooldown_after_loss: "30m"     # 30 minutes (strict)
```

**Lenient Configuration (Short Cooldowns)**:
```yaml
lockout_durations:
  timer_cooldown:
    trade_frequency:
      per_minute_breach: "30s"     # 30 seconds (lenient)
      per_hour_breach: "10m"       # 10 minutes (lenient)
      per_session_breach: "30m"    # 30 minutes (lenient)

    cooldown_after_loss: "5m"      # 5 minutes (lenient)
```

### 4.6 Validation Rules

1. **Duration Format**:
   - MUST match: `^\d+[smh]$` OR special value
   - Special values: `until_reset`, `until_session_start`, `permanent`
   - Examples: `"60s"`, `"15m"`, `"1h"` (valid)
   - Invalid: `"60"`, `"15 minutes"`, `"1hour"`

2. **Range Validation**:
   - Seconds: 1-86400 (1 second to 24 hours)
   - Minutes: 1-1440 (1 minute to 24 hours)
   - Hours: 1-24 (1 hour to 24 hours)

3. **Semantic Validation**:
   - `per_minute_breach` < `per_hour_breach` < `per_session_breach`
   - Cannot set `auth_loss_guard` to time-based value (must be `permanent`)

---

## 5. Session Hours Configuration

### 5.1 Purpose

Controls when trading is allowed (RULE-009: Session Block Outside).

### 5.2 Configuration Options

```yaml
session_hours:
  start: "08:30"                   # REQUIRED: Session start (HH:MM)
  end: "15:00"                     # REQUIRED: Session end (HH:MM)
  timezone: "America/Chicago"      # REQUIRED: IANA timezone
  enabled: true                    # REQUIRED: Enable/disable

  allowed_days:                    # REQUIRED: Weekdays (0=Mon, 6=Sun)
    - 0  # Monday
    - 1  # Tuesday
    - 2  # Wednesday
    - 3  # Thursday
    - 4  # Friday

  pre_market:
    enabled: false                 # Allow pre-market trading?
    start: "07:00"                 # Pre-market start (if enabled)

  after_hours:
    enabled: false                 # Allow after-hours trading?
    end: "20:00"                   # After-hours end (if enabled)
```

### 5.3 Examples

**Regular Trading Hours Only (Conservative)**:
```yaml
session_hours:
  start: "09:30"                   # Market open
  end: "16:00"                     # Market close
  timezone: "America/New_York"
  enabled: true
  allowed_days: [0, 1, 2, 3, 4]    # Mon-Fri only

  pre_market:
    enabled: false

  after_hours:
    enabled: false
```

**Extended Hours (Aggressive)**:
```yaml
session_hours:
  start: "09:30"                   # Regular market
  end: "16:00"
  timezone: "America/New_York"
  enabled: true
  allowed_days: [0, 1, 2, 3, 4]

  pre_market:
    enabled: true                  # Allow pre-market
    start: "04:00"                 # 4:00 AM

  after_hours:
    enabled: true                  # Allow after-hours
    end: "20:00"                   # 8:00 PM
```

**24/7 Trading (Crypto/Futures)**:
```yaml
session_hours:
  start: "00:00"                   # Midnight
  end: "23:59"                     # End of day
  timezone: "America/Chicago"
  enabled: true
  allowed_days: [0, 1, 2, 3, 4, 5, 6]  # All days

  pre_market:
    enabled: false                 # Not applicable

  after_hours:
    enabled: false                 # Not applicable
```

**Disabled (No Restrictions)**:
```yaml
session_hours:
  enabled: false                   # Allow trading any time
```

### 5.4 Validation Rules

1. **Time Format**:
   - MUST match `HH:MM` (24-hour format)
   - Hour: 00-23, Minute: 00-59

2. **Logical Validation**:
   - `end` MUST be after `start`
   - If `pre_market.enabled`, then `pre_market.start` < `start`
   - If `after_hours.enabled`, then `after_hours.end` > `end`

3. **Allowed Days**:
   - MUST be list of integers 0-6
   - 0=Monday, 1=Tuesday, ..., 6=Sunday
   - Cannot be empty list

---

## 6. Holiday Configuration

### 6.1 Purpose

Market holidays when trading is blocked (if RULE-009 `respect_holidays: true`).

### 6.2 Configuration Options

```yaml
holidays:
  enabled: true                    # Enable/disable holiday checks

  dates:
    2025:                          # Year
      - "2025-01-01"               # Holiday (YYYY-MM-DD format)
      - "2025-07-04"
      # ... more holidays

  early_close:
    - date: "2025-11-26"           # Early close date
      close_time: "13:00"          # Close time (HH:MM)
```

### 6.3 Examples

**US Market Holidays (2025)**:
```yaml
holidays:
  enabled: true

  dates:
    2025:
      - "2025-01-01"  # New Year's Day
      - "2025-01-20"  # MLK Day
      - "2025-02-17"  # Presidents' Day
      - "2025-04-18"  # Good Friday
      - "2025-05-26"  # Memorial Day
      - "2025-07-04"  # Independence Day
      - "2025-09-01"  # Labor Day
      - "2025-11-27"  # Thanksgiving
      - "2025-12-25"  # Christmas

  early_close:
    - date: "2025-07-03"           # Day before July 4th
      close_time: "13:00"

    - date: "2025-11-26"           # Day before Thanksgiving
      close_time: "13:00"

    - date: "2025-12-24"           # Christmas Eve
      close_time: "13:00"
```

**No Holiday Restrictions**:
```yaml
holidays:
  enabled: false                   # Ignore holidays
```

### 6.4 Validation Rules

1. **Date Format**:
   - MUST match `YYYY-MM-DD` (ISO 8601)
   - Examples: `"2025-01-01"` (valid), `"1/1/2025"` (invalid)

2. **Year**:
   - MUST be current year or future year
   - Warn if no holidays defined for current year

3. **Early Close**:
   - `close_time` MUST match `HH:MM` format
   - `close_time` MUST be during regular session hours
   - Cannot be same as or after `session_hours.end`

---

## 7. Validation Rules

### 7.1 Cross-Reference Validation

1. **Timezone Consistency**:
   - `daily_reset.timezone` SHOULD match `session_hours.timezone`
   - Warn if different (user may have good reason, but check)

2. **Lockout References**:
   - `"until_reset"` requires `daily_reset.enabled: true`
   - `"until_session_start"` requires `session_hours.enabled: true`

3. **Holiday References**:
   - If `session_hours.respect_holidays: true`, then `holidays.enabled` MUST be true
   - Warn if current year has no holidays defined

### 7.2 Pydantic Validation Models

**Python Implementation**:

```python
from pydantic import BaseModel, Field, field_validator
from datetime import time
import re

class DailyResetConfig(BaseModel):
    time: str = Field(..., description="Reset time HH:MM")
    timezone: str = Field(..., description="IANA timezone")
    enabled: bool = True

    @field_validator('time')
    def validate_time_format(cls, v):
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f"Invalid time format: {v}. Use HH:MM (24-hour)")
        return v

    @field_validator('timezone')
    def validate_timezone(cls, v):
        import zoneinfo
        try:
            zoneinfo.ZoneInfo(v)
        except zoneinfo.ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {v}. Use IANA timezone (e.g., America/Chicago)")
        return v

class LockoutDurationConfig(BaseModel):
    daily_realized_loss: str = "until_reset"
    daily_realized_profit: str = "until_reset"
    session_block_outside: str = "until_session_start"
    auth_loss_guard: str = "permanent"

    @field_validator('*')
    def validate_duration(cls, v):
        # Check special values
        if v in ["until_reset", "until_session_start", "permanent"]:
            return v

        # Check duration format: \d+[smh]
        if not re.match(r'^\d+[smh]$', v):
            raise ValueError(
                f"Invalid duration: {v}. "
                f"Use format: <number><unit> (e.g., '60s', '15m', '1h') "
                f"or special values: 'until_reset', 'until_session_start', 'permanent'"
            )

        return v

class SessionHoursConfig(BaseModel):
    start: str = Field(..., description="Session start HH:MM")
    end: str = Field(..., description="Session end HH:MM")
    timezone: str = Field(..., description="IANA timezone")
    enabled: bool = True
    allowed_days: list[int] = Field(..., description="Weekdays 0-6")

    @field_validator('start', 'end')
    def validate_time_format(cls, v):
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f"Invalid time: {v}. Use HH:MM")
        return v

    @field_validator('allowed_days')
    def validate_days(cls, v):
        if not v:
            raise ValueError("allowed_days cannot be empty")

        for day in v:
            if day not in range(7):
                raise ValueError(f"Invalid day: {day}. Must be 0-6 (0=Monday)")

        return v

    @field_validator('end')
    def validate_end_after_start(cls, v, info):
        start = info.data.get('start')
        if start and v <= start:
            raise ValueError(f"Session end ({v}) must be after start ({start})")
        return v

class TimersConfig(BaseModel):
    daily_reset: DailyResetConfig
    lockout_durations: LockoutDurationConfig
    session_hours: SessionHoursConfig
    holidays: HolidaysConfig
```

---

## 8. Implementation Examples

### 8.1 Loading Configuration

```python
from risk_manager.core.config import TimersConfig
import yaml

# Load from file
with open('config/timers_config.yaml') as f:
    data = yaml.safe_load(f)

# Validate and parse
config = TimersConfig(**data)

# Access values
reset_time = config.daily_reset.time          # "17:00"
timezone = config.daily_reset.timezone        # "America/Chicago"
session_start = config.session_hours.start    # "08:30"
```

### 8.2 Checking if Reset Time Reached

```python
from datetime import datetime
from zoneinfo import ZoneInfo

def is_reset_time_reached(config: TimersConfig) -> bool:
    """Check if daily reset time has been reached."""
    now = datetime.now(ZoneInfo(config.daily_reset.timezone))

    reset_hour, reset_minute = map(int, config.daily_reset.time.split(':'))
    reset_time = now.replace(hour=reset_hour, minute=reset_minute, second=0)

    return now >= reset_time

# Usage
if is_reset_time_reached(timers_config):
    await reset_daily_pnl()
    await unlock_daily_loss_rule()
```

### 8.3 Checking if Within Session Hours

```python
def is_within_session_hours(config: TimersConfig) -> bool:
    """Check if current time is within allowed session hours."""
    if not config.session_hours.enabled:
        return True  # No restrictions

    now = datetime.now(ZoneInfo(config.session_hours.timezone))

    # Check day of week
    if now.weekday() not in config.session_hours.allowed_days:
        return False  # Not allowed on this day

    # Check time range
    start_hour, start_minute = map(int, config.session_hours.start.split(':'))
    end_hour, end_minute = map(int, config.session_hours.end.split(':'))

    session_start = now.replace(hour=start_hour, minute=start_minute)
    session_end = now.replace(hour=end_hour, minute=end_minute)

    return session_start <= now <= session_end

# Usage
if not is_within_session_hours(timers_config):
    await flatten_all_positions()
    await set_lockout(until=next_session_start())
```

### 8.4 Parsing Lockout Duration

```python
import re
from datetime import datetime, timedelta

def parse_duration(duration_str: str) -> timedelta | str:
    """
    Parse duration string to timedelta or special value.

    Examples:
        "60s" -> timedelta(seconds=60)
        "15m" -> timedelta(minutes=15)
        "1h" -> timedelta(hours=1)
        "until_reset" -> "until_reset" (special)
    """
    if duration_str in ["until_reset", "until_session_start", "permanent"]:
        return duration_str  # Special value

    match = re.match(r'^(\d+)([smh])$', duration_str)
    if not match:
        raise ValueError(f"Invalid duration: {duration_str}")

    value, unit = match.groups()
    value = int(value)

    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)

# Usage
cooldown = parse_duration("15m")  # timedelta(minutes=15)
unlock_time = datetime.now() + cooldown
```

---

## Summary

### Key Takeaways

1. **Everything is Configurable**: Reset times, lockout durations, session hours, holidays
2. **No Hardcoding**: Admin controls all timing via YAML
3. **Clear Validation**: Pydantic validates all configurations before deployment
4. **Flexible**: Supports any timezone, any schedule, any trading hours
5. **Safe Defaults**: Works out-of-the-box with sensible defaults

### Configuration Files

- **timers_config.yaml**: Controls timing (THIS FILE)
- **risk_config.yaml**: Controls risk rules
- **accounts.yaml**: Controls API credentials

### Next Steps

1. Implement Pydantic models for validation
2. Add configuration loading logic
3. Wire timers into RiskManager
4. Add admin CLI for timer configuration
5. Test with different timezones and schedules

---

**Document Complete**
**Created**: 2025-10-25
**Status**: PRODUCTION READY
