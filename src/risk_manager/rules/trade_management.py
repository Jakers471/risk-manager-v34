"""
RULE-012: Trade Management (Automation)

Purpose: Automated trade management - auto stop-loss, take-profit, trailing stops
Category: Automation (Category 4) - NOT enforcement
Trigger: POSITION_OPENED, POSITION_UPDATED + market data
Action: Place/modify orders (NO violations, NO lockouts)

This rule implements automated trade management:
- Automatically attach stop-loss orders when positions open
- Automatically attach take-profit orders when positions open
- Automatically adjust trailing stops as price moves favorably
- This is AUTOMATION, not enforcement (no violations, no lockouts)

Configuration:
    - auto_stop_loss.enabled: Enable automatic stop-loss placement
    - auto_stop_loss.distance: Stop-loss distance in ticks
    - auto_take_profit.enabled: Enable automatic take-profit placement
    - auto_take_profit.distance: Take-profit distance in ticks
    - trailing_stop.enabled: Enable trailing stop adjustment
    - trailing_stop.distance: Trailing stop distance in ticks
"""

from typing import TYPE_CHECKING, Any, Dict, Optional
from datetime import datetime, timezone

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine


class TradeManagementRule(RiskRule):
    """
    Automated trade management rule.

    Automatically places and manages stop-loss and take-profit orders
    for open positions. This is NOT an enforcement rule - it's an
    automation helper that provides protection and profit-taking.

    Features:
        - Auto stop-loss placement on position open
        - Auto take-profit placement on position open
        - Trailing stop adjustment as price moves favorably
        - Independent management per symbol
        - Configurable distances in ticks

    Example:
        - ES Long 1 @ 6000.00
        - Auto stop-loss: 6000 - (10 ticks * 0.25) = 5997.50
        - Auto take-profit: 6000 + (20 ticks * 0.25) = 6005.00
        - As price rises to 6010, trailing stop moves to 6008
    """

    def __init__(
        self,
        config: Dict[str, Any],
        tick_values: Dict[str, float],
        tick_sizes: Dict[str, float],
    ):
        """
        Initialize trade management rule.

        Args:
            config: Rule configuration dictionary
                - enabled: Enable/disable rule
                - auto_stop_loss: {enabled, distance}
                - auto_take_profit: {enabled, distance}
                - trailing_stop: {enabled, distance}
            tick_values: Dollar value per tick for each symbol
            tick_sizes: Minimum price increment for each symbol
        """
        # Note: action="automate" to indicate this is automation, not enforcement
        super().__init__(action="automate")

        # Parse main config
        self.enabled = config.get("enabled", True)

        # Parse auto stop-loss config
        auto_sl_config = config.get("auto_stop_loss", {})
        self.auto_stop_loss_enabled = auto_sl_config.get("enabled", True)
        self.stop_loss_distance = auto_sl_config.get("distance", 10)

        # Parse auto take-profit config
        auto_tp_config = config.get("auto_take_profit", {})
        self.auto_take_profit_enabled = auto_tp_config.get("enabled", True)
        self.take_profit_distance = auto_tp_config.get("distance", 20)

        # Parse trailing stop config
        trailing_config = config.get("trailing_stop", {})
        self.trailing_stop_enabled = trailing_config.get("enabled", True)
        self.trailing_stop_distance = trailing_config.get("distance", 8)

        # Store tick info
        self.tick_values = tick_values
        self.tick_sizes = tick_sizes

        # Track highest/lowest prices for trailing stops
        self._position_extremes: Dict[str, float] = {}

    async def evaluate(
        self, event: RiskEvent, engine: "RiskEngine"
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate if trade management actions are needed.

        This is called on position events. It checks if:
        1. New position needs stop-loss/take-profit orders
        2. Existing position needs trailing stop adjustment

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with automation action details, None if no action needed
        """
        if not self.enabled:
            return None

        # Only evaluate position events
        if event.event_type not in [
            EventType.POSITION_OPENED,
            EventType.POSITION_UPDATED,
        ]:
            return None

        # Get symbol from event
        symbol = event.data.get("symbol")
        if not symbol:
            return None

        # Get position data
        position = engine.current_positions.get(symbol)
        if not position:
            return None

        # Handle position opened - place initial orders
        if event.event_type == EventType.POSITION_OPENED:
            return await self._handle_position_opened(symbol, position, engine)

        # Handle position updated - adjust trailing stop
        elif event.event_type == EventType.POSITION_UPDATED:
            return await self._handle_position_updated(symbol, position, engine)

        return None

    async def _handle_position_opened(
        self, symbol: str, position: Dict[str, Any], engine: "RiskEngine"
    ) -> Optional[Dict[str, Any]]:
        """
        Handle new position - place stop-loss and take-profit orders.

        Args:
            symbol: Symbol identifier
            position: Position data
            engine: Risk engine

        Returns:
            Action dictionary with order placement details
        """
        entry_price = position.get("avgPrice")
        size = position.get("size", 0)
        side = "long" if size > 0 else "short"
        contract_id = position.get("contractId")

        if not entry_price or size == 0:
            return None

        # Get tick size for this symbol
        tick_size = self.tick_sizes.get(symbol, 0.25)

        # Initialize price extremes for trailing stop
        self._position_extremes[symbol] = entry_price

        # Calculate stop-loss price
        stop_price = None
        if self.auto_stop_loss_enabled:
            stop_price = self._calculate_stop_price(
                entry_price, self.stop_loss_distance, tick_size, side
            )

        # Calculate take-profit price
        target_price = None
        if self.auto_take_profit_enabled:
            target_price = self._calculate_target_price(
                entry_price, self.take_profit_distance, tick_size, side
            )

        # If both enabled, return bracket order
        if stop_price is not None and target_price is not None:
            return {
                "rule": "TradeManagementRule",
                "action": "place_bracket_order",
                "message": (
                    f"Placing bracket order for {symbol}: "
                    f"Stop=${stop_price:.2f}, Target=${target_price:.2f}"
                ),
                "symbol": symbol,
                "contractId": contract_id,
                "side": side,
                "size": abs(size),
                "entry_price": entry_price,
                "stop_price": stop_price,
                "take_profit_price": target_price,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # If only stop-loss enabled
        elif stop_price is not None:
            return {
                "rule": "TradeManagementRule",
                "action": "place_stop_loss",
                "message": f"Placing stop-loss for {symbol} at ${stop_price:.2f}",
                "symbol": symbol,
                "contractId": contract_id,
                "side": side,
                "size": abs(size),
                "entry_price": entry_price,
                "stop_price": stop_price,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # If only take-profit enabled
        elif target_price is not None:
            return {
                "rule": "TradeManagementRule",
                "action": "place_take_profit",
                "message": f"Placing take-profit for {symbol} at ${target_price:.2f}",
                "symbol": symbol,
                "contractId": contract_id,
                "side": side,
                "size": abs(size),
                "entry_price": entry_price,
                "take_profit_price": target_price,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        return None

    async def _handle_position_updated(
        self, symbol: str, position: Dict[str, Any], engine: "RiskEngine"
    ) -> Optional[Dict[str, Any]]:
        """
        Handle position update - adjust trailing stop if enabled.

        Args:
            symbol: Symbol identifier
            position: Position data
            engine: Risk engine

        Returns:
            Action dictionary with trailing stop adjustment details
        """
        if not self.trailing_stop_enabled:
            return None

        # Get current market price
        current_price = engine.market_prices.get(symbol)
        if current_price is None:
            return None

        # Get position details
        size = position.get("size", 0)
        if size == 0:
            return None

        side = "long" if size > 0 else "short"
        entry_price = position.get("avgPrice")
        old_stop_price = position.get("stop_price")

        if not entry_price:
            return None

        # Get or initialize extreme price
        if symbol not in self._position_extremes:
            self._position_extremes[symbol] = entry_price

        # Track highest price for long, lowest price for short
        extreme_price = self._position_extremes[symbol]

        if side == "long":
            # For long positions, track highest price
            if current_price > extreme_price:
                self._position_extremes[symbol] = current_price
                extreme_price = current_price
            else:
                # Price hasn't moved higher, don't adjust stop
                return None
        else:
            # For short positions, track lowest price
            if current_price < extreme_price:
                self._position_extremes[symbol] = current_price
                extreme_price = current_price
            else:
                # Price hasn't moved lower, don't adjust stop
                return None

        # Calculate new trailing stop price
        tick_size = self.tick_sizes.get(symbol, 0.25)
        new_stop_price = self._calculate_trailing_stop_price(
            extreme_price, self.trailing_stop_distance, tick_size, side
        )

        # Only adjust if new stop is better than old stop (or no old stop)
        if old_stop_price is not None:
            if side == "long":
                # For long, new stop should be higher than old
                if new_stop_price <= old_stop_price:
                    return None
            else:
                # For short, new stop should be lower than old
                if new_stop_price >= old_stop_price:
                    return None

        return {
            "rule": "TradeManagementRule",
            "action": "adjust_trailing_stop",
            "message": (
                f"Adjusting trailing stop for {symbol}: "
                f"${old_stop_price or 0:.2f} -> ${new_stop_price:.2f}"
            ),
            "symbol": symbol,
            "contractId": position.get("contractId"),
            "side": side,
            "current_price": current_price,
            "extreme_price": extreme_price,
            "old_stop_price": old_stop_price,
            "new_stop_price": new_stop_price,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_stop_price(
        self, entry_price: float, distance_ticks: int, tick_size: float, side: str
    ) -> float:
        """
        Calculate stop-loss price.

        For long positions: entry - (distance * tick_size)
        For short positions: entry + (distance * tick_size)

        Args:
            entry_price: Entry price
            distance_ticks: Distance in ticks
            tick_size: Tick size
            side: "long" or "short"

        Returns:
            Stop-loss price
        """
        distance = distance_ticks * tick_size

        if side == "long":
            return entry_price - distance
        else:
            return entry_price + distance

    def _calculate_target_price(
        self, entry_price: float, distance_ticks: int, tick_size: float, side: str
    ) -> float:
        """
        Calculate take-profit price.

        For long positions: entry + (distance * tick_size)
        For short positions: entry - (distance * tick_size)

        Args:
            entry_price: Entry price
            distance_ticks: Distance in ticks
            tick_size: Tick size
            side: "long" or "short"

        Returns:
            Take-profit price
        """
        distance = distance_ticks * tick_size

        if side == "long":
            return entry_price + distance
        else:
            return entry_price - distance

    def _calculate_trailing_stop_price(
        self, extreme_price: float, distance_ticks: int, tick_size: float, side: str
    ) -> float:
        """
        Calculate trailing stop price based on extreme price.

        For long positions: extreme - (distance * tick_size)
        For short positions: extreme + (distance * tick_size)

        Args:
            extreme_price: Highest price for long, lowest for short
            distance_ticks: Distance in ticks
            tick_size: Tick size
            side: "long" or "short"

        Returns:
            Trailing stop price
        """
        distance = distance_ticks * tick_size

        if side == "long":
            return extreme_price - distance
        else:
            return extreme_price + distance
