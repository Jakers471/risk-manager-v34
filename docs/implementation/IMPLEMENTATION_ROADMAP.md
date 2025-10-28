# Risk Manager V34 - Implementation Roadmap

**Current Status**: All 13 rules complete ✅ | Core engine working ✅  
**Next Phase**: Windows Service Daemon + CLI System

---

## 📋 What's Built vs What's Left

### ✅ COMPLETE (All Risk Logic)

**Core Engine** (100% Complete):
- ✅ RiskEngine - Rule evaluation & enforcement
- ✅ EventBus - Event-driven architecture  
- ✅ RiskManager - Central coordinator
- ✅ All 13 risk rules implemented
- ✅ 475 unit tests passing
- ✅ 93 integration tests passing

**State Management** (100% Complete):
- ✅ Database (SQLite persistence)
- ✅ Lockout Manager (hard lockouts + timers)
- ✅ Timer Manager (countdown timers)
- ✅ Reset Scheduler (daily/weekly resets)
- ✅ PnL Tracker (P&L tracking)

**SDK Integration** (100% Complete):
- ✅ Event handling from TopstepX SDK
- ✅ Order management integration
- ✅ Position tracking integration

---

### ❌ NOT BUILT YET (Deployment Infrastructure)

We need **Windows Service Daemon + CLI System** to make it:
1. **Unkillable by trader** (Windows Service)
2. **Admin-controlled** (UAC elevation required)
3. **Auto-start on boot** (Windows Service)
4. **Config file protected** (ACL permissions)

---

## 🎯 What We Need to Build (In Order)

### **Phase 4: Windows Service Daemon** (4-6 hours) ⭐ START HERE

**Component 4.1: Service Wrapper** (2 hours)
- Create Windows Service class
- Wraps RiskManager as unk illable daemon
- Runs as LocalSystem (highest privilege)

**Component 4.2: Installation Script** (1 hour)
- Install service with admin rights
- Configure auto-start on boot
- Set file ACL permissions

**Component 4.3: Service Manager** (1 hour)
- Start/stop/restart commands
- Status checking
- Log viewing

### **Phase 5: Admin CLI** (3-4 hours)

**Component 5.1: UAC Security** (30 min)
- Check Windows admin elevation
- Exit if not elevated with instructions

**Component 5.2: Admin Commands** (2-3 hours)
- Configure API credentials
- Enable/disable rules
- Set rule limits
- Control daemon (start/stop/restart)

### **Phase 6: Trader CLI** (2-3 hours)

**Component 6.1: View-Only Commands** (2-3 hours)
- View account status
- View P&L
- View active lockouts
- View recent logs

### **Phase 7: Config Management** (1-2 hours)

**Component 7.1: Config Loaders** (1-2 hours)
- Load YAML configs
- Validate configs
- Encrypt API credentials

### **Phase 8: File Protection (ACL)** (1 hour)

**Component 8.1: ACL Configuration** (1 hour)
- Set admin-only write access
- Set trader read-only access
- Protect daemon executable

---

## 📦 Total Effort: 11-16 hours

| Phase | Time | Priority |
|-------|------|----------|
| 4: Windows Service | 4-6 hours | **CRITICAL** |
| 5: Admin CLI | 3-4 hours | **CRITICAL** |
| 6: Trader CLI | 2-3 hours | **HIGH** |
| 7: Config Management | 1-2 hours | **HIGH** |
| 8: File Protection | 1 hour | **MEDIUM** |

---

## 🚀 Recommended Approach

### **Option A: Build Everything (Production Ready)** 
**Time**: 2 weeks  
**Result**: Fully deployed Windows Service  

### **Option B: Minimum Viable Service (Quick Deploy)**
**Time**: 1 week  
**Result**: Basic daemon + admin CLI only

### **Option C: Testing First (Current Focus)**
**Time**: This week  
**Result**: E2E tests, then build deployment

---

## 📝 File Structure (What's Missing)

```
risk-manager-v34/
├── src/risk_manager/
│   ├── service/       ❌ NOT BUILT (Phase 4)
│   ├── cli/           ❌ NOT BUILT (Phase 5-6)
│   └── config/        ❌ NOT BUILT (Phase 7)
├── scripts/           ❌ NOT BUILT (Phase 4 + 8)
└── config/            ❌ Need YAML files (Phase 7)
```

---

**Last Updated**: 2025-10-27 22:45  
**Next Decision**: Build daemon now OR do E2E tests first?
