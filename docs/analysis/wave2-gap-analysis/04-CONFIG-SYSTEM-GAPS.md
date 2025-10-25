# Wave 2 Gap Analysis: Configuration System Implementation

**Analysis Date**: 2025-10-25
**Researcher**: RESEARCHER 4 - Configuration System Gap Analyst
**Project**: Risk Manager V34
**Working Directory**: /mnt/c/Users/jakers/Desktop/risk-manager-v34

---

## Executive Summary

The Risk Manager V34 configuration system is **partially implemented** with critical gaps preventing production deployment. While Pydantic models exist for basic configuration, the complete YAML-based configuration system for all 13 risk rules is **missing**. Hot-reload capabilities and multi-account support are **not implemented**.

**Status at a Glance**:
- **Total Components Analyzed**: 4 (YAML Loader, Validator, Hot-Reload, Multi-Account)
- **Fully Implemented**: 0 (0%)
- **Partially Implemented**: 1 (25%) - Basic Pydantic models only
- **Missing**: 3 (75%) - Validator, Hot-Reload, Multi-Account
- **Estimated Total Effort**: 12 days (1.5-2 weeks)

**Critical Blocker**: Without the complete YAML configuration system, the system cannot:
1. Load the 13 risk rule configurations from YAML files
2. Validate complex rule parameters and cross-rule conflicts
3. Update configuration without service restart (hot-reload)
4. Support multiple trading accounts with different risk profiles

---

## Implementation Status Matrix

| Component | Status | Priority | Effort | Blocks |
|-----------|--------|----------|--------|--------|
| **YAML Loader** | 🔄 Partial (40%) | **Critical** | 3 days | All CLI commands, rule initialization |
| **Configuration Validator** | ❌ Missing (0%) | **High** | 3 days | Safe configuration, rule conflicts |
| **Hot-Reload System** | ❌ Missing (0%) | **Medium** | 4 days | Admin workflow, production ops |
| **Multi-Account Support** | ❌ Missing (0%) | **Low** | 2 days | Multiple traders, account isolation |

**Critical Path**: YAML Loader → Configuration Validator → Hot-Reload System
**Parallelizable**: Multi-Account Support can be built alongside Validator

---

## Current State Analysis

### What Exists Today

#### 1. Basic Pydantic Model (`src/risk_manager/core/config.py`)

**Current Implementation** (79 lines):
```python
class RiskConfig(BaseSettings):
    """Risk Manager configuration."""

    # ProjectX API credentials (from .env)
    project_x_api_key: str
    project_x_username: str
    project_x_api_url: str = "https://api.topstepx.com/api"
    project_x_websocket_url: str = "wss://api.topstepx.com"

    # Basic risk settings (hardcoded defaults)
    max_daily_loss: float = -1000.0
    max_contracts: int = 5
    require_stop_loss: bool = True
    stop_loss_grace_seconds: int = 60

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None

    # AI/Notifications (optional)
    anthropic_api_key: str | None = None
    discord_webhook_url: str | None = None

    @classmethod
    def from_file(cls, config_file: str | Path) -> "RiskConfig":
        """Load configuration from YAML file."""
        import yaml

        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)
```

**What Works**:
- ✅ Loads environment variables from `.env` file (API credentials)
- ✅ Basic `from_file()` method exists (loads YAML → dict → Pydantic)
- ✅ PyYAML dependency already in `pyproject.toml`
- ✅ Type validation via Pydantic (str, int, float, bool)

**What's Missing**:
- ❌ **NO models for 13 risk rules** (only 2 hardcoded: max_daily_loss, max_contracts)
- ❌ **NO nested YAML structure support** (e.g., `rules.daily_realized_loss.limit`)
- ❌ **NO environment variable substitution** (e.g., `${API_KEY}`)
- ❌ **NO file existence checking** (currently will crash if file missing)
- ❌ **NO validation** (no `@validator` decorators)
- ❌ **NO schema for multi-instrument limits** (e.g., `max_contracts_per_instrument`)
- ❌ **NO schema for session hours, holidays, timezones**
- ❌ **NO schema for timer/cooldown rules**
- ❌ **NO schema for hard lockout rules**

#### 2. Empty Configuration Directory

**Current State**:
```bash
$ ls -la config/
total 0
drwxrwxrwx 1 jakers jakers 512 Oct 23 13:03 .
drwxrwxrwx 1 jakers jakers 512 Oct 25 11:14 ..
```

**Expected Files** (from specifications):
```
config/
├── risk_config.yaml        # ❌ MISSING - 13 risk rules configuration
├── accounts.yaml           # ❌ MISSING - API credentials & account mappings
└── holidays.yaml           # ❌ MISSING - Market holidays for session blocks
```

**Impact**:
- **Cannot load risk rules from YAML** - Rules are hardcoded in `manager.py`
- **Cannot configure per-instrument limits** - No YAML to load from
- **Cannot support multiple accounts** - No accounts.yaml schema
- **Cannot respect market holidays** - No holidays.yaml

#### 3. Test Fixtures Exist (But Not Used)

**File**: `/mnt/c/Users/jakers/Desktop/risk-manager-v34/tests/fixtures/configs.py` (9KB, 12 fixtures)

**Available Fixtures**:
- `risk_config_all_enabled()` - Full config with all 12 rules
- `risk_config_minimal()` - Minimal 3-rule config
- `risk_config_strict_mode()` - All breaches → permanent lockout
- `risk_config_aggressive_limits()` - Tight risk controls

**Gap**: These fixtures return **Python dictionaries**, but there's **no code to convert them to Pydantic models** or apply them to the RiskEngine.

---

### What's Missing (High-Level)

The current implementation is **environment-variable based** (`.env` file for API keys) but **NOT YAML-based** for risk rules.

**Specification vs Reality**:

| Specification Says | Current Reality |
|-------------------|-----------------|
| Load 13 rules from `risk_config.yaml` | ❌ Only 2 rules hardcoded in Python |
| Support per-instrument limits (MNQ: 2, ES: 1) | ❌ No schema for this |
| Support timer/cooldown rules (60s, 30min, 1hr) | ❌ No timer schema |
| Support hard lockout rules (until 5 PM reset) | ❌ No reset_time schema |
| Load holidays from `holidays.yaml` | ❌ No file, no schema |
| Load account mappings from `accounts.yaml` | ❌ No file, no schema |
| Validate cross-rule conflicts | ❌ No validator logic |
| Hot-reload on YAML change | ❌ No file watcher |
| Multi-account support | ❌ No account isolation |

---

## Detailed Gap Analysis

### Component 1: YAML Loader

**Current Status**: 🔄 **Partial (40%)** - Basic `from_file()` exists but incomplete

#### What It Should Do (Full Specification)

**Requirements**:

1. **Load risk_config.yaml** with nested structure:
   ```yaml
   general:
     instruments: [MNQ, ES]
     timezone: "America/New_York"

   rules:
     daily_realized_loss:
       enabled: true
       limit: -500.0
       reset_time: "17:00"
   ```

