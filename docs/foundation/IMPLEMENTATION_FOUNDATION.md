# Risk Manager V34 - Implementation Foundation

**THE AUTHORITATIVE FOUNDATION FOR PROJECT #34**

Last Updated: 2025-10-25
Status: Foundation for finishing the project
Purpose: Ties together ALL analysis, specifications, implementation, and testing

---

## 🎯 START HERE

**You are here because:**
- You're an AI agent building features
- You're a developer joining the project
- You need to know: What to build, how to build it, where everything is

**This document ties together:**
- Analysis (Waves 1-3) - WHAT exists and WHAT's missing
- Specifications (unified specs) - HOW to build it
- Implementation (roadmap & contracts) - PROCESS and interfaces
- Testing (test strategy & runtime validation) - PROVE it works
- Everything you need to succeed

**This is THE single document that connects ALL the pieces.**

---

## 📚 The Complete System (How It All Connects)

### Layer 1: WHAT to Build (Analysis)

The analysis phase discovered 88 features across the entire project through comprehensive documentation analysis.

#### Wave 1: Feature Discovery (COMPLETE INVENTORY)
- **Location**: `docs/analysis/wave1-feature-inventory/`
- **Purpose**: Complete catalog of all 88 features documented anywhere
- **Start**: `00-WAVE1-SUMMARY.md`
- **Key Metrics**:
  - 201 markdown files analyzed
  - 8 specialized inventory reports
  - ~380KB, ~13,000 lines of analysis
  - 88 features cataloged across all domains
- **Reports**:
  1. `01-RISK-RULES-INVENTORY.md` - 13 risk rules
  2. `02-SDK-INTEGRATION-INVENTORY.md` - SDK patterns, 93% code reduction
  3. `03-ARCHITECTURE-INVENTORY.md` - System design, modules
  4. `04-TESTING-INVENTORY.md` - Testing infrastructure
  5. `05-SECURITY-CONFIG-INVENTORY.md` - Windows UAC, config system
  6. `06-IMPLEMENTATION-STATUS-INVENTORY.md` - What's built (26/88)
  7. `07-DEVELOPER-EXPERIENCE-INVENTORY.md` - CLI, tools
  8. `08-TECHNICAL-REFERENCE-INVENTORY.md` - Specs, APIs
- **Use**: Understanding project scope, discovering features

#### Wave 2: Gap Analysis (WHAT'S MISSING)
- **Location**: `docs/analysis/wave2-gap-analysis/`
- **Purpose**: Identify the 62 missing features (~70% incomplete)
- **Key Findings**:
  - 30% complete (26 of 88 features)
  - 3 critical state managers missing (BLOCKS 8 rules!)
  - 10 of 13 risk rules missing
  - CLI system 0% complete
  - Windows Service 0% complete
  - Quote data integration missing
- **Reports**:
  1. `01-RISK-RULES-GAPS.md` - 10 missing rules, 3-4 weeks effort
  2. `02-STATE-MANAGEMENT-GAPS.md` - 3 managers (MOD-002, 003, 004)
  3. `03-CLI-SYSTEM-GAPS.md` - 13 commands, 5 weeks effort
  4. `04-CONFIG-SYSTEM-GAPS.md` - YAML loaders, validators
  5. `05-DEPLOYMENT-GAPS.md` - Windows Service wrapper
  6. `06-TESTING-GAPS.md` - Coverage 18% → 90%
  7. `07-INFRASTRUCTURE-GAPS.md` - Date/time utils, monitoring
- **Critical**: Identifies blockers and dependencies
- **Use**: Understanding what needs building

#### Wave 3: Spec Consolidation (DESIGN DECISIONS)
- **Location**: `docs/analysis/wave3-spec-consolidation/`
- **Purpose**: Resolved conflicts using user's architectural guidance
- **Key Principle**: **User decisions are Resolution Rule #1**
- **Conflicts Resolved**:
  - RULE-004/005 enforcement type (trade-by-trade vs hard lockout)
  - Manual unlock usage (emergency only, not for trading lockouts)
  - Config reset times (configurable, not hardcoded)
  - Testing approach (TDD mandatory)
- **Status**: All conflicts resolved, unified specs created
- **Use**: Understanding design decisions and architectural choices

---

### Layer 2: HOW to Build (Specifications)

The unified specifications are THE SOURCE OF TRUTH for all implementation details.

#### Unified Specifications (THE SINGLE SOURCE OF TRUTH)
- **Location**: `docs/specifications/unified/`
- **Purpose**: Complete implementation specs for all 88 features
- **Status**: Wave 3 complete - all specs unified and conflict-free
- **Authority**: This directory supersedes ALL other documentation

**Structure**:

