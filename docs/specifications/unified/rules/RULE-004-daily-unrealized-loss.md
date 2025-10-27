# RULE-004: Daily Unrealized Loss

**Category**: Trade-by-Trade (Category 1)
**Priority**: High
**Status**: Not Implemented

---

## Unified Specification (v3.0)

### Purpose
Enforce unrealized (floating) loss limit on individual positions to prevent excessive drawdown. This rule monitors real-time unrealized P&L and closes specific losing positions before they impact the daily realized loss limit.

**Key Insight** (per user guidance): When unrealized positions close (hitting their limit), they become realized P&L. We need quote data for unrealized tracking (Project-X-Py provides this).

### Trigger Condition
**Event Types**: `EventType.POSITION_OPENED`, `EventType.POSITION_UPDATED`, `EventType.POSITION_CLOSED` + real-time market price updates

**Trigger Logic**:
```python
def check(position_event, current_market_price):
    # Calculate unrealized P&L for THIS POSITION
    unrealized_pnl = calculate_unrealized_pnl(
        entry_price=position_event['avgPrice'],
        current_price=current_market_price,
        position_size=position_event['size'],
        position_type=position_event['type'],  # 1=Long, 2=Short
        tick_value=TICK_VALUES[symbol]
    )

    if unrealized_pnl <= config['limit']:
        return BREACH, position_event
```

**Calculation Example** (MNQ, tick value = $5):
```python
# Long position
entry_price = 21000.00
current_price = 20990.00  # Down 10 ticks
size = 2 contracts
tick_value = 5.0

unrealized_pnl = (20990.00 - 21000.00) / 0.25 * size * tick_value
               = (-10.00 / 0.25) * 2 * 5.0
               = -40 ticks * 2 * $5
               = -$400

if -$400 <= -$300:  # Limit = -$300
    BREACH
```

### Enforcement Action

