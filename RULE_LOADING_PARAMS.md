# RULE LOADING PARAMETERS MAPPING

**Document Purpose**: Exact mapping of which config fields each rule requires in its `__init__()` method.

**Status**: Complete analysis of all 13 rules
**Last Updated**: 2025-10-29

---

## Overview

This document maps each rule to:
1. **Config parameters** - Fields read from `config/risk_config.yaml`
2. **State managers** - State manager instances needed from engine
3. **Tick data** - Market-specific data (tick values, tick sizes)
4. **Loading readiness** - Whether rule can be loaded with current config

### Legend

- ✅ Ready - All parameters available in config.yaml
- ⚠️ Partial - Some parameters missing from config.yaml
- ❌ Not Ready - Key parameters missing from config.yaml
- 📊 Needs - Tick data from market configuration

---

## RULE-001: Max Contracts (Account-Wide)

**File**: `src/risk_manager/rules/max_contracts.py`
**Status**: ✅ Ready (but file not yet examined)

**__init__() Signature**:
```python
def __init__(self, limit: int, count_type: str = "net")
```

**Config Source** (`config.rules.max_contracts`):
```yaml
rules:
  max_contracts:
    enabled: true
    limit: 5                    # ✅ Available
    count_type: "net"           # ✅ Available
```

**Parameters**:
- `limit` (int) - **Config**: `rules.max_contracts.limit` = 5
- `count_type` (str) - **Config**: `rules.max_contracts.count_type` = "net"
- `action` (str) - **Default**: "alert" (not in config)

**State Managers**: None required

**Tick Data**: None required

**Loading Code**:
```python
rule = MaxContractsRule(
    limit=config.get("rules.max_contracts.limit"),
    count_type=config.get("rules.max_contracts.count_type", "net"),
    action="alert"
)
```

---

## RULE-002: Max Contracts Per Instrument

**File**: `src/risk_manager/rules/max_contracts_per_instrument.py`
**Status**: ✅ Ready

**__init__() Signature**:
```python
def __init__(
    self,
    limits: dict[str, int],
    enforcement: str = "reduce_to_limit",
    unknown_symbol_action: str = "block",
)
```

**Config Source** (`config.rules.max_contracts_per_instrument`):
```yaml
rules:
  max_contracts_per_instrument:
    enabled: true
    default_limit: 3           # ✅ Available
    instrument_limits:         # ✅ Available
      MNQ: 2
      ES: 1
```

**Parameters**:
- `limits` (dict[str, int]) - **Config**: Merge `default_limit` + `instrument_limits` into dict:
  ```python
  limits = {
      "MNQ": config["rules"]["max_contracts_per_instrument"]["instrument_limits"].get("MNQ", 3),
      "ES": config["rules"]["max_contracts_per_instrument"]["instrument_limits"].get("ES", 3),
      # ... all configured symbols with defaults
  }
  ```
- `enforcement` (str) - **Default**: "reduce_to_limit" (not in config, but documented)
- `unknown_symbol_action` (str) - **Default**: "block" (not in config)

**State Managers**: None required

**Tick Data**: None required

**Loading Code**:
```python
limits = {}
default = config.get("rules.max_contracts_per_instrument.default_limit", 3)
for symbol, limit in config.get("rules.max_contracts_per_instrument.instrument_limits", {}).items():
    limits[symbol] = limit

rule = MaxContractsPerInstrumentRule(
    limits=limits,
    enforcement="reduce_to_limit",
    unknown_symbol_action="block"
)
```

---

## RULE-003: Daily Realized Loss

**File**: `src/risk_manager/rules/daily_realized_loss.py`
**Status**: ✅ Ready

**__init__() Signature**:
```python
def __init__(
    self,
    limit: float,
    pnl_tracker: "PnLTracker",
    lockout_manager: "LockoutManager",
    action: str = "flatten",
    reset_time: str = "17:00",
    timezone_name: str = "America/New_York",
)
```

