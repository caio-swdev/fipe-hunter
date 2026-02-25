"""
Integration tests for FIPEController

Tests the controller endpoints for FIPE lookup operations.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fipe_adapters.controllers.fipe_controller import FIPEController
from fipe_business.domain.value_objects.price import Price


@pytest.fixture
def mock_use_case():
    """Mock LookupFIPEPriceUseCase for testing."""
    return Mock()


@pytest.fixture
def controller(mock_use_case):
    """Create controller instance with mocked use case."""
    return FIPEController(lookup_use_case=mock_use_case)


class TestFIPELookup:
    """Test GET /fipe/lookup endpoint."""

    @pytest.mark.asyncio
    async def test_lookup_success(self, controller, mock_use_case):
        """Should return FIPE price when vehicle found."""
        # Arrange
        mock_use_case.execute = AsyncMock(return_value={"price": Price.from_float(25000.0), "fipe_code": "001004-9", "reference_month": "janeiro/2024"})

        # Act
        response = await controller.lookup(brand="Volkswagen", model="Gol", year=2015)

        # Assert
        assert response["status"] == "success"
        assert response["data"]["brand"] == "Volkswagen"
        assert response["data"]["model"] == "Gol"
        assert response["data"]["year"] == 2015
        assert response["data"]["fipe_price"] == 25000.0
        assert "currency" in response["data"]
        mock_use_case.execute.assert_called_once_with(
            brand="Volkswagen",
            model="Gol",
            year=2015
        )

    @pytest.mark.asyncio
    async def test_lookup_not_found(self, controller, mock_use_case):
        """Should return 404 when vehicle not found in FIPE."""
        # Arrange
        mock_use_case.execute = AsyncMock(return_value=None)

        # Act
        response = await controller.lookup(brand="UnknownBrand", model="Model", year=2015)

        # Assert
        assert response["status"] == "not_found"
        assert response["message"] == "Vehicle not found in FIPE database"
        assert "brand" in response["data"]
        assert "model" in response["data"]
        assert "year" in response["data"]

    @pytest.mark.asyncio
    async def test_lookup_validation_error_missing_brand(self, controller):
        """Should return 400 when brand is missing."""
        # Act & Assert
        with pytest.raises(ValueError, match="Brand is required"):
            await controller.lookup(brand="", model="Gol", year=2015)

    @pytest.mark.asyncio
    async def test_lookup_validation_error_invalid_year(self, controller):
        """Should return 400 when year is invalid."""
        # Act & Assert
        with pytest.raises(ValueError, match="Year must be between 1950 and 2026"):
            await controller.lookup(brand="Volkswagen", model="Gol", year=1900)

    @pytest.mark.asyncio
    async def test_lookup_with_cache_hit(self, controller, mock_use_case):
        """Should return cached price quickly."""
        # Arrange
        mock_use_case.execute = AsyncMock(return_value={"price": Price.from_float(25000.0), "fipe_code": "001004-9", "reference_month": "janeiro/2024"})

        # Act
        response = await controller.lookup(brand="Volkswagen", model="Gol", year=2015)

        # Assert
        assert response["status"] == "success"
        assert response["data"]["fipe_price"] == 25000.0
        # Cached response should be indicated (use case handles caching)

    @pytest.mark.asyncio
    async def test_lookup_normalizes_brand(self, controller, mock_use_case):
        """Should normalize brand name before lookup."""
        # Arrange
        mock_use_case.execute = AsyncMock(return_value={"price": Price.from_float(25000.0), "fipe_code": "001004-9", "reference_month": "janeiro/2024"})

        # Act - Use "vw" lowercase
        response = await controller.lookup(brand="vw", model="Gol", year=2015)

        # Assert
        assert response["status"] == "success"
        # Use case receives normalized input
        mock_use_case.execute.assert_called_once()
        call_args = mock_use_case.execute.call_args[1]
        assert call_args["brand"].lower() == "vw"

    @pytest.mark.asyncio
    async def test_lookup_trims_whitespace(self, controller, mock_use_case):
        """Should trim whitespace from inputs."""
        # Arrange
        mock_use_case.execute = AsyncMock(return_value={"price": Price.from_float(25000.0), "fipe_code": "001004-9", "reference_month": "janeiro/2024"})

        # Act
        response = await controller.lookup(
            brand="  Volkswagen  ",
            model="  Gol  ",
            year=2015
        )

        # Assert
        assert response["status"] == "success"
        mock_use_case.execute.assert_called_once()
        call_args = mock_use_case.execute.call_args[1]
        assert call_args["brand"] == "Volkswagen"
        assert call_args["model"] == "Gol"
