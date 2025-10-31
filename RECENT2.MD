 The Composite Enforcement Problem

  ★ Insight ─────────────────────────────────────

  Your Scenario Breaks Current Architecture

  Current system treats rules as independent silos:
  - REALIZED rule (RULE-003): "I only care about closed trades"
  - UNREALIZED rule (RULE-004): "I only care about open positions"
  - They don't talk to each other!

  Real-World Problem:
  - 4 trades closed: -$200 each = -$800 realized ✅
  - 5th trade open: -$200 unrealized ✅ (within limit)
  - BUT: If 5th trade closes, total realized = -$1000 ❌ (exceeds -$900 limit!)

  The UNREALIZED rule should have closed the 5th trade at -$100, not -$200, because that's all the "budget" remaining before hitting the REALIZED limit.

  This is called "Projected P&L Enforcement" - unrealized rules must consider realized state.

  ─────────────────────────────────────────────────

  ---
  📊 Current Implementation Analysis

  Let me trace through what actually happens today:

  RULE-003 (Daily Realized Loss)

  # daily_realized_loss.py:175-189
  daily_pnl = self.pnl_tracker.add_trade_pnl(str(account_id), profit_and_loss)

  if daily_pnl <= self.limit:  # e.g., -$600 <= -$500
      return violation  # Trigger enforcement

  What it tracks: Only CLOSED tradesWhen it triggers: After a position closes and pushes realized P&L over limitProblem: By this time, it's too late! The loss already happened!

  ---
  RULE-004 (Daily Unrealized Loss)

  # daily_unrealized_loss.py:124-143
  total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

  if total_unrealized_pnl <= self.loss_limit:  # e.g., -$800 <= -$750
      return violation  # Flatten all positions

  What it tracks: Only OPEN positions (floating P&L)What it DOESN'T know: How much realized P&L already consumedProblem: It lets trades get too deep before closing them!

  ---
  🔧 The Solution: Projected P&L Enforcement

  The UNREALIZED rule needs to become context-aware:

  # PROPOSED: daily_unrealized_loss.py

  async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> Optional[Dict[str, Any]]:
      """
      Evaluate unrealized loss with REALIZED budget awareness.
      
      NEW LOGIC:
      1. Get current REALIZED P&L from pnl_tracker
      2. Get REALIZED limit from daily_realized_loss_rule config
      3. Calculate remaining budget: realized_limit - current_realized_pnl
      4. Adjust unrealized threshold to protect realized limit
      5. Close positions BEFORE they breach the combined limit
      """

      if not self.enabled:
          return None

      # ... existing event type checks ...

      # ══════════════════════════════════════════════════════════
      # NEW: Composite Enforcement Logic
      # ══════════════════════════════════════════════════════════

      # Get current unrealized P&L
      total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

      # Get current REALIZED P&L (what's already locked in)
      current_realized_pnl = engine.pnl_tracker.get_daily_pnl(account_id)

      # Get REALIZED limit from RULE-003 config
      # This requires access to other rules' configs!
      realized_limit = self._get_realized_limit(engine)  # e.g., -$900

      # Calculate remaining budget before hitting realized limit
      remaining_budget = realized_limit - current_realized_pnl
      # Example: -$900 - (-$800) = -$100 remaining

      # ──────────────────────────────────────────────────────────
      # Dynamic Threshold Adjustment
      # ──────────────────────────────────────────────────────────

      # Use the SMALLER of:
      # 1. Configured unrealized limit (e.g., -$200 per trade)
      # 2. Remaining realized budget (e.g., -$100 remaining)
      effective_limit = max(self.loss_limit, remaining_budget)

      # Example:
      # - Configured unrealized limit: -$200
      # - Remaining budget: -$100
      # - Effective limit: max(-$200, -$100) = -$100  ← Use this!

      # ──────────────────────────────────────────────────────────
      # Check Against Effective Limit
      # ──────────────────────────────────────────────────────────

      if total_unrealized_pnl <= effective_limit:
          return {
              "rule": "DailyUnrealizedLossRule",
              "message": (
                  f"Unrealized loss exceeds effective limit: "
                  f"${total_unrealized_pnl:.2f} ≤ ${effective_limit:.2f} "
                  f"(realized: ${current_realized_pnl:.2f}, "
                  f"remaining budget: ${remaining_budget:.2f})"
              ),
              "current_unrealized_pnl": total_unrealized_pnl,
              "current_realized_pnl": current_realized_pnl,
              "remaining_budget": remaining_budget,
              "configured_limit": self.loss_limit,
              "effective_limit": effective_limit,  # ← The key insight!
              "action": self.action,
          }

      return None

  ---
  📐 How It Works: Your Scenario

  Let's trace through your exact scenario with the new logic:

  Initial State

  - REALIZED limit: -$900
  - UNREALIZED limit: -$200
  - Current realized P&L: $0
  - Remaining budget: -$900

  ---
  Trade 1

  - Unrealized P&L: -$200
  - Effective limit: max(-$200, -$900) = -$200
  - Trigger? -$200 <= -$200 → YES ✅ Close trade
  - Realized P&L after close: -$200
  - Remaining budget: -$900 - (-$200) = -$700

  ---
  Trade 2

  - Unrealized P&L: -$200
  - Effective limit: max(-$200, -$700) = -$200
  - Trigger? -$200 <= -$200 → YES ✅ Close trade
  - Realized P&L after close: -$400
  - Remaining budget: -$900 - (-$400) = -$500

  ---
  Trade 3

  - Unrealized P&L: -$200
  - Effective limit: max(-$200, -$500) = -$200
  - Trigger? -$200 <= -$200 → YES ✅ Close trade
  - Realized P&L after close: -$600
  - Remaining budget: -$900 - (-$600) = -$300

  ---
  Trade 4

  - Unrealized P&L: -$200
  - Effective limit: max(-$200, -$300) = -$200
  - Trigger? -$200 <= -$200 → YES ✅ Close trade
  - Realized P&L after close: -$800
  - Remaining budget: -$900 - (-$800) = -$100 ⚠️

  ---
  Trade 5 (The Critical One!)

  - Unrealized P&L: -$150
  - Effective limit: max(-$200, -$100) = -$100 🎯
  - Trigger? -$150 <= -$100 → YES ❌ Close trade at -$150!
  - Realized P&L after close: -$950
  - REALIZED RULE TRIGGERS: -$950 <= -$900 → Hard lockout! 🔒

  Wait, that still breaches! Let me recalculate...

  Actually, the rule should trigger earlier:

  Trade 5 (Corrected Logic)

  - Unrealized P&L starts at: $0
  - Effective limit: max(-$200, -$100) = -$100
  - As trade moves:
    - @ -$50: Still OK ✅
    - @ -$100: TRIGGER! ⚠️ Close immediately!

  - Realized P&L after close: -$900 (exactly at limit)

  ---
  🏗️ Architecture Changes Needed

  1. Rule Context Sharing (New Capability)

  Rules need access to other rules' state and limits:

  # src/risk_manager/core/engine.py

  class RiskEngine:
      def __init__(self, ...):
          self.rules = []
          self.rule_configs = {}  # NEW: Store configs for cross-rule access

      def add_rule(self, rule_name: str, rule: RiskRule, config: dict):
          """Register rule with its configuration."""
          self.rules.append(rule)
          self.rule_configs[rule_name] = config  # Store for other rules

      def get_rule_limit(self, rule_name: str) -> float:
          """Allow rules to query other rules' limits."""
          return self.rule_configs.get(rule_name, {}).get("limit")

  ---
  2. Enhanced Unrealized Rule (Projected P&L)

  # src/risk_manager/rules/daily_unrealized_loss.py

  class DailyUnrealizedLossRule(RiskRule):
      def __init__(
          self,
          loss_limit: float,
          pnl_tracker: "PnLTracker",  # NEW: Need pnl_tracker access
          realized_loss_limit: float | None = None,  # NEW: Optional override
          # ... existing params ...
      ):
          self.loss_limit = loss_limit
          self.pnl_tracker = pnl_tracker
          self.realized_loss_limit = realized_loss_limit

      async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> Optional[Dict]:
          # Get current unrealized P&L
          total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

          # Get current realized P&L (NEW!)
          account_id = event.data.get("account_id")
          current_realized_pnl = self.pnl_tracker.get_daily_pnl(account_id)

          # Get realized limit (from config or engine)
          realized_limit = self.realized_loss_limit or engine.get_rule_limit("DailyRealizedLossRule")

          # Calculate effective limit (composite enforcement!)
          if realized_limit:
              remaining_budget = realized_limit - current_realized_pnl
              effective_limit = max(self.loss_limit, remaining_budget)
          else:
              effective_limit = self.loss_limit  # Fallback to standalone


 ▐▛███▜▌   Claude Code v2.0.29
