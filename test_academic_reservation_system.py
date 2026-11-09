"""TDD suite for the academic reservation backbone.

Each test cites the requirement and CT it validates so the implementation stays
traceable to the PRD and quality docs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app_config import AppSettings
from domain_rules import (
    ConflictError,
    is_overlapping_interval,
    material_stock_available,
)
from errors import ValidationError
from models import AuditEntry, Reservation, ReservationItem
from services import ReservationService


@pytest.fixture
def settings(postgres_database_url: str) -> AppSettings:
    return AppSettings(
        database_url=postgres_database_url,
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


def test_service_rejects_missing_request_fields_before_connecting() -> None:
    service = ReservationService(AppSettings())

    with pytest.raises(ValidationError):
        service.create_reservation(solicitante_id="", reason="Teste", items=[{}])

    with pytest.raises(ValidationError):
        service.create_reservation(solicitante_id="user-1", reason="Teste", items=[])


def test_service_parses_iso_datetimes_and_rejects_invalid_values() -> None:
    valid = ReservationService._parse_datetime("2026-02-01T09:00:00Z")
    assert valid == datetime(2026, 2, 1, 9, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        ReservationService._parse_datetime("not-a-date")


@pytest.mark.integration
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
    import models

    session = models.SessionLocal()
    try:
        assert session.query(ReservationItem).filter_by(reservation_id=reservation.id).count() == 1
        assert session.query(AuditEntry).filter_by(
            entity_type="reservation",
            entity_id=reservation.id,
        ).count() == 1
    finally:
        session.close()


@pytest.mark.integration
def test_service_rejects_conflicting_room_reservation(settings: AppSettings) -> None:
    """Verifica FR-06, RN02, NFR-03, CT-15.

    Uma segunda reserva sequencial em intervalo sobreposto deve ser recusada.
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
def test_api_v1_responds_to_creation_endpoint(
    settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifica FR-04, FR-14, NFR-06, CT-10 e CT-33.

    A API /v1 deve expor a criação de reservas com resposta clara.
    """
    from api_v1 import app
    from fastapi.testclient import TestClient

    monkeypatch.setattr("api_v1.AppSettings", lambda: settings)
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


def test_api_health_endpoint_reports_service_status() -> None:
    from api_v1 import app
    from fastapi.testclient import TestClient

    response = TestClient(app).get("/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_returns_422_when_reservation_has_no_items(monkeypatch: pytest.MonkeyPatch) -> None:
    from api_v1 import app
    from fastapi.testclient import TestClient

    settings = AppSettings()
    monkeypatch.setattr("api_v1.AppSettings", lambda: settings)
    response = TestClient(app).post(
        "/v1/reservations",
        json={"solicitante_id": "user-1", "reason": "Teste", "items": []},
    )

    assert response.status_code == 422


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
