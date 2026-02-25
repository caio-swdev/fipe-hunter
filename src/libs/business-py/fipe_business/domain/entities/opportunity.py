"""
Domain Entity: Opportunity

Represents a qualified vehicle opportunity with discount and score.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..value_objects import Price, Discount, Score


@dataclass
class Opportunity:
    """Qualified vehicle opportunity entity."""

    listing_id: str
    brand: str
    model: str
    year: int
    listing_price: Price
    fipe_price: Price
    discount: Discount
    score: Score
    marketplace: str
    listing_url: str
    condition: str
    mileage: Optional[int]
    status: str  # "active" | "suspicious" | "sold" | "expired"
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        """Validate opportunity data."""
        if not self.listing_id:
            raise ValueError("Listing ID is required")

        if not self.brand or len(self.brand) < 2:
            raise ValueError("Brand must be at least 2 characters")

        if not self.model or len(self.model) < 2:
            raise ValueError("Model must be at least 2 characters")

        if self.year < 1950 or self.year > 2026:
            raise ValueError("Year must be between 1950 and 2026")

        if not isinstance(self.listing_price, Price):
            raise TypeError("Listing price must be Price type")

        if not isinstance(self.fipe_price, Price):
            raise TypeError("FIPE price must be Price type")

        if not isinstance(self.discount, Discount):
            raise TypeError("Discount must be Discount type")

        if not isinstance(self.score, Score):
            raise TypeError("Score must be Score type")

        if self.status not in ["active", "suspicious", "sold", "expired"]:
            raise ValueError("Invalid status")

        if self.condition not in ["excellent", "good", "fair", "poor"]:
            raise ValueError("Invalid condition")

        if not self.listing_url.startswith("http"):
            raise ValueError("URL must be valid HTTP/HTTPS URL")

    def mark_as_suspicious(self) -> None:
        """Mark opportunity as suspicious (high fraud risk)."""
        object.__setattr__(self, 'status', 'suspicious')
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def mark_as_sold(self) -> None:
        """Mark opportunity as sold."""
        object.__setattr__(self, 'status', 'sold')
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def mark_as_expired(self) -> None:
        """Mark opportunity as expired."""
        object.__setattr__(self, 'status', 'expired')
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def is_alert_eligible(self, threshold: int = 75) -> bool:
        """Check if opportunity is eligible for alerts."""
        return self.status == "active" and self.score.is_high_priority(threshold)

    def requires_manual_review(self) -> bool:
        """Check if opportunity requires manual review."""
        return self.status == "suspicious"
