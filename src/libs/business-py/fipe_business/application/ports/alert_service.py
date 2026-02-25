"""
Domain Port: Alert Service Interface

Defines the contract for sending alerts.
"""
from typing import Protocol
from fipe_business.domain.entities import Opportunity


class IAlertService(Protocol):
    """Interface for alert notification service."""

    def send_alert(self, opportunity: Opportunity, recipient_id: str) -> bool:
        """
        Send alert notification for an opportunity.

        Args:
            opportunity: The opportunity to alert about
            recipient_id: Recipient identifier (e.g., Telegram user ID)

        Returns:
            True if sent successfully, False otherwise
        """
        ...

    def get_channel_name(self) -> str:
        """Get the alert channel name (e.g., 'telegram', 'email')."""
        ...
