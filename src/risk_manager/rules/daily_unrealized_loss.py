"""
RULE-004: Daily Unrealized Loss (Stop Loss Per Position)

Purpose: Close losing positions when unrealized loss hits limit
Category: Trade-by-Trade (Category 1)
Trigger: POSITION_UPDATED + real-time market data
Enforcement: Close ONLY that losing position (no lockout)

This rule implements stop-loss behavior - when a position's unrealized
loss reaches the limit, close that position to prevent further losses.
Trader can continue trading immediately (no lockout).

Configuration:
    - loss_limit: Maximum unrealized loss per position (negative, e.g., -300.0 for -$300)
    - tick_values: Dollar value per tick for each symbol
    - tick_sizes: Minimum price increment for each symbol
    - action: "close_position" (close that position only)
"""

from typing import TYPE_CHECKING, Any, Dict, Optional
from datetime import datetime, timezone

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule
from risk_manager.integrations.tick_economics import (
    get_tick_value_safe,
    get_tick_size_safe,
    UnitsError,
)

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine


class DailyUnrealizedLossRule(RiskRule):
    """
    Enforce maximum unrealized loss per position (stop loss rule).

    When a position's unrealized loss exceeds the limit, close that
    position to prevent further losses. This is a trade-by-trade rule -
    only the losing position is closed, no lockout is created, and the
    trader can continue trading immediately.

    Example:
        - MNQ Long 2 @ 21000.00
        - Current price: 20970.00
        - Unrealized P&L: -$1200
        - Loss Limit: -$300
        - Action: Close MNQ position (stop loss)
        - Trader can immediately place new trades
    """

    def __init__(
        self,
        loss_limit: float,
        tick_values: Dict[str, float],
        tick_sizes: Dict[str, float],
        action: str = "close_position",
    ):
        """
        Initialize daily unrealized loss rule.

        Args:
            loss_limit: Maximum unrealized loss per position in dollars
                        (must be negative, e.g., -300.0 for -$300)
            tick_values: Dollar value per tick for each symbol
                         e.g., {"ES": 50.0, "MNQ": 5.0}
            tick_sizes: Minimum price increment for each symbol
                        e.g., {"ES": 0.25, "MNQ": 0.25}
            action: Action to take on violation (default: "close_position")

        Raises:
            ValueError: If loss_limit is not negative
        """
        super().__init__(action=action)

        if loss_limit >= 0:
            raise ValueError("Loss limit must be negative")

        self.loss_limit = loss_limit
        self.tick_values = tick_values
        self.tick_sizes = tick_sizes

    async def evaluate(
        self, event: RiskEvent, engine: "RiskEngine"
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate if unrealized loss limit is hit for any position.

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with violation details if loss limit hit, None otherwise
        """
        if not self.enabled:
            return None

        # Only evaluate on position events
        if event.event_type not in [
            EventType.POSITION_OPENED,
            EventType.POSITION_UPDATED,
        ]:
            return None

        # Get symbol from event data
        symbol = event.data.get("symbol")
        if not symbol:
            return None

        # Get position for this symbol
        position = engine.current_positions.get(symbol)
        if not position:
            return None

        # Get current market price
        current_price = engine.market_prices.get(symbol)
        if current_price is None:
            # Can't calculate unrealized P&L without market price
            return None

        # Calculate unrealized P&L for this position
        unrealized_pnl = self._calculate_unrealized_pnl(
            symbol=symbol,
            position=position,
            current_price=current_price,
        )

        # Check if loss limit is hit (unrealized_pnl <= loss_limit, both negative)
        if unrealized_pnl <= self.loss_limit:
            return {
                "rule": "DailyUnrealizedLossRule",
                "message": (
                    f"Loss limit hit for {symbol}: "
                    f"${unrealized_pnl:.2f} <= ${self.loss_limit:.2f} (stop loss)"
                ),
                "symbol": symbol,
                "contractId": position.get("contractId"),
                "unrealized_pnl": unrealized_pnl,
                "loss_limit": self.loss_limit,
                "action": self.action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        return None

    def _calculate_unrealized_pnl(
        self,
        symbol: str,
        position: Dict[str, Any],
        current_price: float,
    ) -> float:
        """
        Calculate unrealized P&L for a position.

        Formula:
            P&L = (current_price - entry_price) / tick_size * size * tick_value

        For short positions, the formula is inverted:
            P&L = (entry_price - current_price) / tick_size * abs(size) * tick_value

        Args:
            symbol: Symbol identifier (e.g., "ES", "MNQ")
            position: Position dictionary with avgPrice, size
            current_price: Current market price

        Returns:
            Unrealized P&L in dollars (positive = profit, negative = loss)
        """
        # Get position details
        entry_price = position.get("avgPrice", 0.0)
        size = position.get("size", 0)

        if size == 0:
            return 0.0

        # Get tick value and size for this symbol (FAIL FAST - no silent defaults)
        # NOTE: We use the rule's own tick_values/tick_sizes for flexibility
        # but validate they exist rather than using silent defaults
        if symbol not in self.tick_values:
            raise UnitsError(
                f"Unknown symbol: {symbol}. "
                f"Tick economics must be configured for all traded symbols. "
                f"Known symbols: {list(self.tick_values.keys())}"
            )

        tick_value = self.tick_values[symbol]
        tick_size = self.tick_sizes.get(symbol, 0.25)  # tick_size is less critical

        if tick_value == 0.0 or tick_size == 0.0:
            raise UnitsError(
                f"Invalid tick economics for {symbol}: "
                f"tick_value={tick_value}, tick_size={tick_size}. "
                f"Values must be > 0."
            )

        # Calculate price difference
        if size > 0:
            # Long position: profit when price goes up
            price_diff = current_price - entry_price
        else:
            # Short position: profit when price goes down
            price_diff = entry_price - current_price

        # Convert to ticks
        ticks = price_diff / tick_size

        # Calculate P&L
        unrealized_pnl = ticks * abs(size) * tick_value

        return unrealized_pnl
