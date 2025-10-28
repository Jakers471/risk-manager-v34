# Admin CLI Guide

Complete reference for the Risk Manager V34 Admin CLI.

## Overview

The Admin CLI provides complete control over the Risk Manager service, including:
- Service control (start, stop, restart, status)
- Configuration management (view, edit, validate)
- Rule management (enable, disable, configure)
- Lockout management (list, remove, history)
- System monitoring (status, logs)

## Installation

The Admin CLI is included with Risk Manager V34. No separate installation needed.

**Entry Point**: `admin_cli.py` in the project root

## Administrator Privileges

Most commands require Windows administrator privileges (UAC elevation).

**To run as administrator**:
1. Open Command Prompt or PowerShell as Administrator:
   - Right-click Command Prompt
   - Select "Run as administrator"
2. Run commands: `python admin_cli.py <command>`

**Commands that require admin**:
- `service start`, `service stop`, `service restart`
- `service install`, `service uninstall`
- `config edit`, `config reload`
- `rules enable`, `rules disable`, `rules configure`
- `lockouts remove`

**Commands that don't require admin** (read-only):
- `service status`
- `config show`, `config validate`
- `rules list`
- `lockouts list`, `lockouts history`
- `status`
- `logs`

## Command Reference

### Service Control

#### `service status`
Check if the Risk Manager service is running.

```bash
python admin_cli.py service status
```

**Example Output**:
```
Service Status
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Property   ┃ Value              ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Service    │ SimpleRiskManager  │
│ Status     │ Running            │
│ Start Type │ Automatic          │
│ Uptime     │ 2h 45m             │
└────────────┴────────────────────┘
```

#### `service start`
Start the Risk Manager service. **Requires admin**.

```bash
python admin_cli.py service start
```

#### `service stop`
Stop the Risk Manager service. **Requires admin**.

```bash
python admin_cli.py service stop
```

#### `service restart`
Restart the Risk Manager service. **Requires admin**.

```bash
python admin_cli.py service restart
```

#### `service install`
Install Risk Manager as Windows service. **Requires admin**.

```bash
python admin_cli.py service install
```

This will:
- Register Risk Manager as Windows service
- Configure auto-start on boot
- Set service recovery options
- Configure Windows ACL permissions

#### `service uninstall`
Uninstall Risk Manager Windows service. **Requires admin**.

```bash
python admin_cli.py service uninstall
```

**Warning**: This will remove the service completely.

---

### Configuration Management

#### `config show`
Display current configuration.

```bash
python admin_cli.py config show
```

**Example Output**:
```
╭──────────────────── General Settings ─────────────────────╮
│ Instruments: MNQ, ES                                      │
│ Timezone: America/Chicago                                 │
│ Log Level: INFO                                           │
╰───────────────────────────────────────────────────────────╯

╭────────────────────── Rule Status ────────────────────────╮
│ Enabled (10):                                             │
│   - max_contracts                                         │
│   - max_contracts_per_instrument                          │
│   - daily_realized_loss                                   │
│   ...                                                     │
│                                                           │
│ Disabled (3):                                             │
│   - symbol_blocks                                         │
│   - trade_management                                      │
╰───────────────────────────────────────────────────────────╯
```

#### `config edit`
Open configuration file in default editor. **Requires admin**.

```bash
python admin_cli.py config edit
```

Opens `config/risk_config.yaml` in your default YAML editor.

**After editing**:
1. Validate changes: `python admin_cli.py config validate`
2. Reload service: `python admin_cli.py config reload`

#### `config validate`
Validate configuration file syntax.

```bash
python admin_cli.py config validate
```

**Example Output (Success)**:
```
╭───────────── Validation Success ──────────────╮
│ Configuration is valid!                       │
│                                               │
│ File: config/risk_config.yaml                 │
│ Rules: 13 configured                          │
│ Instruments: 2                                │
╰───────────────────────────────────────────────╯
```

**Example Output (Failure)**:
```
╭───────────── Validation Failed ───────────────╮
│ Configuration validation failed!              │
│                                               │
│ Error: daily_realized_loss.limit must be     │
│ negative (got: 500.0)                         │
│                                               │
│ Please fix the errors and try again.          │
╰───────────────────────────────────────────────╯
```

#### `config reload`
Reload configuration by restarting service. **Requires admin**.

```bash
python admin_cli.py config reload
```

This will:
1. Validate configuration
2. Restart service
3. Load new configuration

---

### Rule Management

#### `rules list`
List all rules and their status.

```bash
python admin_cli.py rules list
```

