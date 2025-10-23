---
doc_id: ARCH-V1
version: 1.0
last_updated: 2025-01-17
dependencies: []
---

# Risk Manager - System Architecture (v1)
## Original Planning Session Notes

**Session Date:** 2025-01-17
**Status:** Historical Reference

---

## Project Overview

**What:** Professional-grade risk management daemon that connects to TopstepX broker to protect trader from blowing accounts.

**Key Concept:** Dual-CLI system:
- **Admin CLI** - Password protected, can configure rules, start/stop daemon, manage accounts
- **Trader CLI** - View-only, shows status, timers, enforcement logs, clock in/out

**Core Flow:**
1. Trader places order on broker → Order fills
2. TopstepX sends event via SignalR WebSocket
3. Risk daemon receives event → checks against rules
4. If breach detected → flatten position / lock out trader
5. Trader CLI shows what happened and why

---

## Key Decisions Made

### 1. Technology Stack
- **Language:** Python (beginner-friendly, great for daemons, easy to understand)
- **Why Python over Node.js:** Clarity and simplicity trump minor efficiency gains
- **API Integration:** SignalR via `signalrcore` library

### 2. Windows Service Approach (APPROVED)
- Daemon runs as Windows Service (true protection, can't be killed by trader)
- Auto-starts on computer boot
- Admin password required to stop/reconfigure
- Professional/hedge fund grade security

**Setup Process:**
1. Admin installs service (one-time)
2. Admin sets password, configures rules
3. Admin starts service
4. Trader logs in daily → daemon already running
5. Trader can't stop it (requires admin privileges)

**Admin Access:**
- Admin can return anytime to reconfigure rules, accounts, API keys
- Not a "one-time setup" - fully reconfigurable by password holder

### 3. Config File Security
**During Development:**
- Config files in regular user folder (easy iteration)

**Production:**
- Config moved to `C:\ProgramData\RiskManager\`
- Windows ACL permissions (only Admin + SYSTEM can access)
- Trader cannot view or edit config files directly
- Admin CLI elevates with password to modify config

### 4. Architecture Philosophy

**Modular from Day 1:**
- One rule = one file
- No file over 200 lines (hard limit)
- Clear interfaces between modules
- Adding features = adding files (no refactoring existing code)

**Key Principle:** Build architecture complete in Phase 1, add rules incrementally without touching core code.

### 5. Phase-Based Implementation (APPROVED)

**Phase 1: Solid Base + 2-3 Rules**
- Complete architecture (daemon, API, state, CLI)
- 2-3 simple rules (MaxContracts, MaxContractsPerInstrument, SessionBlockOutside)
- Testing infrastructure
- Windows Service setup
- Goal: Finish project #1, understand the system completely

**Phase 2+: Add Rules One by One**
- Each new rule = new file in `rules/`
- No major refactoring needed
- System already designed to handle all rules

### 6. Testing Approach
- **Use Pytest** (NOT full TDD)
- Write tests for core logic (rules, state, P&L tracking)
- Focus on "would a bug cause real money loss?"
- Test after feature works, not before (practical approach for beginners)
- Run tests before commits and deployments

### 7. Data Persistence
- **SQLite database** for state persistence
- Survives computer crashes/reboots
- Stores: P&L, trade counts, cooldown timers, lockout states

---

## Risk Rules to Implement

### Confirmed Rules (detailed requirements needed):
1. **MaxContracts** - Cap net contracts across all instruments
2. **MaxContractsPerInstrument** - Per-symbol caps (e.g., MNQ: 2)
3. **DailyRealizedLoss** - Hard daily realized loss limit
4. **DailyUnrealizedLoss** - Hard floating loss limit
5. **MaxUnrealisedProfit** - Per trade or per account max profit (realized/unrealized, like loss limits)
6. **TradeFrequencyLimit** - Cap trades per hour/session/per minute
7. **CooldownAfterLoss** - Time lockout after loss threshold
8. **NoStopLossGrace** - If no SL after N seconds, enforce
9. **SessionBlockOutside** - Block orders outside session
10. **AuthLossGuard** - On auth loss → warning message
11. **SymbolBlocks** - Can never trade certain symbols (auto-close if filled)
12. **Trade Management** - Auto breakeven rule, auto stop trail

**Notes:**
- Some rules have timers/resets (need to configure reset times)
- Some rules are account-wide, others per-trade
- Some rules lock out trading entirely, others just close positions
- **Rule priorities:** Some rules override others (need clarification)

---

## Trader CLI Requirements

**Real-World Scenario:**
- Wake up, turn on computer
- Risk manager already running (auto-started)
- Open trader CLI to see status
- Trade normally throughout day
- CLI shows enforcements, timers, lockout status

**CLI Display Needs:**
- Connection status (daemon alive, SignalR connected)
- Date/time header
- Clock in/clock out tracking (consistency tracking)
- **Lockout status with colored timers:**
  - Green = OK to trade
  - Yellow = Warning (approaching limit)
  - Red = Locked out (with countdown timer)
- Recent enforcements log (what was enforced, why, when)
- Not verbose - just essential info trader needs to see
- Holiday calendar awareness

**Example of what trader wants to see:**
- "3/3 trades this hour [LOCKED 28m]" ← countdown in red
- Timer hits 0 → turns green → can trade again
- Shows why position was closed: "MaxContracts breach at 14:23:15"

---

## System Architecture

### Complete Directory Structure (Approved):

```
risk-manager/
├── src/
│   ├── core/                           # Core daemon logic
│   │   ├── __init__.py
│   │   ├── daemon.py                   # Main service entry (~100 lines)
│   │   ├── risk_engine.py              # Rule orchestrator (~150 lines)
│   │   ├── rule_loader.py              # Loads rules from config (~80 lines)
│   │   ├── enforcement.py              # Executes actions (~100 lines)
│   │   └── priority_handler.py         # Rule priority logic (~70 lines)
│   │
│   ├── api/                            # TopstepX API integration
│   │   ├── __init__.py
│   │   ├── client.py                   # REST API client (~120 lines)
│   │   ├── signalr_listener.py         # WebSocket event listener (~150 lines)
│   │   ├── auth.py                     # JWT authentication (~60 lines)
│   │   └── position_manager.py         # Position close/flatten (~80 lines)
│   │
│   ├── rules/                          # Risk rules (each rule = 1 file)
│   │   ├── __init__.py
│   │   ├── base_rule.py                # Base class (~60 lines)
│   │   ├── max_contracts.py            # ~90 lines
│   │   ├── max_contracts_per_instrument.py  # ~90 lines
│   │   ├── daily_realized_loss.py      # ~120 lines
│   │   ├── daily_unrealized_loss.py    # ~120 lines
│   │   ├── max_unrealized_profit.py    # ~110 lines
│   │   ├── trade_frequency_limit.py    # ~150 lines
│   │   ├── cooldown_after_loss.py      # ~130 lines
│   │   ├── no_stop_loss_grace.py       # ~100 lines
│   │   ├── session_block_outside.py    # ~90 lines
│   │   ├── auth_loss_guard.py          # ~70 lines
│   │   └── symbol_blocks.py            # ~80 lines
│   │   # (Add more rules here - each is independent)
│   │
│   ├── state/                          # State management & persistence
│   │   ├── __init__.py
│   │   ├── state_manager.py            # In-memory state tracking (~150 lines)
│   │   ├── persistence.py              # SQLite save/load (~120 lines)
│   │   ├── timer_manager.py            # Cooldown/reset timers (~100 lines)
│   │   └── pnl_tracker.py              # P&L calculations (~110 lines)
│   │
│   ├── cli/                            # Command-line interfaces
│   │   ├── __init__.py
│   │   ├── main.py                     # CLI entry point & routing (~80 lines)
│   │   │
│   │   ├── admin/                      # Admin CLI (password-protected)
│   │   │   ├── __init__.py
│   │   │   ├── admin_main.py           # Admin menu (~100 lines)
│   │   │   ├── configure_rules.py      # Rule configuration wizard (~150 lines)
│   │   │   ├── manage_accounts.py      # Account/API key setup (~100 lines)
│   │   │   ├── service_control.py      # Start/stop daemon (~80 lines)
│   │   │   └── auth.py                 # Password verification (~60 lines)
│   │   │
│   │   └── trader/                     # Trader CLI (view-only)
│   │       ├── __init__.py
│   │       ├── trader_main.py          # Trader menu (~80 lines)
│   │       ├── status_screen.py        # Main status display (~120 lines)
│   │       ├── logs_viewer.py          # Enforcement log viewer (~100 lines)
│   │       ├── timer_display.py        # Lockout timer display (~90 lines)
│   │       ├── clock_tracker.py        # Clock in/out tracking (~70 lines)
│   │       └── formatting.py           # Colors, tables, UI helpers (~80 lines)
│   │
│   ├── config/                         # Configuration management
│   │   ├── __init__.py
│   │   ├── loader.py                   # Load/validate YAML (~100 lines)
│   │   ├── validator.py                # Config validation (~90 lines)
│   │   └── defaults.py                 # Default config templates (~60 lines)
│   │
│   ├── utils/                          # Shared utilities
│   │   ├── __init__.py
│   │   ├── logging.py                  # Logging setup (~80 lines)
│   │   ├── datetime_helpers.py         # Time/date utils (~70 lines)
│   │   ├── holidays.py                 # Holiday calendar (~60 lines)
│   │   └── validation.py               # Input validation (~50 lines)
│   │
│   └── service/                        # Windows Service wrapper
│       ├── __init__.py
│       ├── windows_service.py          # Windows Service integration (~120 lines)
│       ├── installer.py                # Service install/uninstall (~100 lines)
│       └── watchdog.py                 # Auto-restart on crash (~80 lines)
│
├── config/                             # Configuration files
│   ├── risk_config.yaml                # Risk rule settings
│   ├── accounts.yaml                   # TopstepX accounts/API keys
│   ├── holidays.yaml                   # Trading holidays calendar
│   └── config.example.yaml             # Example config (for documentation)
│
├── data/                               # Runtime data (gitignored)
│   ├── state.db                        # SQLite database (state persistence)
│   └── backups/                        # State backups
│
├── logs/                               # Log files (gitignored)
│   ├── daemon.log                      # Main daemon log
│   ├── enforcement.log                 # Rule enforcement actions
│   └── error.log                       # Errors only
│
├── tests/                              # Tests (pytest)
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   │
│   ├── unit/                           # Unit tests
│   │   ├── test_rules/                 # Test each rule independently
│   │   │   ├── test_max_contracts.py
│   │   │   ├── test_daily_loss.py
│   │   │   └── (one test file per rule)
│   │   ├── test_state_manager.py
│   │   ├── test_pnl_tracker.py
│   │   └── test_timer_manager.py
│   │
│   └── integration/                    # Integration tests
│       ├── test_full_workflow.py       # End-to-end scenarios
│       ├── test_api_integration.py     # TopstepX API mocking
│       └── test_persistence.py         # State save/load
│
├── docs/                               # Documentation
│   ├── architecture.md                 # System architecture
│   ├── admin_guide.md                  # Admin CLI guide
│   ├── trader_guide.md                 # Trader CLI guide
│   ├── rule_reference.md               # All risk rules explained
│   └── development.md                  # Development guide
│
├── scripts/                            # Utility scripts
│   ├── install_service.py              # Install Windows Service
│   ├── uninstall_service.py            # Remove service
│   └── dev_run.py                      # Run daemon in dev mode (no service)
│
├── .gitignore                          # Git ignore (config, data, logs)
├── .env.example                        # Environment variables example
├── pyproject.toml                      # Python dependencies & config
├── pytest.ini                          # Pytest configuration
├── README.md                           # Project overview
└── requirements.txt                    # Python dependencies (generated from pyproject)
```

**Architecture Principles:**
- **No file over 200 lines** - split immediately if growing too large
- **One rule = one file** - each rule is self-contained and independent
- **CLI highly modularized** - each screen/feature is its own file
- **Clear separation of concerns** - core, api, rules, state, cli, config, utils, service
- **Built to grow** - adding features means adding files, not refactoring existing code

---

## Lessons from Previous 30 Failed Projects

**Why they failed:**
1. Lack of details/clarity (vibe coding without planning)
2. Perfectionist paralysis (nothing felt "right")
3. Too complex, too fast (900-file SDK, async confusion)
4. AI build-then-add problem (messy incremental additions)
5. Lost in the code, too many large steps at once
6. Giving up, restarting projects

**How we're solving it THIS time:**
1. ✅ Detailed upfront planning (this document)
2. ✅ Modular architecture designed to grow (no refactoring spiral)
3. ✅ No SDK - direct API integration (clean, understandable)
4. ✅ Phase-based approach (simple MVP first, add features incrementally)
5. ✅ Small, focused files (< 200 lines, one purpose per file)
6. ✅ Clear documentation (understand everything)
7. ✅ Build "solid base" first, add rules later (working system quickly)

---

## Questions Still to Answer (Next Session)

### 1. Rule Behavior Details
For each rule, need to clarify:
- Exact behavior (what triggers it, what happens)
- Reset timing (daily at 5pm? midnight? session end? configurable?)
- Per-trade vs account-wide
- Enforcement action (close all, close specific, lock out, warning)

### 2. Rule Priorities/Hierarchy
- What happens when multiple rules breach at once?
- Do some rules override others?
- Example: If both DailyLoss and MaxContracts breach, which takes priority?

### 3. Real-World Scenarios
- What happens at end of trading day? (daemon keeps running 24/7)
- What happens on holidays? (no trading, but daemon running)
- What happens if internet/API disconnects? (failsafe behavior?)

### 4. Config File Structure
- How should admin configure complex rules?
- Example: TradeFrequencyLimit (per hour? per session? both?)
- Timer/reset configurations
- Holiday calendar setup

### 5. Phase 1 Scope Confirmation
Are these the right starter rules?
- MaxContracts
- MaxContractsPerInstrument
- SessionBlockOutside

Or different rules?

---

## TopstepX API Capabilities (Verified)

**Real-Time Events (SignalR WebSocket):**
- **User Hub:** Account, order, position, trade updates
- **Market Hub:** Quotes, depth, market trades

**Key Events for Risk Manager:**
- `GatewayUserOrder` - Order status changes
- `GatewayUserPosition` - Position updates
- `GatewayUserTrade` - Trade executions (P&L, fees, price)
- `GatewayUserAccount` - Account balance, canTrade status

**REST API Capabilities:**
- Authentication (JWT tokens via API key)
- Close positions (`POST /api/Position/closeContract`)
- Query orders, positions, trades

**Event Payload Data:**
- Position: accountId, contractId, type (long/short), size, averagePrice
- Trade: price, profitAndLoss, fees, side, size
- Order: status, type, side, limitPrice, stopPrice, fillVolume

**This means:**
- We get instant notification when trader's order fills
- We can calculate P&L from trade events
- We can close positions programmatically
- No polling needed (efficient real-time updates)

---

## Next Steps (When You Return)

1. **Continue Requirements Interview:**
   - Deep dive into each risk rule's behavior
   - Clarify reset timers, priorities, enforcement actions
   - Define config file structure

2. **Finalize Architecture Document:**
   - Complete technical specifications
   - Define all data models
   - Specify exact config file format

3. **Get Your Approval:**
   - Review complete plan
   - Confirm scope and approach
   - Make any final adjustments

4. **Begin Phase 1 Implementation:**
   - Start building the solid base
   - Get first 2-3 rules working
   - Test thoroughly

---

## Important Reminders

- **No 200-line+ files** - split immediately if growing too large
- **One rule = one file** - easy to add, easy to understand
- **Modular from day 1** - no refactoring spiral
- **Test before deploy** - pytest before commits
- **Document everything** - you should understand all code
- **Phase-based approach** - finish Phase 1 completely before Phase 2

---

## User Context

- **Skill Level:** Beginner, learning as going
- **Solo developer:** No team, just you
- **Knows basics:** Understands development fundamentals
- **Perfectionist:** Wants to understand everything deeply
- **Learning async:** Previously struggled with async SDK complexity
- **Windows user:** Need Windows Service solution
- **Trader role:** You are the trader (not admin password holder)
- **Admin role:** Friend/spouse/someone else holds password

---

**STATUS: Ready to resume requirements interview when you return.**

When you're back, we'll dive into the detailed behavior of each risk rule, clarify timers/resets, and finalize the architecture document. Then we'll be ready to start building Phase 1!
