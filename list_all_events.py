#!/usr/bin/env python3
"""
List All SDK Event Types
========================

Extracts ALL EventType enum values from the SDK and generates a reference.
NO live connection needed - just reads the SDK code.
"""

import os

# Set credentials (needed to import SDK)
os.environ["PROJECT_X_API_KEY"] = "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
os.environ["PROJECT_X_USERNAME"] = "jakertrader"
os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRAC-V2-126244-84184528"

from project_x_py import EventType

print("=" * 100)
print("ALL SDK EVENT TYPES")
print("=" * 100)
print()

# Get all EventType values
all_events = [attr for attr in dir(EventType) if not attr.startswith('_') and attr.isupper()]

print(f"Total EventType values found: {len(all_events)}")
print()
print("=" * 100)
print()

# Categorize by likely purpose (based on naming)
categories = {
    'Position Events': [],
    'Order Events': [],
    'Trade Events': [],
    'Quote/Market Data Events': [],
    'Account Events': [],
    'Connection Events': [],
    'Error Events': [],
    'Other Events': [],
}

for event_name in sorted(all_events):
    if 'POSITION' in event_name:
        categories['Position Events'].append(event_name)
    elif 'ORDER' in event_name:
        categories['Order Events'].append(event_name)
    elif 'TRADE' in event_name:
        categories['Trade Events'].append(event_name)
    elif any(word in event_name for word in ['QUOTE', 'BAR', 'DATA', 'TICK', 'MARKET']):
        categories['Quote/Market Data Events'].append(event_name)
    elif 'ACCOUNT' in event_name:
        categories['Account Events'].append(event_name)
    elif any(word in event_name for word in ['CONNECT', 'DISCONNECT', 'HEARTBEAT']):
        categories['Connection Events'].append(event_name)
    elif 'ERROR' in event_name or 'FAIL' in event_name:
        categories['Error Events'].append(event_name)
    else:
        categories['Other Events'].append(event_name)

# Print categorized
for category, events in categories.items():
    if events:
        print(f"{category} ({len(events)}):")
        print("-" * 100)
        for event in events:
            print(f"  EventType.{event}")
        print()

# Output to file
output_file = "ALL_EVENT_TYPES.txt"

with open(output_file, 'w') as f:
    f.write("=" * 100 + "\n")
    f.write("ALL SDK EVENT TYPES\n")
    f.write("=" * 100 + "\n\n")
    f.write(f"Total: {len(all_events)}\n\n")

    for category, events in categories.items():
        if events:
            f.write(f"{category} ({len(events)}):\n")
            f.write("-" * 100 + "\n")
            for event in events:
                f.write(f"  EventType.{event}\n")
            f.write("\n")

    f.write("=" * 100 + "\n")
    f.write("ALPHABETICAL LIST\n")
    f.write("=" * 100 + "\n\n")
    for event in sorted(all_events):
        f.write(f"EventType.{event}\n")

print(f"[✓] Saved complete list to: {output_file}")
print()
