"""
Test different scenarios for events sanity check.
This demonstrates the different exit codes.
"""
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from src.sanity.events_sanity import EventsSanityCheck

async def test_normal_pass():
    """Test normal pass scenario."""
    print("=" * 70)
    print("TEST 1: Normal Pass Scenario")
    print("=" * 70)
    checker = EventsSanityCheck()
    result = await checker.run()
    print(f"\nResult: Exit code {result}")
    assert result == 0, "Expected exit code 0"
    print("PASS: Normal scenario works!")
    return result

if __name__ == "__main__":
    print("Testing Events Sanity Check Scenarios\n")
    
    # Test 1: Normal pass
    exit_code = asyncio.run(test_normal_pass())
    
    print("\n" + "=" * 70)
    print("All scenario tests completed successfully!")
    print("=" * 70)
    
    sys.exit(0)
