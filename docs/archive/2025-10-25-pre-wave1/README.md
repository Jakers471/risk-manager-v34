# Pre-Wave 1 Documentation Archive

**Archived:** October 25, 2025
**Reason:** Superseded by Wave 1 Feature Discovery Analysis

---

## What's in This Archive

This archive contains all documentation that existed **before Wave 1 Feature Discovery**. These documents have been analyzed, consolidated, and their findings are now in:

**📊 Current Source of Truth:** `/docs/analysis/wave1-feature-inventory/`

---

## Archive Organization

### 01-specifications/
**Original:** `docs/PROJECT_DOCS/`

**Contents:**
- Original project specifications (pre-SDK era)
- 12 risk rule specifications
- ProjectX Gateway API documentation (30+ endpoints)
- System architecture (v1 and v2)
- Module specifications (enforcement, lockout, timer, reset)
- Project overview and summaries

**Status:** Analyzed in Wave 1, findings in:
- `01-RISK-RULES-INVENTORY.md`
- `02-SDK-INTEGRATION-INVENTORY.md`
- `03-ARCHITECTURE-INVENTORY.md`

**Note:** These specs were written BEFORE Project-X SDK existed. They describe manual API integration. Current implementation is SDK-first, but these specs are valuable for understanding design intent and edge cases.

---

### 02-status-tracking/
**Original:** `docs/current/`, `docs/implementation/`, `docs/progress/`

**Contents:**
- Project status documents
- Implementation plans
- Progress tracking
- SDK integration guides
- Security model
- Configuration formats
- Multi-symbol support
- Rule categories and mappings

**Status:** Analyzed in Wave 1, findings in:
- `06-IMPLEMENTATION-STATUS-INVENTORY.md`
- `05-SECURITY-CONFIG-INVENTORY.md`
- `02-SDK-INTEGRATION-INVENTORY.md`

**Note:** Current status is now tracked in Wave 1 reports. These docs show the evolution of the project over time.

---

### 03-testing-docs/
**Original:** `docs/testing/`

**Contents:**
- Testing methodology guide
- Runtime debugging documentation
- Working with AI workflows
- Testing navigation

**Status:** Analyzed in Wave 1, findings in:
- `04-TESTING-INVENTORY.md`

**Note:** These docs have been consolidated and improved. The Wave 1 analysis is now the authoritative testing reference.

---

### 04-developer-guides/
**Original:** `docs/dev-guides/`

**Contents:**
- Quick reference guides
- Implementation summaries
- Security quick reference

**Status:** Analyzed in Wave 1, findings in:
- `07-DEVELOPER-EXPERIENCE-INVENTORY.md`
- `08-TECHNICAL-REFERENCE-INVENTORY.md`

**Note:** Developer experience is now comprehensively documented in Wave 1. Use those reports for current guidance.

---

## Why Archive?

### Before Wave 1:
- ❌ Multiple versions of specs (v1, v2, current, old)
- ❌ Conflicting information across docs
- ❌ Unclear which docs were authoritative
- ❌ Hard to find specific features
- ❌ ~200+ markdown files to search through

### After Wave 1:
- ✅ Single source of truth (11 inventory reports)
- ✅ All conflicts identified and resolved
- ✅ Every feature catalogued with source references
- ✅ Clear version matrix (old vs new)
- ✅ Easy navigation by category

---

## How to Use This Archive

### If You Need to Reference Original Specs:

1. **Check Wave 1 First:** `/docs/analysis/wave1-feature-inventory/00-WAVE1-SUMMARY.md`
2. **Find the Category:** Use the appropriate inventory report (01-08)
3. **Trace to Source:** Each finding includes file path and line numbers
4. **Read Original if Needed:** Come to this archive for full original context

### Navigation:

```
Need original risk rule spec?
→ 01-specifications/rules/

Need to see how status tracking evolved?
→ 02-status-tracking/

Need original testing docs?
→ 03-testing-docs/

Need old developer guides?
→ 04-developer-guides/
```

---

## File Counts

| Category | Files | Purpose |
|----------|-------|---------|
| 01-specifications | ~60 files | Original project specs (pre-SDK) |
| 02-status-tracking | ~15 files | Status, plans, progress |
| 03-testing-docs | ~4 files | Testing methodology |
| 04-developer-guides | ~3 files | Quick references |
| **TOTAL** | **~82 files** | **Complete pre-Wave 1 documentation** |

---

## Relationship to Wave 1 Reports

| Archive Category | Wave 1 Report |
|------------------|---------------|
| 01-specifications/rules/ | 01-RISK-RULES-INVENTORY.md |
| 01-specifications/projectx_gateway_api/ | 02-SDK-INTEGRATION-INVENTORY.md |
| 01-specifications/architecture/ | 03-ARCHITECTURE-INVENTORY.md |
| 01-specifications/modules/ | 03-ARCHITECTURE-INVENTORY.md |
| 03-testing-docs/ | 04-TESTING-INVENTORY.md |
| 02-status-tracking/current/SECURITY_MODEL.md | 05-SECURITY-CONFIG-INVENTORY.md |
| 02-status-tracking/current/PROJECT_STATUS.md | 06-IMPLEMENTATION-STATUS-INVENTORY.md |
| 02-status-tracking/implementation/ | 06-IMPLEMENTATION-STATUS-INVENTORY.md |
| 04-developer-guides/ | 07-DEVELOPER-EXPERIENCE-INVENTORY.md |
| 01-specifications/api/ | 08-TECHNICAL-REFERENCE-INVENTORY.md |

---

## Important Notes

### These Docs Are NOT Obsolete

The archive contains valuable information:
- **Design Intent:** Why features were designed a certain way
- **Edge Cases:** Detailed scenarios and error handling
- **Historical Context:** How the project evolved
- **Implementation Details:** Low-level specifications

### When to Use Archive vs Wave 1:

**Use Wave 1 For:**
- ✅ Finding features quickly
- ✅ Understanding current state
- ✅ Implementation guidance
- ✅ API contracts
- ✅ High-level overview

**Use Archive For:**
- ✅ Deep implementation details
- ✅ Understanding design rationale
- ✅ Historical context
- ✅ Tracing feature evolution
- ✅ Original edge case analysis

---

## Archive Maintenance

**This archive should NOT be modified.**

It represents a snapshot of documentation before Wave 1 analysis. If you need to update documentation, do so in:
- `/docs/analysis/` for feature inventories
- Root markdown files for active references
- Create new docs in appropriate locations

---

**Archived by:** Wave 1 Feature Discovery Swarm (Coordinator + 8 Researchers)
**Analyzed:** 201 markdown files
**Output:** 11 consolidated inventory reports (396KB, ~13K lines)
**Completion:** October 25, 2025, 01:15 AM

---

**For current documentation, see:** `/docs/analysis/wave1-feature-inventory/00-WAVE1-SUMMARY.md`
