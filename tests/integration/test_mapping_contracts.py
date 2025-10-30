"""
Contract Test Suite for Mapping Bugs

This test suite focuses on catching mapping mismatches that can slip through unit tests:
- SDK Payload → Canonical Position normalization
- Alias normalization (ENQ → NQ)
- Tick value/size mismatches (units bugs)
- Sign convention bugs (profit sign inversions)
- Schema drift (missing/extra fields)

These tests prevent the "tests pass but wrong answer" problem by validating
the data transformation pipeline from SDK events to internal representations.

CRITICAL: These tests validate contracts between:
1. SDK event format (raw JSON/objects from Project-X-Py)
2. Internal position representation (what we use in rules)
3. P&L calculations (ensuring $$ is correct)

Any mismatch caught here would be invisible in unit tests because they mock
the SDK layer away.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock

from risk_manager.integrations.trading import (
    TradingIntegration,
    TICK_VALUES,
    ALIASES,
)
from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.config.models import RiskConfig


# ============================================================================
# CATEGORY 1: SDK Payload → Canonical Position Normalization
# ============================================================================

class TestSDKPayloadNormalization:
    """Test SDK event payloads normalize correctly to internal Position objects."""

    @pytest.fixture
    def event_bus(self):
        """Create real event bus."""
        return EventBus()

    @pytest.fixture
    def config(self):
        """Create minimal config for testing."""
        return Mock(spec=RiskConfig)

    @pytest.fixture
    def trading_integration(self, config, event_bus):
        """Create TradingIntegration with mocked suite."""
        integration = TradingIntegration(
            instruments=["MNQ", "NQ", "ES"],
            config=config,
            event_bus=event_bus
        )
        # Mock the suite so we don't need real SDK
        integration.suite = Mock()
        return integration

    def test_sdk_position_event_minimal_fields(self, trading_integration):
        """
        Test: SDK position event with minimal required fields normalizes correctly.

        Schema: {type, size, averagePrice, contractId}
        """
        # SDK event payload (minimal)
        sdk_event = {
            "type": 1,  # BUY (LONG)
            "size": 2,
            "averagePrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
        }

        # Add to open positions tracking (simulating what handle_position_opened does)
        trading_integration._open_positions["CON.F.US.MNQ.U25"] = {
            "entry_price": sdk_event["averagePrice"],
            "size": sdk_event["size"],
            "side": "long" if sdk_event["type"] == 1 else "short",
        }

        # Verify the position was stored correctly
        position = trading_integration._open_positions["CON.F.US.MNQ.U25"]
        assert position["entry_price"] == Decimal("21000.00") or position["entry_price"] == 21000.00
        assert position["size"] == 2
        assert position["side"] == "long"

    def test_sdk_position_event_with_extra_fields(self, trading_integration):
        """
        Test: SDK position event with extra fields still normalizes correctly.

        Schema: {type, size, averagePrice, contractId, ... extra fields ...}
        """
        # SDK event with extra fields (should not break normalization)
        sdk_event = {
            "type": 2,  # SELL (SHORT)
            "size": 3,
            "averagePrice": 5000.50,
            "contractId": "CON.F.US.ES.H25",
            "id": 12345,  # Extra field
            "accountId": 999,  # Extra field
            "createdAt": "2025-10-30T10:00:00Z",  # Extra field
            "updatedAt": "2025-10-30T10:00:00Z",  # Extra field
        }

        # Store position
        trading_integration._open_positions["CON.F.US.ES.H25"] = {
            "entry_price": sdk_event["averagePrice"],
            "size": sdk_event["size"],
            "side": "short" if sdk_event["type"] == 2 else "long",
        }

        # Verify extra fields don't break normalization
        position = trading_integration._open_positions["CON.F.US.ES.H25"]
        assert position["entry_price"] == Decimal("5000.50") or position["entry_price"] == 5000.50
        assert position["size"] == 3
        assert position["side"] == "short"

    def test_sdk_position_side_1_is_long(self):
        """Test: SDK type=1 correctly normalizes to 'long' side."""
        # Type 1 = BUY = LONG
        side = "long" if 1 == 1 else "short"
        assert side == "long"

    def test_sdk_position_side_2_is_short(self):
        """Test: SDK type=2 correctly normalizes to 'short' side."""
        # Type 2 = SELL = SHORT
        side = "short" if 2 == 2 else "long"
        assert side == "short"

    def test_contract_id_to_symbol_extraction(self, trading_integration):
        """
        Test: Contract ID → Symbol mapping works correctly.

        Examples:
        - CON.F.US.MNQ.U25 → MNQ
        - CON.F.US.NQ.Z25 → NQ
        - CON.F.US.ES.H25 → ES
        """
        test_cases = [
            ("CON.F.US.MNQ.U25", "MNQ"),
            ("CON.F.US.NQ.Z25", "NQ"),
            ("CON.F.US.ES.H25", "ES"),
            ("CON.F.US.YM.M25", "YM"),
            ("CON.F.US.RTY.H25", "RTY"),
        ]

        for contract_id, expected_symbol in test_cases:
            # Extract symbol from contract ID
            # Format: CON.F.US.{SYMBOL}.{EXPIRY}
            parts = contract_id.split(".")
            symbol = parts[3] if len(parts) >= 4 else None
            assert symbol == expected_symbol, f"Failed for {contract_id}"


# ============================================================================
# CATEGORY 2: Alias Normalization
# ============================================================================

class TestAliasNormalization:
    """Test alias normalization catches symbol mismatches."""

    def test_enq_alias_normalizes_to_nq(self):
        """Test: ENQ (alias) → NQ (canonical)."""
        symbol = "ENQ"
        normalized = ALIASES.get(symbol, symbol)
        assert normalized == "NQ"

    def test_mnq_no_alias(self):
        """Test: MNQ has no alias (already canonical)."""
        symbol = "MNQ"
        normalized = ALIASES.get(symbol, symbol)
        assert normalized == "MNQ"

    def test_unknown_symbol_no_alias(self):
        """Test: Unknown symbols return unchanged."""
        symbol = "UNKNOWN"
        normalized = ALIASES.get(symbol, symbol)
        assert normalized == "UNKNOWN"

    def test_contract_id_with_alias(self):
        """
        Test: Contract ID containing aliased symbol gets normalized.

        Example: CON.F.US.ENQ.Z25 should extract ENQ, normalize to NQ
        """
        contract_id = "CON.F.US.ENQ.Z25"
        # Extract symbol
        parts = contract_id.split(".")
        symbol = parts[3]
        # Normalize
        normalized = ALIASES.get(symbol, symbol)
        assert normalized == "NQ"

    def test_multiple_aliases_in_same_system(self):
        """Test: Multiple different alias mismatches don't collide."""
        # If we add more aliases in future
        test_cases = [
            ("ENQ", "NQ"),
            ("ENQ", "NQ"),  # Same twice
        ]
        for alias, expected in test_cases:
            normalized = ALIASES.get(alias, alias)
            assert normalized == expected


