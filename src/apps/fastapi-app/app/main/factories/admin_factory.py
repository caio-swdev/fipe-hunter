"""
Admin Health Factory

Queries persisted metrics and returns a structured health snapshot.
"""
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy.orm import Session

from sqlalchemy import func

from fipe_infra.repos.rate_limit_event_repository import SQLAlchemyRateLimitEventRepository
from fipe_infra.repos.api_hit_repository import ApiHitRepository
from fipe_infra.clients.fipe_client import get_cache_stats
from fipe_infra.database.models import AlertModel, OpportunityModel, ListingModel, PriceCacheModel, SearchCacheModel, CatalogCacheModel


def get_admin_health(session: Session) -> Dict[str, Any]:
    """Build a complete admin health payload from persisted data."""
    now = datetime.utcnow()
    since_24h = now - timedelta(hours=24)
    since_1h = now - timedelta(hours=1)

    event_repo = SQLAlchemyRateLimitEventRepository(session)
    api_hit_repo = ApiHitRepository(session)


    try:
        api_hit_repo.cleanup(retain_days=30)
        event_repo.cleanup(retain_days=30)
    except Exception:
        pass


    services: Dict[str, Any] = {}
    for svc in ("fipe", "olx", "webmotors"):
        last_at = event_repo.last_event_at(svc)
        count = event_repo.count_since(svc, since_24h)
        if last_at and last_at >= since_1h:
            status = "rate_limited"
        else:
            status = "ok"
        services[svc] = {
            "status": status,
            "last_429_at": last_at.isoformat() if last_at else None,
            "count_24h": count,
        }


    pending = session.query(AlertModel).filter(AlertModel.status == "pending").count()
    failed = session.query(AlertModel).filter(AlertModel.status == "failed").count()
    sent_today = (
        session.query(AlertModel)
        .filter(AlertModel.status == "sent", AlertModel.sent_at >= since_24h)
        .count()
    )


    opportunities_today = (
        session.query(OpportunityModel)
        .filter(OpportunityModel.created_at >= since_24h)
        .count()
    )
    listings_today = (
        session.query(ListingModel)
        .filter(ListingModel.scraped_at >= since_24h)
        .count()
    )


    total_cache = session.query(PriceCacheModel).count()
    expired_cache = (
        session.query(PriceCacheModel)
        .filter(PriceCacheModel.expires_at < now)
        .count()
    )


    search_total = session.query(SearchCacheModel).count()
    search_expired = (
        session.query(SearchCacheModel)
        .filter(SearchCacheModel.expires_at < now)
        .count()
    )


    catalog_total = session.query(CatalogCacheModel).count()
    catalog_expired = (
        session.query(CatalogCacheModel)
        .filter(CatalogCacheModel.expires_at < now)
        .count()
    )
    streak_row = session.query(
        func.avg(CatalogCacheModel.stable_streak).label("avg_streak"),
        func.max(CatalogCacheModel.stable_streak).label("max_streak"),
    ).first()
    avg_streak = round(float(streak_row.avg_streak), 1) if streak_row.avg_streak is not None else 0.0
    max_streak = streak_row.max_streak or 0

    return {
        "services": services,
        "alerts": {
            "pending": pending,
            "failed": failed,
            "sent_today": sent_today,
        },
        "scraping": {
            "opportunities_today": opportunities_today,
            "listings_today": listings_today,
        },
        "cache": {
            "fipe_entries": total_cache,
            "active": total_cache - expired_cache,
            "expired": expired_cache,
        },
        "search_cache": {
            "total": search_total,
            "active": search_total - search_expired,
            "expired": search_expired,
        },
        "api_hits": {
            svc: {
                "total_24h": api_hit_repo.count_since(svc, since_24h),
                "series": api_hit_repo.hourly_counts(svc, hours=24),
            }
            for svc in ("fipe", "olx", "webmotors")
        },
        "catalog_cache": {
            "total": catalog_total,
            "active": catalog_total - catalog_expired,
            "expired": catalog_expired,
            "avg_streak": avg_streak,
            "max_streak": max_streak,
        },
        "cache_stats": get_cache_stats(),
    }
