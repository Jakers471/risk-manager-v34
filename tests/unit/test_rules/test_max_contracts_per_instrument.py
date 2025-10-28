"""
Unit Tests for MaxContractsPerInstrumentRule (RULE-002)

Tests the per-instrument contract limit rule which enforces concentration risk limits.

Rule: RULE-002 - Max Contracts Per Instrument
- Enforces per-symbol contract limits
- Configuration: limits dict mapping symbol to max contracts
- Enforcement: "reduce_to_limit" or "close_all"
- Unknown symbol handling: "block", "allow_with_limit:N", "allow_unlimited"
- Triggers on: POSITION_OPENED, POSITION_UPDATED
"""

import pytest
from unittest.mock import AsyncMock, Mock

from risk_manager.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
from risk_manager.core.events import RiskEvent, EventType


class TestMaxContractsPerInstrumentRuleUnit:
    """Unit tests for MaxContractsPerInstrumentRule."""

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization_basic(self):
        """Test rule initializes with basic configuration."""
        limits = {"MNQ": 2, "ES": 1}
        rule = MaxContractsPerInstrumentRule(limits=limits)
        assert rule.limits == limits
        assert rule.enforcement == "reduce_to_limit"
        assert rule.unknown_symbol_action == "block"

    def test_rule_initialization_custom_enforcement(self):
        """Test rule initializes with custom enforcement action."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            enforcement="close_all"
        )
        assert rule.enforcement == "close_all"

    def test_rule_initialization_unknown_symbol_allow_unlimited(self):
        """Test rule initializes with allow_unlimited for unknown symbols."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="allow_unlimited"
        )
        assert rule.unknown_symbol_action == "allow_unlimited"

    def test_rule_initialization_unknown_symbol_with_limit(self):
        """Test rule initializes with default limit for unknown symbols."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="allow_with_limit:3"
        )
        assert rule.unknown_symbol_action == "allow_with_limit:3"
        assert rule.unknown_symbol_limit == 3

    def test_rule_initialization_invalid_unknown_symbol_action(self):
        """Test rule handles invalid unknown_symbol_action format gracefully."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="allow_with_limit:invalid"
        )
        # Should fallback to "block"
        assert rule.unknown_symbol_action == "block"
        assert rule.unknown_symbol_limit is None

    def test_rule_initialization_empty_limits(self):
        """Test rule can be initialized with empty limits dict."""
        rule = MaxContractsPerInstrumentRule(limits={})
        assert rule.limits == {}

    def test_rule_initialization_multiple_symbols(self):
        """Test rule initializes with multiple symbol limits."""
        limits = {"MNQ": 2, "ES": 1, "NQ": 3, "YM": 1}
        rule = MaxContractsPerInstrumentRule(limits=limits)
        assert rule.limits == limits
        assert len(rule.limits) == 4

    # ========================================================================
    # Test 2: Event Type Filtering
    # ========================================================================

    @pytest.mark.asyncio
    async def test_ignores_non_position_events(self):
        """Test rule ignores events that are not position-related."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        # ORDER_PLACED
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "MNQ", "size": 5}
        )
        result = await rule.evaluate(event, engine)
        assert result is False

        # ORDER_FILLED
        event = RiskEvent(
            event_type=EventType.ORDER_FILLED,
            data={"symbol": "MNQ", "size": 5}
        )
        result = await rule.evaluate(event, engine)
        assert result is False

        # TRADE_EXECUTED
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"symbol": "MNQ", "size": 5}
        )
        result = await rule.evaluate(event, engine)
        assert result is False

    @pytest.mark.asyncio
    async def test_evaluates_position_opened_event(self):
        """Test rule evaluates POSITION_OPENED events."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 3}
        )

        result = await rule.evaluate(event, engine)
        # Should evaluate (result True = breach, False = no breach)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_evaluates_position_updated_event(self):
        """Test rule evaluates POSITION_UPDATED events."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 3}
        )

        result = await rule.evaluate(event, engine)
        assert isinstance(result, bool)

    # ========================================================================
    # Test 3: Position Within Limit (No Breach)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_within_limit_no_breach(self):
        """Test position within limit does not trigger breach."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 1}
        )

        result = await rule.evaluate(event, engine)
        assert result is False  # No breach

    @pytest.mark.asyncio
    async def test_zero_position_no_breach(self):
        """Test zero position does not trigger breach."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 0}
        )

        result = await rule.evaluate(event, engine)
        assert result is False  # No breach for closed position

    @pytest.mark.asyncio
    async def test_position_at_exact_limit_no_breach(self):
        """Test position at exact limit does not trigger breach."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 2}
        )

        result = await rule.evaluate(event, engine)
        assert result is False  # At limit is acceptable

    # ========================================================================
    # Test 4: Position Exceeds Limit (Breach)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_exceeds_limit_triggers_breach(self):
        """Test position exceeding limit triggers breach."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 3}
        )

        result = await rule.evaluate(event, engine)
        assert result is True  # Breach!

    @pytest.mark.asyncio
    async def test_position_one_over_limit_triggers_breach(self):
        """Test position one contract over limit triggers breach."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 3}
        )

        result = await rule.evaluate(event, engine)
        assert result is True

    @pytest.mark.asyncio
    async def test_large_position_exceeds_limit(self):
        """Test large position far exceeding limit triggers breach."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 10}
        )

        result = await rule.evaluate(event, engine)
        assert result is True

    # ========================================================================
    # Test 5: Short Positions (Absolute Value)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_short_position_within_limit_no_breach(self):
        """Test short position within limit does not trigger breach."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": -1}
        )

        result = await rule.evaluate(event, engine)
        assert result is False  # Absolute value checked

    @pytest.mark.asyncio
    async def test_short_position_exceeds_limit_triggers_breach(self):
        """Test short position exceeding limit triggers breach."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": -3}
        )

        result = await rule.evaluate(event, engine)
        assert result is True  # Absolute value checked

    @pytest.mark.asyncio
    async def test_short_position_at_limit_no_breach(self):
        """Test short position at exact limit does not trigger breach."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": -2}
        )

        result = await rule.evaluate(event, engine)
        assert result is False

    # ========================================================================
    # Test 6: Multiple Symbols with Different Limits
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multiple_symbols_each_within_limit(self):
        """Test multiple symbols each within their respective limits."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2, "ES": 1, "NQ": 3})
        engine = Mock()

        # MNQ within limit
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 2}
        )
        result = await rule.evaluate(event, engine)
        assert result is False

        # ES within limit
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "contract_id": "456", "size": 1}
        )
        result = await rule.evaluate(event, engine)
        assert result is False

        # NQ within limit
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "NQ", "contract_id": "789", "size": 3}
        )
        result = await rule.evaluate(event, engine)
        assert result is False

    @pytest.mark.asyncio
    async def test_one_symbol_breaches_while_others_ok(self):
        """Test one symbol breaches while others remain within limits."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2, "ES": 1})
        engine = Mock()

        # MNQ within limit
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 2}
        )
        result = await rule.evaluate(event, engine)
        assert result is False

        # ES breaches
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "contract_id": "456", "size": 2}
        )
        result = await rule.evaluate(event, engine)
        assert result is True

    @pytest.mark.asyncio
    async def test_different_limits_for_different_symbols(self):
        """Test rule respects different limits for different symbols."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 5, "ES": 1})
        engine = Mock()

        # MNQ can have 5
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 5}
        )
        result = await rule.evaluate(event, engine)
        assert result is False

        # ES can only have 1
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ES", "contract_id": "456", "size": 2}
        )
        result = await rule.evaluate(event, engine)
        assert result is True

    # ========================================================================
    # Test 7: Unknown Symbol - Block Mode
    # ========================================================================

    @pytest.mark.asyncio
    async def test_unknown_symbol_block_mode_triggers_breach(self):
        """Test unknown symbol in block mode triggers breach for any position."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="block"
        )
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "UNKNOWN", "contract_id": "123", "size": 1}
        )

        result = await rule.evaluate(event, engine)
        assert result is True  # Block any unknown symbol position

    @pytest.mark.asyncio
    async def test_unknown_symbol_block_mode_zero_position(self):
        """Test unknown symbol with zero position doesn't breach even in block mode."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="block"
        )
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "UNKNOWN", "contract_id": "123", "size": 0}
        )

        result = await rule.evaluate(event, engine)
        assert result is False  # Zero position is OK even in block mode

    # ========================================================================
    # Test 8: Unknown Symbol - Allow Unlimited Mode
    # ========================================================================

    @pytest.mark.asyncio
    async def test_unknown_symbol_allow_unlimited_no_breach(self):
        """Test unknown symbol in allow_unlimited mode never breaches."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="allow_unlimited"
        )
        engine = Mock()

        # Any size should be OK
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "UNKNOWN", "contract_id": "123", "size": 100}
        )

        result = await rule.evaluate(event, engine)
        assert result is False  # Allow unlimited

    @pytest.mark.asyncio
    async def test_unknown_symbol_allow_unlimited_multiple_sizes(self):
        """Test allow_unlimited allows any size for unknown symbols."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="allow_unlimited"
        )
        engine = Mock()

        # Test various sizes
        for size in [1, 5, 10, 100, 1000]:
            event = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={"symbol": "UNKNOWN", "contract_id": "123", "size": size}
            )
            result = await rule.evaluate(event, engine)
            assert result is False

    # ========================================================================
    # Test 9: Unknown Symbol - Allow With Limit Mode
    # ========================================================================

    @pytest.mark.asyncio
    async def test_unknown_symbol_with_default_limit_within(self):
        """Test unknown symbol within default limit does not breach."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="allow_with_limit:3"
        )
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "UNKNOWN", "contract_id": "123", "size": 3}
        )

        result = await rule.evaluate(event, engine)
        assert result is False  # Within default limit

    @pytest.mark.asyncio
    async def test_unknown_symbol_with_default_limit_exceeds(self):
        """Test unknown symbol exceeding default limit triggers breach."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="allow_with_limit:3"
        )
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "UNKNOWN", "contract_id": "123", "size": 4}
        )

        result = await rule.evaluate(event, engine)
        assert result is True  # Exceeds default limit

    @pytest.mark.asyncio
    async def test_unknown_symbol_default_limit_at_boundary(self):
        """Test unknown symbol at exact default limit boundary."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="allow_with_limit:5"
        )
        engine = Mock()

        # At limit (should pass)
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "UNKNOWN", "contract_id": "123", "size": 5}
        )
        result = await rule.evaluate(event, engine)
        assert result is False

        # Over limit by 1 (should breach)
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "UNKNOWN", "contract_id": "123", "size": 6}
        )
        result = await rule.evaluate(event, engine)
        assert result is True

    # ========================================================================
    # Test 10: Context Storage for Enforcement
    # ========================================================================

    @pytest.mark.asyncio
    async def test_breach_stores_context(self):
        """Test breach stores enforcement context."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 5}
        )

        result = await rule.evaluate(event, engine)
        assert result is True

        # Check context was stored
        assert rule.context is not None
        assert rule.context["symbol"] == "MNQ"
        assert rule.context["contract_id"] == "123"
        assert rule.context["current_size"] == 5
        assert rule.context["limit"] == 2

    @pytest.mark.asyncio
    async def test_breach_context_includes_enforcement_type(self):
        """Test breach context includes enforcement type."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            enforcement="close_all"
        )
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 5}
        )

        result = await rule.evaluate(event, engine)
        assert result is True
        assert rule.context["enforcement"] == "close_all"

    @pytest.mark.asyncio
    async def test_unknown_symbol_breach_stores_reason(self):
        """Test unknown symbol breach stores reason in context."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            unknown_symbol_action="block"
        )
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "UNKNOWN", "contract_id": "123", "size": 1}
        )

        result = await rule.evaluate(event, engine)
        assert result is True
        assert "reason" in rule.context
        assert rule.context["reason"] == "unknown_symbol_blocked"

    # ========================================================================
    # Test 11: Enforcement Execution - Reduce to Limit
    # ========================================================================

    @pytest.mark.asyncio
    async def test_enforce_reduce_to_limit(self):
        """Test enforcement with reduce_to_limit action."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            enforcement="reduce_to_limit"
        )
        engine = Mock()
        executor = AsyncMock()
        executor.reduce_position_to_limit = AsyncMock(return_value={"success": True})
        engine.enforcement_executor = executor

        # Set up breach context
        rule.context = {
            "symbol": "MNQ",
            "contract_id": "123",
            "current_size": 5,
            "limit": 2,
            "enforcement": "reduce_to_limit"
        }

        await rule.enforce(engine)

        # Should call reduce_position_to_limit
        executor.reduce_position_to_limit.assert_called_once_with(
            "MNQ", "123", target_size=2
        )

    @pytest.mark.asyncio
    async def test_enforce_reduce_to_zero_closes_position(self):
        """Test enforcement with reduce to zero closes entire position."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 0},  # Zero limit
            enforcement="reduce_to_limit"
        )
        engine = Mock()
        executor = AsyncMock()
        executor.close_position = AsyncMock(return_value={"success": True})
        engine.enforcement_executor = executor

        # Set up breach context
        rule.context = {
            "symbol": "MNQ",
            "contract_id": "123",
            "current_size": 5,
            "limit": 0,
            "enforcement": "reduce_to_limit"
        }

        await rule.enforce(engine)

        # Should call close_position when limit is 0
        executor.close_position.assert_called_once_with("MNQ", "123")

    # ========================================================================
    # Test 12: Enforcement Execution - Close All
    # ========================================================================

    @pytest.mark.asyncio
    async def test_enforce_close_all(self):
        """Test enforcement with close_all action."""
        rule = MaxContractsPerInstrumentRule(
            limits={"MNQ": 2},
            enforcement="close_all"
        )
        engine = Mock()
        executor = AsyncMock()
        executor.close_position = AsyncMock(return_value={"success": True})
        engine.enforcement_executor = executor

        # Set up breach context
        rule.context = {
            "symbol": "MNQ",
            "contract_id": "123",
            "current_size": 5,
            "limit": 2,
            "enforcement": "close_all"
        }

        await rule.enforce(engine)

        # Should call close_position
        executor.close_position.assert_called_once_with("MNQ", "123")

    @pytest.mark.asyncio
    async def test_enforce_clears_context_after_execution(self):
        """Test enforcement clears context after execution."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()
        executor = AsyncMock()
        executor.close_position = AsyncMock(return_value={"success": True})
        engine.enforcement_executor = executor

        rule.context = {
            "symbol": "MNQ",
            "contract_id": "123",
            "current_size": 5,
            "limit": 2,
            "enforcement": "close_all"
        }

        await rule.enforce(engine)

        # Context should be cleared
        assert rule.context is None

    @pytest.mark.asyncio
    async def test_enforce_handles_missing_context(self):
        """Test enforcement handles missing context gracefully."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()
        engine.enforcement_executor = AsyncMock()

        # No context set
        rule.context = None

        # Should not crash
        await rule.enforce(engine)

    @pytest.mark.asyncio
    async def test_enforce_handles_missing_executor(self):
        """Test enforcement handles missing executor gracefully."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()
        # Mock hasattr to return False for enforcement_executor
        engine.enforcement_executor = None

        # Delete the attribute to simulate missing executor
        del engine.enforcement_executor

        rule.context = {
            "symbol": "MNQ",
            "contract_id": "123",
            "current_size": 5,
            "limit": 2,
            "enforcement": "close_all"
        }

        # Should not crash (will log error and return early)
        await rule.enforce(engine)

    # ========================================================================
    # Test 13: Missing or Invalid Event Data
    # ========================================================================

    @pytest.mark.asyncio
    async def test_missing_symbol_returns_false(self):
        """Test event missing symbol returns False."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"contract_id": "123", "size": 5}  # Missing symbol
        )

        result = await rule.evaluate(event, engine)
        assert result is False

    @pytest.mark.asyncio
    async def test_missing_contract_id_returns_false(self):
        """Test event missing contract_id returns False."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "size": 5}  # Missing contract_id
        )

        result = await rule.evaluate(event, engine)
        assert result is False

    @pytest.mark.asyncio
    async def test_missing_size_defaults_to_zero(self):
        """Test event missing size defaults to zero (no breach)."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123"}  # Missing size
        )

        result = await rule.evaluate(event, engine)
        assert result is False  # Zero size = no breach

    # ========================================================================
    # Test 14: get_status() Method
    # ========================================================================

    def test_get_status_returns_configuration(self):
        """Test get_status returns rule configuration."""
        limits = {"MNQ": 2, "ES": 1}
        rule = MaxContractsPerInstrumentRule(
            limits=limits,
            enforcement="close_all",
            unknown_symbol_action="block"
        )

        status = rule.get_status()

        assert status["rule"] == "MaxContractsPerInstrument"
        assert status["enabled"] is True
        assert status["limits"] == limits
        assert status["enforcement"] == "close_all"
        assert status["unknown_symbol_action"] == "block"

    def test_get_status_includes_all_fields(self):
        """Test get_status includes all expected fields."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        status = rule.get_status()

        assert "rule" in status
        assert "enabled" in status
        assert "limits" in status
        assert "enforcement" in status
        assert "unknown_symbol_action" in status

    # ========================================================================
    # Test 15: Edge Cases and Error Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_empty_data_dict(self):
        """Test rule handles empty data dict gracefully."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={}  # Empty data
        )

        result = await rule.evaluate(event, engine)
        assert result is False

    @pytest.mark.asyncio
    async def test_negative_size_uses_absolute_value(self):
        """Test negative size (short position) uses absolute value."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": -5}
        )

        result = await rule.evaluate(event, engine)
        assert result is True  # abs(-5) = 5 > 2

    @pytest.mark.asyncio
    async def test_enforcement_failure_logged(self):
        """Test enforcement failure is logged properly."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 2})
        engine = Mock()
        executor = AsyncMock()
        executor.close_position = AsyncMock(
            return_value={"success": False, "error": "Failed to close"}
        )
        engine.enforcement_executor = executor

        rule.context = {
            "symbol": "MNQ",
            "contract_id": "123",
            "current_size": 5,
            "limit": 2,
            "enforcement": "close_all"
        }

        # Should not crash on failure
        await rule.enforce(engine)

    @pytest.mark.asyncio
    async def test_zero_limit_blocks_all_positions(self):
        """Test zero limit blocks all positions."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 0})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 1}
        )

        result = await rule.evaluate(event, engine)
        assert result is True  # Any size > 0 should breach

    @pytest.mark.asyncio
    async def test_large_limit_allows_large_positions(self):
        """Test large limit allows large positions."""
        rule = MaxContractsPerInstrumentRule(limits={"MNQ": 100})
        engine = Mock()

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 99}
        )

        result = await rule.evaluate(event, engine)
        assert result is False  # Within limit

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "MNQ", "contract_id": "123", "size": 101}
        )

        result = await rule.evaluate(event, engine)
        assert result is True  # Exceeds limit
