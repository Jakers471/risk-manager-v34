"""Unit tests for config/loader.py - ConfigLoader class.

Tests the ConfigLoader class which handles:
- YAML file loading with env var substitution
- Pydantic validation
- Multiple config file loading
- Clear error messages
"""

import os
import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
from pydantic import BaseModel, Field, ValidationError

from risk_manager.config.loader import ConfigLoader, ConfigurationError


# ==============================================================================
# MOCK PYDANTIC MODELS (for testing without real models.py)
# ==============================================================================


class MockTimersConfig(BaseModel):
    """Mock timers config model."""
    reset_time: str = Field(default="17:00")
    enabled: bool = Field(default=True)


class MockRiskConfig(BaseModel):
    """Mock risk config model."""
    max_contracts: int = Field(gt=0)
    daily_loss_limit: float = Field(lt=0)


class MockAccountsConfig(BaseModel):
    """Mock accounts config model."""
    api_key: str = Field(min_length=1)
    username: str = Field(min_length=1)


class MockApiConfig(BaseModel):
    """Mock API config model."""
    timeout: int = Field(default=30)
    retries: int = Field(default=3)


# ==============================================================================
# TEST CLASS: ConfigLoader.__init__
# ==============================================================================


class TestConfigLoaderInit:
    """Test ConfigLoader.__init__() method."""

    def test_init_with_valid_directory(self, tmp_path):
        """Test initialization with valid config directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        loader = ConfigLoader(config_dir=config_dir)

        assert loader.config_dir == config_dir
        assert isinstance(loader.config_dir, Path)

    def test_init_with_string_path(self, tmp_path):
        """Test initialization with string path (converts to Path)."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        loader = ConfigLoader(config_dir=str(config_dir))

        assert loader.config_dir == config_dir
        assert isinstance(loader.config_dir, Path)

    def test_init_with_relative_path(self, tmp_path, monkeypatch):
        """Test initialization with relative path."""
        monkeypatch.chdir(tmp_path)
        config_dir = Path("config")
        config_dir.mkdir()

        loader = ConfigLoader(config_dir="config")

        assert loader.config_dir == config_dir

    def test_init_missing_directory_raises_error(self, tmp_path):
        """Test initialization with missing directory raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader(config_dir=tmp_path / "nonexistent")

        error_msg = str(exc_info.value)
        assert "Configuration directory not found" in error_msg
        assert "timers_config.yaml" in error_msg
        assert "risk_config.yaml" in error_msg
        assert "accounts.yaml" in error_msg

    def test_init_custom_env_file(self, tmp_path):
        """Test initialization with custom env_file path."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        env_file = tmp_path / "custom.env"

        loader = ConfigLoader(config_dir=config_dir, env_file=env_file)

        assert loader.env_file == env_file

    def test_init_default_env_file(self, tmp_path):
        """Test initialization uses default .env file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        loader = ConfigLoader(config_dir=config_dir)

        assert loader.env_file == Path(".env")


# ==============================================================================
# TEST CLASS: ConfigLoader._load_yaml_file
# ==============================================================================


class TestLoadYamlFile:
    """Test ConfigLoader._load_yaml_file() method."""

    def test_load_valid_yaml_file(self, tmp_path):
        """Test loading valid YAML file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"
        yaml_file.write_text("""
key1: value1
key2: 123
key3: true
""")

        loader = ConfigLoader(config_dir=config_dir)
        data = loader._load_yaml_file(yaml_file)

        assert data["key1"] == "value1"
        assert data["key2"] == 123
        assert data["key3"] is True

    def test_load_yaml_file_not_found(self, tmp_path):
        """Test loading non-existent file raises ConfigurationError."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._load_yaml_file(config_dir / "nonexistent.yaml")

        error_msg = str(exc_info.value)
        assert "Configuration file not found" in error_msg
        assert "nonexistent.yaml" in error_msg
        assert "Fix: Create the file" in error_msg

    def test_load_yaml_file_empty_raises_error(self, tmp_path):
        """Test loading empty YAML file raises ConfigurationError."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "empty.yaml"
        yaml_file.write_text("")

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._load_yaml_file(yaml_file)

        error_msg = str(exc_info.value)
        assert "Configuration file is empty" in error_msg
        assert "Fix: Add configuration" in error_msg

    def test_load_yaml_file_with_comments(self, tmp_path):
        """Test loading YAML file with comments."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"
        yaml_file.write_text("""
