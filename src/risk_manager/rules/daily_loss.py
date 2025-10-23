"""Daily loss limit rule."""

from typing import TYPE_CHECKING, Any

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine


class DailyLossRule(RiskRule):
    """Enforce maximum daily loss limit."""

    def __init__(self, limit: float, action: str = "flatten"):
        """
        Initialize daily loss rule.

        Args:
            limit: Maximum allowed daily loss (negative number, e.g., -1000.0)
            action: Action to take on violation ("alert", "pause", "flatten")
        """
        super().__init__(action=action)
        self.limit = limit

        if limit >= 0:
            raise ValueError("Daily loss limit must be negative")

    async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict[str, Any] | None:
        """Evaluate if daily loss limit is violated."""
        if not self.enabled:
            return None

        # Only evaluate on P&L update events
        if event.event_type not in [EventType.PNL_UPDATED, EventType.POSITION_CLOSED]:
            return None

        # Check if daily P&L exceeds limit
        if engine.daily_pnl <= self.limit:
            return {
                "rule": "DailyLossRule",
                "message": f"Daily loss limit exceeded: ${engine.daily_pnl:.2f} (limit: ${self.limit:.2f})",
                "current_loss": engine.daily_pnl,
                "limit": self.limit,
                "action": self.action,
            }

        return None
