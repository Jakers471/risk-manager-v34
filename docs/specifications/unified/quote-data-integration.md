# Quote Data Integration Specification ⭐ NEW

**Document ID:** UNIFIED-SDK-003
**Created:** 2025-10-25
**Status:** New Feature - For Unrealized P&L Tracking
**Dependencies:**
- SDK Integration (UNIFIED-SDK-001)
- Event Handling (UNIFIED-SDK-002)

---

## Executive Summary

Quote data integration enables **real-time unrealized P&L tracking** by providing current market prices for open positions. This is critical for RULE-004 (DailyUnrealizedLoss) and RULE-005 (MaxUnrealizedProfit).

### Problem Statement

**Current Gap:**
- ✅ We can track **realized P&L** from TRADE_EXECUTED events (contains `profit_and_loss` field)
- ❌ We **cannot** track **unrealized P&L** accurately without current market prices
- ❌ RULE-004 (daily unrealized loss) is blocked
- ❌ RULE-005 (max unrealized profit) is blocked

**Solution:**
- ✅ Subscribe to real-time quote updates from SDK
- ✅ Calculate unrealized P&L: `(current_price - entry_price) * contracts * multiplier`
- ✅ Update P&L tracker with unrealized P&L
- ✅ Enable RULE-004 and RULE-005

---

## 1. Quote Data Sources

### 1.1 SDK QuoteManager

**Access:** `suite[symbol].quotes` or `suite.realtime.quotes`

**Methods:**

```python
from project_x_py import TradingSuite

suite = await TradingSuite.create(instruments=["MNQ"])
quote_manager = suite["MNQ"].quotes

# Method 1: Get latest quote (snapshot)
quote = await quote_manager.get_latest_quote()
current_price = quote.last_price

# Method 2: Get bid/ask spread
bid, ask = await quote_manager.get_bid_ask()
mid_price = (bid + ask) / 2

# Method 3: Subscribe to real-time updates
async def on_quote_update(quote_event):
    print(f"Price: {quote_event.last_price}")

await quote_manager.subscribe_quotes(on_quote_update)
```

### 1.2 SDK EventBus

**Quote Update Events:**

```python
from project_x_py import EventType as SDKEventType

# Subscribe to quote updates via SDK EventBus
await suite.on(EventType.QUOTE_UPDATE, handle_quote_update)

async def handle_quote_update(event):
    symbol = event.symbol
    last_price = event.last_price
    bid = event.best_bid
    ask = event.best_ask
```

### 1.3 SignalR WebSocket (via SDK)

**Raw SignalR Event (SDK handles internally):**

```json
{
  "event": "GatewayQuote",
  "data": {
    "symbol": "F.US.MNQ",
    "symbolName": "/MNQ",
    "lastPrice": 21000.25,
    "bestBid": 21000.00,
    "bestAsk": 21000.50,
    "change": 25.50,
    "changePercent": 0.14,
    "volume": 12000,
    "timestamp": "2025-10-25T13:45:00Z"
  }
}
```

---

## 2. Quote Object Structure

### 2.1 SDK Quote Object

```python
@dataclass
class Quote:
    """Quote data from SDK."""

    symbol: str                # Symbol ID (e.g., "F.US.MNQ")
    symbol_name: str           # Display name (e.g., "/MNQ")
    last_price: float          # Last traded price
    best_bid: float            # Best bid price
    best_ask: float            # Best ask price
    bid_size: int              # Size at best bid
    ask_size: int              # Size at best ask
    change: float              # Price change (vs previous close)
    change_percent: float      # Percent change
    volume: int                # Total volume
    timestamp: datetime        # Quote timestamp

    # Optional fields
    high: float | None         # Session high
    low: float | None          # Session low
    open: float | None         # Session open
```

### 2.2 Risk Event Quote Data

**QUOTE_UPDATED Event:**

