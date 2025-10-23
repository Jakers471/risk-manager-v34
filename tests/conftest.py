"""
Pytest Configuration & Shared Fixtures

This file provides fixtures used across all tests.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from typing import AsyncGenerator

# Import core components for mocking
from risk_manager.core.events import RiskEvent, EventType


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_engine():
    """Mock RiskEngine for unit tests."""
    engine = AsyncMock()
    engine.account_id = "TEST-ACCOUNT-123"
    engine.suite_manager = AsyncMock()
    engine.lockout_manager = AsyncMock()
    engine.event_bus = AsyncMock()
    return engine


@pytest.fixture
def mock_suite():
    """Mock TradingSuite (SDK) for testing."""
    suite = AsyncMock()
    suite.close_position = AsyncMock()
    suite.cancel_all_orders = AsyncMock()
    suite.place_order = AsyncMock()

    # Mock stats
    mock_stats = Mock()
    mock_stats.account_id = "TEST-ACCOUNT-123"
    mock_stats.balance = 100000.0
    mock_stats.realized_pl = 0.0
    mock_stats.unrealized_pl = 0.0
    suite.get_stats = AsyncMock(return_value=mock_stats)

    # Mock positions
    suite.get_positions = AsyncMock(return_value=[])

    # Mock orders
    suite.get_orders = AsyncMock(return_value=[])

    return suite


@pytest.fixture
def mock_suite_manager():
    """Mock SuiteManager for testing."""
    manager = AsyncMock()
    manager.get_suite = AsyncMock()
    manager.get_all_suites = AsyncMock(return_value={})
    return manager


# ============================================================================
# Sample Event Fixtures
# ============================================================================

@pytest.fixture
def sample_trade_event():
    """Sample trade event for testing."""
    return RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={
            "symbol": "MNQ",
            "side": "Buy",
            "quantity": 1,
            "price": 20125.0,
            "realized_pnl": -12.50,
            "timestamp": datetime.now().isoformat()
        }
    )


@pytest.fixture
def sample_position_event():
    """Sample position update event for testing."""
    return RiskEvent(
        type=EventType.POSITION_UPDATED,
        data={
            "symbol": "MNQ",
            "quantity": 2,
            "average_price": 20100.0,
            "current_price": 20125.0,
            "unrealized_pnl": 50.0,
            "timestamp": datetime.now().isoformat()
        }
    )


@pytest.fixture
def sample_order_event():
    """Sample order event for testing."""
    return RiskEvent(
        type=EventType.ORDER_UPDATED,
        data={
            "symbol": "MNQ",
            "side": "Buy",
            "quantity": 1,
            "price": 20125.0,
            "status": "Filled",
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_position():
    """Sample position data."""
    return {
        "symbol": "MNQ",
        "quantity": 2,
        "average_price": 20100.0,
        "current_price": 20125.0,
        "unrealized_pnl": 50.0
    }


@pytest.fixture
def losing_trade():
    """Sample losing trade."""
    return RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={
            "symbol": "MNQ",
            "realized_pnl": -150.0,  # Loss
            "timestamp": datetime.now().isoformat()
        }
    )


@pytest.fixture
def winning_trade():
    """Sample winning trade."""
    return RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={
            "symbol": "MNQ",
            "realized_pnl": 100.0,  # Profit
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture
async def risk_manager():
    """
    Fully configured RiskManager for integration tests.

    WARNING: This creates a real RiskManager instance.
    Use only for integration tests, not unit tests.
    """
    from risk_manager import RiskManager

    rm = await RiskManager.create(
        instruments=["MNQ"],
        rules={"max_contracts": 5}
    )

    yield rm

    # Cleanup
    await rm.stop()


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (slow, requires SDK)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# ============================================================================
# Helper Functions
# ============================================================================

def create_trade_event(symbol: str = "MNQ", pnl: float = -12.50) -> RiskEvent:
    """Create a trade event with custom P&L."""
    return RiskEvent(
        type=EventType.TRADE_EXECUTED,
        data={
            "symbol": symbol,
            "realized_pnl": pnl,
            "timestamp": datetime.now().isoformat()
        }
    )


def create_position_event(symbol: str = "MNQ", quantity: int = 2) -> RiskEvent:
    """Create a position event with custom quantity."""
    return RiskEvent(
        type=EventType.POSITION_UPDATED,
        data={
            "symbol": symbol,
            "quantity": quantity,
            "unrealized_pnl": 50.0,
            "timestamp": datetime.now().isoformat()
        }
    )
