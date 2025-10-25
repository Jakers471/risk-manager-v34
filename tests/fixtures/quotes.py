"""Market quote fixtures for testing real-time P&L calculations

All fixtures return quote event dictionaries.
"""
import pytest
from datetime import datetime, timezone


@pytest.fixture
def quote_mnq_current():
    """Current MNQ quote"""
    return {
        "contract_id": "CON.F.US.MNQ.U25",
        "bid": 21000.25,
        "ask": 21000.50,
        "last": 21000.50,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }


@pytest.fixture
def quote_mnq_high():
    """MNQ quote at high price (profit for longs)"""
    return {
        "contract_id": "CON.F.US.MNQ.U25",
        "bid": 21500.00,
        "ask": 21500.25,
        "last": 21500.25,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }


@pytest.fixture
def quote_mnq_low():
    """MNQ quote at low price (loss for longs)"""
    return {
        "contract_id": "CON.F.US.MNQ.U25",
        "bid": 20700.00,
        "ask": 20700.25,
        "last": 20700.25,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }


@pytest.fixture
def quote_es_current():
    """Current ES quote"""
    return {
        "contract_id": "CON.F.US.ES.H25",
        "bid": 5000.00,
        "ask": 5000.25,
        "last": 5000.25,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }


@pytest.fixture
def quote_nq_current():
    """Current NQ quote"""
    return {
        "contract_id": "CON.F.US.NQ.H25",
        "bid": 16000.00,
        "ask": 16000.25,
        "last": 16000.25,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }


@pytest.fixture
def quote_stale():
    """Stale quote (old timestamp > 60 seconds)"""
    return {
        "contract_id": "CON.F.US.MNQ.U25",
        "bid": 21000.25,
        "ask": 21000.50,
        "last": 21000.50,
        "timestamp": "2025-01-17T13:00:00.000Z"  # Old timestamp
    }


@pytest.fixture
def quote_wide_spread():
    """Quote with wide bid-ask spread (low liquidity)"""
    return {
        "contract_id": "CON.F.US.MNQ.U25",
        "bid": 21000.00,
        "ask": 21005.00,  # 20 tick spread
        "last": 21002.50,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }


@pytest.fixture
def quote_zero_bid():
    """Quote with zero bid (testing edge case)"""
    return {
        "contract_id": "CON.F.US.MNQ.U25",
        "bid": 0.00,
        "ask": 21000.50,
        "last": 21000.50,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }


@pytest.fixture
def quotes_streaming():
    """Sequence of quote updates (streaming simulation)"""
    base_time = datetime.now(timezone.utc)
    return [
        {
            "contract_id": "CON.F.US.MNQ.U25",
            "bid": 21000.25,
            "ask": 21000.50,
            "last": 21000.50,
            "timestamp": base_time.isoformat().replace("+00:00", "Z")
        },
        {
            "contract_id": "CON.F.US.MNQ.U25",
            "bid": 21001.00,
            "ask": 21001.25,
            "last": 21001.25,
            "timestamp": base_time.replace(microsecond=500000).isoformat().replace("+00:00", "Z")
        },
        {
            "contract_id": "CON.F.US.MNQ.U25",
            "bid": 21000.75,
            "ask": 21001.00,
            "last": 21001.00,
            "timestamp": base_time.replace(second=base_time.second + 1).isoformat().replace("+00:00", "Z")
        }
    ]