```
docs/specifications/unified/
├── README.md                           # Navigation guide
├── UNIFICATION_REPORT.md               # How specs were consolidated
│
├── rules/                              # All 13 risk rules
│   ├── README.md                       # Rules overview
│   ├── RULE-001-max-contracts.md
│   ├── RULE-002-max-contracts-per-instrument.md
│   ├── RULE-003-daily-realized-loss.md       # HARD LOCKOUT
│   ├── RULE-004-daily-unrealized-loss.md     # TRADE-BY-TRADE
│   ├── RULE-005-max-unrealized-profit.md     # TRADE-BY-TRADE
│   ├── RULE-006-trade-frequency-limit.md
│   ├── RULE-007-cooldown-after-loss.md
│   ├── RULE-008-no-stop-loss-grace.md
│   ├── RULE-009-session-block-outside.md
│   ├── RULE-010-auth-loss-guard.md
│   ├── RULE-011-symbol-blocks.md
│   ├── RULE-012-trade-management.md
│   └── RULE-013-daily-realized-profit.md     # HARD LOCKOUT
│
├── architecture/                       # System design
│   ├── README.md
│   ├── system-architecture.md          # Overall architecture
│   ├── MODULES_SUMMARY.md              # All modules (MOD-001 through MOD-004)
│   ├── daemon-lifecycle.md             # Service lifecycle
│   └── DELIVERABLES.md                 # What to build
│
├── configuration/                      # Config schemas
│   ├── README.md
│   ├── risk-config-schema.md           # All 13 rules config
│   ├── timers-config-schema.md         # Daily reset, session hours
│   ├── accounts-config-schema.md       # Account mappings
│   ├── api-config-schema.md            # SDK credentials
│   └── config-validation.md            # Validation rules
│
├── sdk-integration.md                  # How to use Project-X-Py SDK
├── quote-data-integration.md           # Quote subscriptions, throttling
├── event-handling.md                   # Event flow, types
│
├── admin-cli-reference.md              # 6 admin commands
├── trader-cli-reference.md             # 7 trader commands
├── CLI-SPECS-SUMMARY.md                # Complete CLI overview
├── cli-security-model.md               # Windows UAC, ACL
│
├── testing-strategy.md                 # TDD, test pyramid
├── test-coverage-requirements.md       # Coverage targets (90%+)
└── runtime-validation-strategy.md      # 8-checkpoints, smoke tests
```

**Each spec contains**:
- Complete implementation details
- Code examples
- Configuration examples
- Test coverage requirements
- SDK integration details
- Dependencies and blockers

**Use**: This is your implementation bible. Read the spec FIRST before coding.

---

### Layer 3: WORKFLOW (Implementation Process)

These documents guide the day-to-day workflow of building features.

#### Implementation Roadmap (CENTRAL TRACKER)
- **Location**: `IMPLEMENTATION_ROADMAP.md` (root)
- **Purpose**: What to build next, track progress
- **Status**: 30% complete (26 of 88 features)
- **Next Priority**: Phase 1 - State Managers (MOD-003, 002, 004)
- **Format**: Checkboxes for all features
- **Structure**:
  ```
  Phase 1: State Managers (3 items) - 0% complete
  Phase 2: Risk Rules (13 items) - 23% complete (3/13)
  Phase 3: SDK Integration (4 items) - 50% complete (2/4)
  Phase 4: CLI System (13 items) - 0% complete
  Phase 5: Configuration (4 items) - 25% complete (1/4)
  Phase 6: Windows Service (5 items) - 0% complete
  Phase 7: Infrastructure (6 items) - 33% complete (2/6)
  Phase 8: Testing (4 items) - 25% complete (1/4)
  ```
- **Each item includes**:
  - [ ] Checkbox for tracking
  - Spec path reference
  - Contract reference
  - Dependencies
  - Estimated effort
- **Use**: Daily workflow - pick item, implement, check off

#### Agent Guidelines (HOW TO IMPLEMENT)
- **Location**: `AGENT_GUIDELINES.md` (root)
- **Purpose**: Complete workflow from start to finish
- **Steps**:
  1. Read the Roadmap (pick item)
  2. Read the Specifications (understand feature)
  3. Check Interfaces & Contracts (APIs)
  4. Write Tests (TDD - RED)
  5. Implement Feature (GREEN)
  6. Run Tests (verify passing)
  7. Refactor (if needed)
  8. Run Integration Tests (if applicable)
  9. Update Roadmap (check off item)
  10. Commit Changes (git)
- **Common Mistakes Documented**:
  - Using wrong parameter names (event_type vs type)
  - Hardcoding reset times (should be configurable)
  - Wrong enforcement (trade-by-trade vs hard lockout)
  - Not writing tests first
  - Not updating roadmap
- **Use**: Your implementation bible - follow these steps exactly

#### Contracts Reference (PREVENT API MISMATCHES)
- **Location**: `CONTRACTS_REFERENCE.md` (root)
- **Purpose**: Exact API signatures (internal & SDK)
- **Prevents**: Parameter name mismatches, wrong types, version mismatches
- **Contains**:
  1. **Internal Interfaces** (Our code → Our code)
     - RiskRule base class
     - LockoutManager API
     - TimerManager API
     - ResetScheduler API
     - PnLTracker API
  2. **External Interfaces** (Our code → SDK)
     - TradingSuite (Project-X-Py v3.5.9+)
     - QuoteManager
     - EventBus
  3. **Schemas** (Database/Events/Config)
     - Database tables (violations, lockouts, pnl_tracking, timers)
     - Event structures (RiskEvent, EventType enum)
     - Config structures (YAML schemas)
  4. **Event Contracts**
     - TRADE_EXECUTED format
     - POSITION_UPDATED format
     - QUOTE_UPDATED format
     - RULE_VIOLATED format
  5. **Common Patterns**
     - Rule implementation template
     - SDK integration template
