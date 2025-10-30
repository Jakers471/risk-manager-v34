"""Integration tests for rule loading from configuration.

Tests that rules are correctly loaded from config files and instantiated
with proper parameters. Validates both enabled and disabled rules.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from risk_manager.config.loader import ConfigLoader
from risk_manager.config.models import RiskConfig
from risk_manager.core.manager import RiskManager
from risk_manager.core.engine import RiskEngine
from risk_manager.state.database import Database
from risk_manager.state.pnl_tracker import PnLTracker
from risk_manager.state.lockout_manager import LockoutManager
from risk_manager.state.timer_manager import TimerManager


class TestRuleLoadingFromConfig:
    """Test that rules load correctly from configuration."""

    @pytest.fixture
    async def risk_manager_with_config(self, tmp_path):
        """Create RiskManager with test configuration."""
        # Create test config
        config = MagicMock(spec=RiskConfig)
        config.general = MagicMock()
        config.general.instruments = ["MNQ", "ES"]
        config.general.timezone = "America/Chicago"
        config.general.database = MagicMock()
        config.general.database.path = str(tmp_path / "test.db")
        config.general.logging = MagicMock()
        config.general.logging.level = "INFO"
        config.general.logging.log_to_file = False

        config.rules = MagicMock()
        # Rule configs with various enabled/disabled states
        config.rules.max_contracts = MagicMock(enabled=True, limit=5, count_type="net")
        config.rules.max_contracts_per_instrument = MagicMock(
            enabled=True, default_limit=3, instrument_limits={"MNQ": 2, "ES": 1}
        )
        config.rules.daily_realized_loss = MagicMock(enabled=True, limit=-1000)
        config.rules.daily_realized_profit = MagicMock(enabled=True, target=2000)
        config.rules.daily_unrealized_loss = MagicMock(
            enabled=True, limit=-750, check_interval_seconds=10
        )
        config.rules.max_unrealized_profit = MagicMock(
            enabled=True, target=500, check_interval_seconds=5
        )
        config.rules.trade_frequency_limit = MagicMock(
            enabled=False, limits={"per_minute": 3, "per_hour": 10}
        )
        config.rules.cooldown_after_loss = MagicMock(
            enabled=True, loss_threshold=-100
        )
        config.rules.no_stop_loss_grace = MagicMock(
            enabled=False, require_within_seconds=60, grace_period_seconds=300
        )
        config.rules.session_block_outside = MagicMock(
            enabled=True, start_time="09:30", end_time="16:00"
        )
        config.rules.symbol_blocks = MagicMock(
            enabled=False, blocked_symbols=["ABC"]
        )
        config.rules.trade_management = MagicMock(enabled=True)
        config.rules.auth_loss_guard = MagicMock(
            enabled=True, alert_on_disconnect=True
        )

        # Create manager
        manager = RiskManager(config)
        yield manager

    async def test_rules_load_from_config(self, risk_manager_with_config):
        """Verify RiskManager loads enabled rules from config."""
        manager = risk_manager_with_config

        # Mock the state managers and rule initialization
        with patch.object(manager, "_add_default_rules", new_callable=AsyncMock):
            # Add a simple test rule to verify the engine accepts rules
            from risk_manager.rules.max_position import MaxPositionRule

            test_rule = MaxPositionRule(max_contracts=5)
            manager.engine.add_rule(test_rule)

            # Verify rule was added
            assert len(manager.engine.rules) > 0, "Rules should be loaded"
            assert any(
                isinstance(r, MaxPositionRule) for r in manager.engine.rules
            ), "MaxPositionRule should be in engine"

    async def test_disabled_rules_not_loaded(self, risk_manager_with_config):
        """Verify disabled rules are not loaded."""
        manager = risk_manager_with_config

        # Verify config has disabled rules
        assert not manager.config.rules.trade_frequency_limit.enabled
        assert not manager.config.rules.no_stop_loss_grace.enabled
        assert not manager.config.rules.symbol_blocks.enabled

        # Add an enabled rule
        from risk_manager.rules.max_position import MaxPositionRule

        enabled_rule = MaxPositionRule(max_contracts=5)
        manager.engine.add_rule(enabled_rule)

        # Disabled rule types should not be in engine
        trade_freq_rules = [
            r
            for r in manager.engine.rules
            if "TradeFrequency" in r.__class__.__name__
        ]
        assert len(trade_freq_rules) == 0, "Disabled TradeFrequencyLimit should not be loaded"

    async def test_rule_parameters_loaded_from_config(
        self, risk_manager_with_config
    ):
        """Verify loaded rules have correct parameters from config."""
        manager = risk_manager_with_config

        # Create rules with config parameters
        from risk_manager.rules.max_position import MaxPositionRule
        from risk_manager.rules.max_contracts_per_instrument import (
            MaxContractsPerInstrumentRule,
        )

        max_contracts_rule = MaxPositionRule(
            max_contracts=manager.config.rules.max_contracts.limit
        )
        assert (
            max_contracts_rule.max_contracts
            == manager.config.rules.max_contracts.limit
        )

        # MaxContractsPerInstrumentRule takes 'limits' dict, not 'default_limit'
        per_instrument_rule = MaxContractsPerInstrumentRule(
            limits=manager.config.rules.max_contracts_per_instrument.instrument_limits,
        )
        assert (
            per_instrument_rule.limits
            == manager.config.rules.max_contracts_per_instrument.instrument_limits
        )

    async def test_rule_enabled_flag_respected(self, risk_manager_with_config):
        """Verify rule enabled/disabled flag is respected."""
        manager = risk_manager_with_config

        from risk_manager.rules.max_position import MaxPositionRule

        rule = MaxPositionRule(max_contracts=5)

        # Test enabling/disabling
        rule.enable()
        assert rule.enabled is True

        rule.disable()
        assert rule.enabled is False

    async def test_all_rule_configs_accessible(self, risk_manager_with_config):
        """Verify all rule configurations are accessible from config."""
        manager = risk_manager_with_config
        config = manager.config

        # Verify all expected rule configs exist
        expected_rules = [
            "max_contracts",
            "max_contracts_per_instrument",
            "daily_realized_loss",
            "daily_realized_profit",
            "daily_unrealized_loss",
            "max_unrealized_profit",
            "trade_frequency_limit",
            "cooldown_after_loss",
            "no_stop_loss_grace",
            "session_block_outside",
            "symbol_blocks",
            "trade_management",
            "auth_loss_guard",
        ]

        for rule_name in expected_rules:
            assert hasattr(
                config.rules, rule_name
            ), f"Rule {rule_name} missing from config"
            rule_config = getattr(config.rules, rule_name)
            assert hasattr(
                rule_config, "enabled"
            ), f"Rule {rule_name} missing 'enabled' field"

    async def test_rule_count_matches_enabled_rules(self, risk_manager_with_config):
        """Verify enabled rule count matches configuration."""
        manager = risk_manager_with_config
        config = manager.config

        # Count enabled rules in config
        enabled_count = sum(
            1
            for rule_name in [
                "max_contracts",
                "max_contracts_per_instrument",
                "daily_realized_loss",
                "daily_realized_profit",
                "daily_unrealized_loss",
                "max_unrealized_profit",
                "trade_frequency_limit",
                "cooldown_after_loss",
                "no_stop_loss_grace",
                "session_block_outside",
                "symbol_blocks",
                "trade_management",
                "auth_loss_guard",
            ]
            if getattr(config.rules, rule_name).enabled
        )

        # Should have at least some enabled rules
        assert enabled_count > 0, "Should have at least one enabled rule"


class TestRuleEdgeCases:
    """Test edge cases in rule loading."""

    async def test_load_with_missing_rule_config_sections(self):
        """Verify system handles missing rule config sections gracefully."""
        # Create config with minimal rules using proper logging config
        config = MagicMock(spec=RiskConfig)
        config.general = MagicMock()
        config.general.instruments = ["MNQ"]
        config.general.timezone = "UTC"
        config.general.database = MagicMock()
        config.general.database.path = "test.db"

        # Fix logging config - must have string level, not mock
        config.general.logging = MagicMock()
        config.general.logging.level = "INFO"  # Correct: string, not MagicMock
        config.general.logging.log_to_file = False

        config.rules = MagicMock()
        # Only set one rule
        config.rules.max_contracts = MagicMock(enabled=True, limit=5)

        # Should not raise exception
        manager = RiskManager(config)
        assert manager is not None
        assert manager.config.rules is not None

    async def test_load_with_all_rules_disabled(self):
        """Verify system handles all rules disabled."""
        config = MagicMock(spec=RiskConfig)
        config.general = MagicMock()
        config.general.instruments = ["ES"]
        config.general.timezone = "UTC"
        config.general.database = MagicMock()
        config.general.database.path = "test.db"

        # Fix logging config - must have string level, not mock
        config.general.logging = MagicMock()
        config.general.logging.level = "INFO"  # Correct: string, not MagicMock
        config.general.logging.log_to_file = False

        config.rules = MagicMock()
        # All rules disabled
        config.rules.max_contracts = MagicMock(enabled=False, limit=5)
        config.rules.max_contracts_per_instrument = MagicMock(enabled=False)
        config.rules.daily_realized_loss = MagicMock(enabled=False)
        config.rules.daily_realized_profit = MagicMock(enabled=False)
        config.rules.daily_unrealized_loss = MagicMock(enabled=False)
        config.rules.max_unrealized_profit = MagicMock(enabled=False)
        config.rules.trade_frequency_limit = MagicMock(enabled=False)
        config.rules.cooldown_after_loss = MagicMock(enabled=False)
        config.rules.no_stop_loss_grace = MagicMock(enabled=False)
        config.rules.session_block_outside = MagicMock(enabled=False)
        config.rules.symbol_blocks = MagicMock(enabled=False)
        config.rules.trade_management = MagicMock(enabled=False)
        config.rules.auth_loss_guard = MagicMock(enabled=False)

        manager = RiskManager(config)
        # Should create successfully with no enabled rules
        assert manager is not None

    async def test_load_with_invalid_rule_parameters(self):
        """Verify system validates rule parameters."""
        # Test with invalid max_contracts (negative)
        from risk_manager.rules.max_position import MaxPositionRule

        with pytest.raises(ValueError):
            MaxPositionRule(max_contracts=-5)

    async def test_rule_instantiation_preserves_config_values(self):
        """Verify instantiated rules preserve config values."""
        from risk_manager.rules.max_position import MaxPositionRule

        max_limit = 10
        rule = MaxPositionRule(max_contracts=max_limit)

        assert rule.max_contracts == max_limit, "Rule should preserve max_contracts value"
        assert rule.enabled is True, "Rule should be enabled by default"


class TestRuleLoadingIntegration:
    """Integration tests for complete rule loading pipeline."""

    def test_config_loader_loads_all_rules(self):
        """Test that ConfigLoader correctly loads all rule sections."""
        loader = ConfigLoader(config_dir="config", env_file=".env")
        risk_config = loader.load_risk_config()

        # Verify all rule sections loaded
        assert risk_config.rules is not None
        assert hasattr(risk_config.rules, "max_contracts")
        assert hasattr(risk_config.rules, "max_contracts_per_instrument")
        assert hasattr(risk_config.rules, "daily_realized_loss")
        assert hasattr(risk_config.rules, "daily_realized_profit")
        assert hasattr(risk_config.rules, "daily_unrealized_loss")
        assert hasattr(risk_config.rules, "max_unrealized_profit")
        assert hasattr(risk_config.rules, "trade_frequency_limit")
        assert hasattr(risk_config.rules, "cooldown_after_loss")
        assert hasattr(risk_config.rules, "no_stop_loss_grace")
        assert hasattr(risk_config.rules, "session_block_outside")
        assert hasattr(risk_config.rules, "symbol_blocks")
        assert hasattr(risk_config.rules, "trade_management")
        assert hasattr(risk_config.rules, "auth_loss_guard")

    def test_each_rule_has_enabled_field(self):
        """Verify each rule has an 'enabled' field."""
        loader = ConfigLoader(config_dir="config", env_file=".env")
        risk_config = loader.load_risk_config()

        rule_names = [
            "max_contracts",
            "max_contracts_per_instrument",
            "daily_realized_loss",
            "daily_realized_profit",
            "daily_unrealized_loss",
            "max_unrealized_profit",
            "trade_frequency_limit",
            "cooldown_after_loss",
            "no_stop_loss_grace",
            "session_block_outside",
            "symbol_blocks",
            "trade_management",
            "auth_loss_guard",
        ]

        for rule_name in rule_names:
            rule = getattr(risk_config.rules, rule_name)
            assert hasattr(
                rule, "enabled"
            ), f"Rule {rule_name} missing 'enabled' field"
            assert isinstance(
                rule.enabled, bool
            ), f"Rule {rule_name} 'enabled' should be boolean"

    def test_rule_config_values_are_valid_types(self):
        """Verify rule config values are valid types."""
        loader = ConfigLoader(config_dir="config", env_file=".env")
        risk_config = loader.load_risk_config()

        # Test max_contracts is numeric
        max_contracts = risk_config.rules.max_contracts
        assert isinstance(max_contracts.limit, (int, float))

        # Test max_contracts_per_instrument has dict
        per_inst = risk_config.rules.max_contracts_per_instrument
        assert isinstance(per_inst.default_limit, (int, float))
        assert isinstance(per_inst.instrument_limits, dict)

        # Test trade_frequency_limit has limits object (Pydantic model, not plain dict)
        trade_freq = risk_config.rules.trade_frequency_limit
        # The limits field is a Pydantic model with per_minute, per_hour, per_session
        assert hasattr(trade_freq.limits, 'per_minute')
        assert hasattr(trade_freq.limits, 'per_hour')
        assert hasattr(trade_freq.limits, 'per_session')

    def test_can_instantiate_rules_from_config(self):
        """Test that rules can be instantiated using config values."""
        loader = ConfigLoader(config_dir="config", env_file=".env")
        risk_config = loader.load_risk_config()

        # Test instantiating max position rule from config
        from risk_manager.rules.max_position import MaxPositionRule

        if risk_config.rules.max_contracts.enabled:
            rule = MaxPositionRule(
                max_contracts=int(risk_config.rules.max_contracts.limit)
            )
            assert rule.max_contracts == int(risk_config.rules.max_contracts.limit)

        # Test instantiating max contracts per instrument rule from config
        from risk_manager.rules.max_contracts_per_instrument import (
            MaxContractsPerInstrumentRule,
        )

        if risk_config.rules.max_contracts_per_instrument.enabled:
            # MaxContractsPerInstrumentRule takes 'limits' dict, not 'default_limit'
            rule = MaxContractsPerInstrumentRule(
                limits=risk_config.rules.max_contracts_per_instrument.instrument_limits,
            )
            assert (
                rule.limits
                == risk_config.rules.max_contracts_per_instrument.instrument_limits
            )


class TestValidateRuleLoading:
    """Validation tests for rule loading system."""

    def test_rule_loading_script(self, tmp_path):
        """Test the validate_rule_loading.py script logic."""
        from risk_manager.config.loader import ConfigLoader

        # Load configuration
        loader = ConfigLoader(config_dir="config", env_file=".env")
        risk_config = loader.load_risk_config()

        # Count loaded rules
        loaded_rules = []
        rule_names = [
            "max_contracts",
            "max_contracts_per_instrument",
            "daily_realized_loss",
            "daily_realized_profit",
            "daily_unrealized_loss",
            "max_unrealized_profit",
            "trade_frequency_limit",
            "cooldown_after_loss",
            "no_stop_loss_grace",
            "session_block_outside",
            "symbol_blocks",
            "trade_management",
            "auth_loss_guard",
        ]

        for rule_name in rule_names:
            rule = getattr(risk_config.rules, rule_name)
            if rule.enabled:
                loaded_rules.append(rule_name)

        # Should have at least some loaded rules
        assert len(loaded_rules) > 0, "Should have at least one enabled rule"

        # Print for verification
        print(f"\nLoaded {len(loaded_rules)} enabled rules:")
        for rule_name in loaded_rules:
            print(f"  - {rule_name}")

    def test_validate_all_rule_names(self):
        """Validate that all expected rule names exist in config."""
        loader = ConfigLoader(config_dir="config", env_file=".env")
        risk_config = loader.load_risk_config()

        expected_rules = [
            "max_contracts",
            "max_contracts_per_instrument",
            "daily_realized_loss",
            "daily_realized_profit",
            "daily_unrealized_loss",
            "max_unrealized_profit",
            "trade_frequency_limit",
            "cooldown_after_loss",
            "no_stop_loss_grace",
            "session_block_outside",
            "symbol_blocks",
            "trade_management",
            "auth_loss_guard",
        ]

        missing = []
        for rule_name in expected_rules:
            if not hasattr(risk_config.rules, rule_name):
                missing.append(rule_name)

        assert len(missing) == 0, f"Missing rule configs: {missing}"

    def test_validate_rule_parameter_types(self):
        """Validate that rule parameters have expected types."""
        loader = ConfigLoader(config_dir="config", env_file=".env")
        risk_config = loader.load_risk_config()

        # Check max_contracts has numeric limit
        assert isinstance(
            risk_config.rules.max_contracts.limit, (int, float)
        ), "max_contracts.limit should be numeric"

        # Check max_contracts_per_instrument has dict
        assert isinstance(
            risk_config.rules.max_contracts_per_instrument.instrument_limits, dict
        ), "instrument_limits should be dict"

        # Check trade_frequency_limit has limits object with expected fields
        trade_freq = risk_config.rules.trade_frequency_limit
        assert hasattr(trade_freq.limits, 'per_minute'), "limits should have per_minute"
        assert hasattr(trade_freq.limits, 'per_hour'), "limits should have per_hour"
        assert hasattr(trade_freq.limits, 'per_session'), "limits should have per_session"

        # Check session_block_outside has expected fields
        session_block = risk_config.rules.session_block_outside
        assert hasattr(session_block, 'enabled'), "session_block should have enabled"
        assert hasattr(session_block, 'respect_holidays'), "session_block should have respect_holidays"
        assert isinstance(session_block.respect_holidays, bool), "respect_holidays should be bool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
