S C:\Users\jakers\Desktop\risk-manager-v34> & C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Scripts\Activate.ps1
(.venv-1) PS C:\Users\jakers\Desktop\risk-manager-v34> python run_dev.py

============================================================
        RISK MANAGER V34 - DEVELOPMENT MODE
============================================================

2025-10-30 14:15:43.205 | INFO     | risk_manager.cli.logger:setup_logging:166 - Logging initialized: console=INFO, file=DEBUG
2025-10-30 14:15:43.205 | INFO     | risk_manager.cli.logger:setup_logging:167 - Log file: C:\Users\jakers\Desktop\risk-manager-v34\data\logs\risk_manager.log
2025-10-30 14:15:43.206 | INFO     | __main__:main:126 - 🎛️  Console Log Level: INFO
2025-10-30 14:15:43.206 | INFO     | __main__:main:128 - 💡 Tip: Use --log-level DEBUG to see detailed order payloads
2025-10-30 14:15:43.206 | INFO     | risk_manager.cli.logger:log_checkpoint:208 - 🚀 [CHECKPOINT 1] Service Start | version=1.0.0-dev | mode=development
{"timestamp":"2025-10-30T19:15:43.207486Z","level":"INFO","logger":"risk_manager.checkpoints","module":"logger","function":"log_checkpoint","line":213,"message":"🚀 [CHECKPOINT 1] Service Start | version=1.0.0-dev | mode=development","taskName":"Task-1"}
Loading configuration...
Loading runtime configuration...

1. Loading credentials
   OK: Credentials loaded for user: jake...ader

2. Loading risk configuration
   File: C:\Users\jakers\Desktop\risk-manager-v34\config\risk_config.yaml
