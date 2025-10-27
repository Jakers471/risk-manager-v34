# Unified Architecture Specifications

**Created:** 2025-10-25
**Wave:** Wave 3 - Specification Unification
**Researcher:** Architecture Specification Unification Specialist
**Status:** Authoritative

---

## Purpose

This directory contains the **unified** architecture specifications for Risk Manager V34. These specifications resolve conflicts between v1 and v2, using **v2 (SDK-first) as the authoritative version**.

---

## Architecture Evolution

### Version 1 (Historical)
- **Date:** 2025-01-17
- **Status:** Initial planning session notes
- **Context:** Written before Project-X-Py SDK existed
- **Approach:** Direct TopstepX Gateway API integration
- **Details:** See `/docs/archive/2025-10-25-pre-wave1/01-specifications/architecture/system_architecture_v1.md`

### Version 2 (Current - AUTHORITATIVE)
- **Date:** 2025-01-17 (refined)
- **Status:** Production-ready, SDK-first design
- **Context:** Uses Project-X-Py SDK (v3.5.9) as foundation
- **Approach:** SDK handles WebSocket/auth/orders, we add risk management on top
- **Details:** See `/docs/archive/2025-10-25-pre-wave1/01-specifications/architecture/system_architecture_v2.md`

**Resolution:** Use **v2** as authoritative. Document v1 as design evolution context.

---

## Daemon Architecture

Risk Manager runs as a background daemon/service:

### Key Characteristics
- **System runs as background daemon/service**
- **Auto-starts on computer startup/login**
- **Admin configures settings, starts daemon**
- **Daemon runs continuously monitoring accounts**
- **Trader cannot stop daemon** (UAC protected)
- **Admin can stop/restart daemon to load new configs**

### Lifecycle
1. **Initial Setup** (Admin)
   - Install Windows Service
   - Configure API credentials
   - Configure risk rules
   - Configure account mappings
   - Set reset timers
   - Start daemon

2. **Runtime** (Daemon)
   - Auto-starts on boot/login
   - Connects to Project-X SDK
   - Loads configuration
   - Monitors account events
   - Enforces risk rules
   - Manages lockouts
   - Persists state to SQLite

3. **Daily Operation** (Trader)
   - Trader logs in to computer
   - Daemon already running (auto-started)
   - Trader opens Trader CLI (view-only)
   - Trades normally
   - CLI shows real-time status
   - Cannot modify daemon or configs

4. **Reconfiguration** (Admin)
   - Admin can return anytime
   - Stop daemon (requires admin password)
   - Modify configurations
   - Restart daemon
   - Changes take effect

---

## Files in This Directory

### 1. System Architecture
**File:** `system-architecture.md`
**Purpose:** Complete system architecture (v1→v2 evolution)
**Contents:**
- Architecture evolution (v1 vs v2)
- Component relationships (with TradingIntegration layer)
- Data flow diagrams
- Technology stack (SDK-first)
- Daemon lifecycle
- Directory structure
- Key design decisions
- Component interaction table

### 2. Event Flow Architecture
**File:** `event-flow.md` ⭐ NEW
**Purpose:** Detailed event flow diagrams and sequence flows
**Contents:**
- Complete event flow (TopstepX → SDK → Risk Engine → Enforcement)
- Two event subscription patterns (SignalR direct vs SDK EventBus)
- Async pattern throughout (asyncio coordination)
- Rule category event flows (immediate, hard lockout, cooldown)
- Error handling flows (disconnect, exceptions, enforcement failures)
- Component responsibility matrix
- 8-checkpoint logging in event flow
- Sequence diagrams for each rule category

### 3. Database Manager (MOD-001)
**File:** `MOD-001-database-manager.md`
**Purpose:** State persistence layer
**Contents:**
- SQLite database abstraction
- Schema definitions
- Query interfaces
- Transaction management
- Connection pooling
- Crash recovery

### 4. Lockout Manager (MOD-002)
**File:** `MOD-002-lockout-manager.md`
**Purpose:** Account lockout system
**Contents:**
- Hard lockouts (until specific time)
- Cooldown timers (duration-based)
- Auto-expiry logic
- State persistence
- CLI integration
- Event router integration

### 5. Timer Manager (MOD-003)
**File:** `MOD-003-timer-manager.md`
**Purpose:** Time windows and reset schedules
**Contents:**
- Countdown timers
- Callback execution
- Background task integration
- Trader CLI countdown display
- Precision handling

### 6. Reset Scheduler (MOD-004)
**File:** `MOD-004-reset-scheduler.md`
**Purpose:** Daily reset automation
**Contents:**
- Daily reset at midnight ET
- Timezone handling (DST-aware)
- Holiday calendar integration
- P&L counter resets
- Lockout clearing

### 7. Daemon Lifecycle
**File:** `daemon-lifecycle.md`
**Purpose:** How daemon works
**Contents:**
- Windows Service integration
- Auto-start configuration
- Startup sequence
- Shutdown handling
- Admin vs Trader separation
- Configuration reloading
- State recovery

---

## Conflict Resolution

### v1 vs v2 Differences

