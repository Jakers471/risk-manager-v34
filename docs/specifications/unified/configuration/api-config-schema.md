# API Configuration Schema

**Document Type**: Unified Configuration Specification
**Created**: 2025-10-25
**Researcher**: Wave 3 Researcher 5 - Configuration System Specification Unification
**Status**: PRODUCTION READY

---

## Executive Summary

This document defines the **API configuration schema** for Risk Manager V34, covering ProjectX SDK connection settings, authentication, timeouts, and connection management.

**Note**: This can be integrated into `accounts.yaml` or kept as separate `api_config.yaml`.

---

## Complete YAML Schema

**File**: `config/api_config.yaml` (or integrated into `accounts.yaml`)

```yaml
# ==============================================================================
# API CONFIGURATION
# ==============================================================================
# Purpose: ProjectX SDK connection settings and API behavior
# ==============================================================================

# ==============================================================================
# PROJECTX API CREDENTIALS
# ==============================================================================
projectx:
  # Authentication
  username: "${PROJECT_X_USERNAME}"      # REQUIRED: From .env
  api_key: "${PROJECT_X_API_KEY}"        # REQUIRED: From .env

  # API Endpoints
  api_url: "https://api.topstepx.com/api"              # REST API
  websocket_url: "wss://api.topstepx.com"              # SignalR WebSocket

  # Environment
  environment: "production"              # "production" or "sandbox"

# ==============================================================================
# CONNECTION SETTINGS
# ==============================================================================
connection:
  # Timeouts (seconds)
  connect_timeout: 30                    # Initial connection timeout
  request_timeout: 10                    # API request timeout
  websocket_timeout: 60                  # WebSocket message timeout

  # Retry behavior
  retry:
    enabled: true                        # Enable automatic retries
    max_attempts: 3                      # Max retry attempts
    backoff_multiplier: 2.0              # Exponential backoff (2s, 4s, 8s)
    max_backoff_seconds: 60              # Max backoff time

  # Reconnection (WebSocket)
  reconnect:
    enabled: true                        # Auto-reconnect on disconnect
    initial_delay: 1                     # First reconnect after 1s
    max_delay: 300                       # Max 5 minutes between attempts
    max_attempts: 0                      # 0 = infinite attempts

  # Keep-alive (WebSocket)
  keep_alive:
    enabled: true                        # Send ping/pong
    interval_seconds: 30                 # Ping every 30s
    timeout_seconds: 10                  # Pong timeout

# ==============================================================================
# RATE LIMITING
# ==============================================================================
rate_limit:
  # API request rate limits
  requests:
    per_second: 10                       # Max 10 requests/second
    per_minute: 100                      # Max 100 requests/minute
    per_hour: 1000                       # Max 1000 requests/hour

  # Burst allowance
  burst:
    enabled: true                        # Allow burst requests
    size: 20                             # Burst up to 20 requests

  # Order placement rate limits
  orders:
    per_second: 2                        # Max 2 orders/second
    per_minute: 30                       # Max 30 orders/minute

# ==============================================================================
# ERROR HANDLING
# ==============================================================================
error_handling:
  # Retry on these HTTP status codes
  retry_on_status:
    - 429  # Too Many Requests
    - 500  # Internal Server Error
    - 502  # Bad Gateway
    - 503  # Service Unavailable
    - 504  # Gateway Timeout

  # Fatal errors (do not retry)
  fatal_status:
    - 401  # Unauthorized (bad credentials)
    - 403  # Forbidden (no permission)
    - 404  # Not Found (invalid endpoint)

  # Circuit breaker
  circuit_breaker:
    enabled: true                        # Enable circuit breaker
    failure_threshold: 5                 # Open after 5 failures
    timeout_seconds: 60                  # Try again after 60s
    half_open_attempts: 3                # Test with 3 requests

# ==============================================================================
# CACHING
# ==============================================================================
cache:
  # Cache API responses
  enabled: true                          # Enable caching

  # Account data cache
  account:
    ttl_seconds: 300                     # Cache 5 minutes
    max_size: 100                        # Max 100 cached accounts

  # Instrument data cache
  instruments:
    ttl_seconds: 3600                    # Cache 1 hour
    max_size: 500                        # Max 500 instruments

  # Market data cache
  market_data:
    ttl_seconds: 1                       # Cache 1 second (real-time)
    max_size: 1000                       # Max 1000 quotes

# ==============================================================================
# LOGGING
# ==============================================================================
logging:
  # API request/response logging
  log_requests: true                     # Log all API requests
  log_responses: false                   # Log responses (verbose)

  # Log levels
  level: "INFO"                          # DEBUG, INFO, WARNING, ERROR

  # Sensitive data masking
  mask_credentials: true                 # Mask API keys in logs
  mask_account_ids: false                # Mask account IDs

  # Performance logging
  log_slow_requests: true                # Log slow requests
  slow_threshold_ms: 1000                # > 1s is slow

# ==============================================================================
# ADVANCED SETTINGS
# ==============================================================================
advanced:
  # HTTP/2 support
  http2: false                           # Use HTTP/1.1 (more compatible)

  # Compression
  compression: true                      # Enable gzip compression

  # User agent
  user_agent: "RiskManager/3.4 (TopstepX)"

  # Pool settings
  connection_pool:
    max_connections: 10                  # Max concurrent connections
    max_keepalive: 5                     # Max keepalive connections

  # SSL/TLS
  ssl:
    verify: true                         # Verify SSL certificates
    cert_path: null                      # Custom CA cert (optional)
```

