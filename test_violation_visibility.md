# Rule Violation Visibility Guide

## What You'll See When Rules Detect Breaches

Your Risk Manager has comprehensive logging at every stage. Here's what appears in your console when violations occur:

---

## 🎯 The 6 Active Rules

Currently monitoring:
1. **DailyRealizedLossRule** - Limit: -$5.00 (LOCKOUT: pause trading)
2. **DailyRealizedProfitRule** - Target: $1000.00 (LOCKOUT: pause trading)
3. **MaxContractsPerInstrumentRule** - MNQ: 2, ES: 1 (ACTION: reduce_to_limit)
4. **AuthLossGuardRule** - Monitors authorization loss limits
5. **DailyUnrealizedLossRule** - Limit: -$20.00 (ACTION: close_position/flatten)
6. **MaxUnrealizedProfitRule** - Target: $20.00 (ACTION: close_position)

---

## 📋 Log Visibility Levels

### Every Event Logs:
```
📨 Event: position_opened → evaluating 6 rules
```

### Every Rule Evaluation Logs:
```
✅ Rule: DailyRealizedLoss → PASS (-$2.50)
✅ Rule: MaxUnrealizedProfit → PASS ($+15.00)
```

### When Violation Detected:
```
❌ Rule: DailyRealizedLoss → FAIL (P&L: -$5.25 / -$5.00 limit)
🚨 VIOLATION: DailyRealizedLoss - Daily loss limit exceeded: -$5.25 / -$5.00
```

### When Enforcement Executes:
```
🛑 ENFORCING: Pausing trading (DailyRealizedLoss)
⚠️  Trading paused - awaiting manual intervention
```

---

## 🧪 Test Scenario: Trigger Unrealized Profit Rule

Your unrealized profit limit is set VERY LOW for testing: **$20**

**To see the rule trigger:**

1. Open a position (MNQ or ES)
2. Let it go positive by $20+
3. Watch the logs:

```
📨 Event: unrealized_pnl_update → evaluating 6 rules
✅ Rule: DailyRealizedLoss → PASS
✅ Rule: DailyRealizedProfit → PASS
✅ Rule: MaxContractsPerInstrument → PASS
✅ Rule: AuthLossGuard → PASS
✅ Rule: DailyUnrealizedLoss → PASS
❌ Rule: MaxUnrealizedProfit → FAIL (Position: MNQ @ $+22.00 / $20.00 target)

🚨 VIOLATION: MaxUnrealizedProfit - 1 position(s) hit profit target: $20.00
🛑 ENFORCING: Closing position MNQ (MaxUnrealizedProfit)
Closing position: MNQ (CON.F.US.MNQ.Z25)
✅ Position closed: MNQ
```

---

## 🧪 Test Scenario: Trigger Unrealized Loss Rule

Your unrealized loss limit is also VERY LOW for testing: **-$20**

**To see the rule trigger:**

1. Open a position (MNQ or ES)
2. Let it go negative by $20+
3. Watch the logs:

```
📨 Event: unrealized_pnl_update → evaluating 6 rules
✅ Rule: DailyRealizedLoss → PASS
✅ Rule: DailyRealizedProfit → PASS
✅ Rule: MaxContractsPerInstrument → PASS
✅ Rule: AuthLossGuard → PASS
❌ Rule: DailyUnrealizedLoss → FAIL (Total P&L: -$22.00 / -$20.00 limit)
✅ Rule: MaxUnrealizedProfit → PASS

🚨 VIOLATION: DailyUnrealizedLoss - Daily unrealized loss limit exceeded: -$22.00 ≤ -$20.00
🛑 ENFORCING: Closing all positions (DailyUnrealizedLoss)
Flattening all positions...
✅ All positions flattened
```

---

## 🧪 Test Scenario: Trigger Realized Loss Lockout

Your daily realized loss limit: **-$5.00**

**To see the lockout:**

1. Take multiple losing trades that total -$5+
2. When the cumulative loss hits -$5:

```
📨 Event: trade_executed → evaluating 6 rules
❌ Rule: DailyRealizedLoss → FAIL (P&L: -$5.25 / -$5.00 limit)
✅ Rule: DailyRealizedProfit → PASS
✅ Rule: MaxContractsPerInstrument → PASS
✅ Rule: AuthLossGuard → PASS
✅ Rule: DailyUnrealizedLoss → PASS
✅ Rule: MaxUnrealizedProfit → PASS

🚨 VIOLATION: DailyRealizedLoss - Daily loss limit exceeded: -$5.25 / -$5.00
🛑 ENFORCING: Pausing trading (DailyRealizedLoss)
⚠️  Trading paused - awaiting manual intervention
🔒 LOCKOUT: Account locked until 17:00 America/New_York
```

---

## 📊 P&L Status Bar

While running, you'll see real-time unrealized P&L at the bottom:
```
📊 Unrealized P&L: $+22.50
```

This updates every 0.5 seconds, showing the TOTAL unrealized P&L across ALL open positions.

---

## 🔍 Want MORE Detail?

### Run with DEBUG logging:
```bash
python run_dev.py --log-level DEBUG
```

This shows:
- Every rule's internal calculations
- Market data updates
- Order payload details
- Quote polling activity
- Rule evaluation logic

---

## 📝 Where Logs Are Saved

**Console**: Real-time logs shown in terminal

**File**: `data/logs/risk_manager.log`
- Contains ALL logs (DEBUG level)
- Persists across runs
- Use for post-mortem analysis

**View logs:**
```bash
# Last 50 lines
tail -50 data/logs/risk_manager.log

# Follow live
tail -f data/logs/risk_manager.log

# Search for violations
grep "VIOLATION" data/logs/risk_manager.log

# Search for enforcement
grep "ENFORCING" data/logs/risk_manager.log
```

---

## 🎯 Summary: What You See

**For EVERY violation, you'll see 3 log lines:**

1. **Detection**: `❌ Rule: RuleName → FAIL (context)`
2. **Alert**: `🚨 VIOLATION: RuleName - message`
3. **Enforcement**: `🛑 ENFORCING: action (RuleName)`

**You cannot miss violations - they're logged with critical priority and emoji indicators!**

---

## 💡 Testing Tips

1. **Test unrealized P&L rules first** - Limits are set LOW ($20/-$20) for easy testing
2. **Watch the status bar** - Shows total P&L updating in real-time
3. **Use small positions** - 1 MNQ contract moves ~$5/point, makes testing faster
4. **Check logs after** - `grep "VIOLATION" data/logs/risk_manager.log`

**Your system is already configured for HIGH VISIBILITY! 🔥**
