# Implementation Progress Tracker

**Generated**: 2025-10-27
**Purpose**: Track progress of code changes from CODE_CHANGES_CHECKLIST.md
**Status**: Ready to start

---

## Progress Overview

**Total Tasks**: 48
**Completed**: 0 (0%)
**In Progress**: 0
**Blocked**: 0
**Not Started**: 48 (100%)

---

## Phase 1: CRITICAL Changes (Day 1)

**Target**: Get events flowing with correct fields
**Estimated Time**: 6-8 hours

| ID | Task | Status | File | Lines | Assignee | Notes |
|----|------|--------|------|-------|----------|-------|
| 1.1 | Add realized_pnl to TRADE_EXECUTED | TODO | event_bridge.py | 320-331 | | Blocks RULE-003 |
| 1.2 | Add account_id to TRADE_EXECUTED | TODO | event_bridge.py | 320-331 | | Blocks multi-account |
| 1.3 | Add account_id to POSITION_UPDATED | TODO | event_bridge.py | 184-196 | | Blocks multi-account |
| 1.4 | Add account_id to POSITION_CLOSED | TODO | event_bridge.py | 203-212 | | Blocks multi-account |
| 1.5 | Fix POSITION_UPDATED timestamp | TODO | event_bridge.py | 193 | | datetime object not string |
| 1.6 | Fix POSITION_CLOSED timestamp | TODO | event_bridge.py | 209 | | datetime object not string |
| 1.7 | Fix ORDER event timestamp | TODO | event_bridge.py | 277 | | datetime object not string |
| 1.8 | Fix TRADE_EXECUTED timestamp | TODO | event_bridge.py | 328 | | datetime object not string |
| 1.9 | Add account_id to ORDER events | TODO | event_bridge.py | 267-280 | | Blocks multi-account |
| 1.10 | Add contract_id to ORDER events | TODO | event_bridge.py | 267-280 | | Needed for RULE-008 |
| 1.11 | Add order_type to ORDER events | TODO | event_bridge.py | 267-280 | | CRITICAL for RULE-008 |
| 1.12 | Add stop_price to ORDER events | TODO | event_bridge.py | 267-280 | | CRITICAL for RULE-008 |
| 1.13 | Add limit_price to ORDER events | TODO | event_bridge.py | 267-280 | | Nice to have |
| 2.1 | Add position tracking dict to __init__ | TODO | event_bridge.py | __init__ | | For POSITION_OPENED |
| 2.2 | Implement POSITION_OPENED detection | TODO | event_bridge.py | 178-199 | | CRITICAL for RULE-008 |
| 2.3 | Update tracking on POSITION_CLOSED | TODO | event_bridge.py | 201-216 | | Cleanup tracking |
| 3.1 | Add QUOTE_UPDATE event type | TODO | events.py | 9-46 | | Blocks RULE-004/005 |
| 3.2 | Add NEW_BAR event type | TODO | events.py | 9-46 | | Optional |
| 3.3 | Add DATA_UPDATE event type | TODO | events.py | 9-46 | | Optional |
| 4.1 | Implement _on_quote_update handler | TODO | event_bridge.py | After 363 | | Blocks RULE-004/005 |
| 4.2 | Subscribe to quote_update callback | TODO | event_bridge.py | 100-136 | | Enable quote events |
| 4.3 | (Optional) Add quote throttling | TODO | event_bridge.py | __init__ | | Prevent event flood |

**Phase 1 Completion Criteria**:
- [ ] All events have account_id
- [ ] TRADE_EXECUTED has realized_pnl
- [ ] ORDER_PLACED has order_type and stop_price
- [ ] POSITION_OPENED events fire correctly
- [ ] QUOTE_UPDATE events flow through
- [ ] Smoke test passes

---

## Phase 2: HIGH Changes (Day 2)

**Target**: Fix rules to use correct events
**Estimated Time**: 6-8 hours