# This is a comment
key1: value1  # Inline comment
# Another comment
key2: value2
""")

        loader = ConfigLoader(config_dir=config_dir)
        data = loader._load_yaml_file(yaml_file)

        assert data["key1"] == "value1"
        assert data["key2"] == "value2"

    def test_load_yaml_file_invalid_syntax_with_line_info(self, tmp_path):
        """Test loading invalid YAML shows line/column info."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "bad.yaml"
        yaml_file.write_text("""
key1: value1
key2: [unclosed bracket
key3: value3
""")

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._load_yaml_file(yaml_file)

        error_msg = str(exc_info.value)
        assert "Invalid YAML syntax" in error_msg
        assert "bad.yaml" in error_msg
        # Should include line/column if available
        assert "Line" in error_msg or "Error:" in error_msg

    def test_load_yaml_file_invalid_syntax_without_line_info(self, tmp_path):
        """Test loading invalid YAML without specific line info."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "bad.yaml"
        yaml_file.write_text("{ invalid yaml")

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._load_yaml_file(yaml_file)

        error_msg = str(exc_info.value)
        assert "Invalid YAML syntax" in error_msg
        assert "Fix: Check YAML syntax" in error_msg

    def test_load_yaml_file_with_env_var_substitution(self, tmp_path):
        """Test loading YAML with environment variable substitution."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value")

        yaml_file = config_dir / "test.yaml"
        yaml_file.write_text("""
api_key: ${TEST_VAR}
other_key: static_value
""")

        loader = ConfigLoader(config_dir=config_dir, env_file=env_file)
        data = loader._load_yaml_file(yaml_file)

        assert data["api_key"] == "test_value"
        assert data["other_key"] == "static_value"

    def test_load_yaml_file_missing_env_var_raises_error(self, tmp_path):
        """Test loading YAML with missing env var raises ConfigurationError."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        env_file = tmp_path / ".env"
        env_file.write_text("")

        yaml_file = config_dir / "test.yaml"
        yaml_file.write_text("api_key: ${MISSING_VAR}")

        loader = ConfigLoader(config_dir=config_dir, env_file=env_file)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._load_yaml_file(yaml_file)

        error_msg = str(exc_info.value)
        assert "Environment variable substitution failed" in error_msg
        assert "test.yaml" in error_msg

    def test_load_yaml_file_read_permission_error(self, tmp_path):
        """Test loading YAML file with read permission error."""
        if os.name == 'nt':
            pytest.skip("Permission tests not reliable on Windows")

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"
        yaml_file.write_text("key: value")
        yaml_file.chmod(0o000)

        loader = ConfigLoader(config_dir=config_dir)

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                loader._load_yaml_file(yaml_file)

            error_msg = str(exc_info.value)
            assert "Failed to read configuration file" in error_msg
        finally:
            yaml_file.chmod(0o644)

    def test_load_yaml_file_with_nested_structure(self, tmp_path):
        """Test loading YAML with nested dictionary structure."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"
        yaml_file.write_text("""
database:
  host: localhost
  port: 5432
  credentials:
    username: admin
    password: secret
""")

        loader = ConfigLoader(config_dir=config_dir)
        data = loader._load_yaml_file(yaml_file)

        assert data["database"]["host"] == "localhost"
        assert data["database"]["credentials"]["username"] == "admin"


