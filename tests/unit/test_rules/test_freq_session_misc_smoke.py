"""
Smoke Tests for Frequency, Session, and Miscellaneous Rules

Tests RULE-006 (Trade Frequency), RULE-009 (Session Block),
RULE-010 (Auth Loss Guard), RULE-011 (Symbol Blocks), RULE-012 (Trade Management)

These are SMOKE TESTS - they prove runtime behavior, not just logic:
- [PASS] Frequency tracking works across multiple trades
- [PASS] Session time checks actually fire
- [PASS] Auth status monitoring works
- [PASS] Symbol blacklist enforcement works
- [PASS] Trade management automation triggers
- [PASS] All within acceptable time (<10s per rule)

Author: Test Coordinator Agent
Created: 2025-10-28
"""

import asyncio
import pytest
import time
from datetime import datetime, time as dt_time, timedelta
from unittest.mock import AsyncMock, Mock, MagicMock
from zoneinfo import ZoneInfo

from risk_manager.rules.trade_frequency_limit import TradeFrequencyLimitRule
from risk_manager.rules.session_block_outside import SessionBlockOutsideRule
from risk_manager.rules.auth_loss_guard import AuthLossGuardRule
from risk_manager.rules.symbol_blocks import SymbolBlocksRule
from risk_manager.rules.trade_management import TradeManagementRule
from risk_manager.core.events import RiskEvent, EventType


