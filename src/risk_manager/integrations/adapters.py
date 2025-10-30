"""
SDK adapter layer - converts SDK types to canonical domain types.

This module provides the translation layer between Project-X SDK
and our canonical domain model. It normalizes:
    - Symbol names (ENQ → NQ)
    - Field names (contractId → contract_id)
    - Side values (1/2 → LONG/SHORT)
    - P&L sign conventions

All conversions are explicit and fail loud - no silent fallbacks.
"""

from decimal import Decimal
from typing import Any, Dict

from loguru import logger

from risk_manager.domain.types import Money, Position, Side
from risk_manager.errors import MappingError, UnitsError


# Symbol aliases (some brokers use different names)
# Maps: SDK symbol → canonical symbol root
SYMBOL_ALIASES = {
    "ENQ": "NQ",  # E-mini NASDAQ-100
}

# Tick economics for common futures instruments
# Format: {symbol: {"size": tick_size, "tick_value": tick_value_in_dollars}}
TICK_VALUES = {
    "NQ": {"size": 0.25, "tick_value": 5.00},  # NASDAQ-100 E-mini
    "MNQ": {"size": 0.25, "tick_value": 0.50},  # Micro NASDAQ-100 E-mini
    "ES": {"size": 0.25, "tick_value": 12.50},  # S&P 500 E-mini
    "MES": {"size": 0.25, "tick_value": 1.25},  # Micro S&P 500 E-mini
    "YM": {"size": 1.00, "tick_value": 5.00},  # Dow E-mini
    "MYM": {"size": 1.00, "tick_value": 0.50},  # Micro Dow E-mini
    "RTY": {"size": 0.10, "tick_value": 5.00},  # Russell 2000 E-mini
    "M2K": {"size": 0.10, "tick_value": 0.50},  # Micro Russell 2000 E-mini
}


