# Wave 1: Feature Discovery - Coordinator Work Plan

**Generated**: 2025-10-25
**Working Directory**: /mnt/c/Users/jakers/Desktop/risk-manager-v34
**Total Markdown Files**: 88 (excluding .venv, .pytest_cache, .claude)

---

## Phase 1: Discovery Results

### File Categorization

#### Category 1: Risk Rules (12 files)
**Domain**: Core risk rule specifications
- ./docs/PROJECT_DOCS/rules/01_max_contracts.md
- ./docs/PROJECT_DOCS/rules/02_max_contracts_per_instrument.md
- ./docs/PROJECT_DOCS/rules/03_daily_realized_loss.md
- ./docs/PROJECT_DOCS/rules/04_daily_unrealized_loss.md
- ./docs/PROJECT_DOCS/rules/05_max_unrealized_profit.md
- ./docs/PROJECT_DOCS/rules/06_trade_frequency_limit.md
- ./docs/PROJECT_DOCS/rules/07_cooldown_after_loss.md
- ./docs/PROJECT_DOCS/rules/08_no_stop_loss_grace.md
- ./docs/PROJECT_DOCS/rules/09_session_block_outside.md
- ./docs/PROJECT_DOCS/rules/10_auth_loss_guard.md
- ./docs/PROJECT_DOCS/rules/11_symbol_blocks.md
- ./docs/PROJECT_DOCS/rules/12_trade_management.md

#### Category 2: SDK/API Documentation (20 files)
**Domain**: ProjectX Gateway API specifications (pre-SDK era)
- ./docs/PROJECT_DOCS/projectx_gateway_api/getting_started/authenticate_api_key.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/getting_started/connection_urls.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/getting_started/placing_first_order.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/getting_started/rate_limits.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/getting_started/validate_session.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/account/search_account.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/market_data/list_available_contracts.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/market_data/retrieve_bars.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/market_data/search_contract_by_id.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/market_data/search_contracts.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/orders/cancel_order.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/orders/modify_order.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/orders/place_order.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/orders/search_open_orders.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/orders/search_orders.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/positions/close_positions.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/positions/partially_close_positions.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/positions/search_positions.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/realtime_updates/realtime_data_overview.md
- ./docs/PROJECT_DOCS/projectx_gateway_api/trades/search_trades.md

#### Category 3: Architecture & Modules (7 files)
**Domain**: System architecture and core module specifications
- ./docs/PROJECT_DOCS/architecture/system_architecture_v1.md
- ./docs/PROJECT_DOCS/architecture/system_architecture_v2.md
- ./docs/PROJECT_DOCS/modules/enforcement_actions.md
- ./docs/PROJECT_DOCS/modules/lockout_manager.md
- ./docs/PROJECT_DOCS/modules/reset_scheduler.md
- ./docs/PROJECT_DOCS/modules/timer_manager.md
- ./docs/PROJECT_DOCS/api/topstepx_integration.md

#### Category 4: Current/Active Documentation (8 files)
**Domain**: Latest specifications and status
- ./docs/current/ADAPTABLE_DOCS_SYSTEM.md
- ./docs/current/CONFIG_FORMATS.md
- ./docs/current/MULTI_SYMBOL_SUPPORT.md
- ./docs/current/PROJECT_STATUS.md
- ./docs/current/RULES_TO_SDK_MAPPING.md
- ./docs/current/RULE_CATEGORIES.md
- ./docs/current/SDK_INTEGRATION_GUIDE.md
- ./docs/current/SECURITY_MODEL.md

#### Category 5: Testing Documentation (10 files)
**Domain**: Testing guides, methodologies, and runtime debugging
- ./docs/testing/README.md
- ./docs/testing/RUNTIME_DEBUGGING.md
- ./docs/testing/TESTING_GUIDE.md
- ./docs/testing/WORKING_WITH_AI.md
- ./docs/archive/2025-10-23-testing-docs/AI_ASSISTED_TESTING_WORKFLOW.md
- ./docs/archive/2025-10-23-testing-docs/README.md
- ./docs/archive/2025-10-23-testing-docs/RUNTIME_INTEGRATION_TESTING.md
- ./docs/archive/2025-10-23-testing-docs/SDK_TESTING_VISUAL_GUIDE.md
- ./docs/archive/2025-10-23-testing-docs/TDD_WORKFLOW_GUIDE.md
- ./docs/archive/2025-10-23-testing-docs/TESTING_METHODOLOGY_ANALYSIS.md

