"""
WebMotors Scraper

Uses Playwright (container-optimized Chromium) + playwright-stealth to bypass
PerimeterX protection and scrape real vehicle listings from WebMotors.

Replaced nodriver because Debian's system chromium crashes with SIGTRAP on
Render's seccomp profile. Playwright ships its own Chromium binary built for
headless container environments.
"""
import asyncio
import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from fipe_business.domain.entities import Listing
from fipe_infra.utils.limiters import webmotors_limiter

if TYPE_CHECKING:
    from fipe_business.application.ports.rate_limit_event_repository import IRateLimitEventRepository
    from fipe_infra.repos.api_hit_repository import ApiHitRepository

logger = logging.getLogger(__name__)


_JS_EXTRACT_CARS = """
JSON.stringify(
    Array.from(document.querySelectorAll('a[href*="/comprar/"]'))
        .reduce((acc, a) => {
            const card = a.closest('[class*="Card"]');
            if (!card || acc.seen.has(card)) return acc;
            acc.seen.add(card);

            const href = a.getAttribute('href') || '';
            if (!href.includes('/comprar/')) return acc;

            const h2 = card.querySelector('h2');
            const title = h2 ? h2.textContent.trim() : '';

            const allText = card.textContent || '';
            const priceMatch = allText.match(/R\\$\\s*([\\d.,]+)/);
            if (!priceMatch) return acc;

            const img = card.querySelector('img');
            const imgSrc = img ? (img.src || img.getAttribute('data-src') || '') : '';

            acc.results.push({
                href: href,
                title: title,
                price: priceMatch[1],
                imgSrc: imgSrc.substring(0, 1000)
            });
            return acc;
        }, { seen: new Set(), results: [] })
        .results
)
"""


class WebMotorsScraper:
    """Scraper for WebMotors marketplace using Playwright + stealth (bypasses PerimeterX)."""

    BASE_URL = "https://www.webmotors.com.br/carros"

    def __init__(
        self,
        brand: str = "",
        model: str = "",
        year: int | None = None,
        event_repo: "Optional[IRateLimitEventRepository]" = None,
        api_hit_repo: "Optional[ApiHitRepository]" = None,
    ):
        self._brand = brand.strip()
        self._model = model.strip()
        self._year = year
        self._event_repo = event_repo
        self._api_hit_repo = api_hit_repo

    def get_marketplace_name(self) -> str:
        return "webmotors"

    def _build_url(self) -> str:
        brand_slug = self._brand.lower().replace(" ", "-") if self._brand else ""
        model_slug = self._model.lower().replace(" ", "-") if self._model else ""

        path = f"{self.BASE_URL}/sp"
        if brand_slug:
            path += f"/{brand_slug}"
        if model_slug:
            path += f"/{model_slug}"
        if self._year:
            path += f"/de.{self._year}/ate.{self._year}"

        params = ["tipoveiculo=carros"]
        if self._brand:
            params.append(f"marca1={self._brand.lower()}")
        if self._model:
            params.append(f"modelo1={self._model.lower()}")
        if self._year:
            params.append(f"anode={self._year}")
            params.append(f"anoate={self._year}")

        return f"{path}?{'&'.join(params)}"

    def scrape(self, max_listings: int = 50) -> List[Listing]:
        """Scrape WebMotors listings. Runs Playwright in an async event loop."""
        if self._api_hit_repo:
            try:
                self._api_hit_repo.record("webmotors")
            except Exception:
                pass
        return asyncio.run(self._scrape_async(max_listings))

    async def _scrape_async(self, max_listings: int) -> List[Listing]:
        from playwright.async_api import async_playwright

        try:
            from playwright_stealth import stealth_async
            use_stealth = True
        except ImportError:
            use_stealth = False
            logger.warning("[WebMotors] playwright-stealth not found, running without stealth")

        unique_cars = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--no-zygote",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-crash-reporter",
                    "--disable-breakpad",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
            )
            try:
                page = await browser.new_page()

                if use_stealth:
                    await stealth_async(page)

                url = self._build_url()
                await webmotors_limiter.acquire()
                logger.info("[WebMotors] Fetching: %s", url)
                await page.goto(url, timeout=25000)


                try:
                    await page.wait_for_selector('[class*="Card"]', timeout=10000)
                except Exception:
                    logger.warning("[WebMotors] Cards selector timed out, proceeding anyway")

                title = await page.title()
                logger.info("[WebMotors] Page title: %s", title)

                if "denied" in title.lower():
                    logger.warning("[WebMotors] Blocked by PerimeterX")
                    return []

                result = await page.evaluate(_JS_EXTRACT_CARS)
                import json
                raw_cars = json.loads(result) if result else []
                logger.info("[WebMotors] Raw cards: %d", len(raw_cars))

                seen_urls = set()
                for car in raw_cars:
                    if car["href"] not in seen_urls:
                        seen_urls.add(car["href"])
                        unique_cars.append(car)
                logger.info("[WebMotors] Unique cards after dedup: %d", len(unique_cars))

            except Exception as e:
                logger.error("[WebMotors] Scraping error: %s", e)
                raise
            finally:
                await browser.close()

        listings: List[Listing] = []
        for car in unique_cars:
            if len(listings) >= max_listings:
                break
            try:
                listing = self._parse_car(car)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.warning("[WebMotors] Error parsing car: %s", e)
                continue

        logger.info("[WebMotors] Scraped %d valid listings", len(listings))
        return listings

    def _parse_car(self, car: dict) -> Listing | None:
        href = car.get("href", "")
        title = car.get("title", "")
        price_str = car.get("price", "")
        img_src = car.get("imgSrc", "")

        if not href or not price_str:
            return None

        price = self._parse_price(price_str)
        if price <= 0:
            return None

        brand, model = self._parse_title(title)

        version_str = self._extract_version_from_url(href)
        if version_str:
            model = f"{model} {version_str}"

        year = self._extract_year_from_url(href)
        mileage = None

        if not href.startswith("http"):
            href = f"https://www.webmotors.com.br{href}"

        return Listing(
            brand=brand,
            model=model,
            year=year,
            price=price,
            mileage=mileage,
            condition="good",
            url=href,
            marketplace="webmotors",
            scraped_at=datetime.now(),
            image_url=img_src or None,
        )

    def _parse_title(self, title: str) -> tuple[str, str]:
        parts = title.strip().split()
        if len(parts) >= 2:
            return parts[0], " ".join(parts[1:])
        elif len(parts) == 1:
            return parts[0], "Unknown"
        return self._brand or "Unknown", self._model or "Unknown"

    def _extract_version_from_url(self, url: str) -> str:
        match = re.search(r'/comprar/[^/]+/[^/]+/([^/]+)/', url)
        if not match:
            return ''
        slug = match.group(1)
        parts = []
        for part in slug.split('-'):
            if re.match(r'^\d{2}$', part):
                parts.append(f"{part[0]}.{part[1]}")
            else:
                parts.append(part.upper())
        return ' '.join(parts)

    def _parse_price(self, price_text: str) -> float:
        cleaned = price_text.replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _extract_year_from_url(self, url: str) -> int:
        match = re.search(r"/(\d{4})-(\d{4})/", url)
        if match:
            return int(match.group(2))
        match = re.search(r"/(\d{4})/\d+$", url)
        if match:
            year = int(match.group(1))
            if 1950 <= year <= 2027:
                return year
        return self._year or datetime.now().year
