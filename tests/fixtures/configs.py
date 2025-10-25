"""Risk configuration YAML fixtures for testing rule configurations

All fixtures return parsed YAML configuration dictionaries.
"""
import pytest


@pytest.fixture
def risk_config_all_enabled():
    """Full configuration with all 12 rules enabled (default values)"""
    return {
        "global": {
            "strict_mode": False,
            "logging_level": "INFO"
        },
        "rules": {
            "max_contracts": {
                "enabled": True,
                "limit": 5,
                "count_type": "net"
            },
            "max_contracts_per_instrument": {
                "enabled": True,
                "limits": {
                    "MNQ": 2,
                    "NQ": 1,
                    "ES": 1,
                    "MES": 3
                },
                "enforcement": "reduce_to_limit",
                "unknown_symbol_action": "allow_with_limit:1"
            },
            "daily_realized_loss": {
                "enabled": True,
                "loss_limit": 500.00,
                "action": "CLOSE_ALL_AND_LOCKOUT",
                "lockout_until": "daily_reset"
            },
            "daily_unrealized_loss": {
                "enabled": True,
                "loss_limit": 300.00,
                "scope": "per_position",
                "action": "CLOSE_POSITION",
                "lockout": False
            },
            "max_unrealized_profit": {
                "enabled": True,
                "mode": "profit_target",
                "profit_target": 1000.00,
                "scope": "per_position",
                "action": "CLOSE_POSITION"
            },
            "trade_frequency_limit": {
                "enabled": True,
                "max_trades": 30,
                "time_window_minutes": 60
            },
            "cooldown_after_loss": {
                "enabled": True,
                "loss_threshold": 100.00,
                "cooldown_seconds": 300
            },
            "no_stop_loss_grace": {
                "enabled": True,
                "grace_period_seconds": 30,
                "action": "CLOSE_POSITION"
            },
            "session_block_outside": {
                "enabled": True,
                "allowed_hours": {
                    "start": "08:30",
                    "end": "15:00"
                },
                "timezone": "America/Chicago",
                "action": "CANCEL_ORDER"
            },
            "auth_loss_guard": {
                "enabled": True,
                "action": "CLOSE_ALL_AND_LOCKOUT"
            },
            "symbol_blocks": {
                "enabled": True,
                "blocked_symbols": ["RTY", "BTC"],
                "action": "CANCEL_ORDER",
                "close_existing": True
            },
            "trade_management": {
                "enabled": False,
                "auto_stop_loss": True,
                "stop_loss_ticks": 10
            }
        }
    }


@pytest.fixture
def risk_config_minimal():
    """Minimal configuration (only 3 critical rules enabled)"""
    return {
        "rules": {
            "max_contracts": {
                "enabled": True,
                "limit": 5
            },
            "max_contracts_per_instrument": {
                "enabled": True,
                "limits": {
                    "MNQ": 3,
                    "ES": 2
                }
            },
            "session_block_outside": {
                "enabled": True,
                "allowed_hours": {
                    "start": "09:30",
                    "end": "16:00"
                },
                "timezone": "America/New_York"
            }
        }
    }


@pytest.fixture
def risk_config_strict_mode():
    """Strict mode enabled (all breaches = permanent lockout)"""
    return {
        "global": {
            "strict_mode": True,
            "logging_level": "WARNING"
        },
        "rules": {
            "max_contracts": {
                "enabled": True,
                "limit": 3
            },
            "daily_realized_loss": {
                "enabled": True,
                "loss_limit": 300.00
            }
        }
    }


@pytest.fixture
def risk_config_all_disabled():
    """All rules disabled (testing bypass scenario)"""
    return {
        "rules": {
            "max_contracts": {"enabled": False},
            "max_contracts_per_instrument": {"enabled": False},
            "daily_realized_loss": {"enabled": False},
            "daily_unrealized_loss": {"enabled": False},
            "max_unrealized_profit": {"enabled": False},
            "trade_frequency_limit": {"enabled": False},
            "cooldown_after_loss": {"enabled": False},
            "no_stop_loss_grace": {"enabled": False},
            "session_block_outside": {"enabled": False},
            "auth_loss_guard": {"enabled": False},
            "symbol_blocks": {"enabled": False},
            "trade_management": {"enabled": False}
        }
    }


