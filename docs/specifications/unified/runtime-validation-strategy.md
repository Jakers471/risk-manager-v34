# Runtime Validation Strategy

**Version**: 1.0
**Date**: 2025-10-25
**Status**: Authoritative Specification
**Purpose**: Complete runtime reliability and debugging system

---

## Executive Summary

This document defines the comprehensive runtime validation strategy for Risk Manager V34, preventing the "tests pass but runtime fails" syndrome. It establishes the 8-checkpoint validation system, runtime reliability pack, and troubleshooting procedures.

**Key Principle**: Unit and integration tests validate correctness, but **runtime validation** ensures deployment readiness and system liveness.

**The Problem**: Code can pass all tests but still fail at runtime due to:
- Environment configuration issues
- Missing dependencies
- API connectivity problems
- State management errors
- Resource availability issues
- Async task deadlocks

**The Solution**: Runtime Reliability Pack with 8 strategic checkpoints.

---

## 1. The Runtime Validation Philosophy

### 1.1 Why Runtime Testing Matters

**Traditional Testing** (Unit + Integration + E2E):
- ✅ Validates logic correctness
- ✅ Tests component interactions
- ✅ Verifies business workflows
- ❌ **Does NOT validate** system boots correctly
- ❌ **Does NOT validate** first event fires
- ❌ **Does NOT validate** environment is configured
- ❌ **Does NOT validate** resources are available

**Runtime Testing** (Smoke + Soak + Trace):
- ✅ Validates system boots in <8 seconds
- ✅ Validates first event fires
- ✅ Validates all 8 checkpoints complete
- ✅ Validates no deadlocks or hangs
- ✅ Validates environment configured correctly
- ✅ Validates resources available

**Result**: **BOTH** are required for production readiness!

### 1.2 The Two-Layer Validation Model

```
Layer 1: Logic Validation (pytest)
├── Unit tests validate function logic
├── Integration tests validate component interactions
└── E2E tests validate complete workflows
    └─> Result: Code is CORRECT ✅

Layer 2: Liveness Validation (Runtime Pack)
├── Smoke test validates system boots and runs
├── Soak test validates stability over time
├── Trace mode validates no deadlocks
└── Checkpoints validate boot sequence
    └─> Result: System is ALIVE and READY ✅

Both layers required for deployment!
```

---

## 2. The 8-Checkpoint System

### 2.1 Checkpoint Architecture

The 8-checkpoint system provides strategic logging at critical boot and operation points, allowing precise diagnosis of runtime failures.

```
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 1: 🚀 Service Start                                  │
│ Location: manager.py:start()                                    │
│ Log: "Risk Manager starting..."                                 │
│ Validates: System entry point reached                           │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 2: ✅ Config Loaded                                   │
│ Location: manager.py:_load_config()                             │
│ Log: "Config loaded: X rules"                                   │
│ Validates: YAML parsed, rules present                           │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 3: ✅ SDK Connected                                   │
│ Location: manager.py:_connect_sdk()                             │
│ Log: "SDK connected: account_id"                                │
│ Validates: API authentication succeeded                         │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 4: ✅ Rules Initialized                               │
│ Location: manager.py:_initialize_rules()                        │
│ Log: "Rules initialized: X rules"                               │
│ Validates: Rule objects created                                 │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 5: ✅ Event Loop Running                              │
│ Location: engine.py:start()                                     │
│ Log: "Event loop running"                                       │
│ Validates: Async event loop started                             │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 6: 📨 Event Received                                  │
│ Location: engine.py:handle_event()                              │
│ Log: "Event received: {event}"                                  │
│ Validates: First event arrived (LIVENESS PROOF)                 │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 7: 🔍 Rule Evaluated                                  │
│ Location: engine.py:handle_event()                              │
│ Log: "Rule evaluated: {rule} {result}"                          │
│ Validates: Rules processing events                              │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 8: ⚠️ Enforcement Triggered                           │
│ Location: enforcement.py:enforce()                              │
│ Log: "Enforcement triggered: {action}"                          │
│ Validates: SDK actions executed                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Checkpoint Implementation

#### Checkpoint 1: Service Start
**Purpose**: Prove system entry point reached

**Code Location**: `src/risk_manager/core/manager.py`

```python
async def start(self):
    """Start the Risk Manager system."""
    logger.info("🚀 Risk Manager starting...")  # CHECKPOINT 1

    try:
        await self._load_config()
        await self._connect_sdk()
        await self._initialize_rules()
        await self._start_event_loop()
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        raise
```

**Validation**: Check logs for 🚀 emoji

**Failure Modes**:
- Entry point never called → Check if service started
- Exception before log → Check Python/import errors

#### Checkpoint 2: Config Loaded
**Purpose**: Prove configuration parsed successfully

**Code Location**: `src/risk_manager/core/manager.py`

```python
async def _load_config(self):
    """Load configuration from YAML."""
    config_path = Path("config/risk_config.yaml")

    with open(config_path) as f:
        self.config = yaml.safe_load(f)

    rule_count = len(self.config.get("rules", {}))
    logger.info(f"✅ Config loaded: {rule_count} rules")  # CHECKPOINT 2