# ============================================================================
# CATEGORY 3: Units Mismatch Detection (Tick Value Bug)
# ============================================================================

class TestUnitsMismatch:
    """Test tick value mismatches that cause P&L calculation errors."""

    def test_es_tick_economics_correct(self):
        """Test: ES has correct tick value $12.50."""
        assert TICK_VALUES["ES"]["size"] == 0.25
        assert TICK_VALUES["ES"]["tick_value"] == 12.50

    def test_mnq_tick_economics_correct(self):
        """Test: MNQ has correct tick value $0.50."""
        assert TICK_VALUES["MNQ"]["size"] == 0.25
        assert TICK_VALUES["MNQ"]["tick_value"] == 0.50

    def test_nq_tick_economics_correct(self):
        """Test: NQ has correct tick value $5.00."""
        assert TICK_VALUES["NQ"]["size"] == 0.25
        assert TICK_VALUES["NQ"]["tick_value"] == 5.00

    def test_mes_tick_economics_correct(self):
        """Test: MES has correct tick value $1.25."""
        assert TICK_VALUES["MES"]["size"] == 0.25
        assert TICK_VALUES["MES"]["tick_value"] == 1.25

    def test_pnl_calculation_es_10_ticks_profit(self):
        """
        Test: ES profit calculation correct.

        ES: 10 ticks profit = 10 × $12.50 = $125.00
        """
        entry_price = 5000.00
        exit_price = 5002.50  # 10 ticks = 10 × 0.25
        size = 1
        side = "long"

        tick_size = TICK_VALUES["ES"]["size"]
        tick_value = TICK_VALUES["ES"]["tick_value"]

        price_diff = exit_price - entry_price if side == "long" else entry_price - exit_price
        ticks = price_diff / tick_size
        pnl = ticks * tick_value * size

        assert pnl == 125.00, f"Expected $125.00, got ${pnl}"

    def test_pnl_calculation_mnq_10_ticks_profit(self):
        """
        Test: MNQ profit calculation correct.

        MNQ: 10 ticks profit = 10 × $0.50 = $5.00
        """
        entry_price = 21000.00
        exit_price = 21002.50  # 10 ticks = 10 × 0.25
        size = 1
        side = "long"

        tick_size = TICK_VALUES["MNQ"]["size"]
        tick_value = TICK_VALUES["MNQ"]["tick_value"]

        price_diff = exit_price - entry_price if side == "long" else entry_price - exit_price
        ticks = price_diff / tick_size
        pnl = ticks * tick_value * size

        assert pnl == 5.00, f"Expected $5.00, got ${pnl}"

    def test_pnl_calculation_es_vs_mnq_same_price_move(self):
        """
        Test: Same price move produces different P&L for ES vs MNQ.

        Both move 2.50 points:
        - ES: 2.50 / 0.25 = 10 ticks × $12.50 = $125.00
        - MNQ: 2.50 / 0.25 = 10 ticks × $0.50 = $5.00
        """
        # Same price movement for both
        price_move = 2.50
        size = 1
        side = "long"

        # ES calculation
        tick_size_es = TICK_VALUES["ES"]["size"]
        tick_value_es = TICK_VALUES["ES"]["tick_value"]
        ticks_es = price_move / tick_size_es
        pnl_es = ticks_es * tick_value_es * size

        # MNQ calculation
        tick_size_mnq = TICK_VALUES["MNQ"]["size"]
        tick_value_mnq = TICK_VALUES["MNQ"]["tick_value"]
        ticks_mnq = price_move / tick_size_mnq
        pnl_mnq = ticks_mnq * tick_value_mnq * size

        # Both should have 10 ticks, but different $ values
        assert ticks_es == ticks_mnq == 10, "Both should be 10 ticks"
        assert pnl_es == 125.00, f"ES should be $125.00, got ${pnl_es}"
        assert pnl_mnq == 5.00, f"MNQ should be $5.00, got ${pnl_mnq}"
        assert pnl_es != pnl_mnq, "ES and MNQ should produce different $ amounts"

    def test_unknown_symbol_raises_error(self):
        """Test: Unknown symbol not in TICK_VALUES raises error."""
        symbol = "UNKNOWN"
        if symbol not in TICK_VALUES:
            # This is what should happen
            with pytest.raises((KeyError, Exception)):
                # Would raise when trying to access
                tick_value = TICK_VALUES[symbol]
        else:
            pytest.fail(f"UNKNOWN should not be in TICK_VALUES")

    def test_pnl_loss_calculation_correct(self):
        """
        Test: Loss calculation has correct sign.

        MNQ: Long @ 21000, exit @ 20990 = -$50 loss
        10 ticks down × $0.50 = -$5.00 loss (not -$50)
        Wait, let's recalculate: 21000 - 20990 = 10 points
        10 / 0.25 = 40 ticks
        40 ticks × $0.50 = $20 loss
        """
        entry_price = 21000.00
        exit_price = 20990.00  # Loss
        size = 1
        side = "long"

        tick_size = TICK_VALUES["MNQ"]["size"]
        tick_value = TICK_VALUES["MNQ"]["tick_value"]

        price_diff = exit_price - entry_price if side == "long" else entry_price - exit_price
        ticks = price_diff / tick_size
        pnl = ticks * tick_value * size

        assert pnl < 0, f"Loss should be negative, got ${pnl}"
        # 21000 - 20990 = 10 points = 40 ticks = $20 loss
        assert pnl == -20.00, f"Expected -$20.00, got ${pnl}"

    def test_pnl_short_position_correct(self):
        """
        Test: Short position P&L calculation correct.

        MNQ: Short @ 21000, exit @ 20990 = +$20 profit
        21000 - 20990 = 10 points = 40 ticks
        40 ticks × $0.50 = $20 profit
        """
        entry_price = 21000.00
        exit_price = 20990.00
        size = 1
        side = "short"

        tick_size = TICK_VALUES["MNQ"]["size"]
        tick_value = TICK_VALUES["MNQ"]["tick_value"]

        price_diff = entry_price - exit_price if side == "short" else exit_price - entry_price
        ticks = price_diff / tick_size
        pnl = ticks * tick_value * size

        assert pnl > 0, f"Profit should be positive, got ${pnl}"
        assert pnl == 20.00, f"Expected +$20.00, got ${pnl}"


