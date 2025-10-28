# Sanity Checks

External dependency validation checks.

## What Are Sanity Checks?

**Sanity checks** validate that **external dependencies** are accessible and functional.

They are different from:
- **Unit tests**: Test our code in isolation with mocks
- **Integration tests**: Test our code interacting with real dependencies
- **Smoke tests**: Test our service boots and processes events
- **E2E tests**: Test complete workflows through our system

**Sanity checks** answer: "Can we reach and use external services?"

## Available Sanity Checks

### 1. Auth Sanity Check

**Purpose**: Verify TopstepX authentication works with real credentials.

**Validates**:
1. Environment variables are set (API_KEY, USERNAME, ACCOUNT_NAME)
2. Can connect to TopstepX API
3. Can obtain JWT token
4. Token is valid (not expired)
5. Account exists and is accessible
6. Account has trading permissions

**Usage**:
```bash
# Run check
python src/sanity/auth_sanity.py

# Check exit code
echo $?
# 0 = Success (auth works)
# 1 = Auth failed (connection/API error)
# 2 = Config error (missing credentials)
# 3 = SDK not available (mock SDK detected)
```

**Example Output** (Success):
```
======================================================================
               AUTH SANITY CHECK
======================================================================

----------------------------------------------------------------------
STEP 1: Checking Environment Variables
----------------------------------------------------------------------
[OK] PROJECT_X_API_KEY: tj5F5k0j...n7s=
[OK] PROJECT_X_USERNAME: jakertrader
[OK] PROJECT_X_ACCOUNT_NAME: PRAC-V2-126244-84184528

[OK] PASSED: All environment variables set

----------------------------------------------------------------------
STEP 2: Connecting to TopstepX
----------------------------------------------------------------------
Connecting to TopstepX API...
[OK] Connection established

----------------------------------------------------------------------
STEP 3: Retrieving Account Information
----------------------------------------------------------------------
[OK] Account Name: PRAC-V2-126244-84184528
[OK] Account ID: 126244
[OK] Balance: $150,000.00
[OK] Account Type: SIMULATED

----------------------------------------------------------------------
STEP 4: Checking Trading Permissions
----------------------------------------------------------------------
[OK] Trading Enabled: True

[OK] Disconnected from TopstepX

======================================================================
                    AUTH SANITY PASSED
======================================================================
```

**Example Output** (SDK Not Available):
```
======================================================================
               AUTH SANITY CHECK
======================================================================

X FAILED: project-x-py SDK not available

The sanity check requires the REAL project-x-py SDK.
Currently only a mock SDK is installed.

To install the real SDK:
  1. Obtain the project-x-py package (version >=3.5.8)
  2. Install: pip install project-x-py
  3. Run this check again

Note: The mock SDK is sufficient for unit tests,
but sanity checks need to connect to the real TopstepX API.

Exit code: 3
```

**When to Use**:
- Before deploying to production
- After changing credentials
- When troubleshooting connectivity issues
- As part of environment validation
- In CI/CD pipeline to validate secrets

**Requirements**:
- Real TopstepX credentials in environment variables
- Network connectivity to TopstepX API
- Python 3.12+ with project-x-py SDK installed

---

### 2. Logic Sanity Check

**Purpose**: Verify risk rules work with real market data.

**Validates**:
1. Can fetch real positions from TopstepX
2. Can fetch real orders from TopstepX
3. Risk rules can process real data without crashes
4. Rule logic evaluates correctly with real positions
5. Data types match expectations (int/float sizes, etc.)

**Usage**:
```bash
# Run check
python src/sanity/logic_sanity.py

# Check exit code
echo $?
# 0 = Logic works with real data
# 1 = Logic fails with real data
# 2 = Cannot fetch real data
```

**Example Output**:
```
╔════════════════════════════════════════════════════════════════════╗
║               LOGIC SANITY CHECK                                   ║
╚════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: Connecting to TopstepX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Connected

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: Fetching Real Positions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Fetched 2 positions

  Sample position:
    Size: 3
    Type: LONG
    Contract: MNQZ24...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: Fetching Real Orders
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Fetched 1 open orders

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: Testing Max Contracts Rule Logic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Rule Configuration:
    Max Contracts: 2
    Per Instrument: False
    Action: flatten

  Current Market State:
    Total contracts: 3
    Rule limit: 2
    Would violate: True

  ⚠ Current position exceeds max contracts!
    This is expected if you're testing with > 2 contracts
    The rule logic is working correctly (detected violation)

✓ PASSED: Max contracts logic works with real data

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: Validating Data Types
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Data types are valid

✓ Disconnected from TopstepX

╔════════════════════════════════════════════════════════════════════╗
║                    ✓ LOGIC SANITY PASSED                          ║
╚════════════════════════════════════════════════════════════════════╝
```

**When to Use**:
- Before deploying to production
- After implementing new risk rules
- When troubleshooting rule evaluation issues
- After SDK version updates
- When real market data types change

**Requirements**:
- TopstepX authentication configured
- Active market data subscription
- Python 3.12+ with project-x-py SDK installed

---

### 3. Enforcement Sanity Check

**Purpose**: Verify we can place and cancel orders safely.

**Validates**:
1. Can place test orders via SDK
2. Orders are accepted by TopstepX
3. Can cancel orders
4. Orders are actually cancelled
5. No accidental fills (uses LIMIT orders far from market)

