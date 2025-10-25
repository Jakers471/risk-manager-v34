# Runtime Debugging Guide - Risk Manager V34

**THE comprehensive guide for runtime reliability testing and debugging.**

---

## Table of Contents

1. [Overview](#overview)
2. [Runtime Reliability Pack](#runtime-reliability-pack)
3. [Interactive Debug Menu](#interactive-debug-menu)
4. [Checkpoint System](#checkpoint-system)
5. [Troubleshooting Flowchart](#troubleshooting-flowchart)
6. [Exit Codes](#exit-codes)
7. [Log Interpretation](#log-interpretation)
8. [Common Failures & Fixes](#common-failures--fixes)
9. [Best Practices](#best-practices)

---

## Overview

Runtime debugging ensures your risk manager behaves correctly when deployed, not just when tested. This guide covers the **Runtime Reliability Pack** - a comprehensive suite of tools for validating runtime behavior.

**Key Principle:** Tests can pass but code can still fail at runtime due to:
- Environment configuration issues
- Missing dependencies
- API connectivity problems
- State management errors
- Resource availability

The Runtime Reliability Pack catches these issues **before** they impact production trading.

---

## Runtime Reliability Pack

The Runtime Reliability Pack provides 5 critical capabilities:

### 1. Environment Validation
**What it checks:**
- Python version compatibility
- Required dependencies installed
- Configuration files exist
- Environment variables set
- Directory structure correct

**Example:**
```python
def validate_environment():
    """Runtime checkpoint: Environment validation"""
    # Check Python version
    assert sys.version_info >= (3, 12), "Python 3.12+ required"

    # Check critical dependencies
    try:
        import topstepx_sdk
        import yaml
        import pydantic
    except ImportError as e:
        raise RuntimeError(f"Missing dependency: {e}")

    # Check config files exist
    assert Path("config/risk_config.yaml").exists(), "Missing risk config"
    assert Path("config/accounts.yaml").exists(), "Missing accounts config"
```

### 2. Configuration Loading
**What it checks:**
- YAML syntax is valid
- Required fields present
- Values within valid ranges
- Cross-field validation
- Template vs real config

**Example:**
```python
def load_and_validate_config():
    """Runtime checkpoint: Configuration loading"""
    config_path = Path("config/risk_config.yaml")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Validate structure
    assert "rules" in config, "Missing 'rules' section"
    assert "daily_realized_loss" in config["rules"], "Missing loss rule"

    # Validate values
    daily_loss = config["rules"]["daily_realized_loss"]
    assert daily_loss["enabled"] is True, "Loss rule must be enabled"
    assert daily_loss["limit"] < 0, "Loss limit must be negative"
```

### 3. Component Initialization
**What it checks:**
- Objects instantiate correctly
- Dependencies injected properly
- State initialized
- Resources allocated
- No circular dependencies

**Example:**
```python
def initialize_components():
    """Runtime checkpoint: Component initialization"""
    # Initialize P&L tracker
    pnl_tracker = PnLTracker()
    assert pnl_tracker is not None, "PnL tracker failed to initialize"

    # Initialize state manager
    state_mgr = StateManager()
    assert state_mgr.accounts == {}, "State should start empty"

    # Initialize rule engine
    rule_engine = RuleEngine(config, pnl_tracker, state_mgr)
    assert len(rule_engine.rules) > 0, "No rules loaded"
```

### 4. API Connectivity
**What it checks:**
- API client instantiates
- Authentication succeeds
- Test API calls work
- Rate limiting configured
- Error handling functional

**Example:**
```python
def test_api_connectivity():
    """Runtime checkpoint: API connectivity"""
    from risk_manager.api.client import TopstepXClient

    # Initialize client
    client = TopstepXClient()

    # Test authentication
    try:
        client.authenticate()
        assert client.is_authenticated, "Authentication failed"
    except Exception as e:
        raise RuntimeError(f"API auth failed: {e}")

    # Test basic API call
    try:
        accounts = client.get_accounts()
        assert isinstance(accounts, list), "Invalid accounts response"
    except Exception as e:
        raise RuntimeError(f"API call failed: {e}")
```

### 5. State Management
**What it checks:**
- State updates correctly
- State persists across operations
- State recovery works
- Concurrent access safe
- Memory leaks prevented

**Example:**
```python
def test_state_management():
    """Runtime checkpoint: State management"""
    state_mgr = StateManager()

    # Test state update
    account_id = 12345
    position = {"symbol": "MNQ", "size": 1, "price": 15000.0}
    state_mgr.update_position(account_id, position)

    # Verify state
    assert account_id in state_mgr.accounts, "Account not in state"
    assert "MNQ" in state_mgr.get_positions(account_id), "Position not stored"

    # Test state persistence
    state_mgr.save_state()

    # Test state recovery
    new_mgr = StateManager()
    new_mgr.load_state()
    assert account_id in new_mgr.accounts, "State not recovered"
```

---

## Interactive Debug Menu

The runtime debugger provides an interactive menu for comprehensive system validation.

### Accessing the Menu

```bash
python run_tests.py
# Select: [S] Runtime System Check
```

### Menu Options

```
╔════════════════════════════════════════════════════════════════════╗
║              Runtime Reliability Debugger - V34                    ║
╚════════════════════════════════════════════════════════════════════╝

Select debugging mode:

  [S] System Health Check     - Full environment validation
  [R] Runtime Diagnostics     - Component initialization test
  [T] Test API Connection     - Verify TopstepX connectivity
  [L] Load Configurations     - Validate YAML configs
  [E] End-to-End Flow        - Complete workflow test
  [G] Generate Debug Report   - Full diagnostic output

  [V] Verbose Mode: OFF       - Toggle detailed logging
  [Q] Quit
```

### Menu Commands Explained

#### [S] System Health Check
**What it does:**
- Validates Python version
- Checks installed dependencies
- Verifies directory structure
- Tests file permissions
- Validates environment variables

**When to use:**
- First-time setup
- After environment changes
- Deployment to new server
- Troubleshooting "works on my machine"

**Output:**
```
✓ Python 3.12.1 detected
✓ All required packages installed
✓ Config directory exists: config/
✓ Data directory exists: data/
✓ Logs directory writable: logs/
✓ Environment variables set (5/5)

System Health: PASS (Exit Code: 0)
```

#### [R] Runtime Diagnostics
**What it does:**
- Initializes all core components
- Tests dependency injection
- Verifies state management
- Checks resource allocation
- Tests component interactions

**When to use:**
- After code changes to core classes
- Before deploying new features
- Investigating initialization errors
- Validating refactoring

**Output:**
```
✓ PnLTracker initialized
✓ StateManager initialized
✓ RuleEngine initialized (7 rules loaded)
✓ EventBus initialized
✓ Components linked correctly

Runtime Diagnostics: PASS (Exit Code: 0)
```

#### [T] Test API Connection
**What it does:**
- Initializes API client
- Tests authentication
- Makes sample API calls
- Validates response formats
- Tests error handling

**When to use:**
- New API credentials
- Network connectivity issues
- API version changes
- Rate limiting problems
- Authentication failures

**Output:**
```
✓ API client initialized
✓ Authentication successful
✓ GET /accounts responded (200)
✓ GET /positions responded (200)
✓ Rate limiter configured (60 req/min)

API Connection: PASS (Exit Code: 0)
```

#### [L] Load Configurations
**What it does:**
- Parses YAML files
- Validates structure
- Checks required fields
- Tests value ranges
- Detects template configs

**When to use:**
- After editing configs
- Configuration errors
- Deployment to new environment
- Validating user changes

**Output:**
```
✓ risk_config.yaml loaded
✓ accounts.yaml loaded
✓ All required fields present
✓ Value ranges validated
⚠ Using template config (accounts.yaml.template detected)

Configuration: WARNING (Exit Code: 1)
```

#### [E] End-to-End Flow
**What it does:**
- Runs complete trading workflow
- Tests all components together
- Validates state transitions
- Tests error recovery
- Measures performance

**When to use:**
- Pre-deployment validation
- Integration testing
- Performance benchmarking
- Regression testing

**Output:**
```
✓ System initialized
✓ Account loaded (ID: 12345)
✓ Position updated (MNQ +1)
✓ Trade processed (PnL: -$50)
✓ Rule evaluated (No breach)
✓ State persisted
✓ Cleanup completed

E2E Flow: PASS (Execution time: 0.234s, Exit Code: 0)
```

#### [G] Generate Debug Report
**What it does:**
- Runs all checks
- Collects system info
- Captures logs
- Creates comprehensive report
- Saves to file

**When to use:**
- Reporting bugs
- Support requests
- Performance analysis
- Audit trails

**Output:**
```
Generating debug report...

✓ System health: PASS
✓ Runtime diagnostics: PASS
✓ API connection: PASS
⚠ Configuration: WARNING
✓ E2E flow: PASS

Report saved: debug_reports/2025-10-23_14-30-45_debug.txt

Debug Report: COMPLETE (Exit Code: 0)
```

---

## Checkpoint System

The Runtime Reliability Pack uses an 8-checkpoint validation system.

### Checkpoint Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 1: Environment Validation                            │
│ ✓ Python version, dependencies, file structure                 │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 2: Configuration Loading                             │
│ ✓ Parse YAML, validate structure, check values                 │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 3: Component Initialization                          │
│ ✓ PnLTracker, StateManager, RuleEngine                         │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 4: API Connectivity                                  │
│ ✓ Client init, authentication, test calls                      │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 5: State Management                                  │
│ ✓ Update, persist, recover state                               │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 6: Rule Evaluation                                   │
│ ✓ Rules load, evaluate, trigger correctly                      │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 7: Event Handling                                    │
│ ✓ Events publish, subscribe, dispatch                          │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT 8: Resource Cleanup                                  │
│ ✓ Close connections, save state, release resources             │
└─────────────────────────────────────────────────────────────────┘
```

### Checkpoint Examples

#### Checkpoint 1: Environment Validation
```python
# File: tests/runtime/test_checkpoint_01_environment.py

def test_checkpoint_01_environment():
    """CHECKPOINT 1: Validate runtime environment"""

    # Python version
    assert sys.version_info >= (3, 12), \
        f"Python 3.12+ required, got {sys.version_info}"

    # Required packages
    required = ["topstepx_sdk", "yaml", "pydantic", "pytest"]
    for package in required:
        assert importlib.util.find_spec(package), \
            f"Missing required package: {package}"

    # Directory structure
    required_dirs = ["config", "data", "logs", "tests"]
    for dir_name in required_dirs:
        path = Path(dir_name)
        assert path.exists(), f"Missing directory: {dir_name}"
        assert path.is_dir(), f"Not a directory: {dir_name}"
```

#### Checkpoint 2: Configuration Loading
```python
# File: tests/runtime/test_checkpoint_02_config.py

def test_checkpoint_02_configuration():
    """CHECKPOINT 2: Load and validate configurations"""

    # Load risk config
    risk_config_path = Path("config/risk_config.yaml")
    assert risk_config_path.exists(), "Missing risk_config.yaml"

    with open(risk_config_path) as f:
        risk_config = yaml.safe_load(f)

    # Validate structure
    assert "rules" in risk_config, "Missing 'rules' section"
    assert "daily_realized_loss" in risk_config["rules"], \
        "Missing daily_realized_loss rule"

    # Validate values
    loss_rule = risk_config["rules"]["daily_realized_loss"]
    assert loss_rule["enabled"] is True, "Loss rule must be enabled"
    assert loss_rule["limit"] < 0, "Loss limit must be negative"
    assert loss_rule["limit"] >= -10000, "Loss limit unreasonably large"
```

#### Checkpoint 3: Component Initialization
```python
# File: tests/runtime/test_checkpoint_03_components.py

def test_checkpoint_03_components():
    """CHECKPOINT 3: Initialize core components"""

    # Initialize PnL tracker
    pnl_tracker = PnLTracker()
    assert pnl_tracker is not None, "PnL tracker init failed"
    assert hasattr(pnl_tracker, "add_trade"), "Missing add_trade method"

    # Initialize state manager
    state_mgr = StateManager()
    assert state_mgr is not None, "State manager init failed"
    assert state_mgr.accounts == {}, "State should start empty"

    # Initialize rule engine
    config = load_config("config/risk_config.yaml")
    rule_engine = RuleEngine(config, pnl_tracker, state_mgr)
    assert len(rule_engine.rules) > 0, "No rules loaded"
    assert "daily_realized_loss" in rule_engine.rules, \
        "Critical rule missing"
```

#### Checkpoint 4: API Connectivity
```python
# File: tests/runtime/test_checkpoint_04_api.py

@pytest.mark.integration
def test_checkpoint_04_api_connectivity():
    """CHECKPOINT 4: Test API connectivity"""

    # Initialize client
    client = TopstepXClient()
    assert client is not None, "API client init failed"

    # Test authentication
    try:
        client.authenticate()
        assert client.is_authenticated, "Authentication failed"
    except Exception as e:
        pytest.fail(f"Auth exception: {e}")

    # Test API call
    try:
        accounts = client.get_accounts()
        assert isinstance(accounts, list), "Invalid accounts response"
        assert len(accounts) >= 0, "Unexpected accounts format"
    except Exception as e:
        pytest.fail(f"API call failed: {e}")
```

#### Checkpoint 5: State Management
```python
# File: tests/runtime/test_checkpoint_05_state.py

def test_checkpoint_05_state_management():
    """CHECKPOINT 5: Validate state management"""

    state_mgr = StateManager()

    # Test state update
    account_id = 12345
    position = {
        "contract_id": "CON.F.US.MNQ.U25",
        "symbol": "MNQ",
        "size": 1,
        "average_price": 15000.0
    }

    state_mgr.update_position(account_id, position)

    # Verify state
    assert account_id in state_mgr.accounts, "Account not in state"
    positions = state_mgr.get_positions(account_id)
    assert "MNQ" in [p["symbol"] for p in positions], \
        "Position not stored"

    # Test state persistence
    state_mgr.save_state("data/test_state.json")

    # Test state recovery
    new_mgr = StateManager()
    new_mgr.load_state("data/test_state.json")
    assert account_id in new_mgr.accounts, "State not recovered"
```

#### Checkpoint 6: Rule Evaluation
```python
# File: tests/runtime/test_checkpoint_06_rules.py

def test_checkpoint_06_rule_evaluation():
    """CHECKPOINT 6: Test rule evaluation"""

    # Setup
    config = load_config("config/risk_config.yaml")
    pnl_tracker = PnLTracker()
    state_mgr = StateManager()
    rule_engine = RuleEngine(config, pnl_tracker, state_mgr)

    # Create test trade
    trade = {
        "accountId": 12345,
        "symbol": "MNQ",
        "profitAndLoss": -100.0,
        "executedTime": datetime.now().isoformat()
    }

    # Add to tracker
    pnl_tracker.add_trade(12345, -100.0)

    # Evaluate rules
    breaches = rule_engine.evaluate_all(trade)

    # Verify rules executed
    assert isinstance(breaches, list), "Invalid breaches format"
    # Should not breach on $100 loss
    assert len([b for b in breaches if b.severity == "CRITICAL"]) == 0, \
        "Unexpected critical breach"
```

#### Checkpoint 7: Event Handling
```python
# File: tests/runtime/test_checkpoint_07_events.py

def test_checkpoint_07_event_handling():
    """CHECKPOINT 7: Test event system"""

    event_bus = EventBus()

    # Test event subscription
    received_events = []

    def handler(event):
        received_events.append(event)

    event_bus.subscribe("trade.executed", handler)

    # Test event publishing
    event = {
        "type": "trade.executed",
        "account_id": 12345,
        "symbol": "MNQ",
        "pnl": -50.0
    }

    event_bus.publish(event)

    # Verify event received
    assert len(received_events) == 1, "Event not received"
    assert received_events[0]["type"] == "trade.executed", \
        "Wrong event type"
```

#### Checkpoint 8: Resource Cleanup
```python
# File: tests/runtime/test_checkpoint_08_cleanup.py

def test_checkpoint_08_cleanup():
    """CHECKPOINT 8: Test resource cleanup"""

    # Setup components
    pnl_tracker = PnLTracker()
    state_mgr = StateManager()
    client = TopstepXClient()

    # Use components
    pnl_tracker.add_trade(12345, -50.0)
    state_mgr.update_position(12345, {"symbol": "MNQ"})

    # Cleanup
    state_mgr.save_state("data/final_state.json")

    if hasattr(client, "disconnect"):
        client.disconnect()

    # Verify cleanup
    state_path = Path("data/final_state.json")
    assert state_path.exists(), "State not saved"

    # Verify no lingering resources
    import gc
    gc.collect()
    # Check for leaked resources here
```

---

## Troubleshooting Flowchart

```
START: Runtime Test Failure
         │
         ▼
   ┌─────────────┐
   │ Which Exit  │
   │    Code?    │
   └─────┬───────┘
         │
    ┌────┴────┬──────────┬────────────┐
    ▼         ▼          ▼            ▼
  EXIT 0    EXIT 1     EXIT 2      OTHER
  (Pass)  (Config)  (Runtime)    (Unknown)
    │         │          │            │
    ▼         │          │            │
  DONE       │          │            │
             │          │            │
         ┌───▼──────────▼────────────▼────┐
         │ Read test_reports/latest.txt   │
         └───┬────────────────────────────┘
             │
         ┌───▼────────────────────┐
         │ Identify Failed        │
         │ Checkpoint (1-8)       │
         └───┬────────────────────┘
             │
    ┌────────┴────────┬──────────┬──────────┬──────────┐
    ▼                 ▼          ▼          ▼          ▼
CHECKPOINT 1      CHECKPOINT 2  CP 3-8   ERROR MSG  STACK TRACE
Environment       Configuration  (others) Analysis   Analysis
    │                 │            │         │          │
    ▼                 ▼            ▼         ▼          ▼
┌─────────┐      ┌─────────┐  ┌─────────┐ ┌──────┐ ┌─────────┐
│Check:   │      │Check:   │  │ See     │ │Match │ │Find     │
│-Python  │      │-YAML    │  │specific │ │against│ │failing  │
│ version │      │ syntax  │  │CP guide │ │common │ │line     │
│-Packages│      │-Required│  │below    │ │errors │ │number   │
│-Dirs    │      │ fields  │  │         │ │table  │ │         │
│-Perms   │      │-Values  │  │         │ │       │ │         │
└────┬────┘      └────┬────┘  └────┬────┘ └───┬───┘ └────┬────┘
     │                │            │          │         │
     └────────┬───────┴────────────┴──────────┴─────────┘
              ▼
        ┌─────────────┐
        │ Apply Fix   │
        └─────┬───────┘
              ▼
        ┌─────────────┐
        │ Rerun Test  │
        └─────┬───────┘
              ▼
        ┌─────────────┐
        │  PASS? ─────┼──YES──> DONE
        └─────┬───────┘
              │
              NO
              │
              ▼
        ┌─────────────┐
        │ Try Next    │
        │ Solution    │
        └─────────────┘
```

### Decision Tree

1. **Exit Code 0 (PASS)**
   - All checkpoints passed
   - System ready for use
   - Action: None required

2. **Exit Code 1 (Configuration Error)**
   - Check: YAML syntax
   - Check: Required fields present
   - Check: Value ranges
   - Check: Template vs real config
   - Action: Fix configuration files

3. **Exit Code 2 (Runtime Error)**
   - Check: Failed checkpoint number
   - Check: Error message details
   - Check: Stack trace
   - Action: Fix code or environment

4. **Other Exit Codes**
   - Check: Test framework error
   - Check: System resources
   - Check: Permissions
   - Action: Investigate system issues

---

## Exit Codes

The runtime debugger uses a standardized exit code system:

### Exit Code Reference

| Code | Meaning | Description | Action Required |
|------|---------|-------------|-----------------|
| **0** | SUCCESS | All checks passed | None - system healthy |
| **1** | CONFIG_ERROR | Configuration invalid | Fix YAML files |
| **2** | RUNTIME_ERROR | Runtime failure | Fix code/environment |
| **3** | API_ERROR | API connectivity failed | Check credentials/network |
| **4** | STATE_ERROR | State management failed | Check data directory |
| **5** | DEPENDENCY_ERROR | Missing dependencies | Install packages |
| **6** | PERMISSION_ERROR | File permission denied | Fix file permissions |
| **7** | TIMEOUT_ERROR | Operation timed out | Check performance/resources |

### Exit Code Examples

#### Exit Code 0 - Success
```bash
$ python tests/runtime/test_all_checkpoints.py
✓ Checkpoint 1: Environment validated
✓ Checkpoint 2: Configuration loaded
✓ Checkpoint 3: Components initialized
✓ Checkpoint 4: API connected
✓ Checkpoint 5: State management working
✓ Checkpoint 6: Rules evaluated
✓ Checkpoint 7: Events handled
✓ Checkpoint 8: Cleanup completed

Runtime Tests: PASS
Exit code: 0
```

#### Exit Code 1 - Configuration Error
```bash
$ python tests/runtime/test_all_checkpoints.py
✓ Checkpoint 1: Environment validated
✗ Checkpoint 2: Configuration failed

Error: daily_realized_loss.limit must be negative
Found: 500 (positive)
File: config/risk_config.yaml
Line: 12

Fix: Change limit to negative value (e.g., -500)

Exit code: 1
```

#### Exit Code 2 - Runtime Error
```bash
$ python tests/runtime/test_all_checkpoints.py
✓ Checkpoint 1: Environment validated
✓ Checkpoint 2: Configuration loaded
✗ Checkpoint 3: Component initialization failed

Error: PnLTracker.__init__() missing 1 required positional argument: 'config'
File: src/core/pnl_tracker.py
Line: 45

Fix: Pass config to PnLTracker constructor

Exit code: 2
```

#### Exit Code 3 - API Error
```bash
$ python tests/runtime/test_all_checkpoints.py
✓ Checkpoint 1: Environment validated
✓ Checkpoint 2: Configuration loaded
✓ Checkpoint 3: Components initialized
✗ Checkpoint 4: API connectivity failed

Error: Authentication failed - Invalid API key
Check: .env file contains valid TOPSTEPX_API_KEY

Exit code: 3
```

---

## Log Interpretation

### Log Levels

Runtime tests produce structured logs:

```
[2025-10-23 14:30:45] [INFO] Starting checkpoint 1: Environment validation
[2025-10-23 14:30:45] [DEBUG] Python version: 3.12.1
[2025-10-23 14:30:45] [DEBUG] Checking package: topstepx_sdk
[2025-10-23 14:30:45] [INFO] ✓ Checkpoint 1 passed
[2025-10-23 14:30:45] [INFO] Starting checkpoint 2: Configuration loading
[2025-10-23 14:30:45] [WARNING] Using template config file
[2025-10-23 14:30:45] [ERROR] Configuration validation failed
[2025-10-23 14:30:45] [CRITICAL] Runtime test suite failed
```

### Log Level Meanings

| Level | Meaning | When Used | Action Required |
|-------|---------|-----------|-----------------|
| **DEBUG** | Detailed info | Verbose mode | None - informational |
| **INFO** | Progress update | Normal flow | None - progress tracking |
| **WARNING** | Potential issue | Non-critical problems | Review and fix if needed |
| **ERROR** | Test failed | Checkpoint failed | Fix immediately |
| **CRITICAL** | System broken | Multiple failures | Fix before proceeding |

### Reading Log Output

**Example 1: Successful Run**
```log
[INFO] Starting checkpoint 1: Environment validation
[DEBUG] Python 3.12.1 detected
[DEBUG] Package topstepx_sdk: installed
[DEBUG] Package yaml: installed
[INFO] ✓ Checkpoint 1 passed (0.05s)
[INFO] Starting checkpoint 2: Configuration loading
[DEBUG] Loading config/risk_config.yaml
[DEBUG] Validating YAML structure
[INFO] ✓ Checkpoint 2 passed (0.12s)
```
**Interpretation:** Everything working normally.

**Example 2: Configuration Warning**
```log
[INFO] Starting checkpoint 2: Configuration loading
[DEBUG] Loading config/accounts.yaml
[WARNING] File not found: config/accounts.yaml
[WARNING] Falling back to: config/accounts.yaml.template
[WARNING] Using template config - not suitable for production
[INFO] ✓ Checkpoint 2 passed with warnings (0.08s)
```
**Interpretation:** System works but using template. Create real config for production.

**Example 3: Critical Failure**
```log
[INFO] Starting checkpoint 4: API connectivity
[DEBUG] Initializing TopstepXClient
[ERROR] Authentication failed: Invalid API key
[ERROR] Response: 401 Unauthorized
[CRITICAL] Cannot proceed without valid API credentials
[ERROR] ✗ Checkpoint 4 failed (0.45s)
```
**Interpretation:** API credentials invalid. Check .env file.

---

## Common Failures & Fixes

### Failure Matrix

| Checkpoint | Common Error | Cause | Fix |
|------------|--------------|-------|-----|
| **1: Environment** | `ImportError: No module named 'topstepx_sdk'` | Missing package | `pip install topstepx-sdk` |
| **1: Environment** | `Python 3.10 detected, need 3.12+` | Old Python | Upgrade to Python 3.12+ |
| **2: Configuration** | `yaml.scanner.ScannerError` | Invalid YAML syntax | Fix YAML formatting |
| **2: Configuration** | `KeyError: 'rules'` | Missing section | Add required section to config |
| **3: Components** | `TypeError: __init__() missing argument` | Wrong constructor | Check class signature |
| **3: Components** | `AttributeError: no attribute 'add_trade'` | API mismatch | Update component interface |
| **4: API** | `401 Unauthorized` | Invalid credentials | Check .env API keys |
| **4: API** | `ConnectionRefusedError` | Network issue | Check internet/VPN |
| **5: State** | `PermissionError: [Errno 13]` | File permissions | Fix directory permissions |
| **5: State** | `JSONDecodeError` | Corrupted state file | Delete and regenerate |
| **6: Rules** | `ValueError: limit must be negative` | Invalid config value | Fix rule configuration |
| **7: Events** | `RuntimeError: Event loop closed` | Async issue | Check event loop handling |
| **8: Cleanup** | `ResourceWarning: unclosed file` | Missing cleanup | Add proper close() calls |

### Detailed Failure Scenarios

#### Scenario 1: Missing Dependencies

**Symptom:**
```
ImportError: No module named 'topstepx_sdk'
```

**Diagnosis:**
```bash
# Check installed packages
pip list | grep topstepx

# If not found:
echo "Package not installed"
```

**Fix:**
```bash
# Install missing package
pip install topstepx-sdk

# Verify installation
python -c "import topstepx_sdk; print('OK')"

# Rerun checkpoint
python tests/runtime/test_checkpoint_01_environment.py
```

#### Scenario 2: Configuration Error

**Symptom:**
```
AssertionError: daily_realized_loss.limit must be negative
Found: 500
```

**Diagnosis:**
```bash
# Check configuration value
grep -A 5 "daily_realized_loss:" config/risk_config.yaml
```

**Fix:**
```yaml
# Edit config/risk_config.yaml
rules:
  daily_realized_loss:
    enabled: true
    limit: -500  # ← Change from 500 to -500
```

**Verify:**
```bash
# Rerun checkpoint
python tests/runtime/test_checkpoint_02_config.py
```

#### Scenario 3: API Authentication Failure

**Symptom:**
```
401 Unauthorized: Invalid API key
```

**Diagnosis:**
```bash
# Check .env file exists
ls -la .env

# Check API key format (redacted)
grep TOPSTEPX_API_KEY .env | head -c 30
```

**Fix:**
```bash
# Create/update .env file
cat > .env << EOF
TOPSTEPX_API_KEY=your_actual_api_key_here
TOPSTEPX_API_SECRET=your_actual_secret_here
EOF

# Verify key is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Key loaded' if os.getenv('TOPSTEPX_API_KEY') else 'Key missing')"
```

**Verify:**
```bash
# Rerun checkpoint
python tests/runtime/test_checkpoint_04_api.py
```

#### Scenario 4: State Persistence Error

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: 'data/state.json'
```

**Diagnosis:**
```bash
# Check directory permissions
ls -ld data/
ls -la data/state.json
```

**Fix:**
```bash
# Fix directory permissions
chmod 755 data/
chmod 644 data/*.json

# Or recreate directory
rm -rf data/
mkdir data/
chmod 755 data/
```

**Verify:**
```bash
# Test write permission
echo "test" > data/test.txt && rm data/test.txt && echo "OK"

# Rerun checkpoint
python tests/runtime/test_checkpoint_05_state.py
```

---

## Best Practices

### Development Workflow

1. **Run runtime tests before committing**
   ```bash
   python run_tests.py
   # Select: [S] System Health Check
   ```

2. **Fix failures in checkpoint order**
   - Start with lowest numbered failure
   - Each checkpoint depends on previous ones
   - Don't skip checkpoints

3. **Use verbose mode for debugging**
   ```bash
   python run_tests.py
   # Select: [V] Toggle verbose mode
   # Then run desired check
   ```

4. **Generate debug reports for issues**
   ```bash
   python run_tests.py
   # Select: [G] Generate Debug Report
   # Share report with team/support
   ```

### Deployment Workflow

1. **Pre-deployment validation**
   ```bash
   # Run full E2E test
   python run_tests.py
   # Select: [E] End-to-End Flow

   # Must get Exit Code 0
   ```

2. **Environment-specific configs**
   ```bash
   # Validate configs for each environment
   python tests/runtime/test_checkpoint_02_config.py

   # Check different environments
   CONFIG_ENV=development python tests/runtime/...
   CONFIG_ENV=staging python tests/runtime/...
   CONFIG_ENV=production python tests/runtime/...
   ```

3. **Post-deployment smoke test**
   ```bash
   # Quick health check
   python run_tests.py
   # Select: [T] Test API Connection
   ```

### Continuous Integration

Add to CI/CD pipeline:

```yaml
# .github/workflows/runtime-tests.yml
- name: Runtime Validation
  run: |
    python tests/runtime/test_all_checkpoints.py
    if [ $? -ne 0 ]; then
      echo "Runtime tests failed"
      exit 1
    fi
```

---

## Related Documentation

- **Testing Guide:** `/docs/testing/TESTING_GUIDE.md`
- **AI Workflow:** `/docs/testing/WORKING_WITH_AI.md`
- **Test Reports:** `/test_reports/README.md`
- **Agent Guidelines:** `/.claude/prompts/runtime-guidelines.md`

---

**Last Updated:** 2025-10-23
**Version:** 1.0
**Status:** Production Ready
