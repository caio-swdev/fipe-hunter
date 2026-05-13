"""
Domain Service: Scoring Service

Calculates opportunity scores based on weighted components.
"""
from datetime import datetime
from decimal import Decimal
from ..value_objects import Discount, Score, ScoreComponents


class ScoringService:
    """Service for calculating opportunity scores."""


    CONDITION_SCORES = {
        "excellent": 95,
        "good": 75,
        "fair": 50,
        "poor": 40,
    }


    DEMAND_SCORES = {

        ("volkswagen", "gol"): 85,
        ("fiat", "uno"): 80,
        ("chevrolet", "onix"): 85,
        ("honda", "civic"): 80,
        ("toyota", "corolla"): 82,

        ("ford", "ka"): 70,
        ("renault", "sandero"): 70,

        "default": 70,
    }

    @classmethod
    def calculate_score(
        cls,
        discount: Discount,
        condition: str,
        mileage: int | None,
        brand: str,
        model: str,
        created_at: datetime
    ) -> Score:
        """
        Calculate opportunity score from components.

        Weights:
        - Discount: 40%
        - Condition: 30%
        - Demand: 20%
        - Recency: 10%
        """
        discount_score = cls._calculate_discount_score(discount)
        condition_score = cls._calculate_condition_score(condition, mileage)
        demand_score = cls._calculate_demand_score(brand, model)
        recency_score = cls._calculate_recency_score(created_at)

        components = ScoreComponents(
            discount_score=discount_score,
            condition_score=condition_score,
            demand_score=demand_score,
            recency_score=recency_score
        )

        return Score.from_components(components)

    @classmethod
    def _calculate_discount_score(cls, discount: Discount) -> int:
        """
        Calculate discount score (0-100).

        Mapping:
        - 0% discount → 0
        - 20% discount → 40
        - 50% discount → 100
        - Linear interpolation
        """
        discount_pct = float(discount.percentage)

        if discount_pct <= 0:
            return 0
        elif discount_pct >= 50:
            return 100
        else:

            return int((discount_pct / 50.0) * 100)

    @classmethod
    def _calculate_condition_score(cls, condition: str, mileage: int | None) -> int:
        """
        Calculate condition score (0-100).

        Base scores from condition, then apply mileage penalty.
        """
        base_score = cls.CONDITION_SCORES.get(condition, 50)

        if mileage is None:
            return base_score


        if mileage <= 50000:
            return base_score


        excess_km = mileage - 50000
        penalty_factor = min((excess_km / 50000) * 0.10, 0.30)
        adjusted_score = int(base_score * (1 - penalty_factor))

        return max(adjusted_score, 20)

    @classmethod
    def _calculate_demand_score(cls, brand: str, model: str) -> int:
        """
        Calculate market demand score (0-100).

        Based on brand/model popularity in Rio de Janeiro market.
        """
        lookup_key = (brand.lower().strip(), model.lower().strip())
        return cls.DEMAND_SCORES.get(lookup_key, cls.DEMAND_SCORES["default"])

    @classmethod
    def _calculate_recency_score(cls, created_at: datetime) -> int:
        """
        Calculate recency score (0-100).

        Mapping:
        - Today: 100
        - 1-7 days: 90-60
        - 8-30 days: 59-20
        - >30 days: 20
        """
        now = datetime.utcnow()
        age_days = (now - created_at).days

        if age_days == 0:
            return 100
        elif age_days == 1:
            return 90
        elif 2 <= age_days <= 7:

            return int(90 - ((age_days - 1) / 6) * 30)
        elif 8 <= age_days <= 30:

            return int(59 - ((age_days - 8) / 22) * 39)
        else:
            return 20
