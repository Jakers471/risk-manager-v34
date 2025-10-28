"""
Interactive Rule Configuration Editor for Admin CLI

Provides visual table displays and interactive rule editing.
"""

from typing import Any, Dict, Optional, Tuple
from pathlib import Path

import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

console = Console()


# Rule metadata for display
RULE_METADATA = {
    'max_contracts': {
        'name': 'Max Contracts',
        'limit_key': 'limit',
        'type': 'Flatten',
        'description': 'Maximum total contracts across all instruments',
        'dangerous': True
    },
    'max_contracts_per_instrument': {
        'name': 'Max Contracts Per Inst',
        'limit_key': 'default_limit',
        'type': 'Flatten',
        'description': 'Maximum contracts per specific instrument',
        'dangerous': False
    },
    'daily_realized_loss': {
        'name': 'Daily Realized Loss',
        'limit_key': 'limit',
        'type': 'Lockout',
        'description': 'Hard lockout when daily realized losses exceed limit',
        'dangerous': True
    },
    'daily_unrealized_loss': {
        'name': 'Daily Unrealized Loss',
        'limit_key': 'limit',
        'type': 'Flatten',
        'description': 'Flatten all positions when unrealized loss hits limit',
        'dangerous': True
    },
    'max_unrealized_profit': {
        'name': 'Max Unrealized Profit',
        'limit_key': 'target',
        'type': 'Flatten',
        'description': 'Flatten all positions when unrealized profit hits target',
        'dangerous': False
    },
    'trade_frequency_limit': {
        'name': 'Trade Frequency Limit',
        'limit_key': 'limits',
        'type': 'Cooldown',
        'description': 'Limit number of trades per hour/day',
        'dangerous': False
    },
    'cooldown_after_loss': {
        'name': 'Cooldown After Loss',
        'limit_key': 'loss_threshold',
        'type': 'Cooldown',
        'description': 'Enforce cooldown period after losing trade',
        'dangerous': False
    },
    'no_stop_loss_grace': {
        'name': 'No Stop Loss Grace',
        'limit_key': 'require_within_seconds',
        'type': 'Reject',
        'description': 'Reject new positions without stop-loss within grace period',
        'dangerous': False
    },
    'session_block_outside': {
        'name': 'Session Block Outside',
        'limit_key': 'allowed_hours',
        'type': 'Lockout',
        'description': 'Block trading outside allowed session hours',
        'dangerous': False
    },
    'symbol_blocks': {
        'name': 'Symbol Blocks',
        'limit_key': 'blocked_symbols',
        'type': 'Reject',
        'description': 'Block trading specific symbols',
        'dangerous': False
    },
    'trade_management': {
        'name': 'Trade Management',
        'limit_key': 'auto_breakeven',
        'type': 'Automation',
        'description': 'Automatic trade management (breakeven stop-loss)',
        'dangerous': False
    },
    'auth_loss_guard': {
        'name': 'Auth Loss Guard',
        'limit_key': 'check_interval_seconds',
        'type': 'Alert',
        'description': 'Lockout if API disconnects to prevent unmonitored trading',
        'dangerous': True
    },
    'daily_realized_profit': {
        'name': 'Daily Realized Profit',
        'limit_key': 'target',
        'type': 'Lockout',
        'description': 'Hard lockout when daily profit target reached',
        'dangerous': False
    },
}


def format_limit_value(limit_value: Any, rule_key: str) -> str:
    """Format limit value for display."""
    if isinstance(limit_value, (int, float)):
        if limit_value < 0:
            return f"-${abs(limit_value):,.0f}"
        elif limit_value > 0 and rule_key in ['daily_realized_profit', 'max_unrealized_profit']:
            return f"+${limit_value:,.0f}"
        elif limit_value == 0:
            return "0"
        else:
            return f"{limit_value}"
    elif isinstance(limit_value, dict):
        # For complex values like trade frequency limits
        if rule_key == 'trade_frequency_limit':
            hour = limit_value.get('hour', 'N/A')
            return f"{hour}/hour"
        elif rule_key == 'session_block_outside':
            start = limit_value.get('start', 'N/A')
            end = limit_value.get('end', 'N/A')
            return f"{start}-{end}"
        elif rule_key == 'trade_management':
            if isinstance(limit_value, dict) and 'enabled' in limit_value:
                return "Enabled" if limit_value['enabled'] else "Disabled"
            return str(limit_value)[:20] + "..."
        else:
            return str(limit_value)[:20] + "..."
    elif isinstance(limit_value, list):
        if len(limit_value) == 0:
            return "[]"
        else:
            return str(limit_value)[:30]
    else:
        return str(limit_value)


