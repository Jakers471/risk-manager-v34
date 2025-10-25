# Wave 2 Gap Analysis: Cross-Cutting Infrastructure

**Analysis Date**: 2025-10-25
**Researcher**: RESEARCHER 7 - Cross-Cutting Infrastructure Gap Analyst
**Project**: Risk Manager V34
**Working Directory**: /mnt/c/Users/jakers/Desktop/risk-manager-v34

---

## Executive Summary

This analysis examines cross-cutting infrastructure components (logging, utilities, monitoring, error handling, configuration, validation) to identify gaps between specifications and actual implementation.

### Key Findings

**Overall Assessment**:
- **Total Lines of Code**: 2,828 lines across all modules
- **8-Checkpoint Logging**: ✅ **IMPLEMENTED** (all 8 checkpoints present)
- **Utilities Module**: ❌ **MISSING** (no `utils/` directory)
- **Monitoring & Metrics**: 🔄 **PARTIAL** (directory exists but empty)
- **Error Handling**: 🔄 **PARTIAL** (no custom exception hierarchy)
- **Configuration Management**: ✅ **IMPLEMENTED** (Pydantic-based)
- **Data Validation**: ✅ **IMPLEMENTED** (Pydantic models)

**Estimated Total Effort to Complete**: 2-3 weeks

---

## Implementation Status Matrix

| Category | Status | Priority | Effort | Impact | Blockers |
|----------|--------|----------|--------|--------|----------|
| **8-Checkpoint Logging** | ✅ Implemented | High | ✅ Complete | Runtime debugging | None |
| **Log Rotation & Management** | 🔄 Partial | Medium | 1 day | Log disk usage | None |
| **Utilities Module** | ❌ Missing | High | 1 week | Code reuse, daily reset | None |
| **Monitoring & Metrics** | ❌ Missing | High | 1 week | Observability | None |
| **Error Handling** | 🔄 Partial | High | 4 days | Reliability | None |
| **Config Management** | ✅ Implemented | - | ✅ Complete | Settings | None |
| **Data Validation** | ✅ Implemented | - | ✅ Complete | Data integrity | None |
| **Environment Management** | 🔄 Partial | Medium | 2 days | Dev/Prod separation | None |

---

## Detailed Gap Analysis

### Category 1: Logging Infrastructure ✅ IMPLEMENTED

#### 8-Checkpoint Logging System

**Status**: ✅ **FULLY IMPLEMENTED**

**Evidence from codebase**:

```python
# manager.py:46 - Checkpoint 1: Service Start
sdk_logger.info("🚀 Risk Manager starting...")

# manager.py:111 - Checkpoint 2: Config Loaded
sdk_logger.info(f"✅ Config loaded: {len(rules) if rules else 0} custom rules, monitoring {len(instruments) if instruments else 0} instruments")

# manager.py:144 - Checkpoint 3: SDK Connected
sdk_logger.info(f"✅ SDK connected: {len(instruments)} instrument(s) - {', '.join(instruments)}")

# manager.py:190 - Checkpoint 4: Rules Initialized
sdk_logger.info(f"✅ Rules initialized: {len(rules_added)} rules - {', '.join(rules_added)}")

# engine.py:39 - Checkpoint 5: Event Loop Running
sdk_logger.info(f"✅ Event loop running: {len(self.rules)} active rules monitoring events")

# engine.py:69 - Checkpoint 6: Event Received
sdk_logger.info(f"📨 Event received: {event.event_type.value} - evaluating {len(self.rules)} rules")

# engine.py:76 - Checkpoint 7: Rule Evaluated
sdk_logger.info(f"🔍 Rule evaluated: {rule.__class__.__name__} - {'VIOLATED' if violation else 'PASSED'}")

# engine.py:102/106/110 - Checkpoint 8: Enforcement Triggered
sdk_logger.warning(f"⚠️ Enforcement triggered: FLATTEN ALL - Rule: {rule.__class__.__name__}")
sdk_logger.warning(f"⚠️ Enforcement triggered: PAUSE TRADING - Rule: {rule.__class__.__name__}")
sdk_logger.info(f"⚠️ Enforcement triggered: ALERT - Rule: {rule.__class__.__name__}")
```

**Additional enforcement logging in enforcement.py**:
```python
# enforcement.py:56
sdk_logger.warning(f"⚠️ Enforcement triggered: CLOSE ALL POSITIONS - Symbol: {symbol or 'ALL'}")

# enforcement.py:132
sdk_logger.warning(f"⚠️ Enforcement triggered: CLOSE POSITION - {symbol}/{contract_id}")

# enforcement.py:220
sdk_logger.warning(f"⚠️ Enforcement triggered: CANCEL ALL ORDERS - Symbol: {symbol or 'ALL'}")

# enforcement.py:325
sdk_logger.warning(f"⚠️ Enforcement triggered: FLATTEN AND CANCEL - Symbol: {symbol or 'ALL'} - CRITICAL ACTION")
```

**What's Working**:
- ✅ All 8 strategic checkpoints implemented with emoji markers
- ✅ SDK logger used consistently (`ProjectXLogger.get_logger(__name__)`)
- ✅ Dual logging: both `loguru` and SDK logger
- ✅ Appropriate log levels (INFO for checkpoints, WARNING for enforcement)
- ✅ Rich contextual information in logs

