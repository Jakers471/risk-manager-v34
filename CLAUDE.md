# CLAUDE.md - AI Assistant Entry Point

**READ THIS FIRST** - Every session starts here

---

## ⚠️ IMPORTANT: Adaptable Documentation

**This file uses REFERENCES, not hard-coded structures.**

- ❌ **DON'T** rely on cached file trees or progress percentages
- ✅ **DO** use paths and check actual files for current state
- ✅ **DO** use `ls`, `find`, `pytest --collect-only` to see structure
- ✅ **DO** read `docs/current/PROJECT_STATUS.md` for latest progress

**Reason**: Hard-coded structures go stale immediately. Always check the actual files.

---

## 🎯 Purpose

This file tells Claude AI exactly what to read and in what order to get up to speed on this project.

**Last Updated**: 2025-10-23
**Project**: Risk Manager V34
**Environment**: WSL2 Ubuntu (`~/risk-manager-v34-wsl`)

---

## 📖 Quick Start (First 2 Minutes)

### 1. Read These Files IN ORDER:

```
1. docs/current/PROJECT_STATUS.md          (2 min) - Current state & progress
2. docs/current/SDK_INTEGRATION_GUIDE.md   (3 min) - How we use Project-X SDK
3. docs/dev-guides/QUICK_REFERENCE.md      (1 min) - Commands & common tasks
```

**After reading these 3 files, you will know**:
- ✅ What's been built (25% complete)
- ✅ What the SDK handles for us
- ✅ What we still need to build
- ✅ Exactly where we left off
- ✅ What to do next

---

## 🔑 Key Understanding #1: SDK-First Approach

### CRITICAL CONTEXT

**The specs in `docs/PROJECT_DOCS/` were written BEFORE the Project-X SDK existed.**

At that time:
- We had to map everything to raw ProjectX Gateway API
- Manual WebSocket handling
- Manual state tracking
- Manual order/position management

**NOW we have the Project-X-Py SDK** which handles:
- ✅ WebSocket connections (SignalR)
- ✅ Real-time events (positions, orders, trades)
- ✅ Order management (place, cancel, modify)
- ✅ Position management (close, partially close)
- ✅ Account data & statistics
- ✅ Market data & indicators
- ✅ Auto-reconnection

### What This Means

**DON'T**: Reimplement what the SDK already does
**DO**: Use the SDK as foundation, add risk management on top

**Example**:
- ❌ OLD: Write custom SignalR listener from specs
- ✅ NEW: Use `TradingSuite` from SDK, wrap with risk logic

See `docs/current/SDK_INTEGRATION_GUIDE.md` for mapping.

---

## 🔐 Key Understanding #2: Windows UAC Security

### CRITICAL: NO CUSTOM PASSWORDS

**The system uses Windows UAC (User Account Control) for admin protection.**

**NO custom passwords stored. NO authentication database. Just Windows admin rights.**

### Why This Matters

The Risk Manager is designed to be **"virtually unkillable"** by the trader:

- ✅ Windows Service runs as LocalSystem (highest privilege)
- ✅ Trader CANNOT kill the service without Windows admin password
- ✅ Trader CANNOT edit configs (protected by Windows ACL)
- ✅ Trader CANNOT stop the service via Task Manager
- ✅ Admin CLI requires Windows elevation (UAC prompt)
- ✅ Only Windows admin password can override protection

**This is NOT a custom password system. This is OS-level security.**

### Two Access Levels

```
Admin CLI:  Right-click terminal → "Run as Administrator"
            → Windows UAC prompt → Enter Windows admin password
            → Full control (configure, unlock, stop service)

Trader CLI: Normal terminal (no elevation needed)
            → View-only access
            → See status, P&L, lockouts, logs
            → CANNOT modify anything
```

**See `docs/current/SECURITY_MODEL.md` for complete details.**

---

## 📁 Documentation Structure

