"""API error-path checks for administration and reservation endpoints."""

import pytest


def _token(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": "Bearer " + token}


def _create_resource(client, headers, *, resource_type: str, name: str, quantity_total: int | None = None) -> str:
    payload = {
        "resource_type": resource_type,
        "name": name,
        "category": "equipamento",
    }
    if resource_type == "sala":
        payload.update(category="aula", capacity=20, location="Bloco A")
    if quantity_total is not None:
        payload["quantity_total"] = quantity_total
    response = client.post("/v1/admin/resources", headers=headers, json=payload)
    assert response.status_code == 201
    return response.json()["id"]


def _reserve(client, headers, resource_type: str, resource_id: str, *, quantity: int = 1):
    return client.post(
        "/v1/reservations",
        headers=headers,
        json={
            "solicitante_id": "untrusted-client-id",
            "reason": "Reserva CT-15/18",
            "items": [
                {
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "start": "2026-12-15T09:00:00Z",
                    "end": "2026-12-15T10:00:00Z",
                    "quantity": quantity,
                }
            ],
        },
    )


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        (
            {
                "solicitante_id": "requester-1",
                "reason": "Reserva inválida",
                "items": [{"resource_type": "sala", "start": "2026-12-15T09:00:00Z", "end": "2026-12-15T10:00:00Z"}],
            },
            "resource_id",
        ),
        (
            {
                "solicitante_id": "requester-1",
                "reason": "Reserva inválida",
                "items": [
                    {
                        "resource_type": "sala",
                        "resource_id": "sala-1",
                        "start": "2026-12-15T10:00:00Z",
                        "end": "2026-12-15T09:00:00Z",
                    }
                ],
            },
            "end",
        ),
        (
            {
                "solicitante_id": "requester-1",
                "reason": "",
                "items": [
                    {
                        "resource_type": "sala",
                        "resource_id": "sala-1",
                        "start": "2026-12-15T09:00:00Z",
                        "end": "2026-12-15T10:00:00Z",
                    }
                ],
            },
            "reason",
        ),
        (
            {
                "solicitante_id": "requester-1",
                "reason": "Reserva inválida",
                "items": [
                    {
                        "resource_type": "material",
                        "resource_id": "material-1",
                        "start": "2026-12-15T09:00:00Z",
                        "end": "2026-12-15T10:00:00Z",
                        "quantity": 0,
                    }
                ],
            },
            "quantity",
        ),
    ],
)
def test_ct11_reservation_validation_reports_invalid_field(auth_client, payload, field: str) -> None:
    client, _ = auth_client
    requester = _token(client, "requester@example.test", "requester-password")

    response = client.post("/v1/reservations", headers=requester, json=payload)

    assert response.status_code == 422
    assert any(field in error["loc"] for error in response.json()["detail"])


def test_ct15_overlapping_room_reservation_returns_http_409(auth_client) -> None:
    client, _ = auth_client
    admin = _token(client, "admin@example.test", "correct-password")
    requester = _token(client, "requester@example.test", "requester-password")
    room_id = _create_resource(client, admin, resource_type="sala", name="Sala CT-15 HTTP")
    first = _reserve(client, requester, "sala", room_id)

    second = _reserve(client, requester, "sala", room_id)

    assert first.status_code == 201
    assert second.status_code == 409
    assert room_id in second.json()["detail"]


def test_ct18_material_over_stock_returns_http_409(auth_client) -> None:
    client, _ = auth_client
    admin = _token(client, "admin@example.test", "correct-password")
    requester = _token(client, "requester@example.test", "requester-password")
    material_id = _create_resource(
        client,
        admin,
        resource_type="material",
        name="Material CT-18 HTTP",
        quantity_total=3,
    )
    first = _reserve(client, requester, "material", material_id, quantity=2)

    second = _reserve(client, requester, "material", material_id, quantity=2)

    assert first.status_code == 201
    assert second.status_code == 409
    assert material_id in second.json()["detail"]
    assert "estoque" in second.json()["detail"].lower()


def test_ct33_http_errors_use_details_and_never_look_successful(auth_client) -> None:
    client, _ = auth_client
    requester = _token(client, "requester@example.test", "requester-password")
    admin = _token(client, "admin@example.test", "correct-password")
    missing_auth = client.get("/v1/auth/me")
    validation = client.post(
        "/v1/reservations",
        headers=requester,
        json={"solicitante_id": "requester-1", "reason": "", "items": []},
    )
    forbidden = client.get(
        "/v1/admin/reports",
        headers=requester,
        params={"start": "2026-12-15T09:00:00Z", "end": "2026-12-15T10:00:00Z"},
    )
    not_found = client.patch(
        "/v1/reservations/missing",
        headers=requester,
        json={"reason": "Atualização"},
    )
    room_id = _create_resource(client, admin, resource_type="sala", name="Sala CT-33")
    assert _reserve(client, requester, "sala", room_id).status_code == 201
    conflict = _reserve(client, requester, "sala", room_id)

    responses = {
        401: missing_auth,
        422: validation,
        403: forbidden,
        404: not_found,
        409: conflict,
    }
    assert {status: response.status_code for status, response in responses.items()} == {
        status: status for status in responses
    }
    for status, response in responses.items():
        body = response.json()
        assert isinstance(body, dict)
        assert "detail" in body
        assert isinstance(body["detail"], list if status == 422 else str)
        assert not 200 <= response.status_code < 300


