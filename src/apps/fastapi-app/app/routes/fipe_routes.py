"""
FastAPI Routes for FIPE Lookup

Maps HTTP endpoints to FIPEController methods.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from fipe_adapters.controllers.fipe_controller import FIPEController
from fipe_infra.clients.fipe_client import FIPEClient
from fipe_infra.repos.catalog_cache_repository import CatalogCacheRepository
from fipe_infra.repos.api_hit_repository import ApiHitRepository
from fipe_infra.database.session import get_db_session


# Router instance
router = APIRouter(prefix="/fipe", tags=["fipe"])


def make_fipe_controller() -> FIPEController:
    """
    Factory function to create FIPEController with all dependencies.

    Returns:
        FIPEController instance
    """
    # Import here to avoid circular imports during app initialization
    from app.main.factories.fipe_factory import make_fipe_controller as factory_impl
    return factory_impl()


def get_fipe_controller() -> FIPEController:
    """
    Dependency injection for FIPEController.

    Returns:
        FIPEController instance (can be mocked for testing)
    """
    # This function can be patched by tests to return a mocked controller
    return make_fipe_controller()


@router.get("/lookup/demo")
async def lookup_fipe_demo(
    brand: str = Query(..., min_length=2, description="Vehicle brand"),
    model: str = Query(..., min_length=2, description="Vehicle model"),
    year: int = Query(..., ge=1950, le=2026, description="Vehicle year"),
):
    """
    Demo endpoint that returns mock FIPE data.

    Use this to test the frontend with guaranteed success response.
    """
    return {
        "status": "success",
        "data": {
            "brand": brand.strip().title(),
            "model": model.strip().title(),
            "year": year,
            "fipe_code": "001234-5",
            "reference_price": 85500.00,
            "reference_month": "fevereiro/2026"
        }
    }


@router.get("/lookup")
async def lookup_fipe(
    brand: str = Query(..., min_length=2, description="Vehicle brand"),
    model: str = Query(..., min_length=2, description="Vehicle model"),
    year: int = Query(..., ge=1950, le=2026, description="Vehicle year"),
    controller: FIPEController = Depends(get_fipe_controller),
):
    """
    Lookup FIPE price for a vehicle.

    Args:
        brand: Vehicle brand (min 2 chars)
        model: Vehicle model (min 2 chars)
        year: Vehicle year (1950-2026)
        controller: Injected controller instance

    Returns:
        FIPE price data with status success

    Raises:
        HTTPException: 404 if vehicle not found, 422 for validation errors
    """
    # Trim whitespace from inputs
    brand = brand.strip()
    model = model.strip()

    try:
        response = await controller.lookup(brand=brand, model=model, year=year)

        if response["status"] == "not_found":
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found in FIPE database"
            )

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog/models")
async def get_fipe_models_catalog(
    brand_name: str = Query(..., min_length=2, description="Vehicle brand name"),
    session: Session = Depends(get_db_session),
):
    """
    Get all FIPE models (with versions) for a brand.

    Returns brand_id (needed for subsequent calls) and full models list.
    Each model name already includes the version, e.g. 'Corolla 1.8 GLi CVT'.
    """
    client = FIPEClient(catalog_cache_repo=CatalogCacheRepository(session), api_hit_repo=ApiHitRepository(session))
    result = await client.get_models_for_brand_name(brand_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Brand '{brand_name}' not found in FIPE")
    return result


@router.get("/catalog/versions")
async def get_fipe_versions_catalog(
    brand_id: str = Query(..., description="FIPE brand ID"),
    model_base: str = Query(..., min_length=2, description="Base model name (e.g. 'Corolla')"),
    year: int = Query(..., ge=1950, le=2026, description="Filter by year"),
    session: Session = Depends(get_db_session),
):
    """
    Get versions available for a specific year.

    Checks each model variant matching model_base and returns only
    those that exist in the FIPE database for the given year.
    """
    client = FIPEClient(catalog_cache_repo=CatalogCacheRepository(session), api_hit_repo=ApiHitRepository(session))
    versions = await client.get_versions_for_year(brand_id, model_base, year)
    return {"versions": versions}


@router.get("/catalog/years")
async def get_fipe_years_catalog(
    brand_id: str = Query(..., description="FIPE brand ID"),
    model_id: int = Query(..., description="FIPE model ID"),
    session: Session = Depends(get_db_session),
):
    """
    Get all available years for a specific FIPE model (versão).
    """
    client = FIPEClient(catalog_cache_repo=CatalogCacheRepository(session), api_hit_repo=ApiHitRepository(session))
    years = await client.get_years_for_model(brand_id, model_id)
    return {"years": years}
