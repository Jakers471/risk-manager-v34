# CLAUDE.md - AI Assistant Entry Point

**READ THIS FIRST** - Every session starts here

---

## ⚠️ IMPORTANT: Adaptable Documentation

**This file uses REFERENCES, not hard-coded structures.**

- ❌ **DON'T** rely on cached file trees or progress percentages
- ✅ **DO** use paths and check actual files for current state
- ✅ **DO** use `ls`, `find`, `pytest --collect-only` to see structure
- ✅ **DO** read `docs/current/PROJECT_STATUS.md` for latest progress
- ✅ **DO** check `test_reports/latest.txt` for most recent test results

**Reason**: Hard-coded structures go stale immediately. Always check the actual files.

---

## 🎯 Purpose

This file tells Claude AI exactly what to read and in what order to get up to speed on this project.

**Last Updated**: 2025-10-28
**Project**: Risk Manager V34
**Location**: `C:\Users\jakers\Desktop\risk-manager-v34\`
**Environment**: Windows WSL2

---

## 📖 Quick Start (First 5 Minutes)

### 1. Read These Files IN ORDER:

```
Priority 1 - Latest Session (1 min):
  1. AI_SESSION_HANDOFF_2025-10-28.md     - ⭐ MOST RECENT SESSION (100% rule tests!)
  2. docs/current/PROJECT_STATUS.md       - Current state & progress
  3. test_reports/latest.txt              - Most recent test results

Priority 2 - Testing System (3 min):
  4. docs/testing/README.md               - Testing navigation
  5. docs/testing/TESTING_GUIDE.md        - Core testing reference
  6. docs/testing/RUNTIME_DEBUGGING.md    - Runtime validation system

Priority 3 - SDK Integration (3 min):
  7. docs/current/SDK_INTEGRATION_GUIDE.md  - How we use Project-X SDK
  8. docs/current/MULTI_SYMBOL_SUPPORT.md   - Account-wide risk

Priority 4 - API Reference (For Coding/Testing):
  9. SDK_API_REFERENCE.md                   - Actual SDK & our API contracts
  10. SDK_ENFORCEMENT_FLOW.md               - Complete enforcement wiring
  11. TEST_RUNNER_FINAL_FIXES.md            - Test runner behavior & fixes
```

**After reading these 11 files, you will know**:
- ✅ What's been built and what's working
- ✅ Current test status (passing/failing)
- ✅ How testing and runtime debugging work
- ✅ How the SDK is integrated
- ✅ **Actual API contracts** (prevent test/code mismatches)
- ✅ **Enforcement flow** (how violations trigger SDK actions)
- ✅ **Test runner behavior** (why tests were failing/fixed)
- ✅ What we still need to build
- ✅ Exactly where we left off

---

## 🚀 Entry Points (How to Run the System)

### Development Runtime (Primary Entry Point)

**Command**: `python run_dev.py`

**Purpose**: Live microscope for validating the complete system end-to-end

**Use When**:
- First-time integration testing
- Validating rule math and event flow
- Debugging SDK integration
- Watching real-time events
- Before deploying as Windows Service

**Features**:
- ✅ Maximum logging (8 checkpoints visible)
- ✅ Real-time event streaming
- ✅ Rule evaluation display
- ✅ P&L tracking
- ✅ Enforcement action visibility
- ✅ Graceful Ctrl+C shutdown

**Options**:
```bash
python run_dev.py                    # Interactive account selection
python run_dev.py --account ACC123   # Explicit account
python run_dev.py --config path.yaml # Custom config
python run_dev.py --log-level DEBUG  # More verbose
```

**Documentation**: See `RUN_DEV_IMPLEMENTATION.md`

---

### Admin CLI (Management Interface)

**Command**: `python admin_cli.py`

**Purpose**: Configure, manage, and control the Risk Manager system

**Modes**:
1. **Interactive Menu** (default - no args)
   - Number-based navigation (1-6)
   - Setup wizard, service control, rule configuration
   - Dashboard, connection testing

2. **Command Mode** (with args)
   - Individual commands for scripting
   - `admin_cli service status`
   - `admin_cli rules list`
   - `admin_cli config show`

**Key Features**:
- ✅ Setup wizard (4-step, SDK-free)
- ✅ Service control (start/stop/restart)
- ✅ Rule management (13 rules)
- ✅ Configuration editing
- ✅ UAC elevation checks

**Documentation**: See `ADMIN_CLI_MVP_COMPLETE.md` and `ADMIN_MENU_IMPLEMENTATION.md`

---

### Test Runner

**Command**: `python run_tests.py`

**Purpose**: Interactive test menu for running pytest suites

**Use When**:
- Running unit/integration/E2E tests
- Checking test coverage
- Running runtime smoke tests
- Debugging test failures

**Documentation**: See `docs/testing/TESTING_GUIDE.md`

---

## 🧪 Testing System Overview

### Interactive Test Runner Menu

**Command**: `python run_tests.py`

**Location**: Root directory (`run_tests.py`)

#### Menu Structure:

```
╔════════════════════════════════════════════════════════════╗
║  Risk Manager V34 - Test Runner                           ║
╚════════════════════════════════════════════════════════════╝

