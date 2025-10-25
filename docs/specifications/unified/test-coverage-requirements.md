# Test Coverage Requirements

**Version**: 1.0
**Date**: 2025-10-25
**Status**: Authoritative Specification
**Purpose**: Define coverage targets and requirements for all modules

---

## Executive Summary

This document establishes the authoritative test coverage requirements for Risk Manager V34. It defines module-specific coverage targets, identifies critical gaps, and provides a roadmap to achieve production-ready coverage levels.

**Current State**:
- **Overall Coverage**: 18.27% (1,505 statements, 1,230 missed)
- **Target Coverage**: 90% overall minimum
- **Critical Gap**: Rules and SDK integration have 0% coverage

**Goal**: Achieve 90%+ overall coverage with 95%+ for critical paths.

---

## 1. Coverage Targets by Module

### 1.1 Overall Project Targets

| Metric | Current | Minimum Target | Ideal Target | Status |
|--------|---------|----------------|--------------|--------|
| **Overall Coverage** | 18.27% | 80% | 90% | ❌ Critical Gap |
| **Critical Paths** | Variable | 90% | 95% | ⚠️ Partial |
| **New Features** | N/A | 100% | 100% | 📋 Policy |

### 1.2 Module-Specific Targets

#### Core Modules

| Module | Statements | Current Coverage | Min Target | Ideal Target | Priority | Status |
|--------|------------|------------------|------------|--------------|----------|--------|
| `core/events.py` | 56 | 94.64% | 90% | 95% | High | ✅ Excellent |
| `core/engine.py` | 77 | 54.55% | 85% | 95% | Critical | ⚠️ Needs Work |
| `core/manager.py` | 113 | 22.12% | 85% | 95% | Critical | ❌ Poor |
| `core/config.py` | 39 | 76.92% | 80% | 90% | Medium | ✅ Good |

**Summary**: Events well-tested, engine/manager need significant work.

#### State Management

| Module | Statements | Current Coverage | Min Target | Ideal Target | Priority | Status |
|--------|------------|------------------|------------|--------------|----------|--------|
| `state/database.py` | 72 | 95.83% | 85% | 95% | High | ✅ Excellent |
| `state/pnl_tracker.py` | 56 | 78.57% | 80% | 95% | High | ✅ Good |

**Summary**: State layer has excellent coverage, maintain this standard.

#### Risk Rules (CRITICAL GAP)

| Module | Statements | Current Coverage | Min Target | Ideal Target | Priority | Status |
|--------|------------|------------------|------------|--------------|----------|--------|
| `rules/base.py` | 14 | 0.00% | 90% | 95% | Critical | ❌ Untested |
| `rules/daily_loss.py` | 17 | 0.00% | 90% | 95% | Critical | ❌ Untested |
| `rules/max_position.py` | 24 | 0.00% | 90% | 95% | Critical | ❌ Untested |
| `rules/max_contracts_per_instrument.py` | 81 | 0.00% | 90% | 95% | Critical | ❌ Untested |

**Summary**: **BLOCKER FOR PRODUCTION** - Rules are core business logic and have 0% coverage!

**Required Tests**:
- 5-10 unit tests per rule
- Parametrized tests for edge cases
- Error handling tests
- Configuration validation tests

**Estimated Effort**: 3 days (4 rule files × 5-10 tests each)

#### SDK Integration (CRITICAL GAP)

| Module | Statements | Current Coverage | Min Target | Ideal Target | Priority | Status |
|--------|------------|------------------|------------|--------------|----------|--------|
| `sdk/enforcement.py` | 153 | 0.00% | 70% | 85% | Critical | ❌ Untested |
| `sdk/event_bridge.py` | 104 | 0.00% | 70% | 85% | Critical | ❌ Untested |
| `sdk/suite_manager.py` | 89 | 0.00% | 70% | 85% | Critical | ❌ Untested |

**Summary**: **BLOCKER FOR PRODUCTION** - SDK integration untested, enforcement may fail silently!

**Required Tests**:
- 8-12 unit tests per SDK module
- Integration tests for SDK lifecycle
- Mock SDK responses for unit tests
- Real SDK connection for integration tests

**Estimated Effort**: 4 days (3 SDK files × 8-12 tests each)

#### Trading Integration

