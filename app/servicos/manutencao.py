"""Resource maintenance blocks."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.erros import ValidationError
from app.models import AuditEntry, Resource, ResourceBlock


class MaintenanceService:
    """Records resource unavailability periods."""

    def __init__(self, session: Session):
        self.session = session

    def create_block(
        self,
        *,
        resource_id: str,
        actor_id: str,
        start: datetime,
        end: datetime,
        reason: str,
    ) -> ResourceBlock:
        if start.tzinfo is None or start.utcoffset() is None or end.tzinfo is None or end.utcoffset() is None:
            raise ValidationError("O período da manutenção deve incluir fuso horário.")
        if start >= end:
            raise ValidationError("O início da manutenção deve ser anterior ao fim.")
        if not reason.strip():
            raise ValidationError("O motivo da manutenção é obrigatório.")

        with self.session.begin():
            resource = self.session.get(Resource, resource_id)
            if resource is None:
                raise LookupError("Recurso não encontrado.")
            block = ResourceBlock(
                resource_id=resource_id,
                start=start,
                end=end,
                reason=reason.strip(),
                status="ATIVO",
                created_by=actor_id,
            )
            self.session.add(block)
            self.session.flush()
            self.session.add(
                AuditEntry(
                    entity_type="resource",
                    entity_id=resource_id,
                    action="RESOURCE_BLOCK",
                    payload=json.dumps({"start": start.isoformat(), "end": end.isoformat(), "reason": reason.strip()}),
                    actor_id=actor_id,
                    after_value=json.dumps(
                        {"start": start.isoformat(), "end": end.isoformat(), "reason": reason.strip()},
                        sort_keys=True,
                    ),
                )
            )
            self.session.flush()
            return block
