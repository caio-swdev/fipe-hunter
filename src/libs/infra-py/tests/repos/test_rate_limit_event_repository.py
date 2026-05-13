"""
Integration Test: SQLAlchemyRateLimitEventRepository

Covers the three port methods:
- record()       — persists a rate-limit event row
- count_since()  — counts events per service after a given datetime
- last_event_at() — returns the most-recent event timestamp for a service
"""
import pytest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from fipe_infra.database.models import Base
from fipe_infra.repos.rate_limit_event_repository import SQLAlchemyRateLimitEventRepository


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def repo(db_session: Session) -> SQLAlchemyRateLimitEventRepository:
    return SQLAlchemyRateLimitEventRepository(db_session)


def test_record_persists_event(repo, db_session):
    """record() must insert a row with the correct field values."""
    repo.record("fipe", "/carros/marcas", 429, 0)

    from fipe_infra.database.models import RateLimitEventModel
    row = db_session.query(RateLimitEventModel).first()

    assert row is not None
    assert row.service == "fipe"
    assert row.endpoint == "/carros/marcas"
    assert row.status_code == 429
    assert row.retry_attempt == 0
    assert row.occurred_at is not None


def test_record_endpoint_can_be_none(repo, db_session):
    """record() must succeed when endpoint is None."""
    repo.record("olx", None, 429, 0)

    from fipe_infra.database.models import RateLimitEventModel
    row = db_session.query(RateLimitEventModel).first()
    assert row is not None
    assert row.endpoint is None


def test_record_multiple_events(repo, db_session):
    """Multiple record() calls create independent rows."""
    repo.record("fipe", "/brands", 429, 0)
    repo.record("fipe", "/models", 429, 1)
    repo.record("olx", None, 429, 0)

    from fipe_infra.database.models import RateLimitEventModel
    assert db_session.query(RateLimitEventModel).count() == 3


def test_count_since_counts_events_after_cutoff(repo):
    """count_since() returns only events at or after the since datetime."""
    now = datetime.utcnow()
    two_hours_ago = now - timedelta(hours=2)
    thirty_min_ago = now - timedelta(minutes=30)


    from fipe_infra.database.models import RateLimitEventModel
    from sqlalchemy.orm import Session
    session = repo._session
    session.add(RateLimitEventModel(service="fipe", status_code=429, retry_attempt=0, occurred_at=two_hours_ago))
    session.add(RateLimitEventModel(service="fipe", status_code=429, retry_attempt=0, occurred_at=thirty_min_ago))
    session.add(RateLimitEventModel(service="fipe", status_code=429, retry_attempt=0, occurred_at=thirty_min_ago))
    session.commit()

    since_1h = now - timedelta(hours=1)
    count = repo.count_since("fipe", since_1h)

    assert count == 2


def test_count_since_filters_by_service(repo):
    """count_since() must not mix events from different services."""
    now = datetime.utcnow()
    ten_min_ago = now - timedelta(minutes=10)

    from fipe_infra.database.models import RateLimitEventModel
    session = repo._session
    session.add(RateLimitEventModel(service="fipe", status_code=429, retry_attempt=0, occurred_at=ten_min_ago))
    session.add(RateLimitEventModel(service="olx", status_code=429, retry_attempt=0, occurred_at=ten_min_ago))
    session.add(RateLimitEventModel(service="olx", status_code=429, retry_attempt=0, occurred_at=ten_min_ago))
    session.commit()

    since = now - timedelta(hours=1)
    assert repo.count_since("fipe", since) == 1
    assert repo.count_since("olx", since) == 2
    assert repo.count_since("webmotors", since) == 0


def test_count_since_returns_zero_for_empty_table(repo):
    """count_since() returns 0 when no events exist."""
    since = datetime.utcnow() - timedelta(hours=24)
    assert repo.count_since("fipe", since) == 0


def test_last_event_at_returns_most_recent(repo):
    """last_event_at() returns the timestamp of the most-recent event."""
    now = datetime.utcnow()
    older = now - timedelta(hours=3)
    newer = now - timedelta(minutes=5)

    from fipe_infra.database.models import RateLimitEventModel
    session = repo._session
    session.add(RateLimitEventModel(service="fipe", status_code=429, retry_attempt=0, occurred_at=older))
    session.add(RateLimitEventModel(service="fipe", status_code=429, retry_attempt=0, occurred_at=newer))
    session.commit()

    result = repo.last_event_at("fipe")

    assert result is not None

    assert abs((result - newer).total_seconds()) < 1


def test_last_event_at_returns_none_when_no_events(repo):
    """last_event_at() returns None when service has no events."""
    assert repo.last_event_at("fipe") is None


def test_last_event_at_is_per_service(repo):
    """last_event_at() does not return events from other services."""
    from fipe_infra.database.models import RateLimitEventModel
    session = repo._session
    session.add(RateLimitEventModel(service="olx", status_code=429, retry_attempt=0, occurred_at=datetime.utcnow()))
    session.commit()

    assert repo.last_event_at("fipe") is None
    assert repo.last_event_at("webmotors") is None
