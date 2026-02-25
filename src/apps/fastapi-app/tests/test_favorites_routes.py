"""
API Tests: GET/POST/DELETE /api/favorites

Covers:
1. App import smoke test (catches missing dependencies like slowapi at import time)
2. GET /api/favorites — empty list for a fresh session
3. POST /api/favorites/{id} — adds a favorite, returns status "added"
4. DELETE /api/favorites/{id} — removes a favorite, returns status "removed"
5. GET /api/favorites — returns full opportunity data after adding
6. GET /api/favorites — silently skips orphan IDs (opportunity deleted from DB)
7. POST /api/favorites/{id} — duplicate add is idempotent (no 500 crash)

Session cookie is created automatically by SessionMiddleware on the first request.
TestClient preserves cookies across calls within the same `with` block.
"""
import pytest
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fipe_infra.database.models import Base, OpportunityModel
from fipe_infra.database.session import get_db_session


# ---------------------------------------------------------------------------
# Database fixtures
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
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _seed_opportunity(db_session, listing_id: str) -> OpportunityModel:
    """Insert a minimal OpportunityModel row and return it."""
    opp = OpportunityModel(
        listing_id=listing_id,
        brand="Honda",
        model="Civic",
        year=2020,
        listing_price=50000.0,
        fipe_price=70000.0,
        discount_percentage=28.57,
        discount_amount=20000.0,
        score_value=85,
        marketplace="olx",
        listing_url=f"https://olx.com.br/{listing_id}",
        condition="good",
        mileage=45000,
        status="active",
        image_url=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(opp)
    db_session.commit()
    return opp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFavoritesRoutes:

    def test_app_import_does_not_raise(self):
        """
        Smoke test: importing app.main must succeed without errors.

        Catches missing top-level dependencies (e.g. slowapi) that prevent
        uvicorn from loading the application — the root cause of the
        'Carregando favoritos...' hang in production.
        """
        from app.main import app  # noqa: F401 — import side-effects are the assertion
        assert app is not None

    def test_list_favorites_empty_for_new_session(self, client):
        """
        GET /api/favorites — fresh session returns an empty list, not a loading hang.
        """
        resp = client.get("/api/favorites")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"] == []
        assert data["total"] == 0

    def test_add_favorite(self, client, db_session):
        """
        POST /api/favorites/{id} — returns status "added" with the opportunity id.
        """
        _seed_opportunity(db_session, "add-test-opp-001")

        resp = client.post("/api/favorites/add-test-opp-001")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "added"
        assert data["opportunity_id"] == "add-test-opp-001"

    def test_remove_favorite(self, client, db_session):
        """
        DELETE /api/favorites/{id} — returns status "removed" with the opportunity id.
        """
        _seed_opportunity(db_session, "remove-test-opp-001")
        client.post("/api/favorites/remove-test-opp-001")

        resp = client.delete("/api/favorites/remove-test-opp-001")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "removed"
        assert data["opportunity_id"] == "remove-test-opp-001"

    def test_list_favorites_returns_opportunity_data(self, client, db_session):
        """
        GET /api/favorites — after adding a favorite returns the full opportunity payload.
        """
        _seed_opportunity(db_session, "list-test-opp-001")
        client.post("/api/favorites/list-test-opp-001")

        resp = client.get("/api/favorites")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["total"] >= 1

        ids = [item["id"] for item in data["data"]]
        assert "list-test-opp-001" in ids

        item = next(i for i in data["data"] if i["id"] == "list-test-opp-001")
        assert item["brand"] == "Honda"
        assert item["model"] == "Civic"
        assert item["year"] == 2020
        assert item["listing_price"] == pytest.approx(50000.0)
        assert item["fipe_price"] == pytest.approx(70000.0)
        assert item["discount_percent"] == pytest.approx(28.57, abs=0.01)
        assert item["score"] == 85
        assert item["source"] == "olx"
        assert "olx.com.br" in item["url"]

    def test_list_favorites_skips_orphan_ids(self, client, db_session):
        """
        GET /api/favorites — orphan favorite IDs (opportunity not in DB) are silently
        skipped rather than raising a 500.
        """
        # Add a favorite without seeding the matching opportunity row
        client.post("/api/favorites/ghost-opp-999")

        resp = client.get("/api/favorites")

        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["data"]]
        assert "ghost-opp-999" not in ids

    def test_add_duplicate_favorite_does_not_crash(self, client, db_session):
        """
        POST /api/favorites/{id} twice for the same session must not raise a 500.

        The UniqueConstraint on (session_id, opportunity_id) should be handled
        gracefully rather than bubbling up as an unhandled IntegrityError.
        """
        _seed_opportunity(db_session, "dup-test-opp-001")
        client.post("/api/favorites/dup-test-opp-001")

        resp = client.post("/api/favorites/dup-test-opp-001")

        assert resp.status_code < 500, (
            f"Duplicate add raised a server error: {resp.status_code} {resp.text}"
        )

    def test_remove_nonexistent_favorite_does_not_crash(self, client):
        """
        DELETE /api/favorites/{id} for an ID that was never added must not raise 500.
        """
        resp = client.delete("/api/favorites/never-added-opp")

        assert resp.status_code < 500, (
            f"Remove of nonexistent favorite raised a server error: {resp.status_code} {resp.text}"
        )
