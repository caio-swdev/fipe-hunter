"""
Application Use Cases

Application-agnostic business use cases following Clean Architecture.
"""
from .lookup_fipe_price import LookupFIPEPriceUseCase
from .compare_prices import ComparePricesUseCase
from .calculate_opportunity_score import CalculateOpportunityScoreUseCase
from .create_opportunity import CreateOpportunityUseCase
from .scrape_listings import ScrapeListingsUseCase
from .process_new_listings import ProcessNewListingsUseCase

__all__ = [
    "LookupFIPEPriceUseCase",
    "ComparePricesUseCase",
    "CalculateOpportunityScoreUseCase",
    "CreateOpportunityUseCase",
    "ScrapeListingsUseCase",
    "ProcessNewListingsUseCase",
]
