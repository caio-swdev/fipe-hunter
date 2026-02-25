"""
Integration tests for FIPE FastAPI routes

Tests the FastAPI route adapters for FIPE lookup endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from fipe_business.domain.value_objects.price import Price


@pytest.fixture
def mock_fipe_client():
    """Mock FIPE client for testing."""
    mock = Mock()
    mock.lookup_price = AsyncMock(return_value={"price": Price.from_float(25000.0), "model_version": "Gol 1.0", "fipe_code": "001004-9", "reference_month": "janeiro/2024"})
    mock.get_table_date = AsyncMock(return_value="janeiro/2024")
    return mock


@pytest.fixture
def mock_cache_repository():
    """Mock cache repository for testing."""
    mock = Mock()
    mock.find_by_key = Mock(return_value=None)
    mock.save = Mock()
    return mock


@pytest.fixture
def test_client(mock_fipe_client, mock_cache_repository):
    """Create FastAPI test client with mocked dependencies."""
    # Import must happen inside fixture to allow mocking
    with patch('app.routes.fipe_routes.make_fipe_controller') as mock_factory:
        # Create controller with mocked dependencies
        from fipe_business.application.use_cases.lookup_fipe_price import LookupFIPEPriceUseCase
        from fipe_adapters.controllers.fipe_controller import FIPEController

        use_case = LookupFIPEPriceUseCase(mock_fipe_client, mock_cache_repository)
        controller = FIPEController(use_case)
        mock_factory.return_value = controller

        from app.main import app
        # Use yield instead of return to keep the patch active during the test
        yield TestClient(app)


class TestFIPELookupRoute:
    """Test GET /api/v1/fipe/lookup endpoint."""

    def test_lookup_success(self, test_client, mock_fipe_client):
        """Should return 200 with FIPE price when vehicle found."""
        # Arrange
        mock_fipe_client.lookup_price = AsyncMock(
            return_value={"price": Price.from_float(25000.0), "model_version": "Gol 1.0", "fipe_code": "001004-9", "reference_month": "janeiro/2024"}
        )

        # Act
        response = test_client.get(
            "/api/v1/fipe/lookup",
            params={"brand": "Volkswagen", "model": "Gol", "year": 2015}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["brand"] == "Volkswagen"
        assert data["data"]["model"] == "Gol"
        assert data["data"]["year"] == 2015
        assert data["data"]["fipe_price"] == 25000.0
        assert data["data"]["currency"] == "BRL"

    def test_lookup_not_found(self, test_client, mock_fipe_client):
        """Should return 404 when vehicle not found."""
        # Arrange
        mock_fipe_client.lookup_price = AsyncMock(return_value=None)

        # Act
        response = test_client.get(
            "/api/v1/fipe/lookup",
            params={"brand": "UnknownBrand", "model": "Model", "year": 2015}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_lookup_missing_brand(self, test_client):
        """Should return 422 when brand parameter is missing."""
        # Act
        response = test_client.get(
            "/api/v1/fipe/lookup",
            params={"model": "Gol", "year": 2015}
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "brand" in str(data["detail"]).lower()

    def test_lookup_missing_model(self, test_client):
        """Should return 422 when model parameter is missing."""
        # Act
        response = test_client.get(
            "/api/v1/fipe/lookup",
            params={"brand": "Volkswagen", "year": 2015}
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "model" in str(data["detail"]).lower()

    def test_lookup_invalid_year(self, test_client):
        """Should return 422 when year is invalid."""
        # Act
        response = test_client.get(
            "/api/v1/fipe/lookup",
            params={"brand": "Volkswagen", "model": "Gol", "year": 1900}
        )

        # Assert
        assert response.status_code == 422

    def test_lookup_cached_response(self, test_client, mock_cache_repository):
        """Should return cached price when cache hit."""
        # Arrange
        from fipe_business.domain.entities.price_cache import PriceCache
        from datetime import datetime, timedelta

        cached_entry = PriceCache(
            cache_key="volkswagen-gol-2015",
            brand="Volkswagen",
            model="Gol",
            year=2015,
            price=Price.from_float(25000.0),
            version="Gol 1.0",
            fipe_table_date="janeiro/2024",
            cached_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        mock_cache_repository.find_by_key = Mock(return_value=cached_entry)

        # Act
        response = test_client.get(
            "/api/v1/fipe/lookup",
            params={"brand": "Volkswagen", "model": "Gol", "year": 2015}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["fipe_price"] == 25000.0
        # Should use cached value (no API call)

    def test_lookup_with_whitespace(self, test_client, mock_fipe_client):
        """Should handle inputs with leading/trailing whitespace."""
        # Arrange
        mock_fipe_client.lookup_price = AsyncMock(
            return_value={"price": Price.from_float(25000.0), "model_version": "Gol 1.0", "fipe_code": "001004-9", "reference_month": "janeiro/2024"}
        )

        # Act
        response = test_client.get(
            "/api/v1/fipe/lookup",
            params={"brand": "  Volkswagen  ", "model": "  Gol  ", "year": 2015}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["brand"] == "Volkswagen"
        assert data["data"]["model"] == "Gol"