**What's Missing**:
- 🔄 JSON-formatted structured logging for production
- 🔄 Log rotation configuration (currently basic)
- 🔄 Log retention policy
- 🔄 Per-module log level configuration

**Gap Details**:

**Current Implementation**:
```python
# manager.py:49-64
def _setup_logging(self) -> None:
    """Configure logging."""
    logger.remove()  # Remove default handler
    logger.add(
        lambda msg: print(msg, end=""),
        level=self.config.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )

    if self.config.log_file:
        logger.add(
            self.config.log_file,
            rotation="1 day",
            retention="30 days",
            level=self.config.log_level,
        )
```

**Missing Features**:
1. **JSON Structured Logging** (for production)
   ```python
   # Need to add:
   if self.config.environment == "production":
       logger.add(
           self.config.log_file,
           rotation="100 MB",
           retention="30 days",
           serialize=True,  # JSON format
           level=self.config.log_level,
       )
   ```

2. **Per-Module Log Levels**
   ```python
   # Need configuration like:
   logging_config:
     global_level: "INFO"
     modules:
       risk_manager.core.engine: "DEBUG"
       risk_manager.sdk.enforcement: "WARNING"
   ```

3. **Log Compression**
   ```python
   logger.add(
       self.config.log_file,
       rotation="1 day",
       retention="30 days",
       compression="zip",  # Missing
   )
   ```

**Impact**: LOW
- **Why**: Core logging works, missing features are nice-to-have
- **Users**: Production operations team (for log parsing)
- **Can deploy without**: Yes, but production monitoring harder

**Estimated Effort**: 1 day
- Hour 1-2: Add JSON serialization option
- Hour 3-4: Per-module log level config
- Hour 5-6: Log compression
- Hour 7-8: Testing and documentation

---

### Category 2: Utilities Module ❌ MISSING

**Status**: ❌ **COMPLETELY MISSING**

**Evidence**: No `src/risk_manager/utils/` directory exists

**Impact**: HIGH
- **Why**: Daily reset requires ET timezone utilities, validation needed everywhere
- **Users**: All components
- **Can deploy without**: NO - daily reset feature blocked

**What's Needed**:

#### 2.1 Date/Time Utilities

**Required for**: RULE-003 (Daily Realized Loss), RULE-013 (Daily Realized Profit)

**Missing Functions**:
```python
# src/risk_manager/utils/datetime_utils.py

from datetime import datetime, time
from zoneinfo import ZoneInfo

def get_et_timezone() -> ZoneInfo:
    """Get America/New_York timezone."""
    return ZoneInfo("America/New_York")

def get_current_et() -> datetime:
    """Get current time in ET timezone."""
    return datetime.now(get_et_timezone())

def get_midnight_et(date: datetime | None = None) -> datetime:
    """
    Calculate midnight ET for given date (or today).

    Critical for daily reset calculations.
    """
    if date is None:
        date = get_current_et()

    # Get midnight ET for the date
    midnight = datetime.combine(date.date(), time(0, 0), tzinfo=get_et_timezone())
    return midnight

def get_next_reset_time(reset_hour: int = 17) -> datetime:
    """
    Calculate next daily reset time (default 5:00 PM ET).

    Used by: Daily loss/profit rules
    """
    now = get_current_et()
    reset_time = datetime.combine(
        now.date(),
        time(reset_hour, 0),
        tzinfo=get_et_timezone()
    )

    # If reset time already passed today, get tomorrow's reset
    if now >= reset_time:
        from datetime import timedelta
        reset_time += timedelta(days=1)

    return reset_time

def is_trading_hours(dt: datetime | None = None, start: time = time(9, 30), end: time = time(16, 0)) -> bool:
    """
    Check if given time is within trading hours (default 9:30 AM - 4:00 PM ET).

    Used by: RULE-009 (Session Block Outside)
    """
    if dt is None:
        dt = get_current_et()

    # Convert to ET if not already
    dt_et = dt.astimezone(get_et_timezone())

    return start <= dt_et.time() <= end

def convert_to_et(dt: datetime) -> datetime:
    """Convert any timezone to ET."""
    return dt.astimezone(get_et_timezone())
```

**Why Critical**:
- Daily reset rules (RULE-003, RULE-013) need to know "when is 5:00 PM ET?"
- Session rules (RULE-009) need to check if within trading hours
- All time-based features blocked without this

**Estimated Effort**: 2 days
- Day 1: Implement all datetime utilities, unit tests
- Day 2: Integration testing with daily reset rules

---

#### 2.2 Validation Utilities

**Required for**: Input validation across all components

