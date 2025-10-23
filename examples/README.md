# Risk Manager V34 - Examples

These examples demonstrate various ways to use Risk Manager V34.

## Prerequisites

Before running examples, make sure you have:

1. **Installed dependencies**:
   ```bash
   cd risk-manager-v34
   uv sync
   ```

2. **Configured environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your ProjectX API credentials
   ```

3. **ProjectX API credentials** from TopStepX platform

## Examples

### 01 - Basic Usage
**File**: `01_basic_usage.py`

The simplest way to get started. Shows:
- Creating a risk manager with basic rules
- Monitoring a single instrument (MNQ)
- Handling rule violations

```bash
uv run python examples/01_basic_usage.py
```

### 02 - Advanced Rules
**File**: `02_advanced_rules.py`

Custom risk rules and event handling. Shows:
- Creating custom rule instances
- Multiple rule types with different actions
- Subscribing to various events
- Real-time monitoring

```bash
uv run python examples/02_advanced_rules.py
```

### 03 - Multi-Instrument
**File**: `03_multi_instrument.py`

Portfolio-level risk management. Shows:
- Monitoring multiple instruments simultaneously
- Portfolio-wide risk limits
- Per-instrument tracking and statistics
- Aggregated P&L monitoring

```bash
uv run python examples/03_multi_instrument.py
```

## Example Output

When you run an example, you'll see:

```
🛡️ Risk Manager V34 - Basic Example

✅ Risk Manager configured:
   • Max Daily Loss: $-500
   • Max Contracts: 2
   • Monitoring: MNQ

🚀 Starting risk manager...

💡 Risk Manager is now protecting your capital!
   Press Ctrl+C to stop

📊 Position Update: MNQ
   Size: 1
   P&L: $25.00

✅ Fill: MNQ - 1 @ $16450.50
   Total fills: 1
```

## Next Steps

After trying the examples:

1. **Customize rules** - Modify rule parameters to match your risk tolerance
2. **Add more instruments** - Monitor additional futures contracts
3. **Enable AI features** - Add anomaly detection and pattern recognition
4. **Build your strategy** - Integrate with your trading algorithms

## Troubleshooting

### Connection Issues
```
Error: Failed to connect to trading platform
```
**Solution**: Check your .env file has correct PROJECT_X_API_KEY and PROJECT_X_USERNAME

### Import Errors
```
ModuleNotFoundError: No module named 'risk_manager'
```
**Solution**: Run `uv sync` to install dependencies

### Authentication Errors
```
AuthenticationError: Invalid API key
```
**Solution**: Verify your ProjectX API credentials at topstepx.com

## More Information

- [Main README](../README.md)
- [Configuration Guide](../docs/configuration.md)
- [API Reference](../docs/api-reference.md)
