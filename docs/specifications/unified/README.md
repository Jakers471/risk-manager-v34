# Unified Testing Specifications

**Wave 3 - Researcher 6 Deliverable**
**Date**: 2025-10-25
**Status**: Complete

---

## Overview

This directory contains the **authoritative unified testing specifications** for Risk Manager V34, consolidating best practices from:

1. **Wave 1 Feature Inventory** - Testing infrastructure analysis
2. **Wave 2 Gap Analysis** - Testing gaps and roadmap
3. **Original Documentation** - Testing guides and runtime debugging

**Purpose**: Create single source of truth for all testing approaches, eliminating redundancy and conflicts.

---

## Unified Specifications

### 1. Testing Strategy (`testing-strategy.md`)

**Consolidates**:
- 4-tier testing pyramid (unit, integration, e2e, runtime)
- Test-driven development (TDD) approach
- Test organization and naming conventions
- Fixture and mocking patterns
- Interactive test runner system
- Best practices and workflows

**Key Topics**:
- Unit tests (60% of suite)
- Integration tests (30% of suite)
- E2E tests (10% of suite)
- Runtime validation pack (cross-cutting)
- 8-checkpoint logging system
- Smoke/soak/trace testing
- Daily development workflow
- AI-assisted testing workflow

**Status**: ✅ Complete - 14 sections, comprehensive

---

### 2. Test Coverage Requirements (`test-coverage-requirements.md`)

**Consolidates**:
- Module-specific coverage targets
- Current coverage analysis
- Coverage gaps and priorities
- Test type requirements
- Coverage roadmap

**Key Topics**:
- Overall target: 90% minimum
- Critical paths: 95% target
- Module-specific targets (rules 95%, SDK 85%, etc.)
- Coverage gap analysis (rules 0%, SDK 0%)
- 6-week roadmap to 90%+ coverage
- Coverage enforcement (CI/CD)

**Status**: ✅ Complete - 11 sections, detailed roadmap

---

### 3. Runtime Validation Strategy (`runtime-validation-strategy.md`)

**Consolidates**:
- 8-checkpoint validation system
- Runtime reliability pack capabilities
- Smoke/soak/trace/log/env testing
- Exit codes and meanings
- Troubleshooting flowcharts

**Key Topics**:
- Why runtime testing matters
- 8-checkpoint architecture (🚀 ✅ ✅ ✅ ✅ 📨 🔍 ⚠️)
- Smoke test (8s boot validation)
- Soak test (30-60s stability)
- Trace mode (async debugging)
- Exit codes (0=success, 1=exception, 2=stalled)
- Complete troubleshooting flowchart

**Status**: ✅ Complete - 9 sections, comprehensive

---

## Key Findings

### No Major Conflicts Found

The testing documentation had **excellent consistency** across all sources:

✅ **Testing Pyramid** - Universal agreement on 4-tier model
✅ **TDD Approach** - Red-Green-Refactor consistently documented
✅ **Runtime Validation** - 8-checkpoint system well-defined
✅ **Test Runner** - Interactive menu consistently described
✅ **Coverage Targets** - 90% overall, 95% critical paths agreed

**Consolidation Work**: Primarily **organizational** rather than conflict resolution:
- Combined scattered information into single sources
- Eliminated redundancy
- Added cross-references
- Structured for easy navigation

---

## Testing Strategy Summary

### Current State

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **Overall Coverage** | 18.27% | 90% | ❌ Critical Gap |
| **Unit Tests** | 23 | 120+ | ❌ Major Gap |
| **Integration Tests** | 0 | 29-38 | ❌ Missing |
| **E2E Tests** | 0 | 8-13 | ❌ Missing |
| **Runtime Tests** | 70 (5 failing) | 70 (0 failing) | ⚠️ Near Ready |
| **Test Infrastructure** | Excellent | Excellent | ✅ Complete |

### Critical Blockers

**Cannot deploy to production**:
1. ❌ Rules untested (0% coverage)
2. ❌ SDK integration untested (0% coverage)
3. ❌ No integration tests (component interactions unvalidated)
4. ❌ No E2E tests (workflows unvalidated)
5. ⚠️ 5 failing runtime tests (fixable in <1 day)

### Timeline to Production Ready

**Optimistic** (full-time focus):
- Phase 1: 1 week - Critical unit tests (rules + SDK)
- Phase 2: 2 weeks - Integration tests
- Phase 3: 2 weeks - E2E tests
- Phase 4: 1 week - Polish & CI/CD
- **Total**: 6 weeks