- **Use**: Check EVERY interface before implementing

---

### Layer 4: VALIDATION (Prove It Works)

Testing ensures features work correctly both in tests and runtime.

#### Testing Strategy (TDD WORKFLOW)
- **Location**: `docs/specifications/unified/testing-strategy.md`
- **Purpose**: TDD workflow, test pyramid, test organization
- **Structure**:
  - **Unit Tests (60%)**: Fast, isolated, mocked
  - **Integration Tests (30%)**: Real SDK, database
  - **E2E Tests (10%)**: Full workflows
  - **Runtime Validation**: Cross-cutting (smoke, soak, trace)
- **TDD Workflow**:
  1. Write test (RED - fails)
  2. Write code (GREEN - passes)
  3. Refactor (still passes)
- **Test Organization**:
  ```
  tests/
  ├── unit/              # Fast tests, mocked dependencies
  ├── integration/       # Real SDK connections
  ├── e2e/               # Full system tests
  ├── runtime/           # Runtime reliability tests
  ├── fixtures/          # Shared fixtures
  └── conftest.py        # Pytest config
  ```
- **Interactive Test Runner**:
  - `python run_tests.py`
  - 20+ menu options
  - Auto-saves reports to `test_reports/latest.txt`
- **Use**: Write tests FIRST, always

#### Runtime Validation (THE 33-PROJECT KILLER PREVENTION)
- **Location**: `docs/specifications/unified/runtime-validation-strategy.md`
- **Purpose**: 8-checkpoint system + smoke tests
- **Problem**: "Tests pass but runtime broken" killed projects #1-33
- **Solution**: Mandatory runtime validation after tests pass

**8-Checkpoint System**:
```
Checkpoint 1: 🚀 Service Start
Checkpoint 2: ✅ Config Loaded
Checkpoint 3: ✅ SDK Connected
Checkpoint 4: ✅ Rules Initialized
Checkpoint 5: ✅ Event Loop Running
Checkpoint 6: 📨 Event Received
Checkpoint 7: 🔍 Rule Evaluated
Checkpoint 8: ⚠️ Enforcement Triggered
```

**Location in Code**:
- Checkpoints 1-4: `src/risk_manager/core/manager.py`
- Checkpoints 5-7: `src/risk_manager/core/engine.py`
- Checkpoint 8: `src/risk_manager/sdk/enforcement.py`

**Runtime Reliability Pack** (5 capabilities):

1. **Smoke Test** (`[s]` in menu)
   - Boots system and validates first event fires within 8 seconds
   - Exit code 0 = Success (first event observed)
   - Exit code 1 = Exception occurred (see logs)
   - Exit code 2 = Boot stalled (no events within timeout)
   - **Mandatory**: Feature NOT done until smoke test passes

2. **Soak Test** (`[r]` in menu)
   - Extended 30-60s runtime validation
   - Catches memory leaks, deadlocks, resource exhaustion
   - Use before major deployments

3. **Trace Mode** (`[t]` in menu)
   - Deep async task debugging (ASYNC_DEBUG=1)
   - Output: `runtime_trace.log` with all pending tasks
   - Use when service starts but hangs/stalls

4. **Log Viewer** (`[l]` in menu)
   - Stream logs in real-time or view last 100 lines
   - Location: `data/logs/risk_manager.log`
   - Use for debugging runtime issues

5. **Env Snapshot** (`[e]` in menu)
   - Shows configuration, env vars, Python version
   - Use for configuration troubleshooting

**Exit Code Meanings**:
- `0` = Success (feature works!)
- `1` = Exception (check logs for stack trace)
- `2` = Boot stalled (check event subscriptions)

**Use**: After tests pass, PROVE runtime works with exit code 0

#### Test Infrastructure (AUTO-REPORTS)
- **Location**: `run_tests.py` (root)
- **Purpose**: Interactive test menu with auto-reports
- **Reports**: `test_reports/latest.txt` (agents read this)
- **Auto-Save**: Every test run saves to latest.txt + timestamped archive
- **Format**:
  - Full pytest output with colors
  - Pass/fail status
  - Exit code
  - Timestamp
  - Complete tracebacks for failures
- **Use**: Run tests, check results, iterate

---

## 🔄 The Complete Workflow (Start to Finish)

This is THE workflow every agent and developer follows. No exceptions.

### Step 1: Pick What to Build
```bash
# Read the roadmap
cat IMPLEMENTATION_ROADMAP.md

# Find first unchecked [ ] item in "Next Priority" phase
# Note dependencies and blockers
# Current priority: MOD-003 (Timer Manager) - No blockers!
```

