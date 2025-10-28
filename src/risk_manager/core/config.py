"""Configuration management for Risk Manager."""

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RiskConfig(BaseSettings):
    """Risk Manager configuration.

    IMPORTANT: This class does NOT auto-load from environment variables or .env files.
    Use one of these methods to load configuration:
    - Direct instantiation: RiskConfig(project_x_api_key="...", ...)  # For tests
    - From YAML file: RiskConfig.from_file("config.yaml")  # For file-based config
    - From environment: RiskConfig.from_env()  # For production runtime
    """

    model_config = SettingsConfigDict(
        # Disable environment variable loading to prevent test contamination
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Customize settings sources to ONLY use init values by default.

        This prevents environment variables from leaking into tests.
        Use from_env() to explicitly load from environment.
        """
        # Only use init settings (values passed to constructor)
        return (init_settings,)

    # ProjectX API - Required fields with no defaults
    # NOTE: pydantic-settings automatically maps PROJECT_X_API_KEY to project_x_api_key
    # due to case_sensitive=False, so we don't need validation_alias
    project_x_api_key: str = Field(...)
    project_x_username: str = Field(...)
    project_x_api_url: str = Field(default="https://api.topstepx.com/api")
    project_x_websocket_url: str = Field(default="wss://api.topstepx.com")

    # Risk Settings
    max_daily_loss: float = -1000.0
    max_contracts: int = 5  # Default to 5 contracts
    require_stop_loss: bool = True
    stop_loss_grace_seconds: int = 60

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None

    # Performance
    enforcement_latency_target_ms: int = 500
    max_events_per_second: int = 1000

    # AI Features (optional)
    anthropic_api_key: str | None = Field(default=None)
    enable_ai: bool = False
    enable_pattern_recognition: bool = False
    enable_anomaly_detection: bool = False

    # Notifications (optional)
    discord_webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    # Development
    environment: str = "development"
    debug: bool = False

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "RiskConfig":
        """Load configuration from environment variables and .env file.

        Args:
            env_file: Path to .env file (default: ".env")

        Returns:
            RiskConfig instance with values from environment

        Note: This is the preferred method for production runtime.
        For testing, use the default constructor: RiskConfig(...)
        """
        from pydantic_settings import SettingsConfigDict, PydanticBaseSettingsSource
        from typing import Tuple, Type

        # Create a temporary class with env_file enabled and environment loading restored
        class EnvConfig(cls):
            """Config class that loads from environment."""
            model_config = SettingsConfigDict(
                env_file=str(env_file),
                env_file_encoding="utf-8",
                case_sensitive=False,
                extra="ignore",
                populate_by_name=True,
            )

            @classmethod
            def settings_customise_sources(
                cls,
                settings_cls: Type[BaseSettings],
                init_settings: PydanticBaseSettingsSource,
                env_settings: PydanticBaseSettingsSource,
                dotenv_settings: PydanticBaseSettingsSource,
                file_secret_settings: PydanticBaseSettingsSource,
            ) -> Tuple[PydanticBaseSettingsSource, ...]:
                """Enable all settings sources for environment loading."""
                # Use default priority: init > env > dotenv > file secrets
                return (init_settings, env_settings, dotenv_settings, file_secret_settings)

        return EnvConfig()

    @classmethod
    def from_file(cls, config_file: str | Path, load_env: bool = False) -> "RiskConfig":
        """Load configuration from YAML file.

        Args:
            config_file: Path to YAML configuration file
            load_env: If True, also load from environment variables (default: False)

        Note: By default, this bypasses environment variable loading to ensure
        only the YAML file values are used. For environment variable
        loading, either set load_env=True or use the default constructor: RiskConfig()
        """
        import yaml
        from pathlib import Path
        from pydantic_settings import PydanticBaseSettingsSource
        from typing import Any, Tuple, Type

        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        # Explicitly use UTF-8 encoding for unicode support
        with open(config_path, encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        if config_data is None:
            config_data = {}

        # Convert scientific notation strings to numbers
        # YAML sometimes parses "1e4" as string instead of number
        def convert_scientific_notation(data: dict) -> dict:
            """Convert scientific notation strings to numbers."""
            for key, value in data.items():
                if isinstance(value, str):
                    # Try to parse as float with scientific notation
                    try:
                        # Check if it looks like scientific notation
                        if 'e' in value.lower() or 'E' in value:
                            data[key] = float(value)
                    except (ValueError, AttributeError):
                        pass  # Keep as string
            return data

        config_data = convert_scientific_notation(config_data)

        if not load_env:
            # Create instance without loading from environment
            # by customizing settings sources to only use init values
            class FileOnlyConfig(cls):
                """Temporary config class that doesn't load from env."""
                @classmethod
                def settings_customise_sources(
                    cls,
                    settings_cls: Type[BaseSettings],
                    init_settings: PydanticBaseSettingsSource,
                    env_settings: PydanticBaseSettingsSource,
                    dotenv_settings: PydanticBaseSettingsSource,
                    file_secret_settings: PydanticBaseSettingsSource,
                ) -> Tuple[PydanticBaseSettingsSource, ...]:
                    # Only use init settings (the data we pass in)
                    return (init_settings,)

            return FileOnlyConfig(**config_data)
        else:
            # Load from both file and environment
            return cls(**config_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return self.model_dump()
