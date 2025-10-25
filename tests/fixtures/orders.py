"""Order test fixtures for testing order management and stop-loss rules

IMPORTANT: This file contains two types of fixtures:
1. API response fixtures (camelCase) - Mock TopstepX API responses
2. Internal format fixtures (snake_case) - For internal processing/testing

Use API response fixtures when testing API clients/parsers.
Use internal format fixtures when testing core logic that expects converted data.
"""
import pytest


# ============================================================================
# API RESPONSE FIXTURES (TopstepX API Format - camelCase)
# ============================================================================

@pytest.fixture
def order_stop_loss_working_api():
    """Working stop-loss order - API response format (camelCase)"""
    return {
        "id": 78901,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 4,  # STOP
        "side": 1,  # BUY (to close short)
        "size": 3,
        "stopPrice": 20950.00,
        "state": 2,  # ACTIVE
        "createdAt": "2025-01-17T14:30:05Z",
        "updatedAt": "2025-01-17T14:30:05Z"
    }


# ============================================================================
# INTERNAL FORMAT FIXTURES (snake_case - for core logic)
# ============================================================================

@pytest.fixture
def order_stop_loss_working():
    """Working stop-loss order (ACTIVE state) - Internal format"""
    return {
        "id": 78901,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 4,  # STOP
        "side": 1,  # BUY (to close short)
        "size": 3,
        "stop_price": 20950.00,
        "state": 2,  # ACTIVE
        "created_at": "2025-01-17T14:30:05Z",
        "updated_at": "2025-01-17T14:30:05Z"
    }


@pytest.fixture
def order_limit_working_api():
    """Working limit order - API response format (camelCase)"""
    return {
        "id": 78902,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 2,  # LIMIT
        "side": 1,  # BUY
        "size": 2,
        "limitPrice": 21000.00,
        "state": 2,  # ACTIVE
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def order_limit_working():
    """Working limit order (ACTIVE state) - Internal format"""
    return {
        "id": 78902,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 2,  # LIMIT
        "side": 1,  # BUY
        "size": 2,
        "limit_price": 21000.00,
        "state": 2,  # ACTIVE
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def order_market_pending():
    """Market order pending (submitted but not filled)"""
    return {
        "id": 78903,
        "account_id": 123,
        "contract_id": "CON.F.US.ES.H25",
        "type": 1,  # MARKET
        "side": 1,  # BUY
        "size": 1,
        "state": 1,  # PENDING
        "created_at": "2025-01-17T14:35:00Z",
        "updated_at": "2025-01-17T14:35:00Z"
    }


@pytest.fixture
def order_filled():
    """Filled order (no longer working)"""
    return {
        "id": 78904,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 2,  # LIMIT
        "side": 1,  # BUY
        "size": 3,
        "limit_price": 21000.00,
        "fill_price": 21000.25,
        "filled_size": 3,
        "state": 3,  # FILLED
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:31:00Z"
    }


@pytest.fixture
def order_canceled():
    """Canceled order"""
    return {
        "id": 78905,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 2,  # LIMIT
        "side": 1,  # BUY
        "size": 3,
        "limit_price": 21000.00,
        "state": 4,  # CANCELED
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:35:00Z"
    }


@pytest.fixture
def order_partial_fill():
    """Partially filled order"""
    return {
        "id": 78906,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 2,  # LIMIT
        "side": 1,  # BUY
        "size": 3,
        "limit_price": 21000.00,
        "fill_price": 21000.25,
        "filled_size": 1,
        "state": 5,  # PARTIAL
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:31:00Z"
    }


@pytest.fixture
def order_rejected():
    """Rejected order"""
    return {
        "id": 78907,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 1,  # MARKET
        "side": 1,  # BUY
        "size": 10,
        "state": 6,  # REJECTED
        "rejection_reason": "Insufficient margin",
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:30:01Z"
    }


@pytest.fixture
def order_stop_loss_for_position():
    """Stop-loss order protecting specific position"""
    return {
        "id": 78908,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 4,  # STOP
        "side": 1,  # BUY (to close short)
        "size": 2,
        "stop_price": 20990.00,
        "state": 2,  # ACTIVE
        "position_id": 12345,  # Links to specific position
        "created_at": "2025-01-17T14:30:05Z",
        "updated_at": "2025-01-17T14:30:05Z"
    }


@pytest.fixture
def orders_multiple_working():
    """Multiple working orders"""
    return [
        {
            "id": 78909,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "type": 4,  # STOP
            "side": 1,
            "size": 2,
            "stop_price": 20950.00,
            "state": 2,  # ACTIVE
            "created_at": "2025-01-17T14:30:00Z",
            "updated_at": "2025-01-17T14:30:00Z"
        },
        {
            "id": 78910,
            "account_id": 123,
            "contract_id": "CON.F.US.ES.H25",
            "type": 2,  # LIMIT
            "side": 2,  # SELL
            "size": 1,
            "limit_price": 5010.00,
            "state": 2,  # ACTIVE
            "created_at": "2025-01-17T14:31:00Z",
            "updated_at": "2025-01-17T14:31:00Z"
        }
    ]


@pytest.fixture
def order_blocked_symbol():
    """Order for blocked symbol (RTY)"""
    return {
        "id": 78911,
        "account_id": 123,
        "contract_id": "CON.F.US.RTY.H25",
        "type": 1,  # MARKET
        "side": 1,  # BUY
        "size": 1,
        "state": 2,  # ACTIVE
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def empty_orders_list():
    """No working orders"""
    return []