```

**Validation**: Check logs for ✅ Config loaded

**Failure Modes**:
- YAML syntax error → Fix config file
- Missing config file → Create from template
- Invalid config values → Validate against schema

#### Checkpoint 3: SDK Connected
**Purpose**: Prove API authentication succeeded

**Code Location**: `src/risk_manager/core/manager.py`

```python
async def _connect_sdk(self):
    """Connect to TopstepX SDK."""
    self.suite_manager = SuiteManager(
        api_key=self.config["api_key"],
        account_id=self.config["account_id"]
    )

    await self.suite_manager.connect()

    logger.info(f"✅ SDK connected: {self.config['account_id']}")  # CHECKPOINT 3
```

**Validation**: Check logs for ✅ SDK connected

**Failure Modes**:
- 401 Unauthorized → Check API credentials
- Network timeout → Check connectivity
- SDK import error → Check dependencies

#### Checkpoint 4: Rules Initialized
**Purpose**: Prove rule objects created

**Code Location**: `src/risk_manager/core/manager.py`

```python
async def _initialize_rules(self):
    """Initialize risk rules from config."""
    self.rules = []

    for rule_name, rule_config in self.config["rules"].items():
        if rule_config.get("enabled", False):
            rule_class = RULE_REGISTRY[rule_name]
            rule = rule_class(rule_config)
            self.rules.append(rule)

    logger.info(f"✅ Rules initialized: {len(self.rules)} rules")  # CHECKPOINT 4
```

**Validation**: Check logs for ✅ Rules initialized

**Failure Modes**:
- Rule class not found → Check imports
- Invalid rule config → Validate config
- Rule initialization error → Check rule logic

#### Checkpoint 5: Event Loop Running
**Purpose**: Prove async event loop started

**Code Location**: `src/risk_manager/core/engine.py`

```python
async def start(self):
    """Start the risk engine event loop."""
    self.running = True

    logger.info("✅ Event loop running")  # CHECKPOINT 5

    while self.running:
        try:
            event = await self.event_bus.get_event()
            await self.handle_event(event)
        except Exception as e:
            logger.error(f"Event handling error: {e}")
```

**Validation**: Check logs for ✅ Event loop running

**Failure Modes**:
- Loop never starts → Check async setup
- Loop starts but blocks → Check for blocking calls
- Loop exits immediately → Check exit conditions

#### Checkpoint 6: Event Received
**Purpose**: **LIVENESS PROOF** - Prove system is actually working

**Code Location**: `src/risk_manager/core/engine.py`

```python
async def handle_event(self, event: RiskEvent):
    """Handle a single risk event."""
    logger.info(f"📨 Event received: {event.event_type}")  # CHECKPOINT 6

    # Evaluate all rules
    for rule in self.rules:
        result = await rule.evaluate(event)
        logger.info(f"🔍 Rule evaluated: {rule.name} {result}")  # CHECKPOINT 7

        if result.violated:
            await self._enforce(result)
