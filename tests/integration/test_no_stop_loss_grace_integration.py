"""
Integration Tests for RULE-008: No Stop-Loss Grace

Tests the complete flow of the No Stop-Loss Grace rule with:
- Real TimerManager (asyncio timers, not mocked)
- Real event sequences (POSITION_OPENED → ORDER_PLACED → POSITION_CLOSED)
- Real timer callbacks and async execution
- Real EventBus for event distribution
- Integration with enforcement executor

Flow: Position Opens → Timer Starts → Stop-Loss Placed OR Timer Expires → Enforcement
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.rules.no_stop_loss_grace import NoStopLossGraceRule
from risk_manager.state.timer_manager import TimerManager


class TestNoStopLossGraceIntegration:
    """Integration tests for No Stop-Loss Grace rule with real timers."""

    @pytest.fixture
    async def timer_manager(self):
        """Create and start real TimerManager."""
        manager = TimerManager()
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.fixture
    def event_bus(self):
        """Create EventBus for event integration."""
        return EventBus()

    @pytest.fixture
    def mock_engine(self):
        """Create mock risk engine with enforcement executor."""
        engine = MagicMock()
        engine.enforcement_executor = MagicMock()
        engine.enforcement_executor.close_position = AsyncMock(
            return_value={"success": True}
        )
        return engine

    @pytest.fixture
    async def rule(self, timer_manager):
        """Create NoStopLossGraceRule with short grace period for testing."""
        return NoStopLossGraceRule(
            grace_period_seconds=2,  # Short period for fast tests
            enforcement="close_position",
            timer_manager=timer_manager,
            enabled=True,
        )

    # ========================================================================
    # Test 1: Grace Period Timer Flow (Real Async Timer)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_grace_period_timer_expires_and_closes_position(
        self, rule, mock_engine
    ):
        """
        Test complete grace period expiry flow with real async timer.

        Flow:
        1. Position opened → Timer starts (2s)
        2. Wait 2.5 seconds (real asyncio.sleep)
        3. Timer expires → Callback fires
        4. Position closed via enforcement
        """
        # Track if enforcement was called
        enforcement_called = {"called": False, "symbol": None, "contract_id": None}

        async def track_close(symbol, contract_id):
            enforcement_called["called"] = True
            enforcement_called["symbol"] = symbol
            enforcement_called["contract_id"] = contract_id
            return {"success": True}

        mock_engine.enforcement_executor.close_position = track_close

        # Step 1: Open position (starts grace period)
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.Z25",
                "size": 2,
                "average_price": 18500.0,
            },
        )

        violation = await rule.evaluate(position_event, mock_engine)

        # No immediate violation
        assert violation is None

        # Timer should be active
        timer_name = "no_stop_loss_grace_CON.F.US.MNQ.Z25"
        assert rule.timer_manager.has_timer(timer_name)

        # Verify initial remaining time
        remaining = rule.timer_manager.get_remaining_time(timer_name)
        assert 1 <= remaining <= 2  # Should be close to 2 seconds

        # Step 2: Wait for grace period to expire (real asyncio timer)
        # Timer loop checks every 1s, so we need: grace_period + 1s (loop cycle) + 0.5s (buffer)
        # = 2s + 1s + 0.5s = 3.5s to ensure timer is detected and removed
        await asyncio.sleep(3.5)

        # Step 3: Verify timer expired and callback executed
        assert not rule.timer_manager.has_timer(timer_name)
        assert enforcement_called["called"] is True
        assert enforcement_called["symbol"] == "MNQ"
        assert enforcement_called["contract_id"] == "CON.F.US.MNQ.Z25"

    # ========================================================================
    # Test 2: Stop-Loss Placed Within Grace (Cancel Timer)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_stop_loss_placed_cancels_timer_no_enforcement(
        self, rule, mock_engine
    ):
        """
        Test stop-loss placed within grace period cancels timer.

        Flow:
        1. Position opened → Timer starts
        2. Stop-loss placed (type=3, stopPrice present)
        3. Timer cancelled
        4. Wait past grace period
        5. Verify NO enforcement (grace satisfied)
        """
        # Track enforcement calls
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": True}

        mock_engine.enforcement_executor.close_position = track_close

        # Step 1: Open position
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "contract_id": "CON.F.US.ES.H25",
                "size": 1,
            },
        )

        await rule.evaluate(position_event, mock_engine)
        timer_name = "no_stop_loss_grace_CON.F.US.ES.H25"
        assert rule.timer_manager.has_timer(timer_name)

        # Step 2: Place stop-loss order after 0.5 seconds
        await asyncio.sleep(0.5)

        stop_order_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "contract_id": "CON.F.US.ES.H25",
                "symbol": "ES",
                "type": 3,  # STOP order
                "stopPrice": 5180.0,
                "size": 1,
            },
        )

        await rule.evaluate(stop_order_event, mock_engine)

        # Step 3: Timer should be cancelled
        assert not rule.timer_manager.has_timer(timer_name)

        # Step 4: Wait past original grace period
        await asyncio.sleep(2.0)

        # Step 5: Verify NO enforcement (stop-loss was placed)
        assert len(enforcement_calls) == 0

    # ========================================================================
    # Test 3: Multiple Positions with Independent Timers
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multiple_positions_independent_timers(self, rule, mock_engine):
        """
        Test multiple positions tracked with independent timers.

        Flow:
        1. Open ES position → Timer 1 starts
        2. Open MNQ position → Timer 2 starts
        3. Place stop on ES only
        4. Wait for grace period
        5. Verify only MNQ closed (ES had stop-loss)
        """
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": True}

        mock_engine.enforcement_executor.close_position = track_close

        # Step 1: Open ES position
        es_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "contract_id": "CON.F.US.ES.H25",
                "size": 1,
            },
        )
        await rule.evaluate(es_event, mock_engine)

        # Step 2: Open MNQ position (0.3s later)
        await asyncio.sleep(0.3)

        mnq_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.Z25",
                "size": 2,
            },
        )
        await rule.evaluate(mnq_event, mock_engine)

        # Both timers should exist
        assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.ES.H25")
        assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")

        # Step 3: Place stop-loss for ES only (after another 0.3s)
        await asyncio.sleep(0.3)

        es_stop_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "contract_id": "CON.F.US.ES.H25",
                "symbol": "ES",
                "type": 3,
                "stopPrice": 5180.0,
                "size": 1,
            },
        )
        await rule.evaluate(es_stop_event, mock_engine)

        # ES timer cancelled, MNQ timer still active
        assert not rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.ES.H25")
        assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")

        # Step 4: Wait for MNQ grace period to expire
        # MNQ timer was started 0.3s after ES, and we've waited 0.3s more
        # So we need to wait: 2.0 - 0.3 = 1.7s, plus buffer
        # Add extra time for timer loop to check (runs every 1s)
        await asyncio.sleep(2.5)

        # Step 5: Only MNQ should be closed
        assert len(enforcement_calls) == 1
        assert enforcement_calls[0]["symbol"] == "MNQ"
        assert enforcement_calls[0]["contract_id"] == "CON.F.US.MNQ.Z25"

    # ========================================================================
    # Test 4: Position Closed Before Grace Expires
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_closed_before_grace_expires(self, rule, mock_engine):
        """
        Test position closed manually before grace period expires.

        Flow:
        1. Position opened → Timer starts
        2. Trader closes position manually (1s later)
        3. Timer cancelled
        4. Wait past grace period
        5. Verify NO enforcement (position already closed)
        """
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": True}

        mock_engine.enforcement_executor.close_position = track_close

        # Step 1: Open position
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.Z25",
                "size": 2,
            },
        )
        await rule.evaluate(position_event, mock_engine)

        timer_name = "no_stop_loss_grace_CON.F.US.MNQ.Z25"
        assert rule.timer_manager.has_timer(timer_name)

        # Step 2: Close position manually after 1 second
        await asyncio.sleep(1.0)

        close_event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.Z25",
                "size": 0,
            },
        )
        await rule.evaluate(close_event, mock_engine)

        # Step 3: Timer should be cancelled
        assert not rule.timer_manager.has_timer(timer_name)

        # Step 4: Wait past original grace period
        await asyncio.sleep(2.0)

        # Step 5: No enforcement should occur
        assert len(enforcement_calls) == 0

    # ========================================================================
    # Test 5: Real Async Timer Integration with Callbacks
    # ========================================================================

    @pytest.mark.asyncio
    async def test_real_async_timer_callback_execution(self, timer_manager):
        """
        Test TimerManager executes callbacks correctly.

        This validates the timer infrastructure itself with a simple callback.
        """
        callback_executed = {"count": 0, "timestamp": None}

        async def test_callback():
            callback_executed["count"] += 1
            from datetime import datetime

            callback_executed["timestamp"] = datetime.now()

        # Start timer with 1 second duration
        await timer_manager.start_timer(
            name="test_timer",
            duration=1,
            callback=test_callback,
        )

        # Verify timer exists
        assert timer_manager.has_timer("test_timer")

        # Wait for expiry
        await asyncio.sleep(1.5)

        # Verify callback executed
        assert callback_executed["count"] == 1
        assert callback_executed["timestamp"] is not None

        # Timer should be removed after expiry
        assert not timer_manager.has_timer("test_timer")

    # ========================================================================
    # Test 6: Order Type Detection (STOP vs LIMIT vs MARKET)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_order_type_detection_only_stops_cancel_timer(
        self, rule, mock_engine
    ):
        """
        Test only valid stop-loss orders (type=3 + stopPrice) cancel timer.

        Orders tested:
        - LIMIT (type=1) → Timer NOT cancelled
        - MARKET (type=0) → Timer NOT cancelled
        - STOP without stopPrice → Timer NOT cancelled
        - STOP with stopPrice → Timer cancelled ✅
        """
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": True}

        mock_engine.enforcement_executor.close_position = track_close

        # Open position
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.Z25",
                "size": 2,
            },
        )
        await rule.evaluate(position_event, mock_engine)

        timer_name = "no_stop_loss_grace_CON.F.US.MNQ.Z25"
        assert rule.timer_manager.has_timer(timer_name)

        # Test 1: LIMIT order (should NOT cancel timer)
        limit_order = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "contract_id": "CON.F.US.MNQ.Z25",
                "symbol": "MNQ",
                "type": 1,  # LIMIT
                "limitPrice": 18600.0,
                "size": 2,
            },
        )
        await rule.evaluate(limit_order, mock_engine)
        assert rule.timer_manager.has_timer(timer_name)  # Still active

        # Test 2: MARKET order (should NOT cancel timer)
        market_order = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "contract_id": "CON.F.US.MNQ.Z25",
                "symbol": "MNQ",
                "type": 0,  # MARKET
                "size": 2,
            },
        )
        await rule.evaluate(market_order, mock_engine)
        assert rule.timer_manager.has_timer(timer_name)  # Still active

        # Test 3: STOP without stopPrice (should NOT cancel timer)
        stop_no_price = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "contract_id": "CON.F.US.MNQ.Z25",
                "symbol": "MNQ",
                "type": 3,  # STOP
                # No stopPrice!
                "size": 2,
            },
        )
        await rule.evaluate(stop_no_price, mock_engine)
        assert rule.timer_manager.has_timer(timer_name)  # Still active

        # Test 4: STOP with stopPrice (should cancel timer)
        valid_stop = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "contract_id": "CON.F.US.MNQ.Z25",
                "symbol": "MNQ",
                "type": 3,  # STOP
                "stopPrice": 18450.0,  # Has stopPrice
                "size": 2,
            },
        )
        await rule.evaluate(valid_stop, mock_engine)
        assert not rule.timer_manager.has_timer(timer_name)  # Cancelled!

        # Wait to ensure no enforcement occurs
        await asyncio.sleep(2.5)
        assert len(enforcement_calls) == 0

    # ========================================================================
    # Test 7: EventBus Integration with Rule Events
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_bus_integration_with_rule_events(
        self, rule, mock_engine, event_bus
    ):
        """
        Test rule events flow through EventBus correctly.

        Flow:
        1. Subscribe to POSITION_OPENED events
        2. Publish position event via EventBus
        3. Rule receives and processes event
        4. Timer starts
        """
        events_received = []

        async def event_handler(event):
            events_received.append(event)
            # Simulate rule evaluation
            await rule.evaluate(event, mock_engine)

        # Subscribe to position events
        event_bus.subscribe(EventType.POSITION_OPENED, event_handler)

        # Publish position opened event
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "contract_id": "CON.F.US.ES.H25",
                "size": 1,
            },
        )

        await event_bus.publish(position_event)

        # Small delay for async propagation
        await asyncio.sleep(0.1)

        # Verify event received and timer started
        assert len(events_received) == 1
        assert rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.ES.H25")

    # ========================================================================
    # Test 8: Timer Persistence Edge Case (System Restart)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_timer_recreated_after_manager_restart(self):
        """
        Test timer behavior across TimerManager restart.

        Note: TimerManager is in-memory only, so timers are lost on restart.
        This test validates that behavior and ensures clean state.
        """
        # Create first manager
        manager1 = TimerManager()
        await manager1.start()

        # Start timer
        callback_count = {"count": 0}

        async def callback():
            callback_count["count"] += 1

        await manager1.start_timer(name="test_timer", duration=5, callback=callback)

        assert manager1.has_timer("test_timer")

        # Stop manager (simulates system shutdown)
        await manager1.stop()

        # Verify timer task cancelled
        # (Timer won't fire because manager stopped)

        # Create new manager (simulates system restart)
        manager2 = TimerManager()
        await manager2.start()

        # Timer should NOT exist in new manager
        assert not manager2.has_timer("test_timer")

        # Timer callback should NOT have fired
        assert callback_count["count"] == 0

        await manager2.stop()

    # ========================================================================
    # Test 9: Concurrent Timer Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_concurrent_timer_operations(self, rule, mock_engine):
        """
        Test multiple timer operations happening concurrently.

        Flow:
        1. Open 5 positions rapidly (all timers start)
        2. Place stops on 2 positions
        3. Close 1 position manually
        4. Wait for grace period
        5. Verify correct enforcement (2 positions closed)
        """
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": True}

        mock_engine.enforcement_executor.close_position = track_close

        # Step 1: Open 5 positions rapidly
        contracts = [
            "CON.F.US.MNQ.Z25",
            "CON.F.US.ES.H25",
            "CON.F.US.NQ.Z25",
            "CON.F.US.YM.H25",
            "CON.F.US.RTY.Z25",
        ]

        for i, contract_id in enumerate(contracts):
            event = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={
                    "symbol": f"SYM{i}",
                    "contract_id": contract_id,
                    "size": 1,
                },
            )
            await rule.evaluate(event, mock_engine)
            await asyncio.sleep(0.05)  # Small stagger

        # All timers should exist
        assert rule.timer_manager.get_timer_count() == 5

        # Step 2: Place stops on positions 0 and 1 (quickly, before timers expire)
        await asyncio.sleep(0.1)

        for i in [0, 1]:
            stop_event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={
                    "contract_id": contracts[i],
                    "symbol": f"SYM{i}",
                    "type": 3,
                    "stopPrice": 1000.0 + i,
                    "size": 1,
                },
            )
            await rule.evaluate(stop_event, mock_engine)

        # 3 timers should remain
        assert rule.timer_manager.get_timer_count() == 3

        # Step 3: Close position 2 manually (also before timer expires)
        close_event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "symbol": "SYM2",
                "contract_id": contracts[2],
                "size": 0,
            },
        )
        await rule.evaluate(close_event, mock_engine)

        # 2 timers should remain (positions 3 and 4)
        assert rule.timer_manager.get_timer_count() == 2

        # Step 4: Wait for grace period to expire
        # Timeline:
        # - Position 3 opened at ~0.15s, expires at 2.15s
        # - Position 4 opened at ~0.20s, expires at 2.20s
        # - Currently at ~0.30s (after stop/close operations)
        # - Need to wait until after 2.20s + 1s buffer for timer loop
        # Timer loop checks every 1s, so next check after 2.20s is at 3s
        await asyncio.sleep(3.0)

        # Step 5: Verify positions 3 and 4 were closed
        assert len(enforcement_calls) == 2

        closed_contracts = {call["contract_id"] for call in enforcement_calls}
        assert contracts[3] in closed_contracts
        assert contracts[4] in closed_contracts

    # ========================================================================
    # Test 10: Enforcement Failure Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_enforcement_failure_does_not_crash(self, rule, mock_engine):
        """
        Test that enforcement failures are handled gracefully.

        Flow:
        1. Position opened → Timer starts
        2. Grace period expires
        3. Enforcement fails (returns success=False)
        4. Rule logs error but doesn't crash
        """
        # Track enforcement calls
        enforcement_calls = []

        async def track_close_with_failure(symbol, contract_id):
            """Track enforcement call and return failure."""
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": False, "error": "Test failure"}

        # Make enforcement fail
        mock_engine.enforcement_executor.close_position = track_close_with_failure

        # Open position
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.Z25",
                "size": 2,
            },
        )

        await rule.evaluate(position_event, mock_engine)

        # Wait for grace period to expire
        # Timer checks every 1s, grace period is 2s, so at t=2s it should fire
        # Add buffer to ensure timer loop has time to check
        await asyncio.sleep(3.0)

        # Enforcement should have been attempted
        assert len(enforcement_calls) == 1
        assert enforcement_calls[0]["symbol"] == "MNQ"
        assert enforcement_calls[0]["contract_id"] == "CON.F.US.MNQ.Z25"

        # Rule should not crash (timer removed cleanly)
        assert not rule.timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")

    # ========================================================================
    # Test 11: Rule Status During Active Timers
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_status_shows_active_timers(self, rule, mock_engine):
        """
        Test get_status() returns correct timer information.

        Flow:
        1. Open 2 positions (2 timers)
        2. Check status (should show 2 active timers)
        3. Cancel 1 timer
        4. Check status (should show 1 active timer)
        """
        # Step 1: Open 2 positions
        for i in range(2):
            event = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={
                    "symbol": f"SYM{i}",
                    "contract_id": f"CON.F.US.SYM{i}.Z25",
                    "size": 1,
                },
            )
            await rule.evaluate(event, mock_engine)

        # Step 2: Check status
        status = rule.get_status()

        assert status["rule"] == "NoStopLossGrace"
        assert status["enabled"] is True
        assert status["grace_period_seconds"] == 2
        assert len(status["active_timers"]) == 2

        # Verify timer info structure
        for timer_info in status["active_timers"]:
            assert "contract_id" in timer_info
            assert "remaining_seconds" in timer_info
            assert 0 <= timer_info["remaining_seconds"] <= 2

        # Step 3: Cancel 1 timer (place stop-loss)
        stop_event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "contract_id": "CON.F.US.SYM0.Z25",
                "symbol": "SYM0",
                "type": 3,
                "stopPrice": 1000.0,
                "size": 1,
            },
        )
        await rule.evaluate(stop_event, mock_engine)

        # Step 4: Check status again
        status2 = rule.get_status()
        assert len(status2["active_timers"]) == 1
        assert status2["active_timers"][0]["contract_id"] == "CON.F.US.SYM1.Z25"

    # ========================================================================
    # Test 12: Disabled Rule Does Not Start Timers
    # ========================================================================

    @pytest.mark.asyncio
    async def test_disabled_rule_integration(self, timer_manager, mock_engine):
        """
        Test disabled rule doesn't start timers or enforce.

        Flow:
        1. Create disabled rule
        2. Open position
        3. Verify no timer started
        4. Wait past grace period
        5. Verify no enforcement
        """
        enforcement_calls = []

        async def track_close(symbol, contract_id):
            enforcement_calls.append({"symbol": symbol, "contract_id": contract_id})
            return {"success": True}

        mock_engine.enforcement_executor.close_position = track_close

        # Create disabled rule
        disabled_rule = NoStopLossGraceRule(
            grace_period_seconds=2,
            enforcement="close_position",
            timer_manager=timer_manager,
            enabled=False,
        )

        # Open position
        position_event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.Z25",
                "size": 2,
            },
        )

        await disabled_rule.evaluate(position_event, mock_engine)

        # No timer should be started
        assert not timer_manager.has_timer("no_stop_loss_grace_CON.F.US.MNQ.Z25")

        # Wait past grace period
        await asyncio.sleep(2.5)

        # No enforcement should occur
        assert len(enforcement_calls) == 0