```python
RiskEvent(
    event_type=EventType.QUOTE_UPDATED,
    data={
        "symbol": "MNQ",
        "last_price": 21000.25,
        "bid": 21000.00,
        "ask": 21000.50,
        "bid_size": 10,
        "ask_size": 15,
        "mid_price": 21000.25,  # (bid + ask) / 2
        "spread": 0.50,         # ask - bid
        "timestamp": datetime(...),
        "age_ms": 50            # Age of quote in milliseconds
    }
)
```

---

## 3. Unrealized P&L Calculation

### 3.1 Formula

**For Long Position:**
```python
unrealized_pnl = (current_price - entry_price) * contracts * multiplier

# Example: Long 2 MNQ at 21000, current price 21050
unrealized_pnl = (21050 - 21000) * 2 * 2 = $200
```

**For Short Position:**
```python
unrealized_pnl = (entry_price - current_price) * contracts * multiplier

# Example: Short 2 MNQ at 21000, current price 20950
unrealized_pnl = (21000 - 20950) * 2 * 2 = $200
```

### 3.2 Contract Multipliers

**TopstepX Futures Multipliers:**

| Symbol | Name | Multiplier | Tick Size | Tick Value |
|--------|------|------------|-----------|------------|
| MNQ | Micro Nasdaq | $2 | 0.25 | $0.50 |
| ES | E-mini S&P | $50 | 0.25 | $12.50 |
| NQ | Nasdaq | $20 | 0.25 | $5.00 |
| RTY | Russell 2000 | $50 | 0.10 | $5.00 |
| YM | Dow | $5 | 1.00 | $5.00 |
| CL | Crude Oil | $1000 | 0.01 | $10.00 |
| GC | Gold | $100 | 0.10 | $10.00 |

**Configuration:**

```yaml
# config/instruments.yaml
instruments:
  - symbol: "MNQ"
    name: "Micro Nasdaq"
    multiplier: 2.0
    tick_size: 0.25
    tick_value: 0.50

  - symbol: "ES"
    name: "E-mini S&P"
    multiplier: 50.0
    tick_size: 0.25
    tick_value: 12.50

  - symbol: "NQ"
    name: "Nasdaq"
    multiplier: 20.0
    tick_size: 0.25
    tick_value: 5.00
```

### 3.3 Implementation

**Calculate Unrealized P&L:**

```python
class UnrealizedPnLCalculator:
    """Calculate unrealized P&L for open positions."""

    def __init__(self, instrument_config: dict):
        """
        Args:
            instrument_config: Mapping of symbol → multiplier
                e.g., {"MNQ": 2.0, "ES": 50.0}
        """
        self.multipliers = instrument_config

    def calculate(
        self,
        symbol: str,
        size: int,
        entry_price: float,
        current_price: float
    ) -> float:
        """
        Calculate unrealized P&L.

        Args:
            symbol: Instrument symbol (e.g., "MNQ")
            size: Position size (positive=long, negative=short)
            entry_price: Average entry price
            current_price: Current market price

        Returns:
            Unrealized P&L in dollars
        """
        multiplier = self.multipliers.get(symbol, 1.0)

        if size > 0:  # Long position
            pnl = (current_price - entry_price) * size * multiplier
        elif size < 0:  # Short position
            pnl = (entry_price - current_price) * abs(size) * multiplier
        else:  # No position
            pnl = 0.0

        return pnl

# Usage
calculator = UnrealizedPnLCalculator({"MNQ": 2.0, "ES": 50.0})

# Long 2 MNQ at 21000, current 21050
pnl = calculator.calculate("MNQ", 2, 21000, 21050)
# → $200

# Short 1 ES at 5800, current 5790
pnl = calculator.calculate("ES", -1, 5800, 5790)
# → $500
```

---

## 4. Quote Data Flow

### 4.1 Real-Time Flow (Event-Driven)

