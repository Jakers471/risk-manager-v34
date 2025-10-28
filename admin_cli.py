#!/usr/bin/env python3
"""
Admin CLI Entry Point for Risk Manager V34

This is the main entry point for administrative commands.

Usage:
    admin_cli                           # Interactive menu (default)
    admin_cli --help                    # Show all commands
    admin_cli service status            # Check service status
    admin_cli config show               # Show configuration
    admin_cli rules list                # List all rules
    admin_cli lockouts list             # List active lockouts
    admin_cli status                    # Show system status

Administrator Commands (require UAC elevation):
    admin_cli service start             # Start service
    admin_cli service stop              # Stop service
    admin_cli service restart           # Restart service
    admin_cli config edit               # Edit configuration
    admin_cli rules enable <rule>       # Enable rule
    admin_cli rules disable <rule>      # Disable rule
    admin_cli lockouts remove <account> # Remove lockout (emergency unlock)

For detailed help on any command:
    admin_cli <command> --help

Examples:
    admin_cli                           # Launch interactive menu
    admin_cli service status
    admin_cli rules list
    admin_cli lockouts list
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    # If no arguments provided, launch interactive menu
    if len(sys.argv) == 1:
        from admin_menu import main as menu_main
        menu_main()
    else:
        # Otherwise use command-line interface
        from risk_manager.cli.admin import main
        main()
