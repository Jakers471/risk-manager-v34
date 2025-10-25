"""
Test that RiskEngine is properly wired to TradingIntegration for enforcement.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from risk_manager.core.config import RiskConfig
from risk_manager.core.engine import RiskEngine
from risk_manager.core.events import EventBus


@pytest.mark.asyncio
class TestEnforcementWiring:
    """Test enforcement wiring between RiskEngine and TradingIntegration."""

    async def test_engine_accepts_trading_integration(self):
        """Test that RiskEngine can be initialized with trading_integration."""
        config = RiskConfig()
        event_bus = EventBus()
        mock_trading = AsyncMock()

        # Create engine with trading_integration
        engine = RiskEngine(config, event_bus, trading_integration=mock_trading)

        assert engine.trading_integration is mock_trading

    async def test_flatten_all_calls_trading_integration(self):
        """Test that flatten_all_positions() calls trading_integration.flatten_all()."""
        config = RiskConfig()
        event_bus = EventBus()
        mock_trading = AsyncMock()

        # Create engine with mock trading integration
        engine = RiskEngine(config, event_bus, trading_integration=mock_trading)
        engine.running = True

        # Call flatten_all_positions
        await engine.flatten_all_positions()

        # Verify it called the trading integration
        mock_trading.flatten_all.assert_called_once()

    async def test_flatten_all_without_trading_integration(self):
        """Test that flatten_all_positions() doesn't crash without trading_integration."""
        config = RiskConfig()
        event_bus = EventBus()

        # Create engine WITHOUT trading integration
        engine = RiskEngine(config, event_bus, trading_integration=None)
        engine.running = True

        # Call flatten_all_positions - should not crash
        await engine.flatten_all_positions()

        # Should complete without error (just logs warning)

    async def test_enforcement_from_violation(self):
        """Test complete flow: violation → enforcement → SDK call."""
        config = RiskConfig()
        event_bus = EventBus()
        mock_trading = AsyncMock()

        # Create engine
        engine = RiskEngine(config, event_bus, trading_integration=mock_trading)
        engine.running = True

        # Simulate a rule violation that triggers flatten
        violation = {
            "action": "flatten",
            "reason": "daily_loss_limit_exceeded",
            "limit": -500.0,
            "current": -550.0,
        }

        # Mock rule
        mock_rule = MagicMock()
        mock_rule.__class__.__name__ = "DailyLossRule"

        # Handle violation (this should call flatten_all_positions)
        await engine._handle_violation(mock_rule, violation)

        # Verify SDK's flatten_all was called
        mock_trading.flatten_all.assert_called_once()