**Missing Functions**:
```python
# src/risk_manager/utils/validation.py

from typing import Any

def validate_account_id(account_id: str) -> bool:
    """
    Validate TopstepX account ID format.

    Format: PRAC-V2-XXXXXX-XXXXXXXX or LIVE-V2-XXXXXX-XXXXXXXX
    """
    import re
    pattern = r"^(PRAC|LIVE)-V2-\d{6}-\d{8}$"
    return re.match(pattern, account_id) is not None

def validate_symbol(symbol: str) -> bool:
    """
    Validate futures symbol format.

    Valid: MNQ, ES, NQ, GC, CL, etc.
    Invalid: AAPL (stocks), empty string
    """
    # Basic check: 1-5 uppercase letters
    return symbol.isalpha() and symbol.isupper() and 1 <= len(symbol) <= 5

def validate_contract_size(contracts: int, min_size: int = 1, max_size: int = 100) -> tuple[bool, str | None]:
    """
    Validate contract size is within limits.

    Returns: (is_valid, error_message)
    """
    if contracts < min_size:
        return False, f"Contract size {contracts} below minimum {min_size}"
    if contracts > max_size:
        return False, f"Contract size {contracts} exceeds maximum {max_size}"
    return True, None

def validate_price(price: float) -> bool:
    """Validate price is positive and reasonable."""
    return price > 0 and price < 1_000_000  # Reasonable upper bound

def sanitize_symbol(symbol: str) -> str:
    """
    Sanitize symbol input.

    - Remove whitespace
    - Convert to uppercase
    - Remove invalid characters
    """
    return ''.join(c for c in symbol.upper().strip() if c.isalpha())
```

**Why Important**:
- Prevent invalid data from entering system
- Better error messages for users
- Security (prevent injection attacks)

**Estimated Effort**: 1 day

---

#### 2.3 Math Utilities

**Required for**: P&L calculations, position sizing

**Missing Functions**:
```python
# src/risk_manager/utils/math.py

def calculate_pnl(entry_price: float, exit_price: float, contracts: int, multiplier: float = 20.0) -> float:
    """
    Calculate P&L for futures trade.

    Args:
        entry_price: Entry price (e.g., 20125.50)
        exit_price: Exit price (e.g., 20130.00)
        contracts: Number of contracts
        multiplier: Contract multiplier (MNQ=20, ES=50, NQ=20)

    Returns:
        Realized P&L in dollars
    """
    tick_pnl = (exit_price - entry_price) * contracts * multiplier
    return round(tick_pnl, 2)

def calculate_position_value(price: float, contracts: int, multiplier: float = 20.0) -> float:
    """Calculate notional value of position."""
    return price * contracts * multiplier

def calculate_percentage(value: float, total: float, decimals: int = 2) -> float:
    """
    Calculate percentage with rounding.

    Example: calculate_percentage(250, 1000) -> 25.0
    """
    if total == 0:
        return 0.0
    return round((value / total) * 100, decimals)

def calculate_risk_reward_ratio(risk: float, reward: float) -> float:
    """
    Calculate risk/reward ratio.

    Example: risk=$100, reward=$200 -> 1:2 -> 2.0
    """
    if risk == 0:
        return 0.0
    return round(reward / abs(risk), 2)
```

**Why Important**:
- Consistent P&L calculations across rules
- Position value for max position checks
- Risk/reward analysis

**Estimated Effort**: 1 day

---

#### 2.4 String Utilities

**Required for**: CLI display, logging, reporting

**Missing Functions**:
```python
# src/risk_manager/utils/formatting.py

def format_currency(value: float, decimals: int = 2) -> str:
    """
    Format currency with $ and commas.

    Example: format_currency(1234.56) -> "$1,234.56"
    Example: format_currency(-500) -> "-$500.00"
    """
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    return f"{sign}${abs_value:,.{decimals}f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format percentage.

    Example: format_percentage(12.345) -> "12.35%"
    """
    return f"{value:.{decimals}f}%"

def format_timestamp(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """Format datetime to string."""
    return dt.strftime(format_str)

def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable form.

    Example: format_duration(3665) -> "1h 1m 5s"
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)

def truncate_string(s: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate long strings for display."""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix
```

**Why Important**:
- Consistent formatting in CLI displays
- Better log readability
- User-friendly error messages

**Estimated Effort**: 1 day

---

**Total Utilities Module Effort**: 5 days (1 week)
- Day 1-2: DateTime utilities (highest priority - blocks daily reset)
- Day 3: Validation utilities
- Day 4: Math utilities
- Day 5: String formatting utilities

---

### Category 3: Monitoring & Metrics ❌ MISSING

**Status**: ❌ **EMPTY DIRECTORY**

**Evidence**:
```bash
$ ls -la /mnt/c/Users/jakers/Desktop/risk-manager-v34/src/risk_manager/monitoring/
# Empty directory exists but no files
```

**Impact**: HIGH
- **Why**: Cannot observe system health, performance, or business metrics
- **Users**: Operations team, traders (for dashboards)
- **Can deploy without**: Technically yes, but production monitoring impossible

**What's Needed**:

#### 3.1 System Health Metrics

