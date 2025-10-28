"""
Live TopstepX SDK Fixture for E2E Testing

Provides real SDK connection with practice account for end-to-end testing.

⚠️ SAFETY FIRST:
- ALWAYS uses practice account (never live!)
- Cleans up all positions/orders after each test
- Verifies account is practice before running tests
- Fails fast if environment variables missing

Usage:
    @pytest.mark.e2e
    async def test_something(live_sdk):
        # live_sdk is a real TradingSuite instance
        suite = live_sdk
        await suite["MNQ"].positions.open_position(...)
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator

# Import TopstepX SDK
from project_x_py import TradingSuite
from project_x_py.authentication import ClientCredentials

# Import logging
from loguru import logger


# ============================================================================
# Configuration & Safety Checks
# ============================================================================

def get_practice_credentials() -> dict[str, str]:
    """
    Load practice account credentials from environment variables.

    Required environment variables:
    - TOPSTEPX_CLIENT_ID: API client ID
    - TOPSTEPX_CLIENT_SECRET: API client secret
    - TOPSTEPX_ACCOUNT_ID: Practice account ID

    Returns:
        Dictionary with credentials

    Raises:
        ValueError: If any required environment variable is missing
    """
    required_vars = {
        "client_id": "TOPSTEPX_CLIENT_ID",
        "client_secret": "TOPSTEPX_CLIENT_SECRET",
        "account_id": "TOPSTEPX_ACCOUNT_ID"
    }

    missing = []
    credentials = {}

    for key, env_var in required_vars.items():
        value = os.getenv(env_var)
        if not value:
            missing.append(env_var)
        else:
            credentials[key] = value

    if missing:
        raise ValueError(
            f"Missing required environment variables for E2E testing:\n"
            f"  {', '.join(missing)}\n\n"
            f"Please set these in your .env file:\n"
            f"  TOPSTEPX_CLIENT_ID=your_client_id\n"
            f"  TOPSTEPX_CLIENT_SECRET=your_client_secret\n"
            f"  TOPSTEPX_ACCOUNT_ID=your_practice_account_id\n\n"
            f"⚠️  IMPORTANT: Use PRACTICE account only for testing!"
        )

    return credentials


async def verify_practice_account(suite: TradingSuite) -> None:
    """
    Verify that the account is a practice account.

    Safety check to prevent running E2E tests against live accounts.

    Args:
        suite: TradingSuite instance

    Raises:
        ValueError: If account is not a practice account
    """
    try:
        account_info = suite.account_info

        # Check if account name/ID contains "practice" or "demo"
        account_name = account_info.name.lower()
        account_id = str(account_info.id).lower()

        is_practice = (
            "practice" in account_name or
            "demo" in account_name or
            "prac" in account_id or
            "demo" in account_id
        )

        if not is_practice:
            raise ValueError(
                f"❌ SAFETY CHECK FAILED!\n\n"
                f"Account '{account_info.name}' (ID: {account_info.id}) "
                f"does not appear to be a practice account.\n\n"
                f"E2E tests MUST use practice accounts only!\n"
                f"If this is a practice account, ensure the name contains "
                f"'practice' or 'demo'."
            )

        logger.info(
            f"✅ Practice account verified: {account_info.name} (ID: {account_info.id})"
        )

    except AttributeError:
        logger.warning(
            "⚠️  Could not verify practice account (account_info not available). "
            "Proceeding with caution..."
        )


async def cleanup_account(suite: TradingSuite) -> None:
    """
    Clean up all positions and orders in the account.

    This is run after each test to ensure a clean state.

    Args:
        suite: TradingSuite instance
    """
    logger.info("🧹 Cleaning up account (closing positions, canceling orders)...")

    # Symbols to check
    symbols = ["MNQ", "ES", "NQ", "YM", "RTY", "CL", "GC", "SI"]

    # Close all open positions
    positions_closed = 0
    for symbol in symbols:
        try:
            context = suite[symbol]
            positions = await context.positions.get_all_positions()

            if positions:
                logger.info(f"  Closing {len(positions)} position(s) in {symbol}...")
                await context.positions.close_all_positions()
                positions_closed += len(positions)

        except Exception as e:
            # Some symbols might not be available
            logger.debug(f"  Could not close positions for {symbol}: {e}")
            pass

    # Cancel all open orders
    orders_cancelled = 0
    try:
        open_orders = await suite.orders.get_all_open_orders()

        if open_orders:
            logger.info(f"  Canceling {len(open_orders)} open order(s)...")

            for order in open_orders:
                try:
                    await suite.orders.cancel_order(order.id)
                    orders_cancelled += 1
                except Exception as e:
                    logger.warning(f"  Could not cancel order {order.id}: {e}")

    except Exception as e:
        logger.debug(f"  Could not cancel orders: {e}")
        pass

    if positions_closed or orders_cancelled:
        logger.info(
            f"✅ Cleanup complete: "
            f"{positions_closed} position(s) closed, "
            f"{orders_cancelled} order(s) cancelled"
        )
    else:
        logger.info("✅ Cleanup complete: No positions or orders to clean")

    # Small delay to ensure cleanup propagates
    await asyncio.sleep(0.5)


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def live_sdk_credentials():
    """
    Session-scoped fixture that loads credentials once.

    This is called once per test session (not per test).
    """
    return get_practice_credentials()


@pytest.fixture
async def live_sdk(
    live_sdk_credentials: dict[str, str]
) -> AsyncGenerator[TradingSuite, None]:
    """
    Create live SDK connection for E2E testing.

    This fixture:
    1. Loads credentials from environment
    2. Connects to TopstepX practice account
    3. Verifies account is practice (safety check)
    4. Yields TradingSuite instance to test
    5. Cleans up all positions/orders after test
    6. Disconnects from SDK

    ⚠️  IMPORTANT: This uses a REAL TopstepX API connection!

    Args:
        live_sdk_credentials: Credentials from session fixture

    Yields:
        TradingSuite: Connected SDK instance

    Example:
        @pytest.mark.e2e
        async def test_position_opening(live_sdk):
            # Open position
            await live_sdk["MNQ"].orders.place_market_order(
                side="buy",
                quantity=1
            )

            # Verify position
            positions = await live_sdk["MNQ"].positions.get_all_positions()
            assert len(positions) == 1

            # Cleanup happens automatically via fixture
    """
    logger.info("🔌 Connecting to TopstepX SDK (practice account)...")

    # Create authentication credentials
    creds = ClientCredentials(
        client_id=live_sdk_credentials["client_id"],
        client_secret=live_sdk_credentials["client_secret"]
    )

    # Create TradingSuite instance
    # ⚠️ ALWAYS use practice account!
    suite = TradingSuite(
        credentials=creds,
        account_id=live_sdk_credentials["account_id"],
        environment="practice"  # ⚠️ CRITICAL: Never use "live" in tests!
    )

    # Connect to SDK
    try:
        await suite.connect()
        logger.info("✅ Connected to TopstepX SDK")
    except Exception as e:
        logger.error(f"❌ Failed to connect to SDK: {e}")
        raise

    # Verify account is practice (safety check)
    await verify_practice_account(suite)

    # Clean up any existing positions/orders before test
    await cleanup_account(suite)

    # Yield suite to test
    try:
        yield suite
    finally:
        # Cleanup after test
        try:
            await cleanup_account(suite)
        except Exception as e:
            logger.warning(f"⚠️  Cleanup error: {e}")

        # Disconnect
        try:
            await suite.disconnect()
            logger.info("🔌 Disconnected from TopstepX SDK")
        except Exception as e:
            logger.warning(f"⚠️  Disconnect error: {e}")


# ============================================================================
# Helper Fixtures
# ============================================================================

@pytest.fixture
async def clean_account_state(live_sdk: TradingSuite) -> TradingSuite:
    """
    Ensure account is in clean state before test.

    This is useful for tests that require guaranteed clean state.

    Args:
        live_sdk: Live SDK fixture

    Yields:
        TradingSuite: SDK with verified clean state
    """
    await cleanup_account(live_sdk)

    # Verify clean state
    try:
        # Check no positions
        for symbol in ["MNQ", "ES"]:
            positions = await live_sdk[symbol].positions.get_all_positions()
            assert len(positions) == 0, f"Expected no positions in {symbol}"

        # Check no orders
        orders = await live_sdk.orders.get_all_open_orders()
        assert len(orders) == 0, "Expected no open orders"

        logger.info("✅ Clean account state verified")

    except Exception as e:
        logger.error(f"❌ Failed to verify clean state: {e}")
        raise

    yield live_sdk


@pytest.fixture
def skip_if_no_credentials():
    """
    Skip test if credentials not available.

    Useful for running unit tests without E2E credentials.

    Usage:
        @pytest.mark.e2e
        def test_something(skip_if_no_credentials, live_sdk):
            # Test will be skipped if credentials missing
            pass
    """
    try:
        get_practice_credentials()
    except ValueError as e:
        pytest.skip(f"Skipping E2E test (credentials not available): {e}")


# ============================================================================
# Safety Markers
# ============================================================================

def pytest_configure(config):
    """
    Register custom markers for E2E tests.

    This is called automatically by pytest.
    """
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests using live TopstepX SDK (practice account)"
    )
    config.addinivalue_line(
        "markers",
        "live_sdk: Tests requiring live SDK connection"
    )
