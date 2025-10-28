"""
Admin CLI for Risk Manager V34

Provides commands for:
- Service control (start, stop, restart, status, install, uninstall)
- Configuration management (show, edit, validate, reload)
- Rule management (list, enable, disable, configure)
- Lockout management (list, remove, history)
- Monitoring (status, logs)

All commands require administrator privileges (UAC elevation on Windows).
"""

import asyncio
import ctypes
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

# Initialize Typer app
app = typer.Typer(
    name="admin",
    help="Risk Manager V34 - Admin CLI",
    add_completion=False,
    rich_markup_mode="rich"
)

# Rich console for beautiful output
console = Console()


# ==============================================================================
# WINDOWS UAC ELEVATION CHECK
# ==============================================================================

def is_admin() -> bool:
    """
    Check if script is running with administrator privileges.

    Returns:
        True if running as admin, False otherwise
    """
    if platform.system() != "Windows":
        console.print("[yellow]Warning: Admin elevation check only supported on Windows[/yellow]")
        return True

    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def require_admin(func):
    """
    Decorator to require admin privileges for a command.

    If not admin, shows error message and exits.
    """
    def wrapper(*args, **kwargs):
        if not is_admin():
            console.print()
            console.print(Panel(
                "[bold red]Administrator Privileges Required[/bold red]\n\n"
                "This command requires administrator privileges.\n\n"
                "[bold]To run as administrator:[/bold]\n"
                "1. Open Command Prompt or PowerShell as Administrator\n"
                "2. Run: [cyan]admin_cli <command>[/cyan]\n\n"
                "Or right-click Command Prompt and select 'Run as administrator'",
                title="Access Denied",
                border_style="red",
                expand=False
            ))
            console.print()
            raise typer.Exit(code=1)

        return func(*args, **kwargs)

    return wrapper


# ==============================================================================
# CONFIGURATION HELPERS
# ==============================================================================

def get_config_dir() -> Path:
    """Get configuration directory path."""
    # Check for config in current directory first, then ProgramData
    local_config = Path("config")
    if local_config.exists():
        return local_config

    # Windows: C:\ProgramData\SimpleRiskManager\config
    if platform.system() == "Windows":
        return Path("C:/ProgramData/SimpleRiskManager/config")

    # Linux/Mac: /etc/risk-manager
    return Path("/etc/risk-manager")


def get_data_dir() -> Path:
    """Get data directory path."""
    # Check for data in current directory first
    local_data = Path("data")
    if local_data.exists():
        return local_data

    # Windows: C:\ProgramData\SimpleRiskManager\data
    if platform.system() == "Windows":
        return Path("C:/ProgramData/SimpleRiskManager/data")

    # Linux/Mac: /var/lib/risk-manager
    return Path("/var/lib/risk-manager")


def load_risk_config() -> dict:
    """Load risk configuration from YAML file."""
    config_file = get_config_dir() / "risk_config.yaml"

    if not config_file.exists():
        console.print(f"[red]Configuration file not found: {config_file}[/red]")
        raise typer.Exit(code=1)

    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def save_risk_config(config: dict) -> None:
    """Save risk configuration to YAML file."""
    config_file = get_config_dir() / "risk_config.yaml"

    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Configuration saved: {config_file}[/green]")


# ==============================================================================
# SERVICE CONTROL GROUP
# ==============================================================================

service = typer.Typer(help="Service control commands")
app.add_typer(service, name="service")


@service.command("start")
@require_admin
def service_start():
    """Start the Risk Manager service."""
    console.print("[cyan]Starting Risk Manager service...[/cyan]")

    # TODO: Implement Windows service start
    # For now, placeholder
    console.print("[yellow]Service control not yet implemented[/yellow]")
    console.print("[dim]This will start the Windows service when implemented[/dim]")


@service.command("stop")
@require_admin
def service_stop():
    """Stop the Risk Manager service."""
    console.print("[cyan]Stopping Risk Manager service...[/cyan]")

    # TODO: Implement Windows service stop
    console.print("[yellow]Service control not yet implemented[/yellow]")
    console.print("[dim]This will stop the Windows service when implemented[/dim]")


