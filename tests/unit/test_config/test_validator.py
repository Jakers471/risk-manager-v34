"""Unit tests for configuration validators."""

import pytest
from pydantic import ValidationError, field_validator, model_validator
from typing_extensions import Self

from risk_manager.core.config import RiskConfig


class TestFieldValidation:
    """Test field-level validation."""

    def test_positive_max_contracts_valid(self):
        """Test positive max_contracts is valid."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=10
        )
        assert config.max_contracts == 10

    def test_zero_max_contracts_valid(self):
        """Test zero max_contracts is valid (edge case)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=0
        )
        assert config.max_contracts == 0

    def test_negative_max_contracts_allowed(self):
        """Test negative max_contracts is allowed (no validator)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=-5
        )
        assert config.max_contracts == -5

    def test_negative_max_daily_loss_valid(self):
        """Test negative max_daily_loss is valid (typical case)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss=-1000.0
        )
        assert config.max_daily_loss == -1000.0

    def test_positive_max_daily_loss_allowed(self):
        """Test positive max_daily_loss is allowed (unusual but valid)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss=1000.0
        )
        assert config.max_daily_loss == 1000.0

    def test_zero_max_daily_loss_valid(self):
        """Test zero max_daily_loss is valid."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss=0.0
        )
        assert config.max_daily_loss == 0.0

    def test_positive_grace_seconds_valid(self):
        """Test positive grace seconds is valid."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            stop_loss_grace_seconds=120
        )
        assert config.stop_loss_grace_seconds == 120

    def test_zero_grace_seconds_valid(self):
        """Test zero grace seconds is valid."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            stop_loss_grace_seconds=0
        )
        assert config.stop_loss_grace_seconds == 0

    def test_negative_grace_seconds_allowed(self):
        """Test negative grace seconds is allowed (no validator)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            stop_loss_grace_seconds=-60
        )
        assert config.stop_loss_grace_seconds == -60

    def test_positive_latency_target_valid(self):
        """Test positive latency target is valid."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            enforcement_latency_target_ms=500
        )
        assert config.enforcement_latency_target_ms == 500

    def test_positive_max_events_valid(self):
        """Test positive max events per second is valid."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_events_per_second=2000
        )
        assert config.max_events_per_second == 2000

    def test_empty_string_api_key_valid(self):
        """Test empty string API key is valid (no validator)."""
        config = RiskConfig(
            project_x_api_key="",
            project_x_username="test_user"
        )
        assert config.project_x_api_key == ""

    def test_empty_string_username_valid(self):
        """Test empty string username is valid (no validator)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username=""
        )
        assert config.project_x_username == ""

    def test_whitespace_string_api_key_valid(self):
        """Test whitespace string API key is valid."""
        config = RiskConfig(
            project_x_api_key="   ",
            project_x_username="test_user"
        )
        assert config.project_x_api_key == "   "

    def test_valid_log_levels(self):
        """Test various valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                log_level=level
            )
            assert config.log_level == level

    def test_lowercase_log_level_valid(self):
        """Test lowercase log level is valid."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            log_level="debug"
        )
        assert config.log_level == "debug"

    def test_invalid_log_level_allowed(self):
        """Test invalid log level is allowed (no validator)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            log_level="INVALID_LEVEL"
        )
        assert config.log_level == "INVALID_LEVEL"

    def test_valid_environment_values(self):
        """Test various valid environment values."""
        for env in ["development", "staging", "production", "test"]:
            config = RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                environment=env
            )
            assert config.environment == env

    def test_invalid_environment_allowed(self):
        """Test invalid environment is allowed (no validator)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            environment="invalid_env"
        )
        assert config.environment == "invalid_env"

    def test_valid_url_formats(self):
        """Test various valid URL formats."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            project_x_api_url="https://api.example.com",
            project_x_websocket_url="wss://ws.example.com",
            discord_webhook_url="https://discord.com/webhooks/123"
        )
        assert "https://" in config.project_x_api_url
        assert "wss://" in config.project_x_websocket_url

    def test_invalid_url_format_allowed(self):
        """Test invalid URL format is allowed (no validator)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            project_x_api_url="not_a_url",
            discord_webhook_url="invalid://url"
        )
        assert config.project_x_api_url == "not_a_url"


