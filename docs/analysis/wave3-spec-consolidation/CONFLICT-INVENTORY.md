# Wave 3: Complete Conflict Inventory

**Document ID:** CONFLICT-INVENTORY
**Created:** 2025-10-25
**Purpose:** Comprehensive list of all specification conflicts across 88 features
**Status:** Complete

---

## Executive Summary

### Conflict Statistics
- **Total Conflicts:** 5 major conflicts
- **Critical:** 1 (Admin unlock model)
- **High:** 2 (RULE-004/005 enforcement, RULE-013 missing spec)
- **Medium:** 1 (Architecture v1 vs v2)
- **Low:** 1 (API vs SDK approach)
- **Resolution Status:** All resolvable with clear priority rules

### Impact Assessment
- **Features Affected:** 7 of 88 (8%)
- **Rules Affected:** 5 of 13 (38%)
- **Blockers:** 0 (no unresolvable conflicts)
- **Implementation Impact:** Minor (specs update only, no code changes needed)

---

## Conflict Categories

### Category 1: Risk Rule Enforcement Conflicts

#### CONFLICT-001: RULE-004 Enforcement Type

**Severity:** HIGH
**Domain:** Risk Rules
**Features Affected:** 1 (RULE-004)

**Conflicting Sources:**

| Source | Location | Date | Enforcement Type | Action | Lockout |
|--------|----------|------|------------------|--------|---------|
| **Primary Spec** | `/docs/PROJECT_DOCS/rules/04_daily_unrealized_loss.md` | 2025-01-17 | Hard Lockout (Cat 3) | Close ALL | Yes (until 5 PM) |
| **Categories Doc** | `/docs/current/RULE_CATEGORIES.md` lines 42-66 | 2025-10-23 | Trade-by-Trade (Cat 1) | Close ONLY losing position | None |

**Evidence of Conflict:**
```markdown
# From Primary Spec (2025-01-17):
**Enforcement**: close_all_and_lockout
**Lockout**: Until reset_time (daily at 5:00 PM)
**Can Trade Again**: At reset time

# From Categories Doc (2025-10-23):
**Critical Changes**:
- RULE-004, 005, 008 are trade-by-trade (NOT close all)
- Close that losing position only
- NO lockout
```

**Resolution:** **Use Categories Doc (Trade-by-Trade)**

**Resolution Rules Applied:**
1. **Rule #3:** Newest Specification (2025-10-23 > 2025-01-17)
2. **Rule #1:** User Guidance (autonomous enforcement, no admin unlock needed)

**Rationale:**
- Categories doc is newer (8 months after primary spec)
- Explicitly states "corrected enforcement categories"
- Trade-by-Trade makes more sense: close losing position only, keep winners open
- More granular risk management
- Aligns with autonomous enforcement model

**Impact:**
- Primary spec needs update to reflect Trade-by-Trade
- Implementation: Close specific losing position, not all positions
- No lockout enforcement needed for RULE-004

**Action Items:**
1. Update `04_daily_unrealized_loss.md` to reflect Trade-by-Trade enforcement
2. Create unified spec documenting this resolution
3. Add conflict resolution section explaining why Categories doc won

---

#### CONFLICT-002: RULE-005 Enforcement Type

**Severity:** HIGH
**Domain:** Risk Rules
**Features Affected:** 1 (RULE-005)

**Conflicting Sources:**

| Source | Location | Date | Enforcement Type | Action | Lockout |
|--------|----------|------|------------------|--------|---------|
| **Primary Spec** | `/docs/PROJECT_DOCS/rules/05_max_unrealized_profit.md` | 2025-01-17 | Hard Lockout | Close ALL (lock in profit) | Yes (until 5 PM) |
| **Categories Doc** | `/docs/current/RULE_CATEGORIES.md` lines 42-66 | 2025-10-23 | Trade-by-Trade | Close ONLY winning position | None |

