"""
Event Router Module

Routes SDK events to specialized processors and publishes risk events.

This module handles ALL 16 event types from the SDK:
- 8 ORDER events (placed, filled, partial, cancelled, rejected, modified, expired, unknown)
- 4 POSITION events (opened, closed, updated, handle_position_event)
- 4 LEGACY events (old SignalR callbacks for backward compatibility)

Each handler:
1. Validates and extracts event data
2. Performs deduplication (prevents 3x events from 3 instruments)
3. Delegates to specialized processors (caches, calculators, correlators)
4. Logs human-readable messages
5. Publishes enriched events to risk event bus

After extraction, TradingIntegration is purely facade + connection orchestration.
"""

import time
from typing import Any
from loguru import logger

from risk_manager.core.events import EventBus, RiskEvent, EventType
from risk_manager.integrations.adapters import adapter


class EventRouter:
    """
    Routes SDK events to processors and publishes risk events.

    This is the coordination layer between SDK and risk system.
    All 16 event handlers live here, delegating to specialized modules.
    """

    def __init__(
        self,
        protective_cache,
        order_correlator,
        pnl_calculator,
        order_polling,
        event_bus: EventBus,
    ):
        """
        Initialize event router with all dependencies.

        Args:
            protective_cache: ProtectiveOrderCache instance
            order_correlator: OrderCorrelator instance
            pnl_calculator: UnrealizedPnLCalculator instance
            order_polling: OrderPollingService instance
            event_bus: EventBus for publishing risk events
        """
        self._protective_cache = protective_cache
        self._order_correlator = order_correlator
        self._pnl_calculator = pnl_calculator
        self._order_polling = order_polling
        self._event_bus = event_bus

        # Will be set externally after initialization
        self._client = None
        self._suite = None

        # Helper function references (set externally)
        # These come from TradingIntegration and provide SDK-specific logic
        self._extract_symbol_fn = None
        self._get_stop_loss_fn = None
        self._get_take_profit_fn = None

        # Deduplication cache
        # SDK EventBus emits events from each instrument manager separately,
        # so a single order can trigger 3 identical events (one per instrument)
        self._event_cache: dict[tuple[str, str], float] = {}
        self._event_cache_ttl = 5.0

        logger.debug("EventRouter initialized")

    def set_client(self, client):
        """Set SDK client reference."""
        self._client = client

    def set_suite(self, suite):
        """Set SDK suite reference."""
        self._suite = suite

    def set_helper_functions(
        self,
        extract_symbol_fn,
        get_stop_loss_fn,
        get_take_profit_fn,
    ):
        """Set helper function references from TradingIntegration."""
        self._extract_symbol_fn = extract_symbol_fn
        self._get_stop_loss_fn = get_stop_loss_fn
        self._get_take_profit_fn = get_take_profit_fn

    def _is_duplicate_event(self, event_type: str, entity_id: str) -> bool:
        """
        Check if this event is a duplicate.

        The SDK EventBus emits events from each instrument manager separately,
        so a single order can trigger 3 identical events (one per instrument).

        We use a TTL-based cache (5 seconds) to deduplicate events.
        """
        current_time = time.time()
        cache_key = (event_type, entity_id)

        # Clean expired entries
        expired_keys = [
            k for k, timestamp in self._event_cache.items()
            if current_time - timestamp > self._event_cache_ttl
        ]
        for k in expired_keys:
            del self._event_cache[k]

        # Check if seen recently
        if cache_key in self._event_cache:
            return True

        # Mark as seen
        self._event_cache[cache_key] = current_time
        return False

    # ============================================================================
    # Helper Methods (7 methods)
    # ============================================================================

    def _get_side_name(self, side: int) -> str:
        """Convert side int to name (0=BUY, 1=SELL)."""
        return "BUY" if side == 0 else "SELL"

    def _get_position_type_name(self, pos_type: int) -> str:
        """Convert position type to name (1=LONG, 2=SHORT)."""
        if pos_type == 1:
            return "LONG"
        elif pos_type == 2:
            return "SHORT"
        else:
            return "FLAT"

    def _get_order_placement_display(self, order) -> str:
        """
        Get human-readable order placement display.

        Returns formatted string like:
        - "🛡️ STOP LOSS @ $3975.50 | SELL | Qty: 1" (stop loss protection placed)
        - "🎯 TAKE PROFIT @ $3980.00 | SELL | Qty: 1" (take profit placed)
        - "MARKET | BUY | Qty: 1" (manual market order)
        - "LIMIT @ $3978.00 | BUY | Qty: 1" (manual limit order)
        """
        order_type = order.type_str
        side = self._get_side_name(order.side)
        qty = order.size

        if self._is_stop_loss(order):
            price = order.stopPrice
            return f"🛡️ STOP LOSS @ ${price:.2f} | {side} | Qty: {qty}"
        elif order_type == "LIMIT":
            price = order.limitPrice
            return f"LIMIT @ ${price:.2f} | {side} | Qty: {qty}"
        elif order_type == "MARKET":
            return f"MARKET | {side} | Qty: {qty}"
        elif order_type == "STOP_LIMIT":
            price = order.stopPrice
            return f"STOP_LIMIT @ ${price:.2f} | {side} | Qty: {qty}"
        elif order_type == "TRAILING_STOP":
            return f"TRAILING_STOP | {side} | Qty: {qty}"
        else:
            return f"{order_type} | {side} | Qty: {qty}"

    def _get_order_type_display(self, order) -> str:
        """
        Get human-readable order type display (for fills).

        Returns formatted string like:
        - "STOP LOSS @ $3975.50" (stop order closing a position)
        - "TAKE PROFIT @ $3980.00" (limit order closing at profit)
        - "MARKET" (manual market order)
        - "LIMIT @ $3978.00" (manual limit order)
        """
        order_type = order.type_str

        if self._is_stop_loss(order):
            price = order.stopPrice or order.filledPrice
            return f"🛑 STOP LOSS @ ${price:.2f}"
        elif self._is_take_profit(order):
            price = order.limitPrice or order.filledPrice
            return f"🎯 TAKE PROFIT @ ${price:.2f}"
        elif order_type == "MARKET":
            return "MARKET"
        elif order_type == "LIMIT":
            return f"LIMIT @ ${order.limitPrice:.2f}" if order.limitPrice else "LIMIT"
        elif order_type == "STOP":
            return f"STOP @ ${order.stopPrice:.2f}" if order.stopPrice else "STOP"
        elif order_type == "STOP_LIMIT":
            return f"STOP_LIMIT @ ${order.stopPrice:.2f}" if order.stopPrice else "STOP_LIMIT"
        elif order_type == "TRAILING_STOP":
            return "TRAILING_STOP"
        else:
            return order_type

    def _get_order_emoji(self, order) -> str:
        """Get emoji based on order type/intent."""
        if self._is_stop_loss(order):
            return "🛑"  # Stop sign for stop loss
        elif self._is_take_profit(order):
            return "🎯"  # Target for take profit
        else:
            return "💰"  # Money bag for regular fills

    def _is_stop_loss(self, order) -> bool:
        """
        Detect if order is a stop loss.

        A stop loss is:
        - Type STOP (4) or STOP_LIMIT (3)
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

    # ============================================================================
    # ORDER Event Handlers (8 handlers)
    # ============================================================================

    async def _on_order_placed(self, event) -> None:
        """Handle ORDER_PLACED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_PLACED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate FIRST (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_placed", str(order.id)):
                return

            # Debug: Show payload AFTER dedup (only for unique events)
            logger.debug(f"📦 ORDER_PLACED Payload: order_id={order.id}, type={order.type}, stopPrice={order.stopPrice}")

            symbol = self._extract_symbol_fn(order.contractId)
            order_type_str = order.type_str

            # Build descriptive order placement message
            order_desc = self._get_order_placement_display(order)

            logger.info(f"📋 ORDER PLACED - {symbol} | {order_desc}")

            # Order details at DEBUG level only
            logger.debug(f"Order ID: {order.id}, Type: {order.type} ({order.type_str}), Stop: {order.stopPrice}, Limit: {order.limitPrice}, Status: {order.status}")

            # Cache active protective orders (delegated to cache module)
            self._protective_cache.update_from_order_placed(order)

            # Mark order as seen by polling service (prevents duplicate logging)
            self._order_polling.mark_order_seen(order.id)

            # Bridge to risk event bus
            risk_event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={
                    "symbol": symbol,
                    "order_id": order.id,
                    "side": self._get_side_name(order.side),
                    "quantity": order.size,
                    "price": getattr(order, 'limitPrice', None),
                    "order_type": order.type,
                    "order_type_str": order_type_str,
                    "stop_price": order.stopPrice,
                    "limit_price": order.limitPrice,
                    "is_stop_loss": self._is_stop_loss(order),
                    "raw_data": data,
                },
                source="trading_sdk",
            )
            await self._event_bus.publish(risk_event)

        except Exception as e:
            logger.error(f"Error handling ORDER_PLACED: {e}")
            logger.exception(e)

    async def _on_order_filled(self, event) -> None:
        """Handle ORDER_FILLED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_FILLED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate FIRST (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_filled", str(order.id)):
                return

            # Debug: Show payload AFTER dedup (only for unique events)
            logger.debug(f"📦 ORDER_FILLED Payload: order_id={order.id}, type={order.type}, stopPrice={order.stopPrice}")

            symbol = self._extract_symbol_fn(order.contractId)
            order_type = self._get_order_type_display(order)

            # Use different emoji for stop loss vs take profit vs manual
            emoji = self._get_order_emoji(order)

            # Concise fill message with formatted price
            logger.info(
                f"{emoji} ORDER FILLED - {symbol} {self._get_side_name(order.side)} "
                f"{order.fillVolume} @ ${order.filledPrice:,.2f}"
            )

            # Order details at DEBUG level only
            logger.debug(f"Order ID: {order.id}, Type: {order.type} ({order.type_str}), Stop: {order.stopPrice}, Limit: {order.limitPrice}, Status: {order.status}")

            # Remove from known orders (it's filled now) - Delegated to OrderPollingService
            self._order_polling.mark_order_unseen(order.id)

            # Track this fill for correlation with position updates - Delegated to OrderCorrelator
            is_sl = self._is_stop_loss(order)
            is_tp = self._is_take_profit(order)
            fill_type = "stop_loss" if is_sl else "take_profit" if is_tp else "manual"

            self._order_correlator.record_fill(
                contract_id=order.contractId,
                fill_type=fill_type,
                fill_price=order.filledPrice,
                side=self._get_side_name(order.side),
                order_id=order.id
            )
            logger.debug(f"Recorded {fill_type} fill | _is_stop_loss={is_sl}, _is_take_profit={is_tp}")

            # Remove from active caches (order is now filled)
            if is_sl:
                self._protective_cache.remove_stop_loss(order.contractId)

            if is_tp:
                self._protective_cache.remove_take_profit(order.contractId)

            # Bridge to risk event bus
            risk_event = RiskEvent(
                event_type=EventType.ORDER_FILLED,
                data={
                    "account_id": order.accountId,  # ← CRITICAL: Rules need account_id
                    "symbol": symbol,
                    "order_id": order.id,
                    "side": self._get_side_name(order.side),
                    "quantity": order.fillVolume,
                    "price": order.filledPrice,
                    "order_type": order.type,
                    "order_type_str": order.type_str,
                    "is_stop_loss": self._is_stop_loss(order),
                    "is_take_profit": self._is_take_profit(order),
                    "stop_price": order.stopPrice,
                    "limit_price": order.limitPrice,
                    "raw_data": data,
                },
                source="trading_sdk",
            )
            await self._event_bus.publish(risk_event)

        except Exception as e:
            logger.error(f"Error handling ORDER_FILLED: {e}")
            logger.exception(e)

    async def _on_order_partial_fill(self, event) -> None:
        """Handle ORDER_PARTIAL_FILL event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_PARTIAL_FILL event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload
            logger.debug(f"📦 ORDER_PARTIAL_FILL Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_partial_fill", str(order.id)):
                return

            symbol = self._extract_symbol_fn(order.contractId)

            logger.info(
                f"📊 ORDER PARTIALLY FILLED - {symbol} | ID: {order.id} | Filled: {order.fillVolume}/{order.size} @ ${order.filledPrice:.2f}"
            )

        except Exception as e:
            logger.error(f"Error handling ORDER_PARTIAL_FILL: {e}")

    async def _on_order_cancelled(self, event) -> None:
        """Handle ORDER_CANCELLED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_CANCELLED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload
            logger.debug(f"📦 ORDER_CANCELLED Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_cancelled", str(order.id)):
                return

            symbol = self._extract_symbol_fn(order.contractId)

            logger.info(f"❌ ORDER CANCELLED - {symbol} | ID: {order.id}")

            # Remove from known orders (it's cancelled now) - Delegated to OrderPollingService
            self._order_polling.mark_order_unseen(order.id)

            # Remove from active caches (order is now cancelled)
            # Note: Cache removal is idempotent (safe to call even if not in cache)
            self._protective_cache.remove_stop_loss(order.contractId)
            self._protective_cache.remove_take_profit(order.contractId)

        except Exception as e:
            logger.error(f"Error handling ORDER_CANCELLED: {e}")

    async def _on_order_rejected(self, event) -> None:
        """Handle ORDER_REJECTED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_REJECTED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload
            logger.debug(f"📦 ORDER_REJECTED Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_rejected", str(order.id)):
                return

            symbol = self._extract_symbol_fn(order.contractId)

            logger.warning(f"⛔ ORDER REJECTED - {symbol} | ID: {order.id}")

        except Exception as e:
            logger.error(f"Error handling ORDER_REJECTED: {e}")

    async def _on_order_modified(self, event) -> None:
        """Handle ORDER_MODIFIED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_MODIFIED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload at DEBUG level
            logger.debug(f"📦 ORDER_MODIFIED Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_modified", str(order.id)):
                return

            symbol = self._extract_symbol_fn(order.contractId)
            order_type_str = order.type_str

            # Build descriptive order modification message
            order_desc = self._get_order_placement_display(order)

            logger.info(f"✏️  ORDER MODIFIED - {symbol} | {order_desc}")

            # Order details at DEBUG level only
            logger.debug(f"Order ID: {order.id}, Type: {order.type} ({order_type_str}), Stop: {order.stopPrice}, Limit: {order.limitPrice}, Status: {order.status}")

            # Invalidate protective cache (order parameters changed)
            # This forces a fresh query on next position update
            self._protective_cache.invalidate_for_order(order.id)

        except Exception as e:
            logger.error(f"Error handling ORDER_MODIFIED: {e}")

    async def _on_order_expired(self, event) -> None:
        """Handle ORDER_EXPIRED event from SDK EventBus."""
        logger.debug(f"🔔 ORDER_EXPIRED event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Debug: Show full payload
            logger.debug(f"📦 ORDER_EXPIRED Payload: {data}")

            order = data.get('order') if isinstance(data, dict) else None

            if not order:
                return

            # Check for duplicate (prevents 3x events from 3 instruments)
            if self._is_duplicate_event("order_expired", str(order.id)):
                return

            symbol = self._extract_symbol_fn(order.contractId)

            logger.info(f"⏰ ORDER EXPIRED - {symbol} | ID: {order.id}")

        except Exception as e:
            logger.error(f"Error handling ORDER_EXPIRED: {e}")

    async def _on_unknown_event(self, event) -> None:
        """Handle unknown event from SDK EventBus."""
        logger.debug(f"🔔 UNKNOWN event received")
        logger.debug(f"📦 UNKNOWN Event Payload: {event}")

    # ============================================================================
    # POSITION Event Handlers (4 handlers)
    # ============================================================================

    async def _on_position_opened(self, event) -> None:
        """Handle POSITION_OPENED event from SDK EventBus."""
        await self._handle_position_event(event, "OPENED")

    async def _on_position_closed(self, event) -> None:
        """Handle POSITION_CLOSED event from SDK EventBus."""
        await self._handle_position_event(event, "CLOSED")

    async def _on_position_updated(self, event) -> None:
        """Handle POSITION_UPDATED event from SDK EventBus."""
        await self._handle_position_event(event, "UPDATED")

    async def _handle_position_event(self, event, action_name: str) -> None:
        """
        Handle POSITION events (OPENED, CLOSED, UPDATED).

        This is the most complex handler because it:
        1. Checks protective orders BEFORE dedup (critical for detecting silent orders)
        2. Performs deduplication
        3. Correlates with recent ORDER_FILLED events
        4. Calculates realized P&L for CLOSED positions
        5. Tracks OPENED positions in P&L calculator
        6. Queries protective orders (stop loss / take profit)
        7. Publishes enriched event to risk bus
        """
        logger.debug(f"🔔 POSITION_{action_name} event received")
        try:
            data = event.data if hasattr(event, 'data') else {}

            # Extract position details
            contract_id = data.get('contractId')
            size = data.get('size', 0)
            avg_price = data.get('averagePrice', 0.0)
            unrealized_pnl = data.get('unrealizedPnl', 0.0)
            pos_type = data.get('type', 0)

            # CRITICAL: Check protective orders BEFORE dedup
            # Second order placements don't trigger unique events!
            # Must query on EVERY event to catch them
            if action_name in ["OPENED", "UPDATED"]:
                logger.debug(f"Checking protective orders (pre-dedup)")

                # Always invalidate cache and query fresh
                self._protective_cache.invalidate(contract_id)

                # Query with position data from event
                stop_loss_early = await self._get_stop_loss_fn(
                    contract_id, avg_price, pos_type
                )
                take_profit_early = await self._get_take_profit_fn(
                    contract_id, avg_price, pos_type
                )

                # Log findings (DEBUG level for early check)
                logger.debug(f"Pre-dedup query: SL={bool(stop_loss_early)}, TP={bool(take_profit_early)}")

            # Check for duplicate (prevents 3x events from 3 instruments)
            # Use contract_id + action for deduplication key
            dedup_key = f"{contract_id}_{action_name}"
            if self._is_duplicate_event(f"position_{action_name.lower()}", dedup_key):
                return  # Exit after protective order check

            # Debug: Show payload AFTER dedup (only for unique events)
            logger.debug(f"📦 POSITION_{action_name} Payload keys: {list(data.keys())}")

            # Check if position data includes protective stops (some platforms embed them)
            if 'stopLoss' in data or 'takeProfit' in data or 'protectiveOrders' in data:
                logger.info(f"🛡️  Position has protective orders: SL={data.get('stopLoss')}, TP={data.get('takeProfit')}")

            symbol = self._extract_symbol_fn(contract_id)

            # Check if this position update correlates with a recent order fill (delegated to OrderCorrelator)
            fill_type = self._order_correlator.get_fill_type(contract_id)
            logger.debug(f"🔍 Checking recent fills for {contract_id}: fill_type={fill_type}")
            logger.debug(f"   Recent fills cache: {self._order_correlator.get_active_contracts()}")

            # Build position update label with fill context
            position_label = f"📊 POSITION {action_name}"
            if fill_type == "stop_loss":
                position_label = f"🛑 POSITION {action_name} (STOP LOSS)"
            elif fill_type == "take_profit":
                position_label = f"🎯 POSITION {action_name} (TAKE PROFIT)"

            # Concise position message with formatted numbers
            logger.info(
                f"{position_label} - {symbol} {self._get_position_type_name(pos_type)} "
                f"{size} @ ${avg_price:,.2f} | P&L: ${unrealized_pnl:,.2f}"
            )

            # Show active stop loss/take profit for this position (if any)
            # CRITICAL: Always check on EVERY event, even if deduped for logging
            # This ensures we catch new orders that don't trigger unique events
            if action_name in ["OPENED", "UPDATED"]:
                logger.debug("Checking protective orders (post-dedup)")

                # ALWAYS invalidate cache on position updates
                # This forces a fresh query EVERY time, catching new orders
                logger.debug("Invalidating protective order cache")
                self._protective_cache.invalidate(contract_id)

                # Pass position data from event to avoid hanging get_all_positions() call
                # pos_type: 1=LONG, 2=SHORT
                stop_loss = await self._get_stop_loss_fn(
                    contract_id, avg_price, pos_type
                )
                take_profit = await self._get_take_profit_fn(
                    contract_id, avg_price, pos_type
                )

                if stop_loss:
                    logger.info(f"  🛡️  Stop Loss: ${stop_loss['stop_price']:,.2f}")
                else:
                    logger.warning(f"  ⚠️  NO STOP LOSS")

                if take_profit:
                    logger.info(f"  🎯 Take Profit: ${take_profit['take_profit_price']:,.2f}")
                else:
                    logger.info("  ℹ️  No take profit order")

            # Bridge to risk event bus
            event_type_map = {
                "OPENED": EventType.POSITION_OPENED,
                "CLOSED": EventType.POSITION_CLOSED,  # Fixed: was POSITION_UPDATED
                "UPDATED": EventType.POSITION_UPDATED,
            }

            # Get active stop loss/take profit data for this position
            # Note: We already queried this above for logging, cache will make this instant
            stop_loss_for_event = await self._get_stop_loss_fn(
                contract_id, avg_price, pos_type
            )
            take_profit_for_event = await self._get_take_profit_fn(
                contract_id, avg_price, pos_type
            )

            # Calculate realized P&L for CLOSED positions (delegated to UnrealizedPnLCalculator)
            # SDK doesn't provide profitAndLoss, so we calculate it ourselves!
            realized_pnl = None
            if action_name == "CLOSED":
                # Get exit price from recent fill (delegated to OrderCorrelator), not from position event!
                # POSITION_CLOSED gives us avg_price (entry), not exit price
                # The actual exit price comes from the ORDER_FILLED event
                exit_price = self._order_correlator.get_fill_price(contract_id)
                if exit_price:
                    logger.debug(f"Using exit price from recent fill: ${exit_price:,.2f}")
                else:
                    logger.warning(f"No recent fill found for {contract_id}, using position avg_price: ${avg_price:,.2f}")
                    exit_price = avg_price  # Fallback

                # Calculate realized P&L using consolidated calculator
                realized_pnl_decimal = self._pnl_calculator.calculate_realized_pnl(contract_id, exit_price)

                if realized_pnl_decimal is not None:
                    realized_pnl = float(realized_pnl_decimal)

                    # Log P&L details
                    logger.info(f"💰 Realized P&L: ${realized_pnl:+,.2f}")
                    logger.debug(f"   Exit price: ${exit_price:,.2f}")

                    # Remove from unrealized P&L calculator
                    self._pnl_calculator.remove_position(contract_id)
                else:
                    logger.warning(f"⚠️  Position closed but not tracked! Can't calculate P&L for {contract_id}")

            # Track OPENED positions for P&L calculation (consolidated in UnrealizedPnLCalculator)
            elif action_name == "OPENED":
                side = 'long' if size > 0 else 'short'

                # Track position in consolidated calculator (handles both unrealized and realized P&L)
                self._pnl_calculator.update_position(contract_id, {
                    'price': avg_price,
                    'size': size,
                    'side': side,
                    'symbol': symbol,
                })
                logger.debug(f"📝 Position tracked in calculator: {contract_id} @ ${avg_price:,.2f} x {size} ({side})")

                # IMMEDIATE: Try to get current price and seed the calculator
                # This gives us an initial P&L even if polling hasn't started yet
                try:
                    instrument = self._suite.get(symbol)
                    if instrument and hasattr(instrument, 'last_price') and instrument.last_price:
                        current_price = instrument.last_price
                        if current_price > 0:
                            self._pnl_calculator.update_quote(symbol, current_price)
                            logger.info(f"  💹 Initial price loaded: {symbol} @ ${current_price:.2f}")
                except Exception as e:
                    logger.debug(f"Could not get initial price for {symbol}: {e}")

            risk_event = RiskEvent(
                event_type=event_type_map.get(action_name, EventType.POSITION_UPDATED),
                data={
                    "account_id": self._client.account_info.id if self._client else None,  # ← CRITICAL: Rules need account_id
                    "symbol": symbol,
                    "contractId": contract_id,  # ← CRITICAL: Rules need contractId (for enforcement)
                    "contract_id": contract_id,
                    "size": size,
                    "side": "long" if size > 0 else "short" if size < 0 else "flat",
                    "average_price": avg_price,
                    "unrealized_pnl": unrealized_pnl,
                    "profitAndLoss": realized_pnl,  # Add realized P&L for closed positions
                    "action": action_name.lower(),
                    "fill_type": fill_type,  # "stop_loss", "take_profit", "manual", or None
                    "is_stop_loss": fill_type == "stop_loss",
                    "is_take_profit": fill_type == "take_profit",
                    "stop_loss": stop_loss_for_event,  # Active stop loss order data (or None)
                    "take_profit": take_profit_for_event,  # Active take profit order data (or None)
                    "raw_data": data,
                },
                source="trading_sdk",
            )

            # ============================================================================
            # SHADOW MODE: Canonical Domain Model (No Behavior Change)
            # ============================================================================
            # Convert SDK position to canonical Position type
            # This runs in parallel with existing dict-based event.data
            # Rules can gradually migrate from event.data to event.position
            try:
                # Skip adapter for FLAT/CLOSED positions (type=0)
                # Adapter only handles LONG (1) and SHORT (2)
                if action_name == "CLOSED" or pos_type == 0 or size == 0:
                    logger.debug(f"  ⚠️  Skipping adapter for FLAT position (shadow mode)")
                    risk_event.position = None
                else:
                    # Get current market price for P&L calculation
                    current_price = None
                    if self._suite and hasattr(self._suite, 'get'):
                        try:
                            instrument = self._suite.get(symbol)
                            if instrument and hasattr(instrument, 'last_price'):
                                current_price = instrument.last_price
                        except (KeyError, AttributeError):
                            pass  # No market price available yet

                    # Convert to canonical Position
                    canonical_position = adapter.normalize_position_from_dict(
                        position_data={
                            "contractId": contract_id,
                            "avgPrice": avg_price,
                            "size": size,
                            "type": pos_type,
                        },
                        current_price=current_price,
                        account_id=None,  # Will be added when we have account context
                    )

                    # Attach canonical position to event (shadow mode - doesn't break existing code)
                    risk_event.position = canonical_position

                    # Log the normalization for visibility
                    logger.info(
                        f"  🔄 CANONICAL: {symbol} → {canonical_position.symbol_root} | "
                        f"Side: {canonical_position.side.value.upper()} | "
                        f"Qty: {canonical_position.quantity} | "
                        f"P&L: {canonical_position.unrealized_pnl}"
                    )

            except Exception as e:
                # Log adapter errors but don't crash - shadow mode is best-effort
                logger.warning(f"  ⚠️  Adapter error (shadow mode): {e}")
                risk_event.position = None

            await self._event_bus.publish(risk_event)

        except Exception as e:
            logger.error(f"Error handling POSITION_{action_name}: {e}")
            logger.exception(e)

    # ============================================================================
    # LEGACY SignalR Event Handlers (4 handlers - for backward compatibility)
    # ============================================================================

    async def _on_position_update_old(self, data: Any) -> None:
        """
        Handle position update from SignalR.

        SignalR sends data in format:
        [{'action': 1, 'data': {'contractId': 123, 'size': 2, ...}}]

        Actions:
        - 1 = Add/Update
        - 2 = Remove/Close
        """
        logger.debug(f"🔔 _on_position_update callback invoked (received {len(data) if isinstance(data, list) else 1} update(s))")
        try:
            if not isinstance(data, list):
                logger.warning(f"Position update not a list: {type(data)}")
                return

            for update in data:
                action = update.get('action', 0)
                position_data = update.get('data', {})

                # Extract position details
                contract_id = position_data.get('contractId')
                size = position_data.get('size', 0)
                avg_price = position_data.get('averagePrice', 0.0)
                unrealized_pnl = position_data.get('unrealizedPnl', 0.0)

                # Determine symbol from contract ID
                symbol = self._extract_symbol_fn(contract_id)

                logger.info("=" * 80)
                logger.info(f"📊 POSITION UPDATE - {symbol}")
                logger.info(
                    f"   Action: {action} | Size: {size} | Price: ${avg_price:.2f} | "
                    f"Unrealized P&L: ${unrealized_pnl:.2f}"
                )
                logger.info("=" * 80)

                # Determine event type based on action and size
                if action == 1 and size != 0:
                    # Position opened or updated
                    event_type = EventType.POSITION_UPDATED

                    risk_event = RiskEvent(
                        event_type=event_type,
                        data={
                            "symbol": symbol,
                            "contract_id": contract_id,
                            "size": size,
                            "side": "long" if size > 0 else "short",
                            "average_price": avg_price,
                            "unrealized_pnl": unrealized_pnl,
                            "raw_data": position_data,
                        },
                        source="trading_sdk",
                    )

                    await self._event_bus.publish(risk_event)
                    logger.debug(f"Bridged {event_type} event for {symbol}")

                elif action == 2 or (action == 1 and size == 0):
                    # Position closed
                    risk_event = RiskEvent(
                        event_type=EventType.POSITION_CLOSED,
                        data={
                            "symbol": symbol,
                            "contract_id": contract_id,
                            "realized_pnl": position_data.get('realizedPnl', 0.0),
                            "raw_data": position_data,
                        },
                        source="trading_sdk",
                    )

                    await self._event_bus.publish(risk_event)
                    logger.debug(f"Bridged POSITION_CLOSED event for {symbol}")

        except Exception as e:
            logger.error(f"Error handling position update: {e}")
            logger.exception(e)

    async def _on_order_update(self, data: Any) -> None:
        """
        Handle order update from SignalR.

        SignalR sends data in format:
        [{'action': 1, 'data': {'id': 123, 'status': 'Filled', ...}}]
        """
        logger.debug(f"🔔 _on_order_update callback invoked (received {len(data) if isinstance(data, list) else 1} update(s))")
        try:
            if not isinstance(data, list):
                logger.warning(f"Order update not a list: {type(data)}")
                return

            for update in data:
                action = update.get('action', 0)
                order_data = update.get('data', {})

                # Extract order details
                order_id = order_data.get('id')
                status = order_data.get('status', 'Unknown')
                side = order_data.get('side', 'Unknown')
                quantity = order_data.get('quantity', 0)
                price = order_data.get('price', 0.0)
                filled_quantity = order_data.get('filledQuantity', 0)
                contract_id = order_data.get('contractId')

                symbol = self._extract_symbol_fn(contract_id)

                logger.info("=" * 80)
                logger.info(f"📋 ORDER UPDATE - {symbol}")
                logger.info(
                    f"   ID: {order_id} | Status: {status} | Side: {side} | "
                    f"Qty: {quantity} | Filled: {filled_quantity}"
                )
                logger.info("=" * 80)

                # Map status to event type
                event_type = None
                if status in ['Working', 'Accepted', 'Pending']:
                    event_type = EventType.ORDER_PLACED
                elif status == 'Filled':
                    event_type = EventType.ORDER_FILLED
                elif status == 'Cancelled':
                    event_type = EventType.ORDER_CANCELLED
                elif status == 'Rejected':
                    event_type = EventType.ORDER_REJECTED

                if event_type:
                    risk_event = RiskEvent(
                        event_type=event_type,
                        data={
                            "symbol": symbol,
                            "order_id": order_id,
                            "status": status,
                            "side": side,
                            "quantity": quantity,
                            "price": price,
                            "filled_quantity": filled_quantity,
                            "raw_data": order_data,
                        },
                        source="trading_sdk",
                    )

                    await self._event_bus.publish(risk_event)
                    logger.debug(f"Bridged {event_type} event for {symbol}")

        except Exception as e:
            logger.error(f"Error handling order update: {e}")
            logger.exception(e)

    async def _on_trade_update(self, data: Any) -> None:
        """
        Handle trade update from SignalR.

        SignalR sends data in format:
        [{'action': 1, 'data': {'id': 123, 'price': 21500.0, ...}}]
        """
        logger.debug(f"🔔 _on_trade_update callback invoked (received {len(data) if isinstance(data, list) else 1} update(s))")
        try:
            if not isinstance(data, list):
                logger.warning(f"Trade update not a list: {type(data)}")
                return

            for update in data:
                action = update.get('action', 0)
                trade_data = update.get('data', {})

                # Extract trade details
                trade_id = trade_data.get('id')
                price = trade_data.get('price', 0.0)
                quantity = trade_data.get('quantity', 0)
                side = trade_data.get('side', 'Unknown')
                contract_id = trade_data.get('contractId')

                symbol = self._extract_symbol_fn(contract_id)

                logger.info("=" * 80)
                logger.info(f"💰 TRADE EXECUTED - {symbol}")
                logger.info(
                    f"   ID: {trade_id} | Side: {side} | Qty: {quantity} | "
                    f"Price: ${price:.2f}"
                )
                logger.info("=" * 80)

                risk_event = RiskEvent(
                    event_type=EventType.TRADE_EXECUTED,
                    data={
                        "symbol": symbol,
                        "trade_id": trade_id,
                        "side": side,
                        "quantity": quantity,
                        "price": price,
                        "raw_data": trade_data,
                    },
                    source="trading_sdk",
                )

                await self._event_bus.publish(risk_event)
                logger.debug(f"Bridged TRADE_EXECUTED event for {symbol}")

        except Exception as e:
            logger.error(f"Error handling trade update: {e}")
            logger.exception(e)

    async def _on_account_update(self, data: Any) -> None:
        """
        Handle account update from SignalR.

        Account updates are frequent (every few seconds) and mostly contain
        balance changes. We log them but don't forward to risk engine.
        """
        logger.debug(f"🔔 _on_account_update callback invoked (received {len(data) if isinstance(data, list) else 1} update(s))")
        try:
            if not isinstance(data, list):
                return

            for update in data:
                account_data = update.get('data', {})
                balance = account_data.get('balance', 0.0)
                realized_pnl = account_data.get('realizedPnl', 0.0)
                unrealized_pnl = account_data.get('unrealizedPnl', 0.0)

                # Log account updates with P&L info
                logger.info("=" * 80)
                logger.info(f"💼 ACCOUNT UPDATE")
                logger.info(
                    f"   Balance: ${balance:,.2f} | "
                    f"Realized P&L: ${realized_pnl:.2f} | "
                    f"Unrealized P&L: ${unrealized_pnl:.2f}"
                )
                logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Error handling account update: {e}")
