"""
API Tests: Rate Limiting + Search Cache Integration

Covers:
1. Per-session inbound limit (10/hour via slowapi)
2. Search result cache (15-min SQLite cache, "cached": true on hit)

All external I/O (scrapers, FIPE API) is mocked — zero real network calls.
"""
import pytest
from contextlib import contextmanager
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fipe_infra.database.models import Base
from fipe_infra.database.session import get_db_session


# ---------------------------------------------------------------------------
# Database fixture (in-memory, same as test_search_routes.py)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_db):
    session = test_db()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    from app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Reset slowapi storage between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_limiter():
    """Clear all rate-limit counters before each test."""
    from app.limiter import limiter
    if hasattr(limiter, "_storage"):
        limiter._storage.reset()
    yield


# ---------------------------------------------------------------------------
# Helper: mock scrapers at the factory level
# ---------------------------------------------------------------------------

@contextmanager
def mock_scrapers_factory(olx_listings=None, wm_listings=None):
    """
    Patch CurlOLXScraper and WebMotorsScraper where they are wired (the factory).
    Returns (mock_olx_cls, mock_wm_cls).
    """
    olx_listings = olx_listings or []
    wm_listings = wm_listings or []

    mock_olx = MagicMock()
    mock_olx.return_value.scrape.return_value = olx_listings

    mock_wm = MagicMock()
    mock_wm.return_value.scrape.return_value = wm_listings

    with patch("app.main.factories.search_factory.CurlOLXScraper", mock_olx), \
         patch("app.main.factories.search_factory.WebMotorsScraper", mock_wm):
        yield mock_olx, mock_wm


def _search(client, session_cookie: str, brand="Honda", model="Civic"):
    """POST /api/search/vehicle with a fixed session cookie (no year → no FIPE call)."""
    return client.post(
        "/api/search/vehicle",
        json={"brand": brand, "model": model},
        cookies={"session_id": session_cookie},
    )


# ---------------------------------------------------------------------------
# Rate Limit Tests
# ---------------------------------------------------------------------------

class TestPerSessionRateLimit:

    def test_10_requests_succeed(self, client):
        """10 POSTs from the same session all return 200."""
        with mock_scrapers_factory():
            responses = [_search(client, "rl-test-session-ok") for _ in range(10)]

        statuses = [r.status_code for r in responses]
        assert all(s == 200 for s in statuses), f"Unexpected statuses: {statuses}"

    def test_11th_request_returns_429(self, client):
        """11th POST from the same session returns 429 Too Many Requests."""
        with mock_scrapers_factory():
            for _ in range(10):
                _search(client, "rl-test-session-11th")
            eleventh = _search(client, "rl-test-session-11th")

        assert eleventh.status_code == 429

    def test_different_sessions_independent_quota(self, client):
        """Session A exhausted → Session B still gets 200."""
        with mock_scrapers_factory():
            # Exhaust session A
            for _ in range(10):
                _search(client, "rl-test-session-A")

            # Session B should still succeed
            resp_b = _search(client, "rl-test-session-B")

        assert resp_b.status_code == 200


# ---------------------------------------------------------------------------
# Cache Integration Test
# ---------------------------------------------------------------------------

class TestSearchCache:

    def test_second_search_uses_cache_not_scraper(self, client):
        """
        Two identical searches within the 15-min TTL:
        - First: scraper is called, results stored in cache.
        - Second: served from cache, scraper NOT called again, "cached": true.
        """
        from fipe_business.domain.entities import Listing
        from datetime import datetime

        listing = Listing(
            brand="Honda",
            model="Civic",
            year=2020,
            price=50000.0,
            url="https://olx.com.br/civic-test-1",
            marketplace="olx",
            mileage=45000,
            condition="good",
            scraped_at=datetime.now(),
        )

        mock_olx = MagicMock()
        mock_olx.return_value.scrape.return_value = [listing]
        mock_wm = MagicMock()
        mock_wm.return_value.scrape.return_value = []

        session_cookie = "rl-cache-test-session"
        payload = {"brand": "Honda", "model": "Civic", "year": 2020}

        with patch("app.main.factories.search_factory.CurlOLXScraper", mock_olx), \
             patch("app.main.factories.search_factory.WebMotorsScraper", mock_wm), \
             patch(
                 "fipe_business.application.use_cases.lookup_fipe_price.LookupFIPEPriceUseCase.execute",
             ) as mock_fipe:

            mock_fipe.return_value = None  # No FIPE price (auto-AsyncMocked for async execute)

            # First search — hits scrapers
            r1 = client.post(
                "/api/search/vehicle",
                json=payload,
                cookies={"session_id": session_cookie},
            )
            assert r1.status_code == 200
            data1 = r1.json()
            assert data1.get("cached") is False

            # Second search — same params, same session, within TTL
            r2 = client.post(
                "/api/search/vehicle",
                json=payload,
                cookies={"session_id": session_cookie},
            )
            assert r2.status_code == 200
            data2 = r2.json()

        # Scraper should have been instantiated exactly once (first request only)
        assert mock_olx.call_count == 1, (
            f"OLX scraper was called {mock_olx.call_count} times; expected 1 (second should use cache)"
        )

        # Second response explicitly flagged as cached
        assert data2.get("cached") is True, (
            f"Expected 'cached': true on second response but got: {data2.get('cached')}"
        )
