"""
Unit Tests for DailyUnrealizedLossRule (RULE-004)

Tests the daily unrealized loss rule in isolation with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-004 - Daily Unrealized Loss (Stop Loss Per Position)
- Close losing positions when unrealized loss hits limit
- Trade-by-trade enforcement (close ONLY that losing position)
- No lockout (trader can continue trading)
- Requires real-time market data for unrealized P&L calculation

Key Difference from RULE-005:
- RULE-005: Triggers on unrealized_profit >= target (take profit)
- RULE-004: Triggers on unrealized_loss <= -limit (stop loss)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from risk_manager.rules.daily_unrealized_loss import DailyUnrealizedLossRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine
from risk_manager.core.config import RiskConfig


class TestDailyUnrealizedLossRule:
    """Unit tests for DailyUnrealizedLossRule."""

    @pytest.fixture
    def tick_values(self):
        """Tick values for futures contracts."""
        return {
            "MNQ": 5.0,   # $5 per tick
            "ES": 50.0,   # $50 per tick
            "NQ": 20.0,   # $20 per tick
            "RTY": 5.0,   # $5 per tick
        }

    @pytest.fixture
    def tick_sizes(self):
        """Tick sizes for futures contracts."""
        return {
            "MNQ": 0.25,
            "ES": 0.25,
            "NQ": 0.25,
            "RTY": 0.10,
        }

    @pytest.fixture
    def rule(self, tick_values, tick_sizes):
        """Create daily unrealized loss rule."""
        return DailyUnrealizedLossRule(
            loss_limit=-300.0,  # Stop loss at -$300 unrealized loss per position
            tick_values=tick_values,
            tick_sizes=tick_sizes,
            action="close_position"
        )

    @pytest.fixture
    def mock_engine(self):
        """Create mock risk engine with mocked trading_integration."""
        engine = Mock(spec=RiskEngine)
        engine.current_positions = {}
        engine.market_prices = {}  # Real-time market prices

        # Mock trading_integration for get_total_unrealized_pnl()
        # The rule now calls engine.trading_integration.get_total_unrealized_pnl()
        # We calculate it from mock_engine.current_positions and market_prices
        def calculate_total_pnl():
            total_pnl = 0.0
            for symbol, position in engine.current_positions.items():
                if symbol in engine.market_prices:
                    size = position.get("size", 0)
                    entry_price = position.get("avgPrice", 0)
                    current_price = engine.market_prices[symbol]

                    # Calculate P&L using tick economics
                    price_diff = current_price - entry_price
                    tick_size = 0.25  # Default for most contracts
                    tick_value = 5.0 if symbol == "MNQ" else 50.0  # MNQ=$5, ES=$50

                    ticks = price_diff / tick_size
                    position_pnl = ticks * size * tick_value
                    total_pnl += position_pnl

            return total_pnl

        engine.trading_integration = Mock()
        engine.trading_integration.get_total_unrealized_pnl = Mock(side_effect=calculate_total_pnl)

        return engine

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization(self, rule):
        """Test rule initializes with correct parameters."""
        assert rule.loss_limit == -300.0
        assert rule.action == "close_position"
        assert rule.name == "DailyUnrealizedLossRule"
        assert "MNQ" in rule.tick_values
        assert "ES" in rule.tick_values

    def test_rule_initialization_validates_negative_limit(self):
        """Test rule requires negative loss limit."""
        with pytest.raises((ValueError, AssertionError)):
            DailyUnrealizedLossRule(
                loss_limit=500.0,  # Positive limit should fail
                tick_values={"MNQ": 5.0},
                tick_sizes={"MNQ": 0.25},
            )

    # ========================================================================
    # Test 2: Loss Within Limit (Should PASS)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_loss_within_limit_passes(self, rule, mock_engine):
        """Test that unrealized loss within limit does not trigger violation."""
        # Given: MNQ Long 2 @ 21000.00, current price 20990.00
        # Unrealized P&L: -10 points / 0.25 = -40 ticks * 2 * $5 = -$400
        # Wait, that's -$400 which exceeds -$300 limit
        # Let's use smaller loss: 20995.00 (-5 points = -20 ticks * 2 * $5 = -$200)
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {
            "MNQ": 20995.00  # Down 5 points = -$200 loss
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 2,
                "avgPrice": 21000.00,
            },
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (loss = -$200 > limit = -$300, within limit)
        assert violation is None

    @pytest.mark.asyncio
    async def test_zero_loss_passes(self, rule, mock_engine):
        """Test that zero unrealized loss does not trigger violation."""
        # Given: MNQ Long 2 @ 21000.00, current price still 21000.00
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
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2, "avgPrice": 21000.00},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    @pytest.mark.asyncio
    async def test_profit_does_not_trigger(self, rule, mock_engine):
        """Test that unrealized profit does not trigger loss rule."""
        # Given: MNQ Long 2 @ 21000.00, current price 21050.00 (profit)
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 21050.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2, "avgPrice": 21000.00},
        )

        violation = await rule.evaluate(event, mock_engine)
        # Should not violate (we have profit, not loss)
        assert violation is None

    # ========================================================================
    # Test 3: Loss At Exact Limit (Should VIOLATE - edge case)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_loss_at_exact_limit_violates(self, rule, mock_engine):
        """Test that loss at exact limit triggers violation (<= check)."""
        # Given: MNQ Long 2 @ 21000.00, current price 20970.00
        # Unrealized P&L: -30 points / 0.25 = -120 ticks * 2 * $5 = -$1200
        # Wait, that's too much. Let's calculate for exactly -$300:
        # -$300 / (2 contracts * $5) = -30 ticks
        # -30 ticks * 0.25 = -7.5 points
        # Price = 21000.00 - 7.5 = 20992.50
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 20992.50}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2, "avgPrice": 21000.00},
        )

        violation = await rule.evaluate(event, mock_engine)

        # At exact limit, should trigger (<= comparison)
        assert violation is not None
        assert abs(violation["current_pnl"] - (-300.0)) < 0.01

    # ========================================================================
    # Test 4: Loss Exceeds Limit (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_loss_exceeds_limit_violates(self, rule, mock_engine):
        """Test that unrealized loss exceeding limit triggers violation."""
        # Given: MNQ Long 2 @ 21000.00, current price 20970.00
        # Unrealized P&L: -30 points / 0.25 = -120 ticks * 2 * $5 = -$1200
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 20970.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2, "avgPrice": 21000.00},
        )

        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["action"] == "close_position"
        assert violation["symbol"] == "MNQ"
        assert violation["current_pnl"] <= -1200.0
        assert violation["loss_limit"] == -300.0
        assert "loss limit" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_short_position_loss_exceeds_limit(self, rule, mock_engine):
        """Test short position loss calculation."""
        # Given: ES Short 1 @ 6000.00, current price 6010.00
        # Unrealized P&L: (6000 - 6010) = -10 points = -40 ticks * $50 = -$2000
        mock_engine.current_positions = {
            "ES": {
                "size": -1,  # Short position
                "side": "short",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6010.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": -1, "avgPrice": 6000.00},
        )

        violation = await rule.evaluate(event, mock_engine)

        # Should violate (loss <= -$300)
        assert violation is not None
        assert violation["current_pnl"] <= -2000.0

    # ========================================================================
    # Test 5: Violation Closes Only That Position (Trade-by-Trade)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_targets_specific_position_only(self, rule, mock_engine):
        """Test violation specifies ONLY the losing position to close."""
        # Given: Multiple positions, only MNQ hits loss limit
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            },
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            },
        }
        mock_engine.market_prices = {
            "MNQ": 20970.00,  # -$1200 loss (hit limit)
            "ES": 6002.50,    # $500 profit (no issue)
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "size": 2, "avgPrice": 21000.00},
        )

        violation = await rule.evaluate(event, mock_engine)

        # Should close ONLY MNQ position
        assert violation is not None
        assert violation["symbol"] == "MNQ"
        assert violation["contractId"] == "CON.F.US.MNQ.U25"
        # Should NOT mention ES
        assert "ES" not in violation.get("message", "")

    # ========================================================================
    # Test 6: No Lockout Created
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_does_not_create_lockout(self, rule, mock_engine):
        """Test that violation does NOT create lockout (trade-by-trade mode)."""
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 20970.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)

        # Violation should NOT include lockout
        assert violation is not None
        assert "lockout" not in violation or violation.get("lockout") is None

    # ========================================================================
    # Test 7: Multi-Symbol Loss Tracking
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_symbol_independent_tracking(self, rule, mock_engine):
        """Test each symbol tracked independently."""
        # Given: Two positions, both losing but only one hits limit
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            },
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            },
        }
        mock_engine.market_prices = {
            "MNQ": 20970.00,  # -$1200 loss (exceeds -$300 limit)
            "ES": 5997.50,    # -$500 loss (exceeds -$300 limit too)
        }

        # Check MNQ - should violate
        event_mnq = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )
        violation_mnq = await rule.evaluate(event_mnq, mock_engine)
        assert violation_mnq is not None
        assert violation_mnq["symbol"] == "MNQ"

        # Check ES - should also violate (independent tracking)
        event_es = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES"},
        )
        violation_es = await rule.evaluate(event_es, mock_engine)
        assert violation_es is not None
        assert violation_es["symbol"] == "ES"

    # ========================================================================
    # Test 8: Unrealized P&L Calculation Accuracy
    # ========================================================================

    @pytest.mark.asyncio
    async def test_long_position_pnl_calculation(self, rule, mock_engine):
        """Test unrealized P&L calculation for long positions with loss."""
        # MNQ Long: entry 21000, current 20970, 2 contracts
        # P&L = (20970 - 21000) / 0.25 * 2 * 5 = -120 ticks * 2 * $5 = -$1200
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 20970.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is not None
        # Allow small floating point difference
        assert abs(violation["current_pnl"] - (-1200.0)) < 0.01

    @pytest.mark.asyncio
    async def test_es_position_pnl_calculation(self, rule, mock_engine):
        """Test unrealized P&L calculation for ES with loss."""
        # ES Long: entry 6000, current 5990, 1 contract
        # P&L = (5990 - 6000) / 0.25 * 1 * 50 = -40 ticks * $50 = -$2000
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 5990.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is not None
        assert abs(violation["current_pnl"] - (-2000.0)) < 0.01

    # ========================================================================
    # Test 9: Event Type Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_only_evaluates_position_events(self, rule, mock_engine):
        """Test rule only evaluates position-related events."""
        # Non-position event should be ignored
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    @pytest.mark.asyncio
    async def test_evaluates_position_updated_event(self, rule, mock_engine):
        """Test rule evaluates POSITION_UPDATED events."""
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 20970.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is not None

    # ========================================================================
    # Test 10: Missing Market Data Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_missing_market_price_returns_none(self, rule, mock_engine):
        """Test rule handles missing market price gracefully."""
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {}  # No market price available

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )

        # Should not crash, return None (can't calculate without price)
        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    @pytest.mark.asyncio
    async def test_missing_position_data_returns_none(self, rule, mock_engine):
        """Test rule handles missing position data gracefully."""
        mock_engine.current_positions = {}
        mock_engine.market_prices = {"MNQ": 20970.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    # ========================================================================
    # Test 11: Small Loss Within Limit
    # ========================================================================

    @pytest.mark.asyncio
    async def test_small_loss_within_limit(self, rule, mock_engine):
        """Test small unrealized loss does not trigger violation."""
        # Given: MNQ Long 2 @ 21000.00, current 20998.75
        # Loss: -1.25 points = -5 ticks * 2 * $5 = -$50
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 20998.75}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    # ========================================================================
    # Test 12: Disabled Rule Does Not Trigger
    # ========================================================================

    @pytest.mark.asyncio
    async def test_disabled_rule_does_not_trigger(self, rule, mock_engine):
        """Test disabled rule does not trigger violations."""
        rule.enabled = False

        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 20970.00}  # Big loss

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    # ========================================================================
    # Test 13: Rule Name
    # ========================================================================

    def test_rule_name(self, rule):
        """Test rule has correct name."""
        assert rule.name == "DailyUnrealizedLossRule"

    # ========================================================================
    # Test 14: RTY Symbol with Different Tick Size
    # ========================================================================

    @pytest.mark.asyncio
    async def test_rty_symbol_tick_calculation(self, rule, mock_engine):
        """Test RTY symbol with tick size 0.10 instead of 0.25."""
        # RTY Long: entry 2000.00, current 1990.00, 2 contracts
        # Loss: -10 points / 0.10 = -100 ticks * 2 * $5 = -$1000
        mock_engine.current_positions = {
            "RTY": {
                "size": 2,
                "side": "long",
                "avgPrice": 2000.00,
                "contractId": "CON.F.US.RTY.H25",
            }
        }
        mock_engine.market_prices = {"RTY": 1990.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "RTY"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is not None
        assert abs(violation["current_pnl"] - (-1000.0)) < 0.01

    # ========================================================================
    # Test 15: Position Opened Event
    # ========================================================================

    @pytest.mark.asyncio
    async def test_evaluates_position_opened_event(self, rule, mock_engine):
        """Test rule evaluates POSITION_OPENED events."""
        mock_engine.current_positions = {
            "MNQ": {
                "size": 2,
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 20970.00}

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is not None

    # ========================================================================
    # Test 16: Zero Size Position
    # ========================================================================

    @pytest.mark.asyncio
    async def test_zero_size_position_returns_zero_pnl(self, rule, mock_engine):
        """Test zero size position returns zero P&L."""
        mock_engine.current_positions = {
            "MNQ": {
                "size": 0,  # Zero position
                "side": "long",
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25",
            }
        }
        mock_engine.market_prices = {"MNQ": 20970.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None  # Zero position = no loss
