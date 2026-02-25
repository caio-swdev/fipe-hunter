"""
Scraper Smoke Tests

Validates that OLX and WebMotors scrapers return real listings.
Run against local or prod environment:

    # Local
    pytest tests/e2e/test_scrapers_smoke.py -v -s

    # Against prod (future: run via CI post-deploy)
    BASE_URL=https://fipe-hunter-api.onrender.com pytest tests/e2e/test_scrapers_smoke.py -v -s

Known limitations:
    - WebMotors requires Chrome + Xvfb — skipped automatically if unavailable.
    - OLX is hardcoded to estado-rj; low-volume vehicles may return 0 results.
"""
import logging
import os
import shutil
import pytest

logger = logging.getLogger(__name__)

# Popular vehicle guaranteed to have many listings on OLX RJ
_SMOKE_BRAND = "Honda"
_SMOKE_MODEL = "HRV"
_SMOKE_YEAR = 2020


@pytest.mark.e2e
class TestOLXScraper:
    """Smoke test: OLX returns at least 1 listing for a common vehicle."""

    def test_returns_listings(self):
        from fipe_infra.scrapers.curl_olx_scraper import CurlOLXScraper

        scraper = CurlOLXScraper(
            brand=_SMOKE_BRAND,
            model=_SMOKE_MODEL,
            year=_SMOKE_YEAR,
        )

        listings = scraper.scrape(max_listings=5)

        logger.info("[OLX smoke] Got %d listings", len(listings))
        for l in listings:
            logger.info("  %s %s %d — R$%.0f @ %s", l.brand, l.model, l.year, l.price, l.url)

        assert len(listings) > 0, (
            f"OLX returned 0 listings for {_SMOKE_BRAND} {_SMOKE_MODEL} {_SMOKE_YEAR}. "
            "Possible causes: Cloudflare block, stale HTML selectors, or no listings in estado-rj."
        )

        for listing in listings:
            assert listing.price > 0, f"Listing has invalid price: {listing}"
            assert listing.url.startswith("http"), f"Listing has invalid URL: {listing.url}"
            assert listing.brand, "Listing is missing brand"


@pytest.mark.e2e
class TestWebMotorsScraper:
    """Smoke test: WebMotors returns at least 1 listing for a common vehicle."""

    def test_returns_listings(self):
        # Skip automatically if Chrome is not installed (e.g. Render free tier)
        if not shutil.which("google-chrome") and not shutil.which("chromium") and not shutil.which("chromium-browser"):
            pytest.skip("Chrome/Chromium not installed — WebMotors scraper requires headless Chrome")

        from fipe_infra.scrapers.webmotors_scraper import WebMotorsScraper

        scraper = WebMotorsScraper(
            brand=_SMOKE_BRAND,
            model=_SMOKE_MODEL,
            year=_SMOKE_YEAR,
        )

        listings = scraper.scrape(max_listings=5)

        logger.info("[WebMotors smoke] Got %d listings", len(listings))
        for l in listings:
            logger.info("  %s %s %d — R$%.0f @ %s", l.brand, l.model, l.year, l.price, l.url)

        assert len(listings) > 0, (
            f"WebMotors returned 0 listings for {_SMOKE_BRAND} {_SMOKE_MODEL} {_SMOKE_YEAR}. "
            "Possible causes: PerimeterX block, stale JS selector, or no results for that vehicle."
        )

        for listing in listings:
            assert listing.price > 0, f"Listing has invalid price: {listing}"
            assert listing.url.startswith("http"), f"Listing has invalid URL: {listing.url}"
