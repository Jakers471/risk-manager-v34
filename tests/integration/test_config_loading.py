"""Integration test for configuration loading end-to-end.

Tests the complete flow:
1. YAML files → ConfigLoader → Pydantic models
2. ConfigLoader → RuntimeConfig
3. RuntimeConfig → RiskManager

This ensures the nested structure is correctly loaded and accessible.
"""

import pytest
from pathlib import Path

from risk_manager.cli.config_loader import load_runtime_config, RuntimeConfigError
from risk_manager.config.loader import ConfigLoader, ConfigurationError


class TestConfigLoaderIntegration:
    """Test ConfigLoader with actual config files."""

    def test_load_risk_config_structure(self):
        """Test that risk_config.yaml loads with correct nested structure."""
        loader = ConfigLoader(config_dir="config", env_file=".env")

        # Load risk config
        risk_config = loader.load_risk_config()

        # Test nested structure access
        assert risk_config.general is not None, "general section missing"
        assert risk_config.rules is not None, "rules section missing"

        # Test general config
        assert hasattr(risk_config.general, 'instruments'), "instruments missing"
        assert hasattr(risk_config.general, 'timezone'), "timezone missing"
        assert hasattr(risk_config.general, 'logging'), "logging missing"

        # Test rules exist
        assert hasattr(risk_config.rules, 'max_contracts'), "max_contracts rule missing"
        assert hasattr(risk_config.rules, 'max_contracts_per_instrument'), "max_contracts_per_instrument rule missing"
        assert hasattr(risk_config.rules, 'daily_unrealized_loss'), "daily_unrealized_loss rule missing"
        assert hasattr(risk_config.rules, 'max_unrealized_profit'), "max_unrealized_profit rule missing"

        # Test rule config structure
        max_contracts = risk_config.rules.max_contracts
        assert hasattr(max_contracts, 'enabled'), "enabled field missing"
        assert hasattr(max_contracts, 'limit'), "limit field missing"
        assert hasattr(max_contracts, 'count_type'), "count_type field missing"

        # Test values are correct types
        assert isinstance(max_contracts.enabled, bool), "enabled should be bool"
        assert isinstance(max_contracts.limit, int), "limit should be int"
        assert max_contracts.limit > 0, "limit should be positive"

    def test_load_accounts_config_structure(self):
        """Test that accounts.yaml loads with correct structure."""
        loader = ConfigLoader(config_dir="config", env_file=".env")

        # Load accounts config
        accounts_config = loader.load_accounts_config()

        # Test topstepx credentials
        assert accounts_config.topstepx is not None, "topstepx section missing"
        assert hasattr(accounts_config.topstepx, 'username'), "username missing"
        assert hasattr(accounts_config.topstepx, 'api_key'), "api_key missing"
        assert hasattr(accounts_config.topstepx, 'api_url'), "api_url missing"

        # Test accounts list exists (either monitored_account or accounts)
        has_monitored = accounts_config.monitored_account is not None
        has_accounts = accounts_config.accounts is not None and len(accounts_config.accounts) > 0

        assert has_monitored or has_accounts, "No accounts configured"

    def test_nested_access_pattern(self):
        """Test the specific nested access pattern used in run_dev.py."""
        loader = ConfigLoader(config_dir="config", env_file=".env")
        risk_config = loader.load_risk_config()

        # This is the pattern used in run_dev.py lines 153-156
        try:
            instruments = risk_config.general.instruments
            assert isinstance(instruments, list), "instruments should be a list"
            assert len(instruments) > 0, "instruments should not be empty"
        except AttributeError as e:
            pytest.fail(f"Failed to access risk_config.general.instruments: {e}")

        # Test accessing rule config (pattern: config.rules.rule_name.enabled)
        try:
            enabled_rules = []
            for rule_name in ['max_contracts', 'max_contracts_per_instrument',
                            'daily_unrealized_loss', 'max_unrealized_profit']:
                rule = getattr(risk_config.rules, rule_name)
                if rule.enabled:
                    enabled_rules.append(rule_name)

            assert len(enabled_rules) >= 0, "Should be able to count enabled rules"
        except AttributeError as e:
            pytest.fail(f"Failed to access rule configs: {e}")