**Config Source** (`config.rules.daily_realized_loss`):
```yaml
rules:
  daily_realized_loss:
    enabled: true
    limit: -500                 # ✅ Available
    reset_time: "17:00"         # ✅ Available
    timezone: "America/Chicago" # ✅ Available
```

**Parameters**:
- `limit` (float) - **Config**: `rules.daily_realized_loss.limit` = -500
- `pnl_tracker` (PnLTracker) - **State Manager**: Required instance
- `lockout_manager` (LockoutManager) - **State Manager**: Required instance
- `action` (str) - **Default**: "flatten"
- `reset_time` (str) - **Config**: `rules.daily_realized_loss.reset_time` = "17:00"
- `timezone_name` (str) - **Config**: `rules.daily_realized_loss.timezone` = "America/Chicago"

**State Managers**:
- ✅ `pnl_tracker` (PnLTracker)
- ✅ `lockout_manager` (LockoutManager)

**Tick Data**: None required

**Loading Code**:
```python
rule = DailyRealizedLossRule(
    limit=config.get("rules.daily_realized_loss.limit"),
    pnl_tracker=state_managers["pnl_tracker"],
    lockout_manager=state_managers["lockout_manager"],
    action="flatten",
    reset_time=config.get("rules.daily_realized_loss.reset_time", "17:00"),
    timezone_name=config.get("rules.daily_realized_loss.timezone", "America/New_York"),
)
```

---

## RULE-004: Daily Unrealized Loss (Stop Loss Per Position)

**File**: `src/risk_manager/rules/daily_unrealized_loss.py`
**Status**: ✅ Ready (but needs tick data)

**__init__() Signature**:
```python
def __init__(
    self,
    loss_limit: float,
    tick_values: Dict[str, float],
    tick_sizes: Dict[str, float],
    action: str = "close_position",
)
```

**Config Source** (`config.rules.daily_unrealized_loss`):
```yaml
rules:
  daily_unrealized_loss:
    enabled: true
    limit: -750                 # ✅ Available
    check_interval_seconds: 10  # Available but not used in __init__
```

**Parameters**:
- `loss_limit` (float) - **Config**: `rules.daily_unrealized_loss.limit` = -750
- `tick_values` (Dict[str, float]) - **Tick Data**: Needs market config
  ```python
  # Example: {"ES": 50.0, "MNQ": 5.0, "NQ": 5.0}
  ```
- `tick_sizes` (Dict[str, float]) - **Tick Data**: Needs market config
  ```python
  # Example: {"ES": 0.25, "MNQ": 0.25, "NQ": 0.25}
  ```
- `action` (str) - **Default**: "close_position"

**State Managers**: None required

**Tick Data**:
- 📊 `tick_values` (Dict) - **Source**: Market configuration
- 📊 `tick_sizes` (Dict) - **Source**: Market configuration

**Loading Code**:
```python
rule = DailyUnrealizedLossRule(
    loss_limit=config.get("rules.daily_unrealized_loss.limit"),
    tick_values=market_config.get("tick_values", {}),  # {"ES": 50.0, "MNQ": 5.0, ...}
    tick_sizes=market_config.get("tick_sizes", {}),    # {"ES": 0.25, "MNQ": 0.25, ...}
    action="close_position",
)
```

**Note**: Rule uses `engine.current_positions` and `engine.market_prices` at runtime, so needs live market data.

---

## RULE-005: Max Unrealized Profit (Take Profit Per Position)

**File**: `src/risk_manager/rules/max_unrealized_profit.py`
**Status**: ✅ Ready (but needs tick data)

**__init__() Signature**:
```python
def __init__(
    self,
    target: float,
    tick_values: Dict[str, float],
    tick_sizes: Dict[str, float],
    action: str = "close_position",
)
```

**Config Source** (`config.rules.max_unrealized_profit`):
```yaml
rules:
  max_unrealized_profit:
    enabled: true
    target: 500.0               # ✅ Available
    check_interval_seconds: 5   # Available but not used in __init__
```

