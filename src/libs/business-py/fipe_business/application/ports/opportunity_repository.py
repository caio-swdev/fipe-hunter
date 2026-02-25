"""
Domain Port: Opportunity Repository Interface

Defines the contract for opportunity persistence.
"""
from typing import Protocol, List, Optional
from fipe_business.domain.entities import Opportunity


class IOpportunityRepository(Protocol):
    """Interface for opportunity repository."""

    def save(self, opportunity: Opportunity) -> None:
        """Save an opportunity to the repository."""
        ...

    def find_by_id(self, opportunity_id: str) -> Optional[Opportunity]:
        """Find an opportunity by ID."""
        ...

    def find_by_listing_id(self, listing_id: str) -> Optional[Opportunity]:
        """Find an opportunity by listing ID."""
        ...

    def find_active(self, min_score: int = 0, limit: int = 100) -> List[Opportunity]:
        """Find active opportunities with score >= min_score, sorted by score descending."""
        ...

    def find_by_status(self, status: str, limit: int = 100) -> List[Opportunity]:
        """Find opportunities by status."""
        ...

    def count_by_status(self, status: str) -> int:
        """Count opportunities by status."""
        ...

    def update_status(self, opportunity_id: str, new_status: str) -> None:
        """Update opportunity status."""
        ...