| ID | Task | Status | File | Lines | Assignee | Notes |
|----|------|--------|------|-------|----------|-------|
| 5.1 | Fix RULE-001 event subscriptions | TODO | max_position.py | 37-42 | | Use 3 position events |
| 5.2 | Fix RULE-002 event subscriptions | TODO | max_contracts_per_instrument.py | TBD | | Use 3 position events |
| 5.3 | Change RULE-003 to TRADE_EXECUTED | TODO | daily_loss.py | 29-36 | | Wrong event type |
| 5.4 | Add realized_pnl extraction | TODO | daily_loss.py | 29-36 | | Get from event.data |
| 5.5 | Add null check for half-turns | TODO | daily_loss.py | 29-36 | | Skip if pnl is None |
| 5.6 | Create RULE-004 implementation | TODO | daily_unrealized_loss.py | NEW | | Full implementation |
| 5.7 | Create RULE-005 implementation | TODO | max_unrealized_profit.py | NEW | | Full implementation |
| 5.8 | Add quote_cache to RiskEngine | TODO | engine.py | __init__ | | For current prices |
| 5.9 | Create RULE-008 implementation | TODO | stop_loss_check.py | NEW | | Full implementation |
| 5.10 | Implement timer-based grace period | TODO | stop_loss_check.py | NEW | | asyncio timer |
| 5.11 | Add stop-loss detection logic | TODO | stop_loss_check.py | NEW | | Check order_type == 3 |
| 6.1 | Update PnLTracker to TRADE_EXECUTED | TODO | pnl_tracker.py | TBD | | Subscribe to correct event |
| 6.2 | Add realized_pnl extraction | TODO | pnl_tracker.py | TBD | | From event.data |
| 6.3 | Add null check for half-turns | TODO | pnl_tracker.py | TBD | | Skip opening trades |
| 6.4 | Add POSITION_OPENED handler | TODO | position_tracker.py | TBD | | Track new positions |
| 6.5 | Add POSITION_CLOSED handler | TODO | position_tracker.py | TBD | | Remove closed positions |
| 6.6 | Update POSITION_UPDATED handler | TODO | position_tracker.py | TBD | | Update existing positions |
| 6.7 | Add stop_price tracking | TODO | order_tracker.py | TBD | | Track stop prices |
| 6.8 | Add order_type tracking | TODO | order_tracker.py | TBD | | Track order types |
| 6.9 | Create stop_loss_orders lookup | TODO | order_tracker.py | TBD | | For RULE-008 |
| 7.1 | Add quote_cache to RiskEngine | TODO | engine.py | __init__ | | Dict of latest quotes |
| 7.2 | Subscribe to QUOTE_UPDATE | TODO | engine.py | start() | | Enable quote handling |
| 7.3 | Implement quote cache handler | TODO | engine.py | NEW | | Update cache on quotes |

**Phase 2 Completion Criteria**:
- [ ] RULE-001/002 use all 3 position events
- [ ] RULE-003 uses TRADE_EXECUTED correctly
- [ ] RULE-004/005 implemented and working
- [ ] RULE-008 implemented with correct logic
- [ ] All state trackers updated
- [ ] Quote cache working
- [ ] Integration tests pass

---

## Phase 3: MEDIUM Changes (Day 3)

**Target**: Tests, docs, consistency
**Estimated Time**: 4-6 hours

