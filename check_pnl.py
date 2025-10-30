#!/usr/bin/env python3
"""Quick script to check daily P&L from database."""

import sqlite3
from datetime import date
from pathlib import Path

# Connect to database
db_path = Path("data/risk_manager.db")
if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row  # Enable column access by name
cursor = conn.cursor()

# Query today's P&L
today = date.today().isoformat()
cursor.execute(
    """
    SELECT account_id, date, realized_pnl, trade_count, updated_at
    FROM daily_pnl
    WHERE date = ?
    ORDER BY updated_at DESC
    """,
    (today,)
)

rows = cursor.fetchall()

print("=" * 80)
print(f"📊 Daily P&L Tracker - {today}")
print("=" * 80)

if not rows:
    print("✅ No trades today yet (P&L = $0.00)")
else:
    for row in rows:
        pnl = row["realized_pnl"]
        count = row["trade_count"]
        updated = row["updated_at"][:19]  # Trim microseconds

        # Color code P&L
        if pnl > 0:
            status = "📈 PROFIT"
        elif pnl < 0:
            status = "📉 LOSS"
        else:
            status = "➖ FLAT"

        print(f"\nAccount: {row['account_id']}")
        print(f"  {status}: ${pnl:+,.2f}")
        print(f"  Trades: {count}")
        print(f"  Updated: {updated}")

# Show all-time P&L
cursor.execute(
    """
    SELECT date, realized_pnl, trade_count
    FROM daily_pnl
    ORDER BY date DESC
    LIMIT 10
    """
)

history = cursor.fetchall()

if len(history) > 1 or (len(history) == 1 and history[0]["date"] != today):
    print("\n" + "=" * 80)
    print("📅 Recent History (Last 10 Days)")
    print("=" * 80)

    for row in history:
        pnl = row["realized_pnl"]
        emoji = "📈" if pnl > 0 else "📉" if pnl < 0 else "➖"
        print(f"{row['date']}: {emoji} ${pnl:+,.2f} ({row['trade_count']} trades)")

conn.close()

print("\n" + "=" * 80)
print("💡 TIP: Run this anytime with: python check_pnl.py")
print("=" * 80)
