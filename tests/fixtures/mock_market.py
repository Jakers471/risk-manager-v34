"""Mock market simulator for realistic testing without live market connections

This module provides market simulation capabilities for testing trading systems
with realistic market conditions, price movements, and order execution.

Based on the integration-tester agent pattern from project-x-py SDK.
"""
import asyncio
import random
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
import pytest


@dataclass
class MarketTick:
    """Represents a single market tick"""
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    timestamp: datetime


@dataclass
class OrderFill:
    """Represents an order fill"""
    size: int
    price: Decimal
    timestamp: datetime


@dataclass
class SimulatedOrder:
    """Simulated order with execution details"""
    id: str
    contract_id: str
    side: int  # 0=Buy, 1=Sell
    type: str  # 'market', 'limit', 'stop'
    size: int
    price: Optional[Decimal] = None
    status: str = 'pending'
    placed_at: datetime = field(default_factory=datetime.now)
    fills: List[OrderFill] = field(default_factory=list)
    avg_fill_price: Optional[Decimal] = None


class MarketSimulator:
    """Generate realistic market data for testing

    Simulates market price movements with configurable volatility and trends.
    Provides tick streams, order book generation, and realistic price action.

    Example:
        >>> sim = MarketSimulator("MNQ", Decimal("20000"))
        >>> sim.volatility = 0.02  # 2% volatility
        >>> async for tick in sim.generate_tick_stream(rate=10):
        ...     print(f"{tick.symbol}: {tick.last}")
    """

    def __init__(self, symbol: str, base_price: Decimal):
        self.symbol = symbol
        self.base_price = base_price
        self.current_price = base_price
        self.volatility = 0.02  # 2% volatility
        self.trend = 0.0  # No trend by default
        self.spread_pct = Decimal("0.00125")  # 0.125% spread (~$25 for MNQ)

    async def generate_tick_stream(
        self,
        rate: int = 100,
        max_ticks: Optional[int] = None
    ) -> AsyncGenerator[MarketTick, None]:
        """Generate realistic tick data at specified rate

        Args:
            rate: Ticks per second
            max_ticks: Maximum number of ticks to generate (None = infinite)

        Yields:
            MarketTick objects with bid/ask/last prices
        """
        tick_count = 0

        while True:
            if max_ticks and tick_count >= max_ticks:
                break

            # Random walk with trend using normal distribution
            change = random.gauss(self.trend, self.volatility / 100)
            self.current_price *= Decimal(str(1 + change))

            # Add market microstructure (bid/ask spread)
            spread = self.current_price * self.spread_pct
            bid = self.current_price - spread / 2
            ask = self.current_price + spread / 2

            tick = MarketTick(
                symbol=self.symbol,
                bid=bid.quantize(Decimal("0.25")),  # Round to tick size
                ask=ask.quantize(Decimal("0.25")),
                last=self.current_price.quantize(Decimal("0.25")),
                volume=random.randint(1, 100),
                timestamp=datetime.now()
            )

            yield tick
            tick_count += 1
            await asyncio.sleep(1 / rate)

    async def generate_orderbook(self, levels: int = 10) -> Dict:
        """Generate realistic order book

        Args:
            levels: Number of price levels on each side

        Returns:
            Dict with 'bids' and 'asks' lists
        """
        bids = []
        asks = []

        tick_size = Decimal("0.25")

        for i in range(levels):
            bid_price = self.current_price - Decimal(str(i)) * tick_size
            ask_price = self.current_price + Decimal(str(i)) * tick_size

            # Larger size at better prices (more liquidity near market)
            bid_size = random.randint(10, 100) * (levels - i)
            ask_size = random.randint(10, 100) * (levels - i)

            bids.append({"price": bid_price, "size": bid_size})
            asks.append({"price": ask_price, "size": ask_size})

        return {"bids": bids, "asks": asks}

    def set_trending_market(self):
        """Configure for trending market conditions"""
        self.trend = 0.001  # Uptrend
        self.volatility = 0.01  # Low volatility

    def set_volatile_market(self):
        """Configure for volatile market conditions"""
        self.trend = 0.0
        self.volatility = 0.05  # High volatility

    async def simulate_flash_crash(self, drop_pct: float = 0.05, recovery_seconds: float = 1.0):
        """Simulate a flash crash event

        Args:
            drop_pct: Percentage drop (0.05 = 5%)
            recovery_seconds: Time to recover
        """
        original_price = self.current_price
        self.current_price *= Decimal(str(1 - drop_pct))
        await asyncio.sleep(recovery_seconds)
        self.current_price = original_price


