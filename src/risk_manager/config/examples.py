"""Example usage of the Risk Manager configuration system.

This file demonstrates:
1. Loading individual config files
2. Loading all configs at once
3. Environment variable substitution
4. Error handling
5. Accessing config values
"""

import logging
from pathlib import Path

from risk_manager.config import (
    ConfigLoader,
    ConfigurationError,
    substitute_env_vars,
    validate_env_vars,
)


# ==============================================================================
# Example 1: Load All Configs
# ==============================================================================

def example_load_all_configs():
    """Load all configuration files at once."""
    print("\n=== Example 1: Load All Configs ===\n")

    try:
        # Create loader
        loader = ConfigLoader(config_dir="config", env_file=".env")

        # Load all configs
        config = loader.load_all_configs()

        # Access configs
        print(f" Timers config loaded: {type(config['timers']).__name__}")
        print(f" Risk config loaded: {type(config['risk']).__name__}")
        print(f" Accounts config loaded: {type(config['accounts']).__name__}")

        if config['api']:
            print(f" API config loaded: {type(config['api']).__name__}")
        else:
            print("- API config not found (using defaults)")

        return config

    except ConfigurationError as e:
        print(f"L Configuration error:\n{e}")
        return None


# ==============================================================================
# Example 2: Load Individual Configs
# ==============================================================================

def example_load_individual_configs():
    """Load configuration files one at a time."""
    print("\n=== Example 2: Load Individual Configs ===\n")

    try:
        loader = ConfigLoader(config_dir="config")

        # Load timers config
        timers = loader.load_timers_config()
        print(f" Timers loaded")
        print(f"  Daily reset: {timers.daily_reset.time} {timers.daily_reset.timezone}")
        print(f"  Session hours: {timers.session_hours.start} - {timers.session_hours.end}")

        # Load risk config
        risk = loader.load_risk_config()
        print(f"\n Risk loaded")
        print(f"  Instruments: {risk.general.instruments}")
        print(f"  Max contracts: {risk.rules.max_contracts.limit}")
        print(f"  Daily loss limit: ${abs(risk.rules.daily_realized_loss.limit)}")

        # Load accounts config
        accounts = loader.load_accounts_config()
        print(f"\n Accounts loaded")
        print(f"  API URL: {accounts.topstepx.api_url}")
        print(f"  Monitored account: {accounts.monitored_account.account_id}")

        return timers, risk, accounts

    except ConfigurationError as e:
        print(f"L Configuration error:\n{e}")
        return None, None, None


# ==============================================================================
# Example 3: Environment Variable Substitution
# ==============================================================================

def example_env_var_substitution():
    """Demonstrate environment variable substitution."""
    print("\n=== Example 3: Environment Variable Substitution ===\n")

    # Example YAML with env vars
    yaml_text = """
    api:
      username: "${PROJECT_X_USERNAME}"
      api_key: "${PROJECT_X_API_KEY}"
      url: "https://api.topstepx.com"
    """

    try:
        # Substitute variables
        result = substitute_env_vars(yaml_text, env_file=".env")
        print(" Environment variables substituted:")
        print(result)

    except ValueError as e:
        print(f"L Environment variable error:\n{e}")


# ==============================================================================
# Example 4: Validate Required Environment Variables
# ==============================================================================

def example_validate_env_vars():
    """Validate that required environment variables are present."""
    print("\n=== Example 4: Validate Environment Variables ===\n")

    # Required variables for Risk Manager
    required = [
        'PROJECT_X_USERNAME',
        'PROJECT_X_API_KEY',
    ]

    missing = validate_env_vars(required, env_file=".env")

    if missing:
        print(f"L Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")

        print(f"\nFix: Create .env file with:")
        for var in missing:
            print(f"  {var}=<your-value>")
    else:
        print(" All required environment variables present!")


# ==============================================================================
# Example 5: Error Handling
# ==============================================================================

def example_error_handling():
    """Demonstrate error handling for common configuration issues."""
    print("\n=== Example 5: Error Handling ===\n")

    # Example 5a: Missing config file
    print("--- 5a: Missing config file ---")
    try:
        loader = ConfigLoader(config_dir="nonexistent_dir")
        loader.load_risk_config()
    except ConfigurationError as e:
        print(f"Caught expected error:\n{e}\n")

    # Example 5b: Invalid YAML syntax
    print("--- 5b: Invalid YAML syntax ---")
    # Create temporary invalid YAML file
    invalid_yaml = Path("config/test_invalid.yaml")
    invalid_yaml.write_text("""
    rules:
      max_contracts:
        limit: 5
          indentation_error: true  # Bad indentation
    """)

    try:
        loader = ConfigLoader(config_dir="config")
        # Would fail here due to invalid YAML
        # loader._load_yaml_file(invalid_yaml)
        print("(Skipping actual test to avoid file creation)")
    except ConfigurationError as e:
        print(f"Caught expected error:\n{e}\n")
    finally:
        # Clean up
        if invalid_yaml.exists():
            invalid_yaml.unlink()

    # Example 5c: Missing environment variable
    print("--- 5c: Missing environment variable ---")
    yaml_with_missing_var = "${NONEXISTENT_VAR}"
    try:
        result = substitute_env_vars(yaml_with_missing_var, env_file=".env")
    except ValueError as e:
        print(f"Caught expected error:\n{e}\n")

    # Example 5d: Validation error (negative value should be positive)
    print("--- 5d: Validation error ---")
    print("(Would occur if Pydantic validation fails)")
    print("Example: daily_realized_loss.limit = 500.0 (should be negative)")
    print("Error: Daily loss limit must be negative\n")


