# SDK Integration Guide

**Critical**: This explains how we use the Project-X-Py SDK vs what the original specs described

---

## 🔑 Key Understanding

### The Timeline

**Before** (When Specs Were Written):
- No SDK existed
- Had to use raw ProjectX Gateway API
- Manual WebSocket (SignalR) handling
- Manual state tracking
- Custom API clients for everything

**Now** (Current Implementation):
- **Project-X-Py SDK v3.5.9** available
- Handles all the heavy lifting
- We build risk management ON TOP of SDK
- Much cleaner, less code, more reliable

---

## 📊 What The SDK Provides

### Core Features (We Don't Rebuild These)

| Feature | SDK Handles | We Add |
|---------|-------------|--------|
| **WebSocket Connection** | ✅ SignalR auto-connect | ❌ Nothing (SDK does it) |
| **Real-Time Events** | ✅ Positions, orders, trades | ✅ Risk rule evaluation |
| **Order Management** | ✅ Place, cancel, modify | ✅ Risk checks before SDK calls |
| **Position Management** | ✅ Close, partial close | ✅ Enforcement actions |
| **Account Data** | ✅ Balance, P&L, stats | ✅ Daily tracking, limits |
| **Market Data** | ✅ Quotes, bars, indicators | ❌ Nothing (not needed) |
| **Auto-Reconnect** | ✅ Built-in | ❌ Nothing (SDK does it) |
| **State Tracking** | ✅ Current positions/orders | ✅ Historical state, lockouts |

---

## 🗺️ Mapping: Specs → SDK

### Original Spec Components vs SDK Reality

#### 1. API Integration Layer

**Spec** (`docs/PROJECT_DOCS/api/`):
```python
# What specs described (manual implementation)
class SignalRListener:
    def connect(self):
        # Manual WebSocket setup
        # Manual auth
        # Manual event handling
```

**SDK Reality** (What we actually use):
```python
# SDK handles all of this
from project_x_py import TradingSuite

suite = await TradingSuite.create(
    instruments=["MNQ"],  # SDK handles connection, auth, everything
)

# Events come automatically via SDK
suite.realtime.on_position_update(callback)
```

**Our Code** (`src/risk_manager/sdk/suite_manager.py`):
```python
# We just manage TradingSuite lifecycle
class SuiteManager:
    async def add_instrument(self, symbol):
        suite = await TradingSuite.create(instruments=[symbol])
        self.suites[symbol] = suite
        # SDK handles the rest
```

---

#### 2. Real-Time Events

**Spec** (`docs/PROJECT_DOCS/architecture/`):
```
Described:
- Custom SignalR event listener
- Manual event parsing
- Custom state management
```

**SDK Reality**:
```python
# SDK provides clean event system
suite['MNQ'].on_position_update(lambda pos: handle_position(pos))
suite['MNQ'].on_order_update(lambda order: handle_order(order))
suite['MNQ'].on_trade(lambda trade: handle_trade(trade))
```

**Our Code** (`src/risk_manager/sdk/event_bridge.py`):
```python
# We bridge SDK events → Risk events
class EventBridge:
    def setup_callbacks(self, suite):
        suite.on_position_update(self._on_position)
        suite.on_trade(self._on_trade)

    def _on_position(self, position):
        # Convert SDK event → RiskEvent
        event = RiskEvent(
            type=EventType.POSITION_UPDATED,
            data=position
        )
        self.event_bus.publish(event)  # To risk engine
```

---

#### 3. Enforcement Actions

**Spec** (`docs/PROJECT_DOCS/modules/enforcement_actions.md`):
```python
# What spec described (manual REST API calls)
def close_all_positions(account_id):
    # POST /api/Position/searchOpen
    # Parse response
    # For each position:
    #   POST /api/Position/closeContract
```

**SDK Reality**:
```python
# SDK provides simple methods
from project_x_py import TradingSuite

# Close position
await suite['MNQ'].close_position()

# Close specific size
await suite['MNQ'].close_position(quantity=2)

# Cancel all orders
await suite.cancel_all_orders()
```

