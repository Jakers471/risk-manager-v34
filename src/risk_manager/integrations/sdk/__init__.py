"""
SDK Integration Modules

This package contains specialized modules for interacting with the Project-X-Py SDK.

The TradingIntegration class (in parent module) acts as a facade that delegates
to these specialized modules internally.

Modules:
    - protective_orders: Stop loss and take profit caching
    - market_data: Quote updates and price polling
    - event_router: SDK event routing to risk system
    - order_polling: Background order discovery
    - connection_manager: SDK lifecycle management
    - pnl_tracker: Position tracking and P&L calculation

Design Pattern: Facade
    The public API (TradingIntegration) remains unchanged.
    Internal implementation is split into focused modules.
    This allows refactoring without breaking existing code.
"""

__all__ = [
    # Will be populated as modules are created
]