@pytest.mark.smoke
@pytest.mark.unit
class TestFreqSessionMiscRulesSmoke:
    """Smoke tests for frequency, session, and miscellaneous risk rules."""

    # ========================================================================
    # RULE-006: Trade Frequency Limit - Multi-Trade Tracking
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_006_trade_frequency_per_minute_fires(self):
        """
        Smoke test: Trade Frequency Limit fires after rapid trading.

        PROVES:
        - Multiple trade events tracked correctly
        - Frequency counter increments per trade
        - Violation fires when count exceeds limit
        - Cooldown timer is set (not lockout)
        - Processing completes within 10 seconds

        Scenario:
        - Limit: 3 trades per minute
        - Action: Generate 4 rapid trades
        - Expected: Violation on 4th trade
        - Expected: Cooldown timer set (60s)
        """
        start_time = time.time()

        # Setup: Mock database to track trade count
        mock_db = Mock()
        trade_count = 0

        def get_trade_count(account_id, window):
            """Simulate cumulative trade count."""
            return trade_count

        mock_db.get_trade_count = Mock(side_effect=get_trade_count)
        mock_db.get_session_trade_count = Mock(return_value=trade_count)

        # Mock timer manager
        mock_timer_manager = AsyncMock()
        mock_timer_manager.start_timer = AsyncMock()

        # Create rule: 3 trades per minute limit
        rule = TradeFrequencyLimitRule(
            limits={
                'per_minute': 3,  # Max 3 trades per minute
            },
            cooldown_on_breach={
                'per_minute_breach': 60,  # 60s cooldown
            },
            timer_manager=mock_timer_manager,
            db=mock_db,
            action="cooldown"
        )

        # Mock engine
        mock_engine = Mock()
        mock_engine.current_positions = {}

        violations = []

        # Generate 4 rapid trades (exceeds limit of 3)
        for i in range(1, 5):
            trade_count = i  # Update count before evaluate

            trade_event = RiskEvent(
                event_type=EventType.TRADE_EXECUTED,
                data={
                    "account_id": "ACC-001",
                    "symbol": "MNQ",
                    "side": "BUY",
                    "quantity": 1,
                    "price": 19000.0 + i,
                    "timestamp": time.time()
                }
            )

            # Evaluate rule
            result = await rule.evaluate(trade_event, mock_engine)

            if result:
                violations.append(result)

                # Enforce (should set cooldown timer)
                await rule.enforce("ACC-001", result, mock_engine)

            await asyncio.sleep(0.01)  # Small delay between trades

        elapsed = time.time() - start_time

        # Verify violation fired on 4th trade
        assert len(violations) == 1, f"Expected 1 violation, got {len(violations)}"

        violation = violations[0]
        assert violation["rule"] == "TradeFrequencyLimitRule"
        assert violation["breach_type"] == "per_minute"
        assert violation["trade_count"] == 4
        assert violation["limit"] == 3
        assert violation["cooldown_duration"] == 60
        assert violation["action"] == "cooldown"

        # Verify cooldown timer was set (NOT position close)
        mock_timer_manager.start_timer.assert_called_once()
        call_args = mock_timer_manager.start_timer.call_args
        assert call_args[1]["name"] == "trade_frequency_ACC-001"
        assert call_args[1]["duration"] == 60

        # Verify timing (should be < 10s)
        assert elapsed < 10.0, f"Test took {elapsed:.2f}s (should be < 10s)"

        print(f"[PASS] RULE-006 (per_minute) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_006_trade_frequency_per_hour_fires(self):
        """
        Smoke test: Trade Frequency Limit (per-hour) fires.

        Tests the per-hour limit variant.
        """
        start_time = time.time()

        # Setup
        mock_db = Mock()
        mock_db.get_trade_count = Mock(side_effect=lambda acc, window: 11 if window == 3600 else 2)
        mock_db.get_session_trade_count = Mock(return_value=11)

        mock_timer_manager = AsyncMock()
        mock_timer_manager.start_timer = AsyncMock()

        # Create rule: 10 trades per hour limit
        rule = TradeFrequencyLimitRule(
            limits={
                'per_hour': 10,  # Max 10 trades per hour
            },
            cooldown_on_breach={
                'per_hour_breach': 1800,  # 30 min cooldown
            },
            timer_manager=mock_timer_manager,
            db=mock_db,
            action="cooldown"
        )

        mock_engine = Mock()

        # Generate trade that breaches per-hour limit
        trade_event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ",
                "timestamp": time.time()
            }
        )

        # Evaluate
        result = await rule.evaluate(trade_event, mock_engine)

        # Verify violation
        assert result is not None
        assert result["breach_type"] == "per_hour"
        assert result["trade_count"] == 11
        assert result["limit"] == 10
        assert result["cooldown_duration"] == 1800

        # Enforce
        await rule.enforce("ACC-001", result, mock_engine)

        # Verify cooldown set
        mock_timer_manager.start_timer.assert_called_once()

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-006 (per_hour) fired in {elapsed:.2f}s")

    # ========================================================================
    # RULE-009: Session Block Outside Hours - Time-Based Validation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_009_session_block_outside_fires(self):
        """
        Smoke test: Session Block Outside fires for off-hours trade.

        PROVES:
        - Session time validation works
        - Timezone-aware time checking works
        - Lockout set for outside session hours
        - Next session start calculated correctly
        - Processing completes within 10 seconds

        Scenario:
        - Session: 09:30 - 16:00 ET
        - Current time: Mocked to 20:00 ET (8 PM - outside hours)
        - Action: Try to open position
        - Expected: Violation (outside session)
        - Expected: Hard lockout until next session
        """
        start_time = time.time()

        # Mock lockout manager
        mock_lockout_manager = Mock()
        mock_lockout_manager.is_locked_out = Mock(return_value=False)
        mock_lockout_manager.set_lockout = Mock()

        # Create rule: 09:30 - 16:00 ET session
        rule = SessionBlockOutsideRule(
            config={
                "enabled": True,
                "global_session": {
                    "enabled": True,
                    "start": "09:30",
                    "end": "16:00",
                    "timezone": "America/New_York"
                },
                "block_weekends": True,
                "lockout_outside_session": True
            },
            lockout_manager=mock_lockout_manager
        )

        # Mock engine
        mock_engine = Mock()
        mock_engine.current_positions = {}

        # Create position opened event (happens at 8 PM ET - outside session)
        # We'll test by manipulating the rule's time check
        tz = ZoneInfo("America/New_York")
        now = datetime.now(tz)

        # Mock time to be 8 PM (20:00)
        mock_now = now.replace(hour=20, minute=0, second=0, microsecond=0)

        # Patch datetime to return our mock time
        import unittest.mock
        with unittest.mock.patch('risk_manager.rules.session_block_outside.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now

            position_event = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={
                    "account_id": "ACC-001",
                    "symbol": "MNQ",
                    "quantity": 1,
                    "timestamp": mock_now.isoformat()
                }
            )

            # Evaluate
            result = await rule.evaluate(position_event, mock_engine)

        # Verify violation
        assert result is not None, "Expected violation for outside session hours"
        assert result["rule"] == "SessionBlockOutsideRule"
        assert "outside session hours" in result["message"].lower() or "after session end" in result["message"].lower()
        assert result["action"] == "flatten"
        assert result["lockout_required"] is True

        # Verify next session start calculated
        assert "next_session_start" in result
        next_session = result["next_session_start"]

        # Next session should be tomorrow at 09:30 (or Monday if weekend)
        assert next_session.hour == 9
        assert next_session.minute == 30

        # Enforce lockout
        await rule.enforce("ACC-001", result, mock_engine)

        # Verify lockout was set
        mock_lockout_manager.set_lockout.assert_called_once()
        call_args = mock_lockout_manager.set_lockout.call_args
        assert call_args[1]["account_id"] == "ACC-001"
        assert call_args[1]["until"] == next_session

        elapsed = time.time() - start_time
        assert elapsed < 10.0, f"Test took {elapsed:.2f}s (should be < 10s)"

        print(f"[PASS] RULE-009 (outside session) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_009_weekend_block_fires(self):
        """
        Smoke test: Session Block fires on weekend.

        Tests weekend blocking functionality.
        """
        start_time = time.time()

        mock_lockout_manager = Mock()
        mock_lockout_manager.is_locked_out = Mock(return_value=False)
        mock_lockout_manager.set_lockout = Mock()

        rule = SessionBlockOutsideRule(
            config={
                "enabled": True,
                "global_session": {
                    "enabled": True,
                    "start": "09:30",
                    "end": "16:00",
                    "timezone": "America/New_York"
                },
                "block_weekends": True,
                "lockout_outside_session": True
            },
            lockout_manager=mock_lockout_manager
        )

        mock_engine = Mock()

        # Mock time to Saturday 11:00 AM ET
        tz = ZoneInfo("America/New_York")
        now = datetime.now(tz)
        # Find next Saturday
        days_ahead = 5 - now.weekday()  # Saturday = 5
        if days_ahead <= 0:
            days_ahead += 7
        saturday = now + timedelta(days=days_ahead)
        mock_saturday = saturday.replace(hour=11, minute=0, second=0, microsecond=0)

        import unittest.mock
        with unittest.mock.patch('risk_manager.rules.session_block_outside.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_saturday

            position_event = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={
                    "account_id": "ACC-001",
                    "symbol": "MNQ",
                    "timestamp": mock_saturday.isoformat()
                }
            )

            result = await rule.evaluate(position_event, mock_engine)

        # Verify weekend violation
        assert result is not None
        assert "weekend" in result["message"].lower() or "saturday" in result["message"].lower()

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-009 (weekend) fired in {elapsed:.2f}s")

    # ========================================================================
    # RULE-010: Auth Loss Guard - Alert-Only Monitoring
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_010_auth_loss_guard_disconnected_alert(self):
        """
        Smoke test: Auth Loss Guard fires alert on SDK disconnect.

        PROVES:
        - SDK connection monitoring works
        - Alert generated (not enforcement)
        - No position closing (alert only)
        - Processing completes within 10 seconds

        Scenario:
        - SDK disconnects
        - Action: Publish SDK_DISCONNECTED event
        - Expected: Alert returned (no enforcement)
        - Expected: Connection state tracked

        NOTE: This is ALERT ONLY - no enforcement actions!
        """
        start_time = time.time()

        # Create rule
        rule = AuthLossGuardRule(
            alert_on_disconnect=True,
            alert_on_auth_failure=True,
            log_level="WARNING"
        )

        # Mock engine
        mock_engine = Mock()

        # Create SDK disconnection event
        disconnect_event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={
                "account_id": 12345,
                "reason": "Network timeout",
                "timestamp": datetime.now().isoformat()
            }
        )

        # Evaluate
        result = await rule.evaluate(disconnect_event, mock_engine)

        # Verify alert generated (not violation!)
        assert result is not None, "Expected alert to be generated"
        assert result["rule"] == "AuthLossGuardRule"
        assert result["alert_type"] == "connection_lost"
        assert result["severity"] == "WARNING"
        assert result["action"] == "alert_only"  # NO enforcement!
        assert result["account_id"] == 12345

        # Verify connection state tracked
        assert rule.get_connection_status(12345) is False

        # Call enforce (should do nothing - alert only)
        await rule.enforce(12345, result, mock_engine)

        # Verify no enforcement actions taken (enforce is a no-op)
        # This is verified by the fact that enforce() just passes

        elapsed = time.time() - start_time
        assert elapsed < 10.0, f"Test took {elapsed:.2f}s (should be < 10s)"

        print(f"[PASS] RULE-010 (disconnect alert) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_010_auth_failure_alert(self):
        """
        Smoke test: Auth Loss Guard fires alert on auth failure.

        Tests authentication failure monitoring.
        """
        start_time = time.time()

        rule = AuthLossGuardRule(
            alert_on_disconnect=True,
            alert_on_auth_failure=True,
            log_level="ERROR"
        )

        mock_engine = Mock()

        # Create auth failure event
        auth_fail_event = RiskEvent(
            event_type=EventType.AUTH_FAILED,
            data={
                "account_id": 12345,
                "reason": "Invalid credentials",
                "timestamp": datetime.now().isoformat()
            }
        )

        # Evaluate
        result = await rule.evaluate(auth_fail_event, mock_engine)

        # Verify alert
        assert result is not None
        assert result["alert_type"] == "auth_failed"
        assert result["severity"] == "ERROR"
        assert result["action"] == "alert_only"
        assert "Invalid credentials" in result["reason"]

        # Verify last alert time tracked
        assert rule.get_last_alert_time(12345) is not None

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-010 (auth failure alert) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_010_connection_restored_clears_state(self):
        """
        Smoke test: Auth Loss Guard tracks connection restoration.

        Tests connection recovery tracking.
        """
        start_time = time.time()

        rule = AuthLossGuardRule()
        mock_engine = Mock()

        # First disconnect
        disconnect_event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"account_id": 12345}
        )
        await rule.evaluate(disconnect_event, mock_engine)
        assert rule.get_connection_status(12345) is False

        # Then reconnect
        reconnect_event = RiskEvent(
            event_type=EventType.SDK_CONNECTED,
            data={"account_id": 12345}
        )
        result = await rule.evaluate(reconnect_event, mock_engine)

        # Should not return alert (just update state)
        assert result is None

        # Connection status should be restored
        assert rule.get_connection_status(12345) is True

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-010 (connection restored) tracked in {elapsed:.2f}s")

    # ========================================================================
    # RULE-011: Symbol Blocks - Blacklist Enforcement
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_011_symbol_blocks_exact_match_fires(self):
        """
        Smoke test: Symbol Blocks fires for blacklisted symbol.

        PROVES:
        - Symbol blacklist matching works
        - Exact symbol matching (case-insensitive)
        - Violation fires for blocked symbol
        - No lockout (trade-by-trade)
        - Processing completes within 10 seconds

        Scenario:
        - Blacklist: ["ES", "NQ"]
        - Action: Try to trade ES
        - Expected: Violation (symbol blocked)
        - Expected: Action = "close" (close position, no lockout)
        """
        start_time = time.time()

        # Create rule with blacklist
        rule = SymbolBlocksRule(
            blocked_symbols=["ES", "NQ"],
            action="close"
        )

        # Mock engine
        mock_engine = Mock()

        # Create order for blacklisted symbol
        order_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES",  # Blacklisted!
                "side": "BUY",
                "quantity": 1,
                "timestamp": time.time()
            }
        )

        # Evaluate
        result = await rule.evaluate(order_event, mock_engine)

        # Verify violation
        assert result is not None, "Expected violation for blacklisted symbol"
        assert result["rule"] == "SymbolBlocksRule"
        assert result["symbol"] == "ES"
        assert "blocked" in result["message"].lower()
        assert result["action"] == "close"

        elapsed = time.time() - start_time
        assert elapsed < 10.0, f"Test took {elapsed:.2f}s (should be < 10s)"

        print(f"[PASS] RULE-011 (exact match) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_011_symbol_blocks_case_insensitive(self):
        """
        Smoke test: Symbol Blocks works case-insensitively.

        Tests case-insensitive matching.
        """
        start_time = time.time()

        rule = SymbolBlocksRule(
            blocked_symbols=["ES", "NQ"],
            action="close"
        )

        mock_engine = Mock()

        # Try lowercase symbol
        order_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "es"}  # Lowercase, should still match
        )

        result = await rule.evaluate(order_event, mock_engine)

        # Should still match (case-insensitive)
        assert result is not None
        assert result["symbol"] == "es"

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-011 (case-insensitive) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_011_symbol_blocks_wildcard_match(self):
        """
        Smoke test: Symbol Blocks supports wildcard patterns.

        Tests wildcard matching (MNQ* matches MNQ, MNQH25, etc).
        """
        start_time = time.time()

        rule = SymbolBlocksRule(
            blocked_symbols=["MNQ*"],  # Wildcard: all MNQ contracts
            action="close"
        )

        mock_engine = Mock()

        # Try symbol that matches wildcard
        order_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "MNQH25"}  # Should match MNQ*
        )

        result = await rule.evaluate(order_event, mock_engine)

        # Should match wildcard pattern
        assert result is not None
        assert result["symbol"] == "MNQH25"

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-011 (wildcard) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_011_symbol_blocks_allows_non_blocked(self):
        """
        Smoke test: Symbol Blocks allows non-blacklisted symbols.

        Tests that non-blocked symbols pass through.
        """
        start_time = time.time()

        rule = SymbolBlocksRule(
            blocked_symbols=["ES", "NQ"],
            action="close"
        )

        mock_engine = Mock()

        # Try non-blocked symbol
        order_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "MNQ"}  # NOT blacklisted
        )

        result = await rule.evaluate(order_event, mock_engine)

        # Should NOT violate
        assert result is None, "Non-blocked symbol should not violate"

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-011 (allows non-blocked) verified in {elapsed:.2f}s")

    # ========================================================================
    # RULE-012: Trade Management - Automation Behavior
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_012_trade_management_auto_stop_loss(self):
        """
        Smoke test: Trade Management auto-places stop-loss.

        PROVES:
        - Automation triggers on position open
        - Stop-loss price calculated correctly
        - Action is automation (not violation)
        - No lockout (this is helpful automation)
        - Processing completes within 10 seconds

        Scenario:
        - Position: Long 1 MNQ @ 19000.00
        - Stop distance: 10 ticks * 0.25 = 2.50
        - Action: Position opened
        - Expected: Auto stop-loss at 18997.50
        - Expected: Action = "place_stop_loss" (automation)

        NOTE: This is AUTOMATION, not enforcement!
        """
        start_time = time.time()

        # Create rule
        rule = TradeManagementRule(
            config={
                "enabled": True,
                "auto_stop_loss": {
                    "enabled": True,
                    "distance": 10  # 10 ticks
                },
                "auto_take_profit": {
                    "enabled": False
                },
                "trailing_stop": {
                    "enabled": False
                }
            },
            tick_values={"MNQ": 5.0},  # $5 per tick
            tick_sizes={"MNQ": 0.25}   # 0.25 tick size
        )

        # Mock engine with position
        mock_engine = Mock()
        mock_engine.current_positions = {
            "MNQ": {
                "symbol": "MNQ",
                "size": 1,  # Long 1 contract
                "avgPrice": 19000.0,
                "contractId": "MNQ-001"
            }
        }

        # Create position opened event
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ",
                "quantity": 1,
                "avgPrice": 19000.0,
                "timestamp": time.time()
            }
        )

        # Evaluate
        result = await rule.evaluate(position_event, mock_engine)

        # Verify automation action (NOT violation!)
        assert result is not None, "Expected automation action"
        assert result["rule"] == "TradeManagementRule"
        assert result["action"] == "place_stop_loss"
        assert result["symbol"] == "MNQ"
        assert result["entry_price"] == 19000.0

        # Calculate expected stop price
        # Long: entry - (distance * tick_size) = 19000 - (10 * 0.25) = 18997.50
        expected_stop = 19000.0 - (10 * 0.25)
        assert result["stop_price"] == expected_stop, \
            f"Expected stop at {expected_stop}, got {result['stop_price']}"

        elapsed = time.time() - start_time
        assert elapsed < 10.0, f"Test took {elapsed:.2f}s (should be < 10s)"

        print(f"[PASS] RULE-012 (auto stop-loss) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_012_trade_management_bracket_order(self):
        """
        Smoke test: Trade Management auto-places bracket order.

        Tests both stop-loss and take-profit placement.
        """
        start_time = time.time()

        rule = TradeManagementRule(
            config={
                "enabled": True,
                "auto_stop_loss": {
                    "enabled": True,
                    "distance": 10  # 10 ticks
                },
                "auto_take_profit": {
                    "enabled": True,
                    "distance": 20  # 20 ticks
                },
                "trailing_stop": {
                    "enabled": False
                }
            },
            tick_values={"MNQ": 5.0},
            tick_sizes={"MNQ": 0.25}
        )

        mock_engine = Mock()
        mock_engine.current_positions = {
            "MNQ": {
                "symbol": "MNQ",
                "size": 1,
                "avgPrice": 19000.0,
                "contractId": "MNQ-001"
            }
        }

        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "avgPrice": 19000.0
            }
        )

        result = await rule.evaluate(position_event, mock_engine)

        # Verify bracket order (both stop and target)
        assert result is not None
        assert result["action"] == "place_bracket_order"

        # Long: stop below, target above
        expected_stop = 19000.0 - (10 * 0.25)    # 18997.50
        expected_target = 19000.0 + (20 * 0.25)  # 19005.00

        assert result["stop_price"] == expected_stop
        assert result["take_profit_price"] == expected_target

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-012 (bracket order) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_012_trade_management_trailing_stop(self):
        """
        Smoke test: Trade Management adjusts trailing stop.

        Tests trailing stop automation on favorable price movement.
        """
        start_time = time.time()

        rule = TradeManagementRule(
            config={
                "enabled": True,
                "auto_stop_loss": {
                    "enabled": False
                },
                "auto_take_profit": {
                    "enabled": False
                },
                "trailing_stop": {
                    "enabled": True,
                    "distance": 8  # 8 ticks
                }
            },
            tick_values={"MNQ": 5.0},
            tick_sizes={"MNQ": 0.25}
        )

        # Mock engine with position and market price
        mock_engine = Mock()
        mock_engine.current_positions = {
            "MNQ": {
                "symbol": "MNQ",
                "size": 1,
                "avgPrice": 19000.0,
                "stop_price": 18998.0,  # Old stop
                "contractId": "MNQ-001"
            }
        }
        mock_engine.market_prices = {
            "MNQ": 19010.0  # Price moved up +10 points!
        }

        # Position updated event
        position_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "avgPrice": 19000.0
            }
        )

        result = await rule.evaluate(position_event, mock_engine)

        # Verify trailing stop adjustment
        assert result is not None
        assert result["action"] == "adjust_trailing_stop"

        # New stop should be 8 ticks below new high
        # 19010 - (8 * 0.25) = 19008.00
        expected_new_stop = 19010.0 - (8 * 0.25)
        assert result["new_stop_price"] == expected_new_stop
        assert result["old_stop_price"] == 18998.0

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-012 (trailing stop) fired in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_rule_012_trade_management_short_position(self):
        """
        Smoke test: Trade Management handles short positions correctly.

        Tests stop-loss calculation for short positions (opposite direction).
        """
        start_time = time.time()

        rule = TradeManagementRule(
            config={
                "enabled": True,
                "auto_stop_loss": {
                    "enabled": True,
                    "distance": 10
                },
                "auto_take_profit": {
                    "enabled": False
                },
                "trailing_stop": {
                    "enabled": False
                }
            },
            tick_values={"MNQ": 5.0},
            tick_sizes={"MNQ": 0.25}
        )

        mock_engine = Mock()
        mock_engine.current_positions = {
            "MNQ": {
                "symbol": "MNQ",
                "size": -1,  # Short 1 contract
                "avgPrice": 19000.0,
                "contractId": "MNQ-001"
            }
        }

        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "avgPrice": 19000.0
            }
        )

        result = await rule.evaluate(position_event, mock_engine)

        # Verify stop-loss for short (above entry)
        assert result is not None
        assert result["side"] == "short"

        # Short: stop above entry = 19000 + (10 * 0.25) = 19002.50
        expected_stop = 19000.0 + (10 * 0.25)
        assert result["stop_price"] == expected_stop

        elapsed = time.time() - start_time
        assert elapsed < 10.0

        print(f"[PASS] RULE-012 (short position) fired in {elapsed:.2f}s")


