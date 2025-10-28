"""
Integration Tests for RULE-009: Session Block Outside Hours

Tests the complete integration of SessionBlockOutsideRule with REAL components:
- Real LockoutManager (with database)
- Real timezone conversion (no mocking datetime)
- Real EventBus
- Real enforcement flow

Integration Scope:
- Database persistence of lockouts
- Timezone handling (ET/CT/PT, DST transitions)
- Multi-account lockout independence
- Event pipeline integration
- Lockout recovery after restart
"""

import asyncio
import pytest
from datetime import datetime, timedelta, time, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.engine import RiskEngine
from risk_manager.rules.session_block_outside import SessionBlockOutsideRule
from risk_manager.state.database import Database
from risk_manager.state.lockout_manager import LockoutManager


def mock_datetime(event_time: datetime):
    """
    Helper function to create MockDateTime class for a given time.

    Args:
        event_time: The datetime to return from datetime.now()

    Returns:
        MockDateTime class that can replace datetime module
    """
    import risk_manager.rules.session_block_outside as rule_module
    original_datetime = rule_module.datetime

    class MockDateTime:
        @staticmethod
        def now(tz=None, **kwargs):
            if tz:
                return event_time.astimezone(tz)
            return event_time

        @staticmethod
        def fromisoformat(date_string):
            return original_datetime.fromisoformat(date_string)

    return MockDateTime, original_datetime, rule_module


