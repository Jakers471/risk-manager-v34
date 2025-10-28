# Next Steps for AI Agents - Phase 2 Implementation

**Current Status**: Phase 1 Complete ✅ (95/95 tests passing)
**Next Phase**: Phase 2 - Reset Scheduler & Risk Rules
**Priority**: CRITICAL
**Estimated Duration**: 12-15 hours (parallelizable)

---

## 📋 Agent Onboarding Checklist

### **BEFORE STARTING - READ THESE FILES IN ORDER:**

1. **`CLAUDE.md`** (root) - AI assistant entry point and testing system
2. **`docs/current/DEPLOYMENT_ROADMAP.md`** - Master plan to 100% readiness
3. **`docs/current/PHASE1_COMPLETION_REPORT.md`** - What we just completed
4. **`test_reports/latest.txt`** - Current test results (95/95 passing)
5. **`docs/specifications/unified/architecture/MODULES_SUMMARY.md`** - Module specs
6. **`docs/specifications/unified/rules/README.md`** - Risk rule specifications

### **IMPORTANT CONTEXT:**
- ✅ **Phase 1 is COMPLETE**: MOD-002 (Lockout Manager) + MOD-003 (Timer Manager) implemented
- ✅ **All 95 tests passing**: Foundation is solid
- 🔄 **Phase 2 is NEXT**: MOD-004 (Reset Scheduler) + 10 Risk Rules
- ⚠️ **Follow TDD**: Write tests first (RED), implement (GREEN), refactor
- ⚠️ **Use timezone.utc**: All datetimes must be `datetime.now(timezone.utc)`

---

## 🎯 Phase 2 Task Breakdown

### **Task 1: MOD-004 Reset Scheduler** ⭐ CRITICAL
**Agent**: reset-scheduler-specialist
**Priority**: HIGHEST (blocks 5 rules)
**Duration**: 3-4 hours
**Dependencies**: MOD-001 (Database), MOD-002 (Lockout Manager)

#### Files to Create:
1. **`tests/unit/test_state/test_reset_scheduler.py`** (TDD RED phase)
   - ~18 tests covering daily/weekly resets
   - Timezone conversion (ET ↔ UTC)
   - Database persistence
   - Integration with PnL Tracker

2. **`src/risk_manager/state/reset_scheduler.py`** (TDD GREEN phase)
   - ~250-300 lines
   - Public API (see DEPLOYMENT_ROADMAP.md for details)

#### Test Categories:
```python
class TestDailyReset:
    # Test daily reset at 5:00 PM ET
    test_schedule_daily_reset_creates_schedule()
    test_daily_reset_triggers_at_5pm_et()
    test_daily_reset_converts_et_to_utc()
    test_daily_reset_persists_to_database()
    test_daily_reset_clears_pnl_tracker()
    test_daily_reset_clears_lockout()

class TestWeeklyReset:
    # Test weekly reset (Monday at 5:00 PM ET)
    test_schedule_weekly_reset()
    test_weekly_reset_triggers_monday()
    test_weekly_reset_clears_weekly_pnl()

class TestTimezoneHandling:
    # Critical for ET ↔ UTC conversion
    test_et_to_utc_conversion_standard_time()
    test_et_to_utc_conversion_daylight_time()
    test_dst_transition_handling()

class TestDatabasePersistence:
    test_reset_log_saved_to_database()
    test_last_reset_time_loaded_from_database()

class TestBackgroundTask:
    test_background_task_checks_every_minute()
    test_reset_triggered_automatically()
    test_shutdown_stops_background_task()
```

#### Implementation Requirements:
- **Timezone Handling**: Convert ET (Eastern Time) to UTC correctly
- **Background Task**: Check every minute if reset time reached
- **Database Table**:
  ```sql
  CREATE TABLE reset_log (
      account_id TEXT,
      reset_type TEXT,  -- 'daily' or 'weekly'
      reset_time TEXT,  -- ISO 8601 UTC
      triggered_at TEXT,
      PRIMARY KEY (account_id, reset_time)
  );
  ```