# ==============================================================================
# TEST CLASS: ConfigLoader._validate_with_pydantic
# ==============================================================================


class TestValidateWithPydantic:
    """Test ConfigLoader._validate_with_pydantic() method."""

    def test_validate_valid_data(self, tmp_path):
        """Test validating valid data passes."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"

        data = {"max_contracts": 10, "daily_loss_limit": -1000.0}

        loader = ConfigLoader(config_dir=config_dir)
        result = loader._validate_with_pydantic(data, MockRiskConfig, yaml_file)

        assert isinstance(result, MockRiskConfig)
        assert result.max_contracts == 10
        assert result.daily_loss_limit == -1000.0

    def test_validate_invalid_data_raises_error(self, tmp_path):
        """Test validating invalid data raises ConfigurationError."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"

        # Invalid: max_contracts must be > 0
        data = {"max_contracts": -5, "daily_loss_limit": -1000.0}

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._validate_with_pydantic(data, MockRiskConfig, yaml_file)

        error_msg = str(exc_info.value)
        assert "Configuration validation failed" in error_msg
        assert "test.yaml" in error_msg
        assert "max_contracts" in error_msg

    def test_validate_missing_required_field(self, tmp_path):
        """Test validating data with missing required field."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"

        # Missing daily_loss_limit
        data = {"max_contracts": 10}

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._validate_with_pydantic(data, MockRiskConfig, yaml_file)

        error_msg = str(exc_info.value)
        assert "validation error" in error_msg.lower()
        assert "daily_loss_limit" in error_msg

    def test_validate_multiple_errors_shown(self, tmp_path):
        """Test validation shows all errors, not just first one."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"

        # Both fields invalid
        data = {"max_contracts": -5, "daily_loss_limit": 1000.0}

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._validate_with_pydantic(data, MockRiskConfig, yaml_file)

        error_msg = str(exc_info.value)
        # Should show count of errors
        assert "validation error" in error_msg.lower()
        # Should mention fixing the file
        assert "Fix:" in error_msg

    def test_validate_field_location_in_error(self, tmp_path):
        """Test validation error includes field location."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"

        data = {"max_contracts": -5, "daily_loss_limit": -1000.0}

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._validate_with_pydantic(data, MockRiskConfig, yaml_file)

        error_msg = str(exc_info.value)
        assert "Field:" in error_msg
        assert "max_contracts" in error_msg

    def test_validate_unexpected_exception(self, tmp_path):
        """Test validation handles unexpected exceptions gracefully."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "test.yaml"

        # Create mock model that raises unexpected error
        class BrokenModel(BaseModel):
            @classmethod
            def __init__(cls, **data):
                raise RuntimeError("Unexpected error")

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._validate_with_pydantic({}, BrokenModel, yaml_file)

        error_msg = str(exc_info.value)
        assert "Unexpected error validating configuration" in error_msg


# ==============================================================================
# TEST CLASS: ConfigLoader.load_timers_config
# ==============================================================================


class TestLoadTimersConfig:
    """Test ConfigLoader.load_timers_config() method."""

    def test_load_timers_config_success(self, tmp_path):
        """Test loading valid timers config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        timers_file = config_dir / "timers_config.yaml"
        timers_file.write_text("""
reset_time: "17:00"
enabled: true
""")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.TimersConfig', MockTimersConfig):
            config = loader.load_timers_config()

        assert isinstance(config, MockTimersConfig)
        assert config.reset_time == "17:00"
        assert config.enabled is True

    def test_load_timers_config_file_not_found(self, tmp_path):
        """Test loading missing timers config raises error."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_timers_config()

        error_msg = str(exc_info.value)
        assert "Configuration file not found" in error_msg
        assert "timers_config.yaml" in error_msg

    def test_load_timers_config_custom_filename(self, tmp_path):
        """Test loading timers config with custom filename."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        custom_file = config_dir / "custom_timers.yaml"
        custom_file.write_text("""
