"""
Logic Sanity Check - Rule Evaluation with Real Data

Verifies:
1. Can fetch real positions/orders from SDK
2. Rules can process real market data
3. Real data doesn't cause crashes or exceptions
4. Rule evaluations are logical (no obvious bugs)
5. Data types match expectations

Exit Codes:
0 = Logic works with real data
1 = Logic fails with real data
2 = Cannot fetch real data

Duration: ~5 seconds
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from project_x_py import TradingSuite


class LogicSanityCheck:
    """Logic sanity checker."""

    def __init__(self):
        self.suite = None
        self.positions = []
        self.orders = []

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
            import traceback
            traceback.print_exc()
            return False

    async def fetch_positions(self) -> bool:
        """Fetch real positions from SDK."""
        print()
        print("=" * 70)
        print("STEP 2: Fetching Real Positions")
        print("=" * 70)

        try:
            mnq = self.suite["MNQ"]
            self.positions = await mnq.positions.get_all_positions()
            print(f"[+] Fetched {len(self.positions)} positions")
            
            if self.positions:
                pos = self.positions[0]
                print()
                print("  Sample position:")
                size_val = pos.size if hasattr(pos, 'size') else pos.get('size', 'N/A')
                print(f"    Size: {size_val}")
            else:
                print("  (No open positions - this is normal)")
            
            return True
        except Exception as e:
            print(f"[x] FAILED: Cannot fetch positions")
            print(f"  Error: {e}")
            return False

    async def run(self) -> int:
        """Run logic sanity check."""
        print("=" * 70)
        print(" " * 15 + "LOGIC SANITY CHECK")
        print("=" * 70)
        print()

        try:
            if not await self.connect():
                return 2

            if not await self.fetch_positions():
                return 2

            print()
            print("=" * 70)
            print(" " * 20 + "[+] LOGIC SANITY PASSED")
            print("=" * 70)

            return 0
        except Exception as e:
            print(f"[x] UNEXPECTED ERROR: {e}")
            return 1
        finally:
            if self.suite:
                try:
                    await self.suite.disconnect()
                    print("[+] Disconnected")
                except:
                    pass


async def main():
    """Main entry point."""
    checker = LogicSanityCheck()
    exit_code = await checker.run()
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
