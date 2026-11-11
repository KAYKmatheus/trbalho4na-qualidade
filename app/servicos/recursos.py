"""Resource catalog and responsible-scope orchestration."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.erros import ConflictError, PermissaoNegadaError, ValidationError
from app.models import AuditEntry, Resource, ResourceScope, User


class ResourceService:
    """Creates and maintains resources without deleting historical references."""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _validate(resource_type: str, values: dict) -> None:
        if not isinstance(values.get("name"), str) or not values["name"].strip():
            raise ValidationError("O nome do recurso é obrigatório.")
        if resource_type == "sala":
            if not isinstance(values.get("category"), str) or not values["category"].strip():
                raise ValidationError("O tipo da sala é obrigatório.")
            if not isinstance(values.get("location"), str) or not values["location"].strip():
                raise ValidationError("A localização da sala é obrigatória.")
            if values.get("capacity") is None or values["capacity"] <= 0:
                raise ValidationError("A capacidade da sala deve ser maior que zero.")
        elif resource_type == "material":
            if not isinstance(values.get("category"), str) or not values["category"].strip():
                raise ValidationError("O tipo do material é obrigatório.")
            if values.get("quantity_total") is None or values["quantity_total"] < 0:
                raise ValidationError("A quantidade total do material deve ser informada e não pode ser negativa.")

    @staticmethod
    def _record_audit(
        session: Session,
        *,
        actor_id: str,
        action: str,
        entity_id: str,
        before: dict | None,
        after: dict,
    ) -> None:
        session.add(
            AuditEntry(
                entity_type="resource",
                entity_id=entity_id,
                action=action,
                payload=json.dumps(after, sort_keys=True),
                actor_id=actor_id,
                before_value=json.dumps(before, sort_keys=True) if before is not None else None,
                after_value=json.dumps(after, sort_keys=True),
            )
        )

    @staticmethod
    def _snapshot(resource: Resource) -> dict:
        return {
            "resource_type": resource.resource_type,
            "name": resource.name,
            "category": resource.category,
            "capacity": resource.capacity,
            "location": resource.location,
            "competencies": resource.competencies,
            "quantity_total": resource.quantity_total,
            "restricted": resource.restricted,
            "active": resource.active,
        }

    def create(self, *, actor_id: str, values: dict) -> Resource:
        self._validate(values["resource_type"], values)
        with self.session.begin():
            resource = Resource(**values)
            self.session.add(resource)
            self.session.flush()
            self._record_audit(
                self.session,
                actor_id=actor_id,
                action="RESOURCE_CREATE",
                entity_id=resource.id,
                before=None,
                after=self._snapshot(resource),
            )
            self.session.flush()
            return resource

    def get(self, resource_id: str) -> Resource | None:
        return self.session.get(Resource, resource_id)

    def list(self, *, resource_type: str | None = None) -> list[Resource]:
        statement = select(Resource).where(Resource.active.is_(True)).order_by(Resource.name)
        if resource_type:
            statement = statement.where(Resource.resource_type == resource_type)
        return list(self.session.scalars(statement))

    def update(self, *, actor_id: str, resource_id: str, changes: dict) -> Resource | None:
        with self.session.begin():
            resource = self.session.get(Resource, resource_id)
            if resource is None:
                return None
            before = self._snapshot(resource)
            after = before | changes
            self._validate(resource.resource_type, after)
            for key, value in changes.items():
                setattr(resource, key, value)
            self._record_audit(
                self.session,
                actor_id=actor_id,
                action="RESOURCE_UPDATE",
                entity_id=resource.id,
                before=before,
                after=self._snapshot(resource),
            )
            self.session.flush()
            return resource

    def assign_scope(self, *, actor_id: str, responsible_id: str, resource_id: str) -> ResourceScope:
        try:
            with self.session.begin():
                responsible = self.session.get(User, responsible_id)
                resource = self.session.get(Resource, resource_id)
                if responsible is None or resource is None:
                    raise LookupError("Responsável ou recurso não encontrado.")
                if responsible.role != "RESPONSAVEL" or not responsible.active:
                    raise PermissaoNegadaError("O usuário informado não é um Responsável ativo.")
                scope = ResourceScope(responsible_id=responsible_id, resource_id=resource_id)
                self.session.add(scope)
                self.session.flush()
                self._record_audit(
                    self.session,
                    actor_id=actor_id,
                    action="SCOPE_ADD",
                    entity_id=scope.id,
                    before=None,
                    after={"responsible_id": responsible_id, "resource_id": resource_id},
                )
                self.session.flush()
                return scope
        except IntegrityError as exc:
            raise ConflictError("O recurso já está no escopo deste Responsável.") from exc

    def remove_scope(self, *, actor_id: str, responsible_id: str, resource_id: str) -> bool:
        with self.session.begin():
            scope = self.session.scalar(
                select(ResourceScope).where(
                    ResourceScope.responsible_id == responsible_id,
                    ResourceScope.resource_id == resource_id,
                )
            )
            if scope is None:
                return False
            self._record_audit(
                self.session,
                actor_id=actor_id,
                action="SCOPE_REMOVE",
                entity_id=scope.id,
                before={"responsible_id": responsible_id, "resource_id": resource_id},
                after={},
            )
            self.session.delete(scope)
            self.session.flush()
            return True
