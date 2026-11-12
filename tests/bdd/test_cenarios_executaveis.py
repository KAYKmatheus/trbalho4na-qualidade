"""Execução dos cenários Gherkin pelos serviços reais de reserva."""

from __future__ import annotations

from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from uuid import uuid4

import pytest
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dominio.regras import ACTIVE_RESERVATION_STATUSES, StatusReserva
from app.erros import ConflictError, ValidationError
from app.models import Base, Reservation, ReservationItem, Resource, User
from app.servicos.reservas import ReservationService
from tests.bdd.gherkin_steps import translate_for_pytest_bdd

FEATURE_FILES = (
    "features/reservas.feature",
    "features/conflitos_concorrencia.feature",
)
FEATURE_TEMP_DIR = TemporaryDirectory(prefix="alocasenac-bdd-")
FEATURE_SOURCE_DIR = Path(__file__).parent / "features"
for feature_name in FEATURE_FILES:
    source = FEATURE_SOURCE_DIR / Path(feature_name).name
    target = Path(FEATURE_TEMP_DIR.name) / feature_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        translate_for_pytest_bdd(source.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
scenarios(*FEATURE_FILES, features_base_dir=FEATURE_TEMP_DIR.name)

START = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 12, 1, 11, 0, tzinfo=timezone.utc)
THREAD_COUNT = 10


@pytest.fixture
def scenario_context() -> dict:
    return {}


@pytest.fixture
def scenario_session_factory(request: pytest.FixtureRequest) -> Generator[sessionmaker, None, None]:
    if request.node.get_closest_marker("integration"):
        request.getfixturevalue("clean_postgres_database")
        yield request.getfixturevalue("pg_session_factory")
        return

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()


def _add_requester(factory: sessionmaker) -> str:
    user_id = f"requester-{uuid4().hex}"
    with factory.begin() as session:
        session.add(
            User(
                id=user_id,
                name="BDD requester",
                email=f"{user_id}@example.test",
                password_hash="not-used",
                role="SOLICITANTE",
            )
        )
    return user_id


def _add_resource(
    factory: sessionmaker,
    resource_type: str,
    *,
    quantity_total: int | None = None,
    restricted: bool = False,
) -> str:
    resource_id = f"{resource_type}-{uuid4().hex}"
    with factory.begin() as session:
        session.add(
            Resource(
                id=resource_id,
                resource_type=resource_type,
                name=f"BDD {resource_type}",
                quantity_total=quantity_total,
                restricted=restricted,
            )
        )
    return resource_id


def _reserve(factory: sessionmaker, requester_id: str, items: list[dict], reason: str = "BDD") -> Reservation:
    with factory() as session:
        return ReservationService(session).create_reservation(
            solicitante_id=requester_id,
            reason=reason,
            items=items,
        )


def _item(
    resource_type: str,
    resource_id: str,
    start: datetime = START,
    end: datetime = END,
    quantity: int = 1,
) -> dict:
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "start": start,
        "end": end,
        "quantity": quantity,
    }


@given("que o Solicitante informa solicitante, finalidade, intervalo e ao menos um recurso")
def valid_reservation_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    scenario_context["requester_id"] = _add_requester(scenario_session_factory)
    scenario_context["room_id"] = _add_resource(scenario_session_factory, "sala")
    scenario_context["items"] = [_item("sala", scenario_context["room_id"])]


