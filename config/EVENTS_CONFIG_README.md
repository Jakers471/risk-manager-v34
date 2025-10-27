# Events Configuration Guide

**Location**: `config/events_config.yaml`
**Purpose**: Configure SDK event subscriptions, filtering, and processing for Risk Manager V34
**Last Updated**: 2025-10-27

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Event Categories](#event-categories)
4. [Configuration Sections](#configuration-sections)
5. [Critical Settings](#critical-settings)
6. [Quote Integration (RULE-004/005)](#quote-integration-rule-004005)
7. [P&L Calculation](#pl-calculation)
8. [Event Priorities](#event-priorities)
9. [Backpressure & Performance](#backpressure--performance)
10. [Troubleshooting](#troubleshooting)
11. [Examples](#examples)

---

## Overview

The `events_config.yaml` file controls how Risk Manager V34 subscribes to, filters, and processes events from the Project-X SDK. This configuration is **critical** for:

- **RULE-004/005**: Unrealized P&L tracking (requires quote data)
- **RULE-001**: Max contracts enforcement (requires position events)
- **RULE-003/013**: Realized P&L tracking (requires trade events)
- **RULE-008**: Stop loss validation (requires order events)
- **RULE-010/011**: Account monitoring (requires account events)

### Key Features

✅ **Quote throttling** - Reduce high-frequency quote spam (100+ events/sec → 1/sec)
✅ **Auto-subscribe** - Automatically subscribe to quotes for active positions
✅ **Event filtering** - Process only relevant events
✅ **Priority routing** - Critical events processed immediately
✅ **Backpressure handling** - Graceful degradation under load
✅ **Batch processing** - Efficient event handling
✅ **P&L calculation** - Tick values for unrealized P&L math

---

## Quick Start

### 1. Copy Template

```bash
cd config
cp events_config.yaml.template events_config.yaml
```

### 2. Basic Configuration

For **most users**, the default configuration works out of the box:

```yaml
# Minimum required config
quotes:
  enabled: true              # Required for RULE-004/005
  symbols: []                # Auto-track positions
  update_interval_ms: 1000  # 1 second throttle

positions:
  enabled: true              # Required for position rules

trades:
  enabled: true              # Required for P&L tracking
  track_pnl: true
```

### 3. Verify Configuration

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('events_config.yaml'))"

# View loaded config
python -c "from risk_manager.config import load_events_config; print(load_events_config())"
```

---

## Event Categories

The SDK provides 6 main event categories:

| Category | Event Types | Required For | Frequency |
|----------|-------------|--------------|-----------|
| **Positions** | OPENED, UPDATED, CLOSED | RULE-001, 004, 005, 008 | Low (1-10/min) |
| **Orders** | PLACED, FILLED, CANCELLED, REJECTED, MODIFIED | RULE-008, 012 | Medium (10-50/min) |
| **Trades** | EXECUTED | RULE-003, 013 | Low (1-10/min) |
| **Quotes** | QUOTE_UPDATE | RULE-004, 005, 012 | **Very High** (100+/sec) |
| **Account** | ACCOUNT_UPDATED | RULE-010, 011 | Very Low (1-5/day) |
| **Bars** | NEW_BAR | RULE-012 (optional) | Low (depends on timeframe) |

### Event Importance

**Critical** (must process immediately):
- Position events (for max contracts enforcement)
- Trade events (for realized P&L tracking)
- Account events (for lockout detection)
- Order PLACED/FILLED/REJECTED

**High** (process quickly):
- Quote events (for unrealized P&L, but throttled)
- Order PARTIAL_FILL

**Normal** (standard processing):
- Order CANCELLED/MODIFIED
- Bar events

---

## Configuration Sections

### 1. Quote Events

**Purpose**: Real-time price updates for unrealized P&L calculation

```yaml
quotes:
  enabled: true                          # Enable quote subscription
  symbols: []                            # [] = auto-track, or ['MNQ', 'ES']
  update_interval_ms: 1000              # Throttle: 1000ms = 1/sec
  fields: [last, bid, ask]              # Price fields
  auto_subscribe_on_position: true      # Auto-subscribe on open
  auto_unsubscribe_on_close: true       # Auto-unsubscribe on close
  buffer_size: 10                        # Batch size
  buffer_flush_interval_ms: 500         # Batch timeout
```

**Critical Settings**:
- `enabled: true` - **REQUIRED** for RULE-004/005
- `symbols: []` - Empty list auto-subscribes to active positions only
- `update_interval_ms: 1000` - Throttle to 1/second (prevents flooding)

**Why Throttling?**
- Quote events fire at **100+ times per second** per symbol
- Unrealized P&L only needs updates every 1 second
- Throttling reduces CPU load by 99% with no loss of accuracy

**Auto-Subscribe Behavior**:
1. Position opens (POSITION_OPENED) → Auto-subscribe to quotes for that symbol
2. Position closes (POSITION_CLOSED) → Auto-unsubscribe (saves bandwidth)
3. Manual override: Use `symbols: ['MNQ', 'ES']` to always subscribe

### 2. Position Events

**Purpose**: Track position lifecycle for max contracts and stop loss checks

```yaml
positions:
  enabled: true
  events: [OPENED, UPDATED, CLOSED]
  priority: critical
  fields: [size, averagePrice, contractId, type, accountId]
```

**Critical Settings**:
- `enabled: true` - **REQUIRED** for all position-based rules
- `priority: critical` - Process immediately (no buffering)

**Event Mapping**:
- `POSITION_OPENED` - New position created (0 → 1+)
- `POSITION_UPDATED` - Size changed (1 → 2) or avg price updated
- `POSITION_CLOSED` - Position flattened (1+ → 0)

**Note**: SDK sends `POSITION_UPDATED` for all changes. We distinguish opens/closes by checking `old_size` vs `new_size`.

### 3. Order Events

**Purpose**: Track order lifecycle for stop loss validation and trade management

```yaml
orders:
  enabled: true
  events: [PLACED, FILLED, PARTIAL_FILL, CANCELLED, MODIFIED, REJECTED]
  priority_map:
    PLACED: critical      # Has stop price!
    FILLED: critical
    REJECTED: critical
    CANCELLED: normal
    MODIFIED: normal
    PARTIAL_FILL: high
  fields: [type, side, stopPrice, limitPrice, size, filledPrice, status, accountId, contractId]
```

**Critical Settings**:
- `stopPrice` field - **REQUIRED** for RULE-008 (stop loss check)
- `PLACED: critical` - Must process immediately to extract stop price

**Why PLACED is Critical**:
- RULE-008 checks if position has a stop loss
- Stop price is **only available in ORDER_PLACED event**
- If we miss this event, we can't validate stop loss

### 4. Trade Events

**Purpose**: Track realized P&L from closed trades

```yaml
trades:
  enabled: true
  events: [EXECUTED]
  priority: critical
  track_pnl: true
  fields: [profitAndLoss, quantity, price, accountId, contractId]
```

**Critical Settings**:
- `track_pnl: true` - **REQUIRED** for RULE-003/013
- `profitAndLoss` field - Contains realized P&L in dollars

**Important**:
- `profitAndLoss` is **NULL for opening trades** (only set for closing trades)
- Filter: `if profitAndLoss is not None: update_daily_pnl()`

### 5. Account Events

**Purpose**: Detect account lockouts and balance issues

```yaml
account:
  enabled: true
  events: [UPDATED]
  priority: critical
  fields: [canTrade, balance, equity, marginUsed, accountId]
```

**Critical Settings**:
- `canTrade` field - **REQUIRED** for RULE-010 (authorization guard)
- Detects when TopstepX locks account externally

### 6. Bar Events (Optional)

**Purpose**: Candlestick data for advanced trade management

```yaml
bars:
  enabled: false               # Not required for core rules
  events: [NEW_BAR]
  priority: normal
  timeframes: [5m, 15m]
```

**Note**: Only enable if implementing RULE-012 time-based analysis.

---

## Critical Settings

### Must Enable for Core Functionality

| Setting | Rule Dependency | Reason |
|---------|----------------|---------|
| `quotes.enabled: true` | RULE-004, 005 | Unrealized P&L needs current prices |
| `positions.enabled: true` | RULE-001, 004, 005, 008 | Position tracking |
| `trades.enabled: true` | RULE-003, 013 | Realized P&L tracking |
| `orders.enabled: true` | RULE-008, 012 | Stop loss validation |
| `account.enabled: true` | RULE-010, 011 | Lockout detection |

### Performance-Critical Settings

| Setting | Default | Impact |
|---------|---------|--------|
| `quotes.update_interval_ms` | 1000 | **High** - Too low = CPU overload |
| `processing.max_queue_size` | 1000 | **Medium** - Too low = dropped events |
| `processing.backpressure_strategy` | drop_oldest | **High** - Wrong choice = stale data |

---

## Quote Integration (RULE-004/005)

### Problem Statement

**RULE-004** (Daily Unrealized Loss) and **RULE-005** (Max Unrealized Profit) require **real-time unrealized P&L calculation**:

```python
unrealized_pnl = (current_price - entry_price) / tick_size * contracts * tick_value
```

**Dependencies**:
1. **Entry price** - From `POSITION_UPDATED.averagePrice`
2. **Current price** - From `QUOTE_UPDATE.last` ⬅️ **CRITICAL**
3. **Tick value/size** - From config (see P&L Calculation section)

### Solution: Quote Subscription

```yaml
quotes:
  enabled: true                          # Enable SDK quote subscription
  symbols: []                            # Auto-subscribe to active positions
  update_interval_ms: 1000              # Throttle to 1/sec
  fields: [last]                         # Only need last price
  auto_subscribe_on_position: true      # Subscribe when position opens
```

### Workflow

1. **Position opens** (POSITION_OPENED)
   - Extract: `symbol = position.contractId`
   - Action: `await sdk.subscribe_quotes(symbol)`
   - Store: `entry_price = position.averagePrice`

2. **Quote updates** (QUOTE_UPDATE, throttled to 1/sec)
   - Extract: `current_price = quote.last`
   - Calculate: `unrealized_pnl = (current_price - entry_price) / tick_size * size * tick_value`
   - Check: `if unrealized_pnl <= -300: enforce_rule_004()`

3. **Position closes** (POSITION_CLOSED)
   - Action: `await sdk.unsubscribe_quotes(symbol)` (saves bandwidth)

### Throttling Deep Dive

**Without throttling**:
- Quote events: **100+ per second per symbol**
- 3 active symbols = **300+ events/sec** = **18,000+ events/min**
- CPU usage: **80%+** just processing quote events
- Risk of dropped events and system instability

**With throttling (1000ms)**:
- Quote events: **1 per second per symbol**
- 3 active symbols = **3 events/sec** = **180 events/min**
- CPU usage: **<5%** for quote processing
- **99% reduction** in processing load

**Accuracy impact**: None. Unrealized P&L updated every 1 second is more than sufficient.

---

## P&L Calculation

### Formula

```python
unrealized_pnl = (current_price - entry_price) / tick_size * contracts * tick_value
```

### Example: MNQ (Micro E-mini NASDAQ-100)

**Given**:
- Entry price: `21000.00`
- Current price: `20990.00` (down 10 points)
- Position size: `2 contracts`
- Tick size: `0.25` (from config)
- Tick value: `$5.00` (from config)

**Calculation**:
```python
price_diff = 20990.00 - 21000.00 = -10.00 points
ticks = -10.00 / 0.25 = -40 ticks
unrealized_pnl = -40 * 2 * 5.00 = -$400
```

**Result**: Position has **-$400 unrealized loss**

### Tick Values Configuration

```yaml
tick_values:
  MNQ: 5.0    # $5 per tick (Micro E-mini NASDAQ-100)
  MES: 5.0    # $5 per tick (Micro E-mini S&P 500)
  M2K: 5.0    # $5 per tick (Micro E-mini Russell 2000)
  MYM: 0.5    # $0.50 per tick (Micro E-mini Dow)
  NQ: 20.0    # $20 per tick (E-mini NASDAQ-100)
  ES: 50.0    # $50 per tick (E-mini S&P 500)
  RTY: 5.0    # $5 per tick (E-mini Russell 2000)
  YM: 5.0     # $5 per tick (E-mini Dow)

tick_sizes:
  MNQ: 0.25   # 0.25 point tick
  MES: 0.25   # 0.25 point tick
  M2K: 0.10   # 0.10 point tick
  MYM: 1.0    # 1 point tick
  NQ: 0.25    # 0.25 point tick
  ES: 0.25    # 0.25 point tick
  RTY: 0.10   # 0.10 point tick
  YM: 1.0     # 1 point tick
```

**Adding New Symbols**:
1. Look up contract specifications (CME website)
2. Find tick size (e.g., 0.25 points)
3. Find tick value (e.g., $5.00)
4. Add to config:
   ```yaml
   tick_values:
     NEW_SYMBOL: 5.0
   tick_sizes:
     NEW_SYMBOL: 0.25
   ```

---

## Event Priorities

### Priority Levels

| Priority | Processing | Use Case |
|----------|-----------|----------|
| **critical** | Immediate, no buffering | Account lockouts, positions, trades |
| **high** | Quick, minimal buffering | Partial fills, throttled quotes |
| **normal** | Standard, batch processing | Cancellations, modifications, bars |

### Priority Mapping

```yaml
priority_map:
  # CRITICAL: Must process immediately
  PLACED: critical      # Need stop price now
  FILLED: critical      # Update position state
  REJECTED: critical    # Alert trader immediately

  # HIGH: Process quickly
  PARTIAL_FILL: high    # Position partially filled

  # NORMAL: Can buffer
  CANCELLED: normal     # Informational
  MODIFIED: normal      # Informational
```

### Why Priorities Matter

**Example: Max Contracts Rule (RULE-001)**

1. Trader has 1 MNQ contract (limit: 2)
2. Trader places order for 2 more MNQ (would breach limit)
3. Order fills (POSITION_UPDATED fired)
4. **Critical priority**: Process immediately
5. Detect breach: 1 + 2 = 3 contracts > 2 limit
6. Enforce: Auto-flatten 1 contract
7. **Result**: Breach prevented in <100ms

**If priority was "normal"**:
- Event might sit in buffer for 50-100ms
- Trader could place another order in that window
- Cascading violations possible

---

## Backpressure & Performance

### The Problem

**High-frequency quote events** can overwhelm the system:
- 100+ quote events/sec per symbol
- 3 symbols = 300 events/sec
- If processing takes 10ms per event = **3000ms/sec** = **300% CPU**
- **Result**: Event queue backs up, system crashes

### Solution: Backpressure Strategy

```yaml
processing:
  max_queue_size: 1000                   # Max 1000 events in queue
  backpressure_strategy: drop_oldest    # Drop old events when full
  processing_timeout_ms: 100            # Warn if >100ms per event
```

### Backpressure Strategies

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| **drop_oldest** | Drop old events when queue full | **RECOMMENDED** - Prefer fresh data |
| **drop_newest** | Drop new events when queue full | Rare - when historical context needed |
| **block** | Block SDK until queue space available | **NOT RECOMMENDED** - May crash SDK |

### Performance Settings

```yaml
processing:
  batch_processing:
    enabled: true
    batch_size: 10         # Process 10 events at once
    batch_timeout_ms: 50   # Max 50ms wait for batch
```

**Batch processing**:
- **Benefits**: Reduce overhead (1 batch = 10 events with 1 setup cost)
- **Cost**: 50ms latency (acceptable for non-critical events)
- **Use for**: Quotes (already throttled), bars, cancellations

**Don't batch**:
- Critical events (positions, trades, account)
- These bypass batching and process immediately

### Monitoring Performance

```yaml
logging:
  log_statistics: true                   # Log event counts
  statistics_interval_seconds: 60       # Every 60 seconds
  log_dropped_events: true               # Alert on drops
  log_slow_events: true                  # Alert on slow processing
  slow_event_threshold_ms: 50           # >50ms = slow
```

**Example output**:
```
[INFO] Event statistics (last 60s):
  QUOTE_UPDATE: 180 processed, 0 dropped
  POSITION_UPDATED: 12 processed, 0 dropped
  ORDER_FILLED: 8 processed, 0 dropped
  Avg processing time: 5ms
  Max processing time: 23ms
```

---

## Troubleshooting

### Issue: RULE-004/005 Not Working

**Symptoms**:
- Unrealized P&L shows $0 or NaN
- Positions not closed when hitting loss limit
- No quote events in logs

**Solution**:
1. Check quote subscription:
   ```yaml
   quotes:
     enabled: true  # Must be true!
   ```

2. Check auto-subscribe:
   ```yaml
   auto_subscribe_on_position: true
   ```

3. Enable debug logging:
   ```yaml
   logging:
     log_all_events: true  # Temporarily
   ```

4. Check logs for:
   ```
   [DEBUG] Subscribed to quotes: MNQ
   [DEBUG] Quote update: MNQ last=20990.00
   ```

5. Verify tick values exist for symbol:
   ```yaml
   tick_values:
     MNQ: 5.0  # Must match your symbols!
   ```

### Issue: High CPU Usage

**Symptoms**:
- CPU >50%
- Event queue backing up
- Dropped events in logs

**Solution**:
1. Increase quote throttling:
   ```yaml
   quotes:
     update_interval_ms: 2000  # Increase to 2 seconds
   ```

2. Reduce batch size:
   ```yaml
   batch_processing:
     batch_size: 5  # Reduce from 10
   ```

3. Check for slow event processing:
   ```yaml
   logging:
     log_slow_events: true
   ```

4. Review logs for slow rules:
   ```
   [WARN] Slow event processing: RULE-004 took 150ms
   ```

5. Optimize rule logic (see rule implementation)

### Issue: Dropped Events

**Symptoms**:
- Log shows: `[WARN] Dropped 50 events (queue full)`
- Missing position updates
- Inconsistent P&L

**Solution**:
1. Increase queue size:
   ```yaml
   processing:
     max_queue_size: 2000  # Increase from 1000
   ```

2. Check backpressure strategy:
   ```yaml
   backpressure_strategy: drop_oldest  # Should be drop_oldest
   ```

3. Enable batch processing:
   ```yaml
   batch_processing:
     enabled: true
   ```

4. Reduce event load:
   ```yaml
   quotes:
     update_interval_ms: 2000  # Throttle more aggressively
   ```

### Issue: Stop Loss Check Failing (RULE-008)

**Symptoms**:
- RULE-008 reports "no stop loss" when trader placed stop order
- Stop price shows as NULL

**Solution**:
1. Ensure ORDER_PLACED is enabled:
   ```yaml
   orders:
     enabled: true
     events:
       - PLACED  # Must include PLACED!
   ```

2. Check stopPrice field extracted:
   ```yaml
   fields:
     - stopPrice  # Must include stopPrice!
   ```

3. Check priority (must be critical):
   ```yaml
   priority_map:
     PLACED: critical  # Process immediately
   ```

4. Enable debug logging:
   ```yaml
   logging:
     log_all_events: true
   ```

5. Check logs for:
   ```
   [DEBUG] Order placed: type=3 (STOP), stopPrice=20990.00
   ```

---

## Examples

### Example 1: Minimal Configuration (Development)

```yaml
quotes:
  enabled: true
  symbols: []
  update_interval_ms: 1000

positions:
  enabled: true

trades:
  enabled: true
  track_pnl: true

account:
  enabled: true

orders:
  enabled: true

processing:
  max_queue_size: 500
  backpressure_strategy: drop_oldest

logging:
  log_all_events: true  # For debugging
  log_statistics: true
```

**Use case**: Development/testing, verbose logging

### Example 2: Production Configuration

```yaml
quotes:
  enabled: true
  symbols: []
  update_interval_ms: 1000
  auto_subscribe_on_position: true
  auto_unsubscribe_on_close: true

positions:
  enabled: true
  priority: critical

trades:
  enabled: true
  track_pnl: true
  priority: critical

account:
  enabled: true
  priority: critical

orders:
  enabled: true
  priority_map:
    PLACED: critical
    FILLED: critical
    REJECTED: critical
    CANCELLED: normal
    MODIFIED: normal

processing:
  max_queue_size: 1000
  backpressure_strategy: drop_oldest
  batch_processing:
    enabled: true
    batch_size: 10

logging:
  log_all_events: false  # Disable verbose logging
  log_statistics: true
  log_dropped_events: true
  log_slow_events: true
```

**Use case**: Production, optimized performance

### Example 3: High-Frequency Trading

```yaml
quotes:
  enabled: true
  symbols: []
  update_interval_ms: 500  # More frequent updates
  buffer_size: 20           # Larger buffer

processing:
  max_queue_size: 2000      # Larger queue
  batch_processing:
    enabled: true
    batch_size: 20          # Larger batches
    batch_timeout_ms: 25    # Lower timeout

logging:
  log_statistics: true
  statistics_interval_seconds: 30  # More frequent stats
```

**Use case**: High-frequency strategies requiring fast quote updates

### Example 4: Specific Symbols Only

```yaml
quotes:
  enabled: true
  symbols: ['MNQ', 'MES', 'M2K']  # Only these symbols
  auto_subscribe_on_position: false  # Manual control

positions:
  enabled: true

filters:
  account_ids: ['ACC123456']  # Only this account
```

**Use case**: Multi-account environment, only monitor specific symbols/accounts

---

## Integration with Risk Rules

### Rule → Event Mapping

| Rule | Required Events | Critical Fields |
|------|----------------|-----------------|
| **RULE-001** (Max Contracts) | POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED | size, contractId |
| **RULE-003** (Daily Realized Loss) | TRADE_EXECUTED | profitAndLoss |
| **RULE-004** (Daily Unrealized Loss) | POSITION_UPDATED, QUOTE_UPDATE | averagePrice, last |
| **RULE-005** (Max Unrealized Profit) | POSITION_UPDATED, QUOTE_UPDATE | averagePrice, last |
| **RULE-008** (Stop Loss Check) | POSITION_OPENED, ORDER_PLACED | stopPrice |
| **RULE-010** (Authorization Guard) | ACCOUNT_UPDATED | canTrade |
| **RULE-011** (Account Balance Guard) | ACCOUNT_UPDATED | balance |
| **RULE-012** (Trade Management) | ORDER_PLACED, ORDER_FILLED, QUOTE_UPDATE | Multiple |
| **RULE-013** (Daily Realized Profit) | TRADE_EXECUTED | profitAndLoss |

### Event Flow Example: RULE-004 (Daily Unrealized Loss)

```
1. Position opens:
   Event: POSITION_OPENED
   Data: { contractId: 'MNQ', size: 2, averagePrice: 21000.00 }
   Action: Subscribe to MNQ quotes, store entry price

2. Quote updates (throttled to 1/sec):
   Event: QUOTE_UPDATE
   Data: { contractId: 'MNQ', last: 20990.00 }
   Action: Calculate unrealized P&L

   Calculation:
   price_diff = 20990.00 - 21000.00 = -10.00
   ticks = -10.00 / 0.25 = -40 ticks
   unrealized_pnl = -40 * 2 * 5.00 = -$400

   Check: -$400 <= -$300 (limit) = BREACH!

3. Enforcement:
   Action: Close MNQ position (2 contracts)
   Event: POSITION_CLOSED
   Action: Unsubscribe from MNQ quotes

4. Result:
   Position closed, unrealized loss prevented from growing
```

---

## Best Practices

### 1. Start Simple

- Use default configuration first
- Enable verbose logging during development
- Gradually optimize based on observed performance

### 2. Monitor Performance

- Check event statistics regularly
- Watch for dropped events (indicates overload)
- Monitor slow event processing (>50ms)

### 3. Throttle Aggressively

- Quote updates at 1/sec are sufficient for unrealized P&L
- Don't set `update_interval_ms` < 500ms unless needed

### 4. Use Auto-Subscribe

- Set `auto_subscribe_on_position: true`
- Reduces configuration burden
- Only subscribes to active positions (saves bandwidth)

### 5. Test Quote Integration

- Before deploying RULE-004/005, verify quote subscription works:
  ```python
  # Test script
  from risk_manager.sdk import subscribe_quotes

  await subscribe_quotes('MNQ')
  # Check logs for: "Subscribed to quotes: MNQ"
  # Check logs for: "Quote update: MNQ last=..."
  ```

### 6. Validate Tick Values

- Ensure tick values/sizes match your contracts
- Test P&L calculation manually:
  ```python
  # Test calculation
  entry = 21000.00
  current = 20990.00
  tick_size = 0.25
  tick_value = 5.0
  contracts = 2

  unrealized_pnl = (current - entry) / tick_size * contracts * tick_value
  print(f"Unrealized P&L: ${unrealized_pnl:.2f}")
  # Expected: -$400.00
  ```

---

## File Locations

- **Configuration**: `config/events_config.yaml`
- **Template**: `config/events_config.yaml.template`
- **This README**: `config/EVENTS_CONFIG_README.md`
- **SDK Reference**: `SDK_EVENTS_QUICK_REFERENCE.txt`
- **Rule Specs**: `docs/specifications/unified/rules/`

---

## Related Documentation

- `SDK_EVENTS_QUICK_REFERENCE.txt` - Complete SDK event reference
- `docs/specifications/unified/rules/RULE-004-daily-unrealized-loss.md` - Unrealized loss rule
- `docs/specifications/unified/rules/RULE-005-max-unrealized-profit.md` - Unrealized profit rule
- `docs/current/SDK_INTEGRATION_GUIDE.md` - SDK integration overview

---

## Version History

- **v1.0** (2025-10-27): Initial events configuration created
  - Quote throttling and auto-subscribe
  - Event priorities and backpressure handling
  - P&L calculation tick values
  - Comprehensive documentation

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs: `data/logs/risk_manager.log`
3. Enable debug logging: `log_all_events: true`
4. Test event flow with unit tests: `pytest tests/integration/test_events.py`

---

**Last Updated**: 2025-10-27
**Maintainer**: Risk Manager V34 Team
