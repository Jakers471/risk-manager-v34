#!/usr/bin/env python3
"""
Quick test: Can we subscribe to quotes using suite.on()?
Purpose: Verify the correct pattern works for quote subscriptions
"""
import asyncio
import os
from datetime import datetime

# Set up environment
os.environ["PROJECT_X_API_KEY"] = "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
os.environ["PROJECT_X_USERNAME"] = "jakertrader"
os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRAC-V2-126244-84184528"

import logging
logging.basicConfig(level=logging.INFO)

from project_x_py import TradingSuite, EventType

# Track received quotes
quotes_received = []
max_quotes = 5  # Stop after 5 quotes


def timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


async def on_quote_update(event):
    """Handle quote updates"""
    quotes_received.append(event)

    print(f"\n[{timestamp()}] QUOTE UPDATE #{len(quotes_received)}")
    print(f"  Event Type: {event.event_type if hasattr(event, 'event_type') else 'N/A'}")

    # Try to extract quote data
    if hasattr(event, 'data'):
        data = event.data
        print(f"  Symbol: {data.get('symbol', 'N/A')}")
        print(f"  Last Price: ${data.get('last_price', 0):.2f}")
        print(f"  Bid: ${data.get('bid', 0):.2f}")
        print(f"  Ask: ${data.get('ask', 0):.2f}")
    elif hasattr(event, 'last_price'):
        # Direct event object
        print(f"  Last Price: ${event.last_price:.2f}")
        print(f"  Bid: ${getattr(event, 'best_bid', 0):.2f}")
        print(f"  Ask: ${getattr(event, 'best_ask', 0):.2f}")
    else:
        print(f"  Raw event: {event}")

    print("-" * 60)


async def main():
    print("=" * 60)
    print("  QUOTE SUBSCRIPTION TEST - Using suite.on()")
    print("=" * 60)
    print("")

    try:
        print("[1/4] Creating TradingSuite...")
        suite = await TradingSuite.create(
            instrument="MNQ",
            timeframes=["1min"],
            initial_days=1
        )
        print("  ✓ Suite created")

        account = suite.client.account_info
        print(f"  Account: {account.name}")
        print("")

        print("[2/4] Testing quote subscription with suite.on()...")

        # Test 1: Try QUOTE_UPDATE event type
        try:
            await suite.on(EventType.QUOTE_UPDATE, on_quote_update)
            print("  ✓ Subscribed to EventType.QUOTE_UPDATE")
        except AttributeError as e:
            print(f"  ✗ EventType.QUOTE_UPDATE not available: {e}")
            print(f"  Available EventTypes: {[e.name for e in EventType][:10]}")
        except Exception as e:
            print(f"  ✗ Subscription failed: {e}")

        print("")
        print("[3/4] Checking available EventTypes...")

        # List all available event types
        all_events = [e for e in EventType]
        print(f"  Total EventTypes: {len(all_events)}")

        # Filter for quote-related events
        quote_events = [e for e in EventType if 'quote' in e.name.lower()]
        print(f"  Quote-related events: {[e.name for e in quote_events]}")

        # Filter for market data events
        market_events = [e for e in EventType if any(x in e.name.lower() for x in ['market', 'data', 'tick', 'bar'])]
        print(f"  Market data events: {[e.name for e in market_events][:5]}")

        print("")
        print("[4/4] Waiting for quotes (10 seconds or 5 quotes)...")
        print("      Press Ctrl+C to stop early")
        print("")

        # Wait for quotes or timeout
        start_time = asyncio.get_event_loop().time()
        while True:
            await asyncio.sleep(0.1)

            # Check if we received enough quotes
            if len(quotes_received) >= max_quotes:
                print(f"\n✓ Received {len(quotes_received)} quotes!")
                break

            # Check timeout
            if asyncio.get_event_loop().time() - start_time > 10:
                print(f"\n⏱ Timeout after 10 seconds")
                print(f"   Received {len(quotes_received)} quotes")
                break

        print("")
        print("=" * 60)
        print("  TEST COMPLETE")
        print("=" * 60)
        print("")

        # Summary
        if len(quotes_received) > 0:
            print("✓ SUCCESS: Quote subscriptions work with suite.on()")
            print(f"  Received: {len(quotes_received)} quote updates")
            print("")
            print("CONCLUSION:")
            print("  - suite.on(EventType.QUOTE_UPDATE, callback) ✓ WORKS")
            print("  - Documentation should use this pattern")
        else:
            print("✗ NO QUOTES RECEIVED")
            print("  Possible reasons:")
            print("  1. EventType.QUOTE_UPDATE may not exist")
            print("  2. Quotes may use a different event type")
            print("  3. Market may be closed")
            print("  4. Subscription may need different setup")
            print("")
            print("RECOMMENDATION:")
            print("  - Check SDK documentation for correct quote event type")
            print("  - May need: suite.realtime.subscribe_quotes() instead")

        print("")

        # Disconnect
        await suite.disconnect()

    except KeyboardInterrupt:
        print("\n\n[STOPPED BY USER]")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
