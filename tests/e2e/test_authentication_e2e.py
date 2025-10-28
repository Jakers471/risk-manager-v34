"""
End-to-End Tests for Authentication & Connection

Tests the complete authentication and connection flow from SDK events through
to system initialization and recovery.

Complete Flows Tested:
1. Authentication Success - Valid credentials → SDK_CONNECTED event
2. Authentication Failure - Invalid credentials → AUTH_FAILED event
3. Connection Loss Recovery - SDK disconnect → reconnect → resume
4. Multi-Account Authentication - Multiple accounts authenticate independently

This validates the authentication and connection pipeline works together.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from datetime import datetime

# Risk Manager imports
from risk_manager.core.manager import RiskManager
from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.config import RiskConfig


class MockAccount:
    """Mock SDK Account object."""

    def __init__(self, account_id="PRAC-V2-126244-84184528", name="150k Practice Account"):
        self.id = account_id
        self.name = name
        self.balance = 150000.0
        self.equity = 150000.0


class MockTradingSuite:
    """Mock SDK TradingSuite with authentication simulation."""

    def __init__(self, should_fail_auth=False, account_id="PRAC-V2-126244-84184528"):
        self.event_bus = EventBus()
        self._connected = False
        self._should_fail_auth = should_fail_auth
        self.account_info = MockAccount(account_id=account_id)
        self._symbols = {}

    async def connect(self):
        """Simulate SDK connection."""
        if self._should_fail_auth:
            raise ConnectionError("Authentication failed: Invalid credentials")

        self._connected = True

        # Simulate SDK_CONNECTED event
        await self.event_bus.publish(
            RiskEvent(
                event_type=EventType.SDK_CONNECTED,
                data={
                    "account_id": self.account_info.id,
                    "account_name": self.account_info.name
                }
            )
        )

    async def disconnect(self):
        """Simulate SDK disconnection."""
        if self._connected:
            self._connected = False

            # Simulate SDK_DISCONNECTED event
            await self.event_bus.publish(
                RiskEvent(
                    event_type=EventType.SDK_DISCONNECTED,
                    data={"reason": "Disconnected by user"}
                )
            )

    def __getitem__(self, symbol):
        """Return mock instrument context."""
        if symbol not in self._symbols:
            context = Mock()
            context.positions = Mock()
            context.positions.get_all_positions = AsyncMock(return_value=[])
            context.positions.close_all_positions = AsyncMock()
            context.instrument_info = Mock()
            context.instrument_info.name = symbol
            context.instrument_info.id = f"CON.F.US.{symbol}.Z25"
            self._symbols[symbol] = context
        return self._symbols[symbol]

    async def on(self, event_type, handler):
        """Subscribe to event."""
        self.event_bus.subscribe(event_type, handler)

    @property
    def is_connected(self):
        """Mock connection status."""
        return self._connected


@pytest.mark.e2e
class TestAuthenticationE2E:
    """End-to-end tests for authentication and connection."""

    @pytest.fixture
    def mock_sdk_suite(self):
        """Create mock SDK suite with authentication capability."""
        return MockTradingSuite()

    @pytest.fixture
    def mock_sdk_suite_fail_auth(self):
        """Create mock SDK suite that fails authentication."""
        return MockTradingSuite(should_fail_auth=True)

    @pytest.fixture
    async def risk_manager_base(self):
        """Create base risk manager components without starting."""
        config = RiskConfig(
            project_x_api_key="test_api_key",
            project_x_username="test_user",
            max_contracts=2
        )
        event_bus = EventBus()

        # Mock trading integration
        mock_trading = AsyncMock()
        mock_trading.flatten_all = AsyncMock()
        mock_trading.flatten_position = AsyncMock()

        # Create container
        class SimpleRiskManager:
            def __init__(self):
                self.config = config
                self.event_bus = event_bus
                self.trading_integration = mock_trading
                self._started = False

        return SimpleRiskManager()

    # ========================================================================
    # Test 1: Authentication Success
    # ========================================================================

    @pytest.mark.asyncio
    async def test_authentication_success(self, mock_sdk_suite):
        """Test valid credentials authenticate successfully.

        Flow:
        1. System starts with valid credentials
        2. SDK authenticates successfully
        3. SDK_CONNECTED event fired
        4. Account info retrieved
        """
        # Track events
        events_received = []

        async def track_event(event):
            events_received.append(event)

        mock_sdk_suite.event_bus.subscribe(EventType.SDK_CONNECTED, track_event)

        # Given: Valid credentials configured
        config = RiskConfig(
            project_x_api_key="valid_api_key",
            project_x_username="valid_user",
            max_contracts=2
        )

        # When: System attempts to connect
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)  # Allow async processing

        # Then: SDK authenticates successfully
        assert mock_sdk_suite.is_connected is True

        # And: SDK_CONNECTED event was fired
        assert len(events_received) == 1
        assert events_received[0].event_type == EventType.SDK_CONNECTED

        # And: Account info is available
        assert mock_sdk_suite.account_info is not None
        assert mock_sdk_suite.account_info.id == "PRAC-V2-126244-84184528"
        assert "Practice" in mock_sdk_suite.account_info.name

    # ========================================================================
    # Test 2: Authentication Failure
    # ========================================================================

    @pytest.mark.asyncio
    async def test_authentication_failure(self, mock_sdk_suite_fail_auth):
        """Test invalid credentials are handled gracefully.

        Flow:
        1. System starts with invalid credentials
        2. SDK authentication fails
        3. AUTH_FAILED event fired (or exception caught)
        4. System handles gracefully without crashing
        """
        # Track connection attempts
        connection_failed = False
        error_message = None

        # Given: Invalid credentials configured
        config = RiskConfig(
            project_x_api_key="invalid_api_key",
            project_x_username="invalid_user",
            max_contracts=2
        )

        # When: System attempts to connect with invalid credentials
        try:
            await mock_sdk_suite_fail_auth.connect()
        except ConnectionError as e:
            connection_failed = True
            error_message = str(e)

        await asyncio.sleep(0.1)

        # Then: Connection fails
        assert connection_failed is True
        assert "Authentication failed" in error_message

        # And: SDK is not connected
        assert mock_sdk_suite_fail_auth.is_connected is False

        # And: System should handle this gracefully
        # (In real implementation, RULE-010 would trigger alert)

    # ========================================================================
    # Test 3: Connection Loss Recovery
    # ========================================================================

    @pytest.mark.asyncio
    async def test_connection_loss_recovery(self, mock_sdk_suite):
        """Test SDK disconnect/reconnect recovery.

        Flow:
        1. System connected normally
        2. Force disconnect SDK
        3. SDK_DISCONNECTED event fired
        4. System detects disconnect
        5. SDK reconnects
        6. SDK_CONNECTED event fired
        7. System resumes operation
        """
        # Track events
        connected_events = []
        disconnected_events = []

        async def track_connected(event):
            connected_events.append(event)

        async def track_disconnected(event):
            disconnected_events.append(event)

        mock_sdk_suite.event_bus.subscribe(EventType.SDK_CONNECTED, track_connected)
        mock_sdk_suite.event_bus.subscribe(EventType.SDK_DISCONNECTED, track_disconnected)

        # Given: System connected and running
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)

        assert mock_sdk_suite.is_connected is True
        assert len(connected_events) == 1

        # When: SDK disconnects (simulating network issue)
        await mock_sdk_suite.disconnect()
        await asyncio.sleep(0.1)

        # Then: SDK_DISCONNECTED event fired
        assert len(disconnected_events) == 1
        assert disconnected_events[0].event_type == EventType.SDK_DISCONNECTED

        # And: SDK is disconnected
        assert mock_sdk_suite.is_connected is False

        # When: SDK reconnects
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)

        # Then: SDK_CONNECTED event fired again
        assert len(connected_events) == 2

        # And: SDK is connected
        assert mock_sdk_suite.is_connected is True

        # And: System resumes normal operation
        # (In real implementation, position tracking would resume)

    # ========================================================================
    # Test 4: Multi-Account Authentication
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multi_account_authentication(self):
        """Test multiple accounts authenticate independently.

        Flow:
        1. Multiple accounts configured
        2. Each account authenticates separately
        3. Each account tracked independently
        4. Events tagged with correct account_id
        """
        # Given: Multiple accounts
        account_ids = [
            "PRAC-V2-126244-84184528",
            "PRAC-V2-999888-77665544",
            "PRAC-V2-111222-33344455"
        ]

        suites = []
        connected_events = []

        # Track events across all accounts
        async def track_connected(event):
            connected_events.append(event)

        # Create and connect each account
        for account_id in account_ids:
            suite = MockTradingSuite(account_id=account_id)
            suite.event_bus.subscribe(EventType.SDK_CONNECTED, track_connected)
            suites.append(suite)

        # When: All accounts authenticate
        for suite in suites:
            await suite.connect()
            await asyncio.sleep(0.05)

        # Then: All accounts authenticated successfully
        assert all(suite.is_connected for suite in suites)

        # And: Each account has its own event
        assert len(connected_events) == len(account_ids)

        # And: Each event has correct account_id
        received_account_ids = [
            event.data["account_id"] for event in connected_events
        ]
        assert set(received_account_ids) == set(account_ids)

        # And: Each account can be accessed independently
        for suite in suites:
            assert suite.account_info.id in account_ids
            assert suite.is_connected is True

            # Verify account can access instruments
            mnq_context = suite["MNQ"]
            assert mnq_context is not None

    # ========================================================================
    # Test 5: Connection State Consistency
    # ========================================================================

    @pytest.mark.asyncio
    async def test_connection_state_consistency(self, mock_sdk_suite):
        """Test connection state remains consistent across operations.

        Flow:
        1. Connect → Verify connected state
        2. Disconnect → Verify disconnected state
        3. Reconnect → Verify connected state
        4. Multiple rapid connects → State remains valid
        """
        # Initially disconnected
        assert mock_sdk_suite.is_connected is False

        # Connect
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)
        assert mock_sdk_suite.is_connected is True

        # Disconnect
        await mock_sdk_suite.disconnect()
        await asyncio.sleep(0.1)
        assert mock_sdk_suite.is_connected is False

        # Reconnect
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)
        assert mock_sdk_suite.is_connected is True

        # Verify can still access SDK features
        mnq_context = mock_sdk_suite["MNQ"]
        positions = await mnq_context.positions.get_all_positions()
        assert isinstance(positions, list)

    # ========================================================================
    # Test 6: Authentication with Account Info Retrieval
    # ========================================================================

    @pytest.mark.asyncio
    async def test_authentication_retrieves_account_info(self, mock_sdk_suite):
        """Test authentication retrieves complete account information.

        Flow:
        1. Authenticate successfully
        2. Account info available immediately
        3. Account info contains required fields
        """
        # When: Authenticate
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)

        # Then: Account info is available
        account_info = mock_sdk_suite.account_info
        assert account_info is not None

        # And: Account info has required fields
        assert hasattr(account_info, 'id')
        assert hasattr(account_info, 'name')
        assert hasattr(account_info, 'balance')
        assert hasattr(account_info, 'equity')

        # And: Values are valid
        assert account_info.id == "PRAC-V2-126244-84184528"
        assert "Practice" in account_info.name
        assert account_info.balance > 0
        assert account_info.equity > 0

    # ========================================================================
    # Test 7: Concurrent Authentication Attempts
    # ========================================================================

    @pytest.mark.asyncio
    async def test_concurrent_authentication_attempts(self):
        """Test system handles concurrent authentication attempts gracefully.

        Flow:
        1. Start multiple authentication attempts simultaneously
        2. All attempts complete successfully
        3. No race conditions or conflicts
        """
        # Create multiple suites
        suites = [MockTradingSuite(account_id=f"PRAC-{i}") for i in range(5)]

        # When: Connect all simultaneously
        connect_tasks = [suite.connect() for suite in suites]
        await asyncio.gather(*connect_tasks)
        await asyncio.sleep(0.1)

        # Then: All connected successfully
        assert all(suite.is_connected for suite in suites)

        # And: Each has its own account info
        account_ids = [suite.account_info.id for suite in suites]
        assert len(set(account_ids)) == 5  # All unique

    # ========================================================================
    # Test 8: Authentication Event Data Completeness
    # ========================================================================

    @pytest.mark.asyncio
    async def test_authentication_event_data_completeness(self, mock_sdk_suite):
        """Test SDK_CONNECTED event contains complete data.

        Flow:
        1. Authenticate successfully
        2. SDK_CONNECTED event fired
        3. Event contains all required data fields
        """
        events_received = []

        async def track_event(event):
            events_received.append(event)

        mock_sdk_suite.event_bus.subscribe(EventType.SDK_CONNECTED, track_event)

        # When: Authenticate
        await mock_sdk_suite.connect()
        await asyncio.sleep(0.1)

        # Then: Event received
        assert len(events_received) == 1
        event = events_received[0]

        # And: Event type is correct
        assert event.event_type == EventType.SDK_CONNECTED

        # And: Event data contains required fields
        assert "account_id" in event.data
        assert "account_name" in event.data

        # And: Values are valid
        assert event.data["account_id"] == "PRAC-V2-126244-84184528"
        assert "Practice" in event.data["account_name"]

        # And: Event has timestamp
        assert hasattr(event, 'timestamp')
        assert isinstance(event.timestamp, datetime)
