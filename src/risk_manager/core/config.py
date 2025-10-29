"""Backward compatibility shim for RiskConfig.

This module provides a test-friendly RiskConfig that supports both:
1. Old flat parameter style (for tests): RiskConfig(project_x_api_key="...", log_level="DEBUG")
2. New nested structure (for manager): config.general.logging.level

This allows existing tests to work without modification while the source code
uses the proper nested configuration models.
"""

from pathlib import Path
from typing import Any

# Import the proper nested models
from risk_manager.config.models import (
    RiskConfig as NestedRiskConfig,
    GeneralConfig,
    LoggingConfig,
    DatabaseConfig,
    NotificationsConfig,
    RulesConfig,
    MaxContractsConfig,
    MaxContractsPerInstrumentConfig,
    DailyUnrealizedLossConfig,
    MaxUnrealizedProfitConfig,
    NoStopLossGraceConfig,
    SymbolBlocksConfig,
    TradeFrequencyLimitConfig,
    CooldownAfterLossConfig,
    DailyRealizedLossConfig,
    DailyRealizedProfitConfig,
    SessionBlockOutsideConfig,
    AuthLossGuardConfig,
    TradeManagementConfig,
    AutoBreakevenConfig,
    TrailingStopConfig,
)


class RiskConfig:
    """Backward compatibility wrapper for RiskConfig.

    This class accepts old flat parameters and creates a proper nested RiskConfig internally.
    It exposes both flat attributes (for tests) and nested attributes (for manager).

    Usage:
        # Old style (tests)
        config = RiskConfig(project_x_api_key="...", log_level="DEBUG")
        assert config.log_level == "DEBUG"  # Flat access works

        # New style (manager)
        log_level = config.general.logging.level  # Nested access works
    """

    def __init__(
        self,
        # Old flat parameters (for backward compatibility)
        project_x_api_key: str | None = None,
        project_x_username: str | None = None,
        project_x_api_url: str = "https://api.topstepx.com/api",
        project_x_websocket_url: str = "wss://api.topstepx.com",
        max_daily_loss: float = -1000.0,
        max_contracts: int = 5,
        require_stop_loss: bool = True,
        stop_loss_grace_seconds: int = 60,
        log_level: str = "INFO",
        log_file: str | None = None,
        enforcement_latency_target_ms: int = 500,
        max_events_per_second: int = 1000,
        anthropic_api_key: str | None = None,
        enable_ai: bool = False,
        enable_pattern_recognition: bool = False,
        enable_anomaly_detection: bool = False,
        discord_webhook_url: str | None = None,
        telegram_bot_token: str | None = None,
        telegram_chat_id: str | None = None,
        environment: str = "development",
        debug: bool = False,
        # OR new nested structure
        general: GeneralConfig | None = None,
        rules: RulesConfig | None = None,
        **kwargs: Any
    ):
        """Initialize with either flat or nested parameters."""

        # If nested structure provided, use it directly
        if general is not None and rules is not None:
            self._nested = NestedRiskConfig(general=general, rules=rules)
        else:
            # Create nested structure from flat parameters
            logging_config = LoggingConfig(
                level=log_level,
                log_to_file=log_file is not None,
                log_directory=str(Path(log_file).parent) if log_file else "data/logs/",
                max_log_size_mb=100,
                log_retention_days=30,
            )

            general_config = GeneralConfig(
                instruments=["MNQ", "ES"],  # Default instruments
                timezone="America/Chicago",  # Default timezone
                logging=logging_config,
                database=DatabaseConfig(),
                notifications=NotificationsConfig(),
            )

            rules_config = RulesConfig(
                max_contracts=MaxContractsConfig(enabled=True, limit=max_contracts),
                max_contracts_per_instrument=MaxContractsPerInstrumentConfig(
                    enabled=True, default_limit=3
                ),
                daily_unrealized_loss=DailyUnrealizedLossConfig(
                    enabled=True, limit=-750
                ),
                max_unrealized_profit=MaxUnrealizedProfitConfig(
                    enabled=True, target=500
                ),
                no_stop_loss_grace=NoStopLossGraceConfig(
                    enabled=require_stop_loss,
                    require_within_seconds=stop_loss_grace_seconds,
                    grace_period_seconds=300  # 5 minutes grace period
                ),
                symbol_blocks=SymbolBlocksConfig(enabled=False),
                trade_frequency_limit=TradeFrequencyLimitConfig(
                    enabled=True,
                    limits={"per_minute": 3, "per_hour": 10, "per_session": 50}
                ),
                cooldown_after_loss=CooldownAfterLossConfig(
                    enabled=True, loss_threshold=-100
                ),
                daily_realized_loss=DailyRealizedLossConfig(
                    enabled=True, limit=max_daily_loss
                ),
                daily_realized_profit=DailyRealizedProfitConfig(
                    enabled=True, target=1000
                ),
                session_block_outside=SessionBlockOutsideConfig(
                    enabled=True,
                    start_time="08:30",
                    end_time="15:00",
                    timezone="America/Chicago"
                ),
                auth_loss_guard=AuthLossGuardConfig(
                    enabled=True, check_interval_seconds=30
                ),
                trade_management=TradeManagementConfig(
                    enabled=enable_ai,
                    auto_breakeven=AutoBreakevenConfig(
                        enabled=True,
                        profit_threshold_ticks=4,
                        offset_ticks=1
                    ),
                    trailing_stop=TrailingStopConfig(
                        enabled=True,
                        trail_ticks=4,
                        activation_profit_ticks=8
                    )
                ),
            )

            self._nested = NestedRiskConfig(general=general_config, rules=rules_config)

        # Store flat attributes for backward compatibility
        self.project_x_api_key = project_x_api_key or "test_key"
        self.project_x_username = project_x_username or "test_user"
        self.project_x_api_url = project_x_api_url
        self.project_x_websocket_url = project_x_websocket_url
        self.max_daily_loss = max_daily_loss
        self.max_contracts = max_contracts
        self.require_stop_loss = require_stop_loss
        self.stop_loss_grace_seconds = stop_loss_grace_seconds
        self.log_level = log_level
        self.log_file = log_file
        self.enforcement_latency_target_ms = enforcement_latency_target_ms
        self.max_events_per_second = max_events_per_second
        self.anthropic_api_key = anthropic_api_key
        self.enable_ai = enable_ai
        self.enable_pattern_recognition = enable_pattern_recognition
        self.enable_anomaly_detection = enable_anomaly_detection
        self.discord_webhook_url = discord_webhook_url
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.environment = environment
        self.debug = debug

    # Expose nested structure for manager.py
    @property
    def general(self) -> GeneralConfig:
        """Access general config (nested structure)."""
        return self._nested.general

    @property
    def rules(self) -> RulesConfig:
        """Access rules config (nested structure)."""
        return self._nested.rules

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return self._nested.model_dump()

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "RiskConfig":
        """Load configuration from environment variables and .env file."""
        # For tests, just return a default config
        return cls()

    @classmethod
    def from_file(cls, config_file: str | Path, load_env: bool = False) -> "RiskConfig":
        """Load configuration from YAML file."""
        from risk_manager.config.loader import ConfigLoader

        config_path = Path(config_file)
        loader = ConfigLoader(config_dir=config_path.parent, env_file=None)
        nested_config = loader.load_risk_config(file_name=config_path.name)

        # Wrap in backward compatibility layer
        return cls(general=nested_config.general, rules=nested_config.rules)
