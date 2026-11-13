"""End-to-end reservation flows exercised exclusively through HTTP."""

import pytest

START = "2026-12-15T09:00:00Z"
END = "2026-12-15T10:00:00Z"


def _login(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_room(client, admin_headers, *, name: str, restricted: bool = False) -> dict:
    response = client.post(
        "/v1/admin/resources",
        headers=admin_headers,
        json={
            "resource_type": "sala",
            "name": name,
            "category": "aula",
            "capacity": 24,
            "location": "Bloco E2E",
            "restricted": restricted,
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.e2e
def test_full_reservation_flow_uses_http_only(auth_client) -> None:
    client, _ = auth_client
    admin_headers = _login(client, "admin@example.test", "correct-password")
    requester_headers = _login(client, "requester@example.test", "requester-password")
    responsible_headers = _login(client, "responsible@example.test", "responsible-password")

    room = _create_room(client, admin_headers, name="Sala fluxo E2E", restricted=True)
    material_response = client.post(
        "/v1/admin/resources",
        headers=admin_headers,
        json={
            "resource_type": "material",
            "name": "Kit fluxo E2E",
            "category": "equipamento",
            "quantity_total": 5,
            "restricted": True,
        },
    )
    assert material_response.status_code == 201
    material = material_response.json()

    for resource in (room, material):
        assigned = client.post(
            "/v1/admin/responsaveis/responsible-1/recursos",
            headers=admin_headers,
            json={"resource_id": resource["id"]},
        )
        assert assigned.status_code == 201

    search = client.get(
        "/v1/resources/search",
        headers=requester_headers,
        params={"resource_type": "sala", "start": START, "end": END},
    )
    assert search.status_code == 200
    assert room["id"] in {resource["id"] for resource in search.json()}

    created = client.post(
        "/v1/reservations",
        headers=requester_headers,
        json={
            "solicitante_id": "untrusted-client-id",
            "reason": "Fluxo completo E2E",
            "items": [
                {"resource_type": "sala", "resource_id": room["id"], "start": START, "end": END},
                {
                    "resource_type": "material",
                    "resource_id": material["id"],
                    "start": START,
                    "end": END,
                    "quantity": 2,
                },
            ],
        },
    )
    assert created.status_code == 201
    assert created.json()["status"] == "PENDENTE"
    reservation_id = created.json()["id"]
    items = {item["resource_type"]: item for item in created.json()["items"]}

    for item in items.values():
        decision = client.post(
            f"/v1/reservations/items/{item['id']}/decision",
            headers=responsible_headers,
            json={
                "decision_type": "RECURSO_RESTRITO",
                "decision": "APROVADA",
                "justification": "Escopo e disponibilidade confirmados",
            },
        )
        assert decision.status_code == 200
    assert decision.json()["status"] == "CONFIRMADA"

    using = client.patch(
        f"/v1/reservations/{reservation_id}/status",
        headers=admin_headers,
        json={"status": "EM_USO"},
    )
    assert using.status_code == 200
    assert using.json()["status"] == "EM_USO"

    material_item_id = items["material"]["id"]
    withdrawal = client.post(
        f"/v1/reservations/items/{material_item_id}/movements",
        headers=responsible_headers,
        json={"movement_type": "RETIRADA", "quantity": 2},
    )
    assert withdrawal.status_code == 201
    assert withdrawal.json()["movement_type"] == "RETIRADA"
    return_movement = client.post(
        f"/v1/reservations/items/{material_item_id}/movements",
        headers=responsible_headers,
        json={"movement_type": "DEVOLUCAO", "quantity": 2},
    )
    assert return_movement.status_code == 201
    assert return_movement.json()["movement_type"] == "DEVOLUCAO"

    balance = client.get(
        f"/v1/reservations/items/{material_item_id}/material-balance",
        headers=responsible_headers,
    )
    assert balance.status_code == 200
    assert balance.json() == {"withdrawn": 2, "returned": 2, "pending": 0}

    completed = client.patch(
        f"/v1/reservations/{reservation_id}/status",
        headers=admin_headers,
        json={"status": "CONCLUIDA"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "CONCLUIDA"

    report = client.get(
        "/v1/admin/reports",
        headers=admin_headers,
        params={"start": START, "end": "2026-12-16T00:00:00Z"},
    )
    assert report.status_code == 200
    room_rows = [row for row in report.json()["utilization"] if row["resource_id"] == room["id"]]
    assert len(room_rows) == 1
    assert room_rows[0]["reservation_count"] == 1


@pytest.mark.e2e
def test_overlapping_room_reservation_is_rejected_over_http(auth_client) -> None:
    client, _ = auth_client
    admin_headers = _login(client, "admin@example.test", "correct-password")
    requester_headers = _login(client, "requester@example.test", "requester-password")
    room = _create_room(client, admin_headers, name="Sala conflito E2E")
    payload = {
        "solicitante_id": "untrusted-client-id",
        "reason": "Reserva conflito E2E",
        "items": [
            {"resource_type": "sala", "resource_id": room["id"], "start": START, "end": END}
        ],
    }

    first = client.post("/v1/reservations", headers=requester_headers, json=payload)
    second = client.post("/v1/reservations", headers=requester_headers, json=payload)

    assert first.status_code == 201
    assert first.json()["status"] == "CONFIRMADA"
    assert second.status_code == 409
    assert room["id"] in second.json()["detail"]
