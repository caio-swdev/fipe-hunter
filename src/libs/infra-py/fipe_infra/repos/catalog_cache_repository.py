"""
Catalog Cache Repository

Adaptive-TTL cache for FIPE MMY (Make/Model/Year) catalog data.
TTL grows as successive fetches return consistent item counts (stable_streak),
shrinks back to 1h whenever the count changes (possible partial/bad response).
"""
import json
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from fipe_infra.database.models import CatalogCacheModel

_TTL_LADDER = [
    (10, 30 * 24 * 3600),  # streak >= 10: 30 days
    (6,   7 * 24 * 3600),  # streak >= 6:  7 days
    (3,        24 * 3600),  # streak >= 3:  1 day
    (1,         6 * 3600),  # streak >= 1:  6h
    (0,             3600),  # streak  = 0:  1h
]


def _ttl_for_streak(streak: int) -> int:
    for min_streak, ttl in _TTL_LADDER:
        if streak >= min_streak:
            return ttl
    return 3600


class CatalogCacheRepository:
    """SQLite-backed adaptive-TTL cache for FIPE catalog (brands/models/years)."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, key: str) -> Optional[Any]:
        """Return deserialized data if entry exists and is not expired, else None."""
        row = self.session.query(CatalogCacheModel).filter_by(key=key).first()
        if not row:
            return None
        if datetime.utcnow() > row.expires_at:
            return None
        return json.loads(row.data_json)

    def set(self, key: str, data: Any, count: int) -> None:
        """Upsert entry with adaptive TTL.

        If count matches last_count, increments stable_streak and raises TTL.
        If count differs, resets streak to 0 and TTL back to 1h.
        """
        now = datetime.utcnow()
        data_json = json.dumps(data, default=str)

        row = self.session.query(CatalogCacheModel).filter_by(key=key).first()
        if row:
            if count == row.last_count:
                streak = row.stable_streak + 1
            else:
                streak = 0
            ttl = _ttl_for_streak(streak)
            row.data_json = data_json
            row.last_count = count
            row.stable_streak = streak
            row.current_ttl_seconds = ttl
            row.cached_at = now
            row.expires_at = now + timedelta(seconds=ttl)
        else:
            streak = 0
            ttl = _ttl_for_streak(streak)
            self.session.add(CatalogCacheModel(
                key=key,
                data_json=data_json,
                last_count=count,
                stable_streak=streak,
                current_ttl_seconds=ttl,
                cached_at=now,
                expires_at=now + timedelta(seconds=ttl),
            ))
        self.session.commit()
