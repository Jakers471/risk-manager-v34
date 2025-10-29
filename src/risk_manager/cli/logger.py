"""Logging setup and checkpoint utilities for Risk Manager CLI."""

import sys
from pathlib import Path
from typing import Any

from loguru import logger
from project_x_py.utils import ProjectXLogger

# Color codes for different log levels
COLORS = {
    "TRACE": "dim",
    "DEBUG": "cyan",
    "INFO": "white",
    "SUCCESS": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold red",
}

# Emoji checkpoint markers
CHECKPOINT_EMOJIS = {
    1: "🚀",  # Service Start
    2: "✅",  # Config Loaded
    3: "✅",  # SDK Connected
    4: "✅",  # Rules Initialized
    5: "✅",  # Event Loop Running
    6: "📨",  # Event Received
    7: "🔍",  # Rule Evaluated
    8: "⚠️",  # Enforcement Triggered
}

# Checkpoint descriptions
CHECKPOINT_NAMES = {
    1: "Service Start",
    2: "Config Loaded",
    3: "SDK Connected",
    4: "Rules Initialized",
    5: "Event Loop Running",
    6: "Event Received",
    7: "Rule Evaluated",
    8: "Enforcement Triggered",
}


def _filter_sdk_noise(record: dict) -> bool:
    """
    Filter out known SDK internal errors that don't affect functionality.

    The Project-X SDK has internal order tracking components that try to
    deserialize order data with a 'fills' field, but the Order model doesn't
    accept this parameter. This causes harmless error messages.

    Args:
        record: Log record to filter

    Returns:
        True to keep the log, False to suppress it
    """
    message = record.get("message", "")

    # Suppress SDK's Order.__init__() errors (harmless SDK internal issue)
    if "Failed to create Order object" in message:
        return False
    if "Order.__init__() got an unexpected keyword argument 'fills'" in message:
        return False

    # Keep all other logs
    return True


def setup_logging(
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    log_file: str | Path | None = None,
    colorize: bool = True,
) -> None:
    """
    Setup dual logging system (console + file).

    Args:
        console_level: Console log level (INFO, DEBUG, etc.)
        file_level: File log level (typically DEBUG for detailed logs)
        log_file: Path to log file (default: data/logs/risk_manager.log)
        colorize: Enable color output for console
    """
    # Remove default handler
    logger.remove()

    # Console handler - Human-readable, color-coded
    if colorize and sys.stdout.isatty():
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    else:
        console_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        )

    # Set encoding to UTF-8 for Windows console to support emojis
    import io
    if sys.platform == "win32":
        try:
            # Try to reconfigure stdout to use UTF-8
            sys.stdout.reconfigure(encoding='utf-8')
        except (AttributeError, io.UnsupportedOperation):
            # If reconfigure fails, wrap stdout with UTF-8 encoding
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )

    logger.add(
        sys.stdout,
        format=console_format,
        level=console_level.upper(),
        colorize=colorize,
        filter=_filter_sdk_noise,  # Suppress SDK internal errors
    )

    # File handler - Detailed, structured
    if log_file is None:
        log_file = Path("data/logs/risk_manager.log")

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "PID:{process} | "
        "{message}"
    )

    logger.add(
        log_path,
        format=file_format,
        level=file_level.upper(),
        rotation="1 day",
        retention="30 days",
        compression="zip",
        enqueue=True,  # Thread-safe logging
        filter=_filter_sdk_noise,  # Suppress SDK internal errors
    )

    logger.info(f"Logging initialized: console={console_level}, file={file_level}")
    logger.info(f"Log file: {log_path.absolute()}")


