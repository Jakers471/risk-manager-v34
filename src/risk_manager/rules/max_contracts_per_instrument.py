"""
RULE-002: Max Contracts Per Instrument

Enforces per-symbol contract limits to prevent concentration risk.

Reference: docs/PROJECT_DOCS/rules/02_max_contracts_per_instrument.md
"""

from typing import Any

from loguru import logger

from risk_manager.core.events import EventType, RiskEvent
from risk_manager.rules.base import RiskRule


class MaxContractsPerInstrumentRule(RiskRule):
    """
    Enforce maximum contract limits per instrument.

    Triggers on: POSITION_OPENED, POSITION_UPDATED
    Enforcement: Reduce to limit OR close all (configurable)
    Lockout: No

    Configuration:
    - limits: Dict mapping symbol to max contracts (e.g., {"MNQ": 2, "ES": 1})
    - enforcement: "reduce_to_limit" or "close_all"
    - unknown_symbol_action: "block", "allow_with_limit:N", "allow_unlimited"
    """

    def __init__(
        self,
        limits: dict[str, int],
        enforcement: str = "reduce_to_limit",
        unknown_symbol_action: str = "block",
    ):
        """
        Initialize the rule.

        Args:
            limits: Dictionary mapping symbols to max contracts (e.g., {"MNQ": 2})
            enforcement: "reduce_to_limit" or "close_all"
            unknown_symbol_action: "block", "allow_with_limit:N", "allow_unlimited"
        """
        super().__init__(action="reduce_position")

        self.limits = limits
        self.enforcement = enforcement
        self.unknown_symbol_action = unknown_symbol_action

        # Parse unknown_symbol_action if it has a limit
        self.unknown_symbol_limit: int | None = None
        if unknown_symbol_action.startswith("allow_with_limit:"):
            try:
                self.unknown_symbol_limit = int(unknown_symbol_action.split(":")[1])
            except (IndexError, ValueError):
                logger.error("Invalid unknown_symbol_action format, using 'block'")
                self.unknown_symbol_action = "block"

        logger.info(
            f"MaxContractsPerInstrumentRule initialized - "
            f"Limits: {limits}, Enforcement: {enforcement}, "
            f"Unknown: {unknown_symbol_action}"
        )

    async def evaluate(self, event: RiskEvent, engine: Any) -> bool:
        """
        Evaluate if position size exceeds per-instrument limit.

        Args:
            event: Position event (POSITION_OPENED or POSITION_UPDATED)
            engine: Risk engine instance

        Returns:
            True if rule is violated, False otherwise
        """
        # Only process position events
        if event.type not in [EventType.POSITION_OPENED, EventType.POSITION_UPDATED]:
            return False

        # Extract position data
        symbol = event.data.get("symbol")
        contract_id = event.data.get("contract_id")
        size = event.data.get("size", 0)

        if not symbol or not contract_id:
            logger.warning("Position event missing symbol or contract_id")
            return False

        # Get absolute size (long or short)
        current_size = abs(size)

        # If position is closed (size 0), no breach
        if current_size == 0:
            return False

        # Check if symbol has configured limit
        if symbol in self.limits:
            limit = self.limits[symbol]

            if current_size > limit:
                logger.warning(
                    f"⚠️ RULE-002 BREACH: {symbol} position size {current_size} "
                    f"exceeds limit {limit}"
                )

                # Store enforcement context
                self.context = {
                    "symbol": symbol,
                    "contract_id": contract_id,
                    "current_size": current_size,
                    "limit": limit,
                    "enforcement": self.enforcement,
                }

                return True

        else:
            # Unknown symbol handling
            return await self._handle_unknown_symbol(symbol, contract_id, current_size)

        return False

    async def _handle_unknown_symbol(
        self, symbol: str, contract_id: str, current_size: int
    ) -> bool:
        """
        Handle position in unknown symbol based on configuration.

        Args:
            symbol: Instrument symbol
            contract_id: Contract ID
            current_size: Current position size

        Returns:
            True if breach (should enforce), False otherwise
        """
        if self.unknown_symbol_action == "block":
            # Block all positions in unknown symbols
            if current_size > 0:
                logger.warning(
                    f"⚠️ RULE-002 BREACH: {symbol} not in configured limits, "
                    f"blocking position (size={current_size})"
                )

                self.context = {
                    "symbol": symbol,
                    "contract_id": contract_id,
                    "current_size": current_size,
                    "limit": 0,
                    "enforcement": "close_all",
                    "reason": "unknown_symbol_blocked",
                }

                return True

        elif self.unknown_symbol_action == "allow_unlimited":
            # Allow any size in unknown symbols
            return False

        elif self.unknown_symbol_limit is not None:
            # Allow up to specified limit
            if current_size > self.unknown_symbol_limit:
                logger.warning(
                    f"⚠️ RULE-002 BREACH: {symbol} not in configured limits, "
                    f"size {current_size} exceeds default limit {self.unknown_symbol_limit}"
                )

                self.context = {
                    "symbol": symbol,
                    "contract_id": contract_id,
                    "current_size": current_size,
                    "limit": self.unknown_symbol_limit,
                    "enforcement": self.enforcement,
                    "reason": "unknown_symbol_over_default_limit",
                }

                return True

        return False

    async def enforce(self, engine: Any) -> None:
        """
        Execute enforcement action using SDK.

        Args:
            engine: Risk engine instance (has enforcement_executor)
        """
        if not self.context:
            logger.error("No context for enforcement")
            return

        symbol = self.context["symbol"]
        contract_id = self.context["contract_id"]
        current_size = self.context["current_size"]
        limit = self.context["limit"]
        enforcement = self.context["enforcement"]

        logger.warning(
            f"🚨 ENFORCING RULE-002: {symbol} - {enforcement} "
            f"(size={current_size}, limit={limit})"
        )

        # Get enforcement executor from engine
        if not hasattr(engine, "enforcement_executor"):
            logger.error("Engine has no enforcement_executor")
            return

        executor = engine.enforcement_executor

        if enforcement == "reduce_to_limit":
            # Reduce position to limit
            if limit == 0:
                # Close entire position
                result = await executor.close_position(symbol, contract_id)
            else:
                # Partially close to reach limit
                result = await executor.reduce_position_to_limit(
                    symbol, contract_id, target_size=limit
                )

            if result["success"]:
                logger.success(
                    f"✅ RULE-002 ENFORCED: {symbol} reduced from {current_size} to {limit}"
                )
            else:
                logger.error(
                    f"❌ RULE-002 ENFORCEMENT FAILED: {symbol} - {result['error']}"
                )

        elif enforcement == "close_all":
            # Close entire position
            result = await executor.close_position(symbol, contract_id)

            if result["success"]:
                logger.success(
                    f"✅ RULE-002 ENFORCED: {symbol} entire position closed "
                    f"(was {current_size})"
                )
            else:
                logger.error(
                    f"❌ RULE-002 ENFORCEMENT FAILED: {symbol} - {result['error']}"
                )

        # Clear context
        self.context = None

    def get_status(self) -> dict[str, Any]:
        """
        Get current rule status.

        Returns:
            Dictionary with rule status and configuration
        """
        return {
            "rule": "MaxContractsPerInstrument",
            "enabled": True,
            "limits": self.limits,
            "enforcement": self.enforcement,
            "unknown_symbol_action": self.unknown_symbol_action,
        }
