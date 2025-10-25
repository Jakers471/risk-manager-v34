# Accounts Configuration Schema

**Document Type**: Unified Configuration Specification
**Created**: 2025-10-25
**Researcher**: Wave 3 Researcher 5 - Configuration System Specification Unification
**Status**: PRODUCTION READY

---

## Executive Summary

This document defines the **accounts configuration schema** for Risk Manager V34. Supports multiple trading accounts with individual risk profiles and per-account configuration overrides.

---

## Complete YAML Schema

**File**: `config/accounts.yaml`

```yaml
# ==============================================================================
# ACCOUNTS CONFIGURATION
# ==============================================================================
# Purpose: API credentials + multi-account support with per-account overrides
# Security: KEEP THIS FILE SECURE - Contains API credentials
# ==============================================================================

# ==============================================================================
# API CREDENTIALS
# ==============================================================================
topstepx:
  # API credentials
  username: "${PROJECT_X_USERNAME}"  # From .env or hardcode
  api_key: "${PROJECT_X_API_KEY}"    # From .env or hardcode

  # API endpoints
  api_url: "https://api.topstepx.com/api"
  websocket_url: "wss://api.topstepx.com"

# ==============================================================================
# MONITORED ACCOUNTS (Single Account Mode)
# ==============================================================================
monitored_account:
  account_id: "PRAC-V2-126244-84184528"
  account_type: "practice"           # "practice" or "live"
  description: "Jake's Practice Account"

# ==============================================================================
# MULTI-ACCOUNT CONFIGURATION (Optional - Advanced)
# ==============================================================================
accounts:
  # Account 1: Conservative Trader
  - id: "PRAC-V2-126244-84184528"
    name: "Trader A - Conservative"
    account_type: "practice"
    description: "Conservative risk profile"

    # Option 1: Use custom risk config file
    risk_config_file: null          # null = use default risk_config.yaml

    # Option 2: Override specific rules
    config_overrides:
      rules:
        daily_realized_loss:
          limit: -200.0              # Stricter than default
        max_contracts:
          limit: 2                   # Conservative
        daily_realized_profit:
          target: 400.0              # Lower target

  # Account 2: Aggressive Trader
  - id: "PRAC-V2-126244-84184529"
    name: "Trader B - Aggressive"
    account_type: "live"
    description: "Aggressive risk profile"

    # Use separate config file
    risk_config_file: "config/trader_b_rules.yaml"
    config_overrides: null           # null = use file as-is

  # Account 3: Default Settings
  - id: "PRAC-V2-126244-84184530"
    name: "Trader C - Default"
    account_type: "practice"
    description: "Uses default risk_config.yaml"

    risk_config_file: null           # Use default
    config_overrides: null           # No overrides
```

---

## Schema Details

### 1. API Credentials

```yaml
topstepx:
  username: "${PROJECT_X_USERNAME}"  # REQUIRED
  api_key: "${PROJECT_X_API_KEY}"    # REQUIRED
  api_url: "https://api.topstepx.com/api"      # REQUIRED
  websocket_url: "wss://api.topstepx.com"      # REQUIRED
```

**Validation**:
- `username` MUST be non-empty string
- `api_key` MUST be non-empty string
- Environment variable substitution: `${VAR_NAME}` replaced with `os.getenv("VAR_NAME")`
- URLs MUST be valid HTTPS/WSS URLs

### 2. Single Account (Simple Mode)

```yaml
monitored_account:
  account_id: "PRAC-V2-126244-84184528"  # REQUIRED
  account_type: "practice"                # REQUIRED: "practice" or "live"
  description: "Optional description"     # OPTIONAL
```

**Validation**:
- `account_id` MUST match TopstepX account ID format
- `account_type` MUST be "practice" or "live"

### 3. Multi-Account Configuration

```yaml
accounts:
  - id: "ACCOUNT-ID"                     # REQUIRED: Account ID
    name: "Human Name"                   # REQUIRED: Display name
    account_type: "practice"             # REQUIRED: "practice" or "live"
    description: "Optional description"   # OPTIONAL

    # Configuration options (pick one)
    risk_config_file: "path.yaml"        # Custom config file
    config_overrides:                    # OR: Override specific rules
      rules:
        rule_name:
          parameter: value
```

