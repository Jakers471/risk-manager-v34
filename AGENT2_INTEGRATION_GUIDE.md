# Agent 2 Integration Guide: Using the Logging & Display System

## Overview

Agent 3 has built a complete logging and display system with 8-checkpoint visibility. This guide shows Agent 2 (Daily Realized Loss implementation) how to integrate these logging functions into your code.

## Quick Start

### 1. Import the Functions

```python
from risk_manager.cli import (
    checkpoint_event_received,
    checkpoint_rule_evaluated,
    checkpoint_enforcement_triggered,
    EventDisplay,
)
```

### 2. Basic Usage in Rule Evaluation

```python
from risk_manager.rules.base import RiskRule
from risk_manager.core.events import RiskEvent
from risk_manager.cli import (
    checkpoint_event_received,
    checkpoint_rule_evaluated,
    checkpoint_enforcement_triggered,
)


class DailyRealizedLossRule(RiskRule):
    """Rule to enforce daily realized loss limit."""

    def __init__(self, limit: float = -500.0, action: str = "flatten"):
        super().__init__(action=action)
        self.limit = limit

    async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict | None:
        """Evaluate the rule against an event."""

        # Get current realized loss from state
        current_loss = engine.get_daily_realized_loss()

        # Check if violated
        violated = current_loss < self.limit

        # Log checkpoint 7: Rule evaluated
        checkpoint_rule_evaluated(
            rule_name=self.name,
            passed=not violated,
            current_value=current_loss,
            limit=self.limit,
        )

        if violated:
            # Build violation dict
            violation = {
                "rule": self.name,
                "current_value": current_loss,
                "limit": self.limit,
                "action": self.action,
                "message": f"Daily realized loss {current_loss:.2f} exceeds limit {self.limit:.2f}",
            }

            # Log checkpoint 8: Enforcement triggered
            checkpoint_enforcement_triggered(
                action=self.action,
                rule_name=self.name,
                details={"loss": current_loss, "limit": self.limit},
            )

            return violation

        return None
```

## The 8 Checkpoints

### Checkpoint 1: Service Start
**Where**: `RiskManager.__init__()` (already implemented)
```python
from risk_manager.cli import checkpoint_service_start

checkpoint_service_start({"version": "1.0.0"})
```

### Checkpoint 2: Config Loaded
**Where**: `RiskManager.create()` after loading config (already implemented)
```python
from risk_manager.cli import checkpoint_config_loaded

checkpoint_config_loaded(rules_count=13, instruments=["MNQ", "ES"])
```

### Checkpoint 3: SDK Connected
**Where**: `RiskManager._init_trading_integration()` (already implemented)
```python
from risk_manager.cli import checkpoint_sdk_connected

checkpoint_sdk_connected(instruments=["MNQ"], account_id="ACC123")
```

### Checkpoint 4: Rules Initialized
**Where**: `RiskManager._add_default_rules()` (already implemented)
```python
from risk_manager.cli import checkpoint_rules_initialized

checkpoint_rules_initialized(
    rules=["DailyLossRule", "MaxPositionRule"],
    rules_count=2,
)
```

### Checkpoint 5: Event Loop Running
**Where**: `RiskEngine.start()` (already implemented)
```python
from risk_manager.cli import checkpoint_event_loop_running

checkpoint_event_loop_running(rules_count=13)
```

### Checkpoint 6: Event Received
**Where**: `RiskEngine.evaluate_rules()` (already implemented)
```python
from risk_manager.cli import checkpoint_event_received

checkpoint_event_received(
    event_type=event.event_type.value,
    symbol=event.data.get("symbol"),
    details={"qty": event.data.get("quantity")},
)
```

### Checkpoint 7: Rule Evaluated
**Where**: YOUR RULE'S `evaluate()` METHOD ← **YOU ADD THIS**
```python
from risk_manager.cli import checkpoint_rule_evaluated

# After evaluating your rule logic
checkpoint_rule_evaluated(
    rule_name=self.name,
    passed=not violated,
    current_value=current_loss,
    limit=self.limit,
)
```