# ==============================================================================
# Example 6: Accessing Config Values
# ==============================================================================

def example_access_config_values():
    """Show how to access configuration values."""
    print("\n=== Example 6: Access Config Values ===\n")

    try:
        loader = ConfigLoader(config_dir="config")
        config = loader.load_all_configs()

        timers = config['timers']
        risk = config['risk']
        accounts = config['accounts']

        # Access nested values
        print("--- Daily Reset Settings ---")
        print(f"Time: {timers.daily_reset.time}")
        print(f"Timezone: {timers.daily_reset.timezone}")
        print(f"Enabled: {timers.daily_reset.enabled}")

        print("\n--- Session Hours ---")
        print(f"Start: {timers.session_hours.start}")
        print(f"End: {timers.session_hours.end}")
        print(f"Timezone: {timers.session_hours.timezone}")
        print(f"Allowed days: {timers.session_hours.allowed_days}")

        print("\n--- Risk Rules ---")
        print(f"Max contracts: {risk.rules.max_contracts.limit}")
        print(f"Daily loss limit: ${abs(risk.rules.daily_realized_loss.limit)}")
        print(f"Daily profit target: ${risk.rules.daily_realized_profit.target}")

        print("\n--- Account Info ---")
        print(f"API URL: {accounts.topstepx.api_url}")
        print(f"WebSocket URL: {accounts.topstepx.websocket_url}")
        print(f"Account ID: {accounts.monitored_account.account_id}")
        print(f"Account type: {accounts.monitored_account.account_type}")

        # Convert to dictionary if needed
        print("\n--- Convert to Dict ---")
        timers_dict = timers.model_dump()
        print(f"Timers as dict: {list(timers_dict.keys())}")

    except ConfigurationError as e:
        print(f"L Error: {e}")


# ==============================================================================
# Example 7: Multi-Account Configuration
# ==============================================================================

def example_multi_account():
    """Demonstrate multi-account configuration loading."""
    print("\n=== Example 7: Multi-Account Configuration ===\n")

    try:
        loader = ConfigLoader(config_dir="config")
        accounts = loader.load_accounts_config()

        # Check if multi-account mode
        if hasattr(accounts, 'accounts') and accounts.accounts:
            print(f" Multi-account mode: {len(accounts.accounts)} accounts")

            for i, account in enumerate(accounts.accounts, 1):
                print(f"\nAccount {i}:")
                print(f"  ID: {account.id}")
                print(f"  Name: {account.name}")
                print(f"  Type: {account.account_type}")

                if account.risk_config_file:
                    print(f"  Config: {account.risk_config_file}")
                elif account.config_overrides:
                    print(f"  Overrides: {len(account.config_overrides)} rules")
                else:
                    print(f"  Config: Using default risk_config.yaml")
        else:
            print(" Single account mode")
            print(f"  Account ID: {accounts.monitored_account.account_id}")

    except ConfigurationError as e:
        print(f"L Error: {e}")


# ==============================================================================
# Example 8: Custom Config Directory
# ==============================================================================

def example_custom_config_dir():
    """Load configs from custom directory."""
    print("\n=== Example 8: Custom Config Directory ===\n")

    # Use custom config directory
    custom_dir = Path("config/custom")

    if custom_dir.exists():
        try:
            loader = ConfigLoader(config_dir=custom_dir, env_file=".env")
            config = loader.load_all_configs()
            print(f" Loaded configs from: {custom_dir}")

        except ConfigurationError as e:
            print(f"L Error: {e}")
    else:
        print(f"Custom config directory not found: {custom_dir}")
        print("Using default: config/")


# ==============================================================================
# Main
# ==============================================================================

def main():
    """Run all examples."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    print("=" * 70)
    print("Risk Manager V34 - Configuration System Examples")
    print("=" * 70)

    # Run examples
    example_load_all_configs()
    example_load_individual_configs()
    example_env_var_substitution()
    example_validate_env_vars()
    example_error_handling()
    example_access_config_values()
    example_multi_account()
    example_custom_config_dir()

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
