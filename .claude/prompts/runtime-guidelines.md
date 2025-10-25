# Runtime Testing Guidelines for AI Agents

**Purpose:** Standard operating procedures for AI agents performing runtime validation and debugging.

---

## Quick Reference

**When to run runtime tests:**
- Before deployment (REQUIRED)
- After environment changes
- When troubleshooting "works on my machine" issues
- After core component refactoring

**How to run:**
```bash
python run_tests.py
# Select appropriate menu option: [S][R][T][L][E][G]
```

**Expected outcome:**
- Exit Code 0 = System ready
- Exit Code 1-7 = Issues requiring fixes

---

## Agent Responsibilities

### 1. Pre-Deployment Validation

**Agent task:** Ensure system is deployment-ready

**Steps:**
1. Run system health check
   ```bash
   python run_tests.py
   # Select: [S] System Health Check
   ```

2. Interpret exit code
   - Exit 0: Proceed to step 3
   - Exit 1-7: Fix issues, repeat step 1

3. Run E2E flow validation
   ```bash
   python run_tests.py
   # Select: [E] End-to-End Flow
   ```

4. Generate debug report
   ```bash
   python run_tests.py
   # Select: [G] Generate Debug Report
   ```

5. Confirm deployment readiness
   - All checkpoints PASS
   - No critical errors
   - Warnings documented
   - Exit Code 0 achieved

**Output format:**
```
DEPLOYMENT VALIDATION REPORT
============================
Date: YYYY-MM-DD HH:MM:SS
Agent: [agent-name]

System Health: [PASS/FAIL]
E2E Flow: [PASS/FAIL]
Exit Code: [0-7]

Deployment Ready: [YES/NO]

Issues:
- [None or list of issues]

Recommendations:
- [List of recommendations]
```

### 2. Runtime Error Diagnosis

**Agent task:** Diagnose and fix runtime failures

**Steps:**
1. Read test report
   ```
   Read test_reports/latest.txt
   ```

2. Identify failed checkpoint (1-8)
   - Extract checkpoint number from report
   - Note exit code
   - Capture error message

3. Analyze root cause
   - Checkpoint 1: Environment issues
   - Checkpoint 2: Configuration errors
   - Checkpoint 3: Component initialization
   - Checkpoint 4: API connectivity
   - Checkpoint 5: State management
   - Checkpoint 6: Rule evaluation
   - Checkpoint 7: Event handling
   - Checkpoint 8: Resource cleanup

4. Suggest specific fix
   - Exact file to edit
   - Exact line number
   - Exact change required
   - Verification command

5. Verify fix works
   - Rerun specific checkpoint
   - Confirm exit code 0
   - Document resolution

**Output format:**
```
RUNTIME ERROR DIAGNOSIS
======================
Failed Checkpoint: [1-8]
Exit Code: [code]
Root Cause: [description]

Error Details:
[Exact error message from report]

Fix Required:
File: [path/to/file]
Line: [number]
Change: [specific change]

Verification:
[Command to verify fix]
```

### 3. Configuration Validation

**Agent task:** Validate YAML configuration files

**Steps:**
1. Run configuration validation
   ```bash
   python run_tests.py
   # Select: [L] Load Configurations
   ```

2. Check for errors
   - YAML syntax errors
   - Missing required fields
   - Invalid value ranges
   - Template vs production config

3. Suggest corrections
   - Show exact YAML to add/change
   - Explain why change is needed
   - Provide example values

4. Verify corrections
   ```bash
   # Rerun configuration check
   python tests/runtime/test_checkpoint_02_config.py
   ```

**Output format:**
```
CONFIGURATION VALIDATION
========================
File: [config file name]
Status: [VALID/INVALID]

Issues Found:
1. [Issue 1 description]
   Location: Line [number]
   Current: [current value]
   Required: [required value]
   Fix: [exact YAML to use]

2. [Issue 2 description]
   ...

Verification Command:
python tests/runtime/test_checkpoint_02_config.py
```

### 4. API Connectivity Testing

**Agent task:** Validate API connectivity and authentication

**Steps:**
1. Run API connectivity test
   ```bash
   python run_tests.py
   # Select: [T] Test API Connection
   ```

