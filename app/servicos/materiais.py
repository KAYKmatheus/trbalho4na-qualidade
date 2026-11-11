"""Material inventory movements and outstanding stock calculations."""

from __future__ import annotations

import json

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.dominio.regras import ACTIVE_RESERVATION_STATUSES
from app.erros import PermissaoNegadaError, ValidationError
from app.models import AuditEntry, MaterialMovement, ReservationItem, ResourceScope, User


class MaterialService:
    """Records immutable withdrawals and returns within responsible scope."""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _totals(session: Session, item_id: str) -> tuple[int, int]:
        withdrawals = int(
            session.scalar(
                select(func.coalesce(func.sum(MaterialMovement.quantity), 0)).where(
                    MaterialMovement.reservation_item_id == item_id,
                    MaterialMovement.movement_type == "RETIRADA",
                )
            )
            or 0
        )
        returns = int(
            session.scalar(
                select(func.coalesce(func.sum(MaterialMovement.quantity), 0)).where(
                    MaterialMovement.reservation_item_id == item_id,
                    MaterialMovement.movement_type == "DEVOLUCAO",
                )
            )
            or 0
        )
        return withdrawals, returns

    @staticmethod
    def outstanding_units(session: Session, resource_id: str) -> int:
        delta = case(
            (MaterialMovement.movement_type == "RETIRADA", MaterialMovement.quantity),
            else_=-MaterialMovement.quantity,
        )
        outstanding = session.scalar(
            select(func.coalesce(func.sum(delta), 0))
            .select_from(MaterialMovement)
            .join(ReservationItem, ReservationItem.id == MaterialMovement.reservation_item_id)
            .where(
                ReservationItem.resource_type == "material",
                ReservationItem.resource_id == resource_id,
                ReservationItem.status.notin_(ACTIVE_RESERVATION_STATUSES),
            )
        )
        return max(0, int(outstanding or 0))

    def _authorize_item(self, item_id: str, responsible_id: str) -> ReservationItem:
        item = self.session.scalar(select(ReservationItem).where(ReservationItem.id == item_id).with_for_update())
        if item is None:
            raise LookupError("Item de reserva não encontrado.")
        if item.resource_type != "material":
            raise ValidationError("Movimentação permitida somente para itens de material.")
        responsible = self.session.get(User, responsible_id)
        if responsible is None or responsible.role != "RESPONSAVEL" or not responsible.active:
            raise PermissaoNegadaError("Somente um Responsável ativo pode movimentar materiais.")
        scope = self.session.scalar(
            select(ResourceScope.id).where(
                ResourceScope.responsible_id == responsible_id,
                ResourceScope.resource_id == item.resource_id,
            )
        )
        if scope is None:
            raise PermissaoNegadaError("O material não está no escopo deste Responsável.")
        return item

    def record_movement(
        self,
        *,
        item_id: str,
        responsible_id: str,
        movement_type: str,
        quantity: int,
        observation: str | None = None,
    ) -> MaterialMovement:
        if movement_type not in ("RETIRADA", "DEVOLUCAO"):
            raise ValidationError("Tipo de movimentação inválido.")
        if quantity <= 0:
            raise ValidationError("A quantidade deve ser maior que zero.")

        with self.session.begin():
            item = self._authorize_item(item_id, responsible_id)
            withdrawn, returned = self._totals(self.session, item_id)
            pending = withdrawn - returned
            if movement_type == "DEVOLUCAO" and quantity > pending:
                raise ValidationError("A devolução não pode exceder a quantidade retirada e pendente.")
            if movement_type == "RETIRADA" and pending + quantity > item.quantity:
                raise ValidationError("A retirada excede a quantidade reservada.")

            movement = MaterialMovement(
                reservation_item_id=item_id,
                responsible_id=responsible_id,
                movement_type=movement_type,
                quantity=quantity,
                observation=observation,
            )
            self.session.add(movement)
            self.session.flush()
            self.session.add(
                AuditEntry(
                    entity_type="reservation_item",
                    entity_id=item_id,
                    action=f"MATERIAL_{movement_type}",
                    payload=json.dumps({"quantity": quantity, "observation": observation}),
                    actor_id=responsible_id,
                    after_value=json.dumps({"movement_type": movement_type, "quantity": quantity}),
                )
            )
            self.session.flush()
            return movement

    def balance(self, *, item_id: str, responsible_id: str) -> dict[str, int]:
        with self.session.begin():
            self._authorize_item(item_id, responsible_id)
            withdrawn, returned = self._totals(self.session, item_id)
            return {"withdrawn": withdrawn, "returned": returned, "pending": withdrawn - returned}
