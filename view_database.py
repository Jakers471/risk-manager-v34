#!/usr/bin/env python3
"""
Database Viewer - View lockouts, timers, P&L tracking, and trades

Usage:
    python view_database.py              # Show all data
    python view_database.py lockouts     # Show only lockouts
    python view_database.py pnl          # Show only P&L data
    python view_database.py trades       # Show only trades
    python view_database.py timers       # Show only timers
"""

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def view_lockouts(cursor):
    """Show active lockouts."""
    print('\nACTIVE LOCKOUTS:')
    print('=' * 80)

    cursor.execute('''
        SELECT id, account_id, rule_id, reason, locked_at, expires_at, active
        FROM lockouts
        WHERE active = 1
        ORDER BY locked_at DESC
    ''')
    rows = cursor.fetchall()

    if not rows:
        print('  No active lockouts')
    else:
        for row in rows:
            now = datetime.now(timezone.utc)
            expires_str = row['expires_at'].replace('Z', '+00:00')
            expires = datetime.fromisoformat(expires_str)
            remaining = (expires - now).total_seconds()

            print(f'\n  Lockout ID: {row["id"]}')
            print(f'    Account:    {row["account_id"]}')
            print(f'    Rule:       {row["rule_id"] or "N/A"}')
            print(f'    Reason:     {row["reason"]}')
            print(f'    Locked at:  {row["locked_at"]}')
            print(f'    Expires at: {row["expires_at"]}')

            if remaining > 0:
                hours = int(remaining / 3600)
                minutes = int((remaining % 3600) / 60)
                print(f'    Remaining:  {int(remaining)}s ({hours}h {minutes}m)')
            else:
                print(f'    Remaining:  EXPIRED ({int(-remaining)}s ago)')

            print(f'    Active:     {"YES" if row["active"] else "NO"}')

    print(f'\n  Total active lockouts: {len(rows)}')
    print('=' * 80)


def view_all_lockouts(cursor):
    """Show all lockouts (including inactive)."""
    print('\nALL LOCKOUTS (HISTORY):')
    print('=' * 80)

    cursor.execute('''
        SELECT id, account_id, rule_id, reason, locked_at, expires_at, active
        FROM lockouts
        ORDER BY locked_at DESC
        LIMIT 20
    ''')
    rows = cursor.fetchall()

    if not rows:
        print('  No lockouts in database')
    else:
        for row in rows:
            status = "[ACTIVE]" if row["active"] else "[EXPIRED]"
            print(f'\n  {status} | ID: {row["id"]} | Account: {row["account_id"]}')
            print(f'    Rule:       {row["rule_id"] or "N/A"}')
            print(f'    Reason:     {row["reason"]}')
            print(f'    Locked at:  {row["locked_at"]}')
            print(f'    Expires at: {row["expires_at"]}')

    print(f'\n  Showing last {min(len(rows), 20)} lockouts')
    print('=' * 80)


def view_pnl(cursor):
    """Show P&L tracking data."""
    print('\nDAILY P&L TRACKING:')
    print('=' * 80)

    cursor.execute('''
        SELECT account_id, date, realized_pnl, trade_count, updated_at
        FROM daily_pnl
        ORDER BY date DESC
        LIMIT 10
    ''')
    rows = cursor.fetchall()

    if not rows:
        print('  No P&L data')
    else:
        for row in rows:
            pnl = float(row["realized_pnl"])
            sign = "+" if pnl >= 0 else ""
            print(f'\n  Account: {row["account_id"]} | Date: {row["date"]}')
            print(f'    Realized P&L: ${sign}{pnl:,.2f}')
            print(f'    Trade Count:  {row["trade_count"]}')
            print(f'    Last Update:  {row["updated_at"]}')

    print(f'\n  Total records: {len(rows)}')
    print('=' * 80)


def view_trades(cursor):
    """Show recent trades."""
    print('\nRECENT TRADES:')
    print('=' * 80)

    cursor.execute('''
        SELECT id, account_id, symbol, side, quantity, price, realized_pnl, timestamp
        FROM trades
        ORDER BY timestamp DESC
        LIMIT 20
    ''')
    rows = cursor.fetchall()

    if not rows:
        print('  No trades in database')
    else:
        for row in rows:
            pnl = float(row["realized_pnl"]) if row["realized_pnl"] else 0.0
            sign = "+" if pnl >= 0 else ""
            print(f'\n  Trade ID: {row["id"]} | {row["symbol"]} {row["side"]} {row["quantity"]} @ ${row["price"]:,.2f}')
            print(f'    Account:      {row["account_id"]}')
            print(f'    Realized P&L: ${sign}{pnl:,.2f}')
            print(f'    Timestamp:    {row["timestamp"]}')

    print(f'\n  Showing last {min(len(rows), 20)} trades')
    print('=' * 80)


def view_timers(cursor):
    """Show active timers."""
    print('\nACTIVE TIMERS:')
    print('=' * 80)

    cursor.execute('''
        SELECT id, account_id, rule_id, reason, started_at, expires_at, duration_seconds, active
        FROM timers
        WHERE active = 1
        ORDER BY started_at DESC
    ''')
    rows = cursor.fetchall()

    if not rows:
        print('  No active timers')
    else:
        for row in rows:
            now = datetime.now(timezone.utc)
            expires_str = row['expires_at'].replace('Z', '+00:00')
            expires = datetime.fromisoformat(expires_str)
            remaining = (expires - now).total_seconds()

            print(f'\n  Timer ID: {row["id"]}')
            print(f'    Account:   {row["account_id"]}')
            print(f'    Rule:      {row["rule_id"] or "N/A"}')
            print(f'    Reason:    {row["reason"]}')
            print(f'    Duration:  {row["duration_seconds"]}s')
            print(f'    Started:   {row["started_at"]}')
            print(f'    Expires:   {row["expires_at"]}')

            if remaining > 0:
                print(f'    Remaining: {int(remaining)}s ({int(remaining/60)}m)')
            else:
                print(f'    Remaining: EXPIRED ({int(-remaining)}s ago)')

            print(f'    Active:    {"YES" if row["active"] else "NO"}')

    print(f'\n  Total active timers: {len(rows)}')
    print('=' * 80)


def main():
    """Main entry point."""
    db_path = Path(__file__).parent / 'data' / 'risk_state.db'

    if not db_path.exists():
        print(f'ERROR: Database not found: {db_path}')
        return

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print('\n' + '=' * 80)
    print('  RISK MANAGER V34 - DATABASE VIEWER')
    print('=' * 80)
    print(f'  Database: {db_path}')
    print(f'  Size:     {db_path.stat().st_size / 1024:.1f} KB')
    print('=' * 80)

    # Check command line arguments
    if len(sys.argv) > 1:
        view_type = sys.argv[1].lower()
        if view_type == 'lockouts':
            view_lockouts(cursor)
            view_all_lockouts(cursor)
        elif view_type == 'pnl':
            view_pnl(cursor)
        elif view_type == 'trades':
            view_trades(cursor)
        elif view_type == 'timers':
            view_timers(cursor)
        else:
            print(f'\nERROR: Unknown view type: {view_type}')
            print('       Valid options: lockouts, pnl, trades, timers')
    else:
        # Show everything
        view_lockouts(cursor)
        view_timers(cursor)
        view_pnl(cursor)
        view_trades(cursor)

    print()
    conn.close()


if __name__ == '__main__':
    main()