```python
# src/risk_manager/monitoring/health.py

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict

@dataclass
class SystemHealth:
    """System health metrics."""

    # Uptime
    start_time: datetime = field(default_factory=datetime.now)

    # Event throughput
    events_processed: int = 0
    events_per_second: float = 0.0

    # Rule performance
    rule_evaluation_count: int = 0
    avg_rule_latency_ms: float = 0.0

    # SDK connection
    sdk_connected: bool = False
    last_event_received: datetime | None = None

    # Memory/CPU (optional)
    memory_mb: float = 0.0
    cpu_percent: float = 0.0

    def get_uptime_seconds(self) -> int:
        """Calculate uptime in seconds."""
        return int((datetime.now() - self.start_time).total_seconds())

    def is_healthy(self) -> bool:
        """
        Check if system is healthy.

        Criteria:
        - SDK connected
        - Received event in last 60 seconds (if market open)
        - Events processing (> 0/sec if active)
        """
        if not self.sdk_connected:
            return False

        # If we've received events, check recency
        if self.last_event_received:
            time_since_event = datetime.now() - self.last_event_received
            # Alert if no events for 5 minutes during market hours
            if time_since_event > timedelta(minutes=5):
                # TODO: Check if market is open before alerting
                pass

        return True


class HealthMonitor:
    """Monitor system health."""

    def __init__(self):
        self.health = SystemHealth()
        self._event_times: list[datetime] = []
        self._rule_latencies: list[float] = []

    def record_event(self) -> None:
        """Record an event was processed."""
        now = datetime.now()
        self.health.events_processed += 1
        self.health.last_event_received = now

        # Track for throughput calculation
        self._event_times.append(now)

        # Keep only last minute
        cutoff = now - timedelta(minutes=1)
        self._event_times = [t for t in self._event_times if t > cutoff]

        # Calculate events/second
        if self._event_times:
            duration = (now - self._event_times[0]).total_seconds()
            if duration > 0:
                self.health.events_per_second = len(self._event_times) / duration

    def record_rule_evaluation(self, latency_ms: float) -> None:
        """Record rule evaluation latency."""
        self.health.rule_evaluation_count += 1
        self._rule_latencies.append(latency_ms)

        # Keep only last 100 evaluations
        if len(self._rule_latencies) > 100:
            self._rule_latencies = self._rule_latencies[-100:]

        # Calculate average
        if self._rule_latencies:
            self.health.avg_rule_latency_ms = sum(self._rule_latencies) / len(self._rule_latencies)

    def set_sdk_connected(self, connected: bool) -> None:
        """Update SDK connection status."""
        self.health.sdk_connected = connected

    def get_health_report(self) -> dict:
        """Get health report for API/CLI."""
        return {
            "status": "healthy" if self.health.is_healthy() else "unhealthy",
            "uptime_seconds": self.health.get_uptime_seconds(),
            "events_processed": self.health.events_processed,
            "events_per_second": round(self.health.events_per_second, 2),
            "rule_evaluations": self.health.rule_evaluation_count,
            "avg_rule_latency_ms": round(self.health.avg_rule_latency_ms, 2),
            "sdk_connected": self.health.sdk_connected,
            "last_event": self.health.last_event_received.isoformat() if self.health.last_event_received else None,
        }
```

**Estimated Effort**: 3 days

---

#### 3.2 Business Metrics

```python
# src/risk_manager/monitoring/metrics.py

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BusinessMetrics:
    """Business intelligence metrics."""

    # Violations
    violations_by_rule: dict[str, int]
    violations_today: int = 0

    # Enforcements
    enforcements_by_action: dict[str, int]
    positions_closed_count: int = 0
    orders_cancelled_count: int = 0

    # P&L
    daily_pnl: float = 0.0
    cumulative_pnl: float = 0.0
    peak_pnl: float = 0.0
    drawdown: float = 0.0

    # Trading activity
    trades_today: int = 0
    positions_opened: int = 0
    positions_closed: int = 0

    # Lockouts
    lockouts_active: int = 0
    lockouts_today: int = 0


class MetricsCollector:
    """Collect business metrics."""

    def __init__(self):
        self.metrics = BusinessMetrics(
            violations_by_rule=defaultdict(int),
            enforcements_by_action=defaultdict(int),
        )
        self._reset_time = datetime.now()

    def record_violation(self, rule_name: str) -> None:
        """Record a rule violation."""
        self.metrics.violations_by_rule[rule_name] += 1
        self.metrics.violations_today += 1

    def record_enforcement(self, action: str, count: int = 1) -> None:
        """Record enforcement action."""
        self.metrics.enforcements_by_action[action] += count

        if action == "close_position":
            self.metrics.positions_closed_count += count
        elif action == "cancel_order":
            self.metrics.orders_cancelled_count += count

    def update_pnl(self, daily_pnl: float, cumulative_pnl: float) -> None:
        """Update P&L metrics."""
        self.metrics.daily_pnl = daily_pnl
        self.metrics.cumulative_pnl = cumulative_pnl

        # Track peak for drawdown
        if cumulative_pnl > self.metrics.peak_pnl:
            self.metrics.peak_pnl = cumulative_pnl

        # Calculate drawdown
        self.metrics.drawdown = self.metrics.peak_pnl - cumulative_pnl

    def daily_reset(self) -> None:
        """Reset daily metrics."""
        self.metrics.violations_today = 0
        self.metrics.trades_today = 0
        self.metrics.lockouts_today = 0
        self.metrics.daily_pnl = 0.0
        self._reset_time = datetime.now()

    def get_metrics_summary(self) -> dict:
        """Get metrics summary."""
        return {
            "violations": {
                "total_today": self.metrics.violations_today,
                "by_rule": dict(self.metrics.violations_by_rule),
            },
            "enforcements": {
                "by_action": dict(self.metrics.enforcements_by_action),
                "positions_closed": self.metrics.positions_closed_count,
                "orders_cancelled": self.metrics.orders_cancelled_count,
            },
            "pnl": {
                "daily": round(self.metrics.daily_pnl, 2),
                "cumulative": round(self.metrics.cumulative_pnl, 2),
                "peak": round(self.metrics.peak_pnl, 2),
                "drawdown": round(self.metrics.drawdown, 2),
            },
            "trading": {
                "trades_today": self.metrics.trades_today,
                "positions_opened": self.metrics.positions_opened,
                "positions_closed": self.metrics.positions_closed,
            },
            "lockouts": {
                "active": self.metrics.lockouts_active,
                "today": self.metrics.lockouts_today,
            },
        }
```

