#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Standalone validation script for rule loading from configuration.

This script verifies that:
1. All rules can be loaded from config files
2. Each rule has required configuration fields
3. Rule parameters are correctly typed
4. Enabled rules can be instantiated

Usage:
    python validate_rule_loading.py
    python validate_rule_loading.py --verbose
    python validate_rule_loading.py --check-instantiation
"""

import sys
import io
from pathlib import Path
from typing import Optional, Dict, List
import argparse

# Fix Unicode on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from risk_manager.config.loader import ConfigLoader, ConfigurationError


class RuleLoadingValidator:
    """Validates rule loading and configuration."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.loaded_rules: List[Dict] = []
        self.config = None

    def load_config(self) -> bool:
        """Load configuration from files."""
        try:
            loader = ConfigLoader(config_dir="config", env_file=".env")
            self.config = loader.load_risk_config()
            if self.verbose:
                print("✅ Configuration loaded successfully")
            return True
        except ConfigurationError as e:
            self.errors.append(f"Failed to load configuration: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Unexpected error loading config: {e}")
            return False

    def validate_rule_sections_exist(self) -> bool:
        """Verify all expected rule sections exist in config."""
        if not self.config or not self.config.rules:
            self.errors.append("Rules section missing from configuration")
            return False

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

        missing_rules = []
        for rule_name in expected_rules:
            if not hasattr(self.config.rules, rule_name):
                missing_rules.append(rule_name)

        if missing_rules:
            self.errors.append(f"Missing rule configs: {', '.join(missing_rules)}")
            return False

        if self.verbose:
            print(f"✅ All {len(expected_rules)} expected rule sections found")
        return True

    def validate_rule_fields(self) -> bool:
        """Verify each rule has required fields."""
        required_fields = {
            "max_contracts": ["enabled", "limit"],
            "max_contracts_per_instrument": ["enabled", "default_limit", "instrument_limits"],
            "daily_realized_loss": ["enabled", "limit"],
            "daily_realized_profit": ["enabled", "target"],
            "daily_unrealized_loss": ["enabled", "limit"],
            "max_unrealized_profit": ["enabled", "target"],
            "trade_frequency_limit": ["enabled", "limits"],
            "cooldown_after_loss": ["enabled", "loss_threshold"],
            "no_stop_loss_grace": ["enabled"],
            "session_block_outside": ["enabled", "respect_holidays"],  # Not start_time/end_time
            "symbol_blocks": ["enabled", "blocked_symbols"],
            "trade_management": ["enabled"],
            "auth_loss_guard": ["enabled"],
        }

        all_valid = True
        for rule_name, required_fields_list in required_fields.items():
            rule = getattr(self.config.rules, rule_name)

            for field_name in required_fields_list:
                if not hasattr(rule, field_name):
                    self.errors.append(
                        f"Rule '{rule_name}' missing required field: {field_name}"
                    )
                    all_valid = False

        if all_valid and self.verbose:
            print(f"✅ All rules have required fields")

        return all_valid

    def validate_rule_types(self) -> bool:
        """Verify rule parameters have correct types."""
        type_checks = [
            ("max_contracts", "enabled", bool),
            ("max_contracts", "limit", (int, float)),
            ("max_contracts_per_instrument", "enabled", bool),
            ("max_contracts_per_instrument", "default_limit", (int, float)),
            ("max_contracts_per_instrument", "instrument_limits", dict),
            ("daily_realized_loss", "enabled", bool),
            ("daily_realized_loss", "limit", (int, float)),
            ("daily_realized_profit", "enabled", bool),
            ("daily_realized_profit", "target", (int, float)),
            ("daily_unrealized_loss", "enabled", bool),
            ("daily_unrealized_loss", "limit", (int, float)),
            ("max_unrealized_profit", "enabled", bool),
            ("max_unrealized_profit", "target", (int, float)),
            ("trade_frequency_limit", "enabled", bool),
            # Note: limits is a Pydantic model, not a dict
            ("cooldown_after_loss", "enabled", bool),
            ("cooldown_after_loss", "loss_threshold", (int, float)),
            ("no_stop_loss_grace", "enabled", bool),
            ("session_block_outside", "enabled", bool),
            ("session_block_outside", "start_time", str),
            ("session_block_outside", "end_time", str),
            ("symbol_blocks", "enabled", bool),
            ("symbol_blocks", "blocked_symbols", (list, type(None))),
            ("trade_management", "enabled", bool),
            ("auth_loss_guard", "enabled", bool),
        ]

        all_valid = True
        for rule_name, field_name, expected_type in type_checks:
            rule = getattr(self.config.rules, rule_name)
            value = getattr(rule, field_name, None)

            if value is not None and not isinstance(value, expected_type):
                self.errors.append(
                    f"Rule '{rule_name}' field '{field_name}' has wrong type: "
                    f"expected {expected_type}, got {type(value).__name__}"
                )
                all_valid = False

        if all_valid and self.verbose:
            print(f"✅ All rule parameter types are correct")

        return all_valid

    def count_enabled_rules(self) -> int:
        """Count how many rules are enabled."""
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

        enabled_count = 0
        self.loaded_rules = []

        for rule_name in rule_names:
            rule = getattr(self.config.rules, rule_name)
            if rule.enabled:
                enabled_count += 1
                self.loaded_rules.append({
                    "name": rule_name,
                    "enabled": True,
                    "config": rule
                })
            else:
                self.loaded_rules.append({
                    "name": rule_name,
                    "enabled": False,
                    "config": rule
                })

        return enabled_count

    def validate_rule_instantiation(self) -> bool:
        """Test instantiating rules with config values."""
        try:
            # Test instantiating a few key rules
            from risk_manager.rules.max_position import MaxPositionRule
            from risk_manager.rules.max_contracts_per_instrument import (
                MaxContractsPerInstrumentRule,
            )

            # MaxPositionRule
            if self.config.rules.max_contracts.enabled:
                rule = MaxPositionRule(
                    max_contracts=int(self.config.rules.max_contracts.limit)
                )
                assert rule.max_contracts == int(
                    self.config.rules.max_contracts.limit
                )
                if self.verbose:
                    print(f"✅ MaxPositionRule instantiated: limit={rule.max_contracts}")

            # MaxContractsPerInstrumentRule (takes 'limits' dict, not 'default_limit')
            if self.config.rules.max_contracts_per_instrument.enabled:
                rule = MaxContractsPerInstrumentRule(
                    limits=self.config.rules.max_contracts_per_instrument.instrument_limits,
                )
                if self.verbose:
                    print(
                        f"✅ MaxContractsPerInstrumentRule instantiated: "
                        f"limits={rule.limits}"
                    )

            return True

        except Exception as e:
            self.errors.append(f"Failed to instantiate rules: {e}")
            return False

    def print_results(self) -> None:
        """Print validation results."""
        print("\n" + "=" * 80)
        print("RULE LOADING VALIDATION RESULTS")
        print("=" * 80 + "\n")

        # Print summary
        print("SUMMARY")
        print("-" * 80)
        if not self.errors and not self.warnings:
            print("✅ ALL VALIDATIONS PASSED!\n")
        else:
            if self.errors:
                print(f"❌ ERRORS: {len(self.errors)}")
            if self.warnings:
                print(f"⚠️  WARNINGS: {len(self.warnings)}\n")

        # Print enabled rules
        print("\nENABLED RULES")
        print("-" * 80)
        enabled_rules = [r for r in self.loaded_rules if r["enabled"]]
        if enabled_rules:
            print(f"✅ {len(enabled_rules)} rules enabled:\n")
            for rule in enabled_rules:
                print(f"  ✅ {rule['name']}")
        else:
            print("⚠️  No rules enabled!")

        # Print disabled rules
        print("\n\nDISABLED RULES")
        print("-" * 80)
        disabled_rules = [r for r in self.loaded_rules if not r["enabled"]]
        if disabled_rules:
            print(f"📵 {len(disabled_rules)} rules disabled:\n")
            for rule in disabled_rules:
                print(f"  📵 {rule['name']}")

        # Print errors
        if self.errors:
            print("\n\nERRORS")
            print("-" * 80)
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. ❌ {error}")

        # Print warnings
        if self.warnings:
            print("\n\nWARNINGS")
            print("-" * 80)
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. ⚠️  {warning}")

        # Print rule details if verbose
        if self.verbose:
            print("\n\nDETAILED RULE CONFIGURATION")
            print("-" * 80)
            for rule in self.loaded_rules:
                print(f"\n{rule['name']}:")
                print(f"  enabled: {rule['enabled']}")
                rule_config = rule['config']
                for attr in dir(rule_config):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(rule_config, attr)
                            if not callable(value):
                                print(f"  {attr}: {value}")
                        except:
                            pass

        print("\n" + "=" * 80)
        print("END VALIDATION RESULTS")
        print("=" * 80 + "\n")

    def validate_all(self) -> bool:
        """Run all validations."""
        print("Starting rule loading validation...\n")

        checks = [
            ("Loading configuration", self.load_config),
            ("Validating rule sections exist", self.validate_rule_sections_exist),
            ("Validating rule fields", self.validate_rule_fields),
            ("Validating rule parameter types", self.validate_rule_types),
        ]

        all_passed = True
        for check_name, check_func in checks:
            if self.verbose:
                print(f"\n{check_name}...")
            if not check_func():
                all_passed = False

        # Always count and try instantiation
        self.count_enabled_rules()
        self.validate_rule_instantiation()

        return all_passed and len(self.errors) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate rule loading from configuration"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed output"
    )
    parser.add_argument(
        "--check-instantiation",
        action="store_true",
        help="Test instantiating rules (requires full dependencies)"
    )

    args = parser.parse_args()

    validator = RuleLoadingValidator(verbose=args.verbose)
    success = validator.validate_all()

    if args.check_instantiation:
        if args.verbose:
            print("\n\nTesting rule instantiation...")
        validator.validate_rule_instantiation()

    validator.print_results()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
