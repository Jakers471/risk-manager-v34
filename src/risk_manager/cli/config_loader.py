"""Configuration loader for run_dev.py and runtime operations.

Provides high-level configuration loading for development and production:
- Risk configuration (rules, limits, settings)
- Accounts configuration (multi-account support)
- Account selection (interactive or explicit)
- Validation and error handling

Builds on top of:
- src/risk_manager/config/loader.py (ConfigLoader - low-level YAML parsing)
- src/risk_manager/cli/credential_manager.py (credentials)
"""

import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from ..config.loader import ConfigLoader, ConfigurationError
from ..config.models import RiskConfig, AccountsConfig
from .credential_manager import get_credentials, ProjectXCredentials, CredentialError

logger = logging.getLogger(__name__)
console = Console()


class RuntimeConfigError(Exception):
    """Raised when runtime configuration loading fails."""
    pass


class RuntimeConfig:
    """Complete runtime configuration for Risk Manager.

    Contains everything needed to start the risk manager:
    - Risk configuration (rules, limits, timers)
    - Account configuration (which account to monitor)
    - Credentials (API keys)
    - Config paths for reference

    Attributes:
        risk_config: RiskConfig instance (validated)
        accounts_config: AccountsConfig instance (validated)
        credentials: ProjectXCredentials instance
        selected_account_id: Account ID to monitor
        config_dir: Path to config directory
        risk_config_path: Path to risk_config.yaml
        accounts_config_path: Path to accounts.yaml
    """

    def __init__(
        self,
        risk_config: RiskConfig,
        accounts_config: AccountsConfig,
        credentials: ProjectXCredentials,
        selected_account_id: str,
        config_dir: Path,
        risk_config_path: Path,
        accounts_config_path: Path,
        timers_config=None  # Optional timers config
    ):
        """Initialize runtime configuration."""
        self.risk_config = risk_config
        self.accounts_config = accounts_config
        self.credentials = credentials
        self.selected_account_id = selected_account_id
        self.config_dir = config_dir
        self.risk_config_path = risk_config_path
        self.accounts_config_path = accounts_config_path
        self.timers_config = timers_config

    def __repr__(self) -> str:
        """String representation for logging."""
        return (
            f"RuntimeConfig("
            f"account={self.selected_account_id}, "
            f"config_dir={self.config_dir}, "
            f"credentials=***)"
        )


