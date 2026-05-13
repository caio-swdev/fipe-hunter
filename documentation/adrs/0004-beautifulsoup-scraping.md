# ADR-0004: Use BeautifulSoup4 for Web Scraping

**Status**: Accepted

**Date**: 2026-02-05

**Deciders**: Tech Lead

**Related ADRs**: [ADR-0001: Clean Architecture](0001-clean-architecture.md)

---

## Context

FIPE Hunter needs to scrape vehicle listings from OLX and WebMotors marketplaces. These sites primarily serve static HTML (minimal JavaScript rendering).

---

## Decision Drivers

- **Simplicity**: OLX/WebMotors serve mostly static HTML
- **Performance**: Lightweight parsing faster than browser automation
- **Reliability**: Mature library with extensive documentation
- **MVP Speed**: Quick implementation for MVP
- **Resource Usage**: Low memory footprint

---

## Considered Options

1. **BeautifulSoup4** - HTML parsing library
2. **Selenium/Playwright** - Browser automation
3. **Scrapy** - Full scraping framework

---

## Decision

**Chosen**: Option 1 - BeautifulSoup4

**Rationale**:
BeautifulSoup4 is sufficient for MVP because:
- OLX and WebMotors primarily serve static HTML
- No complex JavaScript rendering required
- Faster and lighter than browser automation
- Simple API, easy to maintain
- Can migrate to Playwright if JavaScript rendering becomes necessary

---

## Consequences

### Positive
- **Lightweight**: Low memory usage, fast parsing
- **Simple**: Easy to learn and maintain
- **Reliable**: Mature library, extensive documentation
- **Flexible**: Works with lxml parser for performance

### Negative
- **No JavaScript**: Cannot handle dynamic content
- **Manual HTTP**: Need to handle requests, sessions manually
- **Fragile**: Breaks when HTML structure changes

### Risks
- **Risk**: Marketplaces add JavaScript rendering
  - **Mitigation**: Monitor for changes; migrate to Playwright if needed (Clean Architecture isolates impact to adapter layer)
- **Risk**: Anti-bot measures block scraper
  - **Mitigation**: User-agent rotation, request delays, exponential backoff

---

## Implementation Notes

**Example Scraper:**
```python
# src/adapters/scrapers/olx_scraper.py
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent

class OLXScraper:
    def scrape(self) -> list[Listing]:
        ua = UserAgent()
        headers = {"User-Agent": ua.random}
        response = requests.get(OLX_URL, headers=headers)
        soup = BeautifulSoup(response.content, "lxml")

        listings = []
        for item in soup.select(".listing-item"):
            listing = self._parse_listing(item)
            listings.append(listing)

        return listings
```

**Migration Path to Playwright:**
If JavaScript rendering becomes required:
1. Create `PlaywrightOLXScraper` implementing `IScraper`
2. Swap in composition root (`main.py`)
3. No changes to use cases or domain

---

## Validation

**Success Criteria**:
- Successfully scrape 20-50 listings per marketplace
- Parse rate > 95% (< 5% failures)
- Performance < 2 minutes for 50 listings

**Review Date**: 2026-04-05 (monitor for JavaScript rendering changes)

---

## Actual Implementation (2026-02-23)

Production deployment revealed that the original assumptions in this ADR held for OLX but not for WebMotors. The following amendments document reality as-shipped.

### OLX (this ADR — Accepted, unchanged)

OLX is scraped with BeautifulSoup4 for HTML parsing, but the HTTP client was changed from `requests` to **`curl_cffi`** (not plain `requests` as shown in the example above). `curl_cffi` impersonates a real browser's TLS fingerprint, which is required to bypass Cloudflare protection on OLX. The scraping logic and HTML parsing remain as described in this ADR.

| Component | Library | Notes |
|-----------|---------|-------|
| HTTP Client | `curl_cffi` 0.7+ | TLS fingerprint impersonation (Cloudflare bypass) |
| HTML Parsing | BeautifulSoup4 4.12+ | Static HTML parsing, unchanged |
| User-Agent | `fake-useragent` 1.4+ | Anti-bot fallback measure |

### WebMotors (diverged — superseded by ADR-0006)

WebMotors **diverged at implementation** and does not use BeautifulSoup4. WebMotors is protected by **PerimeterX** which blocks all pure HTTP clients regardless of headers or TLS fingerprint. The implemented solution is:

- **Library**: `nodriver` (undetected-chromium) + Chromium binary (headless)
- **Technique**: Real headless browser via CDP (Chrome DevTools Protocol) with minimised automation fingerprints
- **Status**: ADR-0004 does not apply to WebMotors; see [ADR-0006](./0006-nodriver-headless-chromium.md) for the full decision record

### Summary of ADR-0004 scope

| Marketplace | ADR-0004 applies? | Actual approach |
|-------------|------------------|----------------|
| OLX | Yes (with curl_cffi amendment) | curl_cffi + BeautifulSoup4 |
| WebMotors | No — superseded by ADR-0006 | nodriver + Chromium headless |

---

## References
- [BeautifulSoup4 Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Web Scraping Best Practices](https://www.scrapingbee.com/blog/web-scraping-best-practices/)
- [ADR-0006: nodriver + Headless Chromium for WebMotors](./0006-nodriver-headless-chromium.md)
