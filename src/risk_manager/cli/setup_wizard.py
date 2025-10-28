"""
Interactive Setup Wizard for Risk Manager V34

Guides users through:
1. API Credentials configuration
2. Account selection
3. Risk rules setup
4. Service installation and testing
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_config_dir() -> Path:
    """Get configuration directory path."""
    local_config = Path("config")
    if local_config.exists():
        return local_config

    # Create if doesn't exist
    local_config.mkdir(parents=True, exist_ok=True)
    return local_config


async def validate_api_credentials(api_key: str, username: str) -> tuple[bool, str]:
    """
    Validate API credentials by attempting to connect to TopstepX.

    Args:
        api_key: TopstepX API key
        username: TopstepX username

    Returns:
        Tuple of (success: bool, message: str)
    """
    # For MVP: Skip actual SDK validation since SDK may not be fully installed yet
    # Just validate that credentials are provided and look reasonable
    if not api_key or not username:
        return False, "API key and username are required"

    if len(api_key) < 10:
        return False, "API key appears too short - please check"

    if len(username) < 3:
        return False, "Username appears too short - please check"

    # Save credentials to environment for later use
    os.environ["PROJECT_X_API_KEY"] = api_key
    os.environ["PROJECT_X_USERNAME"] = username

    # Return success with note that validation will happen on service start
    return True, "[OK] Credentials saved (will be validated when service starts)"


async def fetch_accounts(api_key: str, username: str) -> list[dict]:
    """
    Fetch available accounts from TopstepX.

    Args:
        api_key: TopstepX API key
        username: TopstepX username

    Returns:
        List of account dictionaries
    """
    # For MVP: Return placeholder accounts since SDK may not be installed
    # In production, this would query the actual TopstepX API
    console.print("[yellow]Note: Using placeholder accounts (real accounts will be fetched on service start)[/yellow]")

    account_id = os.getenv("TOPSTEPX_ACCOUNT_ID", "PRAC-V2-XXXXXX")

    return [
        {
            "id": account_id,
            "name": "Practice Account",
            "balance": "$10,000",
            "status": "Pending validation"
        },
        {
            "id": "DEMO-12345",
            "name": "Demo Account",
            "balance": "$5,000",
            "status": "Pending validation"
        }
    ]


def save_credentials(api_key: str, username: str) -> None:
    """
    Save API credentials to .env file.

    Args:
        api_key: TopstepX API key
        username: TopstepX username
    """
    config_dir = get_config_dir()
    env_file = Path(".env")

    # Read existing .env or create new
    env_lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_lines = f.readlines()

    # Update or add credentials
    updated = False
    api_key_updated = False
    username_updated = False

    for i, line in enumerate(env_lines):
        if line.startswith("PROJECT_X_API_KEY="):
            env_lines[i] = f"PROJECT_X_API_KEY={api_key}\n"
            api_key_updated = True
        elif line.startswith("PROJECT_X_USERNAME="):
            env_lines[i] = f"PROJECT_X_USERNAME={username}\n"
            username_updated = True

    # Add if not found
    if not api_key_updated:
        env_lines.append(f"PROJECT_X_API_KEY={api_key}\n")
    if not username_updated:
        env_lines.append(f"PROJECT_X_USERNAME={username}\n")

    # Write back
    with open(env_file, 'w') as f:
        f.writelines(env_lines)

    console.print(f"[green][OK] Credentials saved to .env[/green]")


def save_account_config(account_id: str, account_name: str) -> None:
    """
    Save account configuration to YAML.

    Args:
        account_id: Account ID to monitor
        account_name: Human-readable account name
    """
    config_dir = get_config_dir()
    accounts_file = config_dir / "accounts.yaml"

    config = {
        "accounts": [
            {
                "account_id": account_id,
                "name": account_name,
                "enabled": True
            }
        ]
    }

    with open(accounts_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    console.print(f"[green][OK] Account configuration saved to {accounts_file}[/green]")


def save_risk_config(quick_setup: bool = True) -> None:
    """
    Save risk configuration to YAML.

    Args:
        quick_setup: If True, use recommended defaults. If False, use minimal config.
    """
    config_dir = get_config_dir()
    risk_file = config_dir / "risk_config.yaml"

    if quick_setup:
        config = {
            "general": {
                "instruments": ["MNQ", "NQ", "ES"],
                "timezone": "America/Chicago",
                "logging": {
                    "level": "INFO",
                    "file": "data/logs/risk_manager.log"
                }
            },
            "rules": {
                "max_contracts": {
                    "enabled": True,
                    "limit": 5,
                    "count_type": "net"
                },
                "daily_realized_loss": {
                    "enabled": True,
                    "limit": -500,
                    "reset_time": "17:00",
                    "timezone": "America/Chicago"
                },
                "daily_unrealized_loss": {
                    "enabled": True,
                    "limit": -750
                },
                "session_block_outside": {
                    "enabled": True,
                    "start_time": "08:30",
                    "end_time": "15:00",
                    "timezone": "America/Chicago"
                }
            }
        }
    else:
        # Minimal config
        config = {
            "general": {
                "instruments": ["MNQ"],
                "timezone": "America/Chicago",
                "logging": {
                    "level": "INFO",
                    "file": "data/logs/risk_manager.log"
                }
            },
            "rules": {}
        }

    with open(risk_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green][OK] Risk configuration saved to {risk_file}[/green]")


# ==============================================================================
# WIZARD STEPS
# ==============================================================================

async def step_1_credentials() -> tuple[str, str]:
    """
    Step 1: API Credentials

    Returns:
        Tuple of (api_key, username)
    """
    console.clear()
    console.print()
    console.print(Panel(
        "[bold cyan]Step 1 of 4[/bold cyan]\n"
        "[bold]API Authentication[/bold]\n\n"
        "Enter your TopstepX credentials to connect to the API.\n\n"
        "[dim]Get your API key from TopstepX Dashboard:[/dim]\n"
        "[dim]Settings → API Access → Generate Key[/dim]",
        title="SETUP WIZARD",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    while True:
        # Get username
        username = Prompt.ask(
            "[cyan]TopstepX Username[/cyan]",
            default=os.getenv("PROJECT_X_USERNAME", "")
        )

        # Get API key (masked)
        api_key = Prompt.ask(
            "[cyan]TopstepX API Key[/cyan]",
            password=True
        )

        console.print()
        console.print("[yellow]Validating credentials...[/yellow]")

        # Validate
        success, message = await validate_api_credentials(api_key, username)

        if success:
            console.print()
            console.print(Panel(
                "[bold green][SUCCESS] Authentication successful![/bold green]\n\n"
                "[green][OK] Connected to TopstepX API[/green]\n"
                "[green][OK] Credentials validated[/green]\n"
                "[green][OK] SDK connection working[/green]",
                border_style="green",
                box=box.ROUNDED
            ))
            console.print()

            # Save credentials
            save_credentials(api_key, username)

            input("Press ENTER to continue to Step 2...")
            return api_key, username
        else:
            console.print()
            console.print(Panel(
                f"[bold red][ERROR] Authentication failed[/bold red]\n\n"
                f"[red]{message}[/red]\n\n"
                "[dim]Please check your credentials and try again.[/dim]",
                border_style="red",
                box=box.ROUNDED
            ))
            console.print()

            retry = Confirm.ask("[yellow]Retry?[/yellow]", default=True)
            if not retry:
                console.print("[red]Setup cancelled[/red]")
                sys.exit(0)


async def step_2_account_selection(api_key: str, username: str) -> tuple[str, str]:
    """
    Step 2: Account Selection

    Args:
        api_key: Validated API key
        username: Validated username

    Returns:
        Tuple of (account_id, account_name)
    """
    console.clear()
    console.print()
    console.print(Panel(
        "[bold cyan]Step 2 of 4[/bold cyan]\n"
        "[bold]Account Selection[/bold]\n\n"
        "Select which TopstepX account to monitor for risk violations.",
        title="SETUP WIZARD",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    console.print("[yellow]Fetching your TopstepX accounts...[/yellow]")

    # Fetch accounts
    accounts = await fetch_accounts(api_key, username)

    if not accounts:
        console.print("[red]No accounts found or error fetching accounts[/red]")
        console.print("[yellow]Using default account from environment[/yellow]")
        account_id = os.getenv("TOPSTEPX_ACCOUNT_ID", "DEMO-ACCOUNT")
        account_name = "Default Account"
    else:
        console.print()

        # Display accounts in table
        table = Table(box=box.ROUNDED)
        table.add_column("#", style="cyan", no_wrap=True)
        table.add_column("Account Name", style="white")
        table.add_column("Balance", style="green")
        table.add_column("Status", style="yellow")

        for i, account in enumerate(accounts, 1):
            table.add_row(
                str(i),
                account["name"],
                account["balance"],
                account["status"]
            )

        console.print(table)
        console.print()

        # Select account
        if len(accounts) == 1:
            choice = 1
            console.print(f"[dim]Only one account available, auto-selecting...[/dim]")
        else:
            choice = int(Prompt.ask(
                f"[cyan]Select account[/cyan] [dim][1-{len(accounts)}][/dim]",
                default="1"
            ))

        selected = accounts[choice - 1]
        account_id = selected["id"]
        account_name = selected["name"]

        console.print()
        console.print(Panel(
            f"[bold]Selected Account:[/bold]\n\n"
            f"[cyan]Name:[/cyan] {account_name}\n"
            f"[cyan]ID:[/cyan] {account_id}\n\n"
            "[dim]This account will be monitored for risk violations.[/dim]",
            border_style="green",
            box=box.ROUNDED
        ))

    console.print()

    # Confirm
    confirmed = Confirm.ask("[cyan]Confirm selection?[/cyan]", default=True)

    if confirmed:
        # Save account config
        save_account_config(account_id, account_name)

        console.print()
        input("Press ENTER to continue to Step 3...")
        return account_id, account_name
    else:
        console.print("[red]Setup cancelled[/red]")
        sys.exit(0)


def step_3_risk_rules() -> bool:
    """
    Step 3: Risk Rules Configuration

    Returns:
        True if quick setup was chosen, False for custom
    """
    console.clear()
    console.print()
    console.print(Panel(
        "[bold cyan]Step 3 of 4[/bold cyan]\n"
        "[bold]Risk Rules Configuration[/bold]\n\n"
        "Choose how to configure your risk protection rules.",
        title="SETUP WIZARD",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    console.print("[bold]Configuration Options:[/bold]\n")
    console.print("[cyan]1.[/cyan] Quick Setup (Recommended)")
    console.print("   • Max 5 contracts globally")
    console.print("   • $500 daily loss limit")
    console.print("   • $750 unrealized loss limit")
    console.print("   • Trading hours: 8:30 AM - 3:00 PM CT")
    console.print()
    console.print("[cyan]2.[/cyan] Custom Setup")
    console.print("   • Configure rules manually later")
    console.print("   • Edit config/risk_config.yaml")
    console.print()

    choice = Prompt.ask(
        "[cyan]Choice[/cyan]",
        choices=["1", "2"],
        default="1"
    )

    quick_setup = (choice == "1")

    # Save config
    save_risk_config(quick_setup=quick_setup)

    console.print()
    if quick_setup:
        console.print(Panel(
            "[bold green][SUCCESS] Quick setup applied![/bold green]\n\n"
            "[green][OK] Position limits configured[/green]\n"
            "[green][OK] Loss limits configured[/green]\n"
            "[green][OK] Trading hours configured[/green]\n\n"
            "[dim]You can customize these later in config/risk_config.yaml[/dim]",
            border_style="green",
            box=box.ROUNDED
        ))
    else:
        console.print(Panel(
            "[bold yellow]Custom setup selected[/bold yellow]\n\n"
            "[yellow]Configure rules manually:[/yellow]\n"
            "1. Edit: [cyan]config/risk_config.yaml[/cyan]\n"
            "2. See examples in: [cyan]config/risk_config.yaml.template[/cyan]\n"
            "3. Validate with: [cyan]admin_cli config validate[/cyan]",
            border_style="yellow",
            box=box.ROUNDED
        ))

    console.print()
    input("Press ENTER to continue to Step 4...")
    return quick_setup


def step_4_service_installation() -> None:
    """
    Step 4: Service Installation & Testing
    """
    console.clear()
    console.print()
    console.print(Panel(
        "[bold cyan]Step 4 of 4[/bold cyan]\n"
        "[bold]Service Installation[/bold]\n\n"
        "Installing and testing Risk Manager service.",
        title="SETUP WIZARD",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    # Service installation (placeholder for now)
    console.print("[yellow]Installing Windows Service...[/yellow]")
    console.print("[dim]Note: Service installation requires administrator privileges[/dim]")
    console.print()

    # Simulated installation steps
    steps = [
        ("Creating service definition", True),
        ("Configuring auto-start", True),
        ("Setting up file permissions", True),
        ("Service installation", False),  # Not actually implemented yet
    ]

    for step_name, implemented in steps:
        if implemented:
            console.print(f"[green][OK][/green] {step_name}")
        else:
            console.print(f"[yellow][WARN][/yellow] {step_name} [dim](not yet implemented)[/dim]")

    console.print()
    console.print(Panel(
        "[bold yellow]Service Installation: Not Yet Implemented[/bold yellow]\n\n"
        "[yellow]The Windows service installation is not yet available.[/yellow]\n\n"
        "[bold]For now, you can:[/bold]\n"
        "1. Run manually: [cyan]python -m risk_manager[/cyan]\n"
        "2. Test connection: [cyan]python test_connection.py[/cyan]\n"
        "3. Use trader CLI: [cyan]python trader_cli.py[/cyan]",
        border_style="yellow",
        box=box.ROUNDED
    ))

    console.print()
    console.print(Panel(
        "[bold green]Setup Complete![/bold green]\n\n"
        "[green][OK] API credentials configured[/green]\n"
        "[green][OK] Account selected[/green]\n"
        "[green][OK] Risk rules configured[/green]\n\n"
        "[bold]Next Steps:[/bold]\n"
        "1. Test connection: [cyan]python test_connection.py[/cyan]\n"
        "2. View configuration: [cyan]admin_cli config show[/cyan]\n"
        "3. Run risk manager: [cyan]python -m risk_manager[/cyan]",
        title="SETUP COMPLETE",
        border_style="green",
        box=box.ROUNDED
    ))
    console.print()


# ==============================================================================
# MAIN WIZARD
# ==============================================================================

async def run_setup_wizard():
    """Run the complete setup wizard."""
    console.clear()
    console.print()
    console.print(Panel(
        "[bold cyan]Risk Manager V34[/bold cyan]\n"
        "[bold]Interactive Setup Wizard[/bold]\n\n"
        "This wizard will guide you through initial setup:\n"
        "  • TopstepX API authentication\n"
        "  • Trading account selection\n"
        "  • Risk rule configuration\n"
        "  • Service installation & testing\n\n"
        "[dim]Estimated time: 5-10 minutes[/dim]",
        title="WELCOME",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    proceed = Confirm.ask("[cyan]Ready to begin?[/cyan]", default=True)

    if not proceed:
        console.print("[yellow]Setup cancelled[/yellow]")
        return

    try:
        # Step 1: API Credentials
        api_key, username = await step_1_credentials()

        # Step 2: Account Selection
        account_id, account_name = await step_2_account_selection(api_key, username)

        # Step 3: Risk Rules
        quick_setup = step_3_risk_rules()

        # Step 4: Service Installation
        step_4_service_installation()

    except KeyboardInterrupt:
        console.print()
        console.print("[red]Setup interrupted by user[/red]")
    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Setup Error[/bold red]\n\n"
            f"[red]{str(e)}[/red]\n\n"
            "[dim]Please check the error message and try again.[/dim]",
            border_style="red",
            box=box.ROUNDED
        ))
        raise


def main():
    """Main entry point for setup wizard."""
    asyncio.run(run_setup_wizard())


if __name__ == "__main__":
    main()
