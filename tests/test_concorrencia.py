"""PostgreSQL integration tests for persistence and concurrency."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db import init_db
from app.errors import ConflictError
from app.models import Resource, User
from app.servicos.reservas import ReservationService

START = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 12, 1, 11, 0, tzinfo=timezone.utc)


def _create_requesters(pg_session_factory, user_ids: list[str]) -> None:
    with pg_session_factory.begin() as session:
        session.add_all(
            [
                User(
                    id=user_id,
                    name="Integration requester",
                    email=f"{user_id}@example.test",
                    password_hash="not-used",
                    role="SOLICITANTE",
                )
                for user_id in user_ids
            ]
        )


@pytest.mark.integration
def test_postgres_schema_has_exclusion_and_immutable_triggers(pg_engine, clean_postgres_database) -> None:
    """Verifica que reaplicar migrações mantém a restrição e os três gatilhos."""
    init_db(pg_engine)
    init_db(pg_engine)

    with pg_engine.connect() as connection:
        constraint_count = connection.scalar(
            text(
                "SELECT COUNT(*) FROM pg_constraint "
                "WHERE conrelid = 'reservation_items'::regclass "
                "AND conname = 'reservation_items_no_overlap'"
            )
        )
        trigger_names = set(
            connection.scalars(
                text(
                    "SELECT tgname FROM pg_trigger "
                    "WHERE NOT tgisinternal "
                    "AND tgname IN ("
                    "'audit_entries_immutable_guard', "
                    "'approvals_immutable_guard', "
                    "'material_movements_immutable_guard')"
                )
            ).all()
        )

    assert constraint_count == 1
    assert trigger_names == {
        "audit_entries_immutable_guard",
        "approvals_immutable_guard",
        "material_movements_immutable_guard",
    }


@pytest.mark.integration
def test_overlapping_material_reservations_respect_available_stock(
    pg_session_factory, clean_postgres_database
) -> None:
    """Permite reservas parciais sobrepostas sem exceder o estoque."""
    resource_id = f"material-stock-{uuid4().hex}"
    user_id = f"requester-{uuid4().hex}"
    _create_requesters(pg_session_factory, [user_id])

    with pg_session_factory.begin() as session:
        session.add(
            Resource(
                id=resource_id,
                resource_type="material",
                name="Material com estoque",
                quantity_total=5,
            )
        )

    def reserve_two_units(reason: str) -> None:
        with pg_session_factory() as session:
            ReservationService(session).create_reservation(
                solicitante_id=user_id,
                reason=reason,
                items=[
                    {
                        "resource_type": "material",
                        "resource_id": resource_id,
                        "start": START,
                        "end": END,
                        "quantity": 2,
                    }
                ],
            )

    reserve_two_units("Reserva parcial 1")
    reserve_two_units("Reserva parcial 2")

    with pg_session_factory() as session, pytest.raises(ConflictError) as error:
        ReservationService(session).create_reservation(
            solicitante_id=user_id,
            reason="Reserva além do estoque",
            items=[
                {
                    "resource_type": "material",
                    "resource_id": resource_id,
                    "start": START,
                    "end": END,
                    "quantity": 2,
                }
            ],
        )

    assert error.value.context is not None
    assert error.value.context["cause"] == "ESTOQUE"
