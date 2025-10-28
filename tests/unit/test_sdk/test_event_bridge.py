"""
Unit Tests for EventBridge

Tests the SDK-to-Risk-Engine event bridge in isolation with mocked dependencies.
Covers event bridging from SignalR callbacks to RiskEvents.

Module: src/risk_manager/sdk/event_bridge.py
Coverage Target: 70%+
"""

import pytest
import sys
import asyncio
from unittest.mock import AsyncMock, Mock, patch, call, MagicMock
from datetime import datetime

# Mock the project_x_py SDK before importing our modules
sys.modules['project_x_py'] = MagicMock()
sys.modules['project_x_py.utils'] = MagicMock()

from risk_manager.sdk.event_bridge import EventBridge
from risk_manager.sdk.suite_manager import SuiteManager
from risk_manager.core.events import EventBus, EventType, RiskEvent


class TestEventBridgeInitialization:
    """Test event bridge initialization."""

    def test_initialization_with_dependencies(self):
        """
        GIVEN: Valid suite manager and event bus
        WHEN: EventBridge is initialized
        THEN: Bridge is properly configured
        """
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = Mock(spec=EventBus)

        bridge = EventBridge(mock_suite_manager, mock_event_bus)

        assert bridge.suite_manager is mock_suite_manager
        assert bridge.risk_event_bus is mock_event_bus
        assert bridge.running is False
        assert len(bridge._subscription_tasks) == 0

    def test_initialization_logs_success(self, caplog):
        """
        GIVEN: Dependencies
        WHEN: EventBridge is initialized
        THEN: Initialization is logged
        """
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = Mock(spec=EventBus)

        bridge = EventBridge(mock_suite_manager, mock_event_bus)

        assert "EventBridge initialized" in caplog.text
        assert "using direct realtime callbacks" in caplog.text


class TestEventBridgeLifecycle:
    """Test event bridge start/stop lifecycle."""

    @pytest.fixture
    def bridge(self):
        """Create event bridge with mocks."""
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = Mock(spec=EventBus)
        return EventBridge(mock_suite_manager, mock_event_bus)

    @pytest.mark.asyncio
    async def test_start_bridge(self, bridge):
        """
        GIVEN: EventBridge with no active suites
        WHEN: start is called
        THEN: Bridge is running
        """
        bridge.suite_manager.get_all_suites = Mock(return_value={})

        await bridge.start()

        assert bridge.running is True

    @pytest.mark.asyncio
    async def test_start_subscribes_to_existing_suites(self, bridge):
        """
        GIVEN: Suite manager with 2 existing suites
        WHEN: start is called
        THEN: Bridge subscribes to both suites
        """
        mock_suite_1 = AsyncMock()
        mock_suite_1.realtime = AsyncMock()
        mock_suite_1.realtime.add_callback = AsyncMock()

        mock_suite_2 = AsyncMock()
        mock_suite_2.realtime = AsyncMock()
        mock_suite_2.realtime.add_callback = AsyncMock()

        bridge.suite_manager.get_all_suites = Mock(
            return_value={
                "MNQ": mock_suite_1,
                "ES": mock_suite_2,
            }
        )

        await bridge.start()

        # Each suite should have 4 callbacks registered
        assert mock_suite_1.realtime.add_callback.call_count == 4
        assert mock_suite_2.realtime.add_callback.call_count == 4

    @pytest.mark.asyncio
    async def test_stop_bridge(self, bridge):
        """
        GIVEN: Running event bridge
        WHEN: stop is called
        THEN: Bridge stops and cancels tasks
        """
        bridge.running = True

        # Create a real asyncio task that we can cancel
        async def dummy_coro():
            await asyncio.sleep(10)

        mock_task = asyncio.create_task(dummy_coro())
        bridge._subscription_tasks = [mock_task]

        await bridge.stop()

        assert bridge.running is False
        assert mock_task.cancelled() or mock_task.done()
        assert len(bridge._subscription_tasks) == 0

    @pytest.mark.asyncio
    async def test_stop_handles_cancelled_tasks(self, bridge):
        """
        GIVEN: Running bridge with tasks
        WHEN: stop is called and tasks raise CancelledError
        THEN: Error is handled gracefully
        """
        bridge.running = True

        # Create a real asyncio task that we can cancel
        async def dummy_coro():
            await asyncio.sleep(10)

        mock_task = asyncio.create_task(dummy_coro())
        bridge._subscription_tasks = [mock_task]

        # Should not raise exception
        await bridge.stop()

        assert len(bridge._subscription_tasks) == 0
        assert mock_task.cancelled() or mock_task.done()


