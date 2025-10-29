# RULE-002: Max Contracts Per Instrument

**Category**: Trade-by-Trade (Category 1)
**Priority**: Critical
**Status**: Fully Implemented

---

## Unified Specification (v3.0)

### Purpose
Enforce per-symbol contract limits to prevent concentration risk in specific instruments.

### Trigger Condition
**Event Type**: `EventType.POSITION_UPDATED` (per-symbol position updates)

**Trigger Logic**:
```python
def check(position_event):
    symbol = extract_symbol(position_event['contractId'])  # "CON.F.US.MNQ.U25" → "MNQ"
    current_size = abs(position_event['size'])

    if symbol in config['limits']:
        limit = config['limits'][symbol]
        if current_size > limit:
            return BREACH
```

### Enforcement Action

**Type**: TRADE-BY-TRADE

**Action Sequence**:
1. **Close position in that instrument only** (reduce or close all)
2. **NO lockout**
3. **Trader can immediately trade again**

**Enforcement Modes**:
- `reduce_to_limit` - Partial close to exact limit
- `close_all` - Close entire position in that symbol

**Implementation**: `src/risk_manager/rules/max_contracts_per_instrument.py` (262 lines - most advanced rule)

### Configuration Parameters
```yaml
max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 2
    ES: 1
    NQ: 3
  enforcement: "reduce_to_limit"  # or "close_all"
  unknown_symbol_action: "block"  # or "allow" or "allow_with_limit:N"
```

### State Requirements
- PnL Tracker: No
- Lockout Manager: No
- Timer Manager: No
- Reset Scheduler: No

### SDK Integration
- Events: `EventType.POSITION_UPDATED`
- Methods: `close_position()`, `partial_close_position()`
- Quote data: No

### Database Schema
No persistence required (real-time calculation from SDK position events).

### Examples

**Scenario**: Per-Symbol Limit Breach
- MNQ limit: 2 contracts
- Current: MNQ Long 2
- New trade: MNQ Long 1
- Total: 3 contracts in MNQ
- **Trigger**: Breach (3 > 2)
- **Enforcement**: Reduce MNQ position to 2 contracts
- **Result**: MNQ now 2 contracts, other symbols unaffected

---

## Conflict Resolutions
**No conflicts found.** All documentation sources aligned.

---

## Version History
- v1.0 (2025-01-17): Original specification
- v2.0 (2025-01-17): Revised
- v3.0 (2025-10-25): Unified specification (Wave 3)

---

## Original Sources
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/rules/02_max_contracts_per_instrument.md`
- `/docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` (lines 170-284)

---

## Implementation Status
- **Status**: Fully Implemented ✅
- **Production Ready**: Yes
- **Tests**: Good coverage, needs edge case expansion
- **Features**: Symbol extraction, unknown symbol handling, flexible enforcement modes

---

## Related Rules
- **RULE-001** (MaxContracts): Account-wide limit instead of per-symbol
- **RULE-011** (SymbolBlocks): Blocks specific symbols entirely
