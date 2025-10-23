# Test Reports Directory

**Automated test report storage for AI-assisted debugging**

---

## 📄 What's Here

Every time you run tests via `run_tests.py`, the output is automatically saved to:

- **`latest.txt`** - Always contains the most recent test run (overwritten each time)
- **`YYYY-MM-DD_HH-MM-SS_[passed|failed].txt`** - Timestamped archive of each run

---

## 🤖 AI Workflow

### When You Say: "Fix test errors"

**What happens**:
1. AI reads `test_reports/latest.txt`
2. AI identifies which tests failed
3. AI reads the failure tracebacks
4. AI fixes the code
5. You run tests again
6. Repeat until all tests pass ✅

**No need to copy/paste test output!**

---

## 📊 Report Format

Each report contains:

```
================================================================================
Risk Manager V34 - Test Report
================================================================================
Test Run: Unit tests only
Timestamp: 2025-10-23 14:32:15
Status: FAILED
Exit Code: 1
================================================================================

[Full pytest output with colors]

- Test results (passed/failed/skipped)
- Failure tracebacks
- Warnings
- Summary statistics
- Coverage data (if requested)

================================================================================
End of Report
================================================================================
```

---

## 🎯 Usage Examples

### Example 1: Run tests and auto-save report
```bash
# Interactive menu (auto-saves report)
python3 run_tests.py
# Choose option 1, 2, 3, etc.
```

### Example 2: View latest report
```bash
# Option 1: Via menu
python3 run_tests.py
# Choose option [r]

# Option 2: Direct read
cat test_reports/latest.txt
```

### Example 3: AI fixes errors
```
User: "fix test errors"

AI: [Reads test_reports/latest.txt]
AI: "I see 6 failures in test_pnl_tracker.py..."
AI: [Identifies issues]
AI: [Fixes code]
AI: "Fixed! Run tests again to verify."

User: [Runs tests via menu]
User: "all tests pass now!"
```

---

## 📝 Notes

- Reports are **gitignored** (not tracked in version control)
- Only `README.md` and `.gitkeep` are tracked
- Reports accumulate over time (delete old ones if needed)
- Each report includes full pytest output (colors preserved in file)

---

**TIP**: After running tests, you can immediately say "fix test errors" and the AI will know exactly where to look!
