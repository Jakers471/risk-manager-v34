# SDK Logging Quick Reference

## Quick Import Pattern

```python
from project_x_py.utils import ProjectXLogger
sdk_logger = ProjectXLogger.get_logger(__name__)
```

## All 8 Strategic Checkpoints

### 1. Service Start
```python
# Location: manager.py:44
sdk_logger.info("🚀 Risk Manager starting...")
```

### 2. Config Loaded
```python
# Location: manager.py:109
sdk_logger.info(f"✅ Config loaded: {len(rules) if rules else 0} custom rules, monitoring {len(instruments) if instruments else 0} instruments")
```

### 3. SDK Connected
```python
# Location: manager.py:138
sdk_logger.info(f"✅ SDK connected: {len(instruments)} instrument(s) - {', '.join(instruments)}")
```

### 4. Rules Initialized
```python
# Location: manager.py:184
sdk_logger.info(f"✅ Rules initialized: {len(rules_added)} rules - {', '.join(rules_added)}")
```

### 5. Event Loop Running
```python
# Location: engine.py:38
sdk_logger.info(f"✅ Event loop running: {len(self.rules)} active rules monitoring events")
```

### 6. Event Received
```python
# Location: engine.py:68
sdk_logger.info(f"📨 Event received: {event.event_type.value} - evaluating {len(self.rules)} rules")
```

### 7. Rule Evaluated
```python
# Location: engine.py:75
sdk_logger.info(f"🔍 Rule evaluated: {rule.__class__.__name__} - {'VIOLATED' if violation else 'PASSED'}")
```

### 8. Enforcement Triggered
```python
# Location: engine.py:101, 105, 109
sdk_logger.warning(f"⚠️ Enforcement triggered: FLATTEN ALL - Rule: {rule.__class__.__name__}")
sdk_logger.warning(f"⚠️ Enforcement triggered: PAUSE TRADING - Rule: {rule.__class__.__name__}")
sdk_logger.info(f"⚠️ Enforcement triggered: ALERT - Rule: {rule.__class__.__name__}")
```

## Enforcement Action Logging

### Close All Positions
```python
# Location: enforcement.py:56
sdk_logger.warning(f"⚠️ Enforcement triggered: CLOSE ALL POSITIONS - Symbol: {symbol or 'ALL'}")
```

### Close Specific Position
```python
# Location: enforcement.py:132
sdk_logger.warning(f"⚠️ Enforcement triggered: CLOSE POSITION - {symbol}/{contract_id}")
```

### Cancel All Orders
```python
# Location: enforcement.py:220
sdk_logger.warning(f"⚠️ Enforcement triggered: CANCEL ALL ORDERS - Symbol: {symbol or 'ALL'}")
```

### Flatten and Cancel (Critical)
```python
# Location: enforcement.py:325
sdk_logger.warning(f"⚠️ Enforcement triggered: FLATTEN AND CANCEL - Symbol: {symbol or 'ALL'} - CRITICAL ACTION")
```

## Files Modified

1. `/src/risk_manager/core/manager.py` - 262 lines
2. `/src/risk_manager/core/engine.py` - 174 lines  
3. `/src/risk_manager/sdk/enforcement.py` - 343 lines

## Grep Commands for Verification

```bash
# Find all SDK logger instances
grep -n "sdk_logger" src/risk_manager/core/manager.py
grep -n "sdk_logger" src/risk_manager/core/engine.py
grep -n "sdk_logger" src/risk_manager/sdk/enforcement.py

# Find all checkpoints
grep -n "🚀\|✅\|📨\|🔍\|⚠️" src/risk_manager/**/*.py
```

## Testing the Implementation

```bash
# Quick test
cd /mnt/c/Users/jakers/Desktop/risk-manager-v34
python3 -c "
from project_x_py.utils import ProjectXLogger
logger = ProjectXLogger.get_logger('test')
logger.info('🚀 Test: Service start')
logger.info('✅ Test: Config loaded')
logger.warning('⚠️ Test: Enforcement triggered')
"

# Run example
python examples/01_basic_usage.py
```

## Expected Startup Log Sequence

1. 🚀 Risk Manager starting...
2. ✅ Config loaded: X custom rules, monitoring Y instruments
3. ✅ SDK connected: X instrument(s) - [symbols]
4. ✅ Rules initialized: X rules - [rule list]
5. ✅ Event loop running: X active rules monitoring events

## Log Levels Used

| Level | When to Use | Example |
|-------|-------------|---------|
| INFO | Normal operations, checkpoints | Config loaded, SDK connected |
| WARNING | Risk events, enforcement actions | Flatten all, Cancel orders |
| ERROR | Failures, exceptions | SDK connection failed |

## Additional SDK Logger Features

### Performance Logging
```python
from project_x_py.utils import log_performance
import time

start = time.time()
# ... operation ...
log_performance(sdk_logger, "operation_name", start)
```

### API Call Logging
```python
from project_x_py.utils import log_api_call

log_api_call(
    sdk_logger,
    method="POST",
    endpoint="/api/orders",
    status_code=200,
    duration=0.5
)
```

### Context Logging
```python
from project_x_py.utils import LogContext

with LogContext(sdk_logger, operation="evaluate_rules", rule="DailyLossRule"):
    sdk_logger.info("Evaluating rule")
    # All logs in this block include the context
```

## Documentation Files Created

- `SDK_LOGGING_IMPLEMENTATION.md` - Complete implementation report
- `LOGGING_FLOW.md` - Visual flow diagrams
- `SDK_LOGGING_QUICK_REFERENCE.md` - This quick reference

## Status

✅ **COMPLETE** - All 8+ strategic checkpoints implemented
✅ **TESTED** - SDK logging imports and patterns verified
✅ **DOCUMENTED** - Three documentation files created

---
**Project**: Risk Manager V34  
**Path**: `/mnt/c/Users/jakers/Desktop/risk-manager-v34/`  
**Date**: 2025-10-23