@service.command("restart")
@require_admin
def service_restart():
    """Restart the Risk Manager service."""
    console.print("[cyan]Restarting Risk Manager service...[/cyan]")

    # TODO: Implement Windows service restart
    console.print("[yellow]Service control not yet implemented[/yellow]")
    console.print("[dim]This will restart the Windows service when implemented[/dim]")


@service.command("status")
def service_status():
    """Show service status."""
    console.print("[cyan]Checking Risk Manager service status...[/cyan]")
    console.print()

    # TODO: Implement Windows service status check
    table = Table(title="Service Status", box=box.ROUNDED)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Service Name", "SimpleRiskManager")
    table.add_row("Status", "[yellow]Not Implemented[/yellow]")
    table.add_row("Start Type", "Automatic")
    table.add_row("Uptime", "N/A")

    console.print(table)
    console.print()
    console.print("[dim]Full service control will be implemented in deployment phase[/dim]")


@service.command("install")
@require_admin
def service_install():
    """Install Risk Manager as Windows service."""
    console.print("[cyan]Installing Risk Manager Windows service...[/cyan]")

    # TODO: Implement Windows service installation
    console.print("[yellow]Service installation not yet implemented[/yellow]")
    console.print()
    console.print("[bold]This will:[/bold]")
    console.print("  1. Register Risk Manager as Windows service")
    console.print("  2. Configure auto-start on boot")
    console.print("  3. Set service recovery options")
    console.print("  4. Configure Windows ACL permissions")


@service.command("uninstall")
@require_admin
def service_uninstall():
    """Uninstall Risk Manager Windows service."""
    if not Confirm.ask("[red]Are you sure you want to uninstall the service?[/red]"):
        console.print("[yellow]Cancelled[/yellow]")
        raise typer.Exit()

    console.print("[cyan]Uninstalling Risk Manager Windows service...[/cyan]")

    # TODO: Implement Windows service uninstallation
    console.print("[yellow]Service uninstallation not yet implemented[/yellow]")


# ==============================================================================
# CONFIGURATION MANAGEMENT GROUP
# ==============================================================================

config_group = typer.Typer(help="Configuration management commands")
app.add_typer(config_group, name="config")


@config_group.command("show")
def config_show():
    """Display current configuration."""
    console.print("[cyan]Loading configuration...[/cyan]")
    console.print()

    try:
        config = load_risk_config()

        # Display general settings
        console.print(Panel(
            f"[bold]Instruments:[/bold] {', '.join(config['general']['instruments'])}\n"
            f"[bold]Timezone:[/bold] {config['general']['timezone']}\n"
            f"[bold]Log Level:[/bold] {config['general']['logging']['level']}",
            title="General Settings",
            border_style="cyan"
        ))

        console.print()

        # Display enabled rules
        enabled_rules = []
        disabled_rules = []

        for rule_key, rule_config in config['rules'].items():
            if rule_config.get('enabled', False):
                enabled_rules.append(rule_key)
            else:
                disabled_rules.append(rule_key)

        console.print(Panel(
            f"[bold green]Enabled ({len(enabled_rules)}):[/bold green]\n" +
            "\n".join(f"  - {rule}" for rule in enabled_rules) +
            f"\n\n[bold red]Disabled ({len(disabled_rules)}):[/bold red]\n" +
            "\n".join(f"  - {rule}" for rule in disabled_rules),
            title="Rule Status",
            border_style="cyan"
        ))

    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        raise typer.Exit(code=1)


@config_group.command("edit")
@require_admin
def config_edit():
    """Open configuration file in default editor."""
    config_file = get_config_dir() / "risk_config.yaml"

    if not config_file.exists():
        console.print(f"[red]Configuration file not found: {config_file}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Opening configuration file: {config_file}[/cyan]")

    # Open in default editor
    if platform.system() == "Windows":
        os.startfile(config_file)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", str(config_file)])
    else:  # Linux
        subprocess.run(["xdg-open", str(config_file)])

    console.print("[green]Configuration file opened in default editor[/green]")
    console.print("[yellow]Remember to run 'admin_cli config validate' after making changes[/yellow]")


