# AGENT 2 HANDOFF SUMMARY

**Agent 2 Mission**: Create a mapping of which config fields each rule needs

**Status**: ✅ COMPLETE

**Documents Created**: 3 comprehensive mapping documents

---

## What Was Delivered

### 1. RULE_LOADING_PARAMS.md (Main Document)
**Size**: ~800 lines | **Purpose**: Comprehensive rule-by-rule mapping

**Contains**:
- ✅ All 13 rules analyzed in detail
- ✅ Each rule's `__init__()` signature documented
- ✅ Config source for each parameter (where it comes from in risk_config.yaml)
- ✅ State manager requirements (PnLTracker, LockoutManager, etc.)
- ✅ Tick data requirements (for market-dependent rules)
- ✅ Complete loading code examples for each rule
- ✅ Summary table of all 13 rules with status
- ✅ State manager dependency matrix
- ✅ Tick data requirements summary
- ✅ **4 config issues identified and documented**

**Config Issues Found**:
1. **RULE-006**: Missing `cooldown_on_breach` dict (high priority)
2. **RULE-007**: `loss_threshold` (single) should be `loss_thresholds` (list) - format mismatch
3. **RULE-008**: Field name mismatch - config uses `require_within_seconds`, code expects `grace_period_seconds`
4. **Market config**: `tick_values` and `tick_sizes` not in risk_config.yaml (expected - should come from SDK)

### 2. RULE_LOADING_QUICK_REFERENCE.md (Fast Lookup)
**Size**: ~400 lines | **Purpose**: Quick copy-paste loading code for Agent 1

**Contains**:
- ✅ Instant lookup for each rule's loading code
- ✅ What state managers each rule needs
- ✅ Dependency matrix (which rules need what)
- ✅ Load order requirements
- ✅ Config issues checklist
- ✅ Pseudocode template for `_initialize_rules()`

**Perfect for**: Agent 1 to quickly see exactly what parameters to pass to each rule

### 3. RULE_LOADING_VALIDATION.md (Testing Guide)
**Size**: ~600 lines | **Purpose**: Validation scripts and test templates

**Contains**:
- ✅ Pre-loading validation checks (state managers, market config)
- ✅ Individual test functions for each rule
- ✅ Batch validation script to test all 13 rules at once
- ✅ API contract verification template
- ✅ Config workaround implementations
- ✅ Smoke test after loading
- ✅ Complete test checklist

**Perfect for**: Agent 1 to validate loading works correctly before integration

---

## Key Findings

### Rule Categories by Complexity

**Simple** (No state managers, no tick data):
- RULE-001: Max Contracts
- RULE-002: Max Contracts Per Instrument
- RULE-010: Auth Loss Guard
- RULE-011: Symbol Blocks

**Moderate** (Needs state managers):
- RULE-003: Daily Realized Loss (pnl_tracker, lockout_manager)
- RULE-009: Session Block Outside (lockout_manager)
- RULE-013: Daily Realized Profit (pnl_tracker, lockout_manager)

**Advanced** (Needs state managers + timer):
- RULE-006: Trade Frequency Limit (timer_manager, db)
- RULE-007: Cooldown After Loss (timer_manager, pnl_tracker, lockout_manager)
- RULE-008: No Stop-Loss Grace (timer_manager)

**Market-Dependent** (Needs tick data):
- RULE-004: Daily Unrealized Loss (tick_values, tick_sizes)
- RULE-005: Max Unrealized Profit (tick_values, tick_sizes)
- RULE-012: Trade Management (tick_values, tick_sizes)

### State Manager Requirements

**Must Initialize Before Loading Rules**:
1. `pnl_tracker` (PnLTracker) - Used by 3 rules
2. `lockout_manager` (LockoutManager) - Used by 4 rules
3. `timer_manager` (TimerManager) - Used by 3 rules
4. `database` (DB) - Used by 1 rule (RULE-006)

### Tick Data Requirements

**Must Load Before Creating Tick-Data Rules**:
- `tick_values`: Dict[str, float] - {"ES": 50.0, "MNQ": 5.0, "NQ": 20.0}
- `tick_sizes`: Dict[str, float] - {"ES": 0.25, "MNQ": 0.25, "NQ": 0.25}

**Source**: Should come from Project-X SDK or market configuration (NOT risk_config.yaml)

---

## Config Issues to Fix

### High Priority

1. **RULE-006: Add cooldown_on_breach**
   ```yaml
   # Add to config/risk_config.yaml:
   trade_frequency_limit:
     enabled: true
     limits:
       per_minute: 3
       per_hour: 10
       per_session: 50
     cooldown_on_breach:              # NEW - required
       per_minute_breach: 60
       per_hour_breach: 1800
       per_session_breach: 3600
   ```

2. **RULE-007: Fix loss_thresholds format**
   ```yaml
   # Change from:
   cooldown_after_loss:
     loss_threshold: -100.0

   # To:
   cooldown_after_loss:
     loss_thresholds:
       - loss_amount: -100.0
         cooldown_duration: 300
       - loss_amount: -200.0
         cooldown_duration: 900
   ```

3. **RULE-008: Clarify field naming**
   - Config has: `require_within_seconds: 60`
   - Code expects: `grace_period_seconds`
   - Either change config or add mapping in loader

---

## What Agent 1 Should Do Next

### Phase 1: Read the Mapping Documents
1. Read RULE_LOADING_PARAMS.md (full reference)
2. Read RULE_LOADING_QUICK_REFERENCE.md (fast lookup)
3. Read RULE_LOADING_VALIDATION.md (testing guide)

