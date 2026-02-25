"""
FavoritesController - Manages favorite opportunities per anonymous session.

Follows the established controller pattern (constructor DI, dict responses).
"""
from typing import Dict, Any

from fipe_business.application.ports.favorite_repository import IFavoriteRepository
from fipe_business.application.ports.opportunity_repository import IOpportunityRepository


class FavoritesController:
    """Controller for favorites CRUD operations."""

    def __init__(
        self,
        favorite_repository: IFavoriteRepository,
        opportunity_repository: IOpportunityRepository,
    ):
        self._favs = favorite_repository
        self._opps = opportunity_repository

    def add_favorite(self, session_id: str, opportunity_id: str) -> Dict[str, Any]:
        """Add an opportunity to the session's favorites."""
        self._favs.add(session_id, opportunity_id)
        return {"status": "added", "opportunity_id": opportunity_id}

    def remove_favorite(self, session_id: str, opportunity_id: str) -> Dict[str, Any]:
        """Remove an opportunity from the session's favorites."""
        self._favs.remove(session_id, opportunity_id)
        return {"status": "removed", "opportunity_id": opportunity_id}

    def list_favorites(self, session_id: str) -> Dict[str, Any]:
        """Return full opportunity records for all session favorites."""
        ids = self._favs.list_opportunity_ids(session_id)

        opportunities = []
        for opp_id in ids:
            opp = self._opps.find_by_id(opp_id)
            if opp is None:
                continue
            opportunities.append({
                "id": opp.listing_id,
                "brand": opp.brand,
                "model": opp.model,
                "year": opp.year,
                "listing_price": float(opp.listing_price.amount),
                "fipe_price": float(opp.fipe_price.amount),
                "discount_percent": float(opp.discount.percentage),
                "score": opp.score.value,
                "mileage_km": opp.mileage or 0,
                "source": opp.marketplace,
                "url": opp.listing_url,
                "image_url": getattr(opp, 'image_url', None),
                "found_at": opp.created_at.isoformat() if opp.created_at else "",
            })

        return {
            "status": "success",
            "data": opportunities,
            "total": len(opportunities),
        }
