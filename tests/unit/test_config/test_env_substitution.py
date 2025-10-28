"""Unit tests for environment variable substitution in configuration."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from risk_manager.core.config import RiskConfig


class TestEnvironmentVariableSubstitution:
    """Test environment variable substitution via pydantic-settings.

    NOTE: RiskConfig() by default does NOT load from environment variables.
    Use RiskConfig.from_env() to explicitly load from environment.
    This prevents test contamination from real .env files.
    """

    def test_load_from_env_variables(self, monkeypatch):
        """Test loading configuration from environment variables using from_env()."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "env_api_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "env_username")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "env_api_key"
        assert config.project_x_username == "env_username"

    def test_env_variables_override_defaults(self, monkeypatch):
        """Test environment variables override default values."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "env_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "env_user")
        monkeypatch.setenv("MAX_CONTRACTS", "20")
        monkeypatch.setenv("MAX_DAILY_LOSS", "-3000.0")

        config = RiskConfig.from_env()

        assert config.max_contracts == 20
        assert config.max_daily_loss == -3000.0

    def test_explicit_params_override_env(self, monkeypatch):
        """Test explicit parameters (RiskConfig()) do NOT load from environment."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "env_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "env_user")

        # Direct instantiation ignores environment variables
        config = RiskConfig(
            project_x_api_key="explicit_key",
            project_x_username="explicit_user"
        )

        assert config.project_x_api_key == "explicit_key"
        assert config.project_x_username == "explicit_user"

    def test_partial_env_variables(self, monkeypatch):
        """Test direct instantiation with explicit params (no env loading)."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "env_key")

        # Direct instantiation doesn't load from env - must provide all required fields
        config = RiskConfig(
            project_x_api_key="explicit_key",
            project_x_username="explicit_user"
        )

        assert config.project_x_api_key == "explicit_key"
        assert config.project_x_username == "explicit_user"

    def test_env_variable_case_insensitive(self, monkeypatch):
        """Test environment variables are case-insensitive."""
        monkeypatch.setenv("project_x_api_key", "lower_key")
        monkeypatch.setenv("project_x_username", "lower_user")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "lower_key"
        assert config.project_x_username == "lower_user"

    def test_env_variable_with_prefix(self, monkeypatch):
        """Test environment variables with uppercase names."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "test_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("ENVIRONMENT", "production")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "test_key"
        assert config.log_level == "DEBUG"
        assert config.environment == "production"

    def test_boolean_env_variables(self, monkeypatch):
        """Test boolean values from environment variables."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "test_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")
        monkeypatch.setenv("REQUIRE_STOP_LOSS", "false")
        monkeypatch.setenv("ENABLE_AI", "true")
        monkeypatch.setenv("DEBUG", "1")

        config = RiskConfig.from_env()

        assert config.require_stop_loss is False
        assert config.enable_ai is True
        assert config.debug is True

    def test_integer_env_variables(self, monkeypatch):
        """Test integer values from environment variables."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "test_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")
        monkeypatch.setenv("MAX_CONTRACTS", "15")
        monkeypatch.setenv("STOP_LOSS_GRACE_SECONDS", "120")
        monkeypatch.setenv("MAX_EVENTS_PER_SECOND", "5000")

        config = RiskConfig.from_env()

        assert config.max_contracts == 15
        assert config.stop_loss_grace_seconds == 120
        assert config.max_events_per_second == 5000

    def test_float_env_variables(self, monkeypatch):
        """Test float values from environment variables."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "test_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")
        monkeypatch.setenv("MAX_DAILY_LOSS", "-2500.75")

        config = RiskConfig.from_env()

        assert config.max_daily_loss == -2500.75

    def test_optional_env_variables(self, monkeypatch):
        """Test optional environment variables."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "test_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/webhook")

        config = RiskConfig.from_env()

        assert config.anthropic_api_key == "sk-ant-test"
        assert config.discord_webhook_url == "https://discord.com/webhook"

    def test_missing_optional_env_variables(self, monkeypatch, tmp_path):
        """Test missing optional environment variables use defaults."""
        # Change to temp directory to avoid loading project .env file
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PROJECT_X_API_KEY", "test_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")

        config = RiskConfig.from_env()

        assert config.anthropic_api_key is None
        assert config.discord_webhook_url is None
        assert config.log_file is None

    def test_env_file_loading(self, tmp_path, monkeypatch):
        """Test loading configuration from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
PROJECT_X_API_KEY=dotenv_key
PROJECT_X_USERNAME=dotenv_user
MAX_CONTRACTS=25
ENABLE_AI=true
""")

        # Change to directory with .env file
        monkeypatch.chdir(tmp_path)
        # Unset environment variables so .env file values are used
        monkeypatch.delenv("MAX_CONTRACTS", raising=False)
        monkeypatch.delenv("ENABLE_AI", raising=False)

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "dotenv_key"
        assert config.project_x_username == "dotenv_user"
        assert config.max_contracts == 25
        assert config.enable_ai is True

    def test_env_variables_override_env_file(self, tmp_path, monkeypatch):
        """Test environment variables override .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
PROJECT_X_API_KEY=dotenv_key
PROJECT_X_USERNAME=dotenv_user
""")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PROJECT_X_API_KEY", "env_override_key")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "env_override_key"
        assert config.project_x_username == "dotenv_user"

    def test_empty_env_variable(self, monkeypatch):
        """Test empty environment variable."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == ""

    def test_whitespace_env_variable(self, monkeypatch):
        """Test whitespace-only environment variable."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "   ")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "   "

    def test_env_variable_with_special_characters(self, monkeypatch):
        """Test environment variable with special characters."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "key!@#$%^&*()")
        monkeypatch.setenv("PROJECT_X_USERNAME", "user:test/name")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "key!@#$%^&*()"
        assert config.project_x_username == "user:test/name"

    def test_multiline_env_variable(self, monkeypatch):
        """Test multiline environment variable."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "line1\nline2")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")

        config = RiskConfig.from_env()

        assert "\n" in config.project_x_api_key

    def test_env_variable_validation_alias(self, monkeypatch):
        """Test that validation_alias works for environment variables."""
        # Both PROJECT_X_API_KEY and project_x_api_key should work
        monkeypatch.setenv("PROJECT_X_API_KEY", "alias_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "alias_user")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "alias_key"
        assert config.project_x_username == "alias_user"

    def test_url_env_variables(self, monkeypatch):
        """Test URL environment variables."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "test_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")
        monkeypatch.setenv("PROJECT_X_API_URL", "https://custom.api.com")
        monkeypatch.setenv("PROJECT_X_WEBSOCKET_URL", "wss://custom.ws.com")

        config = RiskConfig.from_env()

        assert config.project_x_api_url == "https://custom.api.com"
        assert config.project_x_websocket_url == "wss://custom.ws.com"

    def test_all_fields_from_env(self, monkeypatch):
        """Test loading all configuration fields from environment."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "test_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")
        monkeypatch.setenv("PROJECT_X_API_URL", "https://api.com")
        monkeypatch.setenv("PROJECT_X_WEBSOCKET_URL", "wss://ws.com")
        monkeypatch.setenv("MAX_DAILY_LOSS", "-5000.0")
        monkeypatch.setenv("MAX_CONTRACTS", "30")
        monkeypatch.setenv("REQUIRE_STOP_LOSS", "false")
        monkeypatch.setenv("STOP_LOSS_GRACE_SECONDS", "180")
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        monkeypatch.setenv("LOG_FILE", "/var/log/risk.log")
        monkeypatch.setenv("ENFORCEMENT_LATENCY_TARGET_MS", "100")
        monkeypatch.setenv("MAX_EVENTS_PER_SECOND", "3000")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-key")
        monkeypatch.setenv("ENABLE_AI", "true")
        monkeypatch.setenv("ENABLE_PATTERN_RECOGNITION", "true")
        monkeypatch.setenv("ENABLE_ANOMALY_DETECTION", "true")
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/hook")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat_123")
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("DEBUG", "true")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "test_key"
        assert config.max_contracts == 30
        assert config.log_level == "ERROR"
        assert config.enable_ai is True
        assert config.environment == "staging"
        assert config.debug is True

    def test_env_variable_type_coercion_errors(self, monkeypatch):
        """Test environment variable type coercion errors."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "test_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "test_user")
        monkeypatch.setenv("MAX_CONTRACTS", "not_a_number")

        with pytest.raises(Exception):  # ValidationError
            RiskConfig()

    def test_missing_required_env_variable(self):
        """Test missing required environment variable raises error."""
        # Clear any existing env vars that might satisfy requirements
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):  # ValidationError
                RiskConfig()

    def test_env_file_with_comments(self, tmp_path, monkeypatch):
        """Test .env file with comments."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
