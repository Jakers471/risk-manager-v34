"""
RULE-005: Max Unrealized Profit (Take Profit)

Purpose: Close winning positions when unrealized profit hits target
Category: Trade-by-Trade (Category 1)
Trigger: POSITION_UPDATED + real-time market data
Enforcement: Close ONLY that winning position (no lockout)

This rule implements profit-taking behavior - when a position's unrealized
profit reaches the target, close that position to lock in gains. Trader can
continue trading immediately (no lockout).

Configuration:
    - target: Profit target in dollars (e.g., 1000.0 for $1000)
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


class MaxUnrealizedProfitRule(RiskRule):
    """
    Enforce maximum unrealized profit per position (take profit rule).

    When a position's unrealized profit exceeds the target, close that
    position to lock in gains. This is a trade-by-trade rule - only the
    winning position is closed, no lockout is created, and the trader
    can continue trading immediately.

    Example:
        - ES Long 1 @ 6000.00
        - Current price: 6010.00
        - Unrealized P&L: $2000
        - Target: $1000
        - Action: Close ES position (take profit)
        - Trader can immediately place new trades
    """

    def __init__(
        self,
        target: float,
        tick_values: Dict[str, float],
        tick_sizes: Dict[str, float],
        action: str = "close_position",
    ):
        """
        Initialize max unrealized profit rule.

        Args:
            target: Profit target in dollars (must be positive, e.g., 1000.0)
            tick_values: Dollar value per tick for each symbol
                         e.g., {"ES": 50.0, "MNQ": 5.0}
            tick_sizes: Minimum price increment for each symbol
                        e.g., {"ES": 0.25, "MNQ": 0.25}
            action: Action to take on violation (default: "close_position")

        Raises:
            ValueError: If target is not positive
        """
        super().__init__(action=action)

        if target <= 0:
            raise ValueError("Profit target must be positive")

        self.target = target
        self.tick_values = tick_values
        self.tick_sizes = tick_sizes

    async def evaluate(
        self, event: RiskEvent, engine: "RiskEngine"
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate if unrealized profit target is hit for any position.

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with violation details if profit target hit, None otherwise
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

        # Check if profit target is hit
        if unrealized_pnl >= self.target:
            return {
                "rule": "MaxUnrealizedProfitRule",
                "message": (
                    f"Profit target hit for {symbol}: "
                    f"${unrealized_pnl:.2f} >= ${self.target:.2f} (take profit)"
                ),
                "symbol": symbol,
                "contractId": position.get("contractId"),
                "unrealized_pnl": unrealized_pnl,
                "target": self.target,
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