Test Selection:
  [1] Run ALL tests
  [2] Run UNIT tests only
  [3] Run INTEGRATION tests only
  [4] Run E2E tests only
  [5] Run SLOW tests only
  [6] Run tests with COVERAGE report
  [7] Run tests with COVERAGE + HTML report
  [8] Run specific test file
  [9] Run tests matching keyword
  [0] Run last failed tests only

Runtime Checks:
  [s] Runtime SMOKE (DRY-RUN, fail-fast, 8s timeout)
  [r] Runtime SOAK (30-60s DRY-RUN)
  [t] Runtime TRACE (ASYNC_DEBUG=1, deep debug)
  [l] View/Tail LOGS
  [e] Env/Config SNAPSHOT
  [g] GATE: Tests + Smoke combo

Utilities:
  [v] Run in VERBOSE mode (shows each test)
  [c] Check COVERAGE status
  [p] View last test REPORT
  [h] Help - Testing with AI
  [q] Quit
```

### Test Reports Auto-Save

**Every test run automatically saves to**:
- `test_reports/latest.txt` - Always the most recent run (overwritten)
- `test_reports/YYYY-MM-DD_HH-MM-SS_passed.txt` - Timestamped pass
- `test_reports/YYYY-MM-DD_HH-MM-SS_failed.txt` - Timestamped fail

**Usage Pattern**:
```bash
# User runs tests
python run_tests.py
# → Select option → Report auto-saves

# AI reads latest results
Read test_reports/latest.txt

# The report contains:
# - Full pytest output with colors
# - Pass/fail status
# - Exit code
# - Timestamp
# - Complete tracebacks for failures
```

### Runtime Reliability Pack

**NEW: Prevents "Tests Green But Runtime Broken" Problem**

The Runtime Reliability Pack provides 5 capabilities:

#### 1. **Smoke Test** (`[s]` in menu)
- **What**: Boots system and validates first event fires within 8 seconds
- **Exit Codes**:
  - `0` = Success (first event observed)
  - `1` = Exception occurred (see logs)
  - `2` = Boot stalled (no events within timeout)
- **When**: After test suite passes, before deployment

#### 2. **Soak Test** (`[r]` in menu)
- **What**: Extended 30-60s runtime validation
- **Why**: Catches memory leaks, deadlocks, resource exhaustion
- **When**: Before major deployments

#### 3. **Trace Mode** (`[t]` in menu)
- **What**: Deep async task debugging (ASYNC_DEBUG=1)
- **Output**: `runtime_trace.log` with all pending tasks
- **When**: Service starts but hangs/stalls

#### 4. **Log Viewer** (`[l]` in menu)
- **What**: Stream logs in real-time or view last 100 lines
- **Location**: `data/logs/risk_manager.log`
- **When**: Debugging runtime issues

#### 5. **Env Snapshot** (`[e]` in menu)
- **What**: Shows configuration, env vars, Python version
- **When**: Configuration troubleshooting

**Implementation**:
- **Source**: `src/runtime/` (1,316 lines across 6 files)
- **Tests**: `tests/runtime/` (70 tests across 5 files)
- **Docs**: `docs/testing/RUNTIME_DEBUGGING.md` (36KB comprehensive guide)

---

## 🔍 8-Checkpoint Logging System

**Location**: SDK logging integrated in:
- `src/risk_manager/core/manager.py` - Checkpoints 1-4
- `src/risk_manager/core/engine.py` - Checkpoints 5-7
- `src/risk_manager/sdk/enforcement.py` - Checkpoint 8

**The 8 Strategic Checkpoints**:

```
Checkpoint 1: 🚀 Service Start
  └─ Log: "Risk Manager starting..."
  └─ Where: manager.py:start()

