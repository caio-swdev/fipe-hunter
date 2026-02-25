"""
Integration tests for Listing API Routes

Tests FastAPI endpoints with TestClient.
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from fipe_infra.database.models import Base
from fipe_infra.database.session import get_db_session


# Test database file
TEST_DB_PATH = "test_fipe_hunter.db"
TEST_DATABASE_URL = f"sqlite:///./{TEST_DB_PATH}"

# Create engine and sessionmaker
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override dependency
app.dependency_overrides[get_db_session] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Create test database tables once per module."""
    # Remove existing test database
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # Create tables
    Base.metadata.create_all(bind=test_engine)
    yield

    # Cleanup after all tests
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(autouse=True)
def cleanup_data():
    """Clean up data between tests."""
    yield
    # Clean tables after each test
    session = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_listing_data():
    """Sample listing data for tests."""
    return {
        "brand": "Volkswagen",
        "model": "Gol",
        "year": 2020,
        "price": 45000.00,
        "mileage": 35000,
        "condition": "good",
        "url": "https://example.com/listing/123",
        "marketplace": "olx",
    }


class TestCreateListingEndpoint:
    """Test POST /api/listings endpoint."""

    def test_create_listing_success(self, client, sample_listing_data):
        """Should create listing and return 201."""
        response = client.post("/api/listings", json=sample_listing_data)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"
        assert data["data"]["brand"] == "Volkswagen"
        assert data["data"]["model"] == "Gol"
        assert "scraped_at" in data["data"]

    def test_create_listing_validation_error(self, client):
        """Should return 422 for invalid data (Pydantic validation)."""
        invalid_data = {
            "brand": "V",  # Too short
            "model": "Gol",
            "year": 2020,
            "price": 45000.00,
            "condition": "good",
            "url": "https://example.com/listing/123",
            "marketplace": "olx",
        }

        response = client.post("/api/listings", json=invalid_data)
        assert response.status_code == 422

    def test_create_listing_duplicate_url(self, client, sample_listing_data):
        """Should return 409 for duplicate URL."""
        # Create first listing
        client.post("/api/listings", json=sample_listing_data)

        # Try to create duplicate
        response = client.post("/api/listings", json=sample_listing_data)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


class TestListListingsEndpoint:
    """Test GET /api/listings endpoint."""

    def test_list_listings_empty(self, client):
        """Should return empty list when no listings."""
        response = client.get("/api/listings")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 0
        assert data["pagination"]["total"] == 0

    def test_list_listings_with_data(self, client, sample_listing_data):
        """Should return listings with pagination."""
        # Create a listing first
        client.post("/api/listings", json=sample_listing_data)

        response = client.get("/api/listings?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1
        assert data["pagination"]["total"] == 1
        assert data["pagination"]["limit"] == 10

    def test_list_listings_pagination(self, client, sample_listing_data):
        """Should respect pagination parameters."""
        # Create multiple listings
        for i in range(5):
            listing = sample_listing_data.copy()
            listing["url"] = f"https://example.com/listing/{i}"
            client.post("/api/listings", json=listing)

        # Test limit
        response = client.get("/api/listings?limit=2&offset=0")
        data = response.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 5

        # Test offset
        response = client.get("/api/listings?limit=2&offset=2")
        data = response.json()
        assert len(data["data"]) == 2


class TestGetListingByUrlEndpoint:
    """Test GET /api/listings/by-url endpoint."""

    def test_get_listing_found(self, client, sample_listing_data):
        """Should return listing when found."""
        # Create listing first
        client.post("/api/listings", json=sample_listing_data)

        url = sample_listing_data["url"]
        response = client.get(f"/api/listings/by-url?url={url}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["url"] == url

    def test_get_listing_not_found(self, client):
        """Should return 404 when listing not found."""
        response = client.get("/api/listings/by-url?url=https://nonexistent.com")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateListingEndpoint:
    """Test PUT /api/listings/by-url endpoint."""

    def test_update_listing_success(self, client, sample_listing_data):
        """Should update listing and return 200."""
        # Create listing first
        client.post("/api/listings", json=sample_listing_data)

        url = sample_listing_data["url"]
        update_data = {"price": 50000.00, "mileage": 40000}

        response = client.put(
            f"/api/listings/by-url?url={url}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["data"]["price"] == 50000.00
        assert data["data"]["mileage"] == 40000

    def test_update_listing_not_found(self, client):
        """Should return 404 when listing not found."""
        update_data = {"price": 50000.00}

        response = client.put(
            "/api/listings/by-url?url=https://nonexistent.com",
            json=update_data,
        )

        assert response.status_code == 404

    def test_update_listing_validation_error(self, client, sample_listing_data):
        """Should return 422 for invalid update data (Pydantic validation)."""
        # Create listing first
        client.post("/api/listings", json=sample_listing_data)

        url = sample_listing_data["url"]
        invalid_data = {"price": -1000}  # Negative price

        response = client.put(
            f"/api/listings/by-url?url={url}", json=invalid_data
        )

        assert response.status_code == 422


class TestDeleteListingEndpoint:
    """Test DELETE /api/listings/by-url endpoint."""

    def test_delete_listing_success(self, client, sample_listing_data):
        """Should delete listing and return 200."""
        # Create listing first
        client.post("/api/listings", json=sample_listing_data)

        url = sample_listing_data["url"]
        response = client.delete(f"/api/listings/by-url?url={url}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"

        # Verify deletion
        get_response = client.get(f"/api/listings/by-url?url={url}")
        assert get_response.status_code == 404

    def test_delete_listing_not_found(self, client):
        """Should return 404 when listing not found."""
        response = client.delete(
            "/api/listings/by-url?url=https://nonexistent.com"
        )

        assert response.status_code == 404


class TestMarketplaceStatsEndpoint:
    """Test GET /api/listings/stats/marketplace endpoint."""

    def test_get_stats_empty(self, client):
        """Should return zero stats when no listings."""
        response = client.get("/api/listings/stats/marketplace")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["olx"] == 0
        assert data["data"]["webmotors"] == 0
        assert data["data"]["total"] == 0

    def test_get_stats_with_data(self, client, sample_listing_data):
        """Should return correct marketplace statistics."""
        # Create OLX listing
        olx_listing = sample_listing_data.copy()
        olx_listing["marketplace"] = "olx"
        client.post("/api/listings", json=olx_listing)

        # Create WebMotors listing
        webmotors_listing = sample_listing_data.copy()
        webmotors_listing["url"] = "https://example.com/listing/456"
        webmotors_listing["marketplace"] = "webmotors"
        client.post("/api/listings", json=webmotors_listing)

        response = client.get("/api/listings/stats/marketplace")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["olx"] == 1
        assert data["data"]["webmotors"] == 1
        assert data["data"]["total"] == 2
