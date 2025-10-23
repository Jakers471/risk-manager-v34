"""
SDK Integration Layer

This module wraps the Project-X SDK and provides a clean interface
for the risk manager to interact with trading operations.

Components:
- SuiteManager: TradingSuite lifecycle management
- EnforcementExecutor: SDK-powered enforcement actions
- EventBridge: Bridge SDK events to risk engine
"""

from risk_manager.sdk.enforcement import EnforcementExecutor
from risk_manager.sdk.event_bridge import EventBridge
from risk_manager.sdk.suite_manager import SuiteManager

__all__ = [
    "SuiteManager",
    "EnforcementExecutor",
    "EventBridge",
]
