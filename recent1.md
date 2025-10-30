
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
2025-10-30 03:59:23.407 | INFO     | risk_manager.core.engine:__init__:33 - Risk Engine initialized
{"timestamp":"2025-10-30T08:59:23.411412Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"__init__","line":48,"message":"🚀 Risk Manager starting...","taskName":"Task-1"}
2025-10-30 03:59:23 | INFO     | risk_manager.core.manager:__init__ - Risk Manager initialized
{"timestamp":"2025-10-30T08:59:23.412435Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"create","line":133,"message":"✅ Config loaded: 0 custom rules, monitoring 0 instruments","taskName":"Task-1"}        
2025-10-30 03:59:23 | INFO     | risk_manager.state.database:__init__ - Database initialized at data\risk_state.db
2025-10-30 03:59:23 | INFO     | risk_manager.state.timer_manager:__init__ - TimerManager initialized
2025-10-30 03:59:23 | INFO     | risk_manager.state.pnl_tracker:__init__ - PnLTracker initialized
2025-10-30 03:59:23 | INFO     | risk_manager.state.lockout_manager:load_lockouts_from_db - Loaded 0 lockouts from database
2025-10-30 03:59:23 | INFO     | risk_manager.state.lockout_manager:__init__ - Lockout Manager initialized
2025-10-30 03:59:23 | INFO     | risk_manager.rules.daily_realized_loss:__init__ - DailyRealizedLossRule initialized: limit=$-5.00, reset=17:00 America/New_York
2025-10-30 03:59:23 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedLossRule
2025-10-30 03:59:23 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedLossRule (limit=$-5.0)
2025-10-30 03:59:23 | INFO     | risk_manager.rules.daily_realized_profit:__init__ - DailyRealizedProfitRule initialized: target=$1000.00, reset=17:00 America/New_York
2025-10-30 03:59:23 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedProfitRule
2025-10-30 03:59:23 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedProfitRule (target=$1000.0)
2025-10-30 03:59:23 | INFO     | risk_manager.rules.max_contracts_per_instrument:__init__ - MaxContractsPerInstrumentRule initialized - Limits: {'MNQ': 2, 'ES': 1}, Enforcement: reduce_to_limit, Unknown: allow_with_limit:3
2025-10-30 03:59:23 | INFO     | risk_manager.core.engine:add_rule - Added rule: MaxContractsPerInstrumentRule
2025-10-30 03:59:23 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: MaxContractsPerInstrumentRule (2 symbols)
2025-10-30 03:59:23 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ TradeFrequencyLimitRule requires timers_config.yaml (skipped)
2025-10-30 03:59:23 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ CooldownAfterLossRule requires timers_config.yaml (skipped)
2025-10-30 03:59:23 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ SessionBlockOutsideRule requires timers_config.yaml (skipped)
2025-10-30 03:59:23 | INFO     | risk_manager.core.engine:add_rule - Added rule: AuthLossGuardRule
2025-10-30 03:59:23 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: AuthLossGuardRule
2025-10-30 03:59:23 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyUnrealizedLossRule
2025-10-30 03:59:23 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyUnrealizedLossRule (limit=$-20.0)
2025-10-30 03:59:23 | INFO     | risk_manager.core.engine:add_rule - Added rule: MaxUnrealizedProfitRule
2025-10-30 03:59:23 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: MaxUnrealizedProfitRule (target=$20.0)
2025-10-30 03:59:23 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ 3 rules skipped (require additional configuration)
2025-10-30 03:59:23 | WARNING  | risk_manager.core.manager:_add_default_rules -    TradeManagement rule requires bracket order configuration
2025-10-30 03:59:23 | WARNING  | risk_manager.core.manager:_add_default_rules -    Timer-based rules require timers_config.yaml
{"timestamp":"2025-10-30T08:59:23.458993Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"_add_default_rules","line":515,"message":"✅ Rules initialized: 6 rules loaded from configuration","taskName":"Task-1"
}
2025-10-30 03:59:23 | INFO     | risk_manager.core.manager:_add_default_rules - Loaded 6/9 enabled rules
2025-10-30 03:59:23 | INFO     | risk_manager.core.manager:create - Risk Manager created for instruments: None
Risk Manager initialized!

Connecting to TopstepX API...
  Username: jakertrader
  Account: PRAC-V2-126244-84184528
2025-10-30 03:59:23 | INFO     | risk_manager.integrations.trading:__init__ - Trading integration initialized for: ['MNQ', 'ENQ', 'ES']
2025-10-30 03:59:23 | INFO     | risk_manager.integrations.trading:connect - Connecting to ProjectX trading platform...
2025-10-30 03:59:23 | INFO     | risk_manager.integrations.trading:connect - Step 1: Authenticating via HTTP API...
2025-10-30 03:59:24 | INFO     | risk_manager.integrations.trading:connect - ✅ Authenticated: PRAC-V2-126244-84184528 (ID: 13298777)
2025-10-30 03:59:24 | INFO     | risk_manager.integrations.trading:connect -    Balance: $146,184.34, Trading: True
2025-10-30 03:59:24 | INFO     | risk_manager.integrations.trading:connect - Step 2: Establishing SignalR WebSocket connection...
{"timestamp":"2025-10-30T08:59:24.666857Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T08:59:35.785741Z","level":"ERROR","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"connect","line":316,"message":"WebSocket error","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
2025-10-30 03:59:35 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ SignalR WebSocket connected (User Hub + Market Hub)
2025-10-30 03:59:35 | INFO     | risk_manager.integrations.trading:connect - Step 3: Initializing TradingSuite...
{"timestamp":"2025-10-30T08:59:36.402719Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-5"}
{"timestamp":"2025-10-30T08:59:36.475383Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-5"}
{"timestamp":"2025-10-30T08:59:36.475789Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-5"}
{"timestamp":"2025-10-30T08:59:36.476053Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-5","instrument":"MNQ"}
{"timestamp":"2025-10-30T08:59:36.476441Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-5"}
{"timestamp":"2025-10-30T08:59:36.476763Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-5","manager":"PositionManager"}
{"timestamp":"2025-10-30T08:59:36.478574Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-7"}
{"timestamp":"2025-10-30T08:59:36.478960Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-7"}
{"timestamp":"2025-10-30T08:59:36.479236Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-7"}    
{"timestamp":"2025-10-30T08:59:36.479429Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-7","instrument":"ES"}
{"timestamp":"2025-10-30T08:59:36.479742Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-7"}
{"timestamp":"2025-10-30T08:59:36.480002Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-7","manager":"PositionManager"}
{"timestamp":"2025-10-30T08:59:36.481246Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-6"}
{"timestamp":"2025-10-30T08:59:36.481586Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-6"}
{"timestamp":"2025-10-30T08:59:36.481903Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-6"}    
{"timestamp":"2025-10-30T08:59:36.482137Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-6","instrument":"ENQ"}
{"timestamp":"2025-10-30T08:59:36.482444Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-6"}
{"timestamp":"2025-10-30T08:59:36.482737Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-6","manager":"PositionManager"}
{"timestamp":"2025-10-30T08:59:36.483201Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"__init__","line":443,"message":"TradingSuite created for ['MNQ', 'ENQ', 'ES'] with features: [<Features.PERFORMANCE_ANALYTICS: 'performance_analytics'>, <Features.AUTO_RECONNECT: 'auto_reconnect'>]","taskName":"Task-1"}
{"timestamp":"2025-10-30T08:59:36.483618Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":840,"message":"Connecting to real-time feeds...","taskName":"Task-1"}
{"timestamp":"2025-10-30T08:59:36.483895Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T08:59:47.565214Z","level":"ERROR","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"connect","line":316,"message":"WebSocket error","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T08:59:47.568139Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-10"}
{"timestamp":"2025-10-30T08:59:47.568491Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-10
"}
{"timestamp":"2025-10-30T08:59:47.568956Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-10"}{"timestamp":"2025-10-30T08:59:47.569396Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-11"}     
{"timestamp":"2025-10-30T08:59:47.569696Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-11
"}
{"timestamp":"2025-10-30T08:59:47.570148Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-11"}{"timestamp":"2025-10-30T08:59:47.570551Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-12"}     
{"timestamp":"2025-10-30T08:59:47.570944Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-12
"}
{"timestamp":"2025-10-30T08:59:47.571392Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-12"}{"timestamp":"2025-10-30T08:59:47.576133Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-11"}
{"timestamp":"2025-10-30T08:59:47.576947Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-11","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T08:59:47.578045Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-11","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T08:59:47.578970Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T08:59:47.579505Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T08:59:47.582267Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-10"}
{"timestamp":"2025-10-30T08:59:47.582760Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-10","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T08:59:47.583558Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-10","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T08:59:47.584053Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T08:59:47.584418Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T08:59:47.585627Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-12"}
{"timestamp":"2025-10-30T08:59:47.586397Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-12","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T08:59:47.587201Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-12","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T08:59:47.588141Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T08:59:47.589154Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T08:59:47.632718Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-11","position_count":0}
{"timestamp":"2025-10-30T08:59:47.633061Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-11","refreshed_count":0}
{"timestamp":"2025-10-30T08:59:47.635343Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-12","position_count":0}
{"timestamp":"2025-10-30T08:59:47.635725Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-12","refreshed_count":0}
{"timestamp":"2025-10-30T08:59:47.641726Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-10","position_count":0}
{"timestamp":"2025-10-30T08:59:47.642022Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-10","refreshed_count":0}
{"timestamp":"2025-10-30T08:59:48.079251Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 209.8 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-11","operation":"initialize","instrument":"MNQ","initial_days":5}
{"timestamp":"2025-10-30T08:59:48.137332Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 209.8 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-12","operation":"initialize","instrument":"MNQ","initial_days":5}
{"timestamp":"2025-10-30T08:59:48.174343Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 1min ends at 2025-10-30 00:30:00-05:00, 209.8 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-10","operation":"initialize","instrument":"MNQ","initial_days":5}
{"timestamp":"2025-10-30T08:59:48.189095Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 209.8 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-11","operation":"initialize","instrument":"MNQ","initial_days":5}
{"timestamp":"2025-10-30T08:59:48.189738Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-11"}
{"timestamp":"2025-10-30T08:59:48.193187Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-11","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T08:59:48.360045Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 209.8 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-12","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T08:59:48.360571Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-12"}
{"timestamp":"2025-10-30T08:59:48.388830Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-12","operation":"start_realtime_feed","instrument":"ES","contract_id":"CON.F.US.EP.Z25"}
{"timestamp":"2025-10-30T08:59:48.407876Z","level":"WARNING","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"_load_timeframe_data","line":931,"message":"Historical data for 5min ends at 2025-10-30 00:30:00-05:00, 209.8 minutes ago. Gap will be filled when real-time data arrives.","taskName":"Task-10","operation":"start_realtime_feed","instrument":"ES","contract_id":"CON.F.US.EP.Z25"}
{"timestamp":"2025-10-30T08:59:48.409242Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-10"}
{"timestamp":"2025-10-30T08:59:48.454982Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-10","operation":"start_realtime_feed","instrument":"MNQ","contract_id":"CON.F.US.MNQ.Z25"}
{"timestamp":"2025-10-30T08:59:48.455908Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":853,"message":"TradingSuite initialization complete","taskName":"Task-1"}
2025-10-30 03:59:48 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ Connected to ProjectX (HTTP + WebSocket + TradingSuite)
Connected to TopstepX API!

Starting event loop...
2025-10-30 03:59:48 | INFO     | risk_manager.core.manager:start - Starting Risk Manager...
{"timestamp":"2025-10-30T08:59:48.460835Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"start","line":40,"message":"✅ Event loop running: 6 active rules monitoring events","taskName":"Task-1"}
2025-10-30 03:59:48 | INFO     | risk_manager.core.engine:start - Risk Engine started
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - Starting trading event monitoring...
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - Registering event callbacks via suite.on()...
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_PLACED
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_FILLED
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_PARTIAL_FILL
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_CANCELLED
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_REJECTED
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_MODIFIED
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_EXPIRED
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_OPENED
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_CLOSED
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_UPDATED
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - 📊 Registering market data event handlers...
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: QUOTE_UPDATE
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: DATA_UPDATE
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: TRADE_TICK
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: NEW_BAR (1min, 5min timeframes)
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - Checking instruments for price data...
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start -   ℹ️  MNQ - prices will come from QUOTE_UPDATE events
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start -   ℹ️  ENQ - prices will come from QUOTE_UPDATE events
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start -   ℹ️  ES - prices will come from QUOTE_UPDATE events
2025-10-30 03:59:48 | SUCCESS  | risk_manager.integrations.trading:start - ✅ Trading monitoring started (14 event handlers registered)
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - 📡 Listening for events: ORDER (8 types), POSITION (3 types), MARKET DATA (4 types)
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - 🔄 Started order polling task (5s interval)
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - 📊 Started unrealized P&L status bar (0.5s refresh)
2025-10-30 03:59:48 | INFO     | risk_manager.integrations.trading:start - ================================================================================
2025-10-30 03:59:48 | SUCCESS  | risk_manager.core.manager:start - ✅ Risk Manager ACTIVE - Protecting your capital!
Risk Manager is running!

Press Ctrl+C to stop

============================================================
                  LIVE EVENT FEED
============================================================

📊 Unrealized P&L: $+0.00  2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - MNQ BUY 5 @ $26,271.50
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION OPENED - MNQ LONG 5 @ $26,271.50 | P&L: $0.00
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | WARNING  | risk_manager.integrations.trading:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_handle_position_event -   ℹ️  No take profit order
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:49 | INFO     | risk_manager.integrations.trading:_handle_position_event -   🔄 CANONICAL: MNQ → MNQ | Side: LONG | Qty: 5 | P&L: $0.00
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_opened → evaluating 6 rules
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:59:49 | WARNING  | risk_manager.rules.max_contracts_per_instrument:evaluate - ⚠️ RULE-002 BREACH: MNQ position size 5 exceeds limit 2
2025-10-30 03:59:49 | ERROR    | risk_manager.core.engine:evaluate_rules - Error evaluating rule MaxContractsPerInstrumentRule: argument of type 'bool' is not iterable
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:59:49 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
📊 Unrealized P&L: $-6.25  2025-10-30 03:59:55 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: unrealized_pnl_update → evaluating 6 rules
2025-10-30 03:59:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:59:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:59:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:59:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:59:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:59:55 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:59:55 | INFO     | risk_manager.integrations.trading:_on_quote_update - 💹 Unrealized P&L update: MNQ $-10.00
📊 Unrealized P&L: $-3.75  2025-10-30 03:59:59 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - MNQ SELL 5 @ $26,270.75
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 6 rules
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS
2025-10-30 03:59:59 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION CLOSED - MNQ FLAT 0 @ $26,271.50 | P&L: $0.00
2025-10-30 03:59:59 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 03:59:59 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
📊 Unrealized P&L: $-5.00  2025-10-30 03:59:59 | INFO     | risk_manager.integrations.trading:_handle_position_event - 💰 Calculated P&L:
2025-10-30 03:59:59 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Entry: $26,271.50 @ 5 (long)
2025-10-30 03:59:59 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Exit: $26,270.75
2025-10-30 03:59:59 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Price diff: -0.75 = -3.0 ticks
2025-10-30 03:59:59 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Realized P&L: $-7.50
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: position_closed → evaluating 6 rules
2025-10-30 03:59:59 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Event type matches! Processing EventType.POSITION_CLOSED
2025-10-30 03:59:59 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    profitAndLoss from event data: -7.5
2025-10-30 03:59:59 | INFO     | risk_manager.rules.daily_realized_loss:evaluate -    ✅ Have profitAndLoss: $-7.50, updating tracker...
2025-10-30 03:59:59 | INFO     | risk_manager.rules.daily_realized_loss:evaluate - 💰 Daily P&L: $+16.50 / $-5.00 limit (this trade: $-7.50)
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyUnrealizedLoss → PASS
2025-10-30 03:59:59 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxUnrealizedProfit → PASS