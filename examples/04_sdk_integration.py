"""
Example: SDK Integration with Risk Manager

This example demonstrates the complete integration between the Risk Manager
and the Project-X SDK, showing:
1. SuiteManager - Managing TradingSuite instances
2. EventBridge - Routing SDK events to risk rules
3. EnforcementExecutor - Using SDK for enforcement
4. MaxContractsPerInstrumentRule - RULE-002 in action

Requirements:
- .env file with PROJECTX_USERNAME and PROJECTX_API_KEY
- Paper trading account
"""

import asyncio
import os

from loguru import logger

from risk_manager.core.config import RiskConfig
from risk_manager.core.engine import RiskEngine
from risk_manager.core.events import EventBus
from risk_manager.rules import MaxContractsPerInstrumentRule
from risk_manager.sdk import EnforcementExecutor, EventBridge, SuiteManager


async def main():
    """Run the SDK integration example."""

    # Check environment
    if not os.getenv("PROJECTX_USERNAME") or not os.getenv("PROJECTX_API_KEY"):
        logger.error("Missing PROJECTX_USERNAME or PROJECTX_API_KEY in .env")
        logger.info("Please create a .env file with your ProjectX credentials")
        return

    logger.info("=" * 80)
    logger.info("SDK Integration Example - Risk Manager V34")
    logger.info("=" * 80)

    # 1. Create Event Bus (our risk engine's event system)
    event_bus = EventBus()
    logger.info("✅ EventBus created")

    # 2. Create SuiteManager (manages SDK TradingSuites)
    suite_manager = SuiteManager(event_bus)
    logger.info("✅ SuiteManager created")

    # 3. Create EnforcementExecutor (uses SDK for enforcement)
    enforcement_executor = EnforcementExecutor(suite_manager)
    logger.info("✅ EnforcementExecutor created")

    # 4. Create EventBridge (bridges SDK events to our rules)
    event_bridge = EventBridge(suite_manager, event_bus)
    logger.info("✅ EventBridge created")

    # 5. Create Risk Engine
    config = RiskConfig()
    risk_engine = RiskEngine(config, event_bus)

    # Attach enforcement executor to engine so rules can use it
    risk_engine.enforcement_executor = enforcement_executor

    logger.info("✅ RiskEngine created")

    # 6. Configure rules - RULE-002: Max Contracts Per Instrument
    max_contracts_rule = MaxContractsPerInstrumentRule(
        limits={
            "MNQ": 2,  # Max 2 contracts in Micro NASDAQ
            "ES": 1,   # Max 1 contract in E-mini S&P
            "NQ": 1,   # Max 1 contract in E-mini NASDAQ
        },
        enforcement="reduce_to_limit",  # Reduce excess contracts
        unknown_symbol_action="block",  # Block unlisted symbols
    )

    risk_engine.add_rule(max_contracts_rule)
    logger.info("✅ RULE-002 (MaxContractsPerInstrument) added")

    # 7. Add instruments to monitor
    logger.info("\n" + "=" * 80)
    logger.info("Adding instruments...")
    logger.info("=" * 80)

    try:
        # Add MNQ (Micro NASDAQ)
        mnq_suite = await suite_manager.add_instrument(
            "MNQ",
            timeframes=["1min", "5min"],
            enable_statistics=True
        )
        logger.success(f"✅ MNQ TradingSuite created: {mnq_suite.instrument_info.id}")

        # Register with event bridge
        await event_bridge.add_instrument("MNQ", mnq_suite)

    except Exception as e:
        logger.error(f"Failed to add instruments: {e}")
        logger.info("\nNote: This example requires a valid ProjectX account")
        logger.info("If you see uvloop errors, you're on Windows - see STATUS.md")
        return

    # 8. Start all components
    logger.info("\n" + "=" * 80)
    logger.info("Starting components...")
    logger.info("=" * 80)

    await suite_manager.start()
    logger.success("✅ SuiteManager started")

    await event_bridge.start()
    logger.success("✅ EventBridge started (bridging SDK events to rules)")

    await risk_engine.start()
    logger.success("✅ RiskEngine started")

    # 9. Show system status
    logger.info("\n" + "=" * 80)
    logger.info("System Status")
    logger.info("=" * 80)

    health = await suite_manager.get_health_status()
    logger.info(f"Total Suites: {health['total_suites']}")

    for symbol, status in health["suites"].items():
        logger.info(
            f"  {symbol}: {'🟢 Connected' if status['connected'] else '🔴 Disconnected'}"
        )

    # 10. Monitor for a while
    logger.info("\n" + "=" * 80)
    logger.info("Monitoring Trading Activity")
    logger.info("=" * 80)
    logger.info("\nPress Ctrl+C to stop...\n")

    logger.info("💡 How this works:")
    logger.info("1. SDK monitors WebSocket for position updates")
    logger.info("2. EventBridge routes SDK events to RiskEngine")
    logger.info("3. Rules evaluate position sizes")
    logger.info("4. If RULE-002 breached, EnforcementExecutor uses SDK to reduce position")
    logger.info("\n🎯 Try opening a position in MNQ:")
    logger.info("   - 2 contracts = OK")
    logger.info("   - 3 contracts = AUTO-REDUCED to 2")
    logger.info("   - RTY position = AUTO-CLOSED (not in limits)")

    try:
        # Run for 5 minutes or until interrupted
        await asyncio.sleep(300)

    except KeyboardInterrupt:
        logger.info("\n\n📊 Stopping...")

    # 11. Cleanup
    logger.info("\n" + "=" * 80)
    logger.info("Shutting down...")
    logger.info("=" * 80)

    await risk_engine.stop()
    logger.success("✅ RiskEngine stopped")

    await event_bridge.stop()
    logger.success("✅ EventBridge stopped")

    await suite_manager.stop()
    logger.success("✅ SuiteManager stopped (all suites disconnected)")

    logger.info("\n" + "=" * 80)
    logger.info("SDK Integration Example Complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    # Run the example
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nExample stopped by user")
    except Exception as e:
        logger.error(f"Example failed: {e}")
        import traceback
        traceback.print_exc()
