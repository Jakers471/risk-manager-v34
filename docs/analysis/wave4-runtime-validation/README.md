# Wave 4 Analysis: Runtime Validation & Debugging Strategy

**Purpose**: Make runtime validation MANDATORY to prevent "tests pass but runtime broken" syndrome

**Status**: Delegation plan complete, researchers ready to spawn

**Timeline**: 1 week

---

## The Problem (33 Failed Projects)

**Pattern**:
1. Write tests (they pass ✅)
2. Mark feature "complete" ✅
3. Deploy → Runtime broken ❌
4. System "seems dead" ❌
5. Hours of debugging ❌
6. Give up, start over ❌

**Root Cause**: Runtime validation was optional, not mandatory

**This is Project #34** - Must succeed where 33 others failed

---

## The Solution

**Make runtime validation MANDATORY in the workflow**

### New Definition of Done (v2.0)

**Before**: Feature complete when tests pass

**After**: Feature complete when:
1. ✅ Tests pass (unit, integration, E2E)
2. ✅ **Smoke test passing (exit code 0)** ← NEW MANDATORY
3. ✅ **8 checkpoints logging** (if core feature) ← NEW MANDATORY
4. ✅ **Runtime trace clean** (no deadlocks) ← NEW MANDATORY
5. ✅ **Feature observable in logs** (can see it working) ← NEW MANDATORY

### New Workflow

```
Old Workflow:
1. Write tests → 2. Tests pass → 3. Mark complete → 4. Deploy → FAILS

New Workflow:
1. Write tests → 2. Tests pass → 3. **RUN SMOKE TEST** → 4. Exit code 0? → 5. Mark complete → 6. Deploy → SUCCESS
```

---

## Wave 4 Deliverables

### Coordinator Report

**File**: `00-WAVE4-COORDINATOR-REPORT.md`

**Contents**:
- Problem statement (33 failed projects)
- Current state analysis
- Solution strategy
- Delegation plan for 4 researchers
- Success criteria

---

### Research Outputs

#### 01-LOGGING-STRATEGY.md (Researcher 1)

**Mission**: Document WHERE to add logs, WHAT to log, HOW to debug

**Contents**:
- Phase-by-phase logging requirements
- 8-checkpoint integration guide
- Log format standards
- Examples for each feature type

**Timeline**: 2-3 days

**Priority**: High

---

#### 02-SMOKE-TEST-REQUIREMENTS.md (Researcher 2)

**Mission**: Document WHEN to run smoke tests, WHAT they validate

**Contents**:
- When to run smoke tests
- What smoke tests validate
- Exit code interpretation (0/1/2)
- Integration with roadmap
- Making smoke tests mandatory

**Timeline**: 2-3 days

**Priority**: Critical

---

#### 03-RUNTIME-DEBUGGING-PROTOCOL.md (Researcher 3)

**Mission**: Document STEP-BY-STEP debugging when runtime fails

**Contents**:
- Debugging flowchart (exit code → diagnosis → fix)
- Checkpoint-based debugging (find where it stopped → fix)
- Common failure patterns (from 33 projects)
- Tools available (logs, trace mode, async debug)

**Timeline**: 3-4 days

**Priority**: High

---

#### 04-DEFINITION-OF-DONE-V2.md (Researcher 4)

**Mission**: Update all workflow documentation with runtime requirements

**Contents**:
- Updated Definition of Done (with runtime validation)
- Updated AGENT_GUIDELINES.md sections
- Updated IMPLEMENTATION_ROADMAP.md format (add smoke test checkboxes)
- Feature complete checklist template
- Enforcement strategy

**Timeline**: 2-3 days

**Priority**: Critical

**Dependencies**: Needs output from Researchers 1, 2, 3

---

## Quick Reference

### Current Runtime Infrastructure (Already Exists)

**8-Checkpoint System**:
```
🚀 Checkpoint 1: Service Start
✅ Checkpoint 2: Config Loaded
✅ Checkpoint 3: SDK Connected
✅ Checkpoint 4: Rules Initialized
✅ Checkpoint 5: Event Loop Running
📨 Checkpoint 6: Event Received ← LIVENESS PROOF
🔍 Checkpoint 7: Rule Evaluated
⚠️ Checkpoint 8: Enforcement Triggered
```

**Runtime Reliability Pack**:
- Smoke Test (8s validation) - `python run_tests.py → [s]`
- Soak Test (30-60s stability) - `python run_tests.py → [r]`
- Trace Mode (async debug) - `python run_tests.py → [t]`
- Log Viewer - `python run_tests.py → [l]`
- Env Snapshot - `python run_tests.py → [e]`

**Exit Codes**:
- `0` = SUCCESS (first event observed, system alive)
- `1` = EXCEPTION (check logs for stack trace)
- `2` = STALLED (boot >8s or no events, check subscriptions)

