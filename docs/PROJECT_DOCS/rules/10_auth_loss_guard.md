---
doc_id: RULE-010
version: 2.0
last_updated: 2025-01-17
dependencies: [MOD-001, MOD-002]
enforcement_type: Hard Lockout (API-Driven)
---

# RULE-010: AuthLossGuard

**Purpose:** Monitor TopstepX `canTrade` status and lockout when API signals account is restricted.

## Config
```yaml
auth_loss_guard:
  enabled: true
  enforcement: "close_all_and_lockout"
```

## Trigger
**Event:** `GatewayUserAccount`

**Logic:**
```python
def check(account_event):
    can_trade = account_event['canTrade']

    if not can_trade:
        return BREACH  # TopstepX API says account cannot trade
```

**API Event Payload:**
```json
{
  "id": 123,
  "balance": 10000.0,
  "canTrade": false   // ← This triggers breach
}
```

## Enforcement
1. Close all positions (MOD-001)
2. Set lockout (MOD-002) - no expiry time (manual unlock only)
3. Display: `"🔴 ACCOUNT RESTRICTED - Contact TopstepX support"`

**Auto-Unlock:** When `canTrade: true` event received, lockout clears automatically.

**Use Case:** TopstepX may disable trading (rule violation, margin call, etc.) - this enforces it.
