"""PostgreSQL integration tests for persistence and concurrency."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text

from app.db import init_db
from app.dominio.regras import ACTIVE_RESERVATION_STATUSES, StatusReserva
from app.erros import ConflictError
from app.models import ReservationItem, Resource, User
from app.servicos.reservas import ReservationService

START = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 12, 1, 11, 0, tzinfo=timezone.utc)
THREAD_COUNT = 10


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


@pytest.mark.integration
@pytest.mark.concorrencia
def test_ct19_concurrent_room_requests_only_one_reservation_succeeds(
    pg_session_factory, clean_postgres_database
) -> None:
    """Verifica CT-19: uma de dez requisições concorrentes pela mesma sala vence."""
    user_ids = [f"requester-{uuid4().hex}" for _ in range(THREAD_COUNT)]
    _create_requesters(pg_session_factory, user_ids)

    def attempt(user_id: str, resource_id: str, barrier: Barrier) -> str:
        with pg_session_factory() as session:
            barrier.wait(timeout=30)
            try:
                reservation = ReservationService(session).create_reservation(
                    solicitante_id=user_id,
                    reason="Reserva concorrente CT-19",
                    items=[
                        {
                            "resource_type": "sala",
                            "resource_id": resource_id,
                            "start": START,
                            "end": END,
                        }
                    ],
                )
                return reservation.status
            except ConflictError:
                return "conflito"

    for _ in range(5):
        resource_id = f"room-concurrent-{uuid4().hex}"
        with pg_session_factory.begin() as session:
            session.add(Resource(id=resource_id, resource_type="sala", name="Sala concorrente"))

        barrier = Barrier(THREAD_COUNT)
        with ThreadPoolExecutor(max_workers=THREAD_COUNT) as pool:
            results = list(pool.map(lambda user_id: attempt(user_id, resource_id, barrier), user_ids))

        assert results.count(StatusReserva.CONFIRMADA.value) == 1
        assert results.count("conflito") == THREAD_COUNT - 1


@pytest.mark.integration
@pytest.mark.concorrencia
def test_ct20_concurrent_material_requests_never_exceed_stock(
    pg_session_factory, clean_postgres_database
) -> None:
    """Verifica CT-20: dez pedidos de uma unidade respeitam o estoque três."""
    resource_id = f"material-concurrent-{uuid4().hex}"
    user_ids = [f"requester-{uuid4().hex}" for _ in range(THREAD_COUNT)]
    _create_requesters(pg_session_factory, user_ids)
    with pg_session_factory.begin() as session:
        session.add(
            Resource(
                id=resource_id,
                resource_type="material",
                name="Material concorrente",
                quantity_total=3,
            )
        )

    barrier = Barrier(THREAD_COUNT)

    def attempt(user_id: str) -> str:
        with pg_session_factory() as session:
            barrier.wait(timeout=30)
            try:
                reservation = ReservationService(session).create_reservation(
                    solicitante_id=user_id,
                    reason="Reserva concorrente CT-20",
                    items=[
                        {
                            "resource_type": "material",
                            "resource_id": resource_id,
                            "start": START,
                            "end": END,
                            "quantity": 1,
                        }
                    ],
                )
                return reservation.status
            except ConflictError as exc:
                return exc.context["cause"] if exc.context is not None else "conflito"

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as pool:
        results = list(pool.map(attempt, user_ids))

    assert results.count(StatusReserva.CONFIRMADA.value) == 3
    assert results.count("ESTOQUE") == THREAD_COUNT - 3
    with pg_session_factory() as session:
        reserved_quantity = session.scalar(
            select(func.coalesce(func.sum(ReservationItem.quantity), 0)).where(
                ReservationItem.resource_type == "material",
                ReservationItem.resource_id == resource_id,
                ReservationItem.status.in_(ACTIVE_RESERVATION_STATUSES),
                ReservationItem.start < END,
                ReservationItem.end > START,
            )
        )
    assert reserved_quantity == 3
    assert reserved_quantity <= 3
