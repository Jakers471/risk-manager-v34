# Scripts Directory

**Utility scripts for project maintenance and development.**

---

## Available Scripts

### `generate_structure.py`

**Purpose**: Generate up-to-date project structure documentation

**Why**: Hard-coded file trees in documentation go stale immediately. This script creates a snapshot when needed.

**Usage**:
```bash
# Print to stdout
python scripts/generate_structure.py

# Save to file
python scripts/generate_structure.py --output docs/current/STRUCTURE_SNAPSHOT.md

# Limit depth
python scripts/generate_structure.py --max-depth 3
```

**When to run**:
- ✅ Major reorganization
- ✅ Adding new directories
- ✅ Need snapshot for documentation
- ✅ Weekly status updates
- ❌ Small file changes
- ❌ Single file additions
- ❌ Every commit

**Output includes**:
- Project tree (respects .gitignore patterns)
- Quick stats (file counts, rules implemented)
- Key directory descriptions
- Commands for manual structure inspection

---

## Adding New Scripts

When you add a new script:

1. **Create the script** in this directory
2. **Make it executable**: `chmod +x scripts/your_script.py`
3. **Add shebang**: `#!/usr/bin/env python3`
4. **Add docstring** explaining purpose and usage
5. **Update this README** with script description
6. **Sync to WSL** if needed: `cp scripts/* ~/risk-manager-v34-wsl/scripts/`

---

## Script Guidelines

### Python Scripts

```python
#!/usr/bin/env python3
"""
Brief description of what this script does.

Usage:
    python scripts/my_script.py [args]
"""

import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="...")
    # Add arguments
    args = parser.parse_args()
    # Do work

if __name__ == "__main__":
    main()
```

### Shell Scripts

```bash
#!/usr/bin/env bash
# Brief description of what this script does

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script logic here
```

---

## Common Patterns

### File Tree Generation
See `generate_structure.py` for pattern

### Stats Collection
```python
def count_files(root: Path, extension: str = None) -> int:
    """Count files in directory tree."""
    count = 0
    for item in root.rglob("*"):
        if item.is_file() and not should_ignore(item):
            if extension is None or item.suffix == extension:
                count += 1
    return count
```

### Ignoring Patterns
```python
def should_ignore(path: Path) -> bool:
    """Check if path should be ignored."""
    ignore_patterns = {
        '.git', '.venv', '__pycache__', '.pytest_cache',
        '.mypy_cache', 'node_modules', '*.pyc', '.DS_Store'
    }
    for part in path.parts:
        if part in ignore_patterns:
            return True
    return False
```

---

## Future Script Ideas

- `validate_docs.py` - Check for broken links in documentation
- `check_rules.py` - Verify all 12 rules have specs and implementations
- `generate_test_coverage.py` - Generate detailed coverage reports
- `sync_envs.py` - Sync Windows ↔ WSL environments
- `check_dependencies.py` - Verify SDK version and dependencies
- `audit_project.py` - Complete project health check

---

**Last Updated**: 2025-10-23
**Maintainer**: Update this README when adding new scripts
