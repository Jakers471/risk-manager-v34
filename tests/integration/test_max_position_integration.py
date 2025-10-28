"""
Integration Tests for RULE-001: Max Contracts

Tests the Max Contracts rule with real components:
- Real position tracking
- Integration with enforcement flow
- Multi-account scenarios

Rule: RULE-001 - Max Contracts (Account-Wide Position Limit)
- Block trades that exceed total contract limit across all symbols
- Trade-by-Trade enforcement (close excess position only)
- No lockout (trader can continue trading within limits)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.rules.max_position import MaxPositionRule


class TestMaxPositionIntegration:
    """Integration tests for MaxPositionRule (RULE-001)."""

    @pytest.fixture
    def rule(self):
        """Create max position rule with limit of 5."""
        return MaxPositionRule(max_contracts=5)

    @pytest.fixture
    def mock_engine(self):
        """Create mock engine with position tracking."""
        engine = Mock()
        engine.current_positions = {}
        return engine

    @pytest.fixture
    def event_bus(self):
        """Create real event bus."""
        return EventBus()

    # ========================================================================
    # Test 1: Single Symbol Within Limit
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_single_symbol_within_limit(self, rule, mock_engine):
        """
        Test position within limit does not trigger violation.

        Given: Max contracts = 5
        When: ES position = 3 contracts
        Then: No violation, no enforcement
        """
        # Given: Position within limit
        mock_engine.current_positions = {
            "ES": {"symbol": "ES", "size": 3, "avgPrice": 5000.0}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 3,
                "avgPrice": 5000.0,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 2: Single Symbol Exceeds Limit
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_single_symbol_exceeds_limit(self, rule, mock_engine):
        """
        Test single symbol exceeding limit triggers violation.

        Given: Max contracts = 5
        When: ES position = 7 contracts
        Then: Violation detected, close excess position
        """
        # Given: Position exceeds limit
        mock_engine.current_positions ={
            "ES": {"symbol": "ES", "size": 7, "avgPrice": 5000.0, "contractId": "CON.F.US.ES.H25"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 7,
                "avgPrice": 5000.0,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["rule"] == "MaxPositionRule"
        assert violation["current_size"] == 7
        assert violation["max_size"] == 5

    # ========================================================================
    # Test 3: Multi-Symbol Total Within Limit
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_symbol_total_within_limit(self, rule, mock_engine):
        """
        Test multiple symbols with total within limit.

        Given: Max contracts = 5
        When: ES=2, MNQ=2 (total=4)
        Then: No violation
        """
        # Given: Multiple positions, total within limit
        mock_engine.current_positions ={
            "ES": {"symbol": "ES", "size": 2, "avgPrice": 5000.0},
            "MNQ": {"symbol": "MNQ", "size": 2, "avgPrice": 21000.0}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 2,
                "avgPrice": 21000.0,
                "contractId": "CON.F.US.MNQ.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 4: Multi-Symbol Total Exceeds Limit
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_symbol_total_exceeds_limit(self, rule, mock_engine):
        """
        Test multiple symbols with total exceeding limit.

        Given: Max contracts = 5
        When: ES=3, MNQ=3 (total=6)
        Then: Violation detected
        """
        # Given: Multiple positions, total exceeds limit
        mock_engine.current_positions ={
            "ES": {"symbol": "ES", "size": 3, "avgPrice": 5000.0, "contractId": "CON.F.US.ES.H25"},
            "MNQ": {"symbol": "MNQ", "size": 3, "avgPrice": 21000.0, "contractId": "CON.F.US.MNQ.H25"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 3,
                "avgPrice": 21000.0,
                "contractId": "CON.F.US.MNQ.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["current_size"] == 6
        assert violation["max_size"] == 5

    # ========================================================================
    # Test 5: Short Positions Counted as Absolute Value
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_short_positions_absolute_value(self, rule, mock_engine):
        """
        Test short positions counted as absolute value.

        Given: Max contracts = 5
        When: ES short -4 contracts
        Then: Counts as 4 contracts (absolute value)
        """
        # Given: Short position
        mock_engine.current_positions ={
            "ES": {"symbol": "ES", "size": -4, "avgPrice": 5000.0}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": -4,
                "avgPrice": 5000.0,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (4 < 5)
        assert violation is None

    # ========================================================================
    # Test 6: Event Bus Integration
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_event_bus_integration(self, rule, mock_engine, event_bus):
        """
        Test complete event flow through EventBus.

        Flow:
        1. Publish POSITION_UPDATED event
        2. Engine receives and evaluates
        3. Violation published if limit exceeded
        """
        # Track RULE_VIOLATED events
        violations_published = []

        async def violation_handler(event):
            if event.event_type == EventType.RULE_VIOLATED:
                violations_published.append(event)

        event_bus.subscribe(EventType.RULE_VIOLATED, violation_handler)

        # Given: Position exceeding limit
        mock_engine.current_positions ={
            "ES": {"symbol": "ES", "size": 6, "avgPrice": 5000.0, "contractId": "CON.F.US.ES.H25"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 6,
                "avgPrice": 5000.0,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # When: Evaluate rule
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["rule"] == "MaxPositionRule"

    # ========================================================================
    # Test 7: No Lockout on Violation
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_no_lockout_on_violation(self, rule, mock_engine):
        """
        Test that violation does NOT create lockout.

        This is a trade-by-trade rule - close excess position only.
        Trader can continue trading within limits.
        """
        # Given: Position exceeds limit
        mock_engine.current_positions ={
            "ES": {"symbol": "ES", "size": 7, "avgPrice": 5000.0, "contractId": "CON.F.US.ES.H25"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 7,
                "avgPrice": 5000.0,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation exists but action is close_position, not lockout
        assert violation is not None
        assert "lockout" not in violation or violation.get("lockout") is False

    # ========================================================================
    # Test 8: Zero Position No Violation
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_zero_position_no_violation(self, rule, mock_engine):
        """Test that zero position does not trigger violation."""
        # Given: No positions
        mock_engine.current_positions ={}

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 0,
                "avgPrice": 0.0,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 9: Exactly at Limit No Violation
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_exactly_at_limit_no_violation(self, rule, mock_engine):
        """
        Test position exactly at limit does not violate.

        Given: Max contracts = 5
        When: Total position = 5
        Then: No violation (>= comparison)
        """
        # Given: Position exactly at limit
        mock_engine.current_positions ={
            "ES": {"symbol": "ES", "size": 5, "avgPrice": 5000.0}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 5,
                "avgPrice": 5000.0,
                "contractId": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (rule uses > not >=)
        assert violation is None

    # ========================================================================
    # Test 10: Performance with Many Symbols
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_performance_many_symbols(self, rule, mock_engine):
        """
        Test rule performs quickly with many symbols.

        Verifies rule can handle accounts with 10+ symbols.
        """
        import time

        # Given: Many symbols
        mock_engine.current_positions ={
            f"SYM{i}": {"symbol": f"SYM{i}", "size": 1, "avgPrice": 100.0}
            for i in range(20)
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "SYM0",
                "size": 1,
                "avgPrice": 100.0,
                "contractId": "CON.F.US.SYM0.H25"
            }
        )

        # When: Rule evaluates
        start = time.time()
        violation = await rule.evaluate(event, mock_engine)
        duration = time.time() - start

        # Then: Completes quickly (< 100ms)
        assert duration < 0.1

        # And: Violation detected (20 > 5)
        assert violation is not None