### Checkpoint 8: Enforcement Triggered
**Where**: YOUR RULE'S `evaluate()` METHOD ← **YOU ADD THIS**
```python
from risk_manager.cli import checkpoint_enforcement_triggered

# When building violation dict
checkpoint_enforcement_triggered(
    action=self.action,
    rule_name=self.name,
    details={"loss": current_loss, "limit": self.limit},
)
```

## Integration Points for Agent 2

### 1. In Daily Realized Loss Rule

Add logging to your `DailyRealizedLossRule.evaluate()` method:

```python
async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict | None:
    """Evaluate daily realized loss."""

    # Your existing logic to calculate loss
    current_loss = self._calculate_daily_realized_loss(engine)

    # ADD: Log rule evaluation
    violated = current_loss < self.limit
    checkpoint_rule_evaluated(
        rule_name="DailyRealizedLossRule",
        passed=not violated,
        current_value=current_loss,
        limit=self.limit,
    )

    if violated:
        # Your existing violation logic
        violation = {
            "rule": self.name,
            "current_value": current_loss,
            "limit": self.limit,
            "action": self.action,
        }

        # ADD: Log enforcement trigger
        checkpoint_enforcement_triggered(
            action=self.action,
            rule_name="DailyRealizedLossRule",
            details={"loss": current_loss, "limit": self.limit},
        )

        return violation

    return None
```

### 2. In State Tracking (if you add it)

If you implement state tracking for P&L:

```python
from risk_manager.cli import log_system_status

def update_realized_pnl(self, amount: float) -> None:
    """Update realized P&L."""
    self.daily_realized_pnl += amount

    # Log status update
    log_system_status(
        "P&L Updated",
        details={"realized": self.daily_realized_pnl},
    )
```

### 3. In Reset Logic (if applicable)

If you implement daily reset:

```python
from risk_manager.cli import log_system_status

async def reset_daily_state(self) -> None:
    """Reset daily state at configured time."""
    old_pnl = self.daily_realized_pnl
    self.daily_realized_pnl = 0.0

    log_system_status(
        "Daily State Reset",
        details={"previous_pnl": old_pnl},
    )
```

## Using EventDisplay

The `EventDisplay` class provides rich formatting for events:

```python
from risk_manager.cli import EventDisplay
from risk_manager.core.events import RiskEvent, EventType

# Create display instance
display = EventDisplay(mode="log")

# Show startup banner
display.show_startup_banner()

# Show events
event = RiskEvent(
    event_type=EventType.PNL_UPDATED,
    data={"symbol": "MNQ", "realized_pnl": -250.00},
)
display.show_event(event)

# Show P&L updates
display.show_pnl_update(
    realized=-250.00,
    unrealized=-100.00,
    total=-350.00,
    symbol="MNQ",
)

# Show position summary
positions = {
    "MNQ": {"quantity": 2, "avg_price": 17500.50, "unrealized_pnl": -100.00},
}
display.show_position_summary(positions)
```

## Example: Complete Integration

Here's a complete example showing all integration points:

