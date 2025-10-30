
(.venv-1) PS C:\Users\jakers\Desktop\risk-manager-v34> python run_dev.py

============================================================
        RISK MANAGER V34 - DEVELOPMENT MODE
============================================================

2025-10-30 00:06:00.662 | INFO     | risk_manager.cli.logger:setup_logging:166 - Logging initialized: console=INFO, file=DEBUG
2025-10-30 00:06:00.662 | INFO     | risk_manager.cli.logger:setup_logging:167 - Log file: C:\Users\jakers\Desktop\risk-manager-v34\data\logs\risk_manager.log
2025-10-30 00:06:00.663 | INFO     | __main__:main:126 - 🎛️  Console Log Level: INFO
2025-10-30 00:06:00.663 | INFO     | __main__:main:128 - 💡 Tip: Use --log-level DEBUG to see detailed order payloads
2025-10-30 00:06:00.664 | INFO     | risk_manager.cli.logger:log_checkpoint:208 - 🚀 [CHECKPOINT 1] Service Start | version=1.0.0-dev | mode=development
{"timestamp":"2025-10-30T05:06:00.664513Z","level":"INFO","logger":"risk_manager.checkpoints","module":"logger","function":"log_checkpoint","line":213,"message":"🚀 [CHECKPOINT 1] Service Start | version=1.0.0-dev | mode=development","taskName":"Task-1"}
Loading configuration...
Loading runtime configuration...

1. Loading credentials
   OK: Credentials loaded for user: jake...ader

2. Loading risk configuration
   File: C:\Users\jakers\Desktop\risk-manager-v34\config\risk_config.yaml