**Evidence of Conflict:**
```markdown
# From Primary Spec:
**Use Case**: "Hit daily target, stop trading completely"
**Enforcement**: Close all positions, lock until reset
**Philosophy**: "Take the win and walk away"

# From Categories Doc:
**Enforcement**: Trade-by-Trade (Category 1)
**Action**: Close that winning position only (take profit)
**Philosophy**: "Take profit and keep trading"
```

**Resolution:** **Make Configurable (Both Modes Valid)**

**Resolution Rules Applied:**
1. **Rule #4:** Most Detailed Specification (include both modes)
2. **Rule #1:** User Guidance (support multiple autonomous modes)

**Rationale:**
- Both approaches have valid use cases:
  - **Trade-by-Trade:** More flexible, take profit and continue
  - **Hard Lockout:** More conservative, "take the win and walk away"
- Different traders have different strategies
- Configuration provides flexibility without requiring spec choice
- Both modes are autonomous (no admin unlock)

**Impact:**
- Primary spec needs update to include both modes
- Implementation: Support both `trade_by_trade` and `hard_lockout` modes
- Add configuration parameter: `enforcement_mode`

**Unified Config Example:**
```yaml
max_unrealized_profit:
  enabled: true
  target: 1000.0
  enforcement_mode: "trade_by_trade"  # or "hard_lockout"
  lockout_until_reset: false  # true if hard_lockout mode
  reset_time: "17:00"  # Only if lockout_until_reset=true
```

**Action Items:**
1. Update `05_max_unrealized_profit.md` to document both modes
2. Add `enforcement_mode` parameter to spec
3. Create unified spec with both approaches
4. Document default: Trade-by-Trade (more flexible)

---

#### CONFLICT-003: RULE-013 Missing Dedicated Specification

**Severity:** HIGH
**Domain:** Risk Rules
**Features Affected:** 1 (RULE-013)

**Problem:** No dedicated specification file exists for RULE-013

**Evidence:**

| What Exists | What's Missing |
|-------------|----------------|
| ✅ Mentioned in `RULE_CATEGORIES.md` (lines 239-271) | ❌ No `/docs/PROJECT_DOCS/rules/13_daily_realized_profit.md` file |
| ✅ Listed in enforcement matrix (lines 219-236) | ❌ No detailed implementation guide |
| ✅ Summary in inventory docs | ❌ No test scenarios |
|  | ❌ No API requirements |
|  | ❌ No edge cases |
|  | ❌ No SQLite schema |

**Comparison to Other Rules:**
- **RULE-001 through RULE-012:** All have dedicated 150-300 line spec files
- **RULE-013:** Only 32 lines in categories doc (summary level)
- **Inconsistency:** All 12 other rules have detailed specs

**Resolution:** **Create Full Specification Using RULE-003 as Template**

**Resolution Rules Applied:**
1. **Consistency:** All rules should have same detail level
2. **Implementation Readiness:** Teams need detailed specs

**Rationale:**
- RULE-013 is nearly identical to RULE-003 (opposite direction)
- RULE-003 spec is comprehensive (228 lines) - perfect template
- Same enforcement type (Hard Lockout)
- Same state tracking (daily realized P&L)
- Same reset logic (daily at 5 PM)
- Only difference: Positive threshold instead of negative

**Template Source:** `/docs/PROJECT_DOCS/rules/03_daily_realized_loss.md`

**Spec Structure to Copy:**
1. Purpose and trigger
2. Enforcement actions sequence
3. SQLite schema (`daily_pnl` table - shared with RULE-003)
4. State tracking logic
5. Reset time calculation
6. Lockout behavior
7. Auto-unlock mechanism
8. Test scenarios
9. API requirements
10. Edge cases

**Differences from RULE-003:**
```python
# RULE-003: Daily Realized LOSS
if daily_realized_pnl <= -500:  # Hit LOSS limit
    BREACH

# RULE-013: Daily Realized PROFIT
if daily_realized_pnl >= +1000:  # Hit PROFIT target
    BREACH
```

