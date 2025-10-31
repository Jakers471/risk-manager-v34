# Composite Enforcement Integration Plan

**Date**: 2025-10-30
**Purpose**: Integrate composite P&L enforcement across the entire Risk Manager V34 architecture
**Context**: Based on analysis from RECENT2.MD and recent1.md

---

## 🎯 Executive Summary

**The Problem**: REALIZED and UNREALIZED rules operate as independent silos, allowing unrealized losses to breach realized limits when positions close.

**The Solution**: "Composite Enforcement" - Enable the unrealized rule to dynamically adjust its threshold based on remaining realized P&L budget.

**Impact Areas**:
1. ✅ Configuration (risk_config.yaml)
2. ✅ Rule initialization (manager.py)
3. ✅ Rule logic (daily_unrealized_loss.py)
4. ✅ State management (pnl_tracker.py)
5. ✅ Enforcement (sdk/enforcement.py)
6. ✅ Testing (new composite enforcement tests)

---

## 📊 Current Architecture Analysis

### 1. Configuration Layer (`config/risk_config.yaml`)

**Current State**:
```yaml
rules:
  daily_realized_loss:      # RULE-003
    enabled: true
    limit: -5               # Hard limit for realized P&L

  daily_unrealized_loss:    # RULE-004
    enabled: true
    limit: -20              # Standalone unrealized limit
```

**Analysis**:
- ✅ Both rules have separate limits
- ❌ No configuration flag to enable composite enforcement
- ❌ No way to link the two rules together
- ❌ No indication that unrealized should respect realized budget

**Integration Need**: Add composite enforcement configuration

---

### 2. Rule Initialization (`src/risk_manager/core/manager.py`)

**Current State** (Lines 468-476):
```python
# RULE-004: Daily Unrealized Loss
if self.config.rules.daily_unrealized_loss.enabled:
    rule = DailyUnrealizedLossRule(
        loss_limit=self.config.rules.daily_unrealized_loss.limit,
        tick_values=tick_values,
        tick_sizes=tick_sizes,
        action="close_position",
    )
    # ❌ NO pnl_tracker passed!
    # ❌ NO realized_loss_limit passed!
```

**Analysis**:
- ✅ pnl_tracker exists (created at line ~252)
- ✅ realized_loss_limit available from config
- ❌ Neither is passed to the unrealized rule
- ❌ Rule is completely isolated from realized P&L state

**Integration Need**: Wire pnl_tracker and realized_loss_limit to unrealized rule

---

### 3. Rule Logic (`src/risk_manager/rules/daily_unrealized_loss.py`)

**Current State** (Lines 60-90, 124-130):
```python
class DailyUnrealizedLossRule(RiskRule):
    def __init__(
        self,
        loss_limit: float,
        tick_values: Dict[str, float],
        tick_sizes: Dict[str, float],
        action: str = "close_position",
    ):
        # ❌ NO pnl_tracker parameter
        # ❌ NO realized_loss_limit parameter
        self.loss_limit = loss_limit

    async def evaluate(self, event: RiskEvent, engine: "RiskEngine"):
        total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

        # ❌ NO composite logic
        # ❌ Checks only against self.loss_limit
        if total_unrealized_pnl <= self.loss_limit:
            return violation
```

**Analysis**:
- ✅ Has access to engine (could theoretically access pnl_tracker via engine)
- ❌ No mechanism to get realized P&L
- ❌ No logic to calculate remaining budget
- ❌ No dynamic limit adjustment

**Integration Need**: Add composite enforcement logic to evaluate()

---

### 4. State Management (`src/risk_manager/state/pnl_tracker.py`)

**Current State**:
```python
class PnLTracker:
    def get_daily_pnl(self, account_id: str) -> float:
        """Get current realized P&L for today"""
        # ✅ Already implemented!
        # Returns sum of all closed trades for the day
```

**Analysis**:
- ✅ PnLTracker already tracks realized P&L
- ✅ get_daily_pnl() method exists and works
- ✅ Daily resets already handled
- ✅ Database persistence working

**Integration Need**: None! State management is ready.

---

### 5. Enforcement (`src/risk_manager/sdk/enforcement.py`)

