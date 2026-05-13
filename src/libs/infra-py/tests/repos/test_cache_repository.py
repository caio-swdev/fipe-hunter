"""
Integration Test: Cache Repository

Tests the SQLAlchemy implementation of ICacheRepository.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fipe_business.domain.entities.price_cache import PriceCache
from fipe_business.domain.value_objects.price import Price
from fipe_infra.database.models import Base, PriceCacheModel
from fipe_infra.repos.cache_repository import SQLAlchemyCacheRepository


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
def repository(db_session: Session) -> SQLAlchemyCacheRepository:
    """Create repository instance."""
    return SQLAlchemyCacheRepository(db_session)


@pytest.fixture
def sample_cache_entry() -> PriceCache:
    """Create sample cache entry for testing."""
    return PriceCache(
        cache_key="volkswagen-gol-2020",
        brand="Volkswagen",
        model="Gol",
        year=2020,
        price=Price.from_float(35000.0),
        version="Gol 1.0 (Flex)",
        fipe_table_date="janeiro/2024",
        cached_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )


def test_save_cache_entry(repository: SQLAlchemyCacheRepository, sample_cache_entry: PriceCache):
    """Test saving a cache entry to database."""

    repository.save(sample_cache_entry)


    result = repository.find_by_key(sample_cache_entry.cache_key)
    assert result is not None
    assert result.cache_key == sample_cache_entry.cache_key
    assert result.price.amount == sample_cache_entry.price.amount


def test_find_by_key_returns_none_when_not_found(repository: SQLAlchemyCacheRepository):
    """Test finding a non-existent cache entry returns None."""

    result = repository.find_by_key("nonexistent-key")


    assert result is None


def test_find_by_key_returns_cache_entry(repository: SQLAlchemyCacheRepository, sample_cache_entry: PriceCache):
    """Test finding existing cache entry by key."""

    repository.save(sample_cache_entry)


    result = repository.find_by_key(sample_cache_entry.cache_key)


    assert result is not None
    assert result.cache_key == sample_cache_entry.cache_key
    assert result.version == sample_cache_entry.version


def test_delete_cache_entry(repository: SQLAlchemyCacheRepository, sample_cache_entry: PriceCache):
    """Test deleting a cache entry."""

    repository.save(sample_cache_entry)


    repository.delete(sample_cache_entry.cache_key)


    result = repository.find_by_key(sample_cache_entry.cache_key)
    assert result is None


def test_clear_expired_removes_expired_entries(repository: SQLAlchemyCacheRepository):
    """Test clearing expired cache entries."""

    expired_entry = PriceCache(
        cache_key="fiat-uno-2019",
        brand="Fiat",
        model="Uno",
        year=2019,
        price=Price.from_float(30000.0),
        version="Uno 1.0",
        fipe_table_date="dezembro/2023",
        cached_at=datetime.utcnow() - timedelta(days=10),
        expires_at=datetime.utcnow() - timedelta(days=1)
    )

    valid_entry = PriceCache(
        cache_key="chevrolet-onix-2021",
        brand="Chevrolet",
        model="Onix",
        year=2021,
        price=Price.from_float(35000.0),
        version="Onix 1.0",
        fipe_table_date="janeiro/2024",
        cached_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )

    repository.save(expired_entry)
    repository.save(valid_entry)


    deleted_count = repository.clear_expired()


    assert deleted_count == 1
    assert repository.find_by_key("fiat-uno-2019") is None
    assert repository.find_by_key("chevrolet-onix-2021") is not None


def test_save_duplicate_key_updates_existing(repository: SQLAlchemyCacheRepository, sample_cache_entry: PriceCache):
    """Test that saving duplicate key updates existing entry."""

    repository.save(sample_cache_entry)

    updated_entry = PriceCache(
        cache_key=sample_cache_entry.cache_key,
        brand="Volkswagen",
        model="Gol",
        year=2020,
        price=Price.from_float(40000.0),
        version="Gol 1.6 (Flex)",
        fipe_table_date="fevereiro/2024",
        cached_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )


    repository.save(updated_entry)


    result = repository.find_by_key(sample_cache_entry.cache_key)
    assert result is not None
    assert result.price.to_float() == 40000.0
    assert result.version == "Gol 1.6 (Flex)"
