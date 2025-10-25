"""API response fixtures for testing TopstepX REST API integration

All fixtures return mock HTTP responses from TopstepX Gateway API.
"""
import pytest


# ============================================================================
# Authentication Responses
# ============================================================================

@pytest.fixture
def auth_success_response():
    """Successful authentication response with JWT token"""
    return {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE3MDYzMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "expiresIn": 86400,
        "tokenType": "Bearer"
    }


@pytest.fixture
def auth_failure_response():
    """Failed authentication (invalid credentials)"""
    return {
        "error": "Unauthorized",
        "message": "Invalid API key or username",
        "statusCode": 401
    }


@pytest.fixture
def auth_expired_token_response():
    """Expired JWT token error"""
    return {
        "error": "TokenExpired",
        "message": "JWT token has expired. Please re-authenticate.",
        "statusCode": 401
    }


# ============================================================================
# Position API Responses
# ============================================================================

@pytest.fixture
def positions_open_response():
    """GET /api/positions - Two open positions"""
    return [
        {
            "id": 12345,
            "accountId": 123,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,  # LONG
            "size": 3,
            "averagePrice": 21000.50,
            "createdAt": "2025-01-17T14:30:00Z",
            "updatedAt": "2025-01-17T14:45:15Z"
        },
        {
            "id": 12346,
            "accountId": 123,
            "contractId": "CON.F.US.ES.H25",
            "type": 2,  # SHORT
            "size": 1,
            "averagePrice": 5000.25,
            "createdAt": "2025-01-17T14:35:00Z",
            "updatedAt": "2025-01-17T14:35:00Z"
        }
    ]


@pytest.fixture
def positions_empty_response():
    """GET /api/positions - No open positions"""
    return []


@pytest.fixture
def position_close_success_response():
    """POST /api/positions/{id}/close - Successful position close"""
    return {
        "success": True,
        "message": "Position closed successfully",
        "positionId": 12345,
        "closedAt": "2025-01-17T14:50:00Z",
        "exitPrice": 21002.25
    }


@pytest.fixture
def position_partial_close_response():
    """POST /api/positions/{id}/close - Partial close (reduce size)"""
    return {
        "success": True,
        "message": "Position partially closed",
        "positionId": 12345,
        "originalSize": 5,
        "closedSize": 2,
        "remainingSize": 3,
        "exitPrice": 21002.00
    }


@pytest.fixture
def position_not_found_response():
    """Position not found error"""
    return {
        "error": "NotFound",
        "message": "Position 99999 not found",
        "statusCode": 404
    }


# ============================================================================
# Order API Responses
# ============================================================================

@pytest.fixture
def orders_open_response():
    """GET /api/orders - One working stop-loss order"""
    return [
        {
            "id": 78901,
            "accountId": 123,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 4,  # STOP
            "side": 1,  # BUY
            "size": 3,
            "stopPrice": 20950.00,
            "state": 2,  # ACTIVE
            "createdAt": "2025-01-17T14:30:05Z",
            "updatedAt": "2025-01-17T14:30:05Z"
        }
    ]


@pytest.fixture
def orders_empty_response():
    """GET /api/orders - No working orders"""
    return []


@pytest.fixture
def order_cancel_success_response():
    """DELETE /api/orders/{id} - Successful cancellation"""
    return {
        "success": True,
        "message": "Order canceled successfully",
        "orderId": 78901,
        "canceledAt": "2025-01-17T14:50:00Z"
    }


@pytest.fixture
def order_place_success_response():
    """POST /api/orders - Stop-loss order placed"""
    return {
        "success": True,
        "message": "Order placed successfully",
        "orderId": 78902,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 4,  # STOP
        "side": 1,  # BUY
        "size": 3,
        "stopPrice": 20990.00,
        "state": 2,  # ACTIVE
        "createdAt": "2025-01-17T14:55:00Z"
    }


@pytest.fixture
def order_rejected_response():
    """Order rejected (insufficient margin)"""
    return {
        "success": False,
        "error": "OrderRejected",
        "message": "Insufficient margin for order",
        "statusCode": 400
    }


@pytest.fixture
def order_not_found_response():
    """Order not found error"""
    return {
        "error": "NotFound",
        "message": "Order 99999 not found",
        "statusCode": 404
    }


# ============================================================================
# Contract API Responses
# ============================================================================

