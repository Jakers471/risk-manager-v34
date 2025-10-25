# Agent Guidelines - Risk Manager V34 Implementation

**READ THIS FIRST** before implementing any features.

---

## 🎯 Foundation Integration

**NEW**: This project now has a unified foundation.

**Start with**:
1. Read `docs/foundation/IMPLEMENTATION_FOUNDATION.md` ← THE master document
2. Read `docs/foundation/QUICK_REFERENCE.md` ← One-page cheat sheet
3. Then return here for detailed workflow

**Key Updates**:
- Runtime validation is MANDATORY
- Smoke tests can't be skipped
- Logging is required for every feature
- Foundation ties everything together

---

## 🎯 Your Mission

Implement Risk Manager V34 features according to:
1. **Foundation docs** (master system integration)
2. **Unified specifications** (single source of truth)
3. **Implementation roadmap** (what to build, in what order)
4. **Contracts** (internal/external interfaces)
5. **Test requirements** (coverage targets)
6. **Runtime validation** (smoke tests MANDATORY)

---

## 📋 Workflow: How to Implement a Feature

### Step 1: Read the Roadmap

**File**: `IMPLEMENTATION_ROADMAP.md`

1. Check "Next Priority" phase
2. Find first unchecked [ ] item
3. Note the referenced spec paths
4. Note dependencies and blockers

---

### Step 2: Read the Specifications

**Every feature has 3 documents**:

#### A) Unified Spec (DETAILED REQUIREMENTS)
- **Location**: `docs/specifications/unified/`
- **Contains**: Complete specification with examples
- **Example**: For RULE-003, read `docs/specifications/unified/rules/RULE-003-daily-realized-loss.md`

#### B) Contract (INTERFACES & SCHEMAS)
- **Location**: `CONTRACTS_REFERENCE.md`
- **Contains**: API signatures, database schemas, event contracts
- **Example**: For RULE-003, check `RiskRule` base class contract

#### C) Gap Analysis (CONTEXT)
- **Location**: `docs/analysis/wave2-gap-analysis/`
- **Contains**: What's missing, effort estimates, dependencies
- **Example**: For rules, read `01-RISK-RULES-GAPS.md`

---

### Step 3: Write Tests First (TDD)

**ALWAYS write tests before implementation.**

#### 3.1 Read Testing Guide
- `docs/specifications/unified/testing-strategy.md` - TDD workflow
- `docs/specifications/unified/test-coverage-requirements.md` - Coverage targets

#### 3.2 Write Unit Tests
```bash
# Create test file
touch tests/unit/test_rules/test_daily_realized_loss.py

# Follow AAA pattern (Arrange, Act, Assert)
# Example from testing-strategy.md
```

#### 3.3 Run Tests (They Should Fail - RED)
```bash
python run_tests.py
# Select: [2] Unit tests
```

#### 3.4 Check Test Results
```bash
cat test_reports/latest.txt
# Shows failures, exit codes, tracebacks
```

---

### Step 4: Implement the Feature

#### 4.1 Follow the Spec EXACTLY
- Read unified spec completely
- Follow examples in spec
- Use contracts from `CONTRACTS_REFERENCE.md`

#### 4.2 Check for Internal Interfaces
**Question**: Does this feature call our code?
- **Yes**: Check `CONTRACTS_REFERENCE.md` → Internal Interfaces
- **Use**: Exact method signatures, parameters, return types

**Example**: RULE-003 calls `LockoutManager.lock_account()`
- Contract: `LockoutManager.lock_account(account_id: str, reason: str, unlock_time: datetime) -> bool`

#### 4.3 Check for External Interfaces (SDK)
**Question**: Does this feature call Project-X-Py SDK?
- **Yes**: Check `CONTRACTS_REFERENCE.md` → External Interfaces (SDK)
- **Use**: Exact SDK methods, versions, parameters

**Example**: RULE-003 closes positions via SDK
- Contract: `TradingSuite.close_all_positions(account_id: str) -> List[Order]`

#### 4.4 Check for Schemas (Database/Events)
**Question**: Does this feature store data or emit events?
- **Yes**: Check `CONTRACTS_REFERENCE.md` → Schemas
- **Use**: Exact table/event structures

