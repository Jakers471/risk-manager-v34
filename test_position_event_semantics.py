#!/usr/bin/env python3
"""
Test Position Event Semantics
============================

Purpose: Determine EXACTLY when each position event fires:
- POSITION_OPENED: When?
- POSITION_UPDATED: When? (Does it fire for NEW positions?)
- POSITION_CLOSED: When?

This will answer: "Should all rules subscribe to all position events?"
"""

import asyncio
import os
from datetime import datetime

# Set credentials BEFORE importing SDK
os.environ["PROJECT_X_API_KEY"] = "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
os.environ["PROJECT_X_USERNAME"] = "jakertrader"
os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRAC-V2-126244-84184528"

from project_x_py import TradingSuite, EventType

# Event counters and logs
events_log = []

async def on_position_opened(event):
    """Track POSITION_OPENED events"""
    data = event.data if hasattr(event, 'data') else {}

    # Extract all available fields
    size = data.get('size', 'N/A')
    symbol = data.get('symbol', 'N/A')
    contract_id = data.get('contractId', 'N/A')
    pos_type = data.get('type', 'N/A')  # 1=LONG, 2=SHORT
    avg_price = data.get('averagePrice', 'N/A')
    unrealized_pnl = data.get('unrealizedPnL', 'N/A')

    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

    # Determine direction
    direction = "LONG" if pos_type == 1 else "SHORT" if pos_type == 2 else "UNKNOWN"

    msg = f"[{timestamp}] 🟢 OPENED  | Contract: {contract_id:20} | Size: {size:5} | Dir: {direction:5} | Entry: ${avg_price}"
    print(msg)
    print(f"               ALL DATA: {data}")
    events_log.append(('OPENED', symbol, size, timestamp))

async def on_position_updated(event):
    """Track POSITION_UPDATED events"""
    data = event.data if hasattr(event, 'data') else {}

    size = data.get('size', 'N/A')
    contract_id = data.get('contractId', 'N/A')
    pos_type = data.get('type', 'N/A')
    avg_price = data.get('averagePrice', 'N/A')
    unrealized_pnl = data.get('unrealizedPnL', 'N/A')

    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    direction = "LONG" if pos_type == 1 else "SHORT" if pos_type == 2 else "UNKNOWN"

    msg = f"[{timestamp}] 🔵 UPDATED | Contract: {contract_id:20} | Size: {size:5} | Dir: {direction:5} | Entry: ${avg_price}"
    print(msg)
    print(f"               ALL DATA: {data}")
    events_log.append(('UPDATED', contract_id, size, timestamp))

async def on_position_closed(event):
    """Track POSITION_CLOSED events"""
    data = event.data if hasattr(event, 'data') else {}

    size = data.get('size', 'N/A')
    contract_id = data.get('contractId', 'N/A')
    realized_pnl = data.get('realizedPnL', 'N/A')

    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    msg = f"[{timestamp}] 🔴 CLOSED  | Contract: {contract_id:20} | Size: {size:5} | Realized P&L: ${realized_pnl}"
    print(msg)
    print(f"               ALL DATA: {data}")
    events_log.append(('CLOSED', contract_id, size, timestamp))