**Impact:**
- New 200+ line specification file needed
- Same SQLite schema as RULE-003 (reuse `daily_pnl` table)
- Same PnL tracker implementation (already exists)
- Same enforcement modules (MOD-001, MOD-002, MOD-004)

**Action Items:**
1. Create `/docs/specifications/unified/rules/13-daily-realized-profit.md`
2. Copy structure from RULE-003
3. Modify trigger condition (positive threshold)
4. Update use case: "Hit profit target, stop for day"
5. Keep all other logic same (lockout, reset, state tracking)

---

### Category 2: Architectural Conflicts

#### CONFLICT-004: Architecture v1 vs v2

**Severity:** MEDIUM
**Domain:** Architecture
**Features Affected:** System-wide (all components)

**Conflicting Sources:**

| Version | Location | Date | Key Characteristics |
|---------|----------|------|---------------------|
| **v1** | `/docs/PROJECT_DOCS/architecture/ARCHITECTURE_V1.md` | 2025-01-17 (earlier) | Initial planning, basic structure |
| **v2** | `/docs/PROJECT_DOCS/architecture/ARCHITECTURE_V2.md` | 2025-01-17 (later) | Refined, modular, MOD-001 to MOD-004 |

**Evidence of Evolution (Not Contradiction):**

**v1 Characteristics:**
- Direct TopstepX API integration (no modules)
- `priority_handler.py` for rule prioritization
- Basic state management
- Simpler structure

**v2 Characteristics:**
- Four core modules (MOD-001 to MOD-004)
- `event_router.py` (cleaner than priority_handler)
- Enhanced state management (lockout, timer, reset managers)
- Production-ready modular design
- Clear separation of concerns

**What Changed:**

| Aspect | v1 | v2 | Change Type |
|--------|----|----|-------------|
| Enforcement | Scattered in rules | Centralized MOD-001 | **Refinement** |
| Lockout State | In state_manager | Dedicated MOD-002 | **Refinement** |
| Timers | Basic timer_manager | Formalized MOD-003 | **Refinement** |
| Event Routing | In risk_engine | Dedicated event_router | **Refinement** |

**Resolution:** **Use v2 (Evolved Production-Ready Design)**

**Resolution Rules Applied:**
1. **Rule #2:** Actual Implementation (v2 is what's being built)
2. **Rule #4:** Most Detailed Specification (v2 is more comprehensive)

**Rationale:**
- v2 is not a replacement of v1, it's an **evolution**
- All v1→v2 changes are **refinements**, not contradictions
- v2 has proven modular design
- v2 is production-ready
- v2 has clear module boundaries (easier to implement/test)

**Impact:**
- Use v2 architecture in all unified specs
- Document v1 as historical context (shows design evolution)
- No code impact (v2 is already being implemented)

**Action Items:**
1. Use v2 module definitions (MOD-001 to MOD-004) in unified specs
2. Document v1 in "Version History" section
3. Note: Both specs written **before SDK existed** (important context)

---

### Category 3: Integration Approach Conflicts

#### CONFLICT-005: Manual API vs SDK Integration

**Severity:** LOW (Not a real conflict, just outdated context)
**Domain:** SDK Integration
**Features Affected:** All integration code

**Context:**

| When Written | What Existed | What Specs Describe |
|--------------|--------------|---------------------|
| 2025-01-17 | Only raw TopstepX Gateway API | Manual WebSocket handling, manual position management |
| 2025-10-25 (now) | Project-X-Py SDK v3.5.9 available | SDK handles WebSocket, positions, orders, auth |

**Original Specs Describe:**
- Manual SignalR connection using `signalrcore` library
- Manual authentication with JWT token management
- Manual position closing (call REST API directly)
- Manual order management
- Manual state tracking
- **~1100 lines of API client code**

