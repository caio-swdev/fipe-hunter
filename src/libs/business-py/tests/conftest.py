"""
Pytest configuration and shared fixtures.
"""
import pytest
from datetime import datetime
from fipe_business.domain.entities import Listing


@pytest.fixture
def sample_listing():
    """Fixture providing a sample listing entity for tests."""
    return Listing(
        brand="Volkswagen",
        model="Gol",
        year=2020,
        price=30000.0,
        mileage=50000,
        condition="good",
        url="https://olx.com.br/listing/123",
        marketplace="olx",
        scraped_at=datetime.utcnow()
    )