class TestSuiteSubscription:
    """Test subscribing to suite events."""

    @pytest.fixture
    def bridge(self):
        """Create event bridge with mocks."""
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = Mock(spec=EventBus)
        return EventBridge(mock_suite_manager, mock_event_bus)

    @pytest.mark.asyncio
    async def test_subscribe_to_suite_registers_callbacks(self, bridge):
        """
        GIVEN: Suite with realtime client
        WHEN: _subscribe_to_suite is called
        THEN: 4 callbacks are registered (position, order, trade, account)
        """
        mock_suite = AsyncMock()
        mock_suite.realtime = AsyncMock()
        mock_suite.realtime.add_callback = AsyncMock()

        await bridge._subscribe_to_suite("MNQ", mock_suite)

        # Should register 4 callbacks
        assert mock_suite.realtime.add_callback.call_count == 4

        # Verify callback types
        callback_types = [
            call[0][0] for call in mock_suite.realtime.add_callback.call_args_list
        ]
        assert "position_update" in callback_types
        assert "order_update" in callback_types
        assert "trade_update" in callback_types
        assert "account_update" in callback_types

    @pytest.mark.asyncio
    async def test_subscribe_to_suite_no_realtime_client(self, bridge, caplog):
        """
        GIVEN: Suite without realtime client
        WHEN: _subscribe_to_suite is called
        THEN: Warning is logged and subscription is skipped
        """
        mock_suite = Mock()
        mock_suite.realtime = None

        await bridge._subscribe_to_suite("MNQ", mock_suite)

        assert "has no realtime client" in caplog.text

    @pytest.mark.asyncio
    async def test_subscribe_to_suite_failure_raises_exception(self, bridge):
        """
        GIVEN: Suite that fails to register callback
        WHEN: _subscribe_to_suite is called
        THEN: Exception is raised
        """
        mock_suite = AsyncMock()
        mock_suite.realtime = AsyncMock()
        mock_suite.realtime.add_callback = AsyncMock(
            side_effect=Exception("Subscription failed")
        )

        with pytest.raises(Exception, match="Subscription failed"):
            await bridge._subscribe_to_suite("MNQ", mock_suite)


