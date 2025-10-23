"""
Example 3: Multi-Instrument Risk Management

Monitor multiple instruments simultaneously with
portfolio-level risk controls.
"""

import asyncio

from risk_manager import RiskManager


async def main():
    print("🛡️ Risk Manager V34 - Multi-Instrument Example\n")

    # Monitor multiple futures contracts
    instruments = ["MNQ", "ES", "MGC"]  # NASDAQ, S&P 500, Gold

    print(f"📊 Monitoring {len(instruments)} instruments:")
    for inst in instruments:
        print(f"   • {inst}")
    print()

    # Create with portfolio-wide limits
    rm = await RiskManager.create(
        instruments=instruments,
        rules={
            "max_daily_loss": -2000.0,  # Portfolio-wide loss limit
            "max_contracts": 10,  # Total contracts across all instruments
        }
    )

    # Track each instrument
    instrument_stats = {inst: {"fills": 0, "pnl": 0.0} for inst in instruments}

    @rm.on("order_filled")
    async def track_fills(event):
        symbol = event.data.get("symbol")
        if symbol in instrument_stats:
            instrument_stats[symbol]["fills"] += 1

        print(f"✅ Fill: {symbol} - {event.data.get('size')} @ ${event.data.get('price')}")
        print(f"   Total fills: {sum(s['fills'] for s in instrument_stats.values())}\n")

    @rm.on("position_updated")
    async def track_pnl(event):
        symbol = event.data["symbol"]
        pnl = event.data.get("unrealized_pnl", 0) + event.data.get("realized_pnl", 0)

        if symbol in instrument_stats:
            instrument_stats[symbol]["pnl"] = pnl

        # Show portfolio summary
        total_pnl = sum(s["pnl"] for s in instrument_stats.values())
        print(f"📊 Portfolio P&L: ${total_pnl:.2f}")
        for inst, stats in instrument_stats.items():
            print(f"   {inst}: ${stats['pnl']:.2f} ({stats['fills']} fills)")
        print()

    @rm.on("rule_violated")
    async def handle_violation(event):
        print(f"\n🚨 PORTFOLIO RULE VIOLATED!")
        print(f"   {event.data['message']}")
        print(f"   Taking action: {event.data['action'].upper()}\n")

    # Start monitoring
    await rm.start()

    print("💡 Multi-instrument risk management active")
    print("   Press Ctrl+C to stop\n")

    try:
        await rm.wait_until_stopped()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        await rm.stop()

        # Final summary
        print("\n📊 Session Summary:")
        for inst, stats in instrument_stats.items():
            print(f"   {inst}: {stats['fills']} fills, ${stats['pnl']:.2f} P&L")


if __name__ == "__main__":
    asyncio.run(main())
