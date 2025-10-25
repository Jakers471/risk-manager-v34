# Wave 3: Specification Consolidation & Unification - Coordinator Report

**Document ID:** 00-WAVE3-COORDINATOR-REPORT
**Created:** 2025-10-25
**Coordinator:** Wave 3 Coordinator - Spec Unification Specialist
**Mission:** Create unified, conflict-free specifications for all 88 features
**Status:** Planning Complete - Ready for Delegation

---

## Executive Summary

### Mission Status
✅ **Phase 1-2 Complete:** Discovery, Conflict Analysis, and Resolution Strategy defined
🔄 **Phase 3 Ready:** Delegation plan created for 6 specialized researchers
⏳ **Timeline:** 2-3 weeks for complete spec unification

### Critical Findings

1. **5 Major Conflicts Identified** requiring resolution
2. **88 Total Features** across 8 domains need unified specs
3. **User Architectural Guidance** provided as authoritative override
4. **Clear Resolution Rules** established (6-tier priority system)
5. **No Architectural Blockers** - conflicts are resolvable

### Key Conflicts Summary

| Conflict | Domain | Severity | Resolution Approach |
|----------|--------|----------|---------------------|
| RULE-004/005 Enforcement Type | Risk Rules | High | **Use Categories Doc** (more recent, explicit correction) |
| RULE-013 Missing Spec | Risk Rules | High | **Create using RULE-003 template** |
| Admin Unlock Mentions | Risk Rules | Critical | **Apply User Guidance** (use reset schedules, NOT manual unlock) |
| Architecture v1 vs v2 | Architecture | Medium | **Use v2** (evolved, production-ready) |
| API vs SDK Approach | SDK Integration | Low | **Use SDK-first** (93% code reduction proven) |

### User Architectural Guidance (AUTHORITATIVE)

**Admin Role:**
- ✅ Admin configures risk settings
- ✅ Admin locks configurations (trader cannot modify)
- ❌ Admin does NOT manually unlock accounts for trading

**Enforcement Model:**
- ✅ Every rule auto-enforces via: reset schedules, trade-by-trade, time-based
- ✅ System is autonomous once configured
- ✅ Rules use: daily reset (midnight ET), session-based, trade-by-trade logic
- ❌ NO manual admin intervention for trading lockouts

**This means:**
- RULE-004, RULE-005 conflicts: **Use reset schedules**, NOT admin unlock
- Any spec mentioning "admin unlock for trading" is **WRONG**
- **Use this as resolution authority**

---

## Phase 1-2: Discovery & Analysis (COMPLETE)

### Conflicts Inventory

#### Conflict 1: RULE-004 Enforcement Type

**Source A - Primary Spec** (`04_daily_unrealized_loss.md`, 2025-01-17):
- Enforcement Type: Hard Lockout (Category 3)
- Action: Close ALL positions
- Lockout: Yes, until reset time
- Trader Can Trade Again: At reset time (5 PM)

**Source B - Categories Doc** (`RULE_CATEGORIES.md`, 2025-10-23):
- Enforcement Type: Trade-by-Trade (Category 1)
- Action: Close ONLY that losing position
- Lockout: NO lockout
- Trader Can Trade Again: Immediately

**Conflict Note in Categories Doc:**
```
**Critical Changes**:
- RULE-004, 005, 008 are trade-by-trade (NOT close all)
- Corrected enforcement categories
```

**Resolution:** **Use Categories Doc (Source B)**

**Rationale:**
1. **Resolution Rule #3:** Newest Specification (Categories Doc is 2025-10-23, Primary is 2025-01-17)
2. **Explicit Correction:** Categories doc states "corrected enforcement categories"
3. **Better Design:** Trade-by-Trade makes more sense (close losing position only, keep winners open)
4. **Aligns with Position-Level Risk Management:** More granular control
5. **User Guidance:** Auto-enforcement via trade-by-trade logic (no admin unlock)

**Action Required:**
- Update `04_daily_unrealized_loss.md` to reflect Trade-by-Trade enforcement
- Create unified spec in Wave 3 output

