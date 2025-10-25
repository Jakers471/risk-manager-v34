"""Account configuration fixtures for testing multi-account scenarios

IMPORTANT: This file contains two types of fixtures:
1. API response fixtures (camelCase) - Mock TopstepX API responses
2. Internal config fixtures (snake_case) - For local configuration/testing

Use API response fixtures when testing API clients/parsers.
Use internal config fixtures when testing configuration management.
"""
import pytest


# ============================================================================
# API RESPONSE FIXTURES (TopstepX API Format - camelCase)
# ============================================================================

@pytest.fixture
def account_details_api():
    """Account details from API - API response format (camelCase)"""
    return {
        "id": 123,
        "username": "test_trader@example.com",
        "status": "Active",
        "balance": 50000.00,
        "equity": 50150.50,
        "marginUsed": 5000.00,
        "marginAvailable": 45150.50,
        "buyingPower": 50000.00,
        "unrealizedProfitLoss": 150.50
    }


# ============================================================================
# INTERNAL CONFIG FIXTURES (snake_case - for local config)
# ============================================================================

@pytest.fixture
def account_test_primary():
    """Primary test account - Internal config format"""
    return {
        "account_id": 123,
        "username": "test_trader@example.com",
        "api_key": "test_api_key_123",
        "enabled": True,
        "nickname": "Test Account 1"
    }


@pytest.fixture
def account_test_secondary():
    """Secondary test account"""
    return {
        "account_id": 456,
        "username": "test_trader2@example.com",
        "api_key": "test_api_key_456",
        "enabled": True,
        "nickname": "Test Account 2"
    }


@pytest.fixture
def account_disabled():
    """Disabled account (testing enabled=False)"""
    return {
        "account_id": 789,
        "username": "disabled@example.com",
        "api_key": "test_api_key_789",
        "enabled": False,
        "nickname": "Disabled Account"
    }


@pytest.fixture
def account_without_api_key():
    """Account missing API key (testing validation)"""
    return {
        "account_id": 999,
        "username": "no_key@example.com",
        "api_key": None,
        "enabled": True,
        "nickname": "No API Key"
    }


@pytest.fixture
def accounts_multiple():
    """Multiple accounts for multi-account testing"""
    return [
        {
            "account_id": 123,
            "username": "test_trader@example.com",
            "api_key": "test_api_key_123",
            "enabled": True,
            "nickname": "Test Account 1"
        },
        {
            "account_id": 456,
            "username": "test_trader2@example.com",
            "api_key": "test_api_key_456",
            "enabled": True,
            "nickname": "Test Account 2"
        },
        {
            "account_id": 789,
            "username": "test_trader3@example.com",
            "api_key": "test_api_key_789",
            "enabled": False,
            "nickname": "Test Account 3 (Disabled)"
        }
    ]


@pytest.fixture
def account_config_minimal():
    """Minimal valid account configuration"""
    return {
        "account_id": 111,
        "username": "minimal@example.com",
        "api_key": "minimal_key"
    }


@pytest.fixture
def account_config_full():
    """Full account configuration with all optional fields"""
    return {
        "account_id": 222,
        "username": "full@example.com",
        "api_key": "full_api_key_222",
        "enabled": True,
        "nickname": "Full Config Account",
        "email_notifications": True,
        "slack_webhook": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX",
        "max_daily_trades": 50,
        "notes": "Test account with full configuration"
    }


@pytest.fixture
def account_suspended_status():
    """Account status: Suspended"""
    return {
        "account_id": 123,
        "username": "suspended@example.com",
        "status": "Suspended",
        "suspension_reason": "Exceeded daily loss limit",
        "suspended_at": "2025-01-17T14:50:00Z",
        "suspended_until": "2025-01-17T17:00:00Z"
    }


@pytest.fixture
def account_suspended_api():
    """Account suspended - API response format (camelCase)"""
    return {
        "id": 123,
        "username": "suspended@example.com",
        "status": "Suspended",
        "balance": 48500.00,
        "equity": 48500.00,
        "marginUsed": 0.00,
        "marginAvailable": 0.00,
        "suspensionReason": "Exceeded daily loss limit",
        "suspendedAt": "2025-01-17T14:50:00Z",
        "suspendedUntil": "2025-01-17T17:00:00Z"
    }


@pytest.fixture
def account_active_status():
    """Account status: Active - Internal format"""
    return {
        "account_id": 123,
        "username": "active@example.com",
        "status": "Active",
        "balance": 50000.00,
        "equity": 50150.50,
        "margin_used": 5000.00,
        "margin_available": 45150.50
    }
