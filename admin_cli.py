#!/usr/bin/env python3
"""
Admin CLI Entry Point for Risk Manager V34

This is the main entry point for administrative commands.

Usage:
    admin_cli --help                    # Show all commands
    admin_cli service status            # Check service status
    admin_cli config show               # Show configuration
    admin_cli rules list                # List all rules
    admin_cli lockouts list             # List active lockouts
    admin_cli status                    # Show system status
    admin_cli logs                      # View recent logs

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
    admin_cli service status
    admin_cli rules list
    admin_cli lockouts list
    admin_cli logs --tail 100
    admin_cli logs --follow
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from risk_manager.cli.admin import main

if __name__ == "__main__":
    main()