---

### What's Missing (Wave 4 Fixes)

1. ❌ Runtime validation not mandatory in workflow
2. ❌ Agents can skip smoke tests
3. ❌ No clear logging strategy (where to add logs for each feature)
4. ❌ No debugging protocol (what to do when smoke test fails)
5. ❌ Definition of Done doesn't require smoke test

---

## Timeline

**Week 1** (Days 1-7):

**Days 1-4**: Parallel research
- Researcher 1: Logging Strategy
- Researcher 2: Smoke Test Requirements
- Researcher 3: Runtime Debugging Protocol

**Days 5-7**: Consolidation
- Researcher 4: Definition of Done v2.0
- Update AGENT_GUIDELINES.md
- Update IMPLEMENTATION_ROADMAP.md

**Result**: Runtime validation is MANDATORY

---

## Success Metrics

**Wave 4 succeeds if**:

1. ✅ Runtime validation becomes MANDATORY in workflow
2. ✅ Agents can't skip smoke tests
3. ✅ Clear logging strategy for every feature type
4. ✅ Debugging protocol prevents "stuck for hours"
5. ✅ Definition of Done includes runtime requirements

**Wave 4 prevents**:

1. ❌ "Tests pass but runtime broken" (projects #1-33 problem)
2. ❌ "System seems dead, no idea why"
3. ❌ "Spent 3 hours debugging, found nothing"
4. ❌ "Feature complete but can't see it working"

---

## Key Principles

1. **Runtime validation is MANDATORY** - Not optional
2. **Smoke tests must pass** - Can't claim "feature complete" without exit code 0
3. **Logging is required** - Every feature needs observable behavior
4. **8-checkpoints for core** - If feature touches manager/engine/enforcement, use checkpoints
5. **Prove it works** - Tests passing is step 1, runtime working is step 2

---

## Navigation

### Coordinator Documents

- `00-WAVE4-COORDINATOR-REPORT.md` - This analysis and delegation plan
- `README.md` - This navigation guide

### Research Outputs (Will be created)

- `01-LOGGING-STRATEGY.md` - Logging requirements for every feature type
- `02-SMOKE-TEST-REQUIREMENTS.md` - When and how to run smoke tests
- `03-RUNTIME-DEBUGGING-PROTOCOL.md` - Step-by-step debugging guide
- `04-DEFINITION-OF-DONE-V2.md` - Updated workflow with runtime validation

### Related Documentation

**Current Runtime System**:
- `docs/specifications/unified/runtime-validation-strategy.md` - 8-checkpoint system (detailed)
- `docs/specifications/unified/testing-strategy.md` - Current testing approach
- `run_tests.py` - Interactive test runner with smoke tests
- `src/runtime/` - Runtime reliability pack implementation

**Current Workflow**:
- `AGENT_GUIDELINES.md` - Current agent workflow (WILL BE UPDATED)
- `IMPLEMENTATION_ROADMAP.md` - Implementation progress (WILL BE UPDATED)
- `CONTRACTS_REFERENCE.md` - API contracts

**Gap Analysis**:
- `docs/analysis/wave2-gap-analysis/06-TESTING-GAPS.md` - Testing gaps identified

---

## For Researchers

### Before You Start

1. Read `00-WAVE4-COORDINATOR-REPORT.md` (coordinator report)
2. Understand the problem (33 failed projects)
3. Review current runtime infrastructure:
   - `docs/specifications/unified/runtime-validation-strategy.md`
   - `docs/specifications/unified/testing-strategy.md`
   - `run_tests.py`

### Your Mission

**Make runtime validation MANDATORY, not optional**

### Output Requirements

Each researcher creates one markdown file:
- Comprehensive documentation
- Real examples from codebase
- Step-by-step instructions
- Clear, actionable guidance

### Timeline

- **Days 1-4**: R1, R2, R3 work in parallel
- **Days 5-7**: R4 consolidates and updates workflow

---

## For Future Agents

**If you're implementing a feature, you MUST**:

1. ✅ Write tests (TDD)
2. ✅ Tests pass
3. ✅ **RUN SMOKE TEST** (`python run_tests.py → [s]`)
4. ✅ **EXIT CODE 0** (if not, debug and fix)
5. ✅ **VERIFY LOGS** (can you see your feature working?)
6. ✅ Update roadmap
7. ✅ Commit

**If smoke test fails**:
- Read `03-RUNTIME-DEBUGGING-PROTOCOL.md`
- Follow step-by-step debugging guide
- Don't mark feature "complete" until exit code 0

**This is how we prevent project #34 from failing like #1-33**

---

**Status**: Delegation plan complete
**Next Action**: Spawn 4 researchers
**Priority**: CRITICAL (prevents project failure)

---

**Last Updated**: 2025-10-25
**Maintained By**: Wave 4 Coordinator
**Version**: 1.0
