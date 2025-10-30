"""
Market Data Handler Module

Handles real-time market data from the ProjectX SDK:
- Quote updates (bid/ask prices)
- Trade ticks
- OHLC bars
- Price polling
- Status bar display

This module solves the "quote events don't fire" problem by implementing
price polling as a backup mechanism for P&L calculations.

The Challenge:
    - SDK SHOULD emit QUOTE_UPDATE events for bid/ask prices
    - In practice, these events often don't fire (SDK limitation)
    - Without prices, unrealized P&L calculations fail
    - Rules depending on P&L (RULE-004, RULE-005) don't work

The Solution:
    - Primary: Subscribe to QUOTE_UPDATE events (fast when they work)
    - Fallback: Poll instrument.last_price every 0.5s (background task)
    - Hybrid: Use whichever provides data
    - Status bar: Display live P&L updates

Usage:
    # Initialize
    handler = MarketDataHandler(
        pnl_calculator=pnl_calc,
        event_bus=event_bus,
        instruments=["MNQ", "ES"]
    )

    # Set SDK references (after connection)
    handler.set_client(client)
    handler.set_suite(suite)

    # Register event handlers
    suite.realtime.on(RealtimeEvent.QUOTE_UPDATE, handler.handle_quote_update)

    # Start status bar
    await handler.start_status_bar()

    # Stop status bar
    await handler.stop_status_bar()
"""

import asyncio
from typing import Any
from loguru import logger

from risk_manager.core.events import EventBus, RiskEvent, EventType