---

#### Conflict 2: RULE-005 Enforcement Type

**Source A - Primary Spec** (`05_max_unrealized_profit.md`, 2025-01-17):
- Enforcement Type: Hard Lockout
- Action: Close ALL positions (lock in profit)
- Lockout: Yes, until reset time
- Use Case: "Hit daily target, stop trading completely"

**Source B - Categories Doc** (`RULE_CATEGORIES.md`, 2025-10-23):
- Enforcement Type: Trade-by-Trade (Category 1)
- Action: Close ONLY that winning position (take profit)
- Lockout: NO lockout
- Use Case: "Take profit on winner, keep trading"

**Resolution:** **Make Configurable (Both Valid)**

**Rationale:**
1. **Both Approaches Valid:**
   - Trade-by-Trade: More flexible, take profit and continue
   - Hard Lockout: More conservative, "take the win and walk away"
2. **User Preference:** Different traders have different strategies
3. **Resolution Rule #4:** Most Detailed Specification (include both modes)
4. **User Guidance:** Support both autonomous modes (reset schedule OR trade-by-trade)

**Action Required:**
- Create unified spec with configurable `enforcement_mode` parameter
- Default: Trade-by-Trade (more flexible)
- Option: Hard Lockout (more conservative)

**Example Unified Config:**
```yaml
max_unrealized_profit:
  enabled: true
  target: 1000.0
  enforcement_mode: "trade_by_trade"  # or "hard_lockout"
  lockout_until_reset: false  # true if hard_lockout mode
  reset_time: "17:00"  # Only if lockout_until_reset=true
```

---

#### Conflict 3: RULE-013 Missing Dedicated Spec

**Found In:**
- `RULE_CATEGORIES.md` (lines 239-271) - Good summary
- Enforcement Matrix (lines 219-236) - Configuration details

**Missing:**
- No `13_daily_realized_profit.md` file in `/docs/PROJECT_DOCS/rules/`
- No detailed implementation guide
- No test scenarios
- No API requirements
- No edge cases documented

**Resolution:** **Create Full Specification**

**Rationale:**
1. **Consistency:** All 12 other rules have dedicated spec files
2. **Implementation Readiness:** Teams need detailed specs to implement
3. **Template Available:** RULE-003 (DailyRealizedLoss) is nearly identical (opposite direction)
4. **User Guidance:** Needs autonomous reset schedule enforcement

**Action Required:**
- Create `13_daily_realized_profit.md` matching RULE-003 detail level
- Include: trigger logic, enforcement actions, SQLite schema, test scenarios, API requirements
- Use RULE-003 as template (similar logic, positive threshold instead of negative)

---

#### Conflict 4: Admin Unlock Mentions in Specs

**Problem:** Several specs mention "admin manually unlocks account"

**Found In:**
- RULE-003: "Lockout until reset or **admin override**"
- RULE-009: "Lockout until session start or **admin override**"
- RULE-010: "Lockout until API clears or **admin override**"
- RULE-013: "Lockout until reset or **admin override**"

**User Guidance Override:**
> **Admin does NOT manually unlock accounts for trading**
> **Every rule auto-enforces via: reset schedules, trade-by-trade, time-based**
> **NO manual admin intervention for trading lockouts**

**Resolution:** **Apply User Guidance (Highest Priority)**

**Rationale:**
1. **Resolution Rule #1:** User Guidance is AUTHORITATIVE (overrides all specs)
2. **Architectural Decision:** System is autonomous once configured
3. **Correct Enforcement:** Use reset schedules, session-based, or trade-by-trade logic
4. **No Manual Intervention:** Admin configures, system auto-enforces

**Corrected Enforcement:**
- ✅ RULE-003: Lockout until **daily reset at 5 PM** (automatic)
- ✅ RULE-009: Lockout until **session start** (automatic via scheduler)
- ✅ RULE-010: Lockout until **API sends `canTrade: true`** (automatic)
- ✅ RULE-013: Lockout until **daily reset at 5 PM** (automatic)
- ❌ ~~Admin manually unlocks~~ (remove from all specs)

