"""
Test SDK Queries - Explore SDK State Management

Query SDK directly to see what it returns for positions and orders.
Run this with an OPEN POSITION and ACTIVE STOPS to see what data is available.

Usage:
    1. Open a position with stop loss in your broker UI
    2. Run: python test_sdk_queries.py
    3. Review the output to see available fields

This will show:
    - All working orders with complete attribute lists
    - All positions with complete attribute lists
    - What fields link orders to positions
"""
import asyncio
import sys
from datetime import datetime

from loguru import logger
from project_x_py import TradingSuite


# Configure logger
logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")


async def query_sdk_state():
    """Query SDK state to explore available data."""

    logger.info("Connecting to TradingSuite...")
    suite = await TradingSuite.create(
        instruments=["MNQ"],
        timeframes=["1min"],
        features=["performance_analytics", "auto_reconnect"],
    )
    logger.success("✅ Connected to TradingSuite\n")

    # ========================================================================
    # WORKING ORDERS
    # ========================================================================
    logger.info("=" * 80)
    logger.info("📋 WORKING ORDERS (from order_manager.get_working_orders())")
    logger.info("=" * 80)

    try:
        orders = suite.order_manager.get_working_orders()
        logger.info(f"Found {len(orders)} working orders\n")

        if not orders:
            logger.warning("⚠️  No working orders found!")
            logger.warning("   Open a position with a stop loss in your broker, then run this again.\n")
        else:
            for i, order in enumerate(orders, 1):
                logger.info(f"\n📦 Order #{i}")
                logger.info(f"{'─' * 40}")
                logger.info(f"  Order ID: {order.id}")
                logger.info(f"  Contract: {order.contractId}")
                logger.info(f"  Type: {order.type} ({order.type_str})")
                logger.info(f"  Side: {order.side} ({'BUY' if order.side == 0 else 'SELL'})")
                logger.info(f"  Size: {order.size}")
                logger.info(f"  Stop Price: {order.stopPrice}")
                logger.info(f"  Limit Price: {order.limitPrice}")
                logger.info(f"  Status: {order.status}")
                logger.info(f"  Fill Volume: {order.fillVolume}")
                logger.info(f"  Filled Price: {order.filledPrice}")

                # Show ALL attributes
                logger.info(f"\n  🔍 All Attributes:")
                all_attrs = [a for a in dir(order) if not a.startswith('_')]
                logger.info(f"    {all_attrs}")

                # Check for linking fields
                logger.info(f"\n  🔗 Looking for linking fields:")
                for attr in ['position_id', 'positionId', 'parent_order_id', 'parentOrderId',
                            'bracket_id', 'bracketId', 'oco_id', 'ocoId']:
                    try:
                        if hasattr(order, attr):
                            val = getattr(order, attr)
                            logger.info(f"    ✅ {attr}: {val}")
                    except:
                        pass

                # Show all attribute values
                logger.info(f"\n  📊 All Attribute Values:")
                for attr in all_attrs:
                    try:
                        val = getattr(order, attr)
                        if not callable(val):
                            logger.info(f"    {attr}: {val} (type: {type(val).__name__})")
                    except Exception as e:
                        logger.debug(f"    {attr}: <error: {e}>")

    except Exception as e:
        logger.error(f"❌ Error getting working orders: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # ========================================================================
    # POSITIONS
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("📊 POSITIONS (from positions.get_all_positions())")
    logger.info("=" * 80)

    try:
        positions = await suite[0].positions.get_all_positions()
        logger.info(f"Found {len(positions)} positions\n")

        if not positions:
            logger.warning("⚠️  No open positions found!")
            logger.warning("   Open a position in your broker, then run this again.\n")
        else:
            for i, pos in enumerate(positions, 1):
                logger.info(f"\n📍 Position #{i}")
                logger.info(f"{'─' * 40}")
                logger.info(f"  Position ID: {pos.id}")
                logger.info(f"  Contract: {pos.contractId}")
                logger.info(f"  Size: {pos.size}")
                logger.info(f"  Type: {pos.type} (1=LONG, 2=SHORT, 0=FLAT)")
                logger.info(f"  Entry (Avg Price): {pos.averagePrice}")
                logger.info(f"  Unrealized P&L: {pos.unrealizedPnl}")

                # Show ALL attributes
                logger.info(f"\n  🔍 All Attributes:")
                all_attrs = [a for a in dir(pos) if not a.startswith('_')]
                logger.info(f"    {all_attrs}")

                # Check for protective order fields
                logger.info(f"\n  🛡️ Looking for protective order fields:")
                for attr in ['stopLoss', 'stop_loss', 'takeProfit', 'take_profit',
                            'protectiveOrders', 'protective_orders', 'orders']:
                    try:
                        if hasattr(pos, attr):
                            val = getattr(pos, attr)
                            logger.info(f"    ✅ {attr}: {val}")
                    except:
                        pass

                # Show all attribute values
                logger.info(f"\n  📊 All Attribute Values:")
                for attr in all_attrs:
                    try:
                        val = getattr(pos, attr)
                        if not callable(val):
                            logger.info(f"    {attr}: {val} (type: {type(val).__name__})")
                    except Exception as e:
                        logger.debug(f"    {attr}: <error: {e}>")

    except Exception as e:
        logger.error(f"❌ Error getting positions: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # ========================================================================
    # CORRELATION ANALYSIS
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("🔗 CORRELATION ANALYSIS")
    logger.info("=" * 80)

    try:
        orders = suite.order_manager.get_working_orders()
        positions = await suite[0].positions.get_all_positions()

        if orders and positions:
            logger.info("\n📌 Attempting to correlate orders with positions...\n")

            for pos in positions:
                logger.info(f"Position: {pos.contractId} (ID: {pos.id})")
                logger.info(f"  Size: {pos.size}, Entry: {pos.averagePrice}")

                # Find orders for this contract
                matching_orders = [o for o in orders if o.contractId == pos.contractId]

                if matching_orders:
                    logger.info(f"  Found {len(matching_orders)} orders for this contract:")
                    for order in matching_orders:
                        logger.info(f"    - Order {order.id}: {order.type_str} @ ${order.stopPrice or order.limitPrice}")
                else:
                    logger.info(f"  No working orders found for this contract")

                logger.info("")

            # Summary
            logger.info("🎯 CORRELATION FINDINGS:")
            logger.info(f"  - Orders and positions linked by: contractId (confirmed)")
            logger.info(f"  - Position has position_id? {'YES' if hasattr(positions[0], 'id') else 'NO'}")
            logger.info(f"  - Order has position_id field? {any(hasattr(o, 'position_id') or hasattr(o, 'positionId') for o in orders)}")

        else:
            logger.warning("Need both orders and positions to analyze correlation")
            logger.warning("Open a position with stop loss, then run this script")

    except Exception as e:
        logger.error(f"❌ Error in correlation analysis: {e}")

    # ========================================================================
    # SUMMARY & NEXT STEPS
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("✅ DISCOVERY COMPLETE")
    logger.info("=" * 80)
    logger.info("\n📝 Next Steps:")
    logger.info("  1. Review the attribute lists above")
    logger.info("  2. Check for linking fields (position_id, bracket_id, etc.)")
    logger.info("  3. Update cache_system.md Phase 6 with findings")
    logger.info("  4. Test edge cases (position scaling, stop modification)")
    logger.info("")

    await suite.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(query_sdk_state())
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