```

**Validation**: Check logs for 📨 Event received

**Failure Modes**:
- No events received → Check SDK subscriptions
- Events received but not logged → Check logging config
- Events stalled → Check async processing

**CRITICAL**: This checkpoint MUST occur within 8 seconds of boot for smoke test to pass!

#### Checkpoint 7: Rule Evaluated
**Purpose**: Prove rules are processing events

**Code Location**: `src/risk_manager/core/engine.py`

```python
async def handle_event(self, event: RiskEvent):
    """Handle a single risk event."""
    # ... (checkpoint 6 code)

    for rule in self.rules:
        result = await rule.evaluate(event)
        logger.info(f"🔍 Rule evaluated: {rule.name} {result}")  # CHECKPOINT 7
```

**Validation**: Check logs for 🔍 Rule evaluated

**Failure Modes**:
- Rules never evaluate → Check rule initialization
- Rules evaluate but wrong result → Check rule logic
- Rules crash → Check error handling

#### Checkpoint 8: Enforcement Triggered
**Purpose**: Prove SDK actions executed

**Code Location**: `src/risk_manager/sdk/enforcement.py`

```python
async def enforce(self, action: EnforcementAction):
    """Execute enforcement action via SDK."""
    logger.warning(f"⚠️ Enforcement triggered: {action.action_type}")  # CHECKPOINT 8

    if action.action_type == "FLATTEN_ALL":
        await self.suite.close_all_positions()
    elif action.action_type == "CANCEL_ORDERS":
        await self.suite.cancel_all_orders()
```

**Validation**: Check logs for ⚠️ Enforcement triggered

**Failure Modes**:
- Enforcement never called → Check rule violation detection
- SDK call fails → Check SDK integration
- Enforcement called but no effect → Check SDK response

### 2.3 Using Checkpoints for Debugging

#### Step 1: Run Smoke Test
```bash
python run_tests.py → [s]
```

**Possible Exit Codes**:
- `0` = Success (all 8 checkpoints reached)
- `1` = Exception (check logs for stack trace)
- `2` = Stalled (check which checkpoint was last)

#### Step 2: View Logs
```bash
python run_tests.py → [l]
# Or directly:
cat data/logs/risk_manager.log
```

#### Step 3: Find Last Checkpoint
```bash
# Look for emoji sequence
grep -E "🚀|✅|📨|🔍|⚠️" data/logs/risk_manager.log
```

**Example Output**:
```
2025-10-25 14:30:00 INFO 🚀 Risk Manager starting...
2025-10-25 14:30:01 INFO ✅ Config loaded: 3 rules
2025-10-25 14:30:02 INFO ✅ SDK connected: ACC-12345
2025-10-25 14:30:02 INFO ✅ Rules initialized: 3 rules
2025-10-25 14:30:02 INFO ✅ Event loop running
# ❌ STOPPED HERE - No events received!
```

**Diagnosis**: System booted successfully but no events are being received.

**Solution**: Check SDK event subscriptions!

#### Step 4: Fix Based on Checkpoint

**Stopped at Checkpoint 1**: System never started
- Check if service/process is running
- Check Python/import errors
- Check entry point configuration

**Stopped at Checkpoint 2**: Config loading failed
- Check YAML syntax
- Check file permissions
- Validate config values

**Stopped at Checkpoint 3**: SDK connection failed
- Check API credentials (.env file)
- Check network connectivity
- Check SDK version compatibility

**Stopped at Checkpoint 4**: Rules initialization failed
- Check rule imports
- Check rule configuration
- Check rule dependencies

**Stopped at Checkpoint 5**: Event loop failed
- Check async setup
- Check blocking calls
- Check exit conditions

**Stopped at Checkpoint 6**: No events received (MOST COMMON)
- Check SDK event subscriptions
- Check event bridge wiring
- Check account has activity
- **This is why smoke test times out!**

**Stopped at Checkpoint 7**: Rules not evaluating
- Check rule logic
- Check rule configuration
- Check error handling

**Stopped at Checkpoint 8**: Enforcement not triggering
- Check violation detection
- Check enforcement thresholds
- Check SDK integration

---

## 3. Runtime Reliability Pack

The Runtime Reliability Pack provides 5 critical validation capabilities.

### 3.1 Smoke Test (8s Boot Validation)

**Purpose**: Validate system boots and first event fires within 8 seconds

**What it tests**:
- System starts without errors
- All 8 checkpoints complete
- First event received within 8s
- No deadlocks or hangs
- Basic system liveness

**When to run**:
- After pytest passes
- Before deployment
- After environment changes
- After significant code changes

**How to run**:
```bash
python run_tests.py → [s]
```

**Exit Codes**:
- `0` = SUCCESS - System is live and ready ✅
- `1` = EXCEPTION - Check logs for stack trace ❌
- `2` = STALLED - Boot took >8s or no events ⚠️

**Implementation**: `src/runtime/smoke_test.py`

```python
async def smoke_test(timeout: float = 8.0) -> int:
    """
    Smoke test: Boot system and validate first event within timeout.

    Returns:
        0: Success (first event observed)
        1: Exception occurred
        2: Boot stalled (no events within timeout)
    """
    try:
        manager = RiskManager(config)

        start_time = time.time()
        await manager.start()

        # Wait for first event (max 8s)
        for _ in range(int(timeout * 10)):
            if manager._events_processed > 0:
                elapsed = time.time() - start_time
                logger.info(f"✅ Smoke test PASSED: First event after {elapsed:.1f}s")
                return 0  # SUCCESS

            await asyncio.sleep(0.1)

        # Timeout - no events
        logger.error(f"⚠️ Smoke test STALLED: No events after {timeout}s")
        return 2  # STALLED

    except Exception as e:
        logger.error(f"❌ Smoke test EXCEPTION: {e}")
        return 1  # EXCEPTION
