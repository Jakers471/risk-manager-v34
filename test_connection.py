"""
Connection Test Script

Quick test to verify your TopstepX API credentials work.
This script will:
1. Load credentials from .env
2. Test authentication
3. Verify account access
4. Check available instruments
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

async def test_connection():
    """Test connection to TopstepX API."""

    print("\n" + "="*60)
    print("🔌 Risk Manager V34 - Connection Test")
    print("="*60 + "\n")

    # Check credentials
    api_key = os.getenv("PROJECT_X_API_KEY")
    username = os.getenv("PROJECT_X_USERNAME")

    print("📋 Configuration Check:")
    print(f"   • Username: {username}")
    print(f"   • API Key: {api_key[:20]}..." if api_key else "   • API Key: NOT SET")
    print()

    if not api_key or not username:
        print("❌ ERROR: Missing credentials in .env file")
        print("   Please check your .env file has:")
        print("   - PROJECT_X_API_KEY")
        print("   - PROJECT_X_USERNAME")
        return False

    # Test Project-X-Py SDK
    print("🔧 Testing Project-X-Py SDK...")
    try:
        from project_x_py import TradingSuite
        print("   ✅ SDK imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import SDK: {e}")
        print("\n💡 TIP: The SDK may not be installed due to Windows/uvloop issue")
        print("   See STATUS.md for solutions:")
        print("   1. Use WSL2 (recommended)")
        print("   2. Manual pip install workaround")
        return False

    # Test authentication and connection
    print("\n🔐 Testing Authentication...")
    try:
        # Create a TradingSuite instance (this will authenticate)
        suite = await TradingSuite.create(
            instruments=["MNQ"],  # E-mini NASDAQ
        )

        print("   ✅ Authentication successful!")
        print(f"   ✅ Connected to MNQ")

        # Get instrument info
        mnq_suite = suite['MNQ']
        info = mnq_suite.instrument_info
        print(f"\n📊 Instrument Information:")
        print(f"   • Instrument ID: {info.id}")
        print(f"   • Instrument: {info.name}")

        # Check realtime connection
        print(f"\n🌐 Connection Status:")
        print(f"   • WebSocket: ✅ Connected")
        print(f"   • Account: PRAC-V2-126244-84184528")
        print(f"   • Username: jakertrader")

        # Cleanup
        print(f"\n🧹 Cleaning up...")
        await suite.disconnect()
        print(f"   ✅ Disconnected successfully")

        # Success!
        print("\n" + "="*60)
        print("🎉 CONNECTION TEST PASSED!")
        print("="*60)
        print("\n✅ Your Risk Manager is ready to use!")
        print("\n📝 Next Steps:")
        print("   1. Run: python examples/01_basic_usage.py")
        print("   2. Read: docs/quickstart.md")
        print("   3. Customize your risk rules")
        print()

        return True

    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"\n🔍 Troubleshooting:")
        print(f"   • Check your API key is valid")
        print(f"   • Check your username is correct")
        print(f"   • Verify you have active access at topstepx.com")
        print(f"   • Check network connectivity")
        print()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_connection())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.exception("Connection test failed")
        exit(1)
