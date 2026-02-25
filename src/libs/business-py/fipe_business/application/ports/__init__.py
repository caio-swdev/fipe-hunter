"""
Application Ports (Interfaces)

Defines contracts for external dependencies following Dependency Inversion Principle.
"""
from .listing_repository import IListingRepository
from .opportunity_repository import IOpportunityRepository
from .cache_repository import ICacheRepository
from .alert_repository import IAlertRepository
from .fipe_client import IFIPEClient
from .scraper import IScraper
from .alert_service import IAlertService
from .sheets_service import ISheetsService
from .carwizard_service import ICarWizardService

__all__ = [
    "IListingRepository",
    "IOpportunityRepository",
    "ICacheRepository",
    "IAlertRepository",
    "IFIPEClient",
    "IScraper",
    "IAlertService",
    "ISheetsService",
    "ICarWizardService",
]