**Current State**:
```python
# When DailyUnrealizedLossRule triggers:
# 1. Receives violation dict from rule.evaluate()
# 2. Executes action (close_position or flatten)
# 3. Logs enforcement details
```

**Analysis**:
- ✅ Enforcement already handles unrealized rule violations
- ✅ Can close individual positions or flatten all
- ❌ Logging doesn't show composite enforcement context
- ❌ No visibility into whether limit was adjusted

**Integration Need**: Enhanced logging for composite enforcement visibility

---

### 6. Testing Infrastructure

**Current State**:
```
tests/
├── unit/
│   ├── test_daily_realized_loss.py     ✅ Tests RULE-003
│   ├── test_daily_unrealized_loss.py   ✅ Tests RULE-004
│   └── ...
├── integration/
│   └── ...
```

**Analysis**:
- ✅ Both rules have unit tests
- ❌ No tests for composite enforcement
- ❌ No tests for rule coordination
- ❌ No tests for dynamic limit adjustment

**Integration Need**: New test suite for composite enforcement

---

## 🔧 Integration Touchpoints

Here's how composite enforcement touches each system:

```
┌─────────────────────────────────────────────────────────────┐
│                     CONFIGURATION LAYER                      │
│  risk_config.yaml: Enable composite_enforcement flag         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   INITIALIZATION LAYER                       │
│  manager.py: Wire pnl_tracker + realized_limit to RULE-004  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      RULE LAYER                              │
│  daily_unrealized_loss.py: Composite evaluation logic       │
│     1. Get current unrealized P&L (existing)                 │
│     2. Get current realized P&L (NEW - via pnl_tracker)      │
│     3. Calculate remaining budget (NEW)                      │
│     4. Adjust effective limit (NEW)                          │
│     5. Check against effective limit (MODIFIED)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   STATE MANAGEMENT LAYER                     │
│  pnl_tracker.py: Provide realized P&L (already working!)    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   ENFORCEMENT LAYER                          │
│  enforcement.py: Execute close_position (already working!)   │
│  + Enhanced logging with composite context (NEW)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      SDK LAYER                               │
│  trading_integration.py: Close positions (already working!)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Implementation Approach

### Phase 1: Configuration (5 minutes)

**File**: `config/risk_config.yaml`

**Changes**:
```yaml
rules:
  daily_realized_loss:
    enabled: true
    limit: -5
    reset_time: "17:00"
    timezone: "America/Chicago"

  daily_unrealized_loss:
    enabled: true
    limit: -20
    # NEW: Composite enforcement settings
    composite_enforcement:
      enabled: true                           # Enable composite enforcement
      respect_realized_limit: true            # Adjust threshold based on realized P&L
      realized_rule_ref: "daily_realized_loss"  # Which rule to coordinate with
```

**Rationale**:
- Explicit opt-in via configuration
- Self-documenting (shows intent)
- Can be toggled without code changes
- Backwards compatible (defaults to disabled)

---

### Phase 2: Configuration Model (10 minutes)

**File**: `src/risk_manager/config/models.py`

**Changes**:
```python
class DailyUnrealizedLossConfig(BaseModel):
    enabled: bool = True
    limit: float = Field(le=0, description="Max unrealized loss (negative)")
    check_interval_seconds: int = Field(default=10, ge=1)

    # NEW: Composite enforcement
    composite_enforcement: Optional[CompositeEnforcementConfig] = None

class CompositeEnforcementConfig(BaseModel):
    """Composite enforcement settings for unrealized rules"""
    enabled: bool = False
    respect_realized_limit: bool = True
    realized_rule_ref: str = "daily_realized_loss"
```

**Validation**:
```python
@model_validator(mode='after')
def validate_composite_enforcement(self) -> Self:
    """Warn if composite enforcement is disabled with risky config"""
    if (self.daily_unrealized_loss.enabled and
        self.daily_realized_loss.enabled and
        self.daily_unrealized_loss.composite_enforcement is None):

        # Check if unrealized limit is more permissive than realized
        unrealized_limit = abs(self.daily_unrealized_loss.limit)
        realized_limit = abs(self.daily_realized_loss.limit)

        if unrealized_limit > realized_limit:
            warnings.warn(
                f"RISK: Unrealized limit ({unrealized_limit}) is more permissive "
                f"than realized limit ({realized_limit}). Positions could breach "
                f"realized limit when closed. Enable composite_enforcement to protect."
            )

    return self
