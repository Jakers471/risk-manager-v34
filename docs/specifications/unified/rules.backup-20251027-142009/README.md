# Unified Risk Rule Specifications

**Version**: 3.0
**Date**: 2025-10-25
**Status**: Complete - All 13 rules specified with conflict resolutions

---

## Overview

This directory contains the **unified, conflict-free specifications** for all 13 risk rules in the Risk Manager V34 project. These specifications have been created through Wave 3 analysis, applying user's authoritative architectural guidance to resolve all conflicts.

---

## Critical User Guidance Applied

### Resolution Rule #1 (HIGHEST AUTHORITY)
User's authoritative architectural guidance on realized vs unrealized PnL enforcement:

**UNREALIZED PnL Rules** (RULE-004, RULE-005):
- ✅ Trade-by-trade enforcement
- ✅ Close ONLY the specific position that breached the limit
- ✅ Trader can continue trading immediately
- ✅ No lockout, no timer

**REALIZED PnL Rules** (RULE-003, RULE-013):
- ✅ Hard lockout enforcement
- ✅ Close ALL positions account-wide immediately
- ✅ Lockout mode = close ANY new trades immediately until timer reset
- ✅ Timer-based auto-unlock (e.g., 5PM → 5PM next day)
- ✅ Timer is CONFIGURABLE (not hardcoded)
- ❌ NO admin manual unlock - timer only

### Admin Role
- ✅ Admin configures risk rules, timers, schedules (locked from trader via UAC)
- ❌ Admin does NOT manually unlock trading lockouts
- ✅ All lockouts are timer/schedule-based (automatic)

