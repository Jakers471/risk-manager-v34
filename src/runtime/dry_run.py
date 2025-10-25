"""
Dry run mode with mock event generation.

Generates fake Trade/Order events for testing without live market data.
Deterministic event generation for CI/CD testing and validation.

Features:
- Generates fake Trade, Order, and Position events
- Deterministic event patterns for reproducible testing
- Controlled via DRY_RUN environment variable
- Configurable event rate and patterns
- No external dependencies

Environment variables:
- DRY_RUN: Enable dry run mode (1=enabled)
- DRY_RUN_RATE: Events per second (default: 1.0)
- DRY_RUN_PATTERN: Event pattern (sequential, random, burst)

Author: Risk Manager Team
Date: 2025-10-23
"""

import asyncio
import logging
import os
import random
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventPattern(Enum):
    """Event generation patterns."""

    SEQUENTIAL = "sequential"  # Predictable sequence
    RANDOM = "random"  # Random events
    BURST = "burst"  # Bursts of events


class EventType(Enum):
    """Mock event types."""

    TRADE = "Trade"
    ORDER = "Order"
    POSITION = "Position"


def is_dry_run_enabled() -> bool:
    """
    Check if dry run mode is enabled.

    Returns:
        True if DRY_RUN=1 is set
    """
    return os.getenv("DRY_RUN", "0") == "1"


def get_dry_run_rate() -> float:
    """
    Get dry run event rate in events per second.

    Returns:
        Events per second (default: 1.0)
    """
    try:
        return float(os.getenv("DRY_RUN_RATE", "1.0"))
    except ValueError:
        logger.warning("Invalid DRY_RUN_RATE, using default 1.0")
        return 1.0


def get_dry_run_pattern() -> EventPattern:
    """
    Get dry run event pattern.

    Returns:
        EventPattern enum value
    """
    pattern_str = os.getenv("DRY_RUN_PATTERN", "sequential").lower()
    try:
        return EventPattern(pattern_str)
    except ValueError:
        logger.warning(f"Invalid DRY_RUN_PATTERN '{pattern_str}', using sequential")
        return EventPattern.SEQUENTIAL


class MockEventGenerator:
    """Generates deterministic mock events for testing."""

    def __init__(self, seed: int = 42):
        """
        Initialize mock event generator.

        Args:
            seed: Random seed for deterministic generation
        """
        self.seed = seed
        self.rng = random.Random(seed)
        self.event_count = 0

        # Mock symbols for deterministic testing
        self.symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]

    def generate_trade(self) -> Dict[str, Any]:
        """
        Generate mock trade event.

        Returns:
            Dictionary with trade data
        """
        self.event_count += 1

        return {
            "type": "Trade",
            "event_id": f"trade_{self.event_count}",
            "timestamp": datetime.now(UTC).isoformat(),
            "symbol": self.symbols[self.event_count % len(self.symbols)],
            "quantity": self.rng.randint(1, 100) * 100,
            "price": round(self.rng.uniform(100, 500), 2),
            "side": "BUY" if self.event_count % 2 == 0 else "SELL",
            "order_id": f"order_{self.event_count}",
            "account_id": "DRY_RUN_ACCOUNT",
            "dry_run": True,
        }

    def generate_order(self) -> Dict[str, Any]:
        """
        Generate mock order event.

        Returns:
            Dictionary with order data
        """
        self.event_count += 1

        order_types = ["MARKET", "LIMIT", "STOP"]
        statuses = ["PENDING", "FILLED", "CANCELLED", "REJECTED"]

        return {
            "type": "Order",
            "event_id": f"order_{self.event_count}",
            "timestamp": datetime.now(UTC).isoformat(),
            "symbol": self.symbols[self.event_count % len(self.symbols)],
            "quantity": self.rng.randint(1, 100) * 100,
            "order_type": order_types[self.event_count % len(order_types)],
            "status": statuses[self.event_count % len(statuses)],
            "side": "BUY" if self.event_count % 2 == 0 else "SELL",
            "price": round(self.rng.uniform(100, 500), 2),
            "order_id": f"order_{self.event_count}",
            "account_id": "DRY_RUN_ACCOUNT",
            "dry_run": True,
        }

    def generate_position(self) -> Dict[str, Any]:
        """
        Generate mock position event.

        Returns:
            Dictionary with position data
        """
        self.event_count += 1

        return {
            "type": "Position",
            "event_id": f"position_{self.event_count}",
            "timestamp": datetime.now(UTC).isoformat(),
            "symbol": self.symbols[self.event_count % len(self.symbols)],
            "quantity": self.rng.randint(-100, 100) * 100,
            "avg_price": round(self.rng.uniform(100, 500), 2),
            "unrealized_pnl": round(self.rng.uniform(-1000, 1000), 2),
            "realized_pnl": round(self.rng.uniform(-500, 500), 2),
            "account_id": "DRY_RUN_ACCOUNT",
            "dry_run": True,
        }


