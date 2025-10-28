"""
End-to-End Tests for Timer-Based Rules (RULE-006 & RULE-008)

Tests complete timer lifecycle with LIVE async timers (not mocked):
- RULE-006: Trade Frequency Limit with cooldown timers
- RULE-008: No Stop-Loss Grace with grace period timers

Complete Flow:
1. Event triggers timer start
2. Real asyncio.sleep() waits for timer expiry
3. Timer callback fires and enforces action
4. State updated correctly (lockout/position closed)
5. Proper cleanup and state management

Suite Focus:
- Real async timer behavior (not mocked)
- Timer expiry and auto-unlock
- Rolling window tracking (RULE-006)
- Grace period enforcement (RULE-008)
- Multi-position timer independence
- Timer cancellation scenarios
"""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# Risk Manager imports
from risk_manager.core.config import RiskConfig
from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.rules.no_stop_loss_grace import NoStopLossGraceRule
from risk_manager.rules.trade_frequency_limit import TradeFrequencyLimitRule
from risk_manager.state.database import Database
from risk_manager.state.lockout_manager import LockoutManager
from risk_manager.state.pnl_tracker import PnLTracker
from risk_manager.state.timer_manager import TimerManager


class MockPosition:
    """Mock SDK Position object."""

    def __init__(self, size=0, symbol="MNQ", avg_price=16500.0, unrealized_pnl=0.0):
        self.size = size
        self.symbol = symbol
        self.averagePrice = avg_price
        self.unrealizedPnl = unrealized_pnl
        self.realizedPnl = 0.0
        self.contractId = f"CON.F.US.{symbol}.Z25"
        self.id = 1
        self.accountId = 12345


class MockTradingSuite:
    """Mock SDK TradingSuite."""

    def __init__(self):
        self.event_bus = EventBus()
        self._positions = []
        self.account_info = Mock()
        self.account_info.id = "PRAC-V2-126244-84184528"
        self.account_info.name = "150k Practice Account"

    def __getitem__(self, symbol):
        """Return mock instrument context."""
        context = Mock()
        context.positions = Mock()
        context.positions.get_all_positions = AsyncMock(return_value=self._positions)
        context.positions.close_all_positions = AsyncMock()
        context.positions.close_position = AsyncMock()
        context.instrument_info = Mock()
        context.instrument_info.name = symbol
        context.instrument_info.id = f"CON.F.US.{symbol}.Z25"
        return context

    async def on(self, event_type, handler):
        """Subscribe to event."""
        self.event_bus.subscribe(event_type, handler)

    async def disconnect(self):
        """Mock disconnect."""
        pass

    @property
    def is_connected(self):
        """Mock connection status."""
        return True


