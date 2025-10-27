# Session Resume Guide - For Claude AI

**Purpose**: Quick reference to resume this project in any future session

---

## 🚀 Quick Start (30 seconds)

### Where We Left Off
**Date**: 2025-10-23
**Status**: Foundation complete, SDK integrated, connection tested
**Next**: Build CLI system (Trader + Admin interfaces)

### Project in 3 Sentences
Risk Manager V34 is a real-time trading risk management system that monitors TopstepX accounts, enforces 12 configurable risk rules, and provides dual CLI interfaces (admin + trader). Foundation is complete (~25%), including core architecture, SDK integration, and 2 basic rules. Next priority: Build CLI system for configuration and monitoring.

---

## 📋 When User Says "Where Did We Leave Off?"

### Response Template
```
We last worked on Risk Manager V34 on 2025-10-23.

**What's Complete** ✅:
- Core architecture (manager, engine, events)
- SDK integration (Project-X-Py v3.5.9)
- API connection verified (TopstepX account: PRAC-V2-126244-84184528)
- 2 of 12 risk rules implemented
- WSL environment set up (~/risk-manager-v34-wsl)

**What's Next** ⏳:
- Build Trader CLI (view-only status interface)
- Build Admin CLI (password-protected configuration)
- YAML config system
- State persistence (SQLite)

**Progress**: ~25% complete

See CURRENT_STATE.md for details.
```

---

## 📖 Essential Reading Order

### First Session (Read These)
1. **`CURRENT_STATE.md`** (5 min) - Complete project status
2. **`PROJECT_STRUCTURE.md`** (3 min) - File tree & what's missing
3. **`ROADMAP.md`** (2 min) - Next steps prioritized

### If User Asks About Specific Topics
- **Architecture**: `docs/PROJECT_DOCS/architecture/system_architecture_v2.md`
- **Rules**: `docs/PROJECT_DOCS/rules/*.md` (12 rule specs)
- **Vision**: `docs/PROJECT_DOCS/summary/project_overview.md`
- **How We Got Here**: `STATUS.md` + `docs/summary_2025-10-23.md`

---

## 🔧 Technical Setup Quick Reference

### Working Environment
```
Location: ~/risk-manager-v34-wsl (WSL2 Ubuntu)
Python: 3.13.7
Package Manager: uv v0.9.5
Status: ✅ All dependencies installed, SDK working
```

### Windows Copy (Reference Only)
```
Location: C:\Users\jakers\Desktop\risk-manager-v34
Status: .env configured, docs editable
Use: Windows development, doc editing
Note: SDK won't install (uvloop incompatibility)
```

### Access WSL
```bash
# From Windows
wsl

# Navigate to project
cd ~/risk-manager-v34-wsl

# Run examples
uv run python examples/01_basic_usage.py

# Test connection
uv run python test_connection.py
```

---

## 📁 File Locations (Common Tasks)

### Read Implementation
```
Core: src/risk_manager/core/
SDK: src/risk_manager/sdk/
Rules: src/risk_manager/rules/
Examples: examples/
```

### Read Specifications
```
Overview: docs/PROJECT_DOCS/summary/project_overview.md
Architecture: docs/PROJECT_DOCS/architecture/system_architecture_v2.md
Rules: docs/PROJECT_DOCS/rules/*.md (12 files)
Modules: docs/PROJECT_DOCS/modules/*.md (4 files)
```

### Edit Documentation
```
Current State: CURRENT_STATE.md
Roadmap: ROADMAP.md
Structure: PROJECT_STRUCTURE.md
Status: STATUS.md
```

---

## 🎯 Common User Requests

### "What Have We Built?"
**Answer**: Foundation is complete (~25%):
- ✅ Core architecture (async event-driven)
- ✅ SDK integration (Project-X-Py)
- ✅ 2 risk rules (max position, per-instrument limits)
- ✅ Examples & comprehensive docs
- ❌ CLI interfaces (not started)
- ❌ State persistence (not started)
- ❌ 10 remaining rules (spec only)

See `CURRENT_STATE.md` for complete inventory.

---

### "What's Next?"
**Answer**: Phase 1 - Configuration & CLI (1-2 weeks):

**Option A** - Build Trader CLI (recommended first):
- File: `src/cli/trader/status_screen.py`
- Show: Real-time status, positions, P&L, lockouts
- Time: 3-4 days
- Priority: 🔴 Critical

**Option B** - Build YAML Config System:
- Files: `src/config/*.py`, `config/*.yaml`
- Enable: Rule configuration via YAML files
- Time: 2-3 days
- Priority: 🔴 Critical

