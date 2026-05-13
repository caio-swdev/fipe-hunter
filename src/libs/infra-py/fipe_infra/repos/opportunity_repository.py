"""
SQLAlchemy-based implementation of IOpportunityRepository.

Handles persistence of Opportunity entities using SQLAlchemy ORM.
Manages mapping between domain entities and database models.
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from fipe_business.domain.entities.opportunity import Opportunity
from fipe_business.application.ports.opportunity_repository import IOpportunityRepository
from fipe_business.domain.value_objects.price import Price
from fipe_business.domain.value_objects.discount import Discount
from fipe_business.domain.value_objects.score import Score, ScoreComponents
from fipe_infra.database.models import OpportunityModel


class SQLAlchemyOpportunityRepository(IOpportunityRepository):
    """SQLAlchemy implementation of opportunity repository."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def save(self, opportunity: Opportunity) -> None:
        """Save an opportunity to the repository.

        Converts Opportunity entity to OpportunityModel, extracting scalar
        values from value objects for storage.
        """

        existing = self.session.query(OpportunityModel).filter_by(
            listing_id=opportunity.listing_id
        ).first()

        image_url = getattr(opportunity, 'image_url', None)

        if existing:

            existing.brand = opportunity.brand
            existing.model = opportunity.model
            existing.year = opportunity.year
            existing.listing_price = opportunity.listing_price.to_float()
            existing.fipe_price = opportunity.fipe_price.to_float()
            existing.discount_percentage = float(opportunity.discount.percentage)
            existing.discount_amount = opportunity.discount.amount.to_float()
            existing.score_value = opportunity.score.value
            existing.marketplace = opportunity.marketplace
            existing.listing_url = opportunity.listing_url
            existing.condition = opportunity.condition
            existing.mileage = opportunity.mileage
            existing.status = opportunity.status
            existing.image_url = image_url
            existing.updated_at = opportunity.updated_at
        else:

            model = OpportunityModel(
                listing_id=opportunity.listing_id,
                brand=opportunity.brand,
                model=opportunity.model,
                year=opportunity.year,
                listing_price=opportunity.listing_price.to_float(),
                fipe_price=opportunity.fipe_price.to_float(),
                discount_percentage=float(opportunity.discount.percentage),
                discount_amount=opportunity.discount.amount.to_float(),
                score_value=opportunity.score.value,
                marketplace=opportunity.marketplace,
                listing_url=opportunity.listing_url,
                condition=opportunity.condition,
                mileage=opportunity.mileage,
                status=opportunity.status,
                image_url=image_url,
                created_at=opportunity.created_at,
                updated_at=opportunity.updated_at
            )
            self.session.add(model)

        self.session.commit()

    def find_by_id(self, opportunity_id: str) -> Optional[Opportunity]:
        """Find an opportunity by ID (listing_id).

        Reconstructs the Opportunity entity with value objects from the database model.
        """
        model = self.session.query(OpportunityModel).filter_by(
            listing_id=opportunity_id
        ).first()

        if not model:
            return None

        return self._model_to_entity(model)

    def find_by_listing_id(self, listing_id: str) -> Optional[Opportunity]:
        """Find an opportunity by listing ID.

        Reconstructs the Opportunity entity with value objects from the database model.
        """
        return self.find_by_id(listing_id)

    def find_active(self, min_score: int = 0, limit: int = 100) -> List[Opportunity]:
        """Find active opportunities with score >= min_score, sorted by score descending.

        Returns only opportunities with status='active' and score >= min_score,
        ordered by score in descending order.
        """
        models = self.session.query(OpportunityModel).filter(
            OpportunityModel.status == "active",
            OpportunityModel.score_value >= min_score
        ).order_by(
            OpportunityModel.score_value.desc()
        ).limit(limit).all()

        return [self._model_to_entity(model) for model in models]

    def find_by_status(self, status: str, limit: int = 100) -> List[Opportunity]:
        """Find opportunities by status.

        Returns opportunities filtered by the given status, up to limit.
        """
        models = self.session.query(OpportunityModel).filter_by(
            status=status
        ).limit(limit).all()

        return [self._model_to_entity(model) for model in models]

    def count_by_status(self, status: str) -> int:
        """Count opportunities by status."""
        count = self.session.query(OpportunityModel).filter_by(
            status=status
        ).count()

        return count

    def update_status(self, opportunity_id: str, new_status: str) -> None:
        """Update opportunity status by listing_id."""
        model = self.session.query(OpportunityModel).filter_by(
            listing_id=opportunity_id
        ).first()

        if model:
            model.status = new_status
            self.session.commit()

    def _model_to_entity(self, model: OpportunityModel) -> Opportunity:
        """Convert OpportunityModel to Opportunity entity.

        Reconstructs value objects from scalar database values.
        """

        listing_price = Price.from_float(model.listing_price)
        fipe_price = Price.from_float(model.fipe_price)


        discount_amount_price = Price(amount=Decimal(str(model.discount_amount)))
        discount = Discount(
            percentage=Decimal(str(model.discount_percentage)),
            amount=discount_amount_price
        )


        score_components = ScoreComponents(
            discount_score=0,
            condition_score=0,
            demand_score=0,
            recency_score=0
        )
        score = Score(value=model.score_value, components=score_components)


        opp = Opportunity(
            listing_id=model.listing_id,
            brand=model.brand,
            model=model.model,
            year=model.year,
            listing_price=listing_price,
            fipe_price=fipe_price,
            discount=discount,
            score=score,
            marketplace=model.marketplace,
            listing_url=model.listing_url,
            condition=model.condition,
            mileage=model.mileage,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

        object.__setattr__(opp, 'image_url', getattr(model, 'image_url', None))
        return opp