2. **Load accounts.yaml** for API credentials:
   ```yaml
   topstepx:
     username: "jakertrader"
     api_key: "tj5F5k0jDY..."

   monitored_account:
     account_id: "PRAC-V2-126244-84184528"
   ```

3. **Load holidays.yaml** for session restrictions:
   ```yaml
   holidays:
     2025:
       - "2025-01-01"  # New Year's Day
       - "2025-07-04"  # Independence Day
   ```

4. **Handle missing files gracefully**:
   - Default to `.env` for API keys if `accounts.yaml` missing
   - Default to empty list if `holidays.yaml` missing
   - **Error if `risk_config.yaml` missing** (required for production)

5. **Environment variable substitution**:
   ```yaml
   topstepx:
     api_key: "${PROJECT_X_API_KEY}"  # Load from .env
   ```

6. **Clear error messages**:
   - File not found → "Config file not found: config/risk_config.yaml"
   - Invalid YAML → "Invalid YAML syntax at line 42: ..."
   - Missing required field → "Missing required field: rules.daily_realized_loss.limit"

#### Current Implementation Gaps

**Existing Code** (4 lines in `config.py`):
```python
@classmethod
def from_file(cls, config_file: str | Path) -> "RiskConfig":
    """Load configuration from YAML file."""
    import yaml
    from pathlib import Path

    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_path) as f:
        config_data = yaml.safe_load(f)

    return cls(**config_data)
```

**What Works**:
- ✅ Basic YAML parsing (`yaml.safe_load`)
- ✅ File existence check
- ✅ FileNotFoundError with message

**What's Missing**:

1. **No support for nested rule structure**:
   - Current model is **flat** (max_daily_loss, max_contracts)
   - Spec requires **nested** (rules.daily_realized_loss.limit)

   **Blocker**: Pydantic model needs nested structure:
   ```python
   class RuleConfig(BaseModel):
       enabled: bool
       limit: float
       reset_time: str | None = None

   class RulesConfig(BaseModel):
       daily_realized_loss: RuleConfig
       max_contracts: RuleConfig
       # ... 11 more rules

   class RiskConfig(BaseSettings):
       general: GeneralConfig
       rules: RulesConfig
   ```

2. **No environment variable substitution**:
   - Current: Loads YAML literally
   - Spec: Should expand `${VAR_NAME}` placeholders

   **Implementation Needed**:
   ```python
   import os
   import re

   def expand_env_vars(yaml_str: str) -> str:
       """Expand ${VAR_NAME} in YAML string."""
       pattern = r'\$\{([^}]+)\}'

       def replacer(match):
           var_name = match.group(1)
           return os.getenv(var_name, match.group(0))

       return re.sub(pattern, replacer, yaml_str)
   ```

3. **No support for multiple config files**:
   - Current: Only loads single file
   - Spec: Needs to load `risk_config.yaml` + `accounts.yaml` + `holidays.yaml`

   **Implementation Needed**:
   ```python
   @classmethod
   def from_files(cls,
       risk_config: str | Path,
       accounts_config: str | Path | None = None,
       holidays_config: str | Path | None = None
   ) -> "RiskConfig":
       """Load from multiple YAML files."""
       # Load main config
       with open(risk_config) as f:
           risk_data = yaml.safe_load(f)

       # Load accounts (optional)
       if accounts_config and Path(accounts_config).exists():
           with open(accounts_config) as f:
               accounts_data = yaml.safe_load(f)
           risk_data["accounts"] = accounts_data

       # Load holidays (optional)
       if holidays_config and Path(holidays_config).exists():
           with open(holidays_config) as f:
               holidays_data = yaml.safe_load(f)
           risk_data["holidays"] = holidays_data

       return cls(**risk_data)
   ```

4. **No graceful degradation**:
   - Current: Crashes if file missing
   - Spec: Should fall back to .env for API keys

   **Example**:
   ```python
   # Try YAML first, fall back to .env
   try:
       config = RiskConfig.from_file("config/accounts.yaml")
   except FileNotFoundError:
       logger.warning("accounts.yaml not found, using .env")
       config = RiskConfig()  # Loads from .env via pydantic-settings
   ```

5. **No YAML schema validation**:
   - Current: Relies on Pydantic model matching YAML structure
   - Spec: Should validate YAML structure **before** passing to Pydantic

   **Why**: Better error messages
   - Without: "TypeError: __init__() missing 1 required positional argument: 'limit'"
   - With: "Invalid config: rules.daily_realized_loss.limit is required"

#### Missing Features Breakdown

| Feature | Status | Lines of Code | Complexity |
|---------|--------|---------------|------------|
| Nested Pydantic models (13 rules) | ❌ Missing | ~200 | Medium |
| Environment variable expansion | ❌ Missing | ~20 | Low |
| Multiple file loading | ❌ Missing | ~40 | Low |
| Graceful degradation | ❌ Missing | ~30 | Low |
| Schema validation | ❌ Missing | ~50 | Medium |
| **Total** | **40% done** | **~340 LOC** | **Medium** |

#### Dependencies

- **None** (can implement immediately)
- PyYAML already in `pyproject.toml`
- Pydantic already installed

#### Estimated Effort

**3 days**:
- Day 1: Design nested Pydantic models for all 13 rules
- Day 2: Implement multi-file loading + env var expansion
- Day 3: Write unit tests + error handling

#### Implementation Roadmap

**Step 1**: Create nested Pydantic models
```python
# src/risk_manager/core/config_models.py (new file)

from pydantic import BaseModel, Field

class GeneralConfig(BaseModel):
    instruments: list[str] = Field(default_factory=list)
    timezone: str = "America/New_York"
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

class DailyRealizedLossConfig(BaseModel):
    enabled: bool = True
    limit: float = -500.0
    reset_time: str = "17:00"
    timezone: str = "America/New_York"
    close_all: bool = True
    cancel_orders: bool = True
    lockout_type: str = "hard"
    lockout_until_reset: bool = True

class RulesConfig(BaseModel):
    max_contracts: MaxContractsConfig = Field(default_factory=MaxContractsConfig)
    daily_realized_loss: DailyRealizedLossConfig = Field(default_factory=DailyRealizedLossConfig)
    # ... 11 more rules

class RiskConfig(BaseSettings):
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    rules: RulesConfig = Field(default_factory=RulesConfig)

    # API credentials (from .env or accounts.yaml)
    project_x_api_key: str = Field(..., validation_alias="PROJECT_X_API_KEY")
    project_x_username: str = Field(..., validation_alias="PROJECT_X_USERNAME")
```

