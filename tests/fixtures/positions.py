"""Position test fixtures for pytest

Provides various position scenarios for testing risk rules.

IMPORTANT: This file contains two types of fixtures:
1. API response fixtures (camelCase) - Mock TopstepX API responses
2. Internal format fixtures (snake_case) - For internal processing/testing

Use API response fixtures when testing API clients/parsers.
Use internal format fixtures when testing core logic that expects converted data.
"""
import pytest
from datetime import datetime, timezone


# ============================================================================
# API RESPONSE FIXTURES (TopstepX API Format - camelCase)
# ============================================================================

@pytest.fixture
def single_es_long_position_api():
    """Single ES long position - API response format (camelCase)"""
    return {
        "id": 12345,
        "accountId": 123,
        "contractId": "CON.F.US.ES.H25",
        "type": 1,  # LONG
        "size": 1,
        "averagePrice": 4500.00,
        "createdAt": "2025-01-17T14:30:00Z",
        "updatedAt": "2025-01-17T14:30:00Z"
    }


# ============================================================================
# INTERNAL FORMAT FIXTURES (snake_case - for core logic)
# ============================================================================

@pytest.fixture
def single_es_long_position():
    """Single ES long position (1 contract at 4500.00) - Internal format"""
    return {
        "id": 12345,
        "account_id": 123,
        "contract_id": "CON.F.US.ES.H25",
        "type": 1,  # LONG
        "size": 1,
        "average_price": 4500.00,
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def single_nq_short_position_api():
    """Single NQ short position - API response format (camelCase)"""
    return {
        "id": 12346,
        "accountId": 123,
        "contractId": "CON.F.US.NQ.H25",
        "type": 2,  # SHORT
        "size": 1,
        "averagePrice": 16000.00,
        "createdAt": "2025-01-17T14:35:00Z",
        "updatedAt": "2025-01-17T14:35:00Z"
    }


@pytest.fixture
def single_nq_short_position():
    """Single NQ short position (1 contract at 16000.00) - Internal format"""
    return {
        "id": 12346,
        "account_id": 123,
        "contract_id": "CON.F.US.NQ.H25",
        "type": 2,  # SHORT
        "size": 1,
        "average_price": 16000.00,
        "created_at": "2025-01-17T14:35:00Z",
        "updated_at": "2025-01-17T14:35:00Z"
    }


@pytest.fixture
def two_open_positions_mixed_api():
    """Two open positions - API response format (camelCase)"""
    return [
        {
            "id": 12345,
            "accountId": 123,
            "contractId": "CON.F.US.ES.H25",
            "type": 1,  # LONG
            "size": 2,
            "averagePrice": 4500.00,
            "createdAt": "2025-01-17T14:30:00Z",
            "updatedAt": "2025-01-17T14:30:00Z"
        },
        {
            "id": 12346,
            "accountId": 123,
            "contractId": "CON.F.US.NQ.H25",
            "type": 2,  # SHORT
            "size": 1,
            "averagePrice": 16000.00,
            "createdAt": "2025-01-17T14:35:00Z",
            "updatedAt": "2025-01-17T14:35:00Z"
        }
    ]


@pytest.fixture
def two_open_positions_mixed():
    """Two open positions: ES long (2 contracts), NQ short (1 contract) - Internal format"""
    return [
        {
            "id": 12345,
            "account_id": 123,
            "contract_id": "CON.F.US.ES.H25",
            "type": 1,  # LONG
            "size": 2,
            "average_price": 4500.00,
            "created_at": "2025-01-17T14:30:00Z",
            "updated_at": "2025-01-17T14:30:00Z"
        },
        {
            "id": 12346,
            "account_id": 123,
            "contract_id": "CON.F.US.NQ.H25",
            "type": 2,  # SHORT
            "size": 1,
            "average_price": 16000.00,
            "created_at": "2025-01-17T14:35:00Z",
            "updated_at": "2025-01-17T14:35:00Z"
        }
    ]


@pytest.fixture
def three_mnq_long_positions():
    """Three MNQ long positions (testing contract-specific limits)"""
    return [
        {
            "id": 12347,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "type": 1,  # LONG
            "size": 1,
            "average_price": 21000.50,
            "created_at": "2025-01-17T14:30:00Z",
            "updated_at": "2025-01-17T14:30:00Z"
        },
        {
            "id": 12348,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "type": 1,  # LONG
            "size": 1,
            "average_price": 21005.00,
            "created_at": "2025-01-17T14:32:00Z",
            "updated_at": "2025-01-17T14:32:00Z"
        },
        {
            "id": 12349,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "type": 1,  # LONG
            "size": 1,
            "average_price": 21010.00,
            "created_at": "2025-01-17T14:33:00Z",
            "updated_at": "2025-01-17T14:33:00Z"
        }
    ]


@pytest.fixture
def max_contracts_breach_positions():
    """Six positions totaling 6 net contracts (breaches limit of 5)"""
    return [
        {
            "id": 12350,
            "account_id": 123,
            "contract_id": "CON.F.US.ES.H25",
            "type": 1,  # LONG
            "size": 2,
            "average_price": 4500.00,
            "created_at": "2025-01-17T14:30:00Z",
            "updated_at": "2025-01-17T14:30:00Z"
        },
        {
            "id": 12351,
            "account_id": 123,
            "contract_id": "CON.F.US.NQ.H25",
            "type": 1,  # LONG
            "size": 2,
            "average_price": 16000.00,
            "created_at": "2025-01-17T14:31:00Z",
            "updated_at": "2025-01-17T14:31:00Z"
        },
        {
            "id": 12352,
            "account_id": 123,
            "contract_id": "CON.F.US.MNQ.U25",
            "type": 1,  # LONG
            "size": 2,
            "average_price": 21000.00,
            "created_at": "2025-01-17T14:32:00Z",
            "updated_at": "2025-01-17T14:32:00Z"
        }
    ]


@pytest.fixture
def position_with_unrealized_loss():
    """Position with large unrealized loss (entry 21000, current 20700 = -$300)"""
    return {
        "id": 12353,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 1,  # LONG
        "size": 2,
        "average_price": 21000.00,
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def position_with_unrealized_profit():
    """Position with large unrealized profit (entry 21000, current 21500 = +$1000)"""
    return {
        "id": 12354,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 1,  # LONG
        "size": 2,
        "average_price": 21000.00,
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def position_at_breakeven():
    """Position at breakeven (entry 21000, current 21000 = $0)"""
    return {
        "id": 12355,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 1,  # LONG
        "size": 2,
        "average_price": 21000.00,
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def position_without_stop_loss():
    """Position opened 60 seconds ago without stop-loss (breach grace period)"""
    return {
        "id": 12356,
        "account_id": 123,
        "contract_id": "CON.F.US.MNQ.U25",
        "type": 1,  # LONG
        "size": 2,
        "average_price": 21000.00,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    }


@pytest.fixture
def position_in_blocked_symbol():
    """Position in blocked symbol (RTY - Russell 2000)"""
    return {
        "id": 12357,
        "account_id": 123,
        "contract_id": "CON.F.US.RTY.H25",
        "type": 1,  # LONG
        "size": 1,
        "average_price": 2100.00,
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def empty_positions_list():
    """No open positions"""
    return []


@pytest.fixture
def large_position_size():
    """Position with large size (10 contracts - testing scaling)"""
    return {
        "id": 12358,
        "account_id": 123,
        "contract_id": "CON.F.US.MES.H25",
        "type": 1,  # LONG
        "size": 10,
        "average_price": 4500.00,
        "created_at": "2025-01-17T14:30:00Z",
        "updated_at": "2025-01-17T14:30:00Z"
    }


@pytest.fixture
def hedged_positions():
    """Two opposite positions in same instrument (net = 0)"""
    return [
        {
            "id": 12359,
            "account_id": 123,
            "contract_id": "CON.F.US.ES.H25",
            "type": 1,  # LONG
            "size": 2,
            "average_price": 4500.00,
            "created_at": "2025-01-17T14:30:00Z",
            "updated_at": "2025-01-17T14:30:00Z"
        },
        {
            "id": 12360,
            "account_id": 123,
            "contract_id": "CON.F.US.ES.H25",
            "type": 2,  # SHORT
            "size": 2,
            "average_price": 4505.00,
            "created_at": "2025-01-17T14:31:00Z",
            "updated_at": "2025-01-17T14:31:00Z"
        }
    ]
