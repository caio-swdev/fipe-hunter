"""
SQLAlchemy-based implementation of IFavoriteRepository.

Handles add/remove/list of favorited opportunities per anonymous session.
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from fipe_infra.database.models import FavoriteModel


class SQLAlchemyFavoriteRepository:
    """SQLAlchemy implementation of favorite repository."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, session_id: str, opportunity_id: str) -> None:
        """Add opportunity to favorites. Silently ignores duplicate (race-safe)."""
        try:
            fav = FavoriteModel(session_id=session_id, opportunity_id=opportunity_id)
            self.session.add(fav)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

    def remove(self, session_id: str, opportunity_id: str) -> None:
        """Remove opportunity from favorites."""
        self.session.query(FavoriteModel).filter_by(
            session_id=session_id,
            opportunity_id=opportunity_id
        ).delete()
        self.session.commit()

    def list_opportunity_ids(self, session_id: str) -> List[str]:
        """Return all favorited opportunity IDs for a session."""
        rows = self.session.query(FavoriteModel.opportunity_id).filter_by(
            session_id=session_id
        ).all()
        return [row.opportunity_id for row in rows]
