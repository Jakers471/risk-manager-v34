"""
Timer Manager (MOD-003)

Provides countdown timers for cooldowns, session checks, and scheduled tasks.
Manages timer infrastructure with callbacks for automatic expiry.

Key Features:
- In-memory timer storage (no DB persistence)
- Background task checking every 1 second
- Callback execution (sync or async)
- Automatic cleanup after expiry
- Error handling with proper logging
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

from loguru import logger


class TimerManager:
    """
    Manages countdown timers with automatic callback execution.

    Timers are in-memory only and do not persist across restarts.
    Background task runs every 1 second to check for expired timers.

    Example:
        ```python
        manager = TimerManager()
        await manager.start()

        # Set a 30-minute cooldown
        await manager.start_timer(
            name="lockout_123",
            duration=1800,
            callback=lambda: print("Cooldown expired!")
        )

        # Check remaining time
        remaining = manager.get_remaining_time("lockout_123")

        # Cancel timer
        await manager.cancel_timer("lockout_123")

        await manager.stop()
        ```
    """

    def __init__(self):
        """Initialize the timer manager."""
        self.timers: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._background_task: Optional[asyncio.Task] = None

        logger.info("TimerManager initialized")

    async def start(self) -> None:
        """Start the timer manager and background task."""
        if self.running:
            logger.warning("TimerManager already running")
            return

        self.running = True
        await self.start_background_task()
        logger.info("TimerManager started")

    async def stop(self) -> None:
        """Stop the timer manager and background task."""
        if not self.running:
            return

        self.running = False

        # Cancel background task
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            self._background_task = None

        logger.info("TimerManager stopped")

    async def start_timer(
        self,
        name: str,
        duration: int,
        callback: Callable[[], Any]
    ) -> None:
        """
        Start a countdown timer with automatic callback execution.

        Args:
            name: Unique timer name/identifier
            duration: Timer duration in seconds (must be >= 0)
            callback: Function to call when timer expires (sync or async)

        Raises:
            ValueError: If duration is negative or callback is None
        """
        # Validation
        if duration < 0:
            raise ValueError(f"Timer duration cannot be negative, got {duration}")

        if callback is None:
            raise ValueError("Timer callback cannot be None")

        # Calculate expiry time
        expires_at = datetime.now() + timedelta(seconds=duration)

        # Store timer
        self.timers[name] = {
            "expires_at": expires_at,
            "callback": callback,
            "duration": duration,
            "created_at": datetime.now()
        }

        logger.info(
            f"Timer started: {name} (duration={duration}s, expires={expires_at.strftime('%H:%M:%S')})"
        )

        # Handle zero-duration timers (execute immediately)
        if duration == 0:
            await self._execute_callback(name)

    def get_remaining_time(self, name: str) -> int:
        """
        Get remaining time for a timer.

        Args:
            name: Timer name

        Returns:
            Remaining seconds (0 if timer doesn't exist or expired)
        """
        timer = self.timers.get(name)
        if not timer:
            return 0

        now = datetime.now()
        remaining = (timer["expires_at"] - now).total_seconds()

        return max(0, int(remaining))

    def cancel_timer(self, name: str) -> None:
        """
        Cancel a timer before it expires.

        Args:
            name: Timer name

        Note:
            Idempotent - no error if timer doesn't exist
        """
        if name in self.timers:
            self.timers.pop(name)
            logger.info(f"Timer cancelled: {name}")
        else:
            logger.debug(f"Timer cancel requested but not found: {name}")

    def has_timer(self, name: str) -> bool:
        """
        Check if a timer exists.

        Args:
            name: Timer name

        Returns:
            True if timer exists, False otherwise
        """
        return name in self.timers

    async def start_background_task(self) -> None:
        """Start the background task that checks timers."""
        if self._background_task:
            logger.warning("Background task already running")
            return

        self._background_task = asyncio.create_task(self._timer_loop())
        logger.debug("Background task started")

    async def check_timers(self) -> None:
        """
        Check for expired timers and execute their callbacks.

        This method is called by the background task every 1 second.
        Can also be called manually for testing.
        """
        now = datetime.now()

        # Find expired timers
        expired = [
            name for name, timer in self.timers.items()
            if now >= timer["expires_at"]
        ]

        # Execute callbacks for expired timers
        for name in expired:
            await self._execute_callback(name)

    async def _timer_loop(self) -> None:
        """
        Background task - runs every 1 second.

        Checks for expired timers and executes their callbacks.
        """
        logger.debug("Timer loop started")

        while self.running:
            try:
                await self.check_timers()
                await asyncio.sleep(1)  # 1-second intervals
            except asyncio.CancelledError:
                logger.debug("Timer loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in timer loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Continue after error

        logger.debug("Timer loop stopped")

    async def _execute_callback(self, name: str) -> None:
        """
        Execute a timer's callback and remove the timer.

        Args:
            name: Timer name
        """
        timer = self.timers.get(name)
        if not timer:
            return

        callback = timer["callback"]

        try:
            # Execute callback (may be sync or async)
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()

            logger.debug(f"Timer callback executed: {name}")

        except Exception as e:
            logger.error(
                f"Timer callback error for {name}: {e}",
                exc_info=True
            )

        finally:
            # Always remove timer after execution (success or failure)
            self.timers.pop(name, None)
            logger.info(f"Timer expired and removed: {name}")

    def get_all_timers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active timers (for debugging/monitoring).

        Returns:
            Dictionary of timer name -> timer info
        """
        return self.timers.copy()

    def get_timer_count(self) -> int:
        """
        Get the number of active timers.

        Returns:
            Count of active timers
        """
        return len(self.timers)