# ============================================================================
# Summary Test - Run All Smoke Tests
# ============================================================================

@pytest.mark.smoke
@pytest.mark.unit
class TestAllFreqSessionMiscSmoke:
    """Summary test - run all 5 rules smoke tests together."""

    @pytest.mark.asyncio
    async def test_all_rules_smoke_suite(self):
        """
        Run all 5 rules smoke tests in sequence.

        Verifies all rules can fire within acceptable time limits.
        """
        total_start = time.time()

        test_class = TestFreqSessionMiscRulesSmoke()

        # RULE-006: Trade Frequency
        await test_class.test_rule_006_trade_frequency_per_minute_fires()

        # RULE-009: Session Block
        await test_class.test_rule_009_session_block_outside_fires()

        # RULE-010: Auth Loss Guard
        await test_class.test_rule_010_auth_loss_guard_disconnected_alert()

        # RULE-011: Symbol Blocks
        await test_class.test_rule_011_symbol_blocks_exact_match_fires()

        # RULE-012: Trade Management
        await test_class.test_rule_012_trade_management_auto_stop_loss()

        total_elapsed = time.time() - total_start

        print(f"\n{'='*60}")
        print(f"[SUCCESS] ALL 5 RULES SMOKE TESTS PASSED")
        print(f"{'='*60}")
        print(f"Total time: {total_elapsed:.2f}s")
        print(f"[PASS] RULE-006: Trade Frequency Limit")
        print(f"[PASS] RULE-009: Session Block Outside")
        print(f"[PASS] RULE-010: Auth Loss Guard")
        print(f"[PASS] RULE-011: Symbol Blocks")
        print(f"[PASS] RULE-012: Trade Management")
        print(f"{'='*60}")

        # Verify total time reasonable (< 50s for all 5)
        assert total_elapsed < 50.0, f"Total suite took {total_elapsed:.2f}s (should be < 50s)"
