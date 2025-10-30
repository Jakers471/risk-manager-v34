"""
Verify P&L Calculation Against Broker Records.

Queries the broker's trade history and compares with our calculations.
"""

import asyncio
import os
from datetime import datetime

from loguru import logger
from project_x_py import ProjectX

from risk_manager.integrations.trade_history import TradeHistoryClient


async def main():
    """Verify P&L against broker trade history."""
    logger.info("=" * 80)
    logger.info("P&L VERIFICATION - Comparing Our Calculations vs Broker Records")
    logger.info("=" * 80)

    # Get account ID from environment
    account_id = os.getenv("PROJECTX_ACCOUNT_ID", "PRAC-V2-126244-84184528")
    logger.info(f"Account: {account_id}")

    # Connect to ProjectX API
    logger.info("Connecting to ProjectX Gateway API...")
    async with ProjectX.from_env() as client:
        await client.authenticate()
        logger.info(f"✅ Authenticated: {client.account_info.firstName} {client.account_info.lastName}")

        # Create trade history client
        history = TradeHistoryClient(client)

        # Get last 24 hours of trades
        logger.info("Querying last 24 hours of trades...")
        trades = await history.get_recent_trades(account_id, hours=24)

        if not trades:
            logger.warning("No trades found in last 24 hours")
            return

        # Display broker's trade summary
        history.display_trade_summary(trades)

        # Compare with our calculations
        logger.info("")
        logger.info("=" * 80)
        logger.info("VERIFICATION NOTES")
        logger.info("=" * 80)
        logger.info("✅ Broker P&L comes from actual execution records")
        logger.info("✅ Our P&L: (exit_price - entry_price) / tick_size * tick_value * contracts")
        logger.info("✅ For MNQ: tick_size=0.25, tick_value=$5.00")
        logger.info("✅ For ENQ (Micro E-mini NASDAQ): tick_size=0.25, tick_value=$0.50")
        logger.info("")
        logger.info("Compare the broker's P&L with what run_dev.py shows in real-time.")
        logger.info("They should match within rounding errors.")
        logger.info("=" * 80)


if __name__ == "__main__":
    # Load environment from .env file
    from dotenv import load_dotenv
    load_dotenv("config/.env")

    asyncio.run(main())
