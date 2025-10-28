"""
RULE-007: Cooldown After Loss

Purpose: Force break after losing trades to prevent revenge trading.
Category: Timer/Cooldown (Category 2)
Priority: Medium

Trigger: TRADE_EXECUTED, POSITION_CLOSED events (when profitAndLoss < 0)
Enforcement: Close all positions + Start tiered cooldown + Auto-unlock when timer expires

Configuration:
    - loss_thresholds: List of {loss_amount, cooldown_duration} pairs
    - action: Enforcement action (default: "flatten")

Dependencies:
    - MOD-003 TimerManager: Countdown timers with callbacks
    - PnL Tracker: Track trade P&L
    - Lockout Manager: Set/clear temporary lockouts

Example Config:
    cooldown_after_loss:
      enabled: true
      loss_thresholds:
        - loss_amount: -100.0
          cooldown_duration: 300   # 5 min
        - loss_amount: -200.0
          cooldown_duration: 900   # 15 min
        - loss_amount: -300.0
          cooldown_duration: 1800  # 30 min
"""

from typing import TYPE_CHECKING, Any

from loguru import logger

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule

if TYPE_CHECKING:
    from risk_manager.core.engine import RiskEngine
    from risk_manager.state.lockout_manager import LockoutManager
    from risk_manager.state.pnl_tracker import PnLTracker
    from risk_manager.state.timer_manager import TimerManager