```

**Example Output (Success)**:
```
🚀 Risk Manager starting...
✅ Config loaded: 3 rules
✅ SDK connected: ACC-12345
✅ Rules initialized: 3 rules
✅ Event loop running
📨 Event received: POSITION_UPDATED
✅ Smoke test PASSED: First event after 2.3s

Exit Code: 0
```

**Example Output (Stalled)**:
```
🚀 Risk Manager starting...
✅ Config loaded: 3 rules
✅ SDK connected: ACC-12345
✅ Rules initialized: 3 rules
✅ Event loop running
⚠️ Smoke test STALLED: No events after 8.0s

Exit Code: 2
```

### 3.2 Soak Test (30-60s Stability Validation)

**Purpose**: Validate system stability over extended runtime

**What it tests**:
- Memory usage remains stable
- No memory leaks
- No resource exhaustion
- No async task buildup
- Performance consistent

**When to run**:
- Before major deployments
- After performance optimizations
- When investigating memory issues
- Before production release

**How to run**:
```bash
python run_tests.py → [r]
```

**Duration**: 30-60 seconds

**Implementation**: `src/runtime/soak_test.py`

```python
async def soak_test(duration: int = 60) -> dict:
    """
    Soak test: Run system for extended period and monitor health.

    Args:
        duration: How long to run (seconds)

    Returns:
        dict: Health metrics
    """
    manager = RiskManager(config)
    await manager.start()

    metrics = {
        "start_memory_mb": get_memory_usage(),
        "events_processed": 0,
        "peak_memory_mb": 0,
        "duration_seconds": duration
    }

    start_time = time.time()

    while time.time() - start_time < duration:
        # Monitor metrics
        current_memory = get_memory_usage()
        metrics["peak_memory_mb"] = max(metrics["peak_memory_mb"], current_memory)
        metrics["events_processed"] = manager._events_processed

        await asyncio.sleep(1)

    metrics["end_memory_mb"] = get_memory_usage()
    metrics["memory_leak_mb"] = metrics["end_memory_mb"] - metrics["start_memory_mb"]

    # Validate no memory leak
    if metrics["memory_leak_mb"] > 50:  # More than 50MB leak
        logger.warning(f"⚠️ Potential memory leak: {metrics['memory_leak_mb']}MB")
    else:
        logger.info(f"✅ Memory stable: {metrics['memory_leak_mb']}MB growth")

    return metrics
