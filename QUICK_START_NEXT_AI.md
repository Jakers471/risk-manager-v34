# QUICK START FOR NEXT AI

**TL;DR**: You're implementing unrealized P&L rules for a live trading risk manager. Read the files below, then start coding.

---

## 📖 Read These Files IN ORDER (30 minutes)

1. **THIS FILE** ← You are here (5 min)
2. **`AI_HANDOFF_UNREALIZED_PNL_RULES.md`** ← Main handoff document (15 min)
3. **`AGENT_SWARM_COMPLETION_2025-10-30.md`** ← What was just built (10 min)

---

## 🎯 Your Mission

**Implement unrealized P&L calculation for 2 risk rules:**
- RULE-004: Daily Unrealized Loss (flatten if floating loss ≤ -$750)
- RULE-005: Max Unrealized Profit (close if floating profit ≥ +$500)

**Challenge**: Need real-time quote data to calculate floating P&L without spamming logs.

---

## 🚀 Quick Start (First 5 Minutes)

### Step 1: See Current State
```bash
cd C:\Users\jakers\Desktop\risk-manager-v34
python run_dev.py
```

**What you'll see**:
- 4/9 rules loading ← Goal: 9/9
- Live events flowing (ORDER_FILLED, POSITION_OPENED)
- Rule evaluations (✅ PASS or ❌ FAIL)

**Press Ctrl+C to stop**

### Step 2: Check What Exists
```bash
# Rule specifications (the plan)
ls docs/specifications/unified/rules/

# Rule implementations (the code)
ls src/risk_manager/rules/

# Key file: Already written, needs quote integration
cat src/risk_manager/rules/daily_unrealized_loss.py
```

### Step 3: Start Implementation

**Create this file first**:
`src/risk_manager/integrations/unrealized_pnl.py`

