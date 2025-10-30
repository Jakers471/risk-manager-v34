"""
Diagnose Stop Loss Detection Issues.

Manually queries SDK to see what orders exist.
"""

import asyncio
import os

from loguru import logger
from project_x_py import TradingSuite


async def main():
    """Check what orders the SDK can see."""
    logger.info("=" * 80)
    logger.info("STOP LOSS DETECTION DIAGNOSTIC")
    logger.info("=" * 80)

    # Load environment
    api_key = os.getenv("PROJECTX_API_KEY")
    api_secret = os.getenv("PROJECTX_API_SECRET")
    account_id = os.getenv("PROJECTX_ACCOUNT_ID")

    logger.info(f"Account: {account_id}")
    logger.info("Connecting to SDK...")

    # Create trading suite
    async with TradingSuite.from_env() as suite:
        await suite.connect()
        logger.info("✅ Connected to SDK")

        # Get instrument (try ENQ first, then MNQ)
        for symbol in ["ENQ", "MNQ", "ES", "MES"]:
            if symbol in suite:
                logger.info(f"\n{'=' * 80}")
                logger.info(f"Checking {symbol}...")
                logger.info(f"{'=' * 80}")

                instrument = suite[symbol]

                # Get all positions
                try:
                    positions = await instrument.positions.get_all_positions()
                    logger.info(f"📊 Positions: {len(positions)}")

                    for pos in positions:
                        logger.info(
                            f"  Position: {pos.contractId} | "
                            f"Type: {pos.type} (1=LONG, 2=SHORT) | "
                            f"Size: {pos.size} | "
                            f"Avg Price: ${pos.avgPrice:,.2f}"
                        )

                        contract_id = pos.contractId

                        # Try method 1: get_position_orders
                        logger.info(f"\n  Method 1: get_position_orders('{contract_id}')")
                        try:
                            orders = await instrument.orders.get_position_orders(contract_id)
                            logger.info(f"  └─ Found {len(orders)} orders")
                            for order in orders:
                                logger.info(
                                    f"     Order #{order.id}: {order.type_str} | "
                                    f"Status: {order.status} | "
                                    f"Stop: ${order.stopPrice} | "
                                    f"Limit: ${order.limitPrice}"
                                )
                        except Exception as e:
                            logger.error(f"  └─ Error: {e}")

                        # Try method 2: search_open_orders (broker API)
                        logger.info(f"\n  Method 2: search_open_orders() [Broker API]")
                        try:
                            all_orders = await instrument.orders.search_open_orders()
                            logger.info(f"  └─ Found {len(all_orders)} total orders")

                            # Filter for this contract
                            contract_orders = [o for o in all_orders if o.contractId == contract_id]
                            logger.info(f"  └─ Filtered to {len(contract_orders)} orders for {contract_id}")

                            for order in contract_orders:
                                logger.info(
                                    f"     Order #{order.id}: {order.type_str} | "
                                    f"Status: {order.status} | "
                                    f"Stop: ${order.stopPrice} | "
                                    f"Limit: ${order.limitPrice}"
                                )
                        except Exception as e:
                            logger.error(f"  └─ Error: {e}")

                        # Semantic analysis
                        logger.info(f"\n  Semantic Analysis:")
                        logger.info(f"  Position: Type={pos.type}, Entry=${pos.avgPrice:,.2f}")

                        for order in (orders if orders else []):
                            trigger_price = order.stopPrice if order.stopPrice else order.limitPrice
                            logger.info(f"  Order #{order.id}:")
                            logger.info(f"    Type: {order.type} ({order.type_str})")
                            logger.info(f"    Trigger: ${trigger_price:,.2f}")

                            # Determine intent
                            if order.type in [3, 4, 5]:  # STOP types
                                logger.info(f"    ✅ STOP ORDER → Stop Loss")
                            elif order.type == 1:  # LIMIT
                                if pos.type == 1:  # LONG position
                                    if trigger_price > pos.avgPrice:
                                        logger.info(f"    ✅ LIMIT ABOVE entry → Take Profit")
                                    else:
                                        logger.info(f"    ⚠️ LIMIT BELOW entry → Entry order?")
                                elif pos.type == 2:  # SHORT position
                                    if trigger_price < pos.avgPrice:
                                        logger.info(f"    ✅ LIMIT BELOW entry → Take Profit")
                                    else:
                                        logger.info(f"    ⚠️ LIMIT ABOVE entry → Entry order?")
                            else:
                                logger.info(f"    ❓ Unknown order type")

                except Exception as e:
                    logger.error(f"Error checking {symbol}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

        logger.info("\n" + "=" * 80)
        logger.info("DIAGNOSTIC COMPLETE")
        logger.info("=" * 80)
        logger.info("\nIf you see orders above but run_dev.py doesn't detect them:")
        logger.info("  1. Check if contract_id matches between position and orders")
        logger.info("  2. Verify semantic analysis is working correctly")
        logger.info("  3. Check cache invalidation timing")
        logger.info("\nIf you DON'T see orders above:")
        logger.info("  1. Orders might not be placed yet in broker UI")
        logger.info("  2. SDK might not have refreshed order state")
        logger.info("  3. Orders might be on a different symbol than position")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv("config/.env")

    asyncio.run(main())
