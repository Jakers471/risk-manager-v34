"""Unit tests for configuration Pydantic models."""

import os
import pytest
from pathlib import Path
from pydantic import ValidationError

from risk_manager.core.config import RiskConfig


class TestRiskConfigModel:
    """Test RiskConfig Pydantic model."""

    def test_valid_config_minimal(self):
        """Test creating config with minimal required fields."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user"
        )

        assert config.project_x_api_key == "test_key"
        assert config.project_x_username == "test_user"
        # Check defaults
        assert config.project_x_api_url == "https://api.topstepx.com/api"
        assert config.project_x_websocket_url == "wss://api.topstepx.com"
        assert config.max_daily_loss == -1000.0
        assert config.max_contracts == 5
        assert config.require_stop_loss is True
        assert config.log_level == "INFO"

    def test_valid_config_all_fields(self):
        """Test creating config with all fields populated."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            project_x_api_url="https://custom.api.com",
            project_x_websocket_url="wss://custom.ws.com",
            max_daily_loss=-2000.0,
            max_contracts=10,
            require_stop_loss=False,
            stop_loss_grace_seconds=120,
            log_level="DEBUG",
            log_file="/path/to/log.txt",
            enforcement_latency_target_ms=250,
            max_events_per_second=2000,
            anthropic_api_key="sk-ant-test",
            enable_ai=True,
            enable_pattern_recognition=True,
            enable_anomaly_detection=True,
            discord_webhook_url="https://discord.com/webhook",
            telegram_bot_token="bot_token",
            telegram_chat_id="chat_123",
            environment="production",
            debug=True
        )

        assert config.project_x_api_key == "test_key"
        assert config.max_daily_loss == -2000.0
        assert config.max_contracts == 10
        assert config.require_stop_loss is False
        assert config.enable_ai is True
        assert config.environment == "production"

    def test_missing_required_field_api_key(self):
        """Test that missing API key raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(project_x_username="test_user")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("project_x_api_key",) for e in errors)

    def test_missing_required_field_username(self):
        """Test that missing username raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(project_x_api_key="test_key")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("project_x_username",) for e in errors)

    def test_missing_both_required_fields(self):
        """Test that missing both required fields raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig()

        errors = exc_info.value.errors()
        assert len(errors) >= 2
        field_names = {e["loc"][0] for e in errors}
        assert "project_x_api_key" in field_names
        assert "project_x_username" in field_names

    def test_invalid_max_contracts_negative(self):
        """Test that negative max_contracts is allowed (edge case)."""
        # Pydantic doesn't validate this by default, just tests the model accepts it
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=-5
        )
        assert config.max_contracts == -5

    def test_invalid_max_contracts_zero(self):
        """Test that zero max_contracts is allowed."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=0
        )
        assert config.max_contracts == 0

    def test_max_daily_loss_positive(self):
        """Test positive max_daily_loss (should be negative for loss limit)."""
        # Model doesn't validate sign, just accepts value
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss=1000.0  # Positive (unusual but accepted)
        )
        assert config.max_daily_loss == 1000.0

    def test_max_daily_loss_zero(self):
        """Test zero max_daily_loss."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss=0.0
        )
        assert config.max_daily_loss == 0.0

    def test_optional_fields_none(self):
        """Test that optional fields can be None."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            log_file=None,
            anthropic_api_key=None,
            discord_webhook_url=None,
            telegram_bot_token=None,
            telegram_chat_id=None
        )

        assert config.log_file is None
        assert config.anthropic_api_key is None
        assert config.discord_webhook_url is None

    def test_log_level_valid_values(self):
        """Test valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                log_level=level
            )
            assert config.log_level == level

    def test_log_level_case_insensitive(self):
        """Test log level is case-insensitive due to BaseSettings."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            log_level="debug"
        )
        assert config.log_level == "debug"

    def test_boolean_fields_true(self):
        """Test boolean fields set to True."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            require_stop_loss=True,
            enable_ai=True,
            enable_pattern_recognition=True,
            enable_anomaly_detection=True,
            debug=True
        )

        assert config.require_stop_loss is True
        assert config.enable_ai is True
        assert config.debug is True

    def test_boolean_fields_false(self):
        """Test boolean fields set to False."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            require_stop_loss=False,
            enable_ai=False,
            enable_pattern_recognition=False,
            enable_anomaly_detection=False,
            debug=False
        )

        assert config.require_stop_loss is False
        assert config.enable_ai is False
        assert config.debug is False

    def test_integer_fields_valid(self):
        """Test integer fields with valid values."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            stop_loss_grace_seconds=300,
            enforcement_latency_target_ms=100,
            max_events_per_second=5000
        )

        assert config.stop_loss_grace_seconds == 300
        assert config.enforcement_latency_target_ms == 100
        assert config.max_events_per_second == 5000

    def test_float_fields_valid(self):
        """Test float fields with valid values."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss=-1500.50
        )

        assert config.max_daily_loss == -1500.50

    def test_string_fields_empty(self):
        """Test string fields with empty strings."""
        config = RiskConfig(
            project_x_api_key="",
            project_x_username="",
            environment=""
        )

        assert config.project_x_api_key == ""
        assert config.project_x_username == ""
        assert config.environment == ""

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored (extra='ignore')."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            unknown_field="value",
            another_unknown=123
        )

        assert not hasattr(config, "unknown_field")
        assert not hasattr(config, "another_unknown")

    def test_to_dict_method(self):
        """Test to_dict() method converts config to dictionary."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=3
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["project_x_api_key"] == "test_key"
        assert config_dict["project_x_username"] == "test_user"
        assert config_dict["max_contracts"] == 3
        assert "max_daily_loss" in config_dict

    def test_model_dump_includes_all_fields(self):
        """Test that model_dump includes all fields."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user"
        )

        dump = config.model_dump()

        # Check required fields
        assert "project_x_api_key" in dump
        assert "project_x_username" in dump
        # Check some default fields
        assert "max_daily_loss" in dump
        assert "max_contracts" in dump
        assert "log_level" in dump

    def test_environment_field_values(self):
        """Test environment field with different values."""
        for env in ["development", "staging", "production", "test"]:
            config = RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                environment=env
            )
            assert config.environment == env

    def test_url_fields_format(self):
        """Test URL fields accept various formats."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            project_x_api_url="https://custom.com/api",
            project_x_websocket_url="wss://custom.com",
            discord_webhook_url="https://discord.com/api/webhooks/123/abc"
        )

        assert config.project_x_api_url == "https://custom.com/api"
        assert config.project_x_websocket_url == "wss://custom.com"
        assert config.discord_webhook_url == "https://discord.com/api/webhooks/123/abc"

    def test_type_coercion_string_to_int(self):
        """Test that Pydantic coerces string to int."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts="10"  # String should be coerced to int
        )

        assert config.max_contracts == 10
        assert isinstance(config.max_contracts, int)

    def test_type_coercion_string_to_float(self):
        """Test that Pydantic coerces string to float."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_daily_loss="-1000.0"  # String should be coerced to float
        )

        assert config.max_daily_loss == -1000.0
        assert isinstance(config.max_daily_loss, float)

    def test_type_coercion_string_to_bool(self):
        """Test that Pydantic coerces string to bool."""
        # Pydantic accepts various string representations of bool
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            require_stop_loss="true"
        )

        assert config.require_stop_loss is True
        assert isinstance(config.require_stop_loss, bool)

    def test_invalid_type_for_int_field(self):
        """Test that invalid type for int field raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                max_contracts="not_a_number"
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_contracts",) for e in errors)

    def test_invalid_type_for_float_field(self):
        """Test that invalid type for float field raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(
                project_x_api_key="test_key",
                project_x_username="test_user",
                max_daily_loss="not_a_number"
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_daily_loss",) for e in errors)

    def test_config_equality(self):
        """Test that two configs with same values are equal."""
        config1 = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=5
        )

        config2 = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=5
        )

        assert config1.model_dump() == config2.model_dump()

    def test_config_immutability_after_creation(self):
        """Test that config fields can be modified after creation."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user"
        )

        # Pydantic models are mutable by default
        config.max_contracts = 10
        assert config.max_contracts == 10