class CooldownAfterLossRule(RiskRule):
    """
    Enforce cooldown periods after losing trades to prevent revenge trading.

    This rule triggers a temporary lockout (cooldown) when a trader incurs
    a losing trade above configured thresholds. The cooldown duration scales
    with the size of the loss (tiered cooldowns).

    Features:
    - Tiered cooldown durations based on loss amount
    - Only triggers on realized losses (closed trades)
    - Ignores half-turn trades (profitAndLoss=None)
    - Automatic unlock when timer expires
    - Prevents trading during cooldown
    - Closes all positions when cooldown triggers

    Example:
        rule = CooldownAfterLossRule(
            loss_thresholds=[
                {"loss_amount": -100.0, "cooldown_duration": 300},
                {"loss_amount": -200.0, "cooldown_duration": 900},
            ],
            timer_manager=timer_manager,
            pnl_tracker=pnl_tracker,
            lockout_manager=lockout_manager
        )
    """

    def __init__(
        self,
        loss_thresholds: list[dict[str, float]],
        timer_manager: "TimerManager",
        pnl_tracker: "PnLTracker",
        lockout_manager: "LockoutManager",
        action: str = "flatten",
    ):
        """
        Initialize cooldown after loss rule.

        Args:
            loss_thresholds: List of {loss_amount, cooldown_duration} dicts
                Example: [
                    {"loss_amount": -100.0, "cooldown_duration": 300},
                    {"loss_amount": -200.0, "cooldown_duration": 900},
                ]
            timer_manager: TimerManager instance for cooldown timers
            pnl_tracker: PnL tracker instance for P&L tracking
            lockout_manager: Lockout manager for temporary lockouts
            action: Action to take on violation (default: "flatten")

        Raises:
            ValueError: If loss amounts are positive or durations are negative
        """
        super().__init__(action=action)

        # Validate thresholds
        for threshold in loss_thresholds:
            loss_amount = threshold.get("loss_amount", 0)
            duration = threshold.get("cooldown_duration", 0)

            if loss_amount >= 0:
                raise ValueError(
                    f"Loss amounts must be negative, got {loss_amount}"
                )

            if duration < 0:
                raise ValueError(
                    f"Cooldown duration must be non-negative, got {duration}"
                )

        # Sort thresholds by loss amount (largest loss first)
        # This ensures we match the highest applicable tier first
        self.loss_thresholds = sorted(
            loss_thresholds,
            key=lambda x: x["loss_amount"]
        )

        self.timer_manager = timer_manager
        self.pnl_tracker = pnl_tracker
        self.lockout_manager = lockout_manager

        logger.info(
            f"CooldownAfterLossRule initialized: {len(loss_thresholds)} tiers"
        )

    async def evaluate(
        self, event: RiskEvent, engine: "RiskEngine"
    ) -> dict[str, Any] | None:
        """
        Evaluate if cooldown should trigger after losing trade.

        Args:
            event: The risk event to evaluate
            engine: The risk engine for accessing state

        Returns:
            Dictionary with violation details if rule is violated, None otherwise

        Evaluation Logic:
        1. Check if rule is enabled
        2. Check if event type is trade-related (TRADE_EXECUTED, POSITION_CLOSED)
        3. Extract account_id and profitAndLoss
        4. Skip if profitAndLoss is None (half-turn) or positive (winning trade)
        5. Skip if account is already in cooldown
        6. Find highest applicable cooldown tier
        7. Return violation if tier matched
        """
        if not self.enabled:
            return None

        # Only evaluate trade execution and position close events
        if event.event_type not in [
            EventType.TRADE_EXECUTED,
            EventType.POSITION_CLOSED,
        ]:
            return None

        # Extract account ID
        account_id = event.data.get("account_id")
        if not account_id:
            logger.debug(f"Event missing account_id: {event.data}")
            return None

        # Skip if account is already in cooldown
        if self.lockout_manager.is_locked_out(account_id):
            logger.debug(
                f"Account {account_id} already in cooldown, skipping evaluation"
            )
            return None

        # Extract profit and loss
        profit_and_loss = event.data.get("profitAndLoss")

        # Ignore half-turn trades (opening positions with no realized P&L)
        if profit_and_loss is None:
            logger.debug("Ignoring half-turn trade (no realized P&L)")
            return None

        # Ignore winning trades and breakeven
        if profit_and_loss >= 0:
            logger.debug(
                f"Trade profitable (+${profit_and_loss:.2f}), no cooldown"
            )
            return None

        # Find applicable cooldown tier
        # Iterate from largest loss to smallest to find highest tier
        applicable_tier = None
        for threshold in self.loss_thresholds:
            loss_amount = threshold["loss_amount"]
            # Check if trade loss meets or exceeds this tier
            # Note: Both are negative, so use <= (more negative = larger loss)
            if profit_and_loss <= loss_amount:
                applicable_tier = threshold
                break

        # No tier matched
        if not applicable_tier:
            logger.debug(
                f"Loss ${profit_and_loss:.2f} below all thresholds, no cooldown"
            )
            return None

        # Cooldown triggered
        cooldown_duration = applicable_tier["cooldown_duration"]
        logger.warning(
            f"Cooldown triggered for account {account_id}: "
            f"Loss=${profit_and_loss:.2f}, Cooldown={cooldown_duration}s"
        )

        return {
            "rule": "CooldownAfterLossRule",
            "message": (
                f"Cooldown triggered after ${profit_and_loss:.2f} loss "
                f"({cooldown_duration}s cooldown)"
            ),
            "account_id": account_id,
            "loss_amount": profit_and_loss,
            "cooldown_duration": cooldown_duration,
            "action": self.action,
        }

    async def enforce(
        self, account_id: str, violation: dict[str, Any], engine: "RiskEngine"
    ) -> None:
        """
        Execute enforcement action for cooldown trigger.

        Enforcement Steps:
        1. Close all positions (via engine)
        2. Set temporary lockout
        3. Start cooldown timer
        4. When timer expires, unlock account

        Args:
            account_id: Account identifier
            violation: Violation details from evaluate()
            engine: Risk engine instance

        Note:
            The actual position closing is delegated to the engine's
            enforcement module. This method handles the lockout and timer.
        """
        loss_amount = violation["loss_amount"]
        cooldown_duration = violation["cooldown_duration"]

        logger.critical(
            f"ENFORCING RULE-007: Account {account_id} "
            f"Loss: ${loss_amount:.2f}, Cooldown: {cooldown_duration}s"
        )

        # Set temporary lockout
        # Try to convert account_id to int if it's a numeric string
        # Otherwise, keep as-is (tests may use string IDs)
        try:
            account_id_for_lockout = int(account_id) if isinstance(account_id, str) and account_id.isdigit() else account_id
        except (ValueError, AttributeError):
            account_id_for_lockout = account_id

        # Set cooldown (duration-based lockout with auto-unlock)
        reason = violation.get("message", f"Cooldown after ${loss_amount:.2f} loss")
        await self.lockout_manager.set_cooldown(
            account_id=account_id_for_lockout,
            reason=reason,
            duration_seconds=cooldown_duration
        )

        logger.warning(
            f"Account {account_id} locked for {cooldown_duration}s: {reason}"
        )
