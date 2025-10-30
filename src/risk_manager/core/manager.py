"""Main Risk Manager class - the central entry point."""

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from project_x_py.utils import ProjectXLogger

from risk_manager.config.models import RiskConfig
from risk_manager.config.loader import ConfigLoader
from risk_manager.core.engine import RiskEngine
from risk_manager.core.events import EventBus, EventType, RiskEvent

# Get SDK logger for standardized logging
sdk_logger = ProjectXLogger.get_logger(__name__)


class RiskManager:
    """
    Main Risk Manager class.

    This is the central entry point for the risk management system.
    Coordinates all components and provides a clean API.
    """

    def __init__(self, config: RiskConfig, timers_config=None):
        self.config = config
        self.timers_config = timers_config  # Will be loaded if None
        self.event_bus = EventBus()

        # Component references (will be initialized)
        self.trading_integration = None
        self.ai_integration = None
        self.monitoring = None

        # Create engine (trading_integration will be set later)
        self.engine = RiskEngine(config, self.event_bus, trading_integration=None)

        # State
        self.running = False
        self._tasks: list[asyncio.Task] = []

        # Setup logging
        self._setup_logging()

        # Checkpoint 1: Service start
        sdk_logger.info("🚀 Risk Manager starting...")
        logger.info("Risk Manager initialized")

    def _setup_logging(self) -> None:
        """Configure logging."""
        # Access logging config from nested structure
        log_config = self.config.general.logging
        log_level = log_config.level

        logger.remove()  # Remove default handler
        logger.add(
            lambda msg: print(msg, end=""),
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        )

        if log_config.log_to_file:
            # Construct log file path from directory
            from pathlib import Path
            log_dir = Path(log_config.log_directory)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "risk_manager.log"

            logger.add(
                str(log_file),
                rotation=f"{log_config.max_log_size_mb} MB",
                retention=f"{log_config.log_retention_days} days",
                level=log_level,
            )

    @classmethod
    async def create(
        cls,
        instruments: list[str] | None = None,
        rules: dict[str, Any] | None = None,
        config: RiskConfig | None = None,
        config_file: str | Path | None = None,
        enable_ai: bool = False,
    ) -> "RiskManager":
        """
        Create and initialize a RiskManager instance.

        Args:
            instruments: List of instruments to monitor (e.g., ["MNQ", "ES"])
            rules: Dictionary of rule configurations
            config: RiskConfig object (optional)
            config_file: Path to config YAML file (optional)
            enable_ai: Enable AI features (requires Claude API key)

        Returns:
            Initialized RiskManager instance

        Example:
            >>> rm = await RiskManager.create(
            ...     instruments=["MNQ"],
            ...     rules={"max_daily_loss": -500.0, "max_contracts": 2}
            ... )
        """
        # Load config
        timers_config = None
        if config is None:
            if config_file:
                config_path = Path(config_file)
                loader = ConfigLoader(config_dir=config_path.parent if config_path.parent != Path('.') else Path('config'))
                config = loader.load_risk_config(file_name=config_path.name)
                # Also load timers_config
                try:
                    timers_config = loader.load_timers_config()
                except Exception as e:
                    logger.warning(f"Could not load timers_config.yaml: {e}")
            else:
                # For tests without config file, this won't work with nested structure
                # Tests should provide a config object directly
                raise ValueError("config parameter is required (config_file loading requires proper YAML)")

        # Override with provided rules
        if rules:
            for key, value in rules.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        # Create instance
        manager = cls(config, timers_config=timers_config)

        # Checkpoint 2: Config loaded
        sdk_logger.info(f"✅ Config loaded: {len(rules) if rules else 0} custom rules, monitoring {len(instruments) if instruments else 0} instruments")

        # Initialize trading integration if instruments provided
        if instruments:
            await manager._init_trading_integration(instruments)

        # Initialize AI if enabled
        if enable_ai and config.anthropic_api_key:
            await manager._init_ai_integration()

        # Add default rules
        await manager._add_default_rules()

        logger.info(f"Risk Manager created for instruments: {instruments}")
        return manager

    async def _init_trading_integration(self, instruments: list[str]) -> None:
        """Initialize trading integration with Project-X-Py."""
        from risk_manager.integrations.trading import TradingIntegration

        self.trading_integration = TradingIntegration(
            instruments=instruments,
            config=self.config,
            event_bus=self.event_bus,
        )

        await self.trading_integration.connect()

        # Wire trading_integration into RiskEngine for enforcement
        self.engine.trading_integration = self.trading_integration
        logger.info("✅ TradingIntegration wired to RiskEngine for enforcement")

        # Checkpoint 3: SDK connected
        sdk_logger.info(f"✅ SDK connected: {len(instruments)} instrument(s) - {', '.join(instruments)}")
        logger.info("Trading integration initialized")

    async def _init_ai_integration(self) -> None:
        """Initialize AI integration with Claude-Flow."""
        try:
            from risk_manager.ai.integration import AIIntegration

            self.ai_integration = AIIntegration(
                config=self.config,
                event_bus=self.event_bus,
            )

            await self.ai_integration.initialize()
            logger.info("AI integration initialized")
        except ImportError:
            logger.warning("AI integration not available (anthropic package not installed)")

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse duration string to seconds.

        Args:
            duration_str: Duration string (e.g., "60s", "15m", "1h", "until_reset")

        Returns:
            Duration in seconds (0 for special values like "until_reset")
        """
        if duration_str in ["until_reset", "until_session_start", "permanent"]:
            return 0  # Special values handled by lockout manager

        # Parse format: \d+[smh]
        import re
        match = re.match(r"^(\d+)([smh])$", duration_str)
        if not match:
            logger.warning(f"Invalid duration format: {duration_str}, using 0")
            return 0

        value, unit = match.groups()
        value = int(value)

        if unit == "s":
            return value
        elif unit == "m":
            return value * 60
        elif unit == "h":
            return value * 3600
        else:
            logger.warning(f"Unknown duration unit: {unit}, using 0")
            return 0

    async def _add_default_rules(self) -> None:
        """Add default risk rules based on configuration.

        Loads rules from config.rules structure and instantiates them.
        Only enabled rules are loaded.
        """
        from risk_manager.rules.daily_realized_loss import DailyRealizedLossRule
        from risk_manager.rules.daily_realized_profit import DailyRealizedProfitRule
        from risk_manager.rules.daily_unrealized_loss import DailyUnrealizedLossRule
        from risk_manager.rules.max_unrealized_profit import MaxUnrealizedProfitRule
        from risk_manager.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
        from risk_manager.rules.no_stop_loss_grace import NoStopLossGraceRule
        from risk_manager.rules.symbol_blocks import SymbolBlocksRule
        from risk_manager.rules.trade_frequency_limit import TradeFrequencyLimitRule
        from risk_manager.rules.cooldown_after_loss import CooldownAfterLossRule
        from risk_manager.rules.session_block_outside import SessionBlockOutsideRule
        from risk_manager.rules.auth_loss_guard import AuthLossGuardRule
        from risk_manager.rules.trade_management import TradeManagementRule
        from risk_manager.state.database import Database
        from risk_manager.state.pnl_tracker import PnLTracker
        from risk_manager.state.lockout_manager import LockoutManager
        from risk_manager.state.timer_manager import TimerManager

        # Initialize state managers (shared across rules)
        db_path = Path(self.config.general.database.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create Database instance
        db = Database(db_path=str(db_path))

        # Create state managers with Database object
        # Note: TimerManager must be created first to be passed to LockoutManager
        timer_manager = TimerManager()
        pnl_tracker = PnLTracker(db=db)
        lockout_manager = LockoutManager(database=db, timer_manager=timer_manager)

        rules_loaded = 0
        enabled_count = 0

        # Count enabled rules to show stats at the end
        if self.config.rules.daily_realized_loss.enabled:
            enabled_count += 1
        if self.config.rules.daily_realized_profit.enabled:
            enabled_count += 1
        if self.config.rules.max_contracts_per_instrument.enabled:
            enabled_count += 1
        if self.config.rules.no_stop_loss_grace.enabled:
            enabled_count += 1
        if self.config.rules.symbol_blocks.enabled:
            enabled_count += 1
        if self.config.rules.trade_frequency_limit.enabled:
            enabled_count += 1
        if self.config.rules.cooldown_after_loss.enabled:
            enabled_count += 1
        if self.config.rules.session_block_outside.enabled:
            enabled_count += 1
        if self.config.rules.auth_loss_guard.enabled:
            enabled_count += 1
        # These require tick data (count but skip):
        if self.config.rules.daily_unrealized_loss.enabled:
            enabled_count += 1
        if self.config.rules.max_unrealized_profit.enabled:
            enabled_count += 1
        if self.config.rules.trade_management.enabled:
            enabled_count += 1

        # RULE-003: Daily Realized Loss
        if self.config.rules.daily_realized_loss.enabled:
            rule = DailyRealizedLossRule(
                limit=self.config.rules.daily_realized_loss.limit,
                pnl_tracker=pnl_tracker,
                lockout_manager=lockout_manager,
                action="flatten",
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: DailyRealizedLossRule (limit=${rule.limit})")

        # RULE-013: Daily Realized Profit
        if self.config.rules.daily_realized_profit.enabled:
            rule = DailyRealizedProfitRule(
                target=self.config.rules.daily_realized_profit.target,
                pnl_tracker=pnl_tracker,
                lockout_manager=lockout_manager,
                action="flatten",
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: DailyRealizedProfitRule (target=${rule.target})")

        # RULE-002: Max Contracts Per Instrument
        if self.config.rules.max_contracts_per_instrument.enabled:
            # Build limits dict from config
            instrument_limits = self.config.rules.max_contracts_per_instrument.instrument_limits

            # Defensive: ensure it's a dict (config validation should ensure this, but be safe)
            if not isinstance(instrument_limits, dict):
                logger.warning(f"instrument_limits is not a dict (got {type(instrument_limits)}), using empty dict")
                instrument_limits = {}

            limits = instrument_limits.copy()

            # If no per-instrument overrides, use default_limit for known instruments
            if not limits:
                for symbol in self.config.general.instruments:
                    limits[symbol] = self.config.rules.max_contracts_per_instrument.default_limit

            rule = MaxContractsPerInstrumentRule(
                limits=limits,
                enforcement="close_all" if self.config.rules.max_contracts_per_instrument.close_all else "reduce_to_limit",
                unknown_symbol_action=f"allow_with_limit:{self.config.rules.max_contracts_per_instrument.default_limit}",
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: MaxContractsPerInstrumentRule ({len(limits)} symbols)")

        # RULE-008: No Stop Loss Grace
        if self.config.rules.no_stop_loss_grace.enabled:
            rule = NoStopLossGraceRule(
                grace_period_seconds=self.config.rules.no_stop_loss_grace.grace_period_seconds,
                enforcement="close_position",
                timer_manager=timer_manager,
                enabled=True,
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: NoStopLossGraceRule (grace={rule.grace_period_seconds}s)")

        # RULE-011: Symbol Blocks
        if self.config.rules.symbol_blocks.enabled:
            rule = SymbolBlocksRule(
                blocked_symbols=self.config.rules.symbol_blocks.blocked_symbols,
                action="close" if self.config.rules.symbol_blocks.close_position else "reject",
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: SymbolBlocksRule ({len(rule.blocked_symbols)} blocked)")

        # RULE-006: Trade Frequency Limit
        if self.config.rules.trade_frequency_limit.enabled and self.timers_config:
            limits = {
                "per_minute": self.config.rules.trade_frequency_limit.limits.per_minute,
                "per_hour": self.config.rules.trade_frequency_limit.limits.per_hour,
                "per_session": self.config.rules.trade_frequency_limit.limits.per_session,
            }

            # Parse cooldown durations from timers_config
            cooldown_on_breach = {
                "per_minute_breach": self._parse_duration(
                    self.timers_config.lockout_durations.timer_cooldown.trade_frequency.per_minute_breach
                ),
                "per_hour_breach": self._parse_duration(
                    self.timers_config.lockout_durations.timer_cooldown.trade_frequency.per_hour_breach
                ),
                "per_session_breach": self._parse_duration(
                    self.timers_config.lockout_durations.timer_cooldown.trade_frequency.per_session_breach
                ),
            }

            rule = TradeFrequencyLimitRule(
                limits=limits,
                cooldown_on_breach=cooldown_on_breach,
                timer_manager=timer_manager,
                db=db,
                action="cooldown",
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: TradeFrequencyLimitRule (limits={limits})")
        elif self.config.rules.trade_frequency_limit.enabled and not self.timers_config:
            logger.warning("⚠️ TradeFrequencyLimitRule requires timers_config.yaml (skipped)")

        # RULE-007: Cooldown After Loss
        if self.config.rules.cooldown_after_loss.enabled and self.timers_config:
            # Parse cooldown duration from timers_config
            cooldown_seconds = self._parse_duration(
                self.timers_config.lockout_durations.timer_cooldown.cooldown_after_loss
            )

            loss_thresholds = [
                {
                    "loss_amount": self.config.rules.cooldown_after_loss.loss_threshold,
                    "cooldown_duration": cooldown_seconds,
                }
            ]

            rule = CooldownAfterLossRule(
                loss_thresholds=loss_thresholds,
                timer_manager=timer_manager,
                pnl_tracker=pnl_tracker,
                lockout_manager=lockout_manager,
                action="flatten",
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: CooldownAfterLossRule (threshold=${self.config.rules.cooldown_after_loss.loss_threshold})")
        elif self.config.rules.cooldown_after_loss.enabled and not self.timers_config:
            logger.warning("⚠️ CooldownAfterLossRule requires timers_config.yaml (skipped)")

        # RULE-009: Session Block Outside
        if self.config.rules.session_block_outside.enabled and self.timers_config:
            # Build config dict from timers_config.session_hours
            session_config = {
                "enabled": self.timers_config.session_hours.enabled,
                "start": self.timers_config.session_hours.start,
                "end": self.timers_config.session_hours.end,
                "timezone": self.timers_config.session_hours.timezone,
                "allowed_days": self.timers_config.session_hours.allowed_days,
            }

            rule = SessionBlockOutsideRule(
                config=session_config,
                lockout_manager=lockout_manager,
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: SessionBlockOutsideRule (session={session_config['start']}-{session_config['end']})")
        elif self.config.rules.session_block_outside.enabled and not self.timers_config:
            logger.warning("⚠️ SessionBlockOutsideRule requires timers_config.yaml (skipped)")

        # RULE-010: Auth Loss Guard
        if self.config.rules.auth_loss_guard.enabled:
            rule = AuthLossGuardRule(
                alert_on_disconnect=True,
                alert_on_auth_failure=True,
                log_level="WARNING",
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: AuthLossGuardRule")

        # RULE-004: Daily Unrealized Loss
        if self.config.rules.daily_unrealized_loss.enabled:
            from risk_manager.integrations.trading import TICK_VALUES, ALIASES

            # Build tick dicts from TICK_VALUES (includes aliases)
            tick_values = {}
            tick_sizes = {}

            for symbol, info in TICK_VALUES.items():
                tick_values[symbol] = info["tick_value"]
                tick_sizes[symbol] = info["size"]

            # Add aliases
            for alias, target in ALIASES.items():
                if target in TICK_VALUES:
                    tick_values[alias] = TICK_VALUES[target]["tick_value"]
                    tick_sizes[alias] = TICK_VALUES[target]["size"]

            rule = DailyUnrealizedLossRule(
                loss_limit=self.config.rules.daily_unrealized_loss.limit,
                tick_values=tick_values,
                tick_sizes=tick_sizes,
                action="close_position",
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: DailyUnrealizedLossRule (limit=${rule.loss_limit})")

        # RULE-005: Max Unrealized Profit
        if self.config.rules.max_unrealized_profit.enabled:
            from risk_manager.integrations.trading import TICK_VALUES, ALIASES

            # Build tick dicts from TICK_VALUES (includes aliases)
            tick_values = {}
            tick_sizes = {}

            for symbol, info in TICK_VALUES.items():
                tick_values[symbol] = info["tick_value"]
                tick_sizes[symbol] = info["size"]

            # Add aliases
            for alias, target in ALIASES.items():
                if target in TICK_VALUES:
                    tick_values[alias] = TICK_VALUES[target]["tick_value"]
                    tick_sizes[alias] = TICK_VALUES[target]["size"]

            rule = MaxUnrealizedProfitRule(
                target=self.config.rules.max_unrealized_profit.target,
                tick_values=tick_values,
                tick_sizes=tick_sizes,
                action="close_position",
            )
            self.add_rule(rule)
            rules_loaded += 1
            logger.info(f"✅ Loaded: MaxUnrealizedProfitRule (target=${rule.target})")

        # Check if any rules were skipped
        skipped_count = enabled_count - rules_loaded

        if skipped_count > 0:
            logger.warning(f"⚠️ {skipped_count} rules skipped (require additional configuration)")
            logger.warning("   TradeManagement rule requires bracket order configuration")
            logger.warning("   Timer-based rules require timers_config.yaml")
        else:
            logger.success(f"🎉 All {rules_loaded} enabled rules loaded successfully!")

        # Checkpoint 4: Rules initialized
        sdk_logger.info(f"✅ Rules initialized: {rules_loaded} rules loaded from configuration")
        logger.info(f"Loaded {rules_loaded}/{enabled_count} enabled rules")

    async def start(self) -> None:
        """Start the risk manager."""
        if self.running:
            logger.warning("Risk Manager already running")
            return

        self.running = True
        logger.info("Starting Risk Manager...")

        # Start risk engine
        await self.engine.start()

        # Start trading integration
        if self.trading_integration:
            await self.trading_integration.start()

        # Start AI integration
        if self.ai_integration:
            await self.ai_integration.start()

        # Subscribe to events for processing
        self.event_bus.subscribe(EventType.ORDER_FILLED, self._handle_fill)
        self.event_bus.subscribe(EventType.POSITION_OPENED, self._handle_position_update)
        self.event_bus.subscribe(EventType.POSITION_CLOSED, self._handle_position_update)
        self.event_bus.subscribe(EventType.POSITION_UPDATED, self._handle_position_update)
        self.event_bus.subscribe(EventType.UNREALIZED_PNL_UPDATE, self._handle_unrealized_pnl)

        logger.success("✅ Risk Manager ACTIVE - Protecting your capital!")

    async def stop(self) -> None:
        """Stop the risk manager."""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping Risk Manager...")

        # Stop components
        await self.engine.stop()

        if self.trading_integration:
            await self.trading_integration.disconnect()

        if self.ai_integration:
            await self.ai_integration.stop()

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        logger.info("Risk Manager stopped")

    async def wait_until_stopped(self) -> None:
        """Wait until the risk manager is stopped."""
        while self.running:
            await asyncio.sleep(1)

    async def _handle_fill(self, event: RiskEvent) -> None:
        """Handle order fill event."""
        await self.engine.evaluate_rules(event)

    async def _handle_position_update(self, event: RiskEvent) -> None:
        """Handle position update event."""
        await self.engine.evaluate_rules(event)

    async def _handle_unrealized_pnl(self, event: RiskEvent) -> None:
        """Handle unrealized P&L update event."""
        await self.engine.evaluate_rules(event)

    def add_rule(self, rule: Any) -> None:
        """Add a custom risk rule."""
        self.engine.add_rule(rule)

    def on(self, event_type: EventType, handler) -> None:
        """Subscribe to events."""
        self.event_bus.subscribe(event_type, handler)

    def get_stats(self) -> dict[str, Any]:
        """Get current statistics."""
        return {
            "running": self.running,
            "engine": self.engine.get_stats(),
            "trading": self.trading_integration.get_stats() if self.trading_integration else {},
        }
