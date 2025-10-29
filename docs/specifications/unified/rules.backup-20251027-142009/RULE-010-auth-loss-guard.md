# RULE-010: Auth Loss Guard

**Category**: Hard Lockout (Category 3)
**Priority**: Medium
**Status**: Not Implemented

---

## Unified Specification (v3.0)

### Purpose
Monitor TopstepX `canTrade` status and lockout when API signals account restriction.

### Trigger Condition
**Event**: `EventType.ACCOUNT_UPDATED` (when `canTrade` changes)

**Logic**:
```python
if account_event['canTrade'] == False:
    return BREACH
```

### Enforcement Action
**Type**: HARD LOCKOUT (per user guidance)

1. Close all positions
2. Set lockout (no expiry - wait for API)
3. Auto-unlock when `canTrade: true` received
4. NO admin manual unlock

**Auto-Unlock**: When TopstepX sends `canTrade: true`

### Configuration
```yaml
auth_loss_guard:
  enabled: true
  enforcement: "close_all_and_lockout"
```

### Dependencies
- MOD-002 (LockoutManager): ❌ Missing
- SDK Account Events: ✅ Exists

---

## Conflict Resolutions

### Conflict 1: Unlock Mechanism
- **Original**: "Admin override only"
- **User Guidance**: "Auto-unlock when API sends canTrade: true"
- **Resolution**: Use API-driven unlock (not admin)

---

## Version History
- v3.0 (2025-10-25): Unified specification (Wave 3)

---

## Implementation Status
- **Status**: Not Started
- **Blockers**: MOD-002
- **Effort**: 1 day
