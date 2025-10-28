"""
RULE-006: Trade Frequency Limit

Purpose: Prevent overtrading by limiting trades per time window (minute/hour/session).
Category: Timer/Cooldown (Category 2)
Priority: High

Trigger: TRADE_EXECUTED events
Enforcement: Set temporary cooldown timer (NO position close - trade already executed)

Configuration:
    - limits: Trade limits per window
        - per_minute: Max trades per minute (e.g., 3)
        - per_hour: Max trades per hour (e.g., 10)
        - per_session: Max trades per session (e.g., 50)
    - cooldown_on_breach: Cooldown durations for each breach type
        - per_minute_breach: Cooldown in seconds (e.g., 60)
        - per_hour_breach: Cooldown in seconds (e.g., 1800)
        - per_session_breach: Cooldown in seconds (e.g., 3600)

Dependencies:
    - Timer Manager: Set/clear cooldown timers
    - Database: Track trade timestamps in rolling windows
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine
    from risk_manager.state.timer_manager import TimerManager


class TradeFrequencyLimitRule(RiskRule):
    """
    Enforce maximum trade frequency limits in rolling time windows.

    This rule tracks trades in multiple time windows (per minute, per hour,
    per session) to prevent overtrading. When a limit is breached, the rule
    sets a temporary cooldown timer that:

    1. Does NOT close positions (trade already executed)
    2. Sets a cooldown timer via TimerManager
    3. Auto-unlocks when timer expires
    4. Prevents new trades during cooldown (enforced by engine)

    Features:
    - Rolling window tracking (per minute, per hour, per session)
    - Priority order: minute > hour > session (shortest cooldown first)
    - Multi-account support (independent tracking)
    - Auto-unlock via timer expiry
    - Database persistence for crash recovery

    Example:
        rule = TradeFrequencyLimitRule(
            limits={
                'per_minute': 3,
                'per_hour': 10,
                'per_session': 50
            },
            cooldown_on_breach={
                'per_minute_breach': 60,      # 1 min
                'per_hour_breach': 1800,      # 30 min
                'per_session_breach': 3600    # 1 hour
            },
            timer_manager=timer_manager,
            db=db
        )
    """

    def __init__(
        self,
        limits: dict[str, int],
        cooldown_on_breach: dict[str, int],
        timer_manager: "TimerManager",
        db: Any,
        action: str = "cooldown",
    ):
        """
        Initialize trade frequency limit rule.

        Args:
            limits: Trade limits per window
                - per_minute: Max trades per minute
                - per_hour: Max trades per hour
                - per_session: Max trades per session
            cooldown_on_breach: Cooldown durations (seconds) for each breach type
                - per_minute_breach: Cooldown for per-minute breach
                - per_hour_breach: Cooldown for per-hour breach
                - per_session_breach: Cooldown for per-session breach
            timer_manager: Timer manager instance for cooldown management
            db: Database instance for trade tracking
            action: Action to take on violation (default: "cooldown")

        Raises:
            ValueError: If any limit is not positive
        """
        super().__init__(action=action)

        # Validate limits
        for key, value in limits.items():
            if value <= 0:
                raise ValueError(f"Trade limit '{key}' must be positive, got {value}")

        self.limits = limits
        self.cooldown_on_breach = cooldown_on_breach
        self.timer_manager = timer_manager
        self.db = db

        logger.info(
            f"TradeFrequencyLimitRule initialized: "
            f"limits={limits}, cooldowns={cooldown_on_breach}"
        )

    async def evaluate(
        self, event: RiskEvent, engine: "RiskEngine"
    ) -> dict[str, Any] | None:
        """
        Evaluate if trade frequency limit is violated.

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with violation details if rule is violated, None otherwise

        Evaluation Logic:
        1. Check if rule is enabled
        2. Check if event type is TRADE_EXECUTED
        3. Extract account_id from event
        4. Check trade counts in rolling windows (minute, hour, session)
        5. Return violation for first exceeded limit (priority order)
        6. Include breach type and cooldown duration

        Priority Order:
        - per_minute (shortest cooldown) checked first
        - per_hour checked second
        - per_session checked last
        """
        if not self.enabled:
            return None

        # Only evaluate on trade execution events
        if event.event_type != EventType.TRADE_EXECUTED:
            return None

        # Extract account ID
        account_id = event.data.get("account_id")
        if not account_id:
            logger.debug(f"Event missing account_id: {event.data}")
            return None

        # Get trade counts in rolling windows
        try:
            # Check per-minute limit (highest priority - shortest cooldown)
            per_minute_limit = self.limits.get('per_minute', 0)
            if per_minute_limit > 0:
                minute_count = self.db.get_trade_count(account_id, window=60)
                if minute_count > per_minute_limit:
                    logger.warning(
                        f"Per-minute trade limit breached for account {account_id}: "
                        f"{minute_count} trades >= {per_minute_limit} limit"
                    )
                    return {
                        "rule": "TradeFrequencyLimitRule",
                        "message": (
                            f"Trade frequency limit exceeded: {minute_count} trades "
                            f"in last minute (limit: {per_minute_limit})"
                        ),
                        "account_id": account_id,
                        "breach_type": "per_minute",
                        "trade_count": minute_count,
                        "limit": per_minute_limit,
                        "cooldown_duration": self.cooldown_on_breach.get('per_minute_breach', 60),
                        "action": self.action,
                    }

            # Check per-hour limit (second priority)
            per_hour_limit = self.limits.get('per_hour', 0)
            if per_hour_limit > 0:
                hour_count = self.db.get_trade_count(account_id, window=3600)
                if hour_count > per_hour_limit:
                    logger.warning(
                        f"Per-hour trade limit breached for account {account_id}: "
                        f"{hour_count} trades >= {per_hour_limit} limit"
                    )
                    return {
                        "rule": "TradeFrequencyLimitRule",
                        "message": (
                            f"Trade frequency limit exceeded: {hour_count} trades "
                            f"in last hour (limit: {per_hour_limit})"
                        ),
                        "account_id": account_id,
                        "breach_type": "per_hour",
                        "trade_count": hour_count,
                        "limit": per_hour_limit,
                        "cooldown_duration": self.cooldown_on_breach.get('per_hour_breach', 1800),
                        "action": self.action,
                    }

            # Check per-session limit (lowest priority)
            per_session_limit = self.limits.get('per_session', 0)
            if per_session_limit > 0:
                session_count = self.db.get_session_trade_count(account_id)
                if session_count > per_session_limit:
                    logger.warning(
                        f"Per-session trade limit breached for account {account_id}: "
                        f"{session_count} trades >= {per_session_limit} limit"
                    )
                    return {
                        "rule": "TradeFrequencyLimitRule",
                        "message": (
                            f"Trade frequency limit exceeded: {session_count} trades "
                            f"in session (limit: {per_session_limit})"
                        ),
                        "account_id": account_id,
                        "breach_type": "per_session",
                        "trade_count": session_count,
                        "limit": per_session_limit,
                        "cooldown_duration": self.cooldown_on_breach.get('per_session_breach', 3600),
                        "action": self.action,
                    }

        except Exception as e:
            logger.error(f"Error checking trade frequency: {e}", exc_info=True)
            return None

        # No limit breached
        return None

    async def enforce(
        self, account_id: str, violation: dict[str, Any], engine: "RiskEngine"
    ) -> None:
        """
        Execute enforcement action for trade frequency violation.

        Enforcement Steps:
        1. NO position close (trade already executed, can't prevent it)
        2. Set cooldown timer based on breach type
        3. Auto-unlock when timer expires (handled by TimerManager)

        Args:
            account_id: Account identifier
            violation: Violation details from evaluate()
            engine: Risk engine instance

        Note:
            Unlike hard lockout rules, this does NOT close positions.
            The trade has already executed - we just prevent new trades
            during the cooldown period.
        """
        breach_type = violation["breach_type"]
        cooldown_duration = violation["cooldown_duration"]
        trade_count = violation["trade_count"]
        limit = violation["limit"]

        logger.warning(
            f"ENFORCING RULE-006: Account {account_id} "
            f"Trade frequency breach: {breach_type} "
            f"({trade_count} trades >= {limit} limit)"
        )

        # Set cooldown timer
        timer_name = f"trade_frequency_{account_id}"

        # Callback to execute when timer expires (auto-unlock)
        def unlock_callback():
            logger.info(
                f"Trade frequency cooldown expired for account {account_id} "
                f"({breach_type})"
            )

        # Start timer with auto-unlock callback
        await self.timer_manager.start_timer(
            name=timer_name,
            duration=cooldown_duration,
            callback=unlock_callback
        )

        logger.info(
            f"Account {account_id} cooldown set: {cooldown_duration}s "
            f"({breach_type} breach)"
        )
