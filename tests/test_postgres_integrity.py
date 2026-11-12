"""PostgreSQL integration tests for reservation constraints and immutable records."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import Reservation, ReservationItem, Resource, User

START = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 12, 1, 11, 0, tzinfo=timezone.utc)


def _create_requester(pg_session_factory) -> str:
    user_id = f"requester-{uuid4().hex}"
    with pg_session_factory.begin() as session:
        session.add(
            User(
                id=user_id,
                name="Integration requester",
                email=f"{user_id}@example.test",
                password_hash="not-used",
                role="SOLICITANTE",
            )
        )
    return user_id


def _insert_raw_reservation(
    connection,
    *,
    reservation_id: str,
    item_id: str,
    requester_id: str,
    resource_type: str,
    resource_id: str,
    start: datetime,
    end: datetime,
    status: str,
) -> None:
    now = datetime.now(timezone.utc)
    connection.execute(
        text(
            "INSERT INTO reservations (id, solicitante_id, reason, status, created_at, updated_at) "
            "VALUES (:id, :requester_id, 'Direct SQL test', :status, :now, :now)"
        ),
        {"id": reservation_id, "requester_id": requester_id, "status": status, "now": now},
    )
    connection.execute(
        text(
            'INSERT INTO reservation_items '
            '(id, reservation_id, resource_type, resource_id, start, "end", quantity, status, created_at, updated_at) '
            "VALUES (:id, :reservation_id, :resource_type, :resource_id, :start, :end, 1, :status, :now, :now)"
        ),
        {
            "id": item_id,
            "reservation_id": reservation_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "start": start,
            "end": end,
            "status": status,
            "now": now,
        },
    )


@pytest.mark.integration
def test_ct15_overlapping_room_insert_is_rejected_by_database(
    pg_engine, pg_session_factory, clean_postgres_database
) -> None:
    """Verifica CT-15 por INSERT direto no banco."""
    requester_id = _create_requester(pg_session_factory)
    room_id = f"room-{uuid4().hex}"
    with pg_session_factory.begin() as session:
        session.add(Resource(id=room_id, resource_type="sala", name="Sala CT-15"))

    with pg_engine.begin() as connection:
        _insert_raw_reservation(
            connection,
            reservation_id=f"reservation-{uuid4().hex}",
            item_id=f"item-{uuid4().hex}",
            requester_id=requester_id,
            resource_type="sala",
            resource_id=room_id,
            start=START,
            end=END,
            status="CONFIRMADA",
        )

    with pytest.raises(IntegrityError):
        with pg_engine.begin() as connection:
            reservation_id = f"reservation-{uuid4().hex}"
            _insert_raw_reservation(
                connection,
                reservation_id=reservation_id,
                item_id=f"item-{uuid4().hex}",
                requester_id=requester_id,
                resource_type="sala",
                resource_id=room_id,
                start=START,
                end=END,
                status="CONFIRMADA",
            )


@pytest.mark.integration
def test_ct16_overlapping_teacher_insert_is_rejected_by_database(
    pg_engine, pg_session_factory, clean_postgres_database
) -> None:
    """Verifica CT-16 por INSERT direto no banco."""
    requester_id = _create_requester(pg_session_factory)
    room_ids = [f"room-{uuid4().hex}" for _ in range(2)]
    teacher_id = f"teacher-{uuid4().hex}"
    first_reservation_id = f"reservation-{uuid4().hex}"
    with pg_session_factory.begin() as session:
        session.add_all(
            [
                Resource(id=room_ids[0], resource_type="sala", name="Sala CT-16 A"),
                Resource(id=room_ids[1], resource_type="sala", name="Sala CT-16 B"),
                Resource(id=teacher_id, resource_type="professor", name="Professor CT-16"),
                Reservation(
                    id=first_reservation_id,
                    solicitante_id=requester_id,
                    reason="Reserva ativa CT-16",
                    status="APROVADA",
                ),
                ReservationItem(
                    reservation_id=first_reservation_id,
                    resource_type="sala",
                    resource_id=room_ids[0],
                    start=START,
                    end=END,
                    status="APROVADA",
                ),
                ReservationItem(
                    reservation_id=first_reservation_id,
                    resource_type="professor",
                    resource_id=teacher_id,
                    start=START,
                    end=END,
                    status="APROVADA",
                ),
            ]
        )

    with pytest.raises(IntegrityError):
        with pg_engine.begin() as connection:
            reservation_id = f"reservation-{uuid4().hex}"
            _insert_raw_reservation(
                connection,
                reservation_id=reservation_id,
                item_id=f"item-{uuid4().hex}",
                requester_id=requester_id,
                resource_type="sala",
                resource_id=room_ids[1],
                start=START,
                end=END,
                status="APROVADA",
            )
            now = datetime.now(timezone.utc)
            connection.execute(
                text(
                    'INSERT INTO reservation_items '
                    '(id, reservation_id, resource_type, resource_id, start, "end", quantity, status, '
                    "created_at, updated_at) "
                    "VALUES (:id, :reservation_id, 'professor', :resource_id, :start, :end, 1, "
                    "'APROVADA', :now, :now)"
                ),
                {
                    "id": f"item-{uuid4().hex}",
                    "reservation_id": reservation_id,
                    "resource_id": teacher_id,
                    "start": START,
                    "end": END,
                    "now": now,
                },
            )

