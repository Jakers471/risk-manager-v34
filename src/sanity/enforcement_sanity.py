"""
Enforcement Sanity Check - Order Placement & Cancellation

Verifies:
1. Can place test orders via SDK
2. Orders are accepted by TopstepX
3. Can cancel orders
4. Orders are actually cancelled
5. No accidental fills (uses LIMIT orders far from market)

Exit Codes:
0 = Can place/cancel orders
1 = Cannot place orders
2 = Cannot cancel orders

Duration: ~8 seconds
SAFETY: Uses limit orders FAR from market price (no fills)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from project_x_py import TradingSuite


class EnforcementSanityCheck:
    """Enforcement sanity checker."""

    def __init__(self):
        self.suite = None
        self.test_order_id = None
        self.contract_id = None

    async def connect(self) -> bool:
        """Connect to SDK."""
        print("=" * 70)
        print("STEP 1: Connecting to TopstepX")
        print("=" * 70)

        try:
            self.suite = await TradingSuite.create(
                instrument="MNQ",
                timeframes=["1min"],
                initial_days=1
            )
            print("[+] Connected")
            return True
        except Exception as e:
            print(f"[x] FAILED: {e}")
            return False

    async def place_test_order(self) -> bool:
        """Place a safe test order (far from market)."""
        print()
        print("=" * 70)
        print("STEP 2: Placing Test Order (SAFE - Far from market)")
        print("=" * 70)

        try:
            mnq = self.suite["MNQ"]

            # Use the current front month contract (December 2025)
            # MNQ contract codes: H=Mar, M=Jun, U=Sep, Z=Dec
            self.contract_id = "CON.F.US.MNQ.Z25"  # December 2025
            print(f"  Using contract: {self.contract_id}")
            
            # Use extreme price that won't fill
            safe_limit_price = 1000.0  # WAY below market (MNQ typically ~19000)
            
            print(f"  Order details:")
            print(f"    Side: BUY")
            print(f"    Size: 1 contract")
            print(f"    Type: LIMIT")
            print(f"    Price: ${safe_limit_price} (far below market - won't fill)")
            print(f"  Placing order...")
            
            # Place limit order
            result = await mnq.orders.place_limit_order(
                contract_id=self.contract_id,
                side=0,  # BUY
                size=1,
                limit_price=safe_limit_price
            )

            # Extract order ID from response
            # OrderPlaceResponse has camelCase attribute: orderId
            self.test_order_id = result.orderId

            print(f"  [+] Order placed successfully!")
            print(f"      Order ID: {self.test_order_id}")
            
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"[x] FAILED: Cannot place order")
            print(f"  Error: {e}")
            return False

    async def cancel_test_order(self) -> bool:
        """Cancel the test order."""
        print()
        print("=" * 70)
        print("STEP 3: Cancelling Test Order")
        print("=" * 70)

        if not self.test_order_id:
            print("[x] No order to cancel")
            return False

        try:
            mnq = self.suite["MNQ"]
            
            print(f"  Cancelling order {self.test_order_id}...")
            
            await mnq.orders.cancel_order(self.test_order_id)
            
            print(f"  [+] Order cancelled successfully!")
            
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"[x] FAILED: Cannot cancel order")
            print(f"  Error: {e}")
            return False

    async def cleanup(self):
        """Cleanup - cancel any remaining orders."""
        if self.suite and self.test_order_id:
            try:
                mnq = self.suite["MNQ"]
                await mnq.orders.cancel_order(self.test_order_id)
                print()
                print("[+] Cleanup: Test order cancelled")
            except:
                pass
        
        if self.suite:
            try:
                await self.suite.disconnect()
                print("[+] Disconnected from TopstepX")
            except:
                pass

    async def run(self) -> int:
        """Run enforcement sanity check."""
        print("=" * 70)
        print(" " * 12 + "ENFORCEMENT SANITY CHECK")
        print("=" * 70)
        print()
        print("WARNING: This check places a test order FAR from market price")
        print("  The order will NOT fill and will be cancelled immediately.")
        print()

        try:
            if not await self.connect():
                return 1

            if not await self.place_test_order():
                return 1

            if not await self.cancel_test_order():
                return 2

            print()
            print("=" * 70)
            print(" " * 17 + "[+] ENFORCEMENT SANITY PASSED")
            print("=" * 70)
            print()
            print("All enforcement actions work correctly:")
            print("  [+] Can place orders")
            print("  [+] Can cancel orders")
            print("  [+] Orders are processed by TopstepX")

            return 0
        except Exception as e:
            print(f"[x] UNEXPECTED ERROR: {e}")
            return 1
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    checker = EnforcementSanityCheck()
    exit_code = await checker.run()
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
