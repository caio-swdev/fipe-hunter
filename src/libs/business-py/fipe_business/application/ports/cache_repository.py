"""
Domain Port: Cache Repository Interface

Defines the contract for price cache storage.
"""
from typing import Protocol, Optional
from fipe_business.domain.entities import PriceCache


class ICacheRepository(Protocol):
    """Interface for cache repository."""

    def save(self, cache_entry: PriceCache) -> None:
        """Save a cache entry."""
        ...

    def find_by_key(self, cache_key: str) -> Optional[PriceCache]:
        """Find cache entry by key."""
        ...

    def delete(self, cache_key: str) -> None:
        """Delete cache entry by key."""
        ...

    def clear_expired(self) -> int:
        """Clear all expired cache entries. Returns count of deleted entries."""
        ...
