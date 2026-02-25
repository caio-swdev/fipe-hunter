"""
Value Object: Score and ScoreComponents

Represents opportunity scoring (0-100 scale).
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class ScoreComponents:
    """Individual scoring components with weights."""

    discount_score: int  # 0-100 (40% weight)
    condition_score: int  # 0-100 (30% weight)
    demand_score: int  # 0-100 (20% weight)
    recency_score: int  # 0-100 (10% weight)

    def __post_init__(self):
        """Validate score components."""
        for field_name in ['discount_score', 'condition_score', 'demand_score', 'recency_score']:
            value = getattr(self, field_name)
            if not isinstance(value, int):
                raise TypeError(f"{field_name} must be integer")
            if not 0 <= value <= 100:
                raise ValueError(f"{field_name} must be between 0-100")

    def calculate_weighted_score(
        self,
        discount_weight: Decimal = Decimal('0.40'),
        condition_weight: Decimal = Decimal('0.30'),
        demand_weight: Decimal = Decimal('0.20'),
        recency_weight: Decimal = Decimal('0.10')
    ) -> int:
        """
        Calculate weighted average of score components.

        Default weights:
        - Discount: 40%
        - Condition: 30%
        - Demand: 20%
        - Recency: 10%
        """
        # Validate weights sum to 1.0
        total_weight = discount_weight + condition_weight + demand_weight + recency_weight
        if abs(total_weight - Decimal('1.0')) > Decimal('0.01'):
            raise ValueError("Weights must sum to 1.0")

        weighted_sum = (
            Decimal(self.discount_score) * discount_weight +
            Decimal(self.condition_score) * condition_weight +
            Decimal(self.demand_score) * demand_weight +
            Decimal(self.recency_score) * recency_weight
        )

        # Round to nearest integer
        return int(weighted_sum.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class Score:
    """Immutable opportunity score (0-100)."""

    value: int
    components: ScoreComponents = None  # type: ignore

    def __post_init__(self):
        """Validate score data."""
        if not isinstance(self.value, int):
            raise TypeError("Score value must be integer")

        if not 0 <= self.value <= 100:
            raise ValueError("Score must be between 0-100")

        if self.components is not None and not isinstance(self.components, ScoreComponents):
            raise TypeError("Components must be ScoreComponents type")

    @classmethod
    def from_components(cls, components: ScoreComponents) -> "Score":
        """Create score from components using default weights."""
        value = components.calculate_weighted_score()
        return cls(value=value, components=components)

    def is_high_priority(self, threshold: int = 75) -> bool:
        """Check if score meets high-priority threshold for alerts."""
        return self.value >= threshold

    def __str__(self) -> str:
        """Format score."""
        return f"Score: {self.value}/100"

    def __eq__(self, other: object) -> bool:
        """Compare scores."""
        if not isinstance(other, Score):
            return False
        return self.value == other.value

    def __lt__(self, other: "Score") -> bool:
        """Less than comparison."""
        return self.value < other.value

    def __le__(self, other: "Score") -> bool:
        """Less than or equal comparison."""
        return self.value <= other.value

    def __gt__(self, other: "Score") -> bool:
        """Greater than comparison."""
        return self.value > other.value

    def __ge__(self, other: "Score") -> bool:
        """Greater than or equal comparison."""
        return self.value >= other.value

    def __int__(self) -> int:
        """Convert to int."""
        return self.value
