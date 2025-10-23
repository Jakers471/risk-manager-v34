"""
Example 2: Advanced Rules Configuration

This example demonstrates how to create custom risk rules
and combine them for sophisticated risk management.
"""

import asyncio

from risk_manager import RiskManager
from risk_manager.rules import DailyLossRule, MaxPositionRule


async def main():
    print("🛡️ Risk Manager V34 - Advanced Rules Example\n")

    # Create risk manager
    rm = await RiskManager.create(instruments=["MNQ", "ES"])

    # Add custom rules with specific actions
    print("📋 Adding custom risk rules:\n")

    # Rule 1: Daily loss with flatten action
    daily_loss = DailyLossRule(
        limit=-1000.0,  # $1000 max loss
        action="flatten"  # Automatically close all positions
    )
    rm.add_rule(daily_loss)
    print("✓ Daily Loss Rule: -$1000 → Flatten all positions")

    # Rule 2: Max position per instrument
    max_position = MaxPositionRule(
        max_contracts=5,
        per_instrument=True,  # Apply limit to each instrument
        action="reject"  # Reject orders that would exceed
    )
    rm.add_rule(max_position)
    print("✓ Max Position Rule: 5 contracts per instrument → Reject orders")

    print()

    # Subscribe to all important events
    @rm.on("rule_violated")
    async def on_violation(event):
        print(f"🚨 VIOLATION: {event.data['rule']}")
        print(f"   {event.data['message']}")
        print(f"   Action: {event.data['action'].upper()}\n")

    @rm.on("enforcement_action")
    async def on_enforcement(event):
        print(f"⚡ ENFORCEMENT: {event.data['action']}")
        print(f"   Reason: {event.data['reason']}\n")

    @rm.on("position_updated")
    async def on_position_update(event):
        data = event.data
        print(f"📊 Position Update: {data['symbol']}")
        print(f"   Size: {data['size']}")
        print(f"   P&L: ${data.get('unrealized_pnl', 0):.2f}\n")

    # Start the risk manager
    print("🚀 Starting advanced risk management system...\n")
    await rm.start()

    print("💡 Monitoring MNQ and ES with custom rules")
    print("   Press Ctrl+C to stop\n")

    try:
        await rm.wait_until_stopped()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        await rm.stop()
        print("✅ Risk Manager stopped")


if __name__ == "__main__":
    asyncio.run(main())
