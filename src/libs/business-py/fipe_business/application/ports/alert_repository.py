"""
Domain Port: Alert Repository Interface

Defines the contract for alert persistence.
"""
from typing import Protocol, List, Optional
from fipe_business.domain.entities import Alert


class IAlertRepository(Protocol):
    """Interface for alert repository."""

    def save(self, alert: Alert) -> None:
        """Save an alert to the repository."""
        ...

    def find_by_id(self, alert_id: str) -> Optional[Alert]:
        """Find an alert by ID."""
        ...

    def find_pending(self, limit: int = 100) -> List[Alert]:
        """Find pending alerts."""
        ...

    def find_by_opportunity_id(self, opportunity_id: str) -> List[Alert]:
        """Find all alerts for a specific opportunity."""
        ...

    def update_status(self, alert_id: str, new_status: str) -> None:
        """Update alert status."""
        ...

    def count_by_status(self, status: str) -> int:
        """Count alerts by status."""
        ...