2. Check authentication
   - API key valid
   - API secret valid
   - Authentication succeeds

3. Verify API calls work
   - GET /accounts
   - GET /positions
   - Rate limiting configured

4. Document findings
   - Connection status
   - Authentication status
   - API response codes
   - Any errors

**Output format:**
```
API CONNECTIVITY TEST
=====================
Timestamp: YYYY-MM-DD HH:MM:SS

Authentication: [PASS/FAIL]
API Key: [VALID/INVALID/MISSING]
API Secret: [VALID/INVALID/MISSING]

API Calls:
- GET /accounts: [status code]
- GET /positions: [status code]

Rate Limiting: [CONFIGURED/NOT CONFIGURED]

Issues:
[None or list of issues]

Recommendations:
[List of recommendations]
```

---

## Checkpoint Patterns

Each checkpoint has specific validation patterns agents should follow:

### Checkpoint 1: Environment Validation

**Validates:**
- Python version ≥ 3.12
- Required packages installed
- Directory structure correct
- File permissions appropriate

**Common failures:**
- `ImportError: No module named 'X'` → Install package
- `Python 3.10 detected` → Upgrade Python
- `Directory not found` → Create directory
- `Permission denied` → Fix permissions

**Agent action:**
```python
# Verify Python version
assert sys.version_info >= (3, 12), "Upgrade to Python 3.12+"

# Check packages
required = ["topstepx_sdk", "yaml", "pydantic", "pytest"]
for pkg in required:
    assert importlib.util.find_spec(pkg), f"Install: pip install {pkg}"

# Check directories
for dir in ["config", "data", "logs", "tests"]:
    assert Path(dir).exists(), f"Create: mkdir {dir}"
```

### Checkpoint 2: Configuration Loading

**Validates:**
- YAML syntax correct
- Required fields present
- Values within ranges
- No template configs in production

**Common failures:**
- `yaml.scanner.ScannerError` → Fix YAML syntax
- `KeyError: 'rules'` → Add missing section
- `AssertionError: limit must be negative` → Fix value
- `Warning: Using template` → Create production config

**Agent action:**
```python
# Load and validate config
with open("config/risk_config.yaml") as f:
    config = yaml.safe_load(f)

# Check structure
assert "rules" in config
assert "daily_realized_loss" in config["rules"]

# Check values
loss_rule = config["rules"]["daily_realized_loss"]
assert loss_rule["limit"] < 0, "Loss limit must be negative"
assert loss_rule["enabled"] is True, "Loss rule must be enabled"
```

### Checkpoint 3: Component Initialization

**Validates:**
- Components instantiate correctly
- Dependencies injected properly
- State initialized
- No circular dependencies

**Common failures:**
- `TypeError: __init__() missing argument` → Fix constructor
- `AttributeError: no attribute 'X'` → Update interface
- `RuntimeError: Circular dependency` → Refactor dependencies

**Agent action:**
```python
# Initialize components in order
pnl_tracker = PnLTracker()
assert pnl_tracker is not None

state_mgr = StateManager()
assert state_mgr.accounts == {}

rule_engine = RuleEngine(config, pnl_tracker, state_mgr)
assert len(rule_engine.rules) > 0
```

### Checkpoint 4: API Connectivity

**Validates:**
- API client initializes
- Authentication succeeds
- Test calls work
- Rate limiting configured

**Common failures:**
- `401 Unauthorized` → Check API credentials
- `ConnectionRefusedError` → Check network
- `Timeout` → Check API endpoint
- `RateLimitError` → Configure rate limiting

**Agent action:**
```python
# Test API connection
client = TopstepXClient()
client.authenticate()
assert client.is_authenticated

# Test API calls
accounts = client.get_accounts()
assert isinstance(accounts, list)

# Verify rate limiting
assert hasattr(client, 'rate_limiter')
```

### Checkpoint 5: State Management

**Validates:**
- State updates correctly
- State persists to disk
- State recovers correctly
- No memory leaks

**Common failures:**
- `PermissionError` → Fix directory permissions
- `JSONDecodeError` → Delete corrupted state file
- `KeyError` → State not updating correctly

