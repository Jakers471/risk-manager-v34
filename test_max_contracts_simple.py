#!/usr/bin/env python3
"""
Simple Max Contracts Test - Just the essentials

Tests:
1. Authenticate with TopstepX
2. Receive position events (event-driven)
3. Flatten position when max contracts exceeded

That's it!
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set credentials
os.environ["PROJECT_X_API_KEY"] = "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
os.environ["PROJECT_X_USERNAME"] = "jakertrader"
os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRAC-V2-126244-84184528"

from loguru import logger
from project_x_py import ProjectX
from project_x_py.realtime import ProjectXRealtimeClient

# Configure simple logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")

MAX_CONTRACTS = 2  # Your limit


async def test_max_contracts():
    """Test max contracts with event-driven position updates."""

    print("\n" + "=" * 80)
    print("  MAX CONTRACTS TEST - Simple Event-Driven")
    print("=" * 80)
    print(f"\n  Max Contracts Limit: {MAX_CONTRACTS}")
    print(f"  Listening for position updates...")
    print("\n" + "=" * 80 + "\n")

    positions_received = []
    violations_detected = []

    # STEP 1: HTTP Authentication
    logger.info("Step 1: Authenticating...")

    # Force the correct credentials AND account
    api_key = "tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s="
    username = "jakertrader"
    account_name = "PRAC-V2-126244-84184528"

    client = ProjectX(
        username=username,
        api_key=api_key,
        account_name=account_name  # ← THIS SELECTS THE CORRECT ACCOUNT!
    )
    await client.authenticate()

    logger.info(f"✅ Authenticated: {client.account_info.name}")
    logger.info(f"   Balance: ${client.account_info.balance:,.2f}")

    # STEP 2: SignalR Connection
    logger.info("\nStep 2: Connecting to SignalR...")

    realtime = ProjectXRealtimeClient(
        jwt_token=client.session_token,
        account_id=str(client.account_info.id)
    )
    await realtime.connect()

    if realtime.is_connected:
        logger.info("✅ SignalR connected")
    else:
        logger.error("❌ SignalR failed to connect")
        return False

    # STEP 3: Subscribe to Position Updates
    logger.info("\nStep 3: Subscribing to position updates...")

    async def on_position_update(data):
        """Handle position update from SignalR."""
        try:
            if not isinstance(data, list):
                return

            for update in data:
                position_data = update.get('data', {})
                size = position_data.get('size', 0)
                contract_id = position_data.get('contractId', 'unknown')

                if size == 0:
                    return  # Ignore flat positions

                positions_received.append(size)

                logger.info(f"\n📨 POSITION UPDATE: {abs(size)} contracts")
                logger.info(f"   Contract: {contract_id}")

                # CHECK MAX CONTRACTS RULE
                if abs(size) > MAX_CONTRACTS:
                    violations_detected.append(size)
                    logger.warning(f"⚠️  VIOLATION: {abs(size)} > {MAX_CONTRACTS} contracts!")
                    logger.warning(f"⚠️  WOULD FLATTEN NOW (flatten disabled for safety)")

                    # UNCOMMENT TO ACTUALLY FLATTEN:
                    # logger.warning("🔨 FLATTENING POSITION...")
                    # await flatten_position(client, contract_id)
                else:
                    logger.info(f"✅ Within limit ({abs(size)}/{MAX_CONTRACTS})")

        except Exception as e:
            logger.error(f"Error handling position: {e}")

    # Register callback
    await realtime.add_callback("position_update", on_position_update)
    logger.info("✅ Subscribed to position_update events")

    # STEP 4: Listen
    logger.info("\n" + "=" * 80)
    logger.info("🎧 LISTENING FOR POSITION EVENTS (60 seconds)")
    logger.info("=" * 80)
    logger.info("\n👉 Place trades in your TopstepX account to test!\n")

    for i in range(60):
        await asyncio.sleep(1)
        if len(positions_received) > 0 and i % 10 == 0:
            logger.info(f"   [{i}s] Received {len(positions_received)} position updates")

    # STEP 5: Results
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST RESULTS")
    logger.info("=" * 80)

    logger.info(f"\n1. Authentication:       ✅ SUCCESS")
    logger.info(f"2. SignalR Connection:   ✅ SUCCESS")
    logger.info(f"3. Position Events:      {len(positions_received)} received")
    logger.info(f"4. Violations Detected:  {len(violations_detected)}")

    if violations_detected:
        logger.warning(f"\n⚠️  VIOLATIONS FOUND:")
        for size in violations_detected:
            logger.warning(f"   - {abs(size)} contracts (limit: {MAX_CONTRACTS})")
        logger.warning(f"\n✅ Would have flattened {len(violations_detected)} time(s)")

    if len(positions_received) > 0:
        logger.info(f"\n✅ SUCCESS: Event-driven position updates working!")
        logger.info(f"   The system received real-time position events")
        logger.info(f"   Max contracts rule would enforce properly")
    else:
        logger.warning(f"\n⚠️  No position updates received")
        logger.warning(f"   Place trades to test the full flow")

    # Cleanup
    await realtime.disconnect()

    logger.info("\n" + "=" * 80 + "\n")

    return len(positions_received) > 0 or len(violations_detected) > 0


async def flatten_position(client, contract_id):
    """Flatten a position (DISABLED FOR SAFETY)."""
    logger.info(f"🔨 FLATTEN: Would close position {contract_id}")
    # Uncomment to actually flatten:
    # response = await client.close_position(contract_id=contract_id)
    # logger.info(f"✅ Position flattened: {response}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  SIMPLE MAX CONTRACTS TEST")
    print("  Event-Driven Position Monitoring + Auto-Flatten")
    print("=" * 80)

    try:
        success = asyncio.run(test_max_contracts())
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user\n")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
