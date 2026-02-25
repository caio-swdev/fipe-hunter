"""
Value Object: MarketplaceType

Represents supported marketplace types.
"""
from enum import Enum


class MarketplaceType(str, Enum):
    """Supported marketplace types."""

    OLX = "olx"
    WEBMOTORS = "webmotors"

    @classmethod
    def from_string(cls, value: str) -> "MarketplaceType":
        """Create MarketplaceType from string."""
        value_lower = value.lower().strip()
        try:
            return cls(value_lower)
        except ValueError:
            raise ValueError(f"Invalid marketplace: {value}. Must be one of: {', '.join([m.value for m in cls])}")

    def __str__(self) -> str:
        """String representation."""
        return self.value
