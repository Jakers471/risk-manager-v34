"""Unit tests for configuration YAML loader."""

import os
import pytest
import tempfile
from pathlib import Path
from pydantic import ValidationError

from risk_manager.core.config import RiskConfig


class TestConfigLoader:
    """Test configuration loading from YAML files."""

    def test_load_valid_yaml_file(self, tmp_path):
        """Test loading valid YAML configuration file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key_123
project_x_username: test_user_456
max_daily_loss: -2000.0
max_contracts: 10
""")

        config = RiskConfig.from_file(config_file)

        assert config.project_x_api_key == "test_key_123"
        assert config.project_x_username == "test_user_456"
        assert config.max_daily_loss == -2000.0
        assert config.max_contracts == 10

    def test_load_yaml_with_all_fields(self, tmp_path):
        """Test loading YAML with all fields populated."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
project_x_api_url: https://custom.api.com
project_x_websocket_url: wss://custom.ws.com
max_daily_loss: -3000.0
max_contracts: 15
require_stop_loss: false
stop_loss_grace_seconds: 120
log_level: DEBUG
log_file: /var/log/risk.log
enforcement_latency_target_ms: 250
max_events_per_second: 2000
anthropic_api_key: sk-ant-test
enable_ai: true
enable_pattern_recognition: true
enable_anomaly_detection: true
discord_webhook_url: https://discord.com/webhook
telegram_bot_token: bot_token
telegram_chat_id: chat_123
environment: production
debug: true
""")

        config = RiskConfig.from_file(config_file)

        assert config.project_x_api_key == "test_key"
        assert config.project_x_api_url == "https://custom.api.com"
        assert config.max_contracts == 15
        assert config.require_stop_loss is False
        assert config.enable_ai is True
        assert config.environment == "production"

    def test_load_yaml_minimal_required_only(self, tmp_path):
        """Test loading YAML with only required fields."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: minimal_key
project_x_username: minimal_user
""")

        config = RiskConfig.from_file(config_file)

        assert config.project_x_api_key == "minimal_key"
        assert config.project_x_username == "minimal_user"
        # Check defaults are applied
        assert config.max_daily_loss == -1000.0
        assert config.max_contracts == 5

    def test_load_yaml_missing_required_field(self, tmp_path):
        """Test loading YAML missing required field raises error."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
# Missing username
max_contracts: 5
""")

        with pytest.raises(ValidationError) as exc_info:
            RiskConfig.from_file(config_file)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("project_x_username",) for e in errors)

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            RiskConfig.from_file("/nonexistent/path/config.yaml")

        assert "Config file not found" in str(exc_info.value)

    def test_load_empty_yaml_file(self, tmp_path):
        """Test loading empty YAML file raises ValidationError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        with pytest.raises(ValidationError):
            RiskConfig.from_file(config_file)

    def test_load_yaml_with_null_values(self, tmp_path):
        """Test loading YAML with null values for optional fields."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
log_file: null
anthropic_api_key: null
discord_webhook_url: null
""")

        config = RiskConfig.from_file(config_file)

        assert config.log_file is None
        assert config.anthropic_api_key is None
        assert config.discord_webhook_url is None

    def test_load_yaml_with_comments(self, tmp_path):
        """Test loading YAML with comments."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
# This is a comment
project_x_api_key: test_key  # Inline comment
project_x_username: test_user
# Another comment
max_contracts: 10
""")

        config = RiskConfig.from_file(config_file)

        assert config.project_x_api_key == "test_key"
        assert config.max_contracts == 10

    def test_load_yaml_with_extra_fields(self, tmp_path):
        """Test loading YAML with extra fields (should be ignored)."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
unknown_field: value
another_unknown: 123
""")

        config = RiskConfig.from_file(config_file)

        assert config.project_x_api_key == "test_key"
        assert not hasattr(config, "unknown_field")

    def test_load_yaml_with_nested_structure(self, tmp_path):
        """Test loading YAML with nested structure (should fail or flatten)."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
nested:
  field1: value1
  field2: value2
""")

        # Should load, but nested fields ignored
        config = RiskConfig.from_file(config_file)
        assert config.project_x_api_key == "test_key"

    def test_load_yaml_with_boolean_strings(self, tmp_path):
        """Test loading YAML with boolean values as strings."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
require_stop_loss: "true"
enable_ai: "false"
debug: "yes"
""")

        config = RiskConfig.from_file(config_file)

        assert config.require_stop_loss is True
        assert config.enable_ai is False
        # "yes" should be coerced to True
        assert config.debug is True

    def test_load_yaml_with_numeric_strings(self, tmp_path):
        """Test loading YAML with numeric values as strings."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
max_contracts: "15"
max_daily_loss: "-2000.5"
stop_loss_grace_seconds: "120"
""")

        config = RiskConfig.from_file(config_file)

        assert config.max_contracts == 15
        assert isinstance(config.max_contracts, int)
        assert config.max_daily_loss == -2000.5
        assert isinstance(config.max_daily_loss, float)

    def test_load_yaml_with_invalid_yaml_syntax(self, tmp_path):
        """Test loading YAML with invalid syntax raises error."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