**Copy the `UnrealizedPnLCalculator` class from the handoff document** (it's in Step 2).

**Then modify**:
`src/risk_manager/integrations/trading.py`

**Add quote subscription** (code in handoff document, Step 1).

---

## 🔥 Critical Success Factors

### ✅ DO:
1. **Read the handoff document completely** before coding
2. **Test with `run_dev.py`** after every change
3. **Start with `action: alert`** in config (don't close positions while testing!)
4. **Process quotes silently** (no logs per tick)
5. **Log rule evaluations** at INFO level (when they trigger)

### ❌ DON'T:
1. **Don't log every quote update** (will spam thousands of lines)
2. **Don't start with enforcement** (use alerts first!)
3. **Don't guess** - if specs are unclear, ask user or check existing code
4. **Don't break existing rules** - they're already working
5. **Don't overthink** - the foundation is solid, just add P&L calculation

---

## 📊 Expected Timeline

| Task | Time | Cumulative |
|------|------|------------|
| Read handoff docs | 30 min | 30 min |
| Implement UnrealizedPnLCalculator | 1 hour | 1.5 hours |
| Add quote subscription | 1 hour | 2.5 hours |
| Update RULE-004 (daily unrealized loss) | 1 hour | 3.5 hours |
| Test RULE-004 with run_dev.py | 30 min | 4 hours |
| Update RULE-005 (max unrealized profit) | 1 hour | 5 hours |
| Test RULE-005 with run_dev.py | 30 min | 5.5 hours |
| **TOTAL for unrealized P&L rules** | **5.5 hours** | ✅ |

After unrealized P&L rules work:
- Create timers_config.yaml (30 min)
- Add rule instantiation code (30 min)
- Test remaining rules (2-3 hours)
- **TOTAL to 100% complete: ~9 hours**

---

## 🎓 Key Concepts (Must Understand)

### Realized vs Unrealized P&L

**Realized P&L** = Profit/loss from CLOSED positions
```
Entry: Long 2 MNQ @ $26,000
Exit:  Sell 2 MNQ @ $26,100
Realized P&L: +$100 × 2 contracts × $2/point = +$400 (DONE - locked in)
```

**Unrealized P&L** = Floating profit/loss from OPEN positions
```
Entry: Long 2 MNQ @ $26,000
Current: Market at $26,100 (position still open)
Unrealized P&L: +$100 × 2 contracts × $2/point = +$400 (FLOATING - not locked in)

If market moves to $25,900:
Unrealized P&L: -$100 × 2 contracts × $2/point = -$400 (LOSS - still floating)
```

**Your job**: Calculate unrealized P&L in real-time as market price changes.

### Event Flow (How It All Works)

```
1. SDK Quote Update (every tick, multiple per second)
   ↓
2. Trading Integration Updates Price Cache (SILENT - no logs)
   ↓
3. Trading Integration Calculates Unrealized P&L (using calculator)
   ↓
4. If P&L changed significantly (>$10), emit UNREALIZED_PNL_UPDATE event
   ↓
5. Risk Engine evaluates all rules against event
   ↓
6. Rule checks: Is unrealized P&L ≥ target or ≤ limit?
   ↓
7. If YES: Return violation dict
   ↓
8. Engine triggers enforcement action (close position, flatten, alert)
```

### Tick Economics (Already Solved)

**Tick Size** = Minimum price movement (e.g., 0.25 for MNQ)
**Tick Value** = Dollar value of one tick (e.g., $0.50 for MNQ)

**Example Calculation**:
```python
Entry: $26,000.00
Current: $26,100.00
Diff: +$100.00

Ticks: $100.00 / $0.25 (tick_size) = 400 ticks
Value: 400 ticks × $0.50 (tick_value) = $200 per contract
P&L: $200 × 2 contracts = $400 unrealized profit
```

**Don't reinvent this** - use existing `TICK_VALUES` table and `get_tick_economics()` function.

---

## 🔍 Debugging Tips

### If Quotes Aren't Coming Through
```bash
# Check SDK connection
python run_dev.py --log-level DEBUG

# Look for:
# ✅ SignalR WebSocket connected
# ✅ TradingSuite created for ['MNQ', 'ENQ', 'ES']
# ✅ Real-time feeds connected

# If missing, check:
# - SDK version (should be 3.5.9)
# - Account credentials
# - Network connection
```

### If P&L Calculation Is Wrong
```python
# Add debug logging:
logger.debug(f"Position: {contract_id}")
logger.debug(f"  Entry: ${entry_price}")
logger.debug(f"  Current: ${current_price}")
logger.debug(f"  Diff: ${current_price - entry_price}")
logger.debug(f"  Ticks: {(current_price - entry_price) / tick_size}")
logger.debug(f"  Value: ${unrealized_pnl}")
```

### If Rule Doesn't Trigger
```python
# Check rule evaluation:
logger.info(f"Rule {self.__class__.__name__}:")
logger.info(f"  Current P&L: ${total_unrealized_pnl}")
logger.info(f"  Limit: ${self.limit}")
logger.info(f"  Should trigger: {total_unrealized_pnl <= self.limit}")
```

---

## 📞 When You're Stuck

1. **Check logs**: `run_dev.py` output shows everything
2. **Check tests**: `tests/unit/test_rules/test_daily_unrealized_loss.py`
3. **Check similar code**: `daily_realized_loss.py` (realized P&L logic)
4. **Read SDK docs**: Project-X-Py SDK documentation
5. **Ask user**: "The specs say X, but the implementation shows Y. Which is correct?"

---

## ✅ Definition of Done

### For Unrealized P&L Rules:
- [ ] `UnrealizedPnLCalculator` class created and tested
- [ ] Quote subscription working (see price updates in debug logs)
- [ ] RULE-004 loads and evaluates correctly
- [ ] RULE-005 loads and evaluates correctly
- [ ] Both rules trigger at correct thresholds
- [ ] Enforcement actions work (test with `alert` first!)
- [ ] No log spam from quote updates
- [ ] Tests pass: `pytest tests/unit/test_rules/test_daily_unrealized_loss.py -v`

### For Overall System:
- [ ] 9/9 rules loading (currently 4/9)
- [ ] All rules tested with `run_dev.py`
- [ ] All tests passing (currently 1,362/1,366)
- [ ] Documentation updated if specs were wrong

---

## 🎯 Success = This Output

```bash
$ python run_dev.py

Configuration loaded successfully!
  Rules enabled: 9

✅ Loaded: DailyRealizedLossRule
✅ Loaded: DailyRealizedProfitRule
✅ Loaded: MaxContractsPerInstrumentRule
✅ Loaded: DailyUnrealizedLossRule          ← NEW!
✅ Loaded: MaxUnrealizedProfitRule          ← NEW!
✅ Loaded: TradeFrequencyLimitRule          ← NEW!
✅ Loaded: CooldownAfterLossRule            ← NEW!
✅ Loaded: SessionBlockOutsideRule          ← NEW!
✅ Loaded: AuthLossGuardRule

Risk Manager is running!

📊 POSITION OPENED - MNQ LONG 2 @ $26,000.00 | Unrealized: $0.00

# Price moves...
📊 Unrealized P&L Update - MNQ: $+400.00

❌ Rule: MaxUnrealizedProfit → FAIL ($+400.00 ≥ $500.00)
⚠️  Enforcement: CLOSE_POSITION triggered

💰 ORDER FILLED - MNQ SELL 2 @ $26,200.00
📊 POSITION CLOSED - Realized P&L: $+400.00

✅ Profit locked in!
```

**That's what success looks like!** 🎉

---

## 📚 Essential Files Reference

| Purpose | File Path |
|---------|-----------|
| **Main handoff** | `AI_HANDOFF_UNREALIZED_PNL_RULES.md` |
| **What was built** | `AGENT_SWARM_COMPLETION_2025-10-30.md` |
| **System status** | `SWARM_COMPLETION_REPORT_2025-10-30.md` |
| **Rule spec 004** | `docs/specifications/unified/rules/RULE-004-daily-unrealized-loss.md` |
| **Rule spec 005** | `docs/specifications/unified/rules/RULE-005-max-unrealized-profit.md` |
| **Rule code 004** | `src/risk_manager/rules/daily_unrealized_loss.py` |
| **Rule code 005** | `src/risk_manager/rules/max_unrealized_profit.py` |
| **SDK integration** | `src/risk_manager/integrations/trading.py` |
| **Tick utilities** | `src/risk_manager/integrations/tick_economics.py` |
| **Test environment** | `run_dev.py` |
| **Config** | `config/risk_config.yaml` |

---

## 🚀 START HERE

1. ✅ Read this quick start (DONE!)
2. 📖 Read `AI_HANDOFF_UNREALIZED_PNL_RULES.md` (15 minutes)
3. 💻 Run `python run_dev.py` to see current state (2 minutes)
4. 🔨 Start coding! (Follow the handoff document's Step 1-4)

**Good luck!** 🎯

---

**Remember**: The system is 85% complete. You're finishing the last 15%. The foundation is solid - just add the P&L calculation layer and everything will work! 💪