**Example Output**:
```
                        Risk Rules
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Rule ID                         ┃ Status   ┃ Key Settings    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ RULE-001: Max Contracts         │ ENABLED  │ 3               │
│ RULE-002: Max Per Instrument    │ ENABLED  │ 2               │
│ RULE-003: Daily Realized Loss   │ ENABLED  │ -500.0          │
│ RULE-004: Daily Unrealized Loss │ ENABLED  │ -200.0          │
│ RULE-005: Max Unrealized Profit │ ENABLED  │ 300.0           │
│ RULE-006: Trade Frequency       │ ENABLED  │ {...}           │
│ RULE-007: Cooldown After Loss   │ ENABLED  │ -100.0          │
│ RULE-008: Stop-Loss Enforcement │ DISABLED │ 60              │
│ RULE-009: Session Block Outside │ ENABLED  │ True            │
│ RULE-010: Auth Loss Guard       │ ENABLED  │ 30              │
│ RULE-011: Symbol Blocks         │ DISABLED │ []              │
│ RULE-012: Trade Management      │ DISABLED │ {...}           │
│ RULE-013: Daily Realized Profit │ ENABLED  │ 1000.0          │
└─────────────────────────────────┴──────────┴─────────────────┘
```

#### `rules enable <rule_id>`
Enable a specific rule. **Requires admin**.

```bash
python admin_cli.py rules enable max_contracts
```

**Example Output**:
```
Enabling rule: max_contracts...
Rule enabled: max_contracts
Remember to reload configuration: admin_cli config reload
```

#### `rules disable <rule_id>`
Disable a specific rule. **Requires admin**.

```bash
python admin_cli.py rules disable symbol_blocks
```

**Example Output**:
```
Disabling rule: symbol_blocks...
Rule disabled: symbol_blocks
Remember to reload configuration: admin_cli config reload
```

#### `rules configure <rule_id>`
Configure rule parameters interactively. **Requires admin**.

```bash
python admin_cli.py rules configure daily_realized_loss
```

*(Not yet implemented - use `config edit` for now)*

---

### Lockout Management

#### `lockouts list`
List active lockouts.

```bash
python admin_cli.py lockouts list
```

**Example Output**:
```
                    Active Lockouts
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Account ID       ┃ Reason                ┃ Locked At          ┃ Expires    ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ PRAC-V2-126244   │ RULE-003: Daily Loss  │ 2025-10-28 09:00  │ Until Reset│
│ PRAC-V2-789012   │ RULE-006: Frequency   │ 2025-10-28 10:30  │ 15m remain │
└──────────────────┴───────────────────────┴────────────────────┴────────────┘
```

#### `lockouts remove <account_id>`
Remove lockout (emergency unlock). **Requires admin**.

```bash
python admin_cli.py lockouts remove PRAC-V2-126244
```

**Example Interaction**:
```
Removing lockout for account: PRAC-V2-126244...
Are you sure you want to unlock PRAC-V2-126244? [y/N]: y
Lockout removed for: PRAC-V2-126244
Account can now trade again
```

**Warning**: Use this only in emergencies. Removing lockouts bypasses risk protections.

#### `lockouts history`
Show lockout history.

```bash
python admin_cli.py lockouts history
```

**Options**:
- `--account <id>` or `-a <id>`: Filter by account ID
- `--limit <n>` or `-l <n>`: Number of records (default: 50)

**Example**:
```bash
# Show last 100 lockouts
python admin_cli.py lockouts history --limit 100

# Show lockouts for specific account
python admin_cli.py lockouts history --account PRAC-V2-126244
```

**Example Output**:
```
                      Lockout History
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Date       ┃ Account        ┃ Reason             ┃ Duration   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 2025-10-28 │ PRAC-V2-126244 │ RULE-003: Daily    │ Until Reset│
│ 2025-10-27 │ PRAC-V2-789012 │ RULE-006: Freq     │ 15m        │
│ 2025-10-27 │ PRAC-V2-126244 │ RULE-007: Cooldown │ 15m        │
└────────────┴────────────────┴────────────────────┴────────────┘
```

---

### System Monitoring

#### `status`
Show system status (accounts, rules, P&L).

```bash
python admin_cli.py status
```

**Example Output**:
```
╭─────────── Service Status ───────────╮
│ Service: Running                     │
│ Uptime: 2h 45m                       │
│ Mode: Production                     │
╰──────────────────────────────────────╯

╭─────────── Accounts Status ──────────╮
│ Accounts Monitored: 3                │
│ Active Lockouts: 1                   │
│ Active Positions: 5                  │
╰──────────────────────────────────────╯

╭─────────── Rules Status ─────────────╮
│ Total Rules: 13                      │
│ Enabled: 10                          │
│ Disabled: 3                          │
╰──────────────────────────────────────╯
```

#### `logs`
View recent logs.

```bash
python admin_cli.py logs
```

**Options**:
- `--tail <n>` or `-n <n>`: Number of lines to show (default: 50)
- `--follow` or `-f`: Follow log output (like `tail -f`)

**Examples**:
```bash
# Show last 50 lines (default)
python admin_cli.py logs

# Show last 100 lines
python admin_cli.py logs --tail 100

# Follow log output (Ctrl+C to stop)
python admin_cli.py logs --follow
```