**Estimated Effort**: 2 days

---

#### 3.3 Alerting System

```python
# src/risk_manager/monitoring/alerts.py

from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """System alert."""
    level: AlertLevel
    message: str
    timestamp: datetime
    component: str
    data: dict | None = None

class AlertManager:
    """Manage system alerts."""

    def __init__(self):
        self.alerts: list[Alert] = []
        self.alert_handlers = []

    def send_alert(self, level: AlertLevel, message: str, component: str, data: dict | None = None) -> None:
        """Send an alert."""
        alert = Alert(
            level=level,
            message=message,
            timestamp=datetime.now(),
            component=component,
            data=data,
        )

        self.alerts.append(alert)

        # Trigger handlers
        for handler in self.alert_handlers:
            handler(alert)

    def register_handler(self, handler) -> None:
        """Register alert handler (e.g., for Discord, email)."""
        self.alert_handlers.append(handler)

    def get_recent_alerts(self, count: int = 10) -> list[Alert]:
        """Get recent alerts."""
        return self.alerts[-count:]
```

**Estimated Effort**: 2 days

**Total Monitoring Effort**: 7 days (1+ week)

---

### Category 4: Error Handling 🔄 PARTIAL

**Status**: 🔄 **BASIC ERROR HANDLING EXISTS, NO CUSTOM EXCEPTIONS**

**Evidence**:
- Try/except blocks exist in code
- No custom exception hierarchy found
- Generic Exception catching used

**Current Implementation**:
```python
# engine.py:80-81
except Exception as e:
    logger.error(f"Error evaluating rule {rule.__class__.__name__}: {e}")

# enforcement.py:70-73
except Exception as e:
    result["success"] = False
    result["errors"].append(f"{symbol}: {e}")
    logger.error(f"Failed to close positions for {symbol}: {e}")
```

**Impact**: HIGH
- **Why**: Generic error handling makes debugging harder, no structured error recovery
- **Users**: Developers (debugging), operations (alerting)
- **Can deploy without**: Yes, but error recovery poor

**What's Missing**:

#### 4.1 Custom Exception Hierarchy

```python
# src/risk_manager/exceptions.py

class RiskManagerError(Exception):
    """Base exception for all Risk Manager errors."""

    def __init__(self, message: str, **kwargs):
        self.message = message
        self.context = kwargs
        super().__init__(message)


class ConfigurationError(RiskManagerError):
    """Configuration-related errors."""
    pass


class SDKError(RiskManagerError):
    """Project-X SDK integration errors."""
    pass


class ConnectionError(SDKError):
    """SDK connection errors."""
    pass


class AuthenticationError(SDKError):
    """SDK authentication errors."""
    pass


class StateError(RiskManagerError):
    """State management errors."""
    pass


class DatabaseError(StateError):
    """Database operation errors."""
    pass


class RuleViolationError(RiskManagerError):
    """Rule violation (not a traditional error, but needs special handling)."""

    def __init__(self, rule_name: str, violation_data: dict, **kwargs):
        self.rule_name = rule_name
        self.violation_data = violation_data
        super().__init__(
            f"Rule {rule_name} violated",
            rule=rule_name,
            violation=violation_data,
            **kwargs
        )


class EnforcementError(RiskManagerError):
    """Enforcement action failed."""

    def __init__(self, action: str, reason: str, **kwargs):
        self.action = action
        self.reason = reason
        super().__init__(
            f"Enforcement action '{action}' failed: {reason}",
            action=action,
            **kwargs
        )


class ValidationError(RiskManagerError):
    """Data validation errors."""

    def __init__(self, field: str, value: any, reason: str, **kwargs):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(
            f"Validation failed for {field}: {reason}",
            field=field,
            value=value,
            **kwargs
        )
```

**Why Important**:
- Better error categorization
- Structured error data (context dict)
- Easier error handling (catch specific exceptions)
- Better logging and alerting

**Estimated Effort**: 1 day

---

#### 4.2 Error Recovery Patterns

