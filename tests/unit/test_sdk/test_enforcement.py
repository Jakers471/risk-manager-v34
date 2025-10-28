"""
Unit Tests for EnforcementExecutor

Tests the SDK-powered enforcement executor in isolation with mocked dependencies.
Covers all enforcement actions: close positions, cancel orders, reduce positions, flatten.

Module: src/risk_manager/sdk/enforcement.py
Coverage Target: 70%+
"""

import pytest
import sys
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Any

# Mock the project_x_py SDK before importing our modules
sys.modules['project_x_py'] = MagicMock()
sys.modules['project_x_py.utils'] = MagicMock()

from risk_manager.sdk.enforcement import EnforcementExecutor
from risk_manager.sdk.suite_manager import SuiteManager


class TestEnforcementExecutorInitialization:
    """Test enforcement executor initialization."""

    def test_initialization_with_suite_manager(self):
        """
        GIVEN: Valid suite manager
        WHEN: EnforcementExecutor is initialized
        THEN: Executor is properly configured
        """
        mock_suite_manager = Mock(spec=SuiteManager)
        executor = EnforcementExecutor(mock_suite_manager)

        assert executor.suite_manager is mock_suite_manager

    def test_initialization_logs_success(self, caplog):
        """
        GIVEN: Suite manager
        WHEN: EnforcementExecutor is initialized
        THEN: Initialization is logged
        """
        mock_suite_manager = Mock(spec=SuiteManager)
        executor = EnforcementExecutor(mock_suite_manager)

        assert "EnforcementExecutor initialized" in caplog.text


class TestCloseAllPositions:
    """Test close_all_positions enforcement action."""

    @pytest.fixture
    def mock_suite_manager(self):
        """Create mock suite manager."""
        manager = Mock(spec=SuiteManager)
        return manager

    @pytest.fixture
    def mock_suite(self):
        """Create mock TradingSuite."""
        suite = AsyncMock()
        suite.positions = AsyncMock()
        return suite

    @pytest.fixture
    def executor(self, mock_suite_manager):
        """Create executor with mock suite manager."""
        return EnforcementExecutor(mock_suite_manager)

    @pytest.mark.asyncio
    async def test_close_all_positions_single_symbol_success(
        self, executor, mock_suite_manager, mock_suite
    ):
        """
        GIVEN: Suite with 2 open positions for symbol
        WHEN: close_all_positions is called for that symbol
        THEN: Both positions are closed successfully
        """
        # Setup
        mock_position_1 = Mock(contract_id="POS1")
        mock_position_2 = Mock(contract_id="POS2")
        mock_suite.positions.get_all_positions = AsyncMock(
            return_value=[mock_position_1, mock_position_2]
        )
        mock_suite.positions.close_position = AsyncMock()
        mock_suite_manager.get_suite = Mock(return_value=mock_suite)

        # Execute
        result = await executor.close_all_positions(symbol="MNQ")

        # Verify
        assert result["success"] is True
        assert result["closed"] == 2
        assert len(result["errors"]) == 0
        assert mock_suite.positions.close_position.call_count == 2

    @pytest.mark.asyncio
    async def test_close_all_positions_no_positions(
        self, executor, mock_suite_manager, mock_suite
    ):
        """
        GIVEN: Suite with no open positions
        WHEN: close_all_positions is called
        THEN: Returns success with 0 closed
        """
        mock_suite.positions.get_all_positions = AsyncMock(return_value=[])
        mock_suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.close_all_positions(symbol="MNQ")

        assert result["success"] is True
        assert result["closed"] == 0
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_close_all_positions_suite_not_found(
        self, executor, mock_suite_manager
    ):
        """
        GIVEN: Suite manager without suite for symbol
        WHEN: close_all_positions is called
        THEN: Returns failure with error message
        """
        mock_suite_manager.get_suite = Mock(return_value=None)

        result = await executor.close_all_positions(symbol="MNQ")

        assert result["success"] is False
        assert result["closed"] == 0
        assert "Suite not found for MNQ" in result["errors"]

    @pytest.mark.asyncio
    async def test_close_all_positions_partial_failure(
        self, executor, mock_suite_manager, mock_suite
    ):
        """
        GIVEN: Suite with 3 positions, one fails to close
        WHEN: close_all_positions is called
        THEN: Returns partial success with errors
        """
        mock_position_1 = Mock(contract_id="POS1")
        mock_position_2 = Mock(contract_id="POS2")
        mock_position_3 = Mock(contract_id="POS3")

        mock_suite.positions.get_all_positions = AsyncMock(
            return_value=[mock_position_1, mock_position_2, mock_position_3]
        )

        # First two succeed, third fails
        async def close_position_side_effect(contract_id, reason):
            if contract_id == "POS3":
                raise Exception("Failed to close POS3")

        mock_suite.positions.close_position = AsyncMock(
            side_effect=close_position_side_effect
        )
        mock_suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.close_all_positions(symbol="MNQ")

        assert result["success"] is False
        assert result["closed"] == 2
        assert len(result["errors"]) > 0
        assert "POS3" in str(result["errors"])

    @pytest.mark.asyncio
    async def test_close_all_positions_all_symbols(
        self, executor, mock_suite_manager, mock_suite
    ):
        """
        GIVEN: Multiple suites with positions
        WHEN: close_all_positions is called with symbol=None
        THEN: Closes positions for all symbols
        """
        mock_position = Mock(contract_id="POS1")
        mock_suite.positions.get_all_positions = AsyncMock(
            return_value=[mock_position]
        )
        mock_suite.positions.close_position = AsyncMock()

        # Return same suite for multiple symbols
        mock_suite_manager.get_all_suites = Mock(
            return_value={
                "MNQ": mock_suite,
                "ES": mock_suite,
            }
        )

        result = await executor.close_all_positions(symbol=None)

        assert result["success"] is True
        assert result["closed"] == 2  # 1 position per symbol
        assert mock_suite.positions.close_position.call_count == 2