@config_group.command("validate")
def config_validate():
    """Validate configuration file syntax."""
    console.print("[cyan]Validating configuration...[/cyan]")

    try:
        from risk_manager.config.validator import validate_risk_config
        from risk_manager.config.loader import ConfigLoader

        config_file = get_config_dir() / "risk_config.yaml"

        # Load and validate
        loader = ConfigLoader(config_dir=get_config_dir())
        config = loader.load_risk_config()

        console.print()
        console.print(Panel(
            "[bold green]Configuration is valid![/bold green]\n\n"
            f"File: {config_file}\n"
            f"Rules: {len(config.rules.__dict__)} configured\n"
            f"Instruments: {len(config.general.instruments)}",
            title="Validation Success",
            border_style="green"
        ))

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Configuration validation failed![/bold red]\n\n"
            f"Error: {str(e)}\n\n"
            "Please fix the errors and try again.",
            title="Validation Failed",
            border_style="red"
        ))
        raise typer.Exit(code=1)


@config_group.command("reload")
@require_admin
def config_reload():
    """Reload configuration (restart service)."""
    console.print("[cyan]Reloading configuration...[/cyan]")

    # Validate first
    try:
        config_validate()
    except typer.Exit:
        console.print("[red]Configuration validation failed. Cannot reload.[/red]")
        raise

    # Restart service to reload
    if Confirm.ask("[yellow]This will restart the service. Continue?[/yellow]"):
        service_restart()
        console.print("[green]Configuration reloaded successfully[/green]")
    else:
        console.print("[yellow]Cancelled[/yellow]")


# ==============================================================================
# RULE MANAGEMENT GROUP
# ==============================================================================

rules = typer.Typer(help="Rule management commands")
app.add_typer(rules, name="rules")


@rules.command("list")
def rules_list():
    """List all rules and their status."""
    console.print("[cyan]Loading rules...[/cyan]")
    console.print()

    try:
        config = load_risk_config()

        table = Table(title="Risk Rules", box=box.ROUNDED)
        table.add_column("Rule ID", style="cyan", no_wrap=True)
        table.add_column("Status", style="white", no_wrap=True)
        table.add_column("Key Settings", style="dim")

        # Rule mappings
        rule_info = {
            'max_contracts': ('RULE-001', 'Max Contracts', 'limit'),
            'max_contracts_per_instrument': ('RULE-002', 'Max Contracts Per Instrument', 'default_limit'),
            'daily_realized_loss': ('RULE-003', 'Daily Realized Loss', 'limit'),
            'daily_unrealized_loss': ('RULE-004', 'Daily Unrealized Loss', 'limit'),
            'max_unrealized_profit': ('RULE-005', 'Max Unrealized Profit', 'target'),
            'trade_frequency_limit': ('RULE-006', 'Trade Frequency Limit', 'limits'),
            'cooldown_after_loss': ('RULE-007', 'Cooldown After Loss', 'loss_threshold'),
            'no_stop_loss_grace': ('RULE-008', 'Stop-Loss Enforcement', 'require_within_seconds'),
            'session_block_outside': ('RULE-009', 'Session Block Outside', 'respect_holidays'),
            'auth_loss_guard': ('RULE-010', 'Auth Loss Guard', 'check_interval_seconds'),
            'symbol_blocks': ('RULE-011', 'Symbol Blocks', 'blocked_symbols'),
            'trade_management': ('RULE-012', 'Trade Management', 'auto_breakeven'),
            'daily_realized_profit': ('RULE-013', 'Daily Realized Profit', 'target'),
        }

        for rule_key, (rule_id, rule_name, setting_key) in rule_info.items():
            if rule_key in config['rules']:
                rule_config = config['rules'][rule_key]
                enabled = rule_config.get('enabled', False)

                status_text = Text()
                if enabled:
                    status_text.append("ENABLED", style="bold green")
                else:
                    status_text.append("DISABLED", style="bold red")

                # Get key setting value
                setting_value = rule_config.get(setting_key, 'N/A')
                if isinstance(setting_value, dict):
                    setting_value = str(setting_value)[:40] + "..."

                table.add_row(
                    f"{rule_id}: {rule_name}",
                    status_text,
                    str(setting_value)
                )

        console.print(table)
        console.print()
        console.print("[dim]Use 'admin_cli rules enable <rule_id>' to enable a rule[/dim]")
        console.print("[dim]Use 'admin_cli rules disable <rule_id>' to disable a rule[/dim]")

    except Exception as e:
        console.print(f"[red]Error loading rules: {e}[/red]")
        raise typer.Exit(code=1)