---

## Schema Details

### 1. Authentication

```yaml
projectx:
  username: "${PROJECT_X_USERNAME}"      # Environment variable
  api_key: "${PROJECT_X_API_KEY}"
  api_url: "https://api.topstepx.com/api"
  websocket_url: "wss://api.topstepx.com"
  environment: "production"              # or "sandbox"
```

**Validation**:
- `username` and `api_key` MUST be non-empty
- URLs MUST start with `https://` or `wss://`
- `environment` MUST be "production" or "sandbox"

### 2. Connection Timeouts

```yaml
connection:
  connect_timeout: 30                    # Max time to establish connection
  request_timeout: 10                    # Max time for API request
  websocket_timeout: 60                  # Max time for WebSocket message
```

**Validation**:
- All timeout values MUST be > 0
- Recommended: `connect_timeout` > `request_timeout`

### 3. Retry Behavior

```yaml
connection:
  retry:
    enabled: true
    max_attempts: 3                      # Retry up to 3 times
    backoff_multiplier: 2.0              # 2s, 4s, 8s exponential backoff
    max_backoff_seconds: 60              # Cap at 60s
```

**Validation**:
- `max_attempts` MUST be >= 1
- `backoff_multiplier` MUST be >= 1.0
- `max_backoff_seconds` MUST be > 0

### 4. Reconnection (WebSocket)

```yaml
connection:
  reconnect:
    enabled: true
    initial_delay: 1                     # Start with 1s delay
    max_delay: 300                       # Max 5 minutes
    max_attempts: 0                      # 0 = infinite
```

**Validation**:
- `initial_delay` <= `max_delay`
- `max_attempts` >= 0 (0 means infinite)

### 5. Rate Limiting

```yaml
rate_limit:
  requests:
    per_second: 10                       # API request rate
    per_minute: 100
    per_hour: 1000

  orders:
    per_second: 2                        # Order placement rate
    per_minute: 30
```

**Validation**:
- All rate limits MUST be > 0
- `per_second` * 60 <= `per_minute`
- `per_minute` * 60 <= `per_hour`
- Order rates <= request rates

---

## Pydantic Validation Models

