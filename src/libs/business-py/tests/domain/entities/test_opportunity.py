"""Unit tests for Opportunity entity."""
import pytest
from datetime import datetime
from decimal import Decimal
from fipe_business.domain.entities import Opportunity
from fipe_business.domain.value_objects import Price, Discount, Score, ScoreComponents


def test_opportunity_creation():
    """Test creating opportunity with valid data."""
    listing_price = Price.from_float(20000.0)
    fipe_price = Price.from_float(25000.0)
    discount = Discount.calculate(listing_price, fipe_price)
    components = ScoreComponents(
        discount_score=80,
        condition_score=75,
        demand_score=85,
        recency_score=100
    )
    score = Score.from_components(components)
    now = datetime.utcnow()

    opportunity = Opportunity(
        listing_id="listing-123",
        brand="Volkswagen",
        model="Gol",
        year=2015,
        listing_price=listing_price,
        fipe_price=fipe_price,
        discount=discount,
        score=score,
        marketplace="olx",
        listing_url="https://olx.com.br/listing/123",
        condition="good",
        mileage=80000,
        status="active",
        created_at=now,
        updated_at=now
    )

    assert opportunity.brand == "Volkswagen"
    assert opportunity.status == "active"
    assert opportunity.score.value == 82


def test_opportunity_is_alert_eligible():
    """Test alert eligibility check."""
    listing_price = Price.from_float(20000.0)
    fipe_price = Price.from_float(25000.0)
    discount = Discount.calculate(listing_price, fipe_price)
    components = ScoreComponents(
        discount_score=100,
        condition_score=95,
        demand_score=85,
        recency_score=100
    )
    score = Score.from_components(components)
    now = datetime.utcnow()

    opportunity = Opportunity(
        listing_id="listing-123",
        brand="Volkswagen",
        model="Gol",
        year=2015,
        listing_price=listing_price,
        fipe_price=fipe_price,
        discount=discount,
        score=score,
        marketplace="olx",
        listing_url="https://olx.com.br/listing/123",
        condition="excellent",
        mileage=50000,
        status="active",
        created_at=now,
        updated_at=now
    )

    assert opportunity.is_alert_eligible(threshold=75) is True


def test_opportunity_mark_as_suspicious():
    """Test marking opportunity as suspicious."""
    listing_price = Price.from_float(10000.0)
    fipe_price = Price.from_float(25000.0)
    discount = Discount.calculate(listing_price, fipe_price)
    components = ScoreComponents(
        discount_score=100,
        condition_score=75,
        demand_score=85,
        recency_score=100
    )
    score = Score.from_components(components)
    now = datetime.utcnow()

    opportunity = Opportunity(
        listing_id="listing-123",
        brand="Volkswagen",
        model="Gol",
        year=2015,
        listing_price=listing_price,
        fipe_price=fipe_price,
        discount=discount,
        score=score,
        marketplace="olx",
        listing_url="https://olx.com.br/listing/123",
        condition="good",
        mileage=80000,
        status="active",
        created_at=now,
        updated_at=now
    )

    opportunity.mark_as_suspicious()
    assert opportunity.status == "suspicious"
    assert opportunity.requires_manual_review() is True


def test_opportunity_validation_rejects_invalid_status():
    """Test that opportunity validation rejects invalid status."""
    listing_price = Price.from_float(20000.0)
    fipe_price = Price.from_float(25000.0)
    discount = Discount.calculate(listing_price, fipe_price)
    components = ScoreComponents(
        discount_score=80,
        condition_score=75,
        demand_score=85,
        recency_score=100
    )
    score = Score.from_components(components)
    now = datetime.utcnow()

    with pytest.raises(ValueError, match="Invalid status"):
        Opportunity(
            listing_id="listing-123",
            brand="Volkswagen",
            model="Gol",
            year=2015,
            listing_price=listing_price,
            fipe_price=fipe_price,
            discount=discount,
            score=score,
            marketplace="olx",
            listing_url="https://olx.com.br/listing/123",
            condition="good",
            mileage=80000,
            status="invalid_status",  # Invalid
            created_at=now,
            updated_at=now
        )
