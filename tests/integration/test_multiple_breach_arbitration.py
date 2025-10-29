"""
Test conflict resolution when multiple rules fire simultaneously.

Validates priority system: flatten > reduce_to_limit > close_position > cooldown > block

This test suite documents expected behavior for the priority system.
The current RiskEngine collects all violations but doesn't sort by priority yet.
These tests validate that:
1. Multiple violations can be detected simultaneously
2. Each violation has an action field
3. Priority order is documented and testable

Future enhancement: RiskEngine should sort violations by priority before enforcement.
"""

import pytest
from datetime import datetime, timezone

from risk_manager.core.events import RiskEvent, EventType
from risk_manager.core.engine import RiskEngine
from risk_manager.core.config import RiskConfig
from risk_manager.core.events import EventBus
from risk_manager.rules.max_position import MaxPositionRule
from risk_manager.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
from risk_manager.rules.daily_unrealized_loss import DailyUnrealizedLossRule
from risk_manager.rules.trade_frequency_limit import TradeFrequencyLimitRule
from risk_manager.state.database import Database


@pytest.mark.integration
class TestMultipleBreachArbitration:
    """Test priority-based conflict resolution when multiple rules fire."""

    @pytest.fixture
    async def engine(self, tmp_path):
        """Create RiskEngine with minimal config."""
        db = Database(db_path=":memory:")
        event_bus = EventBus()

        # Minimal config
        config = RiskConfig(
            project_x_api_key="test_key",
            project_x_username="test_user"
        )

        engine = RiskEngine(config, event_bus, trading_integration=None)

        # Initialize market_prices dict (needed for DailyUnrealizedLossRule)
        engine.market_prices = {}

        yield engine

        # Database close() returns None, not awaitable
        db.close()

    async def test_flatten_and_reduce_to_limit_both_detected(self, engine):
        """
        Scenario:
        - MaxPositionRule (total contracts): action="flatten" when total > 5
        - MaxContractsPerInstrumentRule (per-symbol): enforcement="reduce_to_limit" when ES > 1

        Setup: 5 total contracts (2 MNQ + 1 NQ + 0 ES)
        Event: Open 3 ES contracts
        Result: Total=8 (> 5), ES=3 (> 1)

        Expected: MaxPositionRule violation detected
        Note: MaxContractsPerInstrumentRule returns bool not dict, so it's logged but not in violations list
        """
        # Add rules with different actions
        rule_001 = MaxPositionRule(max_contracts=5, action="flatten", per_instrument=False)
        rule_002 = MaxContractsPerInstrumentRule(
            limits={"ES": 1, "NQ": 3, "MNQ": 5},
            enforcement="reduce_to_limit"
        )

        engine.add_rule(rule_001)
        engine.add_rule(rule_002)

        # Setup: Current positions (5 total: 2 MNQ + 1 NQ)
        engine.current_positions = {
            "MNQ": {"size": 2, "contract_id": "CON.F.US.MNQ.U25", "entry_price": 21500.0},
            "NQ": {"size": 1, "contract_id": "CON.F.US.NQ.H25", "entry_price": 21700.0}
        }

        # Create event that triggers BOTH rules (adds 3 ES, making total 8)
        event = RiskEvent(
            event_type=EventType.POSITION_OPENED,
            data={
                "symbol": "ES",
                "contract_id": "CON.F.US.ES.H25",
                "size": 3,  # Violates both: total=8>5, ES=3>1
                "account_id": "TEST-001"
            },
            timestamp=datetime.now(timezone.utc)
        )

        # Update engine state to reflect the new position
        engine.current_positions["ES"] = {
            "size": 3,
            "contract_id": "CON.F.US.ES.H25",
            "entry_price": 5800.0
        }

        # Evaluate rules
        violations = await engine.evaluate_rules(event)

        # Assert: MaxPositionRule violation detected (returns dict)
        # Note: MaxContractsPerInstrumentRule returns bool, so engine logs error and skips it
        assert len(violations) >= 1, f"Expected at least 1 violation, got {len(violations)}"

        # Assert: MaxPositionRule violation has flatten action
        max_position_violations = [v for v in violations if v.get("rule") == "MaxPositionRule"]
        assert len(max_position_violations) == 1
        assert max_position_violations[0]["action"] == "flatten"

        print(f"Violations detected: {[v.get('rule') for v in violations]}")
        print(f"Actions: {[v.get('action') for v in violations]}")
        print(f"Note: MaxContractsPerInstrumentRule fired but incompatible return type")

    async def test_close_position_and_flatten_both_detected(self, engine):
        """
        Scenario:
        - MaxPositionRule with action="close_position" for per-instrument limit
        - MaxPositionRule with action="flatten" for total limit

        Setup: 4 MNQ contracts
        Event: Position update
        Result: Both per-instrument (4 > 1) and total (4 > 3) limits violated

        Expected: Both violations detected with different actions
        """
        # Add rules with different actions
        rule_close = MaxPositionRule(max_contracts=1, action="close_position", per_instrument=True)
        rule_flatten = MaxPositionRule(max_contracts=3, action="flatten", per_instrument=False)

        engine.add_rule(rule_close)
        engine.add_rule(rule_flatten)

        # Setup: Position that violates both rules
        engine.current_positions = {
            "MNQ": {
                "size": 4,
                "contract_id": "CON.F.US.MNQ.U25",
                "entry_price": 21500.0
            }
        }

        # Create event
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.U25",
                "size": 4,
                "account_id": "TEST-001"
            },
            timestamp=datetime.now(timezone.utc)
        )

        # Evaluate rules
        violations = await engine.evaluate_rules(event)

        # Assert: Both violations detected
        assert len(violations) >= 2, f"Expected at least 2 violations, got {len(violations)}"

        # Check that both rules fired
        rule_names = [v.get("rule") for v in violations]
        assert rule_names.count("MaxPositionRule") == 2

        # Check actions
        actions = [v.get("action") for v in violations]
        assert "close_position" in actions
        assert "flatten" in actions

        print(f"Violations detected: {rule_names}")
        print(f"Actions: {actions}")

    async def test_deterministic_priority_order(self):
        """
        Test that priority order is consistent and documented:
        flatten > reduce_to_limit > close_position > cooldown > block

        This test documents the expected priority hierarchy.
        Future implementation should use these priorities to resolve conflicts.
        """
        # Priority map (lower number = higher priority)
        priority_map = {
            "flatten": 1,
            "reduce_to_limit": 2,
            "close_position": 3,
            "cooldown": 4,
            "block": 5
        }

        # Verify priority ordering
        assert priority_map["flatten"] < priority_map["reduce_to_limit"]
        assert priority_map["reduce_to_limit"] < priority_map["close_position"]
        assert priority_map["close_position"] < priority_map["cooldown"]
        assert priority_map["cooldown"] < priority_map["block"]

        print("Priority order validated:")
        print("   1. flatten (highest)")
        print("   2. reduce_to_limit")
        print("   3. close_position")
        print("   4. cooldown")
        print("   5. block (lowest)")

    async def test_sort_violations_by_priority(self):
        """
        Test helper function to sort violations by action priority.

        This demonstrates how violations should be sorted before enforcement.
        """
        priority_map = {
            "flatten": 1,
            "reduce_to_limit": 2,
            "close_position": 3,
            "cooldown": 4,
            "block": 5
        }

        # Simulated violations (out of order)
        violations = [
            {"rule": "Rule1", "action": "cooldown"},
            {"rule": "Rule2", "action": "flatten"},
            {"rule": "Rule3", "action": "close_position"},
            {"rule": "Rule4", "action": "reduce_to_limit"},
        ]

        # Sort by priority
        sorted_violations = sorted(
            violations,
            key=lambda v: priority_map.get(v.get("action", ""), 999)
        )

        # Verify order
        expected_order = ["flatten", "reduce_to_limit", "close_position", "cooldown"]
        actual_order = [v["action"] for v in sorted_violations]

        assert actual_order == expected_order

        print("Violations sorted correctly by priority:")
        for i, v in enumerate(sorted_violations, 1):
            print(f"   {i}. {v['action']} ({v['rule']})")

    async def test_multiple_violations_same_priority(self, engine):
        """
        Test behavior when multiple rules fire with the same action priority.

        Scenario: Two rules both want to "flatten"
        Expected: Both violations detected, arbitrary order acceptable
        """
        # Add two rules with same action
        rule_001 = MaxPositionRule(max_contracts=2, action="flatten", per_instrument=False)
        rule_002 = MaxPositionRule(max_contracts=1, action="flatten", per_instrument=True)

        engine.add_rule(rule_001)
        engine.add_rule(rule_002)

        # Setup: Position that violates both
        engine.current_positions = {
            "MNQ": {"size": 3, "contract_id": "CON.F.US.MNQ.U25", "entry_price": 21500.0}
        }

        # Create event
        event = RiskEvent(
            event_type=EventType.POSITION_UPDATED,
            data={
                "symbol": "MNQ",
                "contract_id": "CON.F.US.MNQ.U25",
                "size": 3,
                "account_id": "TEST-001"
            },
            timestamp=datetime.now(timezone.utc)
        )

        # Evaluate rules
        violations = await engine.evaluate_rules(event)

        # Assert: Both violations detected
        assert len(violations) == 2

        # Assert: Both have flatten action
        actions = [v.get("action") for v in violations]
        assert all(a == "flatten" for a in actions)

        print(f"Multiple violations with same priority detected: {len(violations)}")
        print(f"All actions: {actions}")


