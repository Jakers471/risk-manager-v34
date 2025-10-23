# Current Architecture Version

**Active Version:** ARCH-V2
**File:** `architecture/system_architecture_v2.md`
**Last Updated:** 2025-01-17

---

## 🎯 Quick Reference

**For AI Assistants:**
```
Read current architecture: docs/architecture/system_architecture_v2.md
```

**For Developers:**
- **Primary Reference:** `architecture/system_architecture_v2.md` (ARCH-V2)
- **API Integration:** `api/topstepx_integration.md` (API-INT-001)
- **Rules:** `rules/*.md` (RULE-001 to RULE-012)
- **Modules:** `modules/*.md` (MOD-001 to MOD-004)

---

## 📊 Version History

### **ARCH-V2** (Current - 2025-01-17)

**What's New:**
- ✅ Modular enforcement architecture (MOD-001 to MOD-004)
- ✅ Complete API integration pipeline and event processing
- ✅ Detailed specifications for all 12 risk rules
- ✅ SQLite state persistence design
- ✅ Windows Service implementation approach
- ✅ Dual-CLI architecture (admin + trader)
- ✅ Production-ready configuration examples

**Key Improvements from V1:**
- Separated concerns: Rules, Modules, API integration
- Reusable modules prevent code duplication
- Detailed API requirements for each component
- Clear enforcement types (trade-by-trade vs lockout)
- Concrete implementation guidance

**File:** `architecture/system_architecture_v2.md`

---

### **ARCH-V1** (Historical - 2025-01-17)

**What It Covered:**
- Original planning session notes
- Technology stack decisions (Python, TopstepX API, SQLite)
- Phase-based implementation strategy
- Initial directory structure
- User context and project goals
- Lessons from previous failed projects

**Why It Was Created:**
- Established foundation and project direction
- Documented key architectural decisions
- Captured requirements from planning interview

**File:** `architecture/system_architecture_v1.md`

---

## 🔄 When to Create ARCH-V3

Create a new architecture version when:
- **Major refactoring** of core components
- **Technology stack changes** (e.g., switch from Python to another language)
- **Fundamental data flow changes** (e.g., different event processing model)
- **New architectural patterns** (e.g., move from monolith to microservices)

**DON'T create new version for:**
- Adding new rules (just add RULE-013, RULE-014, etc.)
- Adding new modules (just add MOD-005, MOD-006, etc.)
- Minor updates to existing architecture (edit ARCH-V2 in place)
- Clarifications or documentation improvements

---

## 📝 How to Update Current Version

### **Small Changes to ARCH-V2:**
1. Edit `architecture/system_architecture_v2.md` in place
2. Update `last_updated` date in file header
3. No need to update this file (CURRENT_VERSION.md)

### **Creating ARCH-V3:**
1. Copy `system_architecture_v2.md` → `system_architecture_v3.md`
2. Update doc_id to `ARCH-V3` in new file
3. Make your architectural changes
4. Update **this file** to point to ARCH-V3
5. Update `ARCHITECTURE_INDEX.md` to reference ARCH-V3 as primary
6. Document changes in "Version History" section above

---

## ✅ Verification

**Current primary references are:**
- ✅ Architecture: ARCH-V2 (`architecture/system_architecture_v2.md`)
- ✅ API Integration: API-INT-001 (`api/topstepx_integration.md`)
- ✅ Project Overview: SUM-001 (`summary/project_overview.md`)

**All other docs (rules, modules) are version-independent.**

---

**Last verified:** 2025-01-17
