
"""PostgreSQL integration tests for append-only records."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.models import (
    Approval,
    AuditEntry,
    MaterialMovement,
    Reservation,
    ReservationItem,
    Resource,
    User,
)

START = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 12, 1, 11, 0, tzinfo=timezone.utc)


@pytest.mark.integration
def test_ct29_immutable_tables_reject_update_delete_and_accept_insert(
    pg_engine, pg_session_factory, clean_postgres_database
) -> None:
    """Verifica CT-29 nos três gatilhos append-only do PostgreSQL."""

    user_id = f"requester-{uuid4().hex}"
    material_id = f"material-{uuid4().hex}"
    reservation_id = f"reservation-{uuid4().hex}"
    item_id = f"item-{uuid4().hex}"

    audit_id = f"audit-{uuid4().hex}"
    approval_id = f"approval-{uuid4().hex}"
    movement_id = f"movement-{uuid4().hex}"

    # 1. Cria primeiro os registros necessários para as chaves estrangeiras.
    with pg_session_factory.begin() as session:
        session.add_all(
            [
                User(
                    id=user_id,
                    name="Integration requester",
                    email=f"{user_id}@example.test",
                    password_hash="not-used",
                    role="SOLICITANTE",
                ),
                Resource(
                    id=material_id,
                    resource_type="material",
                    name="Material CT-29",
                    quantity_total=1,
                ),
                Reservation(
                    id=reservation_id,
                    solicitante_id=user_id,
                    reason="Reserva CT-29",
                    status="CONFIRMADA",
                ),
            ]
        )

        # Persiste usuário, recurso e reserva.
        session.flush()

        # 2. Cria o item da reserva depois que a reserva já existe.
        session.add(
            ReservationItem(
                id=item_id,
                reservation_id=reservation_id,
                resource_type="material",
                resource_id=material_id,
                start=START,
                end=END,
                status="CONFIRMADA",
            )
        )

        # Garante que o item exista antes das aprovações e movimentações.
        session.flush()

        # 3. Cria os três registros append-only.
        session.add_all(
            [
                AuditEntry(
                    id=audit_id,
                    entity_type="reservation",
                    entity_id=reservation_id,
                    action="CREATE",
                    payload="{}",
                ),
                Approval(
                    id=approval_id,
                    reservation_item_id=item_id,
                    responsible_id=user_id,
                    decision_type="RECURSO_RESTRITO",
                    decision="APROVADA",
                    justification="Teste de imutabilidade",
                ),
                MaterialMovement(
                    id=movement_id,
                    reservation_item_id=item_id,
                    responsible_id=user_id,
                    movement_type="RETIRADA",
                    quantity=1,
                ),
            ]
        )

    # 4. Verifica se UPDATE e DELETE são bloqueados.
    immutable_operations = [
        (
            audit_id,
            "UPDATE audit_entries SET payload = 'alterado' WHERE id = :id",
            "DELETE FROM audit_entries WHERE id = :id",
            "Audit entries are immutable",
        ),
        (
            approval_id,
            "UPDATE approvals SET justification = 'alterado' WHERE id = :id",
            "DELETE FROM approvals WHERE id = :id",
            "Approvals are immutable",
        ),
        (
            movement_id,
            "UPDATE material_movements SET observation = 'alterado' WHERE id = :id",
            "DELETE FROM material_movements WHERE id = :id",
            "Material movements are immutable",
        ),
    ]

    for row_id, update_statement, delete_statement, message in immutable_operations:
        for statement in (update_statement, delete_statement):
            with pytest.raises(DBAPIError, match=message):
                with pg_engine.begin() as connection:
                    connection.execute(text(statement), {"id": row_id})

    # 5. Verifica se novas inserções continuam permitidas.
    new_audit_id = f"audit-{uuid4().hex}"
    new_approval_id = f"approval-{uuid4().hex}"
    new_movement_id = f"movement-{uuid4().hex}"

    with pg_session_factory.begin() as session:
        session.add_all(
            [
                AuditEntry(
                    id=new_audit_id,
                    entity_type="reservation",
                    entity_id=reservation_id,
                    action="CREATE",
                    payload='{"teste": "nova insercao"}',
                ),
                Approval(
                    id=new_approval_id,
                    reservation_item_id=item_id,
                    responsible_id=user_id,
                    decision_type="RECURSO_RESTRITO",
                    decision="APROVADA",
                    justification="Nova aprovação CT-29",
                ),
                MaterialMovement(
                    id=new_movement_id,
                    reservation_item_id=item_id,
                    responsible_id=user_id,
                    movement_type="RETIRADA",
                    quantity=1,
                ),
            ]
        )

    # 6. Confirma que os novos registros foram persistidos.
    with pg_session_factory() as session:
        assert session.get(AuditEntry, new_audit_id) is not None
        assert session.get(Approval, new_approval_id) is not None
        assert session.get(MaterialMovement, new_movement_id) is not None
