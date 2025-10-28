"""
Comprehensive unit tests for src/risk_manager/config/models.py

This file tests all Pydantic configuration models including:
1. Field validators (@field_validator) - time, timezone, duration, URL, etc.
2. Model validators (@model_validator) - cross-field validation
3. Nested model validation
4. Edge cases and warnings

Target: Boost coverage from 59.22% to 75%+
"""

import warnings
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from risk_manager.config.models import (
    # Timers Configuration
    DailyResetConfig,
    TradeFrequencyLockoutConfig,
    HardLockoutConfig,
    LockoutDurationsConfig,
    SessionHoursConfig,
    PreMarketConfig,
    AfterHoursConfig,
    EarlyCloseConfig,
    HolidaysConfig,
    TimersConfig,
    # Risk Configuration
    MaxContractsConfig,
    MaxContractsPerInstrumentConfig,
    DailyUnrealizedLossConfig,
    MaxUnrealizedProfitConfig,
    NoStopLossGraceConfig,
    SymbolBlocksConfig,
    FrequencyLimitsConfig,
    TradeFrequencyLimitConfig,
    CooldownAfterLossConfig,
    DailyRealizedLossConfig,
    DailyRealizedProfitConfig,
    SessionBlockOutsideConfig,
    AuthLossGuardConfig,
    TradeManagementConfig,
    AutoBreakevenConfig,
    TrailingStopConfig,
    RulesConfig,
    RiskConfig,
    GeneralConfig,
    # Accounts Configuration
    TopstepXConfig,
    MonitoredAccountConfig,
    AccountConfig,
    AccountsConfig,
    # API Configuration
    ProjectXConfig,
    RetryConfig,
    ReconnectConfig,
    ConnectionConfig,
    ApiConfig,
)


# ==============================================================================
# TIMERS CONFIGURATION TESTS
# ==============================================================================


class TestDailyResetConfig:
    """Test DailyResetConfig model and validators."""

    def test_valid_config(self):
        """Test valid daily reset configuration."""
        config = DailyResetConfig(
            time="17:00",
            timezone="America/Chicago",
            enabled=True
        )

        assert config.time == "17:00"
        assert config.timezone == "America/Chicago"
        assert config.enabled is True

    def test_valid_time_formats(self):
        """Test various valid time formats."""
        valid_times = ["00:00", "09:30", "15:00", "17:00", "23:59"]

        for time_str in valid_times:
            config = DailyResetConfig(
                time=time_str,
                timezone="America/Chicago"
            )
            assert config.time == time_str

    def test_invalid_time_format_hour_too_high(self):
        """Test invalid time with hour > 23 raises error."""
        with pytest.raises(ValidationError, match="Invalid time format"):
            DailyResetConfig(
                time="25:00",
                timezone="America/Chicago"
            )

    def test_invalid_time_format_minute_too_high(self):
        """Test invalid time with minute > 59 raises error."""
        with pytest.raises(ValidationError, match="Invalid time format"):
            DailyResetConfig(
                time="17:60",
                timezone="America/Chicago"
            )

    def test_invalid_time_format_no_colon(self):
        """Test invalid time format without colon raises error."""
        with pytest.raises(ValidationError, match="Invalid time format"):
            DailyResetConfig(
                time="1700",
                timezone="America/Chicago"
            )

    def test_invalid_time_format_12hour(self):
        """Test 12-hour format (5:00 PM) raises error."""
        with pytest.raises(ValidationError, match="Invalid time format"):
            DailyResetConfig(
                time="5:00 PM",
                timezone="America/Chicago"
            )

    def test_invalid_time_format_single_digit(self):
        """Test single-digit hour raises error."""
        with pytest.raises(ValidationError, match="Invalid time format"):
            DailyResetConfig(
                time="5:00",
                timezone="America/Chicago"
            )

    def test_valid_timezone_us_central(self):
        """Test valid US/Central timezone."""
        config = DailyResetConfig(
            time="17:00",
            timezone="America/Chicago"
        )
        assert config.timezone == "America/Chicago"

    def test_valid_timezone_us_eastern(self):
        """Test valid US/Eastern timezone."""
        config = DailyResetConfig(
            time="17:00",
            timezone="America/New_York"
        )
        assert config.timezone == "America/New_York"

    def test_valid_timezone_europe(self):
        """Test valid Europe timezone."""
        config = DailyResetConfig(
            time="17:00",
            timezone="Europe/London"
        )
        assert config.timezone == "Europe/London"

    def test_invalid_timezone_abbreviation(self):
        """Test timezone abbreviation (CST) raises error."""
        with pytest.raises(ValidationError, match="Invalid timezone"):
            DailyResetConfig(
                time="17:00",
                timezone="CST"
            )

    def test_invalid_timezone_typo(self):
        """Test typo in timezone raises error."""
        with pytest.raises(ValidationError, match="Invalid timezone"):
            DailyResetConfig(
                time="17:00",
                timezone="America/Chicag"  # Missing 'o'
            )

    def test_invalid_timezone_fake(self):
        """Test completely invalid timezone raises error."""
        with pytest.raises(ValidationError, match="Invalid timezone"):
            DailyResetConfig(
                time="17:00",
                timezone="FakePlace/FakeCity"
            )

    def test_default_enabled_true(self):
        """Test default enabled value is True."""
        config = DailyResetConfig(
            time="17:00",
            timezone="America/Chicago"
        )
        assert config.enabled is True

    def test_reset_actions_default_all_true(self):
        """Test default reset actions are all True."""
        config = DailyResetConfig(
            time="17:00",
            timezone="America/Chicago"
        )

        assert config.reset_actions.clear_daily_pnl is True
        assert config.reset_actions.unlock_daily_loss is True
        assert config.reset_actions.unlock_daily_profit is True
        assert config.reset_actions.clear_trade_count is True


class TestHardLockoutConfig:
    """Test HardLockoutConfig model and validators."""

    def test_valid_config_defaults(self):
        """Test valid hard lockout config with defaults."""
        config = HardLockoutConfig()

        assert config.daily_realized_loss == "until_reset"
        assert config.daily_realized_profit == "until_reset"
        assert config.session_block_outside == "until_session_start"
        assert config.auth_loss_guard == "permanent"

    def test_auth_loss_guard_must_be_permanent(self):
        """Test auth_loss_guard must be 'permanent'."""
        config = HardLockoutConfig()
        assert config.auth_loss_guard == "permanent"

    def test_auth_loss_guard_time_duration_raises_error(self):
        """Test auth_loss_guard with time duration raises error."""
        with pytest.raises(ValidationError, match="must be 'permanent'"):
            HardLockoutConfig(auth_loss_guard="1h")

    def test_auth_loss_guard_until_reset_raises_error(self):
        """Test auth_loss_guard='until_reset' raises error."""
        with pytest.raises(ValidationError, match="must be 'permanent'"):
            HardLockoutConfig(auth_loss_guard="until_reset")

    def test_other_lockouts_can_be_until_reset(self):
        """Test other lockouts can use 'until_reset'."""
        config = HardLockoutConfig(
            daily_realized_loss="until_reset",
            daily_realized_profit="until_reset",
            session_block_outside="until_session_start"
        )

        assert config.daily_realized_loss == "until_reset"
        assert config.daily_realized_profit == "until_reset"