```python
# src/risk_manager/utils/retry.py

import asyncio
from functools import wraps
from typing import Callable, Type

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """
    Retry decorator with exponential backoff.

    Usage:
        @retry_with_backoff(max_retries=3, base_delay=2.0)
        async def risky_operation():
            # SDK call that might fail
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            delay = base_delay

            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        raise

                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} after {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)  # Exponential backoff

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for failing operations.

    States:
    - CLOSED: Normal operation
    - OPEN: Failing, reject immediately
    - HALF_OPEN: Testing if recovered
    """

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker."""

        # If circuit is OPEN, check if timeout passed
        if self.state == "OPEN":
            if self.last_failure_time and (datetime.now() - self.last_failure_time).total_seconds() > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)

            # Success - reset circuit if HALF_OPEN
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0

            return result

        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.now()

            # Open circuit if threshold reached
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"

            raise


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass
```

**Why Important**:
- Prevent cascading failures
- Automatic recovery from transient errors
- Better system resilience

**Estimated Effort**: 3 days
- Day 1: Implement retry and circuit breaker
- Day 2: Add to SDK calls
- Day 3: Testing and tuning

**Total Error Handling Effort**: 4 days

---

### Category 5: Configuration Management ✅ IMPLEMENTED

**Status**: ✅ **FULLY IMPLEMENTED**

**Evidence**:
```python
# config.py:10-79
class RiskConfig(BaseSettings):
    """Risk Manager configuration."""

    # Pydantic-based configuration
    # Environment variable support
    # YAML file loading
    # Type validation
```

**What's Working**:
- ✅ Pydantic models for type safety
- ✅ Environment variable support
- ✅ YAML file loading
- ✅ Validation on load
- ✅ Default values

**What's Missing** (minor):
- 🔄 Environment-specific configs (dev vs prod)
- 🔄 Secrets management (API keys in .env)
- 🔄 Feature flags

**Gap Details**:

**Environment-Specific Configuration**:
```python
# Need to add:
class RiskConfig(BaseSettings):
    environment: str = "development"  # ✅ Already exists

    # But need environment-specific overrides:
    @classmethod
    def for_environment(cls, env: str) -> "RiskConfig":
        """Load config for specific environment."""
        base_config = cls()

        # Load environment-specific overrides
        env_file = f".env.{env}"
        if Path(env_file).exists():
            # Apply overrides
            pass

        return base_config
```

**Secrets Management**:
```python
# Currently: API keys in .env (acceptable)
# Better: Use secret management service for production

# Add support for:
# - AWS Secrets Manager
# - Azure Key Vault
# - HashiCorp Vault
```

**Feature Flags**:
```python
# Add to RiskConfig:
class RiskConfig(BaseSettings):
    # Feature flags
    feature_flags: dict[str, bool] = {
        "enable_ai": False,
        "enable_pattern_recognition": False,
        "enable_advanced_monitoring": False,
    }
```

**Impact**: MEDIUM
- **Why**: Nice to have, not blocking
- **Users**: DevOps (deployment)
- **Can deploy without**: Yes

**Estimated Effort**: 3 days
- Day 1: Environment-specific configs
- Day 2: Secrets management integration
- Day 3: Feature flags

---

### Category 6: Data Validation ✅ IMPLEMENTED

**Status**: ✅ **FULLY IMPLEMENTED**

**Evidence**:
```python
# config.py uses Pydantic for validation
# events.py uses dataclasses with type hints
# All SDK data validated by Project-X SDK
```

**What's Working**:
- ✅ Pydantic models validate configuration
- ✅ Type checking via Python type hints
- ✅ Dataclasses for event structures
- ✅ SDK validates all trading data

**No gaps identified!**

---

## Critical Path Analysis

### High-Priority Infrastructure (Blocks Features)

**Must Have Before Launch**:

1. **DateTime Utilities** (2 days) - ⚠️ CRITICAL
   - **Blocks**: Daily reset (RULE-003, RULE-013)
   - **Why**: Can't calculate "5:00 PM ET" without timezone utils
   - **Priority**: 1

2. **Error Handling** (4 days) - ⚠️ CRITICAL
   - **Blocks**: Production reliability
   - **Why**: Need graceful error recovery
   - **Priority**: 2

3. **Monitoring & Metrics** (7 days) - ⚠️ CRITICAL
   - **Blocks**: Production operations
   - **Why**: Can't monitor system health
   - **Priority**: 3

**Nice to Have**:

4. **Remaining Utilities** (3 days)
   - Validation, math, formatting utilities
   - **Priority**: 4

5. **Log Enhancements** (1 day)
   - JSON logging, compression
   - **Priority**: 5

6. **Config Enhancements** (3 days)
   - Environment-specific, secrets management
   - **Priority**: 6

**Total Critical Path**: 13 days (~3 weeks)

---

## Recommended Implementation Order

### Week 1: DateTime Utilities + Error Handling

**Days 1-2: DateTime Utilities** ⚠️ HIGHEST PRIORITY
```
✓ Implement timezone utilities
✓ Midnight ET calculation
✓ Trading hours check
✓ Next reset time calculation
✓ Unit tests
✓ Integration with daily reset rules
```

