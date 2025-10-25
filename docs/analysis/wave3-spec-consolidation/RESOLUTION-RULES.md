# Wave 3: Conflict Resolution Rules & Guidelines

**Document ID:** RESOLUTION-RULES
**Created:** 2025-10-25
**Purpose:** Authoritative resolution framework for all specification conflicts
**Status:** Complete - Ready for Researcher Application

---

## Priority Hierarchy (The LAW)

When specifications conflict, apply these resolution rules **IN ORDER**. The first rule that applies wins.

```
Priority 1: User Guidance ⭐⭐⭐⭐⭐ HIGHEST AUTHORITY
    ↓ (if no user guidance, try next rule)
Priority 2: Actual Implementation ⭐⭐⭐⭐
    ↓ (if no implementation exists, try next rule)
Priority 3: Newest Specification ⭐⭐⭐
    ↓ (if dates are same/unclear, try next rule)
Priority 4: Most Detailed Specification ⭐⭐
    ↓ (if detail level similar, try next rule)
Priority 5: Security Model ⭐
    ↓ (if not security-related, try next rule)
Priority 6: SDK Integration
    ↓ (last resort tiebreaker)
```

**If all rules fail to resolve conflict:** Escalate to Coordinator.

---

## Resolution Rule #1: User Guidance (ABSOLUTE AUTHORITY)

### What It Is
User's explicit architectural decisions **override all specifications**, no exceptions.

### When to Use
- User provides design decision in CLAUDE.md, chat, or documentation
- User states preference between conflicting approaches
- User clarifies intended behavior

### Why It's #1
- User is the project owner
- User defines the product vision
- User's decisions are final

### Examples

#### Example 1: Admin Unlock Model (CONFLICT-006)

**Conflict:** Specs say "admin can manually unlock", user says "no admin unlock"

**User Guidance:**
> "Admin does NOT manually unlock accounts for trading. Every rule auto-enforces via reset schedules, trade-by-trade, time-based. System is autonomous once configured."

**Resolution:** Remove ALL "admin override" mentions from specs

**Rationale:** User guidance is ABSOLUTE. When user says "no admin unlock", that's the final word.

**Apply to:** RULE-003, 009, 010, 013 specs

---

#### Example 2: Enforcement Philosophy

**User Guidance:**
> "Rules use: daily reset (midnight ET), session-based, trade-by-trade logic. NO manual admin intervention for trading lockouts."

**Resolution:** All rules must use autonomous enforcement (timers, schedules, API-driven)

**Rationale:** User defines enforcement philosophy for entire system

**Apply to:** All 13 risk rules

---

### How to Apply

```
1. Check if user provided guidance on this conflict
2. If YES:
   a. User guidance wins
   b. Document user's exact words
   c. Update all conflicting specs to match
   d. Mark as "Resolution Rule #1: User Guidance"
3. If NO:
   a. Move to Resolution Rule #2
```

---

## Resolution Rule #2: Actual Implementation (CODE IS TRUTH)

### What It Is
Code in `src/` directory is the ground truth. If working code contradicts spec, code wins.

### When to Use
- Feature is already implemented
- Spec describes one approach, code does another
- Code is working and tested

### Why It's #2
- Working code represents real-world decisions
- Refactoring working code to match outdated spec is wasteful
- Specs should document reality

### Examples

#### Example 3: SDK vs Manual API (CONFLICT-005)

**Conflict:** Specs describe manual API integration, implementation uses SDK

**Actual Implementation:**
```python
# src/risk_manager/integrations/trading.py (80 lines)
from projectx import TradingSuite
# Uses SDK for all API operations
```

**Original Spec:**
```markdown
# Spec describes manual SignalR integration (~1100 lines)
# Uses signalrcore library directly
# Manual position management
# Manual authentication
```