```

**Example Output**:
```
Soak Test Results (60s):
  Start Memory: 45.2 MB
  End Memory: 47.8 MB
  Peak Memory: 52.1 MB
  Memory Growth: 2.6 MB
  Events Processed: 342
  Events/Second: 5.7

✅ Memory stable: 2.6MB growth
✅ Performance consistent
✅ No resource exhaustion detected

Exit Code: 0
```

### 3.3 Trace Mode (Deep Async Debugging)

**Purpose**: Debug async task deadlocks and hangs

**What it outputs**:
- All pending async tasks
- Task call stacks
- Task durations
- Blocked tasks
- Event loop state

**When to run**:
- Service starts but hangs
- Slow performance
- Suspected deadlock
- Async issues

**How to run**:
```bash
python run_tests.py → [t]
# Or with env var:
ASYNC_DEBUG=1 python risk_manager/main.py
```

**Output Location**: `runtime_trace.log`

**Implementation**: `src/runtime/async_debug.py`

```python
def dump_async_tasks():
    """Dump all pending async tasks for debugging."""
    tasks = asyncio.all_tasks()

    logger.info(f"=== Async Task Dump ({len(tasks)} tasks) ===")

    for task in tasks:
        if not task.done():
            stack = task.get_stack()
            logger.info(f"Task: {task.get_name()}")
            logger.info(f"  State: PENDING")
            logger.info(f"  Stack: {stack}")

    logger.info("=== End Task Dump ===")
```

**Example Output**:
```
=== Async Task Dump (5 tasks) ===
Task: event_loop
  State: PENDING
  Stack: [<frame at engine.py:45>, <frame at manager.py:123>]

Task: heartbeat_monitor
  State: PENDING
  Stack: [<frame at heartbeat.py:12>]

Task: sdk_listener
  State: PENDING (BLOCKED - waiting for SDK event!)
  Stack: [<frame at event_bridge.py:67>]

=== End Task Dump ===

Diagnosis: sdk_listener blocked waiting for events
```

### 3.4 Log Viewer

**Purpose**: Stream logs in real-time or view recent logs

**What it shows**:
- All 8 checkpoint logs
- Event processing logs
- Error messages
- Warning messages
- Debug information

**When to use**:
- Debugging runtime issues
- Monitoring system behavior
- Investigating errors
- Tracking event flow

**How to run**:
```bash
python run_tests.py → [l]
```

**Options**:
- View last 100 lines
- Stream in real-time
- Filter by level (INFO, WARNING, ERROR)
- Search by keyword

**Log Location**: `data/logs/risk_manager.log`

**Implementation**: Uses standard Python logging

```python
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('data/logs/risk_manager.log'),
        logging.StreamHandler()
    ]
)
```

### 3.5 Environment Snapshot

**Purpose**: Capture complete environment configuration

**What it captures**:
- Python version
- Installed packages
- Environment variables
- Configuration files
- System resources
- Network connectivity

**When to use**:
- Configuration troubleshooting
- "Works on my machine" issues
- Environment comparison
- Deployment verification

**How to run**:
```bash
python run_tests.py → [e]
```

**Output**:
```
=== Environment Snapshot ===

System:
  OS: Linux 6.6.87.2-microsoft-standard-WSL2
  Python: 3.12.1
  Working Dir: /mnt/c/Users/jakers/Desktop/risk-manager-v34

Dependencies:
  topstepx-sdk: 3.5.9
  pydantic: 2.5.0
  pytest: 7.4.3
  PyYAML: 6.0.1

Environment Variables:
  TOPSTEPX_API_KEY: ***hidden***
  TOPSTEPX_ACCOUNT_ID: ACC-12345
  DRY_RUN_MODE: False
  ASYNC_DEBUG: False

Configuration:
  risk_config.yaml: ✅ Exists, valid YAML
  accounts.yaml: ✅ Exists, 1 account configured
  .env: ✅ Exists, credentials present

Resources:
  CPU Usage: 12%
  Memory Usage: 45.2 MB / 8.0 GB
  Disk Space: 256 GB free

Network:
  Internet: ✅ Connected
  TopstepX API: ✅ Reachable (ping: 34ms)