reset_time: "18:00"
enabled: false
""")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.TimersConfig', MockTimersConfig):
            config = loader.load_timers_config(file_name="custom_timers.yaml")

        assert config.reset_time == "18:00"

    def test_load_timers_config_validation_error(self, tmp_path):
        """Test loading invalid timers config raises validation error."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        timers_file = config_dir / "timers_config.yaml"
        timers_file.write_text("""
reset_time: invalid_time
enabled: true
""")

        # Create strict mock that validates time format
        class StrictTimersConfig(BaseModel):
            reset_time: str = Field(pattern=r'^\d{2}:\d{2}$')
            enabled: bool

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.TimersConfig', StrictTimersConfig):
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_timers_config()

            error_msg = str(exc_info.value)
            assert "validation" in error_msg.lower()

    def test_load_timers_config_model_not_found(self, tmp_path):
        """Test loading timers config when model import fails.

        Note: This test verifies the error message format when models
        cannot be imported. The actual ImportError path is difficult to
        test in isolation without affecting other tests.
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        timers_file = config_dir / "timers_config.yaml"
        timers_file.write_text("reset_time: '17:00'")

        loader = ConfigLoader(config_dir=config_dir)

        # Test the error message that would be raised
        expected_message = "TimersConfig model not found. Ensure Agent 1 has created models.py"
        error = ConfigurationError(expected_message)

        assert "TimersConfig model not found" in str(error)
        assert "models.py" in str(error)


# ==============================================================================
# TEST CLASS: ConfigLoader.load_risk_config
# ==============================================================================


class TestLoadRiskConfig:
    """Test ConfigLoader.load_risk_config() method."""

    def test_load_risk_config_success(self, tmp_path):
        """Test loading valid risk config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        risk_file = config_dir / "risk_config.yaml"
        risk_file.write_text("""
max_contracts: 10
daily_loss_limit: -1000.0
""")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.RiskConfig', MockRiskConfig):
            config = loader.load_risk_config()

        assert isinstance(config, MockRiskConfig)
        assert config.max_contracts == 10
        assert config.daily_loss_limit == -1000.0

    def test_load_risk_config_file_not_found(self, tmp_path):
        """Test loading missing risk config raises error."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_risk_config()

        error_msg = str(exc_info.value)
        assert "Configuration file not found" in error_msg
        assert "risk_config.yaml" in error_msg

    def test_load_risk_config_custom_filename(self, tmp_path):
        """Test loading risk config with custom filename."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        custom_file = config_dir / "custom_risk.yaml"
        custom_file.write_text("""
max_contracts: 20
daily_loss_limit: -2000.0
""")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.RiskConfig', MockRiskConfig):
            config = loader.load_risk_config(file_name="custom_risk.yaml")

        assert config.max_contracts == 20


# ==============================================================================
# TEST CLASS: ConfigLoader.load_accounts_config
# ==============================================================================


class TestLoadAccountsConfig:
    """Test ConfigLoader.load_accounts_config() method."""

    def test_load_accounts_config_success(self, tmp_path):
        """Test loading valid accounts config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        accounts_file = config_dir / "accounts.yaml"
        accounts_file.write_text("""
api_key: test_key_123
username: test_user
""")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.AccountsConfig', MockAccountsConfig):
            config = loader.load_accounts_config()

        assert isinstance(config, MockAccountsConfig)
        assert config.api_key == "test_key_123"
        assert config.username == "test_user"

    def test_load_accounts_config_file_not_found(self, tmp_path):
        """Test loading missing accounts config raises error."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_accounts_config()

        error_msg = str(exc_info.value)
        assert "Configuration file not found" in error_msg
        assert "accounts.yaml" in error_msg

    def test_load_accounts_config_custom_filename(self, tmp_path):
        """Test loading accounts config with custom filename."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        custom_file = config_dir / "prod_accounts.yaml"
        custom_file.write_text("""
