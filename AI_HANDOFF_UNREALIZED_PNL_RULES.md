# AI Handoff: Unrealized P&L Rules Implementation
**Date**: 2025-10-30
**Priority**: HIGH - Core risk rule implementation
**Environment**: Live debugging with `run_dev.py`

---

## 🎯 Mission: Get All Risk Rules 100% Working

Your job is to implement and test all risk rules **one by one** using live debugging with `run_dev.py`. The system is 85% complete - you're finishing the last 15%.

**Primary Focus**: Unrealized P&L rules (RULE-004 & RULE-005)
**End Goal**: All 13 risk rules actively protecting the account
**After This**: Move to CLI enhancements, daemon mode, UAC protection

---

## 📋 Quick Context: Where We Are

### What's Already Working ✅

1. **SDK Integration**: Live connection to TopstepX API
   - Real-time events flowing (ORDER_FILLED, POSITION_OPENED, etc.)
   - MNQ, ENQ, ES symbols working
   - Stop loss detection working
   - Trade history working

2. **P&L Calculation (Realized)**: Working correctly
   - Entry/exit prices tracked
   - Tick values per symbol (MNQ=$0.50, ES=$12.50, etc.)
   - Calculations verified with broker data
   - See recent fix: commit 1914c1e

3. **Core Infrastructure**: Complete
   - Database (SQLite)
   - Lockout Manager
   - Timer Manager
   - P&L Tracker
   - Reset Scheduler
   - Event pipeline (SDK → Engine → Rules → Enforcement)

4. **Data Integrity Layer (NEW - Just Built)**: Complete
   - Adapter layer (SDK → canonical types)
   - Symbol normalization (ENQ → NQ)
   - Tick value validation (fail-fast)
   - Runtime guards (147 new tests)
   - See: `AGENT_SWARM_COMPLETION_2025-10-30.md`

5. **Rules Currently Loading** (4/9):
   - ✅ DailyRealizedLossRule (limit=$-5.0)
   - ✅ DailyRealizedProfitRule (target=$1,000)
   - ✅ MaxContractsPerInstrumentRule
   - ✅ AuthLossGuardRule

### What Needs Work ⚠️

1. **Unrealized P&L Rules** (2 rules - YOUR PRIORITY):
   - ❌ RULE-004: Daily Unrealized Loss (not loading)
   - ❌ RULE-005: Max Unrealized Profit (not loading)
   - **Issue**: Need real-time quote data + floating P&L calculation

2. **Timer-Based Rules** (3 rules):
   - ❌ TradeFrequencyLimit (needs timers_config.yaml)
   - ❌ CooldownAfterLoss (needs timers_config.yaml)
   - ❌ SessionBlockOutside (needs timers_config.yaml)

3. **Other Rules** (already coded, just need testing):
   - NoStopLossGrace
   - SymbolBlocks
   - TradeManagement

---

## 🔥 PRIORITY #1: Unrealized P&L Rules

### The Challenge

**Unrealized P&L** = floating P&L based on **current market price** vs entry price.

**Example**:
```
Entry: Long 2 MNQ @ $26,000.00
Current market: $26,100.00  ← Need this price LIVE
Floating P&L: +100 points × $2/point × 2 contracts = +$400

If floating P&L hits -$750 → Trigger RULE-004 (Daily Unrealized Loss)
If floating P&L hits +$500 → Trigger RULE-005 (Max Unrealized Profit)
```

**The Problem**:
- We can't spam logs with quote data (too noisy)
- We need SDK quote data but calculated on our side
- Rules need to evaluate P&L on EVERY price tick
- Must be performant (not block event loop)

---

## 📖 Rule Specifications

### RULE-004: Daily Unrealized Loss
**File**: `docs/specifications/unified/rules/RULE-004-daily-unrealized-loss.md`
**Implementation**: `src/risk_manager/rules/daily_unrealized_loss.py` (exists!)
**Status**: Code written, not loading (needs tick data integration)

