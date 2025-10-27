# Data Schemas Directory

**Version**: 1.0
**Last Updated**: 2025-10-27
**Purpose**: Canonical data schema definitions for the Risk Manager

---

## Overview

This directory contains the **single source of truth** for all data schemas used in the Risk Manager V34 project. These schemas define the exact structure of events, state, and data flowing through the system.

**Critical Importance**:
- All code MUST reference these schemas
- All tests MUST use these schemas
- All documentation MUST align with these schemas
- Any deviations will cause runtime errors and test failures

---

## What's in This Directory

### 1. event-data-schemas.md (PRIMARY REFERENCE)
**Purpose**: Canonical definitions for all SDK events

**Contains**:
- Complete schema for every event type (POSITION, ORDER, TRADE, QUOTE, ACCOUNT)
- Field names, types, and nullability
- Enum value tables (OrderSide, OrderType, OrderStatus)
- SDK-to-canonical field mappings
- Usage examples for each event

**When to Use**:
- Implementing event handlers
- Writing rule logic
- Creating tests
- Debugging field mismatches

**Key Sections**:
- Position Events (OPENED, UPDATED, CLOSED)
- Order Events (PLACED, FILLED, CANCELLED, etc.)
- Trade Events (TRADE_EXECUTED)
- Quote Events (QUOTE_UPDATE)
- Account Events (ACCOUNT_UPDATED)
- Enum Reference Tables

---

### 2. state-tracking-schemas.md
**Purpose**: Defines persistent state management schemas

**Contains**:
- PositionState (tracking active positions)
- OrderState (tracking active orders)
- PnLState (cumulative P&L tracking)
- ViolationState (rule violation tracking)
- DailyStatsState (daily statistics)
- TimerState (cooldown and grace period timers)
- Database schemas (SQLite)

**When to Use**:
- Implementing state management
- Designing database tables
- Writing state update logic
- Implementing daily resets

**Key Sections**:
- Position State (with stop-loss tracking)
- P&L State (realized + unrealized)
- Violation State (lockouts and warnings)
- State synchronization patterns
- Daily reset procedures

---

### 3. schema-to-sdk-mapping.md
**Purpose**: Field-by-field mapping from SDK to canonical schemas

**Contains**:
- Quick reference table (all mappings at a glance)
- Detailed mapping for each event type
- Symbol extraction utility
- Data type conversions
- Common mapping errors
- Test mock data examples

**When to Use**:
- Implementing EventBridge handlers
- Creating mock SDK data for tests
- Debugging field name mismatches
- Validating SDK integration

**Key Sections**:
- Quick Reference Table
- Position Events Mapping
- Order Events Mapping
- Trade Events Mapping
- Quote Events Mapping
- Common Mapping Errors

---

### 4. SCHEMA_VALIDATION_CHECKLIST.md
**Purpose**: Step-by-step validation checklist

**Contains**:
- Event schema validation checklists
- State schema validation checklists
- SDK mapping validation checklists
- Rule specification validation checklists
- Test schema validation checklists
- Cross-document consistency checks
- Validation report template

**When to Use**:
- Code reviews
- Adding new features
- Debugging schema issues
- Audit/compliance checks

**Key Sections**:
- Event Schema Validation
- SDK Mapping Validation
- Rule Specification Validation
- Common Issues Checklist
- Validation Procedure

---

## Quick Start Guide

### For New Developers

**Step 1**: Read `event-data-schemas.md`
- Understand the canonical event structures
- Note the enum value tables
- See examples of each event type

**Step 2**: Read `schema-to-sdk-mapping.md`
- Understand how SDK data maps to our schemas
- Note the common errors section
- Review the quick reference table

**Step 3**: When implementing, use the validation checklist
- Run through relevant sections before committing
- Verify field names match canonical schemas
- Check for common issues

---

### For Rule Implementers

**Your Workflow**:
1. Read rule specification (e.g., `RULE-003-daily-realized-loss.md`)
2. Identify which events the rule needs
3. Open `event-data-schemas.md` and find those event schemas
4. Write rule logic using EXACT field names from schemas
5. Use `SCHEMA_VALIDATION_CHECKLIST.md` to verify correctness

**Critical Fields to Check**:
- RULE-003: `realized_pnl` (not `pnl` or `profitAndLoss`)
- RULE-004/005: `average_price` (not `entry_price` or `avgPrice`)
- RULE-008: `stop_price` from ORDER_PLACED
- RULE-010: `can_trade` from ACCOUNT_UPDATED

