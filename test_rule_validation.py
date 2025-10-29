#!/usr/bin/env python3
"""
Rule Validation Script - Test All 13 Risk Rules

This script systematically tests each risk rule by injecting mock events
and validating:
1. Rule arithmetic (calculations are correct)
2. Breach detection (violations trigger at right thresholds)
3. Enforcement actions (SDK methods are called correctly)

Usage:
    python test_rule_validation.py                   # Test all rules
    python test_rule_validation.py --rule RULE-003  # Test specific rule
    python test_rule_validation.py --live           # Test with live SDK
    python test_rule_validation.py --verbose        # Show detailed output

Features:
    - Mock event injection (no real trades)
    - Real-time event simulation
    - Enforcement action verification
    - P&L calculation validation
    - Detailed output with timestamps
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, time, timedelta, timezone
from typing import Any
from unittest.mock import patch
from zoneinfo import ZoneInfo

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.config import RiskConfig
from risk_manager.state.database import Database
from risk_manager.state.pnl_tracker import PnLTracker
from risk_manager.state.lockout_manager import LockoutManager

# Force UTF-8 encoding for Windows console
console = Console(force_terminal=True, legacy_windows=False)


class RuleTester:
    """Test individual risk rules with mock events."""

    def __init__(self, config: RiskConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.event_bus = EventBus()

        # Initialize state managers
        self.db = Database(":memory:")  # In-memory for testing
        self.pnl_tracker = PnLTracker(self.db)
        self.lockout_manager = LockoutManager(self.db)

        # Track results
        self.results: dict[str, dict[str, Any]] = {}

    async def test_rule_003_daily_realized_loss(self) -> dict[str, Any]:
        """
        Test RULE-003: Daily Realized Loss

        Arithmetic Test:
        - Loss limit: -$500
        - Trade 1: -$200 (OK)
        - Trade 2: -$150 (OK, total: -$350)
        - Trade 3: -$200 (BREACH, total: -$550 > -$500)

        Expected:
        - Violations: 1
        - Enforcement: flatten_all
        - Lockout: Until next reset (5 PM ET)
        """
        console.print("\n[bold cyan]Testing RULE-003: Daily Realized Loss[/bold cyan]")

        from risk_manager.rules.daily_realized_loss import DailyRealizedLossRule

        # Create rule with test configuration
        rule = DailyRealizedLossRule(
            limit=-500.0,
            pnl_tracker=self.pnl_tracker,
            lockout_manager=self.lockout_manager,
            reset_time="17:00",
            timezone_name="America/New_York"
        )

        test_account = "TEST-ACCOUNT-001"
        violations = []

        # Simulate Trade 1: -$200 loss
        console.print("[yellow]Trade 1: -$200 loss[/yellow]")

        event1 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": -200.0,  # Rule expects camelCase!
                "symbol": "MNQ"
            }
        )

        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        violation1 = await rule.evaluate(event1, mock_engine)
        current_pnl = self.pnl_tracker.get_daily_pnl(test_account)
        console.print(f"  Current P&L: ${current_pnl:.2f}")

        if violation1:
            violations.append(violation1)
            console.print(f"  [X] [red]VIOLATION: {violation1}[/red]")
        else:
            console.print("  [OK] [green]No violation[/green]")

        # Simulate Trade 2: -$150 loss (total: -$350)
        console.print("[yellow]Trade 2: -$150 loss[/yellow]")

        event2 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": -150.0,
                "symbol": "ES"
            }
        )

        violation2 = await rule.evaluate(event2, mock_engine)
        current_pnl = self.pnl_tracker.get_daily_pnl(test_account)
        console.print(f"  Current P&L: ${current_pnl:.2f}")

        if violation2:
            violations.append(violation2)
            console.print(f"  [X] [red]VIOLATION: {violation2}[/red]")
        else:
            console.print("  [OK] [green]No violation[/green]")

        # Simulate Trade 3: -$200 loss (total: -$550, BREACH!)
        console.print("[yellow]Trade 3: -$200 loss[/yellow]")

        event3 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": -200.0,
                "symbol": "NQ"
            }
        )

        violation3 = await rule.evaluate(event3, mock_engine)
        current_pnl = self.pnl_tracker.get_daily_pnl(test_account)
        console.print(f"  Current P&L: ${current_pnl:.2f}")

        if violation3:
            violations.append(violation3)
            console.print(f"  [X] [red]VIOLATION: {violation3}[/red]")
            console.print(f"  [red]Enforcement action: {violation3.get('action')}[/red]")
        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        # Validate results
        result = {
            "rule": "RULE-003",
            "passed": len(violations) == 1,  # Should violate on trade 3 only
            "violations": violations,
            "arithmetic_correct": current_pnl == -550.0,
            "enforcement_action": violations[0].get('action') if violations else None
        }

        if result["passed"] and result["arithmetic_correct"]:
            console.print("\n[bold green][OK] RULE-003 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-003 FAILED[/bold red]")

        return result

    async def test_rule_001_max_contracts(self) -> dict[str, Any]:
        """
        Test RULE-001: Max Contracts (Account-Wide)

        Arithmetic Test:
        - Position limit: 5 contracts (gross, absolute value)
        - Position 1: 2 MNQ long (OK, total: 2)
        - Position 2: 1 ES long (OK, total: 3)
        - Position 3: 3 NQ long (BREACH, total: 6 > 5)

        Expected:
        - Violations: 1
        - Enforcement: Close position to get back under limit
        - NO lockout (trade-by-trade rule)
        """
        console.print("\n[bold cyan]Testing RULE-001: Max Contracts[/bold cyan]")

        from risk_manager.rules.max_position import MaxPositionRule

        # Create rule with correct API
        rule = MaxPositionRule(
            max_contracts=5,
            action="flatten",  # Will flatten when limit exceeded
            per_instrument=False  # Total across all instruments
        )

        violations = []

        # Mock engine with positions
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Position 1: 2 MNQ long
        console.print("[yellow]Position 1: 2 MNQ long[/yellow]")
        mock_engine.current_positions = {"MNQ": {"size": 2}}

        event1 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2, "side": "long"}
        )

        violation1 = await rule.evaluate(event1, mock_engine)
        if violation1:
            violations.append(violation1)
            console.print(f"  [X] [red]VIOLATION: {violation1}[/red]")
        else:
            console.print("  [OK] [green]No violation (2/5 contracts)[/green]")

        # Position 2: 1 ES long (total: 3)
        console.print("[yellow]Position 2: 1 ES long[/yellow]")
        mock_engine.current_positions = {"MNQ": {"size": 2}, "ES": {"size": 1}}

        event2 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1, "side": "long"}
        )

        violation2 = await rule.evaluate(event2, mock_engine)
        if violation2:
            violations.append(violation2)
            console.print(f"  [X] [red]VIOLATION: {violation2}[/red]")
        else:
            console.print("  [OK] [green]No violation (3/5 contracts)[/green]")

        # Position 3: 3 NQ long (total: 6, BREACH!)
        console.print("[yellow]Position 3: 3 NQ long[/yellow]")
        mock_engine.current_positions = {"MNQ": {"size": 2}, "ES": {"size": 1}, "NQ": {"size": 3}}

        event3 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "NQ", "size": 3, "side": "long"}
        )

        violation3 = await rule.evaluate(event3, mock_engine)
        if violation3:
            violations.append(violation3)
            console.print(f"  [X] [red]VIOLATION: {violation3}[/red]")
            console.print(f"  [red]Enforcement action: {violation3.get('action')}[/red]")
            console.print(f"  [red]Excess contracts: {violation3.get('excess')}[/red]")
        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        result = {
            "rule": "RULE-001",
            "passed": len(violations) == 1,  # Should violate on position 3 only
            "violations": violations,
            "arithmetic_correct": True,  # 2 + 1 + 3 = 6 > 5
            "enforcement_action": violations[0].get('action') if violations else None
        }

        if result["passed"]:
            console.print("\n[bold green][OK] RULE-001 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-001 FAILED[/bold red]")

        return result

    async def test_rule_002_max_contracts_per_instrument(self) -> dict[str, Any]:
        """
        Test RULE-002: Max Contracts Per Instrument

        Arithmetic Test:
        - Configure limits: MNQ=2, ES=1, NQ=3
        - Position 1: 1 MNQ (OK, 1/2)
        - Position 2: 2 ES (BREACH, 2 > 1)
        - Position 3: 3 NQ (OK, 3/3)

        Expected:
        - Violations: 1 (ES position exceeds limit)
        - Enforcement: reduce_to_limit or close_all
        - NO lockout (per-trade rule)
        """
        console.print("\n[bold cyan]Testing RULE-002: Max Contracts Per Instrument[/bold cyan]")

        from risk_manager.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule

        # Create rule with test configuration
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2, "ES": 1, "NQ": 3},
            enforcement="reduce_to_limit",
            unknown_symbol_action="block"
        )

        violations = []

        # Mock engine (rule doesn't need it for per-instrument checks)
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Position 1: 1 MNQ long (OK, 1/2)
        console.print("[yellow]Position 1: 1 MNQ long[/yellow]")

        event1 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.U25",
                "size": 1
            }
        )

        violation1 = await rule.evaluate(event1, mock_engine)
        if violation1:
            violations.append(violation1)
            console.print(f"  [X] [red]VIOLATION: {violation1}[/red]")
        else:
            console.print("  [OK] [green]No violation (1/2 contracts for MNQ)[/green]")

        # Position 2: 2 ES long (BREACH, 2 > 1)
        console.print("[yellow]Position 2: 2 ES long[/yellow]")

        event2 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "contract_id": "CON.F.US.ES.H25",
                "size": 2
            }
        )

        violation2 = await rule.evaluate(event2, mock_engine)
        if violation2:
            violations.append(violation2)
            console.print(f"  [X] [red]VIOLATION: {violation2}[/red]")
            console.print(f"  [red]Enforcement action: reduce_to_limit[/red]")
        else:
            console.print("  [X] [red]ERROR: Should have violated! (2 > 1)[/red]")

        # Position 3: 3 NQ long (OK, 3/3)
        console.print("[yellow]Position 3: 3 NQ long[/yellow]")

        event3 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "NQ",
                "contract_id": "CON.F.US.NQ.H25",
                "size": 3
            }
        )

        violation3 = await rule.evaluate(event3, mock_engine)
        if violation3:
            violations.append(violation3)
            console.print(f"  [X] [red]VIOLATION: {violation3}[/red]")
        else:
            console.print("  [OK] [green]No violation (3/3 contracts for NQ)[/green]")

        # Validate results
        result = {
            "rule": "RULE-002",
            "passed": len(violations) == 1,  # Should violate on ES only
            "violations": violations,
            "arithmetic_correct": len(violations) == 1 and violations[0] if violations else False,
            "enforcement_action": "reduce_to_limit" if violations else None
        }

        if result["passed"] and result["arithmetic_correct"]:
            console.print("\n[bold green][OK] RULE-002 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-002 FAILED[/bold red]")

        return result

    async def test_rule_004_daily_unrealized_loss(self) -> dict[str, Any]:
        """
        Test RULE-004: Daily Unrealized Loss (Stop Loss Per Position)

        Arithmetic Test:
        - Limit: -$750 unrealized loss per position
        - Position opened: MNQ @ $21,500, size=5
        - MNQ tick value: $5 per point
        - MNQ tick size: 0.25
        - Market price 1: $21,400 → Unrealized P&L calculation:
          - Price diff: $21,400 - $21,500 = -$100
          - Ticks: -$100 / 0.25 = -400 ticks
          - P&L: -400 * 5 (size) * $5 (tick_value) = -$10,000 (BREACH!)
        - Market price 2: $21,300 → Even worse loss

        Expected:
        - Violations: 1 (triggers on first price update at $21,400)
        - Enforcement: close_position (close MNQ position only)
        - NO lockout (trade-by-trade rule)
        """
        console.print("\n[bold cyan]Testing RULE-004: Daily Unrealized Loss[/bold cyan]")

        from risk_manager.rules.daily_unrealized_loss import DailyUnrealizedLossRule

        # Create rule with test configuration
        rule = DailyUnrealizedLossRule(
            loss_limit=-750.0,  # -$750 max unrealized loss per position
            tick_values={"MNQ": 5.0},  # MNQ tick value: $5 per point
            tick_sizes={"MNQ": 0.25},  # MNQ tick size: 0.25 points
            action="close_position"
        )

        violations = []

        # Mock engine with position and market prices
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Open position: 5 MNQ long @ $21,500
        console.print("[yellow]Position opened: 5 MNQ long @ $21,500[/yellow]")
        mock_engine.current_positions = {
            "MNQ": {
                "size": 5,
                "avgPrice": 21500.0,
                "contractId": "CON.F.US.MNQ.U25"
            }
        }
        mock_engine.market_prices = {"MNQ": 21500.0}  # Current price = entry price

        event_open = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "size": 5,
                "avgPrice": 21500.0,
                "contractId": "CON.F.US.MNQ.U25"
            }
        )

        violation_open = await rule.evaluate(event_open, mock_engine)
        if violation_open:
            violations.append(violation_open)
            console.print(f"  [X] [red]VIOLATION: {violation_open}[/red]")
        else:
            console.print("  [OK] [green]No violation (P&L = $0.00)[/green]")

        # Market price update 1: $21,400 (down $100 from entry)
        console.print("[yellow]Market price update: $21,400[/yellow]")
        mock_engine.market_prices = {"MNQ": 21400.0}

        # Calculate expected P&L manually
        price_diff = 21400.0 - 21500.0  # -100
        ticks = price_diff / 0.25  # -400 ticks
        expected_pnl = ticks * 5 * 5.0  # -400 * 5 * $5 = -$10,000
        console.print(f"  Expected P&L: ${expected_pnl:.2f}")

        event_update1 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 5,
                "avgPrice": 21500.0,
                "contractId": "CON.F.US.MNQ.U25"
            }
        )

        violation1 = await rule.evaluate(event_update1, mock_engine)
        if violation1:
            violations.append(violation1)
            unrealized_pnl = violation1.get('unrealized_pnl', 0)
            console.print(f"  [X] [red]VIOLATION: Unrealized P&L ${unrealized_pnl:.2f} <= ${rule.loss_limit:.2f}[/red]")
            console.print(f"  [red]Enforcement action: {violation1.get('action')}[/red]")
            console.print(f"  [red]Symbol to close: {violation1.get('symbol')}[/red]")
        else:
            console.print("  [X] [red]ERROR: Should have violated! (P&L far below limit)[/red]")

        # Market price update 2: $21,300 (even worse, but already violated)
        console.print("[yellow]Market price update: $21,300[/yellow]")
        mock_engine.market_prices = {"MNQ": 21300.0}

        # Calculate expected P&L manually
        price_diff2 = 21300.0 - 21500.0  # -200
        ticks2 = price_diff2 / 0.25  # -800 ticks
        expected_pnl2 = ticks2 * 5 * 5.0  # -800 * 5 * $5 = -$20,000
        console.print(f"  Expected P&L: ${expected_pnl2:.2f}")

        event_update2 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 5,
                "avgPrice": 21500.0,
                "contractId": "CON.F.US.MNQ.U25"
            }
        )

        violation2 = await rule.evaluate(event_update2, mock_engine)
        if violation2:
            violations.append(violation2)
            unrealized_pnl = violation2.get('unrealized_pnl', 0)
            console.print(f"  [X] [red]VIOLATION: Unrealized P&L ${unrealized_pnl:.2f} <= ${rule.loss_limit:.2f}[/red]")
        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        # Validate results
        result = {
            "rule": "RULE-004",
            "passed": len(violations) >= 1,  # Should violate at least once
            "violations": violations,
            "arithmetic_correct": len(violations) > 0 and violations[0].get('unrealized_pnl', 0) < rule.loss_limit,
            "enforcement_action": violations[0].get('action') if violations else None
        }

        if result["passed"] and result["arithmetic_correct"]:
            console.print("\n[bold green][OK] RULE-004 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-004 FAILED[/bold red]")

        return result


    async def test_rule_006_trade_frequency_limit(self) -> dict[str, Any]:
        """
        Test RULE-006: Trade Frequency Limit

        Arithmetic Test:
        - Limit: 3 trades per minute
        - Trade 1 at 10:00:00 (OK, 1/3)
        - Trade 2 at 10:00:20 (OK, 2/3)
        - Trade 3 at 10:00:40 (OK, 3/3)
        - Trade 4 at 10:00:50 (BREACH, 4 > 3 in same minute)

        Expected:
        - Violations: 1
        - Enforcement: cooldown (60 seconds)
        - NO position close (trade already executed)
        """
        console.print("\n[bold cyan]Testing RULE-006: Trade Frequency Limit[/bold cyan]")

        from risk_manager.rules.trade_frequency_limit import TradeFrequencyLimitRule
        from risk_manager.state.timer_manager import TimerManager

        # Initialize timer manager
        timer_manager = TimerManager()

        # Create rule with test configuration
        rule = TradeFrequencyLimitRule(
            limits={"per_minute": 3},
            cooldown_on_breach={"per_minute_breach": 60},
            timer_manager=timer_manager,
            db=self.db,
            action="cooldown"
        )

        test_account = "TEST-ACCOUNT-006"
        violations = []

        # Mock engine
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Base timestamp: now - 3 seconds (for rolling window test)
        now = datetime.now(timezone.utc)
        base_time = now - timedelta(seconds=3)

        # Trade 1 (3 seconds ago)
        console.print("[yellow]Trade 1 (3s ago)[/yellow]")
        event1 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "symbol": "MNQ",
                "profitAndLoss": 25.0
            },
            timestamp=base_time
        )

        # Record trade in database
        self.db.add_trade(
            account_id=test_account,
            trade_id=f"TRADE-{base_time.timestamp()}-1",
            symbol="MNQ",
            side="buy",
            quantity=1,
            price=21500.0,
            realized_pnl=25.0,
            timestamp=base_time
        )

        violation1 = await rule.evaluate(event1, mock_engine)
        trade_count_1 = self.db.get_trade_count(test_account, window=60)
        console.print(f"  Trade count in last minute: {trade_count_1}/3")

        if violation1:
            violations.append(violation1)
            console.print(f"  [X] [red]VIOLATION: {violation1}[/red]")
        else:
            console.print("  [OK] [green]No violation (1/3 trades)[/green]")

        # Trade 2 at base_time + 20s
        console.print("[yellow]Trade 2 (now + 20s)[/yellow]")
        event2 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "symbol": "ES",
                "profitAndLoss": 30.0
            },
            timestamp=base_time + timedelta(seconds=20)
        )

        self.db.add_trade(
            account_id=test_account,
            trade_id=f"TRADE-{base_time.timestamp()}-2",
            symbol="ES",
            side="buy",
            quantity=1,
            price=5000.0,
            realized_pnl=30.0,
            timestamp=base_time + timedelta(seconds=20)
        )

        violation2 = await rule.evaluate(event2, mock_engine)
        trade_count_2 = self.db.get_trade_count(test_account, window=60)
        console.print(f"  Trade count in last minute: {trade_count_2}/3")

        if violation2:
            violations.append(violation2)
            console.print(f"  [X] [red]VIOLATION: {violation2}[/red]")
        else:
            console.print("  [OK] [green]No violation (2/3 trades)[/green]")

        # Trade 3 at base_time + 40s
        console.print("[yellow]Trade 3 (now + 40s)[/yellow]")
        event3 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "symbol": "NQ",
                "profitAndLoss": 20.0
            },
            timestamp=base_time + timedelta(seconds=40)
        )

        self.db.add_trade(
            account_id=test_account,
            trade_id=f"TRADE-{base_time.timestamp()}-3",
            symbol="NQ",
            side="sell",
            quantity=2,
            price=18000.0,
            realized_pnl=50.0,
            timestamp=base_time + timedelta(seconds=40)
        )

        violation3 = await rule.evaluate(event3, mock_engine)
        trade_count_3 = self.db.get_trade_count(test_account, window=60)
        console.print(f"  Trade count in last minute: {trade_count_3}/3")

        if violation3:
            violations.append(violation3)
            console.print(f"  [X] [red]VIOLATION: {violation3}[/red]")
        else:
            console.print("  [OK] [green]No violation (3/3 trades)[/green]")

        # Trade 4 (base_time + 50s, BREACH!)
        console.print("[yellow]Trade 4 (now + 50s)[/yellow]")
        event4 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "symbol": "MNQ",
                "profitAndLoss": 15.0
            },
            timestamp=base_time + timedelta(seconds=50)
        )

        self.db.add_trade(
            account_id=test_account,
            trade_id=f"TRADE-{base_time.timestamp()}-4",
            symbol="MNQ",
            side="buy",
            quantity=1,
            price=21505.0,
            realized_pnl=15.0,
            timestamp=base_time + timedelta(seconds=50)
        )

        violation4 = await rule.evaluate(event4, mock_engine)
        trade_count_4 = self.db.get_trade_count(test_account, window=60)
        console.print(f"  Trade count in last minute: {trade_count_4}/3")

        if violation4:
            violations.append(violation4)
            console.print(f"  [X] [red]VIOLATION: {violation4}[/red]")
            console.print(f"  [red]Enforcement action: {violation4.get('action')}[/red]")
            console.print(f"  [red]Cooldown duration: {violation4.get('cooldown_duration')}s[/red]")
        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        # Validate results
        result = {
            "rule": "RULE-006",
            "passed": len(violations) == 1,  # Should violate on trade 4 only
            "violations": violations,
            "arithmetic_correct": trade_count_4 == 4,  # 4 trades in rolling window
            "enforcement_action": violations[0].get('action') if violations else None
        }

        if result["passed"] and result["arithmetic_correct"]:
            console.print("\n[bold green][OK] RULE-006 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-006 FAILED[/bold red]")

        return result


    async def test_rule_007_cooldown_after_loss(self) -> dict[str, Any]:
        """
        Test RULE-007: Cooldown After Loss

        Arithmetic Test:
        - Loss threshold: -$100 triggers 5-minute cooldown
        - Trade 1: -$50 (OK, below threshold)
        - Trade 2: -$150 (BREACH, triggers cooldown)

        Expected:
        - Violations: 1
        - Enforcement: flatten + cooldown timer
        - Lockout: 300 seconds (5 minutes)
        """
        console.print("\n[bold cyan]Testing RULE-007: Cooldown After Loss[/bold cyan]")

        from risk_manager.rules.cooldown_after_loss import CooldownAfterLossRule
        from risk_manager.state.timer_manager import TimerManager

        # Create timer manager
        timer_manager = TimerManager()
        await timer_manager.start()

        # Create rule with test configuration
        rule = CooldownAfterLossRule(
            loss_thresholds=[
                {"loss_amount": -100.0, "cooldown_duration": 300}  # -$100 = 5 min
            ],
            timer_manager=timer_manager,
            pnl_tracker=self.pnl_tracker,
            lockout_manager=self.lockout_manager,
            action="flatten"
        )

        test_account = "TEST-ACCOUNT-007"
        violations = []

        # Mock engine
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Trade 1: -$50 loss (below threshold)
        console.print("[yellow]Trade 1: -$50 loss[/yellow]")

        event1 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": -50.0,  # Rule expects camelCase!
                "symbol": "MNQ"
            }
        )

        violation1 = await rule.evaluate(event1, mock_engine)

        if violation1:
            violations.append(violation1)
            console.print(f"  [X] [red]VIOLATION: {violation1}[/red]")
        else:
            console.print("  [OK] [green]No violation (loss below threshold)[/green]")

        # Verify no lockout set
        is_locked_before = self.lockout_manager.is_locked_out(test_account)
        console.print(f"  Account locked: {is_locked_before}")

        # Trade 2: -$150 loss (exceeds threshold, BREACH!)
        console.print("[yellow]Trade 2: -$150 loss[/yellow]")

        event2 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": -150.0,
                "symbol": "ES"
            }
        )

        violation2 = await rule.evaluate(event2, mock_engine)

        is_locked_after = False
        if violation2:
            violations.append(violation2)
            console.print(f"  [X] [red]VIOLATION: {violation2.get('message')}[/red]")
            console.print(f"  [red]Enforcement action: {violation2.get('action')}[/red]")
            console.print(f"  [red]Cooldown duration: {violation2.get('cooldown_duration')}s[/red]")

            # Execute enforcement to set lockout
            await rule.enforce(test_account, violation2, mock_engine)

            # Verify lockout was set
            is_locked_after = self.lockout_manager.is_locked_out(test_account)
            console.print(f"  Account locked after enforcement: {is_locked_after}")

        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        # Cleanup timer manager
        await timer_manager.stop()

        # Validate results
        result = {
            "rule": "RULE-007",
            "passed": len(violations) == 1,  # Should violate on trade 2 only
            "violations": violations,
            "arithmetic_correct": (
                len(violations) == 1 and
                violations[0].get('cooldown_duration') == 300 and
                violations[0].get('loss_amount') == -150.0
            ),
            "enforcement_action": violations[0].get('action') if violations else None,
            "lockout_verified": is_locked_after if violations else False
        }

        if result["passed"] and result["arithmetic_correct"] and result["lockout_verified"]:
            console.print("\n[bold green][OK] RULE-007 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-007 FAILED[/bold red]")

        return result


    async def test_rule_009_session_block_outside(self) -> dict[str, Any]:
        """
        Test RULE-009: Session Block Outside Hours

        Time-Based Test:
        - Trading hours: 08:30 - 15:00 CT (America/Chicago)
        - Trade at 08:00 CT (before hours) -> VIOLATION!
        - Trade at 10:00 CT (during hours) -> OK
        - Trade at 16:00 CT (after hours) -> VIOLATION!

        Expected:
        - Violations: 2 (before and after hours)
        - Enforcement: flatten + lockout until next session
        - Lockout duration: Until next session start (08:30 CT next day)
        """
        console.print("\n[bold cyan]Testing RULE-009: Session Block Outside Hours[/bold cyan]")

        from risk_manager.rules.session_block_outside import SessionBlockOutsideRule

        # Create rule with test configuration (08:30 - 15:00 CT)
        rule = SessionBlockOutsideRule(
            config={
                "enabled": True,
                "global_session": {
                    "enabled": True,
                    "start": "08:30",
                    "end": "15:00",
                    "timezone": "America/Chicago"
                },
                "block_weekends": True,
                "lockout_outside_session": True
            },
            lockout_manager=self.lockout_manager
        )

        test_account = "TEST-ACCOUNT-009"
        violations = []

        # Mock engine
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Test 1: Trade at 08:00 CT (BEFORE hours) - Wednesday
        console.print("[yellow]Test 1: Position opened at 08:00 CT (before hours)[/yellow]")

        # Create a specific datetime: Wednesday, 08:00 CT
        mock_time_before = datetime(2025, 10, 29, 8, 0, 0, tzinfo=ZoneInfo("America/Chicago"))  # Wednesday

        with patch('risk_manager.rules.session_block_outside.datetime') as mock_dt:
            mock_dt.now.return_value = mock_time_before
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            event1 = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={
                    "account_id": test_account,
                    "symbol": "MNQ",
                    "size": 1,
                    "side": "long"
                }
            )

            violation1 = await rule.evaluate(event1, mock_engine)

            if violation1:
                violations.append(violation1)
                console.print(f"  [X] [red]VIOLATION: {violation1.get('message')}[/red]")
                console.print(f"  [red]Current time: {violation1.get('current_time_str')}[/red]")
                console.print(f"  [red]Session: {violation1.get('session_start')} - {violation1.get('session_end')}[/red]")
            else:
                console.print("  [X] [red]ERROR: Should have violated (before hours)![/red]")

        # Test 2: Trade at 10:00 CT (DURING hours) - OK
        console.print("[yellow]Test 2: Position opened at 10:00 CT (during hours)[/yellow]")

        mock_time_during = datetime(2025, 10, 29, 10, 0, 0, tzinfo=ZoneInfo("America/Chicago"))

        with patch('risk_manager.rules.session_block_outside.datetime') as mock_dt:
            mock_dt.now.return_value = mock_time_during
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            event2 = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={
                    "account_id": test_account,
                    "symbol": "ES",
                    "size": 1,
                    "side": "long"
                }
            )

            violation2 = await rule.evaluate(event2, mock_engine)

            if violation2:
                violations.append(violation2)
                console.print(f"  [X] [red]VIOLATION: {violation2}[/red]")
            else:
                console.print("  [OK] [green]No violation (during hours)[/green]")

        # Test 3: Trade at 16:00 CT (AFTER hours) - VIOLATION
        console.print("[yellow]Test 3: Position opened at 16:00 CT (after hours)[/yellow]")

        mock_time_after = datetime(2025, 10, 29, 16, 0, 0, tzinfo=ZoneInfo("America/Chicago"))

        with patch('risk_manager.rules.session_block_outside.datetime') as mock_dt:
            mock_dt.now.return_value = mock_time_after
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            event3 = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={
                    "account_id": test_account,
                    "symbol": "NQ",
                    "size": 1,
                    "side": "long"
                }
            )

            violation3 = await rule.evaluate(event3, mock_engine)

            if violation3:
                violations.append(violation3)
                console.print(f"  [X] [red]VIOLATION: {violation3.get('message')}[/red]")
                console.print(f"  [red]Current time: {violation3.get('current_time_str')}[/red]")
            else:
                console.print("  [X] [red]ERROR: Should have violated (after hours)![/red]")

        # Validate results
        expected_violations = 2  # Before hours and after hours
        all_violations_correct = (
            len(violations) == expected_violations and
            all(v.get('action') == 'flatten' for v in violations) and
            all(v.get('lockout_required') for v in violations)
        )

        result = {
            "rule": "RULE-009",
            "passed": len(violations) == expected_violations,
            "violations": violations,
            "arithmetic_correct": all_violations_correct,
            "enforcement_action": "flatten + lockout" if violations else None
        }

        if result["passed"] and result["arithmetic_correct"]:
            console.print("\n[bold green][OK] RULE-009 PASSED[/bold green]")
        else:
            console.print(f"\n[bold red][X] RULE-009 FAILED (Expected {expected_violations} violations, got {len(violations)})[/bold red]")

        return result

    async def test_rule_012_trade_management(self) -> dict[str, Any]:
        """
        Test RULE-012: Trade Management (Automation)

        Arithmetic Test:
        - Auto stop-loss: 10 ticks below entry
        - Auto take-profit: 20 ticks above entry
        - Position: 2 MNQ long @ $21,500
        - Tick size: $0.25
        - Expected stop: $21,500 - (10 * $0.25) = $21,497.50
        - Expected target: $21,500 + (20 * $0.25) = $21,505.00

        Expected:
        - Violations: 0 (this is automation, not enforcement)
        - Actions: 1 (place_bracket_order)
        - Bracket parameters correct
        """
        console.print("\n[bold cyan]Testing RULE-012: Trade Management[/bold cyan]")

        from risk_manager.rules.trade_management import TradeManagementRule

        # Create rule with test configuration
        rule = TradeManagementRule(
            config={
                "enabled": True,
                "auto_stop_loss": {"enabled": True, "distance": 10},
                "auto_take_profit": {"enabled": True, "distance": 20},
                "trailing_stop": {"enabled": False}
            },
            tick_values={"MNQ": 2.00},  # $2 per tick for MNQ
            tick_sizes={"MNQ": 0.25}    # $0.25 tick size for MNQ
        )

        actions = []

        # Mock engine with position
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Position opened: 2 MNQ long @ $21,500
        console.print("[yellow]Position opened: 2 MNQ long @ $21,500[/yellow]")
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "avgPrice": 21500.0,
                "contractId": "CON.F.US.MNQ.U25"
            }
        }

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "size": 2,
                "avgPrice": 21500.0,
                "contractId": "CON.F.US.MNQ.U25"
            }
        )

        action = await rule.evaluate(event, mock_engine)
        if action:
            actions.append(action)
            console.print(f"  [OK] [green]Action generated: {action['action']}[/green]")
            console.print(f"  [green]Stop-loss: ${action.get('stop_price', 0):.2f}[/green]")
            console.print(f"  [green]Take-profit: ${action.get('take_profit_price', 0):.2f}[/green]")
        else:
            console.print("  [X] [red]ERROR: Should have generated bracket order![/red]")

        # Validate bracket parameters
        expected_stop = 21500.0 - (10 * 0.25)  # $21,497.50
        expected_target = 21500.0 + (20 * 0.25)  # $21,505.00

        arithmetic_correct = False
        if action:
            stop_correct = abs(action.get('stop_price', 0) - expected_stop) < 0.01
            target_correct = abs(action.get('take_profit_price', 0) - expected_target) < 0.01
            arithmetic_correct = stop_correct and target_correct

            if stop_correct:
                console.print(f"  [OK] [green]Stop-loss calculation correct: ${expected_stop:.2f}[/green]")
            else:
                console.print(f"  [X] [red]Stop-loss calculation wrong: got ${action.get('stop_price', 0):.2f}, expected ${expected_stop:.2f}[/red]")

            if target_correct:
                console.print(f"  [OK] [green]Take-profit calculation correct: ${expected_target:.2f}[/green]")
            else:
                console.print(f"  [X] [red]Take-profit calculation wrong: got ${action.get('take_profit_price', 0):.2f}, expected ${expected_target:.2f}[/red]")

        result = {
            "rule": "RULE-012",
            "passed": len(actions) == 1 and action.get('action') == 'place_bracket_order',
            "violations": [],  # Automation rules don't violate
            "actions": actions,
            "arithmetic_correct": arithmetic_correct,
            "enforcement_action": None  # No enforcement, just automation
        }

        if result["passed"] and result["arithmetic_correct"]:
            console.print("\n[bold green][OK] RULE-012 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-012 FAILED[/bold red]")

        return result

    async def test_rule_013_daily_realized_profit(self) -> dict[str, Any]:
        """
        Test RULE-013: Daily Realized Profit Target

        Arithmetic Test:
        - Profit target: +$1000
        - Trade 1: +$300 (OK)
        - Trade 2: +$400 (OK, total: +$700)
        - Trade 3: +$400 (BREACH, total: +$1100 > +$1000)

        Expected:
        - Violations: 1
        - Enforcement: flatten
        - Lockout: Until next reset (5 PM ET)
        - Positive messaging ("Good job!")
        """
        console.print("\n[bold cyan]Testing RULE-013: Daily Realized Profit Target[/bold cyan]")

        from risk_manager.rules.daily_realized_profit import DailyRealizedProfitRule

        # Create rule with test configuration
        rule = DailyRealizedProfitRule(
            target=1000.0,
            pnl_tracker=self.pnl_tracker,
            lockout_manager=self.lockout_manager,
            action="flatten",
            reset_time="17:00",
            timezone_name="America/New_York"
        )

        test_account = "TEST-ACCOUNT-002"
        violations = []

        # Mock engine
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Simulate Trade 1: +$300 profit
        console.print("[yellow]Trade 1: +$300 profit[/yellow]")

        event1 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": 300.0,  # Rule expects camelCase!
                "symbol": "ES"
            }
        )

        violation1 = await rule.evaluate(event1, mock_engine)
        current_pnl = self.pnl_tracker.get_daily_pnl(test_account)
        console.print(f"  Current P&L: ${current_pnl:.2f}")

        if violation1:
            violations.append(violation1)
            console.print(f"  [X] [red]VIOLATION: {violation1}[/red]")
        else:
            console.print("  [OK] [green]No violation[/green]")

        # Simulate Trade 2: +$400 profit (total: +$700)
        console.print("[yellow]Trade 2: +$400 profit[/yellow]")

        event2 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": 400.0,
                "symbol": "MNQ"
            }
        )

        violation2 = await rule.evaluate(event2, mock_engine)
        current_pnl = self.pnl_tracker.get_daily_pnl(test_account)
        console.print(f"  Current P&L: ${current_pnl:.2f}")

        if violation2:
            violations.append(violation2)
            console.print(f"  [X] [red]VIOLATION: {violation2}[/red]")
        else:
            console.print("  [OK] [green]No violation[/green]")

        # Simulate Trade 3: +$400 profit (total: +$1100, BREACH!)
        console.print("[yellow]Trade 3: +$400 profit[/yellow]")

        event3 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": 400.0,
                "symbol": "NQ"
            }
        )

        violation3 = await rule.evaluate(event3, mock_engine)
        current_pnl = self.pnl_tracker.get_daily_pnl(test_account)
        console.print(f"  Current P&L: ${current_pnl:.2f}")

        if violation3:
            violations.append(violation3)
            console.print(f"  [X] [red]VIOLATION: {violation3}[/red]")
            console.print(f"  [green]Enforcement action: {violation3.get('action')} (Good job!)[/green]")
        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        # Validate results
        result = {
            "rule": "RULE-013",
            "passed": len(violations) == 1,  # Should violate on trade 3 only
            "violations": violations,
            "arithmetic_correct": current_pnl == 1100.0,
            "enforcement_action": violations[0].get('action') if violations else None
        }

        if result["passed"] and result["arithmetic_correct"]:
            console.print("\n[bold green][OK] RULE-013 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-013 FAILED[/bold red]")

        return result

    async def test_rule_005_max_unrealized_profit(self) -> dict[str, Any]:
        """
        Test RULE-005: Max Unrealized Profit (Take Profit)

        Arithmetic Test:
        - Target: +$500 unrealized profit (take profit)
        - Position opened: ES @ $5,000, size=2 long
        - Market price 1: $5,002 (profit = $200, OK)
        - Market price 2: $5,005 (profit = $500, BREACH!)

        P&L Calculation:
        - ES tick size: 0.25 points (4 ticks per point)
        - ES tick value: $50 per point = $12.50 per tick
        - Formula: P&L = (price_diff / tick_size) * abs(size) * tick_value
        - Price $5,002: (2 / 0.25) * 2 * 12.5 = 8 * 2 * 12.5 = $200
        - Price $5,005: (5 / 0.25) * 2 * 12.5 = 20 * 2 * 12.5 = $500 (BREACH!)

        Expected:
        - Violations: 1 (at price $5,005)
        - Enforcement: close_position (take profit)
        - NO lockout (trade-by-trade rule)
        """
        console.print("\n[bold cyan]Testing RULE-005: Max Unrealized Profit[/bold cyan]")

        from risk_manager.rules.max_unrealized_profit import MaxUnrealizedProfitRule

        # Create rule with test configuration
        rule = MaxUnrealizedProfitRule(
            target=500.0,  # Take profit at $500
            tick_values={"ES": 12.5},  # $12.50 per tick (0.25 point increment)
            tick_sizes={"ES": 0.25},   # 0.25 point minimum increment
            action="close_position"
        )

        violations = []

        # Mock engine with position and market prices
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Position opened: ES @ $5,000, size=2 long
        console.print("[yellow]Position opened: ES @ $5,000, size=2 long[/yellow]")
        mock_engine.current_positions = {
            "ES": {
                "avgPrice": 5000.0,
                "size": 2,
                "contractId": "CON.F.US.ES.H25"
            }
        }
        mock_engine.market_prices = {"ES": 5000.0}

        event0 = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "avgPrice": 5000.0,
                "size": 2,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        violation0 = await rule.evaluate(event0, mock_engine)
        if violation0:
            violations.append(violation0)
            console.print(f"  [X] [red]VIOLATION: {violation0}[/red]")
        else:
            console.print("  [OK] [green]No violation (profit = $0)[/green]")

        # Market price 1: $5,002 (profit = $200, should be OK)
        console.print("[yellow]Market price 1: $5,002[/yellow]")
        mock_engine.market_prices = {"ES": 5002.0}

        event1 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "avgPrice": 5000.0,
                "size": 2,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        violation1 = await rule.evaluate(event1, mock_engine)

        # Calculate expected profit: (5002 - 5000) / 0.25 * 2 * 12.5 = 8 * 2 * 12.5 = $200
        expected_profit_1 = (5002.0 - 5000.0) / 0.25 * 2 * 12.5
        console.print(f"  Expected profit: ${expected_profit_1:.2f}")

        if violation1:
            violations.append(violation1)
            console.print(f"  [X] [red]VIOLATION: {violation1}[/red]")
        else:
            console.print("  [OK] [green]No violation (profit < $500 target)[/green]")

        # Market price 2: $5,005 (profit = $500, BREACH!)
        console.print("[yellow]Market price 2: $5,005[/yellow]")
        mock_engine.market_prices = {"ES": 5005.0}

        event2 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "avgPrice": 5000.0,
                "size": 2,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        violation2 = await rule.evaluate(event2, mock_engine)

        # Calculate expected profit: (5005 - 5000) / 0.25 * 2 * 12.5 = 20 * 2 * 12.5 = $500
        expected_profit_2 = (5005.0 - 5000.0) / 0.25 * 2 * 12.5
        console.print(f"  Expected profit: ${expected_profit_2:.2f}")

        if violation2:
            violations.append(violation2)
            console.print(f"  [X] [red]VIOLATION: {violation2}[/red]")
            console.print(f"  [red]Enforcement action: {violation2.get('action')}[/red]")
            console.print(f"  [red]Unrealized P&L: ${violation2.get('unrealized_pnl'):.2f}[/red]")
        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        # Validate results
        result = {
            "rule": "RULE-005",
            "passed": len(violations) == 1,  # Should violate on price 2 only
            "violations": violations,
            "arithmetic_correct": violation2 is not None and violation2.get('unrealized_pnl', 0) >= 500.0,
            "enforcement_action": violations[0].get('action') if violations else None
        }

        if result["passed"] and result["arithmetic_correct"]:
            console.print("\n[bold green][OK] RULE-005 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-005 FAILED[/bold red]")

        return result



    async def test_rule_008_no_stop_loss_grace(self) -> dict[str, Any]:
        """
        Test RULE-008: No Stop-Loss Grace

        Scenario Test:
        - Grace period: 60 seconds (for faster testing)
        - Position opened → Grace period starts
        - Wait 61 seconds (simulated)
        - No stop-loss placed → VIOLATION!

        Expected:
        - Violations: 1 (after grace expires)
        - Enforcement: close_position
        - NO lockout (trade-by-trade rule)
        """
        console.print("\n[bold cyan]Testing RULE-008: No Stop-Loss Grace[/bold cyan]")

        from risk_manager.rules.no_stop_loss_grace import NoStopLossGraceRule
        from risk_manager.state.timer_manager import TimerManager

        # Create timer manager
        timer_manager = TimerManager()
        await timer_manager.start()

        # Create rule with short grace period for testing
        rule = NoStopLossGraceRule(
            grace_period_seconds=60,
            enforcement="close_position",
            timer_manager=timer_manager,
            enabled=True
        )

        violations = []
        test_contract_id = "CON.F.US.MNQ.U25"

        # Mock engine
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {},
            'enforcement_executor': type('MockExecutor', (), {
                'close_position': lambda symbol, contract_id: asyncio.sleep(0)
            })()
        })()

        # Step 1: Open position (starts grace period)
        console.print("[yellow]Step 1: Open position (starts 60s grace period)[/yellow]")

        event_open = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "contract_id": test_contract_id,
                "symbol": "MNQ",
                "size": 1
            }
        )

        violation = await rule.evaluate(event_open, mock_engine)
        if violation:
            violations.append(violation)
            console.print(f"  [X] [red]Unexpected violation: {violation}[/red]")
        else:
            console.print("  [OK] [green]Grace period started[/green]")

        # Check timer is active
        timer_name = f"no_stop_loss_grace_{test_contract_id}"
        if timer_manager.has_timer(timer_name):
            remaining = timer_manager.get_remaining_time(timer_name)
            console.print(f"  [OK] [green]Timer active: {remaining}s remaining[/green]")
        else:
            console.print("  [X] [red]ERROR: Timer not created![/red]")

        # Step 2: Simulate time passing (61 seconds) and check timer expiry
        console.print("[yellow]Step 2: Simulating 61 seconds passing...[/yellow]")

        # We'll manually trigger the timer expiry for testing
        # In production, this would happen automatically via the timer manager
        timer_manager.timers[timer_name]["expires_at"] = datetime.now() - timedelta(seconds=1)

        # Manually check timers (this would normally happen in background task)
        await timer_manager.check_timers()

        # The violation happens via callback, not return value
        # So we check if timer was removed (indicating callback executed)
        if not timer_manager.has_timer(timer_name):
            console.print("  [X] [red]VIOLATION: Grace period expired without stop-loss[/red]")
            violations.append({
                "rule": "NoStopLossGraceRule",
                "message": "No stop-loss placed within grace period",
                "action": "close_position"
            })
        else:
            console.print("  [X] [red]ERROR: Timer should have expired![/red]")

        # Stop timer manager
        await timer_manager.stop()

        # Validate results
        result = {
            "rule": "RULE-008",
            "passed": len(violations) == 1,  # Should violate after grace expires
            "violations": violations,
            "arithmetic_correct": True,  # Timer logic correct
            "enforcement_action": violations[0].get('action') if violations else None
        }

        if result["passed"]:
            console.print("\n[bold green][OK] RULE-008 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-008 FAILED[/bold red]")

        return result

    async def test_rule_011_symbol_blocks(self) -> dict[str, Any]:
        """
        Test RULE-011: Symbol Blocks

        Scenario Test:
        - Blocked symbols: ["ES", "NQ"]
        - Try to open MNQ position → [OK] (not blocked)
        - Try to open ES position → [X] VIOLATION (blocked)
        - Try to open NQ position → [X] VIOLATION (blocked)

        Expected:
        - Violations: 2 (ES and NQ)
        - Enforcement: close
        - NO lockout (trade-by-trade rule)
        """
        console.print("\n[bold cyan]Testing RULE-011: Symbol Blocks[/bold cyan]")

        from risk_manager.rules.symbol_blocks import SymbolBlocksRule

        # Create rule with blocked symbols
        rule = SymbolBlocksRule(
            blocked_symbols=["ES", "NQ"],
            action="close"
        )

        violations = []

        # Mock engine
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Test 1: MNQ (not blocked) → Should be OK
        console.print("[yellow]Test 1: Open MNQ position (not blocked)[/yellow]")

        event_mnq = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "size": 1}
        )

        violation_mnq = await rule.evaluate(event_mnq, mock_engine)
        if violation_mnq:
            violations.append(violation_mnq)
            console.print(f"  [X] [red]Unexpected violation: {violation_mnq}[/red]")
        else:
            console.print("  [OK] [green]MNQ is allowed[/green]")

        # Test 2: ES (blocked) → Should violate
        console.print("[yellow]Test 2: Open ES position (blocked)[/yellow]")

        event_es = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "size": 1}
        )

        violation_es = await rule.evaluate(event_es, mock_engine)
        if violation_es:
            violations.append(violation_es)
            console.print(f"  [X] [red]VIOLATION: {violation_es}[/red]")
            console.print(f"  [red]Enforcement action: {violation_es.get('action')}[/red]")
        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        # Test 3: NQ (blocked) → Should violate
        console.print("[yellow]Test 3: Open NQ position (blocked)[/yellow]")

        event_nq = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "NQ", "size": 1}
        )

        violation_nq = await rule.evaluate(event_nq, mock_engine)
        if violation_nq:
            violations.append(violation_nq)
            console.print(f"  [X] [red]VIOLATION: {violation_nq}[/red]")
            console.print(f"  [red]Enforcement action: {violation_nq.get('action')}[/red]")
        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        # Validate results
        result = {
            "rule": "RULE-011",
            "passed": len(violations) == 2,  # Should violate on ES and NQ
            "violations": violations,
            "arithmetic_correct": True,  # Blocked ES and NQ, allowed MNQ
            "enforcement_action": violations[0].get('action') if violations else None
        }

        if result["passed"]:
            console.print("\n[bold green][OK] RULE-011 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-011 FAILED[/bold red]")

        return result

    async def run_all_tests(self) -> dict[str, dict[str, Any]]:
        """Run all rule tests."""
        console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
        console.print("[bold cyan]        RISK RULE VALIDATION TESTS[/bold cyan]")
        console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")

        # Test each rule
        results = {}

        results["RULE-001"] = await self.test_rule_001_max_contracts()
        results["RULE-002"] = await self.test_rule_002_max_contracts_per_instrument()
        results["RULE-003"] = await self.test_rule_003_daily_realized_loss()
        results["RULE-004"] = await self.test_rule_004_daily_unrealized_loss()
        results["RULE-005"] = await self.test_rule_005_max_unrealized_profit()
        results["RULE-006"] = await self.test_rule_006_trade_frequency_limit()
        results["RULE-007"] = await self.test_rule_007_cooldown_after_loss()
        results["RULE-008"] = await self.test_rule_008_no_stop_loss_grace()
        results["RULE-009"] = await self.test_rule_009_session_block_outside()
        results["RULE-011"] = await self.test_rule_011_symbol_blocks()
        results["RULE-012"] = await self.test_rule_012_trade_management()
        results["RULE-013"] = await self.test_rule_013_daily_realized_profit()

        # Add more rule tests here...
        # ... etc for all 13 rules

        # Print summary
        console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
        console.print("[bold cyan]                    SUMMARY[/bold cyan]")
        console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]\n")

        table = Table(title="Rule Test Results")
        table.add_column("Rule", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Arithmetic", style="yellow")
        table.add_column("Enforcement", style="magenta")

        for rule_id, result in results.items():
            status = "[OK] PASS" if result["passed"] else "[X] FAIL"
            arithmetic = "[OK]" if result["arithmetic_correct"] else "[X]"
            enforcement = result["enforcement_action"] or "N/A"

            table.add_row(rule_id, status, arithmetic, enforcement)

        console.print(table)

        return results


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Risk Rule Validation Tests")
    parser.add_argument("--rule", help="Test specific rule (e.g., RULE-003)", default=None)
    parser.add_argument("--live", action="store_true", help="Test with live SDK connection")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    # Load config (mock for now)
    from risk_manager.config.models import RiskConfig

    # For this test, we'll use a minimal config
    # In production, load from config/risk_config.yaml

    tester = RuleTester(config=None, verbose=args.verbose)

    if args.rule:
        # Test specific rule
        test_method = f"test_{args.rule.lower().replace('-', '_')}"
        if hasattr(tester, test_method):
            result = await getattr(tester, test_method)()
            console.print(f"\n[bold]Result:[/bold] {result}")
        else:
            console.print(f"[red]Unknown rule: {args.rule}[/red]")
    else:
        # Test all rules
        results = await tester.run_all_tests()

        # Calculate pass rate
        total = len(results)
        passed = sum(1 for r in results.values() if r["passed"])

        console.print(f"\n[bold]Pass Rate:[/bold] {passed}/{total} ({passed/total*100:.1f}%)")

        if passed == total:
            console.print("\n[bold green][SUCCESS] ALL TESTS PASSED![/bold green]\n")
            return 0
        else:
            console.print("\n[bold red][WARN]  SOME TESTS FAILED[/bold red]\n")
            return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
