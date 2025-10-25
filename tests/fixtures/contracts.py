"""Contract metadata fixtures for testing contract cache and P&L calculations

All fixtures return contract specifications matching TopstepX contract format.
"""
import pytest


@pytest.fixture
def contract_mnq():
    """Micro E-mini Nasdaq-100 (MNQ) contract"""
    return {
        "id": "CON.F.US.MNQ.U25",
        "symbol_id": "MNQ",
        "name": "Micro E-mini Nasdaq-100 Jun 2025",
        "exchange": "CME",
        "tick_size": 0.25,
        "tick_value": 0.50,
        "point_value": 2.00,
        "expiration": "2025-06-20",
        "currency": "USD",
        "cached_at": "2025-01-17T08:00:00Z"
    }


@pytest.fixture
def contract_es():
    """E-mini S&P 500 (ES) contract"""
    return {
        "id": "CON.F.US.ES.H25",
        "symbol_id": "ES",
        "name": "E-mini S&P 500 Mar 2025",
        "exchange": "CME",
        "tick_size": 0.25,
        "tick_value": 12.50,
        "point_value": 50.00,
        "expiration": "2025-03-21",
        "currency": "USD",
        "cached_at": "2025-01-17T08:00:00Z"
    }


@pytest.fixture
def contract_nq():
    """E-mini Nasdaq-100 (NQ) contract"""
    return {
        "id": "CON.F.US.NQ.H25",
        "symbol_id": "NQ",
        "name": "E-mini Nasdaq-100 Mar 2025",
        "exchange": "CME",
        "tick_size": 0.25,
        "tick_value": 5.00,
        "point_value": 20.00,
        "expiration": "2025-03-21",
        "currency": "USD",
        "cached_at": "2025-01-17T08:00:00Z"
    }


@pytest.fixture
def contract_mes():
    """Micro E-mini S&P 500 (MES) contract"""
    return {
        "id": "CON.F.US.MES.H25",
        "symbol_id": "MES",
        "name": "Micro E-mini S&P 500 Mar 2025",
        "exchange": "CME",
        "tick_size": 0.25,
        "tick_value": 1.25,
        "point_value": 5.00,
        "expiration": "2025-03-21",
        "currency": "USD",
        "cached_at": "2025-01-17T08:00:00Z"
    }


@pytest.fixture
def contract_rty():
    """E-mini Russell 2000 (RTY) - blocked symbol"""
    return {
        "id": "CON.F.US.RTY.H25",
        "symbol_id": "RTY",
        "name": "E-mini Russell 2000 Mar 2025",
        "exchange": "CME",
        "tick_size": 0.10,
        "tick_value": 5.00,
        "point_value": 50.00,
        "expiration": "2025-03-21",
        "currency": "USD",
        "cached_at": "2025-01-17T08:00:00Z"
    }


@pytest.fixture
def contract_ym():
    """E-mini Dow ($5) (YM) contract"""
    return {
        "id": "CON.F.US.YM.H25",
        "symbol_id": "YM",
        "name": "E-mini Dow ($5) Mar 2025",
        "exchange": "CBOT",
        "tick_size": 1.00,
        "tick_value": 5.00,
        "point_value": 5.00,
        "expiration": "2025-03-21",
        "currency": "USD",
        "cached_at": "2025-01-17T08:00:00Z"
    }


@pytest.fixture
def contract_cache_all():
    """All common contracts (for cache initialization)"""
    return [
        {
            "id": "CON.F.US.MNQ.U25",
            "symbol_id": "MNQ",
            "name": "Micro E-mini Nasdaq-100 Jun 2025",
            "tick_size": 0.25,
            "tick_value": 0.50,
            "point_value": 2.00,
            "cached_at": "2025-01-17T08:00:00Z"
        },
        {
            "id": "CON.F.US.ES.H25",
            "symbol_id": "ES",
            "name": "E-mini S&P 500 Mar 2025",
            "tick_size": 0.25,
            "tick_value": 12.50,
            "point_value": 50.00,
            "cached_at": "2025-01-17T08:00:00Z"
        },
        {
            "id": "CON.F.US.NQ.H25",
            "symbol_id": "NQ",
            "name": "E-mini Nasdaq-100 Mar 2025",
            "tick_size": 0.25,
            "tick_value": 5.00,
            "point_value": 20.00,
            "cached_at": "2025-01-17T08:00:00Z"
        },
        {
            "id": "CON.F.US.MES.H25",
            "symbol_id": "MES",
            "name": "Micro E-mini S&P 500 Mar 2025",
            "tick_size": 0.25,
            "tick_value": 1.25,
            "point_value": 5.00,
            "cached_at": "2025-01-17T08:00:00Z"
        }
    ]


@pytest.fixture
def contract_unknown():
    """Unknown contract (not in cache, needs API lookup)"""
    return {
        "id": "CON.F.US.UNKNOWN.H25",
        "symbol_id": "UNKNOWN",
        "name": "Unknown Contract Mar 2025",
        "tick_size": 0.01,
        "tick_value": 1.00,
        "point_value": 100.00,
        "cached_at": None  # Not cached
    }


@pytest.fixture
def contract_expired():
    """Expired contract (testing expiration handling)"""
    return {
        "id": "CON.F.US.ES.Z24",
        "symbol_id": "ES",
        "name": "E-mini S&P 500 Dec 2024",
        "exchange": "CME",
        "tick_size": 0.25,
        "tick_value": 12.50,
        "point_value": 50.00,
        "expiration": "2024-12-20",  # Past expiration
        "currency": "USD",
        "cached_at": "2024-12-01T08:00:00Z"
    }


# P&L Calculation Helper Fixtures

@pytest.fixture
def pnl_calc_mnq_long():
    """MNQ P&L calculation: Long 2 @ 21000, current 21500 = +$1000"""
    return {
        "contract": {
            "id": "CON.F.US.MNQ.U25",
            "tick_size": 0.25,
            "tick_value": 0.50,
            "point_value": 2.00
        },
        "position": {
            "type": 1,  # LONG
            "size": 2,
            "entry_price": 21000.00
        },
        "quote": {
            "last": 21500.00
        },
        "expected_pnl": 1000.00  # 500 points * $2/point * 2 contracts
    }


@pytest.fixture
def pnl_calc_mnq_long_loss():
    """MNQ P&L calculation: Long 2 @ 21000, current 20700 = -$600"""
    return {
        "contract": {
            "id": "CON.F.US.MNQ.U25",
            "tick_size": 0.25,
            "tick_value": 0.50,
            "point_value": 2.00
        },
        "position": {
            "type": 1,  # LONG
            "size": 2,
            "entry_price": 21000.00
        },
        "quote": {
            "last": 20700.00
        },
        "expected_pnl": -600.00  # -300 points * $2/point * 2 contracts
    }


@pytest.fixture
def pnl_calc_es_short():
    """ES P&L calculation: Short 1 @ 5000, current 4950 = +$625"""
    return {
        "contract": {
            "id": "CON.F.US.ES.H25",
            "tick_size": 0.25,
            "tick_value": 12.50,
            "point_value": 50.00
        },
        "position": {
            "type": 2,  # SHORT
            "size": 1,
            "entry_price": 5000.00
        },
        "quote": {
            "last": 4950.00
        },
        "expected_pnl": 625.00  # 12.5 points * $50/point * 1 contract
    }