**Example**: RULE-003 stores violations
- Schema: `violations` table with `(id, account_id, rule_id, timestamp, severity, message)`

---

### Step 5: Run Tests (They Should Pass - GREEN)

```bash
python run_tests.py
# Select: [2] Unit tests

# Check results
cat test_reports/latest.txt
# Should show: All tests passing
```

---

### Step 6: Refactor (If Needed)

- Clean up code
- Remove duplication
- Add docstrings
- Follow Python best practices

---

### Step 7: Runtime Validation (PROVE IT WORKS) ← UPDATED

**MANDATORY**: Can't mark complete without this.

**See**: `docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md` for complete guide.

**Quick steps**:
```bash
# Run smoke test
python run_tests.py → [s] Runtime SMOKE

# Check exit code
# 0 = SUCCESS → Continue to Step 8
# 1/2 = FAIL → Debug using protocol, fix, repeat

# Debug if needed
cat data/logs/risk_manager.log
grep "Checkpoint" data/logs/risk_manager.log | tail -1
```

**Can't skip this step.**

---

### Step 8: Run Integration Tests

**If feature integrates with SDK or database**:

```bash
python run_tests.py
# Select: [3] Integration tests

# Check results
cat test_reports/latest.txt
```

---

### Step 9: Update the Roadmap

**CRITICAL**: Update `IMPLEMENTATION_ROADMAP.md`

1. Change `[ ]` to `[x]` for completed item
2. Update "Last Updated" timestamp
3. Update progress percentages if phase complete

**Example**:
```markdown
### MOD-003: Timer Manager
- [x] **Create `src/risk_manager/state/timer_manager.py`** ← YOU DID THIS
- [x] **Smoke test passing (exit code 0)** ← MUST BE CHECKED
```

---

### Step 10: Commit Your Changes

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

Refs: docs/specifications/unified/architecture/MODULES_SUMMARY.md (MOD-003)

🤖 Generated with Claude Code"

# Push to remote
git push
```

---

## 🧪 Understanding the Test Menu

**File**: `run_tests.py`

**User runs this interactively. You can read results.**

### Common Menu Options

```
[1] Run ALL tests               - Run everything
[2] Run UNIT tests only         - Fast, isolated tests
[3] Run INTEGRATION tests       - Real SDK, database
[4] Run E2E tests only          - Full workflows
[s] Runtime SMOKE (8s timeout)  - Deployment validation
[g] GATE: Tests + Smoke combo   - Full validation
```

### Test Reports

**Location**: `test_reports/latest.txt`

**You can read this file to see test results**:
- Pass/fail status
- Exit codes (0=success, 1=exception, 2=stalled)
- Complete tracebacks for failures
- Warnings
- Summary statistics

**Example**:
```bash
# User runs tests via menu
# Results auto-save to test_reports/latest.txt

# You read results
cat test_reports/latest.txt
```

---

## 🔗 Understanding Contracts

**File**: `CONTRACTS_REFERENCE.md`

**Contains 3 types of contracts**:

### 1. Internal Interfaces (Our Code → Our Code)

**Example**: Risk Rule calls Lockout Manager
```python
# Contract defined in CONTRACTS_REFERENCE.md
class LockoutManager:
    def lock_account(
        self,
        account_id: str,
        reason: str,
        unlock_time: datetime
    ) -> bool:
        """Lock account until specified time."""
        pass
```

**You MUST**:
- Use exact method signature
- Pass correct parameter types
- Handle return value correctly

---

### 2. External Interfaces (Our Code → SDK)

**Example**: We close positions via SDK
```python
# Contract defined in CONTRACTS_REFERENCE.md
# From: Project-X-Py SDK v3.5.9+
class TradingSuite:
    async def close_all_positions(
        self,
        account_id: str
    ) -> List[Order]:
        """Close all open positions."""
        pass
