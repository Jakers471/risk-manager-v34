# Risk Configuration Schema (All 13 Rules)

**Document Type**: Unified Configuration Specification
**Created**: 2025-10-25
**Researcher**: Wave 3 Researcher 5 - Configuration System Specification Unification
**Status**: PRODUCTION READY

---

## Executive Summary

This document defines the **complete risk configuration schema** for all 13 risk rules in Risk Manager V34. Every rule is individually configurable via YAML.

**CRITICAL PRINCIPLE**: **ALL risk parameters MUST be configurable**. Loss limits, profit targets, contract limits, frequencies, etc. are NOT hardcoded.

---

## Table of Contents

1. [Configuration Structure](#1-configuration-structure)
2. [General Settings](#2-general-settings)
3. [Category 1: Trade-by-Trade Rules](#3-category-1-trade-by-trade-rules)
4. [Category 2: Timer/Cooldown Rules](#4-category-2-timercooldown-rules)
5. [Category 3: Hard Lockout Rules](#5-category-3-hard-lockout-rules)
6. [Category 4: Automation](#6-category-4-automation)
7. [Validation Rules](#7-validation-rules)
8. [Example Configurations](#8-example-configurations)

---

## 1. Configuration Structure

**File**: `config/risk_config.yaml`

```yaml
# ==============================================================================
# RISK MANAGER V34 - RISK CONFIGURATION
# ==============================================================================

general:
  # General settings (instruments, timezone, logging, database)

rules:
  # Trade-by-Trade Rules (6 rules)
  max_contracts:                   # RULE-001
  max_contracts_per_instrument:    # RULE-002
  daily_unrealized_loss:           # RULE-004
  max_unrealized_profit:           # RULE-005
  no_stop_loss_grace:              # RULE-008
  symbol_blocks:                   # RULE-011

  # Timer/Cooldown Rules (2 rules)
  trade_frequency_limit:           # RULE-006
  cooldown_after_loss:             # RULE-007

  # Hard Lockout Rules (4 rules)
  daily_realized_loss:             # RULE-003
  daily_realized_profit:           # RULE-013
  session_block_outside:           # RULE-009
  auth_loss_guard:                 # RULE-010

  # Automation (1 rule)
  trade_management:                # RULE-012
```

---

## 2. General Settings

### 2.1 Schema

```yaml
general:
  # Instruments to monitor
  instruments:
    - MNQ                          # E-mini NASDAQ
    - ES                           # E-mini S&P 500
    # Add any symbols you trade

  # Timezone (IANA timezone string)
  timezone: "America/Chicago"      # Central Time

  # Logging
  logging:
    level: "INFO"                  # DEBUG, INFO, WARNING, ERROR
    log_to_file: true
    log_directory: "data/logs/"
    max_log_size_mb: 100
    log_retention_days: 30

  # Database
  database:
    path: "data/risk_state.db"
    backup_enabled: true
    backup_interval_hours: 24
    max_backups: 7

  # Notifications (optional)
  notifications:
    discord:
      enabled: false
      webhook_url: ""              # Discord webhook URL

    telegram:
      enabled: false
      bot_token: ""                # Telegram bot token
      chat_id: ""                  # Telegram chat ID
```

### 2.2 Validation Rules

1. **instruments**:
   - MUST be non-empty list of strings
   - Each instrument should be valid symbol
   - Recommended: Validate against SDK symbol list

2. **timezone**:
   - MUST be valid IANA timezone
   - Examples: `America/New_York`, `America/Chicago`, `Europe/London`

3. **logging.level**:
   - MUST be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`

---

## 3. Category 1: Trade-by-Trade Rules

**Characteristic**: Close only that position, NO lockout, immediate retry allowed

### 3.1 RULE-001: Max Contracts

```yaml
max_contracts:
  enabled: true                    # Enable/disable rule

  # Contract limit
  limit: 5                         # Max net contracts (all instruments)

  # Counting method
  count_type: "net"                # "net" or "gross"
                                   # net: long - short (e.g., 5 long - 3 short = 2)
                                   # gross: long + short (e.g., 5 long + 3 short = 8)

  # Enforcement
  close_all: false                 # MUST be false (trade-by-trade)
  close_position: true             # Close violating position
  reduce_to_limit: false           # Alternative: reduce to limit instead
```

**Validation**:
- `limit` MUST be > 0
- `count_type` MUST be "net" or "gross"
- `close_all` MUST be false (trade-by-trade category)

---

### 3.2 RULE-002: Max Contracts Per Instrument

```yaml
max_contracts_per_instrument:
  enabled: true                    # Enable/disable rule

  # Default limit (applies to all instruments not specified)
  default_limit: 3                 # Max 3 contracts per instrument

  # Per-instrument overrides
  instrument_limits:
    MNQ: 2                         # Max 2 MNQ contracts
    ES: 1                          # Max 1 ES contract
    GC: 3                          # Max 3 GC contracts
    # Add more as needed

  # Enforcement
  close_all: false                 # MUST be false (trade-by-trade)
  close_position: true             # Close violating position (that instrument only)
```

**Validation**:
- `default_limit` MUST be > 0
- All `instrument_limits` values MUST be > 0
- Instrument keys should match `general.instruments` list
- `close_all` MUST be false (trade-by-trade category)

---

### 3.3 RULE-004: Daily Unrealized Loss

```yaml
daily_unrealized_loss:
  enabled: true                    # Enable/disable rule

  # Loss limit (per position)
  limit: -200.0                    # Max floating loss per position ($)

  # Monitoring
  check_interval_seconds: 10       # Check position P&L every 10s

  # Enforcement
  close_all: false                 # MUST be false (trade-by-trade)
  close_position: true             # Close only the losing position
```

**Validation**:
- `limit` MUST be < 0 (negative for losses)
- `check_interval_seconds` MUST be >= 1
- `close_all` MUST be false (trade-by-trade category)

---

### 3.4 RULE-005: Max Unrealized Profit (Profit Target)

```yaml
max_unrealized_profit:
  enabled: true                    # Enable/disable rule

  # Profit target (per position)
  target: 500.0                    # Take profit at $500 per position

  # Monitoring
  check_interval_seconds: 5        # Check frequently for profit targets

  # Enforcement
  close_all: false                 # MUST be false (trade-by-trade)
  close_position: true             # Close only that winning position
```

**Validation**:
- `target` MUST be > 0 (positive for profits)
- `check_interval_seconds` MUST be >= 1
- `close_all` MUST be false (trade-by-trade category)

---

### 3.5 RULE-008: Stop-Loss Enforcement

```yaml
no_stop_loss_grace:
  enabled: true                    # Enable/disable rule

  # Time requirements
  require_within_seconds: 60       # Must place stop within 60s of opening
  grace_period_seconds: 300        # 5 min grace before enforcement

  # Enforcement
  close_all: false                 # MUST be false (trade-by-trade)
  close_position: true             # Close position without stop
```

**Validation**:
- `require_within_seconds` MUST be > 0
- `grace_period_seconds` MUST be > 0
- `grace_period_seconds` SHOULD be >= `require_within_seconds`
- `close_all` MUST be false (trade-by-trade category)

---

### 3.6 RULE-011: Symbol Blocks (Blacklist)

```yaml
symbol_blocks:
  enabled: false                   # Disabled by default

  # Blacklisted symbols
  blocked_symbols:
    # - ES                         # Example: block ES trading
    # - NQ                         # Example: block NQ trading

  # Enforcement
  close_all: false                 # MUST be false (trade-by-trade)
  close_position: true             # Close position in blocked symbol
  close_immediately: true          # Close without warning
```

**Validation**:
- `blocked_symbols` MUST be list of strings (can be empty)
- Symbols should exist in `general.instruments` (warn if not)
- `close_all` MUST be false (trade-by-trade category)

---

## 4. Category 2: Timer/Cooldown Rules

**Characteristic**: Close all positions, temporary lockout, auto-unlock

### 4.1 RULE-006: Trade Frequency Limit

```yaml
trade_frequency_limit:
  enabled: true                    # Enable/disable rule

  # Frequency limits
  limits:
    per_minute: 3                  # Max 3 trades per minute
    per_hour: 10                   # Max 10 trades per hour
    per_session: 50                # Max 50 trades per session

  # Cooldown durations (from timers_config.yaml)
  # Defined in: lockout_durations.timer_cooldown.trade_frequency

  # Enforcement
  close_all: true                  # MUST be true (timer/cooldown category)
  cancel_orders: true              # Cancel all orders
  lockout_type: "timer"            # MUST be "timer"
```

**Validation**:
- All limit values MUST be > 0
- `per_minute` <= `per_hour` <= `per_session` (logical hierarchy)
- `close_all` MUST be true (timer/cooldown category)
- `lockout_type` MUST be "timer"

---

### 4.2 RULE-007: Cooldown After Loss

```yaml
cooldown_after_loss:
  enabled: true                    # Enable/disable rule

  # Loss threshold
  loss_threshold: -100.0           # Trigger on $100 loss in single trade

  # Cooldown duration (from timers_config.yaml)
  # Defined in: lockout_durations.timer_cooldown.cooldown_after_loss

  # Enforcement
  close_all: true                  # MUST be true (timer/cooldown category)
  cancel_orders: true              # Cancel all orders
  lockout_type: "timer"            # MUST be "timer"
```

**Validation**:
- `loss_threshold` MUST be < 0 (negative for losses)
- `close_all` MUST be true (timer/cooldown category)
- `lockout_type` MUST be "timer"

---

## 5. Category 3: Hard Lockout Rules

**Characteristic**: Close all positions, hard lockout until condition met

### 5.1 RULE-003: Daily Realized Loss

```yaml
daily_realized_loss:
  enabled: true                    # Enable/disable rule

  # Loss limit
  limit: -500.0                    # Max daily loss (dollars)

  # Reset configuration (from timers_config.yaml)
  # Reset time: daily_reset.time
  # Timezone: daily_reset.timezone
  # Lockout duration: lockout_durations.hard_lockout.daily_realized_loss

  # Enforcement
  close_all: true                  # MUST be true (hard lockout category)
  cancel_orders: true              # Cancel all orders
  lockout_type: "hard"             # MUST be "hard"
```

**Validation**:
- `limit` MUST be < 0 (negative for losses)
- `close_all` MUST be true (hard lockout category)
- `lockout_type` MUST be "hard"
- Should be less strict than `daily_unrealized_loss.limit` (if both enabled)

---

### 5.2 RULE-013: Daily Realized Profit

```yaml
daily_realized_profit:
  enabled: true                    # Enable/disable rule

  # Profit target
  target: 1000.0                   # Daily profit target (dollars)

  # Reset configuration (from timers_config.yaml)
  # Reset time: daily_reset.time
  # Timezone: daily_reset.timezone
  # Lockout duration: lockout_durations.hard_lockout.daily_realized_profit

  # Message
  message: "Daily profit target reached! Good job! See you tomorrow."

  # Enforcement
  close_all: true                  # MUST be true (hard lockout category)
  cancel_orders: true              # Stop further trading
  lockout_type: "hard"             # MUST be "hard"
```

**Validation**:
- `target` MUST be > 0 (positive for profits)
- `close_all` MUST be true (hard lockout category)
- `lockout_type` MUST be "hard"
- `message` is optional string

---

### 5.3 RULE-009: Session Block Outside

```yaml
session_block_outside:
  enabled: true                    # Enable/disable rule

  # Session configuration (from timers_config.yaml)
  # Session hours: session_hours.start / .end
  # Allowed days: session_hours.allowed_days
  # Timezone: session_hours.timezone
  # Lockout duration: lockout_durations.hard_lockout.session_block_outside

  # Holiday check
  respect_holidays: true           # Check holidays from timers_config.yaml

  # Enforcement
  close_all: true                  # MUST be true (hard lockout category)
  cancel_orders: true              # Cancel all orders
  lockout_type: "hard"             # MUST be "hard"
```

**Validation**:
- `respect_holidays` MUST be boolean
- If true, `timers_config.yaml` MUST have holidays defined
- `close_all` MUST be true (hard lockout category)
- `lockout_type` MUST be "hard"

---

### 5.4 RULE-010: Auth Loss Guard

```yaml
auth_loss_guard:
  enabled: true                    # Enable/disable rule

  # Monitoring
  check_interval_seconds: 30       # Check canTrade every 30s

  # Reason
  reason: "API canTrade status is false - account disabled"

  # Lockout duration (from timers_config.yaml)
  # lockout_durations.hard_lockout.auth_loss_guard = "permanent"

  # Enforcement
  close_all: true                  # MUST be true (hard lockout category)
  cancel_orders: true              # Cancel all orders
  lockout_type: "hard"             # MUST be "hard"
  lockout_permanently: true        # MUST be true (requires admin unlock)
```

**Validation**:
- `check_interval_seconds` MUST be >= 10
- `close_all` MUST be true (hard lockout category)
- `lockout_type` MUST be "hard"
- `lockout_permanently` MUST be true
- Lockout duration in timers_config MUST be "permanent"

---

## 6. Category 4: Automation

### 6.1 RULE-012: Trade Management

```yaml
trade_management:
  enabled: false                   # Disabled by default (advanced feature)

  # Auto Breakeven
  auto_breakeven:
    enabled: true
    profit_threshold_ticks: 4      # Move stop to breakeven after 4 ticks profit
    offset_ticks: 1                # Offset from breakeven (safety margin)

  # Trailing Stop
  trailing_stop:
    enabled: true
    trail_ticks: 4                 # Trail by 4 ticks
    activation_profit_ticks: 8     # Activate trail after 8 ticks profit

  # Note: This is automation, not risk enforcement
```

**Validation**:
- All tick values MUST be > 0
- `activation_profit_ticks` SHOULD be >= `profit_threshold_ticks`
- This is automation, not enforcement (different category)

---

## 7. Validation Rules

### 7.1 Category Consistency

**Trade-by-Trade Rules** MUST have:
```yaml
close_all: false
close_position: true
# NO lockout_type field
```

**Timer/Cooldown Rules** MUST have:
```yaml
close_all: true
cancel_orders: true
lockout_type: "timer"
```

**Hard Lockout Rules** MUST have:
```yaml
close_all: true
cancel_orders: true
lockout_type: "hard"
```

### 7.2 Cross-Rule Validation

1. **Loss Limits**:
   - If both enabled: `daily_unrealized_loss.limit` > `daily_realized_loss.limit`
   - Reason: Unrealized should trigger before realized

2. **Contract Limits**:
   - If both enabled: `max_contracts_per_instrument.default_limit` <= `max_contracts.limit`
   - Reason: Per-instrument cannot exceed account total

3. **Frequency Limits**:
   - `trade_frequency_limit.limits.per_minute` <= `.per_hour` <= `.per_session`
   - Reason: Logical hierarchy

4. **Profit Targets**:
   - If both enabled: `max_unrealized_profit.target` <= `daily_realized_profit.target`
   - Reason: Per-position target should be less than daily total

### 7.3 Reference Validation

**Timers Configuration Required**:
- Daily loss/profit rules require `daily_reset` configuration
- Session block requires `session_hours` configuration
- Lockout durations defined in `timers_config.yaml`

---

## 8. Example Configurations

### 8.1 Conservative Trader (Strict Limits)

```yaml
general:
  instruments: [MNQ, ES]
  timezone: "America/Chicago"

rules:
  max_contracts:
    enabled: true
    limit: 2                       # Very conservative

  daily_realized_loss:
    enabled: true
    limit: -200.0                  # Small loss limit

  daily_realized_profit:
    enabled: true
    target: 400.0                  # Take smaller profits

  trade_frequency_limit:
    enabled: true
    limits:
      per_minute: 2
      per_hour: 5
      per_session: 20
```

### 8.2 Aggressive Trader (Loose Limits)

```yaml
general:
  instruments: [MNQ, ES, GC, NQ]
  timezone: "America/New_York"

rules:
  max_contracts:
    enabled: true
    limit: 10                      # More contracts

  daily_realized_loss:
    enabled: true
    limit: -1000.0                 # Larger loss limit

  daily_realized_profit:
    enabled: true
    target: 2000.0                 # Higher profit target

  trade_frequency_limit:
    enabled: true
    limits:
      per_minute: 5
      per_hour: 20
      per_session: 100
```

### 8.3 Evaluation Account (TopstepX Rules)

```yaml
general:
  instruments: [MNQ, ES]
  timezone: "America/Chicago"

rules:
  max_contracts:
    enabled: true
    limit: 5

  max_contracts_per_instrument:
    enabled: true
    instrument_limits:
      MNQ: 2
      ES: 1

  daily_realized_loss:
    enabled: true
    limit: -500.0

  daily_unrealized_loss:
    enabled: true
    limit: -150.0

  session_block_outside:
    enabled: true
    respect_holidays: true
```

### 8.4 Minimal Configuration (Testing)

```yaml
general:
  instruments: [MNQ]
  timezone: "America/Chicago"

rules:
  max_contracts:
    enabled: true
    limit: 5

  daily_realized_loss:
    enabled: true
    limit: -500.0

  # All other rules disabled by default
```

---

## Summary

### Key Takeaways

1. **13 Rules, 3 Categories**: Trade-by-trade, Timer/Cooldown, Hard Lockout
2. **Everything Configurable**: All limits, thresholds, targets are YAML-based
3. **Category Consistency**: Each category has strict enforcement patterns
4. **Cross-Validation**: Rules checked against each other for logical consistency
5. **Timer Integration**: Hard lockouts and cooldowns reference `timers_config.yaml`

### Configuration Files

- **risk_config.yaml**: Risk rules configuration (THIS FILE)
- **timers_config.yaml**: Timing configuration (reset times, lockout durations)
- **accounts.yaml**: API credentials and account mappings

### Validation Summary

- **Type Validation**: Pydantic enforces types (int, float, bool, str)
- **Range Validation**: Limits must be positive/negative as appropriate
- **Category Validation**: Enforcement patterns match rule category
- **Cross-Validation**: Rules checked against each other
- **Reference Validation**: Timer references checked

---

**Document Complete**
**Created**: 2025-10-25
**Status**: PRODUCTION READY
