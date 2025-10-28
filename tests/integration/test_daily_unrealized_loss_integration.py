"""
Integration Tests for DailyUnrealizedLossRule (RULE-004)

Tests the daily unrealized loss rule with real components:
- Real position tracking (simulated positions)
- Real market price updates
- Real P&L calculation
- Real enforcement (close position action)
- Real EventBus integration

Rule: RULE-004 - Daily Unrealized Loss (Stop Loss Per Position)
- Close losing positions when unrealized loss hits limit
- Trade-by-trade enforcement (close ONLY that losing position)
- No lockout (trader can continue trading)
- Real-time market price monitoring required
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from risk_manager.rules.daily_unrealized_loss import DailyUnrealizedLossRule
from risk_manager.core.events import RiskEvent, EventType, EventBus
from risk_manager.core.engine import RiskEngine
from risk_manager.core.config import RiskConfig


@pytest.mark.integration
class TestDailyUnrealizedLossIntegration:
    """Integration tests for DailyUnrealizedLossRule."""

    # ========================================================================
    # Fixtures
    # ========================================================================

    @pytest.fixture
    def tick_values(self):
        """Tick values for futures contracts."""
        return {
            "MNQ": 5.0,   # $5 per tick
            "ES": 50.0,   # $50 per tick
            "NQ": 20.0,   # $20 per tick
            "RTY": 5.0,   # $5 per tick (0.10 tick size)
        }

    @pytest.fixture
    def tick_sizes(self):
        """Tick sizes for futures contracts."""
        return {
            "MNQ": 0.25,
            "ES": 0.25,
            "NQ": 0.25,
            "RTY": 0.10,  # Different tick size
        }

    @pytest.fixture
    def rule(self, tick_values, tick_sizes):
        """Create daily unrealized loss rule with -$300 limit."""
        return DailyUnrealizedLossRule(
            loss_limit=-300.0,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
            action="close_position"
        )

    @pytest.fixture
    def event_bus(self):
        """Create event bus for integration testing."""
        return EventBus()

    @pytest.fixture
    def mock_trading_integration(self):
        """Create mock trading integration for enforcement."""
        integration = AsyncMock()
        integration.flatten_position = AsyncMock(return_value=True)
        integration.flatten_all = AsyncMock(return_value=True)
        return integration

    @pytest.fixture
    async def engine(self, event_bus, mock_trading_integration):
        """
        Create risk engine with real EventBus and mocked SDK.

        The engine tracks positions and market prices, which are
        the core dependencies for unrealized P&L calculation.
        """
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=10
        )
        engine = RiskEngine(config, event_bus, mock_trading_integration)

        # Initialize position and price tracking
        engine.current_positions = {}
        engine.market_prices = {}

        await engine.start()
        yield engine
        await engine.stop()

    # ========================================================================
    # Test 1: Full Unrealized Loss Violation Flow
    # ========================================================================

    @pytest.mark.asyncio
    async def test_full_unrealized_loss_violation_flow(
        self, rule, engine, event_bus, mock_trading_integration
    ):
        """
        Test complete flow from position open to loss violation to enforcement.

        Scenario:
        1. Open ES long at 5000.00 (2 contracts)
        2. Price drops to 4980.00
        3. Unrealized P&L = -$1000 (exceeds -$300 limit)
        4. Verify violation detected
        5. Verify CLOSE_POSITION action (NOT flatten_all)
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # And: ES long position at 5000.00
        engine.current_positions["ES"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 5000.00,
            "contractId": "CON.F.US.ES.H25",
        }

        # And: Market price drops to 4980.00
        # Loss = (4980 - 5000) / 0.25 * 2 * 50 = -80 ticks * 2 * $50 = -$8000
        engine.market_prices["ES"] = 4980.00

        # When: Position update event received
        position_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
            },
        )

        await engine.evaluate_rules(position_event)

        # Then: Flatten position should be called (NOT flatten_all)
        mock_trading_integration.flatten_position.assert_called_once()
        call_args = mock_trading_integration.flatten_position.call_args
        assert "CON.F.US.ES.H25" in str(call_args)

    # ========================================================================
    # Test 2: Multi-Position Independence
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_position_independence(
        self, rule, engine, mock_trading_integration
    ):
        """
        Test that only the violating position is closed, others remain open.

        Scenario:
        - ES long: -$400 unrealized (violates -$300 limit)
        - MNQ long: -$100 unrealized (within limit)
        - Verify only ES position closed
        - Verify MNQ position remains open
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # And: Two positions - ES losing, MNQ minor loss
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            },
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            },
        }

        # And: Market prices
        # ES: (5992 - 6000) / 0.25 * 1 * 50 = -32 ticks * $50 = -$1600 (VIOLATES)
        # MNQ: (20995 - 21000) / 0.25 * 2 * 5 = -20 ticks * 2 * $5 = -$200 (OK)
        engine.market_prices = {
            "ES": 5992.00,
            "MNQ": 20995.00,
        }

        # When: ES position event triggers evaluation
        es_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1, "avgPrice": 6000.00},
        )

        await engine.evaluate_rules(es_event)

        # Then: Only ES position should be closed
        mock_trading_integration.flatten_position.assert_called_once()
        call_args = mock_trading_integration.flatten_position.call_args
        assert "CON.F.US.ES.H25" in str(call_args)

        # Reset mock
        mock_trading_integration.flatten_position.reset_mock()

        # When: MNQ position event triggers evaluation
        mnq_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2, "avgPrice": 21000.00},
        )

        await engine.evaluate_rules(mnq_event)

        # Then: MNQ position should NOT be closed (within limit)
        mock_trading_integration.flatten_position.assert_not_called()

    # ========================================================================
    # Test 3: Real P&L Calculation Accuracy
    # ========================================================================

    @pytest.mark.asyncio
    async def test_real_pnl_calculation_accuracy(self, rule, engine):
        """
        Test P&L calculation accuracy with real formulas.

        Test both long and short positions with different symbols.
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # Test 1: Long position
        # MNQ Long: entry 21000, current 20970, 2 contracts
        # P&L = (20970 - 21000) / 0.25 * 2 * 5 = -120 ticks * 2 * $5 = -$1200
        engine.current_positions["MNQ"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
        }
        engine.market_prices["MNQ"] = 20970.00

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2},
        )

        violation = await rule.evaluate(event, engine)

        # Verify P&L calculation
        assert violation is not None
        assert abs(violation["unrealized_pnl"] - (-1200.0)) < 0.01

        # Test 2: Short position
        # ES Short: entry 6000, current 6010, 1 contract
        # P&L = (6000 - 6010) / 0.25 * 1 * 50 = -40 ticks * $50 = -$2000
        engine.current_positions["ES"] = {
            "size": -1,
            "side": "short",
            "avgPrice": 6000.00,
            "contractId": "CON.F.US.ES.H25",
        }
        engine.market_prices["ES"] = 6010.00

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": -1},
        )

        violation = await rule.evaluate(event, engine)

        # Verify P&L calculation
        assert violation is not None
        assert abs(violation["unrealized_pnl"] - (-2000.0)) < 0.01

    # ========================================================================
    # Test 4: Market Price Updates Real-Time Monitoring
    # ========================================================================

    @pytest.mark.asyncio
    async def test_market_price_updates_real_time_monitoring(
        self, rule, engine, mock_trading_integration
    ):
        """
        Test real-time price monitoring as market moves.

        Scenario:
        - Position opened at 5000
        - Price updates: 4999 → 4997 → 4994
        - Only last update triggers violation
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # And: ES position at 5000.00
        engine.current_positions["ES"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 5000.00,
            "contractId": "CON.F.US.ES.H25",
        }

        # Price update 1: 4999.00 - small loss
        # P&L = (4999 - 5000) / 0.25 * 2 * 50 = -4 ticks * 2 * $50 = -$400
        # This VIOLATES (-400 < -300), let's recalculate
        # For -$300 limit: -300 / (2 * 50) = -3 ticks = -0.75 points
        # Threshold price = 5000 - 0.75 = 4999.25

        # Price 1: 4999.50 (within limit)
        # P&L = (4999.50 - 5000) / 0.25 * 2 * 50 = -2 ticks * 2 * $50 = -$200
        engine.market_prices["ES"] = 4999.50

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 2},
        )

        await engine.evaluate_rules(event)
        mock_trading_integration.flatten_position.assert_not_called()

        # Price 2: 4999.25 (at exact limit)
        # P&L = (4999.25 - 5000) / 0.25 * 2 * 50 = -3 ticks * 2 * $50 = -$300
        engine.market_prices["ES"] = 4999.25

        await engine.evaluate_rules(event)

        # At exact limit should trigger (<= comparison)
        assert mock_trading_integration.flatten_position.call_count >= 1

    # ========================================================================
    # Test 5: Different Tick Sizes Calculation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_different_tick_sizes_calculation(self, rule, engine):
        """
        Test P&L calculation with different tick sizes.

        Test ES (0.25), MNQ (0.25), RTY (0.10) to ensure
        tick size is correctly applied in calculations.
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # Test ES: tick_size=0.25, tick_value=$50
        engine.current_positions["ES"] = {
            "size": 1,
            "side": "long",
            "avgPrice": 6000.00,
            "contractId": "CON.F.US.ES.H25",
        }
        engine.market_prices["ES"] = 5990.00
        # P&L = (5990 - 6000) / 0.25 * 1 * 50 = -40 ticks * $50 = -$2000

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES"},
        )

        violation = await rule.evaluate(event, engine)
        assert violation is not None
        assert abs(violation["unrealized_pnl"] - (-2000.0)) < 0.01

        # Test MNQ: tick_size=0.25, tick_value=$5
        engine.current_positions["MNQ"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
        }
        engine.market_prices["MNQ"] = 20970.00
        # P&L = (20970 - 21000) / 0.25 * 2 * 5 = -120 ticks * 2 * $5 = -$1200

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, engine)
        assert violation is not None
        assert abs(violation["unrealized_pnl"] - (-1200.0)) < 0.01

        # Test RTY: tick_size=0.10, tick_value=$5
        engine.current_positions["RTY"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 2000.00,
            "contractId": "CON.F.US.RTY.H25",
        }
        engine.market_prices["RTY"] = 1990.00
        # P&L = (1990 - 2000) / 0.10 * 2 * 5 = -100 ticks * 2 * $5 = -$1000

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "RTY"},
        )

        violation = await rule.evaluate(event, engine)
        assert violation is not None
        assert abs(violation["unrealized_pnl"] - (-1000.0)) < 0.01

    # ========================================================================
    # Test 6: No Lockout Verification
    # ========================================================================

    @pytest.mark.asyncio
    async def test_no_lockout_created_on_violation(
        self, rule, engine, mock_trading_integration
    ):
        """
        Test that violation does NOT create lockout.

        This is a trade-by-trade rule - close position and move on.
        Trader can immediately open new positions.
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # And: Position with major loss
        engine.current_positions["MNQ"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
        }
        engine.market_prices["MNQ"] = 20970.00

        # Track violation events
        violations_received = []

        async def violation_handler(event):
            violations_received.append(event)

        engine.event_bus.subscribe(EventType.RULE_VIOLATED, violation_handler)

        # When: Violation occurs
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2},
        )

        await engine.evaluate_rules(event)

        # Small delay for event propagation
        await asyncio.sleep(0.1)

        # Then: Violation should be recorded
        assert len(violations_received) > 0

        # But: NO lockout should be created
        violation_data = violations_received[0].data
        assert "lockout" not in violation_data or violation_data.get("lockout") is None

        # And: Position should be closed
        mock_trading_integration.flatten_position.assert_called()

    # ========================================================================
    # Test 7: EventBus Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_bus_integration_complete_flow(
        self, rule, engine, event_bus, mock_trading_integration
    ):
        """
        Test complete EventBus integration flow.

        Flow:
        1. Publish POSITION_UPDATED event
        2. Rule evaluates
        3. Violation published to EventBus
        4. Enforcement action correct (close_position, not flatten_all)
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # And: Track all events
        violations = []
        enforcements = []

        async def violation_handler(event):
            violations.append(event)

        async def enforcement_handler(event):
            enforcements.append(event)

        event_bus.subscribe(EventType.RULE_VIOLATED, violation_handler)
        event_bus.subscribe(EventType.ENFORCEMENT_ACTION, enforcement_handler)

        # And: Position with loss
        engine.current_positions["ES"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 5000.00,
            "contractId": "CON.F.US.ES.H25",
        }
        engine.market_prices["ES"] = 4980.00

        # When: Position update event published
        position_event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 2, "avgPrice": 5000.00},
        )

        await event_bus.publish(position_event)
        await engine.evaluate_rules(position_event)

        # Small delay for async event propagation
        await asyncio.sleep(0.1)

        # Then: Violation event published
        assert len(violations) > 0
        assert violations[0].event_type == EventType.RULE_VIOLATED

        # And: Enforcement triggered
        mock_trading_integration.flatten_position.assert_called()

        # And: Enforcement event published
        assert len(enforcements) > 0
        enforcement_data = enforcements[0].data
        assert enforcement_data["action"] == "close_position"
        assert "ES" in enforcement_data.get("symbol", "")

    # ========================================================================
    # Test 8: Position Closed Before Violation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_closed_before_violation(
        self, rule, engine, mock_trading_integration
    ):
        """
        Test that no violation occurs if position is closed manually.

        Scenario:
        - Position underwater (-$250)
        - Trader closes manually before hitting -$300
        - Verify no violation (position gone)
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # And: Position with moderate loss (not yet violation)
        engine.current_positions["MNQ"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
        }
        # Loss: (20993.75 - 21000) / 0.25 * 2 * 5 = -25 ticks * 2 * $5 = -$250
        engine.market_prices["MNQ"] = 20993.75

        # When: Position update event
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2},
        )

        await engine.evaluate_rules(event)

        # Then: No violation (within limit)
        mock_trading_integration.flatten_position.assert_not_called()

        # When: Trader closes position manually
        del engine.current_positions["MNQ"]

        # And: Another update arrives (position is gone)
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 0},
        )

        violation = await rule.evaluate(event, engine)

        # Then: No violation (position no longer exists)
        assert violation is None
        mock_trading_integration.flatten_position.assert_not_called()

    # ========================================================================
    # Test 9: Long and Short Positions Accuracy
    # ========================================================================

    @pytest.mark.asyncio
    async def test_long_and_short_positions_accuracy(self, rule, engine):
        """
        Test P&L calculation accuracy for both long and short positions.

        Verify both profit and loss directions are correct.
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # Test long position with loss
        engine.current_positions["ES"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 5000.00,
            "contractId": "CON.F.US.ES.H25",
        }
        engine.market_prices["ES"] = 4995.00
        # P&L = (4995 - 5000) / 0.25 * 2 * 50 = -20 ticks * 2 * $50 = -$2000

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 2},
        )

        violation = await rule.evaluate(event, engine)
        assert violation is not None
        assert abs(violation["unrealized_pnl"] - (-2000.0)) < 0.01

        # Test short position with loss
        engine.current_positions["MNQ"] = {
            "size": -2,
            "side": "short",
            "avgPrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
        }
        engine.market_prices["MNQ"] = 21030.00
        # P&L = (21000 - 21030) / 0.25 * 2 * 5 = -120 ticks * 2 * $5 = -$1200

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": -2},
        )

        violation = await rule.evaluate(event, engine)
        assert violation is not None
        assert abs(violation["unrealized_pnl"] - (-1200.0)) < 0.01

        # Test long position with profit (should NOT violate)
        engine.current_positions["ES"]["size"] = 1
        engine.market_prices["ES"] = 5010.00
        # P&L = (5010 - 5000) / 0.25 * 1 * 50 = 40 ticks * $50 = +$2000

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1},
        )

        violation = await rule.evaluate(event, engine)
        assert violation is None  # Profit, not loss

    # ========================================================================
    # Test 10: Enforcement Action Verification
    # ========================================================================

    @pytest.mark.asyncio
    async def test_enforcement_action_close_position_not_flatten_all(
        self, rule, engine, mock_trading_integration
    ):
        """
        Test that enforcement calls flatten_position, NOT flatten_all.

        This is critical - we only close the losing position, not all positions.
        """
        # Given: Rule added to engine
        engine.add_rule(rule)

        # And: Multiple positions
        engine.current_positions = {
            "ES": {
                "size": 2,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            },
            "MNQ": {
                "size": 1,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            },
        }

        # Only ES has loss that violates
        engine.market_prices = {
            "ES": 4980.00,  # Big loss
            "MNQ": 21010.00,  # Profit
        }

        # When: ES violation occurs
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 2},
        )

        await engine.evaluate_rules(event)

        # Then: flatten_position should be called (NOT flatten_all)
        mock_trading_integration.flatten_position.assert_called()
        mock_trading_integration.flatten_all.assert_not_called()

        # And: Correct contractId passed
        call_args = mock_trading_integration.flatten_position.call_args
        assert "CON.F.US.ES.H25" in str(call_args)
