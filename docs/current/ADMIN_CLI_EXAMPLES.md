# Admin CLI Usage Examples

Real-world examples and scenarios for using the Admin CLI.

## Quick Reference

```bash
# View all commands
python admin_cli.py --help

# Service management
python admin_cli.py service status
python admin_cli.py service start        # Requires admin
python admin_cli.py service stop         # Requires admin
python admin_cli.py service restart      # Requires admin

# Configuration
python admin_cli.py config show
python admin_cli.py config validate
python admin_cli.py config edit          # Requires admin
python admin_cli.py config reload        # Requires admin

# Rules
python admin_cli.py rules list
python admin_cli.py rules enable max_contracts     # Requires admin
python admin_cli.py rules disable symbol_blocks    # Requires admin

# Lockouts
python admin_cli.py lockouts list
python admin_cli.py lockouts history
python admin_cli.py lockouts remove PRAC-V2-126244  # Requires admin

# Monitoring
python admin_cli.py status
python admin_cli.py logs
python admin_cli.py logs --tail 100
python admin_cli.py logs --follow
```

---

## Scenario 1: Initial Setup

**Goal**: Install and configure Risk Manager for the first time.

```bash
# Step 1: Create configuration from template
copy config\risk_config.yaml.template config\risk_config.yaml

# Step 2: Edit configuration
python admin_cli.py config edit
# (Opens in editor - configure your rules)

# Step 3: Validate configuration
python admin_cli.py config validate

# Step 4: Check rules are configured correctly
python admin_cli.py rules list

# Step 5: Install Windows service (as admin)
python admin_cli.py service install

# Step 6: Start service (as admin)
python admin_cli.py service start

# Step 7: Verify service is running
python admin_cli.py service status

# Step 8: Monitor startup logs
python admin_cli.py logs --follow
# (Ctrl+C to stop)
```

---

## Scenario 2: Daily Loss Limit Hit

**Situation**: Account PRAC-V2-126244 hit daily loss limit and is locked out.

### Check Status
```bash
# 1. View active lockouts
python admin_cli.py lockouts list

# Expected output:
# ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
# ┃ Account ID       ┃ Reason                ┃ Locked At          ┃ Expires    ┃
# ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
# │ PRAC-V2-126244   │ RULE-003: Daily Loss  │ 2025-10-28 09:00  │ Until Reset│
# └──────────────────┴───────────────────────┴────────────────────┴────────────┘

# 2. Check system status
python admin_cli.py status
```

### Option A: Wait for Daily Reset (Recommended)
The account will automatically unlock at the daily reset time (configured in `timers_config.yaml`).

```bash
# Monitor reset time in config
python admin_cli.py config show

# Check lockout history
python admin_cli.py lockouts history --account PRAC-V2-126244
```

### Option B: Emergency Unlock (Admin Override)
**Warning**: Only use in emergencies. This bypasses risk protections.

```bash
# Remove lockout (requires admin)
python admin_cli.py lockouts remove PRAC-V2-126244

# Confirm prompt:
# Are you sure you want to unlock PRAC-V2-126244? [y/N]: y

# Verify unlocked
python admin_cli.py lockouts list
```

---

## Scenario 3: Adjust Daily Loss Limit

**Goal**: Change daily loss limit from $500 to $750.

```bash
# Step 1: View current configuration
python admin_cli.py config show

# Step 2: Edit configuration (as admin)
python admin_cli.py config edit

# In the editor, find:
# rules:
#   daily_realized_loss:
#     limit: -500.0

# Change to:
# rules:
#   daily_realized_loss:
#     limit: -750.0

# Save and close editor

# Step 3: Validate changes
python admin_cli.py config validate

# Step 4: Reload configuration (restart service)
python admin_cli.py config reload

# Step 5: Verify change applied
python admin_cli.py config show
```

---

## Scenario 4: Enable Symbol Blacklist

**Goal**: Block trading in ES and NQ symbols.

```bash
# Step 1: Check if rule exists
python admin_cli.py rules list
# Look for: RULE-011: Symbol Blocks

# Step 2: Edit configuration (as admin)
python admin_cli.py config edit

# In the editor, find:
# rules:
#   symbol_blocks:
#     enabled: false
#     blocked_symbols: []

# Change to:
# rules:
#   symbol_blocks:
#     enabled: true
#     blocked_symbols: ['ES', 'NQ']

# Save and close

# Step 3: Validate
python admin_cli.py config validate

# Step 4: Reload
python admin_cli.py config reload

# Step 5: Verify enabled
python admin_cli.py rules list
# Should show RULE-011 as ENABLED
```