**Realistic** (part-time):
- **Total**: 9 weeks

---

## Testing Workflow

### Complete Testing Process

```
Step 1: Write Tests (TDD)
  └─> Write test FIRST (RED)
  └─> Implement feature (GREEN)
  └─> Refactor (REFACTOR)

Step 2: Run pytest
  └─> python run_tests.py → [1] (all tests)
  └─> Result: ✅ All tests pass (logic correct)

Step 3: Run Smoke Test
  └─> python run_tests.py → [s]
  └─> Exit code 0 = SUCCESS (system live)
  └─> Exit code 1 = EXCEPTION (fix and retry)
  └─> Exit code 2 = STALLED (check checkpoints)

Step 4: (Optional) Run Soak Test
  └─> python run_tests.py → [r]
  └─> Check memory/performance

Step 5: Deploy
  └─> Only if pytest passed AND smoke test = 0
```

### Daily Development Workflow

**Morning start**:
```bash
python run_tests.py → [s]  # Smoke test
python run_tests.py → [2]  # Unit tests
```

**During development**:
```bash
# TDD cycle
python run_tests.py → [9]  # Last failed
# Repeat until GREEN
```

**Before commit**:
```bash
python run_tests.py → [1]  # All tests
python run_tests.py → [6]  # Coverage
python run_tests.py → [s]  # Smoke test
```

**Before deployment**:
```bash
python run_tests.py → [g]  # Gate test
# Exit code MUST be 0
```

---

## The 8-Checkpoint System

**Strategic logging for runtime debugging**:

```
🚀 Checkpoint 1: Service Start (manager.py)
✅ Checkpoint 2: Config Loaded (manager.py)
✅ Checkpoint 3: SDK Connected (manager.py)
✅ Checkpoint 4: Rules Initialized (manager.py)
✅ Checkpoint 5: Event Loop Running (engine.py)
📨 Checkpoint 6: Event Received (engine.py) ← LIVENESS PROOF
🔍 Checkpoint 7: Rule Evaluated (engine.py)
⚠️ Checkpoint 8: Enforcement Triggered (enforcement.py)
```

**Usage**:
```bash
# Run smoke test
python run_tests.py → [s]

# Check exit code
# 0 = All checkpoints passed
# 1 = Exception (check logs)
# 2 = Stalled (check which checkpoint failed)

# View logs
python run_tests.py → [l]

# Find last checkpoint
grep -E "🚀|✅|📨|🔍|⚠️" data/logs/risk_manager.log
```

**Most Common Issue**: System boots (checkpoints 1-5) but no events received (checkpoint 6) → Check SDK event subscriptions!

---

## Coverage Targets by Module

### Critical Paths (95% Target)

**Well-Covered** ✅:
- `core/events.py` - 94.64%
- `state/database.py` - 95.83%
- `state/pnl_tracker.py` - 78.57%

**Untested** ❌ **BLOCKERS**:
- `rules/` - 0% coverage (35 tests needed)
- `sdk/enforcement.py` - 0% coverage (15 tests needed)
- `sdk/event_bridge.py` - 0% coverage (12 tests needed)
- `sdk/suite_manager.py` - 0% coverage (10 tests needed)

### Core Infrastructure (90% Target)

**Needs Work** ⚠️:
- `core/engine.py` - 54.55% (10 more tests)
- `core/manager.py` - 22.12% (15 more tests)
- `core/config.py` - 76.92% (near target)

### Supporting Features (70% Target)

**Untested** ❌:
- `integrations/trading.py` - 0% (10 tests needed)
- `ai/integration.py` - 0% (5-8 tests needed)

---

## Test Infrastructure

### Current Strengths

✅ **Interactive Test Runner** - 20+ menu options
✅ **Auto-Save Reports** - `test_reports/latest.txt` for AI review
✅ **8-Checkpoint Logging** - Strategic runtime debugging
✅ **Runtime Reliability Pack** - Smoke/soak/trace/logs/env
✅ **Performance Optimized** - Direct venv usage (not `uv run`)
✅ **AI-Friendly** - Clear exit codes, formatted reports

### Missing Infrastructure

❌ **CI/CD Integration** - No GitHub Actions
❌ **Performance Testing** - No load/benchmark tests
❌ **Regression Suite** - No automated PR checks
❌ **Mutation Testing** - No test quality validation

**Estimated Effort**: 1 week to add all missing infrastructure

---

## Best Practices

### DO

