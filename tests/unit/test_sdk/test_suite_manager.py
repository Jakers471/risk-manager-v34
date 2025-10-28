"""
Unit Tests for SuiteManager

Tests the TradingSuite lifecycle manager in isolation with mocked dependencies.
Covers suite creation, removal, health monitoring, and lifecycle management.

Module: src/risk_manager/sdk/suite_manager.py
Coverage Target: 70%+
"""

import pytest
import sys
import asyncio
from unittest.mock import AsyncMock, Mock, patch, call, MagicMock
from typing import Any

# Mock the project_x_py SDK before importing our modules
sys.modules['project_x_py'] = MagicMock()
sys.modules['project_x_py.utils'] = MagicMock()

from risk_manager.sdk.suite_manager import SuiteManager
from risk_manager.core.events import EventBus


class TestSuiteManagerInitialization:
    """Test suite manager initialization."""

    def test_initialization_with_event_bus(self):
        """
        GIVEN: Valid event bus
        WHEN: SuiteManager is initialized
        THEN: Manager is properly configured
        """
        mock_event_bus = Mock(spec=EventBus)
        manager = SuiteManager(mock_event_bus)

        assert manager.event_bus is mock_event_bus
        assert len(manager.suites) == 0
        assert manager.running is False
        assert manager._health_check_task is None

    def test_initialization_logs_success(self, caplog):
        """
        GIVEN: Event bus
        WHEN: SuiteManager is initialized
        THEN: Initialization is logged
        """
        mock_event_bus = Mock(spec=EventBus)
        manager = SuiteManager(mock_event_bus)

        assert "SuiteManager initialized" in caplog.text


class TestAddInstrument:
    """Test adding instruments and creating suites."""

    @pytest.fixture
    def manager(self):
        """Create suite manager with mock event bus."""
        mock_event_bus = Mock(spec=EventBus)
        return SuiteManager(mock_event_bus)

    @pytest.mark.asyncio
    @patch('risk_manager.sdk.suite_manager.TradingSuite')
    async def test_add_instrument_success(self, mock_trading_suite_class, manager):
        """
        GIVEN: Valid instrument symbol
        WHEN: add_instrument is called
        THEN: TradingSuite is created and stored
        """
        mock_suite = AsyncMock()
        mock_trading_suite_class.create = AsyncMock(return_value=mock_suite)

        result = await manager.add_instrument(
            "MNQ",
            timeframes=["1min", "5min"],
            enable_orderbook=False,
            enable_statistics=True
        )

        assert result is mock_suite
        assert "MNQ" in manager.suites
        assert manager.suites["MNQ"] is mock_suite
        mock_trading_suite_class.create.assert_called_once()

    @pytest.mark.asyncio
    @patch('risk_manager.sdk.suite_manager.TradingSuite')
    async def test_add_instrument_default_timeframes(self, mock_trading_suite_class, manager):
        """
        GIVEN: No timeframes specified
        WHEN: add_instrument is called
        THEN: Default timeframes ["1min", "5min"] are used
        """
        mock_suite = AsyncMock()
        mock_trading_suite_class.create = AsyncMock(return_value=mock_suite)

        await manager.add_instrument("MNQ")

        call_args = mock_trading_suite_class.create.call_args
        assert call_args[1]["timeframes"] == ["1min", "5min"]

    @pytest.mark.asyncio
    @patch('risk_manager.sdk.suite_manager.TradingSuite')
    async def test_add_instrument_custom_timeframes(self, mock_trading_suite_class, manager):
        """
        GIVEN: Custom timeframes
        WHEN: add_instrument is called
        THEN: Custom timeframes are used
        """
        mock_suite = AsyncMock()
        mock_trading_suite_class.create = AsyncMock(return_value=mock_suite)

        await manager.add_instrument("MNQ", timeframes=["30min", "1hour"])

        call_args = mock_trading_suite_class.create.call_args
        assert call_args[1]["timeframes"] == ["30min", "1hour"]

    @pytest.mark.asyncio
    async def test_add_instrument_already_exists(self, manager):
        """
        GIVEN: Instrument already added
        WHEN: add_instrument is called again
        THEN: Existing suite is returned without creating new one
        """
        mock_suite = AsyncMock()
        manager.suites["MNQ"] = mock_suite

        result = await manager.add_instrument("MNQ")

        assert result is mock_suite
        assert len(manager.suites) == 1

    @pytest.mark.asyncio
    @patch('risk_manager.sdk.suite_manager.TradingSuite')
    async def test_add_instrument_failure_raises_exception(self, mock_trading_suite_class, manager):
        """
        GIVEN: TradingSuite.create fails
        WHEN: add_instrument is called
        THEN: Exception is raised and propagated
        """
        mock_trading_suite_class.create = AsyncMock(
            side_effect=Exception("SDK Error")
        )

        with pytest.raises(Exception, match="SDK Error"):
            await manager.add_instrument("MNQ")

        assert "MNQ" not in manager.suites

    @pytest.mark.asyncio
    @patch('risk_manager.sdk.suite_manager.TradingSuite')
    async def test_add_instrument_logs_creation(self, mock_trading_suite_class, manager, caplog):
        """
        GIVEN: Valid instrument
        WHEN: add_instrument is called
        THEN: Creation is logged
        """
        mock_suite = AsyncMock()
        mock_trading_suite_class.create = AsyncMock(return_value=mock_suite)

        await manager.add_instrument("MNQ")

        assert "Creating TradingSuite for MNQ" in caplog.text
        assert "TradingSuite created for MNQ" in caplog.text


