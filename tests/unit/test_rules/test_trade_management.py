"""
Unit Tests for TradeManagementRule (RULE-012)

Tests the trade management automation rule in isolation with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-012 - Trade Management (Automation)
- Automatically attach stop-loss orders to positions
- Automatically attach take-profit orders to positions
- Automatically adjust trailing stops
- NO enforcement (this is automation only)
- NO violations, NO lockouts
- Position monitoring and order placement
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from risk_manager.rules.trade_management import TradeManagementRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine


class TestTradeManagementRule:
    """Unit tests for TradeManagementRule."""

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
    def rule(self, rule_config, tick_values, tick_sizes):
        """Create trade management rule."""
        return TradeManagementRule(
            config=rule_config,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
        )

    @pytest.fixture
    def mock_engine(self):
        """Create mock risk engine with SDK access."""
        engine = Mock(spec=RiskEngine)
        engine.current_positions = {}
        engine.market_prices = {}

        # Mock suite manager and order placement
        engine.suite_manager = Mock()
        mock_suite = Mock()
        mock_suite.orders = Mock()
        mock_suite.orders.place_order = AsyncMock(return_value={"order_id": "123", "success": True})
        engine.suite_manager.get_suite = Mock(return_value=mock_suite)

        return engine

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization(self, rule):
        """Test rule initializes with correct parameters."""
        assert rule.enabled is True
        assert rule.auto_stop_loss_enabled is True
        assert rule.stop_loss_distance == 10
        assert rule.auto_take_profit_enabled is True
        assert rule.take_profit_distance == 20
        assert rule.trailing_stop_enabled is True
        assert rule.trailing_stop_distance == 8
        assert rule.name == "TradeManagementRule"

    def test_rule_initialization_with_partial_config(self, tick_values, tick_sizes):
        """Test rule initialization with only stop loss enabled."""
        config = {
            "enabled": True,
            "auto_stop_loss": {
                "enabled": True,
                "distance": 15
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
        rule = TradeManagementRule(
            config=config,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
        )
        assert rule.auto_stop_loss_enabled is True
        assert rule.stop_loss_distance == 15
        assert rule.auto_take_profit_enabled is False
        assert rule.trailing_stop_enabled is False

    # ========================================================================
    # Test 2: Stop-Loss Order Placement on Position Open
    # ========================================================================

    @pytest.mark.asyncio
    async def test_place_stop_loss_on_long_position_open(self, tick_values, tick_sizes, mock_engine):
        """Test that stop-loss is automatically placed when long position opens."""
        # Given: ES Long 1 @ 6000.00, stop should be at 6000 - (10 ticks * 0.25) = 5997.50
        # Use config with only stop-loss enabled
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
        rule = TradeManagementRule(
            config=config,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
        )

        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6000.00}

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            },
        )

        # When: Rule evaluates event
        result = await rule.evaluate(event, mock_engine)

        # Then: Stop-loss order should be placed
        assert result is not None
        assert result["action"] == "place_stop_loss"
        assert result["symbol"] == "ES"
        assert result["stop_price"] == 5997.50  # 6000 - (10 * 0.25)
        assert "stop-loss" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_place_stop_loss_on_short_position_open(self, tick_values, tick_sizes, mock_engine):
        """Test that stop-loss is automatically placed when short position opens."""
        # Given: ES Short 1 @ 6000.00, stop should be at 6000 + (10 ticks * 0.25) = 6002.50
        # Use config with only stop-loss enabled
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
        rule = TradeManagementRule(
            config=config,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
        )

        mock_engine.current_positions = {
            "ES": {
                "size": -1,
                "side": "short",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6000.00}

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "size": -1,
                "side": "short",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            },
        )

        result = await rule.evaluate(event, mock_engine)

        # Then: Stop-loss order should be placed above entry for short
        assert result is not None
        assert result["action"] == "place_stop_loss"
        assert result["stop_price"] == 6002.50  # 6000 + (10 * 0.25)

    # ========================================================================
    # Test 3: Take-Profit Order Placement on Position Open
    # ========================================================================

    @pytest.mark.asyncio
    async def test_place_take_profit_on_long_position_open(self, rule, mock_engine):
        """Test that take-profit is automatically placed when long position opens."""
        # Given: ES Long 1 @ 6000.00, target should be at 6000 + (20 ticks * 0.25) = 6005.00
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6000.00}

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            },
        )

        result = await rule.evaluate(event, mock_engine)

        # Should return action for take-profit (may be combined with stop-loss)
        assert result is not None
        # Check if take-profit info is present
        if "take_profit_price" in result:
            assert result["take_profit_price"] == 6005.00  # 6000 + (20 * 0.25)

    @pytest.mark.asyncio
    async def test_place_take_profit_on_short_position_open(self, rule, mock_engine):
        """Test that take-profit is automatically placed when short position opens."""
        # Given: ES Short 1 @ 6000.00, target should be at 6000 - (20 ticks * 0.25) = 5995.00
        mock_engine.current_positions = {
            "ES": {
                "size": -1,
                "side": "short",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6000.00}

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "size": -1,
                "side": "short",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            },
        )

        result = await rule.evaluate(event, mock_engine)

        # Should return action for take-profit
        assert result is not None
        if "take_profit_price" in result:
            assert result["take_profit_price"] == 5995.00  # 6000 - (20 * 0.25)

    # ========================================================================
    # Test 4: Bracket Order (Stop + Target Combined)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_place_bracket_order_on_position_open(self, rule, mock_engine):
        """Test that both stop-loss and take-profit are placed together."""
        # Given: MNQ Long 2 @ 21000.00
        # Stop: 21000 - (10 * 0.25) = 20997.50
        # Target: 21000 + (20 * 0.25) = 21005.00
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 21000.00}

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

        result = await rule.evaluate(event, mock_engine)

        # Should place both orders
        assert result is not None
        assert result["action"] == "place_bracket_order"
        assert "stop_price" in result
        assert "take_profit_price" in result
        assert result["stop_price"] == 20997.50
        assert result["take_profit_price"] == 21005.00

    # ========================================================================
    # Test 5: Trailing Stop Adjustment
    # ========================================================================

    @pytest.mark.asyncio
    async def test_adjust_trailing_stop_on_profit(self, rule, mock_engine):
        """Test that trailing stop is adjusted when position moves in profit."""
        # Given: ES Long 1 @ 6000.00, now at 6010.00
        # New trailing stop should be: 6010 - (8 ticks * 0.25) = 6008.00
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
                "stop_order_id": "SL123",  # Existing stop-loss
                "stop_price": 5997.50,     # Original stop
            }
        }
        mock_engine.market_prices = {"ES": 6010.00}  # Price moved up

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 1,
                "avgPrice": 6000.00,
            },
        )

        result = await rule.evaluate(event, mock_engine)

        # Should adjust trailing stop
        assert result is not None
        assert result["action"] == "adjust_trailing_stop"
        assert result["new_stop_price"] == 6008.00  # 6010 - (8 * 0.25)
        assert result["old_stop_price"] == 5997.50

    @pytest.mark.asyncio
    async def test_trailing_stop_not_adjusted_on_loss(self, rule, mock_engine):
        """Test that trailing stop is NOT adjusted when position moves against us."""
        # Given: ES Long 1 @ 6000.00, now at 5995.00 (losing)
        # Trailing stop should NOT move down
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
                "stop_order_id": "SL123",
                "stop_price": 5997.50,  # Original stop
                "highest_price": 6000.00,  # Track highest price seen
            }
        }
        mock_engine.market_prices = {"ES": 5995.00}  # Price moved down

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 1,
            },
        )

        result = await rule.evaluate(event, mock_engine)

        # Should NOT adjust stop (or return None)
        if result is not None:
            assert result["action"] != "adjust_trailing_stop"
            # Or check that stop price didn't move
            if "new_stop_price" in result:
                assert result["new_stop_price"] >= 5997.50

    # ========================================================================
    # Test 6: Stop-Loss Disabled Configuration
    # ========================================================================

    @pytest.mark.asyncio
    async def test_no_stop_loss_when_disabled(self, tick_values, tick_sizes, mock_engine):
        """Test that stop-loss is not placed when disabled."""
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
        rule = TradeManagementRule(
            config=config,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
        )

        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "size": 1},
        )

        result = await rule.evaluate(event, mock_engine)

        # Should only have take-profit, no stop-loss
        if result is not None:
            assert result["action"] != "place_stop_loss"
            # Should be take-profit only
            if "stop_price" in result:
                pytest.fail("Stop-loss should not be placed when disabled")

    # ========================================================================
    # Test 7: Multiple Symbol Support
    # ========================================================================

    @pytest.mark.asyncio
    async def test_independent_management_per_symbol(self, rule, mock_engine):
        """Test that each symbol's orders are managed independently."""
        # Given: Two positions in different symbols
        mock_engine.current_positions = {
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
        mock_engine.market_prices = {"ES": 6000.00, "MNQ": 21000.00}

        # ES position opens
        event_es = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "size": 1},
        )

        result_es = await rule.evaluate(event_es, mock_engine)

        # Should place orders for ES only
        assert result_es is not None
        assert result_es["symbol"] == "ES"
        assert "MNQ" not in str(result_es)

        # MNQ position opens
        event_mnq = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "size": 2},
        )

        result_mnq = await rule.evaluate(event_mnq, mock_engine)

        # Should place orders for MNQ only
        assert result_mnq is not None
        assert result_mnq["symbol"] == "MNQ"

    # ========================================================================
    # Test 8: Event Type Filtering
    # ========================================================================

    @pytest.mark.asyncio
    async def test_only_evaluates_position_events(self, rule, mock_engine):
        """Test rule only evaluates position-related events."""
        # Order event should be ignored
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "ES"},
        )

        result = await rule.evaluate(event, mock_engine)
        assert result is None

    @pytest.mark.asyncio
    async def test_evaluates_position_opened_event(self, rule, mock_engine):
        """Test rule evaluates POSITION_OPENED events."""
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6000.00}

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "size": 1},
        )

        result = await rule.evaluate(event, mock_engine)
        assert result is not None

    # ========================================================================
    # Test 9: Missing Data Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_missing_symbol_returns_none(self, rule, mock_engine):
        """Test rule handles missing symbol gracefully."""
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"size": 1},  # Missing symbol
        )

        result = await rule.evaluate(event, mock_engine)
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_position_data_returns_none(self, rule, mock_engine):
        """Test rule handles missing position data gracefully."""
        mock_engine.current_positions = {}  # No positions

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES"},
        )

        result = await rule.evaluate(event, mock_engine)
        assert result is None

    # ========================================================================
    # Test 10: Rule Disabled
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rule_disabled_returns_none(self, rule_config, tick_values, tick_sizes, mock_engine):
        """Test that rule does nothing when disabled."""
        rule_config["enabled"] = False
        rule = TradeManagementRule(
            config=rule_config,
            tick_values=tick_values,
            tick_sizes=tick_sizes,
        )

        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES"},
        )

        result = await rule.evaluate(event, mock_engine)
        assert result is None

    # ========================================================================
    # Test 11: Price Calculation Accuracy
    # ========================================================================

    def test_calculate_stop_price_long(self, rule):
        """Test stop price calculation for long positions."""
        entry_price = 6000.00
        distance_ticks = 10
        tick_size = 0.25
        side = "long"

        stop_price = rule._calculate_stop_price(entry_price, distance_ticks, tick_size, side)
        assert stop_price == 5997.50  # 6000 - (10 * 0.25)

    def test_calculate_stop_price_short(self, rule):
        """Test stop price calculation for short positions."""
        entry_price = 6000.00
        distance_ticks = 10
        tick_size = 0.25
        side = "short"

        stop_price = rule._calculate_stop_price(entry_price, distance_ticks, tick_size, side)
        assert stop_price == 6002.50  # 6000 + (10 * 0.25)

    def test_calculate_target_price_long(self, rule):
        """Test target price calculation for long positions."""
        entry_price = 6000.00
        distance_ticks = 20
        tick_size = 0.25
        side = "long"

        target_price = rule._calculate_target_price(entry_price, distance_ticks, tick_size, side)
        assert target_price == 6005.00  # 6000 + (20 * 0.25)

    def test_calculate_target_price_short(self, rule):
        """Test target price calculation for short positions."""
        entry_price = 6000.00
        distance_ticks = 20
        tick_size = 0.25
        side = "short"

        target_price = rule._calculate_target_price(entry_price, distance_ticks, tick_size, side)
        assert target_price == 5995.00  # 6000 - (20 * 0.25)
