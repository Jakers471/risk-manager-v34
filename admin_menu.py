#!/usr/bin/env python3
"""
Risk Manager V34 - Interactive Admin Menu
Menu-based interface for administration tasks
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_screen():
    """Clear terminal screen"""
    console.clear()


def show_header():
    """Show main header"""
    console.print()
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold cyan]        RISK MANAGER V34 - ADMIN CONTROL PANEL[/bold cyan]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print()


def pause():
    """Wait for user to press enter"""
    console.print()
    Prompt.ask("[dim]Press ENTER to continue[/dim]", default="")


# ============================================================================
# MENU SCREENS
# ============================================================================

def show_main_menu() -> str:
    """Show main menu and get user choice"""
    clear_screen()
    show_header()

    # Create menu table
    table = Table(box=box.ROUNDED, show_header=False, border_style="cyan")
    table.add_column("Option", style="cyan bold", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("1", "Run Setup Wizard")
    table.add_row("2", "Service Control")
    table.add_row("3", "Configure Rules")
    table.add_row("4", "View Configuration")
    table.add_row("5", "Test Connection")
    table.add_row("6", "Dashboard")
    table.add_row("", "")
    table.add_row("0", "[red]Exit[/red]")

    console.print(table)
    console.print()

    choice = Prompt.ask("[cyan]Enter choice[/cyan]", default="0")
    return choice


def screen_setup_wizard():
    """Run setup wizard"""
    clear_screen()
    show_header()

    console.print(Panel(
        "[bold]Setup Wizard[/bold]\n\n"
        "This will guide you through:\n"
        "  1. API Authentication\n"
        "  2. Account Selection\n"
        "  3. Risk Rules Configuration\n"
        "  4. Service Installation",
        title="Setup",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    proceed = Prompt.ask("[cyan]Start setup wizard?[/cyan] [dim](y/n)[/dim]", default="y")

    if proceed.lower() == 'y':
        # Run the actual setup wizard
        from risk_manager.cli.setup_wizard import run_setup_wizard
        import asyncio
        try:
            asyncio.run(run_setup_wizard())
        except KeyboardInterrupt:
            console.print()
            console.print("[yellow]Setup cancelled by user[/yellow]")
        except Exception as e:
            console.print()
            console.print(f"[red]Setup failed: {e}[/red]")

    pause()


def screen_service_control():
    """Service control menu"""
    clear_screen()
    show_header()

    # Check service status first
    try:
        import win32serviceutil
        import win32service

        try:
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
            current_state = status[1]

            if current_state == win32service.SERVICE_RUNNING:
                status_text = "[bold green]RUNNING[/bold green]"
            elif current_state == win32service.SERVICE_STOPPED:
                status_text = "[bold red]STOPPED[/bold red]"
            else:
                status_text = "[bold yellow]TRANSITIONING[/bold yellow]"
        except:
            status_text = "[dim]Not Installed[/dim]"
    except ImportError:
        status_text = "[dim]N/A (not on Windows)[/dim]"

    console.print(Panel(
        f"[bold]Current Status:[/bold] {status_text}",
        title="Service Status",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    # Service control menu
    table = Table(box=box.ROUNDED, show_header=False, border_style="cyan")
    table.add_column("Option", style="cyan bold", no_wrap=True)
    table.add_column("Action", style="white")

    table.add_row("1", "View Detailed Status")
    table.add_row("2", "[green]Start Service[/green]")
    table.add_row("3", "[red]Stop Service[/red]")
    table.add_row("4", "[yellow]Restart Service[/yellow]")
    table.add_row("", "")
    table.add_row("0", "Back to Main Menu")

    console.print(table)
    console.print()

    choice = Prompt.ask("[cyan]Enter choice[/cyan]", default="0")

    if choice == "1":
        # Show detailed status
        from risk_manager.cli.admin import service_status
        try:
            service_status()
        except:
            console.print("[red]Error getting service status[/red]")
        pause()
    elif choice == "2":
        # Start service
        from risk_manager.cli.admin import service_start
        try:
            service_start()
        except:
            console.print("[red]Failed to start service[/red]")
        pause()
    elif choice == "3":
        # Stop service
        from risk_manager.cli.admin import service_stop
        try:
            service_stop()
        except:
            console.print("[red]Failed to stop service[/red]")
        pause()
    elif choice == "4":
        # Restart service
        from risk_manager.cli.admin import service_restart
        try:
            service_restart()
        except:
            console.print("[red]Failed to restart service[/red]")
        pause()


def screen_configure_rules():
    """Configure risk rules"""
    clear_screen()
    show_header()

    console.print(Panel(
        "[bold]Risk Rules Configuration[/bold]\n\n"
        "Manage the 13 risk protection rules.",
        title="Rules",
        border_style="yellow",
        box=box.ROUNDED
    ))
    console.print()

    # Rules menu
    table = Table(box=box.ROUNDED, show_header=False, border_style="yellow")
    table.add_column("Option", style="cyan bold", no_wrap=True)
    table.add_column("Action", style="white")

    table.add_row("1", "List All Rules")
    table.add_row("2", "Enable Rule")
    table.add_row("3", "Disable Rule")
    table.add_row("4", "Edit Configuration File")
    table.add_row("5", "Validate Configuration")
    table.add_row("", "")
    table.add_row("0", "Back to Main Menu")

    console.print(table)
    console.print()

    choice = Prompt.ask("[cyan]Enter choice[/cyan]", default="0")

    if choice == "1":
        # List rules
        from risk_manager.cli.admin import rules_list
        try:
            rules_list()
        except:
            console.print("[red]Error loading rules[/red]")
        pause()
    elif choice == "2":
        # Enable rule
        rule_id = Prompt.ask("[cyan]Enter rule ID to enable[/cyan]")
        from risk_manager.cli.admin import rules_enable
        try:
            rules_enable(rule_id)
        except:
            console.print(f"[red]Error enabling rule: {rule_id}[/red]")
        pause()
    elif choice == "3":
        # Disable rule
        rule_id = Prompt.ask("[cyan]Enter rule ID to disable[/cyan]")
        from risk_manager.cli.admin import rules_disable
        try:
            rules_disable(rule_id)
        except:
            console.print(f"[red]Error disabling rule: {rule_id}[/red]")
        pause()
    elif choice == "4":
        # Edit config
        from risk_manager.cli.admin import config_edit
        try:
            config_edit()
            console.print("[green]Configuration file opened[/green]")
        except:
            console.print("[red]Error opening config file[/red]")
        pause()
    elif choice == "5":
        # Validate config
        from risk_manager.cli.admin import config_validate
        try:
            config_validate()
        except:
            console.print("[red]Configuration validation failed[/red]")
        pause()


def screen_view_config():
    """View current configuration"""
    clear_screen()
    show_header()

    console.print(Panel(
        "[bold]Current Configuration[/bold]",
        title="Configuration",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    from risk_manager.cli.admin import config_show
    try:
        config_show()
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")

    pause()


def screen_test_connection():
    """Test API connection"""
    clear_screen()
    show_header()

    console.print(Panel(
        "[bold]Connection Test[/bold]\n\n"
        "Testing connections to:\n"
        "  - TopstepX API\n"
        "  - Configuration files\n"
        "  - Database",
        title="Testing",
        border_style="magenta",
        box=box.ROUNDED
    ))
    console.print()

    # Basic tests
    tests = [
        ("Configuration files", check_config_files),
        ("Database access", check_database),
        ("Environment variables", check_env_vars),
    ]

    for test_name, test_func in tests:
        console.print(f"[cyan]Testing {test_name}...[/cyan]", end=" ")
        try:
            result = test_func()
            if result:
                console.print("[green]OK[/green]")
            else:
                console.print("[yellow]WARNING[/yellow]")
        except Exception as e:
            console.print(f"[red]FAILED: {e}[/red]")

    console.print()
    console.print("[dim]Note: Full API connection test requires service to be running[/dim]")

    pause()


def screen_dashboard():
    """Show dashboard with metrics"""
    clear_screen()
    show_header()

    console.print(Panel(
        "[bold]System Dashboard[/bold]\n\n"
        "[dim]Real-time metrics require service to be running[/dim]",
        title="Dashboard",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    # Service Status
    try:
        import win32serviceutil
        import win32service

        status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
        current_state = status[1]

        if current_state == win32service.SERVICE_RUNNING:
            service_status = "[green]RUNNING[/green]"
        elif current_state == win32service.SERVICE_STOPPED:
            service_status = "[red]STOPPED[/red]"
        else:
            service_status = "[yellow]TRANSITIONING[/yellow]"
    except:
        service_status = "[dim]Not Available[/dim]"

    # Configuration Status
    try:
        from risk_manager.cli.admin import load_risk_config
        config = load_risk_config()
        enabled_rules = sum(1 for rule in config['rules'].values() if rule.get('enabled', False))
        total_rules = len(config['rules'])
        config_status = f"[green]{enabled_rules}/{total_rules} rules enabled[/green]"
    except:
        config_status = "[red]Configuration error[/red]"

    # Display metrics
    table = Table(box=box.ROUNDED, show_header=False, border_style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Service Status", service_status)
    table.add_row("Risk Rules", config_status)
    table.add_row("Active Lockouts", "[dim]N/A[/dim]")
    table.add_row("Monitored Accounts", "[dim]N/A[/dim]")

    console.print(table)
    console.print()

    console.print("[dim]Note: Full metrics require service to be running and database access[/dim]")

    pause()


# ============================================================================
# TEST HELPER FUNCTIONS
# ============================================================================

def check_config_files() -> bool:
    """Check if config files exist"""
    config_dir = Path("config")
    return config_dir.exists() and (config_dir / "risk_config.yaml").exists()


def check_database() -> bool:
    """Check if database exists"""
    data_dir = Path("data")
    return data_dir.exists()


def check_env_vars() -> bool:
    """Check if environment variables are set"""
    return os.getenv("PROJECT_X_API_KEY") is not None


# ============================================================================
# MAIN APPLICATION LOOP
# ============================================================================

def main():
    """Main application loop"""
    while True:
        choice = show_main_menu()

        if choice == '0':
            clear_screen()
            console.print()
            console.print("[bold green]Thank you for using Risk Manager V34![/bold green]")
            console.print()
            sys.exit(0)
        elif choice == '1':
            screen_setup_wizard()
        elif choice == '2':
            screen_service_control()
        elif choice == '3':
            screen_configure_rules()
        elif choice == '4':
            screen_view_config()
        elif choice == '5':
            screen_test_connection()
        elif choice == '6':
            screen_dashboard()
        else:
            console.print()
            console.print("[red]Invalid choice. Please try again.[/red]")
            import time
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        console.print()
        console.print("[yellow]Admin menu closed by user[/yellow]")
        console.print()
        sys.exit(0)
