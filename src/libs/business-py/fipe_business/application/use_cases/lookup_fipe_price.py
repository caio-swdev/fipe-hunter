"""
Use Case: Lookup FIPE Price

Query FIPE reference price with caching.
"""
from datetime import datetime
from typing import Optional
from fipe_business.domain.entities import PriceCache
from fipe_business.application.ports import IFIPEClient, ICacheRepository
from fipe_business.domain.value_objects import Price


class LookupFIPEPriceUseCase:
    """Look up FIPE reference price for a vehicle."""

    def __init__(
        self,
        fipe_client: IFIPEClient,
        cache_repository: ICacheRepository
    ):
        self.fipe_client = fipe_client
        self.cache_repository = cache_repository

    async def execute(self, brand: str, model: str, year: int) -> Optional[dict]:
        """
        Look up FIPE price with caching.

        Flow:
        1. Generate cache key
        2. Check cache
        3. If cache hit and valid: return cached price data
        4. If cache miss: query FIPE API
        5. Cache result
        6. Return price data with fipe_code and reference_month
        """
        # Generate cache key
        cache_key = PriceCache.generate_key(brand, model, year)

        # Check cache
        cached_entry = self.cache_repository.find_by_key(cache_key)
        if cached_entry and cached_entry.is_valid():
            return {
                "price": cached_entry.price,
                "fipe_code": "cached",
                "reference_month": cached_entry.fipe_table_date
            }

        # Cache miss or expired - query FIPE API
        result = await self.fipe_client.lookup_price(brand, model, year)

        if result is None:
            # Vehicle not found in FIPE
            return None

        price = result["price"]
        version = result["model_version"]
        fipe_code = result["fipe_code"]
        reference_month = result["reference_month"]

        # Cache the result
        cache_entry = PriceCache.create(
            brand=brand,
            model=model,
            year=year,
            price=price,
            version=version,
            fipe_table_date=reference_month,
        )
        self.cache_repository.save(cache_entry)

        return {
            "price": price,
            "fipe_code": fipe_code,
            "reference_month": reference_month
        }
