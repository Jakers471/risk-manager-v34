# Wave 2 Gap Analysis: Risk Rules Implementation

**Analysis Date**: 2025-10-25
**Researcher**: RESEARCHER 1 - Risk Rules Gap Analyst
**Project**: Risk Manager V34
**Working Directory**: `/mnt/c/Users/jakers/Desktop/risk-manager-v34`

---

## Executive Summary

The Risk Manager V34 project has **10 of 13 risk rules missing** (77% gap). Only 3 rules are fully implemented, with strong foundational architecture in place but significant rule implementation work remaining.

### Key Metrics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Rules Specified** | 13 | 100% |
| **Fully Implemented** | 2 | 15% |
| **Partially Implemented** | 1 | 8% |
| **Missing/Not Started** | 10 | 77% |
| **Estimated Effort Remaining** | 3-4 weeks | - |

### Critical Findings

1. **Strong Foundation**: Core architecture, SDK integration, and testing infrastructure are 100% complete
2. **Missing State Managers**: 3 critical state management modules (MOD-002, MOD-003, MOD-004) are blocking 7 rules
3. **Documentation Complete**: All 13 rules have comprehensive specifications
4. **No Architectural Blockers**: Clear implementation path forward

---

## Implementation Status Matrix

| Rule ID | Name | Category | Status | Priority | Estimated Effort | Dependencies |
|---------|------|----------|--------|----------|------------------|--------------|
| **RULE-001** | MaxContracts | Trade-by-Trade | ✅ Implemented | Critical | Done | None |
| **RULE-002** | MaxContractsPerInstrument | Trade-by-Trade | ✅ Implemented | Critical | Done | None |
| **RULE-003** | DailyRealizedLoss | Hard Lockout | ⚠️ Partial (70%) | Critical | 1 day | PnLTracker ✅, MOD-002 ❌, MOD-004 ❌ |
| **RULE-004** | DailyUnrealizedLoss | Trade-by-Trade | ❌ Missing | High | 2 days | Market Data Feed, Real-time Calc |
| **RULE-005** | MaxUnrealizedProfit | Trade-by-Trade | ❌ Missing | Medium | 2 days | Market Data Feed, Real-time Calc |
| **RULE-006** | TradeFrequencyLimit | Timer/Cooldown | ❌ Missing | High | 2-3 days | MOD-003 ❌, Trade Counter |
| **RULE-007** | CooldownAfterLoss | Timer/Cooldown | ❌ Missing | Medium | 1-2 days | MOD-003 ❌, PnLTracker ✅ |
| **RULE-008** | NoStopLossGrace | Trade-by-Trade | ❌ Missing | Medium | 2 days | MOD-003 ❌, Order Query |
| **RULE-009** | SessionBlockOutside | Hard Lockout | ❌ Missing | High | 3-4 days | MOD-002 ❌, MOD-004 ❌, Holiday Calendar |
| **RULE-010** | AuthLossGuard | Hard Lockout | ❌ Missing | Medium | 1 day | MOD-002 ❌, SDK Account Events |
| **RULE-011** | SymbolBlocks | Trade-by-Trade | ❌ Missing | Low | 1 day | MOD-002 ❌ (symbol-specific lockout) |
| **RULE-012** | TradeManagement | Automation | ❌ Missing | Low | 2-3 days | Market Data, Order Modification API |
| **RULE-013** | DailyRealizedProfit | Hard Lockout | ❌ Missing | Medium | 1 day | PnLTracker ✅, MOD-002 ❌, MOD-004 ❌ |

**Legend**:
- ✅ = Complete
- ⚠️ = Partial
- ❌ = Missing
- Dependencies with ✅ = Already implemented
- Dependencies with ❌ = Must implement first

---

## Detailed Gap Analysis

### ✅ Implemented Rules (2 of 13)

---

#### RULE-001: MaxContracts (Account-Wide Position Limit)

**Status**: ✅ **Fully Implemented**

**Implementation**: `src/risk_manager/rules/max_position.py` (73 lines)

**Capabilities**:
- Enforces maximum total contracts across all instruments
- Configurable per-instrument vs total limit modes
- Real-time position tracking
- Immediate enforcement via SDK

**Enforcement**:
- **Type**: Trade-by-Trade (Category 1)
- **Action**: Close all positions or reduce to limit
- **Lockout**: None
- **Can Trade Again**: Immediately

**Tests**: Basic coverage, needs expansion

**Production Readiness**: ✅ Ready for deployment

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 35-168

---

#### RULE-002: MaxContractsPerInstrument

**Status**: ✅ **Fully Implemented** (Most Advanced Rule)

**Implementation**: `src/risk_manager/rules/max_contracts_per_instrument.py` (262 lines)

**Capabilities**:
- Per-symbol position limits (e.g., MNQ: 2, ES: 1)
- Flexible enforcement modes:
  - `reduce_to_limit` - Partial close to exact limit
  - `close_all` - Close entire position
- Unknown symbol handling:
  - `block` - Prevent trading unknown symbols
  - `allow` - Permit unlimited trading
  - `allow_with_limit:N` - Apply default limit
- Symbol extraction from contract IDs
- Integration with SDK enforcement executor

**Enforcement**:
- **Type**: Trade-by-Trade (Category 1)
- **Action**: Reduce to limit or close position
- **Lockout**: None
- **Can Trade Again**: Immediately

**Tests**: Good coverage, needs edge case expansion

**Production Readiness**: ✅ Ready for deployment

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 170-284

**Example Configuration**:
```yaml
max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 2
    ES: 1
    NQ: 3
  enforcement: "reduce_to_limit"  # or "close_all"
  unknown_symbol_action: "block"  # or "allow" or "allow_with_limit:2"
```

---

### ⚠️ Partially Implemented Rules (1 of 13)

---

#### RULE-003: DailyRealizedLoss

**Status**: ⚠️ **70% Complete** - Basic structure exists, needs integration

