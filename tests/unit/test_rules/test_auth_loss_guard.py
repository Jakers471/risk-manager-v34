"""
Unit Tests for AuthLossGuardRule (RULE-010)

Tests the Auth Loss Guard rule in isolation with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-010 - Auth Loss Guard (Connection Monitoring)
- Alert-only rule (NO enforcement)
- Monitor SDK connection health
- Detect authentication failures
- Publish alerts/warnings
- Track connection state per account
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

from risk_manager.rules import AuthLossGuardRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine


class TestAuthLossGuardRuleUnit:
    """Unit tests for AuthLossGuardRule."""

    @pytest.fixture
    def rule(self):
        """Create auth loss guard rule with default settings."""
        return AuthLossGuardRule(
            alert_on_disconnect=True,
            alert_on_auth_failure=True,
            log_level="WARNING"
        )

    @pytest.fixture
    def mock_engine(self):
        """Create mock risk engine."""
        engine = Mock(spec=RiskEngine)
        engine.current_positions = {}
        return engine

    # ========================================================================
    # Test 1: Rule Initialization
    # ========================================================================

    def test_rule_initialization(self, rule):
        """Test rule initializes with correct parameters."""
        assert rule.alert_on_disconnect is True
        assert rule.alert_on_auth_failure is True
        assert hasattr(rule, 'connection_state')
        assert hasattr(rule, 'last_alert_time')
        assert isinstance(rule.connection_state, dict)
        assert isinstance(rule.last_alert_time, dict)

    def test_rule_initialization_custom_settings(self):
        """Test rule can be initialized with custom settings."""
        rule = AuthLossGuardRule(
            alert_on_disconnect=False,
            alert_on_auth_failure=True,
            log_level="ERROR"
        )
        assert rule.alert_on_disconnect is False
        assert rule.alert_on_auth_failure is True

    # ========================================================================
    # Test 2: SDK_DISCONNECTED Event Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_sdk_disconnected_creates_alert(self, rule, mock_engine):
        """Test SDK disconnection creates alert."""
        # Given: SDK disconnect event
        event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"account_id": 12345, "reason": "Connection lost"}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: Alert created
        assert alert is not None
        assert alert["rule"] == "AuthLossGuardRule"
        assert alert["severity"] == "WARNING"
        assert alert["alert_type"] == "connection_lost"
        assert alert["account_id"] == 12345
        assert alert["action"] == "alert_only"
        assert "message" in alert
        assert "recommendation" in alert

    @pytest.mark.asyncio
    async def test_sdk_disconnected_updates_connection_state(self, rule, mock_engine):
        """Test SDK disconnection updates connection state."""
        # Given: SDK disconnect event
        event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"account_id": 12345}
        )

        # When: Rule evaluates event
        await rule.evaluate(event, mock_engine)

        # Then: Connection state updated
        assert rule.connection_state[12345] is False

    @pytest.mark.asyncio
    async def test_sdk_disconnected_disabled_returns_none(self, mock_engine):
        """Test SDK disconnection returns None when disabled."""
        # Given: Rule with disconnect alerts disabled
        rule = AuthLossGuardRule(alert_on_disconnect=False)

        event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"account_id": 12345}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: No alert
        assert alert is None

    @pytest.mark.asyncio
    async def test_sdk_disconnected_no_account_id_returns_none(self, rule, mock_engine):
        """Test SDK disconnection without account_id returns None."""
        # Given: Event without account_id
        event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"reason": "Connection lost"}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: No alert
        assert alert is None

    # ========================================================================
    # Test 3: SDK_CONNECTED Event Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_sdk_connected_no_alert(self, rule, mock_engine):
        """Test SDK connection does not create alert."""
        # Given: SDK connect event
        event = RiskEvent(
            event_type=EventType.SDK_CONNECTED,
            data={"account_id": 12345}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: No alert (connection is good news)
        assert alert is None

    @pytest.mark.asyncio
    async def test_sdk_connected_updates_connection_state(self, rule, mock_engine):
        """Test SDK connection updates connection state."""
        # Given: Previously disconnected
        rule.connection_state[12345] = False

        event = RiskEvent(
            event_type=EventType.SDK_CONNECTED,
            data={"account_id": 12345}
        )

        # When: Rule evaluates event
        await rule.evaluate(event, mock_engine)

        # Then: Connection state updated
        assert rule.connection_state[12345] is True

    # ========================================================================
    # Test 4: AUTH_FAILED Event Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_auth_failed_creates_alert(self, rule, mock_engine):
        """Test authentication failure creates alert."""
        # Given: Auth failed event
        event = RiskEvent(
            event_type=EventType.AUTH_FAILED,
            data={"account_id": 12345, "reason": "Invalid credentials"}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: Alert created
        assert alert is not None
        assert alert["rule"] == "AuthLossGuardRule"
        assert alert["severity"] == "ERROR"
        assert alert["alert_type"] == "auth_failed"
        assert alert["account_id"] == 12345
        assert alert["action"] == "alert_only"
        assert alert["reason"] == "Invalid credentials"
        assert "message" in alert
        assert "recommendation" in alert

    @pytest.mark.asyncio
    async def test_auth_failed_disabled_returns_none(self, mock_engine):
        """Test auth failure returns None when disabled."""
        # Given: Rule with auth failure alerts disabled
        rule = AuthLossGuardRule(alert_on_auth_failure=False)

        event = RiskEvent(
            event_type=EventType.AUTH_FAILED,
            data={"account_id": 12345, "reason": "Invalid credentials"}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: No alert
        assert alert is None

    @pytest.mark.asyncio
    async def test_auth_failed_no_account_id_returns_none(self, rule, mock_engine):
        """Test auth failure without account_id returns None."""
        # Given: Event without account_id
        event = RiskEvent(
            event_type=EventType.AUTH_FAILED,
            data={"reason": "Invalid credentials"}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: No alert
        assert alert is None

    # ========================================================================
    # Test 5: AUTH_SUCCESS Event Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_auth_success_no_alert(self, rule, mock_engine):
        """Test authentication success does not create alert."""
        # Given: Auth success event
        event = RiskEvent(
            event_type=EventType.AUTH_SUCCESS,
            data={"account_id": 12345}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: No alert (auth success is good news)
        assert alert is None

    # ========================================================================
    # Test 6: Ignore Non-SDK-Health Events
    # ========================================================================

    @pytest.mark.asyncio
    async def test_position_updated_ignored(self, rule, mock_engine):
        """Test POSITION_UPDATED event is ignored."""
        # Given: Position updated event
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={"symbol": "ES", "size": 2}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: No alert
        assert alert is None

    @pytest.mark.asyncio
    async def test_order_filled_ignored(self, rule, mock_engine):
        """Test ORDER_FILLED event is ignored."""
        # Given: Order filled event
        event = RiskEvent(
            event_type=EventType.ORDER_FILLED,
            data={"orderId": "123", "quantity": 1}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: No alert
        assert alert is None

    @pytest.mark.asyncio
    async def test_trade_executed_ignored(self, rule, mock_engine):
        """Test TRADE_EXECUTED event is ignored."""
        # Given: Trade executed event
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"symbol": "MNQ", "quantity": 1}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: No alert
        assert alert is None

    # ========================================================================
    # Test 7: Connection State Tracking
    # ========================================================================

    def test_get_connection_status_unknown_account(self, rule):
        """Test getting connection status for unknown account."""
        # When: Check status for unknown account
        status = rule.get_connection_status(99999)

        # Then: Returns True (assume connected if unknown)
        assert status is True

    def test_get_connection_status_known_account(self, rule):
        """Test getting connection status for known account."""
        # Given: Known connection state
        rule.connection_state[12345] = False

        # When: Check status
        status = rule.get_connection_status(12345)

        # Then: Returns stored state
        assert status is False

    def test_get_last_alert_time_unknown_account(self, rule):
        """Test getting last alert time for unknown account."""
        # When: Check last alert time for unknown account
        last_alert = rule.get_last_alert_time(99999)

        # Then: Returns None
        assert last_alert is None

    @pytest.mark.asyncio
    async def test_last_alert_time_tracked(self, rule, mock_engine):
        """Test last alert time is tracked."""
        # Given: SDK disconnect event
        event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"account_id": 12345}
        )

        # When: Rule evaluates event
        await rule.evaluate(event, mock_engine)

        # Then: Last alert time recorded
        last_alert = rule.get_last_alert_time(12345)
        assert last_alert is not None
        assert isinstance(last_alert, datetime)

    # ========================================================================
    # Test 8: Multiple Accounts
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multiple_accounts_independent(self, rule, mock_engine):
        """Test multiple accounts tracked independently."""
        # Given: Disconnection events for two accounts
        event1 = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"account_id": 11111}
        )
        event2 = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"account_id": 22222}
        )

        # When: Both accounts disconnect
        await rule.evaluate(event1, mock_engine)
        await rule.evaluate(event2, mock_engine)

        # Then: Both tracked independently
        assert rule.connection_state[11111] is False
        assert rule.connection_state[22222] is False
        assert rule.get_last_alert_time(11111) is not None
        assert rule.get_last_alert_time(22222) is not None

    @pytest.mark.asyncio
    async def test_one_account_reconnects(self, rule, mock_engine):
        """Test one account reconnecting doesn't affect others."""
        # Given: Two accounts disconnected
        rule.connection_state[11111] = False
        rule.connection_state[22222] = False

        # When: One account reconnects
        event = RiskEvent(
            event_type=EventType.SDK_CONNECTED,
            data={"account_id": 11111}
        )
        await rule.evaluate(event, mock_engine)

        # Then: Only that account updated
        assert rule.connection_state[11111] is True
        assert rule.connection_state[22222] is False

    # ========================================================================
    # Test 9: Enforce Method (No-Op)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_enforce_does_nothing(self, rule, mock_engine):
        """Test enforce method does nothing (alert-only rule)."""
        # Given: Violation from evaluate
        violation = {
            "rule": "AuthLossGuardRule",
            "severity": "WARNING",
            "alert_type": "connection_lost",
            "account_id": 12345,
            "action": "alert_only"
        }

        # When: Enforce called
        result = await rule.enforce(12345, violation, mock_engine)

        # Then: Returns None, does nothing
        assert result is None

    # ========================================================================
    # Test 10: Alert Contains Required Fields
    # ========================================================================

    @pytest.mark.asyncio
    async def test_disconnect_alert_has_required_fields(self, rule, mock_engine):
        """Test disconnection alert has all required fields."""
        # Given: SDK disconnect event
        event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"account_id": 12345}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: Alert has required fields
        assert "rule" in alert
        assert "severity" in alert
        assert "alert_type" in alert
        assert "message" in alert
        assert "account_id" in alert
        assert "timestamp" in alert
        assert "action" in alert
        assert "recommendation" in alert

    @pytest.mark.asyncio
    async def test_auth_failed_alert_has_required_fields(self, rule, mock_engine):
        """Test auth failure alert has all required fields."""
        # Given: Auth failed event
        event = RiskEvent(
            event_type=EventType.AUTH_FAILED,
            data={"account_id": 12345, "reason": "Invalid credentials"}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: Alert has required fields
        assert "rule" in alert
        assert "severity" in alert
        assert "alert_type" in alert
        assert "message" in alert
        assert "account_id" in alert
        assert "timestamp" in alert
        assert "action" in alert
        assert "reason" in alert
        assert "recommendation" in alert

    # ========================================================================
    # Test 11: Alert Timestamps Are Valid
    # ========================================================================

    @pytest.mark.asyncio
    async def test_alert_timestamp_is_iso_format(self, rule, mock_engine):
        """Test alert timestamp is valid ISO format."""
        # Given: SDK disconnect event
        event = RiskEvent(
            event_type=EventType.SDK_DISCONNECTED,
            data={"account_id": 12345}
        )

        # When: Rule evaluates event
        alert = await rule.evaluate(event, mock_engine)

        # Then: Timestamp is valid ISO format
        timestamp_str = alert["timestamp"]
        # Should be parseable as ISO datetime
        parsed = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed, datetime)
