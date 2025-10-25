# SDK Logging Flow Diagram

## Application Startup Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Risk Manager V34 Startup                      │
└─────────────────────────────────────────────────────────────────┘

1. RiskManager.__init__()
   │
   ├─→ 🚀 Risk Manager starting...
   │   └─→ [manager.py:44] sdk_logger.info()
   │
   
2. RiskManager.create()
   │
   ├─→ ✅ Config loaded: X custom rules, monitoring Y instruments
   │   └─→ [manager.py:109] sdk_logger.info()
   │
   
3. _init_trading_integration()
   │
   ├─→ ✅ SDK connected: X instrument(s) - [MNQ, ES, ...]
   │   └─→ [manager.py:138] sdk_logger.info()
   │
   
4. _add_default_rules()
   │
   ├─→ ✅ Rules initialized: X rules - [DailyLossRule($-500), ...]
   │   └─→ [manager.py:184] sdk_logger.info()
   │
   
5. RiskEngine.start()
   │
   └─→ ✅ Event loop running: X active rules monitoring events
       └─→ [engine.py:38] sdk_logger.info()
```

## Runtime Event Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Event Processing Cycle                         │
└─────────────────────────────────────────────────────────────────┘

Event Occurs (Order Fill, Position Update, etc.)
   │
   ├─→ 📨 Event received: EVENT_TYPE - evaluating X rules
   │   └─→ [engine.py:68] sdk_logger.info()
   │
   ├─→ For each rule:
   │   │
   │   ├─→ 🔍 Rule evaluated: RuleName - [VIOLATED|PASSED]
   │   │   └─→ [engine.py:75] sdk_logger.info()
   │   │
   │   └─→ If VIOLATED:
   │       │
   │       └─→ _handle_violation()
   │           │
   │           ├─→ action == "flatten"
   │           │   └─→ ⚠️ Enforcement triggered: FLATTEN ALL - Rule: XYZ
   │           │       └─→ [engine.py:101] sdk_logger.warning()
   │           │
   │           ├─→ action == "pause"
   │           │   └─→ ⚠️ Enforcement triggered: PAUSE TRADING - Rule: XYZ
   │           │       └─→ [engine.py:105] sdk_logger.warning()
   │           │
   │           └─→ action == "alert"
   │               └─→ ⚠️ Enforcement triggered: ALERT - Rule: XYZ
   │                   └─→ [engine.py:109] sdk_logger.info()
```

## Enforcement Actions Flow

```
┌─────────────────────────────────────────────────────────────────┐
│               EnforcementExecutor Actions                        │
└─────────────────────────────────────────────────────────────────┘

1. close_all_positions(symbol)
   │
   └─→ ⚠️ Enforcement triggered: CLOSE ALL POSITIONS - Symbol: [symbol|ALL]
       └─→ [enforcement.py:56] sdk_logger.warning()

2. close_position(symbol, contract_id)
   │
   └─→ ⚠️ Enforcement triggered: CLOSE POSITION - symbol/contract_id
       └─→ [enforcement.py:132] sdk_logger.warning()

3. cancel_all_orders(symbol)
   │
   └─→ ⚠️ Enforcement triggered: CANCEL ALL ORDERS - Symbol: [symbol|ALL]
       └─→ [enforcement.py:220] sdk_logger.warning()

4. flatten_and_cancel(symbol)
   │
   └─→ ⚠️ Enforcement triggered: FLATTEN AND CANCEL - Symbol: [symbol|ALL] - CRITICAL
       └─→ [enforcement.py:325] sdk_logger.warning()
```

## Log Levels by Checkpoint

| Checkpoint | Log Level | Emoji | Purpose |
|------------|-----------|-------|---------|
| Service start | INFO | 🚀 | Application initialization |
| Config loaded | INFO | ✅ | Configuration validation |
| SDK connected | INFO | ✅ | Trading SDK connection |
| Rules initialized | INFO | ✅ | Risk rules setup |
| Event loop running | INFO | ✅ | Event monitoring active |
| Event received | INFO | 📨 | Event processing start |
| Rule evaluated | INFO | 🔍 | Rule evaluation result |
| Enforcement (alert) | INFO | ⚠️ | Low-severity action |
| Enforcement (pause/flatten) | WARNING | ⚠️ | High-severity action |
| Enforcement actions | WARNING | ⚠️ | Position/order modifications |

## Example Log Output

```json
{"timestamp":"2025-10-24T03:00:00.000Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"__init__","line":44,"message":"🚀 Risk Manager starting..."}

{"timestamp":"2025-10-24T03:00:00.100Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"create","line":109,"message":"✅ Config loaded: 2 custom rules, monitoring 1 instruments"}

{"timestamp":"2025-10-24T03:00:00.200Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"_init_trading_integration","line":138,"message":"✅ SDK connected: 1 instrument(s) - MNQ"}

{"timestamp":"2025-10-24T03:00:00.300Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"_add_default_rules","line":184,"message":"✅ Rules initialized: 2 rules - DailyLossRule($-500.0), MaxPositionRule(2 contracts)"}

{"timestamp":"2025-10-24T03:00:00.400Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"start","line":38,"message":"✅ Event loop running: 2 active rules monitoring events"}

{"timestamp":"2025-10-24T03:00:01.000Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"evaluate_rules","line":68,"message":"📨 Event received: order_filled - evaluating 2 rules"}

{"timestamp":"2025-10-24T03:00:01.010Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"evaluate_rules","line":75,"message":"🔍 Rule evaluated: DailyLossRule - VIOLATED"}

{"timestamp":"2025-10-24T03:00:01.020Z","level":"WARNING","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":101,"message":"⚠️ Enforcement triggered: FLATTEN ALL - Rule: DailyLossRule"}

{"timestamp":"2025-10-24T03:00:01.030Z","level":"WARNING","logger":"risk_manager.sdk.enforcement","module":"enforcement","function":"close_all_positions","line":56,"message":"⚠️ Enforcement triggered: CLOSE ALL POSITIONS - Symbol: ALL"}
```

## Integration with Monitoring Tools

The SDK logging can be integrated with:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Datadog**
- **CloudWatch**
- **Grafana Loki**

All logs are JSON-formatted in production mode for easy parsing and querying.

---
**Note**: Logs shown are in production JSON format. In development mode (DEBUG level), logs use a more readable format without JSON encoding.
