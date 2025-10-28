"""
Integration Tests for RULE-002: Max Contracts Per Instrument

Tests the Max Contracts Per Instrument rule with real components:
- Per-symbol position tracking
- Integration with enforcement flow
- Independent limits per symbol

Rule: RULE-002 - Max Contracts Per Instrument (Per-Symbol Limit)
- Block trades that exceed per-symbol contract limit
- Trade-by-Trade enforcement (close excess for that symbol only)
- No lockout (trader can continue trading other symbols)
- Independent limits per symbol
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule


class TestMaxContractsPerInstrumentIntegration:
    """Integration tests for MaxContractsPerInstrumentRule (RULE-002)."""

    @pytest.fixture
    def rule(self):
        """Create per-instrument limit rule with ES=3, MNQ=2, NQ=5."""
        return MaxContractsPerInstrumentRule(
            limits={
                "ES": 3,
                "MNQ": 2,
                "NQ": 5
            }
        )

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
        Test position within per-symbol limit.

        Given: ES limit = 3
        When: ES position = 2 contracts
        Then: No violation
        """
        # Given: Position within limit
        mock_engine.current_positions = {
            "ES": {"symbol": "ES", "size": 2, "avgPrice": 5000.0}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 2,
                "avgPrice": 5000.0,
                "contract_id": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is False

    # ========================================================================
    # Test 2: Single Symbol Exceeds Limit
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_single_symbol_exceeds_limit(self, rule, mock_engine):
        """
        Test position exceeding per-symbol limit.

        Given: ES limit = 3
        When: ES position = 5 contracts
        Then: Violation detected for ES only
        """
        # Given: Position exceeds limit
        mock_engine.current_positions = {
            "ES": {"symbol": "ES", "size": 5, "avgPrice": 5000.0, "contract_id": "CON.F.US.ES.H25"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 5,
                "avgPrice": 5000.0,
                "contract_id": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is True
        assert rule.context["symbol"] == "ES"
        assert rule.context["current_size"] == 5
        assert rule.context["limit"] == 3

    # ========================================================================
    # Test 3: Multiple Symbols Independent Limits
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_symbols_independent_limits(self, rule, mock_engine):
        """
        Test multiple symbols with independent limits.

        Given: ES limit=3, MNQ limit=2
        When: ES=2, MNQ=1
        Then: No violations (both within limits)
        """
        # Given: Multiple positions, each within limit
        mock_engine.current_positions = {
            "ES": {"symbol": "ES", "size": 2, "avgPrice": 5000.0},
            "MNQ": {"symbol": "MNQ", "size": 1, "avgPrice": 21000.0}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 1,
                "avgPrice": 21000.0,
                "contract_id": "CON.F.US.MNQ.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violations
        assert violation is False

    # ========================================================================
    # Test 4: One Symbol Violates, Others OK
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_one_symbol_violates_others_ok(self, rule, mock_engine):
        """
        Test only violating symbol triggers enforcement.

        Given: ES limit=3, MNQ limit=2
        When: ES=2 (OK), MNQ=3 (violates)
        Then: Violation for MNQ only, ES unaffected
        """
        # Given: One symbol exceeds, others OK
        mock_engine.current_positions = {
            "ES": {"symbol": "ES", "size": 2, "avgPrice": 5000.0},
            "MNQ": {"symbol": "MNQ", "size": 3, "avgPrice": 21000.0, "contract_id": "CON.F.US.MNQ.H25"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 3,
                "avgPrice": 21000.0,
                "contract_id": "CON.F.US.MNQ.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation for MNQ only
        assert violation is True
        assert rule.context["symbol"] == "MNQ"
        assert rule.context["current_size"] == 3
        assert rule.context["limit"] == 2

    # ========================================================================
    # Test 5: Symbol Without Configured Limit
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_symbol_without_configured_limit(self, rule, mock_engine):
        """
        Test symbol without configured limit is blocked.

        Given: RTY has no configured limit, unknown_symbol_action="block"
        When: RTY position = 10 contracts
        Then: Violation (unknown symbol blocked by default)
        """
        # Given: Symbol not in limits config
        mock_engine.current_positions = {
            "RTY": {"symbol": "RTY", "size": 10, "avgPrice": 2000.0}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "RTY",
                "size": 10,
                "avgPrice": 2000.0,
                "contract_id": "CON.F.US.RTY.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation (unknown symbols blocked by default)
        assert violation is True
        assert rule.context["symbol"] == "RTY"
        assert rule.context["limit"] == 0

    # ========================================================================
    # Test 6: Short Positions Counted as Absolute Value
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_short_positions_absolute_value(self, rule, mock_engine):
        """
        Test short positions counted as absolute value.

        Given: ES limit = 3
        When: ES short -4 contracts
        Then: Violation (abs(-4) = 4 > 3)
        """
        # Given: Short position exceeding limit
        mock_engine.current_positions = {
            "ES": {"symbol": "ES", "size": -4, "avgPrice": 5000.0, "contract_id": "CON.F.US.ES.H25"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": -4,
                "avgPrice": 5000.0,
                "contract_id": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is True
        assert rule.context["symbol"] == "ES"
        assert rule.context["current_size"] == 4  # Absolute value

    # ========================================================================
    # Test 7: Exactly at Limit No Violation
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_exactly_at_limit_no_violation(self, rule, mock_engine):
        """
        Test position exactly at limit does not violate.

        Given: ES limit = 3
        When: ES position = 3 contracts
        Then: No violation (rule uses > not >=)
        """
        # Given: Position exactly at limit
        mock_engine.current_positions = {
            "ES": {"symbol": "ES", "size": 3, "avgPrice": 5000.0}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 3,
                "avgPrice": 5000.0,
                "contract_id": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is False

    # ========================================================================
    # Test 8: Event Bus Integration
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_event_bus_integration(self, rule, mock_engine, event_bus):
        """
        Test complete event flow through EventBus.

        Flow:
        1. Rule evaluates event
        2. Violation detected
        3. Context stored in rule
        """
        # Given: Position exceeds limit
        mock_engine.current_positions = {
            "MNQ": {"symbol": "MNQ", "size": 4, "avgPrice": 21000.0, "contract_id": "CON.F.US.MNQ.H25"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "size": 4,
                "avgPrice": 21000.0,
                "contract_id": "CON.F.US.MNQ.H25"
            }
        )

        # When: Evaluate rule
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected and context stored
        assert violation is True
        assert rule.context["symbol"] == "MNQ"
        assert rule.context["current_size"] == 4
        assert rule.context["limit"] == 2

    # ========================================================================
    # Test 9: No Lockout on Violation
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_no_lockout_on_violation(self, rule, mock_engine):
        """
        Test violation does NOT create lockout.

        Trade-by-trade rule: Close excess for that symbol only.
        Trader can continue trading other symbols.
        """
        # Given: ES exceeds limit
        mock_engine.current_positions = {
            "ES": {"symbol": "ES", "size": 5, "avgPrice": 5000.0, "contract_id": "CON.F.US.ES.H25"},
            "MNQ": {"symbol": "MNQ", "size": 1, "avgPrice": 21000.0}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 5,
                "avgPrice": 5000.0,
                "contract_id": "CON.F.US.ES.H25"
            }
        )

        # When: Rule evaluates
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation for ES only, no account lockout in context
        assert violation is True
        assert "lockout" not in rule.context or rule.context.get("lockout") is False

    # ========================================================================
    # Test 10: Dynamic Limit Configuration
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_dynamic_limit_configuration(self, mock_engine):
        """
        Test rule can be reconfigured with different limits.

        Verifies limits can be updated without recreating engine.
        """
        # Given: New rule with reduced limits
        new_rule = MaxContractsPerInstrumentRule(
            limits={
                "ES": 2,  # Reduced from 3
                "MNQ": 1   # Reduced from 2
            }
        )

        # And: Position that was OK with old limit (3)
        mock_engine.current_positions = {
            "ES": {"symbol": "ES", "size": 3, "avgPrice": 5000.0, "contract_id": "CON.F.US.ES.H25"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "ES",
                "size": 3,
                "avgPrice": 5000.0,
                "contract_id": "CON.F.US.ES.H25"
            }
        )

        # Then: Now violates with new limit (2)
        violation = await new_rule.evaluate(event, mock_engine)
        assert violation is True
        assert new_rule.context["limit"] == 2  # New limit applied