**Resolution:** Use SDK-first approach (what's implemented)

**Rationale:**
- Code works (80 lines vs 1100 lines = 93% reduction)
- SDK provides better reliability
- Refactoring to manual API would be wasteful

---

#### Example 4: Architecture v2 in Use (CONFLICT-004)

**Conflict:** Two architecture versions exist (v1 and v2)

**Actual Implementation:**
```python
# src/risk_manager/sdk/enforcement.py (MOD-001 equivalent)
# src/risk_manager/state/pnl_tracker.py (part of state management)
# Uses v2 modular architecture
```

**Resolution:** Use v2 architecture (what's being built)

**Rationale:** v2 is the reality, v1 is historical planning

---

### How to Apply

```
1. Check if feature is implemented in src/ directory
2. If YES:
   a. Read the actual code
   b. If code contradicts spec AND code works:
      - Code wins
      - Update spec to match code
      - Mark as "Resolution Rule #2: Actual Implementation"
   c. If code matches one spec but not another:
      - Use the spec that matches code
3. If NO (not implemented):
   a. Move to Resolution Rule #3
```

---

## Resolution Rule #3: Newest Specification (EVOLUTION MATTERS)

### What It Is
More recent specs are more refined. Later dates indicate updated thinking.

### When to Use
- Two specs contradict each other
- Both have clear dates
- Neither has been implemented yet

### Why It's #3
- Specs evolve over time
- Later specs incorporate learnings
- More recent = more refined

### Examples

#### Example 5: RULE-004 Enforcement Type (CONFLICT-001)

**Conflict:** Primary spec (2025-01-17) vs Categories doc (2025-10-23)

**Primary Spec (2025-01-17):**
```markdown
Enforcement Type: Hard Lockout (Category 3)
Action: Close ALL positions
Lockout: Yes, until reset time
```

**Categories Doc (2025-10-23):**
```markdown
Enforcement Type: Trade-by-Trade (Category 1)
Action: Close ONLY that losing position
Lockout: None
**Critical Changes**: RULE-004, 005, 008 are trade-by-trade (NOT close all)
```

**Resolution:** Use Categories Doc (newer)

**Rationale:**
- Categories doc is 8 months newer
- Explicitly states "corrected enforcement categories"
- More refined thinking

**Date Comparison:** 2025-10-23 > 2025-01-17 → Newer wins

---

#### Example 6: Architecture Evolution

**v1 (2025-01-17 morning):**
```markdown
Basic architecture
No MOD-001 to MOD-004 modules
Simpler structure
```

**v2 (2025-01-17 afternoon):**
```markdown
Refined architecture
Four core modules (MOD-001 to MOD-004)
Production-ready design
```

**Resolution:** Use v2 (same day, but later refinement)

**Rationale:** v2 is evolution of v1 (not contradiction)

---

### How to Apply

```
1. Check dates on conflicting specs
2. If dates are different:
   a. Newer spec wins
   b. Document both dates in resolution
   c. Mark as "Resolution Rule #3: Newest Specification"
3. If dates are same OR unclear:
   a. Move to Resolution Rule #4
```

---

## Resolution Rule #4: Most Detailed Specification (COMPLETENESS WINS)

### What It Is
Comprehensive specs over brief summaries. 200-line spec > 40-line spec.

### When to Use
- Two specs describe same feature
- One is much more detailed
- Both are current/undated

### Why It's #4
- More detail = more thought went into it
- Comprehensive specs are implementation-ready
- Brief specs may be summaries of longer specs

### Examples

#### Example 7: RULE-003 vs Brief Mention

**Primary Spec (228 lines):**
```markdown
# /docs/PROJECT_DOCS/rules/03_daily_realized_loss.md

## Purpose
[50 lines of detail]

## Trigger Logic
[40 lines with code examples]

## SQLite Schema
CREATE TABLE daily_pnl (...)

## Test Scenarios
[60 lines of edge cases]

## API Requirements
[30 lines]
```

**Brief Mention (10 lines):**
```markdown
# Some inventory doc
RULE-003: Daily loss limit - close all if loss > $500
```

**Resolution:** Use primary spec (228 lines)

**Rationale:** Comprehensive spec has all implementation details

---

#### Example 8: RULE-005 Both Modes Valid (CONFLICT-002)

**Primary Spec (150 lines):**
```markdown
# Describes Hard Lockout approach
# Use case: "Take the win and walk away"
```

**Categories Doc (50 lines):**
```markdown
# Describes Trade-by-Trade approach
# Use case: "Take profit and keep trading"
```

**Resolution:** Include BOTH (configurable)

**Rationale:**
- Both have merit
- Most detailed = include both approaches
- Make configurable via `enforcement_mode` parameter

---

### How to Apply

```
1. Compare line counts or detail level
2. If one is significantly more detailed:
   a. More detailed spec wins
   b. Brief spec might be summary (check for cross-references)
   c. Mark as "Resolution Rule #4: Most Detailed Specification"
3. If both have similar detail:
   a. Move to Resolution Rule #5
4. If both have merit (different approaches):
   a. Include BOTH (make configurable)
   b. Document both approaches in unified spec
```

---

## Resolution Rule #5: Security Model (PREVENT VIOLATIONS)

### What It Is
For enforcement decisions, security wins. Prevent account violations > user convenience.

### When to Use
- Conflict about enforcement strictness
- One approach is more conservative
- Security/account protection is at stake

### Why It's #5
- Account violations = account termination
- Better safe than sorry
- Risk management is security-critical

### Examples

#### Example 9: Close All vs Reduce to Limit

**Option A:** Close ALL positions (more conservative)
**Option B:** Reduce to limit only (less disruptive)

**Resolution:** Use Option A (close all) **IF account violation risk**

**Rationale:**
- Preventing account violation is paramount
- More conservative = safer
- User can reconfigure if too strict

---

#### Example 10: Lockout Duration

**Option A:** Lock until manual admin unlock (strictest)
**Option B:** Lock until daily reset (balanced)
**Option C:** No lockout (least strict)

**Resolution:** Use Option B (balanced)

**Rationale:**
- Option A conflicts with User Guidance (no admin unlock)
- Option C too permissive (might allow repeated violations)
- Option B balances security + autonomy

---

### How to Apply

```
1. Check if conflict is about enforcement strictness
2. If YES:
   a. Identify security risk (account violation?)
   b. Choose more conservative approach
   c. Mark as "Resolution Rule #5: Security Model"
3. If NOT security-related:
   a. Move to Resolution Rule #6
```

---

## Resolution Rule #6: SDK Integration (PROVEN APPROACH)

### What It Is
SDK-first approach over manual API. Proven 93% code reduction.

### When to Use
- Conflict about how to integrate with TopstepX
- Manual API vs SDK approaches

### Why It's #6 (Last Resort)
- SDK approach is superior (proven)
- Only applies to integration questions
- Rarely a tiebreaker

### Examples

#### Example 11: WebSocket Connection

**Option A:** Manual SignalR using `signalrcore` library
**Option B:** Use SDK `TradingSuite.connect()`

**Resolution:** Use Option B (SDK)

**Rationale:**
- SDK handles connection automatically
- SDK handles reconnection
- SDK handles authentication
- 93% code reduction proven

---

### How to Apply

```
1. Check if conflict is about SDK vs manual API
2. If YES:
   a. SDK wins
   b. Mark as "Resolution Rule #6: SDK Integration"
3. If NO:
   a. ESCALATE TO COORDINATOR (no resolution rule applies)
```

---

## Resolution Decision Tree

```
START: Two specs conflict

    ↓

RULE #1: Did user provide guidance?
    YES → User guidance wins → DONE
    NO  → Continue to Rule #2

    ↓

RULE #2: Is feature implemented in src/?
    YES → Code wins → DONE
    NO  → Continue to Rule #3

    ↓

RULE #3: Do specs have different dates?
    YES → Newer spec wins → DONE
    NO  → Continue to Rule #4

    ↓

RULE #4: Is one spec significantly more detailed?
    YES → More detailed wins → DONE
    NO  → Continue to Rule #5

    ↓

RULE #5: Is this about security/enforcement strictness?
    YES → More conservative wins → DONE
    NO  → Continue to Rule #6

    ↓

RULE #6: Is this about SDK vs manual API?
    YES → SDK wins → DONE
    NO  → ESCALATE TO COORDINATOR
```

---

## Conflict Resolution Template

For each conflict, document resolution like this:

```markdown
### Conflict N: [Description]

**Source A:** [File path, lines X-Y]
- [What Source A said]

**Source B:** [File path, lines X-Y]
- [What Source B said]

**Resolution:** [Which one we chose OR Both (if configurable)]

**Resolution Rule Applied:** [#1 User Guidance / #2 Implementation / etc.]

**Rationale:**
- [Detailed explanation]
- [Why this rule applies]
- [What makes the winner better]

**Impact:**
- [What needs to change]
- [Implementation considerations]
- [Configuration changes]

**Action Items:**
1. [Specific tasks]
2. [Specific tasks]
```

---

## Special Cases

### Case 1: Both Approaches Valid (Make Configurable)

**When to Use:**
- Two approaches are equally valid
- Different users have different preferences
- Both can be implemented without conflict

**Example:** RULE-005 (Trade-by-Trade vs Hard Lockout)

**Resolution:**
```yaml
# Make configurable
enforcement_mode: "trade_by_trade"  # or "hard_lockout"
```

**Document Both Approaches:**
- Default mode (what most users want)
- Alternative mode (for different strategy)

---

### Case 2: Missing Specification (Create New)

**When to Use:**
- Spec mentioned but doesn't exist
- Other rules have detailed specs
- Consistency requires same detail level

**Example:** RULE-013 (no dedicated spec file)

**Resolution:**
- Create new spec using similar rule as template
- Match detail level of other specs
- Ensure consistency across all rules

---

### Case 3: Evolution Not Contradiction (Use Latest)

**When to Use:**
- v2 is refinement of v1
- Later version improves earlier version
- Not a conflict, just evolution

**Example:** Architecture v1 → v2

**Resolution:**
- Use latest version
- Document earlier version as historical context
- Note: Evolution, not contradiction

---

## Researcher Guidelines

### Before Resolving Conflict

1. **Identify the conflict clearly**
   - What are the two (or more) contradicting sources?
   - What specifically contradicts?
   - What is the impact if we choose wrong?

2. **Gather all sources**
   - Primary specifications
   - Categories/inventory docs
   - Implementation code
   - User guidance
   - Dates on all documents

3. **Apply decision tree**
   - Start with Rule #1 (User Guidance)
   - Work down priority order
   - Stop at first rule that applies

### While Resolving Conflict

4. **Document thoroughly**
   - Use conflict resolution template
   - Quote source documents
   - Explain rationale clearly
   - Reference resolution rule explicitly

5. **Consider impact**
   - What specs need updating?
   - What code needs changing?
   - What configurations need adjusting?

### After Resolving Conflict

6. **Validate resolution**
   - Does it make sense technically?
   - Does it align with user guidance?
   - Does it enable implementation?
   - Is rationale clear?

7. **Create unified spec**
   - Single canonical version
   - Include both source histories
   - Document conflict resolution
   - Provide examples

---

## Examples Applied to Real Conflicts

### Full Example: CONFLICT-001 (RULE-004)

**Step 1: Identify Conflict**
```markdown
Primary spec says: Hard Lockout (close all)
Categories doc says: Trade-by-Trade (close that position)
Impact: Different enforcement behavior, user experience
```

**Step 2: Gather Sources**
```markdown
Source A: /docs/PROJECT_DOCS/rules/04_daily_unrealized_loss.md (2025-01-17)
Source B: /docs/current/RULE_CATEGORIES.md lines 42-66 (2025-10-23)
Implementation: Not yet implemented (can choose either)
User Guidance: "Auto-enforce via trade-by-trade, reset schedules" (autonomous)
```

**Step 3: Apply Decision Tree**
```
RULE #1: User guidance?
  → YES: User says "auto-enforce via trade-by-trade"
  → Trade-by-Trade aligns with autonomous enforcement
  → BUT user guidance not explicit about THIS rule specifically
  → Continue to Rule #2

RULE #2: Implemented?
  → NO: Not implemented yet
  → Continue to Rule #3

RULE #3: Different dates?
  → YES: 2025-10-23 > 2025-01-17
  → Categories doc is 8 months newer
  → Categories doc explicitly says "corrected enforcement categories"
  → WINNER: Categories Doc (Trade-by-Trade)
```

**Step 4: Document Resolution**
```markdown
**Resolution:** Use Categories Doc (Trade-by-Trade)

**Resolution Rule Applied:** #3 Newest Specification + #1 User Guidance (alignment)

**Rationale:**
- Categories doc is newer (2025-10-23 vs 2025-01-17)
- Explicitly states "corrected enforcement categories"
- Trade-by-Trade aligns with user's autonomous enforcement philosophy
- More granular risk management (close losing position only)
```

---

## Summary

### The 6 Rules (In Order)
1. **User Guidance** - Absolute authority
2. **Actual Implementation** - Code is truth
3. **Newest Specification** - Evolution matters
4. **Most Detailed Specification** - Completeness wins
5. **Security Model** - Prevent violations
6. **SDK Integration** - Proven approach

### Key Principles
- **Start at Rule #1**, work down
- **First rule that applies wins**
- **Document thoroughly** (rationale, sources, impact)
- **Escalate to Coordinator** if no rule applies

### Success Criteria
Each conflict resolution must:
- ✅ Apply resolution rules explicitly
- ✅ Quote source documents
- ✅ Explain rationale clearly
- ✅ Document impact
- ✅ Provide action items

---

**Resolution Rules Complete - Ready for Application**

**Date:** 2025-10-25
**Status:** Complete
**Usage:** All 6 researchers use these rules to resolve conflicts
**Next:** Researchers create unified specs following these rules
