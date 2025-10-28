"""
Events Sanity Check - Event System Flow Validation

NOTE: This is a MOCK sanity check since the real TopstepX SDK is not installed.
      In production, this would connect to real WebSocket and validate events.

This validates:
1. Event bus can receive events
2. Event handlers can be registered
3. Events can be published and consumed
4. Event data structure is correct
5. Multiple event types work correctly

Exit Codes:
0 = Events flowing (PASS)
1 = No events received (FAIL)
2 = Event format incorrect (FAIL)
3 = System error (FAIL)

Duration: ~3 seconds
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from risk_manager.core.events import EventBus, EventType, RiskEvent


class EventsSanityCheck:
    """
    Events sanity checker.

    This is a MOCK version that validates our event system works.
    In production with real SDK, this would test actual WebSocket events.
    """

    def __init__(self):
        self.event_bus = EventBus()
        self.events_received: list[dict[str, Any]] = []
        self.timeout_seconds = 3
        self.position_events = 0
        self.order_events = 0
        self.trade_events = 0
        self.running = False

    async def setup_event_bus(self) -> bool:
        """Setup event bus and handlers."""
        print("-" * 70)
        print("STEP 1: Setting Up Event Bus")
        print("-" * 70)

        try:
            print("Creating event bus...")
            self.event_bus = EventBus()
            print("OK Event bus created")

            # Register handlers for different event types
            print("\nRegistering event handlers...")

            async def position_handler(event: RiskEvent):
                """Handle position events."""
                self.position_events += 1
                event_data = {
                    "type": "position",
                    "data": event.data,
                    "timestamp": datetime.now(),
                }
                self.events_received.append(event_data)
                if len(self.events_received) <= 3:
                    print(f"  -> Event received: {event.event_type.value}")

            async def order_handler(event: RiskEvent):
                """Handle order events."""
                self.order_events += 1
                event_data = {
                    "type": "order",
                    "data": event.data,
                    "timestamp": datetime.now(),
                }
                self.events_received.append(event_data)
                if len(self.events_received) <= 3:
                    print(f"  -> Event received: {event.event_type.value}")

            async def trade_handler(event: RiskEvent):
                """Handle trade events."""
                self.trade_events += 1
                event_data = {
                    "type": "trade",
                    "data": event.data,
                    "timestamp": datetime.now(),
                }
                self.events_received.append(event_data)
                if len(self.events_received) <= 3:
                    print(f"  -> Event received: {event.event_type.value}")

            # Subscribe handlers
            self.event_bus.subscribe(EventType.POSITION_UPDATED, position_handler)
            print("  OK Subscribed to POSITION_UPDATED")

            self.event_bus.subscribe(EventType.ORDER_PLACED, order_handler)
            print("  OK Subscribed to ORDER_PLACED")

            self.event_bus.subscribe(EventType.ORDER_FILLED, order_handler)
            print("  OK Subscribed to ORDER_FILLED")

            self.event_bus.subscribe(EventType.TRADE_EXECUTED, trade_handler)
            print("  OK Subscribed to TRADE_EXECUTED")

            print("\nOK Event bus configured")
            return True

        except Exception as e:
            print(f"FAIL: Cannot setup event bus")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def simulate_events(self) -> bool:
        """Simulate events being received from SDK."""
        print("\n" + "-" * 70)
        print("STEP 2: Simulating Event Flow")
        print("-" * 70)

        try:
            print("\nPublishing test events...")
            print("(In production, these would come from TopstepX WebSocket)")

            # Simulate position update
            pos_event = RiskEvent(
                event_type=EventType.POSITION_UPDATED,
                data={
                    "account_id": "TEST-123",
                    "symbol": "MNQ",
                    "size": 2,
                    "average_price": 16500.0,
                    "unrealized_pnl": 125.0,
                },
                timestamp=datetime.now(),
            )
            await self.event_bus.publish(pos_event)
            await asyncio.sleep(0.1)

            # Simulate order placed
            order_event = RiskEvent(
                event_type=EventType.ORDER_PLACED,
                data={
                    "account_id": "TEST-123",
                    "symbol": "MNQ",
                    "order_id": "ORD-001",
                    "side": "buy",
                    "size": 1,
                    "price": 16550.0,
                },
                timestamp=datetime.now(),
            )
            await self.event_bus.publish(order_event)
            await asyncio.sleep(0.1)

            # Simulate order filled
            fill_event = RiskEvent(
                event_type=EventType.ORDER_FILLED,
                data={
                    "account_id": "TEST-123",
                    "symbol": "MNQ",
                    "order_id": "ORD-001",
                    "fill_price": 16550.0,
                    "fill_size": 1,
                },
                timestamp=datetime.now(),
            )
            await self.event_bus.publish(fill_event)
            await asyncio.sleep(0.1)

            # Simulate trade executed
            trade_event = RiskEvent(
                event_type=EventType.TRADE_EXECUTED,
                data={
                    "account_id": "TEST-123",
                    "symbol": "MNQ",
                    "trade_id": "TRD-001",
                    "price": 16550.0,
                    "size": 1,
                    "pnl": 50.0,
                },
                timestamp=datetime.now(),
            )
            await self.event_bus.publish(trade_event)
            await asyncio.sleep(0.1)

            # Give handlers time to process
            await asyncio.sleep(0.5)

            print(f"\nOK Published 4 test events")
            return True

        except Exception as e:
            print(f"FAIL: Error publishing events")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def validate_events_received(self) -> bool:
        """Validate events were received."""
        print("\n" + "-" * 70)
        print("STEP 3: Validating Events Received")
        print("-" * 70)

        if len(self.events_received) == 0:
            print("FAIL: No events received")
            print("\nPossible causes:")
            print("  - Event handlers not registered")
            print("  - Event bus not publishing")
            print("  - Handler exceptions")
            return False

        print(f"\nPASS: Received {len(self.events_received)} events")
        print(
            f"  Position events: {self.position_events}, "
            f"Order events: {self.order_events}, "
            f"Trade events: {self.trade_events}"
        )
        return True

    async def validate_event_format(self) -> bool:
        """Validate event data structure."""
        print("\n" + "-" * 70)
        print("STEP 4: Validating Event Format")
        print("-" * 70)

        if not self.events_received:
            print("SKIP: No events to validate")
            return True

        issues = []

        for i, event in enumerate(self.events_received, 1):
            print(f"\nEvent {i}:")

            # Check has event type
            if "type" not in event:
                issues.append(f"Event {i}: Missing event type")
                print(f"  FAIL Event type: MISSING")
            else:
                print(f"  OK Event type: {event['type']}")

            # Check has data
            if "data" not in event or not event["data"]:
                issues.append(f"Event {i}: Missing or empty data")
                print(f"  FAIL Event data: MISSING")
            else:
                data = event["data"]
                if isinstance(data, dict):
                    data_keys = list(data.keys())[:3]  # Show first 3 keys
                    print(
                        f"  OK Event data: {len(data)} fields ({', '.join(data_keys)}...)"
                    )
                else:
                    print(f"  FAIL Event data: Invalid type {type(data).__name__}")
                    issues.append(f"Event {i}: Data is not a dict")

            # Check has timestamp
            if "timestamp" not in event:
                issues.append(f"Event {i}: Missing timestamp")
                print(f"  FAIL Timestamp: MISSING")
            else:
                print(f"  OK Timestamp: {event['timestamp'].strftime('%H:%M:%S')}")

        if issues:
            print(f"\nFAIL: Event format issues detected:")
            for issue in issues:
                print(f"  - {issue}")
            return False

        print(f"\nPASS: All events have valid format")
        return True

    async def run(self) -> int:
        """
        Run complete events sanity check.

        Returns:
            0 = Events flowing (PASS)
            1 = No events received (FAIL)
            2 = Event format incorrect (FAIL)
            3 = System error (FAIL)
        """
        print("=" * 70)
        print(" " * 14 + "EVENTS SANITY CHECK (MOCK)")
        print("=" * 70)
        print()
        print("NOTE: This validates our event system using mock events.")
        print("      With real SDK installed, this would test actual WebSocket events.")
        print()

        try:
            # Step 1: Setup event bus
            if not await self.setup_event_bus():
                return 3  # System error

            # Step 2: Simulate events
            if not await self.simulate_events():
                return 3  # System error

            # Step 3: Validate events received
            if not await self.validate_events_received():
                return 1  # No events

            # Step 4: Validate format
            if not await self.validate_event_format():
                return 2  # Format error

            # All checks passed!
            print("\n" + "=" * 70)
            print(" " * 19 + "EVENTS SANITY PASSED")
            print("=" * 70)

            print(f"\nSummary:")
            print(f"  - Events received: {len(self.events_received)}")
            print(f"  - Position events: {self.position_events}")
            print(f"  - Order events: {self.order_events}")
            print(f"  - Trade events: {self.trade_events}")
            print(f"  - All events valid: YES")
            print()
            print("Next Step: Install real TopstepX SDK to test actual WebSocket events")

            return 0

        except Exception as e:
            print(f"\nUNEXPECTED ERROR: {e}")
            import traceback

            traceback.print_exc()
            return 3


async def main():
    """Main entry point."""
    checker = EventsSanityCheck()
    exit_code = await checker.run()
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
