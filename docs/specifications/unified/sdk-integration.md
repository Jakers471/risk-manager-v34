# SDK Integration Specification

**Document ID:** UNIFIED-SDK-001
**Created:** 2025-10-25
**Status:** Complete - SDK-First Architecture
**Dependencies:** Project-X-Py SDK v3.5.9+

---

## Executive Summary

Risk Manager V34 uses **SDK-first architecture**, leveraging the Project-X-Py SDK to handle all trading platform interactions. This eliminates 93% of custom API integration code and provides reliable, battle-tested communication with TopstepX.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Risk Manager V34                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - Risk Rules (13 rules)                                 │  │
│  │  - Risk Engine (event processing + enforcement)          │  │
│  │  - State Management (P&L, lockouts, timers)             │  │
│  │  - Event Bridge (SDK → Risk event conversion)           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ Clean abstraction layer
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Project-X-Py SDK v3.5.9                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - TradingSuite (main interface)                         │  │
│  │  - PositionManager (positions, P&L)                      │  │
│  │  - OrderManager (place, cancel, modify orders)           │  │
│  │  - RealtimeDataManager (WebSocket events)                │  │
│  │  - QuoteManager (market data, quotes) ⭐ NEW             │  │
│  │  - EventBus (pub/sub events)                             │  │
│  │  - Auto-reconnection + error handling                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API + WebSocket (SignalR)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: TopstepX Gateway API                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API: https://api.topstepx.com                      │  │
│  │  SignalR Hub: wss://rtc.topstepx.com                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. SDK Components

### 1.1 TradingSuite

**Purpose:** Main interface for multi-instrument trading

**Creation Pattern:**
```python
from project_x_py import TradingSuite

suite = await TradingSuite.create(
    instruments=["MNQ", "ES"],        # List of symbols
    timeframes=["1min", "5min"],      # OHLCV timeframes
    enable_orderbook=True,             # Level 2 market depth
    enable_risk_management=True,       # SDK's built-in risk
    enable_statistics=True             # Stats tracking
)
```

**Per-Instrument Access:**
```python
# Access specific instrument context
mnq = suite["MNQ"]
es = suite["ES"]

# Each context provides:
# - positions: PositionManager
# - orders: OrderManager
# - realtime: RealtimeDataManager
# - bars: BarManager
# - quotes: QuoteManager ⭐ NEW (for unrealized P&L)
# - statistics: StatisticsManager
```

**Lifecycle Methods:**
```python
await suite.start()              # Connect to platform
await suite.disconnect()         # Graceful shutdown
is_connected = suite.is_connected  # Connection status
```

**Implementation:** `src/risk_manager/sdk/suite_manager.py`

---

### 1.2 PositionManager

**Purpose:** Manage open positions and calculate P&L

**Access:** `suite[symbol].positions` or `suite.positions`

**Core Methods:**

| Method | Signature | Returns | Purpose |
|--------|-----------|---------|---------|
| `get_all_positions()` | `async () -> list[Position]` | All open positions | Query positions |
| `close_all_positions()` | `async () -> bool` | Success status | Close all positions (market orders) |
| `close_position_by_contract(contract_id)` | `async (str) -> bool` | Success status | Close specific position |
| `partially_close_position(contract_id, size)` | `async (str, int) -> bool` | Success status | Reduce position size |
| `calculate_portfolio_pnl()` | `async () -> dict` | P&L breakdown | Get total P&L |
| `calculate_position_pnl(contract_id)` | `async (str) -> dict` | P&L breakdown | P&L for specific position |

**Position Object:**
```python
@dataclass
class Position:
    id: int                    # Position ID
    account_id: int            # Account ID
    contract_id: str           # Contract identifier (e.g., "CON.F.US.MNQ.U25")
    symbol: str                # Symbol (MNQ, ES, etc.)
    size: int                  # Net size (positive=long, negative=short)
    average_price: float       # Average entry price
    unrealized_pnl: float      # Unrealized P&L (current - entry)
    realized_pnl: float        # Realized P&L (from closed portion)
    creation_timestamp: datetime
```