```python
from risk_manager.rules.base import RiskRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.cli import (
    checkpoint_rule_evaluated,
    checkpoint_enforcement_triggered,
    EventDisplay,
)


class DailyRealizedLossRule(RiskRule):
    """Enforces daily realized loss limit."""

    def __init__(
        self,
        limit: float = -500.0,
        action: str = "flatten",
        reset_time: str = "17:00",
    ):
        super().__init__(action=action)
        self.limit = limit
        self.reset_time = reset_time

    async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict | None:
        """Evaluate the rule against an event."""

        # Only process relevant events
        if event.event_type not in [
            EventType.ORDER_FILLED,
            EventType.POSITION_CLOSED,
            EventType.PNL_UPDATED,
        ]:
            return None

        # Get daily realized loss from state
        current_loss = self._get_daily_realized_loss(engine)

        # Check violation
        violated = current_loss < self.limit

        # LOG CHECKPOINT 7: Rule evaluated
        checkpoint_rule_evaluated(
            rule_name=self.name,
            passed=not violated,
            current_value=current_loss,
            limit=self.limit,
            details={"event": event.event_type.value},
        )

        if violated:
            violation = {
                "rule": self.name,
                "current_value": current_loss,
                "limit": self.limit,
                "action": self.action,
                "message": f"Daily realized loss ${current_loss:.2f} exceeds limit ${self.limit:.2f}",
                "severity": "critical",
            }

            # LOG CHECKPOINT 8: Enforcement triggered
            checkpoint_enforcement_triggered(
                action=self.action,
                rule_name=self.name,
                details={
                    "loss": current_loss,
                    "limit": self.limit,
                    "exceeded_by": current_loss - self.limit,
                },
            )

            return violation

        return None

    def _get_daily_realized_loss(self, engine: "RiskEngine") -> float:
        """Get current daily realized loss from engine state."""
        # Your implementation here
        return engine.daily_pnl  # Or however you track it
```

## Shorthand Functions

For quick logging, use the shorthand functions:

```python
from risk_manager.cli import cp7, cp8

# Instead of checkpoint_rule_evaluated
cp7(rule_name="MyRule", passed=True, current_value=100, limit=200)

# Instead of checkpoint_enforcement_triggered
cp8(action="flatten", rule_name="MyRule", details={"loss": -550})
```

## Testing Your Integration

After adding logging to your rule:

```python
# In your test file
import pytest
from risk_manager.cli import setup_logging, EventDisplay

@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup logging for tests."""
    setup_logging(console_level="DEBUG", file_level="DEBUG")

def test_daily_realized_loss_with_logging(risk_manager):
    """Test rule with logging enabled."""
    display = EventDisplay(mode="log")

    # Your test code here
    # Logging will appear in console and log file
```

## Log Output Examples

### Checkpoint 7 (Pass):
```
2025-10-28 13:45:23.456 | INFO     | risk_manager.cli.logger:log_checkpoint:123 - ✅ [CHECKPOINT 7] Rule Evaluated | rule=DailyRealizedLossRule | status=PASSED | current=-250.00 | limit=-500.00
```

### Checkpoint 7 (Fail):
```
2025-10-28 13:45:25.789 | WARNING  | risk_manager.cli.logger:log_checkpoint:123 - 🔍 [CHECKPOINT 7] Rule Evaluated | rule=DailyRealizedLossRule | status=VIOLATED | current=-550.00 | limit=-500.00
```

### Checkpoint 8:
```
2025-10-28 13:45:25.790 | ERROR    | risk_manager.cli.logger:log_checkpoint:123 - ⚠️ [CHECKPOINT 8] Enforcement Triggered | action=FLATTEN | rule=DailyRealizedLossRule | loss=-550.00 | limit=-500.00
```

## Where Logs Are Stored

- **Console**: Formatted output with colors (INFO level by default)
- **File**: `data/logs/risk_manager.log` (DEBUG level, rotates daily)

## Summary

**Two main integration points for Agent 2:**

1. **In your rule's `evaluate()` method**: Add `checkpoint_rule_evaluated()` after checking the rule
2. **When returning a violation**: Add `checkpoint_enforcement_triggered()` before returning the violation dict

That's it! The rest of the checkpoints (1-6) are already implemented in the core system.

## Questions?

If you need clarification:
- Check `examples/logging_display_example.py` for working code
- Check `src/risk_manager/cli/logger.py` for all available functions
- Check `src/risk_manager/core/engine.py` to see how checkpoints 6-8 are already used

Good luck with the Daily Realized Loss implementation! 🚀
