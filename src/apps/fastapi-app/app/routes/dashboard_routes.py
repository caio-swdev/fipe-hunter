"""
Dashboard API Routes

Provides real opportunity data from database for frontend dashboard.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fipe_adapters.controllers.opportunity_controller import OpportunityController
from fipe_infra.repos.opportunity_repository import SQLAlchemyOpportunityRepository
from fipe_infra.database.session import get_db_session

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_opportunity_controller(session: Session = Depends(get_db_session)) -> OpportunityController:
    """
    Dependency injection for OpportunityController.

    Args:
        session: Database session from dependency

    Returns:
        OpportunityController instance
    """
    repository = SQLAlchemyOpportunityRepository(session)
    return OpportunityController(repository)

# Now using real database data via OpportunityController


@router.get("/summary")
def get_dashboard_summary(
    controller: OpportunityController = Depends(get_opportunity_controller)
):
    """Get dashboard summary statistics."""
    return controller.get_summary()


@router.get("/opportunities")
def get_opportunities(
    limit: int = 20,
    offset: int = 0,
    controller: OpportunityController = Depends(get_opportunity_controller)
):
    """Get list of opportunities from database."""
    return controller.list_opportunities(limit=limit, offset=offset)
