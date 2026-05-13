"""
Value Object: Discount

Represents a price discount with percentage and amount.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from .price import Price


@dataclass(frozen=True)
class Discount:
    """Immutable discount value."""

    percentage: Decimal
    amount: Price

    def __post_init__(self):
        """Validate discount data."""
        if not isinstance(self.percentage, Decimal):
            raise TypeError("Discount percentage must be Decimal type")

        if not isinstance(self.amount, Price):
            raise TypeError("Discount amount must be Price type")


        object.__setattr__(
            self,
            'percentage',
            self.percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )

    @classmethod
    def calculate(cls, listing_price: Price, reference_price: Price) -> "Discount":
        """
        Calculate discount between listing price and reference price.

        discount_pct = (reference_price - listing_price) / reference_price * 100
        discount_amount = reference_price - listing_price
        """
        if reference_price.amount == 0:
            raise ValueError("Reference price cannot be zero")

        discount_amount = reference_price - listing_price
        discount_pct = (discount_amount.amount / reference_price.amount) * Decimal('100')

        return cls(
            percentage=discount_pct.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            amount=discount_amount
        )

    @classmethod
    def from_prices(cls, listing_price: float, reference_price: float) -> "Discount":
        """
        Create discount from float prices.

        Convenience method that accepts float values and calculates discount.
        """
        listing = Price.from_float(listing_price)
        reference = Price.from_float(reference_price)
        return cls.calculate(listing, reference)

    def is_opportunity(self, min_threshold: Decimal = Decimal('20.00')) -> bool:
        """Check if discount meets minimum opportunity threshold."""
        return self.percentage >= min_threshold

    def is_suspicious(self, max_threshold: Decimal = Decimal('50.00')) -> bool:
        """Check if discount is suspiciously high (potential fraud)."""
        return self.percentage > max_threshold

    def is_in_range(
        self,
        min_threshold: Decimal = Decimal('20.00'),
        max_threshold: Decimal = Decimal('50.00')
    ) -> bool:
        """Check if discount is within acceptable range."""
        return min_threshold <= self.percentage <= max_threshold

    def to_float(self) -> float:
        """Convert percentage to float."""
        return float(self.percentage)

    def __str__(self) -> str:
        """Format discount."""
        return f"{self.percentage}% ({self.amount})"

    def __eq__(self, other: object) -> bool:
        """Compare discounts."""
        if not isinstance(other, Discount):
            return False
        return self.percentage == other.percentage and self.amount == other.amount