def display_config_table(config: dict) -> None:
    """Display risk configuration in visual table format."""
    console.print()

    # Build table
    table = Table(title="RISK CONFIGURATION", box=box.ROUNDED)
    table.add_column("Rule", style="cyan", no_wrap=False, width=30)
    table.add_column("Status", style="white", no_wrap=True, width=12)
    table.add_column("Limit", style="yellow", width=20)
    table.add_column("Type", style="dim", width=12)

    for rule_key, metadata in RULE_METADATA.items():
        if rule_key in config['rules']:
            rule_config = config['rules'][rule_key]
            enabled = rule_config.get('enabled', False)

            # Format status (use text without emoji for Windows compatibility)
            status = "[green]ENABLED[/green]" if enabled else "[red]DISABLED[/red]"

            # Format limit
            limit_key = metadata['limit_key']
            limit_value = rule_config.get(limit_key, 'N/A')
            limit_str = format_limit_value(limit_value, rule_key)

            table.add_row(metadata['name'], status, limit_str, metadata['type'])

    console.print(table)
    console.print()

    # Display timers & schedules
    if 'timers' in config:
        timers = config['timers']
        daily_reset = timers.get('daily_reset', {})
        reset_time = daily_reset.get('time', 'N/A')
        timezone = daily_reset.get('timezone', 'N/A')

        console.print(Panel(
            f"[bold]Daily Reset:[/bold] {reset_time} {timezone}\n"
            f"[bold]Lockout Duration:[/bold] Until reset",
            title="Timers & Schedules",
            border_style="cyan",
            box=box.ROUNDED
        ))
        console.print()


def show_rule_editor(rule_key: str, config: dict, config_file: Path) -> None:
    """Interactive rule editor for a specific rule."""
    if rule_key not in config['rules']:
        console.print(f"[red]Rule not found: {rule_key}[/red]")
        console.print("[dim]Use 'admin_cli config view' to see available rules[/dim]")
        return

    if rule_key not in RULE_METADATA:
        console.print(f"[red]Rule metadata not found: {rule_key}[/red]")
        return

    metadata = RULE_METADATA[rule_key]
    rule_config = config['rules'][rule_key]

    while True:
        console.print()

        # Build menu content
        menu_content = Text()
        menu_content.append("Current Settings:\n", style="bold cyan")
        menu_content.append("─" * 40 + "\n", style="dim")

        # Status
        is_enabled = rule_config.get('enabled', False)
        status_str = "ENABLED" if is_enabled else "DISABLED"
        status_style = "green" if is_enabled else "red"
        menu_content.append("Status:  ", style="white")
        menu_content.append(f"{status_str}\n", style=status_style)

        # Limit
        limit_key = metadata['limit_key']
        limit_value = rule_config.get(limit_key, 'N/A')
        limit_str = format_limit_value(limit_value, rule_key)
        menu_content.append(f"Limit:   {limit_str}\n", style="yellow")

        # Action/Type
        menu_content.append(f"Type:    {metadata['type']}\n\n", style="dim")

        # Description
        menu_content.append(metadata['description'] + "\n\n", style="italic dim")

        # Options
        menu_content.append("┌" + "─" * 38 + "┐\n", style="cyan")
        menu_content.append("│ 1. Enable/Disable                    │\n", style="cyan")
        menu_content.append("│ 2. Change Limit                      │\n", style="cyan")
        menu_content.append("│ 3. Save & Exit                       │\n", style="cyan")
        menu_content.append("│ 4. Exit Without Saving               │\n", style="cyan")
        menu_content.append("└" + "─" * 38 + "┘\n", style="cyan")

        panel = Panel(
            menu_content,
            title=f"EDIT RULE - {metadata['name']}",
            box=box.DOUBLE,
            border_style="cyan",
            expand=False
        )
        console.print(panel)

        choice = Prompt.ask("Choice", choices=["1", "2", "3", "4"], default="4")

        if choice == "1":
            # Toggle enable/disable
            current = rule_config.get('enabled', False)
            rule_config['enabled'] = not current
            new_status = "enabled" if not current else "disabled"
            console.print(f"[green]Rule {new_status}[/green]")

        elif choice == "2":
            # Change limit
            console.print()
            change_limit_interactive(rule_key, rule_config, metadata)

        elif choice == "3":
            # Save & Exit
            if Confirm.ask("[yellow]Save changes to configuration?[/yellow]", default=True):
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                console.print(f"[green]✓ Configuration saved: {config_file}[/green]")
                console.print("[yellow]Remember to reload: admin_cli config reload[/yellow]")
            else:
                console.print("[dim]Changes discarded[/dim]")
            break

        elif choice == "4":
            # Exit without saving
            if Confirm.ask("[yellow]Discard changes?[/yellow]", default=False):
                console.print("[dim]Changes discarded[/dim]")
                break


