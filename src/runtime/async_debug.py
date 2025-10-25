"""
Asyncio task debugging and diagnostics utility.

Provides detailed diagnostics for asyncio tasks when enabled via ASYNC_DEBUG=1.
Dumps pending tasks, their states, and stack traces to runtime_trace.log.

Features:
- Dumps all pending asyncio tasks
- Includes task names, states, and stack traces
- Controlled via ASYNC_DEBUG environment variable
- Writes to runtime_trace.log for analysis
- Minimal overhead when disabled

Author: Risk Manager Team
Date: 2025-10-23
"""

import asyncio
import logging
import os
import sys
import traceback
from datetime import UTC, datetime
from typing import Any, List

logger = logging.getLogger(__name__)

# Runtime trace log file
TRACE_LOG_FILE = "runtime_trace.log"


def is_async_debug_enabled() -> bool:
    """
    Check if async debugging is enabled.

    Returns:
        True if ASYNC_DEBUG=1 is set
    """
    return os.getenv("ASYNC_DEBUG", "0") == "1"


def get_task_info(task: asyncio.Task) -> dict[str, Any]:
    """
    Extract detailed information from an asyncio task.

    Args:
        task: Asyncio task to inspect

    Returns:
        Dictionary with task details
    """
    info: dict[str, Any] = {
        "name": task.get_name(),
        "done": task.done(),
        "cancelled": task.cancelled(),
    }

    # Get coroutine info
    coro = task.get_coro()
    if coro:
        info["coroutine"] = f"{coro.__name__}"
        info["coroutine_qualname"] = getattr(coro, "__qualname__", "unknown")

    # Get stack trace if not done
    if not task.done():
        try:
            stack = task.get_stack()
            info["stack_depth"] = len(stack)
            info["stack_trace"] = "".join(traceback.format_stack(stack[0]))
        except Exception as e:
            info["stack_error"] = str(e)

    # Get exception if done and failed
    if task.done() and not task.cancelled():
        try:
            exception = task.exception()
            if exception:
                info["exception"] = str(exception)
                info["exception_type"] = type(exception).__name__
        except Exception as e:
            info["exception_error"] = str(e)

    return info


def dump_async_tasks(write_to_file: bool = True) -> List[dict[str, Any]]:
    """
    Dump all pending asyncio tasks with detailed diagnostics.

    Args:
        write_to_file: Write results to runtime_trace.log

    Returns:
        List of task information dictionaries
    """
    if not is_async_debug_enabled():
        logger.debug("Async debug not enabled, skipping task dump")
        return []

    timestamp = datetime.now(UTC).isoformat()
    logger.info(
        "Dumping asyncio tasks",
        extra={
            "timestamp": timestamp,
            "enabled": True,
        },
    )

    try:
        # Get all tasks
        all_tasks = asyncio.all_tasks()
        task_count = len(all_tasks)

        logger.info(
            f"Found {task_count} asyncio tasks",
            extra={
                "task_count": task_count,
                "timestamp": timestamp,
            },
        )

        # Collect task information
        tasks_info = []
        for task in all_tasks:
            try:
                info = get_task_info(task)
                tasks_info.append(info)
            except Exception as e:
                logger.exception(
                    "Error getting task info",
                    extra={
                        "task": str(task),
                        "error": str(e),
                    },
                )

        # Write to trace log if enabled
        if write_to_file:
            write_trace_log(timestamp, tasks_info)

        return tasks_info

    except Exception as e:
        logger.exception(
            "Error dumping async tasks",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return []


def write_trace_log(timestamp: str, tasks_info: List[dict[str, Any]]) -> None:
    """
    Write task dump to runtime_trace.log.

    Args:
        timestamp: Timestamp of dump
        tasks_info: List of task information dictionaries
    """
    try:
        with open(TRACE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"ASYNC TASK DUMP - {timestamp}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Total Tasks: {len(tasks_info)}\n\n")

            for idx, info in enumerate(tasks_info, 1):
                f.write(f"\n--- Task {idx}/{len(tasks_info)} ---\n")
                f.write(f"Name: {info.get('name', 'unknown')}\n")
                f.write(f"Coroutine: {info.get('coroutine', 'unknown')}\n")
                f.write(f"Done: {info.get('done', False)}\n")
                f.write(f"Cancelled: {info.get('cancelled', False)}\n")

                if "stack_depth" in info:
                    f.write(f"Stack Depth: {info['stack_depth']}\n")

                if "exception" in info:
                    f.write(f"Exception: {info['exception_type']}: {info['exception']}\n")

                if "stack_trace" in info:
                    f.write(f"\nStack Trace:\n{info['stack_trace']}\n")

                f.write("\n")

            f.write(f"\n{'='*80}\n\n")

        logger.info(
            f"Task dump written to {TRACE_LOG_FILE}",
            extra={
                "file": TRACE_LOG_FILE,
                "task_count": len(tasks_info),
            },
        )

    except Exception as e:
        logger.exception(
            "Error writing trace log",
            extra={
                "file": TRACE_LOG_FILE,
                "error": str(e),
            },
        )


async def periodic_task_dump(interval_seconds: float = 10.0) -> None:
    """
    Periodically dump async tasks for monitoring.

    Args:
        interval_seconds: Interval between dumps
    """
    if not is_async_debug_enabled():
        logger.info("Periodic task dump disabled (ASYNC_DEBUG not set)")
        return

    logger.info(
        "Starting periodic task dump",
        extra={"interval_seconds": interval_seconds},
    )

    try:
        while True:
            dump_async_tasks(write_to_file=True)
            await asyncio.sleep(interval_seconds)

    except asyncio.CancelledError:
        logger.info("Periodic task dump cancelled")
        raise
    except Exception as e:
        logger.exception(
            "Error in periodic task dump",
            extra={"error": str(e)},
        )


def configure_async_debug_logging() -> None:
    """Configure enhanced logging when async debug is enabled."""
    if is_async_debug_enabled():
        # Enable asyncio debug mode
        asyncio.get_event_loop().set_debug(True)

        # Configure logging to show debug messages
        logging.getLogger("asyncio").setLevel(logging.DEBUG)

        logger.info(
            "Async debug mode enabled",
            extra={
                "trace_file": TRACE_LOG_FILE,
                "asyncio_debug": True,
            },
        )


# Auto-configure on import if enabled
if is_async_debug_enabled():
    configure_async_debug_logging()