---

### For Test Writers

**Your Workflow**:
1. Open `schema-to-sdk-mapping.md`
2. Find the "Testing with Mock SDK Data" section
3. Copy mock data examples (they use correct SDK field names)
4. Verify your assertions use canonical field names from `event-data-schemas.md`

**Example**:
```python
# Create mock SDK data (use SDK field names)
mock_sdk_data = {
    "contractId": "CON.F.US.MNQ.Z25",
    "accountId": 123456,
    "averagePrice": 25947.0,  # SDK uses camelCase
    "unrealizedPnl": 0.0
}

# Map to canonical schema
event = map_position_event(mock_sdk_data)

# Assert using canonical field names
assert event["average_price"] == 25947.0  # Our schema uses snake_case
assert event["account_id"] == 123456
```

---

## The 12 Critical Fixes

This directory was created to fix **12 critical schema inconsistencies** found in the audit:

### Fixed Issues

1. ✅ **Added `realized_pnl` to TRADE_EXECUTED** (blocks RULE-003)
   - Location: `event-data-schemas.md` line 465-470
   - Mapped from SDK `profitAndLoss`

2. ✅ **Added `account_id` to all events** (blocks multi-account support)
   - All event schemas now include `account_id`
   - Marked as CRITICAL in documentation

3. ✅ **Fixed position field names** (use `average_price`, not `entry_price`)
   - Position events use `average_price`
   - State schemas use `average_price`
   - Rule specs updated to use `average_price`

4. ✅ **Fixed P&L field names** (use `realized_pnl`, not `pnl`)
   - Trade events use `realized_pnl`
   - Position events use `unrealized_pnl` and `realized_pnl`
   - State schemas use snake_case

5. ✅ **Added `stop_price` to ORDER_PLACED** (blocks RULE-008)
   - Order events include `stop_price` field
   - Marked as CRITICAL for stop-loss detection

6. ✅ **Documented enum values** (OrderSide, OrderType, OrderStatus)
   - Complete enum tables in `event-data-schemas.md`
   - Values: OrderSide (1=BUY, 2=SELL), OrderType (1/2/3), OrderStatus (1/2/3/4/6)

7. ✅ **Fixed timestamp type** (datetime object, not string)
   - All events use `timestamp: datetime`
   - Convert to string only for JSON serialization

8. ✅ **Standardized `size` vs `quantity`** usage
   - Positions/Trades use `size`
   - Orders use `quantity`
   - Documented in mapping guide

9. ✅ **Removed redundant position `side` field**
   - Use signed `size` instead (positive=long, negative=short)
   - No separate `side` or `type` enum for positions

10. ✅ **Added calculated fields to QUOTE_UPDATE**
    - `mid_price` = (bid + ask) / 2
    - `spread` = ask - bid
    - `age_ms` for staleness detection

11. ✅ **Documented nullable fields explicitly**
    - `realized_pnl: float | None` (None for opening trades)
    - `stop_price: float | None` (None for non-stop orders)
    - All optional fields marked

12. ✅ **Created complete SDK mapping guide**
    - Field-by-field mapping for all events
    - Common errors documented
    - Test mock data examples

---

## Integration with Other Documentation

### Related Documents

**SDK Integration**:
- `docs/specifications/unified/sdk-integration.md` - High-level SDK usage
- `SDK_EVENTS_QUICK_REFERENCE.txt` - Raw SDK event reference

**Rule Specifications**:
- `docs/specifications/unified/rules/RULE-*.md` - All rule specs
- Must reference these schemas for field names

**Audit Reports**:
- `docs/specifications/unified/DATA_SCHEMA_CONSISTENCY_AUDIT.md` - Audit findings
- `RULES_ALIGNMENT_AUDIT_REPORT.md` - Rules alignment audit

**Implementation**:
- `src/risk_manager/sdk/event_bridge.py` - Event mapping implementation
- `src/risk_manager/state/` - State management implementation

---

## Schema Evolution

### Version History

**Version 1.0 (2025-10-27)**:
- Initial canonical schema definitions
- Fixed 12 critical inconsistencies from audit
- Established as single source of truth

**Future Changes**:
When schemas need to change:
1. Update schemas in this directory FIRST
2. Update implementation to match
3. Update tests to match
4. Update rule specifications to match
5. Document change in schema evolution log

