# Multi-Symbol Support - Account-Wide Risk Management

**Date**: 2025-10-23
**Critical**: How risk rules apply across ALL instruments you trade

---

## 🎯 The Answer

**YES - Risk Manager V34 supports ANY symbol/contract type (MNQ, ES, GC, NQ, MGC, etc.)**

**Risk rules apply to your ENTIRE ACCOUNT, not per-symbol.**

---

## 🏗️ Architecture: Two Approaches

### Approach 1: Single TradingSuite with Multiple Instruments (RECOMMENDED)

**How SDK Works**:
```python
# Create ONE TradingSuite with multiple instruments
suite = await TradingSuite.create(
    instruments=["MNQ", "ES", "GC", "NQ"]  # All instruments you trade
)

# Access individual instrument data
mnq = suite['MNQ']
es = suite['ES']
gc = suite['GC']

# Events from ALL instruments come through suite.event_bus
suite.event_bus.subscribe(EventType.POSITION_UPDATED, callback)
# ↑ Receives position updates for MNQ, ES, GC, NQ, etc.
```

**Key Point**: You get **account-wide events** regardless of which symbol you're trading. The SDK's SignalR connection receives ALL position/trade/order updates for your account.

---

### Approach 2: Multiple TradingSuite Instances (CURRENT - WORKS BUT OVERKILL)

**Current Implementation** (`suite_manager.py`):
```python
# Create separate TradingSuite for each instrument
self.suites = {
    'MNQ': await TradingSuite.create('MNQ', ...),
    'ES': await TradingSuite.create('ES', ...),
    'GC': await TradingSuite.create('GC', ...),
}

# Each suite has its own WebSocket connection
# Each suite receives events for its instrument
```

**This works** but creates multiple WebSocket connections unnecessarily.

---

## 📋 Risk Rules: Account-Wide vs Trade-Specific

### Account-Wide Rules (Apply Across ALL Symbols)

These rules aggregate data from **all instruments**:

#### RULE-001: Max Contracts (Account Total)
```yaml
max_contracts:
  enabled: true
  limit: 5  # Max 5 contracts across ALL instruments combined
```

**Example**:
```
Trader has:
- MNQ: 2 long
- ES: 2 long
- GC: 1 long
Total: 5 contracts ✅ At limit

Trader places order for 1 more ES → BLOCKED (would exceed 5)
```

**Implementation**:
```python
def calculate_total_contracts(self):
    total = 0
    for symbol, suite in self.suites.items():
        positions = suite.get_positions()
        total += abs(positions.net_quantity)  # Sum all symbols
    return total
```

---

#### RULE-003: Daily Realized Loss (Account Total)
```yaml
daily_realized_loss:
  enabled: true
  limit: -500.0  # Max $500 loss per day across ALL instruments
```

**Example**:
```
Today's trades:
- MNQ: -$200 realized
- ES: -$150 realized
- GC: -$180 realized
Total: -$530 → BREACH! Lock account until 5 PM
```

**Implementation**:
```python
async def track_trade(self, trade_event):
    # Trade could be from ANY symbol
    pnl = trade_event.data['realized_pnl']

    # Add to daily total (account-wide)
    self.daily_realized_pnl += pnl

    # Check against account limit
    if self.daily_realized_pnl <= -500.0:
        await self.flatten_all_instruments()  # Close ALL positions
        self.lockout_manager.set_lockout()     # Lock entire account
```

---

#### RULE-006: Trade Frequency (Account Total)
```yaml
trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3  # Max 3 trades per minute across ALL symbols
```

**Example**:
```
Within 1 minute:
- MNQ: 1 trade
- ES: 1 trade
- GC: 1 trade
Total: 3 trades → At limit

4th trade (any symbol) → BLOCKED
```

---

### Per-Instrument Rules (Symbol-Specific)

These rules apply to **individual symbols**:

#### RULE-002: Max Contracts Per Instrument
```yaml
max_contracts_per_instrument:
  enabled: true
  instrument_limits:
    MNQ: 2  # Max 2 MNQ contracts
    ES: 1   # Max 1 ES contract
    GC: 3   # Max 3 GC contracts
```

**Example**:
```
Trader has:
- MNQ: 2 long ✅ (at limit for MNQ)
- ES: 1 long ✅ (at limit for ES)
- GC: 0 ✅ (can trade up to 3)

Trader places order for 1 more MNQ → BLOCKED (MNQ limit)
Trader places order for 1 GC → ALLOWED (under GC limit)
```

---

#### RULE-004: Daily Unrealized Loss (Per Position)
```yaml
daily_unrealized_loss:
  enabled: true
  limit: -200.0  # Max floating loss per position
```

