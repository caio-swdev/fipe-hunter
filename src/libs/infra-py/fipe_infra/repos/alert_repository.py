"""
SQLAlchemy-based implementation of IAlertRepository.

Handles persistence of Alert entities using SQLAlchemy ORM.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fipe_business.domain.entities.alert import Alert
from fipe_infra.database.models import AlertModel


class SQLAlchemyAlertRepository:
    """SQLAlchemy implementation of alert repository."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    def save(self, alert: Alert) -> None:
        """Save an alert to the database.

        Converts Alert entity to AlertModel, adds to session, and commits.

        Args:
            alert: Alert entity to save.
        """
        model = AlertModel(
            alert_id=alert.alert_id,
            opportunity_id=alert.opportunity_id,
            recipient_id=alert.recipient_id,
            channel=alert.channel,
            message=alert.message,
            status=alert.status,
            sent_at=alert.sent_at,
            delivered_at=alert.delivered_at,
            error_message=alert.error_message,
            retry_count=alert.retry_count,
            created_at=alert.created_at,
        )
        self.session.add(model)
        self.session.commit()

    def find_by_id(self, alert_id: str) -> Optional[Alert]:
        """Find an alert by ID.

        Args:
            alert_id: The alert ID to search for.

        Returns:
            Alert entity if found, None otherwise.
        """
        model = self.session.query(AlertModel).filter(
            AlertModel.alert_id == alert_id
        ).first()

        if model is None:
            return None

        return self._model_to_entity(model)

    def find_pending(self, limit: int = 100) -> List[Alert]:
        """Find pending alerts.

        Args:
            limit: Maximum number of alerts to return.

        Returns:
            List of pending Alert entities.
        """
        models = self.session.query(AlertModel).filter(
            AlertModel.status == "pending"
        ).limit(limit).all()

        return [self._model_to_entity(model) for model in models]

    def find_by_opportunity_id(self, opportunity_id: str) -> List[Alert]:
        """Find all alerts for a specific opportunity.

        Args:
            opportunity_id: The opportunity ID to search for.

        Returns:
            List of Alert entities for the given opportunity.
        """
        models = self.session.query(AlertModel).filter(
            AlertModel.opportunity_id == opportunity_id
        ).all()

        return [self._model_to_entity(model) for model in models]

    def update_status(self, alert_id: str, new_status: str) -> None:
        """Update alert status by ID.

        Args:
            alert_id: The alert ID to update.
            new_status: The new status value.
        """
        self.session.query(AlertModel).filter(
            AlertModel.alert_id == alert_id
        ).update({"status": new_status})
        self.session.commit()

    def count_by_status(self, status: str) -> int:
        """Count alerts by status.

        Args:
            status: The status to count.

        Returns:
            Number of alerts with the given status.
        """
        return self.session.query(AlertModel).filter(
            AlertModel.status == status
        ).count()

    def _model_to_entity(self, model: AlertModel) -> Alert:
        """Convert AlertModel to Alert entity.

        Args:
            model: SQLAlchemy AlertModel instance.

        Returns:
            Alert domain entity.
        """
        return Alert(
            alert_id=model.alert_id,
            opportunity_id=model.opportunity_id,
            recipient_id=model.recipient_id,
            channel=model.channel,
            message=model.message,
            status=model.status,
            sent_at=model.sent_at,
            delivered_at=model.delivered_at,
            error_message=model.error_message,
            retry_count=model.retry_count,
            created_at=model.created_at,
        )