```python
from pydantic import BaseModel, Field, field_validator

class ProjectXConfig(BaseModel):
    username: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=1)
    api_url: str = "https://api.topstepx.com/api"
    websocket_url: str = "wss://api.topstepx.com"
    environment: str = "production"

    @field_validator('api_url', 'websocket_url')
    def validate_url(cls, v):
        if not v.startswith(('https://', 'wss://')):
            raise ValueError(f"Invalid URL: {v}")
        return v

    @field_validator('environment')
    def validate_environment(cls, v):
        if v not in ['production', 'sandbox']:
            raise ValueError(f"Invalid environment: {v}")
        return v

class ConnectionConfig(BaseModel):
    connect_timeout: int = 30
    request_timeout: int = 10
    websocket_timeout: int = 60

    @field_validator('*')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError(f"Timeout must be > 0: {v}")
        return v

class RetryConfig(BaseModel):
    enabled: bool = True
    max_attempts: int = 3
    backoff_multiplier: float = 2.0
    max_backoff_seconds: int = 60

    @field_validator('max_attempts')
    def validate_attempts(cls, v):
        if v < 1:
            raise ValueError("max_attempts must be >= 1")
        return v

class APIConfig(BaseModel):
    projectx: ProjectXConfig
    connection: ConnectionConfig
    # ... other sections
```

---

## Example Configurations

### Example 1: Production (Recommended)

```yaml
projectx:
  username: "${PROJECT_X_USERNAME}"
  api_key: "${PROJECT_X_API_KEY}"
  api_url: "https://api.topstepx.com/api"
  websocket_url: "wss://api.topstepx.com"
  environment: "production"

connection:
  connect_timeout: 30
  request_timeout: 10
  websocket_timeout: 60

  retry:
    enabled: true
    max_attempts: 3
    backoff_multiplier: 2.0
    max_backoff_seconds: 60

  reconnect:
    enabled: true
    initial_delay: 1
    max_delay: 300
    max_attempts: 0                      # Infinite retries

rate_limit:
  requests:
    per_second: 10
    per_minute: 100

  orders:
    per_second: 2
    per_minute: 30
```

### Example 2: Development (Verbose Logging)

```yaml
projectx:
  username: "${PROJECT_X_USERNAME}"
  api_key: "${PROJECT_X_API_KEY}"
  environment: "sandbox"

logging:
  log_requests: true
  log_responses: true                    # Verbose
  level: "DEBUG"
  log_slow_requests: true
  slow_threshold_ms: 500                 # Lower threshold

connection:
  connect_timeout: 10                    # Fail fast
  request_timeout: 5

  retry:
    enabled: false                       # No retries (fail fast)
```

### Example 3: Aggressive (High Throughput)

```yaml
connection:
  request_timeout: 5                     # Fast timeout

rate_limit:
  requests:
    per_second: 20                       # Higher rate
    per_minute: 200

  orders:
    per_second: 5                        # More orders
    per_minute: 50

advanced:
  http2: true                            # Use HTTP/2
  compression: true
  connection_pool:
    max_connections: 20                  # More connections
```

---

## Integration Options

### Option 1: Separate File

**File**: `config/api_config.yaml`

```yaml
# Complete API configuration as shown above
```

**Load**:
```python
api_config = load_config('config/api_config.yaml')
```

### Option 2: Integrate into accounts.yaml

**File**: `config/accounts.yaml`

```yaml
# API credentials
topstepx:
  username: "${PROJECT_X_USERNAME}"
  api_key: "${PROJECT_X_API_KEY}"

# API settings
api:
  connection:
    connect_timeout: 30
    # ... other settings

# Accounts
accounts:
  - id: "ACCOUNT-001"
    # ... account config
```

**Recommendation**: **Option 2** (integrate into accounts.yaml) for simplicity.

---

## Summary

### Key Features

1. **Authentication**: Credentials and API endpoints
2. **Connection Management**: Timeouts, retries, reconnection
3. **Rate Limiting**: Prevent API abuse
4. **Error Handling**: Circuit breaker, retry logic
5. **Caching**: Reduce API calls
6. **Logging**: Request/response logging with masking

### Configuration Files

- **api_config.yaml**: API settings (THIS FILE) OR
- **accounts.yaml**: Integrated API + account config

---

**Document Complete**
**Created**: 2025-10-25
**Status**: PRODUCTION READY