=== End Snapshot ===
```

---

## 4. Exit Codes and Meanings

### 4.1 Exit Code Definitions

| Code | Name | Meaning | Action |
|------|------|---------|--------|
| 0 | SUCCESS | System fully operational | ✅ Deploy |
| 1 | EXCEPTION | Runtime exception occurred | ❌ Check logs for stack trace |
| 2 | STALLED | Boot >8s or no events | ⚠️ Check subscriptions/checkpoints |
| 3 | CONFIG_ERROR | Configuration invalid | ❌ Fix YAML files |
| 4 | API_ERROR | SDK connection failed | ❌ Check credentials |
| 5 | DEPENDENCY_ERROR | Missing dependencies | ❌ Run pip install |

### 4.2 Exit Code Workflow

```bash
# Run smoke test
python run_tests.py → [s]

# Check exit code
echo $?

# Exit code 0:
  ✅ System is live and ready
  ✅ All checkpoints passed
  ✅ First event observed
  → Safe to deploy

# Exit code 1:
  ❌ Exception occurred
  → View logs: python run_tests.py → [l]
  → Fix error
  → Rerun smoke test

# Exit code 2:
  ⚠️ Boot stalled or no events
  → Check which checkpoint failed
  → Check event subscriptions
  → Check SDK wiring
  → Rerun smoke test
```

---

## 5. Troubleshooting Flowchart

### 5.1 Smoke Test Fails (Exit Code 1 or 2)

```
Smoke Test Failed
    │
    ▼
Check Exit Code
    │
    ├─> Exit Code 1 (EXCEPTION)
    │   │
    │   ▼
    │   View Logs: python run_tests.py → [l]
    │   │
    │   ▼
    │   Find stack trace
    │   │
    │   ├─> ImportError → pip install missing package
    │   ├─> ConfigError → Fix YAML syntax
    │   ├─> APIError → Check credentials
    │   └─> Other → Debug specific error
    │
    └─> Exit Code 2 (STALLED)
        │
        ▼
        Find Last Checkpoint
        │
        ├─> Stopped at Checkpoint 1-5: Boot failure
        │   └─> Debug component initialization
        │
        └─> Stopped at Checkpoint 5: No events
            │
            ▼
            Check Event Subscriptions
            │
            ├─> SDK not publishing events?
            │   └─> Check SDK configuration
            │
            ├─> EventBridge not mapping?
            │   └─> Check event_bridge.py
            │
            └─> EventBus not dispatching?
                └─> Check event_bus.py
```

### 5.2 Performance Issues

```
Slow Performance
    │
    ▼
Run Soak Test: python run_tests.py → [r]
    │
    ▼
Check Metrics
    │
    ├─> Memory growing >50MB?
    │   └─> Memory leak! Find allocation source
    │
    ├─> Events/second < expected?
    │   └─> Performance bottleneck! Profile code
    │
    └─> CPU usage high?
        └─> Optimization needed! Find hot spots
```

### 5.3 Async Deadlocks

```
Service Hangs
    │
    ▼
Run Trace Mode: python run_tests.py → [t]
    │
    ▼
Check Pending Tasks
    │
    ├─> Task stuck in PENDING?
    │   └─> Find blocking call
    │
    ├─> Multiple tasks waiting on each other?
    │   └─> Deadlock! Refactor dependencies
    │
    └─> Task never completing?
        └─> Infinite loop! Add timeout
```

---

## 6. Best Practices

### 6.1 DO

✅ **Run smoke test after pytest** - Validate logic AND liveness
✅ **Check all 8 checkpoints** - Find exactly where runtime fails
✅ **Use exit codes** - Automate deployment decisions
✅ **Run soak test before major deploys** - Catch stability issues
✅ **Use trace mode for hangs** - Debug async issues
✅ **View logs first** - Most issues are obvious in logs
✅ **Take environment snapshots** - Compare working vs broken

### 6.2 DON'T

❌ **Deploy without smoke test passing** - Exit code must be 0
❌ **Ignore exit code 2** - Stalled boot will fail in production
❌ **Skip soak test** - Memory leaks only show over time
❌ **Ignore checkpoint gaps** - Missing checkpoints indicate issues
❌ **Guess at problems** - Use trace mode to see actual state

---

## 7. Integration with Test Suite

### 7.1 Complete Testing Workflow

```
Step 1: Write Tests (TDD)
  └─> Unit tests → Integration tests → E2E tests

