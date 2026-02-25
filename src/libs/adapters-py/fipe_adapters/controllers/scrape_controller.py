"""
ScrapeController - FastAPI Controller for Web Scraping Operations

Orchestrates scraping and processing workflows via HTTP endpoints.
"""
from typing import Dict, Any
from fipe_business.application.use_cases import (
    ScrapeListingsUseCase,
    ProcessNewListingsUseCase
)
from fipe_infra.repos.listing_repository import SQLAlchemyListingRepository


class ScrapeController:
    """Controller for web scraping operations."""

    def __init__(
        self,
        scrape_listings_usecase: ScrapeListingsUseCase,
        process_listings_usecase: ProcessNewListingsUseCase,
        listing_repository: SQLAlchemyListingRepository
    ):
        """
        Initialize controller with use case dependencies.

        Args:
            scrape_listings_usecase: Use case for scraping marketplaces
            process_listings_usecase: Use case for processing listings pipeline
            listing_repository: Repository for listing access
        """
        self.scrape_listings = scrape_listings_usecase
        self.process_listings = process_listings_usecase
        self.listing_repository = listing_repository

    def scrape_olx(self, limit: int = 50) -> Dict[str, Any]:
        """
        Trigger manual OLX scrape.

        Args:
            limit: Maximum number of listings to scrape

        Returns:
            Response dictionary with status and scrape statistics

        Raises:
            Exception: If scraping fails
        """
        try:
            # Execute scraping
            stats = self.scrape_listings.execute(max_listings=limit)

            return {
                "status": "success",
                "message": f"Scraped {stats['scraped']} listings from OLX",
                "data": {
                    "scraped": stats["scraped"],
                    "saved": stats["saved"],
                    "duplicates": stats["duplicates"],
                    "errors": stats["errors"]
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Scraping failed: {str(e)}",
                "data": None
            }

    async def process_new_listings(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Process unprocessed listings through opportunity pipeline.

        Args:
            limit: Maximum number of listings to process
            offset: Number of listings to skip

        Returns:
            Response dictionary with status and processing statistics

        Raises:
            Exception: If processing fails
        """
        try:
            # Fetch listings from repository
            listings = self.listing_repository.list_all(limit=limit, offset=offset)

            if not listings:
                return {
                    "status": "success",
                    "message": "No listings to process",
                    "data": {
                        "processed": 0,
                        "opportunities_created": 0,
                        "no_fipe_price": 0,
                        "below_threshold": 0,
                        "suspicious": 0,
                        "errors": 0
                    }
                }

            # Generate listing IDs (using URL hash for simplicity)
            def listing_id_generator(listing):
                return str(hash(listing.url))

            # Process listings through pipeline
            stats = await self.process_listings.execute(
                listings=listings,
                listing_id_generator=listing_id_generator
            )

            return {
                "status": "success",
                "message": f"Processed {stats['processed']} listings",
                "data": stats
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Processing failed: {str(e)}",
                "data": None
            }

    def get_scrape_status(self) -> Dict[str, Any]:
        """
        Get scraping status and statistics.

        Returns:
            Response dictionary with status and statistics
        """
        try:
            # Get listing counts by marketplace
            olx_count = self.listing_repository.count_by_marketplace("olx")
            total_count = self.listing_repository.count_all()

            return {
                "status": "success",
                "data": {
                    "total_listings": total_count,
                    "olx_listings": olx_count,
                    "last_scrape": None,  # TODO: Track last scrape timestamp
                    "status": "idle"  # TODO: Track active scraping status
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get status: {str(e)}",
                "data": None
            }