```
TopstepX Platform
│ Market price changes: MNQ 21000 → 21050
▼
SignalR WebSocket: GatewayQuote event
│
▼
Project-X-Py SDK
│ RealtimeDataManager receives event
│ Publishes QUOTE_UPDATE to SDK EventBus
▼
EventBridge._on_quote_update()
│ Subscribes to SDK QUOTE_UPDATE
│ Converts to RiskEvent(QUOTE_UPDATED)
▼
Risk EventBus
│ Publishes QUOTE_UPDATED to subscribers
▼
┌───────────────────────────────────────┐
│ Subscribers                           │
├─> RULE-004: DailyUnrealizedLoss      │
│   └─ Recalculate unrealized P&L      │
│   └─ Check if drawdown limit hit     │
│                                       │
├─> RULE-005: MaxUnrealizedProfit      │
│   └─ Recalculate unrealized P&L      │
│   └─ Check if profit target hit      │
│                                       │
└─> PnL Tracker                        │
    └─ Update unrealized P&L state     │
    └─ Store in database               │
└───────────────────────────────────────┘
```

### 4.2 Polling Flow (Scheduled)

```
Background Task (runs every 5 seconds)
│
├─> For each symbol:
│   ├─> quote = await suite[symbol].quotes.get_latest_quote()
│   ├─> positions = await suite[symbol].positions.get_all_positions()
│   │
│   └─> For each position:
│       ├─> Calculate unrealized P&L
│       └─> Update PnL tracker
│
└─> await asyncio.sleep(5)
```

### 4.3 Hybrid Approach (Recommended)

**Use both real-time + polling:**

```python
class QuoteDataManager:
    """Manage quote data for unrealized P&L tracking."""

    def __init__(self, suite_manager, event_bus, config):
        self.suite_manager = suite_manager
        self.event_bus = event_bus
        self.config = config
        self.calculator = UnrealizedPnLCalculator(config.multipliers)
        self.running = False

    async def start(self):
        """Start quote data tracking."""
        self.running = True

        # Start real-time event subscription
        await self._subscribe_to_quotes()

        # Start polling as backup
        asyncio.create_task(self._poll_quotes())

    async def _subscribe_to_quotes(self):
        """Subscribe to real-time quote updates."""
        for symbol, suite in self.suite_manager.get_all_suites().items():
            await suite.on(
                EventType.QUOTE_UPDATE,
                lambda event: self._on_quote_update(symbol, event)
            )

    async def _on_quote_update(self, symbol: str, sdk_event):
        """Handle real-time quote update."""
        current_price = sdk_event.last_price

        # Get open positions
        suite = self.suite_manager.get_suite(symbol)
        positions = await suite.positions.get_all_positions()

        # Calculate unrealized P&L for each position
        for pos in positions:
            unrealized = self.calculator.calculate(
                symbol,
                pos.size,
                pos.average_price,
                current_price
            )

            # Publish QUOTE_UPDATED event
            event = RiskEvent(
                event_type=EventType.QUOTE_UPDATED,
                data={
                    "symbol": symbol,
                    "position_id": pos.id,
                    "current_price": current_price,
                    "unrealized_pnl": unrealized
                }
            )

            await self.event_bus.publish(event)

    async def _poll_quotes(self):
        """Poll quotes as backup (every 5s)."""
        while self.running:
            try:
                for symbol, suite in self.suite_manager.get_all_suites().items():
                    quote = await suite.quotes.get_latest_quote()
                    await self._on_quote_update(symbol, quote)

                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error polling quotes: {e}")
                await asyncio.sleep(10)
```

---

## 5. EventBridge Integration

### 5.1 Subscribe to Quote Updates

**Add to EventBridge:**

```python
# src/risk_manager/sdk/event_bridge.py

async def _subscribe_to_suite(self, symbol: str, suite: TradingSuite) -> None:
    """Subscribe to events from a specific TradingSuite."""    # ... existing subscriptions ...

    # ⭐ NEW: Subscribe to quote updates
    await suite.on(
        EventType.QUOTE_UPDATE,
        lambda event: self._on_quote_update(symbol, event)
    )

    logger.success(f"Subscribed to quote updates for {symbol}")
```

### 5.2 Handle Quote Updates

**Add handler method:**

