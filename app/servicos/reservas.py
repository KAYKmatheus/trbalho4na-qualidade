"""Application-layer service for reservation creation and auditing."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.dominio.regras import is_overlapping_interval, material_stock_available
from app.erros import ConflictError, ValidationError
from app.models import AuditEntry, Reservation, ReservationItem


class ReservationService:
    """Coordinates domain validation and transactional persistence."""

    def __init__(self, session: Session):
        self.session = session

    def _record_audit(self, entity_type: str, entity_id: str, action: str, payload: dict) -> None:
        self.session.add(
            AuditEntry(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                payload=json.dumps(payload, sort_keys=True),
            )
        )

    def create_reservation(self, *, solicitante_id: str, reason: str, items: list[dict]) -> Reservation:
        """Create a reservation and persist the matching audit record in the same transaction."""
        if not solicitante_id or not reason:
            raise ValidationError("Solicitante e motivo são obrigatórios.")
        if not items:
            raise ValidationError("A reserva deve conter ao menos um item.")

        with self.session.begin():
            reservation = Reservation(solicitante_id=solicitante_id, reason=reason, status="PENDENTE")
            self.session.add(reservation)
            self.session.flush()

            for item in items:
                resource_type = item.get("resource_type")
                resource_id = item.get("resource_id")
                start = item.get("start")
                end = item.get("end")

                if not resource_type or not resource_id or not start or not end:
                    raise ValidationError("Cada item precisa de tipo de recurso, identificador e intervalo.")

                if isinstance(start, str):
                    start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                if isinstance(end, str):
                    end = datetime.fromisoformat(end.replace("Z", "+00:00"))

                if start >= end:
                    raise ValidationError("O intervalo da reserva deve ter início antes do fim.")

                for existing in self.session.query(ReservationItem).filter_by(
                    resource_type=resource_type, resource_id=resource_id
                ):
                    if is_overlapping_interval(start, end, existing.start, existing.end):
                        raise ConflictError(f"Conflito detectado em {resource_type} {resource_id}.")

                if resource_type == "material":
                    available = int(item.get("available", 0))
                    reserved = int(item.get("reserved", 0))
                    requested = int(item.get("quantity", 1))
                    if not material_stock_available(available=available, reserved=reserved, requested=requested):
                        raise ConflictError(
                            f"Requested quantity {requested} exceeds available stock for material {resource_id}."
                        )

                reservation_item = ReservationItem(
                    reservation_id=reservation.id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    start=start,
                    end=end,
                    status="PENDENTE",
                )
                self.session.add(reservation_item)

            self._record_audit(
                entity_type="reservation",
                entity_id=reservation.id,
                action="create",
                payload={"solicitante_id": solicitante_id, "reason": reason, "item_count": len(items)},
            )
            self.session.flush()
            return reservation