▝▜█████▛▘  Sonnet 4.5 · Claude Max
  ▘▘ ▝▝    C:\Users\jakers\Desktop\risk-manager-v34

> C:\Users\jakers\Desktop\risk-manager-v34\recent.md - READ MY LAST CONVOWITH THIS AI, THYE GLITCH OUT YOU NEED TO PICK UP WHERE WE LEFT OFF. MY QUESTION WAS ABOUT THE UNRELISSED/REALISED RULE/ENFOCRMENT LOGIC COMBINED.... ALSO READ THE       
REST OF THE CONVO FOR CONTEXT 

● I'll read your recent conversation to understand the context and pick up where you left off.

● Read(recent.md)
  ⎿  Read 627 lines

● I can see exactly where you left off! You discovered a critical composite enforcement gap between UNREALIZED and REALIZED P&L rules. Let me break down this sophisticated problem:

● Read(src\risk_manager\rules\daily_realized_loss.py)
  ⎿  Read 313 lines

● Read(src\risk_manager\rules\daily_unrealized_loss.py)
  ⎿  Read 145 lines

● Read(src\risk_manager\state\pnl_tracker.py)
  ⎿  Read 278 lines

● Now let me check how these rules work together currently:

● Search(pattern: "get_daily_pnl|get_total_unrealized", path: "src\risk_manager", output_mode: "content")
  ⎿  Found 4 lines (ctrl+o to expand)

