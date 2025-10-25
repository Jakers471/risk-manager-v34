# Quick Reference - Implementation Foundation

**One-page cheat sheet for daily development**

**Last Updated**: 2025-10-25
**Print This**: Keep handy during development

---

## 📋 Daily Workflow (10 Steps)

```
1. Pick feature       → IMPLEMENTATION_ROADMAP.md
2. Read spec          → docs/specifications/unified/[feature].md
3. Check contract     → CONTRACTS_REFERENCE.md
4. Write tests (TDD)  → tests/unit/test_[feature].py
5. Implement          → src/[module]/[feature].py
6. Run tests          → python run_tests.py → [2]
7. Add logging        → See RUNTIME_VALIDATION_INTEGRATION.md
8. Smoke test         → python run_tests.py → [s] → Exit 0 ✅
9. Update roadmap     → [ ] → [x]
10. Commit + push     → git commit + git push
```

**Can't skip Step 8** (smoke test)

---

## 🔍 Quick Lookups

```bash
# Find specification
docs/specifications/unified/[domain]/[feature].md

# Find contract
CONTRACTS_REFERENCE.md → Search feature name

# Check test results
cat test_reports/latest.txt

# Check logs
cat data/logs/risk_manager.log

# Check progress
IMPLEMENTATION_ROADMAP.md → Progress Summary

# Find last checkpoint
grep "Checkpoint" data/logs/risk_manager.log | tail -1
```

---

## 🧪 Test Commands

```bash
# Unit tests (use most often)
python run_tests.py → [2]

# Integration tests
python run_tests.py → [3]

# Smoke test (MANDATORY before complete)
python run_tests.py → [s]

# Gate (tests + smoke combo)
python run_tests.py → [g]

# View logs
python run_tests.py → [l]

# Check results
cat test_reports/latest.txt
```

---

## 🚀 Smoke Test Exit Codes

```
0  = ✅ SUCCESS (runtime works, feature complete)
1  = ❌ EXCEPTION (read logs: cat data/logs/risk_manager.log)
2  = ❌ STALLED (check Checkpoint 6: grep "Checkpoint" data/logs/risk_manager.log)
```

**Debug**:
```bash
# Exit 1: Read logs for exception
cat data/logs/risk_manager.log | tail -50

# Exit 2: Check last checkpoint
grep "Checkpoint" data/logs/risk_manager.log | tail -1

# Run trace mode for async debug
python run_tests.py → [t]
```

---

## 📝 Logging Quick Reference

### Core Features (manager, engine, enforcement)
Use **8-checkpoint system**:
```python
logger.info("🚀 Checkpoint 1: Service Start...")
logger.info("✅ Checkpoint 2: Config Loaded...")
logger.info("✅ Checkpoint 3: SDK Connected...")
logger.info("✅ Checkpoint 4: Rules Initialized...")
logger.info("✅ Checkpoint 5: Event Loop Running...")
logger.info("📨 Checkpoint 6: Event Received...")
logger.info("🔍 Checkpoint 7: Rule Evaluated...")
logger.warning("⚠️ Checkpoint 8: Enforcement...")
```

### State Managers (TimerManager, LockoutManager, etc.)
**Entry/exit + state changes**:
```python
logger.info(f"TimerManager: Creating timer id={id}, duration={dur}s")
logger.info(f"✅ Timer created: id={id}")
logger.error(f"❌ Timer failed: {error}", exc_info=True)
```

### Risk Rules (RULE-001 through RULE-013)
**Checkpoint 7 + 8**:
```python
# Evaluation (Checkpoint 7)
logger.info(
    f"🔍 Checkpoint 7: RULE-003 evaluated - "
    f"pnl=${pnl:.2f}, violated={violated}"
)

# Enforcement (Checkpoint 8)
logger.warning(
    f"⚠️ Checkpoint 8: RULE-003 enforcement - "
    f"closing all positions account={account_id}"
)
```

### SDK Integration
**Connection + subscriptions**:
```python
logger.info("EventBridge: Subscribing to 3 event types...")
logger.info("✅ EventBridge connected")
logger.debug(f"EventBridge: Forwarding {event_type}")
```

**See**: `docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md` for complete guide

---

## ✅ Definition of Done

Feature **NOT complete** until:

```
✅ Unit tests passing (90%+ coverage)
✅ Integration tests passing (if applicable)
✅ Smoke test exit code 0 ← MANDATORY
✅ Logging added (observable)
✅ Feature visible in logs
✅ Roadmap updated [ ] → [x]
✅ Git committed + pushed
```

