"""Lockout state fixtures for testing lockout management

All fixtures return lockout state dictionaries.
"""
import pytest
from datetime import datetime, timedelta, timezone


@pytest.fixture
def lockout_active_daily_loss():
    """Active lockout due to daily loss limit"""
    now = datetime.now(timezone.utc)
    return {
        "account_id": 123,
        "is_locked": True,
        "reason": "Daily realized loss limit exceeded: -$550.00",
        "locked_at": (now - timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
        "locked_until": (now + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
        "rule_id": "RULE-003"
    }


@pytest.fixture
def lockout_active_unrealized_loss():
    """Active lockout due to unrealized loss"""
    now = datetime.now(timezone.utc)
    return {
        "account_id": 123,
        "is_locked": True,
        "reason": "Daily unrealized loss limit exceeded: -$520.00",
        "locked_at": (now - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        "locked_until": (now + timedelta(hours=1, minutes=30)).isoformat().replace("+00:00", "Z"),
        "rule_id": "RULE-004"
    }


@pytest.fixture
def lockout_active_auth_guard():
    """Active lockout due to auth loss guard (permanent)"""
    now = datetime.now(timezone.utc)
    return {
        "account_id": 123,
        "is_locked": True,
        "reason": "Authentication bypass detected",
        "locked_at": (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "locked_until": None,  # Permanent lockout
        "rule_id": "RULE-010"
    }


@pytest.fixture
def lockout_expired():
    """Expired lockout (should be auto-unlocked)"""
    now = datetime.now(timezone.utc)
    return {
        "account_id": 123,
        "is_locked": True,
        "reason": "Daily realized loss limit exceeded: -$520.00",
        "locked_at": (now - timedelta(hours=4)).isoformat().replace("+00:00", "Z"),
        "locked_until": (now - timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),  # Past
        "rule_id": "RULE-003"
    }


@pytest.fixture
def lockout_not_locked():
    """No active lockout"""
    return {
        "account_id": 123,
        "is_locked": False,
        "reason": None,
        "locked_at": None,
        "locked_until": None,
        "rule_id": None
    }


@pytest.fixture
def lockout_max_contracts():
    """Lockout due to max contracts breach"""
    now = datetime.now(timezone.utc)
    return {
        "account_id": 123,
        "is_locked": True,
        "reason": "Max contracts exceeded: 6 net contracts (limit: 5)",
        "locked_at": now.isoformat().replace("+00:00", "Z"),
        "locked_until": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "rule_id": "RULE-001"
    }


@pytest.fixture
def lockout_symbol_blocks():
    """Lockout due to blocked symbol trading"""
    now = datetime.now(timezone.utc)
    return {
        "account_id": 123,
        "is_locked": True,
        "reason": "Blocked symbol traded: RTY",
        "locked_at": now.isoformat().replace("+00:00", "Z"),
        "locked_until": (now + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
        "rule_id": "RULE-011"
    }


@pytest.fixture
def lockout_no_stop_loss():
    """Lockout due to no stop-loss grace period violation"""
    now = datetime.now(timezone.utc)
    return {
        "account_id": 123,
        "is_locked": True,
        "reason": "Position opened without stop-loss for >30 seconds",
        "locked_at": now.isoformat().replace("+00:00", "Z"),
        "locked_until": (now + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        "rule_id": "RULE-008"
    }


@pytest.fixture
def lockout_nearly_expired():
    """Lockout expiring in 1 minute"""
    now = datetime.now(timezone.utc)
    return {
        "account_id": 123,
        "is_locked": True,
        "reason": "Daily realized loss limit exceeded",
        "locked_at": (now - timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
        "locked_until": (now + timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "rule_id": "RULE-003"
    }


@pytest.fixture
def lockout_permanent():
    """Permanent lockout (locked_until = None)"""
    now = datetime.now(timezone.utc)
    return {
        "account_id": 123,
        "is_locked": True,
        "reason": "Permanent lockout - manual admin intervention required",
        "locked_at": (now - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
        "locked_until": None,  # Permanent
        "rule_id": "RULE-010"
    }