| Module | Statements | Current Coverage | Min Target | Ideal Target | Priority | Status |
|--------|------------|------------------|------------|--------------|----------|--------|
| `integrations/trading.py` | 80 | 0.00% | 70% | 85% | High | ❌ Untested |

**Summary**: Wrapper around SDK, needs integration tests.

**Required Tests**:
- 10-15 integration tests
- SDK method call verification
- Error handling and retry logic
- Connection lifecycle tests

**Estimated Effort**: 2 days

#### AI Integration

| Module | Statements | Current Coverage | Min Target | Ideal Target | Priority | Status |
|--------|------------|------------------|------------|--------------|----------|--------|
| `ai/integration.py` | 48 | 0.00% | 60% | 75% | Low | ❌ Untested |

**Summary**: AI features are optional, lower priority but still need testing.

**Required Tests**:
- 5-8 unit tests
- Pattern detection tests
- AI response handling tests

**Estimated Effort**: 2 days

---

## 2. Coverage Analysis by Component Type

### 2.1 Critical Paths (95% Target)

**Definition**: Code that directly impacts trading safety and compliance.

**Components**:
- Risk rule evaluation logic (`rules/`)
- Enforcement actions (`sdk/enforcement.py`)
- P&L tracking (`state/pnl_tracker.py`)
- Account lockout logic (when implemented)
- Event dispatch (`core/events.py`)

**Current Status**:
- ✅ `state/pnl_tracker.py` - 78.57% (needs improvement to 95%)
- ✅ `core/events.py` - 94.64% (excellent!)
- ❌ `rules/` - 0% (critical blocker!)
- ❌ `sdk/enforcement.py` - 0% (critical blocker!)

**Gap**: Rules and enforcement have no coverage!

### 2.2 Core Infrastructure (90% Target)

**Definition**: System components that must be reliable but aren't directly safety-critical.

**Components**:
- Event engine (`core/engine.py`)
- Risk manager (`core/manager.py`)
- Configuration loading (`core/config.py`)
- SDK connection management (`sdk/suite_manager.py`)
- Event bridging (`sdk/event_bridge.py`)

**Current Status**:
- ✅ `core/config.py` - 76.92% (good, needs slight improvement)
- ⚠️ `core/engine.py` - 54.55% (needs work)
- ❌ `core/manager.py` - 22.12% (poor)
- ❌ `sdk/suite_manager.py` - 0% (untested)
- ❌ `sdk/event_bridge.py` - 0% (untested)

**Gap**: Manager and SDK integration poorly covered.

### 2.3 Supporting Features (70% Target)

**Definition**: Important features but not directly safety-critical.

**Components**:
- Trading integration wrapper (`integrations/trading.py`)
- AI pattern detection (`ai/integration.py`)
- CLI interfaces (when implemented)
- Monitoring and metrics (when implemented)

**Current Status**:
- ❌ `integrations/trading.py` - 0%
- ❌ `ai/integration.py` - 0%

**Gap**: All supporting features untested.

---

## 3. Test Type Requirements

### 3.1 Unit Test Coverage (60% of Suite)

**Target**: 60+ unit tests covering isolated logic

**Current**: 23 unit tests
**Gap**: Need 37+ more unit tests

**Priority Areas for Unit Tests**:

#### High Priority (Missing)
1. **Rules** (0 tests currently)
   - `test_rules/test_base.py` - 5 tests
   - `test_rules/test_daily_loss.py` - 10 tests
   - `test_rules/test_max_position.py` - 8 tests
   - `test_rules/test_max_contracts.py` - 12 tests
   - **Total needed**: 35 tests

2. **SDK Layer** (0 tests currently)
   - `test_sdk/test_enforcement.py` - 15 tests
   - `test_sdk/test_event_bridge.py` - 12 tests
   - `test_sdk/test_suite_manager.py` - 10 tests
   - **Total needed**: 37 tests

3. **Core Engine** (partial coverage)
   - `test_core/test_engine.py` - Add 10 more tests
   - `test_core/test_manager.py` - Add 15 more tests
   - **Total needed**: 25 tests

**Total Unit Tests Needed**: ~97 additional tests
**Current Unit Tests**: 23
**Target**: 120+ unit tests

### 3.2 Integration Test Coverage (30% of Suite)

**Target**: 20-30 integration tests covering component interactions

