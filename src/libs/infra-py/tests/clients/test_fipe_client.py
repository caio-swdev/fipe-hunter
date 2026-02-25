"""
Integration Test: FIPE API Client

Tests the HTTP client implementation of IFIPEClient.
"""
import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock
from fipe_infra.clients.fipe_client import FIPEClient, _catalog_cache
from fipe_business.domain.value_objects.price import Price


@pytest.fixture(autouse=True)
def clear_catalog_cache():
    """Clear module-level catalog cache before each test to avoid cross-test contamination."""
    _catalog_cache.clear()
    yield
    _catalog_cache.clear()


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for testing."""
    return Mock(spec=httpx.AsyncClient)


@pytest.fixture
def fipe_client(mock_httpx_client):
    """Create FIPEClient instance with mocked HTTP client."""
    with patch('fipe_infra.clients.fipe_client.httpx.AsyncClient', return_value=mock_httpx_client):
        return FIPEClient(base_url="https://parallelum.com.br/fipe/api/v1", timeout=10.0)


class TestFIPEClientLookupPrice:
    """Test FIPE API price lookup functionality."""

    @pytest.mark.asyncio
    async def test_lookup_price_success(self, mock_httpx_client):
        """Should return price and version when vehicle found."""
        # Arrange
        fipe_client = FIPEClient(base_url="https://parallelum.com.br/fipe/api/v1", timeout=10.0)

        # Mock API responses
        mock_brands_response = Mock()
        mock_brands_response.json.return_value = [
            {"codigo": "59", "nome": "VOLKSWAGEN"}
        ]
        mock_brands_response.raise_for_status = Mock()

        mock_models_response = Mock()
        mock_models_response.json.return_value = {
            "modelos": [
                {"codigo": 2222, "nome": "Gol 1.0"}
            ]
        }
        mock_models_response.raise_for_status = Mock()

        mock_years_response = Mock()
        mock_years_response.json.return_value = [
            {"codigo": "2015-1", "nome": "2015 Gasolina"}
        ]
        mock_years_response.raise_for_status = Mock()

        mock_price_response = Mock()
        mock_price_response.json.return_value = {
            "Valor": "R$ 25.000,00",
            "Marca": "Volkswagen",
            "Modelo": "Gol 1.0",
            "AnoModelo": 2015,
            "Combustivel": "Gasolina",
            "MesReferencia": "janeiro de 2024"
        }
        mock_price_response.raise_for_status = Mock()

        with patch.object(fipe_client, '_client') as mock_client:
            mock_client.get = AsyncMock(side_effect=[
                mock_brands_response,
                mock_models_response,
                mock_years_response,
                mock_price_response
            ])

            # Act
            result = await fipe_client.lookup_price("Volkswagen", "Gol", 2015)

        # Assert
        assert result is not None
        price = result["price"]
        version = result["model_version"]
        assert isinstance(price, Price)
        assert price.to_float() == 25000.0
        assert version == "Gol 1.0"

    @pytest.mark.asyncio
    async def test_lookup_price_brand_not_found(self, mock_httpx_client):
        """Should return None when brand not found in FIPE."""
        # Arrange
        fipe_client = FIPEClient(base_url="https://parallelum.com.br/fipe/api/v1", timeout=10.0)

        mock_brands_response = Mock()
        mock_brands_response.json.return_value = [
            {"codigo": "59", "nome": "VOLKSWAGEN"}
        ]
        mock_brands_response.raise_for_status = Mock()

        with patch.object(fipe_client, '_client') as mock_client:
            mock_client.get = AsyncMock(return_value=mock_brands_response)

            # Act
            result = await fipe_client.lookup_price("UnknownBrand", "Model", 2015)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_price_fuzzy_brand_matching(self, mock_httpx_client):
        """Should match brand names with fuzzy logic (VW -> Volkswagen)."""
        # Arrange
        fipe_client = FIPEClient(base_url="https://parallelum.com.br/fipe/api/v1", timeout=10.0)

        mock_brands_response = Mock()
        mock_brands_response.json.return_value = [
            {"codigo": "59", "nome": "VOLKSWAGEN"}
        ]
        mock_brands_response.raise_for_status = Mock()

        mock_models_response = Mock()
        mock_models_response.json.return_value = {
            "modelos": [
                {"codigo": 2222, "nome": "Gol 1.0"}
            ]
        }
        mock_models_response.raise_for_status = Mock()

        mock_years_response = Mock()
        mock_years_response.json.return_value = [
            {"codigo": "2015-1", "nome": "2015 Gasolina"}
        ]
        mock_years_response.raise_for_status = Mock()

        mock_price_response = Mock()
        mock_price_response.json.return_value = {
            "Valor": "R$ 25.000,00",
            "Marca": "Volkswagen",
            "Modelo": "Gol 1.0",
            "AnoModelo": 2015,
            "Combustivel": "Gasolina",
            "MesReferencia": "janeiro de 2024"
        }
        mock_price_response.raise_for_status = Mock()

        with patch.object(fipe_client, '_client') as mock_client:
            mock_client.get = AsyncMock(side_effect=[
                mock_brands_response,
                mock_models_response,
                mock_years_response,
                mock_price_response
            ])

            # Act - Use "VW" abbreviation
            result = await fipe_client.lookup_price("VW", "Gol", 2015)

        # Assert
        assert result is not None
        price = result["price"]
        version = result["model_version"]
        assert price.to_float() == 25000.0

    @pytest.mark.asyncio
    async def test_lookup_price_timeout(self, mock_httpx_client):
        """Should handle timeout and retry once."""
        # Arrange
        fipe_client = FIPEClient(base_url="https://parallelum.com.br/fipe/api/v1", timeout=10.0)

        with patch.object(fipe_client, '_client') as mock_client:
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))

            # Act
            result = await fipe_client.lookup_price("Volkswagen", "Gol", 2015)

        # Assert
        assert result is None
        # Should retry at least once
        assert mock_client.get.call_count >= 2


class TestFIPEClientGetTableDate:
    """Test FIPE table date retrieval."""

    @pytest.mark.asyncio
    async def test_get_table_date_success(self, mock_httpx_client):
        """Should return current FIPE table reference date."""
        # Arrange
        fipe_client = FIPEClient(base_url="https://parallelum.com.br/fipe/api/v1", timeout=10.0)

        mock_response = Mock()
        mock_response.json.return_value = [
            {"Codigo": 290, "Mes": "janeiro/2024"}
        ]
        mock_response.raise_for_status = Mock()

        with patch.object(fipe_client, '_client') as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            # Act
            result = await fipe_client.get_table_date()

        # Assert
        assert result == "janeiro/2024"

    @pytest.mark.asyncio
    async def test_get_table_date_fallback(self, mock_httpx_client):
        """Should return fallback date on error."""
        # Arrange
        fipe_client = FIPEClient(base_url="https://parallelum.com.br/fipe/api/v1", timeout=10.0)

        with patch.object(fipe_client, '_client') as mock_client:
            mock_client.get = AsyncMock(side_effect=httpx.RequestError("Network error"))

            # Act
            result = await fipe_client.get_table_date()

        # Assert
        assert "202" in result  # Should contain year


class TestBrandNormalization:
    """Test brand name normalization."""

    @pytest.mark.asyncio
    async def test_normalize_common_abbreviations(self):
        """Should normalize common brand abbreviations."""
        fipe_client = FIPEClient(base_url="https://parallelum.com.br/fipe/api/v1", timeout=10.0)

        # Test abbreviation mapping
        assert fipe_client._normalize_brand("VW") == "volkswagen"
        assert fipe_client._normalize_brand("GM") == "chevrolet"
        assert fipe_client._normalize_brand("Fiat") == "fiat"
        assert fipe_client._normalize_brand("FORD") == "ford"
