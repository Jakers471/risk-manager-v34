"""
Demo of Auth Sanity Check Output

This shows what the output would look like with the real SDK.
"""

print("=" * 70)
print(" " * 15 + "AUTH SANITY CHECK")
print("=" * 70)
print()

print("-" * 70)
print("STEP 1: Checking Environment Variables")
print("-" * 70)
print("[OK] PROJECT_X_API_KEY: tj5F5k0j...n7s=")
print("[OK] PROJECT_X_USERNAME: jakertrader")
print("[OK] PROJECT_X_ACCOUNT_NAME: PRAC-V2-126244-84184528")
print()
print("[OK] PASSED: All environment variables set")

print()
print("-" * 70)
print("STEP 2: Connecting to TopstepX")
print("-" * 70)
print("Connecting to TopstepX API...")
print("[OK] Connection established")

print()
print("-" * 70)
print("STEP 3: Retrieving Account Information")
print("-" * 70)
print("[OK] Account Name: PRAC-V2-126244-84184528")
print("[OK] Account ID: 126244")
print("[OK] Balance: $150,000.00")
print("[OK] Account Type: SIMULATED")

print()
print("-" * 70)
print("STEP 4: Checking Trading Permissions")
print("-" * 70)
print("[OK] Trading Enabled: True")

print()
print("[OK] Disconnected from TopstepX")

print()
print("=" * 70)
print(" " * 20 + "AUTH SANITY PASSED")
print("=" * 70)
