# Quick Reference - Common Commands & Tasks

**Quick lookup for daily development tasks**

---

## 🚀 Getting Started

### Enter WSL Environment
```bash
# From Windows
wsl

# Navigate to project
cd ~/risk-manager-v34-wsl

# Verify you're in the right place
pwd
# Should show: /home/jakers/risk-manager-v34-wsl
```

---

## 🧪 Testing

### Run Tests
```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=risk_manager --cov-report=html

# Specific file
uv run pytest tests/unit/test_rules/test_daily_loss.py

# Specific test
uv run pytest tests/unit/test_rules/test_daily_loss.py::test_daily_loss_enforcement

# Only unit tests (fast)
uv run pytest tests/unit/

# Only integration tests (slow)
uv run pytest tests/integration/ -v

# Watch mode (re-run on changes)
uv run pytest-watch

# Stop on first failure
uv run pytest -x

# Show print statements
uv run pytest -s

# Verbose output
uv run pytest -v
```

---

## 🔌 Connection & Examples

### Test API Connection
```bash
uv run python test_connection.py
```

### Run Examples
```bash
# Basic usage
uv run python examples/01_basic_usage.py

# Advanced rules
uv run python examples/02_advanced_rules.py

# Multi-instrument
uv run python examples/03_multi_instrument.py

# Direct SDK usage
uv run python examples/04_sdk_integration.py
```

---

## 📦 Package Management

### Install Dependencies
```bash
# Install all dependencies
uv sync

# Install with dev dependencies
uv sync --all-extras

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name
```

### Update Dependencies
```bash
# Update all
uv sync --upgrade

# Update specific package
uv add package-name@latest
```

---

## 🔧 Code Quality

### Format Code
```bash
# Format all Python files
uv run ruff format .

# Format specific file
uv run ruff format src/risk_manager/core/manager.py
```

### Lint Code
```bash
# Lint all files
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Lint specific file
uv run ruff check src/risk_manager/core/manager.py
```

### Type Checking
```bash
# Check all files
uv run mypy src/

# Check specific file
uv run mypy src/risk_manager/core/manager.py
```

---

## 📝 Documentation

### View Documentation
```bash
# Main entry point
cat CLAUDE.md

# Current status
cat docs/current/PROJECT_STATUS.md

# SDK integration guide
cat docs/current/SDK_INTEGRATION_GUIDE.md

# Testing guide
cat docs/current/TESTING_GUIDE.md
```

### Edit Documentation
```bash
# Use your favorite editor
nano docs/current/PROJECT_STATUS.md
vim docs/current/IMPLEMENTATION_ROADMAP.md
code docs/current/SDK_INTEGRATION_GUIDE.md  # VS Code
```

---

## 🗂️ Project Structure

### Find Files
```bash
# All Python files
find src -name "*.py" -type f

# All test files
find tests -name "test_*.py" -type f

# All documentation
find docs -name "*.md" -type f

# Specific file
find . -name "suite_manager.py"
```

### Check Project Stats
```bash
# Count Python files
find src -name "*.py" | wc -l

# Count lines of code
find src -name "*.py" -exec wc -l {} + | tail -1

# Count tests
find tests -name "test_*.py" | wc -l
```

---

## 🔍 Searching Code

### Search for Text
```bash
# Search in all Python files
grep -r "RiskManager" src/

# Search with line numbers
grep -rn "async def" src/

# Case-insensitive search
grep -ri "TODO" src/

# Search in specific file type
grep -r "class.*Rule" src/ --include="*.py"
```

### Search for Files
```bash
# Find by name
find . -name "*manager*.py"

# Find by pattern
find src -name "test_*.py"

# Find recently modified
find src -name "*.py" -mtime -1  # Last 24 hours
```

---

## 📊 Git Operations

### Check Status
```bash
# What changed
git status

# What's staged
git diff --cached

# All changes
git diff
```

### Commit Changes
```bash
# Stage all changes
git add .

# Commit with message
git commit -m "Add daily loss rule implementation"

# Stage and commit
git commit -am "Update SDK integration guide"
```

### View History
```bash
# Recent commits
git log --oneline -10

# File history
git log -- src/rules/daily_loss.py

# Who changed what
git blame src/rules/daily_loss.py
```

---

## 🐍 Python REPL

### Interactive Python Shell
```bash
# Start Python REPL
uv run python

# Or ipython (if installed)
uv run ipython
```

```python
# In REPL - Quick tests
from risk_manager import RiskManager
from risk_manager.rules import DailyLossRule

# Test imports
import project_x_py
print(project_x_py.__version__)

# Check config
from risk_manager.core.config import RiskConfig
config = RiskConfig()
print(config.project_x_api_key[:20])
```