**Example**:
```
Trader has:
- MNQ: 2 contracts, P&L: -$150 ✅
- ES: 1 contract, P&L: -$220 ❌ (exceeds -$200)
- GC: 1 contract, P&L: +$50 ✅

Action: Close ES position ONLY (not MNQ or GC)
```

---

## 🔄 How Events Flow Across Symbols

### SignalR WebSocket Events (Account-Wide)

```
TopstepX API (SignalR)
     │
     ├─ Position Update: MNQ (2 long @ 20,125)
     ├─ Trade Executed: ES (1 short @ 5,950, P&L: -$50)
     ├─ Position Update: GC (1 long @ 2,030)
     ├─ Order Placed: NQ (2 long limit @ 21,000)
     │
     ▼
TradingSuite.event_bus
     │
     ▼
EventBridge (Our Code)
     │
     ├─ Convert to RiskEvent (with symbol)
     ├─ Add to Risk EventBus
     │
     ▼
RiskEngine
     │
     ├─ Evaluate all 13 rules
     ├─ Aggregate account-wide metrics
     ├─ Check per-symbol limits
     │
     ▼
Enforcement Actions (if breach)
```

**Key Insight**: The SDK receives **ALL account activity** via SignalR, regardless of which instruments you specified. The `instruments` parameter tells the SDK which instruments to track market data for, but you get account-wide position/trade/order events automatically.

---

## 📊 Account-Wide Aggregation Examples

### Example 1: Max Contracts (Account Total)

**Configuration**:
```yaml
max_contracts:
  enabled: true
  limit: 5
  count_type: "net"  # Net position (long - short)
```

**Scenario**:
```
Current positions:
- MNQ: 2 long
- ES: 1 long
- GC: 2 long
Total: 5 net contracts (at limit)

Trader places order for 1 MNQ → BLOCKED
Trader closes 1 ES → Now 4 total
Trader can now place 1 more contract (any symbol)
```

**Implementation**:
```python
class MaxContractsRule(RiskRule):
    async def evaluate(self, event: RiskEvent, engine: RiskEngine):
        if event.type != EventType.POSITION_UPDATED:
            return

        # Aggregate across ALL instruments
        total_contracts = 0
        for symbol, suite in engine.suite_manager.get_all_suites().items():
            positions = suite.get_positions()
            total_contracts += abs(positions.net_quantity)

        # Check account-wide limit
        if total_contracts > self.config['limit']:
            # Breach! Close the position that caused it
            symbol = event.data['symbol']
            await engine.enforcement.close_position(symbol)
```

---

### Example 2: Daily Loss (Account Total)

**Configuration**:
```yaml
daily_realized_loss:
  enabled: true
  limit: -500.0
```

**Scenario**:
```
Today's trades (across ALL symbols):
09:30 - MNQ: -$100
10:15 - ES: -$150
11:00 - GC: -$50
11:30 - MNQ: +$80
12:00 - ES: -$300

Daily Total: -$520 → BREACH!

Action:
1. Close all positions (MNQ, ES, GC, everything)
2. Cancel all orders (all symbols)
3. Lock account until 5:00 PM
```

**Implementation**:
```python
class DailyRealizedLossRule(RiskRule):
    async def evaluate(self, event: RiskEvent, engine: RiskEngine):
        if event.type != EventType.TRADE_EXECUTED:
            return

        # Update daily P&L (account-wide SQLite tracking)
        trade_pnl = event.data['realized_pnl']
        daily_total = engine.pnl_tracker.add_trade(
            account_id=engine.account_id,
            pnl=trade_pnl
        )

        # Check account-wide limit
        if daily_total <= self.config['limit']:  # -500
            # HARD LOCKOUT: Close all instruments
            await engine.enforcement.flatten_all()
            engine.lockout_manager.set_lockout(
                until=self._get_reset_time()  # 5 PM
            )
```

---

## 🛠️ Configuration: Adding New Symbols

### Method 1: Static Configuration (risk_config.yaml)

**File**: `config/risk_config.yaml`

```yaml
general:
  instruments:
    - MNQ   # E-mini NASDAQ
    - ES    # E-mini S&P 500
    - GC    # Gold futures
    - NQ    # NASDAQ-100
    - MGC   # Micro Gold
    # Add any symbol you trade
```

**On startup**:
```python
# Load config
config = yaml.safe_load(open('config/risk_config.yaml'))
instruments = config['general']['instruments']

# Create TradingSuite with all instruments
suite = await TradingSuite.create(instruments=instruments)
```

---

### Method 2: Dynamic Addition (While Running)

**Admin CLI**:
```bash
$ risk-manager-admin

> add-instrument NQ
✅ Added NQ to monitored instruments
✅ Risk rules now apply to NQ

> list-instruments
Active instruments:
- MNQ
- ES
- GC
- NQ (just added)
```

