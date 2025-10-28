"""
RULE-010: Auth Loss Guard (Connection Monitoring)

Category: Alert Only (No Enforcement)
Priority: LOW

This rule monitors SDK authentication/connection health and publishes alerts when
connection is lost. It does NOT enforce any trading restrictions or close positions
because if auth is lost, we cannot execute trades anyway.

Purpose:
- Detect SDK connection loss
- Detect authentication failures
- Publish warning events to alert systems
- Provide visibility into connection health

NOT included:
- Position closing (can't close if auth is lost)
- Order cancellation (can't cancel if auth is lost)
- Account lockout (pointless if SDK is down)
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import logging

from risk_manager.core.events import RiskEvent, EventType
from risk_manager.rules.base import RiskRule

logger = logging.getLogger(__name__)


class AuthLossGuardRule(RiskRule):
    """
    Auth Loss Guard - Monitor SDK connection health and publish alerts.

    This is an alert-only rule. It does NOT enforce trading restrictions.

    Configuration:
        - alert_on_disconnect: bool (default: True)
        - alert_on_auth_failure: bool (default: True)
        - log_level: str (default: "WARNING")

    Example:
        rule = AuthLossGuardRule(
            alert_on_disconnect=True,
            alert_on_auth_failure=True
        )
    """

    def __init__(
        self,
        alert_on_disconnect: bool = True,
        alert_on_auth_failure: bool = True,
        log_level: str = "WARNING",
    ):
        """
        Initialize auth loss guard rule.

        Args:
            alert_on_disconnect: Alert when SDK connection drops
            alert_on_auth_failure: Alert when authentication fails
            log_level: Logging level for alerts (WARNING, ERROR, CRITICAL)
        """
        super().__init__()
        self.alert_on_disconnect = alert_on_disconnect
        self.alert_on_auth_failure = alert_on_auth_failure
        self.log_level = getattr(logging, log_level.upper(), logging.WARNING)

        # Track connection state
        self.connection_state: Dict[int, bool] = {}  # account_id -> connected
        self.last_alert_time: Dict[int, datetime] = {}  # account_id -> last alert

    async def evaluate(
        self, event: RiskEvent, engine: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate SDK connection health events.

        This rule only responds to SDK_DISCONNECTED and AUTH_FAILED events.
        It does NOT block any trading events.

        Args:
            event: The event to evaluate
            engine: Risk engine instance

        Returns:
            Alert dictionary if connection issue detected, None otherwise
        """
        # Only monitor SDK health events
        if event.event_type not in [
            EventType.SDK_DISCONNECTED,
            EventType.SDK_CONNECTED,
            EventType.AUTH_FAILED,
            EventType.AUTH_SUCCESS,
        ]:
            return None

        account_id = event.data.get("account_id")
        if not account_id:
            return None

        # Handle connection events
        if event.event_type == EventType.SDK_DISCONNECTED:
            if not self.alert_on_disconnect:
                return None

            # Update connection state
            self.connection_state[account_id] = False
            self.last_alert_time[account_id] = datetime.now(timezone.utc)

            # Create alert
            alert = {
                "rule": "AuthLossGuardRule",
                "severity": "WARNING",
                "alert_type": "connection_lost",
                "message": f"SDK connection lost for account {account_id}",
                "account_id": account_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "alert_only",  # NO enforcement
                "recommendation": "Check SDK connection, positions cannot be managed until reconnected",
            }

            logger.log(
                self.log_level,
                f"⚠️  ALERT: SDK connection lost for account {account_id}"
            )

            return alert

        elif event.event_type == EventType.SDK_CONNECTED:
            # Connection restored
            was_disconnected = not self.connection_state.get(account_id, True)
            self.connection_state[account_id] = True

            if was_disconnected:
                logger.info(f"✅ SDK connection restored for account {account_id}")

            return None

        elif event.event_type == EventType.AUTH_FAILED:
            if not self.alert_on_auth_failure:
                return None

            # Authentication failed
            self.last_alert_time[account_id] = datetime.now(timezone.utc)

            alert = {
                "rule": "AuthLossGuardRule",
                "severity": "ERROR",
                "alert_type": "auth_failed",
                "message": f"SDK authentication failed for account {account_id}",
                "account_id": account_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "alert_only",  # NO enforcement
                "reason": event.data.get("reason", "Unknown"),
                "recommendation": "Verify credentials, check account status",
            }

            logger.log(
                logging.ERROR,
                f"🔐 ALERT: SDK authentication failed for account {account_id}: {event.data.get('reason', 'Unknown')}"
            )

            return alert

        elif event.event_type == EventType.AUTH_SUCCESS:
            # Authentication restored
            logger.info(f"✅ SDK authentication successful for account {account_id}")
            return None

        return None

    async def enforce(
        self, account_id: int, violation: Dict[str, Any], engine: Any
    ) -> None:
        """
        Enforcement for auth loss guard.

        This rule is ALERT ONLY - no enforcement actions taken.

        The alert has already been created by evaluate() and published
        via RULE_VIOLATED event by the engine. No additional action needed.

        Args:
            account_id: Account ID
            violation: Alert details
            engine: Risk engine instance
        """
        # ALERT ONLY - no enforcement
        # The engine already published the RULE_VIOLATED event with alert details
        pass

    def get_connection_status(self, account_id: int) -> bool:
        """
        Get current connection status for an account.

        Args:
            account_id: Account ID to check

        Returns:
            True if connected, False if disconnected, True if unknown
        """
        return self.connection_state.get(account_id, True)

    def get_last_alert_time(self, account_id: int) -> Optional[datetime]:
        """
        Get timestamp of last alert for an account.

        Args:
            account_id: Account ID to check

        Returns:
            Datetime of last alert, or None if no alerts
        """
        return self.last_alert_time.get(account_id)
