"""
Unrealized P&L Calculator

Calculates floating P&L based on:
- Entry price (from position tracking)
- Current market price (from quote updates)
- Position size and side (long/short)
- Tick values (from tick_economics)

This calculator processes quote updates silently (no logging) and only emits
events when P&L changes significantly. This prevents log spam while maintaining
accurate real-time P&L tracking.
"""

from decimal import Decimal
from typing import Dict, Optional
from loguru import logger

from risk_manager.integrations.tick_economics import (
    get_tick_economics_safe,
    normalize_symbol,
    UnitsError,
)


class UnrealizedPnLCalculator:
    """Calculate floating P&L for open positions."""

    def __init__(self):
        """Initialize calculator with empty position and quote tracking."""
        self._open_positions: Dict[str, Dict] = {}  # {contract_id: position_data}
        self._latest_quotes: Dict[str, Decimal] = {}  # {symbol: last_price}
        self._last_logged_pnl: Dict[str, Decimal] = {}  # {contract_id: last_logged_pnl}

    def update_position(self, contract_id: str, entry_data: dict) -> None:
        """
        Track an opened position.

        Args:
            contract_id: Unique identifier for this position
            entry_data: Dictionary with keys:
                - price: Entry price
                - size: Position size (quantity)
                - side: 'long' or 'short'
                - symbol: Instrument symbol
        """
        try:
            symbol = entry_data['symbol']
            # Normalize symbol and validate tick economics exist
            normalized = normalize_symbol(symbol)
            get_tick_economics_safe(normalized)  # Validates symbol is known

            self._open_positions[contract_id] = {
                'entry_price': Decimal(str(entry_data['price'])),
                'size': abs(entry_data['size']),  # Always positive
                'side': entry_data['side'].lower(),  # 'long' or 'short'
                'symbol': normalized,  # Store normalized symbol
                'original_symbol': symbol,  # Keep original for logging
            }
            self._last_logged_pnl[contract_id] = Decimal('0')
            logger.debug(
                f"Position tracked: {contract_id} - {entry_data['side']} "
                f"{entry_data['size']} {symbol} @ ${entry_data['price']:.2f}"
            )
        except (KeyError, UnitsError) as e:
            logger.error(f"Failed to track position {contract_id}: {e}")

    def remove_position(self, contract_id: str) -> None:
        """
        Remove a closed position from tracking.

        Args:
            contract_id: Position identifier to remove
        """
        if contract_id in self._open_positions:
            del self._open_positions[contract_id]
            logger.debug(f"Position removed from tracking: {contract_id}")
        if contract_id in self._last_logged_pnl:
            del self._last_logged_pnl[contract_id]

    def update_quote(self, symbol: str, price: float) -> None:
        """
        Update latest market price for symbol (silent - no logging).

        Args:
            symbol: Instrument symbol
            price: Current market price
        """
        try:
            # Normalize symbol before storing
            normalized = normalize_symbol(symbol)
            self._latest_quotes[normalized] = Decimal(str(price))
            # NO LOGGING - this happens multiple times per second
        except Exception as e:
            # Only log errors at DEBUG level to avoid spam
            logger.debug(f"Error updating quote for {symbol}: {e}")

    def calculate_unrealized_pnl(self, contract_id: str) -> Optional[Decimal]:
        """
        Calculate floating P&L for a specific position.

        Formula:
            For LONG: (current_price - entry_price) / tick_size * tick_value * size
            For SHORT: (entry_price - current_price) / tick_size * tick_value * size

        Args:
            contract_id: Position identifier

        Returns:
            Decimal: Unrealized P&L in USD (positive = profit, negative = loss)
            None: If position not found or quote not available
        """
        if contract_id not in self._open_positions:
            return None

        position = self._open_positions[contract_id]
        symbol = position['symbol']

        if symbol not in self._latest_quotes:
            return None

        try:
            # Get tick economics
            tick_info = get_tick_economics_safe(symbol)
            tick_size = Decimal(str(tick_info['size']))
            tick_value = Decimal(str(tick_info['tick_value']))

            # Calculate price difference
            entry_price = position['entry_price']
            current_price = self._latest_quotes[symbol]

            if position['side'] == 'long':
                price_diff = current_price - entry_price
            else:  # short
                price_diff = entry_price - current_price

            # Convert to ticks
            ticks = price_diff / tick_size

            # Calculate P&L
            unrealized_pnl = ticks * tick_value * position['size']

            return unrealized_pnl

        except (UnitsError, KeyError, ZeroDivisionError) as e:
            logger.error(
                f"Error calculating P&L for {contract_id} ({symbol}): {e}"
            )
            return None

    def calculate_realized_pnl(
        self,
        contract_id: str,
        exit_price: float
    ) -> Optional[Decimal]:
        """
        Calculate realized P&L when a position closes.

        This is the ACTUAL profit/loss from entry to exit.
        Used when POSITION_CLOSED event fires.

        Formula:
            For LONG: (exit_price - entry_price) / tick_size * tick_value * size
            For SHORT: (entry_price - exit_price) / tick_size * tick_value * size

        Args:
            contract_id: Position identifier
            exit_price: Price at which position was closed

        Returns:
            Decimal: Realized P&L in USD (positive = profit, negative = loss)
            None: If position not found or calculation error
        """
        if contract_id not in self._open_positions:
            logger.warning(
                f"Cannot calculate realized P&L: position {contract_id} not tracked"
            )
            return None

        position = self._open_positions[contract_id]
        symbol = position['symbol']

        try:
            # Get tick economics
            tick_info = get_tick_economics_safe(symbol)
            tick_size = Decimal(str(tick_info['size']))
            tick_value = Decimal(str(tick_info['tick_value']))

            # Calculate price difference
            entry_price = position['entry_price']
            exit = Decimal(str(exit_price))

            if position['side'] == 'long':
                # Long: profit when exit > entry
                price_diff = exit - entry_price
            else:  # short
                # Short: profit when entry > exit
                price_diff = entry_price - exit

            # Convert to ticks
            ticks = price_diff / tick_size

            # Calculate realized P&L
            realized_pnl = ticks * tick_value * position['size']

            logger.debug(
                f"Realized P&L calculated for {contract_id}: "
                f"Entry ${float(entry_price):.2f} → Exit ${float(exit):.2f} = "
                f"{float(ticks):.1f} ticks × ${float(tick_value):.2f} × {position['size']} = "
                f"${float(realized_pnl):+,.2f}"
            )

            return realized_pnl

        except (UnitsError, KeyError, ZeroDivisionError) as e:
            logger.error(
                f"Error calculating realized P&L for {contract_id} ({symbol}): {e}"
            )
            return None

    def calculate_total_unrealized_pnl(self) -> Decimal:
        """
        Calculate total unrealized P&L across all open positions.

        Used by RULE-004 (Daily Unrealized Loss).

        Returns:
            Decimal: Total unrealized P&L in USD
        """
        total = Decimal('0')

        for contract_id in self._open_positions:
            pnl = self.calculate_unrealized_pnl(contract_id)
            if pnl is not None:
                total += pnl

        return total

    def get_open_positions(self) -> Dict[str, Dict]:
        """
        Get all currently tracked open positions.

        Returns:
            Dictionary of {contract_id: position_data}
        """
        return self._open_positions.copy()

    def get_position_count(self) -> int:
        """
        Get count of open positions being tracked.

        Returns:
            Number of open positions
        """
        return len(self._open_positions)

    def has_significant_pnl_change(
        self,
        contract_id: str,
        threshold: float = 10.0
    ) -> bool:
        """
        Check if P&L has changed significantly since last check.

        Used to throttle event emissions and avoid spam.

        Args:
            contract_id: Position identifier
            threshold: Minimum change in dollars to be considered significant

        Returns:
            True if P&L changed by more than threshold
        """
        current_pnl = self.calculate_unrealized_pnl(contract_id)
        if current_pnl is None:
            return False

        last_pnl = self._last_logged_pnl.get(contract_id, Decimal('0'))
        change = abs(current_pnl - last_pnl)

        if change >= Decimal(str(threshold)):
            self._last_logged_pnl[contract_id] = current_pnl
            return True

        return False

    def get_positions_by_symbol(self, symbol: str) -> Dict[str, Dict]:
        """
        Get all positions for a specific symbol.

        Args:
            symbol: Instrument symbol (will be normalized)

        Returns:
            Dictionary of {contract_id: position_data} for matching symbol
        """
        normalized = normalize_symbol(symbol)
        return {
            cid: pos
            for cid, pos in self._open_positions.items()
            if pos['symbol'] == normalized
        }

    def clear_all(self) -> None:
        """Clear all tracked positions and quotes (used for testing/reset)."""
        self._open_positions.clear()
        self._latest_quotes.clear()
        self._last_logged_pnl.clear()
        logger.info("Unrealized P&L calculator cleared")
