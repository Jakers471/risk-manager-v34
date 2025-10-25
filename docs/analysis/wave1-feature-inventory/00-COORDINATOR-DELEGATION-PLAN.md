# Wave 1: Feature Discovery - Coordinator Delegation Plan

**Date**: 2025-10-25
**Coordinator**: Main Agent
**Working Directory**: /mnt/c/Users/jakers/Desktop/risk-manager-v34

---

## PHASE 1: DISCOVERY SUMMARY

### Total Scope Analysis

**Total Markdown Files**: 106 (excluding .venv and .pytest_cache)
- **.claude/ files**: 100+ (agent/command infrastructure - EXCLUDED from analysis)
- **Core Documentation**: 106 files requiring analysis

**Breakdown by Directory**:

1. **Root Level** (10 files)
   - CLAUDE.md, README.md, SDK_API_REFERENCE.md, SDK_ENFORCEMENT_FLOW.md
   - LOGGING_FLOW.md, SDK_LOGGING_IMPLEMENTATION.md, SDK_LOGGING_QUICK_REFERENCE.md
   - TEST_RUNNER_FINAL_FIXES.md, TEST_RUNNER_FIXES.md

2. **docs/PROJECT_DOCS/** (46 files)
   - rules/ - 12 files (RULE-001 through RULE-012)
   - projectx_gateway_api/ - 20 files (API documentation)
   - architecture/ - 2 files (system architecture v1 & v2)
   - modules/ - 4 files (enforcement, lockout, reset, timer)
   - api/ - 1 file (topstepx integration)
   - sessions/ - 1 file
   - summary/ - 1 file
   - Root files - 5 files (indexes, references, integration notes)

3. **docs/current/** (8 files)
   - PROJECT_STATUS.md, SDK_INTEGRATION_GUIDE.md, MULTI_SYMBOL_SUPPORT.md
   - RULE_CATEGORIES.md, RULES_TO_SDK_MAPPING.md, CONFIG_FORMATS.md
   - SECURITY_MODEL.md, ADAPTABLE_DOCS_SYSTEM.md

4. **docs/testing/** (4 files)
   - README.md, TESTING_GUIDE.md, RUNTIME_DEBUGGING.md, WORKING_WITH_AI.md

5. **docs/archive/** (11 files across multiple archive folders)
   - 2025-10-23-old-sessions/ - 5 files
   - 2025-10-23-testing-docs/ - 6 files
   - 2025-10-23/ - 4 files (duplicates)

6. **docs/dev-guides/** (3 files)
   - IMPLEMENTATION_SUMMARY.md, QUICK_REFERENCE.md, SECURITY_QUICK_REF.md

7. **docs/implementation/** (1 file)
   - plan_2025-10-23.md

8. **docs/progress/** (1 file)
   - phase_2-1_complete_2025-10-23.md

9. **docs/analysis/** (1 file - created by this process)
   - wave1-feature-inventory/00-COORDINATOR-WORKPLAN.md

10. **Other** (5 files)
    - docs/INDEX.md, docs/STATUS.md, docs/quickstart.md, docs/summary_2025-10-23.md
    - examples/README.md, scripts/README.md, test_reports/README.md, tests/fixtures/README.md

---

## PHASE 2: CATEGORIZATION STRATEGY

### Analysis Categories (8 Researchers)

**Category 1: Risk Rules Specifications** (12 files)
- All RULE-001 through RULE-012 specifications
- Core feature requirements for the system
- **Researcher**: Risk Rules Specialist

**Category 2: SDK & API Integration** (21 files)
- SDK integration guides (docs/current/)
- ProjectX Gateway API (20 files)
- TopstepX integration
- **Researcher**: SDK Integration Specialist

**Category 3: Architecture & System Design** (6 files)
- System architecture (v1 & v2)
- Modules (enforcement, lockout, timer, reset)
- Multi-symbol support
- **Researcher**: Architecture Specialist

**Category 4: Testing Infrastructure** (10 files)
- Testing guides (4 files in docs/testing/)
- Test runner documentation (2 files in root)
- Archived testing docs (6 files)
- Runtime debugging
- **Researcher**: Testing Specialist

**Category 5: Configuration & Security** (3 files)
- CONFIG_FORMATS.md
- SECURITY_MODEL.md
- Logging configurations
- **Researcher**: Security & Config Specialist

**Category 6: Current Implementation Status** (8 files)
- PROJECT_STATUS.md
- IMPLEMENTATION_SUMMARY.md
- Implementation plans & progress
- STATUS.md
- **Researcher**: Implementation Status Specialist

**Category 7: Developer Guides & Workflows** (6 files)
- CLAUDE.md (AI entry point)
- Dev guides (3 files)
- Quickstart, summary docs
- **Researcher**: Developer Experience Specialist

**Category 8: Root-Level Technical Docs** (7 files)
- SDK_API_REFERENCE.md
- SDK_ENFORCEMENT_FLOW.md
- SDK_LOGGING_* (3 files)
- README.md
- **Researcher**: Technical Reference Specialist

---

## PHASE 3: RESEARCHER ASSIGNMENTS

### Researcher 1: Risk Rules Specialist
**ID**: researcher-risk-rules
**Focus**: Complete risk rule specifications and requirements
**File Count**: 12 files

**Files to Analyze**:
1. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/01_max_contracts.md
2. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/02_max_contracts_per_instrument.md
3. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/03_daily_realized_loss.md
4. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/04_daily_unrealized_loss.md
5. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/05_max_unrealized_profit.md
6. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/06_trade_frequency_limit.md
7. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/07_cooldown_after_loss.md
8. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/08_no_stop_loss_grace.md
9. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/09_session_block_outside.md
10. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/10_auth_loss_guard.md
11. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/11_symbol_blocks.md
12. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/rules/12_trade_management.md

**Cross-Reference Files**:
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/RULE_CATEGORIES.md
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/RULES_TO_SDK_MAPPING.md

**Extract**:
- Feature ID and name for each rule
- Input requirements (what data needed)
- Processing logic (how rule evaluates)
- Output/enforcement actions
- Configuration parameters
- Edge cases and special conditions
- Dependencies on other rules or modules
- Version indicators or change notes

**Output File**:
`/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md`

---

### Researcher 2: SDK Integration Specialist
**ID**: researcher-sdk-integration
**Focus**: SDK integration patterns, API mappings, and external dependencies
**File Count**: 21 files

**Files to Analyze**:
1. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/SDK_INTEGRATION_GUIDE.md
2. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/INTEGRATION_NOTE.md
3. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/api/topstepx_integration.md
4-23. All 20 files in /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/projectx_gateway_api/:
   - account/search_account.md
   - getting_started/* (5 files)
   - market_data/* (4 files)
   - orders/* (5 files)
   - positions/* (3 files)
   - realtime_updates/realtime_data_overview.md
   - trades/search_trades.md

**Cross-Reference Files**:
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/RULES_TO_SDK_MAPPING.md
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/SDK_API_REFERENCE.md

**Extract**:
- SDK capabilities vs custom build requirements
- API endpoints and their purposes
- Real-time event subscriptions
- Data models and transformations
- Authentication & connection patterns
- Rate limits and constraints
- Version dependencies
- Integration patterns (what SDK handles vs what we build)

**Output File**:
`/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/analysis/wave1-feature-inventory/02-SDK-INTEGRATION-INVENTORY.md`

---

### Researcher 3: Architecture Specialist
**ID**: researcher-architecture
**Focus**: System design, component interactions, and architectural patterns
**File Count**: 6 files

**Files to Analyze**:
1. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/architecture/system_architecture_v1.md
2. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/architecture/system_architecture_v2.md
3. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/modules/enforcement_actions.md
4. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/modules/lockout_manager.md
5. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/modules/reset_scheduler.md
6. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/modules/timer_manager.md

**Cross-Reference Files**:
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/MULTI_SYMBOL_SUPPORT.md
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/SDK_ENFORCEMENT_FLOW.md

**Extract**:
- Component/module definitions
- Data flow patterns
- State management approaches
- Event-driven architecture details
- Module dependencies
- Async/concurrency patterns
- Version differences (v1 vs v2)
- Scalability considerations

**Output File**:
`/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/analysis/wave1-feature-inventory/03-ARCHITECTURE-INVENTORY.md`

---

### Researcher 4: Testing Specialist
**ID**: researcher-testing
**Focus**: Testing infrastructure, strategies, and runtime validation
**File Count**: 10 files

**Files to Analyze**:
1. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/testing/README.md
2. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/testing/TESTING_GUIDE.md
3. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/testing/RUNTIME_DEBUGGING.md
4. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/testing/WORKING_WITH_AI.md
5. /mnt/c/Users/jakers/Desktop/risk-manager-v34/TEST_RUNNER_FINAL_FIXES.md
6. /mnt/c/Users/jakers/Desktop/risk-manager-v34/TEST_RUNNER_FIXES.md
7. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/archive/2025-10-23-testing-docs/AI_ASSISTED_TESTING_WORKFLOW.md
8. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/archive/2025-10-23-testing-docs/RUNTIME_INTEGRATION_TESTING.md
9. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/archive/2025-10-23-testing-docs/SDK_TESTING_VISUAL_GUIDE.md
10. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/archive/2025-10-23-testing-docs/TDD_WORKFLOW_GUIDE.md

**Cross-Reference Files**:
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/test_reports/README.md

**Extract**:
- Testing pyramid structure (unit/integration/e2e)
- Runtime reliability pack features
- 8-checkpoint logging system
- Test runner menu capabilities
- TDD workflow patterns
- Mock strategies for SDK
- Runtime smoke test requirements
- Debugging workflows
- Test report formats

**Output File**:
`/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/analysis/wave1-feature-inventory/04-TESTING-INVENTORY.md`

---

### Researcher 5: Security & Config Specialist
**ID**: researcher-security-config
**Focus**: Security model, configuration management, and logging
**File Count**: 5 files

**Files to Analyze**:
1. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/SECURITY_MODEL.md
2. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/CONFIG_FORMATS.md
3. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/dev-guides/SECURITY_QUICK_REF.md
4. /mnt/c/Users/jakers/Desktop/risk-manager-v34/LOGGING_FLOW.md
5. /mnt/c/Users/jakers/Desktop/risk-manager-v34/SDK_LOGGING_IMPLEMENTATION.md

**Cross-Reference Files**:
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/SDK_LOGGING_QUICK_REFERENCE.md

**Extract**:
- Windows UAC security requirements
- Admin vs Trader access levels
- Configuration file formats (YAML structures)
- Security boundaries and protection mechanisms
- Logging checkpoint definitions
- Log file locations and rotation
- Configuration validation rules
- Encryption/protection requirements

**Output File**:
`/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/analysis/wave1-feature-inventory/05-SECURITY-CONFIG-INVENTORY.md`

---

### Researcher 6: Implementation Status Specialist
**ID**: researcher-implementation-status
**Focus**: Current build state, progress tracking, and completion status
**File Count**: 8 files

**Files to Analyze**:
1. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/PROJECT_STATUS.md
2. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/dev-guides/IMPLEMENTATION_SUMMARY.md
3. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/implementation/plan_2025-10-23.md
4. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/progress/phase_2-1_complete_2025-10-23.md
5. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/STATUS.md
6. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/summary_2025-10-23.md
7. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/CURRENT_VERSION.md
8. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/sessions/2025-10-19.md

**Extract**:
- Which features are implemented vs planned
- Completion percentages by component
- Known issues and blockers
- Recent changes and updates
- Phase/milestone definitions
- Version history
- Next priorities
- Implementation decisions made

**Output File**:
`/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/analysis/wave1-feature-inventory/06-IMPLEMENTATION-STATUS-INVENTORY.md`

---

### Researcher 7: Developer Experience Specialist
**ID**: researcher-developer-experience
**Focus**: Developer onboarding, workflows, and documentation navigation
**File Count**: 6 files

**Files to Analyze**:
1. /mnt/c/Users/jakers/Desktop/risk-manager-v34/CLAUDE.md
2. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/dev-guides/QUICK_REFERENCE.md
3. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/quickstart.md
4. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/INDEX.md
5. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/current/ADAPTABLE_DOCS_SYSTEM.md
6. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/README.md

**Cross-Reference Files**:
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/REFERENCE_GUIDE.md
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/ARCHITECTURE_INDEX.md

**Extract**:
- Onboarding workflows for developers
- AI assistant entry points and protocols
- Documentation navigation patterns
- Quick reference materials
- Common tasks and commands
- Tool usage guidelines
- Development environment setup
- Session management patterns

**Output File**:
`/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/analysis/wave1-feature-inventory/07-DEVELOPER-EXPERIENCE-INVENTORY.md`

---

### Researcher 8: Technical Reference Specialist
**ID**: researcher-technical-reference
**Focus**: API contracts, enforcement flows, and technical specifications
**File Count**: 7 files

**Files to Analyze**:
1. /mnt/c/Users/jakers/Desktop/risk-manager-v34/SDK_API_REFERENCE.md
2. /mnt/c/Users/jakers/Desktop/risk-manager-v34/SDK_ENFORCEMENT_FLOW.md
3. /mnt/c/Users/jakers/Desktop/risk-manager-v34/SDK_LOGGING_QUICK_REFERENCE.md
4. /mnt/c/Users/jakers/Desktop/risk-manager-v34/README.md
5. /mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/PROJECT_DOCS/summary/project_overview.md
6. /mnt/c/Users/jakers/Desktop/risk-manager-v34/examples/README.md
7. /mnt/c/Users/jakers/Desktop/risk-manager-v34/scripts/README.md

**Cross-Reference Files**:
- /mnt/c/Users/jakers/Desktop/risk-manager-v34/test_reports/README.md

**Extract**:
- API method signatures and contracts
- Enforcement action flows (step-by-step)
- Event type definitions
- Data model specifications
- Error handling patterns
- Example usage patterns
- Script utilities available
- Project overview and goals

**Output File**:
`/mnt/c/Users/jakers/Desktop/risk-manager-v34/docs/analysis/wave1-feature-inventory/08-TECHNICAL-REFERENCE-INVENTORY.md`

---

## PHASE 4: SPAWN COMMANDS

### Standard Researcher Prompt Template

Each researcher will receive this prompt structure:

```
You are RESEARCHER-{ID} for Wave 1: Feature Discovery.

**YOUR ROLE**: Read assigned documentation files and extract ALL feature specifications, design decisions, and technical requirements into a comprehensive inventory report.

**ASSIGNMENT**: {Category Name}

**FILES TO ANALYZE**:
{List of file paths}

**CROSS-REFERENCE FILES**:
{List of additional context files}

**EXTRACTION REQUIREMENTS**:

For EACH file you read:
1. **Document Metadata**:
   - File path
   - Last modified date (if visible)
   - Version indicators
   - Deprecation notes

2. **Feature Specifications**:
   - Feature IDs or names
   - Requirements and acceptance criteria
   - Input/output specifications
   - Configuration parameters
   - Dependencies

3. **Design Decisions**:
   - Architectural choices
   - Technology selections
   - Patterns and approaches
   - Rationale (when provided)

4. **Technical Details**:
   - Data models
   - API contracts
   - Event types
   - State management
   - Error handling

5. **Cross-Cutting Concerns**:
   - Security requirements
   - Performance considerations
   - Testing requirements
   - Monitoring/logging needs

6. **Conflicts & Inconsistencies**:
   - Multiple versions of same spec
   - Conflicting requirements
   - Deprecated vs current
   - Ambiguities needing clarification

**OUTPUT FORMAT**:

Create file: {output_file_path}

Structure:
# {Category Name} - Feature Inventory
## Metadata
- Researcher ID: {researcher_id}
- Files Analyzed: {count}
- Date: 2025-10-25

## Executive Summary
[2-3 paragraph overview of findings]

## Detailed Inventory

### [Feature/Component Name 1]
**Source**: {file_path}:{section}
**Feature ID**: {if applicable}
**Status**: [Specified/Implemented/Deprecated]
**Description**: {summary}
**Requirements**:
- {requirement 1}
- {requirement 2}
**Technical Details**:
- {detail 1}
**Dependencies**: {list}
**Notes**: {conflicts, questions, observations}

[Repeat for each feature/component]

## Cross-File Analysis
[Identify patterns, conflicts, gaps across files]

## Recommendations
[Suggest clarifications needed, conflicts to resolve]

## Appendix: File Inventory
[Table of all files analyzed with size, sections, key topics]

**IMPORTANT**:
- Read EVERY file completely
- Extract EVERY feature mention, no matter how small
- Note version differences carefully
- Flag ambiguities and conflicts
- Be thorough - this inventory feeds all future work

Begin analysis now.
```

---

## SPAWN EXECUTION PLAN

### Researcher 1: Risk Rules Specialist
```
Task ID: researcher-risk-rules
Priority: CRITICAL (core business logic)
Estimated Time: 45 minutes
Output: 01-RISK-RULES-INVENTORY.md
```

### Researcher 2: SDK Integration Specialist
```
Task ID: researcher-sdk-integration
Priority: CRITICAL (foundation layer)
Estimated Time: 60 minutes
Output: 02-SDK-INTEGRATION-INVENTORY.md
```

### Researcher 3: Architecture Specialist
```
Task ID: researcher-architecture
Priority: HIGH (system design)
Estimated Time: 30 minutes
Output: 03-ARCHITECTURE-INVENTORY.md
```

### Researcher 4: Testing Specialist
```
Task ID: researcher-testing
Priority: HIGH (quality assurance)
Estimated Time: 45 minutes
Output: 04-TESTING-INVENTORY.md
```

### Researcher 5: Security & Config Specialist
```
Task ID: researcher-security-config
Priority: HIGH (security critical)
Estimated Time: 30 minutes
Output: 05-SECURITY-CONFIG-INVENTORY.md
```

### Researcher 6: Implementation Status Specialist
```
Task ID: researcher-implementation-status
Priority: MEDIUM (tracking)
Estimated Time: 30 minutes
Output: 06-IMPLEMENTATION-STATUS-INVENTORY.md
```

### Researcher 7: Developer Experience Specialist
```
Task ID: researcher-developer-experience
Priority: MEDIUM (usability)
Estimated Time: 30 minutes
Output: 07-DEVELOPER-EXPERIENCE-INVENTORY.md
```

### Researcher 8: Technical Reference Specialist
```
Task ID: researcher-technical-reference
Priority: HIGH (API contracts)
Estimated Time: 30 minutes
Output: 08-TECHNICAL-REFERENCE-INVENTORY.md
```

---

## COORDINATION PLAN

### Phase 1: Parallel Spawn (Now)
- Spawn all 8 researchers simultaneously
- Each works independently on their assigned files
- Estimated completion: 60 minutes (longest researcher)

### Phase 2: Report Collection (After completion)
- Verify all 8 inventory files created
- Check for completeness and quality
- Identify any missing analysis

### Phase 3: Synthesis (Wave 2)
- Merge finder agent will process all 8 inventories
- Cross-reference findings
- Identify conflicts and gaps
- Create master feature registry

---

## SUCCESS CRITERIA

Each researcher must deliver:
- ✅ Complete inventory markdown file in correct location
- ✅ All assigned files analyzed
- ✅ Features extracted with full specifications
- ✅ Conflicts and inconsistencies flagged
- ✅ Cross-file patterns identified
- ✅ Recommendations for clarification

Total deliverables: 8 comprehensive inventory reports

---

## NEXT STEPS

1. **Coordinator reviews this plan**
2. **User approves delegation strategy**
3. **Spawn 8 researcher agents** (parallel execution)
4. **Monitor progress** (check file creation)
5. **Collect completed inventories**
6. **Proceed to Wave 2: Merge & Synthesis**

---

**STATUS**: READY TO SPAWN
**AWAITING**: User approval to execute
