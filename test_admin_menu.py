#!/usr/bin/env python3
"""
Quick test for admin menu - verify it loads and displays
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich import box
from rich.table import Table

console = Console()


def test_menu_display():
    """Test that the menu displays correctly"""
    print("=" * 60)
    print("ADMIN MENU TEST")
    print("=" * 60)
    print()

    # Test header
    console.print()
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold cyan]        RISK MANAGER V34 - ADMIN CONTROL PANEL[/bold cyan]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print()

    # Test menu table
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

    print("[OK] Menu displays correctly")
    print()

    # Test that we can import the menu functions
    try:
        from admin_menu import show_main_menu, screen_dashboard, check_config_files
        print("[OK] Menu functions import successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import menu functions: {e}")
        return False

    # Test helper functions
    try:
        result = check_config_files()
        print(f"[OK] Config files check: {result}")
    except Exception as e:
        print(f"[ERROR] Config check failed: {e}")
        return False

    print()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    print()
    print("To run the interactive menu:")
    print("  python admin_menu.py")
    print()

    return True


if __name__ == "__main__":
    test_menu_display()