@pytest.fixture
def risk_config_aggressive_limits():
    """Aggressive limits (tight risk controls)"""
    return {
        "rules": {
            "max_contracts": {
                "enabled": True,
                "limit": 2
            },
            "max_contracts_per_instrument": {
                "enabled": True,
                "limits": {
                    "MNQ": 1,
                    "ES": 1,
                    "NQ": 1
                }
            },
            "daily_realized_loss": {
                "enabled": True,
                "loss_limit": 200.00
            },
            "daily_unrealized_loss": {
                "enabled": True,
                "loss_limit": 150.00,
                "scope": "per_position"
            },
            "max_unrealized_profit": {
                "enabled": True,
                "mode": "profit_target",
                "profit_target": 500.00
            },
            "trade_frequency_limit": {
                "enabled": True,
                "max_trades": 10,
                "time_window_minutes": 60
            },
            "cooldown_after_loss": {
                "enabled": True,
                "loss_threshold": 50.00,
                "cooldown_seconds": 600
            }
        }
    }


@pytest.fixture
def risk_config_permissive_limits():
    """Permissive limits (loose risk controls)"""
    return {
        "rules": {
            "max_contracts": {
                "enabled": True,
                "limit": 10
            },
            "max_contracts_per_instrument": {
                "enabled": True,
                "limits": {
                    "MNQ": 5,
                    "ES": 3,
                    "NQ": 2
                }
            },
            "daily_realized_loss": {
                "enabled": True,
                "loss_limit": 1000.00
            },
            "daily_unrealized_loss": {
                "enabled": True,
                "loss_limit": 800.00,
                "scope": "total"
            },
            "trade_frequency_limit": {
                "enabled": True,
                "max_trades": 100,
                "time_window_minutes": 60
            }
        }
    }


@pytest.fixture
def risk_config_breakeven_mode():
    """Max unrealized profit in breakeven mode"""
    return {
        "rules": {
            "max_unrealized_profit": {
                "enabled": True,
                "mode": "breakeven",
                "scope": "per_position",
                "action": "CLOSE_POSITION"
            }
        }
    }


@pytest.fixture
def risk_config_total_unrealized():
    """Daily unrealized loss in 'total' scope mode"""
    return {
        "rules": {
            "daily_unrealized_loss": {
                "enabled": True,
                "loss_limit": 500.00,
                "scope": "total",
                "action": "CLOSE_ALL_AND_LOCKOUT",
                "lockout": True
            }
        }
    }


@pytest.fixture
def risk_config_24_7_trading():
    """24/7 trading (no session restrictions)"""
    return {
        "rules": {
            "session_block_outside": {
                "enabled": True,
                "allowed_hours": {
                    "start": "00:00",
                    "end": "23:59"
                },
                "timezone": "UTC"
            }
        }
    }


@pytest.fixture
def risk_config_trade_management_enabled():
    """Trade management rule enabled (auto stop-loss)"""
    return {
        "rules": {
            "trade_management": {
                "enabled": True,
                "auto_stop_loss": True,
                "stop_loss_ticks": 15
            }
        }
    }


@pytest.fixture
def risk_config_invalid_yaml():
    """Invalid configuration (testing validation)"""
    return {
        "rules": {
            "max_contracts": {
                "enabled": True,
                "limit": -5  # Invalid: negative limit
            },
            "daily_realized_loss": {
                "enabled": True,
                "loss_limit": "not_a_number"  # Invalid: string instead of float
            }
        }
    }


@pytest.fixture
def risk_config_missing_required_fields():
    """Configuration with missing required fields"""
    return {
        "rules": {
            "max_contracts": {
                "enabled": True
                # Missing 'limit' field
            }
        }
    }
