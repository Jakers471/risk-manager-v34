# RULE-005: Max Unrealized Profit

**Category**: Trade-by-Trade (Category 1)
**Priority**: Medium
**Status**: Not Implemented

---

## Unified Specification (v3.0)

### Purpose
Enforce profit target on individual positions by closing winning positions when unrealized profit hits target. This "takes profit" automatically to prevent giving back gains due to market reversals.

**Key Insight** (per user guidance): When unrealized positions close (hitting their profit target), they become realized P&L. We need quote data for unrealized tracking (Project-X-Py provides this).

### Trigger Condition
**Event Type**: `GatewayUserPosition` + real-time market price updates

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

    if unrealized_pnl >= config['target']:
        return BREACH, position_event  # Hit profit target
```

**Calculation Example** (ES, tick value = $50):
```python
# Long position
entry_price = 6000.00
current_price = 6010.00  # Up 10 ticks
size = 1 contract
tick_value = 50.0

unrealized_pnl = (6010.00 - 6000.00) / 0.25 * size * tick_value
               = (10.00 / 0.25) * 1 * 50.0
               = 40 ticks * 1 * $50
               = $2000

if $2000 >= $1000:  # Target = $1000
    BREACH (hit profit target!)
```

### Enforcement Action

**Type**: TRADE-BY-TRADE (User Guidance Applied - Resolution Rule #1)

**Action Sequence** (per user guidance):
1. **Close ONLY the specific position that hit the profit target** (take profit)
2. **Do NOT close other positions**
3. **Do NOT create lockout**
4. **Trader can continue trading immediately**
5. **Profit is locked in** when position closes

**Implementation Code**:
```python
async def enforce(self, position, unrealized_pnl, engine):
    # Close ONLY this specific position to take profit (trade-by-trade)
    await engine.enforcement.close_position(
        account_id=position['accountId'],
        contract_id=position['contractId'],
        reason=f"Profit target hit: ${unrealized_pnl:.2f} / ${self.config['target']:.2f}"
    )

    # NO lockout
    # NO cancel other orders
    # Trader can immediately place next trade

    self.logger.info(
        f"RULE-005 PROFIT TARGET: Closed {position['contractId']} position (take profit). "
        f"Unrealized P&L: ${unrealized_pnl:.2f}, Target: ${self.config['target']:.2f}"
    )

    # Note: When this position closes, profit becomes realized P&L
    # May trigger RULE-013 if daily realized profit target is hit
```

**Philosophy** (Trade-by-Trade Mode):
- **"Take profit on winner, keep trading"**
- Flexible - allows trader to continue finding opportunities
- Prevents giving back THIS position's profit to market reversal
- Does not force trader to stop for the day

### Configuration Parameters
```yaml
max_unrealized_profit:
  enabled: true
  target: 1000.0  # Take profit at $1000 unrealized profit per position

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
- `GatewayUserPosition` - Position updates
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
    # Check RULE-005 breach
