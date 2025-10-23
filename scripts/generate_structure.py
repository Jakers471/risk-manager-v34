#!/usr/bin/env python3
"""
Generate Up-to-Date Project Structure Documentation

This script generates a current snapshot of the project structure.
Run this when you need to see or document the current file organization.

Usage:
    python scripts/generate_structure.py
    python scripts/generate_structure.py --output docs/current/STRUCTURE.md
"""

import argparse
from pathlib import Path
from datetime import datetime


def should_ignore(path: Path) -> bool:
    """Check if path should be ignored."""
    ignore_patterns = {
        '.git', '.venv', '__pycache__', '.pytest_cache',
        '.mypy_cache', 'node_modules', '*.pyc', '.DS_Store',
        'uv.lock', '.env'
    }

    # Check if any part of the path matches ignore patterns
    for part in path.parts:
        if part in ignore_patterns:
            return True
        if part.startswith('.') and part not in {'.github', '.env.example', '.gitignore', '.docs-structure'}:
            return True

    return False


def generate_tree(root: Path, prefix: str = "", max_depth: int = 4, current_depth: int = 0) -> list[str]:
    """Generate tree structure as list of strings."""
    if current_depth >= max_depth:
        return []

    lines = []

    try:
        items = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        items = [item for item in items if not should_ignore(item)]
    except PermissionError:
        return lines

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        next_prefix = "    " if is_last else "│   "

        # Add comment for important directories
        comment = ""
        if item.is_dir():
            if item.name == "docs":
                comment = "  # Documentation"
            elif item.name == "src":
                comment = "  # Source code"
            elif item.name == "tests":
                comment = "  # TDD test suite"
            elif item.name == "current":
                comment = "  # Active docs (check here first)"
            elif item.name == "rules":
                comment = "  # Risk rule implementations"

        lines.append(f"{prefix}{current_prefix}{item.name}{comment}")

        if item.is_dir() and current_depth < max_depth - 1:
            lines.extend(generate_tree(item, prefix + next_prefix, max_depth, current_depth + 1))

    return lines


def count_files(root: Path, extension: str = None) -> int:
    """Count files in directory tree."""
    count = 0
    for item in root.rglob("*"):
        if item.is_file() and not should_ignore(item):
            if extension is None or item.suffix == extension:
                count += 1
    return count


def generate_stats(root: Path) -> dict:
    """Generate project statistics."""
    return {
        "total_py_files": count_files(root / "src", ".py"),
        "total_test_files": count_files(root / "tests", ".py"),
        "total_docs": count_files(root / "docs", ".md"),
        "total_rules_implemented": count_files(root / "src" / "risk_manager" / "rules", ".py") - 1,  # Exclude __init__.py
    }


def generate_structure_doc(root: Path) -> str:
    """Generate complete structure documentation."""
    stats = generate_stats(root)

    doc = f"""# Project Structure - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**⚠️ This file is AUTO-GENERATED. Do not edit manually.**

**To regenerate**: `python scripts/generate_structure.py`

---

## Quick Stats

- **Source Files**: {stats['total_py_files']} Python files
- **Test Files**: {stats['total_test_files']} test files
- **Documentation**: {stats['total_docs']} markdown files
- **Rules Implemented**: {stats['total_rules_implemented']} of 12

---

## Project Tree

```
{root.name}/
"""

    tree_lines = generate_tree(root, "")
    for line in tree_lines:
        doc += line + "\n"

    doc += """```

---

## Key Directories

### `/src/risk_manager/`
**The main source code**

- `core/` - Core engine, manager, events
- `rules/` - Risk rule implementations (RULE-001 through RULE-012)
- `sdk/` - SDK integration layer (suite manager, event bridge)
- `cli/` - Command-line interfaces (planned)
- `config/` - Configuration management (planned)
- `state/` - State persistence (planned)

### `/docs/`
**All documentation**

- `current/` - **CHECK HERE FIRST** - Active, up-to-date documentation
  - `PROJECT_STATUS.md` - Current status and progress
  - `SDK_INTEGRATION_GUIDE.md` - How we use Project-X SDK
  - `TESTING_GUIDE.md` - TDD approach

- `dev-guides/` - Developer reference guides
  - `QUICK_REFERENCE.md` - Commands and common tasks

- `PROJECT_DOCS/` - Original specifications (pre-SDK)
  - 46 specification files
  - Written before SDK existed
  - See `INTEGRATION_NOTE.md` for how specs map to SDK

- `archive/` - Old versions (dated folders)

### `/tests/`
**TDD test suite**

- `conftest.py` - Shared fixtures and configuration
- `unit/` - Fast, isolated unit tests
- `integration/` - Slower integration tests (planned)

### `/config/`
**Configuration files**

- YAML config files (planned)
- Example configurations

### `/examples/`
**Usage examples**

- Sample scripts showing how to use the risk manager

---

## How to Use This File

**This file is a snapshot.** It will be outdated as soon as you create/move/delete files.

**Instead of reading this file, use:**

```bash
# See directory structure
ls -la
ls -R docs/

# See test structure
pytest --collect-only

# Count Python files
find src -name "*.py" | wc -l

# Find all rules
ls src/risk_manager/rules/

# See docs organization
tree docs/ -L 2
```

---

## Regeneration

This file is generated by `scripts/generate_structure.py`.

**Regenerate when:**
- Major reorganization
- Adding new directories
- Need snapshot for documentation
- Weekly status updates

**Don't regenerate for:**
- Small file changes
- Single file additions
- Every commit

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Script**: `scripts/generate_structure.py`
**Purpose**: Point-in-time snapshot of project structure
"""

    return doc


def main():
    parser = argparse.ArgumentParser(description="Generate project structure documentation")
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: print to stdout)",
        type=Path,
        default=None
    )
    parser.add_argument(
        "--max-depth", "-d",
        help="Maximum depth to traverse (default: 4)",
        type=int,
        default=4
    )

    args = parser.parse_args()

    # Get project root (parent of scripts directory)
    root = Path(__file__).parent.parent

    # Generate documentation
    doc = generate_structure_doc(root)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(doc)
        print(f"✅ Structure documentation written to: {args.output}")
    else:
        print(doc)


if __name__ == "__main__":
    main()
