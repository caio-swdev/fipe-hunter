"""
Integration tests for ListingController

Tests the FastAPI controller endpoints for listing CRUD operations.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from fipe_adapters.controllers.listing_controller import ListingController
from fipe_business.domain.entities.listing import Listing
from fipe_infra.repos.listing_repository import SQLAlchemyListingRepository


@pytest.fixture
def mock_repository():
    """Mock listing repository for testing."""
    return Mock(spec=SQLAlchemyListingRepository)


@pytest.fixture
def controller(mock_repository):
    """Create controller instance with mocked repository."""
    return ListingController(repository=mock_repository)


@pytest.fixture
def sample_listing():
    """Sample listing entity for testing."""
    return Listing(
        brand="Volkswagen",
        model="Gol",
        year=2020,
        price=45000.00,
        mileage=35000,
        condition="good",
        url="https://example.com/listing/123",
        marketplace="olx",
        scraped_at=datetime(2026, 2, 5, 14, 30, 0)
    )


class TestCreateListing:
    """Test POST /listings endpoint."""

    def test_create_listing_success(self, controller, mock_repository):
        """Should create a new listing and return 201."""
        # Arrange
        request_data = {
            "brand": "Volkswagen",
            "model": "Gol",
            "year": 2020,
            "price": 45000.00,
            "mileage": 35000,
            "condition": "good",
            "url": "https://example.com/listing/123",
            "marketplace": "olx"
        }
        mock_repository.save.return_value = None

        # Act
        response = controller.create(request_data)

        # Assert
        assert response["status"] == "created"
        assert response["data"]["brand"] == "Volkswagen"
        assert response["data"]["model"] == "Gol"
        assert response["data"]["year"] == 2020
        assert response["data"]["price"] == 45000.00
        assert "scraped_at" in response["data"]
        mock_repository.save.assert_called_once()

    def test_create_listing_validation_error(self, controller):
        """Should return 400 for invalid data."""
        # Arrange
        invalid_data = {
            "brand": "V",  # Too short
            "model": "Gol",
            "year": 2020,
            "price": -1000,  # Negative price
            "condition": "good",
            "url": "https://example.com/listing/123",
            "marketplace": "olx"
        }

        # Act & Assert
        with pytest.raises(ValueError):
            controller.create(invalid_data)

    def test_create_listing_duplicate_url(self, controller, mock_repository):
        """Should return 409 for duplicate URL."""
        # Arrange
        request_data = {
            "brand": "Volkswagen",
            "model": "Gol",
            "year": 2020,
            "price": 45000.00,
            "mileage": 35000,
            "condition": "good",
            "url": "https://example.com/listing/123",
            "marketplace": "olx"
        }
        from sqlalchemy.exc import IntegrityError
        mock_repository.save.side_effect = IntegrityError(
            "unique constraint", None, None
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            controller.create(request_data)


class TestGetListing:
    """Test GET /listings/{url} endpoint."""

    def test_get_listing_found(self, controller, mock_repository, sample_listing):
        """Should return listing when found."""
        # Arrange
        url = "https://example.com/listing/123"
        mock_repository.find_by_url.return_value = sample_listing

        # Act
        response = controller.get_by_url(url)

        # Assert
        assert response["status"] == "success"
        assert response["data"]["brand"] == "Volkswagen"
        assert response["data"]["model"] == "Gol"
        assert response["data"]["url"] == url
        mock_repository.find_by_url.assert_called_once_with(url)

    def test_get_listing_not_found(self, controller, mock_repository):
        """Should return 404 when listing not found."""
        # Arrange
        url = "https://example.com/listing/nonexistent"
        mock_repository.find_by_url.return_value = None

        # Act
        response = controller.get_by_url(url)

        # Assert
        assert response["status"] == "not_found"
        assert response["message"] == "Listing not found"


class TestListListings:
    """Test GET /listings endpoint."""

    def test_list_listings_success(self, controller, mock_repository, sample_listing):
        """Should return paginated list of listings."""
        # Arrange
        mock_repository.list_all.return_value = [sample_listing]
        mock_repository.count_all.return_value = 1

        # Act
        response = controller.list(limit=10, offset=0)

        # Assert
        assert response["status"] == "success"
        assert len(response["data"]) == 1
        assert response["data"][0]["brand"] == "Volkswagen"
        assert response["pagination"]["total"] == 1
        assert response["pagination"]["limit"] == 10
        assert response["pagination"]["offset"] == 0

    def test_list_listings_empty(self, controller, mock_repository):
        """Should return empty list when no listings."""
        # Arrange
        mock_repository.list_all.return_value = []
        mock_repository.count_all.return_value = 0

        # Act
        response = controller.list(limit=10, offset=0)

        # Assert
        assert response["status"] == "success"
        assert len(response["data"]) == 0
        assert response["pagination"]["total"] == 0


class TestDeleteListing:
    """Test DELETE /listings/{url} endpoint."""

    def test_delete_listing_success(self, controller, mock_repository, sample_listing):
        """Should delete listing and return 200."""
        # Arrange
        url = "https://example.com/listing/123"
        mock_repository.find_by_url.return_value = sample_listing
        mock_repository.delete_by_url.return_value = True

        # Act
        response = controller.delete_by_url(url)

        # Assert
        assert response["status"] == "deleted"
        assert response["message"] == "Listing deleted successfully"
        mock_repository.delete_by_url.assert_called_once_with(url)

    def test_delete_listing_not_found(self, controller, mock_repository):
        """Should return 404 when listing not found."""
        # Arrange
        url = "https://example.com/listing/nonexistent"
        mock_repository.find_by_url.return_value = None

        # Act
        response = controller.delete_by_url(url)

        # Assert
        assert response["status"] == "not_found"
        assert response["message"] == "Listing not found"


class TestUpdateListing:
    """Test PUT /listings/{url} endpoint."""

    def test_update_listing_success(self, controller, mock_repository, sample_listing):
        """Should update listing and return 200."""
        # Arrange
        url = "https://example.com/listing/123"
        update_data = {"price": 50000.00, "mileage": 40000}
        mock_repository.find_by_url.return_value = sample_listing
        mock_repository.update.return_value = None

        # Act
        response = controller.update(url, update_data)

        # Assert
        assert response["status"] == "updated"
        assert response["data"]["price"] == 50000.00
        assert response["data"]["mileage"] == 40000
        mock_repository.update.assert_called_once()

    def test_update_listing_not_found(self, controller, mock_repository):
        """Should return 404 when listing not found."""
        # Arrange
        url = "https://example.com/listing/nonexistent"
        update_data = {"price": 50000.00}
        mock_repository.find_by_url.return_value = None

        # Act
        response = controller.update(url, update_data)

        # Assert
        assert response["status"] == "not_found"
        assert response["message"] == "Listing not found"

    def test_update_listing_validation_error(self, controller, mock_repository, sample_listing):
        """Should return 400 for invalid update data."""
        # Arrange
        url = "https://example.com/listing/123"
        invalid_data = {"price": -1000}  # Negative price
        mock_repository.find_by_url.return_value = sample_listing

        # Act & Assert
        with pytest.raises(ValueError):
            controller.update(url, invalid_data)


class TestGetStatsByMarketplace:
    """Test GET /listings/stats/marketplace endpoint."""

    def test_get_stats_success(self, controller, mock_repository):
        """Should return marketplace statistics."""
        # Arrange
        mock_repository.count_by_marketplace.side_effect = lambda mp: {
            "olx": 150,
            "webmotors": 200
        }.get(mp, 0)

        # Act
        response = controller.get_stats_by_marketplace()

        # Assert
        assert response["status"] == "success"
        assert response["data"]["olx"] == 150
        assert response["data"]["webmotors"] == 200
        assert response["data"]["total"] == 350
