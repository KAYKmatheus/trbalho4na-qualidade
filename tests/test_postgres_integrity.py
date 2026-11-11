"""PostgreSQL integration tests for reservation constraints and immutable records."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.erros import ConflictError
from app.models import Reservation, ReservationItem, Resource, User
from app.servicos.reservas import ReservationService

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
def test_ct12_reservation_persists_room_teacher_and_two_material_items(
    pg_session_factory, clean_postgres_database
) -> None:
    """Verifica CT-12: os quatro itens da reserva são persistidos no mesmo período."""
    requester_id = _create_requester(pg_session_factory)
    room_id = f"room-{uuid4().hex}"
    teacher_id = f"teacher-{uuid4().hex}"
    material_ids = [f"material-{uuid4().hex}" for _ in range(2)]
    with pg_session_factory.begin() as session:
        session.add_all(
            [
                Resource(id=room_id, resource_type="sala", name="Sala CT-12"),
                Resource(id=teacher_id, resource_type="professor", name="Professor CT-12"),
                *[
                    Resource(
                        id=material_id,
                        resource_type="material",
                        name="Material CT-12",
                        quantity_total=2,
                    )
                    for material_id in material_ids
                ],
            ]
        )

    with pg_session_factory() as session:
        reservation = ReservationService(session).create_reservation(
            solicitante_id=requester_id,
            reason="Reserva combinada CT-12",
            items=[
                {"resource_type": "sala", "resource_id": room_id, "start": START, "end": END},
                {"resource_type": "professor", "resource_id": teacher_id, "start": START, "end": END},
                *[
                    {
                        "resource_type": "material",
                        "resource_id": material_id,
                        "start": START,
                        "end": END,
                        "quantity": 1,
                    }
                    for material_id in material_ids
                ],
            ],
        )
        items = session.scalars(select(ReservationItem).where(ReservationItem.reservation_id == reservation.id)).all()

    assert len(items) == 4
    assert {item.resource_type for item in items} == {"sala", "professor", "material"}
    assert sum(item.resource_type == "material" for item in items) == 2
    assert all(item.start == START and item.end == END for item in items)


@pytest.mark.integration
def test_ct15_overlapping_room_reservation_is_rejected_by_service_and_database(
    pg_engine, pg_session_factory, clean_postgres_database
) -> None:
    """Verifica CT-15 pelo serviço e por INSERT direto no banco."""
    requester_id = _create_requester(pg_session_factory)
    room_id = f"room-{uuid4().hex}"
    with pg_session_factory.begin() as session:
        session.add(Resource(id=room_id, resource_type="sala", name="Sala CT-15"))

    with pg_session_factory() as session:
        ReservationService(session).create_reservation(
            solicitante_id=requester_id,
            reason="Primeira reserva CT-15",
            items=[{"resource_type": "sala", "resource_id": room_id, "start": START, "end": END}],
        )

    with pg_session_factory() as session, pytest.raises(ConflictError):
        ReservationService(session).create_reservation(
            solicitante_id=requester_id,
            reason="Sobreposição CT-15",
            items=[{"resource_type": "sala", "resource_id": room_id, "start": START, "end": END}],
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
def test_ct16_overlapping_teacher_reservation_is_rejected_by_service_and_database(
    pg_engine, pg_session_factory, clean_postgres_database
) -> None:
    """Verifica CT-16 quando o professor já tem uma reserva ativa."""
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

    with pg_session_factory() as session, pytest.raises(ConflictError):
        ReservationService(session).create_reservation(
            solicitante_id=requester_id,
            reason="Segundo horário do professor CT-16",
            items=[
                {"resource_type": "sala", "resource_id": room_ids[1], "start": START, "end": END},
                {"resource_type": "professor", "resource_id": teacher_id, "start": START, "end": END},
            ],
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


@pytest.mark.integration
def test_ct17_adjacent_room_reservations_are_allowed(pg_session_factory, clean_postgres_database) -> None:
    """Verifica CT-17: o fim aberto permite reservar quando outra termina."""
    requester_id = _create_requester(pg_session_factory)
    room_id = f"room-{uuid4().hex}"
    with pg_session_factory.begin() as session:
        session.add(Resource(id=room_id, resource_type="sala", name="Sala CT-17"))

    with pg_session_factory() as session:
        first = ReservationService(session).create_reservation(
            solicitante_id=requester_id,
            reason="Primeiro intervalo CT-17",
            items=[
                {
                    "resource_type": "sala",
                    "resource_id": room_id,
                    "start": START,
                    "end": datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc),
                }
            ],
        )
    with pg_session_factory() as session:
        second = ReservationService(session).create_reservation(
            solicitante_id=requester_id,
            reason="Intervalo adjacente CT-17",
            items=[
                {
                    "resource_type": "sala",
                    "resource_id": room_id,
                    "start": datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc),
                    "end": END,
                }
            ],
        )

    assert first.id != second.id