**Concept**:
- Track floating loss across ALL open positions
- If total unrealized loss ≤ limit (e.g., -$750) → Flatten all positions
- Resets daily at 5:00 PM ET

**Enforcement Actions**:
- `flatten` - Close all positions immediately
- `alert` - Send notification only
- `pause` - Prevent new positions

**Example Config**:
```yaml
daily_unrealized_loss:
  enabled: true
  limit: -750.0  # Negative value = loss threshold
  action: flatten
  reset_time: "17:00"  # 5:00 PM ET
  timezone: "America/New_York"
```

### RULE-005: Max Unrealized Profit
**File**: `docs/specifications/unified/rules/RULE-005-max-unrealized-profit.md`
**Implementation**: `src/risk_manager/rules/max_unrealized_profit.py` (exists!)
**Status**: Code written, not loading (needs tick data integration)

**Concept**:
- Track floating profit on individual positions
- When a position hits target profit (e.g., +$500) → Close that position
- This is "profit protection" - lock in gains before they reverse

**Enforcement Actions**:
- `close_position` - Close the winning position
- `reduce_to_limit` - Partially close (scale out)
- `alert` - Notify only

**Example Config**:
```yaml
max_unrealized_profit:
  enabled: true
  target: 500.0  # Positive value = profit target per position
  action: close_position
  per_position: true  # Apply to each position individually
```

---

## 🛠️ Technical Implementation Plan

### Step 1: Quote Data Integration (SDK)

The project-x-py SDK provides quote data. You need to:

1. **Subscribe to Quote Updates**:
   ```python
   # In src/risk_manager/integrations/trading.py

   # Subscribe to real-time quotes for each instrument
   async def _subscribe_to_quotes(self):
       """Subscribe to market data for open positions."""
       for symbol in self.instruments:
           instrument = self.suite[symbol]

           # Subscribe to quote updates
           await instrument.realtime_data.subscribe_to_quotes()

           # Register callback for quote updates
           self.suite.on(
               SDKEventType.QUOTE_UPDATE,
               self._on_quote_update
           )
   ```

2. **Handle Quote Updates** (without spamming logs):
   ```python
   async def _on_quote_update(self, event) -> None:
       """Handle QUOTE_UPDATE from SDK (silent - no logging)."""
       try:
           quote = event.data.get('quote')
           symbol = event.data.get('symbol')

           # Update internal price cache (don't log every tick!)
           self._latest_quotes[symbol] = {
               'last': quote.last,
               'bid': quote.bid,
               'ask': quote.ask,
               'timestamp': time.time()
           }

           # Calculate unrealized P&L for open positions
           await self._update_unrealized_pnl(symbol)

           # Publish internal event for rules to evaluate
           # (Rules subscribe to this, not raw quotes)
           if self._has_unrealized_pnl_change(symbol):
               await self.event_bus.publish(
                   RiskEvent(
                       event_type=EventType.UNREALIZED_PNL_UPDATE,
                       data={
                           'symbol': symbol,
                           'unrealized_pnl': self._calculate_unrealized_pnl(symbol)
                       }
                   )
               )
       except Exception as e:
           logger.debug(f"Error in quote update: {e}")  # Debug only
   ```

### Step 2: Floating P&L Calculation

**Create utility**: `src/risk_manager/integrations/unrealized_pnl.py`

