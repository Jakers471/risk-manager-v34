p\risk-manager-v34> python run_dev.py

============================================================
        RISK MANAGER V34 - DEVELOPMENT MODE
============================================================

2025-10-30 14:19:07.798 | INFO     | risk_manager.cli.logger:setup_logging:166 - Logging initialized: console=INFO, file=DEBUG
2025-10-30 14:19:07.799 | INFO     | risk_manager.cli.logger:setup_logging:167 - Log file: C:\Users\jakers\Desktop\risk-manager-v34\data\logs\risk_manager.log
2025-10-30 14:19:07.799 | INFO     | __main__:main:126 - 🎛️  Console Log Level: INFO
2025-10-30 14:19:07.800 | INFO     | __main__:main:128 - 💡 Tip: Use --log-level DEBUG to see detailed order payloads
2025-10-30 14:19:07.800 | INFO     | risk_manager.cli.logger:log_checkpoint:208 - 🚀 [CHECKPOINT 1] Service Start | version=1.0.0-dev | mode=development
{"timestamp":"2025-10-30T19:19:07.801123Z","level":"INFO","logger":"risk_manager.checkpoints","module":"logger","function":"log_checkpoint","line":213,"message":"🚀 [CHECKPOINT 1] Service Start | version=1.0.0-dev | mode=development","taskName":"Task-1"}
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
2025-10-30 14:19:07.836 | INFO     | risk_manager.core.engine:__init__:33 - Risk Engine initialized
{"timestamp":"2025-10-30T19:19:07.839917Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"__init__","line":48,"message":"🚀 Risk Manager starting...","taskName":"Task-1"}
2025-10-30 14:19:07 | INFO     | risk_manager.core.manager:__init__ - Risk Manager initialized
{"timestamp":"2025-10-30T19:19:07.840626Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"create","line":133,"message":"✅ Config loaded: 0 custom rules, monitoring 0 instruments","taskName":"Task-1"}        
2025-10-30 14:19:07 | INFO     | risk_manager.state.database:__init__ - Database initialized at data\risk_state.db
2025-10-30 14:19:07 | INFO     | risk_manager.state.timer_manager:__init__ - TimerManager initialized
2025-10-30 14:19:07 | INFO     | risk_manager.state.pnl_tracker:__init__ - PnLTracker initialized
2025-10-30 14:19:07 | INFO     | risk_manager.state.lockout_manager:load_lockouts_from_db - Loaded 0 lockouts from database
2025-10-30 14:19:07 | INFO     | risk_manager.state.lockout_manager:__init__ - Lockout Manager initialized
2025-10-30 14:19:07 | INFO     | risk_manager.rules.daily_realized_loss:__init__ - DailyRealizedLossRule initialized: limit=$-5.00, reset=17:00 America/New_York
2025-10-30 14:19:07 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedLossRule
2025-10-30 14:19:07 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedLossRule (limit=$-5.0)
2025-10-30 14:19:07 | INFO     | risk_manager.rules.daily_realized_profit:__init__ - DailyRealizedProfitRule initialized: target=$1000.00, reset=17:00 America/New_York
2025-10-30 14:19:07 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedProfitRule
2025-10-30 14:19:07 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedProfitRule (target=$1000.0)
2025-10-30 14:19:07 | INFO     | risk_manager.rules.max_contracts_per_instrument:__init__ - MaxContractsPerInstrumentRule initialized - Limits: {'MNQ': 2, 'ES': 1}, Enforcement: reduce_to_limit, Unknown: allow_with_limit:3
2025-10-30 14:19:07 | INFO     | risk_manager.core.engine:add_rule - Added rule: MaxContractsPerInstrumentRule
2025-10-30 14:19:07 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: MaxContractsPerInstrumentRule (2 symbols)
2025-10-30 14:19:07 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ TradeFrequencyLimitRule requires timers_config.yaml (skipped)
2025-10-30 14:19:07 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ CooldownAfterLossRule requires timers_config.yaml (skipped)
2025-10-30 14:19:07 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ SessionBlockOutsideRule requires timers_config.yaml (skipped)
2025-10-30 14:19:07 | INFO     | risk_manager.core.engine:add_rule - Added rule: AuthLossGuardRule
2025-10-30 14:19:07 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: AuthLossGuardRule
2025-10-30 14:19:07 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyUnrealizedLossRule
2025-10-30 14:19:07 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyUnrealizedLossRule (limit=$-20.0)
2025-10-30 14:19:07 | INFO     | risk_manager.core.engine:add_rule - Added rule: MaxUnrealizedProfitRule
2025-10-30 14:19:07 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: MaxUnrealizedProfitRule (target=$20.0)
2025-10-30 14:19:07 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ 3 rules skipped (require additional configuration)
2025-10-30 14:19:07 | WARNING  | risk_manager.core.manager:_add_default_rules -    TradeManagement rule requires bracket order configuration
2025-10-30 14:19:07 | WARNING  | risk_manager.core.manager:_add_default_rules -    Timer-based rules require timers_config.yaml
{"timestamp":"2025-10-30T19:19:07.878595Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"_add_default_rules","line":515,"message":"✅ Rules initialized: 6 rules loaded from configuration","taskName":"Task-1"
}
2025-10-30 14:19:07 | INFO     | risk_manager.core.manager:_add_default_rules - Loaded 6/9 enabled rules
2025-10-30 14:19:07 | INFO     | risk_manager.core.manager:create - Risk Manager created for instruments: None
Risk Manager initialized!

Connecting to TopstepX API...
  Username: jakertrader
  Account: PRAC-V2-126244-84184528
2025-10-30 14:19:07 | INFO     | risk_manager.integrations.trading:__init__ - Trading integration initialized for: ['MNQ', 'ENQ', 'ES']
2025-10-30 14:19:07 | INFO     | risk_manager.integrations.trading:connect - Connecting to ProjectX trading platform...
2025-10-30 14:19:07 | INFO     | risk_manager.integrations.trading:connect - Step 1: Authenticating via HTTP API...
2025-10-30 14:19:09 | INFO     | risk_manager.integrations.trading:connect - ✅ Authenticated: PRAC-V2-126244-84184528 (ID: 13298777)
2025-10-30 14:19:09 | INFO     | risk_manager.integrations.trading:connect -    Balance: $146,056.08, Trading: True
2025-10-30 14:19:09 | INFO     | risk_manager.integrations.trading:connect - Step 2: Establishing SignalR WebSocket connection...
{"timestamp":"2025-10-30T19:19:09.044105Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T19:19:20.093517Z","level":"ERROR","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"connect","line":316,"message":"WebSocket error","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
2025-10-30 14:19:20 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ SignalR WebSocket connected (User Hub + Market Hub)
2025-10-30 14:19:20 | INFO     | risk_manager.integrations.trading:connect - Step 3: Initializing TradingSuite...
{"timestamp":"2025-10-30T19:19:20.752059Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-5"}
{"timestamp":"2025-10-30T19:19:20.828452Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-5"}
{"timestamp":"2025-10-30T19:19:20.828846Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-5"}
{"timestamp":"2025-10-30T19:19:20.829060Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-5","instrument":"MNQ"}
{"timestamp":"2025-10-30T19:19:20.829426Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-5"}
{"timestamp":"2025-10-30T19:19:20.829744Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-5","manager":"PositionManager"}
{"timestamp":"2025-10-30T19:19:20.831546Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-6"}
{"timestamp":"2025-10-30T19:19:20.831875Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-6"}
{"timestamp":"2025-10-30T19:19:20.832107Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-6"}    
{"timestamp":"2025-10-30T19:19:20.832318Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-6","instrument":"ENQ"}
{"timestamp":"2025-10-30T19:19:20.832605Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-6"}
{"timestamp":"2025-10-30T19:19:20.832824Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-6","manager":"PositionManager"}
{"timestamp":"2025-10-30T19:19:20.834011Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-7"}
{"timestamp":"2025-10-30T19:19:20.834323Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-7"}
{"timestamp":"2025-10-30T19:19:20.834643Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-7"}    
{"timestamp":"2025-10-30T19:19:20.834845Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-7","instrument":"ES"}
{"timestamp":"2025-10-30T19:19:20.835119Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-7"}
{"timestamp":"2025-10-30T19:19:20.835346Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-7","manager":"PositionManager"}
{"timestamp":"2025-10-30T19:19:20.835676Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"__init__","line":443,"message":"TradingSuite created for ['MNQ', 'ENQ', 'ES'] with features: [<Features.PERFORMANCE_ANALYTICS: 'performance_analytics'>, <Features.AUTO_RECONNECT: 'auto_reconnect'>]","taskName":"Task-1"}
{"timestamp":"2025-10-30T19:19:20.835963Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":840,"message":"Connecting to real-time feeds...","taskName":"Task-1"}
{"timestamp":"2025-10-30T19:19:20.836202Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T19:19:31.939866Z","level":"ERROR","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"connect","line":316,"message":"WebSocket error","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T19:19:31.947085Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-10"}
{"timestamp":"2025-10-30T19:19:31.947999Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-10
"}
{"timestamp":"2025-10-30T19:19:31.949199Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-10"}{"timestamp":"2025-10-30T19:19:31.950613Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-11"}     
{"timestamp":"2025-10-30T19:19:31.952053Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-11
"}
{"timestamp":"2025-10-30T19:19:31.953182Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-11"}{"timestamp":"2025-10-30T19:19:31.954376Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-12"}     
{"timestamp":"2025-10-30T19:19:31.955619Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-12
"}
{"timestamp":"2025-10-30T19:19:31.957305Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-12"}{"timestamp":"2025-10-30T19:19:31.969187Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-10"}
{"timestamp":"2025-10-30T19:19:31.971744Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-10","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T19:19:31.973917Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-10","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T19:19:31.975589Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T19:19:31.980945Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T19:19:31.983349Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-11"}
{"timestamp":"2025-10-30T19:19:31.984027Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-11","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T19:19:31.984724Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-11","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T19:19:31.985442Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T19:19:31.986188Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T19:19:31.987504Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-12"}
{"timestamp":"2025-10-30T19:19:31.988340Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-12","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T19:19:31.988979Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-12","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T19:19:31.989449Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T19:19:31.989783Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T19:19:32.033521Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-10","position_count":0}
{"timestamp":"2025-10-30T19:19:32.033813Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-10","refreshed_count":0}
{"timestamp":"2025-10-30T19:19:32.034963Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-12","position_count":0}
{"timestamp":"2025-10-30T19:19:32.035149Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-12","refreshed_count":0}
{"timestamp":"2025-10-30T19:19:32.037798Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-11","position_count":0}
{"timestamp":"2025-10-30T19:19:32.037987Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-11","refreshed_count":0}
{"timestamp":"2025-10-30T19:19:32.278540Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 829.5 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-12","operation":"initialize","instrument":"ENQ","initial_days":5}
{"timestamp":"2025-10-30T19:19:32.324768Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 829.5 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-10","operation":"initialize","instrument":"ENQ","initial_days":5}
{"timestamp":"2025-10-30T19:19:32.352189Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 829.5 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-11","operation":"initialize","instrument":"ENQ","initial_days":5}
{"timestamp":"2025-10-30T19:19:32.405519Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 829.5 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-12","operation":"initialize","instrument":"ENQ","initial_days":5}
{"timestamp":"2025-10-30T19:19:32.406097Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-12"}
{"timestamp":"2025-10-30T19:19:32.413502Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-12","operation":"start_realtime_feed","instrument":"ES","contract_id":"CON.F.US.EP.Z25"}
{"timestamp":"2025-10-30T19:19:32.426238Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 829.5 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-10","operation":"start_realtime_feed","instrument":"ES","contract_id":"CON.F.US.EP.Z25"}
{"timestamp":"2025-10-30T19:19:32.427092Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-10"}
{"timestamp":"2025-10-30T19:19:32.454432Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 829.5 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-11","operation":"start_realtime_feed","instrument":"MNQ","contract_id":"CON.F.US.MNQ.Z25"}
{"timestamp":"2025-10-30T19:19:32.454988Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-11"}
{"timestamp":"2025-10-30T19:19:32.489052Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-10","operation":"start_realtime_feed","instrument":"MNQ","contract_id":"CON.F.US.MNQ.Z25"}
{"timestamp":"2025-10-30T19:19:32.541227Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-11","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:19:32.542102Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":853,"message":"TradingSuite initialization complete","taskName":"Task-1"}
2025-10-30 14:19:32 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ Connected to ProjectX (HTTP + WebSocket + TradingSuite)
Connected to TopstepX API!

Starting event loop...
2025-10-30 14:19:32 | INFO     | risk_manager.core.manager:start - Starting Risk Manager...
{"timestamp":"2025-10-30T19:19:32.545679Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"start","line":40,"message":"✅ Event loop running: 6 active rules monitoring events","taskName":"Task-1"}
2025-10-30 14:19:32 | INFO     | risk_manager.core.engine:start - Risk Engine started
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - Starting trading event monitoring...
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - Registering event callbacks via suite.on() → EventRouter...
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_PLACED → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_FILLED → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_PARTIAL_FILL → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_CANCELLED → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_REJECTED → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_MODIFIED → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_EXPIRED → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_OPENED → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_CLOSED → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_UPDATED → EventRouter
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - 📊 Registering market data event handlers...
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: QUOTE_UPDATE (MarketDataHandler)
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: DATA_UPDATE (MarketDataHandler)
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: TRADE_TICK (MarketDataHandler)
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: NEW_BAR (1min, 5min timeframes - MarketDataHandler)
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - Checking instruments for price data...
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start -   ℹ️  MNQ - prices will come from QUOTE_UPDATE events
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start -   ℹ️  ENQ - prices will come from QUOTE_UPDATE events
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start -   ℹ️  ES - prices will come from QUOTE_UPDATE events
2025-10-30 14:19:32 | SUCCESS  | risk_manager.integrations.trading:start - ✅ Trading monitoring started (14 event handlers registered)
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - 📡 Listening for events: ORDER (8 types), POSITION (3 types), MARKET DATA (4 types)
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - 🔄 Started order polling task (5s interval - OrderPollingService)
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - 📊 Started unrealized P&L status bar (0.5s refresh - MarketDataHandler)
2025-10-30 14:19:32 | INFO     | risk_manager.integrations.trading:start - ================================================================================
2025-10-30 14:19:32 | SUCCESS  | risk_manager.core.manager:start - ✅ Risk Manager ACTIVE - Protecting your capital!
Risk Manager is running!

Press Ctrl+C to stop

============================================================
                  LIVE EVENT FEED
============================================================

📊 Unrealized P&L: $+0.00  2025-10-30 14:19:41 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ BUY 1 @ $25,935.50
2025-10-30 14:19:41 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 14:19:41 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:19:41 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:19:41 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:19:41 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:19:41 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:19:41 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
📊 Unrealized P&L: $+0.00  2025-10-30 14:19:42 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION OPENED - MNQ LONG 1 @ $25,935.50 | P&L: $0.00
📊 Unrealized P&L: $+0.00  2025-10-30 14:19:42 | WARNING  | risk_manager.integrations.sdk.event_router:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-30 14:19:42 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   ℹ️  No take profit order
2025-10-30 14:19:42 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 1 | P&L: $0.00
2025-10-30 14:19:42 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_opened → evaluating 6 rules
2025-10-30 14:19:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:19:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:19:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS (MNQ: 1/2 max)
2025-10-30 14:19:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:19:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:19:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
📊 Unrealized P&L: $+1.25  2025-10-30 14:19:48 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION UPDATED - MNQ LONG 1 @ $25,935.50 | P&L: $0.00
2025-10-30 14:19:48 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🛡️  Stop Loss: $25,910.50
2025-10-30 14:19:48 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   ℹ️  No take profit order
2025-10-30 14:19:49 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 1 | P&L: $0.00
2025-10-30 14:19:49 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_updated → evaluating 6 rules
2025-10-30 14:19:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:19:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:19:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS (MNQ: 1/2 max)
2025-10-30 14:19:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:19:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:19:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
📊 Unrealized P&L: $+7.50  2025-10-30 14:19:51 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:19:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:19:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:19:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:19:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:19:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:19:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:19:51 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $+13.25
📊 Unrealized P&L: $+11.50  2025-10-30 14:19:56 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION UPDATED - MNQ LONG 1 @ $25,935.50 | P&L: $0.00
2025-10-30 14:19:56 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🛡️  Stop Loss: $25,910.50
2025-10-30 14:19:56 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🎯 Take Profit: $25,982.50
2025-10-30 14:19:56 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 1 | P&L: $0.00
2025-10-30 14:19:56 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_updated → evaluating 6 rules
2025-10-30 14:19:56 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:19:56 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:19:56 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS (MNQ: 1/2 max)
2025-10-30 14:19:56 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:19:56 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:19:56 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
📊 Unrealized P&L: $+5.50  2025-10-30 14:20:01 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:20:01 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:01 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:01 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:01 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:01 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:01 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:01 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $+3.00
📊 Unrealized P&L: $-4.25  2025-10-30 14:20:03 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:20:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:03 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $-7.00
📊 Unrealized P&L: $-13.50  2025-10-30 14:20:17 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:20:17 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:17 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:17 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:17 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:17 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:17 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:17 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $-17.25
📊 Unrealized P&L: $-17.25  2025-10-30 14:20:36 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ SELL 1 @ $25,926.50
2025-10-30 14:20:36 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 14:20:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:36 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_cancelled - ❌ ORDER CANCELLED - MNQ | ID: 1826119825
2025-10-30 14:20:36 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_cancelled - ❌ ORDER CANCELLED - MNQ | ID: 1826120284
2025-10-30 14:20:36 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION CLOSED - MNQ FLAT 0 @ $25,935.50 | P&L: $0.00
2025-10-30 14:20:36 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 💰 Realized P&L: $-18.00
2025-10-30 14:20:36 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_closed → evaluating 6 rules
2025-10-30 14:20:36 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Event type matches! Processing EventType.POSITION_CLOSED
2025-10-30 14:20:36 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    profitAndLoss from event data: -18.0
2025-10-30 14:20:36 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Have profitAndLoss: $-18.00, updating tracker...
2025-10-30 14:20:36 | INFO     | risk_manager.rules.daily_realized_loss:evaluate - 💰 Daily P&L: $-144.50 / $-5.00 limit (this trade: $-18.00)
2025-10-30 14:20:36 | WARNING  | risk_manager.rules.daily_realized_loss:evaluate - Daily loss limit breached for account 13298777: P&L=$-144.50, Limit=$-5.00
2025-10-30 14:20:36 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyRealizedLoss → FAIL (P&L: $-144.50 / $-5.00 limit)
2025-10-30 14:20:36 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyRealizedLoss - Daily loss limit exceeded: $-144.50 (limit: $-5.00)
2025-10-30 14:20:36 | CRITICAL | risk_manager.core.engine:_handle_violation - 🛑 ENFORCING: Closing all positions (DailyRealizedLoss)
{"timestamp":"2025-10-30T19:20:36.522582Z","level":"WARNING","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":278,"message":"⚠️ Enforcement triggered: FLATTEN ALL - Rule: DailyRealizedLoss","taskName"
:"Task-26872"}
2025-10-30 14:20:36 | WARNING  | risk_manager.core.engine:flatten_all_positions - Flattening all positions...
2025-10-30 14:20:36 | WARNING  | risk_manager.integrations.trading:flatten_all - FLATTENING ALL POSITIONS
2025-10-30 14:20:36 | WARNING  | risk_manager.integrations.trading:flatten_position - Flattening position for MNQ
📊 Unrealized P&L: $+0.00  2025-10-30 14:20:42 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ BUY 5 @ $25,924.50
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:42 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION OPENED - MNQ LONG 5 @ $25,924.50 | P&L: $0.00
2025-10-30 14:20:42 | WARNING  | risk_manager.integrations.sdk.event_router:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-30 14:20:42 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   ℹ️  No take profit order
2025-10-30 14:20:42 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 5 | P&L: $0.00
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_opened → evaluating 6 rules
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:42 | WARNING  | risk_manager.rules.max_contracts_per_instrument:evaluate - ⚠️ RULE-002 BREACH: MNQ position size 5 exceeds limit 2
2025-10-30 14:20:42 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: MaxContractsPerInstrument → FAIL (MNQ position size 5 exceeds limit 2)
2025-10-30 14:20:42 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: MaxContractsPerInstrument - MNQ position size 5 exceeds limit 2
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:42 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
📊 Unrealized P&L: $-7.50  2025-10-30 14:20:44 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:20:44 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:44 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:44 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:44 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:44 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:44 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:44 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $+10.00
📊 Unrealized P&L: $+10.00  2025-10-30 14:20:46 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ SELL 5 @ $25,925.50
2025-10-30 14:20:46 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 14:20:46 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:46 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:46 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:46 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:46 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:46 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:46 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION CLOSED - MNQ FLAT 0 @ $25,924.50 | P&L: $0.00
2025-10-30 14:20:46 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 💰 Realized P&L: $+10.00
2025-10-30 14:20:46 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_closed → evaluating 6 rules
2025-10-30 14:20:46 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Event type matches! Processing EventType.POSITION_CLOSED
2025-10-30 14:20:46 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    profitAndLoss from event data: 10.0
2025-10-30 14:20:46 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Have profitAndLoss: $+10.00, updating tracker...
2025-10-30 14:20:46 | INFO     | risk_manager.rules.daily_realized_loss:evaluate - 💰 Daily P&L: $-134.50 / $-5.00 limit (this trade: $+10.00)
2025-10-30 14:20:46 | WARNING  | risk_manager.rules.daily_realized_loss:evaluate - Daily loss limit breached for account 13298777: P&L=$-134.50, Limit=$-5.00
2025-10-30 14:20:46 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyRealizedLoss → FAIL (P&L: $-134.50 / $-5.00 limit)
2025-10-30 14:20:46 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyRealizedLoss - Daily loss limit exceeded: $-134.50 (limit: $-5.00)
2025-10-30 14:20:46 | CRITICAL | risk_manager.core.engine:_handle_violation - 🛑 ENFORCING: Closing all positions (DailyRealizedLoss)
{"timestamp":"2025-10-30T19:20:46.589899Z","level":"WARNING","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":278,"message":"⚠️ Enforcement triggered: FLATTEN ALL - Rule: DailyRealizedLoss","taskName"
:"Task-31140"}
2025-10-30 14:20:46 | WARNING  | risk_manager.core.engine:flatten_all_positions - Flattening all positions...
2025-10-30 14:20:46 | WARNING  | risk_manager.integrations.trading:flatten_all - FLATTENING ALL POSITIONS
2025-10-30 14:20:46 | WARNING  | risk_manager.integrations.trading:flatten_position - Flattening position for MNQ
📊 Unrealized P&L: $+0.00  2025-10-30 14:20:50 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ BUY 4 @ $25,925.50
2025-10-30 14:20:50 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 14:20:50 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:50 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:50 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:50 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:50 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:50 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:51 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION OPENED - MNQ LONG 4 @ $25,925.50 | P&L: $0.00
2025-10-30 14:20:51 | WARNING  | risk_manager.integrations.sdk.event_router:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-30 14:20:51 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   ℹ️  No take profit order
2025-10-30 14:20:51 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 4 | P&L: $0.00
2025-10-30 14:20:51 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_opened → evaluating 6 rules
2025-10-30 14:20:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:51 | WARNING  | risk_manager.rules.max_contracts_per_instrument:evaluate - ⚠️ RULE-002 BREACH: MNQ position size 4 exceeds limit 2
2025-10-30 14:20:51 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: MaxContractsPerInstrument → FAIL (MNQ position size 4 exceeds limit 2)
2025-10-30 14:20:51 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: MaxContractsPerInstrument - MNQ position size 4 exceeds limit 2
2025-10-30 14:20:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:51 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
📊 Unrealized P&L: $-1.00  2025-10-30 14:20:55 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:20:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:20:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:55 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $-10.00
📊 Unrealized P&L: $-16.00  2025-10-30 14:20:58 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:20:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:20:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:20:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:20:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:20:58 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyUnrealizedLoss → FAIL (Daily unrealized loss limit exceeded: $-20.00 ≤ $-20.00)
2025-10-30 14:20:58 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyUnrealizedLoss - Daily unrealized loss limit exceeded: $-20.00 ≤ $-20.00
2025-10-30 14:20:58 | ERROR    | risk_manager.core.engine:_handle_violation - ❌ Cannot close position: Missing required fields! contractId=None, symbol=None, rule=DailyUnrealizedLoss
{"timestamp":"2025-10-30T19:20:58.491511Z","level":"ERROR","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":291,"message":"⚠️ Enforcement FAILED: Missing contract_id or symbol - Rule: DailyUnrealizedL
oss","taskName":"Task-35319"}
2025-10-30 14:20:58 | ERROR    | risk_manager.core.engine:evaluate_rules - Error evaluating rule DailyUnrealizedLossRule: close_position enforcement requires 'contractId' and 'symbol' in violation. Rule: DailyUnrealizedLoss, violation: {'rule': 'DailyUnrealizedLossRule', 'message': 'Daily unrealized loss limit exceeded: $-20.00 ≤ $-20.00', 'severity': 'CRITICAL', 'current_pnl': -20.0, 'limit': -20.0, 'action': 'close_position', 'timestamp': '2025-10-30T19:20:58.490545+00:00'}      
2025-10-30 14:20:58 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:20:58 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $-20.00
📊 Unrealized P&L: $-24.00  2025-10-30 14:21:04 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:21:04 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:21:04 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:21:04 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:21:04 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:21:04 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyUnrealizedLoss → FAIL (Daily unrealized loss limit exceeded: $-30.00 ≤ $-20.00)
2025-10-30 14:21:04 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyUnrealizedLoss - Daily unrealized loss limit exceeded: $-30.00 ≤ $-20.00
2025-10-30 14:21:04 | ERROR    | risk_manager.core.engine:_handle_violation - ❌ Cannot close position: Missing required fields! contractId=None, symbol=None, rule=DailyUnrealizedLoss
{"timestamp":"2025-10-30T19:21:04.944035Z","level":"ERROR","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":291,"message":"⚠️ Enforcement FAILED: Missing contract_id or symbol - Rule: DailyUnrealizedL
oss","taskName":"Task-38019"}
2025-10-30 14:21:04 | ERROR    | risk_manager.core.engine:evaluate_rules - Error evaluating rule DailyUnrealizedLossRule: close_position enforcement requires 'contractId' and 'symbol' in violation. Rule: DailyUnrealizedLoss, violation: {'rule': 'DailyUnrealizedLossRule', 'message': 'Daily unrealized loss limit exceeded: $-30.00 ≤ $-20.00', 'severity': 'CRITICAL', 'current_pnl': -30.0, 'limit': -20.0, 'action': 'close_position', 'timestamp': '2025-10-30T19:21:04.943136+00:00'}      
2025-10-30 14:21:04 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:21:04 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $-30.00
📊 Unrealized P&L: $-36.00  2025-10-30 14:21:08 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:21:08 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:21:08 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:21:08 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:21:08 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:21:08 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyUnrealizedLoss → FAIL (Daily unrealized loss limit exceeded: $-41.00 ≤ $-20.00)
2025-10-30 14:21:08 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyUnrealizedLoss - Daily unrealized loss limit exceeded: $-41.00 ≤ $-20.00
2025-10-30 14:21:08 | ERROR    | risk_manager.core.engine:_handle_violation - ❌ Cannot close position: Missing required fields! contractId=None, symbol=None, rule=DailyUnrealizedLoss
{"timestamp":"2025-10-30T19:21:08.092671Z","level":"ERROR","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":291,"message":"⚠️ Enforcement FAILED: Missing contract_id or symbol - Rule: DailyUnrealizedL
oss","taskName":"Task-39205"}
2025-10-30 14:21:08 | ERROR    | risk_manager.core.engine:evaluate_rules - Error evaluating rule DailyUnrealizedLossRule: close_position enforcement requires 'contractId' and 'symbol' in violation. Rule: DailyUnrealizedLoss, violation: {'rule': 'DailyUnrealizedLossRule', 'message': 'Daily unrealized loss limit exceeded: $-41.00 ≤ $-20.00', 'severity': 'CRITICAL', 'current_pnl': -41.0, 'limit': -20.0, 'action': 'close_position', 'timestamp': '2025-10-30T19:21:08.091634+00:00'}      
2025-10-30 14:21:08 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:21:08 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $-41.00
📊 Unrealized P&L: $-38.00  2025-10-30 14:21:10 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:21:10 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:21:10 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:21:10 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:21:10 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:21:10 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyUnrealizedLoss → FAIL (Daily unrealized loss limit exceeded: $-30.00 ≤ $-20.00)
2025-10-30 14:21:10 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyUnrealizedLoss - Daily unrealized loss limit exceeded: $-30.00 ≤ $-20.00
2025-10-30 14:21:10 | ERROR    | risk_manager.core.engine:_handle_violation - ❌ Cannot close position: Missing required fields! contractId=None, symbol=None, rule=DailyUnrealizedLoss
{"timestamp":"2025-10-30T19:21:10.866261Z","level":"ERROR","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":291,"message":"⚠️ Enforcement FAILED: Missing contract_id or symbol - Rule: DailyUnrealizedL
oss","taskName":"Task-40391"}
2025-10-30 14:21:10 | ERROR    | risk_manager.core.engine:evaluate_rules - Error evaluating rule DailyUnrealizedLossRule: close_position enforcement requires 'contractId' and 'symbol' in violation. Rule: DailyUnrealizedLoss, violation: {'rule': 'DailyUnrealizedLossRule', 'message': 'Daily unrealized loss limit exceeded: $-30.00 ≤ $-20.00', 'severity': 'CRITICAL', 'current_pnl': -30.0, 'limit': -20.0, 'action': 'close_position', 'timestamp': '2025-10-30T19:21:10.865136+00:00'}      
2025-10-30 14:21:10 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:21:10 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $-30.00
📊 Unrealized P&L: $-21.00  2025-10-30 14:21:11 | INFO     | risk_manager.integrations.sdk.event_router:_on_order_filled - 💰 ORDER FILLED - MNQ SELL 4 @ $25,922.75
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:21:11 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 📊 POSITION CLOSED - MNQ FLAT 0 @ $25,925.50 | P&L: $0.00
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 14:21:11 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyUnrealizedLoss → FAIL (Daily unrealized loss limit exceeded: $-20.00 ≤ $-20.00)
2025-10-30 14:21:11 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyUnrealizedLoss - Daily unrealized loss limit exceeded: $-20.00 ≤ $-20.00
2025-10-30 14:21:11 | ERROR    | risk_manager.core.engine:_handle_violation - ❌ Cannot close position: Missing required fields! contractId=None, symbol=None, rule=DailyUnrealizedLoss
{"timestamp":"2025-10-30T19:21:11.709435Z","level":"ERROR","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":291,"message":"⚠️ Enforcement FAILED: Missing contract_id or symbol - Rule: DailyUnrealizedL
oss","taskName":"Task-40801"}
2025-10-30 14:21:11 | ERROR    | risk_manager.core.engine:evaluate_rules - Error evaluating rule DailyUnrealizedLossRule: close_position enforcement requires 'contractId' and 'symbol' in violation. Rule: DailyUnrealizedLoss, violation: {'rule': 'DailyUnrealizedLossRule', 'message': 'Daily unrealized loss limit exceeded: $-20.00 ≤ $-20.00', 'severity': 'CRITICAL', 'current_pnl': -20.0, 'limit': -20.0, 'action': 'close_position', 'timestamp': '2025-10-30T19:21:11.706680+00:00'}      
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 14:21:11 | INFO     | risk_manager.integrations.sdk.market_data:handle_quote_update - 💹 Unrealized P&L update: MNQ $-20.00
2025-10-30 14:21:11 | INFO     | risk_manager.integrations.sdk.event_router:_handle_position_event - 💰 Realized P&L: $-22.00
2025-10-30 14:21:11 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_closed → evaluating 6 rules
2025-10-30 14:21:11 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Event type matches! Processing EventType.POSITION_CLOSED
2025-10-30 14:21:11 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    profitAndLoss from event data: -22.0
2025-10-30 14:21:11 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Have profitAndLoss: $-22.00, updating tracker...
2025-10-30 14:21:11 | INFO     | risk_manager.rules.daily_realized_loss:evaluate - 💰 Daily P&L: $-156.50 / $-5.00 limit (this trade: $-22.00)
2025-10-30 14:21:11 | WARNING  | risk_manager.rules.daily_realized_loss:evaluate - Daily loss limit breached for account 13298777: P&L=$-156.50, Limit=$-5.00
2025-10-30 14:21:11 | WARNING  | risk_manager.core.engine:evaluate_rules - ❌ Rule: DailyRealizedLoss → FAIL (P&L: $-156.50 / $-5.00 limit)
2025-10-30 14:21:11 | CRITICAL | risk_manager.core.engine:_handle_violation - 🚨 VIOLATION: DailyRealizedLoss - Daily loss limit exceeded: $-156.50 (limit: $-5.00)
2025-10-30 14:21:11 | CRITICAL | risk_manager.core.engine:_handle_violation - 🛑 ENFORCING: Closing all positions (DailyRealizedLoss)
{"timestamp":"2025-10-30T19:21:11.910259Z","level":"WARNING","logger":"risk_manager.core.engine","module":"engine","function":"_handle_violation","line":278,"message":"⚠️ Enforcement triggered: FLATTEN ALL - Rule: DailyRealizedLoss","taskName"
:"Task-40783"}
2025-10-30 14:21:11 | WARNING  | risk_manager.core.engine:flatten_all_positions - Flattening all positions...
2025-10-30 14:21:11 | WARNING  | risk_manager.integrations.trading:flatten_all - FLATTENING ALL POSITIONS
2025-10-30 14:21:11 | WARNING  | risk_manager.integrations.trading:flatten_position - Flattening position for MNQ
📊 Unrealized P&L: $+0.00  
Shutdown signal received...

Shutting down gracefully...
2025-10-30 14:21:19 | INFO     | risk_manager.core.manager:stop - Stopping Risk Manager...
2025-10-30 14:21:19 | INFO     | risk_manager.core.engine:stop - Risk Engine stopped
2025-10-30 14:21:19 | INFO     | risk_manager.integrations.trading:disconnect - Disconnecting from trading platform...

{"timestamp":"2025-10-30T19:21:19.726816Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"disconnect","line":983,"message":"Disconnecting TradingSuite...","taskName":"Task-1"}
{"timestamp":"2025-10-30T19:21:19.728015Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"stop_realtime_feed","line":1112,"message":"📉 Unsubscribing from CON.F.US.MNQ.Z25","taskName":"Task-44738","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.728760Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"stop_realtime_feed","line":1112,"message":"📉 Unsubscribing from CON.F.US.ENQ.Z25","taskName":"Task-44739","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.729487Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"stop_realtime_feed","line":1112,"message":"📉 Unsubscribing from CON.F.US.EP.Z25","taskName":"Task-44740","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.734024Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"stop_realtime_feed","line":1124,"message":"✅ Real-time feed stopped for ENQ","taskName":"
Task-44739","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.738693Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"stop_realtime_feed","line":1124,"message":"✅ Real-time feed stopped for MNQ","taskName":"
Task-44738","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.746988Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"stop_realtime_feed","line":1124,"message":"✅ Real-time feed stopped for ES","taskName":"T
ask-44740","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.757331Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"stop","line":557,"message":"Cleanup scheduler stopped","taskName":"Task-44739"}
{"timestamp":"2025-10-30T19:21:19.758288Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"bounded_statistics","function":"cleanup_bounded_statistics","line":926,"message":"Bounded statistics cleanup completed","taskName":"Task-44739","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.761057Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"cleanup","line":1177,"message":"✅ RealtimeDataManager cleanup completed","taskName":"Task
-44739","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.761982Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"stop","line":557,"message":"Cleanup scheduler stopped","taskName":"Task-44738"}
{"timestamp":"2025-10-30T19:21:19.762902Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"bounded_statistics","function":"cleanup_bounded_statistics","line":926,"message":"Bounded statistics cleanup completed","taskName":"Task-44738","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.765779Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"cleanup","line":1177,"message":"✅ RealtimeDataManager cleanup completed","taskName":"Task
-44738","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.767324Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"stop","line":557,"message":"Cleanup scheduler stopped","taskName":"Task-44740"}
{"timestamp":"2025-10-30T19:21:19.768110Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"bounded_statistics","function":"cleanup_bounded_statistics","line":926,"message":"Bounded statistics cleanup completed","taskName":"Task-44740","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.770144Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"cleanup","line":1177,"message":"✅ RealtimeDataManager cleanup completed","taskName":"Task
-44740","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
❌ User hub disconnected
❌ Market hub disconnected
{"timestamp":"2025-10-30T19:21:19.836054Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"disconnect","line":1006,"message":"TradingSuite disconnected","taskName":"Task-1"}
2025-10-30 14:21:19 | SUCCESS  | risk_manager.integrations.trading:disconnect - ✅ Disconnected from trading platform
2025-10-30 14:21:19 | INFO     | risk_manager.core.manager:stop - Risk Manager stopped
Risk Manager stopped
2025-10-30 14:21:19 | INFO     | risk_manager.integrations.trading:disconnect - Disconnecting from trading platform...
{"timestamp":"2025-10-30T19:21:19.845581Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"disconnect","line":983,"message":"Disconnecting TradingSuite...","taskName":"Task-1"}
{"timestamp":"2025-10-30T19:21:19.853571Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"stop","line":557,"message":"Cleanup scheduler stopped","taskName":"Task-44747"}
{"timestamp":"2025-10-30T19:21:19.854971Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"bounded_statistics","function":"cleanup_bounded_statistics","line":926,"message":"Bounded statistics cleanup completed","taskName":"Task-44747","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.855876Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"cleanup","line":1177,"message":"✅ RealtimeDataManager cleanup completed","taskName":"Task
-44747","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.859375Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"stop","line":557,"message":"Cleanup scheduler stopped","taskName":"Task-44748"}
{"timestamp":"2025-10-30T19:21:19.859873Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"bounded_statistics","function":"cleanup_bounded_statistics","line":926,"message":"Bounded statistics cleanup completed","taskName":"Task-44748","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.860269Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"cleanup","line":1177,"message":"✅ RealtimeDataManager cleanup completed","taskName":"Task
-44748","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.863641Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"stop","line":557,"message":"Cleanup scheduler stopped","taskName":"Task-44749"}
{"timestamp":"2025-10-30T19:21:19.864160Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"bounded_statistics","function":"cleanup_bounded_statistics","line":926,"message":"Bounded statistics cleanup completed","taskName":"Task-44749","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.864736Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"cleanup","line":1177,"message":"✅ RealtimeDataManager cleanup completed","taskName":"Task
-44749","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T19:21:19.866061Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"disconnect","line":1006,"message":"TradingSuite disconnected","taskName":"Task-1"}
2025-10-30 14:21:19 | SUCCESS  | risk_manager.integrations.trading:disconnect - ✅ Disconnected from trading platform
SDK disconnected

Shutdown complete

(.venv-1) PS C:\Users\jakers\Desktop\risk-manager-v34> 