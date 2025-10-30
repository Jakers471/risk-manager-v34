# RULE LOADING VALIDATION CHECKLIST

**Purpose**: Validation steps to ensure rules load correctly and parameters match contracts

**Use This When**: Testing rule loading implementation before integration tests

---

## Pre-Loading Validation

### State Manager Availability

Before initializing any rule, verify all state managers exist:

```python
def validate_state_managers(engine):
    """Verify all state managers are initialized."""
    checks = {
        "pnl_tracker": hasattr(engine, "pnl_tracker") and engine.pnl_tracker is not None,
        "lockout_manager": hasattr(engine, "lockout_manager") and engine.lockout_manager is not None,
        "timer_manager": hasattr(engine, "timer_manager") and engine.timer_manager is not None,
        "database": hasattr(engine, "database") and engine.database is not None,
    }

    all_passed = all(checks.values())

    for manager, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {manager}")

    assert all_passed, "Missing state managers - cannot load rules"
    return True
```

### Market Config Availability

Before creating tick-data rules (RULE-004, RULE-005, RULE-012):

```python
def validate_market_config(market_config):
    """Verify market configuration has required tick data."""
    required_symbols = {"ES", "MNQ", "NQ"}  # From config/risk_config.yaml

    assert "tick_values" in market_config, "Missing tick_values in market config"
    assert "tick_sizes" in market_config, "Missing tick_sizes in market config"

    tick_values = market_config["tick_values"]
    tick_sizes = market_config["tick_sizes"]

    for symbol in required_symbols:
        assert symbol in tick_values, f"Missing tick_value for {symbol}"
        assert symbol in tick_sizes, f"Missing tick_size for {symbol}"

    print("✅ Market config verified")
    return True
```

---

## Per-Rule Validation

### Template: Generic Rule Validation

```python
def validate_rule_loading(rule_name, rule_class, params, config):
    """
    Validate a single rule can be instantiated with correct parameters.

    Args:
        rule_name: Rule name (e.g., "RULE-001")
        rule_class: Rule class (e.g., MaxContractsRule)
        params: Dict of __init__ parameters
        config: Full config dict (for reference)

    Returns:
        True if validation passed
    """
    try:
        # Attempt instantiation
        rule = rule_class(**params)

        # Verify it's enabled correctly
        expected_enabled = config.get(f"rules.{rule_name}.enabled", True)
        actual_enabled = getattr(rule, "enabled", True)
        assert actual_enabled == expected_enabled, \
            f"Enabled mismatch: expected {expected_enabled}, got {actual_enabled}"

        print(f"✅ {rule_name} ({rule_class.__name__})")
        return True

    except TypeError as e:
        print(f"❌ {rule_name} - Parameter mismatch: {e}")
        return False
    except ValueError as e:
        print(f"❌ {rule_name} - Validation error: {e}")
        return False
    except Exception as e:
        print(f"❌ {rule_name} - Unexpected error: {e}")
        return False
```

---

## Individual Rule Validation Scripts

### RULE-001: MaxContractsRule
```python
def test_rule_001():
    """Validate RULE-001 parameters match __init__."""
    rule = MaxContractsRule(
        limit=5,
        count_type="net"
    )

    assert rule.limit == 5
    assert rule.count_type == "net"
    assert rule.enabled == True

    print("✅ RULE-001 validation passed")
```

### RULE-003: DailyRealizedLossRule
```python
def test_rule_003(pnl_tracker, lockout_manager, config):
    """Validate RULE-003 state managers are injected correctly."""
    rule = DailyRealizedLossRule(
        limit=config["rules"]["daily_realized_loss"]["limit"],
        pnl_tracker=pnl_tracker,
        lockout_manager=lockout_manager,
        reset_time="17:00",
        timezone_name="America/Chicago"
    )

    # Verify state managers are stored
    assert rule.pnl_tracker is pnl_tracker, "pnl_tracker not stored"
    assert rule.lockout_manager is lockout_manager, "lockout_manager not stored"

    # Verify config values
    assert rule.limit == config["rules"]["daily_realized_loss"]["limit"]
    assert rule.reset_time == "17:00"
    assert rule.timezone_name == "America/Chicago"

    print("✅ RULE-003 validation passed")
```

### RULE-004: DailyUnrealizedLossRule
```python
def test_rule_004(market_config):
    """Validate RULE-004 tick data is correct."""
    rule = DailyUnrealizedLossRule(
        loss_limit=-750,
        tick_values=market_config["tick_values"],
        tick_sizes=market_config["tick_sizes"]
    )

    # Verify tick data is stored
    assert "ES" in rule.tick_values, "ES missing from tick_values"
    assert "MNQ" in rule.tick_values, "MNQ missing from tick_values"
    assert rule.tick_values["ES"] > 0, "ES tick_value must be positive"

    assert "ES" in rule.tick_sizes, "ES missing from tick_sizes"
    assert rule.tick_sizes["ES"] > 0, "ES tick_size must be positive"

    # Verify loss limit is negative
    assert rule.loss_limit < 0, "loss_limit must be negative"

    print("✅ RULE-004 validation passed")
```