● Perfect! I can now see the critical architectural gap you've identified. This is a sophisticated composite enforcement problem that the current system doesn't handle!

  ---
  🚨 The Composite Enforcement Problem

  ★ Insight ─────────────────────────────────────

  Your Scenario Breaks Current Architecture

  Current system treats rules as independent silos:
  - REALIZED rule (RULE-003): "I only care about closed trades"
  - UNREALIZED rule (RULE-004): "I only care about open positions"
  - They don't talk to each other!

  Real-World Problem:
  - 4 trades closed: -$200 each = -$800 realized ✅
  - 5th trade open: -$200 unrealized ✅ (within limit)
  - BUT: If 5th trade closes, total realized = -$1000 ❌ (exceeds -$900 limit!)

  The UNREALIZED rule should have closed the 5th trade at -$100, not -$200, because that's all the "budget" remaining before hitting the REALIZED limit.

  This is called "Projected P&L Enforcement" - unrealized rules must consider realized state.

  ─────────────────────────────────────────────────

  ---
  📊 Current Implementation Analysis

  Let me trace through what actually happens today:

  RULE-003 (Daily Realized Loss)

  # daily_realized_loss.py:175-189
  daily_pnl = self.pnl_tracker.add_trade_pnl(str(account_id), profit_and_loss)

  if daily_pnl <= self.limit:  # e.g., -$600 <= -$500
      return violation  # Trigger enforcement

  What it tracks: Only CLOSED tradesWhen it triggers: After a position closes and pushes realized P&L over limitProblem: By this time, it's too late! The loss already happened!

  ---
  RULE-004 (Daily Unrealized Loss)

  # daily_unrealized_loss.py:124-143
  total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

  if total_unrealized_pnl <= self.loss_limit:  # e.g., -$800 <= -$750
      return violation  # Flatten all positions

  What it tracks: Only OPEN positions (floating P&L)What it DOESN'T know: How much realized P&L already consumedProblem: It lets trades get too deep before closing them!

  ---
  🔧 The Solution: Projected P&L Enforcement

  The UNREALIZED rule needs to become context-aware:

  # PROPOSED: daily_unrealized_loss.py

  async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> Optional[Dict[str, Any]]:
      """
      Evaluate unrealized loss with REALIZED budget awareness.
      
      NEW LOGIC:
      1. Get current REALIZED P&L from pnl_tracker
      2. Get REALIZED limit from daily_realized_loss_rule config
      3. Calculate remaining budget: realized_limit - current_realized_pnl
      4. Adjust unrealized threshold to protect realized limit
      5. Close positions BEFORE they breach the combined limit
      """

      if not self.enabled:
          return None

      # ... existing event type checks ...

      # ══════════════════════════════════════════════════════════
      # NEW: Composite Enforcement Logic
      # ══════════════════════════════════════════════════════════

      # Get current unrealized P&L
      total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

      # Get current REALIZED P&L (what's already locked in)
      current_realized_pnl = engine.pnl_tracker.get_daily_pnl(account_id)

      # Get REALIZED limit from RULE-003 config
      # This requires access to other rules' configs!
      realized_limit = self._get_realized_limit(engine)  # e.g., -$900

      # Calculate remaining budget before hitting realized limit
      remaining_budget = realized_limit - current_realized_pnl
      # Example: -$900 - (-$800) = -$100 remaining

      # ──────────────────────────────────────────────────────────
      # Dynamic Threshold Adjustment
      # ──────────────────────────────────────────────────────────

      # Use the SMALLER of:
      # 1. Configured unrealized limit (e.g., -$200 per trade)
      # 2. Remaining realized budget (e.g., -$100 remaining)
      effective_limit = max(self.loss_limit, remaining_budget)

      # Example:
      # - Configured unrealized limit: -$200
      # - Remaining budget: -$100
      # - Effective limit: max(-$200, -$100) = -$100  ← Use this!

      # ──────────────────────────────────────────────────────────
      # Check Against Effective Limit
      # ──────────────────────────────────────────────────────────

      if total_unrealized_pnl <= effective_limit:
          return {
              "rule": "DailyUnrealizedLossRule",
              "message": (
                  f"Unrealized loss exceeds effective limit: "
                  f"${total_unrealized_pnl:.2f} ≤ ${effective_limit:.2f} "
                  f"(realized: ${current_realized_pnl:.2f}, "
                  f"remaining budget: ${remaining_budget:.2f})"
              ),
              "current_unrealized_pnl": total_unrealized_pnl,
              "current_realized_pnl": current_realized_pnl,
              "remaining_budget": remaining_budget,
              "configured_limit": self.loss_limit,
              "effective_limit": effective_limit,  # ← The key insight!
              "action": self.action,
          }

      return None

  ---
  📐 How It Works: Your Scenario

  Let's trace through your exact scenario with the new logic:

  Initial State

  - REALIZED limit: -$900
  - UNREALIZED limit: -$200
  - Current realized P&L: $0
  - Remaining budget: -$900

  ---
  Trade 1

  - Unrealized P&L: -$200
  - Effective limit: max(-$200, -$900) = -$200
  - Trigger? -$200 <= -$200 → YES ✅ Close trade
  - Realized P&L after close: -$200
  - Remaining budget: -$900 - (-$200) = -$700

  ---
  Trade 2

  - Unrealized P&L: -$200
  - Effective limit: max(-$200, -$700) = -$200
  - Trigger? -$200 <= -$200 → YES ✅ Close trade
  - Realized P&L after close: -$400
  - Remaining budget: -$900 - (-$400) = -$500

  ---
  Trade 3

  - Unrealized P&L: -$200
  - Effective limit: max(-$200, -$500) = -$200
  - Trigger? -$200 <= -$200 → YES ✅ Close trade
  - Realized P&L after close: -$600
  - Remaining budget: -$900 - (-$600) = -$300

  ---
  Trade 4

  - Unrealized P&L: -$200
  - Effective limit: max(-$200, -$300) = -$200
  - Trigger? -$200 <= -$200 → YES ✅ Close trade
  - Realized P&L after close: -$800
  - Remaining budget: -$900 - (-$800) = -$100 ⚠️

  ---
  Trade 5 (The Critical One!)

  - Unrealized P&L: -$150
  - Effective limit: max(-$200, -$100) = -$100 🎯
  - Trigger? -$150 <= -$100 → YES ❌ Close trade at -$150!
  - Realized P&L after close: -$950
  - REALIZED RULE TRIGGERS: -$950 <= -$900 → Hard lockout! 🔒

  Wait, that still breaches! Let me recalculate...

  Actually, the rule should trigger earlier:

  Trade 5 (Corrected Logic)

  - Unrealized P&L starts at: $0
  - Effective limit: max(-$200, -$100) = -$100
  - As trade moves:
    - @ -$50: Still OK ✅
    - @ -$100: TRIGGER! ⚠️ Close immediately!

  - Realized P&L after close: -$900 (exactly at limit)

  ---
  🏗️ Architecture Changes Needed

  1. Rule Context Sharing (New Capability)

  Rules need access to other rules' state and limits:

  # src/risk_manager/core/engine.py

  class RiskEngine:
      def __init__(self, ...):
          self.rules = []
          self.rule_configs = {}  # NEW: Store configs for cross-rule access

      def add_rule(self, rule_name: str, rule: RiskRule, config: dict):
          """Register rule with its configuration."""
          self.rules.append(rule)
          self.rule_configs[rule_name] = config  # Store for other rules

      def get_rule_limit(self, rule_name: str) -> float:
          """Allow rules to query other rules' limits."""
          return self.rule_configs.get(rule_name, {}).get("limit")

  ---
  2. Enhanced Unrealized Rule (Projected P&L)

  # src/risk_manager/rules/daily_unrealized_loss.py

  class DailyUnrealizedLossRule(RiskRule):
      def __init__(
          self,
          loss_limit: float,
          pnl_tracker: "PnLTracker",  # NEW: Need pnl_tracker access
          realized_loss_limit: float | None = None,  # NEW: Optional override
          # ... existing params ...
      ):
          self.loss_limit = loss_limit
          self.pnl_tracker = pnl_tracker
          self.realized_loss_limit = realized_loss_limit

      async def evaluate(self, event: RiskEvent, engine: "RiskEngine") -> Optional[Dict]:
          # Get current unrealized P&L
          total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

          # Get current realized P&L (NEW!)
          account_id = event.data.get("account_id")
          current_realized_pnl = self.pnl_tracker.get_daily_pnl(account_id)

          # Get realized limit (from config or engine)
          realized_limit = self.realized_loss_limit or engine.get_rule_limit("DailyRealizedLossRule")

          # Calculate effective limit (composite enforcement!)
          if realized_limit:
              remaining_budget = realized_limit - current_realized_pnl
              effective_limit = max(self.loss_limit, remaining_budget)
          else:
              effective_limit = self.loss_limit  # Fallback to standalone

          # Check against effective limit
          if total_unrealized_pnl <= effective_limit:
              # Trigger violation with full context
              return {...}

  ---
  3. Configuration Updates

  # config/risk_config.yaml

  rules:
    daily_realized_loss:  # RULE-003
      enabled: true
      limit: -900.0  # Hard limit for realized P&L
      reset_time: "17:00"

    daily_unrealized_loss:  # RULE-004
      enabled: true
      loss_limit: -200.0  # Standalone unrealized limit
      composite_enforcement: true  # NEW: Enable projected P&L
      respect_realized_limit: true  # NEW: Adjust based on RULE-003
      realized_rule_ref: "daily_realized_loss"  # NEW: Which rule to check

  ---
  📊 Does Current Architecture Support This?

  Let me check the actual wiring:

● Read(src\risk_manager\core\engine.py)
  ⎿  Read 100 lines

● Search(pattern: "add_rule|initialize.*rule|rules\[", path: "src\risk_manager\core", output_mode: "content")
  ⎿  Found 15 lines (ctrl+o to expand)

● Read(src\risk_manager\core\manager.py)
  ⎿  Read 604 lines

● Perfect! Now I can see the exact architectural gap. Let me show you what needs to change:

  ---
  🎯 The Problem: Rules Are Isolated Silos

  ★ Insight ─────────────────────────────────────

  Current Architecture (manager.py:450-476):

  # Line 252: Shared state managers created
  pnl_tracker = PnLTracker(db=db)  # ← Tracks realized P&L

  # Line 287-293: REALIZED rule gets pnl_tracker ✅
  rule = DailyRealizedLossRule(
      limit=-900.0,
      pnl_tracker=pnl_tracker,  # ← Can track realized P&L
      lockout_manager=lockout_manager,
  )

  # Line 468-476: UNREALIZED rule does NOT get pnl_tracker ❌
  rule = DailyUnrealizedLossRule(
      loss_limit=-200.0,
      tick_values=tick_values,
      tick_sizes=tick_sizes,
      # ❌ NO pnl_tracker passed!
      # ❌ NO way to see realized P&L!
      # ❌ NO way to calculate remaining budget!
  )

  The Rules Can't Talk:
  - REALIZED rule: "I track closed trades"
  - UNREALIZED rule: "I track open trades"
  - NO COMMUNICATION CHANNEL!

  The architecture treats them as independent, but your use case requires them to be interdependent.

  ─────────────────────────────────────────────────

  ---
  🔧 Solution: Enable Composite Enforcement

  Step 1: Wire pnl_tracker to UNREALIZED Rule

  # src/risk_manager/core/manager.py:468-476 (MODIFIED)

  # RULE-004: Daily Unrealized Loss (WITH COMPOSITE ENFORCEMENT)
  if self.config.rules.daily_unrealized_loss.enabled:
      from risk_manager.integrations.trading import TICK_VALUES, ALIASES

      # Build tick dicts...
      tick_values = {...}
      tick_sizes = {...}

      # ══════════════════════════════════════════════════════════
      # NEW: Enable composite enforcement
      # ══════════════════════════════════════════════════════════

      # Get realized loss limit from config
      realized_loss_limit = (
          self.config.rules.daily_realized_loss.limit
          if self.config.rules.daily_realized_loss.enabled
          else None
      )

      rule = DailyUnrealizedLossRule(
          loss_limit=self.config.rules.daily_unrealized_loss.limit,
          tick_values=tick_values,
          tick_sizes=tick_sizes,
          pnl_tracker=pnl_tracker,  # ← NEW: Give it access to realized P&L!
          realized_loss_limit=realized_loss_limit,  # ← NEW: Know the realized limit!
          action="close_position",
      )
      self.add_rule(rule)
      rules_loaded += 1
      logger.info(f"✅ Loaded: DailyUnrealizedLossRule (limit=${rule.loss_limit}, composite={realized_loss_limit is not None})")

  ---
  Step 2: Update UNREALIZED Rule Constructor

  # src/risk_manager/rules/daily_unrealized_loss.py

  class DailyUnrealizedLossRule(RiskRule):
      def __init__(
          self,
          loss_limit: float,
          tick_values: Dict[str, float],
          tick_sizes: Dict[str, float],
          pnl_tracker: "PnLTracker" | None = None,  # ← NEW (optional for tests)
          realized_loss_limit: float | None = None,  # ← NEW (optional for tests)
          action: str = "close_position",
      ):
          super().__init__(action=action)

          if loss_limit >= 0:
              raise ValueError("Loss limit must be negative")

          self.loss_limit = loss_limit
          self.tick_values = tick_values
          self.tick_sizes = tick_sizes
          self.pnl_tracker = pnl_tracker  # ← NEW
          self.realized_loss_limit = realized_loss_limit  # ← NEW

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

  ---
  Step 3: Implement Composite Logic in evaluate()

  # src/risk_manager/rules/daily_unrealized_loss.py:91-144 (ENHANCED)

  async def evaluate(
      self, event: RiskEvent, engine: "RiskEngine"
  ) -> Optional[Dict[str, Any]]:
      """
      Evaluate unrealized loss with composite enforcement.
      
      NEW: If pnl_tracker and realized_loss_limit are configured,
      adjusts the effective unrealized limit to protect the realized limit.
      
      Example:
          - Realized limit: -$900
          - Current realized P&L: -$800 (4 trades closed)
          - Remaining budget: -$100
          - Configured unrealized limit: -$200
          - Effective unrealized limit: max(-$200, -$100) = -$100 ← USE THIS!
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

      # Get total unrealized P&L
      if not hasattr(engine, 'trading_integration') or not engine.trading_integration:
          return None

      total_unrealized_pnl = engine.trading_integration.get_total_unrealized_pnl()

      if total_unrealized_pnl is None:
          return None

      # ══════════════════════════════════════════════════════════
      # COMPOSITE ENFORCEMENT: Adjust limit based on realized P&L
      # ══════════════════════════════════════════════════════════

      effective_limit = self.loss_limit  # Start with configured limit
      composite_info = {}  # Track composite enforcement details

      if self.pnl_tracker and self.realized_loss_limit:
          # Get account_id from event
          account_id = event.data.get("account_id")

          if account_id:
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

              # Track composite enforcement for logging
              composite_info = {
                  "composite_enforcement": True,
                  "current_realized_pnl": current_realized_pnl,
                  "realized_limit": self.realized_loss_limit,
                  "remaining_budget": remaining_budget,
                  "configured_unrealized_limit": self.loss_limit,
                  "effective_unrealized_limit": effective_limit,
              }

              # Log if limit was adjusted
              if effective_limit != self.loss_limit:
                  logger.warning(
                      f"⚙️ COMPOSITE ENFORCEMENT: Unrealized limit adjusted "
                      f"${self.loss_limit:.2f} → ${effective_limit:.2f} "
                      f"(realized P&L: ${current_realized_pnl:.2f}, "
                      f"remaining budget: ${remaining_budget:.2f})"
                  )

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
              violation["message"] += (
                  f" (composite enforcement: realized ${composite_info['current_realized_pnl']:.2f}, "
                  f"remaining budget ${composite_info['remaining_budget']:.2f})"
              )

          return violation

      return None

  ---
  📊 How It Works: Your Scenario (Revisited)

  With composite enforcement enabled:

  Initial State

  Realized limit: -$900
  Unrealized limit: -$200
  Current realized P&L: $0
  Remaining budget: -$900
  Effective unrealized limit: max(-$200, -$900) = -$200

  ---
  After 4 Trades Close (Each -$200 Loss)

  Current realized P&L: -$800
  Remaining budget: -$900 - (-$800) = -$100 ⚠️
  Effective unrealized limit: max(-$200, -$100) = -$100 🎯

  Log Output:
  ⚙️ COMPOSITE ENFORCEMENT: Unrealized limit adjusted -$200 → -$100
     (realized P&L: -$800, remaining budget: -$100)

  ---
  Trade 5 Opens

  Unrealized P&L: $0 → -$50 → -$100
  At -$100: TRIGGER! ⚠️

  Violation Details:
  {
    "rule": "DailyUnrealizedLossRule",
    "message": "Daily unrealized loss limit exceeded: -$100.00 ≤ -$100.00 (composite enforcement: realized -$800.00, remaining budget -$100.00)",
    "current_unrealized_pnl": -100.0,
    "configured_limit": -200.0,
    "effective_limit": -100.0,  ← Adjusted dynamically!
    "composite_enforcement": true,
    "current_realized_pnl": -800.0,
    "remaining_budget": -100.0,
    "action": "close_position"
  }

  Result: Position closed at -$100, total realized P&L: -$900 (exactly at limit!) ✅

  ---
  📋 Summary: What Changes

  | Component                           | Current State            | After Changes                                    |
  |-------------------------------------|--------------------------|--------------------------------------------------|
  | manager.py:468                      | ❌ No pnl_tracker passed  | ✅ Pass pnl_tracker + realized_loss_limit         |
  | daily_unrealized_loss.py:init       | ❌ No composite params    | ✅ Accept pnl_tracker, realized_loss_limit        |
  | daily_unrealized_loss.py:evaluate() | ❌ Standalone limit check | ✅ Dynamic limit adjustment based on realized P&L |
  | Configuration                       | Independent rules        | Interdependent composite enforcement             |
  | Logging                             | Basic violation          | Detailed composite context                       |

  ---
  🚀 Should I Implement This Now?

  This is a 2-3 hour implementation that includes:

  1. ✅ Wire pnl_tracker to UNREALIZED rule (15 min)
  2. ✅ Update rule constructor (15 min)
  3. ✅ Implement composite logic (1 hour)
  4. ✅ Add tests for composite enforcement (1 hour)
  5. ✅ Update documentation (30 min)

  Would you like me to:
  - Implement the full composite enforcement system?
  - Start with just the wiring and basic logic?
  - Create a detailed implementation plan first?

  This is a critical production feature - without it, traders can inadvertently breach realized limits through unrealized losses!

