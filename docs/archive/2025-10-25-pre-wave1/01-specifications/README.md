# Risk Manager - Documentation

**Last Updated:** 2025-01-17

---

## 🚀 Quick Start

**New to this project? Start here:**

1. **Read:** [`CURRENT_VERSION.md`](CURRENT_VERSION.md) - Find current architecture version
2. **Read:** [`summary/project_overview.md`](summary/project_overview.md) (SUM-001) - High-level understanding
3. **Read:** [`architecture/system_architecture_v2.md`](architecture/system_architecture_v2.md) (ARCH-V2) - **CURRENT ARCHITECTURE**
4. **Browse:** Rule files in [`rules/`](rules/) - Detailed specifications for each risk rule

---

## 📁 Documentation Structure

```
docs/
├── ARCHITECTURE_INDEX.md            ← Master navigation guide
├── CURRENT_VERSION.md               ← Points to current architecture (ARCH-V2)
├── REFERENCE_GUIDE.md               ← How to maintain/update docs
├── README.md                        ← This file
│
├── architecture/                    ← VERSIONED
│   ├── system_architecture_v1.md    (ARCH-V1) - Historical reference
│   └── system_architecture_v2.md    (ARCH-V2) - CURRENT ⭐
│
├── api/                             ← CONCRETE
│   └── topstepx_integration.md      (API-INT-001) - API integration & pipeline
│
├── rules/                           ← CONCRETE (12 rules)
│   ├── max_contracts.md             (RULE-001)
│   ├── max_contracts_per_instrument.md (RULE-002)
│   ├── daily_realized_loss.md       (RULE-003)
│   ├── ... (RULE-004 to RULE-012)
│
├── modules/                         ← CONCRETE (4 modules)
│   ├── enforcement_actions.md       (MOD-001)
│   ├── lockout_manager.md           (MOD-002)
│   ├── timer_manager.md             (MOD-003)
│   └── reset_scheduler.md           (MOD-004)
│
└── summary/
    └── project_overview.md          (SUM-001)
```

---

## 🎯 Document Types

### **VERSIONED Documents (Can Have v1, v2, v3...)**
- **Architecture** (`architecture/`) - System design evolves over time
  - Current: ARCH-V2 (`system_architecture_v2.md`)
  - Historical: ARCH-V1 (`system_architecture_v1.md`)

### **CONCRETE Documents (Immutable Specs)**
- **Rules** (`rules/`) - Each rule is a final, self-contained spec
- **Modules** (`modules/`) - Each module is a final implementation spec
- **API Integration** (`api/`) - TopstepX integration details

**Key Difference:**
- **VERSIONED:** Can create v3, v4, etc. for major refactors
- **CONCRETE:** Edit in place for minor updates, create new ID (RULE-013) for new rules

See [`REFERENCE_GUIDE.md`](REFERENCE_GUIDE.md) for complete maintenance strategy.

---

## 📖 Common Use Cases

### **I want to understand the overall system**
→ Read: **CURRENT_VERSION.md** → **SUM-001** → **ARCH-V2**

### **I want to implement a specific rule**
→ Read: **ARCH-V2** (architecture) → **RULE-XXX** (specific rule) → **MOD-001** (enforcement)

### **I want to understand how events flow through the system**
→ Read: **API-INT-001** (TopstepX integration & event pipeline)

### **I want to understand shared modules**
→ Read: **MOD-001**, **MOD-002**, **MOD-003**, **MOD-004**

### **I want historical context**
→ Read: **ARCH-V1** (original planning session)

### **I want to add new documentation**
→ Read: **REFERENCE_GUIDE.md** (how to add/update docs)

---

## 🔑 Key Principles

1. **ARCH-V2 is the current architecture** - use this for implementation
2. **All rules depend on MOD-001** (enforcement actions)
3. **Config examples are production-ready** - use as templates
4. **API requirements are exact** (endpoints, payloads, events)
5. **Files are AI-optimized** - sharp, concise, comprehensive

---

## 🚦 Phase 1 Implementation (MVP)

Start with these 3 rules:
1. **RULE-001** (MaxContracts)
2. **RULE-002** (MaxContractsPerInstrument)
3. **RULE-009** (SessionBlockOutside)

**Why these?**
- Cover core risk scenarios
- Different enforcement types (trade-by-trade vs. lockout)
- Test the full architecture end-to-end

---

## 🆔 Document IDs

Each document has a unique ID for AI assistant reference:

| Prefix | Category | Example |
|--------|----------|---------|
| **ARCH-VX** | Architecture | ARCH-V2 |
| **RULE-NNN** | Risk Rules | RULE-001, RULE-003 |
| **MOD-NNN** | Modules | MOD-001, MOD-002 |
| **API-XXX-NNN** | API Integration | API-INT-001 |
| **SUM-NNN** | Summary | SUM-001 |

**Usage:** Tell AI assistants: *"Read ARCH-V2"* or *"Read RULE-003 and MOD-001"*

---

## 📊 All 12 Risk Rules

| ID | Rule | Type |
|----|------|------|
| RULE-001 | MaxContracts | Trade-by-Trade |
| RULE-002 | MaxContractsPerInstrument | Trade-by-Trade |
| RULE-003 | DailyRealizedLoss | Hard Lockout |
| RULE-004 | DailyUnrealizedLoss | Hard Lockout |
| RULE-005 | MaxUnrealizedProfit | Hard Lockout |
| RULE-006 | TradeFrequencyLimit | Timer Lockout |
| RULE-007 | CooldownAfterLoss | Timer Lockout |
| RULE-008 | NoStopLossGrace | Trade-by-Trade |
| RULE-009 | SessionBlockOutside | Hard Lockout |
| RULE-010 | AuthLossGuard | Hard Lockout |
| RULE-011 | SymbolBlocks | Hard Lockout |
| RULE-012 | TradeManagement | Automation |

---

## 🔧 All 4 Core Modules

| ID | Module | Purpose |
|----|--------|---------|
| MOD-001 | Enforcement Actions | Close positions, cancel orders |
| MOD-002 | Lockout Manager | Lockout state management |
| MOD-003 | Timer Manager | Countdown timers |
| MOD-004 | Reset Scheduler | Daily reset logic |

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

## 🔄 Maintenance

**To add new content:**
- **New Rule:** Create `rules/new_rule_name.md` with RULE-013 ID
- **New Module:** Create `modules/new_module_name.md` with MOD-005 ID
- **New Architecture Version:** Copy ARCH-V2 → ARCH-V3, update `CURRENT_VERSION.md`

**See [`REFERENCE_GUIDE.md`](REFERENCE_GUIDE.md) for complete instructions.**

---

**When in doubt:**
1. Check [`CURRENT_VERSION.md`](CURRENT_VERSION.md) for current architecture
2. Check [`ARCHITECTURE_INDEX.md`](ARCHITECTURE_INDEX.md) for complete navigation
3. Check [`REFERENCE_GUIDE.md`](REFERENCE_GUIDE.md) for how to maintain docs