**Usage in Risk Manager:**
```python
# Enforcement: Close all MNQ positions
context = suite["MNQ"]
await context.positions.close_all_positions()

# P&L Tracking: Get realized P&L for daily loss rule
pnl_data = await context.positions.calculate_portfolio_pnl()
realized = pnl_data.get("realized_pnl", 0.0)
unrealized = pnl_data.get("unrealized_pnl", 0.0)
```

---

### 1.3 OrderManager

**Purpose:** Place, modify, and cancel orders

**Access:** `suite[symbol].orders` or `suite.orders`

**Core Methods:**

| Method | Signature | Returns | Purpose |
|--------|-----------|---------|---------|
| `place_market_order(contract_id, side, size)` | `async (str, int, int) -> dict` | Order details | Market order |
| `place_limit_order(contract_id, side, size, price)` | `async (str, int, int, float) -> dict` | Order details | Limit order |
| `place_stop_order(contract_id, side, size, stop_price)` | `async (str, int, int, float) -> dict` | Order details | Stop order |
| `cancel_order(order_id)` | `async (int) -> bool` | Success status | Cancel specific order |
| `cancel_all_orders()` | `async () -> bool` | Success status | Cancel all orders |
| `cancel_position_orders(contract_id)` | `async (str) -> bool` | Success status | Cancel orders for position |
| `modify_order(order_id, **kwargs)` | `async (int, dict) -> dict` | Order details | Modify existing order |
| `get_open_orders()` | `async () -> list[Order]` | Open orders | Query orders |

**Order Object:**
```python
@dataclass
class Order:
    id: int                    # Order ID
    account_id: int            # Account ID
    contract_id: str           # Contract identifier
    symbol: str                # Symbol
    side: int                  # 0=Buy/Bid, 1=Sell/Ask
    size: int                  # Order size
    order_type: int            # 1=Limit, 2=Market, 4=Stop, etc.
    status: int                # 1=Open, 2=Filled, 3=Cancelled, etc.
    limit_price: float | None  # Limit price (if applicable)
    stop_price: float | None   # Stop price (if applicable)
    fill_volume: int           # How many contracts filled
    creation_timestamp: datetime
    update_timestamp: datetime
```

**Usage in Risk Manager:**
```python
# Enforcement: Cancel all orders during lockout
await suite["MNQ"].orders.cancel_all_orders()

# Enforcement: Place market order to close position
await suite["MNQ"].orders.place_market_order(
    contract_id="CON.F.US.MNQ.U25",
    side=1,  # Sell to close long position
    size=2
)
```

---

### 1.4 QuoteManager ⭐ NEW

**Purpose:** Get real-time quotes for unrealized P&L tracking

**Access:** `suite[symbol].quotes` or `suite.realtime.quotes`

**Core Methods:**

| Method | Signature | Returns | Purpose |
|--------|-----------|---------|---------|
| `get_latest_quote()` | `async () -> Quote` | Latest quote | Current market price |
| `get_bid_ask()` | `async () -> tuple[float, float]` | (bid, ask) | Current bid/ask prices |
| `subscribe_quotes(callback)` | `async (callable) -> None` | None | Real-time quote updates |

**Quote Object:**
```python
@dataclass
class Quote:
    symbol: str                # Symbol (F.US.MNQ)
    symbol_name: str           # Display name (/MNQ)
    last_price: float          # Last traded price
    best_bid: float            # Best bid price
    best_ask: float            # Best ask price
    bid_size: int              # Size at best bid
    ask_size: int              # Size at best ask
    change: float              # Price change
    change_percent: float      # Percent change
    volume: int                # Total volume
    timestamp: datetime        # Quote timestamp
```

**Usage in Risk Manager:**
```python
# Get current market price for unrealized P&L calculation
quote = await suite["MNQ"].quotes.get_latest_quote()
current_price = quote.last_price

# Calculate unrealized P&L
# For long position: (current_price - entry_price) * size * multiplier
# For short position: (entry_price - current_price) * size * multiplier
unrealized_pnl = (current_price - entry_price) * contracts * multiplier
```