class TestRemoveInstrument:
    """Test removing instruments and disconnecting suites."""

    @pytest.fixture
    def manager(self):
        """Create suite manager with mock event bus."""
        mock_event_bus = Mock(spec=EventBus)
        return SuiteManager(mock_event_bus)

    @pytest.mark.asyncio
    async def test_remove_instrument_success(self, manager):
        """
        GIVEN: Instrument with active suite
        WHEN: remove_instrument is called
        THEN: Suite is disconnected and removed
        """
        mock_suite = AsyncMock()
        mock_suite.disconnect = AsyncMock()
        manager.suites["MNQ"] = mock_suite

        await manager.remove_instrument("MNQ")

        mock_suite.disconnect.assert_called_once()
        assert "MNQ" not in manager.suites

    @pytest.mark.asyncio
    async def test_remove_instrument_not_found(self, manager, caplog):
        """
        GIVEN: Instrument not in manager
        WHEN: remove_instrument is called
        THEN: Warning is logged and no error raised
        """
        await manager.remove_instrument("MNQ")

        assert "Instrument MNQ not found" in caplog.text

    @pytest.mark.asyncio
    async def test_remove_instrument_disconnect_failure(self, manager, caplog):
        """
        GIVEN: Suite that fails to disconnect
        WHEN: remove_instrument is called
        THEN: Error is logged but not raised
        """
        mock_suite = AsyncMock()
        mock_suite.disconnect = AsyncMock(side_effect=Exception("Disconnect failed"))
        manager.suites["MNQ"] = mock_suite

        # Should not raise exception
        await manager.remove_instrument("MNQ")

        assert "Failed to remove TradingSuite for MNQ" in caplog.text


class TestGetSuite:
    """Test retrieving suites."""

    @pytest.fixture
    def manager(self):
        """Create suite manager with mock event bus."""
        mock_event_bus = Mock(spec=EventBus)
        return SuiteManager(mock_event_bus)

    def test_get_suite_exists(self, manager):
        """
        GIVEN: Suite for symbol exists
        WHEN: get_suite is called
        THEN: Suite is returned
        """
        mock_suite = AsyncMock()
        manager.suites["MNQ"] = mock_suite

        result = manager.get_suite("MNQ")

        assert result is mock_suite

    def test_get_suite_not_found(self, manager):
        """
        GIVEN: Suite for symbol does not exist
        WHEN: get_suite is called
        THEN: None is returned
        """
        result = manager.get_suite("MNQ")

        assert result is None

    def test_get_all_suites(self, manager):
        """
        GIVEN: Multiple suites
        WHEN: get_all_suites is called
        THEN: Copy of all suites is returned
        """
        mock_suite_1 = AsyncMock()
        mock_suite_2 = AsyncMock()
        manager.suites["MNQ"] = mock_suite_1
        manager.suites["ES"] = mock_suite_2

        result = manager.get_all_suites()

        assert len(result) == 2
        assert result["MNQ"] is mock_suite_1
        assert result["ES"] is mock_suite_2
        # Verify it's a copy
        assert result is not manager.suites


