"""
Protective Order Cache Module

Handles stop loss and take profit order detection, caching, and querying.

This module solves a critical problem: detecting protective orders BEFORE they execute.

The Challenge:
    - Stop loss orders are often placed via broker UI
    - SDK doesn't always emit ORDER_PLACED events for broker-UI orders
    - Risk rules need to know "Does this position have a stop loss?" IMMEDIATELY
    - Waiting for the stop to hit is too late!

The Solution:
    - Cache stop/TP orders when ORDER_PLACED fires (event-based)
    - Query SDK directly when cache is empty (fallback)
    - Use semantic analysis to determine order intent (stop loss vs take profit vs entry)
    - Invalidate cache on position updates to force fresh queries

Semantic Analysis:
    How we distinguish stop loss from take profit from entry orders:

    For EXISTING positions:
    - STOP orders (type 3, 4, 5) → Stop Loss (protective)
    - LIMIT orders (type 1) → Take Profit IF price is profitable direction
    - MARKET orders (type 2) → Manual exit/entry (unknown)

    Direction logic:
    - LONG position: TP above entry, SL below entry
    - SHORT position: TP below entry, SL above entry

Usage:
    # Initialize
    cache = ProtectiveOrderCache()
    cache.set_suite(suite)  # Provide SDK access

    # Query (checks cache first, queries SDK if needed)
    stop = await cache.get_stop_loss(contract_id, position_price, position_type)
    if stop:
        print(f"Stop @ ${stop['stop_price']}")

    # Update cache from events
    cache.update_from_order_placed(order)  # Add to cache
    cache.remove_order(contract_id)  # Remove on fill/cancel
    cache.invalidate(contract_id)  # Force refresh on next query
"""

import time
from typing import Any, Callable
from loguru import logger


