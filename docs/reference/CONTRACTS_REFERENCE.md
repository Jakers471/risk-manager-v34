# Contracts Reference - Risk Manager V34

**AUTHORITATIVE API CONTRACTS & INTERFACES**

**Purpose**: Prevent API mismatches between components. Use these exact signatures.

**Last Updated**: 2025-10-25

---

## Table of Contents

1. [Internal Interfaces](#internal-interfaces) (Our code → Our code)
2. [External Interfaces](#external-interfaces) (Our code → SDK)
3. [Schemas](#schemas) (Database, Events, Config)
4. [Event Contracts](#event-contracts)

---

## Internal Interfaces

**These are APIs within our codebase. Use exact signatures.**

### RiskRule (Base Class)

**File**: `src/risk_manager/rules/base.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from risk_manager.core.events import RiskEvent

class RiskRule(ABC):
    """Base class for all risk rules."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize rule with configuration.

        Args:
            config: Rule configuration dict from risk_config.yaml
        """
        self.config = config
        self.enabled = config.get('enabled', True)

    @abstractmethod
    async def evaluate(self, event: RiskEvent) -> bool:
        """
        Evaluate if rule is violated.

        Args:
            event: Risk event to evaluate

        Returns:
            True if rule violated, False otherwise
        """
        pass

    @abstractmethod
    async def enforce(self) -> None:
        """
        Execute enforcement action if rule violated.

        Called after evaluate() returns True.
        """
        pass

    def get_subscribed_events(self) -> list[str]:
        """
        Return list of event types this rule subscribes to.

        Returns:
            List of EventType enum values (as strings)
        """
        return []
```

---

### LockoutManager (MOD-002)

**File**: `src/risk_manager/state/lockout_manager.py`

```python
from datetime import datetime
from typing import Optional
from risk_manager.state.database import Database

class LockoutManager:
    """Manages account lockouts and countdown timers."""

    def __init__(self, db: Database):
        """
        Initialize lockout manager.

        Args:
            db: Database instance for persistence
        """
        self.db = db

    async def lock_account(
        self,
        account_id: str,
        reason: str,
        unlock_time: datetime,
        rule_id: str
    ) -> bool:
        """
        Lock account until specified time.

        Args:
            account_id: Account to lock
            reason: Human-readable reason (e.g., "Daily realized loss limit breached")
            unlock_time: When to auto-unlock (datetime with timezone)
            rule_id: Rule that triggered lockout (e.g., "RULE-003")

        Returns:
            True if locked successfully, False if already locked
        """
        pass

    async def unlock_account(self, account_id: str) -> bool:
        """
        Manually unlock account (admin only).

        NOTE: Per user guidance, manual unlock NOT used for trading lockouts.
        This is only for emergency/testing.

        Args:
            account_id: Account to unlock

        Returns:
            True if unlocked, False if not locked
        """
        pass

    async def is_locked(self, account_id: str) -> bool:
        """
        Check if account is currently locked.

        Args:
            account_id: Account to check

        Returns:
            True if locked, False otherwise
        """
        pass

    async def get_lockout_info(self, account_id: str) -> Optional[Dict]:
        """
        Get lockout information for account.

        Args:
            account_id: Account to query

        Returns:
            Dict with keys: reason, unlock_time, rule_id, locked_at
            None if not locked
        """
        pass

    async def get_time_remaining(self, account_id: str) -> Optional[float]:
        """
        Get seconds until unlock.

        Args:
            account_id: Account to query

        Returns:
            Seconds until unlock (float)
            None if not locked
        """
        pass
```

---

### TimerManager (MOD-003)

**File**: `src/risk_manager/state/timer_manager.py`

```python
from datetime import datetime, timedelta
from typing import Callable, Optional
from risk_manager.state.database import Database

class TimerManager:
    """Manages countdown timers and scheduled events."""

    def __init__(self, db: Database):
        """
        Initialize timer manager.

        Args:
            db: Database instance for persistence
        """
        self.db = db

    async def create_timer(
        self,
        timer_id: str,
        duration: timedelta,
        callback: Callable,
        auto_restart: bool = False
    ) -> str:
        """
        Create countdown timer.

        Args:
            timer_id: Unique identifier for timer
            duration: How long until callback fires
            callback: Async function to call when timer expires
            auto_restart: If True, restart timer after firing

        Returns:
            Timer ID
        """
        pass

    async def cancel_timer(self, timer_id: str) -> bool:
        """
        Cancel running timer.

        Args:
            timer_id: Timer to cancel

        Returns:
            True if canceled, False if not found
        """
        pass

    async def get_time_remaining(self, timer_id: str) -> Optional[float]:
        """
        Get seconds until timer fires.

        Args:
            timer_id: Timer to query

        Returns:
            Seconds remaining (float)
            None if timer not found
        """
        pass

    async def is_session_active(self) -> bool:
        """
        Check if current time is within session hours.

        Uses config/timers.yaml session_hours configuration.

        Returns:
            True if within session hours, False otherwise
        """
        pass
```

---

### ResetScheduler (MOD-004)

**File**: `src/risk_manager/state/reset_scheduler.py`

```python
from datetime import datetime
from typing import Callable
from risk_manager.state.database import Database

class ResetScheduler:
    """Manages daily reset at configured time."""

    def __init__(self, db: Database, reset_time: str, timezone: str):
        """
        Initialize reset scheduler.

        Args:
            db: Database instance
            reset_time: Time to reset (HH:MM format, e.g., "17:00")
            timezone: IANA timezone (e.g., "America/Chicago")
        """
        self.db = db
        self.reset_time = reset_time
        self.timezone = timezone

    async def start(self) -> None:
        """
        Start reset scheduler.

        Sets up daily job to run reset() at configured time.
        """
        pass

    async def stop(self) -> None:
        """
        Stop reset scheduler.
        """
        pass

    async def reset(self) -> None:
        """
        Perform daily reset.

        Resets:
        - Realized P&L to 0
        - Unrealized P&L to 0
        - Trade counts
        - Violation counters
        - Lockouts (if configured to unlock at reset)
        """
        pass

    def get_next_reset_time(self) -> datetime:
        """
        Get next reset time.

        Returns:
            Next reset datetime (timezone-aware)
        """
        pass
```

---

### PnLTracker

**File**: `src/risk_manager/state/pnl_tracker.py`

```python
from risk_manager.state.database import Database
from typing import Dict

class PnLTracker:
    """Tracks realized and unrealized P&L."""

    def __init__(self, db: Database):
        """
        Initialize P&L tracker.

        Args:
            db: Database instance for persistence
        """
        self.db = db

    async def update_realized_pnl(
        self,
        account_id: str,
        symbol: str,
        pnl: float
    ) -> None:
        """
        Update realized P&L after trade closes.

        Args:
            account_id: Account ID
            symbol: Instrument symbol (e.g., "MNQ")
            pnl: Realized P&L for this trade (positive or negative)
        """
        pass

    async def update_unrealized_pnl(
        self,
        account_id: str,
        symbol: str,
        position_id: str,
        unrealized_pnl: float
    ) -> None:
        """
        Update unrealized P&L from quote data.

        Args:
            account_id: Account ID
            symbol: Instrument symbol
            position_id: Position ID
            unrealized_pnl: Current unrealized P&L (floating)
        """
        pass

    async def get_realized_pnl(self, account_id: str) -> float:
        """
        Get total realized P&L for account today.

        Args:
            account_id: Account ID

        Returns:
            Total realized P&L (positive or negative)
        """
        pass

    async def get_unrealized_pnl(self, account_id: str) -> float:
        """
        Get total unrealized P&L for account.

        Args:
            account_id: Account ID

        Returns:
            Total unrealized P&L across all positions
        """
        pass

    async def get_combined_pnl(self, account_id: str) -> float:
        """
        Get combined realized + unrealized P&L.

        Args:
            account_id: Account ID

        Returns:
            realized_pnl + unrealized_pnl
        """
        pass
```

---

## External Interfaces

**These are Project-X-Py SDK APIs. Use exact signatures from SDK v3.5.9+**

### TradingSuite (SDK)

**From**: `project_x_py.trading_suite`

```python
from project_x_py import TradingSuite
from typing import List, Dict

# Initialize
suite = await TradingSuite.create(
    api_key="your_api_key",
    api_secret="your_api_secret",
    environment="sim"  # or "live"
)

# Close all positions
orders: List[Order] = await suite.close_all_positions(
    account_id="sim-account-123"
)

# Close specific position
order: Order = await suite.close_position(
    position_id="pos-abc-123"
)

# Get positions
positions: List[Position] = await suite.get_positions(
    account_id="sim-account-123"
)

# Get account info
account: Account = await suite.get_account(
    account_id="sim-account-123"
)
```

---

### QuoteManager (SDK)

**From**: `project_x_py.quote_manager`

```python
from project_x_py import QuoteManager

# Get quote for symbol
quote: Quote = await quote_manager.get_quote(
    symbol="MNQ"
)

# Subscribe to quote updates
await quote_manager.subscribe(
    symbols=["MNQ", "ES", "NQ"],
    callback=on_quote_update
)

# Quote object structure
class Quote:
    symbol: str              # "MNQ"
    bid: float              # Current bid price
    ask: float              # Current ask price
    last: float             # Last traded price
    timestamp: datetime     # Quote timestamp
```

---

### EventBus (SDK)

**From**: `project_x_py.event_bus`

```python
from project_x_py import EventBus, EventType

# Subscribe to events
event_bus.subscribe(
    event_type=EventType.TRADE_EXECUTED,
    callback=on_trade_executed
)

# Event types available
EventType.TRADE_EXECUTED       # Trade closed
EventType.POSITION_UPDATED     # Position changed
EventType.ORDER_FILLED         # Order executed
EventType.QUOTE_UPDATED        # Quote price changed
EventType.ACCOUNT_UPDATED      # Account info changed
```

---

## Schemas

**Database tables, event structures, config structures.**

### Database Schema

**File**: `src/risk_manager/state/database.py`

#### violations table
```sql
CREATE TABLE violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,           -- e.g., "RULE-003"
    timestamp REAL NOT NULL,          -- Unix timestamp
    severity TEXT NOT NULL,           -- 'WARNING', 'CRITICAL'
    message TEXT,                     -- Human-readable description
    details TEXT,                     -- JSON with additional info
    resolved BOOLEAN DEFAULT 0
);
```

#### lockouts table
```sql
CREATE TABLE lockouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL UNIQUE,
    rule_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    locked_at REAL NOT NULL,          -- Unix timestamp
    unlock_at REAL NOT NULL,          -- Unix timestamp
    is_active BOOLEAN DEFAULT 1
);
```

#### pnl_tracking table
```sql
CREATE TABLE pnl_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    position_id TEXT,                 -- NULL for realized
    realized_pnl REAL DEFAULT 0.0,
    unrealized_pnl REAL DEFAULT 0.0,
    timestamp REAL NOT NULL,
    date TEXT NOT NULL                -- YYYY-MM-DD for daily grouping
);
```

#### timers table
```sql
CREATE TABLE timers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timer_id TEXT NOT NULL UNIQUE,
    start_time REAL NOT NULL,
    duration_seconds REAL NOT NULL,
    callback_data TEXT,               -- JSON with callback info
    auto_restart BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1
);
```

---

### Event Schema

**File**: `src/risk_manager/core/events.py`

#### RiskEvent
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class EventType(Enum):
    """Risk event types."""
    TRADE_EXECUTED = "trade_executed"
    POSITION_UPDATED = "position_updated"
    QUOTE_UPDATED = "quote_updated"
    ACCOUNT_UPDATED = "account_updated"
    RULE_VIOLATED = "rule_violated"
    LOCKOUT_TRIGGERED = "lockout_triggered"
    TIMER_EXPIRED = "timer_expired"

@dataclass
class RiskEvent:
    """Risk event data structure."""
    event_type: EventType           # NOTE: event_type not type!
    account_id: str
    symbol: str
    timestamp: datetime
    data: dict                      # Event-specific data
```

---

### Config Schema

**File**: `config/risk_config.yaml`

```yaml
# Example configuration structure
rules:
  daily_realized_loss:
    enabled: true
    limit: -1000.0              # Negative for loss
    enforcement: "hard_lockout"
    lockout_until: "daily_reset"

  daily_unrealized_loss:
    enabled: true
    limit: -500.0
    enforcement: "trade_by_trade"
    # No lockout for trade-by-trade

  max_unrealized_profit:
    enabled: true
    target: 1000.0              # Positive for profit
    enforcement: "trade_by_trade"
```

**File**: `config/timers.yaml`

```yaml
daily_reset:
  time: "17:00"                 # 5:00 PM
  timezone: "America/Chicago"   # Central Time
  enabled: true

session_hours:
  start: "08:30"
  end: "15:00"
  timezone: "America/Chicago"
  allowed_days: [0, 1, 2, 3, 4]  # Mon-Fri

holidays:
  - "2025-12-25"  # Christmas
  - "2025-01-01"  # New Year
```

---

## Event Contracts

**What events are emitted and what data they contain.**

### TRADE_EXECUTED Event

**Emitted by**: SDK EventBridge
**Consumed by**: Rules (RULE-003, RULE-013)

```python
RiskEvent(
    event_type=EventType.TRADE_EXECUTED,
    account_id="sim-account-123",
    symbol="MNQ",
    timestamp=datetime.now(),
    data={
        "trade_id": "trade-abc-123",
        "side": "BUY" | "SELL",
        "quantity": 2,
        "price": 18450.50,
        "realized_pnl": -125.00,    # P&L for this trade
        "position_closed": True      # If position fully closed
    }
)
```

---

### POSITION_UPDATED Event

**Emitted by**: SDK EventBridge
**Consumed by**: Rules (RULE-002, RULE-008)

```python
RiskEvent(
    event_type=EventType.POSITION_UPDATED,
    account_id="sim-account-123",
    symbol="MNQ",
    timestamp=datetime.now(),
    data={
        "position_id": "pos-abc-123",
        "side": "LONG" | "SHORT",
        "quantity": 2,
        "entry_price": 18450.50,
        "current_price": 18455.00,
        "unrealized_pnl": 9.00      # (18455 - 18450.50) * 2 * $2
    }
)
```

---

### QUOTE_UPDATED Event

**Emitted by**: SDK EventBridge (from QuoteManager)
**Consumed by**: Rules (RULE-004, RULE-005)

```python
RiskEvent(
    event_type=EventType.QUOTE_UPDATED,
    account_id="sim-account-123",
    symbol="MNQ",
    timestamp=datetime.now(),
    data={
        "bid": 18450.00,
        "ask": 18450.50,
        "last": 18450.25,
        "timestamp": datetime.now()
    }
)
```

---

### RULE_VIOLATED Event

**Emitted by**: RiskEngine
**Consumed by**: Monitoring, logging

```python
RiskEvent(
    event_type=EventType.RULE_VIOLATED,
    account_id="sim-account-123",
    symbol="MNQ",
    timestamp=datetime.now(),
    data={
        "rule_id": "RULE-003",
        "rule_name": "Daily Realized Loss",
        "severity": "CRITICAL",
        "message": "Daily realized loss limit breached: -$1050.00 <= -$1000.00",
        "enforcement_action": "hard_lockout",
        "lockout_until": "2025-10-25T17:00:00-06:00"
    }
)
```

---

## Contract Multipliers

**For unrealized P&L calculation.**

**Formula**: `unrealized_pnl = (current_price - entry_price) * contracts * multiplier`

| Symbol | Name | Multiplier |
|--------|------|------------|
| MNQ | Micro E-mini NASDAQ-100 | $2 |
| ES | E-mini S&P 500 | $50 |
| NQ | E-mini NASDAQ-100 | $20 |
| RTY | E-mini Russell 2000 | $50 |
| YM | E-mini Dow | $5 |
| CL | Crude Oil | $1000 |
| GC | Gold | $100 |

**Source**: `docs/specifications/unified/quote-data-integration.md`

---

## API Version Requirements

**Project-X-Py SDK**: v3.5.9 or higher

**Check version**:
```bash
pip show project-x-py
```

**Upgrade if needed**:
```bash
pip install --upgrade project-x-py
```

---

## Common Patterns

### Pattern 1: Rule Implementation

```python
from risk_manager.rules.base import RiskRule
from risk_manager.core.events import RiskEvent, EventType

class DailyRealizedLoss(RiskRule):
    """RULE-003: Daily Realized Loss (HARD LOCKOUT)."""

    def __init__(self, config, pnl_tracker, lockout_manager):
        super().__init__(config)
        self.pnl_tracker = pnl_tracker
        self.lockout_manager = lockout_manager
        self.limit = config['limit']  # e.g., -1000.0

    async def evaluate(self, event: RiskEvent) -> bool:
        """Check if realized + unrealized hits limit."""
        combined_pnl = await self.pnl_tracker.get_combined_pnl(event.account_id)
        return combined_pnl <= self.limit  # Breached if <= -1000

    async def enforce(self) -> None:
        """Close all positions + trigger lockout."""
        # Close all positions (SDK)
        await self.trading_integration.close_all_positions(self.account_id)

        # Trigger lockout (our code)
        unlock_time = self.get_next_reset_time()  # From config
        await self.lockout_manager.lock_account(
            account_id=self.account_id,
            reason="Daily realized loss limit breached",
            unlock_time=unlock_time,
            rule_id="RULE-003"
        )

    def get_subscribed_events(self) -> list[str]:
        """Subscribe to trades and position updates."""
        return [
            EventType.TRADE_EXECUTED.value,
            EventType.POSITION_UPDATED.value
        ]
```

---

### Pattern 2: SDK Integration

```python
from project_x_py import TradingSuite

class TradingIntegration:
    """Wrapper around SDK for enforcement actions."""

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.suite = None

    async def connect(self) -> None:
        """Connect to SDK."""
        self.suite = await TradingSuite.create(
            api_key=self.api_key,
            api_secret=self.api_secret,
            environment="sim"
        )

    async def close_all_positions(self, account_id: str) -> List[Order]:
        """Close all positions (HARD LOCKOUT enforcement)."""
        return await self.suite.close_all_positions(account_id)

    async def close_position(self, position_id: str) -> Order:
        """Close specific position (TRADE-BY-TRADE enforcement)."""
        return await self.suite.close_position(position_id)
```

---

## Verification Checklist

**Before implementing, verify**:

- [ ] Using correct parameter names (e.g., `event_type` not `type`)
- [ ] Using correct method signatures from this file
- [ ] Using correct SDK version (v3.5.9+)
- [ ] Using correct database schema (table/column names)
- [ ] Using correct event structure
- [ ] Using correct config structure
- [ ] Using async/await for all SDK calls
- [ ] Using async/await for all database calls

---

**Last Updated**: 2025-10-25
**Maintained By**: Update when adding new interfaces or changing signatures
**Authority**: This is the SINGLE SOURCE OF TRUTH for all contracts