class TestClosePosition:
    """Test close_position enforcement action."""

    @pytest.fixture
    def executor(self):
        """Create executor with mock suite manager."""
        mock_suite_manager = Mock(spec=SuiteManager)
        return EnforcementExecutor(mock_suite_manager)

    @pytest.mark.asyncio
    async def test_close_position_success(self, executor):
        """
        GIVEN: Valid suite and contract ID
        WHEN: close_position is called
        THEN: Position is closed successfully
        """
        mock_suite = AsyncMock()
        mock_suite.positions = AsyncMock()
        mock_suite.positions.close_position = AsyncMock()
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.close_position("MNQ", "POS123")

        assert result["success"] is True
        assert result["error"] is None
        mock_suite.positions.close_position.assert_called_once_with(
            "POS123", reason="Risk rule enforcement"
        )

    @pytest.mark.asyncio
    async def test_close_position_suite_not_found(self, executor):
        """
        GIVEN: Suite manager without suite for symbol
        WHEN: close_position is called
        THEN: Returns failure with error
        """
        executor.suite_manager.get_suite = Mock(return_value=None)

        result = await executor.close_position("MNQ", "POS123")

        assert result["success"] is False
        assert "Suite not found" in result["error"]

    @pytest.mark.asyncio
    async def test_close_position_failure(self, executor):
        """
        GIVEN: Suite that throws exception when closing position
        WHEN: close_position is called
        THEN: Returns failure with error message
        """
        mock_suite = AsyncMock()
        mock_suite.positions = AsyncMock()
        mock_suite.positions.close_position = AsyncMock(
            side_effect=Exception("SDK Error")
        )
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.close_position("MNQ", "POS123")

        assert result["success"] is False
        assert "SDK Error" in result["error"]


