#!/usr/bin/env python3
"""
Risk Manager V34 - Development Runtime

Live microscope for validating rule math and event flow.

Usage:
    python run_dev.py                    # Interactive account selection
    python run_dev.py --account ACC123   # Explicit account
    python run_dev.py --config path.yaml # Custom config
    python run_dev.py --log-level DEBUG  # More verbose
    python run_dev.py --ui dashboard     # Dashboard mode (future)

Features:
    - Maximum logging visibility (8 checkpoints)
    - Real-time event streaming
    - Rule evaluation display
    - P&L tracking
    - Enforcement action visibility
    - Graceful Ctrl+C shutdown

Security:
    - Credentials from .env or OS keyring only
    - Never accepts credentials via CLI args
    - Automatic credential redaction in logs
"""

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path
from contextlib import contextmanager

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load .env file into environment variables BEFORE SDK access
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console

console = Console()


@contextmanager
def suppress_sdk_stderr():
    """Temporarily suppress SDK stderr messages (known harmless errors)."""
    # Save original stderr
    original_stderr = sys.stderr

    # Create a filtering stderr that drops SDK noise
    class FilteredStderr:
        def write(self, text):
            # Drop known SDK noise
            if "Failed to create Order object" in text:
                return
            if "Order.__init__() got an unexpected keyword argument 'fills'" in text:
                return
            # Pass through everything else
            original_stderr.write(text)

        def flush(self):
            original_stderr.flush()

    # Replace stderr temporarily
    sys.stderr = FilteredStderr()
    try:
        yield
    finally:
        # Restore original stderr
        sys.stderr = original_stderr


