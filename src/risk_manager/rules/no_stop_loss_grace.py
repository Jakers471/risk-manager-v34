"""
RULE-008: No Stop-Loss Grace

Enforce stop-loss placement - close position if no stop-loss placed within grace period.

Category: Trade-by-Trade (Category 1)
Priority: Medium

Trigger Conditions:
1. POSITION_OPENED: Start grace period timer when position opens
2. ORDER_PLACED (type=3, stopPrice present): Detect stop-loss order, cancel timer
3. POSITION_CLOSED: Cancel timer if position closed before grace period expires
4. Timer expiry: Check if stop-loss exists, close position if missing

Enforcement Action:
- Close the position if no stop-loss placed within grace period
- NO lockout (trade-by-trade enforcement)
- Can trade immediately after enforcement

Configuration:
- grace_period_seconds: Time allowed to place stop-loss (default: 10 seconds)
- enforcement: "close_position"
- enabled: Enable/disable the rule

Reference: docs/specifications/unified/rules/RULE-008-no-stop-loss-grace.md
"""

from typing import Any, Optional

from loguru import logger

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule
from risk_manager.state.timer_manager import TimerManager


class NoStopLossGraceRule(RiskRule):
    """
    Enforce stop-loss placement with grace period.

    Starts a countdown timer when a position is opened. If no stop-loss order
    (type=3 with stopPrice) is placed within the grace period, closes the position.

    Key Features:
    - Timer per contract (tracked by contract_id)
    - Stop-loss order (type=3) with stopPrice cancels timer
    - Position close cancels timer
    - Trade-by-trade enforcement (no lockout)
    """

    def __init__(
        self,
        grace_period_seconds: int = 10,
        enforcement: str = "close_position",
        timer_manager: Optional[TimerManager] = None,
        enabled: bool = True,
    ):
        """
        Initialize the No Stop-Loss Grace rule.

        Args:
            grace_period_seconds: Time allowed to place stop-loss (seconds)
            enforcement: Enforcement action (always "close_position" for this rule)
            timer_manager: TimerManager instance for grace period timers
            enabled: Enable/disable the rule
        """
        super().__init__(action=enforcement)

        self.grace_period_seconds = grace_period_seconds
        self.enforcement = enforcement
        self.timer_manager = timer_manager
        self.enabled = enabled

        # Store engine reference for callbacks
        self._engine: Optional[Any] = None

        logger.info(
            f"NoStopLossGraceRule initialized - "
            f"Grace period: {grace_period_seconds}s, "
            f"Enforcement: {enforcement}, "
            f"Enabled: {enabled}"
        )

    async def evaluate(self, event: RiskEvent, engine: Any) -> Optional[dict[str, Any]]:
        """
        Evaluate if stop-loss grace period rules are followed.

        Handles three event types:
        1. POSITION_OPENED: Start grace period timer
        2. ORDER_PLACED: Check if stop-loss (type=3) placed, cancel timer
        3. POSITION_CLOSED: Cancel timer if position closed

        Args:
            event: Risk event to evaluate
            engine: Risk engine instance (provides enforcement executor)

        Returns:
            None (enforcement happens via timer callback, not immediate violation)
        """
        # Skip if rule is disabled
        if not self.enabled:
            return None

        # Store engine reference for timer callbacks
        if self._engine is None:
            self._engine = engine

        # Handle different event types
        if event.event_type == EventType.POSITION_OPENED:
            return await self._handle_position_opened(event)

        elif event.event_type == EventType.ORDER_PLACED:
            return await self._handle_order_placed(event)

        elif event.event_type == EventType.POSITION_CLOSED:
            return await self._handle_position_closed(event)

        # Ignore other event types
        return None

    async def _handle_position_opened(self, event: RiskEvent) -> None:
        """
        Handle POSITION_OPENED event by starting grace period timer.

        Args:
            event: Position opened event

        Returns:
            None (no immediate violation)
        """
        # Extract position data
        contract_id = event.data.get("contract_id")
        symbol = event.data.get("symbol")
        size = event.data.get("size", 0)

        # Validate required fields
        if not contract_id:
            logger.warning("POSITION_OPENED event missing contract_id, ignoring")
            return None

        # Ignore zero-size positions (shouldn't happen for POSITION_OPENED, but be safe)
        if size == 0:
            logger.debug(f"POSITION_OPENED with size=0 for {contract_id}, ignoring")
            return None

        # Start grace period timer
        timer_name = self._get_timer_name(contract_id)

        logger.info(
            f"RULE-008: Position opened {symbol}/{contract_id} (size={size}), "
            f"starting {self.grace_period_seconds}s grace period for stop-loss"
        )

        # Create callback that will execute when timer expires
        async def grace_period_expired():
            """Callback executed when grace period expires without stop-loss."""
            await self._enforce_grace_period_violation(symbol, contract_id)

        # Start the timer
        await self.timer_manager.start_timer(
            name=timer_name,
            duration=self.grace_period_seconds,
            callback=grace_period_expired,
        )

        return None

    async def _handle_order_placed(self, event: RiskEvent) -> None:
        """
        Handle ORDER_PLACED event to detect stop-loss orders.

        Checks if the order is a stop-loss (type=3 with stopPrice).
        If so, cancels the grace period timer for that position.

        Args:
            event: Order placed event

        Returns:
            None
        """
        # Extract order data
        contract_id = event.data.get("contract_id")
        order_type = event.data.get("type")
        stop_price = event.data.get("stopPrice")
        symbol = event.data.get("symbol")

        # Validate required fields
        if not contract_id:
            return None

        # Check if this is a stop-loss order
        # According to spec: type=3 (STOP) AND stopPrice must be present
        if order_type == 3 and stop_price is not None:
            # Stop-loss order placed! Cancel grace period timer
            timer_name = self._get_timer_name(contract_id)

            if self.timer_manager.has_timer(timer_name):
                self.timer_manager.cancel_timer(timer_name)
                logger.info(
                    f"RULE-008: Stop-loss order placed for {symbol}/{contract_id} "
                    f"(stopPrice={stop_price}), grace period cancelled ✅"
                )
            else:
                logger.debug(
                    f"Stop-loss order placed for {contract_id} but no active grace period"
                )

        return None

    async def _handle_position_closed(self, event: RiskEvent) -> None:
        """
        Handle POSITION_CLOSED event by cancelling grace period timer.

        If a position is closed before the grace period expires, cancel the timer.

        Args:
            event: Position closed event

        Returns:
            None
        """
        contract_id = event.data.get("contract_id")
        symbol = event.data.get("symbol")

        if not contract_id:
            return None

        # Cancel grace period timer if it exists
        timer_name = self._get_timer_name(contract_id)

        if self.timer_manager.has_timer(timer_name):
            self.timer_manager.cancel_timer(timer_name)
            logger.info(
                f"RULE-008: Position closed for {symbol}/{contract_id}, "
                f"grace period cancelled"
            )

        return None

    async def _enforce_grace_period_violation(self, symbol: str, contract_id: str) -> None:
        """
        Enforce grace period violation by closing the position.

        This method is called by the timer callback when grace period expires
        without a stop-loss order being placed.

        Args:
            symbol: Instrument symbol
            contract_id: Contract ID to close
        """
        logger.warning(
            f"⚠️ RULE-008 BREACH: No stop-loss placed within {self.grace_period_seconds}s "
            f"for {symbol}/{contract_id}"
        )

        # Get enforcement executor from engine
        if not self._engine or not hasattr(self._engine, "enforcement_executor"):
            logger.error("Cannot enforce - no engine or enforcement_executor available")
            return

        executor = self._engine.enforcement_executor

        logger.warning(
            f"🚨 ENFORCING RULE-008: Closing position {symbol}/{contract_id} "
            f"(no stop-loss placed within grace period)"
        )

        # Close the position
        result = await executor.close_position(symbol, contract_id)

        if result["success"]:
            logger.success(
                f"✅ RULE-008 ENFORCED: Position {symbol}/{contract_id} closed "
                f"(grace period expired without stop-loss)"
            )
        else:
            logger.error(
                f"❌ RULE-008 ENFORCEMENT FAILED: {symbol}/{contract_id} - "
                f"{result.get('error', 'Unknown error')}"
            )

    def _get_timer_name(self, contract_id: str) -> str:
        """
        Generate unique timer name for a contract.

        Args:
            contract_id: Contract ID

        Returns:
            Timer name string
        """
        return f"no_stop_loss_grace_{contract_id}"

    def get_status(self) -> dict[str, Any]:
        """
        Get current rule status.

        Returns:
            Dictionary with rule status and active timers
        """
        active_timers = []

        if self.timer_manager:
            # Get all timers for this rule
            all_timers = self.timer_manager.get_all_timers()
            for name, timer_info in all_timers.items():
                if name.startswith("no_stop_loss_grace_"):
                    contract_id = name.replace("no_stop_loss_grace_", "")
                    remaining = self.timer_manager.get_remaining_time(name)
                    active_timers.append({
                        "contract_id": contract_id,
                        "remaining_seconds": remaining,
                    })

        return {
            "rule": "NoStopLossGrace",
            "enabled": self.enabled,
            "grace_period_seconds": self.grace_period_seconds,
            "enforcement": self.enforcement,
            "active_timers": active_timers,
        }