class TestLockoutDurationsConfig:
    """Test LockoutDurationsConfig model and duration validators."""

    def test_valid_duration_seconds(self):
        """Test valid duration in seconds."""
        config = LockoutDurationsConfig(
            timer_cooldown={"cooldown_after_loss": "60s"}
        )
        assert config.timer_cooldown.cooldown_after_loss == "60s"

    def test_valid_duration_minutes(self):
        """Test valid duration in minutes."""
        config = LockoutDurationsConfig(
            timer_cooldown={"cooldown_after_loss": "15m"}
        )
        assert config.timer_cooldown.cooldown_after_loss == "15m"

    def test_valid_duration_hours(self):
        """Test valid duration in hours."""
        config = LockoutDurationsConfig(
            timer_cooldown={"cooldown_after_loss": "2h"}
        )
        assert config.timer_cooldown.cooldown_after_loss == "2h"

    def test_valid_special_value_until_reset(self):
        """Test special value 'until_reset' is valid."""
        config = LockoutDurationsConfig(
            hard_lockout={"daily_realized_loss": "until_reset"}
        )
        assert config.hard_lockout.daily_realized_loss == "until_reset"

    def test_valid_special_value_permanent(self):
        """Test special value 'permanent' is valid."""
        config = LockoutDurationsConfig(
            hard_lockout={"auth_loss_guard": "permanent"}
        )
        assert config.hard_lockout.auth_loss_guard == "permanent"

    def test_invalid_duration_no_unit(self):
        """Test duration without unit raises error."""
        with pytest.raises(ValidationError, match="Invalid duration"):
            LockoutDurationsConfig(
                timer_cooldown={"cooldown_after_loss": "60"}
            )

    def test_invalid_duration_wrong_format(self):
        """Test duration with wrong format raises error."""
        with pytest.raises(ValidationError, match="Invalid duration"):
            LockoutDurationsConfig(
                timer_cooldown={"cooldown_after_loss": "60 seconds"}
            )

    def test_invalid_duration_seconds_out_of_range_too_high(self):
        """Test duration in seconds > 86400 raises error."""
        with pytest.raises(ValidationError, match="must be 1-86400"):
            LockoutDurationsConfig(
                timer_cooldown={"cooldown_after_loss": "99999s"}
            )

    def test_invalid_duration_seconds_out_of_range_zero(self):
        """Test duration of 0s raises error."""
        with pytest.raises(ValidationError, match="must be 1-86400"):
            LockoutDurationsConfig(
                timer_cooldown={"cooldown_after_loss": "0s"}
            )

    def test_invalid_duration_minutes_out_of_range(self):
        """Test duration in minutes > 1440 raises error."""
        with pytest.raises(ValidationError, match="must be 1-1440"):
            LockoutDurationsConfig(
                timer_cooldown={"cooldown_after_loss": "9999m"}
            )

    def test_invalid_duration_hours_out_of_range(self):
        """Test duration in hours > 24 raises error."""
        with pytest.raises(ValidationError, match="must be 1-24"):
            LockoutDurationsConfig(
                timer_cooldown={"cooldown_after_loss": "99h"}
            )

    def test_nested_trade_frequency_durations(self):
        """Test nested trade frequency lockout durations validate."""
        config = LockoutDurationsConfig(
            timer_cooldown={
                "trade_frequency": {
                    "per_minute_breach": "30s",
                    "per_hour_breach": "15m",
                    "per_session_breach": "1h"
                }
            }
        )

        assert config.timer_cooldown.trade_frequency.per_minute_breach == "30s"
        assert config.timer_cooldown.trade_frequency.per_hour_breach == "15m"
        assert config.timer_cooldown.trade_frequency.per_session_breach == "1h"


