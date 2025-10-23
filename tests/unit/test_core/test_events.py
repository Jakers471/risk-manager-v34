"""
Unit Tests for Event System

Tests the event bus and event types used throughout the system.
"""

import pytest
from risk_manager.core.events import EventBus, RiskEvent, EventType


class TestEventBus:
    """Tests for EventBus class."""

    def test_create_event_bus(self):
        """Test creating an event bus."""
        bus = EventBus()
        assert bus is not None

    def test_subscribe_to_event(self):
        """Test subscribing to events."""
        bus = EventBus()
        callback_called = False

        def callback(event):
            nonlocal callback_called
            callback_called = True

        bus.subscribe(EventType.POSITION_UPDATED, callback)
        bus.publish(RiskEvent(type=EventType.POSITION_UPDATED, data={}))

        assert callback_called is True

    def test_subscribe_multiple_callbacks(self):
        """Test multiple callbacks for same event."""
        bus = EventBus()
        callback_count = 0

        def callback1(event):
            nonlocal callback_count
            callback_count += 1

        def callback2(event):
            nonlocal callback_count
            callback_count += 1

        bus.subscribe(EventType.POSITION_UPDATED, callback1)
        bus.subscribe(EventType.POSITION_UPDATED, callback2)
        bus.publish(RiskEvent(type=EventType.POSITION_UPDATED, data={}))

        assert callback_count == 2

    def test_unsubscribe_from_event(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        callback_called = False

        def callback(event):
            nonlocal callback_called
            callback_called = True

        bus.subscribe(EventType.POSITION_UPDATED, callback)
        bus.unsubscribe(EventType.POSITION_UPDATED, callback)
        bus.publish(RiskEvent(type=EventType.POSITION_UPDATED, data={}))

        assert callback_called is False


class TestRiskEvent:
    """Tests for RiskEvent class."""

    def test_create_event(self):
        """Test creating a risk event."""
        event = RiskEvent(
            type=EventType.TRADE_EXECUTED,
            data={"symbol": "MNQ", "pnl": -12.50}
        )

        assert event.type == EventType.TRADE_EXECUTED
        assert event.data["symbol"] == "MNQ"
        assert event.data["pnl"] == -12.50

    def test_event_has_timestamp(self):
        """Test that events have timestamps."""
        event = RiskEvent(
            type=EventType.POSITION_UPDATED,
            data={}
        )

        assert event.timestamp is not None


class TestEventType:
    """Tests for EventType enum."""

    def test_event_types_exist(self):
        """Test that all required event types exist."""
        required_types = [
            EventType.POSITION_UPDATED,
            EventType.ORDER_UPDATED,
            EventType.TRADE_EXECUTED,
            EventType.RULE_VIOLATED,
            EventType.ENFORCEMENT_ACTION,
        ]

        for event_type in required_types:
            assert event_type is not None
