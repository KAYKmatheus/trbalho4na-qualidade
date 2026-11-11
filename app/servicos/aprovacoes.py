"""Approval and teacher-validation decisions."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dominio.regras import ACTIVE_RESERVATION_STATUSES, StatusReserva
from app.erros import ConflictError, PermissaoNegadaError, ValidationError
from app.models import Approval, AuditEntry, Reservation, ReservationItem, Resource, ResourceScope, User
from app.servicos.auditoria import AuditService
from app.servicos.notificacoes import NotificationService
from app.servicos.reservas import ReservationService


class ApprovalService:
    """Records scoped decisions and revalidates availability before approval."""

    def __init__(self, session: Session):
        self.session = session

    def decide(
        self,
        *,
        item_id: str,
        responsible_id: str,
        decision_type: str,
        decision: str,
        justification: str,
    ) -> Reservation | None:
        if not justification.strip():
            raise ValidationError("A justificativa da decisão é obrigatória.")
        if decision not in ("APROVADA", "REJEITADA"):
            raise ValidationError("Decisão inválida.")

        conflict_context: dict[str, str] | None = None
        try:
            with self.session.begin():
                item = self.session.scalar(
                    select(ReservationItem).where(ReservationItem.id == item_id).with_for_update()
                )
                if item is None:
                    return None
                reservation = self.session.scalar(
                    select(Reservation).where(Reservation.id == item.reservation_id).with_for_update()
                )
                responsible = self.session.get(User, responsible_id)
                if reservation is None or responsible is None:
                    return None
                if responsible.role != "RESPONSAVEL" or not responsible.active:
                    raise PermissaoNegadaError("Somente um Responsável ativo pode decidir a solicitação.")
                if reservation.solicitante_id == responsible_id:
                    raise PermissaoNegadaError("O solicitante não pode aprovar a própria solicitação.")

                resource = self.session.get(Resource, item.resource_id)
                if resource is None:
                    raise ValidationError("Recurso da solicitação não encontrado.")
                conflict_context = {
                    "resource_type": item.resource_type,
                    "resource_id": item.resource_id,
                    "start": item.start.isoformat(),
                    "end": item.end.isoformat(),
                }
                expected_decision_type = (
                    "VALIDACAO_DOCENTE" if item.resource_type == "professor" else "RECURSO_RESTRITO"
                )
                if decision_type != expected_decision_type:
                    raise ValidationError("O tipo de decisão não corresponde ao recurso solicitado.")

                scope = self.session.scalar(
                    select(ResourceScope.id).where(
                        ResourceScope.responsible_id == responsible_id,
                        ResourceScope.resource_id == item.resource_id,
                    )
                )
                if scope is None:
                    raise PermissaoNegadaError("O recurso não está no escopo deste Responsável.")
                if item.status != StatusReserva.PENDENTE.value:
                    raise ConflictError("O item não está aguardando decisão.")

                if decision == "APROVADA":
                    ReservationService(self.session)._validate_item_availability(
                        resource_type=item.resource_type,
                        resource_id=item.resource_id,
                        start=item.start,
                        end=item.end,
                        quantity=item.quantity,
                        exclude_reservation_id=reservation.id,
                    )
                    item.status = StatusReserva.APROVADA.value
                else:
                    item.status = StatusReserva.REJEITADA.value

                self.session.add(
                    Approval(
                        reservation_item_id=item.id,
                        responsible_id=responsible_id,
                        decision_type=decision_type,
                        decision=decision,
                        justification=justification.strip(),
                    )
                )
                self.session.add(
                    AuditEntry(
                        entity_type="reservation_item",
                        entity_id=item.id,
                        action="APPROVAL" if decision == "APROVADA" else "REJECTION",
                        payload=json.dumps({"decision_type": decision_type, "decision": decision}),
                        actor_id=responsible_id,
                        before_value=json.dumps({"status": StatusReserva.PENDENTE.value}),
                        after_value=json.dumps(
                            {"status": item.status, "justification": justification.strip()},
                            sort_keys=True,
                        ),
                    )
                )
                notification_event = "APROVADA" if decision == "APROVADA" else "REJEITADA"
                message = (
                    f"A reserva {reservation.id} foi {notification_event.lower()}."
                    if decision == "APROVADA"
                    else f"A reserva {reservation.id} foi rejeitada: {justification.strip()}"
                )
                NotificationService.record(
                    self.session,
                    user_id=reservation.solicitante_id,
                    reservation_id=reservation.id,
                    event=notification_event,
                    message=message,
                )

                self.session.flush()
                statuses = list(
                    self.session.scalars(
                        select(ReservationItem.status).where(ReservationItem.reservation_id == reservation.id)
                    )
                )
                if all(status in ACTIVE_RESERVATION_STATUSES for status in statuses):
                    reservation.status = StatusReserva.CONFIRMADA.value
                elif all(status == StatusReserva.REJEITADA.value for status in statuses):
                    reservation.status = StatusReserva.REJEITADA.value
                else:
                    reservation.status = StatusReserva.PENDENTE.value
                self.session.flush()
                return reservation
        except ConflictError as exc:
            context = exc.context or conflict_context
            if context is not None:
                AuditService.record_avoided_conflict(
                    self.session,
                    actor_id=responsible_id,
                    context=context,
                    reason=str(exc),
                )
            raise
        except IntegrityError as exc:
            if conflict_context is not None:
                conflict_context["cause"] = "CONCORRENCIA"
                AuditService.record_avoided_conflict(
                    self.session,
                    actor_id=responsible_id,
                    context=conflict_context,
                    reason="CONCORRENCIA",
                )
            raise ConflictError("O recurso já foi alocado em um intervalo conflitante.") from exc