---

## 📋 Environment & Config

### Check Environment
```bash
# Python version
python --version

# UV version
uv --version

# Installed packages
uv run pip list

# Environment variables
env | grep PROJECT_X
```

### Edit Configuration
```bash
# Edit .env file
nano .env

# View current config
cat .env

# Test config loading
uv run python -c "from risk_manager.core.config import RiskConfig; print(RiskConfig())"
```

---

## 🔄 Common Workflows

### Adding a New Rule

```bash
# 1. Write test first
nano tests/unit/test_rules/test_new_rule.py

# 2. Run test (should fail)
uv run pytest tests/unit/test_rules/test_new_rule.py

# 3. Implement rule
nano src/risk_manager/rules/new_rule.py

# 4. Run test (should pass)
uv run pytest tests/unit/test_rules/test_new_rule.py

# 5. Run all tests
uv run pytest

# 6. Update docs
nano docs/current/PROJECT_STATUS.md
```

### Fixing a Bug

```bash
# 1. Write failing test that demonstrates bug
nano tests/unit/test_bug.py
uv run pytest tests/unit/test_bug.py  # Should fail

# 2. Fix the bug
nano src/risk_manager/path/to/file.py

# 3. Verify fix
uv run pytest tests/unit/test_bug.py  # Should pass

# 4. Run full suite
uv run pytest

# 5. Commit fix
git add .
git commit -m "Fix: description of bug fix"
```

---

## 🛠️ Development Setup

### First Time Setup
```bash
# 1. Clone/navigate to project
cd ~/risk-manager-v34-wsl

# 2. Install dependencies
uv sync

# 3. Set up environment
cp .env.example .env
nano .env  # Add your API keys

# 4. Test connection
uv run python test_connection.py

# 5. Run tests
uv run pytest
```

### Daily Workflow
```bash
# 1. Update code
git pull

# 2. Update dependencies
uv sync

# 3. Run tests
uv run pytest

# 4. Start coding
# ... make changes ...

# 5. Test changes
uv run pytest

# 6. Commit
git add .
git commit -m "Description"
```

---

## 📡 SDK Usage

### Quick SDK Test
```python
# test_sdk_quick.py
import asyncio
from project_x_py import TradingSuite

async def main():
    suite = await TradingSuite.create(instruments=["MNQ"])
    stats = await suite.get_stats()
    print(f"Account: {stats.account_id}")
    print(f"Balance: ${stats.balance:,.2f}")
    await suite.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

```bash
# Run it
uv run python test_sdk_quick.py
```

---

## 🚨 Troubleshooting

### Common Issues

#### Issue: Tests Failing
```bash
# Clear pytest cache
rm -rf .pytest_cache/

# Reinstall dependencies
uv sync --force

# Run single test with verbose output
uv run pytest tests/unit/test_file.py -vv -s
```

#### Issue: Import Errors
```bash
# Verify package installed
uv run python -c "import risk_manager; print('OK')"

# Check sys.path
uv run python -c "import sys; print(sys.path)"

# Reinstall in editable mode
uv sync
```

#### Issue: Connection Failed
```bash
# Check .env file
cat .env | grep PROJECT_X

# Test connection
uv run python test_connection.py

# Check SDK version
uv run python -c "import project_x_py; print(project_x_py.__version__)"
```

---

## 📞 Getting Help

### Check Documentation
```bash
# Read main docs
cat CLAUDE.md
cat docs/current/PROJECT_STATUS.md

# Search docs
grep -r "search term" docs/
```

### Check Code Examples
```bash
# See how it's used
grep -r "RiskManager" examples/

# See tests
grep -r "test_" tests/
```

---

## ⚡ Quick Tasks

### Add TODO
```bash
# Add TODO comment in code
# TODO: Implement daily reset scheduler

# Or use grep to find all TODOs
grep -rn "TODO" src/
```

### Generate Coverage Report
```bash
uv run pytest --cov=risk_manager --cov-report=html
# Then open htmlcov/index.html
```

### Run Specific Test Multiple Times
```bash
# Run 10 times (check for flaky tests)
for i in {1..10}; do uv run pytest tests/unit/test_file.py; done
```

---

**Last Updated**: 2025-10-23
**See Also**:
- `CLAUDE.md` - Main entry point
- `docs/current/TESTING_GUIDE.md` - Testing details
- `docs/current/SDK_INTEGRATION_GUIDE.md` - SDK usage
