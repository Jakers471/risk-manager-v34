"""
Example 1: Basic Risk Manager Usage

This example shows the simplest way to use Risk Manager V34
to protect your trading capital.
"""

import asyncio

from risk_manager import RiskManager


async def main():
    print("🛡️ Risk Manager V34 - Basic Example\n")

    # Create risk manager with simple rules
    rm = await RiskManager.create(
        instruments=["MNQ"],  # Monitor E-mini NASDAQ
        rules={
            "max_daily_loss": -500.0,  # Stop after $500 loss
            "max_contracts": 2,  # Max 2 contracts at once
        }
    )

    print("✅ Risk Manager configured:")
    print(f"   • Max Daily Loss: $-500")
    print(f"   • Max Contracts: 2")
    print(f"   • Monitoring: MNQ\n")

    # Subscribe to alerts
    @rm.on("rule_violated")
    async def handle_violation(event):
        print(f"⚠️  ALERT: {event.data['message']}")
        print(f"   Action: {event.data['action'].upper()}\n")

    # Start monitoring
    print("🚀 Starting risk manager...\n")
    await rm.start()

    print("💡 Risk Manager is now protecting your capital!")
    print("   Press Ctrl+C to stop\n")

    # Keep running
    try:
        await rm.wait_until_stopped()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping Risk Manager...")
        await rm.stop()
        print("✅ Stopped gracefully")


if __name__ == "__main__":
    asyncio.run(main())
