"""
Domain Port: Favorite Repository Interface

Defines the contract for favorites persistence.
"""
from typing import Protocol, List


class IFavoriteRepository(Protocol):
    """Interface for favorite repository."""

    def add(self, session_id: str, opportunity_id: str) -> None:
        """Add an opportunity to favorites for a session."""
        ...

    def remove(self, session_id: str, opportunity_id: str) -> None:
        """Remove an opportunity from favorites for a session."""
        ...

    def list_opportunity_ids(self, session_id: str) -> List[str]:
        """Return list of favorited opportunity IDs for a session."""
        ...
