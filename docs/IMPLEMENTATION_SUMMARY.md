# Implementation Master Plan - Executive Summary

**Date**: 2025-10-27
**Agent**: Implementation Plan Agent (#7)
**Status**: Complete - Ready for Execution

---

## Overview

This is the **comprehensive, actionable master plan** to wire all 13 risk rules into the Risk Manager V34 event-driven architecture. The plan is based on:

- ✅ 13 unified rule specifications (conflict-free)
- ✅ SDK event mapping (which events trigger which rules)
- ✅ Current implementation analysis (2 rules done, 11 missing)
- ✅ Architectural patterns validated (EventBus, EventBridge, RiskEngine)

---

## Current State

### What's Working ✅
- **Core Architecture**: EventBus, EventBridge, RiskEngine, TradingIntegration
- **State Management**: Database, PnLTracker
- **Rules**: RULE-001 (Max Contracts), RULE-002 (Max Contracts Per Instrument)
- **SDK Integration**: Connected, receiving events, enforcement working

### What's Missing ❌
- **Event Router** (critical - all lockout enforcement depends on this)
- **3 State Managers**: LockoutManager, TimerManager, ResetScheduler
- **Market Data Feed** (for unrealized P&L rules)
- **11 Rules**: RULE-003 (partial), RULE-004 through RULE-013

---

## The Plan (6 Phases, 23-31 days)

### Phase 1: Core Event Infrastructure (5-7 days)
**Goal**: Establish robust event routing foundation

**Deliverables**:
1. **Event Router** (2 days) - Routes events, enforces lockouts
2. **Event Subscriptions** (1 day) - Rules declare which events they need
3. **Event Validation** (1 day) - SDK data validation
4. **Action Queue** (1-2 days) - Prevents race conditions between rules
5. **Integration Tests** (1 day) - E2E event flow validation

**Success Criteria**: Events routed correctly, lockout checks working, action queue preventing conflicts

---

### Phase 2: State Management Modules (4-6 days)
**Goal**: Implement 3 missing state managers

**Deliverables**:
1. **MOD-002: LockoutManager** (2 days) - Hard lockouts with timer-based unlock
2. **MOD-003: TimerManager** (1-2 days) - Countdown timers for cooldowns
3. **MOD-004: ResetScheduler** (1-2 days) - Daily P&L resets at configured time
4. **Integration Tests** (1 day) - Lockout → Timer → Reset flow

**Success Criteria**: All 3 managers working, persisting state, surviving restarts

**Unblocks**: 7 rules (54%) - RULE-003, RULE-006, RULE-007, RULE-008, RULE-009, RULE-010, RULE-011, RULE-013

---

### Phase 3: High-Priority Rules (6-8 days)
**Goal**: Implement critical account protection rules

**Deliverables**:
1. **RULE-003 Complete** (1 day) - Daily realized loss (70% → 100%)
2. **RULE-009** (3 days) - Session block outside (multi-session, holidays)
3. **RULE-006** (2 days) - Trade frequency limit (rolling windows)
4. **Integration Tests** (included) - Account violation prevention

**Success Criteria**: All 3 rules enforcing correctly, tests passing, 8 checkpoints logging

---

### Phase 4: Medium-Priority Rules (4-5 days)
**Goal**: Complete timer/cooldown and symbol-based rules

**Deliverables**:
1. **RULE-007** (1 day) - Cooldown after loss (tiered cooldowns)
2. **RULE-008** (2 days) - No stop-loss grace (10s timer)
3. **RULE-010** (1 day) - Auth loss guard (canTrade monitoring)
4. **RULE-011** (1 day) - Symbol blocks (symbol-specific lockout)
5. **RULE-013** (1 day) - Daily realized profit (opposite of RULE-003)

**Success Criteria**: All 5 rules working, cooldowns/lockouts validated

**Note**: Can parallelize with Phase 5 (Market Data)

---

### Phase 5: Market Data + Unrealized PnL (5-7 days)
**Goal**: Enable unrealized P&L rules (quote-driven)

**Deliverables**:
1. **Market Data Feed** (3 days) - Real-time quote subscriptions, high-frequency
2. **Unrealized Calculator** (included) - Tick values, Long/Short calculations
3. **RULE-004** (2-3 days) - Daily unrealized loss (trade-by-trade)
4. **RULE-005** (shared) - Max unrealized profit (trade-by-trade)
5. **RULE-012** (1-2 days) - Trade management (automation)

**Success Criteria**: Quote feed working (100+ quotes/sec), unrealized P&L accurate

**Unblocks**: 3 rules (23%) - RULE-004, RULE-005, RULE-012

---

### Phase 6: Production Polish (3-4 days)
**Goal**: Production readiness

**Deliverables**:
1. **Comprehensive Testing** (2 days) - 95%+ unit, 80%+ integration, E2E, runtime
2. **Documentation** (1 day) - PROJECT_STATUS.md (100%), OPERATOR_RUNBOOK.md
3. **Monitoring** (1 day) - Prometheus metrics, Grafana dashboards, alerts

**Success Criteria**: All tests passing, documentation complete, monitoring active, runtime smoke test exit code 0

---

## Critical Path (20-28 days)

The **longest dependency chain** (items that cannot be parallelized):

```
Phase 1 (Event Router + Action Queue)     5-7 days
    ↓
Phase 2 (MOD-002, MOD-003, MOD-004)       4-6 days
    ↓
Phase 3 (RULE-003, RULE-009, RULE-006)    6-8 days
    ↓
Phase 5 (Market Data + RULE-004/005/012)  5-7 days
    ↓
Phase 6 (Testing + Docs + Monitoring)     3-4 days
    ↓
TOTAL: 23-32 days (4.5-6.5 weeks)
```

**Note**: Phase 4 can run in parallel with Phase 5 (not on critical path)

---

## Key Architectural Decisions

### 1. Event Router (Critical Component)
**Why**: All lockout enforcement requires pre-rule event routing
**What**: Checks lockouts before routing events to rules
**Impact**: If account locked, new positions closed immediately (not passed to rules)

### 2. Action Queue (Race Condition Prevention)
**Why**: Multiple rules may trigger simultaneously (RULE-001 + RULE-003)
**What**: Priority-based sequential execution (hard lockouts before position limits)
**Impact**: Prevents race conditions when closing positions

### 3. LockoutManager (3 Types)
**Why**: Different rules need different lockout behaviors
**What**:
- **HARD**: Account-wide, timer-based unlock (RULE-003, RULE-009, RULE-013)
- **SYMBOL**: Symbol-specific, permanent (RULE-011)
- **TIMER**: Account-wide, countdown unlock (RULE-006, RULE-007)
**Impact**: Flexible lockout system supporting all 13 rules

### 4. Market Data Feed (High-Frequency)
**Why**: Unrealized P&L rules need real-time price updates
**What**: Subscribe to SDK quote updates, publish QUOTE_UPDATE events
**Impact**: Enables RULE-004, RULE-005, RULE-012 (23% of rules)

---

## Success Metrics

### By Phase
- ✅ Unit tests: 95%+ coverage
- ✅ Integration tests: 80%+ coverage
- ✅ E2E tests: Critical paths covered
- ✅ Runtime smoke test: Exit code 0
- ✅ Code review passed

### Overall Project
- ✅ 13/13 rules implemented (100%)
- ✅ All 3 state managers working
- ✅ Event Router implemented
- ✅ Market Data Feed integrated
- ✅ Action Queue preventing race conditions
- ✅ 8-checkpoint logging working correctly
- ✅ Performance: 100 events/sec sustained
- ✅ Production deployment successful

---

## Files Created

### Documents
1. **`docs/IMPLEMENTATION_MASTER_PLAN.md`** (24KB)
   - Comprehensive phase-by-phase implementation guide
   - Detailed file-by-file breakdown
   - Code examples for each component
   - Testing strategies
   - Risk mitigation

2. **`docs/DEPENDENCY_GRAPH.txt`** (12KB)
   - ASCII art dependency visualization
   - Critical path analysis
   - Bottleneck identification
   - Parallelization opportunities
   - Weekly milestones

3. **`docs/IMPLEMENTATION_SUMMARY.md`** (This file)
   - Executive summary
   - Quick reference for stakeholders

---

## Estimation Accuracy

### Conservative Estimate (Worst Case)
- Phase 1: 7 days
- Phase 2: 6 days
- Phase 3: 8 days
- Phase 4: 5 days
- Phase 5: 7 days
- Phase 6: 4 days
**Total**: 37 days (7.5 weeks)

### Optimistic Estimate (Best Case)
- Phase 1: 5 days
- Phase 2: 4 days
- Phase 3: 6 days
- Phase 4: 4 days (parallel with Phase 5)
- Phase 5: 5 days
- Phase 6: 3 days
**Total**: 23 days (4.5 weeks)

### Realistic Estimate (Expected)
- With parallelization: **26-28 days (5-5.5 weeks)**
- Accounts for: Testing time, integration issues, minor setbacks
- Assumes: No major architectural surprises, SDK stable

---

## Risk Mitigation

### Top Risks

1. **Event Router Complexity**
   - **Risk**: More complex than estimated (2 days → 4 days)
   - **Mitigation**: Simple lockout check in RiskEngine as fallback
   - **Recovery**: Refactor to proper Event Router in Phase 6

2. **SDK API Changes**
   - **Risk**: SDK update breaks integration
   - **Mitigation**: Pin SDK version (`project-x-py==3.5.9`)
   - **Recovery**: Comprehensive integration tests catch breakage

3. **Market Data Feed Overload**
   - **Risk**: High-frequency quotes overwhelm system
   - **Mitigation**: Throttle (max 10/sec per symbol), debounce calculations
   - **Recovery**: Circuit breaker if quote lag >1s

4. **Phase Dependencies**
   - **Risk**: Phase 2 delay blocks Phase 3
   - **Mitigation**: Clear success criteria, integration tests validate boundaries
   - **Recovery**: Can parallelize some Phase 4 work with Phase 5

---

## Next Steps (Start Today)

### Immediate Actions
1. **Review master plan with team** (1 hour)
2. **Create Phase 1 branch** (`git checkout -b phase1-event-infrastructure`)
3. **Start Event Router implementation** (Day 1-2)
   - File: `src/risk_manager/core/event_router.py`
   - Tests: `tests/unit/test_event_router.py`

### Week 1 Goals
- ✅ Event Router implemented and tested
- ✅ Event subscriptions added to BaseRule
- ✅ Action Queue preventing race conditions
- ✅ Phase 1 integration tests passing

### Week 2 Goals
- ✅ MOD-002 (LockoutManager) working
- ✅ MOD-003 (TimerManager) working
- ✅ MOD-004 (ResetScheduler) working
- ✅ Phase 2 integration tests passing

---

## Resources

### Documentation References
- **Rule Specs**: `docs/specifications/unified/rules/` (13 files)
- **Event Mapping**: `SDK_EVENTS_QUICK_REFERENCE.txt`
- **Architecture**: `docs/analysis/wave3-audits/06-architecture-consistency-audit.md`
- **Project Entry**: `CLAUDE.md`

### Code References
- **EventBus**: `src/risk_manager/core/events.py`
- **EventBridge**: `src/risk_manager/sdk/event_bridge.py`
- **RiskEngine**: `src/risk_manager/core/engine.py`
- **BaseRule**: `src/risk_manager/rules/base.py`
- **TradingIntegration**: `src/risk_manager/integrations/trading.py`

---

## Questions?

### For Phase Details
→ Read `docs/IMPLEMENTATION_MASTER_PLAN.md`

### For Dependencies
→ Read `docs/DEPENDENCY_GRAPH.txt`

### For Rule Specs
→ Read `docs/specifications/unified/rules/RULE-XXX-*.md`

### For Current Status
→ Read `docs/current/PROJECT_STATUS.md`

### For Testing
→ Read `docs/testing/TESTING_GUIDE.md`

---

## Approval Checklist

Before starting implementation, verify:

- [ ] Master plan reviewed by lead developer
- [ ] Dependency graph understood by team
- [ ] Resource allocation confirmed (5-6 weeks)
- [ ] Phase 1 success criteria agreed upon
- [ ] Testing strategy approved
- [ ] Risk mitigation plan reviewed
- [ ] Monitoring strategy defined
- [ ] Documentation standards clear

---

**Status**: Ready for Phase 1 execution

**Let's build the most robust trading risk manager! 🛡️**