**Current**: 0 integration tests
**Gap**: Need 20-30 integration tests

**Required Integration Test Scenarios**:

1. **SDK Connection Lifecycle** (2 days)
   - Connect, disconnect, reconnect
   - Authentication flow
   - Error recovery
   - **Tests needed**: 5-7

2. **Real Event Pipeline** (3 days)
   - SDK event → EventBridge → EventBus → Rules → Enforcement
   - Multiple rules processing same event
   - Event priority handling
   - **Tests needed**: 8-10

3. **Multi-Rule Interaction** (2 days)
   - Multiple rules active
   - Conflict resolution
   - Enforcement priority
   - **Tests needed**: 5-7

4. **State Persistence** (2 days)
   - P&L persists across restart
   - Rule state recovery
   - Database migrations
   - **Tests needed**: 5-6

5. **Error Recovery** (3 days)
   - SDK call failures and retries
   - Network timeout handling
   - Invalid event handling
   - **Tests needed**: 6-8

**Total Integration Tests Needed**: 29-38 tests

### 3.3 E2E Test Coverage (10% of Suite)

**Target**: 5-10 E2E tests covering complete workflows

**Current**: 0 E2E tests
**Gap**: Need 5-10 E2E tests

**Required E2E Test Scenarios**:

1. **Full Violation Flow** (4 days)
   - Trade → Rule breach → Enforcement → Lockout
   - **Tests needed**: 2-3

2. **Daily Reset Flow** (3 days)
   - Midnight P&L reset
   - Rule state reset
   - **Tests needed**: 1-2

3. **Account Lockout Flow** (3 days)
   - Critical violation → Lock → Admin unlock
   - **Tests needed**: 2-3

4. **Multi-Symbol Trading** (3 days)
   - Account-wide limits across symbols
   - **Tests needed**: 2-3

5. **Service Restart** (3 days)
   - State recovery after restart
   - **Tests needed**: 1-2

**Total E2E Tests Needed**: 8-13 tests

### 3.4 Runtime Validation (Cross-cutting)

**Target**: Comprehensive runtime reliability pack

**Current**: 70 runtime tests (5 failing)
**Gap**: Fix 5 failing tests

**Status**: Runtime pack is well-developed, just needs bug fixes.

---

## 4. Coverage Gap Analysis

### 4.1 Critical Gaps (Blocking Production)

| Gap | Impact | Coverage Deficit | Tests Needed | Effort | Priority |
|-----|--------|------------------|--------------|--------|----------|
| **Rules untested** | Cannot validate rule logic | 100% | 35 unit tests | 3 days | CRITICAL |
| **SDK untested** | Enforcement may fail silently | 100% | 37 unit tests | 4 days | CRITICAL |
| **No integration tests** | Components may not work together | 100% | 29-38 tests | 2 weeks | CRITICAL |
| **No E2E tests** | Workflows unvalidated | 100% | 8-13 tests | 2 weeks | HIGH |

**Total Critical Gap Effort**: 5-6 weeks

### 4.2 Important Gaps (Reducing Risk)

| Gap | Impact | Coverage Deficit | Tests Needed | Effort | Priority |
|-----|--------|------------------|--------------|--------|----------|
| **Manager coverage low** | Startup/shutdown issues | 78% | 15 unit tests | 2 days | HIGH |
| **Engine coverage low** | Event handling issues | 45% | 10 unit tests | 1 day | HIGH |
| **Trading integration** | SDK wrapper issues | 100% | 10 tests | 2 days | MEDIUM |

**Total Important Gap Effort**: 1 week

### 4.3 Nice-to-Have Gaps (Polish)

| Gap | Impact | Coverage Deficit | Tests Needed | Effort | Priority |
|-----|--------|------------------|--------------|--------|----------|
| **AI integration** | AI features unreliable | 100% | 5-8 tests | 2 days | LOW |
| **CLI coverage** | CLI bugs | N/A | 10 tests | 2 days | LOW |

**Total Nice-to-Have Effort**: 1 week

---

## 5. Coverage Roadmap

### 5.1 Phase 1: Critical Unit Tests (1 week)

**Goal**: Test rules and SDK layer

**Week 1**:
- Day 1-3: Add 35 unit tests for rules
- Day 4-5: Add 37 unit tests for SDK layer

