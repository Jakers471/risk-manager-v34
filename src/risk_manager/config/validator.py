"""
Configuration Validators for Risk Manager V34

This module provides comprehensive validation for all configuration files:
- Field-level validators (using @field_validator)
- Model-level validators (using @model_validator)
- Cross-configuration validators (ConfigValidator class)

Implements 3-layer validation:
1. Type validation (automatic via Pydantic)
2. Range validation (manual via @field_validator)
3. Semantic validation (manual via @model_validator and ConfigValidator)
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import ValidationError


class ValidationHelpers:
    """Helper methods for common validation patterns."""

    @staticmethod
    def validate_time_format(value: str, field_name: str = "time") -> str:
        """
        Validate HH:MM time format (24-hour).

        Args:
            value: Time string to validate
            field_name: Name of field for error messages

        Returns:
            Validated time string

        Raises:
            ValueError: If time format is invalid

        Example:
            validate_time_format("17:00")  # OK
            validate_time_format("25:00")  # ValueError
        """
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', value):
            raise ValueError(
                f"Invalid {field_name} format: '{value}'. "
                f"Use HH:MM (24-hour format). "
                f"Example: 17:00 for 5 PM, 09:30 for 9:30 AM"
            )
        return value

    @staticmethod
    def validate_date_format(value: str, field_name: str = "date") -> str:
        """
        Validate YYYY-MM-DD date format (ISO 8601).

        Args:
            value: Date string to validate
            field_name: Name of field for error messages

        Returns:
            Validated date string

        Raises:
            ValueError: If date format is invalid or date doesn't exist

        Example:
            validate_date_format("2025-07-04")  # OK
            validate_date_format("2025-13-01")  # ValueError (month 13)
        """
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            raise ValueError(
                f"Invalid {field_name} format: '{value}'. "
                f"Use YYYY-MM-DD (ISO 8601 format). "
                f"Example: 2025-07-04 for July 4th, 2025"
            )

        # Validate date actually exists
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError as e:
            raise ValueError(
                f"Invalid {field_name}: '{value}'. "
                f"Reason: {str(e)}. "
                f"Example: Month 13 doesn't exist, use 01-12"
            )

        return value

    @staticmethod
    def validate_timezone(value: str, field_name: str = "timezone") -> str:
        """
        Validate IANA timezone string.

        Args:
            value: Timezone string to validate
            field_name: Name of field for error messages

        Returns:
            Validated timezone string

        Raises:
            ValueError: If timezone is invalid

        Example:
            validate_timezone("America/Chicago")  # OK
            validate_timezone("CST")  # ValueError (abbreviation not allowed)
        """
        try:
            ZoneInfo(value)
        except Exception:
            raise ValueError(
                f"Invalid {field_name}: '{value}'. "
                f"Use IANA timezone (e.g., America/Chicago, Europe/London, America/New_York). "
                f"NOT abbreviations like CST, EST, or PST. "
                f"See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
            )
        return value

    @staticmethod
    def validate_duration_format(value: str, field_name: str = "duration") -> str:
        r"""
        Validate duration format: \d+[smh] or special values.

        Special values:
        - until_reset: Until daily reset time
        - until_session_start: Until next session starts
        - permanent: Requires admin unlock

        Args:
            value: Duration string to validate
            field_name: Name of field for error messages

        Returns:
            Validated duration string

        Raises:
            ValueError: If duration format is invalid

        Example:
            validate_duration_format("60s")  # OK - 60 seconds
            validate_duration_format("15m")  # OK - 15 minutes
            validate_duration_format("1h")   # OK - 1 hour
            validate_duration_format("until_reset")  # OK - special value
            validate_duration_format("invalid")  # ValueError
        """
        # Allow special values
        special_values = ['until_reset', 'until_session_start', 'permanent']
        if value in special_values:
            return value

        # Check format: \d+[smh]
        if not re.match(r'^\d+[smh]$', value):
            raise ValueError(
                f"Invalid {field_name}: '{value}'. "
                f"Use format: <number><unit> where unit is s (seconds), m (minutes), or h (hours). "
                f"Examples: '60s' (60 seconds), '15m' (15 minutes), '1h' (1 hour). "
                f"Or use special values: {', '.join(special_values)}"
            )

        return value

    @staticmethod
    def validate_positive(value: float | int, field_name: str, allow_zero: bool = False) -> float | int:
        """
        Validate value is positive (or zero if allowed).

        Args:
            value: Value to validate
            field_name: Name of field for error messages
            allow_zero: Whether to allow zero (default False)

        Returns:
            Validated value

        Raises:
            ValueError: If value is not positive

        Example:
            validate_positive(5, "limit")  # OK
            validate_positive(0, "limit")  # ValueError
            validate_positive(0, "limit", allow_zero=True)  # OK
            validate_positive(-5, "limit")  # ValueError
        """
        if allow_zero:
            if value < 0:
                raise ValueError(
                    f"{field_name} must be >= 0 (you entered {value}). "
                    f"Reason: This value represents a count/limit. "
                    f"Fix: Use 0 or a positive number."
                )
        else:
            if value <= 0:
                raise ValueError(
                    f"{field_name} must be > 0 (you entered {value}). "
                    f"Reason: This value represents a count/limit. "
                    f"Fix: Use a positive number greater than zero."
                )
        return value

    @staticmethod
    def validate_negative(value: float, field_name: str) -> float:
        """
        Validate value is negative (for loss limits).

        Args:
            value: Value to validate
            field_name: Name of field for error messages

        Returns:
            Validated value

        Raises:
            ValueError: If value is not negative

        Example:
            validate_negative(-500.0, "Daily loss limit")  # OK
            validate_negative(500.0, "Daily loss limit")  # ValueError
        """
        if value >= 0:
            raise ValueError(
                f"{field_name} must be negative (you entered {value}). "
                f"Reason: Negative values represent losses. "
                f"Fix: Change {value} to {-abs(value)}. "
                f"Example: -500.0 means maximum $500 loss allowed."
            )
        return value

    @staticmethod
    def validate_enum(value: str, allowed_values: list[str], field_name: str) -> str:
        """
        Validate value is in allowed enum values.

        Args:
            value: Value to validate
            allowed_values: List of allowed values
            field_name: Name of field for error messages

        Returns:
            Validated value

        Raises:
            ValueError: If value not in allowed values

        Example:
            validate_enum("net", ["net", "gross"], "count_type")  # OK
            validate_enum("invalid", ["net", "gross"], "count_type")  # ValueError
        """
        if value not in allowed_values:
            raise ValueError(
                f"Invalid {field_name}: '{value}'. "
                f"Must be one of: {', '.join(repr(v) for v in allowed_values)}. "
                f"Fix: Choose from the allowed values."
            )
        return value


class ConfigValidator:
    """
    Cross-configuration validator.

    Validates relationships between different configuration files:
    - Timers references (until_reset requires daily_reset.enabled)
    - Holiday references (respect_holidays requires holidays.enabled)
    - Instrument references (instruments in rules match general.instruments)
    - Account references (custom config files exist)
    """

    def validate_all(
        self,
        risk_config: Any,
        timers_config: Any,
        accounts_config: Any | None = None
    ) -> list[str]:
        """
        Validate all cross-configuration relationships.

        Args:
            risk_config: Loaded RiskConfig instance
            timers_config: Loaded TimersConfig instance
            accounts_config: Loaded AccountsConfig instance (optional)

        Returns:
            List of error messages (empty if valid)

        Example:
            errors = validator.validate_all(risk_config, timers_config, accounts_config)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}")
        """
        errors = []

        # Validate timers references
        errors.extend(self.validate_timer_references(risk_config, timers_config))

        # Validate holiday references
        errors.extend(self.validate_holiday_references(risk_config, timers_config))

        # Validate instrument references
        errors.extend(self.validate_instrument_references(risk_config))

        # Validate accounts if provided
        if accounts_config:
            errors.extend(self.validate_accounts(accounts_config))

        return errors

    def validate_timer_references(
        self,
        risk_config: Any,
        timers_config: Any
    ) -> list[str]:
        """
        Validate timer references are valid.

        Checks:
        - "until_reset" requires daily_reset.enabled
        - "until_session_start" requires session_hours.enabled

        Args:
            risk_config: RiskConfig instance
            timers_config: TimersConfig instance

        Returns:
            List of error messages
        """
        errors = []

        # Check if any rule uses "until_reset"
        lockout_durations = timers_config.lockout_durations

        # Check hard lockout rules
        if hasattr(lockout_durations, 'hard_lockout'):
            hard_lockout = lockout_durations.hard_lockout

            # Daily realized loss
            if hasattr(hard_lockout, 'daily_realized_loss'):
                if hard_lockout.daily_realized_loss == "until_reset":
                    if not timers_config.daily_reset.enabled:
                        errors.append(
                            "RULE-003 (daily_realized_loss) uses lockout_duration='until_reset', "
                            "but daily_reset is disabled in timers_config.yaml. "
                            "Fix: Set timers_config.daily_reset.enabled=true or change lockout_duration."
                        )

            # Daily realized profit
            if hasattr(hard_lockout, 'daily_realized_profit'):
                if hard_lockout.daily_realized_profit == "until_reset":
                    if not timers_config.daily_reset.enabled:
                        errors.append(
                            "RULE-013 (daily_realized_profit) uses lockout_duration='until_reset', "
                            "but daily_reset is disabled in timers_config.yaml. "
                            "Fix: Set timers_config.daily_reset.enabled=true or change lockout_duration."
                        )

            # Session block outside
            if hasattr(hard_lockout, 'session_block_outside'):
                if hard_lockout.session_block_outside == "until_session_start":
                    if not timers_config.session_hours.enabled:
                        errors.append(
                            "RULE-009 (session_block_outside) uses lockout_duration='until_session_start', "
                            "but session_hours is disabled in timers_config.yaml. "
                            "Fix: Set timers_config.session_hours.enabled=true or change lockout_duration."
                        )

        return errors

    def validate_holiday_references(
        self,
        risk_config: Any,
        timers_config: Any
    ) -> list[str]:
        """
        Validate holiday references are valid.

        Checks:
        - respect_holidays=true requires holidays.enabled

        Args:
            risk_config: RiskConfig instance
            timers_config: TimersConfig instance

        Returns:
            List of error messages
        """
        errors = []

        # Check session_block_outside rule
        if hasattr(risk_config.rules, 'session_block_outside'):
            rule = risk_config.rules.session_block_outside
            if rule.enabled and hasattr(rule, 'respect_holidays'):
                if rule.respect_holidays and not timers_config.holidays.enabled:
                    errors.append(
                        "RULE-009 (session_block_outside) has respect_holidays=true, "
                        "but holidays are disabled in timers_config.yaml. "
                        "Fix: Set timers_config.holidays.enabled=true or set respect_holidays=false."
                    )

        return errors

    def validate_instrument_references(self, risk_config: Any) -> list[str]:
        """
        Validate instrument references match general.instruments.

        Checks:
        - Per-instrument limits reference defined instruments
        - Blocked symbols (warning only)

        Args:
            risk_config: RiskConfig instance

        Returns:
            List of error messages
        """
        errors = []

        # Get defined instruments
        defined_instruments = set(risk_config.general.instruments)

        # Check max_contracts_per_instrument
        if hasattr(risk_config.rules, 'max_contracts_per_instrument'):
            rule = risk_config.rules.max_contracts_per_instrument
            if rule.enabled and hasattr(rule, 'instrument_limits'):
                for instrument in rule.instrument_limits:
                    if instrument not in defined_instruments:
                        errors.append(
                            f"RULE-002 (max_contracts_per_instrument) references instrument '{instrument}', "
                            f"but it's not in general.instruments list: {list(defined_instruments)}. "
                            f"Fix: Add '{instrument}' to general.instruments or remove from instrument_limits."
                        )

        # Check symbol_blocks (warning only)
        if hasattr(risk_config.rules, 'symbol_blocks'):
            rule = risk_config.rules.symbol_blocks
            if rule.enabled and hasattr(rule, 'blocked_symbols'):
                for symbol in rule.blocked_symbols:
                    if symbol not in defined_instruments:
                        errors.append(
                            f"WARNING: RULE-011 (symbol_blocks) blocks symbol '{symbol}', "
                            f"but it's not in general.instruments list: {list(defined_instruments)}. "
                            f"This may be intentional (blocking instrument not in monitored list). "
                            f"If unintentional, add '{symbol}' to general.instruments."
                        )

        return errors

    def validate_accounts(self, accounts_config: Any) -> list[str]:
        """
        Validate accounts configuration.

        Checks:
        - Account IDs are unique
        - Custom config files exist
        - Not both risk_config_file and config_overrides

        Args:
            accounts_config: AccountsConfig instance

        Returns:
            List of error messages
        """
        errors = []

        # Check unique account IDs
        if hasattr(accounts_config, 'accounts'):
            ids = [acc.id for acc in accounts_config.accounts]
            if len(ids) != len(set(ids)):
                duplicates = [id for id in ids if ids.count(id) > 1]
                errors.append(
                    f"Account IDs must be unique. Found duplicates: {list(set(duplicates))}. "
                    f"Fix: Ensure each account has a unique ID."
                )

            # Check config file references
            for account in accounts_config.accounts:
                # Check custom config file exists
                if hasattr(account, 'risk_config_file') and account.risk_config_file:
                    config_path = Path(account.risk_config_file)
                    if not config_path.exists():
                        errors.append(
                            f"Account '{account.name}' (ID: {account.id}) references config file "
                            f"'{account.risk_config_file}' which does not exist. "
                            f"Fix: Create the file or remove risk_config_file reference."
                        )

                # Check not both file and overrides
                if (hasattr(account, 'risk_config_file') and account.risk_config_file and
                    hasattr(account, 'config_overrides') and account.config_overrides):
                    errors.append(
                        f"Account '{account.name}' (ID: {account.id}) specifies both "
                        f"risk_config_file and config_overrides. Choose one. "
                        f"Fix: Use risk_config_file for complete custom config, "
                        f"OR use config_overrides for partial overrides (not both)."
                    )

        return errors


class ModelValidatorMixins:
    """
    Mixin classes containing @model_validator methods for Pydantic models.

    These are meant to be added to Pydantic models to provide cross-field validation.
    Each mixin contains validators for a specific category of validation.
    """

    class TimeRangeValidator:
        """Validates time ranges (end > start)."""

        @staticmethod
        def validate_time_range(start: str, end: str, start_name: str = "start", end_name: str = "end") -> None:
            """
            Validate end time is after start time.

            Args:
                start: Start time (HH:MM)
                end: End time (HH:MM)
                start_name: Field name for start time (for errors)
                end_name: Field name for end time (for errors)

            Raises:
                ValueError: If end <= start
            """
            start_time = datetime.strptime(start, '%H:%M').time()
            end_time = datetime.strptime(end, '%H:%M').time()

            if end_time <= start_time:
                raise ValueError(
                    f"Session {end_name} ({end}) must be after {start_name} ({start}). "
                    f"Reason: Cannot have an end time before start time. "
                    f"Fix: Swap the times or correct the values. "
                    f"Example: start='09:30', end='16:00'"
                )

    class LossHierarchyValidator:
        """Validates loss limit hierarchy (unrealized < realized)."""

        @staticmethod
        def validate_loss_hierarchy(unrealized_limit: float, realized_limit: float) -> None:
            """
            Validate unrealized loss limit is smaller than realized loss limit.

            Args:
                unrealized_limit: Unrealized loss limit (negative)
                realized_limit: Realized loss limit (negative)

            Raises:
                ValueError: If unrealized >= realized (in absolute value)
            """
            unrealized_abs = abs(unrealized_limit)
            realized_abs = abs(realized_limit)

            if unrealized_abs >= realized_abs:
                raise ValueError(
                    f"Unrealized loss limit ({unrealized_limit}) should be LESS than "
                    f"realized loss limit ({realized_limit}) in absolute value. "
                    f"Reason: Unrealized loss should trigger before realized loss "
                    f"to provide early warning. "
                    f"Fix: Make unrealized limit smaller. "
                    f"Example: unrealized=-200, realized=-500"
                )

    class ContractHierarchyValidator:
        """Validates contract limit hierarchy (per-instrument <= total)."""

        @staticmethod
        def validate_contract_hierarchy(per_instrument_limit: int, total_limit: int) -> None:
            """
            Validate per-instrument limit does not exceed total limit.

            Args:
                per_instrument_limit: Limit for single instrument
                total_limit: Total account limit

            Raises:
                ValueError: If per_instrument > total
            """
            if per_instrument_limit > total_limit:
                raise ValueError(
                    f"Per-instrument limit ({per_instrument_limit}) cannot exceed "
                    f"total account limit ({total_limit}). "
                    f"Reason: Single instrument cannot have more contracts than entire account. "
                    f"Fix: Reduce per-instrument limit or increase total limit. "
                    f"Example: per_instrument=2, total=5"
                )

    class FrequencyHierarchyValidator:
        """Validates frequency limit hierarchy (minute <= hour <= session)."""

        @staticmethod
        def validate_frequency_hierarchy(
            per_minute: int | None,
            per_hour: int | None,
            per_session: int | None
        ) -> None:
            """
            Validate frequency limits form a valid hierarchy.

            Args:
                per_minute: Trades per minute limit
                per_hour: Trades per hour limit
                per_session: Trades per session limit

            Raises:
                ValueError: If hierarchy is invalid
            """
            # Check per_minute * 60 <= per_hour
            if per_minute and per_hour:
                if per_minute * 60 > per_hour:
                    raise ValueError(
                        f"per_minute ({per_minute}) * 60 = {per_minute * 60} exceeds "
                        f"per_hour ({per_hour}). "
                        f"Reason: If you can trade {per_minute} times per minute, "
                        f"you could trade {per_minute * 60} times in an hour. "
                        f"Fix: Reduce per_minute or increase per_hour. "
                        f"Example: per_minute=3, per_hour=10 (not 180)"
                    )

            # Check per_hour * 8 <= per_session (assume 8-hour session)
            if per_hour and per_session:
                if per_hour * 8 > per_session:
                    raise ValueError(
                        f"per_hour ({per_hour}) * 8 = {per_hour * 8} exceeds "
                        f"per_session ({per_session}). "
                        f"Reason: Assuming 8-hour session, you could trade "
                        f"{per_hour * 8} times. "
                        f"Fix: Reduce per_hour or increase per_session. "
                        f"Example: per_hour=10, per_session=50 (not 80)"
                    )

    class CategoryEnforcementValidator:
        """Validates enforcement actions match rule category."""

        @staticmethod
        def validate_trade_by_trade_enforcement(
            close_all: bool,
            close_position: bool,
            rule_name: str
        ) -> None:
            """
            Validate trade-by-trade rule enforcement actions.

            Trade-by-trade rules MUST:
            - close_all=false (only close violating position)
            - close_position=true (must close something)

            Args:
                close_all: Whether to close all positions
                close_position: Whether to close violating position
                rule_name: Name of rule (for error messages)

            Raises:
                ValueError: If enforcement doesn't match category
            """
            if close_all:
                raise ValueError(
                    f"{rule_name} is a trade-by-trade rule and MUST have close_all=false. "
                    f"Reason: Trade-by-trade rules only close the violating position, "
                    f"not all positions. "
                    f"Fix: Set close_all=false."
                )

            if not close_position:
                raise ValueError(
                    f"{rule_name} is a trade-by-trade rule and MUST have close_position=true. "
                    f"Reason: The rule must take action on violation. "
                    f"Fix: Set close_position=true."
                )

        @staticmethod
        def validate_hard_lockout_enforcement(
            close_all: bool,
            lockout_type: str,
            rule_name: str
        ) -> None:
            """
            Validate hard lockout rule enforcement actions.

            Hard lockout rules MUST:
            - close_all=true (close all positions)
            - lockout_type="hard" (hard lockout)

            Args:
                close_all: Whether to close all positions
                lockout_type: Type of lockout
                rule_name: Name of rule (for error messages)

            Raises:
                ValueError: If enforcement doesn't match category
            """
            if not close_all:
                raise ValueError(
                    f"{rule_name} is a hard lockout rule and MUST have close_all=true. "
                    f"Reason: Hard lockout rules close all positions when triggered. "
                    f"Fix: Set close_all=true."
                )

            if lockout_type != 'hard':
                raise ValueError(
                    f"{rule_name} is a hard lockout rule and MUST have lockout_type='hard'. "
                    f"Reason: This rule category requires hard lockouts. "
                    f"Fix: Set lockout_type='hard' (you have '{lockout_type}')."
                )


def format_validation_errors(validation_error: ValidationError) -> str:
    """
    Format Pydantic validation errors for user-friendly display.

    Args:
        validation_error: Pydantic ValidationError

    Returns:
        Formatted error message string

    Example:
        try:
            config = RiskConfig(**data)
        except ValidationError as e:
            print(format_validation_errors(e))
    """
    lines = [
        "Configuration Validation Failed",
        "=" * 80,
        f"{len(validation_error.errors())} validation error(s) found:",
        ""
    ]

    for i, error in enumerate(validation_error.errors(), 1):
        # Get field location
        loc = ' -> '.join(str(x) for x in error['loc'])

        # Get error message
        msg = error['msg']

        # Format error
        lines.append(f"Error {i}: {loc}")
        lines.append(f"  {msg}")
        lines.append("")

    return '\n'.join(lines)


# Export all validators and helpers
__all__ = [
    'ValidationHelpers',
    'ConfigValidator',
    'ModelValidatorMixins',
    'format_validation_errors',
]
