"""
Unit Tests for Process New Listings Use Case

Tests the end-to-end opportunity pipeline orchestration.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from decimal import Decimal
from fipe_business.application.use_cases import ProcessNewListingsUseCase
from fipe_business.domain.entities import Listing, Opportunity
from fipe_business.domain.value_objects import Price, Discount, Score


class TestProcessNewListingsUseCase:
    """Test opportunity pipeline orchestration."""

    @pytest.mark.asyncio
    async def test_process_listings_with_valid_opportunities(self):
        """Test processing listings that result in valid opportunities."""

        listings = [
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
            )
        ]


        mock_listing_repo = Mock()

        mock_lookup_fipe = Mock()
        mock_lookup_fipe.execute = AsyncMock(return_value={
            "price": 100000.0,
            "fipe_code": "123456",
            "reference_month": "January 2026"
        })

        mock_compare_prices = Mock()
        mock_compare_prices.execute.return_value = (
            Discount(
                percentage=Decimal("20.00"),
                amount=Price.from_float(20000.0)
            ),
            "opportunity"
        )

        mock_calculate_score = Mock()
        mock_calculate_score.execute.return_value = Score(value=85)

        mock_create_opportunity = Mock()
        mock_opportunity = Opportunity(
            listing_id="test-id",
            brand="Honda",
            model="Civic",
            year=2020,
            listing_price=Price.from_float(80000.0),
            fipe_price=Price.from_float(100000.0),
            discount=Discount(
                percentage=Decimal("20.00"),
                amount=Price.from_float(20000.0)
            ),
            score=Score(value=85),
            marketplace="olx",
            listing_url="https://olx.com/listing1",
            condition="good",
            mileage=30000,
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_create_opportunity.execute.return_value = mock_opportunity


        use_case = ProcessNewListingsUseCase(
            listing_repository=mock_listing_repo,
            lookup_fipe_price=mock_lookup_fipe,
            compare_prices=mock_compare_prices,
            calculate_score=mock_calculate_score,
            create_opportunity=mock_create_opportunity
        )

        stats = await use_case.execute(
            listings=listings,
            listing_id_generator=lambda l: "test-id"
        )


        assert stats["processed"] == 1
        assert stats["opportunities_created"] == 1
        assert stats["no_fipe_price"] == 0
        assert stats["below_threshold"] == 0
        assert stats["suspicious"] == 0
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_listings_no_fipe_price(self):
        """Test processing listings with no FIPE price found."""

        listings = [
            Listing(
                brand="Unknown",
                model="Model",
                year=2020,
                price=80000.0,
                mileage=30000,
                condition="good",
                url="https://olx.com/listing1",
                marketplace="olx",
                scraped_at=datetime.now()
            )
        ]


        mock_listing_repo = Mock()

        mock_lookup_fipe = Mock()
        mock_lookup_fipe.execute = AsyncMock(return_value=None)

        mock_compare_prices = Mock()
        mock_calculate_score = Mock()
        mock_create_opportunity = Mock()


        use_case = ProcessNewListingsUseCase(
            listing_repository=mock_listing_repo,
            lookup_fipe_price=mock_lookup_fipe,
            compare_prices=mock_compare_prices,
            calculate_score=mock_calculate_score,
            create_opportunity=mock_create_opportunity
        )

        stats = await use_case.execute(
            listings=listings,
            listing_id_generator=lambda l: "test-id"
        )


        assert stats["processed"] == 1
        assert stats["opportunities_created"] == 0
        assert stats["no_fipe_price"] == 1
        assert stats["errors"] == 0


        mock_create_opportunity.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_listings_below_threshold(self):
        """Test processing listings with discount below threshold."""

        listings = [
            Listing(
                brand="Honda",
                model="Civic",
                year=2020,
                price=95000.0,
                mileage=30000,
                condition="good",
                url="https://olx.com/listing1",
                marketplace="olx",
                scraped_at=datetime.now()
            )
        ]


        mock_listing_repo = Mock()

        mock_lookup_fipe = Mock()
        mock_lookup_fipe.execute = AsyncMock(return_value={
            "price": 100000.0,
            "fipe_code": "123456",
            "reference_month": "January 2026"
        })

        mock_compare_prices = Mock()
        mock_compare_prices.execute.return_value = (
            Discount(
                percentage=Decimal("5.00"),
                amount=Price.from_float(5000.0)
            ),
            "below_threshold"
        )

        mock_calculate_score = Mock()
        mock_create_opportunity = Mock()


        use_case = ProcessNewListingsUseCase(
            listing_repository=mock_listing_repo,
            lookup_fipe_price=mock_lookup_fipe,
            compare_prices=mock_compare_prices,
            calculate_score=mock_calculate_score,
            create_opportunity=mock_create_opportunity
        )

        stats = await use_case.execute(
            listings=listings,
            listing_id_generator=lambda l: "test-id"
        )


        assert stats["processed"] == 1
        assert stats["opportunities_created"] == 0
        assert stats["below_threshold"] == 1
        assert stats["errors"] == 0


        mock_create_opportunity.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_listings_suspicious(self):
        """Test processing listings with suspicious discount (>50%)."""

        listings = [
            Listing(
                brand="Honda",
                model="Civic",
                year=2020,
                price=40000.0,
                mileage=30000,
                condition="good",
                url="https://olx.com/listing1",
                marketplace="olx",
                scraped_at=datetime.now()
            )
        ]


        mock_listing_repo = Mock()

        mock_lookup_fipe = Mock()
        mock_lookup_fipe.execute = AsyncMock(return_value={
            "price": 100000.0,
            "fipe_code": "123456",
            "reference_month": "January 2026"
        })

        mock_compare_prices = Mock()
        mock_compare_prices.execute.return_value = (
            Discount(
                percentage=Decimal("60.00"),
                amount=Price.from_float(60000.0)
            ),
            "suspicious"
        )

        mock_calculate_score = Mock()
        mock_calculate_score.execute.return_value = Score(value=70)

        mock_create_opportunity = Mock()
        mock_opportunity = Mock()
        mock_create_opportunity.execute.return_value = mock_opportunity


        use_case = ProcessNewListingsUseCase(
            listing_repository=mock_listing_repo,
            lookup_fipe_price=mock_lookup_fipe,
            compare_prices=mock_compare_prices,
            calculate_score=mock_calculate_score,
            create_opportunity=mock_create_opportunity
        )

        stats = await use_case.execute(
            listings=listings,
            listing_id_generator=lambda l: "test-id"
        )


        assert stats["processed"] == 1
        assert stats["suspicious"] == 1
        assert stats["opportunities_created"] == 0
        assert stats["errors"] == 0


        mock_create_opportunity.execute.assert_called_once()
        call_kwargs = mock_create_opportunity.execute.call_args[1]
        assert call_kwargs["status"] == "suspicious"

    @pytest.mark.asyncio
    async def test_process_listings_with_errors(self):
        """Test processing with errors in pipeline."""

        listings = [
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
            )
        ]


        mock_listing_repo = Mock()

        mock_lookup_fipe = Mock()
        mock_lookup_fipe.execute = AsyncMock(side_effect=Exception("API error"))

        mock_compare_prices = Mock()
        mock_calculate_score = Mock()
        mock_create_opportunity = Mock()


        use_case = ProcessNewListingsUseCase(
            listing_repository=mock_listing_repo,
            lookup_fipe_price=mock_lookup_fipe,
            compare_prices=mock_compare_prices,
            calculate_score=mock_calculate_score,
            create_opportunity=mock_create_opportunity
        )

        stats = await use_case.execute(
            listings=listings,
            listing_id_generator=lambda l: "test-id"
        )


        assert stats["processed"] == 1
        assert stats["opportunities_created"] == 0
        assert stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_process_empty_listings(self):
        """Test processing with no listings."""

        mock_listing_repo = Mock()
        mock_lookup_fipe = Mock()
        mock_compare_prices = Mock()
        mock_calculate_score = Mock()
        mock_create_opportunity = Mock()

        use_case = ProcessNewListingsUseCase(
            listing_repository=mock_listing_repo,
            lookup_fipe_price=mock_lookup_fipe,
            compare_prices=mock_compare_prices,
            calculate_score=mock_calculate_score,
            create_opportunity=mock_create_opportunity
        )

        stats = await use_case.execute(
            listings=[],
            listing_id_generator=lambda l: "test-id"
        )


        assert stats["processed"] == 0
        assert stats["opportunities_created"] == 0
        assert stats["errors"] == 0