@pytest.mark.e2e
class TestTimerRulesE2E:
    """End-to-end tests for timer-based rules (RULE-006 & RULE-008)."""

    @pytest.fixture
    def mock_sdk_suite(self):
        """Create mock SDK suite."""
        return MockTradingSuite()

    @pytest.fixture
    async def database(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test_risk_manager.db"
        db = Database(str(db_path))

        # Add trade tracking methods
        self._add_trade_tracking_methods(db)

        yield db
        # Cleanup
        db.close()

    @pytest.fixture
    async def lockout_manager(self, database):
        """Create lockout manager."""
        manager = LockoutManager(database)
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.fixture
    async def timer_manager(self):
        """Create timer manager with real async timers."""
        manager = TimerManager()
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.fixture
    async def pnl_tracker(self, database):
        """Create P&L tracker."""
        return PnLTracker(database)

    @pytest.fixture
    async def risk_system(
        self, mock_sdk_suite, database, lockout_manager, timer_manager, pnl_tracker
    ):
        """Create simplified risk system with all state managers."""
        config = RiskConfig(
            project_x_api_key="test_api_key",
            project_x_username="test_user",
            max_contracts=2,
        )
        event_bus = EventBus()

        # Mock trading integration
        mock_trading = AsyncMock()
        mock_trading.flatten_all = AsyncMock()
        mock_trading.flatten_position = AsyncMock()
        mock_trading.suite = mock_sdk_suite

        # Create engine with mock trading
        from risk_manager.core.engine import RiskEngine

        engine = RiskEngine(config, event_bus, mock_trading)
        engine.lockout_manager = lockout_manager
        engine.timer_manager = timer_manager
        engine.pnl_tracker = pnl_tracker
        engine.daily_pnl = 0.0

        # Start engine
        await engine.start()

        # Create a simple container object
        class SimpleRiskSystem:
            def __init__(self):
                self.config = config
                self.event_bus = event_bus
                self.engine = engine
                self.trading_integration = mock_trading
                self.lockout_manager = lockout_manager
                self.timer_manager = timer_manager
                self.pnl_tracker = pnl_tracker
                self.database = database

        system = SimpleRiskSystem()

        yield system

        # Cleanup
        await engine.stop()

    def _add_trade_tracking_methods(self, db):
        """Add trade tracking methods to database instance."""

        def get_trade_count(account_id, window):
            """Get trade count in rolling window (seconds)."""
            cutoff = datetime.now() - timedelta(seconds=window)

            result = db.execute_one(
                """
                SELECT COUNT(*) as count
                FROM trades
                WHERE account_id = ? AND timestamp >= ?
                """,
                (account_id, cutoff.isoformat()),
            )
            return result["count"] if result else 0

        def get_session_trade_count(account_id):
            """Get trade count for current session (today)."""
            today = datetime.now().date().isoformat()

            result = db.execute_one(
                """
                SELECT COUNT(*) as count
                FROM trades
                WHERE account_id = ? AND DATE(timestamp) = ?
                """,
                (account_id, today),
            )
            return result["count"] if result else 0

        def add_trade(account_id, symbol="MNQ", timestamp=None):
            """Add trade to database."""
            if timestamp is None:
                timestamp = datetime.now()

            # Generate unique trade ID using timestamp + random component
            import random

            trade_id = f"TRADE-{timestamp.timestamp()}-{random.randint(1000, 9999)}"

            db.execute_write(
                """
                INSERT INTO trades
                (account_id, trade_id, symbol, side, quantity, price, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id,
                    trade_id,
                    symbol,
                    "BUY",
                    1,
                    20100.0,
                    timestamp.isoformat(),
                    datetime.now().isoformat(),
                ),
            )

        def clear_trades(account_id):
            """Clear all trades for account (test cleanup)."""
            db.execute_write("DELETE FROM trades WHERE account_id = ?", (account_id,))

        # Attach methods to database instance
        db.get_trade_count = get_trade_count
        db.get_session_trade_count = get_session_trade_count
        db.add_trade = add_trade
        db.clear_trades = clear_trades

    # ========================================================================
    # RULE-006: Trade Frequency Limit Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_trade_frequency_cooldown_triggers(
        self, risk_system, mock_sdk_suite
    ):
        """
        Test RULE-006: Trade frequency cooldown triggers after exceeding limit.

        Scenario:
        - Given: 3 trades/minute limit with 2s cooldown
        - When: Execute 4 trades within 60 seconds
        - Then: 4th trade triggers violation
        - Then: Cooldown timer starts (2s)
        - Then: Timer is active and tracking correctly
        """
        account_id = mock_sdk_suite.account_info.id

        # Add frequency limit rule with short cooldown for testing
        frequency_rule = TradeFrequencyLimitRule(
            limits={"per_minute": 3},
            cooldown_on_breach={"per_minute_breach": 2},  # 2s for fast testing
            timer_manager=risk_system.timer_manager,
            db=risk_system.database,
            action="cooldown",
        )

        risk_system.engine.add_rule(frequency_rule)

        # Execute trades 1, 2, 3 (within limit)
        for i in range(3):
            risk_system.database.add_trade(account_id)
            event = RiskEvent(
                event_type=EventType.TRADE_EXECUTED,
                data={"account_id": account_id, "symbol": "MNQ"},
            )
            await risk_system.engine.evaluate_rules(event)
            await asyncio.sleep(0.05)

        # Execute trade 4 (exceeds limit)
        risk_system.database.add_trade(account_id)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"},
        )

        # Track enforcement events
        enforcement_events = []

        async def track_enforcement(event):
            enforcement_events.append(event)

        risk_system.event_bus.subscribe(
            EventType.ENFORCEMENT_ACTION, track_enforcement
        )

        violation = await frequency_rule.evaluate(event, risk_system.engine)

        # Manually trigger enforcement (since engine doesn't auto-enforce "cooldown" action)
        if violation:
            await frequency_rule.enforce(account_id, violation, risk_system.engine)

        await asyncio.sleep(0.2)

        # Verify cooldown timer started
        timer_name = f"trade_frequency_{account_id}"
        assert risk_system.timer_manager.has_timer(timer_name)

        # Verify timer has remaining time
        remaining = risk_system.timer_manager.get_remaining_time(timer_name)
        assert remaining > 0
        assert remaining <= 2

    @pytest.mark.asyncio
    async def test_trade_frequency_cooldown_expires(
        self, risk_system, mock_sdk_suite
    ):
        """
        Test RULE-006: Cooldown timer expires and allows trading again.

        Scenario:
        - Given: Cooldown timer active (2s)
        - When: Wait for timer to expire (real asyncio.sleep)
        - Then: Timer expires and auto-unlocks
        - Then: Can execute trades again
        """
        account_id = mock_sdk_suite.account_info.id

        # Add frequency limit rule
        frequency_rule = TradeFrequencyLimitRule(
            limits={"per_minute": 3},
            cooldown_on_breach={"per_minute_breach": 2},
            timer_manager=risk_system.timer_manager,
            db=risk_system.database,
            action="cooldown",
        )

        risk_system.engine.add_rule(frequency_rule)

        # Hit limit (4 trades)
        for _ in range(4):
            risk_system.database.add_trade(account_id)

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"},
        )

        violation = await frequency_rule.evaluate(event, risk_system.engine)

        # Manually trigger enforcement
        if violation:
            await frequency_rule.enforce(account_id, violation, risk_system.engine)

        await asyncio.sleep(0.2)

        # Verify timer started
        timer_name = f"trade_frequency_{account_id}"
        assert risk_system.timer_manager.has_timer(timer_name)

        # Wait for cooldown to expire (real async timer)
        await asyncio.sleep(2.5)

        # Verify timer expired
        remaining = risk_system.timer_manager.get_remaining_time(timer_name)
        assert remaining == 0

        # Clear old trades and verify can trade again
        risk_system.database.clear_trades(account_id)
        risk_system.database.add_trade(account_id)

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"},
        )

        # Should not violate after cooldown expired
        violation = await frequency_rule.evaluate(event, risk_system.engine)
        assert violation is None

    @pytest.mark.asyncio
    async def test_trade_frequency_rolling_window(
        self, risk_system, mock_sdk_suite
    ):
        """
        Test RULE-006: Rolling window tracking (trades age out of window).

        Scenario:
        - Given: 3 trades/minute limit
        - When: Execute trades at T, T+10s, T+20s, T+70s
        - Then: Trade at T+70s doesn't violate (first trade aged out)
        - Then: Only 2 trades in 60s window + current = 3 (at limit, OK)
        """
        account_id = mock_sdk_suite.account_info.id

        # Add frequency limit rule
        frequency_rule = TradeFrequencyLimitRule(
            limits={"per_minute": 3},
            cooldown_on_breach={"per_minute_breach": 2},
            timer_manager=risk_system.timer_manager,
            db=risk_system.database,
            action="cooldown",
        )

        risk_system.engine.add_rule(frequency_rule)

        now = datetime.now()

        # Add 3 trades in the past
        risk_system.database.add_trade(
            account_id, timestamp=now - timedelta(seconds=70)
        )  # Expired
        risk_system.database.add_trade(
            account_id, timestamp=now - timedelta(seconds=50)
        )  # In window
        risk_system.database.add_trade(
            account_id, timestamp=now - timedelta(seconds=30)
        )  # In window

        # Verify only 2 trades in 60s window
        count = risk_system.database.get_trade_count(account_id, window=60)
        assert count == 2

        # Execute trade at T+70s (should not violate)
        risk_system.database.add_trade(account_id)

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"},
        )

        violation = await frequency_rule.evaluate(event, risk_system.engine)

        # Should not violate (3 total, but only 2 in window + current = 3 at limit)
        assert violation is None

    # ========================================================================
    # RULE-008: No Stop-Loss Grace Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_no_stop_loss_grace_timer_starts(
        self, risk_system, mock_sdk_suite
    ):
        """
        Test RULE-008: Grace period timer starts when position opens.

        Scenario:
        - Given: Position opened without stop-loss
        - When: POSITION_OPENED event fires
        - Then: Grace period timer starts (2s)
        - Then: Timer is active and tracking countdown
        """
        account_id = mock_sdk_suite.account_info.id

        # Mock enforcement executor
        mock_enforcement = Mock()
        mock_enforcement.close_position = AsyncMock(return_value={"success": True})
        risk_system.engine.enforcement_executor = mock_enforcement

        # Add no stop-loss grace rule
        grace_rule = NoStopLossGraceRule(
            grace_period_seconds=2,  # Short period for fast testing
            enforcement="close_position",
            timer_manager=risk_system.timer_manager,
            enabled=True,
        )

        risk_system.engine.add_rule(grace_rule)

        # Open position
        contract_id = "CON.F.US.MNQ.Z25"
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "contract_id": contract_id,
                "size": 2,
                "average_price": 18500.0,
            },
        )

        await risk_system.engine.evaluate_rules(position_event)
        await asyncio.sleep(0.1)

        # Verify timer started
        timer_name = f"no_stop_loss_grace_{contract_id}"
        assert risk_system.timer_manager.has_timer(timer_name)

        # Verify remaining time
        remaining = risk_system.timer_manager.get_remaining_time(timer_name)
        assert 1 <= remaining <= 2

    @pytest.mark.asyncio
    async def test_stop_loss_placed_cancels_timer(
        self, risk_system, mock_sdk_suite
    ):
        """
        Test RULE-008: Stop-loss placement cancels grace period timer.

        Scenario:
        - Given: Position opened, grace timer active
        - When: Stop-loss order placed (type=3 with stopPrice)
        - Then: Grace period timer cancelled
        - Then: No enforcement occurs (grace satisfied)
        """
        account_id = mock_sdk_suite.account_info.id

        # Mock enforcement executor
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": True}

        mock_enforcement = Mock()
        mock_enforcement.close_position = track_close
        risk_system.engine.enforcement_executor = mock_enforcement

        # Add no stop-loss grace rule
        grace_rule = NoStopLossGraceRule(
            grace_period_seconds=2,
            enforcement="close_position",
            timer_manager=risk_system.timer_manager,
            enabled=True,
        )

        risk_system.engine.add_rule(grace_rule)

        # Open position
        contract_id = "CON.F.US.ES.H25"
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "contract_id": contract_id,
                "size": 1,
            },
        )

        await risk_system.engine.evaluate_rules(position_event)
        await asyncio.sleep(0.1)

        timer_name = f"no_stop_loss_grace_{contract_id}"
        assert risk_system.timer_manager.has_timer(timer_name)

        # Place stop-loss order after 0.5 seconds
        await asyncio.sleep(0.5)

        stop_order_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "contract_id": contract_id,
                "symbol": "ES",
                "type": 3,  # STOP order
                "stopPrice": 5180.0,
                "size": 1,
            },
        )

        await risk_system.engine.evaluate_rules(stop_order_event)
        await asyncio.sleep(0.1)

        # Verify timer cancelled
        assert not risk_system.timer_manager.has_timer(timer_name)

        # Wait past original grace period
        await asyncio.sleep(2.0)

        # Verify NO enforcement occurred
        assert len(enforcement_calls) == 0

    @pytest.mark.asyncio
    async def test_grace_period_expires_closes_position(
        self, risk_system, mock_sdk_suite
    ):
        """
        Test RULE-008: Grace period expires and position is closed.

        Scenario:
        - Given: Position opened without stop-loss
        - When: Grace period expires (2s, real asyncio.sleep)
        - Then: Timer callback fires
        - Then: Position closed via enforcement
        """
        account_id = mock_sdk_suite.account_info.id

        # Track enforcement calls
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": True}

        mock_enforcement = Mock()
        mock_enforcement.close_position = track_close
        risk_system.engine.enforcement_executor = mock_enforcement

        # Add no stop-loss grace rule
        grace_rule = NoStopLossGraceRule(
            grace_period_seconds=2,
            enforcement="close_position",
            timer_manager=risk_system.timer_manager,
            enabled=True,
        )

        risk_system.engine.add_rule(grace_rule)

        # Open position
        contract_id = "CON.F.US.MNQ.Z25"
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "contract_id": contract_id,
                "size": 2,
                "average_price": 18500.0,
            },
        )

        await risk_system.engine.evaluate_rules(position_event)
        await asyncio.sleep(0.1)

        timer_name = f"no_stop_loss_grace_{contract_id}"
        assert risk_system.timer_manager.has_timer(timer_name)

        # Wait for grace period to expire (real async timer)
        await asyncio.sleep(2.5)

        # Verify timer expired
        assert not risk_system.timer_manager.has_timer(timer_name)

        # Verify enforcement was called
        assert len(enforcement_calls) == 1
        assert enforcement_calls[0]["symbol"] == "MNQ"
        assert enforcement_calls[0]["contract_id"] == contract_id

    # ========================================================================
    # Combined Timer Tests (RULE-006 + RULE-008 together)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multiple_timers_independent_tracking(
        self, risk_system, mock_sdk_suite
    ):
        """
        Test multiple timer types running concurrently with independence.

        Scenario:
        - Given: Both RULE-006 and RULE-008 active
        - When: Trade frequency cooldown AND grace period active simultaneously
        - Then: Both timers tracked independently
        - Then: Each timer expires correctly without interference
        """
        account_id = mock_sdk_suite.account_info.id

        # Mock enforcement
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append(
                {"type": "close_position", "symbol": symbol, "contract_id": contract_id}
            )
            return {"success": True}

        mock_enforcement = Mock()
        mock_enforcement.close_position = track_close
        risk_system.engine.enforcement_executor = mock_enforcement

        # Add both rules
        frequency_rule = TradeFrequencyLimitRule(
            limits={"per_minute": 3},
            cooldown_on_breach={"per_minute_breach": 3},  # 3s cooldown
            timer_manager=risk_system.timer_manager,
            db=risk_system.database,
            action="cooldown",
        )

        grace_rule = NoStopLossGraceRule(
            grace_period_seconds=2,  # 2s grace period
            enforcement="close_position",
            timer_manager=risk_system.timer_manager,
            enabled=True,
        )

        risk_system.engine.add_rule(frequency_rule)
        risk_system.engine.add_rule(grace_rule)

        # Trigger frequency limit (4 trades)
        for _ in range(4):
            risk_system.database.add_trade(account_id)

        trade_event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"},
        )

        violation = await frequency_rule.evaluate(trade_event, risk_system.engine)

        # Manually trigger enforcement
        if violation:
            await frequency_rule.enforce(account_id, violation, risk_system.engine)

        await asyncio.sleep(0.2)

        # Open position (start grace period)
        contract_id = "CON.F.US.ES.H25"
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "contract_id": contract_id,
                "size": 1,
            },
        )
        await risk_system.engine.evaluate_rules(position_event)
        await asyncio.sleep(0.1)

        # Verify both timers exist
        freq_timer = f"trade_frequency_{account_id}"
        grace_timer = f"no_stop_loss_grace_{contract_id}"

        assert risk_system.timer_manager.has_timer(freq_timer)
        assert risk_system.timer_manager.has_timer(grace_timer)

        # Verify total timer count
        assert risk_system.timer_manager.get_timer_count() == 2

        # Wait for grace period to expire (2s grace + 1s timer loop check interval + buffer)
        await asyncio.sleep(3.5)

        # Grace timer should be expired, frequency timer still active
        assert not risk_system.timer_manager.has_timer(grace_timer)
        assert risk_system.timer_manager.has_timer(freq_timer)

        # Verify position was closed
        assert len(enforcement_calls) == 1
        assert enforcement_calls[0]["contract_id"] == contract_id

        # Wait for frequency cooldown to expire (3s total, 0.5s more)
        await asyncio.sleep(1.0)

        # Both timers should be expired now
        freq_remaining = risk_system.timer_manager.get_remaining_time(freq_timer)
        assert freq_remaining == 0

    @pytest.mark.asyncio
    async def test_timer_cleanup_on_position_close(
        self, risk_system, mock_sdk_suite
    ):
        """
        Test timer cleanup when position closed before grace expires.

        Scenario:
        - Given: Grace period timer active
        - When: Position closed manually before grace expires
        - Then: Timer cancelled properly
        - Then: No enforcement occurs
        """
        account_id = mock_sdk_suite.account_info.id

        # Mock enforcement
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": True}

        mock_enforcement = Mock()
        mock_enforcement.close_position = track_close
        risk_system.engine.enforcement_executor = mock_enforcement

        # Add grace rule
        grace_rule = NoStopLossGraceRule(
            grace_period_seconds=2,
            enforcement="close_position",
            timer_manager=risk_system.timer_manager,
            enabled=True,
        )

        risk_system.engine.add_rule(grace_rule)

        # Open position
        contract_id = "CON.F.US.MNQ.Z25"
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "contract_id": contract_id,
                "size": 2,
            },
        )

        await risk_system.engine.evaluate_rules(position_event)
        await asyncio.sleep(0.1)

        timer_name = f"no_stop_loss_grace_{contract_id}"
        assert risk_system.timer_manager.has_timer(timer_name)

        # Close position manually after 1 second
        await asyncio.sleep(1.0)

        close_event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "symbol": "MNQ",
                "contract_id": contract_id,
                "size": 0,
            },
        )
        await risk_system.engine.evaluate_rules(close_event)
        await asyncio.sleep(0.1)

        # Timer should be cancelled
        assert not risk_system.timer_manager.has_timer(timer_name)

        # Wait past original grace period
        await asyncio.sleep(1.5)

        # No enforcement should occur
        assert len(enforcement_calls) == 0

    @pytest.mark.asyncio
    async def test_state_consistency_across_timer_lifecycle(
        self, risk_system, mock_sdk_suite
    ):
        """
        Test state remains consistent throughout timer lifecycle.

        Scenario:
        - Given: Multiple timers with different expiry times
        - When: Timers expire in sequence
        - Then: State updated correctly at each stage
        - Then: No stale timers remain
        - Then: All enforcement actions completed
        """
        account_id = mock_sdk_suite.account_info.id

        # Track all enforcement
        enforcement_log = []

        async def log_enforcement(symbol, contract_id):
            enforcement_log.append(
                {
                    "timestamp": datetime.now(),
                    "symbol": symbol,
                    "contract_id": contract_id,
                }
            )
            return {"success": True}

        mock_enforcement = Mock()
        mock_enforcement.close_position = log_enforcement
        risk_system.engine.enforcement_executor = mock_enforcement

        # Add grace rule with very short period
        grace_rule = NoStopLossGraceRule(
            grace_period_seconds=1,  # Very short for testing
            enforcement="close_position",
            timer_manager=risk_system.timer_manager,
            enabled=True,
        )

        risk_system.engine.add_rule(grace_rule)

        # Open 3 positions with staggered timing
        contracts = [
            "CON.F.US.MNQ.Z25",
            "CON.F.US.ES.H25",
            "CON.F.US.NQ.Z25",
        ]

        for i, contract_id in enumerate(contracts):
            position_event = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={
                    "symbol": f"SYM{i}",
                    "contract_id": contract_id,
                    "size": 1,
                },
            )
            await risk_system.engine.evaluate_rules(position_event)
            await asyncio.sleep(0.3)  # Stagger by 300ms

        # All timers should exist
        assert risk_system.timer_manager.get_timer_count() == 3

        # Wait for all timers to expire (1s grace + 0.6s stagger + buffer)
        await asyncio.sleep(2.5)

        # All timers should be expired and removed
        assert risk_system.timer_manager.get_timer_count() == 0

        # All positions should have been closed
        assert len(enforcement_log) == 3

        # Verify enforcement was sequential (not concurrent issues)
        for i, enforcement in enumerate(enforcement_log):
            assert enforcement["contract_id"] == contracts[i]
