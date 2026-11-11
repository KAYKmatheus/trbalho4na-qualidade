"""API error-path checks for administration and reservation endpoints."""


def _token(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": "Bearer " + token}


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