C:\Users\jakers\Desktop\risk-manager-v34\src\risk_manager\config\models.py:1095: UserWarning: daily_unrealized_loss.limit (-750.0) should be >= daily_realized_loss.limit (-5.0) to trigger before realized loss
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
2025-10-30 00:06:00.701 | INFO     | risk_manager.core.engine:__init__:33 - Risk Engine initialized
{"timestamp":"2025-10-30T05:06:00.706271Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"__init__","line":48,"message":"🚀 Risk Manager starting...","taskName":"Task-1"}
2025-10-30 00:06:00 | INFO     | risk_manager.core.manager:__init__ - Risk Manager initialized
{"timestamp":"2025-10-30T05:06:00.707161Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"create","line":133,"message":"✅ Config loaded: 0 custom rules, monitoring 0 instruments","taskName":"Task-1"}        
2025-10-30 00:06:00 | INFO     | risk_manager.state.database:__init__ - Database initialized at data\risk_state.db
2025-10-30 00:06:00 | INFO     | risk_manager.state.timer_manager:__init__ - TimerManager initialized
2025-10-30 00:06:00 | INFO     | risk_manager.state.pnl_tracker:__init__ - PnLTracker initialized
2025-10-30 00:06:00 | INFO     | risk_manager.state.lockout_manager:load_lockouts_from_db - Loaded 0 lockouts from database
2025-10-30 00:06:00 | INFO     | risk_manager.state.lockout_manager:__init__ - Lockout Manager initialized
2025-10-30 00:06:00 | INFO     | risk_manager.rules.daily_realized_loss:__init__ - DailyRealizedLossRule initialized: limit=$-5.00, reset=17:00 America/New_York
2025-10-30 00:06:00 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedLossRule
2025-10-30 00:06:00 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedLossRule (limit=$-5.0)
2025-10-30 00:06:00 | INFO     | risk_manager.rules.daily_realized_profit:__init__ - DailyRealizedProfitRule initialized: target=$1000.00, reset=17:00 America/New_York
2025-10-30 00:06:00 | INFO     | risk_manager.core.engine:add_rule - Added rule: DailyRealizedProfitRule
2025-10-30 00:06:00 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: DailyRealizedProfitRule (target=$1000.0)
2025-10-30 00:06:00 | INFO     | risk_manager.rules.max_contracts_per_instrument:__init__ - MaxContractsPerInstrumentRule initialized - Limits: {'MNQ': 2, 'ES': 1}, Enforcement: reduce_to_limit, Unknown: allow_with_limit:3
2025-10-30 00:06:00 | INFO     | risk_manager.core.engine:add_rule - Added rule: MaxContractsPerInstrumentRule
2025-10-30 00:06:00 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: MaxContractsPerInstrumentRule (2 symbols)
2025-10-30 00:06:00 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ TradeFrequencyLimitRule requires timers_config.yaml (skipped)
2025-10-30 00:06:00 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ CooldownAfterLossRule requires timers_config.yaml (skipped)
2025-10-30 00:06:00 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ SessionBlockOutsideRule requires timers_config.yaml (skipped)
2025-10-30 00:06:00 | INFO     | risk_manager.core.engine:add_rule - Added rule: AuthLossGuardRule
2025-10-30 00:06:00 | INFO     | risk_manager.core.manager:_add_default_rules - ✅ Loaded: AuthLossGuardRule
2025-10-30 00:06:00 | WARNING  | risk_manager.core.manager:_add_default_rules - ⚠️ 5 rules skipped (require tick economics data)
2025-10-30 00:06:00 | WARNING  | risk_manager.core.manager:_add_default_rules -    Rules DailyUnrealizedLoss, MaxUnrealizedProfit, TradeManagement need tick_value
2025-10-30 00:06:00 | WARNING  | risk_manager.core.manager:_add_default_rules -    Add these manually with tick data or implement tick economics integration
{"timestamp":"2025-10-30T05:06:00.733469Z","level":"INFO","logger":"risk_manager.core.manager","module":"manager","function":"_add_default_rules","line":459,"message":"✅ Rules initialized: 4 rules loaded from configuration","taskName":"Task-1"
}
2025-10-30 00:06:00 | INFO     | risk_manager.core.manager:_add_default_rules - Loaded 4/9 enabled rules
2025-10-30 00:06:00 | INFO     | risk_manager.core.manager:create - Risk Manager created for instruments: None
Risk Manager initialized!

Connecting to TopstepX API...
  Username: jakertrader
  Account: PRAC-V2-126244-84184528
2025-10-30 00:06:00 | INFO     | risk_manager.integrations.trading:__init__ - Trading integration initialized for: ['MNQ', 'ENQ', 'ES']
2025-10-30 00:06:00 | INFO     | risk_manager.integrations.trading:connect - Connecting to ProjectX trading platform...
2025-10-30 00:06:00 | INFO     | risk_manager.integrations.trading:connect - Step 1: Authenticating via HTTP API...
2025-10-30 00:06:02 | INFO     | risk_manager.integrations.trading:connect - ✅ Authenticated: PRAC-V2-126244-84184528 (ID: 13298777)
2025-10-30 00:06:02 | INFO     | risk_manager.integrations.trading:connect -    Balance: $146,763.08, Trading: True
2025-10-30 00:06:02 | INFO     | risk_manager.integrations.trading:connect - Step 2: Establishing SignalR WebSocket connection...
{"timestamp":"2025-10-30T05:06:02.050753Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
2025-10-30 00:06:13 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ SignalR WebSocket connected (User Hub + Market Hub)
2025-10-30 00:06:13 | INFO     | risk_manager.integrations.trading:connect - Step 3: Initializing TradingSuite...
{"timestamp":"2025-10-30T05:06:13.798703Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-5"}
{"timestamp":"2025-10-30T05:06:13.871431Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-5"}
{"timestamp":"2025-10-30T05:06:13.871751Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-5"}
{"timestamp":"2025-10-30T05:06:13.871938Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-5","instrument":"MNQ"}
{"timestamp":"2025-10-30T05:06:13.872257Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-5"}
{"timestamp":"2025-10-30T05:06:13.872617Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-5","manager":"PositionManager"}
{"timestamp":"2025-10-30T05:06:13.874416Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-6"}
{"timestamp":"2025-10-30T05:06:13.874762Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-6"}
{"timestamp":"2025-10-30T05:06:13.875011Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-6"}    
{"timestamp":"2025-10-30T05:06:13.875209Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-6","instrument":"ENQ"}
{"timestamp":"2025-10-30T05:06:13.875518Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-6"}
{"timestamp":"2025-10-30T05:06:13.875843Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-6","manager":"PositionManager"}
{"timestamp":"2025-10-30T05:06:13.877160Z","level":"WARNING","logger":"project_x_py.realtime_data_manager.core","module":"dynamic_resource_limits","function":"__init__","line":246,"message":"psutil not available - using fallback resource monitoring. Install psutil for optimal resource management.","taskName":"Task-7"}
{"timestamp":"2025-10-30T05:06:13.877528Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"configure_dynamic_resources","line":297,"message":"Dynamic resource configuration updated: memory_target=15.0%, memory_pressure=0.8, monitoring_interval=30.0s","taskName":"Task-7"}
{"timestamp":"2025-10-30T05:06:13.877773Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":591,"message":"Dynamic resource limits enabled","taskName":"Task-7"}    
{"timestamp":"2025-10-30T05:06:13.877978Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"core","function":"__init__","line":595,"message":"RealtimeDataManager initialized","taskName":"Task-7","instrument":"ES"}
{"timestamp":"2025-10-30T05:06:13.878239Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"__init__","line":220,"message":"AsyncOrderManager initialized","taskName":"Task-7"}
{"timestamp":"2025-10-30T05:06:13.878460Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"__init__","line":298,"message":"Manager initialized","taskName":"Task-7","manager":"PositionManager"}
{"timestamp":"2025-10-30T05:06:13.878787Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"__init__","line":443,"message":"TradingSuite created for ['MNQ', 'ENQ', 'ES'] with features: [<Features.PERFORMANCE_ANALYTICS: 'performance_analytics'>, <Features.AUTO_RECONNECT: 'auto_reconnect'>]","taskName":"Task-1"}
{"timestamp":"2025-10-30T05:06:13.879047Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":840,"message":"Connecting to real-time feeds...","taskName":"Task-1"}
{"timestamp":"2025-10-30T05:06:13.879270Z","level":"INFO","logger":"project_x_py.realtime.connection_management","module":"connection_management","function":"setup_connections","line":145,"message":"Using URL query parameter for JWT authentication (ProjectX Gateway requirement)","taskName":"Task-1","operation":"setup_connections","user_hub":"https://rtc.topstepx.com/hubs/user","market_hub":"https://rtc.topstepx.com/hubs/market"}
{"timestamp":"2025-10-30T05:06:24.978156Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-10"}
{"timestamp":"2025-10-30T05:06:24.978967Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-10
"}
{"timestamp":"2025-10-30T05:06:24.980035Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-10"}{"timestamp":"2025-10-30T05:06:24.980841Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-11"}     
{"timestamp":"2025-10-30T05:06:24.981383Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-11
"}
{"timestamp":"2025-10-30T05:06:24.982170Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-11"}{"timestamp":"2025-10-30T05:06:24.982995Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":314,"message":"📡 Real-time client already connected and subscribed","taskName":"Task-12"}     
{"timestamp":"2025-10-30T05:06:24.983572Z","level":"INFO","logger":"project_x_py.order_manager.core","module":"core","function":"initialize","line":319,"message":"✅ AsyncOrderManager initialized with real-time capabilities","taskName":"Task-12
"}
{"timestamp":"2025-10-30T05:06:24.984278Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_start_position_processor","line":161,"message":"📋 Position queue processor started","taskName":"Task-12"}{"timestamp":"2025-10-30T05:06:24.992706Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-11"}
{"timestamp":"2025-10-30T05:06:24.993649Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-11","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T05:06:24.994427Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-11","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T05:06:24.995424Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T05:06:24.996087Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-11","account_id":null}
{"timestamp":"2025-10-30T05:06:24.998987Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-12"}
{"timestamp":"2025-10-30T05:06:24.999819Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-12","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T05:06:25.000848Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-12","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T05:06:25.002540Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T05:06:25.003229Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-12","account_id":null}
{"timestamp":"2025-10-30T05:06:25.005092Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"tracking","function":"_setup_realtime_callbacks","line":152,"message":"🔄 Real-time position callbacks registered","taskName":"Task-10"}
{"timestamp":"2025-10-30T05:06:25.006072Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":384,"message":"Manager initialized","taskName":"Task-10","manager":"PositionManager","mode":"realtime"}
{"timestamp":"2025-10-30T05:06:25.006885Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"initialize","line":398,"message":"Manager initialized","taskName":"Task-10","feature":"order_synchronization","enabled":true}
{"timestamp":"2025-10-30T05:06:25.007989Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":602,"message":"Refreshing positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T05:06:25.008732Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":451,"message":"Searching positions","taskName":"Task-10","account_id":null}
{"timestamp":"2025-10-30T05:06:25.055231Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-10","position_count":0}
{"timestamp":"2025-10-30T05:06:25.055669Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-10","refreshed_count":0}
{"timestamp":"2025-10-30T05:06:25.058086Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-11","position_count":0}
{"timestamp":"2025-10-30T05:06:25.058503Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-11","refreshed_count":0}
{"timestamp":"2025-10-30T05:06:25.063464Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"get_all_positions","line":497,"message":"Position updated","taskName":"Task-12","position_count":0}
{"timestamp":"2025-10-30T05:06:25.063821Z","level":"INFO","logger":"project_x_py.position_manager.core","module":"core","function":"refresh_positions","line":607,"message":"Position updated","taskName":"Task-12","refreshed_count":0}
{"timestamp":"2025-10-30T05:06:25.405580Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-11"}
{"timestamp":"2025-10-30T05:06:25.407923Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-11","operation":"start_realtime_feed","instrument":"ENQ","contract_id":"CON.F.US.ENQ.Z25"}
{"timestamp":"2025-10-30T05:06:25.433661Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-10"}
{"timestamp":"2025-10-30T05:06:25.446298Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-10","operation":"start_realtime_feed","instrument":"MNQ","contract_id":"CON.F.US.MNQ.Z25"}
{"timestamp":"2025-10-30T05:06:25.452536Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics","module":"bounded_statistics","function":"start","line":540,"message":"Cleanup scheduler started","taskName":"Task-12"}
{"timestamp":"2025-10-30T05:06:25.455429Z","level":"INFO","logger":"project_x_py.statistics.bounded_statistics.bounded_stats","module":"dynamic_resource_limits","function":"start_resource_monitoring","line":768,"message":"Started dynamic resource monitoring","taskName":"Task-12","operation":"start_realtime_feed","instrument":"ES","contract_id":"CON.F.US.EP.Z25"}
{"timestamp":"2025-10-30T05:06:25.455927Z","level":"INFO","logger":"project_x_py.trading_suite","module":"trading_suite","function":"_initialize","line":853,"message":"TradingSuite initialization complete","taskName":"Task-1"}
2025-10-30 00:06:25 | SUCCESS  | risk_manager.integrations.trading:connect - ✅ Connected to ProjectX (HTTP + WebSocket + TradingSuite)
Connected to TopstepX API!

Starting event loop...
2025-10-30 00:06:25 | INFO     | risk_manager.core.manager:start - Starting Risk Manager...
{"timestamp":"2025-10-30T05:06:25.459904Z","level":"INFO","logger":"risk_manager.core.engine","module":"engine","function":"start","line":40,"message":"✅ Event loop running: 4 active rules monitoring events","taskName":"Task-1"}
2025-10-30 00:06:25 | INFO     | risk_manager.core.engine:start - Risk Engine started
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - Starting trading event monitoring...
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - Registering event callbacks via suite.on()...
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_PLACED
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_FILLED
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_PARTIAL_FILL
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_CANCELLED
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_REJECTED
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_MODIFIED
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: ORDER_EXPIRED
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_OPENED
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_CLOSED
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ✅ Registered: POSITION_UPDATED
2025-10-30 00:06:25 | SUCCESS  | risk_manager.integrations.trading:start - ✅ Trading monitoring started (10 event handlers registered)
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - 📡 Listening for events: ORDER (8 types), POSITION (3 types), + catch-all
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - 🔄 Started order polling task (5s interval)
2025-10-30 00:06:25 | INFO     | risk_manager.integrations.trading:start - ================================================================================
2025-10-30 00:06:25 | SUCCESS  | risk_manager.core.manager:start - ✅ Risk Manager ACTIVE - Protecting your capital!
Risk Manager is running!

Press Ctrl+C to stop

============================================================
                  LIVE EVENT FEED
============================================================

2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - MNQ BUY 1 @ $26,233.25
2025-10-30 00:06:36 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 4 rules
2025-10-30 00:06:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 00:06:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 00:06:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 00:06:36 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION OPENED - MNQ LONG 1 @ $26,233.25 | P&L: $0.00
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:36 | WARNING  | risk_manager.integrations.trading:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_handle_position_event -   ℹ️  No take profit order
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:36 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:45 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - MNQ SELL 1 @ $26,233.75
2025-10-30 00:06:45 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 4 rules
2025-10-30 00:06:45 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 00:06:45 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 00:06:45 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 00:06:45 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 00:06:45 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION CLOSED - MNQ FLAT 0 @ $26,233.25 | P&L: $0.00
2025-10-30 00:06:45 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:45 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on MNQ (contract: CON.F.US.MNQ.Z25)
2025-10-30 00:06:45 | INFO     | risk_manager.integrations.trading:_handle_position_event - 💰 Calculated P&L:
2025-10-30 00:06:45 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Entry: $26,233.25 @ 1 (long)
2025-10-30 00:06:45 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Exit: $26,233.75
2025-10-30 00:06:45 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Price diff: +0.50 = +2.0 ticks
2025-10-30 00:06:45 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Realized P&L: $+10.00
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - ENQ BUY 1 @ $26,232.50
2025-10-30 00:07:00 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 4 rules
2025-10-30 00:07:00 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 00:07:00 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 00:07:00 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 00:07:00 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION OPENED - ENQ LONG 1 @ $26,232.50 | P&L: $0.00
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:00 | WARNING  | risk_manager.integrations.trading:_handle_position_event -   ⚠️  NO STOP LOSS
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_handle_position_event -   ℹ️  No take profit order
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:00 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:03 | INFO     | risk_manager.integrations.trading:_on_order_filled - 💰 ORDER FILLED - ENQ SELL 1 @ $26,231.50
2025-10-30 00:07:03 | INFO     | risk_manager.core.engine:evaluate_rules - 📨 Event: order_filled → evaluating 4 rules
2025-10-30 00:07:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedLoss → PASS (limit: $-5.00)
2025-10-30 00:07:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: DailyRealizedProfit → PASS (target: $1,000.00)
2025-10-30 00:07:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: MaxContractsPerInstrument → PASS
2025-10-30 00:07:03 | INFO     | risk_manager.core.engine:evaluate_rules - ✅ Rule: AuthLossGuard → PASS (connected)
2025-10-30 00:07:03 | INFO     | risk_manager.integrations.trading:_handle_position_event - 📊 POSITION CLOSED - ENQ FLAT 0 @ $26,232.50 | P&L: $0.00
2025-10-30 00:07:03 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:03 | INFO     | risk_manager.integrations.trading:_query_sdk_for_stop_loss - 🔍 Querying SDK for stop loss on ENQ (contract: CON.F.US.ENQ.Z25)
2025-10-30 00:07:03 | INFO     | risk_manager.integrations.trading:_handle_position_event - 💰 Calculated P&L:
2025-10-30 00:07:03 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Entry: $26,232.50 @ 1 (long)
2025-10-30 00:07:03 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Exit: $26,231.50
2025-10-30 00:07:03 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Price diff: -1.00 = -4.0 ticks
2025-10-30 00:07:03 | INFO     | risk_manager.integrations.trading:_handle_position_event -    Realized P&L: $-2.00
