"""
Domain Port: Rate-Limit Event Repository Interface
"""
from typing import Protocol, Optional
from datetime import datetime


class IRateLimitEventRepository(Protocol):
    """Interface for recording and querying external API rate-limit events."""

    def record(self, service: str, endpoint: Optional[str], status_code: int, retry_attempt: int) -> None:
        """Persist a rate-limit event."""
        ...

    def count_since(self, service: str, since: datetime) -> int:
        """Count rate-limit events for a service since a given datetime."""
        ...

    def last_event_at(self, service: str) -> Optional[datetime]:
        """Return the timestamp of the most recent rate-limit event for a service."""
        ...
