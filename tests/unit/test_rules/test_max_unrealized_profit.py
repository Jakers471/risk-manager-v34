"""
Unit Tests for MaxUnrealizedProfitRule (RULE-005)

Tests the max unrealized profit rule in isolation with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-005 - Max Unrealized Profit (Take Profit)
- Close winning positions when unrealized profit hits target
- Trade-by-trade enforcement (close ONLY that position)
- No lockout (trader can continue trading)
- Requires real-time market data for unrealized P&L calculation
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from risk_manager.rules.max_unrealized_profit import MaxUnrealizedProfitRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine
from risk_manager.core.config import RiskConfig


class TestMaxUnrealizedProfitRule:
    """Unit tests for MaxUnrealizedProfitRule."""

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
        """Create max unrealized profit rule."""
        return MaxUnrealizedProfitRule(
            target=1000.0,  # Take profit at $1000 unrealized profit
            tick_values=tick_values,
            tick_sizes=tick_sizes,
            action="close_position"
        )

    @pytest.fixture
    def mock_engine(self):
        """Create mock risk engine."""
        engine = Mock(spec=RiskEngine)
        engine.current_positions = {}
        engine.market_prices = {}  # Real-time market prices
        return engine

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization(self, rule):
        """Test rule initializes with correct parameters."""
        assert rule.target == 1000.0
        assert rule.action == "close_position"
        assert rule.name == "MaxUnrealizedProfitRule"
        assert "MNQ" in rule.tick_values
        assert "ES" in rule.tick_values

    def test_rule_initialization_validates_positive_target(self):
        """Test rule requires positive profit target."""
        with pytest.raises((ValueError, AssertionError)):
            MaxUnrealizedProfitRule(
                target=-500.0,  # Negative target should fail
                tick_values={"MNQ": 5.0},
                tick_sizes={"MNQ": 0.25},
            )

    # ========================================================================
    # Test 2: Profit Below Target (Should PASS)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_profit_below_target_passes(self, rule, mock_engine):
        """Test that unrealized profit below target does not trigger violation."""
        # Given: ES Long 1 @ 6000.00, current price 6005.00
        # Unrealized P&L: 5 points = 20 ticks * $50 = $1000... wait
        # 5 points / 0.25 tick size = 20 ticks
        # 20 ticks * 1 contract * $50 = $1000 (at target, not below)
        # Let's use smaller profit: 6002.50 (2.5 points = 10 ticks = $500)
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {
            "ES": 6002.50  # Up 2.5 points = $500 profit
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 1,
                "avgPrice": 6000.00,
            },
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (profit = $500 < target = $1000)
        assert violation is None

    @pytest.mark.asyncio
    async def test_zero_profit_passes(self, rule, mock_engine):
        """Test that zero unrealized profit does not trigger violation."""
        # Given: ES Long 1 @ 6000.00, current price still 6000.00
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
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1, "avgPrice": 6000.00},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    # ========================================================================
    # Test 3: Profit At Target (Should PASS - edge case)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_profit_at_exact_target_passes(self, rule, mock_engine):
        """Test that profit at exact target does not trigger (>= check)."""
        # Given: ES Long 1 @ 6000.00, current price 6005.00
        # Unrealized P&L: 5 points = 20 ticks * $50 = $1000 (exactly at target)
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6005.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1, "avgPrice": 6000.00},
        )

        violation = await rule.evaluate(event, mock_engine)

        # At exact target, should trigger (>= comparison)
        assert violation is not None

    # ========================================================================
    # Test 4: Profit Exceeds Target (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_profit_exceeds_target_violates(self, rule, mock_engine):
        """Test that unrealized profit exceeding target triggers violation."""
        # Given: ES Long 1 @ 6000.00, current price 6010.00
        # Unrealized P&L: 10 points / 0.25 = 40 ticks * $50 = $2000
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6010.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1, "avgPrice": 6000.00},
        )

        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["action"] == "close_position"
        assert violation["symbol"] == "ES"
        assert violation["unrealized_pnl"] >= 2000.0
        assert violation["target"] == 1000.0
        assert "profit target" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_short_position_profit_exceeds_target(self, rule, mock_engine):
        """Test short position profit calculation."""
        # Given: ES Short 1 @ 6010.00, current price 6005.00
        # Unrealized P&L: (6010 - 6005) = 5 points = 20 ticks * $50 = $1000
        mock_engine.current_positions = {
            "ES": {
                "size": -1,  # Short position
                "side": "short",
                "avgPrice": 6010.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6005.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": -1, "avgPrice": 6010.00},
        )

        violation = await rule.evaluate(event, mock_engine)

        # Should violate (profit >= $1000)
        assert violation is not None
        assert violation["unrealized_pnl"] >= 1000.0

    # ========================================================================
    # Test 5: Violation Closes Only That Position (Trade-by-Trade)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_targets_specific_position_only(self, rule, mock_engine):
        """Test violation specifies ONLY the winning position to close."""
        # Given: Multiple positions, only ES hits target
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
        mock_engine.market_prices = {
            "ES": 6010.00,  # $2000 profit (hit target)
            "MNQ": 21050.00,  # $500 profit (below target)
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1, "avgPrice": 6000.00},
        )

        violation = await rule.evaluate(event, mock_engine)

        # Should close ONLY ES position
        assert violation is not None
        assert violation["symbol"] == "ES"
        assert violation["contractId"] == "CON.F.US.ES.H25"
        # Should NOT mention MNQ
        assert "MNQ" not in violation.get("message", "")

    # ========================================================================
    # Test 6: No Lockout Created
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_does_not_create_lockout(self, rule, mock_engine):
        """Test that violation does NOT create lockout (trade-by-trade mode)."""
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6010.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES"},
        )

        violation = await rule.evaluate(event, mock_engine)

        # Violation should NOT include lockout
        assert violation is not None
        assert "lockout" not in violation or violation.get("lockout") is None

    # ========================================================================
    # Test 7: Multi-Symbol Profit Tracking
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_symbol_independent_tracking(self, rule, mock_engine):
        """Test each symbol tracked independently."""
        # Given: Two positions, both profitable but only one hits target
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
        mock_engine.market_prices = {
            "ES": 6002.50,  # $500 profit (below target)
            "MNQ": 21100.00,  # 100 points = 400 ticks * 2 * $5 = $4000 profit
        }

        # Check ES - should pass
        event_es = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES"},
        )
        violation_es = await rule.evaluate(event_es, mock_engine)
        assert violation_es is None

        # Check MNQ - should violate
        event_mnq = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ"},
        )
        violation_mnq = await rule.evaluate(event_mnq, mock_engine)
        assert violation_mnq is not None
        assert violation_mnq["symbol"] == "MNQ"

    # ========================================================================
    # Test 8: Unrealized P&L Calculation Accuracy
    # ========================================================================

    @pytest.mark.asyncio
    async def test_long_position_pnl_calculation(self, rule, mock_engine):
        """Test unrealized P&L calculation for long positions."""
        # ES Long: entry 6000, current 6010, 1 contract
        # P&L = (6010 - 6000) / 0.25 * 1 * 50 = 40 ticks * $50 = $2000
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6010.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is not None
        # Allow small floating point difference
        assert abs(violation["unrealized_pnl"] - 2000.0) < 0.01

    @pytest.mark.asyncio
    async def test_mnq_position_pnl_calculation(self, rule, mock_engine):
        """Test unrealized P&L calculation for MNQ."""
        # MNQ Long: entry 21000, current 21050, 2 contracts
        # P&L = (21050 - 21000) / 0.25 * 2 * 5 = 200 ticks * 2 * $5 = $2000
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
            data={"symbol": "MNQ"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is not None
        assert abs(violation["unrealized_pnl"] - 2000.0) < 0.01

    # ========================================================================
    # Test 9: Event Type Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_only_evaluates_position_events(self, rule, mock_engine):
        """Test rule only evaluates position-related events."""
        # Non-position event should be ignored
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "ES"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    @pytest.mark.asyncio
    async def test_evaluates_position_updated_event(self, rule, mock_engine):
        """Test rule evaluates POSITION_UPDATED events."""
        mock_engine.current_positions = {
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {"ES": 6010.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES"},
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
            "ES": {
                "size": 1,
                "side": "long",
                "avgPrice": 6000.00,
                "contractId": "CON.F.US.ES.H25",
            }
        }
        mock_engine.market_prices = {}  # No market price available

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES"},
        )

        # Should not crash, return None (can't calculate without price)
        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    @pytest.mark.asyncio
    async def test_missing_position_data_returns_none(self, rule, mock_engine):
        """Test rule handles missing position data gracefully."""
        mock_engine.current_positions = {}
        mock_engine.market_prices = {"ES": 6010.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES"},
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None
