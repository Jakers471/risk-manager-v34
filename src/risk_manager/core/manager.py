"""Main Risk Manager class - the central entry point."""

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from project_x_py.utils import ProjectXLogger

from risk_manager.core.config import RiskConfig
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

    def __init__(self, config: RiskConfig):
        self.config = config
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
        if config is None:
            if config_file:
                config = RiskConfig.from_file(config_file)
            else:
                config = RiskConfig()

        # Override with provided rules
        if rules:
            for key, value in rules.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        # Create instance
        manager = cls(config)

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

    async def _add_default_rules(self) -> None:
        """Add default risk rules based on configuration.

        Note: Rules are now loaded from config.rules.* structure.
        This method is kept for compatibility but rules should be
        instantiated from the config.rules object.
        """
        # TODO: Implement rule loading from config.rules structure
        # For now, rules are managed by the RiskEngine which loads them
        # from the config.rules.* structure

        # Checkpoint 4: Rules initialized
        sdk_logger.info(f"✅ Rules initialized from configuration")

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
        self.event_bus.subscribe(EventType.POSITION_UPDATED, self._handle_position_update)

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