#### Category 6: Implementation & Progress (2 files)
**Domain**: Implementation plans and progress tracking
- ./docs/implementation/plan_2025-10-23.md
- ./docs/progress/phase_2-1_complete_2025-10-23.md

#### Category 7: Root Documentation (9 files)
**Domain**: Critical entry points and SDK integration guides
- ./CLAUDE.md
- ./README.md
- ./SDK_API_REFERENCE.md
- ./SDK_ENFORCEMENT_FLOW.md
- ./SDK_LOGGING_IMPLEMENTATION.md
- ./SDK_LOGGING_QUICK_REFERENCE.md
- ./LOGGING_FLOW.md
- ./TEST_RUNNER_FINAL_FIXES.md
- ./TEST_RUNNER_FIXES.md

#### Category 8: Archive (Old Sessions) (9 files)
**Domain**: Historical documentation (archived 2025-10-23)
- ./docs/archive/2025-10-23-old-sessions/CURRENT_STATE.md
- ./docs/archive/2025-10-23-old-sessions/PROJECT_STRUCTURE.md
- ./docs/archive/2025-10-23-old-sessions/README.md
- ./docs/archive/2025-10-23-old-sessions/ROADMAP.md
- ./docs/archive/2025-10-23-old-sessions/SESSION_RESUME.md
- ./docs/archive/2025-10-23/CURRENT_STATE.md
- ./docs/archive/2025-10-23/PROJECT_STRUCTURE.md
- ./docs/archive/2025-10-23/ROADMAP.md
- ./docs/archive/2025-10-23/SESSION_RESUME.md

#### Category 9: Dev Guides & Misc (7 files)
**Domain**: Developer guides, quick references, and summaries
- ./docs/dev-guides/IMPLEMENTATION_SUMMARY.md
- ./docs/dev-guides/QUICK_REFERENCE.md
- ./docs/dev-guides/SECURITY_QUICK_REF.md
- ./docs/INDEX.md
- ./docs/STATUS.md
- ./docs/quickstart.md
- ./docs/summary_2025-10-23.md

#### Category 10: PROJECT_DOCS Meta (4 files)
**Domain**: Documentation navigation and context
- ./docs/PROJECT_DOCS/ARCHITECTURE_INDEX.md
- ./docs/PROJECT_DOCS/CURRENT_VERSION.md
- ./docs/PROJECT_DOCS/INTEGRATION_NOTE.md
- ./docs/PROJECT_DOCS/README.md
- ./docs/PROJECT_DOCS/REFERENCE_GUIDE.md
- ./docs/PROJECT_DOCS/summary/project_overview.md
- ./docs/PROJECT_DOCS/sessions/2025-10-19.md

---

## Phase 2: Work Distribution Plan

### Researcher Agent Assignments

#### Researcher 1: Risk Rules Specialist
**Assignment**: Category 1 - All 12 risk rule specifications
**Files**: 12
**Focus**: Extract all rule specifications, parameters, enforcement actions, triggers
**Output Section**: 01-RISK-RULES-INVENTORY.md

#### Researcher 2: SDK/API Specialist
**Assignment**: Category 2 - ProjectX Gateway API docs (20 files)
**Files**: 20
**Focus**: API endpoints, authentication, rate limits, real-time updates
**Output Section**: 02-SDK-API-INVENTORY.md

#### Researcher 3: Architecture Specialist
**Assignment**: Category 3 - Architecture & Modules (7 files)
**Files**: 7
**Focus**: System architecture (v1 vs v2), module specifications, enforcement, lockout, timers
**Output Section**: 03-ARCHITECTURE-MODULES-INVENTORY.md

#### Researcher 4: Testing Specialist
**Assignment**: Category 5 - Testing Documentation (10 files)
**Files**: 10
**Focus**: Testing methodologies, runtime debugging, AI workflows, TDD
**Output Section**: 04-TESTING-INVENTORY.md

#### Researcher 5: Current State Specialist
**Assignment**: Categories 4, 6, 7 - Current docs, implementation, root docs (19 files)
**Files**: 19
**Focus**: Latest status, SDK integration, security model, config formats, logging flows
**Output Section**: 05-IMPLEMENTATION-PROGRESS-INVENTORY.md, 06-CONFIG-SECURITY-INVENTORY.md, 07-ROOT-DOCS-INVENTORY.md

#### Researcher 6: Archive Specialist
**Assignment**: Category 8 - Archive (9 files)
**Files**: 9
**Focus**: Historical context, what changed between versions, deprecated features
**Output Section**: 09-VERSION-MATRIX.md