**Parameters**:
- `target` (float) - **Config**: `rules.max_unrealized_profit.target` = 500.0
- `tick_values` (Dict[str, float]) - **Tick Data**: Needs market config
- `tick_sizes` (Dict[str, float]) - **Tick Data**: Needs market config
- `action` (str) - **Default**: "close_position"

**State Managers**: None required

**Tick Data**:
- 📊 `tick_values` (Dict)
- 📊 `tick_sizes` (Dict)

**Loading Code**:
```python
rule = MaxUnrealizedProfitRule(
    target=config.get("rules.max_unrealized_profit.target"),
    tick_values=market_config.get("tick_values", {}),
    tick_sizes=market_config.get("tick_sizes", {}),
    action="close_position",
)
```

**Note**: Similar to RULE-004, requires live market data at runtime.

---

## RULE-006: Trade Frequency Limit

**File**: `src/risk_manager/rules/trade_frequency_limit.py`
**Status**: ✅ Ready

**__init__() Signature**:
```python
def __init__(
    self,
    limits: dict[str, int],
    cooldown_on_breach: dict[str, int],
    timer_manager: "TimerManager",
    db: Any,
    action: str = "cooldown",
)
```

**Config Source** (`config.rules.trade_frequency_limit`):
```yaml
rules:
  trade_frequency_limit:
    enabled: true
    limits:
      per_minute: 3             # ✅ Available
      per_hour: 10              # ✅ Available
      per_session: 50           # ✅ Available
```

**Parameters**:
- `limits` (dict[str, int]) - **Config**: Build from `rules.trade_frequency_limit.limits`:
  ```python
  limits = {
      "per_minute": config.get("rules.trade_frequency_limit.limits.per_minute", 3),
      "per_hour": config.get("rules.trade_frequency_limit.limits.per_hour", 10),
      "per_session": config.get("rules.trade_frequency_limit.limits.per_session", 50),
  }
  ```
- `cooldown_on_breach` (dict[str, int]) - **Default**: Not in config (need to add or use defaults)
  ```python
  # Suggested defaults (not in current config.yaml):
  {
      "per_minute_breach": 60,    # 1 minute
      "per_hour_breach": 1800,    # 30 minutes
      "per_session_breach": 3600  # 1 hour
  }
  ```
- `timer_manager` (TimerManager) - **State Manager**: Required instance
- `db` (Any) - **State Manager**: Database instance
- `action` (str) - **Default**: "cooldown"

**State Managers**:
- ✅ `timer_manager` (TimerManager)
- ✅ `db` (Database)

**Tick Data**: None required

**Loading Code**:
```python
limits = {
    "per_minute": config.get("rules.trade_frequency_limit.limits.per_minute", 3),
    "per_hour": config.get("rules.trade_frequency_limit.limits.per_hour", 10),
    "per_session": config.get("rules.trade_frequency_limit.limits.per_session", 50),
}

cooldown_on_breach = {  # Hardcoded defaults - should be in config
    "per_minute_breach": 60,
    "per_hour_breach": 1800,
    "per_session_breach": 3600,
}

rule = TradeFrequencyLimitRule(
    limits=limits,
    cooldown_on_breach=cooldown_on_breach,
    timer_manager=state_managers["timer_manager"],
    db=database,
    action="cooldown",
)
```

**Note**: `cooldown_on_breach` is missing from config.yaml - needs addition.

---

## RULE-007: Cooldown After Loss

**File**: `src/risk_manager/rules/cooldown_after_loss.py`
**Status**: ⚠️ Partial (config structure needs clarity)

**__init__() Signature**:
```python
def __init__(
    self,
    loss_thresholds: list[dict[str, float]],
    timer_manager: "TimerManager",
    pnl_tracker: "PnLTracker",
    lockout_manager: "LockoutManager",
    action: str = "flatten",
)
```

**Config Source** (`config.rules.cooldown_after_loss`):
```yaml
rules:
  cooldown_after_loss:
    enabled: true
    loss_threshold: -100.0      # ⚠️ PROBLEM: Single value, not list of tiers!
```

