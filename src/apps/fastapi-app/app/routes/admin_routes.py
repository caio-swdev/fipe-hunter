"""
Admin Routes

Provides admin-only health and metrics endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fipe_infra.database.session import get_db_session
from app.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
def admin_health(
    session: Session = Depends(get_db_session),
    _: str = Depends(get_current_admin),
):
    """Admin health check — returns per-service status, alerts, scraping, and cache metrics."""
    from app.main.factories.admin_factory import get_admin_health
    return get_admin_health(session)
