"""Event system for risk management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of risk events."""

    # Position events
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"

    # Order events
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"

    # Risk events
    RULE_VIOLATED = "rule_violated"
    RULE_WARNING = "rule_warning"
    ENFORCEMENT_ACTION = "enforcement_action"

    # P&L events
    PNL_UPDATED = "pnl_updated"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    DRAWDOWN_ALERT = "drawdown_alert"

    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"

    # AI events
    PATTERN_DETECTED = "pattern_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    AI_ALERT = "ai_alert"


@dataclass
class RiskEvent:
    """Risk management event."""

    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)
    source: str = "risk_manager"
    severity: str = "info"  # info, warning, error, critical

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "source": self.source,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RiskEvent":
        """Create event from dictionary."""
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data", {}),
            source=data.get("source", "risk_manager"),
            severity=data.get("severity", "info"),
        )


class EventBus:
    """Simple event bus for distributing events."""

    def __init__(self):
        self._handlers: dict[EventType, list] = {}

    def subscribe(self, event_type: EventType, handler) -> None:
        """Subscribe to event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler) -> None:
        """Unsubscribe from event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: RiskEvent) -> None:
        """Publish event to all subscribers."""
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)


import asyncio
