"""
Helper functions for Windows Service control in Admin CLI.

Provides utilities for querying service status, process information,
and connection testing.
"""

from datetime import datetime
from typing import Optional, Dict, Any


def get_service_info() -> Dict[str, Any]:
    """
    Get comprehensive service information.

    Returns:
        Dictionary containing service status, process info, and monitoring stats
    """
    import win32serviceutil
    import win32service

    try:
        # Query service status
        status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
        current_state = status[1]

        state_name = {
            win32service.SERVICE_STOPPED: "STOPPED",
            win32service.SERVICE_START_PENDING: "STARTING",
            win32service.SERVICE_STOP_PENDING: "STOPPING",
            win32service.SERVICE_RUNNING: "RUNNING",
            win32service.SERVICE_CONTINUE_PENDING: "CONTINUING",
            win32service.SERVICE_PAUSE_PENDING: "PAUSING",
            win32service.SERVICE_PAUSED: "PAUSED",
        }.get(current_state, "UNKNOWN")

        info = {
            "installed": True,
            "state": current_state,
            "state_name": state_name,
            "running": current_state == win32service.SERVICE_RUNNING,
        }

        # Get process info if running
        if current_state == win32service.SERVICE_RUNNING:
            process_info = get_process_info()
            info.update(process_info)

        return info

    except Exception:
        # Service not installed
        return {
            "installed": False,
            "state": None,
            "state_name": "NOT_INSTALLED",
            "running": False,
        }


def get_process_info() -> Dict[str, Any]:
    """
    Get process information for running service.

    Returns:
        Dictionary with PID, CPU, memory, uptime
    """
    try:
        import psutil

        # Find process by service name
        for proc in psutil.process_iter(['name', 'cmdline', 'pid', 'cpu_percent', 'memory_info', 'create_time']):
            try:
                if proc.info['cmdline'] and 'RiskManagerV34' in ' '.join(proc.info['cmdline']):
                    pid = proc.info['pid']

                    # Get detailed process info
                    proc_obj = psutil.Process(pid)
                    cpu_percent = proc_obj.cpu_percent(interval=0.1)
                    memory_mb = proc_obj.memory_info().rss / 1024 / 1024

                    # Calculate uptime
                    create_time = datetime.fromtimestamp(proc.info['create_time'])
                    uptime = datetime.now() - create_time
                    hours = uptime.seconds // 3600
                    minutes = (uptime.seconds % 3600) // 60
                    seconds = uptime.seconds % 60
                    uptime_str = f"{hours}h {minutes}m {seconds}s"

                    return {
                        "pid": pid,
                        "cpu_percent": cpu_percent,
                        "memory_mb": memory_mb,
                        "uptime_str": uptime_str,
                        "uptime_seconds": uptime.total_seconds(),
                    }
            except:
                continue

        # Process not found
        return {
            "pid": None,
            "cpu_percent": None,
            "memory_mb": None,
            "uptime_str": "N/A",
            "uptime_seconds": 0,
        }

    except ImportError:
        # psutil not available
        return {
            "pid": None,
            "cpu_percent": None,
            "memory_mb": None,
            "uptime_str": "N/A",
            "uptime_seconds": 0,
        }


def get_connection_status() -> Dict[str, Dict[str, Any]]:
    """
    Test connections to TopstepX API and database.

    Returns:
        Dictionary with connection status for each service
    """
    # TODO: Implement actual connection testing
    # For now, return placeholder data

    return {
        "api": {
            "connected": False,
            "latency_ms": None,
            "error": None,
        },
        "sdk": {
            "connected": False,
            "latency_ms": None,
            "error": None,
        },
        "database": {
            "connected": False,
            "size_mb": None,
            "error": None,
        },
    }


def get_monitoring_stats(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get monitoring statistics from configuration and database.

    Args:
        config_path: Optional path to risk_config.yaml

    Returns:
        Dictionary with account info, rule counts, lockouts, events
    """
    from pathlib import Path
    import yaml

    stats = {
        "account_id": "Unknown",
        "enabled_rules": 0,
        "total_rules": 0,
        "active_lockouts": 0,
        "events_today": 0,
    }

    try:
        # Load configuration
        if config_path is None:
            # Try common locations
            config_locations = [
                Path("config/risk_config.yaml"),
                Path("C:/ProgramData/RiskManagerV34/config/risk_config.yaml"),
            ]

            for loc in config_locations:
                if loc.exists():
                    config_path = loc
                    break

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Extract account ID
            if 'account' in config and 'account_id' in config['account']:
                stats['account_id'] = config['account']['account_id']

            # Count rules
            if 'rules' in config:
                stats['total_rules'] = len(config['rules'])
                stats['enabled_rules'] = sum(
                    1 for rule in config['rules'].values()
                    if rule.get('enabled', False)
                )

    except Exception:
        pass

    # TODO: Query database for lockouts and events
    # For now, return zeros

    return stats


def format_uptime(seconds: float) -> str:
    """
    Format uptime in human-readable format.

    Args:
        seconds: Uptime in seconds

    Returns:
        Formatted string (e.g., "3h 24m 15s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def is_service_installed() -> bool:
    """
    Check if Windows Service is installed.

    Returns:
        True if installed, False otherwise
    """
    try:
        import win32serviceutil
        win32serviceutil.QueryServiceStatus("RiskManagerV34")
        return True
    except Exception:
        return False


def wait_for_service_state(target_state: int, timeout: int = 30) -> bool:
    """
    Wait for service to reach target state.

    Args:
        target_state: Target service state (win32service.SERVICE_*)
        timeout: Maximum wait time in seconds

    Returns:
        True if state reached, False if timeout
    """
    import win32serviceutil
    import time

    for _ in range(timeout):
        try:
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
            if status[1] == target_state:
                return True
        except Exception:
            return False

        time.sleep(1)

    return False