class MarketDataHandler:
    """
    Handle market data from SDK and update P&L calculations.

    This class provides:
    1. Quote update handling (bid/ask prices)
    2. Alternative market data sources (trade ticks, bars)
    3. Price polling (fallback when quote events don't fire)
    4. Status bar display (live P&L updates)
    """

    def __init__(
        self,
        pnl_calculator,
        event_bus: EventBus,
        instruments: list[str],
    ):
        """
        Initialize market data handler.

        Args:
            pnl_calculator: UnrealizedPnLCalculator instance
            event_bus: Event bus for publishing risk events
            instruments: List of instrument symbols (e.g., ["MNQ", "ES"])
        """
        self.pnl_calculator = pnl_calculator
        self.event_bus = event_bus
        self.instruments = instruments

        # SDK references (set after connection)
        self._client = None
        self._suite = None

        # Running state
        self._running = False

        # Status bar task
        self._status_bar_task = None

    def set_client(self, client):
        """
        Set SDK client reference.

        Args:
            client: ProjectX client instance
        """
        self._client = client

    def set_suite(self, suite):
        """
        Set SDK suite reference.

        Args:
            suite: TradingSuite instance
        """
        self._suite = suite

    # ========================================================================
    # Event Handlers (called by SDK via realtime subscriptions)
    # ========================================================================

    async def handle_quote_update(self, event: Any) -> None:
        """
        Handle market quote update from SignalR.

        Quote updates provide real-time bid/ask prices needed for:
        - Unrealized PnL calculations
        - RULE-004 (Daily Unrealized Loss)
        - RULE-005 (Max Unrealized Profit)
        - Position monitoring

        NOTE: This fires MULTIPLE TIMES PER SECOND. Logging is DEBUG only.

        Data structure (from SDK v3.5.9):
        event.data = {
            'symbol': 'F.US.MNQ',  # Full contract format
            'last_price': 0.0,      # Often zero
            'bid': 26271.00,        # Valid
            'ask': 26271.75         # Valid
        }

        Args:
            event: Quote update event from SDK
        """
        try:
            # Extract quote data from event
            if not hasattr(event, 'data'):
                logger.debug(f"Quote event has no data attribute: {type(event)}")
                logger.debug(f"Event attributes: {dir(event)}")
                return

            quote_data = event.data

            # Validate quote_data is a dict
            if not isinstance(quote_data, dict):
                logger.debug(f"Quote data is not a dict: {type(quote_data)}, value: {quote_data}")
                return

            # Extract quote details with safe defaults
            full_symbol = quote_data.get('symbol', 'UNKNOWN')
            bid = float(quote_data.get('bid', 0.0) or 0.0)
            ask = float(quote_data.get('ask', 0.0) or 0.0)
            last_price = float(quote_data.get('last_price', 0.0) or 0.0)

            # Strip "F.US." prefix to get just "MNQ", "ES", etc.
            # F.US.MNQ → MNQ
            if isinstance(full_symbol, str):
                symbol = full_symbol.replace('F.US.', '') if 'F.US.' in full_symbol else full_symbol
            else:
                logger.debug(f"Symbol is not a string: {type(full_symbol)}, value: {full_symbol}")
                return

            # Use last_price if available, otherwise use bid/ask midpoint
            if last_price and last_price > 0:
                market_price = last_price
            elif bid > 0 and ask > 0:
                market_price = (bid + ask) / 2.0
            else:
                # No valid price data
                logger.debug(f"No valid price for {symbol}: last={last_price}, bid={bid}, ask={ask}")
                return

            # DEBUG logging only - quote updates are too frequent for INFO
            logger.debug(f"Quote: {symbol} @ ${market_price:.2f} (bid: ${bid:.2f}, ask: ${ask:.2f})")

            # Update unrealized P&L calculator (silent)
            self.pnl_calculator.update_quote(symbol, market_price)

            # Check if any position has significant P&L change
            # Only emit UNREALIZED_PNL_UPDATE if P&L changed by $10+
            positions_to_check = self.pnl_calculator.get_positions_by_symbol(symbol)
            for contract_id in positions_to_check:
                if self.pnl_calculator.has_significant_pnl_change(contract_id, threshold=10.0):
                    # Get updated P&L
                    unrealized_pnl = self.pnl_calculator.calculate_unrealized_pnl(contract_id)
                    if unrealized_pnl is not None:
                        # Emit unrealized P&L update event
                        await self.event_bus.publish(RiskEvent(
                            event_type=EventType.UNREALIZED_PNL_UPDATE,
                            data={
                                'account_id': self._client.account_info.id if self._client else None,  # ← CRITICAL: Rules need account_id
                                'contract_id': contract_id,
                                'contractId': contract_id,  # ← CRITICAL: Rules need contractId (for enforcement)
                                'symbol': symbol,
                                'unrealized_pnl': float(unrealized_pnl),
                            },
                            source="trading_sdk"
                        ))
                        logger.info(f"💹 Unrealized P&L update: {symbol} ${float(unrealized_pnl):+.2f}")

            # Also publish MARKET_DATA_UPDATED for backward compatibility
            risk_event = RiskEvent(
                event_type=EventType.MARKET_DATA_UPDATED,
                data={
                    "symbol": symbol,
                    "price": market_price,
                    "bid": bid,
                    "ask": ask,
                    "last": last_price,
                    "timestamp": quote_data.get('timestamp'),
                },
                source="trading_sdk",
            )

            await self.event_bus.publish(risk_event)

        except Exception as e:
            logger.error(f"Error handling quote update: {e}")
            logger.exception(e)

    async def handle_data_update(self, data: Any) -> None:
        """
        Handle DATA_UPDATE event (alternative market data source).

        This might contain price/quote data if QUOTE_UPDATE doesn't work.

        Args:
            data: Data update event from SDK
        """
        try:
            logger.debug(f"_on_data_update called: data type={type(data)}")
            logger.debug(f"DATA_UPDATE content: {data}")

            # Try to extract price information
            # Data structure is unknown, so we'll log it and adapt
            if hasattr(data, '__dict__'):
                logger.debug(f"DATA_UPDATE attributes: {data.__dict__}")

        except Exception as e:
            logger.error(f"Error handling data update: {e}")

    async def handle_trade_tick(self, data: Any) -> None:
        """
        Handle TRADE_TICK event (trade executions with prices).

        Might provide market price information from actual trades.

        Args:
            data: Trade tick event from SDK
        """
        try:
            logger.debug(f"_on_trade_tick called: data type={type(data)}")
            logger.debug(f"TRADE_TICK content: {data}")

            # Try to extract price information
            if hasattr(data, '__dict__'):
                logger.debug(f"TRADE_TICK attributes: {data.__dict__}")
            elif isinstance(data, dict):
                symbol = data.get('symbol')
                price = data.get('price') or data.get('last') or data.get('tradePrice')
                if symbol and price:
                    logger.debug(f"Trade tick: {symbol} @ ${price:.2f}")
                    # Update P&L calculator
                    self.pnl_calculator.update_quote(symbol, price)

        except Exception as e:
            logger.error(f"Error handling trade tick: {e}")

    async def handle_new_bar(self, data: Any) -> None:
        """
        Handle NEW_BAR event (from 1min/5min timeframes).

        Bars contain OHLC data - we can use close price for P&L calculations.
        This fires every 1 minute and 5 minutes based on our timeframes.

        Args:
            data: New bar event from SDK
        """
        try:
            logger.debug(f"_on_new_bar called: data type={type(data)}")

            # Extract bar data (structure varies by SDK version)
            if hasattr(data, 'data'):
                bar_data = data.data
            elif isinstance(data, dict):
                bar_data = data
            else:
                bar_data = data

            # Try to extract symbol and close price
            symbol = None
            close_price = None

            if hasattr(bar_data, '__dict__'):
                attrs = bar_data.__dict__
                symbol = attrs.get('symbol')
                close_price = attrs.get('close') or attrs.get('closePrice')
                logger.debug(f"NEW_BAR attributes: {list(attrs.keys())}")
            elif isinstance(bar_data, dict):
                symbol = bar_data.get('symbol')
                close_price = bar_data.get('close') or bar_data.get('closePrice')

            if symbol and close_price:
                logger.debug(f"Bar complete: {symbol} close @ ${close_price:.2f}")
                # Update P&L calculator with bar close price
                self.pnl_calculator.update_quote(symbol, close_price)

        except Exception as e:
            logger.error(f"Error handling new bar: {e}")

    # ========================================================================
    # Status Bar (Background Task)
    # ========================================================================

    async def start_status_bar(self) -> None:
        """
        Start the status bar update task.

        Creates a background task that updates unrealized P&L display
        every 0.5 seconds and polls prices as fallback.
        """
        if self._status_bar_task and not self._status_bar_task.done():
            logger.warning("Status bar task already running")
            return

        self._running = True
        self._status_bar_task = asyncio.create_task(self._update_status_bar())
        logger.debug("Status bar task started")

    async def stop_status_bar(self) -> None:
        """
        Stop the status bar update task.

        Cancels the background task gracefully.
        """
        self._running = False

        if self._status_bar_task and not self._status_bar_task.done():
            self._status_bar_task.cancel()
            try:
                await self._status_bar_task
            except asyncio.CancelledError:
                pass
            logger.debug("Status bar task stopped")

    async def _update_status_bar(self) -> None:
        """
        Background task that updates the unrealized P&L status bar.

        Updates every 0.5 seconds with current unrealized P&L.
        Uses carriage return (\\r) to overwrite the same line.

        When other logs print, they interrupt the status bar (new line),
        but the status bar resumes on the next update. Since position/rule
        logs are infrequent, this creates a clean display.

        ALSO POLLS PRICES: Since quote events don't fire, we poll
        instrument.last_price every 0.5s to update the calculator.
        """
        logger.debug("Status bar update task started")
        poll_count = 0
        prices_found = False

        while self._running:
            try:
                # Poll prices from instruments (since quote events don't fire)
                if self._suite:
                    for symbol in self.instruments:
                        try:
                            instrument = self._suite.get(symbol)
                            if instrument and hasattr(instrument, 'last_price'):
                                price = instrument.last_price
                                if price and price > 0:
                                    # Update calculator with polled price
                                    self.pnl_calculator.update_quote(symbol, price)
                                    logger.debug(f"Polled price: {symbol} @ ${price:.2f}")
                                    if not prices_found:
                                        prices_found = True
                                        logger.info(f"💹 Price polling active: {symbol} @ ${price:.2f}")
                                else:
                                    # Log when prices are None/0 (but only occasionally)
                                    if poll_count % 10 == 0:  # Every 5 seconds
                                        logger.debug(f"Polled {symbol}: last_price is None/0")
                        except Exception as e:
                            logger.debug(f"Error polling price for {symbol}: {e}")

                poll_count += 1

                # Calculate total unrealized P&L
                total_pnl = self.pnl_calculator.calculate_total_unrealized_pnl()

                # Print status bar (overwrites same line)
                # \r = carriage return, end='' prevents newline, flush=True ensures immediate print
                print(f"\r📊 Unrealized P&L: ${float(total_pnl):+.2f}  ", end="", flush=True)

                # Wait 0.5 seconds before next update
                await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                logger.debug("Status bar task cancelled")
                print()  # Print newline to move cursor to next line
                break
            except Exception as e:
                logger.debug(f"Error in status bar update: {e}")
                await asyncio.sleep(1.0)  # Back off on error
