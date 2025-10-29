# RULE-011: Symbol Blocks

**Category**: Trade-by-Trade (Category 1)
**Priority**: Low
**Status**: Not Implemented

---

## Unified Specification (v3.0)

### Purpose
Blacklist specific symbols - close any position immediately and permanently lock that symbol.

### Trigger Condition
**Event**: `EventType.POSITION_UPDATED` (position opens in blocked symbol)

### Enforcement Action
**Type**: TRADE-BY-TRADE (with symbol-specific lockout)

1. Close position in that symbol
2. Set permanent symbol-specific lockout
3. Can trade other symbols immediately

### Configuration
```yaml
symbol_blocks:
  enabled: true
  blocked_symbols:
    - "RTY"
    - "BTC"
  enforcement: "close_and_lockout_symbol"
```

### Dependencies
- MOD-002 (LockoutManager): ❌ Missing (needs symbol-specific lockout support)

---

## Conflict Resolutions
**No conflicts found.**

---

## Version History
- v3.0 (2025-10-25): Unified specification (Wave 3)

---

## Implementation Status
- **Status**: Not Started
- **Blockers**: MOD-002 (symbol-specific lockout)
- **Effort**: 1 day
