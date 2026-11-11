"""Availability search based on active reservations and resource blocks."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominio.regras import ACTIVE_RESERVATION_STATUSES
from app.erros import ValidationError
from app.models import ReservationItem, Resource, ResourceBlock
from app.servicos.materiais import MaterialService


class AvailabilityService:
    """Filters the catalog to resources available for a requested interval."""

    def __init__(self, session: Session):
        self.session = session

    def search(
        self,
        *,
        start: datetime,
        end: datetime,
        resource_type: str | None = None,
        capacity: int | None = None,
        location: str | None = None,
        competency: str | None = None,
        quantity: int = 1,
    ) -> list[dict]:
        if start.tzinfo is None or start.utcoffset() is None or end.tzinfo is None or end.utcoffset() is None:
            raise ValidationError("O período deve incluir fuso horário.")
        if start >= end:
            raise ValidationError("O início do período deve ser anterior ao fim.")
        if quantity <= 0:
            raise ValidationError("A quantidade deve ser maior que zero.")

        statement = select(Resource).where(Resource.active.is_(True)).order_by(Resource.name)
        if resource_type:
            statement = statement.where(Resource.resource_type == resource_type)
        if capacity is not None:
            statement = statement.where(Resource.capacity >= capacity)
        if location:
            statement = statement.where(Resource.location.ilike(f"%{location}%"))

        results: list[dict] = []
        for resource in self.session.scalars(statement):
            if competency and not any(
                competency.casefold() in entry.casefold() for entry in (resource.competencies or [])
            ):
                continue
            blocked = self.session.scalar(
                select(ResourceBlock.id)
                .where(
                    ResourceBlock.resource_id == resource.id,
                    ResourceBlock.status == "ATIVO",
                    ResourceBlock.start < end,
                    ResourceBlock.end > start,
                )
                .limit(1)
            )
            if blocked is not None:
                continue

            active_item_query = select(ReservationItem).where(
                ReservationItem.resource_type == resource.resource_type,
                ReservationItem.resource_id == resource.id,
                ReservationItem.status.in_(ACTIVE_RESERVATION_STATUSES),
                ReservationItem.start < end,
                ReservationItem.end > start,
            )
            if resource.resource_type == "material":
                reserved = self.session.scalar(
                    select(func.coalesce(func.sum(ReservationItem.quantity), 0)).where(
                        ReservationItem.resource_type == resource.resource_type,
                        ReservationItem.resource_id == resource.id,
                        ReservationItem.status.in_(ACTIVE_RESERVATION_STATUSES),
                        ReservationItem.start < end,
                        ReservationItem.end > start,
                    )
                )
                outstanding = MaterialService.outstanding_units(self.session, resource.id)
                available_quantity = max(
                    0,
                    (resource.quantity_total or 0) - int(reserved or 0) - outstanding,
                )
                if available_quantity < quantity:
                    continue
            else:
                if self.session.scalar(active_item_query.limit(1)) is not None:
                    continue
                available_quantity = None

            results.append(
                {
                    "id": resource.id,
                    "resource_type": resource.resource_type,
                    "name": resource.name,
                    "category": resource.category,
                    "capacity": resource.capacity,
                    "location": resource.location,
                    "competencies": resource.competencies,
                    "quantity_total": resource.quantity_total,
                    "restricted": resource.restricted,
                    "active": resource.active,
                    "available_quantity": available_quantity,
                }
            )
        return results
