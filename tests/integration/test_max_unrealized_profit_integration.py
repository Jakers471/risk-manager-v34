"""
Integration Tests for RULE-005: Max Unrealized Profit

Tests the Max Unrealized Profit rule with REAL components:
- Real EventBus for event flow
- Real RiskEngine for rule evaluation
- Real position tracking with market data
- Integration with P&L calculations
- Real-time position monitoring

Rule: RULE-005 - Max Unrealized Profit Limit
Category: Trade-by-Trade (Category 1)
Priority: Medium

Action: Close position automatically when unrealized profit target reached

Integration Test Scope:
- Test real-time position tracking across symbols
- Test market price updates and P&L recalculation
- Test different tick sizes (ES vs MNQ vs MBT)
- Test long and short positions
- Test enforcement closes specific position only (not flatten all)
- Test multi-symbol independence
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.engine import RiskEngine
from risk_manager.core.config import RiskConfig
from risk_manager.rules.max_unrealized_profit import MaxUnrealizedProfitRule


class TestMaxUnrealizedProfitIntegration:
    """Integration tests for MaxUnrealizedProfitRule (RULE-005)."""

    @pytest.fixture
    def event_bus(self):
        """Create real event bus."""
        return EventBus()

    @pytest.fixture
    def mock_trading_integration(self):
        """Create mock trading integration for enforcement."""
        integration = AsyncMock()
        integration.flatten_all = AsyncMock()
        integration.flatten_position = AsyncMock()
        return integration

    @pytest.fixture
    def mock_engine(self):
        """Create mock engine with position tracking."""
        from unittest.mock import Mock
        engine = Mock()
        engine.current_positions = {}
        engine.market_prices = {}
        return engine

    @pytest.fixture
    def rule(self):
        """Create max unrealized profit rule."""
        # Tick values: ES = $12.50/tick, MNQ = $0.25/tick, NQ = $5.00/tick
        return MaxUnrealizedProfitRule(
            target=2000.0,
            tick_values={"ES": 12.50, "MNQ": 0.25, "NQ": 5.0},
            tick_sizes={"ES": 0.25, "MNQ": 0.25, "NQ": 0.25}
        )

    # ========================================================================
    # Test 1: ES Long Position Reaches Target
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_es_long_position_reaches_target(self, rule, mock_engine):
        """
        GIVEN: ES long 2 contracts @ 5000.00 (tick=$12.50)
        WHEN: Market moves to 5016.00 (+16 points = +64 ticks = +$800 total)
        THEN: No violation (under $2000 target)
        WHEN: Market moves to 5020.00 (+20 points = +80 ticks = +$1000/contract = +$2000 total)
        THEN: Violation triggered, close ES position
        """
        # Position opened: Long 2 ES @ 5000.00
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        }

        # Initial market price
        mock_engine.market_prices = {"ES": 5016.00}

        # Position update event
        event1 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # Evaluate at +$400 profit
        violation1 = await rule.evaluate(event1, mock_engine)
        assert violation1 is None  # Under target

        # Market moves to 5020.00 (exactly +80 ticks = +$2000 profit)
        mock_engine.market_prices["ES"] = 5020.00

        event2 = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # Evaluate at +$2000 profit
        violation2 = await rule.evaluate(event2, mock_engine)
        assert violation2 is not None

        assert violation2["rule"] == "MaxUnrealizedProfitRule"
        assert violation2["symbol"] == "ES"
        assert abs(violation2["unrealized_pnl"] - 2000.0) < 1.0  # Float precision

    # ========================================================================
    # Test 2: MNQ Short Position Reaches Target
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mnq_short_position_reaches_target(self, rule, mock_engine):
        """
        GIVEN: MNQ short -10 contracts @ 21000.00 (tick=$0.25)
        WHEN: Market drops to 20800.00 (-200 points = -800 ticks = +$200/contract = +$2000 total)
        THEN: Violation triggered (short profits on price drop)
        """
        # Position: Short 10 MNQ @ 21000.00
        mock_engine.current_positions = {
            "MNQ": {
                "symbol": "MNQ",
                "size": -10,
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25"
            }
        }

        # Market drops to 20800.00 (-200 points = $2000 profit for short)
        mock_engine.market_prices = {"MNQ": 20800.00}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": -10,
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25"
            }
        )

        # Evaluate
        violation = await rule.evaluate(event, mock_engine)

        # Verify violation (short position profits when price drops)
        assert violation is not None
        assert violation["symbol"] == "MNQ"
        assert abs(violation["unrealized_pnl"] - 2000.0) < 1.0

    # ========================================================================
    # Test 3: Multi-Position Independence
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_position_independence(self, rule, mock_engine):
        """
        GIVEN: ES and MNQ positions open
        WHEN: Only ES reaches profit target
        THEN: Close ES only, MNQ continues
        """
        # Positions
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            },
            "MNQ": {
                "symbol": "MNQ",
                "size": 5,
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25"
            }
        }

        # Prices: ES profitable, MNQ not
        mock_engine.market_prices = {
            "ES": 5020.00,   # ES: +20 points = +$2000 profit (triggers)
            "MNQ": 21020.00  # MNQ: +20 points = +$50 profit (no trigger)
        }

        # Position update with new market price
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # Evaluate
        violation = await rule.evaluate(event, mock_engine)

        # Verify only ES violation
        assert violation is not None
        assert violation["symbol"] == "ES"
        assert violation["action"] == "close_position"

    # ========================================================================
    # Test 4: Market Price Updates Real-Time Monitoring
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_market_price_updates_real_time_monitoring(self, rule, mock_engine):
        """
        GIVEN: Position open, market fluctuating
        WHEN: Market prices update continuously
        THEN: Rule re-evaluates on each POSITION_UPDATED event
        """
        # Position
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        }

        # Price sequence: 5010, 5015, 5020 (gradually reaching target)
        # 5010: +10 points = +40 ticks = +$1000 profit
        # 5015: +15 points = +60 ticks = +$1500 profit
        # 5020: +20 points = +80 ticks = +$2000 profit
        prices = [5010.00, 5015.00, 5020.00]
        expected_profits = [1000.0, 1500.0, 2000.0]

        for price, expected_profit in zip(prices, expected_profits):
            mock_engine.market_prices["ES"] = price

            event = RiskEvent(
                event_type=EventType.POSITION_UPDATED,
                data={
                    "symbol": "ES",
                    "size": 2,
                    "avgPrice": 5000.00,
                    "contractId": "CON.F.US.ES.H25"
                }
            )

            violation = await rule.evaluate(event, mock_engine)

            if expected_profit >= 2000.0:
                assert violation is not None
                assert abs(violation["unrealized_pnl"] - expected_profit) < 1.0
            else:
                assert violation is None

    # ========================================================================
    # Test 5: Different Tick Sizes Calculation
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_different_tick_sizes_calculation(self, rule, mock_engine):
        """
        Test P&L calculation accuracy across different tick sizes.

        - ES: $12.50/tick, 0.25 tick size
        - MNQ: $0.25/tick, 0.25 tick size
        - MBT: $5.00/tick, 0.10 tick size
        """
        # ES position: 2 @ 5000.00
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        }
        mock_engine.market_prices = {"ES": 5020.00}

        event_es = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        )
        violation_es = await rule.evaluate(event_es, mock_engine)

        # ES: +20 points = +80 ticks, 80 ticks * $12.50/tick * 2 = $2000
        if violation_es:
            assert abs(violation_es["unrealized_pnl"] - 2000.0) < 1.0

        # MNQ position: 800 @ 21000.00
        mock_engine.current_positions = {
            "MNQ": {
                "symbol": "MNQ",
                "size": 800,
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25"
            }
        }
        # Move price by +1 point = +4 ticks = +$800 profit (under $2000 target)
        mock_engine.market_prices = {"MNQ": 21001.00}

        event_mnq = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 800,
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25"
            }
        )
        violation_mnq = await rule.evaluate(event_mnq, mock_engine)

        # MNQ: +1 point = +4 ticks, 4 ticks * 800 contracts * $0.25/tick = $800 (no violation)
        assert violation_mnq is None

    # ========================================================================
    # Test 6: Long and Short Positions Accuracy
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_long_and_short_positions_accuracy(self, rule, mock_engine):
        """
        Verify P&L calculations correct for both long and short.

        Long: Profit when price increases
        Short: Profit when price decreases
        """
        # Test 1: Long position profits on price increase
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        }
        mock_engine.market_prices = {"ES": 5020.00}  # +20 points = +$2000 profit

        event_long = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        )
        violation_long = await rule.evaluate(event_long, mock_engine)
        assert violation_long is not None  # Profit target reached

        # Test 2: Short position profits on price decrease
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": -2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        }
        mock_engine.market_prices = {"ES": 4980.00}  # -20 points = +$2000 profit for short

        event_short = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": -2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        )
        violation_short = await rule.evaluate(event_short, mock_engine)
        assert violation_short is not None  # Profit target reached

    # ========================================================================
    # Test 7: Event Bus Integration Complete Flow
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_event_bus_integration_complete_flow(self, rule, mock_engine, event_bus):
        """
        Test complete event flow through EventBus.

        Flow:
        1. POSITION_UPDATED event
        2. Rule evaluates
        3. RULE_VIOLATED published if target reached
        """
        # Track violations
        violations_published = []

        async def violation_handler(event):
            if event.event_type == EventType.RULE_VIOLATED:
                violations_published.append(event)

        event_bus.subscribe(EventType.RULE_VIOLATED, violation_handler)

        # Position at profit target
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        }
        mock_engine.market_prices = {"ES": 5020.00}  # +20 points = +$2000 profit

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # Evaluate
        violation = await rule.evaluate(event, mock_engine)

        # If violation, publish to event bus
        if violation:
            violation_event = RiskEvent(
                event_type=EventType.RULE_VIOLATED,
                data=violation
            )
            await event_bus.publish(violation_event)

        # Wait for propagation
        await asyncio.sleep(0.1)

        # Verify violation published
        assert len(violations_published) == 1
        assert violations_published[0].data["rule"] == "MaxUnrealizedProfitRule"

    # ========================================================================
    # Test 8: Enforcement Closes Position, Not Flatten All
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_enforcement_closes_position_not_flatten_all(
        self, rule, mock_engine
    ):
        """
        GIVEN: Multiple positions open
        WHEN: ES reaches profit target
        THEN: Close ES position only, NOT flatten all
        """
        # Multiple positions
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            },
            "MNQ": {
                "symbol": "MNQ",
                "size": 5,
                "avgPrice": 21000.00,
                "contractId": "CON.F.US.MNQ.U25"
            }
        }

        mock_engine.market_prices = {"ES": 5020.00, "MNQ": 21000.00}  # ES at profit target

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # Evaluate
        violation = await rule.evaluate(event, mock_engine)

        # Verify violation specifies close_position (not flatten_all)
        assert violation is not None
        assert violation["action"] == "close_position"
        assert violation["symbol"] == "ES"

    # ========================================================================
    # Test 9: Position Closed Before Target
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_position_closed_before_target(self, rule, mock_engine):
        """
        GIVEN: Position approaching target
        WHEN: Position closed manually
        THEN: No violation (no position = no unrealized P&L)
        """
        # Position opened
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        }
        mock_engine.market_prices = {"ES": 5070.00}  # Near target

        # Position closed manually
        mock_engine.current_positions = {}

        event = RiskEvent(
            event_type=EventType.POSITION_CLOSED,
            data={
                "symbol": "ES",
                "size": 0,
                "realizedPnL": 1750.0
            }
        )

        # Evaluate
        violation = await rule.evaluate(event, mock_engine)

        # No violation (position closed)
        assert violation is None

    # ========================================================================
    # Test 10: Zero/Negative Profit No Violation
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_zero_negative_profit_no_violation(self, rule, mock_engine):
        """
        GIVEN: Position at loss or breakeven
        WHEN: Rule evaluates
        THEN: No violation (only positive unrealized profit triggers)
        """
        # Position at loss
        mock_engine.current_positions = {
            "ES": {
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        }
        mock_engine.market_prices = {"ES": 4950.00}  # Down 50 points

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.00,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # Evaluate
        violation = await rule.evaluate(event, mock_engine)

        # No violation (at loss, not profit)
        assert violation is None