**Step 2**: Implement multi-file loader
```python
@classmethod
def from_files(cls,
    config_dir: str | Path = "config"
) -> "RiskConfig":
    """Load from config directory."""
    config_dir = Path(config_dir)

    # Load risk_config.yaml (required)
    risk_config_file = config_dir / "risk_config.yaml"
    if not risk_config_file.exists():
        raise FileNotFoundError(f"Required file not found: {risk_config_file}")

    with open(risk_config_file) as f:
        yaml_str = f.read()
        yaml_str = expand_env_vars(yaml_str)  # Expand ${VAR}
        risk_data = yaml.safe_load(yaml_str)

    # Load accounts.yaml (optional - fall back to .env)
    accounts_file = config_dir / "accounts.yaml"
    if accounts_file.exists():
        with open(accounts_file) as f:
            accounts_data = yaml.safe_load(f.read())
        risk_data.update(accounts_data.get("topstepx", {}))

    # Load holidays.yaml (optional)
    holidays_file = config_dir / "holidays.yaml"
    if holidays_file.exists():
        with open(holidays_file) as f:
            holidays_data = yaml.safe_load(f.read())
        risk_data["holidays"] = holidays_data

    return cls(**risk_data)
```

**Step 3**: Add unit tests
```python
# tests/unit/test_config/test_yaml_loader.py

def test_load_from_single_file(tmp_path):
    config_file = tmp_path / "risk_config.yaml"
    config_file.write_text("""
    general:
      instruments: [MNQ, ES]
    rules:
      daily_realized_loss:
        enabled: true
        limit: -500.0
    """)

    config = RiskConfig.from_file(config_file)
    assert config.rules.daily_realized_loss.limit == -500.0

def test_env_var_expansion(tmp_path, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    config_file = tmp_path / "accounts.yaml"
    config_file.write_text("""
    topstepx:
      api_key: "${API_KEY}"
    """)

    config = RiskConfig.from_file(config_file)
    assert config.project_x_api_key == "secret123"
```

---

### Component 2: Configuration Validator

**Current Status**: ❌ **Missing (0%)** - No validation beyond basic Pydantic types

#### What It Should Do (Full Specification)

**Requirements**:

1. **Type Validation** (Pydantic already does this):
   - `limit: float` → Rejects if string/int/bool
   - `enabled: bool` → Rejects if not true/false
   - `instruments: list[str]` → Rejects if not a list