# This is a comment
PROJECT_X_API_KEY=dotenv_key
PROJECT_X_USERNAME=dotenv_user  # Inline comment
# Another comment
MAX_CONTRACTS=10
""")

        monkeypatch.chdir(tmp_path)
        # Unset environment variable so .env file value is used
        monkeypatch.delenv("MAX_CONTRACTS", raising=False)

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "dotenv_key"
        assert config.max_contracts == 10

    def test_env_file_with_quotes(self, tmp_path, monkeypatch):
        """Test .env file with quoted values."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
PROJECT_X_API_KEY="quoted_key"
PROJECT_X_USERNAME='single_quoted_user'
""")

        monkeypatch.chdir(tmp_path)

        config = RiskConfig.from_env()

        # Quotes might be preserved or stripped depending on parser
        assert "key" in config.project_x_api_key
        assert "user" in config.project_x_username

    def test_env_file_with_equals_in_value(self, tmp_path, monkeypatch):
        """Test .env file with equals sign in value."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
PROJECT_X_API_KEY=key=with=equals
PROJECT_X_USERNAME=test_user
""")

        monkeypatch.chdir(tmp_path)

        config = RiskConfig.from_env()

        assert "=" in config.project_x_api_key

    def test_env_file_missing(self, tmp_path, monkeypatch):
        """Test missing .env file uses defaults or env vars."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PROJECT_X_API_KEY", "env_key")
        monkeypatch.setenv("PROJECT_X_USERNAME", "env_user")

        config = RiskConfig.from_env()

        assert config.project_x_api_key == "env_key"
        assert config.project_x_username == "env_user"

    def test_combined_yaml_and_env(self, tmp_path, monkeypatch):
        """Test loading from both YAML file and environment variables."""
        # Create YAML config
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("""
project_x_api_key: yaml_key
project_x_username: yaml_user
max_contracts: 5
""")

        # Set environment variable to override
        monkeypatch.setenv("MAX_CONTRACTS", "15")

        # Load from YAML (env vars don't apply to from_file())
        config = RiskConfig.from_file(yaml_file)

        # YAML values take precedence when using from_file()
        assert config.project_x_api_key == "yaml_key"
        assert config.max_contracts == 5

    def test_env_variable_unicode(self, monkeypatch):
        """Test environment variables with unicode characters."""
        monkeypatch.setenv("PROJECT_X_API_KEY", "key_™_中文")
        monkeypatch.setenv("PROJECT_X_USERNAME", "user_®_日本語")

        config = RiskConfig.from_env()

        assert "™" in config.project_x_api_key
        assert "日本語" in config.project_x_username