class TestSessionHoursConfig:
    """Test SessionHoursConfig model and validators."""

    def test_valid_config(self):
        """Test valid session hours configuration."""
        config = SessionHoursConfig(
            start="08:30",
            end="15:00",
            timezone="America/Chicago"
        )

        assert config.start == "08:30"
        assert config.end == "15:00"
        assert config.timezone == "America/Chicago"

    def test_end_after_start_valid(self):
        """Test end time after start time is valid."""
        config = SessionHoursConfig(
            start="09:00",
            end="17:00",
            timezone="America/Chicago"
        )

        assert config.start == "09:00"
        assert config.end == "17:00"

    def test_end_before_start_raises_error(self):
        """Test end time before start time raises error."""
        with pytest.raises(ValidationError, match="must be after start"):
            SessionHoursConfig(
                start="17:00",
                end="09:00",
                timezone="America/Chicago"
            )

    def test_end_equals_start_raises_error(self):
        """Test end time equal to start time raises error."""
        with pytest.raises(ValidationError, match="must be after start"):
            SessionHoursConfig(
                start="15:00",
                end="15:00",
                timezone="America/Chicago"
            )

    def test_allowed_days_default_weekdays(self):
        """Test default allowed_days is weekdays (0-4)."""
        config = SessionHoursConfig(
            start="08:30",
            end="15:00",
            timezone="America/Chicago"
        )

        assert config.allowed_days == [0, 1, 2, 3, 4]

    def test_allowed_days_valid_range(self):
        """Test allowed_days with valid range (0-6)."""
        config = SessionHoursConfig(
            start="08:30",
            end="15:00",
            timezone="America/Chicago",
            allowed_days=[0, 2, 4, 6]  # Mon, Wed, Fri, Sun
        )

        assert config.allowed_days == [0, 2, 4, 6]

    def test_allowed_days_empty_raises_error(self):
        """Test empty allowed_days raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            SessionHoursConfig(
                start="08:30",
                end="15:00",
                timezone="America/Chicago",
                allowed_days=[]
            )

    def test_allowed_days_out_of_range_raises_error(self):
        """Test allowed_days with day > 6 raises error."""
        with pytest.raises(ValidationError, match="Must be 0-6"):
            SessionHoursConfig(
                start="08:30",
                end="15:00",
                timezone="America/Chicago",
                allowed_days=[0, 1, 7]  # 7 is invalid
            )

    def test_allowed_days_negative_raises_error(self):
        """Test allowed_days with negative day raises error."""
        with pytest.raises(ValidationError, match="Must be 0-6"):
            SessionHoursConfig(
                start="08:30",
                end="15:00",
                timezone="America/Chicago",
                allowed_days=[-1, 0, 1]
            )

    def test_pre_market_enabled_before_start(self):
        """Test pre-market enabled with start before session start."""
        config = SessionHoursConfig(
            start="09:00",
            end="15:00",
            timezone="America/Chicago",
            pre_market={"enabled": True, "start": "07:00"}
        )

        assert config.pre_market.enabled is True
        assert config.pre_market.start == "07:00"

    def test_pre_market_after_session_start_raises_error(self):
        """Test pre-market start after session start raises error."""
        with pytest.raises(ValidationError, match="must be before session start"):
            SessionHoursConfig(
                start="09:00",
                end="15:00",
                timezone="America/Chicago",
                pre_market={"enabled": True, "start": "09:30"}
            )

    def test_pre_market_equals_session_start_raises_error(self):
        """Test pre-market start equal to session start raises error."""
        with pytest.raises(ValidationError, match="must be before session start"):
            SessionHoursConfig(
                start="09:00",
                end="15:00",
                timezone="America/Chicago",
                pre_market={"enabled": True, "start": "09:00"}
            )

    def test_after_hours_enabled_after_end(self):
        """Test after-hours enabled with end after session end."""
        config = SessionHoursConfig(
            start="09:00",
            end="15:00",
            timezone="America/Chicago",
            after_hours={"enabled": True, "end": "20:00"}
        )

        assert config.after_hours.enabled is True
        assert config.after_hours.end == "20:00"

    def test_after_hours_before_session_end_raises_error(self):
        """Test after-hours end before session end raises error."""
        with pytest.raises(ValidationError, match="must be after session end"):
            SessionHoursConfig(
                start="09:00",
                end="15:00",
                timezone="America/Chicago",
                after_hours={"enabled": True, "end": "14:00"}
            )

    def test_after_hours_equals_session_end_raises_error(self):
        """Test after-hours end equal to session end raises error."""
        with pytest.raises(ValidationError, match="must be after session end"):
            SessionHoursConfig(
                start="09:00",
                end="15:00",
                timezone="America/Chicago",
                after_hours={"enabled": True, "end": "15:00"}
            )


class TestEarlyCloseConfig:
    """Test EarlyCloseConfig model and validators."""

    def test_valid_config(self):
        """Test valid early close configuration."""
        config = EarlyCloseConfig(
            date="2025-11-26",
            close_time="13:00"
        )

        assert config.date == "2025-11-26"
        assert config.close_time == "13:00"

    def test_valid_date_formats(self):
        """Test various valid date formats."""
        valid_dates = ["2025-01-01", "2025-12-31", "2030-06-15"]

        for date_str in valid_dates:
            config = EarlyCloseConfig(
                date=date_str,
                close_time="13:00"
            )
            assert config.date == date_str

    def test_invalid_date_format_no_dashes(self):
        """Test invalid date format without dashes raises error."""
        with pytest.raises(ValidationError, match="Invalid date format"):
            EarlyCloseConfig(
                date="20251126",
                close_time="13:00"
            )

    def test_invalid_date_format_slash(self):
        """Test invalid date format with slashes raises error."""
        with pytest.raises(ValidationError, match="Invalid date format"):
            EarlyCloseConfig(
                date="11/26/2025",
                close_time="13:00"
            )

    def test_invalid_date_value(self):
        """Test invalid date value raises error."""
        with pytest.raises(ValidationError, match="Invalid date"):
            EarlyCloseConfig(
                date="2025-13-01",  # Month 13 doesn't exist
                close_time="13:00"
            )

    def test_invalid_date_feb_30(self):
        """Test invalid date (Feb 30) raises error."""
        with pytest.raises(ValidationError, match="Invalid date"):
            EarlyCloseConfig(
                date="2025-02-30",
                close_time="13:00"
            )

    def test_valid_close_time_format(self):
        """Test valid close time format."""
        config = EarlyCloseConfig(
            date="2025-11-26",
            close_time="13:00"
        )
        assert config.close_time == "13:00"

    def test_invalid_close_time_format(self):
        """Test invalid close time format raises error."""
        with pytest.raises(ValidationError, match="Invalid time"):
            EarlyCloseConfig(
                date="2025-11-26",
                close_time="1:00 PM"
            )


class TestHolidaysConfig:
    """Test HolidaysConfig model and validators."""

    def test_valid_config_empty(self):
        """Test valid holidays config with empty dates."""
        config = HolidaysConfig()

        assert config.enabled is True
        assert config.dates == {}
        assert config.early_close == []

    def test_valid_dates_single_year(self):
        """Test valid dates for single year."""
        config = HolidaysConfig(
            dates={2025: ["2025-01-01", "2025-07-04", "2025-12-25"]}
        )

        assert 2025 in config.dates
        assert len(config.dates[2025]) == 3

    def test_valid_dates_multiple_years(self):
        """Test valid dates for multiple years."""
        config = HolidaysConfig(
            dates={
                2025: ["2025-01-01"],
                2026: ["2026-01-01"]
            }
        )

        assert 2025 in config.dates
        assert 2026 in config.dates

    def test_invalid_year_too_low(self):
        """Test year < 2000 raises error."""
        with pytest.raises(ValidationError, match="Invalid year"):
            HolidaysConfig(
                dates={1999: ["1999-01-01"]}
            )

    def test_invalid_year_too_high(self):
        """Test year > 2100 raises error."""
        with pytest.raises(ValidationError, match="Invalid year"):
            HolidaysConfig(
                dates={2101: ["2101-01-01"]}
            )

    def test_invalid_date_format_in_list(self):
        """Test invalid date format in list raises error."""
        with pytest.raises(ValidationError, match="Invalid date format"):
            HolidaysConfig(
                dates={2025: ["01/01/2025"]}
            )

    def test_invalid_date_value_in_list(self):
        """Test invalid date value in list raises error."""
        with pytest.raises(ValidationError, match="Invalid date"):
            HolidaysConfig(
                dates={2025: ["2025-13-32"]}
            )

    def test_early_close_list(self):
        """Test early close list with EarlyCloseConfig objects."""
        config = HolidaysConfig(
            early_close=[
                {"date": "2025-11-26", "close_time": "13:00"},
                {"date": "2025-12-24", "close_time": "13:00"}
            ]
        )

        assert len(config.early_close) == 2
        assert config.early_close[0].date == "2025-11-26"


class TestTimersConfig:
    """Test TimersConfig model and cross-timezone warnings."""

    def test_valid_config_same_timezone(self):
        """Test valid config with same timezone."""
        config = TimersConfig(
            daily_reset={
                "time": "17:00",
                "timezone": "America/Chicago"
            },
            lockout_durations={},
            session_hours={
                "start": "08:30",
                "end": "15:00",
                "timezone": "America/Chicago"
            }
        )

        assert config.daily_reset.timezone == config.session_hours.timezone

    def test_timezone_mismatch_triggers_warning(self):
        """Test timezone mismatch triggers warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            TimersConfig(
                daily_reset={
                    "time": "17:00",
                    "timezone": "America/Chicago"
                },
                lockout_durations={},
                session_hours={
                    "start": "08:30",
                    "end": "15:00",
                    "timezone": "America/New_York"  # Different!
                }
            )

            assert len(w) == 1
            assert "Timezone mismatch" in str(w[0].message)