**SAFETY**: Uses limit orders 50% below market price - will never fill.

**Usage**:
```bash
# Run check
python src/sanity/enforcement_sanity.py

# Check exit code
echo $?
# 0 = Can place/cancel orders
# 1 = Cannot place orders
# 2 = Cannot cancel orders
```

**Example Output**:
```
╔════════════════════════════════════════════════════════════════════╗
║               ENFORCEMENT SANITY CHECK                             ║
╚════════════════════════════════════════════════════════════════════╝

⚠ SAFETY: This check places a test order FAR from market price
  The order will NOT fill and will be cancelled immediately.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: Connecting to TopstepX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Connected

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: Getting Active Contract
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Got active contract
  Contract ID: abc123...
  Symbol: MNQ

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: Placing Test Order (SAFE - Far from market)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Current market price: $19,245.00
  Safe limit price: $9,622.50 (50% below market)

  Order details:
    Side: BUY
    Size: 1 contract
    Type: LIMIT
    Price: $9622.50
    SAFETY: This order will NOT fill (price too low)

  Placing order...
  ✓ Order placed successfully!
    Order ID: order-123

  Waiting 2 seconds for order to register...
  ✓ Order verified in open orders

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: Cancelling Test Order
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Cancelling order order-123...
  ✓ Order cancelled successfully!

  Waiting 2 seconds to verify cancellation...
  ✓ Order confirmed cancelled (not in open orders)

✓ Cleanup: Test order cancelled
✓ Disconnected from TopstepX

╔════════════════════════════════════════════════════════════════════╗
║                  ✓ ENFORCEMENT SANITY PASSED                      ║
╚════════════════════════════════════════════════════════════════════╝

All enforcement actions work correctly:
  ✓ Can place orders
  ✓ Can cancel orders
  ✓ Orders are processed by TopstepX
```

**When to Use**:
- Before deploying to production
- After SDK version updates
- When troubleshooting order placement issues
- After TopstepX API changes
- Before enabling enforcement on live accounts

**Requirements**:
- TopstepX authentication configured
- Account has order placement permissions
- Python 3.12+ with project-x-py SDK installed
- **IMPORTANT**: Only run on simulated accounts initially

---

## Sanity Check Runner

Run all sanity checks in sequence:

```bash
# Run all checks (auth + logic + enforcement)
python src/sanity/runner.py full

# Run quick checks (auth + logic only, ~7s)
python src/sanity/runner.py quick

# Run individual check
python src/sanity/runner.py auth
python src/sanity/runner.py logic
python src/sanity/runner.py enforcement

# Show help
python src/sanity/runner.py --help
```

**Runner Output**:
```
╔════════════════════════════════════════════════════════════════════╗
║                    SANITY CHECK SUITE                              ║
╚════════════════════════════════════════════════════════════════════╝

Running all sanity checks to verify external dependencies...

─────────────────────────────────────────────────────────────────────
CHECK 1: Authentication Sanity
─────────────────────────────────────────────────────────────────────
[Auth check output...]

─────────────────────────────────────────────────────────────────────
CHECK 2: Logic Sanity
─────────────────────────────────────────────────────────────────────
[Logic check output...]

─────────────────────────────────────────────────────────────────────
CHECK 3: Enforcement Sanity
─────────────────────────────────────────────────────────────────────
[Enforcement check output...]

╔════════════════════════════════════════════════════════════════════╗
║                         SUMMARY                                    ║
╚════════════════════════════════════════════════════════════════════╝

  Auth: ✓ PASSED (exit code: 0)
  Logic: ✓ PASSED (exit code: 0)
  Enforcement: ✓ PASSED (exit code: 0)

╔════════════════════════════════════════════════════════════════════╗
║                    ✓ ALL CHECKS PASSED                            ║
╚════════════════════════════════════════════════════════════════════╝
```

## Exit Codes

All sanity checks use standardized exit codes:
- `0` = Success (sanity check passed)
- `1` = Failure (external service issue)
- `2` = Configuration error (missing credentials, invalid config)
- `3` = SDK not available (mock SDK detected, need real SDK)

## Adding New Sanity Checks

To add a new sanity check:

1. Create new file in `src/sanity/`
2. Implement check class with `run()` method returning exit code
3. Add to `__init__.py`
4. Update this README

**Template**:
```python
class MySanityCheck:
    async def run(self) -> int:
        """
        Returns:
            0 = Success
            1 = Failure
            2 = Config error
            3 = SDK not available
        """
        # Implementation
        pass

if __name__ == "__main__":
    exit_code = asyncio.run(MySanityCheck().run())
    sys.exit(exit_code)
```

## Best Practices

1. **Fast**: Sanity checks should complete in <10 seconds
2. **Read-only**: Never modify external state
3. **Clear output**: Use progress indicators (✓/✗)
4. **Exit codes**: Always return 0/1/2 consistently
5. **Cleanup**: Always disconnect/cleanup resources
6. **Error messages**: Provide actionable fix suggestions

## Integration with Test Runner

Sanity checks can be integrated into the test runner menu:

```python
# In run_tests.py
[a] Auth SANITY (TopstepX credentials)
```

This allows developers to quickly validate external dependencies before running tests or deploying.