@when("envia a solicitação de reserva")
def create_valid_reservation(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    scenario_context["reservation"] = _reserve(
        scenario_session_factory,
        scenario_context["requester_id"],
        scenario_context["items"],
    )


@then("a reserva é registrada com o Solicitante, o intervalo e o recurso")
def valid_reservation_then(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    reservation = scenario_context["reservation"]
    with scenario_session_factory() as session:
        persisted = session.get(Reservation, reservation.id)
        assert persisted is not None
        assert persisted.solicitante_id == scenario_context["requester_id"]
        assert persisted.items[0].resource_id == scenario_context["room_id"]
        assert persisted.items[0].start.replace(tzinfo=timezone.utc) == START
        assert persisted.items[0].end.replace(tzinfo=timezone.utc) == END


@given("que a reserva não contém recurso ou finalidade, ou tem início maior ou igual ao fim")
def invalid_reservation_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    scenario_context["requester_id"] = _add_requester(scenario_session_factory)
    scenario_context["room_id"] = _add_resource(scenario_session_factory, "sala")
    scenario_context["items"] = [_item("sala", scenario_context["room_id"], END, START)]


@when("o Solicitante envia a reserva")
def create_invalid_reservation(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    try:
        _reserve(
            scenario_session_factory,
            scenario_context["requester_id"],
            scenario_context["items"],
        )
    except ValidationError as error:
        scenario_context["error"] = error


@then("o sistema responde 422 com erro associado ao campo inválido")
def invalid_reservation_then(scenario_context: dict) -> None:
    error = scenario_context.get("error")
    assert isinstance(error, ValidationError)
    assert "intervalo" in str(error).lower()


@given("que a solicitação contém sala, professor, materiais e suas quantidades")
def combined_reservation_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    scenario_context["requester_id"] = _add_requester(scenario_session_factory)
    room_id = _add_resource(scenario_session_factory, "sala")
    teacher_id = _add_resource(scenario_session_factory, "professor")
    material_ids = [
        _add_resource(scenario_session_factory, "material", quantity_total=3),
        _add_resource(scenario_session_factory, "material", quantity_total=3),
    ]
    scenario_context["items"] = [
        _item("sala", room_id),
        _item("professor", teacher_id),
        *[_item("material", material_id, quantity=2) for material_id in material_ids],
    ]


@when("o Solicitante envia a reserva com um intervalo")
def create_combined_reservation(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    scenario_context["reservation"] = _reserve(
        scenario_session_factory,
        scenario_context["requester_id"],
        scenario_context["items"],
    )


@then("todos os itens ficam registrados para o mesmo intervalo")
def combined_reservation_then(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    with scenario_session_factory() as session:
        items = session.scalars(
            select(ReservationItem).where(
                ReservationItem.reservation_id == scenario_context["reservation"].id
            )
        ).all()
    assert len(items) == 4
    assert all(
        item.start.replace(tzinfo=timezone.utc) == START
        and item.end.replace(tzinfo=timezone.utc) == END
        for item in items
    )


@given("que a reserva original está registrada")
def original_reservation_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    requester_id = _add_requester(scenario_session_factory)
    professor_id = _add_resource(scenario_session_factory, "professor")
    room_id = _add_resource(scenario_session_factory, "sala")
    _reserve(scenario_session_factory, requester_id, [_item("sala", room_id)], "Reserva conflitante")
    original = _reserve(scenario_session_factory, requester_id, [_item("professor", professor_id)], "Original")
    scenario_context.update(
        requester_id=requester_id,
        original_id=original.id,
        original_reason=original.reason,
        room_id=room_id,
        professor_id=professor_id,
    )


@when("o Solicitante tenta alterá-la para um horário em conflito")
def update_reservation_with_conflict(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    try:
        with scenario_session_factory() as session:
            ReservationService(session).update_reservation(
                reservation_id=scenario_context["original_id"],
                actor_id=scenario_context["requester_id"],
                items=[_item("sala", scenario_context["room_id"])],
            )
    except ConflictError as error:
        scenario_context["error"] = error


@then("o sistema responde 409 e preserva a reserva original")
def conflict_preserves_original_then(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    assert isinstance(scenario_context.get("error"), ConflictError)
    with scenario_session_factory() as session:
        original = session.get(Reservation, scenario_context["original_id"])
        assert original is not None
        assert original.reason == scenario_context["original_reason"]
        assert original.items[0].resource_id == scenario_context["professor_id"]
        assert original.items[0].status == StatusReserva.PENDENTE.value


@given("que existe uma reserva ativa")
def active_reservation_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    requester_id = _add_requester(scenario_session_factory)
    room_id = _add_resource(scenario_session_factory, "sala")
    reservation = _reserve(scenario_session_factory, requester_id, [_item("sala", room_id)])
    scenario_context.update(requester_id=requester_id, room_id=room_id, reservation_id=reservation.id)


@when("o Solicitante cancela a reserva")
def cancel_reservation(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    with scenario_session_factory() as session:
        scenario_context["reservation"] = ReservationService(session).cancel_reservation(
            reservation_id=scenario_context["reservation_id"],
            actor_id=scenario_context["requester_id"],
        )


@then("o status passa a CANCELADA e o recurso volta a ficar disponível")
def canceled_reservation_then(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    assert scenario_context["reservation"].status == StatusReserva.CANCELADA.value
    next_reservation = _reserve(
        scenario_session_factory,
        scenario_context["requester_id"],
        [_item("sala", scenario_context["room_id"])],
    )
    assert next_reservation.status == StatusReserva.CONFIRMADA.value


@given("que há uma reserva ativa de sala em determinado intervalo")
def active_room_booking_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    requester_id = _add_requester(scenario_session_factory)
    room_id = _add_resource(scenario_session_factory, "sala")
    _reserve(scenario_session_factory, requester_id, [_item("sala", room_id)])
    scenario_context.update(requester_id=requester_id, room_id=room_id)


@when("outra reserva da mesma sala solicita um intervalo sobreposto")
def overlapping_room_booking(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    try:
        _reserve(
            scenario_session_factory,
            scenario_context["requester_id"],
            [_item("sala", scenario_context["room_id"], START + timedelta(minutes=30), END)],
        )
    except ConflictError as error:
        scenario_context["error"] = error


@then("a segunda reserva é recusada com 409")
def conflict_status_then(scenario_context: dict) -> None:
    assert isinstance(scenario_context.get("error"), ConflictError)


@given("que um professor está reservado em uma sala durante um intervalo")
def active_teacher_booking_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    requester_id = _add_requester(scenario_session_factory)
    room_id = _add_resource(scenario_session_factory, "sala")
    teacher_id = _add_resource(scenario_session_factory, "professor")
    reservation_id = f"reservation-{uuid4().hex}"
    with scenario_session_factory.begin() as session:
        session.add(
            Reservation(
                id=reservation_id,
                solicitante_id=requester_id,
                reason="Reserva aprovada",
                status=StatusReserva.APROVADA.value,
            )
        )
        session.add_all(
            [
                ReservationItem(
                    reservation_id=reservation_id,
                    resource_type="sala",
                    resource_id=room_id,
                    start=START,
                    end=END,
                    status=StatusReserva.APROVADA.value,
                ),
                ReservationItem(
                    reservation_id=reservation_id,
                    resource_type="professor",
                    resource_id=teacher_id,
                    start=START,
                    end=END,
                    status=StatusReserva.APROVADA.value,
                ),
            ]
        )
    scenario_context.update(requester_id=requester_id, teacher_id=teacher_id)


@when("outra reserva solicita o mesmo professor em outra sala no mesmo intervalo")
def overlapping_teacher_booking(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    room_id = _add_resource(scenario_session_factory, "sala")
    try:
        _reserve(
            scenario_session_factory,
            scenario_context["requester_id"],
            [_item("sala", room_id), _item("professor", scenario_context["teacher_id"])],
        )
    except ConflictError as error:
        scenario_context["error"] = error


@given("que uma reserva termina em determinado horário")
def adjacent_reservation_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    requester_id = _add_requester(scenario_session_factory)
    room_id = _add_resource(scenario_session_factory, "sala")
    _reserve(scenario_session_factory, requester_id, [_item("sala", room_id, START, START + timedelta(hours=1))])
    scenario_context.update(requester_id=requester_id, room_id=room_id)


@when("outra reserva do mesmo recurso começa exatamente nesse horário")
def adjacent_reservation_when(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    scenario_context["reservation"] = _reserve(
        scenario_session_factory,
        scenario_context["requester_id"],
        [_item("sala", scenario_context["room_id"], START + timedelta(hours=1), END)],
    )


@then("a segunda reserva é permitida porque o fim do intervalo é aberto")
def adjacent_reservation_then(scenario_context: dict) -> None:
    assert scenario_context["reservation"].status == StatusReserva.CONFIRMADA.value


@given("que a quantidade livre de um material é conhecida")
def known_material_stock_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    requester_id = _add_requester(scenario_session_factory)
    material_id = _add_resource(scenario_session_factory, "material", quantity_total=5)
    _reserve(scenario_session_factory, requester_id, [_item("material", material_id, quantity=3)])
    scenario_context.update(requester_id=requester_id, material_id=material_id)


@when("uma reserva pede mais unidades do que estão livres")
def excess_material_request(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    try:
        _reserve(
            scenario_session_factory,
            scenario_context["requester_id"],
            [_item("material", scenario_context["material_id"], quantity=3)],
        )
    except ConflictError as error:
        scenario_context["error"] = error


@then("o sistema recusa a solicitação e informa o recurso indisponível")
def excess_material_then(scenario_context: dict) -> None:
    error = scenario_context.get("error")
    assert isinstance(error, ConflictError)
    assert error.context is not None
    assert error.context["cause"] == "ESTOQUE"


@given("que N requisições concorrentes solicitam a mesma sala e horário")
def concurrent_room_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    scenario_context["requesters"] = [
        _add_requester(scenario_session_factory) for _ in range(THREAD_COUNT)
    ]
    scenario_context["room_ids"] = [
        _add_resource(scenario_session_factory, "sala") for _ in range(5)
    ]


@when("o sistema processa as requisições simultaneamente")
def concurrent_room_when(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    def run_round(room_id: str) -> list[str]:
        barrier = Barrier(THREAD_COUNT)

        def reserve(user_id: str) -> str:
            with scenario_session_factory() as session:
                barrier.wait(timeout=30)
                try:
                    result = ReservationService(session).create_reservation(
                        solicitante_id=user_id,
                        reason="Reserva concorrente CT-19",
                        items=[_item("sala", room_id)],
                    )
                    return result.status
                except ConflictError:
                    return "conflito"

        with ThreadPoolExecutor(max_workers=THREAD_COUNT) as pool:
            return list(pool.map(reserve, scenario_context["requesters"]))

    scenario_context["rounds"] = [run_round(room_id) for room_id in scenario_context["room_ids"]]


@then("exatamente uma é confirmada e as demais recebem 409")
def concurrent_room_then(scenario_context: dict) -> None:
    for results in scenario_context["rounds"]:
        assert results.count(StatusReserva.CONFIRMADA.value) == 1
        assert results.count("conflito") == THREAD_COUNT - 1


@given("que o estoque do material comporta apenas M unidades")
def concurrent_material_given(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    scenario_context["requesters"] = [
        _add_requester(scenario_session_factory) for _ in range(THREAD_COUNT)
    ]
    scenario_context["material_id"] = _add_resource(
        scenario_session_factory,
        "material",
        quantity_total=3,
    )


@when("N requisições concorrentes solicitam esse material")
def concurrent_material_when(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    barrier = Barrier(THREAD_COUNT)

    def reserve(user_id: str) -> str:
        with scenario_session_factory() as session:
            barrier.wait(timeout=30)
            try:
                result = ReservationService(session).create_reservation(
                    solicitante_id=user_id,
                    reason="Reserva concorrente CT-20",
                    items=[_item("material", scenario_context["material_id"])],
                )
                return result.status
            except ConflictError as error:
                return error.context["cause"] if error.context else "conflito"

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as pool:
        scenario_context["results"] = list(pool.map(reserve, scenario_context["requesters"]))


@then("no máximo M unidades ficam confirmadas")
def concurrent_material_then(scenario_context: dict, scenario_session_factory: sessionmaker) -> None:
    assert scenario_context["results"].count(StatusReserva.CONFIRMADA.value) == 3
    assert scenario_context["results"].count("ESTOQUE") == THREAD_COUNT - 3
    with scenario_session_factory() as session:
        quantity = session.scalar(
            select(func.coalesce(func.sum(ReservationItem.quantity), 0)).where(
                ReservationItem.resource_type == "material",
                ReservationItem.resource_id == scenario_context["material_id"],
                ReservationItem.status.in_(ACTIVE_RESERVATION_STATUSES),
                ReservationItem.start < END,
                ReservationItem.end > START,
            )
        )
    assert quantity == 3
    assert quantity <= 3