# ==============================================================================
# RISK CONFIGURATION TESTS
# ==============================================================================


class TestMaxContractsConfig:
    """Test MaxContractsConfig model and validators."""

    def test_valid_config(self):
        """Test valid max contracts configuration."""
        config = MaxContractsConfig(
            enabled=True,
            limit=5
        )

        assert config.enabled is True
        assert config.limit == 5
        assert config.close_all is False

    def test_limit_must_be_positive(self):
        """Test limit must be > 0."""
        with pytest.raises(ValidationError, match="greater than 0"):
            MaxContractsConfig(
                enabled=True,
                limit=0
            )

    def test_limit_negative_raises_error(self):
        """Test negative limit raises error."""
        with pytest.raises(ValidationError, match="greater than 0"):
            MaxContractsConfig(
                enabled=True,
                limit=-5
            )

    def test_close_all_must_be_false(self):
        """Test close_all must be false for trade-by-trade rule."""
        config = MaxContractsConfig(
            enabled=True,
            limit=5
        )
        assert config.close_all is False

    def test_close_all_true_raises_error(self):
        """Test close_all=true raises error for trade-by-trade rule."""
        with pytest.raises(ValidationError, match="close_all must be false"):
            MaxContractsConfig(
                enabled=True,
                limit=5,
                close_all=True
            )

    def test_count_type_net_default(self):
        """Test count_type defaults to 'net'."""
        config = MaxContractsConfig(
            enabled=True,
            limit=5
        )
        assert config.count_type == "net"

    def test_count_type_gross(self):
        """Test count_type can be 'gross'."""
        config = MaxContractsConfig(
            enabled=True,
            limit=5,
            count_type="gross"
        )
        assert config.count_type == "gross"


class TestMaxContractsPerInstrumentConfig:
    """Test MaxContractsPerInstrumentConfig model and validators."""

    def test_valid_config(self):
        """Test valid per-instrument config."""
        config = MaxContractsPerInstrumentConfig(
            enabled=True,
            default_limit=2,
            instrument_limits={"MNQ": 2, "ES": 1}
        )

        assert config.default_limit == 2
        assert config.instrument_limits["MNQ"] == 2
        assert config.close_all is False

    def test_instrument_limits_positive_only(self):
        """Test instrument limits must be positive."""
        with pytest.raises(ValidationError, match="must be > 0"):
            MaxContractsPerInstrumentConfig(
                enabled=True,
                default_limit=2,
                instrument_limits={"MNQ": 0}
            )

    def test_instrument_limits_negative_raises_error(self):
        """Test negative instrument limit raises error."""
        with pytest.raises(ValidationError, match="must be > 0"):
            MaxContractsPerInstrumentConfig(
                enabled=True,
                default_limit=2,
                instrument_limits={"ES": -1}
            )

    def test_close_all_true_raises_error(self):
        """Test close_all=true raises error."""
        with pytest.raises(ValidationError, match="close_all must be false"):
            MaxContractsPerInstrumentConfig(
                enabled=True,
                default_limit=2,
                close_all=True
            )


class TestDailyUnrealizedLossConfig:
    """Test DailyUnrealizedLossConfig model and validators."""

    def test_valid_config(self):
        """Test valid unrealized loss config."""
        config = DailyUnrealizedLossConfig(
            enabled=True,
            limit=-200.0
        )

        assert config.limit == -200.0
        assert config.close_all is False

    def test_limit_must_be_negative(self):
        """Test limit must be negative (loss)."""
        with pytest.raises(ValidationError, match="less than 0"):
            DailyUnrealizedLossConfig(
                enabled=True,
                limit=200.0  # Positive not allowed
            )

    def test_limit_zero_raises_error(self):
        """Test limit of 0 raises error."""
        with pytest.raises(ValidationError, match="less than 0"):
            DailyUnrealizedLossConfig(
                enabled=True,
                limit=0.0
            )

    def test_close_all_true_raises_error(self):
        """Test close_all=true raises error."""
        with pytest.raises(ValidationError, match="close_all must be false"):
            DailyUnrealizedLossConfig(
                enabled=True,
                limit=-200.0,
                close_all=True
            )


class TestMaxUnrealizedProfitConfig:
    """Test MaxUnrealizedProfitConfig model and validators."""

    def test_valid_config(self):
        """Test valid unrealized profit config."""
        config = MaxUnrealizedProfitConfig(
            enabled=True,
            target=500.0
        )

        assert config.target == 500.0
        assert config.close_all is False

    def test_target_must_be_positive(self):
        """Test target must be positive (profit)."""
        with pytest.raises(ValidationError, match="greater than 0"):
            MaxUnrealizedProfitConfig(
                enabled=True,
                target=-500.0  # Negative not allowed
            )

    def test_target_zero_raises_error(self):
        """Test target of 0 raises error."""
        with pytest.raises(ValidationError, match="greater than 0"):
            MaxUnrealizedProfitConfig(
                enabled=True,
                target=0.0
            )

    def test_close_all_true_raises_error(self):
        """Test close_all=true raises error."""
        with pytest.raises(ValidationError, match="close_all must be false"):
            MaxUnrealizedProfitConfig(
                enabled=True,
                target=500.0,
                close_all=True
            )