**Agent action:**
```python
# Test state management
state_mgr = StateManager()
state_mgr.update_position(account_id, position)
assert account_id in state_mgr.accounts

# Test persistence
state_mgr.save_state()

# Test recovery
new_mgr = StateManager()
new_mgr.load_state()
assert account_id in new_mgr.accounts
```

### Checkpoint 6: Rule Evaluation

**Validates:**
- Rules load correctly
- Rules evaluate trades
- Breaches detected
- Actions triggered

**Common failures:**
- `ValueError: Invalid rule config` → Fix configuration
- `AssertionError: Rule not found` → Check rule registration
- `TypeError: Invalid trade format` → Fix trade structure

**Agent action:**
```python
# Test rule evaluation
rule_engine = RuleEngine(config, pnl_tracker, state_mgr)
breaches = rule_engine.evaluate_all(trade)

# Verify rule execution
assert isinstance(breaches, list)
```

### Checkpoint 7: Event Handling

**Validates:**
- Events publish correctly
- Events subscribe correctly
- Events dispatch properly
- No event queue backlog

**Common failures:**
- `RuntimeError: Event loop closed` → Check async handling
- `ValueError: Invalid event type` → Fix event structure
- `TimeoutError: Event not received` → Check event routing

**Agent action:**
```python
# Test event handling
event_bus = EventBus()
received = []

def handler(event):
    received.append(event)

event_bus.subscribe("trade.executed", handler)
event_bus.publish({"type": "trade.executed", "data": {}})

assert len(received) == 1
```

### Checkpoint 8: Resource Cleanup

**Validates:**
- Connections closed
- State saved
- Resources released
- No warnings

**Common failures:**
- `ResourceWarning: unclosed file` → Add close() call
- `Warning: State not saved` → Save state before exit
- `MemoryError` → Release resources

**Agent action:**
```python
# Test cleanup
components.shutdown()

# Verify state saved
assert Path("data/final_state.json").exists()

# Verify no resource warnings
import gc
gc.collect()
```

---

## Logging Standards

Agents should interpret logs at different levels:

### DEBUG
**Purpose:** Detailed information for troubleshooting
**Action:** Record but don't act on
**Example:** `[DEBUG] Loading config from: config/risk_config.yaml`

### INFO
**Purpose:** Progress and status updates
**Action:** Track progress, no action needed
**Example:** `[INFO] ✓ Checkpoint 1 passed (0.05s)`

### WARNING
**Purpose:** Non-critical issues that should be addressed
**Action:** Document, recommend fixing
**Example:** `[WARNING] Using template config - not suitable for production`

### ERROR
**Purpose:** Test failures requiring fixes
**Action:** Diagnose, suggest fix, verify
**Example:** `[ERROR] Configuration validation failed: limit must be negative`

### CRITICAL
**Purpose:** System broken, cannot proceed
**Action:** Stop deployment, escalate
**Example:** `[CRITICAL] Cannot proceed without valid API credentials`

---

## Test Requirements

### Unit Tests
**Coverage:** ≥90%
**Speed:** <1s per test
**Dependencies:** None (use mocks)
**When:** Before every commit

### Integration Tests
**Coverage:** Critical paths
**Speed:** <5s per test
**Dependencies:** Real components (no API)
**When:** Before merging

### Runtime Tests
**Coverage:** All 8 checkpoints
**Speed:** <2s total
**Dependencies:** Real environment
**When:** Before deployment

### E2E Tests
**Coverage:** Complete workflows
**Speed:** <10s per test
**Dependencies:** Full system
**When:** Pre-deployment validation

---

## Agent Communication Protocol

### Requesting Runtime Tests

**Human request:**
```
"Run runtime health check"
"Validate system before deployment"
"Check if environment is set up correctly"
```

**Agent response:**
```
I'll run the runtime health check for you.

[Runs: python run_tests.py → [S]]

Results:
- Exit Code: 0
- Status: PASS
- All 8 checkpoints passed
- System ready for deployment

Would you like me to generate a detailed debug report?
```

### Reporting Failures

