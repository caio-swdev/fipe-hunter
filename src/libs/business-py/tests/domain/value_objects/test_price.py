"""Unit tests for Price value object."""
import pytest
from decimal import Decimal
from fipe_business.domain.value_objects import Price


def test_price_creation_from_decimal():
    """Test creating price from Decimal."""
    price = Price(amount=Decimal('25000.00'))
    assert price.amount == Decimal('25000.00')


def test_price_creation_from_float():
    """Test creating price from float."""
    price = Price.from_float(25000.50)
    assert price.amount == Decimal('25000.50')


def test_price_creation_from_string():
    """Test creating price from string."""
    price = Price.from_string("25000.00")
    assert price.amount == Decimal('25000.00')


def test_price_creation_from_brazilian_format():
    """Test creating price from Brazilian format."""
    price = Price.from_string("R$ 25.000,00")
    assert price.amount == Decimal('25000.00')


def test_price_rejects_negative():
    """Test that price rejects negative values."""
    with pytest.raises(ValueError, match="Price cannot be negative"):
        Price.from_float(-1000.0)


def test_price_rounds_to_two_decimal_places():
    """Test that price rounds to 2 decimal places."""
    price = Price(amount=Decimal('25000.999'))
    assert price.amount == Decimal('25001.00')


def test_price_comparison():
    """Test price comparison operators."""
    price1 = Price.from_float(20000.0)
    price2 = Price.from_float(25000.0)
    price3 = Price.from_float(20000.0)

    assert price1 < price2
    assert price2 > price1
    assert price1 == price3
    assert price1 != price2


def test_price_subtraction():
    """Test price subtraction."""
    price1 = Price.from_float(25000.0)
    price2 = Price.from_float(20000.0)
    result = price1 - price2
    assert result.amount == Decimal('5000.00')


def test_price_addition():
    """Test price addition."""
    price1 = Price.from_float(20000.0)
    price2 = Price.from_float(5000.0)
    result = price1 + price2
    assert result.amount == Decimal('25000.00')


def test_price_string_formatting():
    """Test price string formatting."""
    price = Price.from_float(25000.00)
    assert "R$" in str(price)
    assert "25.000,00" in str(price)
