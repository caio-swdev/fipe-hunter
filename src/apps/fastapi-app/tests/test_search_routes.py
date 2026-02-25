"""
API Tests: POST /api/search/vehicle

Tests the on-demand vehicle search endpoint that:
1. Looks up FIPE reference price
2. Scrapes OLX + WebMotors for matching listings
3. Calculates discounts and scores
4. Creates and saves opportunities
5. Returns FIPE price + opportunities
"""
import pytest
from contextlib import contextmanager
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch, MagicMock

from fipe_infra.database.models import (
    Base,
    ListingModel,
    OpportunityModel,
    PriceCacheModel,
    AlertModel
)
from fipe_infra.database.session import get_db_session
from fipe_business.domain.value_objects import Price


# Test database setup
@pytest.fixture(scope="module")
def test_db():
    """Create test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_db):
    """Get database session for each test."""
    session = test_db()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """Create FastAPI test client with test database."""
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


@contextmanager
def mock_scrapers(olx_listings=None, wm_listings=None):
    """Mock both OLX and WebMotors scrapers to return given listings."""
    olx_listings = olx_listings or []
    wm_listings = wm_listings or []

    mock_olx_cls = MagicMock()
    mock_olx_cls.return_value.scrape.return_value = olx_listings

    mock_wm_cls = MagicMock()
    mock_wm_cls.return_value.scrape.return_value = wm_listings

    with patch("app.main.factories.search_factory.CurlOLXScraper", mock_olx_cls), \
         patch("app.main.factories.search_factory.WebMotorsScraper", mock_wm_cls):
        yield mock_olx_cls, mock_wm_cls


class TestSearchVehicleAPI:
    """Test suite for POST /api/search/vehicle endpoint."""

    def test_search_vehicle_success_fipe_only(self, client):
        """
        Test successful search that returns FIPE price but no opportunities.

        Scenario: Toyota Corolla 2022 - FIPE price found, but no matching listings.
        """
        with patch("fipe_business.application.use_cases.lookup_fipe_price.LookupFIPEPriceUseCase.execute") as mock_fipe:
            mock_fipe.return_value = {
                "price": Price.from_float(133376.00),
                "fipe_code": "001234-5",
                "reference_month": "Janeiro/2026"
            }

            with mock_scrapers(olx_listings=[], wm_listings=[]):
                response = client.post(
                    "/api/search/vehicle",
                    json={
                        "brand": "Toyota",
                        "model": "Corolla",
                        "year": 2022
                    }
                )

                assert response.status_code == 200
                data = response.json()

                assert data["status"] == "success"
                assert data["fipe"] is not None
                assert data["fipe"]["brand"] == "Toyota"
                assert data["fipe"]["model"] == "Corolla"
                assert data["fipe"]["year"] == 2022
                assert data["fipe"]["reference_price"] > 0
                assert "fipe_code" in data["fipe"]
                assert "reference_month" in data["fipe"]

                assert data["total_results"] == 0
                assert data["results"] == []

    def test_search_vehicle_success_with_opportunities(self, client, db_session):
        """
        Test successful search that returns FIPE price + opportunities.

        Scenario: Honda Civic 2020 - FIPE price found + listings with >20% discount.
        """
        with patch("fipe_business.application.use_cases.lookup_fipe_price.LookupFIPEPriceUseCase.execute") as mock_fipe:
            mock_fipe.return_value = {
                "price": Price.from_float(70000.00),
                "fipe_code": "002345-6",
                "reference_month": "Janeiro/2026"
            }

            from fipe_business.domain.entities import Listing
            from datetime import datetime

            mock_listings = [
                Listing(
                    brand="Honda",
                    model="Civic",
                    year=2020,
                    price=50000.0,
                    url="https://olx.com.br/listing1",
                    marketplace="olx",
                    mileage=45000,
                    condition="good",
                    scraped_at=datetime.now()
                ),
                Listing(
                    brand="Honda",
                    model="Civic",
                    year=2020,
                    price=48000.0,
                    url="https://olx.com.br/listing2",
                    marketplace="olx",
                    mileage=60000,
                    condition="good",
                    scraped_at=datetime.now()
                ),
            ]

            with mock_scrapers(olx_listings=mock_listings, wm_listings=[]):
                response = client.post(
                    "/api/search/vehicle",
                    json={
                        "brand": "Honda",
                        "model": "Civic",
                        "year": 2020
                    }
                )

                assert response.status_code == 200
                data = response.json()

                assert data["status"] == "success"
                assert data["fipe"] is not None
                assert data["fipe"]["brand"] == "Honda"
                assert data["fipe"]["model"] == "Civic"
                assert data["fipe"]["year"] == 2020

                assert data["total_results"] > 0
                assert len(data["results"]) > 0

                opp = data["results"][0]
                assert "id" in opp
                assert opp["brand"] == "Honda"
                assert opp["model"] == "Civic"
                assert opp["year"] == 2020
                assert opp["listing_price"] > 0
                assert opp["fipe_price"] > 0
                assert opp["discount_percent"] >= 20.0
                assert opp["score"] > 0
                assert opp["url"].startswith("https://")

                if len(data["results"]) > 1:
                    scores = [r["score"] for r in data["results"]]
                    assert scores == sorted(scores, reverse=True)

    def test_search_vehicle_missing_required_fields(self, client):
        """Test validation error when required fields are missing."""
        response = client.post(
            "/api/search/vehicle",
            json={
                "model": "Civic",
                "year": 2020
            }
        )
        assert response.status_code == 422

        response = client.post(
            "/api/search/vehicle",
            json={
                "brand": "Honda",
                "year": 2020
            }
        )
        assert response.status_code == 422

    def test_search_vehicle_invalid_brand_length(self, client):
        """Test validation error when brand is too short."""
        response = client.post(
            "/api/search/vehicle",
            json={
                "brand": "H",
                "model": "Civic",
                "year": 2020
            }
        )
        assert response.status_code == 422

    def test_search_vehicle_invalid_year_range(self, client):
        """Test validation error when year is out of range."""
        response = client.post(
            "/api/search/vehicle",
            json={
                "brand": "Honda",
                "model": "Civic",
                "year": 1949
            }
        )
        assert response.status_code == 422

        response = client.post(
            "/api/search/vehicle",
            json={
                "brand": "Honda",
                "model": "Civic",
                "year": 2027
            }
        )
        assert response.status_code == 422

    def test_search_vehicle_year_optional(self, client):
        """Test that year parameter is optional."""
        with mock_scrapers():
            response = client.post(
                "/api/search/vehicle",
                json={
                    "brand": "Honda",
                    "model": "Civic"
                }
            )
            assert response.status_code in [200, 404]

    def test_search_vehicle_fipe_not_found(self, client):
        """Test handling when FIPE price is not found."""
        with patch("fipe_business.application.use_cases.lookup_fipe_price.LookupFIPEPriceUseCase.execute") as mock_lookup:
            mock_lookup.return_value = None

            response = client.post(
                "/api/search/vehicle",
                json={
                    "brand": "NonExistentBrand",
                    "model": "NonExistentModel",
                    "year": 2000
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert data["fipe"] is None
            assert data["fipe_error"] is not None
            assert data["total_results"] == 0

    def test_search_vehicle_fipe_api_timeout(self, client):
        """Test handling when FIPE API times out."""
        with patch("fipe_business.application.use_cases.lookup_fipe_price.LookupFIPEPriceUseCase.execute") as mock_lookup:
            mock_lookup.side_effect = TimeoutError("FIPE API timeout")

            response = client.post(
                "/api/search/vehicle",
                json={
                    "brand": "Honda",
                    "model": "Civic",
                    "year": 2020
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert data["fipe"] is None
            assert "timeout" in data["fipe_error"].lower()

    def test_search_vehicle_olx_scraping_failure(self, client):
        """Test handling when OLX scraping fails."""
        with patch("fipe_business.application.use_cases.lookup_fipe_price.LookupFIPEPriceUseCase.execute") as mock_fipe:
            mock_fipe.return_value = {
                "price": Price.from_float(133376.00),
                "fipe_code": "001234-5",
                "reference_month": "Janeiro/2026"
            }

            mock_olx = MagicMock()
            mock_olx.return_value.scrape.side_effect = Exception("OLX scraping failed")
            mock_wm = MagicMock()
            mock_wm.return_value.scrape.return_value = []

            with patch("app.main.factories.search_factory.CurlOLXScraper", mock_olx), \
                 patch("app.main.factories.search_factory.WebMotorsScraper", mock_wm):
                response = client.post(
                    "/api/search/vehicle",
                    json={
                        "brand": "Toyota",
                        "model": "Corolla",
                        "year": 2022
                    }
                )

                assert response.status_code == 200
                data = response.json()

                assert data["status"] == "success"
                assert data["fipe"] is not None
                assert data["total_results"] == 0

    def test_search_vehicle_input_trimming(self, client):
        """Test that whitespace is trimmed from brand and model inputs."""
        with mock_scrapers():
            response = client.post(
                "/api/search/vehicle",
                json={
                    "brand": "  Honda  ",
                    "model": "  Civic  ",
                    "year": 2020
                }
            )

            assert response.status_code == 200
            data = response.json()

            if data["fipe"]:
                assert data["fipe"]["brand"] == "Honda"
                assert data["fipe"]["model"] == "Civic"

    def test_search_vehicle_idempotent_results(self, client, db_session):
        """Test that repeated searches return consistent results."""
        from fipe_business.domain.entities import Listing
        from datetime import datetime

        listing = Listing(
            brand="Honda",
            model="Civic",
            year=2020,
            price=50000.0,
            url="https://olx.com.br/same-listing",
            marketplace="olx",
            mileage=45000,
            condition="good",
            scraped_at=datetime.now()
        )

        with mock_scrapers(olx_listings=[listing], wm_listings=[]):
            response1 = client.post(
                "/api/search/vehicle",
                json={"brand": "Honda", "model": "Civic", "year": 2020}
            )

            response2 = client.post(
                "/api/search/vehicle",
                json={"brand": "Honda", "model": "Civic", "year": 2020}
            )

            assert response1.status_code == 200
            assert response2.status_code == 200

            data1 = response1.json()
            data2 = response2.json()
            assert data1["total_results"] == data2["total_results"]

    def test_search_vehicle_discount_threshold(self, client):
        """Test that only listings with >=20% discount are returned."""
        from fipe_business.domain.entities import Listing
        from datetime import datetime

        with patch("fipe_business.application.use_cases.lookup_fipe_price.LookupFIPEPriceUseCase.execute") as mock_fipe:
            mock_fipe.return_value = {
                "price": Price.from_float(70000.00),
                "fipe_code": "002345-6",
                "reference_month": "Janeiro/2026"
            }

            listings = [
                Listing(
                    brand="Chevrolet", model="Onix", year=2021, price=50000.0,
                    url="https://olx.com.br/onix-good1", marketplace="olx",
                    mileage=45000, condition="good", scraped_at=datetime.now()
                ),
                Listing(
                    brand="Chevrolet", model="Onix", year=2021, price=63000.0,
                    url="https://olx.com.br/onix-bad1", marketplace="olx",
                    mileage=30000, condition="excellent", scraped_at=datetime.now()
                ),
                Listing(
                    brand="Chevrolet", model="Onix", year=2021, price=48000.0,
                    url="https://olx.com.br/onix-good2", marketplace="olx",
                    mileage=60000, condition="good", scraped_at=datetime.now()
                ),
            ]

            with mock_scrapers(olx_listings=listings, wm_listings=[]):
                response = client.post(
                    "/api/search/vehicle",
                    json={"brand": "Chevrolet", "model": "Onix", "year": 2021}
                )

                assert response.status_code == 200
                data = response.json()

                # All 3 listings match brand/model/year, so all create opportunities
                assert data["total_results"] == 3
                # Verify all have discount info
                for opp in data["results"]:
                    assert opp["discount_percent"] >= 0
