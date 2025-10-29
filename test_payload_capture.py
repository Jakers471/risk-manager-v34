"""
Test Payload Capture - Broker Data Model Discovery

Logs EVERYTHING we receive from the broker.
Run this while manually trading to capture all payload structures.

Usage:
    python test_payload_capture.py

Then perform trades in your broker UI:
    1. Open a position (buy 2 contracts)
    2. Place a stop loss
    3. Scale in (buy 2 more contracts)
    4. Place another stop loss
    5. Modify one stop loss (move it)
    6. Cancel one stop loss
    7. Let one stop loss hit
    8. Manually close remaining position

Press Ctrl+C when done.

Output will be saved to: broker_payloads_TIMESTAMP.log
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger
from project_x_py import TradingSuite, EventType as SDKEventType


# Configure logger to write to both console and file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"broker_payloads_{timestamp}.log"

logger.remove()  # Remove default handler
logger.add(sys.stdout, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
logger.add(log_file, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}")

logger.info(f"Payload capture starting. Logging to: {log_file}")


async def capture_all_events():
    """Capture all events from broker with full payload introspection."""

    logger.info("Connecting to TradingSuite...")
    suite = await TradingSuite.create(
        instruments=["MNQ"],
        timeframes=["1min"],
        features=["performance_analytics", "auto_reconnect"],
    )
    logger.success("✅ Connected to TradingSuite")

    # Event counter
    event_counts = {}

    async def log_event(event, event_name):
        """Log event with complete payload introspection."""
        event_counts[event_name] = event_counts.get(event_name, 0) + 1
        count = event_counts[event_name]

        logger.info("\n" + "=" * 80)
        logger.info(f"EVENT #{count}: {event_name}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80)

        # Get payload
        payload = event.data if hasattr(event, 'data') else {}
        logger.info(f"Payload Type: {type(payload)}")

        if isinstance(payload, dict):
            logger.info(f"Payload Keys: {list(payload.keys())}")

            # Try to JSON serialize (handles basic types)
            try:
                json_str = json.dumps(payload, indent=2, default=str)
                logger.info(f"Payload Data:\n{json_str}")
            except Exception as e:
                logger.warning(f"Could not JSON serialize payload: {e}")
                logger.info(f"Payload (repr): {payload}")

            # If there's an 'order' object, introspect it
            if 'order' in payload:
                order = payload['order']
                logger.info("\n📦 ORDER OBJECT INTROSPECTION:")
                logger.info(f"  Type: {type(order)}")
                logger.info(f"  All attributes: {[a for a in dir(order) if not a.startswith('_')]}")

                logger.info("\n  Attribute Values:")
                for attr in dir(order):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(order, attr)
                            if not callable(val):
                                logger.info(f"    {attr}: {val} (type: {type(val).__name__})")
                        except Exception as e:
                            logger.warning(f"    {attr}: <error getting value: {e}>")

            # If there's position data, introspect it
            if any(key in payload for key in ['id', 'contractId', 'size', 'averagePrice']):
                logger.info("\n📊 POSITION DATA:")
                for key, value in payload.items():
                    logger.info(f"    {key}: {value} (type: {type(value).__name__})")

        else:
            logger.info(f"Payload: {payload}")

        logger.info("=" * 80 + "\n")

    # Register for ALL order events
    logger.info("Registering event handlers...")

    await suite.on(SDKEventType.ORDER_PLACED, lambda e: log_event(e, "ORDER_PLACED"))
    await suite.on(SDKEventType.ORDER_FILLED, lambda e: log_event(e, "ORDER_FILLED"))
    await suite.on(SDKEventType.ORDER_PARTIAL_FILL, lambda e: log_event(e, "ORDER_PARTIAL_FILL"))
    await suite.on(SDKEventType.ORDER_CANCELLED, lambda e: log_event(e, "ORDER_CANCELLED"))
    await suite.on(SDKEventType.ORDER_MODIFIED, lambda e: log_event(e, "ORDER_MODIFIED"))
    await suite.on(SDKEventType.ORDER_REJECTED, lambda e: log_event(e, "ORDER_REJECTED"))
    await suite.on(SDKEventType.ORDER_EXPIRED, lambda e: log_event(e, "ORDER_EXPIRED"))

    logger.info("✅ Registered ORDER event handlers (7 types)")

    # Register for ALL position events
    await suite.on(SDKEventType.POSITION_OPENED, lambda e: log_event(e, "POSITION_OPENED"))
    await suite.on(SDKEventType.POSITION_CLOSED, lambda e: log_event(e, "POSITION_CLOSED"))
    await suite.on(SDKEventType.POSITION_UPDATED, lambda e: log_event(e, "POSITION_UPDATED"))

    logger.info("✅ Registered POSITION event handlers (3 types)")

    logger.success("\n" + "=" * 80)
    logger.success("🎯 EVENT CAPTURE ACTIVE")
    logger.success("=" * 80)
    logger.info("\n📋 INSTRUCTIONS:")
    logger.info("  1. Open your broker UI")
    logger.info("  2. Buy 2 MNQ contracts")
    logger.info("  3. Place a stop loss")
    logger.info("  4. Buy 2 MORE MNQ (scale in)")
    logger.info("  5. Place another stop loss")
    logger.info("  6. Modify one stop loss (move the price)")
    logger.info("  7. Cancel one stop loss")
    logger.info("  8. Let one stop loss hit (or manually close)")
    logger.info("  9. Close remaining position")
    logger.info("\n⌨️  Press Ctrl+C when done\n")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n👍 Capture stopped by user")

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 EVENT SUMMARY")
    logger.info("=" * 80)
    for event_name, count in sorted(event_counts.items()):
        logger.info(f"  {event_name}: {count} events")
    logger.info(f"\n✅ Log saved to: {log_file}")
    logger.info("=" * 80 + "\n")

    await suite.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(capture_all_events())
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