```python
async def _on_quote_update(self, symbol: str, sdk_event: Any) -> None:
    """
    Handle quote update event from SDK.

    Args:
        symbol: Instrument symbol
        sdk_event: SDK quote event
    """
    try:
        # Extract quote data
        risk_event = RiskEvent(
            type=EventType.QUOTE_UPDATED,
            data={
                "symbol": symbol,
                "last_price": getattr(sdk_event, "last_price", None),
                "bid": getattr(sdk_event, "best_bid", None),
                "ask": getattr(sdk_event, "best_ask", None),
                "bid_size": getattr(sdk_event, "bid_size", None),
                "ask_size": getattr(sdk_event, "ask_size", None),
                "mid_price": (
                    getattr(sdk_event, "best_bid", 0) +
                    getattr(sdk_event, "best_ask", 0)
                ) / 2,
                "spread": (
                    getattr(sdk_event, "best_ask", 0) -
                    getattr(sdk_event, "best_bid", 0)
                ),
                "timestamp": getattr(sdk_event, "timestamp", None),
                "sdk_event": sdk_event,
            }
        )

        # Publish to Risk EventBus
        await self.risk_event_bus.publish(risk_event)
        logger.debug(f"Bridged QUOTE_UPDATED event for {symbol}")

    except Exception as e:
        logger.error(f"Error bridging quote update event: {e}")
```

---

## 6. PnL Tracker Integration

### 6.1 Update Unrealized P&L

**Add method to PnLTracker:**

```python
# src/risk_manager/state/pnl_tracker.py

async def update_unrealized_pnl(
    self,
    account_id: str,
    symbol: str,
    unrealized_pnl: float
) -> None:
    """
    Update unrealized P&L for a symbol.

    Args:
        account_id: Account ID
        symbol: Instrument symbol
        unrealized_pnl: Current unrealized P&L
    """
    date_key = datetime.now().strftime("%Y-%m-%d")

    # Store per-symbol unrealized P&L
    if account_id not in self.state:
        self.state[account_id] = {}

    if date_key not in self.state[account_id]:
        self.state[account_id][date_key] = {
            "realized": 0.0,
            "unrealized": {}  # symbol → unrealized P&L
        }

    self.state[account_id][date_key]["unrealized"][symbol] = unrealized_pnl

    # Persist to database
    await self._save_to_db(account_id, date_key)

async def get_unrealized_pnl(self, account_id: str) -> float:
    """
    Get total unrealized P&L across all symbols.

    Args:
        account_id: Account ID

    Returns:
        Total unrealized P&L
    """
    date_key = datetime.now().strftime("%Y-%m-%d")

    if account_id not in self.state:
        return 0.0

    if date_key not in self.state[account_id]:
        return 0.0

    # Sum unrealized P&L across all symbols
    unrealized_dict = self.state[account_id][date_key].get("unrealized", {})
    return sum(unrealized_dict.values())

async def get_unrealized_pnl_by_symbol(
    self,
    account_id: str,
    symbol: str
) -> float:
    """
    Get unrealized P&L for specific symbol.

    Args:
        account_id: Account ID
        symbol: Instrument symbol

    Returns:
        Unrealized P&L for symbol
    """
    date_key = datetime.now().strftime("%Y-%m-%d")

    if account_id not in self.state:
        return 0.0

    if date_key not in self.state[account_id]:
        return 0.0

    unrealized_dict = self.state[account_id][date_key].get("unrealized", {})
    return unrealized_dict.get(symbol, 0.0)
```

---

## 7. Rule Integration

### 7.1 RULE-004: DailyUnrealizedLoss

**Purpose:** Close positions if unrealized drawdown exceeds limit

**Implementation:**