def test_admin_resource_and_scope_errors_are_explicit(auth_client) -> None:
    client, _ = auth_client
    admin = _token(client, "admin@example.test", "correct-password")

    duplicate_user = {
        "name": "Duplicate",
        "email": "admin@example.test",
        "password": "another-password",
        "role": "SOLICITANTE",
    }
    assert client.post("/v1/admin/users", headers=admin, json=duplicate_user).status_code == 409
    assert client.post(
        "/v1/admin/resources",
        headers=admin,
        json={"resource_type": "sala", "name": "Sala incompleta"},
    ).status_code == 422
    assert client.get("/v1/admin/resources/missing", headers=admin).status_code == 404
    assert client.patch("/v1/admin/resources/missing", headers=admin, json={"name": "Novo"}).status_code == 404
    assert client.delete(
        "/v1/admin/responsaveis/responsible-1/recursos/missing",
        headers=admin,
    ).status_code == 404

    assert client.post(
        "/v1/admin/responsaveis/unknown/recursos",
        headers=admin,
        json={"resource_id": "missing"},
    ).status_code == 404
    valid_resource = client.post(
        "/v1/admin/resources",
        headers=admin,
        json={
            "resource_type": "sala",
            "name": "Sala de permissao",
            "category": "aula",
            "capacity": 20,
            "location": "Bloco A",
        },
    ).json()
    assert client.post(
        "/v1/admin/responsaveis/requester-1/recursos",
        headers=admin,
        json={"resource_id": valid_resource["id"]},
    ).status_code == 403


def test_scope_conflicts_and_missing_resource_routes(auth_client) -> None:
    client, _ = auth_client
    admin = _token(client, "admin@example.test", "correct-password")
    resource_response = client.post(
        "/v1/admin/resources",
        headers=admin,
        json={
            "resource_type": "sala",
            "name": "Sala de escopo",
            "category": "aula",
            "capacity": 20,
            "location": "Bloco A",
        },
    )
    assert resource_response.status_code == 201
    resource_id = resource_response.json()["id"]

    assigned = client.post(
        "/v1/admin/responsaveis/responsible-1/recursos",
        headers=admin,
        json={"resource_id": resource_id},
    )
    duplicate = client.post(
        "/v1/admin/responsaveis/responsible-1/recursos",
        headers=admin,
        json={"resource_id": resource_id},
    )
    assert assigned.status_code == 201
    assert duplicate.status_code == 409
    assert client.delete(
        f"/v1/admin/responsaveis/responsible-1/recursos/{resource_id}",
        headers=admin,
    ).status_code == 204

    invalid_interval = client.post(
        "/v1/admin/resources/missing/maintenance",
        headers=admin,
        json={
            "start": "2026-12-15T10:00:00Z",
            "end": "2026-12-15T09:00:00Z",
            "reason": "Teste",
        },
    )
    missing_resource = client.post(
        "/v1/admin/resources/missing/maintenance",
        headers=admin,
        json={
            "start": "2026-12-15T09:00:00Z",
            "end": "2026-12-15T10:00:00Z",
            "reason": "Teste",
        },
    )
    assert invalid_interval.status_code == 422
    assert missing_resource.status_code == 404


def test_search_approval_material_and_report_errors(auth_client) -> None:
    client, _ = auth_client
    admin = _token(client, "admin@example.test", "correct-password")
    responsible = _token(client, "responsible@example.test", "responsible-password")
    requester = _token(client, "requester@example.test", "requester-password")

    invalid_search = client.get(
        "/v1/resources/search",
        headers=requester,
        params={"start": "2026-12-15T10:00:00Z", "end": "2026-12-15T09:00:00Z"},
    )
    assert invalid_search.status_code == 422

    decision = client.post(
        "/v1/reservations/items/missing/decision",
        headers=responsible,
        json={
            "decision_type": "RECURSO_RESTRITO",
            "decision": "APROVADA",
            "justification": "Analisada",
        },
    )
    movement = client.post(
        "/v1/reservations/items/missing/movements",
        headers=responsible,
        json={"movement_type": "RETIRADA", "quantity": 1},
    )
    balance = client.get(
        "/v1/reservations/items/missing/material-balance",
        headers=responsible,
    )
    assert decision.status_code == movement.status_code == balance.status_code == 404

    invalid_report = client.get(
        "/v1/admin/reports",
        headers=admin,
        params={"start": "2026-12-15T10:00:00Z", "end": "2026-12-15T09:00:00Z"},
    )
    forbidden_report = client.get(
        "/v1/admin/reports",
        headers=requester,
        params={"start": "2026-12-15T09:00:00Z", "end": "2026-12-15T10:00:00Z"},
    )
    assert invalid_report.status_code == 422
    assert forbidden_report.status_code == 403


def test_reservation_not_found_transitions_are_404(auth_client) -> None:
    client, _ = auth_client
    requester = _token(client, "requester@example.test", "requester-password")
    responsible = _token(client, "responsible@example.test", "responsible-password")

    assert client.patch(
        "/v1/reservations/missing",
        headers=requester,
        json={"reason": "Atualizada"},
    ).status_code == 404
    assert client.delete("/v1/reservations/missing", headers=requester).status_code == 404
    assert client.patch(
        "/v1/reservations/missing/status",
        headers=responsible,
        json={"status": "EM_USO"},
    ).status_code == 404
