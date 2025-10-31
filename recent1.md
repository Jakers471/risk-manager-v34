
============================================================

📊 Unrealized P&L: $+0.00  2025-10-31 12:21:11 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ BUY 2 @ $25,900.00
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 9 rules
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: TradeFrequencyLimit → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: CooldownAfterLoss → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: SessionBlockOutside → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION OPENED - MNQ LONG 2 @ $25,900.00 | P&L: $0.00
📊 Unrealized P&L: $+0.00  2025-10-31 12:21:11 | WARNING  | risk_manager.integrations.sdk.event_router:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-31 12:21:11 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   ℹ️  No take profit order
2025-10-31 12:21:11 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 2 | P&L: $0.00
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_opened → evaluating 9 rules
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS (MNQ: 2/2 max)
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: TradeFrequencyLimit → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: CooldownAfterLoss → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: SessionBlockOutside → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-31 12:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
📊 Unrealized P&L: $-6.00  2025-10-31 12:21:19 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ SELL 2 @ $25,898.25
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 9 rules
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: TradeFrequencyLimit → PASS
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: CooldownAfterLoss → PASS
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: SessionBlockOutside → PASS
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-31 12:21:19 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION CLOSED - MNQ FLAT 0 @ $25,900.00 | P&L: $0.00
2025-10-31 12:21:19 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 💰 Realized P&L: $-7.00
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_closed → evaluating 9 rules
2025-10-31 12:21:19 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Event type matches! Processing EventType.POSITION_CLOSED
2025-10-31 12:21:19 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    profitAndLoss from event data: -7.0
2025-10-31 12:21:19 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Have profitAndLoss: $-7.00, updating tracker...
2025-10-31 12:21:19 | INFO     | risk_manager.rules.daily_realized_loss:evaluate - 💰 Daily P&L: $-170.50 / $-5.00 limit (this trade: $-7.00)
2025-10-31 12:21:19 | WARNING  | risk_manager.rules.daily_realized_loss:evaluate - Daily loss limit breached for account 13298777: P&L=$-170.50, Limit=$-5.00
2025-10-31 12:21:19 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyRealizedLoss → FAIL (P&L: $-170.50 / $-5.00 limit)
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:_handle_violation - DEBUG: _handle_violation() ENTERED for rule=DailyRealizedLossRule
2025-10-31 12:21:19 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyRealizedLoss - Daily loss limit exceeded: $-170.50 (limit: $-5.00)
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:_handle_violation - DEBUG: After violation log for DailyRealizedLoss
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:_handle_violation - DEBUG: Reached rule.enforce() block for DailyRealizedLoss
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:_handle_violation - DEBUG: hasattr(rule, 'enforce') = True
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:_handle_violation - DEBUG: violation keys = ['rule', 'message', 'account_id', 'daily_loss', 'current_loss', 'limit', 'action', 'lockout_required', 'reset_time', 'timezone']
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:_handle_violation - DEBUG: account_id = 13298777
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:_handle_violation - 🔒 Calling DailyRealizedLoss.enforce() for lockout/timer management
2025-10-31 12:21:19 | CRITICAL | risk_manager.rules.daily_realized_loss:enforce - ENFORCING RULE-003: Account 13298777 Daily P&L: $-170.50, Limit: $-5.00
2025-10-31 12:21:19 | WARNING  | risk_manager.state.lockout_manager:set_lockout - Account 13298777 locked until 2025-10-31T21:00:00+00:00: Daily loss limit exceeded: $-170.50 (limit: $-5.00)
2025-10-31 12:21:19 | WARNING  | risk_manager.rules.daily_realized_loss:enforce - Account 13298777 locked until 2025-10-31T21:00:00+00:00: Daily loss limit exceeded: $-170.50 (limit: $-5.00)
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:_handle_violation - ✅ DailyRealizedLoss.enforce() completed successfully
2025-10-31 12:21:19 | INFO     | risk_manager.core.engine:_handle_violation - DEBUG: action = 'flatten' for DailyRealizedLoss
2025-10-31 12:21:19 | CRITICAL | risk_manager.core.engine:_handle_violation - 🛑 ENFORCING: Closing all positions (DailyRealizedLoss)
{"timestamp":"2025-10-31T17:21:19.811897Z","level":"WARNING","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":356,"message":"⚠️ Enforcement triggered: FLATTEN ALL - Rule: DailyRealizedLoss","taskName"
:"Task-8876"}
2025-10-31 12:21:19 | WARNING  | risk_manager.core.engine:flatten_all_positions - Flattening all positions...
2025-10-31 12:21:19 | WARNING  | risk_manager.integrations.trading:flatten_all - FLATTENING ALL POSITIONS
2025-10-31 12:21:19 | WARNING  | risk_manager.integrations.trading:flatten_position - Flattening position for MNQ
{"timestamp":"2025-10-31T17:21:19.863080Z","level":"INFO","logger":"project_x_py.position_manager.operations","module":"operations","function":"close_all_positions","line":408,"message":"Closing position","taskName":"Task-8876","closed":0,"total":0,"failed":0,"operation":"close_all"}
2025-10-31 12:21:19 | INFO     | risk_manager.integrations.trading:flatten_position - ✅ Closed all positions for MNQ via SDK
2025-10-31 12:21:19 | WARNING  | risk_manager.integrations.trading:flatten_position - Flattening position for ENQ
📊 Unrealized P&L: $+0.00  2025-10-31 12:21:33 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ BUY 1 @ $25,897.75
2025-10-31 12:21:33 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 9 rules
2025-10-31 12:21:33 | WARNING  | risk_manager.core.engine:evaluate_rules - ⚠️  LOCKOUT ACTIVE (hard_lockout)
   Reason: Daily loss limit exceeded: $-170.50 (limit: $-5.00)
   ❌ Skipping ALL 9 rules (lockout active)