**Integration Points:**
- **RULE-004 (DailyUnrealizedLoss):** Use quotes to calculate unrealized drawdown
- **RULE-005 (MaxUnrealizedProfit):** Use quotes to calculate unrealized profit
- **P&L Tracker:** Update unrealized P&L every N seconds using latest quotes

---

### 1.5 EventBus (SDK)

**Purpose:** SDK's internal event system for real-time events

**Event Types (SDK):**

```python
from project_x_py import EventType as SDKEventType

# Connection Events
SDKEventType.CONNECTED
SDKEventType.DISCONNECTED
SDKEventType.AUTHENTICATED
SDKEventType.RECONNECTING

# Order Events
SDKEventType.ORDER_PLACED
SDKEventType.ORDER_FILLED
SDKEventType.ORDER_PARTIAL_FILL
SDKEventType.ORDER_CANCELLED
SDKEventType.ORDER_MODIFIED
SDKEventType.ORDER_REJECTED

# Position Events
SDKEventType.POSITION_OPENED
SDKEventType.POSITION_CLOSED
SDKEventType.POSITION_UPDATED
SDKEventType.POSITION_PNL_UPDATE

# Market Data Events
SDKEventType.NEW_BAR
SDKEventType.QUOTE_UPDATE  ⭐ NEW (for unrealized P&L)
SDKEventType.TRADE_TICK
SDKEventType.ORDERBOOK_UPDATE

# System Events
SDKEventType.ERROR
SDKEventType.WARNING
SDKEventType.LATENCY_WARNING
```

**Subscription Pattern:**
```python
# Subscribe to SDK events
suite.event_bus.subscribe(
    SDKEventType.ORDER_FILLED,
    callback_function
)

# Callback signature
async def callback_function(event: SDKEvent):
    # Handle event
    pass
```

**Implementation:** `src/risk_manager/sdk/event_bridge.py`

---

## 2. Integration Patterns

### 2.1 Suite Manager

**Purpose:** Manage multiple TradingSuite instances (multi-instrument support)

**File:** `src/risk_manager/sdk/suite_manager.py`

**Responsibilities:**
- Create TradingSuite for each symbol
- Health monitoring (check connection status every 30s)
- Auto-reconnection handling (SDK handles, we log)
- Graceful shutdown (disconnect all suites)

**API:**
```python
class SuiteManager:
    async def add_instrument(
        symbol: str,
        timeframes: list[str] = ["1min", "5min"],
        enable_orderbook: bool = False,
        enable_statistics: bool = True
    ) -> TradingSuite

    async def remove_instrument(symbol: str) -> None

    def get_suite(symbol: str) -> TradingSuite | None

    def get_all_suites() -> dict[str, TradingSuite]

    async def start() -> None

    async def stop() -> None

    async def get_health_status() -> dict[str, Any]
```

**Usage:**
```python
# Startup
suite_mgr = SuiteManager(event_bus)
await suite_mgr.start()

# Add instruments
mnq_suite = await suite_mgr.add_instrument("MNQ")
es_suite = await suite_mgr.add_instrument("ES")

# Get suite for specific symbol
suite = suite_mgr.get_suite("MNQ")

# Health check
status = await suite_mgr.get_health_status()
# {
#   "total_suites": 2,
#   "suites": {
#     "MNQ": {"connected": True, "instrument_id": "F.US.MNQ"},
#     "ES": {"connected": True, "instrument_id": "F.US.ES"}
#   }
# }
```

---

### 2.2 Event Bridge

**Purpose:** Convert SDK events to Risk events for rule evaluation

**File:** `src/risk_manager/sdk/event_bridge.py`

**Flow:**
```
SDK Event → EventBridge → RiskEvent → Risk EventBus → RiskEngine → Rules
```

**Event Mappings:**

