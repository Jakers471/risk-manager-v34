# Configuration Validation Rules

**Document Type**: Unified Configuration Specification
**Created**: 2025-10-25
**Researcher**: Wave 3 Researcher 5 - Configuration System Specification Unification
**Status**: PRODUCTION READY

---

## Executive Summary

This document defines **comprehensive validation rules** for all Risk Manager V34 configurations. Validation prevents misconfiguration and catches errors before deployment.

**Three Validation Layers**:
1. **Type Validation**: Pydantic enforces types (int, float, str, bool)
2. **Range Validation**: Values within acceptable ranges
3. **Semantic Validation**: Cross-field and cross-rule logic

---

## Table of Contents

1. [Validation Architecture](#1-validation-architecture)
2. [Type Validation Rules](#2-type-validation-rules)
3. [Range Validation Rules](#3-range-validation-rules)
4. [Semantic Validation Rules](#4-semantic-validation-rules)
5. [Cross-Configuration Validation](#5-cross-configuration-validation)
6. [Error Messages](#6-error-messages)
7. [Implementation Examples](#7-implementation-examples)

---

## 1. Validation Architecture

### 1.1 Three-Layer Validation

```
┌─────────────────────────────────────────────┐
│  LAYER 1: Type Validation (Pydantic)       │
│  - int, float, str, bool, list, dict       │
│  - Non-null required fields                 │
│  - Automatic by Pydantic                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  LAYER 2: Range Validation (@field_validator)│
│  - Positive/negative constraints            │
│  - Min/max values                           │
│  - Format patterns (HH:MM, YYYY-MM-DD)     │
│  - Manual validation decorators             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  LAYER 3: Semantic Validation (@model_validator)│
│  - Cross-field logic (end > start)         │
│  - Cross-rule consistency                   │
│  - Reference validation (files exist)       │
│  - Business logic checks                    │
└─────────────────────────────────────────────┘
```

### 1.2 When Validation Runs

**On Load**:
```python
# Validation runs automatically when loading YAML
config = RiskConfig.from_file('config/risk_config.yaml')
# ↑ If validation fails, raises ValidationError
```

**On Hot-Reload**:
```python
# Validation before applying new config
new_config = RiskConfig.from_file('config/risk_config.yaml')
# ↑ Validates first

# If valid, apply
await manager.reload_config(new_config)

# If invalid, keep old config
```

**On Admin Edit**:
```python
# Admin CLI validates before saving
config_editor.save_config(edited_config)
# ↑ Validates before writing to disk
```

---

## 2. Type Validation Rules

### 2.1 Primitive Types

**Pydantic enforces automatically**:

```python
class RuleConfig(BaseModel):
    enabled: bool                        # MUST be true/false
    limit: float                         # MUST be number (int converted to float)
    count_type: str                      # MUST be string
    cooldown_minutes: int                # MUST be integer
    instruments: list[str]               # MUST be list of strings
    config_overrides: dict | None        # MUST be dict or null
```

**Examples**:

```yaml
# Valid
enabled: true                            # boolean
limit: -500.0                            # float
count_type: "net"                        # string
cooldown_minutes: 15                     # int
instruments: [MNQ, ES]                   # list[str]

# Invalid (type errors)
enabled: "yes"                           # ❌ string (expected bool)
limit: "-500"                            # ❌ string (expected float)
cooldown_minutes: 15.5                   # ❌ float (expected int)
instruments: MNQ                         # ❌ string (expected list)
```

### 2.2 Optional vs Required

```python
class RuleConfig(BaseModel):
    enabled: bool                        # REQUIRED (no default)
    limit: float = -500.0                # OPTIONAL (has default)
    description: str | None = None       # OPTIONAL (nullable)
```

**Examples**:

```yaml
# Valid (uses defaults)
rule:
  enabled: true
  # limit: -500.0 (default used)

# Invalid (missing required field)
rule:
  # enabled: ???  ❌ REQUIRED field missing
  limit: -500.0
```

---

## 3. Range Validation Rules

### 3.1 Loss Limits (Must Be Negative)

```python
class DailyRealizedLossConfig(BaseModel):
    limit: float

    @field_validator('limit')
    def limit_must_be_negative(cls, v):
        if v >= 0:
            raise ValueError(
                f"Daily loss limit must be negative (you entered {v}). "
                f"Example: -500.0 means max $500 loss."
            )
        return v
```

**Applies to**:
- `daily_realized_loss.limit` (MUST be < 0)
- `daily_unrealized_loss.limit` (MUST be < 0)
- `cooldown_after_loss.loss_threshold` (MUST be < 0)

### 3.2 Profit Targets (Must Be Positive)

```python
class DailyRealizedProfitConfig(BaseModel):
    target: float

    @field_validator('target')
    def target_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError(
                f"Profit target must be positive (you entered {v}). "
                f"Example: 1000.0 means $1000 profit target."
            )
        return v
```

**Applies to**:
- `daily_realized_profit.target` (MUST be > 0)
- `max_unrealized_profit.target` (MUST be > 0)

### 3.3 Contract Limits (Must Be Positive)

```python
class MaxContractsConfig(BaseModel):
    limit: int

    @field_validator('limit')
    def limit_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError(f"Max contracts must be > 0 (you entered {v})")
        return v
```

**Applies to**:
- `max_contracts.limit` (MUST be > 0)
- `max_contracts_per_instrument.default_limit` (MUST be > 0)
- All `instrument_limits` values (MUST be > 0)

### 3.4 Time Format Validation (HH:MM)

```python
import re

class TimingConfig(BaseModel):
    time: str

    @field_validator('time')
    def validate_time_format(cls, v):
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(
                f"Invalid time format: {v}. "
                f"Use HH:MM (24-hour format). Example: 17:00 for 5 PM"
            )
        return v
```

**Applies to**:
- `daily_reset.time` (MUST match HH:MM)
- `session_hours.start` (MUST match HH:MM)
- `session_hours.end` (MUST match HH:MM)
- `early_close.close_time` (MUST match HH:MM)

### 3.5 Date Format Validation (YYYY-MM-DD)

```python
class HolidayConfig(BaseModel):
    date: str

    @field_validator('date')
    def validate_date_format(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError(
                f"Invalid date format: {v}. "
                f"Use YYYY-MM-DD (ISO 8601). Example: 2025-07-04"
            )

        # Validate date is valid
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Invalid date: {v} (e.g., month 13 doesn't exist)")

        return v
```

**Applies to**:
- All `holidays.dates` entries
- All `early_close.date` entries

### 3.6 Timezone Validation (IANA)

```python
from zoneinfo import ZoneInfo

class TimezoneConfig(BaseModel):
    timezone: str

    @field_validator('timezone')
    def validate_timezone(cls, v):
        try:
            ZoneInfo(v)
        except Exception:
            raise ValueError(
                f"Invalid timezone: {v}. "
                f"Use IANA timezone (e.g., America/Chicago, Europe/London). "
                f"NOT abbreviations like CST or EST."
            )
        return v
```

**Applies to**:
- `general.timezone`
- `daily_reset.timezone`
- `session_hours.timezone`

### 3.7 Duration Format Validation

```python
class DurationConfig(BaseModel):
    duration: str

    @field_validator('duration')
    def validate_duration_format(cls, v):
        # Allow special values
        if v in ['until_reset', 'until_session_start', 'permanent']:
            return v

        # Check format: \d+[smh]
        if not re.match(r'^\d+[smh]$', v):
            raise ValueError(
                f"Invalid duration: {v}. "
                f"Use format: <number><unit> (e.g., '60s', '15m', '1h') "
                f"or special values: 'until_reset', 'until_session_start', 'permanent'"
            )

        return v
```

**Applies to**:
- All `lockout_durations` entries

### 3.8 Enum Validation

```python
class EnumConfig(BaseModel):
    count_type: str

    @field_validator('count_type')
    def validate_count_type(cls, v):
        if v not in ['net', 'gross']:
            raise ValueError(f"Invalid count_type: {v}. Must be 'net' or 'gross'")
        return v

    account_type: str

    @field_validator('account_type')
    def validate_account_type(cls, v):
        if v not in ['practice', 'live']:
            raise ValueError(f"Invalid account_type: {v}. Must be 'practice' or 'live'")
        return v

    lockout_type: str

    @field_validator('lockout_type')
    def validate_lockout_type(cls, v):
        if v not in ['timer', 'hard']:
            raise ValueError(f"Invalid lockout_type: {v}. Must be 'timer' or 'hard'")
        return v
```

---

## 4. Semantic Validation Rules

### 4.1 Time Range Validation (End > Start)

```python
class SessionHoursConfig(BaseModel):
    start: str
    end: str

    @model_validator(mode='after')
    def validate_end_after_start(self):
        # Parse times
        start_time = datetime.strptime(self.start, '%H:%M').time()
        end_time = datetime.strptime(self.end, '%H:%M').time()

        if end_time <= start_time:
            raise ValueError(
                f"Session end ({self.end}) must be after start ({self.start}). "
                f"Example: start='09:30', end='16:00'"
            )

        return self
```

### 4.2 Loss Limit Hierarchy

```python
class RulesConfig(BaseModel):
    daily_realized_loss: DailyRealizedLossConfig
    daily_unrealized_loss: DailyUnrealizedLossConfig

    @model_validator(mode='after')
    def validate_loss_hierarchy(self):
        if not (self.daily_realized_loss.enabled and self.daily_unrealized_loss.enabled):
            return self  # Skip if either disabled

        unrealized = abs(self.daily_unrealized_loss.limit)
        realized = abs(self.daily_realized_loss.limit)

        if unrealized >= realized:
            raise ValueError(
                f"Unrealized loss limit ({self.daily_unrealized_loss.limit}) "
                f"should be LESS than realized loss limit ({self.daily_realized_loss.limit}). "
                f"Reason: Unrealized should trigger before realized. "
                f"Example: unrealized=-200, realized=-500"
            )

        return self
```

### 4.3 Contract Limit Hierarchy

```python
class RulesConfig(BaseModel):
    max_contracts: MaxContractsConfig
    max_contracts_per_instrument: MaxContractsPerInstrumentConfig

    @model_validator(mode='after')
    def validate_contract_hierarchy(self):
        if not (self.max_contracts.enabled and self.max_contracts_per_instrument.enabled):
            return self

        per_instrument = self.max_contracts_per_instrument.default_limit
        total = self.max_contracts.limit

        if per_instrument > total:
            raise ValueError(
                f"Per-instrument limit ({per_instrument}) cannot exceed "
                f"total account limit ({total}). "
                f"Example: per_instrument=2, total=5"
            )

        return self
```

### 4.4 Trade Frequency Hierarchy

```python
class TradeFrequencyConfig(BaseModel):
    limits: dict[str, int]

    @model_validator(mode='after')
    def validate_frequency_hierarchy(self):
        per_minute = self.limits.get('per_minute', 0)
        per_hour = self.limits.get('per_hour', 0)
        per_session = self.limits.get('per_session', 0)

        if per_minute * 60 > per_hour:
            raise ValueError(
                f"per_minute ({per_minute}) * 60 exceeds per_hour ({per_hour}). "
                f"Example: per_minute=3, per_hour=10 (not 180)"
            )

        if per_hour * 8 > per_session:  # Assume 8-hour session
            raise ValueError(
                f"per_hour ({per_hour}) * 8 exceeds per_session ({per_session}). "
                f"Example: per_hour=10, per_session=50 (not 80)"
            )

        return self
```

### 4.5 Category Enforcement Validation

```python
class TradeByTradeRuleConfig(BaseModel):
    close_all: bool
    close_position: bool

    @model_validator(mode='after')
    def validate_trade_by_trade_enforcement(self):
        if self.close_all:
            raise ValueError(
                "Trade-by-trade rules MUST have close_all=false. "
                "Only close the violating position, not all positions."
            )

        if not self.close_position:
            raise ValueError(
                "Trade-by-trade rules MUST have close_position=true."
            )

        return self

class HardLockoutRuleConfig(BaseModel):
    close_all: bool
    lockout_type: str

    @model_validator(mode='after')
    def validate_hard_lockout_enforcement(self):
        if not self.close_all:
            raise ValueError(
                "Hard lockout rules MUST have close_all=true. "
                "Close all positions when triggered."
            )

        if self.lockout_type != 'hard':
            raise ValueError(
                "Hard lockout rules MUST have lockout_type='hard'."
            )

        return self
```

---

## 5. Cross-Configuration Validation

### 5.1 Timers Reference Validation

```python
class ConfigValidator:
    def validate_references(
        self,
        risk_config: RiskConfig,
        timers_config: TimersConfig
    ) -> list[str]:
        """Validate references between configs."""
        errors = []

        # If using "until_reset", daily_reset must be enabled
        if risk_config.rules.daily_realized_loss.enabled:
            duration = timers_config.lockout_durations.hard_lockout.daily_realized_loss

            if duration == "until_reset" and not timers_config.daily_reset.enabled:
                errors.append(
                    "daily_realized_loss uses lockout_until_reset, "
                    "but daily_reset is disabled in timers_config.yaml"
                )

        # If respecting holidays, holidays must be defined
        if risk_config.rules.session_block_outside.enabled:
            if risk_config.rules.session_block_outside.respect_holidays:
                if not timers_config.holidays.enabled:
                    errors.append(
                        "session_block_outside respects holidays, "
                        "but holidays are disabled in timers_config.yaml"
                    )

        return errors
```

### 5.2 Instrument Validation

```python
class ConfigValidator:
    def validate_instruments(
        self,
        risk_config: RiskConfig
    ) -> list[str]:
        """Validate instrument references."""
        errors = []

        # Get all defined instruments
        defined = set(risk_config.general.instruments)

        # Check per-instrument limits
        if risk_config.rules.max_contracts_per_instrument.enabled:
            for instrument in risk_config.rules.max_contracts_per_instrument.instrument_limits:
                if instrument not in defined:
                    errors.append(
                        f"Instrument '{instrument}' in max_contracts_per_instrument "
                        f"is not in general.instruments list"
                    )

        # Check blocked symbols
        if risk_config.rules.symbol_blocks.enabled:
            for symbol in risk_config.rules.symbol_blocks.blocked_symbols:
                if symbol not in defined:
                    errors.append(
                        f"Blocked symbol '{symbol}' is not in general.instruments list. "
                        f"(This may be intentional - warning only)"
                    )

        return errors
```

### 5.3 Account Validation

```python
class ConfigValidator:
    def validate_accounts(
        self,
        accounts_config: AccountsConfig
    ) -> list[str]:
        """Validate account configuration."""
        errors = []

        # Check unique account IDs
        ids = [acc.id for acc in accounts_config.accounts]
        if len(ids) != len(set(ids)):
            errors.append("Account IDs must be unique")

        # Check config file references
        for account in accounts_config.accounts:
            if account.risk_config_file:
                if not Path(account.risk_config_file).exists():
                    errors.append(
                        f"Account '{account.name}' references config file "
                        f"'{account.risk_config_file}' which does not exist"
                    )

            # Cannot specify both file and overrides
            if account.risk_config_file and account.config_overrides:
                errors.append(
                    f"Account '{account.name}' specifies both risk_config_file "
                    f"and config_overrides. Choose one."
                )

        return errors
```

---

## 6. Error Messages

### 6.1 Error Message Format

**Good Error Messages**:
- ✅ Explain WHAT is wrong
- ✅ Explain WHY it's wrong
- ✅ Provide FIX suggestion
- ✅ Give EXAMPLE of correct value

**Example**:

```python
raise ValueError(
    f"Daily loss limit must be negative (you entered {value}). "  # WHAT
    f"Reason: Negative values represent losses. "                  # WHY
    f"Fix: Change {value} to {-abs(value)}. "                     # FIX
    f"Example: -500.0 means max $500 loss."                       # EXAMPLE
)
```

### 6.2 Validation Error Output

```python
from pydantic import ValidationError

try:
    config = RiskConfig.from_file('config/risk_config.yaml')
except ValidationError as e:
    print("Configuration Error:")
    print(e)

# Output:
# Configuration Error:
# 2 validation errors for RiskConfig
# rules.daily_realized_loss.limit
#   Daily loss limit must be negative (you entered 500.0). Reason: Negative values represent losses. Fix: Change 500.0 to -500.0. Example: -500.0 means max $500 loss. (type=value_error)
# rules.daily_unrealized_loss.limit
#   Daily unrealized loss limit must be negative (you entered 200.0). Fix: Change to -200.0. (type=value_error)
```

---

## 7. Implementation Examples

### 7.1 Complete Validation Example

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import re

class DailyRealizedLossConfig(BaseModel):
    """Daily realized loss rule configuration."""

    enabled: bool = True
    limit: float = Field(..., description="Max daily loss (negative value)")
    close_all: bool = True
    cancel_orders: bool = True
    lockout_type: str = "hard"

    @field_validator('limit')
    def limit_must_be_negative(cls, v):
        """Ensure loss limit is negative."""
        if v >= 0:
            raise ValueError(
                f"Daily loss limit must be negative (you entered {v}). "
                f"Reason: Negative values represent losses. "
                f"Fix: Change {v} to {-abs(v)}. "
                f"Example: -500.0 means max $500 loss."
            )
        return v

    @field_validator('lockout_type')
    def validate_lockout_type(cls, v):
        """Ensure lockout_type is 'hard' for hard lockout rules."""
        if v != 'hard':
            raise ValueError(
                f"Daily realized loss MUST have lockout_type='hard' (you set '{v}'). "
                f"Reason: This is a hard lockout rule category."
            )
        return v

    @model_validator(mode='after')
    def validate_hard_lockout_enforcement(self):
        """Ensure enforcement matches hard lockout category."""
        if not self.close_all:
            raise ValueError(
                "Daily realized loss MUST have close_all=true. "
                "Reason: Hard lockout rules close all positions."
            )

        if not self.cancel_orders:
            raise ValueError(
                "Daily realized loss MUST have cancel_orders=true. "
                "Reason: Hard lockout rules cancel all orders."
            )

        return self
```

### 7.2 Loading with Validation

```python
def load_config_with_validation(config_file: str) -> RiskConfig:
    """Load config with comprehensive validation."""

    try:
        # Load YAML
        with open(config_file) as f:
            yaml_str = f.read()

        # Expand environment variables
        yaml_str = expand_env_vars(yaml_str)

        # Parse YAML
        data = yaml.safe_load(yaml_str)

        # Validate with Pydantic (automatic)
        config = RiskConfig(**data)

        # Success!
        logger.success(f"Configuration loaded and validated: {config_file}")
        return config

    except FileNotFoundError as e:
        logger.error(f"Config file not found: {config_file}")
        raise

    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML syntax in {config_file}: {e}")
        raise

    except ValidationError as e:
        logger.error(f"Configuration validation failed:")
        for error in e.errors():
            loc = ' -> '.join(str(x) for x in error['loc'])
            msg = error['msg']
            logger.error(f"  {loc}: {msg}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        raise
```

---

## Summary

### Validation Layers

1. **Type Validation**: Automatic (Pydantic)
2. **Range Validation**: `@field_validator` decorators
3. **Semantic Validation**: `@model_validator` decorators

### Key Validation Rules

**Must Be Negative**:
- Daily realized loss limit
- Daily unrealized loss limit
- Cooldown after loss threshold

**Must Be Positive**:
- Daily realized profit target
- Max unrealized profit target
- All contract limits
- All frequency limits
- All timeout values

**Format Validation**:
- Times: HH:MM (24-hour)
- Dates: YYYY-MM-DD (ISO 8601)
- Timezones: IANA (e.g., America/Chicago)
- Durations: \d+[smh] or special values

**Cross-Field Validation**:
- Session end > start
- Unrealized loss < realized loss
- Per-instrument limit <= total limit
- Frequency hierarchy (minute <= hour <= session)

**Category Enforcement**:
- Trade-by-trade: close_all=false, close_position=true
- Timer/cooldown: close_all=true, lockout_type="timer"
- Hard lockout: close_all=true, lockout_type="hard"

---

**Document Complete**
**Created**: 2025-10-25
**Status**: PRODUCTION READY