Checkpoint 2: ✅ Config Loaded
  └─ Log: "Config loaded: X rules"
  └─ Where: manager.py:_load_config()

Checkpoint 3: ✅ SDK Connected
  └─ Log: "SDK connected: account_id"
  └─ Where: manager.py:_connect_sdk()

Checkpoint 4: ✅ Rules Initialized
  └─ Log: "Rules initialized: X rules"
  └─ Where: manager.py:_initialize_rules()

Checkpoint 5: ✅ Event Loop Running
  └─ Log: "Event loop running"
  └─ Where: engine.py:start()

Checkpoint 6: 📨 Event Received
  └─ Log: "Event received: {event}"
  └─ Where: engine.py:handle_event()

Checkpoint 7: 🔍 Rule Evaluated
  └─ Log: "Rule evaluated: {rule} {result}"
  └─ Where: engine.py:handle_event()

Checkpoint 8: ⚠️ Enforcement Triggered
  └─ Log: "Enforcement triggered: {action}"
  └─ Where: enforcement.py:enforce()
```

**Reading Logs**:
```bash
# View logs via menu
python run_tests.py → [l]

# Or directly
cat data/logs/risk_manager.log | grep "🚀\|✅\|📨\|🔍\|⚠️"

# Find where it stopped
cat data/logs/risk_manager.log | tail -20
```

---

## 📁 Project Structure

**Critical Directories** (use paths, don't cache structure):

### Source Code
```
src/
├── risk_manager/         # Core risk management system
│   ├── core/            # Manager, engine, events (with SDK logging)
│   ├── rules/           # Risk rule implementations
│   ├── sdk/             # SDK integration layer (with enforcement logging)
│   ├── state/           # State management
│   ├── ai/              # AI integration
│   ├── integrations/    # External integrations
│   └── monitoring/      # Monitoring & metrics
└── runtime/             # Runtime reliability capabilities ⭐ NEW
    ├── smoke_test.py    # Boot validation (exit codes 0/1/2)
    ├── heartbeat.py     # Liveness monitoring (1s intervals)
    ├── async_debug.py   # Task dump for deadlock detection
    ├── post_conditions.py # System wiring validation
    └── dry_run.py       # Deterministic mock event generator