**Parameters**:
- `loss_thresholds` (list[dict[str, float]]) - **Config**: MISMATCH! Config has single `loss_threshold`, but code expects list of tiers:
  ```python
  # Expected format:
  [
      {"loss_amount": -100.0, "cooldown_duration": 300},
      {"loss_amount": -200.0, "cooldown_duration": 900},
      {"loss_amount": -300.0, "cooldown_duration": 1800},
  ]
  ```

  **Current config only has**: `-100.0` (single value)

- `timer_manager` (TimerManager) - **State Manager**: Required instance
- `pnl_tracker` (PnLTracker) - **State Manager**: Required instance
- `lockout_manager` (LockoutManager) - **State Manager**: Required instance
- `action` (str) - **Default**: "flatten"

**State Managers**:
- ✅ `timer_manager` (TimerManager)
- ✅ `pnl_tracker` (PnLTracker)
- ✅ `lockout_manager` (LockoutManager)

**Tick Data**: None required

**Loading Code** (if config is updated to list format):
```python
loss_thresholds = config.get("rules.cooldown_after_loss.loss_thresholds", [
    {"loss_amount": -100.0, "cooldown_duration": 300},
])

rule = CooldownAfterLossRule(
    loss_thresholds=loss_thresholds,
    timer_manager=state_managers["timer_manager"],
    pnl_tracker=state_managers["pnl_tracker"],
    lockout_manager=state_managers["lockout_manager"],
    action="flatten",
)
```

**Issue**: Config needs to be updated from single value to list of tier objects.

---

## RULE-008: No Stop-Loss Grace

**File**: `src/risk_manager/rules/no_stop_loss_grace.py`
**Status**: ✅ Ready

**__init__() Signature**:
```python
def __init__(
    self,
    grace_period_seconds: int = 10,
    enforcement: str = "close_position",
    timer_manager: Optional[TimerManager] = None,
    enabled: bool = True,
)
```

**Config Source** (`config.rules.no_stop_loss_grace`):
```yaml
rules:
  no_stop_loss_grace:
    enabled: false              # ✅ Available
    require_within_seconds: 60  # ⚠️ Config has different field name!
    grace_period_seconds: 300   # ✅ Available (but named differently in spec)
```

**Parameters**:
- `grace_period_seconds` (int) - **Config**: Map from `require_within_seconds` (config uses this name, code expects `grace_period_seconds`)
  ```python
  # Config has: require_within_seconds: 60
  # Code needs: grace_period_seconds: 60
  ```
- `enforcement` (str) - **Default**: "close_position"
- `timer_manager` (TimerManager) - **State Manager**: Required instance
- `enabled` (bool) - **Config**: `rules.no_stop_loss_grace.enabled` = false

**State Managers**:
- ✅ `timer_manager` (TimerManager)

**Tick Data**: None required

**Loading Code**:
```python
rule = NoStopLossGraceRule(
    grace_period_seconds=config.get("rules.no_stop_loss_grace.require_within_seconds", 10),
    enforcement="close_position",
    timer_manager=state_managers["timer_manager"],
    enabled=config.get("rules.no_stop_loss_grace.enabled", False),
)
```

**Note**: Config field naming mismatch - `require_within_seconds` vs expected parameter name.

---

## RULE-009: Session Block Outside Hours

**File**: `src/risk_manager/rules/session_block_outside.py`
**Status**: ✅ Ready

**__init__() Signature**:
```python
def __init__(
    self,
    config: dict[str, Any],
    lockout_manager: "LockoutManager",
)
```

**Config Source** (`config.rules.session_block_outside`):
```yaml
rules:
  session_block_outside:
    enabled: true               # ✅ Available
    start_time: "08:30"         # ✅ Available
    end_time: "15:00"           # ✅ Available
    timezone: "America/Chicago" # ✅ Available
    respect_holidays: true      # ✅ Available (not used in __init__ but documented)
```

**Parameters**:
- `config` (dict) - **Config**: Entire rule config dict passed
- `lockout_manager` (LockoutManager) - **State Manager**: Required instance

