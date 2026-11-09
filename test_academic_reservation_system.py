"""TDD suite for the academic reservation backbone.

Each test cites the requirement and CT it validates so the implementation stays
traceable to the PRD and quality docs.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from app_config import AppSettings
from domain_rules import (
    ConflictError,
    is_overlapping_interval,
    material_stock_available,
)
from models import AuditEntry, Reservation, ReservationItem
from services import ReservationService


@pytest.fixture
def settings() -> AppSettings:
    return AppSettings(
        database_url="postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test",
        app_name="alocasenac",
    )


def test_interval_overlap_rule_detects_conflict() -> None:
    """Verifica FR-06, RN02, CT-15.

    Duas reservas sobrepostas na mesma sala devem ser tratadas como conflito.
    """
    assert is_overlapping_interval(
        datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
    )
    assert not is_overlapping_interval(
        datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
    )


def test_material_stock_is_rejected_when_exceeded() -> None:
    """Verifica FR-06, RN02, CT-18 e CT-20.

    O estoque de materiais deve sempre manter o saldo disponível.
    """
    assert material_stock_available(available=5, reserved=3, requested=2) is True
    assert material_stock_available(available=5, reserved=3, requested=3) is False
    assert material_stock_available(available=4, reserved=3, requested=2) is False


def test_service_creates_reservation_and_audit_record(settings: AppSettings) -> None:
    """Verifica FR-11, RN08, NFR-09, CT-28.

    Toda escrita de reserva precisa persistir auditoria na mesma transação.
    """
    service = ReservationService(settings)

    reservation = service.create_reservation(
        solicitante_id="user-1",
        reason="Aula de laboratórios",
        items=[
            {
                "resource_type": "sala",
                "resource_id": "room-1",
                "start": datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc),
                "end": datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
            }
        ],
    )

    assert isinstance(reservation, Reservation)
    assert len(reservation.items) == 1
    assert ReservationItem.query.filter_by(reservation_id=reservation.id).count() == 1
    assert AuditEntry.query.filter_by(entity_type="reservation", entity_id=reservation.id).count() == 1


def test_service_rejects_conflicting_room_reservation(settings: AppSettings) -> None:
    """Verifica FR-07, RN04, NFR-03, CT-19.

    Operações concorrentes sobre o mesmo recurso devem produzir um conflito e
    uma resposta clara para a segunda tentativa.
    """
    service = ReservationService(settings)

    service.create_reservation(
        solicitante_id="user-1",
        reason="Primeira reserva",
        items=[
            {
                "resource_type": "sala",
                "resource_id": "room-1",
                "start": datetime(2026, 1, 11, 9, 0, tzinfo=timezone.utc),
                "end": datetime(2026, 1, 11, 12, 0, tzinfo=timezone.utc),
            }
        ],
    )

    with pytest.raises(ConflictError):
        service.create_reservation(
            solicitante_id="user-2",
            reason="Segunda reserva",
            items=[
                {
                    "resource_type": "sala",
                    "resource_id": "room-1",
                    "start": datetime(2026, 1, 11, 10, 0, tzinfo=timezone.utc),
                    "end": datetime(2026, 1, 11, 11, 30, tzinfo=timezone.utc),
                }
            ],
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    "resource_type, resource_id, start, end",
    [
        ("sala", "room-7", "2026-01-12T08:00:00Z", "2026-01-12T10:00:00Z"),
        ("professor", "teacher-7", "2026-01-12T08:00:00Z", "2026-01-12T10:00:00Z"),
    ],
)
def test_postgres_real_database_accepts_integration_write(resource_type: str, resource_id: str, start: str, end: str) -> None:
    """Verifica FR-02, FR-11, NFR-05, CT-06 e CT-28.

    A integração usa PostgreSQL real para teste de persistência.
    """
    from sqlalchemy import create_engine, text

    engine = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS integration_probe (resource_type TEXT, resource_id TEXT, start_ts TIMESTAMPTZ, end_ts TIMESTAMPTZ)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO integration_probe (resource_type, resource_id, start_ts, end_ts) VALUES (:resource_type, :resource_id, :start, :end)"
            ),
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "start": start,
                "end": end,
            },
        )
        conn.commit()

        row = conn.execute(
            text(
                "SELECT COUNT(*) FROM integration_probe WHERE resource_type = :resource_type AND resource_id = :resource_id"
            ),
            {"resource_type": resource_type, "resource_id": resource_id},
        ).scalar_one()
        assert row == 1


@pytest.mark.integration
def test_concurrent_room_requests_only_one_reservation_succeeds() -> None:
    """Verifica FR-07, RN04, NFR-03, CT-19.

    Em ambiente PostgreSQL real, apenas uma das solicitações concorrentes deve
    confirmar a reserva no mesmo intervalo.
    """
    from models import init_db
    from services import ReservationService

    init_db("postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test")
    service = ReservationService(AppSettings(database_url="postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test"))

    def attempt(user_id: str):
        try:
            return service.create_reservation(
                solicitante_id=user_id,
                reason="Reserva concorrente",
                items=[
                    {
                        "resource_type": "sala",
                        "resource_id": "room-concurrent",
                        "start": datetime(2026, 2, 1, 9, 0, tzinfo=timezone.utc),
                        "end": datetime(2026, 2, 1, 11, 0, tzinfo=timezone.utc),
                    }
                ],
            )
        except ConflictError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, ["user-a", "user-b"]))

    assert sum(result is not None for result in results) == 1


def test_api_v1_responds_to_creation_endpoint() -> None:
    """Verifica FR-04, FR-14, NFR-06, CT-10 e CT-33.

    A API /v1 deve expor a criação de reservas com resposta clara.
    """
    from api_v1 import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/v1/reservations",
        json={
            "solicitante_id": "user-1",
            "reason": "Reserva de aula",
            "items": [
                {
                    "resource_type": "sala",
                    "resource_id": "room-2",
                    "start": "2026-01-15T09:00:00Z",
                    "end": "2026-01-15T11:00:00Z",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "PENDENTE"
    assert payload["items"][0]["resource_type"] == "sala"


def test_home_page_renders_reservation_dashboard() -> None:
    """Verifica FR-14, FR-15, NFR-06, CT-33 e CT-35.

    A página principal deve apresentar o painel de reservas e documentação da API.
    """
    from api_v1 import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    text = response.text.lower()
    assert "dashboard" in text or "alocasenac" in text
    assert "api" in text
