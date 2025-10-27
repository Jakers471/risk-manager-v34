# State Tracking Schemas

**Version**: 1.0
**Last Updated**: 2025-10-27
**Status**: Canonical Reference
**Purpose**: Defines state management schemas for tracking positions, orders, P&L, and violations

---

## Document Purpose

This document defines the **persistent state schemas** used by the Risk Manager to track:
- Active positions across all accounts and symbols
- Active orders and their status
- Cumulative P&L (realized and unrealized)
- Rule violations and cooldown timers
- Daily statistics and limits

These schemas represent the **in-memory state** and **database persistence** layer.

---

## Table of Contents

1. [Position State](#position-state)
2. [Order State](#order-state)
3. [P&L State](#pnl-state)
4. [Violation State](#violation-state)
5. [Daily Statistics State](#daily-statistics-state)
6. [Timer State](#timer-state)

---

## Position State

### PositionState

**Purpose**: Track all active positions across accounts and symbols

**Schema**:
```python
@dataclass
class PositionState:
    """State tracking for an active position."""

    # Identifiers
    contract_id: str           # e.g., "CON.F.US.MNQ.Z25"
    symbol: str                # e.g., "MNQ"
    account_id: int

    # Position Details (from POSITION_UPDATED)
    size: int                  # Signed: positive=long, negative=short
    average_price: float       # Average entry price (SDK: averagePrice)

    # P&L Tracking
    unrealized_pnl: float      # Current unrealized P&L
    realized_pnl: float        # Cumulative realized P&L for this position

    # Stop Loss Tracking (for RULE-008)
    has_stop_loss: bool        # True if stop-loss order exists
    stop_price: float | None   # Stop-loss price (from ORDER_PLACED)
    stop_order_id: int | None  # Order ID of stop-loss order

    # Timestamps
    opened_at: datetime        # When position was opened
    updated_at: datetime       # Last update time

    # Metadata
    raw_data: dict             # Original SDK data
```

**Key Points**:
- **One record per active position** (keyed by `contract_id` and `account_id`)
- `size` is signed: no need for separate `side` field
- `average_price` matches SDK field name (NOT `entry_price`)
- Stop-loss tracking fields support RULE-008
- Deleted when position closes (size → 0)

**State Transitions**:
```
POSITION_OPENED → Create PositionState record
POSITION_UPDATED → Update size, average_price, unrealized_pnl
ORDER_PLACED (type=3) → Set has_stop_loss=True, stop_price, stop_order_id
POSITION_CLOSED → Delete PositionState record
```

**Database Schema** (SQLite):
```sql
CREATE TABLE position_state (
    contract_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    account_id INTEGER NOT NULL,
    size INTEGER NOT NULL,
    average_price REAL NOT NULL,
    unrealized_pnl REAL NOT NULL,
    realized_pnl REAL NOT NULL,
    has_stop_loss INTEGER NOT NULL DEFAULT 0,
    stop_price REAL,
    stop_order_id INTEGER,
    opened_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    raw_data TEXT,
    PRIMARY KEY (contract_id, account_id)
);
```

---

## Order State

### OrderState

**Purpose**: Track all active orders and their current status

**Schema**:
```python
@dataclass
class OrderState:
    """State tracking for an active order."""

    # Identifiers
    order_id: int
    symbol: str
    account_id: int
    contract_id: str

    # Order Details (from ORDER_PLACED)
    side: int                  # 1=BUY, 2=SELL
    quantity: int              # Total quantity
    order_type: int            # 1=MARKET, 2=LIMIT, 3=STOP
    status: int                # 1=PENDING, 2=FILLED, 3=CANCELLED, 4=REJECTED, 6=PENDING_TRIGGER

    # Prices
    limit_price: float | None
    stop_price: float | None   # CRITICAL for stop-loss tracking

    # Fill Tracking
    filled_quantity: int       # Contracts filled so far
    remaining_quantity: int    # Contracts still pending

    # Timestamps
    placed_at: datetime
    updated_at: datetime

    # Metadata
    raw_data: dict
```

**Key Points**:
- **One record per active order** (keyed by `order_id`)
- `stop_price` field is CRITICAL for RULE-008
- Track fill progress with `filled_quantity` and `remaining_quantity`
- Status 6 (PENDING_TRIGGER) indicates stop order waiting for trigger
- Deleted when order reaches final state (FILLED, CANCELLED, REJECTED)

**State Transitions**:
```
ORDER_PLACED → Create OrderState record (status=1 or 6)
ORDER_PARTIAL_FILL → Update filled_quantity, remaining_quantity
ORDER_FILLED → Update status=2, then delete record
ORDER_CANCELLED → Update status=3, then delete record
ORDER_REJECTED → Update status=4, then delete record
ORDER_MODIFIED → Update prices or quantity
```

**Database Schema** (SQLite):
```sql
CREATE TABLE order_state (
    order_id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    account_id INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    side INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    order_type INTEGER NOT NULL,
    status INTEGER NOT NULL,
    limit_price REAL,
    stop_price REAL,
    filled_quantity INTEGER NOT NULL DEFAULT 0,
    remaining_quantity INTEGER NOT NULL,
    placed_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    raw_data TEXT
);
```

---

## P&L State

### PnLState

**Purpose**: Track cumulative P&L across all positions and accounts

**Schema**:
```python
@dataclass
class PnLState:
    """Cumulative P&L tracking for an account."""

    # Identifiers
    account_id: int
    date: date                 # Trading date (for daily resets)

    # Realized P&L (from TRADE_EXECUTED)
    realized_pnl: float        # CRITICAL - cumulative realized P&L for the day
    realized_pnl_by_symbol: dict[str, float]  # Breakdown by symbol

    # Unrealized P&L (calculated from positions)
    unrealized_pnl: float      # Current unrealized P&L across all positions
    unrealized_pnl_by_symbol: dict[str, float]  # Breakdown by symbol

    # Peak Tracking (for RULE-005)
    peak_unrealized_profit: float  # Highest unrealized profit reached today

    # Trade Counts (for RULE-006)
    trade_count: int           # Number of trades executed today

    # Timestamps
    created_at: datetime       # When tracking started for this date
    updated_at: datetime       # Last update time

    # Metadata
    raw_data: dict
```

**Key Points**:
- **One record per account per trading day**
- `realized_pnl` updated from TRADE_EXECUTED events (skip if None)
- `unrealized_pnl` recalculated on each POSITION_UPDATED or QUOTE_UPDATE
- Reset daily at midnight (or session start time)
- Track peak profit for RULE-005
- Track trade count for RULE-006

**State Transitions**:
```
TRADE_EXECUTED (pnl != None) → Add to realized_pnl
POSITION_UPDATED → Recalculate unrealized_pnl
QUOTE_UPDATE → Recalculate unrealized_pnl
Daily Reset → Create new PnLState for new date
```

**Database Schema** (SQLite):
```sql
CREATE TABLE pnl_state (
    account_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    realized_pnl REAL NOT NULL DEFAULT 0.0,
    realized_pnl_by_symbol TEXT,  -- JSON dict
    unrealized_pnl REAL NOT NULL DEFAULT 0.0,
    unrealized_pnl_by_symbol TEXT,  -- JSON dict
    peak_unrealized_profit REAL NOT NULL DEFAULT 0.0,
    trade_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    raw_data TEXT,
    PRIMARY KEY (account_id, date)
);
```

---

## Violation State

### ViolationState

**Purpose**: Track rule violations, warnings, and lockouts

**Schema**:
```python
@dataclass
class ViolationState:
    """State tracking for a rule violation."""

    # Identifiers
    violation_id: str          # Unique ID (UUID)
    account_id: int
    rule_id: str               # e.g., "RULE-003"

    # Violation Details
    severity: str              # "WARNING", "CRITICAL", "LOCKOUT"
    message: str               # Human-readable description
    triggered_by: str          # Event type that triggered violation

    # Timestamps
    occurred_at: datetime      # When violation occurred
    expires_at: datetime | None  # When cooldown/lockout expires (if applicable)
    resolved_at: datetime | None  # When violation was resolved

    # Status
    is_active: bool            # True if violation is still active
    is_locked_out: bool        # True if account is locked out

    # Metadata
    raw_data: dict             # Event data that triggered violation
```

**Key Points**:
- **One record per violation** (keyed by `violation_id`)
- Severity levels: WARNING → CRITICAL → LOCKOUT
- `expires_at` used for cooldown timers (RULE-006, RULE-007)
- `is_locked_out` prevents all trading when True
- Never deleted (audit trail), only marked resolved

**State Transitions**:
```
Rule Triggered → Create ViolationState (is_active=True)
Cooldown Expires → Update is_active=False, resolved_at
Manual Reset → Update is_active=False, resolved_at
```

**Database Schema** (SQLite):
```sql
CREATE TABLE violation_state (
    violation_id TEXT PRIMARY KEY,
    account_id INTEGER NOT NULL,
    rule_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    triggered_by TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    expires_at TEXT,
    resolved_at TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    is_locked_out INTEGER NOT NULL DEFAULT 0,
    raw_data TEXT,
    INDEX idx_account_active (account_id, is_active),
    INDEX idx_rule_active (rule_id, is_active)
);
```

---

## Daily Statistics State

### DailyStatsState

**Purpose**: Track daily trading statistics for limit enforcement

**Schema**:
```python
@dataclass
class DailyStatsState:
    """Daily trading statistics for an account."""

    # Identifiers
    account_id: int
    date: date

    # Position Counts (for RULE-001, RULE-002)
    max_contracts_today: int           # Highest total contracts held
    max_contracts_per_symbol: dict[str, int]  # Highest per symbol

    # Trade Counts (for RULE-006)
    total_trades_today: int
    trades_last_hour: list[datetime]   # Sliding window for frequency checks

    # Loss Tracking (for RULE-007)
    last_loss_time: datetime | None
    consecutive_losses: int

    # Session Tracking (for RULE-009)
    positions_opened_outside_session: list[str]  # Contract IDs

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Metadata
    raw_data: dict
```

**Key Points**:
- **One record per account per trading day**
- Track peak values for max contracts rules
- Sliding window for trade frequency (RULE-006)
- Reset daily at midnight (or session start time)

**Database Schema** (SQLite):
```sql
CREATE TABLE daily_stats_state (
    account_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    max_contracts_today INTEGER NOT NULL DEFAULT 0,
    max_contracts_per_symbol TEXT,  -- JSON dict
    total_trades_today INTEGER NOT NULL DEFAULT 0,
    trades_last_hour TEXT,  -- JSON list of ISO timestamps
    last_loss_time TEXT,
    consecutive_losses INTEGER NOT NULL DEFAULT 0,
    positions_opened_outside_session TEXT,  -- JSON list
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    raw_data TEXT,
    PRIMARY KEY (account_id, date)
);
```

---

## Timer State

### TimerState

**Purpose**: Track active cooldown timers and grace periods

**Schema**:
```python
@dataclass
class TimerState:
    """State tracking for active timers."""

    # Identifiers
    timer_id: str              # Unique ID (UUID)
    account_id: int
    rule_id: str               # Rule that started the timer

    # Timer Details
    timer_type: str            # "COOLDOWN", "GRACE_PERIOD", "SESSION_END"
    started_at: datetime
    expires_at: datetime
    duration_seconds: int

    # Associated Data
    contract_id: str | None    # For grace period timers (RULE-008)
    trigger_event: str | None  # Event type that started timer

    # Status
    is_active: bool            # True if timer is still running
    was_cancelled: bool        # True if timer was cancelled early

    # Metadata
    raw_data: dict
```

**Key Points**:
- **One record per active timer** (keyed by `timer_id`)
- Used for cooldown periods (RULE-007)
- Used for grace periods (RULE-008)
- Used for session end warnings (RULE-009)
- Automatically expire when `expires_at` reached

**State Transitions**:
```
Start Timer → Create TimerState (is_active=True)
Timer Expires → Update is_active=False
Cancel Timer → Update is_active=False, was_cancelled=True
```

**Database Schema** (SQLite):
```sql
CREATE TABLE timer_state (
    timer_id TEXT PRIMARY KEY,
    account_id INTEGER NOT NULL,
    rule_id TEXT NOT NULL,
    timer_type TEXT NOT NULL,
    started_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    contract_id TEXT,
    trigger_event TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    was_cancelled INTEGER NOT NULL DEFAULT 0,
    raw_data TEXT,
    INDEX idx_account_active (account_id, is_active),
    INDEX idx_expires (expires_at)
);
```

---

## State Synchronization

### State Update Patterns

**Position State Updates**:
```python
# On POSITION_OPENED
position_state = PositionState(
    contract_id=event["contract_id"],
    account_id=event["account_id"],
    size=event["size"],
    average_price=event["average_price"],
    unrealized_pnl=event["unrealized_pnl"],
    realized_pnl=event["realized_pnl"],
    has_stop_loss=False,
    opened_at=event["timestamp"]
)
state_manager.add_position(position_state)

# On POSITION_UPDATED
state_manager.update_position(
    contract_id=event["contract_id"],
    account_id=event["account_id"],
    size=event["size"],
    average_price=event["average_price"],
    unrealized_pnl=event["unrealized_pnl"]
)

# On POSITION_CLOSED
state_manager.remove_position(
    contract_id=event["contract_id"],
    account_id=event["account_id"]
)
```

**P&L State Updates**:
```python
# On TRADE_EXECUTED (with realized P&L)
if event["realized_pnl"] is not None:
    pnl_state = state_manager.get_pnl_state(account_id, date.today())
    pnl_state.realized_pnl += event["realized_pnl"]
    pnl_state.realized_pnl_by_symbol[event["symbol"]] += event["realized_pnl"]
    pnl_state.trade_count += 1

# On QUOTE_UPDATE (recalculate unrealized P&L)
positions = state_manager.get_positions(account_id)
total_unrealized = 0.0
for position in positions:
    current_price = quote_cache.get_price(position.symbol)
    unrealized = calculate_unrealized_pnl(
        size=position.size,
        entry_price=position.average_price,
        current_price=current_price,
        tick_size=config.get_tick_size(position.symbol),
        tick_value=config.get_tick_value(position.symbol)
    )
    position.unrealized_pnl = unrealized
    total_unrealized += unrealized

pnl_state.unrealized_pnl = total_unrealized
```

**Stop Loss Tracking**:
```python
# On ORDER_PLACED (stop order)
if event["order_type"] == 3 and event["stop_price"] is not None:
    position = state_manager.get_position(event["contract_id"], event["account_id"])
    if position:
        position.has_stop_loss = True
        position.stop_price = event["stop_price"]
        position.stop_order_id = event["order_id"]

# On ORDER_CANCELLED (stop order)
if cancelled_order.order_type == 3:
    position = state_manager.find_position_by_stop_order(cancelled_order.order_id)
    if position:
        position.has_stop_loss = False
        position.stop_price = None
        position.stop_order_id = None
```

---

## Daily Reset Logic

### Reset Procedure

**When**: At midnight UTC (or trading session start time)

**What Gets Reset**:
```python
def perform_daily_reset(account_id: int):
    """Reset daily tracking at session start."""

    today = date.today()

    # Create new P&L state for today
    pnl_state = PnLState(
        account_id=account_id,
        date=today,
        realized_pnl=0.0,
        unrealized_pnl=0.0,
        peak_unrealized_profit=0.0,
        trade_count=0,
        created_at=datetime.utcnow()
    )
    state_manager.create_pnl_state(pnl_state)

    # Create new daily stats for today
    stats_state = DailyStatsState(
        account_id=account_id,
        date=today,
        max_contracts_today=0,
        total_trades_today=0,
        consecutive_losses=0,
        created_at=datetime.utcnow()
    )
    state_manager.create_daily_stats(stats_state)

    # Carry over active positions (do NOT reset)
    # Carry over active violations (do NOT reset)
    # Expire timers that crossed midnight (check expires_at)
```

**What Does NOT Get Reset**:
- PositionState (positions carry over)
- ViolationState (violations persist)
- OrderState (active orders persist)
- TimerState (active timers continue, unless expired)

---

## State Persistence Strategy

### In-Memory vs Database

**In-Memory** (fast access, lost on restart):
- Current positions (PositionState)
- Active orders (OrderState)
- Current P&L (PnLState)
- Quote cache (last prices)

**Database** (persistent, survives restart):
- All ViolationState records (audit trail)
- Daily stats archives
- Historical P&L records
- Timer state (for recovery)

**Persistence Schedule**:
- Write to DB on every state change (async)
- Flush to disk every 5 seconds (batch)
- Full state snapshot every 1 minute

**Recovery on Restart**:
```python
def recover_state_on_startup():
    """Recover state from database after restart."""

    # Reload active positions from SDK
    positions = sdk.get_all_positions()
    for position in positions:
        state_manager.add_position(PositionState.from_sdk(position))

    # Reload active violations
    violations = db.get_active_violations()
    for violation in violations:
        state_manager.add_violation(violation)

    # Reload active timers
    timers = db.get_active_timers()
    for timer in timers:
        if timer.expires_at > datetime.utcnow():
            state_manager.add_timer(timer)
        else:
            db.mark_timer_expired(timer.timer_id)

    # Recalculate current P&L
    pnl_state = calculate_current_pnl(positions)
    state_manager.set_pnl_state(pnl_state)
```

---

## Schema Validation

### State Consistency Checks

Run these checks periodically to validate state integrity:

```python
def validate_state_consistency():
    """Validate state is consistent and correct."""

    # Check 1: Position count matches contract count
    positions = state_manager.get_all_positions()
    total_contracts = sum(abs(p.size) for p in positions)
    assert total_contracts <= config.max_contracts_total

    # Check 2: Active violations match rule state
    violations = state_manager.get_active_violations()
    for violation in violations:
        if violation.expires_at and violation.expires_at < datetime.utcnow():
            log.warning(f"Expired violation still active: {violation.violation_id}")

    # Check 3: P&L matches position state
    pnl_state = state_manager.get_pnl_state(account_id, date.today())
    calculated_pnl = sum(p.unrealized_pnl for p in positions)
    assert abs(pnl_state.unrealized_pnl - calculated_pnl) < 0.01

    # Check 4: Stop-loss orders exist for flagged positions
    for position in positions:
        if position.has_stop_loss:
            order = state_manager.get_order(position.stop_order_id)
            assert order is not None
            assert order.order_type == 3  # STOP order
            assert order.stop_price is not None
```

---

## References

- **Event Schemas**: `docs/specifications/unified/data-schemas/event-data-schemas.md`
- **SDK Integration**: `docs/specifications/unified/sdk-integration.md`
- **Implementation**: `src/risk_manager/state/`
- **Database**: SQLite schema in `src/risk_manager/db/schema.sql`

---

**Document Status**: Canonical ✅
**Last Reviewed**: 2025-10-27
**Next Review**: After any major state management changes
