"""Configuration loader for Risk Manager V34.

Loads all configuration files with:
- YAML parsing
- Environment variable substitution
- Pydantic validation
- Clear error messages
- File path resolution
"""

import logging
from pathlib import Path
from typing import Any, Type, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from .env import substitute_env_vars_recursive

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


class ConfigLoader:
    """Load and validate Risk Manager configuration files.

    Handles:
    - Multi-file configuration (timers, risk, accounts, api)
    - Environment variable substitution (${VAR_NAME})
    - Pydantic validation
    - Clear error messages with file/line context
    - Path resolution (relative to config directory)

    Example:
        loader = ConfigLoader(config_dir="config")

        # Load individual configs
        timers = loader.load_timers_config()
        risk = loader.load_risk_config()
        accounts = loader.load_accounts_config()

        # Or load all at once
        config = loader.load_all_configs()
    """

    def __init__(
        self,
        config_dir: str | Path = "config",
        env_file: str | Path | None = ".env"
    ):
        """Initialize configuration loader.

        Args:
            config_dir: Directory containing YAML config files
            env_file: Path to .env file for variable substitution (None to disable)
        """
        self.config_dir = Path(config_dir)
        self.env_file = Path(env_file) if env_file is not None else None

        # Ensure config directory exists
        if not self.config_dir.exists():
            raise ConfigurationError(
                f"Configuration directory not found: {self.config_dir.absolute()}\n"
                f"Expected directory structure:\n"
                f"  {self.config_dir}/\n"
                f"     timers_config.yaml\n"
                f"     risk_config.yaml\n"
                f"     accounts.yaml\n"
                f"     api_config.yaml (optional)\n"
            )

    def _load_yaml_file(self, file_path: Path) -> dict[str, Any]:
        """Load and parse YAML file with environment variable substitution.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML data as dictionary

        Raises:
            ConfigurationError: If file not found, invalid YAML, or env vars missing
        """
        # Check file exists
        if not file_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {file_path.absolute()}\n"
                f"Fix: Create the file or check the path.\n"
                f"Template files may be available in the config directory with .template extension."
            )

        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_text = f.read()

            logger.debug(f"Read configuration file: {file_path}")

        except Exception as e:
            raise ConfigurationError(
                f"Failed to read configuration file: {file_path}\n"
                f"Error: {e}"
            )

        try:
            # Substitute environment variables
            yaml_text = substitute_env_vars_recursive(
                yaml_text,
                env_file=self.env_file,
                raise_on_missing=True
            )

            logger.debug(f"Substituted environment variables in: {file_path}")

        except ValueError as e:
            raise ConfigurationError(
                f"Environment variable substitution failed in: {file_path}\n"
                f"Error: {e}"
            )

        try:
            # Parse YAML
            data = yaml.safe_load(yaml_text)

            if data is None:
                raise ConfigurationError(
                    f"Configuration file is empty: {file_path}\n"
                    f"Fix: Add configuration to the file."
                )

            logger.debug(f"Parsed YAML successfully: {file_path}")
            return data

        except yaml.YAMLError as e:
            # Extract line/column information if available
            error_msg = str(e)

            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                error_msg = (
                    f"Invalid YAML syntax in: {file_path}\n"
                    f"Line {mark.line + 1}, Column {mark.column + 1}\n"
                    f"Error: {e.problem}\n"
                    f"Fix: Check YAML syntax (indentation, colons, quotes, etc.)"
                )
            else:
                error_msg = (
                    f"Invalid YAML syntax in: {file_path}\n"
                    f"Error: {e}\n"
                    f"Fix: Check YAML syntax (indentation, colons, quotes, etc.)"
                )

            raise ConfigurationError(error_msg)

    def _validate_with_pydantic(
        self,
        data: dict[str, Any],
        model: Type[T],
        file_path: Path
    ) -> T:
        """Validate configuration data with Pydantic model.

        Args:
            data: Configuration data dictionary
            model: Pydantic model class
            file_path: Path to config file (for error messages)

        Returns:
            Validated Pydantic model instance

        Raises:
            ConfigurationError: If validation fails
        """
        try:
            # Validate with Pydantic
            config = model(**data)
            logger.info(f"Configuration validated successfully: {file_path.name}")
            return config

        except ValidationError as e:
            # Format validation errors with clear messages
            error_lines = [
                f"\nConfiguration validation failed: {file_path}\n",
                f"{len(e.errors())} validation error(s):\n"
            ]

            for error in e.errors():
                # Get field location (e.g., rules -> daily_realized_loss -> limit)
                loc = ' -> '.join(str(x) for x in error['loc'])
                msg = error['msg']
                error_type = error['type']

                error_lines.append(
                    f"\n  Field: {loc}\n"
                    f"  Error: {msg}\n"
                    f"  Type: {error_type}"
                )

            error_lines.append(
                f"\nFix: Correct the above errors in {file_path}\n"
                f"See configuration documentation for valid values."
            )

            raise ConfigurationError(''.join(error_lines))

        except Exception as e:
            raise ConfigurationError(
                f"Unexpected error validating configuration: {file_path}\n"
                f"Error: {e}"
            )

    def load_timers_config(self, file_name: str = "timers_config.yaml") -> BaseModel:
        """Load timers configuration (reset times, lockout durations, session hours).

        Args:
            file_name: Name of timers config file (default: timers_config.yaml)

        Returns:
            TimersConfig instance (validated)

        Raises:
            ConfigurationError: If loading or validation fails

        Example:
            timers = loader.load_timers_config()
            print(f"Daily reset time: {timers.daily_reset.time}")
            print(f"Session hours: {timers.session_hours.start} - {timers.session_hours.end}")
        """
        file_path = self.config_dir / file_name

        # Load YAML
        data = self._load_yaml_file(file_path)

        # Import model (deferred to avoid circular import)
        try:
            from .models import TimersConfig
        except ImportError:
            raise ConfigurationError(
                "TimersConfig model not found. Ensure Agent 1 has created models.py"
            )

        # Validate
        return self._validate_with_pydantic(data, TimersConfig, file_path)

    def load_risk_config(self, file_name: str = "risk_config.yaml") -> BaseModel:
        """Load risk configuration (all 13 risk rules).

        Args:
            file_name: Name of risk config file (default: risk_config.yaml)

        Returns:
            RiskConfig instance (validated)

        Raises:
            ConfigurationError: If loading or validation fails

        Example:
            risk = loader.load_risk_config()
            print(f"Max contracts: {risk.rules.max_contracts.limit}")
            print(f"Daily loss limit: {risk.rules.daily_realized_loss.limit}")
        """
        file_path = self.config_dir / file_name

        # Load YAML
        data = self._load_yaml_file(file_path)

        # Import model (deferred to avoid circular import)
        try:
            from .models import RiskConfig
        except ImportError:
            raise ConfigurationError(
                "RiskConfig model not found. Ensure Agent 1 has created models.py"
            )

        # Validate
        return self._validate_with_pydantic(data, RiskConfig, file_path)

    def load_accounts_config(self, file_name: str = "accounts.yaml") -> BaseModel:
        """Load accounts configuration (API credentials, monitored accounts).

        Args:
            file_name: Name of accounts config file (default: accounts.yaml)

        Returns:
            AccountsConfig instance (validated)

        Raises:
            ConfigurationError: If loading or validation fails

        Example:
            accounts = loader.load_accounts_config()
            print(f"API URL: {accounts.topstepx.api_url}")
            print(f"Monitored account: {accounts.monitored_account.account_id}")
        """
        file_path = self.config_dir / file_name

        # Load YAML
        data = self._load_yaml_file(file_path)

        # Import model (deferred to avoid circular import)
        try:
            from .models import AccountsConfig
        except ImportError:
            raise ConfigurationError(
                "AccountsConfig model not found. Ensure Agent 1 has created models.py"
            )

        # Validate
        return self._validate_with_pydantic(data, AccountsConfig, file_path)

    def load_api_config(self, file_name: str = "api_config.yaml") -> BaseModel | None:
        """Load API configuration (connection settings, timeouts, retries).

        Args:
            file_name: Name of API config file (default: api_config.yaml)

        Returns:
            ApiConfig instance (validated) or None if file not found

        Note:
            This config file is OPTIONAL. If not present, defaults will be used.

        Example:
            api = loader.load_api_config()
            if api:
                print(f"Connection timeout: {api.connection.timeout_seconds}")
        """
        file_path = self.config_dir / file_name

        # API config is optional - return None if not found
        if not file_path.exists():
            logger.info(f"API config file not found (optional): {file_name}")
            return None

        # Load YAML
        data = self._load_yaml_file(file_path)

        # Import model (deferred to avoid circular import)
        try:
            from .models import ApiConfig
        except ImportError:
            raise ConfigurationError(
                "ApiConfig model not found. Ensure Agent 1 has created models.py"
            )

        # Validate
        return self._validate_with_pydantic(data, ApiConfig, file_path)

    def load_all_configs(self) -> dict[str, BaseModel]:
        """Load all configuration files.

        Returns:
            Dictionary with keys:
                - 'timers': TimersConfig instance
                - 'risk': RiskConfig instance
                - 'accounts': AccountsConfig instance
                - 'api': ApiConfig instance or None

        Raises:
            ConfigurationError: If any required config fails to load

        Example:
            config = loader.load_all_configs()

            timers = config['timers']
            risk = config['risk']
            accounts = config['accounts']
            api = config.get('api')  # May be None
        """
        logger.info("Loading all configuration files...")

        try:
            # Load required configs
            timers = self.load_timers_config()
            logger.info(" Timers configuration loaded")

            risk = self.load_risk_config()
            logger.info(" Risk configuration loaded")

            accounts = self.load_accounts_config()
            logger.info(" Accounts configuration loaded")

            # Load optional configs
            api = self.load_api_config()
            if api:
                logger.info(" API configuration loaded")
            else:
                logger.info("- API configuration not found (using defaults)")

            logger.info("All configurations loaded successfully!")

            return {
                'timers': timers,
                'risk': risk,
                'accounts': accounts,
                'api': api,
            }

        except ConfigurationError:
            logger.error("Configuration loading failed")
            raise


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    try:
        # Create loader
        loader = ConfigLoader(config_dir="config", env_file=".env")

        # Load all configs
        config = loader.load_all_configs()

        print("\n=== Configuration Summary ===")
        print(f"Timers config: {config['timers']}")
        print(f"Risk config: {config['risk']}")
        print(f"Accounts config: {config['accounts']}")
        print(f"API config: {config['api']}")

    except ConfigurationError as e:
        print(f"\nConfiguration Error:\n{e}")
    except Exception as e:
        print(f"\nUnexpected Error:\n{e}")
