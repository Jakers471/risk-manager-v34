"""
P&L Tracker - Daily Realized P&L Tracking

Tracks daily realized P&L with SQLite persistence for crash recovery.
Thread-safe, handles multiple accounts.
"""

from datetime import date, datetime
from typing import Dict

from loguru import logger

from risk_manager.state.database import Database


class PnLTracker:
    """
    Tracks daily realized P&L with SQLite persistence.

    Features:
    - Daily P&L aggregation per account
    - Trade count tracking
    - Crash recovery (persists to SQLite)
    - Multi-account support
    - Daily reset capability
    """

    def __init__(self, db: Database):
        """
        Initialize P&L tracker.

        Args:
            db: Database instance for persistence
        """
        self.db = db
        logger.info("PnLTracker initialized")

    def add_trade_pnl(
        self,
        account_id: str,
        pnl: float,
        trade_date: date | None = None,
    ) -> float:
        """
        Add trade P&L to daily total.

        Args:
            account_id: Account identifier
            pnl: Realized P&L from trade (positive = profit, negative = loss)
            trade_date: Date of trade (defaults to today)

        Returns:
            New daily P&L total

        Example:
            tracker.add_trade_pnl("ACCOUNT-001", -150.0)  # Add $150 loss
            tracker.add_trade_pnl("ACCOUNT-001", 80.0)    # Add $80 profit
        """
        if trade_date is None:
            trade_date = date.today()

        date_str = trade_date.isoformat()
        now = datetime.utcnow().isoformat()

        # Check if record exists for this account/date
        row = self.db.execute_one(
            """
            SELECT id, realized_pnl, trade_count
            FROM daily_pnl
            WHERE account_id = ? AND date = ?
            """,
            (account_id, date_str),
        )

        if row:
            # Update existing record
            new_pnl = row["realized_pnl"] + pnl
            new_count = row["trade_count"] + 1

            self.db.execute_write(
                """
                UPDATE daily_pnl
                SET realized_pnl = ?,
                    trade_count = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (new_pnl, new_count, now, row["id"]),
            )

            logger.debug(
                f"Updated P&L for {account_id} on {date_str}: "
                f"{row['realized_pnl']:.2f} → {new_pnl:.2f} (trade: {pnl:+.2f})"
            )

            return new_pnl

        else:
            # Insert new record
            self.db.execute_write(
                """
                INSERT INTO daily_pnl (account_id, date, realized_pnl, trade_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (account_id, date_str, pnl, 1, now, now),
            )

            logger.debug(
                f"Created P&L record for {account_id} on {date_str}: {pnl:+.2f}"
            )

            return pnl

    def get_daily_pnl(self, account_id: str, trade_date: date | None = None) -> float:
        """
        Get daily realized P&L for account.

        Args:
            account_id: Account identifier
            trade_date: Date to query (defaults to today)

        Returns:
            Daily realized P&L (0.0 if no trades)

        Example:
            pnl = tracker.get_daily_pnl("ACCOUNT-001")
            if pnl <= -500.0:
                # Daily loss limit hit!
        """
        if trade_date is None:
            trade_date = date.today()

        date_str = trade_date.isoformat()

        row = self.db.execute_one(
            """
            SELECT realized_pnl
            FROM daily_pnl
            WHERE account_id = ? AND date = ?
            """,
            (account_id, date_str),
        )

        return row["realized_pnl"] if row else 0.0

    def get_trade_count(self, account_id: str, trade_date: date | None = None) -> int:
        """
        Get number of trades for account on date.

        Args:
            account_id: Account identifier
            trade_date: Date to query (defaults to today)

        Returns:
            Number of trades (0 if no trades)

        Example:
            count = tracker.get_trade_count("ACCOUNT-001")
            if count >= 50:
                # Daily frequency limit hit!
        """
        if trade_date is None:
            trade_date = date.today()

        date_str = trade_date.isoformat()

        row = self.db.execute_one(
            """
            SELECT trade_count
            FROM daily_pnl
            WHERE account_id = ? AND date = ?
            """,
            (account_id, date_str),
        )

        return row["trade_count"] if row else 0

    def reset_daily_pnl(self, account_id: str, trade_date: date | None = None) -> None:
        """
        Reset daily P&L for account (called at 5:00 PM reset).

        Args:
            account_id: Account identifier
            trade_date: Date to reset (defaults to today)

        Example:
            # Daily reset at 5 PM
            tracker.reset_daily_pnl("ACCOUNT-001")
        """
        if trade_date is None:
            trade_date = date.today()

        date_str = trade_date.isoformat()
        now = datetime.utcnow().isoformat()

        self.db.execute_write(
            """
            UPDATE daily_pnl
            SET realized_pnl = 0.0,
                trade_count = 0,
                updated_at = ?
            WHERE account_id = ? AND date = ?
            """,
            (now, account_id, date_str),
        )

        logger.info(f"Reset daily P&L for {account_id} on {date_str}")

    def get_all_daily_pnls(self, trade_date: date | None = None) -> Dict[str, float]:
        """
        Get daily P&L for all accounts.

        Args:
            trade_date: Date to query (defaults to today)

        Returns:
            Dictionary mapping account_id → daily P&L

        Example:
            all_pnls = tracker.get_all_daily_pnls()
            for account_id, pnl in all_pnls.items():
                print(f"{account_id}: ${pnl:.2f}")
        """
        if trade_date is None:
            trade_date = date.today()

        date_str = trade_date.isoformat()

        rows = self.db.execute(
            """
            SELECT account_id, realized_pnl
            FROM daily_pnl
            WHERE date = ?
            """,
            (date_str,),
        )

        return {row["account_id"]: row["realized_pnl"] for row in rows}

    def get_stats(
        self, account_id: str, trade_date: date | None = None
    ) -> Dict[str, float | int]:
        """
        Get complete stats for account/date.

        Args:
            account_id: Account identifier
            trade_date: Date to query (defaults to today)

        Returns:
            Dictionary with realized_pnl and trade_count

        Example:
            stats = tracker.get_stats("ACCOUNT-001")
            print(f"P&L: ${stats['realized_pnl']:.2f}, Trades: {stats['trade_count']}")
        """
        if trade_date is None:
            trade_date = date.today()

        date_str = trade_date.isoformat()

        row = self.db.execute_one(
            """
            SELECT realized_pnl, trade_count
            FROM daily_pnl
            WHERE account_id = ? AND date = ?
            """,
            (account_id, date_str),
        )

        if row:
            return {
                "realized_pnl": row["realized_pnl"],
                "trade_count": row["trade_count"],
            }
        else:
            return {"realized_pnl": 0.0, "trade_count": 0}
