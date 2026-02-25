# ADR-0006: Use nodriver + Headless Chromium for WebMotors

**Status**: Accepted

**Date**: 2026-02-23

**Deciders**: Tech Lead, Development Team

**Related ADRs**:
- [ADR-0004: Use BeautifulSoup4 for Web Scraping](./0004-beautifulsoup-scraping.md)
- [ADR-0001: Clean Architecture](./0001-clean-architecture.md)

---

## Context

WebMotors is one of two target marketplaces for FIPE Hunter. Initial implementation attempted to scrape WebMotors using the same HTTP + BeautifulSoup approach used for OLX (ADR-0004). This failed in production on Render because WebMotors is protected by **PerimeterX** (now called HUMAN Security), a bot-detection layer that:

- Blocks plain HTTP clients (requests, curl_cffi) regardless of headers
- Detects and blocks basic headless browsers (Selenium, Playwright with default config)
- Fingerprints CDP (Chrome DevTools Protocol) traffic to identify automation

Additionally, the Docker image did not include a Chromium binary, causing a `FileNotFoundError` at scraper startup and returning 0 results on every scheduled job run.

The resolution required two coordinated changes: installing Chromium in the Docker runtime stage and switching the scraper from `headless=False` to `headless=True` so that Xvfb (a virtual display server) is not required.

---

## Decision Drivers

- WebMotors uses PerimeterX bot protection — blocks all regular HTTP clients and naive browser automation
- nodriver (undetected-chromium) passes PerimeterX by running a real Chrome instance via CDP with minimised automation fingerprints
- `headless=True` allows running without Xvfb, keeping Docker runtime simpler and more portable
- The `--no-sandbox` flag is required for Docker containers running as a non-root process
- Clean Architecture isolates the impact: only the adapter layer (`webmotors_scraper.py`) is affected; use cases and domain remain unchanged

---

## Considered Options

1. **nodriver + headless=True** (chosen) — Undetected Chrome via CDP, true headless, no Xvfb dependency
2. **Playwright with stealth plugin** — `playwright-stealth` patches automation signals but has weaker PerimeterX bypass than nodriver; requires separate browser binary management
3. **Paid scraping proxy (ScrapingBee / Zyte)** — Outsourced bypass, cost ~$50–$200/month, adds external dependency and latency, not appropriate for MVP budget

---

## Decision

**Chosen**: Option 1 — nodriver + headless=True

**Rationale**:
nodriver is specifically designed to pass PerimeterX and similar bot-protection systems. It patches Chrome's CDP fingerprint at the binary level rather than through JavaScript hooks, making it significantly harder to detect than Playwright stealth or undetected-chromedriver. Running headless removes the Xvfb requirement, which simplifies the Docker image (no display server setup) and improves reliability on PaaS environments like Render that do not provide a virtual display by default.

---

## Consequences

### Positive
- WebMotors scraper works on Render in production without manual intervention
- No Xvfb or virtual display server required — simpler Docker runtime
- nodriver updates regularly in response to PerimeterX fingerprint changes
- Clean Architecture means no domain or use-case changes were needed

### Negative
- Docker image is approximately 200 MB larger due to the Chromium binary
- WebMotors scraping is significantly slower than OLX (browser startup + page load vs. a single HTTP request)
- Two different scraping libraries are now maintained in parallel (curl_cffi for OLX, nodriver for WebMotors)

### Risks
- **Risk**: PerimeterX updates its fingerprint detection and blocks nodriver
  - **Mitigation**: Monitor scrape result counts in scheduled jobs; pin nodriver version and update proactively when PerimeterX detections are reported upstream
- **Risk**: Chromium apt package version diverges from nodriver's expected Chrome version
  - **Mitigation**: Pin Chromium version in Dockerfile; test on image rebuild

---

## Implementation Notes

The scraper startup sequence:

1. `nodriver` attempts to launch Chromium; if Xvfb is unavailable a `FileNotFoundError` is caught and logged as a warning (not a fatal error)
2. Execution falls through to the `headless=True` code path, which does not require a display
3. The `--no-sandbox` flag is passed via Chrome launch arguments for Docker non-root compatibility

**Dockerfile change (runtime stage):**
```dockerfile
RUN apt-get update && apt-get install -y chromium chromium-driver --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
```

**Scraper change:**
```python
# webmotors_scraper.py line 142
browser = await nodriver.start(headless=True)
```

The `IScraper` interface contract is unchanged. Only the adapter implementation was modified.

---

## Validation

**Success Criteria**:
- WebMotors scraper returns > 0 listings on scheduled Render job runs
- No `FileNotFoundError` in production logs
- Scrape completion time < 5 minutes per run (browser startup overhead acceptable)

**Review Date**: 2026-05-23 (reassess if PerimeterX begins blocking nodriver or if image size becomes a constraint)

---

## References
- [nodriver GitHub](https://github.com/ultrafunkamsterdam/nodriver)
- [PerimeterX / HUMAN Security overview](https://www.humansecurity.com/products/bot-defender)
- [ADR-0004: BeautifulSoup for Web Scraping](./0004-beautifulsoup-scraping.md) — OLX approach (HTTP + HTML parsing)
- [Render deployment docs — no virtual display](https://render.com/docs)