class OrderSimulator:
    """Simulate order execution with realistic fills

    Provides realistic order execution simulation including:
    - Market orders with slippage
    - Limit orders with price checking
    - Stop orders with activation logic
    - Partial fills
    - Position tracking

    Example:
        >>> market = MarketSimulator("MNQ", Decimal("20000"))
        >>> order_sim = OrderSimulator(market)
        >>> order = await order_sim.place_order({
        ...     'contract_id': 'MNQ',
        ...     'type': 'market',
        ...     'side': 0,
        ...     'size': 1
        ... })
    """

    def __init__(self, market_simulator: MarketSimulator):
        self.market = market_simulator
        self.orders: Dict[str, SimulatedOrder] = {}
        self.positions: Dict[str, int] = {}
        self.slippage_pct = Decimal("0.001")  # 0.1% slippage

    async def place_order(self, order_dict: Dict) -> SimulatedOrder:
        """Simulate order placement

        Args:
            order_dict: Dict with order parameters

        Returns:
            SimulatedOrder with execution details
        """
        order_id = str(uuid.uuid4())

        order = SimulatedOrder(
            id=order_id,
            contract_id=order_dict['contract_id'],
            side=order_dict['side'],
            type=order_dict.get('type', 'market'),
            size=order_dict['size'],
            price=order_dict.get('price'),
            status='pending',
            placed_at=datetime.now()
        )

        self.orders[order_id] = order

        # Simulate processing delay (network latency)
        await asyncio.sleep(random.uniform(0.01, 0.05))

        # Check if order should fill
        if await self._should_fill(order):
            return await self._fill_order(order)
        else:
            order.status = 'working'
            return order

    async def _should_fill(self, order: SimulatedOrder) -> bool:
        """Determine if order should fill based on current market price"""
        if order.type == 'market':
            return True

        if order.type == 'limit':
            if order.side == 0:  # Buy
                return order.price >= self.market.current_price
            else:  # Sell
                return order.price <= self.market.current_price

        if order.type == 'stop':
            if order.side == 0:  # Buy stop
                return order.price <= self.market.current_price
            else:  # Sell stop
                return order.price >= self.market.current_price

        return False

    async def _fill_order(self, order: SimulatedOrder) -> SimulatedOrder:
        """Simulate order fill with realistic partial fills"""
        fills = []
        remaining = order.size

        # Simulate 1-3 partial fills
        num_fills = random.randint(1, min(3, order.size))

        for i in range(num_fills):
            if i == num_fills - 1:
                # Last fill gets remaining quantity
                fill_size = remaining
            else:
                # Partial fill
                fill_size = random.randint(1, remaining // 2 + 1)

            fill_price = self._get_fill_price(order)

            fills.append(OrderFill(
                size=fill_size,
                price=fill_price,
                timestamp=datetime.now()
            ))

            remaining -= fill_size

            # Simulate fill delay
            if i < num_fills - 1:
                await asyncio.sleep(random.uniform(0.001, 0.01))

        order.status = 'filled'
        order.fills = fills
        order.avg_fill_price = sum(
            f.price * f.size for f in fills
        ) / Decimal(str(order.size))

        # Update position
        self._update_position(order)

        return order

    def _get_fill_price(self, order: SimulatedOrder) -> Decimal:
        """Calculate fill price with slippage"""
        if order.type == 'market':
            # Market orders have slippage
            slippage = self.market.current_price * self.slippage_pct
            if order.side == 0:  # Buy
                return self.market.current_price + slippage
            else:  # Sell
                return self.market.current_price - slippage
        else:
            # Limit orders fill at limit price or better
            return order.price

    def _update_position(self, order: SimulatedOrder):
        """Update position tracking"""
        symbol = order.contract_id
        if symbol not in self.positions:
            self.positions[symbol] = 0

        if order.side == 0:  # Buy
            self.positions[symbol] += order.size
        else:  # Sell
            self.positions[symbol] -= order.size

    def get_position(self, symbol: str) -> int:
        """Get current position for symbol"""
        return self.positions.get(symbol, 0)


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture
async def market_simulator():
    """Provide market simulator for tests"""
    sim = MarketSimulator("MNQ", Decimal("20000"))
    yield sim
    # Cleanup if needed


@pytest.fixture
async def order_simulator(market_simulator):
    """Provide order simulator for tests"""
    order_sim = OrderSimulator(market_simulator)
    yield order_sim


@pytest.fixture
def sample_tick():
    """Provide a sample market tick"""
    return MarketTick(
        symbol="MNQ",
        bid=Decimal("19999.75"),
        ask=Decimal("20000.25"),
        last=Decimal("20000.00"),
        volume=50,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_orderbook():
    """Provide sample orderbook data"""
    return {
        "bids": [
            {"price": Decimal("19999.75"), "size": 50},
            {"price": Decimal("19999.50"), "size": 75},
            {"price": Decimal("19999.25"), "size": 100}
        ],
        "asks": [
            {"price": Decimal("20000.25"), "size": 45},
            {"price": Decimal("20000.50"), "size": 80},
            {"price": Decimal("20000.75"), "size": 120}
        ]
    }


@pytest.fixture
async def trading_suite_mock(market_simulator, order_simulator):
    """Provide mocked trading suite with market simulation

    This is a placeholder for integration with the actual TradingSuite.
    Modify as needed to match your actual trading suite implementation.
    """
    # This would be replaced with actual TradingSuite mock
    mock_suite = {
        'market': market_simulator,
        'orders': order_simulator,
        'symbol': market_simulator.symbol
    }
    yield mock_suite
    # Cleanup


# ============================================================================
# MARKET SCENARIO HELPERS
# ============================================================================

class MarketScenarios:
    """Pre-configured market scenarios for testing

    Use these to quickly set up different market conditions:
    - Trending markets
    - Volatile/choppy markets
    - Flash crashes
    - Low liquidity
    """

    @staticmethod
    def apply_trending(simulator: MarketSimulator):
        """Apply trending market conditions"""
        simulator.set_trending_market()

    @staticmethod
    def apply_volatile(simulator: MarketSimulator):
        """Apply volatile market conditions"""
        simulator.set_volatile_market()

    @staticmethod
    async def apply_flash_crash(simulator: MarketSimulator):
        """Apply flash crash scenario"""
        await simulator.simulate_flash_crash()

    @staticmethod
    def apply_low_liquidity(simulator: MarketSimulator):
        """Apply low liquidity conditions (wide spreads)"""
        simulator.spread_pct = Decimal("0.005")  # 0.5% spread (wide)