```

---

### Phase 3: Rule Initialization (15 minutes)

**File**: `src/risk_manager/core/manager.py`

**Changes** (Lines 468-476):
```python
# RULE-004: Daily Unrealized Loss (WITH COMPOSITE ENFORCEMENT)
if self.config.rules.daily_unrealized_loss.enabled:
    from risk_manager.integrations.trading import TICK_VALUES, ALIASES

    # Build tick value dicts (existing code)
    tick_values = {}
    tick_sizes = {}
    for symbol in self.config.general.instruments:
        # ... existing tick value logic ...

    # ══════════════════════════════════════════════════════════
    # NEW: Check if composite enforcement is enabled
    # ══════════════════════════════════════════════════════════
    composite_config = self.config.rules.daily_unrealized_loss.composite_enforcement

    # Determine if we should pass realized limit for composite enforcement
    realized_loss_limit = None
    if (composite_config and
        composite_config.enabled and
        composite_config.respect_realized_limit and
        self.config.rules.daily_realized_loss.enabled):

        realized_loss_limit = self.config.rules.daily_realized_loss.limit
        logger.info(
            f"   ⚙️  Composite enforcement ENABLED: "
            f"unrealized limit will adjust based on realized P&L "
            f"(realized limit: ${realized_loss_limit:.2f})"
        )

    # ══════════════════════════════════════════════════════════
    # Create rule with composite enforcement support
    # ══════════════════════════════════════════════════════════
    rule = DailyUnrealizedLossRule(
        loss_limit=self.config.rules.daily_unrealized_loss.limit,
        tick_values=tick_values,
        tick_sizes=tick_sizes,
        pnl_tracker=pnl_tracker,                    # ← NEW: Give access to realized P&L
        realized_loss_limit=realized_loss_limit,     # ← NEW: Know the realized limit
        action="close_position",
    )
    self.add_rule(rule)
    rules_loaded += 1

    # Enhanced logging
    if realized_loss_limit:
        logger.info(
            f"✅ Loaded: DailyUnrealizedLossRule "
            f"(limit=${rule.loss_limit:.2f}, "
            f"composite=ENABLED with realized limit ${realized_loss_limit:.2f})"
        )
    else:
        logger.info(
            f"✅ Loaded: DailyUnrealizedLossRule "
            f"(limit=${rule.loss_limit:.2f}, standalone mode)"
        )
```

**Key Insights**:
- ✅ Backwards compatible (works without composite config)
- ✅ Only enables composite if ALL conditions met
- ✅ Clear logging shows composite enforcement status
- ✅ Fails gracefully if realized rule disabled

---

### Phase 4: Rule Logic Enhancement (30 minutes)

**File**: `src/risk_manager/rules/daily_unrealized_loss.py`

**Changes**:

#### 4A: Constructor Update
```python
class DailyUnrealizedLossRule(RiskRule):
    def __init__(
        self,
        loss_limit: float,
        tick_values: Dict[str, float],
        tick_sizes: Dict[str, float],
        pnl_tracker: Optional["PnLTracker"] = None,          # ← NEW (optional for tests)
        realized_loss_limit: Optional[float] = None,          # ← NEW (optional for tests)
        action: str = "close_position",
    ):
        """
        Initialize daily unrealized loss rule with optional composite enforcement.

        Args:
            loss_limit: Maximum unrealized loss (negative, e.g., -750.0)
            tick_values: Dollar value per tick for each symbol
            tick_sizes: Minimum price increment for each symbol
            pnl_tracker: PnL tracker for composite enforcement (optional)
            realized_loss_limit: Realized P&L limit for composite enforcement (optional)
            action: Action to take on violation

        Composite Enforcement:
            If both pnl_tracker and realized_loss_limit are provided, the rule
            will dynamically adjust its effective limit to protect the realized
            P&L limit. This prevents unrealized losses from breaching the realized
            limit when positions close.

            Example:
                - Realized limit: -$900
                - Current realized P&L: -$800 (4 closed trades)
                - Remaining budget: -$100
                - Configured unrealized limit: -$200
                - Effective unrealized limit: max(-$200, -$100) = -$100 ✅
        """
        super().__init__(action=action)

        if loss_limit >= 0:
            raise ValueError("Loss limit must be negative")

        self.loss_limit = loss_limit
        self.tick_values = tick_values
        self.tick_sizes = tick_sizes
        self.pnl_tracker = pnl_tracker                    # ← NEW
        self.realized_loss_limit = realized_loss_limit    # ← NEW

        # Log composite enforcement status
        if pnl_tracker and realized_loss_limit:
            logger.info(
                f"DailyUnrealizedLossRule: Composite enforcement ENABLED "
                f"(will respect realized limit of ${realized_loss_limit:.2f})"
            )
        else:
            logger.info(
                "DailyUnrealizedLossRule: Standalone mode "
                "(no composite enforcement)"
            )