2. **Range Validation**:
   - `max_contracts: int` → Must be > 0
   - `daily_realized_loss.limit: float` → Must be < 0 (it's a loss)
   - `cooldown_minutes: int` → Must be >= 1
   - `reset_time: str` → Must match "HH:MM" format (e.g., "17:00")

3. **Cross-Rule Conflict Detection**:
   - **Conflict**: Both `daily_realized_loss` and `daily_realized_profit` set `close_all: true`
   - **Issue**: When both trigger, which one wins?
   - **Solution**: Validator warns or errors

4. **Semantic Validation**:
   - `daily_unrealized_loss.limit` should be **less than** `daily_realized_loss.limit`
   - `session_hours.end` should be **after** `session_hours.start`
   - `trade_frequency_limit.per_minute` should be **less than** `per_hour`

5. **SDK Integration Validation**:
   - Validate `account_id` exists in TopstepX API
   - Validate `instruments` are valid symbols (MNQ, ES, etc.)
   - **Note**: Requires API call, should be optional (skip in offline mode)

6. **Clear Error Messages**:
   ```
   ❌ Configuration Error:

   rules.daily_realized_loss.limit = 500.0

   Problem: Daily loss limit must be negative (you specified positive $500).
   Fix: Change to -500.0 (negative number for losses)
   ```

#### Current Implementation Gaps

**Existing Code**: **Zero validation** beyond Pydantic's type checking.

**What's Missing**:

1. **No Pydantic validators**:
   ```python
   # What we SHOULD have:
   from pydantic import field_validator

   class DailyRealizedLossConfig(BaseModel):
       limit: float

       @field_validator('limit')
       def limit_must_be_negative(cls, v):
           if v >= 0:
               raise ValueError('Daily loss limit must be negative (e.g., -500.0)')
           return v
   ```

2. **No cross-rule validation**:
   ```python
   # What we SHOULD have:
   from pydantic import model_validator

   class RulesConfig(BaseModel):
       daily_realized_loss: DailyRealizedLossConfig
       daily_unrealized_loss: DailyUnrealizedLossConfig

       @model_validator(mode='after')
       def validate_loss_limits(self):
           """Ensure unrealized loss limit < realized loss limit."""
           if self.daily_unrealized_loss.enabled and self.daily_realized_loss.enabled:
               if abs(self.daily_unrealized_loss.limit) > abs(self.daily_realized_loss.limit):
                   raise ValueError(
                       f"Unrealized loss limit ({self.daily_unrealized_loss.limit}) "
                       f"should be less than realized loss limit ({self.daily_realized_loss.limit})"
                   )
           return self
   ```

3. **No SDK account validation**:
   ```python
   # What we SHOULD have:
   async def validate_account_id(account_id: str, api_key: str) -> bool:
       """Check if account_id exists in TopstepX API."""
       from project_x_py import TradingSuite

       try:
           suite = await TradingSuite.create(instruments=[])
           accounts = await suite.get_accounts()
           return account_id in [acc.id for acc in accounts]
       except Exception as e:
           logger.warning(f"Could not validate account ID: {e}")
           return True  # Allow in offline mode
   ```

4. **No time format validation**:
   ```python
   # What we SHOULD have:
   import re
   from datetime import datetime

   @field_validator('reset_time')
   def validate_time_format(cls, v):
       """Ensure reset_time matches HH:MM format."""
       if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
           raise ValueError(f"Invalid time format: {v}. Use HH:MM (e.g., 17:00)")
       return v
   ```

5. **No instrument validation**:
   ```python
   # What we SHOULD have:
   VALID_INSTRUMENTS = {"MNQ", "ES", "NQ", "GC", "CL", "RTY", "YM", "MES", "MGC"}

   @field_validator('instruments')
   def validate_instruments(cls, v):
       """Ensure all instruments are valid symbols."""
       invalid = set(v) - VALID_INSTRUMENTS
       if invalid:
           raise ValueError(f"Invalid instruments: {invalid}. Valid: {VALID_INSTRUMENTS}")
       return v
   ```

#### Missing Features Breakdown

| Validation Type | Status | Lines of Code | Complexity |
|----------------|--------|---------------|------------|
| Range validators (10 rules) | ❌ Missing | ~100 | Low |
| Time format validators | ❌ Missing | ~30 | Low |
| Cross-rule conflict detection | ❌ Missing | ~80 | Medium |
| Semantic validation | ❌ Missing | ~60 | Medium |
| SDK account validation | ❌ Missing | ~40 | Low |
| Instrument validation | ❌ Missing | ~20 | Low |
| **Total** | **0% done** | **~330 LOC** | **Medium** |

#### Dependencies

- ✅ **YAML Loader** (must load config first before validating)
- ⚠️ **SDK Integration** (optional - for account/instrument validation)

#### Estimated Effort

**3 days**:
- Day 1: Add `@field_validator` decorators to all 13 rule configs
- Day 2: Implement `@model_validator` for cross-rule checks
- Day 3: Add SDK validation + unit tests

#### Implementation Roadmap

**Step 1**: Add field validators to all rule configs
```python
class DailyRealizedLossConfig(BaseModel):
    limit: float
    reset_time: str = "17:00"

    @field_validator('limit')
    def limit_must_be_negative(cls, v):
        if v >= 0:
            raise ValueError('Daily loss limit must be negative')
        return v

    @field_validator('reset_time')
    def validate_time_format(cls, v):
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f"Invalid time: {v}. Use HH:MM")
        return v

class MaxContractsConfig(BaseModel):
    limit: int

    @field_validator('limit')
    def limit_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Max contracts must be > 0')
        return v
```

**Step 2**: Add cross-rule validators
```python
class RulesConfig(BaseModel):
    daily_realized_loss: DailyRealizedLossConfig
    daily_unrealized_loss: DailyUnrealizedLossConfig

    @model_validator(mode='after')
    def validate_no_conflicts(self):
        """Check for rule conflicts."""
        # Check loss limits make sense
        if (self.daily_unrealized_loss.enabled and
            self.daily_realized_loss.enabled):
            if abs(self.daily_unrealized_loss.limit) > abs(self.daily_realized_loss.limit):
                raise ValueError(
                    "Unrealized loss limit should be smaller than realized loss limit"
                )

        return self
```

**Step 3**: Add unit tests
```python
def test_daily_loss_must_be_negative():
    with pytest.raises(ValidationError, match="must be negative"):
        DailyRealizedLossConfig(limit=500.0)  # Positive should fail

def test_max_contracts_must_be_positive():
    with pytest.raises(ValidationError, match="must be > 0"):
        MaxContractsConfig(limit=0)

def test_reset_time_format():
    with pytest.raises(ValidationError, match="Invalid time"):
        DailyRealizedLossConfig(limit=-500.0, reset_time="5pm")  # Should be "17:00"
```

---

### Component 3: Hot-Reload System

**Current Status**: ❌ **Missing (0%)** - No file watching or reload capability

#### What It Should Do (Full Specification)

**Requirements**:

1. **File Watching**:
   - Watch `config/risk_config.yaml` for changes
   - Watch `config/accounts.yaml` for changes
   - Watch `config/holidays.yaml` for changes
   - Detect file modifications (not deletes/renames)

2. **Atomic Config Reload**:
   ```
   File changed → Load YAML → Validate → Apply to RiskEngine
                                ↓ (if fails)
                          Rollback to previous config
   ```

3. **Validation Before Apply**:
   - Load new YAML into temp `RiskConfig` object
   - Run all validators
   - **If valid**: Apply to RiskEngine
   - **If invalid**: Log error, keep old config

4. **Manager Notification**:
   ```python
   # When config reloads successfully:
   await risk_manager.reload_config(new_config)

   # RiskManager should:
   # 1. Stop RiskEngine
   # 2. Remove old rules
   # 3. Add new rules from new config
   # 4. Restart RiskEngine
   ```

5. **Event Logging**:
   - Log when file changes detected
   - Log validation success/failure
   - Log when new config applied
   - Log what changed (diff)

6. **Admin CLI Integration**:
   ```bash
   $ risk-manager admin

   [1] View Status
   [2] Configure Rules
   [3] Reload Config  ← NEW: Manually trigger reload
   ```

#### Current Implementation Gaps

**Existing Code**: **Zero** - No file watching, no reload mechanism.

**What's Missing**:

1. **No file watcher library**:
   - `watchdog` library not in `pyproject.toml`
   - No `FileSystemEventHandler` implementation

2. **No reload mechanism in RiskManager**:
   ```python
   # What we SHOULD have in manager.py:
   async def reload_config(self, new_config: RiskConfig) -> bool:
       """Reload configuration without restarting service."""
       try:
           # Stop engine
           await self.engine.stop()

           # Clear old rules
           self.engine.clear_rules()

           # Update config
           self.config = new_config

           # Re-add rules from new config
           await self._add_default_rules()

           # Restart engine
           await self.engine.start()

           logger.success("✅ Config reloaded successfully")
           return True
       except Exception as e:
           logger.error(f"❌ Config reload failed: {e}")
           return False
   ```

3. **No file watcher service**:
   ```python
   # What we SHOULD have in new file: src/risk_manager/core/config_watcher.py
   from watchdog.observers import Observer
   from watchdog.events import FileSystemEventHandler

   class ConfigFileWatcher(FileSystemEventHandler):
       def __init__(self, risk_manager: RiskManager, config_dir: Path):
           self.risk_manager = risk_manager
           self.config_dir = config_dir

       def on_modified(self, event):
           if event.src_path.endswith(('.yaml', '.yml')):
               logger.info(f"Config file changed: {event.src_path}")
               asyncio.create_task(self._reload_config())

       async def _reload_config(self):
           try:
               # Load new config
               new_config = RiskConfig.from_files(self.config_dir)

               # Apply to manager
               success = await self.risk_manager.reload_config(new_config)

               if success:
                   logger.success("Config reloaded successfully")
               else:
                   logger.error("Config reload failed, keeping old config")
           except Exception as e:
               logger.error(f"Config reload error: {e}")
   ```

4. **No rollback mechanism**:
   ```python
   # What we SHOULD have:
   class RiskManager:
       def __init__(self, config: RiskConfig):
           self.config = config
           self.config_history = [config]  # Keep last 5 configs

       async def reload_config(self, new_config: RiskConfig) -> bool:
           old_config = self.config

           try:
               # Try to apply new config
               await self._apply_config(new_config)

               # Success! Save to history
               self.config_history.append(new_config)
               if len(self.config_history) > 5:
                   self.config_history.pop(0)

               return True
           except Exception as e:
               # Rollback to old config
               logger.error(f"Rollback to previous config due to: {e}")
               await self._apply_config(old_config)
               return False
   ```

5. **No config diff logging**:
   ```python
   # What we SHOULD have:
   def diff_configs(old: RiskConfig, new: RiskConfig) -> dict:
       """Show what changed between configs."""
       changes = {}

       # Check rule changes
       for rule_name in old.rules.__fields__:
           old_rule = getattr(old.rules, rule_name)
           new_rule = getattr(new.rules, rule_name)

           if old_rule != new_rule:
               changes[rule_name] = {
                   "old": old_rule.dict(),
                   "new": new_rule.dict()
               }

       return changes

   # Usage:
   changes = diff_configs(old_config, new_config)
   logger.info(f"Config changes: {changes}")
   # Output: Config changes: {'daily_realized_loss': {'old': {'limit': -500.0}, 'new': {'limit': -1000.0}}}
   ```

#### Missing Features Breakdown

| Feature | Status | Lines of Code | Complexity |
|---------|--------|---------------|------------|
| watchdog library integration | ❌ Missing | ~10 (setup) | Low |
| FileSystemEventHandler | ❌ Missing | ~50 | Low |
| Manager.reload_config() | ❌ Missing | ~40 | Medium |
| Atomic config swap | ❌ Missing | ~30 | Medium |
| Rollback mechanism | ❌ Missing | ~40 | Medium |
| Config diff logging | ❌ Missing | ~50 | Low |
| Admin CLI integration | ❌ Missing | ~30 | Low |
| **Total** | **0% done** | **~250 LOC** | **Medium** |

#### Dependencies

- ✅ **YAML Loader** (must load config before reloading)
- ✅ **Configuration Validator** (must validate before applying)
- ❌ **watchdog library** (not in dependencies)

#### Estimated Effort

**4 days**:
- Day 1: Add `watchdog` dependency, implement `ConfigFileWatcher`
- Day 2: Implement `RiskManager.reload_config()` with rollback
- Day 3: Add config diff logging and testing
- Day 4: Admin CLI integration + end-to-end testing

#### Implementation Roadmap

**Step 1**: Add watchdog to dependencies
```toml
# pyproject.toml
dependencies = [
    "watchdog>=3.0.0",  # File watching for hot-reload
    # ... existing deps
]
```

**Step 2**: Create ConfigFileWatcher
```python
# src/risk_manager/core/config_watcher.py (new file)

from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

class ConfigFileWatcher(FileSystemEventHandler):
    def __init__(self, risk_manager, config_dir: Path):
        self.risk_manager = risk_manager
        self.config_dir = Path(config_dir)
        self.observer = Observer()

    def start(self):
        """Start watching config directory."""
        self.observer.schedule(self, str(self.config_dir), recursive=False)
        self.observer.start()
        logger.info(f"Watching config directory: {self.config_dir}")

    def stop(self):
        """Stop watching."""
        self.observer.stop()
        self.observer.join()

    def on_modified(self, event):
        """Handle file modification."""
        if event.is_directory:
            return

        if event.src_path.endswith(('.yaml', '.yml')):
            logger.info(f"Config file changed: {event.src_path}")

            # Trigger reload (async)
            import asyncio
            asyncio.create_task(self._reload())

    async def _reload(self):
        """Reload configuration."""
        try:
            from risk_manager.core.config import RiskConfig

            # Load new config
            new_config = RiskConfig.from_files(self.config_dir)

            # Apply to manager
            await self.risk_manager.reload_config(new_config)
        except Exception as e:
            logger.error(f"Config reload failed: {e}")
```

**Step 3**: Add reload method to RiskManager
```python
# src/risk_manager/core/manager.py

async def reload_config(self, new_config: RiskConfig) -> bool:
    """
    Reload configuration without restarting service.

    Atomic operation: either fully succeeds or fully rolls back.
    """
    old_config = self.config

    logger.info("Reloading configuration...")

    try:
        # Step 1: Stop engine temporarily
        await self.engine.stop()
        logger.debug("Engine stopped for reload")

        # Step 2: Clear old rules
        self.engine.clear_rules()

        # Step 3: Update config
        self.config = new_config

        # Step 4: Re-add rules from new config
        await self._add_default_rules()

        # Step 5: Restart engine
        await self.engine.start()

        # Step 6: Log changes
        changes = self._diff_configs(old_config, new_config)
        if changes:
            logger.success(f"✅ Config reloaded. Changes: {changes}")
        else:
            logger.info("Config reloaded (no changes)")

        return True

    except Exception as e:
        # Rollback to old config
        logger.error(f"Config reload failed: {e}. Rolling back...")

        try:
            self.config = old_config
            await self._add_default_rules()
            await self.engine.start()
            logger.warning("Rolled back to previous config")
        except Exception as rollback_error:
            logger.critical(f"Rollback failed: {rollback_error}")

        return False

def _diff_configs(self, old: RiskConfig, new: RiskConfig) -> dict:
    """Show what changed."""
    changes = {}

    if old.max_daily_loss != new.max_daily_loss:
        changes["max_daily_loss"] = {
            "old": old.max_daily_loss,
            "new": new.max_daily_loss
        }

    if old.max_contracts != new.max_contracts:
        changes["max_contracts"] = {
            "old": old.max_contracts,
            "new": new.max_contracts
        }

    return changes
```

**Step 4**: Wire watcher into manager
```python
# src/risk_manager/core/manager.py

async def start(self):
    """Start the risk manager."""
    # ... existing startup code

    # Start config file watcher (if in production)
    if self.config.environment == "production":
        from risk_manager.core.config_watcher import ConfigFileWatcher

        self.config_watcher = ConfigFileWatcher(self, Path("config"))
        self.config_watcher.start()
        logger.info("Hot-reload enabled (watching config files)")
```

**Step 5**: Add tests
```python
# tests/integration/test_hot_reload.py

@pytest.mark.asyncio
async def test_hot_reload_updates_rules(tmp_path):
    """Test that changing YAML file updates rules."""
    config_file = tmp_path / "risk_config.yaml"

    # Initial config
    config_file.write_text("""
    rules:
      daily_realized_loss:
        limit: -500.0
    """)

    manager = await RiskManager.create(config_file=config_file)
    assert manager.config.max_daily_loss == -500.0

    # Change config
    config_file.write_text("""
    rules:
      daily_realized_loss:
        limit: -1000.0
    """)

    # Trigger reload
    new_config = RiskConfig.from_file(config_file)
    await manager.reload_config(new_config)

    # Check updated
    assert manager.config.max_daily_loss == -1000.0
```

---

### Component 4: Multi-Account Support

**Current Status**: ❌ **Missing (0%)** - No account isolation or per-account configs

#### What It Should Do (Full Specification)

**Requirements**:

1. **accounts.yaml Schema**:
   ```yaml
   accounts:
     - id: "PRAC-V2-126244-84184528"
       name: "Trader A"
       risk_config: "config/trader_a_rules.yaml"  # Custom config

     - id: "PRAC-V2-126244-84184529"
       name: "Trader B"
       risk_config: "default"  # Use default risk_config.yaml

     - id: "PRAC-V2-126244-84184530"
       name: "Trader C"
       config_overrides:
         rules:
           daily_realized_loss:
             limit: -200.0  # Override just this one rule
   ```

2. **Default + Override Pattern**:
   ```
   Base config (risk_config.yaml):
     daily_realized_loss.limit = -500.0
     max_contracts = 5

   Account override (for Trader C):
     daily_realized_loss.limit = -200.0  ← Override
     max_contracts = 5                   ← Inherited from base

   Final config for Trader C:
     daily_realized_loss.limit = -200.0
     max_contracts = 5
   ```

3. **Account-Specific Rule Evaluation**:
   ```python
   # When event comes in for account "PRAC-V2-126244-84184528":
   config = account_manager.get_config_for_account(event.account_id)

   # Evaluate rules using account-specific config
   await risk_engine.evaluate_rules(event, config)
   ```

4. **Per-Account State Isolation**:
   - Each account has separate daily P&L tracking
   - Each account has separate lockout state
   - Each account has separate trade count

5. **Admin CLI Integration**:
   ```bash
   $ risk-manager admin

   [1] View Status
   [2] Configure Rules
   [3] Manage Accounts  ← NEW
       ├─ List all accounts
       ├─ Add new account
       ├─ Edit account config
       └─ Remove account
   ```

#### Current Implementation Gaps

**Existing Code**: **Zero** - System assumes single account.

**What's Missing**:

1. **No accounts.yaml schema**:
   ```python
   # What we SHOULD have:
   class AccountConfig(BaseModel):
       id: str
       name: str
       risk_config: str | None = None  # Path to custom config
       config_overrides: dict | None = None  # Override specific rules

   class AccountsConfig(BaseModel):
       accounts: list[AccountConfig]
   ```

2. **No account manager**:
   ```python
   # What we SHOULD have in new file: src/risk_manager/core/account_manager.py
   class AccountManager:
       def __init__(self, base_config: RiskConfig, accounts_config: AccountsConfig):
           self.base_config = base_config
           self.accounts = {}

           for account in accounts_config.accounts:
               self.accounts[account.id] = self._build_account_config(account)

       def _build_account_config(self, account: AccountConfig) -> RiskConfig:
           """Build config for specific account."""
           if account.risk_config:
               # Load custom config file
               config = RiskConfig.from_file(account.risk_config)
           else:
               # Start with base config
               config = self.base_config.copy()

           # Apply overrides
           if account.config_overrides:
               config = self._apply_overrides(config, account.config_overrides)

           return config

       def get_config_for_account(self, account_id: str) -> RiskConfig:
           """Get config for specific account."""
           return self.accounts.get(account_id, self.base_config)
   ```

3. **No account-aware event processing**:
   ```python
   # What RiskEngine SHOULD do:
   async def evaluate_rules(self, event: RiskEvent) -> None:
       # Get account-specific config
       account_id = event.data.get("account_id")
       config = self.account_manager.get_config_for_account(account_id)

       # Evaluate rules using account config
       for rule in self.rules:
           result = await rule.evaluate(event, config)
           if result.violated:
               await rule.enforce(event, config)
   ```

4. **No per-account state tracking**:
   ```python
   # PnLTracker already supports this! (database.py, pnl_tracker.py)
   # Just need to wire it properly:

   tracker.add_trade_pnl("ACCOUNT-001", -100.0)  # Trader A
   tracker.add_trade_pnl("ACCOUNT-002", 50.0)    # Trader B

   # Get separate P&L for each
   pnl_a = tracker.get_daily_pnl("ACCOUNT-001")  # -100.0
   pnl_b = tracker.get_daily_pnl("ACCOUNT-002")  # 50.0
   ```

#### Missing Features Breakdown

| Feature | Status | Lines of Code | Complexity |
|---------|--------|---------------|------------|
| AccountConfig Pydantic model | ❌ Missing | ~30 | Low |
| AccountManager class | ❌ Missing | ~80 | Medium |
| Override merge logic | ❌ Missing | ~40 | Medium |
| Account-aware RiskEngine | ❌ Missing | ~30 | Low |
| Admin CLI account management | ❌ Missing | ~60 | Low |
| **Total** | **0% done** | **~240 LOC** | **Medium** |

#### Dependencies

- ✅ **YAML Loader** (need to load accounts.yaml)
- ✅ **PnL Tracker** (already supports multi-account)
- ⚠️ **Optional**: Can be implemented independently

#### Estimated Effort

**2 days**:
- Day 1: Create `AccountConfig` schema + `AccountManager` class
- Day 2: Wire into RiskEngine + add tests

#### Implementation Roadmap

**Step 1**: Create account config schema
```python
# src/risk_manager/core/config_models.py

class AccountConfig(BaseModel):
    id: str = Field(..., description="Account ID from TopstepX")
    name: str = Field(..., description="Human-readable name")
    risk_config_file: str | None = Field(None, description="Path to custom config")
    config_overrides: dict[str, Any] | None = Field(None, description="Override specific rules")

class AccountsConfig(BaseModel):
    accounts: list[AccountConfig] = Field(default_factory=list)
```

**Step 2**: Create AccountManager
```python
# src/risk_manager/core/account_manager.py (new file)

class AccountManager:
    def __init__(self, base_config: RiskConfig, accounts_file: Path | None = None):
        self.base_config = base_config
        self.account_configs = {}

        if accounts_file and accounts_file.exists():
            self._load_accounts(accounts_file)

    def _load_accounts(self, accounts_file: Path):
        """Load accounts from accounts.yaml."""
        with open(accounts_file) as f:
            data = yaml.safe_load(f)

        accounts_config = AccountsConfig(**data)

        for account in accounts_config.accounts:
            self.account_configs[account.id] = self._build_config(account)

    def _build_config(self, account: AccountConfig) -> RiskConfig:
        """Build config for specific account."""
        if account.risk_config_file:
            config = RiskConfig.from_file(account.risk_config_file)
        else:
            config = self.base_config.model_copy()

        if account.config_overrides:
            config = self._apply_overrides(config, account.config_overrides)

        return config

    def _apply_overrides(self, config: RiskConfig, overrides: dict) -> RiskConfig:
        """Apply overrides to config."""
        config_dict = config.model_dump()

        # Deep merge
        for key, value in overrides.items():
            if isinstance(value, dict) and key in config_dict:
                config_dict[key].update(value)
            else:
                config_dict[key] = value

        return RiskConfig(**config_dict)

    def get_config(self, account_id: str) -> RiskConfig:
        """Get config for account (or default)."""
        return self.account_configs.get(account_id, self.base_config)
```

**Step 3**: Add tests
```python
# tests/unit/test_account_manager.py

def test_account_specific_override():
    base_config = RiskConfig(max_daily_loss=-500.0)

    accounts_data = {
        "accounts": [{
            "id": "ACCOUNT-001",
            "name": "Trader A",
            "config_overrides": {
                "max_daily_loss": -200.0
            }
        }]
    }

    manager = AccountManager(base_config)
    manager._load_accounts_from_dict(accounts_data)

    # Account-specific config
    config = manager.get_config("ACCOUNT-001")
    assert config.max_daily_loss == -200.0

    # Default config for unknown account
    config = manager.get_config("ACCOUNT-999")
    assert config.max_daily_loss == -500.0
```

---

## Critical Path Analysis

### Dependencies Graph

```
YAML Loader (3 days)
  ├─→ Configuration Validator (3 days)
  │     └─→ Hot-Reload System (4 days)
  └─→ Multi-Account Support (2 days)
```

**Total Sequential**: 12 days (3 + 3 + 4 + 2)
**With Parallelization**: ~8 days (validator + multi-account can be parallel after loader done)

### Recommended Implementation Order

#### Week 1: Foundation (Days 1-5)

**Days 1-3**: **YAML Loader** (Critical)
- Create nested Pydantic models for all 13 rules
- Implement multi-file loading (risk_config.yaml, accounts.yaml, holidays.yaml)
- Add environment variable expansion
- Write unit tests

**Days 4-5**: **Configuration Validator** (High Priority)
- Add `@field_validator` decorators for range/format validation
- Implement `@model_validator` for cross-rule conflict detection
- Add semantic validation (loss limits, time ranges)
- Write unit tests

#### Week 2: Advanced Features (Days 6-10)

**Days 6-7**: **Multi-Account Support** (Can run in parallel with validator)
- Create AccountConfig schema
- Implement AccountManager class
- Add override merge logic
- Write unit tests

**Days 8-10**: **Hot-Reload System** (Depends on validator)
- Add `watchdog` library
- Implement ConfigFileWatcher
- Add `reload_config()` method to RiskManager
- Add rollback mechanism
- Write integration tests

---

## Blockers Analysis

### What Features Are Blocked

**Without YAML Loader**:
- ❌ Cannot load 13 risk rules from configuration
- ❌ Cannot initialize RiskEngine with rule configs
- ❌ CLI commands cannot read/write config
- ❌ Cannot configure per-instrument limits (MNQ: 2, ES: 1)
- ❌ Cannot configure session hours, holidays
- ❌ Admin CLI `config` command blocked

**Without Configuration Validator**:
- ❌ Cannot detect invalid rule parameters (e.g., positive loss limit)
- ❌ Cannot detect cross-rule conflicts
- ❌ Cannot validate account IDs exist
- ❌ Risk of misconfiguration leading to unintended behavior

**Without Hot-Reload**:
- ❌ Must restart service to change configuration
- ❌ Downtime during config updates
- ❌ Cannot quickly respond to market conditions
- ❌ Admin workflow is clunky (edit YAML → restart service)

**Without Multi-Account**:
- ❌ Cannot support multiple traders with different risk profiles
- ❌ Cannot isolate state between accounts
- ❌ Limited to single-account deployments

---

## Example YAML Schemas

### risk_config.yaml (Complete)

```yaml
# ==============================================================================
# RISK MANAGER V34 - CONFIGURATION
# ==============================================================================

general:
  instruments:
    - MNQ
    - ES
  timezone: "America/New_York"
  logging:
    level: "INFO"
    log_to_file: true
    log_directory: "logs/"
  database:
    path: "data/risk_state.db"
    backup_enabled: true
    backup_interval_hours: 24

# ==============================================================================
# CATEGORY 1: TRADE-BY-TRADE RULES
# ==============================================================================

rules:
  max_contracts:
    enabled: true
    limit: 5
    count_type: "net"
    close_all: false
    close_position: true

  max_contracts_per_instrument:
    enabled: true
    default_limit: 3
    instrument_limits:
      MNQ: 2
      ES: 1
    close_all: false
    close_position: true

  daily_unrealized_loss:
    enabled: true
    limit: -200.0
    check_interval_seconds: 10
    close_all: false
    close_position: true

  max_unrealized_profit:
    enabled: true
    target: 500.0
    check_interval_seconds: 5
    close_all: false
    close_position: true

  no_stop_loss_grace:
    enabled: true
    require_within_seconds: 60
    grace_period_seconds: 300
    close_all: false
    close_position: true

  symbol_blocks:
    enabled: false
    blocked_symbols: []
    close_all: false
    close_position: true
    close_immediately: true

# ==============================================================================
# CATEGORY 2: TIMER/COOLDOWN RULES
# ==============================================================================

  trade_frequency_limit:
    enabled: true
    limits:
      per_minute: 3
      per_hour: 10
      per_session: 50
    cooldowns:
      per_minute_breach: 60
      per_hour_breach: 1800
      per_session_breach: 3600
    close_all: true
    cancel_orders: true
    lockout_type: "timer"

  cooldown_after_loss:
    enabled: true
    loss_threshold: -100.0
    cooldown_minutes: 15
    close_all: true
    cancel_orders: true
    lockout_type: "timer"

# ==============================================================================
# CATEGORY 3: HARD LOCKOUT RULES
# ==============================================================================

  daily_realized_loss:
    enabled: true
    limit: -500.0
    reset_time: "17:00"
    timezone: "America/New_York"
    close_all: true
    cancel_orders: true
    lockout_type: "hard"
    lockout_until_reset: true

  daily_realized_profit:
    enabled: true
    target: 1000.0
    reset_time: "17:00"
    timezone: "America/New_York"
    close_all: true
    cancel_orders: true
    lockout_type: "hard"
    lockout_until_reset: true
    message: "Daily profit target reached! Good job! See you tomorrow."

  session_block_outside:
    enabled: true
    session_hours:
      start: "09:30"
      end: "16:00"
    allowed_days: [0, 1, 2, 3, 4]  # Monday-Friday
    respect_holidays: true
    close_all: true
    cancel_orders: true
    lockout_type: "hard"
    lockout_until_session_start: true

  auth_loss_guard:
    enabled: true
    check_interval_seconds: 30
    close_all: true
    cancel_orders: true
    lockout_type: "hard"
    lockout_permanently: true
    reason: "API canTrade status is false - account disabled"

# ==============================================================================
# CATEGORY 4: AUTOMATION (Optional)
# ==============================================================================

  trade_management:
    enabled: false
    auto_breakeven:
      enabled: true
      profit_threshold_ticks: 4
      offset_ticks: 1
    trailing_stop:
      enabled: true
      trail_ticks: 4
      activation_profit_ticks: 8
```

### accounts.yaml (Multi-Account)

```yaml
# ==============================================================================
# ACCOUNT CONFIGURATION
# ==============================================================================

# TopstepX API Credentials
topstepx:
  username: "${PROJECT_X_USERNAME}"  # From .env
  api_key: "${PROJECT_X_API_KEY}"
  api_url: "https://api.topstepx.com/api"
  websocket_url: "wss://api.topstepx.com"

# Multiple Accounts
accounts:
  - id: "PRAC-V2-126244-84184528"
    name: "Trader A - Conservative"
    config_overrides:
      rules:
        daily_realized_loss:
          limit: -200.0  # Stricter limit
        max_contracts:
          limit: 2

  - id: "PRAC-V2-126244-84184529"
    name: "Trader B - Aggressive"
    config_overrides:
      rules:
        daily_realized_loss:
          limit: -1000.0  # Looser limit
        max_contracts:
          limit: 10

  - id: "PRAC-V2-126244-84184530"
    name: "Trader C - Default"
    # Uses default risk_config.yaml (no overrides)
```

### holidays.yaml (Session Blocks)

```yaml
# ==============================================================================
# MARKET HOLIDAYS
# ==============================================================================

holidays:
  2025:
    - "2025-01-01"  # New Year's Day
    - "2025-01-20"  # Martin Luther King Jr. Day
    - "2025-02-17"  # Presidents' Day
    - "2025-04-18"  # Good Friday
    - "2025-05-26"  # Memorial Day
    - "2025-07-04"  # Independence Day
    - "2025-09-01"  # Labor Day
    - "2025-11-27"  # Thanksgiving
    - "2025-12-25"  # Christmas

  2026:
    - "2026-01-01"  # New Year's Day
    # Add 2026 holidays...
```

---

## Testing Requirements

### Unit Tests (Per Component)

**YAML Loader** (15 tests):
- Load single YAML file
- Load multiple YAML files (risk + accounts + holidays)
- Environment variable expansion
- File not found error
- Invalid YAML syntax error
- Missing required field error
- Nested structure parsing
- Default values applied correctly

**Configuration Validator** (20 tests):
- Daily loss limit must be negative
- Max contracts must be positive
- Reset time must match HH:MM format
- Session end > session start
- Unrealized loss < realized loss
- Trade frequency per_minute < per_hour
- Invalid instrument symbols rejected
- Cross-rule conflict detection

**Hot-Reload System** (10 tests):
- File change detected
- Config reloaded successfully
- Validation failure rollback
- Config diff logged correctly
- Multiple file changes handled
- Reload while running
- Admin CLI manual reload

**Multi-Account Support** (8 tests):
- Load accounts from YAML
- Account-specific overrides applied
- Default config for unknown account
- Per-account state isolation
- Override merge logic correct

### Integration Tests (End-to-End)

**Config Lifecycle** (5 tests):
- Load config → Validate → Apply → Reload → Rollback on error
- Multi-account config isolation
- Hot-reload during active trading
- Admin CLI config edit workflow
- Config persistence across restarts

---

## Key Implementation Questions

### 1. What YAML library should we use?

**Recommendation**: **PyYAML** (already in dependencies)

**Why**:
- ✅ Already in `pyproject.toml` (`pyyaml>=6.0`)
- ✅ Simple API (`yaml.safe_load()`)
- ✅ Widely used, stable
- ✅ Good error messages

**Alternative**: `ruamel.yaml` (preserves comments, formatting)
- ❌ Not in dependencies
- ❌ More complex API
- ✅ Better for round-trip editing (load → modify → save)

**Decision**: Use PyYAML for now, consider ruamel.yaml if we need config editing via code.

---

### 2. Can we deploy without hot-reload initially?

**Answer**: **Yes, but not recommended for production.**

**Minimum Viable Config System** (Days 1-5):
1. ✅ YAML Loader (load config on startup)
2. ✅ Configuration Validator (prevent bad configs)
3. ❌ Hot-Reload (can deploy without this)
4. ❌ Multi-Account (single account works)

**Deployment Without Hot-Reload**:
- ✅ System can start with config from YAML
- ✅ All 13 rules configurable
- ❌ Must restart service to change config
- ❌ Admin must manually edit YAML + restart

**Impact of Skipping Hot-Reload**:
- **Admin workflow**: Edit YAML → Stop service → Start service
- **Downtime**: 5-10 seconds during restart
- **Risk**: Config change requires stopping protection (not ideal)

**Recommendation**: **Implement hot-reload in Week 2** after foundation is solid.

---

### 3. What's the minimum viable config system?

**MVP Feature Set**:

**Week 1 Deliverables** (Must Have):
1. ✅ Load `risk_config.yaml` with nested structure
2. ✅ Pydantic models for all 13 rules
3. ✅ Basic field validation (types, ranges)
4. ✅ Error messages for invalid configs
5. ✅ Unit tests for loader + validator

**What Can Wait** (Nice to Have):
- ❌ Hot-reload (restart service instead)
- ❌ Multi-account (single account initially)
- ❌ Environment variable substitution (hardcode in YAML)
- ❌ SDK account validation (assume account ID is valid)
- ❌ Admin CLI integration (manual YAML editing)

**Result**: With just **YAML Loader + Validator** (6 days), the system can:
- ✅ Load 13 risk rules from configuration
- ✅ Validate configuration prevents bad configs
- ✅ Initialize RiskEngine with correct rules
- ✅ Deploy to production (with manual restarts for config changes)

---

### 4. How do we ensure config changes don't break running system?

**Answer**: **Atomic reload with validation + rollback.**

**Safety Mechanism**:

```python
async def reload_config(self, new_config: RiskConfig) -> bool:
    old_config = self.config

    try:
        # Step 1: Validate NEW config (don't trust YAML)
        new_config.validate()  # Pydantic validators run

        # Step 2: Stop engine temporarily
        await self.engine.stop()

        # Step 3: Apply new config
        self.config = new_config
        await self._add_default_rules()

        # Step 4: Restart engine
        await self.engine.start()

        # Success!
        logger.success("Config reloaded successfully")
        return True

    except Exception as e:
        # Rollback to old config
        logger.error(f"Config reload failed: {e}")

        self.config = old_config
        await self._add_default_rules()
        await self.engine.start()

        logger.warning("Rolled back to previous config")
        return False
```

**Protection Layers**:
1. ✅ **Validation before apply** - Pydantic catches type/range errors
2. ✅ **Atomic swap** - Either fully succeeds or fully rolls back
3. ✅ **Rollback on failure** - Old config restored if anything fails
4. ✅ **Keep old config** - Store last 5 configs in memory
5. ✅ **Logging** - All changes logged with diffs

**Edge Cases Handled**:
- ❌ Invalid YAML syntax → Parse error → Keep old config
- ❌ Missing required field → Validation error → Keep old config
- ❌ Engine fails to start → Exception → Rollback to old config
- ✅ Successful reload → New config active

---

## Summary

### Current State
- **YAML Loader**: 40% complete (basic `from_file()` exists, nested models missing)
- **Configuration Validator**: 0% complete (no validators implemented)
- **Hot-Reload System**: 0% complete (no file watching)
- **Multi-Account Support**: 0% complete (no account isolation)

### Critical Gaps
1. **No nested Pydantic models** for 13 risk rules (~200 LOC)
2. **No field validators** for range/format checking (~100 LOC)
3. **No cross-rule conflict detection** (~80 LOC)
4. **No hot-reload mechanism** (~250 LOC)
5. **No multi-account support** (~240 LOC)

### Recommended Implementation Order
1. **Week 1**: YAML Loader (3 days) + Configuration Validator (3 days)
2. **Week 2**: Multi-Account Support (2 days) + Hot-Reload System (4 days)

### Minimum Viable Product
- **Days 1-6**: YAML Loader + Validator
- **Result**: Can load 13 rules from YAML, validate configs, deploy to production
- **Limitation**: Must restart service to change config (no hot-reload yet)

### Total Effort Estimate
- **Sequential**: 12 days (2.4 weeks)
- **With Parallelization**: ~8 days (1.6 weeks)

---

**Analysis Complete**: 2025-10-25
**Researcher**: RESEARCHER 4 - Configuration System Gap Analyst
**Next Steps**: Begin Week 1 implementation (YAML Loader + Validator)
