"""
Value Object: Price

Represents a monetary value in BRL (Brazilian Real).
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class Price:
    """Immutable price value in BRL."""

    amount: Decimal

    def __post_init__(self):
        """Validate price data."""
        if not isinstance(self.amount, Decimal):
            raise TypeError("Price amount must be Decimal type")

        # Note: We allow negative amounts for discount calculations
        # but prevent negative prices when created directly

        # Ensure 2 decimal places
        object.__setattr__(
            self,
            'amount',
            self.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )

    @classmethod
    def from_float(cls, value: float) -> "Price":
        """Create price from float value."""
        if value < 0:
            raise ValueError("Price cannot be negative when created from float")
        return cls(amount=Decimal(str(value)))

    @classmethod
    def from_string(cls, value: str) -> "Price":
        """
        Create price from string.

        Supports formats:
        - "25000.00"
        - "R$ 25.000,00"
        - "25.000,00"
        """
        # Remove currency symbol and whitespace
        cleaned = value.replace("R$", "").replace(" ", "").strip()

        # Handle Brazilian format (25.000,00 -> 25000.00)
        if "," in cleaned and "." in cleaned:
            # Brazilian format with both thousand separator and decimal
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            # Only comma (decimal separator)
            cleaned = cleaned.replace(",", ".")

        return cls(amount=Decimal(cleaned))

    def to_float(self) -> float:
        """Convert to float (use sparingly, prefer Decimal)."""
        return float(self.amount)

    def __str__(self) -> str:
        """Format as Brazilian Real."""
        return f"R$ {self.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def __eq__(self, other: object) -> bool:
        """Compare prices."""
        if not isinstance(other, Price):
            return False
        return self.amount == other.amount

    def __lt__(self, other: "Price") -> bool:
        """Less than comparison."""
        return self.amount < other.amount

    def __le__(self, other: "Price") -> bool:
        """Less than or equal comparison."""
        return self.amount <= other.amount

    def __gt__(self, other: "Price") -> bool:
        """Greater than comparison."""
        return self.amount > other.amount

    def __ge__(self, other: "Price") -> bool:
        """Greater than or equal comparison."""
        return self.amount >= other.amount

    def __sub__(self, other: "Price") -> "Price":
        """Subtract prices."""
        return Price(amount=self.amount - other.amount)

    def __add__(self, other: "Price") -> "Price":
        """Add prices."""
        return Price(amount=self.amount + other.amount)
