#!/usr/bin/env python3
"""
Test CLI for Config Editor

Quick test script for the interactive rule configuration editor.

Usage:
    python test_config_editor.py view
    python test_config_editor.py edit daily_realized_loss
    python test_config_editor.py enable max_contracts
    python test_config_editor.py disable symbol_blocks
    python test_config_editor.py validate
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import typer
from rich.console import Console

# Import enhanced config commands
from risk_manager.cli.admin_config_enhanced import (
    cmd_config_view,
    cmd_config_edit,
    cmd_config_enable,
    cmd_config_disable,
    cmd_config_validate
)

app = typer.Typer(
    name="test_config_editor",
    help="Test Config Editor - Risk Manager V34",
    add_completion=False
)

console = Console()


@app.command("view")
def view():
    """Display current risk configuration in visual table format."""
    cmd_config_view()


@app.command("edit")
def edit(rule: str = typer.Argument(..., help="Rule ID to edit (e.g., 'daily_realized_loss')")):
    """Edit specific rule configuration interactively."""
    cmd_config_edit(rule)


@app.command("enable")
def enable(rule: str = typer.Argument(..., help="Rule ID to enable (e.g., 'max_contracts')")):
    """Enable a risk rule."""
    cmd_config_enable(rule)


@app.command("disable")
def disable(rule: str = typer.Argument(..., help="Rule ID to disable (e.g., 'symbol_blocks')")):
    """Disable a risk rule (with confirmation for dangerous rules)."""
    cmd_config_disable(rule)


@app.command("validate")
def validate():
    """Validate configuration file syntax and structure."""
    cmd_config_validate()


if __name__ == "__main__":
    app()