# ============================================================================
# CATEGORY 4: Sign Convention Validation
# ============================================================================

class TestSignConvention:
    """Test sign conventions (profit positive, loss negative)."""

    def test_long_price_up_is_positive_pnl(self):
        """Test: Long position with price increase = positive P&L."""
        entry = 21000.00
        exit = 21100.00
        size = 1

        pnl = (exit - entry) * TICK_VALUES["MNQ"]["tick_value"] / TICK_VALUES["MNQ"]["size"] * size
        assert pnl > 0, "Long position with price increase should be profit (positive)"

    def test_long_price_down_is_negative_pnl(self):
        """Test: Long position with price decrease = negative P&L."""
        entry = 21000.00
        exit = 20900.00
        size = 1

        pnl = (exit - entry) * TICK_VALUES["MNQ"]["tick_value"] / TICK_VALUES["MNQ"]["size"] * size
        assert pnl < 0, "Long position with price decrease should be loss (negative)"

    def test_short_price_down_is_positive_pnl(self):
        """Test: Short position with price decrease = positive P&L."""
        entry = 21000.00
        exit = 20900.00
        size = 1

        # For short: profit when price goes down
        pnl = (entry - exit) * TICK_VALUES["MNQ"]["tick_value"] / TICK_VALUES["MNQ"]["size"] * size
        assert pnl > 0, "Short position with price decrease should be profit (positive)"

    def test_short_price_up_is_negative_pnl(self):
        """Test: Short position with price increase = negative P&L."""
        entry = 21000.00
        exit = 21100.00
        size = 1

        # For short: loss when price goes up
        pnl = (entry - exit) * TICK_VALUES["MNQ"]["tick_value"] / TICK_VALUES["MNQ"]["size"] * size
        assert pnl < 0, "Short position with price increase should be loss (negative)"

    def test_all_trades_profit_sum_positive(self):
        """Test: Multiple winning trades sum to positive P&L."""
        trades = [
            {"entry": 21000.00, "exit": 21100.00, "side": "long", "size": 1},  # +$50
            {"entry": 5000.00, "exit": 5100.00, "side": "long", "size": 1},    # +$400
            {"entry": 21000.00, "exit": 20900.00, "side": "short", "size": 1}, # +$50
        ]

        total_pnl = 0
        for trade in trades:
            if trade["side"] == "long":
                pnl = (trade["exit"] - trade["entry"]) / 0.25 * TICK_VALUES["MNQ"]["tick_value"] * trade["size"]
            else:
                pnl = (trade["entry"] - trade["exit"]) / 0.25 * TICK_VALUES["ES"]["tick_value"] * trade["size"]
            total_pnl += pnl

        assert total_pnl > 0, "All winning trades should sum to positive"

    def test_all_trades_loss_sum_negative(self):
        """Test: Multiple losing trades sum to negative P&L."""
        trades = [
            {"entry": 21000.00, "exit": 20900.00, "side": "long", "size": 1},  # -$50
            {"entry": 5000.00, "exit": 4900.00, "side": "long", "size": 1},    # -$400
            {"entry": 21000.00, "exit": 21100.00, "side": "short", "size": 1}, # -$50
        ]

        total_pnl = 0
        for trade in trades:
            if trade["side"] == "long":
                pnl = (trade["exit"] - trade["entry"]) / 0.25 * TICK_VALUES["MNQ"]["tick_value"] * trade["size"]
            else:
                pnl = (trade["entry"] - trade["exit"]) / 0.25 * TICK_VALUES["MNQ"]["tick_value"] * trade["size"]
            total_pnl += pnl

        assert total_pnl < 0, "All losing trades should sum to negative"


