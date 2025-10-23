---
doc_id: RULE-011
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001, MOD-002]
enforcement_type: Hard Lockout (Symbol-Specific)
---

# RULE-011: SymbolBlocks

**Purpose:** Blacklist specific symbols - close any position immediately and permanently lockout that symbol.

## Config
```yaml
symbol_blocks:
  enabled: true
  blocked_symbols:
    - "RTY"     # Russell 2000 - never trade
    - "BTC"     # Bitcoin futures - never trade
  enforcement: "close_and_lockout_symbol"
```

## Trigger
**Event:** `GatewayUserPosition`

**Logic:**
```python
def check(position_event):
    symbol = extract_symbol(position_event['contractId'])  # "CON.F.US.RTY.U25" → "RTY"

    if symbol in config['blocked_symbols']:
        return BREACH, symbol
```

## Enforcement
1. Close position immediately (MOD-001)
2. Set **permanent** symbol lockout (MOD-002):
   - `set_lockout(account_id, f"Symbol {symbol} is blacklisted", until=datetime.max)`
3. Any future fills in this symbol → close instantly

**Use Case:** "I always lose on RTY, never let me trade it."

**Lockout Type:** Symbol-specific permanent lockout (no expiry).
