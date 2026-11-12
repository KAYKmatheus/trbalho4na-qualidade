"""Unit tests for reservation persistence and the HTTP API."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
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


def test_ct28_audits_creation_update_approval_cancel_and_resource_block(auth_client) -> None:
    client, session = auth_client
    admin_login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "correct-password"},
    )
    requester_login = client.post(
        "/v1/auth/login",
        json={"email": "requester@example.test", "password": "requester-password"},
    )
    responsible_login = client.post(
        "/v1/auth/login",
        json={"email": "responsible@example.test", "password": "responsible-password"},
    )
    admin = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    requester = {"Authorization": f"Bearer {requester_login.json()['access_token']}"}
    responsible = {"Authorization": f"Bearer {responsible_login.json()['access_token']}"}
    resource = client.post(
        "/v1/admin/resources",
        headers=admin,
        json={
            "resource_type": "sala",
            "name": "Sala ciclo auditoria CT-28",
            "category": "aula",
            "capacity": 24,
            "location": "Bloco A",
            "restricted": True,
        },
    )
    assert resource.status_code == 201
    resource_id = resource.json()["id"]
    created = client.post(
        "/v1/reservations",
        headers=requester,
        json={
            "solicitante_id": "untrusted",
            "reason": "Reserva original CT-28",
            "items": [
                {
                    "resource_type": "sala",
                    "resource_id": resource_id,
                    "start": "2026-12-15T09:00:00Z",
                    "end": "2026-12-15T10:00:00Z",
                }
            ],
        },
    )
    assert created.status_code == 201
    reservation_id = created.json()["id"]
    item_id = created.json()["items"][0]["id"]

    updated = client.patch(
        f"/v1/reservations/{reservation_id}",
        headers=requester,
        json={"reason": "Reserva alterada CT-28"},
    )
    assigned = client.post(
        "/v1/admin/responsaveis/responsible-1/recursos",
        headers=admin,
        json={"resource_id": resource_id},
    )
    approved = client.post(
        f"/v1/reservations/items/{item_id}/decision",
        headers=responsible,
        json={
            "decision_type": "RECURSO_RESTRITO",
            "decision": "APROVADA",
            "justification": "Escopo validado CT-28",
        },
    )
    cancelled = client.delete(f"/v1/reservations/{reservation_id}", headers=requester)
    blocked = client.post(
        f"/v1/admin/resources/{resource_id}/maintenance",
        headers=admin,
        json={
            "start": "2026-12-15T09:00:00Z",
            "end": "2026-12-15T10:00:00Z",
            "reason": "Manutenção CT-28",
        },
    )

    assert updated.status_code == 200
    assert assigned.status_code == 201
    assert approved.status_code == 200
    assert cancelled.status_code == 200
    assert blocked.status_code == 201

    expected_audits = {
        ("CREATE", reservation_id): "requester-1",
        ("UPDATE", reservation_id): "requester-1",
        ("APPROVAL", item_id): "responsible-1",
        ("CANCEL", reservation_id): "requester-1",
        ("RESOURCE_BLOCK", resource_id): "admin-1",
    }
    audits = session.query(AuditEntry).filter(AuditEntry.action.in_([key[0] for key in expected_audits])).all()
    for (action, entity_id), actor_id in expected_audits.items():
        event = next(audit for audit in audits if audit.action == action and audit.entity_id == entity_id)
        assert event.actor_id == actor_id
        assert event.before_value
        assert event.after_value


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