class TestNoStopLossGraceConfig:
    """Test NoStopLossGraceConfig model and validators."""

    def test_valid_config(self):
        """Test valid stop-loss grace config."""
        config = NoStopLossGraceConfig(
            enabled=True,
            require_within_seconds=60,
            grace_period_seconds=90
        )

        assert config.require_within_seconds == 60
        assert config.grace_period_seconds == 90
        assert config.close_all is False

    def test_require_within_must_be_positive(self):
        """Test require_within_seconds must be > 0."""
        with pytest.raises(ValidationError, match="greater than 0"):
            NoStopLossGraceConfig(
                enabled=True,
                require_within_seconds=0,
                grace_period_seconds=60
            )

    def test_grace_period_must_be_positive(self):
        """Test grace_period_seconds must be > 0."""
        with pytest.raises(ValidationError, match="greater than 0"):
            NoStopLossGraceConfig(
                enabled=True,
                require_within_seconds=60,
                grace_period_seconds=0
            )

    def test_grace_period_less_than_require_within_warning(self):
        """Test warning when grace_period < require_within."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            NoStopLossGraceConfig(
                enabled=True,
                require_within_seconds=60,
                grace_period_seconds=30  # Less than require_within
            )

            assert len(w) == 1
            assert "grace_period_seconds" in str(w[0].message)

    def test_close_all_true_raises_error(self):
        """Test close_all=true raises error."""
        with pytest.raises(ValidationError, match="close_all must be false"):
            NoStopLossGraceConfig(
                enabled=True,
                require_within_seconds=60,
                grace_period_seconds=90,
                close_all=True
            )


class TestSymbolBlocksConfig:
    """Test SymbolBlocksConfig model and validators."""

    def test_valid_config(self):
        """Test valid symbol blocks config."""
        config = SymbolBlocksConfig(
            enabled=True,
            blocked_symbols=["ES", "NQ"]
        )

        assert config.blocked_symbols == ["ES", "NQ"]
        assert config.close_all is False

    def test_empty_blocked_symbols(self):
        """Test empty blocked_symbols list is valid."""
        config = SymbolBlocksConfig(
            enabled=False,
            blocked_symbols=[]
        )

        assert config.blocked_symbols == []

    def test_close_all_true_raises_error(self):
        """Test close_all=true raises error."""
        with pytest.raises(ValidationError, match="close_all must be false"):
            SymbolBlocksConfig(
                enabled=True,
                blocked_symbols=["ES"],
                close_all=True
            )


class TestFrequencyLimitsConfig:
    """Test FrequencyLimitsConfig model and validators."""

    def test_valid_config(self):
        """Test valid frequency limits config."""
        config = FrequencyLimitsConfig(
            per_minute=5,
            per_hour=50,
            per_session=200
        )

        assert config.per_minute == 5
        assert config.per_hour == 50
        assert config.per_session == 200

    def test_limits_must_be_positive(self):
        """Test limits must be > 0."""
        with pytest.raises(ValidationError, match="greater than 0"):
            FrequencyLimitsConfig(
                per_minute=0,
                per_hour=50,
                per_session=200
            )

    def test_logical_hierarchy_valid(self):
        """Test per_minute <= per_hour <= per_session."""
        config = FrequencyLimitsConfig(
            per_minute=5,
            per_hour=50,
            per_session=200
        )

        assert config.per_minute <= config.per_hour <= config.per_session

    def test_per_minute_greater_than_per_hour_raises_error(self):
        """Test per_minute > per_hour raises error."""
        with pytest.raises(ValidationError, match="cannot exceed per_hour"):
            FrequencyLimitsConfig(
                per_minute=100,
                per_hour=50,
                per_session=200
            )

    def test_per_hour_greater_than_per_session_raises_error(self):
        """Test per_hour > per_session raises error."""
        with pytest.raises(ValidationError, match="cannot exceed per_session"):
            FrequencyLimitsConfig(
                per_minute=5,
                per_hour=300,
                per_session=200
            )


class TestTradeFrequencyLimitConfig:
    """Test TradeFrequencyLimitConfig model and validators."""

    def test_valid_config(self):
        """Test valid trade frequency limit config."""
        config = TradeFrequencyLimitConfig(
            enabled=True,
            limits={"per_minute": 5, "per_hour": 50, "per_session": 200}
        )

        assert config.close_all is True
        assert config.lockout_type == "timer"

    def test_close_all_must_be_true(self):
        """Test close_all must be true for timer/cooldown rule."""
        config = TradeFrequencyLimitConfig(
            enabled=True,
            limits={"per_minute": 5, "per_hour": 50, "per_session": 200}
        )
        assert config.close_all is True

    def test_close_all_false_raises_error(self):
        """Test close_all=false raises error."""
        with pytest.raises(ValidationError, match="close_all must be true"):
            TradeFrequencyLimitConfig(
                enabled=True,
                limits={"per_minute": 5, "per_hour": 50, "per_session": 200},
                close_all=False
            )


class TestCooldownAfterLossConfig:
    """Test CooldownAfterLossConfig model and validators."""

    def test_valid_config(self):
        """Test valid cooldown after loss config."""
        config = CooldownAfterLossConfig(
            enabled=True,
            loss_threshold=-100.0
        )

        assert config.loss_threshold == -100.0
        assert config.close_all is True
        assert config.lockout_type == "timer"

    def test_loss_threshold_must_be_negative(self):
        """Test loss_threshold must be negative."""
        with pytest.raises(ValidationError, match="less than 0"):
            CooldownAfterLossConfig(
                enabled=True,
                loss_threshold=100.0  # Positive not allowed
            )

    def test_close_all_must_be_true(self):
        """Test close_all must be true for timer/cooldown rule."""
        config = CooldownAfterLossConfig(
            enabled=True,
            loss_threshold=-100.0
        )
        assert config.close_all is True

    def test_close_all_false_raises_error(self):
        """Test close_all=false raises error."""
        with pytest.raises(ValidationError, match="close_all must be true"):
            CooldownAfterLossConfig(
                enabled=True,
                loss_threshold=-100.0,
                close_all=False
            )


class TestDailyRealizedLossConfig:
    """Test DailyRealizedLossConfig model and validators."""

    def test_valid_config(self):
        """Test valid daily realized loss config."""
        config = DailyRealizedLossConfig(
            enabled=True,
            limit=-500.0
        )

        assert config.limit == -500.0
        assert config.close_all is True
        assert config.lockout_type == "hard"

    def test_limit_must_be_negative(self):
        """Test limit must be negative."""
        with pytest.raises(ValidationError, match="less than 0"):
            DailyRealizedLossConfig(
                enabled=True,
                limit=500.0  # Positive not allowed
            )

    def test_close_all_must_be_true(self):
        """Test close_all must be true for hard lockout rule."""
        config = DailyRealizedLossConfig(
            enabled=True,
            limit=-500.0
        )
        assert config.close_all is True

    def test_close_all_false_raises_error(self):
        """Test close_all=false raises error."""
        with pytest.raises(ValidationError, match="close_all must be true"):
            DailyRealizedLossConfig(
                enabled=True,
                limit=-500.0,
                close_all=False
            )


class TestDailyRealizedProfitConfig:
    """Test DailyRealizedProfitConfig model and validators."""

    def test_valid_config(self):
        """Test valid daily realized profit config."""
        config = DailyRealizedProfitConfig(
            enabled=True,
            target=1000.0
        )

        assert config.target == 1000.0
        assert config.close_all is True
        assert config.lockout_type == "hard"

    def test_target_must_be_positive(self):
        """Test target must be positive."""
        with pytest.raises(ValidationError, match="greater than 0"):
            DailyRealizedProfitConfig(
                enabled=True,
                target=-1000.0  # Negative not allowed
            )

    def test_close_all_must_be_true(self):
        """Test close_all must be true for hard lockout rule."""
        config = DailyRealizedProfitConfig(
            enabled=True,
            target=1000.0
        )
        assert config.close_all is True

    def test_close_all_false_raises_error(self):
        """Test close_all=false raises error."""
        with pytest.raises(ValidationError, match="close_all must be true"):
            DailyRealizedProfitConfig(
                enabled=True,
                target=1000.0,
                close_all=False
            )


class TestSessionBlockOutsideConfig:
    """Test SessionBlockOutsideConfig model and validators."""

    def test_valid_config(self):
        """Test valid session block outside config."""
        config = SessionBlockOutsideConfig(
            enabled=True
        )

        assert config.close_all is True
        assert config.lockout_type == "hard"

    def test_close_all_must_be_true(self):
        """Test close_all must be true for hard lockout rule."""
        config = SessionBlockOutsideConfig(
            enabled=True
        )
        assert config.close_all is True

    def test_close_all_false_raises_error(self):
        """Test close_all=false raises error."""
        with pytest.raises(ValidationError, match="close_all must be true"):
            SessionBlockOutsideConfig(
                enabled=True,
                close_all=False
            )


class TestAuthLossGuardConfig:
    """Test AuthLossGuardConfig model and validators."""

    def test_valid_config(self):
        """Test valid auth loss guard config."""
        config = AuthLossGuardConfig(
            enabled=True
        )

        assert config.close_all is True
        assert config.lockout_type == "hard"
        assert config.lockout_permanently is True

    def test_close_all_must_be_true(self):
        """Test close_all must be true for hard lockout rule."""
        config = AuthLossGuardConfig(
            enabled=True
        )
        assert config.close_all is True

    def test_close_all_false_raises_error(self):
        """Test close_all=false raises error."""
        with pytest.raises(ValidationError, match="close_all must be true"):
            AuthLossGuardConfig(
                enabled=True,
                close_all=False
            )

    def test_lockout_permanently_must_be_true(self):
        """Test lockout_permanently must be true."""
        config = AuthLossGuardConfig(
            enabled=True
        )
        assert config.lockout_permanently is True

    def test_lockout_permanently_false_raises_error(self):
        """Test lockout_permanently=false raises error."""
        with pytest.raises(ValidationError, match="must have lockout_permanently=true"):
            AuthLossGuardConfig(
                enabled=True,
                lockout_permanently=False
            )


class TestTradeManagementConfig:
    """Test TradeManagementConfig model and validators."""

    def test_valid_config(self):
        """Test valid trade management config."""
        config = TradeManagementConfig(
            enabled=True,
            auto_breakeven={"profit_threshold_ticks": 10},
            trailing_stop={"trail_ticks": 5, "activation_profit_ticks": 15}
        )

        assert config.auto_breakeven.profit_threshold_ticks == 10
        assert config.trailing_stop.activation_profit_ticks == 15

    def test_activation_threshold_warning(self):
        """Test warning when activation_profit_ticks < profit_threshold_ticks."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            TradeManagementConfig(
                enabled=True,
                auto_breakeven={"profit_threshold_ticks": 20},
                trailing_stop={"trail_ticks": 5, "activation_profit_ticks": 10}  # Less than 20
            )

            assert len(w) == 1
            assert "activation_profit_ticks" in str(w[0].message)


