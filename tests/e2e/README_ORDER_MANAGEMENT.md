# E2E Tests: Order Management (RULE-011 & RULE-012)

## Quick Start

```bash
# Run all order management E2E tests
pytest tests/e2e/test_order_management_e2e.py -v

# Expected output: ============================= 10 passed in 0.23s ==============================
```

---

## Test Organization

### TestSymbolBlocksE2E (RULE-011) - 4 tests
```bash
pytest tests/e2e/test_order_management_e2e.py::TestSymbolBlocksE2E -v
```

**Tests:**
1. `test_symbol_block_exact_match` - Block specific symbol ("MNQ")
2. `test_symbol_block_wildcard_pattern` - Block pattern ("ES*")
3. `test_symbol_block_case_insensitive` - Case-insensitive matching
4. `test_symbol_block_closes_existing_positions` - Violation on existing positions

### TestTradeManagementE2E (RULE-012) - 5 tests
```bash
pytest tests/e2e/test_order_management_e2e.py::TestTradeManagementE2E -v
```

**Tests:**
1. `test_trade_management_auto_stop_loss` - Auto stop-loss placement
2. `test_trade_management_bracket_order` - Bracket orders (stop + target)
3. `test_trade_management_trailing_stop` - Trailing stop adjustment
4. `test_trade_management_short_position_stop_loss` - Short position stop
5. `test_trade_management_multiple_symbols` - Multi-symbol management

### TestOrderManagementIntegration - 1 test
```bash
pytest tests/e2e/test_order_management_e2e.py::TestOrderManagementIntegration -v
```

**Tests:**
1. `test_symbol_blocks_prevents_trade_management` - Rule interaction

---

## Run Specific Test

```bash
# Single test
pytest tests/e2e/test_order_management_e2e.py::TestSymbolBlocksE2E::test_symbol_block_exact_match -v

# With output
pytest tests/e2e/test_order_management_e2e.py::TestSymbolBlocksE2E::test_symbol_block_exact_match -v -s
```

---

## Coverage Report

```bash
# Generate coverage report
pytest tests/e2e/test_order_management_e2e.py \
  --cov=risk_manager.rules.symbol_blocks \
  --cov=risk_manager.rules.trade_management \
  --cov-report=html \
  --cov-report=term

# View HTML report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

---

## What These Tests Validate

### RULE-011: Symbol Blocks
- ✅ Exact symbol matching ("MNQ" blocks "MNQ")
- ✅ Wildcard patterns ("ES*" blocks "ES", "ESH25", etc.)
- ✅ Case-insensitive matching ("mnq" blocks "MNQ")
- ✅ Violations on position opened/updated events
- ✅ Non-matching symbols remain allowed
- ✅ Action directive included in violation

### RULE-012: Trade Management
- ✅ Auto stop-loss placement at correct price
- ✅ Auto take-profit placement at correct price
- ✅ Bracket orders (both stop + target)
- ✅ Trailing stop adjustment on favorable price moves
- ✅ Direction-aware stops (long below entry, short above)
- ✅ Independent management per symbol
- ✅ Correct tick size calculations per symbol

### Integration
- ✅ Both rules evaluate on same event
- ✅ Both violations detected correctly
- ✅ Enforcement layer receives both actions

---

## Test Performance

```
Total Tests: 10
Pass Rate: 100% (10/10)
Execution Time: ~0.23 seconds
Average per Test: ~23ms
```

---

## Debugging Failed Tests

If a test fails:

```bash
# Run with full traceback
pytest tests/e2e/test_order_management_e2e.py::TestName::test_name -v --tb=long

# Run with print statements visible
pytest tests/e2e/test_order_management_e2e.py::TestName::test_name -v -s

# Run with warnings
pytest tests/e2e/test_order_management_e2e.py::TestName::test_name -v -W all

# Run with pdb debugger
pytest tests/e2e/test_order_management_e2e.py::TestName::test_name -v --pdb
```

---

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run Order Management E2E Tests
  run: |
    pytest tests/e2e/test_order_management_e2e.py \
      -v \
      --junitxml=test-results/e2e-order-management.xml \
      --cov=risk_manager.rules \
      --cov-report=xml
```

### Pre-commit Hook
```bash
# Add to .git/hooks/pre-commit
pytest tests/e2e/test_order_management_e2e.py --tb=short || exit 1
```

---

## Related Files

### Source Code
- `src/risk_manager/rules/symbol_blocks.py` - RULE-011 implementation
- `src/risk_manager/rules/trade_management.py` - RULE-012 implementation
- `src/risk_manager/core/engine.py` - Rule evaluation engine
- `src/risk_manager/sdk/enforcement.py` - Enforcement executor

### Other Tests
- `tests/unit/test_rules/test_symbol_blocks.py` - Unit tests
- `tests/unit/test_rules/test_trade_management.py` - Unit tests
- `tests/integration/test_rules_integration.py` - Integration tests
- `tests/e2e/test_event_pipeline_e2e.py` - Event pipeline tests

### Documentation
- `E2E_ORDER_MANAGEMENT_TESTS_SUMMARY.md` - Complete test summary
- `docs/specifications/unified/rules/RULE-011-SYMBOL-BLOCKS.md`
- `docs/specifications/unified/rules/RULE-012-TRADE-MANAGEMENT.md`

---

## FAQs

**Q: Why don't tests call enforcement methods?**
A: Rules detect violations and return action directives. The engine's enforcement layer acts on those directives. These E2E tests verify rules detect correctly.

**Q: Why use Mock SDK instead of live SDK?**
A: Mock SDK provides fast, isolated, repeatable tests. Live SDK tests would require practice account and are slower. Mock is sufficient for E2E logic validation.

**Q: What's the difference between unit, integration, and E2E tests?**
- **Unit**: Test rule logic in isolation (no engine, no SDK)
- **Integration**: Test rule + engine interaction (mock trading)
- **E2E**: Test complete event pipeline (rule + engine + mock SDK)

**Q: Can I run these tests in parallel?**
A: Yes, use `pytest-xdist`:
```bash
pytest tests/e2e/test_order_management_e2e.py -n auto
```

---

## Support

For issues or questions:
1. Check test output and tracebacks
2. Review test docstrings for expected behavior
3. Check `E2E_ORDER_MANAGEMENT_TESTS_SUMMARY.md` for details
4. Review source code implementations

---

**Last Updated**: 2025-10-28
**Status**: All tests passing ✅
