# AI-Assisted Testing & Deployment Workflow

**How project-x-py SDK Uses AI Agents for Development → Testing → Deployment**

**Document Purpose**: Understand how the SDK orchestrates 15 AI agents to build, test, and deploy code systematically - and how to integrate your `run_tests.py` menu into this workflow.

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [SDK's AI Agent Ecosystem](#sdks-ai-agent-ecosystem)
3. [Test Reporting Systems](#test-reporting-systems)
4. [Complete Development Workflow](#complete-development-workflow)
5. [Integrating Your Test Menu](#integrating-your-test-menu)
6. [GitHub Actions Integration](#github-actions-integration)
7. [Agent Coordination Patterns](#agent-coordination-patterns)
8. [Quality Gates](#quality-gates)
9. [Deployment Pipeline](#deployment-pipeline)
10. [For AI Reading This](#for-ai-reading-this-document)

---

## Executive Summary

### The Problem You Had

> "in past project ive made for this risk manager i get the 'green tests but when i go to start or run the code for real, nothing felt like it was working, like enforcment, logging, detecting incoming signals or repsonses from api so commincation etc. nothing seemed to work, even though tests were green..."

**Root Cause**: Tests used mocks, no AI-assisted validation, no systematic integration testing.

### The SDK's Solution

The SDK uses **15 specialized AI agents** to orchestrate:

```
test-orchestrator: Plan what to test
   ↓
python-developer: Write tests FIRST (TDD)
   ↓
integration-tester: Test with REAL SDK (no mocks)
   ↓
code-standards-enforcer: Quality gates
   ↓
code-reviewer: Review everything
   ↓
deployment-coordinator: Orchestrate release
   ↓
release-manager: Deploy to PyPI
```

**Result**: "Green tests" means "production ready" because every layer was validated.

### Your Current Assets

✅ **`run_tests.py`** - Interactive menu with automatic reporting
✅ **TDD_WORKFLOW_GUIDE.md** - How to write tests
✅ **RUNTIME_INTEGRATION_TESTING.md** - How to prevent runtime failures
⏳ **This Document** - How to orchestrate AI agents

---

## SDK's AI Agent Ecosystem

### Directory Structure

```
project-x-py/
├── .claude/
│   ├── agents/                    # 15 specialized agents
│   │   ├── test-orchestrator.md
│   │   ├── integration-tester.md
│   │   ├── python-developer.md
│   │   ├── code-standards-enforcer.md
│   │   ├── code-reviewer.md
│   │   ├── deployment-coordinator.md
│   │   ├── release-manager.md
│   │   ├── security-auditor.md
│   │   ├── performance-optimizer.md
│   │   ├── code-refactor.md
│   │   ├── code-documenter.md
│   │   ├── code-debugger.md
│   │   ├── data-analyst.md
│   │   ├── architecture-planner.md
│   │   └── README.md
│   └── commands/                  # Workflow automation
│       ├── tdd-development.md
│       └── dev-workflow.md
│
├── .github/workflows/             # CI/CD automation
│   ├── ci.yml                     # Main pipeline
│   ├── claude-code-review.yml     # AI code review
│   └── release.yml                # Deployment
│
└── tests/
    ├── unit/
    ├── integration/
    └── benchmarks/
```

### Agent Categories

**1. Coordinators** (Don't write code, orchestrate others)
- `test-orchestrator` - Plans test strategies
- `deployment-coordinator` - Orchestrates deployments
- `architecture-planner` - Designs system architecture

**2. Implementation** (Write code and tests)
- `python-developer` - Implements features
- `integration-tester` - Creates integration tests
- `code-refactor` - Refactors code

**3. Analysis** (Read-only, provide feedback)
- `code-reviewer` - Reviews code quality
- `code-standards-enforcer` - Enforces quality gates
- `security-auditor` - Scans for vulnerabilities
- `performance-optimizer` - Analyzes performance
- `data-analyst` - Analyzes metrics

**4. Management**
- `release-manager` - Handles releases
- `code-documenter` - Updates documentation
- `code-debugger` - Debugs issues

### Test-Orchestrator: The Testing Coordinator

**Role**: Doesn't write tests, **coordinates** testing strategy

**From**: `.claude/agents/test-orchestrator.md`

**Responsibilities**:
```markdown
1. Define test requirements based on feature
2. Plan test pyramid distribution:
   - 60% unit tests
   - 30% integration tests
   - 10% E2E tests
3. Coordinate with python-developer to write tests
4. Coordinate with integration-tester for E2E tests
5. Review coverage reports
6. Identify testing gaps
```

**Test Pyramid Approach**:
```
         /\
        /E2E\       ← 10% (Critical user journeys)
       /------\
      /  Integ  \    ← 30% (Component interactions)
     /----------\
    /    Unit     \   ← 60% (Isolated logic)
   /--------------\
```

**Coordination Pattern**:
```
test-orchestrator: "We need to test the order placement flow"
   ↓
python-developer: Write unit tests for OrderManager
   ↓
python-developer: Write integration test for order → position flow
   ↓
integration-tester: Create E2E test with market simulation
   ↓
code-reviewer: Review test quality
   ↓
test-orchestrator: Verify coverage meets requirements
```

### Integration-Tester: End-to-End Validation

**Role**: Creates integration tests with **real SDK patterns** (not mocks)

**From**: `.claude/agents/integration-tester.md`

**Market Simulator Pattern**:
```python
class MarketSimulator:
    """Generate realistic market data for testing"""

    def __init__(self, symbol: str, initial_price: Decimal):
        self.symbol = symbol
        self.current_price = initial_price
        self.volatility = 0.02
        self.trend = 0.0

    async def generate_tick_stream(self, rate: int = 100):
        """Generate realistic tick data at specified rate"""
        while True:
            # Simulate price movement
            change = np.random.normal(self.trend, self.volatility)
            self.current_price *= Decimal(str(1 + change))

            # Calculate bid/ask spread
            spread = self.current_price * Decimal("0.0001")
            bid = self.current_price - spread / 2
            ask = self.current_price + spread / 2

            tick = {
                "symbol": self.symbol,
                "bid": bid,
                "ask": ask,
                "last": self.current_price,
                "timestamp": datetime.now()
            }

            yield tick
            await asyncio.sleep(1.0 / rate)
```

**End-to-End Test Example**:
```python
@pytest.mark.integration
class TestTradingFlow:
    async def test_complete_trading_cycle(self):
        # Setup realistic market
        market = MarketSimulator("MNQ", Decimal("20000"))
        suite = await TradingSuite.create("MNQ", backend=MockBackend(market))

        # Subscribe to market data
        tick_count = 0
        async def on_tick(tick):
            nonlocal tick_count
            tick_count += 1

        await suite.on(EventType.TICK, on_tick)

        # Start market simulation
        asyncio.create_task(market.generate_tick_stream())

        # Wait for market data
        await asyncio.sleep(1)
        assert tick_count > 0  # ← Verifies data flows!

        # Place order
        order = await suite.orders.place_market_order(
            contract_id="MNQ", side=0, size=1
        )

        # Verify fill
        await asyncio.sleep(0.5)
        assert order.status == "filled"  # ← Verifies order processing!

        # Check position
        position = await suite.positions.get_position("MNQ")
        assert position.size == 1  # ← Verifies position tracking!
```

**What This Tests That Mocks Can't**:
- ✅ Real event flow (tick → order → position)
- ✅ Timing issues (async delays)
- ✅ State management (position updates)
- ✅ WebSocket message handling
- ✅ API contract compliance

### Code-Standards-Enforcer: Quality Gatekeeper

**Critical First Step**: **ALWAYS CHECK IDE DIAGNOSTICS**

**From**: `.claude/agents/code-standards-enforcer.md`

**Validation Workflow**:
```python
# 1. ALWAYS start with IDE diagnostics
await mcp__ide__getDiagnostics()

# 2. Fix any IDE issues first
# Edit files to resolve diagnostics

# 3. Run static analysis
uv run ruff check src/ --fix
uv run mypy src/ --strict

# 4. Check security
uv run bandit -r src/
uv run pip-audit

# 5. Verify performance
uv run pytest tests/benchmarks --benchmark-compare

# 6. Run full test suite
uv run pytest tests/ --cov=project_x_py

# 7. Final IDE check
await mcp__ide__getDiagnostics()
```

**Quality Gate Requirements**:
```yaml
test_coverage:
  overall: "> 90%"
  critical_paths: "> 95%"
  new_features: "100%"

performance:
  api_calls: "< 100ms"
  tick_processing: "< 10ms"
  order_placement: "< 50ms"

compliance:
  - IDE diagnostics clean
  - All tests passing
  - No security vulnerabilities
  - No performance regressions
  - Type checking passes
  - Code formatted
  - No linting errors
```

---

## Test Reporting Systems

### Your Current System: `run_tests.py`

**File**: `/mnt/c/Users/jakers/Desktop/risk-manager-v34/run_tests.py` (338 lines)

**Features**:
```
[1] Run ALL tests
[2] Run UNIT tests only
[3] Run INTEGRATION tests only
[4] Run SLOW tests only
[5] Run tests with COVERAGE report
[6] Run tests with COVERAGE + HTML report
[7] Run specific test file
[8] Run tests matching keyword
[9] Run last failed tests only
[v] Toggle VERBOSE mode
[c] Check COVERAGE status
[r] View last test REPORT
[q] Quit
```

**Report Structure**:
```
test_reports/
├── latest.txt                         # Always current (overwritten)
└── 2025-10-23_19-57-00_passed.txt    # Timestamped archive
```

**Report Format**:
```
================================================================================
Risk Manager V34 - Test Report
================================================================================
Test Run: All tests with coverage
Timestamp: 2025-10-23 19:57:00
Status: PASSED / FAILED
Exit Code: 0
================================================================================

[pytest output - colored terminal output preserved]

================================================================================
End of Report
================================================================================
```

**Key Code** (from `run_tests.py`):
```python
def save_test_report(output: str, description: str, exit_code: int):
    """Save test results to report files"""

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    status = "PASSED" if exit_code == 0 else "FAILED"

    # Format report
    report = f"""{'=' * 80}
Risk Manager V34 - Test Report
{'=' * 80}
Test Run: {description}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Status: {status}
Exit Code: {exit_code}
{'=' * 80}

{output}

{'=' * 80}
End of Report
{'=' * 80}
"""

    # Save to latest.txt (always overwritten)
    latest_path = REPORTS_DIR / "latest.txt"
    latest_path.write_text(report, encoding="utf-8")

    # Save to timestamped file
    timestamped_path = REPORTS_DIR / f"{timestamp}_{status.lower()}.txt"
    timestamped_path.write_text(report, encoding="utf-8")
```

### SDK's GitHub Actions Reporting

**File**: `.github/workflows/ci.yml`

**Test Job** (runs on every push/PR):
```yaml
test:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ["3.12", "3.13"]  # Test on multiple versions

  steps:
    - name: Run tests
      run: |
        uv run pytest tests/ -v --cov=project_x_py --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        token: ${{ secrets.CODECOV_TOKEN }}
        verbose: true
```

**Security Job**:
```yaml
security:
  steps:
    - name: Run bandit
      run: |
        uv run bandit -r src/ -ll -f json -o bandit-report.json

    - name: Upload security reports
      uses: actions/upload-artifact@v4
      with:
        name: security-reports
        path: bandit-report.json
```

**Performance Job** (only on PRs):
```yaml
performance:
  if: github.event_name == 'pull_request'

  steps:
    - name: Run benchmarks
      run: |
        uv run pytest tests/benchmarks/ --benchmark-json=benchmark.json

    - name: Compare benchmarks
      run: |
        # Compare with main branch baseline
        uv run pytest tests/benchmarks/ \
          --benchmark-compare=/tmp/baseline.json \
          --benchmark-compare-fail=min:20%  # Fail if >20% slower

    - name: Upload benchmark results
      uses: actions/upload-artifact@v4
      with:
        name: benchmark-results
        path: benchmark.json
```

**What Gets Uploaded**:
- Coverage reports → Codecov
- Security scans → GitHub Artifacts
- Benchmark results → GitHub Artifacts
- Test results → GitHub Artifacts

**AI agents can then**:
- Download artifacts
- Parse coverage reports
- Analyze security findings
- Compare performance metrics

---

## Complete Development Workflow

### Phase 1: TDD Development

**Agents**: `test-orchestrator`, `python-developer`, `integration-tester`

**From**: `.claude/commands/tdd-development.md`

```
Phase 1: Requirements Analysis
  test-orchestrator: Analyze feature requirements
  architecture-planner: Design system components
  data-analyst: Identify validation needs
  ↓
Phase 2: Test Definition (RED)
  test-orchestrator: Define test scenarios
  python-developer: Write failing tests
  Run: pytest -v
  Result: ❌ FAILED (expected - no implementation yet)
  ↓
Phase 3: Implementation (GREEN)
  python-developer: Write minimal code to pass tests
  Run: pytest -v
  Result: ✅ PASSED
  ↓
Phase 4: Refactoring (REFACTOR)
  code-refactor: Optimize code quality
  performance-optimizer: Profile and optimize
  Run: pytest -v
  Result: ✅ STILL PASSES
  ↓
Phase 5: Integration Testing
  integration-tester: Create E2E tests with MarketSimulator
  Run: pytest -v -m integration
  Result: ✅ PASSED (validates real SDK integration)
  ↓
Phase 6: Review and Documentation
  code-reviewer: Comprehensive review
  code-documenter: Update documentation
```

**Concrete Example**:

```bash
# 1. test-orchestrator plans
# "We need to test daily loss limit enforcement"

# 2. python-developer writes test FIRST (RED)
cat > tests/unit/rules/test_daily_loss.py << 'EOF'
@pytest.mark.asyncio
async def test_triggers_at_loss_limit():
    """Test that rule triggers when daily loss hits limit"""
    # ARRANGE
    rule = DailyRealizedLossRule(max_daily_loss=1000.0)
    event = RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={"realized_pnl": -1000.0}
    )

    # ACT
    violation = await rule.evaluate(event, mock_engine)

    # ASSERT
    assert violation is not None
    assert violation.severity == RuleSeverity.CRITICAL
EOF

# 3. Run test - should FAIL
pytest tests/unit/rules/test_daily_loss.py -v
# ❌ FAILED - ModuleNotFoundError: No module named 'DailyRealizedLossRule'

# 4. python-developer implements minimal code (GREEN)
cat > src/rules/daily_loss.py << 'EOF'
class DailyRealizedLossRule(BaseRule):
    async def evaluate(self, event, engine):
        if event.data["realized_pnl"] <= -self.max_daily_loss:
            return RuleViolation(severity=RuleSeverity.CRITICAL, ...)
        return None
EOF

# 5. Run test again - should PASS
pytest tests/unit/rules/test_daily_loss.py -v
# ✅ PASSED

# 6. integration-tester creates E2E test
cat > tests/integration/test_daily_loss_enforcement.py << 'EOF'
@pytest.mark.integration
async def test_daily_loss_enforcement_with_real_sdk():
    """Test that daily loss rule enforces with REAL SDK"""
    # Setup realistic market
    market = MarketSimulator("MNQ", Decimal("20000"))
    suite = await TradingSuite.create("MNQ", backend=MockBackend(market))

    # Create risk engine with daily loss rule
    engine = RiskEngine(
        suite=suite,
        rules=[DailyRealizedLossRule(max_daily_loss=1000.0)]
    )

    # Simulate losing trades
    await engine.handle_trade(pnl=-500)
    await engine.handle_trade(pnl=-600)  # Total: -1100 (exceeds limit)

    # Verify enforcement
    assert engine.is_locked_out()  # ← Tests REAL enforcement!
EOF

# 7. Run integration test
pytest tests/integration/test_daily_loss_enforcement.py -v -m integration
# ✅ PASSED - Verified with real SDK patterns!
```

### Phase 2: Quality Gates

**Agents**: `code-standards-enforcer`, `code-reviewer`, `security-auditor`

**Workflow**:
```bash
# 1. code-standards-enforcer runs quality gates
await mcp__ide__getDiagnostics()  # Check IDE first!
uv run ruff check src/ --fix
uv run mypy src/ --strict
uv run bandit -r src/ -ll
uv run pytest tests/ --cov=risk_manager --cov-report=term-missing

# 2. code-reviewer analyzes
# - Code quality
# - Best practices
# - Potential bugs
# - Performance concerns

# 3. security-auditor scans
uv run bandit -r src/ -f json -o security-report.json
uv run pip-audit

# 4. All must pass before proceeding
```

**Quality Gate Checklist**:
```markdown
- [ ] IDE diagnostics clean
- [ ] All tests passing (>90% coverage)
- [ ] No security vulnerabilities
- [ ] No performance regressions
- [ ] Type checking passes (mypy --strict)
- [ ] Code formatted (ruff format)
- [ ] No linting errors (ruff check)
```

### Phase 3: Code Review

**Agent**: `code-reviewer`

**Review Checklist**:
```markdown
## Architecture
- [ ] Follows async-first design
- [ ] Proper separation of concerns
- [ ] Error handling implemented
- [ ] Resource cleanup (async context managers)

## Code Quality
- [ ] Clear, descriptive names
- [ ] No code duplication
- [ ] Manageable complexity
- [ ] Comments explain "why", not "what"

## Testing
- [ ] Unit tests for logic
- [ ] Integration tests for flows
- [ ] Edge cases covered
- [ ] Performance tests if needed

## Security
- [ ] Input validation
- [ ] No hardcoded secrets
- [ ] Proper error handling
- [ ] Auth/authorization checks

## Performance
- [ ] No obvious bottlenecks
- [ ] Efficient algorithms
- [ ] Resource cleanup
- [ ] Memory usage acceptable
```

### Phase 4: Deployment Preparation

**Agents**: `deployment-coordinator`, `release-manager`

**From**: `.claude/agents/deployment-coordinator.md`

**Pre-Deployment Validation** (Parallel):
```
security-auditor: Vulnerability scan
test-orchestrator: Full test suite
performance-optimizer: Benchmarks
code-standards-enforcer: Compliance check
   ↓ (All must pass)
code-reviewer: Final review
   ↓
release-manager: Build packages
```

**Release Manager Pre-Release Checklist**:
```python
checks = {
    'version': await self._check_version(version),
    'tests': await self._run_tests(),
    'coverage': await self._check_coverage(),
    'docs': await self._check_documentation(),
    'changelog': await self._check_changelog(version),
    'breaking_changes': await self._detect_breaking_changes(),
    'dependencies': await self._check_dependencies(),
    'security': await self._security_scan()
}
```

---

## Integrating Your Test Menu

### How AI Agents Use Your Test Menu

**Scenario**: AI agent needs to run tests and analyze results

**Pattern**:
```python
import subprocess
import json

def run_tests_and_analyze():
    """AI agent runs tests via your menu"""

    # 1. Run tests via your menu script
    result = subprocess.run(
        ["python", "run_tests.py"],
        input="5\n",  # Option 5: Run with coverage
        capture_output=True,
        text=True
    )

    # 2. Read the generated report
    with open("test_reports/latest.txt") as f:
        report = f.read()

    # 3. Analyze results
    if "FAILED" in report:
        failures = extract_failures(report)
        print(f"Found {len(failures)} failures")

        # Create integration tests for gaps
        for failure in failures:
            create_integration_test(failure)

    elif "coverage" in report:
        coverage = extract_coverage(report)

        if coverage < 90:
            uncovered = find_uncovered_modules(report)
            print(f"Adding tests for: {uncovered}")
            add_tests_for(uncovered)

    # 4. Save analysis to memory for other agents
    save_to_memory("test-analysis", {
        "timestamp": datetime.now().isoformat(),
        "status": "PASSED" if result.returncode == 0 else "FAILED",
        "coverage": coverage,
        "failures": failures
    })
```

### Automated Test Selection

**Pattern**: AI decides which tests to run based on changes

```python
def select_test_strategy(changed_files: list) -> str:
    """AI agent selects appropriate test option"""

    if any("core/" in f for f in changed_files):
        # Core changes - run ALL tests
        return "1"  # Run ALL tests

    elif any("rules/" in f for f in changed_files):
        # Rule changes - run with coverage
        return "5"  # Run tests with COVERAGE

    elif any("sdk/" in f for f in changed_files):
        # SDK integration changes - focus on integration
        return "3"  # Run INTEGRATION tests only

    elif any("test" in f for f in changed_files):
        # Test file changes - run just those tests
        return "7"  # Run specific test file

    else:
        # Documentation/config changes - run unit only
        return "2"  # Run UNIT tests only
```

### Report Parsing Helpers

```python
def extract_failures(report: str) -> list:
    """Extract failed test names from report"""
    failures = []
    lines = report.split("\n")

    for line in lines:
        if "FAILED" in line:
            # Example: "FAILED tests/unit/test_rule.py::test_triggers"
            test_path = line.split("FAILED")[1].strip().split()[0]
            failures.append(test_path)

    return failures

def extract_coverage(report: str) -> float:
    """Extract overall coverage percentage"""
    for line in report.split("\n"):
        if "TOTAL" in line and "%" in line:
            # Example: "TOTAL    1000    200    80%"
            percentage = line.split("%")[0].split()[-1]
            return float(percentage)
    return 0.0

def find_uncovered_modules(report: str) -> list:
    """Find modules with coverage below 80%"""
    uncovered = []

    for line in report.split("\n"):
        if "%" in line and "TOTAL" not in line:
            parts = line.split()
            if len(parts) >= 2:
                module = parts[0]
                coverage_str = parts[-1].rstrip("%")
                try:
                    coverage = float(coverage_str)
                    if coverage < 80:
                        uncovered.append(module)
                except ValueError:
                    pass

    return uncovered
```

### Integration with Agent Workflow

**Complete Example**:
```python
# Agent: test-orchestrator
# Task: Validate test coverage after new feature

# 1. Run your test menu
import subprocess

result = subprocess.run(
    ["python", "run_tests.py"],
    input="5\n",  # Coverage report
    capture_output=True,
    text=True
)

# 2. Parse report
with open("test_reports/latest.txt") as f:
    report = f.read()

coverage = extract_coverage(report)
failures = extract_failures(report)

# 3. Make decisions
if coverage < 90:
    uncovered = find_uncovered_modules(report)

    # Coordinate with python-developer
    for module in uncovered:
        print(f"Creating tests for {module}")

        # Create test file
        test_file = f"tests/unit/test_{module.replace('/', '_')}.py"

        # Coordinate with python-developer agent to write tests
        coordinate_with_agent("python-developer", {
            "task": "write_unit_tests",
            "module": module,
            "output": test_file
        })

# 4. Re-run tests to verify
result = subprocess.run(
    ["python", "run_tests.py"],
    input="5\n",
    capture_output=True,
    text=True
)

# 5. Verify coverage improved
new_coverage = extract_coverage(open("test_reports/latest.txt").read())
print(f"Coverage improved: {coverage}% → {new_coverage}%")
```

---

## GitHub Actions Integration

### CI Pipeline: 4 Parallel Jobs

**File**: `.github/workflows/ci.yml`

**Job 1: Test** (lines 12-48)
```yaml
test:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ["3.12", "3.13"]  # Test on multiple versions

  steps:
    - name: Install dependencies
      run: uv sync --all-extras --dev

    - name: Run tests
      run: |
        uv run pytest tests/ -v --cov=project_x_py --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
```

**Job 2: Lint** (lines 49-78)
```yaml
lint:
  steps:
    - name: Run ruff
      run: |
        uv run ruff check src/
        uv run ruff format --check src/

    - name: Run mypy
      run: |
        uv run mypy src/

    - name: Check async compliance
      run: |
        uv run python scripts/check_async.py src/
```

**Job 3: Security** (lines 79-113)
```yaml
security:
  steps:
    - name: Run bandit
      run: |
        uv run bandit -r src/ -ll -f json -o bandit-report.json

    - name: Run safety check
      run: |
        uv run safety check --json

    - name: Run pip-audit
      run: |
        uv run pip-audit

    - name: Upload security reports
      uses: actions/upload-artifact@v4
      with:
        name: security-reports
        path: bandit-report.json
```

**Job 4: Performance** (lines 114-188, only on PRs)
```yaml
performance:
  if: github.event_name == 'pull_request'

  steps:
    - name: Run benchmarks
      run: |
        uv run pytest tests/benchmarks/ --benchmark-json=benchmark.json

    - name: Compare with baseline
      run: |
        # Compare with main branch
        uv run pytest tests/benchmarks/ \
          --benchmark-compare=/tmp/baseline.json \
          --benchmark-compare-fail=min:20%  # Fail if >20% slower

    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: benchmark-results
        path: benchmark.json
```

### Claude Code Review Workflow

**File**: `.github/workflows/claude-code-review.yml`

**Automated AI Code Review on Every PR**:
```yaml
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  claude-review:
    runs-on: ubuntu-latest

    steps:
      - name: Run Claude Code Review
        uses: anthropics/claude-code-action@beta
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}

          # Automated review prompt
          direct_prompt: |
            Please review this pull request and provide feedback on:
            - Code quality and best practices
            - Potential bugs or issues
            - Performance considerations
            - Security concerns
            - Test coverage

            Be constructive and helpful in your feedback.
```

**This Gives You**:
- ✅ Automated code review by Claude on every PR
- ✅ Feedback on quality, bugs, performance, security
- ✅ No manual review needed for simple changes
- ✅ Can customize prompts for different file types

### Release Workflow

**File**: `.github/workflows/release.yml`

**Triggered by Git Tags** (e.g., `git tag v1.0.0 && git push --tags`):
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'  # Trigger on version tags

jobs:
  test:
    uses: ./.github/workflows/ci.yml  # Run full CI first

  release:
    needs: test  # Only if all tests pass

    steps:
      - name: Verify version consistency
        run: |
          TAG_VERSION=${GITHUB_REF#refs/tags/v}
          PACKAGE_VERSION=$(python -c "from project import __version__; print(__version__)")
          if [ "$TAG_VERSION" != "$PACKAGE_VERSION" ]; then
            echo "Error: Version mismatch"
            exit 1
          fi

      - name: Build package
        run: uv build

      - name: Generate changelog
        run: python scripts/generate_changelog.py > RELEASE_NOTES.md

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          body_path: RELEASE_NOTES.md

      - name: Publish to Test PyPI
        run: twine upload --repository testpypi dist/*

      - name: Test installation
        run: |
          pip install --index-url https://test.pypi.org/simple/ project
          python -c "from project import main; print('Installation test passed')"

      - name: Publish to PyPI
        run: twine upload dist/*
```

**Complete Release Process**:
```
Developer creates tag: git tag v1.0.0 && git push --tags
   ↓
GitHub Actions triggers automatically
   ↓
Run full CI pipeline (test + lint + security + performance)
   ↓
Verify version consistency
   ↓
Build package
   ↓
Generate changelog
   ↓
Create GitHub release
   ↓
Upload to Test PyPI
   ↓
Test installation from Test PyPI
   ↓
Upload to Production PyPI
   ↓
Done!
```

---

## Agent Coordination Patterns

### Pattern 1: Parallel Pre-Deployment Validation

**Use Case**: Before deployment, validate everything in parallel

**Agents**: `security-auditor`, `test-orchestrator`, `performance-optimizer`, `code-standards-enforcer`

**Workflow**:
```
Parallel Execution:
  ├─ security-auditor: Run vulnerability scan
  ├─ test-orchestrator: Run full test suite
  ├─ performance-optimizer: Run benchmarks
  └─ code-standards-enforcer: Check compliance
        ↓ (All must complete and pass)
Sequential After Parallel:
  1. code-reviewer: Final review of all results
  2. release-manager: Build packages (if all passed)
```

**Implementation**:
```python
# deployment-coordinator orchestrates

async def validate_pre_deployment():
    """Run all validations in parallel"""

    # Launch all validators concurrently
    results = await asyncio.gather(
        security_auditor.scan(),
        test_orchestrator.run_full_suite(),
        performance_optimizer.benchmark(),
        code_standards_enforcer.validate()
    )

    # Check if all passed
    if all(r.passed for r in results):
        # Proceed to sequential review
        review = await code_reviewer.final_review(results)

        if review.approved:
            # Build and deploy
            await release_manager.build_packages()
            return True

    return False
```

### Pattern 2: TDD Development Cycle

**Agents**: `test-orchestrator`, `python-developer`, `integration-tester`, `code-refactor`

**Workflow**:
```
1. test-orchestrator: Define test requirements
   Output: Test plan

2. python-developer: Write failing tests (RED)
   Output: tests/unit/test_feature.py
   Run: pytest -v
   Result: ❌ FAILED

3. python-developer: Implement minimal code (GREEN)
   Output: src/feature.py
   Run: pytest -v
   Result: ✅ PASSED

4. code-refactor: Optimize code (REFACTOR)
   Output: Improved src/feature.py
   Run: pytest -v
   Result: ✅ STILL PASSES

5. integration-tester: Create E2E tests
   Output: tests/integration/test_feature_flow.py
   Run: pytest -v -m integration
   Result: ✅ PASSED
```

### Pattern 3: Post-Deployment Monitoring

**Agents**: `performance-optimizer`, `code-debugger`, `integration-tester`, `data-analyst`

**Workflow**:
```
Post-Deployment (continuous monitoring):
  ├─ performance-optimizer: Monitor metrics
  ├─ code-debugger: Watch error logs
  ├─ integration-tester: Run smoke tests
  └─ data-analyst: Analyze usage patterns
```

---

## Quality Gates

### Pre-Commit Hooks

**File**: `.pre-commit-config.yaml` (from SDK)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
        args: [--config-file, pyproject.toml]

  - repo: https://github.com/PyCQA/bandit
    hooks:
      - id: bandit
        args: [-r, src/, -ll]

  - repo: local
    hooks:
      - id: check-async
        name: Check 100% async compliance
        entry: python scripts/check_async.py
        files: \.py$
```

**What This Means**:
- Every commit triggers automatic checks
- Can't commit if ruff, mypy, or bandit fail
- Enforces code standards before code review

### Test Coverage Gates

```yaml
coverage_requirements:
  overall: "> 90%"
  critical_paths: "> 95%"
  new_features: "100%"
  edge_cases: "> 80%"
```

### Performance Gates

```yaml
performance_standards:
  api_calls: "< 100ms"
  tick_processing: "< 10ms"
  order_placement: "< 50ms"
  bar_aggregation: "< 20ms"

memory_limits:
  max_bars_per_timeframe: 1000
  max_trades_in_orderbook: 10000
  cleanup_after_ticks: 1000
```

---

## Deployment Pipeline

### Standard Release Flow

**From**: `.claude/agents/deployment-coordinator.md`

```
1. Pre-Release Validation (Parallel)
   ├─ code-standards-enforcer: Compliance check
   ├─ security-auditor: Security scan
   ├─ test-orchestrator: Full test suite
   └─ performance-optimizer: Benchmarks
        ↓
2. Release Preparation (Sequential)
   ├─ release-manager: Version bumping
   └─ code-documenter: Changelog generation
        ↓
3. Deployment Execution
   └─ release-manager: Package build, PyPI deployment
        ↓
4. Post-Deployment Validation
   ├─ integration-tester: Smoke tests
   └─ performance-optimizer: Production metrics
```

### Deployment Risk Levels

```yaml
risk_levels:
  low:
    changes:
      - Documentation updates
      - Non-breaking additions
      - Performance improvements
    deployment: Standard flow, normal testing

  medium:
    changes:
      - New features
      - Dependency updates
      - Configuration changes
    deployment: Extended testing, staged rollout, enhanced monitoring

  high:
    changes:
      - Breaking API changes
      - Database migrations
      - Security patches
    deployment: Canary deployment, feature flags, rollback plan ready

  critical:
    changes:
      - Core system changes
      - Authentication updates
      - Data model changes
    deployment: Maintenance window, full backup, war room ready
```

### Emergency Hotfix Process

```
Severity Levels:
  P0: System down        → Immediate response
  P1: Critical broken    → Within 2 hours
  P2: Major feature down → Within 24 hours
  P3: Minor issue        → Next release

Deployment Path:
  P0/P1: Direct to production (skip staging)
  P2:    Expedited staging
  P3:    Normal flow

War Room:
  - deployment-coordinator: Orchestration
  - code-debugger: Issue investigation
  - python-developer: Fix implementation
  - release-manager: Deployment execution
  - integration-tester: Validation

Communication:
  - Status updates every 15 minutes
  - Post-mortem within 48 hours
```

---

## For AI Reading This Document

### Your Mission

You are working on **Risk Manager V34**. Your goal:

1. ✅ Prevent "green tests but broken runtime"
2. ✅ Implement systematic TDD workflow
3. ✅ Create comprehensive integration tests
4. ✅ Automate quality gates
5. ✅ Enable safe deployments

### Critical Documents to Read First

**Read in this order**:

1. **START_HERE.md** - Project overview
2. **TDD_WORKFLOW_GUIDE.md** - How to write tests
3. **RUNTIME_INTEGRATION_TESTING.md** - How to prevent runtime failures
4. **This document** - How to orchestrate workflow

### Identify Your Role

```python
if task.involves("planning test strategy"):
    role = "test-orchestrator"
    # You COORDINATE, don't write tests
    # Create test plans, identify critical paths

elif task.involves("writing tests or code"):
    role = "python-developer"
    # You IMPLEMENT
    # Follow TDD: test first, then code

elif task.involves("integration testing"):
    role = "integration-tester"
    # You create E2E tests with REAL SDK
    # Use MarketSimulator patterns

elif task.involves("code review"):
    role = "code-reviewer"
    # You ANALYZE code quality
    # Use review checklist

elif task.involves("quality gates"):
    role = "code-standards-enforcer"
    # ALWAYS start: await mcp__ide__getDiagnostics()
    # Enforce coverage, linting, security

elif task.involves("deployment"):
    role = "deployment-coordinator"
    # You ORCHESTRATE
    # Coordinate other agents

elif task.involves("releasing"):
    role = "release-manager"
    # You MANAGE releases
    # Version bumping, PyPI deployment
```

### CRITICAL: Test-First Workflow

**NEVER write implementation before tests**:

```python
# ❌ WRONG ORDER
def implement_feature():
    write_code()      # Don't start here!
    write_tests()     # Too late!

# ✅ CORRECT ORDER (TDD)
def implement_feature():
    write_test()      # 1. Failing test first
    run_test()        # 2. Verify RED
    write_code()      # 3. Minimal implementation
    run_test()        # 4. Verify GREEN
    refactor()        # 5. Improve quality
    run_test()        # 6. Still GREEN
```

### Your Workflow Template

```bash
# 1. Read test reports
cat test_reports/latest.txt

# 2. Identify your role (see above)

# 3. Execute based on role

# If test-orchestrator:
#    - Create test plan
#    - Coordinate python-developer

# If python-developer:
#    - Write failing test (RED)
pytest tests/unit/test_feature.py -v  # ❌
#    - Implement minimal code (GREEN)
pytest tests/unit/test_feature.py -v  # ✅
#    - Refactor

# If integration-tester:
#    - Create E2E test with MarketSimulator
pytest tests/integration/test_flow.py -v -m integration  # ✅

# If code-standards-enforcer:
#    - Check IDE diagnostics FIRST
await mcp__ide__getDiagnostics()
#    - Run quality gates
ruff check src/ --fix
mypy src/ --strict
pytest tests/ --cov=risk_manager

# 4. Generate report
python run_tests.py  # Option 5
```

### Quality Gate Enforcement

**Before ANY commit**:

```bash
# 1. IDE diagnostics clean
await mcp__ide__getDiagnostics()

# 2. All tests passing
pytest tests/ -v

# 3. Coverage >90%
pytest tests/ --cov=risk_manager --cov-report=term-missing

# 4. No linting errors
ruff check src/
ruff format --check src/

# 5. Type checking passes
mypy src/

# 6. No security issues
bandit -r src/ -ll

# 7. Integration tests pass
pytest tests/integration/ -v -m integration
```

### Common Anti-Patterns to AVOID

**❌ DON'T**:
- Write code before tests
- Use mocks without spec=
- Skip integration tests
- Ignore IDE diagnostics
- Deploy without full test suite
- Skip quality gates
- Test only happy paths
- Mock internal components

**✅ DO**:
- Write failing test first (TDD)
- Use spec= on all mocks
- Create comprehensive integration tests
- ALWAYS check IDE diagnostics first
- Run full test suite before deploy
- Enforce all quality gates
- Test edge cases and errors
- Mock only at system boundaries

---

## Summary

### What You Have Now

1. **Test Infrastructure**: `run_tests.py` with 9 options + automatic reporting
2. **TDD Guide**: How to write tests (build-test-build)
3. **Integration Guide**: How to prevent runtime failures
4. **This Document**: How to orchestrate AI agents

### The Complete Workflow

```
Development (TDD):
  test-orchestrator: Plan
  python-developer: Test (RED) → Code (GREEN) → Refactor
  integration-tester: E2E tests
     ↓
Quality Gates:
  code-standards-enforcer: IDE → Lint → Type → Security
  code-reviewer: Review
     ↓
Integration Testing:
  integration-tester: MarketSimulator tests
     ↓
CI/CD (GitHub Actions):
  Parallel: test + lint + security + performance
  Claude Code Review: Automated
     ↓
Deployment:
  deployment-coordinator: Orchestrate
  release-manager: Build → PyPI
     ↓
Post-Deployment:
  integration-tester: Smoke tests
  performance-optimizer: Monitor
```

### Success Criteria

**You've succeeded when**:

- ✅ All tests pass (unit + integration)
- ✅ Coverage >90%
- ✅ No security vulnerabilities
- ✅ **Runtime works exactly like tests predicted**
- ✅ Enforcement triggers as expected
- ✅ Logging captures all events
- ✅ API communication verified
- ✅ No surprises in production

**Remember**: The goal is not just "tests pass" - the goal is **"runtime works because tests validated the real integration"**.

That's what the SDK does. That's what you should do.

Good luck! 🚀
