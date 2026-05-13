"""
API Tests: GET /api/admin/health

Covers the critical aggregation logic in get_admin_health():

1. Route is registered and returns 200
2. All top-level keys present in the response
3. Empty DB → all counts are zero, all services 'ok'
4. Service status is 'rate_limited' when a 429 was recorded < 1h ago
5. Service status is 'ok' when last 429 was > 1h ago (aged out)
6. count_24h reflects only events in the last 24h (not older ones)
7. Alert counts (pending, failed, sent_today) are correct
8. Scraping counts (opportunities_today, listings_today) are correct
9. Cache stats (fipe_entries, expired) are correct
10. Multiple services are tracked independently
"""
import os
import pytest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fipe_infra.database.models import (
    Base, RateLimitEventModel, AlertModel,
    OpportunityModel, ListingModel, PriceCacheModel,
)
from fipe_infra.database.session import get_db_session


_TEST_JWT_SECRET = "test-secret-for-pytest"
os.environ.setdefault("ADMIN_JWT_SECRET", _TEST_JWT_SECRET)


def _make_auth_headers() -> dict:
    """Generate a valid admin JWT Bearer header for test requests."""
    from app.auth import create_access_token
    token = create_access_token()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_db():
    """Function-scoped: each test gets a completely fresh in-memory database."""
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
    with TestClient(app, raise_server_exceptions=True, headers=_make_auth_headers()) as c:
        yield c
    app.dependency_overrides.clear()


def _add_rate_limit_event(db, service: str, minutes_ago: float):
    db.add(RateLimitEventModel(
        service=service,
        endpoint="/test",
        status_code=429,
        retry_attempt=0,
        occurred_at=datetime.utcnow() - timedelta(minutes=minutes_ago),
    ))
    db.commit()


def _add_alert(db, status: str, sent_minutes_ago: float | None = None):
    sent_at = (datetime.utcnow() - timedelta(minutes=sent_minutes_ago)) if sent_minutes_ago is not None else None
    import uuid
    db.add(AlertModel(
        alert_id=str(uuid.uuid4()),
        opportunity_id="opp-x",
        recipient_id="user-x",
        channel="telegram",
        message="test",
        status=status,
        sent_at=sent_at,
        created_at=datetime.utcnow(),
    ))
    db.commit()


def _add_opportunity(db, hours_ago: float = 1):
    import uuid
    db.add(OpportunityModel(
        listing_id=str(uuid.uuid4()),
        brand="VW", model="Gol", year=2020,
        listing_price=30000, fipe_price=40000,
        discount_percentage=25, discount_amount=10000,
        score_value=70, marketplace="olx",
        listing_url="https://olx.com.br/x",
        condition="good", status="active",
        created_at=datetime.utcnow() - timedelta(hours=hours_ago),
        updated_at=datetime.utcnow(),
    ))
    db.commit()


def _add_listing(db, hours_ago: float = 1):
    import uuid
    db.add(ListingModel(
        brand="Fiat", model="Uno", year=2018,
        price=20000, condition="good",
        url=f"https://olx.com.br/{uuid.uuid4()}",
        marketplace="olx",
        scraped_at=datetime.utcnow() - timedelta(hours=hours_ago),
    ))
    db.commit()


def _add_cache_entry(db, expired: bool = False):
    import uuid
    now = datetime.utcnow()
    expires = now - timedelta(hours=1) if expired else now + timedelta(hours=23)
    db.add(PriceCacheModel(
        cache_key=str(uuid.uuid4()),
        brand="VW", model="Gol", year=2020,
        price_value=40000, version="1.0 MPI",
        fipe_table_date="janeiro/2024",
        cached_at=now,
        expires_at=expires,
    ))
    db.commit()


