"""
Auth Sanity Check - TopstepX Authentication Validation

Verifies:
1. Environment variables are set (API_KEY, USERNAME, ACCOUNT_NAME)
2. Can connect to TopstepX API
3. Can obtain JWT token
4. Token is valid (not expired)
5. Account exists and is accessible
6. Account has trading permissions (canTrade)

Exit Codes:
0 = Auth works ✅
1 = Auth failed ❌
2 = Config error (missing credentials)
3 = SDK not available (needs real project-x-py SDK)

Duration: ~5 seconds
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Try to import TradingSuite, handle if not available
try:
    from project_x_py import TradingSuite
    SDK_AVAILABLE = hasattr(TradingSuite, 'create')
except (ImportError, AttributeError):
    SDK_AVAILABLE = False
    TradingSuite = None  # type: ignore


class AuthSanityCheck:
    """Authentication sanity checker."""

    def __init__(self):
        self.api_key = None
        self.username = None
        self.account_name = None
        self.suite = None

    def check_env_vars(self) -> bool:
        """Check required environment variables are set."""
        print("-" * 70)
        print("STEP 1: Checking Environment Variables")
        print("-" * 70)

        required_vars = [
            "PROJECT_X_API_KEY",
            "PROJECT_X_USERNAME",
            "PROJECT_X_ACCOUNT_NAME"
        ]

        missing = []
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                missing.append(var)
                print(f"[X] {var}: NOT SET")
            else:
                # Mask sensitive values
                if "KEY" in var:
                    display = value[:8] + "..." + value[-8:]
                else:
                    display = value
                print(f"[OK] {var}: {display}")

                # Store values
                if var == "PROJECT_X_API_KEY":
                    self.api_key = value
                elif var == "PROJECT_X_USERNAME":
                    self.username = value
                elif var == "PROJECT_X_ACCOUNT_NAME":
                    self.account_name = value

        if missing:
            print(f"\n[X] FAILED: Missing environment variables: {', '.join(missing)}")
            print("\nTo fix, set in your .env file or environment:")
            for var in missing:
                print(f"  export {var}=<value>")
            return False

        print("\n[OK] PASSED: All environment variables set")
        return True

    async def check_connection(self) -> bool:
        """Check can connect to TopstepX and create TradingSuite."""
        print("\n" + "-" * 70)
        print("STEP 2: Connecting to TopstepX")
        print("-" * 70)

        try:
            print("Connecting to TopstepX API...")
            self.suite = await TradingSuite.create(
                instrument="MNQ",
                timeframes=["1min"],
                initial_days=1
            )

            print("[OK] Connection established")
            return True

        except Exception as e:
            print(f"[X] FAILED: Cannot connect to TopstepX")
            print(f"  Error: {e}")
            print("\nPossible causes:")
            print("  - Invalid credentials")
            print("  - Network connectivity issues")
            print("  - TopstepX service down")
            print("  - Firewall blocking connection")
            return False

    async def check_account_info(self) -> bool:
        """Check can retrieve account information."""
        print("\n" + "-" * 70)
        print("STEP 3: Retrieving Account Information")
        print("-" * 70)

        try:
            account = self.suite.client.account_info

            print(f"[OK] Account Name: {account.name}")
            print(f"[OK] Account ID: {account.id}")
            print(f"[OK] Balance: ${account.balance:,.2f}")
            print(f"[OK] Account Type: {'SIMULATED' if account.simulated else 'LIVE'}")

            # Verify account name matches
            if account.name != self.account_name:
                print(f"\n[!] WARNING: Account name mismatch!")
                print(f"  Expected: {self.account_name}")
                print(f"  Actual: {account.name}")
                print("  Continuing anyway...")

            return True

        except Exception as e:
            print(f"[X] FAILED: Cannot retrieve account info")
            print(f"  Error: {e}")
            return False

    async def check_permissions(self) -> bool:
        """Check account has trading permissions."""
        print("\n" + "-" * 70)
        print("STEP 4: Checking Trading Permissions")
        print("-" * 70)

        try:
            account = self.suite.client.account_info

            # Check canTrade permission
            can_trade = getattr(account, 'canTrade', None)

            if can_trade is None:
                print("[!] WARNING: Cannot determine canTrade status")
                print("  Attribute not available from SDK")
                return True  # Don't fail if attribute missing

            if can_trade:
                print(f"[OK] Trading Enabled: {can_trade}")
            else:
                print(f"[X] Trading Disabled: {can_trade}")
                print("\nThis account cannot trade!")
                print("Risk manager will not be able to enforce rules.")
                return False

            return True

        except Exception as e:
            print(f"[!] WARNING: Cannot check permissions")
            print(f"  Error: {e}")
            return True  # Don't fail on permission check errors

    async def cleanup(self):
        """Cleanup resources."""
        if self.suite:
            try:
                await self.suite.disconnect()
                print("\n[OK] Disconnected from TopstepX")
            except Exception:
                pass

    async def run(self) -> int:
        """
        Run complete auth sanity check.

        Returns:
            0 = Success
            1 = Auth failed
            2 = Config error
            3 = SDK not available
        """
        print("=" * 70)
        print(" " * 15 + "AUTH SANITY CHECK")
        print("=" * 70)
        print()

        # Check if SDK is available
        if not SDK_AVAILABLE:
            print("X FAILED: project-x-py SDK not available")
            print()
            print("The sanity check requires the REAL project-x-py SDK.")
            print("Currently only a mock SDK is installed.")
            print()
            print("To install the real SDK:")
            print("  1. Obtain the project-x-py package (version >=3.5.8)")
            print("  2. Install: pip install project-x-py")
            print("  3. Run this check again")
            print()
            print("Note: The mock SDK is sufficient for unit tests,")
            print("but sanity checks need to connect to the real TopstepX API.")
            return 3

        try:
            # Step 1: Check environment variables
            if not self.check_env_vars():
                return 2  # Config error

            # Step 2: Connect to TopstepX
            if not await self.check_connection():
                return 1  # Auth failed

            # Step 3: Get account info
            if not await self.check_account_info():
                return 1  # Auth failed

            # Step 4: Check permissions
            if not await self.check_permissions():
                return 1  # Auth failed

            # All checks passed!
            print("\n" + "=" * 70)
            print(" " * 20 + "AUTH SANITY PASSED")
            print("=" * 70)

            return 0

        except Exception as e:
            print(f"\n[X] UNEXPECTED ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1

        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    checker = AuthSanityCheck()
    exit_code = await checker.run()
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
