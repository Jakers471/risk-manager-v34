"""
Integration Tests for TradeFrequencyLimitRule (RULE-006)

Tests the rule working with real database, real TimerManager, and real event sequences.
Validates complete integration without mocking core dependencies.

Focus Areas:
- Real Database trade tracking
- Real TimerManager cooldown timers
- Rolling window queries
- Multi-tier limits (minute, hour, session)
- Cooldown auto-unlock
- Multi-account independence
- Event sequence flow
"""

import pytest
import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from risk_manager.rules.trade_frequency_limit import TradeFrequencyLimitRule
from risk_manager.core.events import RiskEvent, EventType
from risk_manager.state.database import Database
from risk_manager.state.timer_manager import TimerManager


class TestTradeFrequencyLimitIntegration:
    """Integration tests for TradeFrequencyLimitRule with real database and timers."""

    @pytest.fixture
    async def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = Database(db_path)
        yield db

        # Cleanup
        db.close()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    async def timer_manager(self):
        """Create real TimerManager."""
        manager = TimerManager()
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.fixture
    async def integration_setup(self, temp_db, timer_manager):
        """Create complete integration setup with real components."""
        # Add trade tracking methods to database
        self._add_trade_tracking_methods(temp_db)

        rule = TradeFrequencyLimitRule(
            limits={
                'per_minute': 3,
                'per_hour': 10,
                'per_session': 50
            },
            cooldown_on_breach={
                'per_minute_breach': 2,      # 2s for fast testing
                'per_hour_breach': 5,        # 5s for fast testing
                'per_session_breach': 8      # 8s for fast testing
            },
            timer_manager=timer_manager,
            db=temp_db,
            action="cooldown"
        )

        return {
            'rule': rule,
            'db': temp_db,
            'timer_manager': timer_manager
        }

    def _add_trade_tracking_methods(self, db):
        """Add trade tracking methods to database instance."""

        def get_trade_count(account_id, window):
            """Get trade count in rolling window (seconds)."""
            cutoff = datetime.now() - timedelta(seconds=window)

            result = db.execute_one(
                """
                SELECT COUNT(*) as count
                FROM trades
                WHERE account_id = ? AND timestamp >= ?
                """,
                (account_id, cutoff.isoformat())
            )
            return result['count'] if result else 0

        def get_session_trade_count(account_id):
            """Get trade count for current session (today)."""
            today = datetime.now().date().isoformat()

            result = db.execute_one(
                """
                SELECT COUNT(*) as count
                FROM trades
                WHERE account_id = ? AND DATE(timestamp) = ?
                """,
                (account_id, today)
            )
            return result['count'] if result else 0

        def add_trade(account_id, symbol="MNQ", timestamp=None):
            """Add trade to database."""
            if timestamp is None:
                timestamp = datetime.now()

            # Generate unique trade ID using timestamp + random component
            import random
            trade_id = f"TRADE-{timestamp.timestamp()}-{random.randint(1000, 9999)}"

            db.execute_write(
                """
                INSERT INTO trades
                (account_id, trade_id, symbol, side, quantity, price, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id,
                    trade_id,
                    symbol,
                    "BUY",
                    1,
                    20100.0,
                    timestamp.isoformat(),
                    datetime.now().isoformat()
                )
            )

        def clear_trades(account_id):
            """Clear all trades for account (test cleanup)."""
            db.execute_write("DELETE FROM trades WHERE account_id = ?", (account_id,))

        # Attach methods to database instance
        db.get_trade_count = get_trade_count
        db.get_session_trade_count = get_session_trade_count
        db.add_trade = add_trade
        db.clear_trades = clear_trades

    @pytest.fixture
    def mock_engine(self):
        """Create mock engine for rule.enforce() calls."""
        from unittest.mock import AsyncMock
        engine = AsyncMock()
        engine.account_id = "ACC-001"
        return engine

    # ========================================================================
    # Test 1: Full Frequency Limit + Cooldown Flow
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_frequency_limit_cooldown_flow(self, integration_setup, mock_engine):
        """
        GIVEN: Rule with 3 trades/min limit and 2s cooldown
        WHEN: Execute 4 trades within 60s
        THEN: 4th trade violates, cooldown timer starts, auto-unlocks after 2s
        """
        rule = integration_setup['rule']
        db = integration_setup['db']
        timer_mgr = integration_setup['timer_manager']

        account_id = "ACC-001"

        # Execute trades 1, 2, 3 (within limit)
        for i in range(3):
            db.add_trade(account_id)
            event = RiskEvent(
                event_type=EventType.TRADE_EXECUTED,
                data={"account_id": account_id, "symbol": "MNQ"}
            )
            violation = await rule.evaluate(event, mock_engine)
            assert violation is None, f"Trade {i+1} should not violate"

        # Execute trade 4 (exceeds limit)
        db.add_trade(account_id)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "ES"}
        )
        violation = await rule.evaluate(event, mock_engine)

        # Verify violation detected
        assert violation is not None
        assert violation['breach_type'] == 'per_minute'
        assert violation['trade_count'] == 4
        assert violation['limit'] == 3
        assert violation['cooldown_duration'] == 2

        # Trigger enforcement (starts timer)
        await rule.enforce(account_id, violation, mock_engine)

        # Verify timer started
        timer_name = f"trade_frequency_{account_id}"
        assert timer_mgr.has_timer(timer_name)

        # Verify timer has remaining time
        remaining = timer_mgr.get_remaining_time(timer_name)
        assert remaining > 0
        assert remaining <= 2

        # Wait for cooldown to expire
        await asyncio.sleep(2.5)

        # Verify timer expired
        assert timer_mgr.get_remaining_time(timer_name) == 0

        # Verify can trade again (old trades expired from 60s window)
        # Clear old trades and add new one
        db.clear_trades(account_id)
        db.add_trade(account_id)

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )
        violation = await rule.evaluate(event, mock_engine)
        assert violation is None  # Should not violate after cooldown

    # ========================================================================
    # Test 2: Rolling Window Tracking
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rolling_window_tracking(self, integration_setup, mock_engine):
        """
        GIVEN: 3 trades at T, T+10s, T+20s
        WHEN: Trade at T+70s (oldest trade expired from 60s window)
        THEN: Should pass (only 2 trades in window)
        """
        rule = integration_setup['rule']
        db = integration_setup['db']

        account_id = "ACC-002"
        now = datetime.now()

        # Add 3 trades in the past
        db.add_trade(account_id, timestamp=now - timedelta(seconds=70))  # Expired
        db.add_trade(account_id, timestamp=now - timedelta(seconds=50))  # In window
        db.add_trade(account_id, timestamp=now - timedelta(seconds=30))  # In window

        # Verify only 2 trades in 60s window
        count = db.get_trade_count(account_id, window=60)
        assert count == 2

        # Execute trade at T+70s (should not violate - only 2 in window)
        db.add_trade(account_id)

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )
        violation = await rule.evaluate(event, mock_engine)

        # Should not violate (3 total, but only 2 in window + current = 3 at limit)
        assert violation is None

    # ========================================================================
    # Test 3: Multi-Tier Limits (Minute vs Hour)
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_tier_limits(self, integration_setup, mock_engine):
        """
        GIVEN: 3/min and 10/hour limits
        WHEN: Hit minute limit → 2s cooldown, then hit hour limit → 5s cooldown
        THEN: Correct cooldown durations applied
        """
        rule = integration_setup['rule']
        db = integration_setup['db']

        account_id = "ACC-003"

        # Hit per-minute limit (4 trades)
        for _ in range(4):
            db.add_trade(account_id)

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )
        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert violation['breach_type'] == 'per_minute'
        assert violation['cooldown_duration'] == 2

        # Clear minute trades, add 11 trades in last hour
        db.clear_trades(account_id)
        now = datetime.now()
        for i in range(11):
            # Spread across hour to avoid minute limit
            db.add_trade(account_id, timestamp=now - timedelta(seconds=300 + i*60))

        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert violation['breach_type'] == 'per_hour'
        assert violation['cooldown_duration'] == 5

    # ========================================================================
    # Test 4: Database Persistence Across Rule Instances
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_database_persistence(self, temp_db, timer_manager, mock_engine):
        """
        GIVEN: 2 trades in database
        WHEN: Restart system (new rule instance)
        THEN: Trade history loaded from DB, limits still enforced
        """
        # Add trade tracking methods
        self._add_trade_tracking_methods(temp_db)

        account_id = "ACC-004"

        # Create first rule instance and add 2 trades
        rule1 = TradeFrequencyLimitRule(
            limits={'per_minute': 3, 'per_hour': 10, 'per_session': 50},
            cooldown_on_breach={'per_minute_breach': 2, 'per_hour_breach': 5, 'per_session_breach': 8},
            timer_manager=timer_manager,
            db=temp_db
        )

        temp_db.add_trade(account_id)
        temp_db.add_trade(account_id)

        # Verify count
        assert temp_db.get_trade_count(account_id, 60) == 2

        # Create second rule instance (simulating restart)
        rule2 = TradeFrequencyLimitRule(
            limits={'per_minute': 3, 'per_hour': 10, 'per_session': 50},
            cooldown_on_breach={'per_minute_breach': 2, 'per_hour_breach': 5, 'per_session_breach': 8},
            timer_manager=timer_manager,
            db=temp_db
        )

        # Add 2 more trades (should violate 3-trade limit)
        temp_db.add_trade(account_id)
        temp_db.add_trade(account_id)

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "ES"}
        )

        violation = await rule2.evaluate(event, mock_engine)

        # Should violate (4 trades > 3 limit)
        assert violation is not None
        assert violation['trade_count'] == 4

    # ========================================================================
    # Test 5: Timer Auto-Unlock Integration
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_timer_auto_unlock_integration(self, integration_setup, mock_engine):
        """
        GIVEN: Frequency limit breached
        WHEN: Cooldown timer expires
        THEN: Lockout cleared automatically, can trade again
        """
        rule = integration_setup['rule']
        db = integration_setup['db']
        timer_mgr = integration_setup['timer_manager']

        account_id = "ACC-005"

        # Hit limit
        for _ in range(4):
            db.add_trade(account_id)

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )
        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None

        # Start timer
        await rule.enforce(account_id, violation, mock_engine)

        timer_name = f"trade_frequency_{account_id}"
        assert timer_mgr.has_timer(timer_name)

        # Wait for timer to expire
        await asyncio.sleep(2.5)

        # Timer should be expired
        assert timer_mgr.get_remaining_time(timer_name) == 0

        # Clear trades to test fresh scenario
        db.clear_trades(account_id)
        db.add_trade(account_id)

        # Should be able to trade again
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "ES"}
        )
        violation = await rule.evaluate(event, mock_engine)

        assert violation is None

    # ========================================================================
    # Test 6: Multi-Account Independence
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_account_independence(self, integration_setup, mock_engine):
        """
        GIVEN: Two accounts with separate trade histories
        WHEN: Account A hits limit, Account B continues trading
        THEN: Accounts tracked independently
        """
        rule = integration_setup['rule']
        db = integration_setup['db']

        account_a = "ACC-A"
        account_b = "ACC-B"

        # Account A: 4 trades (exceeds limit)
        for _ in range(4):
            db.add_trade(account_a)

        # Account B: 1 trade (within limit)
        db.add_trade(account_b)

        # Account A should violate
        event_a = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_a, "symbol": "MNQ"}
        )
        violation_a = await rule.evaluate(event_a, mock_engine)

        assert violation_a is not None
        assert violation_a['trade_count'] == 4
        assert violation_a['account_id'] == account_a

        # Account B should not violate
        event_b = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_b, "symbol": "ES"}
        )
        violation_b = await rule.evaluate(event_b, mock_engine)

        assert violation_b is None

        # Account B can continue trading
        db.add_trade(account_b)
        violation_b = await rule.evaluate(event_b, mock_engine)
        assert violation_b is None  # Still within limit

    # ========================================================================
    # Test 7: Session Reset
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_session_reset(self, integration_setup, mock_engine):
        """
        GIVEN: Trades from yesterday
        WHEN: Session reset triggered (new day)
        THEN: Old trades don't count toward today's limit
        """
        rule = integration_setup['rule']
        db = integration_setup['db']

        account_id = "ACC-007"

        # Add trades from yesterday (should not count)
        yesterday = datetime.now() - timedelta(days=1)
        for _ in range(45):
            db.add_trade(account_id, timestamp=yesterday)

        # Add trades today
        for _ in range(3):
            db.add_trade(account_id)

        # Verify session count only includes today
        session_count = db.get_session_trade_count(account_id)
        assert session_count == 3  # Only today's trades

        # Should not violate session limit (3 < 50)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )
        violation = await rule.evaluate(event, mock_engine)

        # Check if it's per_session violation
        if violation is not None:
            assert violation['breach_type'] != 'per_session'

    # ========================================================================
    # Test 8: Priority Order (Minute > Hour > Session)
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_priority_order(self, integration_setup, mock_engine):
        """
        GIVEN: Multiple limits violated simultaneously
        WHEN: Rule evaluates violation
        THEN: Per-minute limit checked first (shortest cooldown)
        """
        rule = integration_setup['rule']
        db = integration_setup['db']

        account_id = "ACC-008"

        # Add enough trades to violate all limits
        # 15 trades in last minute (violates minute and hour)
        for i in range(15):
            db.add_trade(account_id, timestamp=datetime.now() - timedelta(seconds=i))

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )
        violation = await rule.evaluate(event, mock_engine)

        # Should return per_minute violation (highest priority)
        assert violation is not None
        assert violation['breach_type'] == 'per_minute'
        assert violation['cooldown_duration'] == 2  # Shortest cooldown

    # ========================================================================
    # Test 9: Concurrent Trades Rapid Fire
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_rapid_fire_trades(self, integration_setup, mock_engine):
        """
        GIVEN: Rapid-fire trade execution
        WHEN: Multiple trades execute within milliseconds
        THEN: All trades tracked correctly, limit enforced
        """
        rule = integration_setup['rule']
        db = integration_setup['db']

        account_id = "ACC-009"

        # Simulate 5 rapid trades
        for i in range(5):
            db.add_trade(account_id)
            await asyncio.sleep(0.01)  # 10ms between trades

        # Verify all trades tracked
        count = db.get_trade_count(account_id, 60)
        assert count == 5

        # Should violate (5 > 3 limit)
        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )
        violation = await rule.evaluate(event, mock_engine)

        assert violation is not None
        assert violation['trade_count'] == 5

    # ========================================================================
    # Test 10: Timer Cancellation and Restart
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_timer_cancellation_and_restart(self, integration_setup, mock_engine):
        """
        GIVEN: Active cooldown timer
        WHEN: Timer is cancelled and restarted
        THEN: Timer state managed correctly
        """
        rule = integration_setup['rule']
        db = integration_setup['db']
        timer_mgr = integration_setup['timer_manager']

        account_id = "ACC-010"
        timer_name = f"trade_frequency_{account_id}"

        # Hit limit
        for _ in range(4):
            db.add_trade(account_id)

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )
        violation = await rule.evaluate(event, mock_engine)

        # Start timer
        await rule.enforce(account_id, violation, mock_engine)
        assert timer_mgr.has_timer(timer_name)

        # Cancel timer
        timer_mgr.cancel_timer(timer_name)
        assert not timer_mgr.has_timer(timer_name)

        # Restart timer (new violation)
        await rule.enforce(account_id, violation, mock_engine)
        assert timer_mgr.has_timer(timer_name)

        remaining = timer_mgr.get_remaining_time(timer_name)
        assert remaining > 0

    # ========================================================================
    # Test 11: Database Query Performance
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_database_query_performance(self, integration_setup, mock_engine):
        """
        GIVEN: Large number of historical trades
        WHEN: Rolling window query executed
        THEN: Query completes quickly (< 100ms)
        """
        import time

        rule = integration_setup['rule']
        db = integration_setup['db']

        account_id = "ACC-011"

        # Add 1000 historical trades from 2 days ago (definitely not in today's session)
        base_time = datetime.now() - timedelta(days=2)
        for i in range(1000):
            db.add_trade(account_id, timestamp=base_time + timedelta(seconds=i))

        # Add recent trades (today)
        for _ in range(3):
            db.add_trade(account_id)

        # Measure query time
        start = time.time()

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )
        violation = await rule.evaluate(event, mock_engine)

        elapsed = time.time() - start

        # Should complete quickly
        assert elapsed < 0.1, f"Query took {elapsed}s, too slow!"

        # Should not violate (only 3 in recent window)
        assert violation is None

    # ========================================================================
    # Test 12: Error Recovery and Resilience
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_recovery_database_unavailable(self, integration_setup, mock_engine):
        """
        GIVEN: Database query fails
        WHEN: Rule evaluates event
        THEN: Error handled gracefully, returns None (fail-open)
        """
        rule = integration_setup['rule']
        db = integration_setup['db']

        account_id = "ACC-012"

        # Corrupt the get_trade_count method to simulate DB error
        original_method = db.get_trade_count

        def failing_get_trade_count(*args, **kwargs):
            raise Exception("Database connection lost")

        db.get_trade_count = failing_get_trade_count

        event = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={"account_id": account_id, "symbol": "MNQ"}
        )

        # Should not crash, return None (fail-open)
        violation = await rule.evaluate(event, mock_engine)
        assert violation is None

        # Restore method
        db.get_trade_count = original_method
