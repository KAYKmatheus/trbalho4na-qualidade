"""Simulated notification generation for reservation state changes."""

from app.models import Notification


def _headers(client, email: str, password: str) -> dict[str, str]:
    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _resource(client, admin, name: str, *, restricted: bool) -> dict:
    return client.post(
        "/v1/admin/resources",
        headers=admin,
        json={
            "resource_type": "sala",
            "name": name,
            "category": "aula",
            "capacity": 20,
            "location": "Bloco A",
            "restricted": restricted,
        },
    ).json()


def _reserve(client, requester, resource_id: str, start: str, end: str):
    return client.post(
        "/v1/reservations",
        headers=requester,
        json={
            "solicitante_id": "untrusted",
            "reason": "Atividade acadêmica",
            "items": [
                {"resource_type": "sala", "resource_id": resource_id, "start": start, "end": end}
            ],
        },
    )


def test_ct30_notifications_are_recorded_for_send_approve_reject_and_cancel(auth_client) -> None:
    client, session = auth_client
    admin = _headers(client, "admin@example.test", "correct-password")
    requester = _headers(client, "requester@example.test", "requester-password")
    responsible = _headers(client, "responsible@example.test", "responsible-password")
    restricted_room = _resource(client, admin, "Sala notificação restrita", restricted=True)
    scope = client.post(
        "/v1/admin/responsaveis/responsible-1/recursos",
        headers=admin,
        json={"resource_id": restricted_room["id"]},
    )
    approved = _reserve(
        client,
        requester,
        restricted_room["id"],
        "2026-12-25T08:00:00Z",
        "2026-12-25T09:00:00Z",
    )
    rejected = _reserve(
        client,
        requester,
        restricted_room["id"],
        "2026-12-25T10:00:00Z",
        "2026-12-25T11:00:00Z",
    )
    assert scope.status_code == 201
    assert approved.status_code == 201
    assert rejected.status_code == 201
    approved_item = approved.json()["items"][0]["id"]
    rejected_item = rejected.json()["items"][0]["id"]
    approval_response = client.post(
        f"/v1/reservations/items/{approved_item}/decision",
        headers=responsible,
        json={"decision_type": "RECURSO_RESTRITO", "decision": "APROVADA", "justification": "Aprovada"},
    )
    rejection_response = client.post(
        f"/v1/reservations/items/{rejected_item}/decision",
        headers=responsible,
        json={
            "decision_type": "RECURSO_RESTRITO",
            "decision": "REJEITADA",
            "justification": "Justificativa de rejeição",
        },
    )

    ordinary_room = _resource(client, admin, "Sala notificação cancelamento", restricted=False)
    to_cancel = _reserve(
        client,
        requester,
        ordinary_room["id"],
        "2026-12-26T08:00:00Z",
        "2026-12-26T09:00:00Z",
    )
    cancelled = client.delete(
        f"/v1/reservations/{to_cancel.json()['id']}",
        headers=requester,
    )
    notifications = session.query(Notification).order_by(Notification.created_at).all()

    assert approval_response.status_code == 200
    assert rejection_response.status_code == 200
    assert cancelled.status_code == 200
    assert {notification.event for notification in notifications} == {
        "SOLICITACAO_ENVIADA",
        "APROVADA",
        "REJEITADA",
        "CANCELADA",
    }
    assert any("Justificativa de rejeição" in notification.message for notification in notifications)