```

### Database Schema
No database schema required (real-time calculation only, no state persistence).

### Examples

**Scenario 1: Position Below Target**
- Account state: ES Long 1 @ 6000.00
- Current price: 6005.00 (up 5 ticks)
- Unrealized P&L: 5 ticks * 1 * $50 = $250
- **Trigger**: No breach (below $1000 target)
- **Enforcement**: None
- **Result**: Position remains open, profit continues to grow

**Scenario 2: Single Position Hits Target (Trade-by-Trade)**
- Account state:
  - ES Long 1 @ 6000.00
  - MNQ Long 2 @ 21000.00
- Current ES price: 6010.00 (up 10 ticks)
- ES Unrealized P&L: 10 ticks * 1 * $50 = $500... wait, recalculate:
  - 10 points = 10 / 0.25 = 40 ticks
  - 40 ticks * 1 * $50 = $2000 (exceeds $1000 target)
- **Trigger**: ES position breach ($2000 >= $1000)
- **Enforcement** (per user guidance):
  1. Close ONLY ES position (take profit)
  2. Leave MNQ position open
  3. No lockout
- **Result**:
  - ES: 0 contracts (closed, profit locked in)
  - MNQ: 2 contracts (still open)
  - Trader can trade immediately

**Scenario 3: Unrealized → Realized Profit Interaction**
- Account state: Daily realized P&L = +$800
- ES Long 1 @ 6000.00
- Current ES price: 6010.00
- ES Unrealized P&L: $2000
- **Trigger**: RULE-005 breach (profit target hit)
- **Enforcement**:
  1. Close ES position (RULE-005)
  2. Position close → +$2000 realized profit
  3. New daily realized P&L: +$800 + $2000 = +$2800
  4. RULE-013 may trigger if daily profit target is $1000
- **Result**: RULE-013 lockout (if enabled)

**Scenario 4: Multiple Winning Positions**
- Account state:
  - ES Long 1 @ 6000.00 (unrealized: +$2000)
  - MNQ Long 2 @ 21000.00 (unrealized: +$500)
- **Trigger**: Only ES breaches RULE-005
- **Enforcement**: Close ONLY ES (take profit), keep MNQ open
- **Result**: MNQ position with +$500 unrealized profit remains open (may hit target later)

---

## Conflict Resolutions

### Conflict 1: Enforcement Type (MAJOR)
- **Source A** (Original spec 05_max_unrealized_profit.md, lines 6, 19, 33-35): "enforcement_type: Hard Lockout (Until Reset)", "close_all_and_lockout"
- **Source B** (RULE_CATEGORIES.md updated 2025-10-23, lines 42-66): "Category 1: Trade-by-Trade", "Close that winning position only (take profit)", "NO lockout"
- **Source C** (User Guidance - Resolution Rule #1): "UNREALIZED PnL Rules (RULE-004, RULE-005): Trade-by-trade enforcement, Close ONLY the specific position that breached the limit, Trader can continue trading immediately, No lockout, no timer"
- **Resolution**: Use User Guidance (Resolution Rule #1 - HIGHEST AUTHORITY) → Trade-by-Trade
- **Rationale**: User's authoritative architectural guidance explicitly states unrealized PnL rules use trade-by-trade enforcement. Categories doc (2025-10-23) also corrected this. Original spec (2025-01-17) is outdated.

### Conflict 2: Use Case Philosophy
- **Source A** (Original spec, line 37): "Use Case: 'Take profit and stop for the day' rule" (implies Hard Lockout)
- **Source B** (User Guidance): "Take profit on winner, keep trading" (implies Trade-by-Trade)
- **Resolution**: Use User Guidance → Trade-by-Trade (flexible, keep trading)
- **Rationale**: Two valid philosophies:
  - **Hard Lockout**: "Hit daily target, stop completely" (more conservative, prevents giving back profits)
  - **Trade-by-Trade**: "Take profit on winner, keep trading" (more flexible, allows continued opportunities)
  - User guidance selects Trade-by-Trade as default. If user wants "stop for the day" behavior, use RULE-013 instead.

### Conflict 3: Close All vs Close One
- **Source A** (Original spec, line 33): "Close all positions (lock in profits)"
- **Source B** (User Guidance): "Close ONLY the specific position that breached the limit"
- **Resolution**: Use User Guidance → Close only that position
- **Rationale**: Trade-by-trade enforcement closes only the winning position. Other positions may still be profitable and running.

---

## Version History
- v1.0 (2025-01-17): Original specification (Hard Lockout)
- v2.0 (2025-01-17): Revised specification
- v3.0 (2025-10-25): Unified specification (Wave 3) - **MAJOR CHANGE**: Enforcement type changed from Hard Lockout to Trade-by-Trade per user guidance and updated categories doc

---

## Original Sources
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/rules/05_max_unrealized_profit.md` (lines 1-38)
- `/docs/archive/2025-10-25-pre-wave1/02-status-tracking/current/RULE_CATEGORIES.md` (lines 42-66, updated 2025-10-23)
- `/docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` (lines 601-732)
- `/docs/analysis/wave2-gap-analysis/01-RISK-RULES-GAPS.md` (lines 260-330)
- User Guidance (Resolution Rule #1): Realized vs Unrealized PnL Enforcement

---

## Implementation Status (from Wave 2)
- **Status**: Not Started
- **Dependencies**:
  - Market Data Feed ❌ (must implement first)
  - Real-time unrealized P&L calculator ❌ (must implement - shared with RULE-004)
  - Tick value map ❌ (configuration)
- **Estimated Effort**: 2 days
- **Priority**: Medium (profit protection, not account violation)
- **Blockers**: Market Data Feed (real-time price updates)

---

## Test Coverage (from Wave 2)
- Unit tests: Not started
- Integration tests: Not started
- E2E tests: Not started

**Required Test Scenarios**:
1. Single position below target (no breach)
2. Single position hits target (close that position only, take profit)
3. Multiple positions, one hits target (close only that one)
4. Unrealized → Realized interaction (cascading to RULE-013)
5. Market data updates trigger recalculation
6. Tick value calculation accuracy
7. Long vs Short position calculations
8. Trader places new trade immediately after close (allowed)
9. Position continues beyond target before close (market movement delay)

---

## Related Rules
- **RULE-004** (DailyUnrealizedLoss): Same infrastructure (market data, real-time calc), opposite direction
- **RULE-013** (DailyRealizedProfit): Interaction when unrealized profit closes → becomes realized profit (may trigger hard lockout)
- **RULE-012** (TradeManagement): Also requires market data feed
