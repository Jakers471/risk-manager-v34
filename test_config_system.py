"""Test script for configuration and credentials system.

Tests:
1. Credential loading from .env
2. Configuration loading (risk + accounts)
3. Account selection (with explicit account)
4. RuntimeConfig validation

Run this to verify Agent 1 deliverables work correctly.
"""

import sys
from pathlib import Path

# Fix Windows console encoding issue
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from risk_manager.cli.credential_manager import get_credentials, validate_credentials
from risk_manager.cli.config_loader import load_runtime_config, validate_runtime_config


def test_credentials():
    """Test credential loading."""
    print("="*60)
    print("TEST 1: Credential Loading")
    print("="*60)
    print()

    try:
        creds = get_credentials()
        print(f"✓ Credentials loaded")
        print(f"  Username: {creds._redact(creds.username)}")
        print(f"  API Key: {creds._redact(creds.api_key)}")

        if creds.client_id:
            print(f"  Client ID: {creds._redact(creds.client_id)}")
        if creds.client_secret:
            print(f"  Client Secret: {creds._redact(creds.client_secret)}")

        # Validate
        validate_credentials(creds)
        print(f"✓ Credentials validated")
        print()
        return True

    except Exception as e:
        print(f"✗ Credential loading failed: {e}")
        print()
        return False


def test_configuration_loading():
    """Test configuration loading."""
    print("="*60)
    print("TEST 2: Configuration Loading")
    print("="*60)
    print()

    try:
        # Use explicit account to avoid interactive prompt
        config = load_runtime_config(
            account_id="PRAC-V2-126244",  # Explicit account from .env
            interactive=False
        )

        print(f"✓ Configuration loaded")
        print(f"  Selected Account: {config.selected_account_id}")
        print(f"  Risk Config: {config.risk_config_path}")
        print(f"  Accounts Config: {config.accounts_config_path}")
        print(f"  Credentials: {config.credentials}")
        print()

        # Count enabled rules
        enabled_rules = []
        for rule_name in dir(config.risk_config.rules):
            if rule_name.startswith("_"):
                continue
            rule = getattr(config.risk_config.rules, rule_name)
            if hasattr(rule, "enabled") and rule.enabled:
                enabled_rules.append(rule_name)

        print(f"  Enabled Rules ({len(enabled_rules)}):")
        for rule_name in enabled_rules:
            print(f"    - {rule_name}")
        print()

        # Validate
        validate_runtime_config(config)
        print(f"✓ Configuration validated")
        print()
        return True

    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


def test_security_redaction():
    """Test that credentials are redacted in logs."""
    print("="*60)
    print("TEST 3: Security - Credential Redaction")
    print("="*60)
    print()

    try:
        creds = get_credentials()

        # Test redaction
        creds_str = str(creds)
        creds_repr = repr(creds)

        print(f"String representation: {creds_str}")
        print(f"Repr representation: {creds_repr}")

        # Verify redaction (should contain "..." but not full credentials)
        if "..." in creds_str and "..." in creds_repr:
            print(f"✓ Credentials are redacted in logs")
            print()
            return True
        else:
            print(f"✗ Credentials NOT redacted (security issue!)")
            print()
            return False

    except Exception as e:
        print(f"✗ Redaction test failed: {e}")
        print()
        return False


def main():
    """Run all tests."""
    print()
    print("="*60)
    print("Configuration & Credentials System Test")
    print("Agent 1 Deliverables Verification")
    print("="*60)
    print()

    results = []

    # Test 1: Credentials
    results.append(("Credential Loading", test_credentials()))

    # Test 2: Configuration
    results.append(("Configuration Loading", test_configuration_loading()))

    # Test 3: Security
    results.append(("Security Redaction", test_security_redaction()))

    # Summary
    print("="*60)
    print("TEST RESULTS")
    print("="*60)
    print()

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {test_name}")

    print()

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    print(f"Passed: {passed_tests}/{total_tests}")
    print()

    if passed_tests == total_tests:
        print("="*60)
        print("✓ ALL TESTS PASSED - Agent 1 deliverables verified!")
        print("="*60)
        return 0
    else:
        print("="*60)
        print("✗ SOME TESTS FAILED - Review errors above")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
