"""
Windows Service daemon for Risk Manager V34.

This package provides Windows Service implementation for running
the Risk Manager as a background service with LocalSystem privileges.
"""

from .runner import ServiceRunner
from .service import RiskManagerService

__all__ = [
    "RiskManagerService",
    "ServiceRunner",
]