**Agent finds failure:**
```
Runtime health check failed:

Failed Checkpoint: 2 (Configuration Loading)
Exit Code: 1
Error: daily_realized_loss.limit must be negative (found: 500)

Fix Required:
File: config/risk_config.yaml
Line: 12
Change: limit: -500

I can apply this fix for you. Should I proceed?
```

### Confirming Fixes

**After applying fix:**
```
Fix applied successfully.

Rerunning checkpoint 2...

Results:
- Exit Code: 0
- Status: PASS
- Configuration validated

All checkpoints now pass. System ready for deployment.
```

---

## Common Agent Tasks

### Task 1: Pre-Deployment Checklist

```
Agent executes:
1. Run [S] System Health Check → Exit Code 0 ✓
2. Run [E] End-to-End Flow → Exit Code 0 ✓
3. Generate [G] Debug Report → Review warnings
4. Confirm no critical issues
5. Report deployment readiness

Agent reports:
"System validated and ready for deployment.
- All checkpoints passed
- No critical errors
- 1 warning: Using template config (non-blocking)
- Exit Code: 0
- Deployment risk: LOW"
```

### Task 2: Diagnose Runtime Failure

```
Agent executes:
1. Read test_reports/latest.txt
2. Identify failed checkpoint: 4 (API Connectivity)
3. Extract error: "401 Unauthorized"
4. Suggest fix: "Check .env file for valid API credentials"
5. Verify fix: Rerun checkpoint 4

Agent reports:
"Runtime failure diagnosed:
- Checkpoint 4 failed (API Connectivity)
- Cause: Invalid API credentials
- Fix: Update .env file with valid TOPSTEPX_API_KEY
- Verification: python tests/runtime/test_checkpoint_04_api.py"
```

### Task 3: Configuration Validation

```
Agent executes:
1. Run [L] Load Configurations
2. Identify errors in YAML
3. Suggest corrections
4. Verify corrections work

Agent reports:
"Configuration errors found in risk_config.yaml:
1. Line 12: limit must be negative (found: 500)
   Fix: Change to limit: -500
2. Line 25: enabled must be boolean (found: 'true')
   Fix: Change to enabled: true

Apply these fixes and rerun validation?"
```

---

## Exit Code Decision Tree

```
Exit Code → Agent Action

0 (SUCCESS)
  → Report system ready
  → Proceed with deployment

1 (CONFIG_ERROR)
  → Read config files
  → Identify invalid values
  → Suggest corrections
  → Rerun validation

2 (RUNTIME_ERROR)
  → Read stack trace
  → Identify failing component
  → Suggest code fix
  → Rerun checkpoint

3 (API_ERROR)
  → Check .env file
  → Verify credentials
  → Test connectivity
  → Rerun API test

4 (STATE_ERROR)
  → Check data directory
  → Verify permissions
  → Test state operations
  → Rerun state test

5 (DEPENDENCY_ERROR)
  → List missing packages
  → Provide install commands
  → Verify installation
  → Rerun environment check

6 (PERMISSION_ERROR)
  → Identify permission issues
  → Suggest chmod commands
  → Verify permissions
  → Rerun checkpoint

7 (TIMEOUT_ERROR)
  → Check system resources
  → Identify bottlenecks
  → Suggest optimizations
  → Rerun with timeout increase
```

---

## Best Practices for Agents

### DO

✓ Read test reports before suggesting fixes
✓ Provide specific, actionable fixes
✓ Verify fixes by rerunning tests
✓ Document all changes made
✓ Report exit codes and status clearly
✓ Escalate critical failures
✓ Generate debug reports for complex issues

### DON'T

✗ Guess at fixes without reading reports
✗ Make changes without verification
✗ Skip checkpoint validation
✗ Ignore warnings
✗ Deploy with failing tests
✗ Override exit code checks
✗ Modify core checkpoint logic

---

## Related Documentation

- **Runtime Debugging Guide:** `/docs/testing/RUNTIME_DEBUGGING.md`
- **Testing Guide:** `/docs/testing/TESTING_GUIDE.md`
- **AI Workflow:** `/docs/testing/WORKING_WITH_AI.md`
- **Test Reports:** `/test_reports/README.md`

---

**Version:** 1.0
**Last Updated:** 2025-10-23
**For:** AI Agents performing runtime validation