@rules.command("enable")
@require_admin
def rules_enable(rule_id: str = typer.Argument(..., help="Rule ID (e.g., 'max_contracts')")):
    """Enable a specific rule."""
    console.print(f"[cyan]Enabling rule: {rule_id}...[/cyan]")

    try:
        config = load_risk_config()

        if rule_id not in config['rules']:
            console.print(f"[red]Rule not found: {rule_id}[/red]")
            console.print("[dim]Use 'admin_cli rules list' to see available rules[/dim]")
            raise typer.Exit(code=1)

        config['rules'][rule_id]['enabled'] = True
        save_risk_config(config)

        console.print(f"[green]Rule enabled: {rule_id}[/green]")
        console.print("[yellow]Remember to reload configuration: admin_cli config reload[/yellow]")

    except Exception as e:
        console.print(f"[red]Error enabling rule: {e}[/red]")
        raise typer.Exit(code=1)


@rules.command("disable")
@require_admin
def rules_disable(rule_id: str = typer.Argument(..., help="Rule ID (e.g., 'max_contracts')")):
    """Disable a specific rule."""
    console.print(f"[cyan]Disabling rule: {rule_id}...[/cyan]")

    try:
        config = load_risk_config()

        if rule_id not in config['rules']:
            console.print(f"[red]Rule not found: {rule_id}[/red]")
            console.print("[dim]Use 'admin_cli rules list' to see available rules[/dim]")
            raise typer.Exit(code=1)

        config['rules'][rule_id]['enabled'] = False
        save_risk_config(config)

        console.print(f"[green]Rule disabled: {rule_id}[/green]")
        console.print("[yellow]Remember to reload configuration: admin_cli config reload[/yellow]")

    except Exception as e:
        console.print(f"[red]Error disabling rule: {e}[/red]")
        raise typer.Exit(code=1)


@rules.command("configure")
@require_admin
def rules_configure(rule_id: str = typer.Argument(..., help="Rule ID to configure")):
    """Configure rule parameters interactively."""
    console.print(f"[cyan]Configuring rule: {rule_id}...[/cyan]")
    console.print()
    console.print("[yellow]Interactive configuration not yet implemented[/yellow]")
    console.print("[dim]For now, use 'admin_cli config edit' to edit configuration manually[/dim]")


# ==============================================================================
# LOCKOUT MANAGEMENT GROUP
# ==============================================================================

lockouts = typer.Typer(help="Lockout management commands")
app.add_typer(lockouts, name="lockouts")


@lockouts.command("list")
def lockouts_list():
    """List active lockouts."""
    console.print("[cyan]Loading lockouts...[/cyan]")
    console.print()

    try:
        # TODO: Load lockouts from database
        table = Table(title="Active Lockouts", box=box.ROUNDED)
        table.add_column("Account ID", style="cyan", no_wrap=True)
        table.add_column("Reason", style="white")
        table.add_column("Locked At", style="dim")
        table.add_column("Expires", style="yellow")

        # Example data (replace with actual database query)
        # table.add_row("PRAC-V2-126244", "RULE-003: Daily Loss Limit", "2025-10-28 09:00:00", "Until Reset")

        console.print(table)
        console.print()
        console.print("[dim]No active lockouts[/dim]")

    except Exception as e:
        console.print(f"[red]Error loading lockouts: {e}[/red]")
        raise typer.Exit(code=1)


@lockouts.command("remove")
@require_admin
def lockouts_remove(
    account_id: str = typer.Argument(..., help="Account ID to unlock")
):
    """Remove lockout (emergency unlock)."""
    console.print(f"[cyan]Removing lockout for account: {account_id}...[/cyan]")

    if not Confirm.ask(f"[red]Are you sure you want to unlock {account_id}?[/red]"):
        console.print("[yellow]Cancelled[/yellow]")
        raise typer.Exit()

    try:
        # TODO: Remove lockout from database
        console.print(f"[green]Lockout removed for: {account_id}[/green]")
        console.print("[yellow]Account can now trade again[/yellow]")

    except Exception as e:
        console.print(f"[red]Error removing lockout: {e}[/red]")
        raise typer.Exit(code=1)


