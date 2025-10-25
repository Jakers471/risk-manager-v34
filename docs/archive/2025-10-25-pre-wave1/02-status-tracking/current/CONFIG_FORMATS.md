# Configuration Formats - Complete YAML Examples

**Date**: 2025-10-23
**Purpose**: Official YAML configuration format for all 13 risk rules

---

## 📁 Configuration Files

```
config/
├── accounts.yaml           # API credentials
├── risk_config.yaml        # Risk rule settings (THIS FILE)
└── holidays.yaml           # Market holidays
```

---

## 🎯 Complete Risk Config (risk_config.yaml)

**File**: `config/risk_config.yaml`

```yaml
# ==============================================================================
# RISK MANAGER V34 - CONFIGURATION
# ==============================================================================
# Last Updated: 2025-10-23
#
# RULE CATEGORIES:
#   Trade-by-Trade: Close only that position, no lockout
#   Timer/Cooldown: Close all + temporary lockout
#   Hard Lockout:   Close all + lockout until reset/condition
# ==============================================================================

# ==============================================================================
# GENERAL SETTINGS
# ==============================================================================
general:
  # Instruments to monitor
  instruments:
    - MNQ
    - ES

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

# ------------------------------------------------------------------------------
# RULE-001: MAX CONTRACTS
# ------------------------------------------------------------------------------
# Purpose: Cap net contracts across ALL instruments
# Trigger: Position update
# Action:  Close position that caused breach (NOT all positions)
# Lockout: None
# ------------------------------------------------------------------------------
max_contracts:
  enabled: true
  limit: 5                    # Max net contracts (all instruments combined)
  count_type: "net"           # "net" (5 long - 3 short = 2 net)
                              # "gross" (5 long + 3 short = 8 gross)

  # Enforcement options
  close_all: false            # Close all? NO - trade-by-trade
  close_position: true        # Close the position that caused breach
  reduce_to_limit: false      # Alternative: reduce position to limit

# ------------------------------------------------------------------------------
# RULE-002: MAX CONTRACTS PER INSTRUMENT
# ------------------------------------------------------------------------------
# Purpose: Cap contracts per specific instrument
# Trigger: Position update
# Action:  Close position in that instrument only (NOT all positions)
# Lockout: None
# ------------------------------------------------------------------------------
max_contracts_per_instrument:
  enabled: true
  default_limit: 3            # Default limit per instrument

  # Per-instrument overrides
  instrument_limits:
    MNQ: 2                    # Max 2 MNQ contracts
    ES: 1                     # Max 1 ES contract
    # NQ: 3                   # Add more as needed

  # Enforcement
  close_all: false            # Close all? NO - trade-by-trade
  close_position: true        # Close position in that instrument only

# ------------------------------------------------------------------------------
# RULE-004: DAILY UNREALIZED LOSS
# ------------------------------------------------------------------------------
# Purpose: Prevent excessive floating losses on single position
# Trigger: Position P&L monitoring
# Action:  Close that position only (NOT all positions)
# Lockout: None
# ------------------------------------------------------------------------------
daily_unrealized_loss:
  enabled: true
  limit: -200.0               # Max floating loss per position ($)

  # Monitoring
  check_interval_seconds: 10  # How often to check position P&L

  # Enforcement
  close_all: false            # Close all? NO - trade-by-trade
  close_position: true        # Close only the losing position

# ------------------------------------------------------------------------------
# RULE-005: MAX UNREALIZED PROFIT (Profit Target Per Position)
# ------------------------------------------------------------------------------
# Purpose: Take profit on winning positions automatically
# Trigger: Position P&L monitoring
# Action:  Close that winning position only (NOT all positions)
# Lockout: None
# ------------------------------------------------------------------------------
max_unrealized_profit:
  enabled: true
  target: 500.0               # Take profit at $500 per position

  # Monitoring
  check_interval_seconds: 5   # Check frequently for profit targets

  # Enforcement
  close_all: false            # Close all? NO - trade-by-trade
  close_position: true        # Close only that winning position

# ------------------------------------------------------------------------------
# RULE-008: STOP-LOSS ENFORCEMENT
# ------------------------------------------------------------------------------
# Purpose: Enforce stop-loss placement within time limit
# Trigger: New position opened without stop
# Action:  Close that position if no stop placed (NOT all positions)
# Lockout: None
# ------------------------------------------------------------------------------
no_stop_loss_grace:
  enabled: true
  require_within_seconds: 60  # Must place stop within 60s of opening
  grace_period_seconds: 300   # 5 min grace before enforcement

  # Enforcement
  close_all: false            # Close all? NO - trade-by-trade
  close_position: true        # Close only the position without stop

# ------------------------------------------------------------------------------
# RULE-011: SYMBOL BLOCKS (Blacklist)
# ------------------------------------------------------------------------------
# Purpose: Prevent trading specific symbols
# Trigger: Any event involving blocked symbol
# Action:  Close position in that symbol immediately (NOT all positions)
# Lockout: None
# ------------------------------------------------------------------------------
symbol_blocks:
  enabled: false              # Disabled by default

  # Blacklisted symbols (close immediately on detection)
  blocked_symbols:
    # - ES                    # Example: block ES trading
    # - NQ                    # Example: block NQ trading

  # Enforcement
  close_all: false            # Close all? NO - trade-by-trade
  close_position: true        # Close position in blocked symbol only
  close_immediately: true     # Close without warning

# ==============================================================================
# CATEGORY 2: TIMER/COOLDOWN RULES
# (Close all + temporary lockout with countdown)
# ==============================================================================

# ------------------------------------------------------------------------------
# RULE-006: TRADE FREQUENCY LIMIT
# ------------------------------------------------------------------------------
# Purpose: Prevent overtrading
# Trigger: Trade execution count
# Action:  Close all + cooldown timer
# Lockout: Temporary (60s / 30min / 1hr)
# ------------------------------------------------------------------------------
trade_frequency_limit:
  enabled: true

  # Frequency limits
  limits:
    per_minute: 3             # Max 3 trades per minute
    per_hour: 10              # Max 10 trades per hour
    per_session: 50           # Max 50 trades per session

  # Cooldown durations (seconds)
  cooldowns:
    per_minute_breach: 60     # 1 minute cooldown
    per_hour_breach: 1800     # 30 minute cooldown
    per_session_breach: 3600  # 1 hour cooldown

  # Enforcement
  close_all: true             # Close all positions
  cancel_orders: true         # Cancel all orders
  lockout_type: "timer"       # Temporary lockout with countdown

# ------------------------------------------------------------------------------
# RULE-007: COOLDOWN AFTER LOSS
# ------------------------------------------------------------------------------
# Purpose: Force break after emotional loss
# Trigger: Single trade loss exceeds threshold
# Action:  Close all + cooldown timer
# Lockout: Temporary (configurable minutes)
# ------------------------------------------------------------------------------
cooldown_after_loss:
  enabled: true
  loss_threshold: -100.0      # Trigger on $100 loss in single trade
  cooldown_minutes: 15        # Force 15-minute break

  # Enforcement
  close_all: true             # Close all positions
  cancel_orders: true         # Cancel all orders
  lockout_type: "timer"       # Temporary lockout with countdown

# ==============================================================================
# CATEGORY 3: HARD LOCKOUT RULES
# (Close all + lockout until reset/condition)
# ==============================================================================

# ------------------------------------------------------------------------------
# RULE-003: DAILY REALIZED LOSS
# ------------------------------------------------------------------------------
# Purpose: Hard stop on daily losses
# Trigger: Trade execution (realized P&L)
# Action:  Close all + lock until reset time
# Lockout: Hard (until 5 PM or admin override)
# ------------------------------------------------------------------------------
daily_realized_loss:
  enabled: true
  limit: -500.0               # Max daily loss (dollars)
  reset_time: "17:00"         # 5:00 PM EST
  timezone: "America/New_York"

  # Enforcement
  close_all: true             # Close all positions
  cancel_orders: true         # Cancel all orders
  lockout_type: "hard"        # Hard lockout until reset
  lockout_until_reset: true   # Lock until reset_time

# ------------------------------------------------------------------------------
# RULE-013: DAILY REALIZED PROFIT (NEW!)
# ------------------------------------------------------------------------------
# Purpose: Take profit and stop trading for the day
# Trigger: Trade execution (realized P&L)
# Action:  Close all + lock until reset time
# Lockout: Hard (until 5 PM or admin override)
# ------------------------------------------------------------------------------
daily_realized_profit:
  enabled: true
  target: 1000.0              # Daily profit target (dollars)
  reset_time: "17:00"         # 5:00 PM EST
  timezone: "America/New_York"

  # Enforcement
  close_all: true             # Close all positions (lock in profit!)
  cancel_orders: true         # Stop further trading
  lockout_type: "hard"        # Hard lockout until reset
  lockout_until_reset: true   # Lock until reset_time
  message: "Daily profit target reached! Good job! See you tomorrow."

# ------------------------------------------------------------------------------
# RULE-009: SESSION BLOCK OUTSIDE
# ------------------------------------------------------------------------------
# Purpose: Prevent trading outside allowed hours
# Trigger: Time check (continuous)
# Action:  Close all if outside hours + lock until session start
# Lockout: Hard (until session start time)
# ------------------------------------------------------------------------------
session_block_outside:
  enabled: true

  # Allowed trading hours (EST)
  session_hours:
    start: "09:30"            # Market open
    end: "16:00"              # Market close

  # Allowed trading days (0=Monday, 6=Sunday)
  allowed_days: [0, 1, 2, 3, 4]  # Monday-Friday only

  # Holiday check
  respect_holidays: true      # Check holidays.yaml

  # Enforcement
  close_all: true             # Close all positions
  cancel_orders: true         # Cancel all orders
  lockout_type: "hard"        # Hard lockout
  lockout_until_session_start: true

# ------------------------------------------------------------------------------
# RULE-010: AUTH LOSS GUARD
# ------------------------------------------------------------------------------
# Purpose: Monitor canTrade status from API
# Trigger: Account canTrade = false
# Action:  Close all + permanent lock
# Lockout: Hard (permanent - admin only)
# ------------------------------------------------------------------------------
auth_loss_guard:
  enabled: true

  # Monitoring
  check_interval_seconds: 30  # Check canTrade every 30s

  # Enforcement
  close_all: true             # Close all positions
  cancel_orders: true         # Cancel all orders
  lockout_type: "hard"        # Hard lockout
  lockout_permanently: true   # Requires admin unlock
  reason: "API canTrade status is false - account disabled"

# ==============================================================================
# CATEGORY 4: AUTOMATION (Optional)
# ==============================================================================

# ------------------------------------------------------------------------------
# RULE-012: TRADE MANAGEMENT (Automation)
# ------------------------------------------------------------------------------
# Purpose: Automated trade management (not enforcement)
# Action:  Auto-adjust stops/targets
# Lockout: None (automation only)
# ------------------------------------------------------------------------------
trade_management:
  enabled: false              # Disabled by default (advanced feature)

  # Auto Breakeven
  auto_breakeven:
    enabled: true
    profit_threshold_ticks: 4  # Move stop to breakeven after 4 ticks profit
    offset_ticks: 1            # Offset from breakeven (safety margin)

  # Trailing Stop
  trailing_stop:
    enabled: true
    trail_ticks: 4             # Trail by 4 ticks
    activation_profit_ticks: 8 # Activate trail after 8 ticks profit

  # Note: This is automation, not risk enforcement
```

