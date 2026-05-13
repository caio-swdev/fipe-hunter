"""
Infrastructure Implementation: SQLAlchemy Cache Repository

Implements ICacheRepository using SQLAlchemy ORM for FIPE price caching.
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fipe_business.domain.entities.price_cache import PriceCache
from fipe_business.domain.value_objects.price import Price
from fipe_infra.database.models import PriceCacheModel


class SQLAlchemyCacheRepository:
    """SQLAlchemy-based implementation of ICacheRepository."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy Session instance.
        """
        self.session = session

    def save(self, cache_entry: PriceCache) -> None:
        """Save a cache entry (upsert by cache_key).

        If an entry with the same cache_key exists, it will be updated.
        Otherwise, a new entry is created.

        Args:
            cache_entry: PriceCache entity to save.
        """

        existing = self.session.query(PriceCacheModel).filter_by(
            cache_key=cache_entry.cache_key
        ).first()

        if existing:

            existing.brand = cache_entry.brand
            existing.model = cache_entry.model
            existing.year = cache_entry.year
            existing.price_value = cache_entry.price.to_float()
            existing.version = cache_entry.version
            existing.fipe_table_date = cache_entry.fipe_table_date
            existing.cached_at = cache_entry.cached_at
            existing.expires_at = cache_entry.expires_at
        else:

            model = PriceCacheModel(
                cache_key=cache_entry.cache_key,
                brand=cache_entry.brand,
                model=cache_entry.model,
                year=cache_entry.year,
                price_value=cache_entry.price.to_float(),
                version=cache_entry.version,
                fipe_table_date=cache_entry.fipe_table_date,
                cached_at=cache_entry.cached_at,
                expires_at=cache_entry.expires_at
            )
            self.session.add(model)

        self.session.commit()

    def find_by_key(self, cache_key: str) -> Optional[PriceCache]:
        """Find cache entry by key.

        Args:
            cache_key: The cache key to search for.

        Returns:
            PriceCache entity if found, None otherwise.
        """
        model = self.session.query(PriceCacheModel).filter_by(
            cache_key=cache_key
        ).first()

        if not model:
            return None


        return PriceCache(
            cache_key=model.cache_key,
            brand=model.brand,
            model=model.model,
            year=model.year,
            price=Price.from_float(model.price_value),
            version=model.version,
            fipe_table_date=model.fipe_table_date,
            cached_at=model.cached_at,
            expires_at=model.expires_at
        )

    def delete(self, cache_key: str) -> None:
        """Delete cache entry by key.

        Args:
            cache_key: The cache key to delete.
        """
        self.session.query(PriceCacheModel).filter_by(
            cache_key=cache_key
        ).delete()
        self.session.commit()

    def clear_expired(self) -> int:
        """Clear all expired cache entries.

        Deletes all entries where expires_at < datetime.utcnow().

        Returns:
            Number of entries deleted.
        """
        now = datetime.utcnow()
        deleted_count = self.session.query(PriceCacheModel).filter(
            PriceCacheModel.expires_at < now
        ).delete()
        self.session.commit()
        return deleted_count
