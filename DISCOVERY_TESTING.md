# Discovery Testing Guide

**Goal**: Understand broker data model before implementing caching/filtering strategy.

**Status**: Ready to test! 🚀

---

## Quick Start

### Step 1: Payload Capture (20 minutes)

**What**: Captures ALL broker events while you manually trade.

**Run**:
```bash
python test_payload_capture.py
```

**Then in your broker UI**:
1. Buy 2 MNQ contracts
2. Place a stop loss
3. Buy 2 MORE MNQ (scale in) ← **Critical edge case**
4. Place another stop loss
5. Modify one stop loss (move the price)
6. Cancel one stop loss
7. Let one stop loss hit (or manually close)
8. Close remaining position

**Press Ctrl+C when done**

**Output**: `broker_payloads_TIMESTAMP.log` with complete event data

**What to look for**:
- Complete Order object schema (all fields)
- Complete Position payload (all fields)
- Linking fields (position_id, parent_order_id, bracket_id?)
- Order type/status number mappings (type=0,1,2,3,4,5...)

---

### Step 2: SDK Query (5 minutes)

**What**: Queries SDK state to see what's available.

**Prerequisites**: Have an OPEN position with ACTIVE stop loss

**Run**:
```bash
python test_sdk_queries.py
```

**What to look for**:
- Does Position have stopLoss/takeProfit fields?
- Does Order have position_id field?
- How are orders linked to positions?
- What's available in working_orders?

---

## Edge Cases to Test

### 🔥 Critical: Position Scaling (Yoking)

**Scenario**:
```
1. Buy 2 MNQ @ $26250 (stop @ $26240)
2. Buy 2 MORE MNQ @ $26260 (stop @ $26250)
```

**Questions to answer**:
- [ ] Do we get POSITION_UPDATED or new POSITION_OPENED?
- [ ] How many stop orders are working? (1 or 2?)
- [ ] Does first stop get auto-cancelled?
- [ ] What's the position size? (4 contracts aggregated?)
- [ ] What's the avg price? ($26255?)
- [ ] If we close 2 contracts, which stop remains?

**How to test**:
```bash
# Run payload capture
python test_payload_capture.py

# In broker:
# 1. Buy 2 MNQ with stop
# 2. Wait 5 seconds
# 3. Buy 2 MORE MNQ with different stop
# 4. Check logs for POSITION_OPENED vs POSITION_UPDATED
# 5. Run SDK query to see how many stops are working

python test_sdk_queries.py
# Check: How many working orders for this contract?
```

---

### Edge Case 2: Stop Loss Modification

**Scenario**: Position open, move stop loss to different price.

**Questions**:
- [ ] Does ORDER_MODIFIED event fire?
- [ ] Same order_id or new order?
- [ ] What changes in the payload?

**Test**: Move stop in broker UI, check logs.

---

### Edge Case 3: Manual Close vs Stop Hit

**Scenario A**: Let stop loss hit naturally
**Scenario B**: Manually close position (with stop still working)

**Questions**:
- [ ] Can we distinguish between them?
- [ ] Does manual close auto-cancel the stop?
- [ ] Different event sequences?

**Test**: Compare event logs for both scenarios.

---

### Edge Case 4: Orphaned Stops

**Critical safety check!**

**Scenario**:
```
1. Open position (stop @ $26240)
2. Manually close position
3. Check: Is stop still working?
```

**If stop is still working** → **DANGER!**
- Could trigger on reverse position
- Need to explicitly cancel stops on close

**Test**:
```bash
# After closing position, run:
python test_sdk_queries.py

# Check working orders - should be 0 for that contract
# If not 0, broker doesn't auto-cancel stops!
```

---

## What to Document

After testing, update `cache_system.md` Phase 6:

### Order Type Mappings
```
type=0: MARKET ✅
type=1: LIMIT ✅
type=2: ??? ← Fill in
type=3: STOP_LIMIT ✅
type=4: STOP ✅
type=5: TRAILING_STOP ✅
```

### Order Status Mappings
```
status=0: ??? ← Fill in
status=1: ???
status=2: FILLED ✅
status=3: ???
```

### Position Behavior
```
Position Scaling:
  - Broker aggregates: YES/NO
  - Multiple stops supported: YES/NO
  - First stop auto-cancelled: YES/NO

Manual Close:
  - Auto-cancels stops: YES/NO ← CRITICAL!

Linking:
  - Orders → Positions via: contractId only / position_id field / other?
```

---

## Expected Timeline

**Today (1 hour)**:
- [ ] Run `test_payload_capture.py` with manual trading (20 min)
- [ ] Run `test_sdk_queries.py` with open position (5 min)
- [ ] Review logs and identify fields (20 min)
- [ ] Test position scaling edge case (15 min)

**Tomorrow**:
- [ ] Test 3-4 more edge cases
- [ ] Document findings in `cache_system.md`

**This Week**:
- [ ] Complete all edge case testing
- [ ] Fill in Phase 6 of `cache_system.md`
- [ ] Choose architecture (Option A/B/C)

**Next Week**:
- [ ] Implement chosen architecture
- [ ] Write tests
- [ ] Deploy

---

## Success Criteria

✅ **Discovery is complete when you can answer**:

1. "Show me the complete Order object schema" → Have it
2. "How many stops after scaling in?" → Tested it
3. "Does close auto-cancel stops?" → Tested it
4. "What links orders to positions?" → Know the field(s)
5. "Which architecture should we use?" → Can justify it

---

## Files Generated

- `test_payload_capture.py` - Event capture script ✅
- `test_sdk_queries.py` - SDK state query script ✅
- `broker_payloads_TIMESTAMP.log` - Event logs (after running)
- `cache_system.md` - Living document (update Phase 6)

---

## Quick Commands

```bash
# Capture events
python test_payload_capture.py

# Query SDK state
python test_sdk_queries.py

# View latest log
ls -lt broker_payloads_*.log | head -1

# Search logs
grep "POSITION_OPENED" broker_payloads_*.log
grep "stop" broker_payloads_*.log -i
```

---

## Need Help?

**If scripts fail**:
- Check credentials (Project-X API keys)
- Check connection (SDK can connect?)
- Try running `python run_dev.py` first to verify setup

**If no events captured**:
- Make sure you're trading in the broker UI
- Check that SDK is actually connected
- Try a simple market order first

**If confused by output**:
- Focus on "All Attributes" section - that's the schema
- Look for fields we're not currently logging
- Check for linking fields (position_id, parent_order_id, etc.)

---

**Ready? Run the first script! 🚀**

```bash
python test_payload_capture.py
```