**Deliverables**:
- `tests/unit/test_rules/` - Complete coverage
- `tests/unit/test_sdk/` - Complete coverage
- Coverage increases from 18% to ~40%

**Success Criteria**: All rules and SDK modules have 90%+ coverage

### 5.2 Phase 2: Integration Tests (2 weeks)

**Goal**: Validate component interactions

**Week 2-3**:
- Day 1-2: SDK connection lifecycle tests
- Day 3-5: Real event pipeline tests
- Day 6-7: Multi-rule interaction tests
- Day 8-9: State persistence tests
- Day 10: Error recovery tests

**Deliverables**:
- `tests/integration/` - 29-38 tests
- Coverage increases from ~40% to ~60%

**Success Criteria**: All critical integration scenarios validated

### 5.3 Phase 3: E2E Tests (2 weeks)

**Goal**: Validate complete workflows

**Week 4-5**:
- Day 1-2: Full violation flow
- Day 3-5: Multi-symbol trading
- Day 6-7: Daily reset flow
- Day 8-10: Remaining E2E scenarios

**Deliverables**:
- `tests/e2e/` - 8-13 tests
- Coverage increases from ~60% to ~75%

**Success Criteria**: All critical workflows validated

### 5.4 Phase 4: Polish & Infrastructure (1 week)

**Goal**: Fill remaining gaps and add CI/CD

**Week 6**:
- Day 1-2: Add missing unit tests (manager, engine)
- Day 3-4: CI/CD setup (GitHub Actions)
- Day 5: Coverage validation and documentation

**Deliverables**:
- Coverage reaches 90%+
- Automated CI/CD pipeline
- Complete test documentation

**Success Criteria**: 90%+ overall coverage, automated testing

---

## 6. Coverage Enforcement

### 6.1 Pre-Commit Checks

**Required before committing**:
```bash
# Run all tests
pytest

# Check coverage
pytest --cov=src --cov-report=term

# Minimum 90% overall
pytest --cov=src --cov-fail-under=90
```

### 6.2 Pull Request Requirements

**Required before merging PR**:
1. All tests pass (exit code 0)
2. No decrease in overall coverage
3. New features have 100% coverage
4. Critical paths maintain 95%+ coverage
5. Smoke test passes (exit code 0)

### 6.3 CI/CD Integration

**GitHub Actions workflow** (when implemented):

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run tests with coverage
        run: |
          .venv/bin/pytest --cov=src --cov-report=xml --cov-fail-under=90
      - name: Upload coverage
        uses: codecov/codecov-action@v2
      - name: Comment coverage on PR
        # Auto-comment coverage report on PRs
```

**Enforcement Rules**:
- PR blocked if tests fail
- PR blocked if coverage drops below 90%
- PR blocked if new code has <100% coverage
- PR blocked if smoke test fails

---

## 7. Coverage Monitoring

### 7.1 Coverage Reports

**Auto-generated reports**:
- **Terminal**: `pytest --cov=src --cov-report=term`
- **HTML**: `pytest --cov=src --cov-report=html` → `htmlcov/index.html`
- **XML**: `pytest --cov=src --cov-report=xml` → For CI/CD

**Report Locations**:
- Latest HTML: `htmlcov/index.html`
- Latest XML: `coverage.xml`
- Historical: Tracked in git commits

### 7.2 Coverage Dashboards

**View coverage via test runner**:
```bash
python run_tests.py → [6]  # Terminal coverage report
python run_tests.py → [7]  # HTML coverage report (opens in browser)
```

**Coverage metrics tracked**:
- Overall project coverage
- Per-module coverage
- Per-file coverage
- Line coverage
- Branch coverage
- Uncovered lines

### 7.3 Coverage Alerts

**Alert conditions**:
- Overall coverage drops below 90%
- Critical path coverage drops below 95%
- New feature added without tests
- Coverage decrease in PR

**Alert actions**:
- Block PR merge
- Notify development team
- Generate coverage report
- Suggest missing tests

---

## 8. Special Coverage Considerations

### 8.1 Excluded from Coverage

**Files excluded from coverage requirements**:
- `__init__.py` files (boilerplate)
- Test files themselves (`tests/*`)
- Development scripts (`scripts/dev_*`)
- Example files (`examples/*`)
- Generated code (if any)

**Why excluded**: These files are either minimal boilerplate or non-production code.

### 8.2 Hard-to-Test Code

**Some code is inherently difficult to test**:
- Windows Service integration (requires Windows)
- Windows UAC prompts (requires admin rights)
- Real-time market data (external dependency)
- Time-sensitive code (midnight resets)

**Approach**:
- Use integration tests where possible
- Mock time-dependent code
- Use conditional coverage targets
- Document untestable code with `# pragma: no cover`

### 8.3 Legacy Code

**Current state**: All code is new, no legacy code yet.

**Future policy**: When refactoring legacy code:
1. Add tests for existing behavior
2. Refactor with tests passing
3. Add tests for new behavior
4. Achieve 90%+ coverage for refactored modules

---

## 9. Tools and Commands

### 9.1 Coverage Commands

```bash
# Quick coverage check
pytest --cov=src

# Detailed coverage with missing lines
pytest --cov=src --cov-report=term-missing

# HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html  # View in browser

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=90

# Coverage for specific module
pytest --cov=src/risk_manager/rules tests/unit/test_rules/

# Branch coverage (not just line coverage)
pytest --cov=src --cov-branch
```

### 9.2 Interactive Runner Commands

```bash
# Via test runner menu
python run_tests.py

# Coverage options:
[6] Coverage report (terminal)
[7] Coverage + HTML report
[c] Check coverage status
```

### 9.3 Coverage Configuration

**File**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
addopts = """
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=90
"""

[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/examples/*",
    "*/scripts/dev_*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

