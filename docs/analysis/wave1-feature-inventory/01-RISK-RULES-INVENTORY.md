# Risk Rules Feature Inventory

**Analysis Date:** 2025-10-25
**Researcher:** RESEARCHER 1 - Risk Rules Specialist
**Working Directory:** /mnt/c/Users/jakers/Desktop/risk-manager-v34

---

## Executive Summary

### Rules Found
- **12 Primary Rules** - RULE-001 through RULE-012 (fully specified)
- **1 Additional Rule** - RULE-013 (mentioned in RULE_CATEGORIES.md, no dedicated spec file)
- **Total: 13 Rules**

### Rule Categories
Rules are organized into 4 enforcement categories:
1. **Trade-by-Trade** (6 rules) - Close specific position, no lockout
2. **Timer/Cooldown** (2 rules) - Close all + temporary lockout
3. **Hard Lockout** (4 rules) - Close all + lockout until condition met
4. **Automation** (1 rule) - Trade management automation

### Documentation Quality
- **Primary Specs**: `/docs/PROJECT_DOCS/rules/` - 12 files, detailed, version 2.0
- **Supplementary Docs**: `/docs/current/` - Updated categorization (2025-10-23)
- **Consistency**: Good alignment between primary specs and current docs
- **Conflicts**: RULE-013 exists in categories but lacks dedicated spec file

---

## Detailed Rule Inventory

---

## RULE-001: MaxContracts

### Specification Summary
- **Purpose**: Cap net contract exposure across all instruments to prevent over-leveraging
- **Trigger**: `GatewayUserPosition` event (every position update)
- **Enforcement**: Close positions (all or reduce to limit) - NO lockout
- **Parameters**:
  - `limit`: Max net contracts (e.g., 5)
  - `count_type`: "net" or "gross"
  - `close_all`: true/false (close all vs reduce to limit)
  - `reduce_to_limit`: Alternative to close_all
  - `lockout_on_breach`: false (no lockout for this rule)

### Enforcement Category
**Trade-by-Trade** (Category 1)

### Scope
**Account-wide** (tracks positions across all instruments)

### Calculation Logic
```python
total_net = 0
for position in all_positions:
    if position.type == 1:  # Long
        total_net += position.size
    elif position.type == 2:  # Short
        total_net -= position.size

total_net = abs(total_net)
if total_net > limit:
    BREACH
```

### Enforcement Actions
1. If `close_all: true`:
   - Close all positions via MOD-001
   - Log enforcement
   - Update Trader CLI
   - NO lockout (can trade immediately)

2. If `reduce_to_limit: true`:
   - Calculate excess contracts
   - Close positions to reach limit
   - Log enforcement
   - NO lockout

### Reset Timing
N/A (no state to reset, evaluated per-event)

### Edge Cases
1. **Net vs Gross**:
   - Net: Long 5 + Short 3 = abs(5-3) = 2
   - Gross: Long 5 + Short 3 = 5+3 = 8
2. **Multi-instrument netting**: MNQ Long 3 + ES Long 2 = 5 total
3. **Reduce to limit logic**: Must decide which positions to close

### Implementation Details

#### State Tracking
```python
# In-memory position tracking (rebuild from API on restart)
positions = {
    "CON.F.US.MNQ.U25": {"type": 1, "size": 3},
    "CON.F.US.ES.U25": {"type": 1, "size": 2}
}
```

#### API Requirements
- **Trigger**: SignalR `GatewayUserPosition` event
- **Enforcement**:
  - `POST /api/Position/searchOpen` (get all positions)
  - `POST /api/Position/closeContract` (close each position)

#### Performance
- Event frequency: High (every position update)
- Calculation cost: O(n) where n = number of open positions
- API calls on breach: 1 search + n closes

#### Dependencies
- **MOD-001** (enforcement/actions.py) - close_all_positions(), close_position()
- **state_manager.py** - get_all_positions()

### Sources Found