- **Integration Points**:
  - Call `pnl_tracker.reset_daily_pnl(account_id)` on daily reset
  - Call `lockout_manager.clear_lockout(account_id)` on reset
  - Emit reset event for rules to handle

#### Acceptance Criteria:
- [ ] 18 tests written and passing
- [ ] Daily reset triggers at 5:00 PM ET
- [ ] Weekly reset triggers Monday at 5:00 PM ET
- [ ] Timezone conversion correct (including DST)
- [ ] Database persistence working
- [ ] Integration with PnL Tracker working
- [ ] Integration with Lockout Manager working

---

### **Task 2: RULE-004 Daily Loss Limit** ⭐ CRITICAL
**Agent**: daily-loss-limit-specialist
**Priority**: HIGHEST
**Duration**: 2-3 hours
**Dependencies**: MOD-002, MOD-004, PnL Tracker

#### Files to Create:
1. **`tests/unit/test_rules/test_daily_loss_limit.py`** (~12 tests)
2. **`src/risk_manager/rules/daily_loss_limit.py`** (~150-200 lines)

#### Test Scenarios:
```python
class TestDailyLossLimit:
    test_loss_below_limit_passes()
    test_loss_at_limit_passes()
    test_loss_exceeds_limit_violates()
    test_violation_flattens_all_positions()
    test_violation_triggers_lockout()
    test_lockout_persists_until_reset()
    test_reset_clears_lockout()
    test_multi_symbol_loss_tracking()
    test_unrealized_plus_realized_pnl()
    test_approaching_limit_warning()
    test_rule_disabled_when_locked()
    test_enforcement_action_correct()
```

#### Implementation:
```python
class DailyLossLimitRule(BaseRule):
    def __init__(self, max_loss: float):  # e.g., -500.00
        self.max_loss = max_loss

    async def evaluate(self, event: RiskEvent) -> Optional[RuleViolation]:
        # Get current daily P&L
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)

        # Check if loss exceeds limit
        if daily_pnl < self.max_loss:
            return RuleViolation(
                rule_id="RULE-004",
                severity=ViolationSeverity.CRITICAL,
                message=f"Daily loss limit exceeded: ${daily_pnl:.2f} < ${self.max_loss:.2f}",
                action=EnforcementAction.FLATTEN_ALL,
                lockout=LockoutConfig(
                    duration_type="until_reset",
                    reset_time="17:00 ET"
                )
            )
        return None
```

---

### **Task 3: RULE-005 Daily Profit Target**
**Agent**: daily-profit-target-specialist
**Duration**: 2 hours
**Dependencies**: MOD-002, MOD-004, PnL Tracker

#### Files to Create:
1. **`tests/unit/test_rules/test_daily_profit_target.py`** (~10 tests)
2. **`src/risk_manager/rules/daily_profit_target.py`** (~150 lines)

**Similar to RULE-004 but triggers on profit > target (e.g., +$500)**

---

### **Task 4: RULE-007 Weekly Loss Limit**
**Agent**: weekly-loss-limit-specialist
**Duration**: 2-3 hours
**Dependencies**: MOD-002, MOD-004, PnL Tracker

#### Files to Create:
1. **`tests/unit/test_rules/test_weekly_loss_limit.py`** (~12 tests)
2. **`src/risk_manager/rules/weekly_loss_limit.py`** (~180 lines)

**Key Difference**: Tracks cumulative P&L across Mon-Fri, resets Monday 5:00 PM ET

---

### **Task 5: RULE-009 Max Trades Per Day**
**Agent**: max-trades-per-day-specialist
**Duration**: 2 hours
**Dependencies**: MOD-002, MOD-004, Trade Counter

#### Files to Create:
1. **`tests/unit/test_rules/test_max_trades_per_day.py`** (~10 tests)
2. **`src/risk_manager/rules/max_trades_per_day.py`** (~150 lines)

**Note**: Requires Trade Counter (simple int tracking, reset daily)

