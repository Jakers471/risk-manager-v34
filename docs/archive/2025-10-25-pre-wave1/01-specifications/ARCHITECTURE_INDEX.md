# Risk Manager - Architecture Documentation Index

**Last Updated:** 2025-01-17
**Purpose:** Master navigation guide for all project documentation.

---

## 📖 How to Use This Index

**For AI Assistants:**
- Each document has a **unique Doc ID** for precise reference
- Reference docs by ID: *"Read ARCH-V2"* or *"Read RULE-003"*

**For Developers:**
- Start with **CURRENT_VERSION.md** to find active architecture version
- Browse folders by category (rules, modules, api)
- Check **REFERENCE_GUIDE.md** for how to maintain/update docs

---

## 🎯 Current Active References

**Quick Links to Current Versions:**

| What You Need | Doc ID | File |
|---------------|--------|------|
| **Current Architecture** | ARCH-V2 | `architecture/system_architecture_v2.md` |
| **API Integration** | API-INT-001 | `api/topstepx_integration.md` |
| **Project Overview** | SUM-001 | `summary/project_overview.md` |
| **How to Maintain Docs** | - | `REFERENCE_GUIDE.md` |
| **Version Pointer** | - | `CURRENT_VERSION.md` |

---

## 📚 Documentation Structure

### 🔄 **Meta Documentation (How-To Guides)**

| File | Purpose |
|------|---------|
| **ARCHITECTURE_INDEX.md** | This file - master navigation |
| **CURRENT_VERSION.md** | Points to current architecture version |
| **REFERENCE_GUIDE.md** | How to maintain, update, and add documentation |
| **README.md** | Quick start guide |

---

### 🏗️ **Architecture Documents** (VERSIONED)

| Doc ID | File | Status | Purpose |
|--------|------|--------|---------|
| **ARCH-V2** | `architecture/system_architecture_v2.md` | **CURRENT** ⭐ | Complete system design, directory structure, modules |
| **ARCH-V1** | `architecture/system_architecture_v1.md` | Historical | Original planning session notes |

**How to use:**
- **ARCH-V2 is current** - use this for implementation
- **ARCH-V1 is historical** - kept for context
- See **CURRENT_VERSION.md** for version status

---

### 🔌 **API Integration Documents** (CONCRETE)

| Doc ID | File | Purpose |
|--------|------|---------|
| **API-INT-001** | `api/topstepx_integration.md` | TopstepX API integration, event pipeline, data flow |

