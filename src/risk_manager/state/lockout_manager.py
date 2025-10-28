"""
MOD-002: Lockout Manager

Purpose: Centralized lockout state management for trading accounts.
Handles hard lockouts (until specific time) and cooldown timers (duration-based).

Features:
- Hard lockouts (until specific datetime)
- Cooldown timers (duration-based with auto-expiry)
- SQLite persistence (crash recovery)
- Background task for auto-expiry
- Integration with Timer Manager (MOD-003) when available
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from loguru import logger

from risk_manager.state.database import Database


class LockoutManager:
    """
    Centralized lockout state management.

    Manages trading account lockouts with:
    - Hard lockouts (until specific time)
    - Cooldown timers (duration-based)
    - Auto-expiry via background task
    - SQLite persistence for crash recovery

    Public API:
        - set_lockout(account_id, reason, until): Set hard lockout until datetime
        - set_cooldown(account_id, reason, duration_seconds): Set cooldown timer
        - is_locked_out(account_id): Check if account is locked
        - get_lockout_info(account_id): Get lockout details for display
        - get_remaining_time(account_id): Get remaining time for cooldown
        - clear_lockout(account_id): Remove lockout
        - check_expired_lockouts(): Auto-clear expired lockouts (background task)
        - load_lockouts_from_db(): Load lockouts from database on startup
        - start_background_task(): Start background expiry task
        - shutdown(): Gracefully shutdown manager
    """

    def __init__(
        self,
        database: Database,
        timer_manager: Optional[Any] = None
    ):
        """
        Initialize Lockout Manager.

        Args:
            database: Database instance for persistence
            timer_manager: Optional Timer Manager instance (MOD-003) for cooldowns
        """
        self.database = database
        self.timer_manager = timer_manager

        # In-memory lockout state for fast lookups
        # Format: {account_id: {"reason": str, "until": datetime, "type": str, "created_at": datetime}}
        self.lockout_state: dict[int, dict[str, Any]] = {}

        # Background task control
        self._running = False
        self._background_task: Optional[asyncio.Task] = None

        # Load lockouts from database on initialization
        self.load_lockouts_from_db()

        logger.info("Lockout Manager initialized")

    async def start(self) -> None:
        """
        Start the lockout manager.

        - Loads lockouts from database
        - Starts background expiry task
        """
        logger.info("Starting Lockout Manager")

        # Load persisted lockouts from database
        self.load_lockouts_from_db()

        # Start background task for auto-expiry
        self._running = True
        self._background_task = asyncio.create_task(self._lockout_loop())

        logger.success("Lockout Manager started")

    async def stop(self) -> None:
        """
        Stop the lockout manager.

        - Stops background expiry task
        - Persists state to database
        """
        logger.info("Stopping Lockout Manager")

        # Stop background task
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

        logger.success("Lockout Manager stopped")

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the lockout manager.

        Cancels all active timers and stops background task.
        """
        logger.info("Shutting down Lockout Manager")

        # Cancel all active timers via Timer Manager
        if self.timer_manager:
            for account_id, lockout in list(self.lockout_state.items()):
                if lockout.get('type') == 'cooldown':
                    try:
                        await self.timer_manager.cancel_timer(f"lockout_{account_id}")
                    except Exception as e:
                        logger.debug(f"Error cancelling timer for account {account_id}: {e}")

        # Stop background task
        await self.stop()

        logger.success("Lockout Manager shutdown complete")

    def set_lockout(
        self,
        account_id: int,
        reason: str,
        until: datetime
    ) -> None:
        """
        Set hard lockout until specific datetime.

        Used for:
        - Daily loss limits (until daily reset at 5:00 PM)
        - Session blocks (until session start)
        - Auth guard (permanent lockout)

        Args:
            account_id: TopstepX account ID
            reason: Human-readable lockout reason
            until: Datetime when lockout expires

        Example:
            set_lockout(123, "Daily loss limit hit", datetime(2025, 10, 27, 17, 0))
        """
        # Ensure until is timezone-aware (UTC)
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)

        # Update in-memory state
        self.lockout_state[account_id] = {
            "reason": reason,
            "until": until,
            "type": "hard_lockout",
            "created_at": datetime.now(timezone.utc)
        }

        # Persist to database
        self.database.execute_write(
            """
            INSERT OR REPLACE INTO lockouts
            (account_id, rule_id, reason, locked_at, expires_at, unlock_condition, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(account_id),
                "MANUAL",  # rule_id is generic for manual lockouts
                reason,
                datetime.now(timezone.utc).isoformat(),
                until.isoformat(),
                "TIME_BASED",
                1,  # active
                datetime.now(timezone.utc).isoformat()
            )
        )

        logger.warning(
            f"Account {account_id} locked until {until.isoformat()}: {reason}"
        )

    async def set_cooldown(
        self,
        account_id: int,
        reason: str,
        duration_seconds: int
    ) -> None:
        """
        Set cooldown timer (duration-based lockout).

        Used for:
        - Trade frequency limits (30 min cooldown)
        - Cooldown after loss (configurable duration)

        Auto-unlocks after duration expires via:
        1. Timer Manager callback (if available)
        2. Background task check (fallback)

        Args:
            account_id: TopstepX account ID
            reason: Human-readable lockout reason
            duration_seconds: Lockout duration in seconds

        Example:
            await set_cooldown(123, "Trade frequency limit", 1800)  # 30 min
        """
        until = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)

        # Update in-memory state
        self.lockout_state[account_id] = {
            "reason": reason,
            "until": until,
            "type": "cooldown",
            "duration": duration_seconds,
            "created_at": datetime.now(timezone.utc)
        }

        # Persist to database
        self.database.execute_write(
            """
            INSERT OR REPLACE INTO lockouts
            (account_id, rule_id, reason, locked_at, expires_at, unlock_condition, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(account_id),
                "COOLDOWN",
                reason,
                datetime.now(timezone.utc).isoformat(),
                until.isoformat(),
                f"DURATION_{duration_seconds}",
                1,  # active
                datetime.now(timezone.utc).isoformat()
            )
        )

        # Start timer callback if Timer Manager available
        if self.timer_manager:
            try:
                await self.timer_manager.start_timer(
                    name=f"lockout_{account_id}",
                    duration=duration_seconds,
                    callback=lambda: asyncio.create_task(self._clear_lockout_async(account_id))
                )
                logger.debug(f"Timer started for account {account_id} cooldown")
            except Exception as e:
                logger.warning(
                    f"Timer Manager unavailable, using background task fallback: {e}"
                )

        logger.warning(
            f"Account {account_id} cooldown for {duration_seconds}s: {reason}"
        )

    def is_locked_out(self, account_id: int) -> bool:
        """
        Check if account is currently locked out.

        Auto-clears expired lockouts when checked.

        Args:
            account_id: TopstepX account ID

        Returns:
            True if locked out, False otherwise

        Example:
            if lockout_manager.is_locked_out(123):
                logger.info("Account is locked out")
        """
        if account_id not in self.lockout_state:
            return False

        lockout = self.lockout_state[account_id]
        now = datetime.now(timezone.utc)

        # Ensure lockout['until'] is timezone-aware
        until = lockout['until']
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)

        # Check if lockout expired
        if now >= until:
            # Auto-clear expired lockout (synchronously)
            self.clear_lockout(account_id)
            return False

        return True

    def get_lockout_info(self, account_id: int) -> Optional[dict[str, Any]]:
        """
        Get lockout information for CLI display.

        Args:
            account_id: TopstepX account ID

        Returns:
            Dict with lockout details, or None if not locked out

        Example return:
            {
                "reason": "Daily loss limit hit",
                "until": datetime(2025, 10, 27, 17, 0),
                "remaining_seconds": 9845,
                "type": "hard_lockout",
                "created_at": datetime(2025, 10, 27, 14, 23)
            }
        """
        if not self.is_locked_out(account_id):
            return None

        lockout = self.lockout_state[account_id]
        now = datetime.now(timezone.utc)

        # Ensure until is timezone-aware
        until = lockout['until']
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)

        remaining = (until - now).total_seconds()

        return {
            "reason": lockout['reason'],
            "until": lockout['until'],
            "remaining_seconds": int(remaining),
            "type": lockout['type'],
            "created_at": lockout['created_at']
        }

    def get_remaining_time(self, account_id: int) -> int:
        """
        Get remaining time in seconds for cooldown timer.

        Args:
            account_id: TopstepX account ID

        Returns:
            Remaining seconds, or 0 if not locked or expired
        """
        if self.timer_manager and account_id in self.lockout_state:
            lockout = self.lockout_state[account_id]
            if lockout.get('type') == 'cooldown':
                try:
                    return self.timer_manager.get_remaining_time(f"lockout_{account_id}")
                except Exception:
                    # Fallback to manual calculation
                    pass

        # Manual calculation fallback
        info = self.get_lockout_info(account_id)
        if info:
            return info['remaining_seconds']
        return 0

    def clear_lockout(self, account_id: int) -> None:
        """
        Clear lockout for account (synchronous).

        Called by:
        - Background task (auto-expiry)
        - Manual unlock (admin)
        - Auto-clear on expiry check

        Args:
            account_id: TopstepX account ID
        """
        if account_id not in self.lockout_state:
            return

        lockout = self.lockout_state[account_id]
        reason = lockout['reason']
        del self.lockout_state[account_id]

        # Remove from database
        self.database.execute_write(
            "UPDATE lockouts SET active = 0 WHERE account_id = ?",
            (str(account_id),)
        )

        # Cancel timer if it's a cooldown
        if lockout.get('type') == 'cooldown' and self.timer_manager:
            try:
                # Cancel timer (now synchronous)
                self.timer_manager.cancel_timer(f"lockout_{account_id}")
            except Exception as e:
                logger.debug(f"Error cancelling timer for account {account_id}: {e}")

        logger.info(f"Lockout cleared for account {account_id}: {reason}")

    async def _clear_lockout_async(self, account_id: int) -> None:
        """
        Async wrapper for clear_lockout (for timer callbacks).

        Args:
            account_id: TopstepX account ID
        """
        self.clear_lockout(account_id)

    def check_expired_lockouts(self) -> None:
        """
        Check all lockouts and auto-clear expired ones (synchronous).

        Called every second by background task.
        """
        now = datetime.now(timezone.utc)
        expired_accounts = []

        for account_id, lockout in list(self.lockout_state.items()):
            until = lockout['until']
            if until.tzinfo is None:
                until = until.replace(tzinfo=timezone.utc)

            if now >= until:
                expired_accounts.append(account_id)

        # Clear expired lockouts
        for account_id in expired_accounts:
            self.clear_lockout(account_id)
            logger.info(f"Auto-cleared expired lockout for account {account_id}")

    def load_lockouts_from_db(self) -> None:
        """
        Load lockouts from database on startup (synchronous).

        Loads only active lockouts that haven't expired yet.
        Provides crash recovery - lockouts survive service restarts.
        """
        now = datetime.now(timezone.utc)

        rows = self.database.execute(
            """
            SELECT account_id, reason, expires_at, locked_at
            FROM lockouts
            WHERE active = 1 AND expires_at > ?
            """,
            (now.isoformat(),)
        )

        for row in rows:
            account_id = int(row['account_id'])
            reason = row['reason']
            expires_at = datetime.fromisoformat(row['expires_at'])
            locked_at = datetime.fromisoformat(row['locked_at'])

            # Ensure timezone-aware
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if locked_at.tzinfo is None:
                locked_at = locked_at.replace(tzinfo=timezone.utc)

            # Restore lockout state
            self.lockout_state[account_id] = {
                "reason": reason,
                "until": expires_at,
                "type": "hard_lockout",  # Assume hard lockout after restart
                "created_at": locked_at
            }

        logger.info(f"Loaded {len(self.lockout_state)} lockouts from database")

    async def start_background_task(self) -> None:
        """
        Start background task for checking expired lockouts.

        Runs check_expired_lockouts() every second.
        """
        self._running = True
        logger.debug("Lockout expiry background task started")

        while self._running:
            try:
                self.check_expired_lockouts()
            except Exception as e:
                logger.error(f"Error in lockout expiry task: {e}", exc_info=True)

            # Check every second
            await asyncio.sleep(1)

        logger.debug("Lockout expiry background task stopped")

    async def _lockout_loop(self) -> None:
        """
        Background task - runs every 1 second.

        Auto-clears expired lockouts.
        """
        await self.start_background_task()
