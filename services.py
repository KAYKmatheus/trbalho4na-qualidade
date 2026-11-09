"""Application-layer service for reservation creation and auditing."""

from __future__ import annotations

from datetime import datetime
import json

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app_config import AppSettings
from domain_rules import ConflictError, is_overlapping_interval
from errors import ValidationError
from models import AuditEntry, Material, Reservation, ReservationItem, configure_database


class ReservationService:
    """Coordinates domain validation and transactional persistence."""

    def __init__(self, settings: AppSettings | None = None):
        self.settings = settings or AppSettings()
        configure_database(self.settings)
        from models import SessionLocal as BoundSessionLocal
        self.session_factory = BoundSessionLocal

    def _record_audit(self, session, entity_type: str, entity_id: str, action: str, payload: dict) -> None:
        session.add(
            AuditEntry(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                payload=json.dumps(payload, sort_keys=True),
            )
        )

    @staticmethod
    def _parse_datetime(value: datetime | str) -> datetime:
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise ValidationError("Data e hora devem usar formato ISO 8601.") from exc

    def create_reservation(self, *, solicitante_id: str, reason: str, items: list[dict]) -> Reservation:
        """Create a reservation and persist the matching audit record in the same transaction."""
        if not solicitante_id or not reason:
            raise ValidationError("Solicitante e motivo são obrigatórios.")
        if not items:
            raise ValidationError("A reserva deve conter ao menos um item.")

        session = self.session_factory()
        try:
            with session.begin():
                reservation = Reservation(solicitante_id=solicitante_id, reason=reason, status="PENDENTE")
                session.add(reservation)
                session.flush()

                for item in items:
                    resource_type = item.get("resource_type")
                    resource_id = item.get("resource_id")
                    start = item.get("start")
                    end = item.get("end")

                    if not resource_type or not resource_id or not start or not end:
                        raise ValidationError("Cada item precisa de tipo de recurso, identificador e intervalo.")
                    start = self._parse_datetime(start)
                    end = self._parse_datetime(end)
                    if start >= end:
                        raise ValidationError("O intervalo da reserva deve ter início antes do fim.")

                    quantity = int(item.get("quantity", 1))
                    if resource_type == "material":
                        if quantity < 1:
                            raise ValidationError("A quantidade de material deve ser positiva.")
                        material = (
                            session.query(Material)
                            .filter_by(id=resource_id, active=True)
                            .with_for_update()
                            .one_or_none()
                        )
                        if material is None:
                            raise ValidationError(f"Material {resource_id} não encontrado ou inativo.")
                        reserved = (
                            session.query(func.coalesce(func.sum(ReservationItem.quantity), 0))
                            .filter(
                                ReservationItem.resource_type == "material",
                                ReservationItem.resource_id == resource_id,
                                ReservationItem.status.in_(("PENDENTE", "APROVADA", "CONFIRMADA")),
                                ReservationItem.start < end,
                                ReservationItem.end > start,
                            )
                            .scalar()
                        )
                        if quantity > material.quantity_total - int(reserved or 0):
                            raise ConflictError(
                                f"Estoque insuficiente para o material {resource_id}."
                            )
                    elif quantity != 1:
                        raise ValidationError("Salas e professores devem ter quantidade igual a 1.")
                    else:
                        for existing in session.query(ReservationItem).filter(
                            ReservationItem.resource_type == resource_type,
                            ReservationItem.resource_id == resource_id,
                            ReservationItem.status.in_(
                                ("PENDENTE", "APROVADA", "CONFIRMADA")
                            ),
                        ):
                            if is_overlapping_interval(start, end, existing.start, existing.end):
                                raise ConflictError(f"Conflito detectado em {resource_type} {resource_id}.")

                    reservation_item = ReservationItem(
                        reservation_id=reservation.id,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        start=start,
                        end=end,
                        quantity=quantity,
                        status="PENDENTE",
                    )
                    reservation.items.append(reservation_item)
                    session.flush()

                self._record_audit(
                    session,
                    entity_type="reservation",
                    entity_id=reservation.id,
                    action="create",
                    payload={"solicitante_id": solicitante_id, "reason": reason, "item_count": len(items)},
                )
                session.flush()
                return reservation
        except IntegrityError as exc:
            sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
            if sqlstate == "23P01":
                raise ConflictError("Conflito detectado para o recurso e intervalo solicitados.") from exc
            raise
        finally:
            session.close()