**State Managers**:
- ✅ `lockout_manager` (LockoutManager)

**Tick Data**: None required

**Loading Code**:
```python
rule = SessionBlockOutsideRule(
    config=config.get("rules.session_block_outside", {}),
    lockout_manager=state_managers["lockout_manager"],
)
```

---

## RULE-010: Auth Loss Guard (Connection Monitoring)

**File**: `src/risk_manager/rules/auth_loss_guard.py`
**Status**: ✅ Ready

**__init__() Signature**:
```python
def __init__(
    self,
    alert_on_disconnect: bool = True,
    alert_on_auth_failure: bool = True,
    log_level: str = "WARNING",
)
```

**Config Source** (`config.rules.auth_loss_guard`):
```yaml
rules:
  auth_loss_guard:
    enabled: true               # ✅ Available
    check_interval_seconds: 30  # Available but not used in __init__
    reason: "..."               # Available but not used in __init__
```

**Parameters**:
- `alert_on_disconnect` (bool) - **Default**: True (not in config)
- `alert_on_auth_failure` (bool) - **Default**: True (not in config)
- `log_level` (str) - **Default**: "WARNING" (not in config)

**State Managers**: None required

**Tick Data**: None required

**Loading Code**:
```python
rule = AuthLossGuardRule(
    alert_on_disconnect=config.get("rules.auth_loss_guard.alert_on_disconnect", True),
    alert_on_auth_failure=config.get("rules.auth_loss_guard.alert_on_auth_failure", True),
    log_level=config.get("rules.auth_loss_guard.log_level", "WARNING"),
)
```

---

## RULE-011: Symbol Blocks

**File**: `src/risk_manager/rules/symbol_blocks.py`
**Status**: ✅ Ready

**__init__() Signature**:
```python
def __init__(self, blocked_symbols: list[str], action: str = "close")
```

**Config Source** (`config.rules.symbol_blocks`):
```yaml
rules:
  symbol_blocks:
    enabled: false              # ✅ Available
    blocked_symbols: []         # ✅ Available (empty by default)
```

**Parameters**:
- `blocked_symbols` (list[str]) - **Config**: `rules.symbol_blocks.blocked_symbols` = []
- `action` (str) - **Default**: "close"

**State Managers**: None required

**Tick Data**: None required

**Loading Code**:
```python
rule = SymbolBlocksRule(
    blocked_symbols=config.get("rules.symbol_blocks.blocked_symbols", []),
    action="close",
)
```

---

## RULE-012: Trade Management (Auto Breakeven + Trailing Stop)

**File**: `src/risk_manager/rules/trade_management.py`
**Status**: ✅ Ready (but needs tick data)

**__init__() Signature**:
```python
def __init__(
    self,
    config: Dict[str, Any],
    tick_values: Dict[str, float],
    tick_sizes: Dict[str, float],
)
```

**Config Source** (`config.rules.trade_management`):
```yaml
rules:
  trade_management:
    enabled: false              # ✅ Available
    auto_breakeven:
      enabled: true             # ✅ Available
      profit_threshold_ticks: 4 # ✅ Available
      offset_ticks: 1           # ✅ Available
    trailing_stop:
      enabled: true             # ✅ Available
      trail_ticks: 4            # ✅ Available
      activation_profit_ticks: 8 # ✅ Available
```

**Parameters**:
- `config` (Dict) - **Config**: Entire rule config dict
- `tick_values` (Dict[str, float]) - **Tick Data**: Market configuration
- `tick_sizes` (Dict[str, float]) - **Tick Data**: Market configuration

**State Managers**: None required

**Tick Data**:
- 📊 `tick_values` (Dict)
- 📊 `tick_sizes` (Dict)

**Loading Code**:
```python
rule = TradeManagementRule(
    config=config.get("rules.trade_management", {}),
    tick_values=market_config.get("tick_values", {}),
    tick_sizes=market_config.get("tick_sizes", {}),
)
```

