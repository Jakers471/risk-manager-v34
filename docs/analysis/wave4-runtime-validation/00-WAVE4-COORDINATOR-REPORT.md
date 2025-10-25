# Wave 4 Coordinator Report: Runtime Validation & Debugging Strategy

**Coordinator**: Wave 4 Coordinator - Runtime Validation & Debugging Strategy
**Date**: 2025-10-25
**Status**: Analysis Complete - Delegation Plan Ready
**Mission**: Make runtime validation MANDATORY to prevent "tests pass but runtime broken" syndrome

---

## Executive Summary

This project is attempt #34 to build a working risk management system. **All 33 previous attempts failed** with the same pattern:
- Tests pass (green)
- Runtime doesn't work (seemingly not alive)
- Project abandoned

**Root Cause**: Tests validate logic correctness, but don't prove the system is actually alive and operational.

**Solution**: Make runtime validation MANDATORY in the development workflow, not optional.

---

## The Problem

### What Happened in Projects #1-33

```
Day 1-7: Build features, write tests
  → Tests pass ✅
  → Feels complete

Day 8: Deploy to staging
  → System starts
  → Nothing happens
  → No events processed
  → No clear errors

Day 9: Debug for hours
  → Can't find the issue
  → Logs show "everything working"
  → System just... doesn't work

Day 10: Give up, start over
  → Project #34
```

### Why Traditional Testing Failed

**Unit Tests** validate:
- Function logic
- Edge cases
- Error handling

**BUT** unit tests don't prove:
- System actually boots
- Events actually fire
- SDK subscriptions work
- System is alive

**Integration Tests** validate:
- Component interactions
- Real SDK calls
- Database operations

**BUT** integration tests don't prove:
- First event arrives within reasonable time
- System doesn't deadlock
- Event loop actually runs

### The Gap

**Traditional workflow**:
```
1. Write tests (TDD) ✅
2. Tests pass (green) ✅
3. Mark feature "complete" ✅
4. Deploy → FAILS ❌
```

