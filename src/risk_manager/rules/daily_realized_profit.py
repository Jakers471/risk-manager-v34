"""
RULE-013: Daily Realized Profit Target

Purpose: Enforce hard daily realized profit target to prevent giving back profits.
Category: Hard Lockout (Category 3)
Priority: Medium

Trigger: TRADE_EXECUTED, POSITION_CLOSED, PNL_UPDATED events
Enforcement: Close all positions + Cancel all orders + Hard lockout until reset

Configuration:
    - target: Daily profit target (positive, e.g., 1000.0)
    - reset_time: Daily reset time in HH:MM format (e.g., "17:00" for 5 PM)
    - timezone: Timezone name (e.g., "America/New_York")
    - action: Enforcement action (default: "flatten")

Dependencies:
    - PnL Tracker: Track daily realized P&L (SHARED WITH RULE-003)
    - Lockout Manager: Set/clear hard lockouts
    - Reset Scheduler: Daily reset at configured time

Philosophy: Profit protection + discipline - prevents psychological overtrading
after hitting daily goal. "Take the win and walk away."
"""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional
from zoneinfo import ZoneInfo

from loguru import logger

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine
    from risk_manager.state.lockout_manager import LockoutManager
    from risk_manager.state.pnl_tracker import PnLTracker


class DailyRealizedProfitRule(RiskRule):
    """
    Enforce maximum daily realized profit target.

    This rule tracks cumulative realized P&L from closed trades throughout
    the trading day. When the daily profit reaches or exceeds the configured
    target, the rule triggers a hard lockout that:

    1. Closes all open positions immediately (lock in profits)
    2. Cancels all pending orders
    3. Locks the account until the daily reset time
    4. Prevents any new trades until unlock

    This is the OPPOSITE of RULE-003 (DailyRealizedLoss):
    - RULE-003: Triggers when P&L <= -loss_limit (loss protection)
    - RULE-013: Triggers when P&L >= +profit_target (profit protection)

    Features:
    - Tracks only realized P&L (closed trades)
    - Ignores half-turn trades (profitAndLoss=None)
    - Multi-symbol support (tracks account-wide P&L)
    - Hard lockout until configured reset time
    - Auto-unlock via daily reset
    - Crash recovery via database persistence
    - Positive reinforcement messaging ("Good job!")

    Example:
        rule = DailyRealizedProfitRule(
            target=1000.0,
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_manager,
            reset_time="17:00",
            timezone_name="America/New_York"
        )
    """

    def __init__(
        self,
        target: float,
        pnl_tracker: "PnLTracker",
        lockout_manager: "LockoutManager",
        action: str = "flatten",
        reset_time: str = "17:00",
        timezone_name: str = "America/New_York",
    ):
        """
        Initialize daily realized profit rule.

        Args:
            target: Daily profit target (positive, e.g., 1000.0 = $1000)
            pnl_tracker: PnL tracker instance for P&L calculations
            lockout_manager: Lockout manager instance for lockout management
            action: Action to take on violation (default: "flatten")
            reset_time: Daily reset time in HH:MM format (default: "17:00")
            timezone_name: Timezone name (default: "America/New_York")

        Raises:
            ValueError: If target is not positive
        """
        super().__init__(action=action)

        if target <= 0:
            raise ValueError("Daily profit target must be positive")

        self.target = target
        self.pnl_tracker = pnl_tracker
        self.lockout_manager = lockout_manager
        self.reset_time = reset_time
        self.timezone_name = timezone_name

        logger.info(
            f"DailyRealizedProfitRule initialized: target=${target:.2f}, "
            f"reset={reset_time} {timezone_name}"
        )

    async def evaluate(
        self, event: RiskEvent, engine: "RiskEngine"
    ) -> dict[str, Any] | None:
        """
        Evaluate if daily realized profit target is reached.

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
        6. Compare P&L to target
        7. Return violation if P&L >= target
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
        if event.event_type == EventType.POSITION_OPENED and profit_and_loss is None:
            logger.debug("Ignoring half-turn trade (no realized P&L)")
            return None

        # Get current daily realized P&L
        try:
            daily_pnl = self.pnl_tracker.get_daily_pnl(account_id)
        except Exception as e:
            logger.error(f"Error getting daily P&L: {e}", exc_info=True)
            return None

        # Check if daily profit reaches or exceeds target
        # Note: Both target and daily_pnl are positive, so we use >= comparison
        # Example: 1100 >= 1000 (profit target reached!)
        if daily_pnl >= self.target:
            logger.warning(
                f"Daily profit target reached for account {account_id}: "
                f"P&L=${daily_pnl:.2f}, Target=${self.target:.2f} - Good job!"
            )

            return {
                "rule": "DailyRealizedProfitRule",
                "message": (
                    f"Daily profit target reached: ${daily_pnl:.2f} "
                    f"(target: ${self.target:.2f}) - Good job!"
                ),
                "account_id": account_id,
                "current_profit": daily_pnl,
                "target": self.target,
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
        Execute enforcement action for daily profit target reached.

        Enforcement Steps:
        1. Close all positions (lock in all profits!)
        2. Cancel all orders (stop further trading)
        3. Calculate next reset time
        4. Set hard lockout until reset time
        5. Log enforcement action with positive tone

        Args:
            account_id: Account identifier
            violation: Violation details from evaluate()
            engine: Risk engine instance

        Note:
            This method would be called by the RiskEngine when a violation
            is detected. The actual enforcement (closing positions, etc.)
            is delegated to the engine's enforcement module.
        """
        daily_pnl = violation["current_profit"]
        target = violation["target"]

        logger.info(
            f"ENFORCING RULE-013: Account {account_id} "
            f"Daily P&L: ${daily_pnl:.2f}, Target: ${self.target:.2f} - Great trading!"
        )

        # Calculate next reset time
        next_reset = self._calculate_next_reset_time()

        # Set hard lockout until reset time
        # Handle account_id conversion (skip if not numeric)
        try:
            numeric_account_id = int(account_id) if isinstance(account_id, str) and account_id.isdigit() else account_id
        except (ValueError, AttributeError):
            numeric_account_id = account_id

        self.lockout_manager.set_lockout(
            account_id=numeric_account_id,
            reason=violation["message"],
            until=next_reset,
        )

        logger.info(
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
            # Parse reset time (HH:MM)
            reset_hour, reset_minute = map(int, self.reset_time.split(":"))

            # Get current time in configured timezone using ZoneInfo
            tz = ZoneInfo(self.timezone_name)
            now = datetime.now(tz)

            # Calculate next reset time
            next_reset = now.replace(
                hour=reset_hour, minute=reset_minute, second=0, microsecond=0
            )

            # If we're past reset time today, schedule for tomorrow
            if now >= next_reset:
                next_reset += timedelta(days=1)

            # Convert to UTC for consistency
            next_reset_utc = next_reset.astimezone(timezone.utc)

            logger.debug(
                f"Next reset time: {next_reset.isoformat()} "
                f"({self.timezone_name}) = {next_reset_utc.isoformat()} (UTC)"
            )

            return next_reset_utc

        except Exception as e:
            logger.error(f"Error calculating reset time: {e}", exc_info=True)
            # Fallback: 24 hours from now
            return datetime.now(timezone.utc) + timedelta(days=1)
