#!/usr/bin/env python3
"""Test the full runtime config loading flow used by run_dev.py"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
console = Console()


def test_runtime_config_flow():
    """Test the exact flow used by run_dev.py"""

    console.print("[bold cyan]Testing Runtime Config Flow (run_dev.py)[/bold cyan]")
    console.print()

    try:
        from risk_manager.cli.config_loader import load_runtime_config

        # This is exactly what run_dev.py does
        console.print("[yellow]Loading runtime config (interactive=False for test)...[/yellow]")

        runtime_config = load_runtime_config(
            config_path=None,  # Use default
            account_id=None,  # Will auto-select if only one account
            interactive=False  # Don't prompt
        )

        console.print("[green]SUCCESS: Runtime config loaded![/green]")
        console.print()

        # Test the exact access patterns from run_dev.py line 153-156
        console.print("[bold]Testing access patterns from run_dev.py:[/bold]")

        # Line 153: runtime_config.risk_config.general.instruments
        instruments = runtime_config.risk_config.general.instruments
        console.print(f"  runtime_config.risk_config.general.instruments: {instruments}")

        # Line 156: Count enabled rules (exactly as run_dev.py does)
        enabled_rules = len([
            r for r in runtime_config.risk_config.rules.__dict__.values()
            if getattr(r, 'enabled', False)
        ])
        console.print(f"  Enabled rules count: {enabled_rules}")

        # Additional tests: verify nested structure works
        console.print()
        console.print("[bold]Testing nested rule access:[/bold]")
        console.print(f"  rules.max_contracts.enabled: {runtime_config.risk_config.rules.max_contracts.enabled}")
        console.print(f"  rules.max_contracts.limit: {runtime_config.risk_config.rules.max_contracts.limit}")
        console.print(f"  rules.daily_realized_loss.enabled: {runtime_config.risk_config.rules.daily_realized_loss.enabled}")
        console.print(f"  rules.daily_realized_loss.limit: {runtime_config.risk_config.rules.daily_realized_loss.limit}")

        console.print()
        console.print("[bold green]All access patterns work correctly![/bold green]")
        return True

    except Exception as e:
        console.print(f"[red]FAILED: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_runtime_config_flow()
    sys.exit(0 if success else 1)
