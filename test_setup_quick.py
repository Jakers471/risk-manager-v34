#!/usr/bin/env python3
"""
Quick test to verify setup wizard works without SDK errors.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from risk_manager.cli.setup_wizard import (
    validate_api_credentials,
    fetch_accounts,
    save_credentials,
    save_account_config,
    save_risk_config
)


async def test_setup_wizard():
    """Test the setup wizard functions."""
    print("=" * 60)
    print("SETUP WIZARD TEST")
    print("=" * 60)
    print()

    # Test 1: Validate credentials
    print("[TEST 1] Validating API credentials...")
    success, message = await validate_api_credentials(
        api_key="test_api_key_12345678",
        username="testuser"
    )
    print(f"  Result: {success}")
    print(f"  Message: {message}")
    assert success, "Credential validation should succeed with valid-looking credentials"
    print("  [OK] PASSED")
    print()

    # Test 2: Fetch accounts
    print("[TEST 2] Fetching accounts...")
    accounts = await fetch_accounts(
        api_key="test_api_key_12345678",
        username="testuser"
    )
    print(f"  Found {len(accounts)} accounts")
    for i, acc in enumerate(accounts, 1):
        print(f"    {i}. {acc['name']} ({acc['id']}) - {acc['status']}")
    assert len(accounts) >= 1, "Should return at least 1 placeholder account"
    assert accounts[0]['status'] == "Pending validation", "Accounts should have pending status"
    print("  [OK] PASSED")
    print()

    # Test 3: Save credentials
    print("[TEST 3] Saving credentials...")
    try:
        save_credentials(
            api_key="test_api_key_12345678",
            username="testuser"
        )
        print("  [OK] PASSED")
    except Exception as e:
        print(f"  [ERROR] FAILED: {e}")
        raise
    print()

    # Test 4: Save account config
    print("[TEST 4] Saving account config...")
    try:
        save_account_config(
            account_id="PRAC-V2-XXXXXX",
            account_name="Practice Account"
        )
        print("  [OK] PASSED")
    except Exception as e:
        print(f"  [ERROR] FAILED: {e}")
        raise
    print()

    # Test 5: Save risk config (quick setup)
    print("[TEST 5] Saving risk config (quick setup)...")
    try:
        save_risk_config(quick_setup=True)
        print("  [OK] PASSED")
    except Exception as e:
        print(f"  [ERROR] FAILED: {e}")
        raise
    print()

    # Test 6: Save risk config (custom setup)
    print("[TEST 6] Saving risk config (custom setup)...")
    try:
        save_risk_config(quick_setup=False)
        print("  [OK] PASSED")
    except Exception as e:
        print(f"  [ERROR] FAILED: {e}")
        raise
    print()

    print("=" * 60)
    print("ALL TESTS PASSED [OK]")
    print("=" * 60)
    print()
    print("The setup wizard is ready to use!")
    print("Run: python admin_cli.py setup")
    print()


if __name__ == "__main__":
    asyncio.run(test_setup_wizard())
