"""
Service runner for Risk Manager V34.

This module provides the controller that manages the Risk Manager
lifecycle within the Windows Service.
"""

import asyncio
import signal
import threading
from pathlib import Path
from typing import Any

from loguru import logger

from risk_manager.config.models import RiskConfig
from risk_manager.core.manager import RiskManager


class ServiceRunner:
    """
    Service runner for Risk Manager.

    Manages the Risk Manager lifecycle, handles configuration loading,
    SDK connection, graceful shutdown, and error recovery.

    Features:
        - Async event loop management in separate thread
        - Graceful shutdown handling
        - SDK reconnection on disconnect
        - Health check monitoring
        - Configuration reload support

    Usage:
        >>> runner = ServiceRunner(config_path="config/risk_config.yaml")
        >>> runner.start()  # Blocks until stopped
        >>> runner.stop()   # Graceful shutdown
    """

    def __init__(self, config_path: str | Path):
        """
        Initialize service runner.

        Args:
            config_path: Path to risk_config.yaml
        """
        self.config_path = Path(config_path)
        self.config: RiskConfig | None = None
        self.manager: RiskManager | None = None

        # Event loop management
        self.loop: asyncio.AbstractEventLoop | None = None
        self.loop_thread: threading.Thread | None = None

        # State
        self.running = False
        self.shutdown_event = threading.Event()

        logger.info(f"ServiceRunner initialized with config: {self.config_path}")

    def start(self) -> None:
        """
        Start the Risk Manager service.

        Loads configuration, initializes Risk Manager with SDK connection,
        and starts monitoring in background thread.

        This method blocks until the service is stopped.
        """
        if self.running:
            logger.warning("ServiceRunner already running")
            return

        logger.info("Starting ServiceRunner...")

        # Load configuration
        self._load_config()

        # Create event loop in separate thread
        self._start_event_loop()

        # Wait for shutdown
        self.shutdown_event.wait()

        logger.info("ServiceRunner stopped")

    def stop(self) -> None:
        """
        Stop the Risk Manager service gracefully.

        Shuts down the Risk Manager, closes SDK connections,
        and stops the event loop.
        """
        if not self.running:
            logger.warning("ServiceRunner not running")
            return

        logger.info("Stopping ServiceRunner...")

        self.running = False

        # Stop Risk Manager
        if self.manager and self.loop:
            # Run stop in event loop
            future = asyncio.run_coroutine_threadsafe(self.manager.stop(), self.loop)

            try:
                future.result(timeout=30)  # 30 second timeout
                logger.info("Risk Manager stopped successfully")

            except Exception as e:
                logger.error(f"Error stopping Risk Manager: {e}")

        # Stop event loop
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

            # Wait for thread to finish
            if self.loop_thread and self.loop_thread.is_alive():
                self.loop_thread.join(timeout=10)

            logger.info("Event loop stopped")

        # Signal shutdown complete
        self.shutdown_event.set()

    def restart(self) -> None:
        """
        Restart the Risk Manager service.

        Stops the current instance and starts a new one.
        """
        logger.info("Restarting ServiceRunner...")

        self.stop()
        self.start()

    def is_running(self) -> bool:
        """
        Check if service is running.

        Returns:
            True if running, False otherwise
        """
        return self.running and self.loop is not None and self.loop.is_running()

    def get_status(self) -> dict[str, Any]:
        """
        Get service status.

        Returns:
            Dictionary with service status information
        """
        return {
            "running": self.running,
            "loop_running": self.loop.is_running() if self.loop else False,
            "manager_running": self.manager.running if self.manager else False,
            "config_path": str(self.config_path),
        }

    def _load_config(self) -> None:
        """
        Load configuration from YAML file.

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        logger.info(f"Loading configuration from {self.config_path}")

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        # Load config using RiskConfig
        self.config = RiskConfig.from_file(self.config_path)

        logger.info(
            f"Configuration loaded: "
            f"max_daily_loss={self.config.max_daily_loss}, "
            f"max_contracts={self.config.max_contracts}, "
            f"log_level={self.config.log_level}"
        )

    def _start_event_loop(self) -> None:
        """
        Start async event loop in separate thread.

        Creates a new event loop, starts it in background thread,
        and initializes the Risk Manager.
        """
        logger.info("Starting event loop...")

        # Create thread for event loop
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()

        # Wait for loop to be ready
        for _ in range(50):  # Wait up to 5 seconds
            if self.loop and self.loop.is_running():
                break
            threading.Event().wait(0.1)

        if not self.loop or not self.loop.is_running():
            raise RuntimeError("Failed to start event loop")

        logger.info("Event loop started")

        # Initialize Risk Manager in event loop
        future = asyncio.run_coroutine_threadsafe(self._init_manager(), self.loop)

        try:
            future.result(timeout=60)  # 60 second timeout for initialization
            logger.info("Risk Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Risk Manager: {e}")
            raise

    def _run_event_loop(self) -> None:
        """
        Run event loop (executed in separate thread).

        Creates event loop and runs until stopped.
        """
        # Create new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # Run event loop
            self.loop.run_forever()

        finally:
            # Cleanup
            self.loop.close()
            self.loop = None

    async def _init_manager(self) -> None:
        """
        Initialize Risk Manager (async).

        Creates RiskManager instance, connects to SDK,
        and starts monitoring.
        """
        logger.info("Initializing Risk Manager...")

        # Get instruments from config
        instruments = getattr(self.config, "instruments", None)

        if not instruments:
            logger.warning("No instruments configured, using default: ['MNQ']")
            instruments = ["MNQ"]

        # Get rules from config
        rules = {}

        if hasattr(self.config, "max_daily_loss"):
            rules["max_daily_loss"] = self.config.max_daily_loss

        if hasattr(self.config, "max_contracts"):
            rules["max_contracts"] = self.config.max_contracts

        # Create Risk Manager
        self.manager = await RiskManager.create(
            instruments=instruments, rules=rules, config=self.config, enable_ai=False
        )

        # Start Risk Manager
        await self.manager.start()

        self.running = True

        logger.info("Risk Manager started")

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for graceful shutdown.

        Handles SIGTERM and SIGINT (Ctrl+C) for graceful shutdown.
        """

        def signal_handler(signum, frame):
            """Handle shutdown signals."""
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()

        # Register signal handlers (only works on main thread)
        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            logger.info("Signal handlers registered")

        except ValueError:
            # Not on main thread - skip signal handlers
            logger.debug("Cannot register signal handlers (not main thread)")

    def reload_config(self) -> None:
        """
        Reload configuration from file.

        Stops the current Risk Manager, reloads config,
        and starts with new configuration.
        """
        logger.info("Reloading configuration...")

        self.stop()
        self._load_config()
        self.start()

        logger.info("Configuration reloaded")


def main():
    """
    Run service runner in standalone mode (for testing).

    Usage:
        python runner.py [config_path]
    """
    import sys

    # Get config path from command line or use default
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/risk_config.yaml"

    # Create and start runner
    runner = ServiceRunner(config_path=config_path)

    try:
        logger.info("Starting Risk Manager in standalone mode...")
        logger.info("Press Ctrl+C to stop")

        runner.start()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")

    finally:
        runner.stop()
        logger.info("Service runner stopped")


if __name__ == "__main__":
    main()
