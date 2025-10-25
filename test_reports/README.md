# Test Reports Directory

This directory contains automated test execution reports for AI analysis and debugging.

## Report Types

### Standard Test Reports

**Location:** `test_reports/`

**Format:**
- `latest.txt` - Most recent test run (always overwritten)
- `YYYY-MM-DD_HH-MM-SS_passed.txt` - Successful test runs
- `YYYY-MM-DD_HH-MM-SS_failed.txt` - Failed test runs

**Content:**
```
================================================================================
Risk Manager V34 - Test Report
================================================================================
Test Run: [Description]
Timestamp: YYYY-MM-DD HH:MM:SS
Status: PASSED/FAILED
Exit Code: 0-7
================================================================================

[Full test output with colors]

================================================================================
End of Report
================================================================================
```

**Usage:**
```bash
# AI reads latest report
"Read test_reports/latest.txt and fix failing tests"

# Browse historical reports
ls -lt test_reports/
```

### Runtime Debug Reports

**Location:** `debug_reports/`

**Format:**
- `YYYY-MM-DD_HH-MM-SS_debug.txt` - Comprehensive diagnostics

**Content:**
- System health status
- Runtime diagnostics
- API connectivity results
- Configuration validation
- E2E flow results
- Environment details
- Dependency versions
- Error stack traces

**Generation:**
```bash
python run_tests.py
# Select: [G] Generate Debug Report
```

**Usage:**
```bash
# AI analyzes debug report
"Read debug_reports/[latest].txt and assess deployment readiness"
```

## Report Structure

### Test Report Sections

1. **Header**
   - Test run description
   - Timestamp
   - Status (PASSED/FAILED)
   - Exit code

2. **Test Output**
   - Pytest execution output
   - Individual test results
   - Assertion failures
   - Error messages
   - Stack traces

3. **Summary**
   - Tests passed/failed count
   - Coverage percentage
   - Execution time

4. **Footer**
   - End marker
   - Next steps guidance

### Runtime Report Sections

1. **Executive Summary**
   - Overall status
   - Critical issues
   - Warnings
   - Exit code

2. **Checkpoint Results**
   - Checkpoint 1: Environment (PASS/FAIL)
   - Checkpoint 2: Configuration (PASS/FAIL/WARNING)
   - Checkpoint 3: Components (PASS/FAIL)
   - Checkpoint 4: API (PASS/FAIL)
   - Checkpoint 5: State (PASS/FAIL)
   - Checkpoint 6: Rules (PASS/FAIL)
   - Checkpoint 7: Events (PASS/FAIL)
   - Checkpoint 8: Cleanup (PASS/FAIL)

3. **Detailed Diagnostics**
   - Environment information
   - Dependency versions
   - Configuration values
   - API test results
   - Performance metrics

4. **Recommendations**
   - Required fixes
   - Optional improvements
   - Deployment readiness

## Exit Codes

Reports include exit codes indicating test status:

| Code | Status | Meaning | Action |
|------|--------|---------|--------|
| 0 | SUCCESS | All tests passed | Proceed |
| 1 | CONFIG_ERROR | Configuration invalid | Fix YAML files |
| 2 | RUNTIME_ERROR | Runtime failure | Fix code/environment |
| 3 | API_ERROR | API connectivity failed | Check credentials |
| 4 | STATE_ERROR | State management failed | Check data directory |
| 5 | DEPENDENCY_ERROR | Missing dependencies | Install packages |
| 6 | PERMISSION_ERROR | File permission denied | Fix permissions |
| 7 | TIMEOUT_ERROR | Operation timed out | Check resources |

## AI Integration

### Reading Reports

AI assistants can directly read test reports:

```bash
# Latest test results
"Read test_reports/latest.txt"

# Specific historical run
"Read test_reports/2025-10-23_14-30-45_failed.txt"

# Debug report
"Read debug_reports/2025-10-23_14-30-45_debug.txt"
```

### Analyzing Failures

AI can identify and fix failures:

```bash
# Analyze failures
"Read test_reports/latest.txt and explain what failed"

# Suggest fixes
"Read test_reports/latest.txt and suggest fixes"

# Create fix checklist
"Read test_reports/latest.txt and create a numbered fix list"
```

### Comparing Reports

AI can compare reports to identify regressions:

```bash
# Compare two runs
"Compare test_reports/2025-10-23_10-00-00_passed.txt vs latest.txt"

# Identify regressions
"What tests passed before but fail now?"

# Track progress
"Are we getting better or worse? Compare last 5 runs"
```

## Report Retention

**Automatic Cleanup:**
- Reports older than 30 days are archived
- Latest 100 reports are always kept
- Failed test reports are kept longer (90 days)

**Manual Cleanup:**
```bash
# Remove old reports
find test_reports/ -name "*.txt" -mtime +30 -delete

# Keep only latest 50
ls -t test_reports/*.txt | tail -n +51 | xargs rm
```

## Best Practices

### For Developers

1. **Always check latest.txt after test runs**
   ```bash
   cat test_reports/latest.txt
   ```

2. **Save failed run reports**
   ```bash
   cp test_reports/latest.txt test_reports/bug_123_reproduction.txt
   ```

3. **Compare before/after fixes**
   ```bash
   diff test_reports/before_fix.txt test_reports/after_fix.txt
   ```