async def main():
    """Main development runtime entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Risk Manager V34 - Development Runtime",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        help="Path to risk_config.yaml (default: config/risk_config.yaml)",
        default=None,
    )
    parser.add_argument(
        "--account", help="Account ID to monitor (if not specified, will prompt)", default=None
    )
    parser.add_argument(
        "--log-level",
        help="Console log level (default: INFO)",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )
    parser.add_argument(
        "--ui",
        help="Display mode (default: log)",
        choices=["log", "dashboard"],
        default="log",
    )

    args = parser.parse_args()

    # Step 1: Setup logging (Agent 3)
    console.print()
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold cyan]        RISK MANAGER V34 - DEVELOPMENT MODE[/bold cyan]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print()

    try:
        from risk_manager.cli import setup_logging, cp1

        setup_logging(
            console_level=args.log_level,
            file_level="DEBUG",
            log_file="data/logs/risk_manager.log",
            colorize=True,
        )

        # Show what log level is active
        from loguru import logger
        logger.info(f"🎛️  Console Log Level: {args.log_level.upper()}")
        if args.log_level != "DEBUG":
            logger.info("💡 Tip: Use --log-level DEBUG to see detailed order payloads")

        cp1(details={"version": "1.0.0-dev", "mode": "development"})

    except ImportError as e:
        console.print(f"[red]Failed to setup logging: {e}[/red]")
        console.print("[yellow]Agent 3 logging system may not be installed[/yellow]")
        # Fall back to basic logging
        import logging

        logging.basicConfig(level=args.log_level, format="%(levelname)s: %(message)s")

    # Step 2: Load configuration (Agent 1)
    console.print("[cyan]Loading configuration...[/cyan]")

    try:
        from risk_manager.cli.config_loader import load_runtime_config

        runtime_config = load_runtime_config(
            config_path=args.config, account_id=args.account, interactive=True
        )

        console.print("[green]Configuration loaded successfully![/green]")
        console.print(f"  Account: [cyan]{runtime_config.selected_account_id}[/cyan]")
        console.print(
            f"  Instruments: [cyan]{', '.join(runtime_config.risk_config.general.instruments)}[/cyan]"
        )
        console.print(
            f"  Rules enabled: [cyan]{len([r for r in runtime_config.risk_config.rules.__dict__.values() if getattr(r, 'enabled', False)])}[/cyan]"
        )

    except ImportError as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        console.print("[yellow]Agent 1 config loader may not be installed[/yellow]")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]Configuration file not found: {e}[/red]")
        console.print()
        console.print("[yellow]Please run setup wizard first:[/yellow]")
        console.print("  [cyan]python admin_cli.py setup[/cyan]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        sys.exit(1)

    # Step 3: Initialize RiskManager (Agent 2 - existing code)
    console.print()
    console.print("[cyan]Initializing Risk Manager...[/cyan]")

    try:
        from risk_manager.core.manager import RiskManager

        # Create RiskManager with loaded config
        risk_manager = await RiskManager.create(config=runtime_config.risk_config)

        console.print("[green]Risk Manager initialized![/green]")

    except Exception as e:
        console.print(f"[red]Failed to initialize Risk Manager: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 4: Connect to TopstepX SDK
    console.print()
    console.print("[cyan]Connecting to TopstepX API...[/cyan]")
    console.print(f"  Username: [dim]{runtime_config.credentials.username}[/dim]")
    console.print(f"  Account: [cyan]{runtime_config.selected_account_id}[/cyan]")

    try:
        # Initialize trading integration
        from risk_manager.integrations.trading import TradingIntegration

        trading_integration = TradingIntegration(
            instruments=runtime_config.risk_config.general.instruments,
            config=runtime_config.risk_config,
            event_bus=risk_manager.event_bus,
        )

        # Connect to SDK
        await trading_integration.connect()

        # Wire up to engine
        risk_manager.trading_integration = trading_integration
        risk_manager.engine.trading_integration = trading_integration

        # Suppress verbose SDK logs (do this AFTER SDK is initialized)
        import logging
        for logger_name in ["project_x_py", "project_x_py.position_manager", "project_x_py.position_manager.core"]:
            sdk_log = logging.getLogger(logger_name)
            sdk_log.handlers = []  # Remove JSON formatter
            sdk_log.propagate = True  # Let logs go through our filter
            sdk_log.setLevel(logging.WARNING)  # Only show warnings

        console.print("[green]Connected to TopstepX API![/green]")

    except Exception as e:
        console.print(f"[red]Failed to connect to TopstepX: {e}[/red]")
        console.print()
        console.print("[yellow]Possible issues:[/yellow]")
        console.print("  1. Invalid credentials in .env")
        console.print("  2. Network connectivity")
        console.print("  3. TopstepX API down")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 5: Start Risk Manager
    console.print()
    console.print("[cyan]Starting event loop...[/cyan]")

    try:
        await risk_manager.start()

        console.print("[bold green]Risk Manager is running![/bold green]")
        console.print()
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        console.print()
        console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
        console.print("[bold cyan]                  LIVE EVENT FEED[/bold cyan]")
        console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
        console.print()

    except Exception as e:
        console.print(f"[red]Failed to start Risk Manager: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 6: Run until interrupted
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully."""
        console.print()
        console.print("[yellow]Shutdown signal received...[/yellow]")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Wait for shutdown signal
        await shutdown_event.wait()

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Keyboard interrupt received...[/yellow]")

    finally:
        # Step 7: Graceful shutdown
        console.print()
        console.print("[cyan]Shutting down gracefully...[/cyan]")

        try:
            await risk_manager.stop()
            console.print("[green]Risk Manager stopped[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning during shutdown: {e}[/yellow]")

        try:
            if risk_manager.trading_integration:
                await risk_manager.trading_integration.disconnect()
                console.print("[green]SDK disconnected[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning during disconnect: {e}[/yellow]")

        console.print()
        console.print("[bold green]Shutdown complete[/bold green]")
        console.print()


if __name__ == "__main__":
    try:
        # Suppress known SDK stderr noise during execution
        with suppress_sdk_stderr():
            asyncio.run(main())
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Development runtime cancelled by user[/yellow]")
        console.print()
        sys.exit(0)
    except Exception as e:
        console.print()
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)
