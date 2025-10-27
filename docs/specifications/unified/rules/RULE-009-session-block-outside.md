# RULE-009: Session Block Outside

**Category**: Hard Lockout (Category 3)
**Priority**: High
**Status**: Not Implemented

---

## Unified Specification (v3.0)

### Purpose
Block trading outside configured session hours and on holidays.

### Trigger Condition
**Events**: 
1. `EventType.POSITION_UPDATED` (position opens outside session)
2. Background timer (session end time reached)
3. Holiday detection

### Enforcement Action
**Type**: HARD LOCKOUT (per user guidance)

1. Close all positions
2. Cancel all orders
3. Set timer-based lockout until session start
4. NO admin manual unlock - timer only

**Auto-Unlock**: At session start time

### Configuration
```yaml
session_block_outside:
  enabled: true
  global_session:
    enabled: true
    start: "09:30"
    end: "16:00"
    timezone: "America/New_York"
  per_instrument_sessions:
    enabled: true
    sessions:
      ES:
        start: "18:00"  # Sunday 6pm
        end: "17:00"    # Friday 5pm
        timezone: "America/Chicago"
  close_positions_at_session_end: true
  lockout_outside_session: true
  respect_holidays: true
  holiday_calendar: "config/holidays.yaml"
```

### Dependencies
- MOD-002 (LockoutManager): ❌ Missing
- MOD-004 (ResetScheduler): ❌ Missing
- Holiday Calendar: ❌ Missing
- Timezone Library: ✅ pytz/zoneinfo

---

## Conflict Resolutions

### Conflict 1: Admin Override
- **Original**: "Admin override" for unlock
- **User Guidance**: "Timer-based unlock only"
- **Resolution**: Use timer-based (session start time)

---

## Version History
- v3.0 (2025-10-25): Unified specification (Wave 3) - applied timer-based unlock

---

## Implementation Status
- **Status**: Not Started
- **Blockers**: MOD-002, MOD-004
- **Effort**: 3-4 days (most complex)
