"""
Test script to verify rule loading from config.

This script creates a RiskManager instance and verifies that rules
are properly loaded from the configuration files.
"""

import asyncio
from pathlib import Path

from loguru import logger
from risk_manager.config.loader import ConfigLoader
from risk_manager.core.manager import RiskManager


async def main():
    """Test rule loading."""
    logger.info("=" * 80)
    logger.info("Testing Rule Loading from Config")
    logger.info("=" * 80)

    # Load configs
    config_dir = Path("config")
    loader = ConfigLoader(config_dir=config_dir)

    try:
        risk_config = loader.load_risk_config()
        logger.success(f"✅ Loaded risk_config.yaml")
    except Exception as e:
        logger.error(f"❌ Failed to load risk_config.yaml: {e}")
        return

    try:
        timers_config = loader.load_timers_config()
        logger.success(f"✅ Loaded timers_config.yaml")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load timers_config.yaml: {e}")
        timers_config = None

    # Create RiskManager
    logger.info("\nCreating RiskManager instance...")
    manager = RiskManager(config=risk_config, timers_config=timers_config)

    # Trigger rule loading
    logger.info("\nLoading rules from config...")
    await manager._add_default_rules()

    # Check loaded rules
    logger.info("\n" + "=" * 80)
    logger.info(f"RESULTS: {len(manager.engine.rules)} rules loaded")
    logger.info("=" * 80)

    if manager.engine.rules:
        logger.success("\n✅ Successfully loaded rules:")
        for i, rule in enumerate(manager.engine.rules, 1):
            rule_class = rule.__class__.__name__
            logger.success(f"  {i}. {rule_class}")

        # Show some rule details
        logger.info("\n📊 Rule Details:")
        for rule in manager.engine.rules:
            rule_class = rule.__class__.__name__
            if hasattr(rule, "limit"):
                logger.info(f"  • {rule_class}: limit=${rule.limit}")
            elif hasattr(rule, "target"):
                logger.info(f"  • {rule_class}: target=${rule.target}")
            elif hasattr(rule, "limits"):
                logger.info(f"  • {rule_class}: limits={rule.limits}")
            elif hasattr(rule, "blocked_symbols"):
                logger.info(f"  • {rule_class}: {len(rule.blocked_symbols)} blocked symbols")
            elif hasattr(rule, "grace_period_seconds"):
                logger.info(f"  • {rule_class}: grace_period={rule.grace_period_seconds}s")
            else:
                logger.info(f"  • {rule_class}")
    else:
        logger.warning("\n⚠️ No rules loaded!")

    # Check which rules are enabled in config
    logger.info("\n📋 Config Status (enabled rules):")
    enabled_rules = []
    if risk_config.rules.daily_realized_loss.enabled:
        enabled_rules.append("DailyRealizedLoss")
    if risk_config.rules.daily_realized_profit.enabled:
        enabled_rules.append("DailyRealizedProfit")
    if risk_config.rules.max_contracts_per_instrument.enabled:
        enabled_rules.append("MaxContractsPerInstrument")
    if risk_config.rules.no_stop_loss_grace.enabled:
        enabled_rules.append("NoStopLossGrace")
    if risk_config.rules.symbol_blocks.enabled:
        enabled_rules.append("SymbolBlocks")
    if risk_config.rules.trade_frequency_limit.enabled:
        enabled_rules.append("TradeFrequencyLimit")
    if risk_config.rules.cooldown_after_loss.enabled:
        enabled_rules.append("CooldownAfterLoss")
    if risk_config.rules.session_block_outside.enabled:
        enabled_rules.append("SessionBlockOutside")
    if risk_config.rules.auth_loss_guard.enabled:
        enabled_rules.append("AuthLossGuard")

    logger.info(f"  Enabled in config: {len(enabled_rules)} rules")
    for rule_name in enabled_rules:
        logger.info(f"    - {rule_name}")

    # Final summary
    loaded_count = len(manager.engine.rules)
    enabled_count = len(enabled_rules)

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Enabled in config: {enabled_count} rules")
    logger.info(f"Actually loaded: {loaded_count} rules")

    if loaded_count == enabled_count:
        logger.success(f"✅ SUCCESS! All {enabled_count} enabled rules loaded correctly!")
    elif loaded_count > 0:
        logger.warning(f"⚠️ PARTIAL SUCCESS: {loaded_count}/{enabled_count} rules loaded")
        logger.warning(f"   {enabled_count - loaded_count} rules failed to load (check logs above)")
    else:
        logger.error(f"❌ FAILURE! No rules loaded (expected {enabled_count})")

    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