async def on_order_placed(event):
    """Track order placement - THIS IS WHERE STOP ORDERS SHOW UP!"""
    data = event.data if hasattr(event, 'data') else {}

    # Check if data has 'order' object (common pattern)
    order = data.get('order', data)

    qty = order.get('size', 'N/A') if isinstance(order, dict) else getattr(order, 'size', 'N/A')
    contract_id = order.get('contractId', 'N/A') if isinstance(order, dict) else getattr(order, 'contractId', 'N/A')
    side = order.get('side', 'N/A') if isinstance(order, dict) else getattr(order, 'side', 'N/A')
    order_type = order.get('type', 'N/A') if isinstance(order, dict) else getattr(order, 'type', 'N/A')
    limit_price = order.get('limitPrice', 'N/A') if isinstance(order, dict) else getattr(order, 'limitPrice', 'N/A')
    stop_price = order.get('stopPrice', 'N/A') if isinstance(order, dict) else getattr(order, 'stopPrice', 'N/A')
    order_id = order.get('id', 'N/A') if isinstance(order, dict) else getattr(order, 'id', 'N/A')

    # Decode side: 1=BUY, 2=SELL, 0=UNKNOWN
    side_str = "BUY" if side == 1 else "SELL" if side == 2 else f"UNKNOWN({side})"

    # Decode order type: 1=MARKET, 2=LIMIT, 3=STOP, 4=STOP_LIMIT
    type_str = {1: "MARKET", 2: "LIMIT", 3: "STOP", 4: "STOP_LIMIT"}.get(order_type, f"UNKNOWN({order_type})")

    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

    # Highlight STOP orders
    emoji = "🛑" if order_type in [3, 4] else "📝"

    msg = f"[{timestamp}] {emoji} PLACED  | Contract: {contract_id:20} | {side_str:4} {qty:5} | Type: {type_str:10} | Limit: ${limit_price} | Stop: ${stop_price} | ID: {order_id}"
    print(msg)
    print(f"               ALL DATA: {data}")
    print()

async def on_order_filled(event):
    """Track order fills (for correlation) - THIS SHOWS WHEN STOP LOSS TRIGGERS!"""
    data = event.data if hasattr(event, 'data') else {}

    # Check if data has 'order' object (common pattern)
    order = data.get('order', data)

    # Try multiple field names for quantity
    qty = None
    if isinstance(order, dict):
        qty = order.get('fillVolume') or order.get('quantity') or order.get('size') or 'N/A'
    else:
        qty = getattr(order, 'fillVolume', None) or getattr(order, 'quantity', None) or getattr(order, 'size', 'N/A')

    contract_id = order.get('contractId', 'N/A') if isinstance(order, dict) else getattr(order, 'contractId', 'N/A')
    side = order.get('side', 'N/A') if isinstance(order, dict) else getattr(order, 'side', 'N/A')
    order_type = order.get('type', 'N/A') if isinstance(order, dict) else getattr(order, 'type', 'N/A')
    price = order.get('filledPrice', 'N/A') if isinstance(order, dict) else getattr(order, 'filledPrice', 'N/A')
    stop_price = order.get('stopPrice', 'N/A') if isinstance(order, dict) else getattr(order, 'stopPrice', 'N/A')
    order_id = order.get('id', 'N/A') if isinstance(order, dict) else getattr(order, 'id', 'N/A')

    # Check old/new status to detect stop triggering
    old_status = data.get('old_status', 'N/A')
    new_status = data.get('new_status', 'N/A')

    # Decode side: 1=BUY, 2=SELL
    side_str = "BUY" if side == 1 else "SELL" if side == 2 else f"UNKNOWN({side})"

    # Decode order type: 1=MARKET, 2=LIMIT, 3=STOP, 4=STOP_LIMIT
    type_str = {1: "MARKET", 2: "LIMIT", 3: "STOP", 4: "STOP_LIMIT"}.get(order_type, f"UNKNOWN({order_type})")

    # Highlight if this might be a triggered stop order
    emoji = "🛑" if order_type in [3, 4] or (old_status == 6 and new_status == 2) else "📦"
    extra_note = " ← STOP LOSS TRIGGERED!" if order_type in [3, 4] or (old_status == 6 and new_status == 2) else ""

    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    msg = f"[{timestamp}] {emoji} FILLED  | Contract: {contract_id:20} | {side_str:4} {qty:5} | Type: {type_str:10} | Price: ${price} | Stop: ${stop_price} | ID: {order_id}{extra_note}"
    print(msg)
    print(f"               STATUS: {old_status} → {new_status} (6=PENDING_TRIGGER, 2=FILLED)")
    print(f"               ALL DATA: {data}")
    print()

