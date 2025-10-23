# Documentation Reference Guide

**Purpose:** How to maintain, update, and navigate this documentation system.

---

## 📚 **Documentation Philosophy**

### **Two Types of Documents:**

1. **CONCRETE (Immutable)** - These don't change once written
   - **Rules** (`rules/`) - Each rule is a specific, self-contained specification
   - **Modules** (`modules/`) - Each module is a specific implementation spec
   - **API Integration** (`api/`) - TopstepX API integration details

2. **VERSIONED (Evolving)** - These can have multiple versions
   - **Architecture** (`architecture/`) - System design evolves over time
   - **Summary** (`summary/`) - High-level overview may change

---

## 🔄 **When to Edit vs. Create New Version**

### **CONCRETE Documents (Rules, Modules, API):**

**When to EDIT (in-place):**
- Minor clarifications
- Typo fixes
- Adding missing details to existing logic
- Config example improvements
- Code snippet corrections

**When to CREATE NEW (add new file):**
- New rule (add `rules/new_rule_name.md` with new RULE-NNN ID)
- New module (add `modules/new_module_name.md` with new MOD-NNN ID)
- New API integration (add `api/new_integration.md` with new API-NNN ID)

**Example:**
```
❌ DON'T: Edit RULE-001 to completely change how MaxContracts works
✅ DO: Edit RULE-001 to clarify a config option or fix a typo
✅ DO: Create RULE-013 for a brand new rule
```

---

### **VERSIONED Documents (Architecture, Summary):**

**When to EDIT (in-place):**
- Current version (v2) needs minor updates
- Clarifications to existing design
- Adding details without changing core architecture

**When to CREATE NEW VERSION:**
- Major architectural changes (new modules, different data flow)
- Significant refactoring of system design
- Different technology stack decisions

**Naming Convention:**
```
architecture/
├── system_architecture_v1.md   (ARCH-V1) - Original design
├── system_architecture_v2.md   (ARCH-V2) - Current design ← EDIT THIS
└── system_architecture_v3.md   (ARCH-V3) - Future major refactor
```

**ALWAYS update `CURRENT_VERSION.md` pointer (see below)**

---

## 📂 **Folder Structure & Hierarchy**

```
docs/
├── ARCHITECTURE_INDEX.md          # Master navigation (update when adding files)
├── REFERENCE_GUIDE.md             # This file - how to maintain docs
├── CURRENT_VERSION.md             # Points to current architecture version
├── README.md                      # Quick start guide
│
├── architecture/                  # VERSIONED (can have v1, v2, v3...)
│   ├── system_architecture_v1.md  (ARCH-V1) - Historical
│   └── system_architecture_v2.md  (ARCH-V2) - CURRENT ⭐
│
├── api/                           # CONCRETE (specific integrations)
│   ├── topstepx_integration.md    (API-INT-001) - TopstepX integration & pipeline
│   └── authentication.md          (API-AUTH-001) - Future: auth details
│
├── rules/                         # CONCRETE (each rule is final spec)
│   ├── max_contracts.md           (RULE-001)
│   ├── max_contracts_per_instrument.md (RULE-002)
│   ├── daily_realized_loss.md     (RULE-003)
│   └── ... (RULE-004 to RULE-012)
│
├── modules/                       # CONCRETE (each module is final spec)
│   ├── enforcement_actions.md     (MOD-001)
│   ├── lockout_manager.md         (MOD-002)
│   ├── timer_manager.md           (MOD-003)
│   └── reset_scheduler.md         (MOD-004)
│
└── summary/
    └── project_overview.md        (SUM-001) - Can be updated as project evolves
```

---

## 🆔 **Document ID System**

| Prefix | Category | Versioning | Examples |
|--------|----------|------------|----------|
| **ARCH-VX** | Architecture | Versioned (v1, v2, v3...) | ARCH-V1, ARCH-V2 |
| **RULE-NNN** | Risk Rules | Immutable (001, 002, 003...) | RULE-001, RULE-013 |
| **MOD-NNN** | Modules | Immutable (001, 002, 003...) | MOD-001, MOD-005 |
| **API-XXX-NNN** | API Integration | Immutable (INT, AUTH, etc.) | API-INT-001, API-AUTH-001 |
| **SUM-NNN** | Summary | Can update (001, 002...) | SUM-001 |

---

## 📝 **How to Add New Documentation**

### **Adding a New Rule (RULE-NNN):**

1. **Identify next available ID:**
   - Check `rules/` folder, find highest number (e.g., RULE-012)
   - Next rule is RULE-013

2. **Create new file:**
   ```bash
   docs/rules/new_rule_name.md
   ```

3. **Use template header:**
   ```markdown
   ---
   doc_id: RULE-013
   version: 1.0
   last_updated: 2025-01-17
   dependencies: [MOD-001, MOD-002]
   enforcement_type: Trade-by-Trade | Hard Lockout | Timer Lockout
   ---
   ```

4. **Update `ARCHITECTURE_INDEX.md`:**
   - Add row to "Risk Rule Specifications" table

5. **Update `architecture/system_architecture_v2.md`:**
   - Add to `src/rules/` directory tree
   - Add to rule list if needed

**DON'T create RULE-001-v2.md - Rules are immutable specs**

---

### **Adding a New Module (MOD-NNN):**