#### Researcher 7: Meta & Index Specialist
**Assignment**: Categories 9, 10 - Dev guides, indexes, summaries (11 files)
**Files**: 11
**Focus**: Documentation structure, quick references, project overviews
**Output Section**: Contribution to 00-INVENTORY-SUMMARY.md

---

## Phase 3: Consensus Rules

### Priority Rules (for conflicts)
1. **Most Recent Wins**: Prefer `docs/current/` over `docs/archive/`
2. **Most Detailed Wins**: Prefer comprehensive specs over brief mentions
3. **SDK-First**: Prefer Project-X-Py SDK integration over raw API specs
4. **Current Implementation**: Prefer `PROJECT_STATUS.md` for what's actually built
5. **Flag Ambiguity**: If specs genuinely conflict on requirements, flag for human review

### Version Hierarchy
- **Tier 1 (Authority)**: `docs/current/`, root `*.md` files (CLAUDE.md, SDK_*.md)
- **Tier 2 (Reference)**: `docs/PROJECT_DOCS/rules/`, `docs/testing/`
- **Tier 3 (Historical)**: `docs/PROJECT_DOCS/architecture/`, API specs
- **Tier 4 (Archive)**: `docs/archive/`

### Conflict Resolution Strategy
1. **Feature Definition**: Use oldest detailed spec (original requirements)
2. **Implementation Approach**: Use newest (reflects SDK-first pivot)
3. **Current Status**: Use `PROJECT_STATUS.md` (single source of truth)
4. **Testing**: Use `docs/testing/` (most recent testing docs)

---

## Phase 4: Output Deliverables

### Reports to Generate

1. **00-INVENTORY-SUMMARY.md** (Coordinator)
   - High-level overview of all findings
   - Total feature count by category
   - Key conflicts identified
   - Recommendations

2. **01-RISK-RULES-INVENTORY.md** (Researcher 1)
   - All 12 rules with complete specifications
   - Parameters, thresholds, enforcement actions
   - Implementation status

3. **02-SDK-API-INVENTORY.md** (Researcher 2)
   - Gateway API endpoints catalog
   - Authentication flows
   - Real-time event types
   - Rate limits

4. **03-ARCHITECTURE-MODULES-INVENTORY.md** (Researcher 3)
   - System architecture (v1 vs v2 comparison)
   - Core modules (enforcement, lockout, timer, reset)
   - Component interactions

5. **04-TESTING-INVENTORY.md** (Researcher 4)
   - Testing methodologies (TDD, runtime, integration)
   - Test runner features
   - Runtime debugging capabilities
   - AI workflow patterns

6. **05-IMPLEMENTATION-PROGRESS-INVENTORY.md** (Researcher 5)
   - Current implementation status
   - What's built vs what's missing
   - Next priorities

7. **06-CONFIG-SECURITY-INVENTORY.md** (Researcher 5)
   - Configuration formats (YAML examples)
   - Security model (Windows UAC)
   - Admin vs trader CLI

8. **07-ROOT-DOCS-INVENTORY.md** (Researcher 5)
   - CLAUDE.md entry point
   - SDK integration guides
   - Logging flows
   - Test runner fixes

9. **08-CONFLICTS-REVIEW.md** (Coordinator)
   - Features with conflicting specifications
   - Version discrepancies
   - Recommendations for human review

10. **09-VERSION-MATRIX.md** (Researcher 6)
    - What changed between architecture v1 and v2
    - Pre-SDK vs post-SDK pivot
    - Archived vs current features

11. **10-SWARM-METADATA.json** (Coordinator)
    - Machine-readable inventory
    - Feature extraction data
    - Cross-references

12. **README.md** (Coordinator)
    - How to use the inventory
    - Navigation guide
    - Update procedures

---

## Execution Timeline

### Phase 1: Discovery (Complete)
- Directory structure mapped
- Files categorized (88 markdown files)
- Work distribution planned

### Phase 2: Spawn Researchers (Next)
- Spawn 7 researcher agents
- Each reads assigned files
- Extract features to structured format

### Phase 3: Collection & Synthesis (After researchers complete)
- Collect all findings
- Apply consensus rules
- Identify conflicts

### Phase 4: Report Generation (Final)
- Generate 12 inventory reports
- Create machine-readable metadata
- Document conflicts for human review

---

## Success Criteria

- [ ] All 88 markdown files analyzed
- [ ] Features categorized by domain
- [ ] Conflicts identified and documented
- [ ] Machine-readable inventory generated
- [ ] Human-readable reports created
- [ ] Version matrix showing old vs new
- [ ] No files modified (read-only operation)

---

**Status**: Phase 1 Complete, Ready for Phase 2 (Spawn Researchers)
