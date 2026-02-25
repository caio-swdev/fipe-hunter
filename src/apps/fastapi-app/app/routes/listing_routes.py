"""
FastAPI Routes for Listing CRUD

Maps HTTP endpoints to ListingController methods.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from fipe_adapters.controllers.listing_controller import ListingController
from fipe_infra.repos.listing_repository import SQLAlchemyListingRepository
from fipe_infra.database.session import get_db_session


# Pydantic models for request/response validation
class CreateListingRequest(BaseModel):
    """Request model for creating a listing."""

    brand: str = Field(..., min_length=2, description="Vehicle brand")
    model: str = Field(..., min_length=2, description="Vehicle model")
    year: int = Field(..., ge=1950, le=2026, description="Vehicle year")
    price: float = Field(..., gt=0, description="Listing price in BRL")
    mileage: Optional[int] = Field(None, ge=0, description="Vehicle mileage in km")
    condition: str = Field(
        ..., description="Vehicle condition", pattern="^(excellent|good|fair|poor)$"
    )
    url: str = Field(..., min_length=10, description="Listing URL")
    marketplace: str = Field(..., description="Marketplace source")

    class Config:
        json_schema_extra = {
            "example": {
                "brand": "Volkswagen",
                "model": "Gol",
                "year": 2020,
                "price": 45000.00,
                "mileage": 35000,
                "condition": "good",
                "url": "https://example.com/listing/123",
                "marketplace": "olx",
            }
        }


class UpdateListingRequest(BaseModel):
    """Request model for updating a listing."""

    brand: Optional[str] = Field(None, min_length=2)
    model: Optional[str] = Field(None, min_length=2)
    year: Optional[int] = Field(None, ge=1950, le=2026)
    price: Optional[float] = Field(None, gt=0)
    mileage: Optional[int] = Field(None, ge=0)
    condition: Optional[str] = Field(None, pattern="^(excellent|good|fair|poor)$")
    marketplace: Optional[str] = None


# Router instance
router = APIRouter(prefix="/listings", tags=["listings"])


def get_listing_controller(session: Session = Depends(get_db_session)) -> ListingController:
    """
    Dependency injection for ListingController.

    Args:
        session: Database session from dependency

    Returns:
        ListingController instance
    """
    repository = SQLAlchemyListingRepository(session)
    return ListingController(repository)


@router.post("", status_code=201)
def create_listing(
    request: CreateListingRequest,
    controller: ListingController = Depends(get_listing_controller),
):
    """
    Create a new listing.

    Args:
        request: Listing creation data
        controller: Injected controller instance

    Returns:
        Created listing data

    Raises:
        HTTPException: 400 for validation errors, 409 for duplicate URL
    """
    try:
        response = controller.create(request.model_dump())
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=409, detail="Listing URL already exists")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/marketplace")
def get_marketplace_stats(
    controller: ListingController = Depends(get_listing_controller),
):
    """
    Get listing statistics by marketplace.

    Args:
        controller: Injected controller instance

    Returns:
        Marketplace statistics
    """
    return controller.get_stats_by_marketplace()


@router.get("")
def list_listings(
    limit: int = Query(10, ge=1, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    controller: ListingController = Depends(get_listing_controller),
):
    """
    List all listings with pagination.

    Args:
        limit: Maximum number of listings to return
        offset: Number of listings to skip
        controller: Injected controller instance

    Returns:
        Paginated listing data
    """
    return controller.list(limit=limit, offset=offset)


@router.get("/by-url")
def get_listing_by_url(
    url: str = Query(..., description="Listing URL to search"),
    controller: ListingController = Depends(get_listing_controller),
):
    """
    Get a listing by URL.

    Args:
        url: Listing URL
        controller: Injected controller instance

    Returns:
        Listing data

    Raises:
        HTTPException: 404 if listing not found
    """
    response = controller.get_by_url(url)

    if response["status"] == "not_found":
        raise HTTPException(status_code=404, detail=response["message"])

    return response


@router.put("/by-url")
def update_listing(
    url: str = Query(..., description="Listing URL to update"),
    request: UpdateListingRequest = ...,
    controller: ListingController = Depends(get_listing_controller),
):
    """
    Update a listing by URL.

    Args:
        url: Listing URL to update
        request: Fields to update
        controller: Injected controller instance

    Returns:
        Updated listing data

    Raises:
        HTTPException: 404 if not found, 400 for validation errors
    """
    try:
        response = controller.update(url, request.model_dump(exclude_unset=True))

        if response["status"] == "not_found":
            raise HTTPException(status_code=404, detail=response["message"])

        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/by-url", status_code=200)
def delete_listing(
    url: str = Query(..., description="Listing URL to delete"),
    controller: ListingController = Depends(get_listing_controller),
):
    """
    Delete a listing by URL.

    Args:
        url: Listing URL to delete
        controller: Injected controller instance

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: 404 if listing not found
    """
    response = controller.delete_by_url(url)

    if response["status"] == "not_found":
        raise HTTPException(status_code=404, detail=response["message"])

    return response
