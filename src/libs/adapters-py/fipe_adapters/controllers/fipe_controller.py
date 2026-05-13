"""
FIPEController - FastAPI Controller for FIPE Lookup Operations

Orchestrates use cases for FIPE price lookups via HTTP endpoints.
"""
from typing import Dict, Any, Optional
from fipe_business.domain.value_objects.price import Price
from fipe_business.application.use_cases.lookup_fipe_price import LookupFIPEPriceUseCase


class FIPEController:
    """Controller for FIPE lookup operations."""

    def __init__(self, lookup_use_case: LookupFIPEPriceUseCase):
        """
        Initialize controller with use case dependency.

        Args:
            lookup_use_case: LookupFIPEPriceUseCase instance
        """
        self.lookup_use_case = lookup_use_case

    async def lookup(self, brand: str, model: str, year: int) -> Dict[str, Any]:
        """
        Look up FIPE price for a vehicle.

        Args:
            brand: Vehicle brand name
            model: Vehicle model name
            year: Vehicle year

        Returns:
            Response dictionary with status and price data or not_found

        Raises:
            ValueError: If validation fails
        """

        self._validate_inputs(brand, model, year)

        brand = brand.strip()
        model = model.strip()


        result = await self.lookup_use_case.execute(
            brand=brand,
            model=model,
            year=year
        )


        if result is None:
            return {
                "status": "not_found",
                "message": "Vehicle not found in FIPE database",
                "data": {
                    "brand": brand,
                    "model": model,
                    "year": year
                }
            }


        price = result["price"]
        fipe_code = result["fipe_code"]
        reference_month = result["reference_month"]


        return {
            "status": "success",
            "data": {
                "brand": brand,
                "model": model,
                "year": year,
                "fipe_code": fipe_code,
                "fipe_price": price.to_float(),
                "currency": "BRL",
                "reference_month": reference_month
            }
        }

    def _validate_inputs(self, brand: str, model: str, year: int) -> None:
        """
        Validate input parameters.

        Args:
            brand: Vehicle brand name
            model: Vehicle model name
            year: Vehicle year

        Raises:
            ValueError: If validation fails
        """

        if not brand or not brand.strip():
            raise ValueError("Brand is required")

        if len(brand.strip()) < 2:
            raise ValueError("Brand must be at least 2 characters")


        if not model or not model.strip():
            raise ValueError("Model is required")

        if len(model.strip()) < 2:
            raise ValueError("Model must be at least 2 characters")


        if not isinstance(year, int):
            raise ValueError("Year must be an integer")

        if year < 1950 or year > 2026:
            raise ValueError("Year must be between 1950 and 2026")
