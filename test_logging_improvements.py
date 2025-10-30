"""
Test script to verify improved rule evaluation logging.

Run this to see the new logging format in action.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from risk_manager.config.loader import ConfigLoader
from risk_manager.core.engine import RiskEngine
from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.rules.daily_realized_loss import DailyRealizedLossRule
from risk_manager.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
from risk_manager.rules.auth_loss_guard import AuthLossGuardRule
from risk_manager.state.database import Database
from risk_manager.state.pnl_tracker import PnLTracker
from risk_manager.state.lockout_manager import LockoutManager
from risk_manager.state.timer_manager import TimerManager


async def test_logging():
    """Test the improved logging format."""
    print("\n" + "=" * 80)
    print("Testing Improved Rule Evaluation Logging")
    print("=" * 80 + "\n")

    # Load config
    config_loader = ConfigLoader(config_dir=Path("config"))
    config = config_loader.load_risk_config()

    # Create event bus and engine
    event_bus = EventBus()
    engine = RiskEngine(config=config, event_bus=event_bus)

    # Initialize state managers
    db_path = Path("data/test_logging.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    db = Database(db_path=str(db_path))
    timer_manager = TimerManager()
    pnl_tracker = PnLTracker(db=db)
    lockout_manager = LockoutManager(database=db, timer_manager=timer_manager)

    # Add some rules
    print("Adding test rules...\n")

    # Rule 1: Daily Realized Loss (will PASS)
    daily_loss_rule = DailyRealizedLossRule(
        limit=-500.0,
        pnl_tracker=pnl_tracker,
        lockout_manager=lockout_manager,
        action="flatten",
    )
    engine.add_rule(daily_loss_rule)

    # Rule 2: Max Contracts Per Instrument (will PASS)
    max_contracts_rule = MaxContractsPerInstrumentRule(
        limits={"MNQ": 2, "ES": 3},
        enforcement="reduce_to_limit",
        unknown_symbol_action="allow_with_limit:1",
    )
    engine.add_rule(max_contracts_rule)

    # Rule 3: Auth Loss Guard (will PASS)
    auth_guard_rule = AuthLossGuardRule(
        alert_on_disconnect=True,
        alert_on_auth_failure=True,
        log_level="WARNING",
    )
    engine.add_rule(auth_guard_rule)

    await engine.start()

    print("\n" + "=" * 80)
    print("TEST 1: Trade event with small profit (all rules should PASS)")
    print("=" * 80 + "\n")

    # Simulate a trade event with small profit
    trade_event = RiskEvent(
        event_type=EventType.TRADE_EXECUTED,
        data={
            "account_id": "TEST-001",
            "symbol": "MNQ",
            "side": 0,  # Buy
            "size": 1,
            "price": 18500.0,
            "profitAndLoss": 125.0,  # $125 profit
            "netPosition": 1,
            "realized_pnl": 125.0,
            "unrealized_pnl": 0.0,
        },
    )

    violations = await engine.evaluate_rules(trade_event)
    print(f"\nViolations detected: {len(violations)}\n")

    print("\n" + "=" * 80)
    print("TEST 2: Trade event with large loss (Daily Loss should FAIL)")
    print("=" * 80 + "\n")

    # Simulate a trade event with large loss (exceeds -$500 limit)
    trade_event_loss = RiskEvent(
        event_type=EventType.TRADE_EXECUTED,
        data={
            "account_id": "TEST-001",
            "symbol": "MNQ",
            "side": 1,  # Sell
            "size": 1,
            "price": 18400.0,
            "profitAndLoss": -650.0,  # $650 loss (total P&L = -525)
            "netPosition": 0,
            "realized_pnl": -525.0,
            "unrealized_pnl": 0.0,
        },
    )

    violations = await engine.evaluate_rules(trade_event_loss)
    print(f"\nViolations detected: {len(violations)}")
    for v in violations:
        print(f"  - {v.get('rule')}: {v.get('message')}\n")

    print("\n" + "=" * 80)
    print("TEST 3: Position update with large position")
    print("=" * 80 + "\n")

    position_event = RiskEvent(
        event_type=EventType.POSITION_UPDATED,
        data={
            "account_id": "TEST-002",
            "symbol": "ES",
            "netPosition": 2,
            "averagePrice": 5200.0,
            "unrealized_pnl": 250.0,
            "realized_pnl": 0.0,
        },
    )

    violations = await engine.evaluate_rules(position_event)
    print(f"\nViolations detected: {len(violations)}\n")

    await engine.stop()

    # Clean up
    if db_path.exists():
        db_path.unlink()

    print("\n" + "=" * 80)
    print("Logging Test Complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_logging())
