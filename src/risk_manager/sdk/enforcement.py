"""
SDK-Powered Enforcement Executor

Wraps the Project-X SDK's PositionManager and OrderManager to provide
standardized enforcement actions for risk rules.
"""

from typing import Any

from loguru import logger
from project_x_py import TradingSuite

from risk_manager.sdk.suite_manager import SuiteManager


class EnforcementExecutor:
    """
    Executes enforcement actions using the Project-X SDK.

    This class provides a clean interface for risk rules to enforce
    actions without directly coupling to the SDK.

    Actions:
    - Close all positions
    - Close specific position
    - Reduce position to limit
    - Cancel all orders
    - Cancel specific order
    """

    def __init__(self, suite_manager: SuiteManager):
        """
        Initialize the enforcement executor.

        Args:
            suite_manager: SuiteManager instance for accessing TradingSuites
        """
        self.suite_manager = suite_manager
        logger.info("EnforcementExecutor initialized")

    async def close_all_positions(self, symbol: str | None = None) -> dict[str, Any]:
        """
        Close all positions for an instrument or all instruments.

        Args:
            symbol: Instrument symbol (None = all instruments)

        Returns:
            Dictionary with results: {"success": bool, "closed": int, "errors": list}
        """
        result = {"success": True, "closed": 0, "errors": []}

        if symbol:
            # Close positions for specific instrument
            suite = self.suite_manager.get_suite(symbol)
            if not suite:
                result["success"] = False
                result["errors"].append(f"Suite not found for {symbol}")
                return result

            try:
                await self._close_positions_for_suite(suite, symbol, result)
            except Exception as e:
                result["success"] = False
                result["errors"].append(f"{symbol}: {e}")
                logger.error(f"Failed to close positions for {symbol}: {e}")

        else:
            # Close positions for all instruments
            for sym, suite in self.suite_manager.get_all_suites().items():
                try:
                    await self._close_positions_for_suite(suite, sym, result)
                except Exception as e:
                    result["success"] = False
                    result["errors"].append(f"{sym}: {e}")
                    logger.error(f"Failed to close positions for {sym}: {e}")

        logger.info(f"Close all positions result: {result}")
        return result

    async def _close_positions_for_suite(
        self, suite: TradingSuite, symbol: str, result: dict[str, Any]
    ) -> None:
        """
        Close positions for a specific suite.

        Args:
            suite: TradingSuite instance
            symbol: Instrument symbol (for logging)
            result: Result dictionary to update
        """
        # Get all open positions
        positions = await suite.positions.get_all_positions()

        if not positions:
            logger.info(f"No open positions for {symbol}")
            return

        logger.info(f"Closing {len(positions)} position(s) for {symbol}")

        for position in positions:
            try:
                # Close the position using SDK
                await suite.positions.close_position(position.contract_id, reason="Risk rule enforcement")
                result["closed"] += 1
                logger.success(f"Closed position {position.contract_id} for {symbol}")

            except Exception as e:
                result["success"] = False
                result["errors"].append(f"{symbol}/{position.contract_id}: {e}")
                logger.error(f"Failed to close position {position.contract_id}: {e}")

    async def close_position(self, symbol: str, contract_id: str) -> dict[str, Any]:
        """
        Close a specific position.

        Args:
            symbol: Instrument symbol
            contract_id: Contract ID to close

        Returns:
            Dictionary with result: {"success": bool, "error": str | None}
        """
        result = {"success": True, "error": None}

        suite = self.suite_manager.get_suite(symbol)
        if not suite:
            result["success"] = False
            result["error"] = f"Suite not found for {symbol}"
            return result

        try:
            await suite.positions.close_position(contract_id, reason="Risk rule enforcement")
            logger.success(f"Closed position {contract_id} for {symbol}")

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            logger.error(f"Failed to close position {contract_id} for {symbol}: {e}")

        return result

    async def reduce_position_to_limit(
        self, symbol: str, contract_id: str, target_size: int
    ) -> dict[str, Any]:
        """
        Partially close a position to reach target size.

        Args:
            symbol: Instrument symbol
            contract_id: Contract ID
            target_size: Target position size (positive for long, negative for short)

        Returns:
            Dictionary with result: {"success": bool, "error": str | None}
        """
        result = {"success": True, "error": None}

        suite = self.suite_manager.get_suite(symbol)
        if not suite:
            result["success"] = False
            result["error"] = f"Suite not found for {symbol}"
            return result

        try:
            # Get current position
            positions = await suite.positions.get_all_positions()
            current_position = next((p for p in positions if p.contract_id == contract_id), None)

            if not current_position:
                result["success"] = False
                result["error"] = f"Position not found for {contract_id}"
                return result

            current_size = current_position.size
            size_to_close = abs(current_size) - abs(target_size)

            if size_to_close <= 0:
                logger.info(f"Position {contract_id} already at or below target size")
                return result

            # Partially close position
            await suite.positions.partially_close_position(
                contract_id,
                size=size_to_close,
                reason="Risk rule enforcement - reduce to limit"
            )
            logger.success(
                f"Reduced position {contract_id} from {current_size} to {target_size}"
            )

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            logger.error(f"Failed to reduce position {contract_id}: {e}")

        return result

    async def cancel_all_orders(self, symbol: str | None = None) -> dict[str, Any]:
        """
        Cancel all pending orders for an instrument or all instruments.

        Args:
            symbol: Instrument symbol (None = all instruments)

        Returns:
            Dictionary with results: {"success": bool, "cancelled": int, "errors": list}
        """
        result = {"success": True, "cancelled": 0, "errors": []}

        if symbol:
            # Cancel orders for specific instrument
            suite = self.suite_manager.get_suite(symbol)
            if not suite:
                result["success"] = False
                result["errors"].append(f"Suite not found for {symbol}")
                return result

            try:
                await self._cancel_orders_for_suite(suite, symbol, result)
            except Exception as e:
                result["success"] = False
                result["errors"].append(f"{symbol}: {e}")
                logger.error(f"Failed to cancel orders for {symbol}: {e}")

        else:
            # Cancel orders for all instruments
            for sym, suite in self.suite_manager.get_all_suites().items():
                try:
                    await self._cancel_orders_for_suite(suite, sym, result)
                except Exception as e:
                    result["success"] = False
                    result["errors"].append(f"{sym}: {e}")
                    logger.error(f"Failed to cancel orders for {sym}: {e}")

        logger.info(f"Cancel all orders result: {result}")
        return result

    async def _cancel_orders_for_suite(
        self, suite: TradingSuite, symbol: str, result: dict[str, Any]
    ) -> None:
        """
        Cancel orders for a specific suite.

        Args:
            suite: TradingSuite instance
            symbol: Instrument symbol (for logging)
            result: Result dictionary to update
        """
        # Get all open orders
        orders = await suite.orders.get_open_orders()

        if not orders:
            logger.info(f"No open orders for {symbol}")
            return

        logger.info(f"Cancelling {len(orders)} order(s) for {symbol}")

        for order in orders:
            try:
                # Cancel the order using SDK
                await suite.orders.cancel_order(order.id)
                result["cancelled"] += 1
                logger.success(f"Cancelled order {order.id} for {symbol}")

            except Exception as e:
                result["success"] = False
                result["errors"].append(f"{symbol}/{order.id}: {e}")
                logger.error(f"Failed to cancel order {order.id}: {e}")

    async def cancel_order(self, symbol: str, order_id: str) -> dict[str, Any]:
        """
        Cancel a specific order.

        Args:
            symbol: Instrument symbol
            order_id: Order ID to cancel

        Returns:
            Dictionary with result: {"success": bool, "error": str | None}
        """
        result = {"success": True, "error": None}

        suite = self.suite_manager.get_suite(symbol)
        if not suite:
            result["success"] = False
            result["error"] = f"Suite not found for {symbol}"
            return result

        try:
            await suite.orders.cancel_order(order_id)
            logger.success(f"Cancelled order {order_id} for {symbol}")

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            logger.error(f"Failed to cancel order {order_id} for {symbol}: {e}")

        return result

    async def flatten_and_cancel(self, symbol: str | None = None) -> dict[str, Any]:
        """
        Close all positions AND cancel all orders (full flatten).

        Args:
            symbol: Instrument symbol (None = all instruments)

        Returns:
            Dictionary with combined results
        """
        logger.warning(f"FLATTEN AND CANCEL triggered for {symbol or 'ALL instruments'}")

        # Close positions
        close_result = await self.close_all_positions(symbol)

        # Cancel orders
        cancel_result = await self.cancel_all_orders(symbol)

        # Combine results
        result = {
            "success": close_result["success"] and cancel_result["success"],
            "closed": close_result["closed"],
            "cancelled": cancel_result["cancelled"],
            "errors": close_result["errors"] + cancel_result["errors"],
        }

        logger.info(f"Flatten and cancel result: {result}")
        return result