#### Primary Source: Most Authoritative
- **File**: `/docs/PROJECT_DOCS/rules/01_max_contracts.md`
- **Lines**: 1-225 (complete specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Comprehensive
- **Key Details**:
  - Full YAML config example
  - Trigger logic with code
  - Enforcement sequence
  - API requirements (SignalR events, REST endpoints)
  - State tracking details
  - Test scenarios (4 scenarios)
  - Performance notes
  - CLI display examples

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 42-66
- **Detail Level**: Summary categorization
- **Key Details**:
  - Confirms Category 1: Trade-by-Trade
  - Enforcement: Close position that caused breach
  - No lockout
  - Can trade immediately after

#### Tertiary Source: SDK Mapping
- **File**: `/docs/current/RULES_TO_SDK_MAPPING.md`
- **Lines**: 34-89
- **Detail Level**: Implementation guide
- **Key Details**:
  - What SDK provides (events, close methods)
  - What we build (rule logic, breach detection)
  - Example implementation code
  - Data flow through system

### Conflicts/Variations
**No conflicts found.** All documentation sources are aligned:
- Primary spec provides detailed implementation details
- Categories doc correctly classifies as Trade-by-Trade
- SDK mapping correctly identifies SDK vs custom code split

### Recommendation
**Use primary source** (`01_max_contracts.md`) as authoritative specification.
- Most detailed and complete
- Version controlled (v2.0)
- Includes all technical details needed for implementation
- Cross-reference with RULE_CATEGORIES.md for enforcement type confirmation

---

## RULE-002: MaxContractsPerInstrument

### Specification Summary
- **Purpose**: Enforce per-symbol contract limits to prevent concentration risk
- **Trigger**: `GatewayUserPosition` event (per-symbol position updates)
- **Enforcement**: Close position in that instrument (all or reduce) - NO lockout
- **Parameters**:
  - `limits`: Dictionary of symbol -> max contracts (e.g., `MNQ: 2, ES: 1`)
  - `enforcement`: "close_all" or "reduce_to_limit"
  - `unknown_symbol_action`: "block", "allow_with_limit:N", "allow_unlimited"
  - `lockout_on_breach`: false

### Enforcement Category
**Trade-by-Trade** (Category 1)

### Scope
**Per-instrument** (tracks positions per symbol, not account-wide)

### Calculation Logic
```python
contract_id = position_event['contractId']
symbol = extract_symbol(contract_id)  # "CON.F.US.MNQ.U25" → "MNQ"
current_size = abs(position_event['size'])

if symbol in config['limits']:
    limit = config['limits'][symbol]
    if current_size > limit:
        BREACH
else:
    # Unknown symbol handling
    if config['unknown_symbol_action'] == "block":
        if current_size > 0:
            BREACH
```

### Symbol Extraction
```python
def extract_symbol(contract_id):
    # "CON.F.US.MNQ.U25" → "MNQ"
    parts = contract_id.split('.')
    return parts[3] if len(parts) >= 4 else contract_id
```

### Enforcement Actions
1. If `enforcement: "reduce_to_limit"`:
   - Calculate excess: current_size - limit
   - Partial close via `POST /api/Position/partialCloseContract`
   - Log enforcement
   - NO lockout

2. If `enforcement: "close_all"`:
   - Close entire position in that symbol
   - Log enforcement
   - NO lockout

### Reset Timing
N/A (no state to reset, evaluated per-event)

### Edge Cases
1. **Unknown symbols**: Three handling modes (block, allow with limit, allow unlimited)
2. **Multi-contract months**: Same symbol, different contract months (e.g., MNQ.U25 vs MNQ.Z25)
3. **Symbol extraction**: Must parse contract ID correctly for various formats

### Implementation Details

#### State Tracking
```python
# Track per-symbol positions
positions_by_symbol = {
    "MNQ": {"contract_id": "CON.F.US.MNQ.U25", "size": 2},
    "ES": {"contract_id": "CON.F.US.ES.U25", "size": 1}
}
```

#### API Requirements
- **Trigger**: SignalR `GatewayUserPosition` event
- **Enforcement**:
  - Reduce: `POST /api/Position/partialCloseContract` (close N contracts)
  - Close all: `POST /api/Position/closeContract` (close entire position)

#### Dependencies
- **MOD-001** (actions.py) - close_position(), reduce_position()
- **state_manager.py** - get_position_by_symbol()

### Sources Found

#### Primary Source: Most Authoritative
- **File**: `/docs/PROJECT_DOCS/rules/02_max_contracts_per_instrument.md`
- **Lines**: 1-189 (complete specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Comprehensive
- **Key Details**:
  - Per-symbol limits configuration
  - Unknown symbol handling (3 modes)
  - Symbol extraction logic
  - Partial close vs full close
  - Test scenarios (4 scenarios)
  - CLI display examples

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 42-66
- **Detail Level**: Summary
- **Key Details**:
  - Confirms Category 1: Trade-by-Trade
  - Close position in that instrument only
  - No lockout

### Conflicts/Variations
**No conflicts found.** Documentation is consistent.

### Recommendation
**Use primary source** (`02_max_contracts_per_instrument.md`) as authoritative specification.

---

## RULE-003: DailyRealizedLoss

### Specification Summary
- **Purpose**: Enforce hard daily realized P&L limit - stops trading when daily loss threshold is hit
- **Trigger**: `GatewayUserTrade` event (when `profitAndLoss` is not null)
- **Enforcement**: Close all positions + Cancel all orders + Hard lockout until reset time
- **Parameters**:
  - `limit`: Max daily loss (negative value, e.g., -500)
  - `reset_time`: Daily reset time (e.g., "17:00" for 5:00 PM)
  - `timezone`: Timezone for reset (e.g., "America/New_York")
  - `enforcement`: "close_all_and_lockout"
  - `lockout_until_reset`: true

### Enforcement Category
**Hard Lockout** (Category 3)

### Scope
**Account-wide** (tracks total daily realized P&L across all symbols)

### Calculation Logic
```python
def check(trade_event):
    pnl = trade_event['profitAndLoss']
    if pnl is not None:  # Only count full-turn trades
        daily_realized_pnl = pnl_tracker.add_trade_pnl(
            trade_event['accountId'],
            pnl
        )

        if daily_realized_pnl <= config['limit']:
            return BREACH
```

### P&L Tracking
- **Only full-turn trades**: `profitAndLoss` field is `null` for opening trades
- **Cumulative daily total**: Sum all realized P&L for the day
- **Persisted to SQLite**: Survives service restarts

### Enforcement Actions
1. **Close all positions** via MOD-001
2. **Cancel all orders** via MOD-001
3. **Set hard lockout** via MOD-002:
   - Calculate next reset time (e.g., 5:00 PM today or tomorrow)
   - Set lockout with expiry = reset_time
   - Log enforcement
4. **Update Trader CLI** with countdown timer
5. **Auto-unlock** at reset time via MOD-004

### Reset Timing
**Daily at configured time** (e.g., 5:00 PM)
- If breach occurs before reset time → unlock at reset time same day
- If breach occurs after reset time → unlock at reset time next day
- Reset scheduler (MOD-004) calls `reset_daily_counters()` at reset time
- Clears lockout and resets daily P&L to 0

### Edge Cases
1. **Half-turn trades**: `profitAndLoss: null` → Ignore (don't update P&L)
2. **Reset time crossing**: Breach at 2 PM → unlock at 5 PM same day
3. **After reset time**: Breach at 6 PM → unlock at 5 PM next day
4. **Service restart**: P&L must persist in SQLite to survive restart
5. **Multiple trades in one event cycle**: Accumulate all before checking

### Implementation Details

#### State Tracking - SQLite Schema
```sql
CREATE TABLE daily_pnl (
    account_id INTEGER PRIMARY KEY,
    realized_pnl REAL DEFAULT 0,
    date DATE DEFAULT CURRENT_DATE
);
```

#### State Update Logic
```python
def add_trade_pnl(account_id, pnl):
    today = datetime.now().date()

    # Get current daily P&L
    row = db.execute(
        "SELECT realized_pnl FROM daily_pnl WHERE account_id=? AND date=?",
        (account_id, today)
    )
    current_pnl = row[0] if row else 0

    # Add new trade P&L
    new_pnl = current_pnl + pnl

    # Update database
    db.execute(
        "INSERT OR REPLACE INTO daily_pnl (account_id, realized_pnl, date) VALUES (?, ?, ?)",
        (account_id, new_pnl, today)
    )

    return new_pnl
```

#### Daily Reset Logic
```python
def reset_daily_counters(account_id):
    today = datetime.now().date()
    db.execute(
        "DELETE FROM daily_pnl WHERE account_id=? AND date < ?",
        (account_id, today)
    )
    db.execute(
        "INSERT INTO daily_pnl (account_id, realized_pnl, date) VALUES (?, 0, ?)",
        (account_id, today)
    )
```

#### API Requirements
- **Trigger**: SignalR `GatewayUserTrade` event
  - Event includes `profitAndLoss` field (null for half-turn)
- **Enforcement**:
  - `POST /api/Position/closeContract` (for each position)
  - `POST /api/Order/cancel` (for each order)

#### Lockout Behavior
**While Locked Out**:
- Trader CLI shows: `"🔴 LOCKED OUT - Daily loss limit hit - Reset at 5:00 PM (2h 47m)"`
- If trader somehow places order and it fills → Close immediately (event router catches)
- All open orders cancelled
- Countdown timer updates every second

**Auto-Unlock**:
- At reset_time → `reset_scheduler.py` calls `reset_daily_counters()`
- `lockout_manager.check_expired_lockouts()` clears lockout
- Trader CLI updates: `"🟢 OK TO TRADE - Daily P&L reset"`

#### Dependencies
- **MOD-001** (actions.py) - close_all_positions(), cancel_all_orders()
- **MOD-002** (lockout_manager.py) - set_lockout(), get_lockout_info()
- **MOD-004** (reset_scheduler.py) - schedule_daily_reset(), reset_daily_counters()
- **pnl_tracker.py** - add_trade_pnl(), get_daily_realized_pnl()

### Sources Found

#### Primary Source: Most Authoritative
- **File**: `/docs/PROJECT_DOCS/rules/03_daily_realized_loss.md`
- **Lines**: 1-228 (complete specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Extremely comprehensive
- **Key Details**:
  - Full P&L tracking logic with SQLite schema
  - Reset time calculation (same day vs next day)
  - Lockout behavior details
  - Auto-unlock mechanism
  - Test scenarios (4 scenarios)
  - CLI display examples (before/after breach)

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 101-133
- **Detail Level**: Summary with example
- **Key Details**:
  - Confirms Category 3: Hard Lockout
  - Unlock condition: Reset time (5 PM) or admin override
  - Example lockout flow

#### Tertiary Source: SDK Mapping
- **File**: `/docs/current/RULES_TO_SDK_MAPPING.md`
- **Lines**: 92-224
- **Detail Level**: Implementation example
- **Key Details**:
  - Complete code examples for P&L tracking
  - Lockout manager implementation
  - Reset scheduler implementation
  - Rule logic example

### Conflicts/Variations
**No conflicts found.** All sources are aligned and complementary.

### Recommendation
**Use primary source** (`03_daily_realized_loss.md`) as authoritative specification.
- Most comprehensive state tracking details
- Includes SQLite schema
- Complete reset logic
- Cross-reference SDK_MAPPING for implementation examples

---

## RULE-004: DailyUnrealizedLoss

### Specification Summary
- **Purpose**: Enforce hard daily floating loss limit (unrealized P&L)
- **Trigger**: `GatewayUserPosition` event + market price updates
- **Enforcement**: Close all positions + Hard lockout until reset time
- **Parameters**:
  - `limit`: Max daily unrealized loss (negative value, e.g., -300)
  - `reset_time`: Daily reset time (e.g., "17:00")
  - `enforcement`: "close_all_and_lockout"

### Enforcement Category
**Trade-by-Trade** (Category 1) according to RULE_CATEGORIES.md
**CONFLICT**: Primary spec says "Hard Lockout", categories doc says "Trade-by-Trade"

### Scope
**Account-wide** (sum unrealized P&L across all open positions)

### Calculation Logic
```python
# Calculate unrealized P&L for all open positions
unrealized_pnl = sum(
    (current_price - avg_price) * size * tick_value
    for all positions
)

if unrealized_pnl <= config['limit']:
    BREACH
```

### Enforcement Actions (per primary spec)
1. Close all positions (MOD-001)
2. Set lockout until reset_time (MOD-002)
3. Auto-unlock at reset time (MOD-004)

### Enforcement Actions (per RULE_CATEGORIES.md)
1. Close that losing position ONLY
2. NO lockout
3. Can trade immediately

### Reset Timing
**Daily at 5:00 PM** (if using Hard Lockout approach)
**N/A** (if using Trade-by-Trade approach)

### Edge Cases
1. **Market price updates**: Requires real-time price feed
2. **Tick value calculation**: Different for each instrument
3. **Multiple positions**: Calculate aggregate unrealized P&L

### Implementation Details

#### State Tracking
- Requires market price updates (not just position events)
- Need tick values for each instrument
- Calculate unrealized P&L in real-time

#### API Requirements
- **Trigger**: `GatewayUserPosition` + market data updates
- **Enforcement**: Same as RULE-003 (close all, set lockout)

#### Dependencies
- Same as RULE-003 if using Hard Lockout
- Same as RULE-001 if using Trade-by-Trade

### Sources Found

#### Primary Source: Brief Specification
- **File**: `/docs/PROJECT_DOCS/rules/04_daily_unrealized_loss.md`
- **Lines**: 1-40 (brief specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Brief/Summary
- **Key Details**:
  - States enforcement is "close_all_and_lockout"
  - Hard lockout until reset
  - References MOD-001, MOD-002, MOD-004

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 42-66
- **Detail Level**: Summary
- **Key Details**:
  - Lists as Category 1: Trade-by-Trade
  - States: "Close that losing position only"
  - NO lockout
  - Example shows closing only MNQ, leaving ES open

### Conflicts/Variations

**MAJOR CONFLICT DETECTED:**

| Aspect | Primary Spec (04_daily_unrealized_loss.md) | Categories Doc (RULE_CATEGORIES.md) |
|--------|---------------------------------------------|-------------------------------------|
| Enforcement Type | Hard Lockout (Category 3) | Trade-by-Trade (Category 1) |
| Close Action | Close ALL positions | Close ONLY that position |
| Lockout | Yes, until reset time | NO lockout |
| Can Trade Again | At reset time (5 PM) | Immediately |

**Updated Categories Doc Note** (dated 2025-10-23):
```
**Critical Changes**:
- RULE-004, 005, 008 are trade-by-trade (NOT close all)
- Corrected enforcement categories
```

This suggests the **Categories doc (2025-10-23) is more recent** than the primary spec (2025-01-17) and represents a **design decision change**.

### Recommendation

**CONFLICT REQUIRES RESOLUTION:**

**Option A: Use Categories Doc (Trade-by-Trade)**
- More recent (2025-10-23 vs 2025-01-17)
- Explicitly states "corrected enforcement categories"
- Makes more sense: Close only the position with excessive unrealized loss
- Aligns with position-level risk management

**Option B: Use Primary Spec (Hard Lockout)**
- More detailed specification
- Prevents all trading when floating loss too high
- More conservative risk management

**RECOMMENDATION**: **Use Option A (Trade-by-Trade from Categories Doc)**
- Categories doc explicitly states this was a correction
- More recent date suggests intentional update
- More granular risk management (close bad position, keep good ones)
- Should update primary spec to match

**ACTION REQUIRED**: Update `04_daily_unrealized_loss.md` to match Categories doc, or create v2.1 spec clarifying Trade-by-Trade approach.

---

## RULE-005: MaxUnrealizedProfit

### Specification Summary
- **Purpose**: Enforce profit target - close positions when daily profit limit is hit
- **Trigger**: `GatewayUserPosition` event + market price updates
- **Enforcement**: Close positions + Lockout until reset
- **Parameters**:
  - `limit`: Profit target (positive value, e.g., 1000)
  - `reset_time`: Daily reset time (e.g., "17:00")
  - `enforcement`: "close_all_and_lockout"

### Enforcement Category
**Trade-by-Trade** (Category 1) according to RULE_CATEGORIES.md
**CONFLICT**: Primary spec says "close_all_and_lockout", categories doc says "Trade-by-Trade"

### Scope
**Account-wide** (sum unrealized P&L across all positions)

### Calculation Logic
```python
unrealized_pnl = sum(
    (current_price - avg_price) * size * tick_value
    for all positions
)

if unrealized_pnl >= config['limit']:
    BREACH  # Hit profit target
```

### Enforcement Actions (per primary spec)
1. Close all positions (lock in profits) (MOD-001)
2. Set lockout until reset_time (MOD-002) - prevents re-entry
3. Auto-unlock at reset time (MOD-004)

### Enforcement Actions (per RULE_CATEGORIES.md)
1. Close that winning position only (take profit)
2. NO lockout
3. Can trade immediately

### Reset Timing
**Daily at reset time** (if using Hard Lockout)
**N/A** (if using Trade-by-Trade)

### Edge Cases
1. **Market price updates**: Requires real-time price feed
2. **Profit protection**: Different philosophy - close winning position vs all
3. **Use case difference**:
   - Hard Lockout: "Hit daily target, stop trading completely"
   - Trade-by-Trade: "Take profit on winner, keep trading"

### Implementation Details

#### State Tracking
- Same as RULE-004 (unrealized P&L calculation)
- Real-time market data required

#### API Requirements
- **Trigger**: `GatewayUserPosition` + market data
- **Enforcement**: Close positions

#### Dependencies
- MOD-001, MOD-002, MOD-004 (if Hard Lockout)
- MOD-001 only (if Trade-by-Trade)

### Sources Found

#### Primary Source: Brief Specification
- **File**: `/docs/PROJECT_DOCS/rules/05_max_unrealized_profit.md`
- **Lines**: 1-38 (brief specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Brief
- **Key Details**:
  - States enforcement is "close_all_and_lockout"
  - Use case: "Take profit and stop for the day"
  - Hard lockout until reset

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 42-66
- **Detail Level**: Summary
- **Key Details**:
  - Lists as Category 1: Trade-by-Trade
  - "Close that winning position only (take profit)"
  - NO lockout

### Conflicts/Variations

**MAJOR CONFLICT DETECTED:**

Same conflict pattern as RULE-004.

| Aspect | Primary Spec | Categories Doc |
|--------|--------------|----------------|
| Enforcement Type | Hard Lockout | Trade-by-Trade |
| Close Action | Close ALL | Close ONLY that position |
| Lockout | Yes | NO |

### Recommendation

**CONFLICT REQUIRES RESOLUTION:**

**Option A: Trade-by-Trade** (per Categories Doc)
- Close winning position, take profit
- Keep other positions open
- Can continue trading
- More flexible

**Option B: Hard Lockout** (per Primary Spec)
- Hit daily target, stop completely
- Prevents giving back profits
- "Take the win and walk away"
- More conservative

**RECOMMENDATION**: **Depends on user philosophy preference**
- Both approaches are valid
- Should be **CONFIGURABLE** in YAML
- Default: Trade-by-Trade (more flexible)
- Option: Hard Lockout (more conservative)

**Suggested Config**:
```yaml
max_unrealized_profit:
  enabled: true
  limit: 1000
  enforcement_mode: "trade_by_trade"  # or "hard_lockout"
  lockout_until_reset: false  # true if hard_lockout mode
  reset_time: "17:00"
```

---

## RULE-006: TradeFrequencyLimit

### Specification Summary
- **Purpose**: Prevent overtrading by limiting trades per time window
- **Trigger**: `GatewayUserTrade` event (every trade execution)
- **Enforcement**: Cooldown timer (NO position close, trade already happened)
- **Parameters**:
  - `limits.per_minute`: Max trades per minute (e.g., 3)
  - `limits.per_hour`: Max trades per hour (e.g., 10)
  - `limits.per_session`: Max trades per session (e.g., 50)
  - `cooldown_on_breach.per_minute_breach`: Cooldown duration in seconds (e.g., 60)
  - `cooldown_on_breach.per_hour_breach`: Cooldown duration (e.g., 1800 = 30 min)
  - `cooldown_on_breach.per_session_breach`: Cooldown duration (e.g., 3600 = 1 hour)

### Enforcement Category
**Timer/Cooldown** (Category 2)

### Scope
**Account-wide** (tracks all trades across all instruments)

### Calculation Logic
```python
minute_count = count_trades_in_window(account_id, window=60)  # Last 60s
hour_count = count_trades_in_window(account_id, window=3600)  # Last 1 hour
session_count = count_trades_since_session_start(account_id)

if minute_count >= config['limits']['per_minute']:
    return BREACH, "per_minute"
elif hour_count >= config['limits']['per_hour']:
    return BREACH, "per_hour"
elif session_count >= config['limits']['per_session']:
    return BREACH, "per_session"
```

### Enforcement Actions
1. **NO position close** (trade already executed, can't prevent it)
2. **Set cooldown timer** via MOD-002/MOD-003:
   - `set_cooldown(account_id, reason, duration=60/1800/3600)`
3. **CLI shows countdown**: `"🟡 COOLDOWN - 3/3 trades - Unlocks in 47s"`
4. **Auto-unlock** when timer expires

### Reset Timing
**Rolling time windows** (per_minute, per_hour)
**Session-based** (per_session - resets at session start)

### Edge Cases
1. **Trade already happened**: Can't prevent it, only prevent NEXT trade
2. **Rolling windows**: 60-second window is sliding, not fixed minute boundaries
3. **Session definition**: Must define when session starts/ends
4. **Multiple breaches**: If hit per_minute, don't also check per_hour (prioritize)

### Implementation Details

#### State Tracking - SQLite Schema
```sql
CREATE TABLE trade_counts (
    account_id INTEGER,
    window_start DATETIME,
    count INTEGER,
    PRIMARY KEY (account_id, window_start)
);
```

#### State Update Logic
```python
def count_trades_in_window(account_id, window_seconds):
    cutoff = datetime.now() - timedelta(seconds=window_seconds)

    # Query trades within window
    count = db.execute(
        "SELECT COUNT(*) FROM trades WHERE account_id=? AND timestamp > ?",
        (account_id, cutoff)
    ).fetchone()[0]

    return count
```

#### API Requirements
- **Trigger**: SignalR `GatewayUserTrade` event
- **Enforcement**: None (no positions to close, just set cooldown)

#### Dependencies
- **MOD-002** (lockout_manager.py) - set_cooldown()
- **MOD-003** (timer_manager.py) - Timer expiration tracking

### Sources Found

#### Primary Source: Specification
- **File**: `/docs/PROJECT_DOCS/rules/06_trade_frequency_limit.md`
- **Lines**: 1-61 (specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Good
- **Key Details**:
  - Three time windows (minute, hour, session)
  - Configurable cooldown durations
  - SQLite schema for trade tracking
  - Cooldown enforcement (no position close)

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 70-98
- **Detail Level**: Summary with example
- **Key Details**:
  - Category 2: Timer/Cooldown
  - Example: 15-minute cooldown with countdown display
  - Auto-unlock when timer expires

#### Tertiary Source: SDK Mapping
- **File**: `/docs/current/RULES_TO_SDK_MAPPING.md`
- **Lines**: 227-339
- **Detail Level**: Implementation example
- **Key Details**:
  - TradeCounter implementation
  - TimerManager implementation
  - Rolling window calculation logic

### Conflicts/Variations
**No conflicts found.** All sources agree on cooldown-based enforcement.

### Recommendation
**Use primary source** (`06_trade_frequency_limit.md`) as authoritative specification.
- Clear time window definitions
- Comprehensive cooldown configuration
- Cross-reference SDK_MAPPING for implementation patterns

---

## RULE-007: CooldownAfterLoss

### Specification Summary
- **Purpose**: Force break after losing trades to prevent revenge trading
- **Trigger**: `GatewayUserTrade` event (when `profitAndLoss < 0`)
- **Enforcement**: Cooldown timer based on loss amount (NO position close)
- **Parameters**:
  - `loss_thresholds`: Array of {loss_amount, cooldown_duration}
    - Example: -$100 loss → 5 min cooldown (300s)
    - Example: -$200 loss → 15 min cooldown (900s)
    - Example: -$300 loss → 30 min cooldown (1800s)

### Enforcement Category
**Timer/Cooldown** (Category 2)

### Scope
**Per-trade** (evaluates each losing trade individually)

### Calculation Logic
```python
trade_pnl = trade_event['profitAndLoss']
if trade_pnl < 0:  # Losing trade
    for threshold in config['loss_thresholds']:
        if trade_pnl <= threshold['loss_amount']:
            return BREACH, threshold['cooldown_duration']
```

### Enforcement Actions
1. **NO position close** (trade already done)
2. **Set cooldown timer** via MOD-002/MOD-003:
   - Duration based on loss amount
   - Example: -$150 loss → 5 min cooldown (first threshold matched)
3. **CLI shows countdown**
4. **Auto-unlock** when timer expires

### Reset Timing
**Timer-based** (cooldown expires after configured duration)

### Edge Cases
1. **Threshold matching**: Use first matching threshold (largest loss if sorted)
2. **Multiple losses in cooldown**: Could extend or ignore subsequent losses
3. **Winning trade during cooldown**: Does it clear cooldown? (spec doesn't say)

### Implementation Details

#### State Tracking
- Track current cooldown state
- Store cooldown expiry time
- Log which threshold triggered

#### API Requirements
- **Trigger**: SignalR `GatewayUserTrade` event
- **Enforcement**: None (just set timer)

#### Dependencies
- **MOD-002** (lockout_manager.py) - set_cooldown()
- **MOD-003** (timer_manager.py) - Timer management

### Sources Found

#### Primary Source: Specification
- **File**: `/docs/PROJECT_DOCS/rules/07_cooldown_after_loss.md`
- **Lines**: 1-46 (specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Good
- **Key Details**:
  - Tiered cooldown based on loss amount
  - Use case: Prevent revenge trading
  - No position close

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 70-98
- **Detail Level**: Summary
- **Key Details**:
  - Category 2: Timer/Cooldown
  - Example with 15-minute cooldown

### Conflicts/Variations
**No conflicts found.**

### Recommendation
**Use primary source** (`07_cooldown_after_loss.md`) as authoritative specification.

---

## RULE-008: NoStopLossGrace

### Specification Summary
- **Purpose**: Enforce stop-loss placement - close position if no SL placed within grace period
- **Trigger**: `GatewayUserOrder` event (when position opens)
- **Enforcement**: Close position if no stop-loss placed within grace period (NO lockout)
- **Parameters**:
  - `grace_period_seconds`: Time allowed to place SL (e.g., 10 seconds)
  - `enforcement`: "close_position"

### Enforcement Category
**Trade-by-Trade** (Category 1)

### Scope
**Per-position** (tracks each position individually)

### Trigger Logic
```python
def on_position_open(position_event):
    # Start timer
    timer_manager.start_timer(
        name=f"sl_grace_{position_event['id']}",
        duration=config['grace_period_seconds'],
        callback=lambda: check_stop_loss(position_event)
    )

def check_stop_loss(position_event):
    # Check if SL order exists for this position
    orders = get_open_orders(account_id)
    has_stop_loss = any(
        o['type'] == 4 and o['contractId'] == position_event['contractId']
        for o in orders
    )

    if not has_stop_loss:
        return BREACH
```

### Enforcement Actions
1. **Close position** via MOD-001
2. **NO lockout** (can trade again immediately)
3. **Log**: `"No stop-loss placed within 10s - position closed"`

### Reset Timing
N/A (per-position timer-based)

### Edge Cases
1. **Order type detection**: Must identify stop-loss orders (type == 4)
2. **Contract matching**: SL must be for same contract as position
3. **Grace period start**: When does timer start? Position open event
4. **SL placed then cancelled**: Does that count? (spec doesn't clarify)

### Implementation Details

#### State Tracking
- Track active grace period timers per position
- Check open orders for stop-loss

#### API Requirements
- **Trigger**: `GatewayUserOrder` event (position open)
- **Query**: Get open orders to check for SL
- **Enforcement**: `POST /api/Position/closeContract`

#### Dependencies
- **MOD-001** (actions.py) - close_position()
- **timer_manager.py** - Grace period timer

### Sources Found

#### Primary Source: Specification
- **File**: `/docs/PROJECT_DOCS/rules/08_no_stop_loss_grace.md`
- **Lines**: 1-49 (specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Good
- **Key Details**:
  - Grace period timer logic
  - Stop-loss order detection
  - Use case: Force SL discipline

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 42-66
- **Detail Level**: Summary
- **Key Details**:
  - Category 1: Trade-by-Trade
  - Close that position, no lockout

### Conflicts/Variations
**No conflicts found.**

### Recommendation
**Use primary source** (`08_no_stop_loss_grace.md`) as authoritative specification.

---

## RULE-009: SessionBlockOutside

### Specification Summary
- **Purpose**: Block trading outside configured session hours and on holidays
- **Trigger**: Multiple triggers
  1. `GatewayUserPosition` event (position opens outside session)
  2. Background timer (session end time reached)
  3. Holiday detection
- **Enforcement**: Close positions + Cancel orders + Hard lockout until session starts
- **Parameters**:
  - `global_session.enabled`: Use global session times
  - `global_session.start`: Session start time (e.g., "09:30")
  - `global_session.end`: Session end time (e.g., "16:00")
  - `global_session.timezone`: Timezone (e.g., "America/New_York")
  - `per_instrument_sessions.enabled`: Use per-instrument overrides
  - `per_instrument_sessions.sessions`: Dictionary of symbol → session times
  - `close_positions_at_session_end`: Auto-close at session end
  - `lockout_outside_session`: Hard lockout when outside hours
  - `respect_holidays`: Use holiday calendar
  - `enforcement`: "close_immediately"

### Enforcement Category
**Hard Lockout** (Category 3)

### Scope
**Account-wide** or **Per-instrument** (configurable)

### Session Time Examples

#### Global Session
```yaml
global_session:
  enabled: true
  start: "09:30"
  end: "16:00"
  timezone: "America/New_York"
```

#### Per-Instrument Override
```yaml
per_instrument_sessions:
  enabled: true
  sessions:
    ES:
      start: "18:00"  # Sunday 6pm
      end: "17:00"    # Friday 5pm
      timezone: "America/Chicago"
    NQ:
      start: "09:30"
      end: "16:00"
      timezone: "America/New_York"
```

### Trigger Conditions

#### Trigger 1: Position Opens Outside Session
```python
def check_position_event(position_event):
    contract_id = position_event['contractId']
    symbol = extract_symbol(contract_id)

    if not is_within_session(symbol, datetime.now()):
        return BREACH
```

#### Trigger 2: Session End Time Reached
```python
def check_session_end():
    current_time = datetime.now()

    for symbol, session in sessions.items():
        if current_time >= session['end_time']:
            if config['close_positions_at_session_end']:
                return BREACH
```

#### Trigger 3: Holiday Detected
```python
def is_holiday(date):
    return date.strftime("%Y-%m-%d") in holiday_calendar
```

### Holiday Calendar
```yaml
# config/holidays.yaml
holidays:
  - "2025-01-01"  # New Year's Day
  - "2025-07-04"  # Independence Day
  - "2025-12-25"  # Christmas
```

### Enforcement Actions

#### If Position Opens Outside Session
1. **Close position immediately** via MOD-001
2. **Set lockout** via MOD-002 → Until session starts
3. **Cancel all orders**
4. **Log enforcement**

#### At Session End
1. **Close all positions** via MOD-001
2. **Cancel all orders**
3. **Set lockout** → Until next session start

### Session Time Logic

#### Global Session Check
```python
def is_within_session(symbol, current_time):
    if not config['global_session']['enabled']:
        return True

    tz = timezone(config['global_session']['timezone'])
    local_time = current_time.astimezone(tz)

    session_start = time(9, 30)
    session_end = time(16, 0)

    if session_start <= local_time.time() <= session_end:
        if config['respect_holidays'] and is_holiday(local_time.date()):
            return False  # Holiday
        return True  # Within session
    else:
        return False  # Outside session
```

#### Per-Instrument Override (ES Example)
```python
# ES: Sunday 18:00 - Friday 17:00 (nearly 24/5)
def is_within_session_es(current_time):
    tz = timezone("America/Chicago")
    local_time = current_time.astimezone(tz)

    day_of_week = local_time.weekday()  # 0=Mon, 6=Sun
    hour = local_time.hour

    # Sunday 18:00 onwards
    if day_of_week == 6 and hour >= 18:
        return True

    # Monday-Thursday (all day)
    if 0 <= day_of_week <= 3:
        return True

    # Friday until 17:00
    if day_of_week == 4 and hour < 17:
        return True

    return False
```

### Reset Timing
**Next session start time**
- Calculated based on current time and session configuration
- Can be same day or next day
- Respects weekends and holidays

### Edge Cases
1. **Timezone handling**: Must convert to correct timezone
2. **Overnight sessions**: ES runs Sunday 6pm - Friday 5pm (crosses days)
3. **Holiday + weekend**: Multiple days locked out
4. **Per-instrument vs global**: Which takes precedence?
5. **Session end auto-close**: Optional feature (configurable)

### Implementation Details

#### State Tracking
```python
session_state = {
    "current_session": "open",  # "open", "closed", "holiday"
    "next_session_start": datetime(2025, 1, 18, 9, 30),
    "next_session_end": datetime(2025, 1, 18, 16, 0)
}
```

#### Background Timer
```python
# Check every minute
def check_session_status():
    if is_session_end_reached():
        if config['close_positions_at_session_end']:
            enforce_session_end(account_id)
```

#### API Requirements
- **Trigger**: `GatewayUserPosition` event + background timer
- **Enforcement**:
  - `POST /api/Position/closeContract`
  - `POST /api/Order/cancel`

#### Dependencies
- **MOD-001** (actions.py) - close_all_positions(), close_position(), cancel_all_orders()
- **MOD-002** (lockout_manager.py) - set_lockout()
- **MOD-003** (timer_manager.py) - Session end timer
- **MOD-004** (reset_scheduler.py) - Holiday calendar integration
- **utils/datetime_helpers.py** - Timezone conversion
- **utils/holidays.py** - Holiday calendar

### Sources Found

#### Primary Source: Comprehensive Specification
- **File**: `/docs/PROJECT_DOCS/rules/09_session_block_outside.md`
- **Lines**: 1-309 (extremely comprehensive)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Extremely detailed
- **Key Details**:
  - Global + per-instrument session configuration
  - Holiday calendar integration
  - Timezone handling logic
  - Three trigger conditions
  - Session end auto-close
  - Multiple test scenarios
  - CLI display examples

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 101-133
- **Detail Level**: Summary
- **Key Details**:
  - Category 3: Hard Lockout
  - Unlock at session start time

### Conflicts/Variations
**No conflicts found.** Documentation is highly detailed and consistent.

### Recommendation
**Use primary source** (`09_session_block_outside.md`) as authoritative specification.
- Most comprehensive session handling details
- Includes holiday calendar
- Complete timezone logic
- Per-instrument override examples

---

## RULE-010: AuthLossGuard

### Specification Summary
- **Purpose**: Monitor TopstepX `canTrade` status and lockout when API signals account is restricted
- **Trigger**: `GatewayUserAccount` event (when `canTrade` field changes)
- **Enforcement**: Close all positions + Hard lockout (no expiry, manual unlock only)
- **Parameters**:
  - `enabled`: true/false
  - `enforcement`: "close_all_and_lockout"

### Enforcement Category
**Hard Lockout** (Category 3)

### Scope
**Account-wide** (based on TopstepX account status)

### Trigger Logic
```python
def check(account_event):
    can_trade = account_event['canTrade']

    if not can_trade:
        return BREACH  # TopstepX says account cannot trade
```

### API Event Payload
```json
{
  "id": 123,
  "balance": 10000.0,
  "canTrade": false   // ← This triggers breach
}
```

### Enforcement Actions
1. **Close all positions** via MOD-001
2. **Set lockout** via MOD-002:
   - No expiry time (manual unlock only)
   - Reason: "Account restricted by TopstepX"
3. **Display**: `"🔴 ACCOUNT RESTRICTED - Contact TopstepX support"`

### Auto-Unlock
**When `canTrade: true` event received**, lockout clears automatically.

### Reset Timing
**API-driven** (no time-based reset)
- Lockout persists until TopstepX sends `canTrade: true`
- OR admin manually unlocks

### Edge Cases
1. **API-driven enforcement**: TopstepX controls the state
2. **Reason unknown**: TopstepX may not provide reason for restriction
3. **Multiple restrictions**: Could be margin call, rule violation, etc.
4. **Auto-clear**: Must handle `canTrade: true` event to auto-unlock

### Implementation Details

#### State Tracking
- Track `canTrade` status
- Persist lockout state in SQLite
- Listen for account update events

#### API Requirements
- **Trigger**: SignalR `GatewayUserAccount` event
- **Enforcement**: Close all positions

#### Dependencies
- **MOD-001** (actions.py) - close_all_positions()
- **MOD-002** (lockout_manager.py) - set_lockout(), clear_lockout()

### Sources Found

#### Primary Source: Brief Specification
- **File**: `/docs/PROJECT_DOCS/rules/10_auth_loss_guard.md`
- **Lines**: 1-49 (brief specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Brief but complete
- **Key Details**:
  - Monitors `canTrade` field
  - Hard lockout, no expiry
  - Auto-unlock on `canTrade: true`
  - Use case: TopstepX-driven restrictions

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 101-133
- **Detail Level**: Summary
- **Key Details**:
  - Category 3: Hard Lockout
  - Unlock: Admin only (or API-driven)

### Conflicts/Variations
**No conflicts found.**

### Recommendation
**Use primary source** (`10_auth_loss_guard.md`) as authoritative specification.
- Clear API-driven enforcement model
- Important integration with TopstepX account status

---

## RULE-011: SymbolBlocks

### Specification Summary
- **Purpose**: Blacklist specific symbols - close any position immediately and permanently lockout that symbol
- **Trigger**: `GatewayUserPosition` event (when position opens in blocked symbol)
- **Enforcement**: Close position + Symbol-specific permanent lockout
- **Parameters**:
  - `enabled`: true/false
  - `blocked_symbols`: Array of symbol names (e.g., ["RTY", "BTC"])
  - `enforcement`: "close_and_lockout_symbol"

### Enforcement Category
**Trade-by-Trade** (Category 1) with symbol-specific permanent lockout

### Scope
**Per-symbol** (lockout applies to specific symbol, not entire account)

### Trigger Logic
```python
def check(position_event):
    symbol = extract_symbol(position_event['contractId'])

    if symbol in config['blocked_symbols']:
        return BREACH, symbol
```

### Enforcement Actions
1. **Close position immediately** via MOD-001
2. **Set permanent symbol lockout** via MOD-002:
   - `set_lockout(account_id, f"Symbol {symbol} is blacklisted", until=datetime.max)`
   - Symbol-specific lockout (not account-wide)
3. **Any future fills in this symbol** → Close instantly

### Lockout Type
**Symbol-specific permanent lockout**
- No expiry time
- Only applies to blocked symbol
- Can still trade other symbols
- Requires admin override to remove from blacklist

### Reset Timing
**Permanent** (no reset, requires manual configuration change)

### Edge Cases
1. **Symbol extraction**: Must correctly parse contract ID
2. **Partial fills**: If trader somehow gets filled again → instant close
3. **Symbol-specific lockout**: More complex than account-wide lockout
4. **Configuration change**: Removing symbol from blacklist should clear lockout

### Implementation Details

#### State Tracking
```python
# Track symbol-specific lockouts
symbol_lockouts = {
    ("account_123", "RTY"): {
        "reason": "Symbol RTY is blacklisted",
        "locked_at": datetime(2025, 1, 17, 10, 30),
        "expires_at": datetime.max  # Permanent
    }
}
```

#### API Requirements
- **Trigger**: `GatewayUserPosition` event
- **Enforcement**: `POST /api/Position/closeContract`

#### Dependencies
- **MOD-001** (actions.py) - close_position()
- **MOD-002** (lockout_manager.py) - set_lockout() with symbol-specific support

### Sources Found

#### Primary Source: Brief Specification
- **File**: `/docs/PROJECT_DOCS/rules/11_symbol_blocks.md`
- **Lines**: 1-44 (brief specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Brief but clear
- **Key Details**:
  - Permanent symbol lockout
  - Use case: "I always lose on RTY, never let me trade it"
  - No expiry

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 42-66
- **Detail Level**: Summary
- **Key Details**:
  - Category 1: Trade-by-Trade
  - Close position in blocked symbol

### Conflicts/Variations
**No conflicts found.**

### Recommendation
**Use primary source** (`11_symbol_blocks.md`) as authoritative specification.
- Clear blacklist concept
- Symbol-specific permanent lockout is unique feature

---

## RULE-012: TradeManagement

### Specification Summary
- **Purpose**: Automated trade management - auto breakeven stop, trailing stops
- **Trigger**: `GatewayUserPosition` event + market price updates
- **Enforcement**: Modify stop-loss orders (NOT closing positions, NOT lockout)
- **Parameters**:
  - `auto_breakeven.enabled`: Enable auto breakeven
  - `auto_breakeven.profit_trigger_ticks`: Move SL to BE after N ticks profit (e.g., 10)
  - `trailing_stop.enabled`: Enable trailing stop
  - `trailing_stop.activation_ticks`: Start trailing after N ticks profit (e.g., 20)
  - `trailing_stop.trail_distance_ticks`: Trail N ticks behind high (e.g., 10)

### Enforcement Category
**Automation** (Category 4) - NOT a risk rule, just automation

### Scope
**Per-position** (manages each position's stop-loss independently)

### Trigger Logic
```python
def check(position_event, current_price):
    unrealized_profit_ticks = calculate_ticks(position_event, current_price)

    # Auto Breakeven
    if config['auto_breakeven']['enabled']:
        if unrealized_profit_ticks >= config['auto_breakeven']['profit_trigger_ticks']:
            return ACTION_MOVE_SL_TO_BREAKEVEN

    # Trailing Stop
    if config['trailing_stop']['enabled']:
        if unrealized_profit_ticks >= config['trailing_stop']['activation_ticks']:
            return ACTION_UPDATE_TRAILING_STOP
```

### Enforcement Actions
1. **Modify stop-loss order** via API:
   ```http
   POST /api/Order/modify
   {
     "accountId": 123,
     "orderId": 789,
     "stopPrice": 21005.0  // New stop (breakeven or trailing)
   }
   ```
2. **NO position close**
3. **NO lockout**

### Auto Breakeven Logic
- Wait until position is +10 ticks (configurable)
- Move stop-loss to entry price (breakeven)
- Protects against loss after profit achieved

### Trailing Stop Logic
- Wait until position is +20 ticks (configurable)
- Start trailing stop 10 ticks behind highest price
- Update stop as price moves higher
- Lock in profits

### Reset Timing
N/A (per-position automation)

### Edge Cases
1. **Stop-loss order must exist**: Can't modify if no SL placed
2. **Tick calculation**: Different for each instrument
3. **Price updates**: Requires real-time market data
4. **Order modification API**: Must support modifying stop price

### Implementation Details

#### State Tracking
- Track highest price reached per position
- Track current stop-loss order ID
- Calculate ticks from entry price

#### API Requirements
- **Trigger**: `GatewayUserPosition` + market data
- **Action**: `POST /api/Order/modify` (modify SL order)

#### Dependencies
None (no enforcement modules, just order modification)

### Sources Found

#### Primary Source: Brief Specification
- **File**: `/docs/PROJECT_DOCS/rules/12_trade_management.md`
- **Lines**: 1-59 (specification)
- **Version**: 2.0
- **Last Updated**: 2025-01-17
- **Detail Level**: Good
- **Key Details**:
  - Auto breakeven trigger
  - Trailing stop logic
  - Order modification API
  - Use case: Automated risk management

#### Secondary Source: Categorization
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 136-146
- **Detail Level**: Summary
- **Key Details**:
  - Category 4: Automation
  - Not enforcement, just automation

### Conflicts/Variations
**No conflicts found.**

### Recommendation
**Use primary source** (`12_trade_management.md`) as authoritative specification.
- Clear automation logic
- Not a risk enforcement rule, separate category

---

## RULE-013: DailyRealizedProfit (NEW - No Dedicated Spec File)

### Specification Summary
- **Purpose**: Take profit and stop trading once daily target hit
- **Trigger**: `GatewayUserTrade` event (cumulative daily realized profit)
- **Enforcement**: Close all positions + Hard lockout until reset time
- **Parameters**:
  - `target`: Daily profit target (positive value, e.g., 1000)
  - `reset_time`: Daily reset time (e.g., "17:00")
  - `enforcement.close_all`: Close all positions (take profit)
  - `enforcement.cancel_orders`: Stop further trading
  - `enforcement.lockout_until_reset`: Lock until reset time

### Enforcement Category
**Hard Lockout** (Category 3)

### Scope
**Account-wide** (cumulative daily realized P&L)

### Calculation Logic
```python
# Similar to RULE-003, but checking profit target
daily_realized_pnl = pnl_tracker.get_daily_realized_pnl(account_id)

if daily_realized_pnl >= config['target']:
    BREACH  # Hit profit target
```

### Enforcement Actions
1. **Close all positions** (lock in profit!)
2. **Cancel all orders**
3. **Lock account until reset time** (5:00 PM)
4. **Message**: "Daily profit target reached! Good job! See you tomorrow."

### Reset Timing
**Daily at reset time** (e.g., 5:00 PM)

### Why Hard Lockout?
**Prevents giving back profits through overtrading.**
Forces trader to stop on a winning day.

### Edge Cases
1. **Similar to RULE-003**: Same P&L tracking mechanism
2. **Profit protection**: Opposite of loss limit
3. **Psychological**: "Take the win and walk away"

### Implementation Details

#### State Tracking
- Same as RULE-003 (daily realized P&L in SQLite)
- Reuse PnLTracker infrastructure

#### API Requirements
- Same as RULE-003 (close all, cancel all)

#### Dependencies
- **MOD-001** (actions.py) - close_all_positions(), cancel_all_orders()
- **MOD-002** (lockout_manager.py) - set_lockout()
- **MOD-004** (reset_scheduler.py) - Daily reset
- **pnl_tracker.py** - Daily realized P&L tracking

### Sources Found

#### Primary Source: RULE_CATEGORIES.md
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 239-271
- **Version**: N/A
- **Last Updated**: 2025-10-23
- **Detail Level**: Good summary
- **Key Details**:
  - Category 3: Hard Lockout
  - Daily profit target enforcement
  - Lock until 5 PM
  - Use case: Prevent giving back profits

#### Secondary Source: Enforcement Matrix
- **File**: `/docs/current/RULE_CATEGORIES.md`
- **Lines**: 219-236
- **Detail Level**: Summary table
- **Key Details**:
  - Close All: Yes
  - Cancel Orders: Yes
  - Lockout Type: Hard (5 PM)
  - Can Trade Again: At reset/admin

### Conflicts/Variations

**MISSING DEDICATED SPEC FILE:**
- RULE-013 is mentioned in `RULE_CATEGORIES.md` (dated 2025-10-23)
- No corresponding file in `/docs/PROJECT_DOCS/rules/`
- No `13_daily_realized_profit.md` file exists

This suggests:
1. RULE-013 was **added recently** (after 2025-01-17 when other specs were written)
2. OR it's a **planned feature** not yet fully specified
3. OR it was **overlooked** when creating individual spec files

### Recommendation

**CREATE DEDICATED SPEC FILE:**

RULE-013 needs a full specification file (`13_daily_realized_profit.md`) matching the detail level of other rules.

**Recommended Structure** (based on RULE-003 as template):
```markdown
# RULE-013: DailyRealizedProfit

**Purpose:** Enforce daily profit target - close positions and stop trading when target hit.

## Config
```yaml
daily_realized_profit:
  enabled: true
  target: 1000.0
  reset_time: "17:00"
  timezone: "America/New_York"
  enforcement: "close_all_and_lockout"
  lockout_until_reset: true
```

## Trigger
**Event Type:** `GatewayUserTrade`

[Full specification following same format as RULE-003]
```

**Until then**: Use RULE_CATEGORIES.md as specification, but note that it lacks:
- Detailed implementation logic
- SQLite schema details
- Test scenarios
- API requirements
- Edge cases

---

## Cross-Cutting Concerns

### 1. State Persistence Requirements

**Rules Requiring SQLite Persistence:**

| Rule | Persistence Needed | Schema | Reset Frequency |
|------|-------------------|--------|-----------------|
| RULE-003 | Daily realized P&L | daily_pnl table | Daily at reset_time |
| RULE-004 | None (real-time calc) | - | N/A |
| RULE-005 | None (real-time calc) | - | N/A |
| RULE-006 | Trade counts | trade_counts table | Rolling windows |
| RULE-007 | Cooldown timers | timers table | When expired |
| RULE-009 | Session state | session_state table | Daily/session-based |
| RULE-013 | Daily realized P&L | Same as RULE-003 | Daily at reset_time |

**Shared Tables:**
- `daily_pnl` - Used by RULE-003 and RULE-013
- `lockouts` - Used by RULE-003, 009, 010, 013
- `timers` - Used by RULE-006, 007, 008

### 2. SDK Dependencies

**All rules depend on SDK for:**
- Event triggers (positions, trades, orders, accounts)
- Enforcement actions (close positions, cancel orders)
- Current state queries (positions, orders, P&L)

**SDK Event Types Used:**

| Event Type | Rules Using It |
|------------|----------------|
| `GatewayUserPosition` | RULE-001, 002, 004, 005, 008, 009, 011, 012 |
| `GatewayUserTrade` | RULE-003, 006, 007, 013 |
| `GatewayUserOrder` | RULE-008 |
| `GatewayUserAccount` | RULE-010 |
| Market Data | RULE-004, 005, 012 |

### 3. Enforcement Modules (MOD-001 through MOD-004)

**MOD-001: Enforcement Actions**
- `close_all_positions(account_id)`
- `close_position(account_id, contract_id)`
- `reduce_position(account_id, contract_id, quantity)`
- `cancel_all_orders(account_id)`
- Used by: All rules except RULE-012

**MOD-002: Lockout Manager**
- `set_lockout(account_id, reason, until)`
- `is_locked_out(account_id)`
- `clear_lockout(account_id)`
- `get_lockout_info(account_id)`
- Used by: RULE-003, 006, 007, 009, 010, 011, 013

**MOD-003: Timer Manager**
- `start_timer(account_id, duration, reason)`
- `get_remaining_time(account_id)`
- `clear_timer(account_id)`
- Used by: RULE-006, 007, 008

**MOD-004: Reset Scheduler**
- `schedule_daily_reset(account_id, reset_time)`
- `reset_daily_counters(account_id)`
- Holiday calendar integration
- Used by: RULE-003, 004, 005, 009, 013

### 4. Real-Time Market Data Requirements

**Rules Requiring Market Price Updates:**
- RULE-004: Daily Unrealized Loss (need current prices)
- RULE-005: Max Unrealized Profit (need current prices)
- RULE-012: Trade Management (need current prices for tick calculations)

**Implementation Challenge:**
- SDK may or may not provide real-time price streaming
- May need separate market data subscription
- Critical for unrealized P&L calculations

### 5. Symbol Extraction Pattern

**Multiple rules need to extract symbol from contract ID:**
```python
def extract_symbol(contract_id):
    # "CON.F.US.MNQ.U25" → "MNQ"
    parts = contract_id.split('.')
    return parts[3] if len(parts) >= 4 else contract_id
```

**Used by:**
- RULE-002: Per-instrument limits
- RULE-009: Per-instrument sessions
- RULE-011: Symbol blacklist

**Shared utility needed** in `utils/symbol_helpers.py`

### 6. Timezone Handling

**Rules with timezone requirements:**
- RULE-003: Reset time in specific timezone
- RULE-009: Session times in multiple timezones
- RULE-013: Reset time in specific timezone

**Need timezone library:**
- `pytz` or `zoneinfo`
- Conversion utilities
- DST handling

### 7. Configuration System

**All rules share YAML configuration:**
```yaml
# config/risk_config.yaml
rules:
  max_contracts:
    enabled: true
    limit: 5
    # ...

  daily_realized_loss:
    enabled: true
    limit: -500
    # ...

  # ... (all 13 rules)
```

**Configuration loader needed:**
- Parse YAML
- Validate schema
- Hot-reload capability
- Rule enable/disable

### 8. Logging System

**All rules need:**
- Enforcement logging
- Breach detection logging
- Performance logging
- Audit trail

**Standardized log format:**
```
[2025-01-17 14:23:15] [RULE-003] [BREACH] Daily loss limit: $-520 / $-500
[2025-01-17 14:23:15] [RULE-003] [ENFORCE] Closed all positions, set lockout until 17:00
```

### 9. CLI Display Requirements

**All rules need CLI representation:**
- Current status
- Limits/thresholds
- Breach warnings
- Lockout countdowns
- Recent enforcement log

**Trader CLI needs to show:**
```
╔═══════════════════════════════════════════════════════╗
║  Risk Manager Status                                  ║
╠═══════════════════════════════════════════════════════╣
║  Max Contracts: 4/5 🟢                                ║
║  Daily P&L: -$450 / -$500 ⚠️ (90%)                   ║
║  Trade Frequency: 2/3 per min 🟢                      ║
║                                                       ║
║  Lockouts:                                            ║
║    None ✅                                            ║
║                                                       ║
║  Recent Enforcements:                                 ║
║    [14:23:15] MaxContracts - Closed MNQ position      ║
╚═══════════════════════════════════════════════════════╝
```

### 10. Testing Strategy

**Each rule needs:**
- Unit tests (rule logic in isolation)
- Integration tests (with SDK events)
- E2E tests (full enforcement flow)
- Edge case tests

**Common test fixtures needed:**
- Mock SDK events
- Mock position data
- Mock trade data
- Time manipulation (for reset/timer tests)

### 11. Performance Considerations

**High-frequency event processing:**
- RULE-001, 002: Every position update (high frequency)
- RULE-003, 006, 007: Every trade (medium frequency)
- RULE-004, 005, 012: Every price update (very high frequency)

**Optimization needed:**
- Efficient state queries
- Caching where appropriate
- Avoid blocking operations
- Async/await throughout

### 12. Rule Interaction Scenarios

**Potential conflicts:**
1. **RULE-003 + RULE-013**: Both track daily realized P&L
   - Hit loss limit AND profit target? (Impossible, but check)
   - Share same P&L tracker

2. **RULE-004 + RULE-005**: Both track unrealized P&L
   - Position has high unrealized loss AND profit? (Different positions)
   - Check which rule fires first

3. **RULE-006 + RULE-007**: Both create cooldowns
   - Hit frequency limit AND big loss in same trade?
   - Which cooldown wins? (Longer duration?)

4. **RULE-009 + Any rule**: Session lockout
   - If locked out by session, other rules don't evaluate
   - Lockout manager checks this first

**Rule evaluation order matters:**
1. Check lockout state first (RULE-009, 010)
2. Check position-level rules (RULE-001, 002, 008, 011)
3. Check P&L rules (RULE-003, 004, 005, 013)
4. Check frequency rules (RULE-006, 007)
5. Apply automation (RULE-012)

---

## Implementation Priorities

### Phase 1: Foundation (SDK + Core Infrastructure)
**Status: ~80% complete**
- [x] SDK integration (TradingSuite wrapper)
- [x] Event bridge (SDK events → Risk events)
- [x] Basic enforcement (close/cancel via SDK)
- [ ] State persistence (SQLite schema)
- [ ] Configuration loader (YAML)

### Phase 2: State Management
**Status: ~30% complete**
- [x] In-memory state tracking
- [ ] PnLTracker with SQLite
- [ ] LockoutManager with SQLite
- [ ] TimerManager with SQLite
- [ ] TradeCounter with SQLite
- [ ] ResetScheduler

### Phase 3: Trade-by-Trade Rules (6 rules)
**Status: ~33% complete**
- [x] RULE-001: MaxContracts
- [x] RULE-002: MaxContractsPerInstrument
- [ ] RULE-004: DailyUnrealizedLoss
- [ ] RULE-005: MaxUnrealizedProfit
- [ ] RULE-008: NoStopLossGrace
- [ ] RULE-011: SymbolBlocks

### Phase 4: Timer/Cooldown Rules (2 rules)
**Status: 0% complete**
- [ ] RULE-006: TradeFrequencyLimit
- [ ] RULE-007: CooldownAfterLoss

### Phase 5: Hard Lockout Rules (4 rules)
**Status: 0% complete**
- [ ] RULE-003: DailyRealizedLoss
- [ ] RULE-009: SessionBlockOutside
- [ ] RULE-010: AuthLossGuard
- [ ] RULE-013: DailyRealizedProfit

### Phase 6: Automation (1 rule)
**Status: 0% complete**
- [ ] RULE-012: TradeManagement

### Phase 7: CLI & Service
**Status: 0% complete**
- [ ] Trader CLI
- [ ] Admin CLI
- [ ] Windows Service wrapper

---

## Major Conflicts Requiring Resolution

### 1. RULE-004 Enforcement Type

**Conflict:**
- Primary spec (2025-01-17): Hard Lockout, close all
- Categories doc (2025-10-23): Trade-by-Trade, close that position only

**Resolution needed:**
- [ ] Decide enforcement approach
- [ ] Update primary spec OR
- [ ] Update categories doc
- [ ] Create new version (v2.1)

**Recommendation:** Use Trade-by-Trade (Categories doc is more recent and explicitly states correction)

### 2. RULE-005 Enforcement Type

**Conflict:**
- Primary spec: Hard Lockout, close all
- Categories doc: Trade-by-Trade, close that position only

**Resolution needed:**
- [ ] Decide: Take profit and stop OR Take profit and continue?
- [ ] Make configurable in YAML?
- [ ] Update specs

**Recommendation:** Make configurable with default to Trade-by-Trade

### 3. RULE-013 Missing Dedicated Spec

**Issue:**
- Mentioned in RULE_CATEGORIES.md
- No dedicated spec file exists
- No detailed implementation guide

**Resolution needed:**
- [ ] Create `13_daily_realized_profit.md`
- [ ] Full specification matching detail level of RULE-003
- [ ] Test scenarios
- [ ] API requirements

**Recommendation:** Create full spec file using RULE-003 as template

---

## Documentation Quality Assessment

### Primary Specs (/docs/PROJECT_DOCS/rules/)
**Quality: Excellent (with noted conflicts)**

**Strengths:**
- Version controlled (v2.0)
- Dated (2025-01-17)
- Comprehensive technical details
- Code examples
- Test scenarios
- API requirements

**Weaknesses:**
- RULE-004, 005 have enforcement type conflicts
- RULE-013 missing
- Some specs brief (RULE-004, 005, 010, 011)
- No cross-rule interaction documented

### Secondary Docs (/docs/current/)
**Quality: Very Good (more recent)**

**Strengths:**
- Updated categorization (2025-10-23)
- Explicit correction notes
- Enforcement matrix
- SDK mapping examples
- Implementation guidance

**Weaknesses:**
- Some rules lack detail
- RULE-013 only in categories, not detailed
- Cross-cutting concerns not fully documented

### Overall Documentation Health
**Score: 8.5/10**

**Excellent:**
- Comprehensive coverage
- Multiple perspectives (spec + implementation)
- Version tracking
- Code examples

**Needs Improvement:**
- Resolve RULE-004, 005 conflicts
- Create RULE-013 dedicated spec
- Expand brief specs (RULE-010, 011)
- Document rule interactions
- Testing strategy document

---

## Recommendations for Wave 1

### Immediate Actions

1. **Resolve Conflicts:**
   - [ ] Update RULE-004 spec to Trade-by-Trade
   - [ ] Update RULE-005 spec OR make configurable
   - [ ] Create RULE-013 dedicated spec file

2. **Complete Foundation:**
   - [ ] Finalize SQLite schema (all tables)
   - [ ] Implement state managers (PnL, Lockout, Timer, TradeCounter)
   - [ ] Implement reset scheduler
   - [ ] Configuration loader with validation

3. **Implementation Order:**
   - [ ] Trade-by-Trade rules first (simpler, no state)
   - [ ] Timer/Cooldown rules second (adds timers)
   - [ ] Hard Lockout rules third (adds daily resets)
   - [ ] Automation rule last (different category)

4. **Testing Infrastructure:**
   - [ ] Mock SDK event generators
   - [ ] Test fixtures for all event types
   - [ ] Time manipulation utilities
   - [ ] Integration test suite

5. **Documentation Updates:**
   - [ ] Create RULE-013 spec
   - [ ] Update RULE-004, 005 specs
   - [ ] Cross-cutting concerns document
   - [ ] Rule interaction matrix

---

## Summary Statistics

### Rules by Category
- **Trade-by-Trade:** 6 rules (RULE-001, 002, 004, 005, 008, 011)
- **Timer/Cooldown:** 2 rules (RULE-006, 007)
- **Hard Lockout:** 4 rules (RULE-003, 009, 010, 013)
- **Automation:** 1 rule (RULE-012)
- **Total:** 13 rules

### Implementation Status
- **Fully Specified:** 12 rules (RULE-001 through RULE-012)
- **Partially Specified:** 1 rule (RULE-013 - no dedicated file)
- **Implemented:** 2 rules (RULE-001, 002 per PROJECT_STATUS.md)
- **Remaining:** 11 rules

### State Management Requirements
- **SQLite Tables Needed:** 5 (daily_pnl, lockouts, timers, trade_counts, session_state)
- **Background Schedulers:** 2 (daily reset, session checker)
- **Real-time Calculations:** 3 (RULE-004, 005, 012 need market data)

### Dependencies
- **SDK Events:** 5 types (Position, Trade, Order, Account, Market Data)
- **Enforcement Modules:** 4 (MOD-001 through MOD-004)
- **Shared Utilities:** Symbol extraction, timezone handling, logging

### Documentation Files Analyzed
- **Primary Specs:** 12 files (01-12_*.md)
- **Supplementary Docs:** 2 files (RULE_CATEGORIES.md, RULES_TO_SDK_MAPPING.md)
- **Total Lines Reviewed:** ~3,500 lines
- **Conflicts Identified:** 2 major (RULE-004, 005)
- **Missing Specs:** 1 (RULE-013)

---

**Analysis Complete**

**Researcher:** RESEARCHER 1 - Risk Rules Specialist
**Date:** 2025-10-25
**Files Analyzed:** 14 documentation files
**Rules Cataloged:** 13 (12 fully specified, 1 partial)
**Conflicts Found:** 2 (RULE-004, 005 enforcement types)
**Missing Specs:** 1 (RULE-013 dedicated file)

**Next Steps:** Pass to RESEARCHER 2 for Enforcement Modules analysis.
