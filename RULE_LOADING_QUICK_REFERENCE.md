# RULE LOADING - QUICK REFERENCE FOR AGENT 1

**Purpose**: Fast lookup for what each rule needs during `_initialize_rules()`

---

## Instant Lookup: What Does This Rule Need?

### RULE-001: MaxContractsRule
```python
rule = MaxContractsRule(
    limit=config["rules"]["max_contracts"]["limit"],           # 5
    count_type=config["rules"]["max_contracts"]["count_type"]  # "net"
)
```
✅ No state managers | No tick data

---

### RULE-002: MaxContractsPerInstrumentRule
```python
limits = config["rules"]["max_contracts_per_instrument"]["instrument_limits"]
rule = MaxContractsPerInstrumentRule(limits=limits)
```
✅ No state managers | No tick data

---

### RULE-003: DailyRealizedLossRule
```python
rule = DailyRealizedLossRule(
    limit=config["rules"]["daily_realized_loss"]["limit"],               # -500
    pnl_tracker=pnl_tracker,                                             # STATE
    lockout_manager=lockout_manager,                                     # STATE
    reset_time=config["rules"]["daily_realized_loss"]["reset_time"],     # "17:00"
    timezone_name=config["rules"]["daily_realized_loss"]["timezone"]     # "America/Chicago"
)
```
⚠️ Needs: pnl_tracker, lockout_manager

---

### RULE-004: DailyUnrealizedLossRule
```python
rule = DailyUnrealizedLossRule(
    loss_limit=config["rules"]["daily_unrealized_loss"]["limit"],  # -750
    tick_values=market_config["tick_values"],                       # {"ES": 50.0, "MNQ": 5.0, ...}
    tick_sizes=market_config["tick_sizes"]                          # {"ES": 0.25, "MNQ": 0.25, ...}
)
```
📊 Needs: tick_values, tick_sizes from market config

---

### RULE-005: MaxUnrealizedProfitRule
```python
rule = MaxUnrealizedProfitRule(
    target=config["rules"]["max_unrealized_profit"]["target"],     # 500.0
    tick_values=market_config["tick_values"],                       # Market data
    tick_sizes=market_config["tick_sizes"]                          # Market data
)
```
📊 Needs: tick_values, tick_sizes from market config

---

### RULE-006: TradeFrequencyLimitRule
```python
limits = {
    "per_minute": config["rules"]["trade_frequency_limit"]["limits"]["per_minute"],      # 3
    "per_hour": config["rules"]["trade_frequency_limit"]["limits"]["per_hour"],          # 10
    "per_session": config["rules"]["trade_frequency_limit"]["limits"]["per_session"]     # 50
}

# ⚠️ ISSUE: cooldown_on_breach not in config! Use defaults:
cooldown_on_breach = {
    "per_minute_breach": 60,
    "per_hour_breach": 1800,
    "per_session_breach": 3600
}

rule = TradeFrequencyLimitRule(
    limits=limits,
    cooldown_on_breach=cooldown_on_breach,
    timer_manager=timer_manager,                                    # STATE
    db=database                                                     # STATE
)
```
⚠️ Needs: timer_manager, db | ⚠️ ISSUE: cooldown_on_breach missing from config

---

### RULE-007: CooldownAfterLossRule
```python
# ⚠️ ISSUE: Config has single loss_threshold, code expects list of tiers!
# Map config value to list:
loss_thresholds = [
    {"loss_amount": config["rules"]["cooldown_after_loss"]["loss_threshold"],
     "cooldown_duration": 300}  # Default: 5 min
]

rule = CooldownAfterLossRule(
    loss_thresholds=loss_thresholds,
    timer_manager=timer_manager,                                    # STATE
    pnl_tracker=pnl_tracker,                                       # STATE
    lockout_manager=lockout_manager                                # STATE
)
```
⚠️ Needs: timer_manager, pnl_tracker, lockout_manager | ⚠️ ISSUE: Config format mismatch

---

### RULE-008: NoStopLossGraceRule
```python
# ⚠️ ISSUE: Config uses "require_within_seconds", code expects "grace_period_seconds"
grace_period = config["rules"]["no_stop_loss_grace"]["require_within_seconds"]  # 60

rule = NoStopLossGraceRule(
    grace_period_seconds=grace_period,
    timer_manager=timer_manager,                                    # STATE
    enabled=config["rules"]["no_stop_loss_grace"]["enabled"]        # false
)
```
⚠️ Needs: timer_manager | ⚠️ ISSUE: Field name mismatch in config

---

### RULE-009: SessionBlockOutsideRule
```python
rule = SessionBlockOutsideRule(
    config=config["rules"]["session_block_outside"],  # Pass entire config dict
    lockout_manager=lockout_manager                   # STATE
)
```
⚠️ Needs: lockout_manager | ✅ Cleanest interface

