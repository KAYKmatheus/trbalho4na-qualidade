"""Persistence for simulated, in-process notifications."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Notification


class NotificationService:
    """Adds notification records without contacting external providers."""

    @staticmethod
    def record(
        session: Session,
        *,
        user_id: str,
        reservation_id: str,
        event: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            reservation_id=reservation_id,
            event=event,
            subject=f"Reserva {event.lower()}",
            message=message,
            status="ENVIADA",
        )
        session.add(notification)
        return notification