---

### **Task 6: RULE-010 Trade Frequency Limit**
**Agent**: trade-frequency-limit-specialist
**Duration**: 2 hours
**Dependencies**: MOD-002 (Cooldown), MOD-003 (Timer)

#### Files to Create:
1. **`tests/unit/test_rules/test_trade_frequency_limit.py`** (~12 tests)
2. **`src/risk_manager/rules/trade_frequency_limit.py`** (~150 lines)

**Example**: 30-minute cooldown between trades

---

## 🤖 Agent Swarm Strategy

### **Parallel Execution Plan:**

**Wave 1 (Start Immediately):**
- **Agent 1**: MOD-004 Reset Scheduler (blocks everything else)
- **Agent 2**: RULE-004 Daily Loss Limit (depends on MOD-004, start tests first)
- **Agent 3**: RULE-005 Daily Profit Target (depends on MOD-004, start tests first)

**Wave 2 (After MOD-004 Complete):**
- **Agent 4**: RULE-007 Weekly Loss Limit
- **Agent 5**: RULE-009 Max Trades Per Day
- **Agent 6**: RULE-010 Trade Frequency Limit

**Wave 3 (Quality & Integration):**
- **Agent 7**: Quality Enforcer - Review all implementations
- **Agent 8**: Integration Validator - Test MOD-004 + rules together

---

## 🧪 Testing Protocol

### **TDD Workflow (STRICTLY FOLLOW):**

#### RED Phase:
```bash
# 1. Write tests first
# Create test file with all test scenarios

# 2. Run tests (they should FAIL)
pytest tests/unit/test_state/test_reset_scheduler.py -v

# Expected: All tests fail (module doesn't exist yet)
```

#### GREEN Phase:
```bash
# 3. Implement minimal code to pass tests
# Create implementation file

# 4. Run tests again
pytest tests/unit/test_state/test_reset_scheduler.py -v

# Expected: All tests pass ✅
```

#### REFACTOR Phase:
```bash
# 5. Clean up code, add documentation
# Run tests to ensure nothing broke

pytest tests/unit/test_state/test_reset_scheduler.py -v

# Expected: Still passing ✅
```

### **Test Running:**
```bash
# Run specific test file
pytest tests/unit/test_rules/test_daily_loss_limit.py -v

# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src/risk_manager --cov-report=html

# Save results
pytest tests/unit/ -v > test_reports/phase2_progress.txt 2>&1
```

---

## ⚠️ Critical Requirements

### **MUST DO:**
1. ✅ **Write tests FIRST** (TDD RED phase)
2. ✅ **Use `datetime.now(timezone.utc)`** for ALL datetimes
3. ✅ **Follow existing patterns** (see MOD-002, MOD-003 for examples)
4. ✅ **Add to `__init__.py`** exports
5. ✅ **Run full test suite** before marking complete
6. ✅ **Document public APIs** with docstrings
7. ✅ **Update DEPLOYMENT_ROADMAP.md** progress

### **MUST NOT DO:**
- ❌ Don't use naive datetimes (`datetime.now()` without timezone)
- ❌ Don't skip tests ("I'll add them later")
- ❌ Don't make functions async unless they do I/O
- ❌ Don't use `datetime.utcnow()` (deprecated)
- ❌ Don't create files outside project structure

---

## 📊 Success Metrics

### **Phase 2 Complete When:**
- [ ] MOD-004 Reset Scheduler implemented (18 tests passing)
- [ ] 5 Priority 1 rules implemented (56 tests passing)
- [ ] All 95 + 74 = **169 tests passing** (Phase 1 + Phase 2 Priority 1)
- [ ] Database migrations complete
- [ ] Integration with existing modules verified
- [ ] Code reviewed by Quality Enforcer
- [ ] No regressions in Phase 1 tests

