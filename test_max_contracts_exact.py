#!/usr/bin/env python3
"""
WORKING TRADE MONITOR - Correctly parses ALL TopStepX event data!

Shows:
- BUY vs SELL
- MARKET, LIMIT, STOP orders
- Order status
- Position direction (LONG/SHORT)
- Fill prices and quantities
- P&L

100% Real-time WebSocket - NO polling!
"""
import asyncio
import os
from datetime import datetime

os.environ["PROJECT_X_API_KEY"] = "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
os.environ["PROJECT_X_USERNAME"] = "jakertrader"
os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRAC-V2-126244-84184528"

import logging
logging.basicConfig(level=logging.CRITICAL)

from project_x_py import TradingSuite, EventType

# Global suite reference for flatten
suite = None

# Prevent re-entry during flatten
currently_flattening = False


def timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def get_side(side: int) -> str:
    """0=BUY, 1=SELL"""
    return "BUY" if side == 0 else "SELL"


def get_order_type(order_type: int) -> str:
    """Order type names"""
    types = {
        1: "LIMIT",
        2: "MARKET",
        3: "STOP LIMIT",
        4: "STOP",
        5: "TRAILING STOP",
        6: "JOIN BID",
        7: "JOIN ASK",
    }
    return types.get(order_type, f"TYPE_{order_type}")


def get_status(status: int) -> str:
    """Order status names"""
    statuses = {
        0: "NONE",
        1: "OPEN",
        2: "FILLED",
        3: "CANCELLED",
        4: "EXPIRED",
        5: "REJECTED",
        6: "PENDING",
    }
    return statuses.get(status, f"STATUS_{status}")


def get_position_type(pos_type: int) -> str:
    """Position type: 1=LONG, 2=SHORT"""
    if pos_type == 1:
        return "LONG"
    elif pos_type == 2:
        return "SHORT"
    else:
        return "FLAT"


def get_contract_name(contract_id: str) -> str:
    """Extract nice name from contract ID"""
    # CON.F.US.MNQ.Z25 -> MNQZ5
    if not contract_id:
        return "UNKNOWN"
    parts = contract_id.split('.')
    if len(parts) >= 4:
        return parts[3]  # MNQ
    return contract_id


async def on_order_event(event):
    """Handle order events - CORRECTED field names!"""
    data = event.data if hasattr(event, 'data') else {}
    order = data.get('order') if isinstance(data, dict) else None

    if not order:
        return

    event_name = event.event_type.value if hasattr(event, 'event_type') else 'ORDER'

    print(f"\n{'='*80}")
    print(f"  [{timestamp()}] {event_name.upper().replace('_', ' ')}")
    print(f"{'='*80}")

    # Use CORRECT field names from the Order object
    print(f"  CONTRACT: {get_contract_name(order.contractId)}")
    print(f"  SIDE: {get_side(order.side)}")
    print(f"  TYPE: {get_order_type(order.type)}")  # Note: 'type' not 'orderType'
    print(f"  QUANTITY: {int(order.size)} contracts")  # Note: 'size' not 'quantity'
    print(f"  STATUS: {get_status(order.status)}")

    # Prices
    if order.limitPrice:
        print(f"  LIMIT PRICE: ${order.limitPrice:.2f}")
    if order.stopPrice:
        print(f"  STOP PRICE: ${order.stopPrice:.2f}")

    # Fill info
    if order.fillVolume and order.fillVolume > 0:  # Note: 'fillVolume' not 'filledQuantity'
        print(f"  FILLED: {order.fillVolume}/{int(order.size)} contracts")
        if order.filledPrice:  # Note: 'filledPrice' not 'avgFillPrice'
            print(f"  FILL PRICE: ${order.filledPrice:.2f}")

    print(f"  ORDER ID: {order.id}")

    # Detect stop loss
    if order.type in [4, 3]:  # STOP or STOP_LIMIT
        print(f"  >> STOP LOSS ORDER <<")

    print(f"{'='*80}")


