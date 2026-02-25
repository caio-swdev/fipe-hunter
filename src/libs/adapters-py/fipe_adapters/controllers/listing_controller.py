"""
ListingController - FastAPI Controller for Listing CRUD Operations

Orchestrates use cases for listing management via HTTP endpoints.
"""
from datetime import datetime
from typing import Dict, Any, List
from fipe_business.domain.entities.listing import Listing
from fipe_business.application.ports.listing_repository import IListingRepository


class ListingController:
    """Controller for listing CRUD operations."""

    def __init__(self, repository: IListingRepository):
        """
        Initialize controller with repository dependency.

        Args:
            repository: SQLAlchemy listing repository instance
        """
        self.repository = repository

    def create(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new listing.

        Args:
            request_data: Dictionary containing listing fields

        Returns:
            Response dictionary with status and created listing data

        Raises:
            ValueError: If validation fails
            IntegrityError: If URL already exists
        """
        # Create entity (validation happens in entity __post_init__)
        listing = Listing(
            brand=request_data["brand"],
            model=request_data["model"],
            year=request_data["year"],
            price=request_data["price"],
            mileage=request_data.get("mileage"),
            condition=request_data["condition"],
            url=request_data["url"],
            marketplace=request_data["marketplace"],
            scraped_at=datetime.utcnow()
        )

        # Persist via repository
        self.repository.save(listing)

        return {
            "status": "created",
            "data": self._to_response(listing)
        }

    def get_by_url(self, url: str) -> Dict[str, Any]:
        """
        Get a listing by URL.

        Args:
            url: Listing URL to search for

        Returns:
            Response dictionary with status and listing data or not_found
        """
        listing = self.repository.find_by_url(url)

        if listing is None:
            return {
                "status": "not_found",
                "message": "Listing not found"
            }

        return {
            "status": "success",
            "data": self._to_response(listing)
        }

    def list(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """
        List all listings with pagination.

        Args:
            limit: Maximum number of listings to return
            offset: Number of listings to skip

        Returns:
            Response dictionary with status, data array, and pagination info
        """
        listings = self.repository.list_all(limit=limit, offset=offset)
        total = self.repository.count_all()

        return {
            "status": "success",
            "data": [self._to_response(listing) for listing in listings],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }

    def delete_by_url(self, url: str) -> Dict[str, Any]:
        """
        Delete a listing by URL.

        Args:
            url: Listing URL to delete

        Returns:
            Response dictionary with status and message
        """
        # Check if exists first
        listing = self.repository.find_by_url(url)
        if listing is None:
            return {
                "status": "not_found",
                "message": "Listing not found"
            }

        self.repository.delete_by_url(url)

        return {
            "status": "deleted",
            "message": "Listing deleted successfully"
        }

    def update(self, url: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a listing by URL.

        Args:
            url: Listing URL to update
            update_data: Dictionary with fields to update

        Returns:
            Response dictionary with status and updated listing data

        Raises:
            ValueError: If validation fails
        """
        # Find existing listing
        existing = self.repository.find_by_url(url)
        if existing is None:
            return {
                "status": "not_found",
                "message": "Listing not found"
            }

        # Create updated entity (merge existing with updates)
        updated_listing = Listing(
            brand=update_data.get("brand", existing.brand),
            model=update_data.get("model", existing.model),
            year=update_data.get("year", existing.year),
            price=update_data.get("price", existing.price),
            mileage=update_data.get("mileage", existing.mileage),
            condition=update_data.get("condition", existing.condition),
            url=existing.url,  # URL is immutable
            marketplace=update_data.get("marketplace", existing.marketplace),
            scraped_at=existing.scraped_at
        )

        # Persist update
        self.repository.update(updated_listing)

        return {
            "status": "updated",
            "data": self._to_response(updated_listing)
        }

    def get_stats_by_marketplace(self) -> Dict[str, Any]:
        """
        Get listing statistics grouped by marketplace.

        Returns:
            Response dictionary with status and marketplace stats
        """
        olx_count = self.repository.count_by_marketplace("olx")
        webmotors_count = self.repository.count_by_marketplace("webmotors")

        return {
            "status": "success",
            "data": {
                "olx": olx_count,
                "webmotors": webmotors_count,
                "total": olx_count + webmotors_count
            }
        }

    def _to_response(self, listing: Listing) -> Dict[str, Any]:
        """
        Convert listing entity to response DTO.

        Args:
            listing: Listing entity

        Returns:
            Dictionary representation for API response
        """
        return {
            "brand": listing.brand,
            "model": listing.model,
            "year": listing.year,
            "price": listing.price,
            "mileage": listing.mileage,
            "condition": listing.condition,
            "url": listing.url,
            "marketplace": listing.marketplace,
            "scraped_at": listing.scraped_at.isoformat()
        }
