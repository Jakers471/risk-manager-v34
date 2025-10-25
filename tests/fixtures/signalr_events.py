"""SignalR real-time event fixtures for testing WebSocket message handling

All fixtures return mock SignalR event payloads from TopstepX Gateway.
"""
import pytest
from datetime import datetime, timezone


# ============================================================================
# GatewayUserTrade Events
# ============================================================================

@pytest.fixture
def trade_profit_event():
    """Profitable trade closed (+$45.50)"""
    return {
        "id": 10001,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "quantity": 2,
        "profitAndLoss": 45.50,
        "executionTime": "2025-01-17T14:45:15Z",
        "entryPrice": 21000.50,
        "exitPrice": 21023.00
    }


@pytest.fixture
def trade_loss_event():
    """Loss trade closed (-$120.00)"""
    return {
        "id": 10002,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "quantity": 3,
        "profitAndLoss": -120.00,
        "executionTime": "2025-01-17T15:00:00Z",
        "entryPrice": 21000.00,
        "exitPrice": 20980.00
    }


@pytest.fixture
def trade_breakeven_event():
    """Breakeven trade closed ($0.00)"""
    return {
        "id": 10003,
        "accountId": 123,
        "contractId": "CON.F.US.ES.H25",
        "quantity": 1,
        "profitAndLoss": 0.00,
        "executionTime": "2025-01-17T15:10:00Z",
        "entryPrice": 5000.00,
        "exitPrice": 5000.00
    }


@pytest.fixture
def trade_large_loss_event():
    """Large loss trade triggering daily loss limit (-$550.00)"""
    return {
        "id": 10004,
        "accountId": 123,
        "contractId": "CON.F.US.ES.H25",
        "quantity": 2,
        "profitAndLoss": -550.00,
        "executionTime": "2025-01-17T15:30:00Z",
        "entryPrice": 5000.00,
        "exitPrice": 4862.50
    }


@pytest.fixture
def trade_small_loss_cooldown_event():
    """Small loss triggering cooldown (-$105.00)"""
    return {
        "id": 10005,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "quantity": 2,
        "profitAndLoss": -105.00,
        "executionTime": "2025-01-17T15:45:00Z",
        "entryPrice": 21000.00,
        "exitPrice": 20895.00
    }


@pytest.fixture
def trade_large_profit_event():
    """Large profit trade (+$1050.00)"""
    return {
        "id": 10006,
        "accountId": 123,
        "contractId": "CON.F.US.ES.H25",
        "quantity": 2,
        "profitAndLoss": 1050.00,
        "executionTime": "2025-01-17T16:00:00Z",
        "entryPrice": 5000.00,
        "exitPrice": 5262.50
    }


# ============================================================================
# GatewayUserPosition Events
# ============================================================================

