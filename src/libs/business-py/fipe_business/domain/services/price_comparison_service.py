"""
Domain Service: Price Comparison Service

Compares marketplace prices against FIPE reference prices.
"""
from decimal import Decimal
from ..value_objects import Price, Discount


class PriceComparisonService:
    """Service for comparing prices and identifying opportunities."""

    DEFAULT_MIN_THRESHOLD = Decimal('20.00')  # 20%
    DEFAULT_MAX_THRESHOLD = Decimal('50.00')  # 50%

    @classmethod
    def compare_prices(
        cls,
        listing_price: Price,
        fipe_price: Price,
        min_threshold: Decimal | None = None,
        max_threshold: Decimal | None = None
    ) -> tuple[Discount, str]:
        """
        Compare listing price vs FIPE reference price.

        Returns:
            tuple[Discount, str]: (discount, status)
                status can be:
                - "opportunity": valid opportunity (discount in range)
                - "suspicious": high fraud risk (discount > max_threshold)
                - "below_threshold": discount < min_threshold
                - "overpriced": negative discount (listing > FIPE)
        """
        min_thresh = min_threshold or cls.DEFAULT_MIN_THRESHOLD
        max_thresh = max_threshold or cls.DEFAULT_MAX_THRESHOLD

        # Validate prices
        if fipe_price.amount == 0:
            raise ValueError("FIPE price cannot be zero")

        if listing_price.amount <= 0:
            raise ValueError("Listing price must be positive")

        # Calculate discount
        discount = Discount.calculate(listing_price, fipe_price)

        # Determine status
        if discount.percentage < 0:
            status = "overpriced"
        elif discount.percentage < min_thresh:
            status = "below_threshold"
        elif discount.percentage > max_thresh:
            status = "suspicious"
        else:
            status = "opportunity"

        return discount, status

    @classmethod
    def is_valid_opportunity(
        cls,
        listing_price: Price,
        fipe_price: Price,
        min_threshold: Decimal | None = None,
        max_threshold: Decimal | None = None
    ) -> bool:
        """
        Check if price comparison represents a valid opportunity.

        Valid opportunity:
        - Discount >= min_threshold (default 20%)
        - Discount <= max_threshold (default 50%)
        """
        _, status = cls.compare_prices(listing_price, fipe_price, min_threshold, max_threshold)
        return status == "opportunity"

    @classmethod
    def is_suspicious(
        cls,
        listing_price: Price,
        fipe_price: Price,
        max_threshold: Decimal | None = None
    ) -> bool:
        """
        Check if price comparison is suspicious (potential fraud).

        Suspicious:
        - Discount > max_threshold (default 50%)
        """
        _, status = cls.compare_prices(listing_price, fipe_price, max_threshold=max_threshold)
        return status == "suspicious"