```

### Tests
```
tests/
├── unit/                # Unit tests (fast, mocked)
├── integration/         # Integration tests (real SDK)
├── runtime/             # Runtime reliability tests ⭐ NEW
│   ├── test_smoke.py    # 13 smoke test scenarios
│   ├── test_heartbeat.py
│   ├── test_async_debug.py
│   ├── test_post_conditions.py
│   └── test_dry_run.py
├── fixtures/            # Shared test fixtures
└── conftest.py          # Pytest configuration
```

### Documentation
```
docs/
├── current/             # Active documentation
│   ├── PROJECT_STATUS.md           # ⭐ START HERE - Current state
│   ├── SDK_INTEGRATION_GUIDE.md    # How we use SDK
│   ├── MULTI_SYMBOL_SUPPORT.md     # Account-wide risk
│   ├── RULE_CATEGORIES.md          # Rule types
│   ├── CONFIG_FORMATS.md           # YAML examples
│   └── SECURITY_MODEL.md           # Windows UAC security
├── testing/             # Testing documentation ⭐ NEW
│   ├── README.md                   # Testing navigation
│   ├── TESTING_GUIDE.md            # Core testing reference
│   ├── RUNTIME_DEBUGGING.md        # Runtime reliability guide
│   └── WORKING_WITH_AI.md          # AI workflow
├── dev-guides/          # Developer guides
├── PROJECT_DOCS/        # Original specifications (pre-SDK)
└── archive/             # Archived old versions
```

### Test Reports
```
test_reports/            # Auto-generated test reports ⭐ NEW
├── README.md            # Report format documentation
├── latest.txt           # ⭐ Most recent test run (ALWAYS CHECK THIS)
└── YYYY-MM-DD_HH-MM-SS_*.txt  # Timestamped archives
```

### Agent Guidelines
```
.claude/
├── agents/              # Custom agent definitions
├── commands/            # Custom slash commands
└── prompts/             # Agent protocols
    └── runtime-guidelines.md  # ⭐ Runtime testing protocols
```

### Configuration
```
config/
├── risk_config.yaml     # Risk rules configuration
├── accounts.yaml        # Account mappings
└── *.yaml.template      # Configuration templates
```

---

## 📚 Essential Documentation Paths

### Must Read First
- `docs/current/PROJECT_STATUS.md` - **START HERE** - Current progress
- `test_reports/latest.txt` - **CHECK THIS** - Most recent test results

### Testing & Debugging
- `docs/testing/TESTING_GUIDE.md` - Core testing reference
- `docs/testing/RUNTIME_DEBUGGING.md` - Runtime reliability guide ⭐ NEW
- `docs/testing/WORKING_WITH_AI.md` - AI workflow including runtime debugging
- `test_reports/README.md` - Test report format documentation
- `.claude/prompts/runtime-guidelines.md` - Agent runtime testing protocols

### SDK Integration
- `docs/current/SDK_INTEGRATION_GUIDE.md` - How to use Project-X SDK
- `docs/current/RULES_TO_SDK_MAPPING.md` - What SDK provides vs what we build

### Architecture
- `docs/current/MULTI_SYMBOL_SUPPORT.md` - Account-wide risk across symbols
- `docs/current/RULE_CATEGORIES.md` - Rule types (CRITICAL!)
- `docs/current/SECURITY_MODEL.md` - Windows UAC security

### Configuration
- `docs/current/CONFIG_FORMATS.md` - Complete YAML config examples

---

## 🔑 Key Understanding #1: SDK-First Approach

### CRITICAL CONTEXT

**The specs in `docs/PROJECT_DOCS/` were written BEFORE the Project-X SDK existed.**

At that time:
- We had to map everything to raw ProjectX Gateway API
- Manual WebSocket handling
- Manual state tracking
- Manual order/position management

**NOW we have the Project-X-Py SDK** which handles:
- ✅ WebSocket connections (SignalR)
- ✅ Real-time events (positions, orders, trades)
- ✅ Order management (place, cancel, modify)
- ✅ Position management (close, partially close)
- ✅ Account data & statistics
- ✅ Market data & indicators
- ✅ Auto-reconnection

### What This Means

**DON'T**: Reimplement what the SDK already does
**DO**: Use the SDK as foundation, add risk management on top

**Example**:
- ❌ OLD: Write custom SignalR listener from specs
- ✅ NEW: Use `TradingSuite` from SDK, wrap with risk logic

See `docs/current/SDK_INTEGRATION_GUIDE.md` for mapping.

---

## 🔐 Key Understanding #2: Windows UAC Security

### CRITICAL: NO CUSTOM PASSWORDS

**The system uses Windows UAC (User Account Control) for admin protection.**

**NO custom passwords stored. NO authentication database. Just Windows admin rights.**

### Why This Matters

The Risk Manager is designed to be **"virtually unkillable"** by the trader:

- ✅ Windows Service runs as LocalSystem (highest privilege)
- ✅ Trader CANNOT kill the service without Windows admin password
- ✅ Trader CANNOT edit configs (protected by Windows ACL)
- ✅ Trader CANNOT stop the service via Task Manager
- ✅ Admin CLI requires Windows elevation (UAC prompt)
- ✅ Only Windows admin password can override protection

**This is NOT a custom password system. This is OS-level security.**

### Two Access Levels

```
Admin CLI:  Right-click terminal → "Run as Administrator"
            → Windows UAC prompt → Enter Windows admin password
            → Full control (configure, unlock, stop service)