invalid yaml here: [no closing bracket
""")

        with pytest.raises(Exception):  # Should raise YAML parsing error
            RiskConfig.from_file(config_file)

    def test_load_yaml_with_duplicate_keys(self, tmp_path):
        """Test loading YAML with duplicate keys (last one wins)."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
max_contracts: 5
max_contracts: 10
""")

        config = RiskConfig.from_file(config_file)

        # YAML parser should use last value
        assert config.max_contracts == 10

    def test_load_from_string_path(self, tmp_path):
        """Test loading from string path (not Path object)."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
""")

        # Pass as string instead of Path
        config = RiskConfig.from_file(str(config_file))

        assert config.project_x_api_key == "test_key"

    def test_load_from_pathlib_path(self, tmp_path):
        """Test loading from pathlib Path object."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
""")

        # Pass as Path object
        config = RiskConfig.from_file(config_file)

        assert config.project_x_api_key == "test_key"

    def test_load_yaml_with_list_values(self, tmp_path):
        """Test loading YAML with list values (should be ignored or fail)."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
list_field:
  - item1
  - item2
""")

        config = RiskConfig.from_file(config_file)
        assert config.project_x_api_key == "test_key"

    def test_load_yaml_with_scientific_notation(self, tmp_path):
        """Test loading YAML with scientific notation for numbers."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
max_daily_loss: -1.5e3
max_events_per_second: 1e4
""")

        config = RiskConfig.from_file(config_file)

        assert config.max_daily_loss == -1500.0
        assert config.max_events_per_second == 10000

    def test_load_yaml_with_multiline_strings(self, tmp_path):
        """Test loading YAML with multiline strings."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: |
  test_key_multiline
  with_newlines
project_x_username: test_user
""")

        config = RiskConfig.from_file(config_file)

        # Should preserve multiline string (though unusual for API key)
        assert "test_key_multiline" in config.project_x_api_key
        assert "\n" in config.project_x_api_key

    def test_load_yaml_preserves_field_types(self, tmp_path):
        """Test that loading YAML preserves correct field types."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
max_contracts: 10
max_daily_loss: -1000.0
require_stop_loss: true
log_level: INFO
""")

        config = RiskConfig.from_file(config_file)

        assert isinstance(config.project_x_api_key, str)
        assert isinstance(config.max_contracts, int)
        assert isinstance(config.max_daily_loss, float)
        assert isinstance(config.require_stop_loss, bool)

    def test_load_yaml_with_special_characters_in_strings(self, tmp_path):
        """Test loading YAML with special characters in strings."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: "test@key#123!$%"
project_x_username: "user:name/test"
discord_webhook_url: "https://discord.com/api/webhooks/123/abc?token=xyz"
""")

        config = RiskConfig.from_file(config_file)

        assert config.project_x_api_key == "test@key#123!$%"
        assert config.project_x_username == "user:name/test"
        assert "token=xyz" in config.discord_webhook_url

    def test_load_yaml_with_unicode_characters(self, tmp_path):
        """Test loading YAML with unicode characters."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key_™
project_x_username: user_中文
""", encoding="utf-8")

        config = RiskConfig.from_file(config_file)

        assert "™" in config.project_x_api_key
        assert "中文" in config.project_x_username

    def test_load_yaml_file_permission_error(self, tmp_path):
        """Test loading YAML file with permission error."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
""")

        # Make file unreadable (Unix only)
        if os.name != 'nt':  # Skip on Windows
            config_file.chmod(0o000)

            with pytest.raises(PermissionError):
                RiskConfig.from_file(config_file)

            # Restore permissions for cleanup
            config_file.chmod(0o644)

    def test_load_yaml_relative_path(self, tmp_path, monkeypatch):
        """Test loading YAML from relative path."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        config_file = Path("config.yaml")
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
""")

        config = RiskConfig.from_file("config.yaml")

        assert config.project_x_api_key == "test_key"

    def test_load_yaml_absolute_path(self, tmp_path):
        """Test loading YAML from absolute path."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
""")

        # Use absolute path
        config = RiskConfig.from_file(config_file.absolute())

        assert config.project_x_api_key == "test_key"

    def test_to_dict_roundtrip(self, tmp_path):
        """Test that to_dict() output matches loaded values."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project_x_api_key: test_key
project_x_username: test_user
max_contracts: 7
max_daily_loss: -1500.0
""")

        config = RiskConfig.from_file(config_file)
        config_dict = config.to_dict()

        assert config_dict["project_x_api_key"] == "test_key"
        assert config_dict["project_x_username"] == "test_user"
        assert config_dict["max_contracts"] == 7
        assert config_dict["max_daily_loss"] == -1500.0
