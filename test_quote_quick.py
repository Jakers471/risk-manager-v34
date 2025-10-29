"""Quick test: Does suite.on() support quotes?"""
import asyncio
import os
from datetime import datetime

os.environ["PROJECT_X_API_KEY"] = "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
os.environ["PROJECT_X_USERNAME"] = "jakertrader"
os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRAC-V2-126244-84184528"

import logging
logging.basicConfig(level=logging.INFO)

from project_x_py import TradingSuite, EventType

quotes_received = []

async def on_quote(event):
    """Quote callback - MUST be async!"""
    quotes_received.append(event)

    # Debug: Show what's in the event
    print(f"\n[QUOTE #{len(quotes_received)}]")
    print(f"  Type: {type(event)}")
    print(f"  Dir: {[x for x in dir(event) if not x.startswith('_')]}")

    # Try to extract data
    if hasattr(event, 'data'):
        print(f"  Data: {event.data}")
    if hasattr(event, 'event_type'):
        print(f"  Event Type: {event.event_type}")
    if hasattr(event, 'timestamp'):
        print(f"  Timestamp: {event.timestamp}")

    # Print all attributes
    for attr in dir(event):
        if not attr.startswith('_'):
            try:
                value = getattr(event, attr)
                if not callable(value):
                    print(f"  {attr}: {value}")
            except:
                pass

    print("-" * 60)

    # Stop after 3 quotes so we can read them
    if len(quotes_received) >= 3:
        return

async def main():
    print("\n" + "="*60)
    print("  TESTING: suite.on() with QUOTES")
    print("="*60 + "\n")

    suite = await TradingSuite.create(instrument="MNQ", timeframes=["1min"], initial_days=1)
    print(f"✓ Suite created for {suite.client.account_info.name}\n")

    # Check what quote-related EventTypes exist
    print("Available EventTypes with 'QUOTE' or 'TICK' or 'BAR':")
    quote_events = [e for e in EventType if any(x in e.name for x in ['QUOTE', 'TICK', 'BAR', 'DATA'])]
    for e in quote_events:
        print(f"  - EventType.{e.name}")

    print(f"\nFound {len(quote_events)} quote-related event types\n")

    if len(quote_events) > 0:
        # Try QUOTE_UPDATE first (fires most frequently)
        quote_update = next((e for e in quote_events if 'QUOTE_UPDATE' in e.name), quote_events[0])
        test_event = quote_update
        print(f"Testing subscription to: EventType.{test_event.name}")
        try:
            await suite.on(test_event, on_quote)
            print(f"✓ Successfully subscribed!\n")

            print("Waiting 10 seconds for quotes...")
            await asyncio.sleep(10)

            if len(quotes_received) > 0:
                print(f"\n✓ SUCCESS: Received {len(quotes_received)} quote events!")
                print(f"  First quote: {quotes_received[0]}")
                print(f"\n  CONCLUSION: suite.on(EventType.{test_event.name}, callback) WORKS!")
            else:
                print(f"\n⚠ No quotes received (market may be closed)")
                print(f"  But subscription worked - EventType.{test_event.name} is valid!")

        except Exception as e:
            print(f"✗ Subscription failed: {e}")
    else:
        print("✗ No quote-related EventTypes found")
        print("\nAll EventTypes:")
        for e in EventType:
            print(f"  - {e.name}")

    await suite.disconnect()
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