```python
"""
Unrealized P&L Calculator

Calculates floating P&L based on:
- Entry price (from position tracking)
- Current market price (from quote updates)
- Position size and side (long/short)
- Tick values (from TICK_VALUES table)
"""

from decimal import Decimal
from loguru import logger

class UnrealizedPnLCalculator:
    """Calculate floating P&L for open positions."""

    def __init__(self, tick_values: dict):
        self.tick_values = tick_values
        self._open_positions = {}  # {contract_id: position_data}
        self._latest_quotes = {}   # {symbol: quote_data}

    def update_position(self, contract_id: str, entry_data: dict) -> None:
        """Track an opened position."""
        self._open_positions[contract_id] = {
            'entry_price': Decimal(str(entry_data['price'])),
            'size': entry_data['size'],
            'side': entry_data['side'],  # 'long' or 'short'
            'symbol': entry_data['symbol']
        }

    def remove_position(self, contract_id: str) -> None:
        """Remove a closed position."""
        if contract_id in self._open_positions:
            del self._open_positions[contract_id]

    def update_quote(self, symbol: str, price: float) -> None:
        """Update latest market price for symbol."""
        self._latest_quotes[symbol] = Decimal(str(price))

    def calculate_unrealized_pnl(
        self,
        contract_id: str
    ) -> Decimal | None:
        """
        Calculate floating P&L for a position.

        Returns:
            Decimal: Unrealized P&L in USD (positive = profit, negative = loss)
            None: If position not found or quote not available
        """
        if contract_id not in self._open_positions:
            return None

        position = self._open_positions[contract_id]
        symbol = position['symbol']

        if symbol not in self._latest_quotes:
            return None

        # Get tick economics
        if symbol not in self.tick_values:
            logger.error(f"Unknown symbol: {symbol}")
            return None

        tick_size = Decimal(str(self.tick_values[symbol]['size']))
        tick_value = Decimal(str(self.tick_values[symbol]['tick_value']))

        # Calculate price difference
        entry_price = position['entry_price']
        current_price = self._latest_quotes[symbol]

        if position['side'] == 'long':
            price_diff = current_price - entry_price
        else:  # short
            price_diff = entry_price - current_price

        # Convert to ticks
        ticks = price_diff / tick_size

        # Calculate P&L
        unrealized_pnl = ticks * tick_value * abs(position['size'])

        return unrealized_pnl

    def calculate_total_unrealized_pnl(self) -> Decimal:
        """
        Calculate total unrealized P&L across all open positions.

        Used by RULE-004 (Daily Unrealized Loss).
        """
        total = Decimal('0')

        for contract_id in self._open_positions:
            pnl = self.calculate_unrealized_pnl(contract_id)
            if pnl is not None:
                total += pnl

        return total
```

### Step 3: Update Rules to Use Floating P&L

**Modify**: `src/risk_manager/rules/daily_unrealized_loss.py`

```python
async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> dict[str, Any] | None:
    """
    Evaluate if total unrealized loss exceeds limit.

    Triggers on:
    - UNREALIZED_PNL_UPDATE events (frequent)
    - POSITION_OPENED/UPDATED events (initial calculation)
    """
    # Only evaluate on relevant events
    if event.event_type not in [
        EventType.UNREALIZED_PNL_UPDATE,
        EventType.POSITION_OPENED,
        EventType.POSITION_UPDATED
    ]:
        return None

    # Get total unrealized P&L across all positions
    # This comes from TradingIntegration's UnrealizedPnLCalculator
    total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

    if total_unrealized_pnl is None:
        return None

    # Check if loss exceeds limit
    if total_unrealized_pnl <= self.limit:  # limit is negative, e.g., -750.0
        return {
            'rule': self.__class__.__name__,
            'severity': 'CRITICAL',
            'message': f'Daily unrealized loss limit exceeded: ${total_unrealized_pnl:.2f} ≤ ${self.limit:.2f}',
            'action': self.action,  # 'flatten', 'alert', 'pause'
            'current_pnl': float(total_unrealized_pnl),
            'limit': self.limit
        }

    return None
```

**Modify**: `src/risk_manager/rules/max_unrealized_profit.py`

