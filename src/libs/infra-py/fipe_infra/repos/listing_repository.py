"""
SQLAlchemy Implementation of Listing Repository

Implements IListingRepository interface for persistent listing storage.
"""
from sqlalchemy.orm import Session
from fipe_business.domain.entities.listing import Listing
from fipe_infra.database.models import ListingModel


class SQLAlchemyListingRepository:
    """SQLAlchemy-based implementation of listing repository."""

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy Session instance
        """
        self.session = session

    def save(self, listing: Listing) -> None:
        """
        Save a listing to the database.

        Args:
            listing: Listing entity to persist

        Raises:
            IntegrityError: If URL already exists (unique constraint violation)
        """
        model = ListingModel(
            brand=listing.brand,
            model=listing.model,
            year=listing.year,
            price=listing.price,
            mileage=listing.mileage,
            condition=listing.condition,
            url=listing.url,
            marketplace=listing.marketplace,
            scraped_at=listing.scraped_at,
        )
        self.session.add(model)
        self.session.commit()

    def find_by_url(self, url: str) -> Listing | None:
        """
        Find a listing by its URL.

        Args:
            url: The listing URL to search for

        Returns:
            Listing entity if found, None otherwise
        """
        model = self.session.query(ListingModel).filter(
            ListingModel.url == url
        ).first()

        if model is None:
            return None

        return Listing(
            brand=model.brand,
            model=model.model,
            year=model.year,
            price=model.price,
            mileage=model.mileage,
            condition=model.condition,
            url=model.url,
            marketplace=model.marketplace,
            scraped_at=model.scraped_at,
        )

    def count_by_marketplace(self, marketplace: str) -> int:
        """
        Count listings from a specific marketplace.

        Args:
            marketplace: The marketplace name to filter by

        Returns:
            Count of listings from the specified marketplace
        """
        return self.session.query(ListingModel).filter(
            ListingModel.marketplace == marketplace
        ).count()

    def list_all(self, limit: int = 10, offset: int = 0) -> list[Listing]:
        """
        List all listings with pagination.

        Args:
            limit: Maximum number of listings to return
            offset: Number of listings to skip

        Returns:
            List of Listing entities
        """
        models = self.session.query(ListingModel).limit(limit).offset(offset).all()

        return [
            Listing(
                brand=model.brand,
                model=model.model,
                year=model.year,
                price=model.price,
                mileage=model.mileage,
                condition=model.condition,
                url=model.url,
                marketplace=model.marketplace,
                scraped_at=model.scraped_at,
            )
            for model in models
        ]

    def count_all(self) -> int:
        """
        Count total number of listings.

        Returns:
            Total count of all listings
        """
        return self.session.query(ListingModel).count()

    def delete_by_url(self, url: str) -> bool:
        """
        Delete a listing by its URL.

        Args:
            url: The listing URL to delete

        Returns:
            True if deleted, False if not found
        """
        result = self.session.query(ListingModel).filter(
            ListingModel.url == url
        ).delete()
        self.session.commit()
        return result > 0

    def update(self, listing: Listing) -> None:
        """
        Update an existing listing.

        Args:
            listing: Listing entity with updated values

        Raises:
            ValueError: If listing with URL not found
        """
        model = self.session.query(ListingModel).filter(
            ListingModel.url == listing.url
        ).first()

        if model is None:
            raise ValueError(f"Listing with URL {listing.url} not found")

        model.brand = listing.brand
        model.model = listing.model
        model.year = listing.year
        model.price = listing.price
        model.mileage = listing.mileage
        model.condition = listing.condition
        model.marketplace = listing.marketplace
        model.scraped_at = listing.scraped_at

        self.session.commit()
