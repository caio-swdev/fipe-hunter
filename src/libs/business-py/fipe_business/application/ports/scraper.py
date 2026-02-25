"""
Domain Port: Scraper Interface

Defines the contract for marketplace scrapers.
"""
from typing import Protocol, List
from fipe_business.domain.entities import Listing


class IScraper(Protocol):
    """Interface for marketplace scraper."""

    def scrape(self, max_listings: int = 50) -> List[Listing]:
        """
        Scrape vehicle listings from marketplace.

        Args:
            max_listings: Maximum number of listings to scrape

        Returns:
            List of scraped and validated listings
        """
        ...

    def get_marketplace_name(self) -> str:
        """Get the marketplace name (e.g., 'olx', 'webmotors')."""
        ...
