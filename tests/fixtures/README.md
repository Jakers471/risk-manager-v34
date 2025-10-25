# Test Fixtures Documentation

**Created:** 2025-01-17
**Total Fixtures:** 139
**Total Files:** 11

---

## Overview

This directory contains all pytest fixtures for testing the Simple Risk Manager. Fixtures provide mock data, API responses, and sample objects for isolated unit testing.

---

## Fixture Categories

### 1. **positions.py** (16 fixtures)
Position state fixtures for testing risk rules and position management.

**Key Fixtures:**
- `single_es_long_position` - Single ES long (1 contract)
- `single_nq_short_position` - Single NQ short (1 contract)
- `two_open_positions_mixed` - Two positions (ES long, NQ short)
- `three_mnq_long_positions` - Three MNQ positions
- `max_contracts_breach_positions` - 6 positions breaching limit
- `position_with_unrealized_loss` - Position with -$300 loss
- `position_with_unrealized_profit` - Position with +$1000 profit
- `position_at_breakeven` - Position at $0 P&L
- `position_without_stop_loss` - Position without stop-loss
- `position_in_blocked_symbol` - RTY position (blocked)
- `empty_positions_list` - No positions
- `large_position_size` - 10 contracts
- `hedged_positions` - Long + short in same instrument

**Usage Example:**
```python
def test_max_contracts_rule(two_open_positions_mixed):
    assert len(two_open_positions_mixed) == 2
    assert two_open_positions_mixed[0]["size"] == 2
```

---

### 2. **api_responses.py** (30+ fixtures)
Mock HTTP responses from TopstepX REST API.

**Categories:**
- **Authentication:** `auth_success_response`, `auth_failure_response`, `auth_expired_token_response`
- **Positions:** `positions_open_response`, `position_close_success_response`, `position_partial_close_response`
- **Orders:** `orders_open_response`, `order_cancel_success_response`, `order_place_success_response`
- **Contracts:** `contract_mnq_response`, `contract_es_response`, `contracts_list_response`
- **Errors:** `rate_limit_error_response`, `server_error_response`, `timeout_error_response`

**Usage Example:**
```python
@pytest.mark.parametrize("response", ["positions_open_response"], indirect=True)
def test_load_positions(response):
    assert len(response) == 2
```

---

### 3. **signalr_events.py** (28+ fixtures)
Mock SignalR WebSocket event payloads.

**Event Types:**
- **GatewayUserTrade:** `trade_profit_event`, `trade_loss_event`, `trade_large_loss_event`
- **GatewayUserPosition:** `position_opened_event`, `position_scaled_in_event`, `position_closed_event`
- **GatewayUserOrder:** `order_placed_event`, `order_filled_event`, `order_canceled_event`
- **MarketQuote:** `quote_mnq_normal`, `quote_mnq_moved_down`, `quote_mnq_moved_up`
- **GatewayUserAccount:** `account_update_event`, `account_auth_event`

**Usage Example:**
```python
def test_trade_loss_handler(trade_loss_event):
    assert trade_loss_event["profitAndLoss"] < 0
    # Process loss event
```

---

### 4. **contracts.py** (13 fixtures)
Contract metadata for cache and P&L calculations.

**Contracts:**
- `contract_mnq` - Micro E-mini Nasdaq-100 (tick_value: $0.50)
- `contract_es` - E-mini S&P 500 (tick_value: $12.50)
- `contract_nq` - E-mini Nasdaq-100 (tick_value: $5.00)
- `contract_mes` - Micro E-mini S&P 500 (tick_value: $1.25)
- `contract_rty` - Russell 2000 (blocked symbol)
- `contract_cache_all` - All contracts for cache initialization

**P&L Calculation Helpers:**
- `pnl_calc_mnq_long` - Long 2 @ 21000, current 21500 = +$1000
- `pnl_calc_mnq_long_loss` - Long 2 @ 21000, current 20700 = -$600
- `pnl_calc_es_short` - Short 1 @ 5000, current 4950 = +$625

**Usage Example:**
```python
def test_pnl_calculation(contract_mnq, position_with_unrealized_profit):
    # Calculate P&L using contract tick values
    pnl = calculate_pnl(contract_mnq, position_with_unrealized_profit, quote)
```

---

### 5. **accounts.py** (10 fixtures)
Account configuration fixtures.

**Fixtures:**
- `account_test_primary` - Primary test account (ID: 123)
- `account_test_secondary` - Secondary account (ID: 456)
- `account_disabled` - Disabled account (enabled=False)
- `accounts_multiple` - List of 3 accounts
- `account_config_full` - Full config with all optional fields
- `account_suspended_status` - Suspended account status
- `account_active_status` - Active account status

