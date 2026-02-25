"""
Unit Tests: SearchCacheRepository

In-memory SQLite database — zero network calls, zero file I/O.
Pattern mirrors tests/repos/test_cache_repository.py.
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from fipe_infra.database.models import Base
from fipe_infra.repos.search_cache_repository import SearchCacheRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session() -> Session:
    """In-memory SQLite session for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def repo(db_session: Session) -> SearchCacheRepository:
    return SearchCacheRepository(db_session)


_SAMPLE_RESULTS = [
    {"brand": "Honda", "model": "Civic", "price": 50000, "url": "https://olx.com/1"},
    {"brand": "Honda", "model": "Civic", "price": 48000, "url": "https://olx.com/2"},
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_returns_none_on_miss(repo):
    """Empty DB → get returns None."""
    assert repo.get("Honda", "Civic", 2020) is None


def test_set_and_get_roundtrip(repo):
    """set then get within TTL returns the same list."""
    repo.set("Honda", "Civic", 2020, _SAMPLE_RESULTS)
    result = repo.get("Honda", "Civic", 2020)
    assert result is not None
    assert len(result) == 2
    assert result[0]["url"] == _SAMPLE_RESULTS[0]["url"]


def test_get_returns_none_after_expiry(repo):
    """Expired entry is deleted and None is returned."""
    repo.set("Honda", "Civic", 2020, _SAMPLE_RESULTS)

    future = datetime.utcnow() + timedelta(hours=3)  # TTL is 2h; advance past it
    with patch("fipe_infra.repos.search_cache_repository.datetime") as mock_dt:
        mock_dt.utcnow.return_value = future
        result = repo.get("Honda", "Civic", 2020)

    assert result is None

    # Row must be deleted from the database
    from fipe_infra.database.models import SearchCacheModel
    row = repo.session.query(SearchCacheModel).first()
    assert row is None


def test_set_upserts_on_collision(repo):
    """set twice with same key keeps only 1 row with the second value."""
    repo.set("Honda", "Civic", 2020, _SAMPLE_RESULTS)

    new_results = [{"brand": "Honda", "model": "Civic", "price": 45000, "url": "https://olx.com/3"}]
    repo.set("Honda", "Civic", 2020, new_results)

    from fipe_infra.database.models import SearchCacheModel
    rows = repo.session.query(SearchCacheModel).all()
    assert len(rows) == 1

    result = repo.get("Honda", "Civic", 2020)
    assert result is not None
    assert len(result) == 1
    assert result[0]["price"] == 45000


def test_key_normalizes_case(repo):
    """set with "Honda" is retrievable with "honda" (and mixed cases)."""
    repo.set("Honda", "Civic", 2020, _SAMPLE_RESULTS)
    assert repo.get("honda", "civic", 2020) is not None
    assert repo.get("HONDA", "CIVIC", 2020) is not None


def test_year_none_is_valid_key(repo):
    """set/get with year=None works as a distinct cache entry."""
    repo.set("Honda", "Civic", None, _SAMPLE_RESULTS)
    result = repo.get("Honda", "Civic", None)
    assert result is not None
    assert len(result) == 2


def test_different_years_are_different_keys(repo):
    """Year 2020 and 2021 produce independent cache entries."""
    results_2020 = [{"price": 50000}]
    results_2021 = [{"price": 55000}]

    repo.set("Honda", "Civic", 2020, results_2020)
    repo.set("Honda", "Civic", 2021, results_2021)

    r2020 = repo.get("Honda", "Civic", 2020)
    r2021 = repo.get("Honda", "Civic", 2021)

    assert r2020 is not None and r2020[0]["price"] == 50000
    assert r2021 is not None and r2021[0]["price"] == 55000