class TestPositionEventHandling:
    """Test position update event handling."""

    @pytest.fixture
    def bridge(self):
        """Create event bridge with mocks."""
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = AsyncMock(spec=EventBus)
        return EventBridge(mock_suite_manager, mock_event_bus)

    @pytest.mark.asyncio
    async def test_position_opened_event(self, bridge):
        """
        GIVEN: SignalR position update with action=1 and size>0
        WHEN: _on_position_update is called
        THEN: POSITION_UPDATED event is published
        """
        position_data = [{
            'action': 1,
            'data': {
                'contractId': 'POS123',
                'size': 2,
                'averagePrice': 20100.0,
                'unrealizedPnl': 50.0,
            }
        }]

        await bridge._on_position_update("MNQ", position_data)

        # Verify event was published
        assert bridge.risk_event_bus.publish.call_count == 1
        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.event_type == EventType.POSITION_UPDATED
        assert published_event.data["symbol"] == "MNQ"
        assert published_event.data["size"] == 2
        assert published_event.data["contract_id"] == "POS123"

    @pytest.mark.asyncio
    async def test_position_closed_event_action_2(self, bridge):
        """
        GIVEN: SignalR position update with action=2 (remove)
        WHEN: _on_position_update is called
        THEN: POSITION_CLOSED event is published
        """
        position_data = [{
            'action': 2,
            'data': {
                'contractId': 'POS123',
                'realizedPnl': 125.50,
            }
        }]

        await bridge._on_position_update("MNQ", position_data)

        assert bridge.risk_event_bus.publish.call_count == 1
        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.event_type == EventType.POSITION_CLOSED
        assert published_event.data["symbol"] == "MNQ"
        assert published_event.data["contract_id"] == "POS123"
        assert published_event.data["realized_pnl"] == 125.50

    @pytest.mark.asyncio
    async def test_position_closed_event_size_zero(self, bridge):
        """
        GIVEN: SignalR position update with action=1 but size=0
        WHEN: _on_position_update is called
        THEN: POSITION_CLOSED event is published
        """
        position_data = [{
            'action': 1,
            'data': {
                'contractId': 'POS123',
                'size': 0,
                'realizedPnl': 75.00,
            }
        }]

        await bridge._on_position_update("MNQ", position_data)

        assert bridge.risk_event_bus.publish.call_count == 1
        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.event_type == EventType.POSITION_CLOSED

    @pytest.mark.asyncio
    async def test_position_update_short_position(self, bridge):
        """
        GIVEN: SignalR position update with negative size (short)
        WHEN: _on_position_update is called
        THEN: Event published with side="short"
        """
        position_data = [{
            'action': 1,
            'data': {
                'contractId': 'POS123',
                'size': -2,
                'averagePrice': 20100.0,
                'unrealizedPnl': -50.0,
            }
        }]

        await bridge._on_position_update("MNQ", position_data)

        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.data["side"] == "short"
        assert published_event.data["size"] == -2

    @pytest.mark.asyncio
    async def test_position_update_multiple_positions(self, bridge):
        """
        GIVEN: SignalR data with multiple position updates
        WHEN: _on_position_update is called
        THEN: Multiple events are published
        """
        position_data = [
            {
                'action': 1,
                'data': {'contractId': 'POS1', 'size': 1, 'averagePrice': 20100.0, 'unrealizedPnl': 25.0}
            },
            {
                'action': 1,
                'data': {'contractId': 'POS2', 'size': 2, 'averagePrice': 20110.0, 'unrealizedPnl': 50.0}
            }
        ]

        await bridge._on_position_update("MNQ", position_data)

        assert bridge.risk_event_bus.publish.call_count == 2

    @pytest.mark.asyncio
    async def test_position_update_invalid_data_format(self, bridge, caplog):
        """
        GIVEN: SignalR data that is not a list
        WHEN: _on_position_update is called
        THEN: Warning is logged and no events published
        """
        position_data = "not a list"

        await bridge._on_position_update("MNQ", position_data)

        assert "Position update for MNQ not a list" in caplog.text
        assert bridge.risk_event_bus.publish.call_count == 0

    @pytest.mark.asyncio
    async def test_position_update_exception_handling(self, bridge, caplog):
        """
        GIVEN: Position data that causes exception
        WHEN: _on_position_update is called
        THEN: Exception is logged and handled
        """
        position_data = [{
            'action': 1,
            'data': None  # Will cause exception
        }]

        # Should not raise exception
        await bridge._on_position_update("MNQ", position_data)

        assert "Error handling position update" in caplog.text


