"""
FIPE API Client Implementation

Provides async HTTP client for FIPE API integration.
Implements IFIPEClient protocol for vehicle price lookups.
"""
import asyncio
import logging
import time
import httpx
from typing import TYPE_CHECKING, Optional
from datetime import date, datetime, timedelta
from fipe_business.domain.value_objects import Price
from fipe_infra.utils.limiters import fipe_limiter

if TYPE_CHECKING:
    from fipe_business.application.ports.rate_limit_event_repository import IRateLimitEventRepository
    from fipe_infra.repos.catalog_cache_repository import CatalogCacheRepository
    from fipe_infra.repos.api_hit_repository import ApiHitRepository

logger = logging.getLogger(__name__)

# Module-level catalog cache: fallback when no CatalogCacheRepository is injected.
# Stores (data, expires_timestamp) tuples keyed by catalog key.
_catalog_cache: dict = {}

_FALLBACK_TTL_SECONDS = 3600  # 1h fallback TTL for in-memory dict

# In-memory counters for catalog cache hit rate (resets on restart).
_cache_stats: dict = {"requests": 0, "hits": 0}


def get_cache_stats() -> dict:
    """Return cache hit/miss counters with computed hit_rate_pct."""
    reqs = _cache_stats["requests"]
    hits = _cache_stats["hits"]
    rate = round((hits / reqs) * 100, 1) if reqs > 0 else 0.0
    return {"requests": reqs, "hits": hits, "hit_rate_pct": rate}


def _dict_cache_get(key: str):
    entry = _catalog_cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None


def _dict_cache_set(key: str, data) -> None:
    _catalog_cache[key] = (data, time.time() + _FALLBACK_TTL_SECONDS)