class TestModelValidation:
    """Test model-level validation (cross-field)."""

    def test_all_required_fields_present(self):
        """Test model validates when all required fields present."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user"
        )
        assert config.project_x_api_key == "test_key"
        assert config.project_x_username == "test_user"

    def test_conflicting_ai_settings_allowed(self):
        """Test conflicting AI settings are allowed (no validator)."""
        # Enable AI features without API key
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            enable_ai=True,
            anthropic_api_key=None
        )
        assert config.enable_ai is True
        assert config.anthropic_api_key is None

    def test_ai_features_without_enable_ai_allowed(self):
        """Test enabling AI features without enable_ai flag is allowed."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            enable_ai=False,
            enable_pattern_recognition=True,
            enable_anomaly_detection=True
        )
        assert config.enable_ai is False
        assert config.enable_pattern_recognition is True

    def test_notifications_without_credentials_allowed(self):
        """Test notification settings without credentials are allowed."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            discord_webhook_url=None,
            telegram_bot_token=None
        )
        assert config.discord_webhook_url is None

    def test_debug_in_production_allowed(self):
        """Test debug mode in production is allowed (no validator)."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            environment="production",
            debug=True
        )
        assert config.environment == "production"
        assert config.debug is True

    def test_low_latency_with_high_events_allowed(self):
        """Test low latency target with high event rate is allowed."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            enforcement_latency_target_ms=50,
            max_events_per_second=10000
        )
        assert config.enforcement_latency_target_ms == 50
        assert config.max_events_per_second == 10000


class TestTypeValidation:
    """Test type validation and coercion."""

    def test_string_to_int_coercion(self):
        """Test string to int coercion works."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts="10"
        )
        assert config.max_contracts == 10
        assert isinstance(config.max_contracts, int)

    def test_string_to_float_coercion(self):
        """Test string to float coercion works."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss="-1000.5"
        )
        assert config.max_daily_loss == -1000.5
        assert isinstance(config.max_daily_loss, float)

    def test_string_to_bool_coercion_true(self):
        """Test string to bool coercion for true values."""
        for true_value in ["true", "True", "TRUE", "yes", "1"]:
            config = RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                require_stop_loss=true_value
            )
            assert config.require_stop_loss is True

    def test_string_to_bool_coercion_false(self):
        """Test string to bool coercion for false values."""
        for false_value in ["false", "False", "FALSE", "no", "0"]:
            config = RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                require_stop_loss=false_value
            )
            assert config.require_stop_loss is False

    def test_int_to_float_coercion(self):
        """Test int to float coercion works."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss=-1000  # Int instead of float
        )
        assert config.max_daily_loss == -1000.0
        assert isinstance(config.max_daily_loss, float)

    def test_float_to_int_coercion(self):
        """Test float to int coercion (pydantic v2 rejects floats with fractional parts)."""
        # Pydantic v2 is stricter - it rejects floats with fractional parts for int fields
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                max_contracts=10.9  # Float with fractional part
            )

        errors = exc_info.value.errors()
        assert any(e["type"] == "int_from_float" for e in errors)

        # However, whole number floats like 10.0 should work
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=10.0  # Whole number float
        )
        assert config.max_contracts == 10
        assert isinstance(config.max_contracts, int)

    def test_invalid_string_to_int_raises_error(self):
        """Test invalid string to int conversion raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                max_contracts="not_a_number"
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_contracts",) for e in errors)

    def test_invalid_string_to_float_raises_error(self):
        """Test invalid string to float conversion raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                max_daily_loss="not_a_number"
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_daily_loss",) for e in errors)

    def test_list_to_string_raises_error(self):
        """Test list to string conversion raises ValidationError."""
        with pytest.raises(ValidationError):
            RiskConfig(
                project_x_api_key=["test", "key"],
                project_x_username="test_user"
            )

    def test_dict_to_string_raises_error(self):
        """Test dict to string conversion raises ValidationError."""
        with pytest.raises(ValidationError):
            RiskConfig(
                project_x_api_key={"key": "value"},
                project_x_username="test_user"
            )

    def test_none_for_required_field_raises_error(self):
        """Test None for required field raises ValidationError."""
        with pytest.raises(ValidationError):
            RiskConfig(
                project_x_api_key=None,
                project_x_username="test_user"
            )

    def test_none_for_optional_field_valid(self):
        """Test None for optional field is valid."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            log_file=None,
            anthropic_api_key=None
        )
        assert config.log_file is None
        assert config.anthropic_api_key is None


class TestErrorMessages:
    """Test validation error messages are helpful."""

    def test_missing_required_field_error_message(self):
        """Test error message for missing required field is clear."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(project_x_username="test_user")

        error_str = str(exc_info.value)
        assert "project_x_api_key" in error_str
        assert "Field required" in error_str or "required" in error_str.lower()

    def test_invalid_type_error_message(self):
        """Test error message for invalid type is clear."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                max_contracts="invalid"
            )

        error_str = str(exc_info.value)
        assert "max_contracts" in error_str

    def test_multiple_errors_reported(self):
        """Test multiple validation errors are reported together."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(
                max_contracts="invalid",
                max_daily_loss="also_invalid"
            )

        errors = exc_info.value.errors()
        # Should have at least 3 errors (missing api_key, missing username, invalid types)
        assert len(errors) >= 3

    def test_error_includes_field_location(self):
        """Test error includes field location."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(project_x_api_key="test_key")

        errors = exc_info.value.errors()
        # Check that error includes field location
        assert all("loc" in error for error in errors)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_max_contracts(self):
        """Test very large max_contracts value."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=1000000
        )
        assert config.max_contracts == 1000000

    def test_very_large_loss_limit(self):
        """Test very large loss limit."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss=-1000000.0
        )
        assert config.max_daily_loss == -1000000.0

    def test_very_small_latency_target(self):
        """Test very small latency target."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            enforcement_latency_target_ms=1
        )
        assert config.enforcement_latency_target_ms == 1

    def test_very_high_event_rate(self):
        """Test very high event rate."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_events_per_second=1000000
        )
        assert config.max_events_per_second == 1000000

    def test_very_long_strings(self):
        """Test very long string values."""
        long_string = "x" * 10000
        config = RiskConfig(
            project_x_api_key=long_string,
            project_x_username=long_string
        )
        assert len(config.project_x_api_key) == 10000

    def test_special_characters_in_all_string_fields(self):
        """Test special characters in all string fields."""
        special = "!@#$%^&*()_+-=[]{}|;':,.<>?/~`"
        config = RiskConfig(
            project_x_api_key=special,
            project_x_username=special,
            log_level=special,
            environment=special
        )
        assert config.project_x_api_key == special
