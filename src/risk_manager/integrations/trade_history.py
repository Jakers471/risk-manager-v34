"""
Trade History Retrieval from ProjectX Gateway API.

Queries broker's actual trade records to verify P&L calculations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

from loguru import logger
from project_x_py import ProjectX


class TradeHistoryClient:
    """
    Client for querying trade history from ProjectX Gateway API.

    Uses the HTTP REST endpoints to get actual broker records.
    """

    def __init__(self, client: ProjectX):
        self.client = client

    async def get_recent_trades(
        self,
        account_id: str,
        hours: int = 24,
    ) -> list[dict[str, Any]]:
        """
        Get recent trades from broker.

        Args:
            account_id: Account ID (e.g., "PRAC-V2-126244-84184528")
            hours: How many hours back to query (default: 24)

        Returns:
            List of trade dicts with fields:
                - id: Trade ID
                - price: Execution price
                - profitAndLoss: Realized P&L (null for half-turn trades)
                - side: 0=BUY, 1=SELL
                - size: Quantity
                - orderId: Order that generated this trade
                - contractId: Contract identifier
                - creationTimestamp: Trade execution time
                - fees: Transaction fees
        """
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        logger.info(f"Querying trades: {start_time.isoformat()} to {end_time.isoformat()}")

        try:
            # Use the Gateway API endpoint
            # POST https://api.topstepx.com/api/Trade/search
            payload = {
                "accountId": int(account_id.split('-')[-1]),  # Extract numeric ID
                "startTimestamp": start_time.isoformat() + 'Z',
                "endTimestamp": end_time.isoformat() + 'Z',
            }

            # Make the request via client
            response = await self.client._http_client.post(
                "/api/Trade/search",
                json=payload,
            )

            trades = response.json()
            logger.info(f"Retrieved {len(trades)} trades from broker")

            return trades

        except Exception as e:
            logger.error(f"Failed to query trade history: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []

    async def get_order_history(
        self,
        account_id: str,
        hours: int = 24,
    ) -> list[dict[str, Any]]:
        """
        Get order history from broker.

        Args:
            account_id: Account ID
            hours: How many hours back to query

        Returns:
            List of order dicts with fields:
                - id: Order ID
                - status: 1=WORKING, 2=FILLED, 3=CANCELLED, 4=REJECTED, 5=PENDING
                - type: 1=LIMIT, 2=MARKET, 3=STOP_LIMIT, 4=STOP, 5=TRAILING_STOP
                - fillVolume: Quantity filled
                - filledPrice: Execution price
                - side: 0=BUY, 1=SELL
                - stopPrice, limitPrice: Order prices
                - creationTimestamp, updateTimestamp: Timestamps
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        try:
            payload = {
                "accountId": int(account_id.split('-')[-1]),
                "startTimestamp": start_time.isoformat() + 'Z',
                "endTimestamp": end_time.isoformat() + 'Z',
            }

            response = await self.client._http_client.post(
                "/api/Order/search",
                json=payload,
            )

            orders = response.json()
            logger.info(f"Retrieved {len(orders)} orders from broker")

            return orders

        except Exception as e:
            logger.error(f"Failed to query order history: {e}")
            return []

    def display_trade_summary(self, trades: list[dict[str, Any]]) -> None:
        """
        Display formatted trade summary for verification.

        Args:
            trades: List of trade dicts from get_recent_trades()
        """
        if not trades:
            logger.warning("No trades to display")
            return

        logger.info("=" * 80)
        logger.info("BROKER TRADE HISTORY (Last 24 Hours)")
        logger.info("=" * 80)

        total_pnl = 0.0
        for trade in trades:
            trade_id = trade.get('id')
            price = trade.get('price', 0.0)
            pnl = trade.get('profitAndLoss')
            side = "BUY" if trade.get('side') == 0 else "SELL"
            size = trade.get('size', 0)
            contract_id = trade.get('contractId', 'UNKNOWN')
            timestamp = trade.get('creationTimestamp', '')

            # Format P&L
            pnl_str = f"${pnl:+,.2f}" if pnl is not None else "N/A (half-turn)"

            logger.info(
                f"  Trade #{trade_id}: {side} {size} @ ${price:,.2f} | "
                f"P&L: {pnl_str} | {timestamp}"
            )

            if pnl is not None:
                total_pnl += pnl

        logger.info("=" * 80)
        logger.info(f"TOTAL REALIZED P&L: ${total_pnl:+,.2f}")
        logger.info("=" * 80)