@pytest.fixture
def position_opened_event():
    """New position opened (3 MNQ long)"""
    return {
        "id": 12347,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 1,  # LONG
        "size": 3,
        "averagePrice": 21000.50,
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def position_scaled_in_event():
    """Position scaled in (size increased 3 → 5)"""
    return {
        "id": 12347,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 1,  # LONG
        "size": 5,
        "averagePrice": 21001.00,
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:35:00Z"
    }


@pytest.fixture
def position_scaled_out_event():
    """Position scaled out (size decreased 5 → 2)"""
    return {
        "id": 12347,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 1,  # LONG
        "size": 2,
        "averagePrice": 21001.00,
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:40:00Z"
    }


@pytest.fixture
def position_closed_event():
    """Position fully closed (size = 0)"""
    return {
        "id": 12347,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 1,  # LONG
        "size": 0,
        "averagePrice": 21000.50,
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:50:00Z"
    }


@pytest.fixture
def position_short_opened_event():
    """Short position opened"""
    return {
        "id": 12348,
        "accountId": 123,
        "contractId": "CON.F.US.ES.H25",
        "type": 2,  # SHORT
        "size": 1,
        "averagePrice": 5000.00,
        "createdAt": "2025-01-17T15:00:00Z",
        "updatedAt": "2025-01-17T15:00:00Z"
    }


# ============================================================================
# GatewayUserOrder Events
# ============================================================================

@pytest.fixture
def order_placed_event():
    """Limit order placed"""
    return {
        "id": 78903,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 2,  # LIMIT
        "side": 1,  # BUY
        "size": 3,
        "limitPrice": 21000.00,
        "state": 2,  # ACTIVE
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def order_filled_event():
    """Order fully filled"""
    return {
        "id": 78903,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 2,  # LIMIT
        "side": 1,  # BUY
        "size": 3,
        "limitPrice": 21000.00,
        "fillPrice": 21000.25,
        "filledSize": 3,
        "state": 3,  # FILLED
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:31:00Z"
    }


@pytest.fixture
def order_partial_fill_event():
    """Order partially filled (1 of 3 contracts)"""
    return {
        "id": 78904,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 2,  # LIMIT
        "side": 1,  # BUY
        "size": 3,
        "limitPrice": 21000.00,
        "fillPrice": 21000.25,
        "filledSize": 1,
        "state": 5,  # PARTIAL
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:31:00Z"
    }


@pytest.fixture
def order_canceled_event():
    """Order canceled"""
    return {
        "id": 78903,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 2,  # LIMIT
        "side": 1,  # BUY
        "size": 3,
        "limitPrice": 21000.00,
        "state": 4,  # CANCELED
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:35:00Z"
    }


@pytest.fixture
def order_stop_loss_placed_event():
    """Stop-loss order placed"""
    return {
        "id": 78905,
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


@pytest.fixture
def order_rejected_event():
    """Order rejected by exchange"""
    return {
        "id": 78906,
        "accountId": 123,
        "contractId": "CON.F.US.MNQ.U25",
        "type": 1,  # MARKET
        "side": 1,  # BUY
        "size": 10,
        "state": 6,  # REJECTED
        "rejectionReason": "Insufficient margin",
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:30:01Z"
    }


# ============================================================================
# MarketQuote Events
# ============================================================================

@pytest.fixture
def quote_mnq_normal():
    """Normal MNQ quote"""
    return {
        "contractId": "CON.F.US.MNQ.U25",
        "bid": 21000.25,
        "ask": 21000.50,
        "last": 21000.50,
        "timestamp": "2025-01-17T14:45:15.123Z"
    }


@pytest.fixture
def quote_mnq_moved_down():
    """MNQ price moved down (loss for long positions)"""
    return {
        "contractId": "CON.F.US.MNQ.U25",
        "bid": 20700.00,
        "ask": 20700.25,
        "last": 20700.25,
        "timestamp": "2025-01-17T14:46:00.456Z"
    }


@pytest.fixture
def quote_mnq_moved_up():
    """MNQ price moved up (profit for long positions)"""
    return {
        "contractId": "CON.F.US.MNQ.U25",
        "bid": 21500.00,
        "ask": 21500.25,
        "last": 21500.25,
        "timestamp": "2025-01-17T14:47:00.789Z"
    }


@pytest.fixture
def quote_es_normal():
    """Normal ES quote"""
    return {
        "contractId": "CON.F.US.ES.H25",
        "bid": 5000.00,
        "ask": 5000.25,
        "last": 5000.25,
        "timestamp": "2025-01-17T14:45:15.123Z"
    }


@pytest.fixture
def quote_nq_normal():
    """Normal NQ quote"""
    return {
        "contractId": "CON.F.US.NQ.H25",
        "bid": 16000.00,
        "ask": 16000.25,
        "last": 16000.25,
        "timestamp": "2025-01-17T14:45:15.123Z"
    }


@pytest.fixture
def quote_stale():
    """Stale quote (old timestamp)"""
    return {
        "contractId": "CON.F.US.MNQ.U25",
        "bid": 21000.25,
        "ask": 21000.50,
        "last": 21000.50,
        "timestamp": "2025-01-17T13:00:00.000Z"  # 1+ hour old
    }


# ============================================================================
# GatewayUserAccount Events
# ============================================================================

@pytest.fixture
def account_update_event():
    """Account balance/equity update"""
    return {
        "accountId": 123,
        "status": "Active",
        "balance": 50150.50,
        "equity": 50200.25,
        "timestamp": "2025-01-17T14:45:00Z"
    }


@pytest.fixture
def account_auth_event():
    """Authentication event (potential auth loss guard trigger)"""
    return {
        "accountId": 123,
        "eventType": "Authentication",
        "status": "Successful",
        "ipAddress": "192.168.1.100",
        "timestamp": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def account_auth_suspicious_event():
    """Suspicious auth event (different IP, potential bypass)"""
    return {
        "accountId": 123,
        "eventType": "Authentication",
        "status": "Successful",
        "ipAddress": "203.0.113.42",  # Different IP
        "timestamp": "2025-01-17T14:30:01Z"
    }


@pytest.fixture
def account_suspended_event():
    """Account suspended event"""
    return {
        "accountId": 123,
        "status": "Suspended",
        "reason": "Exceeded daily loss limit",
        "timestamp": "2025-01-17T14:50:00Z"
    }
