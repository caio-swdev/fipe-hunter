"""
curl_cffi-based OLX Scraper

Uses curl_cffi to impersonate a real Chrome browser TLS fingerprint,
bypassing Cloudflare without needing a headless browser.
"""
import logging
import re
import random
import time
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from fipe_business.domain.entities import Listing
from fipe_infra.utils.limiters import olx_limiter

if TYPE_CHECKING:
    from fipe_business.application.ports.rate_limit_event_repository import IRateLimitEventRepository
    from fipe_infra.repos.api_hit_repository import ApiHitRepository

logger = logging.getLogger(__name__)


class CurlOLXScraper:
    """Scraper for OLX marketplace using curl_cffi (bypasses Cloudflare via TLS impersonation)."""

    BASE_URL = "https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios/estado-rj"

    # Browser versions to impersonate (curl_cffi built-in profiles)
    IMPERSONATE_PROFILES = [
        "chrome120",
        "chrome119",
        "chrome116",
        "chrome110",
    ]

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
        return "olx"

    def _build_url(self) -> str:
        query_parts = []
        if self._brand:
            query_parts.append(self._brand)
        if self._model:
            query_parts.append(self._model)
        if self._year:
            query_parts.append(str(self._year))

        if query_parts:
            q = "+".join(query_parts)
            return f"{self.BASE_URL}?q={q}"
        return self.BASE_URL

    def scrape(self, max_listings: int = 50) -> List[Listing]:
        if self._api_hit_repo:
            try:
                self._api_hit_repo.record("olx")
            except Exception:
                pass
        listings: List[Listing] = []
        profile = random.choice(self.IMPERSONATE_PROFILES)

        session = curl_requests.Session(impersonate=profile)
        session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/",
        })

        try:
            # Warm-up: visit OLX homepage first (mimics real user)
            olx_limiter.acquire_sync()
            logger.info("[CurlOLX] Warming up with homepage visit...")
            session.get("https://www.olx.com.br/", timeout=15)
            time.sleep(random.uniform(0.5, 1.5))

            # Now search
            olx_limiter.acquire_sync()
            url = self._build_url()
            logger.info("[CurlOLX] Fetching: %s", url)
            session.headers["Referer"] = "https://www.olx.com.br/"
            response = session.get(url, timeout=20)
            response.raise_for_status()

            html = response.text
            logger.info("[CurlOLX] Got %d bytes of HTML", len(html))

            soup = BeautifulSoup(html, "html.parser")

            # Try multiple selectors (OLX changes these periodically)
            cards = soup.find_all("section", class_="olx-adcard")
            if not cards:
                cards = soup.find_all("li", attrs={"data-ds-component": "DS-AdCard"})
            if not cards:
                # Fallback: look for ad card links
                cards = soup.find_all("a", attrs={"data-ds-component": "DS-NewAdCard-Link"})
                if cards:
                    # Wrap each link in its parent container
                    cards = [a.parent for a in cards if a.parent]

            logger.info("[CurlOLX] Found %d ad cards", len(cards))

            for card in cards:
                if len(listings) >= max_listings:
                    break
                try:
                    listing = self._parse_card(card)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.warning("[CurlOLX] Error parsing card: %s", e)
                    continue

        except Exception as e:
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code == 429:
                logger.warning("[CurlOLX] Rate limited (429): %s", url if "url" in dir() else "unknown")
                if self._event_repo:
                    try:
                        self._event_repo.record("olx", url if "url" in dir() else None, 429, 0)
                    except Exception:
                        pass
            else:
                logger.error("[CurlOLX] Scraping error: %s", e)
            raise
        finally:
            session.close()

        logger.info("[CurlOLX] Scraped %d valid listings", len(listings))
        return listings

    def _parse_card(self, card) -> Listing | None:
        # Extract link
        link_el = card.find("a", attrs={"data-ds-component": "DS-NewAdCard-Link"})
        if not link_el:
            link_el = card.find("a", attrs={"data-testid": "adcard-link"})
        if not link_el:
            link_el = card.find("a", href=True)
        if not link_el:
            return None

        url = link_el.get("href", "")
        if not url.startswith("http"):
            url = f"https://www.olx.com.br{url}"

        # Extract title
        title_el = card.find("h2")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        brand, model, year = self._parse_title(title)

        # Extract price
        price_el = card.find("h3")
        if not price_el:
            # Try span with aria-label for price
            price_el = card.find("span", attrs={"aria-label": re.compile(r"R\$|reais", re.I)})
        if not price_el:
            return None

        price_text = price_el.get("aria-label") or price_el.get_text(strip=True)
        price = self._parse_price(price_text)
        if price <= 0:
            return None

        # Extract image
        image_url = self._extract_image(card)

        # Extract mileage
        mileage = self._extract_mileage(card)

        return Listing(
            brand=brand,
            model=model,
            year=year,
            price=price,
            mileage=mileage,
            condition="good",
            url=url,
            marketplace="olx",
            scraped_at=datetime.now(),
            image_url=image_url,
        )

    def _parse_title(self, title: str) -> tuple[str, str, int]:
        parts = title.strip().split()
        if len(parts) < 2:
            raise ValueError(f"Invalid title format: {title}")

        year = None
        year_index = -1
        for i, part in enumerate(parts):
            if part.isdigit() and len(part) == 4:
                potential_year = int(part)
                if 1950 <= potential_year <= 2026:
                    year = potential_year
                    year_index = i
                    break

        if year is None:
            year = datetime.now().year

        brand = parts[0]

        if year_index > 1:
            model = " ".join(parts[1:year_index])
        elif year_index == -1:
            model = " ".join(parts[1:])
        else:
            model = parts[1] if len(parts) > 1 else "Unknown"

        return brand, model, year

    def _parse_price(self, price_text: str) -> float:
        cleaned = price_text.replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _extract_image(self, card) -> str | None:
        img_el = card.find("img", src=re.compile(r"img\.olx\.com\.br"))
        if img_el:
            return img_el.get("src")
        img_el = card.find("img", attrs={"data-src": re.compile(r"img\.olx\.com\.br")})
        if img_el:
            return img_el.get("data-src")
        return None

    def _extract_mileage(self, card) -> int | None:
        text = card.get_text()
        match = re.search(r"([\d.]+)\s*km", text, re.IGNORECASE)
        if match:
            mileage_str = match.group(1).replace(".", "")
            try:
                return int(mileage_str)
            except ValueError:
                return None
        return None
