"""
Use Case: Process New Listings

End-to-end opportunity pipeline: FIPE lookup → price comparison → scoring → create opportunity.
"""
import logging
from typing import Dict, Callable
from fipe_business.domain.entities import Listing
from fipe_business.application.ports import IListingRepository
from fipe_business.application.use_cases import (
    LookupFIPEPriceUseCase,
    ComparePricesUseCase,
    CalculateOpportunityScoreUseCase,
    CreateOpportunityUseCase
)
from fipe_business.domain.value_objects import Price

logger = logging.getLogger(__name__)


class ProcessNewListingsUseCase:
    """Process listings through the complete opportunity pipeline."""

    def __init__(
        self,
        listing_repository: IListingRepository,
        lookup_fipe_price: LookupFIPEPriceUseCase,
        compare_prices: ComparePricesUseCase,
        calculate_score: CalculateOpportunityScoreUseCase,
        create_opportunity: CreateOpportunityUseCase
    ):
        """
        Initialize use case with all pipeline dependencies.

        Args:
            listing_repository: Repository to fetch listings
            lookup_fipe_price: Use case for FIPE price lookup
            compare_prices: Use case for price comparison
            calculate_score: Use case for opportunity scoring
            create_opportunity: Use case for creating opportunities
        """
        self.listing_repository = listing_repository
        self.lookup_fipe_price = lookup_fipe_price
        self.compare_prices = compare_prices
        self.calculate_score = calculate_score
        self.create_opportunity = create_opportunity

    async def execute(
        self,
        listings: list[Listing],
        listing_id_generator: Callable[[Listing], str]
    ) -> Dict[str, int]:
        """
        Process listings through the complete pipeline.

        Flow for each listing:
        1. Lookup FIPE price (with caching)
        2. Compare prices to calculate discount
        3. Calculate opportunity score
        4. Create opportunity if valid
        5. Handle errors gracefully (continue processing remaining listings)

        Args:
            listings: List of listings to process
            listing_id_generator: Function to generate listing IDs

        Returns:
            Dictionary with processing statistics:
            - processed: Total listings processed
            - opportunities_created: Valid opportunities saved
            - no_fipe_price: Listings without FIPE price
            - below_threshold: Listings below discount threshold
            - suspicious: Listings flagged as suspicious (>50% discount)
            - errors: Listings that failed processing

        Raises:
            Exception: If critical pipeline component fails
        """
        stats = {
            "processed": 0,
            "opportunities_created": 0,
            "no_fipe_price": 0,
            "below_threshold": 0,
            "suspicious": 0,
            "errors": 0
        }

        for listing in listings:
            try:
                stats["processed"] += 1


                listing_id = listing_id_generator(listing)


                fipe_result = await self.lookup_fipe_price.execute(
                    brand=listing.brand,
                    model=listing.model,
                    year=listing.year
                )

                if fipe_result is None:

                    stats["no_fipe_price"] += 1
                    logger.warning("No FIPE price found for %s %s %s", listing.brand, listing.model, listing.year)
                    continue

                fipe_price = Price.from_float(fipe_result["price"])


                listing_price = Price.from_float(listing.price)
                comparison_result = self.compare_prices.execute(
                    listing_price=listing_price,
                    fipe_price=fipe_price
                )

                if comparison_result is None:

                    stats["errors"] += 1
                    continue

                discount, status = comparison_result


                if status == "below_threshold":

                    stats["below_threshold"] += 1
                    continue
                elif status == "overpriced":

                    stats["below_threshold"] += 1
                    continue


                score = self.calculate_score.execute(
                    discount=discount,
                    condition=listing.condition,
                    mileage=listing.mileage,
                    brand=listing.brand,
                    model=listing.model,
                    created_at=listing.scraped_at
                )


                opportunity_status = "suspicious" if status == "suspicious" else "active"

                opportunity = self.create_opportunity.execute(
                    listing=listing,
                    listing_id=listing_id,
                    fipe_price=fipe_price,
                    discount=discount,
                    score=score,
                    status=opportunity_status
                )


                if opportunity_status == "suspicious":
                    stats["suspicious"] += 1
                else:
                    stats["opportunities_created"] += 1

                logger.info("Created opportunity: %s %s %s - Score: %s", listing.brand, listing.model, listing.year, score.value)

            except Exception as e:

                logger.error("Error processing listing %s: %s", listing.url, e)
                stats["errors"] += 1
                continue

        return stats
