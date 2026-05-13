"""
Unit tests for Listing entity.
"""
import pytest
from datetime import datetime
from fipe_business.domain.entities import Listing


def test_listing_creation_with_valid_data():
    """Test creating a listing with valid data."""

    listing = Listing(
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


    assert listing.brand == "Volkswagen"
    assert listing.model == "Gol"
    assert listing.year == 2020
    assert listing.price == 30000.0


def test_listing_validation_rejects_invalid_brand():
    """Test that listing validation rejects invalid brand."""

    with pytest.raises(ValueError, match="Brand must be at least 2 characters"):
        Listing(
            brand="V",
            model="Gol",
            year=2020,
            price=30000.0,
            mileage=50000,
            condition="good",
            url="https://olx.com.br/listing/123",
            marketplace="olx",
            scraped_at=datetime.utcnow()
        )


def test_listing_validation_rejects_negative_price():
    """Test that listing validation rejects negative price."""

    with pytest.raises(ValueError, match="Price must be positive"):
        Listing(
            brand="Volkswagen",
            model="Gol",
            year=2020,
            price=-1000.0,
            mileage=50000,
            condition="good",
            url="https://olx.com.br/listing/123",
            marketplace="olx",
            scraped_at=datetime.utcnow()
        )


def test_listing_validation_rejects_invalid_year():
    """Test that listing validation rejects invalid year."""

    with pytest.raises(ValueError, match="Year must be between 1950 and 2026"):
        Listing(
            brand="Volkswagen",
            model="Gol",
            year=1900,
            price=30000.0,
            mileage=50000,
            condition="good",
            url="https://olx.com.br/listing/123",
            marketplace="olx",
            scraped_at=datetime.utcnow()
        )


def test_listing_validation_rejects_invalid_condition():
    """Test that listing validation rejects invalid condition."""

    with pytest.raises(ValueError, match="Invalid condition"):
        Listing(
            brand="Volkswagen",
            model="Gol",
            year=2020,
            price=30000.0,
            mileage=50000,
            condition="perfect",
            url="https://olx.com.br/listing/123",
            marketplace="olx",
            scraped_at=datetime.utcnow()
        )
