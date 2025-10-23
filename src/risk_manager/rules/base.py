"""Base class for risk rules."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from risk_manager.core.events import RiskEvent

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine


class RiskRule(ABC):
    """Base class for all risk rules."""

    def __init__(self, action: str = "alert"):
        """
        Initialize risk rule.

        Args:
            action: Action to take on violation ("alert", "pause", "flatten")
        """
        self.action = action
        self.enabled = True

    @abstractmethod
    async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict[str, Any] | None:
        """
        Evaluate the rule against an event.

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with violation details if rule is violated, None otherwise
        """
        pass

    def enable(self) -> None:
        """Enable this rule."""
        self.enabled = True

    def disable(self) -> None:
        """Disable this rule."""
        self.enabled = False