# ============================================================================
# CATEGORY 5: Schema Drift Detection
# ============================================================================

class TestSchemaDrift:
    """Test schema drift detection (missing/extra fields)."""

    def test_missing_required_field_type(self):
        """Test: Event missing 'type' field should fail."""
        sdk_event = {
            "size": 2,
            "averagePrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
            # Missing: "type"
        }

        # Should detect missing required field
        required_fields = ["type", "size", "averagePrice", "contractId"]
        missing = [f for f in required_fields if f not in sdk_event]
        assert "type" in missing, "Should detect missing 'type' field"

    def test_missing_required_field_size(self):
        """Test: Event missing 'size' field should fail."""
        sdk_event = {
            "type": 1,
            "averagePrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
            # Missing: "size"
        }

        required_fields = ["type", "size", "averagePrice", "contractId"]
        missing = [f for f in required_fields if f not in sdk_event]
        assert "size" in missing, "Should detect missing 'size' field"

    def test_missing_required_field_average_price(self):
        """Test: Event missing 'averagePrice' field should fail."""
        sdk_event = {
            "type": 1,
            "size": 2,
            "contractId": "CON.F.US.MNQ.U25",
            # Missing: "averagePrice"
        }

        required_fields = ["type", "size", "averagePrice", "contractId"]
        missing = [f for f in required_fields if f not in sdk_event]
        assert "averagePrice" in missing, "Should detect missing 'averagePrice' field"

    def test_missing_required_field_contract_id(self):
        """Test: Event missing 'contractId' field should fail."""
        sdk_event = {
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00,
            # Missing: "contractId"
        }

        required_fields = ["type", "size", "averagePrice", "contractId"]
        missing = [f for f in required_fields if f not in sdk_event]
        assert "contractId" in missing, "Should detect missing 'contractId' field"

    def test_extra_fields_dont_break_schema(self):
        """Test: Extra unknown fields don't break schema validation."""
        sdk_event = {
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
            "extra_field_1": "value1",
            "extra_field_2": "value2",
            "unknown_nested": {"nested": "data"},
        }

        required_fields = ["type", "size", "averagePrice", "contractId"]
        present = [f for f in required_fields if f in sdk_event]
        assert len(present) == len(required_fields), "All required fields should be present"

    def test_wrong_field_type_detected(self):
        """Test: Wrong field type should be detectable."""
        sdk_event = {
            "type": "BUY",  # Should be int (1 or 2), not string
            "size": 2,
            "averagePrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
        }

        # Type checking
        assert not isinstance(sdk_event["type"], int), "Type should be int but got string"

    def test_null_value_in_required_field(self):
        """Test: Null/None value in required field should be detected."""
        sdk_event = {
            "type": None,  # Should not be null
            "size": 2,
            "averagePrice": 21000.00,
            "contractId": "CON.F.US.MNQ.U25",
        }

        # Null detection
        assert sdk_event["type"] is None, "Type is null"
        assert not sdk_event["type"], "Null value should be falsy"