class TestRulesConfig:
    """Test RulesConfig model and cross-rule validation."""

    def test_loss_limit_hierarchy_warning(self):
        """Test warning when unrealized loss limit < realized loss limit."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            RulesConfig(
                max_contracts={"limit": 5},
                max_contracts_per_instrument={"default_limit": 2},
                daily_unrealized_loss={"limit": -600.0},  # -600 < -500, triggers warning
                max_unrealized_profit={"target": 200.0},
                no_stop_loss_grace={"require_within_seconds": 60, "grace_period_seconds": 90},
                trade_frequency_limit={"limits": {"per_minute": 5, "per_hour": 50, "per_session": 200}},
                cooldown_after_loss={"loss_threshold": -50.0},
                daily_realized_loss={"limit": -500.0},
                daily_realized_profit={"target": 1000.0},
                session_block_outside={},
                auth_loss_guard={},
                trade_management={
                    "enabled": False,
                    "auto_breakeven": {"profit_threshold_ticks": 10},
                    "trailing_stop": {"trail_ticks": 5, "activation_profit_ticks": 15}
                }
            )

            # Warning triggers when unrealized < realized (both negative)
            # -600 < -500 is True, so warning should trigger
            assert len(w) == 1
            assert "daily_unrealized_loss" in str(w[0].message)

    def test_profit_target_hierarchy_warning(self):
        """Test warning when per-position profit > daily profit."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            RulesConfig(
                max_contracts={"limit": 5},
                max_contracts_per_instrument={"default_limit": 2},
                daily_unrealized_loss={"limit": -200.0},
                max_unrealized_profit={"target": 2000.0},  # Higher than daily
                no_stop_loss_grace={"require_within_seconds": 60, "grace_period_seconds": 90},
                trade_frequency_limit={"limits": {"per_minute": 5, "per_hour": 50, "per_session": 200}},
                cooldown_after_loss={"loss_threshold": -50.0},
                daily_realized_loss={"limit": -500.0},
                daily_realized_profit={"target": 1000.0},  # Lower than per-position
                session_block_outside={},
                auth_loss_guard={},
                trade_management={
                    "enabled": False,
                    "auto_breakeven": {"profit_threshold_ticks": 10},
                    "trailing_stop": {"trail_ticks": 5, "activation_profit_ticks": 15}
                }
            )

            # Should trigger warning
            assert any("max_unrealized_profit" in str(warning.message) for warning in w)


# ==============================================================================
# ACCOUNTS CONFIGURATION TESTS
# ==============================================================================


