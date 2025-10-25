# Testing Documentation

**Quick Navigation**

## Core Testing Guide
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - THE authoritative testing reference
  - TDD workflow and best practices
  - Running tests and interpreting results
  - Integration testing with AI agents
  - Performance benchmarking
  - Runtime testing overview

## Specialized Topics

### Runtime Validation
- **[RUNTIME_DEBUGGING.md](RUNTIME_DEBUGGING.md)** ⭐ NEW - Runtime reliability testing
  - Runtime Reliability Pack (5 capabilities)
  - Interactive debug menu [S][R][T][L][E][G]
  - 8-checkpoint validation system
  - Troubleshooting flowchart
  - Exit codes and log interpretation
  - Common failures and fixes

### AI Workflow
- **[WORKING_WITH_AI.md](WORKING_WITH_AI.md)** - AI-assisted development workflow
  - How agents use the test suite
  - Coordination patterns for swarms
  - Automated quality gates
  - Runtime debugging with AI (Workflow 11)

## Test Reports
- **`/test_reports/README.md`** - Test report documentation
  - Standard test report format
  - Runtime debug report format
  - AI integration patterns
  - Exit code reference

## Agent Guidelines
- **`/.claude/prompts/runtime-guidelines.md`** - For AI agents
  - Runtime testing protocols
  - Checkpoint validation patterns
  - Logging standards
  - Test requirements
  - Communication protocols

## External References
See also:
- `/tests/fixtures_reference.md` - Test fixture documentation
- `/tests/conftest.py` - Shared test configuration
- Test files in `/tests/unit/` and `/tests/integration/`

## API Contracts & Troubleshooting ⭐ NEW
- **`/SDK_API_REFERENCE.md`** - Actual API signatures (root directory)
  - Prevents test/code mismatches
  - Essential before writing tests
- **`/SDK_ENFORCEMENT_FLOW.md`** - Complete enforcement wiring
  - Helps understand integration points
- **`/TEST_RUNNER_FINAL_FIXES.md`** - Test runner behavior
  - Performance tips and known issues

---

## Testing Hierarchy

```
Testing Documentation
│
├── TESTING_GUIDE.md (Core reference)
│   ├── Unit testing
│   ├── Integration testing
│   ├── TDD workflow
│   └── Runtime testing overview
│
├── RUNTIME_DEBUGGING.md (Runtime validation)
│   ├── Runtime Reliability Pack
│   ├── 8-checkpoint system
│   ├── Debug menu usage
│   └── Troubleshooting guide
│
├── WORKING_WITH_AI.md (AI workflows)
│   ├── Testing with AI (Workflows 1-10)
│   └── Runtime debugging with AI (Workflow 11)
│
└── Related Resources
    ├── /test_reports/README.md (Report formats)
    └── /.claude/prompts/runtime-guidelines.md (Agent protocols)
```

---

**Last Updated:** 2025-10-23
**Status:** Single source of truth for testing
**New:** Runtime debugging documentation added
