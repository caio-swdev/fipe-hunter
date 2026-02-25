"""
Domain Entity: PriceCache

Represents a cached FIPE price lookup with TTL aligned to the FIPE monthly refresh cycle.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from ..value_objects import Price


def _next_fipe_refresh_datetime() -> datetime:
    """Return expiry datetime: first business day of next month + 2-day safety offset."""
    today = date.today()
    if today.month == 12:
        first_of_next = date(today.year + 1, 1, 1)
    else:
        first_of_next = date(today.year, today.month + 1, 1)
    first_biz = first_of_next
    while first_biz.weekday() >= 5:  # skip Saturday (5) and Sunday (6)
        first_biz += timedelta(days=1)
    expires = first_biz + timedelta(days=2)
    return datetime(expires.year, expires.month, expires.day)


@dataclass
class PriceCache:
    """Cached FIPE price entity."""

    cache_key: str  # "brand-model-year" (normalized, lowercase)
    brand: str
    model: str
    year: int
    price: Price
    version: str  # Vehicle version from FIPE (e.g., "Gol 1.0")
    fipe_table_date: str  # FIPE reference table date
    cached_at: datetime
    expires_at: datetime

    def __post_init__(self):
        """Validate cache data."""
        if not self.cache_key:
            raise ValueError("Cache key is required")

        if not self.brand or len(self.brand) < 2:
            raise ValueError("Brand must be at least 2 characters")

        if not self.model or len(self.model) < 2:
            raise ValueError("Model must be at least 2 characters")

        if self.year < 1950 or self.year > 2026:
            raise ValueError("Year must be between 1950 and 2026")

        if not isinstance(self.price, Price):
            raise TypeError("Price must be Price type")

        if self.expires_at <= self.cached_at:
            raise ValueError("Expiration must be after cache time")

    @classmethod
    def create(
        cls,
        brand: str,
        model: str,
        year: int,
        price: Price,
        version: str,
        fipe_table_date: str,
    ) -> "PriceCache":
        """Create a new cache entry expiring at the next FIPE monthly refresh + 2 days."""
        now = datetime.utcnow()
        cache_key = cls.generate_key(brand, model, year)

        return cls(
            cache_key=cache_key,
            brand=brand,
            model=model,
            year=year,
            price=price,
            version=version,
            fipe_table_date=fipe_table_date,
            cached_at=now,
            expires_at=_next_fipe_refresh_datetime(),
        )

    @staticmethod
    def generate_key(brand: str, model: str, year: int) -> str:
        """Generate normalized cache key."""
        return f"{brand.lower().strip()}-{model.lower().strip()}-{year}"

    def is_expired(self, current_time: datetime | None = None) -> bool:
        """Check if cache entry is expired."""
        check_time = current_time or datetime.utcnow()
        return check_time >= self.expires_at

    def is_valid(self, current_time: datetime | None = None) -> bool:
        """Check if cache entry is still valid."""
        return not self.is_expired(current_time)
