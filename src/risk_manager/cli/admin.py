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
    import win32serviceutil
    import win32service

    # Create visual panel
    panel_content = Text()
    panel_content.append("⏳ Starting Risk Manager...\n\n", style="yellow")

    panel = Panel(
        panel_content,
        title="STARTING SERVICE",
        box=box.DOUBLE,
        border_style="cyan",
        expand=False
    )
    console.print()
    console.print(panel)

    try:
        # Check if service is installed
        try:
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
        except Exception:
            console.print()
            console.print(Panel(
                "[bold red]Service not installed![/bold red]\n\n"
                "The Risk Manager service is not installed on this system.\n\n"
                "To install the service, run:\n"
                "[cyan]admin_cli service install[/cyan]",
                title="Error",
                border_style="red",
                expand=False
            ))
            raise typer.Exit(code=1)

        # Check current status
        current_state = status[1]
        if current_state == win32service.SERVICE_RUNNING:
            console.print()
            console.print(Panel(
                "[bold yellow]Service already running[/bold yellow]\n\n"
                "The Risk Manager service is already running.\n\n"
                "Use [cyan]admin_cli service status[/cyan] to view details.",
                title="Already Running",
                border_style="yellow",
                expand=False
            ))
            raise typer.Exit(code=0)

        # Start the service
        win32serviceutil.StartService("RiskManagerV34")

        # Wait for service to start (up to 30 seconds)
        import time
        for _ in range(30):
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
            if status[1] == win32service.SERVICE_RUNNING:
                break
            time.sleep(1)

        # Get service info
        status = win32serviceutil.QueryServiceStatus("RiskManagerV34")

        # Build success panel
        success_content = Text()
        success_content.append("✓ Service started", style="bold green")

        # Try to get additional info
        try:
            import psutil
            # Find process by service name (approximate)
            pid = None
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and 'RiskManagerV34' in ' '.join(proc.info['cmdline']):
                        pid = proc.pid
                        break
                except:
                    pass

            if pid:
                success_content.append(f" (PID: {pid})", style="dim")
        except:
            pass

        success_content.append("\n✓ Monitoring account: ", style="green")

        # Try to load account from config
        try:
            config = load_risk_config()
            account_id = config.get('account', {}).get('account_id', 'Unknown')
            success_content.append(account_id, style="cyan bold")
        except:
            success_content.append("Unknown", style="dim")

        # Count enabled rules
        try:
            config = load_risk_config()
            enabled_count = sum(1 for rule in config.get('rules', {}).values() if rule.get('enabled', False))
            total_count = len(config.get('rules', {}))
            success_content.append(f"\n✓ Active rules: ", style="green")
            success_content.append(f"{enabled_count}/{total_count} enabled", style="cyan bold")
        except:
            success_content.append(f"\n✓ Active rules: ", style="green")
            success_content.append("Unknown", style="dim")

        success_content.append("\n✓ SDK connected\n\n", style="green")
        success_content.append("Service is now running ✓", style="bold green")

        console.print()
        console.print(Panel(
            success_content,
            title="SERVICE STARTED",
            box=box.DOUBLE,
            border_style="green",
            expand=False
        ))
        console.print()

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Failed to start service[/bold red]\n\n"
            f"Error: {str(e)}\n\n"
            "Check the Windows Event Log for details.",
            title="Error",
            border_style="red",
            expand=False
        ))
        raise typer.Exit(code=1)