See `ROADMAP.md` Phase 1 for details.

---

### "Show Me the Code"
**Most Important Files**:
```bash
# Main entry point
src/risk_manager/core/manager.py

# Rule evaluation
src/risk_manager/core/engine.py

# SDK integration
src/risk_manager/sdk/suite_manager.py

# Example usage
examples/01_basic_usage.py

# Spec for what's needed
docs/PROJECT_DOCS/architecture/system_architecture_v2.md
```

---

### "What Are We Trying To Build?"
**Vision** (from spec docs):

A Windows Service daemon that:
- Monitors TopstepX trading accounts in real-time
- Enforces 12 configurable risk rules automatically
- Provides **Admin CLI** (password-protected) for configuration
- Provides **Trader CLI** (view-only) for monitoring
- Persists state to SQLite (survives crashes)
- Runs as Windows Service (trader cannot stop it)
- Protects traders from account violations and emotional mistakes

See `docs/PROJECT_DOCS/summary/project_overview.md` for complete vision.

---

### "Run a Test"
```bash
# Enter WSL
wsl

# Navigate
cd ~/risk-manager-v34-wsl

# Connection test
uv run python test_connection.py

# Basic example
uv run python examples/01_basic_usage.py

# Multi-instrument
uv run python examples/03_multi_instrument.py
```

---

## 🔍 Project Status At-A-Glance

### Implemented (✅)
```
Core Architecture      ██████████████░░░░░░ 70%
SDK Integration        ████████████████████ 100%
Risk Rules             ███░░░░░░░░░░░░░░░░░ 16% (2/12)
Examples               ████████████████████ 100%
Documentation          ████████████████████ 96%
```

### Missing (❌)
```
CLI System             ░░░░░░░░░░░░░░░░░░░░ 0%
Config Management      ██░░░░░░░░░░░░░░░░░░ 10%
State Persistence      ░░░░░░░░░░░░░░░░░░░░ 0%
Enforcement System     ███░░░░░░░░░░░░░░░░░ 15%
Windows Service        ░░░░░░░░░░░░░░░░░░░░ 0%
Testing                █░░░░░░░░░░░░░░░░░░░ 5%
```

### Overall Progress
```
Total: ████░░░░░░░░░░░░░░░░ 25%
```

---

## 💡 Implementation Strategy

### Current Approach
1. ✅ Build solid foundation (async architecture, SDK integration)
2. 🔄 **Add user interfaces** (CLI for config & monitoring) ← YOU ARE HERE
3. ⏳ Add state persistence (SQLite for crash recovery)
4. ⏳ Complete all 12 risk rules
5. ⏳ Add Windows Service wrapper
6. ⏳ Comprehensive testing
7. ⏳ Production deployment

### Why This Order
- **Foundation first**: Solid architecture pays dividends
- **CLI next**: Enables configuration without code editing
- **Persistence after**: Requires config system
- **Rules incrementally**: One at a time, well-tested
- **Service last**: Wraps completed system

---

## 📊 Key Metrics

### Code Statistics
```
Production Code:   ~1,560 lines (of ~8,310 estimated)
Files Implemented: 19 of ~80 core files
Dependencies:      ✅ All installed (50 packages)
Test Coverage:     ~5% (connection test only)
```

### Time Estimates
```
Phase 1 (CLI & Config):     10-13 days
Phase 2 (Persistence):      8-11 days
Phase 3 (Enforcement):      3-4 days
Phase 4 (All Rules):        14-16 days
Phase 5 (Windows Service):  3-5 days
Phase 6 (Testing):          10-14 days

Total: 48-63 days (solo dev)
MVP:   ~4 weeks (limited scope)
```

---

## 🚨 Critical Notes

### Architecture Decision
- **Specs describe**: Windows Service, synchronous Python, config-driven
- **V34 implements**: Async Python, SDK-based, programmatic rules
- **Resolution**: Hybrid approach - async core + Windows Service wrapper

### WSL Requirement
- **Development**: Must use WSL (uvloop dependency)
- **Deployment**: Windows Service (production)
- **Current**: Developing in WSL, will add Service wrapper later

### Credentials
```
API Key: tj5F5k0jDY2p3EKC2N6K88fgotPEaNyBDpNOz8W5n7s=
Username: jakertrader
Account: PRAC-V2-126244-84184528
Status: ✅ Connected and verified
```

---

## 🎯 Next Actions (Specific Tasks)

### Task 1: Build Trader CLI Status Screen
**File**: `src/cli/trader/status_screen.py`
**Complexity**: Medium
**Time**: 3-4 hours
**Dependencies**: None (reads from RiskManager)

