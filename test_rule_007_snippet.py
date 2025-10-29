    async def test_rule_007_cooldown_after_loss(self) -> dict[str, Any]:
        """
        Test RULE-007: Cooldown After Loss

        Arithmetic Test:
        - Loss threshold: -$100 triggers 5-minute cooldown
        - Trade 1: -$50 (OK, below threshold)
        - Trade 2: -$150 (BREACH, triggers cooldown)

        Expected:
        - Violations: 1
        - Enforcement: flatten + cooldown timer
        - Lockout: 300 seconds (5 minutes)
        """
        console.print("\n[bold cyan]Testing RULE-007: Cooldown After Loss[/bold cyan]")

        from risk_manager.rules.cooldown_after_loss import CooldownAfterLossRule
        from risk_manager.state.timer_manager import TimerManager

        # Create timer manager
        timer_manager = TimerManager()
        await timer_manager.start()

        # Create rule with test configuration
        rule = CooldownAfterLossRule(
            loss_thresholds=[
                {"loss_amount": -100.0, "cooldown_duration": 300}  # -$100 = 5 min
            ],
            timer_manager=timer_manager,
            pnl_tracker=self.pnl_tracker,
            lockout_manager=self.lockout_manager,
            action="flatten"
        )

        test_account = "TEST-ACCOUNT-007"
        violations = []

        # Mock engine
        from risk_manager.core.engine import RiskEngine
        mock_engine = type('MockEngine', (), {
            'current_positions': {},
            'market_prices': {}
        })()

        # Trade 1: -$50 loss (below threshold)
        console.print("[yellow]Trade 1: -$50 loss[/yellow]")

        event1 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": -50.0,  # Rule expects camelCase!
                "symbol": "MNQ"
            }
        )

        violation1 = await rule.evaluate(event1, mock_engine)

        if violation1:
            violations.append(violation1)
            console.print(f"  [X] [red]VIOLATION: {violation1}[/red]")
        else:
            console.print("  [OK] [green]No violation (loss below threshold)[/green]")

        # Verify no lockout set
        is_locked_before = self.lockout_manager.is_locked_out(test_account)
        console.print(f"  Account locked: {is_locked_before}")

        # Trade 2: -$150 loss (exceeds threshold, BREACH!)
        console.print("[yellow]Trade 2: -$150 loss[/yellow]")

        event2 = RiskEvent(
            event_type=EventType.TRADE_EXECUTED,
            data={
                "account_id": test_account,
                "profitAndLoss": -150.0,
                "symbol": "ES"
            }
        )

        violation2 = await rule.evaluate(event2, mock_engine)

        is_locked_after = False
        if violation2:
            violations.append(violation2)
            console.print(f"  [X] [red]VIOLATION: {violation2.get('message')}[/red]")
            console.print(f"  [red]Enforcement action: {violation2.get('action')}[/red]")
            console.print(f"  [red]Cooldown duration: {violation2.get('cooldown_duration')}s[/red]")

            # Execute enforcement to set lockout
            await rule.enforce(test_account, violation2, mock_engine)

            # Verify lockout was set
            is_locked_after = self.lockout_manager.is_locked_out(test_account)
            console.print(f"  Account locked after enforcement: {is_locked_after}")

        else:
            console.print("  [X] [red]ERROR: Should have violated![/red]")

        # Cleanup timer manager
        await timer_manager.stop()

        # Validate results
        result = {
            "rule": "RULE-007",
            "passed": len(violations) == 1,  # Should violate on trade 2 only
            "violations": violations,
            "arithmetic_correct": (
                len(violations) == 1 and
                violations[0].get('cooldown_duration') == 300 and
                violations[0].get('loss_amount') == -150.0
            ),
            "enforcement_action": violations[0].get('action') if violations else None,
            "lockout_verified": is_locked_after if violations else False
        }

        if result["passed"] and result["arithmetic_correct"] and result["lockout_verified"]:
            console.print("\n[bold green][OK] RULE-007 PASSED[/bold green]")
        else:
            console.print("\n[bold red][X] RULE-007 FAILED[/bold red]")

        return result


# ============================================================
# REGISTRATION IN run_all_tests():
# Add this line after RULE-006:
#     results["RULE-007"] = await self.test_rule_007_cooldown_after_loss()
# ============================================================
