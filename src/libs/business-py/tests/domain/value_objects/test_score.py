"""Unit tests for Score and ScoreComponents value objects."""
import pytest
from decimal import Decimal
from fipe_business.domain.value_objects import Score, ScoreComponents


def test_score_components_creation():
    """Test creating score components."""
    components = ScoreComponents(
        discount_score=80,
        condition_score=75,
        demand_score=85,
        recency_score=100
    )

    assert components.discount_score == 80
    assert components.condition_score == 75
    assert components.demand_score == 85
    assert components.recency_score == 100


def test_score_components_rejects_out_of_range():
    """Test that score components reject out-of-range values."""
    with pytest.raises(ValueError, match="must be between 0-100"):
        ScoreComponents(
            discount_score=150,  # Invalid
            condition_score=75,
            demand_score=85,
            recency_score=100
        )


def test_score_components_calculate_weighted_score():
    """Test weighted score calculation."""
    components = ScoreComponents(
        discount_score=80,
        condition_score=75,
        demand_score=85,
        recency_score=100
    )

    # (80 * 0.40) + (75 * 0.30) + (85 * 0.20) + (100 * 0.10)
    # = 32 + 22.5 + 17 + 10 = 81.5 -> 82
    weighted_score = components.calculate_weighted_score()
    assert weighted_score == 82


def test_score_creation_from_components():
    """Test creating score from components."""
    components = ScoreComponents(
        discount_score=80,
        condition_score=75,
        demand_score=85,
        recency_score=100
    )

    score = Score.from_components(components)
    assert score.value == 82
    assert score.components == components


def test_score_rejects_out_of_range():
    """Test that score rejects out-of-range values."""
    components = ScoreComponents(
        discount_score=80,
        condition_score=75,
        demand_score=85,
        recency_score=100
    )

    with pytest.raises(ValueError, match="Score must be between 0-100"):
        Score(value=150, components=components)


def test_score_is_high_priority():
    """Test high priority threshold check."""
    components = ScoreComponents(
        discount_score=100,
        condition_score=95,
        demand_score=85,
        recency_score=100
    )
    score = Score.from_components(components)  # This will be 96

    assert score.is_high_priority(threshold=75) is True
    assert score.is_high_priority(threshold=97) is False


def test_score_comparison():
    """Test score comparison operators."""
    components1 = ScoreComponents(
        discount_score=80,
        condition_score=75,
        demand_score=85,
        recency_score=100
    )
    components2 = ScoreComponents(
        discount_score=100,
        condition_score=95,
        demand_score=85,
        recency_score=100
    )

    score1 = Score.from_components(components1)
    score2 = Score.from_components(components2)

    assert score1 < score2
    assert score2 > score1
    assert score1 != score2


def test_weighted_score_low_discount():
    """Test weighted score with low discount."""
    components = ScoreComponents(
        discount_score=0,
        condition_score=50,
        demand_score=70,
        recency_score=20
    )

    # (0 * 0.40) + (50 * 0.30) + (70 * 0.20) + (20 * 0.10)
    # = 0 + 15 + 14 + 2 = 31
    weighted_score = components.calculate_weighted_score()
    assert weighted_score == 31