class TestOrderEventHandling:
    """Test order update event handling."""

    @pytest.fixture
    def bridge(self):
        """Create event bridge with mocks."""
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = AsyncMock(spec=EventBus)
        return EventBridge(mock_suite_manager, mock_event_bus)

    @pytest.mark.asyncio
    async def test_order_placed_event(self, bridge):
        """
        GIVEN: SignalR order update with status='Working'
        WHEN: _on_order_update is called
        THEN: ORDER_PLACED event is published
        """
        order_data = [{
            'action': 1,
            'data': {
                'id': 'ORD123',
                'status': 'Working',
                'side': 'Buy',
                'quantity': 2,
                'price': 20100.0,
                'filledQuantity': 0,
            }
        }]

        await bridge._on_order_update("MNQ", order_data)

        assert bridge.risk_event_bus.publish.call_count == 1
        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.event_type == EventType.ORDER_PLACED
        assert published_event.data["order_id"] == "ORD123"
        assert published_event.data["status"] == "Working"

    @pytest.mark.asyncio
    async def test_order_filled_event(self, bridge):
        """
        GIVEN: SignalR order update with status='Filled'
        WHEN: _on_order_update is called
        THEN: ORDER_FILLED event is published
        """
        order_data = [{
            'action': 1,
            'data': {
                'id': 'ORD123',
                'status': 'Filled',
                'side': 'Buy',
                'quantity': 2,
                'price': 20100.0,
                'filledQuantity': 2,
            }
        }]

        await bridge._on_order_update("MNQ", order_data)

        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.event_type == EventType.ORDER_FILLED
        assert published_event.data["filled_quantity"] == 2

    @pytest.mark.asyncio
    async def test_order_cancelled_event(self, bridge):
        """
        GIVEN: SignalR order update with status='Cancelled'
        WHEN: _on_order_update is called
        THEN: ORDER_CANCELLED event is published
        """
        order_data = [{
            'action': 1,
            'data': {
                'id': 'ORD123',
                'status': 'Cancelled',
                'side': 'Buy',
                'quantity': 2,
                'price': 20100.0,
                'filledQuantity': 0,
            }
        }]

        await bridge._on_order_update("MNQ", order_data)

        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.event_type == EventType.ORDER_CANCELLED

    @pytest.mark.asyncio
    async def test_order_rejected_event(self, bridge):
        """
        GIVEN: SignalR order update with status='Rejected'
        WHEN: _on_order_update is called
        THEN: ORDER_REJECTED event is published
        """
        order_data = [{
            'action': 1,
            'data': {
                'id': 'ORD123',
                'status': 'Rejected',
                'side': 'Buy',
                'quantity': 2,
                'price': 20100.0,
                'filledQuantity': 0,
            }
        }]

        await bridge._on_order_update("MNQ", order_data)

        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.event_type == EventType.ORDER_REJECTED

    @pytest.mark.asyncio
    async def test_order_update_accepted_status(self, bridge):
        """
        GIVEN: SignalR order update with status='Accepted'
        WHEN: _on_order_update is called
        THEN: ORDER_PLACED event is published
        """
        order_data = [{
            'action': 1,
            'data': {
                'id': 'ORD123',
                'status': 'Accepted',
                'side': 'Buy',
                'quantity': 2,
                'price': 20100.0,
                'filledQuantity': 0,
            }
        }]

        await bridge._on_order_update("MNQ", order_data)

        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.event_type == EventType.ORDER_PLACED

    @pytest.mark.asyncio
    async def test_order_update_invalid_data_format(self, bridge, caplog):
        """
        GIVEN: SignalR data that is not a list
        WHEN: _on_order_update is called
        THEN: Warning is logged and no events published
        """
        order_data = "not a list"

        await bridge._on_order_update("MNQ", order_data)

        assert "Order update for MNQ not a list" in caplog.text
        assert bridge.risk_event_bus.publish.call_count == 0

    @pytest.mark.asyncio
    async def test_order_update_multiple_orders(self, bridge):
        """
        GIVEN: SignalR data with multiple order updates
        WHEN: _on_order_update is called
        THEN: Multiple events are published
        """
        order_data = [
            {'action': 1, 'data': {'id': 'ORD1', 'status': 'Working', 'side': 'Buy', 'quantity': 1, 'price': 20100.0, 'filledQuantity': 0}},
            {'action': 1, 'data': {'id': 'ORD2', 'status': 'Filled', 'side': 'Sell', 'quantity': 1, 'price': 20110.0, 'filledQuantity': 1}}
        ]

        await bridge._on_order_update("MNQ", order_data)

        assert bridge.risk_event_bus.publish.call_count == 2


class TestTradeEventHandling:
    """Test trade update event handling."""

    @pytest.fixture
    def bridge(self):
        """Create event bridge with mocks."""
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = AsyncMock(spec=EventBus)
        return EventBridge(mock_suite_manager, mock_event_bus)

    @pytest.mark.asyncio
    async def test_trade_executed_event(self, bridge):
        """
        GIVEN: SignalR trade update
        WHEN: _on_trade_update is called
        THEN: TRADE_EXECUTED event is published
        """
        trade_data = [{
            'action': 1,
            'data': {
                'id': 'TRD123',
                'price': 20100.0,
                'quantity': 2,
                'side': 'Buy',
            }
        }]

        await bridge._on_trade_update("MNQ", trade_data)

        assert bridge.risk_event_bus.publish.call_count == 1
        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert published_event.event_type == EventType.TRADE_EXECUTED
        assert published_event.data["trade_id"] == "TRD123"
        assert published_event.data["price"] == 20100.0
        assert published_event.data["quantity"] == 2

    @pytest.mark.asyncio
    async def test_trade_update_invalid_data_format(self, bridge, caplog):
        """
        GIVEN: SignalR data that is not a list
        WHEN: _on_trade_update is called
        THEN: Warning is logged and no events published
        """
        trade_data = "not a list"

        await bridge._on_trade_update("MNQ", trade_data)

        assert "Trade update for MNQ not a list" in caplog.text
        assert bridge.risk_event_bus.publish.call_count == 0

    @pytest.mark.asyncio
    async def test_trade_update_multiple_trades(self, bridge):
        """
        GIVEN: SignalR data with multiple trade updates
        WHEN: _on_trade_update is called
        THEN: Multiple events are published
        """
        trade_data = [
            {'action': 1, 'data': {'id': 'TRD1', 'price': 20100.0, 'quantity': 1, 'side': 'Buy'}},
            {'action': 1, 'data': {'id': 'TRD2', 'price': 20110.0, 'quantity': 1, 'side': 'Sell'}}
        ]

        await bridge._on_trade_update("MNQ", trade_data)

        assert bridge.risk_event_bus.publish.call_count == 2


