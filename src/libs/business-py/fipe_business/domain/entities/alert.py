"""
Domain Entity: Alert

Represents a notification sent to users about opportunities.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Alert:
    """Alert notification entity."""

    alert_id: str
    opportunity_id: str
    recipient_id: str  # Telegram user ID or email
    channel: str  # "telegram" | "email"
    message: str
    status: str  # "pending" | "sent" | "failed" | "delivered"
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime

    def __post_init__(self):
        """Validate alert data."""
        if not self.alert_id:
            raise ValueError("Alert ID is required")

        if not self.opportunity_id:
            raise ValueError("Opportunity ID is required")

        if not self.recipient_id:
            raise ValueError("Recipient ID is required")

        if self.channel not in ["telegram", "email"]:
            raise ValueError("Invalid channel. Must be 'telegram' or 'email'")

        if self.status not in ["pending", "sent", "failed", "delivered"]:
            raise ValueError("Invalid status")

        if not self.message or len(self.message) < 10:
            raise ValueError("Message must be at least 10 characters")

        if self.retry_count < 0:
            raise ValueError("Retry count cannot be negative")

    def mark_as_sent(self, sent_time: datetime | None = None) -> None:
        """Mark alert as sent."""
        object.__setattr__(self, 'status', 'sent')
        object.__setattr__(self, 'sent_at', sent_time or datetime.utcnow())

    def mark_as_delivered(self, delivered_time: datetime | None = None) -> None:
        """Mark alert as delivered."""
        object.__setattr__(self, 'status', 'delivered')
        object.__setattr__(self, 'delivered_at', delivered_time or datetime.utcnow())

    def mark_as_failed(self, error_msg: str) -> None:
        """Mark alert as failed."""
        object.__setattr__(self, 'status', 'failed')
        object.__setattr__(self, 'error_message', error_msg)

    def increment_retry(self) -> None:
        """Increment retry count."""
        object.__setattr__(self, 'retry_count', self.retry_count + 1)

    def can_retry(self, max_retries: int = 3) -> bool:
        """Check if alert can be retried."""
        return self.status == "failed" and self.retry_count < max_retries
