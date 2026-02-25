"""
Use Case: Compare Prices

Compare marketplace listing prices against FIPE reference prices.
"""
from decimal import Decimal
from typing import Optional
from fipe_business.domain.services import PriceComparisonService
from fipe_business.domain.value_objects import Price, Discount


class ComparePricesUseCase:
    """Compare listing price against FIPE reference price."""

    def __init__(
        self,
        min_threshold: Decimal = Decimal('20.00'),
        max_threshold: Decimal = Decimal('50.00')
    ):
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold

    def execute(
        self,
        listing_price: Price,
        fipe_price: Optional[Price]
    ) -> Optional[tuple[Discount, str]]:
        """
        Compare prices and determine opportunity status.

        Returns:
            Optional[tuple[Discount, str]]: (discount, status) or None if no FIPE price
                status: "opportunity" | "suspicious" | "below_threshold" | "overpriced"
        """
        if fipe_price is None:
            # Cannot compare without FIPE reference price
            return None

        discount, status = PriceComparisonService.compare_prices(
            listing_price=listing_price,
            fipe_price=fipe_price,
            min_threshold=self.min_threshold,
            max_threshold=self.max_threshold
        )

        return discount, status

    def is_valid_opportunity(
        self,
        listing_price: Price,
        fipe_price: Optional[Price]
    ) -> bool:
        """Check if comparison represents a valid opportunity."""
        if fipe_price is None:
            return False

        result = self.execute(listing_price, fipe_price)
        if result is None:
            return False

        _, status = result
        return status == "opportunity"
