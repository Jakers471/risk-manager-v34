"""
SQLite Database Manager

Handles database connection, schema creation, and migrations.
Thread-safe connection management.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
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
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
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

        Yields:
            SQLite connection with row factory

        Example:
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM daily_pnl")
        """
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

    def close(self) -> None:
        """Close database (for cleanup)."""
        logger.info("Database closed")