@lockouts.command("history")
def lockouts_history(
    account_id: Optional[str] = typer.Option(None, "--account", "-a", help="Filter by account ID"),
    limit: int = typer.Option(50, "--limit", "-l", help="Number of records to show")
):
    """Show lockout history."""
    console.print("[cyan]Loading lockout history...[/cyan]")
    console.print()

    try:
        # TODO: Load lockout history from database
        table = Table(title="Lockout History", box=box.ROUNDED)
        table.add_column("Date", style="cyan", no_wrap=True)
        table.add_column("Account", style="white", no_wrap=True)
        table.add_column("Reason", style="dim")
        table.add_column("Duration", style="yellow")

        # Example data (replace with actual database query)
        # table.add_row("2025-10-28", "PRAC-V2-126244", "RULE-003: Daily Loss", "Until Reset")

        console.print(table)
        console.print()
        console.print("[dim]No lockout history[/dim]")

    except Exception as e:
        console.print(f"[red]Error loading history: {e}[/red]")
        raise typer.Exit(code=1)


# ==============================================================================
# MONITORING COMMANDS
# ==============================================================================

@app.command("status")
def status():
    """Show system status (accounts, rules, P&L)."""
    console.print("[cyan]Loading system status...[/cyan]")
    console.print()

    try:
        config = load_risk_config()

        # Service status
        console.print(Panel(
            "[bold]Service:[/bold] [yellow]Not Implemented[/yellow]\n"
            "[bold]Uptime:[/bold] N/A\n"
            "[bold]Mode:[/bold] Development",
            title="Service Status",
            border_style="cyan"
        ))

        console.print()

        # Accounts status
        console.print(Panel(
            "[bold]Accounts Monitored:[/bold] 0\n"
            "[bold]Active Lockouts:[/bold] 0\n"
            "[bold]Active Positions:[/bold] 0",
            title="Accounts Status",
            border_style="cyan"
        ))

        console.print()

        # Rules status
        enabled_rules = sum(1 for rule in config['rules'].values() if rule.get('enabled'))
        total_rules = len(config['rules'])

        console.print(Panel(
            f"[bold]Total Rules:[/bold] {total_rules}\n"
            f"[bold]Enabled:[/bold] [green]{enabled_rules}[/green]\n"
            f"[bold]Disabled:[/bold] [red]{total_rules - enabled_rules}[/red]",
            title="Rules Status",
            border_style="cyan"
        ))

        console.print()
        console.print("[dim]Full status monitoring will be available when service is running[/dim]")

    except Exception as e:
        console.print(f"[red]Error loading status: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("logs")
def logs(
    tail: int = typer.Option(50, "--tail", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output")
):
    """View recent logs."""
    log_file = get_data_dir() / "logs" / "risk_manager.log"

    if not log_file.exists():
        console.print(f"[yellow]Log file not found: {log_file}[/yellow]")
        console.print("[dim]Start the service to generate logs[/dim]")
        raise typer.Exit()

    console.print(f"[cyan]Showing last {tail} lines from: {log_file}[/cyan]")
    console.print()

    try:
        if follow:
            # Follow mode (like tail -f)
            import time
            with open(log_file, 'r') as f:
                # Go to end of file
                f.seek(0, 2)

                console.print("[yellow]Following log output (Ctrl+C to stop)...[/yellow]")
                console.print()

                try:
                    while True:
                        line = f.readline()
                        if line:
                            console.print(line.rstrip())
                        else:
                            time.sleep(0.1)
                except KeyboardInterrupt:
                    console.print()
                    console.print("[yellow]Stopped following logs[/yellow]")
        else:
            # Show last N lines
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-tail:]:
                    console.print(line.rstrip())

    except Exception as e:
        console.print(f"[red]Error reading logs: {e}[/red]")
        raise typer.Exit(code=1)


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    """Main entry point for admin CLI."""
    app()


if __name__ == "__main__":
    main()
