"""
End-to-End Performance & Latency Tests

Tests the system's performance characteristics under load:
- Event processing latency (event → rule evaluation)
- Enforcement execution latency (violation → SDK call)
- High-frequency event handling (100 events in 10s)

Validates performance targets:
- Event processing: <50ms (p50), <100ms (p99)
- Enforcement execution: <200ms (p50), <500ms (p99)
- Throughput: Handle 100 events/10s without drops

Uses mocked SDK to simulate real trading scenarios with precise timing.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock
from statistics import quantiles
from datetime import datetime

# Risk Manager imports
from risk_manager.core.manager import RiskManager
from risk_manager.core.events import EventBus, EventType, RiskEvent
from risk_manager.core.config import RiskConfig
from risk_manager.rules import MaxPositionRule


class MockPosition:
    """Mock SDK Position object."""

    def __init__(self, size=0, symbol="MNQ", avg_price=16500.0):
        self.size = size
        self.symbol = symbol
        self.averagePrice = avg_price
        self.unrealizedPnl = 0.0
        self.realizedPnl = 0.0
        self.contractId = f"CON.F.US.{symbol}.Z25"
        self.id = 1
        self.accountId = 12345


class MockTradingSuite:
    """Mock SDK TradingSuite."""

    def __init__(self):
        self.event_bus = EventBus()
        self._positions = []
        self.account_info = Mock()
        self.account_info.id = "PRAC-V2-126244-84184528"
        self.account_info.name = "150k Practice Account"
        self.enforcement_call_times = []  # Track enforcement timing

    def __getitem__(self, symbol):
        """Return mock instrument context."""
        context = Mock()
        context.positions = Mock()
        context.positions.get_all_positions = AsyncMock(return_value=self._positions)

        # Track when close_all_positions is called
        async def timed_close_all():
            self.enforcement_call_times.append(time.perf_counter())

        context.positions.close_all_positions = AsyncMock(side_effect=timed_close_all)
        context.instrument_info = Mock()
        context.instrument_info.name = symbol
        context.instrument_info.id = f"CON.F.US.{symbol}.Z25"
        return context

    async def on(self, event_type, handler):
        """Subscribe to event."""
        self.event_bus.subscribe(event_type, handler)

    async def disconnect(self):
        """Mock disconnect."""
        pass

    @property
    def is_connected(self):
        """Mock connection status."""
        return True


@pytest.mark.e2e
class TestPerformanceE2E:
    """End-to-end performance and latency tests."""

    @pytest.fixture
    def mock_sdk_suite(self):
        """Create mock SDK suite."""
        return MockTradingSuite()

    @pytest.fixture
    async def risk_manager(self, mock_sdk_suite):
        """Create simplified risk system for e2e performance testing."""
        # Create components directly (without full RiskManager)
        config = RiskConfig(
            project_x_api_key="test_api_key",
            project_x_username="test_user",
            max_contracts=2,
            enforcement_latency_target_ms=200
        )
        event_bus = EventBus()

        # Mock trading integration
        mock_trading = AsyncMock()
        mock_trading.flatten_all = AsyncMock()
        mock_trading.flatten_position = AsyncMock()
        mock_trading.suite = mock_sdk_suite

        # Create engine with mock trading
        from risk_manager.core.engine import RiskEngine
        engine = RiskEngine(config, event_bus, mock_trading)

        # Add max position rule
        rule = MaxPositionRule(max_contracts=2, action="flatten")
        engine.add_rule(rule)

        # Start engine
        await engine.start()

        # Create a simple container object
        class SimpleRiskManager:
            def __init__(self):
                self.config = config
                self.event_bus = event_bus
                self.engine = engine
                self.trading_integration = mock_trading

        rm = SimpleRiskManager()

        yield rm

        # Cleanup
        await engine.stop()

    # ========================================================================
    # Test 1: Event Processing Latency
    # ========================================================================

    @pytest.mark.asyncio
    async def test_event_processing_latency(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test event processing latency meets performance targets.

        Measures time from event received to rule evaluation complete.
        Target: <50ms (p50), <100ms (p99)
        """
        # Given: System monitoring position updates
        latencies = []

        # Track when rule evaluation completes
        evaluation_times = []

        async def track_evaluation(event):
            """Track when rule evaluation completes."""
            evaluation_times.append(time.perf_counter())

        risk_manager.event_bus.subscribe(
            EventType.POSITION_UPDATED,
            track_evaluation
        )

        # When: Process 100 position update events
        num_events = 100

        for i in range(num_events):
            # Vary position size to keep it interesting
            size = 1 + (i % 2)  # Alternate between 1 and 2
            mock_sdk_suite._positions = [MockPosition(size=size)]
            risk_manager.engine.current_positions = {
                "MNQ": {"size": size, "side": "long"}
            }

            event = RiskEvent(
                event_type=EventType.POSITION_UPDATED,
                data={"symbol": "MNQ", "size": size, "unrealizedPnl": 50.0}
            )

            # Measure: Time from event publish to evaluation complete
            start_time = time.perf_counter()
            await risk_manager.event_bus.publish(event)
            await risk_manager.engine.evaluate_rules(event)

            # Wait for async handlers to complete
            await asyncio.sleep(0.001)

            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

        # Then: Calculate percentiles
        assert len(latencies) == num_events, "Some events were not processed"

        # Sort for percentile calculation
        latencies_sorted = sorted(latencies)

        # Calculate p50 (median) and p99
        p50_index = len(latencies_sorted) // 2
        p99_index = int(len(latencies_sorted) * 0.99)

        p50_latency = latencies_sorted[p50_index]
        p99_latency = latencies_sorted[p99_index]

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)

        print(f"\n{'='*60}")
        print(f"Event Processing Latency Results (n={num_events}):")
        print(f"{'='*60}")
        print(f"  Min:     {min_latency:6.2f}ms")
        print(f"  Average: {avg_latency:6.2f}ms")
        print(f"  Median:  {p50_latency:6.2f}ms (p50)")
        print(f"  p99:     {p99_latency:6.2f}ms")
        print(f"  Max:     {max_latency:6.2f}ms")
        print(f"{'='*60}")

        # Assert performance targets
        assert p50_latency < 50, (
            f"p50 latency {p50_latency:.2f}ms exceeds target of 50ms"
        )
        assert p99_latency < 100, (
            f"p99 latency {p99_latency:.2f}ms exceeds target of 100ms"
        )

    # ========================================================================
    # Test 2: Enforcement Execution Latency
    # ========================================================================

    @pytest.mark.asyncio
    async def test_enforcement_execution_latency(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test enforcement execution latency meets performance targets.

        Measures time from violation detected to enforcement action complete.
        Target: <200ms (p50), <500ms (p99)
        """
        # Given: System ready to enforce violations
        enforcement_latencies = []

        # Track enforcement actions instead of SDK calls
        enforcement_times = []

        async def track_enforcement(event):
            """Track when enforcement action is executed."""
            enforcement_times.append(time.perf_counter())

        risk_manager.event_bus.subscribe(
            EventType.ENFORCEMENT_ACTION,
            track_enforcement
        )

        # When: Trigger 50 violations (smaller sample for enforcement)
        num_violations = 50

        for i in range(num_violations):
            # Create position that violates limit (3 > 2)
            violation_size = 3 + (i % 2)  # Alternate between 3 and 4
            mock_sdk_suite._positions = [MockPosition(size=violation_size)]
            risk_manager.engine.current_positions = {
                "MNQ": {"size": violation_size, "side": "long"}
            }

            event = RiskEvent(
                event_type=EventType.POSITION_UPDATED,
                data={"symbol": "MNQ", "size": violation_size}
            )

            # Measure: Time from violation detection to enforcement complete
            start_time = time.perf_counter()

            # Clear previous enforcement times
            enforcement_times.clear()

            await risk_manager.event_bus.publish(event)
            await risk_manager.engine.evaluate_rules(event)

            # Wait for enforcement to execute
            await asyncio.sleep(0.02)

            # Check if enforcement was triggered
            if enforcement_times:
                enforcement_time = enforcement_times[0]
                latency_ms = (enforcement_time - start_time) * 1000
                enforcement_latencies.append(latency_ms)

        # Then: Calculate percentiles
        assert len(enforcement_latencies) > 0, "No enforcements were executed"

        # Sort for percentile calculation
        latencies_sorted = sorted(enforcement_latencies)

        # Calculate p50 (median) and p99
        p50_index = len(latencies_sorted) // 2
        p99_index = int(len(latencies_sorted) * 0.99)

        p50_latency = latencies_sorted[p50_index]
        p99_latency = latencies_sorted[p99_index]

        avg_latency = sum(enforcement_latencies) / len(enforcement_latencies)
        max_latency = max(enforcement_latencies)
        min_latency = min(enforcement_latencies)

        print(f"\n{'='*60}")
        print(f"Enforcement Execution Latency Results (n={len(enforcement_latencies)}):")
        print(f"{'='*60}")
        print(f"  Min:     {min_latency:6.2f}ms")
        print(f"  Average: {avg_latency:6.2f}ms")
        print(f"  Median:  {p50_latency:6.2f}ms (p50)")
        print(f"  p99:     {p99_latency:6.2f}ms")
        print(f"  Max:     {max_latency:6.2f}ms")
        print(f"{'='*60}")

        # Assert performance targets
        assert p50_latency < 200, (
            f"p50 enforcement latency {p50_latency:.2f}ms exceeds target of 200ms"
        )
        assert p99_latency < 500, (
            f"p99 enforcement latency {p99_latency:.2f}ms exceeds target of 500ms"
        )

    # ========================================================================
    # Test 3: High-Frequency Event Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_high_frequency_event_handling(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test system handles high-frequency events without drops.

        Simulates 100 position updates in 10 seconds (10 events/sec).
        Validates all events are processed and system remains responsive.
        """
        # Given: System monitoring high-frequency updates
        events_published = []
        events_processed = []

        async def track_processing(event):
            """Track processed events."""
            events_processed.append({
                "timestamp": time.perf_counter(),
                "event": event
            })

        risk_manager.event_bus.subscribe(
            EventType.POSITION_UPDATED,
            track_processing
        )

        # When: Fire 100 events over 10 seconds
        num_events = 100
        target_duration = 10.0  # seconds
        event_interval = target_duration / num_events  # ~0.1s between events

        start_time = time.perf_counter()

        for i in range(num_events):
            # Vary position size realistically
            size = 1 + (i % 3)  # Cycle through 1, 2, 3
            mock_sdk_suite._positions = [MockPosition(size=size)]
            risk_manager.engine.current_positions = {
                "MNQ": {"size": size, "side": "long"}
            }

            event = RiskEvent(
                event_type=EventType.POSITION_UPDATED,
                data={
                    "symbol": "MNQ",
                    "size": size,
                    "unrealizedPnl": 50.0 + i,
                    "sequence": i
                }
            )

            events_published.append({
                "timestamp": time.perf_counter(),
                "event": event
            })

            # Publish event
            await risk_manager.event_bus.publish(event)
            await risk_manager.engine.evaluate_rules(event)

            # Maintain event rate
            await asyncio.sleep(event_interval)

        # Wait for any remaining async processing
        await asyncio.sleep(0.5)

        end_time = time.perf_counter()
        total_duration = end_time - start_time

        # Then: Verify all events were processed
        assert len(events_published) == num_events, (
            f"Expected to publish {num_events} events, but published {len(events_published)}"
        )

        assert len(events_processed) == num_events, (
            f"Expected to process {num_events} events, but processed {len(events_processed)}"
        )

        # Calculate throughput
        throughput = num_events / total_duration  # events per second

        # Calculate processing delays (time from publish to process)
        processing_delays = []
        for pub, proc in zip(events_published, events_processed):
            delay_ms = (proc["timestamp"] - pub["timestamp"]) * 1000
            processing_delays.append(delay_ms)

        avg_delay = sum(processing_delays) / len(processing_delays)
        max_delay = max(processing_delays)

        print(f"\n{'='*60}")
        print(f"High-Frequency Event Handling Results:")
        print(f"{'='*60}")
        print(f"  Events Published:    {len(events_published)}")
        print(f"  Events Processed:    {len(events_processed)}")
        print(f"  Events Dropped:      {len(events_published) - len(events_processed)}")
        print(f"  Total Duration:      {total_duration:.2f}s")
        print(f"  Throughput:          {throughput:.2f} events/sec")
        print(f"  Avg Processing Time: {avg_delay:.2f}ms")
        print(f"  Max Processing Time: {max_delay:.2f}ms")
        print(f"{'='*60}")

        # Assert no events dropped
        assert len(events_processed) == len(events_published), (
            f"Events dropped: {len(events_published) - len(events_processed)}"
        )

        # Assert system remains responsive (avg delay < 100ms)
        assert avg_delay < 100, (
            f"Average processing delay {avg_delay:.2f}ms indicates system not responsive"
        )

        # Assert throughput meets target (>= 8 events/sec with some tolerance)
        # Note: 100 events in 10s = 10 events/sec ideal, but 8+ is acceptable for E2E
        assert throughput >= 8.0, (
            f"Throughput {throughput:.2f} events/sec below target of 8 events/sec"
        )

    # ========================================================================
    # Additional Performance Tests (Future Expansion)
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Future test - concurrent rule evaluation")
    async def test_concurrent_rule_evaluation(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test all rules evaluate concurrently on single event.

        Future test for validating parallel rule execution.
        Target: Total evaluation time < 100ms for all 13 rules.
        """
        pass

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Future test - memory usage under load")
    async def test_memory_usage_under_load(
        self, risk_manager, mock_sdk_suite
    ):
        """
        Test memory usage remains stable under sustained load.

        Future test for validating no memory leaks during high-frequency events.
        """
        pass