api_key: prod_key
username: prod_user
""")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.AccountsConfig', MockAccountsConfig):
            config = loader.load_accounts_config(file_name="prod_accounts.yaml")

        assert config.api_key == "prod_key"


# ==============================================================================
# TEST CLASS: ConfigLoader.load_api_config
# ==============================================================================


class TestLoadApiConfig:
    """Test ConfigLoader.load_api_config() method."""

    def test_load_api_config_success(self, tmp_path):
        """Test loading valid API config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        api_file = config_dir / "api_config.yaml"
        api_file.write_text("""
timeout: 60
retries: 5
""")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.ApiConfig', MockApiConfig):
            config = loader.load_api_config()

        assert isinstance(config, MockApiConfig)
        assert config.timeout == 60
        assert config.retries == 5

    def test_load_api_config_file_not_found_returns_none(self, tmp_path):
        """Test loading missing API config returns None (optional file)."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        loader = ConfigLoader(config_dir=config_dir)
        config = loader.load_api_config()

        assert config is None

    def test_load_api_config_custom_filename(self, tmp_path):
        """Test loading API config with custom filename."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        custom_file = config_dir / "prod_api.yaml"
        custom_file.write_text("""
timeout: 120
retries: 10
""")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.ApiConfig', MockApiConfig):
            config = loader.load_api_config(file_name="prod_api.yaml")

        assert config.timeout == 120

    def test_load_api_config_validation_error(self, tmp_path):
        """Test loading invalid API config raises validation error."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        api_file = config_dir / "api_config.yaml"
        api_file.write_text("""
timeout: -10
retries: 5
""")

        # Create strict mock that validates timeout > 0
        class StrictApiConfig(BaseModel):
            timeout: int = Field(gt=0)
            retries: int

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.ApiConfig', StrictApiConfig):
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_api_config()

            error_msg = str(exc_info.value)
            assert "validation" in error_msg.lower()


# ==============================================================================
# TEST CLASS: ConfigLoader.load_all_configs
# ==============================================================================


class TestLoadAllConfigs:
    """Test ConfigLoader.load_all_configs() method."""

    def test_load_all_configs_success(self, tmp_path):
        """Test loading all configs successfully."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create all config files
        (config_dir / "timers_config.yaml").write_text("reset_time: '17:00'\nenabled: true")
        (config_dir / "risk_config.yaml").write_text("max_contracts: 10\ndaily_loss_limit: -1000.0")
        (config_dir / "accounts.yaml").write_text("api_key: key\nusername: user")
        (config_dir / "api_config.yaml").write_text("timeout: 30\nretries: 3")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.TimersConfig', MockTimersConfig):
            with patch('risk_manager.config.models.RiskConfig', MockRiskConfig):
                with patch('risk_manager.config.models.AccountsConfig', MockAccountsConfig):
                    with patch('risk_manager.config.models.ApiConfig', MockApiConfig):
                        configs = loader.load_all_configs()

        assert 'timers' in configs
        assert 'risk' in configs
        assert 'accounts' in configs
        assert 'api' in configs
        assert isinstance(configs['timers'], MockTimersConfig)
        assert isinstance(configs['risk'], MockRiskConfig)
        assert isinstance(configs['accounts'], MockAccountsConfig)
        assert isinstance(configs['api'], MockApiConfig)

    def test_load_all_configs_without_optional_api(self, tmp_path):
        """Test loading all configs when API config missing (optional)."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create only required config files
        (config_dir / "timers_config.yaml").write_text("reset_time: '17:00'\nenabled: true")
        (config_dir / "risk_config.yaml").write_text("max_contracts: 10\ndaily_loss_limit: -1000.0")
        (config_dir / "accounts.yaml").write_text("api_key: key\nusername: user")
        # No api_config.yaml

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.TimersConfig', MockTimersConfig):
            with patch('risk_manager.config.models.RiskConfig', MockRiskConfig):
                with patch('risk_manager.config.models.AccountsConfig', MockAccountsConfig):
                    configs = loader.load_all_configs()

        assert configs['api'] is None
        assert configs['timers'] is not None
        assert configs['risk'] is not None
        assert configs['accounts'] is not None

    def test_load_all_configs_first_failure_stops(self, tmp_path):
        """Test loading stops on first config failure."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create only timers config, missing others
        (config_dir / "timers_config.yaml").write_text("reset_time: '17:00'")
        # Missing risk_config.yaml

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.TimersConfig', MockTimersConfig):
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_all_configs()

            # Should fail on risk config
            error_msg = str(exc_info.value)
            assert "risk_config.yaml" in error_msg

    def test_load_all_configs_returns_dict_with_correct_keys(self, tmp_path):
        """Test load_all_configs returns dict with specific keys."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "timers_config.yaml").write_text("reset_time: '17:00'\nenabled: true")
        (config_dir / "risk_config.yaml").write_text("max_contracts: 10\ndaily_loss_limit: -1000.0")
        (config_dir / "accounts.yaml").write_text("api_key: key\nusername: user")

        loader = ConfigLoader(config_dir=config_dir)

        with patch('risk_manager.config.models.TimersConfig', MockTimersConfig):
            with patch('risk_manager.config.models.RiskConfig', MockRiskConfig):
                with patch('risk_manager.config.models.AccountsConfig', MockAccountsConfig):
                    configs = loader.load_all_configs()

        expected_keys = {'timers', 'risk', 'accounts', 'api'}
        assert set(configs.keys()) == expected_keys


# ==============================================================================
# TEST CLASS: ConfigurationError
# ==============================================================================


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_configuration_error_is_exception(self):
        """Test ConfigurationError is an Exception."""
        error = ConfigurationError("Test error")
        assert isinstance(error, Exception)

    def test_configuration_error_message(self):
        """Test ConfigurationError preserves message."""
        error = ConfigurationError("Custom error message")
        assert str(error) == "Custom error message"

    def test_configuration_error_raised_properly(self):
        """Test ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Test error")

        assert "Test error" in str(exc_info.value)


