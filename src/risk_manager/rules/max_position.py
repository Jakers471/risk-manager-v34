"""Maximum position size rule."""

from typing import TYPE_CHECKING, Any

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine


class MaxPositionRule(RiskRule):
    """Enforce maximum position size limit."""

    def __init__(self, max_contracts: int, action: str = "reject", per_instrument: bool = True):
        """
        Initialize max position rule.

        Args:
            max_contracts: Maximum number of contracts allowed
            action: Action to take on violation ("alert", "reject")
            per_instrument: Apply limit per instrument vs. total across all
        """
        super().__init__(action=action)
        self.max_contracts = max_contracts
        self.per_instrument = per_instrument

        if max_contracts <= 0:
            raise ValueError("Max contracts must be positive")

    async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict[str, Any] | None:
        """Evaluate if position size limit is violated."""
        if not self.enabled:
            return None

        # Only evaluate on position events
        if event.event_type not in [
            EventType.POSITION_OPENED,
            EventType.POSITION_UPDATED,
            EventType.ORDER_FILLED,
        ]:
            return None

        # Calculate total position size
        if self.per_instrument:
            # Check each instrument separately
            for instrument, position in engine.current_positions.items():
                size = abs(position.get("size", 0))
                if size > self.max_contracts:
                    return {
                        "rule": "MaxPositionRule",
                        "message": f"Position size exceeded for {instrument}: {size} (max: {self.max_contracts})",
                        "instrument": instrument,
                        "current_size": size,
                        "max_contracts": self.max_contracts,
                        "action": self.action,
                    }
        else:
            # Check total across all instruments
            total_size = sum(
                abs(pos.get("size", 0)) for pos in engine.current_positions.values()
            )
            if total_size > self.max_contracts:
                return {
                    "rule": "MaxPositionRule",
                    "message": f"Total position size exceeded: {total_size} (max: {self.max_contracts})",
                    "total_size": total_size,
                    "max_contracts": self.max_contracts,
                    "action": self.action,
                }

        return None
