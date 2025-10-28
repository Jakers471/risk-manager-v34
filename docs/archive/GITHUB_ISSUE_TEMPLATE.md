# WebSocket Connection Fails - SignalR Returns "NOT STARTED"

## Environment
- **OS:** Windows 11
- **Python:** 3.13
- **SDK Version:** 3.5.9 (from GitHub main branch)
- **signalrcore version:** 0.9.5

## Problem Description

WebSocket connections to TopstepX SignalR hubs fail with "NOT STARTED" status, despite:
- ✅ Authentication working (JWT generated successfully)
- ✅ Negotiate endpoint returning 200 OK with connectionToken
- ✅ WebSocket protocol supported (verified with `wscat`)
- ✅ Network/firewall not blocking (port 443 open, no proxy)

## Steps to Reproduce

```python
import asyncio
from project_x_py import TradingSuite

async def test():
    suite = await TradingSuite.create(["MNQ"])
    # WebSocket connection fails here
    # Status shows "NOT STARTED" instead of "CONNECTED"
    await suite.disconnect()

asyncio.run(test())
```

## Expected Behavior

WebSocket should connect and show:
```
Status: ✅ CONNECTED
Account data flows successfully
```

## Actual Behavior

```
Status: ❌ NOT STARTED
WebSocket error after 10 second timeout
No account_info available
```

## Diagnostic Evidence

### 1. Negotiate Phase Works

Manual test of negotiate endpoint:
```bash
curl -X POST "https://rtc.topstepx.com/hubs/market/negotiate?negotiateVersion=1&access_token=<JWT>" \
  -H "Content-Type: application/json"
```

**Result:** ✅ 200 OK
```json
{
  "connectionToken": "mBFOGJfECnEBKHHw031pgQ...",
  "connectionId": "E8eLkXVyhF5M2WniOMT0Fg",
  "negotiateVersion": 1,
  "availableTransports": [{"transport": "WebSockets"}]
}
```

### 2. WebSocket Protocol Works

Test with `wscat`:
```bash
wscat -c "wss://rtc.topstepx.com/hubs/user"
```

**Result:** ✅ WebSocket upgrade succeeds, returns 401 (auth expected)

This proves:
- WebSocket protocol works
- Network doesn't block WebSockets
- Issue is with JWT placement during upgrade

### 3. SDK Logs Show Timeout

```json
{"level":"INFO","message":"Using URL query parameter for JWT authentication"}
{"level":"ERROR","message":"WebSocket error","operation":"setup_connections"}
```

Connection times out after 10 seconds waiting for `on_open` callback.

## Root Cause Analysis

The SDK correctly:
1. ✅ Generates JWT via `/Auth/loginKey`
2. ✅ Calls negotiate with `?access_token=<JWT>` → Returns 200 OK
3. ✅ Builds URL: `https://rtc.topstepx.com/hubs/user?access_token=<JWT>`
4. ✅ Passes URL to `HubConnectionBuilder().with_url(url)`

But `signalrcore` library fails to:
- ❌ Complete WebSocket upgrade handshake
- ❌ Send JWT during upgrade (query param may be stripped)
- ❌ Trigger `on_open` callback

### Code Location

`src/project_x_py/realtime/connection_management.py:150-191`

```python
user_url_with_token = f"{self.user_hub_url}?access_token={self.jwt_token}"
self.user_connection = (
    HubConnectionBuilder()
    .with_url(user_url_with_token)
    # ...
    .build()
)
```

Then at line 354:
```python
await loop.run_in_executor(None, connection.start)  # This never completes
```

## Attempted Fixes

### 1. Added Authorization Header
```python
auth_headers = {"Authorization": f"Bearer {self.jwt_token}"}
if hasattr(self.user_connection, 'negotiate_headers'):
    self.user_connection.negotiate_headers = auth_headers
```
**Result:** ❌ Still fails

### 2. Disabled Windows Defender
**Result:** ❌ Still fails

### 3. Disabled Windows Firewall
**Result:** ❌ Still fails

## Workaround Needed

Is there a way to:
1. Force `signalrcore` to send JWT in Authorization header during WebSocket upgrade?
2. Override the WebSocket transport implementation?
3. Use a different SignalR library that works on Windows?

## Additional Context

- This affects ALL Windows users of the SDK
- The SDK has `uvloop` dependency which doesn't work on Windows (had to remove it)
- Official examples don't address this issue
- No documentation for troubleshooting WebSocket 401/connection failures

## Suggested Fix

The SDK should either:
1. Document this known issue and provide Windows-specific setup
2. Include a working WebSocket transport for Windows
3. Provide clear error messages when WebSocket fails (not just "WebSocket error")
4. Add retry logic or fallback transport mechanism

## Question for Maintainer

- Is this SDK officially supported on Windows?
- Are there known issues with `signalrcore` WebSocket upgrades?
- Is there a working example of TopstepX SignalR connection on Windows?

---

**This issue blocks all real-time functionality on Windows**, making the SDK unusable for:
- Real-time price data
- Order/position updates
- Trade notifications
- Any SignalR-dependent features