### Reset Schedule
- ✅ MUST be configurable in config files
- ❌ Not hardcoded
- Example: Reset time could be 5PM ET, midnight ET, 6PM CT, etc. (user's choice)

---

## Navigation Table

### All 13 Rules

| Rule ID | Name | Category | Priority | Status | File |
|---------|------|----------|----------|--------|------|
| **RULE-001** | Max Contracts | Trade-by-Trade | Critical | ✅ Implemented | [RULE-001-max-contracts.md](./RULE-001-max-contracts.md) |
| **RULE-002** | Max Contracts Per Instrument | Trade-by-Trade | Critical | ✅ Implemented | [RULE-002-max-contracts-per-instrument.md](./RULE-002-max-contracts-per-instrument.md) |
| **RULE-003** | Daily Realized Loss | Hard Lockout | Critical | ⚠️ Partial (70%) | [RULE-003-daily-realized-loss.md](./RULE-003-daily-realized-loss.md) |
| **RULE-004** | Daily Unrealized Loss | Trade-by-Trade | High | ❌ Missing | [RULE-004-daily-unrealized-loss.md](./RULE-004-daily-unrealized-loss.md) |
| **RULE-005** | Max Unrealized Profit | Trade-by-Trade | Medium | ❌ Missing | [RULE-005-max-unrealized-profit.md](./RULE-005-max-unrealized-profit.md) |
| **RULE-006** | Trade Frequency Limit | Timer/Cooldown | High | ❌ Missing | [RULE-006-trade-frequency-limit.md](./RULE-006-trade-frequency-limit.md) |
| **RULE-007** | Cooldown After Loss | Timer/Cooldown | Medium | ❌ Missing | [RULE-007-cooldown-after-loss.md](./RULE-007-cooldown-after-loss.md) |
| **RULE-008** | No Stop-Loss Grace | Trade-by-Trade | Medium | ❌ Missing | [RULE-008-no-stop-loss-grace.md](./RULE-008-no-stop-loss-grace.md) |
| **RULE-009** | Session Block Outside | Hard Lockout | High | ❌ Missing | [RULE-009-session-block-outside.md](./RULE-009-session-block-outside.md) |
| **RULE-010** | Auth Loss Guard | Hard Lockout | Medium | ❌ Missing | [RULE-010-auth-loss-guard.md](./RULE-010-auth-loss-guard.md) |
| **RULE-011** | Symbol Blocks | Trade-by-Trade | Low | ❌ Missing | [RULE-011-symbol-blocks.md](./RULE-011-symbol-blocks.md) |
| **RULE-012** | Trade Management | Automation | Low | ❌ Missing | [RULE-012-trade-management.md](./RULE-012-trade-management.md) |
| **RULE-013** | Daily Realized Profit | Hard Lockout | Medium | ❌ Missing | [RULE-013-daily-realized-profit.md](./RULE-013-daily-realized-profit.md) |

---

## Category Breakdown

### Category 1: Trade-by-Trade (6 Rules)
**Enforcement**: Close ONLY that position, no lockout

| Rule | Name | Priority | Status |
|------|------|----------|--------|
| RULE-001 | Max Contracts | Critical | ✅ Implemented |
| RULE-002 | Max Contracts Per Instrument | Critical | ✅ Implemented |
| RULE-004 | Daily Unrealized Loss | High | ❌ Missing |
| RULE-005 | Max Unrealized Profit | Medium | ❌ Missing |
| RULE-008 | No Stop-Loss Grace | Medium | ❌ Missing |
| RULE-011 | Symbol Blocks | Low | ❌ Missing |

### Category 2: Timer/Cooldown (2 Rules)
**Enforcement**: Close all + Temporary lockout with countdown

| Rule | Name | Priority | Status |
|------|------|----------|--------|
| RULE-006 | Trade Frequency Limit | High | ❌ Missing |
| RULE-007 | Cooldown After Loss | Medium | ❌ Missing |

### Category 3: Hard Lockout (4 Rules)
**Enforcement**: Close all + Lockout until reset/condition

| Rule | Name | Priority | Status |
|------|------|----------|--------|
| RULE-003 | Daily Realized Loss | Critical | ⚠️ Partial (70%) |
| RULE-013 | Daily Realized Profit | Medium | ❌ Missing |
| RULE-009 | Session Block Outside | High | ❌ Missing |
| RULE-010 | Auth Loss Guard | Medium | ❌ Missing |

### Category 4: Automation (1 Rule)
**Not enforcement - just automation**

| Rule | Name | Priority | Status |
|------|------|----------|--------|
| RULE-012 | Trade Management | Low | ❌ Missing |

---

## Implementation Priority Order

### Phase 1: Critical State Managers (1 week)
**Goal**: Unblock most rules

1. **MOD-002: LockoutManager** (2 days) - Unblocks 5 rules
2. **MOD-003: TimerManager** (2 days) - Unblocks 3 rules
3. **MOD-004: ResetScheduler** (2 days) - Unblocks 3 rules

### Phase 2: High-Priority Rules (1 week)
**Goal**: Prevent account violations

4. **Complete RULE-003** (1 day) - Daily Realized Loss
5. **RULE-009** (3 days) - Session Block Outside
6. **RULE-006** (2 days) - Trade Frequency Limit

### Phase 3: Medium-Priority Rules (1 week)
**Goal**: Complete timer-based and profit protection

7. **RULE-007** (1 day) - Cooldown After Loss
8. **RULE-008** (2 days) - No Stop-Loss Grace
9. **RULE-010** (1 day) - Auth Loss Guard
10. **RULE-013** (1 day) - Daily Realized Profit
11. **RULE-011** (1 day) - Symbol Blocks

### Phase 4: Optional Features (1 week)
**Goal**: Market-data-dependent rules

12. **Market Data Feed** (3 days) - Real-time price updates
13. **RULE-004** (2 days) - Daily Unrealized Loss
14. **RULE-005** (2 days) - Max Unrealized Profit
15. **RULE-012** (2 days) - Trade Management

**Total Time to 100% Complete**: 3-4 weeks

---

## Major Conflicts Resolved

### 1. RULE-004 Enforcement Type ✅ RESOLVED
**Conflict**:
- Original spec (2025-01-17): Hard Lockout, close all
- Updated categories (2025-10-23): Trade-by-Trade, close that position only
- User guidance: Trade-by-trade enforcement

**Resolution**: Trade-by-Trade (per user guidance - Resolution Rule #1)

### 2. RULE-005 Enforcement Type ✅ RESOLVED
**Conflict**:
- Original spec: Hard Lockout, close all
- Updated categories: Trade-by-Trade, close that position only
- User guidance: Trade-by-trade enforcement

**Resolution**: Trade-by-Trade (per user guidance - Resolution Rule #1)

### 3. RULE-013 Missing Dedicated Spec ✅ RESOLVED
**Issue**: Mentioned in categories doc, no dedicated spec file

**Resolution**: Created comprehensive unified spec using RULE-003 as template

### 4. Admin Manual Unlock vs Timer-Based ✅ RESOLVED
**Conflict**:
- Original specs: "admin override" mentioned
- User guidance: "NO admin manual unlock - timer only"

**Resolution**: Timer-based auto-unlock only (per user guidance - Resolution Rule #1)

### 5. Hardcoded Reset Times ✅ RESOLVED
**Conflict**:
- Original specs: Hardcoded "17:00" examples
- User guidance: "MUST be configurable - not hardcoded"

**Resolution**: Configurable reset_time parameter in all relevant rules

---

## Key Insights from Unification

### 1. Shared Infrastructure
**RULE-003 and RULE-013**:
- Share same PnLTracker
- Share same `daily_pnl` SQLite table
- Share same MOD-002 (LockoutManager)
- Share same MOD-004 (ResetScheduler)
- Only differ in trigger condition (>= vs <=)

**RULE-004 and RULE-005**:
- Share same market data feed
- Share same unrealized P&L calculator
- Share same tick value configuration
- Only differ in trigger condition (loss vs profit)

### 2. Cascading Enforcement
**RULE-004 → RULE-003** interaction:
- Unrealized position closes (RULE-004 trade-by-trade)
- Becomes realized P&L
- May trigger RULE-003 hard lockout if daily realized loss limit hit

**RULE-005 → RULE-013** interaction:
- Unrealized position closes (RULE-005 trade-by-trade)
- Becomes realized profit
- May trigger RULE-013 hard lockout if daily realized profit target hit

### 3. Critical Dependencies
**Market Data Feed** (blocks 3 rules):
- RULE-004: Daily Unrealized Loss
- RULE-005: Max Unrealized Profit
- RULE-012: Trade Management

**State Managers** (blocks 8 rules):
- MOD-002 (LockoutManager): Blocks 5 rules
- MOD-003 (TimerManager): Blocks 3 rules
- MOD-004 (ResetScheduler): Blocks 3 rules

---

## Quick Reference

### Enforcement Patterns

**Trade-by-Trade** (6 rules):
```python
# Close ONLY that position
await engine.enforcement.close_position(account_id, contract_id)
# NO lockout, NO cancel orders
# Can trade immediately
```

**Timer/Cooldown** (2 rules):
```python
# Close all positions
await engine.enforcement.close_all_positions(account_id)
# Start countdown timer
await engine.timer_manager.start_timer(account_id, duration, reason)
# Auto-unlock when timer expires
```

**Hard Lockout** (4 rules):
```python
# Close all positions
await engine.enforcement.close_all_positions(account_id)
# Set lockout with timer-based unlock
await engine.lockout_manager.set_lockout(account_id, reason, until=reset_time)
# NO admin manual unlock - timer only
```

---

## Testing Requirements

Each rule needs:
- ✅ Unit tests (rule logic in isolation)
- ✅ Integration tests (with SDK events)
- ✅ E2E tests (full enforcement flow)
- ✅ Edge case tests
- ✅ Conflict resolution validation (user guidance applied correctly)

---

## Success Criteria

### Specification Complete ✅
- ✅ All 13 rules have unified specs
- ✅ All conflicts documented and resolved
- ✅ User guidance applied to all relevant rules
- ✅ Configuration examples provided
- ✅ Implementation status documented

### Next Steps
1. Implement missing state managers (MOD-002, MOD-003, MOD-004)
2. Complete RULE-003 (70% done → 100%)
3. Implement remaining 10 rules following these unified specs
4. Test all conflict resolutions (especially RULE-004, RULE-005)
5. Validate timer-based unlocks (no admin manual unlock)

---

**Maintainer**: Update this README when rule implementation status changes or new conflicts are discovered.

**Last Updated**: 2025-10-25 (Wave 3 Unification Complete)