async def main():
    print("=" * 70)
    print("Position Event Semantics Test")
    print("=" * 70)
    print()
    print("This test will place an order and observe which events fire:")
    print("  🟢 POSITION_OPENED  - New position?")
    print("  🔵 POSITION_UPDATED - Size change? Or also new?")
    print("  🔴 POSITION_CLOSED  - Flatten?")
    print("  📦 FILL            - Order execution")
    print()
    print("=" * 70)
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

    # Subscribe to ALL position events + order events
    print("[Subscribing to events...]")
    await suite.on(EventType.POSITION_OPENED, on_position_opened)
    await suite.on(EventType.POSITION_UPDATED, on_position_updated)
    await suite.on(EventType.POSITION_CLOSED, on_position_closed)
    await suite.on(EventType.ORDER_PLACED, on_order_placed)  # ← THIS IS WHERE STOP ORDERS SHOW UP!
    await suite.on(EventType.ORDER_FILLED, on_order_filled)
    await suite.on(EventType.ORDER_PARTIAL_FILL, on_order_filled)
    print("[✓] Subscribed to: POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED, ORDER_PLACED, ORDER_FILLED")
    print()
    print("    🛑 = STOP order placed (this is what you're looking for!)")
    print("    📝 = Regular order placed")
    print("    📦 = Order filled")
    print()

    # Wait for initial state
    print("[Waiting 2 seconds for initial position state...]")
    await asyncio.sleep(2)
    print()

    # Instructions for user
    print("=" * 70)
    print("MANUAL TESTING INSTRUCTIONS")
    print("=" * 70)
    print()
    print("Now YOU place trades manually and watch which events fire:")
    print()
    print("  TEST 1: OPEN NEW POSITION")
    print("    → Place BUY 1 MNQ market order")
    print("    → Watch for: 🟢 OPENED and/or 🔵 UPDATED")
    print()
    print("  TEST 2: INCREASE POSITION")
    print("    → Place BUY 1 more MNQ")
    print("    → Watch for: 🔵 UPDATED")
    print()
    print("  TEST 3: CLOSE POSITION")
    print("    → Place SELL 2 MNQ (flatten)")
    print("    → Watch for: 🔴 CLOSED and/or 🔵 UPDATED")
    print()
    print("=" * 70)
    print()
    print("⏳ LISTENING FOR EVENTS... (Press Ctrl+C to stop and see results)")
    print()
    print("=" * 70)
    print()

    # Wait forever for user to place trades
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n\n[Stopping test...]")
        print()

    # Analyze results
    print()
    print("=" * 70)
    print("RESULTS ANALYSIS")
    print("=" * 70)
    print()

    # Count events
    opened_count = len([e for e in events_log if e[0] == 'OPENED'])
    updated_count = len([e for e in events_log if e[0] == 'UPDATED'])
    closed_count = len([e for e in events_log if e[0] == 'CLOSED'])

    print(f"Total Events Received:")
    print(f"  🟢 POSITION_OPENED:  {opened_count}")
    print(f"  🔵 POSITION_UPDATED: {updated_count}")
    print(f"  🔴 POSITION_CLOSED:  {closed_count}")
    print()

    # Sequence analysis
    if events_log:
        print("Event Sequence:")
        for i, (event_type, symbol, size, timestamp) in enumerate(events_log, 1):
            print(f"  {i}. [{timestamp}] {event_type:10} | {symbol:10} | Size: {size}")
        print()

    # Key findings
    print("KEY FINDINGS:")
    print()

    if opened_count > 0 and updated_count > 0:
        print("✓ BOTH POSITION_OPENED and POSITION_UPDATED fired")
        print("  → Rules SHOULD subscribe to BOTH events to catch all position changes")
        print()
    elif updated_count > 0 and opened_count == 0:
        print("✓ Only POSITION_UPDATED fired (POSITION_OPENED did not)")
        print("  → POSITION_UPDATED fires for BOTH new AND updated positions")
        print("  → Rules can subscribe to just POSITION_UPDATED")
        print()
    elif opened_count > 0 and updated_count == 0:
        print("✓ Only POSITION_OPENED fired (POSITION_UPDATED did not)")
        print("  → Need to test if POSITION_UPDATED fires for size changes")
        print()
    else:
        print("⚠ No position events received - you didn't place any trades!")
        print()

    # Cleanup
    print()
    print("[Disconnecting...]")
    await suite.disconnect()
    print("[✓] SDK Disconnected")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Test interrupted by user]")
    except Exception as e:
        print(f"\n[✗] Test failed: {e}")
        import traceback
        traceback.print_exc()
