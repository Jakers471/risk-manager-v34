"""
Pydantic Configuration Models for Risk Manager V34

This module contains ALL configuration models for the four config files:
1. timers_config.yaml - Daily resets, lockouts, session hours, holidays
2. risk_config.yaml - All 13 risk rules
3. accounts.yaml - Account credentials and multi-account support
4. api_config.yaml - API connection settings

All models use Pydantic v2 with comprehensive validation.
"""

import re
from datetime import date, time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# ==============================================================================
# TIMERS CONFIGURATION MODELS
# ==============================================================================


class DailyResetConfig(BaseModel):
    """Daily reset configuration for daily P&L limits (RULE-003, RULE-013)."""

    time: str = Field(
        ...,
        description="Reset time in 24-hour format (HH:MM). Example: '17:00' for 5:00 PM",
    )
    timezone: str = Field(
        ...,
        description="IANA timezone string. Examples: 'America/Chicago', 'America/New_York', 'Europe/London'",
    )
    enabled: bool = Field(
        default=True,
        description="Enable/disable daily reset. If false, limits never reset automatically",
    )

    class ResetActions(BaseModel):
        """Actions to perform at daily reset time."""

        clear_daily_pnl: bool = Field(
            default=True, description="Reset daily P&L counters to $0.00"
        )
        unlock_daily_loss: bool = Field(
            default=True, description="Unlock RULE-003 (Daily Realized Loss)"
        )
        unlock_daily_profit: bool = Field(
            default=True, description="Unlock RULE-013 (Daily Realized Profit)"
        )
        clear_trade_count: bool = Field(
            default=True, description="Reset trade frequency counters"
        )

    reset_actions: ResetActions = Field(
        default_factory=ResetActions, description="Actions to perform at reset"
    )

    @field_validator("time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time is in HH:MM format (24-hour)."""
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError(
                f"Invalid time format: {v}. Must be HH:MM in 24-hour format (e.g., '17:00')"
            )
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone is a valid IANA timezone string."""
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(
                f"Invalid timezone: {v}. Must be IANA timezone (e.g., 'America/Chicago', not 'CST')"
            )
        return v


class TradeFrequencyLockoutConfig(BaseModel):
    """Lockout durations for trade frequency breaches (RULE-006)."""

    per_minute_breach: str = Field(
        default="60s",
        description="Lockout duration for per-minute breach. Example: '60s' = 1 minute",
    )
    per_hour_breach: str = Field(
        default="30m",
        description="Lockout duration for per-hour breach. Example: '30m' = 30 minutes",
    )
    per_session_breach: str = Field(
        default="1h",
        description="Lockout duration for per-session breach. Example: '1h' = 1 hour",
    )


class TimerCooldownConfig(BaseModel):
    """Lockout durations for timer/cooldown rules."""

    trade_frequency: TradeFrequencyLockoutConfig = Field(
        default_factory=TradeFrequencyLockoutConfig,
        description="RULE-006: Trade Frequency Limit lockout durations",
    )
    cooldown_after_loss: str = Field(
        default="15m",
        description="RULE-007: Cooldown After Loss duration. Example: '15m' = 15 minutes",
    )


class HardLockoutConfig(BaseModel):
    """Lockout durations for hard lockout rules."""

    daily_realized_loss: str = Field(
        default="until_reset",
        description="RULE-003: Daily Realized Loss lockout. Options: 'until_reset', '24h', 'permanent'",
    )
    daily_realized_profit: str = Field(
        default="until_reset",
        description="RULE-013: Daily Realized Profit lockout. Options: 'until_reset', '24h', 'permanent'",
    )
    session_block_outside: str = Field(
        default="until_session_start",
        description="RULE-009: Session Block Outside lockout. Options: 'until_session_start', '1h', 'permanent'",
    )
    auth_loss_guard: str = Field(
        default="permanent",
        description="RULE-010: Auth Loss Guard lockout. Must be 'permanent' (requires admin unlock)",
    )

    @field_validator("auth_loss_guard")
    @classmethod
    def validate_auth_loss_guard_permanent(cls, v: str) -> str:
        """Auth Loss Guard must be permanent (cannot be time-based)."""
        if v != "permanent":
            raise ValueError(
                "auth_loss_guard lockout must be 'permanent' (requires admin unlock)"
            )
        return v


class LockoutDurationsConfig(BaseModel):
    """Lockout duration configuration for all rule categories."""

    hard_lockout: HardLockoutConfig = Field(
        default_factory=HardLockoutConfig,
        description="Hard lockout rules (RULE-003, RULE-013, RULE-009, RULE-010)",
    )
    timer_cooldown: TimerCooldownConfig = Field(
        default_factory=TimerCooldownConfig,
        description="Timer/cooldown rules (RULE-006, RULE-007)",
    )

    @field_validator("hard_lockout", "timer_cooldown", mode="before")
    @classmethod
    def validate_all_durations(cls, v: Any) -> Any:
        """Validate all duration strings in nested configs."""
        if isinstance(v, dict):
            # Validate all string values that look like durations
            for key, value in v.items():
                if isinstance(value, str):
                    cls._validate_duration_format(value, key)
                elif isinstance(value, dict):
                    # Nested config (like trade_frequency)
                    for nested_key, nested_value in value.items():
                        if isinstance(nested_value, str):
                            cls._validate_duration_format(nested_value, nested_key)
        return v

    @staticmethod
    def _validate_duration_format(duration: str, field_name: str) -> None:
        """Validate duration string format."""
        # Special values are allowed
        special_values = ["until_reset", "until_session_start", "permanent"]
        if duration in special_values:
            return

        # Check format: \d+[smh]
        if not re.match(r"^\d+[smh]$", duration):
            raise ValueError(
                f"Invalid duration for {field_name}: {duration}. "
                f"Use format: <number><unit> (e.g., '60s', '15m', '1h') "
                f"or special values: {', '.join(special_values)}"
            )

        # Validate range
        match = re.match(r"^(\d+)([smh])$", duration)
        if match:
            value, unit = match.groups()
            value = int(value)

            if unit == "s" and not (1 <= value <= 86400):
                raise ValueError(
                    f"Duration in seconds must be 1-86400 (1 second to 24 hours), got: {duration}"
                )
            elif unit == "m" and not (1 <= value <= 1440):
                raise ValueError(
                    f"Duration in minutes must be 1-1440 (1 minute to 24 hours), got: {duration}"
                )
            elif unit == "h" and not (1 <= value <= 24):
                raise ValueError(
                    f"Duration in hours must be 1-24 (1 hour to 24 hours), got: {duration}"
                )


class PreMarketConfig(BaseModel):
    """Pre-market trading configuration."""

    enabled: bool = Field(
        default=False, description="Allow pre-market trading. Default: false"
    )
    start: str = Field(
        default="07:00",
        description="Pre-market start time (HH:MM). Only used if enabled=true",
    )

    @field_validator("start")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format."""
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError(f"Invalid time format: {v}. Use HH:MM (24-hour)")
        return v


class AfterHoursConfig(BaseModel):
    """After-hours trading configuration."""

    enabled: bool = Field(
        default=False, description="Allow after-hours trading. Default: false"
    )
    end: str = Field(
        default="20:00",
        description="After-hours end time (HH:MM). Only used if enabled=true",
    )

    @field_validator("end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format."""
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError(f"Invalid time format: {v}. Use HH:MM (24-hour)")
        return v


class SessionHoursConfig(BaseModel):
    """Session hours configuration for RULE-009 (Session Block Outside)."""

    start: str = Field(
        ..., description="Session start time (HH:MM). Example: '08:30' for 8:30 AM"
    )
    end: str = Field(
        ..., description="Session end time (HH:MM). Example: '15:00' for 3:00 PM"
    )
    timezone: str = Field(
        ...,
        description="IANA timezone string. Examples: 'America/Chicago', 'America/New_York'",
    )
    enabled: bool = Field(
        default=True,
        description="Enable/disable session restrictions. If false, trading allowed any time",
    )
    allowed_days: list[int] = Field(
        default=[0, 1, 2, 3, 4],
        description="Allowed trading days (0=Monday, 6=Sunday). Example: [0,1,2,3,4] = weekdays only",
    )

    pre_market: PreMarketConfig = Field(
        default_factory=PreMarketConfig, description="Pre-market trading settings"
    )
    after_hours: AfterHoursConfig = Field(
        default_factory=AfterHoursConfig, description="After-hours trading settings"
    )

    @field_validator("start", "end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time is in HH:MM format."""
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError(f"Invalid time: {v}. Use HH:MM (24-hour format)")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone is valid IANA timezone."""
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {v}. Use IANA timezone")
        return v

    @field_validator("allowed_days")
    @classmethod
    def validate_allowed_days(cls, v: list[int]) -> list[int]:
        """Validate allowed days are 0-6."""
        if not v:
            raise ValueError("allowed_days cannot be empty")

        for day in v:
            if day not in range(7):
                raise ValueError(
                    f"Invalid day: {day}. Must be 0-6 (0=Monday, 6=Sunday)"
                )

        return v

    @model_validator(mode="after")
    def validate_end_after_start(self) -> "SessionHoursConfig":
        """Validate end time is after start time."""
        if self.end <= self.start:
            raise ValueError(
                f"Session end ({self.end}) must be after start ({self.start})"
            )

        # Validate pre-market if enabled
        if self.pre_market.enabled and self.pre_market.start >= self.start:
            raise ValueError(
                f"Pre-market start ({self.pre_market.start}) must be before session start ({self.start})"
            )

        # Validate after-hours if enabled
        if self.after_hours.enabled and self.after_hours.end <= self.end:
            raise ValueError(
                f"After-hours end ({self.after_hours.end}) must be after session end ({self.end})"
            )

        return self


class EarlyCloseConfig(BaseModel):
    """Early close day configuration."""

    date: str = Field(
        ..., description="Early close date (YYYY-MM-DD). Example: '2025-11-26'"
    )
    close_time: str = Field(
        ..., description="Early close time (HH:MM). Example: '13:00' for 1:00 PM"
    )

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in YYYY-MM-DD format."""
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError(
                f"Invalid date format: {v}. Use YYYY-MM-DD (e.g., '2025-01-01')"
            )
        # Validate it's a valid date
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date: {v}")
        return v

    @field_validator("close_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format."""
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError(f"Invalid time: {v}. Use HH:MM (24-hour)")
        return v


class HolidaysConfig(BaseModel):
    """Market holidays configuration."""

    enabled: bool = Field(
        default=True,
        description="Enable/disable holiday checks. If false, holidays are ignored",
    )
    dates: dict[int, list[str]] = Field(
        default_factory=dict,
        description="Holiday dates by year. Example: {2025: ['2025-01-01', '2025-07-04']}",
    )
    early_close: list[EarlyCloseConfig] = Field(
        default_factory=list,
        description="Early close days (e.g., day before Thanksgiving)",
    )

    @field_validator("dates")
    @classmethod
    def validate_dates(cls, v: dict[int, list[str]]) -> dict[int, list[str]]:
        """Validate all dates are in correct format."""
        for year, dates in v.items():
            if not isinstance(year, int) or year < 2000 or year > 2100:
                raise ValueError(f"Invalid year: {year}. Must be 2000-2100")

            for date_str in dates:
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                    raise ValueError(
                        f"Invalid date format: {date_str}. Use YYYY-MM-DD"
                    )
                try:
                    date.fromisoformat(date_str)
                except ValueError:
                    raise ValueError(f"Invalid date: {date_str}")

        return v


class AutoUnlockConfig(BaseModel):
    """Auto-unlock behavior configuration."""

    enabled: bool = Field(
        default=True, description="Automatically unlock at reset time"
    )
    notify_on_unlock: bool = Field(
        default=True, description="Send notification when unlocked"
    )


class DSTConfig(BaseModel):
    """Daylight Saving Time handling configuration."""

    auto_adjust: bool = Field(default=True, description="Automatically adjust for DST")
    notify_on_change: bool = Field(
        default=True, description="Notify when DST changes occur"
    )


class AdvancedTimerConfig(BaseModel):
    """Advanced timer settings."""

    check_interval: int = Field(
        default=10,
        ge=1,
        description="How often to check time-based conditions (seconds)",
    )
    session_close_grace: int = Field(
        default=60,
        ge=0,
        description="Grace period before session close enforcement (seconds)",
    )
    auto_unlock: AutoUnlockConfig = Field(
        default_factory=AutoUnlockConfig, description="Auto-unlock behavior"
    )
    dst: DSTConfig = Field(
        default_factory=DSTConfig, description="Daylight Saving Time handling"
    )


class TimersConfig(BaseModel):
    """Complete timers configuration (timers_config.yaml)."""

    daily_reset: DailyResetConfig = Field(
        ..., description="Daily reset configuration for P&L limits"
    )
    lockout_durations: LockoutDurationsConfig = Field(
        ..., description="Lockout durations for all rule categories"
    )
    session_hours: SessionHoursConfig = Field(
        ..., description="Session hours configuration (RULE-009)"
    )
    holidays: HolidaysConfig = Field(
        default_factory=HolidaysConfig, description="Market holidays configuration"
    )
    advanced: AdvancedTimerConfig = Field(
        default_factory=AdvancedTimerConfig, description="Advanced timer settings"
    )

    @model_validator(mode="after")
    def validate_timezone_consistency(self) -> "TimersConfig":
        """Warn if daily_reset and session_hours have different timezones."""
        if self.daily_reset.timezone != self.session_hours.timezone:
            # This is a warning, not an error (user may have good reason)
            import warnings

            warnings.warn(
                f"Timezone mismatch: daily_reset uses '{self.daily_reset.timezone}' "
                f"but session_hours uses '{self.session_hours.timezone}'. "
                f"This may be intentional, but verify it's correct."
            )
        return self


# ==============================================================================
# RISK CONFIGURATION MODELS
# ==============================================================================


class DiscordConfig(BaseModel):
    """Discord notification configuration."""

    enabled: bool = Field(default=False, description="Enable Discord notifications")
    webhook_url: str = Field(default="", description="Discord webhook URL")


class TelegramConfig(BaseModel):
    """Telegram notification configuration."""

    enabled: bool = Field(default=False, description="Enable Telegram notifications")
    bot_token: str = Field(default="", description="Telegram bot token")
    chat_id: str = Field(default="", description="Telegram chat ID")


class NotificationsConfig(BaseModel):
    """Notifications configuration."""

    discord: DiscordConfig = Field(
        default_factory=DiscordConfig, description="Discord notifications"
    )
    telegram: TelegramConfig = Field(
        default_factory=TelegramConfig, description="Telegram notifications"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Log level"
    )
    log_to_file: bool = Field(default=True, description="Log to file")
    log_directory: str = Field(default="data/logs/", description="Log directory path")
    max_log_size_mb: int = Field(
        default=100, ge=1, description="Max log file size in MB"
    )
    log_retention_days: int = Field(
        default=30, ge=1, description="Log retention in days"
    )


class DatabaseConfig(BaseModel):
    """Database configuration."""

    path: str = Field(default="data/risk_state.db", description="Database file path")
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")
    backup_interval_hours: int = Field(
        default=24, ge=1, description="Backup interval in hours"
    )
    max_backups: int = Field(default=7, ge=1, description="Maximum backup files to keep")


class GeneralConfig(BaseModel):
    """General risk manager settings."""

    instruments: list[str] = Field(
        ..., min_length=1, description="Instruments to monitor (e.g., ['MNQ', 'ES'])"
    )
    timezone: str = Field(
        ...,
        description="IANA timezone string (e.g., 'America/Chicago', 'America/New_York')",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig, description="Database configuration"
    )
    notifications: NotificationsConfig = Field(
        default_factory=NotificationsConfig, description="Notifications configuration"
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone is valid IANA timezone."""
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {v}. Use IANA timezone")
        return v


# Trade-by-Trade Rules (Category 1)


class MaxContractsConfig(BaseModel):
    """RULE-001: Max Contracts - Account-wide contract limit."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    limit: int = Field(..., gt=0, description="Max net contracts (all instruments)")
    count_type: Literal["net", "gross"] = Field(
        default="net",
        description="Counting method: 'net' (long-short) or 'gross' (long+short)",
    )
    close_all: bool = Field(
        default=False, description="MUST be false for trade-by-trade rules"
    )
    close_position: bool = Field(default=True, description="Close violating position")
    reduce_to_limit: bool = Field(
        default=False, description="Alternative: reduce to limit instead of closing"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_false(cls, v: bool) -> bool:
        """Trade-by-trade rules must have close_all=false."""
        if v is not False:
            raise ValueError(
                "RULE-001 is trade-by-trade category, close_all must be false"
            )
        return v


class MaxContractsPerInstrumentConfig(BaseModel):
    """RULE-002: Max Contracts Per Instrument - Per-symbol contract limits."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    default_limit: int = Field(
        ...,
        gt=0,
        description="Default limit for instruments not specified in instrument_limits",
    )
    instrument_limits: dict[str, int] = Field(
        default_factory=dict,
        description="Per-instrument overrides. Example: {'MNQ': 2, 'ES': 1}",
    )
    close_all: bool = Field(
        default=False, description="MUST be false for trade-by-trade rules"
    )
    close_position: bool = Field(
        default=True, description="Close violating position (that instrument only)"
    )

    @field_validator("instrument_limits")
    @classmethod
    def validate_instrument_limits(cls, v: dict[str, int]) -> dict[str, int]:
        """Validate all limits are positive."""
        for symbol, limit in v.items():
            if limit <= 0:
                raise ValueError(
                    f"Instrument limit for {symbol} must be > 0, got: {limit}"
                )
        return v

    @field_validator("close_all")
    @classmethod
    def validate_close_all_false(cls, v: bool) -> bool:
        """Trade-by-trade rules must have close_all=false."""
        if v is not False:
            raise ValueError(
                "RULE-002 is trade-by-trade category, close_all must be false"
            )
        return v


class DailyUnrealizedLossConfig(BaseModel):
    """RULE-004: Daily Unrealized Loss - Floating loss limit per position."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    limit: float = Field(
        ..., lt=0, description="Max floating loss per position (negative value, e.g., -200.0)"
    )
    check_interval_seconds: int = Field(
        default=10, ge=1, description="Check position P&L every N seconds"
    )
    close_all: bool = Field(
        default=False, description="MUST be false for trade-by-trade rules"
    )
    close_position: bool = Field(
        default=True, description="Close only the losing position"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_false(cls, v: bool) -> bool:
        """Trade-by-trade rules must have close_all=false."""
        if v is not False:
            raise ValueError(
                "RULE-004 is trade-by-trade category, close_all must be false"
            )
        return v


class MaxUnrealizedProfitConfig(BaseModel):
    """RULE-005: Max Unrealized Profit (Profit Target) - Take profit at target."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    target: float = Field(
        ..., gt=0, description="Profit target per position (positive value, e.g., 500.0)"
    )
    check_interval_seconds: int = Field(
        default=5, ge=1, description="Check position P&L every N seconds"
    )
    close_all: bool = Field(
        default=False, description="MUST be false for trade-by-trade rules"
    )
    close_position: bool = Field(
        default=True, description="Close only that winning position"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_false(cls, v: bool) -> bool:
        """Trade-by-trade rules must have close_all=false."""
        if v is not False:
            raise ValueError(
                "RULE-005 is trade-by-trade category, close_all must be false"
            )
        return v


class NoStopLossGraceConfig(BaseModel):
    """RULE-008: Stop-Loss Enforcement - Require stop-loss within time limit."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    require_within_seconds: int = Field(
        ..., gt=0, description="Must place stop within N seconds of opening position"
    )
    grace_period_seconds: int = Field(
        ..., gt=0, description="Grace period before enforcement starts"
    )
    close_all: bool = Field(
        default=False, description="MUST be false for trade-by-trade rules"
    )
    close_position: bool = Field(
        default=True, description="Close position without stop-loss"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_false(cls, v: bool) -> bool:
        """Trade-by-trade rules must have close_all=false."""
        if v is not False:
            raise ValueError(
                "RULE-008 is trade-by-trade category, close_all must be false"
            )
        return v

    @model_validator(mode="after")
    def validate_grace_period(self) -> "NoStopLossGraceConfig":
        """Grace period should be >= require_within_seconds."""
        if self.grace_period_seconds < self.require_within_seconds:
            import warnings

            warnings.warn(
                f"grace_period_seconds ({self.grace_period_seconds}) is less than "
                f"require_within_seconds ({self.require_within_seconds}). "
                f"Consider making grace period >= require_within."
            )
        return self


class SymbolBlocksConfig(BaseModel):
    """RULE-011: Symbol Blocks (Blacklist) - Block trading in specific symbols."""

    enabled: bool = Field(
        default=False, description="Enable/disable rule (disabled by default)"
    )
    blocked_symbols: list[str] = Field(
        default_factory=list,
        description="Blacklisted symbols (e.g., ['ES', 'NQ']). Empty = none blocked",
    )
    close_all: bool = Field(
        default=False, description="MUST be false for trade-by-trade rules"
    )
    close_position: bool = Field(
        default=True, description="Close position in blocked symbol"
    )
    close_immediately: bool = Field(
        default=True, description="Close without warning (immediate enforcement)"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_false(cls, v: bool) -> bool:
        """Trade-by-trade rules must have close_all=false."""
        if v is not False:
            raise ValueError(
                "RULE-011 is trade-by-trade category, close_all must be false"
            )
        return v


# Timer/Cooldown Rules (Category 2)


class FrequencyLimitsConfig(BaseModel):
    """Trade frequency limits for RULE-006."""

    per_minute: int = Field(..., gt=0, description="Max trades per minute")
    per_hour: int = Field(..., gt=0, description="Max trades per hour")
    per_session: int = Field(..., gt=0, description="Max trades per session")

    @model_validator(mode="after")
    def validate_logical_hierarchy(self) -> "FrequencyLimitsConfig":
        """Validate per_minute <= per_hour <= per_session."""
        if self.per_minute > self.per_hour:
            raise ValueError(
                f"per_minute ({self.per_minute}) cannot exceed per_hour ({self.per_hour})"
            )
        if self.per_hour > self.per_session:
            raise ValueError(
                f"per_hour ({self.per_hour}) cannot exceed per_session ({self.per_session})"
            )
        return self


class TradeFrequencyLimitConfig(BaseModel):
    """RULE-006: Trade Frequency Limit - Limit trading frequency."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    limits: FrequencyLimitsConfig = Field(
        ..., description="Frequency limits (per minute/hour/session)"
    )
    close_all: bool = Field(
        default=True, description="MUST be true for timer/cooldown rules"
    )
    cancel_orders: bool = Field(default=True, description="Cancel all pending orders")
    lockout_type: Literal["timer"] = Field(
        default="timer", description="MUST be 'timer' for this category"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_true(cls, v: bool) -> bool:
        """Timer/cooldown rules must have close_all=true."""
        if v is not True:
            raise ValueError(
                "RULE-006 is timer/cooldown category, close_all must be true"
            )
        return v


class CooldownAfterLossConfig(BaseModel):
    """RULE-007: Cooldown After Loss - Cooldown after losing trade."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    loss_threshold: float = Field(
        ..., lt=0, description="Loss threshold to trigger cooldown (negative, e.g., -100.0)"
    )
    close_all: bool = Field(
        default=True, description="MUST be true for timer/cooldown rules"
    )
    cancel_orders: bool = Field(default=True, description="Cancel all pending orders")
    lockout_type: Literal["timer"] = Field(
        default="timer", description="MUST be 'timer' for this category"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_true(cls, v: bool) -> bool:
        """Timer/cooldown rules must have close_all=true."""
        if v is not True:
            raise ValueError(
                "RULE-007 is timer/cooldown category, close_all must be true"
            )
        return v


# Hard Lockout Rules (Category 3)


class DailyRealizedLossConfig(BaseModel):
    """RULE-003: Daily Realized Loss - Max daily loss limit."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    limit: float = Field(
        ..., lt=0, description="Max daily realized loss (negative, e.g., -500.0)"
    )
    close_all: bool = Field(
        default=True, description="MUST be true for hard lockout rules"
    )
    cancel_orders: bool = Field(default=True, description="Cancel all pending orders")
    lockout_type: Literal["hard"] = Field(
        default="hard", description="MUST be 'hard' for this category"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_true(cls, v: bool) -> bool:
        """Hard lockout rules must have close_all=true."""
        if v is not True:
            raise ValueError(
                "RULE-003 is hard lockout category, close_all must be true"
            )
        return v


class DailyRealizedProfitConfig(BaseModel):
    """RULE-013: Daily Realized Profit - Daily profit target."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    target: float = Field(
        ..., gt=0, description="Daily profit target (positive, e.g., 1000.0)"
    )
    message: str = Field(
        default="Daily profit target reached! Good job! See you tomorrow.",
        description="Message to display when target reached",
    )
    close_all: bool = Field(
        default=True, description="MUST be true for hard lockout rules"
    )
    cancel_orders: bool = Field(
        default=True, description="Stop further trading (cancel orders)"
    )
    lockout_type: Literal["hard"] = Field(
        default="hard", description="MUST be 'hard' for this category"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_true(cls, v: bool) -> bool:
        """Hard lockout rules must have close_all=true."""
        if v is not True:
            raise ValueError(
                "RULE-013 is hard lockout category, close_all must be true"
            )
        return v


class SessionBlockOutsideConfig(BaseModel):
    """RULE-009: Session Block Outside - Block trading outside session hours."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    respect_holidays: bool = Field(
        default=True, description="Check holidays from timers_config.yaml"
    )
    close_all: bool = Field(
        default=True, description="MUST be true for hard lockout rules"
    )
    cancel_orders: bool = Field(default=True, description="Cancel all pending orders")
    lockout_type: Literal["hard"] = Field(
        default="hard", description="MUST be 'hard' for this category"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_true(cls, v: bool) -> bool:
        """Hard lockout rules must have close_all=true."""
        if v is not True:
            raise ValueError(
                "RULE-009 is hard lockout category, close_all must be true"
            )
        return v


class AuthLossGuardConfig(BaseModel):
    """RULE-010: Auth Loss Guard - Monitor account canTrade status."""

    enabled: bool = Field(default=True, description="Enable/disable rule")
    check_interval_seconds: int = Field(
        default=30, ge=10, description="Check canTrade status every N seconds"
    )
    reason: str = Field(
        default="API canTrade status is false - account disabled",
        description="Reason displayed when triggered",
    )
    close_all: bool = Field(
        default=True, description="MUST be true for hard lockout rules"
    )
    cancel_orders: bool = Field(default=True, description="Cancel all pending orders")
    lockout_type: Literal["hard"] = Field(
        default="hard", description="MUST be 'hard' for this category"
    )
    lockout_permanently: bool = Field(
        default=True, description="MUST be true (requires admin unlock)"
    )

    @field_validator("close_all")
    @classmethod
    def validate_close_all_true(cls, v: bool) -> bool:
        """Hard lockout rules must have close_all=true."""
        if v is not True:
            raise ValueError(
                "RULE-010 is hard lockout category, close_all must be true"
            )
        return v

    @field_validator("lockout_permanently")
    @classmethod
    def validate_lockout_permanently_true(cls, v: bool) -> bool:
        """Auth loss guard must lockout permanently."""
        if v is not True:
            raise ValueError("RULE-010 must have lockout_permanently=true")
        return v


# Automation (Category 4)


class AutoBreakevenConfig(BaseModel):
    """Auto breakeven settings for RULE-012."""

    enabled: bool = Field(default=True, description="Enable auto breakeven")
    profit_threshold_ticks: int = Field(
        ..., gt=0, description="Move stop to breakeven after N ticks profit"
    )
    offset_ticks: int = Field(
        default=1, ge=0, description="Offset from breakeven (safety margin)"
    )


class TrailingStopConfig(BaseModel):
    """Trailing stop settings for RULE-012."""

    enabled: bool = Field(default=True, description="Enable trailing stop")
    trail_ticks: int = Field(..., gt=0, description="Trail by N ticks")
    activation_profit_ticks: int = Field(
        ..., gt=0, description="Activate trail after N ticks profit"
    )


class TradeManagementConfig(BaseModel):
    """RULE-012: Trade Management - Automated trade management (breakeven, trailing)."""

    enabled: bool = Field(
        default=False, description="Enable/disable rule (disabled by default - advanced)"
    )
    auto_breakeven: AutoBreakevenConfig = Field(
        default_factory=AutoBreakevenConfig, description="Auto breakeven settings"
    )
    trailing_stop: TrailingStopConfig = Field(
        default_factory=TrailingStopConfig, description="Trailing stop settings"
    )

    @model_validator(mode="after")
    def validate_activation_threshold(self) -> "TradeManagementConfig":
        """Validate activation_profit_ticks >= profit_threshold_ticks."""
        if self.enabled:
            if (
                self.trailing_stop.activation_profit_ticks
                < self.auto_breakeven.profit_threshold_ticks
            ):
                import warnings

                warnings.warn(
                    f"trailing_stop.activation_profit_ticks ({self.trailing_stop.activation_profit_ticks}) "
                    f"should be >= auto_breakeven.profit_threshold_ticks ({self.auto_breakeven.profit_threshold_ticks})"
                )
        return self


# Rules Container


class RulesConfig(BaseModel):
    """All 13 risk rules configuration."""

    # Trade-by-Trade Rules (6 rules)
    max_contracts: MaxContractsConfig = Field(
        ..., description="RULE-001: Max Contracts"
    )
    max_contracts_per_instrument: MaxContractsPerInstrumentConfig = Field(
        ..., description="RULE-002: Max Contracts Per Instrument"
    )
    daily_unrealized_loss: DailyUnrealizedLossConfig = Field(
        ..., description="RULE-004: Daily Unrealized Loss"
    )
    max_unrealized_profit: MaxUnrealizedProfitConfig = Field(
        ..., description="RULE-005: Max Unrealized Profit (Profit Target)"
    )
    no_stop_loss_grace: NoStopLossGraceConfig = Field(
        ..., description="RULE-008: Stop-Loss Enforcement"
    )
    symbol_blocks: SymbolBlocksConfig = Field(
        default_factory=SymbolBlocksConfig, description="RULE-011: Symbol Blocks"
    )

    # Timer/Cooldown Rules (2 rules)
    trade_frequency_limit: TradeFrequencyLimitConfig = Field(
        ..., description="RULE-006: Trade Frequency Limit"
    )
    cooldown_after_loss: CooldownAfterLossConfig = Field(
        ..., description="RULE-007: Cooldown After Loss"
    )

    # Hard Lockout Rules (4 rules)
    daily_realized_loss: DailyRealizedLossConfig = Field(
        ..., description="RULE-003: Daily Realized Loss"
    )
    daily_realized_profit: DailyRealizedProfitConfig = Field(
        ..., description="RULE-013: Daily Realized Profit"
    )
    session_block_outside: SessionBlockOutsideConfig = Field(
        ..., description="RULE-009: Session Block Outside"
    )
    auth_loss_guard: AuthLossGuardConfig = Field(
        ..., description="RULE-010: Auth Loss Guard"
    )

    # Automation (1 rule)
    trade_management: TradeManagementConfig = Field(
        default_factory=TradeManagementConfig, description="RULE-012: Trade Management"
    )

    @model_validator(mode="after")
    def validate_cross_rule_consistency(self) -> "RulesConfig":
        """Validate consistency across rules."""
        # Loss limits: unrealized should trigger before realized
        if (
            self.daily_unrealized_loss.enabled
            and self.daily_realized_loss.enabled
            and self.daily_unrealized_loss.limit < self.daily_realized_loss.limit
        ):
            import warnings

            warnings.warn(
                f"daily_unrealized_loss.limit ({self.daily_unrealized_loss.limit}) "
                f"should be >= daily_realized_loss.limit ({self.daily_realized_loss.limit}) "
                f"to trigger before realized loss"
            )

        # Profit targets: per-position should be less than daily total
        if (
            self.max_unrealized_profit.enabled
            and self.daily_realized_profit.enabled
            and self.max_unrealized_profit.target > self.daily_realized_profit.target
        ):
            import warnings

            warnings.warn(
                f"max_unrealized_profit.target ({self.max_unrealized_profit.target}) "
                f"should be <= daily_realized_profit.target ({self.daily_realized_profit.target})"
            )

        return self


class RiskConfig(BaseModel):
    """Complete risk configuration (risk_config.yaml)."""

    general: GeneralConfig = Field(..., description="General risk manager settings")
    rules: RulesConfig = Field(..., description="All 13 risk rules configuration")


# ==============================================================================
# ACCOUNTS CONFIGURATION MODELS
# ==============================================================================


class TopstepXConfig(BaseModel):
    """TopstepX API credentials."""

    username: str = Field(..., min_length=1, description="TopstepX username")
    api_key: str = Field(..., min_length=1, description="TopstepX API key")
    api_url: str = Field(
        default="https://api.topstepx.com/api", description="REST API endpoint"
    )
    websocket_url: str = Field(
        default="wss://api.topstepx.com", description="WebSocket endpoint"
    )

    @field_validator("api_url", "websocket_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL starts with https:// or wss://."""
        if not v.startswith(("https://", "wss://")):
            raise ValueError(f"URL must start with https:// or wss://, got: {v}")
        return v


class MonitoredAccountConfig(BaseModel):
    """Single account configuration (simple mode)."""

    account_id: str = Field(..., min_length=1, description="Account ID")
    account_type: Literal["practice", "live"] = Field(
        ..., description="Account type: 'practice' or 'live'"
    )
    description: str | None = Field(
        default=None, description="Optional account description"
    )


class AccountConfig(BaseModel):
    """Multi-account configuration with per-account overrides."""

    id: str = Field(..., min_length=1, description="Account ID (must be unique)")
    name: str = Field(..., min_length=1, description="Display name")
    account_type: Literal["practice", "live"] = Field(
        ..., description="Account type: 'practice' or 'live'"
    )
    description: str | None = Field(
        default=None, description="Optional account description"
    )
    risk_config_file: str | None = Field(
        default=None, description="Path to custom risk config file (optional)"
    )
    config_overrides: dict[str, Any] | None = Field(
        default=None, description="Rule overrides (alternative to risk_config_file)"
    )

    @field_validator("risk_config_file")
    @classmethod
    def validate_file_exists(cls, v: str | None) -> str | None:
        """Validate config file exists if specified."""
        if v and not Path(v).exists():
            raise ValueError(f"Config file not found: {v}")
        return v

    @model_validator(mode="after")
    def validate_exclusive_config(self) -> "AccountConfig":
        """Cannot specify both risk_config_file and config_overrides."""
        if self.risk_config_file and self.config_overrides:
            raise ValueError(
                "Cannot specify both risk_config_file and config_overrides. "
                "Choose one configuration method."
            )
        return self


class AccountsConfig(BaseModel):
    """Complete accounts configuration (accounts.yaml)."""

    topstepx: TopstepXConfig = Field(..., description="TopstepX API credentials")
    monitored_account: MonitoredAccountConfig | None = Field(
        default=None, description="Single account mode (simple)"
    )
    accounts: list[AccountConfig] | None = Field(
        default=None, description="Multi-account mode (advanced)"
    )

    @model_validator(mode="after")
    def validate_unique_account_ids(self) -> "AccountsConfig":
        """Validate account IDs are unique in multi-account mode."""
        if self.accounts:
            ids = [acc.id for acc in self.accounts]
            if len(ids) != len(set(ids)):
                raise ValueError("Account IDs must be unique")
        return self


# ==============================================================================
# API CONFIGURATION MODELS
# ==============================================================================


class ProjectXConfig(BaseModel):
    """ProjectX API authentication configuration."""

    username: str = Field(..., min_length=1, description="ProjectX username")
    api_key: str = Field(..., min_length=1, description="ProjectX API key")
    api_url: str = Field(
        default="https://api.topstepx.com/api", description="REST API URL"
    )
    websocket_url: str = Field(
        default="wss://api.topstepx.com", description="WebSocket URL"
    )
    environment: Literal["production", "sandbox"] = Field(
        default="production", description="API environment"
    )

    @field_validator("api_url", "websocket_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("https://", "wss://")):
            raise ValueError(f"Invalid URL: {v}")
        return v


class RetryConfig(BaseModel):
    """Retry behavior configuration."""

    enabled: bool = Field(default=True, description="Enable automatic retries")
    max_attempts: int = Field(default=3, ge=1, description="Max retry attempts")
    backoff_multiplier: float = Field(
        default=2.0, ge=1.0, description="Exponential backoff multiplier"
    )
    max_backoff_seconds: int = Field(
        default=60, gt=0, description="Max backoff time in seconds"
    )


class ReconnectConfig(BaseModel):
    """WebSocket reconnection configuration."""

    enabled: bool = Field(
        default=True, description="Auto-reconnect on WebSocket disconnect"
    )
    initial_delay: int = Field(
        default=1, ge=1, description="Initial reconnect delay (seconds)"
    )
    max_delay: int = Field(
        default=300, ge=1, description="Max reconnect delay (seconds)"
    )
    max_attempts: int = Field(
        default=0, ge=0, description="Max reconnect attempts (0=infinite)"
    )

    @model_validator(mode="after")
    def validate_delays(self) -> "ReconnectConfig":
        """Validate initial_delay <= max_delay."""
        if self.initial_delay > self.max_delay:
            raise ValueError("initial_delay must be <= max_delay")
        return self


class KeepAliveConfig(BaseModel):
    """WebSocket keep-alive configuration."""

    enabled: bool = Field(default=True, description="Send ping/pong keep-alive")
    interval_seconds: int = Field(
        default=30, ge=1, description="Ping interval (seconds)"
    )
    timeout_seconds: int = Field(default=10, ge=1, description="Pong timeout (seconds)")


class ConnectionConfig(BaseModel):
    """Connection settings configuration."""

    connect_timeout: int = Field(
        default=30, gt=0, description="Initial connection timeout (seconds)"
    )
    request_timeout: int = Field(
        default=10, gt=0, description="API request timeout (seconds)"
    )
    websocket_timeout: int = Field(
        default=60, gt=0, description="WebSocket message timeout (seconds)"
    )
    retry: RetryConfig = Field(default_factory=RetryConfig, description="Retry behavior")
    reconnect: ReconnectConfig = Field(
        default_factory=ReconnectConfig, description="Reconnection behavior"
    )
    keep_alive: KeepAliveConfig = Field(
        default_factory=KeepAliveConfig, description="Keep-alive settings"
    )


class RateLimitRequestsConfig(BaseModel):
    """API request rate limits."""

    per_second: int = Field(default=10, gt=0, description="Max requests per second")
    per_minute: int = Field(default=100, gt=0, description="Max requests per minute")
    per_hour: int = Field(default=1000, gt=0, description="Max requests per hour")


class RateLimitBurstConfig(BaseModel):
    """Burst request allowance."""

    enabled: bool = Field(default=True, description="Allow burst requests")
    size: int = Field(default=20, gt=0, description="Burst size (requests)")


class RateLimitOrdersConfig(BaseModel):
    """Order placement rate limits."""

    per_second: int = Field(default=2, gt=0, description="Max orders per second")
    per_minute: int = Field(default=30, gt=0, description="Max orders per minute")


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    requests: RateLimitRequestsConfig = Field(
        default_factory=RateLimitRequestsConfig, description="API request rate limits"
    )
    burst: RateLimitBurstConfig = Field(
        default_factory=RateLimitBurstConfig, description="Burst allowance"
    )
    orders: RateLimitOrdersConfig = Field(
        default_factory=RateLimitOrdersConfig, description="Order placement rate limits"
    )


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""

    enabled: bool = Field(default=True, description="Enable circuit breaker")
    failure_threshold: int = Field(
        default=5, ge=1, description="Open after N failures"
    )
    timeout_seconds: int = Field(
        default=60, gt=0, description="Try again after N seconds"
    )
    half_open_attempts: int = Field(
        default=3, ge=1, description="Test with N requests in half-open state"
    )


class ErrorHandlingConfig(BaseModel):
    """Error handling configuration."""

    retry_on_status: list[int] = Field(
        default=[429, 500, 502, 503, 504],
        description="Retry on these HTTP status codes",
    )
    fatal_status: list[int] = Field(
        default=[401, 403, 404], description="Fatal errors (do not retry)"
    )
    circuit_breaker: CircuitBreakerConfig = Field(
        default_factory=CircuitBreakerConfig, description="Circuit breaker settings"
    )


class CacheAccountConfig(BaseModel):
    """Account data cache configuration."""

    ttl_seconds: int = Field(default=300, gt=0, description="Cache TTL (seconds)")
    max_size: int = Field(default=100, gt=0, description="Max cached items")


class CacheInstrumentsConfig(BaseModel):
    """Instrument data cache configuration."""

    ttl_seconds: int = Field(default=3600, gt=0, description="Cache TTL (seconds)")
    max_size: int = Field(default=500, gt=0, description="Max cached items")


class CacheMarketDataConfig(BaseModel):
    """Market data cache configuration."""

    ttl_seconds: int = Field(
        default=1, gt=0, description="Cache TTL (seconds, real-time)"
    )
    max_size: int = Field(default=1000, gt=0, description="Max cached items")


class CacheConfig(BaseModel):
    """Caching configuration."""

    enabled: bool = Field(default=True, description="Enable caching")
    account: CacheAccountConfig = Field(
        default_factory=CacheAccountConfig, description="Account data cache"
    )
    instruments: CacheInstrumentsConfig = Field(
        default_factory=CacheInstrumentsConfig, description="Instrument data cache"
    )
    market_data: CacheMarketDataConfig = Field(
        default_factory=CacheMarketDataConfig, description="Market data cache"
    )


class ApiLoggingConfig(BaseModel):
    """API logging configuration."""

    log_requests: bool = Field(default=True, description="Log all API requests")
    log_responses: bool = Field(
        default=False, description="Log responses (verbose)"
    )
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Log level"
    )
    mask_credentials: bool = Field(
        default=True, description="Mask API keys in logs"
    )
    mask_account_ids: bool = Field(
        default=False, description="Mask account IDs in logs"
    )
    log_slow_requests: bool = Field(
        default=True, description="Log slow requests"
    )
    slow_threshold_ms: int = Field(
        default=1000, gt=0, description="Slow request threshold (milliseconds)"
    )


class ConnectionPoolConfig(BaseModel):
    """Connection pool configuration."""

    max_connections: int = Field(
        default=10, ge=1, description="Max concurrent connections"
    )
    max_keepalive: int = Field(
        default=5, ge=1, description="Max keepalive connections"
    )


class SSLConfig(BaseModel):
    """SSL/TLS configuration."""

    verify: bool = Field(default=True, description="Verify SSL certificates")
    cert_path: str | None = Field(
        default=None, description="Custom CA certificate path (optional)"
    )


class AdvancedApiConfig(BaseModel):
    """Advanced API settings."""

    http2: bool = Field(default=False, description="Use HTTP/2 (HTTP/1.1 more compatible)")
    compression: bool = Field(default=True, description="Enable gzip compression")
    user_agent: str = Field(
        default="RiskManager/3.4 (TopstepX)", description="User agent string"
    )
    connection_pool: ConnectionPoolConfig = Field(
        default_factory=ConnectionPoolConfig, description="Connection pool settings"
    )
    ssl: SSLConfig = Field(default_factory=SSLConfig, description="SSL/TLS settings")


class ApiConfig(BaseModel):
    """Complete API configuration (api_config.yaml)."""

    projectx: ProjectXConfig = Field(..., description="ProjectX API credentials")
    connection: ConnectionConfig = Field(
        default_factory=ConnectionConfig, description="Connection settings"
    )
    rate_limit: RateLimitConfig = Field(
        default_factory=RateLimitConfig, description="Rate limiting"
    )
    error_handling: ErrorHandlingConfig = Field(
        default_factory=ErrorHandlingConfig, description="Error handling"
    )
    cache: CacheConfig = Field(default_factory=CacheConfig, description="Caching")
    logging: ApiLoggingConfig = Field(
        default_factory=ApiLoggingConfig, description="API logging"
    )
    advanced: AdvancedApiConfig = Field(
        default_factory=AdvancedApiConfig, description="Advanced settings"
    )