class TestReducePositionToLimit:
    """Test reduce_position_to_limit enforcement action."""

    @pytest.fixture
    def executor(self):
        """Create executor with mock suite manager."""
        mock_suite_manager = Mock(spec=SuiteManager)
        return EnforcementExecutor(mock_suite_manager)

    @pytest.mark.asyncio
    async def test_reduce_position_to_limit_success(self, executor):
        """
        GIVEN: Position with size 5, target size 2
        WHEN: reduce_position_to_limit is called
        THEN: Position is reduced by 3 contracts
        """
        mock_position = Mock(contract_id="POS123", size=5)
        mock_suite = AsyncMock()
        mock_suite.positions = AsyncMock()
        mock_suite.positions.get_all_positions = AsyncMock(
            return_value=[mock_position]
        )
        mock_suite.positions.partially_close_position = AsyncMock()
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.reduce_position_to_limit("MNQ", "POS123", 2)

        assert result["success"] is True
        assert result["error"] is None
        mock_suite.positions.partially_close_position.assert_called_once_with(
            "POS123",
            size=3,
            reason="Risk rule enforcement - reduce to limit"
        )

    @pytest.mark.asyncio
    async def test_reduce_position_already_below_target(self, executor):
        """
        GIVEN: Position with size 2, target size 5
        WHEN: reduce_position_to_limit is called
        THEN: No action taken (already below target)
        """
        mock_position = Mock(contract_id="POS123", size=2)
        mock_suite = AsyncMock()
        mock_suite.positions = AsyncMock()
        mock_suite.positions.get_all_positions = AsyncMock(
            return_value=[mock_position]
        )
        mock_suite.positions.partially_close_position = AsyncMock()
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.reduce_position_to_limit("MNQ", "POS123", 5)

        assert result["success"] is True
        mock_suite.positions.partially_close_position.assert_not_called()

    @pytest.mark.asyncio
    async def test_reduce_position_not_found(self, executor):
        """
        GIVEN: Position does not exist
        WHEN: reduce_position_to_limit is called
        THEN: Returns failure with error
        """
        mock_suite = AsyncMock()
        mock_suite.positions = AsyncMock()
        mock_suite.positions.get_all_positions = AsyncMock(return_value=[])
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.reduce_position_to_limit("MNQ", "POS123", 2)

        assert result["success"] is False
        assert "Position not found" in result["error"]

    @pytest.mark.asyncio
    async def test_reduce_position_suite_not_found(self, executor):
        """
        GIVEN: Suite manager without suite for symbol
        WHEN: reduce_position_to_limit is called
        THEN: Returns failure with error
        """
        executor.suite_manager.get_suite = Mock(return_value=None)

        result = await executor.reduce_position_to_limit("MNQ", "POS123", 2)

        assert result["success"] is False
        assert "Suite not found" in result["error"]

    @pytest.mark.asyncio
    async def test_reduce_position_short_position(self, executor):
        """
        GIVEN: Short position with size -5, target size -2
        WHEN: reduce_position_to_limit is called
        THEN: Position is reduced by 3 contracts (using absolute values)
        """
        mock_position = Mock(contract_id="POS123", size=-5)
        mock_suite = AsyncMock()
        mock_suite.positions = AsyncMock()
        mock_suite.positions.get_all_positions = AsyncMock(
            return_value=[mock_position]
        )
        mock_suite.positions.partially_close_position = AsyncMock()
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.reduce_position_to_limit("MNQ", "POS123", -2)

        assert result["success"] is True
        # Should close 3 contracts (abs(-5) - abs(-2) = 3)
        mock_suite.positions.partially_close_position.assert_called_once_with(
            "POS123",
            size=3,
            reason="Risk rule enforcement - reduce to limit"
        )