### Step 2: Understand the Feature
```bash
# Read Wave 2 gap analysis (context)
cat docs/analysis/wave2-gap-analysis/[relevant-domain].md
# → Understand what's missing, why, effort

# Read unified spec (complete details)
cat docs/specifications/unified/[feature-spec].md
# → Complete implementation details, examples

# Read Wave 3 consolidation (if conflicts existed)
cat docs/analysis/wave3-spec-consolidation/[relevant-doc].md
# → Understand design decisions
```

**Example for MOD-003 (Timer Manager)**:
```bash
# Gap analysis
cat docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md
# → MOD-003 section: Why needed, effort (1 week), blocks what

# Unified spec
cat docs/specifications/unified/architecture/MODULES_SUMMARY.md
# → MOD-003 section: Complete API, examples, tests

# No conflicts for MOD-003, skip Wave 3
```

### Step 3: Check Interfaces & Contracts
```bash
# Read contracts reference
cat CONTRACTS_REFERENCE.md

# Find TimerManager API
# → Internal Interfaces → TimerManager
# → Note EXACT signatures:
#   - create_timer(timer_id, duration, callback, auto_restart)
#   - cancel_timer(timer_id)
#   - get_time_remaining(timer_id)
#   - is_session_active()

# Find Database schema
# → Schemas → timers table
# → Note EXACT columns:
#   - timer_id (TEXT UNIQUE)
#   - start_time (REAL)
#   - duration_seconds (REAL)
#   - etc.
```

### Step 4: Write Tests (TDD - RED)
```bash
# Create test file
touch tests/unit/test_state/test_timer_manager.py

# Write tests following spec's "Test Coverage" section
# Example tests:
# - test_create_timer()
# - test_cancel_timer()
# - test_timer_expiration()
# - test_auto_restart()
# - test_session_active()
# etc. (20 tests per spec)

# Run tests (they should fail - feature not implemented yet)
python run_tests.py
# Select: [2] Unit tests

# Check results
cat test_reports/latest.txt
# Should show: 20 failures (expected - RED phase)
```

### Step 5: Implement Feature (GREEN)
```bash
# Create implementation file
touch src/risk_manager/state/timer_manager.py

# Follow unified spec EXACTLY
# Use contracts from CONTRACTS_REFERENCE.md
# Add logging at strategic checkpoints

# Implement TimerManager class with:
# - __init__(self, db: Database)
# - create_timer() - exact signature from contract
# - cancel_timer() - exact signature from contract
# - get_time_remaining() - exact signature from contract
# - is_session_active() - exact signature from contract

# Run tests (they should pass now)
python run_tests.py
# Select: [2] Unit tests

# Check results
cat test_reports/latest.txt
# Should show: 20 passed - GREEN phase!
```

### Step 6: Runtime Validation (PROVE IT WORKS)
```bash
# Run smoke test (MANDATORY - can't skip this!)
python run_tests.py
# Select: [s] Runtime SMOKE

# Wait 8 seconds
# Check exit code

# Exit code 0? ✅ Feature works in runtime!
# Exit code 1? ❌ Exception - read logs, debug
# Exit code 2? ❌ Stalled - check event subscriptions

# If not 0, debug:
cat data/logs/risk_manager.log
# Find last checkpoint emoji (🚀 ✅ ✅ ✅ ✅ 📨 🔍 ⚠️)
# Read runtime-validation-strategy.md troubleshooting flowchart
# Fix issue, repeat until exit code 0
```

### Step 7: Update Progress
```bash
# Edit roadmap
nano IMPLEMENTATION_ROADMAP.md

# Change checkbox from [ ] to [x]
# Before: - [ ] **Create `src/risk_manager/state/timer_manager.py`**
# After:  - [x] **Create `src/risk_manager/state/timer_manager.py`**

# Update "Last Updated" timestamp
# Update progress percentages if phase complete
```

### Step 8: Commit & Push
```bash
# Stage files
git add -A

# Commit with descriptive message
git commit -m "Implemented MOD-003: Timer Manager

- Created timer_manager.py with countdown timer support
- Added database schema for timers table
- Integrated with config/timers.yaml
- Added 20 unit tests (all passing)
- Coverage: 92%
- Smoke test: PASSING (exit code 0)

Refs: docs/specifications/unified/architecture/MODULES_SUMMARY.md (MOD-003)

🤖 Generated with Claude Code"

# Push
git push
```

---

## 🗺️ Quick Navigation (Where to Find Everything)

### "Where's the spec for RULE-003?"
```bash
docs/specifications/unified/rules/RULE-003-daily-realized-loss.md
```

### "What's the API for LockoutManager?"
```bash
cat CONTRACTS_REFERENCE.md
# Search for: "LockoutManager"
# Section: Internal Interfaces → LockoutManager
```

### "What tests are failing?"
```bash
cat test_reports/latest.txt
# Auto-saved after every test run
```