| SDK Event | Risk Event | Data Extracted |
|-----------|------------|----------------|
| `TRADE_EXECUTED` | `TRADE_EXECUTED` | trade_id, price, size, pnl |
| `POSITION_OPENED` | `POSITION_OPENED` | contract_id, side, size, entry_price |
| `POSITION_CLOSED` | `POSITION_CLOSED` | contract_id, realized_pnl |
| `POSITION_UPDATED` | `POSITION_UPDATED` | contract_id, size, unrealized_pnl |
| `ORDER_PLACED` | `ORDER_PLACED` | order_id, side, size, type |
| `ORDER_FILLED` | `ORDER_FILLED` | order_id, fill_price, fill_size |
| `ORDER_CANCELLED` | `ORDER_CANCELLED` | order_id, reason |
| `ORDER_REJECTED` | `ORDER_REJECTED` | order_id, reason |
| `QUOTE_UPDATE` ⭐ | `QUOTE_UPDATED` ⭐ | symbol, last_price, bid, ask |

**API:**
```python
class EventBridge:
    async def start() -> None

    async def stop() -> None

    async def add_instrument(symbol: str, suite: TradingSuite) -> None
```

**Example Handler:**
```python
async def _on_trade_executed(self, symbol: str, sdk_event: Any) -> None:
    # Extract data from SDK event
    risk_event = RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={
            "symbol": symbol,
            "trade_id": sdk_event.trade_id,
            "price": sdk_event.price,
            "pnl": sdk_event.profit_and_loss,  # ⭐ KEY for daily loss rule
            "timestamp": sdk_event.timestamp
        }
    )

    # Publish to Risk Engine
    await self.risk_event_bus.publish(risk_event)
```

---

### 2.3 Trading Integration

**Purpose:** Execute enforcement actions via SDK

**File:** `src/risk_manager/integrations/trading.py`

**Responsibilities:**
- Connect to SDK (TradingSuite.create)
- Monitor positions (poll every 5s)
- Execute enforcement (flatten, cancel)
- Handle SDK failures (fallback to manual orders)

**API:**
```python
class TradingIntegration:
    async def connect() -> None

    async def disconnect() -> None

    async def start() -> None

    async def flatten_position(symbol: str) -> None

    async def flatten_all() -> None

    def get_stats() -> dict[str, Any]
```

**Enforcement Flow:**
```
RiskEngine.flatten_all_positions()
    ↓
TradingIntegration.flatten_all()
    ↓
For each symbol:
    TradingIntegration.flatten_position(symbol)
        ↓
    suite[symbol].positions.close_all_positions()  ⭐ SDK CALL
        ↓
    TopstepX REST API: POST /api/Position/closeContract
        ↓
    ✅ Positions closed on platform
```

**Fallback Strategy:**
```python
async def flatten_position(self, symbol: str) -> None:
    context = self.suite[symbol]

    try:
        # Primary: Use SDK's close method
        await context.positions.close_all_positions()

    except Exception as e:
        logger.error(f"SDK close failed: {e}")

        # Fallback: Manual market orders
        positions = await context.positions.get_all_positions()
        for pos in positions:
            side = 1 if pos.size > 0 else 0  # Opposite side
            await context.orders.place_market_order(
                contract_id=pos.contract_id,
                side=side,
                size=abs(pos.size)
            )
```

---

## 3. Quote Data Integration ⭐ NEW

### 3.1 Purpose

Calculate **unrealized P&L** for open positions by comparing current market price to entry price.

### 3.2 Quote Sources

**From SDK:**
```python
# Method 1: Get latest quote
quote = await suite["MNQ"].quotes.get_latest_quote()
current_price = quote.last_price

# Method 2: Subscribe to real-time quotes
async def on_quote_update(quote_event):
    current_price = quote_event.last_price
    # Update unrealized P&L

await suite["MNQ"].realtime.subscribe_quotes(on_quote_update)
```

**From SignalR (via SDK EventBus):**
```python
# SDK automatically subscribes to quote updates
suite.event_bus.subscribe(
    SDKEventType.QUOTE_UPDATE,
    handle_quote_update
)
```