class TestTopstepXConfig:
    """Test TopstepXConfig model and URL validators."""

    def test_valid_config(self):
        """Test valid TopstepX config."""
        config = TopstepXConfig(
            username="testuser",
            api_key="testkey123"
        )

        assert config.username == "testuser"
        assert config.api_key == "testkey123"

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        config = TopstepXConfig(
            username="testuser",
            api_key="testkey123",
            api_url="https://custom.api.com"
        )

        assert config.api_url == "https://custom.api.com"

    def test_valid_wss_url(self):
        """Test valid WSS URL."""
        config = TopstepXConfig(
            username="testuser",
            api_key="testkey123",
            websocket_url="wss://custom.ws.com"
        )

        assert config.websocket_url == "wss://custom.ws.com"

    def test_invalid_http_url_raises_error(self):
        """Test HTTP URL (not HTTPS) raises error."""
        with pytest.raises(ValidationError, match="must start with https:// or wss://"):
            TopstepXConfig(
                username="testuser",
                api_key="testkey123",
                api_url="http://insecure.com"
            )

    def test_invalid_ws_url_raises_error(self):
        """Test WS URL (not WSS) raises error."""
        with pytest.raises(ValidationError, match="must start with https:// or wss://"):
            TopstepXConfig(
                username="testuser",
                api_key="testkey123",
                websocket_url="ws://insecure.com"
            )

    def test_invalid_ftp_url_raises_error(self):
        """Test FTP URL raises error."""
        with pytest.raises(ValidationError, match="must start with https:// or wss://"):
            TopstepXConfig(
                username="testuser",
                api_key="testkey123",
                api_url="ftp://files.com"
            )


class TestAccountConfig:
    """Test AccountConfig model and validators."""

    def test_valid_config(self):
        """Test valid account config."""
        config = AccountConfig(
            id="ACC123",
            name="My Account",
            account_type="practice"
        )

        assert config.id == "ACC123"
        assert config.name == "My Account"
        assert config.account_type == "practice"

    def test_risk_config_file_exists(self, tmp_path):
        """Test risk_config_file validation with existing file."""
        config_file = tmp_path / "custom_risk.yaml"
        config_file.write_text("# test config")

        config = AccountConfig(
            id="ACC123",
            name="My Account",
            account_type="practice",
            risk_config_file=str(config_file)
        )

        assert config.risk_config_file == str(config_file)

    def test_risk_config_file_not_exists_raises_error(self):
        """Test risk_config_file with non-existent file raises error."""
        with pytest.raises(ValidationError, match="Config file not found"):
            AccountConfig(
                id="ACC123",
                name="My Account",
                account_type="practice",
                risk_config_file="/nonexistent/config.yaml"
            )

    def test_cannot_specify_both_file_and_overrides(self, tmp_path):
        """Test cannot specify both risk_config_file and config_overrides."""
        # Create a temp file so it passes the exists() check
        config_file = tmp_path / "test_risk.yaml"
        config_file.write_text("# test")

        with pytest.raises(ValidationError, match="Cannot specify both"):
            AccountConfig(
                id="ACC123",
                name="My Account",
                account_type="practice",
                risk_config_file=str(config_file),
                config_overrides={"max_contracts": 10}
            )


class TestAccountsConfig:
    """Test AccountsConfig model and validators."""

    def test_valid_config_multi_account(self):
        """Test valid multi-account configuration."""
        config = AccountsConfig(
            topstepx={"username": "user", "api_key": "key"},
            accounts=[
                {"id": "ACC1", "name": "Account 1", "account_type": "practice"},
                {"id": "ACC2", "name": "Account 2", "account_type": "live"}
            ]
        )

        assert len(config.accounts) == 2

    def test_duplicate_account_ids_raises_error(self):
        """Test duplicate account IDs raises error."""
        with pytest.raises(ValidationError, match="Account IDs must be unique"):
            AccountsConfig(
                topstepx={"username": "user", "api_key": "key"},
                accounts=[
                    {"id": "ACC1", "name": "Account 1", "account_type": "practice"},
                    {"id": "ACC1", "name": "Account 2", "account_type": "live"}  # Duplicate!
                ]
            )


# ==============================================================================
# API CONFIGURATION TESTS
# ==============================================================================


class TestProjectXConfig:
    """Test ProjectXConfig model and URL validators."""

    def test_valid_config(self):
        """Test valid ProjectX config."""
        config = ProjectXConfig(
            username="testuser",
            api_key="testkey123"
        )

        assert config.username == "testuser"
        assert config.api_key == "testkey123"

    def test_invalid_http_url_raises_error(self):
        """Test HTTP URL raises error."""
        with pytest.raises(ValidationError, match="Invalid URL"):
            ProjectXConfig(
                username="testuser",
                api_key="testkey123",
                api_url="http://insecure.com"
            )

    def test_invalid_url_no_protocol_raises_error(self):
        """Test URL without protocol raises error."""
        with pytest.raises(ValidationError, match="Invalid URL"):
            ProjectXConfig(
                username="testuser",
                api_key="testkey123",
                api_url="api.example.com"
            )


class TestReconnectConfig:
    """Test ReconnectConfig model and validators."""

    def test_valid_config(self):
        """Test valid reconnect config."""
        config = ReconnectConfig(
            initial_delay=1,
            max_delay=300
        )

        assert config.initial_delay == 1
        assert config.max_delay == 300

    def test_initial_delay_greater_than_max_delay_raises_error(self):
        """Test initial_delay > max_delay raises error."""
        with pytest.raises(ValidationError, match="initial_delay must be <= max_delay"):
            ReconnectConfig(
                initial_delay=500,
                max_delay=300
            )

    def test_initial_delay_equals_max_delay_valid(self):
        """Test initial_delay == max_delay is valid."""
        config = ReconnectConfig(
            initial_delay=300,
            max_delay=300
        )

        assert config.initial_delay == config.max_delay


class TestRetryConfig:
    """Test RetryConfig model and validators."""

    def test_valid_config(self):
        """Test valid retry config."""
        config = RetryConfig(
            max_attempts=5,
            backoff_multiplier=2.0
        )

        assert config.max_attempts == 5
        assert config.backoff_multiplier == 2.0

    def test_max_attempts_must_be_positive(self):
        """Test max_attempts must be >= 1."""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            RetryConfig(
                max_attempts=0
            )

    def test_backoff_multiplier_must_be_positive(self):
        """Test backoff_multiplier must be >= 1.0."""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            RetryConfig(
                backoff_multiplier=0.5
            )


class TestGeneralConfig:
    """Test GeneralConfig model and validators."""

    def test_valid_config(self):
        """Test valid general config."""
        config = GeneralConfig(
            instruments=["MNQ", "ES"],
            timezone="America/Chicago"
        )

        assert config.instruments == ["MNQ", "ES"]
        assert config.timezone == "America/Chicago"

    def test_instruments_must_not_be_empty(self):
        """Test instruments list must have at least 1 item."""
        with pytest.raises(ValidationError, match="at least 1"):
            GeneralConfig(
                instruments=[],
                timezone="America/Chicago"
            )

    def test_invalid_timezone_raises_error(self):
        """Test invalid timezone raises error."""
        with pytest.raises(ValidationError, match="Invalid timezone"):
            GeneralConfig(
                instruments=["MNQ"],
                timezone="InvalidZone"
            )


