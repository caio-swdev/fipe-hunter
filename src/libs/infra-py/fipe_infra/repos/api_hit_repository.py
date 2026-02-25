"""
API Hit Repository

Records every outbound call to 3rd-party APIs (FIPE, OLX, WebMotors).
Provides hourly time-series queries for the monitoring dashboard.
"""
from datetime import datetime, timedelta
from typing import List, Dict

from sqlalchemy.orm import Session

from fipe_infra.database.models import ApiHitModel


class ApiHitRepository:
    """Tracks and queries outbound 3rd-party API calls."""

    def __init__(self, session: Session):
        self.session = session

    def record(self, service: str) -> None:
        """Record a single outbound API call. Non-fatal — never poisons the session."""
        try:
            self.session.add(ApiHitModel(
                service=service,
                called_at=datetime.utcnow(),
            ))
            self.session.commit()
        except Exception:
            self.session.rollback()

    def count_since(self, service: str, since: datetime) -> int:
        """Total hits for a service since a given datetime."""
        return (
            self.session.query(ApiHitModel)
            .filter(ApiHitModel.service == service, ApiHitModel.called_at >= since)
            .count()
        )

    def hourly_counts(self, service: str, hours: int = 24) -> List[Dict]:
        """
        Return hourly hit counts for the last N hours.

        Returns a list of {hour, count} dicts sorted ascending,
        with zero-filled buckets for hours with no activity.
        Buckets in Python (no DB-specific strftime).
        """
        now = datetime.utcnow()
        since = now - timedelta(hours=hours)

        rows = (
            self.session.query(ApiHitModel.called_at)
            .filter(ApiHitModel.service == service, ApiHitModel.called_at >= since)
            .all()
        )

        hits_by_hour: Dict[str, int] = {}
        for (called_at,) in rows:
            bucket_key = called_at.strftime("%Y-%m-%dT%H:00")
            hits_by_hour[bucket_key] = hits_by_hour.get(bucket_key, 0) + 1

        series = []
        for h in range(hours):
            bucket_dt = now - timedelta(hours=hours - 1 - h)
            bucket_key = bucket_dt.strftime("%Y-%m-%dT%H:00")
            series.append({"hour": bucket_key, "count": hits_by_hour.get(bucket_key, 0)})

        return series

    def cleanup(self, retain_days: int = 30) -> int:
        """Delete rows older than retain_days. Returns deleted count."""
        cutoff = datetime.utcnow() - timedelta(days=retain_days)
        deleted = (
            self.session.query(ApiHitModel)
            .filter(ApiHitModel.called_at < cutoff)
            .delete(synchronize_session=False)
        )
        self.session.commit()
        return deleted
