"""
Runtime Test Configuration & Fixtures

Provides fixtures and utilities specific to runtime reliability testing.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime


# ============================================================================
# Runtime Environment Fixtures
# ============================================================================

@pytest.fixture
def dry_run_env():
    """Enable DRY_RUN mode for testing."""
    old_value = os.environ.get('DRY_RUN')
    os.environ['DRY_RUN'] = '1'
    yield
    if old_value is None:
        os.environ.pop('DRY_RUN', None)
    else:
        os.environ['DRY_RUN'] = old_value


@pytest.fixture
def debug_env():
    """Enable DEBUG mode for testing."""
    old_value = os.environ.get('DEBUG')
    os.environ['DEBUG'] = '1'
    yield
    if old_value is None:
        os.environ.pop('DEBUG', None)
    else:
        os.environ['DEBUG'] = old_value


@pytest.fixture
def runtime_config():
    """Runtime configuration for testing."""
    return {
        'heartbeat_interval': 1.0,  # 1 second for testing
        'smoke_test_timeout': 5.0,
        'post_condition_timeout': 3.0,
        'max_retries': 3,
        'enable_monitoring': True
    }


# ============================================================================
# Mock Runtime Components
# ============================================================================

@pytest.fixture
def mock_heartbeat_monitor():
    """Mock heartbeat monitoring system."""
    monitor = AsyncMock()
    monitor.is_alive = AsyncMock(return_value=True)
    monitor.get_last_heartbeat = AsyncMock(return_value=datetime.now())
    monitor.get_health_status = AsyncMock(return_value={'status': 'healthy', 'uptime': 100.0})
    monitor.start = AsyncMock()
    monitor.stop = AsyncMock()
    return monitor


@pytest.fixture
def mock_smoke_test_runner():
    """Mock smoke test runner."""
    runner = AsyncMock()
    runner.run_all_tests = AsyncMock(return_value={'passed': True, 'failed_count': 0})
    runner.run_test = AsyncMock(return_value={'passed': True, 'duration': 0.5})
    return runner


@pytest.fixture
def mock_post_condition_checker():
    """Mock post-condition validation system."""
    checker = AsyncMock()
    checker.validate_all = AsyncMock(return_value={'valid': True, 'violations': []})
    checker.validate_condition = AsyncMock(return_value=True)
    return checker


# ============================================================================
# Runtime State Fixtures
# ============================================================================

@pytest.fixture
def healthy_runtime_state():
    """Sample healthy runtime state."""
    return {
        'status': 'running',
        'health': 'healthy',
        'uptime': 3600.0,
        'last_heartbeat': datetime.now().isoformat(),
        'error_count': 0,
        'warning_count': 0,
        'active_rules': 5,
        'monitored_accounts': 1
    }


@pytest.fixture
def degraded_runtime_state():
    """Sample degraded runtime state."""
    return {
        'status': 'running',
        'health': 'degraded',
        'uptime': 1800.0,
        'last_heartbeat': datetime.now().isoformat(),
        'error_count': 3,
        'warning_count': 10,
        'active_rules': 5,
        'monitored_accounts': 1
    }


@pytest.fixture
def failed_runtime_state():
    """Sample failed runtime state."""
    return {
        'status': 'stopped',
        'health': 'unhealthy',
        'uptime': 0.0,
        'last_heartbeat': None,
        'error_count': 50,
        'warning_count': 20,
        'active_rules': 0,
        'monitored_accounts': 0
    }


# ============================================================================
# Test Result Fixtures
# ============================================================================

@pytest.fixture
def successful_test_result():
    """Sample successful test result."""
    return {
        'exit_code': 0,
        'passed': True,
        'duration': 1.5,
        'output': 'All tests passed',
        'errors': []
    }


@pytest.fixture
def failed_test_result():
    """Sample failed test result."""
    return {
        'exit_code': 1,
        'passed': False,
        'duration': 2.0,
        'output': 'Test failed: Assertion error',
        'errors': ['AssertionError: Expected True, got False']
    }


@pytest.fixture
def timeout_test_result():
    """Sample timeout test result."""
    return {
        'exit_code': 2,
        'passed': False,
        'duration': 10.0,
        'output': 'Test timed out',
        'errors': ['TimeoutError: Test exceeded maximum duration']
    }


# ============================================================================
# Async Helpers
# ============================================================================

@pytest.fixture
async def async_test_context():
    """Provides async test context with cleanup."""
    context = {
        'tasks': [],
        'cleanup_handlers': []
    }

    yield context

    # Cleanup all tasks
    for task in context['tasks']:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    # Run cleanup handlers
    for handler in context['cleanup_handlers']:
        await handler()


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with runtime test markers."""
    config.addinivalue_line(
        "markers", "runtime: mark test as a runtime reliability test"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as a smoke test"
    )
    config.addinivalue_line(
        "markers", "heartbeat: mark test as a heartbeat monitoring test"
    )
    config.addinivalue_line(
        "markers", "post_condition: mark test as a post-condition validation test"
    )
    config.addinivalue_line(
        "markers", "dry_run: mark test as a dry-run mode test"
    )
    config.addinivalue_line(
        "markers", "async_debug: mark test as an async debugging test"
    )


# ============================================================================
# Helper Functions
# ============================================================================

def assert_exit_code(result: Dict[str, Any], expected_code: int) -> None:
    """Assert that result has expected exit code."""
    assert 'exit_code' in result, "Result missing exit_code"
    assert result['exit_code'] == expected_code, \
        f"Expected exit code {expected_code}, got {result['exit_code']}"


def assert_test_passed(result: Dict[str, Any]) -> None:
    """Assert that test passed successfully."""
    assert_exit_code(result, 0)
    assert result.get('passed', False), "Test did not pass"


def assert_test_failed(result: Dict[str, Any]) -> None:
    """Assert that test failed as expected."""
    assert result['exit_code'] in [1, 2], "Test should have failed"
    assert not result.get('passed', True), "Test should not have passed"


async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
    """Wait for a condition to become true with timeout."""
    elapsed = 0.0
    while elapsed < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(interval)
        elapsed += interval
    return False