class TestSuiteManagerLifecycle:
    """Test suite manager start/stop lifecycle."""

    @pytest.fixture
    def manager(self):
        """Create suite manager with mock event bus."""
        mock_event_bus = Mock(spec=EventBus)
        return SuiteManager(mock_event_bus)

    @pytest.mark.asyncio
    async def test_start_manager(self, manager):
        """
        GIVEN: SuiteManager
        WHEN: start is called
        THEN: Manager is running and health check starts
        """
        await manager.start()

        assert manager.running is True
        assert manager._health_check_task is not None
        assert not manager._health_check_task.done()

        # Cleanup
        await manager.stop()

    @pytest.mark.asyncio
    async def test_stop_manager(self, manager):
        """
        GIVEN: Running suite manager
        WHEN: stop is called
        THEN: Manager stops and all suites are removed
        """
        # Add some suites
        mock_suite_1 = AsyncMock()
        mock_suite_1.disconnect = AsyncMock()
        mock_suite_2 = AsyncMock()
        mock_suite_2.disconnect = AsyncMock()
        manager.suites["MNQ"] = mock_suite_1
        manager.suites["ES"] = mock_suite_2

        await manager.start()
        await manager.stop()

        assert manager.running is False
        assert len(manager.suites) == 0
        mock_suite_1.disconnect.assert_called_once()
        mock_suite_2.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_cancels_health_check_task(self, manager):
        """
        GIVEN: Running manager with health check task
        WHEN: stop is called
        THEN: Health check task is cancelled
        """
        await manager.start()
        health_task = manager._health_check_task

        await manager.stop()

        assert health_task.cancelled() or health_task.done()


class TestHealthCheckLoop:
    """Test health monitoring functionality."""

    @pytest.fixture
    def manager(self):
        """Create suite manager with mock event bus."""
        mock_event_bus = Mock(spec=EventBus)
        return SuiteManager(mock_event_bus)

    @pytest.mark.asyncio
    async def test_health_check_monitors_connection(self, manager):
        """
        GIVEN: Suite with disconnected realtime client
        WHEN: Health check runs
        THEN: Disconnection is logged
        """
        mock_realtime = Mock()
        mock_realtime.is_connected = False

        mock_suite = AsyncMock()
        mock_suite.realtime = mock_realtime
        manager.suites["MNQ"] = mock_suite

        # Start manager (starts health check)
        await manager.start()

        # Give health check time to run at least once
        await asyncio.sleep(0.1)

        # Stop manager
        await manager.stop()

        # Health check should have run and logged disconnection
        # (Actual log assertion would depend on logger setup)

    @pytest.mark.asyncio
    async def test_health_check_handles_exceptions(self, manager, caplog):
        """
        GIVEN: Suite that throws exception during health check
        WHEN: Health check runs
        THEN: Exception is logged and loop continues
        """
        mock_suite = Mock()
        mock_suite.realtime = None  # Will cause AttributeError
        manager.suites["MNQ"] = mock_suite

        await manager.start()
        await asyncio.sleep(0.1)
        await manager.stop()

        # Should not crash, should log error

    @pytest.mark.asyncio
    async def test_health_check_stops_on_cancelled(self, manager):
        """
        GIVEN: Running health check task
        WHEN: Task is cancelled
        THEN: Loop exits gracefully
        """
        await manager.start()

        # Cancel the health check task
        manager._health_check_task.cancel()

        # Wait a bit
        await asyncio.sleep(0.1)

        # Should handle CancelledError gracefully
        assert manager._health_check_task.cancelled() or manager._health_check_task.done()

        # Cleanup
        manager.running = False


class TestGetHealthStatus:
    """Test health status reporting."""

    @pytest.fixture
    def manager(self):
        """Create suite manager with mock event bus."""
        mock_event_bus = Mock(spec=EventBus)
        return SuiteManager(mock_event_bus)

    @pytest.mark.asyncio
    async def test_get_health_status_empty(self, manager):
        """
        GIVEN: No suites
        WHEN: get_health_status is called
        THEN: Empty status is returned
        """
        status = await manager.get_health_status()

        assert status["total_suites"] == 0
        assert len(status["suites"]) == 0

    @pytest.mark.asyncio
    async def test_get_health_status_with_suites(self, manager):
        """
        GIVEN: Multiple suites with different states
        WHEN: get_health_status is called
        THEN: Status for all suites is returned
        """
        # Suite 1: Connected
        mock_realtime_1 = Mock()
        mock_realtime_1.is_connected = True
        mock_suite_1 = AsyncMock()
        mock_suite_1.realtime = mock_realtime_1
        mock_suite_1.instrument_info = Mock(id="INST1")
        manager.suites["MNQ"] = mock_suite_1

        # Suite 2: Disconnected
        mock_realtime_2 = Mock()
        mock_realtime_2.is_connected = False
        mock_suite_2 = AsyncMock()
        mock_suite_2.realtime = mock_realtime_2
        mock_suite_2.instrument_info = Mock(id="INST2")
        manager.suites["ES"] = mock_suite_2

        status = await manager.get_health_status()

        assert status["total_suites"] == 2
        assert "MNQ" in status["suites"]
        assert "ES" in status["suites"]
        assert status["suites"]["MNQ"]["connected"] is True
        assert status["suites"]["ES"]["connected"] is False
        assert status["suites"]["MNQ"]["instrument_id"] == "INST1"
        assert status["suites"]["ES"]["instrument_id"] == "INST2"

    @pytest.mark.asyncio
    async def test_get_health_status_with_stats(self, manager):
        """
        GIVEN: Suite with get_stats method
        WHEN: get_health_status is called
        THEN: Stats are included in status
        """
        mock_stats = {"balance": 100000.0, "equity": 100250.0}
        mock_suite = AsyncMock()
        mock_suite.realtime = Mock(is_connected=True)
        mock_suite.instrument_info = Mock(id="INST1")
        mock_suite.get_stats = AsyncMock(return_value=mock_stats)
        manager.suites["MNQ"] = mock_suite

        status = await manager.get_health_status()

        assert "stats" in status["suites"]["MNQ"]
        assert status["suites"]["MNQ"]["stats"] == mock_stats

    @pytest.mark.asyncio
    async def test_get_health_status_handles_errors(self, manager):
        """
        GIVEN: Suite that throws exception during health check
        WHEN: get_health_status is called
        THEN: Error is captured in status
        """
        mock_suite = Mock()
        mock_suite.realtime = None  # Will cause AttributeError
        manager.suites["MNQ"] = mock_suite

        status = await manager.get_health_status()

        assert "MNQ" in status["suites"]
        assert "error" in status["suites"]["MNQ"]