**Configuration Patterns**:

**Pattern 1: Custom Config File**
```yaml
- id: "ACCOUNT-001"
  name: "Custom Rules"
  risk_config_file: "config/custom_rules.yaml"
  config_overrides: null
```

**Pattern 2: Override Specific Rules**
```yaml
- id: "ACCOUNT-002"
  name: "Override Limits"
  risk_config_file: null
  config_overrides:
    rules:
      daily_realized_loss:
        limit: -300.0                    # Override just this
      max_contracts:
        limit: 3                         # And this
```

**Pattern 3: Use Defaults**
```yaml
- id: "ACCOUNT-003"
  name: "Default Settings"
  risk_config_file: null
  config_overrides: null                 # Use risk_config.yaml as-is
```

**Validation**:
- `id` MUST be unique across all accounts
- `name` MUST be non-empty string
- Cannot specify both `risk_config_file` AND `config_overrides` (pick one)
- If `risk_config_file` specified, file MUST exist
- `config_overrides` MUST be valid YAML matching risk_config schema

---

## Configuration Loading Logic

### 1. Single Account Mode

```python
# Load accounts.yaml
config = yaml.safe_load(open('config/accounts.yaml'))

# Simple mode: Use monitored_account
account_id = config['monitored_account']['account_id']
risk_config = load_risk_config('config/risk_config.yaml')

# Apply to risk engine
engine.set_config(account_id, risk_config)
```

### 2. Multi-Account Mode

```python
# Load base risk config
base_config = load_risk_config('config/risk_config.yaml')

# Load accounts
accounts_config = yaml.safe_load(open('config/accounts.yaml'))

for account in accounts_config['accounts']:
    account_id = account['id']

    # Determine config source
    if account['risk_config_file']:
        # Load custom file
        config = load_risk_config(account['risk_config_file'])

    elif account['config_overrides']:
        # Apply overrides to base config
        config = base_config.copy()
        config.update(account['config_overrides'])

    else:
        # Use base config as-is
        config = base_config.copy()

    # Apply to risk engine
    engine.set_config(account_id, config)
```

---

## Example Configurations

### Example 1: Single Account (Simplest)

```yaml
topstepx:
  username: "jakertrader"
  api_key: "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
  api_url: "https://api.topstepx.com/api"
  websocket_url: "wss://api.topstepx.com"

monitored_account:
  account_id: "PRAC-V2-126244-84184528"
  account_type: "practice"
  description: "My Practice Account"

# No multi-account configuration
```

### Example 2: Multi-Account with Overrides

```yaml
topstepx:
  username: "${PROJECT_X_USERNAME}"
  api_key: "${PROJECT_X_API_KEY}"
  api_url: "https://api.topstepx.com/api"
  websocket_url: "wss://api.topstepx.com"

accounts:
  # Conservative trader
  - id: "PRAC-V2-126244-84184528"
    name: "Conservative Trader"
    account_type: "practice"
    config_overrides:
      rules:
        daily_realized_loss:
          limit: -200.0              # Strict
        max_contracts:
          limit: 2                   # Conservative
        trade_frequency_limit:
          limits:
            per_minute: 2
            per_hour: 5

  # Aggressive trader
  - id: "PRAC-V2-126244-84184529"
    name: "Aggressive Trader"
    account_type: "live"
    config_overrides:
      rules:
        daily_realized_loss:
          limit: -1000.0             # Loose
        max_contracts:
          limit: 10                  # Aggressive
        trade_frequency_limit:
          limits:
            per_minute: 5
            per_hour: 20

  # Default settings
  - id: "PRAC-V2-126244-84184530"
    name: "Default Trader"
    account_type: "practice"
    risk_config_file: null
    config_overrides: null           # Uses risk_config.yaml
```

---

## Validation Rules

### 1. API Credentials Validation