Step 2: Run pytest
  └─> python run_tests.py → [1] (all tests)
  └─> Check: test_reports/latest.txt
  └─> Result: ✅ All tests pass (logic correct)

Step 3: Run Smoke Test
  └─> python run_tests.py → [s]
  └─> Check: Exit code
  └─> Result: 0 = SUCCESS (system live)
           1 = EXCEPTION (fix and retry)
           2 = STALLED (check checkpoints)

Step 4: (Optional) Run Soak Test
  └─> python run_tests.py → [r]
  └─> Check: Memory growth, performance
  └─> Result: ✅ System stable (for major deploys)

Step 5: Deploy
  └─> Only if: pytest passed AND smoke test exit code 0
```

### 7.2 Gate Test (Combined Validation)

**Purpose**: Single command for complete validation

**How to run**:
```bash
python run_tests.py → [g]
```

**What it does**:
1. Runs unit tests
2. Runs integration tests
3. Runs smoke test
4. Checks all exit codes
5. Returns 0 only if ALL pass

**Usage**:
```bash
# Pre-deployment check
python run_tests.py → [g]

if [ $? -eq 0 ]; then
  echo "✅ READY TO DEPLOY"
  ./deploy.sh
else
  echo "❌ NOT READY - Fix issues"
  exit 1
fi
```

---

## 8. CI/CD Integration

### 8.1 GitHub Actions Workflow (Future)

```yaml
name: Test and Validate

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run pytest
        run: |
          .venv/bin/pytest --cov=src --cov-fail-under=90

      - name: Run smoke test
        run: |
          .venv/bin/python run_tests.py --smoke-test-only

      - name: Check exit code
        run: |
          if [ $? -ne 0 ]; then
            echo "❌ Smoke test failed!"
            exit 1
          fi

      - name: (Optional) Run soak test
        if: github.event_name == 'pull_request' && contains(github.event.pull_request.labels.*.name, 'major-deploy')
        run: |
          .venv/bin/python run_tests.py --soak-test
```

### 8.2 Pre-Deployment Validation Script

```bash
#!/bin/bash
# deploy_check.sh - Pre-deployment validation

echo "🚀 Starting pre-deployment validation..."

# Step 1: Run all tests
echo "Step 1: Running pytest..."
pytest --cov=src --cov-fail-under=90
if [ $? -ne 0 ]; then
  echo "❌ Tests failed!"
  exit 1
fi

# Step 2: Run smoke test
echo "Step 2: Running smoke test..."
python run_tests.py --smoke-test-only
SMOKE_EXIT_CODE=$?

if [ $SMOKE_EXIT_CODE -eq 0 ]; then
  echo "✅ READY TO DEPLOY"
  exit 0
elif [ $SMOKE_EXIT_CODE -eq 1 ]; then
  echo "❌ Smoke test EXCEPTION - Check logs"
  python run_tests.py --view-logs
  exit 1
elif [ $SMOKE_EXIT_CODE -eq 2 ]; then
  echo "⚠️ Smoke test STALLED - Check checkpoints"
  grep -E "🚀|✅|📨|🔍|⚠️" data/logs/risk_manager.log
  exit 2
fi
```

---

## 9. Related Documentation

**Testing Strategy**:
- `testing-strategy.md` - Complete testing approach
- `test-coverage-requirements.md` - Coverage targets

**Testing Guides**:
- `docs/testing/TESTING_GUIDE.md` - How to write tests
- `docs/testing/RUNTIME_DEBUGGING.md` - Original runtime guide
- `docs/testing/WORKING_WITH_AI.md` - AI-assisted testing

**API Contracts**:
- `SDK_API_REFERENCE.md` - Actual API signatures
- `SDK_ENFORCEMENT_FLOW.md` - Enforcement wiring

---

**Last Updated**: 2025-10-25
**Version**: 1.0
**Status**: Authoritative Specification
**Maintainer**: Development Team