| ID | Task | Status | File | Lines | Assignee | Notes |
|----|------|--------|------|-------|----------|-------|
| 8.1 | Audit P&L field usage | TODO | Multiple | All | | Find all uses |
| 8.2 | Replace with canonical names | TODO | Multiple | All | | realized_pnl, unrealized_pnl |
| 8.3 | Audit price field usage | TODO | Multiple | All | | Find all uses |
| 8.4 | Replace with canonical names | TODO | Multiple | All | | average_price |
| 8.5 | Remove "side" from POSITION events | TODO | event_bridge.py | 190 | | Redundant field |
| 8.6 | Update rules to use size > 0 | TODO | rules/*.py | Various | | Instead of side field |
| 9.1 | Update TRADE_EXECUTED fixtures | TODO | tests/fixtures/*.py | All | | Add realized_pnl, account_id |
| 9.2 | Update POSITION fixtures | TODO | tests/fixtures/*.py | All | | Add account_id, fix timestamp |
| 9.3 | Update ORDER fixtures | TODO | tests/fixtures/*.py | All | | Add stop_price, order_type |
| 9.4 | Fix all timestamp fixtures | TODO | tests/fixtures/*.py | All | | datetime objects |
| 10.1 | Audit integration test subscriptions | TODO | tests/integration/*.py | All | | Find suite.on uses |
| 10.2 | Replace with realtime.add_callback | TODO | tests/integration/*.py | All | | Correct pattern |
| 11.1 | Create instruments.yaml | TODO | config/instruments.yaml | NEW | | Tick sizes/values |
| 11.2 | Add instruments config loader | TODO | config module | NEW | | Load YAML |
| 11.3 | Integrate with RULE-004/005 | TODO | rules/*.py | TBD | | Use tick values |
| 11.4 | Create events_config.yaml | TODO | config/events_config.yaml | NEW | | Event settings |
| 11.5 | Integrate with EventBridge | TODO | event_bridge.py | __init__ | | Load config |
| 12.1 | Rewrite RULE-008 spec trigger | TODO | RULE-008-no-stop-loss-grace.md | 14-17 | | Fix event logic |
| 12.2 | Add stop-loss detection details | TODO | RULE-008-no-stop-loss-grace.md | TBD | | order_type == 3 |
| 12.3 | Add data field requirements | TODO | RULE-008-no-stop-loss-grace.md | TBD | | stopPrice, etc |
| 12.4 | Fix RULE-004 field names | TODO | RULE-004-daily-unrealized-loss.md | 24 | | avgPrice → average_price |
| 12.5 | Fix RULE-004 event subscriptions | TODO | RULE-004-daily-unrealized-loss.md | 124 | | All 3 + QUOTE_UPDATE |
| 12.6 | Fix RULE-005 field names | TODO | RULE-005-max-unrealized-profit.md | 24 | | avgPrice → average_price |
| 12.7 | Fix RULE-005 event subscriptions | TODO | RULE-005-max-unrealized-profit.md | 125 | | All 3 + QUOTE_UPDATE |
| 12.8 | Add QUOTE_UPDATE to RULE-012 | TODO | RULE-012-trade-management.md | 17, 44-45 | | Explicit reference |

**Phase 3 Completion Criteria**:
- [ ] All test fixtures updated
- [ ] All integration tests use correct patterns
- [ ] Configuration files created
- [ ] Documentation specs corrected
- [ ] Field names standardized
- [ ] Full test suite passes
- [ ] Smoke test passes

---

## Blockers & Issues

| ID | Blocker | Blocks Tasks | Status | Resolution | Owner | Date |
|----|---------|--------------|--------|------------|-------|------|
| | None yet | | | | | |

---

## Daily Progress Log

### Day 1: [DATE] - CRITICAL Changes
**Tasks Planned**: 1.1-4.3 (22 tasks)
**Tasks Completed**:
**Blockers**:
**Notes**:

---

### Day 2: [DATE] - HIGH Changes
**Tasks Planned**: 5.1-7.3 (23 tasks)
**Tasks Completed**:
**Blockers**:
**Notes**:

---

### Day 3: [DATE] - MEDIUM Changes
**Tasks Planned**: 8.1-12.8 (24 tasks)
**Tasks Completed**:
**Blockers**:
**Notes**:

---

## Testing Checkpoints

### After Phase 1
- [ ] Run: `pytest tests/unit/test_event_bridge.py -v`
- [ ] Run: `python run_tests.py` → `[s]` Smoke test
- [ ] Verify: All events have account_id
- [ ] Verify: TRADE_EXECUTED has realized_pnl
- [ ] Verify: POSITION_OPENED fires on new positions
- [ ] Verify: QUOTE_UPDATE events flow through

### After Phase 2
- [ ] Run: `pytest tests/unit/test_rules.py -v`
- [ ] Run: `pytest tests/integration/ -v`
- [ ] Verify: RULE-003 tracks realized P&L correctly
- [ ] Verify: RULE-008 detects stop-loss orders
- [ ] Verify: Quote cache updates on QUOTE_UPDATE
- [ ] Run: `python run_tests.py` → `[g]` Gate test

### After Phase 3
- [ ] Run: `pytest --cov` (full coverage)
- [ ] Run: `python run_tests.py` → `[1]` All tests
- [ ] Run: `python run_tests.py` → `[r]` Soak test
- [ ] Verify: All documentation updated
- [ ] Verify: Field names consistent
- [ ] Verify: Configuration files loaded

---

## Completion Metrics

### Code Changes
- **Files Modified**: 0 / ~15
- **Lines Added**: 0 / ~500
- **Lines Modified**: 0 / ~200
- **Lines Deleted**: 0 / ~50

### Test Changes
- **Test Files Modified**: 0 / ~10
- **New Tests Added**: 0 / ~20
- **Test Assertions Updated**: 0 / ~50

### Documentation Changes
- **Spec Files Updated**: 0 / 4
- **Config Files Created**: 0 / 2

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing tests | HIGH | HIGH | Update fixtures first, then code |
| QUOTE_UPDATE event flood | MEDIUM | MEDIUM | Implement throttling (task 4.3) |
| RULE-008 timer leaks | MEDIUM | HIGH | Proper cleanup in finally block |
| Multi-account data mixing | LOW | CRITICAL | Add account_id validation |
| Timestamp serialization issues | MEDIUM | MEDIUM | Test to_dict() thoroughly |

---

## Sign-Off Checklist

**Before marking Phase 1 complete**:
- [ ] All Phase 1 tasks marked DONE
- [ ] Phase 1 tests pass
- [ ] Smoke test passes
- [ ] No new warnings or errors in logs
- [ ] Code reviewed by: __________
- [ ] Date: __________

**Before marking Phase 2 complete**:
- [ ] All Phase 2 tasks marked DONE
- [ ] Phase 2 tests pass
- [ ] Integration tests pass
- [ ] Gate test passes
- [ ] Code reviewed by: __________
- [ ] Date: __________

**Before marking Phase 3 complete**:
- [ ] All Phase 3 tasks marked DONE
- [ ] Full test suite passes
- [ ] Soak test passes
- [ ] Documentation reviewed
- [ ] Final review by: __________
- [ ] Date: __________

---

## Notes & Lessons Learned

### What Went Well
-

### What Could Be Improved
-

### Key Decisions
-

### Future Improvements
-

---

**Last Updated**: 2025-10-27
**Status**: Ready to start Phase 1
**Next Action**: Begin task 1.1 (Add realized_pnl to TRADE_EXECUTED)

---

## Quick Reference

**Files to Modify** (in order):
1. `src/risk_manager/core/events.py` (add QUOTE_UPDATE)
2. `src/risk_manager/sdk/event_bridge.py` (add fields, POSITION_OPENED, QUOTE handler)
3. `src/risk_manager/rules/max_position.py` (fix subscriptions)
4. `src/risk_manager/rules/daily_loss.py` (use TRADE_EXECUTED)
5. `src/risk_manager/rules/daily_unrealized_loss.py` (NEW)
6. `src/risk_manager/rules/max_unrealized_profit.py` (NEW)
7. `src/risk_manager/rules/stop_loss_check.py` (NEW)
8. `src/risk_manager/core/engine.py` (add quote_cache)
9. `src/risk_manager/state/pnl_tracker.py` (use TRADE_EXECUTED)
10. `src/risk_manager/state/position_tracker.py` (handle all 3 events)
11. `src/risk_manager/state/order_tracker.py` (add stop_price tracking)
12. `tests/fixtures/*.py` (update all)
13. `config/instruments.yaml` (NEW)
14. `config/events_config.yaml` (NEW)
15. `docs/specifications/unified/rules/*.md` (fix specs)

**Commands to Run**:
```bash
# After Phase 1
pytest tests/unit/test_event_bridge.py -v
python run_tests.py  # Select [s] for smoke test

# After Phase 2
pytest tests/unit/test_rules.py -v
pytest tests/integration/ -v
python run_tests.py  # Select [g] for gate test

# After Phase 3
pytest --cov
python run_tests.py  # Select [1] for all tests
python run_tests.py  # Select [r] for soak test
```

---

**End of Progress Tracker**