**Code**:
```python
# Add instrument dynamically
await suite_manager.add_instrument('NQ')

# Start bridging events
await event_bridge.add_instrument('NQ', suite['NQ'])
```

---

## 🎯 Recommended Setup

### For Multi-Instrument Trading

**1. List ALL Symbols You Trade**

`config/risk_config.yaml`:
```yaml
general:
  instruments:
    - MNQ
    - ES
    - GC
    - NQ
    - MGC
    - RTY  # Micro Russell 2000
    - CL   # Crude Oil
    # Add all symbols you might trade
```

**2. Configure Account-Wide Limits**

```yaml
# Account-wide limits (apply to ALL symbols combined)
max_contracts:
  enabled: true
  limit: 10  # Max 10 contracts total across all symbols

daily_realized_loss:
  enabled: true
  limit: -1000.0  # Max $1000 loss per day (all symbols)

trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 5   # Max 5 trades/min (all symbols)
    per_hour: 20    # Max 20 trades/hr (all symbols)
```

**3. Configure Per-Instrument Limits (Optional)**

```yaml
# Per-instrument limits (specific to each symbol)
max_contracts_per_instrument:
  enabled: true
  instrument_limits:
    MNQ: 5   # Max 5 MNQ
    ES: 3    # Max 3 ES
    GC: 2    # Max 2 GC
    # Others: use default_limit
  default_limit: 3  # Default for unlisted symbols
```

---

## 🧪 Testing Multi-Symbol Support

### Test Script: `test_multi_symbol.py`

```python
import asyncio
from risk_manager import RiskManager

async def test_multi_symbol():
    """Test risk management across multiple symbols."""

    # Initialize with multiple instruments
    rm = await RiskManager.create(
        instruments=["MNQ", "ES", "GC"],
        rules={
            "max_contracts": 5,           # Account total
            "daily_realized_loss": -500.0  # Account total
        }
    )

    await rm.start()

    print("✅ Risk Manager monitoring: MNQ, ES, GC")
    print("📊 Rules apply to ENTIRE ACCOUNT")
    print("🔒 Max 5 contracts total (all symbols)")
    print("💰 Max -$500 loss per day (all symbols)")

    # Simulate trades across symbols
    # ... test account-wide aggregation

    await rm.stop()

if __name__ == "__main__":
    asyncio.run(test_multi_symbol())
```

---

## 🔍 Troubleshooting

### "Risk Manager only watching MNQ?"

**Cause**: Configuration only lists MNQ

**Fix**: Add all symbols to config:
```yaml
general:
  instruments:
    - MNQ
    - ES
    - GC
    # Add all symbols you trade
```

---

### "Switched to GC but rules didn't trigger?"

**Cause**: GC not in monitored instruments

**Fix**:
```yaml
general:
  instruments:
    - MNQ
    - ES
    - GC  # ← Add this
```

Or add dynamically via Admin CLI:
```bash
> add-instrument GC
```

---

### "Want to trade ANY symbol without pre-configuration?"

**Solution**: Monitor account-wide events regardless of instrument

```python
# Subscribe to ALL account events (not instrument-specific)
suite.event_bus.subscribe_all(self.handle_any_event)

# Events include symbol in data
async def handle_any_event(self, event):
    symbol = event.data.get('symbol')
    # Process regardless of symbol
```

**This is automatic** with the SDK - you get ALL account activity via SignalR.

---

## 📋 Summary

### Multi-Symbol Support

✅ **Supported**: MNQ, ES, GC, NQ, MGC, RTY, CL, etc.
✅ **Account-Wide**: Risk rules aggregate across ALL instruments
✅ **Automatic**: SignalR sends all account activity
✅ **Configurable**: Add/remove instruments in config or dynamically

### Risk Rules Scope

**Account-Wide** (aggregate all symbols):
- RULE-001: Max Contracts
- RULE-003: Daily Realized Loss
- RULE-006: Trade Frequency
- RULE-007: Cooldown After Loss
- RULE-009: Session Restrictions
- RULE-010: Auth Loss Guard
- RULE-013: Daily Realized Profit

**Per-Instrument** (symbol-specific):
- RULE-002: Max Contracts Per Instrument
- RULE-004: Daily Unrealized Loss (per position)
- RULE-005: Max Unrealized Profit (per position)
- RULE-008: Stop-Loss Enforcement (per position)
- RULE-011: Symbol Blocks (blacklist)

### Configuration

**Setup**: List all symbols in `config/risk_config.yaml`
```yaml
general:
  instruments:
    - MNQ
    - ES
    - GC
    - NQ
    # Add all symbols you trade
```

**Result**: Risk Manager protects your ENTIRE ACCOUNT regardless of which symbol you trade.

---

**Created**: 2025-10-23
**Key Insight**: Risk rules apply to your ACCOUNT, not per-symbol. You can trade ANY symbol and risk protection works across everything.