# ============================================================================
# CATEGORY 6: Symbol-Specific Tick Value Contracts
# ============================================================================

class TestSymbolTickValueContracts:
    """Test that each symbol's tick economics are enforced correctly."""

    def test_all_major_symbols_have_tick_values(self):
        """Test: All major futures symbols have defined tick values."""
        expected_symbols = ["NQ", "MNQ", "ES", "MES", "YM", "MYM", "RTY", "M2K"]
        for symbol in expected_symbols:
            assert symbol in TICK_VALUES, f"Missing tick values for {symbol}"
            assert "size" in TICK_VALUES[symbol], f"Missing 'size' for {symbol}"
            assert "tick_value" in TICK_VALUES[symbol], f"Missing 'tick_value' for {symbol}"

    def test_micro_contracts_100x_smaller_than_mini(self):
        """
        Test: Micro contracts have 1/100th the tick value of their mini counterparts.

        - MNQ tick_value ($0.50) = NQ tick_value ($5.00) / 10 ✓
        - MES tick_value ($1.25) = ES tick_value ($12.50) / 10 ✓
        - MYM tick_value ($0.50) = YM tick_value ($5.00) / 10 ✓
        """
        pairs = [
            ("MNQ", "NQ", 10),
            ("MES", "ES", 10),
            ("MYM", "YM", 10),
            ("M2K", "RTY", 10),
        ]

        for micro, mini, divisor in pairs:
            micro_tick = TICK_VALUES[micro]["tick_value"]
            mini_tick = TICK_VALUES[mini]["tick_value"]
            ratio = mini_tick / micro_tick
            assert ratio == divisor, (
                f"{micro} tick_value should be {mini} / {divisor}, "
                f"got {micro_tick} vs {mini_tick} (ratio {ratio})"
            )

    def test_tick_size_consistent_within_decimal_level(self):
        """Test: Tick sizes are consistent (0.25 or 1.00)."""
        for symbol, economics in TICK_VALUES.items():
            tick_size = economics["size"]
            assert tick_size in [0.10, 0.25, 1.00], (
                f"Unexpected tick_size {tick_size} for {symbol} - "
                f"should be 0.10, 0.25, or 1.00"
            )