def load_runtime_config(
    config_path: Optional[str | Path] = None,
    accounts_path: Optional[str | Path] = None,
    account_id: Optional[str] = None,
    env_file: str | Path = ".env",
    interactive: bool = True
) -> RuntimeConfig:
    """Load complete runtime configuration for Risk Manager.

    This is the main entry point for loading configuration in run_dev.py.

    Args:
        config_path: Path to risk_config.yaml (default: config/risk_config.yaml)
        accounts_path: Path to accounts.yaml (default: config/accounts.yaml)
        account_id: Account ID to monitor (default: interactive prompt if multiple)
        env_file: Path to .env file for credentials (default: .env)
        interactive: If True, prompt user for account selection (default: True)

    Returns:
        RuntimeConfig instance with all configuration loaded and validated

    Raises:
        RuntimeConfigError: If any configuration loading fails
        CredentialError: If credentials are missing or invalid
        ConfigurationError: If config files are invalid

    Example:
        # Load with defaults (interactive)
        config = load_runtime_config()

        # Load with explicit account
        config = load_runtime_config(account_id="PRAC-V2-126244")

        # Load with custom config path
        config = load_runtime_config(
            config_path="custom/risk_config.yaml",
            account_id="PRAC-V2-126244"
        )

    Usage in run_dev.py:
        from risk_manager.cli.config_loader import load_runtime_config

        # Load configuration
        config = load_runtime_config(
            config_path=args.config,  # From CLI --config flag
            account_id=args.account,  # From CLI --account flag
            interactive=True
        )

        # Use configuration
        risk_manager = RiskManager(
            config=config.risk_config,
            account_id=config.selected_account_id,
            credentials=config.credentials
        )
    """
    console.print("[cyan]Loading runtime configuration...[/cyan]")
    console.print()

    # Resolve paths
    config_dir = Path("config")
    risk_config_path = Path(config_path) if config_path else config_dir / "risk_config.yaml"
    accounts_config_path = Path(accounts_path) if accounts_path else config_dir / "accounts.yaml"

    # 1. Load credentials first (fail fast if missing)
    console.print("[bold]1. Loading credentials[/bold]")
    try:
        credentials = get_credentials(env_file=env_file)
        console.print(f"   OK: Credentials loaded for user: {credentials._redact(credentials.username)}")
    except CredentialError as e:
        console.print(f"[red]   FAIL: Credential loading failed[/red]")
        raise RuntimeConfigError(f"Credential loading failed:\n{e}")

    console.print()

    # 2. Load risk configuration
    console.print("[bold]2. Loading risk configuration[/bold]")
    console.print(f"   File: {risk_config_path.absolute()}")

    try:
        loader = ConfigLoader(config_dir=risk_config_path.parent, env_file=env_file)
        risk_config = loader.load_risk_config(file_name=risk_config_path.name)
        console.print(f"   OK: Risk configuration loaded")

        # Count enabled rules
        enabled_count = sum(
            1 for rule_name in dir(risk_config.rules)
            if not rule_name.startswith("_")
            and hasattr(getattr(risk_config.rules, rule_name), "enabled")
            and getattr(risk_config.rules, rule_name).enabled
        )
        console.print(f"   OK: Enabled rules: {enabled_count}")

    except ConfigurationError as e:
        console.print(f"[red]   FAIL: Risk configuration loading failed[/red]")
        raise RuntimeConfigError(f"Risk configuration error:\n{e}")

    console.print()

    # 2b. Load timers configuration (optional)
    console.print("[bold]2b. Loading timers configuration[/bold]")
    timers_config = None
    timers_config_path = config_dir / "timers_config.yaml"

    if timers_config_path.exists():
        console.print(f"   File: {timers_config_path.absolute()}")
        try:
            timers_config = loader.load_timers_config()
            console.print(f"   OK: Timers configuration loaded")
            console.print(f"   OK: Daily reset: {timers_config.daily_reset.time} {timers_config.daily_reset.timezone}")
        except Exception as e:
            console.print(f"[yellow]   WARN: Timers configuration loading failed: {e}[/yellow]")
            console.print(f"[yellow]   Timer-based rules will be skipped[/yellow]")
    else:
        console.print(f"   SKIP: timers_config.yaml not found (timer-based rules will be skipped)")

    console.print()

    # 3. Load accounts configuration
    console.print("[bold]3. Loading accounts configuration[/bold]")
    console.print(f"   File: {accounts_config_path.absolute()}")

    try:
        loader = ConfigLoader(config_dir=accounts_config_path.parent, env_file=env_file)
        accounts_config = loader.load_accounts_config(file_name=accounts_config_path.name)
        console.print(f"   OK: Accounts configuration loaded")

    except ConfigurationError as e:
        console.print(f"[red]   FAIL: Accounts configuration loading failed[/red]")
        raise RuntimeConfigError(f"Accounts configuration error:\n{e}")

    console.print()

    # 4. Select account
    console.print("[bold]4. Selecting account[/bold]")

    try:
        selected_account_id = select_account(
            accounts_config=accounts_config,
            account_id=account_id,
            interactive=interactive
        )
        console.print(f"   OK: Selected account: {selected_account_id}")

    except Exception as e:
        console.print(f"[red]   FAIL: Account selection failed[/red]")
        raise RuntimeConfigError(f"Account selection error:\n{e}")

    console.print()

    # 5. Deep validation of critical paths
    console.print("[bold]5. Validating configuration structure[/bold]")

    try:
        _validate_config_structure(risk_config, accounts_config)
        console.print(f"   OK: Configuration structure validated")

    except Exception as e:
        console.print(f"[red]   FAIL: Configuration structure validation failed[/red]")
        raise RuntimeConfigError(f"Configuration structure error:\n{e}")

    console.print()
    console.print("[green]OK: Runtime configuration loaded successfully![/green]")
    console.print()

    # Create RuntimeConfig object
    return RuntimeConfig(
        risk_config=risk_config,
        accounts_config=accounts_config,
        credentials=credentials,
        selected_account_id=selected_account_id,
        config_dir=config_dir,
        risk_config_path=risk_config_path,
        accounts_config_path=accounts_config_path,
        timers_config=timers_config
    )