### For AI Assistants

1. **Read reports before suggesting fixes**
   - Don't guess - read the actual error
   - Check full stack trace
   - Identify exact failure line

2. **Provide specific fixes**
   - Reference exact file paths
   - Quote exact error messages
   - Suggest exact code changes

3. **Verify fixes work**
   - Request rerun after changes
   - Compare new vs old report
   - Confirm exit code 0

## Runtime Report Format

### Example Runtime Debug Report

```
================================================================================
Risk Manager V34 - Runtime Debug Report
================================================================================
Generated: 2025-10-23 14:30:45
Environment: production
Exit Code: 0 (SUCCESS)
================================================================================

EXECUTIVE SUMMARY
-----------------
✓ System health: PASS
✓ Runtime diagnostics: PASS
✓ API connectivity: PASS
⚠ Configuration: WARNING (Using template config)
✓ E2E flow: PASS

Overall Status: READY (with warnings)
Deployment Risk: LOW

================================================================================
CHECKPOINT RESULTS
================================================================================

[1] ENVIRONMENT VALIDATION                                             [PASS]
    ✓ Python 3.12.1 detected
    ✓ All required packages installed (12/12)
    ✓ Directory structure verified
    ✓ File permissions correct
    Duration: 0.05s

[2] CONFIGURATION LOADING                                           [WARNING]
    ✓ YAML syntax valid
    ✓ Required fields present
    ✓ Value ranges validated
    ⚠ Using template config: config/accounts.yaml.template
    Duration: 0.12s

    Recommendation: Create production config file

[3] COMPONENT INITIALIZATION                                           [PASS]
    ✓ PnLTracker initialized
    ✓ StateManager initialized
    ✓ RuleEngine initialized (7 rules loaded)
    ✓ EventBus initialized
    Duration: 0.18s

[4] API CONNECTIVITY                                                   [PASS]
    ✓ Client initialized
    ✓ Authentication successful
    ✓ GET /accounts: 200 OK
    ✓ GET /positions: 200 OK
    ✓ Rate limiter configured (60 req/min)
    Duration: 0.45s

[5] STATE MANAGEMENT                                                   [PASS]
    ✓ State update successful
    ✓ State persisted to disk
    ✓ State recovered correctly
    ✓ No memory leaks detected
    Duration: 0.22s

[6] RULE EVALUATION                                                    [PASS]
    ✓ Rules loaded (7/7)
    ✓ Rule evaluation successful
    ✓ Breach detection working
    ✓ Actions triggered correctly
    Duration: 0.15s

[7] EVENT HANDLING                                                     [PASS]
    ✓ Event subscription working
    ✓ Event publishing working
    ✓ Event dispatch successful
    ✓ No event queue backlog
    Duration: 0.08s

[8] RESOURCE CLEANUP                                                   [PASS]
    ✓ Connections closed
    ✓ State saved
    ✓ Resources released
    ✓ No resource warnings
    Duration: 0.05s

================================================================================
DETAILED DIAGNOSTICS
================================================================================

System Information:
  OS: Linux 6.6.87.2-microsoft-standard-WSL2
  Python: 3.12.1
  Platform: linux

Dependencies:
  topstepx-sdk: 1.2.3
  pydantic: 2.10.5
  pyyaml: 6.0.2
  pytest: 8.4.2

Configuration:
  risk_config.yaml: VALID
  accounts.yaml: TEMPLATE (⚠ Warning)

Environment Variables:
  TOPSTEPX_API_KEY: Set (32 chars)
  TOPSTEPX_API_SECRET: Set (64 chars)
  ENVIRONMENT: production

Performance Metrics:
  Total execution time: 1.30s
  Memory usage: 45.2 MB
  CPU usage: 12%

================================================================================
RECOMMENDATIONS
================================================================================

REQUIRED ACTIONS:
  None - system is operational

WARNINGS:
  1. Using template configuration file
     - Create: config/accounts.yaml from template
     - Add production account IDs

OPTIONAL IMPROVEMENTS:
  1. Enable debug logging for production monitoring
  2. Set up automated health checks
  3. Configure alerting for rule breaches

DEPLOYMENT READINESS: ✓ READY
  - All critical checks passed
  - No blocking issues
  - Minor warnings present (non-critical)

================================================================================
End of Runtime Debug Report
================================================================================
```

## Related Documentation

- **Runtime Debugging Guide:** `/docs/testing/RUNTIME_DEBUGGING.md`
- **Testing Guide:** `/docs/testing/TESTING_GUIDE.md`
- **AI Workflow:** `/docs/testing/WORKING_WITH_AI.md`

---

**Directory Structure:**
```
test_reports/
├── README.md (this file)
├── latest.txt (most recent run)
├── 2025-10-23_14-30-45_passed.txt
├── 2025-10-23_14-15-22_failed.txt
└── ...

debug_reports/
├── 2025-10-23_14-30-45_debug.txt
└── ...
```

**Quick Commands:**
```bash
# View latest report
cat test_reports/latest.txt

# List all reports
ls -lt test_reports/

# Find failed runs
ls test_reports/*_failed.txt

# AI analysis
echo "Read test_reports/latest.txt and fix issues"
```

---

**Last Updated:** 2025-10-23
**Report Format Version:** 1.0
