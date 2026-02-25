"""
Domain Port: Sheets Service Interface

Defines the contract for Google Sheets integration.
"""
from typing import Protocol
from fipe_business.domain.entities import Opportunity


class ISheetsService(Protocol):
    """Interface for Google Sheets service."""

    def log_opportunity(self, opportunity: Opportunity) -> bool:
        """
        Log opportunity to Google Sheets.

        Args:
            opportunity: The opportunity to log

        Returns:
            True if logged successfully, False otherwise
        """
        ...

    def create_sheet_if_not_exists(self, sheet_name: str) -> None:
        """Create a new sheet if it doesn't exist."""
        ...
