"""
Background heartbeat task for system health monitoring.

Emits periodic heartbeat messages to logs for easy filtering and monitoring.
Starts automatically with the engine and runs in the background.

Features:
- Emits "⏰ HEARTBEAT" every 1 second
- Easy to filter in log analysis
- Minimal overhead
- Graceful shutdown support

Author: Risk Manager Team
Date: 2025-10-23
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Optional

logger = logging.getLogger(__name__)


class HeartbeatTask:
    """
    Background async task that emits periodic heartbeat messages.

    Automatically starts with engine and emits heartbeat every second
    for health monitoring and log analysis.
    """

    def __init__(self, interval_seconds: float = 1.0):
        """
        Initialize heartbeat task.

        Args:
            interval_seconds: Interval between heartbeats (default: 1.0)
        """
        self.interval = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._heartbeat_count = 0
        self._start_time: Optional[datetime] = None

    async def _heartbeat_loop(self) -> None:
        """Internal heartbeat loop."""
        self._start_time = datetime.now(UTC)
        logger.info(
            "Heartbeat task started",
            extra={
                "interval_seconds": self.interval,
                "start_time": self._start_time.isoformat(),
            },
        )

        try:
            while self._running:
                self._heartbeat_count += 1
                current_time = datetime.now(UTC)

                # Calculate uptime
                uptime_seconds = (
                    (current_time - self._start_time).total_seconds()
                    if self._start_time
                    else 0
                )

                # Emit heartbeat with emoji for easy filtering
                logger.info(
                    "⏰ HEARTBEAT",
                    extra={
                        "heartbeat_count": self._heartbeat_count,
                        "uptime_seconds": uptime_seconds,
                        "timestamp": current_time.isoformat(),
                    },
                )

                # Wait for next interval
                await asyncio.sleep(self.interval)

        except asyncio.CancelledError:
            logger.info(
                "Heartbeat task cancelled",
                extra={
                    "total_heartbeats": self._heartbeat_count,
                    "final_uptime": uptime_seconds if self._start_time else 0,
                },
            )
            raise
        except Exception as e:
            logger.exception(
                "Heartbeat task error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "heartbeat_count": self._heartbeat_count,
                },
            )
            raise

    def start(self) -> None:
        """Start the heartbeat task."""
        if self._running:
            logger.warning("Heartbeat task already running")
            return

        self._running = True
        self._heartbeat_count = 0
        self._task = asyncio.create_task(self._heartbeat_loop())

        logger.info(
            "Heartbeat task initialized",
            extra={"interval_seconds": self.interval},
        )

    async def stop(self) -> None:
        """Stop the heartbeat task gracefully."""
        if not self._running:
            logger.warning("Heartbeat task not running")
            return

        logger.info(
            "Stopping heartbeat task",
            extra={"total_heartbeats": self._heartbeat_count},
        )

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(
            "Heartbeat task stopped",
            extra={"total_heartbeats": self._heartbeat_count},
        )

    @property
    def is_running(self) -> bool:
        """Check if heartbeat is currently running."""
        return self._running

    @property
    def heartbeat_count(self) -> int:
        """Get total number of heartbeats emitted."""
        return self._heartbeat_count

    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds since start."""
        if not self._start_time:
            return 0.0
        return (datetime.now(UTC) - self._start_time).total_seconds()


# Global heartbeat instance for engine integration
_global_heartbeat: Optional[HeartbeatTask] = None


def start_global_heartbeat(interval_seconds: float = 1.0) -> HeartbeatTask:
    """
    Start global heartbeat task.

    Args:
        interval_seconds: Heartbeat interval

    Returns:
        HeartbeatTask instance
    """
    global _global_heartbeat

    if _global_heartbeat and _global_heartbeat.is_running:
        logger.warning("Global heartbeat already running")
        return _global_heartbeat

    _global_heartbeat = HeartbeatTask(interval_seconds)
    _global_heartbeat.start()

    return _global_heartbeat


async def stop_global_heartbeat() -> None:
    """Stop global heartbeat task."""
    global _global_heartbeat

    if _global_heartbeat:
        await _global_heartbeat.stop()
        _global_heartbeat = None


def get_global_heartbeat() -> Optional[HeartbeatTask]:
    """Get global heartbeat instance."""
    return _global_heartbeat
