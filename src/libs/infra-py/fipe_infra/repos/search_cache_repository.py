"""
Search Cache Repository

Caches scrape results (OLX + WebMotors) by (brand, model, year) key with a 2-hour TTL.
Prevents duplicate outbound scrapes when multiple users search the same vehicle.
"""
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from fipe_infra.database.models import SearchCacheModel

_TTL_HOURS = 2


def _make_key(brand: str, model: str, year: Optional[int]) -> str:
    year_part = str(year) if year else "any"
    return f"search:{brand.lower().strip()}:{model.lower().strip()}:{year_part}"


class SearchCacheRepository:
    """SQLite-backed cache for search scrape results."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, brand: str, model: str, year: Optional[int]) -> Optional[List[Dict[str, Any]]]:
        """Return cached results if present and not expired, else None."""
        key = _make_key(brand, model, year)
        row = self.session.query(SearchCacheModel).filter_by(cache_key=key).first()
        if not row:
            return None
        if datetime.utcnow() > row.expires_at:
            self.session.delete(row)
            self.session.commit()
            return None
        return json.loads(row.results_json)

    def set(self, brand: str, model: str, year: Optional[int], results: List[Dict[str, Any]]) -> None:
        """Store results; upsert on key collision."""
        key = _make_key(brand, model, year)
        now = datetime.utcnow()
        expires = now + timedelta(hours=_TTL_HOURS)
        results_json = json.dumps(results, default=str)

        row = self.session.query(SearchCacheModel).filter_by(cache_key=key).first()
        if row:
            row.results_json = results_json
            row.cached_at = now
            row.expires_at = expires
        else:
            self.session.add(SearchCacheModel(
                cache_key=key,
                brand=brand.lower().strip(),
                model=model.lower().strip(),
                year=year,
                results_json=results_json,
                cached_at=now,
                expires_at=expires,
            ))
        self.session.commit()
