# Risk Manager V34 🛡️

**Next-Generation AI-Powered Trading Risk Management System**

Built from the ground up with modern async Python, leveraging:
- **[Project-X-Py](https://github.com/TexasCoding/project-x-py)** - Professional futures trading SDK
- **[Claude-Flow](https://github.com/ruvnet/claude-flow)** - Enterprise AI orchestration platform

## 🎯 What is Risk Manager V34?

A real-time trading risk management system that protects your capital by:
- Monitoring positions and P&L in real-time
- Enforcing custom risk rules automatically
- Using AI to detect anomalies and patterns
- Providing intelligent alerts and insights

## ✨ Key Features

### Real-Time Risk Monitoring
- Live position tracking across multiple instruments
- Real-time P&L calculations
- Automatic rule enforcement (<500ms latency)
- WebSocket-based instant updates

### Intelligent Risk Rules
- Daily loss limits
- Maximum position size
- Stop-loss requirements
- Trading frequency limits
- Session-based restrictions
- Custom rule creation

### AI-Powered Intelligence
- Pattern recognition via Claude-Flow
- Anomaly detection in trading behavior
- Predictive risk analysis
- Semantic memory for learning
- Multi-agent swarm coordination

### Trading Integration
- Direct integration with ProjectX platform
- Multi-instrument support (futures)
- Order management and automation
- Level 2 market data analysis
- 59+ technical indicators

### Windows UAC Security (Virtually Unkillable)
- Runs as Windows Service (auto-start on boot)
- Protected by Windows UAC (no custom passwords)
- Trader cannot kill service without admin rights
- Config files protected by Windows ACL
- Only Windows admin password can override
- OS-level security (industry standard approach)

## 📚 Documentation

### 🚀 **START HERE**

**For Claude AI**:
- **[CLAUDE.md](CLAUDE.md)** - AI entry point (READ THIS FIRST!)
  - What to read and in what order
  - Quick 2-minute start guide
  - Critical SDK-first approach explanation

**For Humans**:
1. Read this README
2. See [docs/current/PROJECT_STATUS.md](docs/current/PROJECT_STATUS.md) - Complete status (~30% done)
3. See [docs/STATUS.md](docs/STATUS.md) - Windows/WSL setup guide

---

### 📖 Current Documentation

**Location**: `docs/current/` (always up-to-date)

- **[PROJECT_STATUS.md](docs/current/PROJECT_STATUS.md)** - Complete project status & progress
- **[SDK_INTEGRATION_GUIDE.md](docs/current/SDK_INTEGRATION_GUIDE.md)** - How we use Project-X SDK (critical!)
- **[RULES_TO_SDK_MAPPING.md](docs/current/RULES_TO_SDK_MAPPING.md)** - Rule specs → SDK mapping (what we build!)
- **[SECURITY_MODEL.md](docs/current/SECURITY_MODEL.md)** - Windows UAC security (why it's unkillable!)
- **[TESTING_GUIDE.md](docs/current/TESTING_GUIDE.md)** - TDD approach & testing guide

### 🛠️ Developer Guides

**Location**: `docs/dev-guides/`

- **[QUICK_REFERENCE.md](docs/dev-guides/QUICK_REFERENCE.md)** - Common commands & tasks

### 📋 Original Specifications

**Location**: `docs/PROJECT_DOCS/` (written before SDK existed)

- **[46 Specification Documents](docs/PROJECT_DOCS/)** - Complete original specs (345KB)
- **[INTEGRATION_NOTE.md](docs/PROJECT_DOCS/INTEGRATION_NOTE.md)** - How specs map to SDK
- **[Architecture v2](docs/PROJECT_DOCS/architecture/system_architecture_v2.md)** - Original system design
- **[12 Risk Rules](docs/PROJECT_DOCS/rules/)** - Detailed rule specifications

### 📦 Archive

**Location**: `docs/archive/`

- Old versions of documentation (dated folders)
- Previous session notes

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required
- Python 3.12+
- Node.js 18+
- UV package manager
- ProjectX API credentials

# Optional (for AI features)
- Claude API key
```

### Installation

**⚠️ Windows Users**: Known issue with `project-x-py` dependency (`uvloop` doesn't support Windows). **Recommended: Use WSL2**. See [STATUS.md](STATUS.md) for detailed solutions.

```bash
# Clone the repository
git clone <your-repo-url>
cd risk-manager-v34

# Install Python dependencies
# Linux/Mac/WSL:
uv sync

# Windows: See STATUS.md for workaround instructions

# Install Claude-Flow (optional, for AI features)
npm install -g claude-flow@alpha
```

### Configuration

Create `.env` file:

```bash
# ProjectX API (Required)
PROJECT_X_API_KEY=your_api_key
PROJECT_X_USERNAME=your_username

# Claude API (Optional - for AI features)
CLAUDE_API_KEY=your_claude_key
```

### Basic Usage

```python
import asyncio
from risk_manager import RiskManager

async def main():
    # Initialize risk manager
    rm = await RiskManager.create(
        instruments=["MNQ", "ES"],
        rules={
            "max_daily_loss": -1000.0,
            "max_contracts": 5,
            "require_stop_loss": True
        }
    )

    # Start monitoring
    await rm.start()

    print("✅ Risk Manager active - protecting your capital!")

    # Keep running
    await rm.wait_until_stopped()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📖 Documentation

- [Quick Start Guide](docs/quickstart.md)
- [Configuration Reference](docs/configuration.md)
- [Risk Rules Guide](docs/risk-rules.md)
- [AI Features](docs/ai-features.md)
- [API Reference](docs/api-reference.md)
- [Examples](examples/)

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      Risk Manager V34               │
│   Smart Risk Protection Layer       │
└─────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐ ┌──────┐ ┌─────────┐
│AI Flow │ │ Core │ │Trading  │
│(Claude)│◄┤Engine├►│ (SDK)   │
└────────┘ └──────┘ └─────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌───────┐ ┌────────┐ ┌─────────┐
│ Rules │ │Monitor │ │  Alert  │
└───────┘ └────────┘ └─────────┘
```

### Core Components

**Risk Engine** (`src/risk_manager/core/`)
- Event processing and coordination
- Rule evaluation engine
- Real-time monitoring
- Enforcement actions

**Risk Rules** (`src/risk_manager/rules/`)
- Built-in rule library
- Custom rule creation
- Rule composition
- Dynamic rule updates

**Trading Integration** (`src/risk_manager/integrations/`)
- Project-X-Py SDK wrapper
- WebSocket event handling
- Order management
- Position synchronization

**AI Intelligence** (`src/risk_manager/ai/`)
- Claude-Flow integration
- Pattern recognition
- Anomaly detection
- Decision support

**Monitoring** (`src/risk_manager/monitoring/`)
- Real-time dashboards
- Alert system
- Performance metrics
- Audit logging

## 💡 Usage Examples

### Example 1: Basic Risk Protection

```python
from risk_manager import RiskManager

async def basic_protection():
    rm = await RiskManager.create(
        instruments=["MNQ"],
        rules={
            "max_daily_loss": -500.0,  # Stop after $500 loss
            "max_contracts": 2,         # Max 2 contracts
        }
    )

    await rm.start()
    # Your trading strategy runs here
    # Risk Manager automatically protects you
```

### Example 2: Advanced Rules

```python
from risk_manager import RiskManager
from risk_manager.rules import DailyLossRule, MaxPositionRule, StopLossRule

async def advanced_protection():
    rm = await RiskManager.create(instruments=["ES"])

    # Add custom rules
    rm.add_rule(DailyLossRule(limit=-1000.0, action="flatten"))
    rm.add_rule(MaxPositionRule(max_contracts=5, per_instrument=True))
    rm.add_rule(StopLossRule(require_within_seconds=60))

    await rm.start()
```

### Example 3: AI-Powered Monitoring

```python
from risk_manager import RiskManager

async def ai_monitoring():
    rm = await RiskManager.create(
        instruments=["MNQ", "ES"],
        enable_ai=True,  # Enable Claude-Flow features
        ai_config={
            "pattern_recognition": True,
            "anomaly_detection": True,
            "predictive_analysis": True
        }
    )

    # AI will:
    # - Learn your trading patterns
    # - Detect unusual behavior
    # - Provide intelligent alerts
    # - Suggest risk adjustments

    await rm.start()
```

## 🎨 Built-in Risk Rules

- **DailyLossRule** - Maximum daily loss limit
- **MaxPositionRule** - Maximum contracts per instrument
- **StopLossRule** - Require stop-loss orders
- **FrequencyRule** - Limit trades per time period
- **SessionRule** - Restrict trading to specific times
- **DrawdownRule** - Maximum drawdown from peak
- **VelocityRule** - Rate of loss detection
- **ConcentrationRule** - Instrument diversification
- **LeverageRule** - Maximum leverage limits

## 🤖 AI Features (Powered by Claude-Flow)

### Pattern Recognition
```python
# Automatically learns your trading patterns
patterns = await rm.ai.get_learned_patterns()
print(f"Learned {len(patterns)} trading patterns")
```

### Anomaly Detection
```python
# Real-time anomaly detection
@rm.on("anomaly_detected")
async def handle_anomaly(event):
    print(f"⚠️ Unusual pattern detected: {event.description}")
    print(f"Confidence: {event.confidence}%")
```

### Intelligent Alerts
```python
# AI-generated contextual alerts
@rm.on("ai_alert")
async def handle_alert(event):
    print(f"🤖 AI Alert: {event.message}")
    print(f"Recommendation: {event.recommendation}")
```

## 📊 Monitoring & Dashboards

### Real-Time Metrics
- Current P&L (realized & unrealized)
- Position sizes and exposure
- Rule status and violations
- System health and performance

### Alert Channels
- Console output
- Discord webhooks
- Telegram bot
- Email notifications
- Custom webhooks

### Performance Tracking
- Enforcement latency
- Rule evaluation times
- Event processing rates
- System resource usage

## 🔧 Configuration

### Risk Rules Configuration
```yaml
# config/rules.yaml
rules:
  daily_loss:
    enabled: true
    limit: -1000.0
    action: flatten  # flatten, pause, alert

  max_position:
    enabled: true
    max_contracts: 5
    per_instrument: true

  stop_loss:
    enabled: true
    require_within_seconds: 60
    grace_period_seconds: 300
```

### AI Configuration
```yaml
# config/ai.yaml
ai:
  enabled: true
  provider: claude-flow

  features:
    pattern_recognition: true
    anomaly_detection: true
    predictive_analysis: true

  memory:
    enabled: true
    backend: reasoningbank
    namespace: risk-mgmt
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=risk_manager --cov-report=html

# Run specific tests
uv run pytest tests/test_rules.py -v
```

## 📈 Roadmap

### Phase 1: Foundation (Week 1) ✅
- [x] Project setup
- [x] Basic architecture
- [ ] Core risk engine
- [ ] Trading integration

### Phase 2: Core Features (Week 2)
- [ ] Built-in risk rules
- [ ] Real-time monitoring
- [ ] Alert system
- [ ] Basic dashboard

### Phase 3: AI Integration (Week 3)
- [ ] Claude-Flow integration
- [ ] Pattern recognition
- [ ] Anomaly detection
- [ ] Predictive analysis

### Phase 4: Production Ready (Week 4)
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation complete
- [ ] Deployment tools

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with these amazing projects:
- [Project-X-Py](https://github.com/TexasCoding/project-x-py) - Professional trading SDK
- [Claude-Flow](https://github.com/ruvnet/claude-flow) - Enterprise AI orchestration

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](issues)
- **Discussions**: [GitHub Discussions](discussions)

---

**Built with ❤️ for traders who value their capital**

**Version**: 1.0.0-alpha
**Last Updated**: 2025-10-23
