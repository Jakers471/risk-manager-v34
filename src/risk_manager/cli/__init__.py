"""
CLI Module for Risk Manager V34

Provides admin CLI for service control, configuration, and monitoring.
Also provides logging, display, and checkpoint tracking systems.
"""

from risk_manager.cli.admin import app
from risk_manager.cli.checkpoints import (
    checkpoint_config_loaded,
    checkpoint_enforcement_triggered,
    checkpoint_event_loop_running,
    checkpoint_event_received,
    checkpoint_rule_evaluated,
    checkpoint_rules_initialized,
    checkpoint_sdk_connected,
    checkpoint_service_start,
    cp1,
    cp2,
    cp3,
    cp4,
    cp5,
    cp6,
    cp7,
    cp8,
)
from risk_manager.cli.display import DisplayMode, EventDisplay
from risk_manager.cli.logger import (
    checkpoint,
    log_checkpoint,
    log_enforcement_triggered,
    log_error,
    log_event_received,
    log_rule_evaluated,
    log_success,
    log_system_status,
    log_warning,
    setup_logging,
)

__all__ = [
    # Admin CLI
    "app",
    # Logging
    "setup_logging",
    "log_checkpoint",
    "log_event_received",
    "log_rule_evaluated",
    "log_enforcement_triggered",
    "log_system_status",
    "log_success",
    "log_error",
    "log_warning",
    "checkpoint",
    # Display
    "EventDisplay",
    "DisplayMode",
    # Checkpoints
    "checkpoint_service_start",
    "checkpoint_config_loaded",
    "checkpoint_sdk_connected",
    "checkpoint_rules_initialized",
    "checkpoint_event_loop_running",
    "checkpoint_event_received",
    "checkpoint_rule_evaluated",
    "checkpoint_enforcement_triggered",
    "cp1",
    "cp2",
    "cp3",
    "cp4",
    "cp5",
    "cp6",
    "cp7",
    "cp8",
]