@pytest.fixture
def contract_mnq_response():
    """GET /api/contracts/{id} - MNQ contract details"""
    return {
        "id": "CON.F.US.MNQ.U25",
        "symbolId": "MNQ",
        "name": "Micro E-mini Nasdaq-100 Jun 2025",
        "exchange": "CME",
        "tickSize": 0.25,
        "tickValue": 0.50,
        "pointValue": 2.00,
        "expiration": "2025-06-20",
        "currency": "USD"
    }


@pytest.fixture
def contract_es_response():
    """GET /api/contracts/{id} - ES contract details"""
    return {
        "id": "CON.F.US.ES.H25",
        "symbolId": "ES",
        "name": "E-mini S&P 500 Mar 2025",
        "exchange": "CME",
        "tickSize": 0.25,
        "tickValue": 12.50,
        "pointValue": 50.00,
        "expiration": "2025-03-21",
        "currency": "USD"
    }


@pytest.fixture
def contract_nq_response():
    """GET /api/contracts/{id} - NQ contract details"""
    return {
        "id": "CON.F.US.NQ.H25",
        "symbolId": "NQ",
        "name": "E-mini Nasdaq-100 Mar 2025",
        "exchange": "CME",
        "tickSize": 0.25,
        "tickValue": 5.00,
        "pointValue": 20.00,
        "expiration": "2025-03-21",
        "currency": "USD"
    }


@pytest.fixture
def contracts_list_response():
    """GET /api/contracts - List of available contracts"""
    return [
        {
            "id": "CON.F.US.MNQ.U25",
            "symbolId": "MNQ",
            "name": "Micro E-mini Nasdaq-100 Jun 2025",
            "tickSize": 0.25,
            "tickValue": 0.50
        },
        {
            "id": "CON.F.US.ES.H25",
            "symbolId": "ES",
            "name": "E-mini S&P 500 Mar 2025",
            "tickSize": 0.25,
            "tickValue": 12.50
        },
        {
            "id": "CON.F.US.NQ.H25",
            "symbolId": "NQ",
            "name": "E-mini Nasdaq-100 Mar 2025",
            "tickSize": 0.25,
            "tickValue": 5.00
        }
    ]


@pytest.fixture
def contract_not_found_response():
    """Contract not found error"""
    return {
        "error": "NotFound",
        "message": "Contract not found",
        "statusCode": 404
    }


# ============================================================================
# Account API Responses
# ============================================================================

@pytest.fixture
def account_details_response():
    """GET /api/accounts/{id} - Account details"""
    return {
        "id": 123,
        "username": "trader@example.com",
        "status": "Active",
        "balance": 50000.00,
        "equity": 50150.50,
        "marginUsed": 5000.00,
        "marginAvailable": 45150.50
    }


@pytest.fixture
def account_suspended_response():
    """Account suspended status"""
    return {
        "id": 123,
        "username": "trader@example.com",
        "status": "Suspended",
        "balance": 48500.00,
        "equity": 48500.00,
        "marginUsed": 0.00,
        "marginAvailable": 0.00,
        "suspensionReason": "Exceeded daily loss limit"
    }


# ============================================================================
# Error Responses
# ============================================================================

@pytest.fixture
def rate_limit_error_response():
    """HTTP 429 - Rate limit exceeded"""
    return {
        "error": "TooManyRequests",
        "message": "Rate limit exceeded. Maximum 20 requests per second.",
        "statusCode": 429,
        "retryAfter": 1
    }


@pytest.fixture
def server_error_response():
    """HTTP 500 - Internal server error"""
    return {
        "error": "InternalServerError",
        "message": "An unexpected error occurred",
        "statusCode": 500
    }


@pytest.fixture
def bad_request_response():
    """HTTP 400 - Bad request (invalid parameters)"""
    return {
        "error": "BadRequest",
        "message": "Invalid request parameters",
        "statusCode": 400,
        "details": "Field 'size' must be greater than 0"
    }


@pytest.fixture
def timeout_error_response():
    """Request timeout error"""
    return {
        "error": "Timeout",
        "message": "Request timed out after 30 seconds",
        "statusCode": 504
    }


@pytest.fixture
def network_error_response():
    """Network connection error"""
    return {
        "error": "NetworkError",
        "message": "Unable to connect to TopstepX API",
        "statusCode": 0
    }
