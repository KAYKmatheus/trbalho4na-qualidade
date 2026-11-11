"""Append-only audit records for conflicts and avoided allocation failures."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models import AuditEntry


class AuditService:
    """Writes audit records through inserts only."""

    @staticmethod
    def record_avoided_conflict(
        session: Session,
        *,
        actor_id: str,
        context: dict[str, str],
        reason: str,
    ) -> None:
        resource_type = context["resource_type"]
        resource_id = context["resource_id"]
        event = {
            "start": context["start"],
            "end": context["end"],
            "reason": context.get("cause", reason),
            "message": reason,
        }
        with session.begin():
            session.add(
                AuditEntry(
                    entity_type=resource_type,
                    entity_id=resource_id,
                    action="CONFLITO_EVITADO",
                    payload=json.dumps(event, sort_keys=True),
                    actor_id=actor_id,
                    after_value=json.dumps(event, sort_keys=True),
                )
            )
