"""
Configuration System for Risk Manager V34

This package provides:
1. Pydantic models for all configuration files (models.py)
   - TimersConfig: Timers, resets, lockouts, session hours
   - RiskConfig: All 13 risk rules configuration
   - AccountsConfig: Account credentials and multi-account support
   - ApiConfig: API connection settings and behavior

2. Environment variable substitution (env.py)
   - ${VAR_NAME} expansion from .env file or environment
   - Recursive substitution in nested structures

3. Configuration loader (loader.py)
   - Multi-file YAML loading
   - Pydantic validation
   - Clear error messages

All configuration is loaded from YAML files and validated using Pydantic v2.

Usage:
    from risk_manager.config import ConfigLoader

    loader = ConfigLoader(config_dir="config")
    config = loader.load_all_configs()
"""

# Environment variable utilities
from .env import (
    load_env_file,
    substitute_env_vars,
    substitute_env_vars_recursive,
    validate_env_vars,
)

# Configuration loader
from .loader import (
    ConfigLoader,
    ConfigurationError,
)

# Pydantic models (when created by Agent 1)
try:
    from .models import (
    # Timers Configuration
    TimersConfig,
    DailyResetConfig,
    LockoutDurationsConfig,
    HardLockoutConfig,
    TimerCooldownConfig,
    TradeFrequencyLockoutConfig,
    SessionHoursConfig,
    PreMarketConfig,
    AfterHoursConfig,
    HolidaysConfig,
    EarlyCloseConfig,
    AdvancedTimerConfig,
    AutoUnlockConfig,
    DSTConfig,

    # Risk Configuration
    RiskConfig,
    GeneralConfig,
    LoggingConfig,
    DatabaseConfig,
    NotificationsConfig,
    DiscordConfig,
    TelegramConfig,
    RulesConfig,

    # Trade-by-Trade Rules
    MaxContractsConfig,
    MaxContractsPerInstrumentConfig,
    DailyUnrealizedLossConfig,
    MaxUnrealizedProfitConfig,
    NoStopLossGraceConfig,
    SymbolBlocksConfig,

    # Timer/Cooldown Rules
    TradeFrequencyLimitConfig,
    FrequencyLimitsConfig,
    CooldownAfterLossConfig,

    # Hard Lockout Rules
    DailyRealizedLossConfig,
    DailyRealizedProfitConfig,
    SessionBlockOutsideConfig,
    AuthLossGuardConfig,

    # Automation
    TradeManagementConfig,
    AutoBreakevenConfig,
    TrailingStopConfig,

    # Accounts Configuration
    AccountsConfig,
    TopstepXConfig,
    MonitoredAccountConfig,
    AccountConfig,

    # API Configuration
    ApiConfig,
    ProjectXConfig,
    ConnectionConfig,
    RetryConfig,
    ReconnectConfig,
    KeepAliveConfig,
    RateLimitConfig,
    RateLimitRequestsConfig,
    RateLimitBurstConfig,
    RateLimitOrdersConfig,
    ErrorHandlingConfig,
    CircuitBreakerConfig,
    CacheConfig,
    CacheAccountConfig,
    CacheInstrumentsConfig,
    CacheMarketDataConfig,
    ApiLoggingConfig,
    AdvancedApiConfig,
    ConnectionPoolConfig,
    SSLConfig,
)
    # If import successful, set __all__ with models
    _models_available = True
except ImportError:
    # Models not created yet
    _models_available = False

# Define __all__ based on what's available
if _models_available:
    __all__ = [
        # Timers
        "TimersConfig",
    "DailyResetConfig",
    "LockoutDurationsConfig",
    "HardLockoutConfig",
    "TimerCooldownConfig",
    "TradeFrequencyLockoutConfig",
    "SessionHoursConfig",
    "PreMarketConfig",
    "AfterHoursConfig",
    "HolidaysConfig",
    "EarlyCloseConfig",
    "AdvancedTimerConfig",
    "AutoUnlockConfig",
    "DSTConfig",

    # Risk
    "RiskConfig",
    "GeneralConfig",
    "LoggingConfig",
    "DatabaseConfig",
    "NotificationsConfig",
    "DiscordConfig",
    "TelegramConfig",
    "RulesConfig",

    # Trade-by-Trade
    "MaxContractsConfig",
    "MaxContractsPerInstrumentConfig",
    "DailyUnrealizedLossConfig",
    "MaxUnrealizedProfitConfig",
    "NoStopLossGraceConfig",
    "SymbolBlocksConfig",

    # Timer/Cooldown
    "TradeFrequencyLimitConfig",
    "FrequencyLimitsConfig",
    "CooldownAfterLossConfig",

    # Hard Lockout
    "DailyRealizedLossConfig",
    "DailyRealizedProfitConfig",
    "SessionBlockOutsideConfig",
    "AuthLossGuardConfig",

    # Automation
    "TradeManagementConfig",
    "AutoBreakevenConfig",
    "TrailingStopConfig",

    # Accounts
    "AccountsConfig",
    "TopstepXConfig",
    "MonitoredAccountConfig",
    "AccountConfig",

    # API
    "ApiConfig",
    "ProjectXConfig",
    "ConnectionConfig",
    "RetryConfig",
    "ReconnectConfig",
    "KeepAliveConfig",
    "RateLimitConfig",
    "RateLimitRequestsConfig",
    "RateLimitBurstConfig",
    "RateLimitOrdersConfig",
    "ErrorHandlingConfig",
    "CircuitBreakerConfig",
    "CacheConfig",
    "CacheAccountConfig",
    "CacheInstrumentsConfig",
    "CacheMarketDataConfig",
    "ApiLoggingConfig",
    "AdvancedApiConfig",
    "ConnectionPoolConfig",
    "SSLConfig",

    # Environment utilities
    "load_env_file",
    "substitute_env_vars",
    "substitute_env_vars_recursive",
    "validate_env_vars",

    # Loader
    "ConfigLoader",
    "ConfigurationError",
    ]
else:
    # Models not available - export only env and loader utilities
    __all__ = [
        # Environment utilities
        "load_env_file",
        "substitute_env_vars",
        "substitute_env_vars_recursive",
        "validate_env_vars",

        # Loader
        "ConfigLoader",
        "ConfigurationError",
    ]
