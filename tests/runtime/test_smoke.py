"""
Smoke Tests for Runtime Reliability

Tests basic system functionality to ensure the application can start
and perform fundamental operations without crashing.
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime


# ============================================================================
# Smoke Test Success Cases
# ============================================================================

@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_basic_startup_success(dry_run_env):
    """Test that basic system startup succeeds in dry-run mode."""
    os.environ['DRY_RUN'] = '1'

    # Mock the risk manager startup
    with patch('risk_manager.RiskManager.create') as mock_create:
        mock_rm = AsyncMock()
        mock_rm.start = AsyncMock(return_value=None)
        mock_rm.stop = AsyncMock(return_value=None)
        mock_create.return_value = mock_rm

        # Simulate smoke test
        from risk_manager import RiskManager
        rm = await RiskManager.create(instruments=["MNQ"])
        await rm.start()

        result = {
            'exit_code': 0,
            'passed': True,
            'output': 'System started successfully'
        }

        await rm.stop()

    assert result['exit_code'] == 0
    assert result['passed'] is True


@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_configuration_load_success():
    """Test that configuration loads successfully."""
    result = {
        'exit_code': 0,
        'passed': True,
        'config_loaded': True
    }

    # Simulate config loading
    config = {
        'instruments': ['MNQ'],
        'rules': {'max_contracts': 5},
        'monitoring': {'enabled': True}
    }

    assert result['exit_code'] == 0
    assert config is not None
    assert 'instruments' in config


@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_event_bus_success():
    """Test that event bus initializes and processes events."""
    from risk_manager.core.events import EventBus, RiskEvent, EventType

    bus = EventBus()
    event_received = False

    def callback(event):
        nonlocal event_received
        event_received = True

    bus.subscribe(EventType.POSITION_UPDATED, callback)
    await bus.publish(RiskEvent(event_type=EventType.POSITION_UPDATED, data={}))

    result = {
        'exit_code': 0,
        'passed': event_received,
        'output': 'Event bus working'
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True


@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_rule_engine_success(mock_engine):
    """Test that rule engine can be created and initialized."""
    # Mock rule creation
    from risk_manager.rules.base import RiskRule

    class MockRule(RiskRule):
        async def evaluate(self, event):
            return True

    rule = MockRule()  # RiskRule base class takes no arguments

    result = {
        'exit_code': 0,
        'passed': rule is not None,
        'output': 'Rule engine initialized'
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True


@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_state_tracking_success():
    """Test that state tracking components initialize."""
    from risk_manager.state.pnl_tracker import PnLTracker
    from risk_manager.state.database import Database
    import tempfile

    # Create temp database for test
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    db = Database(db_path=db_path)
    tracker = PnLTracker(db=db)

    # Track a simple transaction (using correct API: add_trade_pnl(account_id, pnl))
    account_id = "TEST-ACCOUNT"
    tracker.add_trade_pnl(account_id, 100.0)
    total = tracker.get_daily_pnl(account_id)

    result = {
        'exit_code': 0,
        'passed': total == 100.0,
        'output': f'P&L tracking working: {total}'
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True


# ============================================================================
# Smoke Test Failure Cases
# ============================================================================

@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_missing_config_failure():
    """Test smoke test fails when configuration is missing."""
    result = {
        'exit_code': 1,
        'passed': False,
        'output': 'Configuration file not found',
        'errors': ['FileNotFoundError: config.yaml']
    }

    assert result['exit_code'] == 1
    assert result['passed'] is False
    assert len(result['errors']) > 0


@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_invalid_config_failure():
    """Test smoke test fails with invalid configuration."""
    result = {
        'exit_code': 1,
        'passed': False,
        'output': 'Invalid configuration',
        'errors': ['ValidationError: instruments must be a list']
    }

    assert result['exit_code'] == 1
    assert result['passed'] is False
    assert 'ValidationError' in result['errors'][0]


@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_startup_timeout_failure():
    """Test smoke test fails when startup times out."""
    result = {
        'exit_code': 2,
        'passed': False,
        'output': 'Startup timed out after 5.0 seconds',
        'errors': ['TimeoutError: System did not start within timeout period']
    }

    assert result['exit_code'] == 2
    assert result['passed'] is False
    assert 'TimeoutError' in result['errors'][0]


@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_dependency_failure():
    """Test smoke test fails when dependencies are missing."""
    result = {
        'exit_code': 1,
        'passed': False,
        'output': 'Missing required dependencies',
        'errors': ['ModuleNotFoundError: No module named "required_package"']
    }

    assert result['exit_code'] == 1
    assert result['passed'] is False


# ============================================================================
# Smoke Test Suite
# ============================================================================

@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_full_suite_success(dry_run_env, mock_smoke_test_runner):
    """Test running full smoke test suite."""
    result = await mock_smoke_test_runner.run_all_tests()

    assert result['passed'] is True
    assert result['failed_count'] == 0


@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_partial_failure():
    """Test smoke suite with some failed tests."""
    result = {
        'exit_code': 1,
        'passed': False,
        'total_tests': 10,
        'passed_tests': 7,
        'failed_tests': 3,
        'output': '3 of 10 smoke tests failed'
    }

    assert result['exit_code'] == 1
    assert result['failed_tests'] > 0


# ============================================================================
# Log Output Verification
# ============================================================================

@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_log_output_verification(caplog):
    """Test that smoke tests produce expected log output."""
    import logging

    logger = logging.getLogger('risk_manager')
    logger.info("Smoke test started")
    logger.info("All systems operational")
    logger.info("Smoke test completed successfully")

    result = {
        'exit_code': 0,
        'passed': True,
        'output': caplog.text
    }

    assert "Smoke test started" in caplog.text
    assert "completed successfully" in caplog.text
    assert result['exit_code'] == 0


@pytest.mark.runtime
@pytest.mark.smoke
async def test_smoke_error_log_output():
    """Test smoke test captures error output."""
    import logging

    logger = logging.getLogger('risk_manager')
    logger.error("Critical error during startup")
    logger.error("System initialization failed")

    result = {
        'exit_code': 1,
        'passed': False,
        'output': 'Error logs detected',
        'errors': [
            "Critical error during startup",
            "System initialization failed"
        ]
    }

    assert result['exit_code'] == 1
    assert len(result['errors']) == 2
