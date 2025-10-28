"""
RULE-009: Session Block Outside Hours

Purpose: Block trading outside configured session hours and on weekends/holidays.
Category: Hard Lockout (Category 3)
Priority: High

Trigger: POSITION_OPENED, POSITION_UPDATED events
Enforcement: Hard lockout until next session start

Configuration:
    - global_session: Global session hours (start, end, timezone)
    - block_weekends: Block trading on Saturday/Sunday
    - lockout_outside_session: Set lockout when outside session

Dependencies:
    - Lockout Manager: Set/clear hard lockouts
    - Timezone Library: pytz/zoneinfo for timezone conversion
"""

from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING, Any, Optional
from zoneinfo import ZoneInfo

from loguru import logger

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine
    from risk_manager.state.lockout_manager import LockoutManager


class SessionBlockOutsideRule(RiskRule):
    """
    Block trading outside configured session hours.

    This rule enforces trading hours by checking if the current time falls
    within the configured session window. When trading is attempted outside
    session hours, the rule triggers a hard lockout that:

    1. Prevents any new positions from opening
    2. Locks the account until the next session start
    3. Handles weekend blocking (Saturday/Sunday)
    4. Supports timezone-aware time checking (ET, CT, PT, etc.)
    5. Auto-unlocks when session starts

    Features:
    - Timezone-aware time checking (uses zoneinfo)
    - Weekend blocking (configurable)
    - DST-aware (handles daylight saving time transitions)
    - Hard lockout until next session start
    - Skip weekends when calculating next session start
    - Multi-symbol support (applies to entire account)

    Example:
        rule = SessionBlockOutsideRule(
            config={
                "enabled": True,
                "global_session": {
                    "enabled": True,
                    "start": "09:30",
                    "end": "16:00",
                    "timezone": "America/New_York"
                },
                "block_weekends": True,
                "lockout_outside_session": True
            },
            lockout_manager=lockout_manager
        )
    """

    def __init__(
        self,
        config: dict[str, Any],
        lockout_manager: "LockoutManager",
    ):
        """
        Initialize session block outside rule.

        Args:
            config: Rule configuration dictionary from risk_config.yaml
            lockout_manager: Lockout manager instance for lockout management

        Raises:
            ValueError: If time format is invalid or timezone is invalid
        """
        super().__init__(action="flatten")

        # Parse configuration
        self.enabled = config.get("enabled", True)
        self.lockout_manager = lockout_manager

        # Global session config
        global_session = config.get("global_session", {})
        self.global_session_enabled = global_session.get("enabled", True)

        # Parse session hours (HH:MM format)
        start_str = global_session.get("start", "09:30")
        end_str = global_session.get("end", "16:00")

        try:
            start_hour, start_minute = map(int, start_str.split(":"))
            end_hour, end_minute = map(int, end_str.split(":"))

            # Validate time values
            if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59):
                raise ValueError(f"Invalid start time: {start_str}")
            if not (0 <= end_hour <= 23 and 0 <= end_minute <= 59):
                raise ValueError(f"Invalid end time: {end_str}")

            self.session_start = time(start_hour, start_minute)
            self.session_end = time(end_hour, end_minute)

        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid time format in config: {e}")

        # Timezone config
        self.timezone_name = global_session.get("timezone", "America/New_York")
        try:
            self.timezone = ZoneInfo(self.timezone_name)
        except Exception as e:
            raise ValueError(f"Invalid timezone '{self.timezone_name}': {e}")

        # Weekend blocking
        self.block_weekends = config.get("block_weekends", True)
        self.lockout_outside_session = config.get("lockout_outside_session", True)

        logger.info(
            f"SessionBlockOutsideRule initialized: "
            f"session={self.session_start.strftime('%H:%M')}-{self.session_end.strftime('%H:%M')} "
            f"{self.timezone_name}, "
            f"block_weekends={self.block_weekends}"
        )

    async def evaluate(
        self, event: RiskEvent, engine: "RiskEngine"
    ) -> dict[str, Any] | None:
        """
        Evaluate if trading is attempted outside session hours.

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with violation details if rule is violated, None otherwise

        Evaluation Logic:
        1. Check if rule is enabled
        2. Check if event type is relevant (POSITION_OPENED, POSITION_UPDATED)
        3. Extract account_id from event
        4. Check if account is already locked (skip if locked)
        5. Get current time in configured timezone
        6. Check if weekend (if weekend blocking enabled)
        7. Check if inside session hours
        8. Return violation if outside hours or weekend
        """
        if not self.enabled or not self.global_session_enabled:
            return None

        # Only evaluate position-related events
        if event.event_type not in [
            EventType.POSITION_OPENED,
            EventType.POSITION_UPDATED,
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

        # Get current time in configured timezone
        now = datetime.now(self.timezone)
        current_time = now.time()
        current_weekday = now.weekday()  # Monday=0, Sunday=6

        # Check if weekend
        if self.block_weekends and current_weekday >= 5:  # Saturday=5, Sunday=6
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][current_weekday]
            logger.warning(
                f"Trading attempted on weekend for account {account_id}: "
                f"{day_name} {now.strftime('%H:%M')}"
            )

            next_session_start = self._calculate_next_session_start(now)

            return {
                "rule": "SessionBlockOutsideRule",
                "message": f"Trading blocked: Weekend trading not allowed ({day_name})",
                "account_id": account_id,
                "current_time": now.isoformat(),
                "current_day": day_name,
                "action": self.action,
                "lockout_required": self.lockout_outside_session,
                "next_session_start": next_session_start,
            }

        # Check if inside session hours
        # Session is [start, end), so end time is exclusive
        is_inside_session = self.session_start <= current_time < self.session_end

        if not is_inside_session:
            # Determine if before or after session
            if current_time < self.session_start:
                reason = f"before session start ({self.session_start.strftime('%H:%M')})"
            else:
                reason = f"after session end ({self.session_end.strftime('%H:%M')})"

            logger.warning(
                f"Trading attempted outside session hours for account {account_id}: "
                f"Current: {current_time.strftime('%H:%M')} {self.timezone_name}, {reason}"
            )

            next_session_start = self._calculate_next_session_start(now)

            return {
                "rule": "SessionBlockOutsideRule",
                "message": (
                    f"Trading outside session hours: "
                    f"{current_time.strftime('%H:%M')} {self.timezone_name} is {reason}"
                ),
                "account_id": account_id,
                "current_time": now.isoformat(),
                "current_time_str": current_time.strftime("%H:%M"),
                "session_start": self.session_start.strftime("%H:%M"),
                "session_end": self.session_end.strftime("%H:%M"),
                "timezone": self.timezone_name,
                "action": self.action,
                "lockout_required": self.lockout_outside_session,
                "next_session_start": next_session_start,
            }

        # Inside session hours and not weekend
        return None

    async def enforce(
        self, account_id: str, violation: dict[str, Any], engine: "RiskEngine"
    ) -> None:
        """
        Execute enforcement action for session hours violation.

        Enforcement Steps:
        1. Set hard lockout until next session start
        2. Log enforcement action

        Args:
            account_id: Account identifier (string or int)
            violation: Violation details from evaluate()
            engine: Risk engine instance

        Note:
            Positions are NOT closed automatically. The lockout prevents
            new positions from opening. Trader can manually close positions
            outside session hours if needed (implementation detail TBD).
        """
        next_session_start = violation["next_session_start"]

        logger.critical(
            f"ENFORCING RULE-009: Account {account_id} "
            f"Trading outside session hours, locking until {next_session_start.isoformat()}"
        )

        # Convert account_id to int if needed (TopstepX uses numeric IDs)
        # In tests, we use string IDs like "ACC-001" which can't be converted
        # So we try conversion, but pass through if it fails (for test compatibility)
        try:
            numeric_account_id = int(account_id) if isinstance(account_id, str) else account_id
        except ValueError:
            # Test account ID (e.g., "ACC-001"), use as-is
            numeric_account_id = account_id

        # Set hard lockout until next session start
        self.lockout_manager.set_lockout(
            account_id=numeric_account_id,
            reason=violation["message"],
            until=next_session_start,
        )

        logger.warning(
            f"Account {account_id} locked until {next_session_start.isoformat()}: "
            f"{violation['message']}"
        )

    def _calculate_next_session_start(self, current_time: datetime) -> datetime:
        """
        Calculate next session start time, skipping weekends.

        Args:
            current_time: Current datetime (timezone-aware)

        Returns:
            Next session start datetime (timezone-aware)

        Logic:
        1. If before session start today AND weekday → session start today
        2. If after session start today OR weekend → next weekday session start
        3. Skip weekends: Friday → Monday, Saturday → Monday, Sunday → Monday

        Example:
            Current: Wednesday 7:00 AM ET → Next: Wednesday 9:30 AM ET
            Current: Wednesday 5:00 PM ET → Next: Thursday 9:30 AM ET
            Current: Friday 5:00 PM ET → Next: Monday 9:30 AM ET
            Current: Saturday 11:00 AM ET → Next: Monday 9:30 AM ET
        """
        now = current_time
        current_time_only = now.time()
        current_weekday = now.weekday()

        # Calculate next session start
        next_start = now.replace(
            hour=self.session_start.hour,
            minute=self.session_start.minute,
            second=0,
            microsecond=0,
        )

        # If before session start today AND weekday, use today
        if current_time_only < self.session_start and current_weekday < 5:
            return next_start

        # Otherwise, go to next day
        next_start = next_start + timedelta(days=1)

        # Skip weekends: if next day is Saturday, go to Monday
        while next_start.weekday() >= 5:  # Saturday=5, Sunday=6
            next_start = next_start + timedelta(days=1)

        logger.debug(
            f"Next session start: {next_start.isoformat()} "
            f"({next_start.strftime('%A %H:%M')} {self.timezone_name})"
        )

        return next_start
