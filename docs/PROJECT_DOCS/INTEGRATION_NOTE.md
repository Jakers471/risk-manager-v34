# Integration Note - PROJECT_DOCS in Risk Manager V34

**Date**: 2025-10-23
**Source**: Simple Risk Manager project

---

## What is This?

This `PROJECT_DOCS` directory contains **comprehensive risk management specifications** from a previous project. It includes:

- **12 Risk Rules** - Detailed specifications for different risk scenarios
- **4 Core Modules** - Enforcement, lockout, timer, and reset systems
- **Architecture Documentation** - Complete system design (v1 and v2)
- **API Integration Guide** - TopstepX Gateway API integration
- **Configuration Examples** - Production-ready YAML configs

## How It Relates to Risk Manager V34

### What's Different
Risk Manager V34 is a **fresh implementation** using:
- **Project-X-Py SDK** - Modern async Python trading SDK
- **Claude-Flow** - AI orchestration (optional)
- **Event-driven architecture** - Clean separation of concerns
- **Simplified API** - Easy-to-use `RiskManager.create()`

### What's Similar
The **risk management concepts** are the same:
- Daily loss limits
- Position size limits
- Stop-loss requirements
- Session restrictions
- Enforcement actions (flatten, lockout, etc.)

## How to Use These Docs

### 1. **As Reference Material**
Use the detailed rule specifications when implementing new rules:

```python
# Example: Implementing RULE-006 (Trade Frequency Limit)
# See: rules/trade_frequency_limit.md

from risk_manager.rules import RiskRule

class TradeFrequencyRule(RiskRule):
    # Implementation based on RULE-006 spec
    pass
```

### 2. **For Architecture Ideas**
The system architecture documents provide excellent patterns:
- Read `architecture/system_architecture_v2.md` for design patterns
- See `modules/enforcement_actions.md` for enforcement strategies
- Check `api/topstepx_integration.md` for API integration patterns

### 3. **For Configuration Templates**
Each rule document includes production-ready config examples:

```yaml
# From RULE-001 (MaxContracts)
rules:
  max_contracts:
    enabled: true
    limit: 5
    action: reject_order
```

### 4. **For Test Scenarios**
Rule documents include validation examples - perfect for writing tests:

```python
# Test cases from RULE-003 (Daily Realized Loss)
def test_daily_loss_enforcement():
    # Scenario from RULE-003 documentation
    pass
```

## Mapping to V34 Code

| PROJECT_DOCS | Risk Manager V34 |
|--------------|------------------|
| `rules/max_contracts.md` | `src/risk_manager/rules/max_position.py` |
| `rules/daily_realized_loss.md` | `src/risk_manager/rules/daily_loss.py` |
| `modules/enforcement_actions.md` | `src/risk_manager/core/engine.py` (enforcement methods) |
| `modules/lockout_manager.md` | `src/risk_manager/core/engine.py` (pause_trading) |
| `api/topstepx_integration.md` | `src/risk_manager/integrations/trading.py` |

## Implementation Roadmap

### Phase 1: Core Rules (Implemented ✅)
- ✅ MaxContracts → `MaxPositionRule`
- ✅ DailyRealizedLoss → `DailyLossRule`
- ✅ Base enforcement actions

### Phase 2: Additional Rules (To Implement)
Reference these docs when adding:
- [ ] RULE-006: Trade Frequency Limit
- [ ] RULE-007: Cooldown After Loss
- [ ] RULE-008: No Stop Loss Grace
- [ ] RULE-009: Session Block Outside
- [ ] RULE-010: Auth Loss Guard
- [ ] RULE-011: Symbol Blocks

### Phase 3: Advanced Modules (To Implement)
- [ ] MOD-002: Lockout Manager (state persistence)
- [ ] MOD-003: Timer Manager (cooldown timers)
- [ ] MOD-004: Reset Scheduler (daily resets)

## Quick Links

### Start Here
1. [README.md](README.md) - Documentation overview
2. [CURRENT_VERSION.md](CURRENT_VERSION.md) - Current architecture version
3. [summary/project_overview.md](summary/project_overview.md) - High-level overview

### Implementation Guides
- [architecture/system_architecture_v2.md](architecture/system_architecture_v2.md) - System design
- [api/topstepx_integration.md](api/topstepx_integration.md) - API integration patterns
- [modules/enforcement_actions.md](modules/enforcement_actions.md) - Enforcement strategies

### Rule Specifications
Browse `rules/` directory for detailed specifications of all 12 risk rules.

## Key Differences: Old vs New

### Old Architecture (PROJECT_DOCS)
- Direct TopstepX API integration
- Synchronous Python
- Config-driven rule system
- Complex state management

### New Architecture (V34)
- **Project-X-Py SDK** abstraction layer
- **Async/await** throughout
- **Programmatic** rule creation
- **Event-driven** architecture
- **Optional AI** integration (Claude-Flow)

## Benefits of This Documentation

1. **Complete Specifications** - Every rule is fully documented
2. **Battle-Tested Patterns** - These designs have been thoroughly reviewed
3. **Production Examples** - Real-world configuration templates
4. **Test Scenarios** - Comprehensive validation cases
5. **API Documentation** - Exact endpoint specifications

## How to Add New Rules

When implementing a new rule from PROJECT_DOCS:

```python
# 1. Read the specification
# Example: docs/PROJECT_DOCS/rules/trade_frequency_limit.md

# 2. Create rule class in src/risk_manager/rules/
from risk_manager.rules import RiskRule

class TradeFrequencyRule(RiskRule):
    """Implements RULE-006: Trade Frequency Limit

    Based on: docs/PROJECT_DOCS/rules/trade_frequency_limit.md
    """

    def __init__(self, max_trades: int, window_seconds: int):
        super().__init__(action="pause")
        self.max_trades = max_trades
        self.window_seconds = window_seconds
        self.trade_history = []

    async def evaluate(self, event, engine):
        # Implementation based on RULE-006 spec
        pass

# 3. Add to risk_manager/rules/__init__.py
# 4. Create tests in tests/test_trade_frequency.py
# 5. Add example in examples/04_frequency_limits.py
```

## Questions?

- Check the original docs in this directory
- Compare with V34 implementation in `src/risk_manager/`
- See examples in `examples/`

---

**Note**: This documentation represents the **specification and design** from a previous project. Risk Manager V34 implements similar concepts with a modern, simplified architecture using industry-standard SDKs.

**Use these docs for**:
- Understanding risk management concepts
- Getting implementation ideas
- Finding configuration examples
- Writing comprehensive tests

**Don't use these docs for**:
- Direct code copying (different architecture)
- API integration (V34 uses Project-X-Py SDK)
- File structure (V34 has different organization)

---

**Ready to implement more rules?** Pick a rule from `rules/` directory and follow the pattern above! 🚀