### "How do I run smoke tests?"
```bash
python run_tests.py
# Select: [s] Runtime SMOKE
# Check exit code: 0=success, 1=exception, 2=stalled
```

### "What's blocking RULE-003?"
```bash
cat IMPLEMENTATION_ROADMAP.md
# Search for: "RULE-003"
# Dependencies: MOD-002 (Lockout), MOD-003 (Timer), MOD-004 (Reset)
```

### "Where's the deployment checklist?"
```bash
cat IMPLEMENTATION_ROADMAP.md
# Search for: "Deployment Readiness Checklist"
```

### "What's the current progress?"
```bash
cat IMPLEMENTATION_ROADMAP.md
# Top of file: "Overall Progress: 30% (26 of 88 features)"
# Progress Summary table shows each phase
```

### "How do I add logging?"
```bash
cat docs/specifications/unified/runtime-validation-strategy.md
# Search for: "8-Checkpoint System"
# Shows where to add logging and format
```

### "Where's the test strategy?"
```bash
docs/specifications/unified/testing-strategy.md
```

### "What's the gap analysis for rules?"
```bash
docs/analysis/wave2-gap-analysis/01-RISK-RULES-GAPS.md
```

### "Where's the unified spec for MOD-003?"
```bash
docs/specifications/unified/architecture/MODULES_SUMMARY.md
# Search for: "MOD-003"
```

### "How do I view logs?"
```bash
# Via menu
python run_tests.py
# Select: [l] View/Tail LOGS

# Or directly
cat data/logs/risk_manager.log
```

---

## 🏗️ The Foundation Architecture

Visual representation of how everything connects:

```
┌─────────────────────────────────────────────────┐
│  IMPLEMENTATION_FOUNDATION.md (YOU ARE HERE)    │
│  └─> THE single document that ties it all       │
└─────────────────────────────────────────────────┘
           │
           ├─> Analysis (WHAT to build)
           │   ├─> Wave 1: Feature discovery (88 features cataloged)
           │   │   └─> docs/analysis/wave1-feature-inventory/
           │   │       ├─> 00-WAVE1-SUMMARY.md
           │   │       ├─> 01-RISK-RULES-INVENTORY.md
           │   │       ├─> 02-SDK-INTEGRATION-INVENTORY.md
           │   │       ├─> 03-ARCHITECTURE-INVENTORY.md
           │   │       ├─> 04-TESTING-INVENTORY.md
           │   │       ├─> 05-SECURITY-CONFIG-INVENTORY.md
           │   │       ├─> 06-IMPLEMENTATION-STATUS-INVENTORY.md
           │   │       ├─> 07-DEVELOPER-EXPERIENCE-INVENTORY.md
           │   │       └─> 08-TECHNICAL-REFERENCE-INVENTORY.md
           │   │
           │   ├─> Wave 2: Gap analysis (62 missing features)
           │   │   └─> docs/analysis/wave2-gap-analysis/
           │   │       ├─> 01-RISK-RULES-GAPS.md
           │   │       ├─> 02-STATE-MANAGEMENT-GAPS.md
           │   │       ├─> 03-CLI-SYSTEM-GAPS.md
           │   │       ├─> 04-CONFIG-SYSTEM-GAPS.md
           │   │       ├─> 05-DEPLOYMENT-GAPS.md
           │   │       ├─> 06-TESTING-GAPS.md
           │   │       └─> 07-INFRASTRUCTURE-GAPS.md
           │   │
           │   └─> Wave 3: Conflict resolution (design decisions)
           │       └─> docs/analysis/wave3-spec-consolidation/
           │
           ├─> Specifications (HOW to build)
           │   └─> docs/specifications/unified/
           │       ├─> README.md (navigation)
           │       ├─> rules/ (13 risk rules)
           │       │   ├─> RULE-001 through RULE-013
           │       │   └─> README.md
           │       ├─> architecture/ (system design)
           │       │   ├─> MODULES_SUMMARY.md (MOD-001 to MOD-004)
           │       │   ├─> system-architecture.md
           │       │   └─> daemon-lifecycle.md
           │       ├─> configuration/ (config schemas)
           │       │   ├─> risk-config-schema.md
           │       │   ├─> timers-config-schema.md
           │       │   ├─> accounts-config-schema.md
           │       │   └─> api-config-schema.md
           │       ├─> testing-strategy.md
           │       ├─> runtime-validation-strategy.md
           │       ├─> sdk-integration.md
           │       ├─> quote-data-integration.md
           │       ├─> admin-cli-reference.md
           │       ├─> trader-cli-reference.md
           │       └─> cli-security-model.md
           │
           ├─> Workflow (PROCESS)
           │   ├─> IMPLEMENTATION_ROADMAP.md (what to build next)
           │   │   └─> 30% complete, 8 phases, all checkboxes
           │   ├─> AGENT_GUIDELINES.md (how to implement)
           │   │   └─> 10-step workflow, common mistakes
           │   └─> CONTRACTS_REFERENCE.md (interfaces)
           │       └─> Internal + External + Schemas
           │
           └─> Validation (PROVE IT WORKS)
               ├─> testing-strategy.md (TDD)
               │   └─> Unit (60%), Integration (30%), E2E (10%)
               ├─> runtime-validation-strategy.md (smoke)
               │   └─> 8 checkpoints, exit codes, troubleshooting
               └─> run_tests.py → test_reports/latest.txt
                   └─> Auto-save, timestamped archives
```