class DryRunEventGenerator:
    """
    Dry run event generator for testing without live data.

    Generates deterministic mock events based on configured pattern.
    """

    def __init__(
        self,
        rate: Optional[float] = None,
        pattern: Optional[EventPattern] = None,
        seed: int = 42,
    ):
        """
        Initialize dry run generator.

        Args:
            rate: Events per second (defaults to env var)
            pattern: Event pattern (defaults to env var)
            seed: Random seed for deterministic generation
        """
        self.rate = rate or get_dry_run_rate()
        self.pattern = pattern or get_dry_run_pattern()
        self.generator = MockEventGenerator(seed)
        self._running = False
        self._task: Optional[asyncio.Task] = None

        logger.info(
            "Dry run generator initialized",
            extra={
                "rate": self.rate,
                "pattern": self.pattern.value,
                "seed": seed,
            },
        )

    async def _generate_sequential(self) -> Dict[str, Any]:
        """Generate events in sequential pattern."""
        event_types = [EventType.TRADE, EventType.ORDER, EventType.POSITION]
        event_type = event_types[self.generator.event_count % len(event_types)]

        if event_type == EventType.TRADE:
            return self.generator.generate_trade()
        elif event_type == EventType.ORDER:
            return self.generator.generate_order()
        else:
            return self.generator.generate_position()

    async def _generate_random(self) -> Dict[str, Any]:
        """Generate events in random pattern."""
        event_type = self.generator.rng.choice(list(EventType))

        if event_type == EventType.TRADE:
            return self.generator.generate_trade()
        elif event_type == EventType.ORDER:
            return self.generator.generate_order()
        else:
            return self.generator.generate_position()

    async def _generate_burst(self) -> List[Dict[str, Any]]:
        """Generate burst of events."""
        burst_size = self.generator.rng.randint(3, 10)
        events = []

        for _ in range(burst_size):
            event = await self._generate_random()
            events.append(event)

        return events

    async def _event_loop(self) -> None:
        """Internal event generation loop."""
        logger.info(
            "Dry run event loop started",
            extra={
                "rate": self.rate,
                "pattern": self.pattern.value,
            },
        )

        try:
            while self._running:
                # Generate event(s) based on pattern
                if self.pattern == EventPattern.SEQUENTIAL:
                    event = await self._generate_sequential()
                    await self._emit_event(event)

                elif self.pattern == EventPattern.RANDOM:
                    event = await self._generate_random()
                    await self._emit_event(event)

                elif self.pattern == EventPattern.BURST:
                    events = await self._generate_burst()
                    for event in events:
                        await self._emit_event(event)

                # Wait based on rate
                await asyncio.sleep(1.0 / self.rate)

        except asyncio.CancelledError:
            logger.info("Dry run event loop cancelled")
            raise
        except Exception as e:
            logger.exception(
                "Dry run event loop error",
                extra={"error": str(e)},
            )

    async def _emit_event(self, event: Dict[str, Any]) -> None:
        """
        Emit mock event.

        Args:
            event: Event dictionary to emit
        """
        # TODO: Integrate with actual event bus
        # from risk_manager.events import get_event_bus
        # event_bus = get_event_bus()
        # await event_bus.emit(event)

        # For now, just log
        logger.info(
            f"DRY_RUN EVENT: {event['type']}",
            extra={
                "event": event,
                "event_id": event["event_id"],
                "event_type": event["type"],
            },
        )

    def start(self) -> None:
        """Start generating events."""
        if not is_dry_run_enabled():
            logger.warning("Dry run not enabled, not starting generator")
            return

        if self._running:
            logger.warning("Dry run generator already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._event_loop())

        logger.info("Dry run generator started")

    async def stop(self) -> None:
        """Stop generating events."""
        if not self._running:
            logger.warning("Dry run generator not running")
            return

        logger.info("Stopping dry run generator")

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(
            "Dry run generator stopped",
            extra={"total_events": self.generator.event_count},
        )

    @property
    def is_running(self) -> bool:
        """Check if generator is running."""
        return self._running

    @property
    def event_count(self) -> int:
        """Get total events generated."""
        return self.generator.event_count


# Global dry run instance
_global_dry_run: Optional[DryRunEventGenerator] = None


def start_global_dry_run() -> Optional[DryRunEventGenerator]:
    """
    Start global dry run generator.

    Returns:
        DryRunEventGenerator instance or None if disabled
    """
    if not is_dry_run_enabled():
        logger.info("Dry run mode not enabled")
        return None

    global _global_dry_run

    if _global_dry_run and _global_dry_run.is_running:
        logger.warning("Global dry run already running")
        return _global_dry_run

    _global_dry_run = DryRunEventGenerator()
    _global_dry_run.start()

    return _global_dry_run


async def stop_global_dry_run() -> None:
    """Stop global dry run generator."""
    global _global_dry_run

    if _global_dry_run:
        await _global_dry_run.stop()
        _global_dry_run = None


def get_global_dry_run() -> Optional[DryRunEventGenerator]:
    """Get global dry run instance."""
    return _global_dry_run
