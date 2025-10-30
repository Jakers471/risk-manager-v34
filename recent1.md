

(.venv-1) PS C:\Users\jakers\Desktop\risk-manager-v34> python run_dev.py

============================================================
        RISK MANAGER V34 - DEVELOPMENT MODE
============================================================

2025-10-30 03:35:55.421 | INFO     | risk_manager.cli.logger:setup_logging:166 - Logging initialized: console=INFO, file=DEBUG
2025-10-30 03:35:55.422 | INFO     | risk_manager.cli.logger:setup_logging:167 - Log file: C:\Users\jakers\Desktop\risk-manager-v34\data\logs\risk_manager.log
2025-10-30 03:35:55.423 | INFO     | __main__:main:126 - 🎛️  Console Log Level: INFO
2025-10-30 03:35:55.424 | INFO     | __main__:main:128 - 💡 Tip: Use --log-level DEBUG to see detailed order payloads
2025-10-30 03:35:55.424 | INFO     | risk_manager.cli.logger:log_checkpoint:208 - 🚀 [CHECKPOINT 1] Service Start | version=1.0.0-dev | mode=development
{"timestamp":"2025-10-30T08:35:55.425277Z","level":"INFO","logger":"risk_manager.checkpoints","module":"logger","function":"log_checkpoint","line":213,"message":"🚀 [CHECKPOINT 1] Service Start | version=1.0.0-dev | mode=development","taskName":"Task-1"}
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
2025-10-30 03:35:55.468 | INFO     | risk_manager.core.engine:__init__:33 - Risk Engine initialized
{"timestamp":"2025-10-30T08:35:55.472943Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"__init__","line":48,"message":"🚀 Risk Manager starting...","taskName":"Task-1"}
2025-10-30 03:35:55 | INFO     | risk_manager.core.manager:__init__ - Risk Manager initialized
{"timestamp":"2025-10-30T08:35:55.473666Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"create","line":133,"message":"✅ Config loaded: 0 custom rules, monitoring 0 instruments","taskName":"Task-1"}        
2025-10-30 03:35:55 | INFO     | risk_manager.state.database:__init__ - Database initialized at data\risk_state.db
2025-10-30 03:35:55 | INFO     | risk_manager.state.timer_manager:__init__ - TimerManager initialized
2025-10-30 03:35:55 | INFO     | risk_manager.state.pnl_tracker:__init__ - PnLTracker initialized
2025-10-30 03:35:55 | INFO     | risk_manager.state.lockout_manager:load_lockouts_from_db - Loaded 0 lockouts from database
2025-10-30 03:35:55 | INFO     | risk_manager.state.lockout_manager:__init__ - Lockout Manager initialized
2025-10-30 03:35:55 | INFO     | risk_manager.rules.daily_realized_loss:__init__ - DailyRealizedLossRule initialized: limit=$-5.00, reset=17:00 America/New_York
2025-10-30 03:35:55 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedLossRule
2025-10-30 03:35:55 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedLossRule (limit=$-5.0)
2025-10-30 03:35:55 | INFO     | risk_manager.rules.daily_realized_profit:__init__ - DailyRealizedProfitRule initialized: target=$1000.00, reset=17:00 America/New_York
2025-10-30 03:35:55 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedProfitRule
2025-10-30 03:35:55 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedProfitRule (target=$1000.0)
2025-10-30 03:35:55 | INFO     | risk_manager.rules.max_contracts_per_instrument:__init__ - MaxContractsPerInstrumentRule initialized - Limits: {'MNQ': 2, 'ES': 1}, Enforcement: reduce_to_limit, Unknown: allow_with_limit:3
2025-10-30 03:35:55 | INFO     | risk_manager.core.engine:add_rule - Added rule: MaxContractsPerInstrumentRule
2025-10-30 03:35:55 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: MaxContractsPerInstrumentRule (2 symbols)
2025-10-30 03:35:55 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ TradeFrequencyLimitRule requires timers_config.yaml (skipped)
2025-10-30 03:35:55 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ CooldownAfterLossRule requires timers_config.yaml (skipped)
2025-10-30 03:35:55 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ SessionBlockOutsideRule requires timers_config.yaml (skipped)
2025-10-30 03:35:55 | INFO     | risk_manager.core.engine:add_rule - Added rule: AuthLossGuardRule
2025-10-30 03:35:55 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: AuthLossGuardRule
2025-10-30 03:35:55 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyUnrealizedLossRule
2025-10-30 03:35:55 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyUnrealizedLossRule (limit=$-20.0)
2025-10-30 03:35:55 | INFO     | risk_manager.core.engine:add_rule - Added rule: MaxUnrealizedProfitRule
2025-10-30 03:35:55 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: MaxUnrealizedProfitRule (target=$20.0)
2025-10-30 03:35:55 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ 3 rules skipped (require additional configuration)
2025-10-30 03:35:55 | WARNING  | risk_manager.core.manager:_add_default_rules -    TradeManagement rule requires bracket order configuration
2025-10-30 03:35:55 | WARNING  | risk_manager.core.manager:_add_default_rules -    Timer-based rules require timers_config.yaml
{"timestamp":"2025-10-30T08:35:55.538902Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"_add_default_rules","line":515,"message":"✅ Rules initialized: 6 rules loaded from configuration","taskName":"Task-1"
}
2025-10-30 03:35:55 | INFO     | risk_manager.core.manager:_add_default_rules - Loaded 6/9 enabled rules
2025-10-30 03:35:55 | INFO     | risk_manager.core.manager:create - Risk Manager created for instruments: None
Risk Manager initialized!

Connecting to TopstepX API...
  Username: jakertrader
  Account: PRAC-V2-126244-84184528
2025-10-30 03:35:55 | INFO     | risk_manager.integrations.trading:__init__ - Trading integration initialized for: ['MNQ', 'ENQ', 'ES']
2025-10-30 03:35:55 | INFO     | risk_manager.integrations.trading:connect - Connecting to ProjectX trading platform...
2025-10-30 03:35:55 | INFO     | risk_manager.integrations.trading:connect - Step 1: Authenticating via HTTP API...
2025-10-30 03:35:57 | INFO     | risk_manager.integrations.trading:connect - ✅ Authenticated: PRAC-V2-126244-84184528 (ID: 13298777)
2025-10-30 03:35:57 | INFO     | risk_manager.integrations.trading:connect -    Balance: $146,490.32, Trading: True
2025-10-30 03:35:57 | INFO     | risk_manager.integrations.trading:connect - Step 2: Establishing SignalR WebSocket connection...
{"timestamp":"2025-10-30T08:35:57.019527Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
2025-10-30 03:36:08 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ SignalR WebSocket connected (User Hub + Market Hub)
2025-10-30 03:36:08 | INFO     | risk_manager.integrations.trading:connect - Step 3: Initializing TradingSuite...
{"timestamp":"2025-10-30T08:36:08.927402Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-6"}
{"timestamp":"2025-10-30T08:36:09.039406Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-6"}
{"timestamp":"2025-10-30T08:36:09.039797Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-6"}
{"timestamp":"2025-10-30T08:36:09.040099Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-6","instrument":"ENQ"}
{"timestamp":"2025-10-30T08:36:09.040687Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-6"}
{"timestamp":"2025-10-30T08:36:09.041132Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-6","manager":"PositionManager"}
{"timestamp":"2025-10-30T08:36:09.043349Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-5"}
{"timestamp":"2025-10-30T08:36:09.043830Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-5"}
{"timestamp":"2025-10-30T08:36:09.044131Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-5"}    
{"timestamp":"2025-10-30T08:36:09.044353Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-5","instrument":"MNQ"}
{"timestamp":"2025-10-30T08:36:09.044746Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-5"}
{"timestamp":"2025-10-30T08:36:09.045105Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-5","manager":"PositionManager"}
{"timestamp":"2025-10-30T08:36:09.047192Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-7"}
{"timestamp":"2025-10-30T08:36:09.047750Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-7"}
{"timestamp":"2025-10-30T08:36:09.048094Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-7"}    
{"timestamp":"2025-10-30T08:36:09.048317Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-7","instrument":"ES"}
{"timestamp":"2025-10-30T08:36:09.048756Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-7"}
{"timestamp":"2025-10-30T08:36:09.049061Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-7","manager":"PositionManager"}
{"timestamp":"2025-10-30T08:36:09.049625Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"__init__","line":443,"message":"TradingSuite created for ['MNQ', 'ENQ', 'ES'] with features: [<Features.PERFORMANCE_ANALYTICS: 'performance_analytics'>, <Features.AUTO_RECONNECT: 'auto_reconnect'>]","taskName":"Task-1"}
{"timestamp":"2025-10-30T08:36:09.050072Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":840,"message":"Connecting to real-time feeds...","taskName":"Task-1"}
{"timestamp":"2025-10-30T08:36:09.050373Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T08:36:20.218748Z","level":"ERROR","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"connect","line":316,"message":"WebSocket error","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T08:36:20.221102Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-10"}
{"timestamp":"2025-10-30T08:36:20.221349Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-10
"}
{"timestamp":"2025-10-30T08:36:20.221641Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-10"}{"timestamp":"2025-10-30T08:36:20.221929Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-11"}     
{"timestamp":"2025-10-30T08:36:20.222174Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-11
"}
{"timestamp":"2025-10-30T08:36:20.222513Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-11"}{"timestamp":"2025-10-30T08:36:20.222838Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-12"}     
{"timestamp":"2025-10-30T08:36:20.223064Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-12
"}
{"timestamp":"2025-10-30T08:36:20.223347Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-12"}{"timestamp":"2025-10-30T08:36:20.226693Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-11"}
{"timestamp":"2025-10-30T08:36:20.227094Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-11","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T08:36:20.227381Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-11","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T08:36:20.227764Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T08:36:20.228043Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T08:36:20.228831Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-10"}
{"timestamp":"2025-10-30T08:36:20.229079Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-10","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T08:36:20.229380Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-10","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T08:36:20.229682Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T08:36:20.229876Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T08:36:20.230689Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-12"}
{"timestamp":"2025-10-30T08:36:20.230929Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-12","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T08:36:20.231206Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-12","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T08:36:20.231452Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T08:36:20.231633Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T08:36:20.269113Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-12","position_count":0}
{"timestamp":"2025-10-30T08:36:20.269907Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-12","refreshed_count":0}
{"timestamp":"2025-10-30T08:36:20.273499Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-11","position_count":0}
{"timestamp":"2025-10-30T08:36:20.273985Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-11","refreshed_count":0}
{"timestamp":"2025-10-30T08:36:20.281570Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-10","position_count":0}
{"timestamp":"2025-10-30T08:36:20.282266Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-10","refreshed_count":0}
{"timestamp":"2025-10-30T08:36:20.550275Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 186.3 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-12","operation":"initialize","instrument":"MNQ","initial_days":5}
{"timestamp":"2025-10-30T08:36:20.584611Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 186.3 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-10","operation":"initialize","instrument":"MNQ","initial_days":5}
{"timestamp":"2025-10-30T08:36:20.620733Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 186.3 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-11","operation":"initialize","instrument":"MNQ","initial_days":5}
{"timestamp":"2025-10-30T08:36:20.646447Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 186.3 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-12","operation":"initialize","instrument":"MNQ","initial_days":5}
{"timestamp":"2025-10-30T08:36:20.647253Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-12"}
{"timestamp":"2025-10-30T08:36:20.650627Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-12","operation":"start_realtime_feed","instrument":"ES","contract_id":"CON.F.US.EP.Z25"}
{"timestamp":"2025-10-30T08:36:20.674942Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 186.3 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-10","operation":"start_realtime_feed","instrument":"ES","contract_id":"CON.F.US.EP.Z25"}
{"timestamp":"2025-10-30T08:36:20.675537Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-10"}
{"timestamp":"2025-10-30T08:36:20.723887Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 186.3 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-11","operation":"start_realtime_feed","instrument":"MNQ","contract_id":"CON.F.US.MNQ.Z25"}
{"timestamp":"2025-10-30T08:36:20.724348Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-11"}
{"timestamp":"2025-10-30T08:36:20.725007Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-10","operation":"start_realtime_feed","instrument":"MNQ","contract_id":"CON.F.US.MNQ.Z25"}
{"timestamp":"2025-10-30T08:36:20.727222Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-11","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T08:36:20.727637Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":853,"message":"TradingSuite initialization complete","taskName":"Task-1"}
2025-10-30 03:36:20 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ Connected to ProjectX (HTTP + WebSocket + TradingSuite)
Connected to TopstepX API!

Starting event loop...
2025-10-30 03:36:20 | INFO     | risk_manager.core.manager:start - Starting Risk Manager...
{"timestamp":"2025-10-30T08:36:20.730452Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"start","line":40,"message":"✅ Event loop running: 6 active rules monitoring events","taskName":"Task-1"}
2025-10-30 03:36:20 | INFO     | risk_manager.core.engine:start - Risk Engine started
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - Starting trading event monitoring...
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - Registering event callbacks via suite.on()...
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_PLACED
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_FILLED
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_PARTIAL_FILL
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_CANCELLED
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_REJECTED
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_MODIFIED
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_EXPIRED
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_OPENED
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_CLOSED
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_UPDATED
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - 📊 Registering market data event handlers...
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: QUOTE_UPDATE
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: DATA_UPDATE
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: TRADE_TICK
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: NEW_BAR (1min, 5min timeframes)
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - Checking instruments for price data...
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start -   ℹ️  MNQ - prices will come from QUOTE_UPDATE events
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start -   ℹ️  ENQ - prices will come from QUOTE_UPDATE events
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start -   ℹ️  ES - prices will come from QUOTE_UPDATE events
2025-10-30 03:36:20 | SUCCESS  | risk_manager.integrations.trading:start - ✅ Trading monitoring started (14 event handlers registered)
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - 📡 Listening for events: ORDER (8 types), POSITION (3 types), MARKET DATA (4 types)
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - 🔄 Started order polling task (5s interval)
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - 📊 Started unrealized P&L status bar (0.5s refresh)
2025-10-30 03:36:20 | INFO     | risk_manager.integrations.trading:start - ================================================================================
2025-10-30 03:36:20 | SUCCESS  | risk_manager.core.manager:start - ✅ Risk Manager ACTIVE - Protecting your capital!
Risk Manager is running!

Press Ctrl+C to stop

============================================================
                  LIVE EVENT FEED
============================================================

📊 Unrealized P&L: $+0.00  2025-10-30 03:36:35 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - MNQ BUY 1 @ $26,259.00
2025-10-30 03:36:35 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 03:36:35 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Event type matches! Processing EventType.ORDER_FILLED
2025-10-30 03:36:35 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    profitAndLoss from event data: None
2025-10-30 03:36:35 | WARNING  | risk_manager.rules.daily_realized_loss:evaluate -    ❌ No profitAndLoss in event data (half-turn trade or missing field)
2025-10-30 03:36:35 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:36:35 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:36:35 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:36:35 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:36:35 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:36:35 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:36:35 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:35 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION OPENED - MNQ LONG 1 @ $26,259.00 | P&L: $0.00
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:36 | WARNING  | risk_manager.integrations.trading:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_handle_position_event -   ℹ️  No take profit order
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:36 | INFO     | risk_manager.integrations.trading:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 1 | P&L: $0.00
📊 Unrealized P&L: $+0.75  2025-10-30 03:36:48 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - MNQ SELL 1 @ $26,258.75
2025-10-30 03:36:48 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 03:36:48 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Event type matches! Processing EventType.ORDER_FILLED
2025-10-30 03:36:48 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    profitAndLoss from event data: None
2025-10-30 03:36:48 | WARNING  | risk_manager.rules.daily_realized_loss:evaluate -    ❌ No profitAndLoss in event data (half-turn trade or missing field)
2025-10-30 03:36:48 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:36:48 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:36:48 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:36:48 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:36:48 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:36:48 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:36:48 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION CLOSED - MNQ FLAT 0 @ $26,259.00 | P&L: $0.00
2025-10-30 03:36:48 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:48 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:48 | INFO     | risk_manager.integrations.trading:_handle_position_event - 💰 Calculated P&L:
2025-10-30 03:36:48 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Entry: $26,259.00 @ 1 (long)
2025-10-30 03:36:48 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Exit: $26,258.75
2025-10-30 03:36:48 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Price diff: -0.25 = -1.0 ticks
2025-10-30 03:36:48 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Realized P&L: $-0.50
📊 Unrealized P&L: $+0.00  2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - MNQ BUY 4 @ $26,258.50
2025-10-30 03:36:51 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 03:36:51 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Event type matches! Processing EventType.ORDER_FILLED
2025-10-30 03:36:51 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    profitAndLoss from event data: None
2025-10-30 03:36:51 | WARNING  | risk_manager.rules.daily_realized_loss:evaluate -    ❌ No profitAndLoss in event data (half-turn trade or missing field)
2025-10-30 03:36:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:36:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:36:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:36:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:36:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:36:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION OPENED - MNQ LONG 4 @ $26,258.50 | P&L: $0.00
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:51 | WARNING  | risk_manager.integrations.trading:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_handle_position_event -   ℹ️  No take profit order
2025-10-30 03:36:51 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:52 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:36:52 | INFO     | risk_manager.integrations.trading:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 4 | P&L: $0.00
📊 Unrealized P&L: $-5.00  2025-10-30 03:36:53 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 03:36:53 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:36:53 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:36:53 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:36:53 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:36:53 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:36:53 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:36:53 | INFO     | risk_manager.integrations.trading:_on_quote_update - 💹 Unrealized P&L update: MNQ $-10.00
📊 Unrealized P&L: $-17.00  2025-10-30 03:36:58 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 03:36:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:36:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:36:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:36:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:36:58 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyUnrealizedLoss → FAIL (Daily unrealized loss limit exceeded: $-20.00 ≤ $-20.00)
2025-10-30 03:36:58 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyUnrealizedLoss - Daily unrealized loss limit exceeded: $-20.00 ≤ $-20.00
2025-10-30 03:36:58 | ERROR    | risk_manager.core.engine:_handle_violation - ❌ Cannot close position: Missing required fields! contractId=None, symbol=None, rule=DailyUnrealizedLoss
{"timestamp":"2025-10-30T08:36:58.431660Z","level":"ERROR","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":291,"message":"⚠️ Enforcement FAILED: Missing contract_id or symbol - Rule: DailyUnrealizedL
oss","taskName":"Task-4674"}
2025-10-30 03:36:58 | ERROR    | risk_manager.core.engine:evaluate_rules - Error evaluating rule DailyUnrealizedLossRule: close_position enforcement requires 'contractId' and 'symbol' in violation. Rule: DailyUnrealizedLoss, violation: {'rule': 'DailyUnrealizedLossRule', 'message': 'Daily unrealized loss limit exceeded: $-20.00 ≤ $-20.00', 'severity': 'CRITICAL', 'current_pnl': -20.0, 'limit': -20.0, 'action': 'close_position', 'timestamp': '2025-10-30T08:36:58.430816+00:00'}      
2025-10-30 03:36:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:36:58 | INFO     | risk_manager.integrations.trading:_on_quote_update - 💹 Unrealized P&L update: MNQ $-20.00
📊 Unrealized P&L: $-19.00  2025-10-30 03:36:59 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 03:36:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:36:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:36:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:36:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:36:59 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyUnrealizedLoss → FAIL (Daily unrealized loss limit exceeded: $-31.00 ≤ $-20.00)
2025-10-30 03:36:59 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyUnrealizedLoss - Daily unrealized loss limit exceeded: $-31.00 ≤ $-20.00
2025-10-30 03:36:59 | ERROR    | risk_manager.core.engine:_handle_violation - ❌ Cannot close position: Missing required fields! contractId=None, symbol=None, rule=DailyUnrealizedLoss
{"timestamp":"2025-10-30T08:36:59.238785Z","level":"ERROR","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":291,"message":"⚠️ Enforcement FAILED: Missing contract_id or symbol - Rule: DailyUnrealizedL
oss","taskName":"Task-4811"}
2025-10-30 03:36:59 | ERROR    | risk_manager.core.engine:evaluate_rules - Error evaluating rule DailyUnrealizedLossRule: close_position enforcement requires 'contractId' and 'symbol' in violation. Rule: DailyUnrealizedLoss, violation: {'rule': 'DailyUnrealizedLossRule', 'message': 'Daily unrealized loss limit exceeded: $-31.00 ≤ $-20.00', 'severity': 'CRITICAL', 'current_pnl': -31.0, 'limit': -20.0, 'action': 'close_position', 'timestamp': '2025-10-30T08:36:59.237882+00:00'}      
2025-10-30 03:36:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:36:59 | INFO     | risk_manager.integrations.trading:_on_quote_update - 💹 Unrealized P&L update: MNQ $-31.00
📊 Unrealized P&L: $-27.00  2025-10-30 03:37:02 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 03:37:02 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:37:02 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:37:02 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:37:02 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:37:02 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:37:02 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:37:02 | INFO     | risk_manager.integrations.trading:_on_quote_update - 💹 Unrealized P&L update: MNQ $-16.00
📊 Unrealized P&L: $-17.00  2025-10-30 03:37:03 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 03:37:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:37:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:37:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:37:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:37:03 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyUnrealizedLoss → FAIL (Daily unrealized loss limit exceeded: $-26.00 ≤ $-20.00)
2025-10-30 03:37:03 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyUnrealizedLoss - Daily unrealized loss limit exceeded: $-26.00 ≤ $-20.00
2025-10-30 03:37:03 | ERROR    | risk_manager.core.engine:_handle_violation - ❌ Cannot close position: Missing required fields! contractId=None, symbol=None, rule=DailyUnrealizedLoss
{"timestamp":"2025-10-30T08:37:03.732370Z","level":"ERROR","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":291,"message":"⚠️ Enforcement FAILED: Missing contract_id or symbol - Rule: DailyUnrealizedL
oss","taskName":"Task-5442"}
2025-10-30 03:37:03 | ERROR    | risk_manager.core.engine:evaluate_rules - Error evaluating rule DailyUnrealizedLossRule: close_position enforcement requires 'contractId' and 'symbol' in violation. Rule: DailyUnrealizedLoss, violation: {'rule': 'DailyUnrealizedLossRule', 'message': 'Daily unrealized loss limit exceeded: $-26.00 ≤ $-20.00', 'severity': 'CRITICAL', 'current_pnl': -26.0, 'limit': -20.0, 'action': 'close_position', 'timestamp': '2025-10-30T08:37:03.622805+00:00'}      
2025-10-30 03:37:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:37:03 | INFO     | risk_manager.integrations.trading:_on_quote_update - 💹 Unrealized P&L update: MNQ $-26.00
📊 Unrealized P&L: $-31.00  2025-10-30 03:37:06 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - MNQ SELL 4 @ $26,254.75
2025-10-30 03:37:06 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 03:37:06 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Event type matches! Processing EventType.ORDER_FILLED
2025-10-30 03:37:06 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    profitAndLoss from event data: None
2025-10-30 03:37:06 | WARNING  | risk_manager.rules.daily_realized_loss:evaluate -    ❌ No profitAndLoss in event data (half-turn trade or missing field)
2025-10-30 03:37:06 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:37:06 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:37:06 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:37:06 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:37:06 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:37:06 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:37:06 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION CLOSED - MNQ FLAT 0 @ $26,258.50 | P&L: $0.00
2025-10-30 03:37:06 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:37:06 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:37:06 | INFO     | risk_manager.integrations.trading:_handle_position_event - 💰 Calculated P&L:
2025-10-30 03:37:06 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Entry: $26,258.50 @ 4 (long)
2025-10-30 03:37:06 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Exit: $26,254.75
2025-10-30 03:37:06 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Price diff: -3.75 = -15.0 ticks
2025-10-30 03:37:06 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Realized P&L: $-30.00