```python
# src/risk_manager/rules/daily_unrealized_loss.py

class DailyUnrealizedLossRule(BaseRule):
    """RULE-004: Daily unrealized loss limit."""

    def __init__(self, config: RiskConfig, pnl_tracker: PnLTracker):
        super().__init__("DailyUnrealizedLoss", "RULE-004")
        self.config = config
        self.pnl_tracker = pnl_tracker
        self.calculator = UnrealizedPnLCalculator(config.instrument_multipliers)

    async def evaluate(
        self,
        event: RiskEvent,
        engine: RiskEngine
    ) -> dict | None:
        """
        Evaluate unrealized loss limit.

        Triggered by:
        - QUOTE_UPDATED events (real-time)
        - POSITION_UPDATED events (polling)
        """
        # Listen for quote or position updates
        if event.event_type not in [
            EventType.QUOTE_UPDATED,
            EventType.POSITION_UPDATED
        ]:
            return None  # Ignore other events

        account_id = event.data.get("account_id")
        symbol = event.data.get("symbol")

        # Get current price
        if event.event_type == EventType.QUOTE_UPDATED:
            current_price = event.data.get("last_price")
        else:
            # Get quote for this symbol
            quote = await engine.trading_integration.suite[symbol].quotes.get_latest_quote()
            current_price = quote.last_price

        # Get open positions
        positions = await engine.trading_integration.suite[symbol].positions.get_all_positions()

        # Calculate total unrealized P&L
        total_unrealized = 0.0
        for pos in positions:
            unrealized = self.calculator.calculate(
                symbol,
                pos.size,
                pos.average_price,
                current_price
            )
            total_unrealized += unrealized

            # Update PnL tracker
            await self.pnl_tracker.update_unrealized_pnl(
                account_id,
                symbol,
                unrealized
            )

        # Check limit
        limit = self.config.daily_unrealized_loss_limit

        if total_unrealized <= limit:
            return {
                "action": "close_positions",
                "reason": f"Daily unrealized loss limit hit: ${total_unrealized:.2f} (limit: ${limit:.2f})",
                "account_id": account_id,
                "symbol": symbol,
                "unrealized_pnl": total_unrealized
            }

        return None  # OK
```

### 7.2 RULE-005: MaxUnrealizedProfit

**Purpose:** Close positions when profit target hit (lock in profit)

**Implementation:**

```python
# src/risk_manager/rules/max_unrealized_profit.py

class MaxUnrealizedProfitRule(BaseRule):
    """RULE-005: Maximum unrealized profit target."""

    def __init__(self, config: RiskConfig, pnl_tracker: PnLTracker):
        super().__init__("MaxUnrealizedProfit", "RULE-005")
        self.config = config
        self.pnl_tracker = pnl_tracker
        self.calculator = UnrealizedPnLCalculator(config.instrument_multipliers)

    async def evaluate(
        self,
        event: RiskEvent,
        engine: RiskEngine
    ) -> dict | None:
        """
        Evaluate unrealized profit target.

        Triggered by:
        - QUOTE_UPDATED events (real-time)
        - POSITION_UPDATED events (polling)
        """
        # Same logic as RULE-004 but check upper limit
        if event.event_type not in [
            EventType.QUOTE_UPDATED,
            EventType.POSITION_UPDATED
        ]:
            return None

        account_id = event.data.get("account_id")
        symbol = event.data.get("symbol")

        # Get current price
        if event.event_type == EventType.QUOTE_UPDATED:
            current_price = event.data.get("last_price")
        else:
            quote = await engine.trading_integration.suite[symbol].quotes.get_latest_quote()
            current_price = quote.last_price

        # Get open positions
        positions = await engine.trading_integration.suite[symbol].positions.get_all_positions()

        # Calculate total unrealized P&L
        total_unrealized = 0.0
        for pos in positions:
            unrealized = self.calculator.calculate(
                symbol,
                pos.size,
                pos.average_price,
                current_price
            )
            total_unrealized += unrealized

            await self.pnl_tracker.update_unrealized_pnl(
                account_id,
                symbol,
                unrealized
            )

        # Check target
        target = self.config.max_unrealized_profit_target

        if total_unrealized >= target:
            return {
                "action": "close_positions",
                "reason": f"Unrealized profit target hit: ${total_unrealized:.2f} (target: ${target:.2f})",
                "account_id": account_id,
                "symbol": symbol,
                "unrealized_pnl": total_unrealized
            }

        return None  # OK
```

---

## 8. Quote Event Throttling

### 8.1 Problem

**Quote updates fire very frequently:**
- 10-100+ updates per second during active trading
- Processing every update is resource-intensive
- Rules don't need millisecond precision