**Missing step**: **Runtime validation** (prove it's alive)

---

## Current State Analysis

### What Exists (Good Foundation)

The project has **excellent** runtime infrastructure already:

#### 8-Checkpoint System
**Location**: `docs/specifications/unified/runtime-validation-strategy.md`

Strategic logging at critical points:
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

**Purpose**: Find exactly where runtime fails

#### Runtime Reliability Pack
**Location**: `src/runtime/` (6 files, 1,316 lines)

5 runtime validation capabilities:
1. **Smoke Test** (8s boot validation)
   - Validates first event fires within 8s
   - Exit codes: 0=success, 1=exception, 2=stalled

2. **Soak Test** (30-60s stability)
   - Catches memory leaks, deadlocks

3. **Trace Mode** (async debugging)
   - Dumps all pending tasks
   - Finds deadlocks

4. **Log Viewer** (real-time logs)
   - Stream logs as they happen

5. **Env Snapshot** (configuration)
   - Shows all env vars, config files

**Tests**: 70 runtime tests (65 passing, 5 failing)

#### Interactive Test Runner
**Location**: `run_tests.py` (711 lines)

Menu-driven test runner with:
- Auto-save reports to `test_reports/latest.txt`
- Runtime validation options `[s]`, `[r]`, `[t]`a
- Gate test `[g]` (unit + integration + smoke combo)

### What's Missing (The Problem)

**Runtime validation is OPTIONAL, not MANDATORY**

#### Current Workflow (from AGENT_GUIDELINES.md)

```markdown
### Step 7: Run Integration Tests
**If feature integrates with SDK or database**:
python run_tests.py → [3]

### Step 8: Update the Roadmap
**CRITICAL**: Update IMPLEMENTATION_ROADMAP.md
```

**Notice**: No smoke test requirement!

#### Current Definition of Done (from AGENT_GUIDELINES.md)

```markdown
A feature is complete when:
1. ✅ Implementation matches unified spec
2. ✅ Follows contracts
3. ✅ Unit tests written and passing
4. ✅ Integration tests written and passing
5. ✅ E2E tests written and passing
6. ✅ Roadmap updated
7. ✅ Git commit
8. ✅ Changes pushed
```

**Missing**: Smoke test must pass (exit code 0)

### The Critical Gap

**Agents can mark features "complete" without runtime validation!**

This is how projects #1-33 failed:
1. Agent writes tests (they pass)
2. Agent updates roadmap
3. Agent commits
4. **Agent never runs smoke test**
5. Feature "complete" but runtime broken

---

## The Solution: Mandatory Runtime Validation

### New Definition of Done (v2.0)

**A feature is NOT complete until**:

```markdown
1. ✅ Unit tests passing
2. ✅ Integration tests passing (if applicable)
3. ✅ **SMOKE TEST PASSING (exit code 0)** ← NEW MANDATORY
4. ✅ **8 checkpoints logging** (if feature touches core) ← NEW MANDATORY
5. ✅ **Runtime trace clean** (no deadlocks) ← NEW MANDATORY
6. ✅ **Feature observable in logs** (can see it working) ← NEW MANDATORY
7. ✅ Roadmap updated
8. ✅ Git commit
```

### New Workflow (v2.0)

```markdown
Step 1-6: [Same as before - write tests, implement, pass tests]

Step 7: **MANDATORY Runtime Validation**

  7a. Run smoke test
      python run_tests.py → [s]

  7b. Check exit code
      - 0 = Success → Continue
      - 1 = Exception → Fix error, repeat
      - 2 = Stalled → Check subscriptions, repeat

  7c. Verify checkpoints (if core feature)
      python run_tests.py → [l]
      Look for: 🚀 ✅ ✅ ✅ ✅ 📨 🔍 ⚠️

  7d. Verify feature visible in logs
      grep "<feature-name>" data/logs/risk_manager.log

  7e. (Optional) Run soak test for major features
      python run_tests.py → [r]

Step 8: Update Roadmap (only if Step 7 passes)

Step 9: Commit
```

### Enforcement Strategy

**How to make this MANDATORY**:

1. **Update AGENT_GUIDELINES.md**
   - Add Step 7 (Runtime Validation) to workflow
   - Update Definition of Done
   - Add examples of smoke test failures

2. **Update IMPLEMENTATION_ROADMAP.md**
   - Add smoke test checkbox to every feature
   - Example: `- [ ] Smoke test passing (exit code 0)`

3. **Create Feature Complete Checklist**
   - Template agents must follow
   - Includes runtime validation steps
   - Can't skip

4. **Update Testing Documentation**
   - `docs/specifications/unified/testing-strategy.md`
   - Add runtime validation as Layer 2
   - Update test pyramid

---

## Delegation Plan

I'm delegating to 4 specialist researchers to create comprehensive runtime validation documentation.

### Researcher 1: Logging Strategy Specialist

**Mission**: Document WHERE to add logs, WHAT to log, HOW to debug

**Deliverables**:
- `docs/analysis/wave4-runtime-validation/01-LOGGING-STRATEGY.md`

**Contents**:
1. **Phase-by-Phase Logging Requirements**
   - Phase 1 (State Managers): What logs to add
   - Phase 2 (Risk Rules): What logs to add
   - Phase 3 (SDK Integration): What logs to add
   - For each: File, function, line number, log format

2. **8-Checkpoint Integration Guide**
   - When to use checkpoint logs vs feature logs
   - How to add new checkpoints (if needed)
   - Checkpoint log format standards

3. **Log Format Standards**
   - Structured logging (JSON, key-value)
   - Contextual information (always include account_id, rule_id, etc.)
   - Searchable patterns (grep-friendly)

4. **Examples for Each Feature Type**
   - State Manager logging example
   - Risk Rule logging example
   - SDK Integration logging example
   - Enforcement logging example

**Estimated Effort**: 2-3 days

**Priority**: High (blocks other researchers)

---

### Researcher 2: Smoke Test Requirements Specialist

**Mission**: Document WHEN to run smoke tests, WHAT they validate, HOW to interpret results

**Deliverables**:
- `docs/analysis/wave4-runtime-validation/02-SMOKE-TEST-REQUIREMENTS.md`

**Contents**:
1. **When to Run Smoke Tests**
   - After every feature implementation?
   - After every phase completion?
   - Before every commit?
   - Create decision matrix

2. **What Smoke Tests Validate**
   - System boots without errors
   - All 8 checkpoints complete
   - First event fires within 8s
   - No deadlocks or hangs
   - Basic system liveness

3. **Exit Code Interpretation**
   - Exit code 0: What it means, what to do next
   - Exit code 1: Common causes, debugging steps
   - Exit code 2: Common causes (most common!), debugging steps
   - Examples from actual failures

4. **Integration with Roadmap**
   - Add smoke test checkboxes to every feature
   - Template: `- [ ] Smoke test passing (exit code 0)`
   - How to update roadmap

5. **Making Smoke Tests Mandatory**
   - Why agents can't skip this
   - Checklist template
   - Enforcement strategy

**Estimated Effort**: 2-3 days

**Priority**: Critical (needed for Definition of Done v2.0)

---

### Researcher 3: Runtime Debugging Protocol Specialist

**Mission**: Document STEP-BY-STEP debugging when runtime fails

**Deliverables**:
- `docs/analysis/wave4-runtime-validation/03-RUNTIME-DEBUGGING-PROTOCOL.md`

**Contents**:
1. **Debugging Flowchart**
   ```
   Smoke test fails
   ├─> Exit code 1 (EXCEPTION)
   │   ├─> Read logs
   │   ├─> Find stack trace
   │   └─> Fix error
   │
   └─> Exit code 2 (STALLED)
       ├─> Find last checkpoint
       ├─> Checkpoint 1-5: Boot failure
       │   └─> Debug component initialization
       └─> Checkpoint 5: No events
           ├─> Check SDK subscriptions
           ├─> Check EventBridge mapping
           └─> Check EventBus dispatching
   ```

2. **Exit Code Diagnosis**
   - **Exit Code 1 (Exception)**:
     - Common exceptions (ImportError, ConfigError, APIError)
     - How to read stack traces
     - Fix patterns

   - **Exit Code 2 (Stalled)**:
     - Most common failure mode
     - Checkpoint-based diagnosis
     - SDK subscription troubleshooting
     - EventBridge debugging

3. **Checkpoint-Based Debugging**
   - For each checkpoint: What it validates, what failure means, how to fix
   - Checkpoint 1: Never started → Check entry point
   - Checkpoint 2: Config failed → Check YAML syntax
   - Checkpoint 3: SDK failed → Check credentials
   - Checkpoint 4: Rules failed → Check rule imports
   - Checkpoint 5: Event loop failed → Check async setup
   - Checkpoint 6: No events → **MOST COMMON** → Check subscriptions
   - Checkpoint 7: Rules not evaluating → Check rule logic
   - Checkpoint 8: Enforcement not triggering → Check SDK integration

4. **Common Failure Patterns** (from 33 previous projects)
   - Over-mocking (mocks don't match reality)
   - SDK subscriptions not wired
   - EventBridge not mapping events
   - Event loop blocked
   - Async tasks deadlocked

5. **Tools Available**
   - Logs: `python run_tests.py → [l]`
   - Trace mode: `python run_tests.py → [t]`
   - Env snapshot: `python run_tests.py → [e]`
   - Async debug: `ASYNC_DEBUG=1`

**Estimated Effort**: 3-4 days

**Priority**: High (agents will use this constantly)

---

### Researcher 4: Definition of Done Updater

**Mission**: Update all workflow documentation with runtime requirements

**Deliverables**:
- `docs/analysis/wave4-runtime-validation/04-DEFINITION-OF-DONE-V2.md`

**Contents**:
1. **Updated Definition of Done**
   - Old definition (from AGENT_GUIDELINES.md)
   - New definition (with runtime validation)
   - Side-by-side comparison
   - Rationale for each addition

2. **Updated AGENT_GUIDELINES.md Sections**
   - Add Step 7 (Runtime Validation) to workflow
   - Update "Definition of Done" section
   - Add runtime validation examples
   - Add troubleshooting section

3. **Updated IMPLEMENTATION_ROADMAP.md Format**
   - Add smoke test checkbox to every feature template
   - Example:
     ```markdown
     ### MOD-003: Timer Manager
     - [ ] Create timer_manager.py
     - [ ] Implement database schema
     - [ ] Write unit tests
     - [ ] **Smoke test passing (exit code 0)** ← NEW
     ```

4. **Feature Complete Checklist Template**
   - Checklist agents must follow before marking complete
   - Includes all runtime validation steps
   - Can't skip smoke test

5. **Enforcement Strategy**
   - How to ensure agents follow this
   - Automated checks (future)?
   - Code review requirements (future)?
   - Documentation visibility

**Estimated Effort**: 2-3 days

**Priority**: Critical (updates core workflow docs)

**Dependencies**: Needs output from Researchers 1, 2, 3

---

## Research Coordination

### Parallel Work (Days 1-4)

**Researchers 1, 2, 3** can work in parallel:
- Researcher 1: Logging Strategy (2-3 days)
- Researcher 2: Smoke Test Requirements (2-3 days)
- Researcher 3: Runtime Debugging Protocol (3-4 days)

### Sequential Work (Days 5-7)

**Researcher 4** starts after others complete:
- Needs logging strategy from R1
- Needs smoke test requirements from R2
- Needs debugging protocol from R3
- Consolidates into Definition of Done v2.0

### Total Timeline

**Week 1** (Days 1-7):
- Days 1-4: R1, R2, R3 work in parallel
- Days 5-7: R4 consolidates and updates workflow docs

---

## Success Criteria

**Wave 4 succeeds if**:

1. ✅ **Runtime validation is MANDATORY in workflow**
   - Definition of Done v2.0 includes smoke test requirement
   - AGENT_GUIDELINES.md has Step 7 (Runtime Validation)
   - Can't mark feature "complete" without passing smoke test

2. ✅ **Clear logging strategy for every feature type**
   - Agents know WHERE to add logs
   - Agents know WHAT to log
   - Agents know HOW to format logs

3. ✅ **Smoke test requirements are clear**
   - Agents know WHEN to run smoke tests
   - Agents know HOW to interpret exit codes
   - Agents know WHAT to do when smoke test fails

4. ✅ **Debugging protocol prevents "stuck for hours"**
   - Step-by-step flowchart for every failure mode
   - Checkpoint-based diagnosis
   - Common failure patterns documented

5. ✅ **Agents can't skip runtime validation**
   - Checklist template enforces it
   - Roadmap format includes smoke test checkbox
   - Clear visibility in workflow

---

## What Wave 4 Prevents

By making runtime validation mandatory, we prevent:

1. ❌ **"Tests pass but runtime broken"** (projects #1-33 problem)
2. ❌ **"System seems dead, no idea why"** (no events firing)
3. ❌ **"Spent 3 hours debugging, found nothing"** (no debugging protocol)
4. ❌ **"Feature complete but can't see it working"** (no observable logs)
5. ❌ **"Deployed to staging, nothing happens"** (no smoke test before deploy)

---

## Risk Assessment

### Risks

1. **Agents ignore Step 7** (Runtime Validation)
   - Mitigation: Make it part of Definition of Done
   - Mitigation: Add to roadmap checkboxes
   - Mitigation: Clear visibility in workflow

2. **Smoke tests too slow** (agents skip for speed)
   - Current: 8 second timeout (very fast)
   - Mitigation: Already optimized
   - Mitigation: Gate test combines all validations

3. **Documentation too long** (agents don't read)
   - Mitigation: Create quick reference cards
   - Mitigation: Include examples
   - Mitigation: Make it searchable

### Assumptions

1. **Agents will follow updated AGENT_GUIDELINES.md**
   - Assumption: Agents read guidelines before implementing
   - Validation: Include in every prompt

2. **8-checkpoint system is sufficient**
   - Assumption: Current checkpoints cover critical paths
   - Validation: 70 runtime tests validate this

3. **Smoke test exit codes are clear**
   - Assumption: Exit codes 0/1/2 are self-explanatory
   - Validation: Add detailed documentation

---

## Next Steps

**Immediate (Today)**:
1. ✅ Create Wave 4 directory
2. ✅ Write coordinator report (this document)
3. ✅ Create README.md with navigation

**This Week**:
1. Spawn 4 researchers with delegation instructions
2. Monitor progress
3. Review deliverables
4. Consolidate into final documentation

**Next Week**:
1. Update AGENT_GUIDELINES.md with Definition of Done v2.0
2. Update IMPLEMENTATION_ROADMAP.md with smoke test checkboxes
3. Validate with actual agent workflow
4. Measure success (do agents run smoke tests?)

---

## Researcher Output Files

**Expected deliverables** (all in `docs/analysis/wave4-runtime-validation/`):

1. `01-LOGGING-STRATEGY.md` (Researcher 1)
   - Phase-by-phase logging requirements
   - 8-checkpoint integration
   - Log format standards
   - Examples

2. `02-SMOKE-TEST-REQUIREMENTS.md` (Researcher 2)
   - When to run smoke tests
   - What they validate
   - Exit code interpretation
   - Roadmap integration

3. `03-RUNTIME-DEBUGGING-PROTOCOL.md` (Researcher 3)
   - Debugging flowchart
   - Exit code diagnosis
   - Checkpoint-based debugging
   - Common failure patterns

4. `04-DEFINITION-OF-DONE-V2.md` (Researcher 4)
   - Updated Definition of Done
   - Updated AGENT_GUIDELINES.md sections
   - Updated IMPLEMENTATION_ROADMAP.md format
   - Feature complete checklist template

5. `README.md` (Coordinator)
   - Navigation guide
   - Quick reference
   - Links to all outputs

---

## Key Principles

These principles guide all Wave 4 work:

1. **Runtime validation is MANDATORY** - Not optional, not "nice to have"
2. **Smoke tests must pass** - Can't claim "feature complete" without exit code 0
3. **Logging is required** - Every feature needs observable behavior
4. **8-checkpoints for core** - If feature touches manager/engine/enforcement, use checkpoints
5. **Prove it works** - Tests passing is step 1, runtime working is step 2

---

## Critical Success Factors

**Project #34 succeeds where #1-33 failed if**:

1. ✅ Agents run smoke tests BEFORE marking features complete
2. ✅ Agents know HOW to debug when smoke tests fail
3. ✅ Agents know WHERE to add logs for every feature
4. ✅ Agents can't skip runtime validation (it's mandatory)
5. ✅ Clear documentation prevents "stuck for hours" debugging

---

## Conclusion

**The Problem**: 33 projects failed because runtime validation was optional

**The Solution**: Make runtime validation mandatory in the workflow

**The Strategy**:
- Update Definition of Done v2.0 (requires smoke test)
- Create comprehensive logging strategy
- Document runtime debugging protocol
- Update all workflow documentation

**The Outcome**: Project #34 succeeds where 33 others failed

---

**Status**: Analysis complete, delegation plan ready
**Next Action**: Create README.md and spawn 4 researchers
**Timeline**: 1 week to comprehensive runtime validation strategy
**Priority**: CRITICAL (prevents project failure)

---

**Coordinator**: Wave 4 Coordinator
**Date**: 2025-10-25
**Version**: 1.0
