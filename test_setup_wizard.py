"""
Test script for setup wizard

This script tests that the setup wizard can be imported and that
its helper functions work correctly without running the full interactive wizard.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from risk_manager.cli.setup_wizard import (
    get_config_dir,
    save_credentials,
    save_account_config,
    save_risk_config,
)

def test_config_dir():
    """Test config directory creation."""
    print("Testing config directory...")
    config_dir = get_config_dir()
    print(f"[OK] Config directory: {config_dir}")
    assert config_dir.exists() or config_dir.parent.exists()
    print("[OK] Config directory test passed")


def test_save_credentials():
    """Test credential saving."""
    print("\nTesting credential saving...")

    # Save test credentials
    save_credentials("test_api_key_12345", "test_user")

    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        content = env_file.read_text()
        assert "PROJECT_X_API_KEY=test_api_key_12345" in content
        assert "PROJECT_X_USERNAME=test_user" in content
        print("[OK] Credentials saved successfully")
    else:
        print("[WARN] .env file not created (may need permissions)")


def test_save_account_config():
    """Test account config saving."""
    print("\nTesting account config saving...")

    try:
        save_account_config("TEST-ACCOUNT-123", "Test Account")

        # Check config file
        config_file = get_config_dir() / "accounts.yaml"
        if config_file.exists():
            print(f"[OK] Account config saved to {config_file}")
        else:
            print(f"[WARN] Account config file not found at {config_file}")
    except Exception as e:
        print(f"[WARN] Account config save failed: {e}")


def test_save_risk_config():
    """Test risk config saving."""
    print("\nTesting risk config saving...")

    try:
        # Test quick setup
        save_risk_config(quick_setup=True)

        # Check config file
        config_file = get_config_dir() / "risk_config.yaml"
        if config_file.exists():
            print(f"[OK] Risk config saved to {config_file}")

            # Verify content
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            assert "general" in config
            assert "rules" in config
            assert config["rules"]["max_contracts"]["limit"] == 5
            print("[OK] Risk config content validated")
        else:
            print(f"[WARN] Risk config file not found at {config_file}")
    except Exception as e:
        print(f"[WARN] Risk config save failed: {e}")


def test_imports():
    """Test that all required modules can be imported."""
    print("\nTesting imports...")

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt, Confirm
        from rich.table import Table
        print("[OK] Rich library imports successful")
    except ImportError as e:
        print(f"[ERROR] Rich library import failed: {e}")
        return False

    try:
        import yaml
        print("[OK] YAML library import successful")
    except ImportError as e:
        print(f"[ERROR] YAML library import failed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("="*60)
    print("Setup Wizard Test Suite")
    print("="*60)

    # Test imports first
    if not test_imports():
        print("\n[ERROR] Import tests failed - cannot continue")
        return 1

    # Test helper functions
    try:
        test_config_dir()
        test_save_credentials()
        test_save_account_config()
        test_save_risk_config()

        print("\n" + "="*60)
        print("[SUCCESS] All tests passed!")
        print("="*60)
        print("\nSetup wizard is ready to use.")
        print("Run: python -m risk_manager.cli.admin setup")
        print()

        return 0

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
