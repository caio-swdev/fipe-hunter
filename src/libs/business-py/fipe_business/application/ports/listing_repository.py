"""
Domain Port: Listing Repository Interface

Defines the contract for listing persistence.
"""
from typing import Protocol
from fipe_business.domain.entities import Listing


class IListingRepository(Protocol):
    """Interface for listing repository."""

    def save(self, listing: Listing) -> None:
        """Save a listing to the repository."""
        ...

    def find_by_url(self, url: str) -> Listing | None:
        """Find a listing by its URL."""
        ...

    def count_by_marketplace(self, marketplace: str) -> int:
        """Count listings from a specific marketplace."""
        ...
