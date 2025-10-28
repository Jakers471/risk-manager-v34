"""Display modes and formatting for Risk Manager CLI."""

from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger

from risk_manager.core.events import EventType, RiskEvent


class DisplayMode(str, Enum):
    """Display modes for CLI output."""

    LOG = "log"  # Streaming logs (default)
    DASHBOARD = "dashboard"  # Live dashboard (future)


class EventDisplay:
    """
    Display system for events, rule checks, and enforcement actions.

    Handles color-coded, formatted output for different event types.
    """

    # Color codes for different event types
    EVENT_COLORS = {
        # Position events - Cyan
        EventType.POSITION_OPENED: "cyan",
        EventType.POSITION_CLOSED: "cyan",
        EventType.POSITION_UPDATED: "cyan",
        # Order events - Yellow
        EventType.ORDER_PLACED: "yellow",
        EventType.ORDER_FILLED: "yellow",
        EventType.ORDER_CANCELLED: "yellow",
        EventType.ORDER_REJECTED: "yellow",
        EventType.ORDER_UPDATED: "yellow",
        # Trade events - Green
        EventType.TRADE_EXECUTED: "green",
        # Risk events - Red
        EventType.RULE_VIOLATED: "red",
        EventType.RULE_WARNING: "yellow",
        EventType.ENFORCEMENT_ACTION: "red",
        # P&L events - Magenta
        EventType.PNL_UPDATED: "magenta",
        EventType.DAILY_LOSS_LIMIT: "red",
        EventType.DRAWDOWN_ALERT: "yellow",
        # System events - Blue
        EventType.SYSTEM_STARTED: "blue",
        EventType.SYSTEM_STOPPED: "blue",
        EventType.CONNECTION_LOST: "red",
        EventType.CONNECTION_RESTORED: "green",
        EventType.SDK_CONNECTED: "green",
        EventType.SDK_DISCONNECTED: "red",
        EventType.AUTH_SUCCESS: "green",
        EventType.AUTH_FAILED: "red",
        # AI events - Purple
        EventType.PATTERN_DETECTED: "magenta",
        EventType.ANOMALY_DETECTED: "yellow",
        EventType.AI_ALERT: "yellow",
    }

    def __init__(self, mode: DisplayMode | str = DisplayMode.LOG):
        """
        Initialize display system.

        Args:
            mode: Display mode (log or dashboard)
        """
        if isinstance(mode, str):
            mode = DisplayMode(mode)
        self.mode = mode
        logger.info(f"Display mode: {mode.value}")

    def show_event(self, event: RiskEvent) -> None:
        """
        Display an event with appropriate formatting.

        Args:
            event: The risk event to display
        """
        if self.mode == DisplayMode.LOG:
            self._log_event(event)
        elif self.mode == DisplayMode.DASHBOARD:
            self._dashboard_event(event)

    def _log_event(self, event: RiskEvent) -> None:
        """Display event in log streaming mode."""
        color = self.EVENT_COLORS.get(event.event_type, "white")
        timestamp = event.timestamp.strftime("%H:%M:%S.%f")[:-3]

        # Build event message
        event_type = event.event_type.value.upper().replace("_", " ")
        msg_parts = [f"[{timestamp}]", f"<{color}>{event_type}</{color}>"]

        # Extract key data fields
        data = event.data
        if "symbol" in data:
            msg_parts.append(f"symbol=<bold>{data['symbol']}</bold>")
        if "quantity" in data:
            qty = data["quantity"]
            msg_parts.append(f"qty=<bold>{qty}</bold>")
        if "price" in data:
            price = data["price"]
            msg_parts.append(f"price=<bold>${price:.2f}</bold>")
        if "pnl" in data:
            pnl = data["pnl"]
            pnl_color = "green" if pnl >= 0 else "red"
            msg_parts.append(f"pnl=<{pnl_color}>${pnl:+.2f}</{pnl_color}>")
        if "realized_pnl" in data:
            pnl = data["realized_pnl"]
            pnl_color = "green" if pnl >= 0 else "red"
            msg_parts.append(f"realized_pnl=<{pnl_color}>${pnl:+.2f}</{pnl_color}>")
        if "unrealized_pnl" in data:
            pnl = data["unrealized_pnl"]
            pnl_color = "green" if pnl >= 0 else "red"
            msg_parts.append(f"unrealized_pnl=<{pnl_color}>${pnl:+.2f}</{pnl_color}>")

        # Add action for enforcement events
        if "action" in data:
            action = data["action"].upper()
            msg_parts.append(f"action=<bold red>{action}</bold red>")

        # Add rule for violation events
        if "rule" in data:
            rule = data["rule"]
            msg_parts.append(f"rule=<yellow>{rule}</yellow>")

        # Join and log
        msg = " | ".join(msg_parts)
        logger.opt(colors=True).info(msg)

    def _dashboard_event(self, event: RiskEvent) -> None:
        """Display event in dashboard mode (placeholder for future)."""
        # TODO: Implement live dashboard with Rich tables/panels
        # For now, fall back to log mode
        self._log_event(event)

    def show_rule_check(
        self,
        rule_name: str,
        passed: bool,
        current_value: Any = None,
        limit: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Display a rule evaluation result.

        Args:
            rule_name: Name of the rule
            passed: Whether the rule passed
            current_value: Current value being checked
            limit: Limit value for the rule
            details: Additional details to display
        """
        if self.mode == DisplayMode.LOG:
            self._log_rule_check(rule_name, passed, current_value, limit, details)
        elif self.mode == DisplayMode.DASHBOARD:
            self._dashboard_rule_check(rule_name, passed, current_value, limit, details)

    def _log_rule_check(
        self,
        rule_name: str,
        passed: bool,
        current_value: Any = None,
        limit: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Display rule check in log mode."""
        status_color = "green" if passed else "red"
        status_text = "PASS" if passed else "FAIL"
        icon = "✅" if passed else "❌"

        msg_parts = [
            f"{icon}",
            f"<cyan>{rule_name}</cyan>",
            f"<{status_color}>{status_text}</{status_color}>",
        ]

        # Add current value vs limit if provided
        if current_value is not None and limit is not None:
            if isinstance(current_value, float):
                msg_parts.append(f"current=<bold>{current_value:.2f}</bold>")
            else:
                msg_parts.append(f"current=<bold>{current_value}</bold>")

            if isinstance(limit, float):
                msg_parts.append(f"limit=<bold>{limit:.2f}</bold>")
            else:
                msg_parts.append(f"limit=<bold>{limit}</bold>")

        # Add additional details
        if details:
            for key, value in details.items():
                if isinstance(value, float):
                    msg_parts.append(f"{key}=<dim>{value:.2f}</dim>")
                else:
                    msg_parts.append(f"{key}=<dim>{value}</dim>")

        msg = " | ".join(msg_parts)
        log_func = logger.opt(colors=True).info if passed else logger.opt(colors=True).warning
        log_func(msg)

    def _dashboard_rule_check(
        self,
        rule_name: str,
        passed: bool,
        current_value: Any = None,
        limit: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Display rule check in dashboard mode (placeholder)."""
        # TODO: Implement dashboard view
        self._log_rule_check(rule_name, passed, current_value, limit, details)

    def show_enforcement(
        self,
        action: str,
        rule_name: str,
        symbol: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Display an enforcement action.

        Args:
            action: Enforcement action type
            rule_name: Rule that triggered enforcement
            symbol: Symbol affected (if applicable)
            details: Additional details
        """
        if self.mode == DisplayMode.LOG:
            self._log_enforcement(action, rule_name, symbol, details)
        elif self.mode == DisplayMode.DASHBOARD:
            self._dashboard_enforcement(action, rule_name, symbol, details)

    def _log_enforcement(
        self,
        action: str,
        rule_name: str,
        symbol: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Display enforcement action in log mode."""
        action_upper = action.upper()
        icon = "⚠️"

        # Different colors for different actions
        action_colors = {
            "FLATTEN": "red",
            "CLOSE_POSITION": "red",
            "PAUSE": "yellow",
            "ALERT": "yellow",
            "REJECT": "red",
        }
        action_color = action_colors.get(action_upper, "yellow")

        msg_parts = [
            f"{icon}",
            f"<{action_color}>ENFORCEMENT: {action_upper}</{action_color}>",
            f"rule=<cyan>{rule_name}</cyan>",
        ]

        if symbol:
            msg_parts.append(f"symbol=<bold>{symbol}</bold>")

        if details:
            for key, value in details.items():
                msg_parts.append(f"{key}=<dim>{value}</dim>")

        msg = " | ".join(msg_parts)
        logger.opt(colors=True).warning(msg)

    def _dashboard_enforcement(
        self,
        action: str,
        rule_name: str,
        symbol: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Display enforcement action in dashboard mode (placeholder)."""
        # TODO: Implement dashboard view
        self._log_enforcement(action, rule_name, symbol, details)

    def show_pnl_update(
        self,
        realized: float,
        unrealized: float,
        total: float,
        symbol: str | None = None,
    ) -> None:
        """
        Display P&L update.

        Args:
            realized: Realized P&L
            unrealized: Unrealized P&L
            total: Total P&L
            symbol: Symbol (if for specific position)
        """
        realized_color = "green" if realized >= 0 else "red"
        unrealized_color = "green" if unrealized >= 0 else "red"
        total_color = "green" if total >= 0 else "red"

        msg_parts = [
            "💰",
            "<magenta>P&L UPDATE</magenta>",
        ]

        if symbol:
            msg_parts.append(f"symbol=<bold>{symbol}</bold>")

        msg_parts.extend([
            f"realized=<{realized_color}>${realized:+.2f}</{realized_color}>",
            f"unrealized=<{unrealized_color}>${unrealized:+.2f}</{unrealized_color}>",
            f"total=<{total_color}>${total:+.2f}</{total_color}>",
        ])

        msg = " | ".join(msg_parts)
        logger.opt(colors=True).info(msg)

    def show_position_summary(self, positions: dict[str, Any]) -> None:
        """
        Display position summary.

        Args:
            positions: Dictionary of current positions
        """
        if not positions:
            logger.info("📊 No open positions")
            return

        logger.info(f"📊 Open Positions: {len(positions)}")
        for symbol, pos_data in positions.items():
            qty = pos_data.get("quantity", 0)
            avg_price = pos_data.get("avg_price", 0)
            unrealized = pos_data.get("unrealized_pnl", 0)

            pnl_color = "green" if unrealized >= 0 else "red"
            side = "LONG" if qty > 0 else "SHORT"
            side_color = "green" if qty > 0 else "red"

            msg = (
                f"  <bold>{symbol}</bold> | "
                f"<{side_color}>{side}</{side_color}> | "
                f"qty=<bold>{abs(qty)}</bold> | "
                f"avg=<dim>${avg_price:.2f}</dim> | "
                f"upnl=<{pnl_color}>${unrealized:+.2f}</{pnl_color}>"
            )
            logger.opt(colors=True).info(msg)

    def show_rules_status(self, rules: list[dict[str, Any]]) -> None:
        """
        Display rules status.

        Args:
            rules: List of rule status dictionaries
        """
        logger.info(f"📋 Active Rules: {len(rules)}")
        for rule_data in rules:
            name = rule_data.get("name", "Unknown")
            enabled = rule_data.get("enabled", False)
            action = rule_data.get("action", "unknown")

            status_icon = "✅" if enabled else "❌"
            status_color = "green" if enabled else "dim"

            msg = (
                f"  {status_icon} "
                f"<{status_color}>{name}</{status_color}> | "
                f"action=<dim>{action}</dim>"
            )
            logger.opt(colors=True).info(msg)

    def show_banner(self, title: str, subtitle: str | None = None) -> None:
        """
        Display a banner message.

        Args:
            title: Main title
            subtitle: Optional subtitle
        """
        border = "=" * 60
        logger.info(border)
        logger.info(f"  {title}")
        if subtitle:
            logger.info(f"  {subtitle}")
        logger.info(border)

    def show_startup_banner(self) -> None:
        """Display startup banner."""
        self.show_banner(
            "🛡️  Risk Manager V34",
            "Live Risk Monitoring & Enforcement"
        )

    def show_shutdown_banner(self) -> None:
        """Display shutdown banner."""
        self.show_banner("Risk Manager Stopped")
