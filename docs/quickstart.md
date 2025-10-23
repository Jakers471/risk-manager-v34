# Quick Start Guide

Get up and running with Risk Manager V34 in 5 minutes.

## Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd risk-manager-v34
```

### 2. Install Dependencies
```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials:
# - PROJECT_X_API_KEY (required)
# - PROJECT_X_USERNAME (required)
# - ANTHROPIC_API_KEY (optional, for AI features)
```

## Your First Risk Manager

Create a file `my_risk_manager.py`:

```python
import asyncio
from risk_manager import RiskManager

async def main():
    # Create risk manager with basic protection
    rm = await RiskManager.create(
        instruments=["MNQ"],  # E-mini NASDAQ
        rules={
            "max_daily_loss": -500.0,  # Stop after $500 loss
            "max_contracts": 2,         # Max 2 contracts
        }
    )

    # Subscribe to alerts
    @rm.on("rule_violated")
    async def alert(event):
        print(f"⚠️ {event.data['message']}")

    # Start protecting your capital
    await rm.start()
    print("✅ Risk Manager active!")

    # Keep running
    await rm.wait_until_stopped()

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
uv run python my_risk_manager.py
```

## What Happens Now?

Risk Manager V34 will:
1. ✅ Connect to your ProjectX trading account
2. ✅ Monitor your positions in real-time
3. ✅ Enforce your risk rules automatically
4. ✅ Alert you when limits are approached
5. ✅ Take protective action if rules are violated

## Next Steps

### Add More Rules
```python
from risk_manager.rules import DailyLossRule, MaxPositionRule

# Custom rules with specific actions
rm.add_rule(DailyLossRule(limit=-1000.0, action="flatten"))
rm.add_rule(MaxPositionRule(max_contracts=5, per_instrument=True))
```

### Monitor Multiple Instruments
```python
rm = await RiskManager.create(
    instruments=["MNQ", "ES", "MGC"],  # Multiple futures
    rules={"max_daily_loss": -2000.0}  # Portfolio-wide limit
)
```

### Enable AI Features
```python
rm = await RiskManager.create(
    instruments=["MNQ"],
    enable_ai=True,  # Requires ANTHROPIC_API_KEY
    rules={"max_daily_loss": -500.0}
)

# AI will learn patterns and detect anomalies
```

### Subscribe to Events
```python
@rm.on("order_filled")
async def track_trades(event):
    print(f"Trade: {event.data['symbol']} - {event.data['size']} contracts")

@rm.on("position_updated")
async def monitor_pnl(event):
    print(f"P&L: ${event.data['unrealized_pnl']:.2f}")

@rm.on("enforcement_action")
async def handle_enforcement(event):
    print(f"Enforcement: {event.data['action']}")
```

## Common Issues

### "Failed to connect to trading platform"
- Check your `.env` file has correct `PROJECT_X_API_KEY` and `PROJECT_X_USERNAME`
- Verify credentials are active at topstepx.com

### "ModuleNotFoundError"
- Run `uv sync` to install dependencies
- Make sure you're in the project directory

### "No module named 'anthropic'"
- AI features require: `uv sync --all-extras` or `pip install risk-manager-v34[ai]`

## Examples

Check out the `examples/` directory for more:
- `01_basic_usage.py` - Simple protection
- `02_advanced_rules.py` - Custom rules
- `03_multi_instrument.py` - Portfolio management

## Documentation

- [Configuration Reference](configuration.md)
- [Risk Rules Guide](risk-rules.md)
- [AI Features](ai-features.md)
- [API Reference](api-reference.md)

## Support

- GitHub Issues: [Report bugs or request features](../issues)
- Documentation: [Full docs](../docs/)

---

**Ready to protect your trading capital? Start building!** 🛡️
