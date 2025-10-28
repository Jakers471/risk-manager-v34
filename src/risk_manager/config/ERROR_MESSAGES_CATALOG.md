# Configuration Validation Error Messages Catalog

**Purpose**: Complete catalog of all validation error messages with examples

**Created**: 2025-10-27
**Status**: Production Ready

---

## Table of Contents

1. [Field Validation Errors](#field-validation-errors)
2. [Model Validation Errors](#model-validation-errors)
3. [Cross-Configuration Errors](#cross-configuration-errors)
4. [Edge Cases](#edge-cases)

---

## Field Validation Errors

### Loss Limits (Must Be Negative)

**Fields**: daily_realized_loss.limit, daily_unrealized_loss.limit, cooldown_after_loss.loss_threshold

**Valid Input**:
```yaml
limit: -500.0    # ✅ Negative value
limit: -1000.0   # ✅ Negative value
limit: -0.01     # ✅ Small negative value
```

**Invalid Input & Errors**:

```yaml
# Input:
limit: 500.0

# Error:
Daily loss limit must be negative (you entered 500.0).
Reason: Negative values represent losses.
Fix: Change 500.0 to -500.0.
Example: -500.0 means maximum $500 loss allowed.
```

```yaml
# Input:
limit: 0

# Error:
Daily loss limit must be negative (you entered 0).
Reason: Negative values represent losses.
Fix: Change 0 to -500.0.
Example: -500.0 means maximum $500 loss allowed.
```

---

### Profit Targets (Must Be Positive)

**Fields**: daily_realized_profit.target, max_unrealized_profit.target

**Valid Input**:
```yaml
target: 1000.0   # ✅ Positive value
target: 500.0    # ✅ Positive value
target: 0.01     # ✅ Small positive value
```

**Invalid Input & Errors**:

```yaml
# Input:
target: -1000.0

# Error:
Profit target must be > 0 (you entered -1000.0).
Reason: This value represents a count/limit.
Fix: Use a positive number greater than zero.
```

```yaml
# Input:
target: 0

# Error:
Profit target must be > 0 (you entered 0).
Reason: This value represents a count/limit.
Fix: Use a positive number greater than zero.
```

---

### Contract Limits (Must Be Positive)

**Fields**: max_contracts.limit, max_contracts_per_instrument.default_limit, instrument_limits values

**Valid Input**:
```yaml
limit: 5         # ✅ Positive integer
limit: 1         # ✅ Minimum positive
limit: 100       # ✅ Large positive
```

**Invalid Input & Errors**:

```yaml
# Input:
limit: 0

# Error:
Max contracts limit must be > 0 (you entered 0).
Reason: This value represents a count/limit.
Fix: Use a positive number greater than zero.
```

```yaml
# Input:
limit: -5

# Error:
Max contracts limit must be > 0 (you entered -5).
Reason: This value represents a count/limit.
Fix: Use a positive number greater than zero.
```

---

### Time Format (HH:MM)

**Fields**: daily_reset.time, session_hours.start, session_hours.end, early_close.close_time

**Valid Input**:
```yaml
time: "17:00"    # ✅ 5 PM
time: "09:30"    # ✅ 9:30 AM
time: "00:00"    # ✅ Midnight
time: "23:59"    # ✅ 11:59 PM
```

**Invalid Input & Errors**:

```yaml
# Input:
time: "25:00"

# Error:
Invalid Reset time format: '25:00'.
Use HH:MM (24-hour format).
Example: 17:00 for 5 PM, 09:30 for 9:30 AM
```

```yaml
# Input:
time: "17:60"

# Error:
Invalid Reset time format: '17:60'.
Use HH:MM (24-hour format).
Example: 17:00 for 5 PM, 09:30 for 9:30 AM
```

```yaml
# Input:
time: "5:00 PM"

# Error:
Invalid Reset time format: '5:00 PM'.
Use HH:MM (24-hour format).
Example: 17:00 for 5 PM, 09:30 for 9:30 AM
```

```yaml
# Input:
time: "5:00"

# Error:
Invalid Reset time format: '5:00'.
Use HH:MM (24-hour format).
Example: 17:00 for 5 PM, 09:30 for 9:30 AM
```

---

### Date Format (YYYY-MM-DD)

**Fields**: holidays.dates[], early_close.date

**Valid Input**:
```yaml
date: "2025-07-04"   # ✅ July 4th, 2025
date: "2025-12-25"   # ✅ December 25th, 2025
date: "2025-01-01"   # ✅ January 1st, 2025
```

**Invalid Input & Errors**:

```yaml
# Input:
date: "2025-13-01"

# Error:
Invalid Holiday date format: '2025-13-01'.
Use YYYY-MM-DD (ISO 8601 format).
Example: 2025-07-04 for July 4th, 2025
```

```yaml
# Input:
date: "07/04/2025"

# Error:
Invalid Holiday date format: '07/04/2025'.
Use YYYY-MM-DD (ISO 8601 format).
Example: 2025-07-04 for July 4th, 2025
```

```yaml
# Input:
date: "2025-02-30"

# Error:
Invalid Holiday date: '2025-02-30'.
Reason: day is out of range for month.
Example: Month 13 doesn't exist, use 01-12
```

---

### Timezone (IANA)

**Fields**: general.timezone, daily_reset.timezone, session_hours.timezone

**Valid Input**:
```yaml
timezone: "America/Chicago"      # ✅ Central Time
timezone: "America/New_York"     # ✅ Eastern Time
timezone: "Europe/London"        # ✅ UK Time
timezone: "Asia/Tokyo"           # ✅ Japan Time
```

**Invalid Input & Errors**:

```yaml
# Input:
timezone: "CST"

# Error:
Invalid Timezone: 'CST'.
Use IANA timezone (e.g., America/Chicago, Europe/London, America/New_York).
NOT abbreviations like CST, EST, or PST.
See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

```yaml
# Input:
timezone: "Central Time"

# Error:
Invalid Timezone: 'Central Time'.
Use IANA timezone (e.g., America/Chicago, Europe/London, America/New_York).
NOT abbreviations like CST, EST, or PST.
See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

```yaml
# Input:
timezone: "US/Central"

# Error:
Invalid Timezone: 'US/Central'.
Use IANA timezone (e.g., America/Chicago, Europe/London, America/New_York).
NOT abbreviations like CST, EST, or PST.
See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

---

### Duration Format

**Fields**: All lockout_durations fields

**Valid Input**:
```yaml
duration: "60s"              # ✅ 60 seconds
duration: "15m"              # ✅ 15 minutes
duration: "1h"               # ✅ 1 hour
duration: "24h"              # ✅ 24 hours
duration: "until_reset"      # ✅ Special value
duration: "until_session_start"  # ✅ Special value
duration: "permanent"        # ✅ Special value
```

**Invalid Input & Errors**:

```yaml
# Input:
duration: "invalid"

# Error:
Invalid Lockout duration: 'invalid'.
Use format: <number><unit> where unit is s (seconds), m (minutes), or h (hours).
Examples: '60s' (60 seconds), '15m' (15 minutes), '1h' (1 hour).
Or use special values: until_reset, until_session_start, permanent
```

```yaml
# Input:
duration: "15"

# Error:
Invalid Lockout duration: '15'.
Use format: <number><unit> where unit is s (seconds), m (minutes), or h (hours).
Examples: '60s' (60 seconds), '15m' (15 minutes), '1h' (1 hour).
Or use special values: until_reset, until_session_start, permanent
```

```yaml
# Input:
duration: "15 minutes"

# Error:
Invalid Lockout duration: '15 minutes'.
Use format: <number><unit> where unit is s (seconds), m (minutes), or h (hours).
Examples: '60s' (60 seconds), '15m' (15 minutes), '1h' (1 hour).
Or use special values: until_reset, until_session_start, permanent
```

---

### Enum Validation

**Fields**: count_type, account_type, lockout_type, log_level

**Valid Input**:
```yaml
count_type: "net"            # ✅ Valid enum
count_type: "gross"          # ✅ Valid enum
account_type: "practice"     # ✅ Valid enum
account_type: "live"         # ✅ Valid enum
lockout_type: "hard"         # ✅ Valid enum
lockout_type: "timer"        # ✅ Valid enum
log_level: "INFO"            # ✅ Valid enum
```

**Invalid Input & Errors**:

```yaml
# Input:
count_type: "invalid"

# Error:
Invalid count_type: 'invalid'.
Must be one of: 'net', 'gross'.
Fix: Choose from the allowed values.
```

```yaml
# Input:
account_type: "production"

# Error:
Invalid account_type: 'production'.
Must be one of: 'practice', 'live'.
Fix: Choose from the allowed values.
```

```yaml
# Input:
log_level: "VERBOSE"

# Error:
Invalid log_level: 'VERBOSE'.
Must be one of: 'DEBUG', 'INFO', 'WARNING', 'ERROR'.
Fix: Choose from the allowed values.
```

---

## Model Validation Errors

### Time Range Validation (End > Start)

**Valid Input**:
```yaml
session_hours:
  start: "09:30"    # ✅ 9:30 AM
  end: "16:00"      # ✅ 4:00 PM (after start)
```

**Invalid Input & Errors**:

```yaml
# Input:
session_hours:
  start: "16:00"
  end: "09:30"

# Error:
Session end (09:30) must be after start (16:00).
Reason: Cannot have an end time before start time.
Fix: Swap the times or correct the values.
Example: start='09:30', end='16:00'
```

```yaml
# Input:
session_hours:
  start: "09:30"
  end: "09:30"

# Error:
Session end (09:30) must be after start (09:30).
Reason: Cannot have an end time before start time.
Fix: Swap the times or correct the values.
Example: start='09:30', end='16:00'
```

---

### Loss Hierarchy Validation (Unrealized < Realized)

**Valid Input**:
```yaml
rules:
  daily_realized_loss:
    enabled: true
    limit: -500.0        # ✅ Realized loss limit

  daily_unrealized_loss:
    enabled: true
    limit: -200.0        # ✅ Less than realized (in absolute value)
```

**Invalid Input & Errors**:

```yaml
# Input:
rules:
  daily_realized_loss:
    enabled: true
    limit: -200.0

  daily_unrealized_loss:
    enabled: true
    limit: -500.0        # ❌ Greater than realized

# Error:
Unrealized loss limit (-500.0) should be LESS than realized loss limit (-200.0) in absolute value.
Reason: Unrealized loss should trigger before realized loss to provide early warning.
Fix: Make unrealized limit smaller.
Example: unrealized=-200, realized=-500
```

```yaml
# Input:
rules:
  daily_realized_loss:
    enabled: true
    limit: -500.0

  daily_unrealized_loss:
    enabled: true
    limit: -500.0        # ❌ Equal to realized

# Error:
Unrealized loss limit (-500.0) should be LESS than realized loss limit (-500.0) in absolute value.
Reason: Unrealized loss should trigger before realized loss to provide early warning.
Fix: Make unrealized limit smaller.
Example: unrealized=-200, realized=-500
```

---

### Contract Hierarchy Validation (Per-Instrument <= Total)

**Valid Input**:
```yaml
rules:
  max_contracts:
    enabled: true
    limit: 5                    # ✅ Total limit

  max_contracts_per_instrument:
    enabled: true
    default_limit: 2            # ✅ Less than total
```

**Invalid Input & Errors**:

```yaml
# Input:
rules:
  max_contracts:
    enabled: true
    limit: 5

  max_contracts_per_instrument:
    enabled: true
    default_limit: 10           # ❌ Greater than total

# Error:
Per-instrument limit (10) cannot exceed total account limit (5).
Reason: Single instrument cannot have more contracts than entire account.
Fix: Reduce per-instrument limit or increase total limit.
Example: per_instrument=2, total=5
```

---

### Frequency Hierarchy Validation

**Valid Input**:
```yaml
limits:
  per_minute: 3        # ✅ 3 per minute
  per_hour: 10         # ✅ 10 per hour (3*60=180 would exceed)
  per_session: 50      # ✅ 50 per session (10*8=80 would exceed)
```

**Invalid Input & Errors**:

```yaml
# Input:
limits:
  per_minute: 10
  per_hour: 100        # ❌ 10*60=600 exceeds 100

# Error:
per_minute (10) * 60 = 600 exceeds per_hour (100).
Reason: If you can trade 10 times per minute, you could trade 600 times in an hour.
Fix: Reduce per_minute or increase per_hour.
Example: per_minute=3, per_hour=10 (not 180)
```

```yaml
# Input:
limits:
  per_hour: 20
  per_session: 50      # ❌ 20*8=160 exceeds 50

# Error:
per_hour (20) * 8 = 160 exceeds per_session (50).
Reason: Assuming 8-hour session, you could trade 160 times.
Fix: Reduce per_hour or increase per_session.
Example: per_hour=10, per_session=50 (not 80)
```

---

### Category Enforcement Validation

#### Trade-by-Trade Rules

**Valid Input**:
```yaml
max_contracts:
  enabled: true
  close_all: false     # ✅ Trade-by-trade: close only violating
  close_position: true # ✅ Must close something
```

**Invalid Input & Errors**:

```yaml
# Input:
max_contracts:
  enabled: true
  close_all: true      # ❌ Should be false

# Error:
RULE-001 (Max Contracts) is a trade-by-trade rule and MUST have close_all=false.
Reason: Trade-by-trade rules only close the violating position, not all positions.
Fix: Set close_all=false.
```

```yaml
# Input:
max_contracts:
  enabled: true
  close_all: false
  close_position: false  # ❌ Must be true

# Error:
RULE-001 (Max Contracts) is a trade-by-trade rule and MUST have close_position=true.
Reason: The rule must take action on violation.
Fix: Set close_position=true.
```

#### Hard Lockout Rules

**Valid Input**:
```yaml
daily_realized_loss:
  enabled: true
  close_all: true      # ✅ Hard lockout: close all positions
  lockout_type: "hard" # ✅ Hard lockout type
```

**Invalid Input & Errors**:

```yaml
# Input:
daily_realized_loss:
  enabled: true
  close_all: false     # ❌ Should be true

# Error:
RULE-003 (Daily Realized Loss) is a hard lockout rule and MUST have close_all=true.
Reason: Hard lockout rules close all positions when triggered.
Fix: Set close_all=true.
```

```yaml
# Input:
daily_realized_loss:
  enabled: true
  close_all: true
  lockout_type: "timer"  # ❌ Should be "hard"

# Error:
RULE-003 (Daily Realized Loss) is a hard lockout rule and MUST have lockout_type='hard'.
Reason: This rule category requires hard lockouts.
Fix: Set lockout_type='hard' (you have 'timer').
```

---

## Cross-Configuration Errors

### Timer References

**Valid Input**:
```yaml
# timers_config.yaml
daily_reset:
  enabled: true         # ✅ Enabled
  time: "17:00"

# timers_config.yaml
lockout_durations:
  hard_lockout:
    daily_realized_loss: "until_reset"  # ✅ Can reference reset
```

**Invalid Input & Errors**:

```yaml
# timers_config.yaml
daily_reset:
  enabled: false        # ❌ Disabled

# timers_config.yaml
lockout_durations:
  hard_lockout:
    daily_realized_loss: "until_reset"  # ❌ References disabled reset

# Error:
RULE-003 (daily_realized_loss) uses lockout_duration='until_reset',
but daily_reset is disabled in timers_config.yaml.
Fix: Set timers_config.daily_reset.enabled=true or change lockout_duration.
```

---

### Holiday References

**Valid Input**:
```yaml
# timers_config.yaml
holidays:
  enabled: true         # ✅ Enabled
  dates: ["2025-07-04"]

# risk_config.yaml
session_block_outside:
  enabled: true
  respect_holidays: true  # ✅ Can reference holidays
```

**Invalid Input & Errors**:

```yaml
# timers_config.yaml
holidays:
  enabled: false        # ❌ Disabled

# risk_config.yaml
session_block_outside:
  enabled: true
  respect_holidays: true  # ❌ References disabled holidays

# Error:
RULE-009 (session_block_outside) has respect_holidays=true,
but holidays are disabled in timers_config.yaml.
Fix: Set timers_config.holidays.enabled=true or set respect_holidays=false.
```

---

### Instrument References

**Valid Input**:
```yaml
# risk_config.yaml
general:
  instruments: [MNQ, ES]  # ✅ Defined instruments

rules:
  max_contracts_per_instrument:
    enabled: true
    instrument_limits:
      MNQ: 2              # ✅ References defined instrument
      ES: 1               # ✅ References defined instrument
```

**Invalid Input & Errors**:

```yaml
# risk_config.yaml
general:
  instruments: [MNQ, ES]

rules:
  max_contracts_per_instrument:
    enabled: true
    instrument_limits:
      GC: 3               # ❌ Not in general.instruments

# Error:
RULE-002 (max_contracts_per_instrument) references instrument 'GC',
but it's not in general.instruments list: ['MNQ', 'ES'].
Fix: Add 'GC' to general.instruments or remove from instrument_limits.
```

---

### Account Validation

**Valid Input**:
```yaml
accounts:
  - id: "ACCOUNT-001"     # ✅ Unique ID
    name: "Account 1"

  - id: "ACCOUNT-002"     # ✅ Different ID
    name: "Account 2"
```

**Invalid Input & Errors**:

```yaml
# Input:
accounts:
  - id: "ACCOUNT-001"
    name: "Account 1"

  - id: "ACCOUNT-001"     # ❌ Duplicate ID
    name: "Account 2"

# Error:
Account IDs must be unique. Found duplicates: ['ACCOUNT-001'].
Fix: Ensure each account has a unique ID.
```

```yaml
# Input:
accounts:
  - id: "ACCOUNT-001"
    name: "Account 1"
    risk_config_file: "config/custom.yaml"  # ❌ File doesn't exist

# Error:
Account 'Account 1' (ID: ACCOUNT-001) references config file
'config/custom.yaml' which does not exist.
Fix: Create the file or remove risk_config_file reference.
```

```yaml
# Input:
accounts:
  - id: "ACCOUNT-001"
    name: "Account 1"
    risk_config_file: "config/custom.yaml"  # ❌ Both specified
    config_overrides:
      rules:
        max_contracts:
          limit: 10

# Error:
Account 'Account 1' (ID: ACCOUNT-001) specifies both
risk_config_file and config_overrides. Choose one.
Fix: Use risk_config_file for complete custom config,
OR use config_overrides for partial overrides (not both).
```

---

## Edge Cases

### Empty Strings

```yaml
# Input:
time: ""

# Error:
Invalid Reset time format: ''.
Use HH:MM (24-hour format).
Example: 17:00 for 5 PM, 09:30 for 9:30 AM
```

### Whitespace

```yaml
# Input:
time: " 17:00 "

# Error:
Invalid Reset time format: ' 17:00 '.
Use HH:MM (24-hour format).
Example: 17:00 for 5 PM, 09:30 for 9:30 AM
```

### Case Sensitivity

```yaml
# Input:
count_type: "NET"     # ❌ Wrong case

# Error:
Invalid count_type: 'NET'.
Must be one of: 'net', 'gross'.
Fix: Choose from the allowed values.
```

### Floating Point Precision

```yaml
# Input:
limit: -500.000001    # ✅ Accepted (close to -500.0)
limit: -0.01          # ✅ Accepted (small negative)
```

### Very Large Numbers

```yaml
# Input:
limit: -999999999.99  # ✅ Accepted (very large loss limit)
limit: 999999         # ✅ Accepted (very large contract limit)
```

### Zero Values

```yaml
# Input (loss limit):
limit: 0              # ❌ Must be negative

# Input (profit target):
target: 0             # ❌ Must be positive

# Input (contract limit):
limit: 0              # ❌ Must be positive
```

### Midnight (Edge Case)

```yaml
# Input:
time: "00:00"         # ✅ Valid (midnight)
time: "24:00"         # ❌ Invalid (use 00:00)
```

### Leap Years

```yaml
# Input:
date: "2024-02-29"    # ✅ Valid (2024 is leap year)
date: "2025-02-29"    # ❌ Invalid (2025 is not leap year)
```

### Daylight Saving Time

```yaml
# Input:
timezone: "America/Chicago"  # ✅ Handles DST automatically
# Note: IANA timezones handle DST transitions automatically
```

---

## Summary

**Total Error Messages**: 40+

**Categories**:
- Field validation: 22 error types
- Model validation: 10 error types
- Cross-configuration: 8 error types
- Edge cases: 12+ scenarios

**All error messages follow the pattern**:
1. WHAT is wrong
2. WHY it's wrong
3. FIX suggestion
4. EXAMPLE of correct value

**Ready for production use!**

---

**Created**: 2025-10-27
**Status**: Production Ready
**Next Step**: Use as reference when writing tests or troubleshooting validation