### **Test Count Target:**
| Component | Current | Phase 2 Target | Delta |
|-----------|---------|----------------|-------|
| Phase 1 | 95 | 95 | 0 |
| MOD-004 | 0 | 18 | +18 |
| RULE-004 | 0 | 12 | +12 |
| RULE-005 | 0 | 10 | +10 |
| RULE-007 | 0 | 12 | +12 |
| RULE-009 | 0 | 10 | +10 |
| RULE-010 | 0 | 12 | +12 |
| **TOTAL** | **95** | **169** | **+74** |

---

## 🚀 Agent Invocation Command

**For the user to run:**
```bash
# Deploy Phase 2 agent swarm
"Deploy Phase 2 agent swarm: MOD-004 Reset Scheduler + 5 Priority 1 Rules (RULE-004, 005, 007, 009, 010). Use parallel execution, follow TDD strictly, all agents report back when complete."
```

**Expected agents:**
1. reset-scheduler-specialist
2. daily-loss-limit-specialist
3. daily-profit-target-specialist
4. weekly-loss-limit-specialist
5. max-trades-per-day-specialist
6. trade-frequency-limit-specialist
7. quality-enforcer
8. integration-validator

---

## 📁 File Organization

**After Phase 2, structure should be:**
```
src/risk_manager/
├── state/
│   ├── database.py ✅
│   ├── lockout_manager.py ✅
│   ├── timer_manager.py ✅
│   ├── reset_scheduler.py ← NEW
│   ├── pnl_tracker.py ✅
│   └── __init__.py (update exports)
├── rules/
│   ├── max_position_rule.py ✅
│   ├── max_contracts_rule.py ✅
│   ├── daily_loss_limit.py ← NEW
│   ├── daily_profit_target.py ← NEW
│   ├── weekly_loss_limit.py ← NEW
│   ├── max_trades_per_day.py ← NEW
│   ├── trade_frequency_limit.py ← NEW
│   └── __init__.py (update exports)

tests/unit/
├── test_state/
│   ├── test_lockout_manager.py ✅
│   ├── test_timer_manager.py ✅
│   ├── test_reset_scheduler.py ← NEW
│   └── test_pnl_tracker.py ✅
├── test_rules/
│   ├── test_max_position_rule.py ✅
│   ├── test_daily_loss_limit.py ← NEW
│   ├── test_daily_profit_target.py ← NEW
│   ├── test_weekly_loss_limit.py ← NEW
│   ├── test_max_trades_per_day.py ← NEW
│   └── test_trade_frequency_limit.py ← NEW
```

---

## 🔗 Key Reference Documents

**Specifications:**
- `docs/specifications/unified/architecture/MODULES_SUMMARY.md` - Module specs
- `docs/specifications/unified/rules/` - Individual rule specs

**Implementation Examples:**
- `src/risk_manager/state/lockout_manager.py` - State module pattern
- `src/risk_manager/state/timer_manager.py` - Background task pattern
- `src/risk_manager/rules/max_position_rule.py` - Rule pattern
- `tests/unit/test_state/test_lockout_manager.py` - Test pattern

**Current Status:**
- `docs/current/PHASE1_COMPLETION_REPORT.md` - What we just completed
- `docs/current/DEPLOYMENT_ROADMAP.md` - Full deployment plan
- `test_reports/latest.txt` - Current test results

---

## 💡 Tips for Agents

1. **Copy Existing Patterns**: MOD-002 and MOD-003 are good templates
2. **Test File Before Implementation**: Write all tests first, ensure they fail
3. **Use Fixtures**: See `tests/conftest.py` for database/manager fixtures
4. **Check Timezone Imports**: `from datetime import datetime, timedelta, timezone`
5. **Run Tests Frequently**: After every method implementation
6. **Update Exports**: Add new modules to `__init__.py`
7. **Document as You Go**: Docstrings on all public methods
8. **Communicate Progress**: Update todo list via TodoWrite tool

---

**Status**: ✅ Phase 1 Complete, 🔄 Phase 2 Ready
**Next Action**: Deploy Phase 2 agent swarm
**Expected Completion**: 12-15 hours with parallel agents
**Final Target**: 169/169 tests passing