### RULE-006: TradeFrequencyLimitRule
```python
def test_rule_006(timer_manager, database, config):
    """Validate RULE-006 parameters and handle config issue."""
    limits = {
        "per_minute": config["rules"]["trade_frequency_limit"]["limits"]["per_minute"],
        "per_hour": config["rules"]["trade_frequency_limit"]["limits"]["per_hour"],
        "per_session": config["rules"]["trade_frequency_limit"]["limits"]["per_session"],
    }

    # ⚠️ WORKAROUND: cooldown_on_breach not in config, use defaults
    cooldown_on_breach = {
        "per_minute_breach": 60,
        "per_hour_breach": 1800,
        "per_session_breach": 3600,
    }

    rule = TradeFrequencyLimitRule(
        limits=limits,
        cooldown_on_breach=cooldown_on_breach,
        timer_manager=timer_manager,
        db=database
    )

    # Verify state managers
    assert rule.timer_manager is timer_manager
    assert rule.db is database

    # Verify limits
    assert rule.limits["per_minute"] == 3
    assert rule.limits["per_hour"] == 10
    assert rule.limits["per_session"] == 50

    print("✅ RULE-006 validation passed (with cooldown_on_breach workaround)")
```

### RULE-007: CooldownAfterLossRule
```python
def test_rule_007(timer_manager, pnl_tracker, lockout_manager, config):
    """Validate RULE-007 parameter conversion."""
    # ⚠️ WORKAROUND: Config has single loss_threshold, convert to list
    loss_threshold = config["rules"]["cooldown_after_loss"]["loss_threshold"]
    loss_thresholds = [
        {"loss_amount": loss_threshold, "cooldown_duration": 300}
    ]

    rule = CooldownAfterLossRule(
        loss_thresholds=loss_thresholds,
        timer_manager=timer_manager,
        pnl_tracker=pnl_tracker,
        lockout_manager=lockout_manager
    )

    # Verify state managers
    assert rule.timer_manager is timer_manager
    assert rule.pnl_tracker is pnl_tracker
    assert rule.lockout_manager is lockout_manager

    # Verify thresholds
    assert len(rule.loss_thresholds) >= 1
    assert rule.loss_thresholds[0]["loss_amount"] == loss_threshold

    print("✅ RULE-007 validation passed (with loss_thresholds conversion)")
```

### RULE-008: NoStopLossGraceRule
```python
def test_rule_008(timer_manager, config):
    """Validate RULE-008 field name mapping."""
    # ⚠️ WORKAROUND: Config uses require_within_seconds, code expects grace_period_seconds
    grace_period = config["rules"]["no_stop_loss_grace"]["require_within_seconds"]

    rule = NoStopLossGraceRule(
        grace_period_seconds=grace_period,
        timer_manager=timer_manager,
        enabled=config["rules"]["no_stop_loss_grace"]["enabled"]
    )

    # Verify parameter mapping
    assert rule.grace_period_seconds == grace_period
    assert rule.grace_period_seconds == 60

    # Verify state manager
    assert rule.timer_manager is timer_manager

    # Verify enabled state
    assert rule.enabled == False  # Currently disabled in config

    print("✅ RULE-008 validation passed (with field name mapping)")
```

### RULE-009: SessionBlockOutsideRule
```python
def test_rule_009(lockout_manager, config):
    """Validate RULE-009 config dict passing."""
    rule = SessionBlockOutsideRule(
        config=config["rules"]["session_block_outside"],
        lockout_manager=lockout_manager
    )

    # Verify state manager
    assert rule.lockout_manager is lockout_manager

    # Verify parsed config
    assert rule.session_start.hour == 8
    assert rule.session_start.minute == 30
    assert rule.session_end.hour == 15
    assert rule.session_end.minute == 0
    assert rule.timezone_name == "America/Chicago"
    assert rule.block_weekends == True

    print("✅ RULE-009 validation passed")
```

---

## Batch Validation Script

Use this to test all 13 rules at once:

```python
async def validate_all_rules(engine, config, market_config):
    """Validate all 13 rules can be loaded correctly."""

    print("=" * 60)
    print("RULE LOADING VALIDATION")
    print("=" * 60)

    # Pre-checks
    print("\n1. PRE-LOADING CHECKS:")
    validate_state_managers(engine)
    validate_market_config(market_config)

    # Individual tests
    print("\n2. RULE LOADING TESTS:")

    results = {
        "RULE-001": test_rule_001(),
        "RULE-003": test_rule_003(engine.pnl_tracker, engine.lockout_manager, config),
        "RULE-004": test_rule_004(market_config),
        "RULE-006": test_rule_006(engine.timer_manager, engine.database, config),
        "RULE-007": test_rule_007(engine.timer_manager, engine.pnl_tracker, engine.lockout_manager, config),
        "RULE-008": test_rule_008(engine.timer_manager, config),
        "RULE-009": test_rule_009(engine.lockout_manager, config),
        # ... continue for all 13
    }

    # Summary
    print("\n3. VALIDATION SUMMARY:")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL RULES VALIDATED SUCCESSFULLY")
        return True
    else:
        print("\n❌ SOME RULES FAILED VALIDATION")
        failed = [k for k, v in results.items() if not v]
        print(f"Failed rules: {', '.join(failed)}")
        return False
```