**Implementation**: `src/risk_manager/rules/daily_loss.py` (49 lines)

**What's Done**:
- ✅ Basic rule structure and class
- ✅ Event subscription logic (PNL_UPDATED, POSITION_CLOSED)
- ✅ Breach detection logic (daily_pnl <= limit)
- ✅ Configuration validation

**What's Missing**:
- ❌ Integration with PnLTracker (exists but not wired)
- ❌ Lockout coordination (MOD-002 doesn't exist)
- ❌ Daily reset handling (MOD-004 doesn't exist)
- ❌ Comprehensive tests
- ❌ Enforcement method implementation

**Enforcement**:
- **Type**: Hard Lockout (Category 3)
- **Action**: Close all positions + Cancel all orders + Lock until reset time
- **Lockout**: Until 5:00 PM (configurable reset_time) or admin override
- **Can Trade Again**: At reset time or admin unlock

**Blockers**:
1. **MOD-002 (LockoutManager)** - Missing, required for lockout enforcement
2. **MOD-004 (ResetScheduler)** - Missing, required for daily reset at 5 PM

**Estimated Effort**: 1 day (after MOD-002 and MOD-004 exist)

**Priority**: Critical (account violation prevention)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 286-468

**Example Configuration**:
```yaml
daily_realized_loss:
  enabled: true
  limit: -500.0  # Max daily loss ($500)
  reset_time: "17:00"  # 5 PM ET
  timezone: "America/New_York"
  enforcement: "close_all_and_lockout"
  lockout_until_reset: true
```

**Implementation Notes**:
- Reuses existing PnLTracker for state persistence
- SQLite table `daily_pnl` already exists
- Only needs wiring to lockout/reset managers

---

### ❌ Missing Rules (10 of 13)

---

#### RULE-004: DailyUnrealizedLoss (Floating Loss Limit)

**Status**: ❌ **Not Started**

**Purpose**: Enforce hard limit on unrealized (floating) loss across all open positions

**Trigger**: `GatewayUserPosition` event + real-time market price updates

**Enforcement**:
- **Type**: Trade-by-Trade (Category 1) - **Recent Design Change**
- **Action**: Close losing position only (not all positions)
- **Lockout**: None
- **Can Trade Again**: Immediately

**Specification Conflict Resolution**:
- Original spec (2025-01-17): Hard Lockout, close all
- Updated categories doc (2025-10-23): Trade-by-Trade, close that position only
- **Resolution**: Use updated categories doc (more recent, explicit correction)

**Complexity**: Medium

**Estimated Effort**: 2 days

**Dependencies**:
1. **Market Data Feed** - Real-time price updates (not SDK event)
2. **Unrealized P&L Calculator** - Calculate (current_price - avg_price) * size * tick_value
3. **Tick Value Map** - Different for each instrument (MNQ: $5, ES: $50, etc.)

**Priority**: High (account violation prevention)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 470-599

**Calculation Logic**:
```python
unrealized_pnl = sum(
    (current_price - avg_entry_price) * position_size * tick_value
    for all open positions
)

if unrealized_pnl <= config['limit']:
    # Close the losing position (trade-by-trade)
    close_position(losing_position)
```

**Implementation Notes**:
- Requires market data subscription (WebSocket or polling)
- Real-time calculation on every price update
- High frequency event processing
- No state persistence needed (real-time calc)

**Example Configuration**:
```yaml
daily_unrealized_loss:
  enabled: true
  limit: -300.0  # Max floating loss
  enforcement: "close_position"  # Close that position only
  tick_values:  # Required for P&L calculation
    MNQ: 5.0
    ES: 50.0
    NQ: 20.0
```

---

#### RULE-005: MaxUnrealizedProfit (Profit Target)

**Status**: ❌ **Not Started**

**Purpose**: Take profit when unrealized gains hit target (prevent giving back profits)

**Trigger**: `GatewayUserPosition` event + real-time market price updates

**Enforcement**:
- **Type**: Trade-by-Trade (Category 1) - **Configurable Design Recommendation**
- **Action**: Close winning position only (take profit)
- **Lockout**: None (default) or configurable Hard Lockout
- **Can Trade Again**: Immediately (or at reset if Hard Lockout mode)

**Specification Conflict Resolution**:
- Original spec: Hard Lockout (close all, lock until 5 PM)
- Updated categories doc: Trade-by-Trade (close winning position, no lockout)
- **Resolution**: Make configurable - both approaches valid
  - Default: Trade-by-Trade (more flexible)
  - Option: Hard Lockout (more conservative)

**Complexity**: Medium

**Estimated Effort**: 2 days

**Dependencies**:
1. **Market Data Feed** - Real-time price updates
2. **Unrealized P&L Calculator** - Same as RULE-004
3. **Tick Value Map** - Same as RULE-004
4. **(Optional) MOD-002** - If using Hard Lockout mode

**Priority**: Medium (profit protection, not account violation)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 601-732

**Calculation Logic**:
```python
unrealized_pnl = sum(
    (current_price - avg_entry_price) * position_size * tick_value
    for all open positions
)

if unrealized_pnl >= config['target']:
    if enforcement_mode == "trade_by_trade":
        # Close winning position only
        close_position(winning_position)
    elif enforcement_mode == "hard_lockout":
        # Close all + lock until reset
        close_all_positions()
        set_lockout(until=reset_time)
```

**Implementation Notes**:
- Same infrastructure as RULE-004 (market data, tick values)
- Can reuse unrealized P&L calculator
- Configurable enforcement mode adds flexibility

**Example Configuration**:
```yaml
max_unrealized_profit:
  enabled: true
  target: 1000.0  # Daily profit target
  enforcement_mode: "trade_by_trade"  # or "hard_lockout"
  lockout_until_reset: false  # true for hard_lockout mode
  reset_time: "17:00"  # Only if lockout_until_reset=true
  tick_values:
    MNQ: 5.0
    ES: 50.0
```

---

#### RULE-006: TradeFrequencyLimit (Overtrading Prevention)

**Status**: ❌ **Not Started**

**Purpose**: Prevent overtrading by limiting trades per time window (minute/hour/session)

**Trigger**: `GatewayUserTrade` event (every trade execution)

**Enforcement**:
- **Type**: Timer/Cooldown (Category 2)
- **Action**: Set cooldown timer (NO position close - trade already happened)
- **Lockout**: Temporary cooldown (60s, 30min, 1hr configurable)
- **Can Trade Again**: When cooldown timer expires

**Complexity**: Medium

**Estimated Effort**: 2-3 days

**Dependencies**:
1. **MOD-003 (TimerManager)** - Missing, required for countdown timers
2. **Trade Counter** - Track trades in rolling time windows
3. **SQLite Persistence** - Store trade counts per window

**Priority**: High (prevent psychological overtrading)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 734-859

**Time Windows**:
- **Per Minute**: Rolling 60-second window (e.g., limit: 3 trades/min)
- **Per Hour**: Rolling 3600-second window (e.g., limit: 10 trades/hr)
- **Per Session**: Since session start (e.g., limit: 50 trades/session)

**Calculation Logic**:
```python
minute_count = count_trades_in_window(account_id, window=60)  # Last 60s
hour_count = count_trades_in_window(account_id, window=3600)  # Last 1 hour
session_count = count_trades_since_session_start(account_id)

if minute_count >= config['limits']['per_minute']:
    set_cooldown(duration=60)  # 1 min cooldown
elif hour_count >= config['limits']['per_hour']:
    set_cooldown(duration=1800)  # 30 min cooldown
elif session_count >= config['limits']['per_session']:
    set_cooldown(duration=3600)  # 1 hr cooldown
```

**Enforcement Notes**:
- **Cannot prevent trade** (already executed)
- **Only prevents NEXT trade** (cooldown timer)
- CLI shows countdown: "🟡 COOLDOWN - 3/3 trades - Unlocks in 47s"

**SQLite Schema**:
```sql
CREATE TABLE trade_counts (
    account_id INTEGER,
    window_start DATETIME,
    count INTEGER,
    PRIMARY KEY (account_id, window_start)
);
```

**Example Configuration**:
```yaml
trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3
    per_hour: 10
    per_session: 50
  cooldown_on_breach:
    per_minute_breach: 60  # 1 min
    per_hour_breach: 1800  # 30 min
    per_session_breach: 3600  # 1 hour
```

---

#### RULE-007: CooldownAfterLoss (Revenge Trading Prevention)

**Status**: ❌ **Not Started**

**Purpose**: Force break after losing trades to prevent emotional revenge trading

**Trigger**: `GatewayUserTrade` event (when `profitAndLoss < 0`)

**Enforcement**:
- **Type**: Timer/Cooldown (Category 2)
- **Action**: Set cooldown timer based on loss amount (NO position close)
- **Lockout**: Tiered cooldown based on loss severity
- **Can Trade Again**: When cooldown timer expires

**Complexity**: Simple

**Estimated Effort**: 1-2 days

**Dependencies**:
1. **MOD-003 (TimerManager)** - Missing, required for countdown timers
2. **PnLTracker** - Already exists ✅, provides trade P&L

**Priority**: Medium (psychological protection)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 861-946

**Tiered Cooldown Logic**:
```python
trade_pnl = trade_event['profitAndLoss']

if trade_pnl < 0:  # Losing trade
    for threshold in config['loss_thresholds']:
        if trade_pnl <= threshold['loss_amount']:
            set_cooldown(duration=threshold['cooldown_duration'])
            break
```

**Example Thresholds**:
- Loss $100-199 → 5 min cooldown (300s)
- Loss $200-299 → 15 min cooldown (900s)
- Loss $300+ → 30 min cooldown (1800s)

**Implementation Notes**:
- Evaluate each losing trade individually
- Match first threshold (largest loss if sorted)
- No position close (trade already happened)

**Example Configuration**:
```yaml
cooldown_after_loss:
  enabled: true
  loss_thresholds:
    - loss_amount: -100.0
      cooldown_duration: 300  # 5 min
    - loss_amount: -200.0
      cooldown_duration: 900  # 15 min
    - loss_amount: -300.0
      cooldown_duration: 1800  # 30 min
```

---

#### RULE-008: NoStopLossGrace (Stop-Loss Discipline)

**Status**: ❌ **Not Started**

**Purpose**: Enforce stop-loss placement - close position if no SL placed within grace period

**Trigger**: `GatewayUserOrder` event (when position opens)

**Enforcement**:
- **Type**: Trade-by-Trade (Category 1)
- **Action**: Close position if no stop-loss placed within grace period
- **Lockout**: None
- **Can Trade Again**: Immediately

**Complexity**: Medium

**Estimated Effort**: 2 days

**Dependencies**:
1. **MOD-003 (TimerManager)** - Missing, required for grace period timer
2. **Order Query** - Check if stop-loss order exists for position
3. **Stop-Loss Detection** - Identify order type (type == 4)

**Priority**: Medium (trading discipline)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 948-1042

**Grace Period Logic**:
```python
def on_position_open(position_event):
    # Start grace period timer
    timer_manager.start_timer(
        name=f"sl_grace_{position_event['id']}",
        duration=config['grace_period_seconds'],  # e.g., 10 seconds
        callback=lambda: check_stop_loss(position_event)
    )

def check_stop_loss(position_event):
    # Query open orders
    orders = get_open_orders(account_id)

    # Check if SL order exists for this position
    has_stop_loss = any(
        o['type'] == 4 and o['contractId'] == position_event['contractId']
        for o in orders
    )

    if not has_stop_loss:
        # BREACH - close position
        close_position(position_event['contractId'])
```

**Implementation Notes**:
- Timer starts when position opens
- Query orders at timer expiry
- Match stop-loss to same contract ID
- No lockout (can trade again immediately)

**Example Configuration**:
```yaml
no_stop_loss_grace:
  enabled: true
  grace_period_seconds: 10  # 10 seconds to place SL
  enforcement: "close_position"
```

---

#### RULE-009: SessionBlockOutside (Trading Hours Enforcement)

**Status**: ❌ **Not Started**

**Purpose**: Block trading outside configured session hours and on holidays

**Trigger**: Multiple triggers
1. `GatewayUserPosition` event (position opens outside session)
2. Background timer (session end time reached)
3. Holiday detection

**Enforcement**:
- **Type**: Hard Lockout (Category 3)
- **Action**: Close positions + Cancel orders + Lock until session starts
- **Lockout**: Until next session start or admin override
- **Can Trade Again**: At session start time

**Complexity**: Complex (timezone handling, holiday calendar, multiple triggers)

**Estimated Effort**: 3-4 days

**Dependencies**:
1. **MOD-002 (LockoutManager)** - Missing, required for lockout
2. **MOD-004 (ResetScheduler)** - Missing, required for session timers
3. **Holiday Calendar** - List of trading holidays
4. **Timezone Library** - pytz or zoneinfo for timezone conversion
5. **Background Timer** - Check session end every minute

**Priority**: High (account compliance, no trading outside hours)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 1044-1278

**Session Configuration**:

Global Session (applies to all instruments):
```yaml
global_session:
  enabled: true
  start: "09:30"
  end: "16:00"
  timezone: "America/New_York"
```

Per-Instrument Override:
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

**Holiday Calendar**:
```yaml
# config/holidays.yaml
holidays:
  - "2025-01-01"  # New Year's Day
  - "2025-07-04"  # Independence Day
  - "2025-12-25"  # Christmas
```

**Implementation Notes**:
- Must handle timezone conversion correctly
- ES has overnight sessions (Sunday 6pm - Friday 5pm)
- Holiday calendar blocks all trading
- Background timer checks session status every minute
- Auto-close positions at session end (configurable)

**Example Configuration**:
```yaml
session_block_outside:
  enabled: true
  global_session:
    enabled: true
    start: "09:30"
    end: "16:00"
    timezone: "America/New_York"
  close_positions_at_session_end: true
  lockout_outside_session: true
  respect_holidays: true
  holiday_calendar: "config/holidays.yaml"
```

---

#### RULE-010: AuthLossGuard (Account Restriction Monitor)

**Status**: ❌ **Not Started**

**Purpose**: Monitor TopstepX `canTrade` status and lockout when API signals account is restricted

**Trigger**: `GatewayUserAccount` event (when `canTrade` field changes)

**Enforcement**:
- **Type**: Hard Lockout (Category 3)
- **Action**: Close all positions + Hard lockout (no expiry)
- **Lockout**: Until TopstepX sends `canTrade: true` or admin override
- **Can Trade Again**: When API clears restriction or admin unlock

**Complexity**: Simple (API-driven)

**Estimated Effort**: 1 day

**Dependencies**:
1. **MOD-002 (LockoutManager)** - Missing, required for lockout
2. **SDK Account Events** - Already exists ✅ (`GatewayUserAccount`)

**Priority**: Medium (account compliance)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 1280-1379

**Trigger Logic**:
```python
def check(account_event):
    can_trade = account_event['canTrade']

    if not can_trade:
        # TopstepX says account cannot trade
        close_all_positions()
        set_lockout(
            reason="Account restricted by TopstepX",
            until=None  # No expiry, manual unlock only
        )
```

**API Event Payload**:
```json
{
  "id": 123,
  "balance": 10000.0,
  "canTrade": false  // ← This triggers breach
}
```

**Auto-Unlock**:
- When `canTrade: true` event received, lockout clears automatically

**Implementation Notes**:
- API-driven enforcement (TopstepX controls state)
- No time-based reset
- Must handle both `canTrade: false` → lockout and `canTrade: true` → unlock

**Example Configuration**:
```yaml
auth_loss_guard:
  enabled: true
  enforcement: "close_all_and_lockout"
  # No other config needed - API-driven
```

---

#### RULE-011: SymbolBlocks (Symbol Blacklist)

**Status**: ❌ **Not Started**

**Purpose**: Blacklist specific symbols - close any position immediately and permanently lock that symbol

**Trigger**: `GatewayUserPosition` event (when position opens in blocked symbol)

**Enforcement**:
- **Type**: Trade-by-Trade (Category 1) with symbol-specific permanent lockout
- **Action**: Close position + Permanent symbol lockout
- **Lockout**: Symbol-specific permanent lockout (not account-wide)
- **Can Trade Again**: In other symbols immediately, blocked symbol never (unless removed from blacklist)

**Complexity**: Simple

**Estimated Effort**: 1 day

**Dependencies**:
1. **MOD-002 (LockoutManager)** - Missing, requires extension for symbol-specific lockouts
2. **Symbol Extraction** - Extract symbol from contract ID (already exists ✅)

**Priority**: Low (user preference, not account violation)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 1381-1482

**Trigger Logic**:
```python
def check(position_event):
    symbol = extract_symbol(position_event['contractId'])

    if symbol in config['blocked_symbols']:
        # Close position immediately
        close_position(position_event['contractId'])

        # Set permanent symbol-specific lockout
        set_lockout(
            account_id=account_id,
            symbol=symbol,
            reason=f"Symbol {symbol} is blacklisted",
            until=datetime.max  # Permanent
        )
```

**Symbol-Specific Lockout**:
- Not account-wide (can trade other symbols)
- Permanent (no expiry time)
- Requires admin to remove symbol from blacklist

**Use Case**: "I always lose on RTY, never let me trade it"

**Implementation Notes**:
- Requires MOD-002 extension for symbol-specific lockouts
- Any future fills in blocked symbol → instant close

**Example Configuration**:
```yaml
symbol_blocks:
  enabled: true
  blocked_symbols:
    - "RTY"
    - "BTC"
  enforcement: "close_and_lockout_symbol"
```

---

#### RULE-012: TradeManagement (Automated Stop Management)

**Status**: ❌ **Not Started**

**Purpose**: Automated trade management - auto breakeven stop, trailing stops

**Trigger**: `GatewayUserPosition` event + market price updates

**Enforcement**:
- **Type**: Automation (Category 4) - NOT enforcement, just automation
- **Action**: Modify stop-loss orders (NOT closing positions, NOT lockout)
- **Lockout**: None
- **Can Trade Again**: N/A (doesn't restrict trading)

**Complexity**: Medium (requires order modification API)

**Estimated Effort**: 2-3 days

**Dependencies**:
1. **Market Data Feed** - Real-time price updates
2. **Order Modification API** - Modify existing stop-loss order
3. **Tick Calculation** - Calculate ticks from entry price

**Priority**: Low (automation feature, not risk enforcement)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 1484-1596

**Auto Breakeven Logic**:
```python
unrealized_profit_ticks = calculate_ticks(position, current_price)

if unrealized_profit_ticks >= config['auto_breakeven']['profit_trigger_ticks']:
    # Move stop-loss to entry price (breakeven)
    modify_stop_order(
        order_id=stop_loss_order_id,
        new_stop_price=entry_price
    )
```

**Trailing Stop Logic**:
```python
if unrealized_profit_ticks >= config['trailing_stop']['activation_ticks']:
    # Update trailing stop N ticks behind highest price
    new_stop_price = highest_price - (trail_distance_ticks * tick_size)

    modify_stop_order(
        order_id=stop_loss_order_id,
        new_stop_price=new_stop_price
    )
```

**Implementation Notes**:
- Requires stop-loss order to already exist
- Must track highest price reached per position
- Different tick sizes per instrument
- Not a risk rule, just automation

**Example Configuration**:
```yaml
trade_management:
  enabled: true
  auto_breakeven:
    enabled: true
    profit_trigger_ticks: 10  # Move SL to BE after +10 ticks
  trailing_stop:
    enabled: true
    activation_ticks: 20  # Start trailing after +20 ticks
    trail_distance_ticks: 10  # Trail 10 ticks behind high
  tick_sizes:
    MNQ: 0.25
    ES: 0.25
    NQ: 0.25
```

---

#### RULE-013: DailyRealizedProfit (Profit Target Lockout)

**Status**: ❌ **Not Started**

**Purpose**: Take profit and stop trading once daily target hit (prevent giving back profits)

**Trigger**: `GatewayUserTrade` event (cumulative daily realized profit)

**Enforcement**:
- **Type**: Hard Lockout (Category 3)
- **Action**: Close all positions + Cancel orders + Lock until reset time
- **Lockout**: Until 5:00 PM (configurable reset_time) or admin override
- **Can Trade Again**: At reset time or admin unlock

**Complexity**: Simple (similar to RULE-003)

**Estimated Effort**: 1 day

**Dependencies**:
1. **PnLTracker** - Already exists ✅ (same as RULE-003)
2. **MOD-002 (LockoutManager)** - Missing, required for lockout
3. **MOD-004 (ResetScheduler)** - Missing, required for daily reset

**Priority**: Medium (profit protection, not account violation)

**Specification**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` lines 1598-1731

**Trigger Logic**:
```python
daily_realized_pnl = pnl_tracker.get_daily_realized_pnl(account_id)

if daily_realized_pnl >= config['target']:
    # Hit profit target
    close_all_positions()
    cancel_all_orders()
    set_lockout(until=reset_time, reason="Daily profit target reached")
```

**Why Hard Lockout?**
- Prevents giving back profits through overtrading
- Forces trader to stop on winning day
- Psychological discipline: "Take the win and walk away"

**Implementation Notes**:
- Reuses PnLTracker infrastructure (same SQLite table as RULE-003)
- Opposite of RULE-003 (profit target vs loss limit)
- Same daily reset logic

**Example Configuration**:
```yaml
daily_realized_profit:
  enabled: true
  target: 1000.0  # Daily profit target
  reset_time: "17:00"
  timezone: "America/New_York"
  enforcement: "close_all_and_lockout"
  lockout_until_reset: true
```

**Note**: RULE-013 mentioned in categories doc but lacks dedicated specification file. Should create full spec matching RULE-003 detail level.

---

## Critical Dependencies Analysis

### Missing State Management Modules (3 Critical Blockers)

These modules block **7 of 10 missing rules**:

---

#### MOD-002: LockoutManager (Blocks 5 Rules)

**Status**: ❌ **Not Implemented**

**Blocks Rules**:
- RULE-003: DailyRealizedLoss (partial implementation)
- RULE-009: SessionBlockOutside
- RULE-010: AuthLossGuard
- RULE-011: SymbolBlocks (requires symbol-specific lockout)
- RULE-013: DailyRealizedProfit

**Purpose**: Manage account and symbol-specific lockouts with expiry times

**Required Capabilities**:
- Set/clear lockouts with optional expiry time
- Check lockout status (account-wide or symbol-specific)
- Auto-clear expired lockouts (background task)
- SQLite persistence (survive restarts)
- Support both account-wide and symbol-specific lockouts

**SQLite Schema**:
```sql
CREATE TABLE lockouts (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    symbol TEXT,  -- NULL for account-wide, symbol for symbol-specific
    reason TEXT NOT NULL,
    locked_at DATETIME NOT NULL,
    expires_at DATETIME,  -- NULL for permanent/manual unlock
    UNIQUE(account_id, symbol)
);
```

**API Requirements**:
```python
class LockoutManager:
    async def set_lockout(
        self,
        account_id: int,
        reason: str,
        until: datetime | None = None,
        symbol: str | None = None
    ) -> None:
        """Set lockout with optional expiry and symbol scope."""

    async def is_locked_out(
        self,
        account_id: int,
        symbol: str | None = None
    ) -> bool:
        """Check if account/symbol is locked out."""

    async def clear_lockout(
        self,
        account_id: int,
        symbol: str | None = None
    ) -> None:
        """Manually clear lockout."""

    async def get_lockout_info(
        self,
        account_id: int,
        symbol: str | None = None
    ) -> dict | None:
        """Get lockout details (reason, expiry, time remaining)."""

    async def check_expired_lockouts(self) -> None:
        """Background task: Auto-clear expired lockouts."""
```

**Estimated Effort**: 2 days

**Priority**: Critical (blocks 5 rules)

---

#### MOD-003: TimerManager (Blocks 3 Rules)

**Status**: ❌ **Not Implemented**

**Blocks Rules**:
- RULE-006: TradeFrequencyLimit
- RULE-007: CooldownAfterLoss
- RULE-008: NoStopLossGrace

**Purpose**: Manage countdown timers with callbacks and expiry handling

**Required Capabilities**:
- Start/cancel timers with configurable duration
- Get remaining time for display (CLI countdown)
- Execute callback when timer expires
- Background task to check timer expiry
- SQLite persistence (survive restarts)

**SQLite Schema**:
```sql
CREATE TABLE timers (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    reason TEXT,
    started_at DATETIME NOT NULL,
    duration_seconds INTEGER NOT NULL,
    expires_at DATETIME NOT NULL,
    callback TEXT,  -- Callback function identifier
    UNIQUE(account_id, name)
);
```

**API Requirements**:
```python
class TimerManager:
    async def start_timer(
        self,
        account_id: int,
        name: str,
        duration_seconds: int,
        reason: str = "",
        callback: Callable | None = None
    ) -> None:
        """Start countdown timer with optional callback."""

    async def get_remaining_time(
        self,
        account_id: int,
        name: str
    ) -> int | None:
        """Get remaining seconds (for CLI display)."""

    async def cancel_timer(
        self,
        account_id: int,
        name: str
    ) -> None:
        """Cancel active timer."""

    async def check_expired_timers(self) -> None:
        """Background task: Check for expired timers, execute callbacks."""
```

**Estimated Effort**: 2 days

**Priority**: Critical (blocks 3 rules)

---

#### MOD-004: ResetScheduler (Blocks 3 Rules)

**Status**: ❌ **Not Implemented**

**Blocks Rules**:
- RULE-003: DailyRealizedLoss (partial implementation)
- RULE-009: SessionBlockOutside
- RULE-013: DailyRealizedProfit

**Purpose**: Schedule and execute daily resets at configured time (e.g., 5:00 PM)

**Required Capabilities**:
- Schedule daily reset at specific time (timezone-aware)
- Reset all daily counters (P&L, trades)
- Clear time-based lockouts
- Holiday calendar integration
- Background task (check every minute)

**Reset Actions**:
1. Reset daily P&L counters to 0 (PnLTracker)
2. Reset trade counts (TradeCounter)
3. Clear time-based lockouts (LockoutManager)
4. Check session status (SessionBlockOutside)

**API Requirements**:
```python
class ResetScheduler:
    async def schedule_daily_reset(
        self,
        account_id: int,
        reset_time: str,  # "17:00"
        timezone: str  # "America/New_York"
    ) -> None:
        """Schedule daily reset at specified time."""

    async def reset_daily_counters(self, account_id: int) -> None:
        """Reset all daily state (P&L, trades, lockouts)."""

    async def is_holiday(self, date: datetime.date) -> bool:
        """Check if date is trading holiday."""

    async def check_reset_time(self) -> None:
        """Background task: Check if reset time reached."""
```

**Holiday Calendar**:
```yaml
# config/holidays.yaml
holidays:
  - "2025-01-01"
  - "2025-07-04"
  - "2025-12-25"
```

**Estimated Effort**: 2 days

**Priority**: Critical (blocks 3 rules, including RULE-003 completion)

---

### Market Data Feed (Blocks 3 Rules)

**Status**: ❌ **Not Implemented**

**Blocks Rules**:
- RULE-004: DailyUnrealizedLoss
- RULE-005: MaxUnrealizedProfit
- RULE-012: TradeManagement

**Purpose**: Real-time market price updates for unrealized P&L calculation

**Required Capabilities**:
- Real-time price feed (WebSocket or polling)
- Per-instrument price updates
- High-frequency event processing
- Tick value mapping

**Implementation Options**:
1. **SDK Market Data** (if available)
2. **TopstepX Market Data API**
3. **Polling API** (fallback, less efficient)

**Tick Value Map**:
```python
TICK_VALUES = {
    "MNQ": 5.0,   # $5 per tick
    "ES": 50.0,   # $50 per tick
    "NQ": 20.0,   # $20 per tick
    "RTY": 5.0,   # $5 per tick
}
```

**Unrealized P&L Calculator**:
```python
def calculate_unrealized_pnl(position, current_price, tick_value):
    """Calculate unrealized P&L for position."""
    entry_price = position['avg_entry_price']
    size = position['size']

    # Long: profit when price rises
    # Short: profit when price falls
    price_diff = current_price - entry_price
    pnl = price_diff * size * tick_value

    return pnl
```

**Estimated Effort**: 3-4 days (research + implementation)

**Priority**: Medium (blocks 3 rules, but not critical for account compliance)

---

## Recommended Implementation Order

### Phase 1: Critical State Managers (1 week)

**Goal**: Unblock most rules by implementing missing state managers

1. **MOD-002: LockoutManager** (2 days)
   - Unblocks: RULE-003, 009, 010, 011, 013 (5 rules)
   - Implementation: SQLite + account/symbol-specific lockouts

2. **MOD-003: TimerManager** (2 days)
   - Unblocks: RULE-006, 007, 008 (3 rules)
   - Implementation: SQLite + countdown timers + callbacks

3. **MOD-004: ResetScheduler** (2 days)
   - Unblocks: RULE-003, 009, 013 (3 rules, completes RULE-003)
   - Implementation: Daily reset + holiday calendar + timezone handling

**After Phase 1**:
- ✅ All critical blockers removed
- ✅ RULE-003 can be completed
- ✅ 8 more rules can be implemented

---

### Phase 2: High-Priority Rules (1 week)

**Goal**: Implement rules that prevent account violations

4. **Complete RULE-003: DailyRealizedLoss** (1 day)
   - Wire to LockoutManager and ResetScheduler
   - Add comprehensive tests

5. **RULE-009: SessionBlockOutside** (3 days)
   - Most complex rule (timezones, holidays, multiple triggers)
   - Critical for account compliance

6. **RULE-006: TradeFrequencyLimit** (2 days)
   - Prevent overtrading
   - High psychological value

**After Phase 2**:
- ✅ All critical account violation rules done
- ✅ 6 of 13 rules complete (46%)

---

### Phase 3: Medium-Priority Rules (1 week)

**Goal**: Complete timer-based and profit protection rules

7. **RULE-007: CooldownAfterLoss** (1 day)
   - Simple timer-based rule

8. **RULE-008: NoStopLossGrace** (2 days)
   - Enforce stop-loss discipline

9. **RULE-010: AuthLossGuard** (1 day)
   - API-driven enforcement

10. **RULE-013: DailyRealizedProfit** (1 day)
    - Similar to RULE-003

11. **RULE-011: SymbolBlocks** (1 day)
    - Symbol-specific lockout

**After Phase 3**:
- ✅ 11 of 13 rules complete (85%)

---

### Phase 4: Optional Features (1 week)

**Goal**: Implement market-data-dependent rules (optional)

12. **Market Data Feed** (3 days)
    - Research SDK market data capabilities
    - Implement real-time price updates

13. **RULE-004: DailyUnrealizedLoss** (2 days)
    - Requires market data feed

14. **RULE-005: MaxUnrealizedProfit** (2 days)
    - Requires market data feed

15. **RULE-012: TradeManagement** (2 days)
    - Automation feature (low priority)

**After Phase 4**:
- ✅ All 13 rules complete (100%)

---

## Risk Assessment

### What Functionality is Missing That Could Cause Account Violations?

#### Critical Gaps (Account Termination Risk)

1. **RULE-003 (Incomplete)**: Daily Realized Loss Limit
   - **Risk**: Hit TopstepX daily loss limit, account terminated
   - **Status**: 70% done, needs state manager wiring
   - **Blocker**: MOD-002, MOD-004

2. **RULE-009 (Missing)**: Session Block Outside Hours
   - **Risk**: Trading outside allowed hours, account violation
   - **Status**: Not started
   - **Blocker**: MOD-002, MOD-004, Holiday Calendar

3. **RULE-006 (Missing)**: Trade Frequency Limit
   - **Risk**: Overtrading, hit maximum trade count
   - **Status**: Not started
   - **Blocker**: MOD-003

#### Important Gaps (Risk Management)

4. **RULE-004 (Missing)**: Daily Unrealized Loss
   - **Risk**: Large floating losses, potential account violation
   - **Status**: Not started
   - **Blocker**: Market Data Feed

5. **RULE-013 (Missing)**: Daily Realized Profit Target
   - **Risk**: Give back profits through overtrading
   - **Status**: Not started
   - **Blocker**: MOD-002, MOD-004

#### Medium Gaps (Discipline & Psychology)

6. **RULE-007 (Missing)**: Cooldown After Loss
   - **Risk**: Revenge trading after losses
   - **Status**: Not started
   - **Blocker**: MOD-003

7. **RULE-008 (Missing)**: No Stop-Loss Grace
   - **Risk**: Unprotected positions
   - **Status**: Not started
   - **Blocker**: MOD-003

8. **RULE-010 (Missing)**: Auth Loss Guard
   - **Risk**: Trading when TopstepX says "can't trade"
   - **Status**: Not started
   - **Blocker**: MOD-002

---

## Specification Quality Assessment

### Excellent Specifications (Ready for Implementation)

✅ **12 of 13 rules have comprehensive specifications**

**Location**: `docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md`

**Quality Indicators**:
- Version controlled (v2.0)
- Dated (2025-01-17, with 2025-10-23 updates)
- Complete technical details
- Code examples
- Test scenarios
- API requirements
- SQLite schemas
- Edge case documentation

**Strongest Specifications**:
1. **RULE-001**: MaxContracts (225 lines)
2. **RULE-003**: DailyRealizedLoss (228 lines)
3. **RULE-009**: SessionBlockOutside (309 lines)

**Brief Specifications** (need expansion):
1. **RULE-004**: DailyUnrealizedLoss (40 lines)
2. **RULE-005**: MaxUnrealizedProfit (38 lines)
3. **RULE-010**: AuthLossGuard (49 lines)
4. **RULE-011**: SymbolBlocks (44 lines)

### Specification Conflicts

#### Conflict 1: RULE-004 Enforcement Type

**Primary Spec** (2025-01-17): Hard Lockout, close all positions
**Updated Categories** (2025-10-23): Trade-by-Trade, close losing position only

**Resolution**: Use updated categories doc (more recent, explicit correction)
**Action Required**: Update primary spec to match

#### Conflict 2: RULE-005 Enforcement Type

**Primary Spec**: Hard Lockout, close all positions
**Updated Categories**: Trade-by-Trade, close winning position only

**Resolution**: Make configurable (both approaches valid)
**Action Required**: Update spec to include both modes

### Missing Specification

#### RULE-013: DailyRealizedProfit

**Status**: Mentioned in categories doc, no dedicated spec file

**Action Required**: Create full specification file matching RULE-003 detail level

**Template**: Use RULE-003 as template (similar logic, opposite direction)

---

## Effort Estimation Summary

### Total Implementation Effort

| Phase | Deliverable | Effort | Rules Unblocked |
|-------|-------------|--------|-----------------|
| **Phase 1** | State Managers (MOD-002, 003, 004) | 1 week | Unblocks 8 rules |
| **Phase 2** | High-Priority Rules (3, 6, 9) | 1 week | +3 rules (49% total) |
| **Phase 3** | Medium-Priority Rules (7, 8, 10, 11, 13) | 1 week | +5 rules (85% total) |
| **Phase 4** | Market Data + Optional Rules (4, 5, 12) | 1 week | +3 rules (100% total) |
| **Total** | All 13 rules + state managers | **3-4 weeks** | 100% complete |

### Per-Rule Effort Breakdown

| Rule | Complexity | Estimated Effort | Blockers |
|------|-----------|------------------|----------|
| RULE-003 (complete) | Simple | 1 day | MOD-002 ❌, MOD-004 ❌ |
| RULE-004 | Medium | 2 days | Market Data ❌ |
| RULE-005 | Medium | 2 days | Market Data ❌ |
| RULE-006 | Medium | 2-3 days | MOD-003 ❌ |
| RULE-007 | Simple | 1-2 days | MOD-003 ❌ |
| RULE-008 | Medium | 2 days | MOD-003 ❌ |
| RULE-009 | Complex | 3-4 days | MOD-002 ❌, MOD-004 ❌ |
| RULE-010 | Simple | 1 day | MOD-002 ❌ |
| RULE-011 | Simple | 1 day | MOD-002 ❌ |
| RULE-012 | Medium | 2-3 days | Market Data ❌ |
| RULE-013 | Simple | 1 day | MOD-002 ❌, MOD-004 ❌ |
| **Total Rules** | - | **18-23 days** | - |
| **State Managers** | - | **6 days** | - |
| **Market Data** | - | **3-4 days** | - |
| **Grand Total** | - | **27-33 days** | **3-4 weeks** |

---

## Next Steps

### Immediate Actions (This Week)

1. **Implement MOD-002: LockoutManager** (2 days)
   - Design SQLite schema
   - Write TDD tests first
   - Implement account-wide and symbol-specific lockouts
   - Background task for expired lockout checking

2. **Implement MOD-003: TimerManager** (2 days)
   - Design SQLite schema
   - Write TDD tests first
   - Implement countdown timers with callbacks
   - Background task for timer expiry

3. **Implement MOD-004: ResetScheduler** (2 days)
   - Design daily reset logic
   - Write TDD tests first
   - Implement timezone-aware scheduling
   - Holiday calendar integration

### Short Term (Next 2 Weeks)

4. **Complete RULE-003: DailyRealizedLoss** (1 day)
   - Wire to LockoutManager
   - Wire to ResetScheduler
   - Add comprehensive tests

5. **Implement RULE-009: SessionBlockOutside** (3 days)
   - Most complex rule
   - Multiple triggers (events, timers, holidays)
   - Timezone handling

6. **Implement RULE-006: TradeFrequencyLimit** (2 days)
   - Rolling time windows
   - Trade counting
   - Cooldown enforcement

7. **Implement RULE-010: AuthLossGuard** (1 day)
   - API-driven enforcement
   - Simple implementation

### Medium Term (Weeks 3-4)

8. **Implement Remaining Timer-Based Rules** (4 days)
   - RULE-007: CooldownAfterLoss
   - RULE-008: NoStopLossGrace

9. **Implement Profit Protection Rules** (2 days)
   - RULE-013: DailyRealizedProfit
   - RULE-011: SymbolBlocks

10. **Research Market Data Feed** (2 days)
    - Investigate SDK market data capabilities
    - Design real-time price update system

### Optional (Week 5+)

11. **Implement Market-Data-Dependent Rules** (6 days)
    - Market Data Feed infrastructure
    - RULE-004: DailyUnrealizedLoss
    - RULE-005: MaxUnrealizedProfit
    - RULE-012: TradeManagement

---

## Success Criteria

### Phase 1 Complete (State Managers)
- ✅ MOD-002, MOD-003, MOD-004 implemented
- ✅ All tests passing (>80% coverage)
- ✅ SQLite schemas validated
- ✅ Background tasks working
- ✅ 8 rules unblocked

### Phase 2 Complete (Critical Rules)
- ✅ RULE-003 completed and tested
- ✅ RULE-009 implemented (session enforcement)
- ✅ RULE-006 implemented (frequency limit)
- ✅ All account violation scenarios covered
- ✅ 6 of 13 rules complete (49%)

### Phase 3 Complete (Medium Priority)
- ✅ All timer-based rules implemented
- ✅ Profit protection rules implemented
- ✅ 11 of 13 rules complete (85%)
- ✅ All critical risks mitigated

### Phase 4 Complete (Optional)
- ✅ Market data feed working
- ✅ All 13 rules complete (100%)
- ✅ Full rule coverage
- ✅ Production ready

---

## Conclusion

The Risk Manager V34 project has a **77% rule implementation gap** (10 of 13 rules missing), but the path forward is clear:

### Strengths
- ✅ **Excellent foundation**: Core architecture and SDK integration complete
- ✅ **Comprehensive specs**: All 13 rules fully specified
- ✅ **No architectural blockers**: Clear implementation path
- ✅ **Strong testing infrastructure**: TDD-ready

### Critical Gaps
- ❌ **3 state managers missing**: Blocking 8 rules
- ❌ **10 rules not started**: 77% gap
- ❌ **Market data feed**: Blocks 3 optional rules

### Recommendation

**Focus on Phase 1 (State Managers) first**. This unblocks 8 rules and enables rapid progress in Phases 2-3.

**Time to 85% Complete**: 3 weeks (Phases 1-3)
**Time to 100% Complete**: 4 weeks (Phases 1-4)

The project is **well-positioned for success** with clear priorities and no architectural roadblocks.

---

**Report Complete**

**Analysis Date**: 2025-10-25
**Next Review**: After Phase 1 completion (state managers)
**Maintainer**: Update after each phase milestone