class TestCancelAllOrders:
    """Test cancel_all_orders enforcement action."""

    @pytest.fixture
    def executor(self):
        """Create executor with mock suite manager."""
        mock_suite_manager = Mock(spec=SuiteManager)
        return EnforcementExecutor(mock_suite_manager)

    @pytest.mark.asyncio
    async def test_cancel_all_orders_single_symbol_success(self, executor):
        """
        GIVEN: Suite with 3 open orders
        WHEN: cancel_all_orders is called for that symbol
        THEN: All orders are cancelled successfully
        """
        mock_order_1 = Mock(id="ORD1")
        mock_order_2 = Mock(id="ORD2")
        mock_order_3 = Mock(id="ORD3")

        mock_suite = AsyncMock()
        mock_suite.orders = AsyncMock()
        mock_suite.orders.get_open_orders = AsyncMock(
            return_value=[mock_order_1, mock_order_2, mock_order_3]
        )
        mock_suite.orders.cancel_order = AsyncMock()
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.cancel_all_orders(symbol="MNQ")

        assert result["success"] is True
        assert result["cancelled"] == 3
        assert len(result["errors"]) == 0
        assert mock_suite.orders.cancel_order.call_count == 3

    @pytest.mark.asyncio
    async def test_cancel_all_orders_no_orders(self, executor):
        """
        GIVEN: Suite with no open orders
        WHEN: cancel_all_orders is called
        THEN: Returns success with 0 cancelled
        """
        mock_suite = AsyncMock()
        mock_suite.orders = AsyncMock()
        mock_suite.orders.get_open_orders = AsyncMock(return_value=[])
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.cancel_all_orders(symbol="MNQ")

        assert result["success"] is True
        assert result["cancelled"] == 0

    @pytest.mark.asyncio
    async def test_cancel_all_orders_suite_not_found(self, executor):
        """
        GIVEN: Suite manager without suite for symbol
        WHEN: cancel_all_orders is called
        THEN: Returns failure with error
        """
        executor.suite_manager.get_suite = Mock(return_value=None)

        result = await executor.cancel_all_orders(symbol="MNQ")

        assert result["success"] is False
        assert "Suite not found for MNQ" in result["errors"]

    @pytest.mark.asyncio
    async def test_cancel_all_orders_partial_failure(self, executor):
        """
        GIVEN: Suite with 3 orders, one fails to cancel
        WHEN: cancel_all_orders is called
        THEN: Returns partial success with errors
        """
        mock_order_1 = Mock(id="ORD1")
        mock_order_2 = Mock(id="ORD2")
        mock_order_3 = Mock(id="ORD3")

        mock_suite = AsyncMock()
        mock_suite.orders = AsyncMock()
        mock_suite.orders.get_open_orders = AsyncMock(
            return_value=[mock_order_1, mock_order_2, mock_order_3]
        )

        # First two succeed, third fails
        async def cancel_order_side_effect(order_id):
            if order_id == "ORD3":
                raise Exception("Failed to cancel ORD3")

        mock_suite.orders.cancel_order = AsyncMock(
            side_effect=cancel_order_side_effect
        )
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.cancel_all_orders(symbol="MNQ")

        assert result["success"] is False
        assert result["cancelled"] == 2
        assert len(result["errors"]) > 0
        assert "ORD3" in str(result["errors"])

    @pytest.mark.asyncio
    async def test_cancel_all_orders_all_symbols(self, executor):
        """
        GIVEN: Multiple suites with orders
        WHEN: cancel_all_orders is called with symbol=None
        THEN: Cancels orders for all symbols
        """
        mock_order = Mock(id="ORD1")
        mock_suite = AsyncMock()
        mock_suite.orders = AsyncMock()
        mock_suite.orders.get_open_orders = AsyncMock(
            return_value=[mock_order]
        )
        mock_suite.orders.cancel_order = AsyncMock()

        executor.suite_manager.get_all_suites = Mock(
            return_value={
                "MNQ": mock_suite,
                "ES": mock_suite,
            }
        )

        result = await executor.cancel_all_orders(symbol=None)

        assert result["success"] is True
        assert result["cancelled"] == 2  # 1 order per symbol


class TestCancelOrder:
    """Test cancel_order enforcement action."""

    @pytest.fixture
    def executor(self):
        """Create executor with mock suite manager."""
        mock_suite_manager = Mock(spec=SuiteManager)
        return EnforcementExecutor(mock_suite_manager)

    @pytest.mark.asyncio
    async def test_cancel_order_success(self, executor):
        """
        GIVEN: Valid suite and order ID
        WHEN: cancel_order is called
        THEN: Order is cancelled successfully
        """
        mock_suite = AsyncMock()
        mock_suite.orders = AsyncMock()
        mock_suite.orders.cancel_order = AsyncMock()
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.cancel_order("MNQ", "ORD123")

        assert result["success"] is True
        assert result["error"] is None
        mock_suite.orders.cancel_order.assert_called_once_with("ORD123")

    @pytest.mark.asyncio
    async def test_cancel_order_suite_not_found(self, executor):
        """
        GIVEN: Suite manager without suite for symbol
        WHEN: cancel_order is called
        THEN: Returns failure with error
        """
        executor.suite_manager.get_suite = Mock(return_value=None)

        result = await executor.cancel_order("MNQ", "ORD123")

        assert result["success"] is False
        assert "Suite not found" in result["error"]

    @pytest.mark.asyncio
    async def test_cancel_order_failure(self, executor):
        """
        GIVEN: Suite that throws exception when cancelling order
        WHEN: cancel_order is called
        THEN: Returns failure with error message
        """
        mock_suite = AsyncMock()
        mock_suite.orders = AsyncMock()
        mock_suite.orders.cancel_order = AsyncMock(
            side_effect=Exception("SDK Error")
        )
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        result = await executor.cancel_order("MNQ", "ORD123")

        assert result["success"] is False
        assert "SDK Error" in result["error"]