# ==============================================================================
# NESTED MODEL AND DEFAULT VALUE TESTS
# ==============================================================================


class TestNestedModels:
    """Test nested model validation."""

    def test_timers_config_nested_validation(self):
        """Test TimersConfig validates all nested models."""
        config = TimersConfig(
            daily_reset={
                "time": "17:00",
                "timezone": "America/Chicago"
            },
            lockout_durations={
                "hard_lockout": {
                    "auth_loss_guard": "permanent"
                }
            },
            session_hours={
                "start": "08:30",
                "end": "15:00",
                "timezone": "America/Chicago"
            }
        )

        assert config.daily_reset.time == "17:00"
        assert config.lockout_durations.hard_lockout.auth_loss_guard == "permanent"
        assert config.session_hours.start == "08:30"

    def test_risk_config_nested_validation(self):
        """Test RiskConfig validates all nested models."""
        config = RiskConfig(
            general={
                "instruments": ["MNQ"],
                "timezone": "America/Chicago"
            },
            rules={
                "max_contracts": {"limit": 5},
                "max_contracts_per_instrument": {"default_limit": 2},
                "daily_unrealized_loss": {"limit": -200.0},
                "max_unrealized_profit": {"target": 500.0},
                "no_stop_loss_grace": {"require_within_seconds": 60, "grace_period_seconds": 90},
                "trade_frequency_limit": {"limits": {"per_minute": 5, "per_hour": 50, "per_session": 200}},
                "cooldown_after_loss": {"loss_threshold": -50.0},
                "daily_realized_loss": {"limit": -500.0},
                "daily_realized_profit": {"target": 1000.0},
                "session_block_outside": {},
                "auth_loss_guard": {},
                "trade_management": {
                    "enabled": False,
                    "auto_breakeven": {"profit_threshold_ticks": 10},
                    "trailing_stop": {"trail_ticks": 5, "activation_profit_ticks": 15}
                }
            }
        )

        assert config.general.instruments == ["MNQ"]
        assert config.rules.max_contracts.limit == 5

    def test_api_config_nested_validation(self):
        """Test ApiConfig validates all nested models."""
        config = ApiConfig(
            projectx={
                "username": "testuser",
                "api_key": "testkey"
            }
        )

        assert config.projectx.username == "testuser"
        assert config.connection.connect_timeout == 30  # Default
        assert config.rate_limit.requests.per_second == 10  # Default


class TestDefaultValues:
    """Test default values populate correctly."""

    def test_daily_reset_config_defaults(self):
        """Test DailyResetConfig default values."""
        config = DailyResetConfig(
            time="17:00",
            timezone="America/Chicago"
        )

        assert config.enabled is True
        assert config.reset_actions.clear_daily_pnl is True

    def test_lockout_durations_defaults(self):
        """Test LockoutDurationsConfig default values."""
        config = LockoutDurationsConfig()

        assert config.hard_lockout.daily_realized_loss == "until_reset"
        assert config.hard_lockout.auth_loss_guard == "permanent"
        assert config.timer_cooldown.cooldown_after_loss == "15m"

    def test_session_hours_defaults(self):
        """Test SessionHoursConfig default values."""
        config = SessionHoursConfig(
            start="08:30",
            end="15:00",
            timezone="America/Chicago"
        )

        assert config.enabled is True
        assert config.allowed_days == [0, 1, 2, 3, 4]
        assert config.pre_market.enabled is False
        assert config.after_hours.enabled is False

    def test_max_contracts_defaults(self):
        """Test MaxContractsConfig default values."""
        config = MaxContractsConfig(
            limit=5
        )

        assert config.enabled is True
        assert config.close_all is False
        assert config.close_position is True
        assert config.reduce_to_limit is False
        assert config.count_type == "net"


# ==============================================================================
# EDGE CASES AND ERROR HANDLING
# ==============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_time_boundary_00_00(self):
        """Test time at 00:00 (midnight) is valid."""
        config = DailyResetConfig(
            time="00:00",
            timezone="America/Chicago"
        )
        assert config.time == "00:00"

    def test_time_boundary_23_59(self):
        """Test time at 23:59 is valid."""
        config = DailyResetConfig(
            time="23:59",
            timezone="America/Chicago"
        )
        assert config.time == "23:59"

    def test_limit_exactly_at_boundary(self):
        """Test limit exactly at boundary value."""
        config = MaxContractsConfig(limit=1)
        assert config.limit == 1

    def test_frequency_limits_equal_values(self):
        """Test frequency limits with all equal values."""
        config = FrequencyLimitsConfig(
            per_minute=10,
            per_hour=10,
            per_session=10
        )

        assert config.per_minute == config.per_hour == config.per_session

    def test_duration_at_max_seconds(self):
        """Test duration at maximum seconds (86400 = 24 hours)."""
        config = LockoutDurationsConfig(
            timer_cooldown={"cooldown_after_loss": "86400s"}
        )
        assert config.timer_cooldown.cooldown_after_loss == "86400s"

    def test_duration_at_max_minutes(self):
        """Test duration at maximum minutes (1440 = 24 hours)."""
        config = LockoutDurationsConfig(
            timer_cooldown={"cooldown_after_loss": "1440m"}
        )
        assert config.timer_cooldown.cooldown_after_loss == "1440m"

    def test_duration_at_max_hours(self):
        """Test duration at maximum hours (24)."""
        config = LockoutDurationsConfig(
            timer_cooldown={"cooldown_after_loss": "24h"}
        )
        assert config.timer_cooldown.cooldown_after_loss == "24h"

    def test_year_boundary_2000(self):
        """Test year at minimum boundary (2000)."""
        config = HolidaysConfig(
            dates={2000: ["2000-01-01"]}
        )
        assert 2000 in config.dates

    def test_year_boundary_2100(self):
        """Test year at maximum boundary (2100)."""
        config = HolidaysConfig(
            dates={2100: ["2100-12-31"]}
        )
        assert 2100 in config.dates

    def test_leap_year_date_valid(self):
        """Test leap year date (Feb 29) is valid."""
        config = EarlyCloseConfig(
            date="2024-02-29",  # 2024 is a leap year
            close_time="13:00"
        )
        assert config.date == "2024-02-29"

    def test_optional_fields_none(self):
        """Test optional fields can be None."""
        config = AccountConfig(
            id="ACC123",
            name="Test",
            account_type="practice",
            description=None,
            risk_config_file=None,
            config_overrides=None
        )

        assert config.description is None
        assert config.risk_config_file is None
        assert config.config_overrides is None