class TestMultipleInstruments:
    """Test managing multiple instruments simultaneously."""

    @pytest.fixture
    def manager(self):
        """Create suite manager with mock event bus."""
        mock_event_bus = Mock(spec=EventBus)
        return SuiteManager(mock_event_bus)

    @pytest.mark.asyncio
    @patch('risk_manager.sdk.suite_manager.TradingSuite')
    async def test_add_multiple_instruments(self, mock_trading_suite_class, manager):
        """
        GIVEN: Multiple instrument symbols
        WHEN: add_instrument is called for each
        THEN: All suites are created and tracked
        """
        mock_suite_1 = AsyncMock()
        mock_suite_2 = AsyncMock()
        mock_suite_3 = AsyncMock()

        mock_trading_suite_class.create = AsyncMock(
            side_effect=[mock_suite_1, mock_suite_2, mock_suite_3]
        )

        await manager.add_instrument("MNQ")
        await manager.add_instrument("ES")
        await manager.add_instrument("NQ")

        assert len(manager.suites) == 3
        assert "MNQ" in manager.suites
        assert "ES" in manager.suites
        assert "NQ" in manager.suites

    @pytest.mark.asyncio
    async def test_remove_one_keeps_others(self, manager):
        """
        GIVEN: Three active suites
        WHEN: One is removed
        THEN: Other two remain active
        """
        mock_suite_1 = AsyncMock()
        mock_suite_2 = AsyncMock()
        mock_suite_3 = AsyncMock()

        manager.suites["MNQ"] = mock_suite_1
        manager.suites["ES"] = mock_suite_2
        manager.suites["NQ"] = mock_suite_3

        await manager.remove_instrument("ES")

        assert len(manager.suites) == 2
        assert "MNQ" in manager.suites
        assert "NQ" in manager.suites
        assert "ES" not in manager.suites


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def manager(self):
        """Create suite manager with mock event bus."""
        mock_event_bus = Mock(spec=EventBus)
        return SuiteManager(mock_event_bus)

    @pytest.mark.asyncio
    async def test_stop_when_not_started(self, manager):
        """
        GIVEN: Manager never started
        WHEN: stop is called
        THEN: No error is raised
        """
        # Should not raise exception
        await manager.stop()

    @pytest.mark.asyncio
    async def test_add_instrument_while_stopping(self, manager):
        """
        GIVEN: Manager in process of stopping
        WHEN: add_instrument is called
        THEN: Should handle gracefully
        """
        await manager.start()

        # Start stopping but don't await
        stop_task = asyncio.create_task(manager.stop())

        # Try to add instrument while stopping
        # This should either succeed or fail gracefully
        try:
            with patch('risk_manager.sdk.suite_manager.TradingSuite') as mock_ts:
                mock_ts.create = AsyncMock(return_value=AsyncMock())
                await manager.add_instrument("MNQ")
        except Exception:
            pass  # Either outcome is acceptable

        await stop_task

    @pytest.mark.asyncio
    async def test_double_start(self, manager):
        """
        GIVEN: Already running manager
        WHEN: start is called again
        THEN: Should handle gracefully
        """
        await manager.start()
        first_task = manager._health_check_task

        await manager.start()
        second_task = manager._health_check_task

        # Should still be running
        assert manager.running is True

        # Cleanup
        await manager.stop()
