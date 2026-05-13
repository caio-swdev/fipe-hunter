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

            listings = self.scraper.scrape(max_listings=max_listings)
            stats["scraped"] = len(listings)


            for listing in listings:
                try:

                    existing = self.listing_repository.find_by_url(listing.url)

                    if existing:

                        stats["duplicates"] += 1
                        continue


                    self.listing_repository.save(listing)
                    stats["saved"] += 1

                except Exception as e:

                    print(f"Error processing listing {listing.url}: {e}")
                    stats["errors"] += 1
                    continue

        except Exception as e:

            print(f"Scraping failed: {e}")
            raise

        return stats