---

## Scenario 5: Temporarily Disable a Rule

**Goal**: Temporarily disable trade frequency limits.

```bash
# Step 1: Check current status
python admin_cli.py rules list
# Find: RULE-006: Trade Frequency Limit

# Step 2: Disable rule (as admin)
python admin_cli.py rules disable trade_frequency_limit

# Output:
# Disabling rule: trade_frequency_limit...
# Rule disabled: trade_frequency_limit
# Remember to reload configuration: admin_cli config reload

# Step 3: Reload configuration
python admin_cli.py config reload

# Step 4: Verify disabled
python admin_cli.py rules list
# RULE-006 should show DISABLED

# Later: Re-enable
python admin_cli.py rules enable trade_frequency_limit
python admin_cli.py config reload
```

---

## Scenario 6: Service Not Starting

**Problem**: Service fails to start after configuration change.

```bash
# Step 1: Check service status
python admin_cli.py service status

# Step 2: View recent logs for errors
python admin_cli.py logs --tail 100

# Look for ERROR or WARN messages near the end

# Step 3: Validate configuration
python admin_cli.py config validate

# If validation fails, fix the errors:
python admin_cli.py config edit

# Step 4: Try starting again
python admin_cli.py service start

# Step 5: Monitor startup
python admin_cli.py logs --follow
```

---

## Scenario 7: Monitor Live Trading

**Goal**: Watch logs in real-time during trading session.

```bash
# Terminal 1: Follow logs
python admin_cli.py logs --follow

# Terminal 2: Monitor status
while true; do python admin_cli.py status; sleep 30; done

# Terminal 3: Watch lockouts
while true; do python admin_cli.py lockouts list; sleep 60; done
```

---

## Scenario 8: After-Hours Configuration Change

**Best Practice**: Make configuration changes outside trading hours.

```bash
# Step 1: Check current trading session
python admin_cli.py config show
# Note session hours

# Step 2: Wait until after session close
# (e.g., wait until 4:00 PM if session ends at 3:00 PM)

# Step 3: Stop service (as admin)
python admin_cli.py service stop

# Step 4: Edit configuration
python admin_cli.py config edit

# Step 5: Validate changes
python admin_cli.py config validate

# Step 6: Start service
python admin_cli.py service start

# Step 7: Verify startup
python admin_cli.py logs --tail 50
```

---

## Scenario 9: Check Lockout History for Account

**Goal**: Review all past lockouts for an account.

```bash
# View all lockouts for account
python admin_cli.py lockouts history --account PRAC-V2-126244

# View last 100 lockouts across all accounts
python admin_cli.py lockouts history --limit 100

# Export to file for analysis
python admin_cli.py lockouts history --limit 1000 > lockout_report.txt
```

---

## Scenario 10: Batch Enable/Disable Rules

**Goal**: Enable multiple rules at once.

```bash
# Create a batch script (enable_all_rules.bat)
@echo off
python admin_cli.py rules enable max_contracts
python admin_cli.py rules enable max_contracts_per_instrument
python admin_cli.py rules enable daily_realized_loss
python admin_cli.py rules enable daily_unrealized_loss
python admin_cli.py rules enable max_unrealized_profit
python admin_cli.py rules enable trade_frequency_limit
python admin_cli.py rules enable cooldown_after_loss
python admin_cli.py rules enable session_block_outside
python admin_cli.py rules enable auth_loss_guard
python admin_cli.py rules enable daily_realized_profit
python admin_cli.py config reload
echo All rules enabled!

# Run batch script (as admin)
enable_all_rules.bat
```

---

## Scenario 11: Pre-Flight Check Before Trading

**Daily routine before live trading**.

```bash
# 1. Check service is running
python admin_cli.py service status

# 2. Verify no unexpected lockouts
python admin_cli.py lockouts list

# 3. Check system status
python admin_cli.py status

# 4. Verify rules are enabled
python admin_cli.py rules list

# 5. Check recent logs for issues
python admin_cli.py logs --tail 50

# If all green, ready to trade!
```

---

## Scenario 12: Backup Configuration

**Goal**: Backup configuration before making changes.

```bash
# Windows
copy config\risk_config.yaml config\risk_config.yaml.backup
copy config\accounts.yaml config\accounts.yaml.backup

# With timestamp
set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%
copy config\risk_config.yaml "config\backups\risk_config_%timestamp%.yaml"

# Restore if needed
copy config\risk_config.yaml.backup config\risk_config.yaml
python admin_cli.py config reload
```

