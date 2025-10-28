"""
Example: Using the logging and display system with 8-checkpoint visibility.

This example demonstrates how to use the new logging and display modules
to track the Risk Manager's lifecycle through all 8 checkpoints.
"""

import asyncio
from datetime import datetime

from risk_manager.cli import (
    EventDisplay,
    checkpoint_config_loaded,
    checkpoint_enforcement_triggered,
    checkpoint_event_loop_running,
    checkpoint_event_received,
    checkpoint_rule_evaluated,
    checkpoint_rules_initialized,
    checkpoint_sdk_connected,
    checkpoint_service_start,
    setup_logging,
)
from risk_manager.core.events import EventType, RiskEvent


async def main():
    """Demonstrate logging and display system."""

    # Setup logging system
    print("=" * 60)
    print("Risk Manager V34 - Logging & Display Example")
    print("=" * 60)

    setup_logging(
        console_level="INFO",
        file_level="DEBUG",
        log_file="data/logs/example.log",
    )

    # Initialize display system
    display = EventDisplay(mode="log")
    display.show_startup_banner()

    # Simulate Risk Manager startup sequence
    print("\n--- Simulating Risk Manager Startup ---\n")

    # Checkpoint 1: Service Start
    await asyncio.sleep(0.5)
    checkpoint_service_start({"version": "1.0.0", "environment": "development"})

    # Checkpoint 2: Config Loaded
    await asyncio.sleep(0.5)
    checkpoint_config_loaded(
        rules_count=13,
        instruments=["MNQ", "ES", "NQ"],
    )

    # Checkpoint 3: SDK Connected
    await asyncio.sleep(0.5)
    checkpoint_sdk_connected(
        instruments=["MNQ", "ES"],
        account_id="DEMO123456",
    )

    # Checkpoint 4: Rules Initialized
    await asyncio.sleep(0.5)
    checkpoint_rules_initialized(
        rules=["DailyLossRule", "MaxPositionRule", "DailyUnrealizedLossRule"],
        rules_count=3,
    )

    # Checkpoint 5: Event Loop Running
    await asyncio.sleep(0.5)
    checkpoint_event_loop_running(rules_count=3)

    print("\n--- Simulating Event Processing ---\n")
    await asyncio.sleep(1)

    # Simulate position opened event
    event1 = RiskEvent(
        event_type=EventType.POSITION_OPENED,
        timestamp=datetime.now(),
        data={
            "symbol": "MNQ",
            "quantity": 2,
            "price": 17500.50,
            "contractId": "ESM25",
        },
    )

    # Checkpoint 6: Event Received
    checkpoint_event_received(
        event_type="position_opened",
        symbol="MNQ",
        details={"qty": 2, "price": 17500.50},
    )
    display.show_event(event1)

    await asyncio.sleep(0.5)

    # Checkpoint 7: Rule Evaluated (Pass)
    checkpoint_rule_evaluated(
        rule_name="MaxPositionRule",
        passed=True,
        current_value=2,
        limit=5,
    )
    display.show_rule_check(
        rule_name="MaxPositionRule",
        passed=True,
        current_value=2,
        limit=5,
    )

    await asyncio.sleep(0.5)

    # Simulate P&L update
    event2 = RiskEvent(
        event_type=EventType.PNL_UPDATED,
        timestamp=datetime.now(),
        data={
            "symbol": "MNQ",
            "realized_pnl": -250.00,
            "unrealized_pnl": -100.00,
        },
    )

    checkpoint_event_received(
        event_type="pnl_updated",
        symbol="MNQ",
        details={"realized": -250.00, "unrealized": -100.00},
    )
    display.show_event(event2)
    display.show_pnl_update(
        realized=-250.00,
        unrealized=-100.00,
        total=-350.00,
        symbol="MNQ",
    )

    await asyncio.sleep(0.5)

    print("\n--- Simulating Rule Violation ---\n")
    await asyncio.sleep(1)

    # Checkpoint 7: Rule Evaluated (Fail)
    checkpoint_rule_evaluated(
        rule_name="DailyLossRule",
        passed=False,
        current_value=-550.00,
        limit=-500.00,
    )
    display.show_rule_check(
        rule_name="DailyLossRule",
        passed=False,
        current_value=-550.00,
        limit=-500.00,
    )

    await asyncio.sleep(0.5)

    # Checkpoint 8: Enforcement Triggered
    checkpoint_enforcement_triggered(
        action="flatten",
        rule_name="DailyLossRule",
        details={"loss": -550.00, "limit": -500.00},
    )
    display.show_enforcement(
        action="flatten",
        rule_name="DailyLossRule",
        details={"loss": -550.00},
    )

    await asyncio.sleep(0.5)

    # Show enforcement event
    event3 = RiskEvent(
        event_type=EventType.ENFORCEMENT_ACTION,
        timestamp=datetime.now(),
        data={
            "action": "flatten_all",
            "rule": "DailyLossRule",
            "reason": "daily_loss_limit_exceeded",
        },
        severity="critical",
    )
    display.show_event(event3)

    print("\n--- Status Summary ---\n")
    await asyncio.sleep(1)

    # Show position summary
    positions = {
        "MNQ": {
            "quantity": 2,
            "avg_price": 17500.50,
            "unrealized_pnl": -100.00,
        },
        "ES": {
            "quantity": -1,
            "avg_price": 5025.25,
            "unrealized_pnl": 50.00,
        },
    }
    display.show_position_summary(positions)

    await asyncio.sleep(0.5)

    # Show rules status
    rules = [
        {"name": "DailyLossRule", "enabled": True, "action": "flatten"},
        {"name": "MaxPositionRule", "enabled": True, "action": "reject"},
        {"name": "DailyUnrealizedLossRule", "enabled": True, "action": "alert"},
    ]
    display.show_rules_status(rules)

    await asyncio.sleep(1)

    display.show_shutdown_banner()

    print("\n" + "=" * 60)
    print("Example completed! Check data/logs/example.log for full logs.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