class TestAccountEventHandling:
    """Test account update event handling."""

    @pytest.fixture
    def bridge(self):
        """Create event bridge with mocks."""
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = AsyncMock(spec=EventBus)
        return EventBridge(mock_suite_manager, mock_event_bus)

    @pytest.mark.asyncio
    async def test_account_update_logged_not_published(self, bridge):
        """
        GIVEN: SignalR account update
        WHEN: _on_account_update is called
        THEN: Update is logged but NOT published to risk engine
        """
        account_data = [{
            'action': 1,
            'data': {
                'balance': 100000.0,
                'equity': 100250.0,
            }
        }]

        await bridge._on_account_update("MNQ", account_data)

        # Account updates are NOT published to risk engine
        assert bridge.risk_event_bus.publish.call_count == 0

    @pytest.mark.asyncio
    async def test_account_update_invalid_data_format(self, bridge):
        """
        GIVEN: SignalR data that is not a list
        WHEN: _on_account_update is called
        THEN: Silently ignored (no crash)
        """
        account_data = "not a list"

        # Should not raise exception
        await bridge._on_account_update("MNQ", account_data)


class TestInstrumentManagement:
    """Test adding instruments dynamically."""

    @pytest.fixture
    def bridge(self):
        """Create event bridge with mocks."""
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = AsyncMock(spec=EventBus)
        return EventBridge(mock_suite_manager, mock_event_bus)

    @pytest.mark.asyncio
    async def test_add_instrument_while_running(self, bridge):
        """
        GIVEN: Running event bridge
        WHEN: add_instrument is called
        THEN: Bridge subscribes to new suite
        """
        bridge.running = True

        mock_suite = AsyncMock()
        mock_suite.realtime = AsyncMock()
        mock_suite.realtime.add_callback = AsyncMock()

        await bridge.add_instrument("ES", mock_suite)

        # Should have subscribed to 4 callbacks
        assert mock_suite.realtime.add_callback.call_count == 4

    @pytest.mark.asyncio
    async def test_add_instrument_while_not_running(self, bridge):
        """
        GIVEN: Stopped event bridge
        WHEN: add_instrument is called
        THEN: No subscription happens
        """
        bridge.running = False

        mock_suite = AsyncMock()
        mock_suite.realtime = AsyncMock()
        mock_suite.realtime.add_callback = AsyncMock()

        await bridge.add_instrument("ES", mock_suite)

        # Should not subscribe if not running
        assert mock_suite.realtime.add_callback.call_count == 0


class TestEventDataMapping:
    """Test proper data extraction and mapping from SignalR format."""

    @pytest.fixture
    def bridge(self):
        """Create event bridge with mocks."""
        mock_suite_manager = Mock(spec=SuiteManager)
        mock_event_bus = AsyncMock(spec=EventBus)
        return EventBridge(mock_suite_manager, mock_event_bus)

    @pytest.mark.asyncio
    async def test_position_data_includes_timestamp(self, bridge):
        """
        GIVEN: Position update
        WHEN: Event is published
        THEN: Timestamp is included in event data
        """
        position_data = [{
            'action': 1,
            'data': {
                'contractId': 'POS123',
                'size': 2,
                'averagePrice': 20100.0,
                'unrealizedPnl': 50.0,
            }
        }]

        await bridge._on_position_update("MNQ", position_data)

        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert "timestamp" in published_event.data
        assert published_event.data["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_position_data_includes_raw_data(self, bridge):
        """
        GIVEN: Position update
        WHEN: Event is published
        THEN: Raw SignalR data is preserved
        """
        position_data = [{
            'action': 1,
            'data': {
                'contractId': 'POS123',
                'size': 2,
                'averagePrice': 20100.0,
                'unrealizedPnl': 50.0,
                'customField': 'custom_value',
            }
        }]

        await bridge._on_position_update("MNQ", position_data)

        published_event = bridge.risk_event_bus.publish.call_args[0][0]
        assert "raw_data" in published_event.data
        assert published_event.data["raw_data"]["customField"] == "custom_value"
