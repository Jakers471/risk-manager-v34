#!/usr/bin/env python3
"""Validate configuration loading integration.

This script tests the complete config loading flow without interactive prompts.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Test configuration loading."""
    print("=" * 60)
    print("Config Loader Integration Validation")
    print("=" * 60)
    print()

    # Test 1: Load risk_config.yaml
    print("Test 1: Loading risk_config.yaml...")
    try:
        from risk_manager.config.loader import ConfigLoader

        loader = ConfigLoader(config_dir="config", env_file=".env")
        risk_config = loader.load_risk_config()

        print("  OK: risk_config loaded")

        # Validate structure
        assert risk_config.general is not None, "general section missing"
        assert risk_config.rules is not None, "rules section missing"
        print("  OK: Structure validated (general, rules)")

        # Test nested access
        instruments = risk_config.general.instruments
        print(f"  OK: Instruments accessible: {instruments}")

        max_contracts = risk_config.rules.max_contracts
        print(f"  OK: Rules accessible: max_contracts.limit = {max_contracts.limit}")

    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Test 2: Load accounts.yaml
    print("Test 2: Loading accounts.yaml...")
    try:
        accounts_config = loader.load_accounts_config()

        print("  OK: accounts_config loaded")

        # Validate structure
        assert accounts_config.topstepx is not None, "topstepx section missing"
        print("  OK: Structure validated (topstepx)")

        # Test credentials (should be substituted)
        username = accounts_config.topstepx.username
        api_key = accounts_config.topstepx.api_key
        print(f"  OK: Credentials accessible (username length: {len(username)})")

    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Test 3: RuntimeConfig integration
    print("Test 3: Testing RuntimeConfig integration...")
    try:
        from risk_manager.cli.config_loader import _validate_config_structure

        # This function validates all critical paths
        _validate_config_structure(risk_config, accounts_config)
        print("  OK: Config structure validation passed")

    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Test 4: Full RuntimeConfig loading (non-interactive)
    print("Test 4: Loading full RuntimeConfig (non-interactive)...")
    try:
        # First, get available accounts
        from risk_manager.cli.config_loader import _get_available_accounts

        available = _get_available_accounts(accounts_config)
        if not available:
            print("  SKIP: No accounts configured")
        else:
            account_id = available[0]['account_id']
            print(f"  Using account: {account_id}")

            # Now load full runtime config
            # NOTE: We skip this because it requires credentials in .env
            # and interactive console which may not work in all environments
            print("  SKIP: Full runtime config loading (requires .env setup)")

    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("=" * 60)
    print("SUCCESS: All config integration tests passed!")
    print("=" * 60)
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
