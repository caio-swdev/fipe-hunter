"""
Scrape Routes — dev/debug endpoints to test scrapers individually.

POST /api/scrape/olx       → run CurlOLXScraper directly
POST /api/scrape/webmotors → run WebMotorsScraper directly
"""
import traceback
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/scrape", tags=["scrape"])


class ScrapeRequest(BaseModel):
    brand: str = Field(..., min_length=2)
    model: str = Field(..., min_length=2)
    year: Optional[int] = Field(None, ge=1950, le=2030)
    max_listings: int = Field(10, ge=1, le=50)


@router.get("/diag")
def scrape_diag():
    """Diagnostic: check what's available for WebMotors scraping."""
    import shutil, subprocess, os, time
    chrome = shutil.which("google-chrome-stable") or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    xvfb = shutil.which("Xvfb")
    display = os.environ.get("DISPLAY", "")
    whoami = subprocess.run(["whoami"], capture_output=True, text=True).stdout.strip()
    chrome_version = ""
    if chrome:
        try:
            chrome_version = subprocess.run([chrome, "--version"], capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception as e:
            chrome_version = f"error: {e}"

    # Test Xvfb + Chrome headful launch
    xvfb_test = "not tested"
    chrome_headful_test = "not tested"
    if xvfb and chrome:
        try:
            xvfb_proc = subprocess.Popen(["Xvfb", ":98", "-screen", "0", "1920x1080x24"],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            time.sleep(1.5)
            rc = xvfb_proc.poll()
            if rc is None:
                xvfb_test = "started ok"
                env = os.environ.copy()
                env["DISPLAY"] = ":98"
                result = subprocess.run(
                    [chrome, "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                     "--headless=false", "--remote-debugging-port=0", "--version"],
                    capture_output=True, text=True, timeout=10, env=env
                )
                chrome_headful_test = f"rc={result.returncode} stdout={result.stdout[:200]} stderr={result.stderr[:200]}"
                xvfb_proc.kill()
            else:
                stderr = xvfb_proc.stderr.read().decode()
                xvfb_test = f"exited rc={rc}: {stderr[:200]}"
        except Exception as e:
            xvfb_test = f"error: {e}"

    return {
        "whoami": whoami,
        "chrome_binary": chrome,
        "chrome_version": chrome_version,
        "xvfb_binary": xvfb,
        "display_env": display,
        "xvfb_test": xvfb_test,
        "chrome_headful_test": chrome_headful_test,
    }


@router.get("/nodriver-args")
def nodriver_args():
    """Show the exact Chrome args nodriver would use."""
    try:
        import nodriver as uc
        config = uc.Config(
            headless=True,
            sandbox=False,
            browser_args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                          "--disable-crash-reporter", "--no-first-run", "--no-default-browser-check"],
        )
        return {"args": config.as_list()}
    except Exception as e:
        return {"error": str(e)}


@router.post("/olx")
def scrape_olx(body: ScrapeRequest):
    try:
        from fipe_infra.scrapers.curl_olx_scraper import CurlOLXScraper
        scraper = CurlOLXScraper(brand=body.brand, model=body.model, year=body.year)
        listings = scraper.scrape(max_listings=body.max_listings)
        return {
            "source": "olx",
            "total": len(listings),
            "results": [
                {"brand": l.brand, "model": l.model, "year": l.year, "price": l.price, "url": l.url}
                for l in listings
            ],
        }
    except Exception as e:
        return {"source": "olx", "error": str(e), "traceback": traceback.format_exc()}


@router.get("/webmotors-api-probe")
def webmotors_api_probe():
    """Probe WebMotors API endpoints with curl-cffi to find a working JSON API."""
    from curl_cffi import requests as curl_requests
    session = curl_requests.Session(impersonate="chrome120")
    session.headers.update({
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
        "Referer": "https://www.webmotors.com.br/",
        "Origin": "https://www.webmotors.com.br",
    })
    results = {}
    candidates = [
        ("api_v3_cars", "GET", "https://www.webmotors.com.br/api/search/v3/cars",
         {"TypesIds": "1", "Brand": "Toyota", "Model": "Corolla", "Page": "1", "PageSize": "3"}),
        ("api_v2_cars", "GET", "https://www.webmotors.com.br/api/search/v2/cars",
         {"TypesIds": "1", "Brand": "Toyota", "Model": "Corolla", "Page": "1", "PageSize": "3"}),
        ("search_page_curl", "GET", "https://www.webmotors.com.br/carros/sp/toyota/corolla", {}),
    ]
    for name, method, url, params in candidates:
        try:
            resp = session.request(method, url, params=params, timeout=12)
            ct = resp.headers.get("content-type", "")
            snippet = resp.text[:300]
            results[name] = {"status": resp.status_code, "content_type": ct, "snippet": snippet}
        except Exception as e:
            results[name] = {"error": str(e)}
    session.close()
    return results


@router.get("/webmotors-page-diag")
async def webmotors_page_diag():
    """Diagnose what WebMotors returns: title, card count, first 300 chars of body text."""
    try:
        from playwright.async_api import async_playwright
        try:
            from playwright_stealth import stealth_async
            use_stealth = True
        except ImportError:
            use_stealth = False
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--no-zygote",
                      "--disable-gpu", "--disable-dev-shm-usage",
                      "--disable-crash-reporter", "--disable-breakpad"],
            )
            page = await browser.new_page()
            if use_stealth:
                await stealth_async(page)
            url = "https://www.webmotors.com.br/carros/sp/toyota/corolla?tipoveiculo=carros"
            await page.goto(url, timeout=25000)
            try:
                await page.wait_for_selector('[class*="Card"]', timeout=10000)
            except Exception:
                pass
            title = await page.title()
            card_count = await page.evaluate("document.querySelectorAll('[class*=\"Card\"]').length")
            body_text = await page.evaluate("document.body ? document.body.innerText.slice(0, 300) : ''")
            await browser.close()
            return {"title": title, "card_count": card_count, "body_snippet": body_text, "stealth": use_stealth}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.get("/browser-test")
async def browser_test():
    """Test Playwright Chromium launch — confirms browser works in this container."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--no-zygote",
                      "--disable-gpu", "--disable-dev-shm-usage",
                      "--disable-crash-reporter", "--disable-breakpad"],
            )
            page = await browser.new_page()
            await page.goto("about:blank")
            title = await page.title()
            version = browser.version
            await browser.close()
            return {"browser": "ok", "title": title, "version": version}
    except Exception as e:
        return {"browser": "failed", "error": str(e), "traceback": traceback.format_exc()}



@router.post("/webmotors")
def scrape_webmotors(body: ScrapeRequest):
    try:
        from fipe_infra.scrapers.webmotors_scraper import WebMotorsScraper
        scraper = WebMotorsScraper(brand=body.brand, model=body.model, year=body.year)
        listings = scraper.scrape(max_listings=body.max_listings)
        return {
            "source": "webmotors",
            "total": len(listings),
            "results": [
                {"brand": l.brand, "model": l.model, "year": l.year, "price": l.price, "url": l.url}
                for l in listings
            ],
        }
    except Exception as e:
        return {"source": "webmotors", "error": str(e), "traceback": traceback.format_exc()}