class FIPEClient:
    """Async HTTP client for FIPE API."""

    # Brand normalization mapping
    BRAND_ALIASES = {
        "vw": "volkswagen",
        "gm": "chevrolet",
    }

    def __init__(
        self,
        base_url: str = "https://parallelum.com.br/fipe/api/v1",
        timeout: float = 10.0,
        event_repo: "Optional[IRateLimitEventRepository]" = None,
        catalog_cache_repo: "Optional[CatalogCacheRepository]" = None,
        api_hit_repo: "Optional[ApiHitRepository]" = None,
    ):
        """
        Initialize FIPEClient.

        Args:
            base_url: Base URL for FIPE API
            timeout: Request timeout in seconds
            event_repo: Optional rate-limit event repository for observability
            catalog_cache_repo: Optional DB-backed adaptive-TTL cache for catalog data.
                                 Falls back to module-level dict if None.
            api_hit_repo: Optional repository for tracking outbound FIPE API calls.
        """
        self.base_url = base_url
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self._event_repo = event_repo
        self._catalog_cache_repo = catalog_cache_repo
        self._api_hit_repo = api_hit_repo

    def _record_hit(self) -> None:
        if self._api_hit_repo:
            try:
                self._api_hit_repo.record("fipe")
            except Exception:
                pass

    def _cache_get(self, key: str):
        _cache_stats["requests"] += 1
        if self._catalog_cache_repo is not None:
            result = self._catalog_cache_repo.get(key)
        else:
            result = _dict_cache_get(key)
        if result is not None:
            _cache_stats["hits"] += 1
        return result

    def _cache_set(self, key: str, data, count: int) -> None:
        if self._catalog_cache_repo is not None:
            self._catalog_cache_repo.set(key, data, count)
        else:
            _dict_cache_set(key, data)

    def _normalize_brand(self, brand: str) -> str:
        """
        Normalize brand name for matching.

        Handles common abbreviations and case normalization.

        Args:
            brand: Brand name to normalize

        Returns:
            Normalized brand name in lowercase
        """
        brand_lower = brand.strip().lower()

        # Check if it's a known alias
        if brand_lower in self.BRAND_ALIASES:
            return self.BRAND_ALIASES[brand_lower]

        return brand_lower

    def _match_brand(self, search_brand: str, api_brands: list) -> Optional[dict]:
        """
        Find matching brand in FIPE API response.

        Performs case-insensitive matching with normalized names.

        Args:
            search_brand: Brand to search for
            api_brands: List of brand dicts from API

        Returns:
            Matched brand dict or None
        """
        normalized_search = self._normalize_brand(search_brand)

        for brand in api_brands:
            api_brand_name = brand.get("nome", "").strip().lower()
            # Normalize the API brand name too
            normalized_api = self._normalize_brand(api_brand_name)

            if normalized_api == normalized_search or api_brand_name == normalized_search:
                return brand
            # Substring match: "volkswagen" in "vw - volkswagen"
            if normalized_search in api_brand_name or api_brand_name in normalized_search:
                return brand

        return None

    def _match_models(self, search_model: str, api_models: list) -> list:
        """
        Find all matching models in FIPE API response.

        Returns all models whose name starts with the search term,
        so the caller can try each until finding one with the right year.
        """
        search_lower = search_model.strip().lower()
        matches = []

        for model in api_models:
            api_model_name = model.get("nome", "").strip().lower()
            if api_model_name == search_lower or api_model_name.startswith(search_lower):
                matches.append(model)

        return matches

    def _match_model(self, search_model: str, api_models: list) -> Optional[dict]:
        """Return first matching model (legacy compat)."""
        matches = self._match_models(search_model, api_models)
        return matches[0] if matches else None

    def _match_year(self, search_year: int, api_years: list) -> Optional[dict]:
        """
        Find matching year in FIPE API response.

        Matches year in format like "2015-1" or "2015 Gasolina".

        Args:
            search_year: Year to search for
            api_years: List of year dicts from API

        Returns:
            Matched year dict or None
        """
        year_str = str(search_year)

        for year in api_years:
            year_name = year.get("nome", "").strip()

            # Check if year appears in name (e.g., "2015 Gasolina")
            if year_name.startswith(year_str):
                return year

        return None

    async def lookup_price(self, brand: str, model: str, year: int) -> Optional[dict]:
        """
        Look up FIPE price for a vehicle.

        Follows the FIPE API flow:
        1. GET /carros/marcas → match brand
        2. GET /carros/marcas/{brand_id}/modelos → match model
        3. GET /carros/marcas/{brand_id}/modelos/{model_id}/anos → match year
        4. GET /carros/marcas/{brand_id}/modelos/{model_id}/anos/{year_code} → get price

        Args:
            brand: Vehicle brand
            model: Vehicle model
            year: Vehicle year

        Returns:
            Dict with price, fipe_code, reference_month, model_version or None if not found
        """
        try:
            # Step 1: Get brands
            brands = await self._get_brands_with_retry()
            if not brands:
                return None

            matched_brand = self._match_brand(brand, brands)
            if not matched_brand:
                return None

            brand_id = matched_brand.get("codigo")

            # Step 2: Get models
            models_response = await self._get_models_with_retry(brand_id)
            if not models_response:
                return None

            models = models_response.get("modelos", [])
            matched_models = self._match_models(model, models)
            if not matched_models:
                return None

            # Try each matching model variant until we find one with the right year
            for matched_model in matched_models:
                model_id = matched_model.get("codigo")
                model_version = matched_model.get("nome")

                # Step 3: Get years
                years = await self._get_years_with_retry(brand_id, model_id)
                if not years:
                    continue

                matched_year = self._match_year(year, years)
                if not matched_year:
                    continue

                year_code = matched_year.get("codigo")

                # Step 4: Get price
                price_response = await self._get_price_with_retry(brand_id, model_id, year_code)
                if not price_response:
                    continue

                price_str = price_response.get("Valor", "")
                price = Price.from_string(price_str)
                fipe_code = price_response.get("CodigoFipe", "")
                reference_month = price_response.get("MesReferencia", "")

                return {
                    "price": price,
                    "model_version": model_version,
                    "fipe_code": fipe_code,
                    "reference_month": reference_month
                }

            return None

        except Exception:
            return None

    async def _get_brands_with_retry(self) -> Optional[list]:
        """Get brands list with retry on timeout/rate-limit. Results are cached with adaptive TTL."""
        cached = self._cache_get("brands")
        if cached is not None:
            return cached
        self._record_hit()
        url = f"{self.base_url}/carros/marcas"
        await fipe_limiter.acquire()
        for attempt in range(3):
            try:
                response = await self._client.get(url)
                if response.status_code == 429:
                    logger.warning("FIPE rate limited (attempt %d): %s", attempt + 1, url)
                    if self._event_repo:
                        try:
                            self._event_repo.record("fipe", url.replace(self.base_url, ""), 429, attempt)
                        except Exception:
                            pass
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, list):
                    return None
                self._cache_set("brands", data, count=len(data))
                return data
            except httpx.TimeoutException:
                await asyncio.sleep(0.5)
                continue
            except Exception:
                return None
        return None

    async def _get_models_with_retry(self, brand_id: str) -> Optional[dict]:
        """Get models list with retry on timeout/rate-limit. Results are cached with adaptive TTL."""
        key = f"models:{brand_id}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        self._record_hit()
        url = f"{self.base_url}/carros/marcas/{brand_id}/modelos"
        await fipe_limiter.acquire()
        for attempt in range(3):
            try:
                response = await self._client.get(url)
                if response.status_code == 429:
                    logger.warning("FIPE rate limited (attempt %d): %s", attempt + 1, url)
                    if self._event_repo:
                        try:
                            self._event_repo.record("fipe", url.replace(self.base_url, ""), 429, attempt)
                        except Exception:
                            pass
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict) or "modelos" not in data:
                    return None
                self._cache_set(key, data, count=len(data.get("modelos", [])))
                return data
            except httpx.TimeoutException:
                await asyncio.sleep(0.5)
                continue
            except Exception:
                return None
        return None

    async def _get_years_with_retry(self, brand_id: str, model_id: int) -> Optional[list]:
        """Get years list with retry on timeout/rate-limit. Results are cached with adaptive TTL."""
        key = f"years:{brand_id}:{model_id}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        self._record_hit()
        url = f"{self.base_url}/carros/marcas/{brand_id}/modelos/{model_id}/anos"
        await fipe_limiter.acquire()
        for attempt in range(3):
            try:
                response = await self._client.get(url)
                if response.status_code == 429:
                    logger.warning("FIPE rate limited (attempt %d): %s", attempt + 1, url)
                    if self._event_repo:
                        try:
                            self._event_repo.record("fipe", url.replace(self.base_url, ""), 429, attempt)
                        except Exception:
                            pass
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, list):
                    return None
                self._cache_set(key, data, count=len(data))
                return data
            except httpx.TimeoutException:
                await asyncio.sleep(0.5)
                continue
            except Exception:
                return None
        return None

    async def _get_price_with_retry(self, brand_id: str, model_id: int, year_code: str) -> Optional[dict]:
        """Get price with retry on timeout."""
        self._record_hit()
        await fipe_limiter.acquire()
        try:
            response = await self._client.get(
                f"{self.base_url}/carros/marcas/{brand_id}/modelos/{model_id}/anos/{year_code}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            try:
                response = await self._client.get(
                    f"{self.base_url}/carros/marcas/{brand_id}/modelos/{model_id}/anos/{year_code}"
                )
                response.raise_for_status()
                return response.json()
            except Exception:
                return None
        except Exception:
            return None

    async def get_models_for_brand_name(self, brand_name: str) -> Optional[dict]:
        """
        Get all FIPE models for a brand by name.

        Returns dict with brand_id and models list, or None if brand not found.
        """
        brands = await self._get_brands_with_retry()
        if not brands:
            return None
        matched = self._match_brand(brand_name, brands)
        if not matched:
            return None
        brand_id = str(matched.get("codigo"))
        resp = await self._get_models_with_retry(brand_id)
        if not resp:
            return None
        return {
            "brand_id": brand_id,
            "models": [{"id": m["codigo"], "name": m["nome"]} for m in resp.get("modelos", [])],
        }

    async def get_versions_for_year(
        self, brand_id: str, model_base: str, year: int, models: list[dict] | None = None
    ) -> list[dict]:
        """
        Return only versions (model variants) that are available for a given year.

        Fetches all models matching model_base, then checks each against the years API
        concurrently (semaphore-limited) to stay under FIPE rate limits.
        """
        if models is None:
            resp = await self._get_models_with_retry(brand_id)
            if not resp:
                return []
            models = [{"id": m["codigo"], "name": m["nome"]} for m in resp.get("modelos", [])]

        base_lower = model_base.strip().lower()
        candidates = [m for m in models if m["name"].lower().startswith(base_lower)]

        # Use asyncio.wait with a hard timeout so we return partial results rather than []
        # if FIPE API is slow. Semaphore=5 keeps us under FIPE rate limits while being
        # fast enough for 40+ candidates (e.g. Toyota Corolla has 43 variants).
        sem = asyncio.Semaphore(5)

        async def check_model(m: dict) -> Optional[dict]:
            async with sem:
                years = await self._get_years_with_retry(brand_id, m["id"])
                if not years or not isinstance(years, list):
                    return None
                matched = self._match_year(year, years)
                if matched:
                    return {"id": m["id"], "name": m["name"], "year_code": matched["codigo"]}
                return None

        tasks = [asyncio.create_task(check_model(m)) for m in candidates]
        done, pending = await asyncio.wait(tasks, timeout=20.0)

        if pending:
            logger.warning(
                "[FIPE] get_versions_for_year partial timeout — %d/%d tasks completed for brand_id=%s model_base=%s year=%s",
                len(done), len(tasks), brand_id, model_base, year,
            )
            for t in pending:
                t.cancel()

        results = []
        for t in done:
            if not t.cancelled():
                try:
                    r = t.result()
                    if r is not None:
                        results.append(r)
                except Exception:
                    pass
        return results

    async def get_years_for_model(self, brand_id: str, model_id: int) -> list:
        """Get all years for a FIPE model."""
        years = await self._get_years_with_retry(brand_id, model_id)
        return [{"code": y["codigo"], "name": y["nome"]} for y in (years or [])]

    async def lookup_price_by_ids(self, brand_id: str, model_id: int, year_code: str) -> Optional[dict]:
        """
        Direct FIPE price lookup using exact brand/model/year IDs.

        Skips the name-matching steps entirely.
        """
        try:
            price_response = await self._get_price_with_retry(brand_id, model_id, year_code)
            if not price_response:
                return None
            price_str = price_response.get("Valor", "")
            price = Price.from_string(price_str)
            return {
                "price": price,
                "model_version": price_response.get("Modelo", ""),
                "fipe_code": price_response.get("CodigoFipe", ""),
                "reference_month": price_response.get("MesReferencia", ""),
            }
        except Exception:
            return None

    async def get_table_date(self) -> str:
        """
        Get current FIPE table reference date.

        Returns:
            Date string or fallback date on error
        """
        try:
            response = await self._client.get(f"{self.base_url}/Tabelas")
            response.raise_for_status()
            tables = response.json()

            if tables and len(tables) > 0:
                return tables[0].get("Mes", self._get_fallback_date())

            return self._get_fallback_date()
        except Exception:
            return self._get_fallback_date()

    def _get_fallback_date(self) -> str:
        """Get fallback date (current year/month)."""
        now = datetime.now()
        # Format: "janeiro/2024", "fevereiro/2024", etc.
        months = [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
        ]
        month_name = months[now.month - 1]
        return f"{month_name}/{now.year}"
