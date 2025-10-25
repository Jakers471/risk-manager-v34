# Risk Manager Custom Agents

This directory contains 5 specialized agents customized for the Simple Risk Manager project.

## Agent Overview

### 1. test-coordinator.md
**Type:** Validator  
**Focus:** Risk rule testing and TopstepX integration validation  
**Key Capabilities:**
- Risk rule testing (all 12 rules)
- TopstepX SDK integration testing
- Enforcement action validation
- P&L tracking tests
- Edge case analysis

**When to Use:**
- Running test suites for risk rules
- Validating enforcement actions
- Testing TopstepX API integration
- Checking test coverage and quality

---

### 2. risk-rule-developer.md
**Type:** Developer  
**Focus:** Risk rule implementation for TopstepX  
**Key Capabilities:**
- Risk rule class implementation
- Enforcement action integration
- P&L tracker integration
- Lockout management
- TopstepX event handling

**When to Use:**
- Implementing new risk rules
- Modifying existing rule logic
- Integrating with enforcement actions
- Working with P&L calculations

---

### 3. integration-validator.md
**Type:** Validator  
**Focus:** TopstepX SDK and production readiness  
**Key Capabilities:**
- REST API integration testing
- SignalR real-time event validation
- Database integration testing
- Event pipeline validation
- Production readiness checks

**When to Use:**
- Validating TopstepX API integration
- Testing SignalR event streaming
- Verifying database operations
- Ensuring no mock implementations remain
- Pre-deployment validation

---

### 4. quality-enforcer.md
**Type:** Reviewer  
**Focus:** Code quality and financial safety  
**Key Capabilities:**
- Code quality review
- Security auditing
- Financial safety checks
- Standards enforcement
- Risk rule validation

**When to Use:**
- Reviewing risk rule implementations
- Security audits
- Code quality checks
- Ensuring fail-safe behavior
- Pre-merge reviews

---

### 5. deployment-manager.md
**Type:** Deployment  
**Focus:** Windows Service deployment and releases  
**Key Capabilities:**
- Windows Service installation
- Release coordination
- Production validation
- Rollback management
- Monitoring setup

**When to Use:**
- Deploying Windows Service
- Managing releases
- Service installation/configuration
- Production deployment
- Rollback procedures

---

## Usage Examples

### Running Tests
```bash
# Use test-coordinator agent
claude code "Use test-coordinator agent to run all risk rule tests and report coverage"
```

### Implementing a New Rule
```bash
# Use risk-rule-developer agent
claude code "Use risk-rule-developer to implement RULE-013: Max Daily Trades with limit of 50"
```

### Validating Integration
```bash
# Use integration-validator agent
claude code "Use integration-validator to verify TopstepX SignalR connection and event streaming"
```

### Code Review
```bash
# Use quality-enforcer agent
claude code "Use quality-enforcer to review src/rules/daily_realized_loss.py for security and safety"
```

### Deployment
```bash
# Use deployment-manager agent
claude code "Use deployment-manager to prepare release v1.0.0 and create Windows Service installer"
```

---

## Agent Coordination

These agents work together in the development workflow:

1. **risk-rule-developer** implements the rule
2. **test-coordinator** writes and runs tests
3. **quality-enforcer** reviews code quality and security
4. **integration-validator** validates TopstepX integration
5. **deployment-manager** packages and deploys

---

## MCP Tool Integration

All agents support MCP tool coordination via:
- `mcp__claude-flow__memory_usage` - Share status and results
- `mcp__claude-flow__task_orchestrate` - Coordinate tasks
- `mcp__claude-flow__swarm_init` - Initialize agent swarms

Example:
```javascript
mcp__claude-flow__memory_usage {
  action: "store",
  key: "swarm/test-coordinator/status",
  namespace: "coordination",
  value: JSON.stringify({
    agent: "test-coordinator",
    tests_passed: 143,
    tests_failed: 1,
    coverage: "92%"
  })
}
```

---

## Project Context

These agents are specifically designed for:
- **TopstepX SDK integration** - REST API and SignalR
- **Risk rule implementation** - 12 trading risk rules
- **Financial safety** - Fail-safe behavior, capital protection
- **Windows Service deployment** - Background service architecture
- **Real-time enforcement** - Sub-second event processing

---

## Related Documentation

- Project status: `/START_HERE.md`
- Rule specifications: `/project-specs/SPECS/03-RISK-RULES/`
- API documentation: `/docs/API_CLIENT_COMPLETE.md`
- Testing guide: `/tests/fixtures_reference.md`
- Phase plans: `/docs/PHASE_*_BUILD_PLAN.md`

---

Generated: 2025-10-23
Version: 1.0.0
