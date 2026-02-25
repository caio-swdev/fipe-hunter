"""
Domain Port: CarWizard Service Interface

Defines the contract for CarWizard system integration.
"""
from typing import Protocol, Optional
from fipe_business.domain.entities import Opportunity


class ICarWizardService(Protocol):
    """Interface for CarWizard API client."""

    def send_opportunity(self, opportunity: Opportunity) -> bool:
        """
        Send qualified opportunity to CarWizard system.

        Args:
            opportunity: The opportunity to send

        Returns:
            True if sent successfully, False otherwise
        """
        ...

    def get_vehicle_history(self, brand: str, model: str, year: int) -> Optional[dict]:
        """
        Get vehicle history from CarWizard.

        Returns:
            Vehicle history data or None if not available
        """
        ...
