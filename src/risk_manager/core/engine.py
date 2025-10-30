"""Core risk engine for evaluation and enforcement."""

import asyncio
from datetime import datetime
from typing import Any

from loguru import logger
from project_x_py.utils import ProjectXLogger

from risk_manager.config.models import RiskConfig
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
        # Checkpoint 6: Event received (simple text format)
        if len(self.rules) > 0:
            logger.info(f"📨 Event: {event.event_type.value} → evaluating {len(self.rules)} rules")
        else:
            logger.debug(f"📨 Event received: {event.event_type.value} - no rules configured")

        violations = []
        rule_results = []  # Track results for summary

        for rule in self.rules:
            try:
                violation = await rule.evaluate(event, self)

                # Get rule name (strip 'Rule' suffix for cleaner output)
                rule_name = rule.__class__.__name__.replace('Rule', '')

                # Checkpoint 7: Rule evaluated with context
                if violation:
                    # Extract context for logging
                    context = self._format_violation_context(violation)
                    logger.warning(f"❌ Rule: {rule_name} → FAIL{context}")
                    rule_results.append(("FAIL", rule_name, context))
                else:
                    # Get context for PASS (if available)
                    context = self._get_rule_pass_context(rule, event)
                    logger.info(f"✅ Rule: {rule_name} → PASS{context}")
                    rule_results.append(("PASS", rule_name, context))

                if violation:
                    await self._handle_violation(rule, violation)
                    violations.append(violation)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.__class__.__name__}: {e}")
                rule_results.append(("ERROR", rule.__class__.__name__, f" (error: {e})"))

        # Show P&L summary after rule evaluation (if we have P&L data)
        self._log_pnl_summary(event)

        return violations

    def _format_violation_context(self, violation: dict[str, Any]) -> str:
        """Format violation context for logging.

        Args:
            violation: Violation dictionary from rule evaluation

        Returns:
            Formatted context string (e.g., " (P&L: -$525.00 / -$500.00 limit)")
        """
        # Extract key violation data
        context_parts = []

        # Daily P&L violations (realized loss/profit)
        if "daily_loss" in violation or "current_loss" in violation:
            daily_pnl = violation.get("daily_loss") or violation.get("current_loss")
            limit = violation.get("limit")
            if daily_pnl is not None and limit is not None:
                context_parts.append(f"P&L: ${daily_pnl:,.2f} / ${limit:,.2f} limit")

        # Position violations
        if "symbol" in violation and "position" in violation:
            symbol = violation["symbol"]
            position = violation["position"]
            max_position = violation.get("max_position", violation.get("limit"))
            if max_position is not None:
                context_parts.append(f"{symbol}: {position}/{max_position} max")

        # Contract violations
        if "contracts" in violation and "limit" in violation:
            contracts = violation["contracts"]
            limit = violation["limit"]
            context_parts.append(f"contracts: {contracts}/{limit} max")

        # Unrealized P&L violations
        if "unrealized_pnl" in violation:
            unrealized_pnl = violation["unrealized_pnl"]
            limit = violation.get("limit")
            if limit is not None:
                context_parts.append(f"Unrealized: ${unrealized_pnl:,.2f} / ${limit:,.2f} limit")

        # Frequency violations
        if "trades_count" in violation:
            trades_count = violation["trades_count"]
            limit = violation.get("limit")
            window = violation.get("window", "")
            if limit is not None:
                context_parts.append(f"trades: {trades_count}/{limit} {window}")

        # Generic message fallback
        if not context_parts and "message" in violation:
            # Extract just the key part of the message
            msg = violation["message"]
            if len(msg) < 80:
                context_parts.append(msg)

        return f" ({', '.join(context_parts)})" if context_parts else ""

    def _get_rule_pass_context(self, rule: Any, event: RiskEvent) -> str:
        """Get context for rule PASS logging.

        Args:
            rule: The rule that passed
            event: The event being evaluated

        Returns:
            Formatted context string (e.g., " (P&L: +$125.00 / -$500.00 limit)")
        """
        rule_name = rule.__class__.__name__

        # DailyRealizedLoss - show current P&L vs limit
        if "DailyRealizedLoss" in rule_name:
            if hasattr(rule, "pnl_tracker") and hasattr(rule, "limit"):
                account_id = event.data.get("account_id")
                if account_id:
                    try:
                        daily_pnl = rule.pnl_tracker.get_daily_pnl(str(account_id))
                        return f" (P&L: ${daily_pnl:+,.2f} / ${rule.limit:,.2f} limit)"
                    except Exception:
                        pass

        # DailyRealizedProfit - show current P&L vs target
        if "DailyRealizedProfit" in rule_name:
            if hasattr(rule, "pnl_tracker") and hasattr(rule, "target"):
                account_id = event.data.get("account_id")
                if account_id:
                    try:
                        daily_pnl = rule.pnl_tracker.get_daily_pnl(str(account_id))
                        return f" (P&L: ${daily_pnl:+,.2f} / ${rule.target:,.2f} target)"
                    except Exception:
                        pass

        # MaxContractsPerInstrument - show position size
        if "MaxContractsPerInstrument" in rule_name:
            symbol = event.data.get("symbol")
            position = event.data.get("netPosition") or event.data.get("position")
            if symbol and position is not None:
                limit = rule.limits.get(symbol) if hasattr(rule, "limits") else None
                if limit is not None:
                    return f" ({symbol}: {abs(position)}/{limit} max)"

        # AuthLossGuard - show connection status
        if "AuthLossGuard" in rule_name:
            return " (connected)"

        # NoStopLossGrace - check if stop detected
        if "NoStopLossGrace" in rule_name:
            has_stop = event.data.get("has_stop_loss", False)
            if has_stop:
                return " (stop detected)"
            else:
                return " (no stop detected)"

        return ""

    def _log_pnl_summary(self, event: RiskEvent) -> None:
        """Log P&L summary after rule evaluation.

        Args:
            event: The event that was evaluated
        """
        # Only show P&L summary for P&L-related events
        if event.event_type not in [
            EventType.POSITION_CLOSED,
            EventType.PNL_UPDATED,
            EventType.TRADE_EXECUTED,
            EventType.POSITION_UPDATED,
        ]:
            return

        # Extract P&L data from event or engine state
        realized_pnl = event.data.get("realized_pnl", self.daily_pnl)
        unrealized_pnl = event.data.get("unrealized_pnl", 0.0)

        # Calculate unrealized from positions if available
        if unrealized_pnl == 0.0 and self.current_positions:
            unrealized_pnl = sum(
                pos.get("unrealizedPnl", 0.0)
                for pos in self.current_positions.values()
            )

        total_pnl = realized_pnl + unrealized_pnl

        # Only log if we have meaningful P&L data
        if realized_pnl != 0.0 or unrealized_pnl != 0.0:
            logger.info(
                f"💰 P&L Summary: "
                f"Realized ${realized_pnl:+,.2f} | "
                f"Unrealized ${unrealized_pnl:+,.2f} | "
                f"Total ${total_pnl:+,.2f}"
            )

    async def _handle_violation(self, rule: Any, violation: dict[str, Any]) -> None:
        """Handle a rule violation."""
        # Format violation for clear logging
        rule_name = rule.__class__.__name__.replace('Rule', '')
        message = violation.get("message", "No details provided")

        logger.critical(f"🚨 VIOLATION: {rule_name} - {message}")

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
        rule_name = rule.__class__.__name__.replace('Rule', '')

        if action == "flatten":
            # Checkpoint 8: Enforcement triggered (flatten)
            logger.critical(f"🛑 ENFORCING: Closing all positions ({rule_name})")
            sdk_logger.warning(f"⚠️ Enforcement triggered: FLATTEN ALL - Rule: {rule_name}")
            await self.flatten_all_positions()
        elif action == "close_position":
            # Checkpoint 8: Enforcement triggered (close position)
            contract_id = violation.get("contractId")
            symbol = violation.get("symbol")
            logger.critical(f"🛑 ENFORCING: Closing position {symbol} ({rule_name})")
            sdk_logger.warning(f"⚠️ Enforcement triggered: CLOSE POSITION - Rule: {rule_name}")
            await self.close_position(contract_id, symbol)
        elif action == "pause":
            # Checkpoint 8: Enforcement triggered (pause)
            logger.critical(f"🛑 ENFORCING: Pausing trading ({rule_name})")
            sdk_logger.warning(f"⚠️ Enforcement triggered: PAUSE TRADING - Rule: {rule_name}")
            await self.pause_trading()
        elif action == "alert":
            # Checkpoint 8: Enforcement triggered (alert)
            logger.warning(f"⚠️  ALERT: {message} ({rule_name})")
            sdk_logger.info(f"⚠️ Enforcement triggered: ALERT - Rule: {rule_name}")
            await self.send_alert(violation)

    async def close_position(self, contract_id: str, symbol: str) -> None:
        """Close a specific position."""
        logger.warning(f"Closing position: {symbol} ({contract_id})")

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
                logger.success(f"✅ Position closed: {symbol}")
            except Exception as e:
                logger.error(f"❌ Failed to close position {symbol}: {e}")
        else:
            logger.warning(f"⚠️  TradingIntegration not connected - enforcement not executed")

    async def flatten_all_positions(self) -> None:
        """Flatten all open positions."""
        logger.warning(f"Flattening all positions...")

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
                logger.success(f"✅ All positions flattened")
            except Exception as e:
                logger.error(f"❌ Failed to flatten positions: {e}")
        else:
            logger.warning(f"⚠️  TradingIntegration not connected - enforcement not executed")

    async def pause_trading(self) -> None:
        """Pause all trading activity."""
        logger.warning(f"Trading paused - awaiting manual intervention")

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
        message = violation.get("message", str(violation))
        logger.info(f"🔔 Alert: {message}")

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