### 3.3 Unrealized P&L Calculation

**Formula:**
```python
# For LONG position:
unrealized_pnl = (current_price - entry_price) * contracts * multiplier

# For SHORT position:
unrealized_pnl = (entry_price - current_price) * contracts * multiplier

# Example: MNQ (Micro Nasdaq)
# - Long 2 contracts at 21000
# - Current price: 21050
# - Multiplier: $2 per point
unrealized_pnl = (21050 - 21000) * 2 * 2 = $200
```

**Contract Multipliers (TopstepX):**
- MNQ (Micro Nasdaq): $2 per point
- ES (E-mini S&P): $50 per point
- NQ (Nasdaq): $20 per point
- RTY (Russell): $50 per point
- YM (Dow): $5 per point

### 3.4 Update Frequency

**Real-time Updates:**
- SDK publishes QUOTE_UPDATE events on every price change
- High frequency (millisecond latency)
- Use for immediate enforcement (RULE-004, RULE-005)

**Polling Updates:**
- Alternative: Poll quotes every N seconds (e.g., 5s)
- Lower frequency, less resource intensive
- Use for monitoring dashboards

**Implementation:**
```python
# Real-time (event-driven)
async def _on_quote_update(self, symbol: str, quote_event: Any) -> None:
    current_price = quote_event.last_price

    # Get open positions for this symbol
    positions = await self.suite[symbol].positions.get_all_positions()

    for pos in positions:
        # Calculate unrealized P&L
        if pos.size > 0:  # Long
            unrealized = (current_price - pos.average_price) * pos.size * multiplier
        else:  # Short
            unrealized = (pos.average_price - current_price) * abs(pos.size) * multiplier

        # Update PnL tracker
        await self.pnl_tracker.update_unrealized_pnl(pos.account_id, unrealized)

# Polling (scheduled)
async def _poll_quotes(self):
    while self.running:
        for symbol in self.instruments:
            quote = await self.suite[symbol].quotes.get_latest_quote()
            # Update unrealized P&L
            await self._update_unrealized_pnl(symbol, quote.last_price)

        await asyncio.sleep(5)  # Poll every 5 seconds
```

### 3.5 Integration with Rules

**RULE-004: DailyUnrealizedLoss**
```python
# Check if unrealized drawdown exceeds limit
daily_unrealized = await pnl_tracker.get_unrealized_pnl(account_id)

if daily_unrealized <= config.daily_unrealized_loss_limit:
    # Violation detected
    return {
        "action": "close_positions",
        "reason": f"Daily unrealized loss limit hit: {daily_unrealized}"
    }
```

**RULE-005: MaxUnrealizedProfit**
```python
# Check if unrealized profit exceeds target (close to lock in)
daily_unrealized = await pnl_tracker.get_unrealized_pnl(account_id)

if daily_unrealized >= config.max_unrealized_profit_target:
    # Target hit - close positions to lock in profit
    return {
        "action": "close_positions",
        "reason": f"Unrealized profit target hit: {daily_unrealized}"
    }
```

---

## 4. Configuration

### 4.1 Admin Configuration

**Location:** Risk config YAML (e.g., `config/risk_config.yaml`)

```yaml
# SDK Connection
api_credentials:
  # Set via environment variables (NOT in config file!)
  # TOPSTEPX_API_KEY=xxx
  # TOPSTEPX_USERNAME=xxx

# Account Monitoring
accounts:
  - account_id: 123
    account_name: "PRAC-V2-126244"
    instruments:
      - symbol: "MNQ"
        multiplier: 2.0  # $2 per point
      - symbol: "ES"
        multiplier: 50.0  # $50 per point

# Quote Data Settings ⭐ NEW
quote_settings:
  update_mode: "realtime"  # or "polling"
  polling_interval_seconds: 5
  enable_quote_caching: true
  cache_ttl_seconds: 1
```

### 4.2 Environment Variables

