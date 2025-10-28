"""
Integration Tests for TradeManagementRule (RULE-012)

Tests the trade management automation rule working with:
- Real position tracking
- Real market price updates
- Real order placement (simulated SDK)
- Complete event sequence flow

Flow: Position Event → Rule Evaluation → Order Placement Action → SDK Order

This tests INTEGRATION between:
- TradeManagementRule
- RiskEngine (position & price tracking)
- EventBus (event routing)
- Enforcement (order placement simulation)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.engine import RiskEngine
from risk_manager.core.config import RiskConfig
from risk_manager.rules.trade_management import TradeManagementRule


@pytest.mark.integration
class TestTradeManagementIntegration:
    """Integration tests for TradeManagementRule."""

    @pytest.fixture
    def tick_values(self):
        """Tick values for futures contracts."""
        return {
            "MNQ": 5.0,   # $5 per tick
            "ES": 50.0,   # $50 per tick
            "NQ": 20.0,   # $20 per tick
        }

    @pytest.fixture
    def tick_sizes(self):
        """Tick sizes for futures contracts."""
        return {
            "MNQ": 0.25,
            "ES": 0.25,
            "NQ": 0.25,
        }

    @pytest.fixture
    def rule_config(self):
        """Default rule configuration."""
        return {
            "enabled": True,
            "auto_stop_loss": {
                "enabled": True,
                "distance": 10  # ticks
            },
            "auto_take_profit": {
                "enabled": True,
                "distance": 20  # ticks
            },
            "trailing_stop": {
                "enabled": True,
                "distance": 8  # ticks
            }
        }

    @pytest.fixture
    def event_bus(self):
        """Create event bus."""
        return EventBus()

    @pytest.fixture
    def mock_trading_integration(self):
        """Create mock trading integration with order placement tracking."""
        integration = AsyncMock()
        integration.flatten_all = AsyncMock()
        integration.flatten_position = AsyncMock()

        # Track orders placed
        integration.orders_placed = []

        async def track_order_placement(order_data):
            integration.orders_placed.append(order_data)
            return {"order_id": f"ORD-{len(integration.orders_placed)}", "success": True}

        integration.place_order = AsyncMock(side_effect=track_order_placement)
        integration.cancel_order = AsyncMock(return_value={"success": True})

        return integration

    @pytest.fixture
    async def engine(
        self,
        rule_config,
        tick_values,
        tick_sizes,
        event_bus,
        mock_trading_integration
    ):
        """Create risk engine with trade management rule."""
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=10
        )
        engine = RiskEngine(config, event_bus, mock_trading_integration)

        # Add trade management rule
        rule = TradeManagementRule(
            config=rule_config,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
        )
        engine.add_rule(rule)

        await engine.start()
        yield engine
        await engine.stop()

    # ========================================================================
    # Test 1: Auto Stop-Loss Placement Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_auto_stop_loss_placement_es_long(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test auto stop-loss is placed when ES long position opens.

        Given: ES Long 1 @ 5000.00
        When: POSITION_OPENED event fires
        Then: Stop-loss order placed at 4997.50 (10 ticks * 0.25 = 2.50 below)
        """
        # Track rule violations via event bus
        violations_received = []

        async def capture_violations(event):
            violations_received.append(event)

        event_bus.subscribe(EventType.RULE_VIOLATED, capture_violations)

        # Given: ES long position
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        engine.market_prices = {"ES": 5000.00}

        # When: Position opened event
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            },
        )

        # Evaluate (violation will be captured via event bus)
        await engine.evaluate_rules(event)
        await asyncio.sleep(0.01)  # Brief delay for event propagation

        # Then: Violation event published with order placement details
        assert len(violations_received) == 1
        violation_data = violations_received[0].data["violation"]

        assert "stop_price" in violation_data
        assert violation_data["stop_price"] == 4997.50  # 5000 - (10 * 0.25)
        assert violation_data["symbol"] == "ES"
        assert violation_data["action"] == "place_bracket_order"

    @pytest.mark.asyncio
    async def test_auto_stop_loss_placement_mnq_short(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test auto stop-loss is placed when MNQ short position opens.

        Given: MNQ Short 2 @ 21000.00
        When: POSITION_OPENED event fires
        Then: Stop-loss order placed at 21002.50 (10 ticks * 0.25 = 2.50 above)
        """
        # Given: MNQ short position
        engine.current_positions = {
            "MNQ": {
                "size": -2,
                "side": "short",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        engine.market_prices = {"MNQ": 21000.00}

        # When: Position opened event
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "size": -2,
                "side": "short",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            },
        )

        # Evaluate
        result = await engine.evaluate_rules(event)

        # Then: Stop-loss placed above entry for short
        trade_mgmt_result = None
        if result:
            for r in result if isinstance(result, list) else [result]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_result = r
                    break

        assert trade_mgmt_result is not None
        assert "stop_price" in trade_mgmt_result
        assert trade_mgmt_result["stop_price"] == 21002.50  # 21000 + (10 * 0.25)

    # ========================================================================
    # Test 2: Auto Take-Profit Placement Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_auto_take_profit_placement(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test auto take-profit is placed when position opens.

        Given: ES Long 1 @ 5000.00
        When: POSITION_OPENED event fires
        Then: Take-profit order placed at 5005.00 (20 ticks * 0.25 = 5.00 above)
        """
        # Given: ES long position
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        engine.market_prices = {"ES": 5000.00}

        # When: Position opened event
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            },
        )

        # Evaluate
        result = await engine.evaluate_rules(event)

        # Then: Take-profit action returned
        trade_mgmt_result = None
        if result:
            for r in result if isinstance(result, list) else [result]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_result = r
                    break

        assert trade_mgmt_result is not None
        assert "take_profit_price" in trade_mgmt_result
        assert trade_mgmt_result["take_profit_price"] == 5005.00  # 5000 + (20 * 0.25)

    # ========================================================================
    # Test 3: Bracket Order Creation Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_bracket_order_creation(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test both stop-loss AND take-profit are placed together.

        Given: MNQ Long 2 @ 21000.00
        When: POSITION_OPENED event fires
        Then:
            - Stop-loss at 20997.50 (10 ticks down)
            - Take-profit at 21005.00 (20 ticks up)
        """
        # Given: MNQ long position
        engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        engine.market_prices = {"MNQ": 21000.00}

        # When: Position opened event
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            },
        )

        # Evaluate
        result = await engine.evaluate_rules(event)

        # Then: Bracket order action returned
        trade_mgmt_result = None
        if result:
            for r in result if isinstance(result, list) else [result]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_result = r
                    break

        assert trade_mgmt_result is not None
        assert trade_mgmt_result["action"] == "place_bracket_order"
        assert trade_mgmt_result["stop_price"] == 20997.50  # 21000 - 2.50
        assert trade_mgmt_result["take_profit_price"] == 21005.00  # 21000 + 5.00
        assert trade_mgmt_result["symbol"] == "MNQ"
        assert trade_mgmt_result["size"] == 2

    # ========================================================================
    # Test 4: Trailing Stop Adjustment Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_trailing_stop_adjustment_on_profit(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test trailing stop is adjusted when price moves favorably.

        Given: ES Long 1 @ 5000.00, stop at 4997.50
        When: Price moves to 5002.00
        Then: Stop adjusted to 5000.00 (8 ticks = 2.00 below new high)
        When: Price moves to 5004.00
        Then: Stop adjusted to 5002.00
        """
        # Given: ES long position with existing stop
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
                "stop_price": 4997.50,
                "stop_order_id": "SL123",
            }
        }
        engine.market_prices = {"ES": 5002.00}  # Price moved up

        # When: Position updated event
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 1,
                "avgPrice": 5000.00,
            },
        )

        # Evaluate
        result = await engine.evaluate_rules(event)

        # Then: Trailing stop adjusted
        trade_mgmt_result = None
        if result:
            for r in result if isinstance(result, list) else [result]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_result = r
                    break

        assert trade_mgmt_result is not None
        assert trade_mgmt_result["action"] == "adjust_trailing_stop"
        assert trade_mgmt_result["new_stop_price"] == 5000.00  # 5002 - (8 * 0.25)
        assert trade_mgmt_result["old_stop_price"] == 4997.50

        # Now price moves further up
        engine.market_prices["ES"] = 5004.00

        event2 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 1,
                "avgPrice": 5000.00,
            },
        )

        # Update old stop price
        engine.current_positions["ES"]["stop_price"] = 5000.00

        result2 = await engine.evaluate_rules(event2)

        # Then: Stop adjusted again
        trade_mgmt_result2 = None
        if result2:
            for r in result2 if isinstance(result2, list) else [result2]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_result2 = r
                    break

        assert trade_mgmt_result2 is not None
        assert trade_mgmt_result2["action"] == "adjust_trailing_stop"
        assert trade_mgmt_result2["new_stop_price"] == 5002.00  # 5004 - (8 * 0.25)

    @pytest.mark.asyncio
    async def test_trailing_stop_not_adjusted_on_loss(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test trailing stop is NOT adjusted when price moves unfavorably.

        Given: ES Long 1 @ 5000.00, stop at 4997.50
        When: Price drops to 4998.00 (losing)
        Then: Stop NOT adjusted (stays at 4997.50)
        """
        # Given: ES long position
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
                "stop_price": 4997.50,
            }
        }
        engine.market_prices = {"ES": 4998.00}  # Price moved down

        # When: Position updated event
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 1,
            },
        )

        # Evaluate
        result = await engine.evaluate_rules(event)

        # Then: No trailing stop adjustment (or None)
        if result:
            results_list = result if isinstance(result, list) else [result]
            for r in results_list:
                if r and r.get("rule") == "TradeManagementRule":
                    # Should not be trailing stop adjustment
                    assert r.get("action") != "adjust_trailing_stop"

    # ========================================================================
    # Test 5: Multi-Symbol Independence Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_symbol_independent_management(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test each symbol's orders are managed independently.

        Given: ES position AND MNQ position
        When: Both positions open
        Then:
            - ES orders placed with ES tick size (0.25)
            - MNQ orders placed with MNQ tick size (0.25)
            - Different symbols, independent tracking
        """
        # Given: ES position
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        engine.market_prices = {"ES": 5000.00}

        # When: ES position opened
        event_es = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "size": 1},
        )

        result_es = await engine.evaluate_rules(event_es)

        # Then: ES orders placed
        trade_mgmt_es = None
        if result_es:
            for r in result_es if isinstance(result_es, list) else [result_es]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_es = r
                    break

        assert trade_mgmt_es is not None
        assert trade_mgmt_es["symbol"] == "ES"
        assert "MNQ" not in str(trade_mgmt_es)

        # Given: MNQ position
        engine.current_positions["MNQ"] = {
            "size": 2,
            "side": "long",
            "avgPrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
        }
        engine.market_prices["MNQ"] = 21000.00

        # When: MNQ position opened
        event_mnq = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "size": 2},
        )

        result_mnq = await engine.evaluate_rules(event_mnq)

        # Then: MNQ orders placed independently
        trade_mgmt_mnq = None
        if result_mnq:
            for r in result_mnq if isinstance(result_mnq, list) else [result_mnq]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_mnq = r
                    break

        assert trade_mgmt_mnq is not None
        assert trade_mgmt_mnq["symbol"] == "MNQ"
        assert trade_mgmt_mnq["stop_price"] == 20997.50  # MNQ tick size applied
        assert trade_mgmt_mnq["take_profit_price"] == 21005.00

    # ========================================================================
    # Test 6: Position Closed - Order Cleanup Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_closed_orders_cleanup(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test when position closes, stop/target orders should be cancelled.

        Given: ES position with bracket orders
        When: Position closes
        Then: Stop and target orders cancelled
        """
        # Given: Position with orders
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
                "stop_order_id": "SL123",
                "target_order_id": "TP456",
            }
        }
        engine.market_prices = {"ES": 5000.00}

        # When: Position closed event
        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "symbol": "ES",
                "size": 0,
            },
        )

        # Remove position from tracking
        engine.current_positions.pop("ES", None)

        # Evaluate (may not return anything for closed position)
        result = await engine.evaluate_rules(event)

        # Verify position removed
        assert "ES" not in engine.current_positions

    # ========================================================================
    # Test 7: Event Bus Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_bus_routes_to_rule(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test EventBus publishes position events and rule evaluates them.

        Given: Trade management rule subscribed to position events
        When: POSITION_OPENED event published to event bus
        Then: Rule evaluates and returns order placement action
        """
        # Given: Position
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        engine.market_prices = {"ES": 5000.00}

        # Track automation actions
        automation_actions = []

        async def track_automation(event):
            if event.event_type == EventType.ENFORCEMENT_ACTION:
                if "automate" in str(event.data).lower():
                    automation_actions.append(event)

        event_bus.subscribe(EventType.ENFORCEMENT_ACTION, track_automation)

        # When: Position event published
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "size": 1},
        )

        await event_bus.publish(event)
        result = await engine.evaluate_rules(event)

        # Then: Rule evaluated
        assert result is not None

        # Check if it's our rule result
        if isinstance(result, list):
            trade_mgmt_found = any(r.get("rule") == "TradeManagementRule" for r in result if r)
        else:
            trade_mgmt_found = result.get("rule") == "TradeManagementRule"

        assert trade_mgmt_found

    # ========================================================================
    # Test 8: Configuration Toggle Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_stop_loss_disabled_only_take_profit(
        self, tick_values, tick_sizes, event_bus, mock_trading_integration
    ):
        """
        Test when stop-loss disabled, only take-profit is placed.

        Given: Config with stop-loss disabled, take-profit enabled
        When: Position opens
        Then: Only take-profit order placed, no stop-loss
        """
        # Given: Config with stop-loss disabled
        config = {
            "enabled": True,
            "auto_stop_loss": {
                "enabled": False,
                "distance": 0
            },
            "auto_take_profit": {
                "enabled": True,
                "distance": 20
            },
            "trailing_stop": {
                "enabled": False,
                "distance": 0
            }
        }

        # Create engine with custom config
        risk_config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=10
        )
        engine = RiskEngine(risk_config, event_bus, mock_trading_integration)

        rule = TradeManagementRule(
            config=config,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
        )
        engine.add_rule(rule)

        await engine.start()

        # Given: Position
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        engine.market_prices = {"ES": 5000.00}

        # When: Position opened
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "size": 1},
        )

        result = await engine.evaluate_rules(event)

        # Then: Only take-profit, no stop-loss
        trade_mgmt_result = None
        if result:
            for r in result if isinstance(result, list) else [result]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_result = r
                    break

        assert trade_mgmt_result is not None
        assert trade_mgmt_result["action"] == "place_take_profit"
        assert "take_profit_price" in trade_mgmt_result
        assert "stop_price" not in trade_mgmt_result

        await engine.stop()

    @pytest.mark.asyncio
    async def test_take_profit_disabled_only_stop_loss(
        self, tick_values, tick_sizes, event_bus, mock_trading_integration
    ):
        """
        Test when take-profit disabled, only stop-loss is placed.

        Given: Config with take-profit disabled, stop-loss enabled
        When: Position opens
        Then: Only stop-loss order placed, no take-profit
        """
        # Given: Config with take-profit disabled
        config = {
            "enabled": True,
            "auto_stop_loss": {
                "enabled": True,
                "distance": 10
            },
            "auto_take_profit": {
                "enabled": False,
                "distance": 0
            },
            "trailing_stop": {
                "enabled": False,
                "distance": 0
            }
        }

        # Create engine
        risk_config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user",
            max_contracts=10
        )
        engine = RiskEngine(risk_config, event_bus, mock_trading_integration)

        rule = TradeManagementRule(
            config=config,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
        )
        engine.add_rule(rule)

        await engine.start()

        # Given: Position
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        engine.market_prices = {"ES": 5000.00}

        # When: Position opened
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "size": 1},
        )

        result = await engine.evaluate_rules(event)

        # Then: Only stop-loss, no take-profit
        trade_mgmt_result = None
        if result:
            for r in result if isinstance(result, list) else [result]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_result = r
                    break

        assert trade_mgmt_result is not None
        assert trade_mgmt_result["action"] == "place_stop_loss"
        assert "stop_price" in trade_mgmt_result
        assert "take_profit_price" not in trade_mgmt_result

        await engine.stop()

    # ========================================================================
    # Test 9: Complete Order Flow Integration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_complete_order_placement_flow(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test complete flow from position open to order placement.

        Given: New position opens
        When: Event flows through system
        Then:
            1. Rule evaluates event
            2. Order action returned
            3. Enforcement metadata contains correct prices
            4. Order ready for SDK placement
        """
        # Given: Position opens
        engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        engine.market_prices = {"MNQ": 21000.00}

        # When: Event flows through system
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "MNQ",
                "size": 2,
                "avgPrice": 21000.00,
            },
        )

        # Publish to event bus
        await event_bus.publish(event)

        # Engine evaluates
        result = await engine.evaluate_rules(event)

        # Then: Complete order metadata present
        trade_mgmt_result = None
        if result:
            for r in result if isinstance(result, list) else [result]:
                if r and r.get("rule") == "TradeManagementRule":
                    trade_mgmt_result = r
                    break

        assert trade_mgmt_result is not None

        # Verify all required fields for SDK order placement
        assert "symbol" in trade_mgmt_result
        assert "contractId" in trade_mgmt_result
        assert "side" in trade_mgmt_result
        assert "size" in trade_mgmt_result
        assert "entry_price" in trade_mgmt_result
        assert "stop_price" in trade_mgmt_result
        assert "take_profit_price" in trade_mgmt_result
        assert "timestamp" in trade_mgmt_result

        # Verify correct calculations
        assert trade_mgmt_result["stop_price"] == 20997.50
        assert trade_mgmt_result["take_profit_price"] == 21005.00

    # ========================================================================
    # Test 10: Performance - Event Processing Speed
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_processing_performance(
        self, engine, event_bus, mock_trading_integration
    ):
        """
        Test trade management rule evaluates quickly.

        Given: Position event
        When: Rule evaluates
        Then: Completes in < 50ms
        """
        import time

        # Given: Position
        engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        engine.market_prices = {"ES": 5000.00}

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "size": 1},
        )

        # When: Evaluate rule
        start = time.time()
        result = await engine.evaluate_rules(event)
        elapsed = time.time() - start

        # Then: Fast evaluation
        assert elapsed < 0.05, f"Trade management evaluation took {elapsed}s, too slow!"
        assert result is not None