**Our Code** (`src/risk_manager/sdk/enforcement.py`):
```python
# We wrap SDK methods with enforcement logic
class EnforcementActions:
    async def flatten_all(self, account_id: str):
        # Use SDK to close positions
        for symbol, suite in self.suite_manager.get_all_suites().items():
            await suite.close_position()  # SDK handles API call
            await suite.cancel_all_orders()  # SDK handles API call

        # We add: logging, lockout, notifications
        self.lockout_manager.set_lockout(account_id, reason)
```

---

#### 4. State Management

**Spec** (`docs/PROJECT_DOCS/modules/`):
```
Described:
- Custom P&L tracking
- Manual position reconciliation
- Custom order state management
```

**SDK Reality**:
```python
# SDK tracks current state automatically
stats = await suite.get_stats()
# Returns: balance, open_pl, realized_pl, etc.

positions = suite.get_positions()
# Returns: current positions with P&L

orders = suite.get_orders()
# Returns: pending orders
```

**Our Code** (`src/state/pnl_tracker.py` - to be built):
```python
# We add: historical tracking, daily limits, reset logic
class PnLTracker:
    async def track_trade(self, trade):
        # Get current from SDK
        stats = await self.suite.get_stats()

        # We track: daily totals, trade history
        self.daily_realized += trade.realized_pnl

        # Check against limits
        if self.daily_realized <= self.daily_limit:
            # Trigger enforcement
```

---

## 🏗️ Our Architecture: Risk Layer on SDK

```
┌────────────────────────────────────────────────────────┐
│          Risk Manager V34 (Our Code)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Risk Engine                                     │  │
│  │  - Rule evaluation                               │  │
│  │  - Enforcement coordination                      │  │
│  │  - Lockout management                            │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                              │
│                         ↓                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  SDK Bridge (Our Wrapper)                        │  │
│  │  - Convert SDK events → Risk events              │  │
│  │  - Add risk checks before SDK calls              │  │
│  │  - Manage TradingSuite lifecycle                 │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────┐
│      Project-X-Py SDK (v3.5.9)                         │
│  - WebSocket connection                                │
│  - Real-time events                                    │
│  - Order/position management                           │
│  - API client                                          │
│  - Auto-reconnection                                   │
└────────────────────────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────┐
│      TopstepX Gateway API                              │
│      (ProjectX Platform)                               │
└────────────────────────────────────────────────────────┘
```

---

## 📋 What We Build vs What SDK Provides

### SDK Provides (Don't Rebuild)
- ✅ WebSocket connection & auth
- ✅ Real-time event streaming
- ✅ Order placement/cancellation/modification
- ✅ Position closing (full & partial)
- ✅ Account statistics
- ✅ Market data & indicators
- ✅ Connection health & auto-reconnect
- ✅ Current state tracking

### We Build (Risk Management Layer)
- ⏳ **Risk Rules** (12 rules - see `docs/PROJECT_DOCS/rules/`)
  - Daily loss limits
  - Position size limits
  - Trade frequency limits
  - Session restrictions
  - Stop-loss enforcement
  - etc.

- ⏳ **State Persistence** (SQLite)
  - Historical P&L tracking
  - Trade history
  - Lockout states
  - Daily counters

- ⏳ **Enforcement Coordination**
  - Simultaneous actions (close + cancel + lockout)
  - Retry logic
  - Enforcement logging

- ⏳ **Lockout Management**
  - Prevent trading when limits hit
  - Countdown timers
  - Daily reset at 5:00 PM ET

- ⏳ **CLI Interfaces**
  - Admin CLI (config)
  - Trader CLI (status)

- ⏳ **Config Management**
  - YAML-based configuration
  - Rule enable/disable
  - Limit adjustments

---

## 💻 Code Examples

### Example 1: Using SDK for Enforcement