```python
async def evaluate(self, event: RiskEvent, engine: RiskEngine) -> dict[str, Any] | None:
    """
    Evaluate if position unrealized profit exceeds target.

    Triggers on:
    - UNREALIZED_PNL_UPDATE events (frequent)
    - POSITION_OPENED/UPDATED events (initial calculation)
    """
    # Only evaluate on relevant events
    if event.event_type not in [
        EventType.UNREALIZED_PNL_UPDATE,
        EventType.POSITION_OPENED,
        EventType.POSITION_UPDATED
    ]:
        return None

    # Check each open position's unrealized P&L
    positions_at_target = []

    for contract_id, position_data in engine.trading_integration.get_open_positions().items():
        unrealized_pnl = engine.trading_integration.get_position_unrealized_pnl(contract_id)

        if unrealized_pnl is None:
            continue

        # Check if profit exceeds target
        if unrealized_pnl >= self.target:  # target is positive, e.g., 500.0
            positions_at_target.append({
                'contract_id': contract_id,
                'symbol': position_data['symbol'],
                'unrealized_pnl': float(unrealized_pnl),
                'target': self.target
            })

    if positions_at_target:
        return {
            'rule': self.__class__.__name__,
            'severity': 'MEDIUM',
            'message': f'{len(positions_at_target)} position(s) hit profit target: ${self.target:.2f}',
            'action': self.action,  # 'close_position', 'reduce_to_limit', 'alert'
            'positions': positions_at_target
        }

    return None
```

### Step 4: Avoid Log Spam

**Key principle**: Quote updates happen FAST (multiple times per second). You MUST:

1. **Don't log every quote update**:
   ```python
   # ❌ BAD - Will spam logs
   async def _on_quote_update(self, event):
       logger.info(f"Quote: {event.data['symbol']} @ {event.data['quote'].last}")

   # ✅ GOOD - Silent processing
   async def _on_quote_update(self, event):
       # Update internal cache silently
       self._latest_quotes[symbol] = quote.last
       # No logging!
   ```

2. **Only log when P&L crosses thresholds**:
   ```python
   # Log when unrealized P&L changes significantly
   if abs(new_pnl - old_pnl) > 10.0:  # $10+ change
       logger.debug(f"Unrealized P&L change: {symbol} ${old_pnl:.2f} → ${new_pnl:.2f}")
   ```

3. **Log rule evaluations at INFO level**:
   ```python
   # When rule triggers, log at INFO
   if unrealized_pnl <= limit:
       logger.warning(f"❌ Daily Unrealized Loss: ${unrealized_pnl:.2f} ≤ ${limit:.2f}")
   ```

---

## 🔧 Development Workflow

### Your Primary Tool: `run_dev.py`

This is your live debugging environment. Use it to test each rule one by one.

**Run it**:
```bash
python run_dev.py
# Or with debug logging:
python run_dev.py --log-level DEBUG
```

**What you'll see**:
```
============================================================
        RISK MANAGER V34 - DEVELOPMENT MODE
============================================================

📊 POSITION OPENED - MNQ LONG 2 @ $26,000.00 | P&L: $0.00
  🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 2

📨 Event: position_opened → evaluating 4 rules
✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
✅ Rule: MaxContractsPerInstrument → PASS
✅ Rule: AuthLossGuard → PASS (connected)

# Price moves up...
# Quote updates happen silently (no logs)

# When unrealized P&L changes significantly:
📊 Unrealized P&L Update - MNQ: $0.00 → $+400.00

📨 Event: unrealized_pnl_update → evaluating 6 rules
✅ Rule: DailyUnrealizedLoss → PASS (current: $+400.00, limit: $-750.00)
❌ Rule: MaxUnrealizedProfit → FAIL (current: $+400.00 ≥ target: $500.00)

⚠️  Enforcement triggered: CLOSE_POSITION
```

### Step-by-Step Testing

**Test Plan** (do this for each rule):

1. **Enable the rule** in `config/risk_config.yaml`:
   ```yaml
   daily_unrealized_loss:
     enabled: true
     limit: -750.0
     action: flatten  # Start with 'alert' for testing!
   ```

2. **Start `run_dev.py`**:
   ```bash
   python run_dev.py --log-level INFO
   ```

3. **Open a test position** in TopstepX:
   - Use 1 micro contract (MNQ or MES)
   - Watch the logs for POSITION_OPENED event
   - Verify rule shows PASS initially

