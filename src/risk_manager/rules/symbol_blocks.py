"""
RULE-011: Symbol Blocks

Purpose: Blacklist specific symbols - close any position immediately
Trigger: ORDER_PLACED, POSITION_OPENED, POSITION_UPDATED events
Enforcement: Trade-by-Trade (close position, NO lockout)

Configuration:
    - enabled: Enable/disable the rule
    - blocked_symbols: List of symbols to block (supports wildcards)
    - action: Action to take ("close")
"""

import fnmatch
import logging
from typing import TYPE_CHECKING, Any

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine

logger = logging.getLogger(__name__)


class SymbolBlocksRule(RiskRule):
    """
    RULE-011: Symbol Blocks

    Blacklist specific symbols and prevent trading them.
    Supports case-insensitive matching and wildcard patterns.

    Trade-by-Trade enforcement:
    - Reject orders for blocked symbols
    - Close positions in blocked symbols
    - NO lockout (can trade other symbols)
    """

    def __init__(self, blocked_symbols: list[str], action: str = "close"):
        """
        Initialize Symbol Blocks rule.

        Args:
            blocked_symbols: List of symbols to block (e.g., ["BTC", "ETH", "MNQ*"])
            action: Action to take on violation ("close" or "reject")
        """
        super().__init__(action=action)
        self.blocked_symbols = blocked_symbols

        # Normalize blocked symbols to uppercase for case-insensitive comparison
        self._blocked_patterns = [s.upper() for s in blocked_symbols]

        logger.info(f"SymbolBlocksRule initialized with {len(blocked_symbols)} blocked symbols")

    def _is_symbol_blocked(self, symbol: str) -> bool:
        """
        Check if a symbol is blocked.

        Supports:
        - Exact matching (case-insensitive)
        - Wildcard patterns (*, ?)

        Args:
            symbol: Symbol to check

        Returns:
            True if symbol is blocked, False otherwise
        """
        if not symbol:
            return False

        # Normalize to uppercase for case-insensitive matching
        symbol_upper = symbol.upper()

        for pattern in self._blocked_patterns:
            # Use fnmatch for wildcard support (*, ?)
            if fnmatch.fnmatch(symbol_upper, pattern):
                return True

        return False

    async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> dict[str, Any] | None:
        """
        Evaluate if symbol is blocked.

        Args:
            event: Event from TopstepX (order, position, trade)
            engine: Risk engine for accessing state

        Returns:
            Violation dict if symbol is blocked, None otherwise
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        # Only evaluate relevant events (orders and positions)
        if event.event_type not in [
            EventType.ORDER_PLACED,
            EventType.POSITION_OPENED,
            EventType.POSITION_UPDATED,
            EventType.ORDER_FILLED,
        ]:
            return None

        # Extract symbol from event
        symbol = event.data.get("symbol")
        if not symbol:
            # No symbol in event, nothing to check
            return None

        # Check if symbol is blocked
        if self._is_symbol_blocked(symbol):
            return {
                "rule": "SymbolBlocksRule",
                "message": f"Symbol {symbol} is blocked and cannot be traded",
                "symbol": symbol,
                "action": self.action,
            }

        return None