---

## API Contract Verification

### Verify __init__() Signatures

Before loading, verify actual method signatures match documentation:

```python
import inspect

def verify_rule_signature(rule_class, expected_params):
    """Verify rule __init__ has expected parameters."""
    sig = inspect.signature(rule_class.__init__)
    actual_params = set(sig.parameters.keys()) - {"self"}
    expected_params = set(expected_params)

    if actual_params == expected_params:
        print(f"✅ {rule_class.__name__} signature matches")
        return True
    else:
        print(f"❌ {rule_class.__name__} signature mismatch")
        print(f"   Expected: {expected_params}")
        print(f"   Actual: {actual_params}")
        return False

# Example:
verify_rule_signature(DailyRealizedLossRule, {
    "limit",
    "pnl_tracker",
    "lockout_manager",
    "action",
    "reset_time",
    "timezone_name"
})
```

---

## Config Issues Workarounds

Document workarounds needed in rule loader:

```python
def apply_config_workarounds(config):
    """Apply known workarounds for config issues."""

    # ISSUE-006: Missing cooldown_on_breach
    if "cooldown_on_breach" not in config["rules"]["trade_frequency_limit"]:
        logger.warning("WORKAROUND: Adding default cooldown_on_breach for RULE-006")
        config["rules"]["trade_frequency_limit"]["cooldown_on_breach"] = {
            "per_minute_breach": 60,
            "per_hour_breach": 1800,
            "per_session_breach": 3600,
        }

    # ISSUE-007: loss_threshold vs loss_thresholds
    if "loss_threshold" in config["rules"]["cooldown_after_loss"]:
        single_value = config["rules"]["cooldown_after_loss"]["loss_threshold"]
        logger.warning("WORKAROUND: Converting loss_threshold to loss_thresholds list for RULE-007")
        config["rules"]["cooldown_after_loss"]["loss_thresholds"] = [
            {"loss_amount": single_value, "cooldown_duration": 300}
        ]

    # ISSUE-008: Field naming (require_within_seconds -> grace_period_seconds)
    # Handled at loading time - just use require_within_seconds and pass as grace_period_seconds

    return config
```

---

## Test Checklist

Before committing rule loading implementation:

- [ ] All 13 rules instantiate without TypeError
- [ ] All rules have correct `enabled` status from config
- [ ] State managers are correctly injected (RULE-003, RULE-006, RULE-007, RULE-009, RULE-013)
- [ ] Tick data is correctly passed (RULE-004, RULE-005, RULE-012)
- [ ] Config workarounds applied for RULE-006, RULE-007, RULE-008
- [ ] Field name mapping applied for RULE-008
- [ ] Rules are added to engine in correct order
- [ ] Engine.rules list contains exactly 13 rules (if all enabled)
- [ ] Each rule's evaluate() method is callable
- [ ] Rules with state managers reference them correctly

---

## Runtime Smoke Test

After loading, verify rules work at runtime:

```python
async def smoke_test_rules(engine, event):
    """Quick smoke test: each rule evaluates without error."""

    print("Running smoke test on all rules...")

    for rule in engine.rules:
        try:
            # Create a mock event and evaluate
            result = await rule.evaluate(event, engine)
            print(f"✅ {rule.name} evaluated successfully")
        except Exception as e:
            print(f"❌ {rule.name} failed: {e}")
            return False

    print("✅ All rules smoke tested")
    return True
```

---

## Before/After Checklist

### Before Merging Rule Loading Implementation

- [ ] Read RULE_LOADING_PARAMS.md in full
- [ ] Read RULE_LOADING_QUICK_REFERENCE.md
- [ ] Run all validation tests above
- [ ] Verify config workarounds are applied
- [ ] Test with actual config/risk_config.yaml
- [ ] Test with mock market_config
- [ ] Test with mock state managers
- [ ] Run pytest on rule loading tests
- [ ] Run smoke test via `python run_tests.py [s]`

### After Merging

- [ ] Document any additional issues found
- [ ] Update config.yaml if issues discovered
- [ ] Add any new validation tests to test suite
- [ ] Update PROJECT_STATUS.md with rule loading completion status

---

**Document Created**: 2025-10-29
**Purpose**: Agent 1 validation checklist for rule loading implementation
**Status**: Ready to use