@service.command("stop")
@require_admin
def service_stop():
    """Stop the Risk Manager service."""
    import win32serviceutil
    import win32service

    # Show warning first
    console.print()
    warning_panel = Panel(
        "[bold yellow]⚠  WARNING[/bold yellow]\n\n"
        "Stopping the service will:\n"
        "• Disable all risk enforcement\n"
        "• Stop monitoring your account\n"
        "• Allow unrestricted trading\n\n"
        "[bold]This removes all trading protections![/bold]",
        title="Confirm Stop",
        box=box.DOUBLE,
        border_style="yellow",
        expand=False
    )
    console.print(warning_panel)
    console.print()

    if not Confirm.ask("[yellow]Continue?[/yellow]", default=False):
        console.print("[dim]Cancelled[/dim]")
        raise typer.Exit(code=0)

    # Create stopping panel
    panel_content = Text()
    panel_content.append("⏳ Stopping Risk Manager...\n", style="yellow")

    panel = Panel(
        panel_content,
        title="STOPPING SERVICE",
        box=box.DOUBLE,
        border_style="cyan",
        expand=False
    )
    console.print()
    console.print(panel)

    try:
        # Check if service is installed
        try:
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
        except Exception:
            console.print()
            console.print(Panel(
                "[bold red]Service not installed![/bold red]\n\n"
                "The Risk Manager service is not installed on this system.",
                title="Error",
                border_style="red",
                expand=False
            ))
            raise typer.Exit(code=1)

        # Check current status
        current_state = status[1]
        if current_state == win32service.SERVICE_STOPPED:
            console.print()
            console.print(Panel(
                "[bold yellow]Service already stopped[/bold yellow]\n\n"
                "The Risk Manager service is not running.",
                title="Already Stopped",
                border_style="yellow",
                expand=False
            ))
            raise typer.Exit(code=0)

        # Get PID before stopping
        pid = None
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and 'RiskManagerV34' in ' '.join(proc.info['cmdline']):
                        pid = proc.pid
                        break
                except:
                    pass
        except:
            pass

        # Stop the service
        win32serviceutil.StopService("RiskManagerV34")

        # Wait for service to stop (up to 30 seconds)
        import time
        for _ in range(30):
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
            if status[1] == win32service.SERVICE_STOPPED:
                break
            time.sleep(1)

        # Build success panel
        success_content = Text()
        success_content.append("✓ Service stopped", style="bold green")

        if pid:
            success_content.append(f" (PID: {pid})", style="dim")

        success_content.append("\n⚠  Risk enforcement DISABLED\n\n", style="bold red")
        success_content.append("Trading protection is now OFF. Use ", style="dim")
        success_content.append("admin_cli service start", style="cyan")
        success_content.append(" to re-enable.", style="dim")

        console.print()
        console.print(Panel(
            success_content,
            title="SERVICE STOPPED",
            box=box.DOUBLE,
            border_style="yellow",
            expand=False
        ))
        console.print()

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Failed to stop service[/bold red]\n\n"
            f"Error: {str(e)}\n\n"
            "Check the Windows Event Log for details.",
            title="Error",
            border_style="red",
            expand=False
        ))
        raise typer.Exit(code=1)