### 8.2 Solution: Throttle

**Process at most 1 update per second per symbol:**

```python
import time
from asyncio import Lock

class QuoteThrottle:
    """Throttle quote updates to reduce processing load."""

    def __init__(self, interval_seconds: float = 1.0):
        """
        Args:
            interval_seconds: Minimum time between processed updates
        """
        self.interval = interval_seconds
        self.last_processed: dict[str, float] = {}
        self.lock = Lock()

    async def should_process(self, symbol: str) -> bool:
        """
        Check if quote update should be processed.

        Args:
            symbol: Instrument symbol

        Returns:
            True if update should be processed
        """
        async with self.lock:
            now = time.time()
            last = self.last_processed.get(symbol, 0)

            if now - last >= self.interval:
                self.last_processed[symbol] = now
                return True

            return False

# Usage in EventBridge
throttle = QuoteThrottle(interval_seconds=1.0)

async def _on_quote_update(self, symbol: str, sdk_event: Any) -> None:
    # Check throttle
    if not await throttle.should_process(symbol):
        return  # Skip this update

    # Process quote
    risk_event = RiskEvent(...)
    await self.risk_event_bus.publish(risk_event)
```

### 8.3 Alternative: Debounce

**Wait for quiet period before processing:**

```python
import asyncio

class QuoteDebounce:
    """Debounce quote updates."""

    def __init__(self, wait_seconds: float = 0.5):
        self.wait = wait_seconds
        self.timers: dict[str, asyncio.Task] = {}
        self.pending: dict[str, Any] = {}

    async def debounce(
        self,
        symbol: str,
        event: Any,
        callback: Callable
    ) -> None:
        """
        Debounce quote event.

        Args:
            symbol: Instrument symbol
            event: Quote event
            callback: Function to call after quiet period
        """
        # Cancel existing timer
        if symbol in self.timers:
            self.timers[symbol].cancel()

        # Store pending event
        self.pending[symbol] = event

        # Start new timer
        async def delayed_callback():
            await asyncio.sleep(self.wait)
            await callback(symbol, self.pending[symbol])
            del self.pending[symbol]
            del self.timers[symbol]

        self.timers[symbol] = asyncio.create_task(delayed_callback())

# Usage
debounce = QuoteDebounce(wait_seconds=0.5)

async def _on_quote_update(self, symbol: str, sdk_event: Any) -> None:
    # Debounce
    await debounce.debounce(
        symbol,
        sdk_event,
        self._process_quote_update
    )

async def _process_quote_update(self, symbol: str, sdk_event: Any) -> None:
    # Process quote (only called after 0.5s of quiet)
    risk_event = RiskEvent(...)
    await self.risk_event_bus.publish(risk_event)
```

---

## 9. Stale Quote Detection

### 9.1 Problem

Quotes can become stale if:
- Connection issues
- Market closed
- Low liquidity instrument

### 9.2 Solution

**Check quote age:**

```python
from datetime import datetime, timedelta

class StaleQuoteDetector:
    """Detect stale quotes."""

    def __init__(self, max_age_seconds: float = 5.0):
        """
        Args:
            max_age_seconds: Maximum quote age before considered stale
        """
        self.max_age = timedelta(seconds=max_age_seconds)

    def is_stale(self, quote: Quote) -> bool:
        """
        Check if quote is stale.

        Args:
            quote: Quote object

        Returns:
            True if quote is stale
        """
        if quote.timestamp is None:
            return True

        age = datetime.now() - quote.timestamp
        return age > self.max_age

    def get_age_seconds(self, quote: Quote) -> float:
        """Get quote age in seconds."""
        if quote.timestamp is None:
            return float('inf')

        age = datetime.now() - quote.timestamp
        return age.total_seconds()

# Usage
detector = StaleQuoteDetector(max_age_seconds=5.0)

quote = await suite["MNQ"].quotes.get_latest_quote()

if detector.is_stale(quote):
    logger.warning(f"Stale quote for MNQ (age: {detector.get_age_seconds(quote):.1f}s)")
    # Skip unrealized P&L calculation or use fallback
else:
    # Process quote normally
    current_price = quote.last_price
```