```

**You MUST**:
- Use exact SDK version (v3.5.9+)
- Use exact method signature
- Use `await` (SDK is async)
- Handle List[Order] return

---

### 3. Schemas (Database/Events/Config)

**Example**: Violations table schema
```sql
-- Contract defined in CONTRACTS_REFERENCE.md
CREATE TABLE violations (
    id INTEGER PRIMARY KEY,
    account_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    severity TEXT NOT NULL,  -- 'WARNING', 'CRITICAL'
    message TEXT,
    resolved BOOLEAN DEFAULT 0
);
```

**You MUST**:
- Use exact column names
- Use exact data types
- Follow constraints (NOT NULL, etc.)

---

## ⚠️ Common Mistakes to Avoid

### ❌ Mistake 1: Using Wrong Parameter Names
**Example**: Using `type=` instead of `event_type=`
```python
# WRONG (from old docs)
event = RiskEvent(type=EventType.TRADE_EXECUTED)

# CORRECT (from CONTRACTS_REFERENCE.md)
event = RiskEvent(event_type=EventType.TRADE_EXECUTED)
```

**Fix**: Always check `CONTRACTS_REFERENCE.md` for exact signatures.

---

### ❌ Mistake 2: Hardcoding Reset Times
**Example**: Hardcoding midnight ET
```python
# WRONG
reset_time = "00:00"  # Hardcoded

# CORRECT (from unified spec)
reset_time = config.timers.daily_reset.time  # Configurable
timezone = config.timers.daily_reset.timezone
```

**Fix**: All timers/schedules MUST be configurable.

---

### ❌ Mistake 3: Implementing Wrong Enforcement
**Example**: RULE-004 with hard lockout
```python
# WRONG (RULE-004 is trade-by-trade, not hard lockout)
def enforce(self):
    self.lockout_manager.lock_account()  # ❌ Wrong!

# CORRECT (from RULE-004 unified spec)
def enforce(self):
    self.trading_integration.close_position(self.position_id)  # ✅ Close that position only
    # NO lockout, NO timer
```

**Fix**: Read unified spec carefully. RULE-004/005 are trade-by-trade. RULE-003/013 are hard lockout.

---

### ❌ Mistake 4: Not Writing Tests First
**Example**: Implementing feature, then writing tests
```python
# WRONG sequence:
1. Write implementation
2. Write tests
3. Tests fail → refactor implementation

# CORRECT sequence (TDD):
1. Write tests (they fail - RED)
2. Write implementation (tests pass - GREEN)
3. Refactor (tests still pass)
```

**Fix**: Always TDD. Tests first.

---

### ❌ Mistake 5: Not Updating Roadmap
**Example**: Completing feature but forgetting to update `IMPLEMENTATION_ROADMAP.md`

**Fix**: ALWAYS update roadmap checkboxes when complete.

---

## 🔍 How to Find Information

### "Where's the spec for RULE-003?"
```bash
# Check roadmap for path
cat IMPLEMENTATION_ROADMAP.md | grep "RULE-003"
# → Spec: docs/specifications/unified/rules/RULE-003-daily-realized-loss.md

# Read the spec
cat docs/specifications/unified/rules/RULE-003-daily-realized-loss.md
```

---

### "What's the API for LockoutManager?"
```bash
# Check contracts
cat CONTRACTS_REFERENCE.md | grep -A 20 "LockoutManager"
# → Shows complete API with signatures
```

---

### "What events does RULE-003 subscribe to?"
```bash
# Check unified spec
cat docs/specifications/unified/rules/RULE-003-daily-realized-loss.md | grep -A 10 "SDK Integration"
# → Shows: TRADE_EXECUTED, POSITION_UPDATED
```

---

### "What's the database schema for violations?"
```bash
# Check contracts
cat CONTRACTS_REFERENCE.md | grep -A 15 "violations table"
# → Shows complete SQL schema
```

---

## 📊 Understanding Project Status

### Current Progress: 30%

**What's Done** (26 features):
- ✅ Database Manager (MOD-001)
- ✅ PnL Tracker
- ✅ 3 risk rules (RULE-001, 002, 012)
- ✅ SDK integration (partial)
- ✅ 8-checkpoint logging
- ✅ Interactive test runner

**What's Missing** (62 features):
- ❌ 3 state managers (MOD-002, 003, 004) ← **CRITICAL BLOCKER**
- ❌ 10 risk rules
- ❌ CLI system (0%)
- ❌ Windows Service (0%)
- ❌ Quote data integration
- ❌ Configuration system (partial)

---

## 🎯 Current Priority: Phase 1 (State Managers)

**Why**: Blocks 8 risk rules (62% of missing rules)

**Order**:
1. MOD-003 (Timer Manager) - No blockers, start now
2. MOD-002 (Lockout Manager) - Depends on MOD-003
3. MOD-004 (Reset Scheduler) - Depends on MOD-003

**After Phase 1**: Can implement RULE-003, 006, 007, 009, 010, 011, 013

---

## 🚀 Quick Start for New Agents

```bash
# 1. Read this file (you're doing it!)
cat AGENT_GUIDELINES.md