**Required:**
```bash
# TopstepX API credentials
TOPSTEPX_API_KEY=your_api_key_here
TOPSTEPX_USERNAME=your_username_here

# Optional: Override SDK defaults
TOPSTEPX_API_URL=https://api.topstepx.com
TOPSTEPX_WS_URL=wss://rtc.topstepx.com
```

**Security:**
- ⚠️ Never commit credentials to git
- ⚠️ Use `.env` file (in `.gitignore`)
- ⚠️ SDK automatically reads from environment

---

## 5. SDK vs Manual API Comparison

### 5.1 Complexity Reduction

| Task | Manual API | SDK | Reduction |
|------|-----------|-----|-----------|
| Authentication | 50 lines | 0 lines (auto) | 100% |
| WebSocket setup | 100 lines | 0 lines (auto) | 100% |
| Event subscriptions | 150 lines | 10 lines | 93% |
| Position management | 200 lines | 20 lines | 90% |
| Order management | 250 lines | 20 lines | 92% |
| Quote data | 100 lines ⭐ | 5 lines ⭐ | 95% |
| Reconnection logic | 150 lines | 0 lines (auto) | 100% |
| Error handling | 200 lines | 30 lines | 85% |
| **Total** | **~1200 lines** | **~85 lines** | **~93%** |

### 5.2 Before SDK (Original Specs)

**Manual Implementation Required:**
```python
# 1. Authentication
response = requests.post(
    "https://api.topstepx.com/api/Auth/loginKey",
    json={"userName": username, "apiKey": api_key}
)
token = response.json()["token"]

# 2. SignalR WebSocket
connection = HubConnectionBuilder() \
    .with_url(f"https://rtc.topstepx.com/hubs/user?access_token={token}") \
    .with_automatic_reconnect() \
    .build()

connection.on("GatewayUserTrade", handle_trade)
connection.start()

# 3. Close positions
response = requests.post(
    "https://api.topstepx.com/api/Position/searchOpen",
    headers={"Authorization": f"Bearer {token}"},
    json={"accountId": account_id}
)

for pos in response.json()["positions"]:
    requests.post(
        "https://api.topstepx.com/api/Position/closeContract",
        headers={"Authorization": f"Bearer {token}"},
        json={"accountId": account_id, "contractId": pos["contractId"]}
    )

# 4. Get quotes for unrealized P&L ⭐
response = requests.post(
    "https://api.topstepx.com/api/Market/getQuote",
    headers={"Authorization": f"Bearer {token}"},
    json={"symbolId": "F.US.MNQ"}
)
current_price = response.json()["lastPrice"]

# Result: ~1200 lines of boilerplate
```

### 5.3 After SDK (Current Implementation)

**SDK-First Implementation:**
```python
# 1. All authentication handled automatically
suite = await TradingSuite.create(instruments=["MNQ"])

# 2. All WebSocket handling automatic
# SDK subscribes to events internally

# 3. Close positions (single call)
await suite["MNQ"].positions.close_all_positions()

# 4. Get quotes (single call) ⭐
quote = await suite["MNQ"].quotes.get_latest_quote()
current_price = quote.last_price

# Result: ~85 lines total
```

---

## 6. Error Handling

### 6.1 SDK Connection Failures

**Auto-Reconnection:**
- SDK handles reconnection automatically
- No manual retry logic needed
- We log events for visibility

**Health Monitoring:**
```python
async def _health_check_loop(self):
    while self.running:
        for symbol, suite in self.suites.items():
            if not suite.realtime.is_connected:
                logger.warning(f"Suite for {symbol} disconnected")
                # SDK auto-reconnects, we just log

        await asyncio.sleep(30)
```

### 6.2 API Call Failures

**Primary + Fallback Strategy:**
```python
try:
    # Primary: Use SDK method
    await suite.positions.close_all_positions()

except Exception as e:
    logger.error(f"SDK method failed: {e}")

    # Fallback: Manual approach
    positions = await suite.positions.get_all_positions()
    for pos in positions:
        await suite.orders.place_market_order(...)
```

### 6.3 Quote Data Failures ⭐

