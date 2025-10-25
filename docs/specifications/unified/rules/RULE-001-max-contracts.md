# RULE-001: Max Contracts

**Category**: Trade-by-Trade (Category 1)
**Priority**: Critical
**Status**: Fully Implemented

---

## Unified Specification (v3.0)

### Purpose
Cap net contract exposure across all instruments to prevent over-leveraging and excessive account risk.

### Trigger Condition
**Event Type**: `GatewayUserPosition` (every position update)

**Trigger Logic**:
```python
def check(position_events):
    total_net = 0
    for position in all_positions:
        if position['type'] == 1:  # Long
            total_net += position['size']
        elif position['type'] == 2:  # Short
            total_net -= position['size']

    total_net = abs(total_net)
    if total_net > config['limit']:
        return BREACH
```

### Enforcement Action

**Type**: TRADE-BY-TRADE

**Action Sequence**:
1. **Close positions** (all or reduce to limit based on config)
2. **NO lockout**
3. **Trader can immediately trade again**

**Configuration Options**:
- `close_all: true` - Close all positions
- `reduce_to_limit: true` - Close only excess contracts

**Implementation**: `src/risk_manager/rules/max_position.py`

### Configuration Parameters
```yaml
max_contracts:
  enabled: true
  limit: 5                   # Max net contracts
  count_type: "net"          # "net" or "gross"
  close_all: false
  reduce_to_limit: true
```

### State Requirements
- PnL Tracker: No
- Lockout Manager: No
- Timer Manager: No
- Reset Scheduler: No

### SDK Integration
- Events: `GatewayUserPosition`
- Methods: `close_position()`, `close_all_positions()`
- Quote data: No

### Database Schema
No persistence required (real-time calculation from SDK position events).

### Examples

**Scenario**: Account-Wide Limit Breach
- Positions: MNQ Long 3, ES Long 2
- Total net: 5 contracts
- New trade: MNQ Long 1
- Total net: 6 contracts
- **Trigger**: Breach (6 > 5)
- **Enforcement**: Close 1 contract to reach limit
- **Result**: Can trade immediately

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
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/rules/01_max_contracts.md`
- `/docs/analysis/wave1-feature-inventory/01-RISK-RULES-INVENTORY.md` (lines 35-168)

---

## Implementation Status
- **Status**: Fully Implemented ✅
- **Production Ready**: Yes
- **Tests**: Basic coverage, needs expansion

---

## Related Rules
- **RULE-002** (MaxContractsPerInstrument): Per-symbol limit instead of account-wide
