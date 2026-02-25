"""
Domain Entity: Listing

Represents a scraped vehicle listing from a marketplace.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Listing:
    """Vehicle listing entity."""

    brand: str
    model: str
    year: int
    price: float
    mileage: int | None
    condition: str  # "excellent" | "good" | "fair" | "poor"
    url: str
    marketplace: str  # "olx" | "webmotors"
    scraped_at: datetime
    image_url: str | None = None

    def __post_init__(self):
        """Validate listing data."""
        if not self.brand or len(self.brand) < 2:
            raise ValueError("Brand must be at least 2 characters")

        if not self.model or len(self.model) < 2:
            raise ValueError("Model must be at least 2 characters")

        if self.year < 1950 or self.year > 2026:
            raise ValueError("Year must be between 1950 and 2026")

        if self.price <= 0:
            raise ValueError("Price must be positive")

        if self.condition not in ["excellent", "good", "fair", "poor"]:
            raise ValueError("Invalid condition")

        if not self.url.startswith("http"):
            raise ValueError("URL must be valid HTTP/HTTPS URL")
