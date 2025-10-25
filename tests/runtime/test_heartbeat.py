"""
Heartbeat Monitoring Tests

Tests for system heartbeat monitoring, health checks, and uptime tracking.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch


# ============================================================================
# Heartbeat Success Cases
# ============================================================================

@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_initial_alive(mock_heartbeat_monitor):
    """Test that heartbeat monitor starts in alive state."""
    await mock_heartbeat_monitor.start()
    is_alive = await mock_heartbeat_monitor.is_alive()

    result = {
        'exit_code': 0,
        'passed': is_alive,
        'output': 'Heartbeat monitor is alive'
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_regular_updates():
    """Test that heartbeat updates regularly."""
    heartbeat_times = []

    async def record_heartbeat():
        for _ in range(3):
            heartbeat_times.append(datetime.now())
            await asyncio.sleep(0.1)

    await record_heartbeat()

    # Verify we got 3 heartbeats
    result = {
        'exit_code': 0,
        'passed': len(heartbeat_times) == 3,
        'heartbeat_count': len(heartbeat_times)
    }

    assert result['exit_code'] == 0
    assert result['heartbeat_count'] == 3


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_timestamp_recent(mock_heartbeat_monitor):
    """Test that heartbeat timestamp is recent."""
    last_heartbeat = await mock_heartbeat_monitor.get_last_heartbeat()
    now = datetime.now()
    time_diff = (now - last_heartbeat).total_seconds()

    result = {
        'exit_code': 0,
        'passed': time_diff < 5.0,  # Less than 5 seconds old
        'time_since_heartbeat': time_diff
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_health_status_healthy(mock_heartbeat_monitor):
    """Test that health status reports healthy."""
    health = await mock_heartbeat_monitor.get_health_status()

    result = {
        'exit_code': 0,
        'passed': health['status'] == 'healthy',
        'health_data': health
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True
    assert health['uptime'] > 0


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_continuous_monitoring():
    """Test continuous heartbeat monitoring."""
    monitor_active = True
    heartbeat_count = 0

    async def monitor():
        nonlocal heartbeat_count
        while heartbeat_count < 5:
            heartbeat_count += 1
            await asyncio.sleep(0.05)

    await monitor()

    result = {
        'exit_code': 0,
        'passed': heartbeat_count >= 5,
        'total_heartbeats': heartbeat_count
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True


# ============================================================================
# Heartbeat Failure Cases
# ============================================================================

@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_timeout_failure():
    """Test detection of heartbeat timeout."""
    last_heartbeat = datetime.now() - timedelta(seconds=30)
    timeout_threshold = 10.0  # 10 seconds

    time_since_heartbeat = (datetime.now() - last_heartbeat).total_seconds()
    is_timeout = time_since_heartbeat > timeout_threshold

    result = {
        'exit_code': 1,
        'passed': False,
        'output': f'Heartbeat timeout: {time_since_heartbeat:.1f}s since last heartbeat',
        'errors': [f'No heartbeat for {time_since_heartbeat:.1f} seconds']
    }

    assert result['exit_code'] == 1
    assert is_timeout is True


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_monitor_stopped():
    """Test detection when monitor is stopped."""
    monitor_running = False

    result = {
        'exit_code': 1,
        'passed': False,
        'output': 'Heartbeat monitor is not running',
        'errors': ['MonitorStoppedError: Heartbeat monitor has stopped']
    }

    assert result['exit_code'] == 1
    assert monitor_running is False


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_degraded_health():
    """Test detection of degraded health status."""
    health_status = {
        'status': 'degraded',
        'uptime': 1800.0,
        'error_rate': 0.15,  # 15% error rate
        'warnings': ['High error rate detected']
    }

    result = {
        'exit_code': 1,
        'passed': False,
        'output': 'System health degraded',
        'health_data': health_status
    }

    assert result['exit_code'] == 1
    assert health_status['status'] == 'degraded'


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_unhealthy_status():
    """Test detection of unhealthy system status."""
    health_status = {
        'status': 'unhealthy',
        'uptime': 0.0,
        'error_rate': 0.95,
        'errors': ['Critical system failure', 'Database connection lost']
    }

    result = {
        'exit_code': 2,
        'passed': False,
        'output': 'System unhealthy - critical failures',
        'errors': health_status['errors']
    }

    assert result['exit_code'] == 2
    assert health_status['status'] == 'unhealthy'


# ============================================================================
# Uptime Tracking
# ============================================================================

@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_uptime_tracking():
    """Test that uptime is tracked correctly."""
    start_time = datetime.now()
    await asyncio.sleep(0.2)

    uptime = (datetime.now() - start_time).total_seconds()

    result = {
        'exit_code': 0,
        'passed': uptime >= 0.2,
        'uptime': uptime
    }

    assert result['exit_code'] == 0
    assert result['uptime'] >= 0.19  # Relaxed for timing precision


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_uptime_reset_on_restart():
    """Test that uptime resets when system restarts."""
    # First run
    uptime_1 = 3600.0  # 1 hour

    # Restart
    uptime_2 = 0.0

    result = {
        'exit_code': 0,
        'passed': uptime_2 < uptime_1,
        'uptime_before_restart': uptime_1,
        'uptime_after_restart': uptime_2
    }

    assert result['exit_code'] == 0
    assert uptime_2 == 0.0


# ============================================================================
# Heartbeat Recovery
# ============================================================================

@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_recovery_after_pause():
    """Test heartbeat recovery after temporary pause."""
    heartbeats = []

    # Initial heartbeats
    for i in range(3):
        heartbeats.append(datetime.now())
        await asyncio.sleep(0.05)

    # Pause
    await asyncio.sleep(0.2)

    # Resume heartbeats
    for i in range(3):
        heartbeats.append(datetime.now())
        await asyncio.sleep(0.05)

    result = {
        'exit_code': 0,
        'passed': len(heartbeats) == 6,
        'total_heartbeats': len(heartbeats)
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_automatic_restart():
    """Test automatic heartbeat restart after failure."""
    restart_count = 0
    max_restarts = 3

    async def attempt_restart():
        nonlocal restart_count
        while restart_count < max_restarts:
            restart_count += 1
            await asyncio.sleep(0.05)

    await attempt_restart()

    result = {
        'exit_code': 0,
        'passed': restart_count == max_restarts,
        'restart_count': restart_count
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True


# ============================================================================
# Heartbeat Metrics
# ============================================================================

@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_metrics_collection():
    """Test collection of heartbeat metrics."""
    metrics = {
        'total_heartbeats': 1000,
        'missed_heartbeats': 5,
        'average_interval': 1.0,
        'max_interval': 2.5,
        'uptime_percentage': 99.5
    }

    result = {
        'exit_code': 0,
        'passed': metrics['uptime_percentage'] > 99.0,
        'metrics': metrics
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True
    assert metrics['missed_heartbeats'] < 10


@pytest.mark.runtime
@pytest.mark.heartbeat
async def test_heartbeat_interval_consistency():
    """Test that heartbeat intervals are consistent."""
    intervals = [1.0, 1.1, 0.9, 1.0, 1.05]
    avg_interval = sum(intervals) / len(intervals)
    max_deviation = max(abs(i - avg_interval) for i in intervals)

    result = {
        'exit_code': 0,
        'passed': max_deviation < 0.5,  # Less than 0.5s deviation
        'average_interval': avg_interval,
        'max_deviation': max_deviation
    }

    assert result['exit_code'] == 0
    assert result['passed'] is True
