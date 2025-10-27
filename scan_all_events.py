#!/usr/bin/env python3
"""
Complete Event Type Scanner
===========================

Purpose: Subscribe to ALL event types and capture their data structures.

This will show us:
- What events exist
- When they fire
- What data they contain
- Complete field names and values

Run this, place various trades/orders, and see EVERYTHING the SDK sends!
"""

import asyncio
import os
import json
from datetime import datetime
from collections import defaultdict

# Set credentials BEFORE importing SDK
os.environ["PROJECT_X_API_KEY"] = "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
os.environ["PROJECT_X_USERNAME"] = "jakertrader"
os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRAC-V2-126244-84184528"

from project_x_py import TradingSuite, EventType

# Track event statistics
event_counts = defaultdict(int)
event_samples = {}  # Store one sample of each event type

def format_timestamp():
    """Get formatted timestamp"""
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]

def format_value(value, indent=0):
    """Recursively format any value for display"""
    prefix = "  " * indent

    if value is None:
        return "None"
    elif isinstance(value, (str, int, float, bool)):
        return str(value)
    elif isinstance(value, dict):
        lines = ["{"]
        for key, val in value.items():
            formatted_val = format_value(val, indent + 1)
            lines.append(f"{prefix}  '{key}': {formatted_val},")
        lines.append(f"{prefix}}}")
        return "\n".join(lines)
    elif isinstance(value, list):
        if not value:
            return "[]"
        lines = ["["]
        for item in value:
            formatted_item = format_value(item, indent + 1)
            lines.append(f"{prefix}  {formatted_item},")
        lines.append(f"{prefix}]")
        return "\n".join(lines)
    elif hasattr(value, '__dict__'):
        # Object - convert to dict
        return format_value(vars(value), indent)
    else:
        return str(value)

def create_event_handler(event_type_name):
    """Create a handler for a specific event type"""

    async def handler(event):
        """Generic event handler"""
        timestamp = format_timestamp()
        event_counts[event_type_name] += 1
        count = event_counts[event_type_name]

        # Extract data
        data = event.data if hasattr(event, 'data') else None
        event_time = event.timestamp if hasattr(event, 'timestamp') else None
        source = event.source if hasattr(event, 'source') else None

        # Store sample if first occurrence
        if event_type_name not in event_samples:
            event_samples[event_type_name] = {
                'data': data,
                'timestamp': event_time,
                'source': source,
            }

        # Print event
        print("\n" + "=" * 100)
        print(f"[{timestamp}] 🔔 EVENT #{count}: {event_type_name}")
        print("=" * 100)

        if event_time:
            print(f"Event Timestamp: {event_time}")
        if source:
            print(f"Event Source: {source}")

        print("\nEVENT DATA:")
        print("-" * 100)

        if data is None:
            print("  (No data)")
        elif isinstance(data, dict):
            for key, value in data.items():
                formatted_value = format_value(value, indent=1)
                print(f"  {key}: {formatted_value}")
        elif hasattr(data, '__dict__'):
            # Object - show attributes
            for key, value in vars(data).items():
                formatted_value = format_value(value, indent=1)
                print(f"  {key}: {formatted_value}")
        else:
            print(f"  {format_value(data)}")

        print("-" * 100)
        print()

    return handler