| Aspect | v1 | v2 (AUTHORITATIVE) | Resolution |
|--------|----|--------------------|------------|
| **API Integration** | Direct Gateway API | Project-X-Py SDK | Use SDK (v2) |
| **WebSocket** | Manual SignalR via `signalrcore` | SDK handles SignalR | Use SDK (v2) |
| **Enforcement Module** | `src/core/enforcement.py` | `src/enforcement/actions.py` | Use v2 structure |
| **Event Routing** | In risk_engine | Dedicated event_router | Use v2 (clearer) |
| **Lockout Display** | In status_screen | Dedicated lockout_display.py | Use v2 (better separation) |
| **Connection Health** | In signalr_listener | Dedicated connection_manager | Use v2 (separation of concerns) |
| **Priority Handler** | Included | Removed (simplified) | Use v2 (not needed) |

**Rationale:** v2 is more mature, modular, and production-ready. SDK-first approach eliminates complex manual API integration.

---

## Implementation Status

### Completed (From Wave 2 Gap Analysis)
- Database Manager (MOD-001) - `src/risk_manager/state/database.py`
- PnL Tracker - `src/risk_manager/state/pnl_tracker.py`

### Missing (Critical Path)
- Lockout Manager (MOD-002) - Blocks 7 rules (54%)
- Timer Manager (MOD-003) - Blocks 4 rules
- Reset Scheduler (MOD-004) - Blocks 5 rules
- Event Router - Integration point
- Windows Service Wrapper - Deployment blocker

**See:** `/docs/analysis/wave2-gap-analysis/` for detailed implementation gaps.

---

## SDK Integration Notes

**CRITICAL CONTEXT:** Original specs (v1) were written BEFORE Project-X-Py SDK existed.

### What v1 Specs Described (Manual Approach)
- Direct TopstepX Gateway API calls
- Manual SignalR WebSocket handling
- Manual position/order management
- Custom state tracking
- Low-level API integration

### What v2 Uses (SDK-First Approach)
- **Project-X-Py SDK** (v3.5.9) handles:
  - WebSocket connections (SignalR)
  - Real-time events (positions, orders, trades)
  - Order management (place, cancel, modify)
  - Position management (close, partially close)
  - Account data & statistics
  - Market data & indicators
  - Auto-reconnection

### Risk Manager's Role (v2)
- **Use SDK as foundation** (don't reinvent wheel)
- **Add risk logic on top** (rules, enforcement, lockouts)
- **Manage state** (P&L, lockouts, timers)
- **Provide interfaces** (Admin CLI, Trader CLI)
- **Persist state** (SQLite for crash recovery)

**See:** `/docs/current/SDK_INTEGRATION_GUIDE.md` for SDK mapping details.

---

## Key Design Principles

### 1. SDK-First Architecture
- Don't reimplement what SDK provides
- Use SDK for all trading operations
- Add risk management layer on top
- See `system-architecture.md` for details

### 2. Modular Design
- One rule = one file (< 200 lines)
- Reusable modules (MOD-001 to MOD-004)
- Clear separation of concerns
- Easy to add features without refactoring

### 3. Daemon-Based Deployment
- Runs as Windows Service
- Auto-starts on boot/login
- Admin-only control
- Trader cannot stop/modify
- See `daemon-lifecycle.md` for details

### 4. State Persistence
- SQLite database for all critical state
- Survives crashes and reboots
- Daily lockouts persist across restarts
- P&L tracking recoverable
- See `MOD-001-database-manager.md` for details

### 5. Dual CLI System
- **Admin CLI:** Password-protected, full control
- **Trader CLI:** View-only, status monitoring
- Clear separation of privileges
- UAC integration for admin elevation

### 6. Event-Driven Processing
- SDK provides real-time events
- Event router checks lockouts first
- Rules process events
- Enforcement actions execute
- Lockout manager updates state
- CLI displays updates

---

## Next Steps

1. **Read System Architecture** - Start with `system-architecture.md`
2. **Understand Modules** - Read MOD-001 through MOD-004
3. **Learn Daemon Lifecycle** - Read `daemon-lifecycle.md`
4. **Review Implementation Gaps** - See Wave 2 gap analysis
5. **Begin Implementation** - Follow critical path (Timer → Lockout → Reset)

---

## Related Documentation

### Wave 1 Analysis
- `/docs/analysis/wave1-feature-inventory/03-ARCHITECTURE-INVENTORY.md`

### Wave 2 Gap Analysis
- `/docs/analysis/wave2-gap-analysis/02-STATE-MANAGEMENT-GAPS.md`
- `/docs/analysis/wave2-gap-analysis/05-DEPLOYMENT-GAPS.md`

### Original Specifications
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/architecture/` (v1 and v2)
- `/docs/archive/2025-10-25-pre-wave1/01-specifications/modules/` (MOD specs)

### Current Documentation
- `/docs/current/SDK_INTEGRATION_GUIDE.md` - How we use Project-X SDK
- `/docs/current/PROJECT_STATUS.md` - Current implementation progress

---

**These unified specifications are the authoritative source for Risk Manager V34 architecture.**