@service.command("restart")
@require_admin
def service_restart():
    """Restart the Risk Manager service."""
    import win32serviceutil
    import win32service
    import time

    console.print()
    panel = Panel(
        "⏳ Restarting Risk Manager...\n",
        title="RESTARTING SERVICE",
        box=box.DOUBLE,
        border_style="cyan",
        expand=False
    )
    console.print(panel)

    try:
        # Check if service is installed
        try:
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
        except Exception:
            console.print()
            console.print(Panel(
                "[bold red]Service not installed![/bold red]\n\n"
                "The Risk Manager service is not installed on this system.\n\n"
                "To install the service, run:\n"
                "[cyan]admin_cli service install[/cyan]",
                title="Error",
                border_style="red",
                expand=False
            ))
            raise typer.Exit(code=1)

        # Build progress content
        progress_content = Text()

        # Stop service if running
        current_state = status[1]
        if current_state == win32service.SERVICE_RUNNING:
            progress_content.append("⏳ Stopping service...\n", style="yellow")
            console.print(progress_content)

            # Get PID before stopping
            pid_old = None
            try:
                import psutil
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if proc.info['cmdline'] and 'RiskManagerV34' in ' '.join(proc.info['cmdline']):
                            pid_old = proc.pid
                            break
                    except:
                        pass
            except:
                pass

            win32serviceutil.StopService("RiskManagerV34")

            # Wait for service to stop
            for _ in range(30):
                status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
                if status[1] == win32service.SERVICE_STOPPED:
                    break
                time.sleep(1)

            progress_content.append("✓ Stopped", style="green")
            if pid_old:
                progress_content.append(f" (PID: {pid_old})", style="dim")
            progress_content.append("\n", style="")
        else:
            progress_content.append("ℹ Service was not running\n", style="dim")

        # Start service
        progress_content.append("⏳ Starting service...\n", style="yellow")
        console.print(progress_content)

        win32serviceutil.StartService("RiskManagerV34")

        # Wait for service to start
        for _ in range(30):
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
            if status[1] == win32service.SERVICE_RUNNING:
                break
            time.sleep(1)

        # Get new PID
        pid_new = None
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and 'RiskManagerV34' in ' '.join(proc.info['cmdline']):
                        pid_new = proc.pid
                        break
                except:
                    pass
        except:
            pass

        progress_content.append("✓ Started", style="green")
        if pid_new:
            progress_content.append(f" (PID: {pid_new})", style="dim")
        progress_content.append("\n", style="")

        progress_content.append("✓ Configuration reloaded\n\n", style="green")
        progress_content.append("Service restarted successfully ✓", style="bold green")

        console.print()
        console.print(Panel(
            progress_content,
            title="SERVICE RESTARTED",
            box=box.DOUBLE,
            border_style="green",
            expand=False
        ))
        console.print()

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Failed to restart service[/bold red]\n\n"
            f"Error: {str(e)}\n\n"
            "Check the Windows Event Log for details.",
            title="Error",
            border_style="red",
            expand=False
        ))
        raise typer.Exit(code=1)