---

## ⚠️ Critical Success Factors (Why 33 Projects Failed)

### The Failure Pattern (Projects #1-33)
```
Write tests → Tests pass ✅ → Mark complete → Deploy → Runtime broken ❌
```

**Why this failed**:
- Tests validate logic correctness (unit/integration/e2e)
- Tests DON'T validate system liveness
- Runtime could boot but never emit events
- No way to know it's broken until production
- 33 projects failed this way

### The Success Pattern (Project #34)
```
Write tests → Tests pass ✅ → Smoke test → Exit code 0 ✅ → Mark complete → Deploy ✅
```

**Why this works**:
- Tests validate logic correctness
- Smoke test validates system liveness
- Exit code 0 proves first event fires
- Can't deploy without exit code 0
- Project #34 WILL succeed

### Enforcement Rules

**Definition of Done includes**:
- [ ] Tests passing (unit/integration/e2e)
- [ ] Smoke test passing (exit code 0) ← **MANDATORY**
- [ ] Roadmap updated (checkbox checked)
- [ ] Git committed and pushed

**Roadmap includes**:
- Runtime validation checkboxes for each feature
- Can't skip smoke test
- Agents CANNOT mark feature complete without exit code 0

**Test menu enforces**:
- `[g]` Gate test = Tests + Smoke combo
- Use this before marking complete
- Both must pass

---

## 📋 Complete Feature Checklist Template

Use this checklist for ANY feature:

```markdown
Feature: [NAME]
Spec: [PATH TO UNIFIED SPEC]
Contract: [CONTRACTS_REFERENCE.md SECTION]
Effort: [X days]

Implementation Checklist:
[ ] Read Wave 2 gap analysis (context)
[ ] Read unified spec (details)
[ ] Check contracts (interfaces)
[ ] Write unit tests (TDD - RED)
[ ] Implement feature (GREEN)
[ ] Tests passing (test_reports/latest.txt)
[ ] Add logging (if applicable)
[ ] Run smoke test (exit code 0) ← MANDATORY
[ ] Integration tests (if applicable)
[ ] Update IMPLEMENTATION_ROADMAP.md ([x])
[ ] Git commit + push
```

**Example for MOD-003 (Timer Manager)**:

```markdown
Feature: MOD-003 (Timer Manager)
Spec: docs/specifications/unified/architecture/MODULES_SUMMARY.md (MOD-003)
Contract: CONTRACTS_REFERENCE.md → Internal Interfaces → TimerManager
Effort: 1 week

Implementation Checklist:
[ ] Read docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md
[ ] Read docs/specifications/unified/architecture/MODULES_SUMMARY.md (MOD-003)
[ ] Check CONTRACTS_REFERENCE.md → TimerManager API
[ ] Write 20 unit tests in tests/unit/test_state/test_timer_manager.py
[ ] Implement src/risk_manager/state/timer_manager.py
[ ] Run python run_tests.py → [2] → Check test_reports/latest.txt
[ ] Add logging if touching core manager/engine
[ ] Run python run_tests.py → [s] → Check exit code 0
[ ] No integration tests needed for this feature
[ ] Update IMPLEMENTATION_ROADMAP.md → Phase 1 → MOD-003 → [x]
[ ] git commit -m "Implemented MOD-003: Timer Manager" && git push
```

---

## 🎓 Learning the System (New Agent Onboarding)

### Day 1: Understand the Foundation
```bash
# Hour 1: Read this document
cat docs/foundation/IMPLEMENTATION_FOUNDATION.md

# Hour 2: Read roadmap (what to build)
cat IMPLEMENTATION_ROADMAP.md

# Hour 3: Read guidelines (how to build)
cat AGENT_GUIDELINES.md

# Hour 4: Read contracts (interfaces)
cat CONTRACTS_REFERENCE.md
```

### Day 2: Explore the Specs
```bash
# Hour 1: Browse unified specs directory
ls -R docs/specifications/unified/

# Hour 2: Read a sample rule spec
cat docs/specifications/unified/rules/RULE-003-daily-realized-loss.md

# Hour 3: Read architecture specs
cat docs/specifications/unified/architecture/MODULES_SUMMARY.md

# Hour 4: Read testing strategies
cat docs/specifications/unified/testing-strategy.md
cat docs/specifications/unified/runtime-validation-strategy.md
```

### Day 3: Practice the Workflow
```bash
# Pick simple feature (utility function)
# Follow complete workflow (Steps 1-8)
# Write tests → Implement → Smoke test → Update roadmap
# Repeat until workflow is natural
```

---

## 🚀 Current Status (What's Built, What's Missing)