---

## 📄 Account Configuration (accounts.yaml)

**File**: `config/accounts.yaml`

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

## 📅 Holidays Configuration (holidays.yaml)

**File**: `config/holidays.yaml`

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

  2026:
    - "2026-01-01"  # New Year's Day
    # Add 2026 holidays...
```

---

## 🎯 Config Examples by Scenario

### Conservative Trader (Strict Limits)

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
    per_minute: 2             # Slow down trading
    per_hour: 5
    per_session: 20
```

### Aggressive Trader (Loose Limits)

```yaml
max_contracts:
  enabled: true
  limit: 10                   # More contracts

daily_realized_loss:
  enabled: true
  limit: -1000.0              # Larger loss limit

daily_realized_profit:
  enabled: true
  target: 2000.0              # Higher profit target

trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 5             # Faster trading
    per_hour: 20
    per_session: 100
```

### Evaluation Account (TopstepX Rules)

```yaml
max_contracts:
  enabled: true
  limit: 5                    # Typical eval limit

daily_realized_loss:
  enabled: true
  limit: -500.0               # Typical eval loss limit

daily_unrealized_loss:
  enabled: true
  limit: -150.0               # Floating loss limit

max_contracts_per_instrument:
  enabled: true
  instrument_limits:
    MNQ: 2
    ES: 1

session_block_outside:
  enabled: true               # Prevent overnight holds
  session_hours:
    start: "09:30"
    end: "16:00"
```