def log_checkpoint(
    checkpoint_num: int,
    message: str | None = None,
    details: dict[str, Any] | None = None,
    level: str = "info",
) -> None:
    """
    Log a checkpoint with emoji marker.

    Args:
        checkpoint_num: Checkpoint number (1-8)
        message: Optional custom message (defaults to checkpoint name)
        details: Optional details dictionary
        level: Log level (info, warning, error)

    Example:
        >>> log_checkpoint(1, "Service Start")
        🚀 [CHECKPOINT 1] Service Start

        >>> log_checkpoint(2, details={"rules": 13})
        ✅ [CHECKPOINT 2] Config Loaded | rules=13
    """
    if checkpoint_num not in CHECKPOINT_EMOJIS:
        logger.error(f"Invalid checkpoint number: {checkpoint_num}")
        return

    emoji = CHECKPOINT_EMOJIS[checkpoint_num]
    name = message or CHECKPOINT_NAMES.get(checkpoint_num, f"Checkpoint {checkpoint_num}")

    # Build log message
    log_msg = f"{emoji} [CHECKPOINT {checkpoint_num}] {name}"

    if details:
        detail_str = " | ".join(f"{k}={v}" for k, v in details.items())
        log_msg += f" | {detail_str}"

    # Log at appropriate level
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(log_msg)

    # Also log to SDK logger for consistency
    sdk_logger = ProjectXLogger.get_logger("risk_manager.checkpoints")
    sdk_log_func = getattr(sdk_logger, level.lower(), sdk_logger.info)
    sdk_log_func(log_msg)


def log_event_received(event_type: str, event_data: dict[str, Any] | None = None) -> None:
    """
    Log Checkpoint 6: Event Received.

    Args:
        event_type: Type of event received
        event_data: Optional event data to log
    """
    details = {"type": event_type}
    if event_data:
        # Add key event fields
        if "symbol" in event_data:
            details["symbol"] = event_data["symbol"]
        if "quantity" in event_data:
            details["qty"] = event_data["quantity"]
        if "price" in event_data:
            details["price"] = event_data["price"]

    log_checkpoint(6, "Event Received", details=details)


def log_rule_evaluated(rule_name: str, passed: bool, details: dict[str, Any] | None = None) -> None:
    """
    Log Checkpoint 7: Rule Evaluated.

    Args:
        rule_name: Name of the rule
        passed: Whether the rule passed (True) or violated (False)
        details: Optional details (current value, limit, etc.)
    """
    status = "PASSED" if passed else "VIOLATED"
    level = "info" if passed else "warning"

    eval_details = {"rule": rule_name, "status": status}
    if details:
        eval_details.update(details)

    log_checkpoint(7, "Rule Evaluated", details=eval_details, level=level)


def log_enforcement_triggered(action: str, rule_name: str, details: dict[str, Any] | None = None) -> None:
    """
    Log Checkpoint 8: Enforcement Triggered.

    Args:
        action: Enforcement action (flatten, close_position, pause, alert)
        rule_name: Name of the rule that triggered enforcement
        details: Optional details about the enforcement
    """
    enf_details = {"action": action.upper(), "rule": rule_name}
    if details:
        enf_details.update(details)

    level = "warning" if action in ["alert", "pause"] else "error"

    log_checkpoint(8, "Enforcement Triggered", details=enf_details, level=level)


def log_system_status(status: str, details: dict[str, Any] | None = None) -> None:
    """
    Log system status updates.

    Args:
        status: Status message
        details: Optional details dictionary
    """
    msg = f"[SYSTEM] {status}"
    if details:
        detail_str = " | ".join(f"{k}={v}" for k, v in details.items())
        msg += f" | {detail_str}"

    logger.info(msg)


def log_error(message: str, exc_info: bool = True) -> None:
    """
    Log an error with optional exception info.

    Args:
        message: Error message
        exc_info: Include exception traceback
    """
    if exc_info:
        logger.exception(f"❌ {message}")
    else:
        logger.error(f"❌ {message}")


def log_success(message: str) -> None:
    """Log a success message."""
    logger.success(f"✅ {message}")


def log_warning(message: str) -> None:
    """Log a warning message."""
    logger.warning(f"⚠️  {message}")


# Convenience function for quick checkpoint logging in other modules
def checkpoint(num: int, msg: str | None = None, **kwargs) -> None:
    """
    Shorthand for log_checkpoint.

    Example:
        >>> checkpoint(1)
        >>> checkpoint(2, rules=13)
        >>> checkpoint(3, symbols=["MNQ", "ES"])
    """
    log_checkpoint(num, msg, details=kwargs if kwargs else None)