4. **Watch price movement**:
   - Wait for price to move (or manually adjust position size for testing)
   - Check that unrealized P&L updates
   - Verify rule evaluation logic

5. **Test enforcement** (use `alert` action first):
   - Let price move until rule triggers
   - Verify alert is logged
   - Verify rule shows FAIL with correct message

6. **Test actual enforcement** (change to `flatten` or `close_position`):
   - Let rule trigger again
   - Verify position is closed by SDK
   - Verify rule stops triggering after closure

7. **Check logs** for any errors or unexpected behavior

8. **Move to next rule** and repeat

---

## 📂 Key Files You'll Need

### Configuration
- `config/risk_config.yaml` - Enable/disable rules, set limits
- `config/accounts.yaml` - Account mappings
- `config/timers_config.yaml` - **MISSING** (you'll need to create this)

### Rule Specifications
- `docs/specifications/unified/rules/RULE-004-daily-unrealized-loss.md`
- `docs/specifications/unified/rules/RULE-005-max-unrealized-profit.md`
- All other RULE-*.md files in same directory

### Rule Implementations
- `src/risk_manager/rules/daily_unrealized_loss.py`
- `src/risk_manager/rules/max_unrealized_profit.py`
- `src/risk_manager/rules/base.py` - Base class for all rules

### Integration Layer
- `src/risk_manager/integrations/trading.py` - SDK integration (1,500+ lines)
- `src/risk_manager/integrations/tick_economics.py` - Tick value utilities
- `src/risk_manager/integrations/adapters.py` - NEW adapter layer

### Core System
- `src/risk_manager/core/engine.py` - Rule evaluation engine
- `src/risk_manager/core/events.py` - Event types and event bus
- `src/risk_manager/sdk/enforcement.py` - Enforcement executor

### Testing
- `tests/unit/test_rules/` - Unit tests for each rule
- `tests/integration/` - Integration tests with SDK
- `tests/e2e/` - End-to-end scenarios

### Documentation (What We Just Built)
- `AGENT_SWARM_COMPLETION_2025-10-30.md` - What the agent swarm built
- `COMPLETION_INDEX.md` - Navigation guide
- `SWARM_COMPLETION_REPORT_2025-10-30.md` - Detailed system status

---

## 🎯 Success Criteria

### For Each Rule:
- [ ] Rule loads successfully (no errors in startup logs)
- [ ] Rule evaluates on relevant events (see evaluation logs)
- [ ] Rule logic is correct (PASS when should pass, FAIL when should fail)
- [ ] Enforcement actions work (positions close, orders cancel, alerts fire)
- [ ] No log spam (quote updates don't flood logs)
- [ ] Tests pass for that rule

### Overall:
- [ ] All 9 enabled rules loading (9/9 = 100%)
- [ ] Live testing with `run_dev.py` shows correct behavior
- [ ] Multiple symbols work (MNQ, ENQ, ES)
- [ ] Multiple scenarios tested (profit, loss, limit hits, etc.)
- [ ] Documentation updated with any spec changes

---

## ⚠️ Known Issues & Gotchas

### 1. Specs May Be Outdated
**Issue**: The rule specs in `docs/specifications/unified/rules/` were written before the SDK integration.

**What to do**:
- Use the specs as a **guide** for the rule logic
- Check the **actual implementation** in `src/risk_manager/rules/*.py`
- When in doubt, the **implementation is correct** (it's been tested)
- Update the specs if you find major discrepancies

### 2. Event Types Might Differ
**Issue**: Specs mention event types that don't exist in our EventType enum.

**What to do**:
- Check `src/risk_manager/core/events.py` for actual event types
- Use the closest matching event type
- Add new event types if truly needed (but try to reuse existing ones)

### 3. Quote Data Performance
**Issue**: Quote updates happen multiple times per second. Can overwhelm the system.

**What to do**:
- Process quotes silently (no logging)
- Throttle rule evaluations (e.g., evaluate every 1 second, not every tick)
- Cache P&L calculations (don't recalculate on every quote)
- Only emit UNREALIZED_PNL_UPDATE events when P&L changes significantly

### 4. Tick Values Already Fixed
**Issue**: The agent swarm reports mention "hardcoded tick values" as a problem.

**Reality**: This was already fixed in commit 1914c1e. Tick values are now in `TICK_VALUES` table with validation.

**What to do**: Just use the existing `get_tick_economics()` function. It's safe.

### 5. Adapter Layer Is Shadow Mode
**Issue**: The new adapter layer adds canonical types but doesn't break existing code.

**Reality**: Rules can use EITHER:
- `event.data` (old dict-based, still works)
- `event.position` (new canonical Position object)

**What to do**: Start with `event.data` to get things working. Optionally migrate to `event.position` later.

---

## 🚀 Getting Started Checklist

**Before you start coding**:
- [ ] Read this handoff document (you're doing it!)
- [ ] Read `AGENT_SWARM_COMPLETION_2025-10-30.md` (understand what was built)
- [ ] Read RULE-004 and RULE-005 specs (understand the rules)
- [ ] Run `python run_dev.py` once to see current state
- [ ] Check what rules are currently loading (look for "✅ Loaded" in logs)

**First implementation task**:
- [ ] Create `UnrealizedPnLCalculator` class (see Step 2 above)
- [ ] Add quote subscription to `trading.py` (see Step 1 above)
- [ ] Update `daily_unrealized_loss.py` to use calculator (see Step 3 above)
- [ ] Test with `run_dev.py` - open position, watch P&L update
- [ ] Verify rule triggers when limit is hit

**Second implementation task**:
- [ ] Update `max_unrealized_profit.py` to use calculator
- [ ] Test with `run_dev.py` - open position, watch P&L update
- [ ] Verify rule triggers when target is hit
- [ ] Verify position closes when rule triggers

**Remaining tasks**:
- [ ] Create `timers_config.yaml` (template in SWARM_COMPLETION_REPORT Appendix A)
- [ ] Add rule instantiation code (code in SWARM_COMPLETION_REPORT Appendix B)
- [ ] Test all other rules one by one
- [ ] Fix any failing tests
- [ ] Document any spec discrepancies

---

## 📞 Help & References

### If You Get Stuck

1. **Check the logs**: `run_dev.py` shows everything happening
2. **Check existing tests**: `tests/unit/test_rules/test_daily_unrealized_loss.py`
3. **Check similar rules**: `daily_realized_loss.py` (realized P&L logic)
4. **Read SDK docs**: project-x-py SDK has quote subscription examples
5. **Ask user**: If specs are unclear or seem wrong

### Key Concepts to Understand

**Realized P&L** = Profit/loss from closed positions (already done, working)
**Unrealized P&L** = Floating profit/loss from open positions (YOUR JOB)

**Event Types**:
- `POSITION_OPENED` - New position created
- `POSITION_UPDATED` - Position size/price changed
- `POSITION_CLOSED` - Position fully closed
- `ORDER_FILLED` - Order executed (entry/exit)
- `UNREALIZED_PNL_UPDATE` - Floating P&L changed (YOU NEED TO ADD THIS)

**Enforcement Actions**:
- `alert` - Log message only
- `flatten` - Close all positions
- `close_position` - Close specific position
- `reduce_to_limit` - Partially close position
- `pause` - Prevent new positions
- `cancel_orders` - Cancel pending orders

---

## 🎓 Success Looks Like

When you're done, `run_dev.py` should show:

```
============================================================
        RISK MANAGER V34 - DEVELOPMENT MODE
============================================================

Configuration loaded successfully!
  Account: PRAC-V2-126244-84184528
  Instruments: MNQ, ENQ, ES
  Rules enabled: 9

✅ Loaded: DailyRealizedLossRule (limit=$-5.0)
✅ Loaded: DailyRealizedProfitRule (target=$1000.0)
✅ Loaded: MaxContractsPerInstrumentRule (2 symbols)
✅ Loaded: DailyUnrealizedLossRule (limit=$-750.0)        ← NEW!
✅ Loaded: MaxUnrealizedProfitRule (target=$500.0)        ← NEW!
✅ Loaded: TradeFrequencyLimitRule (max: 5/hour)          ← NEW!
✅ Loaded: CooldownAfterLossRule (cooldown: 5min)         ← NEW!
✅ Loaded: SessionBlockOutsideRule (hours: 8:30-15:00)    ← NEW!
✅ Loaded: AuthLossGuardRule

Risk Manager is running!
Press Ctrl+C to stop

============================================================
                  LIVE EVENT FEED
============================================================

📊 POSITION OPENED - MNQ LONG 2 @ $26,000.00 | Unrealized: $0.00

📨 Event: position_opened → evaluating 9 rules
✅ Rule: DailyRealizedLoss → PASS
✅ Rule: DailyRealizedProfit → PASS
✅ Rule: MaxContractsPerInstrument → PASS
✅ Rule: DailyUnrealizedLoss → PASS (current: $0.00, limit: $-750.00)
✅ Rule: MaxUnrealizedProfit → PASS (current: $0.00, target: $500.00)
✅ Rule: TradeFrequencyLimit → PASS
✅ Rule: CooldownAfterLoss → PASS
✅ Rule: SessionBlockOutside → PASS
✅ Rule: AuthLossGuard → PASS

# Price moves from $26,000 → $26,100
📊 Unrealized P&L Update - MNQ: $0.00 → $+400.00

📨 Event: unrealized_pnl_update → evaluating 9 rules
✅ All rules PASS (total unrealized: $+400.00)

# Price moves from $26,100 → $26,250 (hit profit target!)
📊 Unrealized P&L Update - MNQ: $+400.00 → $+1,000.00

📨 Event: unrealized_pnl_update → evaluating 9 rules
❌ Rule: MaxUnrealizedProfit → FAIL ($+1,000.00 ≥ $500.00 target)

⚠️  Enforcement triggered: CLOSE_POSITION
💰 ORDER FILLED - MNQ SELL 2 @ $26,250.00
📊 POSITION CLOSED - MNQ FLAT | Realized P&L: $+1,000.00

✅ Position closed successfully - Profit locked in!
```

**That's it!** All rules working, protecting the account, ready for production.

---

## 🎯 Final Notes

### The User's Vision

The user wants to:
1. **Get all risk rules 100% working** (your job!)
2. Then move to **CLI enhancements** (admin commands, status display)
3. Then implement **daemon mode** (run as Windows Service)
4. Then add **UAC protection** (prevent trader from killing service)

**You are step 1.** Finish the rules, and the rest becomes easy.

### The Bigger Picture

This risk manager is designed to protect TopstepX traders from blowing their accounts. The rules enforce:
- Position limits (don't overtrade)
- Loss limits (stop when losing)
- Profit targets (lock in gains)
- Time restrictions (no trading outside hours)
- Protection requirements (must have stop loss)

**Every rule saves money.** Make them work correctly!

---

## ✅ Handoff Complete

You have everything you need:
- **Clear mission**: Get unrealized P&L rules working
- **Technical plan**: Quote integration + P&L calculation
- **Testing environment**: `run_dev.py` for live debugging
- **All specs and code**: Rules exist, need integration
- **Success criteria**: All 9 rules loading and working

**Start with RULE-004 and RULE-005. Test them thoroughly. Then move to the rest.**

**Good luck!** 🚀

---

**Questions?** Read:
1. This handoff (you're here)
2. `AGENT_SWARM_COMPLETION_2025-10-30.md` (what was built)
3. `SWARM_COMPLETION_REPORT_2025-10-30.md` (system status)
4. Rule specs: `docs/specifications/unified/rules/RULE-*.md`
5. SDK integration: `src/risk_manager/integrations/trading.py`

**Most important**: Just start with `python run_dev.py` and see what happens! 🎯
