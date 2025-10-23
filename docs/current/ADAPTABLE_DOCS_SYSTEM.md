# Adaptable Documentation System

**Date**: 2025-10-23
**Status**: ✅ Implemented
**Problem Solved**: Hard-coded file trees and structures going stale

---

## The Problem

Previously, documentation files (especially CLAUDE.md) contained hard-coded:
- File trees showing project structure
- Progress tables with percentages
- Lists of implemented rules
- Test structure trees

**The issue**: These go stale immediately when files are added/moved/deleted.

---

## The Solution

**Reference-based documentation** instead of hard-coded structures.

### What Changed

#### Before (Hard-Coded)
```markdown
## Project Structure

```
risk-manager-v34/
├── CLAUDE.md
├── README.md
├── docs/
│   ├── current/
│   │   ├── PROJECT_STATUS.md
│   │   ├── SDK_INTEGRATION_GUIDE.md
│   │   └── TESTING_GUIDE.md
│   └── ...
```
```

**Problem**: As soon as you add a file, this is wrong.

#### After (Reference-Based)
```markdown
## Documentation Structure

**Key Locations** (use these paths):

### Active Documentation
- `docs/current/` - All current documentation
  - `PROJECT_STATUS.md` - Current status
  - `SDK_INTEGRATION_GUIDE.md` - SDK usage

**⚠️ Don't cache structure - use `ls` or `find`**
```

**Benefit**: Always points to the right place, never stale.

---

## Key Changes Made

### 1. Updated CLAUDE.md
**File**: `CLAUDE.md`

**Changes**:
- ✅ Added warning at top about adaptable documentation
- ✅ Removed hard-coded file tree (replaced with path references)
- ✅ Removed hard-coded progress table (points to PROJECT_STATUS.md)
- ✅ Removed hard-coded rule list (points to actual directories)
- ✅ Removed hard-coded test structure (instructs to use `pytest --collect-only`)
- ✅ Added reference to structure generation script

**New approach**:
```markdown
## ⚠️ IMPORTANT: Adaptable Documentation

**This file uses REFERENCES, not hard-coded structures.**

- ❌ DON'T rely on cached file trees or progress percentages
- ✅ DO use paths and check actual files for current state
- ✅ DO use `ls`, `find`, `pytest --collect-only`
- ✅ DO read `docs/current/PROJECT_STATUS.md` for latest progress
```

### 2. Created Structure Generation Script
**File**: `scripts/generate_structure.py`

**Purpose**: Generate up-to-date structure snapshots when needed

**Usage**:
```bash
# Print to stdout
python scripts/generate_structure.py

# Save to file
python scripts/generate_structure.py --output docs/current/STRUCTURE_SNAPSHOT.md
```

**Features**:
- Generates current project tree (respects .gitignore)
- Calculates stats (file counts, rules implemented)
- Adds comments for important directories
- Includes warning that output is a snapshot
- Provides alternative commands for live structure inspection

**When to use**:
- Major reorganization
- Weekly status updates
- Need snapshot for documentation
- NOT for every small change

### 3. Created Scripts README
**File**: `scripts/README.md`

**Purpose**: Document available scripts and how to add new ones

**Contents**:
- Available scripts
- Usage instructions
- Guidelines for adding new scripts
- Common patterns (file tree generation, stats collection)
- Future script ideas

---

## How to Use This System

### For Claude AI

**At start of every session**:
1. ✅ Read `CLAUDE.md` (references to what to read)
2. ✅ Read `docs/current/PROJECT_STATUS.md` (current progress)
3. ✅ Use `ls`, `find`, `pytest --collect-only` to see current structure
4. ❌ Don't cache file trees or progress percentages

**If you need structure snapshot**:
```bash
python scripts/generate_structure.py
```

**If you need to see tests**:
```bash
pytest --collect-only
```

**If you need to count files**:
```bash
find src -name "*.py" | wc -l
find tests -name "test_*.py" | wc -l
```

### For Humans

**To see current structure**:
```bash
# Quick view
ls -R docs/

# Detailed tree
tree docs/ -L 2

# Generate snapshot
python scripts/generate_structure.py

# Save snapshot
python scripts/generate_structure.py --output docs/current/STRUCTURE_SNAPSHOT.md
```

**To see progress**:
- Read `docs/current/PROJECT_STATUS.md` (source of truth)
- Don't rely on cached percentages elsewhere

**To see what's implemented**:
```bash
# Count Python files
find src -name "*.py" | wc -l

# List rules
ls src/risk_manager/rules/

# Count rules (exclude __init__.py)
ls src/risk_manager/rules/*.py | grep -v __init__ | wc -l
```

---

## Maintenance Guidelines

### What SHOULD Be in Documentation

✅ **Paths and references**:
```markdown
- `docs/current/PROJECT_STATUS.md` - Current status
- `src/risk_manager/rules/` - Rule implementations
```