**Type**: TRADE-BY-TRADE (User Guidance Applied - Resolution Rule #1)

**Action Sequence** (per user guidance):
1. **Close ONLY the specific position that breached the limit**
2. **Do NOT close other positions**
3. **Do NOT create lockout**
4. **Trader can continue trading immediately**
5. **Monitor if combined (unrealized + realized) hits realized limit** (would trigger RULE-003)

**Implementation Code**:
```python
async def enforce(self, position, unrealized_pnl, engine):
    # Close ONLY this specific position (trade-by-trade)
    await engine.enforcement.close_position(
        account_id=position['accountId'],
        contract_id=position['contractId'],
        reason=f"Unrealized loss limit: ${unrealized_pnl:.2f} / ${self.config['limit']:.2f}"
    )

    # NO lockout
    # NO cancel other orders
    # Trader can immediately place next trade

    self.logger.warning(
        f"RULE-004 BREACH: Closed {position['contractId']} position. "
        f"Unrealized P&L: ${unrealized_pnl:.2f}, Limit: ${self.config['limit']:.2f}"
    )

    # Note: When this position closes, it becomes realized P&L
    # May trigger RULE-003 if daily realized loss limit is hit
```

**Critical Interaction** (per user guidance):
- When unrealized position closes → becomes realized P&L
- If `unrealized + realized = combined` hits realized limit → triggers RULE-003 (hard lockout)
- This rule acts as an "early warning" before hitting the hard lockout

### Configuration Parameters
```yaml
daily_unrealized_loss:
  enabled: true
  limit: -300.0  # Max unrealized loss per position (e.g., -$300)

  # Enforcement mode (per user guidance - trade-by-trade)
  enforcement: "close_position"  # Close that position only (NOT close_all)

  # Tick values required for unrealized P&L calculation
  tick_values:
    MNQ: 5.0   # $5 per tick
    ES: 50.0   # $50 per tick
    NQ: 20.0   # $20 per tick
    RTY: 5.0   # $5 per tick

  # Tick sizes for calculation
  tick_sizes:
    MNQ: 0.25
    ES: 0.25
    NQ: 0.25
    RTY: 0.10
```

### State Requirements
- **PnL Tracker**: No (real-time calculation, no persistence needed)
- **Lockout Manager**: No (no lockout created)
- **Timer Manager**: No (no timer needed)
- **Reset Scheduler**: No (no daily reset needed)
- **Market Data Feed**: Yes (real-time price updates required)

### SDK Integration
**Events needed**:
- `EventType.POSITION_UPDATED` - Position updates
- **Market Data Updates** - Real-time price feed (critical dependency)

**Methods needed**:
- `close_position(account_id, contract_id)` - Close specific position

**Quote data needed**: Yes (real-time market prices for unrealized P&L calculation)

**SDK Market Data** (from Project-X-Py):
```python
# Subscribe to market data
await trading_suite.subscribe_market_data(contract_id)

# Receive price updates
async def on_market_data_update(price_event):
    current_price = price_event['last']
    # Calculate unrealized P&L
    # Check RULE-004 breach
```

### Database Schema
No database schema required (real-time calculation only, no state persistence).

### Examples

**Scenario 1: Position Within Limit**
- Account state: MNQ Long 2 @ 21000.00
- Current price: 20995.00 (down 5 ticks)
- Unrealized P&L: -5 ticks * 2 * $5 = -$50
- **Trigger**: No breach (within -$300 limit)
- **Enforcement**: None
- **Result**: Position remains open

**Scenario 2: Single Position Breaches Limit (Trade-by-Trade)**
- Account state:
  - MNQ Long 2 @ 21000.00
  - ES Long 1 @ 6000.00
- Current MNQ price: 20970.00 (down 30 ticks)
- MNQ Unrealized P&L: -30 ticks * 2 * $5 = -$300
- **Trigger**: MNQ position breach (-$300 <= -$300)
- **Enforcement** (per user guidance):
  1. Close ONLY MNQ position (2 contracts)
  2. Leave ES position open
  3. No lockout
- **Result**:
  - MNQ: 0 contracts (closed)
  - ES: 1 contract (still open)
  - Trader can trade immediately

**Scenario 3: Unrealized → Realized Interaction**
- Account state: Daily realized P&L = -$400 (close to RULE-003 limit of -$500)
- MNQ Long 2 @ 21000.00
- Current MNQ price: 20970.00 (down 30 ticks)
- MNQ Unrealized P&L: -$300
- **Trigger**: RULE-004 breach (unrealized loss too high)
- **Enforcement**:
  1. Close MNQ position (RULE-004)
  2. Position close → -$300 realized loss
  3. New daily realized P&L: -$400 + (-$300) = -$700
  4. RULE-003 triggers (-$700 <= -$500)
  5. Hard lockout until reset time
- **Result**: Account locked (cascading enforcement)

**Scenario 4: Multiple Positions, Different Symbols**
- Account state:
  - MNQ Long 2 @ 21000.00 (unrealized: -$320)
  - ES Long 1 @ 6000.00 (unrealized: +$100)
- **Trigger**: Only MNQ breaches RULE-004
- **Enforcement**: Close ONLY MNQ, keep ES open
- **Result**: ES position with +$100 unrealized profit remains open

---

## Conflict Resolutions

### Conflict 1: Enforcement Type (MAJOR)
- **Source A** (Original spec 04_daily_unrealized_loss.md, lines 6, 19, 33-35): "enforcement_type: Hard Lockout (Until Reset)", "close_all_and_lockout"
- **Source B** (RULE_CATEGORIES.md updated 2025-10-23, lines 42-66): "Category 1: Trade-by-Trade", "Close that losing position only", "NO lockout"
- **Source C** (User Guidance - Resolution Rule #1): "UNREALIZED PnL Rules (RULE-004, RULE-005): Trade-by-trade enforcement, Close ONLY the specific position that breached the limit, Trader can continue trading immediately, No lockout, no timer"
- **Resolution**: Use User Guidance (Resolution Rule #1 - HIGHEST AUTHORITY) → Trade-by-Trade
- **Rationale**: User's authoritative architectural guidance explicitly states unrealized PnL rules use trade-by-trade enforcement. Categories doc (2025-10-23) also corrected this: "Critical Changes: RULE-004, 005, 008 are trade-by-trade (NOT close all)". Original spec (2025-01-17) is outdated.

### Conflict 2: Lockout Behavior
- **Source A** (Original spec, lines 34-35): "Set lockout until reset_time (MOD-002)"
- **Source B** (User Guidance): "No lockout, no timer"
- **Resolution**: Use User Guidance → No lockout
- **Rationale**: Trade-by-trade enforcement does not create lockouts. Position is closed, trader can immediately trade again.

### Conflict 3: Close All vs Close One
- **Source A** (Original spec, line 33): "Close all positions (MOD-001)"
- **Source B** (User Guidance): "Close ONLY the specific position that breached the limit"
- **Resolution**: Use User Guidance → Close only that position
- **Rationale**: This is the defining characteristic of trade-by-trade enforcement. Makes sense: if one position has excessive unrealized loss, close it, but don't close winning positions.

---

## Version History
- v1.0 (2025-01-17): Original specification (Hard Lockout)
- v2.0 (2025-01-17): Revised specification
- v3.0 (2025-10-25): Unified specification (Wave 3) - **MAJOR CHANGE**: Enforcement type changed from Hard Lockout to Trade-by-Trade per user guidance and updated categories doc

---

## Original Sources
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/rules/04_daily_unrealized_loss.md` (lines 1-40)
- `/docs/archive/2025-10-25-pre-wave1/02-status-tracking/current/RULE_CATEGORIES.md` (lines 42-66, updated 2025-10-23)
- `/docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` (lines 470-599)
- `/docs/analysis/wave2-gap-analysis/01-RISK-RULES-GAPS.md` (lines 197-258)
- User Guidance (Resolution Rule #1): Realized vs Unrealized PnL Enforcement

---

## Implementation Status (from Wave 2)
- **Status**: Not Started
- **Dependencies**:
  - Market Data Feed ❌ (must implement first)
  - Real-time unrealized P&L calculator ❌ (must implement)
  - Tick value map ❌ (configuration)
- **Estimated Effort**: 2 days
- **Priority**: High (account violation prevention)
- **Blockers**: Market Data Feed (real-time price updates)

---

## Test Coverage (from Wave 2)
- Unit tests: Not started
- Integration tests: Not started
- E2E tests: Not started

**Required Test Scenarios**:
1. Single position within limit (no breach)
2. Single position exceeds limit (close that position only)
3. Multiple positions, one breaches (close only that one)
4. Unrealized → Realized interaction (cascading to RULE-003)
5. Market data updates trigger recalculation
6. Tick value calculation accuracy
7. Long vs Short position calculations
8. Trader places new trade immediately after close (allowed)

---

## Related Rules
- **RULE-003** (DailyRealizedLoss): Interaction when unrealized closes → becomes realized
- **RULE-005** (MaxUnrealizedProfit): Similar real-time calculation, opposite direction
- **RULE-012** (TradeManagement): Also requires market data feed