✅ Write tests BEFORE implementation (TDD)
✅ Use `spec=` on all mocks (catch typos)
✅ Test edge cases and errors
✅ Keep tests fast (unit <1s)
✅ Mock at service boundaries only
✅ Run smoke test before deployment
✅ Check all 8 checkpoints

### DON'T

❌ Write code before tests
❌ Use mocks without `spec=`
❌ Only test happy paths
❌ Over-mock internal components
❌ Deploy without smoke test passing
❌ Ignore runtime validation

---

## Using These Specifications

### For Developers

**Start here**:
1. Read `testing-strategy.md` (comprehensive testing approach)
2. Check `test-coverage-requirements.md` (what needs tests)
3. Reference `runtime-validation-strategy.md` (deployment validation)

**Writing tests**:
- Follow TDD: Write test first (RED → GREEN → REFACTOR)
- Use AAA pattern for unit tests
- Use Given-When-Then for business logic
- Parametrize for multiple scenarios

**Running tests**:
```bash
python run_tests.py  # Interactive menu
```

### For AI Agents

**Session start**:
1. Read `testing-strategy.md` - Understand overall approach
2. Check `test_reports/latest.txt` - Current test status
3. Check `test-coverage-requirements.md` - What needs tests

**When fixing tests**:
1. User runs tests → Report auto-saves
2. AI reads `test_reports/latest.txt`
3. AI fixes failures
4. Repeat until green

**When runtime fails**:
1. AI says: "Run smoke test: python run_tests.py → [s]"
2. Check exit code: 0=success, 1=exception, 2=stalled
3. Read logs to find which checkpoint failed
4. Fix based on checkpoint

### For Project Managers

**Production Readiness Checklist**:
- [ ] Overall coverage ≥ 90%
- [ ] Critical path coverage ≥ 95%
- [ ] All rules tested (currently 0%)
- [ ] SDK integration tested (currently 0%)
- [ ] Integration tests exist (currently 0)
- [ ] E2E tests exist (currently 0)
- [ ] Smoke test passes (exit code 0)
- [ ] No failing tests

**Current Status**: ❌ Not production ready

**Timeline**: 6-9 weeks to production ready

---

## Related Documentation

### Original Documentation

**Archived (reference only)**:
- `docs/archive/2025-10-25-pre-wave1/03-testing-docs/testing/TESTING_GUIDE.md`
- `docs/archive/2025-10-25-pre-wave1/03-testing-docs/testing/RUNTIME_DEBUGGING.md`
- `docs/archive/2025-10-23-testing-docs/*.md` (5 files)

**Note**: These are now **deprecated** - use unified specs instead!

### Wave Analysis Documents

**Input documents (research)**:
- `docs/analysis/wave1-feature-inventory/04-TESTING-INVENTORY.md`
- `docs/analysis/wave2-gap-analysis/06-TESTING-GAPS.md`

**Note**: These were inputs to this consolidation effort.

### API Contracts

**Still relevant** (not testing-specific):
- `SDK_API_REFERENCE.md` - Actual API signatures
- `SDK_ENFORCEMENT_FLOW.md` - Enforcement wiring
- `TEST_RUNNER_FINAL_FIXES.md` - Runner behavior

---

## Document History

**Version 1.0** (2025-10-25):
- Initial unified specifications created
- Consolidated 3 testing guides + 2 analysis reports
- No major conflicts found
- Primarily organizational work
- 3 comprehensive specification documents created

**Maintainer**: Development Team
**Next Review**: After Phase 1 completion (critical unit tests)

---

## Quick Reference Card

### Essential Commands

```bash
# Run all tests
python run_tests.py → [1]

# Run unit tests
python run_tests.py → [2]

# Run smoke test (deployment validation)
python run_tests.py → [s]

# Run gate test (complete validation)
python run_tests.py → [g]

# View latest test results
cat test_reports/latest.txt

# View logs
python run_tests.py → [l]

# Check coverage
python run_tests.py → [6]
```

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | SUCCESS | ✅ Deploy |
| 1 | EXCEPTION | ❌ Check logs |
| 2 | STALLED | ⚠️ Check checkpoints |

### 8 Checkpoints

```
🚀 Service Start
✅ Config Loaded
✅ SDK Connected
✅ Rules Initialized
✅ Event Loop Running
📨 Event Received ← Most common failure point
🔍 Rule Evaluated
⚠️ Enforcement Triggered
```

---

**Unified specifications complete!**

**Researcher 6: Mission accomplished.**