**Spec Approach** (What we DON'T do):
```python
# Manual API calls
import httpx

async def close_position(account_id, contract_id):
    url = "https://api.topstepx.com/api/Position/closeContract"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"accountId": account_id, "contractId": contract_id}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        # Parse response, handle errors, etc.
```

**SDK Approach** (What we DO):
```python
# Use SDK
async def close_position(symbol: str):
    suite = self.suite_manager.get_suite(symbol)
    await suite.close_position()  # SDK handles everything
```

---

### Example 2: Monitoring Positions

**Spec Approach** (What we DON'T do):
```python
# Manual SignalR listener
class SignalRListener:
    def on_message(self, message):
        if message['type'] == 'GatewayUserPosition':
            # Parse JSON
            # Update state
            # Validate
            # Route to rules
```

**SDK Approach** (What we DO):
```python
# SDK provides clean events
suite['MNQ'].on_position_update(lambda pos: self.handle_position(pos))

def handle_position(self, position):
    # SDK gives us clean Position object
    # We just evaluate risk rules
    event = RiskEvent(type=EventType.POSITION_UPDATED, data=position)
    await self.risk_engine.evaluate(event)
```

---

### Example 3: Daily Loss Rule Implementation

**Using SDK**:
```python
# src/rules/daily_realized_loss.py
from project_x_py import TradingSuite

class DailyRealizedLossRule(RiskRule):
    async def evaluate(self, event: RiskEvent, engine: RiskEngine):
        if event.type != EventType.TRADE_EXECUTED:
            return  # Only check on trades

        # Get current stats from SDK
        suite = engine.suite_manager.get_suite(event.data['symbol'])
        stats = await suite.get_stats()

        # Check if daily loss limit hit
        if stats.realized_pl <= self.limit:  # e.g., -$500
            # Use SDK to close all positions
            await self.enforcement.flatten_all()

            # We handle: lockout until reset
            self.lockout_manager.set_lockout(
                account_id=engine.account_id,
                reason="Daily loss limit reached",
                until=self.get_reset_time()  # 5:00 PM ET
            )
```

---

## 🗂️ File Organization

### SDK Wrapper Layer
```
src/risk_manager/sdk/
├── __init__.py
├── suite_manager.py        # Manage TradingSuite instances
├── event_bridge.py         # SDK events → Risk events
└── enforcement.py          # Enforcement actions via SDK
```

### Risk Management Layer
```
src/risk_manager/
├── core/
│   ├── manager.py          # Main RiskManager (uses SDK)
│   ├── engine.py           # Rule evaluation
│   ├── events.py           # Event system
│   └── config.py           # Configuration
│
├── rules/                  # Our 12 risk rules
│   ├── base.py
│   ├── daily_loss.py       # Uses SDK for P&L
│   ├── max_position.py     # Uses SDK for positions
│   └── ...
│
└── state/                  # Our state management
    ├── persistence.py      # SQLite (historical)
    ├── lockout_manager.py  # Lockout logic
    ├── pnl_tracker.py      # Daily P&L tracking
    └── ...
```

---

## 🎯 Implementation Guidelines

### When Implementing a New Feature

**1. Check SDK First**
```python
# Ask: Does the SDK already provide this?
# Example: Closing positions

# ✅ USE SDK
await suite.close_position()

# ❌ DON'T manually call API
# await httpx.post("https://api.topstepx.com/...")
```

**2. Wrap SDK with Risk Logic**
```python
# SDK provides capability
# We add risk checks/logging/state

async def close_position_with_enforcement(symbol: str, reason: str):
    # 1. SDK call
    suite = self.suite_manager.get_suite(symbol)
    await suite.close_position()

    # 2. Our additions
    self.log_enforcement(symbol, "close_position", reason)
    self.update_state(symbol, "position_closed")
    self.notify_trader(f"Position closed: {reason}")
```

**3. Add Historical Tracking (What SDK Doesn't Do)**
```python
# SDK: Current state only
stats = await suite.get_stats()  # Right now

# We add: Historical tracking
self.daily_pnl_tracker.record(stats.realized_pl)
self.trade_history.append(trade)
self.db.save(trade)  # Persist for future sessions
```

---

## 📖 Reference Mapping

### Spec File → SDK Feature

| Spec Document | SDK Equivalent | Our Addition |
|---------------|----------------|--------------|
| `api/auth.py` | `TradingSuite.create()` | Nothing (SDK authenticates) |
| `api/signalr_listener.py` | `suite.on_*()` callbacks | Event → Risk evaluation |
| `api/rest_client.py` | `suite.*()` methods | Risk checks before calls |
| `enforcement/actions.py` | `suite.close_position()` | Logging, lockout, retry |
| `state/state_manager.py` | `suite.get_stats()` | Historical tracking |
| `rules/*.py` | N/A | All our code (risk logic) |

---

## ⚠️ Common Mistakes to Avoid

### ❌ Don't Do This
```python
# Reimplementing what SDK provides
class CustomWebSocketListener:
    async def connect(self):
        # Manual WebSocket connection
        # DON'T DO THIS - SDK handles it
```

### ✅ Do This Instead
```python
# Use SDK, add risk logic
suite = await TradingSuite.create(instruments=["MNQ"])
suite.on_position_update(self.check_risk_rules)
```

---

### ❌ Don't Do This
```python
# Manual API calls
async with httpx.AsyncClient() as client:
    await client.post("https://api.topstepx.com/api/Order/cancel", ...)
    # DON'T DO THIS - SDK has methods
```

### ✅ Do This Instead
```python
# Use SDK method
await suite.cancel_all_orders()
```

---

### ❌ Don't Do This
```python
# Duplicating SDK's state tracking
class PositionTracker:
    def track_position(self, position):
        self.current_positions[symbol] = position
        # DON'T DO THIS - SDK tracks current state
```

### ✅ Do This Instead
```python
# Get current from SDK, add historical tracking
current = suite.get_positions()  # From SDK
self.history.append(current)     # We track history
self.db.save(current)            # We persist
```

---

## 🧪 Testing with SDK

### Mock SDK for Unit Tests
```python
# tests/unit/test_daily_loss_rule.py
from unittest.mock import AsyncMock

async def test_daily_loss_enforcement():
    # Mock SDK
    mock_suite = AsyncMock()
    mock_suite.get_stats.return_value = Stats(realized_pl=-600)

    # Test our rule
    rule = DailyRealizedLossRule(limit=-500)
    result = await rule.evaluate(trade_event, engine)

    # Verify our logic
    assert result.action == "flatten"
    mock_suite.close_position.assert_called_once()
```

### Integration Tests with Real SDK
```python
# tests/integration/test_sdk_live.py
@pytest.mark.integration
async def test_connect_to_live_account():
    # Real SDK connection
    suite = await TradingSuite.create(instruments=["MNQ"])

    # Verify it works
    assert suite is not None
    stats = await suite.get_stats()
    assert stats.account_id == "PRAC-V2-126244-84184528"
```

---

## 📚 Further Reading

1. **SDK Documentation**:
   - Project-X-Py README
   - SDK examples
   - API reference

2. **Our Integration**:
   - `src/risk_manager/sdk/suite_manager.py` - How we use SDK
   - `src/risk_manager/sdk/event_bridge.py` - Event conversion
   - `examples/04_sdk_integration.py` - SDK usage examples

3. **Original Specs** (for context):
   - `docs/PROJECT_DOCS/INTEGRATION_NOTE.md` - How specs relate to SDK
   - `docs/PROJECT_DOCS/api/topstepx_integration.md` - Raw API (pre-SDK)

---

## 🎓 Summary

**Key Takeaways**:
1. **SDK handles trading** - WebSocket, orders, positions, auth
2. **We add risk logic** - Rules, limits, lockouts, enforcement
3. **Don't reimplement** - If SDK has it, use it
4. **Wrap with risk** - Add our checks/logging/state on top
5. **Test properly** - Mock SDK for unit tests, real SDK for integration

**Golden Rule**: **If the SDK can do it, use the SDK. We focus on risk management.**

---

**Last Updated**: 2025-10-23
**See Also**:
- `CLAUDE.md` - Main entry point
- `docs/current/PROJECT_STATUS.md` - Current implementation
- `docs/PROJECT_DOCS/INTEGRATION_NOTE.md` - Spec history