1. **Identify next available ID:** (e.g., MOD-005)

2. **Create new file:**
   ```bash
   docs/modules/new_module_name.md
   ```

3. **Use template header:**
   ```markdown
   ---
   doc_id: MOD-005
   version: 1.0
   last_updated: 2025-01-17
   dependencies: []
   ---
   ```

4. **Update `ARCHITECTURE_INDEX.md`:**
   - Add row to "Reusable Module Specifications" table

5. **Update dependencies in rules that use this module**

---

### **Creating New Architecture Version:**

1. **Copy current version:**
   ```bash
   cp architecture/system_architecture_v2.md architecture/system_architecture_v3.md
   ```

2. **Update header in v3:**
   ```markdown
   ---
   doc_id: ARCH-V3
   version: 3.0
   last_updated: 2025-01-XX
   dependencies: [...]
   ---
   ```

3. **Make your changes to v3**

4. **Update `CURRENT_VERSION.md`:**
   ```markdown
   # Current Architecture Version

   **Active Version:** ARCH-V3
   **File:** `architecture/system_architecture_v3.md`
   **Date:** 2025-01-XX

   Previous versions (historical reference):
   - ARCH-V2: `architecture/system_architecture_v2.md`
   - ARCH-V1: `architecture/system_architecture_v1.md`
   ```

5. **Update `ARCHITECTURE_INDEX.md`:**
   - Update "PRIMARY REFERENCE" pointer to ARCH-V3

**KEEP old versions (v1, v2) for historical context**

---

## 🎯 **Version Management Strategy**

### **Current Version Pointer:**

**File:** `CURRENT_VERSION.md` (lives in `docs/`)

**Purpose:** Always points to the current architecture version

**Format:**
```markdown
# Current Architecture Version

**Active Version:** ARCH-V2
**File:** `architecture/system_architecture_v2.md`
**Last Updated:** 2025-01-17

---

## What Changed from Previous Version

### ARCH-V2 (Current)
- Added modular enforcement modules (MOD-001 to MOD-004)
- Detailed API integration pipeline
- Complete rule specifications (RULE-001 to RULE-012)

### ARCH-V1 (Historical)
- Original planning session notes
- Initial technology stack decisions
- Phase-based implementation approach

---

**Always reference ARCH-V2 for current system design.**
```

---

## 🔍 **Finding the Right Document**

### **For AI Assistants:**
```
"Read the current architecture" → Read CURRENT_VERSION.md → Points to ARCH-V2
"Read RULE-003" → docs/rules/daily_realized_loss.md
"Read MOD-001" → docs/modules/enforcement_actions.md
"Read API integration" → docs/api/topstepx_integration.md
```

### **For Developers:**
1. Start with **CURRENT_VERSION.md** to find active architecture
2. Browse **rules/** or **modules/** for specific components
3. Check **api/** for integration details
4. Consult **ARCHITECTURE_INDEX.md** for complete map

---

## ✅ **Checklist: Adding New Content**

### **New Rule:**
- [ ] Create `rules/rule_name.md` with next RULE-NNN ID
- [ ] Add header with dependencies
- [ ] Update `ARCHITECTURE_INDEX.md` table
- [ ] Update current architecture's directory tree

### **New Module:**
- [ ] Create `modules/module_name.md` with next MOD-NNN ID
- [ ] Add header with dependencies
- [ ] Update `ARCHITECTURE_INDEX.md` table
- [ ] Update rules that depend on this module

### **New Architecture Version:**
- [ ] Copy current version to new vN file
- [ ] Update doc_id to ARCH-VN
- [ ] Make architectural changes
- [ ] Update `CURRENT_VERSION.md` pointer
- [ ] Update `ARCHITECTURE_INDEX.md` primary reference
- [ ] Document what changed in CURRENT_VERSION.md

### **Small Edit to Existing Doc:**
- [ ] Make change in-place
- [ ] Update `last_updated` date in header
- [ ] No need to update ARCHITECTURE_INDEX (unless major change)

---

## 🚫 **What NOT to Do**

❌ **DON'T create versioned rules:** `rules/max_contracts_v2.md`
   → Rules are immutable specs. Create new rule with new ID instead.

❌ **DON'T delete old architecture versions:** Keep v1, v2, v3... for history

❌ **DON'T rename files without updating all references:**
   → Search all MDs for old filename before renaming

❌ **DON'T create duplicate IDs:** Always check highest existing ID first

❌ **DON'T forget to update CURRENT_VERSION.md** when creating new architecture

---

## 📌 **Summary**

| Type | Edit in Place? | Version? | Add New? |
|------|----------------|----------|----------|
| **Rules** | ✅ Minor edits | ❌ No versioning | ✅ New RULE-NNN |
| **Modules** | ✅ Minor edits | ❌ No versioning | ✅ New MOD-NNN |
| **API Docs** | ✅ Minor edits | ❌ No versioning | ✅ New API-XXX-NNN |
| **Architecture** | ✅ Current version | ✅ v1, v2, v3... | ✅ New vN |
| **Summary** | ✅ Updates | ⚠️ Rarely version | ➖ Usually just update |

---

**When in doubt:**
- Small change? → Edit in place
- Big refactor? → New version (for architecture) or new ID (for rules/modules)
- Always update `CURRENT_VERSION.md` when changing active architecture
