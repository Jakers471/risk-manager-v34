# Archived Testing Documentation - 2025-10-23

**These are OLD testing documents that have been CONSOLIDATED.**

---

## What's Here

This archive contains **5 redundant testing documents** (175KB total) created during the testing framework migration. These have been **consolidated into a single source of truth**.

### Archived Files

1. **AI_ASSISTED_TESTING_WORKFLOW.md** (41KB) - How SDK uses AI agents for testing
2. **RUNTIME_INTEGRATION_TESTING.md** (42KB) - Preventing "green tests but broken runtime"
3. **SDK_TESTING_VISUAL_GUIDE.md** (33KB) - Visual guide to SDK testing patterns
4. **TDD_WORKFLOW_GUIDE.md** (30KB) - Test-Driven Development workflow
5. **TESTING_METHODOLOGY_ANALYSIS.md** (29KB) - Testing methodology analysis

**Total**: 175KB, ~5,000 lines of redundant content

---

## Why Archived?

These documents had **significant overlap** (~75% redundancy):
- All explained TDD/Red-Green-Refactor cycle
- All covered integration vs unit testing
- All showed SDK testing patterns
- All had AI workflow guidance
- Content was scattered across 5 files

## What Replaced Them?

**CONSOLIDATED into 3 focused documents** (22KB total):

### ✅ Current Testing Documentation

**Location**: `/docs/testing/`

```
docs/testing/
├── README.md                    - Quick navigation (800B)
├── TESTING_GUIDE.md             - THE authoritative testing truth (12KB)
└── WORKING_WITH_AI.md           - AI collaboration workflow (9.3KB)
```

**Benefits of Consolidation**:
- ✅ Single source of truth
- ✅ No contradictions
- ✅ 87% size reduction (175KB → 22KB)
- ✅ Easy to maintain
- ✅ Clear learning path

---

## Content Mapping

**Where the content went:**

### From AI_ASSISTED_TESTING_WORKFLOW.md:
- **Agent descriptions** → `.claude/agents/` (5 custom agents created)
- **AI workflow** → `docs/testing/WORKING_WITH_AI.md`
- **Test reporting** → `docs/testing/TESTING_GUIDE.md` (Coverage section)

### From RUNTIME_INTEGRATION_TESTING.md:
- **Mock boundaries** → `docs/testing/TESTING_GUIDE.md` (Mocking section)
- **Integration patterns** → `docs/testing/TESTING_GUIDE.md` (Integration section)
- **Spec-based mocking** → `docs/testing/TESTING_GUIDE.md` (Best practices)

### From SDK_TESTING_VISUAL_GUIDE.md:
- **Visual patterns** → Integrated into TESTING_GUIDE.md examples
- **Code examples** → `docs/testing/TESTING_GUIDE.md` (AAA pattern, fixtures)

### From TDD_WORKFLOW_GUIDE.md:
- **Red-Green-Refactor** → `docs/testing/TESTING_GUIDE.md` (TDD section)
- **Workflow examples** → `docs/testing/TESTING_GUIDE.md` (Quick start)

### From TESTING_METHODOLOGY_ANALYSIS.md:
- **Methodology** → `docs/testing/TESTING_GUIDE.md` (Philosophy section)
- **Best practices** → `docs/testing/TESTING_GUIDE.md` (Best practices)

---

## Migration Summary

**Before** (Scattered):
```
docs/
├── AI_ASSISTED_TESTING_WORKFLOW.md      (41KB)
├── RUNTIME_INTEGRATION_TESTING.md       (42KB)
├── SDK_TESTING_VISUAL_GUIDE.md          (33KB)
├── TDD_WORKFLOW_GUIDE.md                (30KB)
└── TESTING_METHODOLOGY_ANALYSIS.md      (29KB)
Total: 175KB, 5 files, ~75% redundancy
```

**After** (Consolidated):
```
docs/testing/
├── README.md                             (800B)
├── TESTING_GUIDE.md                      (12KB)
└── WORKING_WITH_AI.md                    (9.3KB)
Total: 22KB, 3 files, 0% redundancy
```

**Space Saved**: 153KB (87% reduction)

---

## DO NOT Use These Files

**Use the current documentation instead:**

### For Testing
- **[docs/testing/README.md](../../testing/README.md)** - Start here
- **[docs/testing/TESTING_GUIDE.md](../../testing/TESTING_GUIDE.md)** - THE authoritative guide
- **[docs/testing/WORKING_WITH_AI.md](../../testing/WORKING_WITH_AI.md)** - AI workflow

### For AI Agents
- **[.claude/agents/](../../../.claude/agents/)** - 5 custom agents for risk manager

---

**Archived**: 2025-10-23
**Reason**: Consolidated into single source of truth
**Keep**: For historical reference only
**Use Instead**: `docs/testing/TESTING_GUIDE.md`