# 2. Read roadmap to see what's next
cat IMPLEMENTATION_ROADMAP.md

# 3. Read contracts to understand interfaces
cat CONTRACTS_REFERENCE.md

# 4. Pick first unchecked item in roadmap
# Example: MOD-003 Timer Manager

# 5. Read the spec
cat docs/specifications/unified/architecture/MODULES_SUMMARY.md
# → Find MOD-003 section

# 6. Read the contract
cat CONTRACTS_REFERENCE.md
# → Find TimerManager API

# 7. Write tests
touch tests/unit/test_state/test_timer_manager.py

# 8. Implement feature
touch src/risk_manager/state/timer_manager.py

# 9. Run tests
python run_tests.py → [2]

# 10. Update roadmap
# Change [ ] to [x] in IMPLEMENTATION_ROADMAP.md

# 11. Commit
git add -A
git commit -m "Implemented MOD-003: Timer Manager"
git push
```

---

## 📖 Essential Files

**Read These**:
1. `IMPLEMENTATION_ROADMAP.md` - What to build
2. `AGENT_GUIDELINES.md` - How to build (you're here)
3. `CONTRACTS_REFERENCE.md` - APIs and interfaces

**Reference These**:
4. `docs/specifications/unified/` - Detailed specs
5. `docs/analysis/wave2-gap-analysis/` - What's missing (context)
6. `test_reports/latest.txt` - Most recent test results

---

## 🆘 When You're Stuck

### Problem: "I don't know what to build next"
**Solution**: Read `IMPLEMENTATION_ROADMAP.md` → Check "Next Priority" phase

### Problem: "I don't understand the spec"
**Solution**:
1. Read unified spec completely
2. Check examples in spec
3. Read Wave 2 gap analysis for context
4. Check similar implemented features

### Problem: "I don't know the API signature"
**Solution**: Check `CONTRACTS_REFERENCE.md` → Find the interface

### Problem: "Tests are failing"
**Solution**:
1. Read `test_reports/latest.txt`
2. Check tracebacks for errors
3. Verify you're using correct contracts
4. Check for parameter name mismatches

### Problem: "I don't know if I should use SDK or custom code"
**Solution**:
- **SDK-first approach**: Use Project-X-Py SDK where possible
- **Custom logic**: Only when SDK can't provide it
- **Check**: `docs/specifications/unified/sdk-integration.md`

---

## ✅ Definition of Done (Version 2.0 - WITH RUNTIME VALIDATION)

**A feature is NOT complete until**:

1. ✅ Implementation matches unified spec exactly
2. ✅ Follows contracts from `CONTRACTS_REFERENCE.md`
3. ✅ Unit tests written and passing (90%+ coverage)
4. ✅ Integration tests written and passing (if applicable)
5. ✅ E2E tests written and passing (if applicable)
6. ✅ **Smoke test passing (exit code 0)** ← NEW & MANDATORY
7. ✅ **Logging added (feature observable)** ← NEW & MANDATORY
8. ✅ **Feature visible in logs** ← NEW & MANDATORY
9. ✅ `IMPLEMENTATION_ROADMAP.md` updated (checkbox checked)
10. ✅ Git commit with descriptive message
11. ✅ Changes pushed to remote

**Can't skip steps 6-8** - See `docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md`

---

**Good luck! Build amazing features. 🚀**

---

**Last Updated**: 2025-10-25
**Maintained By**: AI agents + developers
