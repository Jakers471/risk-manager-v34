
## Who/Where

* **OS/Env:** Windows (PowerShell), Python 3.13 at `C:\Users\jakers\AppData\Local\Programs\Python\Python313\python.exe`
* **Project root:** `C:\Users\jakers\Desktop\risk-manager-v34`
* **SDK:** `project_x_py` (TopstepX / ProjectX), SignalR over WebSocket to `https://rtc.topstepx.com/hubs/{user|market}`

## What we’re fixing (current blocker)

**No trade/position/order events are received** because the **SignalR transport never starts** (WebSocket connect/upgrade doesn’t establish). EventBridge/listeners are fine; upstream WS is dead.

## Key evidence (from logs/tests)

* During connect: `WebSocket error` at `connection_management.connect()`; later runs show **`Status: ❌ NOT STARTED`** and **`⚠️ No account_info available`**.
* `Test-NetConnection rtc.topstepx.com -Port 443` → **succeeds** (network + TLS reachable).
* Negotiate probes:

  * `HEAD` to `/hubs/user/negotiate` → **405 Method Not Allowed** (normal; must use POST).
  * `POST` to `/hubs/market/negotiate` **without token** → **401 Unauthorized** (`WWW-Authenticate: Bearer`) — expected when missing/invalid token.
* Before admin fixes: firewall query denied; after running admin script:

  * **Windows Time synced**, **proxy cleared**, **Python allowed in firewall**, port **443 reachable**.
* Verification/listening tests show 0 events; logs always end with **hubs disconnected**.

## Most likely root cause (ranked)

1. **Auth token (JWT) not applied correctly to SignalR negotiate/upgrade** (missing/expired or placed in the wrong location: query vs header).
2. **Security software (AV/HTTPS inspection) blocking WebSocket upgrade** even though 443 is open.
3. Less likely: SDK not starting transport after negotiate (we’ll guard for it).

## Files/Scripts we’re using right now

* `RUN_WEBSOCKET_TEST.bat` — minimal WS connectivity test (prints transport status).
* `RUN_FULL_DIAGNOSTIC.bat` — step-by-step checks (time, proxies, firewall, negotiate probes, WS test).
* `fix_admin_requirements.ps1` — starts Windows Time, clears proxies, adds Python firewall rule.
* `test_websocket_connection.py` — creates `TradingSuite(["MNQ"])`, attempts realtime connect, prints status.
* (Optional/next) `RUN_JWT_TEST.bat` — to print/validate `PROJECTX_JWT` contents.

## Required behavior (definition of done)

* **WS transport connects** (logs show “Connected to user_hub/market_hub” or equivalent).
* 30–90s listener test receives **≥1 position/order/trade event** after placing a **market** order in **MNQ**.

## Action plan for the agent (do these in order)

1. **Verify JWT exists & isn’t expired**

   * Print env token length and `exp`:

     ```powershell
     "JWT length: " + ($env:PROJECTX_JWT ?? "<empty>").Length
     $tok = $env:PROJECTX_JWT
     $payload = ($tok.Split('.')[1] + '===').Replace('_','/').Replace('-','+')
     $json = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload))
     $exp = (ConvertFrom-Json $json).exp
     "exp: $exp | now(utc): $([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"
     ```
   * If empty/expired: `projectx auth logout && projectx auth login`, then reopen terminal.

2. **Prove negotiate accepts the token**

   * **Query param mode**:

     ```powershell
     $TOKEN = $env:PROJECTX_JWT
     curl -X POST "https://rtc.topstepx.com/hubs/market/negotiate?negotiateVersion=1&access_token=$TOKEN" -H "Content-Type: application/json"
     ```
   * **Header mode**:

     ```powershell
     curl -X POST "https://rtc.topstepx.com/hubs/market/negotiate?negotiateVersion=1" `
          -H "Authorization: Bearer $TOKEN" `
          -H "Content-Type: application/json"
     ```
   * **Success criteria:** JSON with `availableTransports`/`connectionToken`.

     * If **header works but query fails** → gateway requires **Authorization header on negotiate** (common). Adjust SDK config accordingly.

3. **Ensure SDK sends token on negotiate (and upgrade)**

   * In `test_websocket_connection.py` (or wherever `TradingSuite` is constructed), pass headers (and keep query param if the WS upgrade expects it):

     ```python
     import os
     token = os.getenv("PROJECTX_JWT")

     suite = TradingSuite(
         ["MNQ"],
         auth_headers={"Authorization": f"Bearer {token}"},
         auth_query_params={"access_token": token},  # keep if SDK uses it for WS upgrade
         # transport="webSockets",  # default; see step 4
     )

     suite.connect()
     # If available:
     # suite.realtime_connection.start()
     # suite.realtime_connection.wait_ready(30)
     assert suite.realtime_connection.is_connected(), "SignalR not connected"
     ```
   * If headers must be set deeper (SignalR client options), wire them there.

4. **Isolate network vs auth by forcing LongPolling once**

   ```python
   suite = TradingSuite(
       ["MNQ"],
       transport="longPolling",
       auth_headers={"Authorization": f"Bearer {os.environ['PROJECTX_JWT']}"}
   )
   suite.connect()
   ```

   * **If longPolling connects:** auth is fine, **WebSocket is being blocked** by AV/HTTPS inspection. Temporarily disable AV “web shield/HTTPS scanning” and retry WS; hotspot test also isolates LAN/ISP.

5. **Re-run 90s listener test, but place the order only after connected**

   * Extend listen window to **90s**.
   * Wait for logs: **“Connected to user_hub” & “Connected to market_hub”**.
   * Place **market** order in **MNQ**; confirm ≥1 event.

## Notes/quirks already addressed

* Time sync was failing without admin → **fixed** (Windows Time running, resynced).
* Proxy envs cleared and WinHTTP proxy reset.
* Python firewall allow rule added (outbound 443).
* Earlier batch had a stray `with` in `.bat` causing `'with' is not recognized` — ensure batch files call `.py` via `py` or `python` and don’t inline Python.

## What to report back after you run the steps

* `JWT length` and `exp` vs current epoch.
* Result of **negotiate POST** (query vs header).
* Whether **longPolling** connects.
* The first log lines that say the hubs are **connected** (or any 401/403/TLS errors if not).

Once we know those, we can lock in the exact SDK auth configuration (header on negotiate + query/header on upgrade) or finalize the AV/HTTPS-inspection exclusion needed.