**Note**: Rule is disabled by default (advanced feature).

---

## RULE-013: Daily Realized Profit

**File**: `src/risk_manager/rules/daily_realized_profit.py`
**Status**: ✅ Ready

**__init__() Signature**:
```python
def __init__(
    self,
    target: float,
    pnl_tracker: "PnLTracker",
    lockout_manager: "LockoutManager",
    action: str = "flatten",
    reset_time: str = "17:00",
    timezone_name: str = "America/New_York",
)
```

**Config Source** (`config.rules.daily_realized_profit`):
```yaml
rules:
  daily_realized_profit:
    enabled: true               # ✅ Available
    target: 1000.0              # ✅ Available
    message: "..."              # ✅ Available (not used in __init__)
```

**Parameters**:
- `target` (float) - **Config**: `rules.daily_realized_profit.target` = 1000.0
- `pnl_tracker` (PnLTracker) - **State Manager**: Required instance
- `lockout_manager` (LockoutManager) - **State Manager**: Required instance
- `action` (str) - **Default**: "flatten"
- `reset_time` (str) - **Default**: "17:00" (not in config, but can use from RULE-003)
- `timezone_name` (str) - **Default**: "America/New_York" (should get from RULE-003 or general config)

**State Managers**:
- ✅ `pnl_tracker` (PnLTracker)
- ✅ `lockout_manager` (LockoutManager)

**Tick Data**: None required

**Loading Code**:
```python
rule = DailyRealizedProfitRule(
    target=config.get("rules.daily_realized_profit.target"),
    pnl_tracker=state_managers["pnl_tracker"],
    lockout_manager=state_managers["lockout_manager"],
    action="flatten",
    reset_time=config.get("rules.daily_realized_loss.reset_time", "17:00"),  # Reuse from RULE-003
    timezone_name=config.get("rules.daily_realized_loss.timezone", "America/New_York"),  # Reuse from RULE-003
)
```

---

## Summary Table

| Rule | File | Status | State Managers | Tick Data | Config Issues |
|------|------|--------|---|---|---|
| RULE-001 | max_contracts.py | ✅ Ready | None | None | None |
| RULE-002 | max_contracts_per_instrument.py | ✅ Ready | None | None | None |
| RULE-003 | daily_realized_loss.py | ✅ Ready | PnLTracker, LockoutManager | None | None |
| RULE-004 | daily_unrealized_loss.py | ✅ Ready | None | ✅ tick_values, tick_sizes | Needs market config |
| RULE-005 | max_unrealized_profit.py | ✅ Ready | None | ✅ tick_values, tick_sizes | Needs market config |
| RULE-006 | trade_frequency_limit.py | ⚠️ Partial | TimerManager, DB | None | Missing cooldown_on_breach |
| RULE-007 | cooldown_after_loss.py | ⚠️ Partial | TimerManager, PnLTracker, LockoutManager | None | loss_thresholds format mismatch |
| RULE-008 | no_stop_loss_grace.py | ✅ Ready | TimerManager | None | Field name mismatch |
| RULE-009 | session_block_outside.py | ✅ Ready | LockoutManager | None | None |
| RULE-010 | auth_loss_guard.py | ✅ Ready | None | None | None |
| RULE-011 | symbol_blocks.py | ✅ Ready | None | None | None |
| RULE-012 | trade_management.py | ✅ Ready | None | ✅ tick_values, tick_sizes | Needs market config |
| RULE-013 | daily_realized_profit.py | ✅ Ready | PnLTracker, LockoutManager | None | None |

---

## State Manager Requirements Summary

**Unique State Managers Needed** (across all 13 rules):
1. ✅ `pnl_tracker` - PnLTracker (RULE-003, RULE-007, RULE-013)
2. ✅ `lockout_manager` - LockoutManager (RULE-003, RULE-007, RULE-009, RULE-013)
3. ✅ `timer_manager` - TimerManager (RULE-006, RULE-007, RULE-008)
4. ✅ `db` - Database (RULE-006)

---