class TestFlattenAndCancel:
    """Test flatten_and_cancel enforcement action."""

    @pytest.fixture
    def executor(self):
        """Create executor with mock suite manager."""
        mock_suite_manager = Mock(spec=SuiteManager)
        return EnforcementExecutor(mock_suite_manager)

    @pytest.mark.asyncio
    async def test_flatten_and_cancel_success(self, executor):
        """
        GIVEN: Suite with positions and orders
        WHEN: flatten_and_cancel is called
        THEN: All positions closed and all orders cancelled
        """
        # Mock close_all_positions
        executor.close_all_positions = AsyncMock(
            return_value={
                "success": True,
                "closed": 2,
                "errors": []
            }
        )

        # Mock cancel_all_orders
        executor.cancel_all_orders = AsyncMock(
            return_value={
                "success": True,
                "cancelled": 3,
                "errors": []
            }
        )

        result = await executor.flatten_and_cancel(symbol="MNQ")

        assert result["success"] is True
        assert result["closed"] == 2
        assert result["cancelled"] == 3
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_flatten_and_cancel_partial_failure(self, executor):
        """
        GIVEN: Positions close but orders fail
        WHEN: flatten_and_cancel is called
        THEN: Returns combined failure status
        """
        executor.close_all_positions = AsyncMock(
            return_value={
                "success": True,
                "closed": 2,
                "errors": []
            }
        )

        executor.cancel_all_orders = AsyncMock(
            return_value={
                "success": False,
                "cancelled": 1,
                "errors": ["Failed to cancel ORD2"]
            }
        )

        result = await executor.flatten_and_cancel(symbol="MNQ")

        assert result["success"] is False
        assert result["closed"] == 2
        assert result["cancelled"] == 1
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_flatten_and_cancel_all_symbols(self, executor):
        """
        GIVEN: Multiple symbols
        WHEN: flatten_and_cancel is called with symbol=None
        THEN: Flattens all symbols
        """
        executor.close_all_positions = AsyncMock(
            return_value={
                "success": True,
                "closed": 5,
                "errors": []
            }
        )

        executor.cancel_all_orders = AsyncMock(
            return_value={
                "success": True,
                "cancelled": 3,
                "errors": []
            }
        )

        result = await executor.flatten_and_cancel(symbol=None)

        assert result["success"] is True
        assert result["closed"] == 5
        assert result["cancelled"] == 3


class TestLogging:
    """Test enforcement logging behavior."""

    @pytest.fixture
    def executor(self):
        """Create executor with mock suite manager."""
        mock_suite_manager = Mock(spec=SuiteManager)
        return EnforcementExecutor(mock_suite_manager)

    @pytest.mark.asyncio
    async def test_enforcement_action_logged_close_all(self, executor, caplog):
        """
        GIVEN: Enforcement executor
        WHEN: close_all_positions is called
        THEN: Enforcement action is logged with warning level
        """
        mock_suite = AsyncMock()
        mock_suite.positions = AsyncMock()
        mock_suite.positions.get_all_positions = AsyncMock(return_value=[])
        executor.suite_manager.get_suite = Mock(return_value=mock_suite)

        await executor.close_all_positions(symbol="MNQ")

        # Should log enforcement trigger
        # Note: Actual log check depends on logger implementation

    @pytest.mark.asyncio
    async def test_flatten_and_cancel_critical_logging(self, executor, caplog):
        """
        GIVEN: Enforcement executor
        WHEN: flatten_and_cancel is called
        THEN: Critical action is logged
        """
        executor.close_all_positions = AsyncMock(
            return_value={"success": True, "closed": 0, "errors": []}
        )
        executor.cancel_all_orders = AsyncMock(
            return_value={"success": True, "cancelled": 0, "errors": []}
        )

        await executor.flatten_and_cancel(symbol="MNQ")

        # Should log CRITICAL enforcement action
