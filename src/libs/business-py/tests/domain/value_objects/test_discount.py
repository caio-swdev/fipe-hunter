"""Unit tests for Discount value object."""
import pytest
from decimal import Decimal
from fipe_business.domain.value_objects import Price, Discount


def test_discount_calculation():
    """Test discount calculation from prices."""
    listing_price = Price.from_float(20000.0)
    fipe_price = Price.from_float(25000.0)

    discount = Discount.calculate(listing_price, fipe_price)

    assert discount.percentage == Decimal('20.00')
    assert discount.amount.amount == Decimal('5000.00')


def test_discount_calculation_zero():
    """Test discount calculation with equal prices."""
    listing_price = Price.from_float(25000.0)
    fipe_price = Price.from_float(25000.0)

    discount = Discount.calculate(listing_price, fipe_price)

    assert discount.percentage == Decimal('0.00')
    assert discount.amount.amount == Decimal('0.00')


def test_discount_calculation_negative():
    """Test discount calculation when listing > FIPE (overpriced)."""
    listing_price = Price.from_float(28000.0)
    fipe_price = Price.from_float(25000.0)

    discount = Discount.calculate(listing_price, fipe_price)


    assert discount.percentage < 0

    assert discount.amount.amount < 0


def test_discount_is_opportunity():
    """Test if discount meets opportunity threshold."""
    listing_price = Price.from_float(20000.0)
    fipe_price = Price.from_float(25000.0)
    discount = Discount.calculate(listing_price, fipe_price)

    assert discount.is_opportunity(min_threshold=Decimal('20.00')) is True
    assert discount.is_opportunity(min_threshold=Decimal('25.00')) is False


def test_discount_is_suspicious():
    """Test if discount is suspicious (too high)."""
    listing_price = Price.from_float(10000.0)
    fipe_price = Price.from_float(25000.0)
    discount = Discount.calculate(listing_price, fipe_price)

    assert discount.is_suspicious(max_threshold=Decimal('50.00')) is True


def test_discount_is_in_range():
    """Test if discount is in valid range."""
    listing_price = Price.from_float(18750.0)
    fipe_price = Price.from_float(25000.0)
    discount = Discount.calculate(listing_price, fipe_price)

    assert discount.is_in_range(
        min_threshold=Decimal('20.00'),
        max_threshold=Decimal('50.00')
    ) is True


def test_discount_rejects_zero_reference_price():
    """Test that discount calculation rejects zero FIPE price."""
    listing_price = Price.from_float(20000.0)
    fipe_price = Price(amount=Decimal('0.00'))

    with pytest.raises(ValueError, match="Reference price cannot be zero"):
        Discount.calculate(listing_price, fipe_price)


def test_discount_high_precision():
    """Test discount calculation with high precision."""
    listing_price = Price.from_float(19999.0)
    fipe_price = Price.from_float(25000.0)
    discount = Discount.calculate(listing_price, fipe_price)


    assert discount.percentage == Decimal('20.00')
