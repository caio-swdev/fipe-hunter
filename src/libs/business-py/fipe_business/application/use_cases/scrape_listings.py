"""
Use Case: Scrape Listings

Orchestrates the scraping workflow: scrape marketplace, deduplicate, save to repository.
"""
from typing import Dict
from fipe_business.application.ports import IScraper, IListingRepository


class ScrapeListingsUseCase:
    """Orchestrate marketplace scraping workflow."""

    def __init__(
        self,
        scraper: IScraper,
        listing_repository: IListingRepository
    ):
        """
        Initialize use case with dependencies.

        Args:
            scraper: Marketplace scraper implementation
            listing_repository: Repository for persisting listings
        """
        self.scraper = scraper
        self.listing_repository = listing_repository

    def execute(self, max_listings: int = 50) -> Dict[str, int]:
        """
        Execute scraping workflow.

        Flow:
        1. Scrape marketplace with max_listings limit
        2. For each scraped listing:
           a. Check if URL already exists in repository (deduplication)
           b. If duplicate: skip, increment duplicate counter
           c. If new: save to repository, increment saved counter
        3. Return statistics (scraped, saved, duplicates, errors)

        Args:
            max_listings: Maximum number of listings to scrape

        Returns:
            Dictionary with scrape statistics:
            - scraped: Total listings scraped from marketplace
            - saved: New listings saved to database
            - duplicates: Listings skipped (URL already exists)
            - errors: Listings that failed validation/save

        Raises:
            Exception: If scraping or database operations fail
        """
        stats = {
            "scraped": 0,
            "saved": 0,
            "duplicates": 0,
            "errors": 0
        }

        try:
            # Scrape marketplace
            listings = self.scraper.scrape(max_listings=max_listings)
            stats["scraped"] = len(listings)

            # Process each listing
            for listing in listings:
                try:
                    # Deduplication: check if URL already exists
                    existing = self.listing_repository.find_by_url(listing.url)

                    if existing:
                        # Duplicate found - skip
                        stats["duplicates"] += 1
                        continue

                    # New listing - save to repository
                    self.listing_repository.save(listing)
                    stats["saved"] += 1

                except Exception as e:
                    # Error saving individual listing
                    print(f"Error processing listing {listing.url}: {e}")
                    stats["errors"] += 1
                    continue

        except Exception as e:
            # Scraping failed entirely
            print(f"Scraping failed: {e}")
            raise

        return stats