**Can't skip smoke test**

---

## 🔗 Essential Files

### Foundation (start here)
```
docs/foundation/IMPLEMENTATION_FOUNDATION.md  ← MASTER
docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md  ← Logging + smoke
docs/foundation/TESTING_INTEGRATION.md  ← Testing
docs/foundation/QUICK_REFERENCE.md  ← You are here
```

### Workflow
```
IMPLEMENTATION_ROADMAP.md  ← What to build
AGENT_GUIDELINES.md  ← How to build
CONTRACTS_REFERENCE.md  ← APIs
```

### Specs
```
docs/specifications/unified/  ← Source of truth
  ├─ architecture/  ← Modules
  ├─ rules/  ← 13 risk rules
  └─ configuration/  ← Config schemas
```

### Results
```
test_reports/latest.txt  ← Latest test results
data/logs/risk_manager.log  ← Runtime logs
```

---

## 🏃 Common Tasks

### Start New Feature

```bash
# 1. Pick from roadmap
cat IMPLEMENTATION_ROADMAP.md | grep "Next Priority"

# 2. Read spec
cat docs/specifications/unified/[domain]/[feature].md

# 3. Check contract
cat CONTRACTS_REFERENCE.md | grep -A 20 "[FeatureName]"

# 4. Write tests
touch tests/unit/test_[module]/test_[feature].py

# 5. Run tests (RED)
python run_tests.py → [2]
# Should fail ❌

# 6. Implement
touch src/risk_manager/[module]/[feature].py

# 7. Run tests (GREEN)
python run_tests.py → [2]
# Should pass ✅

# 8. Add logging (see section above)

# 9. Smoke test (PROVE IT WORKS)
python run_tests.py → [s]
# Must see exit code 0 ✅

# 10. Update roadmap
# Edit IMPLEMENTATION_ROADMAP.md → [ ] to [x]

# 11. Commit
git add .
git commit -m "Implement [Feature]

- Unit tests: X passed
- Smoke test: Exit code 0
- Logging: Observable

🤖 Generated with Claude Code"
git push
```

---

### Debug Smoke Test Failure

```bash
# Check exit code
# 0 = Success → You're done! ✅
# 1 = Exception → See below
# 2 = Stalled → See below

# Exit Code 1 (Exception):
cat data/logs/risk_manager.log | tail -50
# Look for stack trace
# Fix exception
# Re-run: python run_tests.py → [s]

# Exit Code 2 (Stalled - MOST COMMON):
grep "Checkpoint" data/logs/risk_manager.log | tail -1
# Last checkpoint shows where it stalled

# If stuck at Checkpoint 5 (No events):
# → Check SDK subscriptions in EventBridge
# → Check event forwarding to engine
# → Run trace: python run_tests.py → [t]

# If stuck at earlier checkpoint:
# Checkpoint 1-2: Config issue
# Checkpoint 3: SDK connection issue
# Checkpoint 4: Rule initialization issue

# See: docs/foundation/RUNTIME_VALIDATION_INTEGRATION.md
```

---

### Check Feature Status

```bash
# Check if implemented
cat IMPLEMENTATION_ROADMAP.md | grep "[x]"

# Check if tests pass
cat test_reports/latest.txt

# Check if observable
grep "[FEATURE]" data/logs/risk_manager.log

# Check coverage
python run_tests.py → [6]
```

---

## ⚡ Speed Tips

### During Development
```bash
# Run only unit tests (fast)
python run_tests.py → [2]

# Run specific test file
python run_tests.py → [8]
# Enter: tests/unit/test_[feature].py

# Run last failed only
python run_tests.py → [0]
```

### Before Committing
```bash
# Full validation
python run_tests.py → [g]
# Runs: unit + integration + smoke

# Check coverage
python run_tests.py → [6]
# Must see: 90%+
```

---

## 📊 Progress Tracking

```bash
# Overall progress
cat IMPLEMENTATION_ROADMAP.md | grep "Overall Progress"

# Phase progress
cat IMPLEMENTATION_ROADMAP.md | grep "Phase.*Progress"

# Feature status
cat IMPLEMENTATION_ROADMAP.md | grep "\[x\]" | wc -l
# vs
cat IMPLEMENTATION_ROADMAP.md | grep "\[ \]" | wc -l
```

---