**Current Implementation Uses:**
- Project-X-Py SDK handles all heavy lifting
- SDK auto-authenticates
- SDK auto-connects WebSocket
- SDK provides position/order management
- SDK handles reconnection
- **~80 lines of wrapper code (93% reduction)**

**Resolution:** **Use SDK-First Approach (Already Implemented)**

**Resolution Rules Applied:**
1. **Rule #2:** Actual Implementation (SDK is already integrated)
2. **Rule #6:** SDK Integration (proven 93% code reduction)

**Rationale:**
- This is not a spec conflict, just **outdated context**
- Specs were written **before SDK existed**
- SDK-first approach is superior (93% code reduction)
- SDK provides more reliability (auto-reconnection, error handling)
- Implementation already uses SDK successfully

**Impact:**
- Update integration specs to reflect SDK-first approach
- Keep original API specs for historical context (understanding Gateway API)
- Document evolution: Manual → SDK-first

**Action Items:**
1. Update `SDK_INTEGRATION_GUIDE.md` (already current)
2. Note in unified specs: "Original specs pre-date SDK availability"
3. Document current EventBridge pattern (SDK events → Risk events)

---

## Category 4: Enforcement Model Conflicts

#### CONFLICT-006: Admin Unlock Mentions (CRITICAL)

**Severity:** CRITICAL
**Domain:** Risk Rules (Enforcement Model)
**Features Affected:** 4 rules (RULE-003, 009, 010, 013)

**User Architectural Guidance (AUTHORITATIVE):**
> **Admin does NOT manually unlock accounts for trading**
> **Every rule auto-enforces via: reset schedules, trade-by-trade, time-based**
> **System is autonomous once configured**
> **NO manual admin intervention for trading lockouts**

**Conflicting Spec Mentions:**

| Rule | Spec Location | What It Says | WRONG |
|------|---------------|--------------|-------|
| RULE-003 | `03_daily_realized_loss.md` | "Lockout until reset or **admin override**" | ❌ |
| RULE-009 | `09_session_block_outside.md` | "Lockout until session start or **admin override**" | ❌ |
| RULE-010 | `10_auth_loss_guard.md` | "Lockout until API clears or **admin override**" | ❌ |
| RULE-013 | Categories doc | "Lockout until reset or **admin override**" | ❌ |

**Resolution:** **Remove All Admin Unlock Mentions, Use Autonomous Mechanisms**

**Resolution Rules Applied:**
1. **Rule #1:** User Guidance (HIGHEST priority - overrides all specs)

**Corrected Enforcement:**

| Rule | OLD (Spec) | NEW (User Guidance) |
|------|------------|---------------------|
| RULE-003 | "Lockout until reset **or admin override**" | "Lockout until **daily reset at 5:00 PM** (automatic)" |
| RULE-009 | "Lockout until session start **or admin override**" | "Lockout until **session start** (automatic via scheduler)" |
| RULE-010 | "Lockout until API clears **or admin override**" | "Lockout until **API sends `canTrade: true`** (automatic)" |
| RULE-013 | "Lockout until reset **or admin override**" | "Lockout until **daily reset at 5:00 PM** (automatic)" |

**Autonomous Unlock Mechanisms:**
- **RULE-003:** MOD-004 (ResetScheduler) triggers daily reset at 5:00 PM → clears lockout
- **RULE-009:** MOD-004 (ResetScheduler) detects session start time → clears lockout
- **RULE-010:** SDK receives `canTrade: true` event → clears lockout
- **RULE-013:** MOD-004 (ResetScheduler) triggers daily reset at 5:00 PM → clears lockout

**Impact:**
- All 4 rule specs need updates to remove "admin override" mentions
- Implementation uses autonomous mechanisms only
- Admin can **configure** rules, but **cannot override** runtime enforcement
- System is fully autonomous once configured

**Action Items:**
1. Update all 4 rule specs to remove "admin override"
2. Document autonomous unlock mechanisms only
3. Clarify admin role: **Configure rules, NOT override enforcement**

