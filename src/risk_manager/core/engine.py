"""Core risk engine for evaluation and enforcement."""

import asyncio
from datetime import datetime
from typing import Any

from loguru import logger

from risk_manager.core.config import RiskConfig
from risk_manager.core.events import EventBus, EventType, RiskEvent


class RiskEngine:
    """Core risk evaluation and enforcement engine."""

    def __init__(self, config: RiskConfig, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.rules: list[Any] = []  # Will be filled with rule objects
        self.running = False

        # State tracking
        self.daily_pnl = 0.0
        self.peak_balance = 0.0
        self.current_positions: dict[str, Any] = {}

        logger.info("Risk Engine initialized")

    async def start(self) -> None:
        """Start the risk engine."""
        self.running = True
        logger.info("Risk Engine started")

        await self.event_bus.publish(
            RiskEvent(
                event_type=EventType.SYSTEM_STARTED,
                data={"component": "risk_engine"},
            )
        )

    async def stop(self) -> None:
        """Stop the risk engine."""
        self.running = False
        logger.info("Risk Engine stopped")

        await self.event_bus.publish(
            RiskEvent(
                event_type=EventType.SYSTEM_STOPPED,
                data={"component": "risk_engine"},
            )
        )

    def add_rule(self, rule: Any) -> None:
        """Add a risk rule."""
        self.rules.append(rule)
        logger.info(f"Added rule: {rule.__class__.__name__}")

    async def evaluate_rules(self, event: RiskEvent) -> None:
        """Evaluate all rules against an event."""
        for rule in self.rules:
            try:
                violation = await rule.evaluate(event, self)
                if violation:
                    await self._handle_violation(rule, violation)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.__class__.__name__}: {e}")

    async def _handle_violation(self, rule: Any, violation: dict[str, Any]) -> None:
        """Handle a rule violation."""
        logger.warning(f"Rule violation: {rule.__class__.__name__} - {violation}")

        await self.event_bus.publish(
            RiskEvent(
                event_type=EventType.RULE_VIOLATED,
                data={
                    "rule": rule.__class__.__name__,
                    "violation": violation,
                },
                severity="warning",
            )
        )

        # Execute enforcement action if specified
        action = violation.get("action")
        if action == "flatten":
            await self.flatten_all_positions()
        elif action == "pause":
            await self.pause_trading()
        elif action == "alert":
            await self.send_alert(violation)

    async def flatten_all_positions(self) -> None:
        """Flatten all open positions."""
        logger.warning("FLATTENING ALL POSITIONS")

        await self.event_bus.publish(
            RiskEvent(
                event_type=EventType.ENFORCEMENT_ACTION,
                data={
                    "action": "flatten_all",
                    "reason": "risk_rule_violation",
                },
                severity="critical",
            )
        )

        # Implementation will connect to trading integration
        # For now, just log the action

    async def pause_trading(self) -> None:
        """Pause all trading activity."""
        logger.warning("PAUSING TRADING")

        await self.event_bus.publish(
            RiskEvent(
                event_type=EventType.ENFORCEMENT_ACTION,
                data={
                    "action": "pause_trading",
                    "reason": "risk_rule_violation",
                },
                severity="error",
            )
        )

    async def send_alert(self, violation: dict[str, Any]) -> None:
        """Send alert about violation."""
        logger.info(f"ALERT: {violation}")

        await self.event_bus.publish(
            RiskEvent(
                event_type=EventType.RULE_WARNING,
                data=violation,
                severity="warning",
            )
        )

    def update_pnl(self, realized_pnl: float, unrealized_pnl: float) -> None:
        """Update P&L tracking."""
        self.daily_pnl = realized_pnl
        total_pnl = realized_pnl + unrealized_pnl

        # Update peak for drawdown calculation
        if total_pnl > self.peak_balance:
            self.peak_balance = total_pnl

    def get_stats(self) -> dict[str, Any]:
        """Get current risk statistics."""
        return {
            "daily_pnl": self.daily_pnl,
            "peak_balance": self.peak_balance,
            "position_count": len(self.current_positions),
            "rules_active": len(self.rules),
            "running": self.running,
        }
