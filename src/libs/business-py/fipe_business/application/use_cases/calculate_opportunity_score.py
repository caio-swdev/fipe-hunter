"""
Use Case: Calculate Opportunity Score

Calculate profit potential score for an opportunity.
"""
from datetime import datetime
from fipe_business.domain.services import ScoringService
from fipe_business.domain.value_objects import Discount, Score


class CalculateOpportunityScoreUseCase:
    """Calculate opportunity score based on weighted components."""

    def execute(
        self,
        discount: Discount,
        condition: str,
        mileage: int | None,
        brand: str,
        model: str,
        created_at: datetime
    ) -> Score:
        """
        Calculate opportunity score.

        Components:
        - Discount score (40% weight)
        - Condition score (30% weight)
        - Market demand score (20% weight)
        - Recency score (10% weight)
        """
        return ScoringService.calculate_score(
            discount=discount,
            condition=condition,
            mileage=mileage,
            brand=brand,
            model=model,
            created_at=created_at
        )
