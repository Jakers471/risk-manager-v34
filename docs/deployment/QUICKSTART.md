# Quick Start Guide - Windows Service

**Get Risk Manager V34 running in 5 minutes!**

---

## Prerequisites

- ✅ Windows 10/11 or Server 2016+
- ✅ Python 3.12+
- ✅ Administrator access
- ✅ TopstepX account credentials

---

## 5-Minute Installation

### 1. Install Dependencies (1 min)

```bash
pip install -r requirements.txt
```

### 2. Run Installer (2 min)

**Right-click terminal → "Run as Administrator"**

```bash
python install_service.py
```

Press Enter when prompted. Installation completes automatically.

### 3. Configure (1 min)

**Edit configuration file:**

```bash
notepad C:\ProgramData\RiskManagerV34\config\risk_config.yaml
```

**Minimal required changes:**

```yaml
instruments:
  - MNQ  # Your trading instrument

max_daily_loss: -500.0  # Your daily loss limit
max_contracts: 2        # Your position size limit
```

**Save and close.**

**Add TopstepX credentials:**

```bash
notepad C:\ProgramData\RiskManagerV34\config\accounts.yaml
```

```yaml
accounts:
  - account_id: "YOUR_ACCOUNT_ID"
    username: "your_email@example.com"
    password: "your_password"
    enabled: true
```

**Save and close.**

### 4. Start Service (30 sec)

```bash
net start RiskManagerV34
```

### 5. Verify Running (30 sec)

```bash
sc query RiskManagerV34
```

**Look for**: `STATE: 4 RUNNING`

**Check logs:**

```bash
type "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log"
```

**Look for**:
- 🚀 Service Start
- ✅ Config Loaded
- ✅ SDK Connected
- ✅ Rules Initialized
- ✅ Event Loop Running

---

## ✅ Done!

Your Risk Manager is now running 24/7 in the background, protecting your account!

---

## Common Commands

### Check Status
```bash
sc query RiskManagerV34
```

### View Logs
```bash
type "C:\ProgramData\RiskManagerV34\data\logs\risk_manager.log"
```

### Restart (after config changes)
```bash
net stop RiskManagerV34
net start RiskManagerV34
```

### Stop Service (requires admin)
```bash
net stop RiskManagerV34
```

---

## What's Next?

1. **Monitor Logs**: Watch first few trades to ensure rules working
2. **Fine-tune Rules**: Adjust limits based on trading style
3. **Read Full Guide**: `docs/deployment/WINDOWS_SERVICE.md`
4. **Test Enforcement**: Verify lockouts trigger correctly

---

## Troubleshooting

### Service won't start?
- Check config syntax (YAML)
- Verify credentials are correct
- Check logs for errors

### Configuration not applied?
- Restart service after changes
- Check file saved correctly

### Need help?
- Read full guide: `docs/deployment/WINDOWS_SERVICE.md`
- Check Windows Event Log (eventvwr)

---

**Ready to trade safely! 🛡️**
