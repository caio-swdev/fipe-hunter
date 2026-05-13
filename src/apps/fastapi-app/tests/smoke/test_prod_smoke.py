"""
Production Smoke Tests

Hits the live prod URL to verify critical paths are working.
Run manually or via the fipe-hunter-smoke GitHub Actions cron.

Usage:
    pytest tests/smoke/test_prod_smoke.py -v

    # Against a different URL (e.g. staging):
    FIPE_HUNTER_URL=http://localhost:8000 pytest tests/smoke/test_prod_smoke.py -v

Requirements:
    pip install httpx pytest
"""
import os
import pytest
import httpx

BASE_URL = os.environ.get("FIPE_HUNTER_URL", "https://fipe-hunter-api.onrender.com").rstrip("/")


COLD_START_TIMEOUT = 45
DEFAULT_TIMEOUT = 20
SCRAPER_TIMEOUT = 30


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=COLD_START_TIMEOUT) as c:


        try:
            c.get("/health", timeout=90)
        except Exception:
            pass
        yield c


@pytest.fixture(scope="session")
def toyota_brand_id(client):
    """Fetch Toyota brand_id from FIPE catalog — used by downstream tests."""
    r = client.get("/api/v1/fipe/catalog/models", params={"brand_name": "Toyota"})
    assert r.status_code == 200, f"Models lookup failed: {r.text}"
    data = r.json()
    brand_id = data.get("brand_id")
    assert brand_id, "brand_id missing from /catalog/models response"
    return brand_id


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "healthy"


def test_fipe_models_toyota(client):
    r = client.get("/api/v1/fipe/catalog/models", params={"brand_name": "Toyota"})
    assert r.status_code == 200
    data = r.json()
    assert "brand_id" in data
    assert "models" in data
    assert len(data["models"]) > 0


def test_fipe_versions_corolla(client, toyota_brand_id):
    """Covers both a recent year (2022) and an older year (2014) to catch alphabetical cap bugs."""
    for year in [2022, 2014]:
        r = client.get(
            "/api/v1/fipe/catalog/versions",
            params={"brand_id": toyota_brand_id, "model_base": "Corolla", "year": year},
            timeout=25,
        )
        assert r.status_code == 200, f"Versions {year} failed ({r.status_code}): {r.text}"
        data = r.json()
        assert "versions" in data
        assert len(data["versions"]) > 0, f"versions empty for year {year} — cap or FIPE lookup broken"


def test_fipe_years_corolla(client, toyota_brand_id):

    r = client.get("/api/v1/fipe/catalog/models", params={"brand_name": "Toyota"})
    models = r.json().get("models", [])
    corolla = next((m for m in models if "Corolla" in m.get("name", "")), None)
    if not corolla:
        pytest.skip("No Corolla model found in FIPE catalog")
    model_id = corolla.get("model_id") or corolla.get("id")
    if not model_id:
        pytest.skip("model_id not present in models response")

    r = client.get(
        "/api/v1/fipe/catalog/years",
        params={"brand_id": toyota_brand_id, "model_id": model_id},
        timeout=DEFAULT_TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert "years" in data
    assert len(data["years"]) > 0


def test_scraper_olx(client):
    r = client.post(
        "/api/scrape/olx",
        json={"brand": "fiat", "model": "uno", "max_listings": 3},
        timeout=SCRAPER_TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert "error" not in data, f"Scraper error: {data.get('error')}"
    assert data.get("total", 0) > 0, "OLX returned 0 results"


def test_dashboard_summary(client):
    r = client.get("/api/dashboard/summary", timeout=DEFAULT_TIMEOUT)
    assert r.status_code == 200
    data = r.json()

    assert data.get("status") == "success"
    assert "total_opportunities" in data.get("data", {})
