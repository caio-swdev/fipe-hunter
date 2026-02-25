"""
Use Case: Create Opportunity

Create a new opportunity from a listing and price comparison.
"""
from datetime import datetime
from typing import Callable
from fipe_business.domain.entities import Listing, Opportunity
from fipe_business.application.ports import IOpportunityRepository
from fipe_business.domain.value_objects import Price, Discount, Score


class CreateOpportunityUseCase:
    """Create a new opportunity from listing and analysis."""

    def __init__(
        self,
        opportunity_repository: IOpportunityRepository,
        id_generator: Callable[[], str]
    ):
        self.opportunity_repository = opportunity_repository
        self.id_generator = id_generator

    def execute(
        self,
        listing: Listing,
        listing_id: str,
        fipe_price: Price,
        discount: Discount,
        score: Score,
        status: str = "active",
        image_url: str | None = None,
    ) -> Opportunity:
        """
        Create and persist a new opportunity.

        Args:
            listing: The vehicle listing
            listing_id: ID of the listing
            fipe_price: FIPE reference price
            discount: Calculated discount
            score: Calculated opportunity score
            status: Initial status ("active" or "suspicious")
            image_url: Optional scraper-provided image URL (infra-level, not a domain field)

        Returns:
            Created opportunity
        """
        now = datetime.utcnow()

        opportunity = Opportunity(
            listing_id=listing_id,
            brand=listing.brand,
            model=listing.model,
            year=listing.year,
            listing_price=Price.from_float(listing.price),
            fipe_price=fipe_price,
            discount=discount,
            score=score,
            marketplace=listing.marketplace,
            listing_url=listing.url,
            condition=listing.condition,
            mileage=listing.mileage,
            status=status,
            created_at=now,
            updated_at=now
        )

        # Attach image_url as an out-of-band attribute so the repo can persist it
        # without polluting the domain entity's type signature
        if image_url is not None:
            object.__setattr__(opportunity, 'image_url', image_url)

        self.opportunity_repository.save(opportunity)

        return opportunity