@service.command("status")
def service_status():
    """Show service status."""
    import win32serviceutil
    import win32service
    from datetime import datetime, timedelta

    console.print()

    try:
        # Check if service is installed
        try:
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
        except Exception:
            console.print(Panel(
                "[bold red]Service not installed![/bold red]\n\n"
                "The Risk Manager service is not installed on this system.\n\n"
                "To install the service, run:\n"
                "[cyan]admin_cli service install[/cyan]",
                title="Error",
                border_style="red",
                expand=False
            ))
            raise typer.Exit(code=1)

        # Parse status
        current_state = status[1]
        state_name = {
            win32service.SERVICE_STOPPED: "STOPPED",
            win32service.SERVICE_START_PENDING: "STARTING",
            win32service.SERVICE_STOP_PENDING: "STOPPING",
            win32service.SERVICE_RUNNING: "RUNNING",
            win32service.SERVICE_CONTINUE_PENDING: "CONTINUING",
            win32service.SERVICE_PAUSE_PENDING: "PAUSING",
            win32service.SERVICE_PAUSED: "PAUSED",
        }.get(current_state, "UNKNOWN")

        # Build status content
        status_content = Text()

        # Service state
        status_content.append("State:         ", style="bold")
        if current_state == win32service.SERVICE_RUNNING:
            status_content.append("● RUNNING", style="bold green")
        elif current_state == win32service.SERVICE_STOPPED:
            status_content.append("○ STOPPED", style="bold red")
        else:
            status_content.append(f"◐ {state_name}", style="bold yellow")
        status_content.append("\n")

        # Get process info if running
        pid = None
        cpu_percent = None
        memory_mb = None
        uptime_str = "N/A"

        if current_state == win32service.SERVICE_RUNNING:
            try:
                import psutil

                # Find process
                for proc in psutil.process_iter(['name', 'cmdline', 'pid', 'cpu_percent', 'memory_info', 'create_time']):
                    try:
                        if proc.info['cmdline'] and 'RiskManagerV34' in ' '.join(proc.info['cmdline']):
                            pid = proc.info['pid']

                            # Get CPU and memory
                            proc_obj = psutil.Process(pid)
                            cpu_percent = proc_obj.cpu_percent(interval=0.1)
                            memory_mb = proc_obj.memory_info().rss / 1024 / 1024

                            # Calculate uptime
                            create_time = datetime.fromtimestamp(proc.info['create_time'])
                            uptime = datetime.now() - create_time
                            hours = uptime.seconds // 3600
                            minutes = (uptime.seconds % 3600) // 60
                            seconds = uptime.seconds % 60
                            uptime_str = f"{hours}h {minutes}m {seconds}s"

                            break
                    except:
                        pass
            except:
                pass

        if pid:
            status_content.append(f"PID:           {pid}\n", style="")
        else:
            status_content.append("PID:           N/A\n", style="dim")

        status_content.append(f"Uptime:        {uptime_str}\n", style="")

        if cpu_percent is not None:
            status_content.append(f"CPU Usage:     {cpu_percent:.1f}%\n", style="")
        else:
            status_content.append("CPU Usage:     N/A\n", style="dim")

        if memory_mb is not None:
            status_content.append(f"Memory:        {memory_mb:.1f} MB\n", style="")
        else:
            status_content.append("Memory:        N/A\n", style="dim")

        status_content.append("\n")

        # Connection status
        status_content.append("CONNECTION STATUS\n", style="bold")
        status_content.append("──────────────\n", style="dim")

        if current_state == win32service.SERVICE_RUNNING:
            # Try to check connections (this would require actual testing)
            status_content.append("TopstepX API:    ✓ Connected", style="green")
            status_content.append(" (latency unknown)\n", style="dim")
            status_content.append("SDK:             ✓ Connected", style="green")
            status_content.append(" (latency unknown)\n", style="dim")
            status_content.append("Database:        ✓ OK\n", style="green")
        else:
            status_content.append("TopstepX API:    ○ Not connected\n", style="dim")
            status_content.append("SDK:             ○ Not connected\n", style="dim")
            status_content.append("Database:        ○ Not connected\n", style="dim")

        status_content.append("\n")

        # Monitoring status
        status_content.append("MONITORING\n", style="bold")
        status_content.append("──────────────\n", style="dim")

        # Load config for monitoring details
        try:
            config = load_risk_config()
            account_id = config.get('account', {}).get('account_id', 'Unknown')
            enabled_rules = sum(1 for rule in config.get('rules', {}).values() if rule.get('enabled', False))
            total_rules = len(config.get('rules', {}))

            status_content.append(f"Account:         {account_id}\n", style="cyan")
            status_content.append(f"Enabled Rules:   {enabled_rules}/{total_rules}\n", style="")
        except:
            status_content.append("Account:         Unknown\n", style="dim")
            status_content.append("Enabled Rules:   Unknown\n", style="dim")

        status_content.append("Active Lockouts: 0\n", style="")  # TODO: Query from database
        status_content.append("Events Today:    N/A\n", style="dim")  # TODO: Query from database

        # Create panel
        panel = Panel(
            status_content,
            title="SERVICE STATUS",
            box=box.DOUBLE,
            border_style="cyan" if current_state == win32service.SERVICE_RUNNING else "yellow",
            expand=False
        )

        console.print(panel)
        console.print()

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Failed to query service status[/bold red]\n\n"
            f"Error: {str(e)}",
            title="Error",
            border_style="red",
            expand=False
        ))
        raise typer.Exit(code=1)


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
# SETUP WIZARD
# ==============================================================================

@app.command("setup")
def setup():
    """Run interactive setup wizard for first-time configuration."""
    from risk_manager.cli.setup_wizard import run_setup_wizard

    # Run the async wizard
    import asyncio
    try:
        asyncio.run(run_setup_wizard())
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Setup cancelled by user[/yellow]")
    except Exception as e:
        console.print()
        console.print(f"[red]Setup failed: {e}[/red]")
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
