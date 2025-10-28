"""
Checkpoint logging utilities for 8-checkpoint visibility system.

This module provides convenient wrappers for logging each of the 8 strategic checkpoints
in the Risk Manager lifecycle:

1. 🚀 Service Start - System initialization
2. ✅ Config Loaded - Configuration loaded and validated
3. ✅ SDK Connected - Trading SDK connected
4. ✅ Rules Initialized - Risk rules loaded and ready
5. ✅ Event Loop Running - Event processing started
6. 📨 Event Received - Real-time event captured
7. 🔍 Rule Evaluated - Rule check completed
8. ⚠️ Enforcement Triggered - Action taken on violation
"""

from typing import Any

from risk_manager.cli.logger import log_checkpoint


def checkpoint_service_start(details: dict[str, Any] | None = None) -> None:
    """
    Log Checkpoint 1: Service Start.

    Called when the Risk Manager service initializes.

    Args:
        details: Optional details (e.g., version, config path)

    Example:
        >>> checkpoint_service_start({"version": "1.0.0"})
    """
    log_checkpoint(1, "Service Start", details=details)


def checkpoint_config_loaded(
    rules_count: int | None = None,
    instruments: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Log Checkpoint 2: Config Loaded.

    Called after configuration is loaded and validated.

    Args:
        rules_count: Number of rules configured
        instruments: List of instruments being monitored
        details: Additional details

    Example:
        >>> checkpoint_config_loaded(rules_count=13, instruments=["MNQ", "ES"])
    """
    checkpoint_details = details or {}
    if rules_count is not None:
        checkpoint_details["rules"] = rules_count
    if instruments:
        checkpoint_details["instruments"] = ", ".join(instruments)

    log_checkpoint(2, "Config Loaded", details=checkpoint_details)


def checkpoint_sdk_connected(
    instruments: list[str] | None = None,
    account_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Log Checkpoint 3: SDK Connected.

    Called after successful SDK connection and authentication.

    Args:
        instruments: Instruments connected to
        account_id: Account ID connected
        details: Additional details

    Example:
        >>> checkpoint_sdk_connected(instruments=["MNQ"], account_id="ACC123")
    """
    checkpoint_details = details or {}
    if instruments:
        checkpoint_details["instruments"] = ", ".join(instruments)
    if account_id:
        checkpoint_details["account_id"] = account_id

    log_checkpoint(3, "SDK Connected", details=checkpoint_details)


def checkpoint_rules_initialized(
    rules: list[str] | None = None,
    rules_count: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Log Checkpoint 4: Rules Initialized.

    Called after risk rules are loaded and initialized.

    Args:
        rules: List of rule names
        rules_count: Number of rules loaded
        details: Additional details

    Example:
        >>> checkpoint_rules_initialized(rules=["DailyLossRule", "MaxPositionRule"])
    """
    checkpoint_details = details or {}
    if rules:
        checkpoint_details["rules"] = ", ".join(rules)
    if rules_count is not None:
        checkpoint_details["count"] = rules_count

    log_checkpoint(4, "Rules Initialized", details=checkpoint_details)


def checkpoint_event_loop_running(
    rules_count: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Log Checkpoint 5: Event Loop Running.

    Called when the event processing loop starts.

    Args:
        rules_count: Number of active rules
        details: Additional details

    Example:
        >>> checkpoint_event_loop_running(rules_count=13)
    """
    checkpoint_details = details or {}
    if rules_count is not None:
        checkpoint_details["active_rules"] = rules_count

    log_checkpoint(5, "Event Loop Running", details=checkpoint_details)


def checkpoint_event_received(
    event_type: str,
    symbol: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Log Checkpoint 6: Event Received.

    Called when a real-time event is received from SDK.

    Args:
        event_type: Type of event received
        symbol: Symbol related to event (if applicable)
        details: Additional details (qty, price, etc.)

    Example:
        >>> checkpoint_event_received("position_opened", symbol="MNQ", details={"qty": 2})
    """
    checkpoint_details = details or {}
    checkpoint_details["type"] = event_type
    if symbol:
        checkpoint_details["symbol"] = symbol

    log_checkpoint(6, "Event Received", details=checkpoint_details)


def checkpoint_rule_evaluated(
    rule_name: str,
    passed: bool,
    current_value: Any = None,
    limit: Any = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Log Checkpoint 7: Rule Evaluated.

    Called after a rule is evaluated against an event.

    Args:
        rule_name: Name of the rule
        passed: Whether the rule passed (True) or violated (False)
        current_value: Current value checked
        limit: Limit value
        details: Additional details

    Example:
        >>> checkpoint_rule_evaluated("DailyLossRule", passed=False, current_value=-550, limit=-500)
    """
    checkpoint_details = details or {}
    checkpoint_details["rule"] = rule_name
    checkpoint_details["status"] = "PASSED" if passed else "VIOLATED"

    if current_value is not None:
        checkpoint_details["current"] = current_value
    if limit is not None:
        checkpoint_details["limit"] = limit

    level = "info" if passed else "warning"
    log_checkpoint(7, "Rule Evaluated", details=checkpoint_details, level=level)


def checkpoint_enforcement_triggered(
    action: str,
    rule_name: str,
    symbol: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Log Checkpoint 8: Enforcement Triggered.

    Called when a rule violation triggers an enforcement action.

    Args:
        action: Enforcement action (flatten, close_position, pause, alert)
        rule_name: Rule that triggered enforcement
        symbol: Symbol affected (if applicable)
        details: Additional details

    Example:
        >>> checkpoint_enforcement_triggered("flatten", "DailyLossRule", details={"loss": -550})
    """
    checkpoint_details = details or {}
    checkpoint_details["action"] = action.upper()
    checkpoint_details["rule"] = rule_name

    if symbol:
        checkpoint_details["symbol"] = symbol

    level = "warning" if action in ["alert", "pause"] else "error"
    log_checkpoint(8, "Enforcement Triggered", details=checkpoint_details, level=level)


# Convenience aliases
cp1 = checkpoint_service_start
cp2 = checkpoint_config_loaded
cp3 = checkpoint_sdk_connected
cp4 = checkpoint_rules_initialized
cp5 = checkpoint_event_loop_running
cp6 = checkpoint_event_received
cp7 = checkpoint_rule_evaluated
cp8 = checkpoint_enforcement_triggered