Trader CLI: Normal terminal (no elevation needed)
            → View-only access
            → See status, P&L, lockouts, logs
            → CANNOT modify anything
```

**See `docs/current/SECURITY_MODEL.md` for complete details.**

---

## 🧪 Key Understanding #3: Testing Hierarchy

### The Testing Pyramid

```
        /\
       /E2E\        10% - Full system, realistic scenarios
      /------\
     /  Integ \     30% - Real SDK, component interaction
    /----------\
   / Unit Tests \   60% - Fast, isolated, mocked
  /--------------\
```

### Runtime Validation Layer ⭐ NEW

**Beyond Pytest**: Runtime Reliability Pack prevents "tests green but runtime broken"

```
Step 1: pytest (automated)
  └─ [2] Unit tests
  └─ [3] Integration tests
  └─ [4] E2E tests
  └─ ✅ All pass

Step 2: Runtime validation (enforced liveness)
  └─ [s] Smoke Test ← Proves first event fires within 8s
  └─ Exit code 0 = Actually works!
  └─ Exit code 1 = Exception (fix it)
  └─ Exit code 2 = Boot stalled (check subscriptions)

Step 3: Deploy
  └─ Confident it works!
```

**Why Both?**
- **pytest** validates logic correctness
- **Runtime Pack** validates system liveness
- **Together** prevent "tests pass but nothing happens"

---

## 🔧 Common Tasks Reference

### ⚠️ BEFORE Writing Code or Tests - Read API Contracts!

**CRITICAL**: Always check actual API signatures to prevent test/code mismatches!

```bash
# 1. Check our API contracts
Read SDK_API_REFERENCE.md

# 2. Check actual implementation
from risk_manager.core.events import RiskEvent
import inspect
print(inspect.signature(RiskEvent.__init__))

# 3. Verify enum values exist
from risk_manager.core.events import EventType
print([e.name for e in EventType])
```

**Common Mistakes to Avoid**:
- ❌ Using `RiskEvent(type=...)` → ✅ Use `RiskEvent(event_type=...)`
- ❌ Using `EventType.TRADE_EXECUTED` → ✅ Check if it exists first!
- ❌ Using `PnLTracker(account_id=...)` → ✅ Use `PnLTracker(db=...)`

**See**: `SDK_API_REFERENCE.md` for all actual API contracts

---

### Run Tests (Interactive Menu)
```bash
# Interactive test runner with report generation
python run_tests.py

# Menu auto-saves reports to:
# - test_reports/latest.txt (most recent)
# - test_reports/YYYY-MM-DD_HH-MM-SS_passed.txt (timestamped)
```

**Key Menu Options**:
- `[2]` - Unit tests (fast, use this most often)
- `[3]` - Integration tests (requires SDK connection)
- `[s]` - Runtime smoke test (validates boot + first event)
- `[g]` - Gate test (unit + integration + smoke combo)
- `[p]` - View last test report

### When User Says "Fix Test Errors"
```bash
# 1. Read the latest test report
Read test_reports/latest.txt

# The report contains:
# - Full pytest output with colors
# - Failures with complete tracebacks
# - Warnings
# - Summary statistics
# - Exit code
```

**Workflow**:
1. User runs tests via menu → Auto-saves to `test_reports/latest.txt`
2. User says "fix test errors"
3. AI reads `test_reports/latest.txt`
4. AI identifies failures and fixes them
5. Repeat until all tests pass

### When Tests Pass But Runtime Fails

**Symptom**: Tests green ✅ but service starts and nothing happens

**Solution**: Run Runtime Smoke Test
```bash
python run_tests.py
# Select [s] Runtime SMOKE