**Days 3-4: Custom Exceptions**
```
✓ Define exception hierarchy
✓ Update all error handling
✓ Add context to exceptions
✓ Update logging
```

**Day 5: Retry & Circuit Breaker**
```
✓ Implement retry decorator
✓ Implement circuit breaker
✓ Add to SDK calls
✓ Testing
```

---

### Week 2: Monitoring & Remaining Utilities

**Days 1-3: System Monitoring**
```
✓ Health monitoring
✓ Metrics collection
✓ Performance tracking
✓ Integration with RiskEngine
```

**Days 4-5: Business Metrics & Alerts**
```
✓ Business metrics collector
✓ Alert manager
✓ CLI integration
✓ Testing
```

---

### Week 3: Remaining Utilities + Polish

**Days 1-2: Validation & Math Utilities**
```
✓ Input validation
✓ P&L calculations
✓ Position sizing
✓ Testing
```

**Days 3-4: String Formatting**
```
✓ Currency formatting
✓ Duration formatting
✓ CLI display utilities
✓ Testing
```

**Day 5: Log & Config Enhancements**
```
✓ JSON logging
✓ Log compression
✓ Environment-specific configs
✓ Documentation
```

---

## Testing Requirements

**For Each Infrastructure Component**:

### 1. DateTime Utilities
```python
# tests/unit/test_utils/test_datetime.py

def test_get_et_timezone():
    """Test ET timezone retrieval."""

def test_get_midnight_et():
    """Test midnight calculation."""

def test_get_next_reset_time():
    """Test reset time calculation."""
    # Edge cases:
    # - Before reset time (same day)
    # - After reset time (next day)
    # - Exactly at reset time

def test_is_trading_hours():
    """Test trading hours check."""
    # Edge cases:
    # - Before market open
    # - During market hours
    # - After market close
    # - Weekends
```

### 2. Error Handling
```python
# tests/unit/test_utils/test_retry.py

@pytest.mark.asyncio
async def test_retry_with_backoff_success():
    """Test retry succeeds after failures."""

@pytest.mark.asyncio
async def test_retry_with_backoff_exhausted():
    """Test retry gives up after max attempts."""

@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    """Test circuit breaker opens after threshold."""
```

### 3. Monitoring
```python
# tests/unit/test_monitoring/test_health.py

def test_health_monitor_tracks_events():
    """Test event tracking."""

def test_health_monitor_calculates_throughput():
    """Test throughput calculation."""

def test_health_monitor_detects_unhealthy():
    """Test unhealthy detection."""
```

---

## Blockers Analysis

**What's Blocked by Infrastructure Gaps**:

### Blocked: Daily Reset Feature
- ❌ **Missing**: DateTime utilities (get_midnight_et, get_next_reset_time)
- ❌ **Impact**: RULE-003 (Daily Realized Loss) can't reset at 5 PM
- ❌ **Impact**: RULE-013 (Daily Realized Profit) can't reset at 5 PM
- ⏱️ **Effort to Unblock**: 2 days

### Blocked: Production Debugging
- ❌ **Missing**: JSON structured logging
- ❌ **Impact**: Hard to parse logs programmatically
- ⏱️ **Effort to Unblock**: 1 day

### Blocked: System Resilience
- ❌ **Missing**: Error recovery (retry, circuit breaker)
- ❌ **Impact**: Transient SDK errors cause failures
- ⏱️ **Effort to Unblock**: 3 days

### Blocked: Production Monitoring
- ❌ **Missing**: Health monitoring, metrics, alerting
- ❌ **Impact**: Can't detect issues, no dashboards
- ⏱️ **Effort to Unblock**: 7 days

### NOT Blocked
- ✅ **Can implement**: All rules (except daily reset timing)
- ✅ **Can implement**: All enforcement actions
- ✅ **Can implement**: SDK integration
- ✅ **Can implement**: Basic configuration

---

## Impact Assessment

### 1. DateTime Utilities
- **Impact**: ⚠️ **CRITICAL**
- **Reason**: Daily reset is core feature, requires ET timezone
- **Users**: All users with daily loss/profit limits
- **Workaround**: None - feature doesn't work without this

### 2. Utilities Module (Validation, Math, Formatting)
- **Impact**: 🔶 **MEDIUM-HIGH**
- **Reason**: Code duplication, inconsistent calculations, poor UX
- **Users**: Developers (code reuse), traders (CLI formatting)
- **Workaround**: Implement inline (but duplicated code)

### 3. Monitoring & Metrics
- **Impact**: ⚠️ **HIGH**
- **Reason**: Production operations impossible without observability
- **Users**: Operations team, support, business analysts
- **Workaround**: Manual log inspection (not scalable)

### 4. Error Handling
- **Impact**: ⚠️ **HIGH**
- **Reason**: System reliability depends on graceful error recovery
- **Users**: End users (system stays up), developers (debugging)
- **Workaround**: Generic error handling (current state - poor UX)

### 5. Log Enhancements (JSON, compression)
- **Impact**: 🔷 **MEDIUM**
- **Reason**: Production log management harder
- **Users**: Operations team
- **Workaround**: Text logs work, just harder to parse

