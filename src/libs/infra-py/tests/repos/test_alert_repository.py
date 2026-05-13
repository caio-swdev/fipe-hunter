"""
Integration Test: Alert Repository

Tests the SQLAlchemy implementation of IAlertRepository.
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fipe_business.domain.entities.alert import Alert
from fipe_infra.database.models import Base, AlertModel
from fipe_infra.repos.alert_repository import SQLAlchemyAlertRepository


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
def repository(db_session: Session) -> SQLAlchemyAlertRepository:
    """Create repository instance."""
    return SQLAlchemyAlertRepository(db_session)


@pytest.fixture
def sample_alert() -> Alert:
    """Create sample alert for testing."""
    return Alert(
        alert_id="alert-123",
        opportunity_id="opp-123",
        recipient_id="telegram-user-456",
        channel="telegram",
        message="Great deal: VW Gol 2020 - 28% off!",
        status="pending",
        sent_at=None,
        delivered_at=None,
        error_message=None,
        retry_count=0,
        created_at=datetime(2024, 1, 1, 12, 0, 0)
    )


def test_save_alert(repository: SQLAlchemyAlertRepository, sample_alert: Alert):
    """Test saving an alert to database."""

    repository.save(sample_alert)


    result = repository.find_by_id(sample_alert.alert_id)
    assert result is not None
    assert result.alert_id == sample_alert.alert_id
    assert result.opportunity_id == sample_alert.opportunity_id
    assert result.status == "pending"


def test_find_by_id_returns_none_when_not_found(repository: SQLAlchemyAlertRepository):
    """Test finding a non-existent alert returns None."""

    result = repository.find_by_id("nonexistent-id")


    assert result is None


def test_find_pending_alerts(repository: SQLAlchemyAlertRepository):
    """Test finding pending alerts."""

    alert1 = Alert(
        alert_id="alert-1",
        opportunity_id="opp-1",
        recipient_id="user-1",
        channel="telegram",
        message="Great deal on VW Gol!",
        status="pending",
        sent_at=None,
        delivered_at=None,
        error_message=None,
        retry_count=0,
        created_at=datetime.utcnow()
    )

    alert2 = Alert(
        alert_id="alert-2",
        opportunity_id="opp-2",
        recipient_id="user-2",
        channel="telegram",
        message="Amazing Fiat Uno opportunity!",
        status="sent",
        sent_at=datetime.utcnow(),
        delivered_at=None,
        error_message=None,
        retry_count=0,
        created_at=datetime.utcnow()
    )

    alert3 = Alert(
        alert_id="alert-3",
        opportunity_id="opp-3",
        recipient_id="user-3",
        channel="telegram",
        message="Check this Chevrolet Onix!",
        status="pending",
        sent_at=None,
        delivered_at=None,
        error_message=None,
        retry_count=0,
        created_at=datetime.utcnow()
    )

    repository.save(alert1)
    repository.save(alert2)
    repository.save(alert3)


    results = repository.find_pending(limit=10)


    assert len(results) == 2
    assert all(r.status == "pending" for r in results)


def test_find_by_opportunity_id(repository: SQLAlchemyAlertRepository, sample_alert: Alert):
    """Test finding alerts by opportunity ID."""

    repository.save(sample_alert)

    another_alert = Alert(
        alert_id="alert-456",
        opportunity_id=sample_alert.opportunity_id,
        recipient_id="user-2",
        channel="email",
        message="Another alert for the same car!",
        status="sent",
        sent_at=datetime.utcnow(),
        delivered_at=None,
        error_message=None,
        retry_count=0,
        created_at=datetime.utcnow()
    )
    repository.save(another_alert)


    results = repository.find_by_opportunity_id(sample_alert.opportunity_id)


    assert len(results) == 2


def test_update_status(repository: SQLAlchemyAlertRepository, sample_alert: Alert):
    """Test updating alert status."""

    repository.save(sample_alert)


    repository.update_status(sample_alert.alert_id, "sent")


    result = repository.find_by_id(sample_alert.alert_id)
    assert result is not None
    assert result.status == "sent"


def test_count_by_status(repository: SQLAlchemyAlertRepository, sample_alert: Alert):
    """Test counting alerts by status."""

    repository.save(sample_alert)

    sent_alert = Alert(
        alert_id="alert-789",
        opportunity_id="opp-789",
        recipient_id="user-3",
        channel="telegram",
        message="This alert was sent successfully!",
        status="sent",
        sent_at=datetime.utcnow(),
        delivered_at=None,
        error_message=None,
        retry_count=0,
        created_at=datetime.utcnow()
    )
    repository.save(sent_alert)


    pending_count = repository.count_by_status("pending")
    sent_count = repository.count_by_status("sent")


    assert pending_count == 1
    assert sent_count == 1
