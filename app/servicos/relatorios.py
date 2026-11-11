"""Utilization and avoided-conflict reporting."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominio.regras import ACTIVE_RESERVATION_STATUSES
from app.erros import ValidationError
from app.models import AuditEntry, ReservationItem, Resource, ResourceScope


class ReportService:
    """Calculates utilization and avoided-conflict totals for a date range."""

    def __init__(self, session: Session):
        self.session = session

    def generate(self, *, start: datetime, end: datetime, user_id: str, role: str) -> dict:
        if start.tzinfo is None or start.utcoffset() is None or end.tzinfo is None or end.utcoffset() is None:
            raise ValidationError("O período do relatório deve incluir fuso horário.")
        if start >= end:
            raise ValidationError("O início do relatório deve ser anterior ao fim.")

        resource_ids: set[str] | None = None
        if role == "RESPONSAVEL":
            resource_ids = set(
                self.session.scalars(
                    select(ResourceScope.resource_id).where(ResourceScope.responsible_id == user_id)
                )
            )

        items = list(
            self.session.scalars(
                select(ReservationItem).where(
                    ReservationItem.status.in_(ACTIVE_RESERVATION_STATUSES),
                    ReservationItem.start < end,
                    ReservationItem.end > start,
                )
            )
        )
        utilization: dict[tuple[str, str], dict[str, int | float | str]] = {}
        for item in items:
            if resource_ids is not None and item.resource_id not in resource_ids:
                continue
            item_start = item.start if item.start.tzinfo else item.start.replace(tzinfo=timezone.utc)
            item_end = item.end if item.end.tzinfo else item.end.replace(tzinfo=timezone.utc)
            overlap_start = max(start, item_start)
            overlap_end = min(end, item_end)
            allocated_hours = (overlap_end - overlap_start).total_seconds() / 3600
            key = (item.resource_type, item.resource_id)
            if key not in utilization:
                resource = self.session.get(Resource, item.resource_id)
                utilization[key] = {
                    "resource_type": item.resource_type,
                    "resource_id": item.resource_id,
                    "resource_name": resource.name if resource is not None else item.resource_id,
                    "reservation_count": 0,
                    "allocated_hours": 0.0,
                }
            utilization[key]["reservation_count"] = int(utilization[key]["reservation_count"]) + 1
            utilization[key]["allocated_hours"] = round(
                float(utilization[key]["allocated_hours"]) + allocated_hours,
                2,
            )

        conflict_query = select(AuditEntry.id).where(
            AuditEntry.action == "CONFLITO_EVITADO",
            AuditEntry.created_at >= start,
            AuditEntry.created_at < end,
        )
        if resource_ids is not None:
            if not resource_ids:
                conflict_query = conflict_query.where(AuditEntry.entity_id == "")
            else:
                conflict_query = conflict_query.where(AuditEntry.entity_id.in_(resource_ids))
        conflicts_avoided = len(list(self.session.scalars(conflict_query)))
        teaching_hours = round(
            sum(
                float(row["allocated_hours"])
                for row in utilization.values()
                if row["resource_type"] == "professor"
            ),
            2,
        )
        rows = sorted(utilization.values(), key=lambda row: (str(row["resource_type"]), str(row["resource_id"])))
        return {
            "period_start": start,
            "period_end": end,
            "utilization": rows,
            "teaching_hours": teaching_hours,
            "conflicts_avoided": conflicts_avoided,
        }