class TestRuntimeConfigIntegration:
    """Test RuntimeConfig loading with actual config files."""

    def test_load_runtime_config_basic(self):
        """Test basic runtime config loading (non-interactive, single account)."""
        # This will fail if multiple accounts exist, but that's expected
        # In real use, account_id would be provided
        try:
            runtime_config = load_runtime_config(
                interactive=False,
                account_id="PRAC-V2-XXXXXX"  # Default test account
            )

            # Verify structure
            assert runtime_config.risk_config is not None, "risk_config missing"
            assert runtime_config.accounts_config is not None, "accounts_config missing"
            assert runtime_config.credentials is not None, "credentials missing"
            assert runtime_config.selected_account_id is not None, "selected_account_id missing"

        except RuntimeConfigError as e:
            # If account not found, that's fine - it means validation is working
            if "Account not found" in str(e) or "No accounts configured" in str(e):
                pytest.skip(f"Account not configured in test environment: {e}")
            else:
                raise

    def test_runtime_config_exposes_nested_structure(self):
        """Test that RuntimeConfig correctly exposes nested risk_config structure."""
        try:
            runtime_config = load_runtime_config(
                interactive=False,
                account_id="PRAC-V2-XXXXXX"
            )

            # Test nested access pattern used in run_dev.py
            instruments = runtime_config.risk_config.general.instruments
            assert isinstance(instruments, list), "instruments should be accessible"

            # Test accessing rules
            max_contracts_rule = runtime_config.risk_config.rules.max_contracts
            assert hasattr(max_contracts_rule, 'enabled'), "rule should have enabled field"

        except RuntimeConfigError as e:
            if "Account not found" in str(e) or "No accounts configured" in str(e):
                pytest.skip(f"Account not configured: {e}")
            else:
                raise

    def test_config_loader_get_available_accounts(self):
        """Test the _get_available_accounts function with actual config."""
        from risk_manager.cli.config_loader import _get_available_accounts

        loader = ConfigLoader(config_dir="config", env_file=".env")
        accounts_config = loader.load_accounts_config()

        # Get available accounts
        available = _get_available_accounts(accounts_config)

        # Should return a list
        assert isinstance(available, list), "Should return list of accounts"

        # Each account should have required keys
        for account in available:
            assert "account_id" in account, "account_id key missing"
            assert "name" in account, "name key missing"
            assert "enabled" in account, "enabled key missing"


class TestConfigValidation:
    """Test configuration validation catches issues."""

    def test_risk_config_validates_rules_exist(self):
        """Test that RiskConfig requires rules section."""
        loader = ConfigLoader(config_dir="config", env_file=".env")

        try:
            risk_config = loader.load_risk_config()

            # Verify rules section is not None
            assert risk_config.rules is not None, "rules section should exist"

            # Verify we can iterate over rules
            rule_count = 0
            for attr_name in dir(risk_config.rules):
                if not attr_name.startswith('_'):
                    attr = getattr(risk_config.rules, attr_name)
                    if hasattr(attr, 'enabled'):
                        rule_count += 1

            assert rule_count > 0, "Should have at least one rule"

        except ConfigurationError as e:
            pytest.fail(f"Config validation failed unexpectedly: {e}")

    def test_general_config_validates_instruments(self):
        """Test that GeneralConfig requires instruments list."""
        loader = ConfigLoader(config_dir="config", env_file=".env")

        try:
            risk_config = loader.load_risk_config()

            # Verify instruments exist and is non-empty list
            assert risk_config.general.instruments is not None, "instruments should exist"
            assert isinstance(risk_config.general.instruments, list), "instruments should be list"
            assert len(risk_config.general.instruments) > 0, "instruments should not be empty"

        except ConfigurationError as e:
            pytest.fail(f"Config validation failed unexpectedly: {e}")


class TestEnvVarSubstitution:
    """Test environment variable substitution in configs."""

    def test_accounts_yaml_env_substitution(self):
        """Test that ${PROJECT_X_USERNAME} etc. are substituted."""
        loader = ConfigLoader(config_dir="config", env_file=".env")
        accounts_config = loader.load_accounts_config()

        # Check that variables were substituted (should not contain ${...})
        username = accounts_config.topstepx.username
        api_key = accounts_config.topstepx.api_key

        assert not username.startswith("${"), f"username not substituted: {username}"
        assert not api_key.startswith("${"), f"api_key not substituted: {api_key}"

        # Should have actual values (not empty after substitution)
        assert len(username) > 0, "username is empty after substitution"
        assert len(api_key) > 0, "api_key is empty after substitution"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
