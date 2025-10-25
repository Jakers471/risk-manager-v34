# Root Reference Documentation Archive

**Archived:** October 25, 2025
**Original Location:** Project root (`/`)
**Reason:** Consolidated into Wave 1 Feature Discovery Analysis

---

## What's in This Archive

This folder contains **technical reference documents** that were in the project root before Wave 1 analysis.

These docs provided quick-reference information for:
- SDK API contracts
- Enforcement flow
- Logging system
- Test runner behavior

---

## Files Archived

| File | Size | Purpose | Wave 1 Report |
|------|------|---------|---------------|
| `SDK_API_REFERENCE.md` | 8.6KB | Complete API contracts | 08-TECHNICAL-REFERENCE-INVENTORY.md |
| `SDK_ENFORCEMENT_FLOW.md` | 11KB | 12-step enforcement chain | 02-SDK-INTEGRATION-INVENTORY.md |
| `LOGGING_FLOW.md` | 7.3KB | 8-checkpoint logging system | 05-SECURITY-CONFIG-INVENTORY.md |
| `SDK_LOGGING_IMPLEMENTATION.md` | 5.5KB | SDK logging integration | 05-SECURITY-CONFIG-INVENTORY.md |
| `SDK_LOGGING_QUICK_REFERENCE.md` | 5KB | Quick logging reference | 05-SECURITY-CONFIG-INVENTORY.md |
| `TEST_RUNNER_FINAL_FIXES.md` | 7.7KB | Test runner fixes | 04-TESTING-INVENTORY.md |
| `TEST_RUNNER_FIXES.md` | 4.8KB | Test runner behavior | 04-TESTING-INVENTORY.md |

**Total:** 7 files, ~49KB

---

## Why These Were in Project Root

**Before Wave 1:**
- Quick access for AI assistants (CLAUDE.md referenced them)
- Frequently referenced during development
- Created as "live" documentation alongside code changes

**After Wave 1:**
- All information consolidated into inventory reports
- Wave 1 reports provide better organization and cross-references
- Keeping in root would duplicate information

---

## What Each File Contained

### SDK_API_REFERENCE.md
**Complete API contracts to prevent test/code mismatches.**

Contents:
- RiskEvent API (actual parameters: `event_type`, not `type`)
- EventType enum (24 event types)
- PnLTracker API (takes `db: Database`, not `account_id`)
- RiskRule base class
- SDK integration classes

**Now in:** `08-TECHNICAL-REFERENCE-INVENTORY.md` (sections 1-6)

---

### SDK_ENFORCEMENT_FLOW.md
**12-step enforcement chain from violation to API.**

Contents:
- Complete enforcement flow diagram
- 3 critical wiring points
- SDK methods used for enforcement
- Event → Rule → Enforcement → SDK → API flow

**Now in:** `02-SDK-INTEGRATION-INVENTORY.md` (section: Enforcement Flow)

---

### LOGGING_FLOW.md
**8-checkpoint logging system for runtime debugging.**

Contents:
```
Checkpoint 1: 🚀 Service Start
Checkpoint 2: ✅ Config Loaded
Checkpoint 3: ✅ SDK Connected
Checkpoint 4: ✅ Rules Initialized
Checkpoint 5: ✅ Event Loop Running
Checkpoint 6: 📨 Event Received
Checkpoint 7: 🔍 Rule Evaluated
Checkpoint 8: ⚠️ Enforcement Triggered
```

**Now in:** `05-SECURITY-CONFIG-INVENTORY.md` (section: Logging Infrastructure)

---

### SDK_LOGGING_IMPLEMENTATION.md
**SDK logging integration details.**

Contents:
- Where to add logging (manager.py, engine.py, enforcement.py)
- Checkpoint placement strategy
- Log format (JSON vs human-readable)

**Now in:** `05-SECURITY-CONFIG-INVENTORY.md` (section: Logging Infrastructure)

---

### SDK_LOGGING_QUICK_REFERENCE.md
**Quick copy-paste logging examples.**

Contents:
- Logging code snippets for each checkpoint
- Configuration examples
- Common patterns

**Now in:** `05-SECURITY-CONFIG-INVENTORY.md` (section: Logging Infrastructure)

---

### TEST_RUNNER_FINAL_FIXES.md
**Test runner behavior and fixes.**

Contents:
- Test runner menu options
- Exit code semantics
- Auto-save report behavior
- Runtime smoke test integration

**Now in:** `04-TESTING-INVENTORY.md` (section: Test Runner)

---

### TEST_RUNNER_FIXES.md
**Earlier test runner fixes.**

Contents:
- Initial test runner issues
- Performance optimizations
- WSL2 considerations

**Now in:** `04-TESTING-INVENTORY.md` (section: Test Runner Evolution)

---

## How to Use This Archive

### If You Need Original Reference Docs:

1. **Check Wave 1 First:** See the mapped Wave 1 report (table above)
2. **Find in Inventory:** Wave 1 reports have better cross-references
3. **Reference Original:** Come here for exact original wording if needed

### Example Workflow:

```
Need API contracts?
→ Read 08-TECHNICAL-REFERENCE-INVENTORY.md first
→ If need original doc: archive/05-root-reference-docs/SDK_API_REFERENCE.md

Need enforcement flow?
→ Read 02-SDK-INTEGRATION-INVENTORY.md first
→ If need original diagram: archive/05-root-reference-docs/SDK_ENFORCEMENT_FLOW.md

Need logging checkpoint details?
→ Read 05-SECURITY-CONFIG-INVENTORY.md first
→ If need original: archive/05-root-reference-docs/LOGGING_FLOW.md
```

---

## What Stays in Project Root

**Only two markdown files remain in project root:**

1. **CLAUDE.md** (927 lines)
   - AI assistant entry point
   - Must stay in root for AI discoverability
   - Updated to reference Wave 1 reports

2. **README.md** (project README)
   - Human entry point
   - Standard location for any GitHub project
   - Points to Wave 1 and documentation

**All other docs are now organized in `/docs/`**

---

## Benefits of This Organization

**Before (Root Files):**
- ❌ 9 markdown files cluttering project root
- ❌ Duplicated information (root docs + docs/ folder)
- ❌ Hard to know which doc was most current
- ❌ No clear organization

**After (Archived):**
- ✅ Clean project root (only CLAUDE.md + README.md)
- ✅ Single source of truth (Wave 1 reports)
- ✅ Clear navigation (docs/README.md)
- ✅ Historical preservation (this archive)

---

## Archive Maintenance

**This archive should NOT be modified.**

It represents a snapshot of root reference docs before Wave 1 consolidation.

For current technical references:
- **API contracts:** `/docs/analysis/wave1-feature-inventory/08-TECHNICAL-REFERENCE-INVENTORY.md`
- **SDK integration:** `/docs/analysis/wave1-feature-inventory/02-SDK-INTEGRATION-INVENTORY.md`
- **Security/logging:** `/docs/analysis/wave1-feature-inventory/05-SECURITY-CONFIG-INVENTORY.md`
- **Testing:** `/docs/analysis/wave1-feature-inventory/04-TESTING-INVENTORY.md`

---

**Archived by:** Documentation Reorganization (Post-Wave 1)
**Date:** October 25, 2025
**Location:** `/docs/archive/2025-10-25-pre-wave1/05-root-reference-docs/`

**For current documentation, see:** `/docs/analysis/wave1-feature-inventory/`