# Check exit code:
# 0 = Success (first event observed)
# 1 = Exception (read logs for stack trace)
# 2 = Boot stalled (check event subscriptions)
```

**Debug with 8 Checkpoints**:
```bash
# View logs
python run_tests.py → [l]

# Find where it stopped
# Look for last emoji checkpoint:
# 🚀 ✅ ✅ ✅ ✅ 📨 🔍 ⚠️
#         ^^^ Stopped at checkpoint 3 (SDK connected)
```

**Read the guide**:
```bash
Read docs/testing/RUNTIME_DEBUGGING.md
# Contains complete troubleshooting flowchart
```

### Run Runtime Checks

```bash
# Smoke test (8s boot validation)
python run_tests.py → [s]

# Soak test (30-60s stability)
python run_tests.py → [r]

# Trace mode (deep async debug)
python run_tests.py → [t]

# View logs
python run_tests.py → [l]

# Config snapshot
python run_tests.py → [e]

# Gate: Tests + Smoke combo
python run_tests.py → [g]
```

### Run Tests Manually
```bash
# Run pytest directly (colors preserved)
pytest

# With coverage
pytest --cov

# Specific marker
pytest -m unit
pytest -m integration
pytest -m runtime

# Collect only (see available tests)
pytest --collect-only
```

### Test API Connection
```bash
uv run python test_connection.py
```

### Check Project Status
```bash
# Read current status document
cat docs/current/PROJECT_STATUS.md

# Check latest test results
cat test_reports/latest.txt

# See what's implemented
find src -name "*.py" -type f | wc -l

# See all available tests
pytest --collect-only
```

---

## 📊 Progress Tracking

**⚠️ For current progress, ALWAYS check: `docs/current/PROJECT_STATUS.md`**

That file contains:
- Up-to-date completion percentages
- What's implemented vs what's missing
- File-by-file inventory
- Next priorities

**⚠️ For latest test results, ALWAYS check: `test_reports/latest.txt`**

That file contains:
- Most recent pytest run
- Pass/fail status
- Exit code
- Complete failure tracebacks

**Don't rely on cached progress data - it goes stale immediately.**

---

## 🚀 When User Says "Where Did We Leave Off?"

### Response Template:

```markdown
**Last Session**: 2025-10-28

**🎯 CRITICAL: Read the handoff document first!**
→ `AI_SESSION_HANDOFF_2025-10-28.md`

**Reading Status**:
1. ✅ Read `AI_SESSION_HANDOFF_2025-10-28.md` (latest session details)
2. ✅ Read `docs/current/PROJECT_STATUS.md` to see current progress
3. ✅ Read `test_reports/latest.txt` to see latest test results

**Status**: [Check PROJECT_STATUS.md for completion percentage]

**Latest Test Results**: [Check test_reports/latest.txt]
- All tests passing: ✅/❌
- Exit code: X
- Failures: X

**What's Working** (from PROJECT_STATUS.md):
- [List from PROJECT_STATUS.md]

**What's Next** (from PROJECT_STATUS.md):
- [Next priorities from PROJECT_STATUS.md]

**Testing System**:
- ✅ Interactive test runner menu (`python run_tests.py`)
- ✅ Auto-save reports to `test_reports/latest.txt`
- ✅ Runtime Reliability Pack (smoke, soak, trace, logs, env)
- ✅ 8-checkpoint logging system for runtime debugging

