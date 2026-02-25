"""
Favorites API Routes

POST   /api/favorites/{opportunity_id}  — add to favorites
DELETE /api/favorites/{opportunity_id}  — remove from favorites
GET    /api/favorites                   — list favorites for session
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from fipe_adapters.controllers.favorites_controller import FavoritesController
from fipe_infra.repos.favorite_repository import SQLAlchemyFavoriteRepository
from fipe_infra.repos.opportunity_repository import SQLAlchemyOpportunityRepository
from fipe_infra.database.session import get_db_session

router = APIRouter(prefix="/favorites", tags=["favorites"])


def get_favorites_controller(session: Session = Depends(get_db_session)) -> FavoritesController:
    return FavoritesController(
        SQLAlchemyFavoriteRepository(session),
        SQLAlchemyOpportunityRepository(session),
    )


@router.post("/{opportunity_id}")
def add_favorite(
    opportunity_id: str,
    request: Request,
    ctrl: FavoritesController = Depends(get_favorites_controller),
):
    """Add opportunity to session favorites."""
    return ctrl.add_favorite(request.state.session_id, opportunity_id)


@router.delete("/{opportunity_id}")
def remove_favorite(
    opportunity_id: str,
    request: Request,
    ctrl: FavoritesController = Depends(get_favorites_controller),
):
    """Remove opportunity from session favorites."""
    return ctrl.remove_favorite(request.state.session_id, opportunity_id)


@router.get("")
def list_favorites(
    request: Request,
    ctrl: FavoritesController = Depends(get_favorites_controller),
):
    """List all favorited opportunities for the current session."""
    return ctrl.list_favorites(request.state.session_id)
