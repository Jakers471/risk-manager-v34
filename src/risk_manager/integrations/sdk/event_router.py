"""
Event Router Module

Routes SDK events to specialized processors and publishes risk events.

The Challenge:
    - SDK emits 15+ event types (order, position, trade, account)
    - Each event needs parsing, deduplication, processing, and transformation
    - Events trigger updates to multiple subsystems (caches, calculators, etc.)
    - Complex business logic embedded in event handlers (~600 lines)
    
The Solution:
    - Centralize all event routing in one module
    - Delegate to specialized processors (caches, calculators, correlators)
    - Thin handlers that coordinate rather than implement logic
    - Clean separation: routing vs processing

This is the final extraction in the modular architecture.
After this, TradingIntegration is just facade + connection orchestration.
"""

import time
from typing import Any, Callable
from loguru import logger

from risk_manager.core.events import EventBus, RiskEvent, EventType


class EventRouter:
    """
    Routes SDK events to processors and publishes risk events.
    
    This is the coordination layer between SDK and risk system.
    All 15 event handlers live here, delegating to specialized modules.
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
        self._extract_symbol_fn: Callable[[str], str] | None = None
        self._get_side_name_fn: Callable[[int], str] | None = None
        self._get_position_type_name_fn: Callable[[int], str] | None = None
        self._is_stop_loss_fn: Callable[[Any], bool] | None = None
        self._is_take_profit_fn: Callable[[Any], bool] | None = None
        self._get_order_placement_display_fn: Callable[[Any], str] | None = None
        self._get_order_type_display_fn: Callable[[Any], str] | None = None
        self._get_order_emoji_fn: Callable[[Any], str] | None = None
        
        # Deduplication cache
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
        get_side_name_fn,
        get_position_type_name_fn,
        is_stop_loss_fn,
        is_take_profit_fn,
        get_order_placement_display_fn,
        get_order_type_display_fn,
        get_order_emoji_fn,
    ):
        """Set helper function references."""
        self._extract_symbol_fn = extract_symbol_fn
        self._get_side_name_fn = get_side_name_fn
        self._get_position_type_name_fn = get_position_type_name_fn
        self._is_stop_loss_fn = is_stop_loss_fn
        self._is_take_profit_fn = is_take_profit_fn
        self._get_order_placement_display_fn = get_order_placement_display_fn
        self._get_order_type_display_fn = get_order_type_display_fn
        self._get_order_emoji_fn = get_order_emoji_fn
    
    def _is_duplicate_event(self, event_type: str, entity_id: str) -> bool:
        """
        Check if this event is a duplicate.
        
        The SDK EventBus emits events from each instrument manager separately,
        so a single order can trigger 3 identical events (one per instrument).
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
