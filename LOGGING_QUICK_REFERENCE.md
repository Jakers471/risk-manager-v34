# Logging System Quick Reference Card

## Quick Import

```python
from risk_manager.cli import (
    setup_logging,
    EventDisplay,
    checkpoint_rule_evaluated,
    checkpoint_enforcement_triggered,
    cp7, cp8,  # Shorthand
)
```

## Setup Logging (One Time)

```python
# In your main entry point or __init__
setup_logging(
    console_level="INFO",  # INFO, DEBUG, WARNING, ERROR
    file_level="DEBUG",    # Usually DEBUG for detailed logs
    log_file="data/logs/risk_manager.log",  # Optional, defaults to this
    colorize=True,         # Enable colors (default True)
)
```

## Initialize Display

```python
display = EventDisplay(mode="log")  # or "dashboard" (future)
display.show_startup_banner()
```

## The 8 Checkpoints (At a Glance)

| # | Emoji | Where to Add | Function Call |
|---|-------|--------------|---------------|
| 1 | 🚀 | RiskManager.__init__ | `cp1()` |
| 2 | ✅ | Config loaded | `cp2(rules_count=13, instruments=["MNQ"])` |
| 3 | ✅ | SDK connected | `cp3(instruments=["MNQ"], account_id="ACC123")` |
| 4 | ✅ | Rules initialized | `cp4(rules=["DailyLossRule"], rules_count=1)` |
| 5 | ✅ | Event loop started | `cp5(rules_count=13)` |
| 6 | 📨 | Event received | `cp6(event_type="position_opened", symbol="MNQ")` |
| 7 | 🔍 | Rule evaluated | `cp7(rule_name="MyRule", passed=True, current_value=100, limit=200)` |
| 8 | ⚠️ | Enforcement triggered | `cp8(action="flatten", rule_name="MyRule")` |

## Rule Integration (Copy-Paste This)

```python
async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict | None:
    # Your rule logic here
    current_value = self._calculate_value(engine)
    violated = self._check_violation(current_value)

    # ADD THIS: Log checkpoint 7
    cp7(
        rule_name=self.name,
        passed=not violated,
        current_value=current_value,
        limit=self.limit,
    )

    if violated:
        violation = {
            "rule": self.name,
            "current_value": current_value,
            "limit": self.limit,
            "action": self.action,
        }

        # ADD THIS: Log checkpoint 8
        cp8(
            action=self.action,
            rule_name=self.name,
            details={"current": current_value, "limit": self.limit},
        )

        return violation

    return None
```

## Display Events

```python
# Show any event
display.show_event(event)

# Show P&L update
display.show_pnl_update(
    realized=-250.00,
    unrealized=-100.00,
    total=-350.00,
    symbol="MNQ",
)

# Show rule check
display.show_rule_check(
    rule_name="DailyLossRule",
    passed=False,
    current_value=-550,
    limit=-500,
)

# Show enforcement
display.show_enforcement(
    action="flatten",
    rule_name="DailyLossRule",
    symbol="MNQ",
)

# Show position summary
positions = {
    "MNQ": {"quantity": 2, "avg_price": 17500.50, "unrealized_pnl": -100},
}
display.show_position_summary(positions)

# Show rules status
rules = [
    {"name": "DailyLossRule", "enabled": True, "action": "flatten"},
]
display.show_rules_status(rules)
```

## Log Output Examples

### Checkpoint 1 (Service Start)
```
🚀 [CHECKPOINT 1] Service Start | version=1.0.0
```

### Checkpoint 7 (Rule Pass)
```
🔍 [CHECKPOINT 7] Rule Evaluated | rule=MaxPositionRule | status=PASSED | current=2 | limit=5
```

### Checkpoint 7 (Rule Fail)
```
🔍 [CHECKPOINT 7] Rule Evaluated | rule=DailyLossRule | status=VIOLATED | current=-550.0 | limit=-500.0
```

### Checkpoint 8 (Enforcement)
```
⚠️ [CHECKPOINT 8] Enforcement Triggered | action=FLATTEN | rule=DailyLossRule | loss=-550.0
```

## Utility Functions

```python
from risk_manager.cli import log_success, log_error, log_warning, log_system_status

log_success("All positions closed successfully")
log_error("Failed to connect to SDK", exc_info=True)
log_warning("Approaching daily loss limit")
log_system_status("Daily reset completed", details={"previous_pnl": -250})
```

## Log File Location

- **Console**: Real-time output with colors (INFO level)
- **File**: `data/logs/risk_manager.log` (DEBUG level)
  - Daily rotation
  - 30-day retention
  - ZIP compression

## Testing Your Logging

```python
def test_my_rule_logging():
    """Test rule with logging enabled."""
    from risk_manager.cli import setup_logging

    setup_logging(console_level="DEBUG")  # See everything

    # Your test code here
    # Check console for checkpoint logs
```

## Troubleshooting

### Logs not showing up?
```python
# Make sure you called setup_logging()
setup_logging()
```

### Want more detail?
```python
# Lower the log level
setup_logging(console_level="DEBUG", file_level="DEBUG")
```

### Need to disable colors?
```python
# Turn off colorization
setup_logging(colorize=False)
```

### Want different log file?
```python
# Specify custom path
setup_logging(log_file="my_custom.log")
```

## Example Script

See `examples/logging_display_example.py` for a complete working example.

```bash
python examples/logging_display_example.py
```

## Full Documentation

- **Integration Guide**: `AGENT2_INTEGRATION_GUIDE.md`
- **Delivery Summary**: `AGENT3_LOGGING_SYSTEM_DELIVERY.md`
- **Code**: `src/risk_manager/cli/logger.py`, `display.py`, `checkpoints.py`

---

**That's it! You're ready to add checkpoint logging to your rules.** 🚀
