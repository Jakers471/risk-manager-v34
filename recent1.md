Great—those scans are super telling. Here’s what they mean and exactly what to do next.

## What the scans just proved

**1) Raw SDK field names are leaking past integrations into core & rules.**
Hits for `contractId`, `averagePrice`, `position.type` in:

* `core/engine.py` (violation handling)
* Multiple **rules** (`daily_unrealized_loss.py`, `max_unrealized_profit.py`, `trade_management.py`, etc.)
* `sdk/event_bridge.py` and `integrations/trading.py` (expected here)

✅ Expected: only integrations/adapters should touch SDK shapes.
❌ Current: rules & engine depend on SDK naming → mapping bugs & drift risk.

**2) Rules are reading `event.data` directly.**
Lots of hits in rules. That’s a schema-free escape hatch, so mismatches hide until runtime.

**3) Silent fallbacks (`.get(..., 0/0.0/None)`) on critical paths.**
Found across core, integrations, and rules—e.g. tick value lookups and PnL fields.
This masks mapping/unit errors and yields wrong enforcement with “valid-looking” numbers.

**4) Alias normalization is spotty.**
Used inside `integrations/trading.py` (good), but **not** guaranteed for what rules/engine see.

**5) No hardcoded `tick_value = <number>`**
Good—but several rules use `self.tick_values.get(symbol, 0.0)` → a different silent failure mode.

---

## What will break if you drop in an adapter today?

If you flip to **canonical types** immediately, rules that read `event.data[...]` or `contractId` will crash or act inconsistently. That’s why we migrate in **shadow + phased** mode.

---

## Surgical, low-risk plan (in this order)

### 1) Add canonical fields without removing the old ones (shadow mode)

* In your ingestion path (event bridge): attach **typed, normalized fields** on the event (`event.symbol_root`, `event.contract_id`, `event.position`, etc.) **while still populating `event.data`**.
* Add **one log line** per event showing `RAW → NORMALIZED` (symbol, side, qty).
  Goal: zero behavior change, just extra data + visibility.

### 2) Centralize two utilities and forbid fallbacks

* `normalize_symbol(symbol_or_contract) → symbol_root` (use ALIASES).
* `get_tick_economics(symbol_root) → {size, tick_value}`.
  **Rule:** no `.get(..., 0/None)` on these—**raise** if unknown. Wrong data must fail loud.

### 3) Convert the **3 wired rules** only

* Update those three to read **typed fields** (not `event.data`) and to call `get_tick_economics()` for tick math.
* Add invariants inside the rule (or before rule dispatch):

  * symbol exists in tick table,
  * prices align to tick size,
  * P&L sign matches side.
* Keep the remaining (10) rules as-is temporarily.

### 4) Lock the engine interface

* Replace `violation.get("contractId")` with your **canonical** `contract_id` in the engine.
* Start emitting a **warning** whenever a rule reads `event.data[...]` for core fields (graduated enforcement: warn → deprecate → block).

### 5) Add 3 contract tests (quick wins)

* **SDK → Canonical Position** (fixture from real logs).
* **Alias normalization** (ENQ→NQ, MNQ→MNQ).
* **Tick economics** (ES 10 ticks = $125; MNQ 10 ticks = $5).
  These catch the exact classes of bugs the scans revealed.

---

## How to see what’s “correct” in `dev_runner.py` today

Add a **diagnostic shadow run** (no behavior change):

* For each event, compute decisions twice:

  * **Legacy** (current rules as-is).
  * **Canonical** (normalized fields + tick table) **for the 3 converted rules only**.
* Print a **summary at exit**:

  * `typed_positions%`, `alias_normalizations`, `tick_table_uses vs hardcoded=0`,
  * `decision_match_rate (legacy vs canonical)` for the 3 rules,
  * `invariant_violations_by_type` (symbol unknown, price off-tick, sign mismatch).
* If match rate < 100% or any invariant fires, it will list **trace_id + rule name** so you can jump to the exact spot.

This lets you **prove** the new path is correct before flipping any switches.

---

## Quick follow-up scans (rerun after step 3)

**Rules touching SDK fields or event.data for core:**

```
Get-ChildItem -Recurse src\risk_manager\rules | Select-String -Pattern 'contractId|averagePrice|position\.type|event\.data'
```

Target: ✅ **zero** hits for those core fields after you migrate each rule.

**Silent fallbacks on finance-critical paths:**

```
Get-ChildItem -Recurse src | Select-String -Pattern '\.get\(.+,\s*(0|0\.0|None|\".*\")\)'
```

Target: none in **rules/engine** for symbol/price/pnl/ticks.

---

## What this means for your current state

Yes—this is why adding risk rules has felt tedious despite lots of tests:

* Your **tests validate math**, but **runtime fails** come from **mapping/units/alias** gaps and **silent defaults**.
* Until you add the **adapter + no-fallback policy** and move rules off `event.data`, you’ll keep seeing “works in tests, weird in prod.”

Do the shadowed adapter + migrate your 3 rules now. You’ll get immediate signal without breaking the other 10—and a clear list of what to fix next.
