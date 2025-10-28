# Conflicts Requiring User Decision

**Purpose**: Resolve specification conflicts with your authoritative guidance before Wave 3 researchers create unified specs.

**Instructions**: For each conflict below, read both versions and answer the question. Your answers will be Resolution Rule #1 (highest authority).

---

## CONFLICT-001: RULE-004 (DailyUnrealizedLoss) - Enforcement Type

### The Conflict

**Version A** (Primary Spec - `docs/PROJECT_DOCS/rules/RULE-004.md`, 2025-01-17):
- **Enforcement**: Hard Lockout
- **Behavior**: Lock account until daily reset (5:00 PM ET)
- **Description**: "Close all open positions and lock account from further trading until reset"

**Version B** (Categories Doc - `docs/current/RULE_CATEGORIES.md`, 2025-10-23):
- **Enforcement**: Trade-by-Trade
- **Behavior**: Close only the losing position, allow continued trading
- **Description**: "Corrected enforcement categories" (explicitly says this corrects earlier specs)

### Context
- Categories doc is 8 months newer
- Categories doc explicitly says it "corrects" earlier categorizations
- Trade-by-Trade is more granular (less restrictive)
- Hard Lockout is more protective (more restrictive)

### Question 1: RULE-004 Enforcement
When daily unrealized loss hits the limit (-$500), should the system:

**Option A**: Close ALL positions + lock account until 5:00 PM ET reset (Hard Lockout)
**Option B**: Close ONLY the losing position + allow continued trading (Trade-by-Trade)
**Option C**: Make it configurable (both modes available via config)

**Your answer**: unrelaised loss/profit are trade by trade, not a hard lockout/reset schedule. it also doesnt "close all positions" it closes that specific positon. think of it like im in a trade, its open, the pnl is floating/live and flucuating up and down. thats unrealised pnl. when it hits my configurd limit, -200 or +200, it lcoses that position. they key thing to understand tho is that realised profit/loss for daily IS on a lockout. this is profit o loss that ive already closed out on, its my real pnl, not floating. when i set risk config for these realised profit and relaised loss, say -1000, or +1000, when the total REALISED + UNREALISED COME TOGETHER TO HIT MY REALISED, IT CLOSES ALL POSITIONS ACCOUNT WIDE, BECAUSE IF A RISK LIMIT IS BREACHED, WE MUST CLOSE ALL POSITIONS ACCOUNT WIDE, AND LOCKOUT MEANS > CLOSE POSITIONS ACCOUNT WIDE + IF THE TRADER TRIES TO KEEP TRADING, ITS IN LOCKOUT MDOE = CLOSE ALL POSITIONS ON ANY NEW TRADE EVENT IMMEDIATELY UNTIL TIME RESET. SO MY RESET SCHEDLES/TIMERS, ALL THAT CAN BE CONFIGURED SO SAY 5PM > 5PM THE NEXT DAY, CHICAGO. SOMEHTING LIKE THAT. SO REALISED = HARD LOCKOUT, UNRELAISED = TRADE BY TRADE OR UNTIL UNREALISED + REALISED = REALISED BREACH. BECAUSE ONCE WE CLOSE THOSE UNREALISED POSITIONS, REGARDLESS IF THEY REACHED THEIR RISK LIMIT TO TRIGGER A CLOSE, THE UNREALISED WILL BE AT ITS LIMIT BEFORE THE UNREALISED. WE NEED QUOTE DATA TO CALUCLATE UNREALISED I BLEIVE, PROJECT-X-PY CAN HANDLE QUOTE DATA BUT I BLEIEV WE NEED PNL TRACKING CAPAPBILTIES FOR RELAISED AND UNREALSIED. 

---

## CONFLICT-002: RULE-005 (MaxUnrealizedProfit) - Enforcement Type

### The Conflict

**Version A** (Primary Spec - `docs/PROJECT_DOCS/rules/RULE-005.md`):
- **Enforcement**: Hard Lockout
- **Behavior**: Lock account until daily reset
- **Description**: "Close all positions and lock account when profit target hit"