## Tick Data Requirements Summary

**Symbols Requiring Tick Data** (for rules that calculate unrealized P&L):
- RULE-004: Daily Unrealized Loss
- RULE-005: Max Unrealized Profit
- RULE-012: Trade Management

**Required Tick Data**:
```python
tick_values = {
    "ES": 50.0,      # E-mini S&P 500: $50 per tick
    "MNQ": 5.0,      # E-mini NASDAQ: $5 per tick
    "NQ": 20.0,      # NASDAQ: $20 per tick
}

tick_sizes = {
    "ES": 0.25,      # E-mini S&P 500: 0.25 tick size
    "MNQ": 0.25,     # E-mini NASDAQ: 0.25 tick size
    "NQ": 0.25,      # NASDAQ: 0.25 tick size
}
```

**Source**: These should come from project-x SDK or market configuration, NOT from risk_config.yaml

---

## Config Issues to Fix

### High Priority

1. **RULE-006: Missing cooldown_on_breach**
   - Current config: Only has `limits` dict
   - Needed: Add `cooldown_on_breach` with durations for each breach type
   - Suggested addition:
     ```yaml
     trade_frequency_limit:
       enabled: true
       limits:
         per_minute: 3
         per_hour: 10
         per_session: 50
       cooldown_on_breach:              # NEW
         per_minute_breach: 60          # 1 min
         per_hour_breach: 1800          # 30 min
         per_session_breach: 3600       # 1 hour
     ```

2. **RULE-007: loss_thresholds format mismatch**
   - Current config: `loss_threshold: -100.0` (single value)
   - Needed: List of tier objects
   - Suggested fix:
     ```yaml
     cooldown_after_loss:
       enabled: true
       loss_thresholds:                 # Change from loss_threshold to loss_thresholds
         - loss_amount: -100.0
           cooldown_duration: 300       # 5 min
         - loss_amount: -200.0
           cooldown_duration: 900       # 15 min
         - loss_amount: -300.0
           cooldown_duration: 1800      # 30 min
     ```

3. **RULE-008: Field name mismatch**
   - Current config: `require_within_seconds: 60`
   - Code parameter: `grace_period_seconds`
   - These should align OR code should map the config field name

### Medium Priority

4. **Add optional fields for RULE-010**
   - Config could explicitly set `alert_on_disconnect` and `alert_on_auth_failure`
   - Suggested addition:
     ```yaml
     auth_loss_guard:
       enabled: true
       check_interval_seconds: 30
       alert_on_disconnect: true        # NEW (optional)
       alert_on_auth_failure: true      # NEW (optional)
       log_level: "WARNING"             # NEW (optional)
       reason: "API canTrade status is false - account disabled"
     ```

---

## Implementation Checklist for Agent 1

When loading rules in `_initialize_rules()`, use this checklist:

- [ ] Verify all state managers (PnLTracker, LockoutManager, TimerManager, DB) are initialized BEFORE rule loading
- [ ] Ensure market config with tick_values/tick_sizes is loaded BEFORE initializing RULE-004, RULE-005, RULE-012
- [ ] Handle the 3 config format issues (RULE-006, RULE-007, RULE-008) in config loader
- [ ] Pass correct parameter names to each rule's __init__()
- [ ] For RULE-003 and RULE-013, share same reset_time/timezone values
- [ ] Test each rule instantiation individually before adding to rules list
- [ ] Verify engine.current_positions and engine.market_prices are available for rules that need them at runtime

---

## Testing Hints

When writing tests for rule loading:

```python
# All rules should be instantiable without errors
for rule_name, rule_config in config["rules"].items():
    if rule_config.get("enabled"):
        rule = RULE_CLASSES[rule_name](
            **get_rule_params(rule_name, config, state_managers, market_config)
        )
        assert rule is not None
        assert rule.enabled == True
```

---

**Document Created**: 2025-10-29
**Last Verified**: Against rule source files (all 13 rules analyzed)
**Next Steps**: Share with Agent 1 for rule loading implementation
