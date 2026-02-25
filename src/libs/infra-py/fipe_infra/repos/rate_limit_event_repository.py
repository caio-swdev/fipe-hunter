"""
SQLAlchemy Rate-Limit Event Repository

Persists external API rate-limit events (FIPE, OLX, WebMotors).
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from fipe_infra.database.models import RateLimitEventModel


class SQLAlchemyRateLimitEventRepository:
    """Concrete implementation using SQLAlchemy + SQLite."""

    def __init__(self, session: Session):
        self._session = session

    def record(self, service: str, endpoint: Optional[str], status_code: int, retry_attempt: int) -> None:
        event = RateLimitEventModel(
            service=service,
            endpoint=endpoint,
            status_code=status_code,
            retry_attempt=retry_attempt,
            occurred_at=datetime.utcnow(),
        )
        self._session.add(event)
        self._session.commit()

    def count_since(self, service: str, since: datetime) -> int:
        return (
            self._session.query(RateLimitEventModel)
            .filter(
                RateLimitEventModel.service == service,
                RateLimitEventModel.occurred_at >= since,
            )
            .count()
        )

    def last_event_at(self, service: str) -> Optional[datetime]:
        row = (
            self._session.query(RateLimitEventModel)
            .filter(RateLimitEventModel.service == service)
            .order_by(desc(RateLimitEventModel.occurred_at))
            .first()
        )
        return row.occurred_at if row else None

    def cleanup(self, retain_days: int = 30) -> int:
        """Delete rows older than retain_days. Returns deleted count."""
        cutoff = datetime.utcnow() - timedelta(days=retain_days)
        deleted = (
            self._session.query(RateLimitEventModel)
            .filter(RateLimitEventModel.occurred_at < cutoff)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return deleted
