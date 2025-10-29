"""
End-to-End Tests for Monitoring & Lockout Rules

Tests RULE-010 (Auth Loss Guard) and RULE-013 (Daily Realized Profit Target)
with complete flows from SDK events through enforcement.

Complete Flows Tested:
1. Auth Loss Guard - Connection monitoring and alert generation
2. Auth Loss Guard - Authentication failure detection
3. Auth Loss Guard - Reconnection clears alerts
4. Daily Profit Target - Lockout when target reached
5. Daily Profit Target - Prevents new trades during lockout
6. Daily Profit Target - Reset clears lockout

This validates the monitoring and lockout pipeline works together.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta

# Risk Manager imports
from risk_manager.core.manager import RiskManager
from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.config import RiskConfig
from risk_manager.rules.auth_loss_guard import AuthLossGuardRule
from risk_manager.rules.daily_realized_profit import DailyRealizedProfitRule
from risk_manager.state.lockout_manager import LockoutManager
from risk_manager.state.pnl_tracker import PnLTracker
from risk_manager.state.database import Database


class MockAccount:
    """Mock SDK Account object."""

    def __init__(self, account_id="PRAC-V2-126244-84184528", name="150k Practice Account"):
        self.id = account_id
        self.name = name
        self.balance = 150000.0
        self.equity = 150000.0


class MockTradingSuite:
    """Mock SDK TradingSuite with disconnect simulation."""

    def __init__(
        self,
        should_fail_auth=False,
        should_disconnect=False,
        account_id="PRAC-V2-126244-84184528"
    ):
        self.event_bus = EventBus()
        self._connected = False
        self._should_fail_auth = should_fail_auth
        self._should_disconnect = should_disconnect
        self.account_info = MockAccount(account_id=account_id)
        self._symbols = {}

    async def connect(self):
        """Simulate SDK connection."""
        if self._should_fail_auth:
            # Publish AUTH_FAILED event
            await self.event_bus.publish(
                RiskEvent(
                    event_type=EventType.AUTH_FAILED,
                    data={
                        "account_id": self.account_info.id,
                        "reason": "Invalid credentials"
                    }
                )
            )
            raise ConnectionError("Authentication failed: Invalid credentials")

        if self._should_disconnect:
            # Simulate connection issues
            raise ConnectionError("Connection failed: Network error")

        self._connected = True

        # Simulate SDK_CONNECTED event
        await self.event_bus.publish(
            RiskEvent(
                event_type=EventType.SDK_CONNECTED,
                data={
                    "account_id": self.account_info.id,
                    "account_name": self.account_info.name
                }
            )
        )

    async def disconnect(self):
        """Simulate SDK disconnection."""
        if self._connected:
            self._connected = False

            # Simulate SDK_DISCONNECTED event
            await self.event_bus.publish(
                RiskEvent(
                    event_type=EventType.SDK_DISCONNECTED,
                    data={
                        "account_id": self.account_info.id,
                        "reason": "Connection lost"
                    }
                )
            )

    async def simulate_disconnect(self):
        """Force disconnect (simulate network loss)."""
        await self.disconnect()

    def __getitem__(self, symbol):
        """Return mock instrument context."""
        if symbol not in self._symbols:
            context = Mock()
            context.positions = Mock()
            context.positions.get_all_positions = AsyncMock(return_value=[])
            context.positions.close_all_positions = AsyncMock()
            context.instrument_info = Mock()
            context.instrument_info.name = symbol
            context.instrument_info.id = f"CON.F.US.{symbol}.Z25"
            self._symbols[symbol] = context
        return self._symbols[symbol]

    async def on(self, event_type, handler):
        """Subscribe to event."""
        self.event_bus.subscribe(event_type, handler)

    @property
    def is_connected(self):
        """Mock connection status."""
        return self._connected


@pytest.mark.e2e
class TestAuthLossGuardE2E:
    """End-to-end tests for RULE-010 (Auth Loss Guard)."""

    @pytest.fixture
    def mock_sdk_suite(self):
        """Create mock SDK suite with connection capability."""
        return MockTradingSuite()

    @pytest.fixture
    def mock_sdk_suite_fail_auth(self):
        """Create mock SDK suite that fails authentication."""
        return MockTradingSuite(should_fail_auth=True)

    @pytest.fixture
    async def auth_loss_rule(self):
        """Create auth loss guard rule for testing."""
        rule = AuthLossGuardRule(
            alert_on_disconnect=True,
            alert_on_auth_failure=True,
            log_level="WARNING"
        )
        return rule

    @pytest.fixture
    async def mock_engine(self):
        """Create mock risk engine."""
        engine = Mock()
        engine.event_bus = EventBus()
        return engine

    # ========================================================================
    # Test 1: SDK Disconnect Alert
    # ========================================================================

    @pytest.mark.asyncio
    async def test_auth_loss_guard_disconnect_alert(
        self,
        mock_sdk_suite,
        auth_loss_rule,
        mock_engine
    ):
        """Test alert generation when SDK connection is lost.

        Flow:
        1. System connected normally
        2. SDK disconnects (simulate network loss)
        3. SDK_DISCONNECTED event fired
        4. RULE-010 detects disconnect
        5. Alert generated (no enforcement)
        6. Alert published via RULE_VIOLATED event
        """
        # Track events
        alerts_received = []

        async def track_alert(event):
            if event.event_type == EventType.RULE_VIOLATED:
                alerts_received.append(event)

        mock_engine.event_bus.subscribe(EventType.RULE_VIOLATED, track_alert)

        # Given: System connected and running
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)

        assert mock_sdk_suite.is_connected is True

        # When: SDK disconnects (simulating network issue)
        await mock_sdk_suite.simulate_disconnect()
        await asyncio.sleep(0.1)

        # Create disconnect event
        disconnect_event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={
                "account_id": mock_sdk_suite.account_info.id,
                "reason": "Connection lost"
            }
        )

        # Evaluate rule
        alert = await auth_loss_rule.evaluate(disconnect_event, mock_engine)

        # Then: Alert is generated
        assert alert is not None
        assert alert["rule"] == "AuthLossGuardRule"
        assert alert["severity"] == "WARNING"
        assert alert["alert_type"] == "connection_lost"
        assert alert["account_id"] == mock_sdk_suite.account_info.id
        assert alert["action"] == "alert_only"  # NO enforcement!

        # And: Connection state tracked
        assert auth_loss_rule.get_connection_status(
            mock_sdk_suite.account_info.id
        ) is False

        # And: Last alert time recorded
        last_alert_time = auth_loss_rule.get_last_alert_time(
            mock_sdk_suite.account_info.id
        )
        assert last_alert_time is not None
        assert isinstance(last_alert_time, datetime)

    # ========================================================================
    # Test 2: Authentication Failure Alert
    # ========================================================================

    @pytest.mark.asyncio
    async def test_auth_loss_guard_auth_failure_alert(
        self,
        mock_sdk_suite_fail_auth,
        auth_loss_rule,
        mock_engine
    ):
        """Test alert generation when authentication fails.

        Flow:
        1. System attempts to connect
        2. Authentication fails (invalid credentials)
        3. AUTH_FAILED event fired
        4. RULE-010 detects auth failure
        5. Alert generated with ERROR severity
        6. No enforcement actions (just alert)
        """
        # Track auth failure
        auth_failed = False
        error_message = None

        # When: System attempts to connect with invalid credentials
        try:
            await mock_sdk_suite_fail_auth.connect()
        except ConnectionError as e:
            auth_failed = True
            error_message = str(e)

        await asyncio.sleep(0.1)

        # Then: Connection fails
        assert auth_failed is True
        assert "Authentication failed" in error_message

        # Create auth failed event
        auth_failed_event = RiskEvent(
            event_type=EventType.AUTH_FAILED,
            data={
                "account_id": mock_sdk_suite_fail_auth.account_info.id,
                "reason": "Invalid credentials"
            }
        )

        # Evaluate rule
        alert = await auth_loss_rule.evaluate(auth_failed_event, mock_engine)

        # Then: Alert is generated with ERROR severity
        assert alert is not None
        assert alert["rule"] == "AuthLossGuardRule"
        assert alert["severity"] == "ERROR"
        assert alert["alert_type"] == "auth_failed"
        assert alert["account_id"] == mock_sdk_suite_fail_auth.account_info.id
        assert alert["action"] == "alert_only"  # NO enforcement!
        assert alert["reason"] == "Invalid credentials"
        assert "Verify credentials" in alert["recommendation"]

    # ========================================================================
    # Test 3: Reconnection Clears Alert
    # ========================================================================

    @pytest.mark.asyncio
    async def test_auth_loss_guard_reconnect_clears_alert(
        self,
        mock_sdk_suite,
        auth_loss_rule,
        mock_engine
    ):
        """Test reconnection clears alert state.

        Flow:
        1. System connected
        2. SDK disconnects → Alert triggered
        3. SDK reconnects → Alert cleared
        4. Connection status updated to connected
        """
        # Given: System connected
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)

        # When: SDK disconnects
        await mock_sdk_suite.simulate_disconnect()
        await asyncio.sleep(0.1)

        disconnect_event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={
                "account_id": mock_sdk_suite.account_info.id,
                "reason": "Connection lost"
            }
        )

        # Evaluate disconnect
        alert = await auth_loss_rule.evaluate(disconnect_event, mock_engine)
        assert alert is not None

        # Connection state should be False
        assert auth_loss_rule.get_connection_status(
            mock_sdk_suite.account_info.id
        ) is False

        # When: SDK reconnects
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)

        reconnect_event = RiskEvent(
            event_type=EventType.SDK_CONNECTED,
            data={
                "account_id": mock_sdk_suite.account_info.id,
                "account_name": mock_sdk_suite.account_info.name
            }
        )

        # Evaluate reconnection
        result = await auth_loss_rule.evaluate(reconnect_event, mock_engine)

        # Then: No alert generated (reconnection clears alert state)
        assert result is None

        # And: Connection state updated to True
        assert auth_loss_rule.get_connection_status(
            mock_sdk_suite.account_info.id
        ) is True


@pytest.mark.e2e
class TestDailyRealizedProfitE2E:
    """End-to-end tests for RULE-013 (Daily Realized Profit Target)."""

    @pytest.fixture
    async def database(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test_lockout.db"
        db = Database(str(db_path))
        return db

    @pytest.fixture
    async def lockout_manager(self, database):
        """Create lockout manager for testing."""
        manager = LockoutManager(database=database)
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.fixture
    async def pnl_tracker(self, database):
        """Create P&L tracker for testing."""
        tracker = PnLTracker(db=database)
        return tracker

    @pytest.fixture
    async def profit_rule(self, pnl_tracker, lockout_manager):
        """Create daily realized profit rule for testing."""
        rule = DailyRealizedProfitRule(
            target=1000.0,  # $1000 profit target
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_manager,
            action="flatten",
            reset_time="17:00",
            timezone_name="America/New_York"
        )
        return rule

    @pytest.fixture
    async def mock_engine(self, pnl_tracker, lockout_manager):
        """Create mock risk engine with real components."""
        engine = Mock()
        engine.event_bus = EventBus()
        engine.pnl_tracker = pnl_tracker
        engine.lockout_manager = lockout_manager
        return engine

    # ========================================================================
    # Test 4: Daily Profit Target Lockout
    # ========================================================================

    @pytest.mark.asyncio
    async def test_daily_profit_target_lockout(
        self,
        profit_rule,
        pnl_tracker,
        lockout_manager,
        mock_engine
    ):
        """Test hard lockout when daily profit target is reached.

        Flow:
        1. Account has realized $1100 profit
        2. POSITION_CLOSED event with profit
        3. RULE-013 evaluates P&L
        4. Violation detected (P&L >= target)
        5. Hard lockout set until reset time
        6. Account locked from trading
        """
        account_id = "PRAC-V2-126244-84184528"

        # Given: Account has realized $500 profit from previous trade
        pnl_tracker.add_trade_pnl(account_id, 500.0)

        # When: POSITION_CLOSED event fired with $600 profit (total = $1100, exceeds target)
        position_closed_event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": account_id,
                "symbol": "MNQ",
                "profitAndLoss": 600.0,
                "side": "long",
                "quantity": 2
            }
        )

        # Evaluate rule (rule will add $600 to tracker: 500 + 600 = 1100)
        violation = await profit_rule.evaluate(position_closed_event, mock_engine)

        # Then: Violation detected (P&L now = $1100, exceeds $1000 target)
        assert violation is not None
        assert violation["rule"] == "DailyRealizedProfitRule"
        assert violation["current_profit"] == 1100.0  # 500 (previous) + 600 (this event)
        assert violation["target"] == 1000.0
        assert violation["lockout_required"] is True
        assert "Good job" in violation["message"]

        # When: Enforce lockout
        await profit_rule.enforce(account_id, violation, mock_engine)

        # Then: Account is locked out
        assert lockout_manager.is_locked_out(account_id) is True

        # And: Lockout has expiry time (next reset)
        lockout_info = lockout_manager.get_lockout_info(account_id)
        assert lockout_info is not None
        assert "until" in lockout_info
        assert lockout_info["until"] is not None

    # ========================================================================
    # Test 5: Daily Profit Prevents New Trades
    # ========================================================================

    @pytest.mark.asyncio
    async def test_daily_profit_prevents_new_trades(
        self,
        profit_rule,
        pnl_tracker,
        lockout_manager,
        mock_engine
    ):
        """Test that lockout prevents new trading activity.

        Flow:
        1. Account locked due to profit target reached
        2. Attempt to evaluate new trading event
        3. Rule skips evaluation (account locked)
        4. No additional violations generated
        5. Lockout remains in effect
        """
        account_id = "PRAC-V2-126244-84184528"

        # Given: Account has reached profit target and is locked
        pnl_tracker.add_trade_pnl(account_id, 1100.0)
        lockout_manager.set_lockout(
            account_id=account_id,
            reason="Daily profit target reached",
            until=datetime.now(timezone.utc) + timedelta(hours=2)
        )

        # Verify account is locked
        assert lockout_manager.is_locked_out(account_id) is True

        # When: New trade attempt (POSITION_OPENED event)
        new_trade_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": account_id,
                "symbol": "MNQ",
                "side": "long",
                "quantity": 1,
                "profitAndLoss": None  # Opening position
            }
        )

        # Evaluate rule
        violation = await profit_rule.evaluate(new_trade_event, mock_engine)

        # Then: No violation generated (rule skips locked accounts)
        assert violation is None

        # And: Account remains locked
        assert lockout_manager.is_locked_out(account_id) is True

    # ========================================================================
    # Test 6: Daily Profit Reset Clears Lockout
    # ========================================================================

    @pytest.mark.asyncio
    async def test_daily_profit_reset_clears_lockout(
        self,
        profit_rule,
        pnl_tracker,
        lockout_manager,
        mock_engine
    ):
        """Test that daily reset clears profit lockout.

        Flow:
        1. Account locked due to profit target
        2. Reset time arrives
        3. Lockout cleared (manual or via scheduler)
        4. P&L reset to $0
        5. Account can trade again
        """
        account_id = "PRAC-V2-126244-84184528"

        # Given: Account locked due to profit target
        pnl_tracker.add_trade_pnl(account_id, 1100.0)

        # Set lockout with expiry time in the future initially
        future_time = datetime.now(timezone.utc) + timedelta(seconds=10)
        lockout_manager.set_lockout(
            account_id=account_id,
            reason="Daily profit target reached",
            until=future_time
        )

        # Initially locked (expiry in future)
        assert lockout_manager.is_locked_out(account_id) is True

        # Simulate reset time by updating lockout to past time
        past_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        lockout_manager.set_lockout(
            account_id=account_id,
            reason="Daily profit target reached",
            until=past_time
        )

        # When: Check for expired lockouts (simulates background task)
        lockout_manager.check_expired_lockouts()

        # Then: Lockout cleared (because expiry time is now in the past)
        assert lockout_manager.is_locked_out(account_id) is False

        # When: P&L reset manually (simulating daily reset)
        pnl_tracker.reset_daily_pnl(account_id)

        # Then: P&L is reset to zero
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == 0.0

        # And: New trades allowed
        new_trade_event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": account_id,
                "symbol": "MNQ",
                "profitAndLoss": 50.0,
                "side": "long",
                "quantity": 1
            }
        )

        # Evaluate rule - should NOT violate (P&L below target)
        # Rule will add $50 to tracker automatically
        violation = await profit_rule.evaluate(new_trade_event, mock_engine)
        assert violation is None

        # Verify new P&L tracked correctly (0 + 50 = 50)
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)
        assert daily_pnl == 50.0

    # ========================================================================
    # Test 7: Multiple Accounts Independent Lockouts
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multiple_accounts_independent_lockouts(
        self,
        profit_rule,
        pnl_tracker,
        lockout_manager,
        mock_engine
    ):
        """Test that lockouts are tracked independently per account.

        Flow:
        1. Account A reaches profit target → Locked
        2. Account B still under target → Not locked
        3. Account A cannot trade
        4. Account B can trade normally
        """
        account_a = "PRAC-V2-111111-11111111"
        account_b = "PRAC-V2-222222-22222222"

        # Given: Account A makes $1100 trade (reaches profit target)
        position_closed_a = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": account_a,
                "symbol": "MNQ",
                "profitAndLoss": 1100.0,
                "side": "long",
                "quantity": 2
            }
        )

        # Evaluate rule (will add $1100 to tracker automatically)
        violation_a = await profit_rule.evaluate(position_closed_a, mock_engine)
        assert violation_a is not None

        await profit_rule.enforce(account_a, violation_a, mock_engine)

        # And: Account B has $500 from previous trade (under target)
        pnl_tracker.add_trade_pnl(account_b, 500.0)

        # Then: Account A is locked
        assert lockout_manager.is_locked_out(account_a) is True

        # And: Account B is NOT locked
        assert lockout_manager.is_locked_out(account_b) is False

        # When: Account B makes $200 trade (total = $700, still under target)
        position_closed_b = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "account_id": account_b,
                "symbol": "ES",
                "profitAndLoss": 200.0,
                "side": "short",
                "quantity": 1
            }
        )

        # Evaluate rule (will add $200 to tracker: 500 + 200 = 700)
        violation_b = await profit_rule.evaluate(position_closed_b, mock_engine)

        # Then: No violation (still under $1000 target)
        assert violation_b is None

        # And: Account B remains unlocked
        assert lockout_manager.is_locked_out(account_b) is False

        # Verify P&L tracked separately per account
        assert pnl_tracker.get_daily_pnl(account_a) == 1100.0  # Single $1100 trade
        assert pnl_tracker.get_daily_pnl(account_b) == 700.0   # $500 + $200

    # ========================================================================
    # Test 8: Profit Rule Ignores Half-Turn Trades
    # ========================================================================

    @pytest.mark.asyncio
    async def test_profit_rule_ignores_half_turn_trades(
        self,
        profit_rule,
        pnl_tracker,
        lockout_manager,
        mock_engine
    ):
        """Test that rule ignores opening positions (half-turn trades).

        Flow:
        1. Account opens position (profitAndLoss=None)
        2. POSITION_OPENED event fired
        3. Rule evaluates but ignores (no realized P&L)
        4. No violation generated
        5. Lockout NOT triggered
        """
        account_id = "PRAC-V2-126244-84184528"

        # Given: Account has $900 profit (below target)
        pnl_tracker.add_trade_pnl(account_id, 900.0)

        # When: Position opened (half-turn, no realized P&L)
        position_opened_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": account_id,
                "symbol": "MNQ",
                "side": "long",
                "quantity": 2,
                "profitAndLoss": None  # Opening position
            }
        )

        # Evaluate rule
        violation = await profit_rule.evaluate(position_opened_event, mock_engine)

        # Then: No violation (half-turn trades ignored)
        assert violation is None

        # And: Account not locked
        assert lockout_manager.is_locked_out(account_id) is False

        # And: P&L unchanged
        assert pnl_tracker.get_daily_pnl(account_id) == 900.0
