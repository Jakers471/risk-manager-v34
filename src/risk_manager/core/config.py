"""Configuration management for Risk Manager."""

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RiskConfig(BaseSettings):
    """Risk Manager configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ProjectX API
    project_x_api_key: str = Field(..., validation_alias="PROJECT_X_API_KEY")
    project_x_username: str = Field(..., validation_alias="PROJECT_X_USERNAME")
    project_x_api_url: str = Field(
        default="https://api.topstepx.com/api",
        validation_alias="PROJECT_X_API_URL"
    )
    project_x_websocket_url: str = Field(
        default="wss://api.topstepx.com",
        validation_alias="PROJECT_X_WEBSOCKET_URL"
    )

    # Risk Settings
    max_daily_loss: float = -1000.0
    max_contracts: int = 5
    require_stop_loss: bool = True
    stop_loss_grace_seconds: int = 60

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None

    # Performance
    enforcement_latency_target_ms: int = 500
    max_events_per_second: int = 1000

    # AI Features (optional)
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
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
    def from_file(cls, config_file: str | Path) -> "RiskConfig":
        """Load configuration from YAML file."""
        import yaml
        from pathlib import Path

        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return self.model_dump()