### Deprecation Policy

**Deprecated Field Names**:
- ❌ `entry_price` → Use `average_price`
- ❌ `avgPrice` → Use `average_price`
- ❌ `pnl` → Use `realized_pnl` or `unrealized_pnl`
- ❌ `profitAndLoss` → Use `realized_pnl`

**Do NOT use deprecated names in any new code!**

---

## Validation Workflow

### Before Committing Code

**Checklist**:
1. Open `SCHEMA_VALIDATION_CHECKLIST.md`
2. Run through relevant sections for your changes
3. Verify all field names match `event-data-schemas.md`
4. Check enum values correct
5. Verify nullable fields handled
6. Ensure `account_id` included where needed

### During Code Review

**Reviewer Checklist**:
1. Verify PR uses canonical field names
2. Check for deprecated field names
3. Verify enum values correct
4. Check None handling for nullable fields
5. Verify tests use correct mock data

---

## Common Workflows

### Adding a New Event Type

1. Add schema to `event-data-schemas.md`
2. Add SDK mapping to `schema-to-sdk-mapping.md`
3. Update validation checklist
4. Implement in EventBridge
5. Add tests

### Modifying an Existing Event

1. Update schema in `event-data-schemas.md`
2. Update mapping in `schema-to-sdk-mapping.md`
3. Update all rule specs that use this event
4. Update implementation
5. Update tests
6. Document in evolution log

### Debugging Field Mismatch

1. Check error message for field name
2. Open `schema-to-sdk-mapping.md`
3. Find the event type in question
4. Verify SDK field name vs canonical name
5. Check for common errors section
6. Fix code to use correct field name

---

## FAQ

### Q: Which file should I read first?
**A**: Start with `event-data-schemas.md` - it's the primary reference.

### Q: Where do I find enum values (1=BUY, 2=SELL, etc.)?
**A**: `event-data-schemas.md` has complete enum tables at the bottom.

### Q: How do I know if a field can be None?
**A**: Look for `float | None` type annotations in `event-data-schemas.md`.

### Q: Why do we use `average_price` instead of `entry_price`?
**A**: It matches the SDK field name (`averagePrice`) and is more accurate (average of all entries).

### Q: Why do trades use `size` but orders use `quantity`?
**A**: SDK convention - SDK uses `quantity` for orders and `quantity` for trades. We normalize to `size` for trades and `quantity` for orders to match domain language.

### Q: Where do I find the stop-loss price?
**A**: ORDER_PLACED event, `stop_price` field (mapped from SDK `stopPrice`).

### Q: How do I detect if a trade is opening or closing?
**A**: Check `realized_pnl` - if None, it's an opening trade. If float, it's a closing trade.

### Q: What's the difference between `realized_pnl` and `unrealized_pnl`?
**A**:
- `realized_pnl`: Actual P&L from closed trades (from TRADE_EXECUTED)
- `unrealized_pnl`: Current P&L of open positions (from POSITION_UPDATED or calculated from quotes)

---

## Maintenance

### Regular Reviews

**Weekly** (during active development):
- Run validation checklist on new code
- Update schemas if SDK changes
- Document any issues found

**Monthly**:
- Review for consistency across all docs
- Update examples if needed
- Archive old versions

**After SDK Upgrade**:
- Review SDK changelog
- Update mappings if fields changed
- Verify enum values still correct
- Run full validation checklist

---

## Contact / Questions

**For Schema Questions**:
- Refer to this README first
- Check `event-data-schemas.md` for definitions
- Check `schema-to-sdk-mapping.md` for mappings
- Use validation checklist to verify correctness

**For Implementation Questions**:
- Check `src/risk_manager/sdk/event_bridge.py` for current implementation
- Refer to rule specifications for usage examples

---

## Document Status

- ✅ **event-data-schemas.md**: Complete, reviewed, canonical
- ✅ **state-tracking-schemas.md**: Complete, reviewed, canonical
- ✅ **schema-to-sdk-mapping.md**: Complete, reviewed, reference
- ✅ **SCHEMA_VALIDATION_CHECKLIST.md**: Complete, reviewed, operational
- ✅ **README.md**: Complete, reviewed, guide

**Last Updated**: 2025-10-27
**Next Review**: After any SDK version change or schema modification
**Maintainer**: Update when schemas change