**Note:** API docs are **concrete** (don't version). Add new files for new integrations.

---

### 📋 **Risk Rule Specifications** (CONCRETE)

Each rule is a self-contained, immutable specification.

| Doc ID | Rule Name | File | Enforcement Type |
|--------|-----------|------|------------------|
| **RULE-001** | MaxContracts | `rules/max_contracts.md` | Trade-by-Trade |
| **RULE-002** | MaxContractsPerInstrument | `rules/max_contracts_per_instrument.md` | Trade-by-Trade |
| **RULE-003** | DailyRealizedLoss | `rules/daily_realized_loss.md` | Hard Lockout |
| **RULE-004** | DailyUnrealizedLoss | `rules/daily_unrealized_loss.md` | Hard Lockout |
| **RULE-005** | MaxUnrealizedProfit | `rules/max_unrealized_profit.md` | Hard Lockout |
| **RULE-006** | TradeFrequencyLimit | `rules/trade_frequency_limit.md` | Timer Lockout |
| **RULE-007** | CooldownAfterLoss | `rules/cooldown_after_loss.md` | Timer Lockout |
| **RULE-008** | NoStopLossGrace | `rules/no_stop_loss_grace.md` | Trade-by-Trade |
| **RULE-009** | SessionBlockOutside | `rules/session_block_outside.md` | Hard Lockout |
| **RULE-010** | AuthLossGuard | `rules/auth_loss_guard.md` | Hard Lockout |
| **RULE-011** | SymbolBlocks | `rules/symbol_blocks.md` | Hard Lockout |
| **RULE-012** | TradeManagement | `rules/trade_management.md` | Automation |

**Note:** Rules are **concrete** (don't version). Create RULE-013, RULE-014, etc. for new rules.

---

### 🔧 **Reusable Module Specifications** (CONCRETE)

Core modules shared across all rules.

| Doc ID | Module Name | File | Used By |
|--------|-------------|------|---------|
| **MOD-001** | Enforcement Actions | `modules/enforcement_actions.md` | All rules |
| **MOD-002** | Lockout Manager | `modules/lockout_manager.md` | RULE-003, 004, 005, 006, 007, 009, 010, 011 |
| **MOD-003** | Timer Manager | `modules/timer_manager.md` | RULE-006, 007, 009, MOD-002 |
| **MOD-004** | Reset Scheduler | `modules/reset_scheduler.md` | RULE-003, 004, 005 |

**Note:** Modules are **concrete** (don't version). Create MOD-005, MOD-006, etc. for new modules.

---

### 📊 **Summary Documents**

| Doc ID | File | Purpose |
|--------|------|---------|
| **SUM-001** | `summary/project_overview.md` | Complete project overview, high-level understanding |

---

## 🚀 Quick Start Guides

### **Scenario 1: Understanding the Full System**
```
1. Read CURRENT_VERSION.md (find current architecture)
2. Read SUM-001 (project overview)
3. Read ARCH-V2 (current architecture)
4. Browse rule files (RULE-001 to RULE-012) as needed
```

### **Scenario 2: Implementing a Specific Rule**
```
1. Read ARCH-V2 (understand architecture)
2. Read specific RULE-XXX (e.g., RULE-001)
3. Read MOD-001 (all rules use enforcement actions)
4. Read API-INT-001 (understand event flow)
```

### **Scenario 3: Understanding API Integration**
```
1. Read API-INT-001 (TopstepX integration)
2. Read ARCH-V2 (architecture context)
3. Reference specific rule files as needed
```

### **Scenario 4: Adding New Documentation**
```
1. Read REFERENCE_GUIDE.md (how to add/update docs)
2. Follow checklist for adding new rule/module
3. Update this file (ARCHITECTURE_INDEX.md) with new entry
```

---

## 📂 Folder Organization

```
docs/
├── ARCHITECTURE_INDEX.md           ← You are here
├── CURRENT_VERSION.md              ← Points to current architecture
├── REFERENCE_GUIDE.md              ← How to maintain docs
├── README.md                       ← Quick start
│
├── architecture/                   ← VERSIONED (v1, v2, v3...)
│   ├── system_architecture_v1.md   (ARCH-V1) - Historical
│   └── system_architecture_v2.md   (ARCH-V2) - CURRENT
│
├── api/                            ← CONCRETE (specific integrations)
│   └── topstepx_integration.md     (API-INT-001)
│
├── rules/                          ← CONCRETE (12 rule specs)
│   ├── max_contracts.md            (RULE-001)
│   ├── max_contracts_per_instrument.md (RULE-002)
│   └── ... (RULE-003 to RULE-012)
│
├── modules/                        ← CONCRETE (4 module specs)
│   ├── enforcement_actions.md      (MOD-001)
│   ├── lockout_manager.md          (MOD-002)
│   ├── timer_manager.md            (MOD-003)
│   └── reset_scheduler.md          (MOD-004)
│
└── summary/
    └── project_overview.md         (SUM-001)
```

---

## 🆔 Document ID Reference

| Prefix | Category | Versioning | Next Available ID |
|--------|----------|------------|-------------------|
| **ARCH-VX** | Architecture | Versioned (v1, v2, v3...) | ARCH-V3 |
| **RULE-NNN** | Risk Rules | Immutable (001, 002...) | RULE-013 |
| **MOD-NNN** | Modules | Immutable (001, 002...) | MOD-005 |
| **API-XXX-NNN** | API Integration | Immutable | API-INT-002 |
| **SUM-NNN** | Summary | Can update | SUM-002 |

---

## 📝 Documentation Standards

Each document contains:
- ✅ **Header with metadata** (Doc ID, version, dependencies)
- ✅ **Sharp, concise explanations** (AI-optimized, no fluff)
- ✅ **API requirements** (exact endpoints, payloads, events)
- ✅ **Config examples** (production-ready YAML)
- ✅ **Code examples** (implementation logic)
- ✅ **Test scenarios** (validation examples)

---

## 🔄 Version Management

**CONCRETE Docs (Rules, Modules, API):**
- Don't create versions (e.g., no RULE-001-v2)
- Edit in place for minor updates
- Create new ID for new rule/module (e.g., RULE-013)

**VERSIONED Docs (Architecture):**
- Can have multiple versions (ARCH-V1, ARCH-V2, ARCH-V3...)
- Keep all versions for historical reference
- Update CURRENT_VERSION.md when creating new version

See **REFERENCE_GUIDE.md** for complete version management strategy.

---

## 📌 Important Notes

- **ARCH-V2 is the current architecture** - use this for implementation
- **All rules depend on MOD-001** (enforcement actions)
- **Config examples are production-ready** - use as templates
- **CONCRETE docs don't change** - rules and modules are immutable specs
- **VERSIONED docs evolve** - architecture can have v3, v4, etc.

---

**When in doubt:**
1. Check **CURRENT_VERSION.md** for current architecture
2. Read **REFERENCE_GUIDE.md** for how to maintain docs
3. Start with **ARCH-V2** for system design
