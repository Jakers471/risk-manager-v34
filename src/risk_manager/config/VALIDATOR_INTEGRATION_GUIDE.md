# Configuration Validator Integration Guide

**For Agent 1**: How to integrate validators into Pydantic models

**Created**: 2025-10-27
**Status**: Ready for integration

---

## Table of Contents

1. [Overview](#overview)
2. [Field Validators](#field-validators)
3. [Model Validators](#model-validators)
4. [Integration Examples](#integration-examples)
5. [Complete Validator Checklist](#complete-validator-checklist)
6. [Error Message Examples](#error-message-examples)

---

## Overview

The `validator.py` module provides three types of validators:

1. **ValidationHelpers**: Reusable validation functions for common patterns
2. **ModelValidatorMixins**: Pre-built @model_validator methods for cross-field validation
3. **ConfigValidator**: Cross-configuration validation (between files)

**How to use**:
1. Add `@field_validator` decorators to individual fields
2. Add `@model_validator` decorators for cross-field validation
3. Use `ConfigValidator` to validate relationships between configs

---

## Field Validators

### Import Statement

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from risk_manager.config.validator import ValidationHelpers
```

### Loss Limits (Must Be Negative)

**Apply to**: daily_realized_loss.limit, daily_unrealized_loss.limit, cooldown_after_loss.loss_threshold

```python
class DailyRealizedLossConfig(BaseModel):
    limit: float

    @field_validator('limit')
    @classmethod
    def limit_must_be_negative(cls, v):
        return ValidationHelpers.validate_negative(v, "Daily loss limit")
```

**Error Example**:
```
Daily loss limit must be negative (you entered 500.0).
Reason: Negative values represent losses.
Fix: Change 500.0 to -500.0.
Example: -500.0 means maximum $500 loss allowed.
```

### Profit Targets (Must Be Positive)

**Apply to**: daily_realized_profit.target, max_unrealized_profit.target

```python
class DailyRealizedProfitConfig(BaseModel):
    target: float

    @field_validator('target')
    @classmethod
    def target_must_be_positive(cls, v):
        return ValidationHelpers.validate_positive(v, "Profit target")
```

**Error Example**:
```
Profit target must be > 0 (you entered -100.0).
Reason: This value represents a count/limit.
Fix: Use a positive number greater than zero.
```

### Contract Limits (Must Be Positive)

**Apply to**: max_contracts.limit, max_contracts_per_instrument.default_limit, all instrument_limits

```python
class MaxContractsConfig(BaseModel):
    limit: int

    @field_validator('limit')
    @classmethod
    def limit_must_be_positive(cls, v):
        return ValidationHelpers.validate_positive(v, "Max contracts limit")
```

### Time Format (HH:MM)

**Apply to**: daily_reset.time, session_hours.start, session_hours.end, early_close.close_time

```python
class DailyResetConfig(BaseModel):
    time: str

    @field_validator('time')
    @classmethod
    def validate_time_format(cls, v):
        return ValidationHelpers.validate_time_format(v, "Reset time")
```

**Error Example**:
```
Invalid Reset time format: '25:00'.
Use HH:MM (24-hour format).
Example: 17:00 for 5 PM, 09:30 for 9:30 AM
```

### Date Format (YYYY-MM-DD)

**Apply to**: holidays.dates[], early_close.date

```python
class HolidaysConfig(BaseModel):
    dates: list[str]

    @field_validator('dates')
    @classmethod
    def validate_date_formats(cls, v):
        for date in v:
            ValidationHelpers.validate_date_format(date, "Holiday date")
        return v
```

**Error Example**:
```
Invalid Holiday date format: '2025-13-01'.
Use YYYY-MM-DD (ISO 8601 format).
Example: 2025-07-04 for July 4th, 2025
```

### Timezone (IANA)

**Apply to**: general.timezone, daily_reset.timezone, session_hours.timezone

```python
class GeneralConfig(BaseModel):
    timezone: str

    @field_validator('timezone')
    @classmethod
    def validate_timezone_format(cls, v):
        return ValidationHelpers.validate_timezone(v, "Timezone")
```

**Error Example**:
```
Invalid Timezone: 'CST'.
Use IANA timezone (e.g., America/Chicago, Europe/London, America/New_York).
NOT abbreviations like CST, EST, or PST.
See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

### Duration Format

**Apply to**: All lockout_durations fields

```python
class HardLockoutConfig(BaseModel):
    daily_realized_loss: str

    @field_validator('daily_realized_loss')
    @classmethod
    def validate_duration_format(cls, v):
        return ValidationHelpers.validate_duration_format(v, "Lockout duration")
```

**Error Example**:
```
Invalid Lockout duration: 'invalid'.
Use format: <number><unit> where unit is s (seconds), m (minutes), or h (hours).
Examples: '60s' (60 seconds), '15m' (15 minutes), '1h' (1 hour).
Or use special values: until_reset, until_session_start, permanent
```

### Enum Validation

**Apply to**: count_type, account_type, lockout_type, log_level

```python
class MaxContractsConfig(BaseModel):
    count_type: str

    @field_validator('count_type')
    @classmethod
    def validate_count_type(cls, v):
        return ValidationHelpers.validate_enum(
            v,
            ['net', 'gross'],
            "count_type"
        )
```

**Error Example**:
```
Invalid count_type: 'invalid'.
Must be one of: 'net', 'gross'.
Fix: Choose from the allowed values.
```

---

## Model Validators

### Time Range Validation (End > Start)

**Apply to**: SessionHoursConfig

```python
from risk_manager.config.validator import ModelValidatorMixins

class SessionHoursConfig(BaseModel):
    start: str
    end: str

    @model_validator(mode='after')
    def validate_end_after_start(self):
        ModelValidatorMixins.TimeRangeValidator.validate_time_range(
            self.start,
            self.end,
            "start",
            "end"
        )
        return self
```

**Error Example**:
```
Session end (08:00) must be after start (16:00).
Reason: Cannot have an end time before start time.
Fix: Swap the times or correct the values.
Example: start='09:30', end='16:00'
```

### Loss Hierarchy Validation (Unrealized < Realized)

**Apply to**: RulesConfig (when both daily_realized_loss and daily_unrealized_loss enabled)

```python
class RulesConfig(BaseModel):
    daily_realized_loss: DailyRealizedLossConfig
    daily_unrealized_loss: DailyUnrealizedLossConfig

    @model_validator(mode='after')
    def validate_loss_hierarchy(self):
        if (self.daily_realized_loss.enabled and
            self.daily_unrealized_loss.enabled):

            ModelValidatorMixins.LossHierarchyValidator.validate_loss_hierarchy(
                self.daily_unrealized_loss.limit,
                self.daily_realized_loss.limit
            )
        return self
```

**Error Example**:
```
Unrealized loss limit (-500.0) should be LESS than realized loss limit (-200.0) in absolute value.
Reason: Unrealized loss should trigger before realized loss to provide early warning.
Fix: Make unrealized limit smaller.
Example: unrealized=-200, realized=-500
```

### Contract Hierarchy Validation (Per-Instrument <= Total)

**Apply to**: RulesConfig (when both max_contracts and max_contracts_per_instrument enabled)

```python
class RulesConfig(BaseModel):
    max_contracts: MaxContractsConfig
    max_contracts_per_instrument: MaxContractsPerInstrumentConfig

    @model_validator(mode='after')
    def validate_contract_hierarchy(self):
        if (self.max_contracts.enabled and
            self.max_contracts_per_instrument.enabled):

            ModelValidatorMixins.ContractHierarchyValidator.validate_contract_hierarchy(
                self.max_contracts_per_instrument.default_limit,
                self.max_contracts.limit
            )
        return self
```

**Error Example**:
```
Per-instrument limit (10) cannot exceed total account limit (5).
Reason: Single instrument cannot have more contracts than entire account.
Fix: Reduce per-instrument limit or increase total limit.
Example: per_instrument=2, total=5
```

### Frequency Hierarchy Validation

**Apply to**: TradeFrequencyLimitConfig

```python
class FrequencyLimitsConfig(BaseModel):
    per_minute: int | None = None
    per_hour: int | None = None
    per_session: int | None = None

    @model_validator(mode='after')
    def validate_frequency_hierarchy(self):
        ModelValidatorMixins.FrequencyHierarchyValidator.validate_frequency_hierarchy(
            self.per_minute,
            self.per_hour,
            self.per_session
        )
        return self
```

**Error Example**:
```
per_minute (10) * 60 = 600 exceeds per_hour (100).
Reason: If you can trade 10 times per minute, you could trade 600 times in an hour.
Fix: Reduce per_minute or increase per_hour.
Example: per_minute=3, per_hour=10 (not 180)
```

### Category Enforcement Validation

**Trade-by-Trade Rules** (RULE-001, RULE-002, RULE-004, RULE-005, RULE-008, RULE-011):

```python
class MaxContractsConfig(BaseModel):
    enabled: bool
    close_all: bool
    close_position: bool

    @model_validator(mode='after')
    def validate_trade_by_trade_enforcement(self):
        if self.enabled:
            ModelValidatorMixins.CategoryEnforcementValidator.validate_trade_by_trade_enforcement(
                self.close_all,
                self.close_position,
                "RULE-001 (Max Contracts)"
            )
        return self
```

**Hard Lockout Rules** (RULE-003, RULE-009, RULE-013):

```python
class DailyRealizedLossConfig(BaseModel):
    enabled: bool
    close_all: bool
    lockout_type: str

    @model_validator(mode='after')
    def validate_hard_lockout_enforcement(self):
        if self.enabled:
            ModelValidatorMixins.CategoryEnforcementValidator.validate_hard_lockout_enforcement(
                self.close_all,
                self.lockout_type,
                "RULE-003 (Daily Realized Loss)"
            )
        return self
```

---

## Integration Examples

### Complete Example: DailyRealizedLossConfig

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from risk_manager.config.validator import ValidationHelpers, ModelValidatorMixins


class DailyRealizedLossConfig(BaseModel):
    """
    RULE-003: Daily Realized Loss
    Category: Hard Lockout
    """

    enabled: bool = True
    limit: float = Field(..., description="Max daily loss (negative value)")
    close_all: bool = True
    cancel_orders: bool = True
    lockout_type: str = "hard"

    # Field Validators
    @field_validator('limit')
    @classmethod
    def limit_must_be_negative(cls, v):
        """Ensure loss limit is negative."""
        return ValidationHelpers.validate_negative(v, "Daily loss limit")

    @field_validator('lockout_type')
    @classmethod
    def validate_lockout_type_enum(cls, v):
        """Ensure lockout_type is valid."""
        return ValidationHelpers.validate_enum(
            v,
            ['hard', 'timer'],
            "lockout_type"
        )

    # Model Validators
    @model_validator(mode='after')
    def validate_hard_lockout_enforcement(self):
        """Ensure enforcement matches hard lockout category."""
        if self.enabled:
            ModelValidatorMixins.CategoryEnforcementValidator.validate_hard_lockout_enforcement(
                self.close_all,
                self.lockout_type,
                "RULE-003 (Daily Realized Loss)"
            )

            # Additional category-specific validation
            if not self.cancel_orders:
                raise ValueError(
                    "RULE-003 (Daily Realized Loss) MUST have cancel_orders=true. "
                    "Reason: Hard lockout rules cancel all orders."
                )

        return self
```

### Complete Example: SessionHoursConfig

```python
from pydantic import BaseModel, field_validator, model_validator
from risk_manager.config.validator import ValidationHelpers, ModelValidatorMixins


class SessionHoursConfig(BaseModel):
    """Session hours configuration."""

    start: str
    end: str
    timezone: str = "America/Chicago"
    enabled: bool = True
    allowed_days: list[int] = [0, 1, 2, 3, 4]  # Mon-Fri

    # Field Validators
    @field_validator('start')
    @classmethod
    def validate_start_time(cls, v):
        return ValidationHelpers.validate_time_format(v, "Session start time")

    @field_validator('end')
    @classmethod
    def validate_end_time(cls, v):
        return ValidationHelpers.validate_time_format(v, "Session end time")

    @field_validator('timezone')
    @classmethod
    def validate_timezone_format(cls, v):
        return ValidationHelpers.validate_timezone(v, "Session timezone")

    @field_validator('allowed_days')
    @classmethod
    def validate_allowed_days(cls, v):
        for day in v:
            if not 0 <= day <= 6:
                raise ValueError(
                    f"Invalid day: {day}. "
                    f"Days must be 0-6 (0=Monday, 6=Sunday). "
                    f"Fix: Use values between 0 and 6."
                )
        return v

    # Model Validators
    @model_validator(mode='after')
    def validate_end_after_start(self):
        if self.enabled:
            ModelValidatorMixins.TimeRangeValidator.validate_time_range(
                self.start,
                self.end,
                "start",
                "end"
            )
        return self
```

---

## Complete Validator Checklist

### Timers Configuration (timers_config.yaml)

#### DailyResetConfig
- [ ] `time` → HH:MM format validation
- [ ] `timezone` → IANA timezone validation

#### HardLockoutConfig
- [ ] `daily_realized_loss` → Duration format validation
- [ ] `daily_realized_profit` → Duration format validation
- [ ] `session_block_outside` → Duration format validation
- [ ] `auth_loss_guard` → Duration format validation

#### TimerCooldownConfig
- [ ] All duration fields → Duration format validation

#### SessionHoursConfig
- [ ] `start` → HH:MM format validation
- [ ] `end` → HH:MM format validation
- [ ] `timezone` → IANA timezone validation
- [ ] `allowed_days` → Range validation (0-6)
- [ ] **@model_validator** → End > Start

#### HolidaysConfig
- [ ] `dates` → YYYY-MM-DD format validation

#### EarlyCloseConfig
- [ ] `date` → YYYY-MM-DD format validation
- [ ] `close_time` → HH:MM format validation

### Risk Configuration (risk_config.yaml)

#### GeneralConfig
- [ ] `timezone` → IANA timezone validation
- [ ] `instruments` → Non-empty list validation

#### LoggingConfig
- [ ] `level` → Enum validation (DEBUG, INFO, WARNING, ERROR)

#### MaxContractsConfig (RULE-001)
- [ ] `limit` → Positive validation
- [ ] `count_type` → Enum validation (net, gross)
- [ ] **@model_validator** → Trade-by-trade enforcement

#### MaxContractsPerInstrumentConfig (RULE-002)
- [ ] `default_limit` → Positive validation
- [ ] `instrument_limits` values → Positive validation
- [ ] **@model_validator** → Trade-by-trade enforcement

#### DailyRealizedLossConfig (RULE-003)
- [ ] `limit` → Negative validation
- [ ] `lockout_type` → Enum validation (hard, timer)
- [ ] **@model_validator** → Hard lockout enforcement

#### DailyUnrealizedLossConfig (RULE-004)
- [ ] `limit` → Negative validation
- [ ] **@model_validator** → Trade-by-trade enforcement

#### MaxUnrealizedProfitConfig (RULE-005)
- [ ] `target` → Positive validation
- [ ] **@model_validator** → Trade-by-trade enforcement

#### TradeFrequencyLimitConfig (RULE-006)
- [ ] All limit values → Positive validation
- [ ] **@model_validator** → Frequency hierarchy

#### CooldownAfterLossConfig (RULE-007)
- [ ] `loss_threshold` → Negative validation
- [ ] All cooldown values → Positive validation

#### NoStopLossGraceConfig (RULE-008)
- [ ] `grace_period_seconds` → Positive validation
- [ ] **@model_validator** → Trade-by-trade enforcement

#### SessionBlockOutsideConfig (RULE-009)
- [ ] **@model_validator** → Hard lockout enforcement

#### SymbolBlocksConfig (RULE-011)
- [ ] **@model_validator** → Trade-by-trade enforcement

#### TradeManagementConfig (RULE-012)
- [ ] `stop_loss_offset` → Positive validation
- [ ] `take_profit_offset` → Positive validation

#### DailyRealizedProfitConfig (RULE-013)
- [ ] `target` → Positive validation
- [ ] **@model_validator** → Hard lockout enforcement

#### RulesConfig
- [ ] **@model_validator** → Loss hierarchy (unrealized < realized)
- [ ] **@model_validator** → Contract hierarchy (per-instrument <= total)

### Accounts Configuration (accounts.yaml)

#### TopstepXConfig
- [ ] `api_url` → URL format validation (optional)
- [ ] `websocket_url` → URL format validation (optional)

#### AccountConfig
- [ ] `account_type` → Enum validation (practice, live)

---

## Error Message Examples

### Good Error Messages (Follow This Pattern)

```
Field: rules.daily_realized_loss.limit
Error: Daily loss limit must be negative (you entered 500.0).
       Reason: Negative values represent losses.
       Fix: Change 500.0 to -500.0.
       Example: -500.0 means maximum $500 loss allowed.
```

**Components**:
1. **WHAT**: What's wrong (you entered 500.0)
2. **WHY**: Why it's wrong (negative values represent losses)
3. **FIX**: How to fix it (change 500.0 to -500.0)
4. **EXAMPLE**: Example of correct value (-500.0 means...)

### Bad Error Messages (Avoid These)

```
❌ "Invalid value"
❌ "Validation error"
❌ "Value must be negative"
```

**Why bad**: Doesn't explain what, why, how to fix, or give examples.

---

## Usage Example

### Loading with Validation

```python
from pydantic import ValidationError
from risk_manager.config import RiskConfig
from risk_manager.config.validator import format_validation_errors

try:
    # Load config - validation runs automatically
    config = RiskConfig.from_file('config/risk_config.yaml')
    print("✅ Configuration loaded successfully!")

except FileNotFoundError as e:
    print(f"❌ Config file not found: {e}")

except ValidationError as e:
    # Format and display errors
    print(format_validation_errors(e))

except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

### Cross-Configuration Validation

```python
from risk_manager.config import RiskConfig, TimersConfig, AccountsConfig
from risk_manager.config.validator import ConfigValidator

# Load all configs
risk_config = RiskConfig.from_file('config/risk_config.yaml')
timers_config = TimersConfig.from_file('config/timers_config.yaml')
accounts_config = AccountsConfig.from_file('config/accounts.yaml')

# Validate cross-config relationships
validator = ConfigValidator()
errors = validator.validate_all(risk_config, timers_config, accounts_config)

if errors:
    print("❌ Cross-configuration validation failed:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ All cross-configuration checks passed!")
```

---

## Testing Validators

### Unit Test Template

```python
import pytest
from pydantic import ValidationError
from risk_manager.config.models import DailyRealizedLossConfig


def test_daily_realized_loss_limit_must_be_negative():
    """Test that limit must be negative."""

    # Valid: negative limit
    config = DailyRealizedLossConfig(
        enabled=True,
        limit=-500.0,
        close_all=True,
        cancel_orders=True,
        lockout_type="hard"
    )
    assert config.limit == -500.0

    # Invalid: positive limit
    with pytest.raises(ValidationError) as exc_info:
        DailyRealizedLossConfig(
            enabled=True,
            limit=500.0,  # ❌ Should be negative
            close_all=True,
            cancel_orders=True,
            lockout_type="hard"
        )

    # Check error message contains helpful information
    error_msg = str(exc_info.value)
    assert "negative" in error_msg.lower()
    assert "500.0" in error_msg
    assert "-500.0" in error_msg


def test_hard_lockout_enforcement_validation():
    """Test that hard lockout rules must have correct enforcement."""

    # Invalid: close_all=false (should be true)
    with pytest.raises(ValidationError) as exc_info:
        DailyRealizedLossConfig(
            enabled=True,
            limit=-500.0,
            close_all=False,  # ❌ Should be True for hard lockout
            cancel_orders=True,
            lockout_type="hard"
        )

    error_msg = str(exc_info.value)
    assert "close_all=true" in error_msg.lower()
    assert "hard lockout" in error_msg.lower()
```

---

## Summary

**For Agent 1 to integrate validators**:

1. **Import validators** at top of models.py:
   ```python
   from risk_manager.config.validator import ValidationHelpers, ModelValidatorMixins
   ```

2. **Add @field_validator decorators** to individual fields using checklist above

3. **Add @model_validator decorators** for cross-field validation using checklist above

4. **Test each validator** with unit tests (template above)

5. **Use ConfigValidator** in loading logic to validate cross-config relationships

**All validators are ready in `validator.py` - just need to be integrated into Pydantic models!**

---

**Created**: 2025-10-27
**Status**: Ready for Agent 1 integration
**Next Step**: Agent 1 creates models.py and integrates these validators
