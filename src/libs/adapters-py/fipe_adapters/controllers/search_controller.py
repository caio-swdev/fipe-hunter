"""
SearchController - Orchestrates on-demand vehicle search.

Extracted from search_routes.py to enforce Clean Architecture:
routes stay thin, domain logic stays in use-cases, infra details
stay in repos/scrapers passed via constructor injection.
"""
import asyncio
import hashlib
import re
import uuid
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlunparse

from fipe_business.application.use_cases.lookup_fipe_price import LookupFIPEPriceUseCase
from fipe_business.application.use_cases.compare_prices import ComparePricesUseCase
from fipe_business.application.use_cases.calculate_opportunity_score import CalculateOpportunityScoreUseCase
from fipe_business.application.use_cases.create_opportunity import CreateOpportunityUseCase
from fipe_business.domain.value_objects import Price, Discount


_VERSION_SKIP_WORDS = {
    'sedan', 'hatch', 'hatchback', 'sw', 'suv', 'pick', 'up', 'cab',
    '16v', '8v', '12v', '4p', '2p', '5p', '3p', 'aut', 'man',
    'cvt', 'at', 'mt', 'flex', 'gnv', 'mec', 'gas',
}


def _canonical_url(url: str) -> str:
    """
    Return scheme + netloc + path only — strips query params and fragments.

    OLX and WebMotors often append session/tracking query parameters (e.g.
    ?origin=..., ?sid=..., ?tracking=...) to listing URLs.  Without stripping
    these, two scrape calls for the same physical listing produce different URL
    strings → different md5 hashes → the favorite ID from the first search
    never matches the listing ID from the second search.

    The canonical path always contains the unique listing identifier (e.g. the
    item slug / numeric ID), so this stripping is safe for deduplication.
    """
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, '', '', ''))


def _version_keywords(version: str, model_base: str) -> list[str]:
    """
    Extract trim-level tokens from a FIPE version string for listing matching.

    Only returns alpha tokens (e.g. ['ex', 'gli', 'sport']) — NOT engine sizes.
    """
    model_words = set(model_base.lower().split())
    tokens = []
    for word in version.lower().split():
        w = word.strip('.')
        if w in _VERSION_SKIP_WORDS or w in model_words:
            continue
        if re.match(r'^[a-z]{2,}$', w):
            tokens.append(w)
    return tokens


