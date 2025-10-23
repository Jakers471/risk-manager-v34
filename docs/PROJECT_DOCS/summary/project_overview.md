---
doc_id: SUM-001
version: 2.0
last_updated: 2025-01-17
dependencies: []
---

# Risk Manager - Project Overview

**Purpose:** Professional-grade risk management daemon that protects traders from blowing TopstepX trading accounts.

---

## 🎯 Core Concept

**The Problem:** Traders need automated risk enforcement to prevent account violations and emotional trading mistakes.

**The Solution:** A Windows Service daemon that monitors TopstepX accounts in real-time via SignalR WebSocket, enforces configurable risk rules, and provides dual CLI interfaces (admin + trader).

---

## 🏗️ System Architecture (High-Level)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Windows Service Daemon                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Risk Engine (Core Orchestrator)                           │ │
│  │  - Loads rules from config                                 │ │
│  │  - Processes incoming events                               │ │
│  │  - Executes enforcement actions                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ SignalR      │  │ State Manager│  │ Enforcement Actions  │   │
│  │ Listener     │  │ (SQLite DB)  │  │ (Close/Cancel/Lock)  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Events (GatewayUserPosition,
                              │         GatewayUserTrade, etc.)
                              ▼
                  ┌─────────────────────────┐
                  │  TopstepX Gateway API   │
                  │  (SignalR + REST)       │
                  └─────────────────────────┘
                              │
                              ▼
                  ┌─────────────────────────┐
                  │  Broker (Rithmic/CQG)   │
                  │  (Trader places orders) │
                  └─────────────────────────┘

┌────────────────────┐                    ┌────────────────────┐
│   Admin CLI        │                    │   Trader CLI       │
│   (Password)       │                    │   (View-Only)      │
│  - Configure rules │                    │  - Status screen   │
│  - Manage accounts │                    │  - Lockout timers  │
│  - Start/stop      │                    │  - Enforcement log │
└────────────────────┘                    └────────────────────┘
```

---

## 🔑 Key Features

### 1. **Dual-CLI System**
- **Admin CLI (Password-Protected):** Configure rules, manage accounts, start/stop daemon
- **Trader CLI (View-Only):** See status, timers, lockouts, enforcement logs

### 2. **12 Risk Rules (3 Categories)**

**Trade-by-Trade (No Lockout):**
- MaxContracts - Net contract limit across all instruments
- MaxContractsPerInstrument - Per-symbol caps
- NoStopLossGrace - Enforce stop-loss placement

**Hard Lockout (Until Reset/Condition):**
- DailyRealizedLoss - Hard daily realized P&L limit
- DailyUnrealizedLoss - Hard floating loss limit
- MaxUnrealizedProfit - Profit target enforcement
- SessionBlockOutside - Block orders outside trading hours
- AuthLossGuard - Monitor API `canTrade` status
- SymbolBlocks - Blacklist specific symbols

**Configurable Timer Lockout:**
- TradeFrequencyLimit - Cap trades per minute/hour/session
- CooldownAfterLoss - Time lockout after loss threshold

**Automation:**
- TradeManagement - Auto breakeven, trailing stops

### 3. **Real-Time Enforcement**
- Cannot block orders before broker (API limitation)
- **Reactive enforcement:** Close positions within milliseconds of fill
- Simultaneous: Close position + Cancel orders + Set lockout + CLI warning

### 4. **Windows Service Protection**
- Runs as Windows Service (auto-start on boot)
- Admin password required to stop/reconfigure
- Trader cannot kill the daemon

### 5. **State Persistence (SQLite)**
- Survives crashes/reboots
- Stores: P&L, trade counts, lockout states, cooldown timers

---

## 🔧 Technology Stack

- **Language:** Python (beginner-friendly, daemon-ready)
- **API Integration:** TopstepX Gateway API (SignalR WebSocket + REST)
- **State Persistence:** SQLite
- **Windows Service:** `pywin32` library
- **Testing:** pytest
- **Config Format:** YAML

---

## 📊 TopstepX API Integration

### **Authentication:**
- Username + API Key → JWT token (24hr validity)
- Multiple accounts possible under one username
- Select specific account to monitor

### **Real-Time Events (SignalR WebSocket):**
- `GatewayUserPosition` - Position updates (size, averagePrice, type)
- `GatewayUserOrder` - Order status changes
- `GatewayUserTrade` - Trade executions with P&L
- `GatewayUserAccount` - Account updates (`canTrade` status)

### **REST API Actions:**
- `POST /api/Position/closeContract` - Close entire position
- `POST /api/Position/partialCloseContract` - Close partial position
- `POST /api/Order/cancel` - Cancel order
- `POST /api/Order/modify` - Modify stop/limit prices

---

## 🏛️ Modular Architecture Philosophy

**Core Principle:** One rule = one file, reusable enforcement modules, no file over 200 lines.

### **Shared Modules (Reused by All Rules):**
1. **Enforcement Actions** (`enforcement/actions.py`)
   - `close_all_positions()`, `close_position()`, `cancel_all_orders()`

2. **Lockout Manager** (`state/lockout_manager.py`)
   - `set_lockout()`, `set_cooldown()`, `is_locked_out()`

3. **Timer Manager** (`state/timer_manager.py`)
   - `start_timer()`, `get_remaining_time()`, `check_timers()`

4. **Reset Scheduler** (`state/reset_scheduler.py`)
   - `schedule_daily_reset()`, `reset_daily_counters()`

### **Each Rule Calls Shared Modules (No Duplication):**
```python
class MaxContractsRule(BaseRule):
    def check(self, event):
        if breach_detected:
            self.enforcement.close_all_positions(account_id)
            # NO lockout for this rule type