📊 Unrealized P&L: $+0.00  2025-10-31 12:21:33 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION OPENED - MNQ LONG 1 @ $25,897.75 | P&L: $0.00
2025-10-31 12:21:33 | WARNING  | risk_manager.integrations.sdk.event_router:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-31 12:21:33 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   ℹ️  No take profit order
2025-10-31 12:21:33 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 1 | P&L: $0.00
2025-10-31 12:21:33 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_opened → evaluating 9 rules
2025-10-31 12:21:33 | WARNING  | risk_manager.core.engine:evaluate_rules - ⚠️  LOCKOUT ACTIVE (hard_lockout)
   Reason: Daily loss limit exceeded: $-170.50 (limit: $-5.00)
   ❌ Skipping ALL 9 rules (lockout active)
📊 Unrealized P&L: $+1.50  2025-10-31 12:21:37 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ SELL 1 @ $25,898.25
2025-10-31 12:21:37 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 9 rules
2025-10-31 12:21:37 | WARNING  | risk_manager.core.engine:evaluate_rules - ⚠️  LOCKOUT ACTIVE (hard_lockout)
   Reason: Daily loss limit exceeded: $-170.50 (limit: $-5.00)
   ❌ Skipping ALL 9 rules (lockout active)
2025-10-31 12:21:37 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION CLOSED - MNQ FLAT 0 @ $25,897.75 | P&L: $0.00
2025-10-31 12:21:37 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 💰 Realized P&L: $+1.00
2025-10-31 12:21:37 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_closed → evaluating 9 rules
2025-10-31 12:21:37 | WARNING  | risk_manager.core.engine:evaluate_rules - ⚠️  LOCKOUT ACTIVE (hard_lockout)
   Reason: Daily loss limit exceeded: $-170.50 (limit: $-5.00)
   ❌ Skipping ALL 9 rules (lockout active)
📊 Unrealized P&L: $+0.00  