**Example Output**:
```
Showing last 50 lines from: data/logs/risk_manager.log

2025-10-28 10:30:15 | INFO  | Service started
2025-10-28 10:30:16 | INFO  | Config loaded: 13 rules
2025-10-28 10:30:17 | INFO  | SDK connected: PRAC-V2-126244
2025-10-28 10:30:18 | INFO  | Rules initialized: 10 active
2025-10-28 10:30:19 | INFO  | Event loop running
2025-10-28 10:31:00 | INFO  | Event received: PositionUpdate
2025-10-28 10:31:01 | INFO  | Rule evaluated: max_contracts PASS
2025-10-28 10:32:30 | WARN  | Rule evaluated: daily_realized_loss VIOLATION
2025-10-28 10:32:31 | ERROR | Enforcement triggered: CLOSE_ALL
```

---

## Common Workflows

### Start Service for First Time

```bash
# 1. Validate configuration
python admin_cli.py config validate

# 2. Check rules are configured
python admin_cli.py rules list

# 3. Start service (as admin)
python admin_cli.py service start

# 4. Verify service started
python admin_cli.py service status

# 5. Monitor logs
python admin_cli.py logs --follow
```

### Change Risk Limits

```bash
# 1. Edit configuration (as admin)
python admin_cli.py config edit

# 2. Validate changes
python admin_cli.py config validate

# 3. Reload configuration (restart service)
python admin_cli.py config reload

# 4. Verify changes applied
python admin_cli.py config show
```

### Emergency Unlock Account

```bash
# 1. Check active lockouts
python admin_cli.py lockouts list

# 2. Remove lockout (as admin)
python admin_cli.py lockouts remove PRAC-V2-126244

# 3. Verify unlocked
python admin_cli.py lockouts list
```

### Debug Service Issues

```bash
# 1. Check service status
python admin_cli.py service status

# 2. View recent logs
python admin_cli.py logs --tail 100

# 3. Check system status
python admin_cli.py status

# 4. Validate configuration
python admin_cli.py config validate

# 5. Restart service if needed (as admin)
python admin_cli.py service restart
```

### Enable/Disable Rule

```bash
# 1. Check current rules
python admin_cli.py rules list

# 2. Disable rule (as admin)
python admin_cli.py rules disable symbol_blocks

# 3. Reload configuration
python admin_cli.py config reload

# 4. Verify change
python admin_cli.py rules list
```

---

## Troubleshooting

### "Administrator Privileges Required" Error

**Problem**: Command requires admin rights but running as normal user.

**Solution**:
1. Close current terminal
2. Right-click Command Prompt / PowerShell
3. Select "Run as administrator"
4. Run command again

### "Configuration file not found" Error

**Problem**: Config file missing or wrong location.

**Solution**:
1. Check config exists: `dir config\risk_config.yaml`
2. If missing, copy from template: `copy config\risk_config.yaml.template config\risk_config.yaml`
3. Edit configuration: `python admin_cli.py config edit`

### "Service not responding" Error

**Problem**: Service hung or crashed.

**Solution**:
```bash
# 1. Try restarting service
python admin_cli.py service restart

# 2. If restart fails, stop and start
python admin_cli.py service stop
python admin_cli.py service start

# 3. Check logs for errors
python admin_cli.py logs --tail 100

# 4. Validate configuration
python admin_cli.py config validate
```

### "Database locked" Error

**Problem**: SQLite database file locked by another process.

**Solution**:
1. Stop service: `python admin_cli.py service stop`
2. Wait 5 seconds
3. Start service: `python admin_cli.py service start`

---

## Security Best Practices

1. **Always use UAC elevation**: Run admin commands via "Run as administrator"
2. **Backup before changes**: Backup `config/` and `data/` before major changes
3. **Validate after editing**: Always run `config validate` after manual edits
4. **Document emergency unlocks**: Log why you removed a lockout
5. **Monitor logs**: Regularly check logs for unusual activity
6. **Test in practice first**: Test config changes on practice accounts first

---

## Configuration File Locations

### Development (Current Directory)
- Config: `./config/risk_config.yaml`
- Data: `./data/risk_state.db`
- Logs: `./data/logs/risk_manager.log`

### Production (Windows Service)
- Config: `C:\ProgramData\SimpleRiskManager\config\risk_config.yaml`
- Data: `C:\ProgramData\SimpleRiskManager\data\risk_state.db`
- Logs: `C:\ProgramData\SimpleRiskManager\logs\risk_manager.log`

---

## Exit Codes

The CLI uses standard exit codes:
- `0`: Success
- `1`: Error (configuration, validation, permission denied)
- `2`: Command usage error

Use in scripts:
```bash
python admin_cli.py config validate
if %ERRORLEVEL% EQU 0 (
    echo Validation passed
) else (
    echo Validation failed
)
```

---

## Getting Help

### General Help
```bash
python admin_cli.py --help
```

### Command-Specific Help
```bash
python admin_cli.py service --help
python admin_cli.py rules --help
python admin_cli.py lockouts --help
```

### Command Usage Examples
```bash
python admin_cli.py service start --help
python admin_cli.py rules enable --help
```

---

## What's Next?

- **Trader CLI**: Read-only CLI for traders (view-only access)
- **Web Dashboard**: Browser-based monitoring dashboard
- **Mobile Notifications**: Push notifications for lockouts/violations
- **Slack Integration**: Send alerts to Slack channel

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0-alpha
