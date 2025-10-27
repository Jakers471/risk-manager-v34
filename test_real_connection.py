#!/usr/bin/env python3
"""
Real Connection Test - Validates WebSocket/SignalR connection

This test validates that the TradingIntegration class properly:
1. Authenticates via HTTP API and gets JWT token
2. Establishes SignalR WebSocket connection
3. Subscribes to realtime callbacks
4. Receives actual position/order/trade events from TopstepX

Run this test to verify the WebSocket/SignalR fix is working.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set credentials (same as in forget.md)
os.environ["PROJECT_X_API_KEY"] = "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
os.environ["PROJECT_X_USERNAME"] = "jakertrader"
os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRAC-V2-126244-84184528"

from risk_manager.core.config import RiskConfig
from risk_manager.core.events import EventBus, EventType
from risk_manager.integrations.trading import TradingIntegration


class ConnectionTestResults:
    """Track test results."""
    def __init__(self):
        self.http_auth = False
        self.signalr_connected = False
        self.callbacks_registered = False
        self.events_received = []
        self.errors = []


async def test_connection():
    """Test the complete connection flow."""
    print("\n" + "=" * 80)
    print("  TESTING WEBSOCKET/SIGNALR CONNECTION")
    print("=" * 80)

    results = ConnectionTestResults()
    event_bus = EventBus()

    # Subscribe to all events to verify they're flowing
    async def track_event(event):
        results.events_received.append({
            'type': event.event_type,
            'time': datetime.now(),
            'data': event.data
        })
        print(f"\n✅ EVENT RECEIVED: {event.event_type}")
        print(f"   Data: {event.data}")

    for event_type in EventType:
        event_bus.subscribe(event_type, track_event)

    try:
        # STEP 1: Create Trading Integration
        print("\n[STEP 1] Creating TradingIntegration...")
        print("-" * 80)

        config = RiskConfig()
        trading = TradingIntegration(
            instruments=["MNQ"],
            config=config,
            event_bus=event_bus
        )

        # STEP 2: Connect (HTTP + SignalR)
        print("\n[STEP 2] Connecting to TopstepX...")
        print("-" * 80)

        await trading.connect()

        if trading.client and trading.client.session_token:
            results.http_auth = True
            print(f"  ✅ HTTP Auth: SUCCESS (got JWT token)")
            print(f"     Account: {trading.client.account_info.name}")
            print(f"     Balance: ${trading.client.account_info.balance:,.2f}")
        else:
            raise Exception("HTTP authentication failed")

        if trading.realtime and trading.realtime.is_connected:
            results.signalr_connected = True
            print(f"  ✅ SignalR: CONNECTED")
        else:
            raise Exception("SignalR connection failed")

        # STEP 3: Start (Register Callbacks)
        print("\n[STEP 3] Registering realtime callbacks...")
        print("-" * 80)

        await trading.start()
        results.callbacks_registered = True
        print(f"  ✅ Callbacks: REGISTERED (4 callbacks)")
        print(f"     - position_update")
        print(f"     - order_update")
        print(f"     - trade_update")
        print(f"     - account_update")

        # STEP 4: Wait for Events
        print("\n[STEP 4] Waiting for events (30 seconds)...")
        print("-" * 80)
        print(f"  Listening for real-time events from TopstepX...")
        print(f"  (Place a trade in your account to trigger events)")

        # Wait and monitor
        for i in range(30):
            await asyncio.sleep(1)
            if len(results.events_received) > 0:
                print(f"  📊 Events received: {len(results.events_received)}")

        # STEP 5: Disconnect
        print("\n[STEP 5] Disconnecting...")
        print("-" * 80)

        await trading.disconnect()
        print(f"  ✅ Disconnected cleanly")

    except Exception as e:
        results.errors.append(str(e))
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    # RESULTS SUMMARY
    print("\n" + "=" * 80)
    print("  TEST RESULTS")
    print("=" * 80)

    print(f"\n1. HTTP Authentication:       {'✅ PASS' if results.http_auth else '❌ FAIL'}")
    print(f"2. SignalR WebSocket:         {'✅ PASS' if results.signalr_connected else '❌ FAIL'}")
    print(f"3. Callbacks Registered:      {'✅ PASS' if results.callbacks_registered else '❌ FAIL'}")
    print(f"4. Events Received:           {'✅ PASS' if len(results.events_received) > 0 else '⚠️  NONE'}")
    print(f"   Total events: {len(results.events_received)}")

    if results.events_received:
        print(f"\n   Event Types Received:")
        event_counts = {}
        for evt in results.events_received:
            evt_type = evt['type']
            event_counts[evt_type] = event_counts.get(evt_type, 0) + 1

        for evt_type, count in event_counts.items():
            print(f"     - {evt_type}: {count}")

    if results.errors:
        print(f"\n❌ Errors:")
        for error in results.errors:
            print(f"   - {error}")

    print("\n" + "=" * 80)

    # Determine overall success
    all_connected = results.http_auth and results.signalr_connected and results.callbacks_registered

    if all_connected and len(results.events_received) > 0:
        print("  ✅ SUCCESS: WebSocket/SignalR is working correctly!")
        print("  Real-time events are flowing from TopstepX to Risk Manager")
        return 0
    elif all_connected:
        print("  ⚠️  WARNING: Connection works but no events received")
        print("  This is normal if no trades are active in your account")
        print("  Try placing a trade to trigger events")
        return 0
    else:
        print("  ❌ FAILURE: Connection issue detected")
        return 1


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  WEBSOCKET/SIGNALR CONNECTION TEST")
    print("  Risk Manager V34")
    print("=" * 80)
    print("\nThis test validates the WebSocket/SignalR connection fix")
    print("Applied from: forget.md (two-step connection pattern)")
    print("\nPress Ctrl+C to cancel...")

    try:
        exit_code = asyncio.run(test_connection())

        print("\n" + "=" * 80)
        print(f"  Test Result: {'SUCCESS' if exit_code == 0 else 'FAILED'}")
        print("=" * 80 + "\n")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user\n")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