## 🚨 Critical Reminders

### DO's ✅
- ✅ Read foundation docs first
- ✅ Write tests before code (TDD)
- ✅ Add logging for every feature
- ✅ Run smoke test before complete
- ✅ Check `test_reports/latest.txt`
- ✅ Verify feature in logs
- ✅ Update roadmap after smoke passes

### DON'Ts ❌
- ❌ Skip smoke test (projects #1-33 failed)
- ❌ Mark complete without exit code 0
- ❌ Implement without reading specs
- ❌ Ignore contracts (use exact signatures)
- ❌ Skip logging (must be observable)
- ❌ Assume tests = runtime works

---

## 🎯 Success Checklist

**Before marking feature complete**:

```
- [ ] Read foundation docs
- [ ] Spec read completely
- [ ] Contract checked
- [ ] Tests written (TDD)
- [ ] Tests passing (90%+ coverage)
- [ ] Logging added
- [ ] Smoke test run
- [ ] Smoke test exit code 0 ← MANDATORY
- [ ] Feature visible in logs
- [ ] Roadmap updated [ ] → [x]
- [ ] Git committed
- [ ] Git pushed
```

**If any unchecked → NOT complete**

---

## 🔥 Emergency Commands

```bash
# System not responding
python run_tests.py → [t]  # Trace mode

# Logs not showing events
grep "Checkpoint 6" data/logs/risk_manager.log

# Can't find spec
find docs/specifications/unified -name "*[keyword]*"

# Don't know what to build next
cat IMPLEMENTATION_ROADMAP.md | grep "Next Priority"

# Tests failing but don't know why
cat test_reports/latest.txt | grep "FAILED"

# Need quick help
cat docs/foundation/QUICK_REFERENCE.md  # This file
```

---

## 📞 When You're Stuck

**Problem**: Don't know what to build
**Solution**: `cat IMPLEMENTATION_ROADMAP.md | grep "Next Priority"`

**Problem**: Don't understand spec
**Solution**: Read unified spec → Check examples → Read gap analysis

**Problem**: Don't know API signature
**Solution**: `cat CONTRACTS_REFERENCE.md | grep -A 20 "[API]"`

**Problem**: Tests failing
**Solution**: `cat test_reports/latest.txt` → Check tracebacks

**Problem**: Smoke test failing
**Solution**: See "Debug Smoke Test Failure" above

**Problem**: Can't see feature working
**Solution**: `grep "[FEATURE]" data/logs/risk_manager.log`

---

## 🎓 Key Concepts

**TDD**: Write tests BEFORE code (RED → GREEN → REFACTOR)

**Smoke Test**: Proves system is alive (not just tests passing)

**8 Checkpoints**: Strategic logging for core features

**Observable**: Can see feature working in logs

**Definition of Done 2.0**: Tests + smoke test + logging

**Exit Code 0**: Required to mark feature complete

**Foundation**: Comprehensive system preventing 33-project failure

---

## 🎁 Copy-Paste Templates

### Unit Test Template
```python
def test_feature_happy_path():
    """Test feature with valid inputs."""
    # Arrange
    manager = FeatureManager(config)

    # Act
    result = manager.do_something(valid_input)

    # Assert
    assert result is not None
    assert result.status == "success"
```

### Logging Template
```python
# For state managers
logger.info(f"Feature: Action started - param={value}")
logger.info(f"✅ Feature: Action complete - result={result}")
logger.error(f"❌ Feature: Action failed - {error}", exc_info=True)

# For rules (Checkpoint 7)
logger.info(
    f"🔍 Checkpoint 7: RULE-00X evaluated - "
    f"value={value}, limit={limit}, violated={violated}"
)

# For enforcement (Checkpoint 8)
logger.warning(
    f"⚠️ Checkpoint 8: RULE-00X enforcement - "
    f"action={action}, account={account_id}"
)
```

### Commit Message Template
```bash
git commit -m "Implement [Feature Name]

- Created [files]
- Added [functionality]
- Unit tests: X passed, Y% coverage
- Integration tests: X passed
- Smoke test: Exit code 0
- Logging: Observable in logs

Refs: docs/specifications/unified/[spec-file].md

🤖 Generated with Claude Code"
```

---

**Print this page and keep it next to your keyboard!**

**Last Updated**: 2025-10-25
**Version**: 1.0 (Foundation-integrated)
**Maintained By**: Wave 4 Researcher 4 (Foundation Consolidation)