### Phase 2: Implement Rule Loading
1. Fix config issues in risk_config.yaml (RULE-006, RULE-007, RULE-008)
2. Implement `_initialize_rules()` in manager.py
3. Follow the loading code examples from RULE_LOADING_QUICK_REFERENCE.md
4. Handle config workarounds for known issues

### Phase 3: Test Rule Loading
1. Run pre-loading validation checks (state managers, market config)
2. Use validation scripts from RULE_LOADING_VALIDATION.md
3. Test each rule individually, then all together
4. Run smoke test: `python run_tests.py [s]`

### Phase 4: Integration
1. Integrate with engine initialization
2. Ensure rules are accessible via `engine.rules` list
3. Update PROJECT_STATUS.md with completion status
4. Write tests in tests/unit/test_rule_loading.py

---

## File Locations

**Maps and Documentation** (in project root):
- `RULE_LOADING_PARAMS.md` - Main reference (800 lines)
- `RULE_LOADING_QUICK_REFERENCE.md` - Fast lookup (400 lines)
- `RULE_LOADING_VALIDATION.md` - Testing guide (600 lines)
- `AGENT_2_SUMMARY.md` - This handoff document

**Source Files**:
- `config/risk_config.yaml` - Configuration (currently missing 3 fields)
- `src/risk_manager/rules/*.py` - All 13 rule implementations
- `src/risk_manager/core/manager.py` - Where `_initialize_rules()` goes

---

## Quick Stats

**Analysis Coverage**:
- ✅ All 13 rules analyzed
- ✅ All 13 rule files read
- ✅ Config parameters extracted for all
- ✅ State manager requirements documented
- ✅ Tick data requirements documented
- ✅ Loading examples provided for each rule
- ✅ 4 config issues identified
- ✅ Complete validation scripts provided

**Rules Status**:
- ✅ Ready: 10 rules (RULE-001, 002, 003, 004, 005, 009, 010, 011, 012, 013)
- ⚠️ Partial: 3 rules (RULE-006, 007, 008) - config issues need fixing

**Test Coverage**:
- ✅ Individual rule validation templates provided
- ✅ Batch validation script provided
- ✅ Pre-loading checks provided
- ✅ Smoke test integration documented

---

## Validation Passed

This mapping was created by:
1. ✅ Reading all 13 rule source files
2. ✅ Extracting exact __init__() signatures
3. ✅ Matching to config/risk_config.yaml fields
4. ✅ Identifying state manager requirements
5. ✅ Documenting tick data needs
6. ✅ Creating loading examples
7. ✅ Providing complete test templates
8. ✅ Identifying config issues

**Result**: Agent 1 has everything needed to implement `_initialize_rules()`

---

## Next Steps

1. **Agent 1** - Read the 3 mapping documents
2. **Agent 1** - Fix config issues in risk_config.yaml
3. **Agent 1** - Implement _initialize_rules() using QUICK_REFERENCE as template
4. **Agent 1** - Run validation tests from VALIDATION document
5. **Both** - Run full test suite to ensure rules work end-to-end

---

## Delivery Checklist

- [x] Analyzed all 13 rule files
- [x] Created comprehensive mapping document (RULE_LOADING_PARAMS.md)
- [x] Created quick reference for Agent 1 (RULE_LOADING_QUICK_REFERENCE.md)
- [x] Created validation guide (RULE_LOADING_VALIDATION.md)
- [x] Identified 4 config issues with fixes
- [x] Provided loading code examples for each rule
- [x] Documented state manager requirements
- [x] Documented tick data requirements
- [x] Created test templates and validation scripts
- [x] This handoff document

---

## Questions for Agent 1?

Refer to:
- **"What does RULE-X need?"** → RULE_LOADING_QUICK_REFERENCE.md
- **"How do I load RULE-X?"** → RULE_LOADING_PARAMS.md (specific rule section)
- **"How do I test RULE-X?"** → RULE_LOADING_VALIDATION.md
- **"What config issues exist?"** → RULE_LOADING_PARAMS.md (Config Issues section)
- **"What's the complete loading code?"** → RULE_LOADING_QUICK_REFERENCE.md (Pseudocode Template)

---

**Created By**: Agent 2 (Rule Parameter Validator)
**Date**: 2025-10-29
**Status**: Ready for Agent 1
**Next Phase**: Rule Loading Implementation (Agent 1)

---

## One Last Thing

When Agent 1 finishes implementing `_initialize_rules()`, the 4 config issues will likely need to be fixed. Here's where to document them:

1. **RULE-006 Issue**: Missing `cooldown_on_breach` in config
   - Fix: Add to config/risk_config.yaml
   - Alternative: Hardcode defaults in rule loader

2. **RULE-007 Issue**: `loss_threshold` should be list of tiers
   - Fix: Update config/risk_config.yaml
   - Alternative: Convert single value to list in rule loader

3. **RULE-008 Issue**: Field name mismatch
   - Fix: Update config/risk_config.yaml to use `grace_period_seconds`
   - Alternative: Map field name in rule loader

4. **Tick Data**: Not in risk_config.yaml
   - Expected: Should come from Project-X SDK market config
   - Alternative: Create separate market_config.yaml file

**Recommendation**: Fix the config issues NOW in risk_config.yaml rather than adding workarounds in the loader.

---

**Ready to hand off to Agent 1!**
