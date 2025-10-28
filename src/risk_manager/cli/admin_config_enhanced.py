"""
Enhanced configuration commands for Admin CLI

This module adds the interactive rule configuration editor commands.
Import these and add to the main admin.py config_group.
"""

import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

# Import config editor functions
from risk_manager.cli.config_editor import (
    display_config_table,
    show_rule_editor,
    is_dangerous_to_disable,
    confirm_dangerous_disable,
    validate_config,
    RULE_METADATA
)


def get_config_dir() -> Path:
    """Get configuration directory path."""
    import platform
    # Check for config in current directory first, then ProgramData
    local_config = Path("config")
    if local_config.exists():
        return local_config

    # Windows: C:\ProgramData\SimpleRiskManager\config
    if platform.system() == "Windows":
        return Path("C:/ProgramData/SimpleRiskManager/config")

    # Linux/Mac: /etc/risk-manager
    return Path("/etc/risk-manager")


def load_risk_config() -> dict:
    """Load risk configuration from YAML file."""
    import yaml
    config_file = get_config_dir() / "risk_config.yaml"

    if not config_file.exists():
        console.print(f"[red]Configuration file not found: {config_file}[/red]")
        raise typer.Exit(code=1)

    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def save_risk_config(config: dict) -> None:
    """Save risk configuration to YAML file."""
    import yaml
    config_file = get_config_dir() / "risk_config.yaml"

    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Configuration saved: {config_file}[/green]")


# ==================== Enhanced Config Commands ====================

def cmd_config_view():
    """Display current risk configuration in visual table format."""
    console.print("[cyan]Loading risk configuration...[/cyan]")

    try:
        config = load_risk_config()
        display_config_table(config)

    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        raise typer.Exit(code=1)


def cmd_config_edit(rule: str):
    """Edit specific rule configuration interactively."""
    console.print(f"[cyan]Loading rule configuration: {rule}...[/cyan]")

    try:
        config = load_risk_config()
        config_file = get_config_dir() / "risk_config.yaml"

        # Validate rule exists
        if rule not in config['rules']:
            console.print(f"[red]Rule not found: {rule}[/red]")
            console.print()
            console.print("[bold]Available rules:[/bold]")
            for rule_key in config['rules'].keys():
                metadata = RULE_METADATA.get(rule_key, {})
                rule_name = metadata.get('name', rule_key)
                console.print(f"  • {rule_key} - {rule_name}")
            raise typer.Exit(code=1)

        # Show interactive editor
        show_rule_editor(rule, config, config_file)

    except Exception as e:
        console.print(f"[red]Error editing rule: {e}[/red]")
        raise typer.Exit(code=1)


def cmd_config_enable(rule: str):
    """Enable a risk rule."""
    console.print(f"[cyan]Enabling rule: {rule}...[/cyan]")

    try:
        config = load_risk_config()

        # Validate rule exists
        if rule not in config['rules']:
            console.print(f"[red]Rule not found: {rule}[/red]")
            console.print("[dim]Use 'admin_cli config view' to see available rules[/dim]")
            raise typer.Exit(code=1)

        # Enable the rule
        config['rules'][rule]['enabled'] = True
        save_risk_config(config)

        # Get rule name
        metadata = RULE_METADATA.get(rule, {})
        rule_name = metadata.get('name', rule)

        console.print()
        console.print(Panel(
            f"[bold green]Rule enabled[/bold green]\n\n"
            f"Rule: [cyan]{rule_name}[/cyan]\n"
            f"Status: [green]Enabled[/green]\n\n"
            f"[dim]Remember to reload configuration:[/dim]\n"
            f"[cyan]admin_cli config reload[/cyan]",
            title="Rule Enabled",
            box=box.ROUNDED,
            border_style="green",
            expand=False
        ))
        console.print()

    except Exception as e:
        console.print(f"[red]Error enabling rule: {e}[/red]")
        raise typer.Exit(code=1)


def cmd_config_disable(rule: str):
    """Disable a risk rule (with confirmation for dangerous rules)."""
    console.print(f"[cyan]Disabling rule: {rule}...[/cyan]")

    try:
        config = load_risk_config()

        # Validate rule exists
        if rule not in config['rules']:
            console.print(f"[red]Rule not found: {rule}[/red]")
            console.print("[dim]Use 'admin_cli config view' to see available rules[/dim]")
            raise typer.Exit(code=1)

        # Check if dangerous
        if is_dangerous_to_disable(rule):
            if not confirm_dangerous_disable(rule):
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(code=0)

        # Disable the rule
        config['rules'][rule]['enabled'] = False
        save_risk_config(config)

        # Get rule name
        metadata = RULE_METADATA.get(rule, {})
        rule_name = metadata.get('name', rule)

        console.print()
        console.print(Panel(
            f"[bold yellow]WARNING - Rule disabled[/bold yellow]\n\n"
            f"Rule: [cyan]{rule_name}[/cyan]\n"
            f"Status: [red]Disabled[/red]\n\n"
            f"[dim]This protection is now OFF.[/dim]\n\n"
            f"[dim]Remember to reload configuration:[/dim]\n"
            f"[cyan]admin_cli config reload[/cyan]",
            title="Rule Disabled",
            box=box.ROUNDED,
            border_style="yellow",
            expand=False
        ))
        console.print()

    except Exception as e:
        console.print(f"[red]Error disabling rule: {e}[/red]")
        raise typer.Exit(code=1)


def cmd_config_validate():
    """Validate configuration file syntax and structure."""
    console.print("[cyan]Validating configuration...[/cyan]")
    console.print()

    try:
        config_file = get_config_dir() / "risk_config.yaml"
        config = load_risk_config()

        # Run validation
        is_valid, errors = validate_config(config)

        if is_valid:
            # Success panel (use text without special unicode chars)
            console.print(Panel(
                "[bold green]Configuration is valid![/bold green]\n\n"
                f"[bold]File:[/bold] {config_file}\n"
                f"[bold]Rules:[/bold] {len(config['rules'])} configured\n"
                f"[bold]Instruments:[/bold] {len(config['general']['instruments'])}\n"
                f"[bold]Timezone:[/bold] {config['general']['timezone']}\n\n"
                "[bold green]All checks passed[/bold green]\n\n"
                "Checks performed:\n"
                "  [green]OK[/green] YAML syntax valid\n"
                "  [green]OK[/green] All required sections present\n"
                "  [green]OK[/green] All required fields present\n"
                "  [green]OK[/green] Value types correct\n"
                "  [green]OK[/green] Timezone format valid\n"
                "  [green]OK[/green] No conflicts detected",
                title="Validation Success",
                box=box.DOUBLE,
                border_style="green",
                expand=False
            ))
        else:
            # Error panel (use text without special unicode chars)
            error_list = "\n".join(f"  - {error}" for error in errors)
            console.print(Panel(
                f"[bold red]Configuration validation failed![/bold red]\n\n"
                f"[bold]File:[/bold] {config_file}\n\n"
                f"[bold red]Errors found:[/bold red]\n"
                f"{error_list}\n\n"
                f"[dim]Please fix these errors and try again.[/dim]",
                title="Validation Failed",
                box=box.DOUBLE,
                border_style="red",
                expand=False
            ))
            raise typer.Exit(code=1)

        console.print()

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Configuration validation failed![/bold red]\n\n"
            f"Error: {str(e)}\n\n"
            f"[dim]This might be a YAML syntax error.[/dim]\n"
            f"[dim]Check the file for proper YAML formatting.[/dim]",
            title="Validation Error",
            box=box.DOUBLE,
            border_style="red",
            expand=False
        ))
        raise typer.Exit(code=1)
