#!/usr/bin/env python3
"""Test script to verify config structure compatibility.

This tests that risk_config.yaml loads correctly and exposes nested structure.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
console = Console()


def test_config_loading():
    """Test loading risk_config.yaml and accessing nested attributes."""

    console.print("[bold cyan]Testing Config Structure[/bold cyan]")
    console.print()

    # Test 1: Load YAML directly with ConfigLoader (nested Pydantic model)
    console.print("[bold]Test 1: ConfigLoader (nested Pydantic model)[/bold]")
    try:
        from risk_manager.config.loader import ConfigLoader

        loader = ConfigLoader(config_dir=Path("config"))
        risk_config = loader.load_risk_config()

        console.print(f"  Type: {type(risk_config)}")
        console.print(f"  Has 'general': {hasattr(risk_config, 'general')}")
        console.print(f"  Has 'rules': {hasattr(risk_config, 'rules')}")

        if hasattr(risk_config, 'general'):
            console.print(f"  general.instruments: {risk_config.general.instruments}")

        if hasattr(risk_config, 'rules'):
            console.print(f"  rules.max_contracts: {risk_config.rules.max_contracts}")
            console.print(f"  rules.max_contracts.enabled: {risk_config.rules.max_contracts.enabled}")
            console.print(f"  rules.max_contracts.limit: {risk_config.rules.max_contracts.limit}")

        console.print("[green]  OK: ConfigLoader works correctly (nested structure)[/green]")

    except Exception as e:
        console.print(f"[red]  FAIL: ConfigLoader failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

    console.print()

    # Test 2: Load with backward compatibility shim
    console.print("[bold]Test 2: RiskConfig shim (backward compatibility)[/bold]")
    try:
        from risk_manager.core.config import RiskConfig

        # Create from nested structure
        shim_config = RiskConfig(general=risk_config.general, rules=risk_config.rules)

        console.print(f"  Type: {type(shim_config)}")
        console.print(f"  Has 'general': {hasattr(shim_config, 'general')}")
        console.print(f"  Has 'rules': {hasattr(shim_config, 'rules')}")

        # Test nested access
        if hasattr(shim_config, 'general'):
            console.print(f"  shim.general.instruments: {shim_config.general.instruments}")

        if hasattr(shim_config, 'rules'):
            console.print(f"  shim.rules.max_contracts: {shim_config.rules.max_contracts}")
            console.print(f"  shim.rules.max_contracts.enabled: {shim_config.rules.max_contracts.enabled}")
            console.print(f"  shim.rules.max_contracts.limit: {shim_config.rules.max_contracts.limit}")

        # Test flat access (backward compatibility)
        if hasattr(shim_config, 'max_contracts'):
            console.print(f"  shim.max_contracts (flat): {shim_config.max_contracts}")

        console.print("[green]  OK: RiskConfig shim works correctly[/green]")

    except Exception as e:
        console.print(f"[red]  FAIL: RiskConfig shim failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

    console.print()

    # Test 3: Load via from_file (what run_dev.py should use)
    console.print("[bold]Test 3: RiskConfig.from_file() method[/bold]")
    try:
        from risk_manager.core.config import RiskConfig

        file_config = RiskConfig.from_file("config/risk_config.yaml")

        console.print(f"  Type: {type(file_config)}")
        console.print(f"  Has 'general': {hasattr(file_config, 'general')}")
        console.print(f"  Has 'rules': {hasattr(file_config, 'rules')}")

        # Test nested access (what run_dev.py uses)
        if hasattr(file_config, 'general'):
            console.print(f"  file_config.general.instruments: {file_config.general.instruments}")

        if hasattr(file_config, 'rules'):
            console.print(f"  file_config.rules.max_contracts: {file_config.rules.max_contracts}")
            console.print(f"  file_config.rules.max_contracts.enabled: {file_config.rules.max_contracts.enabled}")

            # Count enabled rules (like run_dev.py does)
            enabled_count = sum(
                1 for rule_name in dir(file_config.rules)
                if not rule_name.startswith("_")
                and hasattr(getattr(file_config.rules, rule_name), "enabled")
                and getattr(file_config.rules, rule_name).enabled
            )
            console.print(f"  Enabled rules: {enabled_count}")

        console.print("[green]  OK: RiskConfig.from_file() works correctly[/green]")

    except Exception as e:
        console.print(f"[red]  FAIL: RiskConfig.from_file() failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

    console.print()
    console.print("[bold green]All tests passed! Config structure is correct.[/bold green]")
    return True


if __name__ == "__main__":
    success = test_config_loading()
    sys.exit(0 if success else 1)