**Stale Quote Handling:**
```python
quote = await suite["MNQ"].quotes.get_latest_quote()

# Check if quote is stale
age = datetime.now() - quote.timestamp
if age.total_seconds() > 5:
    logger.warning(f"Stale quote for MNQ (age: {age.total_seconds()}s)")
    # Use last known good price or skip unrealized P&L update
```

**Missing Quote Handling:**
```python
try:
    quote = await suite["MNQ"].quotes.get_latest_quote()
    current_price = quote.last_price

except Exception as e:
    logger.error(f"Failed to get quote: {e}")

    # Fallback: Use position's current unrealized P&L from SDK
    # SDK calculates unrealized P&L internally
    pos = await suite["MNQ"].positions.get_all_positions()[0]
    unrealized = pos.unrealized_pnl  # SDK provides this
```

---

## 7. Testing Strategy

### 7.1 Unit Tests (Mocked SDK)

**Mock TradingSuite:**
```python
@pytest.fixture
async def mock_suite():
    suite = AsyncMock(spec=TradingSuite)
    suite["MNQ"] = AsyncMock()
    suite["MNQ"].positions.close_all_positions = AsyncMock()
    suite["MNQ"].quotes.get_latest_quote = AsyncMock(return_value=mock_quote)
    return suite

async def test_flatten_position(mock_suite):
    integration = TradingIntegration(["MNQ"], config, event_bus)
    integration.suite = mock_suite

    await integration.flatten_position("MNQ")

    mock_suite["MNQ"].positions.close_all_positions.assert_called_once()
```

### 7.2 Integration Tests (Real SDK)

**Requires:**
- Valid TopstepX credentials
- Live or practice account
- Real SDK connection

**Example:**
```python
@pytest.mark.integration
async def test_sdk_connection():
    suite = await TradingSuite.create(instruments=["MNQ"])
    assert suite.is_connected

    # Test position query
    positions = await suite["MNQ"].positions.get_all_positions()
    assert isinstance(positions, list)

    # Test quote query ⭐
    quote = await suite["MNQ"].quotes.get_latest_quote()
    assert quote.last_price > 0

    await suite.disconnect()
```

---

## 8. Implementation Checklist

### Core SDK Integration
- [x] SuiteManager - Multi-instrument lifecycle
- [x] EventBridge - SDK to Risk event conversion
- [x] TradingIntegration - Enforcement via SDK
- [x] Health monitoring
- [x] Auto-reconnection handling
- [x] Graceful shutdown

### Quote Data Integration ⭐ NEW
- [ ] Quote subscription in EventBridge
- [ ] QuoteManager wrapper (if needed)
- [ ] Unrealized P&L calculation
- [ ] Real-time quote event handling
- [ ] Polling fallback implementation
- [ ] Contract multiplier configuration
- [ ] Stale quote detection

### Event Flow
- [x] Trade events → Risk engine
- [x] Position events → Risk engine
- [x] Order events → Risk engine
- [ ] Quote events → Risk engine ⭐
- [x] Event bus pub/sub system

### Enforcement
- [x] Flatten position (single symbol)
- [x] Flatten all positions (all symbols)
- [x] Close via SDK method
- [x] Fallback to manual orders

---

## 9. References

**SDK Documentation:**
- Project-X-Py SDK: [GitHub](https://github.com/projectx/project-x-py)
- TopstepX API Docs: [api.topstepx.com/docs](https://api.topstepx.com/docs)

**Implementation Files:**
- `src/risk_manager/sdk/suite_manager.py` - TradingSuite lifecycle
- `src/risk_manager/sdk/event_bridge.py` - SDK event conversion
- `src/risk_manager/integrations/trading.py` - Enforcement actions
- `src/risk_manager/core/events.py` - Risk event types

**Wave 1 Analysis:**
- `docs/analysis/wave1-feature-inventory/02-SDK-INTEGRATION-INVENTORY.md`

**Wave 2 Gaps:**
- `docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md`

---

**Document Status:** Complete
**Last Updated:** 2025-10-25
**Next Review:** When SDK version updates or new quote features added
