# Config Editor - Quick Start Guide

**For:** Risk Manager V34 Admins
**Commands:** `test_config_editor.py` or `admin_cli config`

---

## Quick Commands

```bash
# View all rules
python test_config_editor.py view

# Edit a rule
python test_config_editor.py edit daily_realized_loss

# Enable a rule
python test_config_editor.py enable symbol_blocks

# Disable a rule
python test_config_editor.py disable trade_management

# Validate config
python test_config_editor.py validate
```

---

## Common Tasks

### 1. Change Daily Loss Limit

```bash
python test_config_editor.py edit daily_realized_loss
# Choose: 2 (Change Limit)
# Enter: -1500
# Choose: 3 (Save & Exit)
```

### 2. Enable Symbol Blocking

```bash
# First, enable the rule
python test_config_editor.py enable symbol_blocks

# Then edit to add symbols
python test_config_editor.py edit symbol_blocks
# Choose: 2 (Change Limit)
# Enter: ES,NQ,YM (comma-separated)
# Choose: 3 (Save & Exit)
```

### 3. Change Trade Frequency Limit

```bash
python test_config_editor.py edit trade_frequency_limit
# Choose: 2 (Change Limit)
# Trades per hour: 15
# Trades per day: 100
# Choose: 3 (Save & Exit)
```

### 4. Change Session Hours

```bash
python test_config_editor.py edit session_block_outside
# Choose: 2 (Change Limit)
# Session start time (HH:MM): 09:00
# Session end time (HH:MM): 16:00
# Choose: 3 (Save & Exit)
```

---

## All Available Rules

| Rule Key | What It Does |
|----------|-------------|
| `max_contracts` | Limit total contracts (account-wide) |
| `max_contracts_per_instrument` | Limit contracts per symbol (MNQ, MES) |
| `daily_realized_loss` | Hard lockout at loss limit |
| `daily_unrealized_loss` | Flatten positions at unrealized loss |
| `max_unrealized_profit` | Take profit at target |
| `trade_frequency_limit` | Limit trades per hour/day |
| `cooldown_after_loss` | Force cooldown after losing trade |
| `no_stop_loss_grace` | Require stop-loss on new positions |
| `session_block_outside` | Block trading outside hours |
| `auth_loss_guard` | Lockout if API disconnects |
| `symbol_blocks` | Block specific symbols |
| `trade_management` | Auto breakeven stop-loss |
| `daily_realized_profit` | Hard lockout at profit target |

---

## Dangerous Rules

These require typing "DISABLE" to disable:

- `max_contracts` - Removes contract limit protection
- `daily_realized_loss` - Removes daily loss protection
- `daily_unrealized_loss` - Removes unrealized loss protection
- `auth_loss_guard` - Removes API disconnect protection

---

## Tips

- Always run `validate` after making changes
- Remember to reload config after changes
- Use `view` to see current status
- Interactive editor lets you preview changes before saving
- Cancel anytime by choosing "Exit Without Saving"

---

## Troubleshooting

**Config file not found?**
- Ensure you're in the project directory: `C:\Users\jakers\Desktop\risk-manager-v34`
- Config file location: `config/risk_config.yaml`

**Rule not found?**
- Run `python test_config_editor.py view` to see all rule keys
- Use exact rule key name (e.g., `daily_realized_loss`, not "Daily Realized Loss")

**Validation errors?**
- Run `python test_config_editor.py validate` to see specific errors
- Check YAML syntax (colons, indentation)
- Ensure all required fields present

---

## Full Documentation

See `CONFIG_EDITOR_IMPLEMENTATION.md` for:
- Complete feature list
- Technical details
- Integration instructions
- Architecture notes

---

**Quick Reference - Keep This Handy!**
