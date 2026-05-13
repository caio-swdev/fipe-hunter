"""
Mock OLX Scraper for Testing

Returns fake listings to demonstrate the feature working.
"""
from datetime import datetime
from typing import List
from fipe_business.domain.entities import Listing


class MockOLXScraper:
    """Mock scraper that returns fake listings."""


    BASE_URL = "https://rj.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios"

    def __init__(self):
        """Initialize mock scraper."""
        pass

    def get_marketplace_name(self) -> str:
        """Get marketplace name."""
        return "olx"

    def scrape(self, max_listings: int = 50) -> List[Listing]:
        """
        Return fake listings for testing.

        Args:
            max_listings: Maximum number of listings to return

        Returns:
            List of fake listings
        """

        search_terms = []
        if hasattr(self, 'BASE_URL') and '?q=' in self.BASE_URL:
            query = self.BASE_URL.split('?q=')[1]
            search_terms = query.replace('+', ' ').split()


        brand = search_terms[0] if len(search_terms) > 0 else "Toyota"
        model = search_terms[1] if len(search_terms) > 1 else "Corolla"
        year = int(search_terms[2]) if len(search_terms) > 2 and search_terms[2].isdigit() else 2000


        fake_listings = [
            Listing(
                brand=brand,
                model=model,
                year=year,
                price=45000.00,
                mileage=50000,
                condition="good",
                url=f"https://rj.olx.com.br/fake-listing-1-{brand}-{model}-{year}",
                marketplace="olx",
                scraped_at=datetime.now(),
            ),
            Listing(
                brand=brand,
                model=model,
                year=year,
                price=48000.00,
                mileage=35000,
                condition="excellent",
                url=f"https://rj.olx.com.br/fake-listing-2-{brand}-{model}-{year}",
                marketplace="olx",
                scraped_at=datetime.now(),
            ),
            Listing(
                brand=brand,
                model=model,
                year=year,
                price=42000.00,
                mileage=80000,
                condition="good",
                url=f"https://rj.olx.com.br/fake-listing-3-{brand}-{model}-{year}",
                marketplace="olx",
                scraped_at=datetime.now(),
            ),
        ]

        return fake_listings[:max_listings]
