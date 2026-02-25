"""
Integration Test: Listing Repository

Tests the SQLAlchemy implementation of IListingRepository.
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fipe_business.domain.entities.listing import Listing
from fipe_infra.database.models import Base, ListingModel
from fipe_infra.repos.listing_repository import SQLAlchemyListingRepository


@pytest.fixture
def db_session() -> Session:
    """Create in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def repository(db_session: Session) -> SQLAlchemyListingRepository:
    """Create repository instance."""
    return SQLAlchemyListingRepository(db_session)


@pytest.fixture
def sample_listing() -> Listing:
    """Create sample listing for testing."""
    return Listing(
        brand="Volkswagen",
        model="Gol",
        year=2020,
        price=30000.0,
        mileage=50000,
        condition="good",
        url="https://olx.com.br/listing/12345",
        marketplace="olx",
        scraped_at=datetime(2024, 1, 1, 12, 0, 0)
    )


def test_save_listing(repository: SQLAlchemyListingRepository, sample_listing: Listing):
    """Test saving a listing to database."""
    # Act
    repository.save(sample_listing)

    # Assert
    result = repository.find_by_url(sample_listing.url)
    assert result is not None
    assert result.brand == sample_listing.brand
    assert result.model == sample_listing.model
    assert result.year == sample_listing.year
    assert result.price == sample_listing.price


def test_find_by_url_returns_none_when_not_found(repository: SQLAlchemyListingRepository):
    """Test finding a non-existent listing returns None."""
    # Act
    result = repository.find_by_url("https://nonexistent.com")

    # Assert
    assert result is None


def test_find_by_url_returns_listing(repository: SQLAlchemyListingRepository, sample_listing: Listing):
    """Test finding existing listing by URL."""
    # Arrange
    repository.save(sample_listing)

    # Act
    result = repository.find_by_url(sample_listing.url)

    # Assert
    assert result is not None
    assert result.brand == sample_listing.brand
    assert result.url == sample_listing.url


def test_count_by_marketplace(repository: SQLAlchemyListingRepository, sample_listing: Listing):
    """Test counting listings by marketplace."""
    # Arrange
    repository.save(sample_listing)

    webmotors_listing = Listing(
        brand="Fiat",
        model="Uno",
        year=2019,
        price=25000.0,
        mileage=60000,
        condition="fair",
        url="https://webmotors.com.br/listing/67890",
        marketplace="webmotors",
        scraped_at=datetime(2024, 1, 2, 12, 0, 0)
    )
    repository.save(webmotors_listing)

    # Act
    olx_count = repository.count_by_marketplace("olx")
    webmotors_count = repository.count_by_marketplace("webmotors")

    # Assert
    assert olx_count == 1
    assert webmotors_count == 1


def test_save_duplicate_url_raises_integrity_error(
    repository: SQLAlchemyListingRepository,
    sample_listing: Listing
):
    """Test that saving duplicate URL raises error."""
    # Arrange
    repository.save(sample_listing)

    duplicate = Listing(
        brand="Chevrolet",
        model="Onix",
        year=2021,
        price=35000.0,
        mileage=30000,
        condition="excellent",
        url=sample_listing.url,  # Same URL
        marketplace="olx",
        scraped_at=datetime(2024, 1, 3, 12, 0, 0)
    )

    # Act & Assert
    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
        repository.save(duplicate)
