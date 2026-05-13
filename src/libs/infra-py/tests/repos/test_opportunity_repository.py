"""
Integration Test: Opportunity Repository

Tests the SQLAlchemy implementation of IOpportunityRepository.
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fipe_business.domain.entities.opportunity import Opportunity
from fipe_business.domain.value_objects.price import Price
from fipe_business.domain.value_objects.discount import Discount
from fipe_business.domain.value_objects.score import Score
from fipe_infra.database.models import Base, OpportunityModel
from fipe_infra.repos.opportunity_repository import SQLAlchemyOpportunityRepository


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
def repository(db_session: Session) -> SQLAlchemyOpportunityRepository:
    """Create repository instance."""
    return SQLAlchemyOpportunityRepository(db_session)


@pytest.fixture
def sample_opportunity() -> Opportunity:
    """Create sample opportunity for testing."""
    return Opportunity(
        listing_id="listing-123",
        brand="Volkswagen",
        model="Gol",
        year=2020,
        listing_price=Price.from_float(25000.0),
        fipe_price=Price.from_float(35000.0),
        discount=Discount.from_prices(25000.0, 35000.0),
        score=Score(value=85),
        marketplace="olx",
        listing_url="https://olx.com.br/listing/12345",
        condition="good",
        mileage=50000,
        status="active",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0)
    )


def test_save_opportunity(repository: SQLAlchemyOpportunityRepository, sample_opportunity: Opportunity):
    """Test saving an opportunity to database."""

    repository.save(sample_opportunity)


    result = repository.find_by_listing_id(sample_opportunity.listing_id)
    assert result is not None
    assert result.brand == sample_opportunity.brand
    assert result.model == sample_opportunity.model
    assert result.status == "active"


def test_find_by_id_returns_none_when_not_found(repository: SQLAlchemyOpportunityRepository):
    """Test finding a non-existent opportunity returns None."""

    result = repository.find_by_id("nonexistent-id")


    assert result is None


def test_find_by_listing_id(repository: SQLAlchemyOpportunityRepository, sample_opportunity: Opportunity):
    """Test finding opportunity by listing ID."""

    repository.save(sample_opportunity)


    result = repository.find_by_listing_id(sample_opportunity.listing_id)


    assert result is not None
    assert result.listing_id == sample_opportunity.listing_id
    assert result.score.value == sample_opportunity.score.value


def test_find_active_opportunities(repository: SQLAlchemyOpportunityRepository):
    """Test finding active opportunities sorted by score."""

    opp1 = Opportunity(
        listing_id="listing-1",
        brand="Volkswagen",
        model="Gol",
        year=2020,
        listing_price=Price.from_float(25000.0),
        fipe_price=Price.from_float(35000.0),
        discount=Discount.from_prices(25000.0, 35000.0),
        score=Score(value=85),
        marketplace="olx",
        listing_url="https://olx.com.br/1",
        condition="good",
        mileage=50000,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    opp2 = Opportunity(
        listing_id="listing-2",
        brand="Fiat",
        model="Uno",
        year=2019,
        listing_price=Price.from_float(20000.0),
        fipe_price=Price.from_float(30000.0),
        discount=Discount.from_prices(20000.0, 30000.0),
        score=Score(value=90),
        marketplace="webmotors",
        listing_url="https://webmotors.com.br/2",
        condition="excellent",
        mileage=30000,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    opp3 = Opportunity(
        listing_id="listing-3",
        brand="Chevrolet",
        model="Onix",
        year=2021,
        listing_price=Price.from_float(28000.0),
        fipe_price=Price.from_float(38000.0),
        discount=Discount.from_prices(28000.0, 38000.0),
        score=Score(value=60),
        marketplace="olx",
        listing_url="https://olx.com.br/3",
        condition="fair",
        mileage=70000,
        status="sold",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    repository.save(opp1)
    repository.save(opp2)
    repository.save(opp3)


    results = repository.find_active(min_score=70, limit=10)


    assert len(results) == 2
    assert results[0].score.value == 90
    assert results[1].score.value == 85


def test_find_by_status(repository: SQLAlchemyOpportunityRepository, sample_opportunity: Opportunity):
    """Test finding opportunities by status."""

    repository.save(sample_opportunity)


    active_results = repository.find_by_status("active", limit=10)
    sold_results = repository.find_by_status("sold", limit=10)


    assert len(active_results) == 1
    assert len(sold_results) == 0


def test_count_by_status(repository: SQLAlchemyOpportunityRepository, sample_opportunity: Opportunity):
    """Test counting opportunities by status."""

    repository.save(sample_opportunity)


    active_count = repository.count_by_status("active")
    sold_count = repository.count_by_status("sold")


    assert active_count == 1
    assert sold_count == 0


def test_update_status(repository: SQLAlchemyOpportunityRepository, sample_opportunity: Opportunity):
    """Test updating opportunity status."""

    repository.save(sample_opportunity)


    repository.update_status(sample_opportunity.listing_id, "sold")


    result = repository.find_by_listing_id(sample_opportunity.listing_id)
    assert result is not None
    assert result.status == "sold"
