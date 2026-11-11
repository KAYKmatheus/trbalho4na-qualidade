"""Unit tests for reservation persistence and the HTTP API."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.erros import ConflictError
from app.models import AuditEntry, Base, Reservation, ReservationItem, User
from app.servicos.autenticacao import hash_password
from app.servicos.reservas import ReservationService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_service_creates_reservation_and_audit_record(db_session) -> None:
    """Verifica FR-11, RN08, NFR-09, CT-28."""
    reservation = ReservationService(db_session).create_reservation(
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
    assert db_session.query(ReservationItem).filter_by(reservation_id=reservation.id).count() == 1
    assert db_session.query(AuditEntry).filter_by(entity_type="reservation", entity_id=reservation.id).count() == 1


def test_service_rejects_conflicting_room_reservation(db_session) -> None:
    """Verifica conflitos de sala em reservas sequenciais (CT-15)."""
    service = ReservationService(db_session)
    reservation = service.create_reservation(
        solicitante_id="user-1",
        reason="Primeira reserva",
        items=[
            {
                "resource_type": "sala",
                "resource_id": "room-1",
                "start": datetime(2026, 1, 11, 9, 0),
                "end": datetime(2026, 1, 11, 12, 0),
            }
        ],
    )
    db_session.query(ReservationItem).filter_by(reservation_id=reservation.id).one().status = "CONFIRMADA"
    db_session.commit()

    with pytest.raises(ConflictError):
        service.create_reservation(
            solicitante_id="user-2",
            reason="Segunda reserva",
            items=[
                {
                    "resource_type": "sala",
                    "resource_id": "room-1",
                    "start": datetime(2026, 1, 11, 10, 0),
                    "end": datetime(2026, 1, 11, 11, 30),
                }
            ],
        )


def test_api_v1_responds_to_creation_endpoint(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica FR-04, FR-14, NFR-06, CT-10 e CT-33."""
    from app.api.v1 import app

    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-with-enough-entropy")
    db_session.add(
        User(
            id="user-1",
            name="Solicitante",
            email="user-1@example.test",
            password_hash=hash_password("password-1"),
            role="SOLICITANTE",
            active=True,
        )
    )
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        token_response = TestClient(app).post(
            "/v1/auth/login",
            json={"email": "user-1@example.test", "password": "password-1"},
        )
        response = TestClient(app).post(
            "/v1/reservations",
            headers={"Authorization": f"Bearer {token_response.json()['access_token']}"},
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
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "CONFIRMADA"
    assert payload["items"][0]["resource_type"] == "sala"


def test_home_page_renders_reservation_dashboard() -> None:
    """Verifica FR-14, FR-15, NFR-06, CT-33 e CT-35."""
    from app.api.v1 import app

    response = TestClient(app).get("/")

    assert response.status_code == 200
    text = response.text.lower()
    assert "dashboard" in text or "alocasenac" in text
    assert "api" in text