See: `docs/current/PROJECT_STATUS.md` for complete details
```

---

## 🎯 Next Implementation Task

**Check `docs/current/PROJECT_STATUS.md` for current priorities.**

The priorities change as work progresses. Always check the live document.

---

## ⚠️ Critical Notes

### Architecture Clarification

**Original Specs** (`docs/PROJECT_DOCS/`):
- Written before Project-X SDK existed
- Describe manual API integration
- Direct WebSocket handling
- Custom state management

**Current Implementation** (V34):
- **SDK-First**: Project-X-Py handles heavy lifting
- **Risk Layer**: We add risk management on top
- **Async**: Modern async/await throughout
- **Event-Driven**: SDK events → Risk rules → Enforcement
- **Logged**: 8 strategic checkpoints for runtime debugging ⭐ NEW

### Key Decisions
1. **Don't reimplement what SDK provides. Use SDK, add risk logic.**
2. **Write tests first (TDD). Run pytest before runtime checks.**
3. **Check test reports FIRST before asking "what's wrong?"**
4. **Use runtime smoke test to validate deployment readiness**

---

## 🧪 Test-Driven Development Workflow

**We use TDD** - Tests written first, then implementation.

**Workflow**:
1. Write test first (it fails - RED)
2. Write minimal code to pass (GREEN)
3. Refactor (REFACTOR)
4. Run `[s]` smoke test (validate runtime works)
5. Repeat

**Test Structure**: See `tests/` directory
- Use `pytest --collect-only` to see all available tests
- Use `ls -R tests/` to see current test structure
- Check `test_reports/latest.txt` for most recent results

**Complete guides**:
- `docs/testing/TESTING_GUIDE.md` - Core TDD guide
- `docs/testing/RUNTIME_DEBUGGING.md` - Runtime validation
- `docs/testing/WORKING_WITH_AI.md` - AI workflow

---

## 🤖 Agent Guidelines

### For AI Agents Working on This Project

**Before Starting Work**:
1. ✅ Read `CLAUDE.md` (this file)
2. ✅ Read `docs/current/PROJECT_STATUS.md` (current state)
3. ✅ Read `test_reports/latest.txt` (latest test results)
4. ✅ Read `docs/testing/TESTING_GUIDE.md` (testing approach)
5. ✅ Read `.claude/prompts/runtime-guidelines.md` (runtime protocols)

**During Work**:
1. ✅ Write tests first (TDD)
2. ✅ Run tests via menu: `python run_tests.py`
3. ✅ Check `test_reports/latest.txt` for results
4. ✅ Use SDK where possible (don't reinvent)
5. ✅ Add SDK logging at strategic checkpoints
6. ✅ Document as you build

**Before Finishing**:
1. ✅ Run `[g]` Gate test (tests + smoke combo)
2. ✅ Check exit code 0 for smoke test
3. ✅ Update `docs/current/PROJECT_STATUS.md`
4. ✅ Verify all 8 checkpoints log correctly

**Runtime Testing Protocol**:
- After implementing feature → Write tests → Run tests → Run smoke test
- If smoke fails → Check logs → Find which checkpoint failed → Fix issue
- Use `docs/testing/RUNTIME_DEBUGGING.md` troubleshooting flowchart

---

## 🔄 Update This File When

- [ ] Major architecture changes
- [ ] Documentation reorganization
- [ ] New critical features added (like Runtime Reliability Pack)
- [ ] Testing system changes
- [ ] Progress milestones (25% → 50% → etc.)
- [ ] Next priority changes

---

## ✅ Session Checklist

### At Start of Session
- [ ] Read `CLAUDE.md` (this file)
- [ ] Read `docs/current/PROJECT_STATUS.md` (current state)
- [ ] Read `test_reports/latest.txt` (latest test results)
- [ ] Read `docs/testing/README.md` (testing navigation)
- [ ] Check what tests exist (`pytest --collect-only`)

### During Session
- [ ] Write tests first (TDD)
- [ ] Use SDK where possible
- [ ] Add SDK logging at checkpoints if touching core files
- [ ] Run tests via menu (`python run_tests.py`)
- [ ] Check `test_reports/latest.txt` after each run
- [ ] Document as you build

### Before Deploying
- [ ] Run `[g]` Gate test (full suite + smoke)
- [ ] Verify exit code 0
- [ ] Check all 8 checkpoints log correctly
- [ ] Run `[r]` Soak test for major changes

### End of Session
- [ ] Run full test suite (`python run_tests.py` → `[1]`)
- [ ] Run smoke test (`[s]`)
- [ ] Update `docs/current/PROJECT_STATUS.md` if progress made
- [ ] Archive old docs if major changes
- [ ] Git commit with clear message

---

## 🎓 Understanding the Project in 5 Minutes

**What**: Trading risk manager for TopstepX futures accounts
**Why**: Prevent account violations, automate risk enforcement
**How**: SDK handles trading, we add risk rules on top

**12 Risk Rules**: See `docs/PROJECT_DOCS/rules/` for specifications
- Check `src/risk_manager/rules/` to see which are implemented
- Check `docs/current/PROJECT_STATUS.md` for completion status

**Tech Stack**:
- Python 3.12+ async
- Project-X-Py SDK v3.5.9 (handles all trading)
- Pydantic (config/validation)
- SQLite (state persistence)
- pytest (TDD testing)
- Runtime Reliability Pack (runtime validation) ⭐ NEW

**Testing System**:
- Interactive menu: `python run_tests.py`
- Auto-save reports: `test_reports/latest.txt`
- Runtime checks: Smoke, Soak, Trace, Logs, Env
- 8-checkpoint logging: Find exactly where runtime fails

---

## 💡 If You're Confused

**Read in this exact order**:
1. This file (`CLAUDE.md`)
2. `test_reports/latest.txt` - See if tests are passing
3. `docs/current/PROJECT_STATUS.md` - See what's done
4. `docs/testing/README.md` - Understand testing system
5. `docs/current/SDK_INTEGRATION_GUIDE.md` - Understand SDK-first approach

**Still confused?**
- Look at `examples/` directory - See it working
- Run `python run_tests.py → [s]` - Runtime smoke test
- Read `docs/testing/RUNTIME_DEBUGGING.md` - Complete troubleshooting guide
- Read `docs/PROJECT_DOCS/INTEGRATION_NOTE.md` - Understand spec history

---

## 🚀 Ready to Code?

**Quick Start**:
```bash
# 1. Check latest test results
cat test_reports/latest.txt