---

## Non-Conflicts (Clarifications)

### NC-001: Varying Spec Detail Levels

**Observation:** Some specs are 40 lines, others are 300 lines

**Not a Conflict Because:**
- Different rules have different complexity
- Simpler rules (e.g., SymbolBlocks) need less explanation
- Complex rules (e.g., SessionBlockOutside) need more detail
- This is **natural variation**, not a conflict

**Action:** Expand brief specs in unified version to match detail level of comprehensive specs

---

### NC-002: Implementation Gap vs Spec Completeness

**Observation:** 10 of 13 rules have no implementation (77% gap)

**Not a Conflict Because:**
- Specs are complete, implementation is in progress
- This is a **work-to-do gap**, not a spec conflict
- Wave 2 Gap Analysis already documented this

**Action:** No spec changes needed, just implementation work

---

### NC-003: Brief Specs (RULE-004, 005, 010, 011)

**Observation:** 4 rules have brief specs (40-50 lines) vs comprehensive specs (200-300 lines)

**Not a Conflict Because:**
- Brief specs are still **correct**, just less detailed
- Categories doc and other sources fill in details
- This is **completeness gap**, not a conflict

**Action:** Expand to match comprehensive spec detail level in unified version

---

## Conflict Resolution Matrix

| Conflict ID | Severity | Resolution Rule | Winner | Action |
|-------------|----------|-----------------|--------|--------|
| CONFLICT-001 | HIGH | #3 Newest Spec, #1 User Guidance | Categories Doc (Trade-by-Trade) | Update primary spec |
| CONFLICT-002 | HIGH | #4 Most Detailed, #1 User Guidance | Both modes (configurable) | Add config parameter |
| CONFLICT-003 | HIGH | Consistency + Implementation Readiness | Create new spec | Use RULE-003 template |
| CONFLICT-004 | MEDIUM | #2 Implementation, #4 Most Detailed | v2 Architecture | Use v2 in all specs |
| CONFLICT-005 | LOW | #2 Implementation, #6 SDK Integration | SDK-first approach | Update integration docs |
| CONFLICT-006 | CRITICAL | #1 User Guidance (HIGHEST) | Remove admin unlock | Update 4 rule specs |

---

## Impact Summary

### Specs Requiring Updates
1. `04_daily_unrealized_loss.md` - Change to Trade-by-Trade
2. `05_max_unrealized_profit.md` - Add configurable modes
3. `13_daily_realized_profit.md` - **CREATE NEW** using RULE-003 template
4. `03_daily_realized_loss.md` - Remove "admin override"
5. `09_session_block_outside.md` - Remove "admin override"
6. `10_auth_loss_guard.md` - Remove "admin override"
7. RULE-013 (categories doc) - Remove "admin override"

**Total:** 7 specs affected out of 88 features (8% impact)

### Implementation Impact
- **No code changes needed** (conflicts are spec-level only)
- **Configuration changes:** RULE-005 needs `enforcement_mode` parameter
- **New spec needed:** RULE-013 dedicated file

### Timeline Impact
- **No delay** to implementation timeline
- **Spec updates:** 1-2 days in parallel with Wave 3 researchers

---

## Conclusion

**All 5 major conflicts are resolvable** using clear priority rules and user guidance.

**Resolution Confidence:** HIGH
- User guidance provides authoritative override for critical conflict
- Clear priority rules (6-tier system) for all other conflicts
- No architectural blockers
- No implementation blockers

**Next Steps:**
1. Researchers apply resolution rules when creating unified specs
2. Coordinator validates conflict resolutions in Phase 4 review
3. All unified specs include conflict resolution section

---

**Conflict Inventory Complete**

**Date:** 2025-10-25
**Total Conflicts:** 5 major
**Resolvable:** 5 (100%)
**Unresolvable:** 0 (0%)
**Confidence:** HIGH
