"""
RULE-004: Daily Unrealized Loss (Account-Wide Floating Loss Limit)

Purpose: Monitor total unrealized loss across ALL open positions
Category: Trade-by-Trade (Category 1)
Trigger: UNREALIZED_PNL_UPDATE events (when P&L changes $10+)
Enforcement: Flatten all positions when total unrealized loss exceeds limit (no lockout)

This rule monitors the combined floating loss across all open positions
and triggers when the total unrealized loss hits the limit. Uses the
UnrealizedPnLCalculator infrastructure for real-time P&L tracking.

Example:
    - Limit: -$750
    - Position 1: MNQ Long, unrealized P&L: -$400
    - Position 2: ES Long, unrealized P&L: -$350
    - Total unrealized P&L: -$750 → TRIGGER (flatten all)
    - Trader can continue trading after positions closed (no lockout)

Configuration:
    - loss_limit: Maximum total unrealized loss (negative, e.g., -750.0 for -$750)
    - tick_values: Dollar value per tick for each symbol (used by calculator)
    - tick_sizes: Minimum price increment for each symbol (used by calculator)
    - action: "close_position" or "flatten" (close all positions)
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
        Evaluate if total unrealized loss limit is exceeded across all positions.

        This rule monitors the total floating loss across ALL open positions
        and triggers when the combined unrealized loss hits the limit. Uses
        the UnrealizedPnLCalculator infrastructure from Priority 1.

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with violation details if total loss limit hit, None otherwise
        """
        if not self.enabled:
            return None

        # Only evaluate on relevant events
        if event.event_type not in [
            EventType.UNREALIZED_PNL_UPDATE,
            EventType.POSITION_OPENED,
            EventType.POSITION_CLOSED,
        ]:
            return None

        # Get total unrealized P&L across all positions from TradingIntegration
        # This uses the UnrealizedPnLCalculator that tracks real-time quotes
        if not hasattr(engine, 'trading_integration') or not engine.trading_integration:
            return None

        total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

        if total_unrealized_pnl is None:
            return None

        # Check if loss exceeds limit (limit is negative, e.g., -750.0)
        if total_unrealized_pnl <= self.loss_limit:
            return {
                "rule": "DailyUnrealizedLossRule",
                "message": (
                    f"Daily unrealized loss limit exceeded: "
                    f"${total_unrealized_pnl:.2f} ≤ ${self.loss_limit:.2f}"
                ),
                "severity": "CRITICAL",
                "current_pnl": total_unrealized_pnl,
                "limit": self.loss_limit,
                "action": self.action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        return None