def select_account(
    accounts_config: AccountsConfig,
    account_id: Optional[str] = None,
    interactive: bool = True
) -> str:
    """Select account to monitor from accounts configuration.

    Args:
        accounts_config: AccountsConfig instance
        account_id: Explicit account ID (default: None for interactive)
        interactive: If True, prompt user if account_id not provided (default: True)

    Returns:
        Selected account ID

    Raises:
        RuntimeConfigError: If account selection fails or account not found

    Example:
        # Explicit selection
        account_id = select_account(accounts_config, account_id="PRAC-V2-126244")

        # Interactive selection
        account_id = select_account(accounts_config, interactive=True)
    """
    # Get available accounts
    available_accounts = _get_available_accounts(accounts_config)

    if not available_accounts:
        raise RuntimeConfigError(
            "No accounts configured in accounts.yaml\n\n"
            "Fix: Add at least one account to accounts.yaml:\n"
            "  accounts:\n"
            "    - account_id: PRAC-V2-XXXXXX\n"
            "      enabled: true\n"
            "      name: Practice Account\n"
        )

    # If explicit account_id provided, validate it exists
    if account_id:
        if account_id not in [acc["account_id"] for acc in available_accounts]:
            raise RuntimeConfigError(
                f"Account not found: {account_id}\n\n"
                f"Available accounts:\n" +
                "\n".join(f"  - {acc['account_id']}: {acc.get('name', 'N/A')}" for acc in available_accounts)
            )
        return account_id

    # Single account - auto-select
    if len(available_accounts) == 1:
        account_id = available_accounts[0]["account_id"]
        console.print(f"   Auto-selected (only account): {account_id}")
        return account_id

    # Multiple accounts - require selection
    if not interactive:
        raise RuntimeConfigError(
            "Multiple accounts configured but no account_id provided.\n\n"
            "Fix: Specify account with --account flag:\n"
            "  run_dev.py --account PRAC-V2-126244\n\n"
            f"Available accounts:\n" +
            "\n".join(f"  - {acc['account_id']}: {acc.get('name', 'N/A')}" for acc in available_accounts)
        )

    # Interactive prompt
    console.print()
    console.print("[yellow]Multiple accounts available. Please select one:[/yellow]")
    console.print()

    # Display table of accounts
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Account ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="green")

    for idx, account in enumerate(available_accounts, 1):
        table.add_row(
            str(idx),
            account["account_id"],
            account.get("name", "N/A"),
            "Enabled" if account.get("enabled", True) else "Disabled"
        )

    console.print(table)
    console.print()

    # Prompt for selection
    while True:
        choice = Prompt.ask(
            "Select account",
            choices=[str(i) for i in range(1, len(available_accounts) + 1)]
        )

        idx = int(choice) - 1
        selected = available_accounts[idx]
        account_id = selected["account_id"]

        console.print(f"   Selected: {account_id} ({selected.get('name', 'N/A')})")
        return account_id


def _get_available_accounts(accounts_config: AccountsConfig) -> list[dict]:
    """Extract list of available accounts from config.

    Args:
        accounts_config: AccountsConfig instance

    Returns:
        List of account dictionaries with keys: account_id, name, enabled

    Note:
        Supports both simple mode (monitored_account) and multi-account mode (accounts list).
    """
    available = []

    # Simple mode: single monitored_account
    if accounts_config.monitored_account:
        available.append({
            "account_id": accounts_config.monitored_account.account_id,
            "name": accounts_config.monitored_account.description or "Primary Account",
            "enabled": True
        })

    # Multi-account mode: accounts list
    if accounts_config.accounts:
        for account in accounts_config.accounts:
            available.append({
                "account_id": account.id,
                "name": account.name,
                "enabled": True  # Only enabled accounts in config
            })

    return available


