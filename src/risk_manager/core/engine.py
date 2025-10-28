"""Core risk engine for evaluation and enforcement."""

import asyncio
from datetime import datetime
from typing import Any

from loguru import logger
from project_x_py.utils import ProjectXLogger

from risk_manager.core.config import RiskConfig
from risk_manager.core.events import EventBus, EventType, RiskEvent

# Get SDK logger for standardized logging
sdk_logger = ProjectXLogger.get_logger(__name__)


class RiskEngine:
    """Core risk evaluation and enforcement engine."""

    def __init__(self, config: RiskConfig, event_bus: EventBus, trading_integration: Any | None = None):
        self.config = config
        self.event_bus = event_bus
        self.trading_integration = trading_integration  # Reference to TradingIntegration for enforcement
        self.rules: list[Any] = []  # Will be filled with rule objects
        self.running = False

        # State tracking
        self.daily_pnl = 0.0
        self.peak_balance = 0.0
        self.current_positions: dict[str, Any] = {}
        self.market_prices: dict[str, float] = {}  # Real-time market prices by symbol

        logger.info("Risk Engine initialized")

    async def start(self) -> None:
        """Start the risk engine."""
        self.running = True

        # Checkpoint 5: Event loop running
        sdk_logger.info(f"✅ Event loop running: {len(self.rules)} active rules monitoring events")
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

    async def evaluate_rules(self, event: RiskEvent) -> list[dict[str, Any]]:
        """Evaluate all rules against an event.

        Returns:
            List of violations detected by rules. Empty list if no violations.
        """
        # Checkpoint 6: Event received
        sdk_logger.info(f"📨 Event received: {event.event_type.value} - evaluating {len(self.rules)} rules")

        violations = []
        for rule in self.rules:
            try:
                violation = await rule.evaluate(event, self)

                # Checkpoint 7: Rule evaluated
                sdk_logger.info(f"🔍 Rule evaluated: {rule.__class__.__name__} - {'VIOLATED' if violation else 'PASSED'}")

                if violation:
                    await self._handle_violation(rule, violation)
                    violations.append(violation)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.__class__.__name__}: {e}")

        return violations

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
            # Checkpoint 8: Enforcement triggered (flatten)
            sdk_logger.warning(f"⚠️ Enforcement triggered: FLATTEN ALL - Rule: {rule.__class__.__name__}")
            await self.flatten_all_positions()
        elif action == "close_position":
            # Checkpoint 8: Enforcement triggered (close position)
            sdk_logger.warning(f"⚠️ Enforcement triggered: CLOSE POSITION - Rule: {rule.__class__.__name__}")
            contract_id = violation.get("contractId")
            symbol = violation.get("symbol")
            await self.close_position(contract_id, symbol)
        elif action == "pause":
            # Checkpoint 8: Enforcement triggered (pause)
            sdk_logger.warning(f"⚠️ Enforcement triggered: PAUSE TRADING - Rule: {rule.__class__.__name__}")
            await self.pause_trading()
        elif action == "alert":
            # Checkpoint 8: Enforcement triggered (alert)
            sdk_logger.info(f"⚠️ Enforcement triggered: ALERT - Rule: {rule.__class__.__name__}")
            await self.send_alert(violation)

    async def close_position(self, contract_id: str, symbol: str) -> None:
        """Close a specific position."""
        logger.warning(f"CLOSING POSITION: {symbol} ({contract_id})")

        await self.event_bus.publish(
            RiskEvent(
                event_type=EventType.ENFORCEMENT_ACTION,
                data={
                    "action": "close_position",
                    "symbol": symbol,
                    "contractId": contract_id,
                    "reason": "risk_rule_violation",
                },
                severity="warning",
            )
        )

        # Execute enforcement via TradingIntegration
        if self.trading_integration:
            try:
                await self.trading_integration.flatten_position(contract_id)
                logger.success(f"✅ Position closed: {symbol} ({contract_id})")
            except Exception as e:
                logger.error(f"❌ Failed to close position {symbol}: {e}")
        else:
            logger.warning("⚠️ TradingIntegration not connected - enforcement not executed")

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

        # Execute enforcement via TradingIntegration
        if self.trading_integration:
            try:
                await self.trading_integration.flatten_all()
                logger.success("✅ All positions flattened via SDK")
            except Exception as e:
                logger.error(f"❌ Failed to flatten positions: {e}")
        else:
            logger.warning("⚠️ TradingIntegration not connected - enforcement not executed")

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
