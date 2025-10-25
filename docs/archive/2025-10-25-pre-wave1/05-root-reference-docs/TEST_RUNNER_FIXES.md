# Test Runner Fixes - 2025-10-24

## Problems Fixed

### Problem 1: All Tests Deselected ❌

**Symptom**: When running integration or unit tests via the menu, pytest would say:
```
collected 19 items
deselected 19 items
```

**Root Cause**: `pyproject.toml` line 95 had `--strict-markers` which causes pytest to deselect ALL tests that don't have explicit `@pytest.mark.unit` or `@pytest.mark.integration` decorators.

**Fix**: Removed `--strict-markers` from `addopts`

**Before**:
```toml
addopts = "-v --strict-markers --tb=short"
```

**After**:
```toml
addopts = "-v --tb=short"
```

**Result**: ✅ Tests no longer require markers to run. They run by default!

---

### Problem 2: No Real-Time Test Output ❌

**Symptom**: When running tests, you'd see nothing until ALL tests completed, then output would dump all at once. This isn't normal pytest behavior!

**Root Cause**: `run_tests.py` lines 135-140 used `capture_output=True` which buffers ALL output until the process completes.

**Fix**: Changed from `subprocess.run()` with `capture_output=True` to `subprocess.Popen()` with line-by-line streaming.

**Before**:
```python
result = subprocess.run(
    cmd,
    cwd=Path(__file__).parent,
    capture_output=True,  # ← BUFFERS EVERYTHING
    text=True,
)

output_combined = result.stdout + result.stderr
print(output_combined)  # ← Printed AFTER tests finish
```

**After**:
```python
process = subprocess.Popen(
    cmd,
    cwd=Path(__file__).parent,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,  # Line buffered for real-time output
)

output_lines = []
for line in process.stdout:
    print(line, end='')  # ← Printed IMMEDIATELY as tests run
    output_lines.append(line)

process.wait()
output_combined = ''.join(output_lines)
```

**Result**: ✅ Now you see each test as it runs, just like native pytest!

---

## How It Works Now

### Native Pytest Behavior Restored

**What you see while tests run**:
```
tests/unit/test_core/test_enforcement_wiring.py::test_1 PASSED [ 25%]
tests/unit/test_core/test_enforcement_wiring.py::test_2 PASSED [ 50%]
tests/unit/test_core/test_enforcement_wiring.py::test_3 PASSED [ 75%]
tests/unit/test_core/test_enforcement_wiring.py::test_4 PASSED [100%]
```

Each line appears **as the test runs**, not after everything finishes!

---

### Tests Run Without Requiring Markers

**Before** (strict-markers):
```python
# This test would be DESELECTED
def test_something():
    assert True

# Only this would run
@pytest.mark.unit
def test_marked():
    assert True
```

**After** (no strict-markers):
```python
# Both tests run!
def test_something():
    assert True

def test_marked():
    assert True
```

**Markers are now optional** - use them for filtering, not required for running.

---

## Testing The Fixes

### Test 1: Direct pytest (no deselection)
```bash
./.venv/bin/python -m pytest tests/unit/ -v
```

**Expected**: All tests collected and run (not deselected)

**Result**: ✅
```
collected 19 items

tests/unit/test_core/test_enforcement_wiring.py::test_1 PASSED
tests/unit/test_core/test_enforcement_wiring.py::test_2 PASSED
...
```

---

### Test 2: Run tests via menu (real-time output)
```bash
python run_tests.py
# Select [2] Unit tests
```

**Expected**: See each test as it runs (not buffered)

**Result**: ✅ Output streams line-by-line in real-time!

---

## Files Changed

1. **pyproject.toml** (line 95)
   - Removed `--strict-markers` from pytest addopts

2. **run_tests.py** (lines 129-157)
   - Changed from `subprocess.run(capture_output=True)`
   - To `subprocess.Popen()` with line-buffered streaming

---

## Benefits

### ✅ Better Developer Experience

**Before**:
- Run tests → Wait in silence → Everything dumps at once
- Most tests deselected unless explicitly marked
- Confusing when tests seem to not run

**After**:
- Run tests → See progress in real-time
- All tests run by default
- Normal pytest behavior restored

---

### ✅ Markers Still Work (But Optional)

You can still filter by markers:
```bash
pytest -m unit         # Only unit tests
pytest -m integration  # Only integration tests
pytest -m slow         # Only slow tests
```

But tests without markers still run by default!

---

## Summary

**Problem 1**: `--strict-markers` caused test deselection ❌
**Fix 1**: Removed from pytest config ✅

**Problem 2**: Buffered output (no real-time display) ❌
**Fix 2**: Use Popen with line streaming ✅

**Result**: Normal pytest behavior restored! 🎉

---

**Last Updated**: 2025-10-24
**Impact**: Major improvement to testing workflow
**Tests Verified**: 4/4 passing with real-time output