---

### 6. **configs.py** (13 fixtures)
Risk configuration YAML fixtures.

**Configurations:**
- `risk_config_all_enabled` - All 12 rules enabled (default)
- `risk_config_minimal` - Only 3 critical rules
- `risk_config_strict_mode` - Strict mode enabled
- `risk_config_all_disabled` - All rules disabled
- `risk_config_aggressive_limits` - Tight limits (testing edge cases)
- `risk_config_permissive_limits` - Loose limits
- `risk_config_breakeven_mode` - Max profit in breakeven mode
- `risk_config_24_7_trading` - No session restrictions
- `risk_config_invalid_yaml` - Invalid config for testing validation

**Usage Example:**
```python
def test_config_loader(risk_config_all_enabled):
    loader = RuleLoader(risk_config_all_enabled)
    rules = loader.load_rules()
    assert len(rules) == 12
```

---

### 7. **orders.py** (11 fixtures)
Order state fixtures for order management testing.

**Fixtures:**
- `order_stop_loss_working` - Active stop-loss order
- `order_limit_working` - Active limit order
- `order_filled` - Filled order (no longer working)
- `order_canceled` - Canceled order
- `order_partial_fill` - Partially filled order
- `order_rejected` - Rejected order (insufficient margin)
- `orders_multiple_working` - Multiple working orders
- `order_blocked_symbol` - Order in blocked symbol

---

### 8. **trades.py** (10 fixtures)
Trade history fixtures for frequency and P&L tracking.

**Fixtures:**
- `trade_single_profit` - Single profitable trade (+$45.50)
- `trade_single_loss` - Single loss trade (-$120.00)
- `trade_large_loss_breach` - Large loss (-$550.00)
- `trade_cooldown_trigger` - Loss triggering cooldown (-$105.00)
- `trades_sequence_losses` - 3 consecutive losses
- `trades_high_frequency` - 35 trades in 1 hour (breach)
- `trades_within_frequency_limit` - 25 trades in 1 hour (OK)
- `trades_mixed_pnl` - Mix of profits and losses

---

### 9. **lockouts.py** (10 fixtures)
Lockout state fixtures for testing lockout management.

**Fixtures:**
- `lockout_active_daily_loss` - Active lockout (daily loss)
- `lockout_active_unrealized_loss` - Active lockout (unrealized loss)
- `lockout_active_auth_guard` - Permanent lockout (auth bypass)
- `lockout_expired` - Expired lockout (auto-unlock)
- `lockout_not_locked` - No active lockout
- `lockout_permanent` - Permanent lockout (locked_until=None)
- `lockout_nearly_expired` - Expires in 1 minute

---

### 10. **quotes.py** (9 fixtures)
Market quote fixtures for real-time P&L calculations.

**Fixtures:**
- `quote_mnq_current` - Current MNQ quote
- `quote_mnq_high` - MNQ at high price (profit)
- `quote_mnq_low` - MNQ at low price (loss)
- `quote_es_current` - Current ES quote
- `quote_nq_current` - Current NQ quote
- `quote_stale` - Old timestamp (>60 seconds)
- `quote_wide_spread` - Wide bid-ask spread
- `quotes_streaming` - Sequence of 3 quote updates

---

## Fixture Usage Patterns

### Pattern 1: Direct Fixture Injection
```python
def test_position_count(two_open_positions_mixed):
    """Direct injection of fixture"""
    assert len(two_open_positions_mixed) == 2
```

### Pattern 2: Parametrized Fixtures
```python
@pytest.mark.parametrize("position", [
    "single_es_long_position",
    "single_nq_short_position"
], indirect=True)
def test_position_types(position):
    assert position["type"] in [1, 2]
```

### Pattern 3: Multiple Fixtures
```python
def test_pnl_calculation(contract_mnq, position_with_unrealized_profit, quote_mnq_high):
    """Use multiple fixtures together"""
    pnl = calculate_pnl(contract_mnq, position_with_unrealized_profit, quote_mnq_high)
    assert pnl > 0
```

### Pattern 4: Fixture Composition
```python
@pytest.fixture
def complete_test_scenario(two_open_positions_mixed, order_stop_loss_working, contract_cache_all):
    """Compose multiple fixtures into one"""
    return {
        "positions": two_open_positions_mixed,
        "orders": [order_stop_loss_working],
        "contracts": contract_cache_all
    }
```

---

## Testing Different Rule Scenarios

