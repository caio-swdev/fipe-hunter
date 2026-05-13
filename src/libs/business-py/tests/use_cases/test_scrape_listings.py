"""
Unit Tests for Scrape Listings Use Case

Tests the scraping workflow orchestration with mocked dependencies.
"""
import pytest
from unittest.mock import Mock
from datetime import datetime
from fipe_business.application.use_cases import ScrapeListingsUseCase
from fipe_business.domain.entities import Listing


class TestScrapeListingsUseCase:
    """Test scraping workflow orchestration."""

    def test_scrape_new_listings_success(self):
        """Test successful scrape with all new listings."""

        mock_scraper = Mock()
        mock_listings = [
            Listing(
                brand="Honda",
                model="Civic",
                year=2020,
                price=80000.0,
                mileage=30000,
                condition="good",
                url="https://olx.com/listing1",
                marketplace="olx",
                scraped_at=datetime.now()
            ),
            Listing(
                brand="Toyota",
                model="Corolla",
                year=2021,
                price=95000.0,
                mileage=20000,
                condition="excellent",
                url="https://olx.com/listing2",
                marketplace="olx",
                scraped_at=datetime.now()
            )
        ]
        mock_scraper.scrape.return_value = mock_listings


        mock_repo = Mock()
        mock_repo.find_by_url.return_value = None


        use_case = ScrapeListingsUseCase(
            scraper=mock_scraper,
            listing_repository=mock_repo
        )
        stats = use_case.execute(max_listings=2)


        assert stats["scraped"] == 2
        assert stats["saved"] == 2
        assert stats["duplicates"] == 0
        assert stats["errors"] == 0


        mock_scraper.scrape.assert_called_once_with(max_listings=2)


        assert mock_repo.save.call_count == 2

    def test_scrape_with_duplicates(self):
        """Test scrape with some duplicate listings."""

        mock_scraper = Mock()
        mock_listings = [
            Listing(
                brand="Honda",
                model="Civic",
                year=2020,
                price=80000.0,
                mileage=30000,
                condition="good",
                url="https://olx.com/listing1",
                marketplace="olx",
                scraped_at=datetime.now()
            ),
            Listing(
                brand="Toyota",
                model="Corolla",
                year=2021,
                price=95000.0,
                mileage=20000,
                condition="excellent",
                url="https://olx.com/listing2",
                marketplace="olx",
                scraped_at=datetime.now()
            )
        ]
        mock_scraper.scrape.return_value = mock_listings


        mock_repo = Mock()
        mock_repo.find_by_url.side_effect = [
            mock_listings[0],
            None
        ]


        use_case = ScrapeListingsUseCase(
            scraper=mock_scraper,
            listing_repository=mock_repo
        )
        stats = use_case.execute(max_listings=2)


        assert stats["scraped"] == 2
        assert stats["saved"] == 1
        assert stats["duplicates"] == 1
        assert stats["errors"] == 0


        assert mock_repo.save.call_count == 1

    def test_scrape_with_save_errors(self):
        """Test scrape with errors during save."""

        mock_scraper = Mock()
        mock_listings = [
            Listing(
                brand="Honda",
                model="Civic",
                year=2020,
                price=80000.0,
                mileage=30000,
                condition="good",
                url="https://olx.com/listing1",
                marketplace="olx",
                scraped_at=datetime.now()
            ),
            Listing(
                brand="Toyota",
                model="Corolla",
                year=2021,
                price=95000.0,
                mileage=20000,
                condition="excellent",
                url="https://olx.com/listing2",
                marketplace="olx",
                scraped_at=datetime.now()
            )
        ]
        mock_scraper.scrape.return_value = mock_listings


        mock_repo = Mock()
        mock_repo.find_by_url.return_value = None
        mock_repo.save.side_effect = [
            Exception("Database error"),
            None
        ]


        use_case = ScrapeListingsUseCase(
            scraper=mock_scraper,
            listing_repository=mock_repo
        )
        stats = use_case.execute(max_listings=2)


        assert stats["scraped"] == 2
        assert stats["saved"] == 1
        assert stats["duplicates"] == 0
        assert stats["errors"] == 1

    def test_scrape_empty_result(self):
        """Test scrape with no listings found."""

        mock_scraper = Mock()
        mock_scraper.scrape.return_value = []


        mock_repo = Mock()


        use_case = ScrapeListingsUseCase(
            scraper=mock_scraper,
            listing_repository=mock_repo
        )
        stats = use_case.execute(max_listings=50)


        assert stats["scraped"] == 0
        assert stats["saved"] == 0
        assert stats["duplicates"] == 0
        assert stats["errors"] == 0


        assert mock_repo.save.call_count == 0

    def test_scrape_failure(self):
        """Test handling of scraper failure."""

        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = Exception("Scraping failed")


        mock_repo = Mock()


        use_case = ScrapeListingsUseCase(
            scraper=mock_scraper,
            listing_repository=mock_repo
        )

        with pytest.raises(Exception, match="Scraping failed"):
            use_case.execute(max_listings=50)
