"""
Domain Port: FIPE Client Interface

Defines the contract for FIPE API integration.
"""
from typing import Protocol, Optional
from fipe_business.domain.value_objects import Price


class IFIPEClient(Protocol):
    """Interface for FIPE API client."""

    def lookup_price(self, brand: str, model: str, year: int) -> Optional[tuple[Price, str]]:
        """
        Look up FIPE price for a vehicle.

        Returns:
            Optional[tuple[Price, str]]: (price, version) or None if not found
        """
        ...

    def get_table_date(self) -> str:
        """Get current FIPE table reference date."""
        ...