```python
from pydantic import BaseModel, Field, field_validator

class TopstepXConfig(BaseModel):
    username: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=1)
    api_url: str = Field(default="https://api.topstepx.com/api")
    websocket_url: str = Field(default="wss://api.topstepx.com")

    @field_validator('api_url', 'websocket_url')
    def validate_url(cls, v):
        if not v.startswith(('https://', 'wss://')):
            raise ValueError(f"URL must start with https:// or wss://: {v}")
        return v
```

### 2. Account Configuration Validation

```python
class AccountConfig(BaseModel):
    id: str = Field(..., description="Account ID")
    name: str = Field(..., min_length=1)
    account_type: str = Field(..., pattern="^(practice|live)$")
    description: str | None = None
    risk_config_file: str | None = None
    config_overrides: dict | None = None

    @field_validator('risk_config_file')
    def validate_file_exists(cls, v):
        if v and not Path(v).exists():
            raise ValueError(f"Config file not found: {v}")
        return v

    @model_validator(mode='after')
    def validate_exclusive_config(self):
        if self.risk_config_file and self.config_overrides:
            raise ValueError(
                "Cannot specify both risk_config_file and config_overrides. "
                "Choose one configuration method."
            )
        return self
```

### 3. Multi-Account Validation

```python
class AccountsConfig(BaseModel):
    topstepx: TopstepXConfig
    monitored_account: MonitoredAccountConfig | None = None
    accounts: list[AccountConfig] | None = None

    @model_validator(mode='after')
    def validate_unique_account_ids(self):
        if self.accounts:
            ids = [acc.id for acc in self.accounts]
            if len(ids) != len(set(ids)):
                raise ValueError("Account IDs must be unique")
        return self
```

---

## Environment Variable Substitution

### Format

```yaml
username: "${PROJECT_X_USERNAME}"    # Load from environment
api_key: "${PROJECT_X_API_KEY}"
```

### Implementation

```python
import os
import re

def expand_env_vars(yaml_str: str) -> str:
    """Expand ${VAR_NAME} in YAML string."""
    pattern = r'\$\{([^}]+)\}'

    def replacer(match):
        var_name = match.group(1)
        value = os.getenv(var_name)

        if value is None:
            raise ValueError(f"Environment variable not found: {var_name}")

        return value

    return re.sub(pattern, replacer, yaml_str)

# Usage
with open('config/accounts.yaml') as f:
    yaml_str = f.read()
    yaml_str = expand_env_vars(yaml_str)  # Expand ${...}
    config = yaml.safe_load(yaml_str)
```

---

## Security Considerations

### 1. File Permissions

```bash
# Restrict access to accounts.yaml (contains API keys)
chmod 600 config/accounts.yaml

# Windows equivalent (ACL)
icacls config\accounts.yaml /inheritance:r /grant:r Administrators:F /grant:r SYSTEM:F
```

### 2. Environment Variables (Recommended)

**Use `.env` file instead of hardcoding**:

```yaml
# accounts.yaml
topstepx:
  username: "${PROJECT_X_USERNAME}"  # From .env
  api_key: "${PROJECT_X_API_KEY}"    # From .env
```

**`.env` file**:
```
PROJECT_X_USERNAME=jakertrader
PROJECT_X_API_KEY=tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s=
```

**Benefits**:
- API keys NOT in version control
- Easy to rotate credentials
- Can use different credentials per environment

---

## Summary

### Key Features

1. **Single Account Mode**: Simple configuration for one account
2. **Multi-Account Mode**: Support multiple accounts with different risk profiles
3. **Per-Account Overrides**: Override specific rules per account
4. **Custom Config Files**: Load separate YAML files per account
5. **Environment Variables**: Secure credential management
6. **Validation**: Pydantic models ensure correctness

### Configuration Hierarchy

```
Base Config (risk_config.yaml)
  └─→ Account Custom File (optional)
      └─→ Account Overrides (optional)
          └─→ Final Config for Account
```

### Files

- **accounts.yaml**: Account configuration (THIS FILE)
- **risk_config.yaml**: Base risk rules
- **timers_config.yaml**: Timing configuration
- **.env**: API credentials (recommended)

---

**Document Complete**
**Created**: 2025-10-25
**Status**: PRODUCTION READY