### 9.3 Fallback Strategy

**If quote is stale:**

1. **Use SDK's unrealized P&L** (SDK calculates internally)
2. **Use last known good price**
3. **Skip this update** (wait for fresh quote)

```python
async def get_current_price(self, symbol: str) -> float | None:
    """
    Get current price with fallback.

    Returns:
        Current price or None if unavailable
    """
    try:
        # Primary: Get latest quote
        quote = await self.suite[symbol].quotes.get_latest_quote()

        # Check if stale
        if self.detector.is_stale(quote):
            logger.warning(f"Stale quote for {symbol}, using SDK P&L")

            # Fallback: Use SDK's unrealized P&L
            positions = await self.suite[symbol].positions.get_all_positions()
            if positions:
                # SDK calculates unrealized P&L internally
                return None  # Signal to use SDK's value

        return quote.last_price

    except Exception as e:
        logger.error(f"Failed to get quote for {symbol}: {e}")
        return None
```

---

## 10. Configuration

### 10.1 Quote Settings

**Location:** `config/quote_settings.yaml`

```yaml
quote_data:
  # Update mode: "realtime" (event-driven) or "polling" (scheduled)
  update_mode: "realtime"

  # Polling interval (if mode = "polling")
  polling_interval_seconds: 5

  # Throttle settings (if mode = "realtime")
  throttle_enabled: true
  throttle_interval_seconds: 1.0  # Max 1 update per second per symbol

  # Stale quote detection
  stale_detection_enabled: true
  max_quote_age_seconds: 5.0

  # Quote caching
  enable_caching: true
  cache_ttl_seconds: 1

  # Fallback behavior
  fallback_to_sdk_pnl: true  # Use SDK's unrealized P&L if quote unavailable
```

### 10.2 Instrument Multipliers

**Location:** `config/instruments.yaml`

```yaml
instruments:
  - symbol: "MNQ"
    name: "Micro Nasdaq"
    exchange: "CME"
    multiplier: 2.0
    tick_size: 0.25
    tick_value: 0.50
    currency: "USD"

  - symbol: "ES"
    name: "E-mini S&P 500"
    exchange: "CME"
    multiplier: 50.0
    tick_size: 0.25
    tick_value: 12.50
    currency: "USD"

  - symbol: "NQ"
    name: "Nasdaq 100"
    exchange: "CME"
    multiplier: 20.0
    tick_size: 0.25
    tick_value: 5.00
    currency: "USD"
```

---

## 11. Testing Strategy

### 11.1 Unit Tests

**Test unrealized P&L calculation:**

```python
def test_unrealized_pnl_long_position():
    calculator = UnrealizedPnLCalculator({"MNQ": 2.0})

    # Long 2 MNQ at 21000, current 21050
    pnl = calculator.calculate("MNQ", 2, 21000, 21050)

    assert pnl == 200.0  # (21050 - 21000) * 2 * 2

def test_unrealized_pnl_short_position():
    calculator = UnrealizedPnLCalculator({"ES": 50.0})

    # Short 1 ES at 5800, current 5790
    pnl = calculator.calculate("ES", -1, 5800, 5790)

    assert pnl == 500.0  # (5800 - 5790) * 1 * 50

def test_throttle():
    throttle = QuoteThrottle(interval_seconds=1.0)

    # First update should process
    assert await throttle.should_process("MNQ") == True

    # Immediate second update should skip
    assert await throttle.should_process("MNQ") == False

    # After 1 second, should process again
    await asyncio.sleep(1.1)
    assert await throttle.should_process("MNQ") == True
```

### 11.2 Integration Tests

**Test quote subscription:**

```python
@pytest.mark.integration
async def test_quote_subscription():
    suite = await TradingSuite.create(instruments=["MNQ"])

    received_quotes = []

    async def on_quote(event):
        received_quotes.append(event)

    # Subscribe
    await suite.on(EventType.QUOTE_UPDATE, on_quote)

    # Wait for quotes
    await asyncio.sleep(5)

    # Verify received quotes
    assert len(received_quotes) > 0
    assert received_quotes[0].symbol == "MNQ"
    assert received_quotes[0].last_price > 0
```

