"""Application-layer service for reservation creation and auditing."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.dominio.regras import (
    ACTIVE_RESERVATION_STATUSES,
    StatusReserva,
    transition_reservation_status,
)
from app.erros import ConflictError, PermissaoNegadaError, ValidationError
from app.models import AuditEntry, Reservation, ReservationItem, Resource, ResourceBlock
from app.servicos.auditoria import AuditService
from app.servicos.materiais import MaterialService
from app.servicos.notificacoes import NotificationService


class ReservationService:
    """Coordinates domain validation and transactional persistence."""

    def __init__(self, session: Session):
        self.session = session


    def list_for_requester(self, *, solicitante_id: str) -> list[Reservation]:
        """List only reservations belonging to the requesting user."""
        return list(
            self.session.scalars(
                select(Reservation).where(
                    Reservation.solicitante_id == solicitante_id
                )
            ).all()
        )


    @staticmethod
    def _conflict_context(
        resource_type: str,
        resource_id: str,
        start: datetime,
        end: datetime,
        cause: str | None = None,
    ) -> dict[str, str]:
        context = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        if cause:
            context["cause"] = cause
        return context

    def _record_audit(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: dict,
        *,
        actor_id: str | None = None,
        before_value: str | None = None,
        after_value: str | None = None,
    ) -> None:
        self.session.add(
            AuditEntry(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                payload=json.dumps(payload, sort_keys=True),
                actor_id=actor_id,
                before_value=before_value,
                after_value=after_value,
            )
        )

    @staticmethod
    def _parse_item(item: dict) -> tuple[str, str, datetime, datetime, int]:
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
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise ValidationError("Início e fim devem ser datas válidas.")
        if start.tzinfo is None or start.utcoffset() is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None or end.utcoffset() is None:
            end = end.replace(tzinfo=timezone.utc)
        if start >= end:
            raise ValidationError("O intervalo da reserva deve ter início antes do fim.")

        try:
            quantity = int(item.get("quantity", 1))
        except (TypeError, ValueError) as exc:
            raise ValidationError("A quantidade deve ser um número inteiro maior que zero.") from exc
        if quantity <= 0:
            raise ValidationError("A quantidade deve ser maior que zero.")
        return resource_type, resource_id, start, end, quantity

    def _validate_item_availability(
        self,
        *,
        resource_type: str,
        resource_id: str,
        start: datetime,
        end: datetime,
        quantity: int,
        exclude_reservation_id: str | None = None,
    ) -> Resource | None:
        context = self._conflict_context(resource_type, resource_id, start, end)
        resource = self.session.scalar(
            select(Resource).where(Resource.id == resource_id).with_for_update()
            if resource_type == "material"
            else select(Resource).where(Resource.id == resource_id)
        )
        if resource is not None and (not resource.active or resource.resource_type != resource_type):
            raise ConflictError(
                f"Recurso {resource_id} está inativo ou não corresponde ao tipo informado.",
                context=context | {"cause": "INATIVO"},
            )

        blocked = self.session.scalar(
            select(ResourceBlock.id)
            .where(
                ResourceBlock.resource_id == resource_id,
                ResourceBlock.status == "ATIVO",
                ResourceBlock.start < end,
                ResourceBlock.end > start,
            )
            .limit(1)
        )
        if blocked is not None:
            raise ConflictError(
                f"Recurso {resource_id} está bloqueado no período solicitado.",
                context=context | {"cause": "BLOQUEIO"},
            )

        overlaps = (
            select(ReservationItem.id)
            .where(
                ReservationItem.resource_type == resource_type,
                ReservationItem.resource_id == resource_id,
                ReservationItem.status.in_(ACTIVE_RESERVATION_STATUSES),
                ReservationItem.start < end,
                ReservationItem.end > start,
            )
        )
        if exclude_reservation_id:
            overlaps = overlaps.where(ReservationItem.reservation_id != exclude_reservation_id)

        if resource_type != "material":
            if self.session.scalar(overlaps.limit(1)) is not None:
                raise ConflictError(
                    f"Conflito detectado em {resource_type} {resource_id}.",
                    context=context | {"cause": "SOBREPOSICAO"},
                )
            return resource

        if resource is None or resource.quantity_total is None:
            raise ValidationError(f"Material {resource_id} não possui estoque cadastrado.")
        reserved_query = select(func.coalesce(func.sum(ReservationItem.quantity), 0)).where(
            ReservationItem.resource_type == resource_type,
            ReservationItem.resource_id == resource_id,
            ReservationItem.status.in_(ACTIVE_RESERVATION_STATUSES),
            ReservationItem.start < end,
            ReservationItem.end > start,
        )
        if exclude_reservation_id:
            reserved_query = reserved_query.where(ReservationItem.reservation_id != exclude_reservation_id)
        reserved = int(self.session.scalar(reserved_query) or 0)
        reserved += MaterialService.outstanding_units(self.session, resource_id)
        if reserved + quantity > resource.quantity_total:
            raise ConflictError(
                f"Estoque insuficiente para o material {resource_id}.",
                context=context | {"cause": "ESTOQUE"},
            )
        return resource

    def create_reservation(self, *, solicitante_id: str, reason: str, items: list[dict]) -> Reservation:

        """Create a reservation and persist the matching audit record in the same transaction."""
        if not solicitante_id or not reason or not reason.strip():
            raise ValidationError("Solicitante e finalidade são obrigatórios.")
        if not items:
            raise ValidationError("A reserva deve conter ao menos um item.")

        conflict_context: dict[str, str] | None = None
        try:
            with self.session.begin():
                reservation = Reservation(solicitante_id=solicitante_id, reason=reason, status="SOLICITADA")
                self.session.add(reservation)
                self.session.flush()
                item_statuses: list[str] = []

                for item in items:
                    resource_type, resource_id, start, end, quantity = self._parse_item(item)
                    conflict_context = self._conflict_context(resource_type, resource_id, start, end)
                    resource = self._validate_item_availability(
                        resource_type=resource_type,
                        resource_id=resource_id,
                        start=start,
                        end=end,
                        quantity=quantity,
                    )
                    item_status = (
                        StatusReserva.PENDENTE.value
                        if resource_type == "professor" or (resource is not None and resource.restricted)
                        else StatusReserva.CONFIRMADA.value
                    )
                    item_statuses.append(item_status)
                    self.session.add(
                        ReservationItem(
                            reservation_id=reservation.id,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            start=start,
                            end=end,
                            quantity=quantity,
                            status=item_status,
                        )
                    )

                reservation.status = (
                    StatusReserva.PENDENTE.value
                    if StatusReserva.PENDENTE.value in item_statuses
                    else StatusReserva.CONFIRMADA.value
                )
                self._record_audit(
                    entity_type="reservation",
                    entity_id=reservation.id,
                    action="CREATE",
                    payload={"solicitante_id": solicitante_id, "reason": reason, "item_count": len(items)},
                    actor_id=solicitante_id,
                    before_value=json.dumps({"exists": False}, sort_keys=True),
                    after_value=json.dumps({"status": reservation.status}, sort_keys=True),
                )
                NotificationService.record(
                    self.session,
                    user_id=solicitante_id,
                    reservation_id=reservation.id,
                    event="SOLICITACAO_ENVIADA",
                    message=f"Sua solicitação de reserva foi enviada com status {reservation.status}.",
                )
                self.session.flush()
                return reservation
        except ConflictError as exc:
            context = exc.context or conflict_context
            if context is not None:
                AuditService.record_avoided_conflict(
                    self.session,
                    actor_id=solicitante_id,
                    context=context,
                    reason=str(exc),
                )
            raise
        except IntegrityError as exc:
            if conflict_context is not None:
                conflict_context["cause"] = "CONCORRENCIA"
                AuditService.record_avoided_conflict(
                    self.session,
                    actor_id=solicitante_id,
                    context=conflict_context,
                    reason="CONCORRENCIA",
                )
            raise ConflictError("Conflito detectado na reserva.") from exc
        except OperationalError as exc:
            # PostgreSQL: 40P01 = deadlock_detected
            sqlstate = getattr(exc.orig, "sqlstate", None)

            if sqlstate != "40P01" or conflict_context is None:
                raise

            conflict_context["cause"] = "CONCORRENCIA"

            AuditService.record_avoided_conflict(
                self.session,
                actor_id=solicitante_id,
                context=conflict_context,
                reason="CONCORRENCIA",
            )

            raise ConflictError(
                "Conflito de concorrência detectado na reserva.",
                context=conflict_context,
            ) from exc



    def update_reservation(
        self,
        *,
        reservation_id: str,
        actor_id: str,
        reason: str | None = None,
        items: list[dict] | None = None,
    ) -> Reservation | None:
        if reason is not None and not reason.strip():
            raise ValidationError("A finalidade da reserva é obrigatória.")
        if items is not None and not items:
            raise ValidationError("A reserva deve conter ao menos um item.")

        conflict_context: dict[str, str] | None = None
        try:
            with self.session.begin():
                reservation = self.session.scalar(
                    select(Reservation).where(Reservation.id == reservation_id).with_for_update()
                )
                if reservation is None:
                    return None
                if reservation.solicitante_id != actor_id:
                    raise PermissaoNegadaError("Não é permitido alterar reserva de outra pessoa.")
                if reservation.status not in (StatusReserva.SOLICITADA.value, StatusReserva.PENDENTE.value):
                    raise ConflictError("Somente uma solicitação ainda não decidida pode ser alterada.")

                before = {
                    "reason": reservation.reason,
                    "status": reservation.status,
                    "items": [
                        {
                            "resource_type": item.resource_type,
                            "resource_id": item.resource_id,
                            "start": item.start.isoformat(),
                            "end": item.end.isoformat(),
                            "quantity": item.quantity,
                        }
                        for item in reservation.items
                    ],
                }
                if reason is not None:
                    reservation.reason = reason
                if items is not None:
                    for existing in reservation.items:
                        existing.status = StatusReserva.CANCELADA.value
                    self.session.flush()
                    for item in items:
                        resource_type, resource_id, start, end, quantity = self._parse_item(item)
                        conflict_context = self._conflict_context(resource_type, resource_id, start, end)
                        self._validate_item_availability(
                            resource_type=resource_type,
                            resource_id=resource_id,
                            start=start,
                            end=end,
                            quantity=quantity,
                            exclude_reservation_id=reservation_id,
                        )
                        self.session.add(
                            ReservationItem(
                                reservation_id=reservation.id,
                                resource_type=resource_type,
                                resource_id=resource_id,
                                start=start,
                                end=end,
                                quantity=quantity,
                                status=StatusReserva.SOLICITADA.value,
                            )
                        )
                self._record_audit(
                    entity_type="reservation",
                    entity_id=reservation.id,
                    action="UPDATE",
                    payload={"reason": reservation.reason},
                    actor_id=actor_id,
                    before_value=json.dumps(before, sort_keys=True),
                    after_value=json.dumps(
                        {"reason": reservation.reason, "status": reservation.status},
                        sort_keys=True,
                    ),
                )
                self.session.flush()
                return reservation
        except ConflictError as exc:
            context = exc.context or conflict_context
            if context is not None:
                AuditService.record_avoided_conflict(
                    self.session,
                    actor_id=actor_id,
                    context=context,
                    reason=str(exc),
                )
            raise
        except IntegrityError as exc:
            if conflict_context is not None:
                conflict_context["cause"] = "CONCORRENCIA"
                AuditService.record_avoided_conflict(
                    self.session,
                    actor_id=actor_id,
                    context=conflict_context,
                    reason="CONCORRENCIA",
                )
            raise ConflictError("Conflito detectado ao alterar a reserva.") from exc

    def cancel_reservation(self, *, reservation_id: str, actor_id: str) -> Reservation | None:
        with self.session.begin():
            reservation = self.session.scalar(
                select(Reservation).where(Reservation.id == reservation_id).with_for_update()
            )
            if reservation is None:
                return None
            if reservation.solicitante_id != actor_id:
                raise PermissaoNegadaError("Não é permitido cancelar reserva de outra pessoa.")
            before_status = reservation.status
            try:
                reservation.status = transition_reservation_status(before_status, StatusReserva.CANCELADA).value
            except ValidationError as exc:
                raise ConflictError(str(exc)) from exc
            for item in reservation.items:
                item.status = StatusReserva.CANCELADA.value
            self._record_audit(
                entity_type="reservation",
                entity_id=reservation.id,
                action="CANCEL",
                payload={"status": reservation.status},
                actor_id=actor_id,
                before_value=json.dumps({"status": before_status}, sort_keys=True),
                after_value=json.dumps({"status": reservation.status}, sort_keys=True),
            )
            NotificationService.record(
                self.session,
                user_id=actor_id,
                reservation_id=reservation.id,
                event="CANCELADA",
                message=f"A reserva {reservation.id} foi cancelada.",
            )
            self.session.flush()
            return reservation

    def transition_reservation(
        self,
        *,
        reservation_id: str,
        target_status: str,
        actor_id: str,
    ) -> Reservation | None:
        with self.session.begin():
            reservation = self.session.scalar(
                select(Reservation).where(Reservation.id == reservation_id).with_for_update()
            )
            if reservation is None:
                return None
            before_status = reservation.status
            try:
                next_status = transition_reservation_status(before_status, target_status)
            except ValidationError as exc:
                 raise ConflictError(str(exc)) from exc

            reservation.status = next_status.value
            for item in reservation.items:
                if item.status == before_status:
                    item.status = next_status.value
            self._record_audit(
                entity_type="reservation",
                entity_id=reservation.id,
                action="STATUS_TRANSITION",
                payload={"status": next_status.value},
                actor_id=actor_id,
                before_value=json.dumps({"status": before_status}, sort_keys=True),
                after_value=json.dumps({"status": next_status.value}, sort_keys=True),
            )
            self.session.flush()
            return reservation