```

---

## 🎯 Phase-Based Implementation

**Phase 1: Solid Base + 3 Rules (MVP)**
- Complete architecture (daemon, API, state, CLI)
- 3 simple rules: MaxContracts, MaxContractsPerInstrument, SessionBlockOutside
- Testing infrastructure
- Windows Service setup
- **Goal:** Working system end-to-end

**Phase 2+: Add Rules Incrementally**
- Each new rule = new file in `rules/`
- No refactoring needed (architecture designed for growth)

---

## 🔐 Security & Config

### **Development Mode:**
- Config files in user folder
- Easy iteration

### **Production Mode:**
- Config moved to `C:\ProgramData\RiskManager\`
- Windows ACL permissions (Admin + SYSTEM only)
- Trader cannot view/edit configs

### **Config Structure:**
```yaml
# config/accounts.yaml
topstepx:
  username: "your_username"
  api_key: "your_api_key"
monitored_account:
  account_id: 123

# config/risk_config.yaml
max_contracts:
  enabled: true
  limit: 5
  count_type: "net"
  close_all: true

daily_realized_loss:
  enabled: true
  limit: -500
  reset_time: "17:00"
  timezone: "America/New_York"
```

---

## 📈 Data Flow (Simplified)

1. **Trader places order on broker** → Order fills
2. **TopstepX sends event** → SignalR WebSocket (`GatewayUserTrade`)
3. **Risk daemon receives event** → Processes through Risk Engine
4. **Risk Engine checks all enabled rules** → Detects breach
5. **Enforcement action executes** → Close position + Cancel orders + Set lockout
6. **Trader CLI updates** → Shows lockout timer + enforcement log
7. **State persists to SQLite** → Survives crash/reboot

---

## 🛡️ Why This Approach Works

1. **Reactive but Fast:** Can't block broker orders, but close within milliseconds
2. **Modular Design:** Add rules without touching existing code
3. **Failsafe:** Windows Service can't be killed by trader
4. **Beginner-Friendly:** Python, small files, clear architecture
5. **Production-Grade:** State persistence, logging, testing, security
6. **Solo-Dev Optimized:** No complex async/await, clear code flow

---

## 📖 Next Steps

- **Read ARCH-V2-001** for complete architecture details
- **Read rule files (RULE-001 to RULE-012)** for specific implementations
- **Read ARCH-PIPE-001** for integration pipeline details

---

**This is a professional-grade system built with simplicity and maintainability in mind.**