---

## 12. Performance Metrics

### 12.1 Expected Load

**Quote Update Frequency:**
- MNQ: 50-100 updates/second (active trading)
- ES: 30-50 updates/second
- Total: 100-200 updates/second (2 instruments)

**With Throttling (1s interval):**
- MNQ: 1 update/second
- ES: 1 update/second
- Total: 2 updates/second (99% reduction)

### 12.2 Processing Time

**Per Quote Update:**
- Extract data: <1ms
- Calculate unrealized P&L: <1ms
- Update PnL tracker: 1-5ms (database write)
- Publish event: <1ms
- **Total: <10ms per update**

**With 2 updates/second:**
- Total processing: <20ms/second
- CPU usage: <1%

---

## 13. Implementation Checklist

### Core Components
- [ ] UnrealizedPnLCalculator class
- [ ] Quote data manager (hybrid real-time + polling)
- [ ] QuoteThrottle for event throttling
- [ ] StaleQuoteDetector for quote validation

### EventBridge Integration
- [ ] Subscribe to QUOTE_UPDATE events
- [ ] Handle quote update (_on_quote_update)
- [ ] Publish QUOTE_UPDATED risk events
- [ ] Add throttling

### PnL Tracker Integration
- [ ] Add update_unrealized_pnl method
- [ ] Add get_unrealized_pnl method
- [ ] Add get_unrealized_pnl_by_symbol method
- [ ] Add database persistence

### Rules
- [ ] RULE-004: DailyUnrealizedLoss implementation
- [ ] RULE-005: MaxUnrealizedProfit implementation
- [ ] Subscribe to QUOTE_UPDATED events
- [ ] Calculate unrealized P&L on quote updates

### Configuration
- [ ] Quote settings (throttle, stale detection)
- [ ] Instrument multipliers
- [ ] Fallback behavior

### Testing
- [ ] Unit tests (calculator, throttle, stale detection)
- [ ] Integration tests (quote subscription, P&L calculation)
- [ ] Performance tests (quote processing load)

---

## 14. Migration Path

### Phase 1: Add Quote Infrastructure
1. Create UnrealizedPnLCalculator
2. Add quote throttling
3. Add stale quote detection

### Phase 2: EventBridge Integration
1. Subscribe to QUOTE_UPDATE in EventBridge
2. Add _on_quote_update handler
3. Publish QUOTE_UPDATED events

### Phase 3: PnL Tracker Integration
1. Add unrealized P&L methods to PnLTracker
2. Add database persistence
3. Test P&L calculation accuracy

### Phase 4: Rule Implementation
1. Implement RULE-004 (DailyUnrealizedLoss)
2. Implement RULE-005 (MaxUnrealizedProfit)
3. Subscribe to QUOTE_UPDATED events
4. Test violation detection

### Phase 5: Testing & Optimization
1. Integration tests with real quotes
2. Performance testing
3. Tune throttle settings
4. Production deployment

---

## 15. References

**Implementation Files:**
- `src/risk_manager/sdk/event_bridge.py` - Quote event bridging
- `src/risk_manager/state/pnl_tracker.py` - Unrealized P&L tracking
- `src/risk_manager/rules/daily_unrealized_loss.py` - RULE-004
- `src/risk_manager/rules/max_unrealized_profit.py` - RULE-005

**Related Specs:**
- SDK Integration (UNIFIED-SDK-001)
- Event Handling (UNIFIED-SDK-002)

**Wave 1 Analysis:**
- `docs/analysis/wave1-feature-inventory/02-SDK-INTEGRATION-INVENTORY.md`

**Wave 2 Gaps:**
- `docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md`

---

**Document Status:** New Feature Specification
**Last Updated:** 2025-10-25
**Next Steps:** Begin Phase 1 implementation (quote infrastructure)