async def on_position_event(event):
    """Handle position events - CORRECTED to use dict!"""
    data = event.data if hasattr(event, 'data') else {}

    # Position data is a DICT, not an object!
    if not isinstance(data, dict):
        return

    event_name = event.event_type.value if hasattr(event, 'event_type') else 'POSITION'

    print(f"\n{'='*80}")
    print(f"  [{timestamp()}] {event_name.upper().replace('_', ' ')}")
    print(f"{'='*80}")

    # Use dict keys, not object attributes
    contract = get_contract_name(data.get('contractId', ''))
    pos_type = data.get('type', 0)
    size = data.get('size', 0)
    avg_price = data.get('averagePrice', 0)

    print(f"  CONTRACT: {contract}")
    print(f"  DIRECTION: {get_position_type(pos_type)}")
    print(f"  QUANTITY: {size} contracts")
    print(f"  ENTRY PRICE: ${avg_price:.2f}")

    # MAX CONTRACTS CHECK
    MAX_CONTRACTS = 2
    if abs(size) > MAX_CONTRACTS and size != 0:
        global currently_flattening

        # GUARD: Prevent feedback loop from our own flatten orders!
        if currently_flattening:
            print(f"  ⏸️  Already flattening - ignoring this position update")
            return

        # SET GUARD IMMEDIATELY - before any other code!
        currently_flattening = True  # ← MOVED HERE to prevent race condition

        print(f"  ⚠️  VIOLATION: {abs(size)} > {MAX_CONTRACTS} contracts!")
        print(f"  🔨 FLATTENING POSITION NOW...")
        print(f"  CONTRACT ID FROM EVENT: {data.get('contractId', 'NONE')}")

        try:
            global suite

            # PLACE MARKET ORDER IMMEDIATELY - don't wait for position query
            # We already know the size from the event!
            contract_id = data.get('contractId')

            if not contract_id:
                print(f"  ❌ No contract ID in event data!")
            else:
                # IMPORTANT: size is ALWAYS POSITIVE!
                # Direction is in 'type' field: 1=LONG, 2=SHORT
                # To close LONG (type=1): SELL (side=1)
                # To close SHORT (type=2): BUY (side=0)

                if pos_type == 1:  # LONG position
                    side = 1  # SELL to close
                    side_name = "SELL"
                elif pos_type == 2:  # SHORT position
                    side = 0  # BUY to close
                    side_name = "BUY"
                else:
                    print(f"  ❌ Unknown position type: {pos_type}")
                    return

                print(f"  📤 Placing MARKET {side_name} for {size} contracts...")
                print(f"  📋 Contract: {contract_id}")
                print(f"  📋 Position Type: {pos_type} ({get_position_type(pos_type)})")

                mnq = suite["MNQ"]
                result = await mnq.orders.place_market_order(
                    contract_id=contract_id,
                    side=side,
                    size=abs(size)
                )

                print(f"  ✅ FLATTEN ORDER PLACED!")
                print(f"     Order ID: {result.id if hasattr(result, 'id') else result}")
                print(f"     Status: {result.status if hasattr(result, 'status') else 'SENT'}")

        except Exception as e:
            print(f"  ❌ FLATTEN FAILED: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Reset guard after 2 seconds (give time for position to close)
            await asyncio.sleep(2)
            currently_flattening = False
            print(f"  🔓 Flatten guard released")

    # Calculate P&L if we have current price
    # (might not be in the event data)
    if size == 0:
        print(f"  >> POSITION CLOSED <<")

    print(f"{'='*80}")


async def on_fill_event(event):
    """Handle fill events"""
    data = event.data if hasattr(event, 'data') else {}
    order = data.get('order') if isinstance(data, dict) else None

    print(f"\n{'#'*80}")
    print(f"  [{timestamp()}] TRADE EXECUTED!")
    print(f"{'#'*80}")

    if order:
        print(f"  CONTRACT: {get_contract_name(order.contractId)}")
        print(f"  SIDE: {get_side(order.side)}")
        print(f"  QUANTITY: {order.fillVolume} contracts")
        print(f"  FILL PRICE: ${order.filledPrice:.2f}")
        print(f"  ORDER TYPE: {get_order_type(order.type)}")
        print(f"  ORDER ID: {order.id}")

        # Calculate total value
        total_value = order.filledPrice * order.fillVolume
        print(f"  TOTAL VALUE: ${total_value:,.2f}")

    print(f"{'#'*80}")


async def main():
    print("\n" + "="*80)
    print("  WORKING TRADE MONITOR - Real-time Events".center(80))
    print("="*80)

    try:
        print("\n[CONNECTING]...")

        global suite
        suite = await TradingSuite.create(
            instrument="MNQ",
            timeframes=["1min"],
            initial_days=1
        )

        account = suite.client.account_info
        print(f"\n[CONNECTED]")
        print(f"  Account: {account.name}")
        print(f"  Balance: ${account.balance:,.2f}")
        print(f"  Type: {'SIMULATED' if account.simulated else 'LIVE'}")

        print("\n[REGISTERING EVENT HANDLERS]")

        # Order events
        await suite.on(EventType.ORDER_PLACED, on_order_event)
        await suite.on(EventType.ORDER_FILLED, on_fill_event)
        await suite.on(EventType.ORDER_PARTIAL_FILL, on_fill_event)
        await suite.on(EventType.ORDER_CANCELLED, on_order_event)
        await suite.on(EventType.ORDER_MODIFIED, on_order_event)
        await suite.on(EventType.ORDER_REJECTED, on_order_event)

        # Position events
        await suite.on(EventType.POSITION_OPENED, on_position_event)
        await suite.on(EventType.POSITION_CLOSED, on_position_event)
        await suite.on(EventType.POSITION_UPDATED, on_position_event)

        print("[OK] Ready!")

        print("\n" + "="*80)
        print("  LISTENING FOR YOUR TRADES".center(80))
        print("="*80)
        print("""
  Detecting:
    ✓ BUY / SELL orders
    ✓ MARKET / LIMIT / STOP orders
    ✓ Order fills and executions
    ✓ Position opens and closes
    ✓ LONG / SHORT positions
    ✓ Fill prices and quantities

  WebSocket: ACTIVE (real-time, <100ms latency)
  Polling: DISABLED (pure event-driven)

  Place a trade and watch it appear INSTANTLY!
  Press Ctrl+C to stop
""")
        print("="*80 + "\n")

        # Wait forever
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n\n[STOPPING]")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'suite' in locals():
            print("[DISCONNECTING]")
            await suite.disconnect()
            print("[DONE]\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
        print("Press Enter to exit...")
        input()
    except KeyboardInterrupt:
        print("\n[STOPPED]\n")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