**Key Documentation Locations** (use these paths, don't cache the structure):

### Active Documentation
- `docs/current/` - All current/active documentation
  - `PROJECT_STATUS.md` - Where we are now (ALWAYS check this first)
  - `SDK_INTEGRATION_GUIDE.md` - How to use SDK (READ THIS!)
  - `RULES_TO_SDK_MAPPING.md` - What SDK provides vs what we build
  - `SECURITY_MODEL.md` - Windows UAC security (CRITICAL!)
  - `TESTING_GUIDE.md` - TDD approach

### Developer Guides
- `docs/dev-guides/` - Developer reference guides
  - `QUICK_REFERENCE.md` - Commands & common tasks

### Original Specifications
- `docs/PROJECT_DOCS/` - Original specs (pre-SDK)
  - `INTEGRATION_NOTE.md` - Explains spec → SDK mapping
  - `rules/` - 12 risk rule specifications
  - `architecture/` - Original architecture docs

### Old Versions
- `docs/archive/` - Previous versions (dated folders)

### Tests
- `tests/` - TDD test suite
  - `conftest.py` - Pytest configuration
  - `unit/` - Unit tests
  - `integration/` - Integration tests

### Generate Current Structure
**Need a snapshot of the current file structure?**

```bash
# Generate structure documentation
python scripts/generate_structure.py

# Save to file
python scripts/generate_structure.py --output docs/current/STRUCTURE_SNAPSHOT.md
```

**⚠️ Don't hard-code file trees - use `ls` or `find` or the script above**

---

## 🚀 When User Says "Where Did We Leave Off?"

### Response Template:

```markdown
**Last Session**: 2025-10-23

**Status**: Foundation complete (25%), SDK integrated, connection verified

**What's Working** ✅:
- Core async architecture (manager, engine, events)
- SDK integration (Project-X-Py v3.5.9)
- API connected (account PRAC-V2-126244-84184528)
- 2 of 12 risk rules implemented
- Comprehensive test coverage setup ready

**What's Next** ⏳:
1. Build CLI system (Trader + Admin)
2. YAML config management
3. State persistence (SQLite)
4. Complete remaining 10 risk rules
5. Windows Service wrapper

**Current Priority**: Build Trader CLI (view-only status interface)

See: `docs/current/PROJECT_STATUS.md` for complete details
```

---

## 🔧 Common Tasks Reference

### Run Tests
```bash
wsl
cd ~/risk-manager-v34-wsl
uv run pytest
uv run pytest --cov  # With coverage
```

### Test API Connection
```bash
wsl
cd ~/risk-manager-v34-wsl
uv run python test_connection.py
```

### Run Examples
```bash
wsl
cd ~/risk-manager-v34-wsl
uv run python examples/01_basic_usage.py
```

### Check Project Status
```bash
# Read current status document
cat docs/current/PROJECT_STATUS.md

# See what's implemented
find src -name "*.py" -type f | wc -l

# Run full test suite
uv run pytest -v
```

---

## 📊 Progress at a Glance

**⚠️ For current progress, ALWAYS check: `docs/current/PROJECT_STATUS.md`**

That file contains:
- Up-to-date completion percentages
- What's implemented vs what's missing
- File-by-file inventory
- Next priorities

**Don't rely on cached progress data - it goes stale immediately.**

---

## 🎯 Next Implementation Task

### Option A: Build Trader CLI (Recommended)
**File**: `src/cli/trader/status_screen.py`
**Time**: 3-4 hours
**Impact**: High - immediate visibility
**Guide**: `docs/current/IMPLEMENTATION_ROADMAP.md` - Phase 1.2

### Option B: Set Up TDD Testing
**Files**: `tests/unit/`, `tests/conftest.py`
**Time**: 2-3 hours
**Impact**: High - enables safe development
**Guide**: `docs/current/TESTING_GUIDE.md`

### Option C: YAML Config System
**Files**: `src/config/*.py`, `config/*.yaml`
**Time**: 2-3 hours
**Impact**: High - enables configuration
**Guide**: `docs/current/IMPLEMENTATION_ROADMAP.md` - Phase 1.1

---

## 📚 Detailed Documentation

### For Complete Project Understanding
1. `docs/current/PROJECT_STATUS.md` - Complete inventory
2. `docs/current/PROJECT_STRUCTURE.md` - File tree
3. `docs/current/SDK_INTEGRATION_GUIDE.md` - How we use SDK
4. `docs/current/IMPLEMENTATION_ROADMAP.md` - What to build

### For Original Requirements
1. `docs/PROJECT_DOCS/summary/project_overview.md` - Vision
2. `docs/PROJECT_DOCS/architecture/system_architecture_v2.md` - Original design
3. `docs/PROJECT_DOCS/INTEGRATION_NOTE.md` - How specs map to SDK

### For Implementation
1. `docs/dev-guides/QUICK_REFERENCE.md` - Commands
2. `docs/current/TESTING_GUIDE.md` - TDD approach
3. `docs/dev-guides/CONTRIBUTING.md` - How to add features

---

## ⚠️ Critical Notes

### Architecture Clarification

**Original Specs** (`docs/PROJECT_DOCS/`):
- Written before Project-X SDK existed
- Describe manual API integration
- Direct WebSocket handling
- Custom state management

**Current Implementation** (V34):
- **SDK-First**: Project-X-Py handles heavy lifting
- **Risk Layer**: We add risk management on top
- **Async**: Modern async/await throughout
- **Event-Driven**: SDK events → Risk rules → Enforcement

### Key Decision
**Don't reimplement what SDK provides. Use SDK, add risk logic.**

---

## 🧪 Test-Driven Development

**We use TDD** - Tests written first, then implementation.

**Test Structure**: See `tests/` directory
- Use `pytest --collect-only` to see all available tests
- Use `ls -R tests/` to see current test structure

**Workflow**:
1. Write test first (it fails - RED)
2. Write minimal code to pass (GREEN)
3. Refactor (REFACTOR)
4. Repeat

**Complete guide**: `docs/current/TESTING_GUIDE.md`

---

## 🔄 Update This File When

- [ ] Major architecture changes
- [ ] Documentation reorganization
- [ ] New critical files added
- [ ] Progress milestones (25% → 50% → etc.)
- [ ] Next priority changes

---

## ✅ Session Checklist

### At Start of Session
- [ ] Read `CLAUDE.md` (this file)
- [ ] Read `docs/current/PROJECT_STATUS.md`
- [ ] Read `docs/current/SDK_INTEGRATION_GUIDE.md`
- [ ] Check what tests exist (`pytest --collect-only`)
- [ ] Understand current priority

### During Session
- [ ] Write tests first (TDD)
- [ ] Use SDK where possible
- [ ] Document as you build
- [ ] Keep `PROJECT_STATUS.md` updated

### End of Session
- [ ] Run full test suite
- [ ] Update `docs/current/PROJECT_STATUS.md`
- [ ] Archive old docs if major changes
- [ ] Git commit with clear message

---

## 🎓 Understanding the Project in 5 Minutes

**What**: Trading risk manager for TopstepX futures accounts
**Why**: Prevent account violations, automate risk enforcement
**How**: SDK handles trading, we add risk rules on top

**12 Risk Rules**: See `docs/PROJECT_DOCS/rules/` for specifications
- Check `src/risk_manager/rules/` to see which are implemented
- Check `docs/current/PROJECT_STATUS.md` for completion status

**Tech Stack**:
- Python 3.13 async
- Project-X-Py SDK v3.5.9 (handles all trading)
- Pydantic (config/validation)
- SQLite (state persistence - planned)
- pytest (TDD testing)
- Rich + Typer (CLI - planned)

---

## 💡 If You're Confused

**Read in this exact order**:
1. This file (`CLAUDE.md`)
2. `docs/current/SDK_INTEGRATION_GUIDE.md` - Understand SDK-first approach
3. `docs/current/PROJECT_STATUS.md` - See what's done
4. `docs/current/IMPLEMENTATION_ROADMAP.md` - See what's next

**Still confused?**
- Look at `examples/01_basic_usage.py` - See it working
- Run `uv run python test_connection.py` - Verify it works
- Read `docs/PROJECT_DOCS/INTEGRATION_NOTE.md` - Understand spec history

---

**Last Updated**: 2025-10-23
**Next Update**: After documentation reorganization complete
**Maintainer**: Update this when project structure changes significantly

---

## 🚀 Ready to Code?

**Quick Start**:
```bash
# 1. Enter WSL
wsl

# 2. Navigate to project
cd ~/risk-manager-v34-wsl

# 3. Read status
cat docs/current/PROJECT_STATUS.md

# 4. Pick a task from IMPLEMENTATION_ROADMAP.md

# 5. Write test first
# Create test in tests/unit/

# 6. Implement feature
# Create code in src/

# 7. Run tests
uv run pytest

# 8. Update PROJECT_STATUS.md when done
```

**Let's build! 🛡️**