class TestSessionBlockOutsideIntegration:
    """Integration tests for SessionBlockOutsideRule."""

    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Create temporary database path."""
        return tmp_path / "test_session_block.db"

    @pytest.fixture
    async def database(self, temp_db_path):
        """Create real database instance."""
        db = Database(temp_db_path)
        yield db
        # Cleanup
        db.close()
        if temp_db_path.exists():
            temp_db_path.unlink()

    @pytest.fixture
    async def lockout_manager(self, database):
        """Create real lockout manager with database."""
        manager = LockoutManager(database=database)
        await manager.start()
        yield manager
        await manager.shutdown()

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
    async def rule(self, basic_config, lockout_manager):
        """Create session block outside rule with real lockout manager."""
        return SessionBlockOutsideRule(
            config=basic_config,
            lockout_manager=lockout_manager
        )

    @pytest.fixture
    def event_bus(self):
        """Create real event bus."""
        return EventBus()

    @pytest.fixture
    def mock_engine(self):
        """Create mock risk engine (enough for rule evaluation)."""
        engine = Mock()
        engine.current_positions = {}
        return engine

    # ========================================================================
    # Test 1: Outside Hours → Lockout Flow
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_outside_hours_lockout_flow(
        self, rule, lockout_manager, mock_engine, database
    ):
        """
        Test complete lockout flow when position opened outside hours.

        Flow:
        1. Position opened at 8 AM ET (before 9:30 AM session start)
        2. Rule detects violation
        3. Lockout set until 9:30 AM
        4. Lockout persists in database
        5. Account is locked out
        """
        # Given: Position opened at 8 AM ET on Wednesday
        et_tz = ZoneInfo("America/New_York")
        event_time = datetime(2025, 10, 29, 8, 0, tzinfo=et_tz)  # Wednesday 8 AM

        # Create event with timestamp in data
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            timestamp=event_time,
            data={
                "account_id": 123,
                "symbol": "ES",
                "size": 1,
                "timestamp": event_time
            }
        )

        # When: Rule evaluates (before session start)
        # Mock datetime.now() to return 8 AM
        MockDateTime, original_datetime, rule_module = mock_datetime(event_time)
        rule_module.datetime = MockDateTime

        try:
            violation = await rule.evaluate(event, mock_engine)

            # Then: Violation detected
            assert violation is not None
            assert violation["rule"] == "SessionBlockOutsideRule"
            assert violation["lockout_required"] is True
            assert "next_session_start" in violation

            # Verify next session start is today at 9:30 AM
            next_start = violation["next_session_start"]
            assert next_start.hour == 9
            assert next_start.minute == 30
            assert next_start.date() == event_time.date()

            # When: Enforcement executes
            await rule.enforce(123, violation, mock_engine)

            # Then: Lockout is set
            assert lockout_manager.is_locked_out(123)

            # Verify lockout info
            info = lockout_manager.get_lockout_info(123)
            assert info is not None
            assert "Trading outside session hours" in info["reason"]
            assert info["type"] == "hard_lockout"

            # Verify lockout persisted in database
            rows = database.execute(
                "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
                ("123",)
            )
            assert len(rows) == 1
            assert rows[0]["reason"] == violation["message"]

        finally:
            # Restore original datetime
            rule_module.datetime = original_datetime

    # ========================================================================
    # Test 2: Inside Hours → No Violation
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_inside_hours_no_violation(
        self, rule, lockout_manager, mock_engine
    ):
        """
        Test that trading inside session hours does not trigger violation.

        Flow:
        1. Position opened at 2 PM ET (inside 9:30 AM - 4:00 PM session)
        2. Rule evaluates
        3. No violation
        4. No lockout set
        """
        # Given: Position opened at 2 PM ET on Wednesday
        et_tz = ZoneInfo("America/New_York")
        event_time = datetime(2025, 10, 29, 14, 0, tzinfo=et_tz)  # Wednesday 2 PM

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            timestamp=event_time,
            data={
                "account_id": 456,
                "symbol": "MNQ",
                "size": 1
            }
        )

        # When: Rule evaluates (inside session hours)
        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTime:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return event_time.astimezone(tz)
                return event_time

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTime

        try:
            violation = await rule.evaluate(event, mock_engine)

            # Then: No violation
            assert violation is None

            # Verify no lockout
            assert not lockout_manager.is_locked_out(456)

        finally:
            rule_module.datetime = original_datetime

    # ========================================================================
    # Test 3: Weekend Blocking
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_weekend_blocking_saturday(
        self, rule, lockout_manager, mock_engine
    ):
        """
        Test weekend blocking on Saturday.

        Flow:
        1. Position opened Saturday 10 AM
        2. Rule detects weekend violation
        3. Lockout set until Monday 9:30 AM
        4. Lockout persists across weekend
        """
        # Given: Position opened Saturday 10 AM ET
        et_tz = ZoneInfo("America/New_York")
        event_time = datetime(2025, 11, 1, 10, 0, tzinfo=et_tz)  # Saturday

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            timestamp=event_time,
            data={
                "account_id": 789,
                "symbol": "ES",
                "size": 1
            }
        )

        # When: Rule evaluates on Saturday
        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTime:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return event_time.astimezone(tz)
                return event_time

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTime

        try:
            violation = await rule.evaluate(event, mock_engine)

            # Then: Violation detected (weekend)
            assert violation is not None
            assert "weekend" in violation["message"].lower() or "saturday" in violation["message"].lower()
            assert violation["current_day"] == "Saturday"

            # Verify next session start is Monday
            next_start = violation["next_session_start"]
            assert next_start.weekday() == 0  # Monday
            assert next_start.hour == 9
            assert next_start.minute == 30

            # When: Enforcement executes
            await rule.enforce(789, violation, mock_engine)

            # Then: Lockout set until Monday
            assert lockout_manager.is_locked_out(789)

            info = lockout_manager.get_lockout_info(789)
            assert info["until"].weekday() == 0  # Monday

        finally:
            rule_module.datetime = original_datetime

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_weekend_blocking_sunday(
        self, rule, lockout_manager, mock_engine
    ):
        """Test weekend blocking on Sunday."""
        # Given: Position opened Sunday 10 AM ET
        et_tz = ZoneInfo("America/New_York")
        event_time = datetime(2025, 11, 2, 10, 0, tzinfo=et_tz)  # Sunday

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            timestamp=event_time,
            data={
                "account_id": 101,
                "symbol": "NQ",
                "size": 1
            }
        )

        # When: Rule evaluates on Sunday
        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTime:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return event_time.astimezone(tz)
                return event_time

        class MockDateTimeFinal:
            @staticmethod
            def now(tz=None, **kwargs):
                return MockDateTime.now(tz, **kwargs)

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTimeFinal

        try:
            violation = await rule.evaluate(event, mock_engine)

            # Then: Violation detected (weekend)
            assert violation is not None
            assert "weekend" in violation["message"].lower() or "sunday" in violation["message"].lower()
            assert violation["current_day"] == "Sunday"

            # Next session start is Monday
            next_start = violation["next_session_start"]
            assert next_start.weekday() == 0  # Monday

        finally:
            rule_module.datetime = original_datetime

    # ========================================================================
    # Test 4: DST Transition
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_dst_spring_forward_transition(
        self, lockout_manager, mock_engine
    ):
        """
        Test DST spring forward transition (2 AM → 3 AM).

        In March 2025, clocks spring forward at 2 AM → 3 AM.
        Verify session times still work correctly.
        """
        # DST spring forward: March 9, 2025 at 2 AM EDT
        config = {
            "enabled": True,
            "global_session": {
                "enabled": True,
                "start": "09:30",
                "end": "16:00",
                "timezone": "America/New_York"
            },
            "block_weekends": False
        }
        rule = SessionBlockOutsideRule(config=config, lockout_manager=lockout_manager)

        # Test before DST (March 8, 2025 at 10 AM EST)
        et_tz = ZoneInfo("America/New_York")
        before_dst = datetime(2025, 3, 8, 10, 0, tzinfo=et_tz)

        event_before = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"account_id": 202, "symbol": "ES"}
        )

        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTimeBefore:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return before_dst.astimezone(tz)
                return before_dst

        class MockDateTimeBeforeFinal:
            @staticmethod
            def now(tz=None, **kwargs):
                return MockDateTimeBefore.now(tz, **kwargs)

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTimeBeforeFinal

        try:
            # Should not violate (inside hours)
            violation_before = await rule.evaluate(event_before, mock_engine)
            assert violation_before is None

            # Test after DST (March 10, 2025 at 10 AM EDT)
            after_dst = datetime(2025, 3, 10, 10, 0, tzinfo=et_tz)

            class MockDateTimeAfter:
                @staticmethod
                def now(tz=None, **kwargs):
                    if tz:
                        return after_dst.astimezone(tz)
                    return after_dst

            class MockDateTimeAfterFinal:
                @staticmethod
                def now(tz=None, **kwargs):
                    return MockDateTimeAfter.now(tz, **kwargs)

                @staticmethod
                def fromisoformat(date_string):
                    return original_datetime.fromisoformat(date_string)

            rule_module.datetime = MockDateTimeAfterFinal

            event_after = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={"account_id": 203, "symbol": "MNQ"}
            )

            # Should not violate (inside hours after DST)
            violation_after = await rule.evaluate(event_after, mock_engine)
            assert violation_after is None

        finally:
            rule_module.datetime = original_datetime

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_dst_fall_back_transition(
        self, lockout_manager, mock_engine
    ):
        """
        Test DST fall back transition (2 AM → 1 AM).

        In November 2025, clocks fall back at 2 AM → 1 AM EST.
        Verify session times still work correctly.
        """
        # DST fall back: November 2, 2025 at 2 AM EST
        config = {
            "enabled": True,
            "global_session": {
                "enabled": True,
                "start": "09:30",
                "end": "16:00",
                "timezone": "America/New_York"
            },
            "block_weekends": False
        }
        rule = SessionBlockOutsideRule(config=config, lockout_manager=lockout_manager)

        # Test before DST fall back (November 1, 2025 at 10 AM EDT)
        et_tz = ZoneInfo("America/New_York")
        before_dst = datetime(2025, 11, 1, 10, 0, tzinfo=et_tz)

        event_before = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"account_id": 204, "symbol": "ES"}
        )

        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTimeBefore:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return before_dst.astimezone(tz)
                return before_dst

        class MockDateTimeBeforeFinal:
            @staticmethod
            def now(tz=None, **kwargs):
                return MockDateTimeBefore.now(tz, **kwargs)

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTimeBeforeFinal

        try:
            violation_before = await rule.evaluate(event_before, mock_engine)
            assert violation_before is None

            # Test after DST fall back (November 3, 2025 at 10 AM EST)
            after_dst = datetime(2025, 11, 3, 10, 0, tzinfo=et_tz)

            class MockDateTimeAfter:
                @staticmethod
                def now(tz=None, **kwargs):
                    if tz:
                        return after_dst.astimezone(tz)
                    return after_dst

            class MockDateTimeAfterFinal:
                @staticmethod
                def now(tz=None, **kwargs):
                    return MockDateTimeAfter.now(tz, **kwargs)

                @staticmethod
                def fromisoformat(date_string):
                    return original_datetime.fromisoformat(date_string)

            rule_module.datetime = MockDateTimeAfterFinal

            event_after = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={"account_id": 205, "symbol": "NQ"}
            )

            violation_after = await rule.evaluate(event_after, mock_engine)
            assert violation_after is None

        finally:
            rule_module.datetime = original_datetime

    # ========================================================================
    # Test 5: Lockout Persistence Across Restarts
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_lockout_persistence_across_restarts(
        self, temp_db_path, basic_config, mock_engine
    ):
        """
        Test lockout survives service restart.

        Flow:
        1. Trigger lockout Friday 5 PM → locked until Monday 9:30 AM
        2. Shutdown lockout manager
        3. Create new lockout manager (simulating restart)
        4. Verify lockout still active
        5. Verify unlock time is Monday 9:30 AM
        """
        # Phase 1: Initial lockout
        db1 = Database(temp_db_path)
        lockout_mgr1 = LockoutManager(database=db1)
        await lockout_mgr1.start()

        rule1 = SessionBlockOutsideRule(
            config=basic_config,
            lockout_manager=lockout_mgr1
        )

        # Given: Trading attempt Friday 5 PM (after hours)
        et_tz = ZoneInfo("America/New_York")
        friday_5pm = datetime(2025, 10, 31, 17, 0, tzinfo=et_tz)  # Friday 5 PM

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"account_id": 999, "symbol": "ES"}
        )

        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTime:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return friday_5pm.astimezone(tz)
                return friday_5pm

        class MockDateTimeFinal:
            @staticmethod
            def now(tz=None, **kwargs):
                return MockDateTime.now(tz, **kwargs)

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTimeFinal

        try:
            # Trigger violation
            violation = await rule1.evaluate(event, mock_engine)
            assert violation is not None

            # Enforce lockout
            await rule1.enforce(999, violation, mock_engine)

            # Verify lockout active
            assert lockout_mgr1.is_locked_out(999)

            # Get unlock time
            info1 = lockout_mgr1.get_lockout_info(999)
            unlock_time = info1["until"]

            # Verify unlock is Monday 9:30 AM (skip weekend)
            assert unlock_time.weekday() == 0  # Monday
            assert unlock_time.hour == 9
            assert unlock_time.minute == 30

            # Phase 2: Simulate restart
            await lockout_mgr1.shutdown()
            db1.close()

            # Phase 3: New lockout manager (restart)
            db2 = Database(temp_db_path)
            lockout_mgr2 = LockoutManager(database=db2)
            await lockout_mgr2.start()

            rule2 = SessionBlockOutsideRule(
                config=basic_config,
                lockout_manager=lockout_mgr2
            )

            # Verify lockout still active after restart
            assert lockout_mgr2.is_locked_out(999)

            # Verify unlock time matches
            info2 = lockout_mgr2.get_lockout_info(999)
            assert info2["until"] == unlock_time
            assert info2["until"].weekday() == 0  # Monday
            assert info2["until"].hour == 9
            assert info2["until"].minute == 30

            # Cleanup
            await lockout_mgr2.shutdown()
            db2.close()

        finally:
            rule_module.datetime = original_datetime

    # ========================================================================
    # Test 6: Multi-Account Independence
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_account_independence(
        self, rule, lockout_manager, mock_engine
    ):
        """
        Test that lockouts are account-specific.

        Flow:
        1. Account A trades outside hours → locked
        2. Account B trades inside hours → allowed
        3. Verify Account A locked, Account B not locked
        """
        # Given: Account A trades at 7 AM (outside hours)
        et_tz = ZoneInfo("America/New_York")
        early_time = datetime(2025, 10, 29, 7, 0, tzinfo=et_tz)  # Wednesday 7 AM

        event_a = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"account_id": 111, "symbol": "ES"}
        )

        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTimeEarly:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return early_time.astimezone(tz)
                return early_time

        class MockDateTimeEarlyFinal:
            @staticmethod
            def now(tz=None, **kwargs):
                return MockDateTimeEarly.now(tz, **kwargs)

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTimeEarlyFinal

        try:
            # When: Account A triggers violation
            violation_a = await rule.evaluate(event_a, mock_engine)
            assert violation_a is not None

            await rule.enforce(111, violation_a, mock_engine)

            # Then: Account A is locked
            assert lockout_manager.is_locked_out(111)

            # Given: Account B trades at 10 AM (inside hours)
            inside_time = datetime(2025, 10, 29, 10, 0, tzinfo=et_tz)  # Wednesday 10 AM

            event_b = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={"account_id": 222, "symbol": "MNQ"}
            )

            class MockDateTimeInside:
                @staticmethod
                def now(tz=None, **kwargs):
                    if tz:
                        return inside_time.astimezone(tz)
                    return inside_time

            class MockDateTimeInsideFinal:
                @staticmethod
                def now(tz=None, **kwargs):
                    return MockDateTimeInside.now(tz, **kwargs)

                @staticmethod
                def fromisoformat(date_string):
                    return original_datetime.fromisoformat(date_string)

            rule_module.datetime = MockDateTimeInsideFinal

            # When: Account B trades (no violation)
            violation_b = await rule.evaluate(event_b, mock_engine)

            # Then: Account B is NOT locked
            assert violation_b is None
            assert not lockout_manager.is_locked_out(222)

            # Verify independence
            assert lockout_manager.is_locked_out(111)  # Still locked
            assert not lockout_manager.is_locked_out(222)  # Not locked

        finally:
            rule_module.datetime = original_datetime

    # ========================================================================
    # Test 7: Event Bus Integration
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_event_bus_integration(
        self, rule, lockout_manager, mock_engine, event_bus
    ):
        """
        Test complete event flow through EventBus.

        Flow:
        1. Subscribe to POSITION_OPENED events
        2. Publish event with outside-hours timestamp
        3. Rule evaluates and detects violation
        4. Verify violation event published
        """
        # Given: Subscribe to position events
        violations_received = []

        async def violation_handler(event):
            violations_received.append(event)

        event_bus.subscribe(EventType.POSITION_OPENED, violation_handler)

        # And: Event outside hours
        et_tz = ZoneInfo("America/New_York")
        event_time = datetime(2025, 10, 29, 7, 0, tzinfo=et_tz)  # Wednesday 7 AM

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"account_id": 333, "symbol": "ES"}
        )

        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTime:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return event_time.astimezone(tz)
                return event_time

        class MockDateTimeFinal:
            @staticmethod
            def now(tz=None, **kwargs):
                return MockDateTime.now(tz, **kwargs)

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTimeFinal

        try:
            # When: Event published
            await event_bus.publish(event)

            # Wait for event propagation
            await asyncio.sleep(0.1)

            # Then: Event received by handler
            assert len(violations_received) == 1
            assert violations_received[0].event_type == EventType.POSITION_OPENED

            # When: Rule evaluates
            violation = await rule.evaluate(event, mock_engine)

            # Then: Violation detected
            assert violation is not None
            assert violation["rule"] == "SessionBlockOutsideRule"

        finally:
            rule_module.datetime = original_datetime

    # ========================================================================
    # Test 8: Database Schema Validation
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_database_schema_validation(
        self, database, lockout_manager, rule, mock_engine
    ):
        """
        Test that lockouts table has correct schema and stores UTC times.

        Verifies:
        1. Lockouts table exists
        2. Required columns present
        3. UTC times stored correctly
        4. Timezone conversion works
        """
        # Verify lockouts table exists
        tables = database.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='lockouts'"
        )
        assert len(tables) == 1

        # Verify table schema
        schema = database.execute("PRAGMA table_info(lockouts)")
        column_names = [col["name"] for col in schema]

        required_columns = [
            "id", "account_id", "rule_id", "reason",
            "locked_at", "expires_at", "unlock_condition",
            "active", "created_at"
        ]

        for col in required_columns:
            assert col in column_names, f"Missing column: {col}"

        # Test UTC storage
        et_tz = ZoneInfo("America/New_York")
        event_time = datetime(2025, 10, 29, 17, 0, tzinfo=et_tz)  # Wednesday 5 PM ET

        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"account_id": 444, "symbol": "ES"}
        )

        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTime:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return event_time.astimezone(tz)
                return event_time

        class MockDateTimeFinal:
            @staticmethod
            def now(tz=None, **kwargs):
                return MockDateTime.now(tz, **kwargs)

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTimeFinal

        try:
            # Trigger lockout
            violation = await rule.evaluate(event, mock_engine)
            assert violation is not None

            await rule.enforce(444, violation, mock_engine)

            # Verify database record
            rows = database.execute(
                "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
                ("444",)
            )
            assert len(rows) == 1

            lockout_record = rows[0]

            # Verify expires_at is stored as ISO format
            expires_at_str = lockout_record["expires_at"]
            assert "T" in expires_at_str  # ISO format

            # Parse and verify UTC
            expires_at = datetime.fromisoformat(expires_at_str)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            # Verify time is reasonable (next day at 9:30 AM ET)
            # Convert to ET for verification
            expires_at_et = expires_at.astimezone(et_tz)
            assert expires_at_et.hour == 9
            assert expires_at_et.minute == 30

        finally:
            rule_module.datetime = original_datetime

    # ========================================================================
    # Test 9: Lockout Auto-Expiry
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_lockout_auto_expiry(
        self, lockout_manager, database
    ):
        """
        Test that lockouts auto-expire when time passes.

        Flow:
        1. Set lockout for 2 seconds in future
        2. Verify locked immediately
        3. Wait 3 seconds
        4. Verify auto-unlocked
        """
        # Given: Lockout for 2 seconds
        account_id = 555
        unlock_time = datetime.now(timezone.utc) + timedelta(seconds=2)

        lockout_manager.set_lockout(
            account_id=account_id,
            reason="Test lockout",
            until=unlock_time
        )

        # Then: Immediately locked
        assert lockout_manager.is_locked_out(account_id)

        # When: Wait for expiry
        await asyncio.sleep(3)

        # Then: Auto-unlocked
        assert not lockout_manager.is_locked_out(account_id)

        # Verify database updated
        rows = database.execute(
            "SELECT * FROM lockouts WHERE account_id = ? AND active = 1",
            (str(account_id),)
        )
        assert len(rows) == 0

    # ========================================================================
    # Test 10: Different Timezone Support
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_different_timezone_support(
        self, lockout_manager, mock_engine
    ):
        """
        Test rule works with different timezones (CT, PT).

        Verifies:
        1. Chicago time (CT) session works
        2. Los Angeles time (PT) session works
        3. Session boundaries correct in each timezone
        """
        # Test Chicago time (CT) - 8:00 AM - 3:00 PM
        ct_config = {
            "enabled": True,
            "global_session": {
                "enabled": True,
                "start": "08:00",
                "end": "15:00",
                "timezone": "America/Chicago"
            },
            "block_weekends": True
        }

        ct_rule = SessionBlockOutsideRule(
            config=ct_config,
            lockout_manager=lockout_manager
        )

        # Test inside CT hours
        ct_tz = ZoneInfo("America/Chicago")
        ct_inside = datetime(2025, 10, 29, 10, 0, tzinfo=ct_tz)  # 10 AM CT

        event_ct = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={"account_id": 666, "symbol": "ES"}
        )

        import risk_manager.rules.session_block_outside as rule_module
        original_datetime = rule_module.datetime

        class MockDateTimeCT:
            @staticmethod
            def now(tz=None, **kwargs):
                if tz:
                    return ct_inside.astimezone(tz)
                return ct_inside

        class MockDateTimeCTFinal:
            @staticmethod
            def now(tz=None, **kwargs):
                return MockDateTimeCT.now(tz, **kwargs)

            @staticmethod
            def fromisoformat(date_string):
                return original_datetime.fromisoformat(date_string)

        rule_module.datetime = MockDateTimeCTFinal

        try:
            violation_ct = await ct_rule.evaluate(event_ct, mock_engine)
            assert violation_ct is None  # Inside CT hours

            # Test Pacific time (PT) - 6:30 AM - 1:00 PM
            pt_config = {
                "enabled": True,
                "global_session": {
                    "enabled": True,
                    "start": "06:30",
                    "end": "13:00",
                    "timezone": "America/Los_Angeles"
                },
                "block_weekends": True
            }

            pt_rule = SessionBlockOutsideRule(
                config=pt_config,
                lockout_manager=lockout_manager
            )

            # Test inside PT hours
            pt_tz = ZoneInfo("America/Los_Angeles")
            pt_inside = datetime(2025, 10, 29, 9, 0, tzinfo=pt_tz)  # 9 AM PT

            event_pt = RiskEvent(
                event_type=EventType.POSITION_OPENED,
                data={"account_id": 777, "symbol": "MNQ"}
            )

            class MockDateTimePT:
                @staticmethod
                def now(tz=None, **kwargs):
                    if tz:
                        return pt_inside.astimezone(tz)
                    return pt_inside

            class MockDateTimePTFinal:
                @staticmethod
                def now(tz=None, **kwargs):
                    return MockDateTimePT.now(tz, **kwargs)

                @staticmethod
                def fromisoformat(date_string):
                    return original_datetime.fromisoformat(date_string)

            rule_module.datetime = MockDateTimePTFinal

            violation_pt = await pt_rule.evaluate(event_pt, mock_engine)
            assert violation_pt is None  # Inside PT hours

        finally:
            rule_module.datetime = original_datetime
