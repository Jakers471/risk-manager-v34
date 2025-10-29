"""
SQLite Database Manager

Handles database connection, schema creation, and migrations.
Thread-safe connection management.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Generator

from loguru import logger


class Database:
    """
    SQLite database manager for state persistence.

    Provides:
    - Schema creation and migrations
    - Thread-safe connection pooling
    - Transaction management
    - Query helpers
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str | Path):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file or ":memory:" for in-memory
        """
        self.db_path = Path(db_path) if db_path != ":memory:" else db_path
        self._persistent_conn = None  # For in-memory databases

        # For in-memory databases, keep a persistent connection
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:")
            self._persistent_conn.row_factory = sqlite3.Row
            logger.debug("Using persistent in-memory database connection")
        else:
            self._ensure_directory()

        self._init_schema()
        logger.info(f"Database initialized at {self.db_path}")

    def _ensure_directory(self) -> None:
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_schema(self) -> None:
        """Initialize database schema if not exists."""
        with self.connection() as conn:
            cursor = conn.cursor()

            # Schema version tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            """)

            # Check current version
            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cursor.fetchone()
            current_version = row[0] if row else 0

            if current_version < self.SCHEMA_VERSION:
                self._apply_migrations(conn, current_version)

    def _apply_migrations(self, conn: sqlite3.Connection, from_version: int) -> None:
        """
        Apply database migrations.

        Args:
            conn: Database connection
            from_version: Current schema version
        """
        cursor = conn.cursor()

        if from_version < 1:
            logger.info("Applying schema migration: v1 (initial schema)")
            self._migrate_to_v1(cursor)
            cursor.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (1, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()

    def _migrate_to_v1(self, cursor: sqlite3.Cursor) -> None:
        """
        Apply v1 schema (initial schema).

        Tables:
        - daily_pnl: Track daily realized P&L per account
        - lockouts: Track hard lockout states
        - timers: Track cooldown timers
        - trades: Trade history for frequency tracking
        """
        # Daily P&L tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_pnl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                date TEXT NOT NULL,
                realized_pnl REAL NOT NULL DEFAULT 0.0,
                trade_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(account_id, date)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_daily_pnl_account_date ON daily_pnl(account_id, date)"
        )

        # Lockout states (hard lockouts until condition)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lockouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                locked_at TEXT NOT NULL,
                expires_at TEXT,
                unlock_condition TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                UNIQUE(account_id, rule_id) ON CONFLICT REPLACE
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_lockouts_account_active ON lockouts(account_id, active)"
        )

        # Timer states (cooldown timers with countdown)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                started_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                UNIQUE(account_id, rule_id) ON CONFLICT REPLACE
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timers_account_active ON timers(account_id, active)"
        )

        # Trade history (for frequency limits)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                trade_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                realized_pnl REAL,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(account_id, trade_id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_trades_account_timestamp ON trades(account_id, timestamp)"
        )

        # Reset log (for MOD-004 Reset Scheduler)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reset_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                reset_type TEXT NOT NULL,
                reset_time TEXT NOT NULL,
                triggered_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account_id, reset_type, reset_time)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reset_log_account ON reset_log(account_id, reset_type)"
        )

        logger.success("Schema v1 applied successfully")

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection context manager.

        For in-memory databases, returns the persistent connection.
        For file-based databases, creates a new connection per call.

        Yields:
            SQLite connection with row factory

        Example:
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM daily_pnl")
        """
        # Use persistent connection for in-memory databases
        if self._persistent_conn:
            yield self._persistent_conn
        else:
            # Create new connection for file-based databases
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            try:
                yield conn
            finally:
                conn.close()

    def execute(
        self, query: str, params: tuple[Any, ...] | dict[str, Any] | None = None
    ) -> list[sqlite3.Row]:
        """
        Execute a query and return results.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of result rows
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def execute_one(
        self, query: str, params: tuple[Any, ...] | dict[str, Any] | None = None
    ) -> sqlite3.Row | None:
        """
        Execute a query and return first result.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            First result row or None
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()

    def execute_write(
        self, query: str, params: tuple[Any, ...] | dict[str, Any] | None = None
    ) -> int:
        """
        Execute a write query (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Last row ID or number of affected rows
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid or cursor.rowcount

    def add_trade(
        self,
        account_id: str,
        trade_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        realized_pnl: float | None = None,
        timestamp: datetime | None = None,
    ) -> int:
        """
        Add a trade to the database.

        Args:
            account_id: Account identifier
            trade_id: Unique trade identifier
            symbol: Trading symbol
            side: Trade side ('buy' or 'sell')
            quantity: Number of contracts
            price: Execution price
            realized_pnl: Realized P&L (optional)
            timestamp: Trade timestamp (defaults to now)

        Returns:
            Row ID of inserted trade
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Ensure timestamp is ISO format string
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = timestamp

        query = """
            INSERT INTO trades (
                account_id, trade_id, symbol, side, quantity, price,
                realized_pnl, timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        return self.execute_write(
            query,
            (
                account_id,
                trade_id,
                symbol,
                side,
                quantity,
                price,
                realized_pnl,
                timestamp_str,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def get_trade_count(self, account_id: str, window: int) -> int:
        """
        Get count of trades within rolling time window.

        Args:
            account_id: Account identifier
            window: Time window in seconds (e.g., 60 for last minute)

        Returns:
            Number of trades in the window
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=window)
        cutoff_str = cutoff_time.isoformat()

        query = """
            SELECT COUNT(*) as count
            FROM trades
            WHERE account_id = ? AND timestamp >= ?
        """

        result = self.execute_one(query, (account_id, cutoff_str))
        return result["count"] if result else 0

    def get_session_trade_count(self, account_id: str) -> int:
        """
        Get count of trades for current session (today).

        Args:
            account_id: Account identifier

        Returns:
            Number of trades today
        """
        today = datetime.now(timezone.utc).date().isoformat()

        query = """
            SELECT COUNT(*) as count
            FROM trades
            WHERE account_id = ?
            AND DATE(timestamp) = ?
        """

        result = self.execute_one(query, (account_id, today))
        return result["count"] if result else 0

    def close(self) -> None:
        """Close database (for cleanup)."""
        if self._persistent_conn:
            self._persistent_conn.close()
            self._persistent_conn = None
            logger.debug("Closed persistent in-memory connection")
        logger.info("Database closed")
