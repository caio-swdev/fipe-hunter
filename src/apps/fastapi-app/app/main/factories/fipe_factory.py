"""
Dependency Injection Factory: FIPE Controller

Wires together FIPE client, cache repository, use case, and controller.
"""
from fipe_infra.clients.fipe_client import FIPEClient
from fipe_infra.repos.cache_repository import SQLAlchemyCacheRepository
from fipe_infra.repos.catalog_cache_repository import CatalogCacheRepository
from fipe_infra.repos.api_hit_repository import ApiHitRepository
from fipe_infra.repos.rate_limit_event_repository import SQLAlchemyRateLimitEventRepository
from fipe_business.application.use_cases.lookup_fipe_price import LookupFIPEPriceUseCase
from fipe_adapters.controllers.fipe_controller import FIPEController
from fipe_infra.database.session import get_db_session


def make_fipe_controller() -> FIPEController:
    """
    Factory function to create FIPEController with all dependencies.

    Wiring:
    - FIPEClient → HTTP client for FIPE API
    - SQLAlchemyCacheRepository → Cache storage
    - CatalogCacheRepository → Adaptive-TTL catalog cache
    - LookupFIPEPriceUseCase → Domain use case
    - FIPEController → Controller orchestrator

    Returns:
        FIPEController instance with all dependencies wired
    """

    db_session = next(get_db_session())
    event_repo = SQLAlchemyRateLimitEventRepository(db_session)
    catalog_cache_repo = CatalogCacheRepository(db_session)
    api_hit_repo = ApiHitRepository(db_session)


    fipe_client = FIPEClient(
        base_url="https://parallelum.com.br/fipe/api/v1",
        timeout=10.0,
        event_repo=event_repo,
        catalog_cache_repo=catalog_cache_repo,
        api_hit_repo=api_hit_repo,
    )
    cache_repository = SQLAlchemyCacheRepository(db_session)


    lookup_use_case = LookupFIPEPriceUseCase(
        fipe_client=fipe_client,
        cache_repository=cache_repository
    )


    return FIPEController(lookup_use_case=lookup_use_case)