**Requirements**:
- Real-time status display (updates every second)
- Show positions, P&L, active rules
- Color-coded (green/yellow/red)
- Display lockout timers if active
- Use `rich` library for terminal UI

**Reference**: `docs/PROJECT_DOCS/architecture/system_architecture_v2.md` (lines 76-83)

---

### Task 2: Build YAML Config Loader
**File**: `src/config/loader.py`
**Complexity**: Low-Medium
**Time**: 2-3 hours
**Dependencies**: None

**Requirements**:
- Load `config/risk_config.yaml`
- Load `config/accounts.yaml`
- Validate with Pydantic
- Provide defaults
- Environment variable override

**Reference**: `docs/PROJECT_DOCS/architecture/system_architecture_v2.md` (lines 380-448)

---

### Task 3: Implement RULE-003 (Daily Realized Loss)
**File**: `src/rules/daily_realized_loss.py`
**Complexity**: Medium
**Time**: 1-2 hours
**Dependencies**: State persistence needed first

**Requirements**:
- Track daily realized P&L
- Trigger at loss limit (e.g., -$500)
- Close all positions + cancel orders
- Set lockout until reset time (5:00 PM ET)

**Reference**: `docs/PROJECT_DOCS/rules/03_daily_realized_loss.md`

---

## 📚 Recommended Reading Path (New Session)

### 5-Minute Quick Start
1. This file (`SESSION_RESUME.md`) - 2 min
2. `CURRENT_STATE.md` - Summary section - 3 min
3. Start coding!

### 15-Minute Deep Dive
1. `SESSION_RESUME.md` - 2 min
2. `CURRENT_STATE.md` - Full file - 7 min
3. `ROADMAP.md` - Phase 1 section - 3 min
4. `PROJECT_STRUCTURE.md` - Scan tree - 3 min

### 30-Minute Complete Context
1. All above - 15 min
2. `docs/PROJECT_DOCS/summary/project_overview.md` - 5 min
3. `docs/PROJECT_DOCS/architecture/system_architecture_v2.md` - 10 min

---

## 🔄 Update This File

**When to Update**:
- After completing a phase
- When switching focus areas
- At end of each session
- When project status changes significantly

**What to Update**:
- "Where We Left Off" section
- Progress percentages
- Next actions
- File locations (if structure changes)

---

## 🤝 Working With User

### User's Background
- Trader using TopstepX platform
- Wants automated risk protection
- Has comprehensive spec docs (PROJECT_DOCS)
- Appreciates detailed status updates

### User's Preferences
- **Communication**: Direct, technical, no fluff
- **Updates**: Show progress, explain what's done
- **Documentation**: Keep status docs current
- **Approach**: Build incrementally, test as we go

### When User Says "Go From Here"
1. Read `CURRENT_STATE.md` (5 min)
2. Ask which task to prioritize:
   - CLI (user interface)
   - Config system (YAML support)
   - State persistence (crash recovery)
   - Additional rules (risk protection)
3. Implement, test, document
4. Update `CURRENT_STATE.md` when done

---

## ✅ Session Checklist

### Start of Session
- [ ] Read `SESSION_RESUME.md` (this file)
- [ ] Read `CURRENT_STATE.md` - Summary section
- [ ] Understand where we left off
- [ ] Identify next task

### During Session
- [ ] Implement features incrementally
- [ ] Test as you build
- [ ] Keep user updated on progress
- [ ] Document new code

### End of Session
- [ ] Update `CURRENT_STATE.md` with progress
- [ ] Update `SESSION_RESUME.md` if needed
- [ ] Commit changes (git)
- [ ] Summary of what was accomplished

---

## 🎓 Key Learnings

### What Worked Well
1. **Comprehensive Specs**: 46 docs saved tons of time
2. **WSL Solution**: Bypassed Windows/uvloop issue elegantly
3. **SDK Integration**: Project-X-Py handles complexity
4. **Async Architecture**: Clean, scalable, modern
5. **Documentation First**: Specs before code prevents rework

### What Needs Attention
1. **CLI Missing**: Biggest gap, needed for usability
2. **No Persistence**: Can't recover from crashes yet
3. **Limited Rules**: Only 2 of 12 implemented
4. **No Testing**: Just connection test so far
5. **Not Service Yet**: Can't run as Windows daemon

---

**Last Updated**: 2025-10-23
**Next Session**: Start with Task 1 (Trader CLI) or Task 2 (Config Loader)
**Questions?**: Read `CURRENT_STATE.md` for comprehensive status
