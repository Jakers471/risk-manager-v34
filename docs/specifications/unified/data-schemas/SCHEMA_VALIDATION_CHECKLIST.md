# Schema Validation Checklist

**Version**: 1.0
**Last Updated**: 2025-10-27
**Status**: Operational Checklist
**Purpose**: Step-by-step validation checklist for data schema consistency

---

## Document Purpose

This checklist ensures all data schemas are consistent across:
- Event data schemas
- State tracking schemas
- SDK integration code
- Rule specifications
- Test implementations

Use this checklist when:
- Adding new events
- Modifying existing schemas
- Reviewing rule specifications
- Writing tests
- Debugging schema mismatches

---

## Quick Reference

**Status Legend**:
- ✅ = Verified Correct
- ❌ = Error Found
- ⚠️ = Warning / Needs Review
- 🔍 = Needs Investigation
- 📝 = Documentation Update Needed

---

## Checklist Categories

1. [Event Schema Validation](#event-schema-validation)
2. [State Schema Validation](#state-schema-validation)
3. [SDK Mapping Validation](#sdk-mapping-validation)
4. [Rule Specification Validation](#rule-specification-validation)
5. [Test Schema Validation](#test-schema-validation)
6. [Cross-Document Consistency](#cross-document-consistency)

---

## Event Schema Validation

### Position Events (POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED)

**Field Completeness**:
- [ ] `contract_id` field present (type: str)
- [ ] `symbol` field present (type: str)
- [ ] `account_id` field present (type: int) **CRITICAL**
- [ ] `size` field present (type: int, signed)
- [ ] `average_price` field present (type: float) **NOT** `entry_price` or `avgPrice`
- [ ] `unrealized_pnl` field present (type: float)
- [ ] `realized_pnl` field present (type: float)
- [ ] `timestamp` field present (type: datetime) **NOT** string
- [ ] `raw_data` field present (type: dict)

**Field Naming**:
- [ ] Position price field is `average_price` (matches SDK `averagePrice`)
- [ ] P&L fields are `unrealized_pnl` and `realized_pnl` (snake_case)
- [ ] NO separate `side` or `type` field (use signed `size`)

**Data Types**:
- [ ] `size` is signed integer (positive=long, negative=short)
- [ ] `average_price` is float
- [ ] P&L fields are float
- [ ] `timestamp` is datetime object (not string)

**SDK Mapping**:
- [ ] `contract_id` mapped from `contractId`
- [ ] `symbol` extracted from `contractId`
- [ ] `account_id` mapped from `accountId`
- [ ] `average_price` mapped from `averagePrice` (camelCase)
- [ ] `unrealized_pnl` mapped from `unrealizedPnl` (camelCase)
- [ ] `realized_pnl` mapped from `realizedPnl` (camelCase)

---

### Order Events (ORDER_PLACED, ORDER_FILLED, etc.)

**Field Completeness**:
- [ ] `order_id` field present (type: int)
- [ ] `symbol` field present (type: str)
- [ ] `account_id` field present (type: int)
- [ ] `contract_id` field present (type: str)
- [ ] `side` field present (type: int) **1=BUY, 2=SELL**
- [ ] `quantity` field present (type: int) **NOT** `size`
- [ ] `order_type` field present (type: int) **1=MARKET, 2=LIMIT, 3=STOP**
- [ ] `status` field present (type: int)
- [ ] `limit_price` field present (type: float | None)
- [ ] `stop_price` field present (type: float | None) **CRITICAL for RULE-008**
- [ ] `timestamp` field present (type: datetime)
- [ ] `raw_data` field present (type: dict)

**Field Naming**:
- [ ] Orders use `quantity` (not `size`)
- [ ] Stop price field is `stop_price` (matches SDK `stopPrice`)
- [ ] Limit price field is `limit_price` (matches SDK `limitPrice`)

**Enum Values**:
- [ ] `side`: 1=BUY, 2=SELL (NOT 0=BUY, 1=SELL)
- [ ] `order_type`: 1=MARKET, 2=LIMIT, 3=STOP
- [ ] `status`: 1=PENDING, 2=FILLED, 3=CANCELLED, 4=REJECTED, 6=PENDING_TRIGGER

**SDK Mapping**:
- [ ] `order_id` mapped from `id`
- [ ] `quantity` mapped from `size` (SDK uses `size`)
- [ ] `stop_price` mapped from `stopPrice` (CRITICAL)
- [ ] `limit_price` mapped from `limitPrice`

---

### Trade Events (TRADE_EXECUTED)

**Field Completeness**:
- [ ] `trade_id` field present (type: int)
- [ ] `symbol` field present (type: str)
- [ ] `account_id` field present (type: int) **CRITICAL**
- [ ] `side` field present (type: int)
- [ ] `size` field present (type: int) **NOT** `quantity`
- [ ] `price` field present (type: float)
- [ ] `realized_pnl` field present (type: float | None) **CRITICAL**
- [ ] `timestamp` field present (type: datetime)
- [ ] `raw_data` field present (type: dict)

**Field Naming**:
- [ ] Trades use `size` (not `quantity`)
- [ ] P&L field is `realized_pnl` (NOT `pnl` or `profitAndLoss`)

**Nullable Fields**:
- [ ] `realized_pnl` can be None (for opening trades)
- [ ] Code checks `if realized_pnl is not None` before using

**SDK Mapping**:
- [ ] `trade_id` mapped from `id`
- [ ] `size` mapped from `quantity` (SDK uses `quantity`)
- [ ] `realized_pnl` mapped from `profitAndLoss` (CRITICAL)
- [ ] `account_id` mapped from `accountId` (CRITICAL)

---

### Quote Events (QUOTE_UPDATE)

**Field Completeness**:
- [ ] `symbol` field present (type: str)
- [ ] `last_price` field present (type: float) **CRITICAL**
- [ ] `bid` field present (type: float)
- [ ] `ask` field present (type: float)
- [ ] `bid_size` field present (type: int)
- [ ] `ask_size` field present (type: int)
- [ ] `mid_price` field present (type: float) **CALCULATED**
- [ ] `spread` field present (type: float) **CALCULATED**
- [ ] `timestamp` field present (type: datetime)
- [ ] `age_ms` field present (type: int)
- [ ] `raw_data` field present (type: dict)

**Field Naming**:
- [ ] Current price field is `last_price` (NOT `price` or `last`)

**Calculated Fields**:
- [ ] `mid_price` = (bid + ask) / 2
- [ ] `spread` = ask - bid
- [ ] `age_ms` calculated from SDK timestamp

**SDK Mapping**:
- [ ] `last_price` mapped from `last` (CRITICAL)
- [ ] `bid` mapped from `bid`
- [ ] `ask` mapped from `ask`

---

### Account Events (ACCOUNT_UPDATED)

**Field Completeness**:
- [ ] `account_id` field present (type: int)
- [ ] `balance` field present (type: float)
- [ ] `can_trade` field present (type: bool) **CRITICAL**
- [ ] `equity` field present (type: float | None)
- [ ] `margin_used` field present (type: float | None)
- [ ] `margin_available` field present (type: float | None)
- [ ] `timestamp` field present (type: datetime)
- [ ] `raw_data` field present (type: dict)

**Field Naming**:
- [ ] Authorization field is `can_trade` (matches SDK `canTrade`)

**SDK Mapping**:
- [ ] `can_trade` mapped from `canTrade` (CRITICAL)
- [ ] `account_id` mapped from `id`

---

## State Schema Validation

### PositionState

**Field Completeness**:
- [ ] `contract_id` field present
- [ ] `symbol` field present
- [ ] `account_id` field present
- [ ] `size` field present (signed)
- [ ] `average_price` field present (NOT `entry_price`)
- [ ] `unrealized_pnl` field present
- [ ] `realized_pnl` field present
- [ ] `has_stop_loss` field present (bool)
- [ ] `stop_price` field present (float | None)
- [ ] `stop_order_id` field present (int | None)
- [ ] `opened_at` field present (datetime)
- [ ] `updated_at` field present (datetime)
- [ ] `raw_data` field present

**Field Naming Consistency**:
- [ ] Matches event schema field names
- [ ] Uses `average_price` (not `entry_price`)

**Stop Loss Tracking**:
- [ ] `has_stop_loss` updated when stop order placed
- [ ] `stop_price` updated from ORDER_PLACED event
- [ ] `stop_order_id` updated from ORDER_PLACED event

---

### PnLState

**Field Completeness**:
- [ ] `account_id` field present
- [ ] `date` field present (date, not datetime)
- [ ] `realized_pnl` field present **CRITICAL**
- [ ] `realized_pnl_by_symbol` field present (dict)
- [ ] `unrealized_pnl` field present
- [ ] `unrealized_pnl_by_symbol` field present (dict)
- [ ] `peak_unrealized_profit` field present
- [ ] `trade_count` field present
- [ ] `created_at` field present
- [ ] `updated_at` field present

**P&L Updates**:
- [ ] `realized_pnl` incremented from TRADE_EXECUTED
- [ ] Skip if `realized_pnl` is None (opening trades)
- [ ] `unrealized_pnl` recalculated on POSITION_UPDATED
- [ ] `unrealized_pnl` recalculated on QUOTE_UPDATE

**Daily Reset**:
- [ ] New PnLState created daily
- [ ] Values reset to 0.0 at session start
- [ ] Old records archived (not deleted)

---

## SDK Mapping Validation

### Field Name Mapping

**Position Fields**:
- [ ] SDK `contractId` → `contract_id`
- [ ] SDK `accountId` → `account_id`
- [ ] SDK `size` → `size` (unchanged)
- [ ] SDK `averagePrice` → `average_price` **CRITICAL**
- [ ] SDK `unrealizedPnl` → `unrealized_pnl`
- [ ] SDK `realizedPnl` → `realized_pnl`

**Order Fields**:
- [ ] SDK `id` → `order_id`
- [ ] SDK `size` → `quantity` **IMPORTANT**
- [ ] SDK `stopPrice` → `stop_price` **CRITICAL**
- [ ] SDK `limitPrice` → `limit_price`
- [ ] SDK `side` → `side` (unchanged)
- [ ] SDK `type` → `order_type`
- [ ] SDK `status` → `status` (unchanged)

**Trade Fields**:
- [ ] SDK `id` → `trade_id`
- [ ] SDK `quantity` → `size` **IMPORTANT**
- [ ] SDK `profitAndLoss` → `realized_pnl` **CRITICAL**
- [ ] SDK `accountId` → `account_id` **CRITICAL**

**Quote Fields**:
- [ ] SDK `last` → `last_price` **CRITICAL**
- [ ] SDK `bid` → `bid` (unchanged)
- [ ] SDK `ask` → `ask` (unchanged)

**Account Fields**:
- [ ] SDK `canTrade` → `can_trade` **CRITICAL**
- [ ] SDK `balance` → `balance` (unchanged)

---

### Symbol Extraction

- [ ] Symbol extracted from `contractId`
- [ ] Format: `CON.F.US.{SYMBOL}.{EXPIRY}` → `{SYMBOL}`
- [ ] Examples: `CON.F.US.MNQ.Z25` → `MNQ`
- [ ] Handles invalid formats gracefully

---

## Rule Specification Validation

### RULE-001 (Max Contracts)

**Event Subscriptions**:
- [ ] Subscribes to POSITION_OPENED
- [ ] Subscribes to POSITION_UPDATED
- [ ] Subscribes to POSITION_CLOSED

**Field References**:
- [ ] Uses `size` field (not `position_size`)
- [ ] Uses signed `size` (not separate `type` field)

---

### RULE-003 (Daily Realized Loss)

**Event Subscriptions**:
- [ ] Subscribes to TRADE_EXECUTED

**Field References**:
- [ ] Uses `realized_pnl` field (NOT `pnl` or `profitAndLoss`)
- [ ] Checks if `realized_pnl is not None` before using
- [ ] Skips opening trades (None values)

---

### RULE-004/005 (Unrealized P&L)

**Event Subscriptions**:
- [ ] Subscribes to POSITION_OPENED
- [ ] Subscribes to POSITION_UPDATED
- [ ] Subscribes to POSITION_CLOSED
- [ ] Subscribes to QUOTE_UPDATE

**Field References**:
- [ ] Uses `average_price` (NOT `entry_price` or `avgPrice`)
- [ ] Uses `last_price` from QUOTE_UPDATE (NOT `price`)
- [ ] Uses `size` field

---

### RULE-008 (Stop Loss Grace)

**Event Subscriptions**:
- [ ] Subscribes to POSITION_OPENED
- [ ] Subscribes to ORDER_PLACED

**Field References**:
- [ ] Checks `order_type == 3` (STOP)
- [ ] Checks `stop_price` field exists
- [ ] Matches `contract_id` between position and order

---

### RULE-010 (Auth Loss Guard)

**Event Subscriptions**:
- [ ] Subscribes to ACCOUNT_UPDATED

**Field References**:
- [ ] Checks `can_trade` field (NOT `canTrade`)
- [ ] Triggers when `can_trade` becomes False

---

## Test Schema Validation

### Mock SDK Data

**Position Mock Data**:
- [ ] Uses `contractId` (camelCase)
- [ ] Uses `accountId` (camelCase)
- [ ] Uses `averagePrice` (camelCase) **NOT** `avgPrice`
- [ ] Uses `unrealizedPnl` (camelCase)
- [ ] Uses `realizedPnl` (camelCase)

**Trade Mock Data**:
- [ ] Uses `id` for trade_id
- [ ] Uses `quantity` (SDK convention)
- [ ] Uses `profitAndLoss` (camelCase)
- [ ] Uses `accountId` (camelCase)
- [ ] Sets `profitAndLoss: None` for opening trades
- [ ] Sets `profitAndLoss: float` for closing trades

**Order Mock Data**:
- [ ] Uses `id` for order_id
- [ ] Uses `size` (SDK convention for orders)
- [ ] Uses `stopPrice` (camelCase)
- [ ] Uses `limitPrice` (camelCase)
- [ ] Uses `side: 1` or `side: 2` (NOT 0)
- [ ] Uses `type: 3` for stop orders
- [ ] Uses `status: 6` for PENDING_TRIGGER

---

### Test Assertions

**Position Event Tests**:
- [ ] Assert `event["average_price"]` exists (NOT `entry_price`)
- [ ] Assert `event["account_id"]` exists
- [ ] Assert `event["timestamp"]` is datetime (NOT string)

**Trade Event Tests**:
- [ ] Assert `event["realized_pnl"]` can be None
- [ ] Test opening trade (realized_pnl=None)
- [ ] Test closing trade (realized_pnl=float)
- [ ] Assert `event["account_id"]` exists

**Order Event Tests**:
- [ ] Assert `event["stop_price"]` exists for stop orders
- [ ] Assert `event["order_type"] == 3` for stop orders
- [ ] Assert `event["side"]` is 1 or 2 (NOT 0)
- [ ] Assert `event["quantity"]` exists (NOT `size`)

---

## Cross-Document Consistency

### Documentation Alignment

**event-data-schemas.md**:
- [ ] All field names match SDK_EVENTS_QUICK_REFERENCE.txt
- [ ] All enum values documented
- [ ] All nullable fields marked
- [ ] Examples include account_id

**state-tracking-schemas.md**:
- [ ] Field names match event-data-schemas.md
- [ ] Uses `average_price` (not `entry_price`)
- [ ] Includes stop-loss tracking fields

**schema-to-sdk-mapping.md**:
- [ ] All SDK fields documented
- [ ] All mappings show before/after
- [ ] Common errors documented
- [ ] Examples match event-data-schemas.md

**Rule Specifications**:
- [ ] Field references match event-data-schemas.md
- [ ] Event subscriptions correct
- [ ] No references to deprecated field names

---

## Common Issues Checklist

### Field Name Issues

- [ ] ❌ No references to `entry_price` (use `average_price`)
- [ ] ❌ No references to `avgPrice` (use `average_price`)
- [ ] ❌ No references to `pnl` (use `realized_pnl` or `unrealized_pnl`)
- [ ] ❌ No references to `profitAndLoss` (use `realized_pnl`)
- [ ] ❌ No mixing of `size` and `quantity` in same context

### Enum Value Issues

- [ ] ❌ No use of `side: 0` for BUY (should be 1)
- [ ] ❌ No use of separate `type` field for positions (use signed `size`)
- [ ] ❌ No use of string enums where int expected

### Nullable Field Issues

- [ ] ❌ No direct arithmetic on `realized_pnl` without None check
- [ ] ❌ No assumptions that `stop_price` always exists
- [ ] ❌ No assumptions that optional account fields exist

### Timestamp Issues

- [ ] ❌ No storing timestamps as strings in events
- [ ] ❌ No comparing string timestamps to datetime objects

### Account ID Issues

- [ ] ❌ No events missing `account_id` field
- [ ] ❌ No state tracking without `account_id`

---

## Validation Procedure

### Step 1: Event Schema Validation
1. Open `event-data-schemas.md`
2. For each event type, verify all fields present
3. Check field names match SDK (camelCase → snake_case)
4. Verify enum values documented
5. Check nullable fields marked

### Step 2: State Schema Validation
1. Open `state-tracking-schemas.md`
2. Verify field names match event schemas
3. Check database schemas match dataclasses
4. Verify stop-loss tracking fields present

### Step 3: SDK Mapping Validation
1. Open `schema-to-sdk-mapping.md`
2. For each event type, verify mapping correct
3. Check all SDK fields documented
4. Verify examples match event-data-schemas.md

### Step 4: Rule Specification Validation
1. For each rule in `docs/specifications/unified/rules/`
2. Verify event subscriptions correct
3. Check field references match event-data-schemas.md
4. Verify no deprecated field names used

### Step 5: Test Validation
1. For each test file in `tests/`
2. Verify mock SDK data uses correct field names
3. Check assertions use canonical field names
4. Verify nullable fields tested

### Step 6: Implementation Validation
1. Open `src/risk_manager/sdk/event_bridge.py`
2. Verify all mappings match schema-to-sdk-mapping.md
3. Check all CRITICAL fields extracted
4. Verify None checks present

---

## Validation Report Template

```markdown
# Schema Validation Report

**Date**: YYYY-MM-DD
**Validator**: [Name]
**Scope**: [Event Type / Module / Rule]

## Summary
- Total Items Checked: X
- Passed: X ✅
- Failed: X ❌
- Warnings: X ⚠️

## Issues Found

### Critical Issues (❌)
1. [Description]
   - Location: [File:Line]
   - Expected: [Correct value]
   - Actual: [Incorrect value]
   - Fix: [Action required]

### Warnings (⚠️)
1. [Description]
   - Location: [File:Line]
   - Recommendation: [Action suggested]

## Checklist Results
- [ ] Event Schema Validation: [PASS/FAIL]
- [ ] State Schema Validation: [PASS/FAIL]
- [ ] SDK Mapping Validation: [PASS/FAIL]
- [ ] Rule Specification Validation: [PASS/FAIL]
- [ ] Test Schema Validation: [PASS/FAIL]
- [ ] Cross-Document Consistency: [PASS/FAIL]

## Next Steps
1. [Action item 1]
2. [Action item 2]

---
**Status**: [COMPLETE / IN PROGRESS]
```

---

## Automated Validation Scripts

### Schema Linter Script

```python
"""
Schema validation linter script.
Run: python scripts/validate_schemas.py
"""

def validate_event_schemas():
    """Validate all event schemas match canonical definitions."""
    errors = []

    # Check event-data-schemas.md
    event_schema_doc = load_markdown("docs/specifications/unified/data-schemas/event-data-schemas.md")

    # Validate POSITION_OPENED
    if "average_price" not in event_schema_doc["POSITION_OPENED"]:
        errors.append("POSITION_OPENED missing average_price field")
    if "entry_price" in event_schema_doc["POSITION_OPENED"]:
        errors.append("POSITION_OPENED uses deprecated entry_price field")

    # Validate TRADE_EXECUTED
    if "realized_pnl" not in event_schema_doc["TRADE_EXECUTED"]:
        errors.append("TRADE_EXECUTED missing realized_pnl field")
    if "pnl" in event_schema_doc["TRADE_EXECUTED"]:
        errors.append("TRADE_EXECUTED uses deprecated pnl field")

    # ... more validations

    return errors

def validate_rule_specifications():
    """Validate rule specs use correct field names."""
    errors = []

    for rule_file in glob.glob("docs/specifications/unified/rules/RULE-*.md"):
        content = read_file(rule_file)

        # Check for deprecated field names
        if "entry_price" in content and "RULE-004" in rule_file:
            errors.append(f"{rule_file}: Uses deprecated entry_price (should be average_price)")

        if "profitAndLoss" in content and "RULE-003" in rule_file:
            errors.append(f"{rule_file}: Uses SDK field profitAndLoss (should be realized_pnl)")

        # ... more validations

    return errors

if __name__ == "__main__":
    all_errors = []
    all_errors.extend(validate_event_schemas())
    all_errors.extend(validate_rule_specifications())

    if all_errors:
        print("❌ Schema validation failed:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ All schema validations passed")
        sys.exit(0)
```

---

## References

- **Event Schemas**: `docs/specifications/unified/data-schemas/event-data-schemas.md`
- **State Schemas**: `docs/specifications/unified/data-schemas/state-tracking-schemas.md`
- **SDK Mapping**: `docs/specifications/unified/data-schemas/schema-to-sdk-mapping.md`
- **SDK Reference**: `SDK_EVENTS_QUICK_REFERENCE.txt`
- **Audit Report**: `docs/specifications/unified/DATA_SCHEMA_CONSISTENCY_AUDIT.md`

---

**Document Status**: Operational Checklist ✅
**Last Reviewed**: 2025-10-27
**Next Review**: Weekly during active development