### Progress: 30% Complete (26 of 88 features)

**✅ What Works:**
- Database Manager (MOD-001)
- PnL Tracker
- 3 risk rules (RULE-001, 002, 012)
- SDK integration (partial - 2/4 complete)
- 8-checkpoint logging system (fully implemented)
- Interactive test runner with auto-reports
- Runtime Reliability Pack (smoke, soak, trace, logs, env)
- Test infrastructure (93 tests, 88 passing, 94.6%)

**❌ Critical Blockers:**
- **3 state managers (MOD-002, 003, 004)** ← BLOCKS 8 RULES!
  - MOD-003 (Timer Manager) - 0% - NO BLOCKERS, can start NOW!
  - MOD-002 (Lockout Manager) - 0% - Depends on MOD-003
  - MOD-004 (Reset Scheduler) - 0% - Depends on MOD-003
- 10 risk rules (RULE-003 through RULE-013, except 012)
- CLI system (0% - 13 commands)
- Windows Service (0%)
- Quote data integration (0%)
- Configuration system (25% - YAML loaders partial)

**🎯 Next Priority:**
- **MOD-003 (Timer Manager)**
- **Estimated**: 1 week
- **Blockers**: NONE - can start immediately!
- **Unblocks**: MOD-002, MOD-004, and 4 rules (RULE-006, 007, 008, 009)

### Testing Status
- **Current**: 93 tests total, 88 passing (94.6%), 18% coverage
- **Target**: 90%+ coverage, all passing
- **Failing**: 5 runtime tests (missing await, db_path args)
- **Needed**: 97 more unit tests, 29-38 integration tests, 8-13 e2e tests

---

## 📖 Complete Reference Index

### Root Directory (Entry Points)
- `IMPLEMENTATION_FOUNDATION.md` ← **YOU ARE HERE**
- `IMPLEMENTATION_ROADMAP.md` ← Central tracker, 30% complete
- `AGENT_GUIDELINES.md` ← How-to guide, 10-step workflow
- `CONTRACTS_REFERENCE.md` ← API interfaces, prevent mismatches
- `run_tests.py` ← Test runner, auto-reports
- `CLAUDE.md` ← AI assistant entry point

### Analysis (Context - WHAT's missing)
- `docs/analysis/wave1-feature-inventory/` ← 88 features discovered
  - `00-WAVE1-SUMMARY.md` ← Start here
  - 8 specialized inventory reports
- `docs/analysis/wave2-gap-analysis/` ← 62 missing features
  - 7 domain-specific gap reports
- `docs/analysis/wave3-spec-consolidation/` ← Conflicts resolved

### Specifications (Truth - HOW to build)
- `docs/specifications/unified/` ← **THE SOURCE OF TRUTH**
  - `README.md` ← Navigation guide
  - `rules/*.md` ← All 13 risk rules
  - `architecture/*.md` ← System architecture
  - `configuration/*.md` ← Config schemas
  - `testing-strategy.md` ← TDD, test pyramid
  - `runtime-validation-strategy.md` ← 8-checkpoints, smoke
  - `sdk-integration.md` ← Project-X-Py SDK usage
  - `admin-cli-reference.md` ← 6 admin commands
  - `trader-cli-reference.md` ← 7 trader commands
  - `cli-security-model.md` ← Windows UAC

### Testing & Validation
- `docs/specifications/unified/testing-strategy.md` ← TDD workflow
- `docs/specifications/unified/runtime-validation-strategy.md` ← Smoke tests
- `test_reports/latest.txt` ← Most recent results (auto-saved)
- `test_reports/YYYY-MM-DD_HH-MM-SS_*.txt` ← Timestamped archives

### Current Documentation (Legacy - DO NOT USE)
- `docs/current/` ← **DEPRECATED** - Use unified specs instead
- `docs/PROJECT_DOCS/` ← **PRE-SDK** - Historical reference only

---

## ✅ Success Metrics

### Project #34 Succeeds When:
- ✅ All 88 features implemented
- ✅ All tests passing (90%+ coverage)
- ✅ All smoke tests passing (exit code 0)
- ✅ Runtime observable (logs show features working)
- ✅ Deployment ready (checklist complete)
- ✅ No features marked complete without exit code 0

### Agents Succeed When:
- ✅ Know exactly what to build (roadmap is clear)
- ✅ Know exactly how to build (guidelines + specs are clear)
- ✅ Know exactly what interfaces to use (contracts are clear)
- ✅ Know exactly how to validate (tests + smoke are clear)
- ✅ Can navigate docs effortlessly (this foundation helps)
- ✅ Can find anything in <30 seconds
- ✅ Follow workflow without confusion
- ✅ Never mark feature complete without smoke test passing

### This Foundation Succeeds When:
- ✅ Agents can find ANY information in <30 seconds
- ✅ Complete workflow is crystal clear
- ✅ All pieces (analysis/specs/implementation/testing) connected
- ✅ No confusion about where to look
- ✅ Foundation prevents 33-project failure pattern
- ✅ Zero ambiguity in what to do next