def _validate_config_structure(risk_config: RiskConfig, accounts_config: AccountsConfig) -> None:
    """Validate critical configuration structure paths.

    This catches structural issues early before they cause runtime errors.

    Args:
        risk_config: RiskConfig instance to validate
        accounts_config: AccountsConfig instance to validate

    Raises:
        RuntimeConfigError: If any critical path is missing or invalid

    Validates:
    - risk_config.general exists and has instruments, timezone, logging
    - risk_config.rules exists and has all expected rules
    - Each rule has 'enabled' field
    - accounts_config.topstepx exists and has credentials
    """
    errors = []

    # Validate risk_config.general
    if not hasattr(risk_config, 'general') or risk_config.general is None:
        errors.append("risk_config.general is missing")
    else:
        if not hasattr(risk_config.general, 'instruments'):
            errors.append("risk_config.general.instruments is missing")
        elif not isinstance(risk_config.general.instruments, list):
            errors.append(f"risk_config.general.instruments should be list, got {type(risk_config.general.instruments)}")
        elif len(risk_config.general.instruments) == 0:
            errors.append("risk_config.general.instruments is empty")

        if not hasattr(risk_config.general, 'timezone'):
            errors.append("risk_config.general.timezone is missing")

        if not hasattr(risk_config.general, 'logging'):
            errors.append("risk_config.general.logging is missing")

    # Validate risk_config.rules
    if not hasattr(risk_config, 'rules') or risk_config.rules is None:
        errors.append("risk_config.rules is missing")
    else:
        # Check critical rules exist
        critical_rules = [
            'max_contracts',
            'max_contracts_per_instrument',
            'daily_unrealized_loss',
            'max_unrealized_profit',
            'daily_realized_loss',
            'daily_realized_profit',
            'trade_frequency_limit',
            'cooldown_after_loss',
            'session_block_outside',
            'auth_loss_guard',
            'no_stop_loss_grace',
            'symbol_blocks',
            'trade_management'
        ]

        for rule_name in critical_rules:
            if not hasattr(risk_config.rules, rule_name):
                errors.append(f"risk_config.rules.{rule_name} is missing")
            else:
                rule = getattr(risk_config.rules, rule_name)
                if not hasattr(rule, 'enabled'):
                    errors.append(f"risk_config.rules.{rule_name}.enabled is missing")

    # Validate accounts_config.topstepx
    if not hasattr(accounts_config, 'topstepx') or accounts_config.topstepx is None:
        errors.append("accounts_config.topstepx is missing")
    else:
        if not hasattr(accounts_config.topstepx, 'username'):
            errors.append("accounts_config.topstepx.username is missing")
        if not hasattr(accounts_config.topstepx, 'api_key'):
            errors.append("accounts_config.topstepx.api_key is missing")
        if not hasattr(accounts_config.topstepx, 'api_url'):
            errors.append("accounts_config.topstepx.api_url is missing")

    # If any errors, raise with helpful message
    if errors:
        raise RuntimeConfigError(
            "Configuration structure validation failed:\n" +
            "\n".join(f"  - {e}" for e in errors) +
            "\n\nFix: Check that config files match the expected structure.\n"
            "See docs/current/CONFIG_FORMATS.md for examples."
        )


def validate_runtime_config(config: RuntimeConfig) -> bool:
    """Validate runtime configuration is ready for use.

    Args:
        config: RuntimeConfig instance to validate

    Returns:
        True if valid

    Raises:
        RuntimeConfigError: If validation fails

    Validations:
    - Risk config is present
    - Accounts config is present
    - Credentials are present
    - Selected account ID is valid
    - Config files exist
    """
    errors = []

    if not config.risk_config:
        errors.append("Risk configuration is missing")

    if not config.accounts_config:
        errors.append("Accounts configuration is missing")

    if not config.credentials:
        errors.append("Credentials are missing")

    if not config.selected_account_id:
        errors.append("No account selected")

    if not config.risk_config_path.exists():
        errors.append(f"Risk config file not found: {config.risk_config_path}")

    if not config.accounts_config_path.exists():
        errors.append(f"Accounts config file not found: {config.accounts_config_path}")

    # Validate selected account exists in config
    available_accounts = _get_available_accounts(config.accounts_config)
    if config.selected_account_id not in [acc["account_id"] for acc in available_accounts]:
        errors.append(f"Selected account not found in config: {config.selected_account_id}")

    if errors:
        raise RuntimeConfigError(
            "Runtime configuration validation failed:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    return True


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    try:
        # Load runtime configuration (interactive)
        print("="*60)
        print("Risk Manager V34 - Configuration Loader Test")
        print("="*60)
        print()

        config = load_runtime_config(interactive=True)

        print()
        print("="*60)
        print("Configuration loaded successfully!")
        print("="*60)
        print()
        print(f"Selected Account: {config.selected_account_id}")
        print(f"Risk Config: {config.risk_config_path}")
        print(f"Accounts Config: {config.accounts_config_path}")
        print(f"Credentials: {config.credentials}")
        print()

        # Validate
        print("Validating configuration...")
        validate_runtime_config(config)
        print("✓ Configuration is valid and ready to use")

    except RuntimeConfigError as e:
        print(f"\nRuntime Configuration Error:\n{e}")
    except Exception as e:
        print(f"\nUnexpected Error:\n{e}")
        import traceback
        traceback.print_exc()