---

## Scenario 13: Debug Configuration Validation Errors

**Problem**: Configuration validation fails with cryptic error.

```bash
# Step 1: Try to validate
python admin_cli.py config validate

# Error output example:
# ╭───────────── Validation Failed ───────────────╮
# │ daily_realized_loss.limit must be negative   │
# ╰───────────────────────────────────────────────╯

# Step 2: Open config to find the error
python admin_cli.py config edit

# Step 3: Find the rule mentioned in error
# Search for: daily_realized_loss

# Step 4: Fix the error
# Wrong: limit: 500.0
# Right: limit: -500.0  (must be negative)

# Step 5: Validate again
python admin_cli.py config validate

# Repeat until validation passes
```

---

## Scenario 14: Multi-Account Monitoring

**Goal**: Monitor multiple accounts simultaneously.

```bash
# 1. Check all account statuses
python admin_cli.py status

# 2. View lockouts across all accounts
python admin_cli.py lockouts list

# 3. Check lockout history
python admin_cli.py lockouts history --limit 100

# 4. View logs for all accounts
python admin_cli.py logs --follow
# (All account events will be interleaved)
```

---

## Scenario 15: Test Configuration in Practice Mode

**Goal**: Test new configuration on practice account before live.

```bash
# Step 1: Create test configuration
copy config\risk_config.yaml config\risk_config_test.yaml

# Step 2: Edit test config
notepad config\risk_config_test.yaml

# Step 3: Temporarily point to test config
# (Edit accounts.yaml to use risk_config_test.yaml for practice account)

# Step 4: Reload
python admin_cli.py config reload

# Step 5: Monitor practice account trading
python admin_cli.py logs --follow

# Step 6: If successful, apply to live
copy config\risk_config_test.yaml config\risk_config.yaml
python admin_cli.py config reload
```

---

## Power User Tips

### 1. Command Aliases (PowerShell)
```powershell
# Add to PowerShell profile
function rm-status { python admin_cli.py status }
function rm-logs { python admin_cli.py logs --follow }
function rm-rules { python admin_cli.py rules list }
function rm-lockouts { python admin_cli.py lockouts list }

# Usage:
rm-status
rm-logs
```

### 2. Scheduled Status Check (Task Scheduler)
```batch
REM check_status.bat
@echo off
python admin_cli.py service status > status.txt
python admin_cli.py lockouts list >> status.txt
python admin_cli.py status >> status.txt
echo Status check completed at %date% %time% >> status.txt
```

### 3. Log Monitoring Script
```batch
REM monitor.bat
@echo off
:loop
cls
echo ======================================
echo Risk Manager Status - %time%
echo ======================================
python admin_cli.py status
echo.
echo Recent Logs:
python admin_cli.py logs --tail 10
timeout /t 30 /nobreak > nul
goto loop
```

### 4. Quick Health Check
```batch
REM health_check.bat
@echo off
echo Checking Risk Manager health...
python admin_cli.py service status || goto error
python admin_cli.py config validate || goto error
echo All checks passed!
goto end
:error
echo Health check FAILED!
:end
```

---

## Troubleshooting Commands

### Service Won't Start
```bash
python admin_cli.py service status
python admin_cli.py config validate
python admin_cli.py logs --tail 100
```

### Account Stuck in Lockout
```bash
python admin_cli.py lockouts list
python admin_cli.py lockouts history --account <ID>
python admin_cli.py logs --tail 50  # Check why locked
```

### Rules Not Working
```bash
python admin_cli.py rules list  # Check enabled
python admin_cli.py config show  # Check settings
python admin_cli.py config validate  # Check syntax
```

### Logs Not Updating
```bash
python admin_cli.py service status  # Is service running?
dir data\logs\risk_manager.log  # Does file exist?
python admin_cli.py logs --follow  # Watch for updates
```

---

## Integration Examples

### Python Script Integration
```python
import subprocess
import json

# Check service status
result = subprocess.run(
    ['python', 'admin_cli.py', 'service', 'status'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("Service is healthy")
else:
    print("Service has issues")
```

### PowerShell Integration
```powershell
# Check if service running
$status = python admin_cli.py service status
if ($LASTEXITCODE -eq 0) {
    Write-Host "Service OK" -ForegroundColor Green
} else {
    Write-Host "Service Error" -ForegroundColor Red
}
```

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0-alpha