class TestAdminHealthRoute:

    def test_route_returns_200(self, client):
        """GET /api/admin/health must return 200."""
        resp = client.get("/api/admin/health")
        assert resp.status_code == 200

    def test_response_has_all_top_level_keys(self, client):
        """Response must contain services, alerts, scraping, cache keys."""
        resp = client.get("/api/admin/health")
        data = resp.json()

        assert "services" in data
        assert "alerts" in data
        assert "scraping" in data
        assert "cache" in data

    def test_services_has_all_three_providers(self, client):
        """services must contain fipe, olx, webmotors."""
        resp = client.get("/api/admin/health")
        svc = resp.json()["services"]

        assert "fipe" in svc
        assert "olx" in svc
        assert "webmotors" in svc

    def test_service_entry_has_required_fields(self, client):
        """Each service entry must have status, last_429_at, count_24h."""
        resp = client.get("/api/admin/health")
        fipe = resp.json()["services"]["fipe"]

        assert "status" in fipe
        assert "last_429_at" in fipe
        assert "count_24h" in fipe

    def test_empty_db_returns_zeros_and_ok_status(self, client):
        """With no data in DB, all counts are 0 and all services are 'ok'."""
        resp = client.get("/api/admin/health")
        data = resp.json()

        for svc in ("fipe", "olx", "webmotors"):
            assert data["services"][svc]["status"] == "ok"
            assert data["services"][svc]["last_429_at"] is None
            assert data["services"][svc]["count_24h"] == 0

        assert data["alerts"]["pending"] == 0
        assert data["alerts"]["failed"] == 0
        assert data["alerts"]["sent_today"] == 0
        assert data["scraping"]["opportunities_today"] == 0
        assert data["scraping"]["listings_today"] == 0
        assert data["cache"]["fipe_entries"] == 0
        assert data["cache"]["expired"] == 0

    def test_rate_limited_status_when_event_within_1h(self, client, db_session):
        """A 429 recorded 30 minutes ago → service status is 'rate_limited'."""
        _add_rate_limit_event(db_session, "fipe", minutes_ago=30)

        resp = client.get("/api/admin/health")
        assert resp.json()["services"]["fipe"]["status"] == "rate_limited"

    def test_ok_status_when_last_event_older_than_1h(self, client, db_session):
        """A 429 recorded 90 minutes ago → service status is 'ok' (aged out)."""
        _add_rate_limit_event(db_session, "olx", minutes_ago=90)

        resp = client.get("/api/admin/health")
        assert resp.json()["services"]["olx"]["status"] == "ok"

    def test_count_24h_includes_recent_events_only(self, client, db_session):
        """count_24h must include only events within the last 24h, not older ones."""
        _add_rate_limit_event(db_session, "webmotors", minutes_ago=60)
        _add_rate_limit_event(db_session, "webmotors", minutes_ago=120)
        _add_rate_limit_event(db_session, "webmotors", minutes_ago=60 * 25)

        resp = client.get("/api/admin/health")
        assert resp.json()["services"]["webmotors"]["count_24h"] == 2

    def test_last_429_at_is_populated(self, client, db_session):
        """last_429_at must be an ISO string when an event exists."""
        _add_rate_limit_event(db_session, "fipe", minutes_ago=10)

        resp = client.get("/api/admin/health")
        last_at = resp.json()["services"]["fipe"]["last_429_at"]

        assert last_at is not None

        datetime.fromisoformat(last_at)

    def test_services_tracked_independently(self, client, db_session):
        """A 429 for one service must not affect another service's status."""
        _add_rate_limit_event(db_session, "olx", minutes_ago=5)

        resp = client.get("/api/admin/health")
        data = resp.json()["services"]

        assert data["olx"]["status"] == "rate_limited"
        assert data["fipe"]["status"] == "ok"
        assert data["webmotors"]["status"] == "ok"

    def test_alert_counts_by_status(self, client, db_session):
        """pending and failed counts reflect only those alert statuses."""
        _add_alert(db_session, "pending")
        _add_alert(db_session, "pending")
        _add_alert(db_session, "failed")
        _add_alert(db_session, "sent", sent_minutes_ago=30)
        _add_alert(db_session, "sent", sent_minutes_ago=30)

        resp = client.get("/api/admin/health")
        alerts = resp.json()["alerts"]

        assert alerts["pending"] == 2
        assert alerts["failed"] == 1
        assert alerts["sent_today"] == 2

    def test_sent_today_excludes_old_sent_alerts(self, client, db_session):
        """sent_today must not count alerts sent more than 24h ago."""
        _add_alert(db_session, "sent", sent_minutes_ago=60 * 25)

        resp = client.get("/api/admin/health")
        assert resp.json()["alerts"]["sent_today"] == 0

    def test_scraping_opportunities_today(self, client, db_session):
        """opportunities_today counts only opportunities created in the last 24h."""
        _add_opportunity(db_session, hours_ago=1)
        _add_opportunity(db_session, hours_ago=2)
        _add_opportunity(db_session, hours_ago=25)

        resp = client.get("/api/admin/health")
        assert resp.json()["scraping"]["opportunities_today"] == 2

    def test_scraping_listings_today(self, client, db_session):
        """listings_today counts only listings scraped in the last 24h."""
        _add_listing(db_session, hours_ago=1)
        _add_listing(db_session, hours_ago=26)

        resp = client.get("/api/admin/health")
        assert resp.json()["scraping"]["listings_today"] == 1

    def test_cache_entries_and_expired(self, client, db_session):
        """fipe_entries is the total, expired counts only expired rows."""
        _add_cache_entry(db_session, expired=False)
        _add_cache_entry(db_session, expired=False)
        _add_cache_entry(db_session, expired=True)

        resp = client.get("/api/admin/health")
        cache = resp.json()["cache"]

        assert cache["fipe_entries"] == 3
        assert cache["expired"] == 1
