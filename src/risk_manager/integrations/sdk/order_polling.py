"""
Order Polling Service Module

Handles background polling for protective orders that don't emit events.

The Challenge:
    - Some platforms don't emit ORDER_PLACED events for protective stops
    - Especially common for stops placed via broker UI
    - Without detection, "No Stop Loss Grace Period" rule can't work
    - Can't rely solely on event-driven architecture

The Solution:
    - Background task polls for working orders every 5 seconds
    - Tracks seen orders to avoid duplicate logging
    - Integrates with ProtectiveOrderCache for stop loss detection
    - Lightweight and non-intrusive

Usage:
    # Initialize
    service = OrderPollingService()
    service.set_suite(suite)
    service.set_protective_cache(protective_cache)
    service.set_helpers(extract_symbol_fn, get_side_name_fn)

    # Start polling
    await service.start_polling()

    # Mark order as seen (from event handlers)
    service.mark_order_seen(order_id)

    # Stop polling
    await service.stop_polling()
"""

import asyncio
from loguru import logger
from typing import Callable


class OrderPollingService:
    """
    Background service for polling orders to detect protective stops.

    This service compensates for platforms that don't emit ORDER_PLACED
    events for all orders, especially protective stops placed via UI.
    """

    def __init__(self):
        """Initialize order polling service."""
        # SDK references (set after connection)
        self._suite = None
        self._protective_cache = None

        # Helper function references (set externally)
        self._extract_symbol_fn: Callable[[str], str] | None = None
        self._get_side_name_fn: Callable[[int], str] | None = None

        # Running state
        self._running = False

        # Polling task
        self._poll_task = None

        # Track seen orders (to avoid duplicate logging)
        self._known_orders: set[int] = set()

    def set_suite(self, suite):
        """
        Set SDK suite reference.

        Args:
            suite: TradingSuite instance
        """
        self._suite = suite

    def set_protective_cache(self, protective_cache):
        """
        Set protective order cache reference.

        Args:
            protective_cache: ProtectiveOrderCache instance
        """
        self._protective_cache = protective_cache

    def set_helpers(self, extract_symbol_fn: Callable[[str], str], get_side_name_fn: Callable[[int], str]):
        """
        Set helper function references.

        Args:
            extract_symbol_fn: Function to extract symbol from contract ID
            get_side_name_fn: Function to convert side int to name
        """
        self._extract_symbol_fn = extract_symbol_fn
        self._get_side_name_fn = get_side_name_fn

    async def start_polling(self):
        """
        Start the background polling task.

        Creates a task that polls for orders every 5 seconds.
        """
        if self._poll_task and not self._poll_task.done():
            logger.warning("Order polling task already running")
            return

        self._running = True
        self._poll_task = asyncio.create_task(self._poll_orders())
        logger.debug("Order polling task started")

    async def stop_polling(self):
        """
        Stop the background polling task.

        Cancels the task gracefully.
        """
        self._running = False

        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            logger.debug("Order polling task stopped")

    def mark_order_seen(self, order_id: int):
        """
        Mark an order as seen (to avoid duplicate logging).

        Called from event handlers when ORDER_PLACED fires.

        Args:
            order_id: Order ID to mark as seen
        """
        self._known_orders.add(order_id)

    def mark_order_unseen(self, order_id: int):
        """
        Remove order from seen list (when cancelled/filled).

        Args:
            order_id: Order ID to remove
        """
        self._known_orders.discard(order_id)

    async def _poll_orders(self):
        """
        Background task that polls for active orders periodically.

        Runs every 5 seconds and checks for new working orders.
        Integrates with ProtectiveOrderCache to detect protective stops.
        """
        logger.debug("Order polling task started")

        while self._running:
            try:
                await asyncio.sleep(5)  # Poll every 5 seconds

                if not self._suite:
                    logger.debug("Suite not available yet")
                    continue

                # Get all working orders from all instruments
                # Note: get_position_orders() requires contract_id, so we need to get positions first
                orders = []
                for symbol, instrument in self._suite.items():
                    if not hasattr(instrument, 'positions') or not hasattr(instrument, 'orders'):
                        continue

                    # Get all positions for this instrument
                    try:
                        positions = await instrument.positions.get_all_positions()
                        for position in positions:
                            # Get orders for this position's contract (needs await)
                            position_orders = await instrument.orders.get_position_orders(position.contractId)
                            orders.extend(position_orders)
                    except Exception as e:
                        logger.debug(f"Error getting orders for {symbol}: {e}")
                        continue

                logger.debug(f"Polling found {len(orders)} working orders")

                for order in orders:
                    order_id = order.id

                    # Skip if we've already seen this order
                    if order_id in self._known_orders:
                        continue

                    # Mark as seen
                    self._known_orders.add(order_id)

                    # Log new orders at INFO level (concise)
                    if self._extract_symbol_fn and self._get_side_name_fn:
                        symbol = self._extract_symbol_fn(order.contractId)
                        side_name = self._get_side_name_fn(order.side)
                        logger.info(f"🔍 NEW ORDER (polling): {symbol} {order.type_str} {side_name} {order.size}")
                        logger.debug(f"Stop: {order.stopPrice}, Limit: {order.limitPrice}, Status: {order.status}")

                    # Check if it's a protective order and cache it
                    if self._protective_cache:
                        self._protective_cache.update_from_order_placed(order)

            except asyncio.CancelledError:
                logger.debug("Order polling task cancelled")
                break
            except Exception as e:
                logger.warning(f"Error polling orders: {e}")
                import traceback
                logger.debug(traceback.format_exc())

        logger.debug("Order polling task stopped")
