"""
Unit tests for MarketDataHandler module.

Tests market data handling, quote updates, and status bar in isolation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from risk_manager.integrations.sdk.market_data import MarketDataHandler
from risk_manager.core.events import EventBus, EventType


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_pnl_calculator():
    """Create mock PnL calculator."""
    calc = Mock()
    calc.update_quote = Mock()
    calc.get_positions_by_symbol = Mock(return_value=[])
    calc.has_significant_pnl_change = Mock(return_value=False)
    calc.calculate_unrealized_pnl = Mock(return_value=0.0)
    calc.calculate_total_unrealized_pnl = Mock(return_value=0.0)
    return calc


@pytest.fixture
def event_bus():
    """Create real EventBus for testing."""
    return EventBus()


@pytest.fixture
def handler(mock_pnl_calculator, event_bus):
    """Create MarketDataHandler instance."""
    return MarketDataHandler(
        pnl_calculator=mock_pnl_calculator,
        event_bus=event_bus,
        instruments=["MNQ", "ES"]
    )


@pytest.fixture
def mock_quote_event():
    """Create mock quote update event."""
    event = Mock()
    event.data = {
        'symbol': 'F.US.MNQ',
        'bid': 21500.00,
        'ask': 21500.75,
        'last_price': 21500.25,
        'timestamp': 1234567890,
    }
    return event


# ============================================================================
# Test: Initialization
# ============================================================================

def test_initialization(handler, mock_pnl_calculator, event_bus):
    """Test that MarketDataHandler initializes correctly."""
    assert handler.pnl_calculator == mock_pnl_calculator
    assert handler.event_bus == event_bus
    assert handler.instruments == ["MNQ", "ES"]
    assert handler._client is None
    assert handler._suite is None
    assert handler._running is False
    assert handler._status_bar_task is None


def test_set_client(handler):
    """Test that set_client stores SDK client reference."""
    mock_client = Mock()
    handler.set_client(mock_client)

    assert handler._client is mock_client


def test_set_suite(handler):
    """Test that set_suite stores SDK suite reference."""
    mock_suite = Mock()
    handler.set_suite(mock_suite)

    assert handler._suite is mock_suite


# ============================================================================
# Test: Quote Update Handling
# ============================================================================

@pytest.mark.asyncio
async def test_handle_quote_update_processes_valid_quote(handler, mock_pnl_calculator, mock_quote_event):
    """Test that valid quote updates are processed correctly."""
    await handler.handle_quote_update(mock_quote_event)

    # Should have updated P&L calculator with market price
    mock_pnl_calculator.update_quote.assert_called_once()
    call_args = mock_pnl_calculator.update_quote.call_args
    assert call_args[0][0] == "MNQ"  # Symbol (F.US. prefix stripped)
    assert call_args[0][1] == 21500.25  # last_price


@pytest.mark.asyncio
async def test_handle_quote_update_uses_midpoint_when_no_last_price(handler, mock_pnl_calculator):
    """Test that bid/ask midpoint is used when last_price is missing."""
    event = Mock()
    event.data = {
        'symbol': 'F.US.ES',
        'bid': 5200.00,
        'ask': 5200.50,
        'last_price': 0.0,  # No last price
    }

    await handler.handle_quote_update(event)

    # Should use midpoint: (5200.00 + 5200.50) / 2 = 5200.25
    mock_pnl_calculator.update_quote.assert_called_once()
    call_args = mock_pnl_calculator.update_quote.call_args
    assert call_args[0][0] == "ES"
    assert call_args[0][1] == 5200.25


@pytest.mark.asyncio
async def test_handle_quote_update_ignores_invalid_event(handler, mock_pnl_calculator):
    """Test that invalid quote events are ignored gracefully."""
    # Event with no data attribute
    event = Mock(spec=[])  # No attributes

    await handler.handle_quote_update(event)

    # Should not have called update_quote
    mock_pnl_calculator.update_quote.assert_not_called()


@pytest.mark.asyncio
async def test_handle_quote_update_ignores_invalid_prices(handler, mock_pnl_calculator):
    """Test that quotes with no valid prices are ignored."""
    event = Mock()
    event.data = {
        'symbol': 'F.US.MNQ',
        'bid': 0.0,
        'ask': 0.0,
        'last_price': 0.0,
    }

    await handler.handle_quote_update(event)

    # Should not have called update_quote
    mock_pnl_calculator.update_quote.assert_not_called()


@pytest.mark.asyncio
async def test_handle_quote_update_publishes_market_data_event(handler, event_bus, mock_quote_event):
    """Test that quote updates publish MARKET_DATA_UPDATED event."""
    events_received = []

    async def capture_event(event):
        events_received.append(event)

    event_bus.subscribe(EventType.MARKET_DATA_UPDATED, capture_event)

    await handler.handle_quote_update(mock_quote_event)

    # Should have published one event
    assert len(events_received) == 1
    event = events_received[0]
    assert event.event_type == EventType.MARKET_DATA_UPDATED
    assert event.data['symbol'] == "MNQ"
    assert event.data['price'] == 21500.25


@pytest.mark.asyncio
async def test_handle_quote_update_publishes_pnl_update_on_significant_change(
    handler, event_bus, mock_pnl_calculator, mock_quote_event
):
    """Test that significant P&L changes trigger UNREALIZED_PNL_UPDATE event."""
    # Mock P&L calculator to return a position with significant change
    mock_pnl_calculator.get_positions_by_symbol.return_value = ["CON.F.US.MNQ.Z25"]
    mock_pnl_calculator.has_significant_pnl_change.return_value = True
    mock_pnl_calculator.calculate_unrealized_pnl.return_value = 150.00

    # Set client for account_id
    mock_client = Mock()
    mock_client.account_info.id = "TEST_ACCOUNT"
    handler.set_client(mock_client)

    events_received = []

    async def capture_event(event):
        events_received.append(event)

    event_bus.subscribe(EventType.UNREALIZED_PNL_UPDATE, capture_event)

    await handler.handle_quote_update(mock_quote_event)

    # Should have published P&L update event
    pnl_events = [e for e in events_received if e.event_type == EventType.UNREALIZED_PNL_UPDATE]
    assert len(pnl_events) == 1
    event = pnl_events[0]
    assert event.data['account_id'] == "TEST_ACCOUNT"
    assert event.data['symbol'] == "MNQ"
    assert event.data['unrealized_pnl'] == 150.00


# ============================================================================
# Test: Other Market Data Handlers
# ============================================================================

@pytest.mark.asyncio
async def test_handle_data_update_logs_debug(handler):
    """Test that handle_data_update logs data for debugging."""
    data = {"some": "data"}

    # Should not raise exceptions
    await handler.handle_data_update(data)


@pytest.mark.asyncio
async def test_handle_trade_tick_updates_pnl_from_dict(handler, mock_pnl_calculator):
    """Test that trade tick updates P&L calculator when data is a dict."""
    data = {
        'symbol': 'MNQ',
        'price': 21550.00,
    }

    await handler.handle_trade_tick(data)

    # Should have updated P&L calculator
    mock_pnl_calculator.update_quote.assert_called_once_with('MNQ', 21550.00)


@pytest.mark.asyncio
async def test_handle_new_bar_updates_pnl_from_close_price(handler, mock_pnl_calculator):
    """Test that new bar updates P&L calculator with close price."""
    data = {
        'symbol': 'ES',
        'close': 5205.50,
    }

    await handler.handle_new_bar(data)

    # Should have updated P&L calculator with close price
    mock_pnl_calculator.update_quote.assert_called_once_with('ES', 5205.50)


# ============================================================================
# Test: Status Bar Lifecycle
# ============================================================================

@pytest.mark.asyncio
async def test_start_status_bar_creates_task(handler):
    """Test that start_status_bar creates a background task."""
    await handler.start_status_bar()

    # Task should be created
    assert handler._status_bar_task is not None
    assert not handler._status_bar_task.done()
    assert handler._running is True

    # Cleanup
    await handler.stop_status_bar()


@pytest.mark.asyncio
async def test_stop_status_bar_cancels_task(handler):
    """Test that stop_status_bar cancels the background task."""
    await handler.start_status_bar()

    # Give task a moment to start
    await asyncio.sleep(0.1)

    await handler.stop_status_bar()

    # Task should be cancelled
    assert handler._running is False
    assert handler._status_bar_task.done()


@pytest.mark.asyncio
async def test_start_status_bar_twice_warns(handler):
    """Test that starting status bar twice logs a warning."""
    await handler.start_status_bar()

    # Try to start again (should warn, not create second task)
    await handler.start_status_bar()

    # Still only one task
    assert handler._status_bar_task is not None

    # Cleanup
    await handler.stop_status_bar()


@pytest.mark.asyncio
async def test_status_bar_polls_prices(handler, mock_pnl_calculator):
    """Test that status bar task polls prices from instruments."""
    # Create mock suite with instrument
    mock_instrument = Mock()
    mock_instrument.last_price = 21500.00

    mock_suite = Mock()
    mock_suite.get = Mock(return_value=mock_instrument)

    handler.set_suite(mock_suite)

    # Start status bar
    await handler.start_status_bar()

    # Wait for at least one poll cycle (0.5s + margin)
    await asyncio.sleep(0.7)

    # Stop status bar
    await handler.stop_status_bar()

    # Should have polled prices
    mock_suite.get.assert_called()
    mock_pnl_calculator.update_quote.assert_called()


@pytest.mark.asyncio
async def test_status_bar_calculates_total_pnl(handler, mock_pnl_calculator):
    """Test that status bar calculates total unrealized P&L."""
    mock_pnl_calculator.calculate_total_unrealized_pnl.return_value = 250.00

    # Start status bar
    await handler.start_status_bar()

    # Wait for one update cycle
    await asyncio.sleep(0.7)

    # Stop status bar
    await handler.stop_status_bar()

    # Should have calculated total P&L
    mock_pnl_calculator.calculate_total_unrealized_pnl.assert_called()


# ============================================================================
# Test: Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_handle_quote_update_handles_exceptions(handler, mock_pnl_calculator):
    """Test that exceptions in quote handling don't crash the handler."""
    # Make update_quote raise an exception
    mock_pnl_calculator.update_quote.side_effect = Exception("Test error")

    event = Mock()
    event.data = {
        'symbol': 'F.US.MNQ',
        'bid': 21500.00,
        'ask': 21500.75,
        'last_price': 21500.25,
    }

    # Should not raise exception
    await handler.handle_quote_update(event)


@pytest.mark.asyncio
async def test_status_bar_handles_poll_errors(handler):
    """Test that status bar continues running despite poll errors."""
    # Create mock suite that raises errors
    mock_suite = Mock()
    mock_suite.get.side_effect = Exception("Poll error")

    handler.set_suite(mock_suite)

    # Start status bar
    await handler.start_status_bar()

    # Wait for a few poll cycles
    await asyncio.sleep(1.5)

    # Should still be running
    assert handler._running is True

    # Stop status bar
    await handler.stop_status_bar()


# ============================================================================
# Summary
# ============================================================================

def test_market_data_handler_complete_workflow(handler, mock_pnl_calculator, mock_quote_event):
    """
    Integration test: Complete workflow from initialization to quote processing.
    """
    # 1. Initialize (already done in fixture)
    assert handler._client is None

    # 2. Set SDK references
    mock_client = Mock()
    mock_suite = Mock()
    handler.set_client(mock_client)
    handler.set_suite(mock_suite)

    assert handler._client is mock_client
    assert handler._suite is mock_suite

    # 3. Process quote update
    import asyncio
    asyncio.run(handler.handle_quote_update(mock_quote_event))

    # Should have updated P&L calculator
    mock_pnl_calculator.update_quote.assert_called_once()