---

## 🔄 Configuration Loading Process

```python
# How the system loads and uses config

# 1. Load YAML
config = yaml.safe_load(open('config/risk_config.yaml'))

# 2. Create rules
if config['daily_realized_loss']['enabled']:
    rule = DailyRealizedLossRule(
        limit=config['daily_realized_loss']['limit'],
        reset_time=config['daily_realized_loss']['reset_time']
    )
    engine.add_rule(rule)

# 3. Rule evaluates event
result = await rule.evaluate(event, engine)

# 4. If breach:
if result:
    await rule.enforce(event, engine)
```

---

## 📋 Config Validation

**Required fields by rule category**:

### Trade-by-Trade
```yaml
# Minimum required
rule_name:
  enabled: true/false
  limit: <number>             # Threshold value
  close_position: true        # Must be true
  close_all: false            # Must be false
```

### Timer/Cooldown
```yaml
# Minimum required
rule_name:
  enabled: true/false
  threshold: <number>         # Trigger threshold
  cooldown_seconds: <number>  # Timer duration
  close_all: true             # Must be true
  lockout_type: "timer"       # Must be timer
```

### Hard Lockout
```yaml
# Minimum required
rule_name:
  enabled: true/false
  limit: <number>             # Threshold value
  reset_time: "HH:MM"         # Reset time (5 PM)
  close_all: true             # Must be true
  lockout_type: "hard"        # Must be hard
```

---

## 🎯 Summary

**13 Rules, 3 Categories**:

**Trade-by-Trade** (6 rules):
- Close only that position
- No lockout
- Immediate retry allowed

**Timer/Cooldown** (2 rules):
- Close all positions
- Temporary lockout (60s - 1hr)
- Auto-unlock when timer expires

**Hard Lockout** (5 rules):
- Close all positions
- Permanent lockout
- Unlock at reset time or admin override

**All rules are individually configurable via YAML.**

---

**Created**: 2025-10-23
**Updated**: Added RULE-013 (Daily Realized Profit)
**Corrected**: RULE-004, 005, 008 are trade-by-trade
