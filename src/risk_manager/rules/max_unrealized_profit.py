"""
RULE-005: Max Unrealized Profit (Per-Position Take Profit)

Purpose: Close individual positions when unrealized profit hits target
Category: Trade-by-Trade (Category 1)
Trigger: UNREALIZED_PNL_UPDATE events (when P&L changes $10+)
Enforcement: Close ONLY the winning position(s) that hit target (no lockout)

This rule monitors each open position individually for profit targets.
When any position's unrealized profit reaches the target, it closes that
specific position to lock in gains. Uses the UnrealizedPnLCalculator
infrastructure for real-time per-position P&L tracking.

Example:
    - Target: $500
    - Position 1: MNQ Long, unrealized P&L: $450 (no action)
    - Position 2: ES Long, unrealized P&L: $550 → TRIGGER (close ES only)
    - Trader can continue trading after position closed (no lockout)

Configuration:
    - target: Profit target per position (positive, e.g., 500.0 for $500)
    - tick_values: Dollar value per tick for each symbol (used by calculator)
    - tick_sizes: Minimum price increment for each symbol (used by calculator)
    - action: "close_position" (close winning positions individually)
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
        Evaluate if any position's unrealized profit exceeds target.

        This rule monitors individual positions for profit targets. When a
        position's unrealized profit hits the target, it triggers to close
        that specific position and lock in gains. Uses the UnrealizedPnLCalculator
        infrastructure from Priority 1.

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with violation details if any position hits profit target, None otherwise
        """
        if not self.enabled:
            return None

        # Only evaluate on relevant events
        if event.event_type not in [
            EventType.UNREALIZED_PNL_UPDATE,
            EventType.POSITION_OPENED,
        ]:
            return None

        # Get trading integration for accessing position P&L
        if not hasattr(engine, 'trading_integration') or not engine.trading_integration:
            return None

        # Check each open position's unrealized P&L
        positions_at_target = []

        open_positions = engine.trading_integration.get_open_positions()
        for contract_id, position_data in open_positions.items():
            unrealized_pnl = engine.trading_integration.get_position_unrealized_pnl(contract_id)

            if unrealized_pnl is None:
                continue

            # Check if profit exceeds target (target is positive, e.g., 500.0)
            if unrealized_pnl >= self.target:
                positions_at_target.append({
                    'contract_id': contract_id,
                    'symbol': position_data['symbol'],
                    'unrealized_pnl': unrealized_pnl,
                    'target': self.target
                })

        if positions_at_target:
            return {
                'rule': 'MaxUnrealizedProfitRule',
                'severity': 'MEDIUM',
                'message': f'{len(positions_at_target)} position(s) hit profit target: ${self.target:.2f}',
                'action': self.action,  # 'close_position', 'reduce_to_limit', or 'alert'
                'positions': positions_at_target,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }

        return None