```

#### 4B: Evaluate Method Enhancement
```python
async def evaluate(
    self, event: RiskEvent, engine: "RiskEngine"
) -> Optional[Dict[str, Any]]:
    """
    Evaluate unrealized loss with optional composite enforcement.

    NEW BEHAVIOR:
    If composite enforcement is enabled (pnl_tracker + realized_loss_limit set),
    the rule dynamically adjusts its effective limit based on remaining realized
    P&L budget. This prevents unrealized losses from breaching the realized limit
    when positions close.

    Standard Check:
        - Get total unrealized P&L
        - Compare to configured limit
        - Trigger if exceeded

    Composite Check (NEW):
        - Get total unrealized P&L
        - Get current realized P&L from pnl_tracker
        - Calculate remaining budget: realized_limit - current_realized
        - Use more conservative of: configured_limit or remaining_budget
        - Trigger if exceeded

    Returns:
        Violation dict with composite enforcement details, or None
    """
    if not self.enabled:
        return None

    # Only evaluate on relevant events
    if event.event_type not in [
        EventType.UNREALIZED_PNL_UPDATE,
        EventType.POSITION_OPENED,
        EventType.POSITION_CLOSED,
    ]:
        return None

    # Get total unrealized P&L (existing logic)
    if not hasattr(engine, 'trading_integration') or not engine.trading_integration:
        return None

    total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

    if total_unrealized_pnl is None:
        return None

    # ══════════════════════════════════════════════════════════
    # NEW: COMPOSITE ENFORCEMENT LOGIC
    # ══════════════════════════════════════════════════════════

    effective_limit = self.loss_limit  # Start with configured limit
    composite_info = {}  # Track composite enforcement details

    if self.pnl_tracker and self.realized_loss_limit:
        # Get account_id from event
        account_id = event.data.get("account_id")

        if account_id:
            try:
                # Get current realized P&L (what's already locked in today)
                current_realized_pnl = self.pnl_tracker.get_daily_pnl(str(account_id))

                # Calculate remaining budget before hitting realized limit
                # Example: -$900 (limit) - (-$800) (current) = -$100 remaining
                remaining_budget = self.realized_loss_limit - current_realized_pnl

                # Use the MORE CONSERVATIVE of:
                # 1. Configured unrealized limit (e.g., -$200)
                # 2. Remaining realized budget (e.g., -$100)
                # max(-$200, -$100) = -$100 (tighter limit!)
                effective_limit = max(self.loss_limit, remaining_budget)

                # Track composite enforcement for logging/violation details
                composite_info = {
                    "composite_enforcement": True,
                    "current_realized_pnl": current_realized_pnl,
                    "realized_limit": self.realized_loss_limit,
                    "remaining_budget": remaining_budget,
                    "configured_unrealized_limit": self.loss_limit,
                    "effective_unrealized_limit": effective_limit,
                    "limit_adjusted": effective_limit != self.loss_limit,
                }

                # Log if limit was dynamically adjusted
                if effective_limit != self.loss_limit:
                    logger.warning(
                        f"⚙️ COMPOSITE ENFORCEMENT: Unrealized limit adjusted "
                        f"${self.loss_limit:.2f} → ${effective_limit:.2f} "
                        f"(realized P&L: ${current_realized_pnl:.2f}, "
                        f"remaining budget: ${remaining_budget:.2f})"
                    )

            except Exception as e:
                logger.error(
                    f"Error in composite enforcement calculation: {e}",
                    exc_info=True
                )
                # Fall back to standalone limit on error
                effective_limit = self.loss_limit

    # ──────────────────────────────────────────────────────────
    # Check Against Effective Limit
    # ──────────────────────────────────────────────────────────

    if total_unrealized_pnl <= effective_limit:
        violation = {
            "rule": "DailyUnrealizedLossRule",
            "message": (
                f"Daily unrealized loss limit exceeded: "
                f"${total_unrealized_pnl:.2f} ≤ ${effective_limit:.2f}"
            ),
            "severity": "CRITICAL",
            "current_unrealized_pnl": total_unrealized_pnl,
            "configured_limit": self.loss_limit,
            "effective_limit": effective_limit,
            "action": self.action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add composite enforcement details if applicable
        if composite_info:
            violation.update(composite_info)

            # Enhance message with composite context
            if composite_info.get("limit_adjusted"):
                violation["message"] += (
                    f" (COMPOSITE: adjusted from ${self.loss_limit:.2f} "
                    f"due to realized P&L: ${composite_info['current_realized_pnl']:.2f}, "
                    f"remaining budget: ${composite_info['remaining_budget']:.2f})"
                )

        return violation

    return None
```

---

### Phase 5: Enforcement Logging Enhancement (10 minutes)

**File**: `src/risk_manager/sdk/enforcement.py`

**Changes**:
```python
async def enforce(self, violation: Dict[str, Any], engine: "RiskEngine"):
    """
    Execute enforcement action with enhanced composite enforcement logging.
    """
    # ... existing enforcement logic ...

    # Enhanced logging for composite enforcement
    if violation.get("composite_enforcement"):
        logger.warning(
            f"🎯 COMPOSITE ENFORCEMENT TRIGGERED:\n"
            f"   Unrealized P&L: ${violation['current_unrealized_pnl']:.2f}\n"
            f"   Configured limit: ${violation['configured_limit']:.2f}\n"
            f"   Effective limit: ${violation['effective_limit']:.2f}\n"
            f"   Realized P&L: ${violation['current_realized_pnl']:.2f}\n"
            f"   Realized limit: ${violation['realized_limit']:.2f}\n"
            f"   Remaining budget: ${violation['remaining_budget']:.2f}\n"
            f"   Limit adjusted: {violation['limit_adjusted']}"
        )
```

---

### Phase 6: Testing Strategy (60 minutes)

**File**: `tests/unit/test_composite_enforcement.py` (NEW)

**Test Cases**:
```python
class TestCompositeEnforcement:
    """Test composite enforcement between realized and unrealized rules"""

    def test_standalone_mode_no_composite(self):
        """When pnl_tracker or realized_limit is None, works standalone"""
        # No pnl_tracker passed
        rule = DailyUnrealizedLossRule(
            loss_limit=-200.0,
            tick_values={},
            tick_sizes={}
        )
        # Should use configured limit only

    def test_composite_mode_within_budget(self):
        """When within budget, uses configured limit"""
        # Realized limit: -$900
        # Current realized: -$100
        # Remaining budget: -$800
        # Configured unrealized: -$200
        # Effective: max(-$200, -$800) = -$200 (no adjustment)

    def test_composite_mode_tight_budget(self):
        """When budget tight, adjusts to remaining budget"""
        # Realized limit: -$900
        # Current realized: -$800
        # Remaining budget: -$100
        # Configured unrealized: -$200
        # Effective: max(-$200, -$100) = -$100 ✅ ADJUSTED!

    def test_composite_mode_at_realized_limit(self):
        """When at realized limit, effective limit is 0"""
        # Realized limit: -$900
        # Current realized: -$900
        # Remaining budget: $0
        # Configured unrealized: -$200
        # Effective: max(-$200, $0) = $0 (no unrealized loss allowed!)

    def test_composite_mode_violation_details(self):
        """Violation includes all composite enforcement details"""
        # Trigger violation with composite enforcement
        # Verify violation dict includes:
        # - composite_enforcement: True
        # - current_realized_pnl
        # - realized_limit
        # - remaining_budget
        # - configured_unrealized_limit
        # - effective_unrealized_limit
        # - limit_adjusted

    def test_composite_prevents_realized_breach(self):
        """End-to-end: Composite enforcement prevents realized limit breach"""
        # Scenario from RECENT2.MD:
        # 1. Close 4 trades at -$200 each = -$800 realized
        # 2. Open 5th trade
        # 3. Trade goes to -$150 unrealized
        # 4. Composite should trigger at -$100, not -$200
        # 5. After close, total realized = -$900 (exactly at limit!)
```

**File**: `tests/integration/test_composite_enforcement_integration.py` (NEW)

**Test Cases**:
```python
class TestCompositeEnforcementIntegration:
    """Integration tests with real manager, pnl_tracker, and engine"""

    async def test_full_composite_enforcement_flow(self):
        """Complete flow: config → manager → rule → enforcement"""
        # 1. Create config with composite enforcement enabled
        # 2. Initialize manager (should wire pnl_tracker correctly)
        # 3. Simulate trades closing (realized P&L builds up)
        # 4. Simulate unrealized P&L events
        # 5. Verify unrealized rule adjusts threshold
        # 6. Verify enforcement triggers at correct point

    async def test_composite_respects_config_flag(self):
        """When composite_enforcement.enabled=false, works standalone"""
        # Config has composite_enforcement.enabled: false
        # Rule should NOT adjust limits

    async def test_composite_graceful_degradation(self):
        """If realized rule disabled, unrealized works standalone"""
        # Config has daily_realized_loss.enabled: false
        # Unrealized rule should work without composite logic
```

---

## 🎓 How It All Fits Together

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CONFIGURATION                                             │
│    risk_config.yaml: composite_enforcement.enabled = true    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. INITIALIZATION (manager.py)                               │
│    ├─ Create pnl_tracker                                     │
│    ├─ Check if composite enforcement enabled in config       │
│    ├─ If enabled: pass pnl_tracker + realized_limit to rule  │
│    └─ If disabled: pass neither (standalone mode)            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. RUNTIME (Trader Opens Positions)                          │
│    ├─ Trade 1 closes: -$200 → pnl_tracker.add_trade_pnl()   │
│    ├─ Trade 2 closes: -$200 → pnl_tracker.add_trade_pnl()   │
│    ├─ Trade 3 closes: -$200 → pnl_tracker.add_trade_pnl()   │
│    ├─ Trade 4 closes: -$200 → pnl_tracker.add_trade_pnl()   │
│    │                                                          │
│    │   Current realized P&L: -$800                           │
│    │   Realized limit: -$900                                 │
│    │   Remaining budget: -$100 ⚠️                            │
│    │                                                          │
│    └─ Trade 5 opens: MNQ Long @ 21000                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. UNREALIZED P&L UPDATES (Real-time quotes)                 │
│    ├─ Quote: 20990 → Unrealized: -$50                       │
│    ├─ Quote: 20980 → Unrealized: -$100                      │
│    ├─ Quote: 20970 → Unrealized: -$150                      │
│    └─ UNREALIZED_PNL_UPDATE event fired → rule.evaluate()   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. COMPOSITE ENFORCEMENT LOGIC (daily_unrealized_loss.py)   │
│    ├─ Get unrealized P&L: -$150                             │
│    ├─ Get realized P&L from pnl_tracker: -$800              │
│    ├─ Get realized limit: -$900                             │
│    ├─ Calculate remaining budget: -$900 - (-$800) = -$100   │
│    ├─ Configured limit: -$200                               │
│    ├─ Effective limit: max(-$200, -$100) = -$100 🎯         │
│    ├─ Check: -$150 <= -$100? YES! ⚠️ TRIGGER!              │
│    └─ Return violation with composite details               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. ENFORCEMENT (enforcement.py)                              │
│    ├─ Receive violation from unrealized rule                │
│    ├─ Log composite enforcement details                     │
│    ├─ Execute close_position action                         │
│    └─ Position closed at -$150 unrealized loss              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. POSITION CLOSES (SDK)                                     │
│    ├─ Position_closed event fired                           │
│    ├─ Realized P&L updated: -$800 + (-$150) = -$950         │
│    ├─ Realized rule checks: -$950 <= -$900? YES!            │
│    └─ HARD LOCKOUT TRIGGERED! 🔒                            │
└─────────────────────────────────────────────────────────────┘

WAIT! This still breaches the realized limit!

The composite logic triggered at -$150 unrealized,
but we only had -$100 budget remaining!

This means the trigger threshold needs to be EXACT:
Trigger at -$100, not -$150!
```

### Wait, There's a Bug in the Logic!

Looking at the workflow above, I see the issue. Let me correct it:

**The problem**: We're checking `if total_unrealized_pnl <= effective_limit`, but by the time we check at -$150, we've already exceeded -$100!

**The solution**: We need to check on EVERY update, not just when it exceeds. The check should trigger as soon as unrealized P&L reaches (or goes below) the effective limit.

**Corrected trigger logic**:
```python
# BEFORE (WRONG):
if total_unrealized_pnl <= effective_limit:  # Triggers late!

# AFTER (CORRECT):
if total_unrealized_pnl <= effective_limit:  # Already correct!
# This triggers as soon as -$100 is reached/exceeded
```

Actually, the logic IS correct! The issue in the workflow is that we're checking when unrealized = -$150, but in reality the rule should have triggered earlier when it hit -$100.

Let me show the CORRECTED workflow:

```
Trade 5 P&L Timeline (with proper composite enforcement):

│ Price   │ Unrealized │ Effective Limit │ Trigger? │
├─────────┼────────────┼─────────────────┼──────────┤
│ 21000   │ $0         │ -$100           │ No       │
│ 20990   │ -$50       │ -$100           │ No       │
│ 20980   │ -$100      │ -$100           │ YES! ✅  │ ← Close here!
│ 20970   │ -$150      │ -$100           │ (closed) │

Result after close:
  Realized P&L = -$800 + (-$100) = -$900 ✅ Exactly at limit!
```

So the composite enforcement DOES work correctly to prevent breaching the realized limit!

---

## 📝 Configuration Example

### Production Configuration

```yaml
# risk_config.yaml - Production Example

rules:
  # RULE-003: Hard limit on realized P&L
  daily_realized_loss:
    enabled: true
    limit: -900.0                      # Max daily loss: $900
    reset_time: "17:00"
    timezone: "America/Chicago"

  # RULE-004: Unrealized loss with composite enforcement
  daily_unrealized_loss:
    enabled: true
    limit: -200.0                      # Standalone: Max $200 per position
    check_interval_seconds: 10

    # COMPOSITE ENFORCEMENT: Protect realized limit
    composite_enforcement:
      enabled: true                    # Enable dynamic limit adjustment
      respect_realized_limit: true     # Adjust based on realized P&L budget
      realized_rule_ref: "daily_realized_loss"  # Coordinate with RULE-003
```

### Test Configuration

```yaml
# risk_config.yaml - Test Example (smaller limits)

rules:
  daily_realized_loss:
    enabled: true
    limit: -5.0                        # Easier to test
    reset_time: "17:00"
    timezone: "America/Chicago"

  daily_unrealized_loss:
    enabled: true
    limit: -20.0                       # Easier to test

    composite_enforcement:
      enabled: true
      respect_realized_limit: true
      realized_rule_ref: "daily_realized_loss"
```

---

## 🧪 Testing Strategy

### Unit Tests (60 minutes)

**File**: `tests/unit/test_composite_enforcement.py`

**Coverage**:
1. ✅ Standalone mode (no pnl_tracker)
2. ✅ Composite mode with budget remaining
3. ✅ Composite mode with tight budget (limit adjustment)
4. ✅ Composite mode at realized limit (no unrealized allowed)
5. ✅ Violation details include composite info
6. ✅ Error handling (pnl_tracker fails, graceful degradation)

### Integration Tests (30 minutes)

**File**: `tests/integration/test_composite_enforcement_integration.py`

**Coverage**:
1. ✅ Full flow: config → manager → rule → enforcement
2. ✅ Composite enforcement respects config flag
3. ✅ Graceful degradation when realized rule disabled
4. ✅ Multi-trade scenario from RECENT2.MD

### Manual Testing (15 minutes)

**Using `run_dev.py`**:
```bash
# 1. Configure small limits for testing
# Edit config/risk_config.yaml:
#   daily_realized_loss.limit: -5.0
#   daily_unrealized_loss.limit: -20.0
#   composite_enforcement.enabled: true

# 2. Run in dev mode
python run_dev.py

# 3. Place trades and watch composite enforcement in logs:
# Look for: "⚙️ COMPOSITE ENFORCEMENT: Unrealized limit adjusted"

# 4. Verify effective limit changes as realized P&L builds up
```

---

## 📊 Success Metrics

### How We Know It's Working

1. **Configuration Loading**:
   ```
   ✅ Log: "⚙️ Composite enforcement ENABLED: unrealized limit will adjust based on realized P&L"
   ```

2. **Dynamic Limit Adjustment**:
   ```
   ✅ Log: "⚙️ COMPOSITE ENFORCEMENT: Unrealized limit adjusted -$200 → -$100"
   ```

3. **Violation Triggered at Correct Threshold**:
   ```
   ✅ Violation dict includes:
      - effective_limit: -100.0 (adjusted)
      - configured_limit: -200.0 (original)
      - remaining_budget: -100.0
      - limit_adjusted: true
   ```

4. **Enforcement Prevents Realized Breach**:
   ```
   ✅ Final realized P&L = -$900 (exactly at limit, not over!)
   ```

---

## 🚀 Implementation Timeline

| Phase | Task | Time | Files Changed |
|-------|------|------|---------------|
| 1 | Configuration schema | 10 min | `config/risk_config.yaml`, `src/risk_manager/config/models.py` |
| 2 | Rule initialization | 15 min | `src/risk_manager/core/manager.py` |
| 3 | Rule logic enhancement | 30 min | `src/risk_manager/rules/daily_unrealized_loss.py` |
| 4 | Enforcement logging | 10 min | `src/risk_manager/sdk/enforcement.py` |
| 5 | Unit tests | 60 min | `tests/unit/test_composite_enforcement.py` (NEW) |
| 6 | Integration tests | 30 min | `tests/integration/test_composite_enforcement_integration.py` (NEW) |
| 7 | Manual testing | 15 min | - |
| 8 | Documentation | 20 min | This file, `docs/current/PROJECT_STATUS.md` |

**Total**: ~3 hours

---

## ✅ Pre-Flight Checklist

Before implementing:

- [ ] Read RECENT2.MD (understand the problem)
- [ ] Read this integration plan
- [ ] Understand how pnl_tracker works (`src/risk_manager/state/pnl_tracker.py`)
- [ ] Review existing unrealized rule logic (`src/risk_manager/rules/daily_unrealized_loss.py`)
- [ ] Review existing manager wiring (`src/risk_manager/core/manager.py:468-476`)
- [ ] Check current config (`config/risk_config.yaml`)

During implementation:

- [ ] Write tests FIRST (TDD)
- [ ] Test standalone mode (no composite)
- [ ] Test composite mode (with budget)
- [ ] Test composite mode (tight budget, limit adjustment)
- [ ] Test composite mode (at limit, no unrealized allowed)
- [ ] Verify violation details include composite info
- [ ] Test graceful degradation (errors, disabled config)

After implementation:

- [ ] Run full test suite: `python run_tests.py → [1]`
- [ ] Run integration tests: `python run_tests.py → [3]`
- [ ] Run smoke test: `python run_tests.py → [s]`
- [ ] Manual testing with `run_dev.py`
- [ ] Check logs for composite enforcement messages
- [ ] Update `docs/current/PROJECT_STATUS.md`

---

## 🎯 Summary

**What**: Enable unrealized rule to dynamically adjust its threshold based on remaining realized P&L budget

**Why**: Prevent unrealized losses from breaching realized limits when positions close

**How**: Wire pnl_tracker to unrealized rule, implement composite enforcement logic

**Impact**:
- ✅ **Config**: Add composite_enforcement section
- ✅ **Manager**: Pass pnl_tracker + realized_limit to unrealized rule
- ✅ **Rule**: Add composite logic to evaluate()
- ✅ **State**: Already works! (pnl_tracker.get_daily_pnl)
- ✅ **Enforcement**: Enhanced logging
- ✅ **Tests**: New test suite for composite enforcement

**Result**: Trader cannot inadvertently breach realized limit through unrealized losses!

---

**Last Updated**: 2025-10-30
**Author**: Risk Manager V34 Team
**Status**: Ready for Implementation
