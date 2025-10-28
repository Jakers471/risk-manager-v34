"""
RULE-003: Daily Realized Loss Limit

Purpose: Enforce hard daily realized P&L limit to prevent catastrophic losses.
Category: Hard Lockout (Category 3)
Priority: CRITICAL

Trigger: TRADE_EXECUTED, POSITION_CLOSED, PNL_UPDATED events
Enforcement: Close all positions + Cancel all orders + Hard lockout until reset

Configuration:
    - limit: Max daily loss (negative, e.g., -500.0)
    - reset_time: Daily reset time in HH:MM format (e.g., "17:00" for 5 PM)
    - timezone: Timezone name (e.g., "America/New_York")
    - action: Enforcement action (default: "flatten")

Dependencies:
    - PnL Tracker: Track daily realized P&L
    - Lockout Manager: Set/clear hard lockouts
    - Reset Scheduler: Daily reset at configured time
"""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine
    from risk_manager.state.lockout_manager import LockoutManager
    from risk_manager.state.pnl_tracker import PnLTracker


class DailyRealizedLossRule(RiskRule):
    """
    Enforce maximum daily realized loss limit.

    This rule tracks cumulative realized P&L from closed trades throughout
    the trading day. When the daily loss exceeds the configured limit, the
    rule triggers a hard lockout that:

    1. Closes all open positions immediately
    2. Cancels all pending orders
    3. Locks the account until the daily reset time
    4. Prevents any new trades until unlock

    Features:
    - Tracks only realized P&L (closed trades)
    - Ignores half-turn trades (profitAndLoss=None)
    - Multi-symbol support (tracks account-wide P&L)
    - Hard lockout until configured reset time
    - Auto-unlock via daily reset
    - Crash recovery via database persistence

    Example:
        rule = DailyRealizedLossRule(
            limit=-500.0,
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_manager,
            reset_time="17:00",
            timezone_name="America/New_York"
        )
    """

    def __init__(
        self,
        limit: float,
        pnl_tracker: "PnLTracker",
        lockout_manager: "LockoutManager",
        action: str = "flatten",
        reset_time: str = "17:00",
        timezone_name: str = "America/New_York",
    ):
        """
        Initialize daily realized loss rule.

        Args:
            limit: Maximum allowed daily loss (negative, e.g., -500.0 = -$500)
            pnl_tracker: PnL tracker instance for P&L calculations
            lockout_manager: Lockout manager instance for lockout management
            action: Action to take on violation (default: "flatten")
            reset_time: Daily reset time in HH:MM format (default: "17:00")
            timezone_name: Timezone name (default: "America/New_York")

        Raises:
            ValueError: If limit is not negative
        """
        super().__init__(action=action)

        if limit >= 0:
            raise ValueError("Daily loss limit must be negative")

        self.limit = limit
        self.pnl_tracker = pnl_tracker
        self.lockout_manager = lockout_manager
        self.reset_time = reset_time
        self.timezone_name = timezone_name

        logger.info(
            f"DailyRealizedLossRule initialized: limit=${limit:.2f}, "
            f"reset={reset_time} {timezone_name}"
        )

    async def evaluate(
        self, event: RiskEvent, engine: "RiskEngine"
    ) -> dict[str, Any] | None:
        """
        Evaluate if daily realized loss limit is violated.

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with violation details if rule is violated, None otherwise

        Evaluation Logic:
        1. Check if rule is enabled
        2. Check if event type is relevant (POSITION_CLOSED, PNL_UPDATED)
        3. Extract account_id from event
        4. Check if account is already locked (skip if locked)
        5. Get current daily realized P&L from PnL tracker
        6. Compare P&L to limit
        7. Return violation if P&L <= limit
        """
        if not self.enabled:
            return None

        # Only evaluate on P&L-related events
        if event.event_type not in [
            EventType.POSITION_CLOSED,
            EventType.PNL_UPDATED,
            EventType.TRADE_EXECUTED,
        ]:
            return None

        # Extract account ID
        account_id = event.data.get("account_id")
        if not account_id:
            logger.debug(f"Event missing account_id: {event.data}")
            return None

        # Skip if account is already locked out
        if self.lockout_manager.is_locked_out(account_id):
            logger.debug(f"Account {account_id} already locked, skipping evaluation")
            return None

        # Ignore half-turn trades (opening positions with no realized P&L)
        profit_and_loss = event.data.get("profitAndLoss")
        if profit_and_loss is None:
            logger.debug("Ignoring half-turn trade (no realized P&L)")
            return None

        # Update P&L tracker with this trade
        try:
            daily_pnl = self.pnl_tracker.add_trade_pnl(str(account_id), profit_and_loss)
        except Exception as e:
            logger.error(f"Error updating daily P&L: {e}", exc_info=True)
            return None

        # Check if daily loss exceeds limit
        # Note: Both limit and daily_pnl are negative, so we use <= not >
        # Example: -600 <= -500 (loss exceeds limit), -500 <= -500 (at limit)
        if daily_pnl <= self.limit:
            logger.warning(
                f"Daily loss limit breached for account {account_id}: "
                f"P&L=${daily_pnl:.2f}, Limit=${self.limit:.2f}"
            )

            return {
                "rule": "DailyRealizedLossRule",
                "message": (
                    f"Daily loss limit exceeded: ${daily_pnl:.2f} "
                    f"(limit: ${self.limit:.2f})"
                ),
                "account_id": account_id,
                "daily_loss": daily_pnl,  # Use consistent key name
                "current_loss": daily_pnl,
                "limit": self.limit,
                "action": self.action,
                "lockout_required": True,
                "reset_time": self.reset_time,
                "timezone": self.timezone_name,
            }

        return None

    async def enforce(
        self, account_id: str, violation: dict[str, Any], engine: "RiskEngine"
    ) -> None:
        """
        Execute enforcement action for daily loss limit breach.

        Enforcement Steps:
        1. Close all positions (via engine)
        2. Cancel all orders (via engine)
        3. Calculate next reset time
        4. Set hard lockout until reset time
        5. Log enforcement action

        Args:
            account_id: Account identifier
            violation: Violation details from evaluate()
            engine: Risk engine instance

        Note:
            This method would be called by the RiskEngine when a violation
            is detected. The actual enforcement (closing positions, etc.)
            is delegated to the engine's enforcement module.
        """
        daily_pnl = violation["current_loss"]
        limit = violation["limit"]

        logger.critical(
            f"ENFORCING RULE-003: Account {account_id} "
            f"Daily P&L: ${daily_pnl:.2f}, Limit: ${self.limit:.2f}"
        )

        # Calculate next reset time
        next_reset = self._calculate_next_reset_time()

        # Set hard lockout until reset time
        self.lockout_manager.set_lockout(
            account_id=int(account_id) if isinstance(account_id, str) else account_id,
            reason=violation["message"],
            until=next_reset,
        )

        logger.warning(
            f"Account {account_id} locked until {next_reset.isoformat()}: "
            f"{violation['message']}"
        )

    def _calculate_next_reset_time(self) -> datetime:
        """
        Calculate next daily reset time based on configured reset_time.

        Returns:
            Next reset datetime (timezone-aware UTC)

        Logic:
        - Parse reset_time (e.g., "17:00")
        - Get current time in configured timezone
        - If current time < reset time today → reset today
        - If current time >= reset time today → reset tomorrow
        - Convert to UTC for storage

        Example:
            reset_time = "17:00"
            timezone = "America/New_York"

            Current: 2:00 PM ET → Next reset: 5:00 PM ET today
            Current: 6:00 PM ET → Next reset: 5:00 PM ET tomorrow
        """
        try:
            import pytz

            # Parse reset time (HH:MM)
            reset_hour, reset_minute = map(int, self.reset_time.split(":"))

            # Get current time in configured timezone
            tz = pytz.timezone(self.timezone_name)
            now = datetime.now(tz)

            # Calculate next reset time
            next_reset = now.replace(
                hour=reset_hour, minute=reset_minute, second=0, microsecond=0
            )

            # If we're past reset time today, schedule for tomorrow
            if now >= next_reset:
                next_reset += timedelta(days=1)

            # Convert to UTC for consistency
            next_reset_utc = next_reset.astimezone(pytz.utc)

            logger.debug(
                f"Next reset time: {next_reset.isoformat()} "
                f"({self.timezone_name}) = {next_reset_utc.isoformat()} (UTC)"
            )

            return next_reset_utc

        except Exception as e:
            logger.error(f"Error calculating reset time: {e}", exc_info=True)
            # Fallback: 24 hours from now
            return datetime.now(timezone.utc) + timedelta(days=1)