---

### RULE-010: AuthLossGuardRule
```python
rule = AuthLossGuardRule(
    alert_on_disconnect=config["rules"]["auth_loss_guard"].get("alert_on_disconnect", True),
    alert_on_auth_failure=config["rules"]["auth_loss_guard"].get("alert_on_auth_failure", True),
    log_level=config["rules"]["auth_loss_guard"].get("log_level", "WARNING")
)
```
✅ No state managers | No tick data | ✅ All defaults optional

---

### RULE-011: SymbolBlocksRule
```python
rule = SymbolBlocksRule(
    blocked_symbols=config["rules"]["symbol_blocks"]["blocked_symbols"]  # []
)
```
✅ No state managers | No tick data | ✅ Simplest rule

---

### RULE-012: TradeManagementRule
```python
rule = TradeManagementRule(
    config=config["rules"]["trade_management"],        # Pass entire config dict
    tick_values=market_config["tick_values"],           # Market data
    tick_sizes=market_config["tick_sizes"]              # Market data
)
```
📊 Needs: tick_values, tick_sizes | ⚠️ Advanced feature (disabled by default)

---

### RULE-013: DailyRealizedProfitRule
```python
rule = DailyRealizedProfitRule(
    target=config["rules"]["daily_realized_profit"]["target"],           # 1000.0
    pnl_tracker=pnl_tracker,                                             # STATE
    lockout_manager=lockout_manager,                                     # STATE
    reset_time=config["rules"]["daily_realized_loss"]["reset_time"],     # Reuse from RULE-003
    timezone_name=config["rules"]["daily_realized_loss"]["timezone"]     # Reuse from RULE-003
)
```
⚠️ Needs: pnl_tracker, lockout_manager | ✅ Shares reset_time/timezone with RULE-003

---

## State Manager Dependencies

### Which Rules Need What?

```
pnl_tracker:      RULE-003, RULE-007, RULE-013
lockout_manager:  RULE-003, RULE-007, RULE-009, RULE-013
timer_manager:    RULE-006, RULE-007, RULE-008
database:         RULE-006
market_config:    RULE-004, RULE-005, RULE-012
```

### Load Order Requirement

1. **Load state managers FIRST**:
   - pnl_tracker
   - lockout_manager
   - timer_manager
   - database

2. **Load market config SECOND**:
   - tick_values
   - tick_sizes

3. **Load rules THIRD** (in any order):
   - Use state managers from step 1
   - Use market config from step 2

---

## Quick Config Issues Checklist

- [ ] **RULE-006**: Add `cooldown_on_breach` dict to config
- [ ] **RULE-007**: Change `loss_threshold` (single) to `loss_thresholds` (list)
- [ ] **RULE-008**: Clarify field naming: `require_within_seconds` vs `grace_period_seconds`
- [ ] **All tick-data rules**: Ensure market config is loaded before creating rules

---

## Pseudocode Template

```python
async def _initialize_rules(self) -> None:
    """Initialize all 13 risk rules."""

    # Step 1: Ensure state managers exist
    assert self.engine.pnl_tracker is not None
    assert self.engine.lockout_manager is not None
    assert self.engine.timer_manager is not None
    assert self.engine.database is not None

    # Step 2: Load market config
    market_config = self._load_market_config()  # Returns {"tick_values": {...}, "tick_sizes": {...}}

    # Step 3: Create rules
    rules = []

    # RULE-001
    if config["rules"]["max_contracts"]["enabled"]:
        rules.append(MaxContractsRule(
            limit=config["rules"]["max_contracts"]["limit"],
            count_type=config["rules"]["max_contracts"]["count_type"]
        ))

    # RULE-002
    if config["rules"]["max_contracts_per_instrument"]["enabled"]:
        rules.append(MaxContractsPerInstrumentRule(
            limits=config["rules"]["max_contracts_per_instrument"]["instrument_limits"]
        ))

    # ... continue for all 13 rules

    self.rules = rules
    logger.info(f"Loaded {len(self.rules)} risk rules")
```

---

## Ready to Code?

1. Read this quick reference ✅
2. Read the full `RULE_LOADING_PARAMS.md` for details ✅
3. Start with RULE-001 and RULE-011 (simplest) ✅
4. Move to state-manager rules (RULE-003, RULE-009, RULE-013) ✅
5. Handle config issues (RULE-006, RULE-007, RULE-008) ⚠️
6. Finish with tick-data rules (RULE-004, RULE-005, RULE-012) 📊
7. Test each rule instantiation individually ✅

---

**Generated**: 2025-10-29
**For**: Agent 1 (Rule Loading Implementation)