### 6. Config Enhancements
- **Impact**: 🔷 **MEDIUM**
- **Reason**: Dev/prod separation, secrets management
- **Users**: DevOps team
- **Workaround**: Manual environment management

---

## Summary & Recommendations

### Current State
- **8-Checkpoint Logging**: ✅ Excellent - fully implemented
- **Basic Configuration**: ✅ Good - Pydantic working well
- **Data Validation**: ✅ Good - type safety in place
- **Utilities**: ❌ **Missing** - critical gap
- **Monitoring**: ❌ **Missing** - critical gap
- **Error Handling**: 🔄 **Basic** - needs improvement

### Immediate Actions (Week 1)
1. ⚠️ **Implement datetime utilities** (2 days) - **UNBLOCKS DAILY RESET**
2. ⚠️ **Add error handling** (4 days) - **IMPROVES RELIABILITY**

### Short-Term (Weeks 2-3)
1. Implement monitoring & metrics (7 days)
2. Add remaining utilities (3 days)
3. Enhance logging (1 day)

### Long-Term (Month 2)
1. Advanced alerting (Discord/email)
2. Performance profiling
3. Distributed tracing (if microservices)

### Can Deploy Without
- ✅ JSON logging (nice to have)
- ✅ Advanced monitoring (but harder to support)
- ❌ DateTime utilities (daily reset won't work)
- ❌ Basic error handling (system fragile)

### Effort Summary
- **Critical Path**: 13 days (~3 weeks)
- **Nice to Have**: 4 days
- **Total**: ~4 weeks for complete infrastructure

---

## File Count & Size Analysis

**Current Infrastructure**:
```
src/risk_manager/
├── core/              ✅ 5 files (manager, engine, events, config, __init__)
├── sdk/               ✅ 4 files (enforcement, event_bridge, suite_manager, __init__)
├── state/             ✅ 3 files (database, pnl_tracker, __init__)
├── rules/             ✅ 5 files (base, daily_loss, max_position, max_contracts_per_instrument, __init__)
├── integrations/      ✅ 2 files (trading, __init__)
├── ai/                ✅ 2 files (integration, __init__)
├── monitoring/        ❌ 0 files (EMPTY DIRECTORY)
└── utils/             ❌ Directory doesn't exist

Total: 21 files, 2,828 lines
```

**After Implementation** (projected):
```
src/risk_manager/
├── utils/             NEW 5 files
│   ├── datetime_utils.py      (~150 lines)
│   ├── validation.py          (~100 lines)
│   ├── math.py                (~80 lines)
│   ├── formatting.py          (~120 lines)
│   └── retry.py               (~150 lines)
│
├── monitoring/        NEW 3 files
│   ├── health.py              (~200 lines)
│   ├── metrics.py             (~180 lines)
│   └── alerts.py              (~100 lines)
│
└── exceptions.py      NEW 1 file (~100 lines)

New Total: 30 files, ~4,008 lines
Growth: +9 files, +1,180 lines
```

---

## Conclusion

**Infrastructure is 60% complete**:
- ✅ **Excellent**: 8-checkpoint logging, configuration, validation
- 🔄 **Partial**: Error handling, log management
- ❌ **Missing**: Utilities (critical), monitoring (critical)

**Key Recommendation**: **Implement datetime utilities FIRST** (2 days) to unblock daily reset feature, then add monitoring (1 week) for production readiness.

**Total Effort**: 3 weeks to production-ready infrastructure.

---

**Analysis Complete**: 2025-10-25
**Researcher**: RESEARCHER 7 - Cross-Cutting Infrastructure Gap Analyst
**Next Step**: Coordinator review and prioritization

---

## Appendix: Quick Reference

### Files to Create

**High Priority**:
1. `src/risk_manager/utils/datetime_utils.py` (150 lines, 2 days)
2. `src/risk_manager/exceptions.py` (100 lines, 1 day)
3. `src/risk_manager/utils/retry.py` (150 lines, 2 days)
4. `src/risk_manager/monitoring/health.py` (200 lines, 2 days)
5. `src/risk_manager/monitoring/metrics.py` (180 lines, 2 days)

**Medium Priority**:
6. `src/risk_manager/utils/validation.py` (100 lines, 1 day)
7. `src/risk_manager/utils/math.py` (80 lines, 1 day)
8. `src/risk_manager/utils/formatting.py` (120 lines, 1 day)
9. `src/risk_manager/monitoring/alerts.py` (100 lines, 1 day)

**Total**: 9 new files, ~1,180 lines, 13 days

### Integration Points

**DateTime Utilities → Rules**:
- RULE-003 (Daily Realized Loss) needs `get_next_reset_time()`
- RULE-013 (Daily Realized Profit) needs `get_next_reset_time()`
- RULE-009 (Session Block Outside) needs `is_trading_hours()`

**Monitoring → RiskEngine**:
- `RiskEngine.evaluate_rules()` calls `health_monitor.record_event()`
- `RiskEngine._handle_violation()` calls `metrics.record_violation()`

**Error Handling → SDK Calls**:
- All `enforcement.py` methods use `@retry_with_backoff`
- All `trading.py` SDK calls use circuit breaker
