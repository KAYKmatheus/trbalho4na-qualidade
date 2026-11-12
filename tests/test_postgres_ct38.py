"""PostgreSQL end-to-end coverage for avoided conflicts and their report."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.v1 import app
from app.db import get_db
from app.models import AuditEntry, Reservation, ReservationItem, User
from app.servicos.autenticacao import hash_password
from app.servicos.reservas import ReservationService

START = "2026-11-20T09:00:00Z"
END = "2026-11-20T10:00:00Z"


@pytest.mark.integration
def test_ct38_each_avoided_conflict_is_audited_and_counted_by_report(
    pg_session_factory,
    clean_postgres_database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suffix = uuid4().hex
    user_ids = {
        "admin": f"admin-{suffix}",
        "requester": f"requester-{suffix}",
        "responsible": f"responsible-{suffix}",
    }
    credentials = {
        "admin": (f"admin-{suffix}@example.test", "admin-password"),
        "requester": (f"requester-{suffix}@example.test", "requester-password"),
        "responsible": (f"responsible-{suffix}@example.test", "responsible-password"),
    }
    with pg_session_factory.begin() as session:
        session.add_all(
            [
                User(
                    id=user_ids["admin"],
                    name="CT-38 admin",
                    email=credentials["admin"][0],
                    password_hash=hash_password(credentials["admin"][1]),
                    role="ADMIN",
                ),
                User(
                    id=user_ids["requester"],
                    name="CT-38 requester",
                    email=credentials["requester"][0],
                    password_hash=hash_password(credentials["requester"][1]),
                    role="SOLICITANTE",
                ),
                User(
                    id=user_ids["responsible"],
                    name="CT-38 responsible",
                    email=credentials["responsible"][0],
                    password_hash=hash_password(credentials["responsible"][1]),
                    role="RESPONSAVEL",
                ),
            ]
        )

    def override_get_db():
        with pg_session_factory() as session:
            yield session

    monkeypatch.setenv("AUTH_SECRET_KEY", "ct38-integration-secret-with-enough-entropy")
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        def login(role: str) -> dict[str, str]:
            email, password = credentials[role]
            response = client.post("/v1/auth/login", json={"email": email, "password": password})
            assert response.status_code == 200
            return {"Authorization": f"Bearer {response.json()['access_token']}"}

        admin = login("admin")
        requester = login("requester")
        responsible = login("responsible")
        execution_started = datetime.now(timezone.utc)

        def create_resource(resource_type: str, name: str, *, quantity_total: int | None = None) -> str:
            payload = {
                "resource_type": resource_type,
                "name": f"{name}-{suffix}",
                "category": "aula",
            }
            if resource_type == "sala":
                payload.update(capacity=20, location="Bloco A")
            if quantity_total is not None:
                payload["quantity_total"] = quantity_total
            response = client.post("/v1/admin/resources", headers=admin, json=payload)
            assert response.status_code == 201
            return response.json()["id"]

        def reserve(resource_type: str, resource_id: str, *, quantity: int = 1):
            return client.post(
                "/v1/reservations",
                headers=requester,
                json={
                    "solicitante_id": "untrusted",
                    "reason": "Teste de conflitos evitados CT-38",
                    "items": [
                        {
                            "resource_type": resource_type,
                            "resource_id": resource_id,
                            "start": START,
                            "end": END,
                            "quantity": quantity,
                        }
                    ],
                },
            )

        room_id = create_resource("sala", "Sala CT-38")
        assert reserve("sala", room_id).status_code == 201
        room_conflict = reserve("sala", room_id)
        assert room_conflict.status_code == 409

        teacher_id = create_resource("professor", "Professor CT-38")
        teacher_reservation = reserve("professor", teacher_id)
        assert teacher_reservation.status_code == 201
        teacher_item_id = teacher_reservation.json()["items"][0]["id"]
        scope = client.post(
            f"/v1/admin/responsaveis/{user_ids['responsible']}/recursos",
            headers=admin,
            json={"resource_id": teacher_id},
        )
        assert scope.status_code == 201
        decision = client.post(
            f"/v1/reservations/items/{teacher_item_id}/decision",
            headers=responsible,
            json={
                "decision_type": "VALIDACAO_DOCENTE",
                "decision": "APROVADA",
                "justification": "Validada para CT-38",
            },
        )
        assert decision.status_code == 200
        teacher_conflict = reserve("professor", teacher_id)
        assert teacher_conflict.status_code == 409

        material_id = create_resource("material", "Material CT-38", quantity_total=1)
        assert reserve("material", material_id).status_code == 201
        stock_conflict = reserve("material", material_id)
        assert stock_conflict.status_code == 409

        blocked_id = create_resource("sala", "Sala bloqueada CT-38")
        block = client.post(
            f"/v1/admin/resources/{blocked_id}/maintenance",
            headers=admin,
            json={"start": START, "end": END, "reason": "Manutenção CT-38"},
        )
        assert block.status_code == 201
        blocked_conflict = reserve("sala", blocked_id)
        assert blocked_conflict.status_code == 409

        inactive_id = create_resource("sala", "Sala inativa CT-38")
        deactivated = client.patch(
            f"/v1/admin/resources/{inactive_id}",
            headers=admin,
            json={"active": False},
        )
        assert deactivated.status_code == 200
        inactive_conflict = reserve("sala", inactive_id)
        assert inactive_conflict.status_code == 409

        race_id = create_resource("sala", "Sala disputa CT-38")
        original_validate = ReservationService._validate_item_availability
        race_inserted = False

        def insert_competing_reservation(service: ReservationService, **context):
            nonlocal race_inserted
            resource = original_validate(service, **context)
            if context["resource_id"] == race_id and not race_inserted:
                race_inserted = True
                with pg_session_factory.begin() as session:
                    competing = Reservation(
                        solicitante_id=user_ids["requester"],
                        reason="Reserva concorrente CT-38",
                        status="CONFIRMADA",
                    )
                    session.add(competing)
                    session.flush()
                    session.add(
                        ReservationItem(
                            reservation_id=competing.id,
                            resource_type="sala",
                            resource_id=race_id,
                            start=datetime.fromisoformat(START.replace("Z", "+00:00")),
                            end=datetime.fromisoformat(END.replace("Z", "+00:00")),
                            status="CONFIRMADA",
                        )
                    )
            return resource

        monkeypatch.setattr(
            ReservationService,
            "_validate_item_availability",
            insert_competing_reservation,
        )
        race_conflict = reserve("sala", race_id)
        assert race_inserted
        assert race_conflict.status_code == 409

        expected = {
            room_id: ("sala", "SOBREPOSICAO"),
            teacher_id: ("professor", "SOBREPOSICAO"),
            material_id: ("material", "ESTOQUE"),
            blocked_id: ("sala", "BLOQUEIO"),
            inactive_id: ("sala", "INATIVO"),
            race_id: ("sala", "CONCORRENCIA"),
        }
        report_start = execution_started - timedelta(seconds=1)
        report_end = datetime.now(timezone.utc) + timedelta(seconds=1)
        with pg_session_factory() as session:
            events = list(
                session.scalars(
                    select(AuditEntry).where(
                        AuditEntry.action == "CONFLITO_EVITADO",
                        AuditEntry.created_at >= report_start,
                        AuditEntry.created_at < report_end,
                        AuditEntry.entity_id.in_(expected),
                    )
                )
            )

        assert len(events) == len(expected)
        for event in events:
            resource_type, cause = expected[event.entity_id]
            details = json.loads(event.payload)
            assert event.actor_id == user_ids["requester"]
            assert event.entity_type == resource_type
            assert details["reason"] == cause
            assert datetime.fromisoformat(details["start"]) == datetime.fromisoformat(START.replace("Z", "+00:00"))
            assert datetime.fromisoformat(details["end"]) == datetime.fromisoformat(END.replace("Z", "+00:00"))
            assert details["message"]

        report = client.get(
            "/v1/admin/reports",
            headers=admin,
            params={"start": report_start.isoformat(), "end": report_end.isoformat()},
        )
        assert report.status_code == 200
        assert report.json()["conflicts_avoided"] == len(events)
    finally:
        app.dependency_overrides.pop(get_db, None)
