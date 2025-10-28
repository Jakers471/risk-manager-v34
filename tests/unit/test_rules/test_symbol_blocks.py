"""
Unit Tests for SymbolBlocksRule (RULE-011)

Tests the symbol blocks rule in isolation with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-011 - Symbol Blocks
- Block specific symbols from trading
- Close positions in blocked symbols immediately
- Support case-insensitive matching
- Support wildcard patterns (e.g., MNQ*, *CRYPTO*)
- Trade-by-Trade enforcement (NO lockout)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from risk_manager.rules import SymbolBlocksRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine
from risk_manager.core.config import RiskConfig


class TestSymbolBlocksRuleUnit:
    """Unit tests for SymbolBlocksRule."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user"
        )

    @pytest.fixture
    def rule(self):
        """Create symbol blocks rule with basic blocked symbols."""
        return SymbolBlocksRule(
            blocked_symbols=["BTC", "ETH", "RTY"],
            action="close"
        )

    @pytest.fixture
    def rule_with_wildcards(self):
        """Create symbol blocks rule with wildcard patterns."""
        return SymbolBlocksRule(
            blocked_symbols=["BTC", "MNQ*", "*CRYPTO*"],
            action="close"
        )

    @pytest.fixture
    def mock_engine(self, config):
        """Create mock risk engine."""
        engine = Mock(spec=RiskEngine)
        engine.config = config
        engine.current_positions = {}
        engine.daily_pnl = 0.0
        return engine

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization(self, rule):
        """Test rule initializes with correct parameters."""
        assert rule.blocked_symbols == ["BTC", "ETH", "RTY"]
        assert rule.action == "close"
        assert rule.name == "SymbolBlocksRule"

    def test_rule_initialization_with_wildcards(self, rule_with_wildcards):
        """Test rule can be initialized with wildcard patterns."""
        assert "MNQ*" in rule_with_wildcards.blocked_symbols
        assert "*CRYPTO*" in rule_with_wildcards.blocked_symbols

    def test_rule_initialization_empty_list(self):
        """Test rule can be initialized with empty blocked list."""
        rule = SymbolBlocksRule(blocked_symbols=[], action="close")
        assert rule.blocked_symbols == []

    # ========================================================================
    # Test 2: Allowed Symbol (Should PASS)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_allowed_symbol_passes(self, rule, mock_engine):
        """Test that allowed symbol does not trigger violation."""
        # Given: Order for allowed symbol (ES)
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "ES", "size": 1}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    @pytest.mark.asyncio
    async def test_multiple_allowed_symbols_pass(self, rule, mock_engine):
        """Test that multiple allowed symbols do not trigger violation."""
        # Given: Position in allowed symbols
        mock_engine.current_positions = {
            "ES": {"size": 1, "side": "long"},
            "NQ": {"size": 1, "side": "long"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 1}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    # ========================================================================
    # Test 3: Blocked Symbol (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_blocked_symbol_violates(self, rule, mock_engine):
        """Test that blocked symbol triggers violation."""
        # Given: Order for blocked symbol (BTC)
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "BTC", "size": 1}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["action"] == "close"
        assert violation["symbol"] == "BTC"
        assert "blocked" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_position_in_blocked_symbol_violates(self, rule, mock_engine):
        """Test that position in blocked symbol triggers violation."""
        # Given: Position in blocked symbol (ETH)
        mock_engine.current_positions = {
            "ETH": {"size": 2, "side": "long"}
        }

        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ETH", "size": 2}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["symbol"] == "ETH"
        assert violation["action"] == "close"

    @pytest.mark.asyncio
    async def test_all_blocked_symbols_violate(self, rule, mock_engine):
        """Test that all blocked symbols trigger violations."""
        blocked_symbols = ["BTC", "ETH", "RTY"]

        for symbol in blocked_symbols:
            event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={"symbol": symbol, "size": 1}
            )

            violation = await rule.evaluate(event, mock_engine)

            assert violation is not None, f"Symbol {symbol} should be blocked"
            assert violation["symbol"] == symbol

    # ========================================================================
    # Test 4: Case-Insensitive Matching
    # ========================================================================

    @pytest.mark.asyncio
    async def test_case_insensitive_uppercase(self, rule, mock_engine):
        """Test case-insensitive matching for uppercase."""
        # Given: Order for blocked symbol in uppercase
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "BTC", "size": 1}  # Uppercase
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None

    @pytest.mark.asyncio
    async def test_case_insensitive_lowercase(self, rule, mock_engine):
        """Test case-insensitive matching for lowercase."""
        # Given: Order for blocked symbol in lowercase
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "btc", "size": 1}  # Lowercase
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None
        assert violation["symbol"] == "btc"

    @pytest.mark.asyncio
    async def test_case_insensitive_mixed_case(self, rule, mock_engine):
        """Test case-insensitive matching for mixed case."""
        # Given: Order for blocked symbol in mixed case
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "BtC", "size": 1}  # Mixed case
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation detected
        assert violation is not None

    # ========================================================================
    # Test 5: Wildcard Pattern Matching
    # ========================================================================

    @pytest.mark.asyncio
    async def test_wildcard_prefix_match(self, rule_with_wildcards, mock_engine):
        """Test wildcard pattern matching with prefix (MNQ*)."""
        # Given: Order for symbol starting with MNQ
        test_symbols = ["MNQ", "MNQ1", "MNQ2025", "MNQH25"]

        for symbol in test_symbols:
            event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={"symbol": symbol, "size": 1}
            )

            violation = await rule_with_wildcards.evaluate(event, mock_engine)

            assert violation is not None, f"Symbol {symbol} should match MNQ* pattern"
            assert violation["symbol"] == symbol

    @pytest.mark.asyncio
    async def test_wildcard_contains_match(self, rule_with_wildcards, mock_engine):
        """Test wildcard pattern matching with contains (*CRYPTO*)."""
        # Given: Order for symbol containing CRYPTO
        test_symbols = ["BTCCRYPTO", "CRYPTOCOIN", "TESTCRYPTOFUND"]

        for symbol in test_symbols:
            event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={"symbol": symbol, "size": 1}
            )

            violation = await rule_with_wildcards.evaluate(event, mock_engine)

            assert violation is not None, f"Symbol {symbol} should match *CRYPTO* pattern"

    @pytest.mark.asyncio
    async def test_wildcard_no_match(self, rule_with_wildcards, mock_engine):
        """Test wildcard pattern does not match unrelated symbols."""
        # Given: Order for symbol that doesn't match any pattern
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "ES", "size": 1}  # Should not match
        )

        # When: Rule evaluates event
        violation = await rule_with_wildcards.evaluate(event, mock_engine)

        # Then: No violation
        assert violation is None

    @pytest.mark.asyncio
    async def test_wildcard_case_insensitive(self, rule_with_wildcards, mock_engine):
        """Test wildcard patterns are case-insensitive."""
        # Given: Order for symbol matching pattern in different case
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "mnq", "size": 1}  # Lowercase of MNQ*
        )

        # When: Rule evaluates event
        violation = await rule_with_wildcards.evaluate(event, mock_engine)

        # Then: Violation detected (case-insensitive wildcard)
        assert violation is not None

    # ========================================================================
    # Test 6: Event Type Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_evaluates_order_placed_event(self, rule, mock_engine):
        """Test rule evaluates ORDER_PLACED events."""
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "BTC", "size": 1}
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None

    @pytest.mark.asyncio
    async def test_evaluates_position_opened_event(self, rule, mock_engine):
        """Test rule evaluates POSITION_OPENED events."""
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"symbol": "ETH", "size": 1}
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None

    @pytest.mark.asyncio
    async def test_evaluates_position_updated_event(self, rule, mock_engine):
        """Test rule evaluates POSITION_UPDATED events."""
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "RTY", "size": 2}
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None

    @pytest.mark.asyncio
    async def test_ignores_irrelevant_events(self, rule, mock_engine):
        """Test rule ignores events that don't involve symbols."""
        # Given: A system event (no symbol involved)
        event = RiskEvent(
            event_type=EventType.SYSTEM_STARTED,
            data={}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (event ignored)
        assert violation is None

    # ========================================================================
    # Test 7: No Lockout Enforcement
    # ========================================================================

    @pytest.mark.asyncio
    async def test_no_lockout_on_violation(self, rule, mock_engine):
        """Test that violation does NOT include lockout action."""
        # Given: Order for blocked symbol
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "BTC", "size": 1}
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: Violation exists but action is only "close", not "lockout"
        assert violation is not None
        assert violation["action"] == "close"
        assert "lockout" not in violation["action"].lower()

    # ========================================================================
    # Test 8: Edge Cases
    # ========================================================================

    @pytest.mark.asyncio
    async def test_empty_blocked_list_allows_all(self, mock_engine):
        """Test that empty blocked list allows all symbols."""
        rule = SymbolBlocksRule(blocked_symbols=[], action="close")

        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "BTC", "size": 1}
        )

        violation = await rule.evaluate(event, mock_engine)

        # No symbols blocked, should allow all
        assert violation is None

    @pytest.mark.asyncio
    async def test_missing_symbol_in_event(self, rule, mock_engine):
        """Test rule handles missing symbol data gracefully."""
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={}  # Missing symbol
        )

        # Should not crash
        violation = await rule.evaluate(event, mock_engine)

        # Should handle gracefully (no violation if no symbol)
        assert violation is None

    @pytest.mark.asyncio
    async def test_none_symbol_in_event(self, rule, mock_engine):
        """Test rule handles None symbol gracefully."""
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": None}
        )

        # Should not crash
        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    @pytest.mark.asyncio
    async def test_disabled_rule_allows_all(self, rule, mock_engine):
        """Test that disabled rule allows all symbols."""
        # Given: Rule is disabled
        rule.disable()

        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "BTC", "size": 1}  # Blocked symbol
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (rule disabled)
        assert violation is None

    # ========================================================================
    # Test 9: Violation Message Quality
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_message_clarity(self, rule, mock_engine):
        """Test violation message is clear and actionable."""
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "BTC", "size": 1}
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert "message" in violation
        assert isinstance(violation["message"], str)
        assert len(violation["message"]) > 10  # Not empty
        # Message should contain key info
        message_lower = violation["message"].lower()
        assert "blocked" in message_lower or "prohibited" in message_lower
        assert "btc" in message_lower

    @pytest.mark.asyncio
    async def test_violation_includes_rule_name(self, rule, mock_engine):
        """Test violation includes rule name for tracking."""
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "BTC", "size": 1}
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert "rule" in violation
        assert violation["rule"] == "SymbolBlocksRule"

    # ========================================================================
    # Test 10: Multiple Patterns
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multiple_exact_matches(self):
        """Test rule with multiple exact symbol blocks."""
        rule = SymbolBlocksRule(
            blocked_symbols=["BTC", "ETH", "SOL", "ADA"],
            action="close"
        )
        mock_engine = Mock(spec=RiskEngine)

        for symbol in ["BTC", "ETH", "SOL", "ADA"]:
            event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={"symbol": symbol, "size": 1}
            )

            violation = await rule.evaluate(event, mock_engine)
            assert violation is not None, f"Symbol {symbol} should be blocked"

    @pytest.mark.asyncio
    async def test_mixed_exact_and_wildcard(self):
        """Test rule with mix of exact matches and wildcards."""
        rule = SymbolBlocksRule(
            blocked_symbols=["BTC", "MNQ*", "*CRYPTO*", "ETH"],
            action="close"
        )
        mock_engine = Mock(spec=RiskEngine)

        # Test exact matches
        for symbol in ["BTC", "ETH"]:
            event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={"symbol": symbol, "size": 1}
            )
            violation = await rule.evaluate(event, mock_engine)
            assert violation is not None

        # Test wildcard matches
        for symbol in ["MNQ1", "TESTCRYPTO"]:
            event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={"symbol": symbol, "size": 1}
            )
            violation = await rule.evaluate(event, mock_engine)
            assert violation is not None

        # Test allowed
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={"symbol": "ES", "size": 1}
        )
        violation = await rule.evaluate(event, mock_engine)
        assert violation is None