**Version B** (Categories Doc - `docs/current/RULE_CATEGORIES.md`):
- **Enforcement**: Trade-by-Trade
- **Behavior**: Close only the winning position, allow continued trading
- **Description**: "Corrected enforcement categories"

### Context
- This is a profit TAKING rule (when you're UP too much)
- Some traders want to lock in profits and stop (Hard Lockout)
- Some traders want to take profits but keep trading (Trade-by-Trade)
- Both approaches have merit depending on trading strategy

### Question 2: RULE-005 Enforcement
When unrealized profit hits the target (+$1000), should the system:

**Option A**: Close ALL positions + lock account until 5:00 PM ET reset (Hard Lockout)
**Option B**: Close ONLY the winning position + allow continued trading (Trade-by-Trade)
**Option C**: Make it configurable (both modes available via config)

**Your answer**: READ THE CONFLICT 1 ANSWER 

---

## CONFLICT-003: RULE-013 (DailyRealizedProfit) - Missing Specification

### The Conflict

**Current State**:
- RULE-013 is mentioned in multiple documents
- NO dedicated specification file exists
- Information is scattered across 3+ documents
- Cannot implement without complete spec

**What We Know**:
- Purpose: Track daily realized profit (opposite of RULE-003 daily realized loss)
- Trigger: When realized profit >= target (e.g., +$1000)
- Enforcement: ??? (not clearly specified)
- Reset: Daily at 5:00 PM ET
- Similar to RULE-003 but opposite direction

### Question 3A: RULE-013 Enforcement
When daily realized profit hits the target (+$1000), should the system:

**Option A**: Close ALL positions + lock account until 5:00 PM ET reset
**Option B**: Close ONLY the winning position + allow continued trading
**Option C**: Just log/alert, no enforcement (informational only)
**Option D**: Make it configurable

**Your answer**: READ QUESTION 1 ANSWER. 

### Question 3B: RULE-013 Purpose
What is the business purpose of this rule?

**Option A**: Profit protection (lock in profits, prevent giving them back)
**Option B**: Discipline enforcement (stop trading after hitting target)
**Option C**: Account preservation (prevent overtrading after wins)
**Option D**: Other (please explain): _____________________

**Your answer**: AGAIN READ CONFLICT 1 ANSWER. 

---

## CONFLICT-004: Architecture v1 vs v2

### The Conflict

**Version 1** (Original - `docs/PROJECT_DOCS/architecture/system_architecture_v1.md`):
- Basic modular architecture
- Single-account focus
- Manual API integration
- 4 core modules

**Version 2** (Evolved - `docs/PROJECT_DOCS/architecture/system_architecture_v2.md`):
- Advanced multi-account support
- SDK-first integration
- Enhanced state management
- Same 4 core modules but more sophisticated

### Context
- v2 is the evolution of v1
- v2 written AFTER SDK became available
- v2 supports multiple traders (multi-account)
- v2 is more production-ready

### Question 4: Architecture Version
Which architecture should be the authoritative specification?

**Option A**: Use v1 (simpler, original design intent)
**Option B**: Use v2 (evolved, production-ready, SDK-first)
**Option C**: Merge both (document evolution from v1 → v2)

**Your answer**: WE FOLLOW V2 WHATEVER THE SDK CAN HANDLE YES THE PROJECT-X-PY SDK.

---

## CONFLICT-005: Admin Unlock Model

### The Conflict

**Your Guidance** (from earlier in conversation):
- ❌ Admin does NOT manually unlock accounts for trading
- ✅ Admin configures risk settings (locked from trader)
- ✅ System auto-enforces via reset schedules, timers, API events

**What Specs Say** (multiple documents):
- RULE-003: "Lock account until admin manually unlocks"
- RULE-009: "Admin can override session lockout"
- RULE-010: "Admin unlock required for AuthLossGuard"
- RULE-013: "Admin unlock after profit target"

### Context
- You already clarified: NO admin unlock for trading
- Specs contradict your architectural intent
- Need to correct all specs to use automatic unlock mechanisms

### Question 5: Admin Unlock Mechanisms
For each rule that mentioned "admin unlock", what should the ACTUAL unlock mechanism be?

PER THE UAC, AND THE ADMIN CLI, ADMIN CONFIGURES THE ACCOUNTS, API, RISK RULES, TIMERS, SCHEDILES ETC. THE ADMIN CAN ONLY CHNAGE THESE, THE TRADER IS LOCKED OUT. THE TRADER WILL TRADE FROM A DIFFERETN WINDOWS ACCOUNTS, A REGULAR USER ACCOUNT WITHOUT ADMIN PRIVELAGES. SO THE SETTIIINGS ARE LOCKED OUT FORM THE TRADER. BUT THE ADMIN CREATES THE SETTINGS FOR THE TRADERS ACCOUNT 

**RULE-003 (DailyRealizedLoss)**:
- Current spec: "Admin manually unlocks"
- Should be: I ANSWERED THESE ALREADY. 
  - Example options: "Auto-unlock at 5:00 PM ET daily reset", "Auto-unlock at midnight", "Auto-unlock at session start"

**RULE-009 (SessionBlockOutside)**:
- Current spec: "Admin can override"
- Should be: _____________________
  - Example options: "Auto-unlock at next session start", "Auto-unlock when session window opens"

**RULE-010 (AuthLossGuard)**:
- Current spec: "Admin unlock required"
- Should be: _____________________
  - Example options: "Auto-unlock when API sends canTrade: true", "Auto-unlock at daily reset"

**RULE-013 (DailyRealizedProfit)**:
- Current spec: "Admin unlock after profit target"
- Should be: _____________________
  - Example options: "Auto-unlock at 5:00 PM ET daily reset", "Auto-unlock at midnight"

ANSWER TO ALL: ADMIN DOESNT UNLCK RISK SETTING LOCKOUTS, THEY AR EON A TIMER/SCHEUDLE, AUTO CONTROLLED EVERYDAY. OR WHATEVER THE SCHEUDLE/TIMERS ARE SET TOO. 



## CONFLICT-006: CLI Admin Commands - Scope

### The Conflict

**Not clear from specs**: What CAN admin do via CLI?

**Mentioned in various docs**:
- Configure risk rules (enable/disable, change limits)
- View system status
- View logs
- Control Windows Service (start/stop/restart)
- Unlock accounts ← **YOU SAID NO to this for trading**
- Emergency stop

### Question 6A: Admin CLI - Account Unlock Command
Should the admin CLI have an "unlock account" command?

**Context from your guidance**:
- You said: "admin should never need to unlock the accounts for trading"
- But what about: Emergency situations? Testing? Fixing bugs?

**Option A**: NO unlock command at all (accounts only unlock via automatic mechanisms)
**Option B**: YES unlock command, but ONLY for emergency/testing (not normal operations)
**Option C**: YES unlock command, but requires confirmation + logs the override
**Option D**: Other (please explain): _____________________

**Your answer**: I HAVE ALREADY KIND OF EPXLAINIED THIS, LOCKOUTS ARE ON AN AUTO SCHEUDLE. WHILE ADMIN CLI PRIVELAGES ARE LOCKED FORM TRADER TO CHNAGE THEM. ALSO, ADMIN DOES NOT NEED TO SEE LOGS. 

### Question 6B: Admin CLI - Emergency Stop
Should admin CLI have an "emergency stop" command that:
- Closes all open positions immediately
- Locks account from trading
- Overrides all rules

**Option A**: Yes, emergency stop should exist (safety feature)
**Option B**: No, too dangerous (could be abused)
**Option C**: Yes, but requires multi-factor confirmation (password + confirmation prompt)

**Your answer**: NOT REALLY NO,PART OF WHAT THE ADMIN CLI DOES IS START/STOP DAMEON PROCESS, ESENTIALLY WHAT EVEYRHTING IS WWRAPPED IN. THINK ABOUT IT. ADMIN SETS UP/CAN EDIT API INFO, ACCOUNT INFO TO BE MONITORED, RISK RULES, SHCEUDLES, TIMERS ETC. WE HAVE CONFIG LAYOUTS FOR THIS ALREADY. EACH RISK RULE GETS A TYPE OF LOCKOOUT/SCHEUDLE/TIMER ETC. ONCE THE ADMIN STARTS THE DEAMEON, IT SHOULD AUTO START, WITHOUT ADMIN, ON EVERY COMPUTER START UP, LOGIN. SO THINK ABOUT IT, THE AMDIN CONFIGURES SETTINGS, STARTS DAMEON, SHUTS OFF OCMPUTER, THEN THE NEXT DAY AND WEEKS LATER, EVEYRDAY THE TRADER LOGS IN AND OPENS CLI TRADER TO TRADE AND VIEW THEIR BREACHES ETC. THEN THE ADMIN LATER COMES IN WHEBVER, FOR EXAMPLE, THE ACOCUNT HAS GROWN ALOT, MAYEB THE ADMIN WANTS TO ALLOW THE TRADER TO RISK MORE OR CHNAGE THE LIMITS OR SOMETHING, THEY CAN LOAD IN WITH UAC, CONFIGURE HIGHER LIMITS, RESTART THE DAMOEN SO THAT IT LOADS THE NEW SETTINGS, THEN THE PROCESS CONTINUES. SO THE ADMIN STARTS A RUNNING PROCESS, SO THAT WHEN THE TRADER USES TRADER CLI EVEYRDAY, THE RISK MANAGER IS ALWAYS RUNNINGS MONITORIGN ACCOUNT ,BRACHES, ENFROCMENT ETC. AMDIN SHOULD ALSO BE ABLE TO CHECK STATUS OF DAMOEN, SAME WITH THE TRADER > IS THE DAMOEN RUNNING , ARE MY ACOCUNT SBEING MONITORED? IF ACCOUNTS ARENT BEING MONITORED, THEN WE NEED OT FIX THE CODE. 

### Question 6C: Admin CLI - Configuration Changes
When admin changes risk configuration via CLI (e.g., changes daily loss limit from $500 to $1000), when does it take effect?

**Option A**: Immediately (live reload, no restart)
**Option B**: After service restart (safer, prevents mid-session changes)
**Option C**: At next daily reset (5:00 PM ET) - no mid-session changes
**Option D**: Configurable per setting (some immediate, some at reset)

**Your answer**: IT SHOULD BE A LIVE RELOAD OR A RESTART, DOESNT MATTER BUT MAKE SURE ITS CLEAR. 

---

## CONFLICT-007: Trader CLI - Read-Only or Not?

### The Conflict

**Specs say**: Trader CLI is "view-only" (can only read status, cannot modify anything)

**But unclear**:
- Can trader pause/resume their own trading?
- Can trader request account unlock (requires admin approval)?
- Can trader acknowledge violations (mark as "seen")?
- Can trader export data (P&L reports, violation history)?

### Question 7: Trader CLI Capabilities
What CAN the trader do via their CLI?

**Definitely YES** (already specified):
- ✅ View current status (P&L, positions, risk limits)
- ✅ View violation history
- ✅ View logs
- ✅ View lockout status

**Unclear - Your Decision**:
- Can trader pause their own trading? (self-imposed break): YES / NO
- Can trader resume after self-pause?: YES / NO
- Can trader request admin to unlock (creates ticket)?: YES / NO
- Can trader acknowledge violations (mark as read)?: YES / NO
- Can trader export reports (P&L, violations to CSV)?: YES / NO

**Your answers**:
- Pause own trading: _____________________
- Resume after self-pause: _____________________
- Request admin unlock: _____________________
- Acknowledge violations: _____________________
- Export reports: _____________________

--- TRADER cannot pause the dameon or risk manager, its always active only the amdin can start/stop it. no tickets for reuqsting.
trader can see whats settings are configured, they can see a live snapshot of their floating unrelaised pnl and realised pnl. they can see logs for WHY A POSITION WAS ENFORCED, SHOWING WHAT RISK RULE WAS BREACHED! no verbose. they can clock in and out, they can see holidays, current time, when market opens or closes or is active, or when their account is locked out and why, or if its not locked out. i dont need much mroe than that !
## CONFLICT-008: Windows UAC Security - Service Control

### The Conflict

**Specs say**:
- Service runs as LocalSystem (highest privilege)
- Trader cannot kill service (protected by Windows)
- Admin can control service via UAC elevation

**But unclear**:
- Can trader see the service in Task Manager? (visible but unkillable?)
- Can trader restart their own machine? (forces service restart)
- What happens if trader uses "shutdown -r -f -t 0"? (forced reboot)

### Question 8A: Service Visibility
Should the Risk Manager Windows Service be:

**Option A**: Visible in Task Manager (trader can see it but cannot kill it)
**Option B**: Hidden from Task Manager (trader doesn't even see it exists)
**Option C**: Visible with warning message ("Protected service - Admin rights required")

**Your answer**: THE TRADER SHOULD NEVER BEABLE TO SHUT DOWN THE CLI VIA ANYTHIGN. CANNOT KILL INSIDE TASK MANAGER WITHOUT UAC PRIVELAGE, ADMIN PASSWORD. IF THE TRADER SHUTS DOWN THIER COMPUTER, RISK MANAGER/DAMEON RESTARTS AND CONTINUES MONITORING ACOCUNT. ONLY THE ADMIN CAN STOP IT WITH ADMIN PASSWORD!!!!!!!!!!!!!!!!!! 

### Question 8B: Forced Restart Protection
If trader forces a system reboot (power button, shutdown -f, etc.), what happens?

**Option A**: Service auto-starts on boot (protection resumes immediately)
**Option B**: Service auto-starts + logs "forced reboot detected" (audit trail)
**Option C**: Service auto-starts + locks account temporarily (suspicious activity)
**Option D**: Service requires admin to manually restart (safety check)

**Your answer**: OPTION A 

---

## CONFLICT-009: Configuration File Protection

### The Conflict

**Specs say**:
- Config files protected by Windows ACL (admin-only write)
- Trader has read-only access

**But what if**:
- Trader copies config files to another location?
- Trader edits local copy and tries to swap files?
- Trader deletes config files?

### Question 9: Config File Tampering
If trader attempts to modify/delete config files (denied by ACL), should the system:

**Option A**: Silent fail (Windows denies, system continues normally)
**Option B**: Log the attempt (security audit, no action)
**Option C**: Lock account + alert admin (suspicious activity detected)
**Option D**: Just ignore (Windows ACL prevents it anyway)

**Your answer**: OPTION A, OPTION d? IF WINDOWS UAC DENIES IT THEN OKAY,MAKE SURE THE TRADER CANNOT EDIT ANYTHING WITHOUT UAC.

---

## CONFLICT-010: Reset Schedule - Which Timezone?

### The Conflict

**Specs mention**:
- Daily reset at "5:00 PM ET" (Eastern Time)
- Daily reset at "midnight ET"
- Daily reset at "end of trading day"

**All different times!**

### Question 10: Daily Reset Time
What is the EXACT reset time for daily metrics (realized P&L, unrealized P&L, trade counts)?

**TopstepX Context** (if you know):
- What time does TopstepX reset their daily metrics?
- What timezone do they use?

**Your answer**:
- Reset time: _____________________ (e.g., "5:00 PM ET", "midnight ET", "6:00 PM ET")
- Rationale: _____________________

---I SHOUOLD BE ABLLE TO CONFIGURE THIS INSIDE CONFIGS!!!!!!!!!!

#
