"""
Dependency Injection Factory: SearchController

Wires all infra/use-case dependencies for on-demand vehicle search.
Kept in factories/ so search_routes.py stays free of fipe_infra imports.
"""
import uuid
from sqlalchemy.orm import Session

from fipe_infra.clients.fipe_client import FIPEClient
from fipe_infra.repos.cache_repository import SQLAlchemyCacheRepository
from fipe_infra.repos.catalog_cache_repository import CatalogCacheRepository
from fipe_infra.repos.api_hit_repository import ApiHitRepository
from fipe_infra.repos.search_cache_repository import SearchCacheRepository
from fipe_infra.repos.opportunity_repository import SQLAlchemyOpportunityRepository
from fipe_infra.repos.rate_limit_event_repository import SQLAlchemyRateLimitEventRepository
from fipe_infra.scrapers.curl_olx_scraper import CurlOLXScraper
from fipe_business.application.use_cases.lookup_fipe_price import LookupFIPEPriceUseCase
from fipe_business.application.use_cases.create_opportunity import CreateOpportunityUseCase
from fipe_business.application.use_cases.calculate_opportunity_score import CalculateOpportunityScoreUseCase
from fipe_adapters.controllers.search_controller import SearchController

def get_search_controller(session: Session) -> SearchController:
    """Build SearchController with all dependencies wired for a request."""
    event_repo = SQLAlchemyRateLimitEventRepository(session)
    catalog_cache_repo = CatalogCacheRepository(session)
    api_hit_repo = ApiHitRepository(session)
    fipe_client = FIPEClient(
        base_url="https://parallelum.com.br/fipe/api/v1",
        timeout=10.0,
        event_repo=event_repo,
        catalog_cache_repo=catalog_cache_repo,
        api_hit_repo=api_hit_repo,
    )
    cache_repo = SQLAlchemyCacheRepository(session)
    search_cache_repo = SearchCacheRepository(session)
    opportunity_repo = SQLAlchemyOpportunityRepository(session)

    lookup_use_case = LookupFIPEPriceUseCase(
        fipe_client=fipe_client,
        cache_repository=cache_repo
    )
    score_use_case = CalculateOpportunityScoreUseCase()
    create_use_case = CreateOpportunityUseCase(
        opportunity_repository=opportunity_repo,
        id_generator=lambda: str(uuid.uuid4())
    )

    from fipe_infra.scrapers.webmotors_scraper import WebMotorsScraper
    wm_factory = lambda brand, model, year: WebMotorsScraper(brand=brand, model=model, year=year, event_repo=event_repo, api_hit_repo=api_hit_repo)

    return SearchController(
        lookup_use_case=lookup_use_case,
        score_use_case=score_use_case,
        create_use_case=create_use_case,
        fipe_client=fipe_client,
        olx_scraper_factory=lambda brand, model, year: CurlOLXScraper(brand=brand, model=model, year=year, event_repo=event_repo, api_hit_repo=api_hit_repo),
        webmotors_scraper_factory=wm_factory,
        search_cache_repo=search_cache_repo,
    )