# 2. Read current status
cat docs/current/PROJECT_STATUS.md

# 3. Pick a task from PROJECT_STATUS.md

# 4. Write test first
# Create test in tests/unit/ or tests/integration/

# 5. Run tests
python run_tests.py → [2] for unit tests

# 6. Check results
cat test_reports/latest.txt

# 7. Implement feature
# Create code in src/

# 8. Run tests again
python run_tests.py → [2]

# 9. Run smoke test (validates runtime works)
python run_tests.py → [s]
# Check exit code: 0 = good, 1 = exception, 2 = stalled

# 10. Update PROJECT_STATUS.md when done
```

**Let's build! 🛡️**

---

**Last Updated**: 2025-10-23
**Next Update**: When testing system or documentation changes significantly
**Maintainer**: Update this when project structure or testing system changes

---

## 📋 Quick Reference Card

**Most Important Files for Agents**:
1. `CLAUDE.md` ← You are here
2. `docs/current/PROJECT_STATUS.md` ← Current progress
3. `test_reports/latest.txt` ← Latest test results
4. `docs/testing/TESTING_GUIDE.md` ← How to test
5. `docs/testing/RUNTIME_DEBUGGING.md` ← How to debug runtime

**Most Important Commands**:
1. `python run_tests.py` ← Run tests with menu
2. `cat test_reports/latest.txt` ← Check latest results
3. `cat docs/current/PROJECT_STATUS.md` ← Check progress
4. `pytest --collect-only` ← See available tests
5. `python run_tests.py → [s]` ← Runtime smoke test

**Exit Codes to Know**:
- `0` = Success
- `1` = Exception (check logs)
- `2` = Boot stalled (check event subscriptions)

**8 Checkpoints to Look For**:
```
🚀 Service Start
✅ Config Loaded
✅ SDK Connected
✅ Rules Initialized
✅ Event Loop Running
📨 Event Received
🔍 Rule Evaluated
⚠️ Enforcement Triggered
```

**That's everything. Welcome to Risk Manager V34! 🎯**
