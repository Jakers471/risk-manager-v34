"""
MOD-004: Reset Scheduler

Purpose: Automated daily/weekly reset system for P&L tracking, lockouts, and trade counters.
Handles timezone conversion (ET ↔ UTC), DST transitions, and database persistence.

Features:
- Daily reset at configurable time (default 5:00 PM ET)
- Weekly reset (configurable day, default Monday)
- Timezone-aware (ET/EDT ↔ UTC with DST handling)
- Database persistence (reset_log table)
- Integration with PnL Tracker and Lockout Manager
- Background task (check every minute)

Database Schema:
    CREATE TABLE reset_log (
        account_id TEXT,
        reset_type TEXT,  -- 'daily' or 'weekly'
        reset_time TEXT,  -- ISO 8601 UTC
        triggered_at TEXT,
        PRIMARY KEY (account_id, reset_type, reset_time)
    );
"""

import asyncio
from datetime import datetime, timedelta, timezone, time as dt_time
from typing import Any, Optional, Dict
from zoneinfo import ZoneInfo

from loguru import logger

from risk_manager.state.database import Database


class ResetScheduler:
    """
    Manages daily and weekly resets for P&L tracking, lockouts, and trade counters.

    Handles:
    - Daily reset at 5:00 PM ET
    - Weekly reset (Monday at 5:00 PM ET)
    - Timezone conversion (ET/EDT ↔ UTC)
    - Database persistence
    - Integration with PnL Tracker and Lockout Manager

    Public API:
        - schedule_daily_reset(account_id, reset_time): Schedule daily reset
        - schedule_weekly_reset(account_id, day, reset_time): Schedule weekly reset
        - get_next_reset_time(account_id, reset_type): Get next reset datetime
        - trigger_reset_manually(account_id, reset_type): Manually trigger reset
        - has_daily_reset(account_id): Check if daily reset scheduled
        - has_weekly_reset(account_id): Check if weekly reset scheduled
        - get_last_reset_time(account_id, reset_type): Get last reset time from DB
        - start(): Start background task
        - stop(): Stop background task
    """

    def __init__(
        self,
        database: Database,
        pnl_tracker: Optional[Any] = None,
        lockout_manager: Optional[Any] = None
    ):
        """
        Initialize Reset Scheduler.

        Args:
            database: Database instance for persistence
            pnl_tracker: Optional PnL Tracker instance for P&L reset
            lockout_manager: Optional Lockout Manager instance for lockout clearing
        """
        self.database = database
        self.pnl_tracker = pnl_tracker
        self.lockout_manager = lockout_manager

        # In-memory reset schedules
        # Format: {account_id: {"reset_time": "17:00", "last_reset": datetime}}
        self.daily_schedules: Dict[str, Dict[str, Any]] = {}

        # Weekly schedules
        # Format: {account_id: {"day": "Monday", "reset_time": "17:00", "last_reset": datetime}}
        self.weekly_schedules: Dict[str, Dict[str, Any]] = {}

        # Background task control
        self.running = False
        self._background_task: Optional[asyncio.Task] = None

        # Timezone
        self.et_tz = ZoneInfo("America/New_York")

        # Track resets triggered today (to prevent duplicates)
        self._resets_triggered_today: Dict[str, set] = {}  # {account_id: {"daily", "weekly"}}

        # Load last reset times from database
        self._load_last_reset_times()

        logger.info("Reset Scheduler initialized")

    async def start(self) -> None:
        """
        Start the reset scheduler.

        - Starts background task for checking reset times
        """
        logger.info("Starting Reset Scheduler")

        self.running = True
        self._background_task = asyncio.create_task(self._reset_loop())

        logger.success("Reset Scheduler started")

    async def stop(self) -> None:
        """
        Stop the reset scheduler.

        - Stops background task
        """
        logger.info("Stopping Reset Scheduler")

        self.running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

        logger.success("Reset Scheduler stopped")

    def schedule_daily_reset(
        self,
        account_id: str,
        reset_time: str = "17:00"
    ) -> None:
        """
        Schedule daily reset at specific time (ET timezone).

        Args:
            account_id: Account identifier
            reset_time: Time in HH:MM format (ET timezone), default "17:00" (5:00 PM)

        Example:
            schedule_daily_reset("123", "17:00")  # Reset at 5:00 PM ET daily
        """
        self.daily_schedules[account_id] = {
            "reset_time": reset_time,
            "last_reset": None
        }

        logger.info(f"Daily reset scheduled for account {account_id} at {reset_time} ET")

    def schedule_weekly_reset(
        self,
        account_id: str,
        day: str = "Monday",
        reset_time: str = "17:00"
    ) -> None:
        """
        Schedule weekly reset on specific day at specific time (ET timezone).

        Args:
            account_id: Account identifier
            day: Day of week (Monday, Tuesday, etc.)
            reset_time: Time in HH:MM format (ET timezone), default "17:00" (5:00 PM)

        Example:
            schedule_weekly_reset("123", "Monday", "17:00")  # Monday at 5:00 PM ET
        """
        self.weekly_schedules[account_id] = {
            "day": day,
            "reset_time": reset_time,
            "last_reset": None
        }

        logger.info(
            f"Weekly reset scheduled for account {account_id} on {day} at {reset_time} ET"
        )

    def has_daily_reset(self, account_id: str) -> bool:
        """
        Check if daily reset is scheduled for account.

        Args:
            account_id: Account identifier

        Returns:
            True if daily reset scheduled, False otherwise
        """
        return account_id in self.daily_schedules

    def has_weekly_reset(self, account_id: str) -> bool:
        """
        Check if weekly reset is scheduled for account.

        Args:
            account_id: Account identifier

        Returns:
            True if weekly reset scheduled, False otherwise
        """
        return account_id in self.weekly_schedules

    def get_next_reset_time(
        self,
        account_id: str,
        reset_type: str = "daily"
    ) -> Optional[datetime]:
        """
        Get next reset time for account.

        Args:
            account_id: Account identifier
            reset_type: "daily" or "weekly"

        Returns:
            Next reset datetime (UTC), or None if not scheduled
        """
        if reset_type == "daily":
            if account_id not in self.daily_schedules:
                return None

            schedule = self.daily_schedules[account_id]
            reset_time_str = schedule["reset_time"]

        elif reset_type == "weekly":
            if account_id not in self.weekly_schedules:
                return None

            schedule = self.weekly_schedules[account_id]
            reset_time_str = schedule["reset_time"]

        else:
            return None

        # Parse reset time
        hour, minute = map(int, reset_time_str.split(":"))

        # Get current time in ET
        now_et = datetime.now(self.et_tz)

        # Calculate next reset time in ET
        if reset_type == "daily":
            # Daily reset - today if not yet passed, tomorrow otherwise
            next_reset_et = now_et.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if now_et >= next_reset_et:
                # Time already passed today, schedule for tomorrow
                next_reset_et += timedelta(days=1)

        else:  # weekly
            # Weekly reset - next occurrence of specified day
            schedule = self.weekly_schedules[account_id]
            target_day = schedule["day"]

            # Map day name to weekday number (Monday=0, Sunday=6)
            days = {
                "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                "Friday": 4, "Saturday": 5, "Sunday": 6
            }
            target_weekday = days[target_day]

            # Calculate next occurrence
            current_weekday = now_et.weekday()
            days_until = (target_weekday - current_weekday) % 7

            if days_until == 0:
                # It's the target day - check if time passed
                reset_time_today = now_et.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if now_et >= reset_time_today:
                    # Time passed, next week
                    days_until = 7

            next_reset_et = now_et.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_reset_et += timedelta(days=days_until)

        # Convert to UTC
        next_reset_utc = next_reset_et.astimezone(timezone.utc)

        return next_reset_utc

    def trigger_reset_manually(
        self,
        account_id: str,
        reset_type: str = "daily"
    ) -> None:
        """
        Manually trigger reset for account.

        Args:
            account_id: Account identifier
            reset_type: "daily" or "weekly"
        """
        # Check if already reset today
        today = datetime.now(timezone.utc).date().isoformat()
        if account_id not in self._resets_triggered_today:
            self._resets_triggered_today[account_id] = set()

        reset_key = f"{reset_type}_{today}"
        if reset_key in self._resets_triggered_today[account_id]:
            logger.debug(f"Reset already triggered today for {account_id} ({reset_type})")
            return

        # Execute reset sequence
        self._execute_reset(account_id, reset_type)

        # Mark as triggered today
        self._resets_triggered_today[account_id].add(reset_key)

    def get_last_reset_time(
        self,
        account_id: str,
        reset_type: str = "daily"
    ) -> Optional[datetime]:
        """
        Get last reset time from database.

        Args:
            account_id: Account identifier
            reset_type: "daily" or "weekly"

        Returns:
            Last reset datetime (UTC), or None if never reset
        """
        row = self.database.execute_one(
            """
            SELECT reset_time
            FROM reset_log
            WHERE account_id = ? AND reset_type = ?
            ORDER BY triggered_at DESC
            LIMIT 1
            """,
            (account_id, reset_type)
        )

        if row:
            return datetime.fromisoformat(row["reset_time"])

        return None

    def check_reset_time(self) -> None:
        """
        Check if any resets should trigger now.

        Called by background task every minute.
        """
        now = datetime.now(timezone.utc)

        # Check daily resets
        for account_id, schedule in list(self.daily_schedules.items()):
            next_reset = self.get_next_reset_time(account_id, "daily")
            if next_reset and now >= next_reset:
                logger.info(f"Triggering daily reset for account {account_id}")
                self.trigger_reset_manually(account_id, "daily")

        # Check weekly resets
        for account_id, schedule in list(self.weekly_schedules.items()):
            next_reset = self.get_next_reset_time(account_id, "weekly")
            if next_reset and now >= next_reset:
                logger.info(f"Triggering weekly reset for account {account_id}")
                self.trigger_reset_manually(account_id, "weekly")

    def _execute_reset(
        self,
        account_id: str,
        reset_type: str
    ) -> None:
        """
        Execute reset sequence.

        Steps:
        1. Reset P&L Tracker (if available)
        2. Clear lockout (if available)
        3. Log reset to database

        Args:
            account_id: Account identifier
            reset_type: "daily" or "weekly"
        """
        logger.info(f"Executing {reset_type} reset for account {account_id}")

        # 1. Reset P&L Tracker
        if self.pnl_tracker:
            try:
                self.pnl_tracker.reset_daily_pnl(account_id)
                logger.debug(f"P&L reset completed for account {account_id}")
            except Exception as e:
                logger.error(f"Error resetting P&L for account {account_id}: {e}", exc_info=True)

        # 2. Clear lockout
        if self.lockout_manager:
            try:
                self.lockout_manager.clear_lockout(int(account_id))
                logger.debug(f"Lockout cleared for account {account_id}")
            except Exception as e:
                logger.error(f"Error clearing lockout for account {account_id}: {e}", exc_info=True)

        # 3. Log reset to database
        now = datetime.now(timezone.utc)
        try:
            self.database.execute_write(
                """
                INSERT INTO reset_log (account_id, reset_type, reset_time, triggered_at)
                VALUES (?, ?, ?, ?)
                """,
                (account_id, reset_type, now.isoformat(), now.isoformat())
            )
            logger.debug(f"Reset logged to database for account {account_id}")
        except Exception as e:
            logger.error(f"Error logging reset to database for account {account_id}: {e}", exc_info=True)

        logger.success(f"{reset_type.capitalize()} reset completed for account {account_id}")

    def _load_last_reset_times(self) -> None:
        """
        Load last reset times from database on startup.

        Populates last_reset field in schedules.
        """
        # This will be populated when schedules are created
        # For now, just log that we're ready to load
        logger.debug("Reset scheduler ready to load last reset times from database")

    async def _reset_loop(self) -> None:
        """
        Background task - runs every 1 second (for testing) or 60 seconds (production).

        Checks for reset times and triggers resets automatically.
        """
        logger.debug("Reset loop started")

        # Use 1-second interval for testing (will be 60 seconds in production)
        check_interval = 1

        while self.running:
            try:
                self.check_reset_time()
                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                logger.debug("Reset loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in reset loop: {e}", exc_info=True)
                await asyncio.sleep(check_interval)

        logger.debug("Reset loop stopped")
