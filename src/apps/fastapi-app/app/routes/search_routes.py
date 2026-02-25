"""
FastAPI Routes for On-Demand Vehicle Search

Thin route layer — all orchestration lives in SearchController.
All DI wiring lives in app/main/factories/search_factory.py.
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from fipe_adapters.controllers.search_controller import SearchController
from fipe_infra.database.session import get_db_session
from app.limiter import limiter


router = APIRouter(prefix="/search", tags=["search"])


class SearchVehicleRequest(BaseModel):
    """Request model for vehicle search."""
    brand: str = Field(..., min_length=2, description="Vehicle brand")
    model: str = Field(..., min_length=2, description="Vehicle model base name")
    year: Optional[int] = Field(None, ge=1950, le=2026, description="Vehicle year (optional)")
    brand_id: Optional[str] = Field(None, description="FIPE brand code")
    model_id: Optional[int] = Field(None, description="FIPE model code (versão)")
    year_code: Optional[str] = Field(None, description="FIPE year code, e.g. '2020-1'")
    version: Optional[str] = Field(None, description="Full FIPE version name for display")


def _get_controller(session: Session = Depends(get_db_session)) -> SearchController:
    from app.main.factories.search_factory import get_search_controller
    return get_search_controller(session)


@router.post("/vehicle")
@limiter.limit("10/hour")
async def search_vehicle(
    request: Request,
    body: SearchVehicleRequest,
    controller: SearchController = Depends(_get_controller),
):
    """On-demand vehicle search — delegates to SearchController."""
    return await controller.search(body.model_dump())