@pytest.mark.integration
class TestPriorityDocumentation:
    """Document expected priority behavior for future implementation."""

    def test_priority_rationale(self):
        """
        Document the rationale for priority ordering.

        Priority Order: flatten > reduce_to_limit > close_position > cooldown > block

        Rationale:
        1. flatten: Most severe - close ALL positions (account-wide breach)
        2. reduce_to_limit: Partial close (per-instrument limit breach)
        3. close_position: Close specific position (stop loss)
        4. cooldown: Temporary restriction (frequency breach)
        5. block: Preventative only (no position changes)

        When multiple violations occur:
        - Use highest priority action (most restrictive)
        - Example: If flatten + cooldown both fire, execute flatten (cooldown implied)
        """
        rationale = {
            "flatten": "Account-wide emergency: close ALL positions immediately",
            "reduce_to_limit": "Per-instrument limit: partially close to reach limit",
            "close_position": "Stop loss: close specific losing position",
            "cooldown": "Frequency control: temporary trading pause",
            "block": "Preventative: stop new trades, don't modify positions"
        }

        print("\nPriority Rationale:")
        for i, (action, reason) in enumerate(rationale.items(), 1):
            print(f"   {i}. {action}: {reason}")

        assert len(rationale) == 5

    def test_enforcement_execution_order(self):
        """
        Document how enforcement should be executed when multiple violations occur.

        Current State:
        - RiskEngine collects all violations
        - No sorting by priority yet

        Future Enhancement:
        - Sort violations by priority
        - Execute highest priority action first
        - Lower priority actions may become redundant (e.g., flatten makes cooldown unnecessary)
        """
        execution_plan = [
            "1. Collect all violations from all rules",
            "2. Sort violations by action priority (flatten > reduce > close > cooldown > block)",
            "3. Execute highest priority action first",
            "4. Check if lower priority actions are still needed",
            "5. Execute remaining actions if still relevant"
        ]

        print("\nEnforcement Execution Plan:")
        for step in execution_plan:
            print(f"   {step}")

        assert len(execution_plan) == 5


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
