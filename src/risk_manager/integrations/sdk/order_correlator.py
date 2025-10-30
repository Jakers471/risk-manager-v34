"""
Order Correlator Module

Correlates order fills with position updates to determine exit type.

The Challenge:
    - When a position closes, we need to know WHY it closed
    - Was it a stop loss hit? Take profit hit? Manual exit?
    - POSITION_CLOSED event doesn't tell us the exit type
    - ORDER_FILLED event fires BEFORE position close event
    - Need to cache recent fills and correlate them with position closes

The Solution:
    - Cache fills when ORDER_FILLED fires (with type: stop_loss/take_profit/manual)
    - When POSITION_CLOSED fires, check recent fills cache
    - TTL-based: Only keep fills for 2 seconds (correlation window)
    - This gives us accurate exit type for each position close

Usage:
    # Initialize
    correlator = OrderCorrelator(ttl=2.0)

    # When order fills
    correlator.record_fill(
        contract_id="CON.F.US.MNQ.Z25",
        fill_type="stop_loss",  # or "take_profit" or "manual"
        fill_price=21500.00,
        side="SELL",
        order_id=12345
    )

    # When position closes (shortly after)
    fill_type = correlator.get_fill_type(contract_id)  # Returns "stop_loss"
    fill_price = correlator.get_fill_price(contract_id)  # Returns 21500.00

    # Cleanup
    correlator.clear_fill(contract_id)  # Remove after use
"""

import time
from typing import Optional, Dict, Any
from loguru import logger


class OrderCorrelator:
    """
    Correlates order fills with position updates.

    Tracks recent fills to determine exit type when positions close.
    This is critical for distinguishing stop loss hits from manual exits.
    """

    def __init__(self, ttl: float = 2.0):
        """
        Initialize order correlator.

        Args:
            ttl: Time-to-live for fills in seconds (correlation window)
        """
        self._recent_fills: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl
        logger.debug(f"OrderCorrelator initialized with TTL={ttl}s")

    def record_fill(
        self,
        contract_id: str,
        fill_type: str,
        fill_price: float,
        side: str,
        order_id: int
    ) -> None:
        """
        Record an order fill for later correlation.

        Called when ORDER_FILLED event fires.

        Args:
            contract_id: Contract identifier
            fill_type: "stop_loss", "take_profit", or "manual"
            fill_price: Price at which order filled
            side: "BUY" or "SELL"
            order_id: Order identifier
        """
        self._recent_fills[contract_id] = {
            "type": fill_type,
            "timestamp": time.time(),
            "side": side,
            "order_id": order_id,
            "fill_price": fill_price,
        }
        logger.debug(
            f"Recorded {fill_type} fill: {contract_id} @ ${fill_price:.2f} "
            f"(order {order_id})"
        )

    def get_fill_type(self, contract_id: str) -> Optional[str]:
        """
        Get the fill type for a contract (if recent fill exists).

        Called when POSITION_CLOSED event fires to determine why position closed.

        Automatically cleans up expired fills (older than TTL).

        Args:
            contract_id: Contract identifier

        Returns:
            "stop_loss", "take_profit", "manual", or None if no recent fill
        """
        # Cleanup expired fills first
        self._cleanup_expired_fills()

        # Check for recent fill
        fill_data = self._recent_fills.get(contract_id)
        if fill_data:
            return fill_data["type"]

        return None

    def get_fill_price(self, contract_id: str) -> Optional[float]:
        """
        Get the fill price for a contract (if recent fill exists).

        This is the actual exit price, which may differ from the
        average price shown in POSITION_CLOSED event.

        Args:
            contract_id: Contract identifier

        Returns:
            Fill price or None if no recent fill
        """
        fill_data = self._recent_fills.get(contract_id)
        if fill_data:
            return fill_data["fill_price"]

        return None

    def get_fill_data(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete fill data for a contract.

        Returns full dict with type, timestamp, side, order_id, fill_price.

        Args:
            contract_id: Contract identifier

        Returns:
            Fill data dict or None if no recent fill
        """
        return self._recent_fills.get(contract_id)

    def clear_fill(self, contract_id: str) -> None:
        """
        Remove a fill from tracking (after it's been used).

        Called after position close is fully processed.

        Args:
            contract_id: Contract identifier
        """
        if contract_id in self._recent_fills:
            del self._recent_fills[contract_id]
            logger.debug(f"Cleared fill tracking for {contract_id}")

    def _cleanup_expired_fills(self) -> None:
        """
        Remove fills older than TTL.

        Called automatically by get_fill_type() to keep cache clean.
        """
        current_time = time.time()

        expired_contracts = [
            cid for cid, fill_data in self._recent_fills.items()
            if current_time - fill_data["timestamp"] > self._ttl
        ]

        for cid in expired_contracts:
            del self._recent_fills[cid]
            logger.debug(f"Expired fill tracking for {cid} (TTL exceeded)")

    def get_active_fills_count(self) -> int:
        """
        Get count of currently tracked fills.

        Used for debugging and monitoring.

        Returns:
            Number of active fills in cache
        """
        return len(self._recent_fills)

    def get_active_contracts(self) -> list[str]:
        """
        Get list of contracts with active fills.

        Used for debugging and monitoring.

        Returns:
            List of contract IDs with recent fills
        """
        return list(self._recent_fills.keys())

    def clear_all(self) -> None:
        """
        Clear all tracked fills.

        Used for testing/reset.
        """
        self._recent_fills.clear()
        logger.debug("Cleared all fill tracking")
