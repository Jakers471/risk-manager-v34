"""
Unit Tests for SessionBlockOutsideRule (RULE-009)

Tests the session block outside hours rule with mocked dependencies.
Follows TDD approach - these tests should FAIL initially, then we make them pass.

Rule: RULE-009 - Session Block Outside Hours
- Block trading outside configured session hours (e.g., 9:30 AM - 4:00 PM ET)
- Support timezone-aware time checking (ET to UTC conversion)
- Handle weekends and holidays
- Hard lockout when outside session hours
- Auto-unlock when session starts
- Support both global sessions and per-instrument sessions

Category: Hard Lockout (Category 3)
Priority: High
"""

import pytest
from datetime import datetime, time, timedelta, timezone
from unittest.mock import AsyncMock, Mock, MagicMock
from zoneinfo import ZoneInfo

from risk_manager.rules.session_block_outside import SessionBlockOutsideRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine


class TestSessionBlockOutsideRule:
    """Unit tests for SessionBlockOutsideRule."""

    @pytest.fixture
    def mock_lockout_manager(self):
        """Create mock lockout manager."""
        manager = Mock()
        manager.set_lockout = Mock()
        manager.is_locked_out = Mock(return_value=False)
        manager.get_lockout_info = Mock(return_value=None)
        manager.clear_lockout = Mock()
        return manager

    @pytest.fixture
    def basic_config(self):
        """Basic configuration for 9:30 AM - 4:00 PM ET trading hours."""
        return {
            "enabled": True,
            "global_session": {
                "enabled": True,
                "start": "09:30",
                "end": "16:00",
                "timezone": "America/New_York"
            },
            "block_weekends": True,
            "lockout_outside_session": True
        }

    @pytest.fixture
    def rule(self, basic_config, mock_lockout_manager):
        """Create session block outside rule with basic config."""
        return SessionBlockOutsideRule(
            config=basic_config,
            lockout_manager=mock_lockout_manager
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

    def test_rule_initialization(self, rule, basic_config):
        """Test rule initializes with correct parameters."""
        assert rule.enabled is True
        assert rule.name == "SessionBlockOutsideRule"
        assert rule.global_session_enabled is True
        assert rule.session_start == time(9, 30)
        assert rule.session_end == time(16, 0)
        assert rule.block_weekends is True

    def test_rule_initialization_with_custom_hours(self, mock_lockout_manager):
        """Test rule can be initialized with different session hours."""
        config = {
            "enabled": True,
            "global_session": {
                "enabled": True,
                "start": "08:00",
                "end": "17:30",
                "timezone": "America/Chicago"
            },
            "block_weekends": True
        }
        rule = SessionBlockOutsideRule(
            config=config,
            lockout_manager=mock_lockout_manager
        )
        assert rule.session_start == time(8, 0)
        assert rule.session_end == time(17, 30)
        assert rule.timezone_name == "America/Chicago"

    def test_rule_initialization_validates_time_format(self, mock_lockout_manager):
        """Test that invalid time format raises validation error."""
        config = {
            "enabled": True,
            "global_session": {
                "enabled": True,
                "start": "25:00",  # Invalid hour
                "end": "16:00",
                "timezone": "America/New_York"
            }
        }
        with pytest.raises(ValueError):
            SessionBlockOutsideRule(
                config=config,
                lockout_manager=mock_lockout_manager
            )

    def test_rule_disabled_when_config_disabled(self, mock_lockout_manager):
        """Test that rule can be disabled via config."""
        config = {
            "enabled": False,
            "global_session": {
                "enabled": True,
                "start": "09:30",
                "end": "16:00",
                "timezone": "America/New_York"
            }
        }
        rule = SessionBlockOutsideRule(
            config=config,
            lockout_manager=mock_lockout_manager
        )
        assert rule.enabled is False

    # ========================================================================
    # Test 2: Time Conversion and Timezone Handling
    # ========================================================================

    def test_converts_et_to_utc_correctly(self, rule):
        """Test that ET times are correctly converted to UTC."""
        # Create a datetime in ET
        et_tz = ZoneInfo("America/New_York")
        et_time = datetime(2025, 10, 27, 10, 30, tzinfo=et_tz)  # 10:30 AM ET

        # Convert to UTC (should be around 14:30 or 15:30 depending on DST)
        utc_time = et_time.astimezone(ZoneInfo("UTC"))

        # Verify conversion happened
        assert utc_time.tzinfo == ZoneInfo("UTC")
        # The hour in UTC should be different from ET (ET is UTC-4 or UTC-5)
        assert utc_time.hour != et_time.hour

    def test_handles_dst_transitions(self, rule):
        """Test rule handles daylight saving time transitions."""
        et_tz = ZoneInfo("America/New_York")

        # Summer time (EDT - UTC-4)
        summer = datetime(2025, 7, 15, 10, 0, tzinfo=et_tz)
        summer_utc = summer.astimezone(ZoneInfo("UTC"))

        # Winter time (EST - UTC-5)
        winter = datetime(2025, 1, 15, 10, 0, tzinfo=et_tz)
        winter_utc = winter.astimezone(ZoneInfo("UTC"))

        # UTC offset should differ by 1 hour
        offset_diff = summer_utc.hour - winter_utc.hour
        assert abs(offset_diff) == 1 or abs(offset_diff) == 23  # Handle day boundary

    # ========================================================================
    # Test 3: Trading Inside Session Hours (Should PASS)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_trading_inside_hours_passes(self, rule, mock_engine, monkeypatch):
        """Test that trading inside session hours does not trigger violation."""
        # Mock current time to 11:00 AM ET on a weekday (Wednesday)
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 11, 0, tzinfo=et_tz)  # Wednesday 11:00 AM ET

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        # When: Rule evaluates event
        violation = await rule.evaluate(event, mock_engine)

        # Then: No violation (inside trading hours)
        assert violation is None

    @pytest.mark.asyncio
    async def test_trading_at_session_start_passes(self, rule, mock_engine, monkeypatch):
        """Test that trading exactly at session start time passes."""
        # Mock current time to 9:30 AM ET exactly
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 9, 30, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ"
            }
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    @pytest.mark.asyncio
    async def test_trading_just_before_session_end_passes(self, rule, mock_engine, monkeypatch):
        """Test that trading just before session end passes."""
        # Mock current time to 3:59 PM ET
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 15, 59, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "NQ"
            }
        )

        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

    # ========================================================================
    # Test 4: Trading Outside Session Hours (Should VIOLATE)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_trading_before_session_start_violates(self, rule, mock_engine, monkeypatch):
        """Test that trading before session start triggers violation."""
        # Mock current time to 7:00 AM ET (before 9:30 AM)
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 7, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert violation["rule"] == "SessionBlockOutsideRule"
        assert "outside session hours" in violation["message"].lower()
        assert violation["lockout_required"] is True

    @pytest.mark.asyncio
    async def test_trading_after_session_end_violates(self, rule, mock_engine, monkeypatch):
        """Test that trading after session end triggers violation."""
        # Mock current time to 6:00 PM ET (after 4:00 PM)
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 18, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert violation["lockout_required"] is True
        assert "after session end" in violation["message"].lower() or "outside session" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_trading_at_session_end_violates(self, rule, mock_engine, monkeypatch):
        """Test that trading exactly at session end time triggers violation."""
        # Mock current time to 4:00 PM ET exactly (session ends, not inside)
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 16, 0, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        # Session is [start, end), so exactly at end is outside
        assert violation is not None

    # ========================================================================
    # Test 5: Weekend Blocking
    # ========================================================================

    @pytest.mark.asyncio
    async def test_trading_on_saturday_violates(self, rule, mock_engine, monkeypatch):
        """Test that trading on Saturday triggers violation."""
        # Mock current time to Saturday 11:00 AM ET
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 11, 1, 11, 0, tzinfo=et_tz)  # Saturday

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert "weekend" in violation["message"].lower() or "saturday" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_trading_on_sunday_violates(self, rule, mock_engine, monkeypatch):
        """Test that trading on Sunday triggers violation."""
        # Mock current time to Sunday 11:00 AM ET
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 11, 2, 11, 0, tzinfo=et_tz)  # Sunday

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert "weekend" in violation["message"].lower() or "sunday" in violation["message"].lower()

    @pytest.mark.asyncio
    async def test_weekend_blocking_can_be_disabled(self, mock_lockout_manager, mock_engine, monkeypatch):
        """Test that weekend blocking can be disabled via config."""
        config = {
            "enabled": True,
            "global_session": {
                "enabled": True,
                "start": "09:30",
                "end": "16:00",
                "timezone": "America/New_York"
            },
            "block_weekends": False  # Disabled
        }
        rule = SessionBlockOutsideRule(
            config=config,
            lockout_manager=mock_lockout_manager
        )

        # Mock Saturday during session hours
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 11, 1, 11, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        # Should not violate (weekend blocking disabled)
        assert violation is None

    # ========================================================================
    # Test 6: Lockout Management
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_triggers_lockout_until_session_start(
        self, rule, mock_engine, mock_lockout_manager, monkeypatch
    ):
        """Test that violation triggers lockout until next session start."""
        # Mock current time to 7:00 PM ET (after hours)
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 19, 0, tzinfo=et_tz)  # Wednesday 7 PM

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert violation["lockout_required"] is True
        assert "next_session_start" in violation

        # Next session start should be tomorrow (Thursday) at 9:30 AM ET
        next_start = violation["next_session_start"]
        assert next_start > mock_now

    @pytest.mark.asyncio
    async def test_lockout_skips_weekends(self, rule, mock_engine, monkeypatch):
        """Test that lockout scheduled after Friday goes to Monday."""
        # Mock current time to Friday 7:00 PM ET (after hours)
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 31, 19, 0, tzinfo=et_tz)  # Friday 7 PM

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        next_start = violation["next_session_start"]

        # Next session should be Monday (skip weekend)
        assert next_start.weekday() == 0  # Monday

    @pytest.mark.asyncio
    async def test_enforcement_sets_lockout(self, rule, mock_engine, mock_lockout_manager):
        """Test that enforcement action sets lockout correctly."""
        violation = {
            "rule": "SessionBlockOutsideRule",
            "message": "Trading outside session hours",
            "account_id": "ACC-001",
            "lockout_required": True,
            "next_session_start": datetime.now(timezone.utc) + timedelta(hours=14)
        }

        # When: Enforce violation
        await rule.enforce("ACC-001", violation, mock_engine)

        # Then: Lockout manager was called
        mock_lockout_manager.set_lockout.assert_called_once()
        call_args = mock_lockout_manager.set_lockout.call_args
        assert call_args[1]["account_id"] == "ACC-001"
        assert "until" in call_args[1]

    # ========================================================================
    # Test 7: Rule Only Evaluates Position Events
    # ========================================================================

    @pytest.mark.asyncio
    async def test_only_evaluates_position_events(self, rule, mock_engine, monkeypatch):
        """Test rule only evaluates position-related events."""
        # Mock time outside hours
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 7, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        # Non-position event (order placed)
        event = RiskEvent(
            event_type=EventType.ORDER_PLACED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        # Should not evaluate (ignores non-position events)
        assert violation is None

    @pytest.mark.asyncio
    async def test_evaluates_position_opened_event(self, rule, mock_engine, monkeypatch):
        """Test rule evaluates POSITION_OPENED events."""
        # Mock time outside hours
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 7, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        # Should evaluate and violate (outside hours)
        assert violation is not None

    # ========================================================================
    # Test 8: Edge Cases
    # ========================================================================

    @pytest.mark.asyncio
    async def test_handles_missing_account_id_gracefully(self, rule, mock_engine, monkeypatch):
        """Test rule handles missing account_id gracefully."""
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 7, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES"
                # Missing account_id
            }
        )

        # Should not crash
        violation = await rule.evaluate(event, mock_engine)

        # Should return None (can't validate without account_id)
        assert violation is None

    @pytest.mark.asyncio
    async def test_rule_disabled_skips_evaluation(self, mock_lockout_manager, mock_engine, monkeypatch):
        """Test that disabled rule skips evaluation."""
        config = {
            "enabled": False,  # Disabled
            "global_session": {
                "enabled": True,
                "start": "09:30",
                "end": "16:00",
                "timezone": "America/New_York"
            },
            "block_weekends": True
        }
        rule = SessionBlockOutsideRule(
            config=config,
            lockout_manager=mock_lockout_manager
        )

        # Mock time outside hours
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 7, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        # Should not violate (rule disabled)
        assert violation is None

    @pytest.mark.asyncio
    async def test_already_locked_account_skips_evaluation(self, rule, mock_engine, mock_lockout_manager, monkeypatch):
        """Test that already locked account skips evaluation."""
        # Mock account already locked
        mock_lockout_manager.is_locked_out.return_value = True

        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 7, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "ES"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        # Should not violate (already locked)
        assert violation is None

    # ========================================================================
    # Test 9: Violation Message Quality
    # ========================================================================

    @pytest.mark.asyncio
    async def test_violation_message_clarity(self, rule, mock_engine, monkeypatch):
        """Test violation message is clear and actionable."""
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2025, 10, 29, 7, 0, tzinfo=et_tz)

        def mock_datetime_now(tz=None):
            if tz:
                return mock_now.astimezone(tz)
            return mock_now

        monkeypatch.setattr('risk_manager.rules.session_block_outside.datetime',
                           type('MockDateTime', (), {'now': staticmethod(mock_datetime_now)})())

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "account_id": "ACC-001",
                "symbol": "MNQ"
            }
        )

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert "message" in violation
        assert isinstance(violation["message"], str)
        assert len(violation["message"]) > 10

        # Message should contain key info
        message_lower = violation["message"].lower()
        assert any(word in message_lower for word in ["session", "hours", "outside", "trading"])

    # ========================================================================
    # Test 10: Timezone Edge Cases
    # ========================================================================

    def test_different_timezones_supported(self, mock_lockout_manager):
        """Test rule supports different timezone configurations."""
        timezones = [
            "America/New_York",   # ET
            "America/Chicago",     # CT
            "America/Los_Angeles", # PT
            "Europe/London",       # GMT/BST
        ]

        for tz in timezones:
            config = {
                "enabled": True,
                "global_session": {
                    "enabled": True,
                    "start": "09:00",
                    "end": "17:00",
                    "timezone": tz
                },
                "block_weekends": True
            }
            rule = SessionBlockOutsideRule(
                config=config,
                lockout_manager=mock_lockout_manager
            )
            assert rule.timezone_name == tz
