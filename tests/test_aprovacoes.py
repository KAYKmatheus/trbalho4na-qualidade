"""Approval and teacher-validation acceptance checks."""

from datetime import datetime, timezone

from app.models import Approval, Reservation, ReservationItem

PERIOD_START = "2026-12-15T09:00:00Z"
PERIOD_END = "2026-12-15T10:00:00Z"


def _login_headers(client, email: str, password: str) -> dict[str, str]:
    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_resource(client, headers, *, resource_type: str, name: str, restricted: bool = False) -> dict:
    response = client.post(
        "/v1/admin/resources",
        headers=headers,
        json={
            "resource_type": resource_type,
            "name": name,
            "category": "aula" if resource_type != "professor" else None,
            "capacity": 24 if resource_type == "sala" else None,
            "location": "Bloco A" if resource_type == "sala" else None,
            "competencies": ["Matemática"] if resource_type == "professor" else None,
            "quantity_total": 4 if resource_type == "material" else None,
            "restricted": restricted,
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_reservation(client, headers, resource: dict, resource_type: str):
    return client.post(
        "/v1/reservations",
        headers=headers,
        json={
            "solicitante_id": "untrusted-client-value",
            "reason": "Atividade acadêmica",
            "items": [
                {
                    "resource_type": resource_type,
                    "resource_id": resource["id"],
                    "start": PERIOD_START,
                    "end": PERIOD_END,
                }
            ],
        },
    )


def test_ct21_approval_rechecks_conflict_and_keeps_item_pending(auth_client) -> None:
    client, session = auth_client
    admin = _login_headers(client, "admin@example.test", "correct-password")
    requester = _login_headers(client, "requester@example.test", "requester-password")
    responsible = _login_headers(client, "responsible@example.test", "responsible-password")
    resource = _create_resource(client, admin, resource_type="sala", name="Sala restrita CT21", restricted=True)
    pending = _create_reservation(client, requester, resource, "sala")
    item_id = pending.json()["items"][0]["id"]

    active = Reservation(solicitante_id="requester-1", reason="Reserva concorrente", status="CONFIRMADA")
    session.add(active)
    session.flush()
    session.add(
        ReservationItem(
            reservation_id=active.id,
            resource_type="sala",
            resource_id=resource["id"],
            start=datetime(2026, 12, 15, 9, tzinfo=timezone.utc),
            end=datetime(2026, 12, 15, 10, tzinfo=timezone.utc),
            status="CONFIRMADA",
        )
    )
    session.commit()

    assigned = client.post(
        "/v1/admin/responsaveis/responsible-1/recursos",
        headers=admin,
        json={"resource_id": resource["id"]},
    )
    assert assigned.status_code == 201
    decision = client.post(
        f"/v1/reservations/items/{item_id}/decision",
        headers=responsible,
        json={"decision_type": "RECURSO_RESTRITO", "decision": "APROVADA", "justification": "Aprovada"},
    )

    assert decision.status_code == 409
    assert session.query(ReservationItem).filter_by(id=item_id).one().status == "PENDENTE"
    assert session.query(Approval).filter_by(reservation_item_id=item_id).count() == 0


def test_ct22_restricted_resource_stays_pending_and_available_until_decision(auth_client) -> None:
    client, _ = auth_client
    admin = _login_headers(client, "admin@example.test", "correct-password")
    requester = _login_headers(client, "requester@example.test", "requester-password")
    resource = _create_resource(client, admin, resource_type="sala", name="Sala restrita CT22", restricted=True)

    response = _create_reservation(client, requester, resource, "sala")
    availability = client.get(
        "/v1/resources/search",
        headers=requester,
        params={"resource_type": "sala", "start": PERIOD_START, "end": PERIOD_END},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PENDENTE"
    assert response.json()["items"][0]["status"] == "PENDENTE"
    assert resource["id"] in {item["id"] for item in availability.json()}


def test_ct23_decision_requires_justification_and_scope(auth_client) -> None:
    client, session = auth_client
    admin = _login_headers(client, "admin@example.test", "correct-password")
    requester = _login_headers(client, "requester@example.test", "requester-password")
    responsible = _login_headers(client, "responsible@example.test", "responsible-password")
    resource = _create_resource(client, admin, resource_type="sala", name="Sala restrita CT23", restricted=True)
    pending = _create_reservation(client, requester, resource, "sala")
    item_id = pending.json()["items"][0]["id"]

    no_justification = client.post(
        f"/v1/reservations/items/{item_id}/decision",
        headers=responsible,
        json={"decision_type": "RECURSO_RESTRITO", "decision": "APROVADA", "justification": "   "},
    )
    outside_scope = client.post(
        f"/v1/reservations/items/{item_id}/decision",
        headers=responsible,
        json={"decision_type": "RECURSO_RESTRITO", "decision": "APROVADA", "justification": "Analisada"},
    )

    assert no_justification.status_code == 422
    assert outside_scope.status_code == 403
    assert session.query(Approval).filter_by(reservation_item_id=item_id).count() == 0


def test_ct36_responsible_validates_teacher_inside_scope(auth_client) -> None:
    client, session = auth_client
    admin = _login_headers(client, "admin@example.test", "correct-password")
    requester = _login_headers(client, "requester@example.test", "requester-password")
    responsible = _login_headers(client, "responsible@example.test", "responsible-password")
    teacher = _create_resource(client, admin, resource_type="professor", name="Docente CT36")
    scope = client.post(
        "/v1/admin/responsaveis/responsible-1/recursos",
        headers=admin,
        json={"resource_id": teacher["id"]},
    )
    pending = _create_reservation(client, requester, teacher, "professor")
    item_id = pending.json()["items"][0]["id"]

    decision = client.post(
        f"/v1/reservations/items/{item_id}/decision",
        headers=responsible,
        json={"decision_type": "VALIDACAO_DOCENTE", "decision": "APROVADA", "justification": "Agenda validada"},
    )

    assert scope.status_code == 201
    assert pending.json()["items"][0]["status"] == "PENDENTE"
    assert decision.status_code == 200
    assert decision.json()["status"] == "CONFIRMADA"
    assert session.query(ReservationItem).filter_by(id=item_id).one().status == "APROVADA"
    assert session.query(Approval).filter_by(reservation_item_id=item_id).one().decision_type == "VALIDACAO_DOCENTE"


def test_ct37_responsible_without_scope_cannot_decide(auth_client) -> None:
    client, session = auth_client
    admin = _login_headers(client, "admin@example.test", "correct-password")
    requester = _login_headers(client, "requester@example.test", "requester-password")
    responsible = _login_headers(client, "responsible@example.test", "responsible-password")
    resource = _create_resource(client, admin, resource_type="sala", name="Sala restrita CT37", restricted=True)
    pending = _create_reservation(client, requester, resource, "sala")
    item_id = pending.json()["items"][0]["id"]

    decision = client.post(
        f"/v1/reservations/items/{item_id}/decision",
        headers=responsible,
        json={"decision_type": "RECURSO_RESTRITO", "decision": "APROVADA", "justification": "Analisada"},
    )

    assert decision.status_code == 403
    assert session.query(ReservationItem).filter_by(id=item_id).one().status == "PENDENTE"
    assert session.query(Approval).filter_by(reservation_item_id=item_id).count() == 0


def test_ct05_responsible_cannot_approve_own_reservation(auth_client) -> None:
    client, session = auth_client
    admin = _login_headers(client, "admin@example.test", "correct-password")
    responsible = _login_headers(client, "responsible@example.test", "responsible-password")
    resource = _create_resource(client, admin, resource_type="sala", name="Sala CT05", restricted=True)
    pending = _create_reservation(client, responsible, resource, "sala")
    item_id = pending.json()["items"][0]["id"]

    decision = client.post(
        f"/v1/reservations/items/{item_id}/decision",
        headers=responsible,
        json={"decision_type": "RECURSO_RESTRITO", "decision": "APROVADA", "justification": "Analisada"},
    )

    assert pending.status_code == 201
    assert decision.status_code == 403
    assert session.query(ReservationItem).filter_by(id=item_id).one().status == "PENDENTE"
    assert session.query(Approval).filter_by(reservation_item_id=item_id).count() == 0


def test_ct39_teacher_item_stays_pending_until_responsible_validation(auth_client) -> None:
    client, _ = auth_client
    admin = _login_headers(client, "admin@example.test", "correct-password")
    requester = _login_headers(client, "requester@example.test", "requester-password")
    teacher = _create_resource(client, admin, resource_type="professor", name="Docente CT39")

    pending = _create_reservation(client, requester, teacher, "professor")
    item = pending.json()["items"][0]
    availability = client.get(
        "/v1/resources/search",
        headers=requester,
        params={"resource_type": "professor", "start": PERIOD_START, "end": PERIOD_END},
    )

    assert item["status"] == "PENDENTE"
    assert teacher["id"] in {resource["id"] for resource in availability.json()}