def change_limit_interactive(rule_key: str, rule_config: dict, metadata: dict) -> None:
    """Interactive limit change dialog."""
    limit_key = metadata['limit_key']
    current_value = rule_config.get(limit_key, 'N/A')
    current_str = format_limit_value(current_value, rule_key)

    console.print(Panel(
        f"[bold]Current limit:[/bold] {current_str}\n\n"
        f"[dim]{metadata['description']}[/dim]",
        title=f"CHANGE LIMIT - {metadata['name']}",
        box=box.DOUBLE,
        border_style="yellow",
        expand=False
    ))
    console.print()

    # Handle different limit types
    if isinstance(current_value, (int, float)):
        # Simple numeric limit
        new_value_str = Prompt.ask(
            "Enter new limit (number)",
            default=str(current_value)
        )
        try:
            new_value = float(new_value_str)
            rule_config[limit_key] = new_value
            console.print(f"[green]✓ Limit updated to: {format_limit_value(new_value, rule_key)}[/green]")
        except ValueError:
            console.print("[red]Invalid number format[/red]")

    elif isinstance(current_value, dict):
        # Complex limit (e.g., trade frequency, session hours)
        if rule_key == 'trade_frequency_limit':
            hour = Prompt.ask("Trades per hour", default=str(current_value.get('hour', 10)))
            day = Prompt.ask("Trades per day", default=str(current_value.get('day', 50)))
            try:
                rule_config[limit_key] = {
                    'hour': int(hour),
                    'day': int(day)
                }
                console.print(f"[green]✓ Limit updated[/green]")
            except ValueError:
                console.print("[red]Invalid number format[/red]")

        elif rule_key == 'session_block_outside':
            start = Prompt.ask("Session start time (HH:MM)", default=current_value.get('start', '08:30'))
            end = Prompt.ask("Session end time (HH:MM)", default=current_value.get('end', '15:00'))
            rule_config[limit_key] = {
                'start': start,
                'end': end
            }
            console.print(f"[green]✓ Session hours updated to: {start}-{end}[/green]")

        else:
            console.print("[yellow]Complex limit types must be edited manually in YAML file[/yellow]")

    elif isinstance(current_value, list):
        # List limit (e.g., blocked symbols)
        console.print(f"[dim]Current list: {current_value}[/dim]")
        new_list_str = Prompt.ask(
            "Enter comma-separated values (or empty for [])",
            default=",".join(str(x) for x in current_value) if current_value else ""
        )
        if new_list_str.strip():
            new_list = [x.strip() for x in new_list_str.split(',')]
            rule_config[limit_key] = new_list
            console.print(f"[green]✓ List updated to: {new_list}[/green]")
        else:
            rule_config[limit_key] = []
            console.print(f"[green]✓ List cleared[/green]")

    else:
        console.print("[yellow]This limit type must be edited manually in YAML file[/yellow]")


def is_dangerous_to_disable(rule_key: str) -> bool:
    """Check if disabling this rule is dangerous."""
    metadata = RULE_METADATA.get(rule_key, {})
    return metadata.get('dangerous', False)


def confirm_dangerous_disable(rule_key: str) -> bool:
    """Show confirmation dialog for disabling dangerous rules."""
    metadata = RULE_METADATA.get(rule_key, {})
    rule_name = metadata.get('name', rule_key)

    console.print()
    warning_panel = Panel(
        f"[bold red]WARNING - CONFIRM DISABLE[/bold red]\n\n"
        f"You are about to disable:\n"
        f"[bold cyan]{rule_name}[/bold cyan]\n\n"
        f"{metadata.get('description', 'This rule provides trading protection.')}\n\n"
        f"[bold]Disabling removes this protection.[/bold]\n\n"
        f"Type [bold cyan]DISABLE[/bold cyan] to confirm:",
        title="Dangerous Operation",
        box=box.DOUBLE,
        border_style="red",
        expand=False
    )
    console.print(warning_panel)
    console.print()

    confirmation = Prompt.ask("Confirmation")
    return confirmation == "DISABLE"


def validate_config(config: dict) -> Tuple[bool, list]:
    """
    Validate risk configuration.

    Returns:
        (is_valid, errors)
    """
    errors = []

    # Check required sections
    if 'general' not in config:
        errors.append("Missing 'general' section")
    if 'rules' not in config:
        errors.append("Missing 'rules' section")
    if 'timers' not in config:
        errors.append("Missing 'timers' section")

    if errors:
        return False, errors

    # Validate general section
    general = config.get('general', {})
    if 'instruments' not in general or not general['instruments']:
        errors.append("No instruments configured in general section")
    if 'timezone' not in general:
        errors.append("Missing timezone in general section")

    # Validate each rule
    rules = config.get('rules', {})
    for rule_key, rule_config in rules.items():
        if not isinstance(rule_config, dict):
            errors.append(f"Rule '{rule_key}' is not a dictionary")
            continue

        if 'enabled' not in rule_config:
            errors.append(f"Rule '{rule_key}' missing 'enabled' field")

        # Check for required fields based on metadata
        if rule_key in RULE_METADATA:
            metadata = RULE_METADATA[rule_key]
            limit_key = metadata['limit_key']
            if limit_key not in rule_config:
                errors.append(f"Rule '{rule_key}' missing required field '{limit_key}'")

    # Validate timers
    timers = config.get('timers', {})
    if 'daily_reset' not in timers:
        errors.append("Missing 'daily_reset' in timers section")
    else:
        daily_reset = timers['daily_reset']
        if 'time' not in daily_reset:
            errors.append("Missing 'time' in daily_reset configuration")
        if 'timezone' not in daily_reset:
            errors.append("Missing 'timezone' in daily_reset configuration")

    return len(errors) == 0, errors