✅ **Commands to get current info**:
```markdown
Use `ls docs/` to see documentation structure
Use `pytest --collect-only` to see tests
```

✅ **Pointers to source of truth**:
```markdown
For current progress, see docs/current/PROJECT_STATUS.md
```

### What SHOULD NOT Be in Documentation

❌ **Hard-coded file trees**:
```markdown
# BAD - goes stale immediately
docs/
├── current/
│   ├── file1.md
│   ├── file2.md
```

❌ **Hard-coded progress percentages**:
```markdown
# BAD - incorrect as soon as work is done
- Core: 70% complete
- Rules: 16% complete
```

❌ **Hard-coded lists of implemented features**:
```markdown
# BAD - needs manual update every time
- ✅ RULE-001
- ✅ RULE-002
- ⏳ RULE-003
```

---

## Files That Still Need Manual Updates

Some things can't be auto-generated and need manual maintenance:

### `docs/current/PROJECT_STATUS.md`
**Update when**: Complete major work, finish rules, implement features

**What to update**:
- Progress percentages
- ✅/❌ status indicators
- "What's missing" sections
- Next priorities

**How often**: End of each coding session with significant progress

### `CLAUDE.md`
**Update when**:
- Major architecture changes
- Documentation reorganization
- Next priority changes
- Milestone transitions (25% → 50%)

**What to update**:
- Overall status in header
- Next priority section
- Critical notes if architecture changes

**How often**: Rarely (only on major changes)

### `README.md`
**Update when**:
- New major features added
- Installation instructions change
- Dependencies change
- Usage examples change

**How often**: When actually necessary

---

## Testing the System

### Verify Clean Root
```bash
# Windows
ls *.md
# Should show: CLAUDE.md, README.md only

# WSL
wsl bash -c "ls *.md"
# Should show: CLAUDE.md, README.md only
```

### Verify Docs Structure
```bash
ls docs/
# Should show: current/, dev-guides/, archive/, PROJECT_DOCS/, STATUS.md, etc.

ls docs/current/
# Should show: PROJECT_STATUS.md, SDK_INTEGRATION_GUIDE.md, TESTING_GUIDE.md
```

### Test Structure Script
```bash
# In WSL
python scripts/generate_structure.py | head -30
# Should output current project tree
```

---

## Benefits

### For Claude AI
1. ✅ Always gets up-to-date information
2. ✅ No confusion from stale documentation
3. ✅ Clear commands to get current state
4. ✅ Can generate snapshots when needed

### For Humans
1. ✅ Documentation doesn't lie
2. ✅ Less maintenance burden
3. ✅ Can generate structure on demand
4. ✅ Clear where to find information

### For Project
1. ✅ Sustainable documentation system
2. ✅ Scales as project grows
3. ✅ Single source of truth (actual files)
4. ✅ Tools available when snapshots needed

---

## Examples

### Bad (Old Way)
```markdown
## Progress

- Core: 70% ✅
- Rules: 16% (2/12) ⏳
- CLI: 0% ❌
```

**Problem**: Immediately out of date after implementing RULE-003.

### Good (New Way)
```markdown
## Progress

**Check `docs/current/PROJECT_STATUS.md` for current progress.**

To count implemented rules:
```bash
ls src/risk_manager/rules/*.py | grep -v __init__ | wc -l
```
```

**Benefit**: Always accurate, no manual updates needed.

---

## Future Enhancements

### Possible Additions

1. **`validate_docs.py`** - Check for broken links
2. **`check_progress.py`** - Auto-calculate progress percentages
3. **`audit_project.py`** - Complete health check
4. **`generate_status.py`** - Auto-generate parts of PROJECT_STATUS.md

### Rules for New Scripts

When adding scripts that generate documentation:

1. ✅ **Always include timestamp** in generated output
2. ✅ **Always include warning** that it's auto-generated
3. ✅ **Always show regeneration command**
4. ✅ **Prefer generation scripts over cached docs**

---

## Summary

**Old Problem**: Hard-coded structures go stale immediately

**New Solution**:
- Reference-based documentation (paths, not trees)
- Scripts to generate snapshots when needed
- Commands to check current state
- Single source of truth (actual files)

**Result**: Sustainable, maintainable, accurate documentation system

---

**Created**: 2025-10-23
**Status**: ✅ Fully Implemented
**Next Review**: When adding major new documentation

---

## Quick Reference

**Need current structure?**
```bash
python scripts/generate_structure.py
```

**Need current progress?**
```bash
cat docs/current/PROJECT_STATUS.md
```

**Need current tests?**
```bash
pytest --collect-only
```

**Need file counts?**
```bash
find src -name "*.py" | wc -l
```

**That's it. Simple, accurate, maintainable.**