---

## 10. Success Metrics

### 10.1 Current State vs Target

| Metric | Current | Target | Gap | Status |
|--------|---------|--------|-----|--------|
| Overall Coverage | 18.27% | 90% | 71.73% | ❌ Critical Gap |
| Critical Paths | Variable | 95% | N/A | ⚠️ Partial |
| Rules Coverage | 0% | 95% | 95% | ❌ Blocker |
| SDK Coverage | 0% | 85% | 85% | ❌ Blocker |
| State Coverage | 78-95% | 95% | ~5% | ✅ Near Target |
| Unit Tests | 23 | 120+ | 97+ | ❌ Major Gap |
| Integration Tests | 0 | 29-38 | 29-38 | ❌ Missing |
| E2E Tests | 0 | 8-13 | 8-13 | ❌ Missing |

### 10.2 Timeline to Target

**Optimistic** (full-time focus):
- Phase 1: 1 week (critical unit tests)
- Phase 2: 2 weeks (integration tests)
- Phase 3: 2 weeks (E2E tests)
- Phase 4: 1 week (polish)
- **Total**: 6 weeks

**Realistic** (part-time alongside features):
- Phase 1: 2 weeks
- Phase 2: 3 weeks
- Phase 3: 3 weeks
- Phase 4: 1 week
- **Total**: 9 weeks

### 10.3 Production Readiness Criteria

**Cannot deploy to production until**:
- ✅ Overall coverage ≥ 90%
- ✅ Critical path coverage ≥ 95%
- ✅ All rules have 90%+ coverage
- ✅ SDK integration has 85%+ coverage
- ✅ Integration tests pass
- ✅ E2E tests pass
- ✅ Smoke test passes (exit code 0)
- ✅ No failing tests

**Current Production Readiness**: ❌ Not ready

**Blockers**:
1. Rules untested (0% coverage)
2. SDK untested (0% coverage)
3. No integration tests
4. No E2E tests
5. Overall coverage only 18%

---

## 11. Related Documentation

**Testing Strategy**:
- `testing-strategy.md` - Complete testing approach
- `runtime-validation-strategy.md` - 8-checkpoint system

**Testing Guides**:
- `docs/testing/TESTING_GUIDE.md` - How to write tests
- `docs/testing/RUNTIME_DEBUGGING.md` - Runtime validation
- `docs/testing/WORKING_WITH_AI.md` - AI-assisted testing

**API Contracts**:
- `SDK_API_REFERENCE.md` - Actual API signatures
- `SDK_ENFORCEMENT_FLOW.md` - Enforcement wiring

---

**Last Updated**: 2025-10-25
**Version**: 1.0
**Status**: Authoritative Specification
**Next Review**: After Phase 1 completion