---

## 🆘 When You're Stuck

### "I don't know what to build next"
**Solution**: Read `IMPLEMENTATION_ROADMAP.md` → Check "Next Priority" phase
**Answer**: MOD-003 (Timer Manager) - No blockers, can start now

### "I don't understand the feature"
**Solution**:
1. Read Wave 2 gap analysis for context
2. Read unified spec for complete details
3. Check examples in spec
4. Read similar implemented features

### "I don't know the API signature"
**Solution**: Check `CONTRACTS_REFERENCE.md` → Find the interface
**Example**: TimerManager → Internal Interfaces → TimerManager section

### "Tests are failing"
**Solution**:
1. Read `test_reports/latest.txt`
2. Check tracebacks for errors
3. Verify you're using correct contracts
4. Check for parameter name mismatches (event_type vs type)

### "Smoke test failing (exit code 1 or 2)"
**Solution**:
1. Check exit code meaning (0=success, 1=exception, 2=stalled)
2. Read logs: `cat data/logs/risk_manager.log`
3. Find last checkpoint emoji (🚀 ✅ ✅ ✅ ✅ 📨 🔍 ⚠️)
4. Read `runtime-validation-strategy.md` troubleshooting flowchart
5. Debug based on which checkpoint failed
6. Repeat until exit code 0

### "I don't know if I should use SDK or custom code"
**Solution**:
- **SDK-first approach**: Use Project-X-Py SDK where possible
- **Custom logic**: Only when SDK can't provide it
- **Check**: `docs/specifications/unified/sdk-integration.md`
- **Example**: Position closing → Use SDK TradingSuite.close_position()
- **Example**: Lockout timers → Custom (SDK doesn't have this)

### "I can't find a document"
**Solution**: Use the Quick Navigation section above
**Or**: Search this foundation document (Ctrl+F)

---

## 🎯 Next Actions

### For AI Agents (RIGHT NOW):
```bash
# 1. Read this foundation document (you just did!)
# 2. Read the roadmap
cat IMPLEMENTATION_ROADMAP.md

# 3. Pick first item: MOD-003 (Timer Manager)
# 4. Read the gap analysis
cat docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md

# 5. Read the unified spec
cat docs/specifications/unified/architecture/MODULES_SUMMARY.md
# Search for: "MOD-003"

# 6. Check the contract
cat CONTRACTS_REFERENCE.md
# Search for: "TimerManager"

# 7. Start implementing (follow 8-step workflow)
```

### For Developers (GETTING STARTED):
```bash
# 1. Read CLAUDE.md (AI assistant entry point)
cat CLAUDE.md

# 2. Read this foundation document
cat docs/foundation/IMPLEMENTATION_FOUNDATION.md

# 3. Read the roadmap
cat IMPLEMENTATION_ROADMAP.md

# 4. Check current test status
cat test_reports/latest.txt

# 5. Pick a feature and start building
```

### For Project Managers (STATUS CHECK):
```bash
# Check progress
cat IMPLEMENTATION_ROADMAP.md
# Look for: "Overall Progress: 30% (26 of 88 features)"

# Check test status
cat test_reports/latest.txt
# Look for: "93 tests, 88 passing (94.6%)"

# Check next priority
cat IMPLEMENTATION_ROADMAP.md
# Look for: "Next Priority: Phase 1 - State Managers"
```

---

## 📝 Maintenance

### When to Update This Document

Update this foundation when:
- [ ] Major architecture changes (new layers, modules)
- [ ] Documentation reorganization (files moved, renamed)
- [ ] New critical features added (like runtime pack was)
- [ ] Testing system changes (new capabilities)
- [ ] Progress milestones (50%, 75%, 100%)
- [ ] Next priority changes (new phase starts)
- [ ] Workflow changes (new steps added)
- [ ] Foundation not achieving <30s navigation goal

### How to Update

1. Edit this file
2. Update "Last Updated" timestamp
3. Update relevant sections
4. Test navigation (can you find things in <30s?)
5. Commit with clear message
6. Push to remote

### Version History

- **2025-10-25**: Initial creation - Tied together Waves 1-3, roadmap, guidelines, contracts
- **Next**: Update when Phase 1 (State Managers) complete

---

## 🏆 Final Checklist

Before starting any feature, verify you can answer these:

- [ ] What feature am I building? (From roadmap)
- [ ] Why is it needed? (From Wave 2 gap analysis)
- [ ] How do I build it? (From unified spec)
- [ ] What APIs do I use? (From contracts)
- [ ] What tests do I write? (From testing strategy)
- [ ] How do I validate it works? (Smoke test, exit code 0)
- [ ] What do I update when done? (Roadmap checkbox)

**If you can't answer all 7, read this foundation again.**

---

**Last Updated**: 2025-10-25
**Maintained By**: Update when foundation changes
**Authority**: THE foundation document - ties everything together
**Purpose**: Ensure agents can find anything in <30 seconds and follow clear workflow to success

---

**Let's finish project #34! 🚀**