class SDKAdapter:
    """
    Adapter for converting SDK types to canonical domain types.

    This class enforces the boundary between SDK-specific code and
    our domain model. All SDK data should pass through this adapter
    before reaching rules or the engine.
    """

    def normalize_symbol(self, symbol_or_contract: str) -> str:
        """
        Normalize symbol to canonical root form.

        Examples:
            ENQ → NQ
            MNQ → MNQ
            CON.F.US.MNQ.Z25 → MNQ

        Args:
            symbol_or_contract: Raw symbol or contract ID from SDK

        Returns:
            Canonical symbol root (uppercase)

        Raises:
            MappingError: If symbol cannot be extracted
        """
        if not symbol_or_contract:
            raise MappingError("Symbol or contract ID is empty")

        # Extract symbol from contract ID if necessary
        symbol = self._extract_symbol_from_contract(symbol_or_contract)

        # Apply aliases
        canonical = SYMBOL_ALIASES.get(symbol, symbol)

        return canonical.upper()

    def _extract_symbol_from_contract(self, contract_id: str) -> str:
        """
        Extract symbol from contract ID.

        Format: CON.F.US.{SYMBOL}.{EXPIRY}
        Example: CON.F.US.MNQ.Z25 → MNQ

        Args:
            contract_id: Full contract identifier

        Returns:
            Symbol extracted from contract

        Raises:
            MappingError: If contract format is invalid
        """
        if "." not in contract_id:
            # Already a symbol, not a contract ID
            return contract_id

        parts = contract_id.split(".")
        if len(parts) >= 4 and parts[0] == "CON":
            # Format: CON.F.US.{SYMBOL}.{EXPIRY}
            return parts[3]

        # Fallback: last part before expiry
        return parts[-2] if len(parts) >= 2 else contract_id

    def get_tick_economics(self, symbol_root: str) -> Dict[str, float]:
        """
        Get tick size and value for a symbol.

        Args:
            symbol_root: Normalized symbol (e.g., "NQ", "MNQ")

        Returns:
            Dictionary with "size" and "tick_value" keys

        Raises:
            UnitsError: If symbol is not in tick table (prevents silent fallback to 0.0)
        """
        if symbol_root not in TICK_VALUES:
            raise UnitsError(
                f"Unknown symbol '{symbol_root}' - no tick economics configured. "
                f"Known symbols: {list(TICK_VALUES.keys())}"
            )

        return TICK_VALUES[symbol_root]

    def normalize_position(
        self,
        sdk_position: Any,
        current_price: float | None = None,
        account_id: str | None = None,
    ) -> Position:
        """
        Convert SDK position to canonical Position type.

        Args:
            sdk_position: Position object from SDK (or dict with same fields)
            current_price: Current market price for P&L calculation (optional)
            account_id: Account identifier (optional)

        Returns:
            Canonical Position object

        Raises:
            MappingError: If required fields are missing or invalid
            UnitsError: If symbol has no tick economics
        """
        # Extract required fields (fail loud if missing)
        try:
            contract_id = (
                sdk_position.contractId
                if hasattr(sdk_position, "contractId")
                else sdk_position.get("contractId")
            )
            if not contract_id:
                raise MappingError("Position missing contractId")

            avg_price = (
                sdk_position.avgPrice if hasattr(sdk_position, "avgPrice") else sdk_position.get("avgPrice")
            )
            if avg_price is None:
                raise MappingError(f"Position {contract_id} missing avgPrice")

            size = sdk_position.size if hasattr(sdk_position, "size") else sdk_position.get("size")
            if size is None:
                raise MappingError(f"Position {contract_id} missing size")

            pos_type = (
                sdk_position.type if hasattr(sdk_position, "type") else sdk_position.get("type")
            )
            if pos_type is None:
                raise MappingError(f"Position {contract_id} missing type")

        except AttributeError as e:
            raise MappingError(f"Failed to extract position fields: {e}")

        # Normalize symbol
        symbol_root = self.normalize_symbol(contract_id)

        # Convert side
        side = Side.from_sdk_type(pos_type)

        # Calculate quantity (always positive)
        quantity = abs(size)

        # Calculate unrealized P&L
        if current_price is not None:
            unrealized_pnl = self._calculate_unrealized_pnl(
                symbol_root=symbol_root,
                entry_price=float(avg_price),
                current_price=current_price,
                quantity=quantity,
                side=side,
            )
        else:
            # No current price available, P&L is zero
            unrealized_pnl = Money(amount=Decimal("0.0"))

        # Get timestamp if available
        timestamp = getattr(sdk_position, "timestamp", None)

        return Position(
            symbol_root=symbol_root,
            contract_id=contract_id,
            side=side,
            quantity=quantity,
            entry_price=Decimal(str(avg_price)),
            unrealized_pnl=unrealized_pnl,
            account_id=account_id,
            timestamp=timestamp,
        )

    def _calculate_unrealized_pnl(
        self,
        symbol_root: str,
        entry_price: float,
        current_price: float,
        quantity: int,
        side: Side,
    ) -> Money:
        """
        Calculate unrealized P&L for a position.

        Formula:
            Long:  P&L = (current_price - entry_price) / tick_size * quantity * tick_value
            Short: P&L = (entry_price - current_price) / tick_size * quantity * tick_value

        Args:
            symbol_root: Normalized symbol (e.g., "NQ")
            entry_price: Position entry price
            current_price: Current market price
            quantity: Number of contracts (positive)
            side: Position side (LONG or SHORT)

        Returns:
            Unrealized P&L as Money object (negative = loss)

        Raises:
            UnitsError: If symbol has no tick economics
        """
        # Get tick economics (fails loud if unknown)
        tick_info = self.get_tick_economics(symbol_root)
        tick_size = tick_info["size"]
        tick_value = tick_info["tick_value"]

        # Calculate price difference based on side
        if side == Side.LONG:
            price_diff = current_price - entry_price
        else:  # SHORT
            price_diff = entry_price - current_price

        # Convert to ticks
        ticks = price_diff / tick_size

        # Calculate P&L
        pnl_amount = Decimal(str(ticks * quantity * tick_value))

        return Money(amount=pnl_amount)

    def normalize_position_from_dict(
        self,
        position_data: Dict[str, Any],
        current_price: float | None = None,
        account_id: str | None = None,
    ) -> Position:
        """
        Convert position dictionary to canonical Position type.

        This is a convenience method for when SDK data comes as a dict
        instead of an object.

        Args:
            position_data: Position data as dictionary
            current_price: Current market price for P&L calculation (optional)
            account_id: Account identifier (optional)

        Returns:
            Canonical Position object

        Raises:
            MappingError: If required fields are missing or invalid
            UnitsError: If symbol has no tick economics
        """
        # Create a simple object with dict-like access
        class DictWrapper:
            def __init__(self, data):
                self._data = data

            def get(self, key, default=None):
                return self._data.get(key, default)

            def __getattr__(self, key):
                if key.startswith("_"):
                    raise AttributeError(key)
                return self._data.get(key)

        wrapped = DictWrapper(position_data)
        return self.normalize_position(wrapped, current_price, account_id)


# Create singleton instance
adapter = SDKAdapter()
