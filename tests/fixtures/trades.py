"""Trade history fixtures for testing trade frequency and realized P&L tracking

IMPORTANT: This file contains two types of fixtures:
1. API response fixtures (camelCase) - Mock TopstepX API responses
2. Internal format fixtures (snake_case) - For internal processing/testing

Use API response fixtures when testing API clients/parsers.
Use internal format fixtures when testing core logic that expects converted data.
"""
import pytest
from datetime import datetime, timedelta, timezone


# ============================================================================
# API RESPONSE FIXTURES (TopstepX API Format - camelCase)
# ============================================================================

@pytest.fixture
def trade_single_profit_api():
    """Single profitable trade - API response format (camelCase)"""
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


# ============================================================================
# INTERNAL FORMAT FIXTURES (snake_case - for core logic)
# ============================================================================

@pytest.fixture
def trade_single_profit():
    """Single profitable trade (+$45.50) - Internal format"""
    return {
        "id": 10001,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "quantity": 2,
        "profit_and_loss": 45.50,
        "execution_time": "2025-01-17T14:45:15Z",
        "entry_price": 21000.50,
        "exit_price": 21023.00
    }


@pytest.fixture
def trade_single_loss_api():
    """Single loss trade - API response format (camelCase)"""
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
def trade_single_loss():
    """Single loss trade (-$120.00) - Internal format"""
    return {
        "id": 10002,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "quantity": 3,
        "profit_and_loss": -120.00,
        "execution_time": "2025-01-17T15:00:00Z",
        "entry_price": 21000.00,
        "exit_price": 20980.00
    }


@pytest.fixture
def trade_large_loss_breach():
    """Large loss breaching daily limit (-$550.00)"""
    return {
        "id": 10003,
        "account_id": 123,
        "contract_id": "CON.F.US.ES.H25",
        "quantity": 2,
        "profit_and_loss": -550.00,
        "execution_time": "2025-01-17T15:30:00Z",
        "entry_price": 5000.00,
        "exit_price": 4862.50
    }


@pytest.fixture
def trade_cooldown_trigger():
    """Loss triggering cooldown (-$105.00)"""
    return {
        "id": 10004,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "quantity": 2,
        "profit_and_loss": -105.00,
        "execution_time": "2025-01-17T15:45:00Z",
        "entry_price": 21000.00,
        "exit_price": 20895.00
    }


@pytest.fixture
def trades_sequence_losses():
    """Sequence of 3 losing trades (testing cumulative loss)"""
    base_time = datetime(2025, 1, 17, 14, 0, 0, tzinfo=timezone.utc)
    return [
        {
            "id": 10005,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "quantity": 2,
            "profit_and_loss": -150.00,
            "execution_time": base_time.isoformat().replace("+00:00", "Z")
        },
        {
            "id": 10006,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "quantity": 2,
            "profit_and_loss": -200.00,
            "execution_time": (base_time + timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
        },
        {
            "id": 10007,
            "account_id": 123,
            "contract_id": "CON.F.US.ES.H25",
            "quantity": 1,
            "profit_and_loss": -180.00,
            "execution_time": (base_time + timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
        }
    ]


@pytest.fixture
def trades_high_frequency():
    """35 trades in 1 hour (breach frequency limit of 30)"""
    base_time = datetime(2025, 1, 17, 14, 0, 0, tzinfo=timezone.utc)
    trades = []
    for i in range(35):
        trades.append({
            "id": 10100 + i,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "quantity": 1,
            "profit_and_loss": 10.00 if i % 2 == 0 else -10.00,
            "execution_time": (base_time + timedelta(minutes=i*2)).isoformat().replace("+00:00", "Z")
        })
    return trades


@pytest.fixture
def trades_within_frequency_limit():
    """25 trades in 1 hour (within limit of 30)"""
    base_time = datetime(2025, 1, 17, 14, 0, 0, tzinfo=timezone.utc)
    trades = []
    for i in range(25):
        trades.append({
            "id": 10200 + i,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "quantity": 1,
            "profit_and_loss": 15.00 if i % 2 == 0 else -10.00,
            "execution_time": (base_time + timedelta(minutes=i*2.5)).isoformat().replace("+00:00", "Z")
        })
    return trades


@pytest.fixture
def trades_mixed_pnl():
    """Mix of profitable and losing trades (net slightly negative)"""
    base_time = datetime(2025, 1, 17, 14, 0, 0, tzinfo=timezone.utc)
    return [
        {
            "id": 10300,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "quantity": 2,
            "profit_and_loss": 100.00,
            "execution_time": base_time.isoformat().replace("+00:00", "Z")
        },
        {
            "id": 10301,
            "account_id": 123,
            "contract_id": "CON.F.US.ES.H25",
            "quantity": 1,
            "profit_and_loss": -150.00,
            "execution_time": (base_time + timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        },
        {
            "id": 10302,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "quantity": 1,
            "profit_and_loss": 50.00,
            "execution_time": (base_time + timedelta(minutes=20)).isoformat().replace("+00:00", "Z")
        },
        {
            "id": 10303,
            "account_id": 123,
            "contract_id": "CON.F.US.NQ.H25",
            "quantity": 1,
            "profit_and_loss": -80.00,
            "execution_time": (base_time + timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
        }
    ]


@pytest.fixture
def trade_breakeven():
    """Breakeven trade ($0.00 P&L)"""
    return {
        "id": 10400,
        "account_id": 123,
        "contract_id": "CON.F.US.ES.H25",
        "quantity": 1,
        "profit_and_loss": 0.00,
        "execution_time": "2025-01-17T15:10:00Z",
        "entry_price": 5000.00,
        "exit_price": 5000.00
    }


@pytest.fixture
def empty_trades_list():
    """No trades (fresh session)"""
    return []