C:\Users\jakers\Desktop\risk-manager-v34\src\risk_manager\config\models.py:1095: UserWarning: daily_unrealized_loss.limit (-20.0) should be >= daily_realized_loss.limit (-5.0) to trigger before realized loss
  warnings.warn(
   OK: Risk configuration loaded
   OK: Enabled rules: 10

3. Loading accounts configuration
   File: C:\Users\jakers\Desktop\risk-manager-v34\config\accounts.yaml
   OK: Accounts configuration loaded

4. Selecting account
   Auto-selected (only account): PRAC-V2-126244-84184528
   OK: Selected account: PRAC-V2-126244-84184528

5. Validating configuration structure
   OK: Configuration structure validated

OK: Runtime configuration loaded successfully!

Configuration loaded successfully!
  Account: PRAC-V2-126244-84184528
  Instruments: MNQ, ENQ, ES
  Rules enabled: 10

Initializing Risk Manager...
2025-10-30 14:15:43.239 | INFO     | risk_manager.core.engine:__init__:33 - Risk Engine initialized
{"timestamp":"2025-10-30T19:15:43.242830Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"__init__","line":48,"message":"🚀 Risk Manager starting...","taskName":"Task-1"}
2025-10-30 14:15:43 | INFO     | risk_manager.core.manager:__init__ - Risk Manager initialized
{"timestamp":"2025-10-30T19:15:43.243418Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"create","line":133,"message":"✅ Config loaded: 0 custom rules, monitoring 0 instruments","taskName":"Task-1"}        
2025-10-30 14:15:43 | INFO     | risk_manager.state.database:__init__ - Database initialized at data\risk_state.db
2025-10-30 14:15:43 | INFO     | risk_manager.state.timer_manager:__init__ - TimerManager initialized
2025-10-30 14:15:43 | INFO     | risk_manager.state.pnl_tracker:__init__ - PnLTracker initialized
2025-10-30 14:15:43 | INFO     | risk_manager.state.lockout_manager:load_lockouts_from_db - Loaded 0 lockouts from database
2025-10-30 14:15:43 | INFO     | risk_manager.state.lockout_manager:__init__ - Lockout Manager initialized
2025-10-30 14:15:43 | INFO     | risk_manager.rules.daily_realized_loss:__init__ - DailyRealizedLossRule initialized: limit=$-5.00, reset=17:00 America/New_York
2025-10-30 14:15:43 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedLossRule
2025-10-30 14:15:43 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedLossRule (limit=$-5.0)
2025-10-30 14:15:43 | INFO     | risk_manager.rules.daily_realized_profit:__init__ - DailyRealizedProfitRule initialized: target=$1000.00, reset=17:00 America/New_York
2025-10-30 14:15:43 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedProfitRule
2025-10-30 14:15:43 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedProfitRule (target=$1000.0)
2025-10-30 14:15:43 | INFO     | risk_manager.rules.max_contracts_per_instrument:__init__ - MaxContractsPerInstrumentRule initialized - Limits: {'MNQ': 2, 'ES': 1}, Enforcement: reduce_to_limit, Unknown: allow_with_limit:3
2025-10-30 14:15:43 | INFO     | risk_manager.core.engine:add_rule - Added rule: MaxContractsPerInstrumentRule
2025-10-30 14:15:43 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: MaxContractsPerInstrumentRule (2 symbols)
2025-10-30 14:15:43 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ TradeFrequencyLimitRule requires timers_config.yaml (skipped)
2025-10-30 14:15:43 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ CooldownAfterLossRule requires timers_config.yaml (skipped)
2025-10-30 14:15:43 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ SessionBlockOutsideRule requires timers_config.yaml (skipped)
2025-10-30 14:15:43 | INFO     | risk_manager.core.engine:add_rule - Added rule: AuthLossGuardRule
2025-10-30 14:15:43 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: AuthLossGuardRule
2025-10-30 14:15:43 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyUnrealizedLossRule
2025-10-30 14:15:43 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyUnrealizedLossRule (limit=$-20.0)
2025-10-30 14:15:43 | INFO     | risk_manager.core.engine:add_rule - Added rule: MaxUnrealizedProfitRule
2025-10-30 14:15:43 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: MaxUnrealizedProfitRule (target=$20.0)
2025-10-30 14:15:43 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ 3 rules skipped (require additional configuration)
2025-10-30 14:15:43 | WARNING  | risk_manager.core.manager:_add_default_rules -    TradeManagement rule requires bracket order configuration
2025-10-30 14:15:43 | WARNING  | risk_manager.core.manager:_add_default_rules -    Timer-based rules require timers_config.yaml
{"timestamp":"2025-10-30T19:15:43.367607Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"_add_default_rules","line":515,"message":"✅ Rules initialized: 6 rules loaded from configuration","taskName":"Task-1"
}
2025-10-30 14:15:43 | INFO     | risk_manager.core.manager:_add_default_rules - Loaded 6/9 enabled rules
2025-10-30 14:15:43 | INFO     | risk_manager.core.manager:create - Risk Manager created for instruments: None
Risk Manager initialized!

Connecting to TopstepX API...
  Username: jakertrader
  Account: PRAC-V2-126244-84184528
2025-10-30 14:15:43 | INFO     | risk_manager.integrations.trading:__init__ - Trading integration initialized for: ['MNQ', 'ENQ', 'ES']
2025-10-30 14:15:43 | INFO     | risk_manager.integrations.trading:connect - Connecting to ProjectX trading platform...
2025-10-30 14:15:43 | INFO     | risk_manager.integrations.trading:connect - Step 1: Authenticating via HTTP API...
2025-10-30 14:15:44 | INFO     | risk_manager.integrations.trading:connect - ✅ Authenticated: PRAC-V2-126244-84184528 (ID: 13298777)
2025-10-30 14:15:44 | INFO     | risk_manager.integrations.trading:connect -    Balance: $146,056.08, Trading: True
2025-10-30 14:15:44 | INFO     | risk_manager.integrations.trading:connect - Step 2: Establishing SignalR WebSocket connection...
{"timestamp":"2025-10-30T19:15:44.615533Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T19:15:55.759118Z","level":"ERROR","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"connect","line":316,"message":"WebSocket error","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
2025-10-30 14:15:55 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ SignalR WebSocket connected (User Hub + Market Hub)
2025-10-30 14:15:55 | INFO     | risk_manager.integrations.trading:connect - Step 3: Initializing TradingSuite...
{"timestamp":"2025-10-30T19:15:56.429164Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-7"}
{"timestamp":"2025-10-30T19:15:56.524170Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-7"}
{"timestamp":"2025-10-30T19:15:56.524510Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-7"}
{"timestamp":"2025-10-30T19:15:56.524701Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-7","instrument":"ES"}
{"timestamp":"2025-10-30T19:15:56.525035Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-7"}
{"timestamp":"2025-10-30T19:15:56.525360Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-7","manager":"PositionManager"}
{"timestamp":"2025-10-30T19:15:56.526989Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-6"}
{"timestamp":"2025-10-30T19:15:56.527296Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-6"}
{"timestamp":"2025-10-30T19:15:56.527527Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-6"}    
{"timestamp":"2025-10-30T19:15:56.527717Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-6","instrument":"ENQ"}
{"timestamp":"2025-10-30T19:15:56.528000Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-6"}
{"timestamp":"2025-10-30T19:15:56.528230Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-6","manager":"PositionManager"}
{"timestamp":"2025-10-30T19:15:56.529286Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-5"}
{"timestamp":"2025-10-30T19:15:56.529575Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-5"}
{"timestamp":"2025-10-30T19:15:56.529830Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-5"}    
{"timestamp":"2025-10-30T19:15:56.530082Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-5","instrument":"MNQ"}
{"timestamp":"2025-10-30T19:15:56.530341Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-5"}
{"timestamp":"2025-10-30T19:15:56.530570Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-5","manager":"PositionManager"}
{"timestamp":"2025-10-30T19:15:56.530959Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"__init__","line":443,"message":"TradingSuite created for ['MNQ', 'ENQ', 'ES'] with features: [<Features.PERFORMANCE_ANALYTICS: 'performance_analytics'>, <Features.AUTO_RECONNECT: 'auto_reconnect'>]","taskName":"Task-1"}
{"timestamp":"2025-10-30T19:15:56.531224Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":840,"message":"Connecting to real-time feeds...","taskName":"Task-1"}
{"timestamp":"2025-10-30T19:15:56.531471Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T19:16:07.594021Z","level":"ERROR","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"connect","line":316,"message":"WebSocket error","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T19:16:07.596106Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-10"}
{"timestamp":"2025-10-30T19:16:07.596356Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-10
"}
{"timestamp":"2025-10-30T19:16:07.596721Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-10"}{"timestamp":"2025-10-30T19:16:07.597042Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-11"}     
{"timestamp":"2025-10-30T19:16:07.597272Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-11
"}
{"timestamp":"2025-10-30T19:16:07.597632Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-11"}{"timestamp":"2025-10-30T19:16:07.597959Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-12"}     
{"timestamp":"2025-10-30T19:16:07.598191Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-12
"}
{"timestamp":"2025-10-30T19:16:07.598457Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-12"}{"timestamp":"2025-10-30T19:16:07.601067Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-11"}
{"timestamp":"2025-10-30T19:16:07.601360Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-11","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T19:16:07.601608Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-11","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T19:16:07.601844Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T19:16:07.602036Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T19:16:07.602765Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-10"}
{"timestamp":"2025-10-30T19:16:07.603007Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-10","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T19:16:07.603249Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-10","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T19:16:07.603473Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T19:16:07.603674Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T19:16:07.604334Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-12"}
{"timestamp":"2025-10-30T19:16:07.604557Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-12","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T19:16:07.604777Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-12","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T19:16:07.604991Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T19:16:07.605174Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T19:16:07.643520Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-11","position_count":0}
{"timestamp":"2025-10-30T19:16:07.643814Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-11","refreshed_count":0}
{"timestamp":"2025-10-30T19:16:07.645161Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-10","position_count":0}
{"timestamp":"2025-10-30T19:16:07.645372Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-10","refreshed_count":0}
{"timestamp":"2025-10-30T19:16:07.648837Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-12","position_count":0}
{"timestamp":"2025-10-30T19:16:07.649143Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-12","refreshed_count":0}
{"timestamp":"2025-10-30T19:16:07.877161Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 826.1 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-11","operation":"initialize","instrument":"ES","initial_days":5}
{"timestamp":"2025-10-30T19:16:07.899618Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 826.1 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-12","operation":"initialize","instrument":"ES","initial_days":5}
{"timestamp":"2025-10-30T19:16:07.928810Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 826.1 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-10","operation":"initialize","instrument":"ES","initial_days":5}
{"timestamp":"2025-10-30T19:16:07.986105Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 826.1 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-11","operation":"initialize","instrument":"ES","initial_days":5}
{"timestamp":"2025-10-30T19:16:07.986592Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-11"}
{"timestamp":"2025-10-30T19:16:07.988982Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-11","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:16:08.016715Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 826.1 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-12","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:16:08.017206Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-12"}
{"timestamp":"2025-10-30T19:16:08.033595Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-12","operation":"start_realtime_feed","instrument":"ES","contract_id":"CON.F.US.EP.Z25"}
{"timestamp":"2025-10-30T19:16:08.040585Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 826.1 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-10","operation":"start_realtime_feed","instrument":"ES","contract_id":"CON.F.US.EP.Z25"}
{"timestamp":"2025-10-30T19:16:08.041233Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-10"}
{"timestamp":"2025-10-30T19:16:08.085136Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-10","operation":"start_realtime_feed","instrument":"MNQ","contract_id":"CON.F.US.MNQ.Z25"}
{"timestamp":"2025-10-30T19:16:08.085893Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":853,"message":"TradingSuite initialization complete","taskName":"Task-1"}
2025-10-30 14:16:08 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ Connected to ProjectX (HTTP + WebSocket + TradingSuite)
2025-10-30 14:16:08 | ERROR    | risk_manager.integrations.trading:connect - Failed to connect to trading platform: 'TradingIntegration' object has no attribute '_get_side_name'
Failed to connect to TopstepX: 'TradingIntegration' object has no attribute '_get_side_name'

Possible issues:
  1. Invalid credentials in .env
  2. Network connectivity
  3. TopstepX API down
Traceback (most recent call last):
  File "C:\Users\jakers\Desktop\risk-manager-v34\run_dev.py", line 209, in main
    await trading_integration.connect()
  File "C:\Users\jakers\Desktop\risk-manager-v34\src\risk_manager\integrations\trading.py", line 350, in connect
    self._get_side_name
AttributeError: 'TradingIntegration' object has no attribute '_get_side_name'
Task was destroyed but it is pending!
task: <Task pending name='Task-121' coro=<CallbackMixin._trigger_callbacks() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:236> wait_for=<_GatheringFuture finished result=[None]>>
Task was destroyed but it is pending!
task: <Task pending name='Task-163' coro=<CallbackMixin._trigger_callbacks() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225>>
C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\base_events.py:744: RuntimeWarning: coroutine 'CallbackMixin._trigger_callbacks' was never awaited
  self._ready.clear()
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
Task was destroyed but it is pending!
task: <Task pending name='Task-164' coro=<CallbackMixin._trigger_callbacks() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225>>
Task was destroyed but it is pending!
task: <Task pending name='Task-165' coro=<CallbackMixin._trigger_callbacks() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225>>
Task was destroyed but it is pending!
task: <Task pending name='Task-125' coro=<CallbackMixin._trigger_callbacks() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:236> wait_for=<_GatheringFuture finished result=[None]>>
Task was destroyed but it is pending!
task: <Task pending name='Task-166' coro=<CallbackMixin._trigger_callbacks() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225>>
Task was destroyed but it is pending!
task: <Task pending name='Task-167' coro=<CallbackMixin._trigger_callbacks() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225>>
Task was destroyed but it is pending!
task: <Task pending name='Task-128' coro=<CallbackMixin._trigger_callbacks() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:236> wait_for=<_GatheringFuture finished result=[None]>>
Task was destroyed but it is pending!
task: <Task pending name='Task-130' coro=<EventHandlingMixin._forward_event_async() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime\event_handling.py:451> wait_for=<_GatheringFuture finished result=[None]> cb=[_chain_future.<locals>._call_set_state() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\futures.py:391]>
Task was destroyed but it is pending!
task: <Task pending name='Task-132' coro=<EventHandlingMixin._forward_event_async() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime\event_handling.py:451> wait_for=<_GatheringFuture finished result=[None]> cb=[_chain_future.<locals>._call_set_state() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\futures.py:391]>
Task was destroyed but it is pending!
task: <Task pending name='Task-134' coro=<EventHandlingMixin._forward_event_async() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime\event_handling.py:451> wait_for=<_GatheringFuture finished result=[None]> cb=[_chain_future.<locals>._call_set_state() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\futures.py:391]>
Task was destroyed but it is pending!
task: <Task pending name='Task-137' coro=<EventHandlingMixin._forward_event_async() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime\event_handling.py:451> wait_for=<_GatheringFuture finished result=[None]> cb=[_chain_future.<locals>._call_set_state() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\futures.py:391]>
Task was destroyed but it is pending!
task: <Task pending name='Task-143' coro=<CallbackMixin._trigger_callbacks() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225> wait_for=<_GatheringFuture pending cb=[Task.task_wakeup()]>>
Task was destroyed but it is pending!
task: <Task pending name='Task-144' coro=<CallbackMixin._trigger_callbacks() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225> wait_for=<_GatheringFuture pending cb=[Task.task_wakeup()]>>
Task was destroyed but it is pending!
task: <Task pending name='Task-145' coro=<CallbackMixin._trigger_callbacks() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225> wait_for=<_GatheringFuture pending cb=[Task.task_wakeup()]>>
Task was destroyed but it is pending!
task: <Task pending name='Task-147' coro=<CallbackMixin._trigger_callbacks() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225> wait_for=<_GatheringFuture pending cb=[Task.task_wakeup()]>>
Task was destroyed but it is pending!
task: <Task pending name='Task-150' coro=<CallbackMixin._trigger_callbacks() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime_data_manager\callbacks.py:225> wait_for=<_GatheringFuture pending cb=[Task.task_wakeup()]>>
Task was destroyed but it is pending!
task: <Task pending name='Task-155' coro=<EventHandlingMixin._forward_event_async() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime\event_handling.py:451> wait_for=<_GatheringFuture pending cb=[Task.task_wakeup()]> cb=[_chain_future.<locals>._call_set_state() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\futures.py:391]>
Task was destroyed but it is pending!
task: <Task pending name='Task-158' coro=<EventHandlingMixin._forward_event_async() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime\event_handling.py:451> wait_for=<_GatheringFuture pending cb=[Task.task_wakeup()]> cb=[_chain_future.<locals>._call_set_state() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\futures.py:391]>
Task was destroyed but it is pending!
task: <Task pending name='Task-160' coro=<EventHandlingMixin._forward_event_async() done, defined at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\realtime\event_handling.py:451> wait_for=<_GatheringFuture pending cb=[Task.task_wakeup()]> cb=[_chain_future.<locals>._call_set_state() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\futures.py:391]>
<sys>:0: RuntimeWarning: coroutine 'EventBus._execute_handler' was never awaited
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
Task was destroyed but it is pending!
task: <Task pending name='Task-168' coro=<EventBus._execute_handler() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\event_bus.py:281> cb=[gather.<locals>._done_callback() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\tasks.py:820]>
Task was destroyed but it is pending!
task: <Task pending name='Task-169' coro=<EventBus._execute_handler() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\event_bus.py:281> cb=[gather.<locals>._done_callback() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\tasks.py:820]>
Task was destroyed but it is pending!
task: <Task pending name='Task-170' coro=<EventBus._execute_handler() running at C:\Users\jakers\Desktop\risk-manager-v34\.venv-1\Lib\site-packages\project_x_py\event_bus.py:281> cb=[gather.<locals>._done_callback() at C:\Users\jakers\AppData\Local\Programs\Python\Python313\Lib\asyncio\tasks.py:820]>
(.venv-1) PS C:\Users\jakers\Desktop\risk-manager-v34> 