### RULE-001: Max Contracts
```python
def test_max_contracts_breach(max_contracts_breach_positions, risk_config_all_enabled):
    rule = MaxContractsRule(risk_config_all_enabled["rules"]["max_contracts"])
    action = rule.check(max_contracts_breach_positions)
    assert action is not None
```

### RULE-003: Daily Realized Loss
```python
def test_daily_loss_limit(trade_large_loss_breach, risk_config_all_enabled):
    rule = DailyRealizedLossRule(risk_config_all_enabled["rules"]["daily_realized_loss"])
    action = rule.check(trade_large_loss_breach)
    assert action.type == "CLOSE_ALL_AND_LOCKOUT"
```

### RULE-004: Daily Unrealized Loss
```python
def test_unrealized_loss(position_with_unrealized_loss, quote_mnq_low, contract_mnq):
    rule = DailyUnrealizedLossRule(config)
    pnl = calculate_unrealized_pnl(position_with_unrealized_loss, quote_mnq_low, contract_mnq)
    assert pnl < -300.00
```

### RULE-006: Trade Frequency
```python
def test_trade_frequency_breach(trades_high_frequency, risk_config_all_enabled):
    rule = TradeFrequencyLimitRule(config)
    action = rule.check(trades_high_frequency)
    assert action is not None  # 35 trades > 30 limit
```

### RULE-008: No Stop-Loss Grace
```python
def test_no_stop_loss_grace(position_without_stop_loss, empty_orders_list):
    rule = NoStopLossGraceRule(config)
    action = rule.check(position_without_stop_loss, empty_orders_list)
    assert action is not None  # Position without stop-loss > 30s
```

---

## Fixture Statistics

| Category | File | Fixtures | Lines | Purpose |
|----------|------|----------|-------|---------|
| Positions | positions.py | 16 | 220 | Position states and scenarios |
| API Responses | api_responses.py | 30+ | 450 | Mock REST API responses |
| SignalR Events | signalr_events.py | 28+ | 480 | Mock WebSocket events |
| Contracts | contracts.py | 13 | 240 | Contract metadata and P&L helpers |
| Accounts | accounts.py | 10 | 110 | Account configurations |
| Configs | configs.py | 13 | 380 | Risk rule configurations |
| Orders | orders.py | 11 | 180 | Order states |
| Trades | trades.py | 10 | 230 | Trade history |
| Lockouts | lockouts.py | 10 | 160 | Lockout states |
| Quotes | quotes.py | 9 | 150 | Market quotes |

**Total:** 139 fixtures across 11 files, ~2,600 lines of code

---

## Best Practices

### 1. Naming Convention
- Use descriptive names: `position_with_unrealized_loss` not `pos1`
- Include scenario: `trades_high_frequency` describes breach scenario
- Prefix with category: `quote_mnq_high`, `order_stop_loss_working`

### 2. Data Realism
- Use realistic values (MNQ @ 21000, ES @ 5000)
- Include proper timestamps
- Match TopstepX API format exactly

### 3. Test Coverage
- Each fixture covers specific scenario
- Fixtures combine for integration tests
- Edge cases have dedicated fixtures (`quote_zero_bid`, `lockout_permanent`)

### 4. Maintainability
- One fixture per scenario
- Avoid fixture dependencies
- Document expected outcomes in docstrings

---

## Adding New Fixtures

### Step 1: Choose Category
Determine which file to add fixture to based on data type.

### Step 2: Create Fixture
```python
@pytest.fixture
def my_new_fixture():
    """Clear description of scenario"""
    return {
        # Mock data matching API/DB format
    }
```

### Step 3: Update This README
Add fixture to appropriate category section.

### Step 4: Test Fixture
```python
def test_my_fixture(my_new_fixture):
    assert my_new_fixture is not None
```

---

## Related Documentation

- **Test Plan:** `/home/jakers/projects/simple-risk-manager/simple risk manager/reports/2025-10-22-spec-governance/04-testing/TEST_FIXTURES_PLAN.md`
- **Data Model Spec:** `/home/jakers/projects/simple-risk-manager/simple risk manager/project-specs/SPECS/07-DATA-MODELS/DATABASE_SCHEMA.md`
- **API Spec:** `/home/jakers/projects/simple-risk-manager/simple risk manager/project-specs/SPECS/01-EXTERNAL-API/`
- **Risk Rules:** `/home/jakers/projects/simple-risk-manager/simple risk manager/project-specs/SPECS/03-RISK-RULES/`

---

**Generated:** 2025-01-17
**Status:** Complete and ready for use
**Coverage:** All 12 risk rules + API integration + error scenarios