class SearchController:
    """Orchestrates on-demand vehicle search across FIPE + scrapers."""

    def __init__(
        self,
        lookup_use_case: LookupFIPEPriceUseCase,
        score_use_case: CalculateOpportunityScoreUseCase,
        create_use_case: CreateOpportunityUseCase,
        fipe_client,
        olx_scraper_factory,
        webmotors_scraper_factory,
        search_cache_repo=None,
    ):
        self._lookup = lookup_use_case
        self._score = score_use_case
        self._create = create_use_case
        self._fipe_client = fipe_client
        self._olx_factory = olx_scraper_factory
        self._wm_factory = webmotors_scraper_factory
        self._search_cache = search_cache_repo

    async def _fetch_fipe_for_year(self, brand_id: str, model_id: int, year: int, years_list: list) -> Optional[dict]:
        """Look up FIPE price for a specific year using a pre-fetched years_list."""
        matched = self._fipe_client._match_year(year, years_list)
        if not matched:
            return None
        return await self._fipe_client.lookup_price_by_ids(str(brand_id), int(model_id), matched["codigo"])

    async def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute on-demand vehicle search.

        1. FIPE price lookup (real API call)
        2. Scrape OLX + WebMotors in parallel
        3. Filter, score, and create opportunities
        4. Return FIPE data + opportunity list
        """
        brand = params["brand"].strip()
        model = params["model"].strip()
        year: Optional[int] = params.get("year")
        brand_id: Optional[str] = params.get("brand_id")
        model_id: Optional[int] = params.get("model_id")
        year_code: Optional[str] = params.get("year_code")
        version: Optional[str] = params.get("version")


        fipe_data = None
        fipe_error = None
        fipe_price = None

        has_direct_ids = brand_id and model_id and year_code
        if has_direct_ids or year:
            try:
                if has_direct_ids:
                    result = await self._fipe_client.lookup_price_by_ids(brand_id, model_id, year_code)
                    display_year = int(year_code.split("-")[0]) if year_code else year
                    display_model = version or model
                else:
                    result = await self._lookup.execute(brand=brand, model=model, year=year)
                    display_year = year
                    display_model = model

                if result:
                    fipe_price = result["price"]
                    fipe_data = {
                        "brand": brand,
                        "model": display_model,
                        "year": display_year,
                        "reference_price": fipe_price.to_float(),
                        "fipe_code": result["fipe_code"],
                        "reference_month": result["reference_month"],
                    }
                else:
                    fipe_error = "Vehicle not found in FIPE database"
            except Exception as e:
                fipe_error = str(e)


        years_list = None
        if brand_id and model_id and not fipe_price:
            try:
                years_list = await self._fipe_client._get_years_with_retry(str(brand_id), int(model_id))
                print(f"[Search] Pre-fetched {len(years_list or [])} year entries for brand_id={brand_id} model_id={model_id}")
            except Exception as e:
                print(f"[Search] Could not pre-fetch years: {e}")


        scrape_year = year or (int(year_code.split("-")[0]) if year_code else None)


        if self._search_cache:
            cached_results = self._search_cache.get(brand, model, scrape_year)
            if cached_results is not None:
                print(f"[Search] Cache HIT for {brand} {model} {scrape_year} — skipping scrape")

                if years_list:
                    enriched = False
                    for r in cached_results:
                        if not r.get("fipe_price") and r.get("year"):
                            try:
                                fipe_result = await self._fetch_fipe_for_year(brand_id, model_id, r["year"], years_list)
                                if fipe_result:
                                    fp = fipe_result["price"]
                                    lp = Price.from_float(r["listing_price"])
                                    disc = Discount.calculate(lp, fp)
                                    r["fipe_price"] = float(fp.amount)
                                    r["discount_percent"] = float(disc.percentage)
                                    enriched = True
                            except Exception as e:
                                print(f"[Search] FIPE enrichment failed for cached result: {e}")
                    if enriched:
                        try:
                            self._search_cache.set(brand, model, scrape_year, cached_results)
                        except Exception:
                            pass
                cached_results.sort(key=lambda o: o.get("score", 0), reverse=True)
                return {
                    "status": "success",
                    "fipe": fipe_data,
                    "fipe_error": fipe_error,
                    "results": cached_results,
                    "total_results": len(cached_results),
                    "cached": True,
                }

        olx_scraper = self._olx_factory(brand=brand, model=model, year=scrape_year)
        wm_scraper = self._wm_factory(brand=brand, model=model, year=scrape_year)

        async def _scrape_olx():
            try:
                return await asyncio.to_thread(olx_scraper.scrape, 10)
            except Exception as e:
                print(f"[Search] OLX scraping failed: {e}")
                return []

        async def _scrape_webmotors():
            try:
                return await asyncio.to_thread(wm_scraper.scrape, 10)
            except Exception as e:
                print(f"[Search] WebMotors scraping failed: {e}")
                return []

        olx_results, wm_results = await asyncio.gather(_scrape_olx(), _scrape_webmotors())
        listings = olx_results + wm_results
        print(f"[Search] Total listings: {len(listings)} (OLX: {len(olx_results)}, WebMotors: {len(wm_results)})")


        new_opportunities = []

        for listing in listings:
            try:
                brand_match = listing.brand.lower() == brand.lower()
                model_match = model.lower() in listing.model.lower() or listing.model.lower() in model.lower()
                year_match = scrape_year is None or listing.year == scrape_year

                version_match = True
                if version:
                    kws = _version_keywords(version, model)
                    if kws:
                        listing_text = f"{listing.brand} {listing.model}".lower()
                        version_match = any(
                            re.search(rf'\b{re.escape(kw)}\b', listing_text)
                            for kw in kws
                        )

                print(f"[Search] {listing.brand} {listing.model} {listing.year} R${listing.price} | brand={brand_match} model={model_match} year={year_match} version={version_match}")

                if not (brand_match and model_match and year_match and version_match):
                    continue

                if fipe_price:
                    listing_price_vo = Price.from_float(listing.price)
                    discount = Discount.calculate(listing_price_vo, fipe_price)
                    status = "suspicious" if discount.is_suspicious() else "active"

                    score = self._score.execute(
                        discount=discount,
                        condition=listing.condition,
                        mileage=listing.mileage,
                        brand=listing.brand,
                        model=listing.model,
                        created_at=listing.scraped_at
                    )

                    opportunity = self._create.execute(
                        listing=listing,
                        listing_id=hashlib.md5(_canonical_url(listing.url).encode()).hexdigest(),
                        fipe_price=fipe_price,
                        discount=discount,
                        score=score,
                        status=status,
                        image_url=listing.image_url,
                    )

                    new_opportunities.append({
                        "id": opportunity.listing_id,
                        "brand": opportunity.brand,
                        "model": opportunity.model,
                        "year": opportunity.year,
                        "listing_price": float(opportunity.listing_price.amount),
                        "fipe_price": float(opportunity.fipe_price.amount),
                        "discount_percent": float(opportunity.discount.percentage),
                        "score": opportunity.score.value,
                        "mileage_km": opportunity.mileage or 0,
                        "source": opportunity.marketplace,
                        "url": opportunity.listing_url,
                        "image_url": listing.image_url,
                        "found_at": listing.scraped_at.isoformat() if listing.scraped_at else "",
                    })
                else:

                    listing_fipe_price = None
                    if years_list and listing.year:
                        try:
                            fipe_result = await self._fetch_fipe_for_year(brand_id, model_id, listing.year, years_list)
                            if fipe_result:
                                listing_fipe_price = fipe_result["price"]
                        except Exception as e:
                            print(f"[Search] Per-listing FIPE lookup failed: {e}")

                    if listing_fipe_price:
                        listing_price_vo = Price.from_float(listing.price)
                        discount = Discount.calculate(listing_price_vo, listing_fipe_price)
                        status = "suspicious" if discount.is_suspicious() else "active"
                        score = self._score.execute(
                            discount=discount,
                            condition=listing.condition,
                            mileage=listing.mileage,
                            brand=listing.brand,
                            model=listing.model,
                            created_at=listing.scraped_at,
                        )
                        opportunity = self._create.execute(
                            listing=listing,
                            listing_id=hashlib.md5(_canonical_url(listing.url).encode()).hexdigest(),
                            fipe_price=listing_fipe_price,
                            discount=discount,
                            score=score,
                            status=status,
                            image_url=listing.image_url,
                        )
                        new_opportunities.append({
                            "id": opportunity.listing_id,
                            "brand": opportunity.brand,
                            "model": opportunity.model,
                            "year": opportunity.year,
                            "listing_price": float(opportunity.listing_price.amount),
                            "fipe_price": float(opportunity.fipe_price.amount),
                            "discount_percent": float(opportunity.discount.percentage),
                            "score": opportunity.score.value,
                            "mileage_km": opportunity.mileage or 0,
                            "source": opportunity.marketplace,
                            "url": opportunity.listing_url,
                            "image_url": listing.image_url,
                            "found_at": listing.scraped_at.isoformat() if listing.scraped_at else "",
                        })
                    else:
                        new_opportunities.append({
                            "id": str(uuid.uuid4()),
                            "brand": listing.brand,
                            "model": listing.model,
                            "year": listing.year,
                            "listing_price": float(listing.price),
                            "fipe_price": 0.0,
                            "discount_percent": 0.0,
                            "score": 0,
                            "mileage_km": listing.mileage or 0,
                            "source": listing.marketplace if hasattr(listing, 'marketplace') else "olx",
                            "url": listing.url,
                            "image_url": listing.image_url,
                            "found_at": listing.scraped_at.isoformat() if listing.scraped_at else "",
                        })
            except Exception as e:
                import traceback
                print(f"Error processing listing {listing.url}: {e}")
                traceback.print_exc()
                continue

        new_opportunities.sort(key=lambda o: o["score"], reverse=True)


        if self._search_cache:
            try:
                self._search_cache.set(brand, model, scrape_year, new_opportunities)
            except Exception as e:
                print(f"[Search] Cache write failed (non-fatal): {e}")

        return {
            "status": "success",
            "fipe": fipe_data,
            "fipe_error": fipe_error,
            "results": new_opportunities,
            "total_results": len(new_opportunities),
            "cached": False,
        }