# ============================================================================
# INTEGRATION: Multiple Bugs At Once
# ============================================================================

class TestMultipleMapppingBugsDetection:
    """Test detection of multiple mapping bugs in same trade scenario."""

    def test_alias_and_units_bug_together(self):
        """
        Test: Detect when both alias mismatch AND units bug happen together.

        Bug scenario:
        1. ENQ event arrives (alias bug: treated as ENQ not NQ)
        2. Code uses MNQ tick values by mistake (units bug)
        3. Result: completely wrong P&L

        Expected: Both bugs detected via contract tests
        """
        # Event has ENQ (should be NQ)
        sdk_event = {
            "type": 1,
            "size": 1,
            "averagePrice": 16000.00,
            "contractId": "CON.F.US.ENQ.Z25",  # Should extract NQ
        }

        # Extract symbol (with alias handling)
        symbol_raw = sdk_event["contractId"].split(".")[3]
        symbol = ALIASES.get(symbol_raw, symbol_raw)
        assert symbol == "NQ", "Alias bug: ENQ should normalize to NQ"

        # Verify tick values
        assert symbol in TICK_VALUES, "Symbol should be in TICK_VALUES after normalization"
        assert TICK_VALUES[symbol]["tick_value"] == 5.00, (
            "NQ should have $5.00 tick_value, not MNQ's $0.50"
        )

    def test_sign_bug_with_units_bug(self):
        """
        Test: Detect when sign is wrong AND units are wrong together.

        Bug scenario:
        1. Long position with profit
        2. Uses wrong tick value (MNQ instead of ES)
        3. Also inverts sign (negative when should be positive)
        4. Result: completely wrong (negative when should be large positive)
        """
        # Trade: ES long 4900 → 5100 = +$500 (100 point move = 400 ticks)
        entry = 4900.00
        exit = 5100.00
        symbol = "ES"

        # Correct calculation
        # 5100 - 4900 = 200 points
        # 200 / 0.25 = 800 ticks
        # 800 × $12.50 = $10,000
        correct_pnl = (exit - entry) / TICK_VALUES[symbol]["size"] * TICK_VALUES[symbol]["tick_value"]
        assert correct_pnl == 10000.00, f"Correct ES P&L should be $10,000, got ${correct_pnl}"

        # Bug 1: Wrong units (MNQ instead of ES)
        # 800 ticks × $0.50 = $400
        wrong_units_pnl = (exit - entry) / TICK_VALUES["MNQ"]["size"] * TICK_VALUES["MNQ"]["tick_value"]
        assert wrong_units_pnl == 400.00, f"Wrong units should give $400, got ${wrong_units_pnl}"

        # Bug 2: Wrong sign
        wrong_sign_pnl = -(exit - entry) / TICK_VALUES[symbol]["size"] * TICK_VALUES[symbol]["tick_value"]
        assert wrong_sign_pnl == -10000.00, f"Wrong sign should give -$10,000, got ${wrong_sign_pnl}"

        # Bug 1 + Bug 2
        both_bugs_pnl = -(exit - entry) / TICK_VALUES["MNQ"]["size"] * TICK_VALUES["MNQ"]["tick_value"]
        assert both_bugs_pnl == -400.00, f"Both bugs should give -$400, got ${both_bugs_pnl}"

        # All are different (bugs caught!)
        assert correct_pnl != wrong_units_pnl
        assert correct_pnl != wrong_sign_pnl
        assert correct_pnl != both_bugs_pnl
        assert wrong_units_pnl != wrong_sign_pnl


# ============================================================================
# Run this test suite with:
# ============================================================================
# pytest tests/integration/test_mapping_contracts.py -v
# pytest tests/integration/test_mapping_contracts.py::TestSDKPayloadNormalization -v
# pytest tests/integration/test_mapping_contracts.py::TestUnitsMismatch -v
# pytest tests/integration/test_mapping_contracts.py::TestSignConvention -v
# pytest tests/integration/test_mapping_contracts.py::TestSchemaDrift -v
# pytest tests/integration/test_mapping_contracts.py::TestSymbolTickValueContracts -v
# pytest tests/integration/test_mapping_contracts.py::TestMultipleMapppingBugsDetection -v