async def main():
    print("=" * 100)
    print("COMPLETE EVENT TYPE SCANNER")
    print("=" * 100)
    print()
    print("This script subscribes to ALL event types and shows their data.")
    print()
    print("Legend:")
    print("  🔔 = Event fired")
    print("  📊 = Statistics summary")
    print()
    print("=" * 100)
    print()

    # Connect to SDK
    print("[Connecting to SDK...]")
    try:
        suite = await TradingSuite.create(
            instrument="MNQ",
            timeframes=["1min"],
            initial_days=1
        )

        account = suite.client.account_info
        print(f"[✓] SDK Connected")
        print(f"    Account: {account.name}")
        print(f"    Balance: ${account.balance:,.2f}")
        print()
    except Exception as e:
        print(f"[✗] Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Get all EventType values
    print("[Discovering all event types...]")
    all_event_types = [attr for attr in dir(EventType) if not attr.startswith('_') and attr.isupper()]
    print(f"[✓] Found {len(all_event_types)} event types")
    print()

    # Subscribe to ALL events
    print("[Subscribing to ALL event types...]")
    print()

    subscribed_count = 0
    failed_subscriptions = []

    for event_type_name in sorted(all_event_types):
        try:
            event_type = getattr(EventType, event_type_name)
            handler = create_event_handler(event_type_name)
            await suite.on(event_type, handler)
            subscribed_count += 1
            print(f"  ✓ {event_type_name}")
        except Exception as e:
            failed_subscriptions.append((event_type_name, str(e)))
            print(f"  ✗ {event_type_name}: {e}")

    print()
    print(f"[✓] Subscribed to {subscribed_count}/{len(all_event_types)} event types")

    if failed_subscriptions:
        print()
        print(f"[!] Failed subscriptions ({len(failed_subscriptions)}):")
        for name, error in failed_subscriptions:
            print(f"    - {name}: {error}")

    print()
    print("=" * 100)
    print("LISTENING FOR EVENTS...")
    print("=" * 100)
    print()
    print("Instructions:")
    print("  1. Place trades through your trading platform")
    print("  2. Open/close positions")
    print("  3. Place different order types (MARKET, LIMIT, STOP)")
    print("  4. Modify orders")
    print("  5. Let quotes stream")
    print()
    print("Press Ctrl+C to stop and see statistics")
    print()
    print("=" * 100)
    print()

    # Wait for initial events
    await asyncio.sleep(3)

    # Wait forever for events
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n\n[Stopping scanner...]")
        print()

    # Print statistics
    print()
    print("=" * 100)
    print("📊 EVENT STATISTICS")
    print("=" * 100)
    print()

    if not event_counts:
        print("⚠️  No events received!")
        print()
        print("Try:")
        print("  - Place a trade")
        print("  - Open/close positions")
        print("  - Wait a few seconds for quotes")
        print()
    else:
        # Sort by count
        sorted_events = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)

        print("Event Type                          | Count")
        print("-" * 100)

        for event_name, count in sorted_events:
            print(f"{event_name:35} | {count:,}")

        print("-" * 100)
        print(f"{'TOTAL':35} | {sum(event_counts.values()):,}")
        print()

        # Show unique event types seen
        print(f"Unique event types triggered: {len(event_counts)}/{len(all_event_types)}")
        print()

        # Show which events were never triggered
        never_triggered = set(all_event_types) - set(event_counts.keys())
        if never_triggered:
            print(f"Event types NOT triggered ({len(never_triggered)}):")
            for event_name in sorted(never_triggered):
                print(f"  - {event_name}")
            print()

    # Save samples to file
    print("[Saving event samples to file...]")

    samples_file = "event_samples.json"

    # Convert samples to JSON-serializable format
    json_samples = {}
    for event_name, sample_data in event_samples.items():
        json_samples[event_name] = {
            'count': event_counts[event_name],
            'data': str(sample_data['data']),  # Convert to string for JSON
            'timestamp': str(sample_data['timestamp']) if sample_data['timestamp'] else None,
            'source': sample_data['source'],
        }

    with open(samples_file, 'w') as f:
        json.dump(json_samples, f, indent=2)

    print(f"[✓] Saved event samples to: {samples_file}")
    print()

    # Cleanup
    print("[Disconnecting...]")
    await suite.disconnect()
    print("[✓] SDK Disconnected")
    print()
    print("=" * 100)
    print("SCAN COMPLETE")
    print("=" * 100)
    print()
    print(f"Results saved to: {samples_file}")
    print("Review the file to see all event data structures!")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Scan interrupted by user]")
    except Exception as e:
        print(f"\n[✗] Scan failed: {e}")
        import traceback
        traceback.print_exc()