**Action Required:**
- Update all 4 rule specs to remove "admin override" mentions
- Document autonomous unlock mechanisms only
- Clarify that admin can configure rules, but NOT override runtime enforcement

---

#### Conflict 5: Architecture v1 vs v2

**v1 (Initial Planning, 2025-01-17):**
- Basic architecture outline
- No MOD-001 to MOD-004 modules
- Manual API integration assumptions
- Simpler structure

**v2 (Refined Architecture, 2025-01-17 - later same day):**
- Production-ready modular design
- Four core modules (MOD-001 to MOD-004)
- Enhanced state management
- Clear separation of concerns
- SDK-first approach (note: SDK didn't exist when v1 written)

**Resolution:** **Use v2 (Evolved Design)**

**Rationale:**
1. **Resolution Rule #2:** Actual Implementation (v2 is what's being built)
2. **Resolution Rule #4:** Most Detailed Specification (v2 is more comprehensive)
3. **Better Design:** v2 is production-ready with proven modularity
4. **No Contradiction:** v2 is refinement of v1, not replacement

**Action Required:**
- Use v2 architecture in all unified specs
- Document v1 as historical context
- Note: Both specs written before SDK existed (context matters)

---

### Additional Observations

#### Non-Conflicts (Clarifications Needed)

**1. SDK vs Manual API Integration:**
- Original specs written BEFORE Project-X-Py SDK existed
- Specs describe manual WebSocket handling (outdated)
- Current implementation is SDK-first (93% code reduction)
- **Not a conflict**, just outdated context
- **Action:** Update integration specs to reflect SDK-first approach

**2. Missing Implementation vs Spec:**
- 10 of 13 rules have no implementation (77% gap)
- 3 state managers missing (MOD-002, MOD-003, MOD-004)
- **Not a conflict**, just work to be done
- **Action:** No spec changes needed, just implementation

**3. Brief Specs (RULE-004, 005, 010, 011):**
- Some specs are only 40-50 lines
- Others are 200-300 lines
- **Not a conflict**, just varying detail levels
- **Action:** Expand brief specs in unified version

---

## Resolution Strategy

### Resolution Rules (Priority Order)

**Priority 1: User Guidance** ⭐ HIGHEST AUTHORITY
- User's architectural decisions override all specs
- Example: "No admin unlock for trading" = remove all mentions
- When to use: User explicitly provides design decision

**Priority 2: Actual Implementation**
- Code in `src/` is ground truth
- If spec conflicts with working code, code wins
- When to use: Spec describes one thing, implementation does another (and works)

**Priority 3: Newest Specification**
- More recent specs are more refined
- Later dates indicate updated thinking
- When to use: Two specs contradict, check timestamps

**Priority 4: Most Detailed Specification**
- Comprehensive specs over brief summaries
- 200-line spec > 40-line spec
- When to use: One source has way more detail

**Priority 5: Security Model**
- For enforcement decisions, security wins
- Prevent account violations > user convenience
- When to use: Conflict about enforcement strictness

**Priority 6: SDK Integration**
- SDK-first approach over manual API
- Proven 93% code reduction
- When to use: Conflict about how to integrate with TopstepX

### Application Examples

**Example 1: RULE-004 Enforcement Type**
- Conflict: Primary spec says "Hard Lockout", Categories doc says "Trade-by-Trade"
- **Apply Rule #3:** Newest Specification (Categories doc is 2025-10-23, Primary is 2025-01-17)
- **Result:** Use Trade-by-Trade from Categories doc
- **Bonus:** Categories doc explicitly says "corrected enforcement categories"

**Example 2: Admin Unlock Mentions**
- Conflict: Specs say "admin override", User says "no admin unlock"
- **Apply Rule #1:** User Guidance (HIGHEST priority)
- **Result:** Remove all "admin override" mentions, use reset schedules only

**Example 3: Architecture v1 vs v2**
- Conflict: Two architecture versions exist
- **Apply Rule #2:** Actual Implementation (v2 is what's being built)
- **Apply Rule #4:** Most Detailed Specification (v2 is more comprehensive)
- **Result:** Use v2 architecture

---

## Phase 3: Delegation Plan

### Overview

**6 Specialized Researchers** will work in parallel to create unified specifications for all 88 features across 8 domains.

**Output Format:** Each unified spec must include:
1. **Single Canonical Specification** (unified from all sources)
2. **Conflict Resolutions** (what conflicted, which source won, why)
3. **Version History** (v1.0, v2.0, v3.0 - unified)
4. **Original Sources** (file paths and line numbers)
5. **Implementation Status** (from Wave 2 gap analysis)
6. **Examples** (code snippets from codebase if available)
7. **Tests** (coverage status from Wave 2)

### Researcher 1: Risk Rules Unification

**Scope:** 13 risk rules (RULE-001 through RULE-013)

**Input Documents:**
- `/docs/PROJECT_DOCS/rules/01_max_contracts.md` through `12_trade_management.md` (12 files)
- `/docs/current/RULE_CATEGORIES.md` (categorization and updates)
- `/docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md`
- `/docs/analysis/wave2-gap-analysis/01-RISK-RULES-GAPS.md`
- User architectural guidance (this report)

**Conflicts to Resolve:**
1. **RULE-004:** Primary spec (Hard Lockout) vs Categories doc (Trade-by-Trade)
   - **Resolution:** Use Categories doc (newer, explicit correction)
2. **RULE-005:** Primary spec (Hard Lockout) vs Categories doc (Trade-by-Trade)
   - **Resolution:** Make configurable (both modes valid)
3. **RULE-013:** Missing dedicated spec file
   - **Resolution:** Create using RULE-003 as template
4. **Admin Unlock Mentions:** RULE-003, 009, 010, 013
   - **Resolution:** Remove, use reset schedules only

**Output Files:**
- `/docs/specifications/unified/rules/01-max-contracts.md` (13 files total)
- Each file follows unified spec template
- Include conflict resolution section
- Document implementation status from Wave 2

**Estimated Effort:** 3-4 days

**Priority:** Critical (foundation for implementation)

---

### Researcher 2: Architecture Unification

**Scope:** System architecture and 4 core modules (MOD-001 to MOD-004)

**Input Documents:**
- `/docs/PROJECT_DOCS/architecture/ARCHITECTURE_V1.md`
- `/docs/PROJECT_DOCS/architecture/ARCHITECTURE_V2.md`
- `/docs/PROJECT_DOCS/architecture/MOD-001_ENFORCEMENT_ACTIONS.md` through `MOD-004_RESET_SCHEDULER.md`
- `/docs/analysis/wave1-feature-inventory/03-ARCHITECTURE-INVENTORY.md`
- `/docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md`

**Conflicts to Resolve:**
1. **v1 vs v2:** Which architecture to use
   - **Resolution:** Use v2 (evolved, production-ready)
2. **Module Scope:** What each MOD should/shouldn't do
   - **Resolution:** Use v2 module definitions

**Output Files:**
- `/docs/specifications/unified/architecture/system-architecture.md`
- `/docs/specifications/unified/architecture/mod-001-enforcement-actions.md` (4 files for each MOD)
- `/docs/specifications/unified/architecture/component-relationships.md`

**Estimated Effort:** 2-3 days

**Priority:** High (needed for implementation planning)

---

### Researcher 3: SDK Integration Unification

**Scope:** SDK integration approach, API vs SDK comparison, event flow

**Input Documents:**
- `/docs/PROJECT_DOCS/api/topstepx_integration.md`
- `/docs/current/SDK_INTEGRATION_GUIDE.md`
- `/docs/current/RULES_TO_SDK_MAPPING.md`
- `/docs/analysis/wave1-feature-inventory/02-SDK-INTEGRATION-INVENTORY.md`
- `SDK_API_REFERENCE.md`
- `SDK_ENFORCEMENT_FLOW.md`

**Conflicts to Resolve:**
1. **Manual API vs SDK:** Original specs describe manual integration
   - **Resolution:** Use SDK-first (93% code reduction proven)
2. **Event Types:** SDK events vs custom Risk events
   - **Resolution:** Document EventBridge pattern (SDK → Risk events)

**Output Files:**
- `/docs/specifications/unified/sdk-integration.md`
- `/docs/specifications/unified/api-reference.md`
- `/docs/specifications/unified/event-flow.md`

**Estimated Effort:** 2 days

**Priority:** High (critical for understanding integration)

---

### Researcher 4: Testing Strategy Unification

**Scope:** Testing approaches, test pyramid, TDD workflow, runtime debugging

**Input Documents:**
- `/docs/testing/TESTING_GUIDE.md`
- `/docs/testing/RUNTIME_DEBUGGING.md`
- `/docs/testing/WORKING_WITH_AI.md`
- `/docs/analysis/wave1-feature-inventory/04-TESTING-INVENTORY.md`
- `/docs/analysis/wave2-gap-analysis/06-TESTING-GAPS.md`
- `TEST_RUNNER_FINAL_FIXES.md`

**Conflicts to Resolve:**
1. **Testing Hierarchy:** Unit vs Integration vs E2E vs Runtime
   - **Resolution:** Document 4-tier pyramid with runtime validation layer
2. **Test Runner Behavior:** Multiple docs describe different approaches
   - **Resolution:** Use current interactive menu implementation

**Output Files:**
- `/docs/specifications/unified/testing-strategy.md`
- `/docs/specifications/unified/test-coverage-requirements.md`
- `/docs/specifications/unified/runtime-validation.md`

**Estimated Effort:** 2 days

**Priority:** Medium (testing infrastructure exists, just needs consolidation)

---

### Researcher 5: Configuration Unification

**Scope:** YAML config formats, validation, hot reload, accounts mapping

**Input Documents:**
- `/docs/current/CONFIG_FORMATS.md`
- `/docs/current/MULTI_SYMBOL_SUPPORT.md`
- `/docs/analysis/wave1-feature-inventory/05-SECURITY-CONFIG-INVENTORY.md`
- `/docs/analysis/wave2-gap-analysis/04-CONFIG-SYSTEM-GAPS.md`
- Example configs in `/config/`

**Conflicts to Resolve:**
1. **Config Structure:** Different examples in different docs
   - **Resolution:** Create canonical schema, document variations
2. **Validation Approach:** Pydantic vs manual validation
   - **Resolution:** Use Pydantic (already in implementation)

**Output Files:**
- `/docs/specifications/unified/configuration/config-schema.md`
- `/docs/specifications/unified/configuration/accounts-mapping.md`
- `/docs/specifications/unified/configuration/holidays-calendar.md`

**Estimated Effort:** 2 days

**Priority:** Medium (config system partially exists)

---

### Researcher 6: CLI Unification

**Scope:** Trader CLI (view-only) vs Admin CLI (elevated), UAC security

**Input Documents:**
- `/docs/PROJECT_DOCS/cli/TRADER_CLI.md`
- `/docs/PROJECT_DOCS/cli/ADMIN_CLI.md`
- `/docs/current/SECURITY_MODEL.md`
- `/docs/analysis/wave1-feature-inventory/07-DEVELOPER-EXPERIENCE-INVENTORY.md`
- `/docs/analysis/wave2-gap-analysis/03-CLI-SYSTEM-GAPS.md`

**Conflicts to Resolve:**
1. **Admin vs Trader Separation:** What each can do
   - **Resolution:** Use Windows UAC model (admin configures, trader views)
2. **Lockout Display:** How to show countdowns
   - **Resolution:** Document 8-checkpoint logging integration

**Output Files:**
- `/docs/specifications/unified/cli-reference.md`
- `/docs/specifications/unified/trader-cli-screens.md`
- `/docs/specifications/unified/admin-cli-commands.md`

**Estimated Effort:** 2 days

**Priority:** Medium (CLI not started yet, clear specs needed)

---

## Unified Spec Template

Each unified specification MUST follow this format:

```markdown
# [FEATURE-ID]: [Feature Name]

**Version:** 3.0 (Unified Specification)
**Date:** 2025-10-25
**Status:** [Implemented/Partial/Missing]
**Domain:** [Risk Rules / Architecture / SDK Integration / etc.]

---

## Single Canonical Specification

[THE unified specification - this is the ONE SOURCE OF TRUTH going forward]

### Purpose
[What this feature does]

### Triggers
[What events/conditions activate this feature]

### Enforcement/Behavior
[What actions are taken]

### Parameters
[Configuration options]

### Implementation Details
[SQLite schemas, API requirements, dependencies, etc.]

### Examples
[Code snippets, config examples, usage patterns]

---

## Conflict Resolutions

### Conflict 1: [Description]

**Source A:** [File path, lines X-Y]
- [What Source A said]

**Source B:** [File path, lines X-Y]
- [What Source B said]

**Resolution:** [Which one we chose]

**Rationale:** [Why we chose it - reference resolution rules]
- **Resolution Rule:** [#1 User Guidance / #2 Implementation / etc.]
- **Reasoning:** [Detailed explanation]

---

## Version History

### v1.0 (2025-01-17)
- Original specification in [file path]
- [Key characteristics]

### v2.0 (2025-10-23)
- Revised specification in [file path]
- [Changes made]

### v3.0 (2025-10-25) ← UNIFIED VERSION
- Consolidated from all sources
- Resolved [N] conflicts
- Applied user architectural guidance
- **This is the authoritative spec going forward**

---

## Original Sources

All source documents referenced (for traceability):
1. [File path] (lines X-Y) - [Description]
2. [File path] (lines X-Y) - [Description]
3. [etc.]

---

## Implementation Status (from Wave 2 Gap Analysis)

**Status:** [Implemented/Partial/Missing]

**Dependencies:**
- [Module/Feature] - [Status]
- [Module/Feature] - [Status]

**Estimated Effort:** [X days/weeks]

**Priority:** [Critical/High/Medium/Low]

**Blocks:** [List of dependent features]

---

## Test Coverage (from Wave 2 Analysis)

**Unit Tests:** [X tests / Y% coverage]
**Integration Tests:** [X tests / Y% coverage]
**E2E Tests:** [X tests / Y% coverage]
**Runtime Tests:** [X tests / Y% coverage]

**Test Scenarios:**
1. [Test scenario]
2. [Test scenario]

---

## Examples

### Configuration Example
\`\`\`yaml
[YAML config]
\`\`\`

### Code Example
\`\`\`python
[Python code]
\`\`\`

### Usage Example
\`\`\`python
[Usage pattern]
\`\`\`

---

**End of Unified Specification**
```

---

## Timeline Estimate

### Phase 1-2: Coordinator Analysis (COMPLETE)
- **Duration:** 2-3 days
- **Deliverable:** This report + conflict inventory + delegation plan
- **Status:** ✅ Complete

### Phase 3: Parallel Research (IN PROGRESS)
- **Duration:** 1-2 weeks
- **Researchers:** 6 specialists working in parallel
- **Deliverables:** Unified specs for all 88 features

| Researcher | Domain | Files | Effort | Dependencies |
|------------|--------|-------|--------|--------------|
| 1 | Risk Rules | 13 files | 3-4 days | None (can start now) |
| 2 | Architecture | 6 files | 2-3 days | None (can start now) |
| 3 | SDK Integration | 3 files | 2 days | None (can start now) |
| 4 | Testing Strategy | 3 files | 2 days | None (can start now) |
| 5 | Configuration | 3 files | 2 days | None (can start now) |
| 6 | CLI | 3 files | 2 days | None (can start now) |

**All researchers can work in parallel** - no sequential dependencies

### Phase 4: Review & Validation (NOT STARTED)
- **Duration:** 2-3 days
- **Activities:**
  - Coordinator review of all unified specs
  - Cross-check for remaining conflicts
  - Validate completeness
  - Final approval

**Total Timeline:** 2-3 weeks from start to completion

---

## Next Steps

### Immediate Actions (Coordinator)
1. ✅ Create delegation plan (this report)
2. ⏳ Spawn 6 researcher agents with specific instructions
3. ⏳ Monitor progress (daily check-ins)
4. ⏳ Review outputs as researchers complete work

### Researcher Instructions (To be delegated)
Each researcher will receive:
- This coordination report (context)
- Specific input document list
- Conflicts to resolve
- Unified spec template
- Output file locations
- Success criteria

### Success Criteria
Each researcher must:
- ✅ Create unified specs for all features in their domain
- ✅ Resolve all identified conflicts
- ✅ Document resolution rationale
- ✅ Follow unified spec template exactly
- ✅ Include version history
- ✅ Reference all original sources
- ✅ Document implementation status from Wave 2
- ✅ Provide code examples where available

### Final Deliverable
- `/docs/specifications/unified/` directory with:
  - `rules/` (13 files) - Unified rule specs
  - `architecture/` (6 files) - Unified architecture docs
  - `sdk-integration.md` - Unified SDK approach
  - `testing-strategy.md` - Unified testing approach
  - `configuration/` (3 files) - Unified config docs
  - `cli-reference.md` - Unified CLI docs

**Total:** ~31 unified specification files covering all 88 features

---

## Key Principles for Researchers

### 1. User Guidance is LAW
When user provides architectural decisions, they **override all specs**. No exceptions.

### 2. No Information Loss
Every source document must be referenced. Nothing is thrown away. Even outdated specs are preserved in "Version History" for context.

### 3. Clear Rationale
Every conflict resolution must explain **WHY** that choice was made. Reference resolution rules explicitly.

### 4. Implementation-Ready
Unified specs should be clear enough to code from. Include SQLite schemas, API endpoints, configuration examples, test scenarios.

### 5. Version History Matters
Track the evolution of specs over time. v1.0 → v2.0 → v3.0 (unified). Context matters.

---

## Risk Assessment

### High Risk
1. **Researcher Consistency:** 6 different researchers might interpret template differently
   - **Mitigation:** Provide detailed template, examples, and clear success criteria

2. **Missed Conflicts:** Researchers might not spot all conflicts
   - **Mitigation:** Coordinator review phase (Phase 4) catches missed conflicts

### Medium Risk
1. **Spec Interpretation:** Different researchers might resolve conflicts differently
   - **Mitigation:** Clear resolution rules (6-tier priority system)

2. **Timeline Slippage:** Some researchers might take longer
   - **Mitigation:** Daily check-ins, offer support if needed

### Low Risk
1. **Template Compliance:** Researchers might deviate from template
   - **Mitigation:** Clear template with examples, easy to follow

---

## Conclusion

**Wave 3 is ready to execute.**

### Summary
- ✅ 5 major conflicts identified and resolution approach defined
- ✅ 6 specialized researchers ready to work in parallel
- ✅ Clear resolution rules (6-tier priority system)
- ✅ User architectural guidance provides authoritative override
- ✅ Unified spec template ready
- ✅ Timeline: 2-3 weeks to completion

### Critical Success Factors
1. **User Guidance Applied:** All "admin unlock" mentions removed, reset schedules used
2. **RULE-004/005 Conflicts Resolved:** Use newer categories doc approach
3. **RULE-013 Created:** Using RULE-003 as template
4. **Architecture v2 Used:** Production-ready modular design
5. **SDK-First Documented:** Proven 93% code reduction approach

### Next Action
**DO NOT spawn researchers yet** - Coordinator to review this plan first, then delegate to 6 researchers in parallel.

---

**Report Complete - Ready for Delegation**

**Coordinator:** Wave 3 Coordinator - Spec Unification Specialist
**Date:** 2025-10-25
**Status:** Planning Complete, Awaiting Approval to Proceed
**Next Phase:** Delegate to 6 Researchers (Phase 3)