class ProtectiveOrderCache:
    """
    Cache and query protective orders (stop loss and take profit).

    This class provides:
    1. Fast cache-based queries (O(1) lookup)
    2. Fallback SDK queries (when cache is empty)
    3. Semantic order analysis (detect intent from order properties)
    4. Cache invalidation (force refresh when needed)
    """

    def __init__(self):
        """Initialize empty caches."""
        # Active stop loss cache
        # Format: {contract_id: {"order_id": int, "stop_price": float, "side": str, "quantity": int, "timestamp": float}}
        self._active_stop_losses: dict[str, dict[str, Any]] = {}

        # Active take profit cache
        # Format: {contract_id: {"order_id": int, "take_profit_price": float, "side": str, "quantity": int, "timestamp": float}}
        self._active_take_profits: dict[str, dict[str, Any]] = {}

        # SDK suite reference (set externally)
        self._suite = None

        # Helper function references (set externally)
        self._extract_symbol_fn: Callable[[str], str] | None = None
        self._get_side_name_fn: Callable[[int], str] | None = None

    def set_suite(self, suite):
        """
        Set SDK suite reference for fallback queries.

        Args:
            suite: TradingSuite instance from Project-X-Py SDK
        """
        self._suite = suite

    def set_helpers(self, extract_symbol_fn: Callable[[str], str], get_side_name_fn: Callable[[int], str]):
        """
        Set helper function references.

        Args:
            extract_symbol_fn: Function to extract symbol from contract ID
            get_side_name_fn: Function to convert side int to name
        """
        self._extract_symbol_fn = extract_symbol_fn
        self._get_side_name_fn = get_side_name_fn

    # ========================================================================
    # Public Query API
    # ========================================================================

    async def get_stop_loss(
        self,
        contract_id: str,
        position_entry_price: float = None,
        position_type: int = None,
    ) -> dict[str, Any] | None:
        """
        Get the active stop loss order for a position.

        First checks cache, then queries SDK if cache is empty.
        This handles cases where ORDER_PLACED doesn't fire for broker-UI stops.

        Args:
            contract_id: Contract ID of the position
            position_entry_price: Optional entry price (from event data, avoids query)
            position_type: Optional position type (1=LONG, 2=SHORT from event data)

        Returns:
            Stop loss data dict or None if no active stop loss
            Dict format: {"order_id": int, "stop_price": float, "side": str, "quantity": int, "timestamp": float}
        """
        # Check cache first (fast path)
        cached = self._active_stop_losses.get(contract_id)
        if cached:
            return cached

        # Cache miss - query SDK (handles broker-UI stops that don't emit ORDER_PLACED)
        return await self._query_sdk_for_stop_loss(
            contract_id, position_entry_price, position_type
        )

    async def get_take_profit(
        self,
        contract_id: str,
        position_entry_price: float = None,
        position_type: int = None,
    ) -> dict[str, Any] | None:
        """
        Get the active take profit order for a position.

        First checks cache, then queries SDK if cache is empty.
        This handles cases where take profits are created in broker UI.

        Args:
            contract_id: Contract ID of the position
            position_entry_price: Optional entry price (from event data, avoids query)
            position_type: Optional position type (1=LONG, 2=SHORT from event data)

        Returns:
            Take profit data dict or None if no active take profit
            Dict format: {"order_id": int, "take_profit_price": float, "side": str, "quantity": int, "timestamp": float}
        """
        # Check cache first (fast path)
        cached = self._active_take_profits.get(contract_id)
        if cached:
            return cached

        # Cache miss - query SDK (semantic analysis will populate take profit cache too)
        await self._query_sdk_for_stop_loss(
            contract_id, position_entry_price, position_type
        )

        # Return take profit from cache (populated by query if found)
        return self._active_take_profits.get(contract_id)

    def get_all_stop_losses(self) -> dict[str, dict[str, Any]]:
        """
        Get all active stop loss orders across all positions.

        Returns:
            Dict mapping contract_id to stop loss data
        """
        return self._active_stop_losses.copy()

    def get_all_take_profits(self) -> dict[str, dict[str, Any]]:
        """
        Get all active take profit orders across all positions.

        Returns:
            Dict mapping contract_id to take profit data
        """
        return self._active_take_profits.copy()

    # ========================================================================
    # Cache Management API
    # ========================================================================

    def update_from_order_placed(self, order) -> None:
        """
        Update cache when ORDER_PLACED event fires.

        Args:
            order: Order object from SDK
        """
        contract_id = order.contractId

        # Check if it's a stop loss
        if self._is_stop_loss(order):
            self._active_stop_losses[contract_id] = {
                "order_id": order.id,
                "stop_price": order.stopPrice,
                "side": self._get_side_name_fn(order.side) if self._get_side_name_fn else str(order.side),
                "quantity": order.size,
                "timestamp": time.time(),
            }
            logger.debug(f"Cached stop loss: {contract_id} → SL @ ${order.stopPrice:,.2f}")

        # Check if it's a take profit
        elif self._is_take_profit(order):
            self._active_take_profits[contract_id] = {
                "order_id": order.id,
                "take_profit_price": order.limitPrice,
                "side": self._get_side_name_fn(order.side) if self._get_side_name_fn else str(order.side),
                "quantity": order.size,
                "timestamp": time.time(),
            }
            logger.debug(f"Cached take profit: {contract_id} → TP @ ${order.limitPrice:,.2f}")

    def remove_stop_loss(self, contract_id: str) -> None:
        """
        Remove stop loss from cache (when filled/cancelled).

        Args:
            contract_id: Contract ID
        """
        if contract_id in self._active_stop_losses:
            del self._active_stop_losses[contract_id]
            logger.debug(f"Removed stop loss from cache: {contract_id}")

    def remove_take_profit(self, contract_id: str) -> None:
        """
        Remove take profit from cache (when filled/cancelled).

        Args:
            contract_id: Contract ID
        """
        if contract_id in self._active_take_profits:
            del self._active_take_profits[contract_id]
            logger.debug(f"Removed take profit from cache: {contract_id}")

    def invalidate(self, contract_id: str) -> None:
        """
        Invalidate cache for a contract (force refresh on next query).

        Use this when:
        - Position updated (might have new protective orders)
        - Order modified (price might have changed)

        Args:
            contract_id: Contract ID to invalidate
        """
        if contract_id in self._active_stop_losses:
            del self._active_stop_losses[contract_id]
        if contract_id in self._active_take_profits:
            del self._active_take_profits[contract_id]
        logger.debug(f"Invalidated protective order cache for {contract_id}")

    # ========================================================================
    # SDK Query (Fallback for cache misses)
    # ========================================================================

    async def _query_sdk_for_stop_loss(
        self,
        contract_id: str,
        position_entry_price: float = None,
        position_type: int = None,
    ) -> dict[str, Any] | None:
        """
        Query SDK directly for stop loss orders (bypasses cache).

        This is called when cache is empty. Handles broker-UI stops that
        don't emit ORDER_PLACED events.

        This is NOT polling - only called on-demand when position events fire.

        Args:
            contract_id: Contract ID to query
            position_entry_price: Optional position entry price (avoids querying)
            position_type: Optional position type (1=LONG, 2=SHORT, avoids querying)

        Returns:
            Stop loss data dict or None if no stop found
        """
        if not self._suite or not self._extract_symbol_fn:
            logger.debug("SDK suite or helpers not available for query")
            return None

        symbol = self._extract_symbol_fn(contract_id)
        logger.debug(f"🔍 Querying SDK for stop loss on {symbol} (contract: {contract_id})")

        try:
            # Get the instrument manager for this symbol
            if symbol not in self._suite:
                logger.error(f"❌ Symbol {symbol} not in suite! Available: {list(self._suite.keys())}")
                return None

            instrument = self._suite[symbol]
            if not hasattr(instrument, 'orders'):
                logger.error(f"❌ Instrument {symbol} has no orders attribute!")
                return None

            # Query orders
            working_orders = await instrument.orders.get_position_orders(contract_id)
            logger.debug(f"get_position_orders returned {len(working_orders)} orders")

            # If empty, try search_open_orders - queries broker API for ALL orders
            orders_obj = instrument.orders
            if len(working_orders) == 0 and hasattr(orders_obj, 'search_open_orders'):
                logger.debug("Trying search_open_orders (broker API query)...")
                all_orders = await orders_obj.search_open_orders()
                logger.debug(f"search_open_orders returned {len(all_orders)} orders")

                # Filter for this contract
                working_orders = [o for o in all_orders if o.contractId == contract_id]
                logger.debug(f"Filtered to {len(working_orders)} orders for {contract_id}")

            # Get position data for semantic analysis
            if position_entry_price is None or position_type is None:
                logger.debug("Position data not provided, fetching from SDK...")

                try:
                    all_positions = await instrument.positions.get_all_positions()
                    logger.debug(f"get_all_positions returned {len(all_positions)} positions")

                    position = None
                    for pos in all_positions:
                        if pos.contractId == contract_id:
                            position = pos
                            logger.debug("Found matching position")
                            break

                    if not position:
                        logger.warning(f"No position found for {contract_id}")
                        return None

                    position_entry_price = position.avgPrice
                    position_type = position.type  # 1=LONG, 2=SHORT

                except Exception as pos_error:
                    logger.error(f"Error fetching position: {pos_error}")
                    return None
            else:
                logger.debug("Using provided position data (avoids hanging get_all_positions)")

            # Log position details
            pos_direction = "LONG" if position_type == 1 else "SHORT" if position_type == 2 else "UNKNOWN"
            logger.debug(f"Position: {pos_direction} @ ${position_entry_price:.2f}")

            # Analyze orders using semantic layer
            stop_loss_data = None
            take_profit_data = None

            for order in working_orders:
                if order.contractId == contract_id:
                    # Determine trigger price
                    trigger_price = order.stopPrice if order.stopPrice else order.limitPrice

                    logger.debug(f"Order #{order.id}: type={order.type_str}, trigger=${trigger_price}")

                    # Use semantic analysis to determine intent
                    intent = self._determine_order_intent(order, position_entry_price, position_type)
                    logger.debug(f"Semantic intent: {intent}")

                    if intent == "stop_loss":
                        # Found stop loss!
                        stop_loss_data = {
                            "order_id": order.id,
                            "stop_price": trigger_price,
                            "side": self._get_side_name_fn(order.side) if self._get_side_name_fn else str(order.side),
                            "quantity": order.size,
                            "timestamp": time.time(),
                        }
                        # Cache it
                        self._active_stop_losses[contract_id] = stop_loss_data
                        logger.debug(f"Found stop loss: ${trigger_price:,.2f}")

                    elif intent == "take_profit":
                        # Found take profit!
                        take_profit_data = {
                            "order_id": order.id,
                            "take_profit_price": trigger_price,
                            "side": self._get_side_name_fn(order.side) if self._get_side_name_fn else str(order.side),
                            "quantity": order.size,
                            "timestamp": time.time(),
                        }
                        # Cache it
                        self._active_take_profits[contract_id] = take_profit_data
                        logger.debug(f"Found take profit: ${trigger_price:,.2f}")

            # Return stop loss (if found)
            if stop_loss_data:
                logger.debug(f"Query result: Found stop loss @ ${stop_loss_data['stop_price']:,.2f}")
                return stop_loss_data

            # No stop found
            logger.debug("Query result: No stop loss found")
            return None

        except Exception as e:
            logger.error(f"❌ Error querying SDK for stops: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    # ========================================================================
    # Semantic Analysis (Order Intent Detection)
    # ========================================================================

    def _determine_order_intent(
        self, order, position_entry_price: float, position_type: int
    ) -> str:
        """
        Determine order intent using simplified logic.

        For positions that exist, STOP orders are protective (stop loss),
        LIMIT orders are profit targets (take profit).

        Args:
            order: Order object from SDK
            position_entry_price: Position's average entry price
            position_type: Position type (1=LONG, 2=SHORT)

        Returns:
            "stop_loss" | "take_profit" | "entry" | "unknown"
        """
        if not order or position_entry_price is None:
            return "unknown"

        # SIMPLIFIED RULE: For existing positions:
        # - STOP orders (type 3, 4, 5) = Stop Loss (protective)
        # - LIMIT orders (type 1) = Take Profit (target)
        # - MARKET orders (type 2) = Manual exit/entry

        if order.type in [3, 4, 5]:  # STOP_LIMIT, STOP, TRAILING_STOP
            # STOP orders on existing positions are stop losses
            return "stop_loss"

        elif order.type == 1:  # LIMIT
            # LIMIT orders on existing positions are take profits
            # (assuming they're closing orders, not entries)
            trigger_price = order.limitPrice

            if trigger_price is None:
                return "unknown"

            # Use position TYPE (1=LONG, 2=SHORT), not size sign
            is_long_position = (position_type == 1)
            is_short_position = (position_type == 2)

            # Verify this is actually a profit target
            if is_long_position:
                # LONG: Take profit ABOVE entry, entry BELOW
                if trigger_price > position_entry_price:
                    return "take_profit"
                else:
                    return "entry"  # Limit buy below entry = entry order
            elif is_short_position:
                # SHORT: Take profit BELOW entry, entry ABOVE
                if trigger_price < position_entry_price:
                    return "take_profit"
                else:
                    return "entry"  # Limit sell above entry = entry order
            else:
                return "unknown"

        elif order.type == 2:  # MARKET
            # Market orders could be manual exit or entry
            return "unknown"

        else:
            return "unknown"

    def _is_stop_loss(self, order) -> bool:
        """
        Detect if order is a stop loss.

        A stop loss is:
        - Type STOP (4) or STOP_LIMIT (3) or TRAILING_STOP (5)
        - AND closing a position (SELL when we were long, BUY when we were short)
        """
        # Stop orders (types 3, 4, 5)
        if order.type in [3, 4, 5]:  # STOP_LIMIT, STOP, TRAILING_STOP
            return True
        return False

    def _is_take_profit(self, order) -> bool:
        """
        Detect if order is a take profit.

        A take profit is typically:
        - Type LIMIT (1)
        - AND closing a position at a profit target
        - AND has a limit price above entry (for longs) or below (for shorts)

        Note: Without position context, we use heuristics:
        - LIMIT orders that close positions are likely take profits
        - This is not 100% accurate but good enough for logging
        """
        # For now, we'll mark LIMIT orders that close positions as potential TPs
        # This is a heuristic since we don't have full position context here
        if order.type == 1:  # LIMIT
            # Could be enhanced with position tracking to confirm
            return False  # Conservative: don't assume unless we're certain
        return False