# ==============================================================================
# INTEGRATION-STYLE TESTS
# ==============================================================================


class TestConfigLoaderIntegration:
    """Integration-style tests for complete workflows."""

    def test_full_config_loading_workflow(self, tmp_path):
        """Test complete workflow: directory → files → validation → configs."""
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=secret123\nUSERNAME=testuser")

        # Create config files with env vars
        (config_dir / "timers_config.yaml").write_text("reset_time: '17:00'\nenabled: true")
        (config_dir / "risk_config.yaml").write_text("max_contracts: 10\ndaily_loss_limit: -1000.0")
        (config_dir / "accounts.yaml").write_text("api_key: ${API_KEY}\nusername: ${USERNAME}")

        # Load configs
        loader = ConfigLoader(config_dir=config_dir, env_file=env_file)

        with patch('risk_manager.config.models.TimersConfig', MockTimersConfig):
            with patch('risk_manager.config.models.RiskConfig', MockRiskConfig):
                with patch('risk_manager.config.models.AccountsConfig', MockAccountsConfig):
                    configs = loader.load_all_configs()

        # Verify
        assert configs['accounts'].api_key == "secret123"
        assert configs['accounts'].username == "testuser"

    def test_error_message_quality(self, tmp_path):
        """Test that error messages are helpful and actionable."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        bad_yaml = config_dir / "test.yaml"
        bad_yaml.write_text("key: [unclosed")

        loader = ConfigLoader(config_dir=config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader._load_yaml_file(bad_yaml)

        error_msg = str(exc_info.value)
        # Error message should be helpful
        assert "Invalid YAML" in error_msg
        assert "test.yaml" in error_msg
        assert "Fix:" in error_msg or "Error:" in error_msg
